import math
from dataclasses import dataclass
from typing import Annotated, Generic, List, Optional, Type, TypeVar

from fastapi.params import Query
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, asc, desc, func, select

from src.database import engine
from src.utils.fetcher import OrderEnum
from src.utils.loader import get_search_query

T = TypeVar("T")


@dataclass
class Paginate:
    page: Annotated[int, Query(ge=1)] = 1
    per_page: Annotated[int, Query(ge=1, lte=100)] = 10


class PaginatorResultSchema(BaseModel, Generic[T]):
    total_count: int
    total_pages: int
    page: int
    per_page: int
    results: List[T]


class Pagination(Generic[T]):
    @staticmethod
    async def paginate(
        table_name: T, paginate: Paginate, result_schema: T, filters: tuple = ()
    ) -> PaginatorResultSchema:
        with Session(engine) as session:
            offset = (paginate.page - 1) * paginate.per_page

            fetching_query = (
                select(table_name)
                .where(*filters, False == getattr(table_name, "is_deleted"))
                .offset(offset)
                .limit(paginate.per_page)
            )
            total_data = session.exec(fetching_query).all()

            count_query = (
                select(func.count())
                .select_from(table_name)
                .where(*filters, False == getattr(table_name, "is_deleted"))
            )
            count = session.exec(count_query).one()

            page_page_total: int = math.ceil(count / paginate.per_page)

            total_result: List[T] = []
            for data in total_data:
                total_result.append(result_schema(**data.model_dump()))

        return PaginatorResultSchema(
            total_count=count,
            total_pages=page_page_total,
            page=paginate.page,
            per_page=paginate.per_page,
            results=total_result,
        )


M = TypeVar("M")


class PaginatorSchema(SQLModel):
    total_count: int
    total_pages: int
    page: int
    per_page: int


class PaginationResponse(BaseModel, Generic[M]):
    pagination: PaginatorSchema
    data: List[M]


Q = TypeVar("Q", bound="CommonBase")


class PaginatorQuery(Generic[Q]):
    @staticmethod
    async def paginate(
        table_name: Type[Q],
        input_data: Paginate,
        session: Session,
        filters: tuple = (),
        order: Optional[OrderEnum] = None,
        search: Optional[str] = None,
    ):
        offset = (input_data.page - 1) * input_data.per_page

        fetching_query = (
            select(table_name)
            .where(*filters, False == getattr(table_name, "is_deleted"))
            .offset(offset)
            .limit(input_data.per_page)
        )

        if order and order == OrderEnum.ASC:
            fetching_query = fetching_query.order_by(
                asc(
                    getattr(table_name, "created_at"),
                )
            )
        else:
            fetching_query = fetching_query.order_by(
                desc(
                    getattr(table_name, "created_at"),
                )
            )

        if search and len(search) > 0:
            search_query = get_search_query(table_name, search)
            fetching_query = fetching_query.where(search_query)

        total_data = session.exec(fetching_query).all()

        get_count_query = (
            select(func.count())
            .select_from(table_name)
            .where(*filters, False == getattr(table_name, "is_deleted"))
        )
        count = session.exec(get_count_query).one()

        page_page_total: int = math.ceil(count / input_data.per_page)

        return (
            PaginatorSchema(
                total_count=count,
                total_pages=page_page_total,
                page=input_data.page,
                per_page=input_data.per_page,
            ),
            total_data,
        )
