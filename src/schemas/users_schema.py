from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from fastapi import status
from pydantic import model_validator
from sqlmodel import Field, SQLModel

from src.models.authentication_model import RolesEnum
from src.schemas.institution_branch_schema import GetBranchResponseSchema
from src.schemas.roles_schema import GetRoles
from src.utils.custom_errors import AppError


class BaseModel(SQLModel):
    id: UUID
    is_deleted: bool | None
    created_at: datetime


class UserDataSchema(BaseModel):
    name: str
    email: str
    google_id: str | None
    phone: str | None
    verified: bool | None
    is_active: bool | None


class UserScopeResponseSchema(BaseModel):
    role_code: int
    institution_id: UUID | None
    scope_type: str


class UserFullDataSchema(UserDataSchema):
    scopes: List[UserScopeResponseSchema]


class RoleEnum(int, Enum):
    ADMIN = RolesEnum.ADMIN.value
    SYSTEM_USER = RolesEnum.SYSTEM_USER.value
    BRANCH_MANAGER = RolesEnum.BRANCH_MANAGER.value
    BUYER = RolesEnum.BUYER.value


class UserScopeSchema(SQLModel):
    # add a validator
    role_code: RoleEnum
    institution_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_role_code(
        self,
    ):
        if self.role_code == RoleEnum.BUYER.value and (
            self.institution_id or self.branch_id
        ):
            raise AppError(
                detail="Buyer cannot have institution or branch",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return self


class CreateUserScopeSchema(UserScopeSchema):
    user_id: UUID


class InstitutionResponseSchema(SQLModel):
    name: str
    email: str
    address: str
    id: UUID


class GetUserScope(BaseModel):
    user_id: UUID
    role_code: int
    institution_id: Optional[UUID] = Field(default=None, description="Institution id")
    branch_id: Optional[UUID] = Field(default=None, description="Branch id")
    scope_type: str
    is_active: bool

    institution: Optional[InstitutionResponseSchema] = None
    branches: Optional[GetBranchResponseSchema] = None
    role: Optional[GetRoles] = None


class UserProfileSchema(SQLModel):
    User: UserDataSchema
    Scopes: List[GetUserScope]


class UserUpdateSchema(SQLModel):
    name: Optional[str] = Field(default=None, description="Name of the institution")
    phone: Optional[str] = Field(default=None, description="Phone number of the user")
