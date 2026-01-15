"""SQLAlchemy implementation of IngredientRepository."""

from typing import Optional
from sqlalchemy.orm import Session

from app.domain.entities.ingredient import Ingredient
from app.domain.interfaces.ingredient_repository import IngredientRepositoryInterface
from app.infrastructure.database.models import IngredientDB


class SQLAlchemyIngredientRepository(IngredientRepositoryInterface):
    """SQLAlchemy implementation of ingredient repository."""

    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, ingredient_id: int) -> Optional[Ingredient]:
        """IDで食材を取得"""
        db_ingredient = self._session.query(IngredientDB).filter(
            IngredientDB.id == ingredient_id
        ).first()
        return self._to_entity(db_ingredient) if db_ingredient else None

    def find_all(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Ingredient]:
        """食材一覧を取得"""
        query = self._session.query(IngredientDB)

        if category:
            query = query.filter(IngredientDB.category == category)

        db_ingredients = query.order_by(IngredientDB.id).offset(skip).limit(limit).all()
        return [self._to_entity(i) for i in db_ingredients]

    def find_by_ids(self, ingredient_ids: list[int]) -> list[Ingredient]:
        """複数IDで食材を取得"""
        if not ingredient_ids:
            return []
        db_ingredients = self._session.query(IngredientDB).filter(
            IngredientDB.id.in_(ingredient_ids)
        ).all()
        return [self._to_entity(i) for i in db_ingredients]

    def count(self, category: Optional[str] = None) -> int:
        """食材数をカウント"""
        query = self._session.query(IngredientDB)

        if category:
            query = query.filter(IngredientDB.category == category)

        return query.count()

    def get_categories(self) -> list[str]:
        """利用可能なカテゴリ一覧を取得"""
        categories = (
            self._session.query(IngredientDB.category)
            .distinct()
            .all()
        )
        return [c[0] for c in categories if c[0]]

    def _to_entity(self, db_ingredient: IngredientDB) -> Ingredient:
        """DBモデルをドメインエンティティに変換"""
        return Ingredient(
            id=db_ingredient.id,
            name=db_ingredient.name,
            category=db_ingredient.category or "",
            mext_code=db_ingredient.mext_code or "",
            emoji=db_ingredient.emoji or "",
        )
