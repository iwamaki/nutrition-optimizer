"""
設定関連APIエンドポイント

クリーンアーキテクチャ: presentation層
"""
from fastapi import APIRouter

from app.domain.entities import NutrientTarget, AllergenEnum
from app.models.schemas import UserPreferences

router = APIRouter(tags=["preferences"])

# インメモリのユーザー設定（後方互換用）
_user_preferences = UserPreferences()


@router.get("/nutrients/target", response_model=NutrientTarget)
def get_nutrient_target():
    """栄養素目標値を取得（デフォルト値）"""
    return NutrientTarget()


@router.get("/allergens")
def get_allergens():
    """アレルゲン一覧を取得（7大アレルゲン）"""
    return [{"value": a.value, "name": a.name} for a in AllergenEnum]


@router.get("/preferences", response_model=UserPreferences)
def get_preferences():
    """ユーザー設定を取得"""
    return _user_preferences


@router.put("/preferences", response_model=UserPreferences)
def update_preferences(prefs: UserPreferences):
    """ユーザー設定を更新"""
    global _user_preferences
    _user_preferences = prefs
    return _user_preferences
