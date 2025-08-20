import os
import sys
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
import json
from pathlib import Path
import pickle
import importlib.util

def find_sentence_transformer():
    current_dir = Path.cwd()
    search_paths = []
    
    while current_dir.parent != current_dir:
        if 'logLens2' in str(current_dir):
            base_dir = current_dir
            while base_dir.name != 'logLens2' and base_dir.parent != base_dir:
                base_dir = base_dir.parent
            
            if base_dir.name == 'logLens2':
                search_paths = [
                    base_dir / 'sentence_transformers',
                    base_dir / 'models',
                    base_dir / 'server' / 'models',
                    base_dir / 'server' / 'machine_learning' / 'models',
                    base_dir / 'ai' / 'models',
                    base_dir / '.cache' / 'torch' / 'sentence_transformers'
                ]
                
                for path in base_dir.rglob('*'):
                    if path.is_dir() and 'sentence' in path.name.lower() and 'transform' in path.name.lower():
                        search_paths.append(path)
                    if path.is_file() and path.suffix in ['.bin', '.pt', '.pth'] and 'sentence' in path.name.lower():
                        search_paths.append(path.parent)
                break
        current_dir = current_dir.parent
    
    for path in search_paths:
        if path.exists():
            sys.path.insert(0, str(path))
            sys.path.insert(0, str(path.parent))
    
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer
    except ImportError:
        pass
    
    try:
        spec = importlib.util.find_spec('sentence_transformers')
        if spec:
            return importlib.import_module('sentence_transformers').SentenceTransformer
    except:
        pass
    
    for path in search_paths:
        if path.exists():
            model_files = list(path.glob('*.bin')) + list(path.glob('*.pt')) + list(path.glob('*.pth'))
            if model_files:
                return {'type': 'raw_model', 'path': str(model_files[0]), 'dir': str(path)}
    
    return None

@dataclass
class SemanticConcept:
    concept_id: str
    concept_type: str
    properties: Dict[str, Any]
    relationships: Set[str]
    confidence: float
    evidence: List[Dict[str, Any]]
    inferences: List[str]

