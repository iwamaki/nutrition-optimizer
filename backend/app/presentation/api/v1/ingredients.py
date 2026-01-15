"""
食材関連APIエンドポイント

クリーンアーキテクチャ: presentation層
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.database.models import IngredientDB
from app.domain.entities import Ingredient

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[Ingredient])
def get_ingredients(
    category: str = None,
    db: Session = Depends(get_db)
):
    """基本食材一覧を取得（正規化された食材マスタ）

    フロントエンドの「よく使う食材」選択や買い物リストに使用
    """
    query = db.query(IngredientDB)
    if category:
        query = query.filter(IngredientDB.category == category)
    ingredients_db = query.order_by(IngredientDB.id).all()
    return [
        Ingredient(
            id=ing.id,
            name=ing.name,
            category=ing.category,
            mext_code=ing.mext_code or "",
            emoji=ing.emoji or "",
        )
        for ing in ingredients_db
    ]


@router.get("/{ingredient_id}", response_model=Ingredient)
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """特定の基本食材を取得"""
    ing_db = db.query(IngredientDB).filter(IngredientDB.id == ingredient_id).first()
    if not ing_db:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return Ingredient(
        id=ing_db.id,
        name=ing_db.name,
        category=ing_db.category,
        mext_code=ing_db.mext_code or "",
        emoji=ing_db.emoji or "",
    )


@router.get("-categories", name="get_ingredient_categories")
def get_ingredient_categories(db: Session = Depends(get_db)):
    """基本食材のカテゴリ一覧を取得"""
    categories = db.query(IngredientDB.category).distinct().all()
    # 定義順でソート
    order = ['穀類', '野菜類', 'きのこ類', '藻類', '豆類', 'いも類', '肉類', '魚介類', '卵類', '乳類', '果実類', '調味料']
    result = [c[0] for c in categories]
    return sorted(result, key=lambda x: order.index(x) if x in order else 99)
