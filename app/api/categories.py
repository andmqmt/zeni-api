from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.config import get_db
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services import CategoryService
from app.repositories import CategoryRepository
from app.api.dependencies import get_current_user
from app.infrastructure.database import User

router = APIRouter(prefix="/categories", tags=["categories"])


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    repo = CategoryRepository(db)
    return CategoryService(repo)


@router.get("/", response_model=list[CategoryResponse])
def list_categories(
    origin: str | None = Query(None, pattern="^(auto|manual)$", description="Filtrar origem da categoria"),
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    return service.list_categories(current_user, origin=origin)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    return service.create_category(current_user, data)


@router.put("/{category_id}", response_model=CategoryResponse)
def rename_category(
    category_id: int,
    data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    return service.rename_category(current_user, category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    service.delete_category(current_user, category_id)
    return None
