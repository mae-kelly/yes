import json
import numpy as np
from collections import defaultdict
import logging
import re
import math
import statistics
from difflib import SequenceMatcher
import unicodedata
from functools import lru_cache
import hashlib

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    from sklearn.neural_network import MLPClassifier
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
        try:
            from security_taxonomy import SECURITY_TAXONOMY
            from abbreviation_engine import ABBREVIATION_ENGINE
            
            self.security_taxonomy = SECURITY_TAXONOMY
            self.abbreviation_engine = ABBREVIATION_ENGINE
        except ImportError as e:
            logger.warning(f"Could not import taxonomy/abbreviation modules: {e}")
            # Provide minimal fallback data
            self.security_taxonomy = self._get_default_taxonomy()
            self.abbreviation_engine = self._get_default_abbreviations()
        
        self.semantic_embeddings = self._build_advanced_embeddings()
        self.pattern_library = self._build_pattern_library()
        self.context_graphs = self._build_context_graphs()
        self.linguistic_rules = self._build_linguistic_rules()
        self.similarity_cache = {}
        
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=10000)
            self.clustering_model = KMeans(n_clusters=10, random_state=42, n_init=10)
        
        if NLTK_AVAILABLE:
            try:
                self.stemmer = PorterStemmer()
                self.stop_words = set(stopwords.words('english'))
            except:
                try:
                    nltk.download('stopwords', quiet=True)
                    nltk.download('punkt', quiet=True)
                    self.stemmer = PorterStemmer()
                    self.stop_words = set(stopwords.words('english'))
                except:
                    logger.warning("Could not download NLTK data, using fallback")
                    self.stemmer = None
                    self.stop_words = set()

    def _get_default_taxonomy(self):
        """Fallback taxonomy if import fails"""
        return {
            'network': {
                'basic': ['ip', 'port', 'protocol', 'tcp', 'udp', 'http', 'https', 'dns'],
                'security': ['firewall', 'vpn', 'ssl', 'tls']
            },
            'identity': {
                'auth': ['user', 'login', 'password', 'token', 'session'],
                'access': ['permission', 'role', 'group', 'policy']
            },
            'data': {
                'storage': ['file', 'database', 'backup', 'archive'],
                'format': ['json', 'xml', 'csv', 'binary']
            }
        }

    def _get_default_abbreviations(self):
        """Fallback abbreviations if import fails"""
        return {
            'ip': 'internet_protocol',
            'tcp': 'transmission_control_protocol',
            'udp': 'user_datagram_protocol',
            'http': 'hypertext_transfer_protocol',
            'url': 'uniform_resource_locator',
            'dns': 'domain_name_system',
            'ssl': 'secure_sockets_layer',
            'tls': 'transport_layer_security'
        }

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
        
        if '_' in term:
            variations.update([
                term.replace('_', ''), term.replace('_', '-'), 
                term.replace('_', ' '), term.replace('_', '.')
            ])
        
        if len(term) > 6:
            variations.update([term[:4], term[:5], term[:6]])
        
        if NLTK_AVAILABLE and hasattr(self, 'stemmer') and self.stemmer:
            try:
                stemmed = self.stemmer.stem(term)
                if stemmed != term:
                    variations.add(stemmed)
            except:
                pass
        
        return variations

    def _build_pattern_library(self):
        return {
            'ip_patterns': [
                r'(?:ip|addr|address)(?:_?(?:src|source|dst|dest|destination|client|server|remote|local))?',
                r'(?:src|source|dst|dest|destination|client|server|remote|local)(?:_?(?:ip|addr|address))',
            ],
            'port_patterns': [
                r'(?:port|prt)(?:_?(?:src|source|dst|dest|destination|local|remote))?',
            ],
            'time_patterns': [
                r'(?:time|timestamp|date|datetime|epoch|utc|gmt|created|modified|updated)',
            ],
            'user_patterns': [
                r'(?:user|usr|account|identity|subject|principal)(?:_?(?:name|id|email))?',
            ],
            'network_patterns': [
                r'(?:protocol|proto|transport|network|net|connection|conn|session|flow)',
                r'(?:tcp|udp|icmp|http|https|ftp|ssh|dns|dhcp)',
            ],
            'security_patterns': [
                r'(?:security|sec|threat|attack|malware|virus|signature|rule|policy)',
                r'(?:hash|checksum|digest|signature|certificate|key|token)',
            ],
            'cloud_patterns': [
                r'(?:cloud|aws|azure|gcp|vpc|vnet|subnet)',
                r'(?:container|docker|kubernetes|k8s|pod)',
            ]
        }

    def _build_context_graphs(self):
        if NETWORKX_AVAILABLE:
            return self._build_networkx_graphs()
        return self._build_simple_graphs()

    def _build_networkx_graphs(self):
        graphs = {}
        for domain, categories in self.security_taxonomy.items():
            G = nx.Graph()
            for category, terms in categories.items():
                for term in terms:
                    G.add_node(term, domain=domain, category=category)
            
            terms = list(G.nodes())
            for i, term1 in enumerate(terms):
                for j, term2 in enumerate(terms[i+1:], i+1):
                    similarity = SequenceMatcher(None, term1, term2).ratio()
                    if similarity > 0.3:
                        G.add_edge(term1, term2, weight=similarity)
            graphs[domain] = G
        return graphs

    def _build_simple_graphs(self):
        graphs = {}
        for domain, categories in self.security_taxonomy.items():
            graph = defaultdict(set)
            for category, terms in categories.items():
                for term in terms:
                    for other_term in terms:
                        if term != other_term:
                            graph[term].add(other_term)
            graphs[domain] = graph
        return graphs

    def _build_linguistic_rules(self):
        return {
            'compound_rules': {
                'source_destination': {
                    'group1': ['src', 'source', 'from', 'origin', 'sender', 'client'],
                    'group2': ['dst', 'dest', 'destination', 'to', 'target', 'server']
                },
                'create_destroy': {
                    'group1': ['create', 'add', 'insert', 'new', 'make'],
                    'group2': ['delete', 'remove', 'destroy', 'kill', 'drop']
                }
            }
        }

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
        
        if NLTK_AVAILABLE and hasattr(self, 'stop_words') and self.stop_words:
            words = text.split('_')
            words = [w for w in words if w not in self.stop_words and len(w) > 2]
            text = '_'.join(words)
        
        return text

    def extract_semantic_components(self, text):
        components = {
            'tokens': [],
            'patterns': [],
            'domains': [],
            'embeddings': [],
            'variations': []
        }
        
        if not text:
            return components
        
        normalized = self.advanced_normalize(text)
        tokens = re.split(r'[_\s]+', normalized)
        components['tokens'] = [token for token in tokens if len(token) > 1]
        
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
                components['domains'].append(domain)
        
        for token in components['tokens']:
            if token in self.semantic_embeddings:
                components['embeddings'].append(self.semantic_embeddings[token])
            components['variations'].extend(self._generate_variations(token))
        
        return components

    def calculate_multidimensional_similarity(self, text1, text2):
        cache_key = hashlib.md5(f"{text1}|{text2}".encode()).hexdigest()
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        comp1 = self.extract_semantic_components(text1)
        comp2 = self.extract_semantic_components(text2)
        
        similarities = {}
        similarities['token_overlap'] = self._jaccard_similarity(set(comp1['tokens']), set(comp2['tokens']))
        similarities['pattern_match'] = self._jaccard_similarity(set(comp1['patterns']), set(comp2['patterns']))
        similarities['domain_alignment'] = self._jaccard_similarity(set(comp1['domains']), set(comp2['domains']))
        similarities['embedding_cosine'] = self._cosine_similarity_multi(comp1['embeddings'], comp2['embeddings'])
        similarities['variation_overlap'] = self._jaccard_similarity(set(comp1['variations']), set(comp2['variations']))
        similarities['edit_distance'] = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
        if FUZZYWUZZY_AVAILABLE:
            try:
                similarities['fuzzy_ratio'] = fuzz.ratio(text1, text2) / 100.0
            except:
                similarities['fuzzy_ratio'] = 0.0
        else:
            similarities['fuzzy_ratio'] = 0.0
        
        weights = {
            'token_overlap': 0.25,
            'pattern_match': 0.20,
            'domain_alignment': 0.20,
            'embedding_cosine': 0.15,
            'variation_overlap': 0.10,
            'edit_distance': 0.05,
            'fuzzy_ratio': 0.05
        }
        
        final_score = sum(similarities[key] * weights[key] for key in similarities if key in weights)
        
        result = {
            'final_score': final_score,
            'component_scores': similarities,
            'match_evidence': self._generate_match_evidence(comp1, comp2, similarities),
            'match_type': 'ultra_semantic' if final_score > 0.8 else 'semantic' if final_score > 0.6 else 'partial'
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
                try:
                    dot_product = np.dot(emb1, emb2)
                    magnitude1 = np.linalg.norm(emb1)
                    magnitude2 = np.linalg.norm(emb2)
                    
                    if magnitude1 > 0 and magnitude2 > 0:
                        sim = dot_product / (magnitude1 * magnitude2)
                        max_sim = max(max_sim, sim)
                except:
                    continue
        
        return max_sim

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
                evidence.append(f"Domain match: {', '.join(list(common_domains)[:2])}")
        
        if similarities['embedding_cosine'] > 0.5:
            evidence.append("High semantic similarity")
        
        return evidence

    def ultra_intelligent_match(self, target, candidates, threshold=0.25):
        results = []
        
        for candidate in candidates:
            try:
                similarity_data = self.calculate_multidimensional_similarity(target, candidate)
                
                if similarity_data['final_score'] >= threshold:
                    results.append({
                        'candidate': candidate,
                        'confidence': similarity_data['final_score'],
                        'evidence': similarity_data['match_evidence'],
                        'breakdown': similarity_data['component_scores'],
                        'match_type': similarity_data['match_type'],
                        'ml_confidence': similarity_data['final_score']
                    })
            except Exception as e:
                logger.warning(f"Error matching {target} to {candidate}: {e}")
                continue
        
        results = sorted(results, key=lambda x: -x['confidence'])
        return results