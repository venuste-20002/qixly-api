from datetime import datetime
from decimal import Decimal

from sqlmodel import Session, text

from src.utils import constants


def generate_date_stamp() -> str:
    """This function generate date stamp for transactions for example 21010123"""
    current_datetime = datetime.now()
    return current_datetime.strftime("%y%m%d")


def get_system_hour_unique() -> str:
    return f"{constants.SYSTEM_ID}{generate_date_stamp()}"


def generate_transaction_start_value() -> Decimal:
    return Decimal(get_system_hour_unique()) * constants.TRANSACTION_MULTIPLIER


def __set_start_value(base_value, session: Session):
    generated_value = generate_transaction_start_value()
    session.exec(
        text(
            f"SELECT setval('{constants.TRANSACTION_NUMBER_SEQ}', {generated_value}, true) from {constants.TRANSACTION_NUMBER_SEQ} where last_value = {base_value}"
        )
    )


def generate_transaction_number(session: Session) -> int:
    base_value = session.exec(
        text(f"SELECT last_value FROM {constants.TRANSACTION_NUMBER_SEQ}")
    ).scalar()
    if not str(base_value).startswith(get_system_hour_unique()):
        __set_start_value(base_value, session)
    return session.exec(
        text(f"SELECT nextval('{constants.TRANSACTION_NUMBER_SEQ}')")
    ).scalar()
