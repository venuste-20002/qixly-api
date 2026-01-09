import re
import hmac
import hashlib
import base64
import time
from datetime import datetime
from enum import Enum
from typing import Optional

import requests 
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fastapi import status, Header
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select

from src.config import settings
from src.helpers.generate_sales_item_number import generate_sales_item_number
from src.models.card_model import CardVariant
from src.models.cart_model import Cart, CartItem, CartStatus
from src.models.sales_model import SalesItem
from src.models.transaction_model import Transactions, TransactionStatus
from src.utils.custom_errors import AppError


def create_requests_session():
    """
    Create a requests session with retry logic.
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3, 
        backoff_factor=1, 
        status_forcelist=[429, 500, 502, 503, 504], 
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def get_paypack_access_token():
    """Get access token from Paypack API with retry logic."""
    base_url = settings.PAYPACK_BASE_URL or "https://payments.paypack.rw/api"
    auth_url = f"{base_url}/auth/agents/authorize"
    
    try:
        session = create_requests_session()
        response = session.post(
            auth_url,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            json={
                "client_id": settings.PAYPACK_CLIENT_ID,
                "client_secret": settings.PAYPACK_CLIENT_SECRET,
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data["access"]
    except requests.exceptions.ConnectionError as e:
        raise AppError(
            detail=f"Cannot connect to Paypack API. Please check your internet connection or try again later. Error: {str(e)}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except requests.exceptions.Timeout as e:
        raise AppError(
            detail=f"Paypack API request timed out. Please try again. Error: {str(e)}",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except requests.exceptions.HTTPError as e:
        raise AppError(
            detail=f"Paypack authentication failed: {e.response.text if hasattr(e, 'response') else str(e)}",
            status_code=e.response.status_code if hasattr(e, 'response') else status.HTTP_502_BAD_GATEWAY,
        )
    except requests.exceptions.RequestException as e:
        raise AppError(
            detail=f"Failed to authenticate with Paypack: {str(e)}",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    except KeyError:
        raise AppError(
            detail="Invalid response from Paypack API - missing access token",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    except Exception as e:
        raise AppError(
            detail=f"Authentication error: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_sales_number(number: int, base: int = 36, padding: int = 0):
    """Convert number to base representation."""
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


class PaypackCashinSchema(SQLModel):
    """Schema for Paypack cashin request."""
    amount: int
    number: str


class PaymentService(str, Enum):
    PAYPACK = "paypack"


class PaymentController:
    """Controller for handling different payment services."""
    
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
        """Validate input data matches expected schema."""
        if not isinstance(self.input_data, expected_data):
            raise AppError(
                detail=f"Expected {expected_data} but got {type(self.input_data)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def paypack_cashin(self):
        """Initiate a Paypack cashin transaction."""
        data = PaypackCashinSchema(**self.input_data.model_dump())
        try:
            validated_number = normalize_phone_number(data.number)
            data.number = validated_number
        except AppError:
            raise
        
        token = get_paypack_access_token()
        base_url = settings.PAYPACK_BASE_URL or "https://payments.paypack.rw/api"
        cashin_url = f"{base_url}/transactions/cashin"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f"Bearer {token}",
            'X-Webhook-Mode': settings.PAYPACK_WEBHOOK_MODE  
        }
        
        payload = data.model_dump()
        
        try:
            session = create_requests_session()
            response = session.post(
                cashin_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise AppError(
                detail=f"Cannot connect to Paypack API. Please check your internet connection.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except requests.exceptions.Timeout as e:
            raise AppError(
                detail=f"Paypack cashin request timed out. Please try again.",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get('message', e.response.text)
                except:
                    error_detail = e.response.text
            
            raise AppError(
                detail=f"Paypack cashin failed: {error_detail}",
                status_code=e.response.status_code if hasattr(e, 'response') else status.HTTP_502_BAD_GATEWAY,
            )
        except requests.exceptions.RequestException as e:
            raise AppError(
                detail=f"Paypack cashin failed: {str(e)}",
                status_code=status.HTTP_502_BAD_GATEWAY,
            )


class PaymentSchemaPush(BaseModel):
    """Schema for payment push request."""
    amount: int
    reference: str
    network: str
    phone_number: str
    app_transaction_id: str


def create_payment(input_data: PaymentSchemaPush):
    """Create a payment transaction."""
    try:
        phone_number = normalize_phone_number(input_data.phone_number)
    except AppError:
        raise
    except Exception as e:
        raise AppError(
            detail=f"Error normalizing phone number: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    paypack_data = PaypackCashinSchema(
        amount=input_data.amount,
        number=phone_number,
    )

    payment_push = PaymentController(
        payment_service=PaymentService.PAYPACK,
        input_data=paypack_data,
    )
    data = payment_push()
    return data


class PaymentTransactionCallbackSchema(SQLModel):
    """Schema for payment transaction callback."""
    transaction_id: str
    tx_status: TransactionStatus
    payment_channel: str
    transaction_time: datetime
    channel_transaction_id: str


class PaypackCallbackData(SQLModel):
    """Schema for Paypack callback data."""
    ref: str
    amount: int
    fee: int
    client: str
    merchant: str
    timestamp: str
    status: Optional[str] = None 
    kind: Optional[str] = None  
    provider: Optional[str] = None  
    created_at: Optional[str] = None
    processed_at: Optional[str] = None


class PaypackCallbackSchema(SQLModel):
    """Schema for Paypack webhook callback."""
    event_id: str
    kind: str  
    created_at: str
    data: PaypackCallbackData


def verify_paypack_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify Paypack webhook signature.
    
    Args:
        payload: The raw request body as string
        signature: The x-paypack-signature header value
        secret: Your webhook secret key
    
    Returns:
        True if signature is valid, False otherwise
    """
    if not secret or not signature:
        return False
    
    hash_digest = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash_digest).decode()
    return hmac.compare_digest(signature, expected_signature)

