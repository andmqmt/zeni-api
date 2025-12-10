from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.config import get_db
from app.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    DailyBalanceResponse,
)
from app.schemas.smart_transaction import SmartTransactionRequest, SmartTransactionResponse
from app.services import TransactionService
from app.services.smart_transaction_parser import get_smart_parser
from app.repositories import TransactionRepository
from app.infrastructure.database import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    repository = TransactionRepository(db)
    return TransactionService(repository)


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
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    return service.list_transactions(
        current_user, skip=skip, limit=limit, on_date=on_date
    )


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


@router.post("/smart-parse", response_model=SmartTransactionResponse)
def parse_smart_transaction(
    request: SmartTransactionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Parse natural language command into transaction data using AI.
    
    Examples:
    - "gastei 50 reais no uber hoje"
    - "recebi salario de 3500"
    - "comprei no mercado 120 reais ontem"
    - "netflix 45.90 assinatura"
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📥 Smart parse request from user {current_user.id}: '{request.command}'")
    
    try:
        parser = get_smart_parser()
        logger.info(f"Parser enabled: {parser.enabled}, provider: {parser.provider}")
        
        result = parser.parse_command(request.command)
        
        if not result:
            logger.warning(f"⚠️ Failed to parse command: '{request.command}'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "detail": "Não foi possível processar o comando. Tente ser mais específico.",
                    "code": "PARSE_FAILED"
                }
            )
        
        logger.info(f"✅ Successfully parsed command for user {current_user.id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in smart parse: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Erro interno ao processar comando.",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/smart-parse-image", response_model=SmartTransactionResponse)
async def parse_image_transaction(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Parse transaction data from an image (receipt, note, etc) using AI.
    Supports: JPG, PNG, WEBP
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📸 Image parse request from user {current_user.id}, filename: {image.filename}")
    
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": "Arquivo deve ser uma imagem válida (JPG, PNG, WEBP).",
                "code": "INVALID_FILE_TYPE"
            }
        )
    
    try:
        parser = get_smart_parser()
        
        if not parser.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "detail": "Serviço de AI não está disponível no momento.",
                    "code": "AI_SERVICE_UNAVAILABLE"
                }
            )
        
        image_bytes = await image.read()
        result = parser.parse_image(image_bytes, image.content_type)
        
        if not result:
            logger.warning(f"⚠️ Failed to parse image from user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "detail": "Não foi possível identificar dados da imagem. Tente uma foto mais clara.",
                    "code": "PARSE_FAILED"
                }
            )
        
        logger.info(f"✅ Successfully parsed image for user {current_user.id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in image parse: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Erro interno ao processar imagem.",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/smart-parse-audio", response_model=SmartTransactionResponse)
async def parse_audio_transaction(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Parse transaction data from an audio file using AI (transcription + parsing).
    Supports: MP3, WAV, M4A, OGG
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🎤 Audio parse request from user {current_user.id}, filename: {audio.filename}")
    
    if not audio.content_type or not audio.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": "Arquivo deve ser um áudio válido (MP3, WAV, M4A, OGG).",
                "code": "INVALID_FILE_TYPE"
            }
        )
    
    try:
        parser = get_smart_parser()
        
        if not parser.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "detail": "Serviço de AI não está disponível no momento.",
                    "code": "AI_SERVICE_UNAVAILABLE"
                }
            )
        
        audio_bytes = await audio.read()
        result = parser.parse_audio(audio_bytes, audio.content_type)
        
        if not result:
            logger.warning(f"⚠️ Failed to parse audio from user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "detail": "Não foi possível entender o áudio. Tente gravar novamente com clareza.",
                    "code": "PARSE_FAILED"
                }
            )
        
        logger.info(f"✅ Successfully parsed audio for user {current_user.id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in audio parse: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Erro interno ao processar áudio.",
                "code": "INTERNAL_ERROR"
            }
        )

