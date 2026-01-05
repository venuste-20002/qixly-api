from sqlmodel import SQLModel
from fastapi import Form
from fastapi import UploadFile
from typing import Optional
import re
from uuid import UUID
from datetime import datetime
from typing import List

from src.models.coupon_model import CouponType

class CouponSchema (SQLModel):
    amount: int
    expiration_date: datetime 
    type: CouponType
    name: str = None
    min_quantity: int = 0
    max_quantity: int = None
    max_uses_per_user: int = 1
    

class CouponResponse(SQLModel):
    id: UUID
    card_variant_id: UUID
    name :Optional[str]
    amount: int
    code: str
    expiration_date: datetime
    type: CouponType 
    min_quantity: Optional[int]
    max_quantity: Optional[int]
    max_uses_per_user: int


