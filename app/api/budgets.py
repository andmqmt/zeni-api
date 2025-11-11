from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config import get_db
from app.schemas import BudgetCreate, BudgetResponse
from app.services import BudgetService
from app.repositories import BudgetRepository, TransactionRepository
from app.api.dependencies import get_current_user
from app.infrastructure.database import User

router = APIRouter(prefix="/budgets", tags=["budgets"])


def get_budget_service(db: Session = Depends(get_db)) -> BudgetService:
    budget_repo = BudgetRepository(db)
    txn_repo = TransactionRepository(db)
    return BudgetService(budget_repo, txn_repo)


@router.get("/", response_model=list[BudgetResponse])
def list_budgets(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    alerts_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
):
    return service.list_budgets(current_user, year, month, alerts_only)


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def upsert_budget(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
):
    return service.upsert_budget(current_user, data)
