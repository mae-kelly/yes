# discovery/content.py

import asyncio
import logging
import hashlib
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from core.types import Asset
from ai.content import ContentAnalyzer

logger = logging.getLogger(__name__)

class ContentBasedEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.analyzer = ContentAnalyzer()
        
        self.discovered_assets = {}
        self.stats = {
            'datasets_scanned': 0,
            'tables_analyzed': 0,
            'columns_analyzed': 0,
            'hostname_columns_found': 0,
            'total_assets_discovered': 0,
            'processing_errors': 0
        }
    
    async def discover_all_content(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting content-based discovery across all tables")
        start_time = datetime.now()
        
        try:
            datasets = await self._discover_datasets(client_managers)
            await self._analyze_all_content(datasets)
            merged_count = await self._merge_by_hostname()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'total_unique_assets': len(self.discovered_assets),
                'datasets_scanned': self.stats['datasets_scanned'],
                'tables_analyzed': self.stats['tables_analyzed'],
                'columns_analyzed': self.stats['columns_analyzed'],
                'hostname_columns_found': self.stats['hostname_columns_found'],
                'processing_time_seconds': processing_time,
                'assets': self.discovered_assets
            }
            
        except Exception as e:
            logger.error(f"Content-based discovery failed: {e}")
            return {'error': str(e), 'stats': self.stats}
    
    async def _discover_datasets(self, client_managers: Dict[str, Any]) -> List[Dict[str, Any]]:
        datasets = []
        
        for project_id, client_manager in client_managers.items():
            try:
                with client_manager.get_client() as client:
                    project_datasets = list(client.list_datasets(project=project_id))
                    
                    for dataset in project_datasets:
                        datasets.append({
                            'project_id': project_id,
                            'dataset_id': dataset.dataset_id,
                            'client_manager': client_manager
                        })
                
                self.stats['datasets_scanned'] += len(project_datasets)
                
            except Exception as e:
                logger.error(f"Failed to list datasets for {project_id}: {e}")
                self.stats['processing_errors'] += 1
        
        return datasets
    
    async def _analyze_all_content(self, datasets: List[Dict[str, Any]]):
        for dataset_info in datasets:
            try:
                await self._analyze_dataset_content(dataset_info)
            except Exception as e:
                logger.error(f"Failed to analyze dataset {dataset_info['dataset_id']}: {e}")
                self.stats['processing_errors'] += 1
    
    async def _analyze_dataset_content(self, dataset_info: Dict[str, Any]):
        dataset_id = dataset_info['dataset_id']
        project_id = dataset_info['project_id']
        client_manager = dataset_info['client_manager']
        
        logger.debug(f"Analyzing dataset: {project_id}.{dataset_id}")
        
        with client_manager.get_client() as client:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            for table_ref in tables:
                try:
                    await self._analyze_table_content(client, project_id, dataset_id, table_ref.table_id)
                except Exception as e:
                    logger.warning(f"Failed to analyze table {table_ref.table_id}: {e}")
                    self.stats['processing_errors'] += 1
    
    async def _analyze_table_content(self, client, project_id: str, dataset_id: str, table_id: str):
        table_path = f"{project_id}.{dataset_id}.{table_id}"
        
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return
            
            columns = [field.name for field in table.schema]
            column_samples = await self._sample_table_columns(client, table_path, columns)
            
            hostname_columns = []
            
            for column_name, samples in column_samples.items():
                self.stats['columns_analyzed'] += 1
                
                if self._is_hostname_column(column_name, samples):
                    hostname_columns.append({
                        'column': column_name,
                        'confidence': 0.95,
                        'samples': samples
                    })
                    self.stats['hostname_columns_found'] += 1
                else:
                    analysis = self.analyzer.analyze_column(column_name, samples)
                    
                    if analysis and analysis[0] == 'hostname' and analysis[1] > 0.5:
                        hostname_columns.append({
                            'column': column_name,
                            'confidence': analysis[1],
                            'samples': samples
                        })
                        self.stats['hostname_columns_found'] += 1
            
            if hostname_columns:
                await self._extract_assets_from_table(client, table_path, hostname_columns, column_samples)
            
            self.stats['tables_analyzed'] += 1
            
        except Exception as e:
            logger.warning(f"Content analysis failed for {table_path}: {e}")
    
    def _is_hostname_column(self, column_name: str, samples: List[str]) -> bool:
        name_lower = column_name.lower()
        hostname_indicators = ['hostname', 'host', 'computername', 'endpoint', 'device', 'machine', 'computer']
        
        for indicator in hostname_indicators:
            if indicator in name_lower:
                return True
        
        if not samples:
            return False
        
        hostname_count = 0
        for sample in samples[:20]:
            if self._looks_like_hostname(sample):
                hostname_count += 1
        
        return (hostname_count / min(len(samples), 20)) > 0.7
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)
    
    async def _sample_table_columns(self, client, table_path: str, columns: List[str]) -> Dict[str, List[str]]:
        sample_query = f"""
        SELECT {', '.join([f'`{col}`' for col in columns])}
        FROM `{table_path}`
        WHERE RAND() < 0.01
        LIMIT 200
        """
        
        column_data = {}
        try:
            job = client.query(sample_query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(columns):
                values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        values.append(str(row[col_idx]))
                column_data[column_name] = values
        
        except Exception as e:
            logger.warning(f"Sampling failed for {table_path}: {e}")
        
        return column_data
    
    async def _extract_assets_from_table(self, client, table_path: str, 
                                       hostname_columns: List[Dict], all_columns: Dict[str, List[str]]):
        
        for hostname_col_info in hostname_columns:
            hostname_col = hostname_col_info['column']
            
            try:
                query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{hostname_col}` IS NOT NULL
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
                        
                        if hostname not in self.discovered_assets:
                            self.discovered_assets[hostname] = {
                                'hostname': hostname,
                                'all_data': defaultdict(set),
                                'source_tables': [],
                                'confidence_scores': {},
                                'source_count': 0
                            }
                        
                        asset = self.discovered_assets[hostname]
                        
                        for col_idx, column_name in enumerate(columns):
                            if col_idx < len(row) and row[col_idx] is not None:
                                value = str(row[col_idx]).strip()
                                if value and value != hostname:
                                    asset['all_data'][column_name].add(value)
                        
                        if table_path not in asset['source_tables']:
                            asset['source_tables'].append(table_path)
                            asset['source_count'] += 1
                        
                        self.stats['total_assets_discovered'] += 1
                
            except Exception as e:
                logger.error(f"Failed to extract from {table_path}: {e}")
    
    async def _merge_by_hostname(self) -> int:
        logger.info(f"Merging {len(self.discovered_assets)} assets by hostname")
        
        for hostname, asset in self.discovered_assets.items():
            for field_name, value_set in asset['all_data'].items():
                asset['all_data'][field_name] = list(value_set)
        
        return len(self.discovered_assets)

class SmartColumnDetector:
    def __init__(self):
        self.hostname_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        self.hostname_indicators = ['srv', 'web', 'app', 'db', 'sql', 'host', 'server', 'pc', 'ws']
    
    def detect_hostname_columns(self, table_samples: Dict[str, List[str]]) -> List[Tuple[str, float]]:
        candidates = []
        
        for column_name, samples in table_samples.items():
            if not samples:
                continue
            
            name_score = self._score_column_name(column_name)
            content_score = self._score_content(samples)
            
            combined_score = (name_score * 0.4) + (content_score * 0.6)
            
            if combined_score > 0.5:
                candidates.append((column_name, combined_score))
        
        return sorted(candidates, key=lambda x: x[1], reverse=True)
    
    def _score_column_name(self, name: str) -> float:
        name_lower = name.lower()
        
        exact_matches = ['hostname', 'host', 'computername', 'endpoint', 'device', 'server', 'machine']
        for match in exact_matches:
            if match in name_lower:
                return min(1.0, len(match) / len(name_lower))
        
        return 0.0
    
    def _score_content(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = 0
        for sample in samples[:20]:
            if self._looks_like_hostname(sample):
                hostname_count += 1
        
        return hostname_count / min(len(samples), 20)
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        for pattern in self.hostname_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                return True
        
        value_lower = value.lower()
        if any(indicator in value_lower for indicator in self.hostname_indicators):
            return True
        
        return False

class UniversalTableScanner:
    def __init__(self, content_analyzer: ContentAnalyzer):
        self.analyzer = content_analyzer
        self.detector = SmartColumnDetector()
        self.processed_tables = set()
    
    async def scan_all_tables(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        all_assets = {}
        table_count = 0
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                for dataset in datasets:
                    dataset_ref = client.dataset(dataset.dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        if table_path in self.processed_tables:
                            continue
                        
                        try:
                            assets = await self._scan_single_table(client, table_path)
                            
                            for asset_id, asset in assets.items():
                                if asset_id in all_assets:
                                    all_assets[asset_id] = self._merge_asset_data(
                                        all_assets[asset_id], asset
                                    )
                                else:
                                    all_assets[asset_id] = asset
                            
                            table_count += 1
                            self.processed_tables.add(table_path)
                            
                        except Exception as e:
                            logger.warning(f"Failed to scan {table_path}: {e}")
        
        return {
            'assets': all_assets,
            'tables_scanned': table_count,
            'unique_assets': len(all_assets)
        }
    
    async def _scan_single_table(self, client, table_path: str) -> Dict[str, Any]:
        table = client.get_table(table_path)
        
        if not table.schema or table.num_rows == 0:
            return {}
        
        columns = [field.name for field in table.schema]
        samples = await self._sample_columns(client, table_path, columns)
        
        hostname_candidates = self.detector.detect_hostname_columns(samples)
        
        if not hostname_candidates:
            return {}
        
        best_hostname_col = hostname_candidates[0][0]
        return await self._extract_from_hostname_column(client, table_path, best_hostname_col, samples)
    
    async def _sample_columns(self, client, table_path: str, columns: List[str]) -> Dict[str, List[str]]:
        limited_columns = columns[:30]
        
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in limited_columns])}
        FROM `{table_path}`
        WHERE RAND() < 0.02
        LIMIT 300
        """
        
        samples = {}
        try:
            job = client.query(query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(limited_columns):
                values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        values.append(str(row[col_idx]))
                samples[column_name] = values
        
        except Exception as e:
            logger.warning(f"Sampling failed for {table_path}: {e}")
        
        return samples
    
    async def _extract_from_hostname_column(self, client, table_path: str, 
                                          hostname_col: str, samples: Dict[str, List[str]]) -> Dict[str, Any]:
        query = f"""
        SELECT *
        FROM `{table_path}`
        WHERE `{hostname_col}` IS NOT NULL
        LIMIT 25000
        """
        
        assets = {}
        try:
            job = client.query(query)
            results = list(job.result())
            
            table = client.get_table(table_path)
            all_columns = [field.name for field in table.schema]
            hostname_idx = all_columns.index(hostname_col)
            
            for row in results:
                if hostname_idx < len(row) and row[hostname_idx]:
                    hostname = str(row[hostname_idx]).strip().upper()
                    
                    if not hostname or len(hostname) < 1:
                        continue
                    
                    asset_id = f"content_{hashlib.md5(hostname.encode()).hexdigest()[:12]}"
                    
                    if asset_id not in assets:
                        assets[asset_id] = {
                            'hostname': hostname,
                            'source_tables': [table_path],
                            'all_data': {},
                            'source_count': 1
                        }
                    
                    asset = assets[asset_id]
                    
                    for col_idx, column_name in enumerate(all_columns):
                        if col_idx < len(row) and row[col_idx] is not None:
                            value = str(row[col_idx]).strip()
                            if value and value != hostname:
                                if column_name not in asset['all_data']:
                                    asset['all_data'][column_name] = []
                                if value not in asset['all_data'][column_name]:
                                    asset['all_data'][column_name].append(value)
        
        except Exception as e:
            logger.error(f"Extraction failed for {table_path}: {e}")
        
        return assets
    
    def _merge_asset_data(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        for table in secondary['source_tables']:
            if table not in merged['source_tables']:
                merged['source_tables'].append(table)
                merged['source_count'] += 1
        
        for field_name, values in secondary['all_data'].items():
            if field_name not in merged['all_data']:
                merged['all_data'][field_name] = []
            
            for value in values:
                if value not in merged['all_data'][field_name]:
                    merged['all_data'][field_name].append(value)
        
        return merged