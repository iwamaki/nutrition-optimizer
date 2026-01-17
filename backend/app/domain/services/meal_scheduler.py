"""
MealScheduler - 段階的献立決定サービス

Phase 1: 主食スケジューリング（ルールベース）
Phase 2: 主菜スケジューリング（たんぱく源ローテーション）
Phase 3: 副菜・汁物は既存のPuLP最適化に委譲
"""

import random
import logging
from collections import defaultdict
from typing import Optional

from app.domain.entities import Dish
from app.domain.entities.enums import DishCategoryEnum

logger = logging.getLogger(__name__)


# たんぱく源カテゴリのマッピング
PROTEIN_SOURCE_CATEGORIES = {
    "meat": "肉類",
    "fish": "魚介類",
    "egg": "卵類",
    "dairy": "乳類",
    "legume": "豆類",
}

# たんぱく源ローテーション順序
PROTEIN_ROTATION_ORDER = ["meat", "fish", "egg", "legume", "meat", "fish", "dairy"]

# 主食と味付けの相性
FLAVOR_COMPATIBILITY = {
    "rice": ["和風", "中華"],        # ご飯系 → 和風・中華
    "bread": ["洋風"],               # パン系 → 洋風
    "noodle": ["和風", "中華", "洋風"],  # 麺系 → 何でもOK
}

# 主食タイプの判定キーワード
STAPLE_TYPE_KEYWORDS = {
    "rice": ["ご飯", "ライス", "丼", "おにぎり", "チャーハン", "カレー", "ハヤシ", "オムライス", "玄米"],
    "bread": ["パン", "トースト", "オートミール"],
    "noodle": ["麺", "パスタ", "うどん", "そば", "ラーメン", "焼きそば", "ナポリタン", "ペペロンチーノ", "カルボナーラ"],
}


def get_protein_source(dish: Dish) -> Optional[str]:
    """料理の主たんぱく源を推定

    食材のカテゴリから、最も量が多いたんぱく源カテゴリを返す。

    Returns:
        "meat", "fish", "egg", "dairy", "legume" のいずれか、または None
    """
    protein_amounts: dict[str, float] = defaultdict(float)

    for ing in dish.ingredients:
        # ingredient経由でcategoryを取得（ingredient_nameからカテゴリを推定）
        if not ing.ingredient_id:
            continue

        # 料理にはingredient_nameが設定されているはず
        # ただしcategoryは直接持っていないので、食材IDから推定する必要がある
        # ここでは簡易的に、ingredient_idとマッピングを使う
        # 実際の運用では、DishIngredientにcategoryを追加するか、
        # リポジトリ経由でIngredientを取得する

        # 食材カテゴリ情報を取得するため、グローバルなマッピングを使用
        category = _get_ingredient_category(ing.ingredient_id)
        if category:
            for key, cat_name in PROTEIN_SOURCE_CATEGORIES.items():
                if category == cat_name:
                    protein_amounts[key] += ing.amount
                    break

    if not protein_amounts:
        return None

    # 最も量が多いカテゴリを返す
    return max(protein_amounts, key=protein_amounts.get)


def get_staple_type(dish: Dish) -> str:
    """主食の種類を判定

    Returns:
        "rice", "bread", "noodle" のいずれか
    """
    name = dish.name
    for staple_type, keywords in STAPLE_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name:
                return staple_type
    return "rice"  # デフォルトはご飯


# 食材ID→カテゴリのマッピング（起動時にロード）
_ingredient_category_cache: dict[int, str] = {}


def load_ingredient_categories(ingredients: list[tuple[int, str]]) -> None:
    """食材カテゴリのキャッシュをロード

    Args:
        ingredients: [(ingredient_id, category), ...] のリスト
    """
    global _ingredient_category_cache
    _ingredient_category_cache = {ing_id: cat for ing_id, cat in ingredients}
    logger.info(f"Loaded {len(_ingredient_category_cache)} ingredient categories")


def _get_ingredient_category(ingredient_id: int) -> Optional[str]:
    """食材IDからカテゴリを取得"""
    return _ingredient_category_cache.get(ingredient_id)


