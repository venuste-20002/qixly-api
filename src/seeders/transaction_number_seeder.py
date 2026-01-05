from sqlmodel import Session, text

from src.database import engine
from src.utils import  constants

async def transaction_number_seeders():
    with Session(engine) as session:
        query = text(
            f"CREATE SEQUENCE IF NOT EXISTS {constants.TRANSACTION_NUMBER_SEQ} as BIGINT INCREMENT 1 START WITH 1;"
        )
        session.exec(query)
        session.commit()
