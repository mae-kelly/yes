import pickle
import gzip
import threading
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
import psutil

@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    ttl_hours: int
    access_count: int = 0
    last_accessed: datetime = None
    size_bytes: int = 0
    priority: float = 0.0
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
    
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(hours=self.ttl_hours)
    
    def update_access(self):
        self.access_count += 1
        self.last_accessed = datetime.now()
        self.priority = self._calculate_priority()
    
    def _calculate_priority(self) -> float:
        recency = 1.0 / max(1, (datetime.now() - self.last_accessed).total_seconds() / 3600)
        frequency = min(10.0, self.access_count)
        size_penalty = max(0.1, 1.0 - (self.size_bytes / (1024 * 1024)))
        return recency * frequency * size_penalty

class MemoryManager:
    def __init__(self, max_memory_bytes: int):
        self.max_memory = max_memory_bytes
        self.pressure_levels = {'low': 0.7, 'medium': 0.85, 'high': 0.95}
    
    def get_pressure_level(self, current_usage: int) -> str:
        ratio = current_usage / self.max_memory
        
        if ratio >= self.pressure_levels['high']:
            return 'high'
        elif ratio >= self.pressure_levels['medium']:
            return 'medium'
        elif ratio >= self.pressure_levels['low']:
            return 'low'
        return 'none'
    
    def suggest_evictions(self, entries: Dict[str, CacheEntry], current_usage: int) -> List[str]:
        pressure = self.get_pressure_level(current_usage)
        
        if pressure == 'none':
            return []
        
        candidates = []
        for key, entry in entries.items():
            if pressure == 'high' or entry.is_expired():
                candidates.append((key, entry.priority))
            elif pressure == 'medium' and entry.access_count < 2:
                candidates.append((key, entry.priority))
            elif pressure == 'low' and entry.is_expired():
                candidates.append((key, entry.priority))
        
        candidates.sort(key=lambda x: x[1])
        
        eviction_targets = {
            'low': len(candidates) // 4,
            'medium': len(candidates) // 3,
            'high': len(candidates) // 2
        }
        
        target_count = eviction_targets.get(pressure, 0)
        return [key for key, _ in candidates[:target_count]]

class IntelligentCache:
    def __init__(self, cache_dir: str = ".cache", max_memory_mb: int = 512, max_disk_gb: int = 5):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.disk_index: Dict[str, str] = {}
        
        self.max_memory = max_memory_mb * 1024 * 1024
        self.max_disk = max_disk_gb * 1024 * 1024 * 1024
        self.current_memory = 0
        
        self.lock = threading.RLock()
        self.memory_manager = MemoryManager(self.max_memory)
        
        self.stats = {
            'hits': 0, 'misses': 0, 'evictions': 0,
            'disk_reads': 0, 'disk_writes': 0
        }
        
        self._load_disk_index()
    
    def get(self, key: str, default: Any = None) -> Any:
        with self.lock:
            cache_key = self._hash_key(key)
            
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not entry.is_expired():
                    entry.update_access()
                    self.stats['hits'] += 1
                    return entry.data
                else:
                    self._evict_memory(cache_key)
            
            if cache_key in self.disk_index:
                entry = self._load_disk(cache_key)
                if entry and not entry.is_expired():
                    entry.update_access()
                    self._promote_to_memory(cache_key, entry)
                    self.stats['hits'] += 1
                    self.stats['disk_reads'] += 1
                    return entry.data
                else:
                    self._remove_disk(cache_key)
            
            self.stats['misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl_hours: int = 24) -> bool:
        with self.lock:
            cache_key = self._hash_key(key)
            
            try:
                data = pickle.dumps(value)
                size_bytes = len(data)
                
                entry = CacheEntry(
                    data=value,
                    timestamp=datetime.now(),
                    ttl_hours=ttl_hours,
                    size_bytes=size_bytes
                )
                
                if self._can_fit_memory(size_bytes):
                    self._store_memory(cache_key, entry)
                else:
                    self._store_disk(cache_key, entry)
                    self.stats['disk_writes'] += 1
                
                return True
            except Exception:
                return False
    
    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _can_fit_memory(self, size_bytes: int) -> bool:
        return (self.current_memory + size_bytes) <= self.max_memory
    
    def _store_memory(self, cache_key: str, entry: CacheEntry):
        if cache_key in self.memory_cache:
            self.current_memory -= self.memory_cache[cache_key].size_bytes
        
        self.memory_cache[cache_key] = entry
        self.current_memory += entry.size_bytes
        
        self._maybe_evict_memory()
    
    def _store_disk(self, cache_key: str, entry: CacheEntry):
        cache_path = self.cache_dir / f"{cache_key}.cache"
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
            
            self.disk_index[cache_key] = str(cache_path)
            self._save_disk_index()
        except Exception:
            pass
    
    def _load_disk(self, cache_key: str) -> Optional[CacheEntry]:
        if cache_key not in self.disk_index:
            return None
        
        cache_path = Path(self.disk_index[cache_key])
        if not cache_path.exists():
            del self.disk_index[cache_key]
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            try:
                cache_path.unlink()
            except:
                pass
            
            if cache_key in self.disk_index:
                del self.disk_index[cache_key]
            return None
    
    def _promote_to_memory(self, cache_key: str, entry: CacheEntry):
        if self._can_fit_memory(entry.size_bytes):
            self._store_memory(cache_key, entry)
    
    def _evict_memory(self, cache_key: str):
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            self.current_memory -= entry.size_bytes
            del self.memory_cache[cache_key]
            self.stats['evictions'] += 1
    
    def _remove_disk(self, cache_key: str):
        if cache_key in self.disk_index:
            cache_path = Path(self.disk_index[cache_key])
            try:
                if cache_path.exists():
                    cache_path.unlink()
            except:
                pass
            
            del self.disk_index[cache_key]
            self._save_disk_index()
    
    def _maybe_evict_memory(self):
        evictions = self.memory_manager.suggest_evictions(self.memory_cache, self.current_memory)
        
        for cache_key in evictions:
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not entry.is_expired():
                    self._store_disk(cache_key, entry)
                self._evict_memory(cache_key)
    
    def _load_disk_index(self):
        index_path = self.cache_dir / "index.json"
        if index_path.exists():
            try:
                with open(index_path, 'r') as f:
                    self.disk_index = json.load(f)
            except:
                self.disk_index = {}
    
    def _save_disk_index(self):
        index_path = self.cache_dir / "index.json"
        try:
            with open(index_path, 'w') as f:
                json.dump(self.disk_index, f)
        except:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            
            return {
                'memory_entries': len(self.memory_cache),
                'disk_entries': len(self.disk_index),
                'memory_usage_mb': self.current_memory / (1024 * 1024),
                'hit_rate_percent': hit_rate * 100,
                'stats': self.stats.copy()
            }
    
    def clear(self):
        with self.lock:
            self.memory_cache.clear()
            self.current_memory = 0
            
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except:
                    pass
            
            self.disk_index.clear()
            self._save_disk_index()