class MealScheduler:
    """段階的献立決定スケジューラ

    Phase 1: 主食をルールベースでスケジューリング
    Phase 2: 主菜をたんぱく源ローテーションでスケジューリング
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: 乱数シード（再現性のため）
        """
        self._rng = random.Random(seed)

    def schedule_staples(
        self,
        dishes: list[Dish],
        days: int,
        meals: list[str],
        household_type: str = "single",
    ) -> dict[int, dict[str, Optional[Dish]]]:
        """Phase 1: 主食のスケジューリング

        ルール:
        - ご飯系は作り置き可能なら連続配置
        - パンは朝食優先
        - 麺は連続しない
        - 一人暮らしは簡便性重視

        Args:
            dishes: 主食カテゴリの料理リスト
            days: 日数
            meals: 食事タイプリスト ["breakfast", "lunch", "dinner"]
            household_type: 世帯タイプ（"single", "couple", "family"）

        Returns:
            {day: {meal: Dish or None}} の形式
        """
        # 主食カテゴリのみフィルタ
        staple_dishes = [d for d in dishes if d.category == DishCategoryEnum.STAPLE]

        if not staple_dishes:
            logger.warning("No staple dishes available")
            return {day: {meal: None for meal in meals} for day in range(1, days + 1)}

        # 主食を種類別に分類
        rice_dishes = [d for d in staple_dishes if get_staple_type(d) == "rice"]
        bread_dishes = [d for d in staple_dishes if get_staple_type(d) == "bread"]
        noodle_dishes = [d for d in staple_dishes if get_staple_type(d) == "noodle"]

        # デフォルト（ご飯）がない場合は全体から選択
        if not rice_dishes:
            rice_dishes = staple_dishes

        schedule: dict[int, dict[str, Optional[Dish]]] = {}
        last_type: Optional[str] = None

        for day in range(1, days + 1):
            schedule[day] = {}
            for meal in meals:
                dish = self._select_staple_for_meal(
                    meal, day, last_type,
                    rice_dishes, bread_dishes, noodle_dishes,
                    household_type
                )
                schedule[day][meal] = dish
                if dish:
                    last_type = get_staple_type(dish)

        logger.info(f"Scheduled staples for {days} days, {len(meals)} meals/day")
        return schedule

    def _select_staple_for_meal(
        self,
        meal: str,
        day: int,
        last_type: Optional[str],
        rice_dishes: list[Dish],
        bread_dishes: list[Dish],
        noodle_dishes: list[Dish],
        household_type: str,
    ) -> Optional[Dish]:
        """特定の食事に対する主食を選択"""
        if meal == "breakfast":
            # 朝食: パン優先、なければご飯系
            if bread_dishes and self._rng.random() < 0.6:
                return self._rng.choice(bread_dishes)
            # パンがなければシンプルなご飯系
            simple_rice = [d for d in rice_dishes if "おにぎり" in d.name or "ご飯" in d.name]
            if simple_rice:
                return self._rng.choice(simple_rice)
            return self._rng.choice(rice_dishes) if rice_dishes else None

        # 昼・夜
        # 麺は連続させない
        if last_type == "noodle":
            candidates = rice_dishes
        else:
            # 3日周期でローテーション
            cycle = (day - 1) % 3
            if cycle == 0:
                candidates = rice_dishes
            elif cycle == 1 and noodle_dishes:
                candidates = noodle_dishes
            else:
                candidates = rice_dishes

        # 一人暮らしは丼物・一品完結型を優先
        if household_type == "single" and meal in ["lunch", "dinner"]:
            one_dish_meals = [d for d in candidates if any(
                kw in d.name for kw in ["丼", "カレー", "ハヤシ", "オムライス", "チャーハン", "ラーメン", "パスタ"]
            )]
            if one_dish_meals and self._rng.random() < 0.4:
                return self._rng.choice(one_dish_meals)

        return self._rng.choice(candidates) if candidates else None

    def schedule_mains(
        self,
        dishes: list[Dish],
        days: int,
        meals: list[str],
        scheduled_staples: dict[int, dict[str, Optional[Dish]]],
        household_type: str = "single",
        excluded_dish_ids: Optional[set[int]] = None,
        variety_level: str = "normal",
    ) -> dict[int, dict[str, Optional[Dish]]]:
        """Phase 2: 主菜のスケジューリング

        ルール:
        - たんぱく源をローテーション（肉→魚→卵→豆腐...）
        - 同じたんぱく源は最低2日空ける（variety_levelで調整可能）
        - 主食との相性を考慮（パン→洋風、ご飯→和風/中華）
        - 作り置き可能な料理は連続消費OK

        variety_level:
        - small: 作り置き重視（料理繰り返し多い、ローテーション緩め）
        - normal: バランス
        - large: 多様性重視（毎食違う料理、ローテーション厳密）

        Args:
            dishes: 主菜カテゴリの料理リスト
            days: 日数
            meals: 食事タイプリスト
            scheduled_staples: Phase 1で決まった主食
            household_type: 世帯タイプ
            excluded_dish_ids: 除外する料理ID
            variety_level: 多様性レベル（small/normal/large）

        Returns:
            {day: {meal: Dish or None}} の形式
        """
        excluded_dish_ids = excluded_dish_ids or set()

        # 主菜カテゴリのみフィルタ
        main_dishes = [
            d for d in dishes
            if d.category == DishCategoryEnum.MAIN and d.id not in excluded_dish_ids
        ]

        if not main_dishes:
            logger.warning("No main dishes available")
            return {day: {meal: None for meal in meals} for day in range(1, days + 1)}

        # たんぱく源別に分類
        dishes_by_protein: dict[str, list[Dish]] = defaultdict(list)
        dishes_without_protein: list[Dish] = []

        for dish in main_dishes:
            protein = get_protein_source(dish)
            if protein:
                dishes_by_protein[protein].append(dish)
            else:
                dishes_without_protein.append(dish)

        logger.info(f"Main dishes by protein: {[(k, len(v)) for k, v in dishes_by_protein.items()]}")

        schedule: dict[int, dict[str, Optional[Dish]]] = {}
        protein_index = 0
        recent_proteins: list[str] = []  # 直近のたんぱく源（連続回避用）
        used_dishes: dict[int, int] = {}  # {dish_id: last_used_day} 使用日を追跡

        # variety_levelによるパラメータ調整
        # small: 作り置き重視（同じ料理を繰り返す、ローテーションなし）
        # normal: バランス
        # large: 多様性重視（毎食違う、厳密ローテーション）
        if variety_level == "small":
            reuse_gap = 0  # 作り置き期間内なら即再利用可能
            protein_history_len = 0  # ローテーションなし（同じたんぱく源OK）
        elif variety_level == "large":
            reuse_gap = days + 1  # 期間中は再利用しない
            protein_history_len = 3  # 直前3回は回避（厳密ローテーション）
        else:  # normal
            reuse_gap = 2  # 2日空ける
            protein_history_len = 2  # 直前2回は回避

        for day in range(1, days + 1):
            schedule[day] = {}
            for meal in meals:
                # その日使用可能な料理（作り置き期間考慮）
                available_dishes = set()
                for d in main_dishes:
                    if d.id not in used_dishes:
                        available_dishes.add(d.id)
                    else:
                        last_day = used_dishes[d.id]
                        # storage_daysを考慮: 作り置き可能なら繰り返しOK
                        if variety_level == "small" and d.storage_days > 0:
                            if day <= last_day + d.storage_days:
                                available_dishes.add(d.id)
                        elif day - last_day > reuse_gap:
                            available_dishes.add(d.id)

                # 朝食は主菜なし or 軽め
                if meal == "breakfast":
                    breakfast_main = self._select_breakfast_main(
                        main_dishes, dishes_by_protein, available_dishes, variety_level
                    )
                    schedule[day][meal] = breakfast_main
                    if breakfast_main:
                        used_dishes[breakfast_main.id] = day
                    continue

                # 昼・夜: たんぱく源ローテーション
                dish = self._select_main_with_rotation(
                    day, meal,
                    dishes_by_protein,
                    scheduled_staples,
                    protein_index,
                    recent_proteins,
                    available_dishes,
                    household_type,
                    protein_history_len,
                )

                schedule[day][meal] = dish
                if dish:
                    protein = get_protein_source(dish)
                    if protein:
                        recent_proteins.append(protein)
                        if len(recent_proteins) > protein_history_len + 1:
                            recent_proteins.pop(0)
                        protein_index += 1
                    used_dishes[dish.id] = day

        logger.info(f"Scheduled mains for {days} days (variety={variety_level})")
        return schedule

    def _select_breakfast_main(
        self,
        main_dishes: list[Dish],
        dishes_by_protein: dict[str, list[Dish]],
        available_dish_ids: set[int],
        variety_level: str = "normal",
    ) -> Optional[Dish]:
        """朝食用の主菜を選択（軽め）"""
        # 朝食向きの主菜: 卵料理、納豆など
        breakfast_keywords = ["卵", "納豆", "ベーコン", "ウインナー", "ハム", "目玉焼き", "スクランブル", "オムレツ"]
        breakfast_mains = [
            d for d in main_dishes
            if any(kw in d.name for kw in breakfast_keywords)
            and d.id in available_dish_ids
            and "breakfast" in [mt.value for mt in d.meal_types]
        ]

        if breakfast_mains:
            return self._rng.choice(breakfast_mains)
        return None

    def _select_main_with_rotation(
        self,
        day: int,
        meal: str,
        dishes_by_protein: dict[str, list[Dish]],
        scheduled_staples: dict[int, dict[str, Optional[Dish]]],
        protein_index: int,
        recent_proteins: list[str],
        available_dish_ids: set[int],
        household_type: str,
        protein_history_len: int = 2,
    ) -> Optional[Dish]:
        """たんぱく源ローテーションで主菜を選択"""
        # 主食との相性を確認
        staple = scheduled_staples.get(day, {}).get(meal)
        compatible_flavors = ["和風", "洋風", "中華"]  # デフォルトは全て

        if staple:
            staple_type = get_staple_type(staple)
            compatible_flavors = FLAVOR_COMPATIBILITY.get(staple_type, compatible_flavors)

        # protein_history_len=0: ローテーションなし（作り置き重視）
        if protein_history_len == 0:
            # 相性の良い料理から選択（たんぱく源は問わない）
            candidates = []
            for protein, dish_list in dishes_by_protein.items():
                candidates.extend([
                    d for d in dish_list
                    if d.id in available_dish_ids
                    and d.flavor_profile in compatible_flavors
                    and meal in [mt.value for mt in d.meal_types]
                ])

            if not candidates:
                # 相性を無視
                for protein, dish_list in dishes_by_protein.items():
                    candidates.extend([
                        d for d in dish_list
                        if d.id in available_dish_ids
                        and meal in [mt.value for mt in d.meal_types]
                    ])

            if candidates:
                return self._rng.choice(candidates)
            return None

        # 次のたんぱく源を決定（ローテーション）
        target_protein = PROTEIN_ROTATION_ORDER[protein_index % len(PROTEIN_ROTATION_ORDER)]

        # 連続回避: 直近N回と同じたんぱく源は避ける
        attempts = 0
        while target_protein in recent_proteins[-protein_history_len:] and attempts < len(PROTEIN_ROTATION_ORDER):
            protein_index += 1
            target_protein = PROTEIN_ROTATION_ORDER[protein_index % len(PROTEIN_ROTATION_ORDER)]
            attempts += 1

        # 候補を取得（available_dish_idsに含まれるもののみ）
        candidates = [
            d for d in dishes_by_protein.get(target_protein, [])
            if d.id in available_dish_ids
            and d.flavor_profile in compatible_flavors
            and meal in [mt.value for mt in d.meal_types]
        ]

        # 候補がなければ相性を無視
        if not candidates:
            candidates = [
                d for d in dishes_by_protein.get(target_protein, [])
                if d.id in available_dish_ids
                and meal in [mt.value for mt in d.meal_types]
            ]

        # それでもなければ他のたんぱく源から
        if not candidates:
            for alt_protein in PROTEIN_ROTATION_ORDER:
                if alt_protein != target_protein:
                    candidates = [
                        d for d in dishes_by_protein.get(alt_protein, [])
                        if d.id in available_dish_ids
                        and meal in [mt.value for mt in d.meal_types]
                    ]
                    if candidates:
                        break

        # 最終フォールバック: 全料理から選択
        if not candidates:
            for protein, dish_list in dishes_by_protein.items():
                candidates = [
                    d for d in dish_list
                    if meal in [mt.value for mt in d.meal_types]
                ]
                if candidates:
                    break

        if candidates:
            return self._rng.choice(candidates)
        return None

    def get_scheduled_nutrients(
        self,
        staples: dict[int, dict[str, Optional[Dish]]],
        mains: dict[int, dict[str, Optional[Dish]]],
    ) -> dict[int, dict[str, float]]:
        """スケジュール済み料理の日別栄養素を計算

        Args:
            staples: 主食スケジュール
            mains: 主菜スケジュール

        Returns:
            {day: {nutrient: value}} の形式
        """
        nutrients_by_day: dict[int, dict[str, float]] = {}
        nutrient_keys = [
            "calories", "protein", "fat", "carbohydrate", "fiber",
            "sodium", "potassium", "calcium", "magnesium", "iron", "zinc",
            "vitamin_a", "vitamin_d", "vitamin_e", "vitamin_k",
            "vitamin_b1", "vitamin_b2", "vitamin_b6", "vitamin_b12",
            "niacin", "pantothenic_acid", "biotin", "folate", "vitamin_c",
        ]

        for day in staples.keys():
            nutrients_by_day[day] = {k: 0.0 for k in nutrient_keys}

            for meal in staples[day].keys():
                # 主食の栄養素
                staple = staples[day].get(meal)
                if staple:
                    for key in nutrient_keys:
                        nutrients_by_day[day][key] += getattr(staple, key, 0)

                # 主菜の栄養素
                main = mains.get(day, {}).get(meal)
                if main:
                    for key in nutrient_keys:
                        nutrients_by_day[day][key] += getattr(main, key, 0)

        return nutrients_by_day
