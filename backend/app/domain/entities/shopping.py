"""Shopping and cooking task domain entities."""

from pydantic import BaseModel, Field

from app.domain.entities.dish import Dish


class CookingTask(BaseModel):
    """調理タスク（いつ、何を、何人前作るか）"""
    cook_day: int = Field(ge=1, description="調理日（1始まり）")
    dish: Dish
    servings: int = Field(ge=1, description="調理人前数（整数）")
    consume_days: list[int] = Field(description="消費日リスト")


class ShoppingItem(BaseModel):
    """買い物リストアイテム"""
    food_name: str
    total_amount: float = Field(description="合計量(g)")
    display_amount: str = Field(default="", description="表示用の量（例: 2本, 1/2束）")
    unit: str = Field(default="g", description="単位（個, 本, 束, 枚, パック, g）")
    category: str
    is_owned: bool = Field(default=False, description="手持ち食材かどうか")
