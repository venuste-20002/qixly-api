from typing import Optional
from uuid import UUID

from fastapi import status
from sqlmodel import col, select

from src.helpers.common_actions import CommonUsedActions
from src.helpers.paginator import PaginationResponse, PaginatorQuery
from src.models.institutions_model import Branches, Institutions
from src.schemas.institution_branch_schema import (
    GetBranchFullResponseSchema,
    InstitutionResponseSchema,
)
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch


class InstitutionBranchController:
    def __init__(
        self, database, institution_uuid, branch_uuid: Optional[UUID] = None
    ) -> None:
        self.database = database
        self.institution_uuid = institution_uuid
        self.branch_uuid = branch_uuid

    async def get_institution(self):
        get_institution_response = await Fetch(
            Institutions, "id", self.institution_uuid, self.database
        ).get_single_value()

        if not get_institution_response:
            raise AppError(
                "Institution not Found",
                status.HTTP_404_NOT_FOUND,
            )
        return get_institution_response

    async def get_all_branches(self):
        await self.get_institution()

        get_single_institution_branches_data = await Fetch(
            Branches, "institution_id", self.institution_uuid, self.database
        ).get_all_value()
        if not get_single_institution_branches_data:
            raise AppError("No Branches Found", status_code=status.HTTP_404_NOT_FOUND)

        return get_single_institution_branches_data

    async def get_single_institution_branch(self):
        await self.get_institution()

        get_single_institution_data = (
            select(Branches)
            .where(getattr(Branches, "id") == self.branch_uuid)
            .where(getattr(Branches, "institution_id") == self.institution_uuid)
            .where(getattr(Branches, "is_deleted") == False)
        )
        get_single_institution_branch = self.database.exec(
            get_single_institution_data
        ).first()

        return get_single_institution_branch

    async def add_branch(self, input_data):
        await self.get_institution()

        get_branch = await Fetch(
            Branches, "email", input_data.email, self.database
        ).get_single_value()

        if get_branch:
            raise AppError(
                "Branch already exists",
            )

        add_branch_data = Branches(
            **input_data.model_dump(),
            institution_id=self.institution_uuid,
        )

        self.database.add(add_branch_data)
        self.database.commit()
        self.database.refresh(add_branch_data)

        return add_branch_data

    async def update_branch(self, input_data):
        await self.get_institution()

        updated_branch = await CommonUsedActions(
            Branches, self.branch_uuid, self.database, "Branch not found"
        ).update_single_record(input_data)

        return updated_branch


async def get_all_branches_controller(db, input_data, institution, is_active, search):
    filters = ()

    if is_active is not None:
        filters += (Branches.is_active == is_active,)
    if institution:
        filters += (col(Branches.institution_id).in_(institution),)

    result, data = await PaginatorQuery.paginate(
        Branches,
        input_data,
        db,
        search=search,
        filters=filters,
    )
    return PaginationResponse(
        pagination=result,
        data=[
            GetBranchFullResponseSchema(
                **d.model_dump(),
                institution=InstitutionResponseSchema(
                    **d.institution.model_dump(),
                ),
            )
            for d in data
        ],
    )
