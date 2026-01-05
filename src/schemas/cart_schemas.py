from decimal import Decimal
from typing import Optional
from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel

from src.schemas.card_schema import CategoryResponse

# Incoming request schema for creating a category


class Cart(SQLModel):
    card_variant_id: UUID
    quantity: int


class CartItem(SQLModel):
    quantity: int


class CartResponse(SQLModel):
    id: UUID
    user_id: UUID
    total_quantity: int
    total_price: float
    status: str


class CardVariantResponse(SQLModel):
    id: UUID
    price: int
    quantity: int
    description: Optional[str]


class CardResponse(SQLModel):
    id: UUID
    image_url: list[str]
    name: str
    description: str
    category: Optional[CategoryResponse] = None


class CartItemResponse(BaseModel):
    id: UUID
    cart_id: UUID
    card_variant_id: UUID
    quantity: int
    price: int
    coupon_code: Optional[str] = None
    new_price: Optional[Decimal] =None
    coupon_amount: Optional[Decimal] = None
    coupon_value : Optional[Decimal] = None
    coupon_id: Optional[UUID] = None
    card_variant: CardVariantResponse
    card: CardResponse


class CartFullResponse(SQLModel):
    cart: CartResponse
    cart_items: list[CartItemResponse]
    
class CartCouponFullResponse(SQLModel):
    cart: CartResponse
    cart_items: list[CartItemResponse]
    total_final_amount: Decimal
    total_coupon_discount: Decimal
    applied_coupons: list[str]
    

class CartItemPreview(BaseModel):
    card_variant_id: UUID
    quantity: int

class CouponPreviewRequest(BaseModel):
    cart_items: List[CartItemPreview]
    coupon_codes: Optional[List[str]] = None

class CouponPreviewResponse(BaseModel):
    total_price: float
    total_discount: float
    final_amount: float
    applied_coupons: List[str]
    invalid_coupons: dict[str, str]