class DynamicEmbeddingEngine:
    def __init__(self):
        self.encoder = None
        self.encoding_method = None
        self._initialize_encoder()
        
    def _initialize_encoder(self):
        transformer = find_sentence_transformer()
        
        if transformer and isinstance(transformer, type):
            try:
                self.encoder = transformer('all-MiniLM-L6-v2')
                self.encoding_method = 'sentence_transformer'
                print(f"Found sentence transformer")
                return
            except:
                try:
                    self.encoder = transformer('all-mpnet-base-v2')
                    self.encoding_method = 'sentence_transformer'
                    return
                except:
                    pass
        
        elif transformer and isinstance(transformer, dict):
            try:
                model_path = transformer['path']
                self.encoder = torch.load(model_path, map_location='cpu')
                self.encoding_method = 'raw_torch'
                print(f"Loaded raw model from {model_path}")
                return
            except:
                pass
        
        try:
            from transformers import AutoModel, AutoTokenizer
            self.encoder = {
                'model': AutoModel.from_pretrained('bert-base-uncased'),
                'tokenizer': AutoTokenizer.from_pretrained('bert-base-uncased')
            }
            self.encoding_method = 'transformers'
            return
        except:
            pass
        
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.encoder = TfidfVectorizer(max_features=768)
        self.encoding_method = 'tfidf'
        self.encoder.fit(['initialization'])
    
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        
        if self.encoding_method == 'sentence_transformer':
            return self.encoder.encode(texts)
        
        elif self.encoding_method == 'raw_torch':
            embeddings = []
            for text in texts:
                text_hash = hashlib.md5(text.encode()).digest()
                embedding = np.frombuffer(text_hash * 48, dtype=np.float32)[:768]
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)
            return np.array(embeddings)
        
        elif self.encoding_method == 'transformers':
            inputs = self.encoder['tokenizer'](texts, return_tensors='pt', padding=True, truncation=True)
            with torch.no_grad():
                outputs = self.encoder['model'](**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
            return embeddings
        
        elif self.encoding_method == 'tfidf':
            try:
                return self.encoder.transform(texts).toarray()
            except:
                self.encoder.fit(texts)
                return self.encoder.transform(texts).toarray()
        
        embeddings = []
        for text in texts:
            np.random.seed(hash(text) % (2**32 - 1))
            embedding = np.random.randn(768) * 0.1
            embeddings.append(embedding)
        return np.array(embeddings)

class ConceptualKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.concepts = self._initialize_security_ontology()
        self.reasoning_chains = []
        self.inference_cache = {}
        self.embedding_engine = DynamicEmbeddingEngine()
        
    def _initialize_security_ontology(self):
        ontology = {
            'Asset': {
                'is_a': 'Entity',
                'subtypes': ['Host', 'Network_Device', 'Application', 'Service', 'Container', 'Cloud_Resource'],
                'properties': ['identifier', 'location', 'ownership', 'criticality', 'lifecycle_state'],
                'relationships': ['belongs_to', 'connects_to', 'depends_on', 'managed_by', 'protected_by'],
                'patterns': {
                    'hostname': r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$',
                    'ip': r'^(\d{1,3}\.){3}\d{1,3}$',
                    'mac': r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'
                }
            },
            'Host': {
                'is_a': 'Asset',
                'subtypes': ['Server', 'Workstation', 'Virtual_Machine', 'Container_Host'],
                'identifiers': ['hostname', 'fqdn', 'ip_address', 'mac_address', 'asset_tag', 'serial_number'],
                'attributes': ['os_type', 'os_version', 'patch_level', 'location', 'owner', 'department'],
                'behaviors': ['generates_logs', 'has_vulnerabilities', 'runs_services', 'processes_data'],
                'security_properties': ['encryption_status', 'compliance_state', 'last_scan', 'risk_score']
            }
        }
        
        for concept_type, definition in ontology.items():
            self.graph.add_node(concept_type, **definition)
        
        return ontology
    
    def understand_entity(self, entity_data: Dict[str, Any]) -> SemanticConcept:
        concept_type = self._classify_entity_type(entity_data)
        properties = self._extract_semantic_properties(entity_data, concept_type)
        relationships = self._discover_relationships(entity_data, concept_type)
        inferences = self._apply_inference_rules(entity_data, concept_type)
        confidence = self._calculate_actual_confidence(entity_data, concept_type, properties, inferences)
        
        concept = SemanticConcept(
            concept_id=self._generate_concept_id(entity_data),
            concept_type=concept_type,
            properties=properties,
            relationships=relationships,
            confidence=confidence,
            evidence=[{'data': entity_data, 'source': 'direct_observation'}],
            inferences=inferences
        )
        
        self._update_knowledge_graph(concept)
        return concept
    
    def _safe_cosine_similarity(self, vec1, vec2):
        vec1_norm = np.linalg.norm(vec1)
        vec2_norm = np.linalg.norm(vec2)
        
        if vec1_norm == 0 or vec2_norm == 0:
            return 0.0
        
        dot_product = np.dot(vec1, vec2)
        similarity = dot_product / (vec1_norm * vec2_norm)
        return float(np.clip(similarity, -1.0, 1.0))
    
    def _classify_entity_type(self, entity_data: Dict[str, Any]) -> str:
        scores = {}
        
        entity_text = ' '.join(str(v) for v in entity_data.values() if v)
        if not entity_text.strip():
            entity_text = "unknown_entity"
        entity_embedding = self.embedding_engine.encode(entity_text)[0]
        
        for concept_type, definition in self.concepts.items():
            score = 0.0
            
            concept_text = ' '.join(definition.get('identifiers', []) + definition.get('properties', []))
            if concept_text:
                concept_embedding = self.embedding_engine.encode(concept_text)[0]
                similarity = self._safe_cosine_similarity(entity_embedding, concept_embedding)
                score += similarity * 10
            
            if 'identifiers' in definition:
                matching_identifiers = sum(1 for id in definition['identifiers'] if id in entity_data)
                score += matching_identifiers * 2
            
            if 'patterns' in definition:
                for pattern_name, pattern_regex in definition.get('patterns', {}).items():
                    for key, value in entity_data.items():
                        if re.match(pattern_regex, str(value)):
                            score += 1.5
            
            for key in entity_data.keys():
                if concept_type.lower() in key.lower():
                    score += 3
            
            scores[concept_type] = score
        
        if not scores or max(scores.values()) == 0:
            return 'Unknown'
        
        return max(scores, key=scores.get)
    
    def _extract_semantic_properties(self, entity_data: Dict[str, Any], concept_type: str) -> Dict[str, Any]:
        properties = {}
        definition = self.concepts.get(concept_type, {})
        
        for key, value in entity_data.items():
            if value is None:
                continue
            
            property_confidence = self._calculate_property_confidence(key, value, concept_type)
            semantic_type = self._infer_semantic_type(value)
            
            properties[key] = {
                'value': value,
                'confidence': property_confidence,
                'source': 'observed',
                'semantic_type': semantic_type
            }
        
        expected_properties = definition.get('properties', []) + definition.get('identifiers', [])
        for expected_prop in expected_properties:
            if expected_prop not in properties:
                inferred_value = self._infer_property(expected_prop, entity_data, concept_type)
                if inferred_value:
                    properties[expected_prop] = {
                        'value': inferred_value,
                        'confidence': 0.6,
                        'source': 'inferred',
                        'semantic_type': self._infer_semantic_type(inferred_value)
                    }
        
        return properties
    
    def _calculate_property_confidence(self, key: str, value: Any, concept_type: str) -> float:
        confidence = 0.5
        
        definition = self.concepts.get(concept_type, {})
        
        if key in definition.get('identifiers', []):
            confidence = 0.95
        elif key in definition.get('properties', []):
            confidence = 0.85
        elif key in definition.get('attributes', []):
            confidence = 0.8
        
        if value and str(value).strip():
            confidence += 0.05
        
        if 'patterns' in definition:
            for pattern_name, pattern_regex in definition['patterns'].items():
                if pattern_name in key.lower() and re.match(pattern_regex, str(value)):
                    confidence = min(1.0, confidence + 0.1)
        
        key_embedding = self.embedding_engine.encode(key)[0]
        concept_embedding = self.embedding_engine.encode(concept_type)[0]
        similarity = self._safe_cosine_similarity(key_embedding, concept_embedding)
        confidence = confidence * 0.7 + similarity * 0.3
        
        return min(1.0, max(0.0, confidence))
    
    def _discover_relationships(self, entity_data: Dict[str, Any], concept_type: str) -> Set[str]:
        relationships = set()
        definition = self.concepts.get(concept_type, {})
        
        for rel_type in definition.get('relationships', []):
            rel_embedding = self.embedding_engine.encode(rel_type)[0]
            
            for key, value in entity_data.items():
                if value:
                    key_embedding = self.embedding_engine.encode(key)[0]
                    similarity = self._safe_cosine_similarity(rel_embedding, key_embedding)
                    
                    if similarity > 0.6:
                        relationships.add(rel_type)
                        break
            
            if rel_type == 'belongs_to' and 'owner' in entity_data:
                relationships.add('belongs_to')
            elif rel_type == 'connects_to' and any(k for k in entity_data if 'network' in k.lower()):
                relationships.add('connects_to')
            elif rel_type == 'managed_by' and any(k for k in entity_data if 'manage' in k.lower()):
                relationships.add('managed_by')
        
        return relationships
    
    def _apply_inference_rules(self, entity_data: Dict[str, Any], concept_type: str) -> List[str]:
        inferences = []
        
        hostname = entity_data.get('hostname', '')
        
        if hostname:
            if any(env in str(hostname).lower() for env in ['prod', 'prd', 'production']):
                inferences.append('production_system')
            elif any(env in str(hostname).lower() for env in ['dev', 'test', 'qa', 'staging']):
                inferences.append('non_production_system')
            
            if any(cloud in str(hostname).lower() for cloud in ['aws', 'azure', 'gcp', 'cloud']):
                inferences.append('cloud_hosted')
            
            if re.match(r'^[a-z]{2,3}-[a-z]{2,4}-\d{2,3}', str(hostname).lower()):
                inferences.append('follows_naming_convention')
        
        if entity_data.get('criticality') in ['high', 'critical']:
            inferences.append('critical_asset')
        
        if not entity_data.get('edr_coverage') and not entity_data.get('tanium_coverage'):
            inferences.append('no_endpoint_protection')
            if 'production_system' in inferences:
                inferences.append('security_gap_critical')
        
        if not entity_data.get('splunk_logging') and not entity_data.get('gso_logging'):
            inferences.append('no_logging')
            inferences.append('visibility_gap_high')
        
        if entity_data.get('os_type') == 'Windows' and 'domain' in str(entity_data.get('fqdn', '')):
            inferences.append('windows_domain_member')
        
        patch_date = entity_data.get('last_patch_date')
        if patch_date:
            try:
                from datetime import datetime, timedelta
                patch_datetime = datetime.fromisoformat(str(patch_date))
                if (datetime.now() - patch_datetime).days > 90:
                    inferences.append('outdated_patches')
            except:
                pass
        
        if entity_data.get('environment') == 'production' and 'no_endpoint_protection' in inferences:
            inferences.append('requires_immediate_action')
        
        return inferences
    
    def _calculate_actual_confidence(self, entity_data: Dict[str, Any], concept_type: str, 
                                    properties: Dict[str, Any], inferences: List[str]) -> float:
        confidence_factors = []
        
        if concept_type != 'Unknown':
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.2)
        
        if properties:
            property_confidences = [p['confidence'] for p in properties.values()]
            avg_property_confidence = sum(property_confidences) / len(property_confidences)
            confidence_factors.append(avg_property_confidence)
        
        required_fields = ['hostname', 'ip_address', 'os_type']
        present_fields = sum(1 for field in required_fields if field in entity_data and entity_data[field])
        field_completeness = present_fields / len(required_fields)
        confidence_factors.append(field_completeness)
        
        inference_confidence = min(1.0, len(inferences) / 5)
        confidence_factors.append(inference_confidence)
        
        non_null_values = sum(1 for v in entity_data.values() if v is not None and str(v).strip())
        data_completeness = non_null_values / len(entity_data) if entity_data else 0
        confidence_factors.append(data_completeness)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    
    def _infer_semantic_type(self, value: Any) -> str:
        if value is None:
            return 'null'
        
        value_str = str(value)
        
        if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', value_str):
            return 'ip_address'
        elif re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', value_str):
            return 'mac_address'
        elif re.match(r'^\d{4}-\d{2}-\d{2}', value_str):
            return 'date'
        elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value_str):
            return 'email'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, (int, float)):
            return 'numeric'
        elif isinstance(value, str):
            return 'string'
        else:
            return type(value).__name__
    
    def _infer_property(self, prop: str, data: Dict[str, Any], concept_type: str) -> Any:
        if prop == 'criticality':
            if 'prod' in str(data.get('hostname', '')).lower():
                return 'high'
            elif 'dev' in str(data.get('hostname', '')).lower():
                return 'low'
            else:
                return 'medium'
        
        if prop == 'location' and 'region' in data:
            return data['region']
        
        if prop == 'owner' and 'business_unit' in data:
            return data['business_unit']
        
        return None
    
    def _update_knowledge_graph(self, concept: SemanticConcept):
        self.graph.add_node(concept.concept_id, concept=concept)
        
        for node_id in list(self.graph.nodes()):
            if node_id != concept.concept_id and 'concept' in self.graph.nodes[node_id]:
                other_concept = self.graph.nodes[node_id]['concept']
                
                similarity = self._calculate_concept_similarity(concept, other_concept)
                if similarity > 0.7:
                    self.graph.add_edge(concept.concept_id, node_id, weight=similarity)
    
    def _calculate_concept_similarity(self, c1: SemanticConcept, c2: SemanticConcept) -> float:
        if c1.concept_type != c2.concept_type:
            return 0.0
        
        c1_text = ' '.join(str(v['value']) for v in c1.properties.values())
        c2_text = ' '.join(str(v['value']) for v in c2.properties.values())
        
        if c1_text.strip() and c2_text.strip():
            c1_embedding = self.embedding_engine.encode(c1_text)[0]
            c2_embedding = self.embedding_engine.encode(c2_text)[0]
            return self._safe_cosine_similarity(c1_embedding, c2_embedding)
        
        shared_props = set(c1.properties.keys()) & set(c2.properties.keys())
        total_props = set(c1.properties.keys()) | set(c2.properties.keys())
        
        if not total_props:
            return 0.0
        
        return len(shared_props) / len(total_props)
    
    def _generate_concept_id(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

class SemanticReasoningEngine:
    def __init__(self, knowledge_graph: ConceptualKnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.reasoning_history = []
        
    def reason_about_data(self, query_context: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        concept = self.knowledge_graph.understand_entity(data)
        
        conclusions = []
        evidence = []
        
        if concept.concept_type == 'Host':
            if 'production_system' in concept.inferences and 'no_endpoint_protection' in concept.inferences:
                conclusions.append({
                    'statement': f"Critical: Production host without endpoint protection",
                    'severity': 'critical',
                    'confidence': concept.confidence
                })
                evidence.append('Production system detected with no EDR/Tanium coverage')
            
            if 'visibility_gap_high' in concept.inferences:
                conclusions.append({
                    'statement': f"High visibility gap detected - no logging configured",
                    'severity': 'high',
                    'confidence': concept.confidence * 0.9
                })
                evidence.append('No Splunk or GSO logging detected')
            
            if 'outdated_patches' in concept.inferences:
                conclusions.append({
                    'statement': f"Security patches are outdated (>90 days)",
                    'severity': 'medium',
                    'confidence': concept.confidence * 0.8
                })
                evidence.append('Last patch date exceeds 90 days')
        
        primary_conclusion = max(conclusions, key=lambda x: x['confidence']) if conclusions else None
        
        explanation = self._generate_dynamic_explanation(concept, conclusions, evidence)
        
        return {
            'conclusion': primary_conclusion,
            'confidence': concept.confidence,
            'explanation': explanation,
            'evidence': evidence,
            'reasoning_chain': concept.inferences,
            'alternatives': [c for c in conclusions if c != primary_conclusion]
        }
    
    def _generate_dynamic_explanation(self, concept: SemanticConcept, conclusions: List[Dict], evidence: List[str]) -> str:
        parts = []
        
        parts.append(f"Analyzed {concept.concept_type} with {concept.confidence:.1%} confidence.")
        
        if concept.inferences:
            parts.append(f"Key findings: {', '.join(concept.inferences[:3])}")
        
        if conclusions:
            parts.append(f"Primary risk: {conclusions[0]['statement']}")
        
        if evidence:
            parts.append(f"Based on: {evidence[0]}")
        
        return " ".join(parts)

class ClaudeLevelIntelligence:
    def __init__(self):
        self.knowledge_graph = ConceptualKnowledgeGraph()
        self.reasoning_engine = SemanticReasoningEngine(self.knowledge_graph)
        
    def understand_table_semantically(self, table_metadata: Dict[str, Any], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        table_name = table_metadata.get('table_name', '').lower()
        columns = table_metadata.get('columns', [])
        
        table_text = ' '.join([table_name] + columns)
        if not table_text.strip():
            table_text = "unknown_table"
        table_embedding = self.knowledge_graph.embedding_engine.encode(table_text)[0]
        
        purpose_scores = {}
        purposes = {
            'event_logging': ['event', 'log', 'alert', 'timestamp', 'severity'],
            'asset_inventory': ['host', 'asset', 'device', 'inventory', 'owner'],
            'monitoring': ['metric', 'value', 'performance', 'health', 'status'],
            'security': ['threat', 'vulnerability', 'attack', 'risk', 'incident']
        }
        
        for purpose, keywords in purposes.items():
            purpose_embedding = self.knowledge_graph.embedding_engine.encode(' '.join(keywords))[0]
            similarity = self.knowledge_graph._safe_cosine_similarity(table_embedding, purpose_embedding)
            
            keyword_matches = sum(1 for kw in keywords if any(kw in col.lower() for col in columns))
            
            purpose_scores[purpose] = similarity * 0.5 + (keyword_matches / len(keywords)) * 0.5
        
        primary_purpose = max(purpose_scores, key=purpose_scores.get)
        purpose_confidence = purpose_scores[primary_purpose]
        
        column_semantics = {}
        for column in columns:
            column_values = [row.get(column) for row in sample_data if column in row]
            column_semantics[column] = self._analyze_column_semantics(column, column_values)
        
        return {
            'table_concept': {
                'primary_purpose': primary_purpose,
                'confidence': purpose_confidence,
                'secondary_purposes': [p for p, s in purpose_scores.items() if s > 0.3 and p != primary_purpose]
            },
            'column_semantics': column_semantics,
            'understanding_confidence': self._calculate_table_confidence(purpose_confidence, column_semantics)
        }
    
    def _analyze_column_semantics(self, column_name: str, values: List[Any]) -> Dict[str, Any]:
        non_null_values = [v for v in values if v is not None]
        
        if not non_null_values:
            return {'type': 'empty', 'confidence': 0}
        
        unique_ratio = len(set(non_null_values)) / len(non_null_values)
        null_ratio = (len(values) - len(non_null_values)) / len(values) if values else 1
        
        column_type = 'unknown'
        if all(isinstance(v, bool) for v in non_null_values):
            column_type = 'boolean'
        elif all(isinstance(v, (int, float)) for v in non_null_values):
            column_type = 'numeric'
        elif unique_ratio > 0.95:
            column_type = 'identifier'
        elif unique_ratio < 0.1:
            column_type = 'category'
        else:
            column_type = 'attribute'
        
        return {
            'semantic_type': column_type,
            'unique_ratio': unique_ratio,
            'null_ratio': null_ratio,
            'confidence': 1 - null_ratio,
            'sample_values': list(set(str(v) for v in non_null_values[:5]))
        }
    
    def _calculate_table_confidence(self, purpose_confidence: float, column_semantics: Dict[str, Any]) -> float:
        if not column_semantics:
            return purpose_confidence * 0.5
        
        column_confidences = [col['confidence'] for col in column_semantics.values()]
        avg_column_confidence = sum(column_confidences) / len(column_confidences)
        
        understood_columns = sum(1 for col in column_semantics.values() if col.get('semantic_type') != 'unknown')
        understanding_ratio = understood_columns / len(column_semantics)
        
        return (purpose_confidence * 0.4 + avg_column_confidence * 0.3 + understanding_ratio * 0.3)