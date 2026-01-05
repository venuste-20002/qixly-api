import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import status
from pydantic import Field, field_validator
from sqlmodel import SQLModel

from src.schemas.card_schema import (
    CardResponse,
    CardvariantResponse,
    CardvariantSchemas,
)
from src.schemas.users_schema import UserDataSchema
from src.utils.custom_errors import AppError


class SalesBaseSchema(SQLModel):
    phone_number: Optional[str] = None

    @field_validator("phone_number")
    def validate_phone_number(cls, value):
        if not value.startswith("25"):
            value = f"25{value}"

        if not re.match(r"^250?\d{9}$", value):
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number",
            )
        return value


class SalesResult(SalesBaseSchema):
    card_variant_id: UUID
    quantity: int = Field(..., gt=0)
    coupon_code: Optional[str] = None


class SalesCart(SalesBaseSchema):
    coupon_codes: Optional[List[str]] = None
    phone_number: Optional[str] = None


class SalesSchemaResponse(SQLModel):
    total_cost_amount: int
    total_payed_amount: int
    total_coupon_discount: int
    transaction_id: UUID


class SalesSchemaResponse(SQLModel):
    total_cost_amount: int
    total_payed_amount: int
    total_coupon_discount: int
    transaction_id: UUID


class SalesResponse(SQLModel):
    id: UUID
    card_variant_id: UUID
    quantity: int
    cost_amount: int
    amount_payed: int


class SalesCartResponse(SQLModel):
    total_payed_amount: int
    total_coupon_discount: int
    transaction_id: UUID


class SalesItemsResponse(SQLModel):
    id: UUID
    card_variant_id: UUID | None
    cost_variant: int
    viewed: bool
    shared: bool
    user_id: UUID
    cart_id: UUID
    status: str
    used_date: Optional[datetime] = None
    sales_number: Optional[str] = None
    sales_number_sequence: Optional[str] = None
    created_at: datetime


class SalesFullItemsResponse(SQLModel):
    item: SalesItemsResponse
    card_variant: CardvariantResponse


class SaleResponseSchema(SQLModel):
    id: UUID
    card_variant_id: UUID | None
    cost_variant: float
    status: str | None
    shared: bool | None
    viewed: bool | None
    used_date: datetime | None
    created_at: datetime
    sales_number: Optional[str] = None
    sales_number_sequence: Optional[str] = None


class TransactionSchema(SQLModel):
    id: UUID
    transaction_number: Optional[str] = None
    network: Optional[str] = None
    tx_status: str


class SalesItemFullSchema(SaleResponseSchema):
    user: UserDataSchema
    card: CardResponse
    card_variant: CardvariantSchemas
    transaction: TransactionSchema
