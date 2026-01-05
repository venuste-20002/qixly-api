from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from src.models.authentication_model import Users
from src.models.common_base import CommonBase


class CartStatus(str, Enum):
    active = "active"
    completed = "completed"
    pending = "pending"
    failed = "failed"


# Class to define the Cart table
class Cart(CommonBase, table=True):
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    total_quantity: int = Field(nullable=False)
    total_price: int = Field(nullable=False)
    status: str = Field(nullable=True, default=CartStatus.active.value)

    transaction: "Transactions" = Relationship(back_populates="cart")
    salesitem: List["SalesItem"] = Relationship(back_populates="cart")
    user: Optional[List["Users"]] = Relationship(back_populates="cart")
    cartitem: List["CartItem"] = Relationship(back_populates="cart")


# Class to defined the CartItem table
class CartItem(CommonBase, table=True):
    cart_id: UUID = Field(foreign_key="cart.id", nullable=False, index=True)
    card_variant_id: UUID = Field(
        foreign_key="cardvariant.id", nullable=False, index=True
    )
    coupon_id: UUID = Field(foreign_key="coupon.id", nullable=True)
    quantity: int = Field(nullable=False)
    price: int = Field(nullable=True)
    new_price: Decimal = Field(nullable=True)
    coupon_code: str =Field(nullable=True) 
    coupon_amount:Decimal = Field(nullable=True)
    coupon_value : Decimal = Field(nullable=True)

    cart: "Cart" = Relationship(back_populates="cartitem")
    variants: "CardVariant" = Relationship(back_populates="cartitem")
