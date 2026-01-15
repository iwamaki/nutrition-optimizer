# クリーンアーキテクチャ リファクタリング計画書

## 概要

FastAPI バックエンドをクリーンアーキテクチャパターンに従ってリファクタリングし、保守性・拡張性・可読性を向上させる。

**作成日:** 2026-01-16
**ステータス:** Phase 1-3 完了、Phase 4-6 未着手

---

## 目次

1. [現在の進捗状況](#現在の進捗状況)
2. [ディレクトリ構造](#ディレクトリ構造)
3. [完了済みフェーズ詳細](#完了済みフェーズ詳細)
4. [Phase 4: application層・infrastructure/optimizer 実装](#phase-4-application層infrastructureoptimizer-実装)
5. [Phase 5: presentation層 実装](#phase-5-presentation層-実装)
6. [Phase 6: テスト追加](#phase-6-テスト追加)
7. [既存ファイル参照情報](#既存ファイル参照情報)
8. [依存関係ルール](#依存関係ルール)

---

## 現在の進捗状況

| Phase | 内容 | 状態 |
|-------|------|------|
| 1 | core/ ディレクトリ作成 | ✅ 完了 |
| 1 | domain/entities/ 作成 | ✅ 完了 |
| 1 | domain/interfaces/ 作成 | ✅ 完了 |
| 2 | infrastructure/database/ 整理 | ✅ 完了 |
| 2 | infrastructure/repositories/ 実装 | ✅ 完了 |
| 3 | domain/services/ 作成 | ✅ 完了 |
| 3 | 後方互換性ブリッジ作成 | ✅ 完了 |
| 4 | infrastructure/optimizer/ 整理 | 🔲 未着手 |
| 4 | infrastructure/external/ 整理 | 🔲 未着手 |
| 4 | application/use_cases/ 実装 | 🔲 未着手 |
| 5 | presentation/api/v1/ 分割 | 🔲 未着手 |
| 5 | main.py 更新・依存性注入設定 | 🔲 未着手 |
| 6 | テスト追加 | 🔲 未着手 |

---

## ディレクトリ構造

### 現在の状態

```
backend/app/
├── core/                          ✅ 完了
│   ├── __init__.py
│   ├── config.py                  # Settings クラス、settings インスタンス
│   ├── exceptions.py              # AppException, EntityNotFoundError等
│   └── logging.py                 # setup_logging(), get_logger()
│
├── domain/                        ✅ 完了
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py           # 全エンティティをre-export
│   │   ├── enums.py              # AllergenEnum, MealTypeEnum, DishCategoryEnum等
│   │   ├── food.py               # Food, FoodPortion, NutrientTarget
│   │   ├── ingredient.py         # Ingredient
│   │   ├── dish.py               # Dish, DishBase, DishIngredient, DishPortion, RecipeDetails, CookingFactor
│   │   ├── meal_plan.py          # MealPlan, DailyMenuPlan, DailyMealAssignment, MultiDayMenuPlan, NutrientWarning
│   │   ├── user_preference.py    # UserPreferences
│   │   └── shopping.py           # ShoppingItem, CookingTask
│   │
│   ├── interfaces/
│   │   ├── __init__.py           # 全インターフェースをre-export
│   │   ├── dish_repository.py    # DishRepositoryInterface
│   │   ├── food_repository.py    # FoodRepositoryInterface
│   │   ├── ingredient_repository.py # IngredientRepositoryInterface
│   │   └── preference_repository.py # PreferenceRepositoryInterface
│   │
│   └── services/
│       ├── __init__.py
│       ├── constants.py          # ALL_NUTRIENTS, NUTRIENT_WEIGHTS, MEAL_RATIOS等
│       ├── nutrient_calculator.py # NutrientCalculator
│       └── unit_converter.py     # UnitConverter
│
├── infrastructure/                ✅ 部分完了
│   ├── __init__.py
│   ├── database/                  ✅ 完了
│   │   ├── __init__.py
│   │   ├── connection.py         # engine, SessionLocal, Base, init_db, get_db
│   │   └── models.py             # FoodDB, DishDB等 SQLAlchemy ORM
│   │
│   ├── repositories/              ✅ 完了
│   │   ├── __init__.py
│   │   ├── sqlalchemy_dish_repository.py
│   │   ├── sqlalchemy_food_repository.py
│   │   ├── sqlalchemy_ingredient_repository.py
│   │   └── in_memory_preference_repository.py
│   │
│   ├── optimizer/                 🔲 Phase 4で実装
│   │   └── __init__.py           # 空ファイルのみ
│   │
│   └── external/                  🔲 Phase 4で実装
│       └── __init__.py           # 空ファイルのみ
│
├── application/                   🔲 Phase 4で実装
│   ├── __init__.py
│   ├── use_cases/
│   │   └── __init__.py
│   ├── dto/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
│
├── presentation/                  🔲 Phase 5で実装
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       └── __init__.py
│   └── schemas/
│       └── __init__.py
│
├── db/database.py                 ✅ 後方互換ブリッジ（infrastructure/database/からre-export）
├── models/schemas.py              📌 既存維持（Phase 5で一部移行予定）
├── api/routes.py                  📌 既存維持（Phase 5で分割予定）
├── optimizer/solver.py            📌 既存維持（Phase 4で移行予定）
├── services/recipe_generator.py   📌 既存維持（Phase 4で移行予定）
├── data/loader.py                 📌 既存維持
└── main.py                        📌 既存維持（Phase 5で更新予定）
```

---

## 完了済みフェーズ詳細

### core/ モジュール

#### config.py
```python
from app.core.config import settings

# 使用例
settings.database_url      # "sqlite:///./nutrition.db"
settings.allowed_origins   # ["http://localhost:3000", ...]
settings.debug             # True (development環境)
settings.gemini_api_key    # 環境変数から取得
settings.solver_timeout    # 30
```

#### exceptions.py
```python
from app.core.exceptions import (
    AppException,           # 基底例外
    EntityNotFoundError,    # エンティティ未発見 (404)
    OptimizationFailedError,# 最適化失敗 (500)
    ExternalServiceError,   # 外部サービスエラー
    ValidationError,        # バリデーションエラー (400)
    DuplicateEntityError,   # 重複エラー
    InsufficientDataError,  # データ不足エラー
)

# 使用例
raise EntityNotFoundError("Dish", dish_id)
raise OptimizationFailedError("No feasible solution", solver_status="Infeasible")
```

#### logging.py
```python
from app.core.logging import setup_logging, get_logger

# アプリ起動時
logger = setup_logging()

# モジュール内で使用
logger = get_logger(__name__)
logger.info("Processing...")
```

### domain/entities/ モジュール

#### 全エンティティのインポート
```python
from app.domain.entities import (
    # Enums
    AllergenEnum,           # 卵, 乳, 小麦, そば, 落花生, えび, かに
    VolumeLevelEnum,        # small, normal, large
    VarietyLevelEnum,       # small, normal, large
    BatchCookingLevelEnum,  # small, normal, large
    MealTypeEnum,           # breakfast, lunch, dinner, snack
    DishCategoryEnum,       # 主食, 主菜, 副菜, 汁物, デザート
    CookingMethodEnum,      # 生, 茹でる, 蒸す, 焼く, 炒める, 揚げる, 煮る, 電子レンジ
    MealPresetEnum,         # minimal, light, standard, full, japanese, custom

    # Food
    Food,                   # 食品（文科省成分表ベース）
    FoodPortion,            # 食品と分量
    NutrientTarget,         # 栄養素目標値（1日）
    Ingredient,             # 基本食材

    # Dish
    Dish,                   # 料理（栄養素計算済み）
    DishBase,               # 料理ベース
    DishIngredient,         # 料理の材料
    DishPortion,            # 料理と分量
    RecipeDetails,          # レシピ詳細
    CookingFactor,          # 調理係数

    # Meal Plan
    MealPlan,               # 1食分のメニュー
    DailyMenuPlan,          # 1日分のメニュープラン
    DailyMealAssignment,    # 1日分の食事割り当て（複数日用）
    MultiDayMenuPlan,       # 複数日メニュープラン
    NutrientWarning,        # 栄養素警告

    # User
    UserPreferences,        # ユーザー設定

    # Shopping
    ShoppingItem,           # 買い物リストアイテム
    CookingTask,            # 調理タスク
)
```

### domain/interfaces/ モジュール

#### DishRepositoryInterface
```python
from app.domain.interfaces import DishRepositoryInterface

class DishRepositoryInterface(ABC):
    def find_by_id(self, dish_id: int) -> Optional[Dish]: ...
    def find_all(self, category=None, meal_type=None, skip=0, limit=100) -> list[Dish]: ...
    def find_by_ids(self, dish_ids: list[int]) -> list[Dish]: ...
    def find_excluding_allergens(self, allergens: list[str]) -> list[Dish]: ...
    def count(self, category=None, meal_type=None) -> int: ...
    def get_categories(self) -> list[str]: ...
```

#### FoodRepositoryInterface
```python
from app.domain.interfaces import FoodRepositoryInterface

class FoodRepositoryInterface(ABC):
    def find_by_id(self, food_id: int) -> Optional[Food]: ...
    def find_by_mext_code(self, mext_code: str) -> Optional[Food]: ...
    def find_all(self, category=None, skip=0, limit=100) -> list[Food]: ...
    def search(self, keyword: str, category=None, limit=50) -> list[Food]: ...
    def count(self, category=None) -> int: ...
    def get_categories(self) -> list[str]: ...
    def get_allergens_for_food(self, food_id: int) -> list[str]: ...
```

#### IngredientRepositoryInterface
```python
from app.domain.interfaces import IngredientRepositoryInterface

class IngredientRepositoryInterface(ABC):
    def find_by_id(self, ingredient_id: int) -> Optional[Ingredient]: ...
    def find_all(self, category=None, skip=0, limit=100) -> list[Ingredient]: ...
    def find_by_ids(self, ingredient_ids: list[int]) -> list[Ingredient]: ...
    def count(self, category=None) -> int: ...
    def get_categories(self) -> list[str]: ...
```

#### PreferenceRepositoryInterface
```python
from app.domain.interfaces import PreferenceRepositoryInterface

class PreferenceRepositoryInterface(ABC):
    def get(self) -> UserPreferences: ...
    def save(self, preferences: UserPreferences) -> UserPreferences: ...
```

### domain/services/ モジュール

#### constants.py
```python
from app.domain.services.constants import (
    ALL_NUTRIENTS,                    # 全23栄養素リスト
    NUTRIENT_WEIGHTS,                 # 栄養素の重み（最適化時の優先度）
    MEAL_RATIOS,                      # 食事ごとのカロリー比率
    DEFAULT_MEAL_CATEGORY_CONSTRAINTS,# デフォルトのカテゴリ別品数制約
    CATEGORY_CONSTRAINTS_BY_VOLUME,   # volumeレベルからの変換
)
```

#### NutrientCalculator
```python
from app.domain.services import NutrientCalculator

calc = NutrientCalculator()

# 1食分の栄養素合計
nutrients = calc.calculate_meal_nutrients(dish_portions)

# 1日分の栄養素合計
daily_nutrients = calc.calculate_daily_nutrients({
    "breakfast": [...],
    "lunch": [...],
    "dinner": [...]
})

# 達成率計算
achievement = calc.calculate_achievement_rate(nutrients, target)

# 警告生成
warnings = calc.generate_warnings(nutrients, target, threshold=80.0)
```

#### UnitConverter
```python
from app.domain.services import UnitConverter

converter = UnitConverter()

# グラムを実用単位に変換
display, unit = converter.convert_to_display_unit("玉ねぎ", 200)
# -> ("1", "個")

# 食品成分表の名称を正規化
name = converter.normalize_food_name("＜野菜類＞たまねぎ　りん茎　生")
# -> "玉ねぎ"
```

### infrastructure/repositories/ モジュール

```python
from app.infrastructure.repositories import (
    SQLAlchemyDishRepository,
    SQLAlchemyFoodRepository,
    SQLAlchemyIngredientRepository,
    InMemoryPreferenceRepository,
)

# 使用例
from sqlalchemy.orm import Session

def get_dish_repository(db: Session):
    return SQLAlchemyDishRepository(db)
```

---

## Phase 4: application層・infrastructure/optimizer 実装

### 4.1 infrastructure/optimizer/ への移行

**現在のファイル:** `app/optimizer/solver.py` (1564行)

**移行計画:**
```
infrastructure/optimizer/
├── __init__.py
├── pulp_solver.py          # PuLP最適化エンジン本体
├── constraints.py          # 制約条件定義
└── objective.py            # 目的関数定義
```

**pulp_solver.py に移行する関数:**
| 関数名 | 行番号 | 説明 |
|--------|--------|------|
| `optimize_meal()` | 241-408 | 1食分最適化 |
| `optimize_daily_menu()` | 411-469 | 1日分最適化 |
| `solve_multi_day_plan()` | 599-1014 | 複数日最適化（最大関数） |
| `_extract_multi_day_result()` | 1017-1115 | 結果抽出 |
| `_generate_shopping_list()` | 1362-1408 | 買い物リスト生成 |
| `_fallback_multi_day_plan()` | 1411-1483 | フォールバック処理 |
| `refine_multi_day_plan()` | 1483-1534 | 献立調整 |

**既にdomain/services/に移行済み:**
- `ALL_NUTRIENTS` → `constants.py`
- `NUTRIENT_WEIGHTS` → `constants.py`
- `MEAL_RATIOS` → `constants.py`
- `DEFAULT_MEAL_CATEGORY_CONSTRAINTS` → `constants.py`
- `CATEGORY_CONSTRAINTS_BY_VOLUME` → `constants.py`
- `_calc_achievement()` → `NutrientCalculator.calculate_achievement_rate()`
- `_generate_warnings()` → `NutrientCalculator.generate_warnings()`
- `_convert_to_display_unit()` → `UnitConverter.convert_to_display_unit()`
- `_normalize_food_name()` → `UnitConverter.normalize_food_name()`

**db_dish_to_model()について:**
- `SQLAlchemyDishRepository._to_entity()` として既に実装済み
- solver.pyの`db_dish_to_model()`は後方互換性のため維持するか、リポジトリを使用するよう変更

### 4.2 infrastructure/external/ への移行

**現在のファイル:** `app/services/recipe_generator.py` (230行)

**移行計画:**
```
infrastructure/external/
├── __init__.py
└── gemini_recipe_generator.py
    - init_gemini()
    - build_prompt()
    - extract_json_from_response()
    - generate_recipe_detail()
    - get_or_generate_recipe_detail()
```

### 4.3 application/use_cases/ 実装

**実装するユースケース:**
```
application/use_cases/
├── __init__.py
├── optimize_daily_menu.py      # OptimizeDailyMenuUseCase
├── optimize_multi_day_menu.py  # OptimizeMultiDayMenuUseCase
├── refine_menu_plan.py         # RefineMenuPlanUseCase
├── get_dishes.py               # GetDishesUseCase, GetDishByIdUseCase
├── get_ingredients.py          # GetIngredientsUseCase
├── generate_recipe.py          # GenerateRecipeUseCase
└── manage_preferences.py       # GetPreferencesUseCase, UpdatePreferencesUseCase
```

**ユースケース実装例:**
```python
# application/use_cases/optimize_multi_day_menu.py
from dataclasses import dataclass
from app.domain.interfaces import DishRepositoryInterface
from app.domain.entities import NutrientTarget, MultiDayMenuPlan
from app.domain.services import NutrientCalculator

@dataclass
class OptimizeMultiDayMenuUseCase:
    dish_repo: DishRepositoryInterface
    solver: "PuLPSolver"  # infrastructure/optimizer/pulp_solver.py
    nutrient_calc: NutrientCalculator

    def execute(
        self,
        days: int,
        people: int,
        target: NutrientTarget,
        excluded_allergens: list[str] = None,
        excluded_dish_ids: list[int] = None,
        keep_dish_ids: list[int] = None,
        preferred_ingredient_ids: list[int] = None,
        preferred_dish_ids: list[int] = None,
        batch_cooking_level: str = "normal",
        volume_level: str = "normal",
        variety_level: str = "normal",
        meal_settings: dict = None,
    ) -> MultiDayMenuPlan:
        # 1. 料理を取得
        if excluded_allergens:
            dishes = self.dish_repo.find_excluding_allergens(excluded_allergens)
        else:
            dishes = self.dish_repo.find_all(limit=1000)

        # 2. 除外料理をフィルタ
        if excluded_dish_ids:
            dishes = [d for d in dishes if d.id not in set(excluded_dish_ids)]

        # 3. 最適化実行
        result = self.solver.solve_multi_day(
            dishes=dishes,
            days=days,
            people=people,
            target=target,
            keep_dish_ids=keep_dish_ids,
            preferred_ingredient_ids=preferred_ingredient_ids,
            preferred_dish_ids=preferred_dish_ids,
            batch_cooking_level=batch_cooking_level,
            volume_level=volume_level,
            variety_level=variety_level,
            meal_settings=meal_settings,
        )

        # 4. 警告生成
        if result:
            warnings = self.nutrient_calc.generate_warnings(
                result.overall_nutrients, target
            )
            result.warnings = warnings

        return result
```

### 4.4 application/dto/ 実装

```python
# application/dto/request.py
from pydantic import BaseModel, Field
from typing import Optional
from app.domain.entities import NutrientTarget, AllergenEnum

class OptimizeMultiDayRequest(BaseModel):
    days: int = Field(default=1, ge=1, le=7)
    people: int = Field(default=1, ge=1, le=6)
    target: Optional[NutrientTarget] = None
    excluded_allergens: list[AllergenEnum] = Field(default_factory=list)
    excluded_dish_ids: list[int] = Field(default_factory=list)
    keep_dish_ids: list[int] = Field(default_factory=list)
    preferred_ingredient_ids: list[int] = Field(default_factory=list)
    preferred_dish_ids: list[int] = Field(default_factory=list)
    batch_cooking_level: str = "normal"
    volume_level: str = "normal"
    variety_level: str = "normal"
    meal_settings: Optional[dict] = None
```

---

## Phase 5: presentation層 実装

### 5.1 routes.py の分割

**現在のファイル:** `app/api/routes.py` (412行)

**分割先:**
```
presentation/api/v1/
├── __init__.py
├── router.py               # メインルーター（全サブルーターを集約）
├── ingredients.py          # 食材関連
├── dishes.py               # 料理関連
├── optimize.py             # 最適化
├── preferences.py          # 設定
└── health.py               # ヘルスチェック
```

**現在のエンドポイント一覧:**

| メソッド | パス | 分割先 |
|---------|------|--------|
| GET | /ingredients | ingredients.py |
| GET | /ingredients/{id} | ingredients.py |
| GET | /ingredient-categories | ingredients.py |
| GET | /dishes | dishes.py |
| GET | /dishes/{id} | dishes.py |
| GET | /dish-categories | dishes.py |
| POST | /dishes/{id}/generate-recipe | dishes.py |
| POST | /dishes/generate-recipes/batch | dishes.py |
| GET | /nutrients/target | preferences.py |
| POST | /optimize | optimize.py |
| POST | /optimize/multi-day | optimize.py |
| POST | /optimize/multi-day/refine | optimize.py |
| GET | /preferences | preferences.py |
| PUT | /preferences | preferences.py |
| GET | /allergens | preferences.py |
| GET | /health | health.py |

### 5.2 router.py 実装例

```python
# presentation/api/v1/router.py
from fastapi import APIRouter

from app.presentation.api.v1.ingredients import router as ingredients_router
from app.presentation.api.v1.dishes import router as dishes_router
from app.presentation.api.v1.optimize import router as optimize_router
from app.presentation.api.v1.preferences import router as preferences_router
from app.presentation.api.v1.health import router as health_router

router = APIRouter()

router.include_router(ingredients_router, tags=["ingredients"])
router.include_router(dishes_router, tags=["dishes"])
router.include_router(optimize_router, tags=["optimize"])
router.include_router(preferences_router, tags=["preferences"])
router.include_router(health_router, tags=["health"])
```

### 5.3 dependencies.py 実装

```python
# presentation/dependencies.py
from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db_session
from app.infrastructure.repositories import (
    SQLAlchemyDishRepository,
    SQLAlchemyFoodRepository,
    SQLAlchemyIngredientRepository,
    InMemoryPreferenceRepository,
)
from app.domain.services import NutrientCalculator, UnitConverter

# リポジトリ
def get_dish_repository(db: Session = Depends(get_db_session)):
    return SQLAlchemyDishRepository(db)

def get_food_repository(db: Session = Depends(get_db_session)):
    return SQLAlchemyFoodRepository(db)

def get_ingredient_repository(db: Session = Depends(get_db_session)):
    return SQLAlchemyIngredientRepository(db)

@lru_cache()
def get_preference_repository():
    return InMemoryPreferenceRepository()

# ドメインサービス
@lru_cache()
def get_nutrient_calculator():
    return NutrientCalculator()

@lru_cache()
def get_unit_converter():
    return UnitConverter()

# ユースケース（Phase 4完了後）
# def get_optimize_multi_day_use_case(...):
#     return OptimizeMultiDayMenuUseCase(...)
```

### 5.4 main.py 更新

```python
# main.py (更新版)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    EntityNotFoundError,
    OptimizationFailedError,
)
from app.core.logging import setup_logging
from app.infrastructure.database import init_db, SessionLocal
from app.presentation.api.v1.router import router as api_v1_router
from app.data.loader import (
    load_excel_data, load_cooking_factors,
    load_ingredients_from_csv, load_dishes_from_csv,
    load_recipe_details
)

logger = setup_logging()

app = FastAPI(
    title="栄養最適化メニュー生成API",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 例外ハンドラ
@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(status_code=404, content=exc.to_dict())

@app.exception_handler(OptimizationFailedError)
async def optimization_failed_handler(request: Request, exc: OptimizationFailedError):
    return JSONResponse(status_code=500, content=exc.to_dict())

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=500, content=exc.to_dict())

# ルーター
app.include_router(api_v1_router, prefix="/api/v1")

# スタートアップ
@app.on_event("startup")
def startup_event():
    logger.info("Starting application...")
    init_db()
    # データロード処理（既存維持）
    ...
```

---

## Phase 6: テスト追加

### 6.1 テストディレクトリ構造

```
backend/tests/
├── __init__.py
├── conftest.py                    # pytest fixtures
├── unit/
│   ├── __init__.py
│   ├── domain/
│   │   ├── test_nutrient_calculator.py
│   │   ├── test_unit_converter.py
│   │   └── test_entities.py
│   ├── infrastructure/
│   │   └── test_repositories.py
│   └── application/
│       └── test_use_cases.py
└── integration/
    └── test_api_endpoints.py
```

### 6.2 conftest.py 例

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database import Base
from app.domain.entities import NutrientTarget, Dish, DishCategoryEnum, MealTypeEnum

@pytest.fixture
def test_db():
    """テスト用インメモリDB"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()

@pytest.fixture
def sample_nutrient_target():
    return NutrientTarget()

@pytest.fixture
def sample_dish():
    return Dish(
        id=1,
        name="白ごはん",
        category=DishCategoryEnum.STAPLE,
        meal_types=[MealTypeEnum.BREAKFAST, MealTypeEnum.LUNCH, MealTypeEnum.DINNER],
        ingredients=[],
        calories=252,
        protein=3.8,
        fat=0.5,
        carbohydrate=55.7,
        fiber=0.5,
        sodium=1,
        potassium=0,
        calcium=0,
        magnesium=0,
        iron=0,
        zinc=0,
        vitamin_a=0,
        vitamin_d=0,
        vitamin_e=0,
        vitamin_k=0,
        vitamin_b1=0,
        vitamin_b2=0,
        vitamin_b6=0,
        vitamin_b12=0,
        niacin=0,
        pantothenic_acid=0,
        biotin=0,
        folate=0,
        vitamin_c=0,
    )
```

### 6.3 テスト例

```python
# tests/unit/domain/test_nutrient_calculator.py
import pytest
from app.domain.services import NutrientCalculator
from app.domain.entities import NutrientTarget, DishPortion

class TestNutrientCalculator:
    def test_calculate_achievement_rate(self, sample_nutrient_target):
        calc = NutrientCalculator()
        nutrients = {
            "calories": 2000,
            "protein": 60,
            "sodium": 2000,
        }

        result = calc.calculate_achievement_rate(nutrients, sample_nutrient_target)

        assert "calories" in result
        assert "protein" in result
        assert result["calories"] == pytest.approx(100, rel=0.1)

    def test_generate_warnings_low_protein(self, sample_nutrient_target):
        calc = NutrientCalculator()
        nutrients = {"protein": 30}  # 目標の半分以下

        warnings = calc.generate_warnings(nutrients, sample_nutrient_target)

        protein_warnings = [w for w in warnings if w.nutrient == "protein"]
        assert len(protein_warnings) > 0
```

---

## 既存ファイル参照情報

### app/optimizer/solver.py 主要関数シグネチャ

```python
def db_dish_to_model(dish_db: DishDB) -> Dish:
    """DBモデルをPydanticモデルに変換"""

def optimize_meal(
    dishes: list[Dish],
    target: NutrientTarget,
    meal_name: str,
    excluded_dish_ids: set[int] = None,
    volume_multiplier: float = 1.0,
) -> MealPlan | None:
    """1食分のメニューを最適化"""

def optimize_daily_menu(
    db: Session,
    target: NutrientTarget = None,
    excluded_dish_ids: list[int] = None,
) -> DailyMenuPlan | None:
    """1日分のメニューを最適化"""

def solve_multi_day_plan(
    db: Session,
    days: int = 1,
    people: int = 1,
    target: NutrientTarget = None,
    excluded_allergens: list[str] = None,
    excluded_dish_ids: list[int] = None,
    keep_dish_ids: list[int] = None,
    preferred_ingredient_ids: list[int] = None,
    preferred_dish_ids: list[int] = None,
    batch_cooking_level: str = "normal",
    volume_level: str = "normal",
    variety_level: str = "normal",
    meal_settings: dict = None,
) -> MultiDayMenuPlan | None:
    """複数日×複数人の献立を最適化"""

def refine_multi_day_plan(
    db: Session,
    days: int = 1,
    people: int = 1,
    target: NutrientTarget = None,
    keep_dish_ids: list[int] = None,
    exclude_dish_ids: list[int] = None,
    excluded_allergens: list[str] = None,
    preferred_ingredient_ids: list[int] = None,
    preferred_dish_ids: list[int] = None,
    batch_cooking_level: str = "normal",
    volume_level: str = "normal",
    variety_level: str = "normal",
    meal_settings: dict = None,
) -> MultiDayMenuPlan | None:
    """既存献立を調整"""
```

### app/models/schemas.py で維持すべきAPIスキーマ

```python
# リクエストスキーマ（プレゼンテーション層用）
OptimizeRequest
MultiDayOptimizeRequest
RefineOptimizeRequest
MealSettings
MealSetting
CategoryConstraint
MealCategoryConstraints
MEAL_PRESETS
```

### app/data/loader.py 主要関数

```python
def load_excel_data(file_path: str, db: Session, clear_existing: bool = False): ...
def load_cooking_factors(db: Session): ...
def load_ingredients_from_csv(csv_path: str, db: Session, clear_existing: bool = False): ...
def load_dishes_from_csv(csv_path: str, db: Session, clear_existing: bool = False): ...
def get_recipe_details(dish_name: str) -> dict | None: ...
def load_recipe_details(json_path: str): ...
def calculate_dish_nutrients(db: Session, dish: DishDB): ...
def get_cooking_factor(db: Session, food_category: str, cooking_method: str, nutrient: str) -> float: ...
```

---

## 依存関係ルール

```
┌─────────────────────────────────────────────────────────────┐
│                    presentation (API)                        │
│                         ↓ 依存                               │
├─────────────────────────────────────────────────────────────┤
│                    application (Use Cases)                   │
│                         ↓ 依存                               │
├─────────────────────────────────────────────────────────────┤
│          domain (Entities, Interfaces, Services)             │
│                    ↑ 実装                                    │
├─────────────────────────────────────────────────────────────┤
│       infrastructure (Repositories, Optimizer, External)     │
└─────────────────────────────────────────────────────────────┘
```

**ルール:**
1. 外側の層は内側の層に依存できる
2. 内側の層は外側の層に依存してはいけない
3. domain層は他のどの層にも依存しない（最内層）
4. infrastructure層はdomain/interfacesを実装する
5. application層はdomain層のみに依存し、infrastructureには依存しない
6. presentation層はapplication層を通じてビジネスロジックを呼び出す

---

## 実行コマンド

```bash
# サーバー起動
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# テスト実行（Phase 6完了後）
pytest tests/

# インポートテスト
python -c "from app.domain.entities import Dish; print('OK')"
python -c "from app.infrastructure.repositories import SQLAlchemyDishRepository; print('OK')"
```

---

## 次のアクション

1. **Phase 4開始:** `infrastructure/optimizer/pulp_solver.py` の実装
2. solver.pyの関数を新しいクラスに移行
3. application/use_cases/ の実装
4. **Phase 5:** routes.pyの分割、dependencies.pyの実装
5. main.pyの更新
6. **Phase 6:** テストの追加

---

*最終更新: 2026-01-16*
