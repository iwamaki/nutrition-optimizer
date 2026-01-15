"""
料理関連APIエンドポイント

クリーンアーキテクチャ: presentation層
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.database.models import DishDB
from app.domain.entities import Dish, DishCategoryEnum, RecipeDetails
from app.optimizer.solver import db_dish_to_model
from app.services.recipe_generator import generate_recipe_detail, get_or_generate_recipe_detail
from app.data.loader import get_recipe_details

router = APIRouter(prefix="/dishes", tags=["dishes"])


@router.get("", response_model=list[Dish])
def get_dishes(
    category: str = None,
    meal_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """料理一覧を取得"""
    query = db.query(DishDB)
    if category:
        query = query.filter(DishDB.category == category)
    if meal_type:
        query = query.filter(DishDB.meal_types.contains(meal_type))
    dishes_db = query.offset(skip).limit(limit).all()
    return [db_dish_to_model(d) for d in dishes_db]


@router.get("/{dish_id}", response_model=Dish)
def get_dish(dish_id: int, db: Session = Depends(get_db)):
    """特定の料理を取得"""
    dish_db = db.query(DishDB).filter(DishDB.id == dish_id).first()
    if not dish_db:
        raise HTTPException(status_code=404, detail="Dish not found")
    return db_dish_to_model(dish_db)


@router.post("/{dish_id}/generate-recipe", response_model=RecipeDetails)
def generate_dish_recipe(dish_id: int, db: Session = Depends(get_db)):
    """Gemini APIでレシピ詳細を自動生成

    - GEMINI_API_KEY 環境変数が必要
    - 既に詳細がある場合はそれを返す
    - 生成結果は recipe_details.json に保存される
    """
    dish_db = db.query(DishDB).filter(DishDB.id == dish_id).first()
    if not dish_db:
        raise HTTPException(status_code=404, detail="Dish not found")

    # 材料情報を構築
    ingredients = []
    for ing in dish_db.ingredients:
        ingredients.append({
            "name": ing.food.name if ing.food else "",
            "amount": str(ing.amount)
        })

    # 生成
    result = get_or_generate_recipe_detail(
        dish_name=dish_db.name,
        category=dish_db.category,
        ingredients=ingredients,
        hint=dish_db.instructions or ""
    )

    if not result:
        raise HTTPException(
            status_code=503,
            detail="レシピ生成に失敗しました。GEMINI_API_KEY が設定されているか確認してください"
        )

    return RecipeDetails(**result)


@router.post("/generate-recipes/batch")
def generate_recipes_batch(
    category: str = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """未追加レシピをバッチ生成

    - category: カテゴリで絞り込み（主食/主菜/副菜/汁物/デザート）
    - limit: 一度に生成する件数（デフォルト5件、最大20件）
    """
    limit = min(limit, 20)  # 最大20件

    query = db.query(DishDB)
    if category:
        query = query.filter(DishDB.category == category)
    dishes = query.all()

    generated = []
    skipped = []
    failed = []

    for dish in dishes:
        if len(generated) >= limit:
            break

        # 既存チェック
        existing = get_recipe_details(dish.name)
        if existing:
            skipped.append(dish.name)
            continue

        # 材料情報を構築
        ingredients = [
            {"name": ing.food.name if ing.food else "", "amount": str(ing.amount)}
            for ing in dish.ingredients
        ]

        # 生成
        result = generate_recipe_detail(
            dish_name=dish.name,
            category=dish.category,
            ingredients=ingredients,
            hint=dish.instructions or ""
        )

        if result:
            generated.append(dish.name)
        else:
            failed.append(dish.name)

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
