from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db, FoodDB
from app.models.schemas import (
    Food, NutrientTarget, MenuPlan, OptimizeRequest, UserPreferences
)
from app.optimizer.solver import optimize_daily_menu, db_food_to_model

router = APIRouter()

# インメモリのユーザー設定（MVP用）
_user_preferences = UserPreferences()


@router.get("/foods", response_model=list[Food])
def get_foods(
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """食材一覧を取得"""
    query = db.query(FoodDB)
    if category:
        query = query.filter(FoodDB.category == category)
    foods_db = query.offset(skip).limit(limit).all()
    return [db_food_to_model(f) for f in foods_db]


@router.get("/foods/{food_id}", response_model=Food)
def get_food(food_id: int, db: Session = Depends(get_db)):
    """特定の食材を取得"""
    food_db = db.query(FoodDB).filter(FoodDB.id == food_id).first()
    if not food_db:
        raise HTTPException(status_code=404, detail="Food not found")
    return db_food_to_model(food_db)


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """食材カテゴリ一覧を取得"""
    categories = db.query(FoodDB.category).distinct().all()
    return [c[0] for c in categories]


@router.get("/nutrients/target", response_model=NutrientTarget)
def get_nutrient_target():
    """栄養素目標値を取得（デフォルト値）"""
    return NutrientTarget()


@router.post("/optimize", response_model=MenuPlan)
def optimize_menu(
    request: OptimizeRequest = None,
    db: Session = Depends(get_db)
):
    """1日分のメニューを最適化"""
    request = request or OptimizeRequest()
    target = request.target or NutrientTarget()

    # ユーザー設定から除外食材を追加
    excluded = set(request.excluded_food_ids) | set(_user_preferences.excluded_food_ids)

    result = optimize_daily_menu(
        db=db,
        target=target,
        excluded_food_ids=list(excluded),
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="最適化に失敗しました。食材データが不足している可能性があります。"
        )

    return result


@router.get("/preferences", response_model=UserPreferences)
def get_preferences():
    """ユーザー設定を取得"""
    return _user_preferences


@router.put("/preferences", response_model=UserPreferences)
def update_preferences(prefs: UserPreferences):
    """ユーザー設定を更新"""
    global _user_preferences
    _user_preferences = prefs
    return _user_preferences


@router.get("/health")
def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}
