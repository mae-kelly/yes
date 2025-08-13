#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime

@dataclass
class ContentBasedAsset:
    hostname: str = ""
    all_data: Dict[str, Any] = field(default_factory=dict)
    source_tables: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)

@dataclass
class UniversalAsset:
    asset_id: str
    hostname: str = ""
    ip_address: str = ""
    fqdn: str = ""
    mac_address: str = ""
    infrastructure_type: str = ""
    system_classification: str = ""
    global_region: str = ""
    country: str = ""
    business_unit: str = ""
    found_in_cmdb: bool = False
    found_in_splunk: bool = False
    found_in_chronicle: bool = False
    found_in_crowdstrike: bool = False
    has_crowdstrike: bool = False
    in_splunk: bool = False
    in_chronicle: bool = False
    source_count: int = 0
    confidence_score: float = 0.0
    data_quality_score: float = 0.0
    source_systems: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IntelligentAssetRecord:
    master_asset_id: str
    hostname: str = ""
    fqdn: str = ""
    ip_address: str = ""
    mac_address: str = ""
    infrastructure_type: str = ""
    system_classification: str = ""
    global_region: str = ""
    country: str = ""
    data_center: str = ""
    cloud_region: str = ""
    business_unit: str = ""
    cio: str = ""
    apm: str = ""
    application_class: str = ""
    edr_coverage: bool = False
    tanium_coverage: bool = False
    dlp_coverage: bool = False
    in_splunk: bool = False
    in_chronicle: bool = False
    in_gso: bool = False
    network_log_types: str = ""
    endpoint_log_types: str = ""
    cloud_log_types: str = ""
    application_log_types: str = ""
    identity_log_types: str = ""
    found_in_cmdb: bool = False
    found_in_splunk: bool = False
    found_in_chronicle: bool = False
    found_in_crowdstrike: bool = False
    source_count: int = 0
    intelligence_score: float = 0.0
    data_quality_score: float = 0.0
    confidence_score: float = 0.0
    has_crowdstrike: bool = False
    source_systems: str = ""
    enrichment_metadata: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, float] = field(default_factory=dict)
    pattern_analysis: Dict[str, Any] = field(default_factory=dict)
    business_context: Dict[str, Any] = field(default_factory=dict)
    raw_sources: Dict[str, Dict[str, Any]] = field(default_factory=dict)