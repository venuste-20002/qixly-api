from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from src.schemas.institution_branch_schema import GetBranchResponseSchema
from src.schemas.users_schema import RoleEnum

T = TypeVar("T")


class InstitutionCreate(SQLModel):
    name: str = Field(..., description="Name of the institution")
    email: EmailStr = Field(..., description="Email of the institution")
    tin_number: str = Field(..., description="Tin number of the institution")
    address: str = Field(..., description="Address of the institution")
    image_url: Optional[str] = Field(..., description="Image url of the institution")


class InstitutionResponseSchema(SQLModel):
    message: str
    id: UUID
    name: str
    email: str


class InstitutionGetschema(InstitutionCreate):
    id: UUID
    is_deleted: bool
    is_active: bool


class CardResponse(SQLModel):
    id: UUID
    category_id: UUID
    institution_id: UUID
    name: str
    started_date: datetime
    expiration_date: datetime
    description: Optional[str]
    image_url: List[str]
    status: str


class InstitutionGetFullSchema(SQLModel):
    institution: InstitutionGetschema
    branches: List[GetBranchResponseSchema]
    cards: List[CardResponse]


class InstitutionUpdateSchema(SQLModel):
    name: Optional[str] = Field(default=None, description="Name of the institution")
    image_url: Optional[str] = Field(
        default=None, description="Image url of the institution"
    )
    address: Optional[str] = Field(
        default=None, description="Address of the institution"
    )


class UpdateInstitutionMemberRoleSchema(SQLModel):
    role_code: RoleEnum = Field(..., description="Role id of the member")
