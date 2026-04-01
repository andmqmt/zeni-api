from typing import List, Dict, Optional
from datetime import date, timedelta
from decimal import Decimal

from app.repositories import TransactionRepository
from app.infrastructure.database import Transaction, TransactionType, User
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def create_transaction(self, transaction_data: TransactionCreate, user: User) -> Transaction:
        transaction = Transaction(
            user_id=user.id,
            description=transaction_data.description,
            amount=transaction_data.amount,
            type=transaction_data.type,
            transaction_date=transaction_data.transaction_date,
        )
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
    ) -> List[Transaction]:
        return self.repository.get_by_user(
            user.id, skip=skip, limit=limit, on_date=on_date
        )

    def update_transaction(self, transaction_id: int, transaction_data: TransactionUpdate, user: User) -> Transaction:
        transaction = self.repository.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transação com id {transaction_id} não encontrada")
        if transaction.user_id != user.id:
            raise ValueError("Você não tem permissão para atualizar esta transação")
        
        updates = transaction_data.model_dump(exclude_unset=True)
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
        start_date = date(year, month, 1)
        end_date = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)

        # Lightweight query: only (date, amount, type) — no ORM overhead
        rows = self.repository.get_balance_data(start_date, end_date, user.id)

        if not rows:
            return []

        # User thresholds
        bad_t = user.bad_threshold
        ok_t = user.ok_threshold
        good_t = user.good_threshold

        if (
            bad_t is not None and ok_t is not None and good_t is not None
            and not (bad_t <= ok_t <= good_t)
        ):
            bad_t = ok_t = good_t = None

        has_thresholds = bad_t is not None and ok_t is not None and good_t is not None

        # Group by date using dict
        by_date: dict[date, list] = {}
        for tx_date, amount, tx_type in rows:
            by_date.setdefault(tx_date, []).append((amount, tx_type))

        daily_balances = []
        current_balance = Decimal("0.00")
        current_date = start_date

        while current_date <= end_date:
            day_txs = by_date.get(current_date)

            if day_txs is not None:
                for amount, tx_type in day_txs:
                    if tx_type == TransactionType.INCOME:
                        current_balance += amount
                    else:
                        current_balance -= amount

                # Determine status
                if not has_thresholds:
                    status = "unconfigured"
                else:
                    bal = float(current_balance)
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

