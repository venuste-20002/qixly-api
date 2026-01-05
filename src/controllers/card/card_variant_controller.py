from uuid import UUID

from sqlmodel import Session, SQLModel, select

from src.helpers.paginator import Paginate, PaginationResponse, PaginatorQuery
from src.models.card_model import Card, CardVariant
from src.schemas.card_schema import (
    CardResponse,
    CardvariantCreateSchemas,
    CardvariantResponse,
    CardvariantSchemas,
)
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetcher


class CardVariantCreateResponse(SQLModel):
    id: UUID
    card_id: UUID
    price: int
    quantity: int
    description: str


async def create_variant_controller(
    card_id: UUID, card_data: CardvariantCreateSchemas, db: Session
) -> CardvariantResponse:

    existing_card = db.exec(select(Card).where(Card.id == card_id)).first()
    if not existing_card:
        raise AppError(status_code=404, detail="Card not found")

    existing_cardvariant = db.exec(
        select(CardVariant).where(
            CardVariant.card_id == card_id, CardVariant.price == card_data.price
        )
    ).first()

    if existing_cardvariant:
        raise AppError(
            status_code=400,
            detail="This card already has a variant with the same price",
        )

    new_cardvariant = CardVariant(**card_data.model_dump())

    db.add(new_cardvariant)
    db.commit()
    db.refresh(new_cardvariant)

    return new_cardvariant


async def get_card_variants_by_card_id_controller(
    card_id, db: Session, paginate: Paginate, min_price, max_price
) -> PaginationResponse[CardvariantResponse]:
    filter = ()

    if min_price:
        filter += (CardVariant.price >= min_price,)
    if max_price:
        filter += (CardVariant.price <= max_price,)
    if card_id:
        filter += (CardVariant.card_id.in_(card_id),)

    result_paginator, result = await PaginatorQuery.paginate(
        table_name=CardVariant,
        input_data=paginate,
        session=db,
        filters=filter,
    )

    return PaginationResponse(
        pagination=result_paginator,
        data=[
            CardvariantResponse(
                **data.model_dump(),
                card=CardResponse(
                    **data.card.model_dump(),
                ),
            )
            for data in result
        ],
    )


async def get_card_variant_by_id_controller(
    card_variant_id: UUID, db: Session
) -> CardvariantResponse:
    card_variant = Fetcher(
        database=db,
        table=(CardVariant,),
        where=(CardVariant.id == card_variant_id,),
        error="Card Variant not found",
    ).get_one()

    return card_variant


# Update CardVariant


async def update_card_variant_controller(
    card_variant_id: UUID, card_data: CardvariantSchemas, db: Session
) -> CardvariantResponse:
    variant = db.exec(
        select(CardVariant).where(CardVariant.id == card_variant_id)
    ).first()
    if not variant:
        raise AppError(status_code=404, detail="Card variant not found")

    card = card_data.model_dump(exclude_unset=True, exclude_none=True)
    variant.sqlmodel_update(card)

    db.commit()
    db.refresh(variant)

    return variant


async def delete_card_variant_controller(card_variant_id: UUID, db: Session) -> dict:

    card_variant = db.exec(
        select(CardVariant).where(CardVariant.id == card_variant_id)
    ).first()
    if not card_variant:
        raise AppError(status_code=404, detail="Card variant not found")

    card_variant.is_deleted = True
    db.add(card_variant)
    db.commit()
    db.refresh(card_variant)

    return {"detail": "CardVariant marked as deleted successfully"}
