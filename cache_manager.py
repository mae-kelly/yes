#!/usr/bin/env python3

import os
import pickle
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    ttl_hours: int = 24
    
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(hours=self.ttl_hours)

class CacheManager:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._memory_cache = {}
        self._max_memory_entries = 10000
    
    def _get_cache_path(self, key: str) -> Path:
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if not entry.is_expired():
                    return entry.data
                else:
                    del self._memory_cache[key]
            
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                try:
                    with open(cache_path, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if not entry.is_expired():
                        if len(self._memory_cache) < self._max_memory_entries:
                            self._memory_cache[key] = entry
                        return entry.data
                    else:
                        cache_path.unlink()
                except Exception:
                    if cache_path.exists():
                        cache_path.unlink()
            
            return None
    
    def set(self, key: str, value: Any, ttl_hours: int = 24):
        entry = CacheEntry(value, datetime.now(), ttl_hours)
        
        with self._lock:
            if len(self._memory_cache) < self._max_memory_entries:
                self._memory_cache[key] = entry
        
        try:
            cache_path = self._get_cache_path(key)
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
        except Exception:
            pass
    
    def clear(self):
        with self._lock:
            self._memory_cache.clear()
        
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except Exception:
                pass