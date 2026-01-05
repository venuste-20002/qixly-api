from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, col, select, update

from src.helpers.paginator import PaginationResponse, PaginatorQuery
from src.models.authentication_model import Users
from src.models.card_model import Card, CardVariant
from src.models.cart_model import Cart, CartItem, CartStatus
from src.models.coupon_model import Coupon, CouponType
from src.schemas.card_schema import CardResponse
from src.schemas.cart_schemas import (
    CardVariantResponse,
    CartFullResponse,
    CartItemResponse,
    CartResponse,
)
from src.utils.custom_errors import AppError


async def add_cardvariant_to_cart(
    user_id: UUID, card_variant_id: UUID, quantity: int, db: Session
):

    user_exists = db.exec(select(Users).where(Users.id == user_id)).first()
    if not user_exists:
        raise AppError(status_code=404, detail="User not found")

    variant = db.exec(
        select(CardVariant).where(CardVariant.id == card_variant_id)
    ).first()
    if not variant:
        raise AppError(status_code=404, detail="Card variant not found")
    if variant.quantity < quantity:
        raise AppError(status_code=400, detail="Insufficient quantity for sale")

    price = variant.price * quantity
    cart = db.exec(
        select(Cart)
        .where(Cart.user_id == user_exists.id)
        .where(Cart.status == CartStatus.active.value)
    ).first()
    if not cart:
        cart = Cart(
            user_id=user_exists.id,
            card_variant_id=card_variant_id,
            total_quantity=0,
            total_price=0.0,
        )
        db.add(cart)
        db.commit()
        db.refresh(cart)
    cart_item = db.exec(
        select(CartItem).where(
            (CartItem.cart_id == cart.id)
            & (CartItem.card_variant_id == card_variant_id)
        )
    ).first()
    if cart_item:
        cart_item.quantity += quantity
        cart_item.price += price
        db.add(cart_item)
    else:
        new_cart_item = CartItem(
            cart_id=cart.id,
            card_variant_id=card_variant_id,
            quantity=quantity,
            price=price,
        )
        db.add(new_cart_item)
    cart.total_quantity = sum(
        item.quantity
        for item in db.exec(select(CartItem).where(CartItem.cart_id == cart.id))
    )
    cart.total_price = sum(
        item.price
        for item in db.exec(select(CartItem).where(CartItem.cart_id == cart.id))
    )

    db.add(cart)
    db.commit()

    return {
        "id": cart.id,
        "user_id": user_exists.id,
        "card_variant_id": card_variant_id,
        "total_quantity": cart.total_quantity,
        "total_price": cart.total_price,
    }


async def get_cart_by_user_id(
    user_id: UUID,
    db: Session,
):
    cart_data = db.exec(
        select(Cart)
        .where(Cart.user_id == user_id)
        .where(Cart.status == CartStatus.active.value)
    ).first()

    return CartFullResponse(
        cart=CartResponse(**cart_data.model_dump()),
        cart_items=[
            CartItemResponse(
                **i.model_dump(),
                card_variant=CardVariantResponse(**i.variants.model_dump()),
                card=CardResponse(**i.variants.card.model_dump()),
            )
            for i in cart_data.cartitem or []
        ], 
    ) if cart_data else[]

