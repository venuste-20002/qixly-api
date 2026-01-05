from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlmodel import JSON, Column, Field, Relationship

from src.models.authentication_model import Institutions
from src.models.cart_model import CartItem
from src.models.category_model import Category
from src.models.commission_model import Commission
from src.models.common_base import CommonBase
from src.models.coupon_model import Coupon
from src.models.reviews_model import Reviews


#  Class to defined the Card
class CardStatus(str, Enum):
    EXPIRED = "EXPIRED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Card(CommonBase, table=True):
    category_id: UUID = Field(foreign_key="category.id", nullable=False, index=True)
    institution_id: UUID = Field(
        foreign_key="institutions.id", nullable=False, index=True
    )
    name: str = Field(nullable=False, unique=True, index=True)
    description: str = Field(default=None, nullable=True)
    started_date: datetime = Field(nullable=False)
    expiration_date: datetime = Field(nullable=False)
    image_url: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    status: str = Field(default=CardStatus.INACTIVE.value, nullable=True)
    terms_conditions: str = Field(default=None, nullable=True)
    usage_time: str = Field(default=None, nullable=True)

    category: "Category" = Relationship(back_populates="cards")
    variants: List["CardVariant"] = Relationship(back_populates="card")
    institution: Optional[List["Institutions"]] = Relationship(back_populates="cards")
    wishlist: List["Wishlist"] = Relationship(back_populates="card")
    reviews: List["Reviews"] = Relationship(back_populates="card")
    sales: List["SalesItem"] = Relationship(back_populates="card")

    @staticmethod
    def searchable_fields():
        return [Card.name]


# Class to defined the CardVariant
class CardVariant(CommonBase, table=True):
    card_id: UUID = Field(foreign_key="card.id", nullable=False, index=True)
    price: int = Field(nullable=False, index=True)
    quantity: int = Field(nullable=False, index=True)
    description: str = Field(default=None, nullable=True)
    pending_quantity: int = Field(default=0, nullable=True)

    sales_item: "SalesItem" = Relationship(back_populates="card_variant")
    card: Optional[Card] = Relationship(back_populates="variants")
    coup: list["Coupon"] = Relationship(back_populates="variants")
    commissions: list["Commission"] = Relationship(back_populates="variant")
    cartitem: list["CartItem"] = Relationship(back_populates="variants")
