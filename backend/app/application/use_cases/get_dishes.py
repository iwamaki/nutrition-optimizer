"""
料理取得ユースケース

クリーンアーキテクチャ: application層
"""
from dataclasses import dataclass
from typing import Optional

from app.domain.entities import Dish
from app.domain.interfaces import DishRepositoryInterface
from app.core.exceptions import EntityNotFoundError


@dataclass
class GetDishesUseCase:
    """料理一覧を取得するユースケース"""

    dish_repo: DishRepositoryInterface

    def execute(
        self,
        category: Optional[str] = None,
        meal_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Dish]:
        """料理一覧を取得

        Args:
            category: カテゴリでフィルタ
            meal_type: 食事タイプでフィルタ
            skip: スキップ数
            limit: 取得数上限

        Returns:
            料理リスト
        """
        return self.dish_repo.find_all(
            category=category,
            meal_type=meal_type,
            skip=skip,
            limit=limit,
        )

    def count(
        self,
        category: Optional[str] = None,
        meal_type: Optional[str] = None,
    ) -> int:
        """料理数をカウント"""
        return self.dish_repo.count(category=category, meal_type=meal_type)

    def get_categories(self) -> list[str]:
        """カテゴリ一覧を取得"""
        return self.dish_repo.get_categories()


@dataclass
class GetDishByIdUseCase:
    """IDで料理を取得するユースケース"""

    dish_repo: DishRepositoryInterface

    def execute(self, dish_id: int) -> Dish:
        """IDで料理を取得

        Args:
            dish_id: 料理ID

        Returns:
            料理

        Raises:
            EntityNotFoundError: 料理が見つからない場合
        """
        dish = self.dish_repo.find_by_id(dish_id)
        if not dish:
            raise EntityNotFoundError("Dish", dish_id)
        return dish


@dataclass
class GetDishesByIdsUseCase:
    """複数IDで料理を取得するユースケース"""

    dish_repo: DishRepositoryInterface

    def execute(self, dish_ids: list[int]) -> list[Dish]:
        """複数IDで料理を取得

        Args:
            dish_ids: 料理IDリスト

        Returns:
            料理リスト
        """
        return self.dish_repo.find_by_ids(dish_ids)
