from sqlmodel import SQLModel
from fastapi import Form
from fastapi import UploadFile
from typing import Optional
import re
from uuid import UUID
from datetime import datetime
from typing import List

class CommissionResult (SQLModel):
    rate:int = None
    amount : int  = None
    is_active: bool

class CommissionResponse(SQLModel):
    id: UUID
    card_variant_id: UUID 
    rate: Optional[int] 
    amount : Optional[int]
    is_active: bool 
    


