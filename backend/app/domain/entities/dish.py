"""Dish domain entities."""

from typing import Optional
from pydantic import BaseModel, Field

from app.domain.entities.enums import (
    MealTypeEnum,
    DishCategoryEnum,
    CookingMethodEnum,
)


class RecipeDetails(BaseModel):
    """レシピ詳細"""
    prep_time: Optional[int] = Field(default=None, description="下準備時間（分）")
    cook_time: Optional[int] = Field(default=None, description="調理時間（分）")
    servings: Optional[int] = Field(default=None, description="基準人数")
    steps: list[str] = Field(default_factory=list, description="調理手順")
    tips: Optional[str] = Field(default=None, description="コツ・ポイント")
    variations: Optional[str] = Field(default=None, description="アレンジ例")


class DishIngredient(BaseModel):
    """料理の材料"""
    food_id: int
    food_name: Optional[str] = None
    ingredient_id: Optional[int] = Field(default=None, description="基本食材ID（買い物リスト用）")
    ingredient_name: Optional[str] = Field(default=None, description="基本食材名（正規化された名前）")
    amount: float = Field(ge=0, description="g")
    display_amount: str = Field(default="", description="表示用の量（例: 1本, 1/2個）")
    unit: str = Field(default="g", description="単位（個, 本, 束, 枚, g）")
    cooking_method: CookingMethodEnum = CookingMethodEnum.RAW


class DishBase(BaseModel):
    """料理ベース"""
    name: str
    category: DishCategoryEnum
    meal_types: list[MealTypeEnum]
    serving_size: float = Field(default=1.0, ge=0.1)
    description: Optional[str] = None
    instructions: Optional[str] = None


class Dish(DishBase):
    """料理データモデル（栄養素計算済み）"""
    id: int
    ingredients: list[DishIngredient]
    # 作り置き関連
    storage_days: int = Field(default=1, description="作り置き可能日数（0=当日のみ）")
    min_servings: int = Field(default=1, description="最小調理人前")
    max_servings: int = Field(default=4, description="最大調理人前")
    # 味付け系統（段階的決定フロー用）
    flavor_profile: str = Field(default="和風", description="味付け系統（和風/洋風/中華）")
    # 計算済み栄養素（1人前あたり）
    calories: float = 0
    protein: float = 0
    fat: float = 0
    carbohydrate: float = 0
    fiber: float = 0
    # ミネラル
    sodium: float = 0
    potassium: float = 0
    calcium: float = 0
    magnesium: float = 0
    iron: float = 0
    zinc: float = 0
    # ビタミン
    vitamin_a: float = 0
    vitamin_d: float = 0
    vitamin_e: float = 0
    vitamin_k: float = 0
    vitamin_b1: float = 0
    vitamin_b2: float = 0
    vitamin_b6: float = 0
    vitamin_b12: float = 0
    niacin: float = 0
    pantothenic_acid: float = 0
    biotin: float = 0
    folate: float = 0
    vitamin_c: float = 0
    # レシピ詳細
    recipe_details: Optional[RecipeDetails] = Field(default=None, description="詳細レシピ")

    class Config:
        from_attributes = True

    def get_nutrient(self, nutrient: str) -> float:
        """栄養素の値を取得"""
        return getattr(self, nutrient, 0)


class DishPortion(BaseModel):
    """料理と分量"""
    dish: Dish
    servings: float = Field(default=1.0, ge=0.1, description="人前")

    def get_nutrient_total(self, nutrient: str) -> float:
        """栄養素の合計を取得"""
        return self.dish.get_nutrient(nutrient) * self.servings


class CookingFactor(BaseModel):
    """調理係数"""
    food_category: str
    cooking_method: CookingMethodEnum
    nutrient: str
    factor: float = Field(default=1.0, ge=0, le=2.0)
