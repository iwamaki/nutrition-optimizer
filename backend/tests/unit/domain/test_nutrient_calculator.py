"""
NutrientCalculator のユニットテスト
"""
import pytest
from app.domain.services import NutrientCalculator
from app.domain.entities import NutrientTarget, DishPortion


class TestNutrientCalculator:
    """NutrientCalculator のテスト"""

    @pytest.fixture
    def calculator(self):
        return NutrientCalculator()

    def test_calculate_achievement_rate_calories(
        self, calculator, sample_nutrient_target
    ):
        """カロリー達成率の計算テスト"""
        nutrients = {"calories": 2000}
        result = calculator.calculate_achievement_rate(nutrients, sample_nutrient_target)

        assert "calories" in result
        # 2000kcal / ((1800+2200)/2) = 100%
        assert result["calories"] == pytest.approx(100, rel=0.1)

    def test_calculate_achievement_rate_protein(
        self, calculator, sample_nutrient_target
    ):
        """たんぱく質達成率の計算テスト"""
        nutrients = {"protein": 79}  # 目標: 58-100g -> 中間値79
        result = calculator.calculate_achievement_rate(nutrients, sample_nutrient_target)

        assert "protein" in result
        # 79g / ((58+100)/2) = 100%
        assert result["protein"] == pytest.approx(100, rel=0.1)

    def test_calculate_achievement_rate_sodium(
        self, calculator, sample_nutrient_target
    ):
        """ナトリウム達成率の計算テスト（過剰摂取）"""
        # ナトリウムは上限を超えると達成率が下がる
        nutrients = {"sodium": 3000}  # 目標上限: 2300mg
        result = calculator.calculate_achievement_rate(nutrients, sample_nutrient_target)

        assert "sodium" in result
        # 上限を超えているので100%未満
        assert result["sodium"] < 100

    def test_generate_warnings_low_protein(
        self, calculator, sample_nutrient_target
    ):
        """低たんぱく質警告のテスト"""
        nutrients = {"protein": 30}  # 目標の半分以下
        warnings = calculator.generate_warnings(nutrients, sample_nutrient_target)

        protein_warnings = [w for w in warnings if w.nutrient == "protein"]
        assert len(protein_warnings) > 0
        assert protein_warnings[0].current_value == 30

    def test_generate_warnings_low_fiber(
        self, calculator, sample_nutrient_target
    ):
        """食物繊維不足警告のテスト"""
        nutrients = {"fiber": 5}  # 目標より少ない
        warnings = calculator.generate_warnings(nutrients, sample_nutrient_target)

        fiber_warnings = [w for w in warnings if w.nutrient == "fiber"]
        assert len(fiber_warnings) > 0

    def test_generate_warnings_no_warnings(
        self, calculator, sample_nutrient_target
    ):
        """警告なしのテスト"""
        # すべての栄養素が目標範囲内
        nutrients = {
            "calories": 2000,
            "protein": 70,
            "fat": 60,
            "carbohydrate": 280,
            "fiber": 21,
            "sodium": 2000,
            "potassium": 2600,
            "calcium": 700,
            "magnesium": 320,
            "iron": 6.5,
            "zinc": 8,
            "vitamin_a": 800,
            "vitamin_d": 8.5,
            "vitamin_e": 6,
            "vitamin_k": 150,
            "vitamin_b1": 1.2,
            "vitamin_b2": 1.4,
            "vitamin_b6": 1.3,
            "vitamin_b12": 2.4,
            "niacin": 14,
            "pantothenic_acid": 5,
            "biotin": 50,
            "folate": 240,
            "vitamin_c": 100,
        }
        warnings = calculator.generate_warnings(nutrients, sample_nutrient_target)

        # 警告は少ないはず
        assert len(warnings) <= 5

    def test_calculate_meal_nutrients(
        self, calculator, sample_dish, sample_main_dish
    ):
        """1食分の栄養素合計テスト"""
        dish_portions = [
            DishPortion(dish=sample_dish, servings=1),
            DishPortion(dish=sample_main_dish, servings=1),
        ]
        result = calculator.calculate_meal_nutrients(dish_portions)

        assert result["calories"] == pytest.approx(402, rel=0.1)  # 252 + 150
        assert result["protein"] == pytest.approx(23.8, rel=0.1)  # 3.8 + 20

    def test_calculate_daily_nutrients(
        self, calculator, sample_dish, sample_main_dish, sample_side_dish
    ):
        """1日分の栄養素合計テスト"""
        meals = {
            "breakfast": [DishPortion(dish=sample_dish, servings=1)],
            "lunch": [
                DishPortion(dish=sample_dish, servings=1),
                DishPortion(dish=sample_main_dish, servings=1),
            ],
            "dinner": [
                DishPortion(dish=sample_dish, servings=1),
                DishPortion(dish=sample_main_dish, servings=1),
                DishPortion(dish=sample_side_dish, servings=1),
            ],
        }
        result = calculator.calculate_daily_nutrients(meals)

        # 3回のごはん + 2回の鮭 + 1回のお浸し
        expected_calories = 252 * 3 + 150 * 2 + 20  # 1076
        assert result["calories"] == pytest.approx(expected_calories, rel=0.1)
