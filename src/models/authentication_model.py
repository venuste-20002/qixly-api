from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, UniqueConstraint

from src.models.common_base import CommonBase
from src.models.institutions_model import Institutions


class Users(CommonBase, table=True):
    name: str = Field(nullable=False, index=True)
    email: Optional[str] = Field(nullable=True, unique=True)
    password: Optional[str] = Field(nullable=True, default=None)
    phone: Optional[str] = Field(nullable=True, default=None)
    google_id: Optional[str] = Field(nullable=True, unique=True, default=None)
    verified: Optional[bool] = Field(nullable=False, default=False)
    secret: Optional[str] = Field(nullable=True, default=None)
    is_active: Optional[bool] = Field(nullable=True, default=True)

    userscope: list["UserScope"] = Relationship(back_populates="users")
    cart: list["Cart"] = Relationship(back_populates="user")
    transaction: List["Transactions"] = Relationship(back_populates="user")
    reviews: List["Reviews"] = Relationship(back_populates="user")
    sales: "SalesItem" = Relationship(back_populates="user")

    @staticmethod
    def searchable_fields():
        return [Users.name, Users.email, Users.phone]


class UserScopeEnum(str, Enum):
    SYSTEM = "SYSTEM"
    INSTITUTION = "INSTITUTION"
    BRANCH = "BRANCH"


class UserScope(CommonBase, table=True):
    user_id: UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    role_code: int = Field(foreign_key="roles.code", nullable=False)
    institution_id: Optional[UUID] = Field(
        foreign_key="institutions.id", nullable=True, default=None
    )
    branch_id: Optional[UUID] = Field(
        foreign_key="branches.id", nullable=True, default=None
    )
    scope_type: str = Field(nullable=False)
    is_active: bool = Field(default=False, nullable=True)

    users: Users = Relationship(back_populates="userscope")
    institution: Optional[List["Institutions"]] = Relationship(
        back_populates="userscope"
    )
    roles: list["Roles"] = Relationship(back_populates="userscope")
    branches: list["Branches"] = Relationship(back_populates="userscope")


class RolesEnum(str, Enum):
    SUPER_USER = 10
    ADMIN = 11
    SYSTEM_USER = 12
    BRANCH_MANAGER = 13
    BUYER = 14


class Roles(CommonBase, table=True):
    _table_args_ = (
        UniqueConstraint("name", "code", name="uq_role_name_code"),
        {"extend_existing": True},
    )

    name: str = Field(nullable=False, default=RolesEnum.BUYER.name)
    description: str = Field(nullable=True, default=None)
    code: int = Field(default=None, nullable=False, unique=True)

    userscope: UserScope = Relationship(back_populates="roles")
    rolepermissions: list["RolePermissions"] = Relationship(back_populates="roles")


class Permissions(CommonBase, table=True):
    _table_args_ = (
        UniqueConstraint("name", "group", name="uq_permission_name_group"),
        {"extend_existing": True},
    )

    name: str = Field(nullable=False, unique=True, index=True)
    group: str = Field(nullable=False, index=True)
    description: str = Field(nullable=True)


class RolePermissions(CommonBase, table=True):
    _table_args = (UniqueConstraint("role", "permission", name="uq_role_permission"),)

    role: int = Field(foreign_key="roles.code", nullable=False, index=True)
    permission: str = Field(nullable=True, default=None)
    exclude: str = Field(nullable=True, default=None)

    roles: Roles = Relationship(back_populates="rolepermissions")


class Blacklist(CommonBase, table=True):
    token: str = Field(nullable=True)
