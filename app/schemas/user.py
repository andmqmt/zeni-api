from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional


class UserPreferences(BaseModel):
    """Preferências de faixa de valores do usuário"""
    bad_threshold: Optional[int] = Field(
        default=None,
        ge=0,
        description="Valor abaixo indica cenário ruim (vermelho)"
    )
    ok_threshold: Optional[int] = Field(
        default=None,
        ge=0,
        description="Valor até este limite indica cenário ok (amarelo)"
    )
    good_threshold: Optional[int] = Field(
        default=None,
        ge=0,
        description="Valor acima indica cenário bom (verde)"
    )


class UserPreferencesUpdate(BaseModel):
    """Schema para atualização de preferências"""
    bad_threshold: Optional[int] = Field(None, ge=0)
    ok_threshold: Optional[int] = Field(None, ge=0)
    good_threshold: Optional[int] = Field(None, ge=0)


class UserProfile(BaseModel):
    """Perfil completo do usuário"""
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    is_active: bool
    auto_categorize_enabled: bool
    preferences: UserPreferences
    preferences_configured: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema para atualização de perfil"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    auto_categorize_enabled: Optional[bool] = None


class UserPreferencesInit(BaseModel):
    """Schema para primeira configuração de preferências (todos os campos são obrigatórios)"""
    bad_threshold: int = Field(..., ge=0, description="Valor abaixo indica cenário ruim (vermelho)")
    ok_threshold: int = Field(..., ge=0, description="Valor até este limite indica cenário ok (amarelo)")
    good_threshold: int = Field(..., ge=0, description="Valor acima indica cenário bom (verde)")
    
    @field_validator('bad_threshold', 'ok_threshold', 'good_threshold', mode='before')
    @classmethod
    def validate_not_null(cls, v, info):
        if v is None:
            field_name = info.field_name
            raise ValueError(
                f"O campo '{field_name}' é obrigatório e não pode ser null. "
                f"Por favor, forneça um valor numérico válido (>= 0)."
            )
        return v
    
    @field_validator('good_threshold')
    @classmethod
    def validate_thresholds_order(cls, v, info):
        """Valida que os valores estão em ordem crescente"""
        data = info.data
        bad = data.get('bad_threshold')
        ok = data.get('ok_threshold')
        
        if bad is not None and ok is not None and v is not None:
            if not (bad <= ok <= v):
                raise ValueError(
                    f"Os valores devem estar em ordem crescente: "
                    f"bad_threshold ({bad}) <= ok_threshold ({ok}) <= good_threshold ({v})"
                )
        return v