def update_cart(user_id: UUID, card_variant_id: UUID, new_quantity: int, db: Session):
    user_exists = db.exec(
        select(Users)
        .where(Users.id == user_id)
        .where(Cart.status == CartStatus.active.value)
    ).first()
    if not user_exists:
        raise AppError(status_code=404, detail="User not found")

    variant = db.exec(
        select(CardVariant).where(CardVariant.id == card_variant_id)
    ).first()
    if not variant:
        raise AppError(status_code=404, detail="Card variant not found")

    if variant.quantity < new_quantity:
        raise AppError(status_code=400, detail="Insufficient quantity for sale")

    price = variant.price * new_quantity

    cart = db.exec(
        select(Cart)
        .where(Cart.user_id == user_exists.id)
        .where(Cart.status == CartStatus.active)
    ).first()
    if not cart:
        cart = Cart(
            user_id=user_id,
            total_quantity=new_quantity,
            total_price=price,
        )
        db.add(cart)

    cart_item = db.exec(
        select(CartItem).where(
            (CartItem.cart_id == cart.id)
            & (CartItem.card_variant_id == card_variant_id)
        )
    ).first()

    if cart_item:
        cart_item.quantity = new_quantity
        cart_item.price = price
        db.add(cart_item)
    else:
        new_cart_item = CartItem(
            cart_id=cart.id,
            card_variant_id=card_variant_id,
            quantity=new_quantity,
            price=price,
        )
        db.add(new_cart_item)

    # Check if there are any applied coupons for this cart item
    applied_coupon = db.exec(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .where(CartItem.card_variant_id == card_variant_id)
        .where(CartItem.coupon_id.is_not(None))
    ).first()

    new_price = price
    coupon_amount = Decimal('0')

    if applied_coupon and applied_coupon.coupon_id:
        coupon = db.exec(select(Coupon).where(Coupon.id == applied_coupon.coupon_id)).first()
        
        if coupon:
            if coupon.type == CouponType.FIXED:
                coupon_amount = Decimal(str(coupon.amount * new_quantity))
            elif coupon.type == CouponType.PERCENTAGE:
                coupon_amount = Decimal(str(price * (coupon.amount / 100)))
            
            new_price = price - float(coupon_amount)
            cart_item.new_price = new_price
            cart_item.coupon_amount = float(coupon_amount)
            cart_item.coupon_id = coupon.id
            db.add(cart_item)

    cart.total_quantity = sum(
        item.quantity
        for item in db.exec(select(CartItem).where(CartItem.cart_id == cart.id))
    )
    cart.total_price = sum(
        item.price
        for item in db.exec(select(CartItem).where(CartItem.cart_id == cart.id))
    )

    db.add(cart)
    db.commit()

    return {
        "id": cart.id,
        "user_id": user_exists.id,
        "card_variant_id": card_variant_id,
        "total_quantity": cart.total_quantity,
        "total_price": cart.total_price,
        "coupon_value": coupon.amount,
        "new_price": new_price,
        "coupon_amount": float(coupon_amount)
    }


async def remove_card_variant_from_cart(
    user_id: UUID, card_variant_id: UUID, db: Session
):
    cart = db.exec(
        select(Cart)
        .where(Cart.user_id == user_id)
        .where(Cart.status == CartStatus.active.value)
    ).first()

    if not cart:
        raise AppError(status_code=404, detail="cart not found for this user")

    cart_item = db.exec(
        select(CartItem).where(
            (CartItem.cart_id == cart.id)
            & (CartItem.card_variant_id == card_variant_id)
        )
    ).first()

    if cart_item:
        db.delete(cart_item)
    else:
        raise AppError(status_code=404, detail="Card variant not found in cart")

    db.commit()

    return {"message": "Card variant removed from cart"}


async def clear_cart(user_id: UUID, db: Session):
    cart = db.exec(
        select(Cart)
        .where(Cart.user_id == user_id)
        .where(Cart.status == CartStatus.active.value)
    ).first()

    if not cart:
        raise AppError(status_code=404, detail="Cart not found for this user")

    cart_items = db.exec(select(CartItem).where(CartItem.cart_id == cart.id)).all()
    for item in cart_items:
        db.delete(item)

    db.commit()

    return {"message": "All items cleared from cart and cart deleted"}


