from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str

    SUPER_USER_EMAIL: str
    SUPER_USER_PASSWORD: str

    ALGORITHM: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    BASE_URL: str

    MAILER_EMAIL: str
    MAILER_PASSWORD: str
    MAILER_SERVER: str
    MAILER_PORT: str
    PORT: int

    SUPER_PRIVATE_KEY: str
    PAYMENT_CALLBACK_URL: str
    MTN_API_PUSH: str = ""  # No longer used - kept for compatibility
    AIRTEL_API_PUSH: str = ""  # No longer used - kept for compatibility
    PAYPACK_CLIENT_ID: str
    PAYPACK_CLIENT_SECRET: str
    PAYPACK_BASE_URL: str 
    PAYPACK_WEBHOOK_SECRET: str

    SMS_API_KEY_PUSH:str
    SMS_API_URL:str
    SMS_API_TOKEN:str

    
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
