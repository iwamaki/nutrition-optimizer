from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db, FoodDB, DishDB, AllergenType
from app.models.schemas import (
    Food, NutrientTarget, OptimizeRequest, UserPreferences,
    Dish, DishCreate, DailyMenuPlan, DishCategoryEnum,
    MultiDayOptimizeRequest, MultiDayMenuPlan, AllergenEnum,
    RefineOptimizeRequest
)
from app.optimizer.solver import (
    optimize_daily_menu, db_food_to_model, db_dish_to_model,
    solve_multi_day_plan, refine_multi_day_plan
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


@router.post("/optimize/multi-day", response_model=MultiDayMenuPlan)
def optimize_multi_day_menu(
    request: MultiDayOptimizeRequest = None,
    db: Session = Depends(get_db)
):
    """複数日・複数人のメニューを最適化（作り置き対応）

    作り置きを考慮した最適化を行い、調理計画と買い物リストを生成します。

    パラメータ:
    - days: 日数（1-7日）
    - people: 人数（1-6人）
    - target: 栄養素目標（1人1日あたり）
    - excluded_allergens: 除外アレルゲン（卵, 乳, 小麦, そば, 落花生, えび, かに）
    - excluded_dish_ids: 除外料理ID
    - prefer_batch_cooking: 作り置き優先モード（trueで調理回数を最小化）

    戻り値:
    - daily_plans: 日別の献立
    - cooking_tasks: 調理計画（いつ何を何人前作るか）
    - shopping_list: 買い物リスト
    - overall_achievement: 期間全体の栄養達成率
    """
    request = request or MultiDayOptimizeRequest()
    target = request.target or NutrientTarget()

    # アレルゲン除外
    excluded_allergens = [a.value for a in request.excluded_allergens]

    result = solve_multi_day_plan(
        db=db,
        days=request.days,
        people=request.people,
        target=target,
        excluded_allergens=excluded_allergens,
        excluded_dish_ids=request.excluded_dish_ids,
        prefer_batch_cooking=request.prefer_batch_cooking,
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="最適化に失敗しました。料理データが不足しているか、制約が厳しすぎる可能性があります。"
        )

    return result


@router.post("/optimize/multi-day/refine", response_model=MultiDayMenuPlan)
def refine_multi_day_menu(
    request: RefineOptimizeRequest,
    db: Session = Depends(get_db)
):
    """献立を調整して再最適化（イテレーション用）

    ユーザーが提案された献立を見て「残したい料理」「外したい料理」を
    指定して再最適化を行います。栄養バランスが崩れる場合は警告が出ます。

    使い方:
    1. まず /optimize/multi-day で初回の献立を取得
    2. 献立を確認し、気に入った料理のIDを keep_dish_ids に、
       外したい料理のIDを exclude_dish_ids に指定
    3. このAPIを呼び出して再最適化
    4. 満足するまで繰り返し

    パラメータ:
    - days: 日数（1-7日）
    - people: 人数（1-6人）
    - keep_dish_ids: 残したい料理ID（これらは必ず含まれる）
    - exclude_dish_ids: 外したい料理ID（これらは除外される）
    - excluded_allergens: 除外アレルゲン
    - prefer_batch_cooking: 作り置き優先モード

    戻り値:
    - plan_id: プランID
    - daily_plans: 日別の献立
    - cooking_tasks: 調理計画
    - shopping_list: 買い物リスト
    - overall_achievement: 栄養達成率
    - warnings: 栄養素の警告（不足している場合）
    """
    target = request.target or NutrientTarget()

    # アレルゲン除外
    excluded_allergens = [a.value for a in request.excluded_allergens]

    result = refine_multi_day_plan(
        db=db,
        days=request.days,
        people=request.people,
        target=target,
        keep_dish_ids=request.keep_dish_ids,
        exclude_dish_ids=request.exclude_dish_ids,
        excluded_allergens=excluded_allergens,
        prefer_batch_cooking=request.prefer_batch_cooking,
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="調整に失敗しました。指定された条件では献立を生成できません。"
        )

    return result


@router.get("/allergens")
def get_allergens():
    """アレルゲン一覧を取得（7大アレルゲン）"""
    return [{"value": a.value, "name": a.name} for a in AllergenEnum]


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
