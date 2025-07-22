"""
API security and rate limiting for Scherman Trading System
"""

import time
import hashlib
import hmac
import base64
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock

class RateLimiter:
    """Thread-safe rate limiter"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit"""
        with self.lock:
            now = time.time()
            
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < self.time_window
            ]
            
            # Check if under limit
            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(now)
                return True
            
            return False

class APIKeyManager:
    """Secure API key management"""
    
    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key.encode()
    
    def validate_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Validate API request signature"""
        try:
            expected = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected)
        except Exception:
            return False
    
    def generate_api_signature(self, method: str, path: str, body: str, timestamp: str, secret: str) -> str:
        """Generate API signature for requests"""
        message = timestamp + method.upper() + path + body
        signature = base64.b64encode(
            hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
        ).decode()
        return signature

