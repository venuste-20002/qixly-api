from sqlmodel import Session

from src.config import settings
from src.controllers.trusted_controller import (
    generate_rsa_key_pair,
    serialize_private_key,
)
from src.database import engine
from src.models.trusted_model import Trusted
from src.utils.fetcher import Fetcher


async def generate_private_key():
    with Session(engine) as session:
        is_private_key_exist = Fetcher(
            database=session,
            table=(Trusted,),
            where=(Trusted.name == settings.SUPER_PRIVATE_KEY,),
        ).get_value()

        if is_private_key_exist:
            return

        create_private_key = generate_rsa_key_pair()
        serialize_private_ = serialize_private_key(create_private_key)

        session.add(
            Trusted(
                name=settings.SUPER_PRIVATE_KEY,
                private_key=serialize_private_,
            ),
        )
        session.commit()
        session.close()
