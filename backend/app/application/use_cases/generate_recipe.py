"""
レシピ生成ユースケース

クリーンアーキテクチャ: application層
"""
from dataclasses import dataclass
from typing import Optional

from app.domain.entities import RecipeDetails
from app.domain.interfaces import DishRepositoryInterface
from app.infrastructure.external import GeminiRecipeGenerator
from app.core.exceptions import EntityNotFoundError, ExternalServiceError


@dataclass
class GenerateRecipeUseCase:
    """料理のレシピ詳細を生成するユースケース"""

    dish_repo: DishRepositoryInterface
    recipe_generator: GeminiRecipeGenerator

    def execute(
        self,
        dish_id: int,
        force: bool = False,
    ) -> Optional[RecipeDetails]:
        """料理のレシピ詳細を生成

        Args:
            dish_id: 料理ID
            force: 既存データがあっても再生成するか

        Returns:
            生成されたレシピ詳細

        Raises:
            EntityNotFoundError: 料理が見つからない場合
            ExternalServiceError: Gemini API呼び出しに失敗した場合
        """
        # 料理を取得
        dish = self.dish_repo.find_by_id(dish_id)
        if not dish:
            raise EntityNotFoundError("Dish", dish_id)

        # 既存のレシピ詳細があれば返す（forceでない場合）
        if not force and dish.recipe_details:
            return dish.recipe_details

        # 材料リストを構築
        ingredients = [
            {"name": ing.food_name or "", "amount": ing.amount}
            for ing in dish.ingredients
        ]

        # レシピを生成
        recipe_data = self.recipe_generator.generate_recipe_detail(
            dish_name=dish.name,
            category=dish.category.value,
            ingredients=ingredients,
            hint=dish.description or "",
            save=True,
            force=force,
        )

        if not recipe_data:
            return None

        return RecipeDetails(**recipe_data)


@dataclass
class GetRecipeDetailUseCase:
    """料理のレシピ詳細を取得するユースケース"""

    dish_repo: DishRepositoryInterface
    recipe_generator: GeminiRecipeGenerator

    def execute(self, dish_id: int) -> Optional[RecipeDetails]:
        """料理のレシピ詳細を取得（生成しない）

        Args:
            dish_id: 料理ID

        Returns:
            レシピ詳細、存在しない場合はNone

        Raises:
            EntityNotFoundError: 料理が見つからない場合
        """
        dish = self.dish_repo.find_by_id(dish_id)
        if not dish:
            raise EntityNotFoundError("Dish", dish_id)

        # 既存のレシピ詳細を返す
        if dish.recipe_details:
            return dish.recipe_details

        # JSONファイルからも取得を試みる
        recipe_data = self.recipe_generator.get_recipe_detail(dish.name)
        if recipe_data:
            return RecipeDetails(**recipe_data)

        return None


@dataclass
class BatchGenerateRecipesUseCase:
    """複数料理のレシピを一括生成するユースケース"""

    dish_repo: DishRepositoryInterface
    recipe_generator: GeminiRecipeGenerator

    def execute(
        self,
        dish_ids: Optional[list[int]] = None,
        category: Optional[str] = None,
        force: bool = False,
    ) -> dict[int, Optional[RecipeDetails]]:
        """複数料理のレシピを一括生成

        Args:
            dish_ids: 対象料理ID（指定しない場合は全料理）
            category: カテゴリでフィルタ
            force: 既存データがあっても再生成するか

        Returns:
            料理ID -> RecipeDetails のマップ
        """
        if dish_ids:
            dishes = self.dish_repo.find_by_ids(dish_ids)
        else:
            dishes = self.dish_repo.find_all(category=category, limit=1000)

        results: dict[int, Optional[RecipeDetails]] = {}

        for dish in dishes:
            # 既存があり、forceでなければスキップ
            if not force and dish.recipe_details:
                results[dish.id] = dish.recipe_details
                continue

            # JSONからも確認
            existing = self.recipe_generator.get_recipe_detail(dish.name)
            if existing and not force:
                results[dish.id] = RecipeDetails(**existing)
                continue

            # 生成
            try:
                ingredients = [
                    {"name": ing.food_name or "", "amount": ing.amount}
                    for ing in dish.ingredients
                ]
                recipe_data = self.recipe_generator.generate_recipe_detail(
                    dish_name=dish.name,
                    category=dish.category.value,
                    ingredients=ingredients,
                    hint=dish.description or "",
                    save=True,
                    force=force,
                )
                if recipe_data:
                    results[dish.id] = RecipeDetails(**recipe_data)
                else:
                    results[dish.id] = None
            except ExternalServiceError:
                results[dish.id] = None

        return results
