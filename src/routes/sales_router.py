from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from src.controllers.sales_controller import (
    create_sales_from_cart_controller,
    create_variant_sale_controller,
    get_all_sales_items_controller
)
from src.database import database
from src.helpers.paginator import (
    Paginate,
    Pagination,
    PaginationResponse,
    PaginatorResultSchema,
)
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.sales_model import SalesItem, SaleStatus
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.sales_schema import (
    SalesCart,
    SalesFullItemsResponse,
    SalesItemsResponse,
    SalesResult,
)
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(tags=["Sales"], prefix="/sales", dependencies=[Depends(auth)])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[PaginationResponse[SalesFullItemsResponse]],
)
@authorized(
    permission__(PermissionsResources.SALES, PermissionActivity.READ),
)
async def get_all_sales_items_route(
    _: Request,
    db: database,
    user: list[UUID] = Query(None),
    cart: list[UUID] = Query(None),
    card_variant: list[UUID] = Query(None),
    shared: Optional[bool] = None,
    viewed: Optional[bool] = None,
    status: Optional[SaleStatus] = None,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema:

    total_sales_items = await get_all_sales_items_controller(
        db=db,
        user=user,
        cart=cart,
        card_variant=card_variant,
        shared=shared,
        viewed=viewed,
        status_=status,
        input_data=input_data,
    )

    return CommonResponseSchema(
        message="Sales items fetched successfully", data=total_sales_items
    )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[PaginatorResultSchema[SalesItemsResponse]],
)
@authorized(
    permission__(PermissionsResources.SALE, PermissionActivity.READ),
)
async def get_all_sales_items_route_me(
    request: Request,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginatorResultSchema]:
    user_id = request.session["user"]["id"]
    total_sales_items = await Pagination.paginate(
        SalesItem,
        input_data,
        SalesItemsResponse,
        filters=(SalesItem.user_id == user_id,),
    )
    return CommonResponseSchema(
        message="Sales items fetched successfully", data=total_sales_items
    )


@router.get(
    "/{sales_id}",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[SalesFullItemsResponse],
)
@authorized(
    permission__(PermissionsResources.SALE, PermissionActivity.READ),
)
async def get_single_sales_item(
    request: Request,
    db: database,
    sales_id: UUID,
) -> CommonResponseSchema[SalesFullItemsResponse]:
    user_id = request.session["user"]["id"]
    get_single_sale = await get_single_sale_item(db, sales_id, user_id)
    return CommonResponseSchema(
        message="Sales item fetched successfully", data=get_single_sale
    )


@router.post(
    "/variant",
    status_code=status.HTTP_201_CREATED,
)
@authorized(
    permission__(PermissionsResources.SALE, PermissionActivity.WRITE),
)
async def create_variant(
    request: Request,
    db: database,
    form: SalesResult,
):
    user = request.session["user"]
    return create_variant_sale_controller(
        input_data=form,
        db=db,
        user=user,
    )


@router.post(
    "/cart",
    status_code=status.HTTP_201_CREATED,
)
@authorized(
    permission__(PermissionsResources.SALE, PermissionActivity.WRITE),
)
async def create_sales_from_cart(
    request: Request,
    db: database,
    form: SalesCart,
):
    user_id = request.session["user"]
    return create_sales_from_cart_controller(
        user_id=user_id, coupon_codes=form.coupon_codes, db=db, input_data=form
    )
