from typing import List, Optional, Union
from uuid import UUID
from typing import Union

from fastapi import APIRouter, Depends, Query, Request, status

from src.controllers.cart_controller import (
    add_cardvariant_to_cart,
    apply_coupon,
    apply_coupon_all_controller,
    clear_cart,
    get_all_carts_controller,
    get_cart_by_user_id,
    remove_card_variant_from_cart,
    update_cart,
    # calculate_cart_coupon_preview
)
from src.database import database
from src.helpers.paginator import Paginate, PaginationResponse
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.cart_model import CartStatus
from src.schemas.cart_schemas import (
    Cart,
    CartFullResponse,
    CartItem,
    CartItemResponse,
    CartResponse,
    CouponPreviewRequest,
    CouponPreviewResponse
)
from src.schemas.common_schema import CommonResponseSchema
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(tags=["Carts"], prefix="/carts", dependencies=[Depends(auth)])


@router.get("", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.CARTS, PermissionActivity.WRITE),
)
async def get_all_carts(
    _: Request,
    db: database,
    user: list[UUID] = Query(None),
    status_: Optional[CartStatus] = None,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginationResponse[CartFullResponse]]:
    total_carts = await get_all_carts_controller(
        db,
        input_data,
        user,
        status_,
    )

    return CommonResponseSchema(
        message="Carts fetched successfully",
        data=total_carts,
    )


@router.post("/me", status_code=status.HTTP_201_CREATED)
@authorized(
    permission__(PermissionsResources.CART, PermissionActivity.WRITE),
)
async def add_card_variant(
    request: Request,
    db: database,
    form: Cart,
):
    user_id = request.session["user"]["id"]
    return await add_cardvariant_to_cart(
        user_id=user_id,
        card_variant_id=form.card_variant_id,
        quantity=form.quantity,
        db=db,
    )


@router.post("/{user_id}", response_model=CartResponse)
@authorized(
    permission__(PermissionsResources.CART, PermissionActivity.WRITE),
)
async def add_card_variant_to_cart_route(
    _: Request, db: database, user_id: UUID, form: Cart
):
    return await add_cardvariant_to_cart(
        user_id=user_id,
        card_variant_id=form.card_variant_id,
        quantity=form.quantity,
        db=db,
    )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[Union[list[None],CartFullResponse]],
)
@authorized(
    permission__(PermissionsResources.CART, PermissionActivity.READ),
)
async def get_user_carts_me(
    request: Request,
    db: database,

) -> CommonResponseSchema[Union[list[None], CartFullResponse]]:
    user_id = request.session["user"]["id"]
    data = await get_cart_by_user_id(
        user_id=user_id,
        db=db,
    )
    return CommonResponseSchema(
        message="Cart items fetched successfully",
        data=data,
    )


@router.get(
    "/{user_id}/cart_items",
)
@authorized(
    permission__(PermissionsResources.CART, PermissionActivity.READ),
)
async def get_user_carts(
    _: Request,
    user_id: UUID,
    db: database,
) -> CommonResponseSchema[list[CartItemResponse]]:
    data = await get_cart_by_user_id(
        user_id=user_id,
        db=db,
    )
    return CommonResponseSchema(
        message="Cart items fetched successfully",
        data=data,
    )


#
# @router.patch("/{user_id}/{card_variant_id}")
# @authorized(
#     permission__(PermissionsResources.CART, PermissionActivity.WRITE),
# )
# async def update_cart_item(
#     _: Request,
#     user_id: UUID,
#     card_variant_id: UUID,
#     form: CartItem,
#     db: database,
# ):
#     updated_cart = update_cart(
#         user_id=user_id,
#         card_variant_id=card_variant_id,
#         new_quantity=form.quantity,
#         db=db,
#     )
#     return {"status": "success", "cart": updated_cart}


@router.patch("/me/{card_variant_id}")
@authorized(
    permission__(PermissionsResources.CART, PermissionActivity.WRITE),
)
async def update_cart_item_(
    request: Request,
    card_variant_id: UUID,
    form: CartItem,
    db: database,
):
    user_id = request.session["user"]["id"]
    updated_cart = update_cart(
        user_id=user_id,
        card_variant_id=card_variant_id,
        new_quantity=form.quantity,
        db=db,
    )
    return {"status": "success", "cart": updated_cart}


@router.delete("/me/{card_variant_id}")
@authorized(
    permission__(PermissionsResources.CART, PermissionActivity.WRITE),
)
async def remove_from_cart(
    request:Request, 
    card_variant_id: UUID, 
    db: database
):
    user_id= request.session["user"]["id"]
    return await remove_card_variant_from_cart(user_id, card_variant_id, db)


@router.delete("/me")
@authorized(
    permission__(PermissionsResources.CART, PermissionActivity.WRITE),
)
async def delete_cart_route(request: Request, db: database):
    user_id = request.session["user"]["id"]
    return await clear_cart(user_id, db)


@router.post(
    "/me/{cart_item_id}/apply/{coupon}",
)
async def apply_coupon_router(
    request: Request,
    cart_item_id: UUID,
    coupon: str,
    db: database,
) -> CommonResponseSchema:
    user_data = request.session["user"]["id"]
    apply = await apply_coupon(cart_item_id, coupon, db, user_data)

    return CommonResponseSchema(message="Coupon applied successfully", data=apply)


@router.patch(
    "/me/apply/{coupon}",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[CartFullResponse],
)
async def all_apply_coupon_router(coupon: str, db: database, request: Request):
    user_id = request.session["user"]["id"]  
    res = await apply_coupon_all_controller(
        user_id=user_id,
        coupon_codes=[coupon], 
        db=db
    )
    return CommonResponseSchema(message="Coupon applied successfully", data=res)
