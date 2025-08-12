#!/usr/bin/env python3

import logging
import duckdb
import asyncio
import json
import hashlib
import re
import ipaddress
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict, Counter
import statistics
import numpy as np

logger = logging.getLogger(__name__)

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

class IntelligentFieldMapper:
    def __init__(self, content_matcher):
        self.content_matcher = content_matcher
        self.field_mapping_cache = {}
        self.column_quality_scores = defaultdict(float)
        self.semantic_analysis_cache = {}
        
    async def analyze_table_schema_intelligently(self, client, table_path: str, table_name: str) -> Dict[str, Any]:
        cache_key = f"schema:{table_path}"
        if cache_key in self.semantic_analysis_cache:
            return self.semantic_analysis_cache[cache_key]
        
        try:
            table_ref = client.get_table(table_path)
            
            if not table_ref.schema:
                return {'error': 'No schema available'}
            
            columns = [field.name for field in table_ref.schema]
            
            sample_query = f"""
            SELECT {', '.join([f'`{col}`' for col in columns[:50]])}
            FROM `{table_path}`
            WHERE RAND() < 0.05
            LIMIT 500
            """
            
            column_samples = {}
            try:
                job = client.query(sample_query)
                results = list(job.result())
                
                for col_idx, column_name in enumerate(columns[:50]):
                    sample_values = []
                    for row in results:
                        if col_idx < len(row) and row[col_idx] is not None:
                            sample_values.append(str(row[col_idx]))
                    column_samples[column_name] = sample_values[:20]
                    
            except Exception as e:
                logger.warning(f"Failed to sample table {table_path}: {e}")
                return {'error': f'Sampling failed: {e}'}
            
            table_context = {
                'table_name': table_name,
                'table_path': table_path,
                'row_count': table_ref.num_rows or 0,
                'column_count': len(columns)
            }
            
            intelligent_mappings = {}
            confidence_scores = {}
            
            for column_name, samples in column_samples.items():
                analysis = self.content_matcher.analyze_column_intelligently(
                    column_name, samples, table_context
                )
                
                if analysis:
                    field_type, confidence, metadata = analysis
                    intelligent_mappings[field_type] = column_name
                    confidence_scores[field_type] = confidence
                    
                    self.column_quality_scores[f"{table_path}:{column_name}"] = metadata.get('data_quality', {}).get('score', 0.0)
            
            schema_analysis = {
                'table_path': table_path,
                'table_name': table_name,
                'intelligent_mappings': intelligent_mappings,
                'confidence_scores': confidence_scores,
                'column_samples': column_samples,
                'table_context': table_context,
                'schema_quality': self._assess_schema_quality(intelligent_mappings, confidence_scores),
                'recommended_fields': self._prioritize_field_extraction(intelligent_mappings, confidence_scores)
            }
            
            self.semantic_analysis_cache[cache_key] = schema_analysis
            return schema_analysis
            
        except Exception as e:
            logger.error(f"Schema analysis failed for {table_path}: {e}")
            return {'error': str(e)}
    
    def _assess_schema_quality(self, mappings: Dict[str, str], confidences: Dict[str, float]) -> Dict[str, Any]:
        critical_fields = ['hostname', 'ip_address', 'infrastructure_type', 'system_classification']
        
        critical_coverage = sum(1 for field in critical_fields if field in mappings) / len(critical_fields)
        avg_confidence = statistics.mean(confidences.values()) if confidences else 0.0
        
        quality_score = (critical_coverage * 0.6) + (avg_confidence * 0.4)
        
        return {
            'quality_score': quality_score,
            'critical_coverage': critical_coverage,
            'avg_confidence': avg_confidence,
            'field_count': len(mappings),
            'assessment': 'excellent' if quality_score > 0.8 else 'good' if quality_score > 0.6 else 'poor'
        }
    
    def _prioritize_field_extraction(self, mappings: Dict[str, str], confidences: Dict[str, float]) -> List[Tuple[str, str, float]]:
        field_priorities = {
            'hostname': 100,
            'fqdn': 95,
            'ip_address': 90,
            'infrastructure_type': 85,
            'system_classification': 80,
            'global_region': 75,
            'business_unit': 70,
            'country': 65,
            'mac_address': 60
        }
        
        prioritized = []
        for field_type, column_name in mappings.items():
            confidence = confidences.get(field_type, 0.0)
            priority = field_priorities.get(field_type, 50)
            combined_score = (confidence * 0.7) + (priority / 100 * 0.3)
            prioritized.append((field_type, column_name, combined_score))
        
        return sorted(prioritized, key=lambda x: x[2], reverse=True)

