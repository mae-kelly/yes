from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import numpy as np
import hashlib

@dataclass
class QuantumAsset:
    hostname: str
    infrastructure_type: str = ""
    region: str = ""
    country: str = ""
    business_unit: str = ""
    datacenter: str = ""
    cloud_region: str = ""
    cio: str = ""
    apm: str = ""
    application_class: str = ""
    system_classification: str = ""
    edr_coverage: bool = False
    tanium_coverage: bool = False
    dlp_coverage: bool = False
    splunk_logging: bool = False
    gso_logging: bool = False
    domain: str = ""
    ip_address: str = ""
    fqdn: str = ""
    mac_address: str = ""
    network_zones: List[str] = field(default_factory=list)
    ipam_public_ip: bool = False
    geolocation: str = ""
    vpc: str = ""
    crowdstrike_coverage: bool = False
    chronicle_coverage: bool = False
    cmdb_visibility: bool = False
    owner: str = ""
    criticality: str = ""
    environment: str = ""
    visibility_score: float = 0.0
    confidence_score: float = 0.0
    risk_score: float = 0.0
    compliance_score: float = 0.0
    ml_confidence: float = 0.0
    source_tables: Set[str] = field(default_factory=set)
    log_types: Dict[str, List[str]] = field(default_factory=dict)
    data_fields: Dict[str, Any] = field(default_factory=dict)
    visibility_factors: Dict[str, float] = field(default_factory=dict)
    anomaly_scores: Dict[str, float] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.now)
    first_seen: datetime = field(default_factory=datetime.now)
    
    def calculate_visibility_score(self) -> float:
        weights = {
            'cmdb_visibility': 0.25,
            'edr_coverage': 0.15,
            'tanium_coverage': 0.10,
            'dlp_coverage': 0.10,
            'splunk_logging': 0.15,
            'gso_logging': 0.10,
            'crowdstrike_coverage': 0.10,
            'chronicle_coverage': 0.05
        }
        score = sum(weights[k] * getattr(self, k, False) for k in weights)
        self.visibility_score = min(1.0, score)
        return self.visibility_score
    
    def get_unique_id(self) -> str:
        return hashlib.sha256(f"{self.hostname}_{self.domain}".encode()).hexdigest()[:16]
    
    def merge_with(self, other: 'QuantumAsset') -> 'QuantumAsset':
        for attr in ['infrastructure_type', 'region', 'country', 'business_unit', 
                    'datacenter', 'cloud_region', 'cio', 'apm', 'application_class',
                    'system_classification', 'domain', 'ip_address', 'fqdn', 'mac_address',
                    'owner', 'criticality', 'environment', 'geolocation', 'vpc']:
            if not getattr(self, attr) and getattr(other, attr):
                setattr(self, attr, getattr(other, attr))
        
        for coverage in ['edr_coverage', 'tanium_coverage', 'dlp_coverage', 
                        'splunk_logging', 'gso_logging', 'crowdstrike_coverage',
                        'chronicle_coverage', 'cmdb_visibility', 'ipam_public_ip']:
            setattr(self, coverage, getattr(self, coverage) or getattr(other, coverage))
        
        self.source_tables.update(other.source_tables)
        self.network_zones.extend(other.network_zones)
        self.log_types.update(other.log_types)
        self.data_fields.update(other.data_fields)
        self.visibility_factors.update(other.visibility_factors)
        
        self.ml_confidence = max(self.ml_confidence, other.ml_confidence)
        self.confidence_score = max(self.confidence_score, other.confidence_score)
        self.first_seen = min(self.first_seen, other.first_seen)
        self.last_seen = max(self.last_seen, other.last_seen)
        
        self.calculate_visibility_score()
        return self

@dataclass
class LogMapping:
    role: str
    log_types: List[str]
    data_fields: List[str]
    visibility_factors: List[str]
    
    def matches_pattern(self, text: str) -> float:
        text_lower = text.lower()
        matches = sum(1 for field in self.data_fields if field in text_lower)
        return matches / len(self.data_fields) if self.data_fields else 0.0

@dataclass
class DiscoveryMetrics:
    total_assets: int = 0
    cmdb_coverage: float = 0.0
    url_fqdn_coverage: float = 0.0
    public_ip_coverage: float = 0.0
    endpoint_coverage: float = 0.0
    cloud_coverage: float = 0.0
    network_coverage: float = 0.0
    application_coverage: float = 0.0
    identity_coverage: float = 0.0
    host_parity: float = 0.0
    infrastructure_distribution: Dict[str, int] = field(default_factory=dict)
    regional_distribution: Dict[str, int] = field(default_factory=dict)
    business_unit_distribution: Dict[str, int] = field(default_factory=dict)
    system_classification_distribution: Dict[str, int] = field(default_factory=dict)
    security_gaps: List[Dict[str, Any]] = field(default_factory=list)
    logging_gaps: List[Dict[str, Any]] = field(default_factory=list)
    compliance_issues: List[Dict[str, Any]] = field(default_factory=list)