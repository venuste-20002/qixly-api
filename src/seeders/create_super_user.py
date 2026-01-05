from fastapi import status
from sqlmodel import Session, select

from src.config import settings
from src.database import engine
from src.models.authentication_model import (
    Roles,
    RolesEnum,
    Users,
    UserScope,
    UserScopeEnum,
)
from src.utils.custom_errors import AppError
from src.utils.password_encrypt import hash_password


async def create_super_user():
    with Session(engine) as session:

        get_roles_query = select(Roles).where(
            getattr(Roles, "code") == RolesEnum.SUPER_USER.value
        )
        role_super_user = session.exec(get_roles_query).first()

        if not role_super_user:
            return AppError("Role not Found", status.HTTP_404_NOT_FOUND)

        super_user = session.exec(
            select(Users).where(getattr(Users, "email") == settings.SUPER_USER_EMAIL)
        ).first()

        if super_user:
            return

        create_user = Users(
            name="Super Admin",
            email=settings.SUPER_USER_EMAIL,
            password=hash_password(settings.SUPER_USER_PASSWORD),
            verified=True,
        )

        create_super_user_scope = UserScope(
            user_id=create_user.id,
            role_code=RolesEnum.SUPER_USER.value,
            scope_type=UserScopeEnum.SYSTEM.value,
        )

        session.add(create_user)
        session.add(create_super_user_scope)

        session.commit()
