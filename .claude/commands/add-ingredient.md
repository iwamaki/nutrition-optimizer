# 食材追加コマンド

ユーザーが指定した食材を `backend/data/app_ingredients.csv` に追加します。

## 手順

1. ユーザーに追加したい食材名を確認する
2. 文科省食品成分表（food_composition_2023.xlsx）から該当する食品を検索してmext_codeを特定する
3. 適切なカテゴリを決定する（穀類/野菜類/きのこ類/藻類/豆類/いも類/肉類/魚介類/卵類/乳類/果実類/調味料）
4. 適切な絵文字を選ぶ
5. `backend/data/app_ingredients.csv` に追加する（IDは最後の番号+1）
6. サーバーを再起動してDBを更新する

## CSVフォーマット

```
id,name,category,mext_code,emoji
```

## 例

```csv
131,豚こま肉,肉類,11126,🥩
```

## 注意

- mext_codeは文科省データと一致する必要がある
- 同じ食材の重複登録を避ける
- カテゴリは既存のものから選ぶ

$ARGUMENTS
