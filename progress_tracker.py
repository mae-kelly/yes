#!/usr/bin/env python3

import time
import threading
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class ProcessingStats:
    datasets_total: int = 0
    datasets_processed: int = 0
    datasets_skipped: int = 0
    datasets_failed: int = 0
    tables_total: int = 0
    tables_processed: int = 0
    tables_skipped: int = 0
    tables_failed: int = 0
    endpoints_discovered: int = 0
    bigquery_bytes_processed: int = 0
    processing_time_seconds: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class ProgressTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.start_time = time.time()
        self.stats = ProcessingStats()
        self.last_checkpoint = time.time()
        self.checkpoint_interval = 60
        
    def update_stats(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.stats, key):
                    if isinstance(getattr(self.stats, key), list):
                        getattr(self.stats, key).append(value)
                    else:
                        setattr(self.stats, key, getattr(self.stats, key) + value)
    
    def set_stats(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.stats, key):
                    setattr(self.stats, key, value)
    
    def get_stats(self) -> ProcessingStats:
        with self._lock:
            self.stats.processing_time_seconds = time.time() - self.start_time
            return ProcessingStats(**asdict(self.stats))
    
    def should_checkpoint(self) -> bool:
        current_time = time.time()
        if current_time - self.last_checkpoint >= self.checkpoint_interval:
            self.last_checkpoint = current_time
            return True
        return False