"""
複数日献立最適化ユースケース

クリーンアーキテクチャ: application層
"""
from dataclasses import dataclass
from typing import Optional

from app.domain.entities import NutrientTarget, MultiDayMenuPlan
from app.domain.interfaces import DishRepositoryInterface
from app.infrastructure.optimizer import PuLPSolver


@dataclass
class OptimizeMultiDayMenuUseCase:
    """複数日×複数人のメニューを最適化するユースケース"""

    dish_repo: DishRepositoryInterface
    solver: PuLPSolver

    def execute(
        self,
        days: int = 1,
        people: int = 1,
        target: Optional[NutrientTarget] = None,
        excluded_allergens: Optional[list[str]] = None,
        excluded_dish_ids: Optional[list[int]] = None,
        keep_dish_ids: Optional[list[int]] = None,
        preferred_ingredient_ids: Optional[list[int]] = None,
        preferred_dish_ids: Optional[list[int]] = None,
        batch_cooking_level: str = "normal",
        volume_level: str = "normal",
        variety_level: str = "normal",
        meal_settings: Optional[dict] = None,
    ) -> Optional[MultiDayMenuPlan]:
        """複数日献立を最適化

        Args:
            days: 日数（1-7）
            people: 人数（1-6）
            target: 栄養素目標（1人1日あたり）
            excluded_allergens: 除外アレルゲン
            excluded_dish_ids: 除外料理ID
            keep_dish_ids: 必ず含める料理ID
            preferred_ingredient_ids: 優先食材ID（手持ち食材）
            preferred_dish_ids: 優先料理ID（お気に入り）
            batch_cooking_level: 作り置き優先度
            volume_level: 献立ボリューム
            variety_level: 料理の繰り返し
            meal_settings: 朝昼夜別の設定

        Returns:
            最適化された献立プラン
        """
        target = target or NutrientTarget()

        # 料理を取得
        if excluded_allergens:
            dishes = self.dish_repo.find_excluding_allergens(excluded_allergens)
        else:
            dishes = self.dish_repo.find_all(limit=1000)

        if not dishes:
            return None

        # 除外料理をフィルタ
        excluded_ids = set(excluded_dish_ids or [])
        dishes = [d for d in dishes if d.id not in excluded_ids]

        # ボリュームレベルによる目標調整
        target = self._adjust_target_for_volume(target, volume_level)

        # 最適化実行
        result = self.solver.solve_multi_day(
            dishes=dishes,
            days=days,
            people=people,
            target=target,
            excluded_dish_ids=excluded_ids,
            keep_dish_ids=set(keep_dish_ids or []),
            preferred_ingredient_ids=set(preferred_ingredient_ids or []),
            preferred_dish_ids=set(preferred_dish_ids or []),
            batch_cooking_level=batch_cooking_level,
            variety_level=variety_level,
            meal_settings=meal_settings,
        )

        return result

    def _adjust_target_for_volume(
        self,
        target: NutrientTarget,
        volume_level: str
    ) -> NutrientTarget:
        """ボリュームレベルに応じて目標を調整"""
        volume_multipliers = {"small": 0.8, "normal": 1.0, "large": 1.2}
        mult = volume_multipliers.get(volume_level, 1.0)

        if mult == 1.0:
            return target

        return NutrientTarget(
            calories_min=target.calories_min * mult,
            calories_max=target.calories_max * mult,
            protein_min=target.protein_min * mult,
            protein_max=target.protein_max * mult,
            fat_min=target.fat_min * mult,
            fat_max=target.fat_max * mult,
            carbohydrate_min=target.carbohydrate_min * mult,
            carbohydrate_max=target.carbohydrate_max * mult,
            fiber_min=target.fiber_min * mult,
            sodium_max=target.sodium_max * mult,
            # ミネラル・ビタミンは変えない
            potassium_min=target.potassium_min,
            calcium_min=target.calcium_min,
            magnesium_min=target.magnesium_min,
            iron_min=target.iron_min,
            zinc_min=target.zinc_min,
            vitamin_a_min=target.vitamin_a_min,
            vitamin_d_min=target.vitamin_d_min,
            vitamin_e_min=target.vitamin_e_min,
            vitamin_k_min=target.vitamin_k_min,
            vitamin_b1_min=target.vitamin_b1_min,
            vitamin_b2_min=target.vitamin_b2_min,
            vitamin_b6_min=target.vitamin_b6_min,
            vitamin_b12_min=target.vitamin_b12_min,
            niacin_min=target.niacin_min,
            pantothenic_acid_min=target.pantothenic_acid_min,
            biotin_min=target.biotin_min,
            folate_min=target.folate_min,
            vitamin_c_min=target.vitamin_c_min,
        )
