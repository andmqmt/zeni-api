from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.database.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_category_user_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_auto_generated = Column(Boolean, nullable=False, server_default='false', default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="categories")
    transactions = relationship("Transaction", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"