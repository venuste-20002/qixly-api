from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlmodel import Session, col

from src.config import settings
from src.helpers.generate_transaction_number import generate_transaction_number
from src.helpers.paginator import PaginationResponse, PaginatorQuery
from src.helpers.payment import PaymentSchemaPush, create_payment, phone_network_action
from src.helpers.qrcode import qr_code
from src.models.card_model import CardVariant, Commission
from src.models.cart_model import Cart, CartItem, CartStatus
from src.models.coupon_model import Coupon, CouponType
from src.models.sales_model import SalesItem
from src.models.transaction_model import TransactionInputSchema, Transactions
from src.schemas.card_schema import CardResponse, CardvariantResponse
from src.schemas.institution_schema import InstitutionGetschema
from src.schemas.sales_schema import (
    SalesFullItemsResponse,
    SalesItemsResponse,
    SalesResult,
)
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch, Fetcher

# part one 
def create_transaction(input_data: TransactionInputSchema, db: Session):
    record = Transactions(
        **input_data.model_dump(), transaction_number=generate_transaction_number(db)
    )
    db.add(record)
    return record

# the part two 

def create_sales_item(input_data: SalesItem, db: Session):
    record = SalesItem(**input_data.model_dump())
    db.add(record)
    return record


def create_variant_sale_controller(input_data: SalesResult, db: Session, user):
    card_variant, commission = db.exec(
        select(CardVariant, Commission)
        .join(
            Commission,
            col(CardVariant.id).__eq__(Commission.card_variant_id),
            isouter=True,
        )
        .where(col(CardVariant.id).__eq__(input_data.card_variant_id))
        .where(col(CardVariant.is_deleted).__eq__(False))
    ).first()
    if not card_variant:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card variant not found"
        )

    if card_variant.quantity < input_data.quantity:
        raise AppError(detail="Insufficient quantity")

    card_variant.pending_quantity += input_data.quantity
    card_variant.quantity -= input_data.quantity

    coupon_discount = 0
    coupon = None
    if input_data.coupon_code:
        coupon = Fetcher(
            database=db,
            table=(Coupon,),
            where=(
                Coupon.code == input_data.coupon_code,
                Coupon.card_variant_id == input_data.card_variant_id,
            ),
            error="Coupon not found",
        ).get_one()

        if coupon.type == CouponType.PERCENTAGE.value:
            coupon_discount = (
                card_variant.price * (coupon.amount / 100) * input_data.quantity
            )
        else:
            coupon_discount = coupon.amount * input_data.quantity
    payment_price = max((card_variant.price * input_data.quantity) - coupon_discount, 0)

    create_cart = Cart(
        user_id=UUID(user["id"]),
        total_price=payment_price,
        total_quantity=input_data.quantity,
        status=CartStatus.pending.value,
    )
    db.add(create_cart)
    create_cart_item = CartItem(
        cart_id=create_cart.id,
        price=int(card_variant.price * input_data.quantity),
        coupon_id=coupon.id if coupon else None,
        **input_data.model_dump(),
    )
    db.add(create_cart_item)

    phone_network = phone_network_action(input_data.phone_number or user["phone"])

    add_transaction = create_transaction(
        input_data=TransactionInputSchema(
            user_id=UUID(user["id"]),
            commission_amount=(
                payment_price * commission.rate / 100 if commission else 0
            ),
            coupon_amount=int(coupon_discount),
            total_payed_amount=int(payment_price),
            total_recieved_amount=int(payment_price),
            commission_rate=commission.rate if commission else 0,
            phone_number=str(input_data.phone_number or user["phone"]),
            cart_id=create_cart.id,
            network=phone_network,
        ),
        db=db,
    )

    payment = create_payment(
        input_data=PaymentSchemaPush(
            amount=payment_price,
            network=phone_network,
            phone_number=str(input_data.phone_number or user["phone"]),
            reference=str(input_data.phone_number or user["phone"]),
            app_transaction_id=str(add_transaction.id),
        )
    )

    db.commit()
    return payment


