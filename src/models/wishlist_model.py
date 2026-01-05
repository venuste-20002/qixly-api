from uuid import UUID

from sqlmodel import Field, Relationship

from src.models.common_base import CommonBase


class Wishlist(CommonBase, table=True):
    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
    )
    card_id: UUID = Field(
        foreign_key="card.id",
        nullable=True,
        default=None,
    )
    card: "Card" = Relationship(back_populates="wishlist")
