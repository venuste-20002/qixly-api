import re
from typing import Optional
from uuid import UUID
from src.utils.fetcher import Fetch
from src.models.authentication_model import (Users)
from src.database import database

from fastapi import status
from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel

from src.utils.custom_errors import AppError


class CommonAutheticationSchema(SQLModel):
    email: Optional[EmailStr] = Field(..., description="Email of the user")
    name: str = Field(..., description="Name of the user")
    phone: str = Field(...,description="Phone of the user")
    id: UUID = Field(..., description="Id of the user", sa_column_kwargs={"primary"} )


class SignupSchema(SQLModel):
    email: Optional[EmailStr] = Field(default=None, description="Email of the user (optional)")
    name: str = Field(..., description="Name of the user")
    password: str = Field(..., description="Password of the user")
    phone: str = Field(..., description="Phone number of the user", max_length=15)

    @field_validator("password")
    def validate_password_strength(cls, v):
        if not re.match(
            r"^(?=.*[a-zA-Z])(?=.*\d)[A-Za-z\d!@#$&]{6,15}$",
            v,
        ):
            raise AppError(
                detail="Password should have more than 6-15 characters, a capital letter, and a symbol",
                status_code=status.HTTP_412_PRECONDITION_FAILED,
            )
        return v

class VerificationSchema(SQLModel):
    token:str = Field(..., description="The token recieve on the email")

class SignupResponseSchema(CommonAutheticationSchema):
    pass

class VerifyTokenSchema(SQLModel):
    email : Optional[str]
    token :str

class LoginSchema(SQLModel):
    username: str = Field(..., description="Email or Phone of the user")
    password: str = Field(
        description="Password of the user",
    )


class LoginResponseSchema(SQLModel):
    access_token: str = Field(..., description="Access token")
    token_type: Optional[str] = Field(
        default="Bearer",
        description="Token type",
    )


class TokenData(CommonAutheticationSchema):
    id: Optional[str | UUID] = Field(..., description="Id of the user")
    phone: Optional[str] = Field(..., description="Phone number of the user")


class ResetPasswordRequestSchema(SQLModel):
    email: EmailStr = Field(..., description="Email of the user")


class ResetPasswordSchema(SQLModel):
    old_password: Optional[str] = Field(
        default=None, description="Old password of the user"
    )
    new_password: str = Field(..., description="New Password of the user")

    @field_validator("new_password")
    def validate_password_strength(cls, v):
        if not re.match(
            r"^(?=.*[a-zA-Z])(?=.*\d)[A-Za-z\d!@#$&]{6,15}$",
            v,
        ):
            raise AppError(
                detail="Password should have more than 6-15 characters, a capital letter, and a symbol",
                status_code=status.HTTP_412_PRECONDITION_FAILED,
            )
        return v
