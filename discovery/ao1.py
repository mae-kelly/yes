# discovery/ao1.py

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class HostEntityResolver:
    def __init__(self):
        self.identity_hierarchy = [
            'hostname', 'fqdn', 'computer_name', 'host', 
            'asset_id', 'serial_number', 
            'ip_address', 'mac_address'
        ]
        
        self.entity_clusters = defaultdict(set)
        self.canonical_identities = {}
        self.identity_mappings = defaultdict(set)
        
    def normalize_hostname(self, value: str) -> str:
        if not value or not isinstance(value, str):
            return ""
        
        value = value.strip().upper()
        
        if '.' in value:
            hostname = value.split('.')[0]
        else:
            hostname = value
        
        hostname = re.sub(r'[^A-Z0-9\-]', '', hostname)
        
        if len(hostname) < 1 or len(hostname) > 63:
            return ""
            
        return hostname
    
    def normalize_ip_address(self, value: str) -> str:
        if not value:
            return ""
        
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, str(value).strip()):
            return str(value).strip()
        return ""
    
    def create_canonical_identity(self, value: str, field_type: str) -> Optional[str]:
        if field_type in ['hostname', 'fqdn', 'computer_name', 'host']:
            normalized = self.normalize_hostname(value)
            if normalized:
                return f"HOST_{normalized}"
        
        elif field_type == 'asset_id':
            clean_value = str(value).strip().upper()
            if clean_value and len(clean_value) > 2:
                return f"ASSET_{clean_value}"
        
        elif field_type == 'serial_number':
            clean_value = str(value).strip().upper()
            if clean_value and len(clean_value) > 3:
                return f"SERIAL_{clean_value}"
        
        elif field_type == 'ip_address':
            normalized = self.normalize_ip_address(value)
            if normalized:
                return f"IP_{normalized}"
        
        elif field_type == 'mac_address':
            mac = re.sub(r'[^0-9A-Fa-f]', '', str(value).upper())
            if len(mac) == 12:
                normalized = ':'.join([mac[i:i+2] for i in range(0, 12, 2)])
                return f"MAC_{normalized}"
        
        return None
    
    def add_identity(self, value: str, field_type: str, source_info: Dict[str, Any]):
        canonical = self.create_canonical_identity(value, field_type)
        if not canonical:
            return None
        
        raw_value = str(value).strip()
        
        self.identity_mappings[canonical].add((raw_value, field_type, source_info['table_path']))
        
        if canonical.startswith('HOST_'):
            hostname_key = canonical.split('_', 1)[1]
            self.entity_clusters[hostname_key].add(canonical)
            
            if hostname_key not in self.canonical_identities:
                self.canonical_identities[hostname_key] = canonical
        
        return canonical
    
    def resolve_entity_clusters(self) -> Dict[str, Dict[str, Any]]:
        resolved_entities = {}
        
        for hostname_key, identity_set in self.entity_clusters.items():
            primary_identity = self.canonical_identities.get(hostname_key, list(identity_set)[0])
            
            merged_entity = {
                'primary_identity': primary_identity,
                'hostname_key': hostname_key,
                'all_identities': list(identity_set),
                'attributes': defaultdict(set),
                'source_tables': set(),
                'source_columns': set(),
                'coverage_flags': {},
                'identity_sources': defaultdict(list)
            }
            
            for identity in identity_set:
                for raw_value, field_type, table_path in self.identity_mappings[identity]:
                    merged_entity['attributes'][field_type].add(raw_value)
                    merged_entity['source_tables'].add(table_path)
                    merged_entity['source_columns'].add(f"{table_path}:{field_type}")
                    merged_entity['identity_sources'][identity].append({
                        'value': raw_value,
                        'field_type': field_type,
                        'table': table_path
                    })
            
            for attr_type, value_set in merged_entity['attributes'].items():
                merged_entity['attributes'][attr_type] = list(value_set)
            
            merged_entity['source_tables'] = list(merged_entity['source_tables'])
            merged_entity['source_columns'] = list(merged_entity['source_columns'])
            
            resolved_entities[hostname_key] = merged_entity
        
        return resolved_entities

