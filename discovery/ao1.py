# discovery/ao1.py

import asyncio
import logging
import re
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class AO1VisibilityEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_weights = {
            'log_coverage': 0.4,
            'cmdb_coverage': 0.3,
            'security_coverage': 0.2,
            'field_completeness': 0.1
        }
    
    def is_hostname_column_by_content(self, samples: List[str]) -> bool:
        if not samples or len(samples) < 3:
            return False
        
        hostname_count = 0
        valid_samples = 0
        
        for sample in samples[:100]:
            if sample and str(sample).strip():
                valid_samples += 1
                if self.looks_like_hostname(sample):
                    hostname_count += 1
        
        if valid_samples == 0:
            return False
        
        hostname_ratio = hostname_count / valid_samples
        return hostname_ratio > 0.25
    
    def looks_like_hostname(self, value: str) -> bool:
        if not value:
            return False
        
        value = str(value).strip()
        
        if len(value) < 1 or len(value) > 253:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0', 'TRUE', 'FALSE'}
        if value.upper() in invalid_values:
            return False
        
        if value.isdigit():
            return False
        
        if self.looks_like_ip(value):
            return False
        
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'FTP://', 'WWW.', '@', '.COM', '.NET', '.ORG']):
            return False
        
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]*$', value):
            return False
        
        return True
    
    def looks_like_ip(self, value: str) -> bool:
        if not value:
            return False
        
        parts = str(value).strip().split('.')
        if len(parts) == 4:
            try:
                for part in parts:
                    num = int(part)
                    if not (0 <= num <= 255):
                        return False
                return True
            except:
                return False
        return False

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_engine = AO1VisibilityEngine(config)
        
        self.performance_metrics = {
            'classifications': 0,
            'processing_times': [],
            'confidence_scores': [],
            'visibility_scores': []
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        
        logger.info("🔥 STARTING CONTENT-BASED DISCOVERY - NO COLUMN NAME FILTERING 🔥")
        start_time = datetime.now()
        
        discovered_assets = {}
        total_hosts_processed = 0
        total_rows_scanned = 0
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🚀 PROCESSING PROJECT: {project_id}")
            
            try:
                project_assets, project_rows = await self._discover_project_assets(client_manager, project_id)
                
                for hostname, asset in project_assets.items():
                    if hostname in discovered_assets:
                        discovered_assets[hostname] = self._merge_assets(discovered_assets[hostname], asset)
                    else:
                        discovered_assets[hostname] = asset
                
                total_hosts_processed += len(project_assets)
                total_rows_scanned += project_rows
                
                logger.info(f"✅ PROJECT {project_id}: {len(project_assets):,} HOSTS FROM {project_rows:,} ROWS")
                
            except Exception as e:
                logger.error(f"❌ FAILED TO PROCESS PROJECT {project_id}: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎉 CONTENT-BASED DISCOVERY COMPLETE! 🎉")
        logger.info(f"   📊 UNIQUE HOSTS DISCOVERED: {len(discovered_assets):,}")
        logger.info(f"   🔍 TOTAL ROWS SCANNED: {total_rows_scanned:,}")
        logger.info(f"   ⏱️  PROCESSING TIME: {processing_time/60:.1f} MINUTES")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(discovered_assets),
                'total_hosts_processed': total_hosts_processed,
                'total_rows_scanned': total_rows_scanned,
                'processing_time_minutes': processing_time / 60,
                'content_based_discovery': True
            },
            'assets': discovered_assets,
            'performance_metrics': self._get_performance_summary()
        }
    
    async def _discover_project_assets(self, client_manager, project_id: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        total_rows = 0
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            prioritized_datasets = self._prioritize_datasets(datasets, project_id)
            
            for dataset_priority, dataset in prioritized_datasets:
                logger.info(f"🗂️  PROCESSING DATASET: {dataset.dataset_id} (Priority: {dataset_priority})")
                
                try:
                    dataset_assets, dataset_rows = await self._discover_dataset_assets(
                        client, project_id, dataset.dataset_id
                    )
                    
                    for hostname, asset in dataset_assets.items():
                        if hostname in assets:
                            assets[hostname] = self._merge_assets(assets[hostname], asset)
                        else:
                            assets[hostname] = asset
                    
                    total_rows += dataset_rows
                    
                    logger.info(f"📊 DATASET {dataset.dataset_id}: {len(dataset_assets):,} hosts from {dataset_rows:,} rows")
                    
                except Exception as e:
                    logger.error(f"❌ FAILED TO PROCESS DATASET {dataset.dataset_id}: {e}")
        
        return assets, total_rows
    
    def _prioritize_datasets(self, datasets, project_id: str) -> List[Tuple[int, Any]]:
        prioritized = []
        
        for dataset in datasets:
            priority = 100
            
            if 'SAS_BI' in dataset.dataset_id.upper():
                priority = 1
            elif any(keyword in dataset.dataset_id.upper() for keyword in ['ENDPOINT', 'HOST', 'ASSET', 'DEVICE']):
                priority = 2
            elif any(keyword in dataset.dataset_id.upper() for keyword in ['SECURITY', 'LOG', 'EVENT']):
                priority = 3
            elif any(keyword in dataset.dataset_id.upper() for keyword in ['CMDB', 'INVENTORY']):
                priority = 4
            
            prioritized.append((priority, dataset))
        
        return sorted(prioritized, key=lambda x: x[0])
    
    async def _discover_dataset_assets(self, client, project_id: str, dataset_id: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        total_rows = 0
        
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            logger.info(f"📋 FOUND {len(tables)} TABLES IN DATASET {dataset_id}")
            
            for table_ref in tables:
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                
                try:
                    table_assets, table_rows = await self._discover_table_assets(client, table_path)
                    
                    for hostname, asset in table_assets.items():
                        if hostname in assets:
                            assets[hostname] = self._merge_assets(assets[hostname], asset)
                        else:
                            assets[hostname] = asset
                    
                    total_rows += table_rows
                    
                    if len(table_assets) > 0:
                        logger.info(f"🎯 TABLE {table_ref.table_id}: {len(table_assets):,} hosts from {table_rows:,} rows")
                    
                except Exception as e:
                    logger.debug(f"⚠️  FAILED TO PROCESS TABLE {table_ref.table_id}: {e}")
            
        except Exception as e:
            logger.error(f"❌ FAILED TO LIST TABLES IN DATASET {dataset_id}: {e}")
        
        return assets, total_rows
    
    async def _discover_table_assets(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return assets, 0
            
            columns = [field.name for field in table.schema]
            
            hostname_columns = await self._find_hostname_columns_by_content(client, table_path, columns)
            if not hostname_columns:
                return assets, 0
            
            logger.info(f"🎯 HOSTNAME COLUMNS IN {table_path}: {hostname_columns}")
            
            max_rows = min(table.num_rows, 100000)
            
            query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT {max_rows}
            """
            
            job = client.query(query)
            results = list(job.result())
            
            if results:
                assets = self._extract_hosts_from_results(
                    results, columns, hostname_columns, table_path
                )
                rows_processed = len(results)
            
        except Exception as e:
            logger.debug(f"Failed to process table {table_path}: {e}")
        
        return assets, rows_processed
    
    async def _find_hostname_columns_by_content(self, client, table_path: str, columns: List[str]) -> List[str]:
        hostname_columns = []
        
        try:
            sample_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 200
            """
            
            job = client.query(sample_query)
            results = list(job.result())
            
            if not results:
                return []
            
            for column_name in columns:
                samples = []
                
                for row in results:
                    if hasattr(row, '_fields'):
                        row_dict = row._asdict()
                    elif isinstance(row, dict):
                        row_dict = row
                    elif isinstance(row, (list, tuple)):
                        row_dict = dict(zip(columns, row))
                    else:
                        continue
                    
                    if column_name in row_dict and row_dict[column_name] is not None:
                        samples.append(str(row_dict[column_name]))
                
                if len(samples) >= 5:
                    if self.visibility_engine.is_hostname_column_by_content(samples):
                        hostname_columns.append(column_name)
                        hostname_ratio = self._calculate_hostname_ratio(samples)
                        logger.info(f"🎯 HOSTNAME COLUMN: {column_name} (ratio: {hostname_ratio:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to analyze columns in {table_path}: {e}")
        
        return hostname_columns
    
    def _calculate_hostname_ratio(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = sum(1 for sample in samples if self.visibility_engine.looks_like_hostname(sample))
        return hostname_count / len(samples)
    
    def _extract_hosts_from_results(self, results: List, columns: List[str], 
                                  hostname_columns: List[str], table_path: str) -> Dict[str, Any]:
        assets = {}
        
        for row in results:
            if hasattr(row, '_fields'):
                row_dict = row._asdict()
            elif isinstance(row, dict):
                row_dict = row
            elif isinstance(row, (list, tuple)):
                row_dict = dict(zip(columns, row))
            else:
                continue
            
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col] is not None:
                    hostname_value = str(row_dict[hostname_col]).strip().upper()
                    
                    if self._is_valid_hostname(hostname_value):
                        if hostname_value not in assets:
                            assets[hostname_value] = {
                                'hostname': hostname_value,
                                'sources': [],
                                'tables_found_in': [],
                                'all_data': {},
                                'row_count': 0
                            }
                        
                        asset = assets[hostname_value]
                        asset['row_count'] += 1
                        
                        source_name = self._determine_source_from_table(table_path)
                        if source_name not in asset['sources']:
                            asset['sources'].append(source_name)
                        
                        if table_path not in asset['tables_found_in']:
                            asset['tables_found_in'].append(table_path)
                        
                        self._extract_additional_fields(asset, row_dict, columns)
                        self._set_coverage_flags(asset, source_name)
        
        return assets
    
    def _determine_source_from_table(self, table_path: str) -> str:
        table_lower = table_path.lower()
        
        if 'sas_bi' in table_lower:
            if 'endpoint' in table_lower:
                return 'cmdb'
            elif 'spl' in table_lower or 'splunk' in table_lower:
                return 'splunk'
            elif 'agent' in table_lower:
                return 'crowdstrike'
        elif 'chronicle' in table_lower:
            return 'chronicle'
        elif 'crowdstrike' in table_lower:
            return 'crowdstrike'
        elif 'splunk' in table_lower:
            return 'splunk'
        
        return 'unknown'
    
    def _extract_additional_fields(self, asset: Dict[str, Any], row_dict: Dict[str, Any], columns: List[str]):
        field_patterns = {
            'ip_address': ['ip', 'addr'],
            'fqdn': ['fqdn', 'domain', 'dns'],
            'country': ['country', 'ctry'],
            'region': ['region', 'geo'],
            'business_unit': ['business', 'unit', 'bu'],
            'datacenter': ['datacenter', 'dc', 'site'],
            'application_class': ['application', 'app', 'class'],
            'infrastructure_type': ['infrastructure', 'infra', 'type'],
            'system_classification': ['system', 'classification', 'os'],
            'mac_address': ['mac', 'physical']
        }
        
        for field_type, patterns in field_patterns.items():
            for col in columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in patterns):
                    if col in row_dict and row_dict[col] is not None:
                        value = str(row_dict[col]).strip()
                        if self._is_valid_field_value(value):
                            if field_type not in asset['all_data']:
                                asset['all_data'][field_type] = set()
                            asset['all_data'][field_type].add(value)
        
        for field_type in asset['all_data']:
            asset['all_data'][field_type] = list(asset['all_data'][field_type])
    
    def _is_valid_hostname(self, value: str) -> bool:
        if not value:
            return False
        
        value = str(value).strip()
        
        if len(value) < 1 or len(value) > 253:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0', 'TRUE', 'FALSE'}
        if value.upper() in invalid_values:
            return False
        
        if value.isdigit():
            return False
        
        if self.visibility_engine.looks_like_ip(value):
            return False
        
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'FTP://', 'WWW.', '@']):
            return False
        
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]*$', value):
            return False
        
        return True
    
    def _is_valid_field_value(self, value: str) -> bool:
        if not value:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0'}
        return str(value).upper().strip() not in invalid_values
    
    def _set_coverage_flags(self, asset: Dict[str, Any], source: str):
        coverage_mapping = {
            'cmdb': {'cmdb_visibility': True},
            'splunk': {'splunk_coverage': True, 'siem_coverage': True},
            'chronicle': {'chronicle_coverage': True, 'siem_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True}
        }
        
        flags = coverage_mapping.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        merged['row_count'] = merged.get('row_count', 0) + secondary.get('row_count', 0)
        
        for source in secondary.get('sources', []):
            if source not in merged['sources']:
                merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage', 'siem_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        return {
            'content_based_discovery': True,
            'column_name_filtering': False,
            'pure_content_analysis': True
        }