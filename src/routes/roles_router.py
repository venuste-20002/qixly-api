from fastapi import APIRouter, Depends, Request, status

from src.controllers.role_controller import RolesController
from src.database import database
from src.helpers.paginator import Paginate, Pagination, PaginatorResultSchema
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.authentication_model import Roles
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.roles_schema import GetRolePermissions, GetRoles, RoleCreateSchema
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(prefix="/roles", tags=["Roles"], dependencies=[Depends(auth)])


@router.get("", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.ROLES, PermissionActivity.READ))
async def get_all_roles(
    _: Request,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginatorResultSchema[GetRoles]]:
    get_all_roles__ = await Pagination.paginate(Roles, input_data, GetRoles)
    return CommonResponseSchema(
        message="Roles fetched successfully", data=get_all_roles__
    )


@router.get("/{role_code}", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.ROLES, PermissionActivity.READ))
async def get_single_role(
    _: Request, role_code: int, db: database
) -> CommonResponseSchema[GetRoles]:

    get_single_role_ = await RolesController(role_code, db).get_role()

    return CommonResponseSchema(
        message="Role fetched successfully",
        data=GetRoles(**get_single_role_.model_dump()),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
@authorized("ROLES:WRITE")
async def create_role(
    _: Request, db: database, input_data: RoleCreateSchema
) -> CommonResponseSchema[GetRoles]:

    create_new_role = await RolesController(database=db).create_role(input_data)

    return CommonResponseSchema(
        message="Role created successfully",
        data=GetRoles(**create_new_role.model_dump()),
    )


@router.get("/{role_code}/permissions", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.ROLES, PermissionActivity.READ),
)
async def get_role_permissions(
    _: Request,
    db: database,
    role_code: int,
) -> CommonResponseSchema[GetRolePermissions]:
    get_single_role_permission = await RolesController(
        role_code, db
    ).get_role_permissions()

    return CommonResponseSchema(
        message="Role Permissions fetched successfully",
        data=GetRolePermissions(
            role=role_code,
            permission=get_single_role_permission,
        ),
    )


@router.post("/{role_code}/permissions", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.ROLES, PermissionActivity.WRITE))
async def assign_role_permissions(
    _: Request,
    role_code: int,
    db: database,
    input_data: list[str],
) -> CommonResponseSchema:

    assign_role_permission = await RolesController(
        database=db,
        role_code=role_code,
    ).assign_role_permission(input_data)

    return CommonResponseSchema(
        message="Role Permissions assigned successfully",
        data=assign_role_permission,
    )
