from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.infrastructure.database import Budget


class BudgetRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(self, user_id: int, category_id: int, year: int, month: int, amount, notify_threshold: float) -> Budget:
        budget = (
            self.db.query(Budget)
            .options(joinedload(Budget.category))
            .filter(
                and_(
                    Budget.user_id == user_id,
                    Budget.category_id == category_id,
                    Budget.year == year,
                    Budget.month == month,
                )
            )
            .first()
        )
        if budget:
            budget.amount = amount
            budget.notify_threshold = notify_threshold
        else:
            budget = Budget(
                user_id=user_id,
                category_id=category_id,
                year=year,
                month=month,
                amount=amount,
                notify_threshold=notify_threshold,
            )
            self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        # Explicitly load the relationship after refresh
        self.db.refresh(budget, ['category'])
        return budget

    def list_by_user_and_month(self, user_id: int, year: int, month: int) -> List[Budget]:
        return (
            self.db.query(Budget)
            .options(joinedload(Budget.category))
            .filter(Budget.user_id == user_id, Budget.year == year, Budget.month == month)
            .all()
        )

    def delete(self, budget: Budget) -> None:
        self.db.delete(budget)
        self.db.commit()

    def get_by_id(self, budget_id: int) -> Optional[Budget]:
        return self.db.query(Budget).filter(Budget.id == budget_id).first()
