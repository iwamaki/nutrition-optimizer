"""SQLAlchemy implementation of FoodRepository."""

from typing import Optional
from sqlalchemy.orm import Session

from app.domain.entities.food import Food
from app.domain.interfaces.food_repository import FoodRepositoryInterface
from app.infrastructure.database.models import FoodDB, FoodAllergenDB


class SQLAlchemyFoodRepository(FoodRepositoryInterface):
    """SQLAlchemy implementation of food repository."""

    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, food_id: int) -> Optional[Food]:
        """IDで食品を取得"""
        db_food = self._session.query(FoodDB).filter(FoodDB.id == food_id).first()
        return self._to_entity(db_food) if db_food else None

    def find_by_mext_code(self, mext_code: str) -> Optional[Food]:
        """文科省コードで食品を取得"""
        db_food = self._session.query(FoodDB).filter(FoodDB.mext_code == mext_code).first()
        return self._to_entity(db_food) if db_food else None

    def find_all(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Food]:
        """食品一覧を取得"""
        query = self._session.query(FoodDB)

        if category:
            query = query.filter(FoodDB.category == category)

        db_foods = query.offset(skip).limit(limit).all()
        return [self._to_entity(f) for f in db_foods]

    def search(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> list[Food]:
        """キーワードで食品を検索"""
        query = self._session.query(FoodDB).filter(
            FoodDB.name.contains(keyword)
        )

        if category:
            query = query.filter(FoodDB.category == category)

        db_foods = query.limit(limit).all()
        return [self._to_entity(f) for f in db_foods]

    def count(self, category: Optional[str] = None) -> int:
        """食品数をカウント"""
        query = self._session.query(FoodDB)

        if category:
            query = query.filter(FoodDB.category == category)

        return query.count()

    def get_categories(self) -> list[str]:
        """利用可能なカテゴリ一覧を取得"""
        categories = (
            self._session.query(FoodDB.category)
            .distinct()
            .all()
        )
        return [c[0] for c in categories if c[0]]

    def get_allergens_for_food(self, food_id: int) -> list[str]:
        """食品のアレルゲン情報を取得"""
        allergens = (
            self._session.query(FoodAllergenDB.allergen)
            .filter(FoodAllergenDB.food_id == food_id)
            .all()
        )
        return [a[0] for a in allergens]

    def _to_entity(self, db_food: FoodDB) -> Food:
        """DBモデルをドメインエンティティに変換"""
        return Food(
            id=db_food.id,
            name=db_food.name,
            category=db_food.category or "",
            calories=db_food.calories or 0,
            protein=db_food.protein or 0,
            fat=db_food.fat or 0,
            carbohydrate=db_food.carbohydrate or 0,
            fiber=db_food.fiber or 0,
            sodium=db_food.sodium or 0,
            potassium=db_food.potassium or 0,
            calcium=db_food.calcium or 0,
            magnesium=db_food.magnesium or 0,
            iron=db_food.iron or 0,
            zinc=db_food.zinc or 0,
            vitamin_a=db_food.vitamin_a or 0,
            vitamin_d=db_food.vitamin_d or 0,
            vitamin_e=db_food.vitamin_e or 0,
            vitamin_k=db_food.vitamin_k or 0,
            vitamin_b1=db_food.vitamin_b1 or 0,
            vitamin_b2=db_food.vitamin_b2 or 0,
            vitamin_b6=db_food.vitamin_b6 or 0,
            vitamin_b12=db_food.vitamin_b12 or 0,
            niacin=db_food.niacin or 0,
            pantothenic_acid=db_food.pantothenic_acid or 0,
            biotin=db_food.biotin or 0,
            folate=db_food.folate or 0,
            vitamin_c=db_food.vitamin_c or 0,
            max_portion=db_food.max_portion or 300,
        )
