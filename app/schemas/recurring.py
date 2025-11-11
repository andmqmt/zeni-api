from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal

from app.infrastructure.database.transaction import TransactionType


class Frequency(str):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RecurringCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0)
    type: TransactionType

    frequency: str = Field(..., pattern="^(daily|weekly|monthly)$")
    interval: int = Field(1, ge=1)
    start_date: date
    end_date: Optional[date] = None
    weekday: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)

    category_id: Optional[int] = None


class RecurringResponse(BaseModel):
    id: int
    description: str
    amount: float
    type: TransactionType
    frequency: str
    interval: int
    start_date: date
    end_date: Optional[date]
    weekday: Optional[int]
    day_of_month: Optional[int]
    category_id: Optional[int]
    next_run_date: date

    class Config:
        from_attributes = True


class MaterializeRequest(BaseModel):
    up_to_date: date
