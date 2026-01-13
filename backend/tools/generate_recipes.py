#!/usr/bin/env python3
"""
レシピ詳細バッチ生成ツール

使い方:
  # 未登録レシピを確認（ドライラン）
  python tools/generate_recipes.py --dry-run

  # 全ての未登録レシピを生成
  python tools/generate_recipes.py

  # カテゴリ指定
  python tools/generate_recipes.py -c 主食

  # 件数制限
  python tools/generate_recipes.py --limit 5

  # 特定の料理のみ（名前指定）
  python tools/generate_recipes.py --name "親子丼"

環境変数:
  GEMINI_API_KEY: Google AI Studio APIキー
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.recipe_generator import (
    generate_recipe_detail,
    load_recipe_details,
    simplify_food_name,
    GEMINI_AVAILABLE,
)

DATA_DIR = Path(__file__).parent.parent / "data"
DISHES_CSV = DATA_DIR / "dishes.csv"
RECIPE_DETAILS_JSON = DATA_DIR / "recipe_details.json"


def load_dishes(csv_path: Path) -> list[dict]:
    """dishes.csvを読み込み"""
    dishes = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dishes.append(row)
    return dishes


def parse_ingredients(ingredients_str: str) -> list[dict]:
    """材料文字列をパース"""
    ingredients = []
    if not ingredients_str:
        return ingredients
    for item in ingredients_str.split("|"):
        parts = item.split(":")
        if len(parts) >= 2:
            ingredients.append({
                "name": parts[0].strip(),
                "amount": parts[1].strip(),
            })
    return ingredients


def get_missing_recipes(dishes: list[dict], existing: dict) -> list[dict]:
    """未登録のレシピを取得"""
    missing = []
    for dish in dishes:
        name = dish["name"]
        if name not in existing and not name.startswith("_"):
            missing.append(dish)
    return missing


def main():
    parser = argparse.ArgumentParser(description="レシピ詳細をバッチ生成")
    parser.add_argument("-c", "--category", help="カテゴリで絞り込み")
    parser.add_argument("--limit", type=int, help="生成件数の上限")
    parser.add_argument("--name", help="特定の料理名を指定")
    parser.add_argument("--dry-run", action="store_true", help="生成せずに確認のみ")
    parser.add_argument("--delay", type=float, default=1.0, help="APIリクエスト間隔（秒）")
    args = parser.parse_args()

    # APIキー確認
    if not args.dry_run:
        if not GEMINI_AVAILABLE:
            print("エラー: google-generativeai がインストールされていません")
            print("  pip install google-generativeai")
            sys.exit(1)
        if not os.getenv("GEMINI_API_KEY"):
            print("エラー: GEMINI_API_KEY が設定されていません")
            print("  export GEMINI_API_KEY='your-api-key'")
            sys.exit(1)

    # データ読み込み
    dishes = load_dishes(DISHES_CSV)
    existing = load_recipe_details()

    print(f"料理マスタ: {len(dishes)} 件")
    print(f"レシピ詳細: {len(existing) - 1} 件（_schemaを除く）")

    # 絞り込み
    if args.category:
        dishes = [d for d in dishes if d.get("category") == args.category]
        print(f"カテゴリ '{args.category}': {len(dishes)} 件")

    if args.name:
        dishes = [d for d in dishes if d.get("name") == args.name]
        if not dishes:
            print(f"エラー: 料理 '{args.name}' が見つかりません")
            sys.exit(1)

    # 未登録を抽出
    missing = get_missing_recipes(dishes, existing)
    print(f"未登録: {len(missing)} 件")

    if not missing:
        print("\n全てのレシピ詳細が登録済みです")
        return

    # 件数制限
    if args.limit:
        missing = missing[:args.limit]
        print(f"生成対象: {len(missing)} 件（--limit）")

    # 対象一覧を表示
    print("\n--- 対象レシピ ---")
    for i, dish in enumerate(missing, 1):
        print(f"  {i}. {dish['name']} ({dish.get('category', '?')})")

    if args.dry_run:
        print("\n（ドライラン: 実際の生成は行いません）")
        return

    print(f"\n--- 生成開始 ---")

    # 生成
    success = 0
    failed = []

    for i, dish in enumerate(missing, 1):
        name = dish["name"]
        category = dish.get("category", "")
        ingredients = parse_ingredients(dish.get("ingredients", ""))
        hint = dish.get("instructions", "")

        print(f"[{i}/{len(missing)}] {name}... ", end="", flush=True)

        result = generate_recipe_detail(
            dish_name=name,
            category=category,
            ingredients=ingredients,
            hint=hint,
            save=True,
        )

        if result:
            print("OK")
            success += 1
        else:
            print("NG")
            failed.append(name)

        # APIレート制限を考慮
        if i < len(missing):
            time.sleep(args.delay)

    # 結果サマリ
    print(f"\n--- 完了 ---")
    print(f"成功: {success} 件")
    if failed:
        print(f"失敗: {len(failed)} 件")
        for name in failed:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
