import asyncio
import logging
import re
import statistics
from typing import Dict, List, Any, Optional
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
    
    def enhanced_classification(self, column_name: str, samples: List[str], 
                               context: Dict[str, Any] = None) -> Dict[str, Any]:
        
        if self._is_hostname_column(column_name, samples):
            return {
                'field_type': 'hostname',
                'confidence': 0.95,
                'metadata': {
                    'ai_confidence': 0.95,
                    'content_confidence': 0.95,
                    'visibility_score': 1.0,
                    'ao1_enhanced': True
                }
            }
        
        content_analysis = self._analyze_visibility_content(samples, 'unknown')
        final_confidence = content_analysis['confidence']
        
        metadata = {
            'ai_confidence': final_confidence,
            'content_confidence': content_analysis['confidence'],
            'visibility_score': self._calculate_visibility_score(samples, 'unknown'),
            'log_visibility_score': self._calculate_log_visibility(samples, 'unknown'),
            'cmdb_alignment_score': self._calculate_cmdb_alignment(samples, 'unknown'),
            'security_relevance': self._assess_security_relevance(samples, 'unknown'),
            'ao1_enhanced': True
        }
        
        return {
            'field_type': 'unknown',
            'confidence': final_confidence,
            'metadata': metadata
        }
    
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
    
    def _analyze_visibility_content(self, samples: List[str], field_type: str) -> Dict[str, Any]:
        if not samples:
            return {'confidence': 0.0, 'patterns': [], 'pattern_matches': {}}
        
        visibility_patterns = {
            'hostname': [r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$'],
            'ip_address': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
            'log_type': [r'firewall|ids|ips|proxy|dns|syslog|winlog'],
            'security': [r'edr|dlp|crowdstrike|security|auth']
        }
        
        patterns = visibility_patterns.get(field_type, [])
        matches = 0
        
        for pattern in patterns:
            matches += sum(1 for value in samples if re.search(pattern, str(value), re.IGNORECASE))
        
        pattern_score = matches / len(samples) if samples else 0.0
        format_consistency = self._assess_format_consistency(samples)
        data_quality = self._assess_data_quality(samples)
        
        combined_confidence = (pattern_score * 0.5) + (format_consistency * 0.3) + (data_quality * 0.2)
        
        return {
            'confidence': combined_confidence,
            'patterns': [field_type] if pattern_score > 0.3 else [],
            'pattern_matches': {field_type: pattern_score},
            'format_consistency': format_consistency,
            'data_quality': data_quality
        }
    
    def _calculate_visibility_score(self, samples: List[str], field_type: str) -> float:
        if field_type in ['hostname', 'ip_address', 'fqdn']:
            return 0.9
        elif field_type in ['log_type', 'network_log_types', 'endpoint_log_types']:
            return 0.8
        elif field_type in ['edr_coverage', 'dlp_coverage', 'security']:
            return 0.7
        return 0.5
    
    def _calculate_log_visibility(self, samples: List[str], field_type: str) -> float:
        if field_type in ['log_type', 'network_log_types', 'endpoint_log_types']:
            return 1.0
        
        log_indicators = ['log', 'event', 'syslog', 'audit', 'firewall']
        matches = sum(1 for value in samples 
                     for indicator in log_indicators 
                     if indicator in str(value).lower())
        
        return min(1.0, matches / max(len(samples), 1))
    
    def _calculate_cmdb_alignment(self, samples: List[str], field_type: str) -> float:
        cmdb_fields = ['hostname', 'ip_address', 'system_classification', 'infrastructure_type']
        
        if field_type in cmdb_fields:
            return 0.9
        
        return 0.3
    
    def _assess_security_relevance(self, samples: List[str], field_type: str) -> float:
        security_fields = ['edr_coverage', 'dlp_coverage', 'security', 'auth']
        
        if field_type in security_fields:
            return 1.0
        
        security_terms = ['security', 'threat', 'vulnerability', 'compliance']
        matches = sum(1 for value in samples 
                     for term in security_terms 
                     if term in str(value).lower())
        
        return min(1.0, matches / max(len(samples), 1))
    
    def _assess_format_consistency(self, samples: List[str]) -> float:
        if len(samples) < 2:
            return 1.0
        
        from collections import Counter
        
        patterns = []
        for value in samples:
            pattern = re.sub(r'[a-zA-Z]', 'A', str(value))
            pattern = re.sub(r'[0-9]', '9', pattern)
            patterns.append(pattern)
        
        pattern_counts = Counter(patterns)
        most_common_ratio = pattern_counts.most_common(1)[0][1] / len(patterns) if pattern_counts else 0
        
        return most_common_ratio
    
    def _assess_data_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        valid_samples = [s for s in samples if s and str(s).strip() and str(s).upper() not in ['NULL', 'N/A']]
        completeness = len(valid_samples) / len(samples)
        
        uniqueness = len(set(valid_samples)) / len(valid_samples) if valid_samples else 0
        
        return (completeness * 0.7) + (uniqueness * 0.3)

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
        
        self.comprehensive_hosts = {}
        self.processed_tables = set()
        self.host_enrichment_map = {
            'country': ['country', 'country_code', 'location_country', 'geo_country'],
            'region': ['region', 'global_region', 'geographic_region', 'area', 'zone'],
            'business_unit': ['business_unit', 'bu', 'department', 'org', 'organization'],
            'cio': ['cio', 'cio_org', 'cio_organization', 'chief_info_officer'],
            'datacenter': ['datacenter', 'data_center', 'dc', 'facility', 'site'],
            'application_class': ['application_class', 'app_class', 'criticality', 'tier'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'asset_type', 'device_type'],
            'system_classification': ['system_classification', 'sys_class', 'os_type', 'platform'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'internal_ip', 'private_ip'],
            'fqdn': ['fqdn', 'fully_qualified_domain_name', 'domain_name', 'dns_name']
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        
        logger.info("Starting comprehensive CMDB discovery across ALL tables")
        start_time = datetime.now()
        
        total_tables_processed = 0
        total_hosts_discovered = 0
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"Scanning ALL datasets in project: {project_id}")
            
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                for dataset in datasets:
                    dataset_ref = client.dataset(dataset.dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    
                    logger.info(f"Processing {len(tables)} tables in dataset {dataset.dataset_id}")
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        if table_path in self.processed_tables:
                            continue
                        
                        try:
                            hosts_found = await self._scan_table_for_hosts(client, table_path)
                            if hosts_found > 0:
                                total_hosts_discovered += hosts_found
                                logger.info(f"Found {hosts_found} hosts in {table_path}")
                            
                            total_tables_processed += 1
                            self.processed_tables.add(table_path)
                            
                            if total_tables_processed % 50 == 0:
                                logger.info(f"Progress: {total_tables_processed} tables, {len(self.comprehensive_hosts)} unique hosts")
                            
                        except Exception as e:
                            logger.warning(f"Failed to process table {table_path}: {e}")
        
        self._enrich_all_hosts(client_managers)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'discovery_stats': {
                'total_tables_processed': total_tables_processed,
                'unique_hosts_discovered': len(self.comprehensive_hosts),
                'total_host_instances': total_hosts_discovered,
                'processing_time': processing_time,
                'comprehensive_cmdb_mode': True
            },
            'assets': self.comprehensive_hosts,
            'performance_metrics': self._get_performance_summary()
        }
    
    async def _scan_table_for_hosts(self, client, table_path: str) -> int:
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return 0
            
            columns = [field.name for field in table.schema]
            
            sample_query = f"""
            SELECT {', '.join([f'`{col}`' for col in columns[:30]])}
            FROM `{table_path}`
            WHERE RAND() < 0.02
            LIMIT 200
            """
            
            job = client.query(sample_query)
            results = list(job.result())
            
            if not results:
                return 0
            
            hostname_column = self._identify_hostname_column(columns, results)
            
            if not hostname_column:
                return 0
            
            return await self._extract_all_hosts_from_table(client, table_path, hostname_column, columns)
            
        except Exception as e:
            logger.debug(f"Table scan failed for {table_path}: {e}")
            return 0
    
    def _identify_hostname_column(self, columns: List[str], sample_data: List) -> Optional[str]:
        for col_idx, column_name in enumerate(columns):
            if self._is_likely_hostname_column_name(column_name):
                sample_values = []
                for row in sample_data:
                    if col_idx < len(row) and row[col_idx] is not None:
                        sample_values.append(str(row[col_idx]))
                
                if sample_values and self._validate_hostname_content(sample_values):
                    return column_name
        
        for col_idx, column_name in enumerate(columns):
            sample_values = []
            for row in sample_data:
                if col_idx < len(row) and row[col_idx] is not None:
                    sample_values.append(str(row[col_idx]))
            
            if sample_values and self._validate_hostname_content(sample_values, strict=False):
                return column_name
        
        return None
    
    def _is_likely_hostname_column_name(self, column_name: str) -> bool:
        name_lower = column_name.lower()
        hostname_indicators = [
            'hostname', 'host', 'computername', 'computer_name', 'endpoint', 
            'device', 'machine', 'asset', 'system', 'server', 'workstation'
        ]
        return any(indicator in name_lower for indicator in hostname_indicators)
    
    def _validate_hostname_content(self, values: List[str], strict: bool = True) -> bool:
        if not values:
            return False
        
        valid_count = 0
        threshold = 0.6 if strict else 0.3
        
        for value in values[:20]:
            if self._looks_like_hostname(value):
                valid_count += 1
        
        return (valid_count / min(len(values), 20)) > threshold
    
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
    
    async def _extract_all_hosts_from_table(self, client, table_path: str, hostname_column: str, all_columns: List[str]) -> int:
        try:
            query = f"""
            SELECT *
            FROM `{table_path}`
            WHERE `{hostname_column}` IS NOT NULL
            AND `{hostname_column}` != ''
            AND `{hostname_column}` NOT IN ('NULL', 'N/A', 'UNKNOWN', 'NONE')
            LIMIT 500000
            """
            
            job = client.query(query)
            results = list(job.result())
            
            hosts_added = 0
            hostname_idx = all_columns.index(hostname_column)
            
            for row in results:
                if hostname_idx < len(row) and row[hostname_idx]:
                    hostname = str(row[hostname_idx]).strip().upper()
                    
                    if not hostname or len(hostname) < 2:
                        continue
                    
                    if hostname not in self.comprehensive_hosts:
                        self.comprehensive_hosts[hostname] = {
                            'hostname': hostname,
                            'source_tables': [],
                            'raw_data': {},
                            'country': '',
                            'region': '',
                            'business_unit': '',
                            'cio': '',
                            'datacenter': '',
                            'application_class': '',
                            'infrastructure_type': '',
                            'system_classification': '',
                            'ip_address': '',
                            'fqdn': '',
                            'first_seen': datetime.now(),
                            'sources_count': 0
                        }
                    
                    if table_path not in self.comprehensive_hosts[hostname]['source_tables']:
                        self.comprehensive_hosts[hostname]['source_tables'].append(table_path)
                        self.comprehensive_hosts[hostname]['sources_count'] += 1
                    
                    for col_idx, column_name in enumerate(all_columns):
                        if col_idx < len(row) and row[col_idx] is not None:
                            value = str(row[col_idx]).strip()
                            if value and value != hostname:
                                if table_path not in self.comprehensive_hosts[hostname]['raw_data']:
                                    self.comprehensive_hosts[hostname]['raw_data'][table_path] = {}
                                self.comprehensive_hosts[hostname]['raw_data'][table_path][column_name] = value
                    
                    hosts_added += 1
            
            return hosts_added
            
        except Exception as e:
            logger.error(f"Host extraction failed for {table_path}: {e}")
            return 0
    
    def _enrich_all_hosts(self, client_managers: Dict[str, Any]):
        logger.info(f"Enriching {len(self.comprehensive_hosts)} hosts with comprehensive data")
        
        enriched_count = 0
        
        for hostname, host_data in self.comprehensive_hosts.items():
            try:
                self._enrich_single_host(hostname, host_data)
                enriched_count += 1
                
                if enriched_count % 10000 == 0:
                    logger.info(f"Enriched {enriched_count} hosts")
                    
            except Exception as e:
                logger.debug(f"Enrichment failed for host {hostname}: {e}")
        
        logger.info(f"Completed enrichment for {enriched_count} hosts")
    
    def _enrich_single_host(self, hostname: str, host_data: Dict[str, Any]):
        all_raw_data = host_data.get('raw_data', {})
        
        for field_name, possible_columns in self.host_enrichment_map.items():
            if host_data.get(field_name):
                continue
            
            best_value = None
            best_confidence = 0
            
            for table_path, table_data in all_raw_data.items():
                for column_name, value in table_data.items():
                    column_lower = column_name.lower()
                    
                    for possible_col in possible_columns:
                        if possible_col in column_lower:
                            confidence = len(possible_col) / len(column_lower)
                            if confidence > best_confidence and value and len(str(value).strip()) > 0:
                                clean_value = str(value).strip()
                                if clean_value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '', '-']:
                                    best_value = clean_value
                                    best_confidence = confidence
            
            if best_value:
                host_data[field_name] = best_value
        
        self._set_coverage_flags(host_data)
        host_data['visibility_score'] = self._calculate_comprehensive_visibility_score(host_data)
    
    def _set_coverage_flags(self, host_data: Dict[str, Any]):
        source_tables = host_data.get('source_tables', [])
        
        host_data['cmdb_coverage'] = any('cmdb' in table.lower() or 'endpoint' in table.lower() for table in source_tables)
        host_data['splunk_coverage'] = any('splunk' in table.lower() or 'spl_' in table.lower() for table in source_tables)
        host_data['chronicle_coverage'] = any('chronicle' in table.lower() for table in source_tables)
        host_data['crowdstrike_coverage'] = any('crowdstrike' in table.lower() or 'endpointagent' in table.lower() for table in source_tables)
        host_data['edr_coverage'] = host_data['crowdstrike_coverage']
        
        for table_path, table_data in host_data.get('raw_data', {}).items():
            for column_name, value in table_data.items():
                column_lower = column_name.lower()
                value_lower = str(value).lower()
                
                if 'dlp' in column_lower or 'data_loss_prevention' in column_lower:
                    host_data['dlp_coverage'] = True
                if 'tanium' in column_lower or 'tanium' in value_lower:
                    host_data['tanium_coverage'] = True
    
    def _calculate_comprehensive_visibility_score(self, host_data: Dict[str, Any]) -> float:
        score = 0.0
        
        if host_data.get('cmdb_coverage'):
            score += 0.25
        if host_data.get('splunk_coverage'):
            score += 0.2
        if host_data.get('chronicle_coverage'):
            score += 0.15
        if host_data.get('edr_coverage'):
            score += 0.2
        if host_data.get('dlp_coverage'):
            score += 0.1
        
        field_completeness = sum([
            1 for field in ['country', 'region', 'business_unit', 'datacenter', 'ip_address']
            if host_data.get(field)
        ]) / 5.0
        score += field_completeness * 0.1
        
        return min(1.0, score)
    
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