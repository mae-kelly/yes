#!/usr/bin/env python3

import re
import ipaddress
import numpy as np
from typing import List, Optional, Tuple, Dict, Set
from collections import Counter, defaultdict
import statistics
from datetime import datetime
import json
import hashlib

class SemanticEmbeddingMatcher:
    def __init__(self):
        self.embedding_cache = {}
        self.concept_vectors = self._initialize_concept_vectors()
        
    def _initialize_concept_vectors(self):
        return {
            'hostname': np.array([1.0, 0.8, 0.6, 0.4, 0.2]),
            'ip_address': np.array([0.2, 1.0, 0.7, 0.3, 0.1]),
            'infrastructure': np.array([0.6, 0.3, 1.0, 0.8, 0.4]),
            'security': np.array([0.4, 0.2, 0.7, 1.0, 0.9]),
            'business': np.array([0.3, 0.1, 0.4, 0.5, 1.0])
        }
    
    def get_semantic_similarity(self, text: str, concept: str) -> float:
        text_vector = self._text_to_vector(text)
        concept_vector = self.concept_vectors.get(concept, np.zeros(5))
        
        dot_product = np.dot(text_vector, concept_vector)
        norms = np.linalg.norm(text_vector) * np.linalg.norm(concept_vector)
        
        if norms == 0:
            return 0.0
        
        return dot_product / norms
    
    def _text_to_vector(self, text: str) -> np.ndarray:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        vector = np.random.rand(5)
        
        feature_weights = {
            'tech_terms': ['server', 'host', 'endpoint', 'device', 'machine'],
            'network_terms': ['ip', 'address', 'network', 'subnet', 'dns'],
            'security_terms': ['auth', 'security', 'access', 'credential', 'token'],
            'business_terms': ['customer', 'product', 'sales', 'revenue', 'user'],
            'infrastructure_terms': ['cloud', 'datacenter', 'region', 'zone', 'environment']
        }
        
        text_lower = text.lower()
        for i, (category, terms) in enumerate(feature_weights.items()):
            weight = sum(1 for term in terms if term in text_lower)
            vector[i] = weight / len(terms)
        
        self.embedding_cache[text_hash] = vector
        return vector

