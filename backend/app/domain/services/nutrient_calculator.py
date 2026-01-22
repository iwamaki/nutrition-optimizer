"""Nutrient calculation service."""


from app.domain.entities.food import NutrientTarget
from app.domain.entities.dish import DishPortion
from app.domain.entities.meal_plan import NutrientWarning
from app.domain.services.constants import ALL_NUTRIENTS


class NutrientCalculator:
    """栄養素計算サービス"""

    def calculate_meal_nutrients(
        self,
        dish_portions: list[DishPortion],
    ) -> dict[str, float]:
        """
        1食分の栄養素合計を計算

        Args:
            dish_portions: 料理と分量のリスト

        Returns:
            栄養素名をキーとした合計値の辞書
        """
        totals = {n: 0.0 for n in ALL_NUTRIENTS}

        for dp in dish_portions:
            for nutrient in ALL_NUTRIENTS:
                value = getattr(dp.dish, nutrient, 0) or 0
                totals[nutrient] += value * dp.servings

        return totals

    def calculate_daily_nutrients(
        self,
        meals: dict[str, list[DishPortion]],
    ) -> dict[str, float]:
        """
        1日分の栄養素合計を計算

        Args:
            meals: 食事名をキーとした料理リストの辞書
                   例: {"breakfast": [...], "lunch": [...], "dinner": [...]}

        Returns:
            栄養素名をキーとした合計値の辞書
        """
        totals = {n: 0.0 for n in ALL_NUTRIENTS}

        for meal_name, dish_portions in meals.items():
            meal_nutrients = self.calculate_meal_nutrients(dish_portions)
            for nutrient in ALL_NUTRIENTS:
                totals[nutrient] += meal_nutrients[nutrient]

        return totals

    def calculate_achievement_rate(
        self,
        nutrients: dict[str, float],
        target: NutrientTarget,
    ) -> dict[str, float]:
        """
        栄養素達成率を計算

        Args:
            nutrients: 実際の栄養素値
            target: 目標値

        Returns:
            栄養素名をキーとした達成率(%)の辞書
        """
        achievement = {}

        for n in ALL_NUTRIENTS:
            val = nutrients.get(n, 0)

            if n == "sodium":
                # ナトリウムは上限目標（低いほど良い）
                target_val = target.sodium_max
                if val > 0:
                    achievement[n] = min(100, target_val / max(val, 1) * 100)
                else:
                    achievement[n] = 100
            else:
                # その他は下限目標（高いほど良い）
                # _min を100%達成の基準とする（推奨量達成 = 100%）
                if hasattr(target, f"{n}_min"):
                    target_val = getattr(target, f"{n}_min")
                else:
                    target_val = 0

                if target_val > 0:
                    achievement[n] = val / target_val * 100
                else:
                    achievement[n] = 100

        return achievement

    def generate_warnings(
        self,
        nutrients: dict[str, float],
        target: NutrientTarget,
        threshold: float = 80.0,
    ) -> list[NutrientWarning]:
        """
        栄養素不足の警告を生成

        Args:
            nutrients: 実際の栄養素値
            target: 目標値
            threshold: 警告を出す達成率の閾値(%)

        Returns:
            警告リスト
        """
        warnings = []
        achievement = self.calculate_achievement_rate(nutrients, target)

        # 警告対象の栄養素（重要度の高いもの）
        important_nutrients = [
            ("protein", "たんぱく質"),
            ("fiber", "食物繊維"),
            ("calcium", "カルシウム"),
            ("iron", "鉄分"),
            ("vitamin_d", "ビタミンD"),
            ("vitamin_b12", "ビタミンB12"),
            ("folate", "葉酸"),
            ("vitamin_c", "ビタミンC"),
        ]

        for nutrient, display_name in important_nutrients:
            rate = achievement.get(nutrient, 100)
            if rate < threshold:
                target_val = self._get_target_value(target, nutrient)
                current_val = nutrients.get(nutrient, 0)

                warnings.append(
                    NutrientWarning(
                        nutrient=nutrient,
                        message=f"{display_name}が目標の{rate:.0f}%です",
                        current_value=round(current_val, 1),
                        target_value=round(target_val, 1),
                        deficit_percent=round(100 - rate, 1),
                    )
                )

        return warnings

    def _get_target_value(self, target: NutrientTarget, nutrient: str) -> float:
        """栄養素の目標値を取得（_min を基準とする）"""
        if nutrient == "sodium":
            return target.sodium_max

        if hasattr(target, f"{nutrient}_min"):
            return getattr(target, f"{nutrient}_min")

        return 0
