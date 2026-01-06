import re
from datetime import datetime
from enum import Enum
from typing import Optional, Union

import requests 
from fastapi import status
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select

from src.config import settings
from src.helpers.generate_sales_item_number import generate_sales_item_number
from src.models.card_model import CardVariant
from src.models.cart_model import Cart, CartItem, CartStatus
from src.models.sales_model import SalesItem
from src.models.transaction_model import Transactions, TransactionStatus
from src.utils.custom_errors import AppError


def get_paypack_access_token():
    """Get access token from Paypack API."""
    auth_url = f"{settings.PAYPACK_BASE_URL}/auth/agents/authorize"
    response = requests.post(
        auth_url,
        json={
            "client_id": settings.PAYPACK_CLIENT_ID,
            "client_secret": settings.PAYPACK_CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["access"]


def get_sales_number(number: int, base: int = 36, padding: int = 0):
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if base > len(digits):
        raise ValueError("Bases greater than 36 not handled in base_repr.")
    elif base < 2:
        raise ValueError("Bases less than 2 not handled in base_repr.")

    num = abs(int(number))
    res = []
    while num:
        res.append(digits[num % base])
        num //= base
    if padding:
        res.append("0" * padding)
    if number < 0:
        res.append("-")
    return "".join(reversed(res or "0"))


class PaymentPushCallback(str, Enum):
    MTN_PUSH = settings.MTN_API_PUSH
    AIRTEL_PUSH = settings.AIRTEL_API_PUSH

    def __str__(self):
        return self.value


class PaymentPushSchema(SQLModel):
    phone_number: str
    amount: int
    reference: str
    app_transaction_id: str
    callback_url: str = settings.PAYMENT_CALLBACK_URL


class MomoPaymentSchema(PaymentPushSchema):
    payee_note: Optional[str] = Field(
        default="Payment for goods",
    )
    payer_note: Optional[str] = Field(
        default="Payment for goods",
    )


class AirtelPaymentSchema(PaymentPushSchema):
    pass


class PaypackCashinSchema(SQLModel):
    amount: int
    phone: str
    reference: str
    reason: Optional[str] = Field(default="Payment for goods")


class PaymentService(str, Enum):
    PAYPACK = "paypack"


class PaymentController:
    def __init__(
        self,
        payment_service: PaymentService,
        input_data: PaypackCashinSchema,
    ):
        self.payment_service = payment_service
        self.input_data = input_data

    def __call__(self):
        match self.payment_service:
            case PaymentService.PAYPACK:
                self.validate_input_data(PaypackCashinSchema)
                return self.paypack_cashin()

    def validate_input_data(self, expected_data: type):
        if not isinstance(self.input_data, expected_data):
            raise AppError(
                detail=f"Expected {expected_data} but got {type(self.input_data)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def paypack_cashin(self):
        data = PaypackCashinSchema(**self.input_data.model_dump())
        token = get_paypack_access_token()
        cashin_url = f"{settings.PAYPACK_BASE_URL}/transactions/cashin"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            cashin_url,
            headers=headers,
            json=data.model_dump(),
        )
        return response.json()


class PaymentSchemaPush(BaseModel):
    amount: int
    reference: str
    network: str
    phone_number: str
    app_transaction_id: str


def create_payment(
    input_data: PaymentSchemaPush,
):
    # Since we now only support Paypack, always use PAYPACK
    # Map phone_number to phone for PaypackCashinSchema
    paypack_data = PaypackCashinSchema(
        amount=input_data.amount,
        phone=input_data.phone_number,
        reference=input_data.reference,
        reason="Payment for goods"
    )
    payment_push = PaymentController(
        payment_service=PaymentService.PAYPACK,
        input_data=paypack_data,
    )
    data = payment_push()
    return data


class PaymentTransactionCallbackSchema(SQLModel):
    transaction_id: str
    # transaction_number: str
    tx_status: TransactionStatus
    payment_channel: str
    transaction_time: datetime
    channel_transaction_id: str


class PaypackCallbackData(SQLModel):
    ref: str
    amount: int
    fee: int
    client: str
    timestamp: str


class PaypackCallbackSchema(SQLModel):
    event: str
    data: PaypackCallbackData


def payment_callback_controller(
    transaction: PaymentTransactionCallbackSchema, db: Session
):

    tx_data = db.exec(
        select(Transactions)
        .where(getattr(Transactions, "id") == transaction.transaction_id)
        .where(getattr(Transactions, "tx_status") == TransactionStatus.PENDING.value)
    ).first()

    s_data = db.exec(
        select(Cart, CartItem, CardVariant)
        .join(CartItem, CartItem.cart_id == Cart.id, isouter=True)
        .join(
            CardVariant,
            CardVariant.id == CartItem.card_variant_id,
            isouter=True,
        )
        .where(Cart.id == tx_data.cart_id)
    ).all()

    if transaction.tx_status == TransactionStatus.SUCCESS.value:
        for data in s_data:
            cart, cart_item, card_variant = data
            card_variant.pending_quantity -= cart_item.quantity
            cart.status = CartStatus.completed.value

            for _ in range(cart_item.quantity):
                """Generate sales number and generate sales number in base 36"""

                sales_number_sequence = generate_sales_item_number(db)
                sales_number = get_sales_number(int(sales_number_sequence))

                """Create sales item"""
                sales_item = SalesItem(
                    cart_id=cart.id,
                    card_variant_id=cart_item.card_variant_id,
                    user_id=cart.user_id,
                    cost_variant=card_variant.price,
                    card_id=card_variant.card_id,
                    sales_number_sequence=sales_number_sequence,
                    sales_number=sales_number,
                )
                db.add(sales_item)

    if transaction.tx_status == TransactionStatus.FAILED.value:
        for data in s_data:
            cart, cart_item, card_variant = data

            cart.status = CartStatus.failed.value

            card_variant.pending_quantity -= cart_item.quantity
            card_variant.quantity += cart_item.quantity

    tx_data_update = transaction.model_dump(exclude_unset=True)
    tx_data.sqlmodel_update(tx_data_update)

    db.commit()
    db.refresh(tx_data)

    return tx_data


def paypack_callback_controller(
    callback: PaypackCallbackSchema, db: Session, signature: str = None
):
    """Handle Paypack webhook callback."""
    # Optional: Verify webhook signature if signature is provided
    if signature and settings.PAYPACK_WEBHOOK_SECRET:
        import hmac
        import hashlib
        expected_signature = hmac.new(
            settings.PAYPACK_WEBHOOK_SECRET.encode(),
            callback.model_dump_json().encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise AppError(detail="Invalid signature", status_code=status.HTTP_401_UNAUTHORIZED)

    # Extract transaction_id from ref (assuming ref is the app_transaction_id)
    transaction_id = callback.data.ref

    # Determine status from event
    if callback.event == "cashin:success":
        tx_status = TransactionStatus.SUCCESS
    elif callback.event == "cashin:failed":
        tx_status = TransactionStatus.FAILED
    else:
        # Unknown event, perhaps log and return
        return {"status": "unknown event"}

    # Create a PaymentTransactionCallbackSchema-like object
    transaction = PaymentTransactionCallbackSchema(
        transaction_id=transaction_id,
        tx_status=tx_status,
        payment_channel="paypack",
        transaction_time=datetime.fromisoformat(callback.data.timestamp.replace('Z', '+00:00')),
        channel_transaction_id=callback.data.client,  # or some other identifier
    )

    return payment_callback_controller(transaction, db)


class NetworkRegexSchema(Enum):
    paypack = ["^250(72|73|78|79)[0-9]{7}$"]

def phone_network_action(phone_number: str):
    if phone_number.startswith("07"):
        phone_number = f"250{phone_number}"
    # Since we now only support Paypack for all Rwandan numbers
    if re.match(r"^250(72|73|78|79)[0-9]{7}$", phone_number):
        return "paypack"

    raise AppError(
        detail="Invalid phone number",
        status_code=status.HTTP_400_BAD_REQUEST,
    )
