# ai/content.py

import re
import ipaddress
import statistics
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
import hashlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

class AdvancedContentAnalyzer:
    def __init__(self):
        self.semantic_vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        self.pattern_library = self._build_comprehensive_patterns()
        self.semantic_cache = {}
        self.learning_memory = defaultdict(list)
        self.concept_network = self._build_concept_network()
        
    def _build_comprehensive_patterns(self):
        return {
            'hostname': {
                'strict': [
                    r'^[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]$',
                    r'^[a-zA-Z0-9]{1,63}$'
                ],
                'semantic': [
                    r'^[a-zA-Z]{2,4}[0-9]{1,6}$',
                    r'^[a-zA-Z]+\-[a-zA-Z0-9]+\-[a-zA-Z0-9]+$',
                    r'(server|srv|host|node|vm|pc|ws|desktop|laptop)',
                    r'(prod|dev|test|stage|qa|demo|lab)',
                    r'(web|app|db|sql|ad|dc|dns|dhcp|proxy|fw)',
                    r'(us|eu|ap|na|sa|asia|amer|emea|apac)',
                    r'[0-9]{1,3}$'
                ],
                'indicators': [
                    'server', 'srv', 'host', 'hostname', 'computer', 'machine', 'device',
                    'endpoint', 'node', 'workstation', 'desktop', 'laptop', 'vm', 'instance'
                ]
            },
            'ip_address': {
                'strict': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
                'semantic': [r'ip', r'addr', r'address']
            },
            'fqdn': {
                'strict': [r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'],
                'semantic': [r'fqdn', r'domain', r'dns']
            },
            'mac_address': {
                'strict': [
                    r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$',
                    r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$'
                ],
                'semantic': [r'mac', r'ethernet', r'physical']
            }
        }
    
    def _build_concept_network(self):
        G = nx.Graph()
        
        concepts = {
            'identity': {
                'hostname': ['computer', 'machine', 'device', 'endpoint', 'server', 'host', 'node'],
                'network': ['ip', 'address', 'subnet', 'domain', 'dns'],
                'infrastructure': ['datacenter', 'cloud', 'region', 'zone', 'cluster'],
                'business': ['organization', 'unit', 'department', 'division']
            }
        }
        
        for category, subcategories in concepts.items():
            G.add_node(category, type='category')
            for subcat, terms in subcategories.items():
                G.add_node(subcat, type='subcategory', parent=category)
                G.add_edge(category, subcat, weight=1.0)
                
                for term in terms:
                    G.add_node(term, type='term', parent=subcat)
                    G.add_edge(subcat, term, weight=0.8)
                    
                    for other_term in terms:
                        if term != other_term:
                            similarity = self._calculate_semantic_distance(term, other_term)
                            if similarity > 0.5:
                                G.add_edge(term, other_term, weight=similarity)
        
        return G
    
    def analyze_column_intelligent(self, name: str, values: List[str], context: Dict = None) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        if self._should_skip_column(name):
            return None
        
        clean_values = self._intelligent_cleaning(values)
        if len(clean_values) < 2:
            return None
        
        cache_key = self._generate_cache_key(name, clean_values[:10])
        if cache_key in self.semantic_cache:
            return self.semantic_cache[cache_key]
        
        semantic_analysis = self._deep_semantic_analysis(name, clean_values, context)
        pattern_analysis = self._advanced_pattern_analysis(name, clean_values)
        contextual_analysis = self._contextual_understanding(name, clean_values, context)
        
        field_scores = self._compute_unified_scores(semantic_analysis, pattern_analysis, contextual_analysis)
        
        if not field_scores:
            return None
        
        best_field, confidence = max(field_scores.items(), key=lambda x: x[1])
        
        if confidence < 0.4:
            return None
        
        metadata = {
            'semantic_features': semantic_analysis,
            'pattern_features': pattern_analysis,
            'contextual_features': contextual_analysis,
            'confidence_breakdown': field_scores,
            'learning_applied': self._apply_learned_patterns(name, clean_values),
            'quality_metrics': self._calculate_quality_metrics(clean_values)
        }
        
        result = (best_field, confidence, metadata)
        self.semantic_cache[cache_key] = result
        
        self._update_learning_memory(name, clean_values, best_field, confidence)
        
        return result
    
    def _should_skip_column(self, name: str) -> bool:
        skip_patterns = [
            r'\bid\b', r'\bkey\b', r'\bcount\b', r'\btotal\b', r'\bsum\b',
            r'\bcreated\b', r'\bupdated\b', r'\bmodified\b', r'\bdeleted\b',
            r'\bflag\b', r'\bbool\b', r'\bindex\b', r'\border\b', r'\brank\b',
            r'\bversion\b', r'\btimestamp\b', r'\bdate\b', r'\btime\b',
            r'\bstatus\b', r'\bstate\b', r'\btype\b', r'\bcategory\b'
        ]
        
        name_lower = name.lower()
        return any(re.search(pattern, name_lower) for pattern in skip_patterns)
    
    def _intelligent_cleaning(self, values: List[str]) -> List[str]:
        cleaned = []
        
        for value in values:
            if value is None:
                continue
            
            str_value = str(value).strip()
            
            if not str_value or str_value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '', '-', 'NA']:
                continue
            
            if len(str_value) > 1000:
                continue
            
            if str_value.isdigit() and len(str_value) > 10:
                continue
            
            cleaned.append(str_value)
        
        return list(set(cleaned))[:100]
    
    def _deep_semantic_analysis(self, name: str, values: List[str], context: Dict = None) -> Dict[str, Any]:
        name_embedding = self._create_semantic_embedding(name)
        content_embedding = self._create_semantic_embedding(' '.join(values[:20]))
        
        concept_scores = self._calculate_concept_scores(name, values)
        
        network_centrality = self._calculate_network_centrality(name)
        
        semantic_clusters = self._perform_semantic_clustering(values)
        
        return {
            'name_embedding': name_embedding,
            'content_embedding': content_embedding,
            'concept_scores': concept_scores,
            'network_centrality': network_centrality,
            'semantic_clusters': semantic_clusters,
            'semantic_coherence': self._calculate_semantic_coherence(values)
        }
    
    def _advanced_pattern_analysis(self, name: str, values: List[str]) -> Dict[str, Any]:
        pattern_matches = {}
        
        for field_type, patterns in self.pattern_library.items():
            strict_matches = self._count_strict_matches(values, patterns['strict'])
            semantic_matches = self._count_semantic_matches(values, patterns['semantic'])
            indicator_score = self._calculate_indicator_score(name, patterns.get('indicators', []))
            
            pattern_matches[field_type] = {
                'strict_ratio': strict_matches / len(values) if values else 0,
                'semantic_ratio': semantic_matches / len(values) if values else 0,
                'indicator_score': indicator_score,
                'combined_score': self._combine_pattern_scores(strict_matches, semantic_matches, indicator_score, len(values))
            }
        
        format_analysis = self._analyze_format_patterns(values)
        statistical_features = self._extract_statistical_features(values)
        
        return {
            'pattern_matches': pattern_matches,
            'format_analysis': format_analysis,
            'statistical_features': statistical_features
        }
    
    def _contextual_understanding(self, name: str, values: List[str], context: Dict = None) -> Dict[str, Any]:
        table_context = context or {}
        
        table_type_score = self._infer_table_type(table_context)
        source_reliability = self._assess_source_reliability(table_context)
        domain_relevance = self._calculate_domain_relevance(name, values, table_context)
        
        return {
            'table_type_score': table_type_score,
            'source_reliability': source_reliability,
            'domain_relevance': domain_relevance,
            'context_confidence': self._calculate_context_confidence(table_context)
        }
    
    def _compute_unified_scores(self, semantic: Dict, pattern: Dict, contextual: Dict) -> Dict[str, float]:
        unified_scores = {}
        
        for field_type in self.pattern_library.keys():
            semantic_score = semantic['concept_scores'].get(field_type, 0.0)
            pattern_score = pattern['pattern_matches'].get(field_type, {}).get('combined_score', 0.0)
            context_boost = contextual['domain_relevance'].get(field_type, 0.0)
            
            network_weight = semantic.get('network_centrality', 0.0)
            coherence_weight = semantic.get('semantic_coherence', 0.5)
            
            unified_score = (
                semantic_score * 0.35 * (1 + network_weight * 0.2) +
                pattern_score * 0.45 +
                context_boost * 0.2
            ) * coherence_weight
            
            if unified_score > 0.1:
                unified_scores[field_type] = unified_score
        
        return unified_scores
    
    def _create_semantic_embedding(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(300)
        
        words = text.lower().split()
        
        embedding = np.zeros(300)
        for i, word in enumerate(words[:20]):
            word_hash = hash(word) % 2**32
            np.random.seed(word_hash)
            word_vector = np.random.normal(0, 0.1, 300)
            embedding += word_vector
        
        if len(words) > 0:
            embedding = embedding / len(words)
        
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _calculate_concept_scores(self, name: str, values: List[str]) -> Dict[str, float]:
        scores = {}
        
        text_to_analyze = name.lower() + ' ' + ' '.join(str(v).lower() for v in values[:10])
        
        for field_type in self.pattern_library.keys():
            concept_score = 0.0
            
            if field_type == 'hostname':
                hostname_terms = ['host', 'server', 'computer', 'machine', 'device', 'endpoint']
                concept_score = sum(1 for term in hostname_terms if term in text_to_analyze) / len(hostname_terms)
            elif field_type == 'ip_address':
                ip_terms = ['ip', 'address', 'addr', 'network']
                concept_score = sum(1 for term in ip_terms if term in text_to_analyze) / len(ip_terms)
            elif field_type == 'fqdn':
                fqdn_terms = ['domain', 'dns', 'fqdn', 'qualified']
                concept_score = sum(1 for term in fqdn_terms if term in text_to_analyze) / len(fqdn_terms)
            
            scores[field_type] = concept_score
        
        return scores
    
    def _calculate_network_centrality(self, name: str) -> float:
        name_lower = name.lower()
        centrality_score = 0.0
        
        for node in self.concept_network.nodes():
            if node in name_lower:
                centrality = nx.degree_centrality(self.concept_network).get(node, 0.0)
                centrality_score = max(centrality_score, centrality)
        
        return centrality_score
    
    def _perform_semantic_clustering(self, values: List[str]) -> Dict[str, Any]:
        if len(values) < 3:
            return {'clusters': 1, 'coherence': 1.0}
        
        try:
            embeddings = [self._create_semantic_embedding(str(v)) for v in values[:50]]
            embeddings_array = np.array(embeddings)
            
            n_clusters = min(5, len(values) // 3)
            if n_clusters < 2:
                return {'clusters': 1, 'coherence': 1.0}
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings_array)
            
            coherence = self._calculate_cluster_coherence(embeddings_array, cluster_labels)
            
            return {
                'clusters': n_clusters,
                'coherence': coherence,
                'largest_cluster_ratio': max(Counter(cluster_labels).values()) / len(cluster_labels)
            }
        except:
            return {'clusters': 1, 'coherence': 0.5}
    
    def _calculate_semantic_coherence(self, values: List[str]) -> float:
        if len(values) < 2:
            return 1.0
        
        embeddings = [self._create_semantic_embedding(str(v)) for v in values[:20]]
        
        if not embeddings:
            return 0.5
        
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                similarities.append(similarity)
        
        return statistics.mean(similarities) if similarities else 0.5
    
    def _count_strict_matches(self, values: List[str], patterns: List[str]) -> int:
        matches = 0
        for value in values:
            for pattern in patterns:
                if re.match(pattern, str(value), re.IGNORECASE):
                    matches += 1
                    break
        return matches
    
    def _count_semantic_matches(self, values: List[str], patterns: List[str]) -> int:
        matches = 0
        for value in values:
            value_str = str(value).lower()
            for pattern in patterns:
                if re.search(pattern, value_str, re.IGNORECASE):
                    matches += 1
                    break
        return matches
    
    def _calculate_indicator_score(self, name: str, indicators: List[str]) -> float:
        name_lower = name.lower()
        matches = sum(1 for indicator in indicators if indicator in name_lower)
        return matches / len(indicators) if indicators else 0.0
    
    def _combine_pattern_scores(self, strict: int, semantic: int, indicator: float, total: int) -> float:
        if total == 0:
            return indicator * 0.5
        
        strict_ratio = strict / total
        semantic_ratio = semantic / total
        
        return (strict_ratio * 0.6 + semantic_ratio * 0.3 + indicator * 0.1)
    
    def _analyze_format_patterns(self, values: List[str]) -> Dict[str, Any]:
        if not values:
            return {}
        
        lengths = [len(str(v)) for v in values]
        
        format_patterns = []
        for value in values[:20]:
            pattern = re.sub(r'[a-zA-Z]', 'A', str(value))
            pattern = re.sub(r'[0-9]', '9', pattern)
            format_patterns.append(pattern)
        
        pattern_consistency = len(set(format_patterns)) / len(format_patterns) if format_patterns else 1.0
        
        return {
            'avg_length': statistics.mean(lengths),
            'length_variance': statistics.variance(lengths) if len(lengths) > 1 else 0,
            'pattern_consistency': 1.0 - pattern_consistency,
            'unique_patterns': len(set(format_patterns)),
            'most_common_pattern': Counter(format_patterns).most_common(1)[0][0] if format_patterns else ''
        }
    
    def _extract_statistical_features(self, values: List[str]) -> Dict[str, Any]:
        if not values:
            return {}
        
        return {
            'total_count': len(values),
            'unique_count': len(set(values)),
            'uniqueness_ratio': len(set(values)) / len(values),
            'has_numbers': sum(1 for v in values if re.search(r'\d', str(v))) / len(values),
            'has_letters': sum(1 for v in values if re.search(r'[a-zA-Z]', str(v))) / len(values),
            'has_special_chars': sum(1 for v in values if re.search(r'[^a-zA-Z0-9]', str(v))) / len(values),
            'avg_word_count': statistics.mean([len(str(v).split()) for v in values])
        }
    
    def _infer_table_type(self, context: Dict) -> Dict[str, float]:
        table_name = context.get('table_name', '').lower()
        
        type_scores = {
            'dimension': any(dim in table_name for dim in ['dim', 'dimension', 'master', 'ref']),
            'fact': any(fact in table_name for fact in ['fact', 'event', 'log', 'trans']),
            'endpoint': 'endpoint' in table_name,
            'asset': any(asset in table_name for asset in ['asset', 'device', 'machine']),
            'network': any(net in table_name for net in ['network', 'ip', 'dns']),
            'security': any(sec in table_name for sec in ['security', 'auth', 'audit'])
        }
        
        return {k: 1.0 if v else 0.0 for k, v in type_scores.items()}
    
    def _assess_source_reliability(self, context: Dict) -> float:
        source = context.get('source', '').lower()
        
        reliability_scores = {
            'cmdb': 0.9,
            'crowdstrike': 0.85,
            'splunk': 0.8,
            'chronicle': 0.8,
            'tanium': 0.75
        }
        
        return reliability_scores.get(source, 0.5)
    
    def _calculate_domain_relevance(self, name: str, values: List[str], context: Dict) -> Dict[str, float]:
        relevance = {}
        
        table_type = self._infer_table_type(context)
        
        if table_type.get('endpoint') or table_type.get('asset'):
            relevance['hostname'] = 0.8
        if table_type.get('network'):
            relevance['ip_address'] = 0.7
            relevance['fqdn'] = 0.6
        
        return relevance
    
    def _calculate_context_confidence(self, context: Dict) -> float:
        confidence_factors = []
        
        if context.get('table_name'):
            confidence_factors.append(0.8)
        if context.get('source'):
            confidence_factors.append(0.7)
        if context.get('schema_info'):
            confidence_factors.append(0.6)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5
    
    def _apply_learned_patterns(self, name: str, values: List[str]) -> Dict[str, Any]:
        learning_key = self._generate_learning_key(name, values)
        
        if learning_key in self.learning_memory:
            similar_patterns = self.learning_memory[learning_key]
            if similar_patterns:
                best_pattern = max(similar_patterns, key=lambda x: x.get('confidence', 0))
                return {
                    'pattern_found': True,
                    'confidence_boost': 0.1,
                    'learned_field_type': best_pattern.get('field_type'),
                    'pattern_count': len(similar_patterns)
                }
        
        return {'pattern_found': False}
    
    def _calculate_quality_metrics(self, values: List[str]) -> Dict[str, float]:
        if not values:
            return {}
        
        completeness = len([v for v in values if v and str(v).strip()]) / len(values)
        consistency = 1.0 - (len(set(values)) / len(values))
        
        return {
            'completeness': completeness,
            'consistency': consistency,
            'overall_quality': (completeness + consistency) / 2
        }
    
    def _generate_cache_key(self, name: str, values: List[str]) -> str:
        content = f"{name}:{':'.join(str(v) for v in values)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _update_learning_memory(self, name: str, values: List[str], field_type: str, confidence: float):
        learning_key = self._generate_learning_key(name, values)
        
        self.learning_memory[learning_key].append({
            'field_type': field_type,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        if len(self.learning_memory[learning_key]) > 10:
            self.learning_memory[learning_key] = self.learning_memory[learning_key][-10:]
    
    def _generate_learning_key(self, name: str, values: List[str]) -> str:
        name_signature = re.sub(r'[0-9]+', 'N', name.lower())
        
        if values:
            value_pattern = re.sub(r'[a-zA-Z]', 'A', str(values[0]))
            value_pattern = re.sub(r'[0-9]', '9', value_pattern)
        else:
            value_pattern = ''
        
        return f"{name_signature}:{value_pattern}"
    
    def _calculate_semantic_distance(self, term1: str, term2: str) -> float:
        embedding1 = self._create_semantic_embedding(term1)
        embedding2 = self._create_semantic_embedding(term2)
        
        similarity = cosine_similarity([embedding1], [embedding2])[0][0]
        return max(0.0, similarity)
    
    def _calculate_cluster_coherence(self, embeddings: np.ndarray, labels: np.ndarray) -> float:
        coherence_scores = []
        
        for cluster_id in set(labels):
            cluster_embeddings = embeddings[labels == cluster_id]
            if len(cluster_embeddings) > 1:
                cluster_similarities = []
                for i in range(len(cluster_embeddings)):
                    for j in range(i + 1, len(cluster_embeddings)):
                        sim = cosine_similarity([cluster_embeddings[i]], [cluster_embeddings[j]])[0][0]
                        cluster_similarities.append(sim)
                
                if cluster_similarities:
                    coherence_scores.append(statistics.mean(cluster_similarities))
        
        return statistics.mean(coherence_scores) if coherence_scores else 0.5

class EnhancedValidationEngine:
    def __init__(self):
        self.validation_cache = {}
        self.learned_validators = defaultdict(list)
        
    def validate_field_advanced(self, field_type: str, values: List[str], 
                               context: Dict = None) -> Dict[str, Any]:
        
        cache_key = f"{field_type}:{hash(tuple(values[:10]))}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
        
        if field_type == 'hostname':
            result = self._validate_hostname_advanced(values, context)
        elif field_type == 'ip_address':
            result = self._validate_ip_advanced(values)
        elif field_type == 'fqdn':
            result = self._validate_fqdn_advanced(values)
        elif field_type == 'mac_address':
            result = self._validate_mac_advanced(values)
        else:
            result = self._validate_generic(field_type, values, context)
        
        self.validation_cache[cache_key] = result
        return result
    
    def _validate_hostname_advanced(self, values: List[str], context: Dict = None) -> Dict[str, Any]:
        if not values:
            return {'valid_ratio': 0.0, 'confidence': 0.0}
        
        validation_results = []
        semantic_scores = []
        
        for value in values[:50]:
            basic_valid = self._is_valid_hostname_basic(value)
            semantic_score = self._calculate_hostname_semantic_score(value)
            context_score = self._calculate_hostname_context_score(value, context)
            
            combined_score = (basic_valid * 0.5 + semantic_score * 0.3 + context_score * 0.2)
            validation_results.append(combined_score > 0.6)
            semantic_scores.append(combined_score)
        
        valid_ratio = sum(validation_results) / len(validation_results)
        avg_semantic = statistics.mean(semantic_scores)
        
        return {
            'valid_ratio': valid_ratio,
            'semantic_score': avg_semantic,
            'confidence': (valid_ratio + avg_semantic) / 2,
            'sample_analysis': self._analyze_hostname_samples(values[:10])
        }
    
    def _is_valid_hostname_basic(self, value: str) -> bool:
        if not isinstance(value, str) or not (1 <= len(value) <= 253):
            return False
        
        if value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
            return False
        
        patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)
    
    def _calculate_hostname_semantic_score(self, value: str) -> float:
        if not value:
            return 0.0
        
        value_lower = value.lower()
        
        semantic_indicators = [
            'srv', 'server', 'host', 'node', 'vm', 'pc', 'ws', 'desktop',
            'web', 'app', 'db', 'sql', 'ad', 'dc', 'dns', 'dhcp',
            'prod', 'dev', 'test', 'stage', 'qa', 'demo', 'lab'
        ]
        
        indicator_score = sum(1 for indicator in semantic_indicators if indicator in value_lower)
        normalized_score = min(1.0, indicator_score / 3.0)
        
        has_structure = bool(re.search(r'[-_.]', value)) or bool(re.search(r'\d', value))
        structure_score = 0.5 if has_structure else 0.0
        
        return (normalized_score * 0.7 + structure_score * 0.3)
    
    def _calculate_hostname_context_score(self, value: str, context: Dict = None) -> float:
        if not context:
            return 0.5
        
        score = 0.5
        
        table_name = context.get('table_name', '').lower()
        if 'endpoint' in table_name or 'device' in table_name:
            score += 0.3
        
        source = context.get('source', '').lower()
        if source in ['cmdb', 'crowdstrike']:
            score += 0.2
        
        return min(1.0, score)
    
    def _analyze_hostname_samples(self, samples: List[str]) -> Dict[str, Any]:
        if not samples:
            return {}
        
        analysis = {
            'avg_length': statistics.mean([len(s) for s in samples]),
            'has_separators': sum(1 for s in samples if re.search(r'[-_.]', s)) / len(samples),
            'has_numbers': sum(1 for s in samples if re.search(r'\d', s)) / len(samples),
            'common_prefixes': self._find_common_patterns(samples, 'prefix'),
            'common_suffixes': self._find_common_patterns(samples, 'suffix')
        }
        
        return analysis
    
    def _find_common_patterns(self, samples: List[str], pattern_type: str) -> List[str]:
        patterns = Counter()
        
        for sample in samples:
            if pattern_type == 'prefix':
                for i in range(2, min(6, len(sample))):
                    patterns[sample[:i]] += 1
            elif pattern_type == 'suffix':
                for i in range(2, min(6, len(sample))):
                    patterns[sample[-i:]] += 1
        
        threshold = max(2, len(samples) * 0.3)
        return [pattern for pattern, count in patterns.most_common(5) if count >= threshold]
    
    def _validate_ip_advanced(self, values: List[str]) -> Dict[str, Any]:
        valid_count = 0
        for value in values[:50]:
            try:
                ipaddress.ip_address(value.strip())
                valid_count += 1
            except:
                pass
        
        return {
            'valid_ratio': valid_count / len(values[:50]) if values else 0.0,
            'confidence': valid_count / len(values[:50]) if values else 0.0
        }
    
    def _validate_fqdn_advanced(self, values: List[str]) -> Dict[str, Any]:
        valid_count = 0
        for value in values[:50]:
            if self._is_valid_fqdn(value):
                valid_count += 1
        
        return {
            'valid_ratio': valid_count / len(values[:50]) if values else 0.0,
            'confidence': valid_count / len(values[:50]) if values else 0.0
        }
    
    def _validate_mac_advanced(self, values: List[str]) -> Dict[str, Any]:
        valid_count = 0
        patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2},
            r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}
        ]
        
        for value in values[:50]:
            if any(re.match(pattern, str(value).strip()) for pattern in patterns):
                valid_count += 1
        
        return {
            'valid_ratio': valid_count / len(values[:50]) if values else 0.0,
            'confidence': valid_count / len(values[:50]) if values else 0.0
        }
    
    def _validate_generic(self, field_type: str, values: List[str], context: Dict = None) -> Dict[str, Any]:
        return {
            'valid_ratio': 0.5,
            'confidence': 0.5,
            'method': 'generic_validation'
        }
    
    def _is_valid_fqdn(self, value: str) -> bool:
        if not isinstance(value, str) or not (4 <= len(value) <= 253):
            return False
        
        if value.count('.') < 1:
            return False
        
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}
        return bool(re.match(pattern, value, re.IGNORECASE))