# discovery/ao1.py

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class RealtimeCMDBBuilder:
    def __init__(self):
        self.cmdb = {}
        self.stats = {
            'hosts_discovered': 0,
            'attributes_added': 0,
            'tables_processed': 0,
            'rows_processed': 0,
            'duplicate_hosts_updated': 0
        }
    
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname:
            return ""
        
        hostname = str(hostname).strip().upper()
        
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Z0-9\-]', '', hostname)
        
        return hostname
    
    def get_coverage_flag(self, source_table: str) -> Optional[str]:
        table_lower = source_table.lower()
        
        if 'chronicle-fisv.datalake.events' in table_lower:
            return 'in_chronicle'
        elif 'v_dim_endpointagent' in table_lower:
            return 'in_crowdstrike'
        elif 'v_dim_endpoint' in table_lower and 'agent' not in table_lower:
            return 'in_original_cmdb'
        elif 'v_spl_endpoint_log' in table_lower:
            return 'in_splunk'
        
        return None
    
    def add_host_to_cmdb(self, hostname: str, attribute_type: str, attribute_value: str, source_table: str):
        normalized_hostname = self.normalize_hostname(hostname)
        
        if not normalized_hostname:
            return
        
        is_new_host = normalized_hostname not in self.cmdb
        
        if is_new_host:
            self.cmdb[normalized_hostname] = {
                'hostname': normalized_hostname,
                'original_hostnames': set(),
                'attributes': defaultdict(set),
                'source_tables': set(),
                'source_columns': set(),
                'in_chronicle': False,
                'in_crowdstrike': False,
                'in_original_cmdb': False,
                'in_splunk': False,
                'first_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self.stats['hosts_discovered'] += 1
            logger.info(f"NEW HOST DISCOVERED: {normalized_hostname}")
        else:
            self.stats['duplicate_hosts_updated'] += 1
            logger.info(f"DUPLICATE HOST FOUND - ADDING NEW ATTRIBUTES: {normalized_hostname}")
        
        host = self.cmdb[normalized_hostname]
        
        host['original_hostnames'].add(hostname)
        
        if attribute_value and str(attribute_value).strip():
            clean_value = str(attribute_value).strip()
            old_count = len(host['attributes'][attribute_type])
            host['attributes'][attribute_type].add(clean_value)
            new_count = len(host['attributes'][attribute_type])
            
            if new_count > old_count:
                self.stats['attributes_added'] += 1
                logger.info(f"   ADDING VALUE FOR {attribute_type.upper()}: {clean_value}")
        
        host['source_tables'].add(source_table)
        host['source_columns'].add(f"{source_table}:{attribute_type}")
        
        coverage_flag = self.get_coverage_flag(source_table)
        if coverage_flag:
            host[coverage_flag] = True
            logger.info(f"   SETTING {coverage_flag.upper()}: YES")
        
        host['last_updated'] = datetime.now().isoformat()
    
    def get_current_cmdb_snapshot(self) -> Dict[str, Any]:
        serializable_cmdb = {}
        
        for hostname, host_data in self.cmdb.items():
            serializable_cmdb[hostname] = {
                'asset_id': hostname,
                'hostname': host_data['hostname'],
                'original_hostnames': list(host_data['original_hostnames']),
                'attributes': {k: list(v) for k, v in host_data['attributes'].items()},
                'source_tables': list(host_data['source_tables']),
                'source_columns': list(host_data['source_columns']),
                'in_chronicle': host_data['in_chronicle'],
                'in_crowdstrike': host_data['in_crowdstrike'],
                'in_original_cmdb': host_data['in_original_cmdb'],
                'in_splunk': host_data['in_splunk'],
                'first_seen': host_data['first_seen'],
                'last_updated': host_data['last_updated'],
                'total_sources': len(host_data['source_tables']),
                'total_attributes': sum(len(v) for v in host_data['attributes'].items())
            }
        
        return serializable_cmdb
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_hosts': len(self.cmdb),
            'hosts_discovered': self.stats['hosts_discovered'],
            'duplicate_hosts_updated': self.stats['duplicate_hosts_updated'],
            'attributes_added': self.stats['attributes_added'],
            'tables_processed': self.stats['tables_processed'],
            'rows_processed': self.stats['rows_processed']
        }

