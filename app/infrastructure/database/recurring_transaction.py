from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.infrastructure.database.database import Base
from .transaction import TransactionType


class Frequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)

    frequency = Column(Enum(Frequency), nullable=False)
    interval = Column(Integer, nullable=False, default=1)  # e.g., every N days/weeks/months
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    weekday = Column(Integer, nullable=True)  # 0=Monday .. 6=Sunday (for weekly)
    day_of_month = Column(Integer, nullable=True)  # 1..31 (for monthly), best effort

    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)

    next_run_date = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="recurring_transactions")
    category = relationship("Category")
    transactions = relationship("Transaction", back_populates="recurring", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RecurringTransaction(id={self.id}, freq={self.frequency}, interval={self.interval})>"