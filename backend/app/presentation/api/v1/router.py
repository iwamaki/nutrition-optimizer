"""
API v1 メインルーター

クリーンアーキテクチャ: presentation層
全サブルーターを集約
"""
from fastapi import APIRouter

from app.presentation.api.v1.ingredients import router as ingredients_router
from app.presentation.api.v1.dishes import router as dishes_router
from app.presentation.api.v1.optimize import router as optimize_router
from app.presentation.api.v1.preferences import router as preferences_router
from app.presentation.api.v1.health import router as health_router

# メインルーター
router = APIRouter()

# サブルーターを登録
router.include_router(ingredients_router)
router.include_router(dishes_router)
router.include_router(optimize_router)
router.include_router(preferences_router)
router.include_router(health_router)
