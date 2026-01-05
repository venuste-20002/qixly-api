import logging
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from src.models.commission_model import Commission
from src.schemas.commission_schema import CommissionResponse
from src.utils.custom_errors import AppError

logger = logging.getLogger(__name__)

# Add a commission


async def add_commission_controller(
    card_variant_id: UUID,
    is_active: bool,
    rate: Optional[int],
    amount: Optional[int],
    db: Session,
) -> CommissionResponse:
    if is_active:
        if rate is not None and amount is not None:
            raise AppError(
                status_code=400,
                detail="You can provide either Rate or Amount, but not both.",
            )
        if rate is None and amount is None:
            raise AppError(
                status_code=400,
                detail="Either Rate or Amount must be provided when is_active is true.",
            )
    else:
        if rate is not None or amount is not None:
            raise AppError(
                status_code=400,
                detail="Rate and Amount must not be provided when is_active is false.",
            )
        rate = 0
        amount = 0
    existing_commission = db.exec(
        select(Commission).where(Commission.card_variant_id == card_variant_id)
    ).first()
    if existing_commission:
        raise AppError(
            status_code=400, detail="Commission already exists for the card variant"
        )

    new_commission = Commission(
        card_variant_id=card_variant_id, rate=rate, amount=amount, is_active=is_active
    )

    db.add(new_commission)
    db.commit()
    db.refresh(new_commission)
    return new_commission


# Get commission by ID


def get_commission_by_id_controller(
    commission_id: UUID, db: Session
) -> CommissionResponse:
    commission = db.exec(
        select(Commission).where(Commission.id == commission_id)
    ).first()
    if not commission:
        raise AppError(status_code=404, detail="Commission not found")
    return commission


# Update a commission by ID


async def update_commission_controller(
    commission_id: UUID,
    is_active: bool,
    rate: Optional[int],
    amount: Optional[int],
    db: Session,
) -> CommissionResponse:
    commission = db.exec(
        select(Commission).where(Commission.id == commission_id)
    ).first()
    if not commission:
        raise AppError(status_code=404, detail="Commission not found")
    if rate is not None and amount is not None:
        raise AppError(
            status_code=400,
            detail="You can provide either Rate or Amount, but not both.",
        )

    if is_active and (rate is None and amount is None):
        raise AppError(
            status_code=400,
            detail="You must provide either Rate or Amount when is_active is true.",
        )

    if not is_active and (rate is not None or amount is not None):
        raise AppError(
            status_code=400,
            detail="Rate and Amount should not be provided when is_active is false.",
        )

    commission.is_active = is_active
    if rate is not None:
        commission.rate = rate
        commission.amount = 0
    elif amount is not None:
        commission.amount = amount
        commission.rate = 0

    db.commit()
    db.refresh(commission)
    return commission
