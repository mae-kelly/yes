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
                self.prediction_accuracy[pred_key]