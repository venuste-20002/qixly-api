
from sqlmodel import  Field, Relationship
from src.models.common_base import CommonBase
from uuid import UUID
from src.models.authentication_model import Users
from typing import Optional
# from src.models.sales_model import SalesItem

class SharedCard(CommonBase , table=True):
    sales_item_id:UUID = Field(foreign_key="salesitem.id", nullable=False)
    card_amount : int = Field(nullable=False,index=True)
    email :str = Field(nullable=True,index=True)
    phone : str = Field(nullable=True,index=True)

    sales:"SalesItem" = Relationship(back_populates="share")
