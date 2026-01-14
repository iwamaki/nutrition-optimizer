from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AllergenEnum(str, Enum):
    """7大アレルゲン（特定原材料）"""
    EGG = "卵"
    MILK = "乳"
    WHEAT = "小麦"
    BUCKWHEAT = "そば"
    PEANUT = "落花生"
    SHRIMP = "えび"
    CRAB = "かに"


class VolumeLevelEnum(str, Enum):
    """献立ボリュームレベル"""
    SMALL = "small"    # 少なめ（カロリー目標 × 0.8）
    NORMAL = "normal"  # 普通（カロリー目標 × 1.0）
    LARGE = "large"    # 多め（カロリー目標 × 1.2）


class VarietyLevelEnum(str, Enum):
    """食材の種類レベル（多様性）"""
    SMALL = "small"    # 少なめ（作り置き優先、同じ料理を繰り返す）
    NORMAL = "normal"  # 普通（バランス）
    LARGE = "large"    # 多め（毎食違う料理）


class BatchCookingLevelEnum(str, Enum):
    """作り置き優先度レベル"""
    SMALL = "small"    # 少なめ（調理回数多めでもOK、毎食違う料理）
    NORMAL = "normal"  # 普通（バランス）
    LARGE = "large"    # 多め（調理回数を最小化、作り置き重視）


class MealTypeEnum(str, Enum):
    """食事タイプ"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DishCategoryEnum(str, Enum):
    """料理カテゴリ"""
    STAPLE = "主食"
    MAIN = "主菜"
    SIDE = "副菜"
    SOUP = "汁物"
    DESSERT = "デザート"


class CookingMethodEnum(str, Enum):
    """調理法"""
    RAW = "生"
    BOIL = "茹でる"
    STEAM = "蒸す"
    GRILL = "焼く"
    FRY = "炒める"
    DEEP_FRY = "揚げる"
    SIMMER = "煮る"
    MICROWAVE = "電子レンジ"


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


# ========== 料理関連スキーマ ==========

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
    amount: float = Field(ge=0, description="g")
    cooking_method: CookingMethodEnum = CookingMethodEnum.RAW


class DishBase(BaseModel):
    """料理ベース"""
    name: str
    category: DishCategoryEnum
    meal_types: list[MealTypeEnum]
    serving_size: float = Field(default=1.0, ge=0.1)
    description: Optional[str] = None
    instructions: Optional[str] = None  # 作り方


class DishCreate(DishBase):
    """料理作成リクエスト"""
    ingredients: list[DishIngredient]


class Dish(DishBase):
    """料理データモデル（栄養素計算済み）"""
    id: int
    ingredients: list[DishIngredient]
    # 作り置き関連
    storage_days: int = Field(default=1, description="作り置き可能日数（0=当日のみ）")
    min_servings: int = Field(default=1, description="最小調理人前")
    max_servings: int = Field(default=4, description="最大調理人前")
    # 計算済み栄養素（1人前あたり）
    calories: float = 0
    protein: float = 0
    fat: float = 0
    carbohydrate: float = 0
    fiber: float = 0
    sodium: float = 0
    calcium: float = 0
    iron: float = 0
    vitamin_a: float = 0
    vitamin_c: float = 0
    vitamin_d: float = 0
    # レシピ詳細（JSONから読み込み）
    recipe_details: Optional[RecipeDetails] = Field(default=None, description="詳細レシピ")

    class Config:
        from_attributes = True


class DishPortion(BaseModel):
    """料理と分量"""
    dish: Dish
    servings: float = Field(default=1.0, ge=0.1, description="人前")


class CookingFactor(BaseModel):
    """調理係数"""
    food_category: str
    cooking_method: CookingMethodEnum
    nutrient: str
    factor: float = Field(default=1.0, ge=0, le=2.0)


# ========== 最適化結果（料理ベース） ==========

class MealPlan(BaseModel):
    """1食分のメニュー（料理ベース）"""
    name: str  # breakfast, lunch, dinner
    dishes: list[DishPortion]
    total_calories: float
    total_protein: float
    total_fat: float
    total_carbohydrate: float
    total_fiber: float
    total_sodium: float
    total_calcium: float
    total_iron: float
    total_vitamin_a: float
    total_vitamin_c: float
    total_vitamin_d: float


class DailyMenuPlan(BaseModel):
    """1日分のメニュープラン（料理ベース）"""
    breakfast: MealPlan
    lunch: MealPlan
    dinner: MealPlan
    total_nutrients: dict[str, float]
    achievement_rate: dict[str, float]  # 全栄養素の達成率(%)


# ========== 複数日最適化（作り置き対応） ==========

class MultiDayOptimizeRequest(BaseModel):
    """複数日最適化リクエスト"""
    days: int = Field(default=1, ge=1, le=7, description="日数")
    people: int = Field(default=1, ge=1, le=6, description="人数")
    target: Optional[NutrientTarget] = None
    excluded_allergens: list[AllergenEnum] = Field(default_factory=list, description="除外アレルゲン")
    excluded_dish_ids: list[int] = Field(default_factory=list, description="除外料理ID")
    batch_cooking_level: BatchCookingLevelEnum = Field(default=BatchCookingLevelEnum.NORMAL, description="作り置き優先度")
    volume_level: VolumeLevelEnum = Field(default=VolumeLevelEnum.NORMAL, description="献立ボリューム")
    variety_level: VarietyLevelEnum = Field(default=VarietyLevelEnum.NORMAL, description="食材の種類（多様性）")


class CookingTask(BaseModel):
    """調理タスク（いつ、何を、何人前作るか）"""
    cook_day: int = Field(ge=1, description="調理日（1始まり）")
    dish: Dish
    servings: int = Field(ge=1, description="調理人前数（整数）")
    consume_days: list[int] = Field(description="消費日リスト")


class ShoppingItem(BaseModel):
    """買い物リストアイテム"""
    food_name: str
    total_amount: float = Field(description="合計量(g)")
    category: str


class DailyMealAssignment(BaseModel):
    """1日分の食事割り当て"""
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
    cooking_tasks: list[CookingTask] = Field(description="調理計画")
    shopping_list: list[ShoppingItem] = Field(description="買い物リスト")
    overall_nutrients: dict[str, float] = Field(description="期間合計栄養素")
    overall_achievement: dict[str, float] = Field(description="期間全体の達成率")
    warnings: list[NutrientWarning] = Field(default_factory=list, description="栄養素警告")


class RefineOptimizeRequest(BaseModel):
    """献立調整リクエスト"""
    days: int = Field(default=1, ge=1, le=7, description="日数")
    people: int = Field(default=1, ge=1, le=6, description="人数")
    target: Optional[NutrientTarget] = None
    keep_dish_ids: list[int] = Field(default_factory=list, description="残したい料理ID")
    exclude_dish_ids: list[int] = Field(default_factory=list, description="外したい料理ID")
    excluded_allergens: list[AllergenEnum] = Field(default_factory=list, description="除外アレルゲン")
    batch_cooking_level: BatchCookingLevelEnum = Field(default=BatchCookingLevelEnum.NORMAL, description="作り置き優先度")
    volume_level: VolumeLevelEnum = Field(default=VolumeLevelEnum.NORMAL, description="献立ボリューム")
    variety_level: VarietyLevelEnum = Field(default=VarietyLevelEnum.NORMAL, description="食材の種類（多様性）")
