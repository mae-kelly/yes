"""
Security-first input validation for Scherman Trading System
"""

import re
import logging
from typing import Any, Dict, Optional
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when input validation fails"""
    pass

class InputValidator:
    """Comprehensive input validation for trading system"""
    
    @staticmethod
    def validate_api_key(api_key: str, min_length: int = 20) -> bool:
        """Validate API key format and length"""
        if not isinstance(api_key, str):
            raise ValidationError("API key must be a string")
        
        if len(api_key) < min_length:
            raise ValidationError(f"API key must be at least {min_length} characters")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            raise ValidationError("API key contains invalid characters")
        
        return True
    
    @staticmethod
    def validate_risk_percentage(risk_pct: float) -> bool:
        """Validate risk percentage is within safe bounds"""
        if not isinstance(risk_pct, (int, float)):
            raise ValidationError("Risk percentage must be numeric")
        
        if risk_pct < 0:
            raise ValidationError("Risk percentage cannot be negative")
        
        if risk_pct > 0.05:  # 5% maximum
            raise ValidationError("Risk percentage too high (max 5%)")
        
        return True
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate trading symbol format"""
        if not isinstance(symbol, str):
            raise ValidationError("Symbol must be a string")
        
        # Standard crypto symbol format
        if not re.match(r'^[A-Z]{2,5}-[A-Z]{2,5}(-SWAP)?$', symbol):
            raise ValidationError("Invalid symbol format")
        
        return True
    
    @staticmethod
    def validate_decimal_amount(amount: Any, min_value: float = 0) -> Decimal:
        """Validate and convert amount to Decimal for precision"""
        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError("Invalid amount format")
        
        if decimal_amount < Decimal(str(min_value)):
            raise ValidationError(f"Amount must be >= {min_value}")
        
        return decimal_amount
    
    @staticmethod
    def sanitize_string_input(input_str: str, max_length: int = 255) -> str:
        """Sanitize string input to prevent injection attacks"""
        if not isinstance(input_str, str):
            raise ValidationError("Input must be a string")
        
        # Remove potential injection characters
        sanitized = re.sub(r'[<>"\';\\]', '', input_str)
        
        if len(sanitized) > max_length:
            raise ValidationError(f"Input too long (max {max_length} characters)")
        
        return sanitized.strip()

