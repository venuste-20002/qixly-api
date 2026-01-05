from typing import Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from src.models.common_base import CommonBase


class Institutions(CommonBase, table=True):
    name: str = Field(nullable=False, index=True)
    email: str = Field(nullable=False, index=True)
    tin_number: str = Field(nullable=False)
    image_url: Optional[str] = Field(nullable=True, default=None)
    is_active: bool = Field(default=False, nullable=True)
    address: Optional[str] = Field(nullable=False, default=None)

    branch: list["Branches"] = Relationship(back_populates="institution")
    userscope: list["UserScope"] = Relationship(back_populates="institution")
    cards: list["Card"] = Relationship(back_populates="institution")

    @staticmethod
    def searchable_fields():
        return [
            Institutions.name,
            Institutions.email,
            Institutions.tin_number,
        ]


class Branches(CommonBase, table=True):
    name: str = Field(nullable=False, index=True)
    email: str = Field(nullable=False, index=True)
    is_active: bool = Field(default=False, nullable=True)
    address: str = Field(nullable=False)
    institution_id: UUID = Field(foreign_key="institutions.id", nullable=False)

    institution: Institutions = Relationship(back_populates="branch")
    userscope: list["UserScope"] = Relationship(back_populates="branches")

    @staticmethod
    def searchable_fields():
        return [
            Branches.name,
            Branches.email,
            Branches.address,
        ]
