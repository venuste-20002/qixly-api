from datetime import datetime, timedelta, timezone

import jwt
from fastapi import status
from fastapi.openapi.models import HTTPBearer

from src.config import settings
from src.utils.custom_errors import AppError
from src.utils.logger import logger

authenticationScheme = HTTPBearer()


def create_access_token(data: dict):
    to_encode = data.copy()
    expires_delta = timedelta(minutes=float(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def decode_access_token(token: str):
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )
        return decoded_token
    except Exception as e:
        logger.error(f"JWT Error {e}")
        raise AppError(f"JWT ERROR: {str(e)}", status.HTTP_400_BAD_REQUEST)
