from typing import List, Dict, Optional
from datetime import date, timedelta
from decimal import Decimal

from app.repositories import TransactionRepository, CategoryRepository
from app.infrastructure.database import Transaction, TransactionType, User
from .auto_categorizer import suggest_category
from .ai_category_service import get_ai_category_service
from app.config import settings
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    def __init__(self, repository: TransactionRepository, category_repo: CategoryRepository | None = None):
        self.repository = repository
        self.category_repo = category_repo
        self.ai_service = get_ai_category_service()

    def _auto_categorize(self, description: str, user: User) -> Optional[int]:
        """
        Auto-categorize a transaction using AI or rules.
        Returns category_id if found, None otherwise.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 Auto-categorizing: '{description}' for user {user.id}")
        
        if not self.category_repo:
            logger.warning("❌ No category_repo available")
            return None
            
        if not settings.auto_categorize_enabled:
            logger.warning("❌ Auto-categorize disabled in settings")
            return None
        
        if not getattr(user, "auto_categorize_enabled", True):
            logger.warning(f"❌ Auto-categorize disabled for user {user.id}")
            return None
        
        # Get all user categories for AI context
        user_categories = self.category_repo.list_by_user(user.id)
        category_names = [cat.name for cat in user_categories]
        
        logger.info(f"📋 Available categories: {category_names}")
        
        # Try AI categorization first, with fallback to rules built-in
        category_name = self.ai_service.categorize(description, category_names)
        
        if category_name:
            logger.info(f"✅ AI/Rules suggested: '{category_name}'")
            # Find or create the category
            existing = self.category_repo.get_by_name(user.id, category_name)
            if not existing:
                logger.info(f"📝 Creating new category: '{category_name}'")
                existing = self.category_repo.create(user.id, category_name, is_auto_generated=True)
            return existing.id
        
        logger.warning(f"⚠️ No category found for: '{description}'")
        return None

    def create_transaction(self, transaction_data: TransactionCreate, user: User) -> Transaction:
        transaction = Transaction(
            user_id=user.id,
            description=transaction_data.description,
            amount=transaction_data.amount,
            type=transaction_data.type,
            transaction_date=transaction_data.transaction_date,
            category_id=transaction_data.category_id,
        )
        
        # Auto-categorize if no category was provided
        if transaction.category_id is None:
            category_id = self._auto_categorize(transaction.description, user)
            if category_id:
                transaction.category_id = category_id
        
        return self.repository.create(transaction)

    def get_transaction(self, transaction_id: int, user: User) -> Transaction:
        transaction = self.repository.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transação com id {transaction_id} não encontrada")
        if transaction.user_id != user.id:
            raise ValueError("Você não tem permissão para acessar esta transação")
        return transaction

    def list_transactions(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
        on_date: Optional[date] = None,
        category_id: Optional[int] = None,
    ) -> List[Transaction]:
        return self.repository.get_by_user(
            user.id, skip=skip, limit=limit, on_date=on_date, category_id=category_id
        )

    def update_transaction(self, transaction_id: int, transaction_data: TransactionUpdate, user: User) -> Transaction:
        transaction = self.repository.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transação com id {transaction_id} não encontrada")
        if transaction.user_id != user.id:
            raise ValueError("Você não tem permissão para atualizar esta transação")
        
        updates = transaction_data.model_dump(exclude_unset=True)
        
        # Only auto-categorize if user didn't set a category AND the transaction currently has no category
        if (
            'category_id' not in updates
            and 'description' in updates
            and getattr(transaction, 'category_id', None) is None
        ):
            category_id = self._auto_categorize(updates['description'], user)
            if category_id:
                updates['category_id'] = category_id
        
        transaction = self.repository.update(transaction_id, updates)
        return transaction

    def delete_transaction(self, transaction_id: int, user: User) -> bool:
        transaction = self.repository.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transação com id {transaction_id} não encontrada")
        if transaction.user_id != user.id:
            raise ValueError("Você não tem permissão para deletar esta transação")
        
        return self.repository.delete(transaction_id)

    def calculate_daily_balance(self, year: int, month: int, user: User) -> List[Dict]:
        try:
            start_date = date(year, month, 1)
            
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            transactions = self.repository.get_by_date_range_and_user(start_date, end_date, user.id)
            
            daily_balances = []
            current_balance = Decimal("0.00")
            
            transactions_by_date = {}
            for transaction in transactions:
                if transaction.transaction_date not in transactions_by_date:
                    transactions_by_date[transaction.transaction_date] = []
                transactions_by_date[transaction.transaction_date].append(transaction)
            
            current_date = start_date
            # Capturar preferências do usuário
            bad_t = user.bad_threshold
            ok_t = user.ok_threshold
            good_t = user.good_threshold

            # Regra de negócio garante thresholds crescentes no momento da configuração.
            # Se houver qualquer inconsistência (ex: manipulação direta no banco), marcamos como 'unconfigured'.
            if (
                bad_t is not None and ok_t is not None and good_t is not None and
                not (bad_t <= ok_t <= good_t)
            ):
                bad_t = ok_t = good_t = None  # Força status 'unconfigured'

            while current_date <= end_date:
                if current_date in transactions_by_date:
                    for transaction in transactions_by_date[current_date]:
                        if transaction.type == TransactionType.INCOME:
                            current_balance += transaction.amount
                        else:
                            current_balance -= transaction.amount

                # Determinar status com base nas preferências (FORA do if)
                status = None
                if bad_t is None or ok_t is None or good_t is None:
                    status = "unconfigured"
                else:
                    bal = float(current_balance)
                    # Lógica: valor <= threshold indica nível
                    # Exemplo: bad=3000, ok=5000, good=8000
                    # - balance <= 3000 => red (ruim)
                    # - balance <= 5000 => yellow (médio)
                    # - balance <= 8000 => green (bom)
                    # - balance > 8000 => green (também bom)
                    if bal <= bad_t:
                        status = "red"
                    elif bal <= ok_t:
                        status = "yellow"
                    else:
                        status = "green"

                daily_balances.append({
                    "date": current_date.isoformat(),
                    "balance": float(current_balance),
                    "status": status,
                })
                
                current_date += timedelta(days=1)
            
            return daily_balances
        except Exception as e:
            # Log temporário para debug
            import traceback
            print(f"ERROR in calculate_daily_balance: {e}")
            print(traceback.format_exc())
            raise
