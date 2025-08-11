#!/usr/bin/env python3

import re
from typing import List, Optional, Tuple, Dict

class ContentBasedMatcher:
    def __init__(self):
        self.patterns = {
            'endpoint': ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system', 'workstation'],
            'fqdn': ['fqdn', 'dns', 'domain', 'qualified', 'full', 'canonical'],
            'ip': ['ip', 'address', 'addr', 'ipaddr'],
            'domain': ['domain', 'dns', 'namespace', 'zone'],
            'region': ['region', 'geo', 'location', 'site', 'area', 'zone', 'datacenter', 'center', 'country'],
            'environment': ['env', 'environment', 'stage', 'tier', 'level'],
            'os': ['os', 'operating', 'platform', 'system'],
            'app': ['app', 'application', 'service', 'software'],
            'type': ['type', 'category', 'class', 'kind', 'classification'],
            'scope': ['scope', 'pci', 'compliance'],
            'security': ['security', 'agent', 'edr', 'av', 'antivirus'],
            'network': ['network', 'net', 'subnet', 'vlan', 'vpc'],
            'infrastructure': ['infrastructure', 'infra', 'platform', 'cloud', 'aws', 'azure', 'gcp'],
            'business': ['business', 'unit', 'org', 'organization', 'department', 'team'],
            'owner': ['owner', 'responsible', 'contact', 'admin', 'manager'],
            'status': ['status', 'state', 'active', 'enabled', 'online'],
            'version': ['version', 'ver', 'release', 'build'],
            'cost': ['cost', 'billing', 'charge', 'price'],
            'criticality': ['critical', 'priority', 'importance', 'tier'],
            'compliance': ['compliance', 'regulation', 'policy', 'standard'],
            'performance': ['cpu', 'memory', 'disk', 'performance', 'utilization'],
            'configuration': ['config', 'setting', 'parameter', 'property']
        }
        self._validation_cache = {}
    
    def analyze_column(self, column_name: str, sample_values: List[str]) -> Optional[Tuple[str, float]]:
        cache_key = f"{column_name}:{hash(tuple(sample_values[:5]))}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
        
        skip_patterns = ['id', 'key', 'count', 'total', 'sum', 'avg', 'created', 'updated', 'modified', 'deleted', 'flag', 'bool']
        column_lower = column_name.lower()
        
        if any(skip in column_lower for skip in skip_patterns):
            result = None
        else:
            best_match = None
            best_score = 0.0
            
            for field_type, keywords in self.patterns.items():
                score = self._calculate_match_score(column_lower, keywords)
                if score > best_score and score >= 0.2:
                    if self._validate_sample_data(field_type, sample_values):
                        best_match = field_type
                        best_score = score
            
            result = (best_match, best_score) if best_match else None
        
        self._validation_cache[cache_key] = result
        return result
    
    def analyze_all_columns(self, columns: List[str]) -> Dict[str, List[str]]:
        categorized_columns = {}
        
        for column in columns:
            column_lower = column.lower()
            
            for field_type, keywords in self.patterns.items():
                for keyword in keywords:
                    if keyword in column_lower:
                        if field_type not in categorized_columns:
                            categorized_columns[field_type] = []
                        if column not in categorized_columns[field_type]:
                            categorized_columns[field_type].append(column)
                        break
        
        return categorized_columns
    
    def find_best_hostname_column(self, columns: List[str]) -> Optional[str]:
        hostname_patterns = ['hostname', 'host_name', 'endpoint', 'computer', 'device', 'server', 'machine']
        
        exact_matches = []
        partial_matches = []
        
        for column in columns:
            column_lower = column.lower()
            
            for pattern in hostname_patterns:
                if pattern == column_lower:
                    exact_matches.append((column, 1.0))
                elif pattern in column_lower:
                    score = len(pattern) / len(column_lower)
                    partial_matches.append((column, score))
        
        if exact_matches:
            return max(exact_matches, key=lambda x: x[1])[0]
        elif partial_matches:
            return max(partial_matches, key=lambda x: x[1])[0]
        
        return None
    
    def extract_network_info(self, text: str) -> Dict[str, List[str]]:
        if not text:
            return {}
        
        text_str = str(text)
        network_info = {}
        
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, text_str)
        if ips:
            network_info['ip_addresses'] = list(set(ips))
        
        mac_pattern = r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
        macs = re.findall(mac_pattern, text_str)
        if macs:
            network_info['mac_addresses'] = list(set(macs))
        
        domain_pattern = r'\b[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, text_str)
        if domains:
            network_info['domains'] = list(set([d for d in domains if '.' in d and len(d) > 4]))
        
        return network_info
    
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
            
            if clean_column.startswith(clean_keyword) or clean_column.endswith(clean_keyword):
                score = len(clean_keyword) / len(clean_column)
                best_score = max(best_score, score)
        
        return best_score
    
    def _validate_sample_data(self, field_type: str, sample_values: List[str]) -> bool:
        if not sample_values or len(sample_values) < 2:
            return False
        
        valid_count = 0
        total_samples = min(len(sample_values), 10)
        
        for value in sample_values[:total_samples]:
            if not value:
                continue
            
            value_str = str(value).strip()
            if len(value_str) < 1:
                continue
            
            if field_type == 'endpoint':
                if self._looks_like_hostname(value_str):
                    valid_count += 1
            elif field_type == 'fqdn':
                if self._looks_like_fqdn(value_str):
                    valid_count += 1
            elif field_type == 'ip':
                if self._looks_like_ip(value_str):
                    valid_count += 1
            elif field_type == 'domain':
                if self._looks_like_domain(value_str):
                    valid_count += 1
            elif field_type == 'region':
                if self._looks_like_region(value_str):
                    valid_count += 1
            elif field_type == 'environment':
                if self._looks_like_environment(value_str):
                    valid_count += 1
            elif field_type in ['network', 'infrastructure', 'business', 'security']:
                if self._looks_like_categorical_text(value_str):
                    valid_count += 1
            else:
                if self._looks_like_general_text(value_str):
                    valid_count += 1
        
        threshold = 0.3 if total_samples >= 5 else 0.4
        return (valid_count / total_samples) >= threshold
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 253:
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t']):
            return False
        
        hostname_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$'
        ]
        
        if any(re.match(pattern, value) for pattern in hostname_patterns):
            return True
        
        common_patterns = ['srv', 'web', 'app', 'db', 'sql', 'prod', 'dev', 'test', 'win', 'linux', 'server']
        value_lower = value.lower()
        if any(pattern in value_lower for pattern in common_patterns):
            return True
        
        return False
    
    def _looks_like_fqdn(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 4:
            return False
        
        if value.count('.') < 1:
            return False
        
        fqdn_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'
        return bool(re.match(fqdn_pattern, value))
    
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
    
    def _looks_like_domain(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 4:
            return False
        
        if '.' not in value:
            return False
        
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'
        return bool(re.match(domain_pattern, value))
    
    def _looks_like_region(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 100:
            return False
        
        region_patterns = [
            r'^[a-zA-Z][a-zA-Z\s\-_]+$',
            r'^[A-Z]{2,4}[-_]?[A-Z]{2,4}[-_]?\d*$',
            r'^(us|eu|ap|ca|sa)[-_](east|west|central|north|south)[-_]?\d*$',
            r'^[A-Z]{2,3}\d*$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in region_patterns)
    
    def _looks_like_environment(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        env_values = ['prod', 'production', 'dev', 'development', 'test', 'testing', 
                     'stage', 'staging', 'qa', 'uat', 'sit', 'preprod', 'demo', 'sandbox']
        
        return value.lower() in env_values
    
    def _looks_like_categorical_text(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 200:
            return False
        
        if value.isdigit():
            return False
        
        return value.replace(' ', '').replace('-', '').replace('_', '').isalnum()
    
    def _looks_like_general_text(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 1 or len(value) > 500:
            return False
        
        return len(value.strip()) > 0