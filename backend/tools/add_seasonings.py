#!/usr/bin/env python3
"""
dishes.csvに調味料を自動追加するスクリプト

料理名・フレーバープロファイル・調理法から調味料を推定して追加する。
"""

import csv
import sys
from pathlib import Path

# 調味料ID（app_ingredients.csvと対応）
SEASONINGS = {
    "醤油": 134,
    "みりん": 135,
    "砂糖": 136,
    "塩": 137,
    "酢": 138,
    "サラダ油": 139,
    "マヨネーズ": 140,
    "ケチャップ": 141,
    "ソース": 142,
    "料理酒": 143,
    "ごま油": 144,
    "オリーブ油": 145,
    "こしょう": 146,
    "めんつゆ": 147,
}

# 1人前あたりの標準使用量（g）
SEASONING_AMOUNTS = {
    "醤油": 9,      # 小さじ1.5
    "みりん": 9,    # 小さじ1.5
    "砂糖": 3,      # 小さじ1
    "塩": 1,        # 少々
    "酢": 5,        # 小さじ1
    "サラダ油": 4,  # 小さじ1
    "マヨネーズ": 12,  # 大さじ1
    "ケチャップ": 15,  # 大さじ1
    "ソース": 15,   # 大さじ1
    "料理酒": 5,    # 小さじ1
    "ごま油": 2,    # 少々
    "オリーブ油": 4,  # 小さじ1
    "こしょう": 0.1,  # 少々
    "めんつゆ": 15,  # 大さじ1
}


def guess_seasonings(name: str, flavor: str, instructions: str) -> list[tuple[str, float]]:
    """
    料理名・フレーバー・調理説明から調味料を推定

    Returns:
        [(調味料名, 量g), ...]
    """
    seasonings = []
    name_lower = name.lower()
    inst_lower = instructions.lower() if instructions else ""

    # === 特定パターン ===

    # 生・そのまま系（調味料なし）
    no_seasoning_words = [
        "バナナ", "りんご", "みかん", "ヨーグルト", "いちご", "キウイ",
        "オレンジ", "ぶどう", "もも", "梨", "マンゴー", "パイナップル",
        "グレープフルーツ", "白ごはん", "玄米ご飯", "トースト", "食パン",
        "味噌汁", "みそ汁",  # 味噌は食材として含まれるため
    ]
    if any(w in name for w in no_seasoning_words):
        return []

    # シンプルな生野菜（千切り等）
    if any(w in name for w in ["千切り", "生野菜"]):
        return []

    # 冷奴・納豆（醤油のみ）
    if name in ["冷奴", "納豆"]:
        return [("醤油", 6)]

    # サラダ系
    if "サラダ" in name:
        if "ツナ" in name or "マヨ" in name:
            seasonings.append(("マヨネーズ", 12))
        elif "ごま" in name or flavor == "中華":
            seasonings.append(("ごま油", 2))
            seasonings.append(("醤油", 6))
        else:
            seasonings.append(("塩", 0.5))
            seasonings.append(("オリーブ油", 4))
        return seasonings

    # 丼もの
    if "丼" in name:
        seasonings.append(("醤油", 12))
        seasonings.append(("みりん", 9))
        seasonings.append(("砂糖", 3))
        seasonings.append(("料理酒", 5))
        return seasonings

    # カレー
    if "カレー" in name:
        seasonings.append(("サラダ油", 4))
        return seasonings

    # ラーメン
    if "ラーメン" in name:
        if "味噌" in name:
            seasonings.append(("ごま油", 2))
        else:
            seasonings.append(("醤油", 9))
        seasonings.append(("塩", 1))
        return seasonings

    # パスタ・麺類
    if any(w in name for w in ["パスタ", "ナポリタン", "ペペロンチーノ", "カルボナーラ"]):
        if "ナポリタン" in name:
            seasonings.append(("ケチャップ", 30))
            seasonings.append(("サラダ油", 4))
        else:
            seasonings.append(("オリーブ油", 8))
            seasonings.append(("塩", 1))
        return seasonings

    # 焼きそば
    if "焼きそば" in name:
        seasonings.append(("ソース", 20))
        seasonings.append(("サラダ油", 4))
        return seasonings

    # 炒飯・チャーハン
    if "チャーハン" in name or "炒飯" in name:
        seasonings.append(("醤油", 6))
        seasonings.append(("ごま油", 4))
        seasonings.append(("塩", 0.5))
        return seasonings

    # オムライス
    if "オムライス" in name:
        seasonings.append(("ケチャップ", 30))
        seasonings.append(("サラダ油", 8))
        seasonings.append(("塩", 0.5))
        return seasonings

    # うどん・そば
    if any(w in name for w in ["うどん", "そば"]):
        seasonings.append(("めんつゆ", 30))
        return seasonings

    # 揚げ物
    if any(w in name for w in ["揚げ", "フライ", "カツ", "天ぷら", "唐揚げ", "コロッケ"]):
        seasonings.append(("サラダ油", 15))  # 揚げ油
        if flavor == "和風":
            seasonings.append(("醤油", 6))
        else:
            seasonings.append(("塩", 1))
            seasonings.append(("こしょう", 0.1))
        return seasonings

    # 味噌汁・スープ
    if "味噌汁" in name or "みそ汁" in name:
        return []  # 味噌は別の食材として登録されている
    if "スープ" in name or "ポタージュ" in name:
        seasonings.append(("塩", 1))
        seasonings.append(("こしょう", 0.1))
        return seasonings

    # シチュー
    if "シチュー" in name:
        seasonings.append(("塩", 1))
        seasonings.append(("こしょう", 0.1))
        return seasonings

    # おひたし
    if "おひたし" in name:
        seasonings.append(("醤油", 6))
        return seasonings

    # 和え物
    if "和え" in name:
        if "ごま" in name:
            seasonings.append(("醤油", 6))
            seasonings.append(("砂糖", 2))
        elif "白和え" in name:
            seasonings.append(("醤油", 6))
            seasonings.append(("砂糖", 2))
        else:
            seasonings.append(("醤油", 6))
        return seasonings

    # 煮物
    if "煮" in name or "煮る" in inst_lower:
        if flavor == "和風":
            seasonings.append(("醤油", 9))
            seasonings.append(("みりん", 9))
            seasonings.append(("砂糖", 3))
            seasonings.append(("料理酒", 5))
        return seasonings

    # 炒め物
    if "炒め" in name or "炒める" in inst_lower:
        if flavor == "中華":
            seasonings.append(("ごま油", 4))
            seasonings.append(("醤油", 6))
        elif flavor == "和風":
            seasonings.append(("サラダ油", 4))
            seasonings.append(("醤油", 6))
        else:
            seasonings.append(("オリーブ油", 4))
            seasonings.append(("塩", 1))
        return seasonings

    # 焼き物
    if "焼き" in name or "焼く" in inst_lower or "ソテー" in name:
        if "塩焼き" in name:
            seasonings.append(("塩", 2))
        elif "照り焼き" in name:
            seasonings.append(("醤油", 12))
            seasonings.append(("みりん", 12))
            seasonings.append(("砂糖", 6))
            seasonings.append(("料理酒", 5))
        elif "生姜焼き" in name:
            seasonings.append(("醤油", 12))
            seasonings.append(("みりん", 9))
            seasonings.append(("料理酒", 5))
        elif flavor == "和風":
            seasonings.append(("醤油", 6))
            seasonings.append(("サラダ油", 4))
        else:
            seasonings.append(("塩", 1))
            seasonings.append(("こしょう", 0.1))
            seasonings.append(("サラダ油", 4))
        return seasonings

    # === フレーバーベースのデフォルト ===
    if flavor == "和風":
        seasonings.append(("醤油", 6))
        seasonings.append(("みりん", 6))
    elif flavor == "洋風":
        seasonings.append(("塩", 1))
        seasonings.append(("こしょう", 0.1))
        seasonings.append(("オリーブ油", 4))
    elif flavor == "中華":
        seasonings.append(("ごま油", 4))
        seasonings.append(("醤油", 6))

    return seasonings