async def get_all_carts_controller(
    db: Session,
    input_data,
    user,
    status,
) -> PaginationResponse[CartFullResponse]:
    filter_ = ()

    if user:
        filter_ += (Cart.user_id.in_(user),)

    if status:
        filter_ += (Cart.status == status,)

    total_data_pagination, data = await PaginatorQuery.paginate(
        Cart,
        input_data,
        session=db,
        filters=filter_,
    )

    return PaginationResponse(
        pagination=total_data_pagination,
        data=[
            CartFullResponse(
                cart=CartResponse(**d.model_dump()),
                cart_items=[
                    CartItemResponse(
                        **item.model_dump(),
                        card_variant=CardVariantResponse(
                            **item.variants.model_dump(),
                        ),
                        card=CardResponse(
                            **item.variants.card.model_dump(),
                        ),
                    )
                    for item in d.cartitem or []
                ],
            )
            for d in data
        ],
    )


async def apply_coupon(cart_item_id, coupon, database, user_id):
    get_cart_item = database.exec(
        select(CartItem, Cart, Coupon, CardVariant)
        .join(Cart, Cart.id == CartItem.cart_id, isouter=True)
        .join(CardVariant, CartItem.card_variant_id == CardVariant.id)
        .join(Coupon, Coupon.name == coupon, isouter=True)
        .where(CartItem.id == cart_item_id)
        .where(Cart.user_id == user_id)
    ).first()

    cart_item, cart, coupon_, card_variant = get_cart_item

    if not coupon_ or (coupon_.card_variant_id != card_variant.id):
        raise AppError(detail="Coupon is not found")

    cart_item.coupon_id = coupon_.id

    database.commit()
    database.refresh(cart_item)

    return cart_item


