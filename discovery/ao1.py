# discovery/ao1.py

import asyncio
import logging
import re
import gc
import psutil
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class RealtimeCMDBBuilder:
    def __init__(self, database_manager=None):
        self.cmdb = {}
        self.database_manager = database_manager
        self.stored_count = 0
        self.processing_stats = {
            'hosts_discovered': 0,
            'attributes_enriched': 0,
            'tables_processed': 0,
            'rows_processed': 0,
            'cells_analyzed': 0,
            'coverage_flags_set': 0,
            'enrichment_operations': 0,
            'start_time': datetime.now()
        }
        
        self.field_mappings = self._initialize_field_mappings()
        self.hostname_patterns = self._initialize_hostname_patterns()
        self.enrichment_rules = self._initialize_enrichment_rules()
    
    def _initialize_field_mappings(self) -> Dict[str, str]:
        return {
            'hostname': ['hostname', 'host_name', 'computername', 'computer_name', 'device_name', 'endpoint_name', 'asset_name'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'internal_ip', 'private_ip', 'host_ip', 'device_ip'],
            'fqdn': ['fqdn', 'full_name', 'dns_name', 'qualified_name', 'domain_name'],
            'mac_address': ['mac_address', 'mac', 'physical_address', 'ethernet_address', 'hw_address'],
            'infrastructure_type': ['infrastructure_type', 'hosting_type', 'deployment_type', 'platform_type'],
            'system_classification': ['system_classification', 'os_type', 'operating_system', 'platform', 'os_family'],
            'business_unit': ['business_unit', 'bu', 'department', 'division', 'org_unit', 'cost_center'],
            'global_region': ['global_region', 'region', 'geo_region', 'location', 'geography', 'area'],
            'country': ['country', 'country_code', 'nation', 'territory'],
            'datacenter': ['datacenter', 'dc', 'site', 'facility', 'location_name'],
            'zone': ['zone', 'availability_zone', 'az', 'cluster', 'rack', 'pod'],
            'cloud_provider': ['cloud_provider', 'cloud_vendor', 'provider', 'vendor'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
            'environment': ['environment', 'env', 'tier', 'stage', 'lifecycle'],
            'application_class': ['application_class', 'app_class', 'service_class', 'workload_type'],
            'criticality': ['criticality', 'priority', 'importance', 'tier', 'class'],
            'owner': ['owner', 'responsible_party', 'asset_owner', 'business_owner'],
            'technical_contact': ['technical_contact', 'tech_contact', 'admin', 'administrator'],
            'cio': ['cio', 'cio_org', 'cio_organization', 'it_organization'],
            'manufacturer': ['manufacturer', 'vendor', 'make', 'brand'],
            'model': ['model', 'product', 'type', 'variant'],
            'serial_number': ['serial_number', 'serial', 'sn', 'asset_tag'],
            'network_segment': ['network_segment', 'segment', 'vlan', 'subnet'],
            'domain': ['domain', 'ad_domain', 'dns_domain', 'forest'],
            'patch_level': ['patch_level', 'patches', 'updates', 'security_patches'],
            'antivirus_product': ['antivirus', 'av_product', 'endpoint_protection', 'security_software']
        }
    
    def _initialize_hostname_patterns(self) -> List[re.Pattern]:
        patterns = [
            re.compile(r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9], re.IGNORECASE),
            re.compile(r'^[a-zA-Z0-9]{1,63}, re.IGNORECASE),
            re.compile(r'^[a-zA-Z]{2,6}[0-9]{1,8}, re.IGNORECASE),
            re.compile(r'^[a-zA-Z]+\-[a-zA-Z0-9]+\-[a-zA-Z0-9]+, re.IGNORECASE),
            re.compile(r'^(srv|web|app|db|sql|dc|vm|host|pc|ws)\-?[a-zA-Z0-9]+', re.IGNORECASE)
        ]
        return patterns
    
    def _initialize_enrichment_rules(self) -> Dict[str, Any]:
        return {
            'cloud_detection': {
                'aws': ['aws', 'amazon', 'ec2', 'lambda', 's3'],
                'azure': ['azure', 'microsoft', 'vm', 'webapp'],
                'gcp': ['gcp', 'google', 'compute', 'cloud'],
                'kubernetes': ['k8s', 'kube', 'pod', 'node']
            },
            'environment_detection': {
                'production': ['prod', 'production', 'live', 'prd'],
                'development': ['dev', 'development', 'devel'],
                'test': ['test', 'testing', 'tst', 'qa'],
                'staging': ['stage', 'staging', 'stg', 'uat']
            },
            'infrastructure_detection': {
                'on_premise': ['onprem', 'datacenter', 'physical', 'bare'],
                'cloud': ['cloud', 'saas', 'paas', 'iaas'],
                'hybrid': ['hybrid', 'mixed', 'multi'],
                'virtual': ['vm', 'virtual', 'hyperv', 'vmware']
            }
        }
    
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname:
            return ""
        
        hostname = str(hostname).strip().upper()
        
        if '.' in hostname and not hostname.count('.') > 3:
            hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Z0-9\-_]', '', hostname)
        
        return hostname
    
    def is_valid_hostname(self, hostname: str) -> bool:
        if not hostname or len(hostname) < 2 or len(hostname) > 253:
            return False
        
        if hostname.upper() in ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NIL', 'LOCALHOST', '127.0.0.1']:
            return False
        
        return any(pattern.match(hostname) for pattern in self.hostname_patterns)
    
    def extract_hostname_candidates(self, row_data: Dict[str, Any]) -> List[Tuple[str, str]]:
        candidates = []
        
        for column_name, value in row_data.items():
            if not value:
                continue
            
            column_lower = column_name.lower()
            value_str = str(value).strip()
            
            if any(pattern in column_lower for pattern in self.field_mappings['hostname']):
                if self.is_valid_hostname(value_str):
                    candidates.append((value_str, column_name))
        
        return candidates
    
    def intelligent_field_mapping(self, column_name: str) -> Optional[str]:
        column_lower = column_name.lower()
        
        for field_type, patterns in self.field_mappings.items():
            for pattern in patterns:
                if pattern in column_lower:
                    return field_type
        
        if any(term in column_lower for term in ['log', 'event', 'time', 'date']):
            return 'log_data'
        
        return 'custom_attribute'
    
    def apply_intelligent_enrichment(self, hostname: str, all_data: Dict[str, Any]) -> Dict[str, Any]:
        enriched = {}
        
        hostname_lower = hostname.lower()
        
        for category, detection_rules in self.enrichment_rules.items():
            for value, keywords in detection_rules.items():
                if any(keyword in hostname_lower for keyword in keywords):
                    if category == 'cloud_detection':
                        enriched['cloud_provider'] = [value]
                        enriched['infrastructure_type'] = ['cloud']
                    elif category == 'environment_detection':
                        enriched['environment'] = [value]
                    elif category == 'infrastructure_detection':
                        enriched['infrastructure_type'] = [value]
        
        for column_name, values in all_data.items():
            if not values:
                continue
            
            column_lower = column_name.lower()
            
            if 'region' in column_lower:
                enriched['global_region'] = values if isinstance(values, list) else [values]
            elif 'country' in column_lower:
                enriched['country'] = values if isinstance(values, list) else [values]
            elif any(term in column_lower for term in ['business', 'bu', 'dept']):
                enriched['business_unit'] = values if isinstance(values, list) else [values]
            elif any(term in column_lower for term in ['critical', 'priority', 'tier']):
                enriched['criticality'] = values if isinstance(values, list) else [values]
            elif any(term in column_lower for term in ['owner', 'responsible']):
                enriched['owner'] = values if isinstance(values, list) else [values]
            elif any(term in column_lower for term in ['datacenter', 'site', 'facility']):
                enriched['datacenter'] = values if isinstance(values, list) else [values]
        
        return enriched
    
    def set_coverage_flags(self, host_data: Dict[str, Any], source_table: str) -> Dict[str, bool]:
        table_lower = source_table.lower()
        coverage_flags = host_data.get('coverage_flags', {})
        
        coverage_mappings = {
            'in_chronicle': ['chronicle', 'backstory', 'google_security'],
            'in_crowdstrike': ['crowdstrike', 'cs_', 'falcon', 'crwd'],
            'in_original_cmdb': ['cmdb', 'v_dim_endpoint', 'servicenow', 'remedy'],
            'in_splunk': ['splunk', 'spl_', 'universal_forwarder'],
            'in_tanium': ['tanium', 'tan_', 'endpoint_platform'],
            'in_dlp': ['dlp', 'data_loss', 'symantec_dlp', 'forcepoint']
        }
        
        for flag, keywords in coverage_mappings.items():
            if any(keyword in table_lower for keyword in keywords):
                coverage_flags[flag] = True
                self.processing_stats['coverage_flags_set'] += 1
        
        return coverage_flags
    
    def process_single_host(self, hostname: str, row_data: Dict[str, Any], source_table: str):
        normalized_hostname = self.normalize_hostname(hostname)
        
        if not normalized_hostname or not self.is_valid_hostname(normalized_hostname):
            return
        
        is_new_host = normalized_hostname not in self.cmdb
        
        if is_new_host:
            self.cmdb[normalized_hostname] = {
                'hostname': normalized_hostname,
                'primary_identity': normalized_hostname,
                'all_data': defaultdict(set),
                'source_tables': set(),
                'coverage_flags': {},
                'enrichment_data': {},
                'quality_metrics': {},
                'first_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'source_count': 0,
                'total_rows': 0
            }
            self.processing_stats['hosts_discovered'] += 1
            logger.info(f"New host discovered: {normalized_hostname}")
        
        host = self.cmdb[normalized_hostname]
        
        new_attributes_count = 0
        for column_name, value in row_data.items():
            if value is None or str(value).strip() == '':
                continue
            
            clean_value = str(value).strip()
            mapped_field = self.intelligent_field_mapping(column_name)
            
            if mapped_field not in host['all_data']:
                host['all_data'][mapped_field] = set()
            
            if clean_value not in host['all_data'][mapped_field]:
                host['all_data'][mapped_field].append(clean_value)
                new_attributes_count += 1
                self.processing_stats['attributes_enriched'] += 1
        
        host['source_tables'].add(source_table)
        host['source_count'] = len(host['source_tables'])
        host['total_rows'] += 1
        host['last_updated'] = datetime.now().isoformat()
        
        host['coverage_flags'] = self.set_coverage_flags(host, source_table)
        
        enrichment_data = self.apply_intelligent_enrichment(normalized_hostname, host['all_data'])
        if enrichment_data:
            host['enrichment_data'].update(enrichment_data)
            self.processing_stats['enrichment_operations'] += 1
        
        host['quality_metrics'] = self.calculate_quality_metrics(host)
        
        if self.database_manager:
            self.store_host_to_database(normalized_hostname, host)
        
        self.processing_stats['cells_analyzed'] += len(row_data)
        
        if new_attributes_count > 0:
            logger.debug(f"Host {normalized_hostname} enriched with {new_attributes_count} new attributes")
    
    def calculate_quality_metrics(self, host_data: Dict[str, Any]) -> Dict[str, float]:
        all_data = host_data.get('all_data', {})
        coverage_flags = host_data.get('coverage_flags', {})
        
        data_completeness = len([v for v in all_data.values() if v]) / max(len(self.field_mappings), 1)
        coverage_score = sum(1 for v in coverage_flags.values() if v) / max(len(coverage_flags), 1)
        source_reliability = min(1.0, host_data.get('source_count', 0) / 3.0)
        
        overall_quality = (data_completeness * 0.4 + coverage_score * 0.4 + source_reliability * 0.2)
        
        return {
            'data_completeness': data_completeness,
            'coverage_score': coverage_score,
            'source_reliability': source_reliability,
            'overall_quality': overall_quality
        }
    
    def store_host_to_database(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        try:
            serialized_data = self.prepare_for_database(host_data)
            
            if hasattr(self.database_manager, 'store_single_host_immediately'):
                success = self.database_manager.store_single_host_immediately(hostname, serialized_data)
            else:
                success = False
            
            if success:
                self.stored_count += 1
            
            return success
        except Exception as e:
            logger.error(f"Database storage failed for {hostname}: {e}")
            return False
    
    def prepare_for_database(self, host_data: Dict[str, Any]) -> Dict[str, Any]:
        serialized = {}
        
        for key, value in host_data.items():
            if isinstance(value, set):
                serialized[key] = list(value)
            elif isinstance(value, defaultdict):
                serialized[key] = {k: list(v) if isinstance(v, set) else v for k, v in value.items()}
            else:
                serialized[key] = value
        
        return serialized
    
    def get_comprehensive_results(self) -> Dict[str, Any]:
        processing_time = (datetime.now() - self.processing_stats['start_time']).total_seconds()
        
        return {
            'assets': {hostname: self.prepare_for_database(data) for hostname, data in self.cmdb.items()},
            'discovery_stats': {
                'total_unique_hosts': len(self.cmdb),
                'processing_time_seconds': processing_time,
                'hosts_per_second': len(self.cmdb) / processing_time if processing_time > 0 else 0,
                'tables_processed': self.processing_stats['tables_processed'],
                'rows_processed': self.processing_stats['rows_processed'],
                'cells_analyzed': self.processing_stats['cells_analyzed'],
                'attributes_enriched': self.processing_stats['attributes_enriched'],
                'coverage_flags_set': self.processing_stats['coverage_flags_set'],
                'enrichment_operations': self.processing_stats['enrichment_operations'],
                'database_storage_count': self.stored_count
            }
        }

class AdvancedTableProcessor:
    def __init__(self, cmdb_builder: RealtimeCMDBBuilder):
        self.cmdb_builder = cmdb_builder
        self.processed_tables = set()
        self.processing_stats = {
            'tables_attempted': 0,
            'tables_successful': 0,
            'rows_processed': 0,
            'hosts_found': 0,
            'processing_errors': 0
        }
    
    def detect_hostname_columns(self, schema_fields: List[Any]) -> List[str]:
        hostname_columns = []
        
        hostname_indicators = [
            'hostname', 'host_name', 'computername', 'computer_name', 'device_name',
            'endpoint_name', 'asset_name', 'machine_name', 'system_name', 'server_name'
        ]
        
        for field in schema_fields:
            field_name = field.name.lower()
            if any(indicator in field_name for indicator in hostname_indicators):
                hostname_columns.append(field.name)
        
        return hostname_columns
    
    async def process_table_comprehensively(self, client, table_path: str) -> Dict[str, Any]:
        if table_path in self.processed_tables:
            return {'skipped': True, 'reason': 'already_processed'}
        
        self.processing_stats['tables_attempted'] += 1
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return {'skipped': True, 'reason': 'empty_table'}
            
            columns = [field.name for field in table.schema]
            hostname_columns = self.detect_hostname_columns(table.schema)
            
            if not hostname_columns:
                return {'skipped': True, 'reason': 'no_hostname_columns'}
            
            primary_hostname_column = hostname_columns[0]
            
            logger.info(f"Processing table: {table_path}")
            logger.info(f"Rows: {table.num_rows:,}, Columns: {len(columns)}, Hostname column: {primary_hostname_column}")
            
            batch_size = self.calculate_optimal_batch_size(table.num_rows)
            offset = 0
            total_processed = 0
            hosts_found = 0
            
            while True:
                query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{primary_hostname_column}` IS NOT NULL
                AND TRIM(`{primary_hostname_column}`) != ''
                LIMIT {batch_size} OFFSET {offset}
                """
                
                try:
                    job = client.query(query)
                    results = list(job.result())
                    
                    if not results:
                        break
                    
                    batch_hosts = 0
                    for row in results:
                        row_data = dict(zip(columns, row))
                        hostname_value = row_data.get(primary_hostname_column)
                        
                        if hostname_value and str(hostname_value).strip():
                            self.cmdb_builder.process_single_host(
                                str(hostname_value).strip(), row_data, table_path
                            )
                            batch_hosts += 1
                    
                    total_processed += len(results)
                    hosts_found += batch_hosts
                    offset += batch_size
                    
                    self.processing_stats['rows_processed'] += len(results)
                    self.processing_stats['hosts_found'] += batch_hosts
                    
                    if len(results) < batch_size:
                        break
                    
                    if total_processed % 10000 == 0:
                        logger.info(f"Progress: {total_processed:,} rows, {hosts_found:,} hosts")
                        gc.collect()
                
                except Exception as e:
                    logger.error(f"Batch processing failed for {table_path}: {e}")
                    self.processing_stats['processing_errors'] += 1
                    break
            
            self.processed_tables.add(table_path)
            self.processing_stats['tables_successful'] += 1
            
            result = {
                'table_path': table_path,
                'rows_processed': total_processed,
                'hosts_found': hosts_found,
                'hostname_column': primary_hostname_column,
                'total_columns': len(columns),
                'success': True
            }
            
            logger.info(f"Table completed: {table_path} - {total_processed:,} rows, {hosts_found:,} hosts")
            return result
            
        except Exception as e:
            logger.error(f"Table processing failed: {table_path} - {e}")
            self.processing_stats['processing_errors'] += 1
            return {'table_path': table_path, 'success': False, 'error': str(e)}
    
    def calculate_optimal_batch_size(self, total_rows: int) -> int:
        if total_rows < 1000:
            return 500
        elif total_rows < 10000:
            return 1000
        elif total_rows < 100000:
            return 5000
        elif total_rows < 1000000:
            return 10000
        else:
            return 25000
    
    def get_processing_stats(self) -> Dict[str, Any]:
        return self.processing_stats.copy()

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        from storage.database import QuantumEnhancedDatabaseManager
        self.database_manager = QuantumEnhancedDatabaseManager(
            config.get('database_path', 'ao1_discovery.db')
        )
        
        self.cmdb_builder = RealtimeCMDBBuilder(self.database_manager)
        self.table_processor = AdvancedTableProcessor(self.cmdb_builder)
        
        self.discovery_stats = {
            'start_time': datetime.now(),
            'projects_processed': 0,
            'datasets_processed': 0,
            'tables_processed': 0,
            'total_execution_time': 0.0
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("AO1 Enhanced Discovery Engine Starting")
        start_time = datetime.now()
        
        total_results = []
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"Processing project: {project_id}")
            
            try:
                with client_manager.get_client() as client:
                    datasets = list(client.list_datasets(project=project_id))
                    self.discovery_stats['datasets_processed'] += len(datasets)
                    
                    logger.info(f"Found {len(datasets)} datasets in {project_id}")
                    
                    for dataset in datasets:
                        try:
                            dataset_tables = list(client.list_tables(dataset))
                            logger.info(f"Processing dataset {dataset.dataset_id}: {len(dataset_tables)} tables")
                            
                            with ThreadPoolExecutor(max_workers=self.config.get('max_workers', 16)) as executor:
                                table_futures = []
                                
                                for table_ref in dataset_tables:
                                    table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                                    future = executor.submit(
                                        asyncio.run,
                                        self.table_processor.process_table_comprehensively(client, table_path)
                                    )
                                    table_futures.append(future)
                                
                                for future in as_completed(table_futures):
                                    try:
                                        result = future.result(timeout=300)
                                        total_results.append(result)
                                        
                                        if result.get('success'):
                                            self.discovery_stats['tables_processed'] += 1
                                    except Exception as e:
                                        logger.error(f"Table processing future failed: {e}")
                        
                        except Exception as e:
                            logger.error(f"Dataset processing failed for {dataset.dataset_id}: {e}")
                
                self.discovery_stats['projects_processed'] += 1
                
            except Exception as e:
                logger.error(f"Project processing failed for {project_id}: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        self.discovery_stats['total_execution_time'] = processing_time
        
        final_results = self.cmdb_builder.get_comprehensive_results()
        final_results['discovery_stats'].update(self.discovery_stats)
        final_results['table_processing_stats'] = self.table_processor.get_processing_stats()
        
        logger.info("AO1 Enhanced Discovery Completed")
        logger.info(f"Total hosts discovered: {len(final_results['assets']):,}")
        logger.info(f"Total processing time: {processing_time / 60:.1f} minutes")
        logger.info(f"Database storage count: {self.cmdb_builder.stored_count}")
        
        return final_results
    
    def get_discovery_summary(self) -> Dict[str, Any]:
        return {
            'engine_name': 'AO1_Enhanced_Discovery',
            'discovery_stats': self.discovery_stats,
            'cmdb_stats': self.cmdb_builder.processing_stats,
            'processor_stats': self.table_processor.get_processing_stats(),
            'database_path': self.database_manager.db_path,
            'configuration': self.config
        }