from decimal import Decimal
from typing import List

from app.repositories import BudgetRepository, TransactionRepository
from app.schemas import BudgetCreate, BudgetResponse
from app.infrastructure.database import User, TransactionType


class BudgetService:
    def __init__(self, budget_repo: BudgetRepository, txn_repo: TransactionRepository):
        self.budget_repo = budget_repo
        self.txn_repo = txn_repo

    def upsert_budget(self, user: User, data: BudgetCreate) -> BudgetResponse:
        budget = self.budget_repo.upsert(
            user_id=user.id,
            category_id=data.category_id,
            year=data.year,
            month=data.month,
            amount=data.amount,
            notify_threshold=data.notify_threshold,
        )
        return self._to_response_with_status(user, budget)

    def list_budgets(self, user: User, year: int, month: int, alerts_only: bool = False) -> List[BudgetResponse]:
        budgets = self.budget_repo.list_by_user_and_month(user.id, year, month)
        responses = [self._to_response_with_status(user, b) for b in budgets]
        if alerts_only:
            responses = [r for r in responses if r.status in ("warning", "exceeded")]
        return responses

    def _to_response_with_status(self, user: User, budget) -> BudgetResponse:
        # Sum expenses for that category/month
        start_year = budget.year
        start_month = budget.month
        # Use repository to fetch transactions
        from datetime import date, timedelta
        start_date = date(start_year, start_month, 1)
        if start_month == 12:
            end_date = date(start_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(start_year, start_month + 1, 1) - timedelta(days=1)

        txns = self.txn_repo.get_by_date_range_and_user(start_date, end_date, user.id)
        spent = Decimal("0.00")
        for t in txns:
            if t.type == TransactionType.EXPENSE and t.category_id == budget.category_id:
                spent += t.amount

        amount = Decimal(budget.amount)
        remaining = amount - spent
        percent = float(spent / amount) if amount > 0 else 0.0
        status = "ok"
        if percent >= 1.0:
            status = "exceeded"
        elif percent >= budget.notify_threshold:
            status = "warning"
        
        # Build category payload (include basic meta expected by frontend)
        from app.schemas.budget import CategoryInBudget
        category_obj = None
        if hasattr(budget, 'category') and budget.category is not None:
            category = budget.category
            category_obj = CategoryInBudget(
                id=category.id,
                name=category.name,
                user_id=category.user_id,
                created_at=category.created_at,
            )

        return BudgetResponse(
            id=budget.id,
            user_id=budget.user_id,
            category_id=budget.category_id,
            category=category_obj,
            year=budget.year,
            month=budget.month,
            amount=float(amount),
            notify_threshold=float(budget.notify_threshold),
            spent=float(spent),
            remaining=float(remaining),
            percent=percent,
            status=status,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
        )
