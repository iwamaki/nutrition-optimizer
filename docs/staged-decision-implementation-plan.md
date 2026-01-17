# 段階的決定フロー 実装計画書

## 現状のデータ構造（調査結果）

### すでに使えるもの

| データ | フィールド | 用途 |
|--------|-----------|------|
| IngredientDB | `category` | たんぱく源分類（肉類/魚介類/卵類/乳類/豆類） |
| DishIngredientDB | `cooking_method` | 調理方法（焼く/茹でる/蒸す/etc） |
| DishDB | `category` | 料理カテゴリ（主食/主菜/副菜/汁物） |
| DishDB | `storage_days` | 作り置き可能日数 |

### 新規追加が必要なもの

| データ | フィールド | 用途 |
|--------|-----------|------|
| DishDB（または新テーブル） | `flavor_profile` | 味付け系統（和風/洋風/中華） |

## たんぱく源の推定ロジック

既存データから推定可能。新規フィールド追加は不要。

```python
PROTEIN_SOURCE_CATEGORIES = {
    "meat": "肉類",
    "fish": "魚介類",
    "egg": "卵類",
    "dairy": "乳類",
    "legume": "豆類",
}

def get_primary_protein_source(dish: Dish) -> Optional[str]:
    """料理の主たんぱく源を推定"""
    protein_amounts = defaultdict(float)

    for ing in dish.ingredients:
        # ingredient経由でcategoryを取得
        if ing.ingredient and ing.ingredient.category in PROTEIN_SOURCE_CATEGORIES.values():
            protein_amounts[ing.ingredient.category] += ing.amount

    if not protein_amounts:
        return None

    # 最も量が多いカテゴリを返す
    return max(protein_amounts, key=protein_amounts.get)
```

## 調理方法の活用

DishIngredientDB.cooking_methodから集計可能。

```python
COOKING_METHODS = {
    "raw": ["生"],
    "boil": ["茹でる", "蒸す"],
    "grill": ["焼く"],
    "fry": ["炒める", "揚げる"],
    "simmer": ["煮る"],
    "microwave": ["電子レンジ"],
}

def get_main_cooking_method(dish: Dish) -> str:
    """料理の主要調理方法を取得"""
    method_counts = defaultdict(int)
    for ing in dish.ingredients:
        if ing.cooking_method:
            method_counts[ing.cooking_method.value] += 1

    if not method_counts:
        return "生"
    return max(method_counts, key=method_counts.get)
```

## 味付け系統（新規追加）

### 選択肢A: dishes.csv に `flavor_profile` カラム追加

```csv
name,category,meal_types,storage_days,flavor_profile,ingredients,instructions
鶏の照り焼き,主菜,"lunch,dinner",2,和風,52:100:焼く,...
```

### 選択肢B: 料理名から推定（ルールベース）

```python
FLAVOR_KEYWORDS = {
    "和風": ["照り焼き", "味噌", "煮物", "和え物", "おひたし", "丼"],
    "洋風": ["グラタン", "パスタ", "ソテー", "シチュー", "サラダ"],
    "中華": ["チャーハン", "麻婆", "餃子", "炒め", "あんかけ"],
}
```

**推奨**: 選択肢A（明示的なデータが信頼性高い）

---

## 実装フェーズ

### Phase 0: データ拡張（準備）

**タスク:**
1. dishes.csv に `flavor_profile` カラムを追加
2. 既存150件の料理に味付け系統を設定
3. DBマイグレーション（DishDBに`flavor_profile`追加）

**工数**: 軽（CSVの編集 + マイグレーション）

### Phase 1: MealSchedulerクラスの実装

**新規ファイル**: `backend/app/domain/services/meal_scheduler.py`

```python
class MealScheduler:
    """主食・主菜のスケジューリング（ルールベース）"""

    def schedule_staples(
        self,
        staple_dishes: list[Dish],
        days: int,
        meals_per_day: list[str],  # ["breakfast", "lunch", "dinner"]
    ) -> dict[int, dict[str, Dish]]:
        """
        Phase 1: 主食のスケジューリング

        ルール:
        - ご飯系は2-3日ブロックで配置（作り置き活用）
        - パンは朝食優先
        - 麺は連続しない

        Returns:
            {day: {meal: dish}} の形式
        """
        pass

    def schedule_mains(
        self,
        main_dishes: list[Dish],
        days: int,
        meals_per_day: list[str],
        scheduled_staples: dict[int, dict[str, Dish]],
    ) -> dict[int, dict[str, Dish]]:
        """
        Phase 2: 主菜のスケジューリング

        ルール:
        - たんぱく源ローテーション（肉→魚→卵→豆腐...）
        - 同じたんぱく源は最低2日空ける
        - 主食との相性考慮（パン→洋風、ご飯→和風/中華）
        - 作り置き可能な料理は連続消費OK

        Returns:
            {day: {meal: dish}} の形式
        """
        pass
```

