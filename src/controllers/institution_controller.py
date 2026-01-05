from typing import TypeVar

from fastapi import status
from sqlmodel import Session

from src.database import database
from src.helpers.common_actions import CommonUsedActions
from src.helpers.paginator import PaginationResponse, PaginatorQuery
from src.models.institutions_model import Institutions
from src.schemas.card_schema import CardResponse
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.institution_branch_schema import GetBranchResponseSchema
from src.schemas.institution_schema import (
    InstitutionCreate,
    InstitutionGetFullSchema,
    InstitutionGetschema,
)
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch

T = TypeVar("T")


async def get_institution(table, column, value, database_):
    get_value = await Fetch(table, column, value, database_).get_single_value()
    return get_value


async def institution_add_controller(input_data: InstitutionCreate, db: database):
    is_check_if_institution_exists = await get_institution(
        Institutions, "name", input_data.name, db
    )

    is_check_if_email_exists = await get_institution(
        Institutions, "email", input_data.email, db
    )

    if is_check_if_institution_exists or is_check_if_email_exists:
        raise AppError("Institution already exists", status.HTTP_409_CONFLICT)

    add_institution = Institutions(**input_data.model_dump())

    db.add(add_institution)
    db.commit()
    db.refresh(add_institution)

    return CommonResponseSchema(
        message="Institution Added Successfully",
        data=InstitutionGetschema(**add_institution.model_dump()),
    )


async def update_institution_controller(uuid, input_data: T, db: Session):
    is_check_if_institution_exists = await get_institution(Institutions, "id", uuid, db)
    if not is_check_if_institution_exists:
        raise AppError("Institution does not exist", status.HTTP_404_NOT_FOUND)

    get_user_name = await get_institution(Institutions, "name", input_data.name, db)
    if get_user_name:
        raise AppError("Name already exists", status.HTTP_409_CONFLICT)

    institution_update = await CommonUsedActions(
        Institutions,
        uuid,
        db,
        "Institution not found",
    ).update_single_record(input_data)

    return CommonResponseSchema(
        message="Institution Update Successfully",
        data=InstitutionGetschema(**institution_update.model_dump()),
    )


async def get_single_institution_controller(uuid, db):
    get_single_institution_data = await get_institution(Institutions, "id", uuid, db)

    if not get_single_institution_data:
        raise AppError("No Institution Found", status_code=status.HTTP_404_NOT_FOUND)

    return CommonResponseSchema(
        message="Institution fetched successfully",
        data=InstitutionGetFullSchema(
            institution=InstitutionGetschema(
                **get_single_institution_data.model_dump()
            ),
            branches=[
                GetBranchResponseSchema(**data.model_dump())
                for data in get_single_institution_data.branch or []
            ],
            cards=[
                CardResponse(**data.model_dump())
                for data in get_single_institution_data.cards or []
            ],
        ),
    )


async def get_all_institutions_controller(
    session: Session, created_date, is_active, input_data, search
) -> PaginationResponse[InstitutionGetFullSchema]:
    filter_ = ()

    if created_date:
        filter_ += (Institutions.created_at == created_date,)

    if is_active:
        filter_ += (Institutions.is_active == is_active,)

    total_institutions, data = await PaginatorQuery.paginate(
        Institutions,
        input_data,
        session=session,
        search=search,
        filters=filter_,
    )

    return PaginationResponse(
        pagination=total_institutions,
        data=[
            InstitutionGetFullSchema(
                institution=InstitutionGetschema(**d.model_dump()),
                branches=[
                    GetBranchResponseSchema(**branch.model_dump())
                    for branch in d.branch
                ],
                cards=[CardResponse(**card.model_dump()) for card in d.cards],
            )
            for d in data
        ],
    )
