from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nutrition.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class FoodDB(Base):
    """食品テーブル"""
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    calories = Column(Float, default=0)
    protein = Column(Float, default=0)
    fat = Column(Float, default=0)
    carbohydrate = Column(Float, default=0)
    fiber = Column(Float, default=0)
    sodium = Column(Float, default=0)
    calcium = Column(Float, default=0)
    iron = Column(Float, default=0)
    vitamin_a = Column(Float, default=0)
    vitamin_c = Column(Float, default=0)
    vitamin_d = Column(Float, default=0)
    max_portion = Column(Float, default=300)


def init_db():
    """データベース初期化"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """DBセッション取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
