"""Domain entities."""

from app.domain.entities.enums import (
    AllergenEnum,
    VolumeLevelEnum,
    VarietyLevelEnum,
    BatchCookingLevelEnum,
    MealTypeEnum,
    DishCategoryEnum,
    CookingMethodEnum,
    MealPresetEnum,
)
from app.domain.entities.food import (
    Food,
    FoodPortion,
    NutrientTarget,
)
from app.domain.entities.ingredient import Ingredient
from app.domain.entities.dish import (
    Dish,
    DishBase,
    DishIngredient,
    DishPortion,
    RecipeDetails,
    CookingFactor,
)
from app.domain.entities.meal_plan import (
    MealPlan,
    DailyMenuPlan,
    DailyMealAssignment,
    MultiDayMenuPlan,
    NutrientWarning,
)
from app.domain.entities.user_preference import UserPreferences
from app.domain.entities.shopping import ShoppingItem, CookingTask

__all__ = [
    # Enums
    "AllergenEnum",
    "VolumeLevelEnum",
    "VarietyLevelEnum",
    "BatchCookingLevelEnum",
    "MealTypeEnum",
    "DishCategoryEnum",
    "CookingMethodEnum",
    "MealPresetEnum",
    # Food
    "Food",
    "FoodPortion",
    "NutrientTarget",
    "Ingredient",
    # Dish
    "Dish",
    "DishBase",
    "DishIngredient",
    "DishPortion",
    "RecipeDetails",
    "CookingFactor",
    # Meal Plan
    "MealPlan",
    "DailyMenuPlan",
    "DailyMealAssignment",
    "MultiDayMenuPlan",
    "NutrientWarning",
    # User
    "UserPreferences",
    # Shopping
    "ShoppingItem",
    "CookingTask",
]
