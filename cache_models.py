#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime, timedelta

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