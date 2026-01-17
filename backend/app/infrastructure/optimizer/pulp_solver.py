"""
PuLP線形計画法ソルバー

クリーンアーキテクチャ: infrastructure層
"""
import uuid
import logging
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.schemas import OptimizePhase
from pulp import (
    LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value, PULP_CBC_CMD
)

# HiGHS solver import with fallback
try:
    from pulp import HiGHS_CMD
    HIGHS_AVAILABLE = True
except ImportError:
    HIGHS_AVAILABLE = False
    HiGHS_CMD = None

from app.domain.entities import (
    Dish, DishPortion, MealPlan, DailyMenuPlan, DailyMealAssignment,
    MultiDayMenuPlan, NutrientTarget, CookingTask, ShoppingItem,
    MealTypeEnum,
)
from app.domain.services.constants import (
    ALL_NUTRIENTS, NUTRIENT_WEIGHTS, MEAL_RATIOS,
    DEFAULT_MEAL_CATEGORY_CONSTRAINTS, CATEGORY_CONSTRAINTS_BY_VOLUME,
    get_enabled_nutrients,
    SATURATION_THRESHOLD, UNDER_PENALTY, OVER_PENALTY,
    NUTRIENT_UPPER_LIMIT_RATIO, UPPER_TARGET_NUTRIENTS, UPPER_LIMIT_PENALTY,
    RANGE_TARGET_NUTRIENTS,
)
from app.domain.services import NutrientCalculator, UnitConverter

logger = logging.getLogger(__name__)


