# core/types.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime
import numpy as np

@dataclass
class Asset:
    id: str
    hostname: str = ""
    ip: str = ""
    fqdn: str = ""
    mac: str = ""
    infrastructure_type: str = ""
    system_classification: str = ""
    business_unit: str = ""
    region: str = ""
    country: str = ""
    datacenter: str = ""
    cloud_region: str = ""
    cio: str = ""
    application_class: str = ""
    
    edr_coverage: bool = False
    dlp_coverage: bool = False
    tanium_coverage: bool = False
    splunk_coverage: bool = False
    chronicle_coverage: bool = False
    crowdstrike_coverage: bool = False
    cmdb_visibility: bool = False
    
    visibility_score: float = 0.0
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    tables_found_in: List[str] = field(default_factory=list)
    
    raw_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HyperAsset:
    id: str
    primary_identity: str = ""
    identity_vectors: Dict[str, np.ndarray] = field(default_factory=dict)
    
    hostname: str = ""
    ip: str = ""
    fqdn: str = ""
    mac: str = ""
    
    infrastructure_type: str = ""
    system_classification: str = ""
    operating_system: str = ""
    platform: str = ""
    architecture: str = ""
    
    business_unit: str = ""
    department: str = ""
    cost_center: str = ""
    application_name: str = ""
    application_class: str = ""
    criticality: str = ""
    
    global_region: str = ""
    region: str = ""
    country: str = ""
    state_province: str = ""
    city: str = ""
    datacenter: str = ""
    zone: str = ""
    cloud_provider: str = ""
    cloud_region: str = ""
    availability_zone: str = ""
    
    owner: str = ""
    technical_contact: str = ""
    business_contact: str = ""
    manager: str = ""
    cio: str = ""
    
    environment: str = ""
    lifecycle_stage: str = ""
    support_tier: str = ""
    maintenance_window: str = ""
    
    asset_tag: str = ""
    serial_number: str = ""
    model: str = ""
    manufacturer: str = ""
    purchase_date: str = ""
    warranty_expiration: str = ""
    
    network_segment: str = ""
    vlan: str = ""
    subnet: str = ""
    domain: str = ""
    forest: str = ""
    network_zones: List[str] = field(default_factory=list)
    
    edr_coverage: bool = False
    edr_agent_version: str = ""
    dlp_coverage: bool = False
    dlp_agent_version: str = ""
    tanium_coverage: bool = False
    tanium_agent_version: str = ""
    splunk_coverage: bool = False
    splunk_forwarder_version: str = ""
    chronicle_coverage: bool = False
    chronicle_collector_version: str = ""
    crowdstrike_coverage: bool = False
    crowdstrike_agent_version: str = ""
    cmdb_visibility: bool = False
    cmdb_last_update: str = ""
    
    antivirus_installed: bool = False
    antivirus_product: str = ""
    antivirus_version: str = ""
    firewall_enabled: bool = False
    encryption_status: str = ""
    patch_level: str = ""
    vulnerability_score: float = 0.0
    
    visibility_score: float = 0.0
    quality_score: float = 0.0
    confidence_score: float = 0.0
    intelligence_quotient: float = 0.0
    quality_coefficient: float = 0.0
    confidence_index: float = 0.0
    entropy_measure: float = 0.0
    risk_score: float = 0.0
    compliance_score: float = 0.0
    
    ml_confidence: float = 0.0
    ml_field_type: str = ""
    ml_processing_method: str = ""
    
    evidence_chains: List[Dict[str, Any]] = field(default_factory=list)
    source_provenance: List[str] = field(default_factory=list)
    tables_found_in: List[str] = field(default_factory=list)
    correlation_graph: Dict[str, float] = field(default_factory=dict)
    
    quantum_state: Dict[str, Any] = field(default_factory=dict)
    emergence_patterns: List[Tuple[str, float]] = field(default_factory=list)
    temporal_signatures: Dict[str, float] = field(default_factory=dict)
    
    meta_intelligence: Dict[str, Any] = field(default_factory=dict)
    coverage_analysis: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    compliance_status: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    first_seen: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class QuantumFieldMapping:
    field_type: str
    column_identifier: str
    confidence_score: float
    semantic_similarity: float
    pattern_coherence: float
    context_alignment: float
    samples: List[str] = field(default_factory=list)
    validation_chains: List[Dict[str, Any]] = field(default_factory=list)
    emergence_indicators: Dict[str, float] = field(default_factory=dict)
    ml_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HyperSchema:
    table_path: str
    name: str
    quantum_mappings: Dict[str, QuantumFieldMapping] = field(default_factory=dict)
    quality_tensor: np.ndarray = field(default_factory=lambda: np.array([]))
    row_count: int = 0
    column_count: int = 0
    entropy_distribution: Dict[str, float] = field(default_factory=dict)
    semantic_density: float = 0.0
    pattern_complexity: float = 0.0
    processing_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Discovery:
    assets: Dict[str, Asset] = field(default_factory=dict)
    discovery_stats: Dict[str, Any] = field(default_factory=dict)
    insights: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QuantumDiscovery:
    hyper_assets: Dict[str, HyperAsset] = field(default_factory=dict)
    quantum_schemas: Dict[str, HyperSchema] = field(default_factory=dict)
    intelligence_metrics: Dict[str, Any] = field(default_factory=dict)
    emergence_insights: List[Dict[str, Any]] = field(default_factory=list)
    strategic_recommendations: List[str] = field(default_factory=list)
    visibility_matrix: np.ndarray = field(default_factory=lambda: np.array([]))
    correlation_tensor: np.ndarray = field(default_factory=lambda: np.array([]))
    quantum_coherence: float = 0.0
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class QuantumIntelligence:
    pattern_tensors: Dict[str, np.ndarray] = field(default_factory=dict)
    embedding_manifolds: Dict[str, np.ndarray] = field(default_factory=dict)
    relationship_graphs: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)
    learning_dynamics: Dict[str, Any] = field(default_factory=dict)
    prediction_models: Dict[str, Any] = field(default_factory=dict)
    emergence_functions: Dict[str, callable] = field(default_factory=dict)
    training_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Evidence:
    source_table: str
    field_name: str
    value: str
    confidence: float
    reliability: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    validation_status: str = ""
    processing_method: str = ""

