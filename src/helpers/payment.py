import re
from datetime import datetime
from enum import Enum
from typing import Optional, Union
import secrets

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
    PAYPACK_BASE_URL = "https://payments.paypack.rw/api"

    def __str__(self):
        return self.value


class PaymentPushSchema(SQLModel):
    phone_number: str
    amount: int
    reference: str
    app_transaction_id: str
    callback_url: str = settings.PAYMENT_CALLBACK_URL


class PaypackPaymentSchema(PaymentPushSchema):
    idempotency_key: Optional[str] = None


class PaymentService(str, Enum):
    # Paypack handles both MTN and Airtel
    MOBILE_MONEY = "mobile_money"


class PaymentController:
    def __init__(
        self,
        payment_service: PaymentService,
        input_data: PaypackPaymentSchema,
    ):
        self.payment_service = payment_service
        self.input_data = input_data

    def __call__(self):
        match self.payment_service:
            case PaymentService.MOBILE_MONEY:
                self.validate_input_data(PaypackPaymentSchema)
                return self.paypack_payment()

    def validate_input_data(self, expected_data: type):
        if not isinstance(self.input_data, expected_data):
            raise AppError(
                detail=f"Expected {expected_data} but got {type(self.input_data)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def paypack_payment(self):
        """Handle Paypack cashin (deposit) payment - supports both MTN and Airtel"""
        data = PaypackPaymentSchema(**self.input_data.model_dump())
        
        # Generate idempotency key if not provided
        idempotency_key = data.idempotency_key or secrets.token_hex(16)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {settings.PAYPACK_ACCESS_TOKEN}',
            'Idempotency-Key': idempotency_key
        }
        
        # Prepare payload for Paypack API
        payload = {
            "amount": data.amount,
            "number": data.phone_number
        }
        
        try:
            # Make cashin request to Paypack
            push_payment = requests.post(
                url=f"{PaymentPushCallback.PAYPACK_BASE_URL}/transactions/cashin",
                headers=headers,
                json=payload,
                timeout=30
            )
            push_payment.raise_for_status()
            
            response_data = push_payment.json()
            
            # Return in consistent format
            return {
                "status": "success",
                "transaction_ref": response_data.get("ref"),
                "amount": response_data.get("amount"),
                "kind": response_data.get("kind"),
                "payment_status": response_data.get("status"),
                "created_at": response_data.get("created_at"),
                "app_transaction_id": data.app_transaction_id,
                "reference": data.reference,
                "phone_number": data.phone_number
            }
            
        except requests.exceptions.RequestException as e:
            raise AppError(
                detail=f"Payment failed: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaymentSchemaPush(BaseModel):
    amount: int
    reference: str
    phone_number: str
    app_transaction_id: str


def create_payment(input_data: PaymentSchemaPush):
    """
    Create a mobile money payment using Paypack.
    Paypack automatically detects if it's MTN or Airtel based on phone number.
    """
    payment_push = PaymentController(
        payment_service=PaymentService.MOBILE_MONEY,
        input_data=PaypackPaymentSchema(**input_data.model_dump()),
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


class NetworkRegexSchema(Enum):
    # Paypack automatically detects MTN or Airtel
    mtn = ["^250(78|79)[0-9]{7}$"]
    airtel = ["^250(72|73)[0-9]{7}$"]


def validate_phone_number(phone_number: str) -> str:
    """
    Validate Rwanda phone number format.
    Returns formatted phone number (with 250 prefix).
    Paypack will automatically route to MTN or Airtel.
    """
    # Add country code if not present
    if phone_number.startswith("07"):
        phone_number = f"250{phone_number}"
    
    # Check if it's a valid Rwanda mobile number
    is_valid = False
    for network in NetworkRegexSchema:
        for regex in network.value:
            if re.match(regex, phone_number):
                is_valid = True
                break
        if is_valid:
            break
    
    if not is_valid:
        raise AppError(
            detail="Invalid Rwanda phone number. Use format 078xxxxxxx or 072xxxxxxx",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    
    return phone_number


def get_paypack_transaction_status(transaction_ref: str):
    """
    Check transaction status from Paypack using the transaction reference.
    Use this to verify payment status.
    """
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.PAYPACK_ACCESS_TOKEN}'
    }
    
    try:
        response = requests.get(
            url=f"{PaymentPushCallback.PAYPACK_BASE_URL}/transactions/find/{transaction_ref}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        transaction_data = response.json()
        
        return {
            "ref": transaction_data.get("ref"),
            "amount": transaction_data.get("amount"),
            "client": transaction_data.get("client"),
            "fee": transaction_data.get("fee"),
            "kind": transaction_data.get("kind"),
            "merchant": transaction_data.get("merchant"),
            "status": transaction_data.get("status"),
            "timestamp": transaction_data.get("timestamp")
        }
        
    except requests.exceptions.RequestException as e:
        raise AppError(
            detail=f"Failed to retrieve transaction status: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )