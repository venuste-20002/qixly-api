from src.schemas.card_schema import CardResponse
from src.schemas.coupon_schema import CouponResponse
from src.models.card_model import Card,Coupon

def format_card_response(card: Card) -> CardResponse:
    return CardResponse(
        id=card.id,
        institution_id=card.institution_id,
        category_id=card.category_id,
        name=card.name,
        started_date=card.started_date.isoformat(),
        expiration_date=card.expiration_date.isoformat(),
        description=card.description,
        image_url=card.image_url
    )


def format_coupon_response(coupon: Coupon) -> Coupon:
    return coupon

