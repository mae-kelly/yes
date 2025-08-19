# discovery/ao1.py

import asyncio
import logging
import re
import gc
import psutil
import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
            'start_time': datetime.now(),
            'memory_usage_mb': 0.0,
            'processing_rate_per_second': 0.0,
            'duplicate_hosts_merged': 0,
            'data_quality_issues': 0,
            'validation_failures': 0
        }
        
        self.field_mappings = self._initialize_field_mappings()
        self.hostname_patterns = self._initialize_hostname_patterns()
        self.enrichment_rules = self._initialize_enrichment_rules()
        self.data_validators = self._initialize_data_validators()
        self.performance_monitor = PerformanceMonitor()
        
        self.processing_lock = threading.RLock()
        self.batch_buffer = []
        self.batch_size = 1000
        self.commit_interval = 5.0
        self.last_commit_time = time.time()
    
    def _initialize_field_mappings(self) -> Dict[str, List[str]]:
        return {
            'hostname': [
                'hostname', 'host_name', 'computername', 'computer_name', 'device_name', 
                'endpoint_name', 'asset_name', 'machine_name', 'system_name', 'server_name',
                'workstation_name', 'node_name', 'instance_name', 'vm_name', 'container_name'
            ],
            'ip_address': [
                'ip_address', 'ip', 'ipv4', 'internal_ip', 'private_ip', 'host_ip', 
                'device_ip', 'endpoint_ip', 'server_ip', 'source_ip', 'dest_ip',
                'primary_ip', 'management_ip', 'cluster_ip', 'virtual_ip'
            ],
            'fqdn': [
                'fqdn', 'full_name', 'dns_name', 'qualified_name', 'domain_name',
                'canonical_name', 'fully_qualified_name', 'complete_name', 'dns_fqdn'
            ],
            'mac_address': [
                'mac_address', 'mac', 'physical_address', 'ethernet_address', 'hw_address',
                'hardware_address', 'network_address', 'nic_address', 'adapter_address'
            ],
            'infrastructure_type': [
                'infrastructure_type', 'hosting_type', 'deployment_type', 'platform_type',
                'environment_type', 'service_type', 'architecture_type', 'compute_type'
            ],
            'system_classification': [
                'system_classification', 'os_type', 'operating_system', 'platform', 'os_family',
                'system_type', 'os_version', 'platform_version', 'kernel_version'
            ],
            'business_unit': [
                'business_unit', 'bu', 'department', 'division', 'org_unit', 'cost_center',
                'organization', 'team', 'group', 'business_group', 'functional_area'
            ],
            'global_region': [
                'global_region', 'region', 'geo_region', 'location', 'geography', 'area',
                'continent', 'zone', 'territory', 'locale', 'geo_location'
            ],
            'country': [
                'country', 'country_code', 'nation', 'territory', 'state', 'province',
                'country_name', 'iso_country', 'geographic_country'
            ],
            'datacenter': [
                'datacenter', 'dc', 'site', 'facility', 'location_name', 'data_center',
                'server_farm', 'compute_center', 'hosting_facility', 'colocation'
            ],
            'zone': [
                'zone', 'availability_zone', 'az', 'cluster', 'rack', 'pod', 'subnet_zone',
                'network_zone', 'security_zone', 'dmz', 'vlan_zone'
            ],
            'cloud_provider': [
                'cloud_provider', 'cloud_vendor', 'provider', 'vendor', 'csp',
                'cloud_service_provider', 'hosting_provider', 'iaas_provider'
            ],
            'cloud_region': [
                'cloud_region', 'aws_region', 'azure_region', 'gcp_region', 'provider_region',
                'cloud_zone', 'availability_region', 'service_region'
            ],
            'environment': [
                'environment', 'env', 'tier', 'stage', 'lifecycle', 'deployment_env',
                'runtime_environment', 'execution_environment', 'service_tier'
            ],
            'application_class': [
                'application_class', 'app_class', 'service_class', 'workload_type',
                'application_type', 'service_type', 'workload_class', 'app_category'
            ],
            'criticality': [
                'criticality', 'priority', 'importance', 'tier', 'class', 'severity',
                'business_criticality', 'service_level', 'priority_level'
            ],
            'owner': [
                'owner', 'responsible_party', 'asset_owner', 'business_owner', 'system_owner',
                'technical_owner', 'service_owner', 'application_owner', 'data_owner'
            ],
            'technical_contact': [
                'technical_contact', 'tech_contact', 'admin', 'administrator', 'sys_admin',
                'system_admin', 'technical_lead', 'ops_contact', 'support_contact'
            ],
            'cio': [
                'cio', 'cio_org', 'cio_organization', 'it_organization', 'it_org',
                'information_technology', 'technology_organization', 'it_department'
            ],
            'manufacturer': [
                'manufacturer', 'vendor', 'make', 'brand', 'oem', 'hardware_vendor',
                'equipment_manufacturer', 'device_manufacturer'
            ],
            'model': [
                'model', 'product', 'type', 'variant', 'hardware_model', 'device_model',
                'equipment_model', 'product_model', 'system_model'
            ],
            'serial_number': [
                'serial_number', 'serial', 'sn', 'asset_tag', 'service_tag',
                'hardware_serial', 'device_serial', 'equipment_serial'
            ],
            'network_segment': [
                'network_segment', 'segment', 'vlan', 'subnet', 'network_zone',
                'ip_segment', 'network_range', 'subnet_range'
            ],
            'domain': [
                'domain', 'ad_domain', 'dns_domain', 'forest', 'active_directory',
                'windows_domain', 'kerberos_realm', 'authentication_domain'
            ],
            'patch_level': [
                'patch_level', 'patches', 'updates', 'security_patches', 'hotfixes',
                'software_updates', 'system_updates', 'os_patches'
            ],
            'antivirus_product': [
                'antivirus', 'av_product', 'endpoint_protection', 'security_software',
                'antimalware', 'epp', 'endpoint_security', 'virus_scanner'
            ]
        }
    
    def _initialize_hostname_patterns(self) -> List[re.Pattern]:
        patterns = [
            re.compile(r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$', re.IGNORECASE),
            re.compile(r'^[a-zA-Z0-9]{1,63}$', re.IGNORECASE),
            re.compile(r'^[a-zA-Z]{2,6}[0-9]{1,8}$', re.IGNORECASE),
            re.compile(r'^[a-zA-Z]+\-[a-zA-Z0-9]+\-[a-zA-Z0-9]+$', re.IGNORECASE),
            re.compile(r'^(srv|web|app|db|sql|dc|vm|host|pc|ws|node|server)\-?[a-zA-Z0-9]+', re.IGNORECASE),
            re.compile(r'^[a-zA-Z0-9]+\.(local|corp|internal|lan|domain)$', re.IGNORECASE),
            re.compile(r'^[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}$', re.IGNORECASE),
            re.compile(r'^(prod|dev|test|stage|qa|uat)\-[a-zA-Z0-9\-]+$', re.IGNORECASE)
        ]
        return patterns
    
    def _initialize_enrichment_rules(self) -> Dict[str, Any]:
        return {
            'cloud_detection': {
                'aws': ['aws', 'amazon', 'ec2', 'lambda', 's3', 'rds', 'elb', 'eks'],
                'azure': ['azure', 'microsoft', 'vm', 'webapp', 'aks', 'sql'],
                'gcp': ['gcp', 'google', 'compute', 'cloud', 'gke', 'bigquery'],
                'kubernetes': ['k8s', 'kube', 'pod', 'node', 'container', 'docker'],
                'openstack': ['openstack', 'nova', 'neutron', 'cinder'],
                'vmware': ['vmware', 'vsphere', 'vcenter', 'esx', 'vsan']
            },
            'environment_detection': {
                'production': ['prod', 'production', 'live', 'prd', 'p1', 'master'],
                'development': ['dev', 'development', 'devel', 'd1', 'develop'],
                'test': ['test', 'testing', 'tst', 'qa', 'quality', 't1'],
                'staging': ['stage', 'staging', 'stg', 'uat', 'pre', 's1'],
                'sandbox': ['sandbox', 'sbx', 'demo', 'poc', 'trial'],
                'backup': ['backup', 'bck', 'dr', 'disaster', 'recovery']
            },
            'infrastructure_detection': {
                'on_premise': ['onprem', 'datacenter', 'physical', 'bare', 'dedicated'],
                'cloud': ['cloud', 'saas', 'paas', 'iaas', 'hosted', 'managed'],
                'hybrid': ['hybrid', 'mixed', 'multi', 'federation'],
                'virtual': ['vm', 'virtual', 'hyperv', 'vmware', 'kvm', 'xen'],
                'container': ['container', 'docker', 'pod', 'kubernetes', 'openshift'],
                'serverless': ['serverless', 'lambda', 'function', 'faas']
            },
            'service_type_detection': {
                'web_server': ['web', 'http', 'apache', 'nginx', 'iis', 'tomcat'],
                'database': ['db', 'sql', 'mysql', 'postgres', 'oracle', 'mongo'],
                'application': ['app', 'application', 'service', 'api', 'microservice'],
                'storage': ['storage', 'nas', 'san', 'file', 'block', 'object'],
                'network': ['network', 'router', 'switch', 'firewall', 'proxy', 'lb'],
                'security': ['security', 'ids', 'ips', 'waf', 'siem', 'antivirus']
            }
        }
    
    def _initialize_data_validators(self) -> Dict[str, callable]:
        return {
            'hostname': self._validate_hostname,
            'ip_address': self._validate_ip_address,
            'fqdn': self._validate_fqdn,
            'mac_address': self._validate_mac_address,
            'email': self._validate_email,
            'url': self._validate_url
        }
    
    def _validate_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (1 <= len(value) <= 253):
            return False
        
        if value.upper() in ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NIL', 'LOCALHOST', '127.0.0.1', 'BLANK', 'EMPTY']:
            return False
        
        return any(pattern.match(value) for pattern in self.hostname_patterns)
    
    def _validate_ip_address(self, value: str) -> bool:
        try:
            import ipaddress
            ipaddress.ip_address(value)
            return True
        except:
            return False
    
    def _validate_fqdn(self, value: str) -> bool:
        if not isinstance(value, str) or not (3 <= len(value) <= 253):
            return False
        
        fqdn_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$', re.IGNORECASE)
        return bool(fqdn_pattern.match(value))
    
    def _validate_mac_address(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        mac_patterns = [
            re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'),
            re.compile(r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$')
        ]
        
        return any(pattern.match(value) for pattern in mac_patterns)
    
    def _validate_email(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(email_pattern.match(value))
    
    def _validate_url(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        url_pattern = re.compile(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE)
        return bool(url_pattern.match(value))
    
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname:
            return ""
        
        hostname = str(hostname).strip()
        
        if '.' in hostname and hostname.count('.') <= 4:
            if self._validate_fqdn(hostname):
                return hostname.lower()
            else:
                hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Za-z0-9\-_]', '', hostname)
        
        return hostname.upper() if len(hostname) <= 15 else hostname.lower()
    
    def is_valid_hostname(self, hostname: str) -> bool:
        if not hostname or len(hostname) < 2 or len(hostname) > 253:
            return False
        
        return self._validate_hostname(hostname)
    
    def extract_hostname_candidates(self, row_data: Dict[str, Any]) -> List[Tuple[str, str, float]]:
        candidates = []
        
        for column_name, value in row_data.items():
            if not value:
                continue
            
            column_lower = column_name.lower()
            value_str = str(value).strip()
            
            confidence_score = 0.0
            
            for pattern in self.field_mappings['hostname']:
                if pattern in column_lower:
                    confidence_score = max(confidence_score, len(pattern) / len(column_lower))
            
            if confidence_score > 0.3 and self.is_valid_hostname(value_str):
                candidates.append((value_str, column_name, confidence_score))
        
        return sorted(candidates, key=lambda x: x[2], reverse=True)
    
    def intelligent_field_mapping(self, column_name: str) -> Optional[str]:
        column_lower = column_name.lower()
        
        best_match = None
        best_score = 0.0
        
        for field_type, patterns in self.field_mappings.items():
            for pattern in patterns:
                if pattern in column_lower:
                    score = len(pattern) / len(column_lower)
                    if score > best_score:
                        best_score = score
                        best_match = field_type
        
        if best_score > 0.3:
            return best_match
        
        if any(term in column_lower for term in ['log', 'event', 'time', 'date', 'timestamp']):
            return 'log_data'
        
        if any(term in column_lower for term in ['id', 'key', 'index', 'sequence', 'number']):
            return 'identifier'
        
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
                    elif category == 'service_type_detection':
                        enriched['service_type'] = [value]
        
        for column_name, values in all_data.items():
            if not values:
                continue
            
            column_lower = column_name.lower()
            field_type = self.intelligent_field_mapping(column_name)
            
            if field_type and field_type in self.field_mappings:
                enriched[field_type] = values if isinstance(values, list) else [values]
            
            if 'region' in column_lower and field_type != 'global_region':
                enriched['global_region'] = values if isinstance(values, list) else [values]
            elif 'country' in column_lower and field_type != 'country':
                enriched['country'] = values if isinstance(values, list) else [values]
        
        geo_enrichment = self._enrich_geographic_data(hostname, all_data)
        enriched.update(geo_enrichment)
        
        business_enrichment = self._enrich_business_context(hostname, all_data)
        enriched.update(business_enrichment)
        
        return enriched
    
    def _enrich_geographic_data(self, hostname: str, all_data: Dict[str, Any]) -> Dict[str, Any]:
        geo_data = {}
        
        geographic_indicators = {
            'us': 'United States', 'usa': 'United States', 'america': 'United States',
            'uk': 'United Kingdom', 'gb': 'United Kingdom', 'britain': 'United Kingdom',
            'ca': 'Canada', 'canada': 'Canada',
            'de': 'Germany', 'germany': 'Germany', 'deutschland': 'Germany',
            'fr': 'France', 'france': 'France',
            'jp': 'Japan', 'japan': 'Japan',
            'au': 'Australia', 'australia': 'Australia',
            'in': 'India', 'india': 'India',
            'cn': 'China', 'china': 'China',
            'br': 'Brazil', 'brazil': 'Brazil'
        }
        
        hostname_lower = hostname.lower()
        for indicator, country in geographic_indicators.items():
            if indicator in hostname_lower:
                geo_data['country'] = [country]
                break
        
        city_indicators = {
            'nyc': 'New York', 'ny': 'New York', 'newyork': 'New York',
            'la': 'Los Angeles', 'losangeles': 'Los Angeles',
            'sf': 'San Francisco', 'sanfrancisco': 'San Francisco',
            'chi': 'Chicago', 'chicago': 'Chicago',
            'lon': 'London', 'london': 'London',
            'par': 'Paris', 'paris': 'Paris',
            'tok': 'Tokyo', 'tokyo': 'Tokyo',
            'syd': 'Sydney', 'sydney': 'Sydney'
        }
        
        for indicator, city in city_indicators.items():
            if indicator in hostname_lower:
                geo_data['city'] = [city]
                break
        
        return geo_data
    
    def _enrich_business_context(self, hostname: str, all_data: Dict[str, Any]) -> Dict[str, Any]:
        business_data = {}
        
        business_indicators = {
            'fin': 'Finance', 'finance': 'Finance', 'accounting': 'Finance',
            'hr': 'Human Resources', 'people': 'Human Resources', 'talent': 'Human Resources',
            'it': 'Information Technology', 'tech': 'Information Technology',
            'sales': 'Sales', 'revenue': 'Sales', 'commercial': 'Sales',
            'marketing': 'Marketing', 'brand': 'Marketing', 'promo': 'Marketing',
            'ops': 'Operations', 'operations': 'Operations', 'support': 'Operations',
            'legal': 'Legal', 'compliance': 'Legal', 'risk': 'Legal',
            'eng': 'Engineering', 'engineering': 'Engineering', 'dev': 'Engineering'
        }
        
        hostname_lower = hostname.lower()
        for indicator, department in business_indicators.items():
            if indicator in hostname_lower:
                business_data['business_unit'] = [department]
                break
        
        criticality_indicators = {
            'prod': 'high', 'production': 'high', 'critical': 'critical',
            'mission': 'critical', 'essential': 'high', 'important': 'medium',
            'dev': 'low', 'test': 'low', 'sandbox': 'low', 'demo': 'low'
        }
        
        for indicator, level in criticality_indicators.items():
            if indicator in hostname_lower:
                business_data['criticality'] = [level]
                break
        
        return business_data
    
    def set_coverage_flags(self, host_data: Dict[str, Any], source_table: str) -> Dict[str, bool]:
        table_lower = source_table.lower()
        coverage_flags = host_data.get('coverage_flags', {})
        
        coverage_mappings = {
            'edr_coverage': ['edr', 'endpoint_detection', 'endpoint_response'],
            'in_chronicle': ['chronicle', 'backstory', 'google_security', 'chronicle_security'],
            'in_crowdstrike': ['crowdstrike', 'cs_', 'falcon', 'crwd', 'crowdstrike_falcon'],
            'in_original_cmdb': ['cmdb', 'v_dim_endpoint', 'servicenow', 'remedy', 'itil'],
            'in_splunk': ['splunk', 'spl_', 'universal_forwarder', 'splunk_enterprise'],
            'in_tanium': ['tanium', 'tan_', 'endpoint_platform', 'tanium_core'],
            'in_dlp': ['dlp', 'data_loss', 'symantec_dlp', 'forcepoint', 'data_prevention'],
            'antivirus_coverage': ['antivirus', 'av_', 'mcafee', 'symantec', 'trend', 'kaspersky'],
            'backup_coverage': ['backup', 'veeam', 'commvault', 'netbackup', 'backup_exec'],
            'monitoring_coverage': ['monitor', 'nagios', 'zabbix', 'scom', 'datadog', 'newrelic'],
            'patch_management': ['wsus', 'sccm', 'patch', 'update', 'vulnerability'],
            'asset_management': ['asset', 'inventory', 'discovery', 'lansweeper', 'kace']
        }
        
        for flag, keywords in coverage_mappings.items():
            if any(keyword in table_lower for keyword in keywords):
                coverage_flags[flag] = True
                self.processing_stats['coverage_flags_set'] += 1
        
        return coverage_flags
    
    def process_single_host(self, hostname: str, row_data: Dict[str, Any], source_table: str):
        with self.processing_lock:
            try:
                normalized_hostname = self.normalize_hostname(hostname)
                
                if not normalized_hostname or not self.is_valid_hostname(normalized_hostname):
                    self.processing_stats['validation_failures'] += 1
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
                        'validation_status': {},
                        'confidence_scores': {},
                        'data_lineage': [],
                        'first_seen': datetime.now().isoformat(),
                        'last_updated': datetime.now().isoformat(),
                        'source_count': 0,
                        'total_rows': 0,
                        'processing_history': []
                    }
                    self.processing_stats['hosts_discovered'] += 1
                    logger.debug(f"New host discovered: {normalized_hostname}")
                else:
                    self.processing_stats['duplicate_hosts_merged'] += 1
                
                host = self.cmdb[normalized_hostname]
                
                new_attributes_count = 0
                data_quality_issues = 0
                
                for column_name, value in row_data.items():
                    if value is None or str(value).strip() == '':
                        continue
                    
                    clean_value = str(value).strip()
                    mapped_field = self.intelligent_field_mapping(column_name)
                    
                    if not mapped_field:
                        mapped_field = 'unmapped_data'
                        data_quality_issues += 1
                    
                    if mapped_field not in host['all_data']:
                        host['all_data'][mapped_field] = set()
                    
                    if clean_value not in host['all_data'][mapped_field]:
                        if self._validate_data_value(mapped_field, clean_value):
                            host['all_data'][mapped_field].add(clean_value)
                            new_attributes_count += 1
                            self.processing_stats['attributes_enriched'] += 1
                        else:
                            data_quality_issues += 1
                            self.processing_stats['data_quality_issues'] += 1
                
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
                host['confidence_scores'] = self.calculate_confidence_scores(host)
                host['validation_status'] = self.validate_host_data(host)
                
                host['data_lineage'].append({
                    'source_table': source_table,
                    'timestamp': datetime.now().isoformat(),
                    'attributes_added': new_attributes_count,
                    'data_quality_score': 1.0 - (data_quality_issues / max(len(row_data), 1))
                })
                
                host['processing_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'processed_row',
                    'source': source_table,
                    'new_attributes': new_attributes_count,
                    'quality_issues': data_quality_issues
                })
                
                if self.database_manager:
                    self.batch_buffer.append((normalized_hostname, host))
                    if len(self.batch_buffer) >= self.batch_size or (time.time() - self.last_commit_time) > self.commit_interval:
                        self._flush_batch_to_database()
                
                self.processing_stats['cells_analyzed'] += len(row_data)
                
                if new_attributes_count > 0:
                    logger.debug(f"Host {normalized_hostname} enriched with {new_attributes_count} new attributes")
            
            except Exception as e:
                logger.error(f"Error processing host {hostname}: {e}")
                self.processing_stats['validation_failures'] += 1
    
    def _validate_data_value(self, field_type: str, value: str) -> bool:
        if not value or len(value) > 1000:
            return False
        
        if field_type in self.data_validators:
            return self.data_validators[field_type](value)
        
        return True
    
    def _flush_batch_to_database(self):
        if not self.batch_buffer:
            return
        
        try:
            for hostname, host_data in self.batch_buffer:
                success = self.store_host_to_database(hostname, host_data)
                if success:
                    self.stored_count += 1
            
            self.batch_buffer.clear()
            self.last_commit_time = time.time()
            
        except Exception as e:
            logger.error(f"Batch database flush failed: {e}")
    
    def calculate_quality_metrics(self, host_data: Dict[str, Any]) -> Dict[str, float]:
        all_data = host_data.get('all_data', {})
        coverage_flags = host_data.get('coverage_flags', {})
        
        total_possible_fields = len(self.field_mappings)
        filled_fields = len([v for v in all_data.values() if v])
        data_completeness = filled_fields / total_possible_fields
        
        total_coverage_flags = len(coverage_flags)
        true_coverage_flags = sum(1 for v in coverage_flags.values() if v)
        coverage_score = true_coverage_flags / max(total_coverage_flags, 1)
        
        source_reliability = min(1.0, host_data.get('source_count', 0) / 5.0)
        
        data_consistency = self._calculate_data_consistency(all_data)
        data_freshness = self._calculate_data_freshness(host_data)
        
        overall_quality = (
            data_completeness * 0.25 +
            coverage_score * 0.25 +
            source_reliability * 0.20 +
            data_consistency * 0.15 +
            data_freshness * 0.15
        )
        
        return {
            'data_completeness': data_completeness,
            'coverage_score': coverage_score,
            'source_reliability': source_reliability,
            'data_consistency': data_consistency,
            'data_freshness': data_freshness,
            'overall_quality': overall_quality
        }
    
    def _calculate_data_consistency(self, all_data: Dict[str, Any]) -> float:
        consistency_score = 1.0
        
        for field_type, values in all_data.items():
            if len(values) > 1:
                unique_values = len(set(str(v).lower() for v in values))
                if unique_values > 1:
                    consistency_score -= 0.1
        
        return max(0.0, consistency_score)
    
    def _calculate_data_freshness(self, host_data: Dict[str, Any]) -> float:
        last_updated = host_data.get('last_updated')
        if not last_updated:
            return 0.5
        
        try:
            last_update_time = datetime.fromisoformat(last_updated)
            time_diff = datetime.now() - last_update_time
            hours_since_update = time_diff.total_seconds() / 3600
            
            if hours_since_update < 1:
                return 1.0
            elif hours_since_update < 24:
                return 0.8
            elif hours_since_update < 168:
                return 0.6
            elif hours_since_update < 720:
                return 0.4
            else:
                return 0.2
        
        except:
            return 0.5
    
    def calculate_confidence_scores(self, host_data: Dict[str, Any]) -> Dict[str, float]:
        confidence_scores = {}
        
        source_count = host_data.get('source_count', 0)
        source_confidence = min(1.0, source_count / 3.0)
        
        quality_metrics = host_data.get('quality_metrics', {})
        quality_confidence = quality_metrics.get('overall_quality', 0.0)
        
        data_volume = sum(len(values) for values in host_data.get('all_data', {}).values())
        volume_confidence = min(1.0, data_volume / 20.0)
        
        validation_status = host_data.get('validation_status', {})
        validation_confidence = sum(validation_status.values()) / max(len(validation_status), 1)
        
        overall_confidence = (
            source_confidence * 0.3 +
            quality_confidence * 0.3 +
            volume_confidence * 0.2 +
            validation_confidence * 0.2
        )
        
        confidence_scores = {
            'source_confidence': source_confidence,
            'quality_confidence': quality_confidence,
            'volume_confidence': volume_confidence,
            'validation_confidence': validation_confidence,
            'overall_confidence': overall_confidence
        }
        
        return confidence_scores
    
    def validate_host_data(self, host_data: Dict[str, Any]) -> Dict[str, bool]:
        validation_results = {}
        all_data = host_data.get('all_data', {})
        
        for field_type, values in all_data.items():
            if field_type in self.data_validators:
                validator = self.data_validators[field_type]
                valid_count = sum(1 for value in values if validator(str(value)))
                validation_results[field_type] = valid_count / len(values) > 0.8
            else:
                validation_results[field_type] = True
        
        return validation_results
    
    def store_host_to_database(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        try:
            serialized_data = self.prepare_for_database(host_data)
            
            if hasattr(self.database_manager, 'store_single_host_immediately'):
                success = self.database_manager.store_single_host_immediately(hostname, serialized_data)
            else:
                success = False
            
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
        if self.batch_buffer:
            self._flush_batch_to_database()
        
        processing_time = (datetime.now() - self.processing_stats['start_time']).total_seconds()
        
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
        self.processing_stats['memory_usage_mb'] = memory_usage
        
        if processing_time > 0:
            self.processing_stats['processing_rate_per_second'] = len(self.cmdb) / processing_time
        
        performance_summary = self.performance_monitor.get_summary()
        
        return {
            'assets': {hostname: self.prepare_for_database(data) for hostname, data in self.cmdb.items()},
            'discovery_stats': {
                'total_unique_hosts': len(self.cmdb),
                'processing_time_seconds': processing_time,
                'hosts_per_second': self.processing_stats['processing_rate_per_second'],
                'tables_processed': self.processing_stats['tables_processed'],
                'rows_processed': self.processing_stats['rows_processed'],
                'cells_analyzed': self.processing_stats['cells_analyzed'],
                'attributes_enriched': self.processing_stats['attributes_enriched'],
                'coverage_flags_set': self.processing_stats['coverage_flags_set'],
                'enrichment_operations': self.processing_stats['enrichment_operations'],
                'duplicate_hosts_merged': self.processing_stats['duplicate_hosts_merged'],
                'data_quality_issues': self.processing_stats['data_quality_issues'],
                'validation_failures': self.processing_stats['validation_failures'],
                'database_storage_count': self.stored_count,
                'memory_usage_mb': memory_usage
            },
            'performance_metrics': performance_summary,
            'quality_analysis': self._generate_quality_analysis(),
            'coverage_analysis': self._generate_coverage_analysis()
        }
    
    def _generate_quality_analysis(self) -> Dict[str, Any]:
        if not self.cmdb:
            return {}
        
        quality_scores = []
        completeness_scores = []
        consistency_scores = []
        
        for host_data in self.cmdb.values():
            quality_metrics = host_data.get('quality_metrics', {})
            quality_scores.append(quality_metrics.get('overall_quality', 0.0))
            completeness_scores.append(quality_metrics.get('data_completeness', 0.0))
            consistency_scores.append(quality_metrics.get('data_consistency', 0.0))
        
        return {
            'average_quality_score': sum(quality_scores) / len(quality_scores),
            'average_completeness': sum(completeness_scores) / len(completeness_scores),
            'average_consistency': sum(consistency_scores) / len(consistency_scores),
            'high_quality_assets': len([s for s in quality_scores if s > 0.8]),
            'medium_quality_assets': len([s for s in quality_scores if 0.5 <= s <= 0.8]),
            'low_quality_assets': len([s for s in quality_scores if s < 0.5])
        }
    
    def _generate_coverage_analysis(self) -> Dict[str, Any]:
        if not self.cmdb:
            return {}
        
        coverage_summary = defaultdict(int)
        total_hosts = len(self.cmdb)
        
        for host_data in self.cmdb.values():
            coverage_flags = host_data.get('coverage_flags', {})
            for flag, status in coverage_flags.items():
                if status:
                    coverage_summary[flag] += 1
        
        coverage_percentages = {
            flag: (count / total_hosts * 100) for flag, count in coverage_summary.items()
        }
        
        return {
            'coverage_counts': dict(coverage_summary),
            'coverage_percentages': coverage_percentages,
            'total_hosts': total_hosts,
            'fully_covered_hosts': len([
                host for host in self.cmdb.values()
                if sum(host.get('coverage_flags', {}).values()) >= 3
            ]),
            'uncovered_hosts': len([
                host for host in self.cmdb.values()
                if sum(host.get('coverage_flags', {}).values()) == 0
            ])
        }

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.operation_times = defaultdict(list)
        self.memory_samples = []
        self.cpu_samples = []
        self.processing_rates = []
        
    def record_operation(self, operation: str, duration: float):
        self.operation_times[operation].append(duration)
    
    def sample_system_metrics(self):
        try:
            process = psutil.Process()
            self.memory_samples.append(process.memory_info().rss / 1024 / 1024)
            self.cpu_samples.append(process.cpu_percent())
        except:
            pass
    
    def record_processing_rate(self, items_processed: int, time_elapsed: float):
        if time_elapsed > 0:
            rate = items_processed / time_elapsed
            self.processing_rates.append(rate)
    
    def get_summary(self) -> Dict[str, Any]:
        total_time = time.time() - self.start_time
        
        operation_stats = {}
        for operation, times in self.operation_times.items():
            operation_stats[operation] = {
                'count': len(times),
                'total_time': sum(times),
                'average_time': sum(times) / len(times) if times else 0,
                'min_time': min(times) if times else 0,
                'max_time': max(times) if times else 0
            }
        
        return {
            'total_runtime_seconds': total_time,
            'operation_statistics': operation_stats,
            'memory_usage': {
                'current_mb': self.memory_samples[-1] if self.memory_samples else 0,
                'peak_mb': max(self.memory_samples) if self.memory_samples else 0,
                'average_mb': sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
            },
            'cpu_usage': {
                'current_percent': self.cpu_samples[-1] if self.cpu_samples else 0,
                'peak_percent': max(self.cpu_samples) if self.cpu_samples else 0,
                'average_percent': sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
            },
            'processing_rates': {
                'current_items_per_second': self.processing_rates[-1] if self.processing_rates else 0,
                'peak_items_per_second': max(self.processing_rates) if self.processing_rates else 0,
                'average_items_per_second': sum(self.processing_rates) / len(self.processing_rates) if self.processing_rates else 0
            }
        }

class AdvancedTableProcessor:
    def __init__(self, cmdb_builder: RealtimeCMDBBuilder):
        self.cmdb_builder = cmdb_builder
        self.processed_tables = set()
        self.table_cache = {}
        self.processing_stats = {
            'tables_attempted': 0,
            'tables_successful': 0,
            'tables_skipped': 0,
            'rows_processed': 0,
            'hosts_found': 0,
            'processing_errors': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'batch_operations': 0,
            'optimization_count': 0
        }
        
        self.table_metadata = {}
        self.column_analysis_cache = {}
        self.optimization_strategies = self._initialize_optimization_strategies()
    
    def _initialize_optimization_strategies(self) -> Dict[str, callable]:
        return {
            'small_table': self._process_small_table,
            'medium_table': self._process_medium_table,
            'large_table': self._process_large_table,
            'huge_table': self._process_huge_table
        }
    
    def detect_hostname_columns(self, schema_fields: List[Any]) -> List[Dict[str, Any]]:
        hostname_columns = []
        
        hostname_indicators = [
            'hostname', 'host_name', 'computername', 'computer_name', 'device_name',
            'endpoint_name', 'asset_name', 'machine_name', 'system_name', 'server_name',
            'workstation_name', 'node_name', 'instance_name'
        ]
        
        for field in schema_fields:
            field_name = field.name.lower()
            confidence_score = 0.0
            
            for indicator in hostname_indicators:
                if indicator in field_name:
                    score = len(indicator) / len(field_name)
                    confidence_score = max(confidence_score, score)
            
            if confidence_score > 0.3:
                hostname_columns.append({
                    'name': field.name,
                    'confidence': confidence_score,
                    'type': str(field.field_type) if hasattr(field, 'field_type') else 'STRING',
                    'nullable': getattr(field, 'is_nullable', True)
                })
        
        return sorted(hostname_columns, key=lambda x: x['confidence'], reverse=True)
    
    async def process_table_comprehensively(self, client, table_path: str) -> Dict[str, Any]:
        if table_path in self.processed_tables:
            self.processing_stats['tables_skipped'] += 1
            return {'skipped': True, 'reason': 'already_processed'}
        
        self.processing_stats['tables_attempted'] += 1
        
        try:
            table_info = self._analyze_table_metadata(client, table_path)
            if not table_info['processable']:
                self.processing_stats['tables_skipped'] += 1
                return {'skipped': True, 'reason': table_info['skip_reason']}
            
            optimization_strategy = self._select_optimization_strategy(table_info)
            processor = self.optimization_strategies[optimization_strategy]
            
            result = await processor(client, table_path, table_info)
            
            if result.get('success'):
                self.processed_tables.add(table_path)
                self.processing_stats['tables_successful'] += 1
                self.processing_stats['optimization_count'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Table processing failed: {table_path} - {e}")
            self.processing_stats['processing_errors'] += 1
            return {'table_path': table_path, 'success': False, 'error': str(e)}
    
    def _analyze_table_metadata(self, client, table_path: str) -> Dict[str, Any]:
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return {'processable': False, 'skip_reason': 'empty_table'}
            
            hostname_columns = self.detect_hostname_columns(table.schema)
            if not hostname_columns:
                return {'processable': False, 'skip_reason': 'no_hostname_columns'}
            
            table_info = {
                'processable': True,
                'table_path': table_path,
                'row_count': table.num_rows,
                'column_count': len(table.schema),
                'hostname_columns': hostname_columns,
                'primary_hostname_column': hostname_columns[0]['name'],
                'table_size_category': self._categorize_table_size(table.num_rows),
                'estimated_processing_time': self._estimate_processing_time(table.num_rows),
                'memory_requirements': self._estimate_memory_requirements(table.num_rows, len(table.schema))
            }
            
            self.table_metadata[table_path] = table_info
            return table_info
            
        except Exception as e:
            logger.error(f"Table metadata analysis failed for {table_path}: {e}")
            return {'processable': False, 'skip_reason': f'metadata_error: {str(e)}'}
    
    def _categorize_table_size(self, row_count: int) -> str:
        if row_count < 1000:
            return 'small_table'
        elif row_count < 50000:
            return 'medium_table'
        elif row_count < 1000000:
            return 'large_table'
        else:
            return 'huge_table'
    
    def _estimate_processing_time(self, row_count: int) -> float:
        base_rate = 1000
        return row_count / base_rate
    
    def _estimate_memory_requirements(self, row_count: int, column_count: int) -> float:
        estimated_cell_size = 50
        total_cells = row_count * column_count
        return (total_cells * estimated_cell_size) / (1024 * 1024)
    
    def _select_optimization_strategy(self, table_info: Dict[str, Any]) -> str:
        return table_info['table_size_category']
    
    async def _process_small_table(self, client, table_path: str, table_info: Dict[str, Any]) -> Dict[str, Any]:
        try:
            primary_hostname_column = table_info['primary_hostname_column']
            
            query = f"""
            SELECT *
            FROM `{table_path}`
            WHERE `{primary_hostname_column}` IS NOT NULL
            AND TRIM(`{primary_hostname_column}`) != ''
            """
            
            job = client.query(query)
            results = list(job.result())
            
            table = client.get_table(table_path)
            columns = [field.name for field in table.schema]
            
            hosts_found = 0
            for row in results:
                row_data = dict(zip(columns, row))
                hostname_value = row_data.get(primary_hostname_column)
                
                if hostname_value and str(hostname_value).strip():
                    self.cmdb_builder.process_single_host(
                        str(hostname_value).strip(), row_data, table_path
                    )
                    hosts_found += 1
            
            self.processing_stats['rows_processed'] += len(results)
            self.processing_stats['hosts_found'] += hosts_found
            
            return {
                'table_path': table_path,
                'strategy': 'small_table',
                'rows_processed': len(results),
                'hosts_found': hosts_found,
                'hostname_column': primary_hostname_column,
                'total_columns': len(columns),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Small table processing failed for {table_path}: {e}")
            return {'table_path': table_path, 'success': False, 'error': str(e)}
    
    async def _process_medium_table(self, client, table_path: str, table_info: Dict[str, Any]) -> Dict[str, Any]:
        try:
            primary_hostname_column = table_info['primary_hostname_column']
            batch_size = 5000
            offset = 0
            total_processed = 0
            hosts_found = 0
            
            table = client.get_table(table_path)
            columns = [field.name for field in table.schema]
            
            while True:
                query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{primary_hostname_column}` IS NOT NULL
                AND TRIM(`{primary_hostname_column}`) != ''
                LIMIT {batch_size} OFFSET {offset}
                """
                
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
                
                self.processing_stats['batch_operations'] += 1
                
                if len(results) < batch_size:
                    break
                
                if total_processed % 10000 == 0:
                    logger.info(f"Medium table progress: {total_processed:,} rows, {hosts_found:,} hosts")
                    gc.collect()
            
            self.processing_stats['rows_processed'] += total_processed
            self.processing_stats['hosts_found'] += hosts_found
            
            return {
                'table_path': table_path,
                'strategy': 'medium_table',
                'rows_processed': total_processed,
                'hosts_found': hosts_found,
                'hostname_column': primary_hostname_column,
                'batch_operations': offset // batch_size + 1,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Medium table processing failed for {table_path}: {e}")
            return {'table_path': table_path, 'success': False, 'error': str(e)}
    
    async def _process_large_table(self, client, table_path: str, table_info: Dict[str, Any]) -> Dict[str, Any]:
        try:
            primary_hostname_column = table_info['primary_hostname_column']
            batch_size = 10000
            offset = 0
            total_processed = 0
            hosts_found = 0
            
            table = client.get_table(table_path)
            columns = [field.name for field in table.schema]
            
            essential_columns = [col for col in columns if self._is_essential_column(col)]
            if len(essential_columns) < len(columns):
                columns = essential_columns
                logger.info(f"Large table optimization: using {len(essential_columns)} essential columns")
            
            while True:
                column_list = ', '.join([f'`{col}`' for col in columns])
                query = f"""
                SELECT {column_list}
                FROM `{table_path}`
                WHERE `{primary_hostname_column}` IS NOT NULL
                AND TRIM(`{primary_hostname_column}`) != ''
                LIMIT {batch_size} OFFSET {offset}
                """
                
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
                
                self.processing_stats['batch_operations'] += 1
                
                if len(results) < batch_size:
                    break
                
                if total_processed % 50000 == 0:
                    logger.info(f"Large table progress: {total_processed:,} rows, {hosts_found:,} hosts")
                    gc.collect()
            
            self.processing_stats['rows_processed'] += total_processed
            self.processing_stats['hosts_found'] += hosts_found
            
            return {
                'table_path': table_path,
                'strategy': 'large_table',
                'rows_processed': total_processed,
                'hosts_found': hosts_found,
                'hostname_column': primary_hostname_column,
                'columns_used': len(columns),
                'optimization_applied': len(essential_columns) < len(table.schema),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Large table processing failed for {table_path}: {e}")
            return {'table_path': table_path, 'success': False, 'error': str(e)}
    
    async def _process_huge_table(self, client, table_path: str, table_info: Dict[str, Any]) -> Dict[str, Any]:
        try:
            primary_hostname_column = table_info['primary_hostname_column']
            
            sample_query = f"""
            SELECT *
            FROM `{table_path}`
            WHERE `{primary_hostname_column}` IS NOT NULL
            AND TRIM(`{primary_hostname_column}`) != ''
            AND RAND() < 0.1
            LIMIT 100000
            """
            
            logger.info(f"Huge table optimization: sampling 10% of data for {table_path}")
            
            job = client.query(sample_query)
            results = list(job.result())
            
            table = client.get_table(table_path)
            columns = [field.name for field in table.schema]
            
            hosts_found = 0
            for row in results:
                row_data = dict(zip(columns, row))
                hostname_value = row_data.get(primary_hostname_column)
                
                if hostname_value and str(hostname_value).strip():
                    self.cmdb_builder.process_single_host(
                        str(hostname_value).strip(), row_data, table_path
                    )
                    hosts_found += 1
            
            self.processing_stats['rows_processed'] += len(results)
            self.processing_stats['hosts_found'] += hosts_found
            
            return {
                'table_path': table_path,
                'strategy': 'huge_table',
                'rows_processed': len(results),
                'rows_sampled': True,
                'sample_percentage': 10,
                'estimated_total_hosts': hosts_found * 10,
                'hosts_found': hosts_found,
                'hostname_column': primary_hostname_column,
                'optimization_applied': True,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Huge table processing failed for {table_path}: {e}")
            return {'table_path': table_path, 'success': False, 'error': str(e)}
    
    def _is_essential_column(self, column_name: str) -> bool:
        essential_patterns = [
            'hostname', 'host', 'computer', 'device', 'endpoint', 'asset',
            'ip', 'address', 'fqdn', 'domain', 'mac', 'serial',
            'business', 'department', 'owner', 'region', 'datacenter',
            'environment', 'criticality', 'type', 'classification'
        ]
        
        column_lower = column_name.lower()
        return any(pattern in column_lower for pattern in essential_patterns)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        stats = self.processing_stats.copy()
        
        if stats['tables_attempted'] > 0:
            stats['success_rate'] = (stats['tables_successful'] / stats['tables_attempted']) * 100
            stats['skip_rate'] = (stats['tables_skipped'] / stats['tables_attempted']) * 100
            stats['error_rate'] = (stats['processing_errors'] / stats['tables_attempted']) * 100
        
        if stats['rows_processed'] > 0:
            stats['host_discovery_rate'] = (stats['hosts_found'] / stats['rows_processed']) * 100
        
        return stats
    
    def get_table_analysis_summary(self) -> Dict[str, Any]:
        if not self.table_metadata:
            return {}
        
        size_distribution = Counter(info['table_size_category'] for info in self.table_metadata.values())
        
        total_rows = sum(info['row_count'] for info in self.table_metadata.values())
        total_columns = sum(info['column_count'] for info in self.table_metadata.values())
        
        return {
            'tables_analyzed': len(self.table_metadata),
            'size_distribution': dict(size_distribution),
            'total_rows_across_tables': total_rows,
            'total_columns_across_tables': total_columns,
            'average_rows_per_table': total_rows / len(self.table_metadata) if self.table_metadata else 0,
            'average_columns_per_table': total_columns / len(self.table_metadata) if self.table_metadata else 0
        }

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        try:
            from storage.database import QuantumEnhancedDatabaseManager
            self.database_manager = QuantumEnhancedDatabaseManager(
                config.get('database_path', 'ao1_discovery.db')
            )
        except ImportError:
            logger.warning("Database manager not available")
            self.database_manager = None
        
        self.cmdb_builder = RealtimeCMDBBuilder(self.database_manager)
        self.table_processor = AdvancedTableProcessor(self.cmdb_builder)
        self.performance_monitor = PerformanceMonitor()
        
        self.discovery_stats = {
            'start_time': datetime.now(),
            'projects_processed': 0,
            'datasets_processed': 0,
            'tables_processed': 0,
            'total_execution_time': 0.0,
            'total_hosts_discovered': 0,
            'total_rows_processed': 0,
            'total_cells_analyzed': 0,
            'memory_peak_mb': 0.0,
            'processing_rate': 0.0,
            'error_count': 0,
            'optimization_applied': 0
        }
        
        self.project_results = {}
        self.execution_context = {
            'max_workers': config.get('max_workers', 16),
            'max_concurrent_tables': config.get('max_concurrent_tables', 8),
            'memory_limit_mb': config.get('max_memory_mb', 8192),
            'enable_optimizations': config.get('enable_optimizations', True),
            'batch_processing': config.get('batch_processing', True),
            'aggressive_caching': config.get('aggressive_caching', True)
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("AO1 Enhanced Discovery Engine Starting")
        start_time = datetime.now()
        
        self.performance_monitor.sample_system_metrics()
        
        try:
            total_results = []
            
            for project_id, client_manager in client_managers.items():
                logger.info(f"Processing project: {project_id}")
                
                project_start_time = time.time()
                project_result = await self._process_single_project(project_id, client_manager)
                project_processing_time = time.time() - project_start_time
                
                project_result['processing_time_seconds'] = project_processing_time
                self.project_results[project_id] = project_result
                
                total_results.extend(project_result.get('table_results', []))
                self.discovery_stats['projects_processed'] += 1
                
                logger.info(f"Project {project_id} completed in {project_processing_time:.2f}s")
                
                self.performance_monitor.sample_system_metrics()
                gc.collect()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.discovery_stats['total_execution_time'] = processing_time
            
            final_results = self.cmdb_builder.get_comprehensive_results()
            
            final_results['discovery_stats'].update(self.discovery_stats)
            final_results['table_processing_stats'] = self.table_processor.get_processing_stats()
            final_results['table_analysis_summary'] = self.table_processor.get_table_analysis_summary()
            final_results['performance_metrics'] = self.performance_monitor.get_summary()
            final_results['project_results'] = self.project_results
            final_results['execution_context'] = self.execution_context
            
            self._update_final_statistics(final_results)
            
            logger.info("AO1 Enhanced Discovery Completed Successfully")
            logger.info(f"Total hosts discovered: {len(final_results['assets']):,}")
            logger.info(f"Total processing time: {processing_time / 60:.1f} minutes")
            logger.info(f"Processing rate: {self.discovery_stats['processing_rate']:.2f} hosts/second")
            
            if self.database_manager:
                logger.info(f"Database storage count: {self.cmdb_builder.stored_count}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"AO1 Enhanced Discovery failed: {e}")
            self.discovery_stats['error_count'] += 1
            
            partial_results = self.cmdb_builder.get_comprehensive_results()
            partial_results['discovery_error'] = str(e)
            partial_results['discovery_stats'] = self.discovery_stats
            partial_results['partial_completion'] = True
            
            return partial_results
    
    async def _process_single_project(self, project_id: str, client_manager) -> Dict[str, Any]:
        project_result = {
            'project_id': project_id,
            'datasets_processed': 0,
            'tables_processed': 0,
            'table_results': [],
            'errors': [],
            'processing_time_seconds': 0.0
        }
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                self.discovery_stats['datasets_processed'] += len(datasets)
                
                logger.info(f"Found {len(datasets)} datasets in {project_id}")
                
                for dataset in datasets:
                    try:
                        dataset_result = await self._process_single_dataset(
                            client, project_id, dataset
                        )
                        
                        project_result['table_results'].extend(dataset_result['table_results'])
                        project_result['tables_processed'] += dataset_result['tables_processed']
                        project_result['datasets_processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"Dataset processing failed for {dataset.dataset_id}: {e}"
                        logger.error(error_msg)
                        project_result['errors'].append(error_msg)
                        self.discovery_stats['error_count'] += 1
                
                logger.info(f"Project {project_id} completed: {project_result['datasets_processed']} datasets, {project_result['tables_processed']} tables")
                
        except Exception as e:
            error_msg = f"Project processing failed for {project_id}: {e}"
            logger.error(error_msg)
            project_result['errors'].append(error_msg)
            self.discovery_stats['error_count'] += 1
        
        return project_result
    
    async def _process_single_dataset(self, client, project_id: str, dataset) -> Dict[str, Any]:
        dataset_result = {
            'dataset_id': dataset.dataset_id,
            'tables_processed': 0,
            'table_results': [],
            'processing_strategy': 'parallel' if self.execution_context['batch_processing'] else 'sequential'
        }
        
        try:
            dataset_tables = list(client.list_tables(dataset))
            logger.info(f"Processing dataset {dataset.dataset_id}: {len(dataset_tables)} tables")
            
            if self.execution_context['batch_processing'] and len(dataset_tables) > 3:
                dataset_result['table_results'] = await self._process_tables_parallel(
                    client, project_id, dataset.dataset_id, dataset_tables
                )
            else:
                dataset_result['table_results'] = await self._process_tables_sequential(
                    client, project_id, dataset.dataset_id, dataset_tables
                )
            
            dataset_result['tables_processed'] = len([r for r in dataset_result['table_results'] if r.get('success')])
            self.discovery_stats['tables_processed'] += dataset_result['tables_processed']
            
        except Exception as e:
            logger.error(f"Dataset processing failed for {dataset.dataset_id}: {e}")
            self.discovery_stats['error_count'] += 1
        
        return dataset_result
    
    async def _process_tables_parallel(self, client, project_id: str, dataset_id: str, 
                                     dataset_tables: List[Any]) -> List[Dict[str, Any]]:
        table_results = []
        
        max_workers = min(self.execution_context['max_concurrent_tables'], len(dataset_tables))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            table_futures = []
            
            for table_ref in dataset_tables:
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                future = executor.submit(
                    asyncio.run,
                    self.table_processor.process_table_comprehensively(client, table_path)
                )
                table_futures.append((future, table_path))
            
            for future, table_path in table_futures:
                try:
                    result = future.result(timeout=600)
                    table_results.append(result)
                    
                    if result.get('success'):
                        logger.debug(f"Table processed successfully: {table_path}")
                    else:
                        logger.warning(f"Table processing failed: {table_path}")
                        self.discovery_stats['error_count'] += 1
                
                except Exception as e:
                    error_result = {
                        'table_path': table_path,
                        'success': False,
                        'error': f'Future execution failed: {str(e)}',
                        'timeout': True
                    }
                    table_results.append(error_result)
                    logger.error(f"Table processing future failed for {table_path}: {e}")
                    self.discovery_stats['error_count'] += 1
        
        return table_results
    
    async def _process_tables_sequential(self, client, project_id: str, dataset_id: str,
                                       dataset_tables: List[Any]) -> List[Dict[str, Any]]:
        table_results = []
        
        for table_ref in dataset_tables:
            try:
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                result = await self.table_processor.process_table_comprehensively(client, table_path)
                table_results.append(result)
                
                if result.get('success'):
                    logger.debug(f"Table processed successfully: {table_path}")
                else:
                    logger.warning(f"Table processing failed: {table_path}")
                    self.discovery_stats['error_count'] += 1
            
            except Exception as e:
                error_result = {
                    'table_path': f"{project_id}.{dataset_id}.{table_ref.table_id}",
                    'success': False,
                    'error': str(e)
                }
                table_results.append(error_result)
                logger.error(f"Sequential table processing failed: {e}")
                self.discovery_stats['error_count'] += 1
        
        return table_results
    
    def _update_final_statistics(self, final_results: Dict[str, Any]):
        discovery_stats = final_results.get('discovery_stats', {})
        
        self.discovery_stats['total_hosts_discovered'] = discovery_stats.get('total_unique_hosts', 0)
        self.discovery_stats['total_rows_processed'] = discovery_stats.get('rows_processed', 0)
        self.discovery_stats['total_cells_analyzed'] = discovery_stats.get('cells_analyzed', 0)
        
        processing_time = self.discovery_stats['total_execution_time']
        if processing_time > 0 and self.discovery_stats['total_hosts_discovered'] > 0:
            self.discovery_stats['processing_rate'] = self.discovery_stats['total_hosts_discovered'] / processing_time
        
        performance_metrics = final_results.get('performance_metrics', {})
        memory_info = performance_metrics.get('memory_usage', {})
        self.discovery_stats['memory_peak_mb'] = memory_info.get('peak_mb', 0.0)
        
        table_stats = final_results.get('table_processing_stats', {})
        self.discovery_stats['optimization_applied'] = table_stats.get('optimization_count', 0)
    
    def get_discovery_summary(self) -> Dict[str, Any]:
        return {
            'engine_name': 'AO1_Enhanced_Discovery_Engine',
            'version': '2.0',
            'discovery_stats': self.discovery_stats,
            'cmdb_stats': self.cmdb_builder.processing_stats,
            'processor_stats': self.table_processor.get_processing_stats(),
            'performance_summary': self.performance_monitor.get_summary(),
            'execution_context': self.execution_context,
            'database_path': self.database_manager.db_path if self.database_manager else None,
            'configuration': self.config,
            'project_results_summary': {
                'total_projects': len(self.project_results),
                'successful_projects': len([r for r in self.project_results.values() if not r.get('errors')]),
                'total_errors': sum(len(r.get('errors', [])) for r in self.project_results.values())
            }
        }
    
    def export_discovery_results(self, output_path: str) -> bool:
        try:
            results = self.cmdb_builder.get_comprehensive_results()
            summary = self.get_discovery_summary()
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'discovery_summary': summary,
                'discovery_results': results,
                'project_breakdown': self.project_results
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Discovery results exported to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def get_performance_report(self) -> Dict[str, Any]:
        performance_summary = self.performance_monitor.get_summary()
        processing_stats = self.table_processor.get_processing_stats()
        cmdb_stats = self.cmdb_builder.processing_stats
        
        return {
            'execution_performance': {
                'total_runtime_seconds': self.discovery_stats['total_execution_time'],
                'hosts_discovered_per_second': self.discovery_stats['processing_rate'],
                'tables_processed_per_minute': (self.discovery_stats['tables_processed'] / 
                                               max(self.discovery_stats['total_execution_time'] / 60, 1)),
                'memory_efficiency': self._calculate_memory_efficiency(),
                'cpu_efficiency': self._calculate_cpu_efficiency(),
                'error_rate_percentage': (self.discovery_stats['error_count'] / 
                                         max(self.discovery_stats['tables_processed'], 1)) * 100
            },
            'resource_utilization': performance_summary,
            'processing_breakdown': {
                'table_processing': processing_stats,
                'cmdb_building': cmdb_stats,
                'optimization_impact': self._calculate_optimization_impact()
            },
            'quality_metrics': {
                'data_quality_score': self._calculate_data_quality_score(),
                'coverage_completeness': self._calculate_coverage_completeness(),
                'discovery_accuracy': self._calculate_discovery_accuracy()
            }
        }
    
    def _calculate_memory_efficiency(self) -> float:
        performance_summary = self.performance_monitor.get_summary()
        memory_info = performance_summary.get('memory_usage', {})
        peak_memory = memory_info.get('peak_mb', 0)
        hosts_discovered = self.discovery_stats['total_hosts_discovered']
        
        if peak_memory > 0 and hosts_discovered > 0:
            return hosts_discovered / peak_memory
        return 0.0
    
    def _calculate_cpu_efficiency(self) -> float:
        performance_summary = self.performance_monitor.get_summary()
        cpu_info = performance_summary.get('cpu_usage', {})
        avg_cpu = cpu_info.get('average_percent', 0)
        
        if avg_cpu > 0:
            return min(100, (self.discovery_stats['processing_rate'] * 100) / avg_cpu)
        return 0.0
    
    def _calculate_optimization_impact(self) -> Dict[str, Any]:
        table_stats = self.table_processor.get_processing_stats()
        
        return {
            'optimization_applications': self.discovery_stats['optimization_applied'],
            'batch_operations_used': table_stats.get('batch_operations', 0),
            'cache_hit_rate': (table_stats.get('cache_hits', 0) / 
                              max(table_stats.get('cache_hits', 0) + table_stats.get('cache_misses', 0), 1)) * 100,
            'processing_strategy_distribution': self._get_strategy_distribution()
        }
    
    def _get_strategy_distribution(self) -> Dict[str, int]:
        strategy_counts = defaultdict(int)
        
        for project_result in self.project_results.values():
            for table_result in project_result.get('table_results', []):
                strategy = table_result.get('strategy', 'unknown')
                strategy_counts[strategy] += 1
        
        return dict(strategy_counts)
    
    def _calculate_data_quality_score(self) -> float:
        cmdb_stats = self.cmdb_builder.processing_stats
        
        total_attributes = cmdb_stats.get('attributes_enriched', 0)
        quality_issues = cmdb_stats.get('data_quality_issues', 0)
        
        if total_attributes > 0:
            return max(0.0, 1.0 - (quality_issues / total_attributes))
        return 0.0
    
    def _calculate_coverage_completeness(self) -> float:
        results = self.cmdb_builder.get_comprehensive_results()
        coverage_analysis = results.get('coverage_analysis', {})
        
        total_hosts = coverage_analysis.get('total_hosts', 0)
        fully_covered = coverage_analysis.get('fully_covered_hosts', 0)
        
        if total_hosts > 0:
            return fully_covered / total_hosts
        return 0.0
    
    def _calculate_discovery_accuracy(self) -> float:
        cmdb_stats = self.cmdb_builder.processing_stats
        
        total_discovered = cmdb_stats.get('hosts_discovered', 0)
        validation_failures = cmdb_stats.get('validation_failures', 0)
        
        if total_discovered > 0:
            return max(0.0, 1.0 - (validation_failures / total_discovered))
        return 0.0
    
    def cleanup_resources(self):
        try:
            if self.cmdb_builder.batch_buffer:
                self.cmdb_builder._flush_batch_to_database()
            
            if self.database_manager:
                self.database_manager.close()
            
            self.table_processor.table_cache.clear()
            self.table_processor.column_analysis_cache.clear()
            
            gc.collect()
            
            logger.info("AO1 Engine resources cleaned up successfully")
        
        except Exception as e:
            logger.error(f"Resource cleanup failed: {e}")

class AO1DiscoveryOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engines = {}
        self.orchestration_stats = {
            'engines_created': 0,
            'total_discoveries': 0,
            'successful_discoveries': 0,
            'failed_discoveries': 0,
            'total_processing_time': 0.0
        }
    
    def create_engine(self, engine_id: str, engine_config: Dict[str, Any] = None) -> AO1SuperEngine:
        effective_config = self.config.copy()
        if engine_config:
            effective_config.update(engine_config)
        
        engine = AO1SuperEngine(effective_config)
        self.engines[engine_id] = engine
        self.orchestration_stats['engines_created'] += 1
        
        logger.info(f"AO1 Engine created: {engine_id}")
        return engine
    
    async def orchestrate_discovery(self, engine_id: str, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        if engine_id not in self.engines:
            raise ValueError(f"Engine {engine_id} not found")
        
        engine = self.engines[engine_id]
        
        try:
            start_time = time.time()
            result = await engine.enhanced_discovery(client_managers)
            processing_time = time.time() - start_time
            
            self.orchestration_stats['total_discoveries'] += 1
            self.orchestration_stats['successful_discoveries'] += 1
            self.orchestration_stats['total_processing_time'] += processing_time
            
            result['orchestration_metadata'] = {
                'engine_id': engine_id,
                'orchestrator_stats': self.orchestration_stats.copy()
            }
            
            return result
        
        except Exception as e:
            self.orchestration_stats['total_discoveries'] += 1
            self.orchestration_stats['failed_discoveries'] += 1
            
            logger.error(f"Orchestrated discovery failed for engine {engine_id}: {e}")
            raise
    
    def get_orchestration_summary(self) -> Dict[str, Any]:
        return {
            'orchestrator_version': '1.0',
            'engines_managed': len(self.engines),
            'orchestration_statistics': self.orchestration_stats,
            'engine_summaries': {
                engine_id: engine.get_discovery_summary() 
                for engine_id, engine in self.engines.items()
            }
        }
    
    def cleanup_all_engines(self):
        for engine_id, engine in self.engines.items():
            try:
                engine.cleanup_resources()
                logger.info(f"Engine {engine_id} cleaned up")
            except Exception as e:
                logger.error(f"Failed to cleanup engine {engine_id}: {e}")
        
        self.engines.clear()
        logger.info("All AO1 engines cleaned up")