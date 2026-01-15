"""External service integrations."""

from app.infrastructure.external.gemini_recipe_generator import (
    GeminiRecipeGenerator,
    get_recipe_generator,
    # 後方互換性関数
    init_gemini,
    generate_recipe_detail,
    get_or_generate_recipe_detail,
)

__all__ = [
    "GeminiRecipeGenerator",
    "get_recipe_generator",
    "init_gemini",
    "generate_recipe_detail",
    "get_or_generate_recipe_detail",
]
