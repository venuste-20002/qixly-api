from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel

from src.config import settings
import pyotp
from pyotp import TOTP
from src.utils.custom_errors import AppError
from src.controllers.authentication_controller import (
    AuthenticationController,
    AuthenticationControllerInput,
)
from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from sqlmodel import select
from src.models.authentication_model import Users
from src.controllers.reset_password_controller import ResetPasswordController
from src.controllers.trusted_controller import (
    decrypt_data,
    encrypt_data,
    generate_keys,
    get_public_key,
)
from src.database import database
from src.helpers import state
from src.helpers.access_token import create_access_token, decode_access_token
from src.helpers.google_auth import google_callback
from src.helpers.mailer import Mailer
from src.middlewares.auth import auth
from src.schemas.authentication_schema import (
    LoginResponseSchema,
    LoginSchema,
    ResetPasswordRequestSchema,
    ResetPasswordSchema,
    SignupResponseSchema,
    SignupSchema,
    VerificationSchema
)
from src.schemas.common_schema import CommonResponseSchema
from src.helpers.sms_send import send_sms 
import logging

router = APIRouter(prefix="/auth", tags=["Authentication"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#  router of signup

@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=CommonResponseSchema[SignupResponseSchema],
)
async def signup(
    input_data: SignupSchema,
    db: database,
    background: BackgroundTasks,
):
    register = AuthenticationController(
        database=db,
        input_data=AuthenticationControllerInput(
            **input_data.model_dump(exclude_unset=True)
        ),
    )
    signup_response = await register.signup_controller()

    secret = pyotp.random_base32()

    user_query = db.exec(select(Users).where(Users.phone == input_data.phone))
    user = user_query.first()

    if user:
        user.secret = secret  
        db.add(user)
        db.commit()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User  not found after signup"
        )

    totp = pyotp.TOTP(secret, interval=120)
    token = totp.now() 
    if input_data.email:
        message = f"""
        Hello,

        Your Verification Code: {token}
        """
        background.add_task(
            Mailer(input_data.email).mailer_config,
            message=message,
            subject="Email Verification"
        )

    sms_text = f"Welcome to our platform! Your verification code is: {token}"
    sms_response = await send_sms(
        to=input_data.phone, 
        text=sms_text
    )

    logger.info(f"SMS sent to {input_data.phone}: {sms_response}")
    return signup_response


#  router of verify the token

@router.post("/verify-token/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[dict]
)
async def verify_token(
    user_id: UUID,
    input_data : VerificationSchema,
    db:database  
):
    user_query = db.exec(select(Users).where(Users.id == user_id))
    user = user_query.first()

    if user is None:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User  not found"
        )

    if user.secret is None:
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User  does not have a secret set"
        )

    secret = user.secret
    totp = TOTP(secret, interval=120)

    if not totp.verify(input_data.token):
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    user.verified = True
    db.add(user)
    db.commit() 

    return CommonResponseSchema(
        status="success",
        message="Email verification successful",
        data={"verified": True}
    )

# router of resend the token on the email

@router.post("/resend-token/{email}",
status_code=status.HTTP_200_OK,response_model=CommonResponseSchema[dict])

async def resend_token(email: str,db: database,background: BackgroundTasks):

    user_query =db.exec(select(Users).where(Users.email == email))
    user = user_query.first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User  not found"
        )

    if user.secret is None:
        user.secret = pyotp.random_base32()  
        db.add(user)
        db.commit() 

    totp = pyotp.TOTP(user.secret, interval=120)
    token = totp.now() 

    message = f"""
    Hello {user.email},

    Your new Verification Code: {token}
    """
    background.add_task(
        Mailer(user.email).mailer_config,
        message=message,
        subject="Email Verification"
    )

    return CommonResponseSchema(
        status="success",
        message="Verification token has been resent",
        data={"token": token}  
    )


# login router 

