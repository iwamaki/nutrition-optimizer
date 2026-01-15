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

class CategoryConstraint(BaseModel):
    """カテゴリ別品数制約（min/max）"""
    min: int = Field(default=0, ge=0, description="最小品数")
    max: int = Field(default=2, ge=0, description="最大品数")


class MealCategoryConstraints(BaseModel):
    """1食分のカテゴリ別品数制約"""
    staple: CategoryConstraint = Field(default_factory=lambda: CategoryConstraint(min=1, max=1), alias="主食", description="主食")
    main: CategoryConstraint = Field(default_factory=lambda: CategoryConstraint(min=1, max=1), alias="主菜", description="主菜")
    side: CategoryConstraint = Field(default_factory=lambda: CategoryConstraint(min=0, max=2), alias="副菜", description="副菜")
    soup: CategoryConstraint = Field(default_factory=lambda: CategoryConstraint(min=0, max=1), alias="汁物", description="汁物")
    dessert: CategoryConstraint = Field(default_factory=lambda: CategoryConstraint(min=0, max=1), alias="デザート", description="デザート")

    class Config:
        populate_by_name = True

    def to_solver_dict(self) -> dict:
        """solver用のdict形式に変換 {"主食": (min, max), ...}"""
        return {
            "主食": (self.staple.min, self.staple.max),
            "主菜": (self.main.min, self.main.max),
            "副菜": (self.side.min, self.side.max),
            "汁物": (self.soup.min, self.soup.max),
            "デザート": (self.dessert.min, self.dessert.max),
        }


class MealPresetEnum(str, Enum):
    """食事プリセット"""
    MINIMAL = "minimal"      # 最小限（主食のみ）
    LIGHT = "light"          # 軽め（主食+主菜）
    STANDARD = "standard"    # 標準（主食+主菜+副菜）
    FULL = "full"            # 充実（主食+主菜+副菜+汁物）
    JAPANESE = "japanese"    # 和定食（一汁三菜）
    CUSTOM = "custom"        # カスタム（categoriesを直接指定）


# プリセット定義（各プリセットのカテゴリ制約）
MEAL_PRESETS: dict[str, MealCategoryConstraints] = {
    "minimal": MealCategoryConstraints(
        staple=CategoryConstraint(min=1, max=1),
        main=CategoryConstraint(min=0, max=0),
        side=CategoryConstraint(min=0, max=0),
        soup=CategoryConstraint(min=0, max=0),
        dessert=CategoryConstraint(min=0, max=0),
    ),
    "light": MealCategoryConstraints(
        staple=CategoryConstraint(min=1, max=1),
        main=CategoryConstraint(min=1, max=1),
        side=CategoryConstraint(min=0, max=0),
        soup=CategoryConstraint(min=0, max=0),
        dessert=CategoryConstraint(min=0, max=0),
    ),
    "standard": MealCategoryConstraints(
        staple=CategoryConstraint(min=1, max=1),
        main=CategoryConstraint(min=1, max=1),
        side=CategoryConstraint(min=1, max=1),
        soup=CategoryConstraint(min=0, max=1),
        dessert=CategoryConstraint(min=0, max=0),
    ),
    "full": MealCategoryConstraints(
        staple=CategoryConstraint(min=1, max=1),
        main=CategoryConstraint(min=1, max=1),
        side=CategoryConstraint(min=1, max=2),
        soup=CategoryConstraint(min=1, max=1),
        dessert=CategoryConstraint(min=0, max=1),
    ),
    "japanese": MealCategoryConstraints(
        staple=CategoryConstraint(min=1, max=1),
        main=CategoryConstraint(min=1, max=1),
        side=CategoryConstraint(min=2, max=3),
        soup=CategoryConstraint(min=1, max=1),
        dessert=CategoryConstraint(min=0, max=0),
    ),
}


class MealSetting(BaseModel):
    """食事タイプ別の設定（拡張版）"""
    enabled: bool = Field(default=True, description="この食事を生成するか")
    preset: MealPresetEnum = Field(default=MealPresetEnum.STANDARD, description="プリセット")
    categories: Optional[dict] = Field(default=None, description="カテゴリ制約（フロントエンドからの直接指定用、{'主食': [min, max], ...}形式）")

    def get_category_constraints_dict(self) -> dict:
        """solver用のカテゴリ制約dictを取得"""
        # categoriesが直接指定されている場合（フロントエンドからの形式）
        if self.categories:
            result = {}
            for cat, constraint in self.categories.items():
                if isinstance(constraint, list) and len(constraint) == 2:
                    result[cat] = (constraint[0], constraint[1])
                elif isinstance(constraint, dict):
                    result[cat] = (constraint.get('min', 0), constraint.get('max', 2))
                elif isinstance(constraint, tuple):
                    result[cat] = constraint
            return result
        # プリセットから取得
        preset_constraints = MEAL_PRESETS.get(self.preset.value, MEAL_PRESETS["standard"])
        return preset_constraints.to_solver_dict()


class MealSettings(BaseModel):
    """朝昼夜の設定"""
    breakfast: Optional[MealSetting] = Field(default=None, description="朝食設定")
    lunch: Optional[MealSetting] = Field(default=None, description="昼食設定")
    dinner: Optional[MealSetting] = Field(default=None, description="夕食設定")

    def to_dict(self) -> dict:
        """solver用のdict形式に変換"""
        result = {}
        if self.breakfast:
            result["breakfast"] = {
                "enabled": self.breakfast.enabled,
                "categories": self.breakfast.get_category_constraints_dict(),
            }
        if self.lunch:
            result["lunch"] = {
                "enabled": self.lunch.enabled,
                "categories": self.lunch.get_category_constraints_dict(),
            }
        if self.dinner:
            result["dinner"] = {
                "enabled": self.dinner.enabled,
                "categories": self.dinner.get_category_constraints_dict(),
            }
        return result if result else None


class MultiDayOptimizeRequest(BaseModel):
    """複数日最適化リクエスト"""
    days: int = Field(default=1, ge=1, le=7, description="日数")
    people: int = Field(default=1, ge=1, le=6, description="人数")
    target: Optional[NutrientTarget] = None
    excluded_allergens: list[AllergenEnum] = Field(default_factory=list, description="除外アレルゲン")
    excluded_dish_ids: list[int] = Field(default_factory=list, description="除外料理ID")
    batch_cooking_level: BatchCookingLevelEnum = Field(default=BatchCookingLevelEnum.NORMAL, description="作り置き優先度")
    volume_level: VolumeLevelEnum = Field(default=VolumeLevelEnum.NORMAL, description="カロリー目標レベル")
    variety_level: VarietyLevelEnum = Field(default=VarietyLevelEnum.NORMAL, description="料理の繰り返し")
    meal_settings: Optional[MealSettings] = Field(default=None, description="朝昼夜別の設定")


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
    volume_level: VolumeLevelEnum = Field(default=VolumeLevelEnum.NORMAL, description="カロリー目標レベル")
    variety_level: VarietyLevelEnum = Field(default=VarietyLevelEnum.NORMAL, description="料理の繰り返し")
    meal_settings: Optional[MealSettings] = Field(default=None, description="朝昼夜別の設定")
