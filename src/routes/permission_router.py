from uuid import UUID

from fastapi import APIRouter, Depends, Request

from src.controllers.permissions_controller import PermissionController
from src.database import database
from src.helpers.common_actions import CommonUsedActions
from src.helpers.paginator import Paginate, Pagination, PaginatorResultSchema
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.authentication_model import Permissions
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.permission_schema import PermissionResponse
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
    dependencies=[
        Depends(auth),
    ],
)


@router.get("")
@authorized(
    permission__(PermissionsResources.PERMISSIONS, PermissionActivity.READ),
)
async def get_permissions_all(
    _: Request,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginatorResultSchema[PermissionResponse]]:

    res = await Pagination.paginate(
        Permissions,
        input_data,
        PermissionResponse,
    )
    return CommonResponseSchema(
        message="Permissions fetched successfully",
        data=res,
    )


@router.get("/permissions_groups")
@authorized(
    permission__(PermissionsResources.PERMISSIONS, PermissionActivity.READ),
)
async def get_permission_groups(
    _: Request,
    db: database,
) -> CommonResponseSchema:
    res = PermissionController(db).get_permission_groups()
    return CommonResponseSchema(
        message="Permission groups fetched successfully",
        data=res,
    )


@router.get("/{permission_id}")
@authorized(
    permission__(PermissionsResources.PERMISSIONS, PermissionActivity.READ),
)
async def get_permission(
    _: Request,
    permission_id: UUID,
    db: database,
) -> CommonResponseSchema[PermissionResponse]:
    res = await CommonUsedActions(
        Permissions,
        permission_id,
        db,
        "Permission not found",
    ).get_record()

    return CommonResponseSchema(
        message="Permission fetched successfully",
        data=PermissionResponse(**res.model_dump()),
    )
