from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from src.controllers.users_controller import UsersController, get_all_users_controller
from src.database import database
from src.helpers.common_actions import CommonUsedActions
from src.helpers.paginator import Paginate, PaginationResponse
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.authentication_model import Users
from src.schemas.common_schema import ChangeStatusSchema, CommonResponseSchema
from src.schemas.users_schema import (
    GetUserScope,
    UserDataSchema,
    UserFullDataSchema,
    UserProfileSchema,
    UserUpdateSchema,
)
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(auth)])


@router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[UserProfileSchema],
)
@authorized(permission__(PermissionsResources.USER, PermissionActivity.READ))
async def user_profile(
    request: Request, db: database
) -> CommonResponseSchema[UserProfileSchema]:
    payload = request.session["user"]
    users_profile_data = UsersController(db, payload.get("id"))
    user_profile_data = await users_profile_data.get_user()
    user_scopes = await users_profile_data.get_user_scopes()

    return CommonResponseSchema(
        status="success",
        message="User profile fetched successfully",
        data=UserProfileSchema(
            User=UserDataSchema(**user_profile_data.model_dump()), Scopes=user_scopes
        ),
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
@authorized(permission__(PermissionsResources.USERS, PermissionActivity.READ))
async def get_all_users(
    _: Request,
    db: database,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginationResponse[UserFullDataSchema]]:
    total_user = await get_all_users_controller(db, is_active, input_data, search)
    return CommonResponseSchema(
        status="success", message="Users fetched successfully", data=total_user
    )


@router.get(
    "/{uuid}",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
)
@authorized(permission__(PermissionsResources.USER, PermissionActivity.READ))
async def get_single_users(
    _: Request, uuid: UUID, db: database
) -> CommonResponseSchema:
    single_user = UsersController(db, uuid)
    single_user_data = await single_user.get_user()
    single_user_scopes = await single_user.get_user_scopes()

    return CommonResponseSchema(
        message="Single User fetched successfully",
        data=UserProfileSchema(
            User=UserDataSchema(**single_user_data.model_dump()),
            Scopes=single_user_scopes,
        ),
    )


@router.patch(
    "/{uuid}",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[UserDataSchema],
)
@authorized(permission__(PermissionsResources.USER, PermissionActivity.WRITE))
async def update_single_user_details(
    _: Request,
    uuid: UUID,
    input_data: UserUpdateSchema,
    db: database,
) -> CommonResponseSchema[UserDataSchema]:
    record_update = await CommonUsedActions(
        Users, uuid, db, "User not found"
    ).update_single_record(input_data)
    return CommonResponseSchema(
        message="User updated successfully",
        data=UserDataSchema(**record_update.model_dump()),
    )


@router.patch("/{uuid}/status", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.USERS, PermissionActivity.WRITE))
async def update_single_user_status(
    _: Request,
    uuid: UUID,
    db: database,
    input_data: ChangeStatusSchema,
) -> CommonResponseSchema[UserDataSchema]:
    record = CommonUsedActions(Users, uuid, db)
    record_update_status = await record.change_status(input_data)
    return CommonResponseSchema(
        message="User status updated successfully",
        data=UserDataSchema(**record_update_status.model_dump()),
    )


@router.get(
    "/{uuid}/scopes",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[List[GetUserScope]],
)
@authorized(permission__(PermissionsResources.USERSCOPES, PermissionActivity.READ))
async def get_user_single_scopes(
    _: Request, uuid: UUID, db: database
) -> CommonResponseSchema[List[GetUserScope]]:
    record = await UsersController(db, uuid).get_user_scopes()
    return CommonResponseSchema(message="User Scopes fetched successfully", data=record)


@router.get(
    "/me/permissions",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
)
@authorized(permission__(PermissionsResources.USER, PermissionActivity.READ))
async def get_user_single_permissions(request: Request, db: database):
    user = request.session["user"]["id"]
    record = await UsersController(db, user).get_user_permissions()
    return CommonResponseSchema(
        message="User Permissions fetched successfully",
        data=record,
    )