class IntelligentAssetProcessor:
    def __init__(self, content_matcher, intelligence_engine):
        self.content_matcher = content_matcher
        self.intelligence_engine = intelligence_engine
        self.asset_registry = {}
        self.processing_lock = threading.RLock()
        self.similarity_threshold = 0.85
        self.conflict_resolution_rules = {
            'cmdb': 4,
            'crowdstrike': 3,
            'splunk': 2,
            'chronicle': 1
        }
    
    def generate_master_asset_id(self, hostname: str, ip_address: str = "", fqdn: str = "") -> str:
        primary_identifier = hostname.upper().strip() if hostname else ""
        
        if not primary_identifier and fqdn:
            primary_identifier = fqdn.lower().strip()
        elif not primary_identifier and ip_address:
            primary_identifier = ip_address.strip()
        
        if not primary_identifier:
            primary_identifier = f"unknown_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        normalized = re.sub(r'[^a-zA-Z0-9\-\.]', '_', primary_identifier)
        return f"asset_{normalized}_{hashlib.md5(normalized.encode()).hexdigest()[:8]}"
    
    def find_similar_assets(self, candidate_asset: IntelligentAssetRecord) -> List[Tuple[str, float]]:
        similar_assets = []
        
        for asset_id, existing_asset in self.asset_registry.items():
            similarity_score = self._calculate_asset_similarity(candidate_asset, existing_asset)
            
            if similarity_score >= self.similarity_threshold:
                similar_assets.append((asset_id, similarity_score))
        
        return sorted(similar_assets, key=lambda x: x[1], reverse=True)
    
    def _calculate_asset_similarity(self, asset1: IntelligentAssetRecord, asset2: IntelligentAssetRecord) -> float:
        similarity_factors = []
        
        if asset1.hostname and asset2.hostname:
            hostname_sim = self._string_similarity(asset1.hostname.upper(), asset2.hostname.upper())
            similarity_factors.append(('hostname', hostname_sim, 0.4))
        
        if asset1.ip_address and asset2.ip_address:
            if asset1.ip_address == asset2.ip_address:
                similarity_factors.append(('ip_exact', 1.0, 0.3))
            else:
                ip_sim = self._ip_similarity(asset1.ip_address, asset2.ip_address)
                similarity_factors.append(('ip_subnet', ip_sim, 0.2))
        
        if asset1.fqdn and asset2.fqdn:
            fqdn_sim = self._string_similarity(asset1.fqdn.lower(), asset2.fqdn.lower())
            similarity_factors.append(('fqdn', fqdn_sim, 0.2))
        
        if asset1.mac_address and asset2.mac_address:
            if asset1.mac_address == asset2.mac_address:
                similarity_factors.append(('mac_exact', 1.0, 0.1))
        
        if not similarity_factors:
            return 0.0
        
        weighted_score = sum(score * weight for _, score, weight in similarity_factors)
        total_weight = sum(weight for _, _, weight in similarity_factors)
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        if str1 == str2:
            return 1.0
        
        if not str1 or not str2:
            return 0.0
        
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return 1.0
        
        common_chars = sum(1 for c in shorter if c in longer)
        return common_chars / len(longer)
    
    def _ip_similarity(self, ip1: str, ip2: str) -> float:
        try:
            addr1 = ipaddress.ip_address(ip1)
            addr2 = ipaddress.ip_address(ip2)
            
            if addr1.version != addr2.version:
                return 0.0
            
            if addr1.version == 4:
                octets1 = str(addr1).split('.')
                octets2 = str(addr2).split('.')
                
                matching_octets = sum(1 for o1, o2 in zip(octets1, octets2) if o1 == o2)
                return matching_octets / 4
            
            return 0.0
            
        except:
            return 0.0
    
    def merge_asset_intelligently(self, primary_asset: IntelligentAssetRecord, 
                                secondary_asset: IntelligentAssetRecord, 
                                source_name: str) -> IntelligentAssetRecord:
        
        merged_asset = IntelligentAssetRecord(master_asset_id=primary_asset.master_asset_id)
        
        fields_to_merge = [
            'hostname', 'fqdn', 'ip_address', 'mac_address', 'infrastructure_type',
            'system_classification', 'global_region', 'country', 'data_center',
            'cloud_region', 'business_unit', 'cio', 'apm', 'application_class'
        ]
        
        for field_name in fields_to_merge:
            primary_value = getattr(primary_asset, field_name, "")
            secondary_value = getattr(secondary_asset, field_name, "")
            
            merged_value = self._resolve_field_conflict(
                field_name, primary_value, secondary_value, 
                primary_asset.source_systems, source_name
            )
            
            setattr(merged_asset, field_name, merged_value)
        
        merged_asset.source_count = primary_asset.source_count + 1
        merged_asset.source_systems = f"{primary_asset.source_systems},{source_name}" if primary_asset.source_systems else source_name
        
        boolean_fields = ['found_in_cmdb', 'found_in_splunk', 'found_in_chronicle', 'found_in_crowdstrike', 
                         'in_splunk', 'in_chronicle', 'in_gso', 'edr_coverage', 'tanium_coverage', 'dlp_coverage']
        
        for field_name in boolean_fields:
            primary_val = getattr(primary_asset, field_name, False)
            secondary_val = getattr(secondary_asset, field_name, False)
            setattr(merged_asset, field_name, primary_val or secondary_val)
        
        if source_name == 'crowdstrike':
            merged_asset.has_crowdstrike = True
            merged_asset.edr_coverage = True
        
        merged_asset.raw_sources = {**primary_asset.raw_sources, source_name: secondary_asset.raw_sources.get(source_name, {})}
        
        merged_asset.intelligence_score = self._calculate_intelligence_score(merged_asset)
        merged_asset.data_quality_score = self._calculate_data_quality_score(merged_asset)
        merged_asset.confidence_score = self._calculate_confidence_score(merged_asset)
        
        return merged_asset
    
    def _resolve_field_conflict(self, field_name: str, primary_value: str, secondary_value: str, 
                              primary_sources: str, secondary_source: str) -> str:
        
        if not secondary_value or secondary_value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY']:
            return primary_value
        
        if not primary_value or primary_value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY']:
            return secondary_value
        
        if primary_value == secondary_value:
            return primary_value
        
        primary_source_priority = max([self.conflict_resolution_rules.get(src.strip(), 0) 
                                     for src in primary_sources.split(',') if src.strip()], default=0)
        secondary_source_priority = self.conflict_resolution_rules.get(secondary_source, 0)
        
        if secondary_source_priority > primary_source_priority:
            return secondary_value
        elif secondary_source_priority < primary_source_priority:
            return primary_value
        else:
            return secondary_value if len(secondary_value) > len(primary_value) else primary_value
    
    def _calculate_intelligence_score(self, asset: IntelligentAssetRecord) -> float:
        score_factors = []
        
        source_diversity = min(asset.source_count / 4.0, 1.0)
        score_factors.append(('source_diversity', source_diversity, 0.3))
        
        critical_fields = [asset.hostname, asset.infrastructure_type, asset.system_classification]
        field_completeness = sum(1 for field in critical_fields if field and field.strip()) / len(critical_fields)
        score_factors.append(('field_completeness', field_completeness, 0.25))
        
        all_fields = [asset.hostname, asset.fqdn, asset.ip_address, asset.infrastructure_type, 
                     asset.system_classification, asset.global_region, asset.business_unit]
        overall_completeness = sum(1 for field in all_fields if field and field.strip()) / len(all_fields)
        score_factors.append(('overall_completeness', overall_completeness, 0.2))
        
        security_coverage = sum([asset.edr_coverage, asset.tanium_coverage, asset.dlp_coverage]) / 3.0
        score_factors.append(('security_coverage', security_coverage, 0.15))
        
        log_coverage = sum([asset.in_splunk, asset.in_chronicle, asset.in_gso]) / 3.0
        score_factors.append(('log_coverage', log_coverage, 0.1))
        
        weighted_score = sum(score * weight for _, score, weight in score_factors)
        return min(1.0, weighted_score)
    
    def _calculate_data_quality_score(self, asset: IntelligentAssetRecord) -> float:
        quality_factors = []
        
        if asset.hostname:
            hostname_quality = 1.0 if self.content_matcher._validate_hostname(asset.hostname) else 0.3
            quality_factors.append(hostname_quality)
        
        if asset.ip_address:
            ip_quality = 1.0 if self.content_matcher._validate_ip(asset.ip_address) else 0.0
            quality_factors.append(ip_quality)
        
        if asset.fqdn:
            fqdn_quality = 1.0 if self.content_matcher._validate_fqdn(asset.fqdn) else 0.5
            quality_factors.append(fqdn_quality)
        
        consistency_score = 1.0
        if asset.hostname and asset.fqdn:
            if asset.hostname.lower() not in asset.fqdn.lower():
                consistency_score *= 0.8
        
        quality_factors.append(consistency_score)
        
        return statistics.mean(quality_factors) if quality_factors else 0.5
    
    def _calculate_confidence_score(self, asset: IntelligentAssetRecord) -> float:
        confidence_factors = []
        
        source_reliability = {
            'cmdb': 0.9,
            'crowdstrike': 0.85,
            'splunk': 0.7,
            'chronicle': 0.75
        }
        
        sources = asset.source_systems.split(',') if asset.source_systems else []
        avg_source_reliability = statistics.mean([source_reliability.get(src.strip(), 0.5) for src in sources]) if sources else 0.5
        confidence_factors.append(avg_source_reliability)
        
        field_validation_score = asset.data_quality_score
        confidence_factors.append(field_validation_score)
        
        completeness_confidence = asset.intelligence_score
        confidence_factors.append(completeness_confidence)
        
        return statistics.mean(confidence_factors)

