from fastapi import APIRouter
from .endpoints import auth

api_router = APIRouter()

# Include auth router
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# TODO: Add other routers as they are implemented
# from .endpoints import users, webhooks
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
