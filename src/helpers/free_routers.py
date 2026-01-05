import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlmodel import SQLModel

from src.controllers.sales_controller import view_sale
from src.database import database
from src.helpers.paginator import Paginate, PaginationResponse, PaginatorQuery
from src.helpers.payment import (
    PaymentTransactionCallbackSchema,
    payment_callback_controller,
)
from src.helpers.report_generator import generate_sales_item_pdf
from src.models.institutions_model import Institutions
from src.models.sales_model import SalesItem
from src.schemas.card_schema import CardResponse, CardvariantResponse
from src.schemas.institution_schema import InstitutionGetschema
from src.schemas.sales_schema import SalesItemFullSchema, TransactionSchema
from src.schemas.users_schema import UserDataSchema
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetcher

router = APIRouter()


class InstitutionFreeSchema(SQLModel):
    id: UUID
    name: str
    address: str
    image_url: str


@router.get(
    "/institution/free",
    tags=["Institutions"],
)
async def get_institutions(
    db: database,
    search: Optional[str] = None,
    input_data: Paginate = Depends(),
) -> PaginationResponse[InstitutionFreeSchema]:
    pagination_result, institutions = await PaginatorQuery.paginate(
        table_name=Institutions,
        input_data=input_data,
        session=db,
        search=search,
    )
    return PaginationResponse(
        pagination=pagination_result,
        data=[InstitutionFreeSchema(**data.model_dump()) for data in institutions],
    )


@router.post("/sales/callback", tags=["Sales"])
async def callback(request: Request, db: database):
    res = await request.json()
    return payment_callback_controller(
        PaymentTransactionCallbackSchema(**res),
        db,
    )


@router.get("/sales/{sales_id}/view", tags=["Sales"])
async def view_sales(sales_id: UUID, db: database):
    res = await view_sale(sales_id, db)
    return StreamingResponse(res, media_type="image/png")


def file_iterator(file_path: str, chunk_size: int = 1024 * 1024):
    with open(file_path, "rb") as file:
        while chunk := file.read(chunk_size):
            yield chunk


@router.get("/resources/{file:path}", tags=["Resources"])
async def get_image(file: str):
    file_directory = "./images/"
    file_path = os.path.join(file_directory, file)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise AppError(status_code=404, detail="Image not found")

    def get_file():
        with open(file_path, "rb") as f:
            yield from f

    file_extension = os.path.splitext(file_path)[-1].lower()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
    }.get(file_extension, "image/png")

    return StreamingResponse(
        get_file(),
        media_type=media_type,
    )


@router.get(
    "/sales/{sales_item_id}/pdf", status_code=status.HTTP_200_OK, tags=["Sales"]
)
async def get_sales_item_pdf(db: database, sales_item_id: UUID):
    get_sales_item = Fetcher(
        table=(SalesItem,),
        database=db,
        where=(SalesItem.id == sales_item_id,),
        error="SalesItem not found",
    ).get_one()
    return generate_sales_item_pdf(
        res=SalesItemFullSchema(
            **get_sales_item.model_dump(),
            user=UserDataSchema(**get_sales_item.user.model_dump()),
            card_variant=CardvariantResponse(
                **get_sales_item.card_variant.model_dump()
            ),
            card=CardResponse(
                **get_sales_item.card.model_dump(),
                institution=InstitutionGetschema(
                    **get_sales_item.card.institution.model_dump()
                ),
            ),
            transaction=TransactionSchema(
                **get_sales_item.cart.transaction.model_dump()
            ),
        )
    )
