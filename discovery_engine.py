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
    def dataset(dataset_name: str, count: int, total: int):
        print(f"   ˚ ༘♡ ⋆｡˚   Dataset {count}/{total}: {dataset_name}")
    
    @staticmethod
    def table(table_name: str, endpoints_found: int = 0):
        if endpoints_found > 0:
            print(f"   ･ﾟ✧ ◞ ♡   Found {endpoints_found} endpoints in: {table_name}")
    
    @staticmethod
    def endpoint_merge(endpoint: str, table_count: int):
        print(f"   ♡˗ˏˋ ◞ ～   Merging {endpoint} from {table_count} sources")
    
    @staticmethod
    def progress(current: int, total: int, item_type: str):
        percentage = (current / total * 100) if total > 0 else 0
        print(f"   ✧･ﾟ: *✧･ﾟ:*   Progress: {current}/{total} {item_type} ({percentage:.1f}%)")
    
    @staticmethod
    def critical_source(source_name: str, count: int):
        print(f"   ♡₊˚ 🌸 ⋆｡˚   Critical source {source_name}: {count} endpoints")

class DiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*80)
        print("   ♡₊˚ 🦢 ✧ ‧₊˚ ⋅   AO1 Log Visibility Discovery Engine   ⋅ ˚₊‧ ✧ 🦢 ˚₊♡")
        print("="*80)
        PrettyLogger.info(f"Initializing brilliant discovery for project: {project_id}")
        
        self.client_manager = BigQueryClientManager(project_id)
        self.chronicle_client_manager = None
        
        if not self.client_manager.test_connection():
            raise ConnectionError("Failed to authenticate with BigQuery")
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
            if not self.chronicle_client_manager.test_connection():
                PrettyLogger.warning("Chronicle project authentication failed - continuing without Chronicle data")
                self.chronicle_client_manager = None
        except Exception as e:
            PrettyLogger.warning(f"Chronicle authentication failed: {e}")
            self.chronicle_client_manager = None
        
        PrettyLogger.success("BigQuery authentication successful")
        
        self.matcher = ContentBasedMatcher()
        self.cache = CacheManager(self.config.get('cache_dir', '.cache'))
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_visibility_cmdb.db')
        self.max_workers = min(4, self.config.get('max_workers', 4))
        
        self.critical_sources = {
            'cmdb': {
                'project': project_id,
                'dataset': 'SAS_BI',
                'table': 'V_DIM_ENDPOINT',
                'endpoint_column': 'Endpoint_Nme',
                'region_column': 'EndpointRegion_Nme',
                'environment_column': 'EndpointEnvironment_Type',
                'type_column': 'Endpoint_Type'
            },
            'crowdstrike': {
                'project': project_id,
                'dataset': 'SAS_BI', 
                'table': 'V_DIM_ENDPOINTAGENT',
                'endpoint_column': 'Endpoint_Nme',
                'region_column': 'EndpointRegion_Nme',
                'environment_column': 'EndpointEnvironment_Type'
            },
            'splunk': {
                'project': project_id,
                'dataset': 'SAS_BI',
                'table': 'V_SPL_ENDPOINT_LOG', 
                'endpoint_column': 'host_nme',
                'region_column': 'region',
                'environment_column': 'environment'
            },
            'chronicle': {
                'project': 'chronicle-fisv',
                'dataset': 'datalake',
                'table': 'events',
                'endpoint_column': 'principal.hostname',
                'region_column': 'network.ip_geo_artifact.location.region',
                'environment_column': 'metadata.description'
            }
        }
        
        self.processed_datasets = set()
        self.processed_tables = set()
        self._processing_lock = threading.Lock()
        self.dataset_counter = 0
        self.table_counter = 0
        self.endpoint_merge_stats = {}
        
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
            source_count INTEGER DEFAULT 1,
            
            visibility_score DOUBLE DEFAULT 0.0,
            last_log_seen TIMESTAMP,
            discovery_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_table_analytics (
            table_path VARCHAR PRIMARY KEY,
            dataset_name VARCHAR,
            table_name VARCHAR,
            row_count BIGINT,
            size_bytes BIGINT,
            endpoints_discovered INTEGER DEFAULT 0,
            endpoint_columns TEXT,
            is_partitioned BOOLEAN DEFAULT FALSE,
            partition_column VARCHAR,
            brilliance_score DOUBLE DEFAULT 0.0,
            processing_time_seconds DOUBLE DEFAULT 0.0,
            discovered_at TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ao1_visibility_metrics (
            metric_name VARCHAR PRIMARY KEY,
            metric_value DOUBLE,
            calculation_details TEXT,
            calculated_at TIMESTAMP DEFAULT NOW()
        )
        """)
    
    async def discover_all_endpoints(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting brilliant comprehensive asset discovery")
        
        try:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            if checkpoint:
                PrettyLogger.info("Resuming from checkpoint with brilliance")
                await self._resume_from_checkpoint(checkpoint)
            
            await self._load_critical_sources()
            await self._discover_all_datasets_brilliantly()
            await self._calculate_ao1_metrics()
            
            stats = self.progress.get_stats()
            queries = self._create_brilliant_analysis_queries()
            
            final_stats = {
                'processing_time': time.time() - start_time,
                'database_path': self.db_path,
                'total_endpoints': self._count_endpoints(),
                'visibility_coverage': self._get_visibility_coverage(),
                'discovery_summary': self._get_summary(),
                'performance_stats': asdict(stats),
                'brilliance_metrics': self._get_brilliance_metrics(),
                'endpoint_merge_stats': self.endpoint_merge_stats
            }
            
            self.checkpoint_manager.clear_checkpoint()
            PrettyLogger.success("Brilliant discovery completed successfully")
            
            return final_stats, queries
            
        except Exception as e:
            PrettyLogger.error(f"Discovery failed with error: {e}")
            await self._save_emergency_checkpoint()
            raise
        finally:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
    
    async def _resume_from_checkpoint(self, checkpoint: Dict[str, Any]):
        self.processed_datasets = set(checkpoint.get('processed_datasets', []))
        self.processed_tables = set(checkpoint.get('processed_tables', []))
        self.endpoint_merge_stats = checkpoint.get('endpoint_merge_stats', {})
        
        self.progress.set_stats(
            datasets_processed=len(self.processed_datasets),
            tables_processed=len(self.processed_tables),
            endpoints_discovered=checkpoint.get('endpoints_discovered', 0)
        )
    
    async def _load_critical_sources(self):
        PrettyLogger.info("Loading critical AO1 sources with precision")
        
        for source_name, source_config in self.critical_sources.items():
            try:
                await asyncio.sleep(random.uniform(1, 3))
                
                if source_config['project'] == 'chronicle-fisv':
                    if self.chronicle_client_manager is None:
                        PrettyLogger.warning(f"Skipping {source_name} - Chronicle client not available")
                        continue
                    client_manager = self.chronicle_client_manager
                else:
                    client_manager = self.client_manager
                
                endpoints_found = await self._load_critical_source(source_name, source_config, client_manager)
                PrettyLogger.critical_source(source_name, endpoints_found)
                
                await asyncio.sleep(2)
                
            except Exception as e:
                PrettyLogger.error(f"Failed to load critical source {source_name}: {e}")
                await asyncio.sleep(5)
    
    async def _load_critical_source(self, source_name: str, config: Dict[str, Any], client_manager: BigQueryClientManager) -> int:
        table_path = f"{config['project']}.{config['dataset']}.{config['table']}"
        
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            with client_manager.get_client() as client:
                try:
                    table_ref = client.get_table(table_path)
                    available_columns = [field.name for field in table_ref.schema]
                except Exception as e:
                    PrettyLogger.error(f"Failed to get table schema for {source_name}: {e}")
                    return 0
                
                if config['endpoint_column'] not in available_columns:
                    PrettyLogger.warning(f"Endpoint column {config['endpoint_column']} not found in {source_name}")
                    return 0
                
                select_parts = [f"UPPER(TRIM(CAST({config['endpoint_column']} AS STRING))) as hostname"]
                
                for col_key, col_name in [
                    ('region_column', 'global_region'),
                    ('environment_column', 'environment'),
                    ('type_column', 'system_classification')
                ]:
                    if col_key in config and config[col_key] in available_columns:
                        select_parts.append(f"CAST({config[col_key]} AS STRING) as {col_name}")
                
                is_partitioned = table_ref.time_partitioning is not None
                partition_filter = ""
                
                if is_partitioned and table_ref.time_partitioning.field:
                    partition_col = table_ref.time_partitioning.field
                    partition_filter = f"WHERE {partition_col} >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
                
                query = f"""
                SELECT DISTINCT {', '.join(select_parts)}
                FROM `{table_path}`
                {partition_filter}
                {" AND " if partition_filter else "WHERE"} {config['endpoint_column']} IS NOT NULL
                    AND LENGTH(TRIM(CAST({config['endpoint_column']} AS STRING))) >= 3
                    AND {config['endpoint_column']} NOT LIKE '%@%'
                    AND {config['endpoint_column']} NOT LIKE 'http%'
                LIMIT 50000
                """
                
                endpoints_found = await self._execute_and_store_endpoints(query, source_name, table_path, client_manager)
                return endpoints_found
                
        except Exception as e:
            PrettyLogger.error(f"Failed to load critical source {source_name}: {e}")
            return 0
    
    async def _discover_all_datasets_brilliantly(self):
        PrettyLogger.info("Discovering all datasets with brilliant analysis")
        
        try:
            with self.client_manager.get_client() as client:
                all_datasets = list(client.list_datasets(project=self.project_id))
        except Exception as e:
            PrettyLogger.error(f"Failed to list datasets: {e}")
            return
            
        filtered_datasets = [d for d in all_datasets if d.dataset_id not in self.processed_datasets]
        
        self.progress.set_stats(datasets_total=len(filtered_datasets))
        PrettyLogger.info(f"Found {len(filtered_datasets)} datasets to analyze brilliantly")
        
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_dataset_with_semaphore(dataset):
            async with semaphore:
                return await self._process_dataset_brilliantly(dataset.dataset_id)
        
        tasks = [process_dataset_with_semaphore(dataset) for dataset in filtered_datasets]
        
        for i, task in enumerate(asyncio.as_completed(tasks)):
            if self.signal_handler.shutdown_requested:
                break
            
            try:
                await task
                self.progress.update_stats(datasets_processed=1)
                
                if i % 3 == 0:
                    PrettyLogger.progress(i+1, len(filtered_datasets), "datasets")
                
                if self.progress.should_checkpoint():
                    await self._save_checkpoint()
                    
            except Exception as e:
                PrettyLogger.error(f"Dataset processing failed: {e}")
                self.progress.update_stats(datasets_failed=1)
                await asyncio.sleep(3)
    
    async def _process_dataset_brilliantly(self, dataset_id: str):
        try:
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            with self.client_manager.get_client() as client:
                dataset_ref = client.dataset(dataset_id, project=self.project_id)
                
                try:
                    all_tables = list(client.list_tables(dataset_ref))
                except Exception as e:
                    PrettyLogger.warning(f"Could not list tables in {dataset_id}: {e}")
                    return
                
                PrettyLogger.dataset(dataset_id, len(self.processed_datasets) + 1, self.progress.get_stats().datasets_total)
                
                table_tasks = []
                for table_ref in all_tables[:10]:
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    table_full_path = f"{self.project_id}.{dataset_id}.{table_ref.table_id}"
                    
                    if table_full_path in self.processed_tables:
                        continue
                    
                    table_tasks.append(self._analyze_table_brilliantly(table_full_path, dataset_id, table_ref.table_id))
                
                results = await asyncio.gather(*table_tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        PrettyLogger.error(f"Table analysis failed: {str(result)[:100]}")
                        self.progress.update_stats(tables_failed=1)
                    else:
                        endpoints_found = result
                        if endpoints_found > 0:
                            table_name = f"{dataset_id}.{all_tables[i].table_id}"
                            PrettyLogger.table(table_name, endpoints_found)
                        
                        self.progress.update_stats(tables_processed=1)
                
                with self._processing_lock:
                    self.processed_datasets.add(dataset_id)
                        
        except Exception as e:
            PrettyLogger.error(f"Dataset processing failed {dataset_id}: {e}")
            raise
    
    async def _analyze_table_brilliantly(self, table_path: str, dataset_id: str, table_id: str) -> int:
        start_time = time.time()
        
        with self._processing_lock:
            if table_path in self.processed_tables:
                return 0
            self.processed_tables.add(table_path)
        
        try:
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            with self.client_manager.get_client() as client:
                try:
                    table_ref = client.get_table(table_path)
                except Exception as e:
                    return 0
                
                is_partitioned = table_ref.time_partitioning is not None
                partition_filter = ""
                partition_column = None
                
                if is_partitioned and table_ref.time_partitioning.field:
                    partition_column = table_ref.time_partitioning.field
                    partition_filter = f"WHERE {partition_column} >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)"
                
                endpoints_found = 0
                endpoint_columns = []
                
                string_fields = [field for field in table_ref.schema if field.field_type == 'STRING'][:3]
                
                for field in string_fields:
                    if self.signal_handler.shutdown_requested:
                        break
                        
                    try:
                        sample_query = f"""
                        SELECT {field.name}
                        FROM `{table_path}`
                        {partition_filter}
                        {" AND " if partition_filter else "WHERE"} {field.name} IS NOT NULL
                            AND LENGTH(TRIM(CAST({field.name} AS STRING))) >= 3
                        LIMIT 10
                        """
                        
                        job = client.query(sample_query)
                        samples = [str(row[0]) for row in job.result() if row[0] is not None]
                        
                        if samples:
                            match_result = self.matcher.analyze_column(field.name, samples)
                            if match_result and match_result[0] == 'endpoint' and match_result[1] > 0.4:
                                endpoint_columns.append(field.name)
                                
                                endpoint_query = f"""
                                SELECT DISTINCT
                                    UPPER(TRIM(CAST({field.name} AS STRING))) as hostname
                                FROM `{table_path}`
                                {partition_filter}
                                {" AND " if partition_filter else "WHERE"} {field.name} IS NOT NULL
                                    AND LENGTH(TRIM(CAST({field.name} AS STRING))) >= 3
                                    AND {field.name} NOT LIKE '%@%'
                                    AND {field.name} NOT LIKE 'http%'
                                LIMIT 1000
                                """
                                
                                endpoint_job = client.query(endpoint_query)
                                endpoints = list(endpoint_job.result())
                                
                                for row in endpoints:
                                    if row[0] and len(str(row[0]).strip()) >= 3:
                                        await self._brilliant_endpoint_merge({
                                            'hostname': str(row[0]).upper().strip(),
                                            'found_in_tables': table_path,
                                            'source_dataset': dataset_id
                                        })
                                        endpoints_found += 1
                        
                        await asyncio.sleep(0.5)
                    
                    except Exception:
                        continue
                
                processing_time = time.time() - start_time
                brilliance_score = self._calculate_brilliance_score(endpoints_found, len(endpoint_columns), processing_time)
                
                await self._store_table_analytics({
                    'table_path': table_path,
                    'dataset_name': dataset_id,
                    'table_name': table_id,
                    'row_count': table_ref.num_rows or 0,
                    'size_bytes': table_ref.num_bytes or 0,
                    'endpoints_discovered': endpoints_found,
                    'endpoint_columns': ','.join(endpoint_columns),
                    'is_partitioned': is_partitioned,
                    'partition_column': partition_column,
                    'brilliance_score': brilliance_score,
                    'processing_time_seconds': processing_time
                })
                
                return endpoints_found
                
        except Exception as e:
            return 0
    
    def _calculate_brilliance_score(self, endpoints_found: int, endpoint_columns: int, processing_time: float) -> float:
        if endpoints_found == 0:
            return 0.0
        
        endpoint_score = min(endpoints_found / 1000.0, 1.0) * 0.5
        column_score = min(endpoint_columns / 5.0, 1.0) * 0.3
        efficiency_score = max(0, 1.0 - (processing_time / 60.0)) * 0.2
        
        return endpoint_score + column_score + efficiency_score
    
    async def _brilliant_endpoint_merge(self, endpoint_data: Dict[str, Any]):
        hostname = endpoint_data['hostname']
        
        existing = self.conn.execute(
            """SELECT found_in_tables, global_region, environment, system_classification, 
               source_count FROM ao1_asset_inventory WHERE hostname = ?""",
            (hostname,)
        ).fetchone()
        
        if existing:
            existing_tables = existing[0] or ""
            new_table = endpoint_data.get('found_in_tables', '')
            current_source_count = existing[4] or 1
            
            if new_table and new_table not in existing_tables:
                updated_tables = f"{existing_tables},{new_table}" if existing_tables else new_table
                new_source_count = current_source_count + 1
                
                update_fields = ["found_in_tables = ?", "source_count = ?"]
                update_values = [updated_tables, new_source_count]
                
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
                
                if new_source_count not in self.endpoint_merge_stats:
                    self.endpoint_merge_stats[new_source_count] = 0
                self.endpoint_merge_stats[new_source_count] += 1
                
                if new_source_count >= 3:
                    PrettyLogger.endpoint_merge(hostname, new_source_count)
        else:
            flags = {}
            table_str = endpoint_data.get('found_in_tables', '').lower()
            if 'v_dim_endpoint' in table_str:
                flags['found_in_cmdb'] = True
            if 'v_dim_endpointagent' in table_str or 'crowdstrike' in table_str:
                flags['has_crowdstrike'] = True
            if 'v_spl_endpoint_log' in table_str or 'splunk' in table_str:
                flags['in_splunk'] = True
            if 'chronicle' in table_str or 'events' in table_str:
                flags['in_chronicle'] = True
            
            self.conn.execute("""
            INSERT INTO ao1_asset_inventory (
                hostname, found_in_tables, global_region, environment, system_classification,
                found_in_cmdb, has_crowdstrike, in_splunk, in_chronicle, source_count,
                discovery_timestamp, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                hostname,
                endpoint_data.get('found_in_tables', ''),
                endpoint_data.get('global_region', ''),
                endpoint_data.get('environment', ''),
                endpoint_data.get('system_classification', ''),
                flags.get('found_in_cmdb', False),
                flags.get('has_crowdstrike', False),
                flags.get('in_splunk', False),
                flags.get('in_chronicle', False),
                1
            ))
            
            if 1 not in self.endpoint_merge_stats:
                self.endpoint_merge_stats[1] = 0
            self.endpoint_merge_stats[1] += 1
    
    async def _execute_and_store_endpoints(self, query: str, source: str, table_path: str, client_manager: BigQueryClientManager) -> int:
        try:
            with client_manager.get_client() as client:
                job = client.query(query)
                results = list(job.result())
                
                endpoints_stored = 0
                
                for row in results:
                    if row[0] and len(str(row[0]).strip()) >= 3:
                        endpoint_data = {'hostname': str(row[0]).upper().strip()}
                        
                        if len(row) > 1 and row[1]:
                            endpoint_data['global_region'] = str(row[1])
                        if len(row) > 2 and row[2]:
                            endpoint_data['environment'] = str(row[2])
                        if len(row) > 3 and row[3]:
                            endpoint_data['system_classification'] = str(row[3])
                        
                        endpoint_data['found_in_tables'] = table_path
                        
                        await self._brilliant_endpoint_merge(endpoint_data)
                        endpoints_stored += 1
                
                self.progress.update_stats(endpoints_discovered=endpoints_stored)
                return endpoints_stored
                
        except Exception as e:
            PrettyLogger.error(f"Failed to execute query for {source}: {e}")
            return 0
    
    async def _store_table_analytics(self, table_info: Dict[str, Any]):
        try:
            self.conn.execute("""
            INSERT OR REPLACE INTO ao1_table_analytics (
                table_path, dataset_name, table_name, row_count, size_bytes,
                endpoints_discovered, endpoint_columns, is_partitioned, partition_column,
                brilliance_score, processing_time_seconds, discovered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                table_info['table_path'],
                table_info['dataset_name'],
                table_info['table_name'],
                table_info['row_count'],
                table_info['size_bytes'],
                table_info['endpoints_discovered'],
                table_info['endpoint_columns'],
                table_info['is_partitioned'],
                table_info['partition_column'],
                table_info['brilliance_score'],
                table_info['processing_time_seconds']
            ))
        except Exception as e:
            PrettyLogger.error(f"Failed to store table analytics: {e}")
    
    async def _calculate_ao1_metrics(self):
        PrettyLogger.info("Calculating brilliant AO1 visibility metrics")
        
        metrics = {}
        
        try:
            result = self.conn.execute("""
            SELECT 
                COUNT(*) as total_assets,
                SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_covered,
                SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_covered,
                SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) as logging_covered,
                SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_covered,
                SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_covered,
                AVG(source_count) as avg_source_count
            FROM ao1_asset_inventory
            """).fetchone()
            
            if result and result[0] > 0:
                total = result[0]
                metrics['global_visibility_pct'] = (result[3] / total) * 100
                metrics['splunk_coverage_pct'] = (result[1] / total) * 100
                metrics['chronicle_coverage_pct'] = (result[2] / total) * 100
                metrics['crowdstrike_coverage_pct'] = (result[4] / total) * 100
                metrics['cmdb_coverage_pct'] = (result[5] / total) * 100
                metrics['avg_source_count'] = result[6] or 1.0
            
            for metric_name, metric_value in metrics.items():
                self.conn.execute("""
                INSERT OR REPLACE INTO ao1_visibility_metrics (metric_name, metric_value, calculated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (metric_name, metric_value))
            
            PrettyLogger.success(f"Calculated {len(metrics)} brilliant AO1 metrics")
            
        except Exception as e:
            PrettyLogger.error(f"Failed to calculate AO1 metrics: {e}")
    
    async def _save_checkpoint(self):
        stats = self.progress.get_stats()
        checkpoint_data = {
            'processed_datasets': list(self.processed_datasets),
            'processed_tables': list(self.processed_tables),
            'endpoints_discovered': stats.endpoints_discovered,
            'datasets_processed': stats.datasets_processed,
            'tables_processed': stats.tables_processed,
            'endpoint_merge_stats': self.endpoint_merge_stats
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
            SELECT metric_name, metric_value FROM ao1_visibility_metrics
            """).fetchall()
            
            return {row[0]: row[1] for row in result} if result else {}
        except Exception:
            return {}
    
    def _get_brilliance_metrics(self) -> Dict[str, Any]:
        try:
            result = self.conn.execute("""
            SELECT 
                COUNT(*) as tables_analyzed,
                SUM(endpoints_discovered) as total_endpoints_discovered,
                AVG(brilliance_score) as avg_brilliance_score,
                MAX(brilliance_score) as max_brilliance_score,
                SUM(processing_time_seconds) as total_processing_time
            FROM ao1_table_analytics
            """).fetchone()
            
            if result:
                return {
                    'tables_analyzed': result[0] or 0,
                    'total_endpoints_discovered': result[1] or 0,
                    'avg_brilliance_score': result[2] or 0.0,
                    'max_brilliance_score': result[3] or 0.0,
                    'total_processing_time': result[4] or 0.0
                }
        except Exception:
            pass
        return {}
    
    def _get_summary(self) -> Dict[str, Any]:
        total_endpoints = self._count_endpoints()
        coverage = self._get_visibility_coverage()
        brilliance = self._get_brilliance_metrics()
        
        return {
            'total_endpoints': total_endpoints,
            'visibility_coverage': coverage,
            'brilliance_metrics': brilliance,
            'endpoint_merge_stats': self.endpoint_merge_stats,
            'discovery_status': 'BRILLIANT_COMPLETE'
        }
    
    def _create_brilliant_analysis_queries(self) -> Dict[str, str]:
        return {
            'ao1_global_visibility_brilliant': """
            SELECT 
                COUNT(*) as total_assets,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as global_visibility_pct,
                AVG(source_count) as avg_sources_per_asset,
                MAX(source_count) as max_sources_per_asset
            FROM ao1_asset_inventory;
            """,
            
            'ao1_infrastructure_breakdown': """
            SELECT 
                COALESCE(system_classification, 'Unknown') as infrastructure_type,
                COUNT(*) as asset_count,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as visibility_pct,
                (SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as security_coverage_pct
            FROM ao1_asset_inventory
            GROUP BY system_classification
            ORDER BY visibility_pct DESC;
            """,
            
            'ao1_regional_brilliance': """
            SELECT 
                COALESCE(global_region, 'Unknown') as region,
                COUNT(*) as asset_count,
                (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as visibility_pct,
                AVG(source_count) as avg_sources_per_asset
            FROM ao1_asset_inventory
            WHERE global_region IS NOT NULL AND global_region != ''
            GROUP BY global_region
            ORDER BY visibility_pct DESC;
            """,
            
            'ao1_multi_source_assets': """
            SELECT 
                source_count,
                COUNT(*) as asset_count,
                (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ao1_asset_inventory)) as percentage
            FROM ao1_asset_inventory
            GROUP BY source_count
            ORDER BY source_count DESC;
            """,
            
            'ao1_visibility_gaps_critical': """
            SELECT 
                hostname,
                found_in_tables,
                global_region,
                system_classification,
                source_count,
                CASE 
                    WHEN NOT in_splunk AND NOT in_chronicle AND NOT found_in_cmdb THEN 'Critical Gap'
                    WHEN NOT in_splunk AND NOT in_chronicle THEN 'No Logging Coverage'
                    WHEN NOT has_crowdstrike THEN 'No Security Tool Coverage'
                    WHEN source_count = 1 THEN 'Single Source Risk'
                    ELSE 'Partial Coverage'
                END as gap_severity
            FROM ao1_asset_inventory
            WHERE NOT (in_splunk AND in_chronicle AND has_crowdstrike AND found_in_cmdb)
            ORDER BY 
                CASE gap_severity 
                    WHEN 'Critical Gap' THEN 1
                    WHEN 'No Logging Coverage' THEN 2
                    WHEN 'No Security Tool Coverage' THEN 3
                    WHEN 'Single Source Risk' THEN 4
                    ELSE 5
                END,
                source_count ASC;
            """,
            
            'ao1_brilliance_table_analytics': """
            SELECT 
                dataset_name,
                table_name,
                endpoints_discovered,
                brilliance_score,
                processing_time_seconds,
                endpoint_columns
            FROM ao1_table_analytics
            WHERE endpoints_discovered > 0
            ORDER BY brilliance_score DESC, endpoints_discovered DESC
            LIMIT 50;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()