def create_sales_from_cart_controller(
    user_id,
    coupon_codes: Optional[List[str]],
    db: Session,
    input_data,
):
    cart = Fetcher(
        database=db,
        table=(Cart,),
        where=(
            Cart.user_id == user_id["id"],
            Cart.status == CartStatus.active.value,
        ),
        error="There is no cart or the cart is empty",
    ).get_one()

    cart_items = Fetcher(
        database=db,
        table=(CartItem,),
        where=(CartItem.cart_id == cart.id,),
        error="cart is empty",
    ).get_all()

    cart.status = CartStatus.pending.value

    total_final_amount = 0
    total_commission_amount = 0
    total_coupon_discount = 0

    applied_coupons = set()

    for item_row in cart_items:
        item = item_row 
        card_variant_id = getattr(item, 'card_variant_id')
        quantity = getattr(item, 'quantity')

        variant = Fetcher(
            database=db,
            table=(CardVariant,),
            where=(CardVariant.id == card_variant_id,),
            error=f"Card variant {card_variant_id} not found",
        ).get_one()

        if item.quantity < quantity:
            raise AppError(
                status_code=400,
                detail=f"Insufficient quantity for card variant {card_variant_id}",
            )

        variant.pending_quantity += quantity
        variant.quantity -= quantity

        coupon_discount = 0
        if coupon_codes:
            total_coupon_discount = 0

            for code in coupon_codes:
                if code in applied_coupons:
                    continue

                coupon_row = db.exec(
                    select(Coupon).where(col(Coupon.code).__eq__(code))
                ).first()
                if not coupon_row:
                    raise AppError(status_code=404, detail="invalid coupon")    
                coupon = coupon_row[0]

                current_time = datetime.now(timezone.utc)
                if coupon.expiration_date.tzinfo is None:
                    coupon.expiration_date = coupon.expiration_date.replace(
                        tzinfo=timezone.utc
                    )
                if coupon.expiration_date < current_time:
                    raise AppError(status_code=400, detail="Coupon has expired")

                if coupon.max_uses_per_user < 1:
                    raise AppError(
                        status_code=400, detail="Coupon usage limit per user exceeded"
                    )

                coupon_discount = coupon.amount * quantity
                total_coupon_discount += coupon_discount
                coupon.max_uses_per_user -= 1
                db.add(coupon)
                db.commit()
                db.refresh(coupon)
                applied_coupons.add(code)
                break

        total_price = variant.price * quantity
        final_amount = max(total_price - coupon_discount, 0)

        commission_row = db.exec(
            select(Commission).where(
                col(Commission.card_variant_id).__eq__(card_variant_id)
            )
        ).first()
        commission = commission_row[0] if commission_row else None
        commission_amount = (total_price * commission.rate) / 100 if commission else 0

        total_final_amount += final_amount
        total_commission_amount += commission_amount
        total_coupon_discount += coupon_discount

    phone_network = phone_network_action(input_data.phone_number or user_id["phone"])

    transaction = create_transaction(
        input_data=TransactionInputSchema(
            user_id=UUID(user_id["id"]),
            commission_amount=total_commission_amount,
            coupon_amount=total_coupon_discount,
            total_payed_amount=total_final_amount,
            total_recieved_amount=total_final_amount,
            commission_rate=commission.rate if commission else 0,
            phone_number=str(input_data.phone_number or user_id["phone"]),
            cart_id=cart.id,
            network=phone_network,
        ),
        db=db,
    )
    payment = create_payment(
        input_data=PaymentSchemaPush(
            amount=total_final_amount,
            network=phone_network,
            phone_number=str(input_data.phone_number or user_id["phone"]),
            reference=str(input_data.phone_number or user_id["phone"]),
            app_transaction_id=str(transaction.id),
        )
    )

    db.commit()

    # Return transaction and cart information since sales items are created via webhook
    return {
        "payment_response": payment,
        "transaction_id": str(transaction.id),
        "cart_id": str(cart.id),
        "total_amount": total_final_amount,
        "phone_number": str(input_data.phone_number or user_id["phone"]),
        "network": phone_network,
        "status": "pending",  # Payment is initiated, awaiting confirmation
        "message": "Payment initiated successfully. Sales items will be created upon payment confirmation."
    }


async def view_sale(sales_item_id: UUID, database: Session):
    get_order = await Fetch(SalesItem, "id", sales_item_id, database).get_single_value()
    if not get_order:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")

    if get_order.shared:
        raise AppError(detail="Share already shared. Unable to view")
    get_order.viewed = True

    buffered = await qr_code(
        f"http://{settings.BASE_URL}/api/v1/sales/{sales_item_id}/view"
    )
    database.add(get_order)
    database.commit()

    return buffered


async def get_all_sales_items_controller(
    db,
    input_data,
    user,
    cart,
    card_variant,
    shared,
    viewed,
    status_,
) -> PaginationResponse[SalesFullItemsResponse]:
    filters = ()
    if user:
        filters += (col(SalesItem.user_id).in_(user),)
    if cart:
        filters += (col(SalesItem.cart_id).in_(cart),)
    if card_variant:
        filters += (col(SalesItem.card_variant_id).in_(card_variant),)
    if shared:
        filters += (SalesItem.shared == shared,)
    if viewed:
        filters += (SalesItem.viewed == viewed,)
    if status_:
        filters += (SalesItem.status == status_,)

    total_sales, total_sales_items = await PaginatorQuery.paginate(
        session=db,
        table_name=SalesItem,
        input_data=input_data,
        filters=filters,
    )
    return PaginationResponse(
        pagination=total_sales,
        data=[
            SalesFullItemsResponse(
                item=SalesItemsResponse(**d.model_dump()),
                card_variant=CardvariantResponse(
                    **d.card_variant.model_dump(),
                    card=CardResponse(**d.card_variant.card.model_dump()),
                )
                or [],
            )
            for d in total_sales_items
        ],
    )


async def get_single_sale_item(db: Session, sales_id: UUID, user_id: UUID):
    sale = Fetcher(
        database=db,
        table=(SalesItem,),
        where=(SalesItem.id == sales_id, SalesItem.user_id == user_id),
        error="SalesItem not found",
    ).get_one()

    return SalesFullItemsResponse(
        item=SalesItemsResponse(**sale.model_dump()),
        card_variant=CardvariantResponse(
            **sale.card_variant.model_dump(),
            card=CardResponse(
                **sale.card_variant.card.model_dump(),
                institution=InstitutionGetschema(
                    **sale.card_variant.card.institution.model_dump()
                ),
            ),
        )
        or [],
    )