### Phase 2: PuLPSolverとの統合

**変更ファイル**: `backend/app/infrastructure/optimizer/pulp_solver.py`

```python
class PuLPSolver:
    def solve_multi_day_staged(
        self,
        dishes: list[Dish],
        days: int,
        people: int,
        target: NutrientTarget,
        # ... 既存パラメータ ...
        scheduling_mode: str = "staged",  # "staged" or "full"
    ) -> Optional[MultiDayMenuPlan]:
        """
        段階的決定モード

        1. MealScheduler で主食・主菜を決定
        2. 残りの副菜・汁物を既存の最適化で埋める
        3. 栄養達成率チェック
        4. 達成率<70% なら主菜を別候補で1回リトライ
        """
        if scheduling_mode == "full":
            return self.solve_multi_day(...)  # 従来モード

        scheduler = MealScheduler()

        # Phase 1: 主食
        staples = scheduler.schedule_staples(...)

        # Phase 2: 主菜
        mains = scheduler.schedule_mains(..., staples)

        # Phase 3: 副菜・汁物を最適化
        result = self._optimize_sides_and_soups(
            dishes, days, people, target,
            fixed_staples=staples,
            fixed_mains=mains,
        )

        # 評価 & リトライ
        if result.overall_achievement["calories"] < 70:
            # 主菜を別候補で再試行
            alt_mains = scheduler.schedule_mains(..., exclude=mains)
            result = self._optimize_sides_and_soups(...)

        return result
```

### Phase 3: ユースケースの更新

**変更ファイル**: `backend/app/application/use_cases/optimize_multi_day_menu.py`

```python
class OptimizeMultiDayMenuUseCase:
    def execute(
        self,
        request: OptimizeMultiDayRequest,
        scheduling_mode: str = "staged",  # 新パラメータ
    ) -> MultiDayMenuPlan:
        # ...
        return self._solver.solve_multi_day_staged(
            ...,
            scheduling_mode=scheduling_mode,
        )
```

---

## 段階的決定フローの詳細設計

### Phase 1: 主食スケジューリング

**入力:**
- 主食カテゴリの料理リスト
- 日数
- 食事タイプ（朝/昼/夜）

**ロジック:**

```python
def schedule_staples(self, staple_dishes, days, meals):
    # 主食を種類別に分類
    rice_dishes = [d for d in staple_dishes if "ご飯" in d.name or "ライス" in d.name]
    bread_dishes = [d for d in staple_dishes if "パン" in d.name or "トースト" in d.name]
    noodle_dishes = [d for d in staple_dishes if "麺" in d.name or "パスタ" in d.name or "うどん" in d.name]

    schedule = {}
    for day in range(1, days + 1):
        schedule[day] = {}
        for meal in meals:
            if meal == "breakfast":
                # 朝はパン優先、なければご飯
                schedule[day][meal] = random.choice(bread_dishes or rice_dishes)
            else:
                # 昼夜は3日周期でローテーション
                cycle = (day - 1) % 3
                if cycle == 0:
                    schedule[day][meal] = random.choice(rice_dishes)
                elif cycle == 1:
                    schedule[day][meal] = random.choice(noodle_dishes or rice_dishes)
                else:
                    schedule[day][meal] = random.choice(rice_dishes)

    return schedule
```

### Phase 2: 主菜スケジューリング

**入力:**
- 主菜カテゴリの料理リスト
- 日数
- Phase 1で決まった主食

**ロジック:**

