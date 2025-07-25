import json
import numpy as np
from collections import defaultdict
import logging
import re
import math
import statistics
from difflib import SequenceMatcher
import unicodedata
import itertools
from functools import lru_cache
import hashlib

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    from nltk.util import ngrams
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from textdistance import jaro_winkler, cosine, jaccard as td_jaccard
    TEXTDISTANCE_AVAILABLE = True
except ImportError:
    TEXTDISTANCE_AVAILABLE = False

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

logger = logging.getLogger(__name__)

class UltraIntelligentNLPMatcher:
    def __init__(self):
        from .security_taxonomy import SECURITY_TAXONOMY
        from .abbreviations import ABBREVIATION_ENGINE
        from .patterns import PATTERN_LIBRARY
        
        self.security_taxonomy = SECURITY_TAXONOMY
        self.abbreviation_engine = ABBREVIATION_ENGINE
        self.pattern_library = PATTERN_LIBRARY
        
        self.semantic_embeddings = self._build_advanced_embeddings()
        self.context_graphs = self._build_context_graphs()
        self.linguistic_rules = self._build_linguistic_rules()
        self.domain_vectors = self._build_domain_vectors()
        self.similarity_cache = {}
        
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=10000)
        
        if NLTK_AVAILABLE:
            try:
                self.stemmer = PorterStemmer()
                self.stop_words = set(stopwords.words('english'))
            except:
                nltk.download('stopwords', quiet=True)
                nltk.download('punkt', quiet=True)
        
        if NETWORKX_AVAILABLE:
            self.semantic_graph = self._build_semantic_network()

    def _build_advanced_embeddings(self):
        embeddings = {}
        vector_dim = 256
        
        for domain, categories in self.security_taxonomy.items():
            domain_base = hash(domain) % vector_dim
            for category, terms in categories.items():
                category_base = hash(category) % vector_dim
                for i, term in enumerate(terms):
                    vector = np.zeros(vector_dim)
                    vector[domain_base] = 1.0
                    vector[category_base] = 0.8
                    vector[(hash(term) + domain_base) % vector_dim] = 0.6
                    vector[(hash(term) + category_base) % vector_dim] = 0.4
                    
                    for j, other_term in enumerate(terms):
                        if i != j:
                            vector[(hash(other_term) + hash(term)) % vector_dim] = 0.2
                    
                    if np.linalg.norm(vector) > 0:
                        vector = vector / np.linalg.norm(vector)
                    
                    embeddings[term] = vector
                    
                    variations = self._generate_variations(term)
                    for variation in variations:
                        if variation not in embeddings:
                            var_vector = vector.copy()
                            var_vector[(hash(variation)) % vector_dim] = 0.3
                            if np.linalg.norm(var_vector) > 0:
                                var_vector = var_vector / np.linalg.norm(var_vector)
                            embeddings[variation] = var_vector
        
        return embeddings

    def _generate_variations(self, term):
        variations = set()
        
        parts = re.split(r'[_\-\s]+', term)
        if len(parts) > 1:
            variations.update([
                ''.join(parts), '_'.join(parts), '-'.join(parts), ' '.join(parts),
                ''.join(p[0] for p in parts if p),
            ])
            
            for i in range(len(parts)):
                if len(parts[i]) > 3:
                    abbreviated = parts.copy()
                    abbreviated[i] = parts[i][:3]
                    variations.add('_'.join(abbreviated))
        
        if '_' in term:
            variations.update([
                term.replace('_', ''), term.replace('_', '-'), 
                term.replace('_', ' '), term.replace('_', '.')
            ])
        
        if len(term) > 6:
            variations.update([term[:4], term[:5], term[:6]])
            variations.update([term[-4:], term[-5:], term[-6:]])
        
        return variations

    def _build_context_graphs(self):
        graphs = {}
        
        if not NETWORKX_AVAILABLE:
            return self._build_simple_context_graphs()
        
        for domain, categories in self.security_taxonomy.items():
            G = nx.Graph()
            all_terms = []
            
            for category, terms in categories.items():
                all_terms.extend(terms)
                G.add_node(category, type='category', domain=domain)
                G.add_node(domain, type='domain')
                G.add_edge(category, domain, weight=1.0)
                
                for term in terms:
                    G.add_node(term, type='term', category=category, domain=domain)
                    G.add_edge(term, category, weight=0.8)
                    
                    for other_term in terms:
                        if term != other_term:
                            similarity = SequenceMatcher(None, term, other_term).ratio()
                            if similarity > 0.3:
                                G.add_edge(term, other_term, weight=similarity)
            
            graphs[domain] = G
        
        return graphs

    def _build_simple_context_graphs(self):
        graphs = {}
        
        for domain, categories in self.security_taxonomy.items():
            graph = defaultdict(set)
            all_terms = []
            
            for category, terms in categories.items():
                all_terms.extend(terms)
                for term in terms:
                    graph[term].add(category)
                    graph[category].add(domain)
                    for other_term in terms:
                        if term != other_term:
                            graph[term].add(other_term)
            
            graphs[domain] = graph
        
        return graphs

    def _build_semantic_network(self):
        if not NETWORKX_AVAILABLE:
            return None
        
        G = nx.Graph()
        
        for domain, categories in self.security_taxonomy.items():
            for category, terms in categories.items():
                for term in terms:
                    G.add_node(term, domain=domain, category=category)
        
        terms = list(G.nodes())
        for i, term1 in enumerate(terms):
            for j, term2 in enumerate(terms[i+1:], i+1):
                similarity = self._calculate_semantic_similarity(term1, term2)
                if similarity > 0.3:
                    G.add_edge(term1, term2, weight=similarity)
        
        return G

    def _build_linguistic_rules(self):
        return {
            'prefix_rules': {
                'un': 'negative', 'non': 'negative', 'anti': 'opposite',
                'pre': 'before', 'post': 'after', 'sub': 'under', 'super': 'above',
                'multi': 'many', 'single': 'one', 'auto': 'automatic', 'semi': 'partial'
            },
            'suffix_rules': {
                'ing': 'action', 'ed': 'past', 'er': 'agent', 'or': 'agent',
                'tion': 'process', 'sion': 'process', 'ment': 'result',
                'ness': 'quality', 'ity': 'quality', 'able': 'capable'
            },
            'compound_rules': {
                'source_destination': {
                    'group1': ['src', 'source', 'from', 'origin', 'sender'],
                    'group2': ['dst', 'dest', 'destination', 'to', 'target', 'recipient']
                },
                'success_failure': {
                    'group1': ['success', 'ok', 'pass', 'accept', 'allow', 'grant'],
                    'group2': ['fail', 'error', 'deny', 'block', 'reject', 'refuse']
                }
            }
        }

    def _build_domain_vectors(self):
        vectors = {}
        vector_size = 128
        
        for domain, categories in self.security_taxonomy.items():
            domain_vector = np.zeros(vector_size)
            domain_hash_base = hash(domain) % vector_size
            domain_vector[domain_hash_base] = 1.0
            
            category_weights = []
            for category, terms in categories.items():
                category_hash = hash(category) % vector_size
                domain_vector[category_hash] = 0.7
                category_weights.append(len(terms))
                
                for term in terms:
                    term_hash = hash(term) % vector_size
                    domain_vector[term_hash] = max(domain_vector[term_hash], 0.3)
            
            if category_weights:
                weight_factor = statistics.mean(category_weights) / max(category_weights)
                domain_vector = domain_vector * weight_factor
                
                norm = np.linalg.norm(domain_vector)
                if norm > 0:
                    domain_vector = domain_vector / norm
            
            vectors[domain] = domain_vector
        
        return vectors

    @lru_cache(maxsize=50000)
    def advanced_normalize(self, text):
        if not text:
            return ""
        
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        text = text.lower()
        text = re.sub(r'[^\w\s]', '_', text)
        text = re.sub(r'_+', '_', text)
        text = text.strip('_')
        
        if NLTK_AVAILABLE and hasattr(self, 'stop_words'):
            words = text.split('_')
            words = [w for w in words if w not in self.stop_words and len(w) > 2]
            text = '_'.join(words)
        
        return text

    def ultra_stem(self, word):
        if not word:
            return word
        
        word = word.lower().strip()
        
        if word in self.abbreviation_engine:
            return self.abbreviation_engine[word]
        
        if NLTK_AVAILABLE and hasattr(self, 'stemmer'):
            stemmed = self.stemmer.stem(word)
            if stemmed != word and len(stemmed) >= 3:
                word = stemmed
        
        return word

    def extract_semantic_components(self, text):
        components = {
            'tokens': [],
            'patterns': [],
            'domains': [],
            'embeddings': [],
            'context': [],
            'variations': [],
            'ngrams': [],
            'complexity': 0.0
        }
        
        if not text:
            return components
        
        normalized = self.advanced_normalize(text)
        tokens = re.split(r'[_\s]+', normalized)
        components['tokens'] = [self.ultra_stem(token) for token in tokens if len(token) > 1]
        
        for pattern_type, patterns in self.pattern_library.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    components['patterns'].append(pattern_type)
        
        for domain in self.security_taxonomy:
            domain_score = 0
            for category in self.security_taxonomy[domain]:
                for token in components['tokens']:
                    if token in self.security_taxonomy[domain][category]:
                        domain_score += 1
            if domain_score > 0:
                components['domains'].append((domain, domain_score))
        
        components['domains'] = [d[0] for d in sorted(components['domains'], key=lambda x: x[1], reverse=True)]
        
        for token in components['tokens']:
            if token in self.semantic_embeddings:
                components['embeddings'].append(self.semantic_embeddings[token])
        
        for token in components['tokens']:
            components['variations'].extend(self._generate_variations(token))
        
        if len(components['tokens']) > 1:
            for n in range(2, min(4, len(components['tokens']) + 1)):
                components['ngrams'].extend(list(ngrams(components['tokens'], n)))
        
        components['complexity'] = self._calculate_text_complexity(text, components)
        
        return components

    def _calculate_text_complexity(self, text, components):
        complexity = 0.0
        complexity += min(len(text) / 50, 1.0) * 0.2
        
        if components['tokens']:
            unique_tokens = len(set(components['tokens']))
            total_tokens = len(components['tokens'])
            complexity += (unique_tokens / total_tokens) * 0.3
        
        complexity += min(len(set(components['patterns'])) / 5, 1.0) * 0.2
        complexity += min(len(components['domains']) / 3, 1.0) * 0.3
        
        return min(complexity, 1.0)

    def _calculate_semantic_similarity(self, text1, text2):
        if not text1 or not text2:
            return 0.0
        
        if TEXTDISTANCE_AVAILABLE:
            try:
                return max(
                    jaro_winkler(text1, text2),
                    cosine(text1, text2),
                    td_jaccard(text1, text2)
                )
            except:
                pass
        
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def calculate_multidimensional_similarity(self, text1, text2):
        cache_key = hashlib.md5(f"{text1}|{text2}".encode()).hexdigest()
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        comp1 = self.extract_semantic_components(text1)
        comp2 = self.extract_semantic_components(text2)
        
        similarities = {}
        
        similarities['token_overlap'] = self._jaccard_similarity(
            set(comp1['tokens']), set(comp2['tokens'])
        )
        
        similarities['pattern_match'] = self._jaccard_similarity(
            set(comp1['patterns']), set(comp2['patterns'])
        )
        
        similarities['domain_alignment'] = self._jaccard_similarity(
            set(comp1['domains']), set(comp2['domains'])
        )
        
        if comp1['embeddings'] and comp2['embeddings']:
            similarities['embedding_cosine'] = self._cosine_similarity_multi(
                comp1['embeddings'], comp2['embeddings']
            )
        else:
            similarities['embedding_cosine'] = 0.0
        
        similarities['variation_overlap'] = self._jaccard_similarity(
            set(comp1['variations']), set(comp2['variations'])
        )
        
        similarities['edit_distance'] = self._calculate_semantic_similarity(text1, text2)
        similarities['abbreviation'] = self._abbreviation_similarity(text1, text2)
        similarities['structural'] = self._structural_similarity(text1, text2)
        similarities['ngram'] = self._ngram_similarity(comp1['ngrams'], comp2['ngrams'])
        
        weights = {
            'token_overlap': 0.15,
            'pattern_match': 0.12,
            'domain_alignment': 0.20,
            'embedding_cosine': 0.18,
            'variation_overlap': 0.10,
            'edit_distance': 0.10,
            'abbreviation': 0.08,
            'structural': 0.04,
            'ngram': 0.03
        }
        
        final_score = sum(similarities[key] * weights[key] for key in similarities if key in weights)
        
        result = {
            'final_score': final_score,
            'component_scores': similarities,
            'match_evidence': self._generate_match_evidence(comp1, comp2, similarities),
            'confidence': self._calculate_confidence(similarities),
            'match_type': self._determine_match_type(final_score)
        }
        
        self.similarity_cache[cache_key] = result
        return result

    def _jaccard_similarity(self, set1, set2):
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _cosine_similarity_multi(self, embeddings1, embeddings2):
        if not embeddings1 or not embeddings2:
            return 0.0
        
        max_sim = 0.0
        for emb1 in embeddings1:
            for emb2 in embeddings2:
                sim = self._cosine_similarity(emb1, emb2)
                max_sim = max(max_sim, sim)
        
        return max_sim

    def _cosine_similarity(self, vec1, vec2):
        if isinstance(vec1, list):
            vec1 = np.array(vec1)
        if isinstance(vec2, list):
            vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        magnitude1 = np.linalg.norm(vec1)
        magnitude2 = np.linalg.norm(vec2)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return float(dot_product / (magnitude1 * magnitude2))

    def _abbreviation_similarity(self, text1, text2):
        expanded1 = text1
        expanded2 = text2
        
        for abbrev, full in self.abbreviation_engine.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            expanded1 = re.sub(pattern, full, expanded1, flags=re.IGNORECASE)
            expanded2 = re.sub(pattern, full, expanded2, flags=re.IGNORECASE)
        
        if FUZZYWUZZY_AVAILABLE:
            return fuzz.ratio(expanded1.lower(), expanded2.lower()) / 100.0
        
        return SequenceMatcher(None, expanded1.lower(), expanded2.lower()).ratio()

    def _structural_similarity(self, text1, text2):
        def get_structure(text):
            structure = []
            for char in text:
                if char.isalpha():
                    structure.append('L')
                elif char.isdigit():
                    structure.append('D')
                elif char in '_-':
                    structure.append('S')
                else:
                    structure.append('O')
            return ''.join(structure)
        
        struct1 = get_structure(text1)
        struct2 = get_structure(text2)
        
        return SequenceMatcher(None, struct1, struct2).ratio()

    def _ngram_similarity(self, ngrams1, ngrams2):
        if not ngrams1 or not ngrams2:
            return 0.0
        
        ngrams1_set = set(tuple(ng) if isinstance(ng, (list, tuple)) else ng for ng in ngrams1)
        ngrams2_set = set(tuple(ng) if isinstance(ng, (list, tuple)) else ng for ng in ngrams2)
        
        return self._jaccard_similarity(ngrams1_set, ngrams2_set)

    def _generate_match_evidence(self, comp1, comp2, similarities):
        evidence = []
        
        if similarities['token_overlap'] > 0.3:
            common_tokens = set(comp1['tokens']).intersection(set(comp2['tokens']))
            if common_tokens:
                evidence.append(f"Token overlap: {', '.join(list(common_tokens)[:3])}")
        
        if similarities['pattern_match'] > 0.4:
            common_patterns = set(comp1['patterns']).intersection(set(comp2['patterns']))
            if common_patterns:
                evidence.append(f"Pattern match: {', '.join(list(common_patterns)[:2])}")
        
        if similarities['domain_alignment'] > 0.3:
            common_domains = set(comp1['domains']).intersection(set(comp2['domains']))
            if common_domains:
                evidence.append(f"Domain alignment: {', '.join(list(common_domains)[:2])}")
        
        if similarities['embedding_cosine'] > 0.5:
            evidence.append("High semantic similarity")
        
        if similarities['abbreviation'] > 0.7:
            evidence.append("Abbreviation match")
        
        return evidence

    def _calculate_confidence(self, similarities):
        non_zero_count = sum(1 for score in similarities.values() if score > 0)
        total_metrics = len(similarities)
        
        coverage = non_zero_count / total_metrics
        consistency = 1.0 - statistics.stdev(similarities.values()) if len(similarities) > 1 else 1.0
        
        return (coverage + consistency) / 2

    def _determine_match_type(self, final_score):
        if final_score > 0.8:
            return 'ultra_semantic'
        elif final_score > 0.6:
            return 'semantic'
        elif final_score > 0.4:
            return 'partial'
        else:
            return 'weak'

    def ultra_intelligent_match(self, target, candidates, threshold=0.25):
        results = []
        
        for candidate in candidates:
            similarity_data = self.calculate_multidimensional_similarity(target, candidate)
            
            if similarity_data['final_score'] >= threshold:
                results.append({
                    'candidate': candidate,
                    'confidence': similarity_data['final_score'],
                    'evidence': similarity_data['match_evidence'],
                    'breakdown': similarity_data['component_scores'],
                    'match_type': similarity_data['match_type'],
                    'ml_confidence': similarity_data.get('confidence', 0.0)
                })
        
        results = sorted(results, key=lambda x: (-x['confidence'], -x['ml_confidence']))
        
        return results