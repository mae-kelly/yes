import re
import logging
import statistics
from typing import Dict, List, Tuple, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class DataPatternAnalyzer:
    def __init__(self):
        self.pattern_cache = {}
        self.learned_patterns = defaultdict(list)
        self.statistical_models = {}
    
    async def analyze_field_data(self, table_ref: Any, field_name: str, client: Any) -> Dict[str, Any]:
        cache_key = f"data_pattern_{table_ref.project}_{table_ref.dataset_id}_{table_ref.table_id}_{field_name}"
        cached_result = self.pattern_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            sample_query = f"""
            SELECT 
                {field_name},
                COUNT(*) as frequency
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            WHERE {field_name} IS NOT NULL
            GROUP BY {field_name}
            ORDER BY frequency DESC
            LIMIT 50
            """
            
            query_job = client.query(sample_query)
            results = list(query_job.result())
            
            if not results:
                return {'pattern_type': 'no_data', 'confidence_boost': 0.0}
            
            values = [(str(row[0]), row[1]) for row in results if row[0] is not None]
            
            if not values:
                return {'pattern_type': 'all_null', 'confidence_boost': 0.0}
            
            analysis = self._comprehensive_pattern_analysis(field_name, values)
            
            self.pattern_cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Data pattern analysis failed for {field_name}: {e}")
            return {'pattern_type': 'analysis_failed', 'confidence_boost': 0.0, 'error': str(e)}
    
    def _comprehensive_pattern_analysis(self, field_name: str, values: List[Tuple[str, int]]) -> Dict[str, Any]:
        field_values = [v[0] for v in values]
        frequencies = [v[1] for v in values]
        
        analysis = {
            'pattern_type': 'unknown',
            'confidence_boost': 0.0,
            'pattern_confidence': 0.0,
            'data_examples': field_values[:5],
            'pattern_indicators': [],
            'statistical_properties': {},
            'semantic_indicators': []
        }
        
        pattern_results = []
        
        format_result = self._detect_format_patterns(field_values)
        if format_result['confidence'] > 0.5:
            pattern_results.append(format_result)
        
        semantic_result = self._detect_semantic_patterns(field_name, field_values)
        if semantic_result['confidence'] > 0.4:
            pattern_results.append(semantic_result)
        
        statistical_result = self._detect_statistical_patterns(field_values, frequencies)
        if statistical_result['confidence'] > 0.3:
            pattern_results.append(statistical_result)
        
        domain_result = self._detect_domain_patterns(field_values)
        if domain_result['confidence'] > 0.4:
            pattern_results.append(domain_result)
        
        if pattern_results:
            best_pattern = max(pattern_results, key=lambda x: x['confidence'])
            analysis.update(best_pattern)
            
            if len(pattern_results) >= 2:
                analysis['confidence_boost'] += 0.1
                analysis['pattern_indicators'].append('multi_pattern_consensus')
        
        return analysis
    
    def _detect_format_patterns(self, values: List[str]) -> Dict[str, Any]:
        format_patterns = {
            'uuid': {
                'regex': r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
                'confidence_base': 0.9,
                'boost': 0.3
            },
            'asset_id': {
                'regex': r'^[A-Z]{2,6}\d{4,}$',
                'confidence_base': 0.8,
                'boost': 0.25
            },
            'hostname': {
                'regex': r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$',
                'confidence_base': 0.85,
                'boost': 0.2
            },
            'ip_address': {
                'regex': r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
                'confidence_base': 0.95,
                'boost': 0.2
            },
            'mac_address': {
                'regex': r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
                'confidence_base': 0.95,
                'boost': 0.2
            },
            'email': {
                'regex': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'confidence_base': 0.9,
                'boost': 0.15
            },
            'timestamp_iso': {
                'regex': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$',
                'confidence_base': 0.9,
                'boost': 0.15
            },
            'version_number': {
                'regex': r'^\d+\.\d+(\.\d+)?(\.\d+)?$',
                'confidence_base': 0.8,
                'boost': 0.1
            },
            'country_code': {
                'regex': r'^[A-Z]{2}$',
                'confidence_base': 0.7,
                'boost': 0.15
            },
            'serial_number': {
                'regex': r'^[A-Z0-9]{8,20}$',
                'confidence_base': 0.75,
                'boost': 0.2
            }
        }
        
        best_match = {'pattern_type': 'unknown', 'confidence': 0.0, 'confidence_boost': 0.0}
        
        for pattern_name, pattern_info in format_patterns.items():
            matches = sum(1 for value in values if re.match(pattern_info['regex'], value, re.IGNORECASE))
            match_ratio = matches / len(values) if values else 0
            
            if match_ratio >= 0.7:
                confidence = pattern_info['confidence_base'] * match_ratio
                if confidence > best_match['confidence']:
                    best_match = {
                        'pattern_type': pattern_name,
                        'confidence': confidence,
                        'confidence_boost': pattern_info['boost'] * match_ratio,
                        'pattern_indicators': [f'format_match_{pattern_name}'],
                        'match_ratio': match_ratio
                    }
        
        return best_match
    
    def _detect_semantic_patterns(self, field_name: str, values: List[str]) -> Dict[str, Any]:
        field_lower = field_name.lower()
        
        semantic_patterns = {
            'security_status': {
                'keywords': ['installed', 'enabled', 'active', 'disabled', 'running', 'stopped', 'protected'],
                'confidence_base': 0.8,
                'boost': 0.2
            },
            'infrastructure_type': {
                'keywords': ['cloud', 'aws', 'azure', 'gcp', 'onprem', 'physical', 'virtual', 'container'],
                'confidence_base': 0.75,
                'boost': 0.18
            },
            'operating_system': {
                'keywords': ['windows', 'linux', 'macos', 'ubuntu', 'centos', 'rhel', 'debian'],
                'confidence_base': 0.8,
                'boost': 0.2
            },
            'business_department': {
                'keywords': ['finance', 'hr', 'it', 'sales', 'marketing', 'ops', 'legal', 'engineering'],
                'confidence_base': 0.7,
                'boost': 0.15
            },
            'geographic_region': {
                'keywords': ['us', 'eu', 'asia', 'americas', 'emea', 'apac', 'east', 'west', 'north', 'south'],
                'confidence_base': 0.75,
                'boost': 0.18
            },
            'log_source': {
                'keywords': ['splunk', 'chronicle', 'syslog', 'eventlog', 'audit', 'security'],
                'confidence_base': 0.8,
                'boost': 0.2
            }
        }
        
        best_match = {'pattern_type': 'unknown', 'confidence': 0.0, 'confidence_boost': 0.0}
        
        for pattern_name, pattern_info in semantic_patterns.items():
            field_relevance = sum(1 for keyword in pattern_info['keywords'] if keyword in field_lower)
            field_relevance_score = field_relevance / len(pattern_info['keywords'])
            
            value_matches = 0
            for value in values:
                value_lower = value.lower()
                if any(keyword in value_lower for keyword in pattern_info['keywords']):
                    value_matches += 1
            
            value_relevance_score = value_matches / len(values) if values else 0
            
            combined_relevance = (field_relevance_score * 0.4) + (value_relevance_score * 0.6)
            
            if combined_relevance >= 0.3:
                confidence = pattern_info['confidence_base'] * combined_relevance
                if confidence > best_match['confidence']:
                    best_match = {
                        'pattern_type': f'semantic_{pattern_name}',
                        'confidence': confidence,
                        'confidence_boost': pattern_info['boost'] * combined_relevance,
                        'pattern_indicators': [f'semantic_match_{pattern_name}'],
                        'field_relevance': field_relevance_score,
                        'value_relevance': value_relevance_score
                    }
        
        return best_match
    
    def _detect_statistical_patterns(self, values: List[str], frequencies: List[int]) -> Dict[str, Any]:
        if not values or not frequencies:
            return {'pattern_type': 'unknown', 'confidence': 0.0, 'confidence_boost': 0.0}
        
        total_count = sum(frequencies)
        unique_count = len(values)
        
        cardinality_ratio = unique_count / total_count if total_count > 0 else 0
        frequency_variance = statistics.variance(frequencies) if len(frequencies) > 1 else 0
        max_frequency = max(frequencies)
        frequency_concentration = max_frequency / total_count if total_count > 0 else 0
        
        statistical_patterns = {
            'high_cardinality_identifier': {
                'condition': cardinality_ratio > 0.8 and unique_count > 100,
                'confidence_base': 0.8,
                'boost': 0.25
            },
            'categorical_enum': {
                'condition': unique_count <= 20 and frequency_concentration < 0.8,
                'confidence_base': 0.75,
                'boost': 0.15
            },
            'dominant_value_flag': {
                'condition': frequency_concentration > 0.9 and unique_count <= 5,
                'confidence_base': 0.7,
                'boost': 0.1
            },
            'distributed_categorical': {
                'condition': 5 < unique_count <= 50 and 0.1 < frequency_concentration < 0.5,
                'confidence_base': 0.6,
                'boost': 0.12
            },
            'sparse_identifier': {
                'condition': cardinality_ratio > 0.5 and frequency_variance > total_count * 0.1,
                'confidence_base': 0.65,
                'boost': 0.18
            }
        }
        
        best_match = {'pattern_type': 'unknown', 'confidence': 0.0, 'confidence_boost': 0.0}
        
        for pattern_name, pattern_info in statistical_patterns.items():
            if pattern_info['condition']:
                confidence = pattern_info['confidence_base']
                boost = pattern_info['boost']
                
                if confidence > best_match['confidence']:
                    best_match = {
                        'pattern_type': f'statistical_{pattern_name}',
                        'confidence': confidence,
                        'confidence_boost': boost,
                        'pattern_indicators': [f'statistical_{pattern_name}'],
                        'statistical_properties': {
                            'cardinality_ratio': cardinality_ratio,
                            'unique_count': unique_count,
                            'frequency_concentration': frequency_concentration,
                            'total_records': total_count
                        }
                    }
        
        return best_match
    
    def _detect_domain_patterns(self, values: List[str]) -> Dict[str, Any]:
        domain_patterns = {
            'security_tool_agent': {
                'indicators': ['crowdstrike', 'falcon', 'sentinelone', 'tanium', 'carbon_black', 'defender'],
                'confidence_base': 0.9,
                'boost': 0.3
            },
            'cloud_provider': {
                'indicators': ['aws', 'azure', 'gcp', 'amazon', 'microsoft', 'google'],
                'confidence_base': 0.85,
                'boost': 0.25
            },
            'log_platform': {
                'indicators': ['splunk', 'chronicle', 'elastic', 'logstash', 'graylog', 'datadog'],
                'confidence_base': 0.8,
                'boost': 0.2
            },
            'vulnerability_scanner': {
                'indicators': ['nessus', 'qualys', 'rapid7', 'openvas', 'nexpose'],
                'confidence_base': 0.85,
                'boost': 0.22
            },
            'network_device': {
                'indicators': ['cisco', 'juniper', 'fortinet', 'palo', 'checkpoint', 'firewall'],
                'confidence_base': 0.8,
                'boost': 0.18
            },
            'compliance_framework': {
                'indicators': ['sox', 'pci', 'hipaa', 'gdpr', 'iso27001', 'nist'],
                'confidence_base': 0.75,
                'boost': 0.15
            }
        }
        
        best_match = {'pattern_type': 'unknown', 'confidence': 0.0, 'confidence_boost': 0.0}
        
        for pattern_name, pattern_info in domain_patterns.items():
            matches = 0
            for value in values:
                value_lower = value.lower()
                if any(indicator in value_lower for indicator in pattern_info['indicators']):
                    matches += 1
            
            match_ratio = matches / len(values) if values else 0
            
            if match_ratio >= 0.2:
                confidence = pattern_info['confidence_base'] * match_ratio
                boost = pattern_info['boost'] * match_ratio
                
                if confidence > best_match['confidence']:
                    best_match = {
                        'pattern_type': f'domain_{pattern_name}',
                        'confidence': confidence,
                        'confidence_boost': boost,
                        'pattern_indicators': [f'domain_{pattern_name}'],
                        'match_ratio': match_ratio,
                        'matched_indicators': [ind for ind in pattern_info['indicators'] 
                                             if any(ind in v.lower() for v in values)]
                    }
        
        return best_match