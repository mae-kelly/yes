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
            'infrastructure_type': {
                'keywords': ['type', 'infra', 'infrastructure', 'platform', 'onprem', 'cloud', 'saas', 'api'],
                'validators': ['_validate_infrastructure_type'],
                'priority': 95
            },
            'system_classification': {
                'keywords': ['classification', 'category', 'class', 'webserver', 'windows', 'linux', 'nix', 'mainframe', 'database', 'appliance'],
                'validators': ['_validate_system_classification'],
                'priority': 90
            },
            'global_region': {
                'keywords': ['region', 'global_region', 'location', 'geo', 'area'],
                'validators': ['_validate_global_region'],
                'priority': 85
            },
            'country': {
                'keywords': ['country', 'nation', 'countrycode', 'cc'],
                'validators': ['_validate_country'],
                'priority': 80
            },
            'data_center': {
                'keywords': ['datacenter', 'dc', 'facility', 'site'],
                'validators': ['_validate_data_center'],
                'priority': 75
            },
            'cloud_region': {
                'keywords': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
                'validators': ['_validate_cloud_region'],
                'priority': 80
            },
            'business_unit': {
                'keywords': ['business_unit', 'bu', 'org', 'organization', 'department'],
                'validators': ['_validate_business_unit'],
                'priority': 70
            },
            'cio': {
                'keywords': ['cio', 'chief_information_officer'],
                'validators': ['_validate_cio'],
                'priority': 65
            },
            'apm': {
                'keywords': ['apm', 'application_performance_monitoring'],
                'validators': ['_validate_apm'],
                'priority': 60
            },
            'application_class': {
                'keywords': ['application_class', 'app_class', 'application_type'],
                'validators': ['_validate_application_class'],
                'priority': 65
            },
            'edr_coverage': {
                'keywords': ['edr', 'endpoint_detection', 'crowdstrike', 'defender'],
                'validators': ['_validate_coverage'],
                'priority': 85
            },
            'tanium_coverage': {
                'keywords': ['tanium', 'tanium_agent'],
                'validators': ['_validate_coverage'],
                'priority': 80
            },
            'dlp_coverage': {
                'keywords': ['dlp', 'data_loss_prevention'],
                'validators': ['_validate_coverage'],
                'priority': 80
            },
            'network_log_types': {
                'keywords': ['firewall', 'ids', 'ips', 'ndr', 'proxy', 'dns', 'waf'],
                'validators': ['_validate_log_types'],
                'priority': 90
            },
            'endpoint_log_types': {
                'keywords': ['oslog', 'winlog', 'syslog', 'edr_log', 'dlp_log', 'fim'],
                'validators': ['_validate_log_types'],
                'priority': 90
            },
            'cloud_log_types': {
                'keywords': ['cloudtrail', 'cloudconfig', 'cloudlb', 'theom', 'wiz'],
                'validators': ['_validate_log_types'],
                'priority': 85
            },
            'application_log_types': {
                'keywords': ['weblog', 'applog', 'api_gateway'],
                'validators': ['_validate_log_types'],
                'priority': 80
            },
            'identity_log_types': {
                'keywords': ['auth', 'identity', 'authentication', 'privilege'],
                'validators': ['_validate_log_types'],
                'priority': 85
            },
            'url_fqdn_coverage': {
                'keywords': ['url', 'fqdn', 'domain', 'dns_name'],
                'validators': ['_validate_coverage'],
                'priority': 75
            },
            'public_ip_coverage': {
                'keywords': ['public_ip', 'external_ip', 'wan_ip'],
                'validators': ['_validate_coverage'],
                'priority': 70
            },
            'cmdb_asset_visibility': {
                'keywords': ['cmdb', 'asset_db', 'inventory'],
                'validators': ['_validate_coverage'],
                'priority': 85
            },
            'network_zones': {
                'keywords': ['zone', 'network_zone', 'security_zone', 'vlan'],
                'validators': ['_validate_network_zones'],
                'priority': 70
            },
            'ipam_coverage': {
                'keywords': ['ipam', 'ip_management', 'subnet'],
                'validators': ['_validate_coverage'],
                'priority': 70
            },
            'geolocation': {
                'keywords': ['geo', 'location', 'physical_location'],
                'validators': ['_validate_geolocation'],
                'priority': 65
            },
            'vpc': {
                'keywords': ['vpc', 'virtual_private_cloud', 'vnet'],
                'validators': ['_validate_vpc'],
                'priority': 70
            },
            'domain_visibility': {
                'keywords': ['domain', 'ad_domain', 'dns_domain'],
                'validators': ['_validate_domain_visibility'],
                'priority': 75
            },
            'internal_external': {
                'keywords': ['internal', 'external', 'dmz'],
                'validators': ['_validate_internal_external'],
                'priority': 70
            },
            'controls': {
                'keywords': ['control', 'security_control', 'compliance'],
                'validators': ['_validate_controls'],
                'priority': 65
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