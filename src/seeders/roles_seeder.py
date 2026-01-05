from sqlmodel import Session

from src.database import engine
from src.models.authentication_model import Roles, RolesEnum
from src.utils.fetcher import Fetch


async def roles_seeder():
    with Session(engine) as session:
        for role in RolesEnum:
            query_get_role = await Fetch(Roles, "name", role.name,session).get_single_value()

            if query_get_role:
                continue

            role_enum_save = Roles(
                name=role.name, code=role.value, description=f"{role.name} ROLE"
            )

            session.add(role_enum_save)
        session.commit()