class IntelligentUniversalCMDBBuilder:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, content_matcher, intelligence_engine):
        self.project_id = project_id
        self.config = config
        self.cache_manager = cache_manager
        self.content_matcher = content_matcher
        self.intelligence_engine = intelligence_engine
        
        from gcp_client import BigQueryClientManager
        self.client_manager = BigQueryClientManager(project_id)
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
        except:
            self.chronicle_client_manager = None
            logger.warning("Chronicle access not available")
        
        self.db_path = config.get('database_path', 'ao1_intelligent_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        
        self.field_mapper = IntelligentFieldMapper(content_matcher)
        self.asset_processor = IntelligentAssetProcessor(content_matcher, intelligence_engine)
        
        self.shutdown_requested = False
        self.processing_stats = {
            'tables_analyzed': 0,
            'assets_discovered': 0,
            'assets_merged': 0,
            'high_quality_assets': 0,
            'processing_errors': 0
        }
        
        self._setup_intelligent_schema()
        logger.info("Intelligent Universal CMDB Builder initialized")
    
    def _setup_intelligent_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS intelligent_asset_inventory")
        self.conn.execute("DROP TABLE IF EXISTS intelligent_endpoints")
        self.conn.execute("DROP TABLE IF EXISTS intelligent_endpoint_data")
        
        self.conn.execute("""
            CREATE TABLE intelligent_asset_inventory (
                master_asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                fqdn VARCHAR,
                ip_address VARCHAR,
                mac_address VARCHAR,
                infrastructure_type VARCHAR,
                system_classification VARCHAR,
                global_region VARCHAR,
                country VARCHAR,
                data_center VARCHAR,
                cloud_region VARCHAR,
                business_unit VARCHAR,
                cio VARCHAR,
                apm VARCHAR,
                application_class VARCHAR,
                edr_coverage BOOLEAN DEFAULT FALSE,
                tanium_coverage BOOLEAN DEFAULT FALSE,
                dlp_coverage BOOLEAN DEFAULT FALSE,
                in_splunk BOOLEAN DEFAULT FALSE,
                in_chronicle BOOLEAN DEFAULT FALSE,
                in_gso BOOLEAN DEFAULT FALSE,
                network_log_types VARCHAR,
                endpoint_log_types VARCHAR,
                cloud_log_types VARCHAR,
                application_log_types VARCHAR,
                identity_log_types VARCHAR,
                found_in_cmdb BOOLEAN DEFAULT FALSE,
                found_in_splunk BOOLEAN DEFAULT FALSE,
                found_in_chronicle BOOLEAN DEFAULT FALSE,
                found_in_crowdstrike BOOLEAN DEFAULT FALSE,
                source_count INTEGER DEFAULT 0,
                intelligence_score DOUBLE DEFAULT 0.0,
                data_quality_score DOUBLE DEFAULT 0.0,
                confidence_score DOUBLE DEFAULT 0.0,
                has_crowdstrike BOOLEAN DEFAULT FALSE,
                source_systems VARCHAR,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE intelligent_endpoints (
                endpoint_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                source_table VARCHAR,
                intelligence_metadata JSON,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE intelligent_endpoint_data (
                data_id VARCHAR PRIMARY KEY,
                endpoint_id VARCHAR,
                field_type VARCHAR,
                field_value VARCHAR,
                confidence_score DOUBLE,
                source_table VARCHAR,
                extraction_metadata JSON,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info("Intelligent database schema created")
    
    async def execute_intelligent_discovery(self, intelligence_result: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting intelligent universal CMDB discovery")
        start_time = datetime.now()
        
        try:
            strategy = intelligence_result.get('strategy_recommendation', {})
            logger.info(f"Using strategy: {strategy.get('strategy_name', 'default')}")
            
            source_tables = {
                'cmdb': 'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
                'splunk': 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
                'crowdstrike': 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT'
            }
            
            if self.chronicle_client_manager:
                source_tables['chronicle'] = 'chronicle-fisv.datalake.events'
            
            discovered_assets = {}
            
            for source_name, table_path in source_tables.items():
                if self.shutdown_requested:
                    break
                
                logger.info(f"Processing {source_name}: {table_path}")
                
                try:
                    client_manager = self.chronicle_client_manager if source_name == 'chronicle' else self.client_manager
                    
                    source_assets = await self._extract_intelligent_assets(
                        client_manager, table_path, source_name
                    )
                    
                    logger.info(f"Extracted {len(source_assets)} assets from {source_name}")
                    
                    for asset_key, asset_data in source_assets.items():
                        if asset_key in discovered_assets:
                            discovered_assets[asset_key] = self.asset_processor.merge_asset_intelligently(
                                discovered_assets[asset_key], asset_data, source_name
                            )
                            self.processing_stats['assets_merged'] += 1
                        else:
                            discovered_assets[asset_key] = asset_data
                            self.processing_stats['assets_discovered'] += 1
                
                except Exception as e:
                    logger.error(f"Failed to process {source_name}: {e}")
                    self.processing_stats['processing_errors'] += 1
            
            logger.info("Performing intelligent asset consolidation")
            consolidated_assets = await self._perform_intelligent_consolidation(discovered_assets)
            
            logger.info("Storing assets in intelligent database")
            stored_count = await self._store_intelligent_assets(consolidated_assets)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            final_stats = {
                'total_assets': len(consolidated_assets),
                'stored_assets': stored_count,
                'high_quality_assets': sum(1 for asset in consolidated_assets.values() if asset.intelligence_score > 0.8),
                'multi_source_assets': sum(1 for asset in consolidated_assets.values() if asset.source_count > 1),
                'cmdb_coverage': sum(1 for asset in consolidated_assets.values() if asset.found_in_cmdb),
                'crowdstrike_coverage': sum(1 for asset in consolidated_assets.values() if asset.found_in_crowdstrike),
                'splunk_coverage': sum(1 for asset in consolidated_assets.values() if asset.found_in_splunk),
                'chronicle_coverage': sum(1 for asset in consolidated_assets.values() if asset.found_in_chronicle),
                'avg_intelligence_score': statistics.mean([asset.intelligence_score for asset in consolidated_assets.values()]) if consolidated_assets else 0.0,
                'avg_data_quality_score': statistics.mean([asset.data_quality_score for asset in consolidated_assets.values()]) if consolidated_assets else 0.0,
                'avg_confidence_score': statistics.mean([asset.confidence_score for asset in consolidated_assets.values()]) if consolidated_assets else 0.0,
                'processing_time_seconds': processing_time,
                'processing_stats': self.processing_stats,
                'database_path': self.db_path
            }
            
            logger.info(f"Intelligent discovery complete: {final_stats['total_assets']} assets processed")
            return final_stats
            
        except Exception as e:
            logger.error(f"Intelligent discovery failed: {e}")
            return {'error': str(e), 'processing_stats': self.processing_stats}
    
    async def _extract_intelligent_assets(self, client_manager, table_path: str, source_name: str) -> Dict[str, IntelligentAssetRecord]:
        cache_key = f"intelligent_extract:{table_path}:{source_name}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logger.debug(f"Using cached extraction for {source_name}")
            return cached_result
        
        assets = {}
        
        try:
            with client_manager.get_client() as client:
                table_name = table_path.split('.')[-1]
                schema_analysis = await self.field_mapper.analyze_table_schema_intelligently(
                    client, table_path, table_name
                )
                
                if 'error' in schema_analysis:
                    logger.warning(f"Schema analysis failed for {table_path}: {schema_analysis['error']}")
                    return assets
                
                mappings = schema_analysis.get('intelligent_mappings', {})
                
                if 'hostname' not in mappings:
                    logger.warning(f"No hostname field found in {table_path}")
                    return assets
                
                hostname_col = mappings['hostname']
                
                select_fields = [f"UPPER(TRIM(`{hostname_col}`)) as hostname"]
                
                for field_type, column_name in mappings.items():
                    if field_type != 'hostname':
                        select_fields.append(f"`{column_name}` as {field_type}")
                
                extraction_query = f"""
                SELECT {', '.join(select_fields)}
                FROM `{table_path}`
                WHERE `{hostname_col}` IS NOT NULL
                AND TRIM(`{hostname_col}`) != ''
                AND LENGTH(TRIM(`{hostname_col}`)) >= 1
                LIMIT 500000
                """
                
                job = client.query(extraction_query)
                results = list(job.result())
                
                for row in results:
                    if not row or not row[0]:
                        continue
                    
                    hostname = str(row[0]).strip().upper()
                    
                    if not hostname or len(hostname) < 1:
                        continue
                    
                    if hostname.upper() in ['NULL', 'NONE', '']:
                        continue
                    
                    master_asset_id = self.asset_processor.generate_master_asset_id(hostname)
                    
                    asset = IntelligentAssetRecord(
                        master_asset_id=master_asset_id,
                        hostname=hostname
                    )
                    
                    for idx, (field_type, _) in enumerate(mappings.items()):
                        if idx < len(row) and row[idx] and str(row[idx]).strip():
                            value = str(row[idx]).strip()
                            if value and len(value) > 0:
                                setattr(asset, field_type, value)
                    
                    if source_name == 'cmdb':
                        asset.found_in_cmdb = True
                    elif source_name == 'splunk':
                        asset.found_in_splunk = True
                        asset.in_splunk = True
                    elif source_name == 'chronicle':
                        asset.found_in_chronicle = True
                        asset.in_chronicle = True
                    elif source_name == 'crowdstrike':
                        asset.found_in_crowdstrike = True
                        asset.has_crowdstrike = True
                        asset.edr_coverage = True
                    
                    asset.source_count = 1
                    asset.source_systems = source_name
                    asset.raw_sources = {source_name: dict(zip([f[0] for f in mappings.items()], row))}
                    
                    asset.intelligence_score = self.asset_processor._calculate_intelligence_score(asset)
                    asset.data_quality_score = self.asset_processor._calculate_data_quality_score(asset)
                    asset.confidence_score = self.asset_processor._calculate_confidence_score(asset)
                    
                    assets[master_asset_id] = asset
                
                self.processing_stats['tables_analyzed'] += 1
                
                self.cache_manager.set(cache_key, assets, ttl_hours=24)
                logger.info(f"Extracted {len(assets)} intelligent assets from {source_name}")
                
        except Exception as e:
            logger.error(f"Asset extraction failed for {table_path}: {e}")
        
        return assets
    
    async def _perform_intelligent_consolidation(self, discovered_assets: Dict[str, IntelligentAssetRecord]) -> Dict[str, IntelligentAssetRecord]:
        logger.info("Performing intelligent asset consolidation")
        
        consolidated = {}
        processed_ids = set()
        
        for asset_id, asset in discovered_assets.items():
            if asset_id in processed_ids:
                continue
            
            similar_assets = self.asset_processor.find_similar_assets(asset)
            
            if similar_assets:
                primary_asset = asset
                
                for similar_id, similarity_score in similar_assets:
                    if similar_id in discovered_assets and similar_id not in processed_ids:
                        similar_asset = discovered_assets[similar_id]
                        
                        primary_asset = self.asset_processor.merge_asset_intelligently(
                            primary_asset, similar_asset, similar_asset.source_systems
                        )
                        
                        processed_ids.add(similar_id)
                
                consolidated[asset_id] = primary_asset
            else:
                consolidated[asset_id] = asset
            
            processed_ids.add(asset_id)
        
        logger.info(f"Consolidated {len(discovered_assets)} assets into {len(consolidated)} unique assets")
        return consolidated
    
    async def _store_intelligent_assets(self, assets: Dict[str, IntelligentAssetRecord]) -> int:
        stored_count = 0
        
        insert_query = """
        INSERT INTO intelligent_asset_inventory (
            master_asset_id, hostname, fqdn, ip_address, mac_address, infrastructure_type,
            system_classification, global_region, country, data_center, cloud_region,
            business_unit, cio, apm, application_class, edr_coverage, tanium_coverage,
            dlp_coverage, in_splunk, in_chronicle, in_gso, network_log_types,
            endpoint_log_types, cloud_log_types, application_log_types, identity_log_types,
            found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike,
            source_count, intelligence_score, data_quality_score, confidence_score,
            has_crowdstrike, source_systems, discovery_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
        """
        
        for asset in assets.values():
            try:
                values = [
                    asset.master_asset_id, asset.hostname, asset.fqdn, asset.ip_address,
                    asset.mac_address, asset.infrastructure_type, asset.system_classification,
                    asset.global_region, asset.country, asset.data_center, asset.cloud_region,
                    asset.business_unit, asset.cio, asset.apm, asset.application_class,
                    asset.edr_coverage, asset.tanium_coverage, asset.dlp_coverage,
                    asset.in_splunk, asset.in_chronicle, asset.in_gso, asset.network_log_types,
                    asset.endpoint_log_types, asset.cloud_log_types, asset.application_log_types,
                    asset.identity_log_types, asset.found_in_cmdb, asset.found_in_splunk,
                    asset.found_in_chronicle, asset.found_in_crowdstrike, asset.source_count,
                    asset.intelligence_score, asset.data_quality_score, asset.confidence_score,
                    asset.has_crowdstrike, asset.source_systems
                ]
                
                self.conn.execute(insert_query, values)
                stored_count += 1
                
                if asset.intelligence_score > 0.8:
                    self.processing_stats['high_quality_assets'] += 1
                
            except Exception as e:
                logger.error(f"Failed to store asset {asset.master_asset_id}: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} intelligent assets in database")
        return stored_count
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        logger.info("Intelligent CMDB Builder closed")