from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.controllers.card.category_controller import (
    create_category,
    get_category_by_id,
    update_category,
)
from src.database import database
from src.helpers.paginator import Paginate, PaginationResponse, PaginatorQuery
from src.middlewares.auth import auth
from src.models.card_model import Category
from src.schemas.card_schema import (
    CardResponse,
    CategoryFullResponse,
    CategoryResponse,
    CategorySchemas,
)
from src.schemas.common_schema import CommonResponseSchema

router = APIRouter(tags=["Category"], prefix="/category")


@router.post(
    "",
    response_model=CategoryResponse,
    dependencies=[Depends(auth)],
)
async def create_category_router(category_data: CategorySchemas, db: database):
    return create_category(category_data, db)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[PaginationResponse[CategoryFullResponse]],
)
async def get_all_categories_route(
    db: database,
    search: Optional[str] = None,
    input_data: Paginate = Depends(),
) -> CommonResponseSchema[PaginationResponse[CategoryFullResponse]]:
    total_categories, category_data = await PaginatorQuery.paginate(
        Category, input_data, db, search=search
    )
    return CommonResponseSchema(
        message="Categories fetched successfully",
        data=PaginationResponse(
            pagination=total_categories,
            data=[
                CategoryFullResponse(
                    category=CategoryResponse(**data.model_dump()),
                    cards=[CardResponse(**card.model_dump()) for card in data.cards],
                )
                for data in category_data
            ],
        ),
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_single_category_by_id(category_id: UUID, db: database):
    return get_category_by_id(category_id, db)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(auth)],
)
async def update_category_route(
    category_id: UUID, category_data: CategorySchemas, db: database
):
    return update_category(category_id, category_data, db)
