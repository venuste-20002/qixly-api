from decimal import Decimal
from uuid import UUID

from sqlmodel import Field, Relationship

from src.models.common_base import CommonBase


class Reviews(CommonBase, table=True):
    card_id: UUID = Field(foreign_key="card.id", primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", primary_key=True, index=True)
    review: str = Field(max_length=500, nullable=False)
    rating: Decimal = Field(nullable=False, default=0.0, decimal_places=2)

    card: "Card" = Relationship(back_populates="reviews")
    user: "Users" = Relationship(back_populates="reviews")
