from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status

from src.controllers.shared_controller import (
    Shared_card_item,
    get_shared_by_id_controler,
)
from src.database import database
from src.helpers.paginator import Paginate, Pagination, PaginatorResultSchema
from src.middlewares.auth import auth
from src.models.shared_model import SharedCard
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.shared_schema import SharedResponse, SharedResult

router = APIRouter(prefix="/share", tags=["shared"], dependencies=[Depends(auth)])


@router.post("", response_model=SharedResponse)
async def share_file(db: database, form: SharedResult, background: BackgroundTasks):
    return await Shared_card_item(
        sales_item_card=form.sales_item_id,
        email=form.email,
        phone=form.phone,
        db=db,
        background=background,
    )


# router of getting all the shared card
@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[PaginatorResultSchema[SharedResponse]],
)
async def get_all_shared_card(
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginatorResultSchema]:
    total_sales = await Pagination.paginate(SharedCard, input_data, SharedResponse)
    return CommonResponseSchema(message="Sales fetched successfully", data=total_sales)


# router of getting single shared card
@router.get("/{share_id}", response_model=SharedResponse)
async def get_single_shared_by_id(db: database, shared_id: UUID):
    return await get_shared_by_id_controler(db=db, shared_id=shared_id)
