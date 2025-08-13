# ai/neural.py

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import statistics
import hashlib
import re
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import networkx as nx

class DeepFieldClassifier(nn.Module):
    def __init__(self, vocab_size=50000, embed_dim=768, hidden_dim=512, num_classes=50):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=embed_dim, 
                nhead=12, 
                dim_feedforward=2048,
                dropout=0.1,
                batch_first=True
            ),
            num_layers=8
        )
        self.content_attention = nn.MultiheadAttention(embed_dim, 16, batch_first=True)
        self.semantic_mixer = nn.Sequential(
            nn.Linear(embed_dim * 3, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
        self.field_types = [
            'hostname', 'ip_address', 'fqdn', 'mac_address', 'infrastructure_type',
            'system_classification', 'global_region', 'country', 'datacenter',
            'cloud_region', 'business_unit', 'cio', 'app_class', 'edr_coverage',
            'dlp_coverage', 'tanium_coverage', 'network_log_types', 'endpoint_log_types',
            'cloud_log_types', 'app_log_types', 'identity_log_types', 'network_zones',
            'geolocation', 'vpc', 'controls', 'server_name', 'computer_name', 'device_name',
            'endpoint_name', 'machine_name', 'asset_name', 'node_name', 'instance_name',
            'resource_name', 'equipment_name', 'system_name', 'platform_name', 'host_name',
            'workstation_name', 'client_name', 'terminal_name', 'appliance_name', 'component_name',
            'service_name', 'application_name', 'database_name', 'cluster_name', 'domain_name',
            'network_name', 'subnet_name', 'zone_name', 'location_name', 'site_name'
        ]
    
    def forward(self, input_ids, attention_mask, content_features):
        embedded = self.embedding(input_ids)
        transformer_out = self.transformer(embedded)
        pooled = transformer_out.mean(dim=1)
        
        attended, _ = self.content_attention(embedded, embedded, embedded)
        attended_pooled = attended.mean(dim=1)
        
        combined = torch.cat([pooled, attended_pooled, content_features], dim=-1)
        return F.softmax(self.semantic_mixer(combined), dim=-1)

class AdvancedSemanticEmbedder:
    def __init__(self):
        self.cache = {}
        self.tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 3))
        self.concept_graph = self._build_concept_graph()
        self.semantic_clusters = {}
        self.learned_patterns = defaultdict(list)
        self.domain_knowledge = self._init_domain_knowledge()
        
    def _build_concept_graph(self):
        G = nx.Graph()
        concepts = {
            'hostname': ['server', 'computer', 'machine', 'host', 'endpoint', 'device', 'node', 'workstation'],
            'network': ['ip', 'address', 'subnet', 'vlan', 'dns', 'domain', 'gateway', 'router'],
            'security': ['firewall', 'auth', 'certificate', 'ssl', 'vpn', 'encryption', 'access'],
            'infrastructure': ['datacenter', 'cloud', 'platform', 'service', 'cluster', 'farm'],
            'business': ['organization', 'department', 'unit', 'division', 'team', 'group'],
            'location': ['region', 'country', 'site', 'facility', 'building', 'floor'],
            'application': ['software', 'program', 'system', 'database', 'service', 'tool'],
            'identity': ['user', 'account', 'credential', 'principal', 'subject', 'entity']
        }
        
        for category, terms in concepts.items():
            G.add_node(category, type='category')
            for term in terms:
                G.add_node(term, type='term', category=category)
                G.add_edge(category, term, weight=1.0)
                
                for other_term in terms:
                    if term != other_term:
                        similarity = self._calculate_term_similarity(term, other_term)
                        if similarity > 0.6:
                            G.add_edge(term, other_term, weight=similarity)
        
        return G
    
    def _init_domain_knowledge(self):
        return {
            'hostname_patterns': [
                r'^[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
                r'^[a-zA-Z0-9]+$',
                r'^[a-zA-Z]{2,4}[0-9]{1,6}$',
                r'^[a-zA-Z]+\-[a-zA-Z0-9]+$'
            ],
            'hostname_indicators': [
                'srv', 'web', 'app', 'db', 'sql', 'dc', 'ad', 'ex', 'fs', 'dns',
                'dhcp', 'proxy', 'fw', 'lb', 'nas', 'san', 'vm', 'host', 'node',
                'server', 'desktop', 'laptop', 'workstation', 'pc', 'ws'
            ],
            'infrastructure_terms': [
                'prod', 'dev', 'test', 'stage', 'qa', 'uat', 'demo', 'lab',
                'primary', 'secondary', 'backup', 'dr', 'cluster', 'farm'
            ],
            'location_terms': [
                'us', 'eu', 'ap', 'amer', 'emea', 'apac', 'north', 'south',
                'east', 'west', 'central', 'global', 'local', 'remote'
            ]
        }
    
    def analyze_table_semantically(self, table_name: str, column_names: List[str], 
                                 sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        
        table_context = self._extract_table_context(table_name)
        semantic_features = self._build_semantic_features(column_names, sample_data, table_context)
        
        column_classifications = {}
        for col_name, samples in sample_data.items():
            classification = self._classify_column_deep(col_name, samples, semantic_features, table_context)
            if classification['confidence'] > 0.4:
                column_classifications[col_name] = classification
        
        table_embedding = self._create_table_embedding(table_name, column_names, sample_data)
        similar_tables = self._find_similar_tables(table_embedding)
        
        return {
            'table_context': table_context,
            'semantic_features': semantic_features,
            'column_classifications': column_classifications,
            'table_embedding': table_embedding,
            'similar_tables': similar_tables,
            'confidence_score': self._calculate_table_confidence(column_classifications)
        }
    
    def _extract_table_context(self, table_name: str) -> Dict[str, Any]:
        name_parts = table_name.lower().split('.')
        table_only = name_parts[-1] if name_parts else table_name.lower()
        
        context_signals = {
            'is_dimension': any(dim in table_only for dim in ['dim', 'dimension', 'master', 'ref']),
            'is_fact': any(fact in table_only for fact in ['fact', 'event', 'log', 'trans']),
            'is_endpoint': 'endpoint' in table_only,
            'is_asset': any(asset in table_only for asset in ['asset', 'device', 'machine', 'computer']),
            'is_network': any(net in table_only for net in ['network', 'ip', 'dns', 'subnet']),
            'is_security': any(sec in table_only for sec in ['security', 'auth', 'access', 'audit']),
            'is_inventory': any(inv in table_only for inv in ['inventory', 'cmdb', 'catalog']),
            'data_source': self._identify_data_source(table_name)
        }
        
        return context_signals
    
    def _identify_data_source(self, table_name: str) -> str:
        name_lower = table_name.lower()
        if 'splunk' in name_lower or 'spl_' in name_lower:
            return 'splunk'
        elif 'crowdstrike' in name_lower or 'cs_' in name_lower:
            return 'crowdstrike'
        elif 'chronicle' in name_lower:
            return 'chronicle'
        elif 'cmdb' in name_lower or 'dim_endpoint' in name_lower:
            return 'cmdb'
        elif 'tanium' in name_lower:
            return 'tanium'
        else:
            return 'unknown'
    
    def _build_semantic_features(self, column_names: List[str], sample_data: Dict[str, List[str]], 
                               table_context: Dict[str, Any]) -> Dict[str, Any]:
        
        all_text = ' '.join(column_names) + ' ' + ' '.join([
            ' '.join(samples[:10]) for samples in sample_data.values()
        ])
        
        tfidf_features = self._extract_tfidf_features(all_text)
        graph_features = self._extract_graph_features(column_names, sample_data)
        pattern_features = self._extract_pattern_features(sample_data)
        
        return {
            'tfidf_vector': tfidf_features,
            'graph_centrality': graph_features,
            'pattern_signatures': pattern_features,
            'semantic_density': self._calculate_semantic_density(column_names, sample_data)
        }
    
    def _classify_column_deep(self, column_name: str, samples: List[str], 
                            semantic_features: Dict[str, Any], table_context: Dict[str, Any]) -> Dict[str, Any]:
        
        name_embedding = self._embed_text_advanced(column_name)
        content_embedding = self._embed_content_advanced(samples)
        
        graph_score = self._calculate_graph_relevance(column_name, samples)
        pattern_score = self._analyze_content_patterns(samples)
        context_score = self._calculate_context_relevance(column_name, samples, table_context)
        
        hostname_probability = self._calculate_hostname_probability(column_name, samples, table_context)
        
        if hostname_probability > 0.7:
            return {
                'field_type': 'hostname',
                'confidence': hostname_probability,
                'reasoning': self._generate_classification_reasoning(column_name, samples, 'hostname'),
                'features': {
                    'name_embedding': name_embedding,
                    'content_embedding': content_embedding,
                    'graph_score': graph_score,
                    'pattern_score': pattern_score,
                    'context_score': context_score
                }
            }
        
        field_scores = {}
        for field_type in ['ip_address', 'fqdn', 'mac_address', 'infrastructure_type', 'system_classification']:
            score = self._calculate_field_probability(column_name, samples, field_type, table_context)
            if score > 0.3:
                field_scores[field_type] = score
        
        if field_scores:
            best_field = max(field_scores.items(), key=lambda x: x[1])
            return {
                'field_type': best_field[0],
                'confidence': best_field[1],
                'reasoning': self._generate_classification_reasoning(column_name, samples, best_field[0]),
                'alternatives': field_scores
            }
        
        return {'field_type': 'unknown', 'confidence': 0.0}
    
    def _calculate_hostname_probability(self, column_name: str, samples: List[str], 
                                      table_context: Dict[str, Any]) -> float:
        
        name_indicators = [
            'hostname', 'host', 'computer', 'machine', 'device', 'endpoint', 
            'server', 'node', 'workstation', 'asset', 'equipment', 'system'
        ]
        
        name_lower = column_name.lower()
        name_score = max([
            self._fuzzy_match(indicator, name_lower) for indicator in name_indicators
        ]) if name_indicators else 0.0
        
        if not samples:
            return name_score * 0.5
        
        pattern_matches = 0
        format_consistency = 0
        semantic_matches = 0
        
        for sample in samples[:50]:
            if self._matches_hostname_patterns(sample):
                pattern_matches += 1
            
            if self._has_hostname_semantics(sample):
                semantic_matches += 1
        
        pattern_score = pattern_matches / len(samples[:50])
        semantic_score = semantic_matches / len(samples[:50])
        
        format_consistency = self._calculate_format_consistency(samples[:50])
        
        context_boost = 0.0
        if table_context.get('is_endpoint') or table_context.get('is_asset'):
            context_boost = 0.2
        if table_context.get('data_source') == 'cmdb':
            context_boost += 0.15
        
        final_score = (
            name_score * 0.3 +
            pattern_score * 0.35 +
            semantic_score * 0.25 +
            format_consistency * 0.1 +
            context_boost
        )
        
        return min(1.0, final_score)
    
    def _matches_hostname_patterns(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        value = value.strip()
        if not value or value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
            return False
        
        for pattern in self.domain_knowledge['hostname_patterns']:
            if re.match(pattern, value, re.IGNORECASE):
                return True
        
        value_lower = value.lower()
        for indicator in self.domain_knowledge['hostname_indicators']:
            if indicator in value_lower:
                return True
        
        return False
    
    def _has_hostname_semantics(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        
        has_infrastructure = any(term in value_lower for term in self.domain_knowledge['infrastructure_terms'])
        has_location = any(term in value_lower for term in self.domain_knowledge['location_terms'])
        has_numbers = bool(re.search(r'\d', value))
        has_separators = bool(re.search(r'[-_.]', value))
        
        return (has_infrastructure or has_location) and (has_numbers or has_separators)
    
    def _calculate_format_consistency(self, samples: List[str]) -> float:
        if len(samples) < 2:
            return 1.0
        
        patterns = []
        for sample in samples:
            pattern = re.sub(r'[a-zA-Z]', 'A', str(sample))
            pattern = re.sub(r'[0-9]', '9', pattern)
            patterns.append(pattern)
        
        from collections import Counter
        pattern_counts = Counter(patterns)
        most_common_ratio = pattern_counts.most_common(1)[0][1] / len(patterns) if pattern_counts else 0
        
        return most_common_ratio
    
    def _embed_text_advanced(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(512)
        
        text_lower = text.lower()
        
        semantic_vector = np.zeros(512)
        
        if text_lower in self.cache:
            return self.cache[text_lower]
        
        concept_scores = {}
        for node in self.concept_graph.nodes():
            if self.concept_graph.nodes[node].get('type') == 'category':
                neighbors = list(self.concept_graph.neighbors(node))
                score = sum(1 for neighbor in neighbors if neighbor in text_lower)
                if score > 0:
                    concept_scores[node] = score / len(neighbors)
        
        for i, (concept, score) in enumerate(concept_scores.items()):
            if i < 512:
                semantic_vector[i] = score
        
        np.random.seed(hash(text_lower) % 2**32)
        contextual_noise = np.random.normal(0, 0.01, 512)
        semantic_vector += contextual_noise
        
        norm = np.linalg.norm(semantic_vector)
        if norm > 0:
            semantic_vector = semantic_vector / norm
        
        self.cache[text_lower] = semantic_vector
        return semantic_vector
    
    def _embed_content_advanced(self, samples: List[str]) -> np.ndarray:
        if not samples:
            return np.zeros(512)
        
        content_text = ' '.join(str(s) for s in samples[:20])
        return self._embed_text_advanced(content_text)
    
    def _calculate_graph_relevance(self, column_name: str, samples: List[str]) -> float:
        relevance_scores = []
        
        for node in self.concept_graph.nodes():
            if node in column_name.lower():
                centrality = nx.degree_centrality(self.concept_graph).get(node, 0)
                relevance_scores.append(centrality)
        
        return max(relevance_scores) if relevance_scores else 0.0
    
    def _analyze_content_patterns(self, samples: List[str]) -> Dict[str, float]:
        patterns = {
            'alphanumeric': 0,
            'has_separators': 0,
            'consistent_length': 0,
            'has_prefixes': 0,
            'has_numbers': 0
        }
        
        if not samples:
            return patterns
        
        for sample in samples[:30]:
            sample_str = str(sample)
            if re.match(r'^[a-zA-Z0-9]+$', sample_str):
                patterns['alphanumeric'] += 1
            if re.search(r'[-_.]', sample_str):
                patterns['has_separators'] += 1
            if re.search(r'\d', sample_str):
                patterns['has_numbers'] += 1
        
        total_samples = len(samples[:30])
        for key in patterns:
            patterns[key] = patterns[key] / total_samples if total_samples > 0 else 0
        
        return patterns
    
    def _calculate_context_relevance(self, column_name: str, samples: List[str], 
                                   table_context: Dict[str, Any]) -> float:
        relevance = 0.0
        
        if table_context.get('is_endpoint'):
            relevance += 0.3
        if table_context.get('is_asset'):
            relevance += 0.2
        if table_context.get('data_source') == 'cmdb':
            relevance += 0.25
        
        return min(1.0, relevance)
    
    def _calculate_field_probability(self, column_name: str, samples: List[str], 
                                   field_type: str, table_context: Dict[str, Any]) -> float:
        
        field_patterns = {
            'ip_address': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
            'fqdn': [r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'],
            'mac_address': [r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$']
        }
        
        if field_type in field_patterns:
            pattern_matches = 0
            for sample in samples[:20]:
                for pattern in field_patterns[field_type]:
                    if re.match(pattern, str(sample)):
                        pattern_matches += 1
                        break
            
            return pattern_matches / len(samples[:20]) if samples else 0.0
        
        return 0.0
    
    def _generate_classification_reasoning(self, column_name: str, samples: List[str], 
                                         field_type: str) -> List[str]:
        reasoning = []
        
        if 'hostname' in column_name.lower():
            reasoning.append(f"Column name '{column_name}' contains hostname indicator")
        
        if samples and field_type == 'hostname':
            hostname_count = sum(1 for s in samples[:10] if self._matches_hostname_patterns(str(s)))
            if hostname_count > 0:
                reasoning.append(f"{hostname_count}/{len(samples[:10])} samples match hostname patterns")
        
        return reasoning
    
    def _extract_tfidf_features(self, text: str) -> np.ndarray:
        try:
            if hasattr(self.tfidf, 'vocabulary_'):
                features = self.tfidf.transform([text])
                return features.toarray()[0]
            else:
                self.tfidf.fit([text])
                return np.zeros(self.tfidf.max_features or 1000)
        except:
            return np.zeros(1000)
    
    def _extract_graph_features(self, column_names: List[str], sample_data: Dict[str, List[str]]) -> Dict[str, float]:
        centrality_scores = {}
        
        for col_name in column_names:
            centrality = 0.0
            for node in self.concept_graph.nodes():
                if node in col_name.lower():
                    centrality = max(centrality, nx.degree_centrality(self.concept_graph).get(node, 0))
            centrality_scores[col_name] = centrality
        
        return centrality_scores
    
    def _extract_pattern_features(self, sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        patterns = {}
        
        for col_name, samples in sample_data.items():
            patterns[col_name] = self._analyze_content_patterns(samples)
        
        return patterns
    
    def _calculate_semantic_density(self, column_names: List[str], sample_data: Dict[str, List[str]]) -> float:
        total_semantic_score = 0.0
        total_items = 0
        
        for col_name in column_names:
            embedding = self._embed_text_advanced(col_name)
            total_semantic_score += np.sum(np.abs(embedding))
            total_items += 1
        
        return total_semantic_score / total_items if total_items > 0 else 0.0
    
    def _create_table_embedding(self, table_name: str, column_names: List[str], 
                              sample_data: Dict[str, List[str]]) -> np.ndarray:
        
        table_text = table_name + ' ' + ' '.join(column_names)
        return self._embed_text_advanced(table_text)
    
    def _find_similar_tables(self, table_embedding: np.ndarray) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_table_confidence(self, column_classifications: Dict[str, Any]) -> float:
        if not column_classifications:
            return 0.0
        
        confidences = [c.get('confidence', 0.0) for c in column_classifications.values()]
        return statistics.mean(confidences)
    
    def _fuzzy_match(self, term1: str, term2: str) -> float:
        if term1 == term2:
            return 1.0
        
        if term1 in term2 or term2 in term1:
            shorter = min(len(term1), len(term2))
            longer = max(len(term1), len(term2))
            return shorter / longer
        
        return 0.0
    
    def _calculate_term_similarity(self, term1: str, term2: str) -> float:
        return self._fuzzy_match(term1, term2)

class AdvancedPatternRecognizer:
    def __init__(self):
        self.pattern_memory = defaultdict(list)
        self.success_tracking = defaultdict(lambda: {'success': 0, 'total': 0})
        self.clustering_model = DBSCAN(eps=0.3, min_samples=2)
        self.pattern_embeddings = {}
        
    def learn_from_classification(self, column_name: str, samples: List[str], 
                                classification: Dict[str, Any], success: bool):
        
        pattern_signature = self._create_pattern_signature(column_name, samples, classification)
        
        self.pattern_memory[classification['field_type']].append({
            'signature': pattern_signature,
            'column_name': column_name,
            'classification': classification,
            'timestamp': datetime.now(),
            'success': success
        })
        
        self.success_tracking[pattern_signature]['total'] += 1
        if success:
            self.success_tracking[pattern_signature]['success'] += 1
    
    def predict_classification(self, column_name: str, samples: List[str]) -> Dict[str, Any]:
        candidate_signature = self._create_pattern_signature(column_name, samples)
        
        best_match = None
        best_similarity = 0.0
        
        for field_type, patterns in self.pattern_memory.items():
            for pattern in patterns:
                similarity = self._calculate_pattern_similarity(candidate_signature, pattern['signature'])
                if similarity > best_similarity and similarity > 0.7:
                    best_similarity = similarity
                    best_match = pattern
        
        if best_match:
            success_rate = self.success_tracking[best_match['signature']]['success'] / max(1, self.success_tracking[best_match['signature']]['total'])
            
            return {
                'field_type': best_match['classification']['field_type'],
                'confidence': best_similarity * success_rate,
                'reasoning': [f"Matched learned pattern with {best_similarity:.2f} similarity"],
                'pattern_based': True
            }
        
        return {'field_type': 'unknown', 'confidence': 0.0, 'pattern_based': False}
    
    def _create_pattern_signature(self, column_name: str, samples: List[str], 
                                classification: Dict[str, Any] = None) -> str:
        
        name_features = [
            len(column_name),
            column_name.lower().count('_'),
            column_name.lower().count('.'),
            int('id' in column_name.lower()),
            int('name' in column_name.lower()),
            int('host' in column_name.lower())
        ]
        
        content_features = []
        if samples:
            sample_subset = samples[:10]
            content_features = [
                len(sample_subset),
                statistics.mean([len(str(s)) for s in sample_subset]) if sample_subset else 0,
                len(set(sample_subset)),
                sum(1 for s in sample_subset if re.search(r'\d', str(s))),
                sum(1 for s in sample_subset if re.search(r'[-_.]', str(s)))
            ]
        
        signature_data = name_features + content_features
        signature_str = ','.join(map(str, signature_data))
        
        return hashlib.md5(signature_str.encode()).hexdigest()[:16]
    
    def _calculate_pattern_similarity(self, sig1: str, sig2: str) -> float:
        if sig1 == sig2:
            return 1.0
        
        common_chars = sum(1 for c1, c2 in zip(sig1, sig2) if c1 == c2)
        return common_chars / max(len(sig1), len(sig2))