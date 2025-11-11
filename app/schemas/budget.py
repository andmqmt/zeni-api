from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class BudgetCreate(BaseModel):
    category_id: int
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    amount: Decimal = Field(..., gt=0)
    notify_threshold: float = Field(0.8, ge=0.0, le=1.0)


class CategoryInBudget(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class BudgetResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    category: CategoryInBudget
    year: int
    month: int
    amount: float
    notify_threshold: float

    # Computed
    spent: float
    remaining: float
    percent: float
    status: str  # ok | warning | exceeded

    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
