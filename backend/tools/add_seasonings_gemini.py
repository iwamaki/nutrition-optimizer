#!/usr/bin/env python3
"""
Gemini APIを使ってdishes.csvに調味料を追加するスクリプト

1行ずつ料理情報を渡し、必要な調味料とg数を推定してもらう。
"""

import csv
import json
import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeai がインストールされていません")
    print("pip install google-generativeai")
    sys.exit(1)

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
    "ポン酢": 148,
    "オイスターソース": 149,
    "豆板醤": 150,
    "コンソメ": 151,
    "バター": 123,  # 乳類カテゴリだが調味料としても使用
}

# 食材ID→名前マッピング（主要なもの）
INGREDIENT_NAMES = {}


def load_ingredient_names(path: Path):
    """app_ingredients.csvから食材名をロード"""
    global INGREDIENT_NAMES
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            INGREDIENT_NAMES[int(row["id"])] = row["name"]


def parse_ingredients(ingredients_str: str) -> list[str]:
    """ingredients文字列を食材名リストに変換"""
    names = []
    for part in ingredients_str.split("|"):
        if not part:
            continue
        food_id = int(part.split(":")[0])
        if food_id in INGREDIENT_NAMES:
            names.append(INGREDIENT_NAMES[food_id])
    return names


def build_prompt_batch(dishes: list[dict]) -> str:
    """複数料理の調味料推定用プロンプトを構築"""
    dishes_text = ""
    for i, d in enumerate(dishes, 1):
        ingredients_text = "、".join(d["ingredient_names"]) if d["ingredient_names"] else "なし"
        dishes_text += f"""
{i}. {d["name"]}
   - カテゴリ: {d["category"]}
   - 風味: {d["flavor"]}
   - 食材: {ingredients_text}
   - 調理: {d["instructions"]}
"""

    return f"""あなたは20年のキャリアを持つ和食・洋食・中華すべてに精通した料理人です。
家庭で美味しく作れる、実践的な調味料の分量を教えてください。

【料理一覧】
{dishes_text}
【使用可能な調味料】
醤油, みりん, 砂糖, 塩, 酢, サラダ油, マヨネーズ, ケチャップ, ソース, 料理酒, ごま油, オリーブ油, こしょう, めんつゆ, ポン酢, オイスターソース, 豆板醤, コンソメ, バター

【分量の考え方】
- 1人前の分量で回答
- 照り焼きや生姜焼きのタレは、しっかり絡む量（醤油・みりん各大さじ1〜1.5程度）
- 煮物の煮汁は、具材が浸る程度
- 炒め物の油は、フライパン全体に回る量
- 下味の酒は、肉や魚に馴染む量（大さじ1程度）
- 塩・こしょうの「少々」は控えめでOK

【ルール】
- 調味料が不要な料理（フルーツ、白ごはん等）は空配列
- 味噌汁の味噌、カレールウは食材に含まれるので不要
- 分量は「大さじ1」「小さじ2」「少々」の形式

【出力形式】
JSON形式のみ。説明不要。
```json
{{
  "料理名1": [{{"name": "調味料名", "amount": "大さじ1"}}, ...],
  "料理名2": [],
  ...
}}
```"""


def extract_json_dict(text: str) -> dict:
    """レスポンスからJSON（オブジェクト形式）を抽出"""
    import re

    # ```json ... ``` を探す
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
    else:
        # { ... } を探す
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_text = match.group(0)
        else:
            return {}

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return {}


# 調味料ごとの大さじ・小さじのグラム数
SEASONING_GRAMS = {
    # (大さじ1のg, 小さじ1のg)
    "醤油": (18, 6),
    "みりん": (18, 6),
    "砂糖": (9, 3),
    "塩": (18, 6),
    "酢": (15, 5),
    "サラダ油": (12, 4),
    "マヨネーズ": (12, 4),
    "ケチャップ": (15, 5),
    "ソース": (15, 5),
    "料理酒": (15, 5),
    "ごま油": (12, 4),
    "オリーブ油": (12, 4),
    "こしょう": (6, 2),  # 実際は少々=0.1g程度
    "めんつゆ": (15, 5),
    "ポン酢": (15, 5),
    "オイスターソース": (18, 6),
    "豆板醤": (18, 6),
    "コンソメ": (9, 3),  # 固形1個約5g
    "バター": (12, 4),
}


def parse_amount_to_grams(name: str, amount_str: str) -> float:
    """「大さじ1」「小さじ2」などをグラムに変換"""
    import re

    if name not in SEASONING_GRAMS:
        return 0

    tbsp_g, tsp_g = SEASONING_GRAMS[name]

    # 少々
    if "少々" in amount_str:
        if name == "こしょう":
            return 0.1
        elif name == "塩":
            return 1
        else:
            return tsp_g / 2  # 小さじ半分程度

    # 大さじ
    match = re.search(r'大さじ\s*(\d+(?:\.\d+)?)', amount_str)
    if match:
        return float(match.group(1)) * tbsp_g

    # 小さじ
    match = re.search(r'小さじ\s*(\d+(?:\.\d+)?)', amount_str)
    if match:
        return float(match.group(1)) * tsp_g

    # 数字だけ（グラムとして扱う）
    match = re.search(r'(\d+(?:\.\d+)?)\s*g?', amount_str)
    if match:
        return float(match.group(1))

    return 0


