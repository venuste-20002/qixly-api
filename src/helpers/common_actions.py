from typing import Generic, TypeVar
from uuid import UUID

from fastapi import status
from sqlmodel import Session

from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch

T = TypeVar("T")


class CommonUsedActions(Generic[T]):
    def __init__(self, table_name: T, uuid: UUID, database: Session) -> None:
        self.table_name = table_name
        self.uuid = uuid
        self.database = database

    async def get_record(self):
        get_record = Fetch(self.table_name, "id", self.uuid)
        get_record_response = await get_record.get_single_value()
        if not get_record_response:
            raise AppError(
                f"Record of {self.uuid} not Found", status.HTTP_404_NOT_FOUND
            )
        return get_record_response

    async def delete_record(self):
        record = await self.get_record()

        record.is_deleted = True

        self.database.add(record)
        self.database.commit()
        self.database.refresh(record)

        return record

    async def change_status(self):
        record = await self.get_record()
        record.is_active = not record.is_active
        self.database.add(record)
        self.database.commit()
        self.database.refresh(record)
        return record

    async def update_single_record(self, input_data: T):
        record = await self.get_record()

        record_update = input_data.model_dump(exclude_unset=True)

        record.sqlmodel_update(record_update)

        self.database.add(record)
        self.database.commit()
        self.database.refresh(record)

        return record
