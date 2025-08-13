#!/usr/bin/env python3

import re
import ipaddress
from typing import List, Dict, Any

class ContentAnalyzer:
    def __init__(self):
        self.hostname_validators = [
            self._is_hostname_pattern,
            self._is_server_name,
            self._is_endpoint_name,
            self._is_computer_name
        ]
        
        self.ip_validators = [
            self._is_ipv4_address,
            self._is_private_ip,
            self._is_public_ip
        ]
        
        self.fqdn_validators = [
            self._is_fqdn_pattern,
            self._is_domain_name
        ]
    
    def analyze_column_content(self, values: List[str]) -> Dict[str, float]:
        if not values:
            return {}
        
        clean_values = [str(v).strip() for v in values if v and str(v).strip()]
        if not clean_values:
            return {}
        
        scores = {
            'hostname': self._score_hostname_content(clean_values),
            'ip_address': self._score_ip_content(clean_values),
            'fqdn': self._score_fqdn_content(clean_values),
            'mac_address': self._score_mac_content(clean_values),
            'infrastructure_type': self._score_infrastructure_content(clean_values),
            'system_classification': self._score_system_content(clean_values),
            'region': self._score_region_content(clean_values),
            'business_unit': self._score_business_content(clean_values)
        }
        
        return {k: v for k, v in scores.items() if v > 0.3}
    
    def _score_hostname_content(self, values: List[str]) -> float:
        hostname_count = 0
        for value in values[:50]:
            for validator in self.hostname_validators:
                if validator(value):
                    hostname_count += 1
                    break
        
        return hostname_count / min(len(values), 50) if values else 0.0
    
    def _score_ip_content(self, values: List[str]) -> float:
        ip_count = 0
        for value in values[:50]:
            for validator in self.ip_validators:
                if validator(value):
                    ip_count += 1
                    break
        
        return ip_count / min(len(values), 50) if values else 0.0
    
    def _score_fqdn_content(self, values: List[str]) -> float:
        fqdn_count = 0
        for value in values[:50]:
            for validator in self.fqdn_validators:
                if validator(value):
                    fqdn_count += 1
                    break
        
        return fqdn_count / min(len(values), 50) if values else 0.0
    
    def _score_mac_content(self, values: List[str]) -> float:
        mac_count = sum(1 for v in values[:50] if self._is_mac_address(v))
        return mac_count / min(len(values), 50) if values else 0.0
    
    def _score_infrastructure_content(self, values: List[str]) -> float:
        infra_terms = ['cloud', 'onprem', 'on-prem', 'saas', 'api', 'physical', 'virtual', 'aws', 'azure', 'gcp']
        match_count = sum(1 for v in values[:50] if any(term in str(v).lower() for term in infra_terms))
        return match_count / min(len(values), 50) if values else 0.0
    
    def _score_system_content(self, values: List[str]) -> float:
        system_terms = ['windows', 'linux', 'unix', 'server', 'workstation', 'database', 'web', 'centos', 'ubuntu']
        match_count = sum(1 for v in values[:50] if any(term in str(v).lower() for term in system_terms))
        return match_count / min(len(values), 50) if values else 0.0
    
    def _score_region_content(self, values: List[str]) -> float:
        region_terms = ['us', 'usa', 'eu', 'europe', 'apac', 'asia', 'americas', 'emea', 'north', 'south', 'east', 'west']
        match_count = sum(1 for v in values[:50] if any(term in str(v).lower() for term in region_terms))
        return match_count / min(len(values), 50) if values else 0.0
    
    def _score_business_content(self, values: List[str]) -> float:
        business_terms = ['finance', 'marketing', 'sales', 'hr', 'it', 'operations', 'legal', 'compliance']
        match_count = sum(1 for v in values[:50] if any(term in str(v).lower() for term in business_terms))
        return match_count / min(len(values), 50) if values else 0.0
    
    def _is_hostname_pattern(self, value: str) -> bool:
        if not value or len(value) < 2 or len(value) > 253:
            return False
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', value)) or bool(re.match(r'^[a-zA-Z0-9]+$', value))
    
    def _is_server_name(self, value: str) -> bool:
        server_patterns = ['srv', 'server', 'web', 'app', 'db', 'sql', 'win', 'linux']
        return any(pattern in value.lower() for pattern in server_patterns)
    
    def _is_endpoint_name(self, value: str) -> bool:
        endpoint_patterns = ['pc', 'laptop', 'desktop', 'workstation', 'endpoint']
        return any(pattern in value.lower() for pattern in endpoint_patterns)
    
    def _is_computer_name(self, value: str) -> bool:
        return bool(re.match(r'^[A-Z0-9\-]+$', value)) and 3 <= len(value) <= 15
    
    def _is_ipv4_address(self, value: str) -> bool:
        try:
            addr = ipaddress.IPv4Address(value)
            return True
        except:
            return False
    
    def _is_private_ip(self, value: str) -> bool:
        try:
            addr = ipaddress.IPv4Address(value)
            return addr.is_private
        except:
            return False
    
    def _is_public_ip(self, value: str) -> bool:
        try:
            addr = ipaddress.IPv4Address(value)
            return not addr.is_private and not addr.is_loopback
        except:
            return False
    
    def _is_fqdn_pattern(self, value: str) -> bool:
        return '.' in value and bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', value))
    
    def _is_domain_name(self, value: str) -> bool:
        return '.' in value and len(value.split('.')) >= 2
    
    def _is_mac_address(self, value: str) -> bool:
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$'
        ]
        return any(re.match(pattern, value) for pattern in mac_patterns)