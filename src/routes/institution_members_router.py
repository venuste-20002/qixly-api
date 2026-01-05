from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from src.controllers.institution_members_controller import InstitutionMembersController
from src.database import database
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.institution_branch_schema import GetUserScope, UserDataSchema
from src.schemas.institution_schema import UpdateInstitutionMemberRoleSchema
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(
    prefix="/institutions/{institution_uuid}/users",
    tags=["Institutions"],
    dependencies=[Depends(auth)],
)


@router.get("", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.MEMBERS, PermissionActivity.READ))
async def get_all_members(
    _: Request, institution_uuid: UUID, db: database
) -> CommonResponseSchema[List[UserDataSchema]]:
    return await InstitutionMembersController(
        institution_uuid=institution_uuid, database=db
    ).get_all_members_data()


@router.get("/{member_uuid}", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.MEMBERS, PermissionActivity.READ))
async def get_single_member(
    _: Request, institution_uuid: UUID, member_uuid: UUID, db: database
) -> CommonResponseSchema[UserDataSchema]:
    single_institution_data = await InstitutionMembersController(
        institution_uuid=institution_uuid, database=db, member_uuid=member_uuid
    ).get_single_member_data()
    return CommonResponseSchema(
        message="Member fetched successfully", data=single_institution_data
    )


@router.patch("/{member_uuid}/roles", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.MEMBERS, PermissionActivity.WRITE))
async def update_member_roles(
    _: Request,
    institution_uuid: UUID,
    member_uuid: UUID,
    db: database,
    input_data: UpdateInstitutionMemberRoleSchema,
) -> CommonResponseSchema[GetUserScope]:

    role_updated = await InstitutionMembersController(
        institution_uuid=institution_uuid, database=db, member_uuid=member_uuid
    ).update_member_role(input_data)

    return CommonResponseSchema(
        message="Member role updated successfully", data=role_updated
    )
