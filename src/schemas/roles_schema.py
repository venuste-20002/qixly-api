from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from sqlmodel import SQLModel

T = TypeVar("T")


class GetRoles(SQLModel):
    id: UUID
    name: str
    code: int
    description: str
    is_deleted: bool


class GetRolePermissions(SQLModel, Generic[T]):
    role: int
    permission: List[T]


class RoleCreateSchema(SQLModel):
    name: str
    description: Optional[str] = None


class CreateRoleSchema(SQLModel):
    name: str
    code: int
    description: Optional[str] = None