def format_ingredient(seasoning_name: str, amount: float) -> str:
    """調味料をingredients形式に変換"""
    seasoning_id = SEASONINGS[seasoning_name]
    return f"{seasoning_id}:{amount}:生"


def process_dishes(input_path: Path, output_path: Path, dry_run: bool = False):
    """dishes.csvを処理して調味料を追加"""
    rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    updated_count = 0
    for row in rows:
        name = row["name"]
        flavor = row["flavor_profile"]
        instructions = row.get("instructions", "")
        ingredients = row["ingredients"]

        # すでに調味料が含まれているかチェック
        existing_ids = {int(ing.split(":")[0]) for ing in ingredients.split("|") if ing}
        seasoning_ids = set(SEASONINGS.values())
        if existing_ids & seasoning_ids:
            # すでに調味料あり、スキップ
            continue

        # 調味料を推定
        guessed = guess_seasonings(name, flavor, instructions)
        if not guessed:
            continue

        # ingredients に追加
        new_parts = [format_ingredient(s, a) for s, a in guessed]
        row["ingredients"] = ingredients + "|" + "|".join(new_parts)
        updated_count += 1

        if dry_run:
            print(f"[{name}] + {', '.join(s for s, _ in guessed)}")

    print(f"\n更新対象: {updated_count}件")

    if not dry_run:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"保存しました: {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="dishes.csvに調味料を自動追加")
    parser.add_argument("--dry-run", action="store_true", help="実際には書き込まず、追加内容を表示")
    parser.add_argument("-i", "--input", default="data/dishes.csv", help="入力ファイル")
    parser.add_argument("-o", "--output", default="data/dishes.csv", help="出力ファイル")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output

    if not input_path.exists():
        print(f"ファイルが見つかりません: {input_path}")
        sys.exit(1)

    process_dishes(input_path, output_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
