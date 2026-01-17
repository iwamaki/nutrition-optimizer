# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

栄養バランスを考慮した献立自動生成システム。線形計画法（PuLP + HiGHS/CBCソルバー）を使用して、日本政府の食品成分表（八訂2023）に基づき最適な献立を提案する。

## 開発コマンド

### Backend (FastAPI + Python)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### Frontend (Flutter)
```bash
cd frontend
flutter pub get
flutter run -d chrome                   # Web
flutter run -d ios                      # iOS
dart run build_runner build             # Riverpod コード生成
```

### 料理マスタの追加・検証
```bash
cd backend
python tools/list_dishes.py -c 主食 --compact    # 既存確認
python tools/validate_dishes.py data/new.csv -o data/dishes.csv  # 検証
rm nutrition.db && uvicorn app.main:app --reload  # DB再構築
```

### レシピ詳細の自動生成（Gemini API）
```bash
cd backend
export GEMINI_API_KEY=$(gcloud secrets versions access latest \
  --secret=GEMINI_API_KEY --project=gen-lang-client-0309495198)
python tools/generate_recipes.py --dry-run    # 未登録確認
python tools/generate_recipes.py              # 全て生成
python tools/generate_recipes.py -c 主食      # カテゴリ指定
```

## アーキテクチャ（Clean Architecture）

### Backend
```
backend/app/
├── main.py                    # FastAPI エントリポイント
├── domain/                    # ビジネスロジック・エンティティ
│   ├── entities/              # Dish, Food, Ingredient, MealPlan, UserPreference
│   └── services/              # NutrientCalculator, UnitConverter
├── application/               # ユースケース層
│   └── use_cases/             # OptimizeMultiDayMenu, RefineMenuPlan, GenerateRecipe
├── infrastructure/            # 外部実装
│   ├── database/              # SQLAlchemy モデル・接続
│   ├── optimizer/pulp_solver.py  # PuLP 線形計画ソルバー
│   ├── repositories/          # SQLAlchemy Repository 実装
│   └── external/              # Gemini API クライアント
├── presentation/              # API層
│   └── api/v1/                # FastAPI ルーター（dishes, optimize, preferences）
└── models/schemas.py          # Pydantic リクエスト/レスポンススキーマ
```

### Frontend (Flutter + Riverpod)
```
frontend/lib/
├── main.dart                  # Material Design 3 アプリ
├── domain/                    # エンティティ・リポジトリインターフェース
├── data/                      # API Service・リポジトリ実装
└── presentation/
    ├── screens/               # Home, Calendar, Shopping, Settings
    ├── modals/                # GenerateModal（3ステップ）, DishDetailModal
    ├── providers/             # Riverpod 状態管理
    └── widgets/               # MealCard, NutrientProgressBar
```

## 主要API

### 最適化
- `POST /api/v1/optimize` - 1日分の献立最適化
- `POST /api/v1/optimize/multi-day` - 複数日×複数人の作り置き対応
- `POST /api/v1/optimize/multi-day/refine` - 献立調整（料理差し替え）

### マスタ
- `GET /api/v1/dishes` - 料理一覧
- `GET /api/v1/dishes/{id}` - 料理詳細
- `POST /api/v1/dishes/{id}/generate-recipe` - レシピ詳細生成（Gemini）
- `GET /api/v1/ingredients` - 食材一覧
- `GET /api/v1/foods` - 食品一覧（検索対応）

### 設定
- `GET/PUT /api/v1/preferences` - ユーザー設定

## 最適化ロジック (pulp_solver.py)

### 栄養素目標の考え方（厚生労働省「日本人の食事摂取基準」）

**5つの指標**（[参照](https://www.nutri.co.jp/nutrition/keywords/append/)）：
- **推定平均必要量（EAR）**: 集団の50%が必要量を満たす摂取量
- **推奨量（RDA）**: 集団の97〜98%が充足する摂取量（EAR × 算定係数）
- **目安量（AI）**: 科学的根拠が不十分な場合に設定される十分量
- **耐容上限量（UL）**: 健康障害リスクがないとみなされる上限
- **目標量（DG）**: 生活習慣病予防を目的とした摂取量

**最適化における目標**:
- 推奨量・目安量 → **100%以上**を目指す（不足は避ける）
- 耐容上限量 → **超えてはいけない**（過剰摂取リスク）
- 目標量（範囲指定）→ 範囲内に収める

### 目的関数

各栄養素の目標値からの乖離を最小化（不足にはより大きなペナルティ）
```
Σ(weight × penalty × |実績 - 目標| / 目標)
```
- 不足（< 100%）: UNDER_PENALTY（大きい）
- 過剰（> 上限）: OVER_PENALTY

**制約条件**:
- カロリー範囲（1800-2200 kcal）
- 料理カテゴリ構成: 主食(1) + 主菜(1) + 副菜(1-2) + 汁物(0-1)
- アレルゲン除外（28品目対応: 8特定原材料 + 20推奨表示）

**ソルバー設定**:
- HiGHS 優先、CBC フォールバック
- タイムアウト: 30秒、MIPギャップ: 5%
- カテゴリ別上位30件をプレフィルタリング

## データ

- `backend/data/food_composition_2023.xlsx` - 文科省食品成分表（約2,500食品）
- `backend/data/dishes.csv` - 料理マスタ（約150件）
- `backend/data/recipe_details.json` - レシピ詳細（手順・コツ）
- `backend/data/app_ingredients.csv` - 正規化食材リスト

## ドキュメント

- `/docs/PLAN.md` - システム設計書
- `/docs/ui-design-mobile.svg` - スマホUI設計書
- `/docs/add-dish-workflow.md` - 料理追加ワークフロー
