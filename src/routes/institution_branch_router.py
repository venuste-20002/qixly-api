from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from src.controllers.institution_branch_controller import (
    InstitutionBranchController,
    get_all_branches_controller,
)
from src.database import database
from src.helpers.common_actions import CommonUsedActions
from src.helpers.paginator import Paginate, PaginationResponse
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.institutions_model import Branches
from src.schemas.common_schema import ChangeStatusSchema, CommonResponseSchema
from src.schemas.institution_branch_schema import (
    CreateInstitutionBranchSchema,
    GetBranchFullResponseSchema,
    GetBranchResponseSchema,
    InstitutionResponseSchema,
    UpdateBranchSchema,
)
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)
from src.utils.fetcher import Fetcher

router = APIRouter(prefix="/branches", tags=["Branches"], dependencies=[Depends(auth)])

error_message = "Branch not found"


@router.get("", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.BRANCHES, PermissionActivity.READ),
)
async def get_all_branches(
    _: Request,
    db: database,
    institution: list[UUID] = Query(None),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginationResponse[GetBranchFullResponseSchema]]:
    total_branches = await get_all_branches_controller(
        db, input_data, institution, is_active, search
    )
    return CommonResponseSchema(
        message="Branches fetched successfully",
        data=total_branches,
    )


@router.get("/{uuid}", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.BRANCHES, PermissionActivity.READ),
)
async def get_single_branch(
    _: Request, uuid: UUID, db: database
) -> CommonResponseSchema[GetBranchFullResponseSchema]:
    get_branch = Fetcher(
        database=db,
        table=(Branches,),
        where=(Branches.id == uuid,),
        error=error_message,
    ).get_one()
    return CommonResponseSchema(
        message="Branch fetched successfully",
        data=GetBranchFullResponseSchema(
            **get_branch.model_dump(),
            institution=InstitutionResponseSchema(
                **get_branch.institution.model_dump(),
            ),
        ),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
@authorized(
    permission__(PermissionsResources.BRANCHES, PermissionActivity.WRITE),
)
async def create_branch(
    _: Request, input_data: CreateInstitutionBranchSchema, db: database
) -> CommonResponseSchema[GetBranchResponseSchema]:
    add_branch = await InstitutionBranchController(
        db, input_data.institution_uuid
    ).add_branch(input_data)
    return CommonResponseSchema(
        message="Branch added successfully",
        data=GetBranchResponseSchema(**add_branch.model_dump()),
    )


@router.patch("/{branch_uuid}", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.BRANCHES, PermissionActivity.WRITE),
)
async def update_branch(
    _: Request,
    branch_uuid: UUID,
    input_data: UpdateBranchSchema,
    db: database,
) -> CommonResponseSchema[GetBranchResponseSchema]:
    updated_branch = await CommonUsedActions(
        Branches, branch_uuid, db, error_message
    ).update_single_record(input_data)
    return CommonResponseSchema(
        message="Branch updated successfully",
        data=GetBranchResponseSchema(**updated_branch.model_dump()),
    )


@router.patch("/{branch_uuid}/status", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.BRANCHES, PermissionActivity.WRITE),
)
async def update_branch_status(
    _: Request,
    branch_uuid: UUID,
    db: database,
    input_data: ChangeStatusSchema,
) -> CommonResponseSchema:
    update_status_branch = await CommonUsedActions(
        Branches, branch_uuid, db, error_message
    ).change_status(input_data)
    return CommonResponseSchema(
        message="Branch status updated successfully",
        data=GetBranchResponseSchema(**update_status_branch.model_dump()),
    )


@router.delete("/{uuid}", status_code=status.HTTP_200_OK)
@authorized(
    permission__(PermissionsResources.BRANCHES, PermissionActivity.DELETE),
)
async def delete_single_branch(
    _: Request,
    uuid: UUID,
    db: database,
):
    delete_single = await CommonUsedActions(
        Branches,
        uuid,
        db,
        error_message,
    ).delete_record()
    return CommonResponseSchema(
        message="Branch deleted successfully",
        data=GetBranchResponseSchema(**delete_single.model_dump()),
    )
