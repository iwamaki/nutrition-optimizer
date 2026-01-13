#!/usr/bin/env python3
"""
LLMの出力をrecipe_details.jsonに追記するツール

使用例:
  # クリップボードから（pbpaste/xclip）
  pbpaste | python tools/add_recipe_detail.py

  # ファイルから
  python tools/add_recipe_detail.py < output.json

  # 直接入力（Ctrl+Dで終了）
  python tools/add_recipe_detail.py
  {"焼き鮭": {"prep_time": 5, ...}}
  ^D
"""

import json
import sys
import re
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"
RECIPE_DETAILS_JSON = DATA_DIR / "recipe_details.json"


def extract_json_from_text(text: str) -> str:
    """テキストからJSONブロックを抽出"""
    # ```json ... ``` ブロックを探す
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # { で始まる行を探す
    lines = text.strip().split('\n')
    json_lines = []
    in_json = False
    brace_count = 0

    for line in lines:
        if not in_json and line.strip().startswith('{'):
            in_json = True

        if in_json:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0:
                break

    if json_lines:
        return '\n'.join(json_lines)

    return text.strip()


def load_existing() -> dict:
    """既存のrecipe_details.jsonを読み込む"""
    if not RECIPE_DETAILS_JSON.exists():
        return {"_schema": {
            "description": "レシピ詳細データ",
            "fields": {
                "prep_time": "下準備時間（分）",
                "cook_time": "調理時間（分）",
                "servings": "基準人数",
                "steps": "調理手順（配列）",
                "tips": "コツ・ポイント（任意）"
            }
        }}

    with open(RECIPE_DETAILS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict):
    """recipe_details.jsonに保存"""
    with open(RECIPE_DETAILS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def validate_recipe(name: str, recipe: dict) -> list[str]:
    """レシピデータのバリデーション"""
    errors = []

    if not isinstance(recipe, dict):
        errors.append(f"'{name}': データが辞書形式ではありません")
        return errors

    # 必須フィールドチェック
    if "steps" not in recipe or not recipe["steps"]:
        errors.append(f"'{name}': stepsが必要です")
    elif not isinstance(recipe["steps"], list):
        errors.append(f"'{name}': stepsは配列である必要があります")

    # 型チェック
    if "prep_time" in recipe and not isinstance(recipe["prep_time"], (int, float)):
        errors.append(f"'{name}': prep_timeは数値である必要があります")

    if "cook_time" in recipe and not isinstance(recipe["cook_time"], (int, float)):
        errors.append(f"'{name}': cook_timeは数値である必要があります")

    return errors


def main():
    # 標準入力から読み込み
    print("JSONを入力してください（Ctrl+Dで終了）:", file=sys.stderr)

    try:
        input_text = sys.stdin.read()
    except KeyboardInterrupt:
        print("\nキャンセルしました", file=sys.stderr)
        return

    if not input_text.strip():
        print("エラー: 入力が空です", file=sys.stderr)
        sys.exit(1)

    # JSONを抽出
    json_text = extract_json_from_text(input_text)

    try:
        new_data = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"エラー: JSONのパースに失敗しました", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print(f"\n抽出されたテキスト:\n{json_text[:500]}...", file=sys.stderr)
        sys.exit(1)

    if not isinstance(new_data, dict):
        print("エラー: JSONはオブジェクト形式である必要があります", file=sys.stderr)
        sys.exit(1)

    # バリデーション
    all_errors = []
    for name, recipe in new_data.items():
        if name.startswith("_"):
            continue
        errors = validate_recipe(name, recipe)
        all_errors.extend(errors)

    if all_errors:
        print("エラー: バリデーションに失敗しました", file=sys.stderr)
        for err in all_errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    # 既存データを読み込み
    existing = load_existing()

    # マージ
    added = []
    updated = []
    for name, recipe in new_data.items():
        if name.startswith("_"):
            continue
        if name in existing:
            updated.append(name)
        else:
            added.append(name)
        existing[name] = recipe

    # 保存
    save_data(existing)

    # 結果表示
    recipe_count = len([k for k in existing.keys() if not k.startswith("_")])
    print(f"\n✓ 保存しました: {RECIPE_DETAILS_JSON}")
    print(f"  追加: {len(added)}件 {added if added else ''}")
    if updated:
        print(f"  更新: {len(updated)}件 {updated}")
    print(f"  合計: {recipe_count}件")


if __name__ == "__main__":
    main()
