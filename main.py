#!/usr/bin/env python3

import os
import asyncio
import logging
import duckdb
import time
import threading
from typing import Dict, List, Any, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dataclasses import asdict
import json
import random
import re
from collections import defaultdict

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
    def discovery(source: str, endpoints: int, enriched: int):
        print(f"   ♡₊˚ 🌸 ⋆｡˚   {source}: {endpoints:,} endpoints discovered, {enriched:,} enriched")

class HostnameNormalizer:
    @staticmethod
    def normalize(hostname: str) -> str:
        if not hostname:
            return ""
        
        hostname = str(hostname).strip().upper()
        if len(hostname) < 2:
            return ""
        
        invalid_patterns = ['@', 'HTTP', 'HTTPS', 'UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 'TEST', 'EXAMPLE', 'LOCALHOST']
        if any(pattern in hostname for pattern in invalid_patterns):
            return ""
        
        hostname = re.sub(r'^[^A-Z0-9]+|[^A-Z0-9]+$', '', hostname)
        hostname = re.sub(r'\..*$', '', hostname)
        
        if len(hostname) < 2:
            return ""
        
        return hostname

class SmartTableAnalyzer:
    def __init__(self, matcher: ContentBasedMatcher):
        self.matcher = matcher
        self.hostname_patterns = ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system', 'workstation']
        
    def analyze_table_structure(self, table_ref, client) -> Dict[str, Any]:
        try:
            all_columns = [field.name for field in table_ref.schema]
            
            hostname_cols = []
            for col in all_columns:
                col_lower = col.lower()
                for pattern in self.hostname_patterns:
                    if pattern in col_lower:
                        hostname_cols.append(col)
                        break
            
            if not hostname_cols:
                return None
            
            categorized = self.matcher.analyze_all_columns(all_columns)
            
            primary_hostname = self._select_best_hostname_column(hostname_cols)
            
            data_columns = {}
            for category, cols in categorized.items():
                if category != 'endpoint' and cols:
                    data_columns[category] = cols[0]
            
            sample_query = f"SELECT * FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}` LIMIT 5"
            try:
                sample_job = client.query(sample_query)
                sample_data = list(sample_job.result())
                has_data = len(sample_data) > 0
            except:
                has_data = False
            
            return {
                'table_path': f"{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}",
                'primary_hostname_col': primary_hostname,
                'hostname_columns': hostname_cols,
                'data_columns': data_columns,
                'all_columns': all_columns,
                'has_data': has_data,
                'row_count': table_ref.num_rows or 0,
                'size_bytes': table_ref.num_bytes or 0
            }
        except Exception as e:
            return None
    
    def _select_best_hostname_column(self, hostname_cols: List[str]) -> str:
        priority_patterns = ['hostname', 'host_name', 'endpoint', 'computer_name', 'device_name', 'server_name']
        
        for pattern in priority_patterns:
            for col in hostname_cols:
                if pattern in col.lower():
                    return col
        
        return hostname_cols[0] if hostname_cols else None

class IntelligentDataMerger:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_tables()
        self._lock = threading.Lock()
        
    def _setup_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_endpoints (
            hostname VARCHAR PRIMARY KEY,
            normalized_hostname VARCHAR,
            discovered_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_endpoint_data (
            hostname VARCHAR,
            field_name VARCHAR,
            field_value TEXT,
            data_source VARCHAR,
            table_source VARCHAR,
            confidence_score DOUBLE DEFAULT 1.0,
            last_updated TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (hostname, field_name, data_source)
        )
        """)
        
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
            environment VARCHAR,
            cost_center VARCHAR,
            owner VARCHAR,
            criticality VARCHAR,
            
            in_splunk BOOLEAN DEFAULT FALSE,
            in_chronicle BOOLEAN DEFAULT FALSE,
            has_crowdstrike BOOLEAN DEFAULT FALSE,
            found_in_cmdb BOOLEAN DEFAULT FALSE,
            
            source_systems TEXT,
            data_completeness_score DOUBLE DEFAULT 0.0,
            ao1_visibility_score DOUBLE DEFAULT 0.0,
            
            discovery_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW(),
            raw_data TEXT
        )
        """)
    
    def register_endpoint(self, hostname: str, original_hostname: str = None):
        normalized = HostnameNormalizer.normalize(hostname)
        if not normalized:
            return False
            
        with self._lock:
            try:
                self.conn.execute("""
                INSERT OR IGNORE INTO ao1_endpoints (hostname, normalized_hostname)
                VALUES (?, ?)
                """, (normalized, original_hostname or hostname))
                return True
            except:
                return False
    
    def add_endpoint_data(self, hostname: str, field_name: str, field_value: str, 
                         data_source: str, table_source: str, confidence: float = 1.0):
        normalized = HostnameNormalizer.normalize(hostname)
        if not normalized or not field_value:
            return
            
        with self._lock:
            try:
                self.conn.execute("""
                INSERT OR REPLACE INTO ao1_endpoint_data 
                (hostname, field_name, field_value, data_source, table_source, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (normalized, field_name, str(field_value).strip(), data_source, table_source, confidence))
            except Exception as e:
                pass
    
    def build_consolidated_inventory(self):
        with self._lock:
            try:
                endpoints = self.conn.execute("SELECT DISTINCT hostname FROM ao1_endpoints").fetchall()
                
                for (hostname,) in endpoints:
                    data = self._get_best_data_for_endpoint(hostname)
                    self._insert_or_update_inventory(hostname, data)
                    
            except Exception as e:
                PrettyLogger.error(f"Consolidation failed: {e}")
    
    def _get_best_data_for_endpoint(self, hostname: str) -> Dict[str, str]:
        data_query = """
        SELECT field_name, field_value, confidence_score, data_source
        FROM ao1_endpoint_data 
        WHERE hostname = ?
        ORDER BY confidence_score DESC, last_updated DESC
        """
        
        results = self.conn.execute(data_query, (hostname,)).fetchall()
        
        best_data = {}
        sources = set()
        
        for field_name, field_value, confidence, data_source in results:
            sources.add(data_source)
            
            if field_name not in best_data and field_value and str(field_value).strip():
                best_data[field_name] = str(field_value).strip()
        
        best_data['source_systems'] = ','.join(sorted(sources))
        return best_data
    
    def _insert_or_update_inventory(self, hostname: str, data: Dict[str, str]):
        try:
            source_flags = {
                'found_in_cmdb': any('cmdb' in s.lower() for s in data.get('source_systems', '').split(',')),
                'has_crowdstrike': any('crowdstrike' in s.lower() for s in data.get('source_systems', '').split(',')),
                'in_splunk': any('splunk' in s.lower() for s in data.get('source_systems', '').split(',')),
                'in_chronicle': any('chronicle' in s.lower() for s in data.get('source_systems', '').split(','))
            }
            
            completeness = self._calculate_completeness(data)
            
            self.conn.execute("""
            INSERT OR REPLACE INTO ao1_asset_inventory (
                hostname, fqdn, ip_addresses, infrastructure_type, system_classification,
                operating_system, global_region, country, data_center, cloud_region,
                business_unit, environment, cost_center, owner, criticality,
                found_in_cmdb, has_crowdstrike, in_splunk, in_chronicle,
                source_systems, data_completeness_score, raw_data, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                hostname,
                data.get('fqdn', ''),
                data.get('ip_address', ''),
                data.get('infrastructure_type', ''),
                data.get('system_classification', ''),
                data.get('os', ''),
                data.get('region', ''),
                data.get('country', ''),
                data.get('data_center', ''),
                data.get('cloud_region', ''),
                data.get('business_unit', ''),
                data.get('environment', ''),
                data.get('cost_center', ''),
                data.get('owner', ''),
                data.get('criticality', ''),
                source_flags['found_in_cmdb'],
                source_flags['has_crowdstrike'],
                source_flags['in_splunk'],
                source_flags['in_chronicle'],
                data.get('source_systems', ''),
                completeness,
                json.dumps(data)
            ))
        except Exception as e:
            pass
    
    def _calculate_completeness(self, data: Dict[str, str]) -> float:
        critical_fields = ['fqdn', 'ip_address', 'infrastructure_type', 'region', 'business_unit', 'environment']
        populated = sum(1 for field in critical_fields if data.get(field))
        return (populated / len(critical_fields)) * 100
    
    def get_stats(self) -> Dict[str, int]:
        try:
            endpoints_count = self.conn.execute("SELECT COUNT(*) FROM ao1_endpoints").fetchone()[0]
            inventory_count = self.conn.execute("SELECT COUNT(*) FROM ao1_asset_inventory").fetchone()[0]
            data_points = self.conn.execute("SELECT COUNT(*) FROM ao1_endpoint_data").fetchone()[0]
            
            return {
                'total_endpoints': endpoints_count,
                'consolidated_assets': inventory_count,
                'total_data_points': data_points
            }
        except:
            return {'total_endpoints': 0, 'consolidated_assets': 0, 'total_data_points': 0}

class AO1SmartDiscovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   AO1 Smart Multi-Table Discovery   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*90)
        
        self.client_manager = BigQueryClientManager(project_id)
        self.chronicle_client_manager = None
        
        if not self.client_manager.test_connection():
            raise ConnectionError("Failed to authenticate with BigQuery")
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
            if not self.chronicle_client_manager.test_connection():
                PrettyLogger.warning("Chronicle project unavailable")
                self.chronicle_client_manager = None
        except:
            self.chronicle_client_manager = None
        
        self.matcher = ContentBasedMatcher()
        self.analyzer = SmartTableAnalyzer(self.matcher)
        self.cache = CacheManager(self.config.get('cache_dir', '.cache'))
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_visibility_cmdb.db')
        self.merger = IntelligentDataMerger(self.db_path)
        
        self.processed_tables = set()
        self.discovered_endpoints = set()
        self._lock = threading.Lock()
        
        self.critical_sources = [
            (project_id, 'SAS_BI', 'V_DIM_ENDPOINT', 'cmdb', 100),
            (project_id, 'SAS_BI', 'V_DIM_ENDPOINTAGENT', 'crowdstrike', 95),
            (project_id, 'SAS_BI', 'V_SPL_ENDPOINT_LOG', 'splunk', 90),
            ('chronicle-fisv', 'datalake', 'events', 'chronicle', 85)
        ]
    
    async def execute_smart_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting intelligent multi-table discovery")
        
        try:
            await self._discover_all_tables()
            
            await self._execute_smart_hostname_discovery()
            
            await self._execute_comprehensive_data_enrichment()
            
            PrettyLogger.info("Building consolidated asset inventory")
            self.merger.build_consolidated_inventory()
            
            stats = self._generate_final_stats(time.time() - start_time)
            queries = self._create_analysis_queries()
            
            PrettyLogger.success("Smart discovery completed successfully")
            return stats, queries
            
        except Exception as e:
            PrettyLogger.error(f"Smart discovery failed: {e}")
            raise
        finally:
            if hasattr(self.merger, 'conn'):
                self.merger.conn.close()
    
    async def _discover_all_tables(self):
        PrettyLogger.info("Discovering all available tables")
        
        self.all_table_metadata = []
        
        for project_id in [self.project_id, 'chronicle-fisv']:
            if project_id == 'chronicle-fisv' and not self.chronicle_client_manager:
                continue
                
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                with client_mgr.get_client() as client:
                    datasets = list(client.list_datasets(project=project_id))
                    
                    for dataset in datasets:
                        try:
                            tables = list(client.list_tables(dataset.reference))
                            
                            for table_ref in tables:
                                try:
                                    full_table = client.get_table(table_ref)
                                    analysis = self.analyzer.analyze_table_structure(full_table, client)
                                    
                                    if analysis and analysis['has_data']:
                                        analysis['project_id'] = project_id
                                        self.all_table_metadata.append(analysis)
                                        
                                except Exception:
                                    continue
                        except Exception:
                            continue
            except Exception as e:
                PrettyLogger.warning(f"Failed to analyze project {project_id}: {e}")
        
        PrettyLogger.success(f"Discovered {len(self.all_table_metadata)} tables with hostname data")
    
    async def _execute_smart_hostname_discovery(self):
        PrettyLogger.info("Phase 1: Smart hostname discovery across all tables")
        
        critical_tables = [t for t in self.all_table_metadata 
                          if any(crit[1] in t['table_path'] and crit[2] in t['table_path'] 
                               for crit in self.critical_sources)]
        
        other_tables = [t for t in self.all_table_metadata if t not in critical_tables]
        
        all_tables = critical_tables + other_tables
        
        hostname_counts = {}
        
        for table_meta in all_tables:
            try:
                count = await self._discover_hostnames_from_table(table_meta)
                if count > 0:
                    hostname_counts[table_meta['table_path']] = count
                    
            except Exception as e:
                PrettyLogger.error(f"Hostname discovery failed for {table_meta['table_path']}: {e}")
                continue
        
        total_hostnames = len(self.discovered_endpoints)
        PrettyLogger.success(f"Discovered {total_hostnames:,} unique endpoints from {len(hostname_counts)} tables")
    
    async def _discover_hostnames_from_table(self, table_meta: Dict[str, Any]) -> int:
        table_path = table_meta['table_path']
        hostname_col = table_meta['primary_hostname_col']
        
        if not hostname_col:
            return 0
        
        project_id = table_meta['project_id']
        client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
        
        try:
            with client_mgr.get_client() as client:
                hostname_query = f"""
                SELECT DISTINCT 
                    UPPER(TRIM(CAST(`{hostname_col}` AS STRING))) as hostname
                FROM `{table_path}`
                WHERE `{hostname_col}` IS NOT NULL
                    AND LENGTH(TRIM(CAST(`{hostname_col}` AS STRING))) >= 2
                    AND TRIM(CAST(`{hostname_col}` AS STRING)) NOT IN ('', 'NULL', 'N/A', 'UNKNOWN')
                """
                
                job = client.query(hostname_query)
                results = list(job.result())
                
                discovered_count = 0
                for row in results:
                    hostname = row[0]
                    normalized = HostnameNormalizer.normalize(hostname)
                    
                    if normalized and self.merger.register_endpoint(normalized, hostname):
                        with self._lock:
                            self.discovered_endpoints.add(normalized)
                        discovered_count += 1
                
                if discovered_count > 0:
                    table_name = table_path.split('.')[-1]
                    PrettyLogger.success(f"{table_name}: {discovered_count:,} hostnames")
                
                return discovered_count
                
        except Exception as e:
            return 0
    
    async def _execute_comprehensive_data_enrichment(self):
        PrettyLogger.info("Phase 2: Comprehensive data enrichment for all endpoints")
        
        endpoint_chunks = list(self.discovered_endpoints)
        chunk_size = 1000
        
        for i in range(0, len(endpoint_chunks), chunk_size):
            if self.signal_handler.shutdown_requested:
                break
                
            chunk = endpoint_chunks[i:i + chunk_size]
            await self._enrich_endpoint_chunk(chunk)
            
            PrettyLogger.info(f"Enriched {min(i + chunk_size, len(endpoint_chunks)):,}/{len(endpoint_chunks):,} endpoints")
    
    async def _enrich_endpoint_chunk(self, hostnames: List[str]):
        for table_meta in self.all_table_metadata:
            if self.signal_handler.shutdown_requested:
                break
                
            try:
                enriched = await self._enrich_from_table(table_meta, hostnames)
                
                if enriched > 0:
                    table_name = table_meta['table_path'].split('.')[-1]
                    data_source = self._determine_data_source(table_meta['table_path'])
                    
            except Exception:
                continue
    
    async def _enrich_from_table(self, table_meta: Dict[str, Any], target_hostnames: List[str]) -> int:
        table_path = table_meta['table_path']
        hostname_col = table_meta['primary_hostname_col']
        data_columns = table_meta['data_columns']
        
        if not data_columns:
            return 0
        
        project_id = table_meta['project_id']
        client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
        
        hostname_list = "', '".join(target_hostnames)
        
        select_fields = [f"UPPER(TRIM(CAST(`{hostname_col}` AS STRING))) as hostname"]
        field_mappings = {'hostname': hostname_col}
        
        for field_type, column in data_columns.items():
            select_fields.append(f"CAST(`{column}` AS STRING) as {field_type}")
            field_mappings[field_type] = column
        
        enrichment_query = f"""
        SELECT {', '.join(select_fields)}
        FROM `{table_path}`
        WHERE UPPER(TRIM(CAST(`{hostname_col}` AS STRING))) IN ('{hostname_list}')
            AND `{hostname_col}` IS NOT NULL
        """
        
        try:
            with client_mgr.get_client() as client:
                job = client.query(enrichment_query)
                results = list(job.result())
                
                data_source = self._determine_data_source(table_path)
                enriched_count = 0
                
                for row in results:
                    hostname = HostnameNormalizer.normalize(row[0])
                    if not hostname:
                        continue
                    
                    for i, (field_type, _) in enumerate(field_mappings.items()):
                        if i > 0 and i < len(row) and row[i]:
                            value = str(row[i]).strip()
                            if value and value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
                                self.merger.add_endpoint_data(
                                    hostname, field_type, value, data_source, table_path
                                )
                    
                    enriched_count += 1
                
                return enriched_count
                
        except Exception:
            return 0
    
    def _determine_data_source(self, table_path: str) -> str:
        table_lower = table_path.lower()
        
        if 'cmdb' in table_lower or 'dim_endpoint' in table_lower:
            return 'cmdb'
        elif 'crowdstrike' in table_lower or 'agent' in table_lower:
            return 'crowdstrike'
        elif 'splunk' in table_lower or 'spl_' in table_lower:
            return 'splunk'
        elif 'chronicle' in table_lower or 'events' in table_lower:
            return 'chronicle'
        elif 'security' in table_lower:
            return 'security'
        elif 'network' in table_lower:
            return 'network'
        else:
            return 'discovery'
    
    def _generate_final_stats(self, processing_time: float) -> Dict[str, Any]:
        merger_stats = self.merger.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'total_tables_analyzed': len(self.all_table_metadata),
            'total_endpoints_discovered': merger_stats['total_endpoints'],
            'consolidated_assets': merger_stats['consolidated_assets'],
            'total_data_points': merger_stats['total_data_points'],
            'unique_hostnames': len(self.discovered_endpoints),
            'tables_with_hostnames': len([t for t in self.all_table_metadata if t['has_data']]),
            'data_enrichment_complete': True
        }
    
    def _create_analysis_queries(self) -> Dict[str, str]:
        return {
            'consolidated_assets': """
            SELECT 
                hostname, fqdn, ip_addresses, infrastructure_type, global_region,
                business_unit, environment, found_in_cmdb, has_crowdstrike, 
                in_splunk, in_chronicle, data_completeness_score, source_systems
            FROM ao1_asset_inventory 
            ORDER BY data_completeness_score DESC;
            """,
            
            'data_enrichment_summary': """
            SELECT 
                field_name,
                COUNT(DISTINCT hostname) as endpoints_with_data,
                COUNT(DISTINCT data_source) as data_sources,
                AVG(confidence_score) as avg_confidence
            FROM ao1_endpoint_data
            GROUP BY field_name
            ORDER BY endpoints_with_data DESC;
            """,
            
            'source_contribution': """
            SELECT 
                data_source,
                COUNT(DISTINCT hostname) as unique_endpoints,
                COUNT(*) as total_data_points,
                COUNT(DISTINCT field_name) as field_types
            FROM ao1_endpoint_data
            GROUP BY data_source
            ORDER BY unique_endpoints DESC;
            """,
            
            'completeness_analysis': """
            SELECT 
                CASE 
                    WHEN data_completeness_score >= 80 THEN 'Excellent (80%+)'
                    WHEN data_completeness_score >= 60 THEN 'Good (60-79%)'
                    WHEN data_completeness_score >= 40 THEN 'Fair (40-59%)'
                    ELSE 'Poor (<40%)'
                END as completeness_tier,
                COUNT(*) as asset_count,
                AVG(data_completeness_score) as avg_score
            FROM ao1_asset_inventory
            GROUP BY completeness_tier
            ORDER BY avg_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.merger, 'conn') and self.merger.conn:
            self.merger.conn.close()