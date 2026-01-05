from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

T = TypeVar("T")


class CommonResponseSchema(BaseModel, Generic[T]):
    status: str = Field(default="success", description="Status of the response")
    message: str = Field(
        default="Request Successfully", description="Message of the response"
    )
    data: T = Field(..., description="Data of the response")


class ChangeStatusSchema(SQLModel):
    is_active: bool
