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
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class ContentBasedAsset:
    hostname: str = ""
    all_data: Dict[str, Any] = field(default_factory=dict)
    source_tables: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)

class ContentAnalyzer:
    def __init__(self):
        self.hostname_validators = [
            self._is_hostname_pattern,
            self._is_server_name,
            self._is_endpoint_name,
            self._is_computer_name
        ]
        
        self.ip_validators = [
            self._is_ipv4_address,
            self._is_private_ip,
            self._is_public_ip
        ]
        
        self.fqdn_validators = [
            self._is_fqdn_pattern,
            self._is_domain_name
        ]
    
    def analyze_column_content(self, values: List[str]) -> Dict[str, float]:
        if not values:
            return {}
        
        clean_values = [str(v).strip() for v in values if v and str(v).strip()]
        if not clean_values:
            return {}
        
        scores = {
            'hostname': self._score_hostname_content(clean_values),
            'ip_address': self._score_ip_content(clean_values),
            'fqdn': self._score_fqdn_content(clean_values),
            'mac_address': self._score_mac_content(clean_values),
            'infrastructure_type': self._score_infrastructure_content(clean_values),
            'system_classification': self._score_system_content(clean_values),
            'region': self._score_region_content(clean_values),
            'business_unit': self._score_business_content(clean_values)
        }
        
        return {k: v for k, v in scores.items() if v > 0.3}
    
    def _score_hostname_content(self, values: List[str]) -> float:
        hostname_count = 0
        for value in values[:50]:
            for validator in self.hostname_validators:
                if validator(value):
                    hostname_count += 1
                    break
        
        return hostname_count / min(len(values), 50) if values else 0.0
    
    def _score_ip_content(self, values: List[str]) -> float:
        ip_count = 0
        for value in values[:50]:
            for validator in self.ip_validators:
                if validator(value):
                    ip_count += 1
                    break
        
        return ip_count / min(len(values), 50) if values else 0.0
    
    def _score_fqdn_content(self, values: List[str]) -> float:
        fqdn_count = 0
        for value in values[:50]:
            for validator in self.fqdn_validators:
                if validator(value):
                    fqdn_count += 1
                    break
        
        return fqdn_count / min(len(values), 50) if values else 0.0
    
    def _score_mac_content(self, values: List[str]) -> float:
        mac_count = sum(1 for v in values[:50] if self._is_mac_address(v))
        return mac_count / min(len(values), 50) if values else 0.0
    
    def _score_infrastructure_content(self, values: List[str]) -> float:
        infra_terms = ['cloud', 'onprem', 'on-prem', 'saas', 'api', 'physical', 'virtual', 'aws', 'azure', 'gcp']
        match_count = sum(1 for v in values[:50] if any(term in str(v).lower() for term in infra_terms))
        return match_count / min(len(values), 50) if values else 0.0
    
    def _score_system_content(self, values: List[str]) -> float:
        system_terms = ['windows', 'linux', 'unix', 'server', 'workstation', 'database', 'web', 'centos', 'ubuntu']
        match_count = sum(1 for v in values[:50] if any(term in str(v).lower() for term in system_terms))
        return match_count / min(len(values), 50) if values else 0.0
    
    def _score_region_content(self, values: List[str]) -> float:
        region_terms = ['us', 'usa', 'eu', 'europe', 'apac', 'asia', 'americas', 'emea', 'north', 'south', 'east', 'west']
        match_count = sum(1 for v in values[:50] if any(term in str(v).lower() for term in region_terms))
        return match_count / min(len(values), 50) if values else 0.0
    
    def _score_business_content(self, values: List[str]) -> float:
        business_terms = ['finance', 'marketing', 'sales', 'hr', 'it', 'operations', 'legal', 'compliance']
        match_count = sum(1 for v in values[:50] if any(term in str(v).lower() for term in business_terms))
        return match_count / min(len(values), 50) if values else 0.0
    
    def _is_hostname_pattern(self, value: str) -> bool:
        if not value or len(value) < 2 or len(value) > 253:
            return False
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', value)) or bool(re.match(r'^[a-zA-Z0-9]+$', value))
    
    def _is_server_name(self, value: str) -> bool:
        server_patterns = ['srv', 'server', 'web', 'app', 'db', 'sql', 'win', 'linux']
        return any(pattern in value.lower() for pattern in server_patterns)
    
    def _is_endpoint_name(self, value: str) -> bool:
        endpoint_patterns = ['pc', 'laptop', 'desktop', 'workstation', 'endpoint']
        return any(pattern in value.lower() for pattern in endpoint_patterns)
    
    def _is_computer_name(self, value: str) -> bool:
        return bool(re.match(r'^[A-Z0-9\-]+$', value)) and 3 <= len(value) <= 15
    
    def _is_ipv4_address(self, value: str) -> bool:
        try:
            addr = ipaddress.IPv4Address(value)
            return True
        except:
            return False
    
    def _is_private_ip(self, value: str) -> bool:
        try:
            addr = ipaddress.IPv4Address(value)
            return addr.is_private
        except:
            return False
    
    def _is_public_ip(self, value: str) -> bool:
        try:
            addr = ipaddress.IPv4Address(value)
            return not addr.is_private and not addr.is_loopback
        except:
            return False
    
    def _is_fqdn_pattern(self, value: str) -> bool:
        return '.' in value and bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', value))
    
    def _is_domain_name(self, value: str) -> bool:
        return '.' in value and len(value.split('.')) >= 2
    
    def _is_mac_address(self, value: str) -> bool:
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$'
        ]
        return any(re.match(pattern, value) for pattern in mac_patterns)

