from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status

from src.controllers.card.card_controller import (
    create_card_controller,
    get_all_cards_controller,
    get_card_by_id_controller,
    mark_card_as_deleted_controller,
    update_card_by_id_controller,
)
from src.database import database
from src.helpers.image_uploader import save_image
from src.helpers.paginator import Paginate, PaginationResponse
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.card_model import Card, CardStatus
from src.schemas.card_schema import CardFullResponse, CardResponse, UpdateCardSchema
from src.schemas.common_schema import CommonResponseSchema
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)
from src.utils.fetcher import Fetcher

router = APIRouter(tags=["Cards"], prefix="/cards")


@router.post("", dependencies=[Depends(auth)])
@authorized(
    permission__(PermissionsResources.CARD, PermissionActivity.WRITE),
)
async def create_card(
    _: Request,
    db: database,
    category_id: UUID = Form(...),
    institution_id: UUID = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    started_date: datetime = Form(...),
    expiration_date: datetime = Form(...),
    usage_time: str = Form(...),
    image: list[UploadFile] = File(None),
):
    return await create_card_controller(
        usage_time,
        category_id,
        institution_id,
        name,
        description,
        started_date,
        expiration_date,
        image,
        db,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[PaginationResponse[CardFullResponse]],
)
async def get_all_card_route(
    db: database,
    status_: Optional[CardStatus] = None,
    start_date: Optional[datetime] = None,
    ending_date: Optional[datetime] = None,
    institution: Optional[list[UUID]] = Query(None),
    category: Optional[list[UUID]] = Query(None),
    input_data: Paginate = Depends(),
    search: Optional[str] = None,
) -> CommonResponseSchema:
    total_cards = await get_all_cards_controller(
        db=db,
        search=search,
        status_=status_,
        start_date=start_date,
        ending_date=ending_date,
        institution=institution,
        category=category,
        input_data=input_data,
    )
    return CommonResponseSchema(message="Card fetched successfully", data=total_cards)


@router.get("/{card_id}", response_model=CommonResponseSchema[CardFullResponse])
async def get_card_by_id(card_id: UUID, db: database):
    data = await get_card_by_id_controller(card_id, db)
    return CommonResponseSchema(message="Card fetched successfully", data=data)


@router.patch(
    "/{card_id}",
    response_model=CommonResponseSchema[CardResponse],
    dependencies=[Depends(auth)],
)
@authorized(
    permission__(PermissionsResources.CARD, PermissionActivity.WRITE),
)
async def update_card_by_id(
    _: Request,
    db: database,
    card_id: UUID,
    name: str = Form(None),
    description: str = Form(None),
    terms_conditions: str = Form(None),
    started_date: datetime = Form(None),
    expiration_date: datetime = Form(None),
    image: UploadFile = File(None),
) -> CommonResponseSchema[CardResponse]:

    image_link = save_image(image)

    return await update_card_by_id_controller(
        card_id=card_id,
        input_data=UpdateCardSchema(
            name=name,
            description=description,
            started_date=started_date,
            expiration_date=expiration_date,
            image=image_link,
            terms_conditions=terms_conditions,
        ),
        db=db,
    )


class CardStatusUpdate(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@router.patch(
    "/{card_id}/status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth)],
)
@authorized(
    permission__(PermissionsResources.CARDS, PermissionActivity.WRITE),
)
async def update_card_status(
    _: Request,
    card_id: UUID,
    status_: CardStatusUpdate,
    db: database,
):
    get_card = Fetcher(
        database=db,
        table=(Card,),
        where=(Card.id == card_id,),
        error="Card not found",
    ).get_one()

    get_card.status = status_

    db.commit()
    db.refresh(get_card)

    return CommonResponseSchema(
        message="Card status updated",
        data=CardResponse(**get_card.model_dump()),
    )


@router.delete(
    "/{card_id}",
    response_model=dict,
    dependencies=[Depends(auth)],
)
@authorized(
    permission__(PermissionsResources.CARDS, PermissionActivity.WRITE),
)
async def delete_card_by_id(_: Request, card_id: UUID, db: database):
    return await mark_card_as_deleted_controller(card_id, db)
