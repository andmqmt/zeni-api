from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import date

from app.infrastructure.database import RecurringTransaction


class RecurringRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, r: RecurringTransaction) -> RecurringTransaction:
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def list_by_user(self, user_id: int) -> List[RecurringTransaction]:
        return (
            self.db.query(RecurringTransaction)
            .filter(RecurringTransaction.user_id == user_id)
            .all()
        )

    def get_by_id(self, rid: int) -> Optional[RecurringTransaction]:
        return self.db.query(RecurringTransaction).filter(RecurringTransaction.id == rid).first()

    def delete(self, r: RecurringTransaction) -> None:
        self.db.delete(r)
        self.db.commit()

    def update(self, r: RecurringTransaction) -> RecurringTransaction:
        self.db.commit()
        self.db.refresh(r)
        return r
