from typing import Generic, List, Optional, Type, TypeVar

from fastapi import status
from sqlmodel import Enum, Session, asc, desc, select

from src.utils.custom_errors import AppError


class Fetch:
    def __init__(
        self,
        table_name,
        table_field,
        value,
        session: Session,
        where: Optional[list] = [],
    ) -> None:
        self.table_name = table_name
        self.table_field = table_field
        self.value = value
        self.session = session
        self.where = where

    def query(self):
        get_value_query = (
            select(self.table_name)
            .where(
                *self.where,
                getattr(self.table_name, self.table_field) == self.value,
            )
            .where(getattr(self.table_name, "is_deleted") == False)
        )
        return get_value_query

    async def get_single_value(self):
        get_query = self.query()
        get_single_value = self.session.exec(get_query).first()
        if get_single_value:
            return get_single_value
        return None

    async def get_single_value_id(self):
        get_query = self.query()
        get_single_value_id = self.session.exec(get_query).first()
        if get_single_value_id:
            return get_single_value_id.id
        return None

    async def get_all_value(self):
        get_query = self.query()
        get_all_values = self.session.exec(get_query).all()
        if get_all_values:
            return get_all_values
        return None


T = TypeVar("T")


class OrderEnum(str, Enum):
    ASC = "asc"
    DESC = "desc"


class Fetcher(Generic[T]):
    def __init__(
        self,
        database: Session,
        table: tuple = (),
        where: Optional[tuple] = (),
        join: Optional[List[Type]] = None,
        sort: Optional[str] = None,
        offset: Optional[int] = None,
        limits: Optional[int] = None,
        order: Optional[OrderEnum] = None,
        error: Optional[str] = "Record not found",
        status_code: int = status.HTTP_404_NOT_FOUND,
    ) -> None:
        self.database = database
        self.table = table
        self.where = where
        self.join = join
        self.sort = sort
        self.order = order
        self.offset = offset
        self.limits = limits
        self.error = error
        self.status = status_code

    def query(self):
        query = select(*self.table).where(
            *self.where,
            getattr(self.table[0], "is_deleted") == False,
        )

        if self.join:
            for condition in self.join:
                query += query.join(condition, isouter=True)

        if self.offset:
            query = query.offset(self.offset)

        if self.limits:
            query = query.limit(self.limits)

        if self.order and self.order == OrderEnum.ASC:
            query = query.order_by(
                asc(
                    getattr(self.table[0], self.sort or "created_at"),
                )
            )
        else:
            query = query.order_by(
                desc(
                    getattr(self.table[0], self.sort or "created_at"),
                )
            )

        return query

    def get_one(self):
        get_query = self.query()
        get_single_value = self.database.exec(get_query).first()

        if not get_single_value:
            raise AppError(self.error, self.status)

        return get_single_value

    def get_all(self):
        get_query = self.query()

        get_all_values = self.database.exec(get_query).all()
        if not get_all_values:
            raise AppError(self.error, self.status)

        return get_all_values

    def get_exist(self):
        get_query = self.query()

        get_single_value = self.database.exec(get_query).first()
        if get_single_value:
            raise AppError(self.error, self.status)
        return get_single_value

    def get_value(self):
        get_query = self.query()
        get_single_value = self.database.exec(get_query).first()

        return get_single_value
