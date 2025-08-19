# advanced_column_classifier.py

import re
import statistics
import math
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import numpy as np

class AdvancedColumnClassifier:
    
    def __init__(self):
        self.field_type_patterns = self._initialize_field_patterns()
        self.value_validators = self._initialize_validators()
        self.semantic_embeddings = self._initialize_semantic_embeddings()
        self.classification_cache = {}
        
    def _initialize_field_patterns(self) -> Dict[str, Dict[str, Any]]:
        return {
            'infrastructure_type': {
                'name_indicators': ['infrastructure', 'platform', 'hosting', 'deployment', 'cloud', 'environment'],
                'value_patterns': {
                    'on_prem': ['on_prem', 'datacenter', 'physical', 'bare_metal', 'on_premise', 'local'],
                    'cloud': ['aws', 'azure', 'gcp', 'cloud', 'ec2', 'virtual', 'vm', 'iaas', 'paas'],
                    'saas': ['saas', 'software_as_service', 'hosted', 'managed'],
                    'api': ['api', 'service', 'endpoint', 'gateway', 'rest', 'soap']
                },
                'statistical_profile': {'unique_ratio_range': (0.1, 0.8), 'avg_length_range': (3, 20)}
            },
            'system_classification': {
                'name_indicators': ['os', 'operating', 'system', 'platform', 'classification', 'type'],
                'value_patterns': {
                    'windows': ['windows', 'win', 'microsoft', 'nt', 'server_2019', 'server_2016'],
                    'linux': ['linux', 'ubuntu', 'centos', 'rhel', 'redhat', 'debian', 'suse'],
                    'unix': ['unix', 'aix', 'solaris', 'hpux', 'bsd'],
                    'web_server': ['apache', 'nginx', 'iis', 'tomcat', 'web', 'http'],
                    'database': ['sql', 'oracle', 'mysql', 'postgres', 'db2', 'mongodb'],
                    'network': ['firewall', 'router', 'switch', 'proxy', 'load_balancer']
                },
                'statistical_profile': {'unique_ratio_range': (0.05, 0.5), 'avg_length_range': (3, 30)}
            },
            'business_unit': {
                'name_indicators': ['business', 'department', 'bu', 'org', 'division', 'team'],
                'value_patterns': {
                    'finance': ['finance', 'accounting', 'treasury', 'billing'],
                    'hr': ['hr', 'human_resources', 'people', 'talent'],
                    'it': ['it', 'technology', 'engineering', 'development'],
                    'sales': ['sales', 'revenue', 'commercial', 'business_development'],
                    'operations': ['operations', 'ops', 'support', 'infrastructure']
                },
                'statistical_profile': {'unique_ratio_range': (0.01, 0.3), 'avg_length_range': (2, 25)}
            },
            'global_region': {
                'name_indicators': ['region', 'location', 'geography', 'area', 'zone'],
                'value_patterns': {
                    'north_america': ['north_america', 'na', 'us', 'usa', 'canada', 'america'],
                    'europe': ['europe', 'eu', 'emea', 'uk', 'germany', 'france'],
                    'asia_pacific': ['asia', 'apac', 'japan', 'china', 'australia', 'singapore'],
                    'latin_america': ['latam', 'brazil', 'mexico', 'south_america']
                },
                'statistical_profile': {'unique_ratio_range': (0.01, 0.2), 'avg_length_range': (2, 20)}
            },
            'country': {
                'name_indicators': ['country', 'nation', 'territory'],
                'value_patterns': {
                    'iso_codes': ['us', 'uk', 'de', 'fr', 'jp', 'au', 'ca', 'br'],
                    'full_names': ['united_states', 'united_kingdom', 'germany', 'france', 'japan']
                },
                'statistical_profile': {'unique_ratio_range': (0.01, 0.1), 'avg_length_range': (2, 25)}
            },
            'datacenter': {
                'name_indicators': ['datacenter', 'dc', 'site', 'facility', 'location'],
                'value_patterns': {
                    'dc_codes': ['dc01', 'dc_ny', 'site_a', 'facility_west'],
                    'locations': ['new_york', 'london', 'singapore', 'sydney']
                },
                'statistical_profile': {'unique_ratio_range': (0.01, 0.3), 'avg_length_range': (3, 20)}
            },
            'application_class': {
                'name_indicators': ['application', 'app', 'service', 'workload', 'tier'],
                'value_patterns': {
                    'web': ['web', 'frontend', 'ui', 'portal'],
                    'database': ['database', 'db', 'data', 'storage'],
                    'middleware': ['middleware', 'integration', 'messaging'],
                    'security': ['security', 'auth', 'identity', 'firewall']
                },
                'statistical_profile': {'unique_ratio_range': (0.05, 0.4), 'avg_length_range': (3, 25)}
            },
            'domain': {
                'name_indicators': ['domain', 'dns', 'realm'],
                'value_patterns': {
                    'active_directory': ['corp.local', 'internal.com', 'ad.company'],
                    'dns_domains': ['.com', '.local', '.internal', '.corp']
                },
                'statistical_profile': {'unique_ratio_range': (0.01, 0.2), 'avg_length_range': (5, 50)}
            },
            'fqdn': {
                'name_indicators': ['fqdn', 'fully_qualified', 'dns_name'],
                'value_patterns': {
                    'fqdn_format': [r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$']
                },
                'statistical_profile': {'unique_ratio_range': (0.8, 1.0), 'avg_length_range': (10, 100)}
            },
            'ip_address': {
                'name_indicators': ['ip', 'address', 'addr'],
                'value_patterns': {
                    'ipv4': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
                    'ipv6': [r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$']
                },
                'statistical_profile': {'unique_ratio_range': (0.1, 1.0), 'avg_length_range': (7, 40)}
            },
            'mac_address': {
                'name_indicators': ['mac', 'physical', 'ethernet', 'hardware'],
                'value_patterns': {
                    'mac_colon': [r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'],
                    'mac_dash': [r'^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$'],
                    'mac_dot': [r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$']
                },
                'statistical_profile': {'unique_ratio_range': (0.8, 1.0), 'avg_length_range': (12, 18)}
            }
        }
    
    def _initialize_validators(self) -> Dict[str, callable]:
        return {
            'ip_address': self._validate_ip,
            'mac_address': self._validate_mac,
            'fqdn': self._validate_fqdn,
            'domain': self._validate_domain
        }
    
    def _initialize_semantic_embeddings(self) -> Dict[str, List[str]]:
        return {
            'infrastructure_semantic': [
                'cloud', 'aws', 'azure', 'gcp', 'physical', 'virtual', 'container',
                'kubernetes', 'docker', 'vmware', 'hyperv', 'bare_metal'
            ],
            'location_semantic': [
                'region', 'country', 'continent', 'timezone', 'geography',
                'north', 'south', 'east', 'west', 'america', 'europe', 'asia'
            ],
            'business_semantic': [
                'department', 'organization', 'division', 'team', 'group',
                'finance', 'engineering', 'operations', 'sales', 'marketing'
            ],
            'technical_semantic': [
                'operating_system', 'platform', 'architecture', 'version',
                'windows', 'linux', 'unix', 'database', 'web_server'
            ]
        }
    
    def classify_column_advanced(self, column_name: str, sample_values: List[str], 
                               table_context: Dict[str, Any] = None) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        
        if not sample_values:
            return None
        
        cache_key = self._generate_cache_key(column_name, sample_values[:5])
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]
        
        cleaned_values = self._clean_and_validate_samples(sample_values)
        if len(cleaned_values) < 2:
            return None
        
        classification_scores = {}
        
        for field_type, config in self.field_type_patterns.items():
            score = self._calculate_comprehensive_score(
                column_name, cleaned_values, field_type, config, table_context
            )
            if score > 0.3:
                classification_scores[field_type] = score
        
        if not classification_scores:
            return None
        
        best_field_type = max(classification_scores, key=classification_scores.get)
        best_score = classification_scores[best_field_type]
        
        metadata = {
            'method': 'advanced_ai_classification',
            'all_scores': classification_scores,
            'samples_analyzed': len(cleaned_values),
            'confidence_factors': self._explain_classification(column_name, cleaned_values, best_field_type)
        }
        
        result = (best_field_type, best_score, metadata)
        self.classification_cache[cache_key] = result
        
        return result
    
    def _calculate_comprehensive_score(self, column_name: str, values: List[str], 
                                     field_type: str, config: Dict[str, Any],
                                     table_context: Dict[str, Any] = None) -> float:
        
        name_score = self._calculate_name_semantic_score(column_name, config['name_indicators'])
        
        content_score = self._calculate_content_pattern_score(values, config.get('value_patterns', {}))
        
        statistical_score = self._calculate_statistical_profile_score(values, config.get('statistical_profile', {}))
        
        validation_score = self._calculate_validation_score(values, field_type)
        
        context_score = self._calculate_context_score(column_name, table_context, field_type)
        
        semantic_score = self._calculate_semantic_embedding_score(column_name, values, field_type)
        
        weights = [0.25, 0.25, 0.15, 0.15, 0.1, 0.1]
        scores = [name_score, content_score, statistical_score, validation_score, context_score, semantic_score]
        
        final_score = sum(w * s for w, s in zip(weights, scores))
        
        return min(1.0, final_score)
    
    def _calculate_name_semantic_score(self, column_name: str, indicators: List[str]) -> float:
        name_lower = column_name.lower()
        name_words = re.split(r'[_\-\s]+', name_lower)
        
        exact_matches = sum(1 for indicator in indicators if indicator in name_words)
        partial_matches = sum(1 for indicator in indicators if indicator in name_lower)
        
        if exact_matches > 0:
            return min(1.0, exact_matches / len(indicators) + 0.5)
        elif partial_matches > 0:
            return min(0.8, partial_matches / len(indicators) + 0.3)
        
        return 0.0
    
    def _calculate_content_pattern_score(self, values: List[str], patterns: Dict[str, List[str]]) -> float:
        if not patterns:
            return 0.5
        
        total_matches = 0
        total_values = len(values)
        
        for category, pattern_list in patterns.items():
            for value in values[:50]:
                value_lower = str(value).lower()
                
                for pattern in pattern_list:
                    if pattern.startswith('^') and pattern.endswith('$'):
                        try:
                            if re.match(pattern, str(value), re.IGNORECASE):
                                total_matches += 1
                                break
                        except:
                            continue
                    else:
                        if pattern in value_lower:
                            total_matches += 1
                            break
        
        return min(1.0, total_matches / min(total_values, 50))
    
    def _calculate_statistical_profile_score(self, values: List[str], profile: Dict[str, Any]) -> float:
        if not profile:
            return 0.5
        
        score = 0.0
        factors = 0
        
        unique_values = len(set(values))
        total_values = len(values)
        unique_ratio = unique_values / total_values if total_values > 0 else 0
        
        if 'unique_ratio_range' in profile:
            min_ratio, max_ratio = profile['unique_ratio_range']
            if min_ratio <= unique_ratio <= max_ratio:
                score += 1.0
            else:
                distance = min(abs(unique_ratio - min_ratio), abs(unique_ratio - max_ratio))
                score += max(0, 1.0 - distance * 2)
            factors += 1
        
        if 'avg_length_range' in profile:
            avg_length = statistics.mean([len(str(v)) for v in values])
            min_length, max_length = profile['avg_length_range']
            if min_length <= avg_length <= max_length:
                score += 1.0
            else:
                distance = min(abs(avg_length - min_length), abs(avg_length - max_length))
                score += max(0, 1.0 - distance / max_length)
            factors += 1
        
        return score / factors if factors > 0 else 0.5
    
    def _calculate_validation_score(self, values: List[str], field_type: str) -> float:
        if field_type not in self.value_validators:
            return 0.5
        
        validator = self.value_validators[field_type]
        valid_count = 0
        
        for value in values[:20]:
            if validator(str(value)):
                valid_count += 1
        
        return valid_count / min(len(values), 20)
    
    def _calculate_context_score(self, column_name: str, table_context: Dict[str, Any], 
                                field_type: str) -> float:
        if not table_context:
            return 0.5
        
        score = 0.5
        
        table_name = table_context.get('table_name', '').lower()
        related_columns = table_context.get('other_columns', [])
        
        context_boost_patterns = {
            'infrastructure_type': ['infrastructure', 'platform', 'deployment'],
            'business_unit': ['organization', 'department', 'business'],
            'global_region': ['location', 'geography', 'region'],
            'system_classification': ['os', 'platform', 'system'],
            'application_class': ['application', 'service', 'app']
        }
        
        if field_type in context_boost_patterns:
            boost_patterns = context_boost_patterns[field_type]
            for pattern in boost_patterns:
                if pattern in table_name:
                    score += 0.2
                if any(pattern in col.lower() for col in related_columns):
                    score += 0.1
        
        return min(1.0, score)
    
    def _calculate_semantic_embedding_score(self, column_name: str, values: List[str], 
                                          field_type: str) -> float:
        
        semantic_categories = {
            'infrastructure_type': 'infrastructure_semantic',
            'global_region': 'location_semantic', 
            'business_unit': 'business_semantic',
            'system_classification': 'technical_semantic'
        }
        
        if field_type not in semantic_categories:
            return 0.5
        
        semantic_key = semantic_categories[field_type]
        semantic_words = self.semantic_embeddings.get(semantic_key, [])
        
        column_words = re.split(r'[_\-\s]+', column_name.lower())
        value_words = []
        
        for value in values[:10]:
            value_words.extend(re.split(r'[_\-\s]+', str(value).lower()))
        
        column_semantic_matches = sum(1 for word in column_words if word in semantic_words)
        value_semantic_matches = sum(1 for word in value_words if word in semantic_words)
        
        column_score = min(1.0, column_semantic_matches / max(len(column_words), 1))
        value_score = min(1.0, value_semantic_matches / max(len(value_words), 1))
        
        return (column_score * 0.6 + value_score * 0.4)
    
    def _validate_ip(self, value: str) -> bool:
        try:
            parts = value.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not (0 <= int(part) <= 255):
                    return False
            return True
        except:
            return False
    
    def _validate_mac(self, value: str) -> bool:
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$',
            r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$'
        ]
        return any(re.match(pattern, value) for pattern in mac_patterns)
    
    def _validate_fqdn(self, value: str) -> bool:
        if not isinstance(value, str) or not (3 <= len(value) <= 253):
            return False
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$', value))
    
    def _validate_domain(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', value)) or \
               value.endswith('.local') or value.endswith('.corp')
    
    def _clean_and_validate_samples(self, values: List[str]) -> List[str]:
        cleaned = []
        seen = set()
        
        for value in values:
            if value is None:
                continue
            
            str_value = str(value).strip()
            
            if not str_value or str_value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
                continue
            
            if len(str_value) > 500:
                continue
            
            if str_value not in seen:
                cleaned.append(str_value)
                seen.add(str_value)
            
            if len(cleaned) >= 100:
                break
        
        return cleaned
    
    def _explain_classification(self, column_name: str, values: List[str], field_type: str) -> Dict[str, Any]:
        explanation = {
            'column_name_analysis': f"Column name '{column_name}' analyzed for semantic meaning",
            'sample_count': len(values),
            'unique_values': len(set(values)),
            'field_type_classified': field_type,
            'classification_basis': []
        }
        
        if field_type in self.field_type_patterns:
            config = self.field_type_patterns[field_type]
            name_indicators = config['name_indicators']
            
            for indicator in name_indicators:
                if indicator in column_name.lower():
                    explanation['classification_basis'].append(f"Column name contains '{indicator}'")
        
        return explanation
    
    def _generate_cache_key(self, column_name: str, sample_values: List[str]) -> str:
        content = f"{column_name}:{':'.join(str(v) for v in sample_values)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def batch_classify_columns(self, table_schema: List[Dict[str, Any]], 
                              table_samples: Dict[str, List[str]],
                              table_context: Dict[str, Any] = None) -> Dict[str, Tuple[str, float, Dict[str, Any]]]:
        
        classifications = {}
        
        for column_info in table_schema:
            column_name = column_info['name']
            sample_values = table_samples.get(column_name, [])
            
            if sample_values:
                classification = self.classify_column_advanced(
                    column_name, sample_values, table_context
                )
                if classification:
                    classifications[column_name] = classification
        
        return classifications