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
def sample_soup_dish():
    """サンプル汁物（味噌汁）"""
    return Dish(
        id=4,
        name="味噌汁",
        category=DishCategoryEnum.SOUP,
        meal_types=[MealTypeEnum.BREAKFAST, MealTypeEnum.LUNCH, MealTypeEnum.DINNER],
        serving_size=150,
        ingredients=[
            DishIngredient(
                food_id=4,
                food_name="味噌",
                ingredient_id=4,
                ingredient_name="味噌",
                amount=15,
                display_amount="大さじ1",
                unit="",
                cooking_method=CookingMethodEnum.RAW,
            )
        ],
        storage_days=1,
        min_servings=1,
        max_servings=4,
        calories=30,
        protein=2,
        fat=1,
        carbohydrate=3,
        fiber=0.5,
        sodium=500,
        potassium=100,
        calcium=20,
        magnesium=10,
        iron=0.5,
        zinc=0.2,
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
def sample_dessert_dish():
    """サンプルデザート（ヨーグルト）"""
    return Dish(
        id=5,
        name="ヨーグルト",
        category=DishCategoryEnum.DESSERT,
        meal_types=[MealTypeEnum.BREAKFAST, MealTypeEnum.LUNCH],
        serving_size=100,
        ingredients=[
            DishIngredient(
                food_id=5,
                food_name="ヨーグルト",
                ingredient_id=5,
                ingredient_name="ヨーグルト",
                amount=100,
                display_amount="1",
                unit="個",
                cooking_method=CookingMethodEnum.RAW,
            )
        ],
        storage_days=3,
        min_servings=1,
        max_servings=4,
        calories=60,
        protein=3.5,
        fat=3,
        carbohydrate=5,
        fiber=0,
        sodium=50,
        potassium=150,
        calcium=120,
        magnesium=10,
        iron=0,
        zinc=0.4,
        vitamin_a=30,
        vitamin_d=0,
        vitamin_e=0,
        vitamin_k=0,
        vitamin_b1=0,
        vitamin_b2=0.15,
        vitamin_b6=0,
        vitamin_b12=0.1,
        niacin=0,
        pantothenic_acid=0,
        biotin=0,
        folate=10,
        vitamin_c=1,
    )


@pytest.fixture
def sample_side_dish2():
    """サンプル副菜2（きんぴらごぼう）"""
    return Dish(
        id=6,
        name="きんぴらごぼう",
        category=DishCategoryEnum.SIDE,
        meal_types=[MealTypeEnum.LUNCH, MealTypeEnum.DINNER],
        serving_size=60,
        ingredients=[
            DishIngredient(
                food_id=6,
                food_name="ごぼう",
                ingredient_id=6,
                ingredient_name="ごぼう",
                amount=50,
                display_amount="1/4",
                unit="本",
                cooking_method=CookingMethodEnum.FRY,
            )
        ],
        storage_days=3,
        min_servings=1,
        max_servings=4,
        calories=40,
        protein=1,
        fat=1,
        carbohydrate=8,
        fiber=3,
        sodium=200,
        potassium=200,
        calcium=30,
        magnesium=30,
        iron=0.5,
        zinc=0.3,
        vitamin_a=0,
        vitamin_d=0,
        vitamin_e=0,
        vitamin_k=0,
        vitamin_b1=0.03,
        vitamin_b2=0.02,
        vitamin_b6=0.1,
        vitamin_b12=0,
        niacin=0.3,
        pantothenic_acid=0,
        biotin=0,
        folate=30,
        vitamin_c=2,
    )


@pytest.fixture
def sample_main_dish2():
    """サンプル主菜2（豚の生姜焼き）"""
    return Dish(
        id=7,
        name="豚の生姜焼き",
        category=DishCategoryEnum.MAIN,
        meal_types=[MealTypeEnum.LUNCH, MealTypeEnum.DINNER],
        serving_size=120,
        ingredients=[
            DishIngredient(
                food_id=7,
                food_name="豚肉",
                ingredient_id=7,
                ingredient_name="豚ロース肉",
                amount=100,
                display_amount="100",
                unit="g",
                cooking_method=CookingMethodEnum.FRY,
            )
        ],
        storage_days=2,
        min_servings=1,
        max_servings=4,
        calories=250,
        protein=18,
        fat=18,
        carbohydrate=5,
        fiber=0,
        sodium=400,
        potassium=300,
        calcium=5,
        magnesium=20,
        iron=0.8,
        zinc=2,
        vitamin_a=5,
        vitamin_d=0.3,
        vitamin_e=0.3,
        vitamin_k=0,
        vitamin_b1=0.6,
        vitamin_b2=0.2,
        vitamin_b6=0.3,
        vitamin_b12=0.4,
        niacin=4,
        pantothenic_acid=0.8,
        biotin=3,
        folate=3,
        vitamin_c=2,
    )


@pytest.fixture
def sample_dishes(sample_dish, sample_main_dish, sample_side_dish):
    """サンプル料理リスト（基本3品）"""
    return [sample_dish, sample_main_dish, sample_side_dish]


@pytest.fixture
def sample_dishes_full(
    sample_dish, sample_main_dish, sample_side_dish,
    sample_soup_dish, sample_dessert_dish, sample_side_dish2, sample_main_dish2
):
    """サンプル料理リスト（全7品）"""
    return [
        sample_dish, sample_main_dish, sample_side_dish,
        sample_soup_dish, sample_dessert_dish, sample_side_dish2, sample_main_dish2
    ]


@pytest.fixture
def solver():
    """PuLPソルバーインスタンス"""
    from app.infrastructure.optimizer import PuLPSolver
    return PuLPSolver(time_limit=10, msg=0)
