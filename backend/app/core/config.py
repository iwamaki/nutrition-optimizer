"""Application configuration management."""

import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Environment
        self.env: str = os.getenv("ENV", "development")
        self.debug: bool = self.env == "development"

        # Database
        self.database_url: str = os.getenv(
            "DATABASE_URL", "sqlite:///./nutrition.db"
        )

        # CORS
        self.allowed_origins: list[str] = self._parse_origins()

        # API
        self.api_v1_prefix: str = "/api/v1"

        # External Services
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")

        # Optimization
        self.solver_timeout: int = int(os.getenv("SOLVER_TIMEOUT", "30"))

        # Data files
        self.data_dir: str = os.getenv(
            "DATA_DIR",
            os.path.join(os.path.dirname(__file__), "..", "..", "data")
        )
        self.food_composition_file: str = "food_composition_2023.xlsx"
        self.dishes_file: str = "dishes.csv"
        self.ingredients_file: str = "app_ingredients.csv"
        self.recipe_details_file: str = "recipe_details.json"

    def _parse_origins(self) -> list[str]:
        """Parse CORS allowed origins from environment."""
        default_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ]

        env_origins = os.getenv("ALLOWED_ORIGINS", "")
        if env_origins:
            default_origins.extend(env_origins.split(","))

        # Allow all origins in development
        if self.env != "production":
            default_origins.append("*")

        return default_origins

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience accessor
settings = get_settings()
