from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.controllers.coupon_controller import (
    create_coupon_controller,
    delete_coupon_controller,
    get_coupon_by_id_controller,
    update_coupon_controller,
)
from src.database import database
from src.helpers.paginator import Paginate, Pagination, PaginatorResultSchema
from src.middlewares.auth import auth
from src.models.coupon_model import Coupon
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.coupon_schema import CouponResponse, CouponSchema

router = APIRouter(tags=["Coupon"], prefix="/coupons", dependencies=[Depends(auth)])


# Route to create a new coupon
@router.post("/coupon/{card_variant_id}", response_model=CouponResponse)
async def create_coupon(db: database, card_variant_id: UUID, form: CouponSchema):

    return await create_coupon_controller(
        db=db,
        card_variant_id=card_variant_id,
        amount=form.amount,
        expiration_date=form.expiration_date,
        type=form.type,
        name=form.name,
        min_quantity=form.min_quantity,
        max_quantity=form.max_quantity,
        max_uses_per_user=form.max_uses_per_user,
    )


# Route to get all active coupons with pagination


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[PaginatorResultSchema[CouponResponse]],
)
async def get_all_coupon_route(
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginatorResultSchema]:
    total_coupon = await Pagination.paginate(Coupon, input_data, CouponResponse)
    return CommonResponseSchema(
        message="Coupon fetched successfully", data=total_coupon
    )


# Route to get a single coupon by ID


@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon_by_id(coupon_id: UUID, db: database):
    return await get_coupon_by_id_controller(coupon_id, db)


# Route to update a coupon


@router.put("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(db: database, coupon_id: UUID, form: CouponSchema):
    return await update_coupon_controller(
        db=db,
        coupon_id=coupon_id,
        amount=form.amount,
        expiration_date=form.expiration_date,
        type=form.type,
        name=form.name,
        min_quantity=form.min_quantity,
        max_quantity=form.max_quantity,
        max_uses_per_user=form.max_uses_per_user,
    )


# Route to delete a coupon


@router.delete("/{coupon_id}", response_model=CouponResponse)
async def delete_coupon(coupon_id: UUID, db: database):
    return await delete_coupon_controller(coupon_id, db)

