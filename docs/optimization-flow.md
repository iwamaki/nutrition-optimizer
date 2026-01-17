# 献立最適化フロー設計書

## 現状の課題

現在の最適化は「栄養バランス最適化」のみを行っており、以下の問題がある：
- 同じ料理が2日後にまた出てくる（多様性不足）
- 主菜のたんぱく源がランダム（肉→肉→肉になることも）
- 時系列を考慮した「気が利く」献立になっていない

## 改善方針

**段階的決定アプローチ**を採用する：
1. Phase 1: 主食を決める
2. Phase 2: 主菜を決める（たんぱく源ローテーション）
3. Phase 3: 副菜・汁物・デザートを最適化（残り栄養を補完）

## 現在の最適化フロー

### エントリーポイント

```
POST /api/v1/optimize/multi-day
    ↓
OptimizeMultiDayMenuUseCase.execute()
    ↓
PuLPSolver.solve_multi_day()
```

### PuLPSolver.solve_multi_day() の処理フロー

```
入力:
- dishes: 利用可能な料理リスト（約150件）
- days: 日数（1-7）
- people: 人数（1-6）
- target: 栄養素目標（NutrientTarget）
- excluded_dish_ids: 除外料理
- excluded_ingredient_ids: 除外食材（アレルゲン等）
- keep_dish_ids: 必須料理（お気に入り）
- variety_level: 多様性レベル（small/normal/large）
- meal_settings: 朝昼夜の設定（有効/無効、ボリューム）

Step 1: 前処理
├── 有効な栄養素を決定
├── meal_settings正規化
├── 除外料理をフィルタリング
└── 除外食材を含む料理をフィルタリング

Step 2: 決定変数の作成
├── x[d,t]: 料理dを日tに調理するか（Binary）
├── s[d,t]: 調理人前数（Integer, 1〜max_servings）
├── c[d,t,t',m]: 日tに調理した料理dを日t'の食事mで消費するか（Binary）
└── q[d,t,t',m]: 消費人前数（Integer, 1〜people）

Step 3: 目的関数
minimize:
  Σ(栄養素偏差ペナルティ)
  + 調理回数 × 作り置き重み
  - 手持ち食材ボーナス
  - お気に入り料理ボーナス

Step 4: 制約条件
├── C1: 調理-人前数リンク（調理しない→0人前）
├── C2: 消費量=調理量（作った分は全部消費）
├── C3: 消費フラグ-消費量リンク
├── C4: 日別栄養素制約（目標値との偏差）
├── C5: カテゴリ別品数制約
│   └── 朝: 主食1, 副菜0-1
│   └── 昼: 主食1, 主菜1, 副菜0-1
│   └── 夜: 主食1, 主菜1, 副菜1-2, 汁物0-1
├── C6: 多様性制約
│   └── large: 同じ料理は全期間で1回のみ
│   └── normal: 連続2日で同じ食事に同じ料理は出さない
│   └── small: 制約なし
└── C7: 必須料理制約（keep_dish_ids）

Step 5: 求解（HiGHS or CBC）
├── タイムアウト: 30秒
├── MIPギャップ: 5%
└── 失敗時→フォールバック（1日ずつ個別最適化）

Step 6: 結果抽出
├── CookingTask: いつ何を何人前作るか
├── DailyMealAssignment: 日別の食事割り当て
├── ShoppingList: 買い物リスト
└── 栄養素達成率・警告
```

## 新しい段階的決定フロー（提案）

### 概要

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: 主食スケジューリング                               │
│  ・ご飯/パン/麺のローテーション                              │
│  ・作り置き考慮（ご飯は3日分まとめて炊くなど）               │
├─────────────────────────────────────────────────────────────┤
│  Phase 2: 主菜スケジューリング                               │
│  ・たんぱく源ローテーション（肉→魚→卵→豆腐→肉...）          │
│  ・主食との相性考慮（パン→洋風主菜、ご飯→和風主菜）         │
│  ・作り置き考慮（storage_days活用）                          │
├─────────────────────────────────────────────────────────────┤
│  Phase 3: 副菜・汁物・デザート最適化                         │
│  ・主食+主菜で不足している栄養素を補完                       │
│  ・既存のPuLP最適化を活用                                    │
│  ・カテゴリ制約: 副菜1-2品, 汁物0-1品                        │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: 主食スケジューリング

