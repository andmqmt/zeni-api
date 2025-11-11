"""
Smart Transaction Parser Service using Google Gemini AI.

Parses natural language commands into structured transaction data.
"""

import logging
import re
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
import google.generativeai as genai

from app.config import settings
from app.schemas.smart_transaction import SmartTransactionResponse

logger = logging.getLogger(__name__)


class SmartTransactionParser:
    """Service to parse natural language transaction commands using AI."""
    
    def __init__(self):
        """Initialize AI parser with configured provider."""
        self.provider = settings.ai_provider
        self.api_key = settings.ai_provider_api_key
        self.enabled = bool(self.api_key)
        
        if self.enabled and self.provider == "gemini":
            try:
                genai.configure(api_key=self.api_key)
                try:
                    self.model = genai.GenerativeModel('models/gemini-2.5-pro')
                    logger.info("✅ Gemini 2.5 Pro enabled for smart transactions")
                except Exception:
                    self.model = genai.GenerativeModel('models/gemini-2.5-flash')
                    logger.info("✅ Gemini 2.5 Flash enabled for smart transactions")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini: {e}")
                self.enabled = False
        else:
            logger.info("ℹ️ AI parser disabled")
    
    def parse_command(self, command: str) -> Optional[SmartTransactionResponse]:
        """
        Parse natural language command into transaction data.
        
        Args:
            command: Natural language command (e.g., "gastei 50 reais no uber hoje")
            
        Returns:
            SmartTransactionResponse or None if parsing fails
        """
        if not self.enabled or not command.strip():
            return None
        
        try:
            return self._parse_with_ai(command)
        except Exception as e:
            logger.error(f"❌ AI parsing failed: {e}")
            return None
    
    def _parse_with_ai(self, command: str) -> Optional[SmartTransactionResponse]:
        """Internal method to parse using AI provider."""
        if self.provider != "gemini":
            return None
        
        today = date.today()
        prompt = f"""Parse this transaction command into structured data.

Command: "{command}"

Today's date: {today.isoformat()}

Extract:
1. description: Brief description (max 50 chars)
2. amount: Numeric value (positive number)
3. type: "income" or "expense"
4. transaction_date: Date in YYYY-MM-DD format
   - "hoje" or "today" = {today.isoformat()}
   - "ontem" or "yesterday" = {(today.replace(day=today.day-1) if today.day > 1 else today).isoformat()}
   - If no date mentioned, use today
5. category_name: Best matching category (optional)
   - Common categories: Transporte, Alimentacao, Supermercado, Delivery, Salario, Assinaturas, Compras, Energia, Agua, Internet, Combustivel, Farmacia, Academia, Restaurante
6. confidence: Your confidence in this parsing (0-1)

Respond ONLY with valid JSON (no markdown, no explanation):
{{"description": "...", "amount": 0.0, "type": "expense", "transaction_date": "YYYY-MM-DD", "category_name": "...", "confidence": 0.0}}"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=200,
                )
            )
            
            # Check if response was blocked
            if not response.candidates or not response.candidates[0].content.parts:
                logger.warning(f"⚠️ AI response blocked for command: {command[:50]}")
                return None
            
            # Extract JSON from response
            json_text = response.text.strip()
            
            # Remove markdown code blocks if present
            json_text = re.sub(r'^```json\s*', '', json_text)
            json_text = re.sub(r'\s*```$', '', json_text)
            json_text = json_text.strip()
            
            # Parse JSON
            import json
            data = json.loads(json_text)
            
            # Validate and create response
            result = SmartTransactionResponse(
                description=str(data.get('description', ''))[:255],
                amount=Decimal(str(data.get('amount', 0))),
                type=data.get('type', 'expense'),
                transaction_date=datetime.strptime(data.get('transaction_date', today.isoformat()), '%Y-%m-%d').date(),
                category_name=data.get('category_name'),
                confidence=float(data.get('confidence', 0.5))
            )
            
            logger.info(f"✅ Parsed command: '{command[:30]}...' → {result.description} ({result.amount})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to parse command '{command[:30]}...': {e}")
            return None


# Singleton instance
_parser: Optional[SmartTransactionParser] = None


def get_smart_parser() -> SmartTransactionParser:
    """Get or create singleton parser instance."""
    global _parser
    if _parser is None:
        _parser = SmartTransactionParser()
    return _parser