```python
PROTEIN_ROTATION = ["meat", "fish", "egg", "legume"]  # 基本ローテーション

FLAVOR_COMPATIBILITY = {
    # 主食 → 相性の良い味付け系統
    "ご飯": ["和風", "中華"],
    "パン": ["洋風"],
    "麺": ["和風", "中華", "洋風"],
}

def schedule_mains(self, main_dishes, days, meals, staples):
    # 主菜をたんぱく源別に分類
    dishes_by_protein = defaultdict(list)
    for dish in main_dishes:
        protein = get_primary_protein_source(dish)
        if protein:
            dishes_by_protein[protein].append(dish)

    schedule = {}
    protein_index = 0
    last_protein = None

    for day in range(1, days + 1):
        schedule[day] = {}
        for meal in meals:
            if meal == "breakfast":
                continue  # 朝食は主菜なし（設定による）

            # たんぱく源をローテーション
            protein = PROTEIN_ROTATION[protein_index % len(PROTEIN_ROTATION)]

            # 同じたんぱく源が連続しないよう調整
            if protein == last_protein:
                protein_index += 1
                protein = PROTEIN_ROTATION[protein_index % len(PROTEIN_ROTATION)]

            # 主食との相性でフィルタリング
            staple_name = staples[day][meal].name
            compatible_flavors = FLAVOR_COMPATIBILITY.get(staple_name, ["和風", "洋風", "中華"])

            candidates = [
                d for d in dishes_by_protein.get(protein, [])
                if getattr(d, 'flavor_profile', '和風') in compatible_flavors
            ]

            if candidates:
                schedule[day][meal] = random.choice(candidates)
            else:
                # フォールバック: 相性無視で選択
                schedule[day][meal] = random.choice(dishes_by_protein.get(protein, main_dishes))

            last_protein = protein
            protein_index += 1

    return schedule
```

### Phase 3: 副菜・汁物の最適化

**入力:**
- 副菜・汁物カテゴリの料理リスト
- Phase 1,2で決まった主食・主菜
- 残り栄養素目標

**ロジック:**

```python
def _optimize_sides_and_soups(
    self, dishes, days, people, target,
    fixed_staples, fixed_mains
):
    # 主食・主菜の栄養素を計算
    fixed_nutrients = self._calculate_fixed_nutrients(fixed_staples, fixed_mains)

    # 残り目標を計算
    remaining_target = self._calculate_remaining_target(target, fixed_nutrients)

    # 副菜・汁物のみをフィルタ
    side_dishes = [d for d in dishes if d.category.value in ["副菜", "汁物", "デザート"]]

    # 既存のPuLP最適化を実行（カテゴリ制約を調整）
    return self._solve_with_fixed_dishes(
        side_dishes,
        remaining_target,
        fixed_staples,
        fixed_mains,
    )
```

---

## フォールバック戦略

```
Phase 1 → Phase 2 → Phase 3 → 評価
                                ↓
                        栄養達成率 < 70%?
                                ↓ Yes
                        Phase 2 の主菜を別候補で1回リトライ
                                ↓
                        それでもダメ → 警告付きで結果を返す
```

**警告例:**
- "たんぱく質が目標の65%です。主菜を追加することをおすすめします。"
- "ビタミンCが不足しています。フルーツを追加してください。"

---

## 実装順序

| 順序 | タスク | ファイル | 工数 |
|------|--------|----------|------|
| 1 | dishes.csvに`flavor_profile`追加 | data/dishes.csv | 小 |
| 2 | DishDBに`flavor_profile`カラム追加 | models.py, loader.py | 小 |
| 3 | たんぱく源推定ヘルパー実装 | domain/services/meal_scheduler.py | 小 |
| 4 | MealScheduler.schedule_staples実装 | domain/services/meal_scheduler.py | 中 |
| 5 | MealScheduler.schedule_mains実装 | domain/services/meal_scheduler.py | 中 |
| 6 | PuLPSolver.solve_multi_day_staged実装 | infrastructure/optimizer/pulp_solver.py | 中 |
| 7 | フォールバック機構実装 | infrastructure/optimizer/pulp_solver.py | 小 |
| 8 | ユースケース更新 | application/use_cases/optimize_multi_day_menu.py | 小 |
| 9 | テスト | tests/ | 中 |

---

## 成功指標

1. **多様性**: 同じ料理が3日以内に再登場しない
2. **たんぱく源**: 連続2日で同じたんぱく源にならない
3. **相性**: 主食と主菜の味付け系統が矛盾しない
4. **栄養達成率**: 平均70%以上を維持
5. **計算時間**: 7日分の献立生成が10秒以内
