from fastapi import APIRouter
from .transactions import router as transactions_router
from .auth import router as auth_router
from .user import router as user_router
from .categories import router as categories_router
from .recurring import router as recurring_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(transactions_router)
api_router.include_router(user_router)
api_router.include_router(categories_router)
api_router.include_router(recurring_router)
