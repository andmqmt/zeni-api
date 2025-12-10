from typing import List, Dict, Optional
from datetime import date
from collections import defaultdict, Counter

from app.repositories import TransactionRepository
from app.infrastructure.database import TransactionType, User


class InsightsService:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def _analyze_spending_patterns(self, expenses: List) -> List[Dict]:
        patterns = []
        descriptions = [t.description.lower() for t in expenses]
        
        keywords = {
            'transporte': ['uber', 'taxi', '99', 'transporte', 'gasolina', 'combustivel'],
            'alimentação': ['mercado', 'supermercado', 'restaurante', 'delivery', 'ifood'],
            'assinaturas': ['netflix', 'spotify', 'disney', 'prime', 'youtube'],
            'contas': ['energia', 'agua', 'luz', 'internet', 'aluguel'],
        }
        
        for pattern_name, words in keywords.items():
            matching_transactions = [
                t for t in expenses 
                if any(word in t.description.lower() for word in words)
            ]
            if matching_transactions:
                total = sum(float(t.amount) for t in matching_transactions)
                patterns.append({
                    'name': pattern_name,
                    'amount': total,
                    'count': len(matching_transactions)
                })
        
        return sorted(patterns, key=lambda x: x['amount'], reverse=True)

    def generate_insights(self, user: User, year: int, month: int) -> Dict:
        start_date = date(year, month, 1)
        
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        from datetime import timedelta
        end_date = end_date - timedelta(days=1)
        
        transactions = self.transaction_repository.get_by_date_range_and_user(
            start_date, end_date, user.id
        )
        
        if not transactions:
            return {
                'insights': [],
                'summary': {
                    'total_income': 0,
                    'total_expenses': 0,
                    'balance': 0,
                    'savings_rate': 0,
                    'transaction_count': 0
                }
            }
        
        expenses = [t for t in transactions if t.type == TransactionType.EXPENSE]
        income = [t for t in transactions if t.type == TransactionType.INCOME]
        
        total_expenses = sum(float(t.amount) for t in expenses)
        total_income = sum(float(t.amount) for t in income)
        balance = total_income - total_expenses
        savings_rate = (balance / total_income * 100) if total_income > 0 else 0
        
        patterns = self._analyze_spending_patterns(expenses)
        insights = []
        
        for pattern in patterns[:3]:
            percentage = (pattern['amount'] / total_expenses * 100) if total_expenses > 0 else 0
            
            if percentage > 40:
                insights.append({
                    'type': 'warning',
                    'title': pattern['name'].title(),
                    'message': f'Alto gasto com {pattern["name"]} ({percentage:.0f}% do total). {pattern["count"]} transação(ões) identificadas.',
                    'amount': pattern['amount'],
                    'percentage': round(percentage, 1)
                })
            elif percentage > 25:
                insights.append({
                    'type': 'tip',
                    'title': pattern['name'].title(),
                    'message': f'{pattern["name"].title()} representa {percentage:.0f}% dos gastos. Há oportunidades de economia.',
                    'amount': pattern['amount'],
                    'percentage': round(percentage, 1)
                })
        
        if savings_rate < 10 and total_income > 0:
            insights.append({
                'type': 'warning',
                'title': 'Taxa de Economia Baixa',
                'message': f'Economizando apenas {savings_rate:.0f}% da renda. Meta recomendada: 20%.',
                'amount': balance,
                'percentage': round(savings_rate, 1)
            })
        elif savings_rate >= 20:
            insights.append({
                'type': 'success',
                'title': 'Ótima Economia',
                'message': f'Parabéns! Você está economizando {savings_rate:.0f}% da sua renda.',
                'amount': balance,
                'percentage': round(savings_rate, 1)
            })
        
        if len(expenses) >= 3:
            avg_expense = total_expenses / len(expenses)
            high_expenses = [t for t in expenses if float(t.amount) > avg_expense * 2]
            
            if high_expenses:
                insights.append({
                    'type': 'tip',
                    'title': 'Transações Atípicas',
                    'message': f'{len(high_expenses)} transação(ões) acima da média detectadas. Revise se eram necessárias.',
                    'amount': None,
                    'percentage': None
                })
        
        return {
            'insights': insights,
            'summary': {
                'total_income': round(total_income, 2),
                'total_expenses': round(total_expenses, 2),
                'balance': round(balance, 2),
                'savings_rate': round(savings_rate, 1),
                'transaction_count': len(transactions),
                'expense_count': len(expenses),
                'income_count': len(income),
                'avg_expense': round(total_expenses / len(expenses), 2) if expenses else 0,
                'patterns': [
                    {
                        'name': p['name'],
                        'amount': round(p['amount'], 2),
                        'count': p['count'],
                        'percentage': round((p['amount'] / total_expenses * 100) if total_expenses > 0 else 0, 1)
                    }
                    for p in patterns[:5]
                ]
            }
        }

