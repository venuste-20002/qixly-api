from uuid import UUID
from sqlmodel import SQLModel
from typing import List,Optional

class SharedResult(SQLModel):
     sales_item_id : UUID
     email : str = None
     phone : str = None
     

class SharedResponse(SQLModel):
     id : UUID
     sales_item_id : UUID
     card_amount : int 
     email : Optional[str]
     phone : Optional[str]
