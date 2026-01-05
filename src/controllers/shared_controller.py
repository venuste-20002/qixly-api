from uuid import UUID

from fastapi import BackgroundTasks
from sqlmodel import Session, select

from src.helpers.mailer import Mailer
from src.helpers.qrcode import qr_code
from src.models.sales_model import SalesItem
from src.models.shared_model import SharedCard
from src.schemas.shared_schema import SharedResponse
from src.utils.custom_errors import AppError


async def Shared_card_item(
    sales_item_card: UUID,
    email: str,
    phone: str,
    db: Session,
    background: BackgroundTasks,
):
    # TODO: should add if was shared
    salesitem = db.exec(select(SalesItem).where(SalesItem.is_deleted == False)).first()

    if not salesitem:
        raise AppError(
            status_code=404, detail="Sales Item not found or is already shared"
        )

    shared = SharedCard(
        sales_item_id=sales_item_card,
        card_amount=salesitem.cost_variant,
        email=email,
        phone=phone,
    )

    salesitem.shared = True

    qr_base64 = await qr_code(sales_item_card)

    background.add_task(Mailer(email).share_email, qr_base64, salesitem.cost_variant)

    # await Mailer(email).share_email(qr_base64, salesitem.cost_variant)
    db.add(shared)
    db.commit()
    db.refresh(shared)

    return SharedResponse(**shared.model_dump())


# function of get shared by id


async def get_shared_by_id_controler(shared_id: UUID, db: Session) -> SharedResponse:
    shared = db.exec(select(SharedCard).where(SharedCard.id == shared_id)).first()
    if not shared:
        raise AppError(
            status_code=404, detail="Card item not found or is already shared"
        )
    return shared