class SmartKeywordProcessor:
    def __init__(self, cmdb_builder: RealtimeCMDBBuilder):
        self.cmdb_builder = cmdb_builder
        self.host_identifier = 'host'
        
        self.secondary_keywords = {
            'hostname': ['hostname'],
            'fqdn': ['fqdn'],
            'computer_name': ['computer_name', 'computername'],
            'ip_address': ['ip'],
            'mac_address': ['mac'],
            'asset_id': ['asset_id', 'assetid'],
            'serial_number': ['serial'],
            'domain': ['domain'],
            'infrastructure_type': ['hosting', 'infrastructure'],
            'cloud_provider': ['aws', 'azure', 'gcp', 'cloud'],
            'cloud_region': ['region'],
            'datacenter': ['datacenter', 'dc'],
            'vpc': ['vpc', 'vlan'],
            'global_region': ['americas', 'emea', 'apac'],
            'country': ['country'],
            'site': ['site', 'building'],
            'business_unit': ['business_unit', 'bu'],
            'cio': ['cio'],
            'apm': ['apm'],
            'application_class': ['app_class', 'application_class'],
            'application_name': ['app_name', 'application'],
            'os_type': ['os', 'operating'],
            'os_version': ['version'],
            'server_role': ['role', 'function'],
            'virtualization': ['virtual', 'vm', 'container'],
            'edr_status': ['edr', 'crowdstrike', 'sentinelone'],
            'tanium_status': ['tanium'],
            'dlp_status': ['dlp'],
            'firewall': ['firewall'],
            'encryption': ['encryption'],
            'vulnerability': ['vuln', 'vulnerability'],
            'logging_platform': ['splunk', 'chronicle', 'siem'],
            'log_source': ['log_source', 'logsource'],
            'log_type': ['log_type', 'logtype'],
            'compliance': ['compliance'],
            'external_exposure': ['external', 'internet'],
            'lifecycle_status': ['lifecycle', 'status']
        }
        
        self.stats = {
            'keywords_found': {},
            'columns_processed': 0,
            'host_tables_found': 0,
            'non_host_tables_skipped': 0
        }
    
    def _contains_exact_word(self, column_name: str, keyword: str) -> bool:
        column_lower = column_name.lower()
        keyword_lower = keyword.lower()
        
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        
        return bool(re.search(pattern, column_lower))
    
    def _has_host_column(self, columns: List[str]) -> bool:
        for column in columns:
            if self._contains_exact_word(column, self.host_identifier):
                return True
        return False
    
    def find_keyword_columns(self, columns: List[str]) -> Dict[str, List[str]]:
        keyword_columns = {}
        
        has_host_column = self._has_host_column(columns)
        
        if not has_host_column:
            self.stats['non_host_tables_skipped'] += 1
            return keyword_columns
        
        self.stats['host_tables_found'] += 1
        
        host_columns = []
        for column in columns:
            if self._contains_exact_word(column, self.host_identifier):
                host_columns.append(column)
        
        if host_columns:
            keyword_columns['host'] = host_columns
            self.stats['keywords_found']['host'] = len(host_columns)
        
        if keyword_columns:
            for keyword, patterns in self.secondary_keywords.items():
                matching_columns = []
                
                for column in columns:
                    for pattern in patterns:
                        if self._contains_exact_word(column, pattern):
                            matching_columns.append(column)
                            break
                
                if matching_columns:
                    keyword_columns[keyword] = matching_columns
                    self.stats['keywords_found'][keyword] = len(matching_columns)
        
        return keyword_columns