class SmartKeywordProcessor:
    def __init__(self):
        self.entity_resolver = HostEntityResolver()
        
        self.primary_keywords = {
            'host': ['host'],
            'hostname': ['hostname'],
            'fqdn': ['fqdn'],
            'computer_name': ['computer_name', 'computername']
        }
        
        self.secondary_keywords = {
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
            'values_extracted': 0,
            'tables_scanned': 0,
            'host_tables_found': 0,
            'non_host_tables_skipped': 0,
            'entities_resolved': 0,
            'identity_clusters_created': 0
        }
    
    def _contains_exact_word(self, column_name: str, keyword: str) -> bool:
        column_lower = column_name.lower()
        keyword_lower = keyword.lower()
        
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        
        return bool(re.search(pattern, column_lower))
    
    def find_keyword_columns(self, columns: List[str]) -> Dict[str, List[str]]:
        keyword_columns = {}
        
        has_host_column = self._has_host_column(columns)
        
        if not has_host_column:
            self.stats['non_host_tables_skipped'] += 1
            self.stats['columns_processed'] += len(columns)
            return keyword_columns
        
        self.stats['host_tables_found'] += 1
        
        for keyword, patterns in self.primary_keywords.items():
            matching_columns = []
            
            for column in columns:
                for pattern in patterns:
                    if self._contains_exact_word(column, pattern):
                        matching_columns.append(column)
                        break
            
            if matching_columns:
                keyword_columns[keyword] = matching_columns
                self.stats['keywords_found'][keyword] = len(matching_columns)
        
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
        
        self.stats['columns_processed'] += len(columns)
        return keyword_columns
    
    def _has_host_column(self, columns: List[str]) -> bool:
        host_indicators = ['host', 'hostname', 'fqdn', 'computer_name', 'computername']
        
        for column in columns:
            for indicator in host_indicators:
                if self._contains_exact_word(column, indicator):
                    return True
        
        return False
    
    def add_extracted_value(self, value: str, field_type: str, table_path: str, column_name: str):
        source_info = {
            'table_path': table_path,
            'column_name': column_name
        }
        
        canonical_identity = self.entity_resolver.add_identity(value, field_type, source_info)
        return canonical_identity
    
    def resolve_all_entities(self) -> Dict[str, Dict[str, Any]]:
        resolved = self.entity_resolver.resolve_entity_clusters()
        self.stats['entities_resolved'] = len(resolved)
        self.stats['identity_clusters_created'] = len(self.entity_resolver.entity_clusters)
        return resolved

class AdvancedAssetExtractor:
    def __init__(self, keyword_processor: SmartKeywordProcessor):
        self.processor = keyword_processor
        self.extraction_stats = {
            'batches_processed': 0,
            'total_values': 0,
            'unique_assets': 0,
            'extraction_errors': 0
        }
    
    async def extract_all_column_values(self, client, table_path: str, column_name: str, keyword_type: str) -> int:
        total_extracted = 0
        
        count_query = f"""
        SELECT COUNT(*) as total 
        FROM `{table_path}` 
        WHERE `{column_name}` IS NOT NULL 
        AND SAFE_CAST(`{column_name}` AS STRING) IS NOT NULL
        AND SAFE_CAST(`{column_name}` AS STRING) != ''
        AND SAFE_CAST(`{column_name}` AS STRING) NOT IN ('NULL', 'NONE', 'UNKNOWN', 'N/A', 'NIL', '0')
        """
        count_job = client.query(count_query)
        count_result = list(count_job.result())
        total_values = count_result[0]['total'] if count_result else 0
        
        if total_values == 0:
            return 0
        
        logger.info(f"🔥 EXTRACTING {total_values:,} VALUES FROM {column_name} ({keyword_type})")
        
        batch_size = 2000000
        offset = 0
        
        while True:
            extraction_query = f"""
            SELECT SAFE_CAST(`{column_name}` AS STRING) as value
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            AND SAFE_CAST(`{column_name}` AS STRING) IS NOT NULL
            AND SAFE_CAST(`{column_name}` AS STRING) != ''
            AND SAFE_CAST(`{column_name}` AS STRING) NOT IN ('NULL', 'NONE', 'UNKNOWN', 'N/A', 'NIL', '0')
            LIMIT {batch_size} OFFSET {offset}
            """
            
            try:
                job = client.query(extraction_query)
                results = list(job.result())
                
                if not results:
                    break
                
                batch_extracted = self._process_value_batch_for_entity_resolution(results, table_path, column_name, keyword_type)
                
                total_extracted += batch_extracted
                offset += batch_size
                
                logger.info(f"📊 EXTRACTED {total_extracted:,}/{total_values:,} values")
                
                if len(results) < batch_size:
                    break
                    
            except Exception as e:
                logger.error(f"❌ EXTRACTION FAILED: {e}")
                self.extraction_stats['extraction_errors'] += 1
                break
        
        self.extraction_stats['total_values'] += total_extracted
        
        return total_extracted
    
    def _process_value_batch_for_entity_resolution(self, results: List, table_path: str, column_name: str, keyword_type: str) -> int:
        extracted_count = 0
        
        for row in results:
            value = None
            
            if hasattr(row, 'value'):
                value = row.value
            elif isinstance(row, dict):
                value = row.get('value')
            elif isinstance(row, (list, tuple)) and len(row) > 0:
                value = row[0]
            
            if value is not None:
                clean_value = str(value).strip()
                
                if self._is_valid_asset_value(clean_value):
                    self.processor.add_extracted_value(clean_value, keyword_type, table_path, column_name)
                    extracted_count += 1
        
        return extracted_count
    
    def _is_valid_asset_value(self, value: str) -> bool:
        if not value or len(value) < 1 or len(value) > 1000:
            return False
        
        if value.upper() in {'NULL', 'NONE', '', '-', '0', 'N/A'}:
            return False
        
        return True

class ComprehensiveDiscoveryOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.processor = SmartKeywordProcessor()
        self.extractor = AdvancedAssetExtractor(self.processor)
        
        self.orchestration_stats = {
            'projects_processed': 0,
            'datasets_processed': 0,
            'tables_processed': 0,
            'total_assets_discovered': 0,
            'processing_start_time': None,
            'processing_errors': 0
        }
    
    async def execute_comprehensive_discovery(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        self.orchestration_stats['processing_start_time'] = datetime.now()
        
        logger.info("🚀 EXACT WORD MATCHING DISCOVERY INITIATED")
        logger.info("🎯 USING PRECISE KEYWORD DETECTION WITH WORD BOUNDARIES")
        logger.info("⚡ ENTITY RESOLUTION WITH EXACT MATCHING")
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🎯 PROJECT: {project_id}")
            
            try:
                await self._process_complete_project(client_manager, project_id)
                self.orchestration_stats['projects_processed'] += 1
                
            except Exception as e:
                logger.error(f"❌ PROJECT {project_id} FAILED: {e}")
                self.orchestration_stats['processing_errors'] += 1
        
        logger.info("🔗 RESOLVING ENTITY CLUSTERS...")
        resolved_entities = self.processor.resolve_all_entities()
        
        processing_time = (datetime.now() - self.orchestration_stats['processing_start_time']).total_seconds()
        
        logger.info("🎉 EXACT WORD MATCHING DISCOVERY COMPLETE")
        logger.info(f"📊 UNIQUE HOSTS DISCOVERED: {len(resolved_entities):,}")
        logger.info(f"📋 HOST TABLES PROCESSED: {self.processor.stats['host_tables_found']:,}")
        logger.info(f"📋 NON-HOST TABLES SKIPPED: {self.processor.stats['non_host_tables_skipped']:,}")
        logger.info(f"🔗 ENTITY CLUSTERS RESOLVED: {self.processor.stats['identity_clusters_created']:,}")
        logger.info(f"⏱️ PROCESSING TIME: {processing_time/60:.1f} minutes")
        
        return {
            'discovery_stats': {
                'total_assets': len(resolved_entities),
                'host_tables_processed': self.processor.stats['host_tables_found'],
                'non_host_tables_skipped': self.processor.stats['non_host_tables_skipped'],
                'entity_clusters_resolved': self.processor.stats['identity_clusters_created'],
                'processing_time_minutes': processing_time / 60,
                'exact_word_matching_enabled': True,
                'entity_resolution_enabled': True
            },
            'assets': resolved_entities,
            'processing_statistics': {
                'orchestration': self.orchestration_stats,
                'keyword_processing': self.processor.stats,
                'extraction': self.extractor.extraction_stats
            }
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
                        logger.error(f"❌ DATASET {dataset.dataset_id} FAILED: {e}")
                        self.orchestration_stats['processing_errors'] += 1
                        
            except Exception as e:
                logger.error(f"❌ PROJECT LISTING FAILED: {e}")
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
                    logger.error(f"❌ TABLE {table_ref.table_id} FAILED: {e}")
                    self.orchestration_stats['processing_errors'] += 1
            
        except Exception as e:
            logger.error(f"❌ DATASET PROCESSING FAILED: {e}")
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
            
            logger.info(f"🔥 {table_path}: Found {sum(len(cols) for cols in keyword_columns.values())} keyword columns")
            
            for keyword_type, matching_columns in keyword_columns.items():
                for column_name in matching_columns:
                    try:
                        extracted_count = await self.extractor.extract_all_column_values(
                            client, table_path, column_name, keyword_type
                        )
                        
                        if extracted_count > 0:
                            logger.info(f"✅ {column_name}: {extracted_count:,} values added to entity resolution")
                        
                    except Exception as e:
                        logger.error(f"❌ COLUMN {column_name} EXTRACTION FAILED: {e}")
                        self.orchestration_stats['processing_errors'] += 1
            
        except Exception as e:
            logger.error(f"❌ TABLE SCHEMA ACCESS FAILED: {e}")
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