from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import get_db
from app.schemas import (
    UserProfile,
    UserProfileUpdate,
    UserPreferences,
    UserPreferencesUpdate,
    UserPreferencesInit
)
from app.services import UserService
from app.repositories import UserRepository
from app.infrastructure.database import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_repository = UserRepository(db)
    return UserService(user_repository)


@router.get("/profile", response_model=UserProfile, summary="Obter perfil do usuário")
def get_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Retorna o perfil completo do usuário autenticado, incluindo suas preferências.
    """
    return user_service.get_profile(current_user.id)


@router.put(
    "/profile",
    response_model=UserProfile,
    summary="Atualizar perfil do usuário"
)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Atualiza informações do perfil do usuário autenticado.
    
    Campos atualizáveis:
    - first_name: Nome
    - last_name: Sobrenome
    - phone: Telefone (deve ser único)
    """
    return user_service.update_profile(current_user.id, profile_data)


@router.get(
    "/preferences",
    response_model=UserPreferences,
    summary="Obter preferências de faixa de valores"
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Retorna as preferências de faixa de valores do usuário para colorização no front-end.
    
    - **bad_threshold**: Valor abaixo indica cenário ruim (vermelho)
    - **ok_threshold**: Valor até este limite indica cenário ok (amarelo)
    - **good_threshold**: Valor acima indica cenário bom (verde)
    """
    return user_service.get_preferences(current_user.id)


@router.put(
    "/preferences",
    response_model=UserPreferences,
    summary="Atualizar preferências de faixa de valores"
)
def update_preferences(
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Atualiza as preferências de faixa de valores do usuário.

    Regras:
    - Se as preferências ainda não foram configuradas (primeira vez), este endpoint retorna 400.
      Use o endpoint `POST /user/preferences/init` para a primeira configuração (todos os valores obrigatórios).
    - Para ajustes posteriores, este endpoint permite atualização parcial, validando a ordem apenas
      quando os pares comparáveis estiverem presentes.

    Observação sobre ordem crescente: bad_threshold <= ok_threshold <= good_threshold.
    """
    return user_service.update_preferences(current_user.id, preferences)


@router.post(
    "/preferences/init",
    response_model=UserPreferences,
    summary="Primeira configuração de preferências do usuário",
    status_code=status.HTTP_201_CREATED
)
def init_preferences(
    preferences: UserPreferencesInit,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Define pela primeira vez as preferências de faixa de valores do usuário.
    
    **Todos os campos são obrigatórios e não podem ser null:**
    - bad_threshold: Valor inteiro >= 0 (cenário ruim - vermelho)
    - ok_threshold: Valor inteiro >= 0 (cenário ok - amarelo)
    - good_threshold: Valor inteiro >= 0 (cenário bom - verde)
    
    **Regras de validação:**
    - Valores devem estar em ordem crescente: bad_threshold <= ok_threshold <= good_threshold
    - Nenhum campo pode ser null
    
    **Exemplo de requisição válida:**
    ```json
    {
        "bad_threshold": 0,
        "ok_threshold": 500,
        "good_threshold": 1000
    }
    ```
    
    **Exemplo de erro (422) se enviar null:**
    ```json
    {
        "detail": [
            {
                "loc": ["body", "bad_threshold"],
                "msg": "O campo 'bad_threshold' é obrigatório e não pode ser null. Por favor, forneça um valor numérico válido (>= 0).",
                "type": "value_error"
            }
        ]
    }
    ```
    """
    return user_service.init_preferences(current_user.id, preferences)
