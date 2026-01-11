from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db, FoodDB, DishDB
from app.models.schemas import (
    Food, NutrientTarget, OptimizeRequest, UserPreferences,
    Dish, DishCreate, DailyMenuPlan, DishCategoryEnum
)
from app.optimizer.solver import (
    optimize_daily_menu, db_food_to_model, db_dish_to_model
)

router = APIRouter()

# インメモリのユーザー設定（MVP用）
_user_preferences = UserPreferences()


# ========== 食品（素材）API ==========

@router.get("/foods", response_model=list[Food])
def get_foods(
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """食品（素材）一覧を取得"""
    query = db.query(FoodDB)
    if category:
        query = query.filter(FoodDB.category == category)
    foods_db = query.offset(skip).limit(limit).all()
    return [db_food_to_model(f) for f in foods_db]


@router.get("/foods/search")
def search_foods(
    q: str = None,
    code: str = None,
    category: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """食品検索API

    - q: キーワード検索（スペース区切りでAND検索）
    - code: 文科省コード（mext_code）で完全一致検索
    - category: カテゴリで絞り込み
    """
    query = db.query(FoodDB)

    # コード検索
    if code:
        query = query.filter(FoodDB.mext_code == code)

    # カテゴリ絞り込み
    if category:
        query = query.filter(FoodDB.category == category)

    # キーワード検索（AND検索）
    if q:
        keywords = q.split()
        for kw in keywords:
            query = query.filter(FoodDB.name.like(f"%{kw}%"))

    foods_db = query.limit(limit).all()
    return [
        {
            "mext_code": f.mext_code,
            "name": f.name,
            "category": f.category,
            "calories": f.calories,
        }
        for f in foods_db
    ]


@router.get("/foods/{food_id}", response_model=Food)
def get_food(food_id: int, db: Session = Depends(get_db)):
    """特定の食品を取得"""
    food_db = db.query(FoodDB).filter(FoodDB.id == food_id).first()
    if not food_db:
        raise HTTPException(status_code=404, detail="Food not found")
    return db_food_to_model(food_db)


@router.get("/food-categories")
def get_food_categories(db: Session = Depends(get_db)):
    """食品カテゴリ一覧を取得（文科省分類）"""
    categories = db.query(FoodDB.category).distinct().all()
    return sorted([c[0] for c in categories])


# ========== 料理API ==========

@router.get("/dishes", response_model=list[Dish])
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


@router.get("/dishes/{dish_id}", response_model=Dish)
def get_dish(dish_id: int, db: Session = Depends(get_db)):
    """特定の料理を取得"""
    dish_db = db.query(DishDB).filter(DishDB.id == dish_id).first()
    if not dish_db:
        raise HTTPException(status_code=404, detail="Dish not found")
    return db_dish_to_model(dish_db)


@router.get("/dish-categories")
def get_dish_categories():
    """料理カテゴリ一覧を取得"""
    return [cat.value for cat in DishCategoryEnum]


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """カテゴリ一覧を取得（旧API互換 - 食品カテゴリ）"""
    categories = db.query(FoodDB.category).distinct().all()
    return sorted([c[0] for c in categories])


# ========== 栄養素API ==========

@router.get("/nutrients/target", response_model=NutrientTarget)
def get_nutrient_target():
    """栄養素目標値を取得（デフォルト値）"""
    return NutrientTarget()


# ========== 最適化API ==========

@router.post("/optimize", response_model=DailyMenuPlan)
def optimize_menu(
    request: OptimizeRequest = None,
    db: Session = Depends(get_db)
):
    """1日分のメニューを最適化（料理ベース）

    料理の組み合わせで最適化を行い、栄養バランスの取れた献立を生成します。
    各食事は「主食1 + 主菜1 + 副菜1-2 + 汁物0-1」の構成で最適化されます。
    """
    request = request or OptimizeRequest()
    target = request.target or NutrientTarget()

    # 除外料理ID（将来的にはexcluded_dish_idsに変更）
    excluded = set(request.excluded_food_ids)

    result = optimize_daily_menu(
        db=db,
        target=target,
        excluded_dish_ids=list(excluded),
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="最適化に失敗しました。料理データが不足している可能性があります。"
        )

    return result


# ========== ユーザー設定API ==========

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


# ========== ヘルスチェック ==========

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
