"""Domain interfaces - Repository and service abstractions."""

from app.domain.interfaces.dish_repository import DishRepositoryInterface
from app.domain.interfaces.food_repository import FoodRepositoryInterface
from app.domain.interfaces.ingredient_repository import IngredientRepositoryInterface
from app.domain.interfaces.preference_repository import PreferenceRepositoryInterface

__all__ = [
    "DishRepositoryInterface",
    "FoodRepositoryInterface",
    "IngredientRepositoryInterface",
    "PreferenceRepositoryInterface",
]