@router.post(
    "/signin",
    response_model=CommonResponseSchema[LoginResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def login(
    input_data: LoginSchema, db: database
) -> CommonResponseSchema[LoginResponseSchema]:

    authenticate_user = AuthenticationController(
        database=db,
        input_data=AuthenticationControllerInput(
            **input_data.model_dump(exclude_unset=True)
        ),
    )
    return await authenticate_user.login_controller()


@router.get("/google", status_code=200)
async def login_google(_: Request):
    # Redirect to google auth page
    redirect_uri = f"{settings.GOOGLE_REDIRECT_URI}"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": str(redirect_uri),
        "access_type": "offline",
    }

    auth_url = (
        f"{state.fastAPI.google_config['authorization_endpoint']}?{urlencode(params)}"
    )

    return RedirectResponse(auth_url)


@router.get(
    "/google/callback",
    status_code=200,
)
async def login_google_callback_(request: Request, db: database):
    code = request.query_params.get("code")

    redirect_uri = f"{settings.GOOGLE_REDIRECT_URI}"
    token_url = state.fastAPI.google_config["token_endpoint"]
    user_info = await google_callback(code, token_url, redirect_uri)

    controller = AuthenticationController(
        database=db,
        input_data=AuthenticationControllerInput(
            **user_info,
            google_id=user_info["id"],
        ),
    )

    return await controller.google_controller()

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
)
async def reset_password_create_token(
    input_data: ResetPasswordRequestSchema,
    background: BackgroundTasks,
    db: database,
):
    reset_current_password = AuthenticationController(
        database=db, input_data=AuthenticationControllerInput(email=input_data.email)
    )
    link, token = await reset_current_password.reset_password_initialize()
    background.add_task(Mailer(input_data.email).reset_password, link)
    return CommonResponseSchema(
        message="Reset password link sent to your email", data={"token": token}
    )


@router.post(
    "/reset-password/{token}",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
)
async def reset_password(
    db: database, input_data: ResetPasswordSchema, token: str
) -> CommonResponseSchema:
    payload = await decode_access_token(token)

    reset_password_controller = ResetPasswordController(
        payload.get("email"), input_data.old_password, input_data.new_password, db
    )
    result = await reset_password_controller()

    return CommonResponseSchema(message=result, data={})


class Trusted(SQLModel):
    name: str


class TrustedResponse(SQLModel):
    name: str
    public_key: str
    is_active: bool


@router.post(
    "/trusted",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth)],
    response_model=CommonResponseSchema[TrustedResponse],
)
async def create_trusted_service(_: Request, input_data: Trusted, db: database):
    keys = generate_keys(input_data.name, db)
    return CommonResponseSchema(
        message=f"Keys generated successfully for {input_data.name}",
        data=TrustedResponse(**keys.model_dump()),
    )


@router.get(
    "/trusted/signin",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema[LoginResponseSchema],
)
async def get_trusted(_: Request, db: database, key: str):
    """
    Signin from a trusted service
    """
    decrypt = decrypt_data(key, db)
    return CommonResponseSchema(
        message="User Logged in successfully",
        data=LoginResponseSchema(access_token=decrypt),
    )


class TrustedEncryptData(SQLModel):
    request_id: str
    username: str
    phone: str


@router.post("/trusted/encrypt", status_code=status.HTTP_200_OK)
async def encrypt_data_(
    _: Request,
    db: database,
    name: str,
    input_data: TrustedEncryptData,
):
    encrypt = encrypt_data(
        input_data,
        name,
        db,
    )
    return CommonResponseSchema(
        message="Data encrypted successfully",
        data=encrypt,
    )


@router.get(
    "/trusted",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    dependencies=[Depends(auth)],
)
async def trusted(_: Request, name: str, db: database):
    """
    Get public key for trusted service
    """
    keys = get_public_key(name, db)
    return CommonResponseSchema(
        message=f"Public key for {name}",
        data=keys,
    )
