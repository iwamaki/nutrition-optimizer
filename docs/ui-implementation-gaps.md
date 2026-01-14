# UI実装ギャップ分析レポート

作成日: 2024-01-14
対象: `docs/ui-design-mobile.svg` (v6) と Flutter実装の比較

## 概要

UI設計書（SVG）と現在のFlutter実装を比較し、相違点と未実装機能を特定した。
本ドキュメントは継続作業のためのチェックリストを含む。

---

## 実装状況チェックリスト

### 1. ホーム画面 (`frontend/lib/screens/home_screen.dart`)

- [x] 栄養達成率カード
- [x] 朝食/昼食/夕食のMealCard
- [x] 「献立を生成」ボタン
- [x] 期間トグル（今日/週間）
- [ ] **期間トグルに「月間」を追加** - 設計では3択（今日/週間/月間）
- [ ] 食事アイコンを絵文字に変更（任意）- 設計では🌅☀️🌙

### 2. 週間/カレンダー画面 (`frontend/lib/screens/calendar_screen.dart`)

- [x] 日付セレクター（横スクロール）
- [x] 日別の献立表示
- [x] 栄養達成率サマリー
- [x] **週表示/月表示トグルの追加** - SegmentedButtonで実装済み ✅
- [x] **ドラッグ&ドロップで献立入れ替え** ✅
  - 長押しでドラッグ開始
  - ドラッグハンドル（≡）の表示
  - ドロップ先のハイライト表示
- [x] **日付表示を実際の日付に変更** - 「1月15日（月）」形式で実装済み ✅

### 3. 買い物リスト画面 (`frontend/lib/screens/shopping_screen.dart`)

- [x] カテゴリ別グループ化
- [x] チェックボックス付きリスト
- [x] 共有機能
- [x] 進捗表示
- [ ] **期間表示を日付形式に変更** - 「1/15(月)〜1/17(水) 2人分」
- [ ] **「手持ち食材を除いた不足分のみ」注記の追加**
- [ ] **サマリーの詳細化** - 「不足分: X品目 / 購入済み: X品 / 残り: X品」

### 4. 設定画面 (`frontend/lib/screens/settings_screen.dart`)

- [x] デフォルト日数設定
- [x] デフォルト人数設定
- [x] 作り置き優先設定
- [x] カロリー目標設定
- [x] アレルゲン除外設定
- [ ] **タンパク質目標の追加** - 設計では「60-100g」
- [ ] **その他栄養素目標の追加** - 設計では「その他栄養素...」→詳細画面

### 5. 献立生成モーダル (`frontend/lib/modals/generate_modal.dart`)

#### Step1: 基本設定
- [x] 期間選択（1〜7日）
- [x] 人数選択
- [x] アレルゲン除外
- [x] 作り置き優先スイッチ
- [x] **献立ボリューム選択の追加** - 「少なめ/普通/多め」 ✅
- [x] **食材の種類選択の追加** - 「少なめ/普通/多め」 ✅

#### Step2: 手持ち食材
- [x] **食材検索機能** ✅
- [x] **よく使う食材の表示**（絵文字付きチップ）✅
- [x] **カテゴリから探す機能**（肉類/魚介/野菜/卵乳）✅
- [x] **選択中の食材表示** ✅

#### Step3: 献立確認
- [x] 栄養達成率サマリー
- [x] 日別献立の折りたたみ表示
- [x] 警告表示
- [x] **料理の個別除外機能** - タップで除外/解除 ✅
- [x] **「再生成」ボタンの常時表示** ✅

### 6. 料理詳細モーダル (`frontend/lib/modals/dish_detail_modal.dart`)

- [x] 料理名・カテゴリ・カロリー表示
- [x] 栄養素表示（P/F/C + 微量栄養素）
- [x] 材料リスト
- [x] 作り方表示
- [x] AI生成機能
- [x] 「除外」ボタン
- [x] 「固定」ボタン（設計にはないが実装済み - 追加機能として維持）

---

## 優先度別タスク

### Priority 1: 主要機能（設計のコア機能）✅ 完了

1. **[P1-1] カレンダー画面: ドラッグ&ドロップ実装** ✅ 完了
   - ファイル: `calendar_screen.dart`
   - 実装内容:
     - LongPressDraggable + DragTarget で実装
     - 異なる日間での料理入れ替え（swapDishes）
     - ドラッグハンドル・ドロップ先ハイライト

