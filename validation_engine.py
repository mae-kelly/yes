#!/usr/bin/env python3

import re
import ipaddress
from typing import List, Dict, Any

class ValidationEngine:
    def __init__(self):
        self.validators = self._initialize_validators()
    
    def _initialize_validators(self) -> Dict[str, callable]:
        return {
            '_validate_hostname': self._validate_hostname,
            '_validate_fqdn': self._validate_fqdn,
            '_validate_ip': self._validate_ip,
            '_validate_mac': self._validate_mac,
            '_validate_infrastructure_type': self._validate_infrastructure_type,
            '_validate_system_classification': self._validate_system_classification,
            '_validate_global_region': self._validate_global_region,
            '_validate_country': self._validate_country,
            '_validate_data_center': self._validate_data_center,
            '_validate_cloud_region': self._validate_cloud_region,
            '_validate_business_unit': self._validate_business_unit,
            '_validate_cio': self._validate_cio,
            '_validate_apm': self._validate_apm,
            '_validate_application_class': self._validate_application_class,
            '_validate_coverage': self._validate_coverage,
            '_validate_log_types': self._validate_log_types,
            '_validate_network_zones': self._validate_network_zones,
            '_validate_geolocation': self._validate_geolocation,
            '_validate_vpc': self._validate_vpc,
            '_validate_domain_visibility': self._validate_domain_visibility,
            '_validate_internal_external': self._validate_internal_external,
            '_validate_controls': self._validate_controls
        }
    
    def validate_field_content(self, field_type: str, values: List[str], validators: List[str]) -> float:
        if not values:
            return 0.0
        
        valid_count = 0
        total_count = min(len(values), 20)
        
        for value in values[:total_count]:
            is_valid = False
            
            for validator_name in validators:
                validator_func = self.validators.get(validator_name)
                if validator_func and validator_func(value):
                    is_valid = True
                    break
            
            if is_valid:
                valid_count += 1
        
        return valid_count / total_count if total_count > 0 else 0.0
    
    def _validate_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 253:
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        if value.count('.') > 5:
            return False
        
        hostname_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, value, re.IGNORECASE) for pattern in hostname_patterns):
            return True
        
        hostname_indicators = ['srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 'host', 'vm', 'node']
        value_lower = value.lower()
        if any(indicator in value_lower for indicator in hostname_indicators):
            return True
        
        return False
    
    def _validate_fqdn(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 4 or len(value) > 253:
            return False
        
        if value.count('.') < 1:
            return False
        
        fqdn_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'
        return bool(re.match(fqdn_pattern, value, re.IGNORECASE))
    
    def _validate_ip(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        try:
            ipaddress.ip_address(value.strip())
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False
    
    def _validate_mac(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$'
        ]
        
        return any(re.match(pattern, value.strip()) for pattern in mac_patterns)
    
    def _validate_infrastructure_type(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        infra_types = [
            'onprem', 'on-prem', 'on-premises', 'physical', 'bare', 'metal',
            'cloud', 'aws', 'azure', 'gcp', 'saas', 'software', 'service',
            'api', 'interface', 'gateway'
        ]
        
        value_lower = value.lower()
        return any(infra_type in value_lower for infra_type in infra_types)
    
    def _validate_system_classification(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        system_types = [
            'web', 'webserver', 'iis', 'apache', 'windows', 'win', 'microsoft',
            'linux', 'unix', 'centos', 'ubuntu', 'nix', 'aix', 'solaris',
            'mainframe', 'mf', 'zos', 'database', 'db', 'sql', 'oracle',
            'appliance', 'firewall', 'switch', 'router'
        ]
        
        value_lower = value.lower()
        return any(system_type in value_lower for system_type in system_types)
    
    def _validate_global_region(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        regions = [
            'us', 'usa', 'america', 'north america', 'eu', 'europe', 'emea',
            'ap', 'asia', 'pacific', 'apac', 'latam', 'south america'
        ]
        
        value_lower = value.lower()
        return any(region in value_lower for region in regions)
    
    def _validate_country(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        country_indicators = [
            'us', 'usa', 'united states', 'canada', 'uk', 'united kingdom',
            'germany', 'france', 'japan', 'australia', 'brazil', 'india'
        ]
        
        value_lower = value.lower()
        return any(country in value_lower for country in country_indicators) or len(value) == 2
    
    def _validate_data_center(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        dc_indicators = ['dc', 'datacenter', 'data center', 'facility', 'site']
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in dc_indicators)
    
    def _validate_cloud_region(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        cloud_patterns = [
            r'us-(east|west|central)-\d+',
            r'eu-(west|central|north)-\d+',
            r'ap-(southeast|northeast|south)-\d+',
            r'(aws|azure|gcp)[-_]',
            r'(eastus|westus|centralus)',
            r'(us-east-1|us-west-2|eu-west-1)'
        ]
        
        return any(re.search(pattern, value, re.IGNORECASE) for pattern in cloud_patterns)
    
    def _validate_business_unit(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 100:
            return False
        
        return value.replace(' ', '').replace('-', '').replace('_', '').isalnum()
    
    def _validate_cio(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        cio_indicators = ['cio', 'chief', 'information', 'officer']
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in cio_indicators)
    
    def _validate_apm(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        apm_indicators = ['apm', 'application', 'performance', 'monitoring']
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in apm_indicators)
    
    def _validate_application_class(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        app_indicators = ['web', 'database', 'api', 'service', 'application', 'batch']
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in app_indicators)
    
    def _validate_coverage(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        coverage_values = [
            'true', 'false', 'yes', 'no', 'enabled', 'disabled', 'active', 
            'inactive', 'installed', 'not installed', 'covered', 'not covered'
        ]
        
        return value.lower().strip() in coverage_values
    
    def _validate_log_types(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        log_indicators = [
            'firewall', 'ids', 'ips', 'ndr', 'proxy', 'dns', 'waf',
            'syslog', 'winlog', 'edr', 'dlp', 'fim', 'cloudtrail',
            'weblog', 'applog', 'auth', 'authentication'
        ]
        
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in log_indicators)
    
    def _validate_network_zones(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        zone_indicators = ['dmz', 'internal', 'external', 'vlan', 'subnet', 'zone']
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in zone_indicators)
    
    def _validate_geolocation(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        geo_indicators = ['building', 'floor', 'room', 'location', 'address']
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in geo_indicators)
    
    def _validate_vpc(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        vpc_patterns = [
            r'vpc-[a-zA-Z0-9]+',
            r'vnet-[a-zA-Z0-9]+',
            r'virtual.*private.*cloud'
        ]
        
        return any(re.search(pattern, value, re.IGNORECASE) for pattern in vpc_patterns)
    
    def _validate_domain_visibility(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        domain_indicators = ['domain', 'ad', 'dns', 'ldap']
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in domain_indicators)
    
    def _validate_internal_external(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        return value.lower().strip() in ['internal', 'external', 'dmz', 'public', 'private']
    
    def _validate_controls(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        control_indicators = ['control', 'compliance', 'security', 'policy', 'standard']
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in control_indicators)