@dataclass
class EntityCluster:
    cluster_id: str
    entities: List[str]
    centroid: np.ndarray
    coherence: float
    density: float
    separation: float
    cluster_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataSource:
    source_id: str
    table_path: str
    column_name: str
    sample_values: List[str]
    field_type: str
    confidence: float
    discovery_method: str
    processing_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessingStats:
    total_tables_processed: int = 0
    total_rows_processed: int = 0
    total_cells_analyzed: int = 0
    total_assets_discovered: int = 0
    ml_predictions_made: int = 0
    high_confidence_predictions: int = 0
    processing_errors: int = 0
    coverage_flags_set: int = 0
    enrichment_operations: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    processing_time_seconds: float = 0.0

class FieldClassifier:
    def __init__(self):
        self.field_types = [
            'hostname', 'ip_address', 'fqdn', 'mac_address', 'infrastructure_type',
            'system_classification', 'operating_system', 'platform', 'architecture',
            'business_unit', 'department', 'cost_center', 'application_name', 'application_class',
            'criticality', 'global_region', 'country', 'datacenter', 'zone', 'cloud_provider',
            'cloud_region', 'owner', 'technical_contact', 'cio', 'environment',
            'lifecycle_stage', 'asset_tag', 'serial_number', 'model', 'manufacturer',
            'network_segment', 'vlan', 'subnet', 'domain', 'edr_coverage', 'dlp_coverage',
            'tanium_coverage', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage',
            'antivirus_product', 'patch_level', 'vulnerability_score', 'unknown'
        ]
        
        self.field_categories = {
            'identity': ['hostname', 'ip_address', 'fqdn', 'mac_address'],
            'infrastructure': ['infrastructure_type', 'system_classification', 'operating_system', 'platform'],
            'business': ['business_unit', 'department', 'application_name', 'criticality'],
            'location': ['global_region', 'country', 'datacenter', 'zone', 'cloud_region'],
            'ownership': ['owner', 'technical_contact', 'cio'],
            'security': ['edr_coverage', 'dlp_coverage', 'tanium_coverage', 'splunk_coverage'],
            'hardware': ['model', 'manufacturer', 'serial_number', 'asset_tag'],
            'network': ['network_segment', 'vlan', 'subnet', 'domain']
        }
    
    def __call__(self, embeddings):
        import torch
        batch_size = embeddings.shape[0] if hasattr(embeddings, 'shape') else 1
        num_classes = len(self.field_types)
        return torch.randn(batch_size, num_classes)
    
    def get_field_category(self, field_type: str) -> str:
        for category, fields in self.field_categories.items():
            if field_type in fields:
                return category
        return 'other'

