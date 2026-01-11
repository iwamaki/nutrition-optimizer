# 料理追加ワークフロー

LLM（Claude等）を使って新しい料理をCSVに追加する手順です。

## 1. 食品コードを検索

料理に使う食材の文科省コード（mext_code）を検索します。

```bash
cd backend
python tools/food_search.py 鶏肉
python tools/food_search.py もも 焼き -c 肉類
python tools/food_search.py --code 11222
```

### よく使う食品コード例

| コード | 食品名 | カテゴリ |
|--------|--------|----------|
| 01088 | 精白米めし | 穀類 |
| 01174 | 角形食パン焼き | 穀類 |
| 11222 | 若どり もも 焼き | 肉類 |
| 11124 | 豚ロース焼き | 肉類 |
| 10136 | しろさけ焼き | 魚介類 |
| 12004 | 全卵生 | 卵類 |
| 04032 | 木綿豆腐 | 豆類 |
| 06153 | たまねぎ 生 | 野菜類 |

## 2. CSVフォーマット

`backend/data/dishes.csv` に以下の形式で追加します。

```csv
name,category,meal_types,ingredients,instructions
```

### 各列の説明

| 列名 | 説明 | 例 |
|------|------|-----|
| name | 料理名 | 親子丼 |
| category | カテゴリ（主食/主菜/副菜/汁物/デザート） | 主菜 |
| meal_types | 食事タイプ（breakfast/lunch/dinner/snack） | "lunch,dinner" |
| ingredients | 材料（mext_code:量g:調理法 を \| で区切り） | "11222:80:煮る\|12004:50:煮る" |
| instructions | 作り方（改行は \\n でエスケープ） | "鶏肉を煮て卵でとじる" |

### 調理法一覧

- 生
- 茹でる
- 蒸す
- 焼く
- 炒める
- 揚げる
- 煮る
- 電子レンジ

## 3. 追加例

```csv
親子丼,主菜,"lunch,dinner","11222:80:煮る|12004:50:煮る|06153:30:煮る|01088:150:蒸す","鶏もも肉を一口大に切り、玉ねぎと一緒に出汁で煮る。溶き卵を回し入れてとじ、ごはんにのせる"
```

## 4. LLMプロンプト例

以下のプロンプトでLLMにレシピを生成させることができます：

---

あなたは料理レシピをCSV形式で作成するアシスタントです。

### 食品コード検索
食材の文科省コード（mext_code）を確認するために、以下のコマンドを使ってください：
```bash
python tools/food_search.py [キーワード]
```

### CSVフォーマット
```
name,category,meal_types,ingredients,instructions
```

- name: 料理名
- category: 主食/主菜/副菜/汁物/デザート
- meal_types: breakfast,lunch,dinner,snack をカンマ区切り
- ingredients: mext_code:量g:調理法 を | で区切り
- instructions: 作り方（改行は \n）

### 調理法
生, 茹でる, 蒸す, 焼く, 炒める, 揚げる, 煮る, 電子レンジ

### 例
```csv
チキンカレー,主菜,"lunch,dinner","11222:100:煮る|06153:50:炒める|06215:30:煮る","鶏肉と野菜を炒めてカレールーで煮込む"
```

[料理名]のレシピをCSV形式で作成してください。

---

## 5. バリデーション

CSVを追加したら、サーバーを再起動して読み込みエラーがないか確認します。

```bash
# DBを削除してクリーンスタート
rm nutrition.db

# サーバー起動
uvicorn app.main:app --reload
```

エラーがあれば以下のような警告が表示されます：
```
警告: 2件のエラー
  行5 '親子丼': コードが見つかりません: 99999
```
