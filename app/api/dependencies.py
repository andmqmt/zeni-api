from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_db
from app.services import AuthService
from app.repositories import UserRepository
from app.infrastructure.database import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repository = UserRepository(db)
    return AuthService(user_repository)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service)
) -> User:
    try:
        return service.get_current_user(token)
    except ValueError as e:
        # Padroniza resposta para o frontend
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Not authenticated", "code": "NOT_AUTHENTICATED"},
            headers={"WWW-Authenticate": "Bearer"},
        )
