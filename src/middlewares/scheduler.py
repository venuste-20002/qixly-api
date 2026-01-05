from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from src.database import engine
from src.models.card_model import Card, CardStatus
from src.utils.logger import logger


def change_card_status_expired():
    with Session(engine) as session:
        get_all_expired_cards_query = session.exec(
            select(Card)
            .where(Card.expiration_date < datetime.now())
            .where(Card.is_deleted == False)
        ).all()

        for card in get_all_expired_cards_query:
            card.status = CardStatus.EXPIRED.value
            session.add(card)

        session.commit()


def change_card_status_startdate():
    with Session(engine) as session:
        get_all_expired_cards_query = session.exec(
            select(Card)
            .where(Card.started_date <= datetime.now())
            .where(Card.is_deleted == False)
        ).all()

        for card in get_all_expired_cards_query:
            card.status = CardStatus.ACTIVE.value
            session.add(card)

        session.commit()


def cron_job():
    logger.info("Cron job is running...")

    change_card_status_expired()
    change_card_status_startdate()

    logger.info("Cron job is successfully completed.")


scheduler = BackgroundScheduler()

scheduler.add_job(
    cron_job,
    CronTrigger(hour=00, minute=00, second=00),
)

scheduler.start()
