"""
食材取得ユースケース

クリーンアーキテクチャ: application層
"""
from dataclasses import dataclass
from typing import Optional

from app.domain.entities import Ingredient
from app.domain.interfaces import IngredientRepositoryInterface
from app.core.exceptions import EntityNotFoundError


@dataclass
class GetIngredientsUseCase:
    """食材一覧を取得するユースケース"""

    ingredient_repo: IngredientRepositoryInterface

    def execute(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Ingredient]:
        """食材一覧を取得

        Args:
            category: カテゴリでフィルタ
            skip: スキップ数
            limit: 取得数上限

        Returns:
            食材リスト
        """
        return self.ingredient_repo.find_all(
            category=category,
            skip=skip,
            limit=limit,
        )

    def count(self, category: Optional[str] = None) -> int:
        """食材数をカウント"""
        return self.ingredient_repo.count(category=category)

    def get_categories(self) -> list[str]:
        """カテゴリ一覧を取得"""
        return self.ingredient_repo.get_categories()


@dataclass
class GetIngredientByIdUseCase:
    """IDで食材を取得するユースケース"""

    ingredient_repo: IngredientRepositoryInterface

    def execute(self, ingredient_id: int) -> Ingredient:
        """IDで食材を取得

        Args:
            ingredient_id: 食材ID

        Returns:
            食材

        Raises:
            EntityNotFoundError: 食材が見つからない場合
        """
        ingredient = self.ingredient_repo.find_by_id(ingredient_id)
        if not ingredient:
            raise EntityNotFoundError("Ingredient", ingredient_id)
        return ingredient


@dataclass
class GetIngredientsByIdsUseCase:
    """複数IDで食材を取得するユースケース"""

    ingredient_repo: IngredientRepositoryInterface

    def execute(self, ingredient_ids: list[int]) -> list[Ingredient]:
        """複数IDで食材を取得

        Args:
            ingredient_ids: 食材IDリスト

        Returns:
            食材リスト
        """
        return self.ingredient_repo.find_by_ids(ingredient_ids)
