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
        self.max_workers = self.config.get('max_workers', min(16, mp.cpu_count()))
        self.batch_size = self.config.get('batch_size', 500)
        
        self.core_tables = {
            'cmdb': f'{project_id}.SAS_BI.V_DIM_ENDPOINT',
            'splunk': f'{project_id}.SAS_BI.V_SPL_ENDPOINT_LOG',
            'crowdstrike': f'{project_id}.SAS_BI.V_DIM_ENDPOINTAGENT'
        }
        
        self.skip_patterns = {
            'datasets': ['temp', 'test', 'staging', 'backup', 'archive'],
            'tables': ['temp_', 'test_', 'staging_', 'backup_', 'archive_']
        }
        
        self.processed_datasets = set()
        self.processed_tables = set()
        self._processing_lock = threading.Lock()
        
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
        logger.info("Starting comprehensive endpoint discovery")
        
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
            await self._discover_all_datasets_and_tables()
            
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
        self.processed_datasets = set(checkpoint.get('processed_datasets', []))
        self.processed_tables = set(checkpoint.get('processed_tables', []))
        
        self.progress.set_stats(
            datasets_processed=len(self.processed_datasets),
            tables_processed=len(self.processed_tables),
            endpoints_discovered=checkpoint.get('endpoints_discovered', 0),
            bigquery_bytes_processed=checkpoint.get('bigquery_bytes_processed', 0)
        )
        
        logger.info(f"Resumed: {len(self.processed_datasets)} datasets, {len(self.processed_tables)} tables processed")
    
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
                        try:
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
                        except Exception as col_e:
                            logger.debug(f"Failed to sample column {field.name}: {col_e}")
                            continue
                
                return valid_columns
                
        except Exception as e:
            logger.error(f"Failed to discover columns for {table_path}: {e}")
            return []
    
    async def _discover_all_datasets_and_tables(self):
        logger.info("Starting comprehensive discovery of ALL datasets and tables")
        
        with self.client_manager.get_client() as client:
            all_datasets = list(client.list_datasets(project=self.project_id))
            logger.info(f"Found {len(all_datasets)} total datasets in project")
            
            self.progress.set_stats(datasets_total=len(all_datasets))
            
            dataset_futures = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                for dataset in all_datasets:
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    if dataset.dataset_id in self.processed_datasets:
                        logger.info(f"Skipping already processed dataset: {dataset.dataset_id}")
                        continue
                    
                    logger.info(f"Queuing dataset for processing: {dataset.dataset_id}")
                    future = executor.submit(self._process_complete_dataset, dataset.dataset_id)
                    dataset_futures.append((future, dataset.dataset_id))
                
                for future, dataset_id in dataset_futures:
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    try:
                        result = future.result()
                        with self._processing_lock:
                            self.processed_datasets.add(dataset_id)
                        self.progress.update_stats(datasets_processed=1)
                        logger.info(f"Completed processing dataset: {dataset_id}")
                        
                        if self.progress.should_checkpoint():
                            await self._save_checkpoint()
                            
                    except Exception as e:
                        logger.error(f"Dataset processing failed for {dataset_id}: {e}")
                        self.progress.update_stats(datasets_failed=1)
    
    def _process_complete_dataset(self, dataset_id: str):
        logger.info(f"Processing ALL tables in dataset: {dataset_id}")
        
        try:
            with self.client_manager.get_client() as client:
                dataset_ref = client.dataset(dataset_id, project=self.project_id)
                all_tables = list(client.list_tables(dataset_ref))
                logger.info(f"Found {len(all_tables)} tables in dataset {dataset_id}")
                
                for table_ref in all_tables:
                    if self.signal_handler.shutdown_requested:
                        break
                    
                    table_full_path = f"{self.project_id}.{dataset_id}.{table_ref.table_id}"
                    
                    if table_full_path in self.processed_tables:
                        logger.debug(f"Skipping already processed table: {table_full_path}")
                        continue
                    
                    try:
                        logger.info(f"Processing table: {table_full_path}")
                        self._process_single_table_complete(table_full_path, dataset_id, table_ref.table_id)
                        
                        with self._processing_lock:
                            self.processed_tables.add(table_full_path)
                        self.progress.update_stats(tables_processed=1)
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Table processing failed {table_full_path}: {e}")
                        self.progress.update_stats(tables_failed=1)
                        
        except Exception as e:
            logger.error(f"Dataset processing failed {dataset_id}: {e}")
            raise
    
    def _process_single_table_complete(self, table_path: str, dataset_id: str, table_id: str):
        try:
            cache_key = f"table_analysis:{table_path}"
            cached_result = self.cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Using cached analysis for {table_path}")
                self.progress.update_stats(cache_hits=1)
                return cached_result
            
            with self.client_manager.get_client() as client:
                table_ref = client.get_table(table_path)
                
                table_info = {
                    'table_path': table_path,
                    'dataset_name': dataset_id,
                    'table_name': table_id,
                    'row_count': table_ref.num_rows or 0,
                    'size_bytes': table_ref.num_bytes or 0,
                    'endpoint_field': '',
                    'domain_field': '',
                    'other_field': '',
                    'discovery_score': 0.0
                }
                
                logger.debug(f"Analyzing table schema: {table_path}")
                
                for field in table_ref.schema:
                    if field.field_type == 'STRING':
                        try:
                            sample_query = f"""
                            SELECT `{field.name}`
                            FROM `{table_path}`
                            WHERE `{field.name}` IS NOT NULL
                            LIMIT 10
                            """
                            
                            job = client.query(sample_query)
                            samples = [str(row[0]) for row in job.result() if row[0] is not None]
                            
                            if samples:
                                match_result = self.matcher.analyze_column(field.name, samples)
                                if match_result:
                                    field_type, confidence = match_result
                                    table_info['discovery_score'] = max(table_info['discovery_score'], confidence)
                                    
                                    if field_type == 'endpoint' and not table_info['endpoint_field']:
                                        table_info['endpoint_field'] = field.name
                                        
                                        endpoint_query = f"""
                                        SELECT DISTINCT
                                            UPPER(TRIM(CAST(`{field.name}` AS STRING))) as endpoint_name
                                        FROM `{table_path}`
                                        WHERE `{field.name}` IS NOT NULL
                                            AND LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 3
                                        LIMIT {self.batch_size}
                                        """
                                        
                                        endpoint_job = client.query(endpoint_query)
                                        endpoint_results = list(endpoint_job.result())
                                        
                                        if endpoint_results:
                                            batch_data = []
                                            for row in endpoint_results:
                                                if row[0]:
                                                    batch_data.append({
                                                        'endpoint_name': str(row[0]).upper().strip(),
                                                        'source_table': table_path,
                                                        'source_dataset': dataset_id,
                                                        'original_cmdb': False,
                                                        'original_splunk': False,
                                                        'original_crowdstrike': False
                                                    })
                                            
                                            if batch_data:
                                                self._store_endpoint_batch(batch_data)
                                                self.progress.update_stats(endpoints_discovered=len(batch_data))
                                                logger.info(f"Found {len(batch_data)} endpoints in {table_path}")
                                    
                                    elif field_type == 'domain' and not table_info['domain_field']:
                                        table_info['domain_field'] = field.name
                        
                        except Exception as field_e:
                            logger.debug(f"Failed to analyze field {field.name} in {table_path}: {field_e}")
                            continue
                
                self._store_table_info(table_info)
                self.cache.set(cache_key, table_info, ttl_hours=24)
                self.progress.update_stats(cache_misses=1)
                
                return table_info
                
        except Exception as e:
            logger.error(f"Failed to process table {table_path}: {e}")
            return None
    
    def _store_table_info(self, table_info: Dict[str, Any]):
        try:
            self.conn.execute("""
            INSERT OR REPLACE INTO discovered_table (
                table_path, dataset_name, table_name, row_count, size_bytes,
                endpoint_field, domain_field, other_field, discovery_score, discovered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                table_info['table_path'],
                table_info['dataset_name'],
                table_info['table_name'],
                table_info['row_count'],
                table_info['size_bytes'],
                table_info['endpoint_field'],
                table_info['domain_field'],
                table_info['other_field'],
                table_info['discovery_score']
            ))
        except Exception as e:
            logger.error(f"Failed to store table info: {e}")
    
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
                    endpoint_name, source_table, source_dataset, original_cmdb, original_splunk, original_crowdstrike,
                    region, environment, endpoint_type, discovery_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    endpoint['endpoint_name'],
                    endpoint.get('source_table', ''),
                    endpoint.get('source_dataset', ''),
                    endpoint.get('original_cmdb', False),
                    endpoint.get('original_splunk', False),
                    endpoint.get('original_crowdstrike', False),
                    endpoint.get('region', ''),
                    endpoint.get('environment', ''),
                    endpoint.get('endpoint_type', '')
                ))
        except Exception as e:
            logger.error(f"Failed to store endpoint batch: {e}")
    
    async def _save_checkpoint(self):
        stats = self.progress.get_stats()
        checkpoint_data = {
            'processed_datasets': list(self.processed_datasets),
            'processed_tables': list(self.processed_tables),
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
                source_dataset,
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
                source_dataset,
                region,
                environment,
                endpoint_type,
                confidence_score
            FROM universal_endpoint
            WHERE NOT original_cmdb
            ORDER BY confidence_score DESC;
            """,
            
            'dataset_summary': """
            SELECT 
                dataset_name,
                COUNT(*) as table_count,
                SUM(row_count) as total_rows,
                SUM(size_bytes) as total_bytes,
                AVG(discovery_score) as avg_discovery_score
            FROM discovered_table
            GROUP BY dataset_name
            ORDER BY avg_discovery_score DESC;
            """,
            
            'processing_analysis': """
            SELECT 
                table_path,
                row_count,
                size_bytes,
                endpoint_field,
                domain_field,
                discovery_score
            FROM discovered_table
            WHERE discovery_score > 0
            ORDER BY discovery_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()