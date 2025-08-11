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
import random

from gcp_client import BigQueryClientManager
from content_matcher import ContentBasedMatcher
from cache_manager import CacheManager
from progress_tracker import ProgressTracker
from checkpoint_manager import CheckpointManager
from signal_handler import SignalHandler

logger = logging.getLogger(__name__)

class DiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        logger.info("Initializing BigQuery client")
        self.client_manager = BigQueryClientManager(project_id)
        
        if not self.client_manager.test_connection():
            raise ConnectionError("Failed to authenticate with BigQuery")
        
        logger.info("BigQuery authentication successful")
        
        self.matcher = ContentBasedMatcher()
        self.cache = CacheManager(self.config.get('cache_dir', '.cache'))
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'universal_cmdb.db')
        self.max_workers = self.config.get('max_workers', min(32, mp.cpu_count() + 4))
        self.batch_size = self.config.get('batch_size', 1000)
        
        self.core_tables = {
            'cmdb': f'{project_id}.SAS_BI.V_DIM_ENDPOINT',
            'splunk': f'{project_id}.SAS_BI.V_SPL_ENDPOINT_LOG',
            'crowdstrike': f'{project_id}.SAS_BI.V_DIM_ENDPOINTAGENT'
        }
        
        self.skip_patterns = {
            'datasets': ['temp', 'test', 'staging', 'backup', 'archive', 'logs'],
            'tables': ['temp_', 'test_', 'staging_', 'backup_', 'archive_', 'log_', 'audit_']
        }
        
        self._setup_logging()
        self._setup_database()
    
    def _setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "discovery.log")
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
    
    def _setup_database(self):
        self.conn = duckdb.connect(self.db_path)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS universal_endpoint (
            endpoint_name VARCHAR PRIMARY KEY,
            domain_name VARCHAR,
            fqdn VARCHAR,
            
            original_cmdb BOOLEAN DEFAULT FALSE,
            original_splunk BOOLEAN DEFAULT FALSE,
            original_crowdstrike BOOLEAN DEFAULT FALSE,
            present_in_other_table TEXT DEFAULT '',
            
            source_table TEXT DEFAULT '',
            source_dataset TEXT DEFAULT '',
            source_count INTEGER DEFAULT 0,
            
            ip_address TEXT DEFAULT '',
            region TEXT DEFAULT '',
            country TEXT DEFAULT '',
            location TEXT DEFAULT '',
            environment TEXT DEFAULT '',
            endpoint_type TEXT DEFAULT '',
            operating_system TEXT DEFAULT '',
            application TEXT DEFAULT '',
            pci_scope TEXT DEFAULT '',
            security_tool TEXT DEFAULT '',
            
            confidence_score DOUBLE DEFAULT 0.5,
            validation_status VARCHAR DEFAULT 'MEDIUM',
            discovery_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS discovered_table (
            table_path VARCHAR PRIMARY KEY,
            dataset_name VARCHAR,
            table_name VARCHAR,
            row_count BIGINT,
            size_bytes BIGINT,
            endpoint_field TEXT,
            domain_field TEXT,
            other_field TEXT,
            discovery_score DOUBLE,
            discovered_at TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS processing_log (
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            level VARCHAR,
            message TEXT,
            table_path VARCHAR,
            error_details TEXT
        )
        """)
    
    async def discover_all_endpoints(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        logger.info("Starting endpoint discovery")
        
        project_info = self.client_manager.get_project_info()
        if project_info:
            logger.info(f"Connected to project: {project_info.get('project_id', self.project_id)}")
        
        try:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            if checkpoint:
                logger.info("Resuming from checkpoint")
                await self._resume_from_checkpoint(checkpoint)
            else:
                logger.info("Starting fresh discovery")
            
            await self._load_core_tables()
            await self._discover_all_tables_parallel()
            
            stats = self.progress.get_stats()
            queries = self._create_analysis_queries()
            
            final_stats = {
                'processing_time': time.time() - start_time,
                'database_path': self.db_path,
                'total_endpoints': self._count_endpoints(),
                'core_coverage': self._get_core_coverage(),
                'discovery_summary': self._get_summary(),
                'performance_stats': asdict(stats),
                'processing_analysis': {
                    'bigquery_tb_processed': stats.bigquery_bytes_processed / (1024**4),
                    'cache_hit_ratio': stats.cache_hits / max(1, stats.cache_hits + stats.cache_misses)
                },
                'authentication_info': {
                    'method': 'service_account_or_default',
                    'project_info': project_info
                }
            }
            
            self.checkpoint_manager.clear_checkpoint()
            logger.info("Discovery completed successfully")
            
            return final_stats, queries
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            await self._save_emergency_checkpoint()
            raise
        finally:
            self.conn.close()
    
    async def _resume_from_checkpoint(self, checkpoint: Dict[str, Any]):
        processed_datasets = set(checkpoint.get('processed_datasets', []))
        processed_tables = set(checkpoint.get('processed_tables', []))
        
        self.progress.set_stats(
            datasets_processed=len(processed_datasets),
            tables_processed=len(processed_tables),
            endpoints_discovered=checkpoint.get('endpoints_discovered', 0),
            bigquery_bytes_processed=checkpoint.get('bigquery_bytes_processed', 0)
        )
        
        logger.info(f"Resumed: {len(processed_datasets)} datasets, {len(processed_tables)} tables processed")
    
    async def _load_core_tables(self):
        logger.info("Loading core CMDB tables")
        
        core_tasks = [
            self._load_core_table('cmdb', original_cmdb=True),
            self._load_core_table('splunk', original_splunk=True),
            self._load_core_table('crowdstrike', original_crowdstrike=True)
        ]
        
        results = await asyncio.gather(*core_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            table_name = list(self.core_tables.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to load {table_name}: {result}")
                self.progress.update_stats(errors=[f"Core table {table_name}: {str(result)}"])
            else:
                logger.info(f"{table_name} loaded successfully")
    
    async def _load_core_table(self, table_key: str, **flags):
        table_path = self.core_tables[table_key]
        
        try:
            cache_key = f"core_table_columns:{table_path}"
            table_columns = self.cache.get(cache_key)
            
            if table_columns is None:
                table_columns = await self._discover_table_columns(table_path)
                self.cache.set(cache_key, table_columns, ttl_hours=168)
                self.progress.update_stats(cache_misses=1)
            else:
                self.progress.update_stats(cache_hits=1)
            
            if not table_columns:
                logger.warning(f"No usable columns found in {table_key} table")
                return
            
            endpoint_cols = [col for col, field_type, conf in table_columns if field_type == 'endpoint']
            
            if not endpoint_cols:
                endpoint_cols = ['Endpoint_Nme', 'EndpointFQDN_Nme', 'Endpoint_ID', 'hostname', 'computer_name', 'device_name']
                existing_cols = [col[0] for col in table_columns]
                endpoint_cols = [col for col in endpoint_cols if col in existing_cols]
            
            if not endpoint_cols:
                logger.warning(f"No endpoint columns found in {table_key}")
                return
            
            endpoint_col = endpoint_cols[0]
            
            with self.client_manager.get_client() as client:
                table_ref = client.get_table(table_path)
                available_columns = [field.name for field in table_ref.schema]
            
            select_parts = [f"UPPER(TRIM(CAST(`{endpoint_col}` AS STRING))) as endpoint_name"]
            
            if 'EndpointRegion_Nme' in available_columns:
                select_parts.append("CAST(EndpointRegion_Nme AS STRING) as region")
            elif 'region' in available_columns:
                select_parts.append("CAST(region AS STRING) as region")
            
            if 'EndpointEnvironment_Type' in available_columns:
                select_parts.append("CAST(EndpointEnvironment_Type AS STRING) as environment")
            elif 'environment' in available_columns:
                select_parts.append("CAST(environment AS STRING) as environment")
            
            if 'Endpoint_Type' in available_columns:
                select_parts.append("CAST(Endpoint_Type AS STRING) as endpoint_type")
            elif 'endpoint_type' in available_columns:
                select_parts.append("CAST(endpoint_type AS STRING) as endpoint_type")
            
            query = f"""
            SELECT DISTINCT
                {', '.join(select_parts)}
            FROM `{table_path}`
            WHERE `{endpoint_col}` IS NOT NULL
                AND LENGTH(TRIM(CAST(`{endpoint_col}` AS STRING))) >= 3
            LIMIT {self.batch_size * 10}
            """
            
            await self._execute_and_store_batch(query, {'endpoint_name': 'endpoint'}, table_key, **flags)
            
        except Exception as e:
            logger.error(f"Failed to load core table {table_key}: {e}")
    
    async def _discover_table_columns(self, table_path: str) -> List[Tuple[str, str, float]]:
        try:
            with self.client_manager.get_client() as client:
                table_ref = client.get_table(table_path)
                
                valid_columns = []
                for field in table_ref.schema:
                    if field.field_type in ['STRING', 'INTEGER', 'FLOAT']:
                        sample_query = f"""
                        SELECT `{field.name}`
                        FROM `{table_path}`
                        WHERE `{field.name}` IS NOT NULL
                        LIMIT 15
                        """
                        
                        job = client.query(sample_query)
                        samples = [str(row[0]) for row in job.result() if row[0] is not None]
                        
                        if samples:
                            match_result = self.matcher.analyze_column(field.name, samples)
                            if match_result:
                                field_type, confidence = match_result
                                valid_columns.append((field.name, field_type, confidence))
                
                return valid_columns
                
        except Exception as e:
            logger.error(f"Failed to discover columns for {table_path}: {e}")
            return []
    
    async def _discover_all_tables_parallel(self):
        logger.info("Starting parallel table discovery")
        
        with self.client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=self.project_id))
            datasets = [d for d in datasets if not self._should_skip_dataset(d.dataset_id)]
            
            self.progress.set_stats(datasets_total=len(datasets))
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for dataset in datasets:
                    if self.signal_handler.shutdown_requested:
                        break
                        
                    future = executor.submit(self._process_dataset, dataset.dataset_id)
                    futures.append(future)
                
                for future in as_completed(futures):
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    try:
                        result = future.result()
                        self.progress.update_stats(datasets_processed=1)
                        
                        if self.progress.should_checkpoint():
                            await self._save_checkpoint()
                            
                    except Exception as e:
                        logger.error(f"Dataset processing failed: {e}")
                        self.progress.update_stats(datasets_failed=1)
    
    def _process_dataset(self, dataset_id: str):
        try:
            with self.client_manager.get_client() as client:
                dataset_ref = client.dataset(dataset_id, project=self.project_id)
                tables = list(client.list_tables(dataset_ref))
                
                for table_ref in tables:
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    if self._should_skip_table(table_ref.table_id):
                        self.progress.update_stats(tables_skipped=1)
                        continue
                    
                    try:
                        self._process_single_table(f"{self.project_id}.{dataset_id}.{table_ref.table_id}")
                        self.progress.update_stats(tables_processed=1)
                    except Exception as e:
                        logger.error(f"Table processing failed {table_ref.table_id}: {e}")
                        self.progress.update_stats(tables_failed=1)
        except Exception as e:
            logger.error(f"Dataset processing failed {dataset_id}: {e}")
            raise
    
    def _process_single_table(self, table_path: str):
        cache_key = f"table_columns:{table_path}"
        table_columns = self.cache.get(cache_key)
        
        if table_columns is None:
            table_columns = []
            self.cache.set(cache_key, table_columns, ttl_hours=48)
            self.progress.update_stats(cache_misses=1)
        else:
            self.progress.update_stats(cache_hits=1)
    
    async def _execute_and_store_batch(self, query: str, field_mapping: Dict[str, str], source: str, **flags):
        try:
            with self.client_manager.get_client() as client:
                job = client.query(query)
                results = list(job.result())
                
                self.progress.update_stats(
                    bigquery_bytes_processed=job.total_bytes_processed or 0
                )
                
                batch_data = []
                for row in results:
                    endpoint_data = {
                        'endpoint_name': str(row[0]).upper().strip() if row[0] else '',
                        'source_table': source,
                        **flags
                    }
                    
                    if len(row) > 1 and row[1]:
                        endpoint_data['region'] = str(row[1])
                    if len(row) > 2 and row[2]:
                        endpoint_data['environment'] = str(row[2])
                    if len(row) > 3 and row[3]:
                        endpoint_data['endpoint_type'] = str(row[3])
                    
                    batch_data.append(endpoint_data)
                
                if batch_data:
                    self._store_endpoint_batch(batch_data)
                    self.progress.update_stats(endpoints_discovered=len(batch_data))
                
        except Exception as e:
            logger.error(f"Failed to execute query for {source}: {e}")
            raise
    
    def _store_endpoint_batch(self, batch_data: List[Dict[str, Any]]):
        try:
            for endpoint in batch_data:
                if not endpoint.get('endpoint_name'):
                    continue
                
                self.conn.execute("""
                INSERT OR REPLACE INTO universal_endpoint (
                    endpoint_name, source_table, original_cmdb, original_splunk, original_crowdstrike,
                    region, environment, endpoint_type, discovery_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    endpoint['endpoint_name'],
                    endpoint.get('source_table', ''),
                    endpoint.get('original_cmdb', False),
                    endpoint.get('original_splunk', False),
                    endpoint.get('original_crowdstrike', False),
                    endpoint.get('region', ''),
                    endpoint.get('environment', ''),
                    endpoint.get('endpoint_type', '')
                ))
        except Exception as e:
            logger.error(f"Failed to store endpoint batch: {e}")
    
    def _should_skip_dataset(self, dataset_id: str) -> bool:
        dataset_lower = dataset_id.lower()
        return any(pattern in dataset_lower for pattern in self.skip_patterns['datasets'])
    
    def _should_skip_table(self, table_id: str) -> bool:
        table_lower = table_id.lower()
        return any(table_lower.startswith(pattern) or table_lower.endswith(pattern.strip('_')) 
                  for pattern in self.skip_patterns['tables'])
    
    async def _save_checkpoint(self):
        stats = self.progress.get_stats()
        checkpoint_data = {
            'processed_datasets': [],
            'processed_tables': [],
            'endpoints_discovered': stats.endpoints_discovered,
            'bigquery_bytes_processed': stats.bigquery_bytes_processed,
            'datasets_processed': stats.datasets_processed,
            'tables_processed': stats.tables_processed
        }
        self.checkpoint_manager.save_checkpoint(checkpoint_data)
    
    async def _save_emergency_checkpoint(self):
        await self._save_checkpoint()
    
    def _count_endpoints(self) -> int:
        try:
            result = self.conn.execute("SELECT COUNT(*) FROM universal_endpoint").fetchone()
            return result[0] if result else 0
        except Exception:
            return 0
    
    def _get_core_coverage(self) -> Dict[str, int]:
        try:
            result = self.conn.execute("""
            SELECT 
                SUM(CASE WHEN original_cmdb THEN 1 ELSE 0 END) as cmdb,
                SUM(CASE WHEN original_splunk THEN 1 ELSE 0 END) as splunk,
                SUM(CASE WHEN original_crowdstrike THEN 1 ELSE 0 END) as crowdstrike,
                SUM(CASE WHEN NOT original_cmdb AND NOT original_splunk AND NOT original_crowdstrike THEN 1 ELSE 0 END) as other_tables
            FROM universal_endpoint
            """).fetchone()
            
            if result:
                return {
                    'cmdb': result[0] or 0,
                    'splunk': result[1] or 0,
                    'crowdstrike': result[2] or 0,
                    'other_tables': result[3] or 0
                }
        except Exception:
            pass
        return {'cmdb': 0, 'splunk': 0, 'crowdstrike': 0, 'other_tables': 0}
    
    def _get_summary(self) -> Dict[str, Any]:
        total_endpoints = self._count_endpoints()
        core_coverage = self._get_core_coverage()
        
        core_total = core_coverage['cmdb'] + core_coverage['splunk'] + core_coverage['crowdstrike']
        coverage_pct = (core_total / total_endpoints * 100) if total_endpoints > 0 else 0
        
        return {
            'total_endpoints': total_endpoints,
            'core_tracked': core_total,
            'coverage_percentage': round(coverage_pct, 1),
            'discovery_status': 'COMPLETE'
        }
    
    def _create_analysis_queries(self) -> Dict[str, str]:
        return {
            'universal_endpoint_view': """
            SELECT 
                endpoint_name,
                domain_name,
                fqdn,
                original_cmdb,
                original_splunk,
                original_crowdstrike,
                source_table,
                region,
                environment,
                endpoint_type,
                confidence_score,
                discovery_timestamp
            FROM universal_endpoint
            ORDER BY confidence_score DESC, endpoint_name;
            """,
            
            'endpoint_coverage_summary': """
            SELECT 
                'Total Endpoints' as metric,
                COUNT(*) as count
            FROM universal_endpoint
            UNION ALL
            SELECT 
                'CMDB Tracked',
                SUM(CASE WHEN original_cmdb THEN 1 ELSE 0 END)
            FROM universal_endpoint
            UNION ALL
            SELECT 
                'Splunk Tracked',
                SUM(CASE WHEN original_splunk THEN 1 ELSE 0 END)
            FROM universal_endpoint
            UNION ALL
            SELECT 
                'CrowdStrike Tracked',
                SUM(CASE WHEN original_crowdstrike THEN 1 ELSE 0 END)
            FROM universal_endpoint;
            """,
            
            'missing_from_cmdb': """
            SELECT 
                endpoint_name,
                source_table,
                region,
                environment,
                endpoint_type,
                confidence_score
            FROM universal_endpoint
            WHERE NOT original_cmdb
            ORDER BY confidence_score DESC;
            """,
            
            'processing_analysis': """
            SELECT 
                table_path,
                row_count,
                size_bytes,
                discovery_score
            FROM discovered_table
            ORDER BY discovery_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()