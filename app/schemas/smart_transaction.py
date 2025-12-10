from pydantic import BaseModel, Field
from typing import Optional, Literal
from decimal import Decimal
from datetime import date


class SmartTransactionRequest(BaseModel):
    """Request to parse a natural language transaction command."""
    command: str = Field(..., min_length=1, max_length=500, description="Natural language command")


class SmartTransactionResponse(BaseModel):
    description: str
    amount: Decimal
    type: Literal["income", "expense"]
    transaction_date: date
    confidence: float = Field(..., ge=0, le=1, description="Confidence score of the parsing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Uber para casa",
                "amount": 25.50,
                "type": "expense",
                "transaction_date": "2025-11-11",
                "confidence": 0.95
            }
        }
