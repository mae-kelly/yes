#!/usr/bin/env python3

import re
from typing import List, Optional, Tuple, Dict

class ContentBasedMatcher:
    def __init__(self):
        self.patterns = {
            'hostname': ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system', 'name'],
            'fqdn': ['fqdn', 'full', 'qualified', 'domain', 'dns', 'canonical', 'complete'],
            'ip_address': ['ip', 'address', 'addr', 'ipv4', 'ipv6', 'network'],
            'infrastructure_type': ['infra', 'infrastructure', 'type', 'category', 'class', 'tier', 'platform'],
            'system_classification': ['classification', 'class', 'type', 'category', 'kind', 'role', 'function'],
            'region': ['region', 'geo', 'location', 'site', 'area', 'zone', 'datacenter', 'center', 'country', 'locale'],
            'country': ['country', 'nation', 'territory', 'state', 'province'],
            'data_center': ['datacenter', 'data_center', 'dc', 'facility', 'site', 'center', 'location'],
            'cloud_region': ['cloud', 'aws', 'azure', 'gcp', 'region', 'availability', 'zone'],
            'business_unit': ['business', 'unit', 'bu', 'org', 'organization', 'department', 'division'],
            'environment': ['env', 'environment', 'stage', 'tier', 'level', 'deployment'],
            'operating_system': ['os', 'operating', 'system', 'platform', 'version'],
            'application': ['app', 'application', 'service', 'software', 'program'],
            'owner': ['owner', 'responsible', 'contact', 'admin', 'manager'],
            'status': ['status', 'state', 'condition', 'health', 'active'],
            'compliance': ['compliance', 'compliant', 'pci', 'sox', 'hipaa', 'gdpr'],
            'security': ['security', 'agent', 'edr', 'av', 'antivirus', 'protection'],
            'network': ['network', 'subnet', 'vlan', 'segment', 'cidr'],
            'port': ['port', 'service', 'protocol', 'tcp', 'udp'],
            'last_seen': ['last', 'seen', 'updated', 'modified', 'timestamp', 'date'],
            'created': ['created', 'added', 'inserted', 'established', 'provisioned'],
            'criticality': ['critical', 'criticality', 'importance', 'priority', 'severity'],
            'cost_center': ['cost', 'center', 'billing', 'charge', 'account'],
            'vendor': ['vendor', 'manufacturer', 'make', 'brand', 'supplier'],
            'model': ['model', 'type', 'series', 'variant', 'sku'],
            'serial': ['serial', 'number', 'id', 'identifier', 'asset_tag'],
            'cpu': ['cpu', 'processor', 'core', 'vcpu', 'compute'],
            'memory': ['memory', 'ram', 'gb', 'mb', 'storage'],
            'disk': ['disk', 'storage', 'drive', 'volume', 'capacity'],
            'virtualization': ['virtual', 'vm', 'hypervisor', 'vmware', 'hyper'],
            'cluster': ['cluster', 'group', 'pool', 'farm', 'collection'],
            'backup': ['backup', 'restore', 'recovery', 'snapshot', 'archive'],
            'monitoring': ['monitor', 'alert', 'snmp', 'agent', 'probe'],
            'patch_level': ['patch', 'update', 'version', 'build', 'release'],
            'license': ['license', 'licensing', 'key', 'activation', 'subscription']
        }
        self._validation_cache = {}
    
    def analyze_column_intelligent(self, column_name: str, sample_values: List[str]) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        cache_key = f"{column_name}:{hash(tuple(sample_values))}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
        
        skip_patterns = ['id', 'key', 'count', 'total', 'flag', 'ind', 'flg']
        column_lower = column_name.lower()
        
        if any(skip in column_lower for skip in skip_patterns if len(skip) >= 3):
            result = None
        else:
            best_match = None
            best_score = 0.0
            metadata = {}
            
            for field_type, keywords in self.patterns.items():
                score = self._calculate_intelligent_score(column_lower, keywords)
                if score > best_score and score >= 0.25:
                    validation_result = self._validate_sample_data_intelligent(field_type, sample_values)
                    if validation_result['is_valid']:
                        best_match = field_type
                        best_score = score
                        metadata = validation_result['metadata']
            
            result = (best_match, best_score, metadata) if best_match else None
        
        self._validation_cache[cache_key] = result
        return result
    
    def _calculate_intelligent_score(self, column_name: str, keywords: List[str]) -> float:
        clean_column = re.sub(r'[_\-\s]', '', column_name)
        
        best_score = 0.0
        for keyword in keywords:
            clean_keyword = re.sub(r'[_\-\s]', '', keyword)
            
            if clean_keyword == clean_column:
                return 1.0
            
            if clean_keyword in clean_column:
                score = len(clean_keyword) / len(clean_column)
                best_score = max(best_score, score)
            
            if clean_column in clean_keyword and len(clean_column) >= 3:
                score = len(clean_column) / len(clean_keyword)
                best_score = max(best_score, score)
            
            if any(part in clean_column for part in clean_keyword.split('_')):
                score = 0.7
                best_score = max(best_score, score)
        
        return best_score
    
    def _validate_sample_data_intelligent(self, field_type: str, sample_values: List[str]) -> Dict[str, Any]:
        if not sample_values or len(sample_values) < 2:
            return {'is_valid': False, 'metadata': {}}
        
        valid_count = 0
        metadata = {
            'sample_count': len(sample_values),
            'unique_values': len(set(sample_values)),
            'patterns': [],
            'data_quality': 'unknown'
        }
        
        for value in sample_values[:20]:
            if not value:
                continue
            
            value_str = str(value).strip()
            if len(value_str) < 1:
                continue
            
            is_valid = False
            
            if field_type == 'hostname':
                is_valid = self._validate_hostname(value_str)
            elif field_type == 'fqdn':
                is_valid = self._validate_fqdn(value_str)
            elif field_type == 'ip_address':
                is_valid = self._validate_ip_address(value_str)
            elif field_type == 'infrastructure_type':
                is_valid = self._validate_infrastructure_type(value_str)
            elif field_type == 'system_classification':
                is_valid = self._validate_system_classification(value_str)
            elif field_type == 'region':
                is_valid = self._validate_region(value_str)
            elif field_type == 'country':
                is_valid = self._validate_country(value_str)
            elif field_type == 'data_center':
                is_valid = self._validate_data_center(value_str)
            elif field_type == 'cloud_region':
                is_valid = self._validate_cloud_region(value_str)
            elif field_type == 'business_unit':
                is_valid = self._validate_business_unit(value_str)
            elif field_type == 'environment':
                is_valid = self._validate_environment(value_str)
            elif field_type == 'operating_system':
                is_valid = self._validate_operating_system(value_str)
            elif field_type == 'application':
                is_valid = self._validate_application(value_str)
            elif field_type == 'status':
                is_valid = self._validate_status(value_str)
            elif field_type == 'compliance':
                is_valid = self._validate_compliance(value_str)
            elif field_type == 'criticality':
                is_valid = self._validate_criticality(value_str)
            else:
                is_valid = self._validate_general_text(value_str)
            
            if is_valid:
                valid_count += 1
                if value_str not in metadata['patterns']:
                    metadata['patterns'].append(value_str)
        
        validation_ratio = (valid_count / len(sample_values)) if sample_values else 0
        metadata['validation_ratio'] = validation_ratio
        
        if validation_ratio >= 0.8:
            metadata['data_quality'] = 'excellent'
        elif validation_ratio >= 0.6:
            metadata['data_quality'] = 'good'
        elif validation_ratio >= 0.4:
            metadata['data_quality'] = 'fair'
        else:
            metadata['data_quality'] = 'poor'
        
        return {
            'is_valid': validation_ratio >= 0.3,
            'metadata': metadata
        }
    
    def _validate_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 253:
            return False
        
        hostname_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$'
        ]
        
        if any(re.match(pattern, value) for pattern in hostname_patterns):
            return True
        
        common_prefixes = ['srv', 'web', 'app', 'db', 'sql', 'prod', 'dev', 'test', 'win', 'linux']
        common_suffixes = ['server', 'srv', 'host', 'node', '01', '02', '03']
        
        value_lower = value.lower()
        has_prefix = any(value_lower.startswith(prefix) for prefix in common_prefixes)
        has_suffix = any(value_lower.endswith(suffix) for suffix in common_suffixes)
        
        return has_prefix or has_suffix or re.match(r'^[a-zA-Z0-9\-_]+$', value)
    
    def _validate_fqdn(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 4:
            return False
        
        if '.' not in value:
            return False
        
        fqdn_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'
        return bool(re.match(fqdn_pattern, value))
    
    def _validate_ip_address(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ipv4_pattern, value):
            try:
                octets = value.split('.')
                return all(0 <= int(octet) <= 255 for octet in octets)
            except ValueError:
                return False
        
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        return bool(re.match(ipv6_pattern, value))
    
    def _validate_infrastructure_type(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        infra_types = ['physical', 'virtual', 'cloud', 'container', 'on-prem', 'on-premise', 
                      'saas', 'paas', 'iaas', 'hybrid', 'edge', 'aws', 'azure', 'gcp']
        
        return value.lower() in infra_types or any(itype in value.lower() for itype in infra_types)
    
    def _validate_system_classification(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        classifications = ['server', 'workstation', 'laptop', 'desktop', 'mobile', 'tablet',
                          'database', 'web', 'application', 'file', 'print', 'domain',
                          'network', 'security', 'backup', 'storage', 'virtualization']
        
        return any(cls in value.lower() for cls in classifications)
    
    def _validate_region(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 50:
            return False
        
        region_patterns = [
            r'^[a-zA-Z][a-zA-Z\s\-_]+$',
            r'^[A-Z]{2,3}[-_]?[A-Z]{2,4}[-_]?\d*$',
            r'^(us|eu|ap|ca|sa)[-_](east|west|central|north|south)[-_]?\d*$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in region_patterns)
    
    def _validate_country(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        countries = ['us', 'usa', 'united states', 'uk', 'united kingdom', 'canada', 'germany',
                    'france', 'japan', 'china', 'india', 'australia', 'brazil', 'mexico']
        
        return value.lower() in countries or len(value) == 2 and value.isalpha()
    
    def _validate_data_center(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        dc_patterns = [
            r'^dc\d+$',
            r'^datacenter\d+$',
            r'^[a-zA-Z]{2,4}\d+$',
            r'^[a-zA-Z]+[-_]dc[-_]?\d*$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in dc_patterns)
    
    def _validate_cloud_region(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        cloud_regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1',
                        'eastus', 'westus', 'northeurope', 'southeastasia']
        
        return value.lower() in cloud_regions or any(provider in value.lower() 
                                                   for provider in ['aws', 'azure', 'gcp'])
    
    def _validate_business_unit(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        bu_types = ['it', 'finance', 'hr', 'sales', 'marketing', 'operations', 'engineering',
                   'security', 'legal', 'compliance', 'audit', 'procurement']
        
        return any(bu in value.lower() for bu in bu_types) or re.match(r'^[a-zA-Z\s&\-_]+$', value)
    
    def _validate_environment(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        env_values = ['prod', 'production', 'dev', 'development', 'test', 'testing', 
                     'stage', 'staging', 'qa', 'uat', 'sit', 'preprod', 'demo', 'sandbox']
        
        return value.lower() in env_values
    
    def _validate_operating_system(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        os_types = ['windows', 'linux', 'unix', 'macos', 'centos', 'ubuntu', 'redhat',
                   'debian', 'suse', 'aix', 'solaris', 'freebsd']
        
        return any(os_type in value.lower() for os_type in os_types)
    
    def _validate_application(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        app_types = ['web', 'database', 'email', 'file', 'print', 'backup', 'monitoring',
                    'security', 'crm', 'erp', 'cms', 'api', 'service']
        
        return any(app in value.lower() for app in app_types) or re.match(r'^[a-zA-Z0-9\s\-_\.]+$', value)
    
    def _validate_status(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        status_values = ['active', 'inactive', 'online', 'offline', 'running', 'stopped',
                        'enabled', 'disabled', 'up', 'down', 'healthy', 'unhealthy']
        
        return value.lower() in status_values
    
    def _validate_compliance(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        compliance_values = ['pci', 'sox', 'hipaa', 'gdpr', 'compliant', 'non-compliant',
                           'yes', 'no', 'true', 'false', 'exempt']
        
        return value.lower() in compliance_values
    
    def _validate_criticality(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        criticality_values = ['high', 'medium', 'low', 'critical', 'important', 'normal',
                             '1', '2', '3', '4', '5', 'tier1', 'tier2', 'tier3']
        
        return value.lower() in criticality_values
    
    def _validate_general_text(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 1 or len(value) > 500:
            return False
        
        return value.replace(' ', '').replace('-', '').replace('_', '').replace('.', '').isalnum()