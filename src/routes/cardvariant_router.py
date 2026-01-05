from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.controllers.card.card_variant_controller import (
    create_variant_controller,
    delete_card_variant_controller,
    get_card_variant_by_id_controller,
    get_card_variants_by_card_id_controller,
    update_card_variant_controller,
)
from src.database import database
from src.helpers.paginator import Paginate, PaginationResponse
from src.middlewares.auth import auth
from src.schemas.card_schema import (
    CardvariantCreateSchemas,
    CardvariantResponse,
    CardvariantSchemas,
)

router = APIRouter(
    prefix="/card_variant",
    tags=["Card Variant"],
)


@router.post(
    "",
    response_model=CardvariantResponse,
    dependencies=[Depends(auth)],
)
async def create_variant(
    card_data: CardvariantCreateSchemas,
    db: database,
):
    return await create_variant_controller(
        card_data.card_id,
        card_data,
        db,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginationResponse[CardvariantResponse],
)
async def get_card_variants_by_card_id_endpoint(
    db: database,
    card_id: list[UUID] = Query(None),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    paginate: Paginate = Depends(),
):
    return await get_card_variants_by_card_id_controller(
        card_id,
        db,
        paginate,
        min_price,
        max_price,
    )


@router.get("/{card_variant_id}", response_model=CardvariantResponse)
async def get_card_variant_by_id(card_variant_id: UUID, db: database):
    return await get_card_variant_by_id_controller(card_variant_id, db)


@router.patch(
    "/{card_variant_id}",
    response_model=CardvariantResponse,
    dependencies=[Depends(auth)],
    status_code=status.HTTP_201_CREATED,
)
async def update_card_variant(
    card_variant_id: UUID,
    card_data: CardvariantSchemas,
    db: database,
):
    return await update_card_variant_controller(card_variant_id, card_data, db)


@router.delete(
    "/{card_variant_id}",
    response_model=dict,
    dependencies=[Depends(auth)],
    status_code=status.HTTP_200_OK,
)
async def delete_card_variant(card_variant_id: UUID, db: database):
    return await delete_card_variant_controller(card_variant_id, db)
