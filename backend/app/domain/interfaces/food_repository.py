"""Food repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.food import Food


class FoodRepositoryInterface(ABC):
    """食品リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, food_id: int) -> Optional[Food]:
        """IDで食品を取得"""
        pass

    @abstractmethod
    def find_by_mext_code(self, mext_code: str) -> Optional[Food]:
        """文科省コードで食品を取得"""
        pass

    @abstractmethod
    def find_all(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Food]:
        """食品一覧を取得"""
        pass

    @abstractmethod
    def search(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> list[Food]:
        """キーワードで食品を検索"""
        pass

    @abstractmethod
    def count(self, category: Optional[str] = None) -> int:
        """食品数をカウント"""
        pass

    @abstractmethod
    def get_categories(self) -> list[str]:
        """利用可能なカテゴリ一覧を取得"""
        pass

    @abstractmethod
    def get_allergens_for_food(self, food_id: int) -> list[str]:
        """食品のアレルゲン情報を取得"""
        pass
