import asyncio
import logging
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from core.types import HyperAsset
from ai.content import QuantumContentAnalyzer

logger = logging.getLogger(__name__)

class QuantumContentBasedEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.quantum_cache = cache_manager
        self.quantum_intelligence = intelligence
        self.quantum_analyzer = QuantumContentAnalyzer()
        
        self.quantum_discovered_assets = {}
        self.quantum_stats = {
            'datasets_scanned': 0,
            'tables_analyzed': 0,
            'columns_analyzed': 0,
            'quantum_hostname_columns_found': 0,
            'total_quantum_assets_discovered': 0,
            'quantum_processing_errors': 0,
            'quantum_emergence_events': 0
        }
    
    async def discover_all_quantum_content(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting quantum content-based discovery across all tables")
        start_time = datetime.now()
        
        try:
            quantum_datasets = await self._discover_quantum_datasets(client_managers)
            await self._analyze_all_quantum_content(quantum_datasets)
            quantum_merged_count = await self._merge_by_quantum_hostname()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'total_unique_quantum_assets': len(self.quantum_discovered_assets),
                'quantum_datasets_scanned': self.quantum_stats['datasets_scanned'],
                'quantum_tables_analyzed': self.quantum_stats['tables_analyzed'],
                'quantum_columns_analyzed': self.quantum_stats['columns_analyzed'],
                'quantum_hostname_columns_found': self.quantum_stats['quantum_hostname_columns_found'],
                'quantum_processing_time_seconds': processing_time,
                'quantum_assets': self.quantum_discovered_assets,
                'quantum_emergence_events': self.quantum_stats['quantum_emergence_events']
            }
            
        except Exception as e:
            logger.error(f"Quantum content-based discovery failed: {e}")
            return {'error': str(e), 'quantum_stats': self.quantum_stats}
    
    async def _discover_quantum_datasets(self, client_managers: Dict[str, Any]) -> List[Dict[str, Any]]:
        quantum_datasets = []
        
        for project_id, client_manager in client_managers.items():
            try:
                with client_manager.get_client() as client:
                    project_datasets = list(client.list_datasets(project=project_id))
                    
                    for dataset in project_datasets:
                        quantum_datasets.append({
                            'project_id': project_id,
                            'dataset_id': dataset.dataset_id,
                            'client_manager': client_manager
                        })
                
                self.quantum_stats['datasets_scanned'] += len(project_datasets)
                
            except Exception as e:
                logger.error(f"Failed to list quantum datasets for {project_id}: {e}")
                self.quantum_stats['quantum_processing_errors'] += 1
        
        return quantum_datasets
    
    async def _analyze_all_quantum_content(self, quantum_datasets: List[Dict[str, Any]]):
        for dataset_info in quantum_datasets:
            try:
                await self._analyze_quantum_dataset_content(dataset_info)
            except Exception as e:
                logger.error(f"Failed to analyze quantum dataset {dataset_info['dataset_id']}: {e}")
                self.quantum_stats['quantum_processing_errors'] += 1
    
    async def _analyze_quantum_dataset_content(self, dataset_info: Dict[str, Any]):
        dataset_id = dataset_info['dataset_id']
        project_id = dataset_info['project_id']
        client_manager = dataset_info['client_manager']
        
        logger.debug(f"Quantum analyzing dataset: {project_id}.{dataset_id}")
        
        with client_manager.get_client() as client:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            for table_ref in tables:
                try:
                    await self._analyze_quantum_table_content(client, project_id, dataset_id, table_ref.table_id)
                except Exception as e:
                    logger.warning(f"Failed to quantum analyze table {table_ref.table_id}: {e}")
                    self.quantum_stats['quantum_processing_errors'] += 1
    
    async def _analyze_quantum_table_content(self, client, project_id: str, dataset_id: str, table_id: str):
        table_path = f"{project_id}.{dataset_id}.{table_id}"
        
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return
            
            columns = [field.name for field in table.schema]
            quantum_column_samples = await self._sample_quantum_table_columns(client, table_path, columns)
            
            quantum_hostname_columns = []
            
            for column_name, samples in quantum_column_samples.items():
                self.quantum_stats['columns_analyzed'] += 1
                
                if self._is_quantum_hostname_column(column_name, samples):
                    quantum_hostname_columns.append({
                        'column': column_name,
                        'confidence': 0.98,
                        'samples': samples,
                        'quantum_enhanced': True
                    })
                    self.quantum_stats['quantum_hostname_columns_found'] += 1
                else:
                    quantum_analysis = self.quantum_analyzer.analyze_column_quantum_intelligently(column_name, samples)
                    
                    if quantum_analysis and quantum_analysis[0] == 'hostname' and quantum_analysis[1] > 0.6:
                        quantum_hostname_columns.append({
                            'column': column_name,
                            'confidence': quantum_analysis[1],
                            'samples': samples,
                            'quantum_metadata': quantum_analysis[2]
                        })
                        self.quantum_stats['quantum_hostname_columns_found'] += 1
                        
                        if quantum_analysis[2].get('emergence_probability', 0) > 0.8:
                            self.quantum_stats['quantum_emergence_events'] += 1
            
            if quantum_hostname_columns:
                await self._extract_quantum_assets_from_table(client, table_path, quantum_hostname_columns, quantum_column_samples)
            
            self.quantum_stats['tables_analyzed'] += 1
            
        except Exception as e:
            logger.warning(f"Quantum content analysis failed for {table_path}: {e}")
    
    def _is_quantum_hostname_column(self, column_name: str, samples: List[str]) -> bool:
        name_lower = column_name.lower()
        quantum_hostname_indicators = [
            'hostname', 'host', 'computername', 'endpoint', 'device', 'machine', 'computer',
            'asset', 'equipment', 'system', 'node', 'workstation', 'server'
        ]
        
        for indicator in quantum_hostname_indicators:
            if indicator in name_lower:
                return True
        
        if not samples:
            return False
        
        quantum_hostname_count = 0
        for sample in samples[:25]:
            if self._looks_like_quantum_hostname(sample):
                quantum_hostname_count += 1
        
        return (quantum_hostname_count / min(len(samples), 25)) > 0.75
    
    def _looks_like_quantum_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n', '|', ';']):
            return False
        
        quantum_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9],
            r'^[a-zA-Z0-9]+
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in quantum_patterns)
    
    async def _sample_quantum_table_columns(self, client, table_path: str, columns: List[str]) -> Dict[str, List[str]]:
        quantum_sample_query = f"""
        SELECT {', '.join([f'`{col}`' for col in columns])}
        FROM `{table_path}`
        WHERE RAND() < 0.015
        LIMIT 300
        """
        
        quantum_column_data = {}
        try:
            job = client.query(quantum_sample_query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(columns):
                values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        values.append(str(row[col_idx]))
                quantum_column_data[column_name] = values
        
        except Exception as e:
            logger.warning(f"Quantum sampling failed for {table_path}: {e}")
        
        return quantum_column_data
    
    async def _extract_quantum_assets_from_table(self, client, table_path: str, 
                                               quantum_hostname_columns: List[Dict], quantum_all_columns: Dict[str, List[str]]):
        
        for quantum_hostname_col_info in quantum_hostname_columns:
            quantum_hostname_col = quantum_hostname_col_info['column']
            
            try:
                quantum_query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{quantum_hostname_col}` IS NOT NULL
                LIMIT 75000
                """
                
                job = client.query(quantum_query)
                results = list(job.result())
                
                table_ref = client.get_table(table_path)
                columns = [field.name for field in table_ref.schema]
                
                for row in results:
                    hostname_idx = columns.index(quantum_hostname_col)
                    if hostname_idx < len(row) and row[hostname_idx]:
                        quantum_hostname = str(row[hostname_idx]).strip().upper()
                        
                        if not quantum_hostname or len(quantum_hostname) < 1:
                            continue
                        
                        if quantum_hostname in ['NULL', 'NONE', 'UNKNOWN', '', 'N/A', 'NIL']:
                            continue
                        
                        if quantum_hostname not in self.quantum_discovered_assets:
                            self.quantum_discovered_assets[quantum_hostname] = {
                                'quantum_hostname': quantum_hostname,
                                'quantum_all_data': defaultdict(set),
                                'quantum_source_tables': [],
                                'quantum_confidence_scores': {},
                                'quantum_source_count': 0,
                                'quantum_emergence_indicators': []
                            }
                        
                        quantum_asset = self.quantum_discovered_assets[quantum_hostname]
                        
                        for col_idx, column_name in enumerate(columns):
                            if col_idx < len(row) and row[col_idx] is not None:
                                value = str(row[col_idx]).strip()
                                if value and value != quantum_hostname:
                                    quantum_asset['quantum_all_data'][column_name].add(value)
                        
                        if table_path not in quantum_asset['quantum_source_tables']:
                            quantum_asset['quantum_source_tables'].append(table_path)
                            quantum_asset['quantum_source_count'] += 1
                        
                        if quantum_hostname_col_info.get('quantum_metadata'):
                            quantum_asset['quantum_emergence_indicators'].append(quantum_hostname_col_info['quantum_metadata'])
                        
                        self.quantum_stats['total_quantum_assets_discovered'] += 1
                
            except Exception as e:
                logger.error(f"Failed to quantum extract from {table_path}: {e}")
    
    async def _merge_by_quantum_hostname(self) -> int:
        logger.info(f"Quantum merging {len(self.quantum_discovered_assets)} assets by hostname")
        
        for quantum_hostname, quantum_asset in self.quantum_discovered_assets.items():
            for field_name, value_set in quantum_asset['quantum_all_data'].items():
                quantum_asset['quantum_all_data'][field_name] = list(value_set)
        
        return len(self.quantum_discovered_assets)

class QuantumSmartColumnDetector:
    def __init__(self):
        self.quantum_hostname_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9],
            r'^[a-zA-Z0-9]+,
            r'^[a-zA-Z]{2,4}[0-9]{1,8}
        ]
        
        self.quantum_hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'host', 'server', 'pc', 'ws', 'node',
            'vm', 'container', 'pod', 'instance', 'device', 'endpoint', 'asset'
        ]
    
    def detect_quantum_hostname_columns(self, table_samples: Dict[str, List[str]]) -> List[Tuple[str, float]]:
        quantum_candidates = []
        
        for column_name, samples in table_samples.items():
            if not samples:
                continue
            
            quantum_name_score = self._score_quantum_column_name(column_name)
            quantum_content_score = self._score_quantum_content(samples)
            quantum_structure_score = self._score_quantum_structure(samples)
            
            quantum_combined_score = (
                quantum_name_score * 0.35 + 
                quantum_content_score * 0.45 + 
                quantum_structure_score * 0.2
            )
            
            if quantum_combined_score > 0.55:
                quantum_candidates.append((column_name, quantum_combined_score))
        
        return sorted(quantum_candidates, key=lambda x: x[1], reverse=True)
    
    def _score_quantum_column_name(self, name: str) -> float:
        name_lower = name.lower()
        
        quantum_exact_matches = [
            'hostname', 'host', 'computername', 'endpoint', 'device', 'server', 
            'machine', 'asset', 'equipment', 'system'
        ]
        for match in quantum_exact_matches:
            if match in name_lower:
                return min(1.0, len(match) / len(name_lower))
        
        return 0.0
    
    def _score_quantum_content(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quantum_hostname_count = 0
        for sample in samples[:30]:
            if self._looks_like_quantum_hostname(sample):
                quantum_hostname_count += 1
        
        return quantum_hostname_count / min(len(samples), 30)
    
    def _score_quantum_structure(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quantum_structure_indicators = 0
        for sample in samples[:20]:
            sample_str = str(sample)
            if re.search(r'[a-zA-Z]+[0-9]+', sample_str):
                quantum_structure_indicators += 1
            elif re.search(r'[a-zA-Z]+[\-_][a-zA-Z0-9]+', sample_str):
                quantum_structure_indicators += 1
        
        return quantum_structure_indicators / min(len(samples), 20)
    
    def _looks_like_quantum_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        for pattern in self.quantum_hostname_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                return True
        
        value_lower = value.lower()
        if any(indicator in value_lower for indicator in self.quantum_hostname_indicators):
            return True
        
        return False

class QuantumUniversalTableScanner:
    def __init__(self, quantum_content_analyzer: QuantumContentAnalyzer):
        self.quantum_analyzer = quantum_content_analyzer
        self.quantum_detector = QuantumSmartColumnDetector()
        self.quantum_processed_tables = set()
    
    async def scan_all_quantum_tables(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        quantum_all_assets = {}
        quantum_table_count = 0
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                for dataset in datasets:
                    dataset_ref = client.dataset(dataset.dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        if table_path in self.quantum_processed_tables:
                            continue
                        
                        try:
                            quantum_assets = await self._scan_quantum_single_table(client, table_path)
                            
                            for asset_id, asset in quantum_assets.items():
                                if asset_id in quantum_all_assets:
                                    quantum_all_assets[asset_id] = self._merge_quantum_asset_data(
                                        quantum_all_assets[asset_id], asset
                                    )
                                else:
                                    quantum_all_assets[asset_id] = asset
                            
                            quantum_table_count += 1
                            self.quantum_processed_tables.add(table_path)
                            
                        except Exception as e:
                            logger.warning(f"Failed to quantum scan {table_path}: {e}")
        
        return {
            'quantum_assets': quantum_all_assets,
            'quantum_tables_scanned': quantum_table_count,
            'quantum_unique_assets': len(quantum_all_assets)
        }
    
    async def _scan_quantum_single_table(self, client, table_path: str) -> Dict[str, Any]:
        table = client.get_table(table_path)
        
        if not table.schema or table.num_rows == 0:
            return {}
        
        columns = [field.name for field in table.schema]
        quantum_samples = await self._sample_quantum_columns(client, table_path, columns)
        
        quantum_hostname_candidates = self.quantum_detector.detect_quantum_hostname_columns(quantum_samples)
        
        if not quantum_hostname_candidates:
            return {}
        
        quantum_best_hostname_col = quantum_hostname_candidates[0][0]
        return await self._extract_from_quantum_hostname_column(client, table_path, quantum_best_hostname_col, quantum_samples)
    
    async def _sample_quantum_columns(self, client, table_path: str, columns: List[str]) -> Dict[str, List[str]]:
        quantum_limited_columns = columns[:40]
        
        quantum_query = f"""
        SELECT {', '.join([f'`{col}`' for col in quantum_limited_columns])}
        FROM `{table_path}`
        WHERE RAND() < 0.025
        LIMIT 400
        """
        
        quantum_samples = {}
        try:
            job = client.query(quantum_query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(quantum_limited_columns):
                values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        values.append(str(row[col_idx]))
                quantum_samples[column_name] = values
        
        except Exception as e:
            logger.warning(f"Quantum sampling failed for {table_path}: {e}")
        
        return quantum_samples
    
    async def _extract_from_quantum_hostname_column(self, client, table_path: str, 
                                                  quantum_hostname_col: str, quantum_samples: Dict[str, List[str]]) -> Dict[str, Any]:
        quantum_query = f"""
        SELECT *
        FROM `{table_path}`
        WHERE `{quantum_hostname_col}` IS NOT NULL
        LIMIT 50000
        """
        
        quantum_assets = {}
        try:
            job = client.query(quantum_query)
            results = list(job.result())
            
            table = client.get_table(table_path)
            quantum_all_columns = [field.name for field in table.schema]
            hostname_idx = quantum_all_columns.index(quantum_hostname_col)
            
            for row in results:
                if hostname_idx < len(row) and row[hostname_idx]:
                    quantum_hostname = str(row[hostname_idx]).strip().upper()
                    
                    if not quantum_hostname or len(quantum_hostname) < 1:
                        continue
                    
                    quantum_asset_id = f"quantum_content_{hashlib.md5(quantum_hostname.encode()).hexdigest()[:16]}"
                    
                    if quantum_asset_id not in quantum_assets:
                        quantum_assets[quantum_asset_id] = {
                            'quantum_hostname': quantum_hostname,
                            'quantum_source_tables': [table_path],
                            'quantum_all_data': {},
                            'quantum_source_count': 1,
                            'quantum_confidence': 0.95
                        }
                    
                    quantum_asset = quantum_assets[quantum_asset_id]
                    
                    for col_idx, column_name in enumerate(quantum_all_columns):
                        if col_idx < len(row) and row[col_idx] is not None:
                            value = str(row[col_idx]).strip()
                            if value and value != quantum_hostname:
                                if column_name not in quantum_asset['quantum_all_data']:
                                    quantum_asset['quantum_all_data'][column_name] = []
                                if value not in quantum_asset['quantum_all_data'][column_name]:
                                    quantum_asset['quantum_all_data'][column_name].append(value)
        
        except Exception as e:
            logger.error(f"Quantum extraction failed for {table_path}: {e}")
        
        return quantum_assets
    
    def _merge_quantum_asset_data(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        quantum_merged = primary.copy()
        
        for table in secondary['quantum_source_tables']:
            if table not in quantum_merged['quantum_source_tables']:
                quantum_merged['quantum_source_tables'].append(table)
                quantum_merged['quantum_source_count'] += 1
        
        for field_name, values in secondary['quantum_all_data'].items():
            if field_name not in quantum_merged['quantum_all_data']:
                quantum_merged['quantum_all_data'][field_name] = []
            
            for value in values:
                if value not in quantum_merged['quantum_all_data'][field_name]:
                    quantum_merged['quantum_all_data'][field_name].append(value)
        
        quantum_merged['quantum_confidence'] = max(
            primary.get('quantum_confidence', 0), 
            secondary.get('quantum_confidence', 0)
        )
        
        return quantum_merged

ContentBasedEngine = QuantumContentBasedEngine
UniversalTableScanner = QuantumUniversalTableScanner