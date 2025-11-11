from fastapi import HTTPException, status
from typing import List

from app.repositories import CategoryRepository
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.infrastructure.database import User


class CategoryService:
    def __init__(self, repo: CategoryRepository):
        self.repo = repo

    def list_categories(self, user: User, origin: str | None = None) -> List[CategoryResponse]:
        if origin not in (None, 'auto', 'manual'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"detail": "Filtro de origem inválido", "code": "INVALID_FILTER"})
        cats = self.repo.list_by_user(user.id, origin=origin)
        return [CategoryResponse.model_validate(c) for c in cats]

    def create_category(self, user: User, data: CategoryCreate) -> CategoryResponse:
        existing = self.repo.get_by_name(user.id, data.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria já existe")
        c = self.repo.create(user.id, data.name)
        return CategoryResponse.model_validate(c)

    def rename_category(self, user: User, category_id: int, data: CategoryUpdate) -> CategoryResponse:
        c = self.repo.get_by_id(category_id)
        if not c or c.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
        # check unique name
        existing = self.repo.get_by_name(user.id, data.name)
        if existing and existing.id != category_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe categoria com este nome")
        c = self.repo.rename(c, data.name)
        return CategoryResponse.model_validate(c)

    def delete_category(self, user: User, category_id: int) -> None:
        c = self.repo.get_by_id(category_id)
        if not c or c.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
        try:
            self.repo.delete(c)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
