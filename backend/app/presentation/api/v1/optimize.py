"""
最適化APIエンドポイント

クリーンアーキテクチャ: presentation層
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.domain.entities import NutrientTarget, DailyMenuPlan, MultiDayMenuPlan
from app.models.schemas import OptimizeRequest, MultiDayOptimizeRequest, RefineOptimizeRequest
from app.optimizer.solver import (
    optimize_daily_menu,
    solve_multi_day_plan,
    refine_multi_day_plan,
)

router = APIRouter(prefix="/optimize", tags=["optimize"])


@router.post("", response_model=DailyMenuPlan)
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

    # 除外料理ID
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


@router.post("/multi-day", response_model=MultiDayMenuPlan)
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
    - batch_cooking_level: 作り置き優先度（small/normal/large）
    - volume_level: カロリー目標レベル（small/normal/large）
    - variety_level: 料理の繰り返し（small/normal/large）
    - meal_settings: 朝昼夜別の設定（enabled, volume）

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

    # 朝昼夜別設定
    meal_settings = request.meal_settings.to_dict() if request.meal_settings else None

    result = solve_multi_day_plan(
        db=db,
        days=request.days,
        people=request.people,
        target=target,
        excluded_allergens=excluded_allergens,
        excluded_dish_ids=request.excluded_dish_ids,
        keep_dish_ids=request.keep_dish_ids,
        preferred_ingredient_ids=request.preferred_ingredient_ids,
        preferred_dish_ids=request.preferred_dish_ids,
        batch_cooking_level=request.batch_cooking_level.value,
        volume_level=request.volume_level.value,
        variety_level=request.variety_level.value,
        meal_settings=meal_settings,
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="最適化に失敗しました。料理データが不足しているか、制約が厳しすぎる可能性があります。"
        )

    return result


@router.post("/multi-day/refine", response_model=MultiDayMenuPlan)
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
    - batch_cooking_level: 作り置き優先度（small/normal/large）
    - volume_level: カロリー目標レベル（small/normal/large）
    - variety_level: 料理の繰り返し（small/normal/large）
    - meal_settings: 朝昼夜別の設定（enabled, volume）

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

    # 朝昼夜別設定
    meal_settings = request.meal_settings.to_dict() if request.meal_settings else None

    result = refine_multi_day_plan(
        db=db,
        days=request.days,
        people=request.people,
        target=target,
        keep_dish_ids=request.keep_dish_ids,
        exclude_dish_ids=request.exclude_dish_ids,
        excluded_allergens=excluded_allergens,
        preferred_ingredient_ids=request.preferred_ingredient_ids,
        preferred_dish_ids=request.preferred_dish_ids,
        batch_cooking_level=request.batch_cooking_level.value,
        volume_level=request.volume_level.value,
        variety_level=request.variety_level.value,
        meal_settings=meal_settings,
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="調整に失敗しました。指定された条件では献立を生成できません。"
        )

    return result
