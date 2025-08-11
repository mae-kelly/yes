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
import re

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
    def column_detection(table_name: str, found_columns: List[str]):
        print(f"   ･ﾟ✧ ◞ ♡   {table_name}: Extracting {len(found_columns)} columns")
    
    @staticmethod
    def data_extraction(source: str, endpoints: int, fields: int):
        print(f"   ♡˗ˏˋ ◞ ～   {source}: {endpoints:,} endpoints × {fields} fields = {endpoints * fields:,} data points")
    
    @staticmethod
    def critical_discovery(source: str, count: int):
        print(f"   ♡₊˚ 🌸 ⋆｡˚   {source} Complete: {count:,} endpoints with full data")

class IntelligentDataExtractor:
    @staticmethod
    def find_all_relevant_columns(available_columns: List[str]) -> Dict[str, List[str]]:
        field_patterns = {
            'hostname': ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system'],
            'fqdn': ['fqdn', 'dns', 'domain', 'qualified', 'full'],
            'ip_address': ['ip', 'address', 'addr'],
            'infrastructure_type': ['infrastructure', 'infra', 'type', 'category', 'class', 'tier'],
            'system_classification': ['classification', 'class', 'type', 'category', 'os', 'operating'],
            'region': ['region', 'geo', 'location', 'site', 'area', 'zone'],
            'country': ['country', 'nation', 'ctry'],
            'data_center': ['datacenter', 'center', 'dc', 'facility'],
            'cloud_region': ['cloud', 'aws', 'azure', 'gcp'],
            'business_unit': ['business', 'unit', 'bu', 'org', 'organization'],
            'environment': ['env', 'environment', 'stage', 'tier', 'level'],
            'agent_type': ['agent', 'tool', 'software'],
            'status': ['status', 'state', 'active', 'enabled'],
            'version': ['version', 'ver', 'release'],
            'last_seen': ['last', 'seen', 'updated', 'modified'],
            'created': ['created', 'added', 'installed'],
            'owner': ['owner', 'responsible', 'contact'],
            'cost_center': ['cost', 'billing', 'charge'],
            'application': ['app', 'application', 'service'],
            'criticality': ['critical', 'priority', 'importance'],
            'compliance': ['compliance', 'regulation', 'policy'],
            'network': ['network', 'subnet', 'vlan'],
            'security': ['security', 'encryption', 'cert'],
            'performance': ['cpu', 'memory', 'disk', 'performance'],
            'configuration': ['config', 'setting', 'parameter']
        }
        
        matched_columns = {}
        for field_type, patterns in field_patterns.items():
            matches = []
            for column in available_columns:
                column_lower = column.lower()
                for pattern in patterns:
                    if pattern in column_lower:
                        matches.append(column)
                        break
            if matches:
                matched_columns[field_type] = matches
        
        return matched_columns
    
    @staticmethod
    def extract_ip_addresses(text: str) -> List[str]:
        if not text:
            return []
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        return list(set(re.findall(ip_pattern, str(text))))
    
    @staticmethod
    def normalize_hostname(hostname: str) -> str:
        if not hostname:
            return ""
        hostname = str(hostname).strip().upper()
        if len(hostname) < 3:
            return ""
        invalid_patterns = ['@', 'HTTP', 'UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 'TEST', 'EXAMPLE']
        if any(pattern in hostname for pattern in invalid_patterns):
            return ""
        return hostname
    
    @staticmethod
    def infer_infrastructure_type(data: Dict[str, Any]) -> str:
        hostname = data.get('hostname', '').upper()
        region = data.get('region', '').upper()
        
        cloud_indicators = ['AWS', 'AZURE', 'GCP', 'CLOUD', 'EC2', 'INSTANCE']
        if any(indicator in hostname or indicator in region for indicator in cloud_indicators):
            return 'Cloud'
        
        saas_indicators = ['SAAS', 'SERVICE', 'ONLINE', 'WEB']
        if any(indicator in hostname for indicator in saas_indicators):
            return 'SaaS'
        
        api_indicators = ['API', 'REST', 'ENDPOINT', 'SERVICE']
        if any(indicator in hostname for indicator in api_indicators):
            return 'API'
        
        return 'On-Prem'

class AO1IntelligentDiscovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Complete Data Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*90)
        PrettyLogger.info("Initializing brilliant comprehensive data extraction")
        
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
        
        PrettyLogger.success("Connected to all data sources - building complete AO1 CMDB")
        
        self.matcher = ContentBasedMatcher()
        self.cache = CacheManager(self.config.get('cache_dir', '.cache'))
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        self.data_extractor = IntelligentDataExtractor()
        
        self.db_path = self.config.get('database_path', 'ao1_visibility_cmdb.db')
        self.max_workers = min(2, self.config.get('max_workers', 2))
        
        self.ao1_critical_sources = {
            'cmdb_master': {
                'project': project_id,
                'dataset': 'SAS_BI',
                'table': 'V_DIM_ENDPOINT',
                'source_type': 'cmdb',
                'priority': 100
            },
            'security_agents': {
                'project': project_id,
                'dataset': 'SAS_BI',
                'table': 'V_DIM_ENDPOINTAGENT',
                'source_type': 'crowdstrike',
                'priority': 95
            },
            'splunk_logs': {
                'project': project_id,
                'dataset': 'SAS_BI',
                'table': 'V_SPL_ENDPOINT_LOG',
                'source_type': 'splunk',
                'priority': 90
            },
            'chronicle_events': {
                'project': 'chronicle-fisv',
                'dataset': 'datalake',
                'table': 'events',
                'source_type': 'chronicle',
                'priority': 85
            }
        }
        
        self.processed_datasets = set()
        self.processed_tables = set()
        self._processing_lock = threading.Lock()
        
        self._setup_comprehensive_database()
    
    def _setup_comprehensive_database(self):
        self.conn = duckdb.connect(self.db_path)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_asset_inventory (
            hostname VARCHAR PRIMARY KEY,
            fqdn VARCHAR,
            ip_addresses TEXT,
            
            infrastructure_type VARCHAR,
            system_classification VARCHAR,
            operating_system VARCHAR,
            global_region VARCHAR,
            country VARCHAR,
            data_center VARCHAR,
            cloud_region VARCHAR,
            business_unit VARCHAR,
            cio VARCHAR,
            apm VARCHAR,
            application_class VARCHAR,
            environment VARCHAR,
            cost_center VARCHAR,
            owner VARCHAR,
            criticality VARCHAR,
            
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
            agent_version VARCHAR,
            agent_status VARCHAR,
            last_agent_checkin TIMESTAMP,
            
            found_in_cmdb BOOLEAN DEFAULT FALSE,
            cmdb_last_updated TIMESTAMP,
            source_systems TEXT,
            data_completeness_score DOUBLE DEFAULT 0.0,
            
            network_info TEXT,
            security_info TEXT,
            compliance_status VARCHAR,
            performance_data TEXT,
            configuration_data TEXT,
            
            ao1_visibility_score DOUBLE DEFAULT 0.0,
            ao1_gap_severity VARCHAR DEFAULT 'Unknown',
            ao1_recommendation TEXT,
            
            discovery_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW(),
            raw_data TEXT
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
        CREATE TABLE IF NOT EXISTS ao1_data_completeness (
            hostname VARCHAR,
            field_name VARCHAR,
            field_value TEXT,
            data_source VARCHAR,
            confidence_score DOUBLE,
            last_updated TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (hostname, field_name, data_source)
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_source_coverage (
            table_name VARCHAR PRIMARY KEY,
            total_records BIGINT,
            processed_records BIGINT,
            unique_hostnames BIGINT,
            data_fields_extracted INTEGER,
            processing_time_seconds DOUBLE,
            coverage_percentage DOUBLE,
            last_processed TIMESTAMP DEFAULT NOW()
        )
        """)
    
    async def execute_ao1_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Executing comprehensive AO1 data discovery")
        
        try:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            if checkpoint:
                PrettyLogger.info("Resuming from checkpoint")
                await self._resume_from_checkpoint(checkpoint)
            
            await self._discover_all_critical_sources()
            await self._execute_comprehensive_discovery()
            await self._calculate_data_completeness()
            await self._calculate_ao1_metrics()
            await self._perform_gap_analysis()
            
            stats = self.progress.get_stats()
            queries = self._create_analysis_queries()
            
            final_results = {
                'processing_time': time.time() - start_time,
                'database_path': self.db_path,
                'total_assets_discovered': self._count_total_assets(),
                'data_completeness': self._get_data_completeness(),
                'source_coverage': self._get_source_coverage(),
                'ao1_visibility_metrics': self._get_ao1_metrics(),
                'performance_stats': asdict(stats)
            }
            
            self.checkpoint_manager.clear_checkpoint()
            PrettyLogger.success("AO1 comprehensive discovery completed")
            
            return final_results, queries
            
        except Exception as e:
            PrettyLogger.error(f"AO1 discovery failed: {e}")
            await self._save_emergency_checkpoint()
            raise
        finally:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
    
    async def _discover_all_critical_sources(self):
        PrettyLogger.info("Discovering all critical sources with complete data extraction")
        
        for source_name, source_config in self.ao1_critical_sources.items():
            try:
                await asyncio.sleep(random.uniform(0.2, 0.8))
                
                client_manager = self.chronicle_client_manager if source_config['project'] == 'chronicle-fisv' else self.client_manager
                
                if client_manager is None:
                    PrettyLogger.warning(f"Skipping {source_name} - client unavailable")
                    continue
                
                endpoints_discovered = await self._comprehensive_source_discovery(source_name, source_config, client_manager)
                PrettyLogger.critical_discovery(source_name, endpoints_discovered)
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                PrettyLogger.error(f"Failed to discover {source_name}: {e}")
                await asyncio.sleep(2)
    
    async def _comprehensive_source_discovery(self, source_name: str, config: Dict[str, Any], client_manager: BigQueryClientManager) -> int:
        table_path = f"{config['project']}.{config['dataset']}.{config['table']}"
        
        try:
            PrettyLogger.info(f"Comprehensive analysis of {source_name}: {table_path}")
            
            with client_manager.get_client() as client:
                try:
                    table_ref = client.get_table(table_path)
                    all_columns = [field.name for field in table_ref.schema]
                    PrettyLogger.success(f"Connected to {source_name}, analyzing {len(all_columns)} columns")
                    
                except Exception as e:
                    PrettyLogger.error(f"Cannot access table {table_path}: {e}")
                    return 0
                
                relevant_columns = self.data_extractor.find_all_relevant_columns(all_columns)
                PrettyLogger.column_detection(source_name, [col for cols in relevant_columns.values() for col in cols])
                
                hostname_candidates = relevant_columns.get('hostname', [])
                if not hostname_candidates:
                    PrettyLogger.error(f"No hostname columns found in {source_name}")
                    return 0
                
                primary_hostname_col = hostname_candidates[0]
                
                select_fields = [f"UPPER(TRIM(CAST(`{primary_hostname_col}` AS STRING))) as hostname"]
                field_mappings = {'hostname': primary_hostname_col}
                
                for field_type, columns in relevant_columns.items():
                    if field_type != 'hostname' and columns:
                        col = columns[0]
                        select_fields.append(f"CAST(`{col}` AS STRING) as {field_type}")
                        field_mappings[field_type] = col
                
                is_partitioned = table_ref.time_partitioning is not None
                partition_filter = ""
                
                if is_partitioned and table_ref.time_partitioning.field:
                    partition_field = table_ref.time_partitioning.field
                    partition_filter = f"WHERE `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)"
                
                comprehensive_query = f"""
                SELECT {', '.join(select_fields)}
                FROM `{table_path}`
                {partition_filter}
                {" AND " if partition_filter else "WHERE"} `{primary_hostname_col}` IS NOT NULL
                    AND LENGTH(TRIM(CAST(`{primary_hostname_col}` AS STRING))) >= 3
                """
                
                PrettyLogger.info(f"Executing comprehensive data extraction for {source_name}")
                
                with client_manager.get_client() as client:
                    job = client.query(comprehensive_query)
                    results = list(job.result())
                
                if not results:
                    PrettyLogger.warning(f"No data found in {source_name}")
                    return 0
                
                endpoints_processed = 0
                total_data_points = 0
                
                for row in results:
                    hostname = self.data_extractor.normalize_hostname(row[0])
                    if not hostname:
                        continue
                    
                    asset_data = {'hostname': hostname, 'source_type': config['source_type']}
                    
                    for i, (field_type, _) in enumerate(field_mappings.items()):
                        if i > 0 and i < len(row) and row[i]:
                            value = str(row[i]).strip()
                            if value and value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE']:
                                asset_data[field_type] = value
                                total_data_points += 1
                    
                    if 'ip_address' in asset_data:
                        ips = self.data_extractor.extract_ip_addresses(asset_data['ip_address'])
                        if ips:
                            asset_data['ip_addresses'] = ','.join(ips)
                    
                    if 'infrastructure_type' not in asset_data:
                        asset_data['infrastructure_type'] = self.data_extractor.infer_infrastructure_type(asset_data)
                    
                    await self._comprehensive_asset_merge(asset_data)
                    endpoints_processed += 1
                
                await self._record_source_coverage(table_path, len(results), endpoints_processed, len(field_mappings))
                
                PrettyLogger.data_extraction(source_name, endpoints_processed, len(field_mappings))
                self.progress.update_stats(endpoints_discovered=endpoints_processed)
                
                return endpoints_processed
                
        except Exception as e:
            PrettyLogger.error(f"Comprehensive discovery failed for {source_name}: {e}")
            return 0
    
    async def _comprehensive_asset_merge(self, asset_data: Dict[str, Any]):
        hostname = asset_data['hostname']
        source_type = asset_data['source_type']
        
        existing = self.conn.execute("""
            SELECT source_systems, raw_data FROM ao1_asset_inventory WHERE hostname = ?
        """, (hostname,)).fetchone()
        
        if existing:
            existing_sources = existing[0] or ""
            if source_type not in existing_sources:
                updated_sources = f"{existing_sources},{source_type}" if existing_sources else source_type
                
                update_fields = ["source_systems = ?"]
                update_values = [updated_sources]
                
                source_flags = {
                    'cmdb': 'found_in_cmdb = TRUE',
                    'crowdstrike': 'has_crowdstrike = TRUE',
                    'splunk': 'in_splunk = TRUE',
                    'chronicle': 'in_chronicle = TRUE'
                }
                
                if source_type in source_flags:
                    update_fields.append(source_flags[source_type])
                
                field_mappings = {
                    'fqdn': 'fqdn',
                    'ip_addresses': 'ip_addresses',
                    'infrastructure_type': 'infrastructure_type',
                    'system_classification': 'system_classification',
                    'operating_system': 'operating_system',
                    'region': 'global_region',
                    'country': 'country',
                    'data_center': 'data_center',
                    'cloud_region': 'cloud_region',
                    'business_unit': 'business_unit',
                    'environment': 'environment',
                    'cost_center': 'cost_center',
                    'owner': 'owner',
                    'criticality': 'criticality',
                    'agent_type': 'agent_version',
                    'status': 'agent_status'
                }
                
                for asset_field, db_field in field_mappings.items():
                    if asset_field in asset_data and asset_data[asset_field]:
                        update_fields.append(f"{db_field} = ?")
                        update_values.append(asset_data[asset_field])
                
                update_fields.append("raw_data = ?")
                update_values.append(json.dumps(asset_data))
                
                update_values.append(hostname)
                
                self.conn.execute(f"""
                    UPDATE ao1_asset_inventory 
                    SET {', '.join(update_fields)}, last_updated = CURRENT_TIMESTAMP
                    WHERE hostname = ?
                """, update_values)
                
                for field_name, field_value in asset_data.items():
                    if field_name not in ['hostname', 'source_type'] and field_value:
                        self.conn.execute("""
                            INSERT OR REPLACE INTO ao1_data_completeness 
                            (hostname, field_name, field_value, data_source, confidence_score)
                            VALUES (?, ?, ?, ?, ?)
                        """, (hostname, field_name, str(field_value), source_type, 1.0))
        else:
            flags = {
                'found_in_cmdb': source_type == 'cmdb',
                'has_crowdstrike': source_type == 'crowdstrike',
                'in_splunk': source_type == 'splunk',
                'in_chronicle': source_type == 'chronicle'
            }
            
            self.conn.execute("""
                INSERT INTO ao1_asset_inventory (
                    hostname, fqdn, ip_addresses, infrastructure_type, system_classification, 
                    operating_system, global_region, country, data_center, cloud_region,
                    business_unit, environment, cost_center, owner, criticality,
                    found_in_cmdb, has_crowdstrike, in_splunk, in_chronicle,
                    source_systems, raw_data, discovery_timestamp, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                hostname,
                asset_data.get('fqdn', ''),
                asset_data.get('ip_addresses', ''),
                asset_data.get('infrastructure_type', ''),
                asset_data.get('system_classification', ''),
                asset_data.get('operating_system', ''),
                asset_data.get('region', ''),
                asset_data.get('country', ''),
                asset_data.get('data_center', ''),
                asset_data.get('cloud_region', ''),
                asset_data.get('business_unit', ''),
                asset_data.get('environment', ''),
                asset_data.get('cost_center', ''),
                asset_data.get('owner', ''),
                asset_data.get('criticality', ''),
                flags['found_in_cmdb'],
                flags['has_crowdstrike'],
                flags['in_splunk'],
                flags['in_chronicle'],
                source_type,
                json.dumps(asset_data)
            ))
            
            for field_name, field_value in asset_data.items():
                if field_name not in ['hostname', 'source_type'] and field_value:
                    self.conn.execute("""
                        INSERT INTO ao1_data_completeness 
                        (hostname, field_name, field_value, data_source, confidence_score)
                        VALUES (?, ?, ?, ?, ?)
                    """, (hostname, field_name, str(field_value), source_type, 1.0))
    
    async def _record_source_coverage(self, table_name: str, total_records: int, processed_records: int, fields_extracted: int):
        coverage_pct = (processed_records / total_records * 100) if total_records > 0 else 0
        
        unique_hostnames = self.conn.execute("""
            SELECT COUNT(DISTINCT hostname) FROM ao1_asset_inventory 
            WHERE source_systems LIKE ?
        """, (f"%{table_name.split('.')[-1].lower()}%",)).fetchone()[0]
        
        self.conn.execute("""
            INSERT OR REPLACE INTO ao1_source_coverage 
            (table_name, total_records, processed_records, unique_hostnames, data_fields_extracted, coverage_percentage)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (table_name, total_records, processed_records, unique_hostnames, fields_extracted, coverage_pct))
    
    async def _execute_comprehensive_discovery(self):
        PrettyLogger.info("Executing comprehensive dataset discovery")
        
        try:
            with self.client_manager.get_client() as client:
                all_datasets = list(client.list_datasets(project=self.project_id))
        except Exception as e:
            PrettyLogger.error(f"Failed to list datasets: {e}")
            return
            
        priority_datasets = ['SAS_BI', 'SECURITY', 'MONITORING', 'NETWORK', 'CMDB', 'INFRASTRUCTURE']
        filtered_datasets = [d for d in all_datasets 
                           if d.dataset_id not in self.processed_datasets 
                           and (d.dataset_id in priority_datasets or any(keyword in d.dataset_id.upper() 
                               for keyword in ['ENDPOINT', 'HOST', 'ASSET', 'DEVICE', 'SERVER']))]
        
        self.progress.set_stats(datasets_total=len(filtered_datasets))
        PrettyLogger.info(f"Analyzing {len(filtered_datasets)} datasets for comprehensive discovery")
        
        for i, dataset in enumerate(filtered_datasets):
            if self.signal_handler.shutdown_requested:
                break
            
            try:
                await self._process_dataset_comprehensively(dataset.dataset_id)
                self.progress.update_stats(datasets_processed=1)
                
                if self.progress.should_checkpoint():
                    await self._save_checkpoint()
                    
            except Exception as e:
                PrettyLogger.error(f"Dataset processing failed {dataset.dataset_id}: {e}")
                self.progress.update_stats(datasets_failed=1)
                await asyncio.sleep(1)
    
    async def _process_dataset_comprehensively(self, dataset_id: str):
        try:
            await asyncio.sleep(random.uniform(0.2, 0.8))
            
            with self.client_manager.get_client() as client:
                dataset_ref = client.dataset(dataset_id, project=self.project_id)
                
                try:
                    tables = list(client.list_tables(dataset_ref))
                except Exception as e:
                    PrettyLogger.warning(f"Cannot list tables in {dataset_id}: {e}")
                    return
                
                relevant_tables = [t for t in tables 
                                 if any(keyword in t.table_id.upper() 
                                       for keyword in ['ENDPOINT', 'HOST', 'ASSET', 'DEVICE', 'SERVER', 'COMPUTER', 'MACHINE'])]
                
                if relevant_tables:
                    PrettyLogger.info(f"Found {len(relevant_tables)} relevant tables in {dataset_id}")
                
                for table_ref in relevant_tables:
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    table_path = f"{self.project_id}.{dataset_id}.{table_ref.table_id}"
                    
                    if table_path in self.processed_tables:
                        continue
                    
                    try:
                        endpoints_found = await self._comprehensive_table_analysis(table_path)
                        if endpoints_found > 0:
                            PrettyLogger.success(f"Extracted {endpoints_found} endpoints from {table_ref.table_id}")
                        
                        with self._processing_lock:
                            self.processed_tables.add(table_path)
                        self.progress.update_stats(tables_processed=1)
                        
                        await asyncio.sleep(0.3)
                        
                    except Exception as e:
                        PrettyLogger.error(f"Table analysis failed {table_path}: {str(e)[:100]}")
                        self.progress.update_stats(tables_failed=1)
                
                with self._processing_lock:
                    self.processed_datasets.add(dataset_id)
                        
        except Exception as e:
            PrettyLogger.error(f"Dataset processing failed {dataset_id}: {e}")
    
    async def _comprehensive_table_analysis(self, table_path: str) -> int:
        try:
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            with self.client_manager.get_client() as client:
                try:
                    table_ref = client.get_table(table_path)
                except Exception:
                    return 0
                
                all_columns = [field.name for field in table_ref.schema]
                relevant_columns = self.data_extractor.find_all_relevant_columns(all_columns)
                
                hostname_candidates = relevant_columns.get('hostname', [])
                if not hostname_candidates:
                    return 0
                
                primary_hostname_col = hostname_candidates[0]
                
                select_fields = [f"UPPER(TRIM(CAST(`{primary_hostname_col}` AS STRING))) as hostname"]
                
                for field_type, columns in relevant_columns.items():
                    if field_type != 'hostname' and columns:
                        select_fields.append(f"CAST(`{columns[0]}` AS STRING) as {field_type}")
                
                comprehensive_query = f"""
                SELECT {', '.join(select_fields)}
                FROM `{table_path}`
                WHERE `{primary_hostname_col}` IS NOT NULL
                    AND LENGTH(TRIM(CAST(`{primary_hostname_col}` AS STRING))) >= 3
                """
                
                with client_manager.get_client() as client:
                    job = client.query(comprehensive_query)
                    results = list(job.result())
                
                endpoints_found = 0
                
                for row in results:
                    hostname = self.data_extractor.normalize_hostname(row[0])
                    if not hostname:
                        continue
                    
                    asset_data = {'hostname': hostname, 'source_type': 'discovery'}
                    
                    field_types = ['hostname'] + [ft for ft in relevant_columns.keys() if ft != 'hostname']
                    for i, field_type in enumerate(field_types):
                        if i > 0 and i < len(row) and row[i]:
                            value = str(row[i]).strip()
                            if value and value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE']:
                                asset_data[field_type] = value
                    
                    await self._comprehensive_asset_merge(asset_data)
                    endpoints_found += 1
                
                return endpoints_found
                
        except Exception:
            return 0
    
    async def _calculate_data_completeness(self):
        PrettyLogger.info("Calculating comprehensive data completeness scores")
        
        try:
            completeness_query = """
            SELECT 
                hostname,
                COUNT(CASE WHEN fqdn IS NOT NULL AND fqdn != '' THEN 1 END) as has_fqdn,
                COUNT(CASE WHEN ip_addresses IS NOT NULL AND ip_addresses != '' THEN 1 END) as has_ip,
                COUNT(CASE WHEN infrastructure_type IS NOT NULL AND infrastructure_type != '' THEN 1 END) as has_infra,
                COUNT(CASE WHEN global_region IS NOT NULL AND global_region != '' THEN 1 END) as has_region,
                COUNT(CASE WHEN country IS NOT NULL AND country != '' THEN 1 END) as has_country,
                COUNT(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 END) as has_bu,
                COUNT(CASE WHEN environment IS NOT NULL AND environment != '' THEN 1 END) as has_env
            FROM ao1_asset_inventory
            GROUP BY hostname
            """
            
            results = self.conn.execute(completeness_query).fetchall()
            
            for row in results:
                hostname = row[0]
                total_fields = 7
                populated_fields = sum(row[1:])
                completeness_score = (populated_fields / total_fields) * 100
                
                self.conn.execute("""
                    UPDATE ao1_asset_inventory 
                    SET data_completeness_score = ?
                    WHERE hostname = ?
                """, (completeness_score, hostname))
            
            PrettyLogger.success("Data completeness analysis completed")
            
        except Exception as e:
            PrettyLogger.error(f"Data completeness calculation failed: {e}")
    
    async def _calculate_ao1_metrics(self):
        PrettyLogger.info("Calculating comprehensive AO1 visibility metrics")
        
        try:
            total_assets = self.conn.execute("SELECT COUNT(*) FROM ao1_asset_inventory").fetchone()[0]
            
            if total_assets == 0:
                PrettyLogger.warning("No assets found for metrics calculation")
                return
            
            metrics_data = self.conn.execute("""
            SELECT 
                COUNT(*) as total_assets,
                AVG(data_completeness_score) as avg_completeness,
                SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) as logging_coverage,
                SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as security_coverage,
                SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN fqdn IS NOT NULL AND fqdn != '' THEN 1 ELSE 0 END) as fqdn_coverage,
                SUM(CASE WHEN ip_addresses IS NOT NULL AND ip_addresses != '' THEN 1 ELSE 0 END) as ip_coverage,
                SUM(CASE WHEN infrastructure_type IS NOT NULL AND infrastructure_type != '' THEN 1 ELSE 0 END) as infra_coverage,
                SUM(CASE WHEN global_region IS NOT NULL AND global_region != '' THEN 1 ELSE 0 END) as region_coverage,
                SUM(CASE WHEN country IS NOT NULL AND country != '' THEN 1 ELSE 0 END) as country_coverage
            FROM ao1_asset_inventory
            """).fetchone()
            
            metrics = {
                ('data_quality', 'average_completeness'): (metrics_data[1] or 0, 95.0),
                ('visibility', 'logging_coverage'): ((metrics_data[2] / total_assets) * 100, 90.0),
                ('security', 'agent_coverage'): ((metrics_data[3] / total_assets) * 100, 85.0),
                ('inventory', 'cmdb_coverage'): ((metrics_data[4] / total_assets) * 100, 95.0),
                ('network', 'fqdn_coverage'): ((metrics_data[5] / total_assets) * 100, 80.0),
                ('network', 'ip_coverage'): ((metrics_data[6] / total_assets) * 100, 85.0),
                ('classification', 'infrastructure_coverage'): ((metrics_data[7] / total_assets) * 100, 90.0),
                ('geography', 'region_coverage'): ((metrics_data[8] / total_assets) * 100, 75.0),
                ('geography', 'country_coverage'): ((metrics_data[9] / total_assets) * 100, 70.0)
            }
            
            for (category, metric_name), (value, target) in metrics.items():
                gap = max(0, target - value)
                priority = 1 if gap > 20 else 2 if gap > 10 else 3
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO ao1_visibility_metrics 
                    (metric_category, metric_name, metric_value, metric_target, gap_percentage, improvement_priority)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (category, metric_name, value, target, gap, priority))
            
            PrettyLogger.success(f"Calculated {len(metrics)} comprehensive AO1 metrics")
            
        except Exception as e:
            PrettyLogger.error(f"AO1 metrics calculation failed: {e}")
    
    async def _perform_gap_analysis(self):
        PrettyLogger.info("Performing comprehensive gap analysis")
        
        gap_analyses = [
            ("data_completeness_low", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE data_completeness_score < 50"),
            ("missing_fqdn", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE fqdn IS NULL OR fqdn = ''"),
            ("missing_ip", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE ip_addresses IS NULL OR ip_addresses = ''"),
            ("missing_infrastructure", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE infrastructure_type IS NULL OR infrastructure_type = ''"),
            ("missing_region", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE global_region IS NULL OR global_region = ''"),
            ("missing_country", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE country IS NULL OR country = ''"),
            ("no_logging", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE NOT in_splunk AND NOT in_chronicle"),
            ("no_security", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE NOT has_crowdstrike"),
            ("not_in_cmdb", "SELECT COUNT(*) FROM ao1_asset_inventory WHERE NOT found_in_cmdb")
        ]
        
        for gap_id, query in gap_analyses:
            try:
                count = self.conn.execute(query).fetchone()[0]
                if count > 0:
                    PrettyLogger.warning(f"Gap identified - {gap_id}: {count:,} assets")
            except Exception as e:
                PrettyLogger.error(f"Gap analysis failed for {gap_id}: {e}")
    
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
    
    def _get_data_completeness(self) -> Dict[str, Any]:
        try:
            result = self.conn.execute("""
                SELECT 
                    AVG(data_completeness_score) as avg_completeness,
                    COUNT(CASE WHEN data_completeness_score >= 90 THEN 1 END) as high_quality,
                    COUNT(CASE WHEN data_completeness_score >= 50 THEN 1 END) as medium_quality,
                    COUNT(CASE WHEN data_completeness_score < 50 THEN 1 END) as low_quality
                FROM ao1_asset_inventory
            """).fetchone()
            
            return {
                'average_completeness': result[0] or 0,
                'high_quality_assets': result[1] or 0,
                'medium_quality_assets': result[2] or 0,
                'low_quality_assets': result[3] or 0
            } if result else {}
        except Exception:
            return {}
    
    def _get_source_coverage(self) -> Dict[str, Any]:
        try:
            result = self.conn.execute("""
                SELECT table_name, total_records, processed_records, coverage_percentage
                FROM ao1_source_coverage ORDER BY coverage_percentage DESC
            """).fetchall()
            
            return {row[0]: {
                'total_records': row[1],
                'processed_records': row[2],
                'coverage_percentage': row[3]
            } for row in result} if result else {}
        except Exception:
            return {}
    
    def _get_ao1_metrics(self) -> Dict[str, Any]:
        try:
            result = self.conn.execute("""
                SELECT metric_category, metric_name, metric_value, metric_target, gap_percentage
                FROM ao1_visibility_metrics ORDER BY improvement_priority, gap_percentage DESC
            """).fetchall()
            
            return {f"{row[0]}_{row[1]}": {
                'value': row[2], 'target': row[3], 'gap': row[4]
            } for row in result} if result else {}
        except Exception:
            return {}
    
    def _create_analysis_queries(self) -> Dict[str, str]:
        return {
            'comprehensive_asset_overview': """
            SELECT 
                hostname, fqdn, ip_addresses, infrastructure_type, system_classification,
                global_region, country, business_unit, environment,
                found_in_cmdb, has_crowdstrike, in_splunk, in_chronicle,
                data_completeness_score, source_systems
            FROM ao1_asset_inventory 
            ORDER BY data_completeness_score DESC;
            """,
            
            'data_completeness_analysis': """
            SELECT 
                CASE 
                    WHEN data_completeness_score >= 90 THEN 'High Quality (90%+)'
                    WHEN data_completeness_score >= 70 THEN 'Good Quality (70-89%)'
                    WHEN data_completeness_score >= 50 THEN 'Medium Quality (50-69%)'
                    ELSE 'Low Quality (<50%)'
                END as quality_tier,
                COUNT(*) as asset_count,
                AVG(data_completeness_score) as avg_score
            FROM ao1_asset_inventory
            GROUP BY quality_tier
            ORDER BY avg_score DESC;
            """,
            
            'missing_critical_data': """
            SELECT 
                'Missing FQDN' as gap_type,
                COUNT(*) as affected_assets
            FROM ao1_asset_inventory WHERE fqdn IS NULL OR fqdn = ''
            UNION ALL
            SELECT 
                'Missing IP Address' as gap_type,
                COUNT(*) as affected_assets  
            FROM ao1_asset_inventory WHERE ip_addresses IS NULL OR ip_addresses = ''
            UNION ALL
            SELECT 
                'Missing Infrastructure Type' as gap_type,
                COUNT(*) as affected_assets
            FROM ao1_asset_inventory WHERE infrastructure_type IS NULL OR infrastructure_type = ''
            ORDER BY affected_assets DESC;
            """,
            
            'source_coverage_report': """
            SELECT 
                table_name,
                total_records,
                processed_records,
                unique_hostnames,
                data_fields_extracted,
                coverage_percentage,
                last_processed
            FROM ao1_source_coverage
            ORDER BY coverage_percentage DESC;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()