from datetime import datetime
from uuid import UUID

from fastapi import UploadFile, status
from sqlmodel import Session, col, select

from src.helpers.image_uploader import save_image
from src.helpers.paginator import Paginate, PaginationResponse, PaginatorQuery
from src.models.authentication_model import Institutions
from src.models.card_model import Card, Category
from src.schemas.card_schema import (
    CardFullResponse,
    CardResponse,
    CardVariantFullResponse,
    CardvariantResponse,
    UpdateCardSchema,
)
from src.schemas.common_schema import CommonResponseSchema
from src.schemas.institution_schema import InstitutionGetschema
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetcher


# Create card function
async def create_card_controller(
    usage_time: str,
    category_id: UUID,
    institution_id: UUID,
    name: str,
    description: str,
    started_date: datetime,
    expiration_date: datetime,
    image: UploadFile,
    db: Session,
):
    category = db.exec(
        select(Category).where(col(Category.id).__eq__(category_id))
    ).first()
    if not category:
        raise AppError(status_code=400, detail="Category does not exist")

    institution = db.exec(
        select(Institutions).where(col(Institutions.id).__eq__(institution_id))
    ).first()
    if not institution:
        raise AppError(status_code=400, detail="Institution does not exist")

    if expiration_date <= started_date:
        raise AppError(
            status_code=400, detail="Expiration date must be after start date"
        )

    existing_card = db.exec(select(Card).where(col(Card.name).__eq__(name))).first()
    if existing_card:
        raise AppError(status_code=400, detail="Card already exists")
    saved_image = []

    for i in image:
        saved_image.append(save_image(i))

    # card_image_url = save_image(image) if image else None

    new_card = Card(
        institution_id=institution_id,
        category_id=category_id,
        name=name,
        started_date=started_date,
        expiration_date=expiration_date,
        description=description,
        image_url=saved_image,
        usage_time=usage_time,
    )

    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return CardResponse(**new_card.model_dump())


async def get_all_cards_controller(
    db: Session,
    status_,
    start_date,
    ending_date,
    institution: list[UUID],
    category: list[UUID],
    input_data: Paginate,
    search,
) -> PaginationResponse[CardFullResponse]:
    filter_ = ()

    if status_:
        filter_ += (Card.status == status_,)
    if start_date:
        filter_ += (Card.created_at >= start_date,)
    if ending_date:
        filter_ += (Card.created_at <= ending_date,)
    if institution:
        filter_ += (col(Card.institution_id).in_(institution),)
    if category:
        filter_ += (col(Card.category_id).in_(category),)

    total_cards, data = await PaginatorQuery.paginate(
        table_name=Card,
        input_data=input_data,
        session=db,
        filters=filter_,
        search=search,
    )

    return PaginationResponse(
        pagination=total_cards,
        data=[
            CardFullResponse(
                card=CardResponse(**d.model_dump()),
                variants=[
                    CardVariantFullResponse(**d.model_dump()) for d in d.variants
                ],
                institution=InstitutionGetschema(**d.institution.model_dump()),
            )
            for d in data
        ],
    )


# Fetch single card by ID
async def get_card_by_id_controller(card_id: UUID, db: Session):
    card = Fetcher(
        database=db,
        table=(Card,),
        where=(Card.id == card_id,),
        error="Card not found",
    ).get_one()

    return CardFullResponse(
        card=CardResponse(**card.model_dump()),
        variants=[CardVariantFullResponse(**d.model_dump()) for d in card.variants],
        institution=InstitutionGetschema(**card.institution.model_dump()),
    )


# Update card by ID
async def update_card_by_id_controller(
    card_id: UUID,
    input_data: UpdateCardSchema,
    db: Session,
):
    statement = select(Card).where(col(Card.id).__eq__(card_id))
    existing_card = db.exec(statement).first()
    if not existing_card:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    card_update_data = input_data.model_dump(exclude_unset=True, exclude_none=True)
    existing_card.sqlmodel_update(card_update_data)

    db.add(existing_card)
    db.commit()
    db.refresh(existing_card)

    return CommonResponseSchema(
        message="Card updated successfully",
        data=CardResponse(**existing_card.model_dump()),
    )


async def mark_card_as_deleted_controller(card_id: UUID, db: Session) -> dict:
    existing_card = Fetcher(
        database=db,
        table=(Card,),
        where=(Card.id == card_id,),
        error="Card not found",
    ).get_one()

    existing_card.is_deleted = True

    db.add(existing_card)
    db.commit()
    db.refresh(existing_card)

    return {"detail": "Card marked as deleted successfully"}
