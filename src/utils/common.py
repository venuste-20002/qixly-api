from enum import Enum
from fastapi import Query,Depends
from typing import Annotated


# Common Query Params like offset and limit

class Pagination:
    def __init__(
            self,
            page: Annotated[int, Query(ge=1)] = 1,
            per_page: Annotated[int, Query(ge=1, lte=100)] = 10,
    ):
        self.page = page
        self.per_page = per_page


PaginationDep = Annotated[Pagination, Depends()]


class Order(str, Enum):
    ASC = "ASC"
    DESC = "DESC"