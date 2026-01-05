import httpx
from fastapi import FastAPI, status

from src.config import settings
from src.utils.custom_errors import AuthorisationError

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

fast: FastAPI


async def fetch_google_public_keys():
    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_JWKS_URL)
        jwks = resp.json()

    public_keys = {}
    for key in jwks["keys"]:
        kid = key["kid"]
        fkey = {"kty": "RSA", "e": key["e"], "n": key["n"]}
        public_keys[kid] = fkey
    return public_keys


async def initialize_google_client(app):
    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_DISCOVERY_URL)
        json_data = resp.json()
        app.google_config = json_data
        await update_google_public_keys(app)


async def update_google_public_keys(app):
    app.google_public_keys = await fetch_google_public_keys()


async def google_callback(code, token_url, redirect_uri):
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": str(redirect_uri),
                },
            )
        token_data = token_response.json()
        id_token = token_data.get("id_token")
        access_token = token_data.get("access_token")

        if not id_token or not access_token:
            raise AuthorisationError(
                "No ID token or access token found in response",
                status.HTTP_400_BAD_REQUEST,
            )

        async with httpx.AsyncClient() as client:
            user_info = await client.get(
                f"{GOOGLE_USERINFO_URL}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        return user_info.json()
    except Exception as e:
        raise AuthorisationError(e)
