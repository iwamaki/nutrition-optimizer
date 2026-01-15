"""Application use cases."""

from app.application.use_cases.optimize_multi_day_menu import OptimizeMultiDayMenuUseCase
from app.application.use_cases.refine_menu_plan import RefineMenuPlanUseCase
from app.application.use_cases.get_dishes import (
    GetDishesUseCase,
    GetDishByIdUseCase,
    GetDishesByIdsUseCase,
)
from app.application.use_cases.get_ingredients import (
    GetIngredientsUseCase,
    GetIngredientByIdUseCase,
    GetIngredientsByIdsUseCase,
)
from app.application.use_cases.generate_recipe import (
    GenerateRecipeUseCase,
    GetRecipeDetailUseCase,
    BatchGenerateRecipesUseCase,
)
from app.application.use_cases.manage_preferences import (
    GetPreferencesUseCase,
    UpdatePreferencesUseCase,
    GetAllergensUseCase,
)

__all__ = [
    # 最適化
    "OptimizeMultiDayMenuUseCase",
    "RefineMenuPlanUseCase",
    # 料理
    "GetDishesUseCase",
    "GetDishByIdUseCase",
    "GetDishesByIdsUseCase",
    # 食材
    "GetIngredientsUseCase",
    "GetIngredientByIdUseCase",
    "GetIngredientsByIdsUseCase",
    # レシピ生成
    "GenerateRecipeUseCase",
    "GetRecipeDetailUseCase",
    "BatchGenerateRecipesUseCase",
    # 設定
    "GetPreferencesUseCase",
    "UpdatePreferencesUseCase",
    "GetAllergensUseCase",
]
