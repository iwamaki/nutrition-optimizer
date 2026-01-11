#!/usr/bin/env python3
"""
料理CSVバリデーションツール

LLMが生成した自然言語の食品名をあいまい検索し、
文科省データと完全一致する正式な食品名に変換する。

使用例:
  python tools/validate_dishes.py data/dishes_draft.csv
  python tools/validate_dishes.py data/dishes_draft.csv -o data/dishes.csv
  python tools/validate_dishes.py data/dishes_draft.csv --auto  # 候補が1件なら自動選択
"""

import argparse
import csv
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, FoodDB


class DishValidator:
    def __init__(self, db, auto_select: bool = False):
        self.db = db
        self.auto_select = auto_select
        self.errors = []
        self.warnings = []
        self.corrections = 0

    def find_food(self, name: str) -> tuple[FoodDB | None, list[FoodDB]]:
        """
        食品を検索。完全一致→あいまい検索の順。

        Returns:
            (完全一致した食品 or None, あいまい検索の候補リスト)
        """
        # 完全一致
        exact = self.db.query(FoodDB).filter(FoodDB.name == name).first()
        if exact:
            return (exact, [])

        # あいまい検索（キーワード分割）
        keywords = name.replace("　", " ").replace("、", " ").replace(",", " ").split()
        keywords = [kw.strip() for kw in keywords if kw.strip()]

        if not keywords:
            return (None, [])

        query = self.db.query(FoodDB)
        for kw in keywords:
            query = query.filter(FoodDB.name.like(f"%{kw}%"))

        candidates = query.limit(10).all()
        return (None, candidates)

    def select_candidate(self, original: str, candidates: list[FoodDB]) -> str | None:
        """候補から選択（対話またはauto）"""
        if not candidates:
            return None

        if self.auto_select and len(candidates) == 1:
            print(f"    → 自動選択: {candidates[0].name}")
            return candidates[0].name

        print(f"  候補:")
        for i, c in enumerate(candidates, 1):
            print(f"    {i}. {c.name} [{c.category}]")

        while True:
            try:
                choice = input(f"  選択 (1-{len(candidates)}, s=スキップ, m=手動入力): ")
            except EOFError:
                return None

            choice = choice.strip().lower()

            if choice == "s":
                return None
            if choice == "m":
                try:
                    manual = input("  食品名を入力: ")
                except EOFError:
                    return None
                return manual.strip() if manual.strip() else None

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(candidates):
                    return candidates[idx].name
            except ValueError:
                pass

            print("  無効な入力です")

    def validate_ingredient(self, food_name: str, row_num: int, dish_name: str) -> str | None:
        """
        単一の食品名を検証

        Returns:
            検証済みの食品名 or None（スキップ）
        """
        food, candidates = self.find_food(food_name)

        if food:
            print(f"  ✓ '{food_name}'")
            return food.name

        if candidates:
            print(f"  × '{food_name}' が見つかりません")
            selected = self.select_candidate(food_name, candidates)

            if selected:
                # 選択した名前を再検証
                final_food = self.db.query(FoodDB).filter(FoodDB.name == selected).first()
                if final_food:
                    print(f"    → '{final_food.name}' に修正")
                    self.corrections += 1
                    return final_food.name
                else:
                    self.warnings.append(f"行{row_num} '{dish_name}': '{selected}' が見つかりません")
                    return selected
            else:
                self.warnings.append(f"行{row_num} '{dish_name}': '{food_name}' をスキップ")
                return None
        else:
            print(f"  × '{food_name}' - 候補なし")
            self.errors.append(f"行{row_num} '{dish_name}': '{food_name}' の候補が見つかりません")
            return None

    def validate_row(self, row_num: int, row: dict) -> dict:
        """1行を検証し、修正した行を返す"""
        name = row.get("name", "")
        print(f"\n行{row_num} '{name}' を検証中...")

        ingredients_str = row.get("ingredients", "")
        if not ingredients_str:
            print("  (材料なし)")
            return row

        new_ingredients = []

        for ing_str in ingredients_str.split("|"):
            parts = ing_str.strip().split(":")
            if len(parts) < 2:
                self.errors.append(f"行{row_num} '{name}': 形式エラー '{ing_str}'")
                continue

            food_name = parts[0].strip()
            amount = parts[1].strip()
            method = parts[2].strip() if len(parts) > 2 else "生"

            validated_name = self.validate_ingredient(food_name, row_num, name)

            if validated_name:
                new_ingredients.append(f"{validated_name}:{amount}:{method}")

        row["ingredients"] = "|".join(new_ingredients)
        return row


def validate_csv(input_path: Path, output_path: Path, auto_select: bool):
    """CSVファイルをバリデーション"""
    db = SessionLocal()
    validator = DishValidator(db, auto_select=auto_select)

    try:
        with open(input_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames

        validated_rows = []
        for i, row in enumerate(rows, start=2):
            validated_row = validator.validate_row(i, row)
            validated_rows.append(validated_row)

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(validated_rows)

        print(f"\n{'='*60}")
        print(f"検証完了: {output_path}")
        print(f"  料理数: {len(validated_rows)}")
        print(f"  修正: {validator.corrections}件")

        if validator.errors:
            print(f"\nエラー: {len(validator.errors)}件")
            for e in validator.errors:
                print(f"  {e}")

        if validator.warnings:
            print(f"\n警告: {len(validator.warnings)}件")
            for w in validator.warnings:
                print(f"  {w}")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="料理CSVをバリデーションし、食品名を正式名称に変換",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  %(prog)s data/dishes_draft.csv                    # 対話モード
  %(prog)s data/dishes_draft.csv -o data/dishes.csv # 出力先を指定
  %(prog)s data/dishes_draft.csv --auto             # 候補1件なら自動選択
"""
    )
    parser.add_argument("input", help="入力CSVファイル")
    parser.add_argument(
        "-o", "--output",
        help="出力CSVファイル (デフォルト: 入力ファイル名_validated.csv)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="候補が1件の場合は自動選択"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_stem(input_path.stem + "_validated")

    if not input_path.exists():
        print(f"エラー: ファイルが見つかりません: {input_path}")
        sys.exit(1)

    validate_csv(input_path, output_path, args.auto)


if __name__ == "__main__":
    main()
