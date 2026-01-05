from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from src.config import settings

engine = create_engine(settings.DB_URL, echo=False, pool_size=20, max_overflow=50)


def getdb():
    with Session(engine) as session:
        yield session


database = Annotated[Session, Depends(getdb)]
