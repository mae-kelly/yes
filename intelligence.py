import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Set
import hashlib
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
import networkx as nx
from scipy.spatial.distance import cosine
import json

@dataclass
class SemanticConcept:
    concept_id: str
    concept_type: str
    properties: Dict[str, Any]
    relationships: Set[str]
    confidence: float
    evidence: List[Dict[str, Any]]
    inferences: List[str]
    
class ConceptualKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.concepts = self._initialize_security_ontology()
        self.reasoning_chains = []
        self.inference_cache = {}
        
    def _initialize_security_ontology(self):
        ontology = {
            'Asset': {
                'is_a': 'Entity',
                'subtypes': ['Host', 'Network_Device', 'Application', 'Service', 'Container', 'Cloud_Resource'],
                'properties': ['identifier', 'location', 'ownership', 'criticality', 'lifecycle_state'],
                'relationships': ['belongs_to', 'connects_to', 'depends_on', 'managed_by', 'protected_by'],
                'inference_rules': [
                    lambda x: 'requires_protection' if x.get('criticality') == 'high' else None,
                    lambda x: 'legacy_system' if x.get('lifecycle_state') == 'deprecated' else None
                ]
            },
            'Host': {
                'is_a': 'Asset',
                'subtypes': ['Server', 'Workstation', 'Virtual_Machine', 'Container_Host'],
                'identifiers': ['hostname', 'fqdn', 'ip_address', 'mac_address', 'asset_tag', 'serial_number'],
                'attributes': ['os_type', 'os_version', 'patch_level', 'location', 'owner', 'department'],
                'behaviors': ['generates_logs', 'has_vulnerabilities', 'runs_services', 'processes_data'],
                'security_properties': ['encryption_status', 'compliance_state', 'last_scan', 'risk_score'],
                'relationships': ['member_of_domain', 'located_in_subnet', 'managed_by_system', 'monitored_by'],
                'inference_rules': [
                    lambda x: 'windows_domain_member' if 'domain' in x.get('fqdn', '') else None,
                    lambda x: 'cloud_hosted' if any(cloud in str(x.get('hostname', '')) for cloud in ['aws', 'azure', 'gcp']) else None,
                    lambda x: 'production_system' if 'prod' in str(x.get('hostname', '')).lower() else None
                ]
            },
            'Security_Event': {
                'is_a': 'Event',
                'components': ['timestamp', 'source', 'target', 'action', 'outcome', 'severity'],
                'context': ['threat_level', 'attack_stage', 'confidence', 'detection_method'],
                'relationships': ['affects_asset', 'part_of_campaign', 'triggers_response', 'correlated_with'],
                'patterns': ['attack_pattern', 'ioc_matches', 'behavioral_anomaly'],
                'inference_rules': [
                    lambda x: 'potential_breach' if x.get('severity') == 'critical' and x.get('outcome') == 'success' else None,
                    lambda x: 'reconnaissance' if x.get('attack_stage') == 'initial' else None
                ]
            },
            'Network': {
                'is_a': 'Infrastructure',
                'properties': ['network_range', 'vlan_id', 'zone', 'gateway', 'dns_servers'],
                'security_attributes': ['firewall_rules', 'access_controls', 'monitoring_status'],
                'relationships': ['contains_hosts', 'connected_to', 'routed_through', 'isolated_from'],
                'inference_rules': [
                    lambda x: 'dmz' if 'dmz' in str(x.get('zone', '')).lower() else None,
                    lambda x: 'internal_network' if x.get('network_range', '').startswith('10.') else None
                ]
            },
            'Vulnerability': {
                'is_a': 'Risk',
                'properties': ['cve_id', 'cvss_score', 'description', 'affected_systems', 'remediation'],
                'relationships': ['affects', 'exploited_by', 'mitigated_by', 'detected_on'],
                'inference_rules': [
                    lambda x: 'critical_risk' if float(x.get('cvss_score', 0)) >= 9.0 else None,
                    lambda x: 'actively_exploited' if x.get('exploit_available') else None
                ]
            }
        }
        
        for concept_type, definition in ontology.items():
            self.graph.add_node(concept_type, **definition)
            if 'is_a' in definition:
                self.graph.add_edge(definition['is_a'], concept_type, relationship='subtype')
            for subtype in definition.get('subtypes', []):
                self.graph.add_edge(concept_type, subtype, relationship='subtype')
        
        return ontology
    
    def understand_entity(self, entity_data: Dict[str, Any]) -> SemanticConcept:
        concept_type = self._classify_entity_type(entity_data)
        properties = self._extract_semantic_properties(entity_data, concept_type)
        relationships = self._discover_relationships(entity_data, concept_type)
        inferences = self._apply_inference_rules(entity_data, concept_type)
        
        concept = SemanticConcept(
            concept_id=self._generate_concept_id(entity_data),
            concept_type=concept_type,
            properties=properties,
            relationships=relationships,
            confidence=self._calculate_understanding_confidence(entity_data, concept_type),
            evidence=[{'data': entity_data, 'source': 'direct_observation'}],
            inferences=inferences
        )
        
        self._update_knowledge_graph(concept)
        return concept
    
    def _classify_entity_type(self, entity_data: Dict[str, Any]) -> str:
        scores = {}
        
        for concept_type, definition in self.concepts.items():
            score = 0.0
            
            if 'identifiers' in definition:
                for identifier in definition['identifiers']:
                    if identifier in entity_data:
                        score += 1.0
            
            if 'properties' in definition:
                for prop in definition['properties']:
                    if prop in entity_data:
                        score += 0.5
            
            if 'patterns' in definition:
                for pattern in definition['patterns']:
                    if self._matches_pattern(entity_data, pattern):
                        score += 0.7
            
            scores[concept_type] = score
        
        return max(scores, key=scores.get) if scores else 'Unknown'
    
    def _extract_semantic_properties(self, entity_data: Dict[str, Any], concept_type: str) -> Dict[str, Any]:
        properties = {}
        definition = self.concepts.get(concept_type, {})
        
        for key, value in entity_data.items():
            semantic_key = self._map_to_semantic_property(key, concept_type)
            properties[semantic_key] = {
                'value': value,
                'confidence': self._assess_property_confidence(key, value, concept_type),
                'source': 'observed',
                'semantic_type': self._infer_semantic_type(value)
            }
        
        for required_prop in definition.get('properties', []):
            if required_prop not in properties:
                inferred_value = self._infer_property(required_prop, entity_data, concept_type)
                if inferred_value:
                    properties[required_prop] = {
                        'value': inferred_value,
                        'confidence': 0.7,
                        'source': 'inferred',
                        'semantic_type': self._infer_semantic_type(inferred_value)
                    }
        
        return properties
    
    def _discover_relationships(self, entity_data: Dict[str, Any], concept_type: str) -> Set[str]:
        relationships = set()
        definition = self.concepts.get(concept_type, {})
        
        for rel_type in definition.get('relationships', []):
            if self._has_relationship_evidence(entity_data, rel_type):
                relationships.add(rel_type)
        
        implicit_relationships = self._discover_implicit_relationships(entity_data, concept_type)
        relationships.update(implicit_relationships)
        
        return relationships
    
    def _apply_inference_rules(self, entity_data: Dict[str, Any], concept_type: str) -> List[str]:
        inferences = []
        definition = self.concepts.get(concept_type, {})
        
        for rule in definition.get('inference_rules', []):
            inference = rule(entity_data)
            if inference:
                inferences.append(inference)
        
        chain_inferences = self._apply_reasoning_chains(entity_data, concept_type, inferences)
        inferences.extend(chain_inferences)
        
        return inferences
    
    def _apply_reasoning_chains(self, entity_data: Dict[str, Any], concept_type: str, initial_inferences: List[str]) -> List[str]:
        additional_inferences = []
        
        if concept_type == 'Host' and 'production_system' in initial_inferences:
            if not entity_data.get('edr_coverage'):
                additional_inferences.append('security_gap_critical')
            if not entity_data.get('logging_enabled'):
                additional_inferences.append('visibility_gap_high')
        
        if concept_type == 'Security_Event' and 'potential_breach' in initial_inferences:
            additional_inferences.append('requires_immediate_response')
            additional_inferences.append('trigger_incident_response')
        
        if 'cloud_hosted' in initial_inferences and 'legacy_system' in initial_inferences:
            additional_inferences.append('migration_candidate')
        
        return additional_inferences
    
    def _update_knowledge_graph(self, concept: SemanticConcept):
        self.graph.add_node(concept.concept_id, concept=concept)
        
        for relationship in concept.relationships:
            related_concepts = self._find_related_concepts(concept, relationship)
            for related_id in related_concepts:
                self.graph.add_edge(concept.concept_id, related_id, relationship=relationship)
    
    def _find_related_concepts(self, concept: SemanticConcept, relationship: str) -> List[str]:
        related = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_id != concept.concept_id and 'concept' in node_data:
                other_concept = node_data['concept']
                if self._concepts_are_related(concept, other_concept, relationship):
                    related.append(node_id)
        
        return related
    
    def _concepts_are_related(self, concept1: SemanticConcept, concept2: SemanticConcept, relationship: str) -> bool:
        if relationship == 'belongs_to':
            return concept1.properties.get('owner') == concept2.properties.get('identifier')
        elif relationship == 'located_in_subnet':
            return self._same_subnet(concept1.properties.get('ip_address'), concept2.properties.get('network_range'))
        elif relationship == 'managed_by':
            return concept1.properties.get('management_system') == concept2.properties.get('system_name')
        return False
    
    def _matches_pattern(self, data: Dict[str, Any], pattern: str) -> bool:
        return False
    
    def _map_to_semantic_property(self, key: str, concept_type: str) -> str:
        return key
    
    def _assess_property_confidence(self, key: str, value: Any, concept_type: str) -> float:
        return 0.9
    
    def _infer_semantic_type(self, value: Any) -> str:
        return type(value).__name__
    
    def _infer_property(self, prop: str, data: Dict[str, Any], concept_type: str) -> Any:
        return None
    
    def _has_relationship_evidence(self, data: Dict[str, Any], rel_type: str) -> bool:
        return False
    
    def _discover_implicit_relationships(self, data: Dict[str, Any], concept_type: str) -> Set[str]:
        return set()
    
    def _generate_concept_id(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def _calculate_understanding_confidence(self, data: Dict[str, Any], concept_type: str) -> float:
        return 0.85
    
    def _same_subnet(self, ip1: str, network_range: str) -> bool:
        return False

class SemanticReasoningEngine:
    def __init__(self, knowledge_graph: ConceptualKnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.reasoning_methods = {
            'deductive': self._deductive_reasoning,
            'inductive': self._inductive_reasoning,
            'abductive': self._abductive_reasoning,
            'analogical': self._analogical_reasoning
        }
        self.reasoning_history = []
        
    def reason_about_data(self, query_context: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        query_understanding = self._understand_query(query_context)
        relevant_concepts = self._gather_relevant_concepts(query_understanding, data)
        
        reasoning_results = {}
        for method_name, method_func in self.reasoning_methods.items():
            reasoning_results[method_name] = method_func(relevant_concepts, query_understanding)
        
        combined_reasoning = self._combine_reasoning_results(reasoning_results)
        confidence = self._assess_reasoning_confidence(combined_reasoning)
        explanation = self._generate_explanation(combined_reasoning, query_understanding)
        
        result = {
            'conclusion': combined_reasoning['conclusion'],
            'confidence': confidence,
            'explanation': explanation,
            'evidence': combined_reasoning['evidence'],
            'reasoning_chain': combined_reasoning['chain'],
            'alternatives': combined_reasoning.get('alternatives', [])
        }
        
        self.reasoning_history.append(result)
        return result
    
    def _understand_query(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'intent': query_context.get('intent', 'analyze'),
            'target': query_context.get('target', 'unknown'),
            'constraints': query_context.get('constraints', []),
            'expected_output': query_context.get('expected_output', 'classification')
        }
    
    def _gather_relevant_concepts(self, query: Dict[str, Any], data: Dict[str, Any]) -> List[SemanticConcept]:
        concepts = []
        
        primary_concept = self.knowledge_graph.understand_entity(data)
        concepts.append(primary_concept)
        
        for neighbor in self.knowledge_graph.graph.neighbors(primary_concept.concept_id):
            if 'concept' in self.knowledge_graph.graph.nodes[neighbor]:
                concepts.append(self.knowledge_graph.graph.nodes[neighbor]['concept'])
        
        return concepts
    
    def _deductive_reasoning(self, concepts: List[SemanticConcept], query: Dict[str, Any]) -> Dict[str, Any]:
        conclusions = []
        
        for concept in concepts:
            if concept.concept_type == 'Host':
                if 'production_system' in concept.inferences and not concept.properties.get('edr_coverage'):
                    conclusions.append({
                        'statement': f"Host {concept.properties.get('hostname')} is a production system without EDR coverage",
                        'certainty': 1.0,
                        'rule': "production_systems_require_edr"
                    })
                
                if concept.properties.get('os_type') == 'Windows' and 'domain' in str(concept.properties.get('fqdn', '')):
                    conclusions.append({
                        'statement': f"Host {concept.properties.get('hostname')} is a Windows domain member",
                        'certainty': 0.95,
                        'rule': "windows_fqdn_pattern"
                    })
        
        return {'conclusions': conclusions, 'method': 'deductive'}
    
    def _inductive_reasoning(self, concepts: List[SemanticConcept], query: Dict[str, Any]) -> Dict[str, Any]:
        patterns = defaultdict(list)
        
        for concept in concepts:
            for inference in concept.inferences:
                patterns[inference].append(concept.concept_id)
        
        generalizations = []
        for pattern, instances in patterns.items():
            if len(instances) >= 3:
                generalizations.append({
                    'pattern': pattern,
                    'confidence': min(0.9, len(instances) / 10),
                    'instances': instances
                })
        
        return {'generalizations': generalizations, 'method': 'inductive'}
    
    def _abductive_reasoning(self, concepts: List[SemanticConcept], query: Dict[str, Any]) -> Dict[str, Any]:
        best_explanations = []
        
        for concept in concepts:
            if concept.concept_type == 'Security_Event':
                possible_causes = self._generate_possible_causes(concept)
                best_cause = max(possible_causes, key=lambda x: x['likelihood']) if possible_causes else None
                if best_cause:
                    best_explanations.append(best_cause)
        
        return {'explanations': best_explanations, 'method': 'abductive'}
    
    def _analogical_reasoning(self, concepts: List[SemanticConcept], query: Dict[str, Any]) -> Dict[str, Any]:
        analogies = []
        
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                similarity = self._calculate_concept_similarity(concept1, concept2)
                if similarity > 0.7:
                    analogies.append({
                        'source': concept1.concept_id,
                        'target': concept2.concept_id,
                        'similarity': similarity,
                        'shared_properties': self._get_shared_properties(concept1, concept2)
                    })
        
        return {'analogies': analogies, 'method': 'analogical'}
    
    def _combine_reasoning_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        combined = {
            'conclusion': None,
            'evidence': [],
            'chain': [],
            'alternatives': []
        }
        
        all_conclusions = []
        
        if 'deductive' in results and results['deductive']['conclusions']:
            all_conclusions.extend(results['deductive']['conclusions'])
            combined['chain'].append(('deductive', results['deductive']['conclusions']))
        
        if 'inductive' in results and results['inductive']['generalizations']:
            for gen in results['inductive']['generalizations']:
                all_conclusions.append({
                    'statement': f"Pattern detected: {gen['pattern']}",
                    'certainty': gen['confidence']
                })
            combined['chain'].append(('inductive', results['inductive']['generalizations']))
        
        if 'abductive' in results and results['abductive']['explanations']:
            combined['alternatives'] = results['abductive']['explanations']
            combined['chain'].append(('abductive', results['abductive']['explanations']))
        
        if all_conclusions:
            combined['conclusion'] = max(all_conclusions, key=lambda x: x['certainty'])
            combined['evidence'] = all_conclusions
        
        return combined
    
    def _assess_reasoning_confidence(self, reasoning: Dict[str, Any]) -> float:
        if not reasoning['conclusion']:
            return 0.0
        
        base_confidence = reasoning['conclusion'].get('certainty', 0.5)
        evidence_factor = min(1.0, len(reasoning['evidence']) / 5)
        chain_factor = min(1.0, len(reasoning['chain']) / 3)
        
        return base_confidence * (0.6 + 0.2 * evidence_factor + 0.2 * chain_factor)
    
    def _generate_explanation(self, reasoning: Dict[str, Any], query: Dict[str, Any]) -> str:
        if not reasoning['conclusion']:
            return "No conclusion could be drawn from the available data."
        
        explanation_parts = [
            f"Based on {query['intent']} analysis:",
            f"Primary conclusion: {reasoning['conclusion']['statement']}"
        ]
        
        if reasoning['chain']:
            explanation_parts.append(f"Reasoning methods used: {', '.join([c[0] for c in reasoning['chain']])}")
        
        if reasoning['evidence']:
            explanation_parts.append(f"Supporting evidence: {len(reasoning['evidence'])} pieces")
        
        if reasoning['alternatives']:
            explanation_parts.append(f"Alternative explanations considered: {len(reasoning['alternatives'])}")
        
        return " ".join(explanation_parts)
    
    def _generate_possible_causes(self, event: SemanticConcept) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_concept_similarity(self, c1: SemanticConcept, c2: SemanticConcept) -> float:
        if c1.concept_type != c2.concept_type:
            return 0.0
        
        shared_props = len(set(c1.properties.keys()) & set(c2.properties.keys()))
        total_props = len(set(c1.properties.keys()) | set(c2.properties.keys()))
        
        return shared_props / total_props if total_props > 0 else 0.0
    
    def _get_shared_properties(self, c1: SemanticConcept, c2: SemanticConcept) -> List[str]:
        return list(set(c1.properties.keys()) & set(c2.properties.keys()))

class MentalModelBuilder:
    def __init__(self, knowledge_graph: ConceptualKnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.mental_models = {}
        
    def build_table_mental_model(self, table_name: str, columns: List[str], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        table_purpose = self._infer_table_purpose(table_name, columns, sample_data)
        logical_model = self._build_logical_model(columns, sample_data, table_purpose)
        implicit_relationships = self._discover_implicit_relationships(logical_model)
        predictive_model = self._build_predictive_model(logical_model, implicit_relationships)
        semantic_constraints = self._derive_semantic_constraints(logical_model)
        
        mental_model = {
            'table_name': table_name,
            'purpose': table_purpose,
            'logical_structure': logical_model,
            'relationships': implicit_relationships,
            'predictive_capabilities': predictive_model,
            'constraints': semantic_constraints,
            'confidence': self._calculate_model_confidence(logical_model)
        }
        
        self.mental_models[table_name] = mental_model
        return mental_model
    
    def _infer_table_purpose(self, table_name: str, columns: List[str], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        purpose_indicators = {
            'event_logging': 0,
            'entity_tracking': 0,
            'monitoring': 0,
            'configuration': 0,
            'audit': 0,
            'inventory': 0
        }
        
        table_lower = table_name.lower()
        columns_lower = [c.lower() for c in columns]
        
        if any(word in table_lower for word in ['log', 'event', 'alert', 'incident']):
            purpose_indicators['event_logging'] += 2
        
        if any(word in columns_lower for word in ['timestamp', 'datetime', 'created_at', 'event_time']):
            purpose_indicators['event_logging'] += 1
            purpose_indicators['audit'] += 1
        
        if any(word in columns_lower for word in ['hostname', 'device_id', 'asset_id', 'server_name']):
            purpose_indicators['entity_tracking'] += 2
            purpose_indicators['inventory'] += 1
        
        if any(word in columns_lower for word in ['metric', 'value', 'count', 'average', 'sum']):
            purpose_indicators['monitoring'] += 2
        
        if any(word in columns_lower for word in ['config', 'setting', 'parameter', 'option']):
            purpose_indicators['configuration'] += 2
        
        if any(word in columns_lower for word in ['user', 'action', 'change', 'modified_by']):
            purpose_indicators['audit'] += 2
        
        primary_purpose = max(purpose_indicators, key=purpose_indicators.get)
        
        return {
            'primary': primary_purpose,
            'secondary': [k for k, v in purpose_indicators.items() if v > 0 and k != primary_purpose],
            'confidence': purpose_indicators[primary_purpose] / sum(purpose_indicators.values()) if sum(purpose_indicators.values()) > 0 else 0
        }
    
    def _build_logical_model(self, columns: List[str], sample_data: List[Dict[str, Any]], purpose: Dict[str, Any]) -> Dict[str, Any]:
        model = {
            'entities': [],
            'attributes': [],
            'identifiers': [],
            'temporal_fields': [],
            'metrics': [],
            'relationships': []
        }
        
        for column in columns:
            column_lower = column.lower()
            
            if any(id_word in column_lower for id_word in ['id', 'key', 'uuid', 'guid']):
                model['identifiers'].append(column)
            elif any(time_word in column_lower for time_word in ['time', 'date', 'timestamp']):
                model['temporal_fields'].append(column)
            elif any(metric_word in column_lower for metric_word in ['count', 'sum', 'avg', 'max', 'min']):
                model['metrics'].append(column)
            elif any(entity_word in column_lower for entity_word in ['host', 'user', 'device', 'system']):
                model['entities'].append(column)
            else:
                model['attributes'].append(column)
        
        if sample_data:
            model['data_characteristics'] = self._analyze_data_characteristics(sample_data)
        
        return model
    
    def _discover_implicit_relationships(self, logical_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        relationships = []
        
        for entity in logical_model['entities']:
            for identifier in logical_model['identifiers']:
                if entity != identifier:
                    relationships.append({
                        'type': 'entity_identifier',
                        'from': entity,
                        'to': identifier,
                        'confidence': 0.8
                    })
        
        for temporal in logical_model['temporal_fields']:
            for metric in logical_model['metrics']:
                relationships.append({
                    'type': 'time_series',
                    'from': temporal,
                    'to': metric,
                    'confidence': 0.7
                })
        
        return relationships
    
    def _build_predictive_model(self, logical_model: Dict[str, Any], relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'can_identify_entities': len(logical_model['identifiers']) > 0,
            'can_track_over_time': len(logical_model['temporal_fields']) > 0,
            'can_measure_metrics': len(logical_model['metrics']) > 0,
            'can_establish_relationships': len(relationships) > 0,
            'predictable_patterns': self._identify_predictable_patterns(logical_model)
        }
    
    def _derive_semantic_constraints(self, logical_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        constraints = []
        
        if logical_model['identifiers']:
            constraints.append({
                'type': 'uniqueness',
                'fields': logical_model['identifiers'],
                'constraint': 'must_be_unique'
            })
        
        if logical_model['temporal_fields']:
            constraints.append({
                'type': 'temporal_ordering',
                'fields': logical_model['temporal_fields'],
                'constraint': 'chronological_order'
            })
        
        return constraints
    
    def _calculate_model_confidence(self, logical_model: Dict[str, Any]) -> float:
        factors = [
            len(logical_model['identifiers']) > 0,
            len(logical_model['entities']) > 0,
            len(logical_model['temporal_fields']) > 0,
            len(logical_model['attributes']) > 2
        ]
        
        return sum(factors) / len(factors)
    
    def _analyze_data_characteristics(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'sample_size': len(sample_data),
            'completeness': self._calculate_completeness(sample_data),
            'consistency': self._calculate_consistency(sample_data)
        }
    
    def _identify_predictable_patterns(self, logical_model: Dict[str, Any]) -> List[str]:
        patterns = []
        
        if logical_model['temporal_fields'] and logical_model['metrics']:
            patterns.append('time_series_analysis')
        
        if logical_model['entities'] and logical_model['identifiers']:
            patterns.append('entity_resolution')
        
        return patterns
    
    def _calculate_completeness(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 0.0
        
        total_fields = len(data[0].keys()) if data else 0
        non_null_counts = defaultdict(int)
        
        for row in data:
            for key, value in row.items():
                if value is not None:
                    non_null_counts[key] += 1
        
        if not non_null_counts:
            return 0.0
        
        completeness_scores = [count / len(data) for count in non_null_counts.values()]
        return sum(completeness_scores) / len(completeness_scores)
    
    def _calculate_consistency(self, data: List[Dict[str, Any]]) -> float:
        return 0.85

class ClaudeLevelIntelligence:
    def __init__(self):
        self.knowledge_graph = ConceptualKnowledgeGraph()
        self.reasoning_engine = SemanticReasoningEngine(self.knowledge_graph)
        self.model_builder = MentalModelBuilder(self.knowledge_graph)
        self.learning_history = []
        
    def understand_table_semantically(self, table_metadata: Dict[str, Any], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        table_concept = self._derive_table_concept(table_metadata, sample_data)
        
        column_meanings = {}
        for column in table_metadata.get('columns', []):
            column_meanings[column] = self._understand_column_meaning(
                column,
                self._extract_column_values(sample_data, column),
                table_concept,
                column_meanings
            )
        
        semantic_model = self._build_semantic_model(table_concept, column_meanings)
        mental_model = self.model_builder.build_table_mental_model(
            table_metadata.get('table_name', 'unknown'),
            list(column_meanings.keys()),
            sample_data
        )
        
        return {
            'table_concept': table_concept,
            'column_semantics': column_meanings,
            'semantic_model': semantic_model,
            'mental_model': mental_model,
            'understanding_confidence': self._calculate_understanding_confidence(semantic_model)
        }
    
    def _derive_table_concept(self, metadata: Dict[str, Any], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        table_name = metadata.get('table_name', '').lower()
        
        concept_indicators = {
            'asset_inventory': ['asset', 'inventory', 'cmdb', 'device', 'host'],
            'security_events': ['event', 'alert', 'incident', 'threat', 'attack'],
            'network_traffic': ['flow', 'packet', 'connection', 'traffic', 'network'],
            'access_logs': ['access', 'login', 'auth', 'session', 'user'],
            'vulnerability_data': ['vuln', 'cve', 'patch', 'risk', 'scan'],
            'configuration': ['config', 'setting', 'parameter', 'policy'],
            'monitoring': ['metric', 'performance', 'health', 'status', 'monitor']
        }
        
        scores = {}
        for concept, indicators in concept_indicators.items():
            score = sum(1 for ind in indicators if ind in table_name)
            if metadata.get('columns'):
                for column in metadata['columns']:
                    score += sum(0.5 for ind in indicators if ind in column.lower())
            scores[concept] = score
        
        primary_concept = max(scores, key=scores.get) if scores else 'unknown'
        
        return {
            'primary_concept': primary_concept,
            'confidence': scores.get(primary_concept, 0) / sum(scores.values()) if sum(scores.values()) > 0 else 0,
            'secondary_concepts': [k for k, v in scores.items() if v > 0 and k != primary_concept]
        }
    
    def _understand_column_meaning(self, column_name: str, sample_values: List[Any], 
                                  table_concept: Dict[str, Any], existing_meanings: Dict[str, Any]) -> Dict[str, Any]:
        conceptual_analysis = self._analyze_conceptual_meaning(column_name, sample_values)
        contextual_meaning = self._derive_contextual_meaning(conceptual_analysis, table_concept)
        relational_meaning = self._analyze_column_relationships(column_name, existing_meanings)
        functional_role = self._infer_functional_role(conceptual_analysis, contextual_meaning, relational_meaning)
        
        return {
            'conceptual_type': conceptual_analysis,
            'contextual_role': contextual_meaning,
            'relationships': relational_meaning,
            'functional_role': functional_role,
            'confidence': self._calculate_meaning_confidence(conceptual_analysis, contextual_meaning)
        }
    
    def _analyze_conceptual_meaning(self, column_name: str, sample_values: List[Any]) -> Dict[str, Any]:
        column_lower = column_name.lower()
        
        concept_patterns = {
            'identifier': ['id', 'key', 'uuid', 'guid', 'ref'],
            'hostname': ['host', 'server', 'machine', 'computer', 'node'],
            'network': ['ip', 'mac', 'port', 'subnet', 'vlan'],
            'temporal': ['time', 'date', 'timestamp', 'created', 'modified'],
            'security': ['threat', 'risk', 'vuln', 'attack', 'exploit'],
            'metric': ['count', 'sum', 'avg', 'max', 'min', 'value'],
            'status': ['status', 'state', 'flag', 'enabled', 'active'],
            'location': ['region', 'zone', 'datacenter', 'location', 'geo']
        }
        
        detected_concepts = []
        for concept, patterns in concept_patterns.items():
            if any(pattern in column_lower for pattern in patterns):
                detected_concepts.append(concept)
        
        value_analysis = self._analyze_value_patterns(sample_values)
        
        return {
            'detected_concepts': detected_concepts,
            'primary_concept': detected_concepts[0] if detected_concepts else 'unknown',
            'value_patterns': value_analysis,
            'column_name_analysis': self._analyze_column_name_structure(column_name)
        }
    
    def _derive_contextual_meaning(self, conceptual: Dict[str, Any], table_concept: Dict[str, Any]) -> Dict[str, Any]:
        context_mappings = {
            ('identifier', 'asset_inventory'): 'primary_key',
            ('hostname', 'asset_inventory'): 'asset_identifier',
            ('hostname', 'security_events'): 'event_source',
            ('temporal', 'security_events'): 'event_timestamp',
            ('network', 'network_traffic'): 'traffic_endpoint',
            ('security', 'vulnerability_data'): 'vulnerability_indicator'
        }
        
        primary_concept = conceptual['primary_concept']
        table_primary = table_concept['primary_concept']
        
        contextual_role = context_mappings.get((primary_concept, table_primary), 'attribute')
        
        return {
            'role': contextual_role,
            'importance': 'high' if contextual_role in ['primary_key', 'asset_identifier'] else 'medium',
            'context_confidence': 0.8
        }
    
    def _analyze_column_relationships(self, column_name: str, existing_meanings: Dict[str, Any]) -> List[Dict[str, Any]]:
        relationships = []
        
        for other_column, meaning in existing_meanings.items():
            if other_column != column_name:
                relationship_type = self._detect_relationship_type(column_name, other_column, meaning)
                if relationship_type:
                    relationships.append({
                        'column': other_column,
                        'type': relationship_type,
                        'confidence': 0.7
                    })
        
        return relationships
    
    def _infer_functional_role(self, conceptual: Dict[str, Any], contextual: Dict[str, Any], 
                               relational: List[Dict[str, Any]]) -> str:
        if contextual['role'] == 'primary_key':
            return 'unique_identifier'
        elif 'temporal' in conceptual['detected_concepts']:
            return 'timestamp'
        elif 'metric' in conceptual['detected_concepts']:
            return 'measurement'
        elif 'status' in conceptual['detected_concepts']:
            return 'state_indicator'
        else:
            return 'attribute'
    
    def _build_semantic_model(self, table_concept: Dict[str, Any], column_meanings: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'table_semantics': table_concept,
            'column_semantics': column_meanings,
            'semantic_relationships': self._extract_semantic_relationships(column_meanings),
            'semantic_constraints': self._derive_semantic_constraints_from_meanings(column_meanings),
            'semantic_completeness': self._calculate_semantic_completeness(column_meanings)
        }
    
    def _calculate_understanding_confidence(self, semantic_model: Dict[str, Any]) -> float:
        completeness = semantic_model.get('semantic_completeness', 0)
        table_confidence = semantic_model['table_semantics']['confidence']
        
        column_confidences = []
        for column, meaning in semantic_model['column_semantics'].items():
            column_confidences.append(meaning.get('confidence', 0))
        
        avg_column_confidence = sum(column_confidences) / len(column_confidences) if column_confidences else 0
        
        return (completeness * 0.3 + table_confidence * 0.3 + avg_column_confidence * 0.4)
    
    def _extract_column_values(self, sample_data: List[Dict[str, Any]], column: str) -> List[Any]:
        return [row.get(column) for row in sample_data if column in row]
    
    def _analyze_value_patterns(self, values: List[Any]) -> Dict[str, Any]:
        non_null_values = [v for v in values if v is not None]
        
        if not non_null_values:
            return {'pattern': 'empty', 'confidence': 0}
        
        patterns = {
            'numeric': all(isinstance(v, (int, float)) for v in non_null_values),
            'string': all(isinstance(v, str) for v in non_null_values),
            'boolean': all(isinstance(v, bool) for v in non_null_values),
            'mixed': len(set(type(v) for v in non_null_values)) > 1
        }
        
        detected_pattern = next((k for k, v in patterns.items() if v), 'unknown')
        
        return {
            'pattern': detected_pattern,
            'unique_ratio': len(set(non_null_values)) / len(non_null_values) if non_null_values else 0,
            'null_ratio': (len(values) - len(non_null_values)) / len(values) if values else 0
        }
    
    def _analyze_column_name_structure(self, column_name: str) -> Dict[str, Any]:
        return {
            'has_underscore': '_' in column_name,
            'has_camelcase': any(c.isupper() for c in column_name[1:]),
            'length': len(column_name),
            'starts_with_verb': column_name.split('_')[0].lower() in ['get', 'set', 'is', 'has', 'can']
        }
    
    def _detect_relationship_type(self, col1: str, col2: str, col2_meaning: Dict[str, Any]) -> Optional[str]:
        if 'id' in col1.lower() and 'name' in col2.lower():
            return 'id_to_name'
        elif 'timestamp' in col1.lower() and 'event' in col2.lower():
            return 'temporal_association'
        elif col2_meaning.get('functional_role') == 'unique_identifier':
            return 'foreign_key_candidate'
        return None
    
    def _extract_semantic_relationships(self, column_meanings: Dict[str, Any]) -> List[Dict[str, Any]]:
        relationships = []
        columns = list(column_meanings.keys())
        
        for i, col1 in enumerate(columns):
            for col2 in columns[i+1:]:
                if self._columns_are_related(col1, col2, column_meanings):
                    relationships.append({
                        'from': col1,
                        'to': col2,
                        'type': 'semantic_association',
                        'strength': 0.7
                    })
        
        return relationships
    
    def _derive_semantic_constraints_from_meanings(self, column_meanings: Dict[str, Any]) -> List[Dict[str, Any]]:
        constraints = []
        
        for column, meaning in column_meanings.items():
            if meaning['functional_role'] == 'unique_identifier':
                constraints.append({
                    'column': column,
                    'constraint': 'unique',
                    'confidence': 0.9
                })
            elif meaning['functional_role'] == 'timestamp':
                constraints.append({
                    'column': column,
                    'constraint': 'temporal_ordering',
                    'confidence': 0.8
                })
        
        return constraints
    
    def _calculate_semantic_completeness(self, column_meanings: Dict[str, Any]) -> float:
        understood_columns = sum(1 for m in column_meanings.values() if m['primary_concept'] != 'unknown')
        total_columns = len(column_meanings)
        
        return understood_columns / total_columns if total_columns > 0 else 0
    
    def _columns_are_related(self, col1: str, col2: str, meanings: Dict[str, Any]) -> bool:
        meaning1 = meanings.get(col1, {})
        meaning2 = meanings.get(col2, {})
        
        if meaning1.get('primary_concept') == meaning2.get('primary_concept'):
            return True
        
        related_concepts = {
            'identifier': ['hostname', 'network'],
            'temporal': ['security', 'metric'],
            'hostname': ['network', 'location']
        }
        
        concept1 = meaning1.get('primary_concept')
        concept2 = meaning2.get('primary_concept')
        
        return concept2 in related_concepts.get(concept1, [])
    
    def _calculate_meaning_confidence(self, conceptual: Dict[str, Any], contextual: Dict[str, Any]) -> float:
        concept_confidence = 1.0 if conceptual['primary_concept'] != 'unknown' else 0.3
        context_confidence = contextual.get('context_confidence', 0.5)
        
        return (concept_confidence * 0.6 + context_confidence * 0.4)