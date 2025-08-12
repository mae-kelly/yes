#!/usr/bin/env python3

import re
import hashlib
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime
import statistics
import json
import logging

logger = logging.getLogger(__name__)

class DeepPatternRecognizer:
    def __init__(self):
        self.learned_patterns = defaultdict(list)
        self.pattern_success_rates = defaultdict(lambda: {'hits': 0, 'total': 0})
        self.contextual_patterns = defaultdict(dict)
        self.temporal_patterns = defaultdict(list)
        self.similarity_cache = {}
        
    def learn_pattern(self, pattern_type: str, pattern_data: Dict[str, Any], success: bool):
        pattern_signature = self._generate_pattern_signature(pattern_data)
        
        self.learned_patterns[pattern_type].append({
            'signature': pattern_signature,
            'data': pattern_data,
            'timestamp': datetime.now(),
            'success': success
        })
        
        self.pattern_success_rates[pattern_signature]['total'] += 1
        if success:
            self.pattern_success_rates[pattern_signature]['hits'] += 1
    
    def _generate_pattern_signature(self, pattern_data: Dict[str, Any]) -> str:
        normalized_data = {}
        for key, value in pattern_data.items():
            if isinstance(value, str):
                normalized_data[key] = re.sub(r'[0-9]+', 'N', value.lower())
            else:
                normalized_data[key] = str(value)
        
        signature_string = json.dumps(normalized_data, sort_keys=True)
        return hashlib.md5(signature_string.encode()).hexdigest()[:12]
    
    def recognize_pattern(self, pattern_type: str, candidate_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        candidate_signature = self._generate_pattern_signature(candidate_data)
        
        if candidate_signature in self.pattern_success_rates:
            rates = self.pattern_success_rates[candidate_signature]
            confidence = rates['hits'] / max(rates['total'], 1)
            return confidence, {'known_pattern': True, 'signature': candidate_signature}
        
        best_match_confidence = 0.0
        best_match_info = {}
        
        for pattern in self.learned_patterns[pattern_type]:
            similarity = self._calculate_pattern_similarity(candidate_data, pattern['data'])
            
            if similarity > best_match_confidence and similarity > 0.7:
                best_match_confidence = similarity
                best_match_info = {
                    'similar_pattern': True,
                    'similarity': similarity,
                    'reference_pattern': pattern['signature']
                }
        
        return best_match_confidence, best_match_info
    
    def _calculate_pattern_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        cache_key = f"{id(data1)}:{id(data2)}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        common_keys = set(data1.keys()) & set(data2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            val1, val2 = str(data1[key]), str(data2[key])
            
            if val1 == val2:
                similarities.append(1.0)
            else:
                char_similarity = self._string_similarity(val1, val2)
                similarities.append(char_similarity)
        
        result = statistics.mean(similarities) if similarities else 0.0
        self.similarity_cache[cache_key] = result
        return result
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        if not s1 or not s2:
            return 0.0
        
        s1_norm = re.sub(r'[0-9]+', 'N', s1.lower())
        s2_norm = re.sub(r'[0-9]+', 'N', s2.lower())
        
        if s1_norm == s2_norm:
            return 1.0
        
        common_chars = sum(1 for c in s1_norm if c in s2_norm)
        max_length = max(len(s1_norm), len(s2_norm))
        
        return common_chars / max_length if max_length > 0 else 0.0

class HierarchicalFieldClassifier:
    def __init__(self):
        self.classification_tree = self._build_classification_tree()
        self.field_feature_extractors = self._create_feature_extractors()
        self.classification_cache = {}
        
    def _build_classification_tree(self) -> Dict[str, Any]:
        return {
            'identifier_fields': {
                'network_identifiers': {
                    'hostname': {
                        'patterns': [r'host', r'computer', r'endpoint', r'device', r'server', r'machine'],
                        'validators': ['is_hostname_like'],
                        'priority': 100
                    },
                    'fqdn': {
                        'patterns': [r'fqdn', r'domain', r'dns', r'qualified'],
                        'validators': ['is_fqdn_like'],
                        'priority': 95
                    },
                    'ip_address': {
                        'patterns': [r'ip', r'address', r'addr', r'inet'],
                        'validators': ['is_ip_like'],
                        'priority': 90
                    },
                    'mac_address': {
                        'patterns': [r'mac', r'ethernet', r'physical'],
                        'validators': ['is_mac_like'],
                        'priority': 85
                    }
                },
                'location_identifiers': {
                    'global_region': {
                        'patterns': [r'region', r'geo', r'area', r'location'],
                        'validators': ['is_region_like'],
                        'priority': 80
                    },
                    'country': {
                        'patterns': [r'country', r'nation', r'cc'],
                        'validators': ['is_country_like'],
                        'priority': 75
                    },
                    'data_center': {
                        'patterns': [r'datacenter', r'dc', r'facility'],
                        'validators': ['is_datacenter_like'],
                        'priority': 70
                    }
                }
            },
            'classification_fields': {
                'technical_classification': {
                    'infrastructure_type': {
                        'patterns': [r'infra', r'platform', r'type', r'cloud', r'onprem'],
                        'validators': ['is_infrastructure_like'],
                        'priority': 85
                    },
                    'system_classification': {
                        'patterns': [r'os', r'system', r'platform', r'windows', r'linux'],
                        'validators': ['is_system_like'],
                        'priority': 80
                    }
                },
                'business_classification': {
                    'business_unit': {
                        'patterns': [r'bu', r'unit', r'org', r'department'],
                        'validators': ['is_business_unit_like'],
                        'priority': 70
                    },
                    'cio': {
                        'patterns': [r'cio', r'owner', r'responsible'],
                        'validators': ['is_cio_like'],
                        'priority': 65
                    }
                }
            },
            'coverage_fields': {
                'security_coverage': {
                    'edr_coverage': {
                        'patterns': [r'edr', r'endpoint', r'crowdstrike', r'defender'],
                        'validators': ['is_coverage_like'],
                        'priority': 85
                    },
                    'dlp_coverage': {
                        'patterns': [r'dlp', r'data.*loss', r'prevention'],
                        'validators': ['is_coverage_like'],
                        'priority': 80
                    }
                },
                'logging_coverage': {
                    'splunk_coverage': {
                        'patterns': [r'splunk', r'log', r'siem'],
                        'validators': ['is_coverage_like'],
                        'priority': 75
                    }
                }
            }
        }
    
    def _create_feature_extractors(self) -> Dict[str, callable]:
        return {
            'length_features': lambda text: {
                'avg_length': statistics.mean([len(w) for w in text.split()]) if text.split() else 0,
                'total_length': len(text),
                'word_count': len(text.split())
            },
            'character_features': lambda text: {
                'alpha_ratio': sum(c.isalpha() for c in text) / max(len(text), 1),
                'digit_ratio': sum(c.isdigit() for c in text) / max(len(text), 1),
                'special_ratio': sum(not c.isalnum() for c in text) / max(len(text), 1),
                'upper_ratio': sum(c.isupper() for c in text) / max(len(text), 1)
            },
            'pattern_features': lambda text: {
                'has_dots': '.' in text,
                'has_dashes': '-' in text,
                'has_underscores': '_' in text,
                'starts_with_letter': text[0].isalpha() if text else False,
                'ends_with_letter': text[-1].isalpha() if text else False
            },
            'semantic_features': lambda text: {
                'contains_tech_terms': any(term in text.lower() for term in ['server', 'host', 'ip', 'network']),
                'contains_business_terms': any(term in text.lower() for term in ['unit', 'org', 'dept', 'business']),
                'contains_geo_terms': any(term in text.lower() for term in ['region', 'country', 'location', 'dc'])
            }
        }
    
    def classify_field_hierarchically(self, field_name: str, sample_values: List[str]) -> Dict[str, Any]:
        cache_key = f"{field_name}:{hash(tuple(sample_values[:5]))}"
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]
        
        field_features = self._extract_field_features(field_name)
        content_features = self._extract_content_features(sample_values)
        
        classification_results = {}
        
        for category_name, category_tree in self.classification_tree.items():
            category_scores = self._score_category(field_name, sample_values, category_tree, field_features, content_features)
            if category_scores:
                classification_results[category_name] = category_scores
        
        best_classification = self._select_best_classification(classification_results)
        
        result = {
            'best_match': best_classification,
            'all_scores': classification_results,
            'field_features': field_features,
            'content_features': content_features
        }
        
        self.classification_cache[cache_key] = result
        return result
    
    def _extract_field_features(self, field_name: str) -> Dict[str, Any]:
        features = {}
        
        for extractor_name, extractor_func in self.field_feature_extractors.items():
            try:
                features[extractor_name] = extractor_func(field_name)
            except:
                features[extractor_name] = {}
        
        return features
    
    def _extract_content_features(self, sample_values: List[str]) -> Dict[str, Any]:
        if not sample_values:
            return {}
        
        clean_values = [str(v).strip() for v in sample_values if v and str(v).strip()]
        if not clean_values:
            return {}
        
        return {
            'sample_count': len(clean_values),
            'unique_count': len(set(clean_values)),
            'uniqueness_ratio': len(set(clean_values)) / len(clean_values),
            'avg_value_length': statistics.mean([len(v) for v in clean_values]),
            'value_length_variance': statistics.variance([len(v) for v in clean_values]) if len(clean_values) > 1 else 0,
            'common_patterns': self._identify_common_patterns(clean_values),
            'data_types': self._analyze_data_types(clean_values)
        }
    
    def _identify_common_patterns(self, values: List[str]) -> Dict[str, int]:
        patterns = {
            'ip_like': sum(1 for v in values if re.match(r'^\d+\.\d+\.\d+\.\d+, v)),
            'hostname_like': sum(1 for v in values if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9], v)),
            'fqdn_like': sum(1 for v in values if '.' in v and len(v.split('.')) > 1),
            'mac_like': sum(1 for v in values if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}, v)),
            'uuid_like': sum(1 for v in values if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}, v, re.I)),
            'code_like': sum(1 for v in values if re.match(r'^[A-Z]{2,5}, v)),
            'number_like': sum(1 for v in values if v.isdigit()),
            'mixed_alphanumeric': sum(1 for v in values if any(c.isalpha() for c in v) and any(c.isdigit() for c in v))
        }
        
        return {k: v for k, v in patterns.items() if v > 0}
    
    def _analyze_data_types(self, values: List[str]) -> Dict[str, float]:
        total = len(values)
        return {
            'numeric': sum(1 for v in values if v.replace('.', '').isdigit()) / total,
            'alphabetic': sum(1 for v in values if v.isalpha()) / total,
            'alphanumeric': sum(1 for v in values if v.isalnum()) / total,
            'mixed': sum(1 for v in values if any(c.isalpha() for c in v) and any(c.isdigit() for c in v)) / total
        }
    
    def _score_category(self, field_name: str, sample_values: List[str], category_tree: Dict[str, Any], field_features: Dict[str, Any], content_features: Dict[str, Any]) -> Dict[str, float]:
        scores = {}
        
        for subcategory_name, subcategory_data in category_tree.items():
            if isinstance(subcategory_data, dict) and 'patterns' in subcategory_data:
                score = self._score_field_type(field_name, sample_values, subcategory_data, field_features, content_features)
                if score > 0.1:
                    scores[subcategory_name] = score
            elif isinstance(subcategory_data, dict):
                subscore = self._score_category(field_name, sample_values, subcategory_data, field_features, content_features)
                if subscore:
                    scores.update(subscore)
        
        return scores
    
    def _score_field_type(self, field_name: str, sample_values: List[str], field_config: Dict[str, Any], field_features: Dict[str, Any], content_features: Dict[str, Any]) -> float:
        score_components = []
        
        patterns = field_config.get('patterns', [])
        name_score = self._calculate_name_pattern_score(field_name, patterns)
        score_components.append(('name_pattern', name_score, 0.4))
        
        validators = field_config.get('validators', [])
        validation_score = self._calculate_validation_score(sample_values, validators)
        score_components.append(('validation', validation_score, 0.3))
        
        content_score = self._calculate_content_compatibility_score(content_features, field_config)
        score_components.append(('content', content_score, 0.2))
        
        context_score = self._calculate_contextual_score(field_features, field_config)
        score_components.append(('context', context_score, 0.1))
        
        weighted_score = sum(score * weight for _, score, weight in score_components)
        return min(1.0, weighted_score)
    
    def _calculate_name_pattern_score(self, field_name: str, patterns: List[str]) -> float:
        field_lower = field_name.lower()
        
        best_score = 0.0
        for pattern in patterns:
            if re.search(pattern, field_lower):
                match_length = len(re.findall(pattern, field_lower)[0]) if re.findall(pattern, field_lower) else 0
                score = match_length / len(field_lower) if field_lower else 0
                best_score = max(best_score, score)
        
        return min(1.0, best_score)
    
    def _calculate_validation_score(self, sample_values: List[str], validators: List[str]) -> float:
        if not sample_values or not validators:
            return 0.0
        
        valid_count = 0
        for value in sample_values[:20]:
            for validator_name in validators:
                if self._validate_value(value, validator_name):
                    valid_count += 1
                    break
        
        return valid_count / min(len(sample_values), 20)
    
    def _validate_value(self, value: str, validator_name: str) -> bool:
        validators = {
            'is_hostname_like': lambda v: bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9], v)) and len(v) <= 253,
            'is_fqdn_like': lambda v: '.' in v and bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}, v)),
            'is_ip_like': lambda v: bool(re.match(r'^\d+\.\d+\.\d+\.\d+, v)),
            'is_mac_like': lambda v: bool(re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}, v)),
            'is_region_like': lambda v: any(term in v.lower() for term in ['us', 'eu', 'ap', 'americas', 'emea', 'apac']),
            'is_country_like': lambda v: len(v) == 2 or any(country in v.lower() for country in ['united states', 'canada', 'germany']),
            'is_datacenter_like': lambda v: any(term in v.lower() for term in ['dc', 'datacenter', 'facility']),
            'is_infrastructure_like': lambda v: any(term in v.lower() for term in ['cloud', 'onprem', 'saas', 'api']),
            'is_system_like': lambda v: any(term in v.lower() for term in ['windows', 'linux', 'unix', 'server']),
            'is_business_unit_like': lambda v: v.replace(' ', '').replace('-', '').isalnum() and 2 <= len(v) <= 50,
            'is_cio_like': lambda v: any(term in v.lower() for term in ['cio', 'chief', 'officer']),
            'is_coverage_like': lambda v: v.lower() in ['true', 'false', 'yes', 'no', 'enabled', 'disabled']
        }
        
        validator_func = validators.get(validator_name)
        if validator_func:
            try:
                return validator_func(value)
            except:
                return False
        
        return False
    
    def _calculate_content_compatibility_score(self, content_features: Dict[str, Any], field_config: Dict[str, Any]) -> float:
        if not content_features:
            return 0.0
        
        compatibility_factors = []
        
        common_patterns = content_features.get('common_patterns', {})
        data_types = content_features.get('data_types', {})
        
        field_name = field_config.get('patterns', [''])[0] if field_config.get('patterns') else ''
        
        if 'ip' in field_name and common_patterns.get('ip_like', 0) > 0:
            compatibility_factors.append(common_patterns['ip_like'] / content_features.get('sample_count', 1))
        
        if 'hostname' in field_name and common_patterns.get('hostname_like', 0) > 0:
            compatibility_factors.append(common_patterns['hostname_like'] / content_features.get('sample_count', 1))
        
        if 'fqdn' in field_name and common_patterns.get('fqdn_like', 0) > 0:
            compatibility_factors.append(common_patterns['fqdn_like'] / content_features.get('sample_count', 1))
        
        uniqueness = content_features.get('uniqueness_ratio', 0)
        if 'hostname' in field_name or 'ip' in field_name:
            compatibility_factors.append(uniqueness)
        
        return statistics.mean(compatibility_factors) if compatibility_factors else 0.5
    
    def _calculate_contextual_score(self, field_features: Dict[str, Any], field_config: Dict[str, Any]) -> float:
        semantic_features = field_features.get('semantic_features', {})
        
        score = 0.0
        
        if field_config.get('patterns'):
            pattern = field_config['patterns'][0]
            
            if any(tech_term in pattern for tech_term in ['host', 'ip', 'server']) and semantic_features.get('contains_tech_terms'):
                score += 0.3
            
            if any(business_term in pattern for business_term in ['unit', 'org', 'cio']) and semantic_features.get('contains_business_terms'):
                score += 0.3
            
            if any(geo_term in pattern for geo_term in ['region', 'country', 'location']) and semantic_features.get('contains_geo_terms'):
                score += 0.3
        
        return min(1.0, score)
    
    def _select_best_classification(self, classification_results: Dict[str, Dict[str, float]]) -> Optional[Tuple[str, float]]:
        all_scores = []
        
        for category_name, scores in classification_results.items():
            for field_type, score in scores.items():
                all_scores.append((field_type, score))
        
        if not all_scores:
            return None
        
        return max(all_scores, key=lambda x: x[1])

