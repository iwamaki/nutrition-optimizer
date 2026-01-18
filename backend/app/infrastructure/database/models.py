"""SQLAlchemy ORM models."""

import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.infrastructure.database.connection import Base


class MealType(enum.Enum):
    """食事タイプ"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DishCategory(enum.Enum):
    """料理カテゴリ"""
    STAPLE = "主食"
    MAIN = "主菜"
    SIDE = "副菜"
    SOUP = "汁物"
    DESSERT = "デザート"


class CookingMethod(enum.Enum):
    """調理法"""
    RAW = "生"
    BOIL = "茹でる"
    STEAM = "蒸す"
    GRILL = "焼く"
    FRY = "炒める"
    DEEP_FRY = "揚げる"
    SIMMER = "煮る"
    MICROWAVE = "電子レンジ"


class AllergenType(enum.Enum):
    """7大アレルゲン（特定原材料）"""
    EGG = "卵"
    MILK = "乳"
    WHEAT = "小麦"
    BUCKWHEAT = "そば"
    PEANUT = "落花生"
    SHRIMP = "えび"
    CRAB = "かに"


class FoodDB(Base):
    """食品テーブル（文科省食品成分表ベース）"""
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    mext_code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    # 基本栄養素
    calories = Column(Float, default=0)
    protein = Column(Float, default=0)
    fat = Column(Float, default=0)
    carbohydrate = Column(Float, default=0)
    fiber = Column(Float, default=0)
    # ミネラル
    sodium = Column(Float, default=0)
    potassium = Column(Float, default=0)
    calcium = Column(Float, default=0)
    magnesium = Column(Float, default=0)
    iron = Column(Float, default=0)
    zinc = Column(Float, default=0)
    # ビタミン
    vitamin_a = Column(Float, default=0)
    vitamin_d = Column(Float, default=0)
    vitamin_e = Column(Float, default=0)
    vitamin_k = Column(Float, default=0)
    vitamin_b1 = Column(Float, default=0)
    vitamin_b2 = Column(Float, default=0)
    vitamin_b6 = Column(Float, default=0)
    vitamin_b12 = Column(Float, default=0)
    niacin = Column(Float, default=0)
    pantothenic_acid = Column(Float, default=0)
    biotin = Column(Float, default=0)
    folate = Column(Float, default=0)
    vitamin_c = Column(Float, default=0)
    max_portion = Column(Float, default=300)

    # リレーション
    dish_ingredients = relationship("DishIngredientDB", back_populates="food")
    allergens = relationship("FoodAllergenDB", back_populates="food", cascade="all, delete-orphan")


class DishDB(Base):
    """料理マスタ"""
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, index=True)
    meal_types = Column(String)  # カンマ区切り
    serving_size = Column(Float, default=1.0)
    description = Column(String, nullable=True)
    instructions = Column(String, nullable=True)
    # 作り置き関連
    storage_days = Column(Integer, default=1)
    min_servings = Column(Integer, default=1)
    max_servings = Column(Integer, default=4)
    # 味付け系統（段階的決定フロー用）
    flavor_profile = Column(String, default="和風")  # 和風/洋風/中華
    # キャッシュ用: 計算済み栄養素
    calories = Column(Float, default=0)
    protein = Column(Float, default=0)
    fat = Column(Float, default=0)
    carbohydrate = Column(Float, default=0)
    fiber = Column(Float, default=0)
    # ミネラル
    sodium = Column(Float, default=0)
    potassium = Column(Float, default=0)
    calcium = Column(Float, default=0)
    magnesium = Column(Float, default=0)
    iron = Column(Float, default=0)
    zinc = Column(Float, default=0)
    # ビタミン
    vitamin_a = Column(Float, default=0)
    vitamin_d = Column(Float, default=0)
    vitamin_e = Column(Float, default=0)
    vitamin_k = Column(Float, default=0)
    vitamin_b1 = Column(Float, default=0)
    vitamin_b2 = Column(Float, default=0)
    vitamin_b6 = Column(Float, default=0)
    vitamin_b12 = Column(Float, default=0)
    niacin = Column(Float, default=0)
    pantothenic_acid = Column(Float, default=0)
    biotin = Column(Float, default=0)
    folate = Column(Float, default=0)
    vitamin_c = Column(Float, default=0)

    # リレーション
    ingredients = relationship("DishIngredientDB", back_populates="dish", cascade="all, delete-orphan")


class DishIngredientDB(Base):
    """料理の材料（中間テーブル）"""
    __tablename__ = "dish_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=True)
    amount = Column(Float, nullable=False)
    cooking_method = Column(String, default="生")

    # リレーション
    dish = relationship("DishDB", back_populates="ingredients")
    food = relationship("FoodDB", back_populates="dish_ingredients")
    ingredient = relationship("IngredientDB", back_populates="dish_ingredients")


class CookingFactorDB(Base):
    """調理係数マスタ（栄養素の変化率）"""
    __tablename__ = "cooking_factors"

    id = Column(Integer, primary_key=True, index=True)
    food_category = Column(String, index=True)
    cooking_method = Column(String, index=True)
    nutrient = Column(String, index=True)
    factor = Column(Float, default=1.0)


class FoodAllergenDB(Base):
    """食品のアレルゲン情報"""
    __tablename__ = "food_allergens"

    id = Column(Integer, primary_key=True, index=True)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False, index=True)
    allergen = Column(String, nullable=False, index=True)

    # リレーション
    food = relationship("FoodDB", back_populates="allergens")


class IngredientDB(Base):
    """基本食材マスタ"""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, index=True)
    mext_code = Column(String, index=True)
    emoji = Column(String, nullable=True)
    # アレルゲン情報（カンマ区切り）
    allergens_required = Column(String, nullable=True)     # 特定原材料8品目（表示義務）: 卵,乳,小麦,えび,かに,くるみ,落花生,そば
    allergens_recommended = Column(String, nullable=True)  # 準特定原材料20品目（表示推奨）: 大豆,鶏肉,豚肉,牛肉,さけ,さば,いか,etc.
    # 単位変換情報
    unit_g = Column(Float, nullable=True)                  # 1単位あたりのグラム数（調味料は大さじ1のg）
    unit_name = Column(String, nullable=True)              # 単位名（本,個,枚,大さじ等）

    # リレーション
    dish_ingredients = relationship("DishIngredientDB", back_populates="ingredient")
