from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import get_db
from app.schemas import UserRegister, UserResponse, Token
from app.services import AuthService
from app.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repository = UserRepository(db)
    return AuthService(user_repository)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    service: AuthService = Depends(get_auth_service)
):
    try:
        user = service.register_user(user_data)
        return user
    except ValueError as e:
        # Padroniza mensagem de erro para frontend e mapeia conflitos
        msg = str(e)
        if "E-mail" in msg and "cadastrado" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"detail": "E-mail já está em uso", "code": "EMAIL_CONFLICT"})
        if "Telefone" in msg and "cadastrado" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"detail": "Telefone já está em uso", "code": "PHONE_CONFLICT"})
        if "Código de acesso" in msg and "inválido" in msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"detail": "Código de acesso inválido", "code": "INVALID_ACCESS_CODE"})
        # Fallback
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"detail": msg, "code": "REGISTRATION_ERROR"})


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    try:
        return service.login(form_data.username, form_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": str(e), "code": "INVALID_CREDENTIALS"},
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service)
):
    try:
        user = service.get_current_user(token)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": str(e), "code": "NOT_AUTHENTICATED"},
            headers={"WWW-Authenticate": "Bearer"},
        )

