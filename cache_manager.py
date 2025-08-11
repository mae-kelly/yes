#!/usr/bin/env python3

import os
import pickle
import hashlib
import threading
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, asdict
import psutil

@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    ttl_hours: int
    access_count: int = 0
    last_accessed: datetime = None
    size_bytes: int = 0
    content_hash: str = ""
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
    
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(hours=self.ttl_hours)
    
    def is_stale(self, staleness_hours: int = 1) -> bool:
        return datetime.now() > self.last_accessed + timedelta(hours=staleness_hours)
    
    def update_access(self):
        self.access_count += 1
        self.last_accessed = datetime.now()

class IntelligentCacheManager:
    def __init__(self, cache_dir: str = ".cache", max_memory_mb: int = 512, max_disk_gb: int = 5):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._disk_index: Dict[str, str] = {}
        
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_disk_bytes = max_disk_gb * 1024 * 1024 * 1024
        self.current_memory_usage = 0
        
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'disk_reads': 0,
            'disk_writes': 0
        }
        
        self._load_disk_index()
        self._cleanup_expired_entries()
    
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            cache_key = self._generate_cache_key(key)
            
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if not entry.is_expired():
                    entry.update_access()
                    self._stats['hits'] += 1
                    return entry.data
                else:
                    self._evict_from_memory(cache_key)
            
            if cache_key in self._disk_index:
                entry = self._load_from_disk(cache_key)
                if entry and not entry.is_expired():
                    entry.update_access()
                    self._promote_to_memory(cache_key, entry)
                    self._stats['hits'] += 1
                    self._stats['disk_reads'] += 1
                    return entry.data
                else:
                    self._remove_from_disk(cache_key)
            
            self._stats['misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl_hours: int = 24, force_disk: bool = False) -> bool:
        with self._lock:
            cache_key = self._generate_cache_key(key)
            
            try:
                serialized_data = pickle.dumps(value)
                size_bytes = len(serialized_data)
                content_hash = hashlib.md5(serialized_data).hexdigest()
                
                entry = CacheEntry(
                    data=value,
                    timestamp=datetime.now(),
                    ttl_hours=ttl_hours,
                    size_bytes=size_bytes,
                    content_hash=content_hash
                )
                
                if not force_disk and self._can_fit_in_memory(size_bytes):
                    self._store_in_memory(cache_key, entry)
                else:
                    self._store_on_disk(cache_key, entry)
                    self._stats['disk_writes'] += 1
                
                return True
                
            except Exception as e:
                return False
    
    def invalidate(self, key: str) -> bool:
        with self._lock:
            cache_key = self._generate_cache_key(key)
            removed = False
            
            if cache_key in self._memory_cache:
                self._evict_from_memory(cache_key)
                removed = True
            
            if cache_key in self._disk_index:
                self._remove_from_disk(cache_key)
                removed = True
            
            return removed
    
    def invalidate_pattern(self, pattern: str) -> int:
        with self._lock:
            removed_count = 0
            
            keys_to_remove = []
            for key in self._memory_cache.keys():
                if pattern in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._evict_from_memory(key)
                removed_count += 1
            
            keys_to_remove = []
            for key in self._disk_index.keys():
                if pattern in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._remove_from_disk(key)
                removed_count += 1
            
            return removed_count
    
    def clear(self) -> None:
        with self._lock:
            self._memory_cache.clear()
            self.current_memory_usage = 0
            
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass
            
            for cache_file in self.cache_dir.glob("*.cache.gz"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass
            
            self._disk_index.clear()
            self._save_disk_index()
    
    def optimize(self) -> Dict[str, int]:
        with self._lock:
            optimization_stats = {
                'memory_evictions': 0,
                'disk_evictions': 0,
                'promoted_to_memory': 0,
                'compressed_files': 0
            }
            
            self._cleanup_expired_entries()
            
            if self._is_memory_pressure():
                evicted = self._evict_least_used_memory()
                optimization_stats['memory_evictions'] = evicted
            
            if self._is_disk_pressure():
                evicted = self._evict_least_used_disk()
                optimization_stats['disk_evictions'] = evicted
            
            promoted = self._promote_hot_entries()
            optimization_stats['promoted_to_memory'] = promoted
            
            compressed = self._compress_old_files()
            optimization_stats['compressed_files'] = compressed
            
            return optimization_stats
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            memory_usage_mb = self.current_memory_usage / (1024 * 1024)
            disk_usage_mb = self._calculate_disk_usage() / (1024 * 1024)
            
            hit_rate = self._stats['hits'] / (self._stats['hits'] + self._stats['misses']) if (self._stats['hits'] + self._stats['misses']) > 0 else 0
            
            return {
                'memory_entries': len(self._memory_cache),
                'disk_entries': len(self._disk_index),
                'memory_usage_mb': round(memory_usage_mb, 2),
                'disk_usage_mb': round(disk_usage_mb, 2),
                'hit_rate': round(hit_rate * 100, 2),
                'stats': self._stats.copy()
            }
    
    def _generate_cache_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _can_fit_in_memory(self, size_bytes: int) -> bool:
        return (self.current_memory_usage + size_bytes) <= self.max_memory_bytes
    
    def _is_memory_pressure(self) -> bool:
        system_memory = psutil.virtual_memory()
        return (system_memory.percent > 85 or 
                self.current_memory_usage > (self.max_memory_bytes * 0.9))
    
    def _is_disk_pressure(self) -> bool:
        disk_usage = self._calculate_disk_usage()
        return disk_usage > (self.max_disk_bytes * 0.9)
    
    def _store_in_memory(self, cache_key: str, entry: CacheEntry) -> None:
        if cache_key in self._memory_cache:
            self.current_memory_usage -= self._memory_cache[cache_key].size_bytes
        
        self._memory_cache[cache_key] = entry
        self.current_memory_usage += entry.size_bytes
        
        if not self._can_fit_in_memory(0):
            self._evict_least_used_memory()
    
    def _store_on_disk(self, cache_key: str, entry: CacheEntry) -> None:
        cache_path = self.cache_dir / f"{cache_key}.cache"
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
            
            self._disk_index[cache_key] = str(cache_path)
            self._save_disk_index()
            
        except Exception:
            pass
    
    def _load_from_disk(self, cache_key: str) -> Optional[CacheEntry]:
        if cache_key not in self._disk_index:
            return None
        
        cache_path = Path(self._disk_index[cache_key])
        
        if not cache_path.exists():
            del self._disk_index[cache_key]
            return None
        
        try:
            if cache_path.suffix == '.gz':
                with gzip.open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
            else:
                with open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
            
            return entry
            
        except Exception:
            try:
                cache_path.unlink()
            except Exception:
                pass
            
            if cache_key in self._disk_index:
                del self._disk_index[cache_key]
            
            return None
    
    def _promote_to_memory(self, cache_key: str, entry: CacheEntry) -> None:
        if self._can_fit_in_memory(entry.size_bytes):
            self._store_in_memory(cache_key, entry)
    
    def _evict_from_memory(self, cache_key: str) -> None:
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            self.current_memory_usage -= entry.size_bytes
            del self._memory_cache[cache_key]
            self._stats['evictions'] += 1
    
    def _remove_from_disk(self, cache_key: str) -> None:
        if cache_key in self._disk_index:
            cache_path = Path(self._disk_index[cache_key])
            try:
                if cache_path.exists():
                    cache_path.unlink()
            except Exception:
                pass
            
            del self._disk_index[cache_key]
            self._save_disk_index()
    
    def _evict_least_used_memory(self) -> int:
        if not self._memory_cache:
            return 0
        
        entries_by_usage = sorted(
            self._memory_cache.items(),
            key=lambda x: (x[1].access_count, x[1].last_accessed)
        )
        
        evicted_count = 0
        target_usage = self.max_memory_bytes * 0.7
        
        for cache_key, entry in entries_by_usage:
            if self.current_memory_usage <= target_usage:
                break
            
            if not entry.is_stale(staleness_hours=0.5):
                self._store_on_disk(cache_key, entry)
            
            self._evict_from_memory(cache_key)
            evicted_count += 1
        
        return evicted_count
    
    def _evict_least_used_disk(self) -> int:
        if not self._disk_index:
            return 0
        
        disk_entries = []
        for cache_key, cache_path in self._disk_index.items():
            path_obj = Path(cache_path)
            if path_obj.exists():
                try:
                    stat = path_obj.stat()
                    disk_entries.append((cache_key, stat.st_atime, stat.st_size))
                except Exception:
                    continue
        
        disk_entries.sort(key=lambda x: x[1])
        
        evicted_count = 0
        target_usage = self.max_disk_bytes * 0.8
        current_usage = self._calculate_disk_usage()
        
        for cache_key, _, size in disk_entries:
            if current_usage <= target_usage:
                break
            
            self._remove_from_disk(cache_key)
            current_usage -= size
            evicted_count += 1
        
        return evicted_count
    
    def _promote_hot_entries(self) -> int:
        if not self._disk_index:
            return 0
        
        promoted_count = 0
        
        for cache_key in list(self._disk_index.keys()):
            if not self._can_fit_in_memory(0):
                break
            
            entry = self._load_from_disk(cache_key)
            if entry and entry.access_count >= 3 and not entry.is_stale():
                if self._can_fit_in_memory(entry.size_bytes):
                    self._promote_to_memory(cache_key, entry)
                    self._remove_from_disk(cache_key)
                    promoted_count += 1
        
        return promoted_count
    
    def _compress_old_files(self) -> int:
        compressed_count = 0
        
        for cache_key, cache_path in list(self._disk_index.items()):
            path_obj = Path(cache_path)
            
            if not path_obj.exists() or path_obj.suffix == '.gz':
                continue
            
            try:
                stat = path_obj.stat()
                age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600
                
                if age_hours > 6:
                    compressed_path = path_obj.with_suffix('.cache.gz')
                    
                    with open(path_obj, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            f_out.write(f_in.read())
                    
                    path_obj.unlink()
                    self._disk_index[cache_key] = str(compressed_path)
                    compressed_count += 1
                    
            except Exception:
                continue
        
        if compressed_count > 0:
            self._save_disk_index()
        
        return compressed_count
    
    def _cleanup_expired_entries(self) -> None:
        expired_memory_keys = []
        for cache_key, entry in self._memory_cache.items():
            if entry.is_expired():
                expired_memory_keys.append(cache_key)
        
        for cache_key in expired_memory_keys:
            self._evict_from_memory(cache_key)
        
        expired_disk_keys = []
        for cache_key in self._disk_index.keys():
            entry = self._load_from_disk(cache_key)
            if not entry or entry.is_expired():
                expired_disk_keys.append(cache_key)
        
        for cache_key in expired_disk_keys:
            self._remove_from_disk(cache_key)
    
    def _calculate_disk_usage(self) -> int:
        total_size = 0
        for cache_path in self._disk_index.values():
            path_obj = Path(cache_path)
            if path_obj.exists():
                try:
                    total_size += path_obj.stat().st_size
                except Exception:
                    pass
        return total_size
    
    def _load_disk_index(self) -> None:
        index_path = self.cache_dir / "disk_index.json"
        if index_path.exists():
            try:
                with open(index_path, 'r') as f:
                    self._disk_index = json.load(f)
            except Exception:
                self._disk_index = {}
    
    def _save_disk_index(self) -> None:
        index_path = self.cache_dir / "disk_index.json"
        try:
            with open(index_path, 'w') as f:
                json.dump(self._disk_index, f, indent=2)
        except Exception:
            pass