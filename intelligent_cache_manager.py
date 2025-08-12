#!/usr/bin/env python3

import os
import pickle
import hashlib
import threading
import json
import gzip
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, asdict
import psutil
from collections import defaultdict
import statistics

@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    ttl_hours: int
    access_count: int = 0
    last_accessed: datetime = None
    size_bytes: int = 0
    content_hash: str = ""
    access_pattern: str = "unknown"
    priority_score: float = 0.0
    intelligence_metadata: Dict = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
        if self.intelligence_metadata is None:
            self.intelligence_metadata = {}
    
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(hours=self.ttl_hours)
    
    def is_stale(self, staleness_hours: int = 1) -> bool:
        return datetime.now() > self.last_accessed + timedelta(hours=staleness_hours)
    
    def update_access(self):
        self.access_count += 1
        self.last_accessed = datetime.now()
        self.priority_score = self._calculate_priority()
    
    def _calculate_priority(self) -> float:
        recency_factor = 1.0 / max(1, (datetime.now() - self.last_accessed).total_seconds() / 3600)
        frequency_factor = min(10.0, self.access_count)
        size_penalty = max(0.1, 1.0 - (self.size_bytes / (1024 * 1024)))
        
        return recency_factor * frequency_factor * size_penalty

class AccessPatternAnalyzer:
    def __init__(self):
        self.access_history = defaultdict(list)
        self.pattern_weights = {
            'sequential': 1.2,
            'random': 0.8,
            'burst': 1.5,
            'periodic': 1.1
        }
    
    def record_access(self, key: str):
        self.access_history[key].append(datetime.now())
        if len(self.access_history[key]) > 100:
            self.access_history[key] = self.access_history[key][-50:]
    
    def analyze_pattern(self, key: str) -> str:
        history = self.access_history.get(key, [])
        if len(history) < 3:
            return "unknown"
        
        intervals = []
        for i in range(1, len(history)):
            interval = (history[i] - history[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return "unknown"
        
        interval_variance = statistics.variance(intervals) if len(intervals) > 1 else 0
        mean_interval = statistics.mean(intervals)
        
        if interval_variance < mean_interval * 0.1:
            return "periodic"
        elif len(history) > 10 and all(intervals[i] <= intervals[i+1] * 1.1 for i in range(len(intervals)-1)):
            return "sequential"
        elif interval_variance > mean_interval * 2:
            return "burst"
        else:
            return "random"
    
    def get_priority_multiplier(self, pattern: str) -> float:
        return self.pattern_weights.get(pattern, 1.0)

class PredictivePrefetcher:
    def __init__(self):
        self.correlation_matrix = defaultdict(lambda: defaultdict(float))
        self.sequence_patterns = defaultdict(list)
        self.prediction_accuracy = defaultdict(float)
    
    def record_sequence(self, keys: List[str]):
        for i in range(len(keys) - 1):
            current_key = keys[i]
            next_key = keys[i + 1]
            self.correlation_matrix[current_key][next_key] += 1.0
            
        if len(keys) > 2:
            sequence = tuple(keys[-3:])
            self.sequence_patterns[sequence[:-1]].append(sequence[-1])
    
    def predict_next_access(self, current_key: str, recent_sequence: List[str] = None) -> List[str]:
        predictions = []
        
        correlations = self.correlation_matrix.get(current_key, {})
        if correlations:
            sorted_correlations = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
            predictions.extend([key for key, _ in sorted_correlations[:3]])
        
        if recent_sequence and len(recent_sequence) >= 2:
            sequence_key = tuple(recent_sequence[-2:])
            if sequence_key in self.sequence_patterns:
                pattern_predictions = self.sequence_patterns[sequence_key]
                most_common = max(set(pattern_predictions), key=pattern_predictions.count)
                if most_common not in predictions:
                    predictions.append(most_common)
        
        return predictions[:5]
    
    def update_prediction_accuracy(self, predicted_keys: List[str], actual_key: str):
        for pred_key in predicted_keys:
            if pred_key == actual_key:
                self.prediction_accuracy[pred_key] = min(1.0, self.prediction_accuracy[pred_key] + 0.1)
            else:
                self.prediction_accuracy[pred_key] = max(0.0, self.prediction_accuracy[pred_key] - 0.05)

class MemoryPressureManager:
    def __init__(self, max_memory_bytes: int):
        self.max_memory_bytes = max_memory_bytes
        self.pressure_thresholds = {
            'low': 0.7,
            'medium': 0.85,
            'high': 0.95
        }
        self.eviction_strategies = {
            'low': self._gentle_eviction,
            'medium': self._moderate_eviction,
            'high': self._aggressive_eviction
        }
    
    def get_pressure_level(self, current_usage: int) -> str:
        usage_ratio = current_usage / self.max_memory_bytes
        
        if usage_ratio >= self.pressure_thresholds['high']:
            return 'high'
        elif usage_ratio >= self.pressure_thresholds['medium']:
            return 'medium'
        elif usage_ratio >= self.pressure_thresholds['low']:
            return 'low'
        else:
            return 'none'
    
    def _gentle_eviction(self, entries: Dict[str, CacheEntry]) -> List[str]:
        expired_keys = [key for key, entry in entries.items() if entry.is_expired()]
        return expired_keys[:len(expired_keys)//2]
    
    def _moderate_eviction(self, entries: Dict[str, CacheEntry]) -> List[str]:
        candidates = []
        for key, entry in entries.items():
            if entry.is_expired() or entry.is_stale(staleness_hours=2):
                candidates.append((key, entry.priority_score))
        
        candidates.sort(key=lambda x: x[1])
        return [key for key, _ in candidates[:len(candidates)//3]]
    
    def _aggressive_eviction(self, entries: Dict[str, CacheEntry]) -> List[str]:
        all_candidates = [(key, entry.priority_score) for key, entry in entries.items()]
        all_candidates.sort(key=lambda x: x[1])
        return [key for key, _ in all_candidates[:len(all_candidates)//4]]
    
    def suggest_eviction(self, entries: Dict[str, CacheEntry], current_usage: int) -> List[str]:
        pressure_level = self.get_pressure_level(current_usage)
        
        if pressure_level == 'none':
            return []
        
        strategy = self.eviction_strategies[pressure_level]
        return strategy(entries)

class IntelligentContentAnalyzer:
    def __init__(self):
        self.content_signatures = {}
        self.compression_ratios = defaultdict(list)
        self.access_correlations = defaultdict(set)
    
    def analyze_content(self, key: str, data: Any) -> Dict[str, Any]:
        analysis = {
            'data_type': type(data).__name__,
            'estimated_size': self._estimate_size(data),
            'compressibility': self._estimate_compressibility(data),
            'access_locality': self._analyze_access_locality(key),
            'content_hash': self._generate_content_hash(data)
        }
        
        self.content_signatures[key] = analysis['content_hash']
        return analysis
    
    def _estimate_size(self, data: Any) -> int:
        try:
            return len(pickle.dumps(data))
        except:
            return 1024
    
    def _estimate_compressibility(self, data: Any) -> float:
        try:
            serialized = pickle.dumps(data)
            compressed = gzip.compress(serialized)
            ratio = len(compressed) / len(serialized)
            return 1.0 - ratio
        except:
            return 0.5
    
    def _analyze_access_locality(self, key: str) -> float:
        similar_keys = [k for k in self.content_signatures.keys() 
                       if self._keys_similar(key, k)]
        return len(similar_keys) / max(1, len(self.content_signatures))
    
    def _keys_similar(self, key1: str, key2: str) -> bool:
        return any(part in key2 for part in key1.split('_')[:2])
    
    def _generate_content_hash(self, data: Any) -> str:
        try:
            content_str = str(data)[:1000]
            return hashlib.md5(content_str.encode()).hexdigest()[:8]
        except:
            return "unknown"
    
    def find_similar_content(self, content_hash: str) -> List[str]:
        return [key for key, hash_val in self.content_signatures.items() 
                if hash_val == content_hash]

class AdaptiveCompressionManager:
    def __init__(self):
        self.compression_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0, 'avg_ratio': 0.5})
        self.size_thresholds = {
            'small': 1024,
            'medium': 10240,
            'large': 102400
        }
    
    def should_compress(self, data: Any, size_bytes: int) -> bool:
        data_type = type(data).__name__
        stats = self.compression_stats[data_type]
        
        if size_bytes < self.size_thresholds['small']:
            return False
        
        if stats['attempts'] == 0:
            return size_bytes > self.size_thresholds['medium']
        
        success_rate = stats['successes'] / stats['attempts']
        expected_savings = stats['avg_ratio'] * size_bytes
        
        return success_rate > 0.3 and expected_savings > 512
    
    def record_compression_result(self, data_type: str, original_size: int, compressed_size: int):
        stats = self.compression_stats[data_type]
        stats['attempts'] += 1
        
        if compressed_size < original_size:
            stats['successes'] += 1
            ratio = (original_size - compressed_size) / original_size
            stats['avg_ratio'] = (stats['avg_ratio'] + ratio) / 2

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
            'disk_writes': 0,
            'predictions_made': 0,
            'predictions_correct': 0
        }
        
        self.access_analyzer = AccessPatternAnalyzer()
        self.predictive_prefetcher = PredictivePrefetcher()
        self.memory_manager = MemoryPressureManager(self.max_memory_bytes)
        self.content_analyzer = IntelligentContentAnalyzer()
        self.compression_manager = AdaptiveCompressionManager()
        
        self.recent_access_sequence = []
        self.intelligence_enabled = True
        
        self._load_disk_index()
        self._cleanup_expired_entries()
    
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if self.intelligence_enabled:
                self.access_analyzer.record_access(key)
                self._update_access_sequence(key)
            
            cache_key = self._generate_cache_key(key)
            
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if not entry.is_expired():
                    entry.update_access()
                    if self.intelligence_enabled:
                        entry.access_pattern = self.access_analyzer.analyze_pattern(key)
                    self._stats['hits'] += 1
                    self._maybe_prefetch(key)
                    return entry.data
                else:
                    self._evict_from_memory(cache_key)
            
            if cache_key in self._disk_index:
                entry = self._load_from_disk(cache_key)
                if entry and not entry.is_expired():
                    entry.update_access()
                    if self.intelligence_enabled:
                        entry.access_pattern = self.access_analyzer.analyze_pattern(key)
                    self._promote_to_memory(cache_key, entry)
                    self._stats['hits'] += 1
                    self._stats['disk_reads'] += 1
                    self._maybe_prefetch(key)
                    return entry.data
                else:
                    self._remove_from_disk(cache_key)
            
            self._stats['misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl_hours: int = 24, force_disk: bool = False) -> bool:
        with self._lock:
            cache_key = self._generate_cache_key(key)
            
            try:
                content_analysis = {}
                if self.intelligence_enabled:
                    content_analysis = self.content_analyzer.analyze_content(key, value)
                
                serialized_data = pickle.dumps(value)
                size_bytes = len(serialized_data)
                content_hash = hashlib.md5(serialized_data).hexdigest()
                
                should_compress = self.compression_manager.should_compress(value, size_bytes)
                if should_compress:
                    try:
                        compressed_data = gzip.compress(serialized_data)
                        if len(compressed_data) < size_bytes:
                            serialized_data = compressed_data
                            size_bytes = len(compressed_data)
                            self.compression_manager.record_compression_result(
                                type(value).__name__, len(pickle.dumps(value)), size_bytes
                            )
                    except:
                        pass
                
                entry = CacheEntry(
                    data=value,
                    timestamp=datetime.now(),
                    ttl_hours=ttl_hours,
                    size_bytes=size_bytes,
                    content_hash=content_hash,
                    intelligence_metadata=content_analysis
                )
                
                if self.intelligence_enabled:
                    entry.access_pattern = self.access_analyzer.analyze_pattern(key)
                    entry.priority_score = entry._calculate_priority()
                
                if not force_disk and self._can_fit_in_memory(size_bytes):
                    self._store_in_memory(cache_key, entry)
                else:
                    self._store_on_disk(cache_key, entry)
                    self._stats['disk_writes'] += 1
                
                return True
                
            except Exception as e:
                return False
    
    def _update_access_sequence(self, key: str):
        self.recent_access_sequence.append(key)
        if len(self.recent_access_sequence) > 20:
            self.recent_access_sequence = self.recent_access_sequence[-10:]
        
        if len(self.recent_access_sequence) >= 3:
            self.predictive_prefetcher.record_sequence(self.recent_access_sequence[-3:])
    
    def _maybe_prefetch(self, current_key: str):
        if not self.intelligence_enabled:
            return
        
        predictions = self.predictive_prefetcher.predict_next_access(
            current_key, self.recent_access_sequence
        )
        
        for predicted_key in predictions[:2]:
            predicted_cache_key = self._generate_cache_key(predicted_key)
            
            if (predicted_cache_key not in self._memory_cache and 
                predicted_cache_key in self._disk_index):
                
                entry = self._load_from_disk(predicted_cache_key)
                if entry and not entry.is_expired():
                    if self._can_fit_in_memory(entry.size_bytes):
                        self._promote_to_memory(predicted_cache_key, entry)
                        self._stats['predictions_made'] += 1
    
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
                'compressed_files': 0,
                'intelligent_optimizations': 0
            }
            
            self._cleanup_expired_entries()
            
            if self.intelligence_enabled:
                optimization_stats['intelligent_optimizations'] = self._intelligent_optimization()
            
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
    
    def _intelligent_optimization(self) -> int:
        optimizations = 0
        
        suggested_evictions = self.memory_manager.suggest_eviction(
            self._memory_cache, self.current_memory_usage
        )
        
        for cache_key in suggested_evictions:
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if not entry.is_expired():
                    self._store_on_disk(cache_key, entry)
                self._evict_from_memory(cache_key)
                optimizations += 1
        
        similar_content_groups = defaultdict(list)
        for key, entry in self._memory_cache.items():
            content_hash = entry.content_hash
            similar_content_groups[content_hash].append(key)
        
        for content_hash, similar_keys in similar_content_groups.items():
            if len(similar_keys) > 1:
                keep_key = max(similar_keys, key=lambda k: self._memory_cache[k].priority_score)
                for key in similar_keys:
                    if key != keep_key:
                        self._evict_from_memory(key)
                        optimizations += 1
        
        return optimizations
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            memory_usage_mb = self.current_memory_usage / (1024 * 1024)
            disk_usage_mb = self._calculate_disk_usage() / (1024 * 1024)
            
            hit_rate = self._stats['hits'] / (self._stats['hits'] + self._stats['misses']) if (self._stats['hits'] + self._stats['misses']) > 0 else 0
            
            prediction_accuracy = (self._stats['predictions_correct'] / max(1, self._stats['predictions_made']))
            
            intelligence_stats = {}
            if self.intelligence_enabled:
                intelligence_stats = {
                    'prediction_accuracy': prediction_accuracy,
                    'access_patterns_learned': len(self.access_analyzer.access_history),
                    'content_signatures': len(self.content_analyzer.content_signatures),
                    'compression_types_learned': len(self.compression_manager.compression_stats)
                }
            
            return {
                'memory_entries': len(self._memory_cache),
                'disk_entries': len(self._disk_index),
                'memory_usage_mb': round(memory_usage_mb, 2),
                'disk_usage_mb': round(disk_usage_mb, 2),
                'hit_rate': round(hit_rate * 100, 2),
                'stats': self._stats.copy(),
                'intelligence_enabled': self.intelligence_enabled,
                'intelligence_stats': intelligence_stats,
                'memory_pressure': self.memory_manager.get_pressure_level(self.current_memory_usage)
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
        
        if self.intelligence_enabled:
            entries_by_priority = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1].priority_score
            )
        else:
            entries_by_priority = sorted(
                self._memory_cache.items(),
                key=lambda x: (x[1].access_count, x[1].last_accessed)
            )
        
        evicted_count = 0
        target_usage = self.max_memory_bytes * 0.7
        
        for cache_key, entry in entries_by_priority:
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
                    priority = 0
                    if self.intelligence_enabled and cache_key in self._memory_cache:
                        priority = self._memory_cache[cache_key].priority_score
                    disk_entries.append((cache_key, stat.st_atime, stat.st_size, priority))
                except Exception:
                    continue
        
        if self.intelligence_enabled:
            disk_entries.sort(key=lambda x: (x[3], x[1]))
        else:
            disk_entries.sort(key=lambda x: x[1])
        
        evicted_count = 0
        target_usage = self.max_disk_bytes * 0.8
        current_usage = self._calculate_disk_usage()
        
        for cache_key, _, size, _ in disk_entries:
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
            if entry:
                should_promote = False
                
                if self.intelligence_enabled:
                    should_promote = (entry.priority_score > 5.0 and 
                                    entry.access_count >= 3 and 
                                    not entry.is_stale())
                else:
                    should_promote = (entry.access_count >= 3 and not entry.is_stale())
                
                if should_promote and self._can_fit_in_memory(entry.size_bytes):
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
                
                should_compress = age_hours > 6
                if self.intelligence_enabled:
                    entry = self._load_from_disk(cache_key)
                    if entry and entry.intelligence_metadata:
                        compressibility = entry.intelligence_metadata.get('compressibility', 0.5)
                        should_compress = should_compress and compressibility > 0.3
                
                if should_compress:
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