def format_seasonings(seasonings: list[dict]) -> str:
    """調味料リストをingredients形式に変換"""
    parts = []
    for s in seasonings:
        name = s.get("name", "")
        amount_str = s.get("amount", "")

        if name not in SEASONINGS:
            continue

        # 大さじ/小さじをグラムに変換
        if isinstance(amount_str, str):
            amount = parse_amount_to_grams(name, amount_str)
        else:
            amount = float(amount_str) if amount_str else 0

        if amount > 0:
            parts.append(f"{SEASONINGS[name]}:{amount}:生")

    return "|".join(parts)


def process_dishes(
    input_path: Path,
    output_path: Path,
    dry_run: bool = False,
    limit: int = 0,
    skip_existing: bool = True,
    batch_size: int = 3,
):
    """dishes.csvを処理して調味料を追加（バッチ処理）"""

    model = None
    if not dry_run:
        # Gemini初期化
        api_key = settings.gemini_api_key
        if not api_key:
            print("GEMINI_API_KEY が設定されていません")
            sys.exit(1)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3-flash-preview")

    # 食材名をロード
    ingredients_path = input_path.parent / "app_ingredients.csv"
    load_ingredient_names(ingredients_path)

    # CSVを読み込む
    rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    seasoning_ids = set(SEASONINGS.values())
    updated_count = 0
    processed_count = 0

    # 処理対象を収集
    targets = []
    for i, row in enumerate(rows):
        ingredients_str = row["ingredients"]
        existing_ids = {int(ing.split(":")[0]) for ing in ingredients_str.split("|") if ing}
        if skip_existing and (existing_ids & seasoning_ids):
            continue
        targets.append((i, row))

    if limit:
        targets = targets[:limit]

    total_batches = (len(targets) + batch_size - 1) // batch_size
    print(f"対象: {len(targets)}件 (バッチサイズ: {batch_size}, 全{total_batches}バッチ)", flush=True)

    # バッチ処理
    for batch_idx, batch_start in enumerate(range(0, len(targets), batch_size)):
        batch = targets[batch_start:batch_start + batch_size]

        # バッチ用データを準備
        batch_data = []
        for idx, row in batch:
            batch_data.append({
                "idx": idx,
                "row": row,
                "name": row["name"],
                "category": row["category"],
                "flavor": row["flavor_profile"],
                "instructions": row.get("instructions", ""),
                "ingredient_names": parse_ingredients(row["ingredients"]),
            })

        if dry_run:
            for d in batch_data:
                print(f"[{d['idx']+1}] {d['name']}", flush=True)
                print(f"    食材: {', '.join(d['ingredient_names'])}", flush=True)
            processed_count += len(batch_data)
            continue

        # プロンプト構築
        prompt = build_prompt_batch(batch_data)

        # 進捗表示
        pct = (batch_idx + 1) * 100 // total_batches
        print(f"\n[バッチ {batch_idx+1}/{total_batches}] ({pct}%) 処理中...", flush=True)

        # Gemini API呼び出し
        try:
            response = model.generate_content(prompt)
            if not response.text:
                print(f"バッチ {batch_idx+1}: 空のレスポンス", flush=True)
                continue

            results = extract_json_dict(response.text)

            for d in batch_data:
                name = d["name"]
                row = d["row"]
                seasonings = results.get(name, [])

                if not seasonings:
                    print(f"  [{d['idx']+1}] {name}: 調味料なし", flush=True)
                else:
                    seasonings_str = format_seasonings(seasonings)
                    if seasonings_str:
                        row["ingredients"] = row["ingredients"] + "|" + seasonings_str
                        updated_count += 1
                        seasoning_names = [s["name"] for s in seasonings if s.get("name") in SEASONINGS]
                        print(f"  [{d['idx']+1}] {name}: + {', '.join(seasoning_names)}", flush=True)
                    else:
                        print(f"  [{d['idx']+1}] {name}: 調味料なし", flush=True)

            processed_count += len(batch_data)

            # レート制限対策
            time.sleep(1)

        except Exception as e:
            print(f"バッチ {batch_idx+1}: エラー - {e}", flush=True)
            time.sleep(2)

    print(f"\n処理: {processed_count}件, 更新: {updated_count}件", flush=True)

    if not dry_run and updated_count > 0:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"保存しました: {output_path}", flush=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Geminiで調味料を推定してdishes.csvに追加")
    parser.add_argument("--dry-run", action="store_true", help="API呼び出しせず対象を表示")
    parser.add_argument("-i", "--input", default="data/dishes.csv", help="入力ファイル")
    parser.add_argument("-o", "--output", default="data/dishes.csv", help="出力ファイル")
    parser.add_argument("-n", "--limit", type=int, default=0, help="処理件数の上限（0=無制限）")
    parser.add_argument("--include-existing", action="store_true", help="既存調味料ありも再処理")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output

    if not input_path.exists():
        print(f"ファイルが見つかりません: {input_path}")
        sys.exit(1)

    process_dishes(
        input_path,
        output_path,
        dry_run=args.dry_run,
        limit=args.limit,
        skip_existing=not args.include_existing,
    )


if __name__ == "__main__":
    main()
