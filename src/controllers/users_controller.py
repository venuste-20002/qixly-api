from typing import List

from fastapi import status

from src.helpers.paginator import PaginationResponse, PaginatorQuery
from src.models.authentication_model import (
    RolePermissions,
    Roles,
    Users,
    UserScope,
    UserScopeEnum,
)
from src.models.institutions_model import Branches, Institutions
from src.schemas.institution_branch_schema import GetBranchResponseSchema
from src.schemas.roles_schema import GetRoles
from src.schemas.users_schema import (
    GetUserScope,
    InstitutionResponseSchema,
    UserFullDataSchema,
    UserScopeResponseSchema,
    UserScopeSchema,
)
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch, Fetcher


class UsersController:
    def __init__(self, database, uuid):
        self.database = database
        self.uuid = uuid

    async def get_user(self):
        get_current_user = await Fetch(
            Users, "id", self.uuid, self.database
        ).get_single_value()

        if not get_current_user:
            raise AppError("User not Found", status.HTTP_404_NOT_FOUND)

        return get_current_user

    async def get_user_scopes(self) -> List[GetUserScope]:
        await self.get_user()
        user_scopes = await Fetch(
            UserScope, "user_id", self.uuid, self.database
        ).get_all_value()

        return [
            GetUserScope(
                **data.model_dump(),
                institution=(
                    InstitutionResponseSchema(**data.institution.model_dump())
                    if data.institution
                    else None
                ),
                branches=(
                    GetBranchResponseSchema(**data.branches.model_dump())
                    if data.branches
                    else None
                ),
                role=GetRoles(**data.roles.model_dump())
            )
            for data in user_scopes or []
        ]


    async def get_role(self, role_code: int):
        get_current_role = await Fetch(
            Roles, "code", role_code, self.database
        ).get_single_value()

        if not get_current_role:
            raise AppError("Role not Found", status.HTTP_404_NOT_FOUND)

        return get_current_role

    async def get_user_permissions(self):
        get_user = await self.get_user()
        get_user_scope = get_user.userscope

        user_permissions = set()

        for scope in get_user_scope:
            if scope.role_code == 10:
                return {"all"}

            get_role_permissions = Fetcher(
                database=self.database,
                table=(RolePermissions,),
                where=(RolePermissions.role == scope.role_code,),
                error="Role Permissions not found",
            ).get_all()

            [
                user_permissions.add(permission.permission)
                for permission in get_role_permissions
            ]

        return user_permissions

    async def add_new_scope(self, input_data: UserScopeSchema):
        await self.get_user()
        await self.get_role(input_data.role_code)

        get_scope = await Fetch(
            table_name=UserScope,
            table_field="user_id",
            value=self.uuid,
            session=self.database,
            where=[
                (getattr(UserScope, "role_code") == input_data.role_code),
                (getattr(UserScope, "institution_id") == input_data.institution_id),
                (getattr(UserScope, "branch_id") == input_data.branch_id),
            ],
        ).get_single_value()

        if get_scope:
            raise AppError("User Scope already exists", status.HTTP_409_CONFLICT)

        if input_data.institution_id:
            get_institution = Fetch(
                Institutions, "id", input_data.institution_id, self.database
            )
            check_institution = await get_institution.get_single_value()

            if not check_institution:
                raise AppError("No Institution Found", status.HTTP_404_NOT_FOUND)

        if input_data.branch_id:
            get_branch = Fetch(Branches, "id", input_data.branch_id, self.database)
            check_branch = await get_branch.get_single_value()

            if not check_branch:
                raise AppError("No Branch Found", status.HTTP_404_NOT_FOUND)

        if input_data.branch_id:
            scope_type = UserScopeEnum.BRANCH
        elif input_data.institution_id:
            scope_type = UserScopeEnum.INSTITUTION
        else:
            scope_type = UserScopeEnum.SYSTEM

        user_scope = UserScope(**input_data.model_dump(), scope_type=scope_type)

        self.database.add(user_scope)
        self.database.commit()
        self.database.refresh(user_scope)

        return user_scope


async def get_all_users_controller(db, is_active, input_data, search):
    filter_ = ()
    if is_active is not None:
        filter_ += (Users.is_active == is_active,)

    total_users_pagination_data, total_user_data = await PaginatorQuery.paginate(
        Users,
        input_data=input_data,
        session=db,
        search=search,
        filters=filter_,
    )
    return PaginationResponse(
        pagination=total_users_pagination_data,
        data=[
            UserFullDataSchema(
                **d.model_dump(),
                scopes=[
                    UserScopeResponseSchema(**user.model_dump())
                    for user in d.userscope or []
                ]
            )
            for d in total_user_data
        ],
    )
