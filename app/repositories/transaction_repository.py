from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.infrastructure.database import Transaction, TransactionType


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        on_date: Optional[date] = None,
    ) -> List[Transaction]:
        q = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        if on_date is not None:
            q = q.filter(Transaction.transaction_date == on_date)
        return (
            q.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, transaction_id: int, updates: dict) -> Optional[Transaction]:
        transaction = self.get_by_id(transaction_id)
        if not transaction:
            return None
        
        for key, value in updates.items():
            if hasattr(transaction, key) and value is not None:
                setattr(transaction, key, value)
        
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def delete(self, transaction_id: int) -> bool:
        transaction = self.get_by_id(transaction_id)
        if not transaction:
            return False
        
        self.db.delete(transaction)
        self.db.commit()
        return True

    def get_by_date_range_and_user(self, start_date: date, end_date: date, user_id: int) -> List[Transaction]:
        """Full ORM objects — used when complete transaction data is needed."""
        return self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        ).order_by(Transaction.transaction_date.asc()).all()

    def get_balance_data(self, start_date: date, end_date: date, user_id: int):
        """Lightweight projection — only loads columns needed for daily balance.
        Returns list of (transaction_date, amount, type) tuples.
        ~60% less data transfer from PostgreSQL vs full ORM load."""
        return (
            self.db.query(
                Transaction.transaction_date,
                Transaction.amount,
                Transaction.type,
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .order_by(Transaction.transaction_date.asc())
            .all()
        )
