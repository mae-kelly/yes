#!/usr/bin/env python3

import re
import ipaddress
from typing import List, Optional, Tuple, Dict, Set
from collections import Counter
import statistics

class IntelligentContentMatcher:
    def __init__(self):
        self.semantic_patterns = {
            'hostname': {
                'keywords': ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system', 'workstation', 'name'],
                'validators': ['_validate_hostname'],
                'priority': 100
            },
            'fqdn': {
                'keywords': ['fqdn', 'dns', 'domain', 'qualified', 'full', 'canonical'],
                'validators': ['_validate_fqdn'],
                'priority': 95
            },
            'ip_address': {
                'keywords': ['ip', 'address', 'addr', 'ipaddr', 'inet'],
                'validators': ['_validate_ip'],
                'priority': 90
            },
            'mac_address': {
                'keywords': ['mac', 'ethernet', 'physical', 'hardware'],
                'validators': ['_validate_mac'],
                'priority': 85
            },
            'region': {
                'keywords': ['region', 'geo', 'location', 'site', 'area', 'zone', 'datacenter', 'center', 'country', 'locale'],
                'validators': ['_validate_region'],
                'priority': 80
            },
            'environment': {
                'keywords': ['env', 'environment', 'stage', 'tier', 'level'],
                'validators': ['_validate_environment'],
                'priority': 75
            },
            'operating_system': {
                'keywords': ['os', 'operating', 'platform', 'system'],
                'validators': ['_validate_os'],
                'priority': 70
            },
            'application': {
                'keywords': ['app', 'application', 'service', 'software', 'program'],
                'validators': ['_validate_application'],
                'priority': 65
            },
            'business_unit': {
                'keywords': ['business', 'unit', 'org', 'organization', 'department', 'team', 'division'],
                'validators': ['_validate_business_unit'],
                'priority': 60
            },
            'infrastructure_type': {
                'keywords': ['type', 'category', 'class', 'kind', 'classification', 'infra', 'infrastructure'],
                'validators': ['_validate_infrastructure'],
                'priority': 55
            },
            'status': {
                'keywords': ['status', 'state', 'active', 'enabled', 'online', 'condition'],
                'validators': ['_validate_status'],
                'priority': 50
            }
        }
        
        self.validation_cache = {}
        self.column_analysis_cache = {}
    
    def analyze_column_intelligently(self, column_name: str, sample_values: List[str]) -> Optional[Tuple[str, float, Dict[str, any]]]:
        cache_key = f"{column_name}:{hash(tuple(sample_values[:10]))}"
        if cache_key in self.column_analysis_cache:
            return self.column_analysis_cache[cache_key]
        
        if self._should_skip_column(column_name):
            self.column_analysis_cache[cache_key] = None
            return None
        
        cleaned_values = self._clean_sample_values(sample_values)
        if len(cleaned_values) < 2:
            self.column_analysis_cache[cache_key] = None
            return None
        
        best_match = None
        best_score = 0.0
        best_metadata = {}
        
        for field_type, config in self.semantic_patterns.items():
            semantic_score = self._calculate_semantic_score(column_name, config['keywords'])
            if semantic_score < 0.1:
                continue
            
            validation_score = self._validate_content_intelligently(field_type, cleaned_values, config['validators'])
            if validation_score < 0.3:
                continue
            
            combined_score = (semantic_score * 0.4) + (validation_score * 0.6)
            
            if combined_score > best_score:
                best_match = field_type
                best_score = combined_score
                best_metadata = {
                    'semantic_score': semantic_score,
                    'validation_score': validation_score,
                    'sample_analysis': self._analyze_sample_patterns(cleaned_values),
                    'data_quality': self._assess_data_quality(cleaned_values)
                }
        
        result = (best_match, best_score, best_metadata) if best_match else None
        self.column_analysis_cache[cache_key] = result
        return result
    
    def find_optimal_hostname_column(self, columns_with_samples: Dict[str, List[str]]) -> Optional[Tuple[str, float]]:
        candidates = []
        
        for column_name, samples in columns_with_samples.items():
            analysis = self.analyze_column_intelligently(column_name, samples)
            
            if analysis and analysis[0] in ['hostname', 'fqdn']:
                field_type, confidence, metadata = analysis
                
                hostname_specific_score = self._calculate_hostname_specificity(column_name, samples)
                
                final_score = confidence * hostname_specific_score
                candidates.append((column_name, final_score, metadata))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0], candidates[0][1]
    
    def extract_network_intelligence(self, text: str) -> Dict[str, List[str]]:
        if not text or len(str(text).strip()) < 3:
            return {}
        
        text_str = str(text).strip()
        network_info = {}
        
        ips = self._extract_ip_addresses(text_str)
        if ips:
            network_info['ip_addresses'] = ips
        
        macs = self._extract_mac_addresses(text_str)
        if macs:
            network_info['mac_addresses'] = macs
        
        domains = self._extract_domains(text_str)
        if domains:
            network_info['domains'] = domains
        
        hostnames = self._extract_hostnames(text_str)
        if hostnames:
            network_info['hostnames'] = hostnames
        
        return network_info
    
    def intelligently_categorize_all_columns(self, all_columns: List[str], sample_data: Dict[str, List[str]] = None) -> Dict[str, List[Tuple[str, float]]]:
        categorized = {}
        
        for column in all_columns:
            samples = sample_data.get(column, []) if sample_data else []
            analysis = self.analyze_column_intelligently(column, samples)
            
            if analysis:
                field_type, confidence, metadata = analysis
                
                if field_type not in categorized:
                    categorized[field_type] = []
                
                categorized[field_type].append((column, confidence))
        
        for field_type in categorized:
            categorized[field_type].sort(key=lambda x: x[1], reverse=True)
        
        return categorized
    
    def _should_skip_column(self, column_name: str) -> bool:
        skip_patterns = [
            r'\bid\b', r'\bkey\b', r'\bcount\b', r'\btotal\b', r'\bsum\b', r'\bavg\b',
            r'\bcreated\b', r'\bupdated\b', r'\bmodified\b', r'\bdeleted\b',
            r'\bflag\b', r'\bbool\b', r'\bindex\b', r'\border\b', r'\brank\b',
            r'\bversion\b', r'\btimestamp\b', r'\bdate\b', r'\btime\b'
        ]
        
        column_lower = column_name.lower()
        return any(re.search(pattern, column_lower) for pattern in skip_patterns)
    
    def _clean_sample_values(self, sample_values: List[str]) -> List[str]:
        cleaned = []
        for value in sample_values:
            if value is None:
                continue
            
            str_value = str(value).strip()
            if not str_value or str_value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY', '', 'NAN']:
                continue
            
            if len(str_value) > 0 and len(str_value) < 1000:
                cleaned.append(str_value)
        
        return cleaned[:50]
    
    def _calculate_semantic_score(self, column_name: str, keywords: List[str]) -> float:
        column_clean = re.sub(r'[_\-\s]', '', column_name.lower())
        
        best_score = 0.0
        
        for keyword in keywords:
            keyword_clean = re.sub(r'[_\-\s]', '', keyword.lower())
            
            if keyword_clean == column_clean:
                return 1.0
            
            if keyword_clean in column_clean:
                score = len(keyword_clean) / len(column_clean)
                best_score = max(best_score, score)
            
            if column_clean in keyword_clean and len(column_clean) >= 3:
                score = len(column_clean) / len(keyword_clean)
                best_score = max(best_score, score * 0.8)
            
            if column_clean.startswith(keyword_clean) or column_clean.endswith(keyword_clean):
                score = len(keyword_clean) / len(column_clean)
                best_score = max(best_score, score * 0.9)
        
        return min(best_score, 1.0)
    
    def _validate_content_intelligently(self, field_type: str, values: List[str], validators: List[str]) -> float:
        if not values:
            return 0.0
        
        valid_count = 0
        total_count = min(len(values), 20)
        
        for value in values[:total_count]:
            is_valid = False
            
            for validator_name in validators:
                validator_func = getattr(self, validator_name, None)
                if validator_func and validator_func(value):
                    is_valid = True
                    break
            
            if is_valid:
                valid_count += 1
        
        return valid_count / total_count if total_count > 0 else 0.0
    
    def _calculate_hostname_specificity(self, column_name: str, samples: List[str]) -> float:
        specificity_score = 1.0
        
        column_lower = column_name.lower()
        
        if 'hostname' in column_lower:
            specificity_score += 0.5
        elif 'host' in column_lower:
            specificity_score += 0.3
        elif 'endpoint' in column_lower:
            specificity_score += 0.3
        elif 'computer' in column_lower:
            specificity_score += 0.2
        
        hostname_like_count = sum(1 for sample in samples[:10] if self._validate_hostname(sample))
        if len(samples) > 0:
            hostname_ratio = hostname_like_count / min(len(samples), 10)
            specificity_score *= hostname_ratio
        
        return min(specificity_score, 2.0)
    
    def _analyze_sample_patterns(self, values: List[str]) -> Dict[str, any]:
        if not values:
            return {}
        
        lengths = [len(v) for v in values]
        
        patterns = {
            'avg_length': statistics.mean(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'unique_count': len(set(values)),
            'uniqueness_ratio': len(set(values)) / len(values),
            'common_prefixes': self._find_common_prefixes(values),
            'common_suffixes': self._find_common_suffixes(values),
            'contains_numbers': sum(1 for v in values if any(c.isdigit() for c in v)),
            'contains_special_chars': sum(1 for v in values if any(not c.isalnum() for c in v))
        }
        
        return patterns
    
    def _assess_data_quality(self, values: List[str]) -> Dict[str, any]:
        if not values:
            return {'score': 0.0}
        
        quality_metrics = {
            'completeness': len(values) / max(len(values), 1),
            'consistency': len(set(len(v) for v in values)) <= 3,
            'uniqueness': len(set(values)) / len(values),
            'validity': sum(1 for v in values if len(v.strip()) > 0) / len(values)
        }
        
        overall_score = sum(quality_metrics.values()) / len(quality_metrics)
        
        return {
            'score': overall_score,
            'metrics': quality_metrics
        }
    
    def _find_common_prefixes(self, values: List[str], min_length: int = 2) -> List[str]:
        if len(values) < 2:
            return []
        
        prefix_counts = Counter()
        
        for value in values:
            for i in range(min_length, min(len(value) + 1, 6)):
                prefix = value[:i]
                prefix_counts[prefix] += 1
        
        common_prefixes = [prefix for prefix, count in prefix_counts.items() 
                          if count >= max(2, len(values) * 0.3)]
        
        return sorted(common_prefixes, key=len, reverse=True)[:5]
    
    def _find_common_suffixes(self, values: List[str], min_length: int = 2) -> List[str]:
        if len(values) < 2:
            return []
        
        suffix_counts = Counter()
        
        for value in values:
            for i in range(min_length, min(len(value) + 1, 6)):
                suffix = value[-i:]
                suffix_counts[suffix] += 1
        
        common_suffixes = [suffix for suffix, count in suffix_counts.items() 
                          if count >= max(2, len(values) * 0.3)]
        
        return sorted(common_suffixes, key=len, reverse=True)[:5]
    
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
    
    def _validate_region(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 100:
            return False
        
        region_patterns = [
            r'^[a-zA-Z][a-zA-Z\s\-_]+$',
            r'^[A-Z]{2,4}[-_]?[A-Z]{2,4}[-_]?\d*$',
            r'^(us|eu|ap|ca|sa)[-_](east|west|central|north|south)[-_]?\d*$',
            r'^[A-Z]{2,3}\d*$'
        ]
        
        return any(re.match(pattern, value.strip(), re.IGNORECASE) for pattern in region_patterns)
    
    def _validate_environment(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        env_values = [
            'prod', 'production', 'dev', 'development', 'test', 'testing',
            'stage', 'staging', 'qa', 'uat', 'sit', 'preprod', 'demo', 'sandbox',
            'int', 'integration', 'perf', 'performance', 'load', 'stress'
        ]
        
        return value.lower().strip() in env_values
    
    def _validate_os(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 3:
            return False
        
        os_indicators = [
            'windows', 'linux', 'unix', 'macos', 'centos', 'ubuntu', 'redhat',
            'debian', 'suse', 'aix', 'solaris', 'freebsd', 'win', 'rhel'
        ]
        
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in os_indicators)
    
    def _validate_application(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 200:
            return False
        
        if value.isdigit():
            return False
        
        return len(value.strip()) > 1 and not value.strip().isspace()
    
    def _validate_business_unit(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 100:
            return False
        
        return value.replace(' ', '').replace('-', '').replace('_', '').isalnum()
    
    def _validate_infrastructure(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        infra_types = [
            'physical', 'virtual', 'cloud', 'container', 'vm', 'bare', 'metal',
            'aws', 'azure', 'gcp', 'vmware', 'hyper', 'kvm', 'xen', 'docker'
        ]
        
        value_lower = value.lower()
        return any(infra_type in value_lower for infra_type in infra_types)
    
    def _validate_status(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        status_values = [
            'active', 'inactive', 'enabled', 'disabled', 'online', 'offline',
            'running', 'stopped', 'up', 'down', 'healthy', 'unhealthy',
            'available', 'unavailable', 'ok', 'error', 'warning'
        ]
        
        return value.lower().strip() in status_values
    
    def _extract_ip_addresses(self, text: str) -> List[str]:
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        potential_ips = re.findall(ip_pattern, text)
        
        valid_ips = []
        for ip in potential_ips:
            try:
                ipaddress.ip_address(ip)
                valid_ips.append(ip)
            except (ValueError, ipaddress.AddressValueError):
                continue
        
        return list(set(valid_ips))
    
    def _extract_mac_addresses(self, text: str) -> List[str]:
        mac_patterns = [
            r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',
            r'\b(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}\b'
        ]
        
        macs = []
        for pattern in mac_patterns:
            macs.extend(re.findall(pattern, text))
        
        return list(set(macs))
    
    def _extract_domains(self, text: str) -> List[str]:
        domain_pattern = r'\b[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}\b'
        potential_domains = re.findall(domain_pattern, text)
        
        valid_domains = []
        for domain in potential_domains:
            if '.' in domain and len(domain) > 4 and not domain.replace('.', '').isdigit():
                valid_domains.append(domain.lower())
        
        return list(set(valid_domains))
    
    def _extract_hostnames(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]\b', text)
        
        hostnames = []
        for word in words:
            if self._validate_hostname(word) and len(word) >= 3:
                hostnames.append(word.upper())
        
        return list(set(hostnames))