from functools import wraps

from fastapi import Request, status
from sqlmodel import Session, select

from src.database import engine
from src.models.authentication_model import RolePermissions, RolesEnum, UserScope
from src.utils.custom_errors import AppError
from src.utils.fetcher import Fetch


def get_session(kwargs):
    for _, value in kwargs.items():
        if isinstance(value, Session):
            return value

    return None


def get_request(kwargs):
    for _, value in kwargs.items():
        if isinstance(value, Request):
            return value

    raise AppError(
        "Request object not found",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def authorize(request, session: Session, permission) -> bool:
    error_message = "You are not authorized to access this resource"
    current_user = request.session["user"]

    get_user_scopes = await Fetch(
        UserScope, "user_id", current_user["id"], session
    ).get_all_value()

    if not get_user_scopes:
        raise AppError(
            error_message,
            status.HTTP_403_FORBIDDEN,
        )

    roles = [role.role_code for role in get_user_scopes or []]

    if int(RolesEnum.SUPER_USER.value) in roles:
        return True

    for role in roles:
        query_get_permission = session.exec(
            (
                select(RolePermissions)
                .where(getattr(RolePermissions, "role") == role)
                .where(getattr(RolePermissions, "permission") == permission)
                .where(getattr(RolePermissions, "is_deleted") == False)
            )
        ).first()

        if query_get_permission:
            return True

    raise AppError(
        error_message,
        status.HTTP_403_FORBIDDEN,
    )


def authorized(permission: str):
    def __authorized(func):
        @wraps(func)
        async def ___authorisation(*args, **kwargs):
            session = get_session(kwargs)
            request: Request = get_request(kwargs)

            if session:
                authorised = await authorize(request, session, permission)
            else:
                with Session(engine) as session_ctx:
                    authorised = await authorize(request, session_ctx, permission)

            if authorised:
                return await func(*args, **kwargs)

        ___authorisation.__doc__ = f"Authorization:```{permission} ```"

        return ___authorisation

    return __authorized
