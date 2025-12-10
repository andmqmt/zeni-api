from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import get_db
from app.schemas.insights import InsightsAnalysisResponse
from app.services.insights_service import InsightsService
from app.repositories import TransactionRepository
from app.infrastructure.database import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/insights", tags=["insights"])


def get_insights_service(db: Session = Depends(get_db)) -> InsightsService:
    transaction_repository = TransactionRepository(db)
    return InsightsService(transaction_repository)


@router.get("/analysis", response_model=InsightsAnalysisResponse)
def get_insights_analysis(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    service: InsightsService = Depends(get_insights_service)
):
    return service.generate_insights(current_user, year, month)

