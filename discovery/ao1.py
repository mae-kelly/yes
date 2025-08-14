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
    
    def _is_hostname_column_by_content(self, samples: List[str]) -> bool:
        if not samples or len(samples) < 3:
            return False
        
        hostname_count = 0
        valid_samples = 0
        
        for sample in samples[:100]:
            if sample and str(sample).strip():
                valid_samples += 1
                if self._looks_like_hostname(sample):
                    hostname_count += 1
        
        if valid_samples == 0:
            return False
        
        hostname_ratio = hostname_count / valid_samples
        return hostname_ratio > 0.2
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        if not value or len(value) < 1 or len(value) > 253:
            return False
        
        if value.upper() in ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0', 'TRUE', 'FALSE']:
            return False
        
        if value.isdigit():
            return False
        
        if self._looks_like_ip(value):
            return False
        
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'FTP://', 'WWW.', '@', '\\', '/']):
            return False
        
        if not any(c.isalpha() for c in value):
            return False
        
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]*$', value, re.IGNORECASE):
            return True
        
        return False
    
    def _looks_like_ip(self, value: str) -> bool:
        parts = value.split('.')
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
        
        logger.info("🔥 STARTING CONTENT-BASED HOSTNAME DISCOVERY 🔥")
        logger.info("🎯 ANALYZING ALL COLUMNS BY CONTENT ONLY - NO COLUMN NAMES CONSIDERED")
        start_time = datetime.now()
        
        discovered_assets = {}
        total_hosts_processed = 0
        total_rows_scanned = 0
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🗂️ PROCESSING PROJECT: {project_id}")
            
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                sas_bi_datasets = [d for d in datasets if 'SAS_BI' in d.dataset_id.upper()]
                other_datasets = [d for d in datasets if 'SAS_BI' not in d.dataset_id.upper()]
                
                prioritized_datasets = sas_bi_datasets + other_datasets
                
                logger.info(f"📂 FOUND {len(datasets)} DATASETS: {len(sas_bi_datasets)} SAS_BI, {len(other_datasets)} OTHERS")
                
                for dataset_idx, dataset in enumerate(prioritized_datasets):
                    logger.info(f"🗂️ DATASET {dataset_idx + 1}/{len(prioritized_datasets)}: {dataset.dataset_id}")
                    
                    tables = list(client.list_tables(dataset))
                    logger.info(f"📋 TABLES IN DATASET: {len(tables)}")
                    
                    for table_idx, table_ref in enumerate(tables):
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        try:
                            logger.info(f"🔍 TABLE {table_idx + 1}/{len(tables)}: {table_ref.table_id}")
                            
                            assets, rows_processed = await self._process_table_content_based(client_manager, table_path)
                            
                            for hostname, asset in assets.items():
                                if hostname in discovered_assets:
                                    discovered_assets[hostname] = self._merge_assets(
                                        discovered_assets[hostname], asset
                                    )
                                else:
                                    discovered_assets[hostname] = asset
                            
                            total_hosts_processed += len(assets)
                            total_rows_scanned += rows_processed
                            
                            if len(assets) > 0:
                                logger.info(f"✅ FOUND {len(assets):,} HOSTS FROM {rows_processed:,} ROWS")
                            
                            logger.info(f"🔥 CUMULATIVE: {len(discovered_assets):,} UNIQUE HOSTS, {total_rows_scanned:,} ROWS SCANNED")
                            
                        except Exception as e:
                            logger.error(f"❌ FAILED TO PROCESS {table_path}: {e}")
                    
                    logger.info(f"📊 DATASET {dataset.dataset_id} COMPLETE: {len(discovered_assets):,} TOTAL HOSTS")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎉 CONTENT-BASED DISCOVERY COMPLETE! 🎉")
        logger.info(f"🏆 FINAL RESULTS:")
        logger.info(f"   📊 UNIQUE HOSTS DISCOVERED: {len(discovered_assets):,}")
        logger.info(f"   🔍 TOTAL ROWS SCANNED: {total_rows_scanned:,}")
        logger.info(f"   ⏱️ PROCESSING TIME: {processing_time/60:.1f} MINUTES")
        logger.info(f"   🚀 ROWS PER SECOND: {total_rows_scanned/processing_time:,.0f}")
        logger.info(f"   💻 HOSTS PER SECOND: {len(discovered_assets)/processing_time:,.0f}")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(discovered_assets),
                'total_hosts_processed': total_hosts_processed,
                'total_rows_scanned': total_rows_scanned,
                'processing_time_minutes': processing_time / 60,
                'rows_per_second': total_rows_scanned / processing_time,
                'hosts_per_second': len(discovered_assets) / processing_time,
                'content_based_discovery': True,
                'no_column_name_filtering': True
            },
            'assets': discovered_assets,
            'performance_metrics': self._get_performance_summary()
        }
    
    async def _process_table_content_based(self, client_manager, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        total_rows_processed = 0
        
        with client_manager.get_client() as client:
            try:
                table = client.get_table(table_path)
                if not table.schema:
                    return assets, 0
                
                columns = [field.name for field in table.schema]
                total_rows = table.num_rows
                
                logger.info(f"🔍 ANALYZING TABLE: {table_path}")
                logger.info(f"📋 COLUMNS: {len(columns)}")
                logger.info(f"📊 TOTAL ROWS: {total_rows:,}")
                
                hostname_columns = await self._find_hostname_columns_by_content_only(client, table_path, columns)
                if not hostname_columns:
                    logger.info(f"⚠️ NO HOSTNAME COLUMNS FOUND IN {table_path}")
                    return assets, 0
                
                logger.info(f"🎯 HOSTNAME COLUMNS DETECTED: {hostname_columns}")
                
                field_mappings = self._create_field_mappings(columns)
                
                max_rows_to_process = min(total_rows, 500000)
                batch_size = 50000
                batches = (max_rows_to_process + batch_size - 1) // batch_size
                
                logger.info(f"⚡ PROCESSING {batches} BATCHES OF {batch_size:,} ROWS EACH")
                
                for batch_num in range(batches):
                    offset = batch_num * batch_size
                    
                    query = f"""
                    SELECT *
                    FROM `{table_path}`
                    LIMIT {batch_size} OFFSET {offset}
                    """
                    
                    logger.info(f"🚀 BATCH {batch_num + 1}/{batches}: OFFSET {offset:,}")
                    
                    try:
                        job = client.query(query)
                        results = list(job.result())
                        
                        logger.info(f"📊 QUERY RETURNED {len(results):,} ROWS")
                        
                        if len(results) == 0:
                            logger.warning(f"⚠️ NO ROWS RETURNED FOR BATCH {batch_num + 1}")
                            continue
                        
                        batch_assets = self._extract_hosts_from_batch(results, columns, hostname_columns, field_mappings, table_path)
                        
                        for hostname, asset in batch_assets.items():
                            if hostname in assets:
                                assets[hostname] = self._merge_batch_assets(assets[hostname], asset)
                            else:
                                assets[hostname] = asset
                        
                        total_rows_processed += len(results)
                        
                        logger.info(f"✅ BATCH {batch_num + 1}/{batches}: {len(batch_assets):,} HOSTS FROM {len(results):,} ROWS")
                        
                        if len(results) < batch_size:
                            logger.info(f"🏁 REACHED END OF TABLE")
                            break
                            
                    except Exception as batch_e:
                        logger.error(f"❌ BATCH {batch_num + 1} FAILED: {batch_e}")
                        continue
                
                logger.info(f"🎉 TABLE COMPLETE: {len(assets):,} HOSTS FROM {total_rows_processed:,} ROWS")
                
            except Exception as e:
                logger.error(f"❌ TABLE PROCESSING FAILED: {table_path}: {e}")
        
        return assets, total_rows_processed
    
    async def _find_hostname_columns_by_content_only(self, client, table_path: str, columns: List[str]) -> List[str]:
        hostname_columns = []
        
        logger.info(f"🔍 ANALYZING ALL {len(columns)} COLUMNS BY CONTENT ONLY")
        
        sample_query = f"""
        SELECT *
        FROM `{table_path}`
        LIMIT 200
        """
        
        try:
            job = client.query(sample_query)
            results = list(job.result())
            
            logger.info(f"📊 CONTENT ANALYSIS: {len(results)} SAMPLE ROWS")
            
            if not results:
                logger.warning("❌ NO SAMPLE ROWS FOR CONTENT ANALYSIS")
                return []
            
            for col_idx, column_name in enumerate(columns):
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
                        value = str(row_dict[column_name]).strip()
                        if value:
                            samples.append(value)
                
                if len(samples) >= 5:
                    hostname_ratio = self._calculate_hostname_ratio(samples)
                    logger.info(f"🔍 {column_name}: {len(samples)} samples, {hostname_ratio:.2f} hostname ratio")
                    
                    if self.visibility_engine._is_hostname_column_by_content(samples):
                        hostname_columns.append(column_name)
                        logger.info(f"🎯 HOSTNAME COLUMN: {column_name} (ratio: {hostname_ratio:.2f})")
            
            logger.info(f"🎯 FOUND {len(hostname_columns)} HOSTNAME COLUMNS: {hostname_columns}")
            
        except Exception as e:
            logger.error(f"❌ CONTENT ANALYSIS FAILED: {e}")
        
        return hostname_columns
    
    def _calculate_hostname_ratio(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = sum(1 for sample in samples if self.visibility_engine._looks_like_hostname(sample))
        return hostname_count / len(samples)
    
    def _create_field_mappings(self, columns: List[str]) -> Dict[str, List[str]]:
        mappings = {
            'ip_address': [],
            'fqdn': [],
            'country': [],
            'region': [],
            'business_unit': [],
            'cio': [],
            'datacenter': [],
            'application_class': [],
            'infrastructure_type': [],
            'system_classification': [],
            'mac_address': []
        }
        
        field_patterns = {
            'ip_address': ['ip', 'address'],
            'fqdn': ['fqdn', 'domain', 'dns'],
            'country': ['country', 'ctry'],
            'region': ['region', 'geo', 'location'],
            'business_unit': ['business', 'unit', 'bu', 'org'],
            'cio': ['cio', 'chief'],
            'datacenter': ['datacenter', 'dc', 'site'],
            'application_class': ['application', 'app', 'class'],
            'infrastructure_type': ['infrastructure', 'infra', 'type'],
            'system_classification': ['system', 'classification'],
            'mac_address': ['mac', 'physical']
        }
        
        for col in columns:
            col_lower = col.lower()
            for field_type, patterns in field_patterns.items():
                for pattern in patterns:
                    if pattern in col_lower:
                        mappings[field_type].append(col)
                        break
        
        return mappings
    
    def _extract_hosts_from_batch(self, results: List, columns: List[str], hostname_columns: List[str], 
                                field_mappings: Dict[str, List[str]], table_path: str) -> Dict[str, Any]:
        assets = {}
        rows_with_hostnames = 0
        total_rows_processed = len(results)
        
        logger.info(f"🔍 EXTRACTING HOSTS FROM {total_rows_processed:,} ROWS")
        logger.info(f"🎯 HOSTNAME COLUMNS: {hostname_columns}")
        
        for row_idx, row in enumerate(results):
            if not row:
                continue
            
            if hasattr(row, '_fields'):
                row_dict = row._asdict()
            elif isinstance(row, dict):
                row_dict = row
            elif isinstance(row, (list, tuple)):
                row_dict = dict(zip(columns, row))
            else:
                try:
                    row_dict = dict(row)
                except:
                    continue
            
            hostnames = []
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col] is not None:
                    hostname_value = str(row_dict[hostname_col]).strip()
                    
                    if self._is_valid_hostname(hostname_value):
                        hostnames.append(hostname_value.upper())
            
            if hostnames:
                rows_with_hostnames += 1
                
                for hostname in hostnames:
                    if hostname not in assets:
                        assets[hostname] = {
                            'hostname': hostname,
                            'sources': [],
                            'tables_found_in': [],
                            'all_data': {},
                            'row_count': 0
                        }
                    
                    asset = assets[hostname]
                    asset['row_count'] += 1
                    
                    source_name = self._determine_source_type(table_path)
                    if source_name not in asset['sources']:
                        asset['sources'].append(source_name)
                    
                    if table_path not in asset['tables_found_in']:
                        asset['tables_found_in'].append(table_path)
                    
                    for field_type, field_columns in field_mappings.items():
                        for field_col in field_columns:
                            if field_col in row_dict and row_dict[field_col]:
                                value = str(row_dict[field_col]).strip()
                                if self._is_valid_field_value(value):
                                    if field_type not in asset['all_data']:
                                        asset['all_data'][field_type] = set()
                                    asset['all_data'][field_type].add(value)
                    
                    self._set_coverage_flags(asset, source_name)
        
        for hostname, asset in assets.items():
            for field_type, value_set in asset['all_data'].items():
                asset['all_data'][field_type] = list(value_set)
        
        logger.info(f"📊 EXTRACTION RESULTS:")
        logger.info(f"   🔢 ROWS PROCESSED: {total_rows_processed:,}")
        logger.info(f"   🏠 ROWS WITH HOSTNAMES: {rows_with_hostnames:,}")
        logger.info(f"   🎯 UNIQUE HOSTS: {len(assets):,}")
        if total_rows_processed > 0:
            logger.info(f"   📈 EXTRACTION RATE: {(rows_with_hostnames/total_rows_processed*100):.1f}%")
        
        return assets
    
    def _determine_source_type(self, table_path: str) -> str:
        table_lower = table_path.lower()
        
        if 'endpoint' in table_lower:
            if 'log' in table_lower:
                return 'splunk'
            elif 'agent' in table_lower:
                return 'crowdstrike'
            else:
                return 'cmdb'
        elif 'splunk' in table_lower or 'spl_' in table_lower:
            return 'splunk'
        elif 'chronicle' in table_lower or 'datalake' in table_lower:
            return 'chronicle'
        elif 'crowdstrike' in table_lower or 'cs_' in table_lower:
            return 'crowdstrike'
        elif 'cmdb' in table_lower or 'dim_' in table_lower:
            return 'cmdb'
        else:
            return 'unknown'
    
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
        
        if self._looks_like_ip(value):
            return False
        
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'FTP://', 'WWW.', '@']):
            return False
        
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]*$', value, re.IGNORECASE):
            return False
        
        return True
    
    def _looks_like_ip(self, value: str) -> bool:
        parts = value.split('.')
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
    
    def _is_valid_field_value(self, value: str) -> bool:
        if not value:
            return False
        
        invalid_values = ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', 'null', 'none', '0']
        return value.upper() not in invalid_values
    
    def _set_coverage_flags(self, asset: Dict[str, Any], source: str):
        coverage_flags = {
            'cmdb': {'cmdb_visibility': True, 'cmdb_coverage': True},
            'splunk': {'splunk_coverage': True, 'siem_coverage': True},
            'chronicle': {'chronicle_coverage': True, 'siem_coverage': True, 'google_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True, 'endpoint_protection': True}
        }
        
        flags = coverage_flags.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_batch_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _merge_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
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
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        metrics = self.performance_metrics
        
        if not metrics['confidence_scores']:
            return {'status': 'no_data'}
        
        return {
            'total_classifications': metrics['classifications'],
            'avg_processing_time': statistics.mean(metrics['processing_times']) if metrics['processing_times'] else 0,
            'avg_confidence': statistics.mean(metrics['confidence_scores']) if metrics['confidence_scores'] else 0,
            'avg_visibility': statistics.mean(metrics['visibility_scores']) if metrics['visibility_scores'] else 0
        }