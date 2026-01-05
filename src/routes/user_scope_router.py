from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from src.controllers.users_controller import UsersController
from src.database import database
from src.helpers.common_actions import CommonUsedActions
from src.helpers.paginator import Paginate, Pagination, PaginatorResultSchema
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.authentication_model import UserScope
from src.schemas.common_schema import ChangeStatusSchema, CommonResponseSchema
from src.schemas.users_schema import CreateUserScopeSchema, GetUserScope
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch

router = APIRouter(
    prefix="/users_scope",
    tags=["Users Scope "],
    dependencies=[Depends(auth)],
)


@router.get("", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.USERSCOPES, PermissionActivity.READ))
async def get_all_users_scope(
    _: Request,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginatorResultSchema[GetUserScope]]:
    paginated_result = await Pagination.paginate(UserScope, input_data, GetUserScope)
    return CommonResponseSchema(
        message="User Scopes fetched successfully", data=paginated_result
    )


@router.get("/{uuid}", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.USERSCOPES, PermissionActivity.READ))
async def get_single_users_scope(
    _: Request, uuid: UUID, session: database
) -> CommonResponseSchema[GetUserScope]:
    single_user_scope = await Fetch(UserScope, "id", uuid, session).get_single_value()
    if not single_user_scope:
        raise AppError("User Scope not Found", status.HTTP_404_NOT_FOUND)

    return CommonResponseSchema(
        message="User Scope fetched successfully",
        data=GetUserScope(**single_user_scope.model_dump()),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
@authorized(permission__(PermissionsResources.USERSCOPES, PermissionActivity.WRITE))
async def add_new_users_scope(
    _: Request, input_data: CreateUserScopeSchema, db: database
) -> CommonResponseSchema[GetUserScope]:
    added_scope = await UsersController(db, input_data.user_id).add_new_scope(
        input_data
    )
    return CommonResponseSchema(
        message="Scope added successfully",
        data=GetUserScope(**added_scope.model_dump()),
    )


@router.patch("/{uuid}/status", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.USERSCOPES, PermissionActivity.WRITE))
async def change_users_scope_status(
    _: Request,
    uuid: UUID,
    db: database,
    input_data: ChangeStatusSchema,
) -> CommonResponseSchema[GetUserScope]:
    updated_scope = await CommonUsedActions(
        UserScope,
        uuid,
        db,
        "User Scope not found",
    ).change_status(input_data)
    return CommonResponseSchema(
        message="User scope updated successfully",
        data=GetUserScope(**updated_scope.model_dump()),
    )


@router.delete("/{uuid}", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.USERSCOPES, PermissionActivity.DELETE))
async def delete_single_users_scope(
    _: Request, uuid: UUID, db: database
) -> CommonResponseSchema[GetUserScope]:
    delete_record = await CommonUsedActions(
        UserScope,
        uuid,
        db,
        "User Scope not found",
    ).delete_record()
    return CommonResponseSchema(
        message="User scope deleted successfully",
        data=GetUserScope(**delete_record.model_dump()),
    )
