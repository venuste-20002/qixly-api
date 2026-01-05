from typing import Generic, List, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.sql import func
from sqlmodel import Field, Session, select

from src.database import engine

M = TypeVar("M")


class Pagination(BaseModel):
    count: int = Field(description="Total items before pagination")
    total_pages: int = Field(description="Number of pages depending on the page size")
    page_size: int = Field(description="Number of items returned in the response")
    page: int = Field(description="Current page number")


class PaginatedResponse(BaseModel, Generic[M]):
    pagination: Union[Pagination, None]
    data: List[M] = Field(
        description="List of items returned in the response following given criteria"
    )


class ListResponse(BaseModel, Generic[M]):
    message: str = Field(description="Message returned in the response")
    data: List[M] = Field(
        description="List of items returned in the response following given criteria"
    )


class GeneralResponse(BaseModel, Generic[M]):
    message: str = Field(description="Message returned in the response")
    data: Union[M, None] = Field(description="Data returned in the response")


class Paginator:
    def __init__(self, session: Session, query: select, page: int, per_page: int):
        self.session = session
        self.query = query
        self.page = page
        self.per_page = per_page
        self.limit = per_page
        self.offset = (page - 1) * per_page
        # computed later
        self.number_of_pages = 0
        self.next_page = ""
        self.previous_page = ""

    def get_response(self) -> dict:
        return {
            "pagination": {
                "count": self._get_total_count(),
                "total_pages": self._get_number_of_pages(self._get_total_count()),
                "page_size": self.per_page,
                "page": self.page,
            },
            "data": [
                item
                for item in self.session.scalars(
                    self.query.offset(self.offset).limit(self.limit)
                )
            ],
        }

    def get_pagination(self):
        return {
            "count": self._get_total_count(),
            "total_pages": self._get_number_of_pages(self._get_total_count()),
            "page_size": self.per_page,
            "page": self.page,
        }

    def _get_number_of_pages(self, count: int) -> int:
        rest = count % self.per_page
        quotient = count // self.per_page
        return quotient if not rest else quotient + 1

    def _get_total_count(self) -> int:
        count = self.session.scalar(
            select(func.count()).select_from(self.query.subquery())
        )
        self.number_of_pages = self._get_number_of_pages(count)
        return count


async def paginate(query: select, page: int, per_page: int) -> dict:
    with Session(engine) as session:
        paginator = Paginator(session, query, page, per_page)
        return await paginator.get_response()


def paginate_with_session(session, query: select, page: int, per_page: int) -> dict:
    paginator = Paginator(session, query, page, per_page)
    return paginator.get_response()
