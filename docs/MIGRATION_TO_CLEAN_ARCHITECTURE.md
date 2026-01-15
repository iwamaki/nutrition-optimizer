# クリーンアーキテクチャ完全移行タスク

## 概要

既存の `app/api/routes.py` と `app/optimizer/solver.py` を削除し、新しいクリーンアーキテクチャ構造に完全移行するためのタスクリスト。

**作成日:** 2026-01-16
**ステータス:** 未着手

---

## 現状の依存関係

```
app/main.py
  └─→ app/api/routes.py (削除対象)
        └─→ app/optimizer/solver.py (削除対象)
        └─→ app/services/recipe_generator.py (削除対象)

app/presentation/api/v1/*.py (新規作成済み)
  └─→ app/optimizer/solver.py (依存を解消する必要あり)
  └─→ app/services/recipe_generator.py (依存を解消する必要あり)
```

---

## 移行タスク

### Task 1: main.py を新ルーターに切り替え

**ファイル:** `app/main.py`

**変更内容:**
```python
# 変更前
from app.api.routes import router
app.include_router(router, prefix="/api/v1")

# 変更後
from app.presentation.api.v1 import router
app.include_router(router, prefix="/api/v1")
```

**追加:** 例外ハンドラの追加
```python
from app.core.exceptions import (
    AppException,
    EntityNotFoundError,
    OptimizationFailedError,
)
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(status_code=404, content=exc.to_dict())

@app.exception_handler(OptimizationFailedError)
async def optimization_failed_handler(request: Request, exc: OptimizationFailedError):
    return JSONResponse(status_code=500, content=exc.to_dict())

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=500, content=exc.to_dict())
```

---

### Task 2: presentation/api/v1/dishes.py を新アーキテクチャに移行

**ファイル:** `app/presentation/api/v1/dishes.py`

**現状の依存:**
```python
from app.optimizer.solver import db_dish_to_model
from app.services.recipe_generator import generate_recipe_detail, get_or_generate_recipe_detail
from app.data.loader import get_recipe_details
```

**変更後:**
```python
from fastapi import Depends
from app.presentation.dependencies import (
    get_dish_repository,
    get_dishes_use_case,
    get_dish_by_id_use_case,
    get_generate_recipe_use_case,
    get_batch_generate_recipes_use_case,
)
```

**エンドポイント変更例:**
```python
# 変更前
@router.get("", response_model=list[Dish])
def get_dishes(category: str = None, meal_type: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(DishDB)
    ...
    return [db_dish_to_model(d) for d in dishes_db]

# 変更後
@router.get("", response_model=list[Dish])
def get_dishes(
    category: str = None,
    meal_type: str = None,
    skip: int = 0,
    limit: int = 100,
    use_case: GetDishesUseCase = Depends(get_dishes_use_case),
):
    return use_case.execute(category=category, meal_type=meal_type, skip=skip, limit=limit)
```

---

### Task 3: presentation/api/v1/optimize.py を新アーキテクチャに移行

**ファイル:** `app/presentation/api/v1/optimize.py`

**現状の依存:**
```python
from app.optimizer.solver import (
    optimize_daily_menu,
    solve_multi_day_plan,
    refine_multi_day_plan,
)
```

**変更後:**
```python
from fastapi import Depends
from app.presentation.dependencies import (
    get_optimize_multi_day_use_case,
    get_refine_menu_plan_use_case,
)
from app.application.use_cases import OptimizeMultiDayMenuUseCase, RefineMenuPlanUseCase
```

**エンドポイント変更例:**
```python
# 変更前
@router.post("/multi-day", response_model=MultiDayMenuPlan)
def optimize_multi_day_menu(request: MultiDayOptimizeRequest = None, db: Session = Depends(get_db)):
    result = solve_multi_day_plan(db=db, days=request.days, ...)
    return result

# 変更後
@router.post("/multi-day", response_model=MultiDayMenuPlan)
def optimize_multi_day_menu(
    request: MultiDayOptimizeRequest = None,
    use_case: OptimizeMultiDayMenuUseCase = Depends(get_optimize_multi_day_use_case),
):
    result = use_case.execute(
        days=request.days,
        people=request.people,
        target=request.target,
        excluded_allergens=[a.value for a in request.excluded_allergens],
        ...
    )
    return result
```

**注意:** `optimize_daily_menu` は現在ユースケースがないため、以下のいずれかが必要:
1. `OptimizeDailyMenuUseCase` を新規作成
2. または `OptimizeMultiDayMenuUseCase` を `days=1` で使用

---

### Task 4: presentation/api/v1/ingredients.py を新アーキテクチャに移行

**ファイル:** `app/presentation/api/v1/ingredients.py`

**現状の依存:**
```python
from app.infrastructure.database.models import IngredientDB
```

**変更後:**
```python
from app.presentation.dependencies import (
    get_ingredients_use_case,
    get_ingredient_by_id_use_case,
)
```

---

### Task 5: 古いファイルを削除

移行完了後に削除するファイル:

```
app/api/routes.py          # 412行
app/optimizer/solver.py    # 1564行（関数は新クラスに移行済み）
app/services/recipe_generator.py  # 230行（新サービスに移行済み）
```

**削除前の確認:**
```bash
# 依存がないことを確認
grep -r "from app.api.routes" app/
grep -r "from app.optimizer.solver" app/
grep -r "from app.services.recipe_generator" app/
```

---

## 移行後のディレクトリ構造

```
backend/app/
├── core/                      # 共通設定 ✅
├── domain/                    # ドメイン層 ✅
│   ├── entities/
│   ├── interfaces/
│   └── services/
├── application/               # アプリケーション層 ✅
│   ├── use_cases/
│   ├── dto/
│   └── services/
├── infrastructure/            # インフラ層 ✅
│   ├── database/
│   ├── repositories/
│   ├── optimizer/             # PuLPSolver
│   └── external/              # GeminiRecipeGenerator
├── presentation/              # プレゼンテーション層
│   ├── api/v1/               # ← Task 2-4 で移行
│   ├── schemas/
│   └── dependencies.py        # ✅
├── data/loader.py            # そのまま維持
└── main.py                    # ← Task 1 で更新

削除対象:
├── api/routes.py             # ← Task 5 で削除
├── optimizer/solver.py       # ← Task 5 で削除
└── services/recipe_generator.py  # ← Task 5 で削除
```

---

## 検証手順

### 各タスク完了後

```bash
# インポートテスト
python -c "from app.main import app; print(f'Routes: {len(app.routes)}')"

# サーバー起動テスト
uvicorn app.main:app --reload

# Swagger UI確認
# http://localhost:8000/docs

# テスト実行
pytest tests/
```

### 全タスク完了後

```bash
# 古いファイルへの依存がないことを確認
grep -r "from app.api.routes" app/
grep -r "from app.optimizer.solver" app/
grep -r "from app.services.recipe_generator" app/

# 上記が何も出力しなければ削除可能
```

---

## 注意事項

1. **後方互換性**: APIのパス `/api/v1/*` とレスポンス形式は変更しない
2. **段階的移行**: 1タスクずつ完了し、動作確認してから次へ
3. **ロールバック**: 問題発生時は `git checkout` で戻せる
4. **テスト**: 移行後も21件のテストが成功することを確認

---

## 追加実装が必要なもの（オプション）

1. **OptimizeDailyMenuUseCase**: 1日分最適化のユースケース（現在は未実装）
2. **統合テスト**: APIエンドポイントのE2Eテスト
3. **Pydantic v2対応**: 警告の解消

---

*最終更新: 2026-01-16*
