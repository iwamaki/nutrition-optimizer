"""
Gemini APIを使用したレシピ詳細自動生成サービス

クリーンアーキテクチャ: infrastructure層（外部サービス）

環境変数:
  GEMINI_API_KEY: Google AI Studio APIキー
"""

import json
import re
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import ExternalServiceError

# Gemini SDKのインポート（インストールされていない場合はスキップ）
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

logger = get_logger(__name__)


class GeminiRecipeGenerator:
    """Gemini APIを使用したレシピ生成サービス"""

    MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, recipe_details_path: Optional[Path] = None):
        """
        Args:
            recipe_details_path: レシピ詳細JSONファイルのパス
        """
        self._initialized = False
        self._recipe_details: dict = {}

        # デフォルトパス
        if recipe_details_path is None:
            recipe_details_path = Path(__file__).parent.parent.parent.parent / "data" / "recipe_details.json"
        self._recipe_details_path = recipe_details_path

        # 既存データのロード
        self._load_recipe_details()

    def initialize(self) -> bool:
        """Gemini APIを初期化

        Returns:
            初期化成功かどうか
        """
        if not GEMINI_AVAILABLE:
            logger.warning("google-generativeai がインストールされていません")
            return False

        api_key = settings.gemini_api_key
        if not api_key:
            logger.warning("GEMINI_API_KEY が設定されていません")
            return False

        try:
            genai.configure(api_key=api_key)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Gemini API初期化エラー: {e}")
            return False

    @property
    def is_available(self) -> bool:
        """Gemini APIが利用可能かどうか"""
        return GEMINI_AVAILABLE and bool(settings.gemini_api_key)

    def generate_recipe_detail(
        self,
        dish_name: str,
        category: str,
        ingredients: list[dict],
        hint: str = "",
        save: bool = True,
        force: bool = False,
    ) -> Optional[dict]:
        """レシピ詳細を生成

        Args:
            dish_name: 料理名
            category: カテゴリ（主食/主菜/副菜/汁物/デザート）
            ingredients: 材料リスト [{"name": "...", "amount": "..."}]
            hint: 参考情報
            save: Trueの場合、生成結果をJSONに保存
            force: Trueの場合、既存データがあっても再生成

        Returns:
            生成されたレシピ詳細、失敗時はNone
        """
        # 既存チェック（forceでなければ）
        if not force and dish_name in self._recipe_details:
            return self._recipe_details[dish_name]

        if not self.is_available:
            logger.warning("Gemini APIが利用できません")
            return None

        # 初期化
        if not self._initialized:
            if not self.initialize():
                return None

        try:
            model = genai.GenerativeModel(self.MODEL_NAME)
            prompt = self._build_prompt(dish_name, category, ingredients, hint)
            response = model.generate_content(prompt)

            if not response.text:
                logger.warning(f"レシピ生成: 空のレスポンス ({dish_name})")
                return None

            result = self._extract_json_from_response(response.text)
            if not result:
                logger.warning(f"レシピ生成: JSON抽出失敗 ({dish_name})")
                return None

            # 料理名のキーでデータを取得
            recipe_data = result.get(dish_name)
            if not recipe_data:
                for key, value in result.items():
                    if not key.startswith("_"):
                        recipe_data = value
                        break

            if not recipe_data:
                logger.warning(f"レシピ生成: データ抽出失敗 ({dish_name})")
                return None

            # 保存
            if save:
                self._recipe_details[dish_name] = recipe_data
                self._save_recipe_details()

            return recipe_data

        except Exception as e:
            logger.error(f"レシピ生成エラー ({dish_name}): {e}")
            raise ExternalServiceError(
                service="Gemini API",
                message=f"レシピ生成に失敗しました: {dish_name}",
                details={"error": str(e)}
            )

    def get_recipe_detail(self, dish_name: str) -> Optional[dict]:
        """既存のレシピ詳細を取得

        Args:
            dish_name: 料理名

        Returns:
            レシピ詳細、存在しない場合はNone
        """
        return self._recipe_details.get(dish_name)

    def get_or_generate_recipe_detail(
        self,
        dish_name: str,
        category: str,
        ingredients: list[dict],
        hint: str = ""
    ) -> Optional[dict]:
        """レシピ詳細を取得、なければ生成

        Args:
            dish_name: 料理名
            category: カテゴリ
            ingredients: 材料リスト
            hint: 参考情報

        Returns:
            レシピ詳細
        """
        existing = self.get_recipe_detail(dish_name)
        if existing:
            return existing
        return self.generate_recipe_detail(dish_name, category, ingredients, hint)

    def _build_prompt(
        self,
        dish_name: str,
        category: str,
        ingredients: list[dict],
        hint: str = ""
    ) -> str:
        """レシピ生成用プロンプトを構築"""
        prompt = f"""以下の料理について、詳細なレシピをJSON形式で生成してください。

## 料理名
{dish_name}（{category}）

## 材料（1人前）
"""
        for ing in ingredients:
            simple_name = self._simplify_food_name(ing.get("name", ""))
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

    def _simplify_food_name(self, name: str) -> str:
        """食品名を簡略化"""
        parts = name.replace("＜", "").replace("＞", "").replace("［", "").replace("］", "")
        parts = parts.replace("（", " ").replace("）", " ")
        tokens = [t.strip() for t in parts.split() if t.strip()]
        if len(tokens) >= 2:
            if tokens[-1] in ["生", "焼き", "ゆで", "蒸す", "油いため"]:
                return f"{tokens[-2]}（{tokens[-1]}）"
            return tokens[-1]
        return tokens[-1] if tokens else name

    def _extract_json_from_response(self, text: str) -> Optional[dict]:
        """レスポンスからJSONを抽出"""
        # ```json ... ``` ブロックを探す
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
        else:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                json_text = match.group(0)
            else:
                return None

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return None

    def _load_recipe_details(self):
        """既存のrecipe_details.jsonを読み込む"""
        if not self._recipe_details_path.exists():
            self._recipe_details = {}
            return

        try:
            with open(self._recipe_details_path, "r", encoding="utf-8") as f:
                self._recipe_details = json.load(f)
        except Exception as e:
            logger.warning(f"レシピ詳細の読み込みに失敗: {e}")
            self._recipe_details = {}

    def _save_recipe_details(self):
        """recipe_details.jsonに保存"""
        try:
            with open(self._recipe_details_path, "w", encoding="utf-8") as f:
                json.dump(self._recipe_details, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"レシピ詳細の保存に失敗: {e}")


# シングルトンインスタンス（後方互換用）
_default_generator: Optional[GeminiRecipeGenerator] = None


def get_recipe_generator() -> GeminiRecipeGenerator:
    """デフォルトのレシピジェネレーターを取得"""
    global _default_generator
    if _default_generator is None:
        _default_generator = GeminiRecipeGenerator()
    return _default_generator


# 後方互換性のための関数（既存コードからの移行用）
def init_gemini() -> bool:
    """Gemini APIを初期化（後方互換）"""
    return get_recipe_generator().initialize()


def generate_recipe_detail(
    dish_name: str,
    category: str,
    ingredients: list[dict],
    hint: str = "",
    save: bool = True
) -> Optional[dict]:
    """レシピ詳細を生成（後方互換）"""
    return get_recipe_generator().generate_recipe_detail(
        dish_name, category, ingredients, hint, save
    )


def get_or_generate_recipe_detail(
    dish_name: str,
    category: str,
    ingredients: list[dict],
    hint: str = ""
) -> Optional[dict]:
    """レシピ詳細を取得・生成（後方互換）"""
    return get_recipe_generator().get_or_generate_recipe_detail(
        dish_name, category, ingredients, hint
    )
