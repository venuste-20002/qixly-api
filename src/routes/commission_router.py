from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.controllers.commission_controller import (
    add_commission_controller,
    get_commission_by_id_controller,
    update_commission_controller,
)
from src.database import database
from src.helpers.paginator import Paginate, Pagination, PaginatorResultSchema
from src.middlewares.auth import auth
from src.models.commission_model import Commission
from src.schemas.commission_schema import CommissionResponse, CommissionResult
from src.schemas.common_schema import CommonResponseSchema

router = APIRouter(
    tags=["Commission"],
    prefix="/commissions",
    dependencies=[Depends(auth)],
)


# Route to add a new commission
@router.post("/{card_variant_id}", response_model=CommissionResponse)
async def add_commission(db: database, card_variant_id: UUID, form: CommissionResult):
    return await add_commission_controller(
        card_variant_id=card_variant_id,
        is_active=form.is_active,
        rate=form.rate,
        amount=form.amount,
        db=db,
    )


# router to get all the commission
@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[PaginatorResultSchema[CommissionResponse]],
)
async def get_all_commission_route(
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginatorResultSchema]:
    total_commission = await Pagination.paginate(
        Commission, input_data, CommissionResponse
    )
    return CommonResponseSchema(
        message="Categories fetched successfully", data=total_commission
    )


# Route to get a commission by ID
@router.get("/{commission_id}", response_model=CommissionResponse)
def get_commission_by_id(commission_id: UUID, db: database):
    return get_commission_by_id_controller(commission_id, db)


# Route to update a commission by ID
@router.put("/{commission_id}", response_model=CommissionResponse)
async def update_commission(
    db: database,
    commission_id: UUID,
    form: CommissionResult,
):
    return await update_commission_controller(
        commission_id=commission_id,
        db=db,
        is_active=form.is_active,
        rate=form.rate,
        amount=form.amount,
    )
