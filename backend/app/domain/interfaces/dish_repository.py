"""Dish repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.dish import Dish
from app.domain.entities.enums import DishCategoryEnum, MealTypeEnum


class DishRepositoryInterface(ABC):
    """料理リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, dish_id: int) -> Optional[Dish]:
        """IDで料理を取得"""
        pass

    @abstractmethod
    def find_all(
        self,
        category: Optional[DishCategoryEnum] = None,
        meal_type: Optional[MealTypeEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Dish]:
        """
        料理一覧を取得

        Args:
            category: カテゴリでフィルタ
            meal_type: 食事タイプでフィルタ
            skip: オフセット
            limit: 取得件数
        """
        pass

    @abstractmethod
    def find_by_ids(self, dish_ids: list[int]) -> list[Dish]:
        """複数IDで料理を取得"""
        pass

    @abstractmethod
    def find_excluding_allergens(self, allergens: list[str]) -> list[Dish]:
        """指定アレルゲンを含まない料理を取得"""
        pass

    @abstractmethod
    def count(
        self,
        category: Optional[DishCategoryEnum] = None,
        meal_type: Optional[MealTypeEnum] = None,
    ) -> int:
        """料理数をカウント"""
        pass

    @abstractmethod
    def get_categories(self) -> list[str]:
        """利用可能なカテゴリ一覧を取得"""
        pass
