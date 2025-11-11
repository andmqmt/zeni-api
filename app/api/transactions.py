from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.config import get_db
from app.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    DailyBalanceResponse,
    SuggestCategoryRequest,
    SuggestCategoryResponse,
)
from app.services import TransactionService
from app.repositories import TransactionRepository, CategoryRepository
from app.infrastructure.database import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    repository = TransactionRepository(db)
    category_repo = CategoryRepository(db)
    return TransactionService(repository, category_repo)


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    try:
        return service.create_transaction(transaction, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"detail": str(e), "code": "TRANSACTION_CREATE_ERROR"})


@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    on_date: date | None = Query(None, description="Filtrar por data exata (YYYY-MM-DD)"),
    category_id: int | None = Query(None, ge=1, description="Filtrar por categoria (id)"),
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    return service.list_transactions(
        current_user, skip=skip, limit=limit, on_date=on_date, category_id=category_id
    )


@router.post("/suggest-category", response_model=SuggestCategoryResponse)
def suggest_category_endpoint(
    payload: SuggestCategoryRequest,
):
    # Stateless suggestion; does not require auth nor create categories
    from app.services.auto_categorizer import suggest_category_explain
    result = suggest_category_explain(payload.description)
    if not result:
        return {"category": None, "matched_keyword": None}
    return result


@router.get("/balance/daily", response_model=List[DailyBalanceResponse])
def get_daily_balance(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    return service.calculate_daily_balance(year, month, current_user)


@router.get("/daily-balance", response_model=List[DailyBalanceResponse])
def get_daily_balance_alias(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """Alias para compatibilidade: /transactions/daily-balance

    Retorna o saldo diário do mês (um objeto por dia), cumulativo.
    """
    return service.calculate_daily_balance(year, month, current_user)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    try:
        return service.get_transaction(transaction_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": str(e), "code": "TRANSACTION_NOT_FOUND"})


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    try:
        return service.update_transaction(transaction_id, transaction, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": str(e), "code": "TRANSACTION_NOT_FOUND"})


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    try:
        service.delete_transaction(transaction_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": str(e), "code": "TRANSACTION_NOT_FOUND"})
