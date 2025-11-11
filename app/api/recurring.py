from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from app.config import get_db
from app.api.dependencies import get_current_user
from app.infrastructure.database import User
from app.repositories import RecurringRepository, TransactionRepository
from app.services import RecurringService
from app.schemas import RecurringCreate, RecurringResponse, MaterializeRequest


router = APIRouter(prefix="/recurring", tags=["recurring"])


def get_recurring_service(db: Session = Depends(get_db)) -> RecurringService:
    repo = RecurringRepository(db)
    txn_repo = TransactionRepository(db)
    return RecurringService(repo, txn_repo)


@router.get("/", response_model=List[RecurringResponse])
def list_recurring(
    current_user: User = Depends(get_current_user),
    service: RecurringService = Depends(get_recurring_service),
):
    return service.list(current_user)


@router.post("/", response_model=RecurringResponse, status_code=status.HTTP_201_CREATED)
def create_recurring(
    payload: RecurringCreate,
    current_user: User = Depends(get_current_user),
    service: RecurringService = Depends(get_recurring_service),
):
    return service.create(current_user, payload)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring(
    recurring_id: int,
    current_user: User = Depends(get_current_user),
    service: RecurringService = Depends(get_recurring_service),
):
    service.delete(current_user, recurring_id)
    return None


@router.post("/materialize", response_model=Dict[str, int])
def materialize_recurring(
    body: MaterializeRequest,
    current_user: User = Depends(get_current_user),
    service: RecurringService = Depends(get_recurring_service),
):
    created = service.materialize_up_to(current_user, body.up_to_date)
    return {"created": created}
