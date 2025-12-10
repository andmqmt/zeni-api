from fastapi import APIRouter
from .transactions import router as transactions_router
from .auth import router as auth_router
from .user import router as user_router
from .insights import router as insights_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(transactions_router)
api_router.include_router(user_router)
api_router.include_router(insights_router)
