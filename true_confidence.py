import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter, defaultdict
import re
import hashlib
from datetime import datetime, timedelta
import statistics
import math

class TrueIntelligenceConfidence:
    def __init__(self):
        self.observed_patterns = defaultdict(lambda: defaultdict(int))
        self.field_correlations = defaultdict(lambda: defaultdict(float))
        self.learned_relationships = []
        self.confidence_history = []
        self.pattern_discovery_engine = PatternDiscoveryEngine()
        self.relationship_analyzer = RelationshipAnalyzer()
        self.coherence_detector = CoherenceDetector()
        
    def calculate_confidence(self, entity_data: Dict[str, Any], concept_type: str, 
                            properties: Dict[str, Any], inferences: List[str],
                            embeddings: Optional[np.ndarray] = None) -> Tuple[float, Dict[str, Any]]:
        
        analysis_results = {}
        
        discovered_patterns = self.pattern_discovery_engine.discover(entity_data)
        analysis_results['patterns'] = discovered_patterns
        
        relationships = self.relationship_analyzer.analyze(entity_data, properties)
        analysis_results['relationships'] = relationships
        
        coherence = self.coherence_detector.measure(entity_data, inferences)
        analysis_results['coherence'] = coherence
        
        information_density = self._measure_information_density(entity_data)
        analysis_results['information_density'] = information_density
        
        predictive_power = self._measure_predictive_power(entity_data, inferences)
        analysis_results['predictive_power'] = predictive_power
        
        uniqueness = self._measure_uniqueness(entity_data)
        analysis_results['uniqueness'] = uniqueness
        
        confidence = self._synthesize_confidence(analysis_results)
        
        self._learn_from_observation(entity_data, confidence, analysis_results)
        
        return confidence, analysis_results
    
    def _measure_information_density(self, entity_data: Dict[str, Any]) -> Dict[str, float]:
        total_information = 0
        field_information = {}
        
        for field, value in entity_data.items():
            if value is None or value == '':
                field_info = 0
            else:
                value_str = str(value)
                
                entropy = self._calculate_entropy(value_str)
                
                uniqueness = len(set(value_str)) / len(value_str) if value_str else 0
                
                length_factor = math.log(len(value_str) + 1) / 10
                
                field_info = entropy * 0.4 + uniqueness * 0.3 + length_factor * 0.3
                
                if isinstance(value, bool):
                    field_info *= 0.8
                elif re.match(r'^[\d.]+$', value_str):
                    field_info *= 0.9
                elif '@' in value_str or '.' in value_str:
                    field_info *= 1.1
                
            field_information[field] = field_info
            total_information += field_info
        
        avg_information = total_information / len(entity_data) if entity_data else 0
        
        return {
            'total': total_information,
            'average': avg_information,
            'per_field': field_information,
            'density_score': min(1.0, avg_information)
        }
    
    def _calculate_entropy(self, text: str) -> float:
        if not text:
            return 0
        
        char_counts = Counter(text)
        total_chars = len(text)
        
        entropy = 0
        for count in char_counts.values():
            probability = count / total_chars
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        normalized_entropy = entropy / math.log2(len(char_counts)) if len(char_counts) > 1 else 0
        
        return normalized_entropy
    
    def _measure_predictive_power(self, entity_data: Dict[str, Any], inferences: List[str]) -> Dict[str, float]:
        predictive_scores = []
        
        field_pairs = [
            (entity_data.get('hostname', ''), entity_data.get('environment', '')),
            (entity_data.get('criticality', ''), entity_data.get('environment', '')),
            (entity_data.get('os_type', ''), entity_data.get('domain', ''))
        ]
        
        for field1, field2 in field_pairs:
            if field1 and field2:
                correlation = self._calculate_field_correlation(str(field1), str(field2))
                predictive_scores.append(correlation)
        
        inference_prediction_score = len(inferences) / 10 if inferences else 0
        predictive_scores.append(min(1.0, inference_prediction_score))
        
        if entity_data.get('hostname'):
            hostname = str(entity_data['hostname']).lower()
            predicted_env = None
            
            if 'prod' in hostname:
                predicted_env = 'production'
            elif 'dev' in hostname:
                predicted_env = 'development'
            elif 'test' in hostname:
                predicted_env = 'test'
            
            if predicted_env and entity_data.get('environment') == predicted_env:
                predictive_scores.append(1.0)
            elif predicted_env and entity_data.get('environment'):
                predictive_scores.append(0.3)
        
        avg_predictive = sum(predictive_scores) / len(predictive_scores) if predictive_scores else 0.5
        
        return {
            'score': avg_predictive,
            'predictions_made': len(predictive_scores),
            'inference_contribution': inference_prediction_score
        }
    
    def _calculate_field_correlation(self, field1: str, field2: str) -> float:
        combined = field1 + field2
        
        if not combined:
            return 0.5
        
        char_overlap = len(set(field1) & set(field2)) / len(set(field1) | set(field2)) if field1 and field2 else 0
        
        self.field_correlations[field1][field2] += 0.1
        historical_correlation = min(1.0, self.field_correlations[field1][field2])
        
        return char_overlap * 0.5 + historical_correlation * 0.5
    
    def _measure_uniqueness(self, entity_data: Dict[str, Any]) -> Dict[str, float]:
        uniqueness_scores = []
        
        for field, value in entity_data.items():
            if value:
                self.observed_patterns[field][str(value)] += 1
                
                times_seen = self.observed_patterns[field][str(value)]
                uniqueness = 1.0 / (times_seen + 1)
                uniqueness_scores.append(uniqueness)
        
        avg_uniqueness = sum(uniqueness_scores) / len(uniqueness_scores) if uniqueness_scores else 0.5
        
        return {
            'score': avg_uniqueness,
            'unique_fields': sum(1 for s in uniqueness_scores if s > 0.8)
        }
    
    def _synthesize_confidence(self, analysis_results: Dict[str, Any]) -> float:
        components = []
        
        if 'patterns' in analysis_results:
            pattern_strength = analysis_results['patterns'].get('strength', 0)
            components.append(pattern_strength)
        
        if 'relationships' in analysis_results:
            relationship_score = analysis_results['relationships'].get('score', 0)
            components.append(relationship_score)
        
        if 'coherence' in analysis_results:
            coherence_score = analysis_results['coherence'].get('score', 0)
            components.append(coherence_score)
        
        if 'information_density' in analysis_results:
            density_score = analysis_results['information_density'].get('density_score', 0)
            components.append(density_score)
        
        if 'predictive_power' in analysis_results:
            predictive_score = analysis_results['predictive_power'].get('score', 0)
            components.append(predictive_score)
        
        if 'uniqueness' in analysis_results:
            uniqueness_score = analysis_results['uniqueness'].get('score', 0)
            components.append(uniqueness_score * 0.5)
        
        if not components:
            return 0.0
        
        mean_confidence = sum(components) / len(components)
        
        std_dev = statistics.stdev(components) if len(components) > 1 else 0
        consistency_factor = 1.0 - (std_dev * 0.2)
        
        final_confidence = mean_confidence * consistency_factor
        
        if len([c for c in components if c > 0.8]) >= len(components) * 0.6:
            final_confidence *= 1.1
        
        return min(1.0, max(0.0, final_confidence))
    
    def _learn_from_observation(self, entity_data: Dict[str, Any], confidence: float, analysis: Dict[str, Any]):
        self.confidence_history.append({
            'timestamp': datetime.now(),
            'confidence': confidence,
            'field_count': len(entity_data),
            'analysis': analysis
        })
        
        if confidence > 0.8:
            for field1, value1 in entity_data.items():
                for field2, value2 in entity_data.items():
                    if field1 != field2:
                        self.learned_relationships.append((field1, field2, confidence))

