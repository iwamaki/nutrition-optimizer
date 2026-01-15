"""
Pytest フィクスチャ

クリーンアーキテクチャ: テスト設定
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database import Base
from app.domain.entities import (
    NutrientTarget, Dish, DishIngredient,
    DishCategoryEnum, MealTypeEnum, CookingMethodEnum,
)


@pytest.fixture
def test_engine():
    """テスト用インメモリDBエンジン"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_db(test_engine):
    """テスト用DBセッション"""
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def sample_nutrient_target():
    """サンプル栄養素目標"""
    return NutrientTarget()


@pytest.fixture
def sample_dish():
    """サンプル料理（白ごはん）"""
    return Dish(
        id=1,
        name="白ごはん",
        category=DishCategoryEnum.STAPLE,
        meal_types=[MealTypeEnum.BREAKFAST, MealTypeEnum.LUNCH, MealTypeEnum.DINNER],
        serving_size=150,
        ingredients=[
            DishIngredient(
                food_id=1,
                food_name="白米",
                ingredient_id=1,
                ingredient_name="白米",
                amount=150,
                display_amount="1",
                unit="合",
                cooking_method=CookingMethodEnum.RAW,
            )
        ],
        storage_days=1,
        min_servings=1,
        max_servings=4,
        calories=252,
        protein=3.8,
        fat=0.5,
        carbohydrate=55.7,
        fiber=0.5,
        sodium=1,
        potassium=0,
        calcium=0,
        magnesium=0,
        iron=0,
        zinc=0,
        vitamin_a=0,
        vitamin_d=0,
        vitamin_e=0,
        vitamin_k=0,
        vitamin_b1=0,
        vitamin_b2=0,
        vitamin_b6=0,
        vitamin_b12=0,
        niacin=0,
        pantothenic_acid=0,
        biotin=0,
        folate=0,
        vitamin_c=0,
    )


@pytest.fixture
def sample_main_dish():
    """サンプル主菜（焼き鮭）"""
    return Dish(
        id=2,
        name="焼き鮭",
        category=DishCategoryEnum.MAIN,
        meal_types=[MealTypeEnum.BREAKFAST, MealTypeEnum.LUNCH, MealTypeEnum.DINNER],
        serving_size=100,
        ingredients=[
            DishIngredient(
                food_id=2,
                food_name="鮭",
                ingredient_id=2,
                ingredient_name="鮭",
                amount=80,
                display_amount="1",
                unit="切れ",
                cooking_method=CookingMethodEnum.GRILL,
            )
        ],
        storage_days=2,
        min_servings=1,
        max_servings=4,
        calories=150,
        protein=20,
        fat=7,
        carbohydrate=0.1,
        fiber=0,
        sodium=100,
        potassium=350,
        calcium=10,
        magnesium=30,
        iron=0.5,
        zinc=0.5,
        vitamin_a=10,
        vitamin_d=30,
        vitamin_e=1.0,
        vitamin_k=0,
        vitamin_b1=0.15,
        vitamin_b2=0.2,
        vitamin_b6=0.5,
        vitamin_b12=5,
        niacin=8,
        pantothenic_acid=1,
        biotin=5,
        folate=10,
        vitamin_c=0,
    )


@pytest.fixture
def sample_side_dish():
    """サンプル副菜（ほうれん草のお浸し）"""
    return Dish(
        id=3,
        name="ほうれん草のお浸し",
        category=DishCategoryEnum.SIDE,
        meal_types=[MealTypeEnum.LUNCH, MealTypeEnum.DINNER],
        serving_size=80,
        ingredients=[
            DishIngredient(
                food_id=3,
                food_name="ほうれん草",
                ingredient_id=3,
                ingredient_name="ほうれん草",
                amount=80,
                display_amount="1/2",
                unit="束",
                cooking_method=CookingMethodEnum.BOIL,
            )
        ],
        storage_days=2,
        min_servings=1,
        max_servings=4,
        calories=20,
        protein=2,
        fat=0.3,
        carbohydrate=3,
        fiber=2,
        sodium=50,
        potassium=500,
        calcium=50,
        magnesium=70,
        iron=2,
        zinc=0.5,
        vitamin_a=400,
        vitamin_d=0,
        vitamin_e=2.0,
        vitamin_k=300,
        vitamin_b1=0.1,
        vitamin_b2=0.2,
        vitamin_b6=0.1,
        vitamin_b12=0,
        niacin=0.5,
        pantothenic_acid=0.2,
        biotin=5,
        folate=200,
        vitamin_c=30,
    )


@pytest.fixture
def sample_dishes(sample_dish, sample_main_dish, sample_side_dish):
    """サンプル料理リスト"""
    return [sample_dish, sample_main_dish, sample_side_dish]
