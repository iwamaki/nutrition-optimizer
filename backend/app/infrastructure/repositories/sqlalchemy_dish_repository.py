"""SQLAlchemy implementation of DishRepository."""

from typing import Optional
from sqlalchemy.orm import Session

from app.domain.entities.dish import Dish, DishIngredient, RecipeDetails
from app.domain.entities.enums import DishCategoryEnum, MealTypeEnum, CookingMethodEnum
from app.domain.interfaces.dish_repository import DishRepositoryInterface
from app.infrastructure.database.models import DishDB, FoodAllergenDB
from app.data.loader import get_recipe_details


class SQLAlchemyDishRepository(DishRepositoryInterface):
    """SQLAlchemy implementation of dish repository."""

    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, dish_id: int) -> Optional[Dish]:
        """IDで料理を取得"""
        db_dish = self._session.query(DishDB).filter(DishDB.id == dish_id).first()
        return self._to_entity(db_dish) if db_dish else None

    def find_all(
        self,
        category: Optional[DishCategoryEnum] = None,
        meal_type: Optional[MealTypeEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Dish]:
        """料理一覧を取得"""
        query = self._session.query(DishDB)

        if category:
            query = query.filter(DishDB.category == category.value)
        if meal_type:
            query = query.filter(DishDB.meal_types.contains(meal_type.value))

        db_dishes = query.offset(skip).limit(limit).all()
        return [self._to_entity(d) for d in db_dishes]

    def find_by_ids(self, dish_ids: list[int]) -> list[Dish]:
        """複数IDで料理を取得"""
        if not dish_ids:
            return []
        db_dishes = self._session.query(DishDB).filter(DishDB.id.in_(dish_ids)).all()
        return [self._to_entity(d) for d in db_dishes]

    def find_excluding_allergens(self, allergens: list[str]) -> list[Dish]:
        """指定アレルゲンを含まない料理を取得"""
        if not allergens:
            return self.find_all()

        # アレルゲンを含む食品IDを取得
        allergen_food_ids = (
            self._session.query(FoodAllergenDB.food_id)
            .filter(FoodAllergenDB.allergen.in_(allergens))
            .distinct()
            .all()
        )
        allergen_food_id_set = {fid[0] for fid in allergen_food_ids}

        # 全料理を取得してフィルタリング
        all_dishes = self._session.query(DishDB).all()
        filtered_dishes = []

        for dish_db in all_dishes:
            # 料理の材料にアレルゲン食品が含まれているかチェック
            has_allergen = any(
                ing.food_id in allergen_food_id_set
                for ing in dish_db.ingredients
            )
            if not has_allergen:
                filtered_dishes.append(self._to_entity(dish_db))

        return filtered_dishes

    def count(
        self,
        category: Optional[DishCategoryEnum] = None,
        meal_type: Optional[MealTypeEnum] = None,
    ) -> int:
        """料理数をカウント"""
        query = self._session.query(DishDB)

        if category:
            query = query.filter(DishDB.category == category.value)
        if meal_type:
            query = query.filter(DishDB.meal_types.contains(meal_type.value))

        return query.count()

    def get_categories(self) -> list[str]:
        """利用可能なカテゴリ一覧を取得"""
        categories = (
            self._session.query(DishDB.category)
            .distinct()
            .all()
        )
        return [c[0] for c in categories if c[0]]

    def _to_entity(self, db_dish: DishDB) -> Dish:
        """DBモデルをドメインエンティティに変換"""
        # 食事タイプを解析
        meal_types = []
        if db_dish.meal_types:
            for mt in db_dish.meal_types.split(","):
                mt = mt.strip()
                try:
                    meal_types.append(MealTypeEnum(mt))
                except ValueError:
                    pass

        # カテゴリを解析
        try:
            category = DishCategoryEnum(db_dish.category)
        except ValueError:
            category = DishCategoryEnum.MAIN

        # 材料を変換
        ingredients = []
        for ing_db in db_dish.ingredients:
            cooking_method = CookingMethodEnum.RAW
            if ing_db.cooking_method:
                try:
                    cooking_method = CookingMethodEnum(ing_db.cooking_method)
                except ValueError:
                    pass

            ingredients.append(
                DishIngredient(
                    food_id=ing_db.food_id,
                    food_name=ing_db.food.name if ing_db.food else None,
                    ingredient_id=ing_db.ingredient_id,
                    ingredient_name=ing_db.ingredient.name if ing_db.ingredient else None,
                    amount=ing_db.amount,
                    cooking_method=cooking_method,
                )
            )

        # レシピ詳細を取得
        recipe_details = None
        recipe_data = get_recipe_details(db_dish.name)
        if recipe_data:
            recipe_details = RecipeDetails(**recipe_data)

        return Dish(
            id=db_dish.id,
            name=db_dish.name,
            category=category,
            meal_types=meal_types,
            serving_size=db_dish.serving_size or 1.0,
            description=db_dish.description,
            instructions=db_dish.instructions,
            ingredients=ingredients,
            storage_days=db_dish.storage_days or 1,
            min_servings=db_dish.min_servings or 1,
            max_servings=db_dish.max_servings or 4,
            calories=db_dish.calories or 0,
            protein=db_dish.protein or 0,
            fat=db_dish.fat or 0,
            carbohydrate=db_dish.carbohydrate or 0,
            fiber=db_dish.fiber or 0,
            sodium=db_dish.sodium or 0,
            potassium=db_dish.potassium or 0,
            calcium=db_dish.calcium or 0,
            magnesium=db_dish.magnesium or 0,
            iron=db_dish.iron or 0,
            zinc=db_dish.zinc or 0,
            vitamin_a=db_dish.vitamin_a or 0,
            vitamin_d=db_dish.vitamin_d or 0,
            vitamin_e=db_dish.vitamin_e or 0,
            vitamin_k=db_dish.vitamin_k or 0,
            vitamin_b1=db_dish.vitamin_b1 or 0,
            vitamin_b2=db_dish.vitamin_b2 or 0,
            vitamin_b6=db_dish.vitamin_b6 or 0,
            vitamin_b12=db_dish.vitamin_b12 or 0,
            niacin=db_dish.niacin or 0,
            pantothenic_acid=db_dish.pantothenic_acid or 0,
            biotin=db_dish.biotin or 0,
            folate=db_dish.folate or 0,
            vitamin_c=db_dish.vitamin_c or 0,
            recipe_details=recipe_details,
        )
