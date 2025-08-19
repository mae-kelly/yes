# cache/system.py

import pickle
import gzip
import threading
import hashlib
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Tuple
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
    compression_enabled: bool = False
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
        self.priority = self._calculate_priority()
    
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(hours=self.ttl_hours)
    
    def update_access(self):
        self.access_count += 1
        self.last_accessed = datetime.now()
        self.priority = self._calculate_priority()
    
    def _calculate_priority(self) -> float:
        now = datetime.now()
        time_since_access = (now - self.last_accessed).total_seconds() / 3600
        time_since_creation = (now - self.timestamp).total_seconds() / 3600
        
        recency_factor = 1.0 / max(1, time_since_access)
        frequency_factor = min(10.0, self.access_count)
        age_factor = 1.0 / max(1, time_since_creation / 24)
        size_penalty = max(0.1, 1.0 - (self.size_bytes / (10 * 1024 * 1024)))
        
        return (recency_factor * 0.4 + frequency_factor * 0.3 + age_factor * 0.2) * size_penalty

class MemoryManager:
    def __init__(self, max_memory_bytes: int):
        self.max_memory = max_memory_bytes
        self.pressure_levels = {
            'none': 0.0,
            'low': 0.65,
            'medium': 0.80,
            'high': 0.90,
            'critical': 0.95
        }
        
        self.eviction_strategies = {
            'none': 0,
            'low': 0.05,
            'medium': 0.15,
            'high': 0.30,
            'critical': 0.50
        }
    
    def get_pressure_level(self, current_usage: int) -> str:
        ratio = current_usage / self.max_memory
        
        for level in ['critical', 'high', 'medium', 'low']:
            if ratio >= self.pressure_levels[level]:
                return level
        
        return 'none'
    
    def get_eviction_ratio(self, pressure_level: str) -> float:
        return self.eviction_strategies.get(pressure_level, 0.0)
    
    def suggest_evictions(self, entries: Dict[str, CacheEntry], 
                         current_usage: int) -> List[str]:
        pressure = self.get_pressure_level(current_usage)
        eviction_ratio = self.get_eviction_ratio(pressure)
        
        if eviction_ratio == 0:
            return []
        
        candidates = []
        for key, entry in entries.items():
            if entry.is_expired():
                candidates.append((key, 0))
            else:
                candidates.append((key, entry.priority))
        
        candidates.sort(key=lambda x: x[1])
        
        num_to_evict = max(1, int(len(candidates) * eviction_ratio))
        return [key for key, _ in candidates[:num_to_evict]]
    
    def get_system_memory_info(self) -> Dict[str, float]:
        try:
            memory = psutil.virtual_memory()
            return {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'percent_used': memory.percent
            }
        except:
            return {}

class CompressionManager:
    @staticmethod
    def compress_data(data: Any) -> bytes:
        try:
            pickled_data = pickle.dumps(data)
            compressed_data = gzip.compress(pickled_data)
            return compressed_data
        except Exception:
            return pickle.dumps(data)
    
    @staticmethod
    def decompress_data(compressed_data: bytes) -> Any:
        try:
            if compressed_data[:2] == b'\x1f\x8b':
                decompressed_data = gzip.decompress(compressed_data)
                return pickle.loads(decompressed_data)
            else:
                return pickle.loads(compressed_data)
        except Exception:
            return None
    
    @staticmethod
    def should_compress(data_size: int, threshold_kb: int = 100) -> bool:
        return data_size > (threshold_kb * 1024)