def payment_callback_controller(
    transaction: PaymentTransactionCallbackSchema, 
    db: Session
):
    """Process payment callback and update database."""
    
    tx_data = db.exec(
        select(Transactions)
        .where(Transactions.id == transaction.transaction_id)
        .where(Transactions.tx_status == TransactionStatus.PENDING.value)
    ).first()

    if not tx_data:
        raise AppError(
            detail="Transaction not found or already processed",
            status_code=status.HTTP_404_NOT_FOUND,
        )
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
                sales_number_sequence = generate_sales_item_number(db)
                sales_number = get_sales_number(int(sales_number_sequence))

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

    elif transaction.tx_status == TransactionStatus.FAILED.value:
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
    callback: PaypackCallbackSchema, 
    db: Session, 
    raw_body: str = None,
    x_paypack_signature: str = None
):
    """
    Handle Paypack webhook callback.
    
    Args:
        callback: Parsed callback data
        db: Database session
        raw_body: Raw request body for signature verification
        x_paypack_signature: Signature from x-paypack-signature header
    """
    if settings.PAYPACK_WEBHOOK_SECRET and x_paypack_signature:
        if not raw_body:
            raise AppError(
                detail="Raw body required for signature verification",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        is_valid = verify_paypack_signature(
            raw_body, 
            x_paypack_signature, 
            settings.PAYPACK_WEBHOOK_SECRET
        )
        
        if not is_valid:
            raise AppError(
                detail="Invalid webhook signature",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

    transaction_id = callback.data.ref

    if callback.kind == "transaction:processed":
        if callback.data.status == "successful":
            tx_status = TransactionStatus.SUCCESS
        else:
            tx_status = TransactionStatus.FAILED
    elif callback.kind == "transaction:created":
        tx_status = TransactionStatus.PENDING
    else:
        return {"status": "unknown event", "event": callback.kind}

    timestamp_str = callback.data.timestamp
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str.replace('Z', '+00:00')
    transaction_time = datetime.fromisoformat(timestamp_str)

    transaction = PaymentTransactionCallbackSchema(
        transaction_id=transaction_id,
        tx_status=tx_status,
        payment_channel="paypack",
        transaction_time=transaction_time,
        channel_transaction_id=callback.data.client,
    )

    return payment_callback_controller(transaction, db)


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number to Paypack format (07XXXXXXXX).
    
    Accepts formats:
    - 0781234567 (10 digits with leading 0)
    - 781234567 (9 digits without leading 0)
    - 250781234567 (12 digits with country code, no leading 0 after code)
    - 2500781234567 (13 digits with country code and leading 0)
    - +250781234567 or +2500781234567
    
    Args:
        phone_number: Phone number in various formats
    
    Returns:
        Normalized phone number in format 07XXXXXXXX
    
    Raises:
        AppError: If phone number format is invalid
    """
    phone = phone_number.strip().replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    
    if phone.startswith("250"):
        phone = phone[3:]  
    
    if len(phone) == 9 and phone[0] != "0":
        phone = "0" + phone

    if len(phone) != 10:
        raise AppError(
            detail=f"Invalid phone number length. Expected 10 digits (07XXXXXXXX), got {len(phone)} digits. Input: {phone_number}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not phone.startswith(("072", "073", "078", "079")):
        raise AppError(
            detail=f"Invalid phone number prefix. Must start with 072 (Airtel), 073 (Airtel), 078 (MTN), or 079 (MTN). Got: {phone[:3]} from input: {phone_number}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not phone.isdigit():
        raise AppError(
            detail=f"Phone number must contain only digits. Got: {phone_number}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    
    return phone


def phone_network_action(phone_number: str) -> str:
    """
    Validate phone number and determine network.
    
    Args:
        phone_number: Phone number to validate
    
    Returns:
        Network identifier ('paypack')
    
    Raises:
        AppError: If phone number is invalid
    """
    normalized = normalize_phone_number(phone_number)
    if normalized.startswith("078") or normalized.startswith("079"):
        provider = "MTN Rwanda"
    elif normalized.startswith("072") or normalized.startswith("073"):
        provider = "Airtel Rwanda"
    else:
        raise AppError(
            detail="Phone number must be MTN (078/079) or Airtel (072/073) Rwanda number.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    
    return "paypack"


def find_transaction(ref: str) -> dict:
    """
    Find a transaction by reference.
    
    Args:
        ref: Transaction reference
    
    Returns:
        Transaction details
    """
    token = get_paypack_access_token()
    base_url = settings.PAYPACK_BASE_URL or "https://payments.paypack.rw/api"
    find_url = f"{base_url}/transactions/find/{ref}"
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {token}"
    }
    
    try:
        session = create_requests_session()
        response = session.get(find_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as e:
        raise AppError(
            detail=f"Cannot connect to Paypack API to find transaction.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except requests.exceptions.RequestException as e:
        raise AppError(
            detail=f"Failed to find transaction: {str(e)}",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )