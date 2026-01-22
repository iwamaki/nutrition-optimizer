"""
食材関連APIエンドポイント

クリーンアーキテクチャ: presentation層
"""
from fastapi import APIRouter, Depends

from app.domain.entities import Ingredient
from app.application.use_cases import (
    GetIngredientsUseCase,
    GetIngredientByIdUseCase,
)
from app.presentation.dependencies import (
    get_ingredients_use_case,
    get_ingredient_by_id_use_case,
)

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[Ingredient])
def get_ingredients(
    category: str = None,
    use_case: GetIngredientsUseCase = Depends(get_ingredients_use_case),
):
    """基本食材一覧を取得（正規化された食材マスタ）

    フロントエンドの「よく使う食材」選択や買い物リストに使用
    """
    return use_case.execute(category=category, limit=10000)


@router.get("/{ingredient_id}", response_model=Ingredient)
def get_ingredient(
    ingredient_id: int,
    use_case: GetIngredientByIdUseCase = Depends(get_ingredient_by_id_use_case),
):
    """特定の基本食材を取得"""
    return use_case.execute(ingredient_id)


@router.get("-categories", name="get_ingredient_categories")
def get_ingredient_categories(
    use_case: GetIngredientsUseCase = Depends(get_ingredients_use_case),
):
    """基本食材のカテゴリ一覧を取得"""
    return use_case.get_categories()
