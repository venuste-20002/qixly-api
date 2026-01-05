from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from src.database import database
from src.helpers.paginator import Paginate, PaginationResponse, PaginatorQuery
from src.models.cart_model import CartItem
from src.models.transaction_model import (
    Transactions,
    TransactionSchema,
    TransactionSingleSchema,
)
from src.schemas.card_schema import CardResponse, CardvariantResponse, CategoryResponse
from src.schemas.cart_schemas import CartResponse
from src.schemas.sales_schema import SalesFullItemsResponse, SalesItemsResponse
from src.schemas.users_schema import UserDataSchema
from src.utils.fetcher import Fetcher


async def get_transaction_controller(
    db: database,
    start_date: str,
    end_date: str,
    paginate: Paginate,
    user_ids: Optional[List[UUID]] = None,
    tx_status: Optional[List[str]] = None,
    payment_channel: Optional[List[str]] = None,
    cart_id: Optional[List[UUID]] = None,
    card_variant_id: Optional[List[UUID]] = None,
    order: Optional[str] = None,
) -> PaginationResponse[TransactionSchema]:

    filters = []
    if start_date:
        filters.append(Transactions.created_at >= start_date)
    if end_date:
        filters.append(Transactions.created_at <= end_date)

    if user_ids:
        filters.append(Transactions.user_id.in_(user_ids))

    if tx_status:
        filters.append(Transactions.tx_status.in_(tx_status))

    if payment_channel:
        filters.append(Transactions.payment_channel.in_(payment_channel))

    if cart_id:
        filters.append(Transactions.cart_id.in_(cart_id))

    if card_variant_id:
        filters.append(CartItem.card_variant_id.in_(card_variant_id))

    paginated_result, tx_data = await PaginatorQuery.paginate(
        table_name=Transactions,
        input_data=paginate,
        session=db,
        filters=tuple(filters),
        order=order,
    )

    return PaginationResponse(
        pagination=paginated_result,
        data=[
            TransactionSchema(
                **data.model_dump(),
                user=UserDataSchema(
                    **data.user.model_dump(),
                ),
                cart=CartResponse(**data.cart.model_dump()),
            )
            for data in tx_data
        ],
    )


# function of get the single transaction
async def get_single_transaction_controller(
    transaction_id: UUID, db: Session
) -> TransactionSingleSchema:

    transaction = Fetcher(
        database=db,
        table=(Transactions,),
        where=(Transactions.id == transaction_id,),
        error="Transaction not found",
    ).get_one()

    return TransactionSingleSchema(
        **transaction.model_dump(),
        user=UserDataSchema(**transaction.user.model_dump()),
        sales_items=(
            [
                SalesFullItemsResponse(
                    item=SalesItemsResponse(**item.model_dump()),
                    card_variant=CardvariantResponse(
                        **item.card_variant.model_dump(),
                        card=CardResponse(
                            **item.card_variant.card.model_dump(),
                            category=CategoryResponse(
                                **item.card_variant.card.category.model_dump()
                            ),
                        ),
                    ),
                )
                for item in transaction.cart.salesitem
            ]
            if transaction.cart.salesitem
            else []
        ),
    )
