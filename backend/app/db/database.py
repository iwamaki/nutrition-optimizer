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
    sodium = Column(Float, default=0)       # mg/100g
    calcium = Column(Float, default=0)      # mg/100g
    iron = Column(Float, default=0)         # mg/100g
    vitamin_a = Column(Float, default=0)    # μg/100g
    vitamin_c = Column(Float, default=0)    # mg/100g
    vitamin_d = Column(Float, default=0)    # μg/100g
    max_portion = Column(Float, default=300)

    # リレーション
    dish_ingredients = relationship("DishIngredientDB", back_populates="food")


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


class DishDB(Base):
    """料理マスタ"""
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, index=True)  # DishCategory の値
    meal_types = Column(String)  # カンマ区切り: "breakfast,lunch,dinner"
    serving_size = Column(Float, default=1.0)  # 1人前の係数
    description = Column(String, nullable=True)

    # キャッシュ用: 計算済み栄養素（材料から計算して保存）
    calories = Column(Float, default=0)
    protein = Column(Float, default=0)
    fat = Column(Float, default=0)
    carbohydrate = Column(Float, default=0)
    fiber = Column(Float, default=0)
    sodium = Column(Float, default=0)
    calcium = Column(Float, default=0)
    iron = Column(Float, default=0)
    vitamin_a = Column(Float, default=0)
    vitamin_c = Column(Float, default=0)
    vitamin_d = Column(Float, default=0)

    # リレーション
    ingredients = relationship("DishIngredientDB", back_populates="dish", cascade="all, delete-orphan")


class DishIngredientDB(Base):
    """料理の材料（中間テーブル）"""
    __tablename__ = "dish_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    amount = Column(Float, nullable=False)  # g
    cooking_method = Column(String, default="生")  # CookingMethod の値

    # リレーション
    dish = relationship("DishDB", back_populates="ingredients")
    food = relationship("FoodDB", back_populates="dish_ingredients")


class CookingFactorDB(Base):
    """調理係数マスタ（栄養素の変化率）"""
    __tablename__ = "cooking_factors"

    id = Column(Integer, primary_key=True, index=True)
    food_category = Column(String, index=True)  # 食品カテゴリ（または "default"）
    cooking_method = Column(String, index=True)  # CookingMethod の値
    nutrient = Column(String, index=True)  # 栄養素名
    factor = Column(Float, default=1.0)  # 係数（1.0 = 変化なし）


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
