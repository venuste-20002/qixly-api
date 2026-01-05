from contextlib import asynccontextmanager
from functools import lru_cache

import uvicorn
from fastapi import Depends, FastAPI, Request
from sqlmodel import SQLModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.config import settings
from src.database import engine
from src.helpers import free_routers, state
from src.helpers.google_auth import initialize_google_client
from src.middlewares.auth import auth
from src.middlewares.errors import get_all_errors
from src.middlewares.role_checker import authorized
from src.middlewares.scheduler import scheduler
from src.routes import (
    authentication_router,
    card_router,
    cardvariant_router,
    cart_router,
    category_router,
    claim_router,
    commission_router,
    coupon_router,
    institution_branch_router,
    institution_members_router,
    institution_router,
    permission_router,
    review_router,
    roles_router,
    sales_router,
    share_router,
    transaction_router,
    user_scope_router,
    users_router,
    wishlist_router,
)
from src.seeders.permission_seeder import (
    PermissionActivity,
    PermissionsResources,
    permission__,
)
from src.seeds import seeders_run


@asynccontextmanager
@lru_cache(maxsize=200)
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    await seeders_run()
    await initialize_google_client(app)
    state.fastAPI = app
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Qixly Card Ticket-BE",
    description="BackEnd for Ticketing platform",
    lifespan=lifespan,
    version="0.0.1",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(BaseHTTPMiddleware, dispatch=get_all_errors())


@app.get(
    "/",
    tags=["Welcome"],
    dependencies=[Depends(auth)],
)
@authorized(
    permission__(PermissionsResources.WISHLIST, PermissionActivity.WRITE),
)
async def main(request: Request):
    user_data = request.session["user"]
    return {"msg": f"Ticketing platform Card Backend {user_data['email']}"}


routes = [
    authentication_router.router,
    users_router.router,
    user_scope_router.router,
    roles_router.router,
    institution_router.router,
    institution_branch_router.router,
    institution_members_router.router,
    category_router.router,
    card_router.router,
    cardvariant_router.router,
    commission_router.router,
    coupon_router.router,
    cart_router.router,
    wishlist_router.router,
    permission_router.router,
    sales_router.router,
    share_router.router,
    claim_router.router,
    free_routers.router,
    transaction_router.router,
    review_router.router,
]

for route in routes:
    app.include_router(router=route, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        port=settings.PORT,
        reload=True,
    )
