"""
最適化APIエンドポイント

クリーンアーキテクチャ: presentation層
"""
import json
import time
import asyncio
from typing import AsyncGenerator, Callable

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.domain.entities import NutrientTarget, DailyMenuPlan, MultiDayMenuPlan
from app.models.schemas import (
    OptimizeRequest, MultiDayOptimizeRequest, RefineOptimizeRequest,
    OptimizePhase, OptimizeProgressEvent, OptimizeResultEvent, OptimizeErrorEvent,
    PHASE_MESSAGES,
)
from app.application.use_cases import (
    OptimizeMultiDayMenuUseCase,
    RefineMenuPlanUseCase,
)
from app.presentation.dependencies import (
    get_optimize_multi_day_use_case,
    get_refine_menu_plan_use_case,
    get_solver,
    get_dish_repository,
)
from app.infrastructure.optimizer import PuLPSolver
from app.domain.interfaces import DishRepositoryInterface

router = APIRouter(prefix="/optimize", tags=["optimize"])


@router.post("", response_model=DailyMenuPlan)
def optimize_menu(
    request: OptimizeRequest = None,
    dish_repo: DishRepositoryInterface = Depends(get_dish_repository),
    solver: PuLPSolver = Depends(get_solver),
):
    """1日分のメニューを最適化（料理ベース）

    料理の組み合わせで最適化を行い、栄養バランスの取れた献立を生成します。
    各食事は「主食1 + 主菜1 + 副菜1-2 + 汁物0-1」の構成で最適化されます。
    """
    request = request or OptimizeRequest()
    target = request.target or NutrientTarget()

    # 除外料理ID
    excluded = list(set(request.excluded_food_ids))

    # 料理を取得
    dishes = dish_repo.find_all(limit=1000)
    if not dishes:
        raise HTTPException(
            status_code=500,
            detail="料理データが見つかりません。"
        )

    # 1日分として最適化
    result = solver.optimize_daily_menu(
        dishes=dishes,
        target=target,
        excluded_dish_ids=excluded,
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
    use_case: OptimizeMultiDayMenuUseCase = Depends(get_optimize_multi_day_use_case),
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
    - scheduling_mode: スケジューリングモード（classic/staged）
      - classic: 従来の一括最適化
      - staged: 段階的決定（主食→主菜→副菜・汁物）。たんぱく源ローテーション対応
    - household_type: 世帯タイプ（single/couple/family）

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

    result = use_case.execute(
        days=request.days,
        people=request.people,
        target=target,
        excluded_allergens=excluded_allergens,
        excluded_dish_ids=request.excluded_dish_ids,
        excluded_ingredient_ids=request.excluded_ingredient_ids,
        keep_dish_ids=request.keep_dish_ids,
        preferred_ingredient_ids=request.preferred_ingredient_ids,
        preferred_dish_ids=request.preferred_dish_ids,
        batch_cooking_level=request.batch_cooking_level.value,
        volume_level=request.volume_level.value,
        variety_level=request.variety_level.value,
        meal_settings=meal_settings,
        enabled_nutrients=request.enabled_nutrients,
        optimization_strategy=request.optimization_strategy.value,
        scheduling_mode=request.scheduling_mode.value,
        household_type=request.household_type.value,
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
    use_case: RefineMenuPlanUseCase = Depends(get_refine_menu_plan_use_case),
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

    result = use_case.execute(
        days=request.days,
        people=request.people,
        target=target,
        keep_dish_ids=request.keep_dish_ids,
        exclude_dish_ids=request.exclude_dish_ids,
        excluded_allergens=excluded_allergens,
        excluded_ingredient_ids=request.excluded_ingredient_ids,
        preferred_ingredient_ids=request.preferred_ingredient_ids,
        preferred_dish_ids=request.preferred_dish_ids,
        batch_cooking_level=request.batch_cooking_level.value,
        volume_level=request.volume_level.value,
        variety_level=request.variety_level.value,
        meal_settings=meal_settings,
        enabled_nutrients=request.enabled_nutrients,
        optimization_strategy=request.optimization_strategy.value,
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="調整に失敗しました。指定された条件では献立を生成できません。"
        )

    return result


def _format_sse_event(event_type: str, data: dict) -> str:
    """SSEイベントをフォーマット"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _generate_sse_stream(
    use_case: OptimizeMultiDayMenuUseCase,
    request: MultiDayOptimizeRequest,
) -> AsyncGenerator[str, None]:
    """SSEストリームを生成"""
    import queue
    import threading

    start_time = time.time()
    progress_queue: queue.Queue = queue.Queue()

    # フェーズを進捗率にマッピング
    phase_progress = {
        OptimizePhase.FILTERING_NUTRIENTS: 10,
        OptimizePhase.FILTERING_DISHES: 20,
        OptimizePhase.BUILDING_MODEL: 35,
        OptimizePhase.APPLYING_CONSTRAINTS: 50,
        OptimizePhase.SOLVING: 70,
        OptimizePhase.FINALIZING: 95,
    }

    def report_progress(phase: OptimizePhase) -> None:
        """進捗を報告（コールバック関数）- キューに追加"""
        elapsed = time.time() - start_time
        event = OptimizeProgressEvent(
            phase=phase,
            message=PHASE_MESSAGES[phase],
            progress=phase_progress[phase],
            elapsed_seconds=round(elapsed, 1),
        )
        progress_queue.put(("progress", event.model_dump()))

    def run_optimization():
        """最適化を実行（別スレッド）"""
        try:
            target = request.target or NutrientTarget()
            excluded_allergens = [a.value for a in request.excluded_allergens]
            meal_settings = request.meal_settings.to_dict() if request.meal_settings else None

            result = use_case.execute_with_progress(
                days=request.days,
                people=request.people,
                target=target,
                excluded_allergens=excluded_allergens,
                excluded_dish_ids=request.excluded_dish_ids,
                excluded_ingredient_ids=request.excluded_ingredient_ids,
                keep_dish_ids=request.keep_dish_ids,
                preferred_ingredient_ids=request.preferred_ingredient_ids,
                preferred_dish_ids=request.preferred_dish_ids,
                batch_cooking_level=request.batch_cooking_level.value,
                volume_level=request.volume_level.value,
                variety_level=request.variety_level.value,
                meal_settings=meal_settings,
                enabled_nutrients=request.enabled_nutrients,
                optimization_strategy=request.optimization_strategy.value,
                scheduling_mode=request.scheduling_mode.value,
                household_type=request.household_type.value,
                progress_callback=report_progress,
            )
            progress_queue.put(("result", result))
        except Exception as e:
            progress_queue.put(("error", str(e)))

    try:
        # 最適化を別スレッドで開始
        optimization_thread = threading.Thread(target=run_optimization)
        optimization_thread.start()

        result = None
        while True:
            try:
                # キューから進捗を取得（タイムアウト付き）
                event_type, data = progress_queue.get(timeout=0.1)

                if event_type == "progress":
                    yield _format_sse_event("progress", data)
                elif event_type == "result":
                    result = data
                    break
                elif event_type == "error":
                    error_event = OptimizeErrorEvent(message=data)
                    yield _format_sse_event("error", error_event.model_dump())
                    return
            except queue.Empty:
                # キューが空の場合、スレッドがまだ実行中か確認
                if not optimization_thread.is_alive():
                    break
                # スレッドが実行中ならasyncioに制御を戻す
                await asyncio.sleep(0.05)

        # スレッドの終了を待機
        optimization_thread.join(timeout=1.0)

        # 結果を送信
        if result:
            # 完了の進捗
            elapsed = time.time() - start_time
            final_progress = OptimizeProgressEvent(
                phase=OptimizePhase.FINALIZING,
                message="完了しました",
                progress=100,
                elapsed_seconds=round(elapsed, 1),
            )
            yield _format_sse_event("progress", final_progress.model_dump())

            # 結果イベント（直接dictを構築）
            result_data = {
                "type": "result",
                "plan": result.model_dump() if hasattr(result, 'model_dump') else result.dict(),
            }
            yield _format_sse_event("result", result_data)
        else:
            error_event = OptimizeErrorEvent(
                message="最適化に失敗しました。料理データが不足しているか、制約が厳しすぎる可能性があります。"
            )
            yield _format_sse_event("error", error_event.model_dump())

    except Exception as e:
        error_event = OptimizeErrorEvent(message=str(e))
        yield _format_sse_event("error", error_event.model_dump())


@router.post("/multi-day/stream")
async def optimize_multi_day_menu_stream(
    request: MultiDayOptimizeRequest = None,
    use_case: OptimizeMultiDayMenuUseCase = Depends(get_optimize_multi_day_use_case),
):
    """複数日・複数人のメニューを最適化（SSEストリーム）

    Server-Sent Events (SSE) で進捗をリアルタイム送信します。

    イベントタイプ:
    - progress: 進捗情報（phase, message, progress, elapsed_seconds）
    - result: 最適化結果（plan）
    - error: エラー情報（message）

    使用例（JavaScript）:
    ```javascript
    const eventSource = new EventSource('/api/v1/optimize/multi-day/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ days: 3, people: 2 })
    });
    eventSource.addEventListener('progress', (e) => console.log(JSON.parse(e.data)));
    eventSource.addEventListener('result', (e) => console.log(JSON.parse(e.data)));
    eventSource.addEventListener('error', (e) => console.error(JSON.parse(e.data)));
    ```
    """
    request = request or MultiDayOptimizeRequest()

    return StreamingResponse(
        _generate_sse_stream(use_case, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # nginx buffering を無効化
        },
    )
