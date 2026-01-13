# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

栄養バランスを考慮した献立自動生成システム。線形計画法（PuLP/CBCソルバー）を使用して、日本政府の食品成分表（八訂2023）に基づき最適な献立を提案する。

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

## アーキテクチャ

```
backend/
├── app/
│   ├── main.py              # FastAPI エントリポイント
│   ├── api/routes.py        # 全APIエンドポイント (/api/v1)
│   ├── db/database.py       # SQLAlchemy + SQLite
│   ├── optimizer/solver.py  # PuLP 線形計画ソルバー（核心ロジック）
│   ├── models/schemas.py    # Pydantic スキーマ
│   ├── data/loader.py       # Excel/CSV/JSONデータローダー
│   └── services/
│       └── recipe_generator.py  # Gemini APIレシピ詳細生成
├── data/
│   ├── food_composition_2023.xlsx  # 文科省食品成分表（約2,500食品）
│   ├── dishes.csv                  # 料理マスタ（117件）
│   └── recipe_details.json         # レシピ詳細（手順・コツ）
└── tools/                   # CLI ユーティリティ

frontend/lib/
├── main.dart                # Material Design 3 アプリ
├── screens/home_screen.dart # メイン画面（献立表示）
├── services/api_service.dart # HTTP クライアント
├── models/food.dart         # データモデル
└── widgets/                 # MealCard, NutrientChart
```

## 主要API

- `POST /api/v1/optimize` - 1日分の献立最適化
- `POST /api/v1/optimize/multi-day` - 複数日×複数人の作り置き対応
- `POST /api/v1/optimize/multi-day/refine` - 献立調整（イテレーション）
- `GET /api/v1/dishes`, `/foods` - マスタ参照
- `POST /api/v1/dishes/{id}/generate-recipe` - レシピ詳細生成（Gemini）

## 最適化ロジック (solver.py)

**目的関数**: 各栄養素の目標値からの乖離を最小化
```
Σ(weight × |実績 - 目標| / 目標)
```

**制約条件**:
- カロリー範囲（1800-2200 kcal）
- 料理カテゴリ構成: 主食(1) + 主菜(1) + 副菜(1-2) + 汁物(0-1)
- 食材の最大使用量
- 作り置き日数 (storage_days)
- アレルゲン除外

**栄養素重み** (優先度):
- 高: protein(1.5), fiber(1.2), iron(1.3), vitamin_d(1.5)
- 標準: calories, fat, carbs(1.0)
- 低: sodium(0.8)

## データ

- 食品成分表: `backend/data/food_composition_2023.xlsx` から起動時に自動ロード
- 料理CSV形式: `name,category,meal_types,ingredients,instructions,storage_days`
- ingredients: `食品名:グラム数:調理法` 形式
- レシピ詳細: `backend/data/recipe_details.json`（料理名をキーにした詳細手順）

## ドキュメント

- `/docs/PLAN.md` - システム設計書
- `/docs/add-dish-workflow.md` - 料理追加ワークフロー
