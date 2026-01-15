"""
ヘルスチェックAPIエンドポイント

クリーンアーキテクチャ: presentation層
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.database.models import FoodDB, DishDB

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """ヘルスチェック"""
    food_count = db.query(FoodDB).count()
    dish_count = db.query(DishDB).count()
    return {
        "status": "ok",
        "foods": food_count,
        "dishes": dish_count,
    }
