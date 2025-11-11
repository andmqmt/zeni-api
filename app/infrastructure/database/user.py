from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    # Habilita/desabilita categorização automática de transações
    auto_categorize_enabled = Column(Boolean, nullable=False, default=True, server_default='true')
    
    # Preferências de faixa de valores (sem defaults; definidas por usuário)
    bad_threshold = Column(Integer, nullable=True, comment="Valor abaixo indica cenário ruim (vermelho)")
    ok_threshold = Column(Integer, nullable=True, comment="Valor até este limite indica cenário ok (amarelo)")
    good_threshold = Column(Integer, nullable=True, comment="Valor acima indica cenário bom (verde)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"
