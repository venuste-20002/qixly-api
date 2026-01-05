import uuid
from datetime import datetime
from sqlmodel import Session, select
from src.models.coupon_model import CouponType
from src.models.card_model import Coupon,CardVariant
from src.schemas.coupon_schema import CouponResponse
from src.utils.custom_errors import AppError
from uuid import UUID
from datetime import datetime, timezone
from src.helpers.response_form import format_coupon_response


# Get Coupon by ID
async def create_coupon_controller(
    db: Session,
    card_variant_id: UUID,  
    amount: int,
    expiration_date: datetime,
    type: CouponType, 
    name: str = None,
    min_quantity: int = 0,
    max_quantity: int = None,
    max_uses_per_user: int = 1
) -> CouponResponse:
    card_variant = db.exec(select(CardVariant).where(CardVariant.id == card_variant_id)
    ).first()
    
    if not card_variant or not card_variant.card:
        raise AppError(status_code=404, detail="Card variant or associated card not found.")
    
    card_expiration_date = card_variant.card.expiration_date
    if card_expiration_date.tzinfo is None:
        card_expiration_date = card_expiration_date.replace(tzinfo=timezone.utc)
    
    current_time = datetime.now(timezone.utc)

    if expiration_date > card_expiration_date or expiration_date < current_time:
        raise AppError(status_code=400, detail="The coupon expiration date must be between now and the card's expiration date.")
    
    existed_coupon = db.exec(select(Coupon).where(Coupon.card_variant_id == card_variant_id,Coupon.name==name)).first()
    if existed_coupon:
        raise AppError(status_code=400, detail="Coupon with the same name already exists.")

    existing_coupon = db.exec(select(Coupon).where(Coupon.card_variant_id == card_variant_id)).first()

    if existing_coupon:
        if existing_coupon.expiration_date.tzinfo is None:
            existing_coupon_expiration_date = existing_coupon.expiration_date.replace(tzinfo=timezone.utc)
        else:
            existing_coupon_expiration_date = existing_coupon.expiration_date

        if existing_coupon_expiration_date < current_time:
            db.delete(existing_coupon)
            db.commit()
        else:
            raise AppError(
                status_code=400,
                detail="A valid coupon is already applied to this card variant. Only one active coupon is allowed."
            )
    
    if name:
        coupon_code = name
    else:
        coupon_code = str(uuid.uuid4()).replace("-", "").upper()[:10]
        while db.exec(select(Coupon).where(Coupon.code == coupon_code)).first():
            coupon_code = str(uuid.uuid4()).replace("-", "").upper()[:10]
    
    coupon = Coupon(
        card_variant_id=card_variant_id,
        name=name,
        amount=amount,
        expiration_date=expiration_date,
        code=coupon_code,  
        type=type,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        max_uses_per_user=max_uses_per_user
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    
    return format_coupon_response(coupon)


# function of get all the coupon

async def get_coupon_by_id_controller(coupon_id: UUID, db: Session) -> CouponResponse:
        coupon = db.exec(select(Coupon).where(Coupon.id == coupon_id)).first()
        if not coupon:
            raise AppError(status_code=404, detail="Coupon not found")
        
        return format_coupon_response(coupon)




async def update_coupon_controller(
    db: Session,
    coupon_id: UUID,
    amount: int = None,
    expiration_date: datetime = None,
    type: str = None,
    name: str = None,
    min_quantity: int = None,
    max_quantity: int = None,
    max_uses_per_user: int = None
) -> CouponResponse:
    coupon = db.exec(select(Coupon).where(Coupon.id == coupon_id)).first()
    if not coupon:
        raise AppError(status_code=404, detail="Coupon not found.")

    if name and name != coupon.name:
        existed_coupon = db.exec(select(Coupon).where(Coupon.name == name)).first()
        if existed_coupon:
            raise AppError(status_code=400, detail="Coupon with the same name already exists.")

    card_variant = db.exec(select(CardVariant).where(CardVariant.id == coupon.card_variant_id)).first()
    if not card_variant or not card_variant.card:
        raise AppError(status_code=404, detail="Card variant or associated card not found.")

    card_expiration_date = card_variant.card.expiration_date
    if card_expiration_date.tzinfo is None:
        card_expiration_date = card_expiration_date.replace(tzinfo=timezone.utc)

    current_time = datetime.now(timezone.utc)
    if expiration_date:
        if expiration_date > card_expiration_date or expiration_date < current_time:
            raise AppError(
                status_code=400,
                detail="The coupon expiration date must be between now and the card's expiration date."
            )
    if type and type not in ["percentage", "fixed"]:
        raise AppError(
            status_code=400,
            detail="Invalid coupon type. Choose 'percentage' or 'fixed'."
        )

    if amount is not None:
        coupon.amount = amount
    if expiration_date is not None:
        coupon.expiration_date = expiration_date
    if type is not None:
        coupon.type = type
    if name is not None:
        coupon.name = name
        coupon.code = name 
    if min_quantity is not None:
        coupon.min_quantity = min_quantity
    if max_quantity is not None:
        coupon.max_quantity = max_quantity
    if max_uses_per_user is not None:
        coupon.max_uses_per_user = max_uses_per_user

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return format_coupon_response(coupon)


# Delete Coupon
async def delete_coupon_controller(coupon_id: UUID, db: Session) -> CouponResponse:
        coupon = db.exec(select(Coupon).where(Coupon.id == coupon_id)).first()
        if not coupon:
            raise AppError(status_code=404, detail="Coupon not found")
        
        coupon.is_deleted = True
        db.add(coupon)
        db.commit()
        db.refresh(coupon)
        
        return format_coupon_response(coupon)
