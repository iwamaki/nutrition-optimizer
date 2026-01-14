# 栄養最適化メニュー生成システム - 開発計画

## コンセプト

1日に必要な栄養素を満たす最適な献立を自動生成するシステム。

### 解決する課題

- 栄養バランスを考慮した献立作成は、複数の栄養素を同時に満たす必要があり、人間が直感で解くのは困難
- 手計算による栄養管理は非現実的で継続しにくい

### アプローチ

- **数理最適化（線形計画法）** により、食材の組み合わせと量を自動調整
- **文部科学省 食品標準成分表（八訂）** を栄養素データの基盤とする
- **調理係数** により、加熱等による栄養素変化を反映（予定）

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    Flutter (Frontend)                    │
│                  Web / iOS / Android                     │
├─────────────────────────────────────────────────────────┤
│                         REST API                         │
├─────────────────────────────────────────────────────────┤
│                  FastAPI (Backend)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Routes    │  │   Solver    │  │   Data Loader   │  │
│  │  (API層)    │  │ (PuLP/CBC)  │  │ (Excel Parser)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────┤
│              SQLite + SQLAlchemy (永続化)                │
└─────────────────────────────────────────────────────────┘
```

---

## 最適化モデル

### 目的関数

栄養素目標との重み付き相対誤差を最小化:

```
minimize Σ (weight_i × |actual_i - target_i| / target_i)
```

### 決定変数

- `x[food_id]`: 各食材の使用量 (g)
- `y[food_id]`: 各食材の使用有無 (0/1)

### 制約条件

- カロリー範囲（目標 ± 許容範囲）
- 食材ごとの最大使用量
- 1食あたりの品数（2〜5品）
- カテゴリ除外（アレルギー等）

---

## 開発フェーズ

### Phase 0: MVP（完了）

- [x] FastAPI による REST API
- [x] PuLP + CBC Solver による最適化エンジン
- [x] SQLite + SQLAlchemy によるデータ永続化
- [x] 41品目のサンプル食材データ
- [x] Flutter による基本UI（メニュー表示、栄養グラフ）

### Phase 1: データ拡充（完了）

- [x] 文科省食品成分表（Excel）パーサー実装
- [x] 2,000品目以上の食品データ投入
- [x] 料理マスタ（117件）整備
- [x] Gemini APIによるレシピ詳細自動生成

### Phase 2: バックエンドAPI拡張（完了）

- [x] 複数日最適化API (`/optimize/multi-day`)
- [x] 献立調整API (`/optimize/multi-day/refine`)
- [x] アレルゲン除外機能（7大アレルゲン）
- [x] 買い物リスト自動生成
- [x] 作り置き対応（storage_days）

### Phase 3: Flutter UI刷新（進行中）

UI設計書: `docs/ui-design-mobile.svg` (v6)

---

## Flutter実装計画

### 画面構成（8画面）

| # | 画面名 | ファイル | 説明 |
|---|--------|----------|------|
| ① | ホーム | `home_screen.dart` | 今日の献立・栄養達成率・生成ボタン |
| ② | 献立カレンダー | `calendar_screen.dart` | 週/月表示・ドラッグで入れ替え |
| ③ | 買い物リスト | `shopping_screen.dart` | 不足食材のみ表示・チェック機能 |
| ④ | 設定 | `settings_screen.dart` | 人数・目標・アレルゲン |
| ⑤ | Step1 | `generate_modal.dart` | 期間・人数・ボリューム・アレルゲン |
| ⑥ | Step2 | `generate_modal.dart` | 手持ち食材選択 |
| ⑦ | Step3 | `generate_modal.dart` | 献立確認・除外・栄養達成率 |
| ⑧ | 料理詳細 | `dish_detail_modal.dart` | 栄養素・作り方・除外ボタン |

### ディレクトリ構成（予定）

```
frontend/lib/
├── main.dart
├── app.dart                      # MaterialApp設定
├── models/
│   ├── food.dart                 # 既存
│   ├── dish.dart                 # 料理モデル
│   ├── menu_plan.dart            # 献立モデル
│   └── shopping_item.dart        # 買い物モデル
├── services/
│   ├── api_service.dart          # 既存（拡張）
│   └── storage_service.dart      # ローカル保存
├── providers/
│   ├── menu_provider.dart        # 献立状態管理
│   ├── settings_provider.dart    # 設定状態管理
│   └── shopping_provider.dart    # 買い物状態管理
├── screens/
│   ├── main_scaffold.dart        # 共通レイアウト+タブナビ
│   ├── home_screen.dart          # ①ホーム
│   ├── calendar_screen.dart      # ②献立カレンダー
│   ├── shopping_screen.dart      # ③買い物リスト
│   └── settings_screen.dart      # ④設定
├── widgets/
│   ├── meal_card.dart            # 既存
│   ├── nutrient_chart.dart       # 既存
│   ├── nutrient_progress_bar.dart # 栄養達成率バー
│   ├── period_toggle.dart        # 今日/週間/月間切替
│   ├── draggable_meal_card.dart  # ドラッグ可能カード
│   └── allergen_chip.dart        # アレルゲン選択チップ
└── modals/
    ├── generate_modal.dart       # ⑤⑥⑦献立生成モーダル
    └── dish_detail_modal.dart    # ⑧料理詳細モーダル
