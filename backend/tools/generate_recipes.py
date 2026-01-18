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

  # 全レシピを強制再生成（プレースホルダー形式への移行用）
  python tools/generate_recipes.py --all --force

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

from app.infrastructure.external.gemini_recipe_generator import (
    get_recipe_generator,
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


def get_missing_recipes(dishes: list[dict], existing: dict) -> list[dict]:
    """未登録のレシピを取得"""
    missing = []
    for dish in dishes:
        name = dish["name"]
        if name not in existing and not name.startswith("_"):
            missing.append(dish)
    return missing


def load_food_names(data_dir: Path) -> dict[str, str]:
    """食材IDと名前の対応表を読み込み"""
    food_names = {}
    ingredients_csv = data_dir / "app_ingredients.csv"
    if ingredients_csv.exists():
        with open(ingredients_csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                food_names[row["id"]] = row["name"]
    return food_names


def parse_ingredients_with_names(ingredients_str: str, food_names: dict[str, str]) -> list[dict]:
    """材料文字列をパースして食材名を付与"""
    ingredients = []
    if not ingredients_str:
        return ingredients
    for item in ingredients_str.split("|"):
        parts = item.split(":")
        if len(parts) >= 2:
            food_id = parts[0].strip()
            amount = parts[1].strip()
            name = food_names.get(food_id, f"食材{food_id}")
            ingredients.append({
                "name": name,
                "amount": amount,
            })
    return ingredients


def main():
    parser = argparse.ArgumentParser(description="レシピ詳細をバッチ生成")
    parser.add_argument("-c", "--category", help="カテゴリで絞り込み")
    parser.add_argument("--limit", type=int, help="生成件数の上限")
    parser.add_argument("--name", help="特定の料理名を指定")
    parser.add_argument("--dry-run", action="store_true", help="生成せずに確認のみ")
    parser.add_argument("--delay", type=float, default=1.0, help="APIリクエスト間隔（秒）")
    parser.add_argument("--force", action="store_true", help="既存レシピを上書き再生成")
    parser.add_argument("--all", action="store_true", help="全レシピを対象にする（--forceと併用）")
    parser.add_argument("-y", "--yes", action="store_true", help="確認をスキップ")
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
    generator = get_recipe_generator()
    existing = generator._recipe_details
    food_names = load_food_names(DATA_DIR)

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

    # 対象を決定
    if args.all or args.force:
        # 全レシピを対象（--all または --force）
        target = dishes
        if args.all:
            print(f"対象: 全 {len(target)} 件")
        else:
            print(f"対象: {len(target)} 件（--force: 既存も再生成）")
    else:
        # 未登録のみ
        target = get_missing_recipes(dishes, existing)
        print(f"未登録: {len(target)} 件")

    if not target:
        print("\n生成対象のレシピがありません")
        return

    # 件数制限
    if args.limit:
        target = target[:args.limit]
        print(f"生成対象: {len(target)} 件（--limit）")

    # 対象一覧を表示
    print("\n--- 対象レシピ ---")
    for i, dish in enumerate(target, 1):
        name = dish['name']
        status = "（既存）" if name in existing else "（新規）"
        print(f"  {i}. {name} ({dish.get('category', '?')}) {status}")

    if args.dry_run:
        print("\n（ドライラン: 実際の生成は行いません）")
        return

    # 確認プロンプト（--all --force の場合、-y でスキップ可能）
    if args.all and args.force and len(target) > 5 and not args.yes:
        print(f"\n⚠️  {len(target)} 件のレシピを再生成します。よろしいですか？ [y/N] ", end="")
        confirm = input().strip().lower()
        if confirm != 'y':
            print("キャンセルしました")
            return

    print(f"\n--- 生成開始 ---")

    # 生成
    success = 0
    failed = []

    for i, dish in enumerate(target, 1):
        name = dish["name"]
        category = dish.get("category", "")
        ingredients = parse_ingredients_with_names(dish.get("ingredients", ""), food_names)
        hint = dish.get("instructions", "")

        print(f"[{i}/{len(target)}] {name}... ", end="", flush=True)

        try:
            result = generator.generate_recipe_detail(
                dish_name=name,
                category=category,
                ingredients=ingredients,
                hint=hint,
                save=True,
                force=args.force,
            )

            if result:
                print("OK")
                success += 1
            else:
                print("NG")
                failed.append(name)
        except Exception as e:
            print(f"NG ({e})")
            failed.append(name)

        # APIレート制限を考慮
        if i < len(target):
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
