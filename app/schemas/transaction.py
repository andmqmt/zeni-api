from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from decimal import Decimal

from app.infrastructure.database import TransactionType


class TransactionBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    type: TransactionType
    transaction_date: date


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    type: Optional[TransactionType] = None
    transaction_date: Optional[date] = None


class TransactionResponse(TransactionBase):
    id: int

    class Config:
        from_attributes = True


class DailyBalanceResponse(BaseModel):
    date: str
    balance: float
    status: Optional[str] = Field(
        default=None,
        description=(
            "Classificação do saldo diário baseada nas preferências do usuário: "
            "'red' | 'yellow' | 'green' | 'unconfigured' (quando não definido)."
        )
    )


