"""Meal plan domain entities."""

from pydantic import BaseModel, Field

from app.domain.entities.dish import DishPortion


class MealPlan(BaseModel):
    """1食分のメニュー（料理ベース）"""
    name: str  # breakfast, lunch, dinner
    dishes: list[DishPortion]
    # 基本栄養素
    total_calories: float
    total_protein: float
    total_fat: float
    total_carbohydrate: float
    total_fiber: float
    # ミネラル
    total_sodium: float
    total_potassium: float = 0
    total_calcium: float
    total_magnesium: float = 0
    total_iron: float
    total_zinc: float = 0
    # ビタミン
    total_vitamin_a: float
    total_vitamin_d: float
    total_vitamin_e: float = 0
    total_vitamin_k: float = 0
    total_vitamin_b1: float = 0
    total_vitamin_b2: float = 0
    total_vitamin_b6: float = 0
    total_vitamin_b12: float = 0
    total_niacin: float = 0
    total_pantothenic_acid: float = 0
    total_biotin: float = 0
    total_folate: float = 0
    total_vitamin_c: float


class DailyMenuPlan(BaseModel):
    """1日分のメニュープラン（料理ベース）"""
    breakfast: MealPlan
    lunch: MealPlan
    dinner: MealPlan
    total_nutrients: dict[str, float]
    achievement_rate: dict[str, float]


class DailyMealAssignment(BaseModel):
    """1日分の食事割り当て（複数日プラン用）"""
    day: int = Field(ge=1)
    breakfast: list[DishPortion]
    lunch: list[DishPortion]
    dinner: list[DishPortion]
    total_nutrients: dict[str, float]
    achievement_rate: dict[str, float]


class NutrientWarning(BaseModel):
    """栄養素に関する警告"""
    nutrient: str = Field(description="栄養素名")
    message: str = Field(description="警告メッセージ")
    current_value: float = Field(description="現在値")
    target_value: float = Field(description="目標値")
    deficit_percent: float = Field(description="不足率(%)")


class MultiDayMenuPlan(BaseModel):
    """複数日メニュープラン"""
    plan_id: str = Field(description="プランID（調整時に使用）")
    days: int
    people: int
    daily_plans: list[DailyMealAssignment]
    cooking_tasks: list = Field(description="調理計画")  # CookingTask list
    shopping_list: list = Field(description="買い物リスト")  # ShoppingItem list
    overall_nutrients: dict[str, float] = Field(description="期間合計栄養素")
    overall_achievement: dict[str, float] = Field(description="期間全体の達成率")
    warnings: list[NutrientWarning] = Field(default_factory=list, description="栄養素警告")
