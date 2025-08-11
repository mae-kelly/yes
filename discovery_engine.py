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
import gc
import platform

from gcp_client import BigQueryClientManager
from content_matcher import ContentBasedMatcher
from cache_manager import CacheManager
from progress_tracker import ProgressTracker
from checkpoint_manager import CheckpointManager
from signal_handler import SignalHandler

logger = logging.getLogger(__name__)

def setup_m1_optimization():
    if platform.system() == "Darwin" and platform.processor() == "arm":
        try:
            import torch
            if torch.backends.mps.is_available():
                os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
                os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
                print("   ❀°｡ ‧˚♡ ˚‧ ｡°❀   M1 GPU acceleration enabled")
                return True
        except ImportError:
            pass
    return False

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
    def dataset(dataset_name: str, count: int, total: int):
        print(f"   ˚ ༘♡ ⋆｡˚   Dataset {count}/{total}: {dataset_name}")
    
    @staticmethod
    def table(table_name: str, endpoints_found: int = 0):
        if endpoints_found > 0:
            print(f"   ･ﾟ✧ ◞ ♡   Found {endpoints_found} endpoints in: {table_name}")
        else:
            print(f"   ｡･:*:･ﾟ★   Analyzing: {table_name}")
    
    @staticmethod
    def endpoint_merge(endpoint: str, table_count: int):
        print(f"   ♡˗ˏˋ ◞ ～   Merging {endpoint} from {table_count} sources")
    
    @staticmethod
    def progress(current: int, total: int, item_type: str):
        percentage = (current / total * 100) if total > 0 else 0
        print(f"   ✧･ﾟ: *✧･ﾟ:*   Progress: {current}/{total} {item_type} ({percentage:.1f}%)")
    
    @staticmethod
    def memory_cleanup():
        print(f"   ｡･:*:･ﾟ★   Memory cleanup performed")

class DiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*80)
        print("   ♡₊˚ ✧ ‧₊˚ ⋅   AO1 Log Visibility Discovery   ⋅ ˚₊‧ ✧ ˚₊♡")
        print("="*80)
        
        self.m1_enabled = setup_m1_optimization()
        
        PrettyLogger.info(f"Initializing for project: {project_id}")
        
        self.client_manager = BigQueryClientManager(project_id)
        
        if not self.client_manager.test_connection():
            raise ConnectionError("Failed to authenticate with BigQuery")
        
        PrettyLogger.success("BigQuery authentication successful")
        
        self.matcher = ContentBasedMatcher()
        self.cache = CacheManager(self.config.get('cache_dir', '.cache'))
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_visibility_cmdb.db')
        
        cpu_count = mp.cpu_count()
        if self.m1_enabled:
            self.max_workers = min(8, cpu_count)
        else:
            self.max_workers = self.config.get('max_workers', min(6, cpu_count))
        
        PrettyLogger.info(f"Using {self.max_workers} workers (M1 optimized: {self.m1_enabled})")
        
        self.core_tables = {
            'cmdb': f'{project_id}.SAS_BI.V_DIM_ENDPOINT',
            'splunk': f'{project_id}.SAS_BI.V_SPL_ENDPOINT_LOG',
            'crowdstrike': f'{project_id}.SAS_BI.V_DIM_ENDPOINTAGENT'
        }
        
        self.processed_datasets = set()
        self.processed_tables = set()
        self._processing_lock = threading.Lock()
        self.dataset_counter = 0
        self.table_counter = 0
        self._cleanup_counter = 0
        
        self._setup_database()
    
    def _setup_database(self):
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
            logging_platforms TEXT,
            
            has_edr BOOLEAN DEFAULT FALSE,
            has_tanium BOOLEAN DEFAULT FALSE,
            has_dlp BOOLEAN DEFAULT FALSE,
            has_crowdstrike BOOLEAN DEFAULT FALSE,
            security_tools TEXT,
            
            found_in_cmdb BOOLEAN DEFAULT FALSE,
            found_in_ad BOOLEAN DEFAULT FALSE,
            found_in_dhcp BOOLEAN DEFAULT FALSE,
            found_in_dns BOOLEAN DEFAULT FALSE,
            found_in_tables TEXT,
            
            visibility_score DOUBLE DEFAULT 0.0,
            last_log_seen TIMESTAMP,
            discovery_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS discovered_tables (
            table_path VARCHAR PRIMARY KEY,
            dataset_name VARCHAR,
            table_name VARCHAR,
            row_count BIGINT,
            size_bytes BIGINT,
            endpoints_found INTEGER DEFAULT 0,
            is_partitioned BOOLEAN DEFAULT FALSE,
            partition_column VARCHAR,
            discovery_score DOUBLE DEFAULT 0.0,
            discovered_at TIMESTAMP DEFAULT NOW()
        )
        """)
    
    def _periodic_cleanup(self):
        self._cleanup_counter += 1
        if self._cleanup_counter % 20 == 0:
            gc.collect()
            PrettyLogger.memory_cleanup()
    
    async def discover_all_endpoints(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting comprehensive asset discovery")
        
        try:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            if checkpoint:
                PrettyLogger.info("Resuming from checkpoint")
                await self._resume_from_checkpoint(checkpoint)
            
            await self._load_core_tables()
            await self._discover_all_datasets_and_tables()
            
            stats = self.progress.get_stats()
            queries = self._create_analysis_queries()
            
            final_stats = {
                'processing_time': time.time() - start_time,
                'database_path': self.db_path,
                'total_endpoints': self._count_endpoints(),
                'visibility_coverage': self._get_visibility_coverage(),
                'discovery_summary': self._get_summary(),
                'performance_stats': asdict(stats),
                'm1_gpu_enabled': self.m1_enabled
            }
            
            self.checkpoint_manager.clear_checkpoint()
            PrettyLogger.success("Discovery completed successfully")
            
            return final_stats, queries
            
        except Exception as e:
            PrettyLogger.error(f"Discovery failed: {e}")
            await self._save_emergency_checkpoint()
            raise
        finally:
            if hasattr(self.client_manager, 'close_all'):
                self.client_manager.close_all()
            self.conn.close()
    
    async def _resume_from_checkpoint(self, checkpoint: Dict[str, Any]):
        self.processed_datasets = set(checkpoint.get('processed_datasets', []))
        self.processed_tables = set(checkpoint.get('processed_tables', []))
        
        self.progress.set_stats(
            datasets_processed=len(self.processed_datasets),
            tables_processed=len(self.processed_tables),
            endpoints_discovered=checkpoint.get('endpoints_discovered', 0)
        )
    
    async def _load_core_tables(self):
        PrettyLogger.info("Loading core CMDB tables")
        
        for table_key in self.core_tables:
            try:
                await self._load_core_table(table_key)
                PrettyLogger.success(f"Loaded {table_key} successfully")
                time.sleep(1)
            except Exception as e:
                PrettyLogger.error(f"Failed to load {table_key}: {e}")
    
    async def _load_core_table(self, table_key: str):
        table_path = self.core_tables[table_key]
        
        try:
            with self.client_manager.get_client() as client:
                table_ref = client.get_table(table_path)
                available_columns = [field.name for field in table_ref.schema]
                
                endpoint_cols = []
                for col in ['Endpoint_Nme', 'EndpointFQDN_Nme', 'Endpoint_ID', 'hostname', 'computer_name', 'device_name']:
                    if col in available_columns:
                        endpoint_cols.append(col)
                
                if not endpoint_cols:
                    PrettyLogger.warning(f"No endpoint columns found in {table_key}")
                    return
                
                endpoint_col = endpoint_cols[0]
                
                select_parts = [f"UPPER(TRIM(CAST(`{endpoint_col}` AS STRING))) as hostname"]
                
                for col, alias in [
                    ('EndpointRegion_Nme', 'global_region'),
                    ('region', 'global_region'),
                    ('EndpointEnvironment_Type', 'environment'),
                    ('environment', 'environment'),
                    ('Endpoint_Type', 'system_classification'),
                    ('endpoint_type', 'system_classification')
                ]:
                    if col in available_columns:
                        select_parts.append(f"CAST({col} AS STRING) as {alias}")
                        break
                
                query = f"""
                SELECT DISTINCT {', '.join(select_parts)}
                FROM `{table_path}`
                WHERE `{endpoint_col}` IS NOT NULL
                    AND LENGTH(TRIM(CAST(`{endpoint_col}` AS STRING))) >= 3
                """
                
                await self._execute_and_store_endpoints(query, table_key, table_path)
                
        except Exception as e:
            PrettyLogger.error(f"Failed to load core table {table_key}: {e}")
    
    async def _discover_all_datasets_and_tables(self):
        PrettyLogger.info("Discovering all datasets and tables")
        
        with self.client_manager.get_client() as client:
            all_datasets = list(client.list_datasets(project=self.project_id))
        
        self.progress.set_stats(datasets_total=len(all_datasets))
        PrettyLogger.info(f"Found {len(all_datasets)} datasets to analyze")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for i, dataset in enumerate(all_datasets, 1):
                if self.signal_handler.shutdown_requested:
                    break
                
                if dataset.dataset_id in self.processed_datasets:
                    continue
                
                PrettyLogger.dataset(dataset.dataset_id, i, len(all_datasets))
                future = executor.submit(self._process_complete_dataset, dataset.dataset_id)
                futures.append((future, dataset.dataset_id))
                
                if i % 5 == 0:
                    time.sleep(2)
            
            for future, dataset_id in futures:
                if self.signal_handler.shutdown_requested:
                    break
                
                try:
                    result = future.result()
                    with self._processing_lock:
                        self.processed_datasets.add(dataset_id)
                    self.progress.update_stats(datasets_processed=1)
                    
                    self._periodic_cleanup()
                    
                    if self.progress.should_checkpoint():
                        await self._save_checkpoint()
                        
                except Exception as e:
                    PrettyLogger.error(f"Dataset processing failed for {dataset_id}: {e}")
                    self.progress.update_stats(datasets_failed=1)
    
    def _process_complete_dataset(self, dataset_id: str):
        try:
            with self.client_manager.get_client() as client:
                dataset_ref = client.dataset(dataset_id, project=self.project_id)
                all_tables = list(client.list_tables(dataset_ref))
                
                for table_ref in all_tables:
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    table_full_path = f"{self.project_id}.{dataset_id}.{table_ref.table_id}"
                    
                    if table_full_path in self.processed_tables:
                        continue
                    
                    try:
                        PrettyLogger.table(f"{dataset_id}.{table_ref.table_id}")
                        endpoints_found = self._analyze_table_for_endpoints(table_full_path, dataset_id, table_ref.table_id)
                        
                        if endpoints_found > 0:
                            PrettyLogger.table(f"{dataset_id}.{table_ref.table_id}", endpoints_found)
                        
                        with self._processing_lock:
                            self.processed_tables.add(table_full_path)
                        self.progress.update_stats(tables_processed=1)
                        
                        time.sleep(0.2)
                        
                    except Exception as e:
                        PrettyLogger.error(f"Table analysis failed {table_full_path}: {e}")
                        self.progress.update_stats(tables_failed=1)
                        time.sleep(0.5)
                        
        except Exception as e:
            PrettyLogger.error(f"Dataset processing failed {dataset_id}: {e}")
            raise
    
    def _analyze_table_for_endpoints(self, table_path: str, dataset_id: str, table_id: str) -> int:
        try:
            with self.client_manager.get_client() as client:
                table_ref = client.get_table(table_path)
                
                is_partitioned = table_ref.time_partitioning is not None
                partition_filter = ""
                
                if is_partitioned and table_ref.time_partitioning.field:
                    partition_col = table_ref.time_partitioning.field
                    partition_filter = f"WHERE {partition_col} >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
                
                endpoints_found = 0
                
                for field in table_ref.schema:
                    if field.field_type == 'STRING':
                        try:
                            sample_query = f"""
                            SELECT `{field.name}`
                            FROM `{table_path}`
                            {partition_filter}
                            {" AND " if partition_filter else "WHERE"} `{field.name}` IS NOT NULL
                            LIMIT 10
                            """
                            
                            job = client.query(sample_query)
                            samples = [str(row[0]) for row in job.result() if row[0] is not None]
                            
                            if samples:
                                match_result = self.matcher.analyze_column(field.name, samples)
                                if match_result and match_result[0] == 'endpoint':
                                    
                                    endpoint_query = f"""
                                    SELECT DISTINCT
                                        UPPER(TRIM(CAST(`{field.name}` AS STRING))) as hostname
                                    FROM `{table_path}`
                                    {partition_filter}
                                    {" AND " if partition_filter else "WHERE"} `{field.name}` IS NOT NULL
                                        AND LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 3
                                    """
                                    
                                    endpoint_job = client.query(endpoint_query)
                                    endpoints = list(endpoint_job.result())
                                    
                                    if endpoints:
                                        for row in endpoints:
                                            if row[0]:
                                                self._merge_endpoint_data({
                                                    'hostname': str(row[0]).upper().strip(),
                                                    'found_in_tables': table_path
                                                })
                                                endpoints_found += 1
                        
                        except Exception:
                            continue
                
                self._store_table_metadata({
                    'table_path': table_path,
                    'dataset_name': dataset_id,
                    'table_name': table_id,
                    'row_count': table_ref.num_rows or 0,
                    'size_bytes': table_ref.num_bytes or 0,
                    'endpoints_found': endpoints_found,
                    'is_partitioned': is_partitioned
                })
                
                return endpoints_found
                
        except Exception as e:
            return 0
    
    def _merge_endpoint_data(self, endpoint_data: Dict[str, Any]):
        hostname = endpoint_data['hostname']
        
        existing = self.conn.execute(
            "SELECT found_in_tables, global_region, environment, system_classification FROM ao1_asset_inventory WHERE hostname = ?",
            (hostname,)
        ).fetchone()
        
        if existing:
            existing_tables = existing[0] or ""
            new_table = endpoint_data.get('found_in_tables', '')
            
            if new_table and new_table not in existing_tables:
                updated_tables = f"{existing_tables},{new_table}" if existing_tables else new_table
                
                update_fields = ["found_in_tables = ?"]
                update_values = [updated_tables]
                
                for field, idx in [('global_region', 1), ('environment', 2), ('system_classification', 3)]:
                    if field in endpoint_data and endpoint_data[field] and not existing[idx]:
                        update_fields.append(f"{field} = ?")
                        update_values.append(endpoint_data[field])
                
                update_values.append(hostname)
                
                self.conn.execute(f"""
                    UPDATE ao1_asset_inventory 
                    SET {', '.join(update_fields)}, last_updated = CURRENT_TIMESTAMP
                    WHERE hostname = ?
                """, update_values)
                
                PrettyLogger.endpoint_merge(hostname, len(updated_tables.split(',')))
        else:
            self.conn.execute("""
            INSERT INTO ao1_asset_inventory (
                hostname, found_in_tables, global_region, environment, system_classification,
                discovery_timestamp, last_updated
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                hostname,
                endpoint_data.get('found_in_tables', ''),
                endpoint_data.get('global_region', ''),
                endpoint_data.get('environment', ''),
                endpoint_data.get('system_classification', '')
            ))
    
    async def _execute_and_store_endpoints(self, query: str, source: str, table_path: str):
        try:
            with self.client_manager.get_client() as client:
                job = client.query(query)
                results = list(job.result())
                
                for row in results:
                    if row[0]:
                        endpoint_data = {'hostname': str(row[0]).upper().strip()}
                        
                        if len(row) > 1 and row[1]:
                            endpoint_data['global_region'] = str(row[1])
                        if len(row) > 2 and row[2]:
                            endpoint_data['environment'] = str(row[2])
                        if len(row) > 3 and row[3]:
                            endpoint_data['system_classification'] = str(row[3])
                        
                        endpoint_data['found_in_tables'] = table_path
                        
                        if source == 'cmdb':
                            endpoint_data['found_in_cmdb'] = True
                        elif source == 'splunk':
                            endpoint_data['in_splunk'] = True
                        elif source == 'crowdstrike':
                            endpoint_data['has_crowdstrike'] = True
                        
                        self._merge_endpoint_data(endpoint_data)
                
                self.progress.update_stats(endpoints_discovered=len(results))
                
        except Exception as e:
            PrettyLogger.error(f"Failed to execute query for {source}: {e}")
    
    def _store_table_metadata(self, table_info: Dict[str, Any]):
        try:
            self.conn.execute("""
            INSERT OR REPLACE INTO discovered_tables (
                table_path, dataset_name, table_name, row_count, size_bytes,
                endpoints_found, is_partitioned, discovered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                table_info['table_path'],
                table_info['dataset_name'],
                table_info['table_name'],
                table_info['row_count'],
                table_info['size_bytes'],
                table_info['endpoints_found'],
                table_info['is_partitioned']
            ))
        except Exception as e:
            PrettyLogger.error(f"Failed to store table metadata: {e}")
    
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
    
    def _count_endpoints(self) -> int:
        try:
            result = self.conn.execute("SELECT COUNT(*) FROM ao1_asset_inventory").fetchone()
            return result[0] if result else 0
        except Exception:
            return 0
    
    def _get_visibility_coverage(self) -> Dict[str, Any]:
        try:
            result = self.conn.execute("""
            SELECT 
                COUNT(*) as total_assets,
                SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_coverage
            FROM ao1_asset_inventory
            """).fetchone()
            
            if result:
                total = result[0] or 1
                return {
                    'total_assets': result[0],
                    'splunk_coverage_pct': (result[1] / total) * 100,
                    'chronicle_coverage_pct': (result[2] / total) * 100,
                    'crowdstrike_coverage_pct': (result[3] / total) * 100,
                    'cmdb_coverage_pct': (result[4] / total) * 100
                }
        except Exception:
            pass
        return {}
    
    def _get_summary(self) -> Dict[str, Any]:
        total_endpoints = self._count_endpoints()
        coverage = self._get_visibility_coverage()
        
        return {
            'total_endpoints': total_endpoints,
            'visibility_coverage': coverage,
            'discovery_status': 'COMPLETE'
        }
    
    def _create_analysis_queries(self) -> Dict[str, str]:
        return {
            'ao1_global_visibility': """
            SELECT 
                COUNT(*) as total_assets,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as global_visibility_pct
            FROM ao1_asset_inventory;
            """,
            
            'ao1_infrastructure_type_breakdown': """
            SELECT 
                infrastructure_type,
                COUNT(*) as asset_count,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as visibility_pct
            FROM ao1_asset_inventory
            GROUP BY infrastructure_type
            ORDER BY visibility_pct DESC;
            """,
            
            'ao1_regional_visibility': """
            SELECT 
                global_region,
                COUNT(*) as asset_count,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as visibility_pct
            FROM ao1_asset_inventory
            WHERE global_region IS NOT NULL
            GROUP BY global_region
            ORDER BY visibility_pct DESC;
            """,
            
            'ao1_security_control_coverage': """
            SELECT 
                'EDR Coverage' as control_type,
                (SUM(CASE WHEN has_edr THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as coverage_pct
            FROM ao1_asset_inventory
            UNION ALL
            SELECT 
                'CrowdStrike Coverage',
                (SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
            FROM ao1_asset_inventory
            UNION ALL
            SELECT 
                'Tanium Coverage',
                (SUM(CASE WHEN has_tanium THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
            FROM ao1_asset_inventory;
            """,
            
            'ao1_visibility_gaps': """
            SELECT 
                hostname,
                found_in_tables,
                global_region,
                system_classification,
                CASE 
                    WHEN NOT in_splunk AND NOT in_chronicle THEN 'No Logging Coverage'
                    WHEN NOT has_crowdstrike AND NOT has_edr THEN 'No Security Tool Coverage'
                    ELSE 'Partial Coverage'
                END as gap_type
            FROM ao1_asset_inventory
            WHERE NOT (in_splunk AND in_chronicle AND has_crowdstrike)
            ORDER BY gap_type, global_region;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        if hasattr(self.client_manager, 'close_all'):
            self.client_manager.close_all()