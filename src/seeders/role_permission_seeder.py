from fastapi import status
from sqlalchemy import Select
from sqlmodel import Session, col, select

from src.database import engine
from src.models.authentication_model import Permissions, RolePermissions, RolesEnum
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionGroup,
    PermissionsResources,
    permission__,
)
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch

role_permissions = {
    RolesEnum.BUYER.value: {"groups": [PermissionGroup.BASIC], "exclude": []},
    RolesEnum.ADMIN.value: {
        "groups": [PermissionGroup.INSTITUTION, PermissionGroup.BRANCH],
        "exclude": [],
    },
    RolesEnum.SYSTEM_USER.value: {
        "groups": [
            PermissionGroup.INSTITUTION,
            PermissionGroup.BRANCH,
        ],
        "exclude": [
            permission__(PermissionsResources.MEMBERS, PermissionActivity.WRITE),
            permission__(PermissionsResources.MEMBERS, PermissionActivity.DELETE),
            permission__(PermissionsResources.INSTITUTION, PermissionActivity.WRITE),
            permission__(PermissionsResources.INSTITUTION, PermissionActivity.DELETE),
            permission__(PermissionsResources.BRANCHES, PermissionActivity.WRITE),
            permission__(PermissionsResources.BRANCHES, PermissionActivity.DELETE),
            permission__(PermissionsResources.CARD, PermissionActivity.DELETE),
            permission__(PermissionsResources.CARD, PermissionActivity.WRITE),
        ],
    },
    RolesEnum.BRANCH_MANAGER.value: {
        "groups": [
            PermissionGroup.BRANCH,
        ],
        "exclude": [
            permission__(PermissionsResources.BRANCHES, PermissionActivity.DELETE),
        ],
    },
}


async def seed_role_permission():
    with Session(engine) as session:
        for role_code, data in role_permissions.items():
            current_permissions_query: Select = select(RolePermissions).where(
                col(RolePermissions.role).__eq__(role_code)
            )
            current_permissions = session.exec(current_permissions_query).all()
            current_permission_names = {rp.permission for rp in current_permissions}

            keep_permissions = set()
            for group in data["groups"]:
                group_permissions = await Fetch(
                    Permissions, "group", group, session
                ).get_all_value()

                if not group_permissions:
                    raise AppError(
                        f"Permissions with group {group} not found",
                        status.HTTP_404_NOT_FOUND,
                    )

                for permission in group_permissions:
                    if permission.name not in data["exclude"]:
                        keep_permissions.add(permission.name)

            for permission_name in keep_permissions - current_permission_names:
                session.add(RolePermissions(role=role_code, permission=permission_name))

            for permission_name in current_permission_names - keep_permissions:
                permission_to_remove_query: Select = (
                    select(RolePermissions)
                    .where(col(RolePermissions.role).__eq__(role_code))
                    .where(col(RolePermissions.permission).__eq__(permission_name))
                )
                permission_to_remove = session.exec(permission_to_remove_query).first()
                if permission_to_remove:
                    session.delete(permission_to_remove)

        session.commit()
