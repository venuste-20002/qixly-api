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
    signature = request.headers.get("X-Paypack-Signature")
    result = paypack_callback_controller(callback, db, signature)

    return {"status": "success", "message": "Webhook processed", "data": result}

