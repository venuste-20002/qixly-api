from typing import Optional
from sqlmodel import select,Session

from fastapi import status
from sqlmodel import Session, SQLModel

from src.config import settings
from src.helpers.access_token import create_access_token
from src.models.authentication_model import (
    Blacklist,
    Roles,
    RolesEnum,
    Users,
    UserScope,
    UserScopeEnum,
)
from src.schemas.authentication_schema import (
    LoginResponseSchema,
    SignupResponseSchema,
    TokenData,
)
from src.schemas.common_schema import CommonResponseSchema
from src.utils.custom_errors import AuthorisationError
from src.utils.fetcher import Fetch
from src.utils.logger import logger
from src.utils.password_encrypt import compare_password, hash_password


class AuthenticationControllerInput(SQLModel):
    username: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    google_id: Optional[str] = None
    phone: Optional[str] = None


class AuthenticationController:
    def __init__(
        self,
        database: Session,
        input_data: AuthenticationControllerInput,
    ):
        self.database = database
        self.input_data = input_data

    
    async def get_user(self):
        get_user_by_email = Fetch(Users, "email", self.input_data.email, self.database)
        user_by_email = await get_user_by_email.get_single_value()
        if user_by_email:
          return user_by_email
        get_user_by_phone = Fetch(Users, "phone", self.input_data.phone, self.database)
        user_by_phone = await get_user_by_phone.get_single_value()
        return user_by_phone

    async def get_role(self):
        query_fetch_roles = Fetch(Roles, "name", RolesEnum.BUYER.value, self.database)
        get_role_buyer = await query_fetch_roles.get_single_value_id()

        if not get_role_buyer:
            raise AuthorisationError("Role not found", status.HTTP_404_NOT_FOUND)
        return get_role_buyer

    async def save_user(self):
        if self.input_data.password:
            self.input_data.password = hash_password(self.input_data.password)

        create_new_user_buyer = Users(**self.input_data.model_dump())

        self.database.add(create_new_user_buyer)

        return create_new_user_buyer

    async def get_access_token(self, user):
        token_payload = TokenData(
            id=str(user.id),
            email=user.email,
            name=str(user.name),
            phone=user.phone,
        )
        return create_access_token(token_payload.model_dump())

    async def password_compare(self, password: str):
        check_user_password = compare_password(str(self.input_data.password), password)
        if not check_user_password:
            logger.info("Incorrect password")
            raise AuthorisationError(
                "Invalid email , phone or Password", status.HTTP_409_CONFLICT
            )
        return check_user_password

    async def signup_controller(self) -> CommonResponseSchema[SignupResponseSchema]:
        get_user = await self.get_user()
        if get_user:
            logger.info("User Exists")
            raise AuthorisationError("User already exist", status.HTTP_409_CONFLICT)

        create_new_user_buyer = await self.save_user()

        self.database.commit()
        self.database.refresh(create_new_user_buyer)

        return CommonResponseSchema(
            message="User Created Successfully. Verify your email",
            data=SignupResponseSchema(**create_new_user_buyer.model_dump()),
        )

    async def get_user_by_email(self, email: str):
        result =  self.database.exec(select(Users).where(Users.email == email))
        return result.first()

    async def get_user_by_phone(self, phone: str):
        result =  self.database.exec(select(Users).where(Users.phone == phone))
        return result.first()
    
    async def login_controller(self) -> CommonResponseSchema[LoginResponseSchema]:
     if "@" in self.input_data.username:
        get_user_data = await self.get_user_by_email(self.input_data.username)
     else:
        get_user_data = await self.get_user_by_phone(self.input_data.username)

     if not get_user_data:
        logger.info("User  Doesn't exist")
        raise AuthorisationError(
            "Invalid Username or Password", status.HTTP_404_NOT_FOUND
        )

     if not get_user_data.verified:
        logger.info("User  not verified")
        raise AuthorisationError(
            "User  not verified, Verify your email before login",
            status.HTTP_403_FORBIDDEN,
        )

     is_password_valid = await self.password_compare(get_user_data.password)
     if not is_password_valid:
        logger.info("Invalid Password")
        raise AuthorisationError(
            "Invalid Username or Password", status.HTTP_404_NOT_FOUND
        )
     get_access_token = await self.get_access_token(get_user_data)
     return CommonResponseSchema(
        message="User  Successfully Signed in",
        data=LoginResponseSchema(access_token=get_access_token),
    )

    async def google_controller(self):
        get_user = await self.get_user()

        if get_user:
            if not get_user.google_id:
                get_user.google_id = self.input_data.google_id

                self.database.add(get_user)
                self.database.commit()

            get_access_token = await self.get_access_token(get_user)

            return CommonResponseSchema(
                message="Successfully Signed In",
                data=LoginResponseSchema(access_token=get_access_token),
            )

        create_new_user = await self.save_user()
        create_new_user.verified = True

        self.database.add(create_new_user)

        # create a user scope
        create_user_scope_buyer = UserScope(
            user_id=create_new_user.id,
            role_code=RolesEnum.BUYER.value,
            scope_type=UserScopeEnum.SYSTEM.value,
        )

        self.database.add(create_user_scope_buyer)
        self.database.commit()
        self.database.refresh(create_new_user)

        get_access_token = await self.get_access_token(create_new_user)

        return CommonResponseSchema(
            message="Successfully Signed Up",
            data=LoginResponseSchema(access_token=get_access_token),
        )

    async def reset_password_initialize(self):
        get_user = await self.get_user()
        if not get_user:
            raise AuthorisationError("User not found", status.HTTP_404_NOT_FOUND)
        create_token = create_access_token({"email": self.input_data.email})
        return (
            f"{settings.BASE_URL}/api/auth/reset-password/{create_token}",
        ), create_token

    async def verify_email(self, token) -> CommonResponseSchema:
        get_token = await Fetch(
            Blacklist, "token", token, self.database
        ).get_single_value()
        if get_token:
            raise AuthorisationError("Token already used", status.HTTP_409_CONFLICT)

        get_user = await self.get_user()
        if not get_user:
            raise AuthorisationError("No user Found", status.HTTP_404_NOT_FOUND)
        get_user.verified = True

        create_user_scope_buyer = UserScope(
            user_id=get_user.id,
            role_code=RolesEnum.BUYER.value,
            scope_type=UserScopeEnum.SYSTEM.value,
        )

        self.database.add(get_user)
        self.database.add(create_user_scope_buyer)
        self.database.add(Blacklist(token=token))
        self.database.commit()

        return CommonResponseSchema(message="Email Successfully Verified", data={})