async def apply_coupon_all_controller(
        user_id,
        coupon_codes: Optional[List[str]],
        db: Session
):
    get_cart = db.exec(
        select(Cart)
        .where(Cart.user_id == user_id)
        .where(Cart.status == CartStatus.active.value)
    ).first()

    if not get_cart:
        raise AppError(status_code=404, detail="There is no cart or the cart is empty")

    cart_items = db.exec(
        select(CartItem).where(CartItem.cart_id == get_cart.id)
    ).all()

    if not cart_items:
        raise AppError(status_code=404, detail="Cart is empty")

    total_final_amount = Decimal('0')
    total_coupon_discount = Decimal('0')
    applied_coupons = set()

    existing_coupons = {}
    for item in cart_items:
        if item.coupon_id:
            existing_coupons[item.id] = {
                'coupon_id': item.coupon_id,
                'coupon_code': item.coupon_code if hasattr(item, 'coupon_code') else None,
                'coupon_value': item.coupon_value if hasattr(item, 'coupon_value') else None,
                'coupon_amount': item.coupon_amount if hasattr(item, 'coupon_amount') else Decimal('0'),
                'new_price': item.new_price if hasattr(item, 'new_price') else item.price
            }

    new_valid_coupons = {}
    if coupon_codes:
        for code in coupon_codes:
            coupon = db.exec(
                select(Coupon).where(Coupon.code == code)
            ).first()
            
            if not coupon:
                raise AppError(status_code=404, detail=f"Invalid coupon: {code}")

            current_time = datetime.now(timezone.utc)
            if coupon.expiration_date.tzinfo is None:
                coupon.expiration_date = coupon.expiration_date.replace(
                    tzinfo=timezone.utc
                )
            if coupon.expiration_date < current_time:
                raise AppError(status_code=400, detail=f"Coupon {code} has expired")
        
            if coupon.max_uses_per_user < 1:
                raise AppError(
                    status_code=400, detail=f"Coupon {code} usage limit per user exceeded"
                )
            
            new_valid_coupons[code] = coupon

    for item in cart_items:
        variant = db.exec(
            select(CardVariant).where(CardVariant.id == item.card_variant_id)
        ).first()
        
        if not variant:
            raise AppError(
                status_code=404, 
                detail=f"Card variant {item.card_variant_id} not found"
            )
        
        if item.price is None:
            item.price = variant.price

        original_total = Decimal(str(item.price)) * Decimal(str(item.quantity))

        if item.id in existing_coupons:
            existing = existing_coupons[item.id]
            item.coupon_id = existing['coupon_id']
            item.coupon_code = existing['coupon_code']
            item.coupon_value = existing['coupon_value']
            item.coupon_amount = existing['coupon_amount']
            item.new_price = existing['new_price']
            
            if item.coupon_code:
                applied_coupons.add(item.coupon_code)
        else:
            item.new_price = Decimal(str(item.price))
            item.coupon_amount = Decimal('0')
            
            best_discount = Decimal('0')
            best_coupon = None
            
            for code, coupon in new_valid_coupons.items():
                if code in applied_coupons:
                    continue

                if coupon.card_variant_id != item.card_variant_id:
                    continue

                if coupon.type == CouponType.FIXED:
                    discount = Decimal(str(coupon.amount)) * item.quantity
                elif coupon.type == CouponType.PERCENTAGE:
                    discount = (Decimal(str(coupon.amount)) / Decimal('100')) * Decimal(str(item.price)) * item.quantity

                if discount > best_discount:
                    best_discount = discount
                    best_coupon = coupon

            if best_coupon:
                if best_coupon.type == CouponType.FIXED:
                    item.new_price = max(Decimal(str(item.price)) - Decimal(str(best_coupon.amount)), Decimal('0'))
                elif best_coupon.type == CouponType.PERCENTAGE:
                    discount = (Decimal(str(best_coupon.amount)) / Decimal('100')) * Decimal(str(item.price))
                    item.new_price = Decimal(str(item.price)) - discount

                item.coupon_amount = best_discount
                item.coupon_id = best_coupon.id
                item.coupon_code = best_coupon.code
                item.coupon_value = best_coupon.amount
                applied_coupons.add(best_coupon.code)

        item_final_amount = item.new_price * Decimal(str(item.quantity))
        item_discount = original_total - item_final_amount

        total_final_amount += item_final_amount
        total_coupon_discount += item_discount

        db.add(item)

    get_cart.total_price = total_final_amount
    db.add(get_cart)
    db.commit()
    db.refresh(get_cart)

    updated_cart_items = db.exec(
        select(CartItem, CardVariant)
        .join(CardVariant, CartItem.card_variant_id == CardVariant.id)
        .where(CartItem.cart_id == get_cart.id)
    ).all()

    cart_items_response = []
    for cart_item, variant in updated_cart_items:
        card = db.exec(
            select(Card).where(Card.id == variant.card_id)
        ).first()

        cart_item_dict = {
            "id": cart_item.id,
            "cart_id": cart_item.cart_id,
            "card_variant_id": cart_item.card_variant_id,
            "coupon_id": cart_item.coupon_id,
            "coupon_code": getattr(cart_item, 'coupon_code', None),
            "coupon_value": getattr(cart_item, 'coupon_value', None),
            "quantity": cart_item.quantity,
            "price": cart_item.price,
            "new_price": getattr(cart_item, 'new_price', cart_item.price),
            "coupon_amount": getattr(cart_item, 'coupon_amount', Decimal('0')),
            "card_variant": CardVariantResponse(
                id=variant.id,
                price=variant.price,
                quantity=variant.quantity,
                description=variant.description
            ),
            "card": CardResponse(
                id=card.id,
                image_url=card.image_url,
                name=card.name,
                description=card.description,
                category_id=card.category_id,
                institution_id=card.institution_id,
                started_date=card.started_date,
                expiration_date=card.expiration_date,
                status=card.status,
                created_at=card.created_at,
                is_deleted=card.is_deleted
            )
        }
        cart_items_response.append(CartItemResponse(**cart_item_dict))

    result = {
        "cart": get_cart,
        "cart_items": cart_items_response,
        "total_final_amount": total_final_amount,
        "total_coupon_discount": total_coupon_discount,
        "applied_coupons": list(applied_coupons)
    }

    return result