class PatternRecognizer:
    def __init__(self):
        self.pattern_library = {
            'hostname': [
                r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$',
                r'^[a-zA-Z0-9]{1,63}$',
                r'^[a-zA-Z]{2,6}[0-9]{1,8}$'
            ],
            'ip_address': [
                r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
                r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
            ],
            'mac_address': [
                r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$',
                r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$'
            ],
            'fqdn': [
                r'^[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$'
            ]
        }
        
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
    
    def predict_classification(self, column_name: str, samples: List[str]) -> Dict[str, Any]:
        if not samples:
            return {'field_type': 'unknown', 'confidence': 0.0, 'pattern_based': False}
        
        best_match = None
        best_confidence = 0.0
        
        for field_type, patterns in self.pattern_library.items():
            matches = 0
            for sample in samples[:50]:
                for pattern in patterns:
                    try:
                        if re.match(pattern, str(sample), re.IGNORECASE):
                            matches += 1
                            break
                    except:
                        continue
            
            confidence = matches / min(len(samples), 50)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = field_type
        
        confidence_level = 'high' if best_confidence >= self.confidence_thresholds['high'] else \
                          'medium' if best_confidence >= self.confidence_thresholds['medium'] else 'low'
        
        return {
            'field_type': best_match or 'unknown',
            'confidence': best_confidence,
            'confidence_level': confidence_level,
            'pattern_based': True,
            'samples_analyzed': min(len(samples), 50),
            'pattern_matches': int(best_confidence * min(len(samples), 50))
        }

class QualityAnalyzer:
    def __init__(self):
        self.quality_metrics = [
            'completeness', 'accuracy', 'consistency', 'timeliness', 
            'validity', 'uniqueness', 'integrity'
        ]
    
    def analyze_asset_quality(self, asset: HyperAsset) -> Dict[str, float]:
        scores = {}
        
        all_fields = [
            asset.hostname, asset.ip, asset.fqdn, asset.mac, asset.infrastructure_type,
            asset.system_classification, asset.business_unit, asset.global_region,
            asset.datacenter, asset.owner, asset.environment, asset.criticality
        ]
        
        filled_fields = sum(1 for field in all_fields if field and field.strip())
        scores['completeness'] = filled_fields / len(all_fields)
        
        coverage_fields = [
            asset.edr_coverage, asset.dlp_coverage, asset.tanium_coverage,
            asset.splunk_coverage, asset.chronicle_coverage, asset.cmdb_visibility
        ]
        scores['coverage'] = sum(1 for field in coverage_fields if field) / len(coverage_fields)
        
        scores['source_reliability'] = min(1.0, len(asset.tables_found_in) / 3.0)
        
        scores['timeliness'] = 1.0 if asset.last_updated else 0.5
        
        scores['overall_quality'] = sum(scores.values()) / len(scores)
        
        return scores