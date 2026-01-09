from pydantic import BaseModel, Field
from typing import Optional


class Food(BaseModel):
    """食品データモデル"""
    id: int
    name: str
    category: str
    calories: float = Field(ge=0, description="kcal/100g")
    protein: float = Field(ge=0, description="g/100g")
    fat: float = Field(ge=0, description="g/100g")
    carbohydrate: float = Field(ge=0, description="g/100g")
    fiber: float = Field(ge=0, description="g/100g")
    sodium: float = Field(ge=0, description="mg/100g")
    calcium: float = Field(ge=0, description="mg/100g")
    iron: float = Field(ge=0, description="mg/100g")
    vitamin_a: float = Field(ge=0, description="μg/100g")
    vitamin_c: float = Field(ge=0, description="mg/100g")
    vitamin_d: float = Field(ge=0, description="μg/100g")
    max_portion: float = Field(default=300, ge=0, description="1食あたり最大量(g)")


class FoodPortion(BaseModel):
    """食材と分量"""
    food: Food
    amount: float = Field(ge=0, description="g")


class NutrientTarget(BaseModel):
    """栄養素目標値（1日）"""
    calories_min: float = Field(default=1800, ge=0)
    calories_max: float = Field(default=2200, ge=0)
    protein_min: float = Field(default=60, ge=0)
    protein_max: float = Field(default=100, ge=0)
    fat_min: float = Field(default=50, ge=0)
    fat_max: float = Field(default=80, ge=0)
    carbohydrate_min: float = Field(default=250, ge=0)
    carbohydrate_max: float = Field(default=350, ge=0)
    fiber_min: float = Field(default=20, ge=0)
    sodium_max: float = Field(default=2500, ge=0, description="mg")
    calcium_min: float = Field(default=650, ge=0, description="mg")
    iron_min: float = Field(default=7.5, ge=0, description="mg")
    vitamin_a_min: float = Field(default=850, ge=0, description="μg")
    vitamin_c_min: float = Field(default=100, ge=0, description="mg")
    vitamin_d_min: float = Field(default=8.5, ge=0, description="μg")


class Meal(BaseModel):
    """1食分のメニュー"""
    name: str  # breakfast, lunch, dinner
    foods: list[FoodPortion]
    total_calories: float
    total_protein: float
    total_fat: float
    total_carbohydrate: float


class MenuPlan(BaseModel):
    """1日分のメニュープラン"""
    breakfast: Meal
    lunch: Meal
    dinner: Meal
    total_nutrients: dict[str, float]
    achievement_rate: dict[str, float]  # 各栄養素の達成率(%)


class OptimizeRequest(BaseModel):
    """最適化リクエスト"""
    target: Optional[NutrientTarget] = None
    excluded_food_ids: list[int] = Field(default_factory=list)
    preferred_food_ids: list[int] = Field(default_factory=list)


class UserPreferences(BaseModel):
    """ユーザー設定"""
    calories_target: float = Field(default=2000, ge=1000, le=4000)
    excluded_categories: list[str] = Field(default_factory=list)
    excluded_food_ids: list[int] = Field(default_factory=list)