class ContentBasedCMDBBuilder:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager=None, content_matcher=None, intelligence_engine=None):
        self.project_id = project_id
        self.config = config
        
        from gcp_client import BigQueryClientManager
        self.client_manager = BigQueryClientManager(project_id)
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
        except:
            self.chronicle_client_manager = None
            logger.warning("Chronicle access not available")
        
        self.db_path = config.get('database_path', 'ao1_content_based_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        
        self.content_analyzer = ContentAnalyzer()
        self.shutdown_requested = False
        
        self.master_assets = {}
        self.processing_stats = {
            'datasets_scanned': 0,
            'tables_analyzed': 0,
            'columns_analyzed': 0,
            'hostname_columns_found': 0,
            'total_assets_discovered': 0,
            'processing_errors': 0
        }
        
        self._setup_content_based_schema()
        logger.info("Content-Based CMDB Builder initialized")
    
    def _setup_content_based_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS content_based_assets")
        
        self.conn.execute("""
            CREATE TABLE content_based_assets (
                asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                all_data JSON,
                source_tables JSON,
                confidence_scores JSON,
                total_sources INTEGER,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info("Content-based database schema created")
    
    async def execute_content_based_discovery(self, intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.info("Starting CONTENT-BASED discovery - analyzing ALL columns in ALL tables")
        start_time = datetime.now()
        
        try:
            logger.info("PHASE 1: Discovering all datasets")
            datasets = await self._discover_all_datasets()
            logger.info(f"Found {len(datasets)} datasets to scan")
            
            logger.info("PHASE 2: Analyzing content in ALL tables")
            await self._analyze_all_table_content(datasets)
            
            logger.info("PHASE 3: Merging data by hostname")
            merged_count = await self._merge_assets_by_hostname()
            
            logger.info("PHASE 4: Storing final assets")
            stored_count = await self._store_content_based_assets()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            final_stats = {
                'total_unique_assets': len(self.master_assets),
                'stored_assets': stored_count,
                'datasets_scanned': self.processing_stats['datasets_scanned'],
                'tables_analyzed': self.processing_stats['tables_analyzed'],
                'columns_analyzed': self.processing_stats['columns_analyzed'],
                'hostname_columns_found': self.processing_stats['hostname_columns_found'],
                'processing_time_seconds': processing_time,
                'processing_stats': self.processing_stats,
                'database_path': self.db_path
            }
            
            logger.info(f"Content-based discovery complete: {final_stats['total_unique_assets']} unique assets")
            return final_stats
            
        except Exception as e:
            logger.error(f"Content-based discovery failed: {e}")
            return {'error': str(e), 'processing_stats': self.processing_stats}
    
    async def _discover_all_datasets(self) -> List[Dict[str, str]]:
        datasets = []
        
        try:
            with self.client_manager.get_client() as client:
                project_datasets = list(client.list_datasets(project=self.project_id))
                
                for dataset in project_datasets:
                    datasets.append({
                        'project_id': self.project_id,
                        'dataset_id': dataset.dataset_id,
                        'client_manager': self.client_manager
                    })
                
                self.processing_stats['datasets_scanned'] += len(datasets)
        
        except Exception as e:
            logger.error(f"Failed to list main project datasets: {e}")
        
        if self.chronicle_client_manager:
            try:
                with self.chronicle_client_manager.get_client() as client:
                    chronicle_datasets = list(client.list_datasets(project="chronicle-fisv"))
                    
                    for dataset in chronicle_datasets:
                        datasets.append({
                            'project_id': "chronicle-fisv",
                            'dataset_id': dataset.dataset_id,
                            'client_manager': self.chronicle_client_manager
                        })
                    
                    self.processing_stats['datasets_scanned'] += len(chronicle_datasets)
            
            except Exception as e:
                logger.warning(f"Failed to list chronicle datasets: {e}")
        
        return datasets
    
    async def _analyze_all_table_content(self, datasets: List[Dict[str, str]]):
        for dataset_info in datasets:
            if self.shutdown_requested:
                break
            
            try:
                await self._analyze_dataset_content(dataset_info)
            except Exception as e:
                logger.error(f"Failed to analyze dataset {dataset_info['dataset_id']}: {e}")
                self.processing_stats['processing_errors'] += 1
    
    async def _analyze_dataset_content(self, dataset_info: Dict[str, str]):
        dataset_id = dataset_info['dataset_id']
        project_id = dataset_info['project_id']
        client_manager = dataset_info['client_manager']
        
        logger.info(f"Analyzing dataset: {project_id}.{dataset_id}")
        
        with client_manager.get_client() as client:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            for table_ref in tables:
                if self.shutdown_requested:
                    break
                
                try:
                    await self._analyze_table_content(client, project_id, dataset_id, table_ref.table_id)
                except Exception as e:
                    logger.warning(f"Failed to analyze table {table_ref.table_id}: {e}")
                    self.processing_stats['processing_errors'] += 1
    
    async def _analyze_table_content(self, client, project_id: str, dataset_id: str, table_id: str):
        table_path = f"{project_id}.{dataset_id}.{table_id}"
        
        try:
            full_table = client.get_table(table_path)
            
            if not full_table.schema or full_table.num_rows == 0:
                return
            
            columns = [field.name for field in full_table.schema]
            
            sample_query = f"""
            SELECT {', '.join([f'`{col}`' for col in columns])}
            FROM `{table_path}`
            LIMIT 200
            """
            
            job = client.query(sample_query)
            results = list(job.result())
            
            if not results:
                return
            
            column_data = {}
            for col_idx, column_name in enumerate(columns):
                column_values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        column_values.append(str(row[col_idx]))
                column_data[column_name] = column_values
            
            hostname_columns = []
            
            for column_name, values in column_data.items():
                self.processing_stats['columns_analyzed'] += 1
                
                content_scores = self.content_analyzer.analyze_column_content(values)
                
                if 'hostname' in content_scores and content_scores['hostname'] > 0.5:
                    hostname_columns.append({
                        'column_name': column_name,
                        'score': content_scores['hostname'],
                        'values': values
                    })
                    self.processing_stats['hostname_columns_found'] += 1
            
            if hostname_columns:
                logger.info(f"Found {len(hostname_columns)} hostname columns in {table_path}")
                await self._extract_assets_from_table(table_path, hostname_columns, column_data, client)
            
            self.processing_stats['tables_analyzed'] += 1
        
        except Exception as e:
            logger.warning(f"Content analysis failed for {table_path}: {e}")
    
    async def _extract_assets_from_table(self, table_path: str, hostname_columns: List[Dict], all_column_data: Dict[str, List], client):
        for hostname_col_info in hostname_columns:
            hostname_col = hostname_col_info['column_name']
            
            try:
                query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{hostname_col}` IS NOT NULL
                AND TRIM(`{hostname_col}`) != ''
                LIMIT 50000
                """
                
                job = client.query(query)
                results = list(job.result())
                
                table_ref = client.get_table(table_path)
                columns = [field.name for field in table_ref.schema]
                
                for row in results:
                    hostname_idx = columns.index(hostname_col)
                    if hostname_idx < len(row) and row[hostname_idx]:
                        hostname = str(row[hostname_idx]).strip().upper()
                        
                        if not hostname or len(hostname) < 1:
                            continue
                        
                        if hostname in ['NULL', 'NONE', 'UNKNOWN', '']:
                            continue
                        
                        if hostname not in self.master_assets:
                            self.master_assets[hostname] = ContentBasedAsset(hostname=hostname)
                        
                        asset = self.master_assets[hostname]
                        
                        for col_idx, column_name in enumerate(columns):
                            if col_idx < len(row) and row[col_idx] is not None:
                                value = str(row[col_idx]).strip()
                                if value and value != hostname:
                                    if column_name not in asset.all_data:
                                        asset.all_data[column_name] = set()
                                    asset.all_data[column_name].add(value)
                        
                        if table_path not in asset.source_tables:
                            asset.source_tables.append(table_path)
                        
                        self.processing_stats['total_assets_discovered'] += 1
                
                logger.info(f"Extracted assets from {table_path} using column {hostname_col}")
            
            except Exception as e:
                logger.error(f"Failed to extract from {table_path}: {e}")
    
    async def _merge_assets_by_hostname(self) -> int:
        logger.info(f"Merging {len(self.master_assets)} assets by hostname")
        
        for hostname, asset in self.master_assets.items():
            for field_name, value_set in asset.all_data.items():
                asset.all_data[field_name] = list(value_set)
        
        return len(self.master_assets)
    
    async def _store_content_based_assets(self) -> int:
        stored_count = 0
        
        insert_query = """
        INSERT INTO content_based_assets (
            asset_id, hostname, all_data, source_tables, confidence_scores, total_sources, discovery_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, NOW())
        """
        
        for hostname, asset in self.master_assets.items():
            try:
                asset_id = f"asset_{hashlib.md5(hostname.encode()).hexdigest()[:12]}"
                
                values = [
                    asset_id,
                    hostname,
                    json.dumps(asset.all_data, default=str),
                    json.dumps(asset.source_tables),
                    json.dumps(asset.confidence_scores),
                    len(asset.source_tables)
                ]
                
                self.conn.execute(insert_query, values)
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store asset {hostname}: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} content-based assets")
        return stored_count
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        logger.info("Content-Based CMDB Builder closed")