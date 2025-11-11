from typing import List, Optional
from sqlalchemy.orm import Session

from app.infrastructure.database import Category, Transaction


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, name: str, is_auto_generated: bool = False) -> Category:
        category = Category(user_id=user_id, name=name, is_auto_generated=is_auto_generated)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_by_user(self, user_id: int, origin: str | None = None) -> List[Category]:
        q = self.db.query(Category).filter(Category.user_id == user_id)
        if origin == 'auto':
            q = q.filter(Category.is_auto_generated == True)  # noqa: E712
        elif origin == 'manual':
            q = q.filter(Category.is_auto_generated == False)  # noqa: E712
        return q.order_by(Category.name.asc()).all()

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_by_name(self, user_id: int, name: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.user_id == user_id, Category.name == name).first()

    def rename(self, category: Category, new_name: str) -> Category:
        category.name = new_name
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        # Ensure no transactions linked
        used = self.db.query(Transaction).filter(Transaction.category_id == category.id).first()
        if used:
            raise ValueError("Categoria em uso por transações; remova ou recategorize-as antes de excluir.")
        self.db.delete(category)
        self.db.commit()
