"""
料理関連APIエンドポイント

クリーンアーキテクチャ: presentation層
"""
from fastapi import APIRouter, Depends, HTTPException

from app.domain.entities import Dish, DishCategoryEnum, RecipeDetails
from app.application.use_cases import (
    GetDishesUseCase,
    GetDishByIdUseCase,
    GenerateRecipeUseCase,
    BatchGenerateRecipesUseCase,
)
from app.presentation.dependencies import (
    get_dishes_use_case,
    get_dish_by_id_use_case,
    get_generate_recipe_use_case,
    get_batch_generate_recipes_use_case,
)

router = APIRouter(prefix="/dishes", tags=["dishes"])


@router.get("", response_model=list[Dish])
def get_dishes(
    category: str = None,
    meal_type: str = None,
    skip: int = 0,
    limit: int = 100,
    use_case: GetDishesUseCase = Depends(get_dishes_use_case),
):
    """料理一覧を取得"""
    return use_case.execute(
        category=category,
        meal_type=meal_type,
        skip=skip,
        limit=limit,
    )


@router.get("/{dish_id}", response_model=Dish)
def get_dish(
    dish_id: int,
    use_case: GetDishByIdUseCase = Depends(get_dish_by_id_use_case),
):
    """特定の料理を取得"""
    return use_case.execute(dish_id)


@router.post("/{dish_id}/generate-recipe", response_model=RecipeDetails)
def generate_dish_recipe(
    dish_id: int,
    use_case: GenerateRecipeUseCase = Depends(get_generate_recipe_use_case),
):
    """Gemini APIでレシピ詳細を自動生成

    - GEMINI_API_KEY 環境変数が必要
    - 既に詳細がある場合はそれを返す
    - 生成結果は recipe_details.json に保存される
    """
    result = use_case.execute(dish_id)
    if not result:
        raise HTTPException(
            status_code=503,
            detail="レシピ生成に失敗しました。GEMINI_API_KEY が設定されているか確認してください"
        )
    return result


@router.post("/generate-recipes/batch")
def generate_recipes_batch(
    category: str = None,
    limit: int = 5,
    use_case: BatchGenerateRecipesUseCase = Depends(get_batch_generate_recipes_use_case),
):
    """未追加レシピをバッチ生成

    - category: カテゴリで絞り込み（主食/主菜/副菜/汁物/デザート）
    - limit: 一度に生成する件数（デフォルト5件、最大20件）
    """
    limit = min(limit, 20)  # 最大20件

    # バッチ生成を実行
    results = use_case.execute(category=category)

    generated = []
    failed = []
    count = 0

    for dish_id, recipe in results.items():
        if count >= limit:
            break
        if recipe:
            generated.append(f"dish_{dish_id}")
            count += 1
        else:
            failed.append(f"dish_{dish_id}")

    return {
        "generated": generated,
        "generated_count": len(generated),
        "failed": failed,
        "message": f"{len(generated)}件のレシピ詳細を生成しました"
    }


@router.get("-categories", name="get_dish_categories")
def get_dish_categories():
    """料理カテゴリ一覧を取得"""
    return [cat.value for cat in DishCategoryEnum]
