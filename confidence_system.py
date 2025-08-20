import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter, defaultdict
import re
import hashlib
from datetime import datetime, timedelta
import statistics
import math

class GeniusConfidenceSystem:
    def __init__(self):
        self.knowledge_accumulator = defaultdict(list)
        self.pattern_library = self._build_pattern_library()
        self.learned_patterns = defaultdict(float)
        self.confidence_history = []
        
    def _build_pattern_library(self):
        return {
            'hostname_patterns': [
                (r'^[a-z]{2,4}-[a-z]{2,6}-\d{2,4}$', 0.95, 'standard_naming'),
                (r'^(prod|dev|test|qa|stg)-.*', 0.9, 'environment_prefix'),
                (r'^[a-z]+-[a-z]+-[a-z]+-\d+$', 0.92, 'structured_naming'),
                (r'.*\.(corp|internal|local)\..*', 0.88, 'corporate_domain'),
                (r'^(srv|svr|server|host|node)-.*', 0.85, 'server_prefix'),
                (r'^(web|app|db|api|cache|proxy)-.*', 0.87, 'service_type'),
                (r'^[a-z]{3}\d{2}[a-z]{3}\d{2}$', 0.83, 'datacenter_code'),
                (r'.*-(primary|secondary|master|slave|replica).*', 0.86, 'role_suffix')
            ],
            'ip_patterns': [
                (r'^10\..*', 0.95, 'private_class_a'),
                (r'^172\.(1[6-9]|2[0-9]|3[01])\..*', 0.95, 'private_class_b'),
                (r'^192\.168\..*', 0.95, 'private_class_c'),
                (r'^127\..*', 0.99, 'loopback'),
                (r'^169\.254\..*', 0.85, 'link_local')
            ],
            'criticality_indicators': {
                'production': ['prod', 'prd', 'production', 'live', 'master'],
                'development': ['dev', 'development', 'test', 'qa', 'staging'],
                'critical_services': ['database', 'db', 'auth', 'authentication', 'payment', 'billing'],
                'infrastructure': ['dns', 'dhcp', 'ad', 'domain', 'ldap', 'ntp']
            }
        }
    
    def calculate_genius_confidence(self, entity_data: Dict[str, Any], concept_type: str, 
                                   properties: Dict[str, Any], inferences: List[str],
                                   embeddings: Optional[np.ndarray] = None) -> Tuple[float, Dict[str, Any]]:
        
        confidence_signals = []
        confidence_details = {}
        
        signal_1 = self._deep_pattern_analysis(entity_data, concept_type)
        confidence_signals.append(signal_1['score'])
        confidence_details['pattern_analysis'] = signal_1
        
        signal_2 = self._intelligent_field_analysis(entity_data, properties)
        confidence_signals.append(signal_2['score'])
        confidence_details['field_analysis'] = signal_2
        
        signal_3 = self._contextual_coherence_analysis(entity_data, inferences)
        confidence_signals.append(signal_3['score'])
        confidence_details['coherence'] = signal_3
        
        signal_4 = self._cross_field_validation(entity_data)
        confidence_signals.append(signal_4['score'])
        confidence_details['validation'] = signal_4
        
        signal_5 = self._inference_strength_analysis(inferences, entity_data)
        confidence_signals.append(signal_5['score'])
        confidence_details['inference_strength'] = signal_5
        
        signal_6 = self._data_quality_assessment(entity_data)
        confidence_signals.append(signal_6['score'])
        confidence_details['data_quality'] = signal_6
        
        signal_7 = self._semantic_coherence_score(entity_data, embeddings)
        confidence_signals.append(signal_7['score'])
        confidence_details['semantic_coherence'] = signal_7
        
        signal_8 = self._predictive_consistency(entity_data, concept_type)
        confidence_signals.append(signal_8['score'])
        confidence_details['predictive'] = signal_8
        
        base_confidence = self._calculate_weighted_confidence(confidence_signals)
        
        boost_factor = self._calculate_confidence_boost(entity_data, inferences, confidence_details)
        
        final_confidence = min(0.99, base_confidence * boost_factor)
        
        self._learn_from_analysis(entity_data, final_confidence, confidence_details)
        
        confidence_details['final_score'] = final_confidence
        confidence_details['boost_factor'] = boost_factor
        confidence_details['component_scores'] = confidence_signals
        
        return final_confidence, confidence_details
    
    def _deep_pattern_analysis(self, entity_data: Dict[str, Any], concept_type: str) -> Dict[str, Any]:
        pattern_matches = []
        
        hostname = str(entity_data.get('hostname', '')).lower()
        if hostname:
            for pattern, weight, pattern_type in self.pattern_library['hostname_patterns']:
                if re.match(pattern, hostname):
                    pattern_matches.append({
                        'type': pattern_type,
                        'weight': weight,
                        'field': 'hostname'
                    })
        
        ip = str(entity_data.get('ip_address', ''))
        if ip:
            for pattern, weight, pattern_type in self.pattern_library['ip_patterns']:
                if re.match(pattern, ip):
                    pattern_matches.append({
                        'type': pattern_type,
                        'weight': weight,
                        'field': 'ip_address'
                    })
        
        for field, value in entity_data.items():
            if value and field not in ['hostname', 'ip_address']:
                field_patterns = self._detect_field_patterns(field, value)
                pattern_matches.extend(field_patterns)
        
        if not pattern_matches:
            return {'score': 0.7, 'matches': [], 'strength': 'baseline'}
        
        avg_weight = sum(m['weight'] for m in pattern_matches) / len(pattern_matches)
        match_diversity = len(set(m['field'] for m in pattern_matches)) / max(len(entity_data), 1)
        
        score = avg_weight * 0.7 + match_diversity * 0.3
        
        return {
            'score': min(0.95, score),
            'matches': pattern_matches,
            'strength': 'strong' if score > 0.85 else 'moderate'
        }
    
    def _intelligent_field_analysis(self, entity_data: Dict[str, Any], properties: Dict[str, Any]) -> Dict[str, Any]:
        field_scores = []
        critical_fields_present = []
        
        critical_fields = {
            'hostname': 0.95,
            'ip_address': 0.9,
            'environment': 0.88,
            'criticality': 0.87,
            'edr_coverage': 0.92,
            'splunk_logging': 0.9,
            'os_type': 0.85,
            'domain': 0.83,
            'owner': 0.8
        }
        
        for field, importance in critical_fields.items():
            if field in entity_data and entity_data[field] not in [None, '', 'unknown', 'n/a']:
                field_scores.append(importance)
                critical_fields_present.append(field)
                
                if field in properties:
                    prop_confidence = properties[field].get('confidence', 0)
                    field_scores.append(prop_confidence * 0.5)
        
        optional_fields_bonus = 0
        for field in entity_data:
            if field not in critical_fields and entity_data[field]:
                optional_fields_bonus += 0.02
        
        if not field_scores:
            return {'score': 0.6, 'critical_fields': [], 'completeness': 0}
        
        base_score = sum(field_scores) / len(critical_fields)
        completeness = len(critical_fields_present) / len(critical_fields)
        
        final_score = base_score * 0.6 + completeness * 0.3 + min(0.1, optional_fields_bonus)
        
        return {
            'score': min(0.98, final_score),
            'critical_fields': critical_fields_present,
            'completeness': completeness
        }
    
    def _contextual_coherence_analysis(self, entity_data: Dict[str, Any], inferences: List[str]) -> Dict[str, Any]:
        coherence_checks = []
        
        if 'production_system' in inferences:
            if entity_data.get('criticality') in ['high', 'critical']:
                coherence_checks.append(('criticality_matches_env', 0.95))
            if entity_data.get('environment') == 'production':
                coherence_checks.append(('environment_confirmed', 0.98))
        
        if 'windows_domain_member' in inferences:
            if 'corp' in str(entity_data.get('domain', '')).lower():
                coherence_checks.append(('domain_validates', 0.92))
            if entity_data.get('os_type') == 'Windows':
                coherence_checks.append(('os_matches', 0.94))
        
        if 'cloud_hosted' in inferences:
            if any(cloud in str(entity_data.get('hostname', '')).lower() for cloud in ['aws', 'azure', 'gcp']):
                coherence_checks.append(('cloud_naming_confirmed', 0.91))
        
        hostname = str(entity_data.get('hostname', '')).lower()
        ip = str(entity_data.get('ip_address', ''))
        
        if hostname and ip:
            if ('prod' in hostname and ip.startswith('10.')):
                coherence_checks.append(('network_segregation', 0.89))
            if ('dev' in hostname and (ip.startswith('172.') or ip.startswith('192.168.'))):
                coherence_checks.append(('dev_network', 0.87))
        
        if entity_data.get('edr_coverage') and entity_data.get('splunk_logging'):
            coherence_checks.append(('security_tools_present', 0.93))
        
        if not coherence_checks:
            return {'score': 0.75, 'coherent_aspects': [], 'strength': 'baseline'}
        
        avg_coherence = sum(score for _, score in coherence_checks) / len(coherence_checks)
        
        return {
            'score': min(0.97, avg_coherence),
            'coherent_aspects': [aspect for aspect, _ in coherence_checks],
            'strength': 'very_strong' if avg_coherence > 0.9 else 'strong'
        }
    
    def _cross_field_validation(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        validations = []
        
        hostname = str(entity_data.get('hostname', '')).lower()
        environment = str(entity_data.get('environment', '')).lower()
        criticality = str(entity_data.get('criticality', '')).lower()
        
        if hostname and environment:
            if ('prod' in hostname and environment == 'production') or \
               ('dev' in hostname and environment == 'development') or \
               ('test' in hostname and environment in ['test', 'qa']):
                validations.append(('hostname_environment_match', 0.96))
        
        if environment == 'production' and criticality in ['high', 'critical']:
            validations.append(('production_criticality_appropriate', 0.94))
        
        if entity_data.get('os_type') == 'Windows' and entity_data.get('domain'):
            if '.com' in str(entity_data.get('domain')) or '.local' in str(entity_data.get('domain')):
                validations.append(('windows_domain_valid', 0.92))
        
        if entity_data.get('business_unit') and entity_data.get('owner'):
            if '@' in str(entity_data.get('owner')):
                validations.append(('owner_format_valid', 0.88))
        
        ip = str(entity_data.get('ip_address', ''))
        if ip.startswith('10.') or ip.startswith('172.') or ip.startswith('192.168.'):
            if not entity_data.get('ipam_public_ip'):
                validations.append(('private_ip_confirmed', 0.95))
        
        if not validations:
            return {'score': 0.8, 'validations': [], 'consistency': 'good'}
        
        avg_validation = sum(score for _, score in validations) / len(validations)
        
        return {
            'score': min(0.98, avg_validation),
            'validations': [v for v, _ in validations],
            'consistency': 'excellent' if avg_validation > 0.92 else 'very_good'
        }
    
    def _inference_strength_analysis(self, inferences: List[str], entity_data: Dict[str, Any]) -> Dict[str, Any]:
        inference_quality = []
        
        critical_inferences = ['production_system', 'security_gap_critical', 'requires_immediate_action']
        important_inferences = ['no_endpoint_protection', 'visibility_gap_high', 'outdated_patches']
        
        for inference in inferences:
            if inference in critical_inferences:
                supporting_evidence = self._find_supporting_evidence(inference, entity_data)
                if supporting_evidence:
                    inference_quality.append(0.95)
            elif inference in important_inferences:
                inference_quality.append(0.88)
            else:
                inference_quality.append(0.82)
        
        if len(inferences) > 3:
            inference_quality.append(0.9)
        
        if 'production_system' in inferences and 'security_gap_critical' in inferences:
            inference_quality.append(0.97)
        
        if not inference_quality:
            return {'score': 0.75, 'strength': 'moderate', 'count': 0}
        
        avg_quality = sum(inference_quality) / len(inference_quality)
        
        return {
            'score': min(0.96, avg_quality),
            'strength': 'very_strong' if avg_quality > 0.9 else 'strong',
            'count': len(inferences)
        }
    
    def _find_supporting_evidence(self, inference: str, entity_data: Dict[str, Any]) -> List[str]:
        evidence = []
        
        if inference == 'production_system':
            if 'prod' in str(entity_data.get('hostname', '')).lower():
                evidence.append('hostname_contains_prod')
            if entity_data.get('environment') == 'production':
                evidence.append('environment_is_production')
            if entity_data.get('criticality') in ['high', 'critical']:
                evidence.append('high_criticality')
        
        elif inference == 'security_gap_critical':
            if not entity_data.get('edr_coverage'):
                evidence.append('no_edr')
            if not entity_data.get('tanium_coverage'):
                evidence.append('no_tanium')
        
        return evidence
    
    def _data_quality_assessment(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        quality_metrics = []
        
        non_null_count = sum(1 for v in entity_data.values() if v not in [None, '', 'unknown', 'n/a'])
        total_fields = len(entity_data)
        completeness = non_null_count / total_fields if total_fields > 0 else 0
        quality_metrics.append(completeness)
        
        text_fields = [v for v in entity_data.values() if isinstance(v, str) and v]
        if text_fields:
            avg_length = sum(len(f) for f in text_fields) / len(text_fields)
            if avg_length > 3:
                quality_metrics.append(0.85)
        
        bool_fields = [k for k, v in entity_data.items() if isinstance(v, bool)]
        if bool_fields:
            quality_metrics.append(0.9)
        
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        date_fields = [v for v in entity_data.values() if isinstance(v, str) and re.match(date_pattern, v)]
        if date_fields:
            quality_metrics.append(0.88)
        
        if entity_data.get('hostname') and entity_data.get('ip_address'):
            quality_metrics.append(0.95)
        
        if not quality_metrics:
            return {'score': 0.7, 'completeness': 0, 'quality': 'fair'}
        
        avg_quality = sum(quality_metrics) / len(quality_metrics)
        
        return {
            'score': min(0.94, avg_quality * 1.1),
            'completeness': completeness,
            'quality': 'excellent' if avg_quality > 0.85 else 'good'
        }
    
    def _semantic_coherence_score(self, entity_data: Dict[str, Any], embeddings: Optional[np.ndarray]) -> Dict[str, Any]:
        coherence_score = 0.8
        
        text_representation = ' '.join(str(v) for v in entity_data.values() if v)
        unique_tokens = len(set(text_representation.lower().split()))
        total_tokens = len(text_representation.split())
        
        if total_tokens > 0:
            diversity_ratio = unique_tokens / total_tokens
            coherence_score += diversity_ratio * 0.1
        
        if embeddings is not None and len(embeddings) > 0:
            embedding_norm = np.linalg.norm(embeddings)
            if embedding_norm > 0:
                coherence_score += 0.05
        
        field_relationships = self._analyze_field_relationships(entity_data)
        if field_relationships > 3:
            coherence_score += 0.08
        
        return {
            'score': min(0.93, coherence_score),
            'relationships': field_relationships,
            'semantic_strength': 'strong'
        }
    
    def _analyze_field_relationships(self, entity_data: Dict[str, Any]) -> int:
        relationships = 0
        
        if entity_data.get('hostname') and entity_data.get('domain'):
            relationships += 1
        if entity_data.get('hostname') and entity_data.get('ip_address'):
            relationships += 1
        if entity_data.get('environment') and entity_data.get('criticality'):
            relationships += 1
        if entity_data.get('owner') and entity_data.get('business_unit'):
            relationships += 1
        if entity_data.get('edr_coverage') and entity_data.get('splunk_logging'):
            relationships += 1
        
        return relationships
    
    def _predictive_consistency(self, entity_data: Dict[str, Any], concept_type: str) -> Dict[str, Any]:
        predictions_correct = []
        
        if concept_type == 'Host':
            if entity_data.get('hostname'):
                predictions_correct.append(0.9)
            if entity_data.get('ip_address'):
                predictions_correct.append(0.88)
            if entity_data.get('os_type'):
                predictions_correct.append(0.85)
        
        hostname = str(entity_data.get('hostname', '')).lower()
        if 'prod' in hostname and entity_data.get('environment') == 'production':
            predictions_correct.append(0.95)
        if 'db' in hostname and entity_data.get('criticality') in ['high', 'critical']:
            predictions_correct.append(0.92)
        
        if not predictions_correct:
            return {'score': 0.78, 'consistency': 'baseline'}
        
        avg_prediction = sum(predictions_correct) / len(predictions_correct)
        
        return {
            'score': min(0.94, avg_prediction),
            'consistency': 'excellent' if avg_prediction > 0.9 else 'good'
        }
    
    def _detect_field_patterns(self, field: str, value: Any) -> List[Dict[str, Any]]:
        patterns = []
        value_str = str(value)
        
        if re.match(r'^[A-Z]{2,5}-\d{3,6}$', value_str):
            patterns.append({'type': 'id_pattern', 'weight': 0.85, 'field': field})
        
        if re.match(r'^\w+@\w+\.\w+$', value_str):
            patterns.append({'type': 'email_pattern', 'weight': 0.9, 'field': field})
        
        if re.match(r'^\d{4}-\d{2}-\d{2}', value_str):
            patterns.append({'type': 'date_pattern', 'weight': 0.88, 'field': field})
        
        return patterns
    
    def _calculate_weighted_confidence(self, signals: List[float]) -> float:
        if not signals:
            return 0.7
        
        weights = np.array([1.2, 1.1, 1.0, 0.95, 0.9, 0.85, 0.8, 0.75])[:len(signals)]
        weights = weights / weights.sum()
        
        weighted_avg = np.average(signals, weights=weights)
        
        std_dev = np.std(signals)
        consistency_bonus = 0.05 * (1 - min(std_dev, 0.2) / 0.2)
        
        return min(0.95, weighted_avg + consistency_bonus)
    
    def _calculate_confidence_boost(self, entity_data: Dict[str, Any], inferences: List[str], 
                                   details: Dict[str, Any]) -> float:
        boost = 1.0
        
        if len(inferences) >= 5:
            boost *= 1.05
        
        if 'production_system' in inferences and 'security_gap_critical' in inferences:
            boost *= 1.08
        
        high_scoring_components = sum(1 for v in details.values() if isinstance(v, dict) and v.get('score', 0) > 0.9)
        if high_scoring_components >= 4:
            boost *= 1.06
        
        if entity_data.get('hostname') and entity_data.get('ip_address') and entity_data.get('environment'):
            boost *= 1.04
        
        pattern_matches = details.get('pattern_analysis', {}).get('matches', [])
        if len(pattern_matches) >= 3:
            boost *= 1.03
        
        return min(1.15, boost)
    
    def _learn_from_analysis(self, entity_data: Dict[str, Any], confidence: float, details: Dict[str, Any]):
        key = self._generate_pattern_key(entity_data)
        self.learned_patterns[key] = max(self.learned_patterns[key], confidence)
        
        self.confidence_history.append({
            'timestamp': datetime.now(),
            'confidence': confidence,
            'entity_type': entity_data.get('hostname', 'unknown'),
            'details': details
        })
        
        for field, value in entity_data.items():
            if value and confidence > 0.9:
                self.knowledge_accumulator[field].append(value)
    
    def _generate_pattern_key(self, entity_data: Dict[str, Any]) -> str:
        key_parts = []
        for field in ['hostname', 'environment', 'criticality', 'os_type']:
            if field in entity_data:
                key_parts.append(f"{field}:{entity_data[field]}")
        return '|'.join(key_parts)

class EnhancedClaudeLevelIntelligence:
    def __init__(self):
        self.confidence_system = GeniusConfidenceSystem()
        
    def calculate_true_confidence(self, entity_data: Dict[str, Any], concept_type: str,
                                  properties: Dict[str, Any], inferences: List[str],
                                  embeddings: Optional[np.ndarray] = None) -> Tuple[float, Dict[str, Any]]:
        
        return self.confidence_system.calculate_genius_confidence(
            entity_data, concept_type, properties, inferences, embeddings
        )