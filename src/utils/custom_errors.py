from typing import Generic, TypeVar
import traceback
from fastapi import HTTPException, status

from src.utils.logger import logger

T = TypeVar("T")


class ErrorBase(HTTPException, Generic[T]):
    def __init__(
        self,
        detail: T,
        status_code: int,
    ) -> None:
        super().__init__(
            status_code, detail, headers={"Content-Type": "application/json"}
        )


class AuthorisationError(ErrorBase, Generic[T]):
    def __init__(
        self, detail: T, status_code: int = status.HTTP_401_UNAUTHORIZED
    ) -> None:
        super().__init__(detail, status_code)
        logger.error(f"Authorization ERROR:{detail}")


class AppError(ErrorBase, Generic[T]):
    def __init__(
        self, detail: T, status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> None:
        super().__init__(detail=f"{detail} {traceback.format_exc()} ", status_code=status_code)
        logger.error(f"API ERROR:{detail}")
