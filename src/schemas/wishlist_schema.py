from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from src.schemas.card_schema import CardResponse


class CreateWishlistSchema(SQLModel):
    card_id: Optional[UUID] = None


class WishlistResponse(SQLModel):
    id: UUID
    user_id: UUID
    card_id: Optional[UUID] = None
    card: CardResponse
