from datetime import date, timedelta
from calendar import monthrange
from decimal import Decimal
from typing import List

from fastapi import HTTPException, status

from app.repositories import RecurringRepository, TransactionRepository
from app.schemas import RecurringCreate, RecurringResponse
from app.infrastructure.database import RecurringTransaction, Transaction, TransactionType, User


class RecurringService:
    def __init__(self, repo: RecurringRepository, txn_repo: TransactionRepository):
        self.repo = repo
        self.txn_repo = txn_repo

    def list(self, user: User) -> List[RecurringResponse]:
        items = self.repo.list_by_user(user.id)
        return [RecurringResponse.model_validate(i) for i in items]

    def create(self, user: User, data: RecurringCreate) -> RecurringResponse:
        # Basic validation per frequency
        if data.frequency == "weekly" and data.weekday is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="weekday é obrigatório para frequência semanal")
        if data.frequency == "monthly" and data.day_of_month is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="day_of_month é obrigatório para frequência mensal")
        if data.end_date and data.end_date < data.start_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date deve ser >= start_date")

        next_run = data.start_date
        r = RecurringTransaction(
            user_id=user.id,
            description=data.description,
            amount=data.amount,
            type=data.type,
            frequency=data.frequency,  # stored as enum by SQLAlchemy
            interval=data.interval,
            start_date=data.start_date,
            end_date=data.end_date,
            weekday=data.weekday,
            day_of_month=data.day_of_month,
            category_id=data.category_id,
            next_run_date=next_run,
        )
        r = self.repo.create(r)
        return RecurringResponse.model_validate(r)

    def delete(self, user: User, rid: int) -> None:
        r = self.repo.get_by_id(rid)
        if not r or r.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recorrência não encontrada")
        self.repo.delete(r)

    def materialize_up_to(self, user: User, up_to: date) -> int:
        """Create transactions for all recurrences due up to the given date. Returns count created."""
        items = self.repo.list_by_user(user.id)
        created = 0
        for r in items:
            created += self._materialize_one(r, up_to)
        return created

    def _materialize_one(self, r: RecurringTransaction, up_to: date) -> int:
        count = 0
        while r.next_run_date <= up_to and (r.end_date is None or r.next_run_date <= r.end_date):
            # Create transaction for next_run_date
            t = Transaction(
                user_id=r.user_id,
                description=r.description,
                amount=r.amount,
                type=r.type,
                transaction_date=r.next_run_date,
                category_id=r.category_id,
                recurring_id=r.id,
            )
            self.txn_repo.create(t)
            count += 1

            # Advance next_run_date according to frequency and interval
            r.next_run_date = self._advance(r)
            self.repo.update(r)
        return count

    def _advance(self, r: RecurringTransaction) -> date:
        if r.frequency == "daily":
            return r.next_run_date + timedelta(days=r.interval)
        if r.frequency == "weekly":
            # Jump weeks, then align to weekday
            d = r.next_run_date + timedelta(weeks=r.interval)
            if r.weekday is not None:
                # Align to requested weekday within the week of the new date
                while d.weekday() != r.weekday:
                    d += timedelta(days=1)
            return d
        if r.frequency == "monthly":
            # Add N months
            y = r.next_run_date.year
            m = r.next_run_date.month + r.interval
            while m > 12:
                y += 1
                m -= 12
            dom = r.day_of_month or r.next_run_date.day
            last_day = monthrange(y, m)[1]
            day = min(dom, last_day)
            return date(y, m, day)
        # Fallback
        return r.next_run_date + timedelta(days=1)
