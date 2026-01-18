#!/usr/bin/env python3
"""
dishes.csvの食材ID表記を食材名表記に変換するスクリプト

変換前: 52:100:焼く|134:18.0:生
変換後: 鶏もも肉:100:焼く|醤油:18.0:生
"""

import csv
import sys
from pathlib import Path


def load_ingredients(csv_path: Path) -> dict[int, str]:
    """app_ingredients.csvから ID -> 名前 のマッピングを作成"""
    mapping = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ing_id = int(row["id"])
            name = row["name"]
            mapping[ing_id] = name
    return mapping


def convert_ingredients(ingredients_str: str, id_to_name: dict[int, str]) -> str:
    """
    食材文字列のIDを名前に変換

    入力: "52:100:焼く|134:18.0:生"
    出力: "鶏もも肉:100:焼く|醤油:18.0:生"
    """
    if not ingredients_str:
        return ingredients_str

    parts = []
    for item in ingredients_str.split("|"):
        components = item.split(":")
        if len(components) >= 3:
            try:
                ing_id = int(components[0])
                amount = components[1]
                method = components[2]
                name = id_to_name.get(ing_id, f"不明({ing_id})")
                parts.append(f"{name}:{amount}:{method}")
            except ValueError:
                # IDが数値でない場合はそのまま（既に名前の可能性）
                parts.append(item)
        else:
            parts.append(item)

    return "|".join(parts)


def main():
    data_dir = Path(__file__).parent.parent / "data"
    ingredients_csv = data_dir / "app_ingredients.csv"
    dishes_csv = data_dir / "dishes.csv"
    output_csv = data_dir / "dishes_named.csv"

    # 引数で出力先を指定可能
    if len(sys.argv) > 1:
        if sys.argv[1] == "--inplace":
            output_csv = dishes_csv
            print("インプレース変換モード: dishes.csvを直接更新します")
        else:
            output_csv = Path(sys.argv[1])

    # 食材マッピングを読み込み
    print(f"食材マスタを読み込み中: {ingredients_csv}")
    id_to_name = load_ingredients(ingredients_csv)
    print(f"  {len(id_to_name)}件の食材を読み込みました")

    # dishes.csvを読み込んで変換
    print(f"料理マスタを変換中: {dishes_csv}")
    rows = []
    with open(dishes_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            original = row["ingredients"]
            converted = convert_ingredients(original, id_to_name)
            row["ingredients"] = converted
            rows.append(row)

    # 出力
    print(f"出力先: {output_csv}")
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"変換完了: {len(rows)}件の料理を処理しました")

    # サンプル表示
    print("\n変換例:")
    sample_dishes = ["白ごはん", "鶏の照り焼き", "麻婆豆腐"]
    for row in rows:
        if row["name"] in sample_dishes:
            print(f"  {row['name']}: {row['ingredients']}")


if __name__ == "__main__":
    main()
