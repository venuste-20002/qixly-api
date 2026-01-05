import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from src.config import settings
from src.database import engine
from src.models.authentication_model import Users
from src.utils.custom_errors import AuthorisationError
from src.utils.fetcher import Fetcher
from src.utils.logger import logger

BearerToken = HTTPBearer()


async def auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(BearerToken),
):
    request.session.clear()
    token = credentials.credentials

    try:
        users_data = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if not users_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No payload Found",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        logger.error(f"JWT Error {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT ERROR: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with Session(engine) as session:
        user = Fetcher(
            database=session,
            table=(Users,),
            where=(Users.id == users_data.get("id"),),
        ).get_one()

        if not user.is_active:
            raise AuthorisationError(
                "Your account is not active, please contact the admin",
                status.HTTP_401_UNAUTHORIZED,
            )

        request.session["user"] = users_data
        yield user