class RealtimeAssetExtractor:
    def __init__(self, keyword_processor: SmartKeywordProcessor):
        self.processor = keyword_processor
        self.extraction_stats = {
            'batches_processed': 0,
            'total_rows_processed': 0,
            'extraction_errors': 0
        }
    
    async def extract_and_build_cmdb_realtime(self, client, table_path: str, keyword_columns: Dict[str, List[str]]) -> int:
        total_rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return 0
            
            logger.info(f"PROCESSING TABLE: {table_path} ({table.num_rows:,} rows)")
            
            all_columns = [field.name for field in table.schema]
            
            host_column = None
            for col in keyword_columns.get('host', []):
                host_column = col
                break
            
            if not host_column:
                return 0
            
            batch_size = 100000
            offset = 0
            
            while True:
                query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{host_column}` IS NOT NULL
                AND SAFE_CAST(`{host_column}` AS STRING) != ''
                AND SAFE_CAST(`{host_column}` AS STRING) NOT IN ('NULL', 'NONE', 'UNKNOWN', 'N/A', 'NIL')
                LIMIT {batch_size} OFFSET {offset}
                """
                
                try:
                    job = client.query(query)
                    results = list(job.result())
                    
                    if not results:
                        break
                    
                    batch_rows = self._process_rows_to_cmdb_realtime(results, table_path, all_columns, keyword_columns, host_column)
                    
                    total_rows_processed += batch_rows
                    offset += batch_size
                    
                    logger.info(f"PROCESSED {total_rows_processed:,} ROWS - CMDB HAS {len(self.processor.cmdb_builder.cmdb):,} HOSTS")
                    
                    if len(results) < batch_size:
                        break
                        
                except Exception as e:
                    logger.error(f"BATCH PROCESSING FAILED: {e}")
                    self.extraction_stats['extraction_errors'] += 1
                    break
            
            self.processor.cmdb_builder.stats['tables_processed'] += 1
            
        except Exception as e:
            logger.error(f"TABLE PROCESSING FAILED: {e}")
            self.extraction_stats['extraction_errors'] += 1
        
        return total_rows_processed
    
    def _process_rows_to_cmdb_realtime(self, results: List, table_path: str, all_columns: List[str], keyword_columns: Dict[str, List[str]], host_column: str) -> int:
        rows_processed = 0
        
        host_column_idx = all_columns.index(host_column)
        
        for row in results:
            if host_column_idx < len(row) and row[host_column_idx]:
                hostname = str(row[host_column_idx]).strip()
                
                if not hostname or hostname.upper() in ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NIL']:
                    continue
                
                for keyword_type, columns in keyword_columns.items():
                    for column_name in columns:
                        try:
                            column_idx = all_columns.index(column_name)
                            if column_idx < len(row) and row[column_idx] is not None:
                                attribute_value = str(row[column_idx]).strip()
                                if attribute_value:
                                    self.processor.cmdb_builder.add_host_to_cmdb(
                                        hostname, keyword_type, attribute_value, table_path
                                    )
                        except (ValueError, IndexError):
                            continue
                
                rows_processed += 1
                self.processor.cmdb_builder.stats['rows_processed'] += 1
        
        return rows_processed

class ComprehensiveDiscoveryOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cmdb_builder = RealtimeCMDBBuilder()
        self.processor = SmartKeywordProcessor(self.cmdb_builder)
        self.extractor = RealtimeAssetExtractor(self.processor)
        
        self.orchestration_stats = {
            'projects_processed': 0,
            'datasets_processed': 0,
            'tables_processed': 0,
            'processing_start_time': None,
            'processing_errors': 0
        }
    
    async def execute_comprehensive_discovery(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        self.orchestration_stats['processing_start_time'] = datetime.now()
        
        logger.info("REAL-TIME CMDB BUILDING INITIATED")
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"PROJECT: {project_id}")
            
            try:
                await self._process_complete_project(client_manager, project_id)
                self.orchestration_stats['projects_processed'] += 1
                
            except Exception as e:
                logger.error(f"PROJECT {project_id} FAILED: {e}")
                self.orchestration_stats['processing_errors'] += 1
        
        final_cmdb = self.cmdb_builder.get_current_cmdb_snapshot()
        cmdb_stats = self.cmdb_builder.get_stats()
        
        processing_time = (datetime.now() - self.orchestration_stats['processing_start_time']).total_seconds()
        
        logger.info("REAL-TIME CMDB BUILDING COMPLETE")
        logger.info(f"FINAL CMDB SIZE: {len(final_cmdb):,} UNIQUE HOSTS")
        logger.info(f"HOST TABLES PROCESSED: {self.processor.stats['host_tables_found']:,}")
        logger.info(f"NON-HOST TABLES SKIPPED: {self.processor.stats['non_host_tables_skipped']:,}")
        logger.info(f"TOTAL ATTRIBUTES ADDED: {cmdb_stats['attributes_added']:,}")
        logger.info(f"TOTAL ROWS PROCESSED: {cmdb_stats['rows_processed']:,}")
        
        return {
            'discovery_stats': {
                'total_assets': len(final_cmdb),
                'host_tables_processed': self.processor.stats['host_tables_found'],
                'non_host_tables_skipped': self.processor.stats['non_host_tables_skipped'],
                'total_attributes_added': cmdb_stats['attributes_added'],
                'total_rows_processed': cmdb_stats['rows_processed'],
                'duplicate_hosts_updated': cmdb_stats['duplicate_hosts_updated'],
                'processing_time_minutes': processing_time / 60,
                'realtime_cmdb_building': True
            },
            'assets': final_cmdb,
            'cmdb_stats': cmdb_stats
        }
    
    async def _process_complete_project(self, client_manager, project_id: str):
        with client_manager.get_client() as client:
            try:
                datasets = list(client.list_datasets(project=project_id))
                
                prioritized_datasets = self._prioritize_datasets(datasets)
                
                for priority, dataset in prioritized_datasets:
                    try:
                        await self._process_complete_dataset(client, project_id, dataset.dataset_id)
                        self.orchestration_stats['datasets_processed'] += 1
                        
                    except Exception as e:
                        logger.error(f"DATASET {dataset.dataset_id} FAILED: {e}")
                        self.orchestration_stats['processing_errors'] += 1
                        
            except Exception as e:
                logger.error(f"PROJECT LISTING FAILED: {e}")
                self.orchestration_stats['processing_errors'] += 1
    
    async def _process_complete_dataset(self, client, project_id: str, dataset_id: str):
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            for table_ref in tables:
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                
                try:
                    await self._process_complete_table(client, table_path)
                    self.orchestration_stats['tables_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"TABLE {table_ref.table_id} FAILED: {e}")
                    self.orchestration_stats['processing_errors'] += 1
            
        except Exception as e:
            logger.error(f"DATASET PROCESSING FAILED: {e}")
            self.orchestration_stats['processing_errors'] += 1
    
    async def _process_complete_table(self, client, table_path: str):
        try:
            table = client.get_table(table_path)
            if not table.schema:
                return
            
            columns = [field.name for field in table.schema]
            keyword_columns = self.processor.find_keyword_columns(columns)
            
            if not keyword_columns:
                return
            
            logger.info(f"HOST TABLE FOUND: {table_path}")
            
            rows_processed = await self.extractor.extract_and_build_cmdb_realtime(
                client, table_path, keyword_columns
            )
            
            if rows_processed > 0:
                logger.info(f"COMPLETED: {table_path} - {rows_processed:,} rows processed")
            
        except Exception as e:
            logger.error(f"TABLE PROCESSING FAILED: {e}")
            self.orchestration_stats['processing_errors'] += 1
    
    def _prioritize_datasets(self, datasets) -> List[Tuple[int, Any]]:
        prioritized = []
        
        for dataset in datasets:
            priority = 100
            name = dataset.dataset_id.upper()
            
            if 'SAS_BI' in name:
                priority = 1
            elif any(keyword in name for keyword in ['HOST', 'ENDPOINT', 'ASSET', 'CMDB']):
                priority = 2
            elif any(keyword in name for keyword in ['SECURITY', 'LOG']):
                priority = 3
            
            prioritized.append((priority, dataset))
        
        return sorted(prioritized, key=lambda x: x[0])

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.orchestrator = ComprehensiveDiscoveryOrchestrator(config)
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        return await self.orchestrator.execute_comprehensive_discovery(client_managers)