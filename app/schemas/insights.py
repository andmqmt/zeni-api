from pydantic import BaseModel
from typing import List, Optional, Literal


class InsightResponse(BaseModel):
    type: Literal["warning", "tip", "success"]
    title: str
    message: str
    amount: Optional[float] = None
    percentage: Optional[float] = None


class SpendingPattern(BaseModel):
    name: str
    amount: float
    count: int
    percentage: float


class InsightsSummary(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    savings_rate: float
    transaction_count: int
    expense_count: int
    income_count: int
    avg_expense: float
    patterns: List[SpendingPattern]


class InsightsAnalysisResponse(BaseModel):
    insights: List[InsightResponse]
    summary: InsightsSummary

