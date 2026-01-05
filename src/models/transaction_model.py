from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from src.models.authentication_model import Users
from src.models.common_base import CommonBase
from src.schemas.sales_schema import SalesFullItemsResponse
from src.schemas.users_schema import UserDataSchema


class TransactionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class Transactions(CommonBase, table=True):
    user_id: UUID = Field(foreign_key="users.id", nullable=True)
    total_payed_amount: int = Field(nullable=True)
    total_recieved_amount: int = Field(nullable=True)
    coupon_amount: int = Field(nullable=True)
    commission_amount: Decimal = Field(
        nullable=True, default=0, max_digits=5, decimal_places=3
    )
    commission_rate: int = Field(nullable=True)
    phone_number: str = Field(
        nullable=True, index=True, max_length=20, default="0000000000"
    )
    tx_status: str = Field(nullable=True, default=TransactionStatus.PENDING.value)
    channel_transaction_id: str = Field(nullable=True)
    payment_channel: str = Field(nullable=True)
    transaction_number: str = Field(nullable=True)
    transaction_time: datetime = Field(nullable=True)
    cart_id: UUID = Field(foreign_key="cart.id", nullable=True)
    network: str = Field(default=None, nullable=True)
    transaction_number: str = Field(nullable=True, default=None)

    cart: "Cart" = Relationship(back_populates="transaction")
    user: Optional[Users] = Relationship(back_populates="transaction")


class CartResponse(SQLModel):
    id: UUID
    user_id: UUID
    total_quantity: int
    total_price: float
    status: str


class TransactionSchema(BaseModel):
    id: UUID
    user_id: UUID
    cart_id: UUID
    phone_number: str
    total_payed_amount: int
    total_recieved_amount: int
    commission_amount: Decimal = Field(nullable=True, default=0.0, decimal_places=3)
    commission_rate: int
    coupon_amount: int
    payment_channel: str | None
    tx_status: str
    transaction_time: Optional[datetime] = None
    created_at: datetime
    network: Optional[str] = None

    user: UserDataSchema
    cart: CartResponse


class TransactionSingleSchema(BaseModel):
    id: UUID
    user_id: UUID
    cart_id: UUID
    phone_number: str
    total_payed_amount: int
    total_recieved_amount: int
    commission_amount: Decimal = Field(nullable=True, default=0.0, decimal_places=3)
    commission_rate: int
    coupon_amount: int
    payment_channel: str | None
    tx_status: str
    transaction_time: Optional[datetime] = None
    created_at: datetime
    channel_transaction_id: Optional[str] = None
    network: Optional[str] = None
    transaction_number: Optional[str] = None

    user: UserDataSchema
    sales_items: Optional[list[SalesFullItemsResponse]] = None


class TransactionInputSchema(BaseModel):
    user_id: UUID
    cart_id: UUID
    phone_number: str
    total_payed_amount: int
    total_recieved_amount: int
    commission_amount: Decimal = Field(nullable=True, default=0.0, decimal_places=3)
    commission_rate: int
    coupon_amount: int
    network: Optional[str] = None
