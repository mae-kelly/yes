# core/types.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import numpy as np

@dataclass
class Asset:
    id: str
    hostname: str = ""
    ip: str = ""
    fqdn: str = ""
    mac: str = ""
    infra_type: str = ""
    system_class: str = ""
    region: str = ""
    country: str = ""
    datacenter: str = ""
    cloud_region: str = ""
    business_unit: str = ""
    cio: str = ""
    app_class: str = ""
    edr: bool = False
    dlp: bool = False
    tanium: bool = False
    splunk: bool = False
    chronicle: bool = False
    gso: bool = False
    cmdb: bool = False
    crowdstrike: bool = False
    sources: int = 0
    intelligence: float = 0.0
    quality: float = 0.0
    confidence: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FieldMapping:
    field_type: str
    column: str
    confidence: float
    patterns: List[str] = field(default_factory=list)
    validators: List[str] = field(default_factory=list)
    samples: List[str] = field(default_factory=list)

@dataclass
class TableSchema:
    path: str
    name: str
    mappings: Dict[str, FieldMapping] = field(default_factory=dict)
    quality: float = 0.0
    rows: int = 0
    columns: int = 0

@dataclass
class Discovery:
    assets: Dict[str, Asset] = field(default_factory=dict)
    schemas: Dict[str, TableSchema] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    insights: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class Intelligence:
    patterns: Dict[str, float] = field(default_factory=dict)
    embeddings: Dict[str, np.ndarray] = field(default_factory=dict)
    relationships: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)
    learning: Dict[str, Any] = field(default_factory=dict)
    predictions: Dict[str, Any] = field(default_factory=dict)