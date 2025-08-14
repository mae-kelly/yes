import re
import statistics
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
import hashlib

class QuantumContentAnalyzer:
    def __init__(self):
        self.domain_ontology = {
            'cybersecurity_indicators': {
                'endpoint_identifiers': [
                    'hostname', 'host', 'computer', 'machine', 'device', 'endpoint', 'asset',
                    'workstation', 'server', 'node', 'system', 'equipment', 'appliance'
                ],
                'network_identifiers': [
                    'ip', 'address', 'network', 'subnet', 'domain', 'fqdn', 'dns',
                    'ipv4', 'ipv6', 'cidr', 'gateway', 'router', 'switch', 'firewall'
                ],
                'security_tools': [
                    'edr', 'dlp', 'siem', 'soar', 'ids', 'ips', 'waf', 'xdr', 'ndr'
                ]
            },
            'pattern_signatures': {
                'hostname_patterns': [
                    r'^[a-zA-Z][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]$',
                    r'^[a-zA-Z0-9]+$'
                ],
                'ip_patterns': [
                    r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
                ]
            }
        }
        
        self.pattern_quantum_library = self._build_quantum_pattern_library()
        self.semantic_quantum_cache = {}
        
    def _build_quantum_pattern_library(self):
        return {
            'hostname': {
                'quantum_strict': self.domain_ontology['pattern_signatures']['hostname_patterns'],
                'quantum_indicators': self.domain_ontology['cybersecurity_indicators']['endpoint_identifiers']
            },
            'ip_address': {
                'quantum_strict': self.domain_ontology['pattern_signatures']['ip_patterns'],
                'quantum_indicators': ['ip', 'addr', 'address', 'network', 'subnet']
            }
        }

    def analyze_column_quantum_intelligently(self, name: str, values: List[str], 
                                           context: Dict = None) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        if self._should_skip_quantum_column(name):
            return None
        
        quantum_cleaned_values = self._quantum_intelligent_cleaning(values)
        if len(quantum_cleaned_values) < 2:
            return None
        
        cache_key = self._generate_quantum_cache_key(name, quantum_cleaned_values[:15])
        if cache_key in self.semantic_quantum_cache:
            return self.semantic_quantum_cache[cache_key]
        
        if self._is_likely_hostname_column(name, quantum_cleaned_values):
            return ('hostname', 0.95, {
                'method': 'pattern_match', 
                'confidence': 0.95,
                'quantum_enhanced': True
            })
        
        quantum_analysis = self._analyze_with_patterns(name, quantum_cleaned_values, context)
        
        if quantum_analysis:
            result = quantum_analysis
            self.semantic_quantum_cache[cache_key] = result
            return result
            
        return self._enhanced_fallback_analysis(name, values)
    
    def _is_likely_hostname_column(self, name: str, values: List[str]) -> bool:
        name_lower = name.lower()
        hostname_indicators = ['hostname', 'host', 'computername', 'endpoint', 'device', 'machine', 'computer']
        
        for indicator in hostname_indicators:
            if indicator in name_lower:
                return True
        
        if not values:
            return False
        
        hostname_count = 0
        for value in values[:20]:
            if self._looks_like_hostname(str(value)):
                hostname_count += 1
        
        return (hostname_count / min(len(values), 20)) > 0.7
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', value, re.IGNORECASE))
    
    def _analyze_with_patterns(self, name: str, values: List[str], context: Dict) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        best_match = None
        best_confidence = 0.0
        
        for field_type, patterns in self.pattern_quantum_library.items():
            confidence = self._calculate_pattern_confidence(values, patterns)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = field_type
        
        if best_match and best_confidence > 0.6:
            return (best_match, best_confidence, {
                'method': 'quantum_pattern', 
                'confidence': best_confidence,
                'pattern_matches': True
            })
        
        return None
    
    def _calculate_pattern_confidence(self, values: List[str], patterns: Dict) -> float:
        if not values or not patterns:
            return 0.0
        
        strict_patterns = patterns.get('quantum_strict', [])
        if not strict_patterns:
            return 0.0
            
        matches = 0
        
        for value in values[:30]:
            for pattern in strict_patterns:
                try:
                    if re.match(pattern, str(value), re.IGNORECASE):
                        matches += 1
                        break
                except:
                    continue
        
        return matches / min(len(values), 30)
    
    def _enhanced_fallback_analysis(self, name: str, values: List[str]) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        name_lower = name.lower()
        
        for field_type, patterns in self.pattern_quantum_library.items():
            indicators = patterns.get('quantum_indicators', [])
            
            for indicator in indicators:
                if indicator in name_lower:
                    confidence = 0.7 + (len(indicator) / len(name_lower)) * 0.2
                    return (field_type, min(0.95, confidence), {
                        'method': 'enhanced_fallback',
                        'matched_indicator': indicator,
                        'field_type': field_type
                    })
        
        return None
    
    def _should_skip_quantum_column(self, name: str) -> bool:
        skip_patterns = [
            r'\bid\b', r'\bkey\b', r'\bcount\b', r'\btotal\b', r'\bsum\b', r'\bavg\b',
            r'\bcreated\b', r'\bupdated\b', r'\bmodified\b', r'\bdeleted\b', r'\btimestamp\b',
            r'\bflag\b', r'\bbool\b', r'\bindex\b', r'\border\b', r'\brank\b', r'\bscore\b',
            r'\bversion\b', r'\bdate\b', r'\btime\b', r'\byear\b', r'\bmonth\b', r'\bday\b'
        ]
        name_lower = name.lower()
        return any(re.search(pattern, name_lower) for pattern in skip_patterns)
    
    def _quantum_intelligent_cleaning(self, values: List[str]) -> List[str]:
        cleaned = []
        for value in values:
            if value is None:
                continue
            str_value = str(value).strip()
            if (str_value and 
                str_value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '', '-', 'NA', 'NIL'] and
                len(str_value) <= 2000):
                cleaned.append(str_value)
        return list(set(cleaned))[:150]
    
    def _generate_quantum_cache_key(self, name: str, values: List[str]) -> str:
        content = f"{name}:{':'.join(str(v) for v in values)}"
        return hashlib.sha256(content.encode()).hexdigest()[:24]
    
    def analyze_column(self, name: str, values: List[str], context: Dict = None):
        return self.analyze_column_quantum_intelligently(name, values, context)

AdvancedContentAnalyzer = QuantumContentAnalyzer
ContentAnalyzer = QuantumContentAnalyzer