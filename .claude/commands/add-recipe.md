# 料理追加コマンド

ユーザーが指定した料理を `backend/data/dishes.csv` に追加し、Gemini APIでレシピ詳細を生成します。

## 手順

1. ユーザーに追加したい料理名を確認する
2. 料理のカテゴリを決定する（主食/主菜/副菜/汁物/デザート）
3. meal_typesを決定する（breakfast/lunch/dinner/snack の組み合わせ）
4. storage_days（作り置き日数）を決定する
5. 材料を `backend/data/app_ingredients.csv` から選んで分量と調理法を決める
6. `backend/data/dishes.csv` に追加する
7. DBを再構築する（nutrition.db削除→サーバー再起動）
8. Gemini APIでレシピ詳細を生成する

## dishes.csv フォーマット

```
name,category,meal_types,storage_days,ingredients,instructions
```

### ingredientsの形式

`ingredient_id:量g:調理法` をパイプ（|）で区切る

- ingredient_id: app_ingredients.csvのID
- 量g: グラム数（1人前）
- 調理法: 生/焼く/煮る/炒める/茹でる/蒸す/揚げる

## 例

```csv
肉野菜炒め,主菜,"lunch,dinner",1,49:80:炒める|19:60:炒める|16:40:炒める|22:30:炒める,豚肉と野菜を炒めて塩こしょうで味付け
```

## Geminiレシピ生成

```bash
cd backend
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=GEMINI_API_KEY --project=gen-lang-client-0309495198)
python tools/generate_recipes.py --name "料理名"
```

## 注意

- ingredient_idは必ずapp_ingredients.csvに存在するものを使う
- 分量は1人前で指定する
- 同じ料理名の重複登録を避ける

$ARGUMENTS