class AdvancedSemanticMatcher:
    def __init__(self):
        self.embedding_cache = {}
        self.concept_embeddings = self._initialize_embeddings()
        self.context_vectors = {}
        
    def _initialize_embeddings(self) -> Dict[str, np.ndarray]:
        return {
            'hostname': np.array([1.0, 0.9, 0.7, 0.4, 0.2, 0.1, 0.3, 0.5]),
            'ip_address': np.array([0.3, 1.0, 0.8, 0.2, 0.1, 0.4, 0.6, 0.3]),
            'infrastructure': np.array([0.5, 0.4, 1.0, 0.8, 0.6, 0.3, 0.7, 0.2]),
            'business': np.array([0.2, 0.1, 0.3, 1.0, 0.9, 0.7, 0.4, 0.6]),
            'security': np.array([0.4, 0.3, 0.6, 0.5, 1.0, 0.8, 0.2, 0.7]),
            'location': np.array([0.1, 0.2, 0.4, 0.6, 0.3, 1.0, 0.9, 0.5]),
            'network': np.array([0.7, 0.8, 0.5, 0.2, 0.4, 0.3, 1.0, 0.6]),
            'classification': np.array([0.6, 0.4, 0.8, 0.7, 0.5, 0.4, 0.3, 1.0])
        }
    
    def calculate_semantic_similarity(self, text1: str, text2: str, context: str = "") -> float:
        cache_key = f"{text1}:{text2}:{context}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        vec1 = self._text_to_vector(text1, context)
        vec2 = self._text_to_vector(text2, context)
        
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        similarity = max(0.0, min(1.0, similarity))
        
        self.embedding_cache[cache_key] = similarity
        return similarity
    
    def _text_to_vector(self, text: str, context: str = "") -> np.ndarray:
        base_vector = np.zeros(8)
        text_lower = text.lower()
        
        concept_weights = {
            'hostname': ['host', 'endpoint', 'computer', 'device', 'server', 'machine'],
            'ip_address': ['ip', 'address', 'addr', 'inet'],
            'infrastructure': ['cloud', 'onprem', 'saas', 'api', 'platform'],
            'business': ['unit', 'org', 'department', 'business', 'company'],
            'security': ['security', 'auth', 'firewall', 'vpn', 'edr'],
            'location': ['region', 'country', 'location', 'geo', 'datacenter'],
            'network': ['network', 'subnet', 'vlan', 'dns', 'domain'],
            'classification': ['type', 'class', 'category', 'system', 'os']
        }
        
        for i, (concept, keywords) in enumerate(concept_weights.items()):
            weight = sum(1 for keyword in keywords if keyword in text_lower)
            if weight > 0:
                base_vector[i] = weight / len(keywords)
        
        if context:
            context_boost = self._get_context_boost(text_lower, context.lower())
            base_vector = base_vector * (1 + context_boost * 0.2)
        
        return base_vector / (np.linalg.norm(base_vector) + 1e-8)
    
    def _get_context_boost(self, text: str, context: str) -> float:
        context_mappings = {
            'cmdb': ['asset', 'inventory', 'management'],
            'security': ['protection', 'monitoring', 'threat'],
            'network': ['connectivity', 'infrastructure', 'topology'],
            'business': ['organization', 'operational', 'enterprise']
        }
        
        boost = 0.0
        for context_type, keywords in context_mappings.items():
            if any(keyword in context for keyword in keywords):
                if any(keyword in text for keyword in keywords):
                    boost += 0.3
        
        return min(1.0, boost)