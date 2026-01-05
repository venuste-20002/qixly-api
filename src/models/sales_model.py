from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlmodel import Field, Relationship

from src.models.common_base import CommonBase
from src.models.shared_model import SharedCard


class SaleStatus(str, Enum):
    USED = "USED"
    UNUSED = "UNUSED"


class SalesItem(CommonBase, table=True):
    user_id: UUID = Field(foreign_key="users.id", nullable=True)
    cart_id: UUID = Field(
        foreign_key="cart.id", nullable=True, default=None, index=True
    )
    card_variant_id: UUID = Field(
        foreign_key="cardvariant.id", nullable=True, index=True, default=None
    )
    card_id: UUID = Field(foreign_key="card.id", nullable=True, index=True)
    cost_variant: int = Field(nullable=False)
    shared: bool = Field(nullable=True, default=False)
    viewed: bool = Field(nullable=True, default=False)
    status: str = Field(nullable=True, default=SaleStatus.UNUSED)
    used_date: datetime = Field(nullable=True, default=None)
    sales_number_sequence: str = Field(nullable=True, default=None)
    sales_number: str = Field(nullable=True, default=None)

    card_variant: "CardVariant" = Relationship(back_populates="sales_item")
    cart: "Cart" = Relationship(back_populates="salesitem")
    share: list["SharedCard"] = Relationship(back_populates="sales")
    card: "Card" = Relationship(back_populates="sales")
    user: "Users" = Relationship(back_populates="sales")
