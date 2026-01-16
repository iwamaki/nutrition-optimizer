"""SQLAlchemy implementation of DishRepository."""

from typing import Optional
from sqlalchemy.orm import Session

from app.domain.entities.dish import Dish, DishIngredient, RecipeDetails
from app.domain.entities.enums import DishCategoryEnum, MealTypeEnum, CookingMethodEnum
from app.domain.interfaces.dish_repository import DishRepositoryInterface
from app.infrastructure.database.models import DishDB
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
            # 文字列またはEnumどちらでも対応
            cat_value = category.value if hasattr(category, 'value') else category
            query = query.filter(DishDB.category == cat_value)
        if meal_type:
            mt_value = meal_type.value if hasattr(meal_type, 'value') else meal_type
            query = query.filter(DishDB.meal_types.contains(mt_value))

        db_dishes = query.offset(skip).limit(limit).all()
        return [self._to_entity(d) for d in db_dishes]

    def find_by_ids(self, dish_ids: list[int]) -> list[Dish]:
        """複数IDで料理を取得"""
        if not dish_ids:
            return []
        db_dishes = self._session.query(DishDB).filter(DishDB.id.in_(dish_ids)).all()
        return [self._to_entity(d) for d in db_dishes]

    def find_excluding_allergens(self, allergens: list[str]) -> list[Dish]:
        """指定アレルゲンを含まない料理を取得

        アレルゲン情報は基本食材マスタ（IngredientDB.allergens）から取得する。
        7大アレルゲン: 卵, 乳, 小麦, そば, 落花生, えび, かに
        """
        if not allergens:
            return self.find_all()

        def ingredient_contains_allergen(ingredient, allergens_to_check: list[str]) -> bool:
            """食材がアレルゲンを含むか判定"""
            if not ingredient or not ingredient.allergens:
                return False
            # カンマ区切りのアレルゲン文字列をリストに変換
            ingredient_allergens = [a.strip() for a in ingredient.allergens.split(",")]
            # 指定アレルゲンと一致するものがあるかチェック
            return any(allergen in ingredient_allergens for allergen in allergens_to_check)

        # 全料理を取得してフィルタリング
        all_dishes = self._session.query(DishDB).all()
        filtered_dishes = []

        for dish_db in all_dishes:
            # 料理の材料にアレルゲン食材が含まれているかチェック
            has_allergen = False
            for ing in dish_db.ingredients:
                if ing.ingredient and ingredient_contains_allergen(ing.ingredient, allergens):
                    has_allergen = True
                    break

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
            # 文字列またはEnumどちらでも対応
            cat_value = category.value if hasattr(category, 'value') else category
            query = query.filter(DishDB.category == cat_value)
        if meal_type:
            mt_value = meal_type.value if hasattr(meal_type, 'value') else meal_type
            query = query.filter(DishDB.meal_types.contains(mt_value))

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

            # 表示名は ingredient_name（簡潔名）を優先
            display_name = (
                ing_db.ingredient.name if ing_db.ingredient
                else (ing_db.food.name if ing_db.food else None)
            )
            ingredients.append(
                DishIngredient(
                    food_id=ing_db.food_id,
                    food_name=display_name,  # 表示用に簡潔名を優先
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