class AdaptiveLearningSystem:
    def __init__(self):
        self.pattern_success_rates = defaultdict(lambda: {'successes': 0, 'attempts': 0})
        self.field_confidence_history = defaultdict(list)
        self.learning_metadata = {
            'total_discoveries': 0,
            'accuracy_improvements': 0,
            'last_learning_update': None
        }
    
    def record_pattern_success(self, pattern: str, field_type: str, success: bool):
        key = f"{pattern}:{field_type}"
        self.pattern_success_rates[key]['attempts'] += 1
        if success:
            self.pattern_success_rates[key]['successes'] += 1
    
    def get_pattern_confidence(self, pattern: str, field_type: str) -> float:
        key = f"{pattern}:{field_type}"
        rates = self.pattern_success_rates[key]
        if rates['attempts'] == 0:
            return 0.5
        return rates['successes'] / rates['attempts']
    
    def update_field_confidence(self, field_type: str, confidence: float, validation_result: bool):
        self.field_confidence_history[field_type].append({
            'confidence': confidence,
            'validated': validation_result,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.field_confidence_history[field_type]) > 1000:
            self.field_confidence_history[field_type] = self.field_confidence_history[field_type][-500:]
    
    def get_adaptive_threshold(self, field_type: str) -> float:
        history = self.field_confidence_history[field_type]
        if len(history) < 10:
            return 0.3
        
        validated_confidences = [h['confidence'] for h in history if h['validated']]
        if not validated_confidences:
            return 0.3
        
        return max(0.1, min(0.8, statistics.mean(validated_confidences) - 0.1))

class KnowledgeGraph:
    def __init__(self):
        self.entities = {}
        self.relationships = {}
        self.entity_embeddings = {}
        self.relationship_weights = defaultdict(float)
    
    def add_entity(self, entity_id: str, entity_type: str, attributes: Dict):
        self.entities[entity_id] = {
            'type': entity_type,
            'attributes': attributes,
            'discovered_at': datetime.now().isoformat(),
            'confidence': attributes.get('confidence', 0.5)
        }
        self.entity_embeddings[entity_id] = self._compute_entity_embedding(attributes)
    
    def _compute_entity_embedding(self, attributes: Dict) -> np.ndarray:
        embedding = np.zeros(10)
        
        for i, (key, value) in enumerate(attributes.items()):
            if i >= 10:
                break
            if isinstance(value, (int, float)):
                embedding[i] = float(value)
            else:
                embedding[i] = hash(str(value)) % 1000 / 1000.0
        
        return embedding
    
    def find_similar_entities(self, entity_id: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        if entity_id not in self.entity_embeddings:
            return []
        
        target_embedding = self.entity_embeddings[entity_id]
        similarities = []
        
        for other_id, other_embedding in self.entity_embeddings.items():
            if other_id != entity_id:
                similarity = np.dot(target_embedding, other_embedding) / (
                    np.linalg.norm(target_embedding) * np.linalg.norm(other_embedding)
                )
                if similarity >= threshold:
                    similarities.append((other_id, similarity))
        
        return sorted(similarities, key=lambda x: x[1], reverse=True)
    
    def infer_relationships(self, entity_id: str) -> List[Dict]:
        similar_entities = self.find_similar_entities(entity_id)
        inferences = []
        
        for similar_id, similarity in similar_entities:
            inference = {
                'source': entity_id,
                'target': similar_id,
                'relationship_type': 'similar_context',
                'confidence': similarity,
                'evidence': f'Embedding similarity: {similarity:.3f}'
            }
            inferences.append(inference)
        
        return inferences

class ContextualReasoning:
    def __init__(self):
        self.business_context_patterns = {
            'production': ['prod', 'production', 'live', 'prd'],
            'development': ['dev', 'development', 'test', 'staging', 'uat'],
            'security': ['sec', 'security', 'auth', 'firewall', 'vpn'],
            'analytics': ['analytics', 'bi', 'data', 'warehouse', 'lake'],
            'finance': ['finance', 'accounting', 'billing', 'payment'],
            'operations': ['ops', 'operations', 'monitoring', 'infra']
        }
        
        self.inference_rules = [
            self._infer_environment_criticality,
            self._infer_data_sensitivity,
            self._infer_operational_importance,
            self._infer_compliance_requirements
        ]
    
    def analyze_business_context(self, text: str, metadata: Dict = None) -> Dict:
        text_lower = text.lower()
        context_scores = {}
        
        for context_type, patterns in self.business_context_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            if score > 0:
                context_scores[context_type] = score / len(patterns)
        
        primary_context = max(context_scores.items(), key=lambda x: x[1]) if context_scores else ('unknown', 0)
        
        inferences = []
        for rule in self.inference_rules:
            inference = rule(text, context_scores, metadata or {})
            if inference:
                inferences.append(inference)
        
        return {
            'primary_context': primary_context[0],
            'context_confidence': primary_context[1],
            'all_contexts': context_scores,
            'inferences': inferences
        }
    
    def _infer_environment_criticality(self, text: str, contexts: Dict, metadata: Dict) -> Optional[Dict]:
        if 'production' in contexts and contexts['production'] > 0.3:
            return {
                'type': 'environment_criticality',
                'value': 'high',
                'confidence': contexts['production'],
                'reasoning': 'Production environment indicators detected'
            }
        elif 'development' in contexts and contexts['development'] > 0.3:
            return {
                'type': 'environment_criticality',
                'value': 'low',
                'confidence': contexts['development'],
                'reasoning': 'Development environment indicators detected'
            }
        return None
    
    def _infer_data_sensitivity(self, text: str, contexts: Dict, metadata: Dict) -> Optional[Dict]:
        sensitive_indicators = ['customer', 'personal', 'financial', 'health', 'pii']
        text_lower = text.lower()
        
        sensitivity_score = sum(1 for indicator in sensitive_indicators if indicator in text_lower)
        if sensitivity_score > 0:
            return {
                'type': 'data_sensitivity',
                'value': 'high' if sensitivity_score > 2 else 'medium',
                'confidence': min(1.0, sensitivity_score / len(sensitive_indicators)),
                'reasoning': f'Found {sensitivity_score} sensitivity indicators'
            }
        return None
    
    def _infer_operational_importance(self, text: str, contexts: Dict, metadata: Dict) -> Optional[Dict]:
        critical_terms = ['critical', 'core', 'primary', 'main', 'essential']
        text_lower = text.lower()
        
        importance_score = sum(1 for term in critical_terms if term in text_lower)
        if importance_score > 0 or contexts.get('production', 0) > 0.5:
            return {
                'type': 'operational_importance',
                'value': 'high',
                'confidence': max(importance_score / len(critical_terms), contexts.get('production', 0)),
                'reasoning': 'Critical operational indicators found'
            }
        return None
    
    def _infer_compliance_requirements(self, text: str, contexts: Dict, metadata: Dict) -> Optional[Dict]:
        compliance_terms = ['compliance', 'audit', 'regulation', 'gdpr', 'hipaa', 'sox']
        text_lower = text.lower()
        
        compliance_score = sum(1 for term in compliance_terms if term in text_lower)
        if compliance_score > 0:
            return {
                'type': 'compliance_requirements',
                'value': 'required',
                'confidence': min(1.0, compliance_score / len(compliance_terms)),
                'reasoning': f'Compliance indicators detected: {compliance_score}'
            }
        return None

class PredictiveModeling:
    def __init__(self):
        self.asset_count_model = AssetCountPredictor()
        self.coverage_predictor = CoveragePredictor()
        self.performance_predictor = PerformancePredictor()
    
    def predict_discovery_outcomes(self, context: Dict) -> Dict:
        return {
            'estimated_assets': self.asset_count_model.predict(context),
            'expected_coverage': self.coverage_predictor.predict(context),
            'estimated_duration': self.performance_predictor.predict(context),
            'confidence_intervals': self._calculate_confidence_intervals(context)
        }
    
    def _calculate_confidence_intervals(self, context: Dict) -> Dict:
        dataset_count = context.get('dataset_count', 0)
        uncertainty = max(0.1, min(0.5, 1.0 / max(dataset_count, 1)))
        
        return {
            'asset_count': {'lower': 0.8, 'upper': 1.2},
            'coverage': {'lower': 1.0 - uncertainty, 'upper': 1.0},
            'duration': {'lower': 0.7, 'upper': 1.5}
        }

class AssetCountPredictor:
    def __init__(self):
        self.base_multipliers = {
            'small': 100,
            'medium': 500,
            'large': 2000,
            'enterprise': 10000
        }
        
        self.context_multipliers = {
            'production': 2.0,
            'development': 0.5,
            'security': 1.5,
            'analytics': 1.2
        }
    
    def predict(self, context: Dict) -> int:
        dataset_count = context.get('dataset_count', 0)
        table_count = context.get('table_count', 0)
        
        if dataset_count == 0:
            return 0
        
        scale = self._determine_scale(dataset_count, table_count)
        base_assets = self.base_multipliers[scale]
        
        business_context = context.get('business_context', {})
        multiplier = 1.0
        
        for ctx, mult in self.context_multipliers.items():
            if ctx in business_context:
                multiplier *= mult
        
        return int(base_assets * multiplier * (dataset_count / 10))
    
    def _determine_scale(self, dataset_count: int, table_count: int) -> str:
        total_objects = dataset_count + (table_count / 10)
        
        if total_objects < 10:
            return 'small'
        elif total_objects < 50:
            return 'medium'
        elif total_objects < 200:
            return 'large'
        else:
            return 'enterprise'

class CoveragePredictor:
    def __init__(self):
        self.base_coverage_rates = {
            'hostname_fields': 0.8,
            'ip_fields': 0.6,
            'infrastructure_fields': 0.4,
            'security_fields': 0.3,
            'business_fields': 0.2
        }
    
    def predict(self, context: Dict) -> float:
        field_types_present = context.get('detected_field_types', [])
        
        if not field_types_present:
            return 0.3
        
        coverage_scores = []
        for field_type in field_types_present:
            base_rate = self.base_coverage_rates.get(field_type, 0.1)
            coverage_scores.append(base_rate)
        
        return min(0.95, max(0.1, statistics.mean(coverage_scores)))

class PerformancePredictor:
    def __init__(self):
        self.base_processing_times = {
            'table_analysis': 2.0,
            'hostname_extraction': 5.0,
            'field_enrichment': 10.0,
            'data_fusion': 3.0
        }
    
    def predict(self, context: Dict) -> float:
        table_count = context.get('table_count', 0)
        dataset_count = context.get('dataset_count', 0)
        estimated_assets = context.get('estimated_assets', 0)
        
        total_time = 0
        
        total_time += self.base_processing_times['table_analysis'] * table_count / 10
        total_time += self.base_processing_times['hostname_extraction'] * dataset_count / 5
        total_time += self.base_processing_times['field_enrichment'] * estimated_assets / 1000
        total_time += self.base_processing_times['data_fusion']
        
        parallelism_factor = context.get('parallel_workers', 16) / 16
        return max(30, total_time / parallelism_factor)

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
        
        self.semantic_matcher = SemanticEmbeddingMatcher()
        self.adaptive_learner = AdaptiveLearningSystem()
        self.knowledge_graph = KnowledgeGraph()
        self.contextual_reasoning = ContextualReasoning()
        self.predictive_model = PredictiveModeling()
        
        self.intelligence_metadata = {
            'learning_enabled': True,
            'semantic_matching_enabled': True,
            'predictive_modeling_enabled': True,
            'contextual_reasoning_enabled': True
        }
    
    def analyze_column_intelligently(self, column_name: str, sample_values: List[str], 
                                   table_context: Dict = None) -> Optional[Tuple[str, float, Dict[str, any]]]:
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
        
        context_analysis = {}
        if table_context:
            context_analysis = self.contextual_reasoning.analyze_business_context(
                f"{column_name} {table_context.get('table_name', '')}", table_context
            )
        
        best_match = None
        best_score = 0.0
        best_metadata = {}
        
        for field_type, config in self.semantic_patterns.items():
            semantic_score = self._calculate_enhanced_semantic_score(
                column_name, config['keywords'], context_analysis
            )
            
            if semantic_score < 0.1:
                continue
            
            validation_score = self._validate_content_intelligently(field_type, cleaned_values, config['validators'])
            if validation_score < 0.3:
                continue
            
            adaptive_threshold = self.adaptive_learner.get_adaptive_threshold(field_type)
            semantic_embedding_score = self.semantic_matcher.get_semantic_similarity(column_name, field_type)
            
            combined_score = (
                semantic_score * 0.3 + 
                validation_score * 0.4 + 
                semantic_embedding_score * 0.2 +
                (context_analysis.get('context_confidence', 0) * 0.1)
            )
            
            if combined_score > best_score and combined_score > adaptive_threshold:
                best_match = field_type
                best_score = combined_score
                best_metadata = {
                    'semantic_score': semantic_score,
                    'validation_score': validation_score,
                    'embedding_score': semantic_embedding_score,
                    'context_score': context_analysis.get('context_confidence', 0),
                    'adaptive_threshold': adaptive_threshold,
                    'sample_analysis': self._analyze_sample_patterns(cleaned_values),
                    'data_quality': self._assess_data_quality(cleaned_values),
                    'business_context': context_analysis,
                    'confidence_factors': {
                        'pattern_history': self.adaptive_learner.get_pattern_confidence(column_name, field_type),
                        'semantic_strength': semantic_score,
                        'validation_strength': validation_score
                    }
                }
        
        if best_match:
            self.knowledge_graph.add_entity(
                f"column:{column_name}", 
                best_match, 
                {'confidence': best_score, 'table_context': table_context}
            )
            
            self.adaptive_learner.record_pattern_success(column_name, best_match, True)
        
        result = (best_match, best_score, best_metadata) if best_match else None
        self.column_analysis_cache[cache_key] = result
        return result
    
    def _calculate_enhanced_semantic_score(self, column_name: str, keywords: List[str], 
                                         context_analysis: Dict) -> float:
        base_score = self._calculate_semantic_score(column_name, keywords)
        
        context_boost = 0.0
        if context_analysis:
            primary_context = context_analysis.get('primary_context', '')
            if any(keyword in primary_context for keyword in keywords):
                context_boost = context_analysis.get('context_confidence', 0) * 0.2
        
        return min(1.0, base_score + context_boost)
    
    def predict_field_relationships(self, discovered_fields: Dict[str, Any]) -> List[Dict]:
        relationships = []
        
        for field1, metadata1 in discovered_fields.items():
            for field2, metadata2 in discovered_fields.items():
                if field1 != field2:
                    relationship_strength = self._calculate_field_relationship_strength(
                        field1, metadata1, field2, metadata2
                    )
                    
                    if relationship_strength > 0.6:
                        relationships.append({
                            'field1': field1,
                            'field2': field2,
                            'relationship_type': 'semantic_correlation',
                            'strength': relationship_strength,
                            'evidence': f'Semantic correlation: {relationship_strength:.3f}'
                        })
        
        return relationships
    
    def _calculate_field_relationship_strength(self, field1: str, meta1: Dict, 
                                             field2: str, meta2: Dict) -> float:
        semantic_similarity = self.semantic_matcher.get_semantic_similarity(field1, field2)
        
        context_similarity = 0.0
        if 'business_context' in meta1 and 'business_context' in meta2:
            ctx1 = meta1['business_context'].get('primary_context', '')
            ctx2 = meta2['business_context'].get('primary_context', '')
            context_similarity = 1.0 if ctx1 == ctx2 and ctx1 != 'unknown' else 0.0
        
        confidence_similarity = abs(meta1.get('confidence', 0) - meta2.get('confidence', 0))
        confidence_factor = 1.0 - confidence_similarity
        
        return (semantic_similarity * 0.5 + context_similarity * 0.3 + confidence_factor * 0.2)
    
    def generate_discovery_insights(self, discovery_results: Dict) -> List[Dict]:
        insights = []
        
        field_distribution = defaultdict(int)
        confidence_scores = []
        
        for result in discovery_results.values():
            if isinstance(result, dict):
                field_type = result.get('field_type')
                confidence = result.get('confidence', 0)
                
                if field_type:
                    field_distribution[field_type] += 1
                    confidence_scores.append(confidence)
        
        if confidence_scores:
            avg_confidence = statistics.mean(confidence_scores)
            insights.append({
                'type': 'confidence_analysis',
                'average_confidence': avg_confidence,
                'confidence_distribution': {
                    'high': sum(1 for c in confidence_scores if c > 0.8),
                    'medium': sum(1 for c in confidence_scores if 0.5 <= c <= 0.8),
                    'low': sum(1 for c in confidence_scores if c < 0.5)
                },
                'recommendation': self._generate_confidence_recommendation(avg_confidence)
            })
        
        if field_distribution:
            most_common_field = max(field_distribution.items(), key=lambda x: x[1])
            insights.append({
                'type': 'field_distribution',
                'most_common_field': most_common_field[0],
                'field_counts': dict(field_distribution),
                'coverage_assessment': self._assess_field_coverage(field_distribution)
            })
        
        return insights
    
    def _generate_confidence_recommendation(self, avg_confidence: float) -> str:
        if avg_confidence > 0.8:
            return "Excellent field detection confidence. Consider enabling strict validation."
        elif avg_confidence > 0.6:
            return "Good confidence levels. Monitor for improvement opportunities."
        elif avg_confidence > 0.4:
            return "Moderate confidence. Consider expanding semantic patterns."
        else:
            return "Low confidence detected. Review validation logic and expand training data."
    
    def _assess_field_coverage(self, field_distribution: Dict) -> Dict:
        total_fields = sum(field_distribution.values())
        critical_fields = ['hostname', 'ip_address', 'infrastructure_type', 'system_classification']
        
        coverage_score = sum(field_distribution.get(field, 0) for field in critical_fields) / max(total_fields, 1)
        
        return {
            'coverage_score': coverage_score,
            'missing_critical_fields': [f for f in critical_fields if f not in field_distribution],
            'coverage_assessment': 'excellent' if coverage_score > 0.8 else 
                                 'good' if coverage_score > 0.6 else 
                                 'needs_improvement'
        }
    
    def find_optimal_hostname_column(self, columns_with_samples: Dict[str, List[str]]) -> Optional[Tuple[str, float]]:
        candidates = []
        
        for column_name, samples in columns_with_samples.items():
            analysis = self.analyze_column_intelligently(column_name, samples)
            
            if analysis and analysis[0] in ['hostname', 'fqdn']:
                field_type, confidence, metadata = analysis
                
                hostname_specific_score = self._calculate_hostname_specificity(column_name, samples)
                semantic_boost = self.semantic_matcher.get_semantic_similarity(column_name, 'hostname')
                
                final_score = confidence * hostname_specific_score * (1 + semantic_boost * 0.2)
                
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
    
    def intelligently_categorize_all_columns(self, all_columns: List[str], 
                                           sample_data: Dict[str, List[str]] = None,
                                           table_context: Dict = None) -> Dict[str, List[Tuple[str, float]]]:
        categorized = {}
        
        for column in all_columns:
            samples = sample_data.get(column, []) if sample_data else []
            analysis = self.analyze_column_intelligently(column, samples, table_context)
            
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
        
        base_score = valid_count / total_count if total_count > 0 else 0.0
        
        adaptive_adjustment = self.adaptive_learner.get_pattern_confidence('validation', field_type)
        adjusted_score = base_score * 0.8 + adaptive_adjustment * 0.2
        
        return min(1.0, adjusted_score)
    
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
        
        semantic_boost = self.semantic_matcher.get_semantic_similarity(column_name, 'hostname')
        specificity_score *= (1 + semantic_boost * 0.3)
        
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
        
        patterns['pattern_complexity'] = self._calculate_pattern_complexity(values)
        patterns['semantic_indicators'] = self._extract_semantic_indicators(values)
        
        return patterns
    
    def _calculate_pattern_complexity(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        unique_chars = set(''.join(values))
        char_types = {
            'letters': sum(1 for c in unique_chars if c.isalpha()),
            'digits': sum(1 for c in unique_chars if c.isdigit()),
            'special': sum(1 for c in unique_chars if not c.isalnum())
        }
        
        complexity = (
            (char_types['letters'] / 26) * 0.4 +
            (char_types['digits'] / 10) * 0.3 +
            (char_types['special'] / 20) * 0.3
        )
        
        return min(1.0, complexity)
    
    def _extract_semantic_indicators(self, values: List[str]) -> List[str]:
        indicators = []
        
        common_patterns = {
            'server_pattern': r'(srv|server|host)\d+',
            'ip_pattern': r'\d+\.\d+\.\d+\.\d+',
            'mac_pattern': r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}',
            'domain_pattern': r'[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}',
            'uuid_pattern': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        }
        
        for pattern_name, pattern in common_patterns.items():
            matches = sum(1 for value in values if re.search(pattern, value, re.IGNORECASE))
            if matches > len(values) * 0.3:
                indicators.append(pattern_name.replace('_pattern', ''))
        
        return indicators
    
    def _assess_data_quality(self, values: List[str]) -> Dict[str, any]:
        if not values:
            return {'score': 0.0}
        
        quality_metrics = {
            'completeness': len(values) / max(len(values), 1),
            'consistency': len(set(len(v) for v in values)) <= 3,
            'uniqueness': len(set(values)) / len(values),
            'validity': sum(1 for v in values if len(v.strip()) > 0) / len(values)
        }
        
        format_consistency = self._assess_format_consistency(values)
        quality_metrics['format_consistency'] = format_consistency
        
        overall_score = sum(quality_metrics.values()) / len(quality_metrics)
        
        quality_assessment = {
            'score': overall_score,
            'metrics': quality_metrics,
            'recommendations': self._generate_quality_recommendations(quality_metrics)
        }
        
        return quality_assessment
    
    def _assess_format_consistency(self, values: List[str]) -> float:
        if len(values) < 2:
            return 1.0
        
        format_patterns = []
        for value in values:
            pattern = re.sub(r'[a-zA-Z]', 'A', value)
            pattern = re.sub(r'[0-9]', '9', pattern)
            format_patterns.append(pattern)
        
        unique_patterns = len(set(format_patterns))
        consistency_score = 1.0 - (unique_patterns - 1) / max(len(values) - 1, 1)
        
        return max(0.0, consistency_score)
    
    def _generate_quality_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        recommendations = []
        
        if metrics['completeness'] < 0.9:
            recommendations.append("Improve data completeness - consider validation rules")
        
        if metrics['consistency'] < 0.7:
            recommendations.append("Enhance data consistency - standardize formats")
        
        if metrics['uniqueness'] < 0.5:
            recommendations.append("Review uniqueness constraints - possible duplicates")
        
        if metrics['validity'] < 0.8:
            recommendations.append("Strengthen validation logic - invalid entries detected")
        
        if metrics.get('format_consistency', 1.0) < 0.6:
            recommendations.append("Standardize data formats for better consistency")
        
        return recommendations
    
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