**入力:**
- 主食カテゴリの料理リスト
- 日数
- 世帯タイプ（一人暮らし/複数人）

**ロジック:**
```python
# 一人暮らしの場合
staple_rotation = ["ご飯", "パン", "麺", "ご飯", "パン", ...]

# ご飯は2-3日分まとめて炊く（storage_days考慮）
# パン・麺は当日のみ
```

**出力:**
- 日別の主食料理ID

### Phase 2: 主菜スケジューリング

**入力:**
- 主菜カテゴリの料理リスト
- 日数
- Phase 1で決まった主食

**たんぱく源の分類:**
```python
PROTEIN_SOURCES = {
    "meat": ["肉類"],           # 豚肉、鶏肉、牛肉
    "fish": ["魚介類"],         # 鮭、さば、いわし
    "egg": ["卵類"],            # 卵焼き、オムレツ
    "dairy": ["乳類"],          # チーズ焼き
    "legume": ["豆類"],         # 豆腐、納豆
}
```

**ローテーションロジック:**
```python
# 理想: meat → fish → egg → legume → meat → fish ...
# 同じたんぱく源は最低2日空ける
# 作り置き可能な主菜は連続消費OK
```

**主食との相性:**
```python
COMPATIBILITY = {
    "ご飯": ["和風", "中華", "アジアン"],
    "パン": ["洋風"],
    "麺": ["中華", "和風", "洋風"],
}
```

**出力:**
- 日別の主菜料理ID

### Phase 3: 副菜・汁物の最適化

**入力:**
- 副菜・汁物カテゴリの料理リスト
- 日数
- Phase 1,2で決まった主食・主菜
- 残り栄養素目標（全体目標 - 主食+主菜の栄養）

**ロジック:**
既存のPuLPソルバーを流用
- 主食・主菜は`keep_dish_ids`として固定
- 副菜・汁物のみを最適化対象に
- 栄養素目標を残り分に調整

**出力:**
- 日別の副菜・汁物料理ID

## 実装計画

### Step 1: データ拡張（任意）
- DishIngredientに`food_category`を追加
- 料理の主たんぱく源を推定するヘルパー関数

### Step 2: MealPlannerクラスの実装
```python
class MealPlanner:
    """段階的献立決定"""

    def plan(self, dishes, days, household_type="single"):
        # Phase 1
        staples = self._schedule_staples(dishes, days)

        # Phase 2
        mains = self._schedule_mains(dishes, days, staples)

        # Phase 3: PuLPSolverに委譲
        result = self._optimize_sides(dishes, days, staples, mains)

        return result
```

### Step 3: 既存のsolve_multi_dayとの統合
- 新しいフラグ`scheduling_mode="staged"`を追加
- 段階的決定モードと従来モードを切り替え可能に

## 関連ファイル

- `backend/app/infrastructure/optimizer/pulp_solver.py` - 現在の最適化ロジック
- `backend/app/domain/entities/dish.py` - 料理エンティティ
- `backend/app/data/loader.py` - 食品カテゴリマッピング（CATEGORY_MAP）
- `backend/app/domain/services/constants.py` - 栄養素重み、カテゴリ制約

## 補足: 食品カテゴリ（loader.py）

```python
CATEGORY_MAP = {
    "01": "穀類",
    "02": "いも及びでん粉類",
    "04": "豆類",
    "06": "野菜類",
    "10": "魚介類",
    "11": "肉類",
    "12": "卵類",
    "13": "乳類",
    # ...
}
```

たんぱく源グループへのマッピング:
- 肉類 → meat
- 魚介類 → fish
- 卵類 → egg
- 乳類 → dairy
- 豆類 → legume
