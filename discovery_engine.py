#!/usr/bin/env python3

import os
import asyncio
import logging
import duckdb
import time
import multiprocessing as mp
from typing import Dict, List, Any, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dataclasses import asdict
import threading
import json
import random

from gcp_client import BigQueryClientManager
from content_matcher import ContentBasedMatcher
from cache_manager import CacheManager
from progress_tracker import ProgressTracker
from checkpoint_manager import CheckpointManager
from signal_handler import SignalHandler

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

logger = logging.getLogger(__name__)

class PrettyLogger:
    @staticmethod
    def info(msg: str):
        print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   {msg}")
    
    @staticmethod
    def success(msg: str):
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   {msg}")
    
    @staticmethod
    def warning(msg: str):
        print(f"   ⚠°｡⋆⸜ ♡   {msg}")
    
    @staticmethod
    def error(msg: str):
        print(f"   ✗°｡⋆⸜ ♡   {msg}")
    
    @staticmethod
    def column_detection(table_name: str, expected: str, found: str):
        print(f"   ･ﾟ✧ ◞ ♡   {table_name}: Expected '{expected}' → Found '{found}'")
    
    @staticmethod
    def ao1_metric(metric_name: str, value: str):
        print(f"   ♡₊˚ ⋆｡˚   AO1 {metric_name}: {value}")
    
    @staticmethod
    def visibility_analysis(analysis: str):
        print(f"   ･ﾟ✧ ◞ ♡   Visibility Analysis: {analysis}")
    
    @staticmethod
    def critical_discovery(source: str, count: int):
        print(f"   ♡˗ˏˋ ◞ ～   {source} Discovery: {count:,} endpoints")
    
    @staticmethod
    def gap_identification(gap_type: str, count: int):
        print(f"   ⚠°｡⋆⸜ ♡   Gap Identified - {gap_type}: {count:,} assets")

class IntelligentColumnMatcher:
    @staticmethod
    def find_column_case_insensitive(column_name: str, available_columns: List[str]) -> str:
        column_lower = column_name.lower()
        
        for available_col in available_columns:
            if available_col.lower() == column_lower:
                return available_col
        
        for available_col in available_columns:
            if column_lower in available_col.lower() or available_col.lower() in column_lower:
                return available_col
        
        column_variations = [
            column_name.upper(),
            column_name.lower(), 
            column_name.replace('_', '').upper(),
            column_name.replace('_', '').lower(),
            column_name.replace('_', ' ').upper(),
            column_name.replace('_', ' ').lower()
        ]
        
        for variation in column_variations:
            for available_col in available_columns:
                if variation == available_col or variation.replace(' ', '_') == available_col:
                    return available_col
        
        return None
    
    @staticmethod
    def smart_column_mapping(expected_fields: Dict[str, str], available_columns: List[str]) -> Dict[str, str]:
        mapped_fields = {}
        
        for field_key, expected_column in expected_fields.items():
            found_column = IntelligentColumnMatcher.find_column_case_insensitive(expected_column, available_columns)
            if found_column:
                mapped_fields[field_key] = found_column
            else:
                potential_matches = [col for col in available_columns 
                                   if any(part.lower() in col.lower() 
                                         for part in expected_column.replace('_', ' ').split())]
                if potential_matches:
                    mapped_fields[field_key] = potential_matches[0]
        
        return mapped_fields

