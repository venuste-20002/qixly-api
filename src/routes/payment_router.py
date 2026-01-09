from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from src.database import getdb
from src.helpers.payment import paypack_callback_controller, PaypackCallbackSchema
from src.middlewares.auth import auth

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/webhook")
async def paypack_webhook(
    callback: PaypackCallbackSchema,
    request: Request,
    db: Session = Depends(getdb),
):
    """
    Handle Paypack webhook callbacks for payment confirmations.
    This endpoint receives notifications from Paypack when payments are completed.
    """
    # Optional: Get signature from headers for verification
    signature = request.headers.get("X-Paypack-Signature")

    # Process the callback
    result = paypack_callback_controller(callback, db, signature)

    return {"status": "success", "message": "Webhook processed", "data": result}


@router.get("/status/{transaction_id}")
async def get_payment_status(
    transaction_id: str,
    db: Session = Depends(getdb),
    user=Depends(auth),
):
    """
    Get the status of a payment transaction.
    """
    from src.models.transaction_model import Transactions

    transaction = db.get(Transactions, transaction_id)
    if not transaction:
        return {"error": "Transaction not found"}

    return {
        "transaction_id": transaction.id,
        "status": transaction.tx_status,
        "amount": transaction.total_payed_amount,
        "phone_number": transaction.phone_number,
        "network": transaction.network,
    }
