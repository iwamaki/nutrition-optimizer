"""
Gemini APIを使用したレシピ詳細自動生成サービス

環境変数:
  GEMINI_API_KEY: Google AI Studio APIキー
"""

import os
import json
import re
from pathlib import Path
from typing import Optional

# Gemini SDKのインポート（インストールされていない場合はスキップ）
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


# 設定
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RECIPE_DETAILS_JSON = DATA_DIR / "recipe_details.json"
MODEL_NAME = "gemini-2.5-flash"


def init_gemini() -> bool:
    """Gemini APIを初期化"""
    if not GEMINI_AVAILABLE:
        print("警告: google-generativeai がインストールされていません")
        return False

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("警告: GEMINI_API_KEY が設定されていません")
        return False

    genai.configure(api_key=api_key)
    return True


def simplify_food_name(name: str) -> str:
    """食品名を簡略化"""
    parts = name.replace("＜", "").replace("＞", "").replace("［", "").replace("］", "")
    parts = parts.replace("（", " ").replace("）", " ")
    tokens = [t.strip() for t in parts.split() if t.strip()]
    if len(tokens) >= 2:
        if tokens[-1] in ["生", "焼き", "ゆで", "蒸す", "油いため"]:
            return f"{tokens[-2]}（{tokens[-1]}）"
        return tokens[-1]
    return tokens[-1] if tokens else name


def build_prompt(dish_name: str, category: str, ingredients: list[dict], hint: str = "") -> str:
    """レシピ生成用プロンプトを構築"""
    prompt = f"""以下の料理について、詳細なレシピをJSON形式で生成してください。

## 料理名
{dish_name}（{category}）

## 材料（1人前）
"""
    for ing in ingredients:
        simple_name = simplify_food_name(ing.get("name", ""))
        amount = ing.get("amount", "")
        prompt += f"- {simple_name}: {amount}g\n"

    if hint:
        prompt += f"\n## 参考\n{hint}\n"

    prompt += f"""
## 出力フォーマット
以下のJSON形式のみを出力してください。説明文は不要です。

```json
{{
  "{dish_name}": {{
    "prep_time": 下準備時間（分・整数）,
    "cook_time": 調理時間（分・整数）,
    "servings": 1,
    "steps": [
      "手順1",
      "手順2"
    ],
    "tips": "コツ・ポイント"
  }}
}}
```

## 注意事項
- 手順は具体的に、初心者でもわかるように
- 火加減（強火/中火/弱火）や時間の目安を含める
- 材料の下処理も手順に含める
- 5〜8ステップ程度で簡潔に
"""
    return prompt


def extract_json_from_response(text: str) -> Optional[dict]:
    """レスポンスからJSONを抽出"""
    # ```json ... ``` ブロックを探す
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
    else:
        # { で始まる部分を探す
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_text = match.group(0)
        else:
            return None

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return None


def load_recipe_details() -> dict:
    """既存のrecipe_details.jsonを読み込む"""
    if not RECIPE_DETAILS_JSON.exists():
        return {}
    with open(RECIPE_DETAILS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_recipe_details(data: dict):
    """recipe_details.jsonに保存"""
    with open(RECIPE_DETAILS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_recipe_detail(
    dish_name: str,
    category: str,
    ingredients: list[dict],
    hint: str = "",
    save: bool = True
) -> Optional[dict]:
    """
    Gemini APIでレシピ詳細を生成

    Args:
        dish_name: 料理名
        category: カテゴリ（主食/主菜/副菜/汁物/デザート）
        ingredients: 材料リスト [{"name": "...", "amount": "..."}]
        hint: 参考情報（現在の簡易説明）
        save: Trueの場合、生成結果をJSONに保存

    Returns:
        生成されたレシピ詳細（dict）、失敗時はNone
    """
    if not GEMINI_AVAILABLE:
        return None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    # 既に存在する場合はスキップ
    existing = load_recipe_details()
    if dish_name in existing and not dish_name.startswith("_"):
        return existing[dish_name]

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL_NAME)

        prompt = build_prompt(dish_name, category, ingredients, hint)
        response = model.generate_content(prompt)

        if not response.text:
            return None

        result = extract_json_from_response(response.text)
        if not result:
            return None

        # 料理名のキーでデータを取得
        recipe_data = result.get(dish_name)
        if not recipe_data:
            # 最初のキーを使用
            for key, value in result.items():
                if not key.startswith("_"):
                    recipe_data = value
                    break

        if not recipe_data:
            return None

        # 保存
        if save:
            existing[dish_name] = recipe_data
            save_recipe_details(existing)

        return recipe_data

    except Exception as e:
        print(f"レシピ生成エラー ({dish_name}): {e}")
        return None


def get_or_generate_recipe_detail(
    dish_name: str,
    category: str,
    ingredients: list[dict],
    hint: str = ""
) -> Optional[dict]:
    """
    レシピ詳細を取得、なければ生成

    Args:
        dish_name: 料理名
        category: カテゴリ
        ingredients: 材料リスト
        hint: 参考情報

    Returns:
        レシピ詳細（dict）
    """
    # 既存データをチェック
    existing = load_recipe_details()
    if dish_name in existing:
        return existing[dish_name]

    # 生成
    return generate_recipe_detail(dish_name, category, ingredients, hint)
