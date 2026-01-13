# 料理追加ワークフロー

LLM（Claude等）を使って新しい料理をCSVに追加する手順です。

## 概要

```
既存料理を確認  →  LLM生成  →  バリデーション  →  本番CSV
```

## 1. 既存料理を確認（重複回避）

LLMに既存料理リストを渡して重複を避けます。

```bash
cd backend
source venv/bin/activate

# カテゴリ別の件数を確認
python tools/list_dishes.py --categories

# 特定カテゴリの料理一覧
python tools/list_dishes.py -c 主食

# コンパクト形式（プロンプトにコピペしやすい）
python tools/list_dishes.py -c 主食 --compact
```

## 2. LLMでレシピを生成

既存料理リストを含めたプロンプトでLLMにレシピを生成させます：

---

あなたは料理レシピをCSV形式で作成するアシスタントです。

### CSVフォーマット
```
name,category,meal_types,ingredients,instructions
```

- name: 料理名
- category: 主食/主菜/副菜/汁物/デザート
- meal_types: breakfast,lunch,dinner,snack をカンマ区切り
- ingredients: 食品名:量g:調理法 を | で区切り
- instructions: 作り方

### 調理法
生, 茹でる, 蒸す, 焼く, 炒める, 揚げる, 煮る, 電子レンジ

### 既存の料理（これ以外で作成してください）
[ここに list_dishes.py の出力をペースト]

### 例
```csv
チキンカレー,主食,"lunch,dinner","鶏もも肉:100:煮る|玉ねぎ:50:炒める|人参:30:煮る|ごはん:150:蒸す","鶏肉と野菜を炒めてカレールーで煮込み、ごはんにかける"
```

[カテゴリ]の新しいレシピを10件、CSV形式で作成してください。

---

## 3. CSVフォーマット

`backend/data/dishes.csv` の形式：

| 列名 | 説明 | 例 |
|------|------|-----|
| name | 料理名 | 親子丼 |
| category | カテゴリ | 主食/主菜/副菜/汁物/デザート |
| meal_types | 食事タイプ | "lunch,dinner" |
| ingredients | 材料（食品名:量g:調理法） | "鶏もも肉:80:煮る\|卵:50:煮る" |
| instructions | 作り方 | "鶏肉を煮て卵でとじる" |

## 4. バリデーション

LLMが生成したCSVを正式な食品名に変換します。

```bash
cd backend
source venv/bin/activate

# バリデーションツールを実行
python tools/validate_dishes.py data/dishes_draft.csv -o data/dishes.csv

# 候補が1件の場合は自動選択
python tools/validate_dishes.py data/dishes_draft.csv --auto
```

### バリデーションの流れ

```
行2 '親子丼' を検証中...
  × '鶏もも肉' が見つかりません
  候補:
    1. ＜鳥肉類＞ にわとり ［若どり・主品目］ もも 皮つき 生 [肉類]
    2. ＜鳥肉類＞ にわとり ［若どり・主品目］ もも 皮つき 焼き [肉類]
  選択 (1-2, s=スキップ, m=手動入力): 2
    → '＜鳥肉類＞ にわとり ［若どり・主品目］ もも 皮つき 焼き' に修正
  ✓ '卵'
  ...
```

## 5. 食品名の検索（参考）

バリデーションツールが自動で検索しますが、事前に調べたい場合：

```bash
python tools/food_search.py 鶏肉
python tools/food_search.py もも 焼き -c 肉類
python tools/food_search.py --categories  # カテゴリ一覧
```

## 6. 動作確認

CSVを更新したら、DBを再作成してエラーがないか確認します。

```bash
cd backend
rm nutrition.db
source venv/bin/activate
uvicorn app.main:app --reload
```

エラーがあれば警告が表示されます：
```
警告: 2件のエラー
  行5 '親子丼': 食品名が見つかりません: '鶏もも肉'
```

## 7. レシピ詳細の生成

CSVに追加した料理の詳細な調理手順を、Gemini APIで自動生成します。

### 環境変数の設定

```bash
# Google Cloud Secret Manager から取得する場合
export GEMINI_API_KEY=$(gcloud secrets versions access latest \
  --secret=GEMINI_API_KEY --project=gen-lang-client-0309495198)

# または直接設定
export GEMINI_API_KEY='your-api-key'
```

### CLIツールで生成

```bash
cd backend
source venv/bin/activate

# 未登録レシピを確認（ドライラン）
python tools/generate_recipes.py --dry-run

# 全ての未登録レシピを生成
python tools/generate_recipes.py

# カテゴリ指定
python tools/generate_recipes.py -c 主食

# 件数制限
python tools/generate_recipes.py --limit 5

# 特定の料理のみ
python tools/generate_recipes.py --name "親子丼"
```

### API経由で生成（サーバー起動中）

```bash
# 特定の料理のレシピ詳細を生成
curl -X POST http://localhost:8000/api/v1/dishes/{dish_id}/generate-recipe

# バッチ生成（5件ずつ）
curl -X POST "http://localhost:8000/api/v1/dishes/generate-recipes/batch?limit=5"
```

### 生成データの確認

生成されたレシピ詳細は `data/recipe_details.json` に保存されます：

```json
{
  "親子丼": {
    "prep_time": 10,
    "cook_time": 15,
    "servings": 1,
    "steps": [
      "鶏もも肉を一口大に切る",
      "玉ねぎは薄切りにする",
      ...
    ],
    "tips": "卵は半熟に仕上げるのがポイント"
  }
}
```

## 料理追加のクイックリファレンス

```bash
# 1. 既存料理確認
python tools/list_dishes.py -c [カテゴリ] --compact

# 2. LLMでCSV生成（別途）

# 3. バリデーション
python tools/validate_dishes.py data/draft.csv -o data/dishes.csv

# 4. DB再作成
rm nutrition.db && uvicorn app.main:app --reload

# 5. レシピ詳細生成
export GEMINI_API_KEY=...
python tools/generate_recipes.py --dry-run  # 確認
python tools/generate_recipes.py            # 実行
```