class PuLPSolver:
    """PuLP線形計画法を使用した献立最適化ソルバー"""

    def __init__(
        self,
        time_limit: int = 30,
        msg: int = 0,
        solver_type: str = "auto",
        prefilter_top_n: int = 30,
        gap_rel: float = 0.05,
    ):
        """
        Args:
            time_limit: ソルバーのタイムリミット（秒）
            msg: メッセージ出力レベル（0=なし）
            solver_type: ソルバータイプ ("highs", "cbc", "auto")
            prefilter_top_n: 事前フィルタリングで残す料理数（カテゴリ毎）
            gap_rel: MIPギャップ許容値（0.05=最適解の5%以内で終了）
        """
        self.time_limit = time_limit
        self.msg = msg
        self.solver_type = solver_type
        self.prefilter_top_n = prefilter_top_n
        self.gap_rel = gap_rel
        self._solver = self._create_solver()
        self._nutrient_calc = NutrientCalculator()
        self._unit_converter = UnitConverter()

    def _create_solver(self):
        """ソルバーインスタンスを作成（HiGHS優先、CBCフォールバック）

        gapRel: 相対ギャップ許容値を設定することで、最適解に近い解が
        見つかった時点で早期終了できる（例: 0.05 = 5%以内で終了）
        """
        if self.solver_type == "highs" or (self.solver_type == "auto" and HIGHS_AVAILABLE):
            if HIGHS_AVAILABLE:
                logger.info("Using HiGHS solver")
                try:
                    # HiGHS version によってはgapRelをサポートしていない
                    return HiGHS_CMD(
                        msg=self.msg,
                        timeLimit=self.time_limit,
                        gapRel=self.gap_rel,
                    )
                except TypeError:
                    logger.warning("HiGHS does not support gapRel, using without it")
                    return HiGHS_CMD(
                        msg=self.msg,
                        timeLimit=self.time_limit,
                    )
            else:
                logger.warning("HiGHS not available, falling back to CBC")

        logger.info("Using CBC solver")
        return PULP_CBC_CMD(
            msg=self.msg,
            timeLimit=self.time_limit,
            gapRel=self.gap_rel,
        )

    def _calculate_dish_score(
        self,
        dish: Dish,
        target: NutrientTarget,
        enabled_nutrients: list[str],
    ) -> float:
        """料理の栄養密度スコアを計算

        Args:
            dish: 料理
            target: 栄養素目標
            enabled_nutrients: 有効な栄養素リスト

        Returns:
            栄養密度スコア（高いほど良い）
        """
        score = 0.0
        calories = max(dish.calories, 1)  # ゼロ除算防止

        for nutrient in enabled_nutrients:
            value = getattr(dish, nutrient, 0)
            weight = NUTRIENT_WEIGHTS.get(nutrient, 1.0)

            # 目標値を取得
            if nutrient == "sodium":
                target_val = getattr(target, "sodium_max", 2500)
                # ナトリウムは低いほうが良い（逆スコア）
                if target_val > 0 and value < target_val:
                    score += weight * (1 - value / target_val)
            elif nutrient == "calories":
                # カロリーはスコアに含めない（密度計算の分母なので）
                continue
            else:
                target_attr = f"{nutrient}_min"
                target_val = getattr(target, target_attr, 0)
                if target_val > 0:
                    # 栄養密度 = 栄養素量 / カロリー × 目標比率
                    density = (value / calories) * (100 / target_val) * weight
                    score += density

        return score

    def _prefilter_dishes(
        self,
        dishes: list[Dish],
        target: NutrientTarget,
        enabled_nutrients: list[str],
        preferred_dish_ids: Optional[set[int]] = None,
        keep_dish_ids: Optional[set[int]] = None,
    ) -> list[Dish]:
        """栄養密度スコアでカテゴリ毎に上位N件に絞る

        Args:
            dishes: 全料理リスト
            target: 栄養素目標
            enabled_nutrients: 有効な栄養素リスト
            preferred_dish_ids: 優先料理ID（必ず残す）
            keep_dish_ids: 必須料理ID（必ず残す）

        Returns:
            フィルタリングされた料理リスト
        """
        if len(dishes) <= self.prefilter_top_n * 5:
            # 料理数が少なければフィルタリング不要
            return dishes

        preferred_dish_ids = preferred_dish_ids or set()
        keep_dish_ids = keep_dish_ids or set()
        must_keep_ids = preferred_dish_ids | keep_dish_ids

        # カテゴリ別に分類
        dishes_by_category: dict[str, list[tuple[Dish, float]]] = {}
        for dish in dishes:
            cat = dish.category.value
            if cat not in dishes_by_category:
                dishes_by_category[cat] = []
            score = self._calculate_dish_score(dish, target, enabled_nutrients)
            dishes_by_category[cat].append((dish, score))

        # 各カテゴリで上位N件を選択
        filtered_dishes = []
        for cat, dish_scores in dishes_by_category.items():
            # スコア降順でソート
            dish_scores.sort(key=lambda x: x[1], reverse=True)

            selected = []
            for dish, score in dish_scores:
                if dish.id in must_keep_ids:
                    # 必須料理は常に含める
                    selected.append(dish)
                elif len(selected) < self.prefilter_top_n:
                    selected.append(dish)

            filtered_dishes.extend(selected)

        logger.info(f"Dish pre-filtering: {len(dishes)} -> {len(filtered_dishes)} dishes")
        return filtered_dishes

    def optimize_meal(
        self,
        dishes: list[Dish],
        target: NutrientTarget,
        meal_name: str,
        excluded_dish_ids: Optional[set[int]] = None,
        volume_multiplier: float = 1.0,
        category_constraints: Optional[dict] = None,
    ) -> Optional[MealPlan]:
        """1食分のメニューを最適化

        Args:
            dishes: 利用可能な料理リスト
            target: 栄養素目標（1日分）
            meal_name: 食事タイプ（breakfast/lunch/dinner）
            excluded_dish_ids: 除外する料理ID
            volume_multiplier: 人前数の倍率
            category_constraints: カテゴリ別品数制約

        Returns:
            最適化されたMealPlan、失敗時はNone
        """
        excluded_dish_ids = excluded_dish_ids or set()
        meal_type = MealTypeEnum(meal_name)

        # デフォルトのカテゴリ制約
        if category_constraints is None:
            category_constraints = DEFAULT_MEAL_CATEGORY_CONSTRAINTS.get(
                meal_name,
                DEFAULT_MEAL_CATEGORY_CONSTRAINTS["dinner"]
            )

        # この食事タイプに適した料理のみフィルタ
        available_dishes = [
            d for d in dishes
            if d.id not in excluded_dish_ids and meal_type in d.meal_types
        ]

        if not available_dishes:
            return None

        ratio = MEAL_RATIOS.get(meal_name, 0.33)

        # カテゴリ別に料理を分類
        dishes_by_category: dict[str, list[Dish]] = {}
        for d in available_dishes:
            cat = d.category.value
            if cat not in dishes_by_category:
                dishes_by_category[cat] = []
            dishes_by_category[cat].append(d)

        # 問題定義
        prob = LpProblem(f"meal_optimization_{meal_name}", LpMinimize)

        # 変数: 各料理を選択するかどうか（バイナリ）
        y = {d.id: LpVariable(f"dish_{d.id}", cat="Binary") for d in available_dishes}

        # 変数: 各料理の人前数
        max_servings = 2.0 * volume_multiplier
        min_servings_per_dish = 0.5 * volume_multiplier
        servings = {
            d.id: LpVariable(f"servings_{d.id}", lowBound=0, upBound=max_servings)
            for d in available_dishes
        }

        # 栄養素の計算
        nutrients = {}
        for nutrient in ALL_NUTRIENTS:
            nutrients[nutrient] = lpSum(
                getattr(d, nutrient) * servings[d.id] for d in available_dishes
            )

        # 目標値（1食分の比率を適用）
        targets = self._calculate_meal_targets(target, ratio)

        # 偏差変数
        dev_pos = {n: LpVariable(f"dev_pos_{n}", lowBound=0) for n in targets}
        dev_neg = {n: LpVariable(f"dev_neg_{n}", lowBound=0) for n in targets}

        # 目的関数: 重み付き偏差の最小化
        # 下振れ（不足）は重くペナルティ、上振れ（超過）は軽く
        prob += lpSum(
            NUTRIENT_WEIGHTS.get(n, 1.0) * (
                OVER_PENALTY * dev_pos[n] + UNDER_PENALTY * dev_neg[n]
            ) / max(targets[n], 1)
            for n in targets
        )

        # 偏差制約
        for n in targets:
            if n == "sodium":
                prob += nutrients[n] - dev_neg[n] <= targets[n]
            else:
                prob += nutrients[n] + dev_neg[n] - dev_pos[n] == targets[n]

        # カロリー範囲制約
        prob += nutrients["calories"] >= target.calories_min * ratio * 0.8
        prob += nutrients["calories"] <= target.calories_max * ratio * 1.2

        # 料理選択と人前数のリンク
        for d in available_dishes:
            prob += servings[d.id] <= max_servings * y[d.id]
            prob += servings[d.id] >= min_servings_per_dish * y[d.id]

        # カテゴリ別の品数制約
        for cat, (min_count, max_count) in category_constraints.items():
            if cat in dishes_by_category:
                cat_dishes = dishes_by_category[cat]
                prob += lpSum(y[d.id] for d in cat_dishes) >= min_count
                prob += lpSum(y[d.id] for d in cat_dishes) <= max_count

        # 求解
        prob.solve(self._solver)

        if LpStatus[prob.status] not in ["Optimal", "Not Solved"]:
            return None

        # 結果抽出
        return self._extract_meal_result(
            available_dishes, y, servings, meal_name
        )

    def optimize_daily_menu(
        self,
        dishes: list[Dish],
        target: Optional[NutrientTarget] = None,
        excluded_dish_ids: Optional[list[int]] = None,
    ) -> Optional[DailyMenuPlan]:
        """1日分のメニューを最適化

        Args:
            dishes: 利用可能な料理リスト
            target: 栄養素目標
            excluded_dish_ids: 除外する料理ID

        Returns:
            最適化されたDailyMenuPlan、失敗時はNone
        """
        target = target or NutrientTarget()
        excluded_dish_ids = set(excluded_dish_ids or [])

        if not dishes:
            return None

        used_dish_ids: set[int] = set()

        # 各食事を最適化（同じ料理は使わない）
        breakfast = self.optimize_meal(
            dishes, target, "breakfast", excluded_dish_ids | used_dish_ids
        )
        if breakfast:
            used_dish_ids.update(dp.dish.id for dp in breakfast.dishes)

        lunch = self.optimize_meal(
            dishes, target, "lunch", excluded_dish_ids | used_dish_ids
        )
        if lunch:
            used_dish_ids.update(dp.dish.id for dp in lunch.dishes)

        dinner = self.optimize_meal(
            dishes, target, "dinner", excluded_dish_ids | used_dish_ids
        )

        # フォールバック: 料理重複を許可して再試行
        if not all([breakfast, lunch, dinner]):
            if not breakfast:
                breakfast = self.optimize_meal(dishes, target, "breakfast", excluded_dish_ids)
            if not lunch:
                lunch = self.optimize_meal(dishes, target, "lunch", excluded_dish_ids)
            if not dinner:
                dinner = self.optimize_meal(dishes, target, "dinner", excluded_dish_ids)

        if not all([breakfast, lunch, dinner]):
            return None

        # 合計栄養素
        total_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}
        for meal in [breakfast, lunch, dinner]:
            for nutrient in ALL_NUTRIENTS:
                total_nutrients[nutrient] += getattr(meal, f"total_{nutrient}")

        # 達成率計算
        achievement = self._nutrient_calc.calculate_achievement_rate(total_nutrients, target)

        return DailyMenuPlan(
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            total_nutrients={k: round(v, 1) for k, v in total_nutrients.items()},
            achievement_rate={k: round(v, 1) for k, v in achievement.items()},
        )

    def solve_multi_day(
        self,
        dishes: list[Dish],
        days: int = 1,
        people: int = 1,
        target: Optional[NutrientTarget] = None,
        excluded_dish_ids: Optional[set[int]] = None,
        excluded_ingredient_ids: Optional[set[int]] = None,
        keep_dish_ids: Optional[set[int]] = None,
        preferred_ingredient_ids: Optional[set[int]] = None,
        preferred_dish_ids: Optional[set[int]] = None,
        batch_cooking_level: str = "normal",
        variety_level: str = "normal",
        meal_settings: Optional[dict] = None,
        enabled_nutrients: Optional[list[str]] = None,
        optimization_strategy: str = "auto",
    ) -> Optional[MultiDayMenuPlan]:
        """複数日×複数人のメニューを最適化（作り置き対応）

        Args:
            dishes: 利用可能な料理リスト
            days: 日数（1-7）
            people: 人数（1-6）
            target: 栄養素目標（1人1日あたり）
            excluded_dish_ids: 除外料理ID
            excluded_ingredient_ids: 除外食材ID（嫌いな食材を含む料理を除外）
            keep_dish_ids: 必ず含める料理ID
            preferred_ingredient_ids: 優先食材ID
            preferred_dish_ids: 優先料理ID
            batch_cooking_level: 作り置き優先度
            variety_level: 料理の繰り返し
            meal_settings: 朝昼夜別の設定
            enabled_nutrients: 有効な栄養素リスト（Noneの場合は全栄養素）
            optimization_strategy: 最適化戦略 ("full_mip", "rolling", "auto")

        Returns:
            MultiDayMenuPlan
        """
        target = target or NutrientTarget()
        excluded_dish_ids = excluded_dish_ids or set()
        excluded_ingredient_ids = excluded_ingredient_ids or set()
        keep_dish_ids = keep_dish_ids or set()
        preferred_ingredient_ids = preferred_ingredient_ids or set()
        preferred_dish_ids = preferred_dish_ids or set()

        # 有効な栄養素を決定（Phase 1）
        active_nutrients = get_enabled_nutrients(enabled_nutrients)
        logger.info(f"Active nutrients: {len(active_nutrients)} (of {len(ALL_NUTRIENTS)})")

        # meal_settingsの正規化
        meal_settings = self._normalize_meal_settings(meal_settings)

        # 有効な食事タイプのみ抽出
        enabled_meals = [
            m for m in ["breakfast", "lunch", "dinner"]
            if meal_settings[m].get("enabled", True)
        ]

        # 除外料理を適用
        available_dishes = [d for d in dishes if d.id not in excluded_dish_ids]

        # 除外食材を含む料理をフィルタリング
        if excluded_ingredient_ids:
            available_dishes = self._filter_dishes_by_excluded_ingredients(
                available_dishes, excluded_ingredient_ids
            )
            logger.info(f"After excluding ingredients: {len(available_dishes)} dishes")

        if not available_dishes:
            return None

        # 問題定義
        prob = LpProblem("multi_day_meal_planning", LpMinimize)

        # 決定変数の作成
        x, s, c, q = self._create_multi_day_variables(
            available_dishes, days, people, enabled_meals
        )

        # 偏差変数（有効な栄養素のみ）
        dev_pos, dev_neg = self._create_deviation_variables(days, active_nutrients)

        # 目的関数（有効な栄養素のみ使用）
        prob += self._build_multi_day_objective(
            available_dishes, days, x,
            dev_pos, dev_neg, target,
            preferred_ingredient_ids, preferred_dish_ids,
            batch_cooking_level, active_nutrients
        )

        # 制約条件を追加（有効な栄養素のみ）
        self._add_multi_day_constraints(
            prob, available_dishes, days, people, target,
            x, s, c, q, dev_pos, dev_neg,
            enabled_meals, meal_settings,
            variety_level, keep_dish_ids, active_nutrients
        )

        # 求解（Phase 5: HiGHS/CBCを使用）
        prob.solve(self._solver)

        if LpStatus[prob.status] not in ["Optimal", "Not Solved"]:
            # フォールバック
            return self._fallback_multi_day(
                available_dishes, days, people, target,
                preferred_ingredient_ids
            )

        # 結果抽出
        return self._extract_multi_day_result(
            available_dishes, days, people, target,
            x, s, c, q, enabled_meals,
            preferred_ingredient_ids
        )

    def refine_plan(
        self,
        dishes: list[Dish],
        days: int = 1,
        people: int = 1,
        target: Optional[NutrientTarget] = None,
        keep_dish_ids: Optional[set[int]] = None,
        exclude_dish_ids: Optional[set[int]] = None,
        excluded_ingredient_ids: Optional[set[int]] = None,
        preferred_ingredient_ids: Optional[set[int]] = None,
        preferred_dish_ids: Optional[set[int]] = None,
        batch_cooking_level: str = "normal",
        variety_level: str = "normal",
        meal_settings: Optional[dict] = None,
        enabled_nutrients: Optional[list[str]] = None,
        optimization_strategy: str = "auto",
    ) -> Optional[MultiDayMenuPlan]:
        """献立を調整して再最適化"""
        return self.solve_multi_day(
            dishes=dishes,
            days=days,
            people=people,
            target=target,
            excluded_dish_ids=exclude_dish_ids,
            excluded_ingredient_ids=excluded_ingredient_ids,
            keep_dish_ids=keep_dish_ids,
            preferred_ingredient_ids=preferred_ingredient_ids,
            preferred_dish_ids=preferred_dish_ids,
            batch_cooking_level=batch_cooking_level,
            variety_level=variety_level,
            meal_settings=meal_settings,
            enabled_nutrients=enabled_nutrients,
            optimization_strategy=optimization_strategy,
        )

    def solve_multi_day_staged(
        self,
        dishes: list[Dish],
        days: int = 1,
        people: int = 1,
        target: Optional[NutrientTarget] = None,
        excluded_dish_ids: Optional[set[int]] = None,
        excluded_ingredient_ids: Optional[set[int]] = None,
        keep_dish_ids: Optional[set[int]] = None,
        preferred_ingredient_ids: Optional[set[int]] = None,
        preferred_dish_ids: Optional[set[int]] = None,
        batch_cooking_level: str = "normal",
        variety_level: str = "normal",
        meal_settings: Optional[dict] = None,
        enabled_nutrients: Optional[list[str]] = None,
        household_type: str = "single",
        scheduler_seed: Optional[int] = None,
        progress_callback: Optional[Callable[["OptimizePhase"], None]] = None,
    ) -> Optional[MultiDayMenuPlan]:
        """段階的決定モードで複数日メニューを最適化

        Phase 1: MealSchedulerで主食を決定（ルールベース）
        Phase 2: MealSchedulerで主菜を決定（たんぱく源ローテーション）
        Phase 3: 副菜・汁物を既存の最適化で埋める
        Phase 4: 栄養達成率チェック、必要なら主菜を変更してリトライ

        Args:
            dishes: 利用可能な料理リスト
            days: 日数（1-7）
            people: 人数（1-6）
            target: 栄養素目標（1人1日あたり）
            excluded_dish_ids: 除外料理ID
            excluded_ingredient_ids: 除外食材ID
            keep_dish_ids: 必ず含める料理ID
            preferred_ingredient_ids: 優先食材ID
            preferred_dish_ids: 優先料理ID
            batch_cooking_level: 作り置き優先度
            variety_level: 料理の繰り返し
            meal_settings: 朝昼夜別の設定
            enabled_nutrients: 有効な栄養素リスト
            household_type: 世帯タイプ（single/couple/family）
            scheduler_seed: MealSchedulerの乱数シード

        Returns:
            MultiDayMenuPlan
        """
        from app.domain.services.meal_scheduler import (
            MealScheduler, load_ingredient_categories, get_protein_source
        )

        target = target or NutrientTarget()
        excluded_dish_ids = excluded_dish_ids or set()
        excluded_ingredient_ids = excluded_ingredient_ids or set()
        keep_dish_ids = keep_dish_ids or set()
        preferred_ingredient_ids = preferred_ingredient_ids or set()
        preferred_dish_ids = preferred_dish_ids or set()

        # meal_settingsの正規化
        meal_settings = self._normalize_meal_settings(meal_settings)

        # 有効な食事タイプのみ抽出
        enabled_meals = [
            m for m in ["breakfast", "lunch", "dinner"]
            if meal_settings[m].get("enabled", True)
        ]

        # 除外料理を適用
        available_dishes = [d for d in dishes if d.id not in excluded_dish_ids]

        # 除外食材を含む料理をフィルタリング
        if excluded_ingredient_ids:
            available_dishes = self._filter_dishes_by_excluded_ingredients(
                available_dishes, excluded_ingredient_ids
            )

        if not available_dishes:
            logger.warning("No dishes available after filtering")
            return None

        # MealSchedulerを初期化
        scheduler = MealScheduler(seed=scheduler_seed)

        # 進捗報告用のヘルパー関数
        def report_progress(phase_name: str) -> None:
            if progress_callback:
                from app.models.schemas import OptimizePhase
                phase_map = {
                    "building_model": OptimizePhase.BUILDING_MODEL,
                    "applying_constraints": OptimizePhase.APPLYING_CONSTRAINTS,
                    "solving": OptimizePhase.SOLVING,
                    "finalizing": OptimizePhase.FINALIZING,
                }
                if phase_name in phase_map:
                    progress_callback(phase_map[phase_name])

        # 食材カテゴリをロード（たんぱく源検出用）
        ingredient_categories = []
        for dish in available_dishes:
            for ing in dish.ingredients:
                if ing.ingredient_id and ing.ingredient_name:
                    # 食材名からカテゴリを推定
                    category = self._estimate_ingredient_category(ing.ingredient_name)
                    ingredient_categories.append((ing.ingredient_id, category))
        if ingredient_categories:
            load_ingredient_categories(ingredient_categories)

        # keep_dish_ids から主食・主菜を抽出
        from app.domain.entities.enums import DishCategoryEnum
        keep_staples: list[Dish] = []
        keep_mains: list[Dish] = []
        if keep_dish_ids:
            for dish in available_dishes:
                if dish.id in keep_dish_ids:
                    if dish.category in (DishCategoryEnum.STAPLE, DishCategoryEnum.STAPLE_MAIN):
                        keep_staples.append(dish)
                    elif dish.category == DishCategoryEnum.MAIN:
                        keep_mains.append(dish)
            if keep_staples:
                logger.info(f"Keep staples from keep_dish_ids: {[d.name for d in keep_staples]}")
            if keep_mains:
                logger.info(f"Keep mains from keep_dish_ids: {[d.name for d in keep_mains]}")

        # === 確定枠の初期化 ===
        # keep_dish_ids の料理は条件チェックなしで最初に配置
        fixed_staples: dict[int, dict[str, Dish]] = {d: {} for d in range(1, days + 1)}
        fixed_mains: dict[int, dict[str, Dish]] = {d: {} for d in range(1, days + 1)}

        # keep_staples を確定枠に配置（条件チェックなし、順番に空きスロットへ）
        staple_idx = 0
        for day in range(1, days + 1):
            for meal in enabled_meals:
                if staple_idx >= len(keep_staples):
                    break
                fixed_staples[day][meal] = keep_staples[staple_idx]
                logger.info(f"Fixed staple: {keep_staples[staple_idx].name} -> day {day} {meal}")
                staple_idx += 1
            if staple_idx >= len(keep_staples):
                break

        # keep_mains を確定枠に配置（条件チェックなし、順番に空きスロットへ）
        main_idx = 0
        for day in range(1, days + 1):
            for meal in enabled_meals:
                if main_idx >= len(keep_mains):
                    break
                # 確定主食が「主食・主菜」の場合はスキップ（主菜枠がない）
                fixed_staple = fixed_staples.get(day, {}).get(meal)
                if fixed_staple and fixed_staple.category == DishCategoryEnum.STAPLE_MAIN:
                    continue
                fixed_mains[day][meal] = keep_mains[main_idx]
                logger.info(f"Fixed main: {keep_mains[main_idx].name} -> day {day} {meal}")
                main_idx += 1
            if main_idx >= len(keep_mains):
                break

        # 配置できなかった料理があれば警告
        if staple_idx < len(keep_staples):
            unplaced = [d.name for d in keep_staples[staple_idx:]]
            logger.warning(f"Could not place all keep_staples: {unplaced}")
        if main_idx < len(keep_mains):
            unplaced = [d.name for d in keep_mains[main_idx:]]
            logger.warning(f"Could not place all keep_mains: {unplaced}")

        # Phase 1: 主食スケジューリング（確定枠以外を埋める）
        logger.info("Phase 1: Scheduling staples")
        staples = scheduler.schedule_staples(
            available_dishes, days, enabled_meals, household_type, meal_settings, variety_level
        )
        # 確定枠で上書き
        for day in fixed_staples:
            for meal in fixed_staples[day]:
                staples[day][meal] = fixed_staples[day][meal]

        # Phase 2: 主菜スケジューリング（確定枠以外を埋める）
        logger.info("Phase 2: Scheduling mains")
        mains = scheduler.schedule_mains(
            available_dishes, days, enabled_meals, staples,
            household_type, excluded_dish_ids, variety_level
        )
        # 確定枠で上書き
        for day in fixed_mains:
            for meal in fixed_mains[day]:
                mains[day][meal] = fixed_mains[day][meal]

        # Phase 3: 副菜・汁物を最適化
        logger.info("Phase 3: Optimizing sides and soups")
        report_progress("building_model")
        result = self._optimize_sides_staged(
            available_dishes, days, people, target,
            staples, mains, enabled_meals, meal_settings,
            preferred_ingredient_ids, preferred_dish_ids,
            variety_level, enabled_nutrients,
            report_progress,
        )

        if result is None:
            logger.warning("Phase 3 optimization failed, falling back to full optimization")
            return self.solve_multi_day(
                dishes=dishes,
                days=days,
                people=people,
                target=target,
                excluded_dish_ids=excluded_dish_ids,
                excluded_ingredient_ids=excluded_ingredient_ids,
                keep_dish_ids=keep_dish_ids,
                preferred_ingredient_ids=preferred_ingredient_ids,
                preferred_dish_ids=preferred_dish_ids,
                batch_cooking_level=batch_cooking_level,
                variety_level=variety_level,
                meal_settings=meal_settings,
                enabled_nutrients=enabled_nutrients,
            )

        # Phase 4: 栄養達成率チェック（最低達成率で判定）
        min_achievement = min(result.overall_achievement.values())
        min_nutrient = min(result.overall_achievement, key=result.overall_achievement.get)
        logger.info(f"Phase 4: Minimum achievement rate: {min_achievement:.1f}% ({min_nutrient})")

        if min_achievement < 85:
            logger.info("Achievement rate too low, retrying with different mains")
            # 使用した主菜を除外して再試行（ただし確定枠は除外しない）
            fixed_main_ids = {d.id for day in fixed_mains for d in fixed_mains[day].values()}
            used_main_ids = {
                mains[d][m].id for d in mains for m in mains[d]
                if mains[d][m] is not None and mains[d][m].id not in fixed_main_ids
            }
            mains_retry = scheduler.schedule_mains(
                available_dishes, days, enabled_meals, staples,
                household_type, excluded_dish_ids | used_main_ids, variety_level
            )
            # 確定枠で上書き
            for day in fixed_mains:
                for meal in fixed_mains[day]:
                    mains_retry[day][meal] = fixed_mains[day][meal]
            result_retry = self._optimize_sides_staged(
                available_dishes, days, people, target,
                staples, mains_retry, enabled_meals, meal_settings,
                preferred_ingredient_ids, preferred_dish_ids,
                variety_level, enabled_nutrients
            )
            if result_retry:
                retry_min = min(result_retry.overall_achievement.values())
                if retry_min > min_achievement:
                    retry_min_nutrient = min(result_retry.overall_achievement, key=result_retry.overall_achievement.get)
                    logger.info(f"Retry improved minimum achievement: {min_achievement:.1f}% ({min_nutrient}) -> {retry_min:.1f}% ({retry_min_nutrient})")
                    result = result_retry

        return result

    def _optimize_sides_staged(
        self,
        dishes: list[Dish],
        days: int,
        people: int,
        target: NutrientTarget,
        staples: dict[int, dict[str, Optional[Dish]]],
        mains: dict[int, dict[str, Optional[Dish]]],
        meals: list[str],
        meal_settings: dict,
        preferred_ingredient_ids: set[int],
        preferred_dish_ids: set[int],
        variety_level: str,
        enabled_nutrients: Optional[list[str]],
        report_progress: Optional[Callable[[str], None]] = None,
    ) -> Optional[MultiDayMenuPlan]:
        """Phase 3: 副菜・汁物を最適化

        主食・主菜は固定し、残りのカテゴリを最適化で埋める。
        """
        from app.domain.entities.enums import DishCategoryEnum

        # 有効な栄養素を決定
        active_nutrients = get_enabled_nutrients(enabled_nutrients)

        # 副菜・汁物・デザートのみフィルタ
        side_categories = {DishCategoryEnum.SIDE, DishCategoryEnum.SOUP, DishCategoryEnum.DESSERT}
        side_dishes = [d for d in dishes if d.category in side_categories]

        if not side_dishes:
            logger.warning("No side dishes available")
            # 主食・主菜だけで結果を構築
            return self._build_result_from_scheduled(
                days, people, target, staples, mains, {}, meals, preferred_ingredient_ids
            )

        # 固定された料理のIDを収集
        fixed_dish_ids: set[int] = set()
        for day in range(1, days + 1):
            for meal in meals:
                if staples.get(day, {}).get(meal):
                    fixed_dish_ids.add(staples[day][meal].id)
                if mains.get(day, {}).get(meal):
                    fixed_dish_ids.add(mains[day][meal].id)

        # 問題定義
        prob = LpProblem("staged_sides_optimization", LpMinimize)

        # 決定変数: 各副菜を各日各食事に割り当てるか
        y = {}
        for d in side_dishes:
            for day in range(1, days + 1):
                for meal in meals:
                    meal_type = MealTypeEnum(meal)
                    if meal_type in d.meal_types:
                        y[(d.id, day, meal)] = LpVariable(
                            f"side_{d.id}_{day}_{meal}", cat="Binary"
                        )

        # 偏差変数
        dev_pos = {}
        dev_neg = {}
        for day in range(1, days + 1):
            dev_pos[day] = {n: LpVariable(f"dev_pos_{day}_{n}", lowBound=0) for n in active_nutrients}
            dev_neg[day] = {n: LpVariable(f"dev_neg_{day}_{n}", lowBound=0) for n in active_nutrients}

        # 目的関数: 栄養偏差最小化（3グループ対応）
        objective_terms = []
        for day in range(1, days + 1):
            for n in active_nutrients:
                weight = NUTRIENT_WEIGHTS.get(n, 1.0)
                normalizer = max(getattr(target, f"{n}_min", 1) if hasattr(target, f"{n}_min") else 1, 1)

                if n in UPPER_TARGET_NUTRIENTS:
                    # グループC（上限重視）: 超過を強くペナルティ
                    penalty = weight * UNDER_PENALTY * dev_pos[day][n] / normalizer

                elif n in RANGE_TARGET_NUTRIENTS:
                    # グループA（範囲型）: 下限未達と上限超過を等しくペナルティ
                    penalty = weight * (UNDER_PENALTY * dev_neg[day][n] + UNDER_PENALTY * dev_pos[day][n]) / normalizer

                else:
                    # グループB（下限重視）: 下限未達を強く、UL超過はさらに強くペナルティ
                    ul_ratio = NUTRIENT_UPPER_LIMIT_RATIO.get(n)
                    if ul_ratio is not None:
                        # ULがある場合: 超過にUPPER_LIMIT_PENALTY
                        penalty = weight * (UNDER_PENALTY * dev_neg[day][n] + UPPER_LIMIT_PENALTY * dev_pos[day][n]) / normalizer
                    else:
                        # ULがない場合: 超過は軽いペナルティ（または0）
                        penalty = weight * (UNDER_PENALTY * dev_neg[day][n] + OVER_PENALTY * dev_pos[day][n]) / normalizer

                objective_terms.append(penalty)

        prob += lpSum(objective_terms)

        # 制約: 日別栄養素
        for day in range(1, days + 1):
            for nutrient in active_nutrients:
                # 固定料理からの栄養素
                fixed_nutrients = 0.0
                for meal in meals:
                    staple = staples.get(day, {}).get(meal)
                    main = mains.get(day, {}).get(meal)
                    if staple:
                        fixed_nutrients += getattr(staple, nutrient, 0) * people
                    if main:
                        fixed_nutrients += getattr(main, nutrient, 0) * people

                # 副菜からの栄養素
                side_nutrients = lpSum(
                    getattr(d, nutrient, 0) * people * y[(d.id, day, meal)]
                    for d in side_dishes
                    for meal in meals
                    if (d.id, day, meal) in y
                )

                total_intake = fixed_nutrients + side_nutrients
                intake_per_person = total_intake / people

                # 3グループ対応の栄養素制約
                if nutrient in UPPER_TARGET_NUTRIENTS:
                    # グループC（上限重視）: x ≤ max を目指す（食塩など）
                    max_val = getattr(target, f"{nutrient}_max")
                    # 上限超過分をdev_posで捕捉
                    prob += intake_per_person - dev_pos[day][nutrient] <= max_val

                elif nutrient in RANGE_TARGET_NUTRIENTS:
                    # グループA（範囲型）: min ≤ x ≤ max を等しく重視
                    min_val = getattr(target, f"{nutrient}_min")
                    max_val = getattr(target, f"{nutrient}_max")
                    # 下限未達分をdev_negで捕捉
                    prob += intake_per_person + dev_neg[day][nutrient] >= min_val
                    # 上限超過分をdev_posで捕捉
                    prob += intake_per_person - dev_pos[day][nutrient] <= max_val

                else:
                    # グループB（下限重視）: x ≥ min を強く目指す
                    if hasattr(target, f"{nutrient}_min"):
                        min_val = getattr(target, f"{nutrient}_min")
                        # 下限未達分をdev_negで捕捉
                        prob += intake_per_person + dev_neg[day][nutrient] >= min_val

                        # UL（耐容上限量）がある場合は上限制約も追加
                        ul_ratio = NUTRIENT_UPPER_LIMIT_RATIO.get(nutrient)
                        if ul_ratio is not None:
                            ul_val = min_val * ul_ratio
                            # 上限超過分をdev_posで捕捉（UPPER_LIMIT_PENALTYで重く罰する）
                            prob += intake_per_person - dev_pos[day][nutrient] <= ul_val

        # 制約: カテゴリ別品数（副菜・汁物）
        for day in range(1, days + 1):
            for meal in meals:
                category_constraints = meal_settings[meal].get(
                    "categories", DEFAULT_MEAL_CATEGORY_CONSTRAINTS[meal]
                )

                for cat, (min_count, max_count) in category_constraints.items():
                    if cat in ["主食", "主菜"]:
                        continue  # 主食・主菜は固定済み

                    cat_dishes = [
                        d for d in side_dishes
                        if d.category.value == cat and (d.id, day, meal) in y
                    ]
                    if cat_dishes:
                        prob += lpSum(y[(d.id, day, meal)] for d in cat_dishes) >= min_count
                        prob += lpSum(y[(d.id, day, meal)] for d in cat_dishes) <= max_count

        # 制約: 料理の使用回数を促進（作り置き効果）
        # 各料理が使われるかどうかを示す変数
        dish_used = {}
        for d in side_dishes:
            dish_used[d.id] = LpVariable(f"dish_used_{d.id}", cat="Binary")
            # 料理が1回でも使われたらdish_used=1
            all_uses = [y[(d.id, day, meal)]
                       for day in range(1, days + 1)
                       for meal in meals
                       if (d.id, day, meal) in y]
            if all_uses:
                prob += dish_used[d.id] * len(all_uses) >= lpSum(all_uses)
                prob += dish_used[d.id] <= lpSum(all_uses)

        # 使用する副菜の種類数を制限（作り置きを促進）
        # variety_level: small=種類少なめ（繰り返し多い）, large=種類多め（多様性重視）
        if variety_level == "small":
            max_distinct = max(days, 5)  # 7日なら7種類まで（繰り返し重視）
        elif variety_level == "large":
            max_distinct = len(side_dishes)  # 制限なし（多様性重視）
        else:  # normal
            max_distinct = days + 3  # 7日なら10種類まで

        prob += lpSum(dish_used[d.id] for d in side_dishes) <= max_distinct

        # 進捗報告: 制約条件適用完了
        if report_progress:
            report_progress("applying_constraints")

        # 制約: 多様性（同じ副菜は連続日で使わない）
        # small: 連続OK（作り置き重視）、large: 連続NG（多様性重視）
        if variety_level == "large":
            for d in side_dishes:
                for meal in meals:
                    for day in range(1, days):
                        key_today = (d.id, day, meal)
                        key_tomorrow = (d.id, day + 1, meal)
                        if key_today in y and key_tomorrow in y:
                            prob += y[key_today] + y[key_tomorrow] <= 1

        # 進捗報告: 計算開始
        if report_progress:
            report_progress("solving")

        # 求解
        prob.solve(self._solver)

        if LpStatus[prob.status] not in ["Optimal", "Not Solved"]:
            logger.warning(f"Optimization failed with status: {LpStatus[prob.status]}")
            return None

        # 進捗報告: 結果整理開始
        if report_progress:
            report_progress("finalizing")

        # 結果抽出: 選択された副菜
        sides: dict[int, dict[str, list[Dish]]] = {}
        for day in range(1, days + 1):
            sides[day] = {meal: [] for meal in meals}
            for d in side_dishes:
                for meal in meals:
                    key = (d.id, day, meal)
                    if key in y and value(y[key]) and value(y[key]) > 0.5:
                        sides[day][meal].append(d)

        return self._build_result_from_scheduled(
            days, people, target, staples, mains, sides, meals, preferred_ingredient_ids
        )

    def _build_result_from_scheduled(
        self,
        days: int,
        people: int,
        target: NutrientTarget,
        staples: dict[int, dict[str, Optional[Dish]]],
        mains: dict[int, dict[str, Optional[Dish]]],
        sides: dict[int, dict[str, list[Dish]]],
        meals: list[str],
        preferred_ingredient_ids: set[int],
    ) -> MultiDayMenuPlan:
        """スケジュールされた料理からMultiDayMenuPlanを構築"""
        cooking_tasks: list[CookingTask] = []
        daily_plans: list[DailyMealAssignment] = []
        overall_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}
        dish_usage: dict[int, dict] = {}  # 料理の使用状況を追跡

        for day in range(1, days + 1):
            day_meals = {"breakfast": [], "lunch": [], "dinner": []}
            day_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}

            for meal in meals:
                # 主食
                staple = staples.get(day, {}).get(meal)
                if staple:
                    day_meals[meal].append(DishPortion(dish=staple, servings=people))
                    for nutrient in ALL_NUTRIENTS:
                        day_nutrients[nutrient] += getattr(staple, nutrient, 0) * people
                    if staple.id not in dish_usage:
                        dish_usage[staple.id] = {"dish": staple, "days": [], "servings": 0}
                    dish_usage[staple.id]["days"].append(day)
                    dish_usage[staple.id]["servings"] += people

                # 主菜
                main = mains.get(day, {}).get(meal)
                if main:
                    day_meals[meal].append(DishPortion(dish=main, servings=people))
                    for nutrient in ALL_NUTRIENTS:
                        day_nutrients[nutrient] += getattr(main, nutrient, 0) * people
                    if main.id not in dish_usage:
                        dish_usage[main.id] = {"dish": main, "days": [], "servings": 0}
                    dish_usage[main.id]["days"].append(day)
                    dish_usage[main.id]["servings"] += people

                # 副菜・汁物
                for side in sides.get(day, {}).get(meal, []):
                    day_meals[meal].append(DishPortion(dish=side, servings=people))
                    for nutrient in ALL_NUTRIENTS:
                        day_nutrients[nutrient] += getattr(side, nutrient, 0) * people
                    if side.id not in dish_usage:
                        dish_usage[side.id] = {"dish": side, "days": [], "servings": 0}
                    dish_usage[side.id]["days"].append(day)
                    dish_usage[side.id]["servings"] += people

            # 1人あたりの栄養素
            day_nutrients_per_person = {k: v / people for k, v in day_nutrients.items()}
            achievement = self._nutrient_calc.calculate_achievement_rate(day_nutrients_per_person, target)

            daily_plans.append(DailyMealAssignment(
                day=day,
                breakfast=day_meals.get("breakfast", []),
                lunch=day_meals.get("lunch", []),
                dinner=day_meals.get("dinner", []),
                total_nutrients={k: round(v, 1) for k, v in day_nutrients_per_person.items()},
                achievement_rate={k: round(v, 1) for k, v in achievement.items()},
            ))

            for n in ALL_NUTRIENTS:
                overall_nutrients[n] += day_nutrients_per_person[n]

        # CookingTaskを生成
        for dish_id, usage in dish_usage.items():
            dish = usage["dish"]
            cook_days = sorted(set(usage["days"]))
            if cook_days:
                cooking_tasks.append(CookingTask(
                    cook_day=cook_days[0],
                    dish=dish,
                    servings=usage["servings"],
                    consume_days=cook_days,
                ))

        # 期間平均
        avg_nutrients = {k: v / days for k, v in overall_nutrients.items()}
        overall_achievement = self._nutrient_calc.calculate_achievement_rate(avg_nutrients, target)

        # 買い物リスト
        shopping_list = self._generate_shopping_list(cooking_tasks, preferred_ingredient_ids)

        # 警告
        warnings = self._nutrient_calc.generate_warnings(avg_nutrients, target)

        return MultiDayMenuPlan(
            plan_id=str(uuid.uuid4()),
            days=days,
            people=people,
            daily_plans=daily_plans,
            cooking_tasks=cooking_tasks,
            shopping_list=shopping_list,
            overall_nutrients={k: round(v, 1) for k, v in overall_nutrients.items()},
            overall_achievement={k: round(v, 1) for k, v in overall_achievement.items()},
            warnings=warnings,
        )

    # ========== Private Methods ==========

    def _estimate_ingredient_category(self, ingredient_name: str) -> str:
        """食材名からカテゴリを推定

        Args:
            ingredient_name: 食材名

        Returns:
            カテゴリ名（肉類, 魚介類, 卵類, 乳類, 豆類, その他）
        """
        name = ingredient_name.lower()

        # 肉類
        if any(kw in name for kw in ["鶏", "豚", "牛", "肉", "ベーコン", "ハム", "ウインナー", "ソーセージ", "ひき肉", "ささみ"]):
            return "肉類"

        # 魚介類
        if any(kw in name for kw in ["鮭", "サバ", "さば", "鯖", "魚", "えび", "いか", "たこ", "貝", "ツナ", "しらす", "ちりめん", "あじ", "ぶり", "まぐろ", "かつお"]):
            return "魚介類"

        # 卵類
        if any(kw in name for kw in ["卵", "たまご", "玉子"]):
            return "卵類"

        # 乳類
        if any(kw in name for kw in ["牛乳", "チーズ", "ヨーグルト", "バター", "クリーム", "乳"]):
            return "乳類"

        # 豆類
        if any(kw in name for kw in ["豆腐", "納豆", "大豆", "厚揚げ", "油揚げ", "豆", "あずき", "枝豆"]):
            return "豆類"

        return "その他"

    def _filter_dishes_by_excluded_ingredients(
        self,
        dishes: list[Dish],
        excluded_ingredient_ids: set[int],
    ) -> list[Dish]:
        """除外食材を含む料理をフィルタリング

        Args:
            dishes: 料理リスト
            excluded_ingredient_ids: 除外食材ID（嫌いな食材）

        Returns:
            除外食材を含まない料理リスト
        """
        if not excluded_ingredient_ids:
            return dishes

        filtered = []
        for dish in dishes:
            # 料理の食材IDを収集
            dish_ingredient_ids = {
                ing.ingredient_id for ing in dish.ingredients
                if ing.ingredient_id is not None
            }
            # 除外食材を含まなければ追加
            if not dish_ingredient_ids & excluded_ingredient_ids:
                filtered.append(dish)

        return filtered

    def _calculate_meal_targets(
        self,
        target: NutrientTarget,
        ratio: float
    ) -> dict[str, float]:
        """1食分の目標値を計算

        サチュレーション閾値を適用: 目標の80%を達成すれば十分
        """
        sat = SATURATION_THRESHOLD
        return {
            # PFC（カロリー・タンパク質・脂質・炭水化物）はサチュレーション適用
            "calories": ((target.calories_min + target.calories_max) / 2) * ratio * sat,
            "protein": ((target.protein_min + target.protein_max) / 2) * ratio * sat,
            "fat": ((target.fat_min + target.fat_max) / 2) * ratio * sat,
            "carbohydrate": ((target.carbohydrate_min + target.carbohydrate_max) / 2) * ratio * sat,
            "fiber": target.fiber_min * ratio * sat,
            # ナトリウムは上限制約なのでサチュレーション不適用
            "sodium": target.sodium_max * ratio,
            # ミネラル・ビタミンはサチュレーション適用
            "potassium": target.potassium_min * ratio * sat,
            "calcium": target.calcium_min * ratio * sat,
            "magnesium": target.magnesium_min * ratio * sat,
            "iron": target.iron_min * ratio * sat,
            "zinc": target.zinc_min * ratio * sat,
            "vitamin_a": target.vitamin_a_min * ratio * sat,
            "vitamin_d": target.vitamin_d_min * ratio * sat,
            "vitamin_e": target.vitamin_e_min * ratio * sat,
            "vitamin_k": target.vitamin_k_min * ratio * sat,
            "vitamin_b1": target.vitamin_b1_min * ratio * sat,
            "vitamin_b2": target.vitamin_b2_min * ratio * sat,
            "vitamin_b6": target.vitamin_b6_min * ratio * sat,
            "vitamin_b12": target.vitamin_b12_min * ratio * sat,
            "niacin": target.niacin_min * ratio * sat,
            "pantothenic_acid": target.pantothenic_acid_min * ratio * sat,
            "biotin": target.biotin_min * ratio * sat,
            "folate": target.folate_min * ratio * sat,
            "vitamin_c": target.vitamin_c_min * ratio * sat,
        }

    def _extract_meal_result(
        self,
        dishes: list[Dish],
        y: dict,
        servings: dict,
        meal_name: str,
    ) -> MealPlan:
        """最適化結果からMealPlanを生成"""
        selected_dishes = []
        totals = {n: 0.0 for n in ALL_NUTRIENTS}

        for d in dishes:
            if value(y[d.id]) and value(y[d.id]) > 0.5:
                serving_amount = value(servings[d.id]) or 1.0
                selected_dishes.append(DishPortion(dish=d, servings=round(serving_amount, 1)))

                for nutrient in ALL_NUTRIENTS:
                    totals[nutrient] += getattr(d, nutrient) * serving_amount

        return MealPlan(
            name=meal_name,
            dishes=selected_dishes,
            total_calories=round(totals["calories"], 1),
            total_protein=round(totals["protein"], 1),
            total_fat=round(totals["fat"], 1),
            total_carbohydrate=round(totals["carbohydrate"], 1),
            total_fiber=round(totals["fiber"], 1),
            total_sodium=round(totals["sodium"], 1),
            total_potassium=round(totals["potassium"], 1),
            total_calcium=round(totals["calcium"], 1),
            total_magnesium=round(totals["magnesium"], 1),
            total_iron=round(totals["iron"], 1),
            total_zinc=round(totals["zinc"], 1),
            total_vitamin_a=round(totals["vitamin_a"], 1),
            total_vitamin_d=round(totals["vitamin_d"], 1),
            total_vitamin_e=round(totals["vitamin_e"], 1),
            total_vitamin_k=round(totals["vitamin_k"], 1),
            total_vitamin_b1=round(totals["vitamin_b1"], 1),
            total_vitamin_b2=round(totals["vitamin_b2"], 1),
            total_vitamin_b6=round(totals["vitamin_b6"], 1),
            total_vitamin_b12=round(totals["vitamin_b12"], 1),
            total_niacin=round(totals["niacin"], 1),
            total_pantothenic_acid=round(totals["pantothenic_acid"], 1),
            total_biotin=round(totals["biotin"], 1),
            total_folate=round(totals["folate"], 1),
            total_vitamin_c=round(totals["vitamin_c"], 1),
        )

    def _normalize_meal_settings(self, meal_settings: Optional[dict]) -> dict:
        """meal_settingsを正規化"""
        if meal_settings is None:
            return {
                meal: {"enabled": True, "categories": DEFAULT_MEAL_CATEGORY_CONSTRAINTS[meal]}
                for meal in ["breakfast", "lunch", "dinner"]
            }

        result = {}
        for meal in ["breakfast", "lunch", "dinner"]:
            if meal not in meal_settings:
                result[meal] = {
                    "enabled": True,
                    "categories": DEFAULT_MEAL_CATEGORY_CONSTRAINTS[meal]
                }
            else:
                setting = meal_settings[meal].copy()
                if "enabled" not in setting:
                    setting["enabled"] = True
                if "categories" not in setting:
                    if "volume" in setting:
                        volume = setting["volume"]
                        setting["categories"] = CATEGORY_CONSTRAINTS_BY_VOLUME.get(
                            volume, DEFAULT_MEAL_CATEGORY_CONSTRAINTS[meal]
                        )
                    else:
                        setting["categories"] = DEFAULT_MEAL_CATEGORY_CONSTRAINTS[meal]
                result[meal] = setting

        return result

    def _create_multi_day_variables(
        self,
        dishes: list[Dish],
        days: int,
        people: int,
        meals: list[str],
    ) -> tuple[dict, dict, dict, dict]:
        """複数日最適化用の決定変数を作成"""
        # x[d, t] = 料理dを日tに調理するか（バイナリ）
        x = {}
        for d in dishes:
            for t in range(1, days + 1):
                x[(d.id, t)] = LpVariable(f"cook_{d.id}_{t}", cat="Binary")

        # s[d, t] = 料理dを日tに調理する人前数
        s = {}
        for d in dishes:
            for t in range(1, days + 1):
                s[(d.id, t)] = LpVariable(
                    f"servings_{d.id}_{t}",
                    lowBound=0,
                    upBound=d.max_servings,
                    cat="Integer"
                )

        # c[d, t, t', m] = 日tに調理した料理dを日t'の食事mで消費するか
        c = {}
        for d in dishes:
            for t in range(1, days + 1):
                for t_prime in range(t, min(t + d.storage_days + 1, days + 1)):
                    for m in meals:
                        meal_type = MealTypeEnum(m)
                        if meal_type in d.meal_types:
                            c[(d.id, t, t_prime, m)] = LpVariable(
                                f"consume_{d.id}_{t}_{t_prime}_{m}",
                                cat="Binary"
                            )

        # q[d, t, t', m] = 消費人前数
        q = {}
        for key in c:
            d_id, t, t_prime, m = key
            q[key] = LpVariable(
                f"qty_{d_id}_{t}_{t_prime}_{m}",
                lowBound=0,
                upBound=people,
                cat="Integer"
            )

        return x, s, c, q

    def _create_deviation_variables(
        self,
        days: int,
        active_nutrients: list[str] | None = None
    ) -> tuple[dict, dict]:
        """偏差変数を作成（有効な栄養素のみ）

        Args:
            days: 日数
            active_nutrients: 有効な栄養素リスト（Noneの場合は全栄養素）
        """
        nutrients = active_nutrients if active_nutrients else ALL_NUTRIENTS
        dev_pos = {}
        dev_neg = {}
        for day in range(1, days + 1):
            dev_pos[day] = {n: LpVariable(f"dev_pos_{day}_{n}", lowBound=0) for n in nutrients}
            dev_neg[day] = {n: LpVariable(f"dev_neg_{day}_{n}", lowBound=0) for n in nutrients}
        return dev_pos, dev_neg

    def _build_multi_day_objective(
        self,
        dishes: list[Dish],
        days: int,
        x: dict,
        dev_pos: dict,
        dev_neg: dict,
        target: NutrientTarget,
        preferred_ingredient_ids: set[int],
        preferred_dish_ids: set[int],
        batch_cooking_level: str,
        active_nutrients: list[str] | None = None,
    ):
        """目的関数を構築（有効な栄養素のみ使用）

        Args:
            active_nutrients: 有効な栄養素リスト（Noneの場合は全栄養素）
        """
        nutrients = active_nutrients if active_nutrients else ALL_NUTRIENTS

        # 栄養バランスからの偏差（有効な栄養素のみ）
        # 厚生労働省の指針に基づく:
        # - 通常栄養素: 推奨量(100%)以上を目指す。未達はペナルティ大、超過はOK
        # - ナトリウム: 目標量(100%)以下を目指す。超過はペナルティ大、未達はOK
        nutrient_deviation_terms = []
        for day in range(1, days + 1):
            for n in nutrients:
                weight = NUTRIENT_WEIGHTS.get(n, 1.0)
                normalizer = max(getattr(target, f"{n}_min", 1) if hasattr(target, f"{n}_min") else 1, 1)

                if n in UPPER_TARGET_NUTRIENTS:
                    # ナトリウム等: 超過を抑制（減らす方向が良い）
                    penalty = weight * (
                        UNDER_PENALTY * dev_pos[day][n] +  # 超過は大きなペナルティ
                        OVER_PENALTY * dev_neg[day][n]     # 未達は軽いペナルティ
                    ) / normalizer
                else:
                    # 通常栄養素: 未達を抑制（増やす方向が良い）
                    penalty = weight * (
                        UNDER_PENALTY * dev_neg[day][n] +  # 未達は大きなペナルティ
                        OVER_PENALTY * dev_pos[day][n]     # 超過は軽いペナルティ
                    ) / normalizer
                nutrient_deviation_terms.append(penalty)

        nutrient_deviation = lpSum(nutrient_deviation_terms)

        # 調理回数
        cooking_count = lpSum(x[(d.id, t)] for d in dishes for t in range(1, days + 1))

        # 重み付け
        batch_cooking_weights = {"small": 0.01, "normal": 0.05, "large": 0.2}
        cooking_weight = batch_cooking_weights.get(batch_cooking_level, 0.05)

        # 手持ち食材ボーナス
        preferred_scores = {}
        if preferred_ingredient_ids:
            for d in dishes:
                matching_count = sum(
                    1 for ing in d.ingredients
                    if ing.food_id in preferred_ingredient_ids
                )
                if matching_count > 0:
                    preferred_scores[d.id] = matching_count * 0.5

        preferred_bonus = lpSum(
            preferred_scores.get(d.id, 0) * lpSum(x[(d.id, t)] for t in range(1, days + 1))
            for d in dishes
            if d.id in preferred_scores
        )

        # お気に入り料理ボーナス
        favorite_bonus = lpSum(
            0.3 * lpSum(x[(d.id, t)] for t in range(1, days + 1))
            for d in dishes
            if d.id in preferred_dish_ids
        )

        return nutrient_deviation + cooking_weight * cooking_count - preferred_bonus - favorite_bonus

    def _add_multi_day_constraints(
        self,
        prob: LpProblem,
        dishes: list[Dish],
        days: int,
        people: int,
        target: NutrientTarget,
        x: dict,
        s: dict,
        c: dict,
        q: dict,
        dev_pos: dict,
        dev_neg: dict,
        meals: list[str],
        meal_settings: dict,
        variety_level: str,
        keep_dish_ids: set[int],
        active_nutrients: list[str] | None = None,
    ):
        """複数日最適化の制約条件を追加（有効な栄養素のみ）

        Args:
            active_nutrients: 有効な栄養素リスト（Noneの場合は全栄養素）
        """
        nutrients = active_nutrients if active_nutrients else ALL_NUTRIENTS

        # C1: 調理しない場合は人前数0
        for d in dishes:
            for t in range(1, days + 1):
                prob += s[(d.id, t)] <= d.max_servings * x[(d.id, t)]
                prob += s[(d.id, t)] >= 1 * x[(d.id, t)]

        # C2: 消費量は調理量と一致
        for d in dishes:
            for t in range(1, days + 1):
                consumptions = []
                for t_prime in range(t, min(t + d.storage_days + 1, days + 1)):
                    for m in meals:
                        key = (d.id, t, t_prime, m)
                        if key in q:
                            consumptions.append(q[key])
                if consumptions:
                    prob += lpSum(consumptions) == s[(d.id, t)]

        # C3: 消費変数と消費量のリンク
        for key in q:
            d_id, t, t_prime, m = key
            prob += q[key] <= people * c[key]
            prob += q[key] >= 1 * c[key]

        # C4: 各日の栄養素制約（有効な栄養素のみ）
        for day in range(1, days + 1):
            for nutrient in nutrients:
                daily_intake = []
                for d in dishes:
                    for t in range(max(1, day - d.storage_days), day + 1):
                        for m in meals:
                            key = (d.id, t, day, m)
                            if key in q:
                                daily_intake.append(getattr(d, nutrient) * q[key])

                if daily_intake:
                    intake_sum = lpSum(daily_intake)
                    intake_per_person = intake_sum / people

                    if nutrient == "sodium":
                        # ナトリウムは上限制約（過剰摂取を避ける）
                        target_val = target.sodium_max
                        prob += intake_per_person <= target_val + dev_pos[day][nutrient]
                    else:
                        if hasattr(target, f"{nutrient}_min"):
                            min_val = getattr(target, f"{nutrient}_min")
                            max_val = getattr(target, f"{nutrient}_max", min_val * 1.5)
                            # サチュレーション: 目標の80%を達成すれば十分
                            # 100%を目指すより、全体的なバランスを重視
                            target_val = (min_val + max_val) / 2 * SATURATION_THRESHOLD
                        else:
                            target_val = 0
                        if target_val > 0:
                            prob += intake_per_person + dev_neg[day][nutrient] - dev_pos[day][nutrient] == target_val

        # C5: カテゴリ別品数制約
        for day in range(1, days + 1):
            for m in meals:
                category_constraints = meal_settings[m].get(
                    "categories", DEFAULT_MEAL_CATEGORY_CONSTRAINTS[m]
                )

                for cat, (min_count, max_count) in category_constraints.items():
                    cat_dishes = [
                        d for d in dishes
                        if d.category.value == cat and MealTypeEnum(m) in d.meal_types
                    ]
                    if cat_dishes:
                        cat_selected = []
                        for d in cat_dishes:
                            for t in range(max(1, day - d.storage_days), day + 1):
                                key = (d.id, t, day, m)
                                if key in c:
                                    cat_selected.append(c[key])
                        if cat_selected:
                            prob += lpSum(cat_selected) >= min_count
                            prob += lpSum(cat_selected) <= max_count

        # C6: 多様性制約
        if variety_level == "large":
            for d in dishes:
                all_consumptions = []
                for t in range(1, days + 1):
                    for t_prime in range(t, min(t + d.storage_days + 1, days + 1)):
                        for m in meals:
                            key = (d.id, t, t_prime, m)
                            if key in c:
                                all_consumptions.append(c[key])
                if all_consumptions:
                    prob += lpSum(all_consumptions) <= 1
        elif variety_level != "small":
            for d in dishes:
                for m in meals:
                    for day in range(1, days):
                        today_consumed = []
                        tomorrow_consumed = []
                        for t in range(max(1, day - d.storage_days), day + 1):
                            key_today = (d.id, t, day, m)
                            if key_today in c:
                                today_consumed.append(c[key_today])
                        for t in range(max(1, day + 1 - d.storage_days), day + 2):
                            key_tomorrow = (d.id, t, day + 1, m)
                            if key_tomorrow in c:
                                tomorrow_consumed.append(c[key_tomorrow])
                        if today_consumed and tomorrow_consumed:
                            prob += lpSum(today_consumed) + lpSum(tomorrow_consumed) <= 1

        # C7: keep_dish_ids
        if keep_dish_ids:
            for dish_id in keep_dish_ids:
                kept_dish = [d for d in dishes if d.id == dish_id]
                if kept_dish:
                    prob += lpSum(x[(dish_id, t)] for t in range(1, days + 1)) >= 1

    def _extract_multi_day_result(
        self,
        dishes: list[Dish],
        days: int,
        people: int,
        target: NutrientTarget,
        x: dict,
        s: dict,
        c: dict,
        q: dict,
        meals: list[str],
        preferred_ingredient_ids: set[int],
    ) -> MultiDayMenuPlan:
        """最適化結果からMultiDayMenuPlanを生成"""
        # 調理タスクを抽出
        cooking_tasks = []
        for d in dishes:
            for t in range(1, days + 1):
                if value(x[(d.id, t)]) and value(x[(d.id, t)]) > 0.5:
                    servings_val = int(round(value(s[(d.id, t)]) or 1))
                    consume_days = []
                    for t_prime in range(t, min(t + d.storage_days + 1, days + 1)):
                        for m in meals:
                            key = (d.id, t, t_prime, m)
                            if key in c and value(c[key]) and value(c[key]) > 0.5:
                                if t_prime not in consume_days:
                                    consume_days.append(t_prime)
                    if consume_days:
                        cooking_tasks.append(CookingTask(
                            cook_day=t,
                            dish=d,
                            servings=servings_val,
                            consume_days=sorted(consume_days),
                        ))

        # 日別の食事割り当て
        daily_plans = []
        overall_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}

        for day in range(1, days + 1):
            day_meals = {"breakfast": [], "lunch": [], "dinner": []}
            day_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}

            for m in meals:
                for d in dishes:
                    for t in range(max(1, day - d.storage_days), day + 1):
                        key = (d.id, t, day, m)
                        if key in q:
                            qty_val = value(q[key])
                            if qty_val and qty_val > 0.5:
                                qty_int = int(round(qty_val))
                                day_meals[m].append(DishPortion(
                                    dish=d,
                                    servings=qty_int,
                                ))
                                for nutrient in ALL_NUTRIENTS:
                                    day_nutrients[nutrient] += getattr(d, nutrient) * qty_int

            day_nutrients_per_person = {k: v / people for k, v in day_nutrients.items()}
            achievement = self._nutrient_calc.calculate_achievement_rate(day_nutrients_per_person, target)

            daily_plans.append(DailyMealAssignment(
                day=day,
                breakfast=day_meals["breakfast"],
                lunch=day_meals["lunch"],
                dinner=day_meals["dinner"],
                total_nutrients={k: round(v, 1) for k, v in day_nutrients_per_person.items()},
                achievement_rate={k: round(v, 1) for k, v in achievement.items()},
            ))

            for n in ALL_NUTRIENTS:
                overall_nutrients[n] += day_nutrients_per_person[n]

        # 期間平均
        avg_nutrients = {k: v / days for k, v in overall_nutrients.items()}
        overall_achievement = self._nutrient_calc.calculate_achievement_rate(avg_nutrients, target)

        # 買い物リスト
        shopping_list = self._generate_shopping_list(cooking_tasks, preferred_ingredient_ids)

        # 警告
        warnings = self._nutrient_calc.generate_warnings(avg_nutrients, target)

        return MultiDayMenuPlan(
            plan_id=str(uuid.uuid4()),
            days=days,
            people=people,
            daily_plans=daily_plans,
            cooking_tasks=cooking_tasks,
            shopping_list=shopping_list,
            overall_nutrients={k: round(v, 1) for k, v in overall_nutrients.items()},
            overall_achievement={k: round(v, 1) for k, v in overall_achievement.items()},
            warnings=warnings,
        )

    def _generate_shopping_list(
        self,
        cooking_tasks: list[CookingTask],
        preferred_ingredient_ids: set[int],
    ) -> list[ShoppingItem]:
        """買い物リストを生成"""
        shopping: dict[str, dict] = {}

        for task in cooking_tasks:
            for ing in task.dish.ingredients:
                if ing.ingredient_id:
                    key = f"ing_{ing.ingredient_id}"
                    name = ing.ingredient_name or ing.food_name or f"食品ID:{ing.food_id}"
                else:
                    raw_name = ing.food_name or f"食品ID:{ing.food_id}"
                    name = self._unit_converter.normalize_food_name(raw_name)
                    key = f"name_{name}"

                if key not in shopping:
                    shopping[key] = {'amount': 0, 'ingredient_ids': set(), 'name': name}
                shopping[key]['amount'] += ing.amount * task.servings
                if ing.ingredient_id:
                    shopping[key]['ingredient_ids'].add(ing.ingredient_id)

        result = []
        for key, data in sorted(shopping.items(), key=lambda x: x[1]['name']):
            name = data['name']
            display_amount, unit = self._unit_converter.convert_to_display_unit(name, data['amount'])
            is_owned = bool(data['ingredient_ids'] & preferred_ingredient_ids)
            result.append(ShoppingItem(
                food_name=name,
                total_amount=round(data['amount'], 1),
                display_amount=display_amount,
                unit=unit,
                category="",
                is_owned=is_owned,
            ))

        return result

    def _fallback_multi_day(
        self,
        dishes: list[Dish],
        days: int,
        people: int,
        target: NutrientTarget,
        preferred_ingredient_ids: set[int],
    ) -> Optional[MultiDayMenuPlan]:
        """フォールバック: 1日ずつ個別に最適化"""
        daily_plans = []
        cooking_tasks = []
        overall_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}
        used_dish_ids: set[int] = set()

        for day in range(1, days + 1):
            day_meals = {}
            day_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}

            for meal_name in ["breakfast", "lunch", "dinner"]:
                result = self.optimize_meal(dishes, target, meal_name, used_dish_ids)
                if result:
                    day_meals[meal_name] = result.dishes
                    for dp in result.dishes:
                        servings = people
                        cooking_tasks.append(CookingTask(
                            cook_day=day,
                            dish=dp.dish,
                            servings=servings,
                            consume_days=[day],
                        ))
                        used_dish_ids.add(dp.dish.id)
                        for nutrient in ALL_NUTRIENTS:
                            day_nutrients[nutrient] += getattr(dp.dish, nutrient) * dp.servings
                else:
                    day_meals[meal_name] = []

            achievement = self._nutrient_calc.calculate_achievement_rate(day_nutrients, target)

            daily_plans.append(DailyMealAssignment(
                day=day,
                breakfast=day_meals.get("breakfast", []),
                lunch=day_meals.get("lunch", []),
                dinner=day_meals.get("dinner", []),
                total_nutrients={k: round(v, 1) for k, v in day_nutrients.items()},
                achievement_rate={k: round(v, 1) for k, v in achievement.items()},
            ))

            for n in ALL_NUTRIENTS:
                overall_nutrients[n] += day_nutrients[n]

        avg_nutrients = {k: v / days for k, v in overall_nutrients.items()}
        overall_achievement = self._nutrient_calc.calculate_achievement_rate(avg_nutrients, target)
        shopping_list = self._generate_shopping_list(cooking_tasks, preferred_ingredient_ids)
        warnings = self._nutrient_calc.generate_warnings(avg_nutrients, target)

        return MultiDayMenuPlan(
            plan_id=str(uuid.uuid4()),
            days=days,
            people=people,
            daily_plans=daily_plans,
            cooking_tasks=cooking_tasks,
            shopping_list=shopping_list,
            overall_nutrients={k: round(v, 1) for k, v in overall_nutrients.items()},
            overall_achievement={k: round(v, 1) for k, v in overall_achievement.items()},
            warnings=warnings,
        )
