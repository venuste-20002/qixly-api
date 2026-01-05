from uuid import UUID

from sqlmodel import Field, Relationship

from src.models.common_base import CommonBase


# Class to defined the Commission table
class Commission(CommonBase, table=True):
    card_variant_id: UUID = Field(
        foreign_key="cardvariant.id", nullable=False, index=True
    )
    rate: int = Field(nullable=True, index=True)
    amount: int = Field(nullable=True, index=True)
    is_active: bool = Field(nullable=False, default=True, index=True)

    variant: "CardVariant" = Relationship(back_populates="commissions")