class AO1IntelligentDiscovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Log Visibility Measurement System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*90)
        PrettyLogger.info("Initializing brilliant AO1 visibility measurement capabilities")
        
        self.client_manager = BigQueryClientManager(project_id)
        self.chronicle_client_manager = None
        
        if not self.client_manager.test_connection():
            raise ConnectionError("Failed to authenticate with BigQuery")
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
            if not self.chronicle_client_manager.test_connection():
                PrettyLogger.warning("Chronicle project authentication failed")
                self.chronicle_client_manager = None
        except Exception:
            self.chronicle_client_manager = None
        
        PrettyLogger.success("Connected to data sources - building AO1 visibility CMDB")
        
        self.matcher = ContentBasedMatcher()
        self.cache = CacheManager(self.config.get('cache_dir', '.cache'))
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        self.column_matcher = IntelligentColumnMatcher()
        
        self.db_path = self.config.get('database_path', 'ao1_visibility_cmdb.db')
        self.max_workers = min(2, self.config.get('max_workers', 2))
        
        self.ao1_source_definitions = {
            'cmdb_master': {
                'project': project_id,
                'dataset': 'SAS_BI',
                'table': 'V_DIM_ENDPOINT',
                'primary_key': 'endpoint_nme',
                'fields': {
                    'hostname': 'endpoint_nme',
                    'region': 'endpointregion_nme', 
                    'environment': 'endpointenvironment_type',
                    'type': 'endpoint_type',
                    'business_unit': 'businessunit_nme'
                },
                'field_variations': {
                    'hostname': ['endpoint_nme', 'Endpoint_Nme', 'ENDPOINT_NME', 'endpoint_name', 'host_name'],
                    'region': ['endpointregion_nme', 'EndpointRegion_Nme', 'ENDPOINTREGION_NME', 'region', 'endpoint_region'],
                    'environment': ['endpointenvironment_type', 'EndpointEnvironment_Type', 'ENDPOINTENVIRONMENT_TYPE', 'environment', 'env'],
                    'type': ['endpoint_type', 'Endpoint_Type', 'ENDPOINT_TYPE', 'system_type', 'classification'],
                    'business_unit': ['businessunit_nme', 'BusinessUnit_Nme', 'BUSINESSUNIT_NME', 'business_unit', 'bu']
                },
                'source_type': 'cmdb',
                'priority': 100
            },
            'security_agents': {
                'project': project_id,
                'dataset': 'SAS_BI',
                'table': 'V_DIM_ENDPOINTAGENT',
                'primary_key': 'endpoint_nme',
                'fields': {
                    'hostname': 'endpoint_nme',
                    'region': 'endpointregion_nme',
                    'environment': 'endpointenvironment_type',
                    'agent_type': 'agenttype_nme'
                },
                'field_variations': {
                    'hostname': ['endpoint_nme', 'Endpoint_Nme', 'ENDPOINT_NME', 'endpoint_name', 'host_name'],
                    'region': ['endpointregion_nme', 'EndpointRegion_Nme', 'ENDPOINTREGION_NME', 'region'],
                    'environment': ['endpointenvironment_type', 'EndpointEnvironment_Type', 'ENDPOINTENVIRONMENT_TYPE', 'environment'],
                    'agent_type': ['agenttype_nme', 'AgentType_Nme', 'AGENTTYPE_NME', 'agent_type', 'tool_type']
                },
                'source_type': 'crowdstrike',
                'priority': 95
            },
            'splunk_logs': {
                'project': project_id,
                'dataset': 'SAS_BI',
                'table': 'V_SPL_ENDPOINT_LOG',
                'primary_key': 'host_nme',
                'fields': {
                    'hostname': 'host_nme',
                    'region': 'region',
                    'environment': 'environment',
                    'log_volume': 'daily_log_volume'
                },
                'field_variations': {
                    'hostname': ['host_nme', 'HOST_NME', 'Host_Nme', 'hostname', 'host_name', 'endpoint'],
                    'region': ['region', 'REGION', 'Region', 'location', 'geo'],
                    'environment': ['environment', 'ENVIRONMENT', 'Environment', 'env', 'stage'],
                    'log_volume': ['daily_log_volume', 'DAILY_LOG_VOLUME', 'log_volume', 'volume']
                },
                'source_type': 'splunk',
                'priority': 90
            },
            'chronicle_events': {
                'project': 'chronicle-fisv',
                'dataset': 'datalake', 
                'table': 'events',
                'primary_key': 'principal.hostname',
                'fields': {
                    'hostname': 'principal.hostname',
                    'region': 'network.ip_geo_artifact.location.region',
                    'event_type': 'metadata.event_type'
                },
                'field_variations': {
                    'hostname': ['principal.hostname', 'PRINCIPAL.HOSTNAME', 'hostname', 'host', 'endpoint'],
                    'region': ['network.ip_geo_artifact.location.region', 'region', 'location', 'geo'],
                    'event_type': ['metadata.event_type', 'event_type', 'type']
                },
                'source_type': 'chronicle',
                'priority': 85
            }
        }
        
        self.ao1_visibility_requirements = {
            'global_view': {
                'description': 'CSOC ability to view x% of all assets globally',
                'measurement': 'percentage_with_logging_coverage'
            },
            'infrastructure_type': {
                'description': 'Visibility by host and log type across infrastructure types',
                'categories': ['On-Prem', 'Cloud', 'SaaS', 'API']
            },
            'regional_view': {
                'description': 'Visibility statement on % of visibility by location',
                'breakdown': ['Global Region', 'Country', 'Data Center', 'Cloud region']
            },
            'bu_application_view': {
                'description': 'Business Unit and Application visibility breakdown',
                'categories': ['Business Unit', 'CIO', 'APM', 'Application Class']
            },
            'system_classification': {
                'description': 'System type visibility analysis',
                'types': ['Web Server', 'Windows Server', 'Linux Server', 'Database', 'Network Appliance']
            },
            'security_control_coverage': {
                'description': 'Security tool coverage analysis',
                'tools': ['EDR', 'Tanium', 'DLP Agent']
            }
        }
        
        self.processed_datasets = set()
        self.processed_tables = set()
        self._processing_lock = threading.Lock()
        self.ao1_metrics = {}
        self.visibility_analysis = {}
        
        self._setup_ao1_intelligent_database()
    
    def _setup_ao1_intelligent_database(self):
        self.conn = duckdb.connect(self.db_path)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_asset_inventory (
            hostname VARCHAR PRIMARY KEY,
            fqdn VARCHAR,
            ip_addresses TEXT,
            
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
            environment VARCHAR,
            
            in_splunk BOOLEAN DEFAULT FALSE,
            in_chronicle BOOLEAN DEFAULT FALSE,
            in_gso BOOLEAN DEFAULT FALSE,
            splunk_log_volume BIGINT DEFAULT 0,
            chronicle_event_count BIGINT DEFAULT 0,
            last_splunk_log TIMESTAMP,
            last_chronicle_event TIMESTAMP,
            
            has_edr BOOLEAN DEFAULT FALSE,
            has_tanium BOOLEAN DEFAULT FALSE,
            has_dlp BOOLEAN DEFAULT FALSE,
            has_crowdstrike BOOLEAN DEFAULT FALSE,
            agent_coverage_score DOUBLE DEFAULT 0.0,
            
            found_in_cmdb BOOLEAN DEFAULT FALSE,
            cmdb_last_updated TIMESTAMP,
            source_systems TEXT,
            data_quality_score DOUBLE DEFAULT 0.0,
            
            url_fqdn_coverage BOOLEAN DEFAULT FALSE,
            public_ip_space_mapped BOOLEAN DEFAULT FALSE,
            domain_visibility BOOLEAN DEFAULT FALSE,
            
            ao1_visibility_score DOUBLE DEFAULT 0.0,
            ao1_gap_severity VARCHAR DEFAULT 'Unknown',
            ao1_recommendation TEXT,
            
            discovery_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_visibility_metrics (
            metric_category VARCHAR,
            metric_name VARCHAR,
            metric_value DOUBLE,
            metric_target DOUBLE,
            gap_percentage DOUBLE,
            improvement_priority INTEGER,
            calculation_method TEXT,
            last_calculated TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (metric_category, metric_name)
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_gap_analysis (
            gap_id VARCHAR PRIMARY KEY,
            gap_category VARCHAR,
            gap_description TEXT,
            affected_asset_count INTEGER,
            severity_level VARCHAR,
            business_impact TEXT,
            recommended_action TEXT,
            estimated_effort VARCHAR,
            identified_at TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_logging_compliance (
            hostname VARCHAR,
            logging_platform VARCHAR,
            compliance_status VARCHAR,
            log_types_covered TEXT,
            coverage_percentage DOUBLE,
            gaps_identified TEXT,
            compliance_date TIMESTAMP,
            PRIMARY KEY (hostname, logging_platform)
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_domain_visibility (
            domain_name VARCHAR PRIMARY KEY,
            asset_count INTEGER,
            covered_assets INTEGER,
            visibility_percentage DOUBLE,
            missing_coverage INTEGER,
            domain_classification VARCHAR,
            last_analyzed TIMESTAMP DEFAULT NOW()
        )
        """)
    
    async def execute_ao1_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Executing brilliant AO1 log visibility discovery")
        
        try:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            if checkpoint:
                PrettyLogger.info("Resuming AO1 discovery from intelligent checkpoint")
                await self._resume_from_checkpoint(checkpoint)
            
            await self._discover_critical_ao1_sources()
            await self._execute_comprehensive_discovery()
            await self._calculate_ao1_visibility_metrics()
            await self._perform_gap_analysis()
            await self._generate_compliance_insights()
            
            stats = self.progress.get_stats()
            queries = self._create_ao1_analysis_queries()
            
            final_results = {
                'processing_time': time.time() - start_time,
                'database_path': self.db_path,
                'total_assets_discovered': self._count_total_assets(),
                'ao1_visibility_metrics': self._get_ao1_metrics(),
                'gap_analysis': self._get_gap_analysis(),
                'compliance_status': self._get_compliance_status(),
                'performance_stats': asdict(stats),
                'ao1_recommendations': self._generate_ao1_recommendations()
            }
            
            self.checkpoint_manager.clear_checkpoint()
            PrettyLogger.success("AO1 discovery completed with brilliant insights")
            
            return final_results, queries
            
        except Exception as e:
            PrettyLogger.error(f"AO1 discovery failed: {e}")
            await self._save_emergency_checkpoint()
            raise
        finally:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
    
    async def _discover_critical_ao1_sources(self):
        PrettyLogger.info("Discovering critical AO1 data sources with brilliant column detection")
        
        for source_name, source_config in self.ao1_source_definitions.items():
            try:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                client_manager = self.chronicle_client_manager if source_config['project'] == 'chronicle-fisv' else self.client_manager
                
                if client_manager is None:
                    PrettyLogger.warning(f"Skipping {source_name} - client unavailable")
                    continue
                
                endpoints_discovered = await self._intelligent_source_discovery(source_name, source_config, client_manager)
                PrettyLogger.critical_discovery(source_name, endpoints_discovered)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                PrettyLogger.error(f"Failed to discover {source_name}: {e}")
                await asyncio.sleep(3)
    
    async def _intelligent_source_discovery(self, source_name: str, config: Dict[str, Any], client_manager: BigQueryClientManager) -> int:
        table_path = f"{config['project']}.{config['dataset']}.{config['table']}"
        
        try:
            PrettyLogger.info(f"Analyzing {source_name} source: {table_path}")
            
            with client_manager.get_client() as client:
                try:
                    table_ref = client.get_table(table_path)
                    available_columns = [field.name for field in table_ref.schema]
                    PrettyLogger.success(f"Connected to {source_name}, found {len(available_columns)} columns")
                    
                    PrettyLogger.info(f"Available columns: {', '.join(available_columns[:10])}")
                    
                except Exception as e:
                    PrettyLogger.error(f"Cannot access table {table_path}: {e}")
                    return 0
                
                mapped_fields = self.column_matcher.smart_column_mapping(config['fields'], available_columns)
                
                if not mapped_fields or 'hostname' not in mapped_fields:
                    PrettyLogger.error(f"Cannot find hostname column in {source_name}")
                    
                    if 'field_variations' in config:
                        for hostname_variation in config['field_variations']['hostname']:
                            found_col = self.column_matcher.find_column_case_insensitive(hostname_variation, available_columns)
                            if found_col:
                                mapped_fields['hostname'] = found_col
                                PrettyLogger.column_detection(source_name, hostname_variation, found_col)
                                break
                    
                    if 'hostname' not in mapped_fields:
                        PrettyLogger.error(f"No hostname column found in {source_name} after trying all variations")
                        return 0
                
                for field_key, expected_field in config['fields'].items():
                    if field_key in mapped_fields:
                        if mapped_fields[field_key] != expected_field:
                            PrettyLogger.column_detection(source_name, expected_field, mapped_fields[field_key])
                
                hostname_field = mapped_fields['hostname']
                select_fields = [f"UPPER(TRIM(CAST(`{hostname_field}` AS STRING))) as hostname"]
                
                for field_key, actual_field in mapped_fields.items():
                    if field_key != 'hostname':
                        select_fields.append(f"CAST(`{actual_field}` AS STRING) as {field_key}")
                
                is_partitioned = table_ref.time_partitioning is not None
                date_filter = ""
                
                if is_partitioned and table_ref.time_partitioning.field:
                    partition_field = table_ref.time_partitioning.field
                    date_filter = f"WHERE `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
                
                discovery_query = f"""
                SELECT DISTINCT {', '.join(select_fields)}
                FROM `{table_path}`
                {date_filter}
                {" AND " if date_filter else "WHERE"} `{hostname_field}` IS NOT NULL
                    AND LENGTH(TRIM(CAST(`{hostname_field}` AS STRING))) >= 3
                    AND UPPER(TRIM(CAST(`{hostname_field}` AS STRING))) NOT LIKE '%@%'
                    AND UPPER(TRIM(CAST(`{hostname_field}` AS STRING))) NOT LIKE 'HTTP%'
                    AND UPPER(TRIM(CAST(`{hostname_field}` AS STRING))) NOT LIKE 'UNKNOWN%'
                    AND UPPER(TRIM(CAST(`{hostname_field}` AS STRING))) NOT LIKE 'NULL%'
                    AND UPPER(TRIM(CAST(`{hostname_field}` AS STRING))) NOT LIKE 'N/A%'
                    AND UPPER(TRIM(CAST(`{hostname_field}` AS STRING))) NOT LIKE 'NONE%'
                LIMIT 10000
                """
                
                PrettyLogger.info(f"Executing discovery query for {source_name}")
                
                try:
                    results = list(client_manager.execute_query_unlimited(discovery_query))
                except Exception as e:
                    PrettyLogger.warning(f"Query failed with cost limits, trying simplified query: {e}")
                    
                    simplified_query = f"""
                    SELECT DISTINCT UPPER(TRIM(CAST(`{hostname_field}` AS STRING))) as hostname
                    FROM `{table_path}`
                    {date_filter}
                    {" AND " if date_filter else "WHERE"} `{hostname_field}` IS NOT NULL
                        AND LENGTH(TRIM(CAST(`{hostname_field}` AS STRING))) >= 3
                    LIMIT 10000
                    """
                    
                    results = list(client_manager.execute_query_unlimited(simplified_query))
                
                if not results:
                    PrettyLogger.warning(f"No endpoints found in {source_name}")
                    return 0
                
                endpoints_processed = 0
                
                for row in results:
                    if row[0] and len(str(row[0]).strip()) >= 3:
                        asset_data = {
                            'hostname': str(row[0]).upper().strip(),
                            'source_system': source_name,
                            'source_type': config['source_type']
                        }
                        
                        field_mapping = list(mapped_fields.keys())[1:]
                        for i, field_key in enumerate(field_mapping, 1):
                            if i < len(row) and row[i]:
                                asset_data[field_key] = str(row[i])
                        
                        await self._intelligent_asset_merge(asset_data)
                        endpoints_processed += 1
                
                self.progress.update_stats(endpoints_discovered=endpoints_processed)
                return endpoints_processed
                
        except Exception as e:
            PrettyLogger.error(f"Discovery failed for {source_name}: {e}")
            return 0
    
    async def _intelligent_asset_merge(self, asset_data: Dict[str, Any]):
        hostname = asset_data['hostname']
        source_type = asset_data['source_type']
        
        existing = self.conn.execute("""
            SELECT source_systems, global_region, environment, system_classification, 
                   business_unit, found_in_cmdb, has_crowdstrike, in_splunk, in_chronicle
            FROM ao1_asset_inventory WHERE hostname = ?
        """, (hostname,)).fetchone()
        
        if existing:
            source_systems = existing[0] or ""
            if source_type not in source_systems:
                updated_sources = f"{source_systems},{source_type}" if source_systems else source_type
                
                update_fields = ["source_systems = ?"]
                update_values = [updated_sources]
                
                if source_type == 'cmdb':
                    update_fields.append("found_in_cmdb = TRUE")
                elif source_type == 'crowdstrike':
                    update_fields.append("has_crowdstrike = TRUE")
                elif source_type == 'splunk':
                    update_fields.append("in_splunk = TRUE")
                elif source_type == 'chronicle':
                    update_fields.append("in_chronicle = TRUE")
                
                for field, idx in [('region', 1), ('environment', 2), ('type', 3), ('business_unit', 4)]:
                    if field in asset_data and asset_data[field] and not existing[idx]:
                        db_field = {
                            'region': 'global_region',
                            'environment': 'environment', 
                            'type': 'system_classification',
                            'business_unit': 'business_unit'
                        }[field]
                        update_fields.append(f"{db_field} = ?")
                        update_values.append(asset_data[field])
                
                update_values.append(hostname)
                
                self.conn.execute(f"""
                    UPDATE ao1_asset_inventory 
                    SET {', '.join(update_fields)}, last_updated = CURRENT_TIMESTAMP
                    WHERE hostname = ?
                """, update_values)
        else:
            flags = {
                'found_in_cmdb': source_type == 'cmdb',
                'has_crowdstrike': source_type == 'crowdstrike',
                'in_splunk': source_type == 'splunk',
                'in_chronicle': source_type == 'chronicle'
            }
            
            self.conn.execute("""
                INSERT INTO ao1_asset_inventory (
                    hostname, source_systems, global_region, environment, system_classification,
                    business_unit, found_in_cmdb, has_crowdstrike, in_splunk, in_chronicle,
                    discovery_timestamp, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                hostname,
                source_type,
                asset_data.get('region', ''),
                asset_data.get('environment', ''),
                asset_data.get('type', ''),
                asset_data.get('business_unit', ''),
                flags['found_in_cmdb'],
                flags['has_crowdstrike'],
                flags['in_splunk'],
                flags['in_chronicle']
            ))
    
    async def _execute_comprehensive_discovery(self):
        PrettyLogger.info("Executing comprehensive dataset discovery")
        
        try:
            with self.client_manager.get_client() as client:
                all_datasets = list(client.list_datasets(project=self.project_id))
        except Exception as e:
            PrettyLogger.error(f"Failed to list datasets: {e}")
            return
            
        priority_datasets = ['SAS_BI', 'SECURITY', 'MONITORING', 'NETWORK', 'CMDB']
        filtered_datasets = [d for d in all_datasets 
                           if d.dataset_id not in self.processed_datasets 
                           and (d.dataset_id in priority_datasets or 'ENDPOINT' in d.dataset_id.upper())]
        
        self.progress.set_stats(datasets_total=len(filtered_datasets))
        PrettyLogger.info(f"Analyzing {len(filtered_datasets)} priority datasets for AO1")
        
        for i, dataset in enumerate(filtered_datasets):
            if self.signal_handler.shutdown_requested:
                break
            
            try:
                await self._process_dataset_intelligently(dataset.dataset_id)
                self.progress.update_stats(datasets_processed=1)
                
                if self.progress.should_checkpoint():
                    await self._save_checkpoint()
                    
            except Exception as e:
                PrettyLogger.error(f"Dataset processing failed {dataset.dataset_id}: {e}")
                self.progress.update_stats(datasets_failed=1)
                await asyncio.sleep(2)
    
    async def _process_dataset_intelligently(self, dataset_id: str):
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            with self.client_manager.get_client() as client:
                dataset_ref = client.dataset(dataset_id, project=self.project_id)
                
                try:
                    tables = list(client.list_tables(dataset_ref))
                except Exception as e:
                    PrettyLogger.warning(f"Cannot list tables in {dataset_id}: {e}")
                    return
                
                endpoint_tables = [t for t in tables 
                                 if any(keyword in t.table_id.upper() 
                                       for keyword in ['ENDPOINT', 'HOST', 'ASSET', 'DEVICE', 'SERVER'])]
                
                if endpoint_tables:
                    PrettyLogger.info(f"Found {len(endpoint_tables)} potential endpoint tables in {dataset_id}")
                
                for table_ref in endpoint_tables[:5]:
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    table_path = f"{self.project_id}.{dataset_id}.{table_ref.table_id}"
                    
                    if table_path in self.processed_tables:
                        continue
                    
                    try:
                        endpoints_found = await self._analyze_table_for_endpoints(table_path)
                        if endpoints_found > 0:
                            PrettyLogger.visibility_analysis(f"Found {endpoints_found} endpoints in {table_ref.table_id}")
                        
                        with self._processing_lock:
                            self.processed_tables.add(table_path)
                        self.progress.update_stats(tables_processed=1)
                        
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        PrettyLogger.error(f"Table analysis failed {table_path}: {str(e)[:100]}")
                        self.progress.update_stats(tables_failed=1)
                
                with self._processing_lock:
                    self.processed_datasets.add(dataset_id)
                        
        except Exception as e:
            PrettyLogger.error(f"Dataset processing failed {dataset_id}: {e}")
    
    async def _analyze_table_for_endpoints(self, table_path: str) -> int:
        try:
            await asyncio.sleep(random.uniform(0.3, 1.0))
            
            with self.client_manager.get_client() as client:
                try:
                    table_ref = client.get_table(table_path)
                except Exception:
                    return 0
                
                string_fields = [field for field in table_ref.schema 
                               if field.field_type == 'STRING' 
                               and any(keyword in field.name.lower() 
                                     for keyword in ['host', 'endpoint', 'server', 'device', 'asset'])]
                
                endpoints_found = 0
                
                for field in string_fields[:2]:
                    try:
                        sample_query = f"""
                        SELECT DISTINCT UPPER(TRIM(CAST(`{field.name}` AS STRING))) as hostname
                        FROM `{table_path}`
                        WHERE `{field.name}` IS NOT NULL
                            AND LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 3
                            AND `{field.name}` NOT LIKE '%@%'
                            AND `{field.name}` NOT LIKE 'http%'
                        LIMIT 1000
                        """
                        
                        job = client.query(sample_query, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=None))
                        results = list(job.result())
                        
                        for row in results:
                            if row[0] and len(str(row[0]).strip()) >= 3:
                                await self._intelligent_asset_merge({
                                    'hostname': str(row[0]).upper().strip(),
                                    'source_system': table_path.split('.')[-1],
                                    'source_type': 'discovery'
                                })
                                endpoints_found += 1
                        
                        await asyncio.sleep(0.3)
                    
                    except Exception:
                        continue
                
                return endpoints_found
                
        except Exception:
            return 0
    
    async def _calculate_ao1_visibility_metrics(self):
        PrettyLogger.info("Calculating brilliant AO1 visibility metrics")
        
        try:
            total_assets_result = self.conn.execute("SELECT COUNT(*) FROM ao1_asset_inventory").fetchone()
            total_assets = total_assets_result[0] if total_assets_result else 0
            
            if total_assets == 0:
                PrettyLogger.warning("No assets found for AO1 calculation")
                return
            
            metrics_query = """
            SELECT 
                COUNT(*) as total_assets,
                SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) as logging_coverage,
                SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN in_splunk AND in_chronicle AND has_crowdstrike AND found_in_cmdb THEN 1 ELSE 0 END) as full_coverage
            FROM ao1_asset_inventory
            """
            
            result = self.conn.execute(metrics_query).fetchone()
            
            if result:
                total = result[0]
                
                metrics = {
                    ('global_view', 'total_asset_visibility'): (result[3] / total * 100, 95.0),
                    ('global_view', 'splunk_coverage'): (result[1] / total * 100, 85.0),
                    ('global_view', 'chronicle_coverage'): (result[2] / total * 100, 80.0),
                    ('security_coverage', 'crowdstrike_coverage'): (result[4] / total * 100, 90.0),
                    ('data_quality', 'cmdb_coverage'): (result[5] / total * 100, 95.0),
                    ('comprehensive', 'full_visibility'): (result[6] / total * 100, 75.0)
                }
                
                for (category, metric_name), (value, target) in metrics.items():
                    gap = max(0, target - value)
                    priority = 1 if gap > 20 else 2 if gap > 10 else 3
                    
                    self.conn.execute("""
                        INSERT OR REPLACE INTO ao1_visibility_metrics 
                        (metric_category, metric_name, metric_value, metric_target, gap_percentage, improvement_priority, last_calculated)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (category, metric_name, value, target, gap, priority))
                    
                    PrettyLogger.ao1_metric(f"{category}/{metric_name}", f"{value:.1f}% (target: {target}%)")
            
            PrettyLogger.success("AO1 visibility metrics calculated successfully")
            
        except Exception as e:
            PrettyLogger.error(f"Failed to calculate AO1 metrics: {e}")
    
    async def _perform_gap_analysis(self):
        PrettyLogger.info("Performing intelligent gap analysis")
        
        gap_analyses = [
            {
                'id': 'no_logging_coverage',
                'query': "SELECT COUNT(*) FROM ao1_asset_inventory WHERE NOT in_splunk AND NOT in_chronicle",
                'category': 'Logging Coverage',
                'description': 'Assets with no logging platform coverage',
                'severity': 'Critical'
            },
            {
                'id': 'missing_security_tools',
                'query': "SELECT COUNT(*) FROM ao1_asset_inventory WHERE NOT has_crowdstrike",
                'category': 'Security Coverage', 
                'description': 'Assets without security agent coverage',
                'severity': 'High'
            },
            {
                'id': 'cmdb_gaps',
                'query': "SELECT COUNT(*) FROM ao1_asset_inventory WHERE NOT found_in_cmdb",
                'category': 'Data Quality',
                'description': 'Assets not found in CMDB',
                'severity': 'Medium'
            },
            {
                'id': 'single_source_risk',
                'query': "SELECT COUNT(*) FROM ao1_asset_inventory WHERE (CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) + (CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) + (CASE WHEN in_splunk THEN 1 ELSE 0 END) + (CASE WHEN in_chronicle THEN 1 ELSE 0 END) = 1",
                'category': 'Data Reliability',
                'description': 'Assets found in only one source system',
                'severity': 'Medium'
            }
        ]
        
        for gap in gap_analyses:
            try:
                result = self.conn.execute(gap['query']).fetchone()
                count = result[0] if result else 0
                
                if count > 0:
                    self.conn.execute("""
                        INSERT OR REPLACE INTO ao1_gap_analysis 
                        (gap_id, gap_category, gap_description, affected_asset_count, severity_level, identified_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (gap['id'], gap['category'], gap['description'], count, gap['severity']))
                    
                    PrettyLogger.gap_identification(gap['description'], count)
                
            except Exception as e:
                PrettyLogger.error(f"Gap analysis failed for {gap['id']}: {e}")
    
    async def _generate_compliance_insights(self):
        PrettyLogger.info("Generating AO1 compliance insights")
        
        try:
            compliance_query = """
            SELECT 
                hostname,
                CASE 
                    WHEN in_splunk AND in_chronicle THEN 'Full Compliance'
                    WHEN in_splunk OR in_chronicle THEN 'Partial Compliance'
                    ELSE 'Non-Compliant'
                END as compliance_status,
                CASE 
                    WHEN in_splunk AND in_chronicle THEN 100.0
                    WHEN in_splunk OR in_chronicle THEN 50.0
                    ELSE 0.0
                END as coverage_percentage
            FROM ao1_asset_inventory
            """
            
            results = self.conn.execute(compliance_query).fetchall()
            
            for row in results:
                hostname, status, coverage = row
                
                gaps = []
                if not self.conn.execute("SELECT in_splunk FROM ao1_asset_inventory WHERE hostname = ?", (hostname,)).fetchone()[0]:
                    gaps.append("Missing Splunk coverage")
                if not self.conn.execute("SELECT in_chronicle FROM ao1_asset_inventory WHERE hostname = ?", (hostname,)).fetchone()[0]:
                    gaps.append("Missing Chronicle coverage")
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO ao1_logging_compliance 
                    (hostname, logging_platform, compliance_status, coverage_percentage, gaps_identified, compliance_date)
                    VALUES (?, 'AO1_COMBINED', ?, ?, ?, CURRENT_TIMESTAMP)
                """, (hostname, status, coverage, '; '.join(gaps)))
            
            PrettyLogger.success("AO1 compliance analysis completed")
            
        except Exception as e:
            PrettyLogger.error(f"Compliance insight generation failed: {e}")
    
    async def _resume_from_checkpoint(self, checkpoint: Dict[str, Any]):
        self.processed_datasets = set(checkpoint.get('processed_datasets', []))
        self.processed_tables = set(checkpoint.get('processed_tables', []))
        
        self.progress.set_stats(
            datasets_processed=len(self.processed_datasets),
            tables_processed=len(self.processed_tables),
            endpoints_discovered=checkpoint.get('endpoints_discovered', 0)
        )
    
    async def _save_checkpoint(self):
        stats = self.progress.get_stats()
        checkpoint_data = {
            'processed_datasets': list(self.processed_datasets),
            'processed_tables': list(self.processed_tables),
            'endpoints_discovered': stats.endpoints_discovered,
            'datasets_processed': stats.datasets_processed,
            'tables_processed': stats.tables_processed
        }
        self.checkpoint_manager.save_checkpoint(checkpoint_data)
    
    async def _save_emergency_checkpoint(self):
        await self._save_checkpoint()
    
    def _count_total_assets(self) -> int:
        try:
            result = self.conn.execute("SELECT COUNT(*) FROM ao1_asset_inventory").fetchone()
            return result[0] if result else 0
        except Exception:
            return 0
    
    def _get_ao1_metrics(self) -> Dict[str, Any]:
        try:
            result = self.conn.execute("""
                SELECT metric_category, metric_name, metric_value, metric_target, gap_percentage
                FROM ao1_visibility_metrics ORDER BY improvement_priority
            """).fetchall()
            
            return {f"{row[0]}_{row[1]}": {
                'value': row[2], 'target': row[3], 'gap': row[4]
            } for row in result} if result else {}
        except Exception:
            return {}
    
    def _get_gap_analysis(self) -> Dict[str, Any]:
        try:
            result = self.conn.execute("""
                SELECT gap_category, gap_description, affected_asset_count, severity_level
                FROM ao1_gap_analysis ORDER BY affected_asset_count DESC
            """).fetchall()
            
            return {row[0]: {
                'description': row[1], 'count': row[2], 'severity': row[3]
            } for row in result} if result else {}
        except Exception:
            return {}
    
    def _get_compliance_status(self) -> Dict[str, Any]:
        try:
            result = self.conn.execute("""
                SELECT compliance_status, COUNT(*) as count
                FROM ao1_logging_compliance 
                GROUP BY compliance_status
            """).fetchall()
            
            return {row[0]: row[1] for row in result} if result else {}
        except Exception:
            return {}
    
    def _generate_ao1_recommendations(self) -> List[str]:
        recommendations = []
        
        try:
            gaps = self._get_gap_analysis()
            metrics = self._get_ao1_metrics()
            
            for gap_category, gap_info in gaps.items():
                if gap_info['count'] > 0:
                    if gap_info['severity'] == 'Critical':
                        recommendations.append(f"URGENT: Address {gap_info['description']} affecting {gap_info['count']} assets")
                    else:
                        recommendations.append(f"Improve {gap_info['description']} for {gap_info['count']} assets")
            
            for metric_name, metric_data in metrics.items():
                if metric_data['gap'] > 15:
                    recommendations.append(f"Focus on improving {metric_name} - currently {metric_data['gap']:.1f}% below target")
            
        except Exception:
            recommendations.append("Review AO1 database for detailed recommendations")
        
        return recommendations[:10]
    
    def _create_ao1_analysis_queries(self) -> Dict[str, str]:
        return {
            'ao1_global_visibility_dashboard': """
            SELECT 
                COUNT(*) as total_assets,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as global_visibility_percentage,
                (SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as splunk_coverage_percentage,
                (SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as chronicle_coverage_percentage,
                (SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as security_coverage_percentage,
                (SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as cmdb_coverage_percentage
            FROM ao1_asset_inventory;
            """,
            
            'ao1_infrastructure_type_analysis': """
            SELECT 
                COALESCE(infrastructure_type, 'On-Prem') as infrastructure_category,
                COUNT(*) as asset_count,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as logging_visibility_pct,
                (SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as security_coverage_pct
            FROM ao1_asset_inventory
            GROUP BY infrastructure_type
            ORDER BY logging_visibility_pct DESC;
            """,
            
            'ao1_regional_visibility_breakdown': """
            SELECT 
                COALESCE(global_region, 'Unknown Region') as region,
                COUNT(*) as total_assets,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as visibility_percentage,
                SUM(CASE WHEN NOT in_splunk AND NOT in_chronicle THEN 1 ELSE 0 END) as visibility_gaps
            FROM ao1_asset_inventory
            GROUP BY global_region
            ORDER BY visibility_percentage DESC;
            """,
            
            'ao1_business_unit_application_view': """
            SELECT 
                COALESCE(business_unit, 'Unknown BU') as business_unit,
                COUNT(*) as asset_count,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as logging_coverage,
                (SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as security_coverage
            FROM ao1_asset_inventory
            GROUP BY business_unit
            ORDER BY asset_count DESC;
            """,
            
            'ao1_system_classification_analysis': """
            SELECT 
                COALESCE(system_classification, 'Unknown System') as system_type,
                COUNT(*) as asset_count,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as visibility_pct,
                (SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as agent_coverage_pct
            FROM ao1_asset_inventory
            GROUP BY system_classification
            ORDER BY visibility_pct DESC;
            """,
            
            'ao1_critical_visibility_gaps': """
            SELECT 
                hostname,
                global_region,
                business_unit,
                system_classification,
                CASE 
                    WHEN NOT in_splunk AND NOT in_chronicle AND NOT found_in_cmdb THEN 'Critical - No Coverage'
                    WHEN NOT in_splunk AND NOT in_chronicle THEN 'High - No Logging'
                    WHEN NOT has_crowdstrike THEN 'Medium - No Security Agent'
                    WHEN NOT found_in_cmdb THEN 'Low - Missing CMDB'
                    ELSE 'Good Coverage'
                END as gap_severity,
                source_systems
            FROM ao1_asset_inventory
            WHERE NOT (in_splunk AND in_chronicle AND has_crowdstrike AND found_in_cmdb)
            ORDER BY 
                CASE 
                    WHEN NOT in_splunk AND NOT in_chronicle AND NOT found_in_cmdb THEN 1
                    WHEN NOT in_splunk AND NOT in_chronicle THEN 2
                    WHEN NOT has_crowdstrike THEN 3
                    WHEN NOT found_in_cmdb THEN 4
                    ELSE 5
                END;
            """,
            
            'ao1_logging_compliance_status': """
            SELECT 
                compliance_status,
                COUNT(*) as asset_count,
                (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ao1_logging_compliance)) as percentage,
                AVG(coverage_percentage) as avg_coverage
            FROM ao1_logging_compliance
            GROUP BY compliance_status
            ORDER BY asset_count DESC;
            """,
            
            'ao1_domain_visibility_analysis': """
            SELECT 
                domain_name,
                asset_count,
                covered_assets,
                visibility_percentage,
                missing_coverage,
                domain_classification
            FROM ao1_domain_visibility
            WHERE asset_count > 5
            ORDER BY visibility_percentage ASC, missing_coverage DESC;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()