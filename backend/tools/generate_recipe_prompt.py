#!/usr/bin/env python3
"""
未追加レシピを検出し、LLMプロンプトを生成するツール

使用例:
  python tools/generate_recipe_prompt.py              # 未追加レシピ一覧
  python tools/generate_recipe_prompt.py --next      # 次の1件のプロンプト生成
  python tools/generate_recipe_prompt.py --next -c 主菜  # 主菜の次の1件
  python tools/generate_recipe_prompt.py --index 5   # 5番目のレシピのプロンプト
"""

import argparse
import csv
import json
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"
DISHES_CSV = DATA_DIR / "dishes.csv"
RECIPE_DETAILS_JSON = DATA_DIR / "recipe_details.json"


def load_dishes() -> list[dict]:
    """dishes.csvを読み込む"""
    dishes = []
    with open(DISHES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dishes.append(row)
    return dishes


def load_recipe_details() -> dict:
    """recipe_details.jsonを読み込む"""
    if not RECIPE_DETAILS_JSON.exists():
        return {}
    with open(RECIPE_DETAILS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    # _schema は除外
    return {k: v for k, v in data.items() if not k.startswith("_")}


def parse_ingredients(ingredients_str: str) -> list[dict]:
    """材料文字列をパース: 食品名:グラム数:調理法"""
    ingredients = []
    for item in ingredients_str.split("|"):
        parts = item.split(":")
        if len(parts) >= 2:
            food_name = parts[0].strip()
            ingredients.append({
                "name": food_name,
                "amount": parts[1].strip(),
                "method": parts[2].strip() if len(parts) > 2 else "生"
            })
    return ingredients


def simplify_food_name(name: str) -> str:
    """食品名を簡略化（LLM向け）"""
    # 例: "＜魚類＞　（さけ・ます類）　しろさけ　焼き" → "しろさけ（焼き）"
    parts = name.replace("＜", "").replace("＞", "").replace("［", "").replace("］", "")
    parts = parts.replace("（", " ").replace("）", " ")
    tokens = [t.strip() for t in parts.split() if t.strip()]
    if len(tokens) >= 2:
        # 最後の2つを使う（食品名 + 状態）
        return f"{tokens[-2]}（{tokens[-1]}）" if tokens[-1] in ["生", "焼き", "ゆで", "蒸す", "油いため"] else tokens[-1]
    return tokens[-1] if tokens else name


def get_missing_recipes(dishes: list[dict], existing: dict, category: str = None) -> list[dict]:
    """未追加レシピを取得"""
    missing = []
    for dish in dishes:
        name = dish["name"]
        if name not in existing:
            if category is None or dish.get("category") == category:
                missing.append(dish)
    return missing


def generate_single_prompt(recipe: dict) -> str:
    """1件のレシピ用プロンプトを生成"""
    name = recipe["name"]
    category = recipe["category"]
    ingredients = parse_ingredients(recipe.get("ingredients", ""))
    instructions_hint = recipe.get("instructions", "")

    prompt = f"""以下の料理について、詳細なレシピをJSON形式で生成してください。

## 料理名
{name}（{category}）

## 材料（1人前）
"""
    for ing in ingredients:
        simple_name = simplify_food_name(ing['name'])
        prompt += f"- {simple_name}: {ing['amount']}g\n"

    if instructions_hint:
        prompt += f"\n## 参考（現在の簡易説明）\n{instructions_hint}\n"

    prompt += """
## 出力フォーマット
以下のJSON形式で出力してください。コードブロックで囲んでください。

```json
{
  "RECIPE_NAME": {
    "prep_time": 下準備時間（分）,
    "cook_time": 調理時間（分）,
    "servings": 1,
    "steps": [
      "手順1（具体的に）",
      "手順2（火加減や時間も含める）",
      ...
    ],
    "tips": "コツ・ポイント"
  }
}
```

## 注意事項
- RECIPE_NAME は「""" + name + """」に置き換えてください
- 手順は具体的に、初心者でもわかるように
- 火加減（強火/中火/弱火）や時間の目安を含める
- 材料の下処理も手順に含める
"""
    return prompt


def main():
    parser = argparse.ArgumentParser(description="未追加レシピを検出してLLMプロンプトを生成")
    parser.add_argument("-c", "--category", help="カテゴリで絞り込み（主食/主菜/副菜/汁物/デザート）")
    parser.add_argument("-n", "--next", action="store_true", help="次の1件のプロンプトを生成")
    parser.add_argument("-i", "--index", type=int, help="指定番号のレシピのプロンプトを生成（1始まり）")
    parser.add_argument("--list", action="store_true", help="未追加レシピ名のみ一覧表示")
    parser.add_argument("--stats", action="store_true", help="カテゴリ別の統計を表示")
    args = parser.parse_args()

    dishes = load_dishes()
    existing = load_recipe_details()
    missing = get_missing_recipes(dishes, existing, args.category)

    # 統計表示
    if args.stats:
        all_missing = get_missing_recipes(dishes, existing, None)
        by_category = {}
        for r in all_missing:
            cat = r.get("category", "不明")
            by_category[cat] = by_category.get(cat, 0) + 1

        print(f"総料理数: {len(dishes)}")
        print(f"詳細追加済み: {len(existing)}")
        print(f"未追加合計: {len(all_missing)}")
        print("\nカテゴリ別未追加数:")
        for cat in ["主食", "主菜", "副菜", "汁物", "デザート"]:
            count = by_category.get(cat, 0)
            print(f"  {cat}: {count}件")
        return

    print(f"総料理数: {len(dishes)} / 詳細追加済み: {len(existing)} / 未追加: {len(missing)}")
    if args.category:
        print(f"カテゴリ: {args.category}")
    print()

    if not missing:
        if args.category:
            print(f"{args.category}のレシピ詳細はすべて追加済みです！")
        else:
            print("すべてのレシピ詳細が追加済みです！")
        return

    # 一覧表示
    if args.list:
        print("=== 未追加レシピ一覧 ===")
        for i, recipe in enumerate(missing, 1):
            print(f"{i:3}. [{recipe['category']}] {recipe['name']}")
        return

    # 1件のプロンプト生成
    if args.next or args.index:
        idx = (args.index - 1) if args.index else 0
        if idx < 0 or idx >= len(missing):
            print(f"エラー: インデックスは1〜{len(missing)}の範囲で指定してください")
            return

        recipe = missing[idx]
        print(f"=== [{idx + 1}/{len(missing)}] {recipe['name']} ===\n")
        print(generate_single_prompt(recipe))
        print(f"\n--- 次のレシピ: --index {idx + 2} ---" if idx + 1 < len(missing) else "\n--- これが最後のレシピです ---")
        return

    # デフォルト: 使い方を表示
    print("使い方:")
    print("  --list        未追加レシピの一覧を表示")
    print("  --next        次の1件のプロンプトを生成")
    print("  --index N     N番目のレシピのプロンプトを生成")
    print("  --stats       カテゴリ別の統計を表示")
    print("  -c カテゴリ   カテゴリで絞り込み")
    print()
    print("例:")
    print("  python tools/generate_recipe_prompt.py --next")
    print("  python tools/generate_recipe_prompt.py -c 主菜 --next")
    print("  python tools/generate_recipe_prompt.py --index 10")


if __name__ == "__main__":
    main()
