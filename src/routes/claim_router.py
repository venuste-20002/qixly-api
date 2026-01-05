from uuid import UUID

from fastapi import APIRouter, Depends, Request

from src.controllers.claim_controller import ClaimOrderController
from src.database import database
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.sales_schema import SaleResponseSchema
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(prefix="/claims", tags=["Claim"], dependencies=[Depends(auth)])


@router.post("/{sales_item_id}")
@authorized(
    permission__(PermissionsResources.WISHLIST, PermissionActivity.WRITE),
)
async def claim_sale(
    _: Request,
    sales_item_id: UUID,
    db: database,
) -> CommonResponseSchema[SaleResponseSchema]:
    res = await ClaimOrderController(sales_item_id, db).claim_order()
    return CommonResponseSchema(
        message="Claim successful",
        data=SaleResponseSchema(**res.model_dump()),
    )