```

### API対応表

| Flutter機能 | バックエンドAPI | 備考 |
|-------------|----------------|------|
| 献立生成 | `POST /optimize/multi-day` | days, people, allergens |
| 献立再生成 | `POST /optimize/multi-day/refine` | keep/exclude dish IDs |
| 食材検索 | `GET /foods/search` | キーワード・カテゴリ検索 |
| 料理一覧 | `GET /dishes` | カテゴリ・食事タイプ絞込 |
| 料理詳細 | `GET /dishes/{id}` | 栄養素・レシピ |
| レシピ生成 | `POST /dishes/{id}/generate-recipe` | Gemini API |
| アレルゲン一覧 | `GET /allergens` | 7大アレルゲン |
| 設定取得/更新 | `GET/PUT /preferences` | デフォルト値 |

### 実装ステップ

#### Step 1: 基盤整備
- [ ] Providerパッケージ導入（状態管理）
- [ ] モデルクラス追加（Dish, MultiDayMenuPlan, ShoppingItem）
- [ ] ApiService拡張（multi-day, refine, foods/search）
- [ ] MainScaffold（タブナビゲーション）

#### Step 2: ホーム画面リニューアル
- [ ] 栄養達成率バー（今日/週間/月間切替）
- [ ] 朝昼夕カード表示
- [ ] 「献立を生成」ボタン

#### Step 3: 献立生成モーダル（3ステップ）
- [ ] Step1: 期間・人数・ボリューム・アレルゲン選択
- [ ] Step2: 手持ち食材選択（検索・カテゴリ・よく使う）
- [ ] Step3: 献立確認・除外・栄養達成率・再生成/確定

#### Step 4: 献立カレンダー
- [ ] 週表示/月表示切替
- [ ] 日別・食事別リスト表示
- [ ] ドラッグ&ドロップで入れ替え（ReorderableListView）

#### Step 5: 買い物リスト
- [ ] カテゴリ別表示（野菜/肉/魚/卵乳）
- [ ] チェック機能
- [ ] 期間・人数表示
- [ ] 共有機能（share_plus）

#### Step 6: 設定画面
- [ ] デフォルト人数・日数
- [ ] 栄養目標（カロリー範囲など）
- [ ] アレルゲン除外設定

#### Step 7: 料理詳細モーダル
- [ ] 栄養素表示（P/F/C）
- [ ] 作り方表示
- [ ] 除外ボタン

### 必要なパッケージ

```yaml
dependencies:
  provider: ^6.0.0        # 状態管理
  shared_preferences: ^2.0.0  # ローカル保存
  share_plus: ^7.0.0      # 共有機能
  fl_chart: ^0.66.0       # グラフ（既存）
  google_fonts: ^6.0.0    # フォント（既存）
  http: ^1.0.0            # API通信（既存）
```

---

## データソース

### 食品成分表

- **出典**: 日本食品標準成分表（八訂）増補2023年
- **URL**: https://www.mext.go.jp/a_menu/syokuhinseibun/mext_00001.html
- **収録栄養素**: エネルギー、たんぱく質、脂質、炭水化物、食物繊維、ナトリウム、カルシウム、鉄、ビタミンA/C/D 等

### 調理係数（予定）

加熱調理による栄養素の変化を係数で補正:

| 調理法 | 対象栄養素 | 係数例 |
|--------|-----------|--------|
| 茹でる | ビタミンC | 0.5〜0.7 |
| 炒める | ビタミンB1 | 0.8〜0.9 |
| 揚げる | 脂質 | +吸油率 |

※ 食材×調理法の組み合わせが多いため、主要なものから段階的に実装

---

## API エンドポイント

### 最適化API

| Method | Path | 説明 |
|--------|------|------|
| POST | `/api/v1/optimize` | 1日分メニュー最適化 |
| POST | `/api/v1/optimize/multi-day` | 複数日最適化（作り置き対応） |
| POST | `/api/v1/optimize/multi-day/refine` | 献立調整（イテレーション） |

### マスタAPI

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/foods` | 食品一覧 |
| GET | `/api/v1/foods/search` | 食品検索 |
| GET | `/api/v1/dishes` | 料理一覧 |
| GET | `/api/v1/dishes/{id}` | 料理詳細 |
| POST | `/api/v1/dishes/{id}/generate-recipe` | レシピ生成 |
| GET | `/api/v1/allergens` | アレルゲン一覧 |

### 設定API

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/preferences` | ユーザー設定取得 |
| PUT | `/api/v1/preferences` | ユーザー設定更新 |

---

## 技術スタック

### Backend
- Python 3.12
- FastAPI
- PuLP (CBC Solver)
- SQLAlchemy + SQLite
- pandas (Excel読み込み)
- Google Generative AI (Gemini)

### Frontend
- Flutter 3.x
- Material Design 3
- Provider (状態管理)
- fl_chart (グラフ描画)
- http (API通信)

---

## 起動方法

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (Web)

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

---

*最終更新: 2026-01-14*
