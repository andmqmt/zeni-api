from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.database.database import Base


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint('user_id', 'category_id', 'year', 'month', name='uq_budget_user_category_month'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    notify_threshold = Column(Float, nullable=False, default=0.8, comment="Percentual para alerta, ex.: 0.8 = 80%")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="budgets")
    category = relationship("Category")

    def __repr__(self):
        return f"<Budget(id={self.id}, category_id={self.category_id}, {self.month}/{self.year}, amount={self.amount})>"