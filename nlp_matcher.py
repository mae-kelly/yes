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

# Optional imports with fallbacks
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

logger = logging.getLogger(__name__)

class UltraIntelligentNLPMatcher:
    def __init__(self):
        # Load taxonomy and abbreviations
        try:
            from security_taxonomy import SECURITY_TAXONOMY
            from abbreviation_engine import ABBREVIATION_ENGINE
            self.security_taxonomy = SECURITY_TAXONOMY
            self.abbreviation_engine = ABBREVIATION_ENGINE
        except ImportError as e:
            logger.warning(f"Could not import taxonomy modules: {e}")
            self.security_taxonomy = self._get_enhanced_security_taxonomy()
            self.abbreviation_engine = self._get_enhanced_abbreviations()
        
        # Enhanced stopwords (no NLTK dependency)
        self.stop_words = self._get_security_stopwords()
        
        # Build enhanced matching components
        self.exact_matches = self._build_exact_match_dictionary()
        self.semantic_patterns = self._build_semantic_patterns()
        self.context_boosters = self._build_context_boosters()
        self.similarity_cache = {}
        
        logger.info(f"✅ NLP Matcher initialized with {len(self.exact_matches)} exact matches")

    def _get_security_stopwords(self):
        """Security-aware stopwords list (no NLTK dependency)"""
        return {
            # Common English stopwords
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
            'had', 'what', 'said', 'each', 'which', 'their', 'time', 'will',
            # BUT keep security-relevant words that might normally be stopwords
            # 'id', 'name', 'type', 'data', 'info', 'log', 'event' - keep these!
        }

    def _get_enhanced_security_taxonomy(self):
        """Enhanced security taxonomy focused on log/data analysis"""
        return {
            'network': {
                'addresses': ['ip', 'addr', 'address', 'host', 'hostname', 'fqdn', 'domain', 'url', 'uri'],
                'ports': ['port', 'prt', 'portnum', 'service_port', 'listen_port'],
                'protocols': ['tcp', 'udp', 'icmp', 'http', 'https', 'ftp', 'ssh', 'dns', 'dhcp', 'proto', 'protocol'],
                'traffic': ['src', 'source', 'dst', 'dest', 'destination', 'origin', 'target', 'from', 'to'],
                'connections': ['conn', 'connection', 'session', 'flow', 'stream', 'link'],
                'security': ['firewall', 'fw', 'proxy', 'nat', 'vpn', 'gateway', 'gw', 'router']
            },
            'identity': {
                'users': ['user', 'usr', 'username', 'userid', 'account', 'login', 'logon', 'signin'],
                'authentication': ['auth', 'authn', 'password', 'pwd', 'token', 'credential', 'cred'],
                'authorization': ['authz', 'permission', 'privilege', 'role', 'group', 'access'],
                'directory': ['ad', 'ldap', 'domain', 'dn', 'cn', 'sam', 'upn', 'email']
            },
            'endpoints': {
                'devices': ['computer', 'machine', 'workstation', 'server', 'endpoint', 'device', 'host'],
                'processes': ['process', 'proc', 'pid', 'ppid', 'executable', 'exe', 'binary', 'command', 'cmd'],
                'files': ['file', 'filename', 'filepath', 'path', 'directory', 'folder', 'doc', 'document'],
                'system': ['os', 'system', 'service', 'daemon', 'task', 'job', 'thread']
            },
            'security_events': {
                'threats': ['malware', 'virus', 'threat', 'attack', 'suspicious', 'malicious'],
                'detection': ['alert', 'alarm', 'signature', 'rule', 'policy', 'detection', 'match'],
                'response': ['block', 'allow', 'deny', 'permit', 'drop', 'accept', 'reject'],
                'analysis': ['hash', 'checksum', 'signature', 'digest', 'md5', 'sha', 'reputation']
            },
            'data_context': {
                'temporal': ['time', 'timestamp', 'date', 'datetime', 'epoch', 'created', 'modified', 'updated'],
                'identification': ['id', 'guid', 'uuid', 'key', 'index', 'reference', 'ref'],
                'classification': ['type', 'kind', 'category', 'class', 'level', 'priority', 'severity'],
                'measurement': ['size', 'count', 'num', 'number', 'total', 'bytes', 'length', 'volume']
            },
            'cloud': {
                'providers': ['aws', 'azure', 'gcp', 'cloud'],
                'networking': ['vpc', 'vnet', 'subnet', 'security_group', 'nacl'],
                'compute': ['instance', 'vm', 'container', 'docker', 'kubernetes', 'k8s', 'pod']
            }
        }

    def _get_enhanced_abbreviations(self):
        """Enhanced abbreviations focused on security/logging"""
        return {
            # Network
            'ip': 'internet_protocol',
            'tcp': 'transmission_control_protocol',
            'udp': 'user_datagram_protocol',
            'http': 'hypertext_transfer_protocol',
            'https': 'http_secure',
            'ftp': 'file_transfer_protocol',
            'ssh': 'secure_shell',
            'dns': 'domain_name_system',
            'dhcp': 'dynamic_host_configuration_protocol',
            'url': 'uniform_resource_locator',
            'uri': 'uniform_resource_identifier',
            'fqdn': 'fully_qualified_domain_name',
            'src': 'source',
            'dst': 'destination',
            'dest': 'destination',
            
            # Security
            'fw': 'firewall',
            'ids': 'intrusion_detection_system',
            'ips': 'intrusion_prevention_system',
            'av': 'antivirus',
            'edr': 'endpoint_detection_response',
            'siem': 'security_information_event_management',
            'auth': 'authentication',
            'authz': 'authorization',
            'authn': 'authentication',
            'mfa': 'multi_factor_authentication',
            '2fa': 'two_factor_authentication',
            'sso': 'single_sign_on',
            
            # Identity
            'ad': 'active_directory',
            'ldap': 'lightweight_directory_access_protocol',
            'usr': 'user',
            'pwd': 'password',
            'cred': 'credential',
            'acct': 'account',
            
            # System
            'os': 'operating_system',
            'proc': 'process',
            'pid': 'process_id',
            'ppid': 'parent_process_id',
            'exe': 'executable',
            'cmd': 'command',
            'svc': 'service',
            'sys': 'system',
            
            # Data
            'db': 'database',
            'json': 'javascript_object_notation',
            'xml': 'extensible_markup_language',
            'csv': 'comma_separated_values',
            'api': 'application_programming_interface',
            'guid': 'globally_unique_identifier',
            'uuid': 'universally_unique_identifier',
            
            # Cloud
            'vpc': 'virtual_private_cloud',
            'vm': 'virtual_machine',
            'k8s': 'kubernetes',
            'aws': 'amazon_web_services',
            'gcp': 'google_cloud_platform'
        }

    def _build_exact_match_dictionary(self):
        """Build comprehensive exact match dictionary"""
        exact_matches = {}
        
        # Add all taxonomy terms and their variations
        for domain, categories in self.security_taxonomy.items():
            for category, terms in categories.items():
                for term in terms:
                    variations = self._generate_comprehensive_variations(term)
                    for variation in variations:
                        if variation not in exact_matches:
                            exact_matches[variation] = []
                        exact_matches[variation].append({
                            'original_term': term,
                            'domain': domain,
                            'category': category,
                            'confidence': 1.0 if variation == term else 0.9
                        })
        
        # Add abbreviation expansions
        for abbr, expansion in self.abbreviation_engine.items():
            variations = self._generate_comprehensive_variations(abbr)
            expansion_variations = self._generate_comprehensive_variations(expansion)
            
            all_variations = variations | expansion_variations
            for variation in all_variations:
                if variation not in exact_matches:
                    exact_matches[variation] = []
                exact_matches[variation].append({
                    'original_term': abbr,
                    'expansion': expansion,
                    'confidence': 1.0 if variation in [abbr, expansion] else 0.8
                })
        
        return exact_matches

    def _generate_comprehensive_variations(self, term):
        """Generate comprehensive variations of a term"""
        variations = {term.lower()}
        
        # Basic transformations
        variations.add(term.lower().replace('_', ''))
        variations.add(term.lower().replace('_', '-'))
        variations.add(term.lower().replace('_', ' '))
        variations.add(term.lower().replace('_', '.'))
        variations.add(term.lower().replace('-', '_'))
        variations.add(term.lower().replace('-', ''))
        variations.add(term.lower().replace(' ', '_'))
        variations.add(term.lower().replace(' ', ''))
        
        # Handle common patterns
        if '_' in term or '-' in term or ' ' in term:
            parts = re.split(r'[_\-\s]+', term.lower())
            if len(parts) > 1:
                # Concatenated version
                variations.add(''.join(parts))
                # First letters acronym
                variations.add(''.join(p[0] for p in parts if p))
                # Common combinations
                variations.add('_'.join(parts))
                variations.add('-'.join(parts))
        
        # Add plurals and singulars
        if term.endswith('s') and len(term) > 3:
            variations.add(term[:-1].lower())
        elif not term.endswith('s'):
            variations.add((term + 's').lower())
        
        # Common prefixes and suffixes
        prefixes = ['src_', 'dst_', 'source_', 'dest_', 'user_', 'client_', 'server_', 'remote_', 'local_']
        suffixes = ['_id', '_name', '_addr', '_address', '_num', '_number', '_type', '_info', '_data']
        
        for prefix in prefixes:
            variations.add((prefix + term).lower())
        for suffix in suffixes:
            variations.add((term + suffix).lower())
            
        return variations

    def _build_semantic_patterns(self):
        """Build semantic matching patterns"""
        return {
            'ip_address_patterns': [
                r'.*ip.*addr.*', r'.*addr.*ip.*', r'.*source.*ip.*', r'.*dest.*ip.*',
                r'.*client.*ip.*', r'.*server.*ip.*', r'.*host.*addr.*', r'.*inet.*addr.*'
            ],
            'port_patterns': [
                r'.*port.*', r'.*prt.*', r'.*service.*port.*', r'.*listen.*port.*'
            ],
            'user_patterns': [
                r'.*user.*name.*', r'.*user.*id.*', r'.*account.*name.*', r'.*login.*name.*',
                r'.*principal.*', r'.*subject.*'
            ],
            'time_patterns': [
                r'.*time.*stamp.*', r'.*event.*time.*', r'.*created.*', r'.*modified.*',
                r'.*occurred.*', r'.*datetime.*', r'.*epoch.*'
            ],
            'url_domain_patterns': [
                r'.*url.*', r'.*domain.*', r'.*hostname.*', r'.*fqdn.*', r'.*site.*',
                r'.*web.*addr.*', r'.*dns.*name.*'
            ],
            'file_patterns': [
                r'.*file.*name.*', r'.*file.*path.*', r'.*document.*', r'.*binary.*',
                r'.*executable.*', r'.*script.*'
            ]
        }

    def _build_context_boosters(self):
        """Build context-aware boosters for better matching"""
        return {
            'network_context': {
                'terms': ['network', 'net', 'conn', 'traffic', 'packet', 'flow'],
                'boost': 0.2
            },
            'security_context': {
                'terms': ['security', 'sec', 'threat', 'alert', 'event', 'log'],
                'boost': 0.15
            },
            'identity_context': {
                'terms': ['identity', 'user', 'auth', 'login', 'account', 'credential'],
                'boost': 0.15
            },
            'system_context': {
                'terms': ['system', 'sys', 'host', 'machine', 'computer', 'endpoint'],
                'boost': 0.1
            }
        }

    def advanced_normalize(self, text):
        """Enhanced normalization for better matching"""
        if not text:
            return ""
        
        text = text.lower().strip()
        
        # Handle common separators
        text = re.sub(r'[_\-\.\s]+', '_', text)
        text = re.sub(r'_+', '_', text)
        text = text.strip('_')
        
        # Remove stop words but keep important terms
        if '_' in text:
            words = text.split('_')
            words = [w for w in words if w not in self.stop_words or len(w) <= 3]
            text = '_'.join(words)
        
        return text

    def calculate_enhanced_similarity(self, target, candidate):
        """Enhanced similarity calculation with multiple strategies"""
        
        # Normalize both terms
        norm_target = self.advanced_normalize(target)
        norm_candidate = self.advanced_normalize(candidate)
        
        similarities = {}
        
        # 1. Exact match check
        exact_score = self._check_exact_matches(norm_target, norm_candidate)
        similarities['exact_match'] = exact_score
        
        # 2. Fuzzy string matching
        if FUZZYWUZZY_AVAILABLE:
            similarities['fuzzy_ratio'] = fuzz.ratio(norm_target, norm_candidate) / 100.0
            similarities['fuzzy_partial'] = fuzz.partial_ratio(norm_target, norm_candidate) / 100.0
            similarities['fuzzy_token_sort'] = fuzz.token_sort_ratio(norm_target, norm_candidate) / 100.0
        else:
            # Fallback to basic string matching
            similarities['fuzzy_ratio'] = SequenceMatcher(None, norm_target, norm_candidate).ratio()
            similarities['fuzzy_partial'] = 0.0
            similarities['fuzzy_token_sort'] = 0.0
        
        # 3. Semantic pattern matching
        similarities['pattern_match'] = self._check_semantic_patterns(target, candidate)
        
        # 4. Abbreviation/expansion matching
        similarities['abbreviation_match'] = self._check_abbreviation_matches(norm_target, norm_candidate)
        
        # 5. Context-aware boosting
        similarities['context_boost'] = self._calculate_context_boost(target, candidate)
        
        # 6. Substring and containment
        similarities['substring_match'] = self._calculate_substring_similarity(norm_target, norm_candidate)
        
        # Weighted final score
        weights = {
            'exact_match': 0.30,
            'fuzzy_ratio': 0.20,
            'fuzzy_partial': 0.15,
            'pattern_match': 0.15,
            'abbreviation_match': 0.10,
            'fuzzy_token_sort': 0.05,
            'context_boost': 0.03,
            'substring_match': 0.02
        }
        
        final_score = sum(similarities[key] * weights[key] for key in similarities if key in weights)
        final_score = min(final_score, 1.0)
        
        # Determine match type
        if final_score > 0.85:
            match_type = 'ultra_semantic'
        elif final_score > 0.65:
            match_type = 'semantic'
        elif final_score > 0.40:
            match_type = 'partial'
        else:
            match_type = 'weak'
        
        return {
            'final_score': final_score,
            'component_scores': similarities,
            'match_type': match_type,
            'evidence': self._generate_enhanced_evidence(target, candidate, similarities)
        }

    def _check_exact_matches(self, target, candidate):
        """Check for exact matches in our dictionary"""
        max_score = 0.0
        
        # Check target variations
        target_variations = self._generate_comprehensive_variations(target)
        candidate_variations = self._generate_comprehensive_variations(candidate)
        
        for t_var in target_variations:
            if t_var in self.exact_matches:
                for c_var in candidate_variations:
                    if c_var in self.exact_matches:
                        # Check if they match the same concept
                        target_matches = self.exact_matches[t_var]
                        candidate_matches = self.exact_matches[c_var]
                        
                        for t_match in target_matches:
                            for c_match in candidate_matches:
                                if (t_match.get('original_term') == c_match.get('original_term') or
                                    t_match.get('expansion') == c_match.get('expansion')):
                                    score = min(t_match['confidence'], c_match['confidence'])
                                    max_score = max(max_score, score)
        
        return max_score

    def _check_semantic_patterns(self, target, candidate):
        """Check semantic patterns"""
        score = 0.0
        
        for pattern_type, patterns in self.semantic_patterns.items():
            target_matches = any(re.match(pattern, target.lower()) for pattern in patterns)
            candidate_matches = any(re.match(pattern, candidate.lower()) for pattern in patterns)
            
            if target_matches and candidate_matches:
                score = max(score, 0.8)
            elif target_matches or candidate_matches:
                # Partial pattern match
                if any(word in candidate.lower() for word in target.lower().split('_')):
                    score = max(score, 0.4)
        
        return score

    def _check_abbreviation_matches(self, target, candidate):
        """Check abbreviation and expansion matches"""
        score = 0.0
        
        # Check if one is abbreviation of another
        for abbr, expansion in self.abbreviation_engine.items():
            abbr_variations = self._generate_comprehensive_variations(abbr)
            exp_variations = self._generate_comprehensive_variations(expansion)
            
            target_is_abbr = any(target == var for var in abbr_variations)
            target_is_exp = any(target == var for var in exp_variations)
            candidate_is_abbr = any(candidate == var for var in abbr_variations)
            candidate_is_exp = any(candidate == var for var in exp_variations)
            
            if (target_is_abbr and candidate_is_exp) or (target_is_exp and candidate_is_abbr):
                score = max(score, 0.9)
            elif (target_is_abbr and candidate_is_abbr) or (target_is_exp and candidate_is_exp):
                score = max(score, 0.7)
        
        return score

    def _calculate_context_boost(self, target, candidate):
        """Calculate context-aware boost"""
        boost = 0.0
        
        target_words = set(re.split(r'[_\-\s]+', target.lower()))
        candidate_words = set(re.split(r'[_\-\s]+', candidate.lower()))
        
        for context_name, context_info in self.context_boosters.items():
            context_terms = set(context_info['terms'])
            
            target_context = bool(target_words & context_terms)
            candidate_context = bool(candidate_words & context_terms)
            
            if target_context and candidate_context:
                boost += context_info['boost']
        
        return min(boost, 0.3)  # Cap the boost

    def _calculate_substring_similarity(self, target, candidate):
        """Calculate substring similarity"""
        if not target or not candidate:
            return 0.0
        
        # Check if one is substring of another
        if target in candidate or candidate in target:
            longer = max(target, candidate, key=len)
            shorter = min(target, candidate, key=len)
            return len(shorter) / len(longer)
        
        # Check word overlap
        target_words = set(target.split('_'))
        candidate_words = set(candidate.split('_'))
        
        if target_words and candidate_words:
            overlap = len(target_words & candidate_words)
            total = len(target_words | candidate_words)
            return overlap / total if total > 0 else 0.0
        
        return 0.0

    def _generate_enhanced_evidence(self, target, candidate, similarities):
        """Generate detailed evidence for the match"""
        evidence = []
        
        if similarities['exact_match'] > 0.7:
            evidence.append("Exact semantic match found")
        
        if similarities.get('fuzzy_ratio', 0) > 0.8:
            evidence.append(f"High string similarity ({similarities['fuzzy_ratio']:.2f})")
        
        if similarities['pattern_match'] > 0.6:
            evidence.append("Semantic pattern match")
        
        if similarities['abbreviation_match'] > 0.7:
            evidence.append("Abbreviation/expansion match")
        
        if similarities['context_boost'] > 0.1:
            evidence.append("Strong contextual relationship")
        
        if similarities['substring_match'] > 0.5:
            evidence.append("Significant word overlap")
        
        return evidence

    def ultra_intelligent_match(self, target, candidates, threshold=0.25):
        """Enhanced matching with better accuracy"""
        results = []
        
        logger.debug(f"Matching '{target}' against {len(candidates)} candidates")
        
        for candidate in candidates:
            try:
                similarity_data = self.calculate_enhanced_similarity(target, candidate)
                
                if similarity_data['final_score'] >= threshold:
                    results.append({
                        'candidate': candidate,
                        'confidence': similarity_data['final_score'],
                        'evidence': similarity_data['evidence'],
                        'breakdown': similarity_data['component_scores'],
                        'match_type': similarity_data['match_type'],
                        'ml_confidence': similarity_data['final_score']
                    })
                    
            except Exception as e:
                logger.warning(f"Error matching {target} to {candidate}: {e}")
                continue
        
        # Sort by confidence
        results = sorted(results, key=lambda x: -x['confidence'])
        
        logger.debug(f"Found {len(results)} matches for '{target}' above threshold {threshold}")
        return results