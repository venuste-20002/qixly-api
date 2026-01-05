from datetime import datetime
from decimal import Decimal

from sqlmodel import text

from src.utils import constants


def generate_date_stamp_() -> str:
    """This function generate date stamp for transactions for example 21010123"""
    current_datetime = datetime.now()
    return current_datetime.strftime("%y%m")


def generate_sales_items_start_value() -> Decimal:
    return Decimal(generate_date_stamp_()) * constants.SALES_ITEM_MULTIPLIER


def ___set_start_value(base_value, session):
    generated_value = generate_sales_items_start_value()
    session.exec(
        text(
            f"SELECT setval('{constants.SALES_ITEM_NUMBER_SEQ}', {generated_value}, true) from {constants.SALES_ITEM_NUMBER_SEQ} where last_value = {base_value}"
        )
    )


def generate_sales_item_number(session):
    base_value = session.exec(
        text(f"SELECT last_value FROM {constants.SALES_ITEM_NUMBER_SEQ}")
    ).scalar()
    if not str(base_value).startswith(generate_date_stamp_()):
        ___set_start_value(base_value, session)
    return session.exec(
        text(f"SELECT nextval('{constants.SALES_ITEM_NUMBER_SEQ}')")
    ).scalar()
