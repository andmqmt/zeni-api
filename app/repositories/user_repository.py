from typing import Optional
from sqlalchemy.orm import Session

from app.infrastructure.database import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()

    def get_by_email_or_phone(self, identifier: str) -> Optional[User]:
        return self.db.query(User).filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()

    def update_profile(self, user: User, **kwargs) -> User:
        """Atualiza informações do perfil do usuário"""
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_preferences(
        self,
        user: User,
        bad_threshold: Optional[int] = None,
        ok_threshold: Optional[int] = None,
        good_threshold: Optional[int] = None
    ) -> User:
        """Atualiza preferências de faixa de valores do usuário"""
        if bad_threshold is not None:
            user.bad_threshold = bad_threshold
        if ok_threshold is not None:
            user.ok_threshold = ok_threshold
        if good_threshold is not None:
            user.good_threshold = good_threshold
    
        self.db.commit()
        self.db.refresh(user)
        return user
