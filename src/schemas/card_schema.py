from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel
from sqlmodel import SQLModel

from src.models.card_model import CardStatus
from src.schemas.institution_schema import InstitutionGetschema


# Incoming request schema for creating a category
class CategorySchemas(SQLModel):
    name: str
    description: Optional[str] = None

    @classmethod
    def as_form(
        cls, name: str = Form(...), description: str = Form(...)
    ) -> "CategorySchemas":
        return cls(name=name, description=description)


class CategoryResponse(SQLModel):
    id: UUID
    name: str
    description: str


#  the schema on the card
class CardResponse(SQLModel):
    id: UUID
    category_id: UUID
    institution_id: UUID
    name: str
    started_date: datetime
    expiration_date: datetime
    description: Optional[str]
    image_url: list[str]
    usage_time: Optional[str] = None
    status: str
    created_at: datetime
    is_deleted: bool
    terms_conditions: Optional[str] = None
    category: Optional[CategoryResponse] = None
    institution: Optional[InstitutionGetschema] = None


class CategoryFullResponse(SQLModel):
    category: CategoryResponse
    cards: List[CardResponse]


class CardvariantSchemas(SQLModel):
    price: Optional[int] = None
    quantity: Optional[int] = None
    description: Optional[str] = None


class CardvariantCreateSchemas(CardvariantSchemas):
    card_id: UUID


class CardvariantResponse(CardvariantSchemas):
    id: UUID
    card_id: UUID
    card: Optional[CardResponse] = None


class CardVariantFullResponse(CardvariantSchemas):
    id: UUID
    card_id: UUID


class CardFullResponse(SQLModel):
    card: CardResponse
    variants: List[CardVariantFullResponse]
    institution: InstitutionGetschema


class UpdateCardSchema(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    started_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    image: Optional[str] = None
    terms_conditions: Optional[str] = None


class FilterCardSchema(BaseModel):
    status: Optional[CardStatus] = None
