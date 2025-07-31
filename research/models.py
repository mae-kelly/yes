from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class EnhancedMatch:
    field: str
    table: str
    dataset: str
    requirement: str
    score: float
    semantic_depth: int
    reasoning: List[str]
    confidence_interval: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    data_samples: List[str] = field(default_factory=list)
    pattern_type: str = "unknown"
    business_priority: int = 5
    table_metrics: Dict[str, Any] = field(default_factory=dict)
    calibrated_confidence: float = 0.0

@dataclass
class TableMetrics:
    row_count: int
    column_count: int
    size_bytes: int
    last_modified: datetime
    creation_time: datetime
    table_type: str
    clustering_fields: List[str]
    partitioning_field: Optional[str]
    labels: Dict[str, str]