2. **[P1-2] 生成モーダル Step2: 手持ち食材選択** ✅ 完了
   - ファイル: `generate_modal.dart`
   - 実装内容:
     - 食品検索（APIと連携）
     - よく使う食材（絵文字付きチップ）
     - カテゴリ別ブラウズ（肉類/魚介/野菜/卵類）
     - 選択状態の表示

3. **[P1-3] 生成モーダル Step3: 料理の個別除外** ✅ 完了
   - ファイル: `generate_modal.dart`
   - 実装内容:
     - タップで除外/解除（取り消し線・背景色）
     - 「再生成」ボタン常時表示
     - refinePlanで再最適化

### Priority 2: UI改善（設計との整合性）

4. **[P2-1] カレンダー画面: 週/月表示トグル** ✅ 完了
   - ファイル: `calendar_screen.dart`
   - 実装内容: SegmentedButtonで週/月切り替え、月表示はグリッド形式

5. **[P2-2] カレンダー画面: 日付表示形式** ✅ 完了
   - ファイル: `calendar_screen.dart`
   - 実装内容: 「1月15日（月）」形式、今日を開始日として計算

6. **[P2-3] ホーム画面: 月間トグル追加**
   - ファイル: `home_screen.dart`
   - 要件:
     - 期間トグルに「月間」を追加
     - 月間の栄養達成率計算ロジック

7. **[P2-4] 買い物リスト: 表示改善**
   - ファイル: `shopping_screen.dart`
   - 要件:
     - 日付範囲表示
     - 「手持ち食材を除いた不足分のみ」注記
     - サマリーの詳細化

### Priority 3: 追加設定

8. **[P3-1] 生成モーダル Step1: ボリューム/食材種類** ✅ 完了
   - ファイル: `generate_modal.dart`
   - 実装内容:
     - 「献立ボリューム」選択（少なめ/普通/多め）→ カロリー目標を調整
     - 「食材の種類」選択（少なめ/普通/多め）→ 料理の多様性を調整
     - バックエンド（schemas.py, solver.py, routes.py）に対応パラメータ追加

9. **[P3-2] 設定画面: 栄養目標の拡充**
   - ファイル: `settings_screen.dart`
   - 要件:
     - タンパク質目標
     - その他栄養素の詳細設定画面

---

## 技術メモ

### ドラッグ&ドロップ実装のヒント

```dart
// ReorderableListView を使う場合
ReorderableListView(
  onReorder: (oldIndex, newIndex) {
    // 並べ替えロジック
  },
  children: [...],
)

// 異なる日間の入れ替えには Draggable + DragTarget の組み合わせ
Draggable<DishPortion>(
  data: dish,
  child: MealCard(...),
  feedback: Material(child: MealCard(...)),
)

DragTarget<DishPortion>(
  onAccept: (dish) {
    // 入れ替え処理
  },
  builder: (context, candidateData, rejectedData) {
    // ドロップ先の表示
  },
)
```

### 手持ち食材選択の状態管理

```dart
// MenuProvider または新規 IngredientProvider に追加
Set<int> _ownedFoodIds = {};

void toggleOwnedFood(int foodId) {
  if (_ownedFoodIds.contains(foodId)) {
    _ownedFoodIds.remove(foodId);
  } else {
    _ownedFoodIds.add(foodId);
  }
  notifyListeners();
}
```

### バックエンドAPI

- 食品検索: `GET /api/v1/foods/search?q=keyword&category=野菜類`
- 献立調整: `POST /api/v1/optimize/multi-day/refine`
  ```json
  {
    "current_plan": {...},
    "exclude_dish_ids": [1, 2, 3],
    "keep_dish_ids": [4, 5]
  }
  ```

---

## 作業の進め方

1. このチェックリストの該当項目を `[x]` でマークして進捗管理
2. 各タスクは独立してコミット可能
3. P1タスクを優先的に実装
4. UIの変更は `ui-design-mobile.svg` を参照しながら実装

---

## 関連ファイル

- 設計書: `docs/ui-design-mobile.svg`
- 実装計画: `docs/PLAN.md`
- フロントエンド: `frontend/lib/`
  - screens/
  - modals/
  - providers/
  - models/
