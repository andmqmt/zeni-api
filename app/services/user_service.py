from typing import Optional
from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserProfile,
    UserProfileUpdate,
    UserPreferences,
    UserPreferencesUpdate,
    UserPreferencesInit,
)
from app.infrastructure.database import User


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_profile(self, user_id: int) -> UserProfile:
        """Obtém o perfil completo do usuário"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return self._user_to_profile(user)

    def update_profile(self, user_id: int, profile_data: UserProfileUpdate) -> UserProfile:
        """Atualiza informações do perfil do usuário"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Validar se phone já está em uso por outro usuário
        if profile_data.phone:
            existing_user = self.user_repository.get_by_phone(profile_data.phone)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este telefone já está em uso"
                )

        # Atualizar apenas os campos fornecidos
        update_data = profile_data.model_dump(exclude_unset=True)
        updated_user = self.user_repository.update_profile(user, **update_data)
        
        return self._user_to_profile(updated_user)

    def get_preferences(self, user_id: int) -> UserPreferences:
        """Obtém as preferências de faixa de valores do usuário"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return UserPreferences(
            bad_threshold=user.bad_threshold,
            ok_threshold=user.ok_threshold,
            good_threshold=user.good_threshold
        )

    def update_preferences(self, user_id: int, preferences: UserPreferencesUpdate) -> UserPreferences:
        """Atualiza as preferências de faixa de valores do usuário"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Bloquear atualização parcial antes da primeira configuração
        is_configured = (
            user.bad_threshold is not None and
            user.ok_threshold is not None and
            user.good_threshold is not None
        )
        if not is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Preferências ainda não configuradas. "
                    "Use POST /user/preferences/init para a primeira configuração."
                )
            )

        # Validar ordem crescente apenas quando comparações fizerem sentido
        bad = preferences.bad_threshold if preferences.bad_threshold is not None else user.bad_threshold
        ok = preferences.ok_threshold if preferences.ok_threshold is not None else user.ok_threshold
        good = preferences.good_threshold if preferences.good_threshold is not None else user.good_threshold

        # Se ambos existirem, validar pares
        if bad is not None and ok is not None and bad > ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="bad_threshold não pode ser maior que ok_threshold"
            )
        if ok is not None and good is not None and ok > good:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ok_threshold não pode ser maior que good_threshold"
            )
        if bad is not None and good is not None and bad > good:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="bad_threshold não pode ser maior que good_threshold"
            )

        updated_user = self.user_repository.update_preferences(
            user,
            bad_threshold=preferences.bad_threshold,
            ok_threshold=preferences.ok_threshold,
            good_threshold=preferences.good_threshold
        )
        
        return UserPreferences(
            bad_threshold=updated_user.bad_threshold,
            ok_threshold=updated_user.ok_threshold,
            good_threshold=updated_user.good_threshold
        )

    def init_preferences(self, user_id: int, preferences: UserPreferencesInit) -> UserPreferences:
        """Define as preferências iniciais (todos os valores obrigatórios)."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Validação de ordem já é feita no schema, mas garantimos aqui também
        bad = preferences.bad_threshold
        ok = preferences.ok_threshold
        good = preferences.good_threshold

        if not (bad <= ok <= good):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Os valores devem estar em ordem crescente: bad_threshold <= ok_threshold <= good_threshold"
            )

        updated_user = self.user_repository.update_preferences(
            user,
            bad_threshold=bad,
            ok_threshold=ok,
            good_threshold=good
        )

        return UserPreferences(
            bad_threshold=updated_user.bad_threshold,
            ok_threshold=updated_user.ok_threshold,
            good_threshold=updated_user.good_threshold
        )

    def _user_to_profile(self, user: User) -> UserProfile:
        """Converte User para UserProfile"""
        return UserProfile(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            auto_categorize_enabled=user.auto_categorize_enabled,
            preferences=UserPreferences(
                bad_threshold=user.bad_threshold,
                ok_threshold=user.ok_threshold,
                good_threshold=user.good_threshold
            ),
            preferences_configured=(
                user.bad_threshold is not None and
                user.ok_threshold is not None and
                user.good_threshold is not None
            ),
            created_at=user.created_at,
            updated_at=user.updated_at
        )
