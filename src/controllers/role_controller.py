from typing import Optional

from fastapi import status
from sqlmodel import Session, select

from src.models.authentication_model import Permissions, RolePermissions, Roles
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch


class RolesController:
    def __init__(
        self,
        role_code: Optional[int] = None,
        database: Optional[Session] = None,
    ) -> None:
        self.role_code = role_code
        self.database = database

    async def get_role(self):
        get_role = await Fetch(
            Roles, "code", self.role_code, self.database
        ).get_single_value()

        if not get_role:
            raise AppError("Role not found", status.HTTP_404_NOT_FOUND)

        return get_role

    async def get_all_role_permissions(self):
        get_role_permissions = await Fetch(
            RolePermissions, "role", self.role_code, self.database
        ).get_all_value()

        if not get_role_permissions:
            raise AppError("Role Permission not found", status.HTTP_404_NOT_FOUND)

        return get_role_permissions

    async def get_role_permissions(self):
        get_role_permissions = await self.get_all_role_permissions()
        list_permissions = [data.permission for data in get_role_permissions or []]

        return list_permissions

    async def create_role(self, input_data):
        get_all_roles = self.database.exec(select(Roles)).all()

        role_codes = set(role.code for role in get_all_roles)
        role_name = [role.name for role in get_all_roles]

        if input_data.name in role_name:
            raise AppError(
                detail=f"Role with name {input_data.name} already exists",
                status_code=status.HTTP_409_CONFLICT,
            )

        create_new_role = Roles(
            code=max(role_codes) + 1,
            name=input_data.name,
            description=input_data.description,
        )

        self.database.add(create_new_role)
        self.database.commit()
        self.database.refresh(create_new_role)

        return create_new_role

    async def assign_role_permission(self, input_data):
        await self.get_role()

        for data in input_data:
            is_check_permission = await Fetch(
                Permissions, "name", data, self.database
            ).get_single_value()

            if not is_check_permission:
                raise AppError(
                    detail=f"Permission with name {data} not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            is_check_role_permission = await Fetch(
                table_name=RolePermissions,
                table_field="role",
                value=self.role_code,
                session=self.database,
                where=[(getattr(RolePermissions, "permission") == data)],
            ).get_single_value()

            if is_check_role_permission:
                raise AppError(
                    detail=f"Role with permission already exists",
                    status_code=status.HTTP_409_CONFLICT,
                )

            create_role_permission = RolePermissions(
                role=self.role_code,
                permission=data,
            )
            self.database.add(create_role_permission)

        self.database.commit()

        return input_data
