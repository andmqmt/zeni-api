"""
AI Categorization Service using Google Gemini API.

This service provides intelligent transaction categorization using AI,
with fallback to rule-based categorization when AI is unavailable.
"""

import logging
from typing import Optional
import google.generativeai as genai

from app.config import settings
from app.services.auto_categorizer import suggest_category

logger = logging.getLogger(__name__)


class AICategoryService:
    """Service for AI-powered transaction categorization."""
    
    def __init__(self):
        """Initialize AI service with configured provider."""
        self.provider = settings.ai_provider
        self.api_key = settings.ai_provider_api_key
        self.enabled = bool(self.api_key)
        
        if self.enabled and self.provider == "gemini":
            try:
                genai.configure(api_key=self.api_key)
                
                # Usar gemini-2.5-pro se disponível (Google One), fallback para flash
                # Com Google One, você pode ter acesso a modelos mais avançados
                try:
                    self.model = genai.GenerativeModel('models/gemini-2.5-pro')
                    logger.info("✅ Gemini 2.5 Pro enabled (Google One)")
                except Exception:
                    self.model = genai.GenerativeModel('models/gemini-2.5-flash')
                    logger.info("✅ Gemini 2.5 Flash enabled")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini: {e}")
                self.enabled = False
        else:
            logger.info("ℹ️ AI categorization disabled - using rule-based fallback")
    
    def categorize(self, description: str, available_categories: list[str]) -> Optional[str]:
        """
        Categorize a transaction using AI or fallback to rules.
        
        Args:
            description: Transaction description to categorize
            available_categories: List of available category names
            
        Returns:
            Category name or None if no match found
        """
        if not description or not available_categories:
            return None
        
        # Try AI categorization if enabled
        if self.enabled:
            try:
                category = self._categorize_with_ai(description, available_categories)
                if category:
                    logger.info(f"✅ AI categorized '{description[:30]}...' → '{category}'")
                    return category
            except Exception as e:
                logger.warning(f"⚠️ AI categorization failed: {e}. Falling back to rules.")
        
        # Fallback to rule-based categorization
        category = suggest_category(description)
        if category and category in available_categories:
            logger.info(f"📋 Rule-based categorized '{description[:30]}...' → '{category}'")
            return category
        
        return None
    
    def _categorize_with_ai(self, description: str, available_categories: list[str]) -> Optional[str]:
        """
        Internal method to categorize using AI provider.
        
        Args:
            description: Transaction description
            available_categories: Available category names
            
        Returns:
            Category name or None
        """
        if self.provider != "gemini":
            return None
        
        # Build category list with better formatting
        categories_text = "\n".join([f"- {cat}" for cat in available_categories])
        
        # Very simple prompt to avoid blocks - use JSON format
        categories_list = ', '.join(available_categories)
        prompt = f"Choose the best category for: '{description}'\nCategories: {categories_list}\nRespond with just the category name."

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=15,
                )
            )
            
            # Check if response was blocked
            if not response.candidates or not response.candidates[0].content.parts:
                logger.warning(f"⚠️ AI response blocked (finish_reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'})")
                return None
            
            category = response.text.strip()
            
            # Clean up response
            category = category.strip('"\'.,;: ')
            
            # Validate category exists
            if category in available_categories:
                return category
            
            # Try case-insensitive match
            category_lower = category.lower()
            for available_cat in available_categories:
                if available_cat.lower() == category_lower:
                    return available_cat
            
            logger.warning(f"⚠️ AI returned invalid category: '{category}'")
            return None
            
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            raise


# Singleton instance
_ai_service: Optional[AICategoryService] = None


def get_ai_category_service() -> AICategoryService:
    """Get or create singleton AI category service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AICategoryService()
    return _ai_service
