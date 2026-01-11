#!/usr/bin/env python3
"""
料理CSVの移行スクリプト

mext_codeベースのingredientsを食品名ベースに変換する。

使用例:
  python tools/migrate_dishes_csv.py data/dishes.csv data/dishes_new.csv
"""

import argparse
import csv
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, FoodDB


def migrate_ingredients(db, ingredients_str: str) -> tuple[str, list[str]]:
    """
    mext_codeベースのingredientsを食品名ベースに変換

    Returns:
        (変換後の文字列, エラーリスト)
    """
    if not ingredients_str:
        return ("", [])

    new_parts = []
    errors = []

    for ing_str in ingredients_str.split("|"):
        parts = ing_str.strip().split(":")
        if len(parts) < 2:
            errors.append(f"形式エラー: {ing_str}")
            continue

        mext_code = parts[0].strip()
        amount = parts[1].strip()
        method = parts[2].strip() if len(parts) > 2 else "生"

        food = db.query(FoodDB).filter(FoodDB.mext_code == mext_code).first()
        if food:
            new_parts.append(f"{food.name}:{amount}:{method}")
        else:
            errors.append(f"コードが見つかりません: {mext_code}")

    return ("|".join(new_parts), errors)


def migrate_csv(input_path: Path, output_path: Path):
    """CSVファイルを移行"""
    db = SessionLocal()

    try:
        with open(input_path, encoding="utf-8") as f_in:
            reader = csv.DictReader(f_in)
            rows = list(reader)
            fieldnames = reader.fieldnames

        total_errors = []
        migrated_rows = []

        for i, row in enumerate(rows, start=2):
            name = row.get("name", "")
            ingredients_str = row.get("ingredients", "")

            new_ingredients, errors = migrate_ingredients(db, ingredients_str)

            if errors:
                for err in errors:
                    total_errors.append(f"行{i} '{name}': {err}")

            row["ingredients"] = new_ingredients
            migrated_rows.append(row)

        with open(output_path, "w", encoding="utf-8", newline="") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(migrated_rows)

        print(f"移行完了: {len(migrated_rows)}件")
        print(f"出力: {output_path}")

        if total_errors:
            print(f"\n警告: {len(total_errors)}件のエラー")
            for err in total_errors[:20]:
                print(f"  {err}")
            if len(total_errors) > 20:
                print(f"  ... 他{len(total_errors) - 20}件")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="料理CSVをmext_codeベースから食品名ベースに移行"
    )
    parser.add_argument("input", help="入力CSVファイル")
    parser.add_argument("output", help="出力CSVファイル")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"エラー: ファイルが見つかりません: {input_path}")
        sys.exit(1)

    migrate_csv(input_path, output_path)


if __name__ == "__main__":
    main()
