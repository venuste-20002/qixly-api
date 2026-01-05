from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from src.controllers.wishlist_controller import WishlistController
from src.database import database
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.schemas.card_schema import CardResponse
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.wishlist_schema import CreateWishlistSchema, WishlistResponse
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(
    prefix="/wishlists",
    tags=["Wishlist"],
    dependencies=[Depends(auth)],
)


@router.get("/me", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.WISHLIST, PermissionActivity.READ),
)
async def get_wishlists(
    request: Request,
    db: database,
) -> CommonResponseSchema:

    user_info = request.session["user"]
    get_wishlist = await WishlistController(
        database=db,
        user_uuid=user_info.get("id"),
    ).get_wishlist()

    return CommonResponseSchema(
        message="Wishlist fetched successfully",
        data=[
            WishlistResponse(
                **data.model_dump(), card=CardResponse(**data.card.model_dump())
            )
            for data in get_wishlist or []
        ],
    )


@router.post("", status_code=status.HTTP_201_CREATED)
@authorized(permission__(PermissionsResources.WISHLIST, PermissionActivity.WRITE))
async def add_wishlists(
    request: Request,
    input_data: CreateWishlistSchema,
    db: database,
) -> CommonResponseSchema[WishlistResponse]:
    user_info = request.session["user"]

    create_new_wishlist = await WishlistController(
        database=db, user_uuid=user_info.get("id"), **input_data.model_dump()
    ).add_to_wishlist()

    return CommonResponseSchema(
        message="Wishlist added successfully",
        data=WishlistResponse(
            **create_new_wishlist.model_dump(),
            card=CardResponse(**create_new_wishlist.card.model_dump())
        ),
    )


@router.delete("/{wishlist_item_uuid}", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.WISHLIST, PermissionActivity.WRITE),
)
async def delete_wishlist_item(
    request: Request,
    wishlist_item_uuid: UUID,
    db: database,
) -> CommonResponseSchema:
    user_info = request.session["user"]
    await WishlistController(
        database=db, user_uuid=user_info.get("id")
    ).delete_single_wishlist(wishlist_item_uuid)

    return CommonResponseSchema(message="Wishlist item deleted successfully", data={})


@router.delete("", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.WISHLIST, PermissionActivity.WRITE),
)
async def delete_all_wishlist_items(
    request: Request,
    db: database,
) -> CommonResponseSchema:
    user_info = request.session["user"]

    await WishlistController(
        database=db, user_uuid=user_info.get("id")
    ).delete_wishlist()

    return CommonResponseSchema(
        message="Wishlist flushed successfully",
        data={},
    )
