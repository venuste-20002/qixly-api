from enum import Enum
from typing import Type, TypeVar

from sqlmodel import Session, SQLModel, select

from src.database import engine

T = TypeVar("T", bound=SQLModel)
E = TypeVar("E")


async def create_enum_seeders(enum_value: Type[E], table_name: Type[T], field: str):
    if not hasattr(table_name, "__table__"):
        raise TypeError(f"{table_name} is not a valid SQLModel table.")

    if not hasattr(table_name, field):
        raise TypeError(f"{table_name} has no field {field}")

    if not issubclass(enum_value, Enum):
        raise TypeError(f"{enum_value} is not a valid Enum type.")

    with Session(engine) as session:
        for enum_value in enum_value:
            query_get_value = select(table_name).where(
                getattr(table_name, field) == enum_value.value
            )
            value_found = session.exec(query_get_value).first()

            if value_found:
                continue

            values = {field: enum_value.value}
            create_seed = table_name(**values)
            session.add(create_seed)

        session.commit()
