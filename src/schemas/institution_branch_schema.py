from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel

T = TypeVar("T")


class InstitutionResponseSchema(SQLModel):
    id: UUID
    name: str
    email: str
    tin_number: str
    address: str
    is_active: bool


class GetBranchResponseSchema(SQLModel):
    id: UUID
    name: str
    email: str
    institution_id: UUID
    address: str
    is_active: bool
    is_deleted: bool
    created_at: datetime


class GetBranchFullResponseSchema(GetBranchResponseSchema):
    institution: InstitutionResponseSchema


class CreateBranchSchema(SQLModel):
    name: str
    email: EmailStr
    address: str


class CreateInstitutionBranchSchema(CreateBranchSchema):
    institution_uuid: UUID


class UpdateBranchSchema(SQLModel):
    name: Optional[str] = Field(default=None, description="Name of the institution")
    tin_number: Optional[str] = Field(
        default=None, description="Name of the institution"
    )
    address: Optional[str] = Field(default=None, description="Name of the institution")


class UserDataResponseSchema(SQLModel):
    id: UUID
    name: str
    email: str
    verified: bool
    is_active: bool


class GetUserScope(SQLModel):
    user_id: UUID
    role_code: int
    institution_id: Optional[UUID]


class UserDataSchema(BaseModel, Generic[T]):
    user: UserDataResponseSchema
    userscope: list[GetUserScope]