class IntelligentCache:
    def __init__(self, cache_dir: str = ".cache", max_memory_mb: int = 1024, 
                 max_disk_gb: int = 10):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.disk_index: Dict[str, str] = {}
        
        self.max_memory = max_memory_mb * 1024 * 1024
        self.max_disk = max_disk_gb * 1024 * 1024 * 1024
        self.current_memory = 0
        
        self.lock = threading.RLock()
        self.memory_manager = MemoryManager(self.max_memory)
        self.compression_manager = CompressionManager()
        
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'disk_reads': 0,
            'disk_writes': 0,
            'compressions': 0,
            'decompressions': 0,
            'cache_size_checks': 0,
            'memory_pressure_events': 0
        }
        
        self.performance_metrics = {
            'avg_access_time_ms': 0.0,
            'avg_storage_time_ms': 0.0,
            'hit_rate_percentage': 0.0,
            'compression_ratio': 0.0
        }
        
        self._load_disk_index()
        self._start_background_maintenance()
    
    def get(self, key: str, default: Any = None) -> Any:
        start_time = time.time()
        
        with self.lock:
            cache_key = self._hash_key(key)
            
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not entry.is_expired():
                    entry.update_access()
                    self.stats['hits'] += 1
                    self._update_performance_metrics('access', time.time() - start_time)
                    return entry.data
                else:
                    self._evict_memory(cache_key)
            
            if cache_key in self.disk_index:
                entry = self._load_from_disk(cache_key)
                if entry and not entry.is_expired():
                    entry.update_access()
                    self._promote_to_memory(cache_key, entry)
                    self.stats['hits'] += 1
                    self.stats['disk_reads'] += 1
                    self._update_performance_metrics('access', time.time() - start_time)
                    return entry.data
                else:
                    self._remove_from_disk(cache_key)
            
            self.stats['misses'] += 1
            self._update_performance_metrics('access', time.time() - start_time)
            return default
    
    def set(self, key: str, value: Any, ttl_hours: int = 24, 
            force_compression: bool = False) -> bool:
        start_time = time.time()
        
        with self.lock:
            cache_key = self._hash_key(key)
            
            try:
                data_size = len(pickle.dumps(value))
                
                should_compress = (force_compression or 
                                 self.compression_manager.should_compress(data_size))
                
                if should_compress:
                    compressed_data = self.compression_manager.compress_data(value)
                    stored_data = compressed_data
                    actual_size = len(compressed_data)
                    self.stats['compressions'] += 1
                else:
                    stored_data = value
                    actual_size = data_size
                
                entry = CacheEntry(
                    data=value,
                    timestamp=datetime.now(),
                    ttl_hours=ttl_hours,
                    size_bytes=actual_size,
                    compression_enabled=should_compress
                )
                
                if self._can_fit_in_memory(actual_size):
                    self._store_in_memory(cache_key, entry)
                else:
                    self._store_on_disk(cache_key, entry, stored_data)
                    self.stats['disk_writes'] += 1
                
                self._update_performance_metrics('storage', time.time() - start_time)
                return True
                
            except Exception as e:
                return False
    
    def _can_fit_in_memory(self, size_bytes: int) -> bool:
        available_memory = self.max_memory - self.current_memory
        return size_bytes <= available_memory
    
    def _store_in_memory(self, cache_key: str, entry: CacheEntry):
        if cache_key in self.memory_cache:
            old_entry = self.memory_cache[cache_key]
            self.current_memory -= old_entry.size_bytes
        
        self.memory_cache[cache_key] = entry
        self.current_memory += entry.size_bytes
        
        self._maybe_evict_memory()
    
    def _store_on_disk(self, cache_key: str, entry: CacheEntry, data: Any):
        disk_path = self.cache_dir / f"{cache_key}.cache"
        
        try:
            with open(disk_path, 'wb') as f:
                if entry.compression_enabled:
                    f.write(data)
                else:
                    pickle.dump(entry, f)
            
            self.disk_index[cache_key] = str(disk_path)
            self._save_disk_index()
            
        except Exception:
            pass
    
    def _load_from_disk(self, cache_key: str) -> Optional[CacheEntry]:
        if cache_key not in self.disk_index:
            return None
        
        disk_path = Path(self.disk_index[cache_key])
        if not disk_path.exists():
            del self.disk_index[cache_key]
            return None
        
        try:
            with open(disk_path, 'rb') as f:
                data = f.read()
            
            if data[:2] == b'\x1f\x8b':
                decompressed_data = self.compression_manager.decompress_data(data)
                entry = CacheEntry(
                    data=decompressed_data,
                    timestamp=datetime.fromtimestamp(disk_path.stat().st_mtime),
                    ttl_hours=24,
                    size_bytes=len(data),
                    compression_enabled=True
                )
                self.stats['decompressions'] += 1
            else:
                entry = pickle.loads(data)
            
            return entry
            
        except Exception:
            try:
                disk_path.unlink()
            except:
                pass
            
            if cache_key in self.disk_index:
                del self.disk_index[cache_key]
            
            return None
    
    def _promote_to_memory(self, cache_key: str, entry: CacheEntry):
        if self._can_fit_in_memory(entry.size_bytes):
            self._store_in_memory(cache_key, entry)
            self._remove_from_disk(cache_key)
    
    def _evict_memory(self, cache_key: str):
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            self.current_memory -= entry.size_bytes
            del self.memory_cache[cache_key]
            self.stats['evictions'] += 1
    
    def _remove_from_disk(self, cache_key: str):
        if cache_key in self.disk_index:
            disk_path = Path(self.disk_index[cache_key])
            try:
                if disk_path.exists():
                    disk_path.unlink()
            except:
                pass
            
            del self.disk_index[cache_key]
            self._save_disk_index()
    
    def _maybe_evict_memory(self):
        pressure_level = self.memory_manager.get_pressure_level(self.current_memory)
        
        if pressure_level != 'none':
            self.stats['memory_pressure_events'] += 1
            eviction_candidates = self.memory_manager.suggest_evictions(
                self.memory_cache, self.current_memory
            )
            
            for cache_key in eviction_candidates:
                if cache_key in self.memory_cache:
                    entry = self.memory_cache[cache_key]
                    
                    if not entry.is_expired() and entry.priority > 0.5:
                        self._store_on_disk(cache_key, entry, entry.data)
                    
                    self._evict_memory(cache_key)
    
    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _load_disk_index(self):
        index_path = self.cache_dir / "cache_index.json"
        if index_path.exists():
            try:
                with open(index_path, 'r') as f:
                    self.disk_index = json.load(f)
            except:
                self.disk_index = {}
    
    def _save_disk_index(self):
        index_path = self.cache_dir / "cache_index.json"
        try:
            with open(index_path, 'w') as f:
                json.dump(self.disk_index, f, indent=2)
        except:
            pass
    
    def _start_background_maintenance(self):
        def maintenance_worker():
            while True:
                try:
                    time.sleep(300)
                    self._perform_maintenance()
                except:
                    pass
        
        maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True)
        maintenance_thread.start()
    
    def _perform_maintenance(self):
        with self.lock:
            expired_keys = []
            
            for key, entry in self.memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._evict_memory(key)
            
            disk_expired = []
            for key in self.disk_index.keys():
                disk_path = Path(self.disk_index[key])
                if disk_path.exists():
                    file_age = datetime.now() - datetime.fromtimestamp(disk_path.stat().st_mtime)
                    if file_age.days > 7:
                        disk_expired.append(key)
            
            for key in disk_expired:
                self._remove_from_disk(key)
            
            self._update_cache_statistics()
    
    def _update_performance_metrics(self, operation: str, duration: float):
        duration_ms = duration * 1000
        
        if operation == 'access':
            current_avg = self.performance_metrics['avg_access_time_ms']
            self.performance_metrics['avg_access_time_ms'] = (current_avg * 0.9) + (duration_ms * 0.1)
        elif operation == 'storage':
            current_avg = self.performance_metrics['avg_storage_time_ms']
            self.performance_metrics['avg_storage_time_ms'] = (current_avg * 0.9) + (duration_ms * 0.1)
    
    def _update_cache_statistics(self):
        total_requests = self.stats['hits'] + self.stats['misses']
        if total_requests > 0:
            self.performance_metrics['hit_rate_percentage'] = (self.stats['hits'] / total_requests) * 100
        
        if self.stats['compressions'] > 0:
            compression_ratio = self.stats['decompressions'] / self.stats['compressions']
            self.performance_metrics['compression_ratio'] = compression_ratio
    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            current_disk_usage = sum(
                Path(path).stat().st_size if Path(path).exists() else 0
                for path in self.disk_index.values()
            )
            
            return {
                'memory_entries': len(self.memory_cache),
                'disk_entries': len(self.disk_index),
                'memory_usage_mb': self.current_memory / (1024 * 1024),
                'memory_usage_percentage': (self.current_memory / self.max_memory) * 100,
                'disk_usage_mb': current_disk_usage / (1024 * 1024),
                'disk_usage_percentage': (current_disk_usage / self.max_disk) * 100,
                'cache_efficiency': self.performance_metrics,
                'operations': self.stats.copy(),
                'system_memory': self.memory_manager.get_system_memory_info(),
                'pressure_level': self.memory_manager.get_pressure_level(self.current_memory)
            }
    
    def get_detailed_analysis(self) -> Dict[str, Any]:
        with self.lock:
            memory_entries_by_priority = {}
            memory_size_distribution = {'small': 0, 'medium': 0, 'large': 0}
            
            for entry in self.memory_cache.values():
                priority_bucket = 'high' if entry.priority > 0.7 else 'medium' if entry.priority > 0.3 else 'low'
                memory_entries_by_priority[priority_bucket] = memory_entries_by_priority.get(priority_bucket, 0) + 1
                
                size_mb = entry.size_bytes / (1024 * 1024)
                if size_mb < 1:
                    memory_size_distribution['small'] += 1
                elif size_mb < 10:
                    memory_size_distribution['medium'] += 1
                else:
                    memory_size_distribution['large'] += 1
            
            return {
                'memory_priority_distribution': memory_entries_by_priority,
                'memory_size_distribution': memory_size_distribution,
                'cache_effectiveness': {
                    'hit_rate': self.performance_metrics['hit_rate_percentage'],
                    'avg_access_time': self.performance_metrics['avg_access_time_ms'],
                    'memory_efficiency': (self.current_memory / self.max_memory) * 100
                },
                'storage_efficiency': {
                    'compression_usage': self.stats['compressions'],
                    'disk_promotions': self.stats['disk_reads'],
                    'eviction_rate': self.stats['evictions']
                }
            }
    
    def optimize(self) -> Dict[str, Any]:
        with self.lock:
            optimization_results = {
                'actions_taken': [],
                'memory_freed_mb': 0,
                'disk_cleaned_mb': 0,
                'performance_improvement': {}
            }
            
            initial_memory = self.current_memory
            initial_disk_count = len(self.disk_index)
            
            low_priority_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.priority < 0.3 and entry.access_count < 2
            ]
            
            for key in low_priority_keys:
                self._evict_memory(key)
            
            if low_priority_keys:
                optimization_results['actions_taken'].append(f'Evicted {len(low_priority_keys)} low-priority entries')
            
            old_disk_files = []
            for key, path in self.disk_index.items():
                disk_path = Path(path)
                if disk_path.exists():
                    file_age = datetime.now() - datetime.fromtimestamp(disk_path.stat().st_mtime)
                    if file_age.days > 3:
                        old_disk_files.append(key)
            
            for key in old_disk_files:
                self._remove_from_disk(key)
            
            if old_disk_files:
                optimization_results['actions_taken'].append(f'Cleaned {len(old_disk_files)} old disk entries')
            
            optimization_results['memory_freed_mb'] = (initial_memory - self.current_memory) / (1024 * 1024)
            optimization_results['disk_cleaned_mb'] = (initial_disk_count - len(self.disk_index)) * 0.5
            
            return optimization_results
    
    def clear(self, preserve_high_priority: bool = False):
        with self.lock:
            if preserve_high_priority:
                keys_to_remove = [
                    key for key, entry in self.memory_cache.items()
                    if entry.priority < 0.8
                ]
                for key in keys_to_remove:
                    self._evict_memory(key)
            else:
                self.memory_cache.clear()
                self.current_memory = 0
            
            if not preserve_high_priority:
                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        cache_file.unlink()
                    except:
                        pass
                
                self.disk_index.clear()
                self._save_disk_index()
            
            if not preserve_high_priority:
                for key in ['hits', 'misses', 'evictions', 'disk_reads', 'disk_writes']:
                    self.stats[key] = 0