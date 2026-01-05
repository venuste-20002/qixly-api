from decimal import Decimal
from uuid import UUID

from fastapi import Query
from sqlmodel import SQLModel

from src.schemas.card_schema import CardResponse


class ReviewsInputSchema(SQLModel):
    card_id: UUID
    review: str
    rating: Decimal = Query(default=0.0, gt=0, le=5, max_digits=2, decimal_places=1)


class ReviewsSchema(ReviewsInputSchema):
    user_id: UUID


class ReviewResponseSchema(ReviewsSchema):
    id: UUID
    is_deleted: bool


class ReviewFullResponseSchema(ReviewResponseSchema):
    card: CardResponse
