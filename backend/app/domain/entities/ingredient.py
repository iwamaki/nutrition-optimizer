"""Ingredient domain entity."""

from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    """基本食材データモデル（正規化された食材）"""
    id: int
    name: str = Field(description="正規化された食材名（例: 卵, 玉ねぎ）")
    category: str = Field(description="カテゴリ（例: 野菜類, 肉類）")
    mext_code: str = Field(default="", description="代表的な文科省食品コード")
    emoji: str = Field(default="", description="表示用絵文字")
