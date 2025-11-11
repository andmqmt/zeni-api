from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.repositories import UserRepository
from app.infrastructure.database import User
from app.schemas import UserRegister, Token, TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                return None
            return TokenData(user_id=int(user_id))
        except (JWTError, ValueError):
            return None

    def register_user(self, user_data: UserRegister) -> User:
        if user_data.access_code != settings.access_code:
            raise ValueError("Código de acesso inválido")

        if self.user_repository.get_by_email(user_data.email):
            raise ValueError("E-mail já cadastrado")

        if self.user_repository.get_by_phone(user_data.phone):
            raise ValueError("Telefone já cadastrado")

        hashed_password = self.get_password_hash(user_data.password)

        user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            hashed_password=hashed_password
        )

        return self.user_repository.create(user)

    def authenticate_user(self, identifier: str, password: str) -> Optional[User]:
        user = self.user_repository.get_by_email_or_phone(identifier)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def login(self, identifier: str, password: str) -> Token:
        user = self.authenticate_user(identifier, password)
        if not user:
            # Mensagem padronizada para o frontend
            raise ValueError("Credenciais inválidas")

        access_token = self.create_access_token(data={"sub": str(user.id)})
        return Token(access_token=access_token, token_type="bearer")

    def get_current_user(self, token: str) -> User:
        token_data = self.decode_token(token)
        if token_data is None or token_data.user_id is None:
            raise ValueError("Não autenticado")

        user = self.user_repository.get_by_id(token_data.user_id)
        if user is None:
            raise ValueError("Não autenticado")
        
        if not user.is_active:
            raise ValueError("Não autenticado")

        return user