class PatternDiscoveryEngine:
    def __init__(self):
        self.discovered_patterns = []
        
    def discover(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        patterns_found = []
        
        for field, value in entity_data.items():
            if value:
                field_patterns = self._discover_field_patterns(field, value)
                patterns_found.extend(field_patterns)
        
        cross_field_patterns = self._discover_cross_field_patterns(entity_data)
        patterns_found.extend(cross_field_patterns)
        
        pattern_strength = self._calculate_pattern_strength(patterns_found)
        
        return {
            'patterns': patterns_found,
            'count': len(patterns_found),
            'strength': pattern_strength
        }
    
    def _discover_field_patterns(self, field: str, value: Any) -> List[Dict[str, Any]]:
        patterns = []
        value_str = str(value)
        
        if re.match(r'^[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+', value_str):
            patterns.append({
                'type': 'structured_naming',
                'field': field,
                'confidence': len(value_str.split('-')) / 10
            })
        
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value_str):
            patterns.append({
                'type': 'ip_address',
                'field': field,
                'confidence': 0.95
            })
        
        if '@' in value_str and '.' in value_str:
            patterns.append({
                'type': 'email',
                'field': field,
                'confidence': 0.9
            })
        
        if re.match(r'\d{4}-\d{2}-\d{2}', value_str):
            patterns.append({
                'type': 'date',
                'field': field,
                'confidence': 0.85
            })
        
        if field.lower() in ['hostname', 'host', 'server'] and '-' in value_str:
            parts = value_str.split('-')
            if len(parts) >= 2:
                patterns.append({
                    'type': 'hostname_structure',
                    'field': field,
                    'confidence': min(0.9, len(parts) * 0.3)
                })
        
        return patterns
    
    def _discover_cross_field_patterns(self, entity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        patterns = []
        
        hostname = str(entity_data.get('hostname', '')).lower()
        environment = str(entity_data.get('environment', '')).lower()
        
        if hostname and environment:
            if ('prod' in hostname and environment == 'production') or \
               ('dev' in hostname and environment == 'development'):
                patterns.append({
                    'type': 'consistent_naming',
                    'confidence': 0.9
                })
        
        if entity_data.get('ip_address') and entity_data.get('hostname'):
            patterns.append({
                'type': 'network_identity',
                'confidence': 0.85
            })
        
        security_fields = ['edr_coverage', 'splunk_logging', 'tanium_coverage']
        security_count = sum(1 for f in security_fields if entity_data.get(f))
        if security_count > 0:
            patterns.append({
                'type': 'security_monitoring',
                'confidence': security_count / len(security_fields)
            })
        
        return patterns
    
    def _calculate_pattern_strength(self, patterns: List[Dict[str, Any]]) -> float:
        if not patterns:
            return 0.0
        
        confidences = [p.get('confidence', 0) for p in patterns]
        avg_confidence = sum(confidences) / len(confidences)
        
        pattern_types = set(p.get('type') for p in patterns)
        diversity_factor = len(pattern_types) / 10
        
        return min(1.0, avg_confidence * 0.7 + diversity_factor * 0.3)

class RelationshipAnalyzer:
    def analyze(self, entity_data: Dict[str, Any], properties: Dict[str, Any]) -> Dict[str, Any]:
        relationships = []
        
        for field1 in entity_data:
            for field2 in entity_data:
                if field1 < field2:
                    strength = self._measure_relationship_strength(
                        field1, entity_data[field1],
                        field2, entity_data[field2]
                    )
                    if strength > 0.3:
                        relationships.append({
                            'field1': field1,
                            'field2': field2,
                            'strength': strength
                        })
        
        relationship_score = self._calculate_relationship_score(relationships)
        
        return {
            'relationships': relationships,
            'count': len(relationships),
            'score': relationship_score
        }
    
    def _measure_relationship_strength(self, field1: str, value1: Any, field2: str, value2: Any) -> float:
        if value1 is None or value2 is None:
            return 0.0
        
        known_relationships = {
            ('hostname', 'environment'): 0.8,
            ('hostname', 'ip_address'): 0.9,
            ('environment', 'criticality'): 0.7,
            ('os_type', 'domain'): 0.6,
            ('edr_coverage', 'splunk_logging'): 0.5
        }
        
        key = tuple(sorted([field1, field2]))
        if key in known_relationships:
            return known_relationships[key]
        
        str1, str2 = str(value1).lower(), str(value2).lower()
        
        if str1 in str2 or str2 in str1:
            return 0.6
        
        common_chars = set(str1) & set(str2)
        if common_chars:
            return len(common_chars) / (len(set(str1) | set(str2)) + 1) * 0.5
        
        return 0.0
    
    def _calculate_relationship_score(self, relationships: List[Dict[str, Any]]) -> float:
        if not relationships:
            return 0.3
        
        strengths = [r['strength'] for r in relationships]
        avg_strength = sum(strengths) / len(strengths)
        
        relationship_count_factor = min(1.0, len(relationships) / 5)
        
        return avg_strength * 0.6 + relationship_count_factor * 0.4

class CoherenceDetector:
    def measure(self, entity_data: Dict[str, Any], inferences: List[str]) -> Dict[str, Any]:
        coherence_checks = []
        
        hostname = str(entity_data.get('hostname', '')).lower()
        environment = str(entity_data.get('environment', '')).lower()
        criticality = str(entity_data.get('criticality', '')).lower()
        
        if 'production_system' in inferences:
            if environment == 'production':
                coherence_checks.append(('inference_matches_data', 0.9))
            if criticality in ['high', 'critical']:
                coherence_checks.append(('criticality_appropriate', 0.85))
        
        if hostname and environment:
            hostname_env = self._extract_environment_from_hostname(hostname)
            if hostname_env and hostname_env == environment:
                coherence_checks.append(('naming_convention_followed', 0.95))
        
        if entity_data.get('ip_address'):
            ip = str(entity_data['ip_address'])
            if ip.startswith('10.') or ip.startswith('192.168.'):
                if not entity_data.get('ipam_public_ip', False):
                    coherence_checks.append(('private_ip_consistent', 0.9))
        
        os_type = entity_data.get('os_type')
        domain = entity_data.get('domain')
        if os_type == 'Windows' and domain and '.com' in domain:
            coherence_checks.append(('windows_domain_coherent', 0.85))
        
        if not coherence_checks:
            return {'score': 0.5, 'checks': []}
        
        avg_coherence = sum(score for _, score in coherence_checks) / len(coherence_checks)
        
        return {
            'score': avg_coherence,
            'checks': [check for check, _ in coherence_checks],
            'coherence_level': 'high' if avg_coherence > 0.8 else 'moderate'
        }
    
    def _extract_environment_from_hostname(self, hostname: str) -> Optional[str]:
        if 'prod' in hostname or 'prd' in hostname:
            return 'production'
        elif 'dev' in hostname:
            return 'development'
        elif 'test' in hostname or 'qa' in hostname:
            return 'test'
        elif 'stg' in hostname or 'stage' in hostname:
            return 'staging'
        return None