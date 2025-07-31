import json
import logging
from typing import Dict, Any, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.memory_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
                self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis cache enabled")
            except Exception as e:
                logger.warning(f"Redis not available, using memory cache: {e}")
                self.redis_enabled = False
        else:
            self.redis_enabled = False
            logger.info("Redis module not available, using memory cache only")
    
    def get(self, key: str) -> Optional[Any]:
        if self.redis_enabled:
            try:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats["hits"] += 1
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        if key in self.memory_cache:
            self.cache_stats["hits"] += 1
            return self.memory_cache[key]
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        serialized = json.dumps(value, default=str)
        
        if self.redis_enabled:
            try:
                self.redis_client.setex(key, ttl, serialized)
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        
        self.memory_cache[key] = value
        
        if len(self.memory_cache) > 1000:
            keys_to_remove = list(self.memory_cache.keys())[:100]
            for k in keys_to_remove:
                del self.memory_cache[k]
    
    def get_stats(self) -> Dict[str, Any]:
        hit_rate = self.cache_stats["hits"] / (self.cache_stats["hits"] + self.cache_stats["misses"]) * 100
        return {
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": self.cache_stats["hits"] + self.cache_stats["misses"],
            "redis_enabled": self.redis_enabled
        }