"""Ingredient repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.ingredient import Ingredient


class IngredientRepositoryInterface(ABC):
    """基本食材リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, ingredient_id: int) -> Optional[Ingredient]:
        """IDで食材を取得"""
        pass

    @abstractmethod
    def find_all(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Ingredient]:
        """食材一覧を取得"""
        pass

    @abstractmethod
    def find_by_ids(self, ingredient_ids: list[int]) -> list[Ingredient]:
        """複数IDで食材を取得"""
        pass

    @abstractmethod
    def count(self, category: Optional[str] = None) -> int:
        """食材数をカウント"""
        pass

    @abstractmethod
    def get_categories(self) -> list[str]:
        """利用可能なカテゴリ一覧を取得"""
        pass
