from datetime import datetime

from fastapi import status

from src.models.sales_model import SalesItem, SaleStatus
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch


class ClaimOrderController:
    def __init__(self, sales_item_id, database):
        self.token = sales_item_id
        self.database = database

    async def get_order(self):

        get_order_data = await Fetch(
            SalesItem,
            "id",
            self.token,
            self.database,
            where=[
                getattr(SalesItem, "status") == SaleStatus.UNUSED.value,
            ],
        ).get_single_value()

        if not get_order_data:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales Item not found",
            )

        return get_order_data

    async def claim_order(self):
        res = await self.get_order()

        res.status = SaleStatus.USED.value
        res.used_date = datetime.now()

        self.database.add(res)
        self.database.commit()
        self.database.refresh(res)

        return res
