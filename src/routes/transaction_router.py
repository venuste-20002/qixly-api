from enum import Enum
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.controllers.transaction_controller import (
    get_single_transaction_controller,
    get_transaction_controller,
)
from src.database import database
from src.helpers.paginator import Paginate, PaginationResponse
from src.middlewares.auth import auth
from src.models.transaction_model import TransactionSchema, TransactionSingleSchema
from src.utils.custom_errors import AppError

router = APIRouter(
    tags=["Transactions"], dependencies=[Depends(auth)], prefix="/transactions"
)


class OrderType(str, Enum):
    ASC = "asc"
    DESC = "desc"


@router.get(
    "",
    summary="Retrieve Transactions",
    description="Fetch a list of transactions filtered by various optional parameters such as date range, user IDs, status, and more.",
)
async def get_transactions(
    db: database,
    start_date: str = Query(
        default=None,
        description="Start date for the transactions in  (default: 30 days ago).",
    ),
    end_date: str = Query(
        default=None,
        description="End date for the transactions  (default: current date).",
    ),
    paginate: Paginate = Depends(),
    user_ids: Optional[List[UUID]] = Query(
        None, description="List of user IDs to filter transactions."
    ),
    tx_status: Optional[List[str]] = Query(
        None,
        description="List of transaction statuses to filter (e.g., 'success', 'pending').",
    ),
    order: Optional[OrderType] = None,
    payment_channel: Optional[List[str]] = Query(
        None, description="List of payment channels to filter"
    ),
    cart_id: Optional[List[UUID]] = Query(
        None, description="List of cart IDs to filter transactions."
    ),
    card_variant_id: Optional[List[UUID]] = Query(
        None, description="List of card variant IDs to filter transactions."
    ),
) -> PaginationResponse[TransactionSchema]:
    transactions = await get_transaction_controller(
        db,
        start_date,
        end_date,
        paginate,
        user_ids,
        tx_status,
        payment_channel,
        cart_id,
        card_variant_id,
        order,
    )

    if isinstance(transactions, AppError):
        raise AppError(status_code=transactions.status_code, detail=transactions.detail)

    return transactions


@router.get("/{transaction_id}", response_model=TransactionSingleSchema)
async def get_transaction(transaction_id: UUID, db: database):
    return await get_single_transaction_controller(transaction_id, db)
