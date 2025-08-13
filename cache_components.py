#!/usr/bin/env python3

import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict

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
    
    def _gentle_eviction(self, entries):
        expired_keys = [key for key, entry in entries.items() if entry.is_expired()]
        return expired_keys[:len(expired_keys)//2]
    
    def _moderate_eviction(self, entries):
        candidates = []
        for key, entry in entries.items():
            if entry.is_expired() or entry.is_stale(staleness_hours=2):
                candidates.append((key, entry.priority_score))
        
        candidates.sort(key=lambda x: x[1])
        return [key for key, _ in candidates[:len(candidates)//3]]
    
    def _aggressive_eviction(self, entries):
        all_candidates = [(key, entry.priority_score) for key, entry in entries.items()]
        all_candidates.sort(key=lambda x: x[1])
        return [key for key, _ in all_candidates[:len(all_candidates)//4]]
    
    def suggest_eviction(self, entries, current_usage: int) -> List[str]:
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
            import pickle
            return len(pickle.dumps(data))
        except:
            return 1024
    
    def _estimate_compressibility(self, data: Any) -> float:
        try:
            import pickle
            import gzip
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
            import hashlib
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