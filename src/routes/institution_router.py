from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from pydantic import EmailStr
from sqlmodel import SQLModel

from src.controllers.institution_branch_controller import InstitutionBranchController
from src.controllers.institution_controller import (
    get_all_institutions_controller,
    get_single_institution_controller,
    institution_add_controller,
    update_institution_controller,
)
from src.database import database
from src.helpers.common_actions import CommonUsedActions
from src.helpers.image_uploader import save_image
from src.helpers.paginator import Paginate, PaginationResponse
from src.middlewares.auth import auth
from src.middlewares.role_checker import authorized
from src.models.institutions_model import Institutions
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.institution_branch_schema import GetBranchResponseSchema
from src.schemas.institution_schema import (
    InstitutionCreate,
    InstitutionGetFullSchema,
    InstitutionGetschema,
    InstitutionUpdateSchema,
)
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)

router = APIRouter(
    prefix="/institutions",
    tags=["Institutions"],
    dependencies=[Depends(auth)],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[PaginationResponse[InstitutionGetFullSchema]],
)
@authorized(permission__(PermissionsResources.INSTITUTIONS, PermissionActivity.READ))
async def get_all_institutions(
    _: Request,
    db: database,
    created_date: Optional[datetime] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginationResponse[InstitutionGetFullSchema]]:
    total_institutions = await get_all_institutions_controller(
        db, created_date, is_active, input_data, search
    )
    return CommonResponseSchema(
        message="Institutions fetched successfully",
        data=total_institutions,
    )


@router.get(
    "/{uuid}",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[InstitutionGetFullSchema],
)
@authorized(permission__(PermissionsResources.INSTITUTION, PermissionActivity.READ))
async def get_single_institution(
    _: Request, uuid: UUID, db: database
) -> CommonResponseSchema[InstitutionGetFullSchema]:

    return await get_single_institution_controller(uuid, db)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
@authorized(permission__(PermissionsResources.INSTITUTIONS, PermissionActivity.WRITE))
async def add_institution(
    _: Request,
    db: database,
    email: Annotated[EmailStr, Form(...)],
    address: Annotated[str, Form(...)],
    tin_number: Annotated[str, Form(...)],
    name: Annotated[str, Form(...)],
    image_url: Optional[UploadFile] = File(None),
) -> CommonResponseSchema[InstitutionGetschema]:
    image_link: str = save_image(image_url)

    create_institution = await institution_add_controller(
        InstitutionCreate(
            name=name,
            email=email,
            address=address,
            tin_number=tin_number,
            image_url=image_link,
        ),
        db,
    )
    return create_institution


@router.put("/{uuid}", status_code=status.HTTP_202_ACCEPTED)
@authorized(permission__(PermissionsResources.INSTITUTIONS, PermissionActivity.WRITE))
async def update_institution(
    _: Request,
    uuid: UUID,
    db: database,
    image_url: Optional[UploadFile] = None,
    address: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
) -> CommonResponseSchema[InstitutionGetschema]:
    image_link = save_image(image_url)
    update_institution_ = await update_institution_controller(
        uuid=uuid,
        input_data=InstitutionUpdateSchema(
            name=name, address=address, image_url=image_link
        ),
        db=db,
    )
    return update_institution_


class InstitutionStatusSchema(SQLModel):
    is_active: bool


@router.patch("/{uuid}/status", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.INSTITUTIONS, PermissionActivity.WRITE))
async def update_single_institution_status(
    _: Request,
    db: database,
    uuid: UUID,
    input_data: InstitutionStatusSchema,
) -> CommonResponseSchema[InstitutionGetschema]:
    record = CommonUsedActions(Institutions, uuid, db, "Institution not found")
    updated_record = await record.change_status(input_data)

    return CommonResponseSchema(
        message="Institution status updated", data=updated_record
    )


@router.get("/{institution_uuid}/branches", status_code=status.HTTP_200_OK)
@authorized(permission__(PermissionsResources.BRANCHES, PermissionActivity.READ))
async def get_all_branches(
    _: Request, institution_uuid: UUID, db: database
) -> CommonResponseSchema[List[GetBranchResponseSchema]]:
    get_all_institution_branch_data = await InstitutionBranchController(
        db, institution_uuid
    ).get_all_branches()
    return CommonResponseSchema(
        message="Branches fetched successfully",
        data=[
            GetBranchResponseSchema(**data.model_dump())
            for data in get_all_institution_branch_data
        ],
    )


@router.get(
    "/{institution_uuid}/branches/{branch_uuid}", status_code=status.HTTP_200_OK
)
@authorized(permission__(PermissionsResources.BRANCHES, PermissionActivity.READ))
async def get_single_branch(
    _: Request,
    institution_uuid: UUID,
    branch_uuid: UUID,
    db: database,
) -> CommonResponseSchema[GetBranchResponseSchema]:

    get_single_institution_branch_data = await InstitutionBranchController(
        db, institution_uuid, branch_uuid
    ).get_single_institution_branch()

    return CommonResponseSchema(
        message="Branch fetched successfully",
        data=GetBranchResponseSchema(**get_single_institution_branch_data.model_dump()),
    )
