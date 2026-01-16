"""
依存性注入設定

クリーンアーキテクチャ: presentation層
FastAPIのDependsで使用するファクトリ関数を定義
"""
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.repositories import (
    SQLAlchemyDishRepository,
    SQLAlchemyFoodRepository,
    SQLAlchemyIngredientRepository,
    InMemoryPreferenceRepository,
)
from app.infrastructure.optimizer import PuLPSolver
from app.infrastructure.external import GeminiRecipeGenerator
from app.domain.services import NutrientCalculator, UnitConverter
from app.domain.interfaces import (
    DishRepositoryInterface,
    FoodRepositoryInterface,
    IngredientRepositoryInterface,
    PreferenceRepositoryInterface,
)
from app.application.use_cases import (
    OptimizeMultiDayMenuUseCase,
    RefineMenuPlanUseCase,
    GetDishesUseCase,
    GetDishByIdUseCase,
    GetDishesByIdsUseCase,
    GetIngredientsUseCase,
    GetIngredientByIdUseCase,
    GenerateRecipeUseCase,
    GetRecipeDetailUseCase,
    BatchGenerateRecipesUseCase,
    GetPreferencesUseCase,
    UpdatePreferencesUseCase,
    GetAllergensUseCase,
)


# ========== リポジトリ ==========

def get_dish_repository(db: Session = Depends(get_db)) -> DishRepositoryInterface:
    """料理リポジトリを取得"""
    return SQLAlchemyDishRepository(db)


def get_food_repository(db: Session = Depends(get_db)) -> FoodRepositoryInterface:
    """食品リポジトリを取得"""
    return SQLAlchemyFoodRepository(db)


def get_ingredient_repository(db: Session = Depends(get_db)) -> IngredientRepositoryInterface:
    """食材リポジトリを取得"""
    return SQLAlchemyIngredientRepository(db)


# シングルトンインスタンス
_preference_repository: InMemoryPreferenceRepository | None = None


def get_preference_repository() -> PreferenceRepositoryInterface:
    """設定リポジトリを取得（シングルトン）"""
    global _preference_repository
    if _preference_repository is None:
        _preference_repository = InMemoryPreferenceRepository()
    return _preference_repository


# ========== ドメインサービス ==========

@lru_cache()
def get_nutrient_calculator() -> NutrientCalculator:
    """栄養素計算サービスを取得"""
    return NutrientCalculator()


@lru_cache()
def get_unit_converter() -> UnitConverter:
    """単位変換サービスを取得"""
    return UnitConverter()


# ========== インフラサービス ==========

@lru_cache()
def get_solver() -> PuLPSolver:
    """PuLPソルバーを取得

    パフォーマンスチューニング:
    - gap_rel=0.35: 35%以内で早期終了（サチュレーション時に早期終了）
    - 栄養密度ベースの事前フィルタリングは削除
      → 代わりに除外食材(excluded_ingredient_ids)でユーザーが制御
    """
    return PuLPSolver(
        time_limit=30,
        solver_type="cbc",  # HiGHS CLIが未インストールのためCBC使用
        gap_rel=0.35,  # 35%以内で早期終了
    )


@lru_cache()
def get_recipe_generator() -> GeminiRecipeGenerator:
    """レシピジェネレーターを取得"""
    return GeminiRecipeGenerator()


# ========== ユースケース ==========

def get_optimize_multi_day_use_case(
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
    solver: PuLPSolver = Depends(get_solver),
) -> OptimizeMultiDayMenuUseCase:
    """複数日最適化ユースケースを取得"""
    return OptimizeMultiDayMenuUseCase(
        dish_repo=dish_repo,
        solver=solver,
    )


def get_refine_menu_plan_use_case(
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
    solver: PuLPSolver = Depends(get_solver),
) -> RefineMenuPlanUseCase:
    """献立調整ユースケースを取得"""
    return RefineMenuPlanUseCase(
        dish_repo=dish_repo,
        solver=solver,
    )


def get_dishes_use_case(
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
) -> GetDishesUseCase:
    """料理一覧取得ユースケースを取得"""
    return GetDishesUseCase(dish_repo=dish_repo)


def get_dish_by_id_use_case(
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
) -> GetDishByIdUseCase:
    """料理取得ユースケースを取得"""
    return GetDishByIdUseCase(dish_repo=dish_repo)


def get_dishes_by_ids_use_case(
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
) -> GetDishesByIdsUseCase:
    """複数料理取得ユースケースを取得"""
    return GetDishesByIdsUseCase(dish_repo=dish_repo)


def get_ingredients_use_case(
    ingredient_repo: IngredientRepositoryInterface = Depends(get_ingredient_repository),
) -> GetIngredientsUseCase:
    """食材一覧取得ユースケースを取得"""
    return GetIngredientsUseCase(ingredient_repo=ingredient_repo)


def get_ingredient_by_id_use_case(
    ingredient_repo: IngredientRepositoryInterface = Depends(get_ingredient_repository),
) -> GetIngredientByIdUseCase:
    """食材取得ユースケースを取得"""
    return GetIngredientByIdUseCase(ingredient_repo=ingredient_repo)


def get_generate_recipe_use_case(
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
    recipe_generator: GeminiRecipeGenerator = Depends(get_recipe_generator),
) -> GenerateRecipeUseCase:
    """レシピ生成ユースケースを取得"""
    return GenerateRecipeUseCase(
        dish_repo=dish_repo,
        recipe_generator=recipe_generator,
    )


def get_recipe_detail_use_case(
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
    recipe_generator: GeminiRecipeGenerator = Depends(get_recipe_generator),
) -> GetRecipeDetailUseCase:
    """レシピ詳細取得ユースケースを取得"""
    return GetRecipeDetailUseCase(
        dish_repo=dish_repo,
        recipe_generator=recipe_generator,
    )


def get_batch_generate_recipes_use_case(
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
    recipe_generator: GeminiRecipeGenerator = Depends(get_recipe_generator),
) -> BatchGenerateRecipesUseCase:
    """一括レシピ生成ユースケースを取得"""
    return BatchGenerateRecipesUseCase(
        dish_repo=dish_repo,
        recipe_generator=recipe_generator,
    )


def get_preferences_use_case(
    preference_repo: PreferenceRepositoryInterface = Depends(get_preference_repository),
) -> GetPreferencesUseCase:
    """設定取得ユースケースを取得"""
    return GetPreferencesUseCase(preference_repo=preference_repo)


def get_update_preferences_use_case(
    preference_repo: PreferenceRepositoryInterface = Depends(get_preference_repository),
) -> UpdatePreferencesUseCase:
    """設定更新ユースケースを取得"""
    return UpdatePreferencesUseCase(preference_repo=preference_repo)


def get_allergens_use_case() -> GetAllergensUseCase:
    """アレルゲン一覧取得ユースケースを取得"""
    return GetAllergensUseCase()
