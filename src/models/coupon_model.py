from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlmodel import Field, Relationship

from src.models.common_base import CommonBase


# Enum to define discount types
class CouponType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class Coupon(CommonBase, table=True):
    card_variant_id: UUID = Field(
        foreign_key="cardvariant.id", nullable=False, index=True
    )
    name: str = Field(nullable=True, default=None, index=True, unique=True)
    amount: int = Field(nullable=False)
    expiration_date: datetime = Field(nullable=False)
    code: str = Field(nullable=False, index=True, unique=True)
    type: CouponType = Field(nullable=False)
    min_quantity: int = Field(default=0, nullable=True)
    max_quantity: int = Field(default=None, nullable=True)
    max_uses_per_user: int = Field(default=1, nullable=False)

    variants: "CardVariant" = Relationship(back_populates="coup")
