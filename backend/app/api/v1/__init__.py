from fastapi import APIRouter
from app.api.v1.endpoints import auth

api_router = APIRouter()

# Include the API router with its prefix
api_router.include_router(auth.api_router, prefix="/auth", tags=["auth"])

# TODO: Add other routers as they are implemented
# from .endpoints import users, webhooks
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
