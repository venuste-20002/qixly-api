from typing import Generic, Optional, TypeVar
from uuid import UUID

from fastapi import status
from sqlmodel import Session, select

from src.models.authentication_model import Roles, Users, UserScope
from src.models.institutions_model import Institutions
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.institution_branch_schema import (
    GetUserScope,
    UserDataResponseSchema,
    UserDataSchema,
)
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch

T = TypeVar("T", bound=Session)


class InstitutionMembersController(Generic[T]):
    def __init__(
        self,
        database: T,
        member_uuid: Optional[UUID] = None,
        institution_uuid: Optional[UUID] = None,
    ):
        self.database = database
        self.institution_uuid = institution_uuid
        self.member_uuid = member_uuid

    async def get_institution(self):
        get_institution_response = await Fetch(
            Institutions, "id", self.institution_uuid,self.database
        ).get_single_value()

        if not get_institution_response:
            raise AppError(
                "Institution not Found",
                status.HTTP_404_NOT_FOUND,
            )
        return get_institution_response

    async def get_all_member(self):
        await self.get_institution()

        get_members = (
            select(UserScope, Users)
            .join(Users, getattr(Users, "id") == getattr(UserScope, "user_id"))
            .where(getattr(UserScope, "institution_id") == self.institution_uuid)
            .where(getattr(UserScope, "is_deleted") == False)
        )
        return self.database.exec(get_members).all()

    async def get_single_member(self):
        await self.get_institution()

        get_single_member_scopes = (
            select(UserScope)
            .where(getattr(UserScope, "institution_id") == self.institution_uuid)
            .where(getattr(UserScope, "user_id") == self.member_uuid)
            .where(getattr(UserScope, "is_deleted") == False)
        )

        single_member_data = await Fetch(
            Users, "id", self.member_uuid, self.database
        ).get_single_value()

        single_member_data_scopes = self.database.exec(get_single_member_scopes).all()

        if not single_member_data:
            raise AppError("Member not Found", status.HTTP_404_NOT_FOUND)

        return single_member_data, single_member_data_scopes

    async def get_all_members_data(self):
        members = await self.get_all_member()
        list_members = []
        for scope, user in members:
            list_members.append(
                UserDataSchema(
                    user=UserDataResponseSchema(**user.model_dump()),
                    userscope=[GetUserScope(**scope.model_dump())],
                )
            )
        return CommonResponseSchema(
            message="Members fetched successfully", data=list_members
        )

    async def get_single_member_data(self):
        member_data, member_data_scopes = await self.get_single_member()

        return UserDataSchema(
            user=UserDataResponseSchema(**member_data.model_dump()),
            userscope=[
                GetUserScope(**scope.model_dump())
                for scope in member_data_scopes
            ],
        )

    async def update_member_role(self, input_data):
        await self.get_institution()

        get_single_member = (
            select(UserScope)
            .where(getattr(UserScope, "user_id") == self.member_uuid)
            .where(getattr(UserScope, "institution_id") == self.institution_uuid)
        )
        single_member_data = self.database.exec(get_single_member).first()
        if not single_member_data:
            raise AppError("Member not Found", status.HTTP_404_NOT_FOUND)

        get_single_role = Fetch(Roles, "code", input_data.role_code,self.database)
        single_role_data = await get_single_role.get_single_value()

        if not single_role_data:
            raise AppError("Role not Found", status.HTTP_404_NOT_FOUND)

        single_member_data.code = input_data.role_code

        self.database.add(single_member_data)
        self.database.commit()
        self.database.refresh(single_member_data)

        return single_member_data
