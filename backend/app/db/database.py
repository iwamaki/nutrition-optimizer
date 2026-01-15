from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nutrition.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class FoodDB(Base):
    """食品テーブル（文科省食品成分表ベース）"""
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    mext_code = Column(String, unique=True, index=True)  # 文科省食品番号（例: "01088"）
    name = Column(String, index=True)
    category = Column(String, index=True)  # 文科省の食品群
    calories = Column(Float, default=0)     # kcal/100g
    protein = Column(Float, default=0)      # g/100g
    fat = Column(Float, default=0)          # g/100g
    carbohydrate = Column(Float, default=0) # g/100g
    fiber = Column(Float, default=0)        # g/100g
    # ミネラル
    sodium = Column(Float, default=0)       # mg/100g
    potassium = Column(Float, default=0)    # mg/100g (カリウム)
    calcium = Column(Float, default=0)      # mg/100g
    magnesium = Column(Float, default=0)    # mg/100g
    iron = Column(Float, default=0)         # mg/100g
    zinc = Column(Float, default=0)         # mg/100g (亜鉛)
    # ビタミン
    vitamin_a = Column(Float, default=0)    # μg/100g (レチノール活性当量)
    vitamin_d = Column(Float, default=0)    # μg/100g
    vitamin_e = Column(Float, default=0)    # mg/100g (α-トコフェロール)
    vitamin_k = Column(Float, default=0)    # μg/100g
    vitamin_b1 = Column(Float, default=0)   # mg/100g (チアミン)
    vitamin_b2 = Column(Float, default=0)   # mg/100g (リボフラビン)
    vitamin_b6 = Column(Float, default=0)   # mg/100g
    vitamin_b12 = Column(Float, default=0)  # μg/100g
    niacin = Column(Float, default=0)       # mg/100g (ナイアシン/B3)
    pantothenic_acid = Column(Float, default=0)  # mg/100g (パントテン酸/B5)
    biotin = Column(Float, default=0)       # μg/100g (ビオチン/B7)
    folate = Column(Float, default=0)       # μg/100g (葉酸)
    vitamin_c = Column(Float, default=0)    # mg/100g
    max_portion = Column(Float, default=300)

    # リレーション
    dish_ingredients = relationship("DishIngredientDB", back_populates="food")
    allergens = relationship("FoodAllergenDB", back_populates="food", cascade="all, delete-orphan")


class MealType(enum.Enum):
    """食事タイプ"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DishCategory(enum.Enum):
    """料理カテゴリ"""
    STAPLE = "主食"       # ご飯、パン、麺
    MAIN = "主菜"         # 肉・魚料理
    SIDE = "副菜"         # 野菜料理
    SOUP = "汁物"         # 味噌汁、スープ
    DESSERT = "デザート"  # 果物、甘味


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


class DishDB(Base):
    """料理マスタ"""
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, index=True)  # DishCategory の値
    meal_types = Column(String)  # カンマ区切り: "breakfast,lunch,dinner"
    serving_size = Column(Float, default=1.0)  # 1人前の係数
    description = Column(String, nullable=True)
    instructions = Column(String, nullable=True)  # 作り方

    # 作り置き関連
    storage_days = Column(Integer, default=1)  # 作り置き可能日数（0=当日のみ、1=翌日まで...）
    min_servings = Column(Integer, default=1)  # 最小調理人前
    max_servings = Column(Integer, default=4)  # 最大調理人前

    # キャッシュ用: 計算済み栄養素（材料から計算して保存）
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
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=True)  # 基本食材ID（買い物リスト用）
    amount = Column(Float, nullable=False)  # g
    cooking_method = Column(String, default="生")  # CookingMethod の値

    # リレーション
    dish = relationship("DishDB", back_populates="ingredients")
    food = relationship("FoodDB", back_populates="dish_ingredients")
    ingredient = relationship("IngredientDB", back_populates="dish_ingredients")


class CookingFactorDB(Base):
    """調理係数マスタ（栄養素の変化率）"""
    __tablename__ = "cooking_factors"

    id = Column(Integer, primary_key=True, index=True)
    food_category = Column(String, index=True)  # 食品カテゴリ（または "default"）
    cooking_method = Column(String, index=True)  # CookingMethod の値
    nutrient = Column(String, index=True)  # 栄養素名
    factor = Column(Float, default=1.0)  # 係数（1.0 = 変化なし）


class FoodAllergenDB(Base):
    """食品のアレルゲン情報"""
    __tablename__ = "food_allergens"

    id = Column(Integer, primary_key=True, index=True)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False, index=True)
    allergen = Column(String, nullable=False, index=True)  # AllergenType の値

    # リレーション
    food = relationship("FoodDB", back_populates="allergens")


class IngredientDB(Base):
    """基本食材マスタ（アプリ専用の正規化された食材リスト）"""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # 正規化された食材名（例: "卵", "玉ねぎ"）
    category = Column(String, index=True)  # カテゴリ（例: "野菜類", "肉類"）
    mext_code = Column(String, index=True)  # 代表的な文科省食品コード（栄養素参照用）
    emoji = Column(String, nullable=True)  # 表示用絵文字

    # リレーション
    dish_ingredients = relationship("DishIngredientDB", back_populates="ingredient")


def init_db():
    """データベース初期化"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """DBセッション取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
