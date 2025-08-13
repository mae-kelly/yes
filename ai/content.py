# ai/content.py

import re
import ipaddress
import statistics
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
import hashlib

class ContentAnalyzer:
    def __init__(self):
        self.field_patterns = {
            'hostname': [
                r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
                r'^[a-zA-Z0-9]+$'
            ],
            'ip_address': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
            'fqdn': [r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'],
            'mac_address': [
                r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$',
                r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$'
            ]
        }
        
        self.semantic_indicators = {
            'hostname': ['host', 'server', 'endpoint', 'computer', 'device', 'machine'],
            'infrastructure': ['cloud', 'onprem', 'saas', 'api', 'physical', 'virtual'],
            'system': ['windows', 'linux', 'unix', 'database', 'web', 'mainframe'],
            'region': ['us', 'eu', 'apac', 'americas', 'emea', 'global'],
            'business': ['finance', 'marketing', 'sales', 'hr', 'operations'],
            'security': ['edr', 'dlp', 'firewall', 'vpn', 'auth', 'security']
        }
        
        self.cache = {}
    
    def analyze_column(self, name: str, values: List[str], context: Dict = None) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        cache_key = f"{name}:{hash(tuple(values[:10]))}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self._should_skip(name):
            return None
        
        clean_values = self._clean_values(values)
        if len(clean_values) < 2:
            return None
        
        scores = {}
        for field_type in self.field_patterns.keys():
            score = self._score_field_type(name, clean_values, field_type)
            if score > 0.3:
                scores[field_type] = score
        
        semantic_scores = self._analyze_semantics(name, clean_values)
        for field_type, score in semantic_scores.items():
            if score > 0.3:
                scores[field_type] = max(scores.get(field_type, 0), score)
        
        if not scores:
            return None
        
        best_type = max(scores.items(), key=lambda x: x[1])
        field_type, confidence = best_type
        
        metadata = {
            'pattern_score': self._pattern_score(clean_values, field_type),
            'semantic_score': semantic_scores.get(field_type, 0),
            'quality_score': self._quality_score(clean_values),
            'sample_analysis': self._analyze_samples(clean_values),
            'all_scores': scores
        }
        
        result = (field_type, confidence, metadata)
        self.cache[cache_key] = result
        return result
    
    def _should_skip(self, name: str) -> bool:
        skip_patterns = [
            r'\bid\b', r'\bkey\b', r'\bcount\b', r'\btotal\b', r'\bsum\b',
            r'\bcreated\b', r'\bupdated\b', r'\bmodified\b', r'\bdeleted\b',
            r'\bflag\b', r'\bbool\b', r'\bindex\b', r'\border\b', r'\brank\b',
            r'\bversion\b', r'\btimestamp\b', r'\bdate\b', r'\btime\b'
        ]
        
        name_lower = name.lower()
        return any(re.search(pattern, name_lower) for pattern in skip_patterns)
    
    def _clean_values(self, values: List[str]) -> List[str]:
        cleaned = []
        for value in values:
            if value is None:
                continue
            
            str_value = str(value).strip()
            if not str_value or str_value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
                continue
            
            if 0 < len(str_value) < 1000:
                cleaned.append(str_value)
        
        return cleaned[:50]
    
    def _score_field_type(self, name: str, values: List[str], field_type: str) -> float:
        name_score = self._score_name(name, field_type)
        pattern_score = self._pattern_score(values, field_type)
        
        return (name_score * 0.4) + (pattern_score * 0.6)
    
    def _score_name(self, name: str, field_type: str) -> float:
        name_clean = re.sub(r'[_\-\s]', '', name.lower())
        
        field_keywords = {
            'hostname': ['host', 'hostname', 'computer', 'endpoint', 'device', 'server', 'machine'],
            'ip_address': ['ip', 'ipaddr', 'address', 'addr', 'inet'],
            'fqdn': ['fqdn', 'dns', 'domain', 'qualified', 'canonical'],
            'mac_address': ['mac', 'ethernet', 'physical', 'hardware']
        }
        
        keywords = field_keywords.get(field_type, [])
        best_score = 0.0
        
        for keyword in keywords:
            keyword_clean = re.sub(r'[_\-\s]', '', keyword.lower())
            
            if keyword_clean == name_clean:
                return 1.0
            
            if keyword_clean in name_clean:
                score = len(keyword_clean) / len(name_clean)
                best_score = max(best_score, score)
            
            if name_clean in keyword_clean and len(name_clean) >= 3:
                score = len(name_clean) / len(keyword_clean) * 0.8
                best_score = max(best_score, score)
        
        return best_score
    
    def _pattern_score(self, values: List[str], field_type: str) -> float:
        if field_type not in self.field_patterns:
            return 0.0
        
        patterns = self.field_patterns[field_type]
        match_count = 0
        
        for value in values[:20]:
            for pattern in patterns:
                if re.match(pattern, value):
                    match_count += 1
                    break
        
        return match_count / min(len(values), 20) if values else 0.0
    
    def _analyze_semantics(self, name: str, values: List[str]) -> Dict[str, float]:
        scores = {}
        
        name_lower = name.lower()
        sample_text = ' '.join(values[:10]).lower()
        
        for field_category, indicators in self.semantic_indicators.items():
            name_matches = sum(1 for indicator in indicators if indicator in name_lower)
            value_matches = sum(1 for indicator in indicators if indicator in sample_text)
            
            if name_matches > 0 or value_matches > 0:
                name_score = name_matches / len(indicators)
                value_score = value_matches / (len(indicators) * len(values[:10]))
                scores[field_category] = (name_score * 0.7) + (value_score * 0.3)
        
        return scores
    
    def _quality_score(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        unique_ratio = len(set(values)) / len(values)
        avg_length = statistics.mean([len(v) for v in values])
        
        non_empty = sum(1 for v in values if v.strip())
        completeness = non_empty / len(values)
        
        length_consistency = 1.0 - (statistics.stdev([len(v) for v in values]) / max(avg_length, 1))
        length_consistency = max(0.0, length_consistency)
        
        return (unique_ratio * 0.3) + (completeness * 0.4) + (length_consistency * 0.3)
    
    def _analyze_samples(self, values: List[str]) -> Dict[str, Any]:
        if not values:
            return {}
        
        lengths = [len(v) for v in values]
        
        return {
            'count': len(values),
            'unique_count': len(set(values)),
            'uniqueness_ratio': len(set(values)) / len(values),
            'avg_length': statistics.mean(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'length_variance': statistics.variance(lengths) if len(lengths) > 1 else 0,
            'has_numbers': sum(1 for v in values if any(c.isdigit() for c in v)),
            'has_special': sum(1 for v in values if any(not c.isalnum() for c in v)),
            'common_prefixes': self._find_common_prefixes(values),
            'common_suffixes': self._find_common_suffixes(values)
        }
    
    def _find_common_prefixes(self, values: List[str], min_length: int = 2) -> List[str]:
        if len(values) < 2:
            return []
        
        prefix_counts = Counter()
        for value in values:
            for i in range(min_length, min(len(value) + 1, 6)):
                prefix = value[:i]
                prefix_counts[prefix] += 1
        
        threshold = max(2, len(values) * 0.3)
        common = [prefix for prefix, count in prefix_counts.items() if count >= threshold]
        return sorted(common, key=len, reverse=True)[:5]
    
    def _find_common_suffixes(self, values: List[str], min_length: int = 2) -> List[str]:
        if len(values) < 2:
            return []
        
        suffix_counts = Counter()
        for value in values:
            for i in range(min_length, min(len(value) + 1, 6)):
                suffix = value[-i:]
                suffix_counts[suffix] += 1
        
        threshold = max(2, len(values) * 0.3)
        common = [suffix for suffix, count in suffix_counts.items() if count >= threshold]
        return sorted(common, key=len, reverse=True)[:5]

class ValidationEngine:
    def __init__(self):
        self.validators = {
            'hostname': self._validate_hostname,
            'ip_address': self._validate_ip,
            'fqdn': self._validate_fqdn,
            'mac_address': self._validate_mac
        }
    
    def validate_field(self, field_type: str, values: List[str]) -> float:
        validator = self.validators.get(field_type)
        if not validator:
            return 0.5
        
        valid_count = sum(1 for value in values[:20] if validator(value))
        return valid_count / min(len(values), 20) if values else 0.0
    
    def _validate_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)
    
    def _validate_ip(self, value: str) -> bool:
        try:
            ipaddress.ip_address(value.strip())
            return True
        except:
            return False
    
    def _validate_fqdn(self, value: str) -> bool:
        if not isinstance(value, str) or not (4 <= len(value) <= 253):
            return False
        
        if value.count('.') < 1:
            return False
        
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value, re.IGNORECASE))
    
    def _validate_mac(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$',
            r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$'
        ]
        
        return any(re.match(pattern, value.strip()) for pattern in patterns)