#!/usr/bin/env python3

import re
from typing import List, Optional, Tuple

class ContentBasedMatcher:
    def __init__(self):
        self.patterns = {
            'endpoint': ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system'],
            'domain': ['domain', 'fqdn', 'dns', 'namespace'],
            'region': ['region', 'geo', 'location', 'site', 'area', 'zone', 'datacenter', 'center', 'country'],
            'environment': ['env', 'environment', 'stage', 'tier', 'level'],
            'ip': ['ip', 'address'],
            'os': ['os', 'operating', 'platform'],
            'app': ['app', 'application', 'service', 'software'],
            'type': ['type', 'category', 'class', 'kind'],
            'scope': ['scope', 'pci', 'compliance'],
            'security': ['security', 'agent', 'edr', 'av']
        }
        self._validation_cache = {}
    
    def analyze_column(self, column_name: str, sample_values: List[str]) -> Optional[Tuple[str, float]]:
        cache_key = f"{column_name}:{hash(tuple(sample_values))}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
        
        skip_patterns = ['id', 'key', 'count', 'total', 'date', 'time', 'created', 'updated', 'status', 'flag']
        column_lower = column_name.lower()
        
        if any(skip in column_lower for skip in skip_patterns):
            result = None
        else:
            best_match = None
            best_score = 0.0
            
            for field_type, keywords in self.patterns.items():
                score = self._calculate_match_score(column_lower, keywords)
                if score > best_score and score >= 0.3:
                    if self._validate_sample_data(field_type, sample_values):
                        best_match = field_type
                        best_score = score
            
            result = (best_match, best_score) if best_match else None
        
        self._validation_cache[cache_key] = result
        return result
    
    def _calculate_match_score(self, column_name: str, keywords: List[str]) -> float:
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
        
        return best_score
    
    def _validate_sample_data(self, field_type: str, sample_values: List[str]) -> bool:
        if not sample_values or len(sample_values) < 3:
            return False
        
        valid_count = 0
        for value in sample_values[:10]:
            if not value:
                continue
            
            value_str = str(value).strip()
            if len(value_str) < 2:
                continue
            
            if field_type == 'endpoint':
                if self._looks_like_hostname(value_str):
                    valid_count += 1
            elif field_type == 'domain':
                if self._looks_like_domain(value_str):
                    valid_count += 1
            elif field_type == 'ip':
                if self._looks_like_ip(value_str):
                    valid_count += 1
            elif field_type == 'region':
                if self._looks_like_region(value_str):
                    valid_count += 1
            elif field_type == 'environment':
                if self._looks_like_environment(value_str):
                    valid_count += 1
            else:
                if self._looks_like_general_text(value_str):
                    valid_count += 1
        
        return (valid_count / len(sample_values)) >= 0.4
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 3 or len(value) > 253:
            return False
        
        hostname_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$'
        ]
        
        if any(re.match(pattern, value) for pattern in hostname_patterns):
            return True
        
        common_prefixes = ['srv', 'web', 'app', 'db', 'sql', 'prod', 'dev', 'test']
        common_suffixes = ['server', 'srv', 'host', 'node', '01', '02', '03']
        
        value_lower = value.lower()
        has_prefix = any(value_lower.startswith(prefix) for prefix in common_prefixes)
        has_suffix = any(value_lower.endswith(suffix) for suffix in common_suffixes)
        
        return has_prefix or has_suffix
    
    def _looks_like_domain(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 4:
            return False
        
        if '.' not in value:
            return False
        
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'
        return bool(re.match(domain_pattern, value))
    
    def _looks_like_ip(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, value):
            try:
                octets = value.split('.')
                return all(0 <= int(octet) <= 255 for octet in octets)
            except ValueError:
                return False
        return False
    
    def _looks_like_region(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 50:
            return False
        
        region_patterns = [
            r'^[a-zA-Z][a-zA-Z\s\-_]+$',
            r'^[A-Z]{2,3}[-_]?[A-Z]{2,4}[-_]?\d*$',
            r'^(us|eu|ap|ca|sa)[-_](east|west|central|north|south)[-_]?\d*$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in region_patterns)
    
    def _looks_like_environment(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        env_values = ['prod', 'production', 'dev', 'development', 'test', 'testing', 
                     'stage', 'staging', 'qa', 'uat', 'sit', 'preprod']
        
        return value.lower() in env_values
    
    def _looks_like_general_text(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 100:
            return False
        
        return value.replace(' ', '').replace('-', '').replace('_', '').isalnum()