import json
import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set
import logging
import re
import math
from difflib import SequenceMatcher
import unicodedata
import itertools
from functools import lru_cache
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltraIntelligentNLPMatcher:
    def __init__(self):
        self.security_taxonomy = {
            'network': {
                'layer2': ['mac', 'ethernet', 'switch', 'vlan', 'trunk', 'spanning_tree', 'arp'],
                'layer3': ['ip', 'routing', 'subnet', 'gateway', 'router', 'ospf', 'bgp', 'rip'],
                'layer4': ['tcp', 'udp', 'port', 'socket', 'connection', 'session', 'flow'],
                'layer7': ['http', 'https', 'ftp', 'smtp', 'dns', 'dhcp', 'snmp', 'ssh', 'telnet'],
                'topology': ['source', 'destination', 'origin', 'target', 'from', 'to', 'via', 'through'],
                'metrics': ['bandwidth', 'latency', 'jitter', 'packet_loss', 'throughput', 'utilization'],
                'protocols': ['icmp', 'igmp', 'gre', 'ipsec', 'vpn', 'mpls', 'vxlan'],
                'wireless': ['wifi', 'wlan', 'ssid', 'bssid', 'wpa', 'wep', 'radius', '802.11']
            },
            'security': {
                'threats': ['malware', 'virus', 'trojan', 'worm', 'ransomware', 'spyware', 'adware', 'rootkit', 'botnet', 'apt'],
                'attacks': ['dos', 'ddos', 'mitm', 'phishing', 'spoofing', 'hijacking', 'injection', 'overflow', 'poisoning'],
                'vulnerabilities': ['cve', 'exploit', 'zero_day', 'buffer_overflow', 'sql_injection', 'xss', 'csrf', 'lfi', 'rfi'],
                'controls': ['firewall', 'ids', 'ips', 'waf', 'proxy', 'antivirus', 'edr', 'dlp', 'sandbox', 'honeypot'],
                'cryptography': ['encryption', 'decryption', 'hash', 'digest', 'signature', 'certificate', 'pki', 'ssl', 'tls'],
                'analysis': ['forensics', 'incident', 'investigation', 'attribution', 'indicators', 'ioc', 'ttp', 'mitre'],
                'intelligence': ['threat_intel', 'feeds', 'reputation', 'blacklist', 'whitelist', 'indicators', 'yara', 'sigma']
            },
            'identity': {
                'authentication': ['login', 'logon', 'signin', 'sso', 'mfa', '2fa', 'biometric', 'token', 'password', 'pin'],
                'authorization': ['permission', 'privilege', 'access', 'role', 'group', 'policy', 'acl', 'rbac', 'abac'],
                'provisioning': ['create', 'modify', 'delete', 'disable', 'enable', 'suspend', 'unlock', 'reset'],
                'federation': ['saml', 'oauth', 'oidc', 'jwt', 'kerberos', 'ldap', 'ad', 'radius', 'tacacs'],
                'lifecycle': ['joiner', 'mover', 'leaver', 'onboard', 'offboard', 'transfer', 'promote', 'terminate'],
                'attributes': ['username', 'email', 'domain', 'group', 'role', 'department', 'title', 'manager']
            },
            'data': {
                'classification': ['public', 'internal', 'confidential', 'restricted', 'secret', 'top_secret', 'pii', 'phi'],
                'handling': ['create', 'read', 'update', 'delete', 'copy', 'move', 'share', 'print', 'download'],
                'protection': ['encryption', 'masking', 'tokenization', 'anonymization', 'pseudonymization', 'redaction'],
                'formats': ['json', 'xml', 'csv', 'pdf', 'doc', 'xls', 'txt', 'binary', 'compressed', 'archive'],
                'storage': ['database', 'file', 'object', 'block', 'cloud', 'on_premise', 'hybrid', 'backup'],
                'governance': ['retention', 'disposal', 'archival', 'compliance', 'audit', 'lineage', 'catalog']
            },
            'operations': {
                'monitoring': ['log', 'event', 'alert', 'alarm', 'notification', 'dashboard', 'metric', 'kpi'],
                'analysis': ['correlation', 'aggregation', 'enrichment', 'normalization', 'parsing', 'filtering'],
                'response': ['incident', 'investigation', 'containment', 'eradication', 'recovery', 'lessons_learned'],
                'automation': ['orchestration', 'playbook', 'workflow', 'script', 'api', 'webhook', 'trigger'],
                'maintenance': ['patch', 'update', 'upgrade', 'configuration', 'deployment', 'rollback', 'backup'],
                'compliance': ['audit', 'assessment', 'scan', 'validation', 'certification', 'attestation', 'evidence']
            },
            'infrastructure': {
                'compute': ['server', 'vm', 'container', 'pod', 'node', 'cluster', 'hypervisor', 'docker', 'kubernetes'],
                'storage': ['disk', 'volume', 'partition', 'filesystem', 'raid', 'san', 'nas', 'object_store'],
                'network': ['switch', 'router', 'firewall', 'load_balancer', 'proxy', 'gateway', 'bridge', 'hub'],
                'cloud': ['aws', 'azure', 'gcp', 'hybrid', 'multi_cloud', 'saas', 'paas', 'iaas', 'serverless'],
                'platforms': ['windows', 'linux', 'unix', 'macos', 'android', 'ios', 'embedded', 'iot'],
                'services': ['web', 'database', 'application', 'middleware', 'message_queue', 'cache', 'cdn']
            }
        }
        
        # Add alias for backward compatibility
        self.ao1_metric_requirements = self.ao1_visibility_requirements

    def __getattr__(self, name):
        """Handle missing attributes gracefully for backward compatibility"""
        if name == 'ao1_metric_requirements':
            return self.ao1_visibility_requirements
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        self.semantic_embeddings = self._build_advanced_embeddings()
        self.pattern_library = self._build_pattern_library()
        self.abbreviation_engine = self._build_abbreviation_engine()
        self.context_graphs = self._build_context_graphs()
        self.linguistic_rules = self._build_linguistic_rules()
        self.domain_vectors = self._build_domain_vectors()
        self.similarity_cache = {}
        
    def _build_advanced_embeddings(self):
        embeddings = {}
        vector_dim = 128
        
        for domain, categories in self.security_taxonomy.items():
            domain_base = hash(domain) % vector_dim
            for category, terms in categories.items():
                category_base = hash(category) % vector_dim
                for i, term in enumerate(terms):
                    vector = [0.0] * vector_dim
                    vector[domain_base] = 1.0
                    vector[category_base] = 0.8
                    vector[(hash(term) + domain_base) % vector_dim] = 0.6
                    vector[(hash(term) + category_base) % vector_dim] = 0.4
                    
                    for j, other_term in enumerate(terms):
                        if i != j:
                            vector[(hash(other_term) + hash(term)) % vector_dim] = 0.2
                    
                    embeddings[term] = vector
                    
                    variations = self._generate_variations(term)
                    for variation in variations:
                        if variation not in embeddings:
                            var_vector = vector.copy()
                            var_vector[(hash(variation)) % vector_dim] = 0.3
                            embeddings[variation] = var_vector
        
        return embeddings
    
    def _generate_variations(self, term):
        variations = set()
        
        parts = re.split(r'[_\-\s]+', term)
        if len(parts) > 1:
            variations.add(''.join(parts))
            variations.add('_'.join(parts))
            variations.add('-'.join(parts))
            variations.add(' '.join(parts))
            
            for i in range(len(parts)):
                if len(parts[i]) > 3:
                    abbreviated = parts.copy()
                    abbreviated[i] = parts[i][:3]
                    variations.add('_'.join(abbreviated))
        
        if '_' in term:
            variations.add(term.replace('_', ''))
            variations.add(term.replace('_', '-'))
            variations.add(term.replace('_', ' '))
        
        if len(term) > 6:
            variations.add(term[:4])
            variations.add(term[:5])
        
        return variations
    
    def _build_pattern_library(self):
        return {
            'ip_patterns': [
                r'(?:ip|addr|address)(?:_?(?:src|source|dst|dest|destination|client|server|remote|local|public|private))?',
                r'(?:src|source|dst|dest|destination|client|server|remote|local)(?:_?(?:ip|addr|address))',
                r'(?:v4|v6|ipv4|ipv6)(?:_?(?:addr|address))?'
            ],
            'port_patterns': [
                r'(?:port|prt)(?:_?(?:src|source|dst|dest|destination|local|remote|listen|bind))?',
                r'(?:src|source|dst|dest|destination|local|remote)(?:_?(?:port|prt))'
            ],
            'time_patterns': [
                r'(?:time|timestamp|date|datetime|epoch|utc|gmt|created|modified|updated|start|end|begin|finish|occurred|when)',
                r'(?:create|mod|update|start|end|begin|finish|occur)(?:_?(?:time|date|timestamp))',
                r'(?:year|month|day|hour|minute|second|millisecond|microsecond)(?:s)?'
            ],
            'user_patterns': [
                r'(?:user|usr|account|identity|subject|principal|actor|person|individual)(?:_?(?:name|id|email|domain))?',
                r'(?:login|logon|signin|username|userid|email|upn|dn|cn|sam)(?:_?(?:name|id))?'
            ],
            'action_patterns': [
                r'(?:action|operation|activity|event|command|request|response|result|outcome|status|verdict)',
                r'(?:allow|deny|block|drop|permit|reject|accept|forward|route|redirect|proxy)',
                r'(?:success|fail|error|ok|pass|deny|grant|revoke|create|delete|modify|update)'
            ],
            'file_patterns': [
                r'(?:file|filename|filepath|path|document|doc|binary|executable|exe|dll|script)',
                r'(?:directory|folder|dir|location|parent|child|root|base|full)(?:_?(?:path|name))',
                r'(?:extension|ext|type|format|mime|content)(?:_?(?:type))?'
            ],
            'process_patterns': [
                r'(?:process|proc|program|application|app|service|daemon|task|job|thread)',
                r'(?:pid|ppid|process_id|parent|child|executable|image|command|cmd)(?:_?(?:line|name|path))?'
            ],
            'network_patterns': [
                r'(?:protocol|proto|transport|network|net|connection|conn|session|flow|stream)',
                r'(?:tcp|udp|icmp|http|https|ftp|ssh|dns|dhcp|smtp|pop|imap|snmp)',
                r'(?:packet|frame|segment|datagram|message|payload|header|body)'
            ],
            'security_patterns': [
                r'(?:security|sec|threat|attack|malware|virus|signature|rule|policy|alert|alarm)',
                r'(?:hash|checksum|digest|signature|certificate|key|token|credential|password)',
                r'(?:encrypt|decrypt|cipher|crypto|ssl|tls|pki|x509|rsa|aes|sha|md5)'
            ],
            'size_patterns': [
                r'(?:size|bytes|length|count|volume|amount|quantity|total|sum|max|min|avg)',
                r'(?:kb|mb|gb|tb|kilobyte|megabyte|gigabyte|terabyte)(?:s)?'
            ],
            'geo_patterns': [
                r'(?:country|region|city|state|province|location|geo|geographic|latitude|longitude|coordinates)',
                r'(?:continent|timezone|locale|language|culture|iso|cc|country_code)'
            ]
        }
    
    def _build_abbreviation_engine(self):
        base_abbrevs = {
            'auth': 'authentication', 'authz': 'authorization', 'fw': 'firewall', 'gw': 'gateway',
            'ids': 'intrusion_detection', 'ips': 'intrusion_prevention', 'waf': 'web_application_firewall',
            'src': 'source', 'dst': 'destination', 'dest': 'destination', 'orig': 'origin',
            'usr': 'user', 'usr_id': 'user_id', 'uid': 'user_id', 'gid': 'group_id',
            'pwd': 'password', 'passwd': 'password', 'cred': 'credential', 'cert': 'certificate',
            'conn': 'connection', 'sess': 'session', 'req': 'request', 'resp': 'response',
            'msg': 'message', 'sig': 'signature', 'proc': 'process', 'svc': 'service',
            'sys': 'system', 'os': 'operating_system', 'net': 'network', 'addr': 'address',
            'proto': 'protocol', 'url': 'uniform_resource_locator', 'uri': 'uniform_resource_identifier',
            'fqdn': 'fully_qualified_domain_name', 'dns': 'domain_name_system',
            'http': 'hypertext_transfer_protocol', 'https': 'http_secure', 'ftp': 'file_transfer_protocol',
            'ssh': 'secure_shell', 'ssl': 'secure_sockets_layer', 'tls': 'transport_layer_security',
            'tcp': 'transmission_control_protocol', 'udp': 'user_datagram_protocol',
            'icmp': 'internet_control_message_protocol', 'dhcp': 'dynamic_host_configuration_protocol',
            'smtp': 'simple_mail_transfer_protocol', 'pop': 'post_office_protocol',
            'imap': 'internet_message_access_protocol', 'snmp': 'simple_network_management_protocol',
            'ldap': 'lightweight_directory_access_protocol', 'ad': 'active_directory',
            'saml': 'security_assertion_markup_language', 'oauth': 'open_authorization',
            'jwt': 'json_web_token', 'api': 'application_programming_interface',
            'sql': 'structured_query_language', 'db': 'database', 'dbms': 'database_management_system',
            'xss': 'cross_site_scripting', 'csrf': 'cross_site_request_forgery',
            'sqli': 'sql_injection', 'lfi': 'local_file_inclusion', 'rfi': 'remote_file_inclusion',
            'rce': 'remote_code_execution', 'dos': 'denial_of_service', 'ddos': 'distributed_denial_of_service',
            'av': 'antivirus', 'edr': 'endpoint_detection_response', 'dlp': 'data_loss_prevention',
            'siem': 'security_information_event_management', 'soar': 'security_orchestration_automated_response',
            'soc': 'security_operations_center', 'noc': 'network_operations_center',
            'iot': 'internet_of_things', 'scada': 'supervisory_control_data_acquisition',
            'vpn': 'virtual_private_network', 'wan': 'wide_area_network', 'lan': 'local_area_network',
            'vlan': 'virtual_local_area_network', 'nat': 'network_address_translation',
            'pat': 'port_address_translation', 'acl': 'access_control_list',
            'rbac': 'role_based_access_control', 'abac': 'attribute_based_access_control',
            'mfa': 'multi_factor_authentication', '2fa': 'two_factor_authentication',
            'sso': 'single_sign_on', 'pki': 'public_key_infrastructure',
            'ca': 'certificate_authority', 'crl': 'certificate_revocation_list',
            'ocsp': 'online_certificate_status_protocol', 'pem': 'privacy_enhanced_mail',
            'der': 'distinguished_encoding_rules', 'pkcs': 'public_key_cryptography_standards',
            'aes': 'advanced_encryption_standard', 'des': 'data_encryption_standard',
            'rsa': 'rivest_shamir_adleman', 'dsa': 'digital_signature_algorithm',
            'ecdsa': 'elliptic_curve_digital_signature_algorithm', 'sha': 'secure_hash_algorithm',
            'md5': 'message_digest_5', 'hmac': 'hash_based_message_authentication_code',
            'vm': 'virtual_machine', 'os': 'operating_system', 'cpu': 'central_processing_unit',
            'gpu': 'graphics_processing_unit', 'ram': 'random_access_memory', 'rom': 'read_only_memory',
            'hdd': 'hard_disk_drive', 'ssd': 'solid_state_drive', 'usb': 'universal_serial_bus',
            'cd': 'compact_disc', 'dvd': 'digital_versatile_disc', 'blu': 'blu_ray',
            'iso': 'international_organization_standardization', 'utf': 'unicode_transformation_format',
            'ascii': 'american_standard_code_information_interchange', 'mime': 'multipurpose_internet_mail_extensions',
            'json': 'javascript_object_notation', 'xml': 'extensible_markup_language',
            'html': 'hypertext_markup_language', 'css': 'cascading_style_sheets',
            'js': 'javascript', 'php': 'php_hypertext_preprocessor', 'asp': 'active_server_pages',
            'jsp': 'java_server_pages'
        }
        
        extended_abbrevs = {}
        for abbrev, full in base_abbrevs.items():
            extended_abbrevs[abbrev] = full
            extended_abbrevs[abbrev.upper()] = full
            extended_abbrevs[abbrev.capitalize()] = full
            
            if '_' in full:
                parts = full.split('_')
                if len(parts) == 2:
                    extended_abbrevs[abbrev + '_' + parts[1]] = full
                    extended_abbrevs[parts[0] + '_' + abbrev] = full
        
        return extended_abbrevs
    
    def _build_context_graphs(self):
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
            
            for i, term1 in enumerate(all_terms):
                for j, term2 in enumerate(all_terms[i+1:], i+1):
                    similarity = SequenceMatcher(None, term1, term2).ratio()
                    if similarity > 0.6:
                        graph[term1].add(term2)
                        graph[term2].add(term1)
            
            graphs[domain] = graph
        
        return graphs
    
    def _build_linguistic_rules(self):
        return {
            'prefix_rules': {
                'un': 'negative',
                'non': 'negative', 
                'anti': 'opposite',
                'pre': 'before',
                'post': 'after',
                'sub': 'under',
                'super': 'above',
                'multi': 'many',
                'single': 'one',
                'auto': 'automatic',
                'semi': 'partial',
                'pseudo': 'fake',
                'meta': 'about'
            },
            'suffix_rules': {
                'ing': 'action',
                'ed': 'past',
                'er': 'agent',
                'or': 'agent',
                'tion': 'process',
                'sion': 'process',
                'ment': 'result',
                'ness': 'quality',
                'ity': 'quality',
                'able': 'capable',
                'ible': 'capable',
                'ful': 'full_of',
                'less': 'without',
                'ous': 'having',
                'ive': 'tendency',
                'al': 'relating_to',
                'ic': 'relating_to',
                'ly': 'manner'
            },
            'compound_rules': {
                'source_destination': ['src', 'source', 'from', 'origin', 'sender'] + ['dst', 'dest', 'destination', 'to', 'target', 'recipient'],
                'input_output': ['in', 'input', 'incoming', 'inbound', 'ingress'] + ['out', 'output', 'outgoing', 'outbound', 'egress'],
                'start_end': ['start', 'begin', 'initial', 'first', 'open'] + ['end', 'finish', 'final', 'last', 'close'],
                'success_failure': ['success', 'ok', 'pass', 'accept', 'allow', 'grant', 'yes'] + ['fail', 'error', 'deny', 'block', 'reject', 'no'],
                'create_destroy': ['create', 'add', 'insert', 'new', 'make', 'build'] + ['delete', 'remove', 'destroy', 'kill', 'drop'],
                'read_write': ['read', 'get', 'fetch', 'retrieve', 'select', 'view'] + ['write', 'set', 'put', 'update', 'modify', 'change'],
                'public_private': ['public', 'external', 'internet', 'wan', 'outside'] + ['private', 'internal', 'intranet', 'lan', 'inside'],
                'high_low': ['high', 'max', 'maximum', 'top', 'upper'] + ['low', 'min', 'minimum', 'bottom', 'lower']
            }
        }
    
    def _build_domain_vectors(self):
        vectors = {}
        vector_size = 64
        
        for domain, categories in self.security_taxonomy.items():
            domain_vector = [0.0] * vector_size
            domain_hash_base = hash(domain) % vector_size
            domain_vector[domain_hash_base] = 1.0
            
            category_count = 0
            for category, terms in categories.items():
                category_hash = hash(category) % vector_size
                domain_vector[category_hash] = 0.7
                category_count += 1
                
                for term in terms:
                    term_hash = hash(term) % vector_size
                    domain_vector[term_hash] = max(domain_vector[term_hash], 0.3)
            
            if category_count > 0:
                for i in range(vector_size):
                    domain_vector[i] = domain_vector[i] / math.sqrt(category_count)
            
            vectors[domain] = domain_vector
        
        return vectors
    
    @lru_cache(maxsize=10000)
    def advanced_normalize(self, text):
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        text = text.lower()
        text = re.sub(r'[^\w\s]', '_', text)
        text = re.sub(r'_+', '_', text)
        text = text.strip('_')
        return text
    
    def ultra_stem(self, word):
        word = word.lower().strip()
        
        if word in self.abbreviation_engine:
            return self.abbreviation_engine[word]
        
        original_word = word
        
        for prefix, meaning in self.linguistic_rules['prefix_rules'].items():
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                word = word[len(prefix):]
                break
        
        for suffix, meaning in self.linguistic_rules['suffix_rules'].items():
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                stem = word[:-len(suffix)]
                if len(stem) >= 3:
                    word = stem
                break
        
        if word != original_word:
            return word
        
        vowels = 'aeiou'
        if len(word) > 6:
            compressed = ''.join(c for i, c in enumerate(word) if i == 0 or c not in vowels or word[i-1] in vowels)
            if len(compressed) >= 4:
                return compressed
        
        return word
    
    def extract_semantic_components(self, text):
        components = {
            'tokens': [],
            'patterns': [],
            'domains': [],
            'embeddings': [],
            'context': [],
            'variations': []
        }
        
        normalized = self.advanced_normalize(text)
        tokens = re.split(r'[_\s]+', normalized)
        components['tokens'] = [self.ultra_stem(token) for token in tokens if len(token) > 1]
        
        for pattern_type, patterns in self.pattern_library.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    components['patterns'].append(pattern_type)
        
        for domain in self.security_taxonomy:
            if any(token in self.security_taxonomy[domain].get(cat, []) 
                   for cat in self.security_taxonomy[domain] 
                   for token in components['tokens']):
                components['domains'].append(domain)
        
        for token in components['tokens']:
            if token in self.semantic_embeddings:
                components['embeddings'].append(self.semantic_embeddings[token])
        
        for rule_type, rule_groups in self.linguistic_rules['compound_rules'].items():
            mid = len(rule_groups) // 2
            group1, group2 = rule_groups[:mid], rule_groups[mid:]
            if (any(g in components['tokens'] for g in group1) or 
                any(g in components['tokens'] for g in group2)):
                components['context'].append(rule_type)
        
        for token in components['tokens']:
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
        
        if comp1['embeddings'] and comp2['embeddings']:
            similarities['embedding_cosine'] = self._cosine_similarity_multi(comp1['embeddings'], comp2['embeddings'])
        else:
            similarities['embedding_cosine'] = 0.0
        
        similarities['context_match'] = self._jaccard_similarity(set(comp1['context']), set(comp2['context']))
        
        similarities['variation_overlap'] = self._jaccard_similarity(set(comp1['variations']), set(comp2['variations']))
        
        similarities['edit_distance'] = SequenceMatcher(None, self.advanced_normalize(text1), self.advanced_normalize(text2)).ratio()
        
        similarities['abbreviation'] = self._abbreviation_similarity(text1, text2)
        
        similarities['phonetic'] = self._phonetic_similarity(text1, text2)
        
        similarities['structural'] = self._structural_similarity(text1, text2)
        
        similarities['semantic_graph'] = self._graph_similarity(comp1['tokens'], comp2['tokens'])
        
        weights = {
            'token_overlap': 0.15,
            'pattern_match': 0.12,
            'domain_alignment': 0.18,
            'embedding_cosine': 0.16,
            'context_match': 0.10,
            'variation_overlap': 0.08,
            'edit_distance': 0.07,
            'abbreviation': 0.06,
            'phonetic': 0.03,
            'structural': 0.03,
            'semantic_graph': 0.02
        }
        
        final_score = sum(similarities[key] * weights[key] for key in similarities if key in weights)
        
        result = {
            'final_score': final_score,
            'component_scores': similarities,
            'match_evidence': self._generate_match_evidence(comp1, comp2, similarities)
        }
        
        self.similarity_cache[cache_key] = result
        return result
    
    def _jaccard_similarity(self, set1, set2):
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        return len(set1.intersection(set2)) / len(set1.union(set2))
    
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
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _abbreviation_similarity(self, text1, text2):
        expanded1 = text1
        expanded2 = text2
        
        for abbrev, full in self.abbreviation_engine.items():
            expanded1 = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, expanded1, flags=re.IGNORECASE)
            expanded2 = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, expanded2, flags=re.IGNORECASE)
        
        return SequenceMatcher(None, expanded1.lower(), expanded2.lower()).ratio()
    
    def _phonetic_similarity(self, text1, text2):
        def soundex(word):
            if not word:
                return ""
            
            word = word.upper()
            soundex_code = word[0]
            
            mapping = {'BFPV': '1', 'CGJKQSXZ': '2', 'DT': '3', 'L': '4', 'MN': '5', 'R': '6'}
            
            for char in word[1:]:
                for chars, code in mapping.items():
                    if char in chars:
                        if soundex_code[-1] != code:
                            soundex_code += code
                        break
            
            soundex_code = soundex_code.ljust(4, '0')[:4]
            return soundex_code
        
        words1 = re.findall(r'\w+', text1)
        words2 = re.findall(r'\w+', text2)
        
        if not words1 or not words2:
            return 0.0
        
        matches = 0
        for w1 in words1:
            for w2 in words2:
                if soundex(w1) == soundex(w2):
                    matches += 1
                    break
        
        return matches / max(len(words1), len(words2))
    
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
    
    def _graph_similarity(self, tokens1, tokens2):
        if not tokens1 or not tokens2:
            return 0.0
        
        connected_pairs = 0
        total_pairs = 0
        
        for token1 in tokens1:
            for token2 in tokens2:
                total_pairs += 1
                for domain_graph in self.context_graphs.values():
                    if token1 in domain_graph and token2 in domain_graph[token1]:
                        connected_pairs += 1
                        break
        
        return connected_pairs / total_pairs if total_pairs > 0 else 0.0
    
    def _generate_match_evidence(self, comp1, comp2, similarities):
        evidence = []
        
        if similarities['token_overlap'] > 0.3:
            common_tokens = set(comp1['tokens']).intersection(set(comp2['tokens']))
            evidence.append(f"Common semantic tokens: {', '.join(list(common_tokens)[:3])}")
        
        if similarities['pattern_match'] > 0.5:
            common_patterns = set(comp1['patterns']).intersection(set(comp2['patterns']))
            evidence.append(f"Matching patterns: {', '.join(list(common_patterns)[:2])}")
        
        if similarities['domain_alignment'] > 0.4:
            common_domains = set(comp1['domains']).intersection(set(comp2['domains']))
            evidence.append(f"Same security domains: {', '.join(list(common_domains)[:2])}")
        
        if similarities['embedding_cosine'] > 0.6:
            evidence.append("High semantic vector similarity")
        
        if similarities['abbreviation'] > 0.7:
            evidence.append("Abbreviation expansion match")
        
        return evidence
    
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
                    'match_type': 'ultra_semantic' if similarity_data['final_score'] > 0.6 else 'semantic'
                })
        
        return sorted(results, key=lambda x: x['confidence'], reverse=True)

class DataDrivenMetricsRecommender:
    def __init__(self, mapping_results_file: str = "security_mapping_results.json", original_data_file: str = "new.json"):
        self.mapping_results_file = mapping_results_file
        self.original_data_file = original_data_file
        self.mapping_data = None
        self.original_data = None
        self.nlp_matcher = UltraIntelligentNLPMatcher()
        self.load_results()

        # BRILLIANT AO1 VISIBILITY METRICS - Comprehensive Security Intelligence Framework
        self.ao1_visibility_requirements = {
            'Network': {
                'Digital Asset Discovery Coverage': {
                    'synonyms': ['asset', 'device', 'endpoint', 'host', 'server', 'workstation', 'node', 'machine', 'computer', 'system', 'appliance', 'infrastructure', 'cmdb', 'inventory', 'discovery', 'enumeration'],
                    'partial_matches': ['asset', 'device', 'host', 'server', 'endpoint', 'node', 'machine', 'system', 'cmdb', 'inventory', 'discovery'],
                    'description': 'Measure comprehensive asset discovery and inventory coverage across all network segments',
                    'visibility_query': 'What percentage of network-connected assets are discovered, classified, and continuously monitored?',
                    'business_impact': 'Critical for attack surface management and zero-trust architecture',
                    'threat_context': 'Unknown assets = blind spots for lateral movement detection'
                },
                'DNS Intelligence & Domain Reputation': {
                    'synonyms': ['dns', 'domain', 'fqdn', 'hostname', 'url', 'uri', 'web_address', 'site', 'subdomain', 'tld', 'dns_query', 'dns_response', 'nslookup', 'dig', 'resolver'],
                    'partial_matches': ['dns', 'domain', 'host', 'fqdn', 'url', 'web', 'site', 'query', 'lookup', 'resolve'],
                    'description': 'Measure DNS visibility for threat hunting, C2 detection, and domain reputation analysis',
                    'visibility_query': 'What percentage of DNS queries are logged with full request/response context and threat intelligence correlation?',
                    'business_impact': 'Essential for detecting DNS tunneling, C2 communications, and malicious domains',
                    'threat_context': 'DNS is the most common exfiltration and C2 communication vector'
                },
                'Network Segmentation & Zone Intelligence': {
                    'synonyms': ['zone', 'segment', 'vlan', 'subnet', 'network_zone', 'security_zone', 'trust_zone', 'dmz', 'lan', 'wan', 'perimeter', 'boundary', 'enclave', 'microsegment'],
                    'partial_matches': ['zone', 'segment', 'vlan', 'subnet', 'network', 'security', 'trust', 'dmz', 'perimeter', 'boundary'],
                    'description': 'Measure network segmentation visibility and cross-zone traffic analysis for zero-trust validation',
                    'visibility_query': 'What percentage of network traffic is tagged with source/destination security zones and trust levels?',
                    'business_impact': 'Critical for zero-trust implementation and lateral movement prevention',
                    'threat_context': 'Unmonitored cross-zone traffic enables privilege escalation and data exfiltration'
                },
                'Geospatial Threat Intelligence': {
                    'synonyms': ['geo', 'geolocation', 'location', 'country', 'region', 'city', 'coordinates', 'latitude', 'longitude', 'geoip', 'asn', 'isp', 'geographic', 'spatial', 'territorial'],
                    'partial_matches': ['geo', 'location', 'country', 'region', 'city', 'coord', 'lat', 'lon', 'geographic', 'spatial'],
                    'description': 'Measure geographic context enrichment for threat attribution and anomaly detection',
                    'visibility_query': 'What percentage of network connections include high-fidelity geospatial context with threat intelligence overlay?',
                    'business_impact': 'Enables geopolitical risk assessment and compliance monitoring',
                    'threat_context': 'Geographic anomalies often indicate compromised accounts or insider threats'
                },
                'Cloud Network Fabric Visibility': {
                    'synonyms': ['vpc', 'vnet', 'virtual_network', 'cloud_network', 'aws_vpc', 'azure_vnet', 'gcp_vpc', 'subnet', 'security_group', 'nacl', 'route_table', 'internet_gateway', 'nat_gateway'],
                    'partial_matches': ['vpc', 'vnet', 'virtual', 'cloud', 'aws', 'azure', 'gcp', 'security_group', 'route', 'gateway'],
                    'description': 'Measure cloud network architecture visibility and east-west traffic monitoring',
                    'visibility_query': 'What percentage of cloud network traffic includes VPC flow logs with security group and routing context?',
                    'business_impact': 'Essential for cloud security posture management and compliance',
                    'threat_context': 'Cloud misconfigurations are the leading cause of data breaches'
                },
                'Protocol Intelligence & Deep Packet Inspection': {
                    'synonyms': ['protocol', 'dpi', 'deep_packet_inspection', 'application_layer', 'l7', 'payload', 'content', 'signature', 'pattern', 'behavior', 'flow', 'session', 'stream'],
                    'partial_matches': ['protocol', 'dpi', 'packet', 'payload', 'content', 'flow', 'session', 'l7', 'application'],
                    'description': 'Measure deep protocol analysis coverage for advanced threat detection',
                    'visibility_query': 'What percentage of network traffic undergoes deep packet inspection with behavioral analysis?',
                    'business_impact': 'Critical for detecting encrypted threats and zero-day attacks',
                    'threat_context': 'Encrypted malware and living-off-the-land techniques bypass signature-based detection'
                },
                'Bandwidth & Performance Intelligence': {
                    'synonyms': ['bandwidth', 'throughput', 'latency', 'jitter', 'packet_loss', 'performance', 'qos', 'utilization', 'capacity', 'congestion', 'bottleneck', 'saturation'],
                    'partial_matches': ['bandwidth', 'throughput', 'latency', 'performance', 'utilization', 'capacity', 'qos'],
                    'description': 'Measure network performance metrics for capacity planning and DDoS detection',
                    'visibility_query': 'What percentage of network segments have real-time performance monitoring with anomaly detection?',
                    'business_impact': 'Enables proactive capacity management and service level compliance',
                    'threat_context': 'Performance anomalies often indicate DDoS attacks or data exfiltration'
                }
            },
            'Endpoint': {
                'Endpoint Detection & Response Coverage': {
                    'synonyms': ['edr', 'endpoint_detection', 'agent', 'sensor', 'crowdstrike', 'falcon', 'defender', 'sentinelone', 'carbon_black', 'cylance', 'endpoint_protection'],
                    'partial_matches': ['edr', 'agent', 'sensor', 'crowdstrike', 'falcon', 'defender', 'endpoint', 'protection'],
                    'description': 'Measure EDR agent deployment and telemetry coverage across all endpoint types',
                    'visibility_query': 'What percentage of endpoints have active EDR agents with full behavioral monitoring enabled?',
                    'business_impact': 'Critical for ransomware prevention and incident response',
                    'threat_context': 'Unmonitored endpoints are prime targets for initial access and persistence'
                },
                'Process Execution Intelligence': {
                    'synonyms': ['process', 'execution', 'command', 'cmd', 'powershell', 'bash', 'shell', 'script', 'binary', 'executable', 'pid', 'ppid', 'process_tree', 'command_line'],
                    'partial_matches': ['process', 'execution', 'command', 'cmd', 'shell', 'script', 'binary', 'executable'],
                    'description': 'Measure process execution visibility with command-line arguments and parent-child relationships',
                    'visibility_query': 'What percentage of process executions are logged with full command-line context and process ancestry?',
                    'business_impact': 'Essential for detecting living-off-the-land attacks and advanced persistence',
                    'threat_context': 'Fileless attacks rely on legitimate processes for malicious activities'
                },
                'File System Intelligence': {
                    'synonyms': ['file', 'filesystem', 'registry', 'creation', 'modification', 'deletion', 'access', 'hash', 'checksum', 'signature', 'fim', 'file_integrity'],
                    'partial_matches': ['file', 'registry', 'hash', 'checksum', 'signature', 'fim', 'integrity'],
                    'description': 'Measure file system monitoring coverage with hash-based threat intelligence',
                    'visibility_query': 'What percentage of file system changes are monitored with cryptographic hashing and threat intelligence correlation?',
                    'business_impact': 'Critical for malware detection and data loss prevention',
                    'threat_context': 'File system changes are key indicators of malware installation and data theft'
                },
                'Memory & Runtime Intelligence': {
                    'synonyms': ['memory', 'ram', 'heap', 'stack', 'injection', 'dll', 'library', 'module', 'runtime', 'dynamic', 'loaded', 'mapped', 'allocated'],
                    'partial_matches': ['memory', 'ram', 'injection', 'dll', 'library', 'module', 'runtime', 'dynamic'],
                    'description': 'Measure memory analysis and runtime behavior monitoring for advanced threat detection',
                    'visibility_query': 'What percentage of endpoints have memory protection and runtime analysis capabilities?',
                    'business_impact': 'Essential for detecting fileless malware and advanced persistent threats',
                    'threat_context': 'Memory-resident threats bypass traditional file-based detection'
                },
                'Network Connection Intelligence': {
                    'synonyms': ['connection', 'socket', 'port', 'network', 'tcp', 'udp', 'listening', 'established', 'netstat', 'network_connection', 'remote_connection'],
                    'partial_matches': ['connection', 'socket', 'port', 'network', 'tcp', 'udp', 'listening', 'remote'],
                    'description': 'Measure endpoint network connection visibility for C2 and lateral movement detection',
                    'visibility_query': 'What percentage of endpoint network connections are monitored with process correlation?',
                    'business_impact': 'Critical for detecting command & control communications',
                    'threat_context': 'Malicious network connections are primary indicators of compromise'
                },
                'Asset Configuration & Vulnerability Intelligence': {
                    'synonyms': ['vulnerability', 'cve', 'patch', 'update', 'configuration', 'baseline', 'compliance', 'hardening', 'posture', 'assessment', 'scan'],
                    'partial_matches': ['vulnerability', 'cve', 'patch', 'update', 'config', 'baseline', 'compliance', 'scan'],
                    'description': 'Measure endpoint vulnerability and configuration management coverage',
                    'visibility_query': 'What percentage of endpoints have real-time vulnerability assessment and configuration monitoring?',
                    'business_impact': 'Essential for proactive risk management and compliance',
                    'threat_context': 'Unpatched vulnerabilities are the most common initial access vectors'
                }
            },
            'Identity_Authentication': {
                'Identity Lifecycle Intelligence': {
                    'synonyms': ['identity', 'user', 'account', 'principal', 'subject', 'entity', 'lifecycle', 'provisioning', 'deprovisioning', 'creation', 'deletion', 'modification'],
                    'partial_matches': ['identity', 'user', 'account', 'lifecycle', 'provisioning', 'creation', 'deletion'],
                    'description': 'Measure identity lifecycle management and orphaned account detection',
                    'visibility_query': 'What percentage of identity lifecycle events are monitored with automated risk assessment?',
                    'business_impact': 'Critical for insider threat prevention and compliance',
                    'threat_context': 'Orphaned and over-privileged accounts are common attack vectors'
                },
                'Authentication Behavior Intelligence': {
                    'synonyms': ['authentication', 'login', 'logon', 'signin', 'sso', 'mfa', '2fa', 'biometric', 'token', 'credential', 'password', 'kerberos', 'saml', 'oauth'],
                    'partial_matches': ['auth', 'login', 'logon', 'signin', 'sso', 'mfa', 'token', 'credential', 'password'],
                    'description': 'Measure authentication event visibility with behavioral anomaly detection',
                    'visibility_query': 'What percentage of authentication attempts include contextual risk scoring and behavioral analysis?',
                    'business_impact': 'Essential for preventing credential-based attacks',
                    'threat_context': 'Compromised credentials are involved in 80% of data breaches'
                },
                'Privileged Access Intelligence': {
                    'synonyms': ['privilege', 'admin', 'administrator', 'root', 'sudo', 'elevation', 'escalation', 'pam', 'privileged_access', 'service_account', 'system_account'],
                    'partial_matches': ['privilege', 'admin', 'root', 'sudo', 'elevation', 'escalation', 'pam', 'service'],
                    'description': 'Measure privileged access monitoring and just-in-time access controls',
                    'visibility_query': 'What percentage of privileged access events are monitored with session recording and approval workflows?',
                    'business_impact': 'Critical for preventing insider threats and privilege escalation',
                    'threat_context': 'Privileged account abuse is the fastest path to complete system compromise'
                },
                'Access Pattern Intelligence': {
                    'synonyms': ['access', 'permission', 'authorization', 'resource', 'data', 'file', 'folder', 'share', 'database', 'application', 'system', 'entitlement'],
                    'partial_matches': ['access', 'permission', 'authorization', 'resource', 'data', 'entitlement'],
                    'description': 'Measure resource access patterns for anomaly detection and least privilege validation',
                    'visibility_query': 'What percentage of resource access attempts are logged with user/resource context and anomaly scoring?',
                    'business_impact': 'Essential for data loss prevention and zero-trust implementation',
                    'threat_context': 'Abnormal access patterns indicate compromised accounts or insider threats'
                },
                'Federation & Trust Intelligence': {
                    'synonyms': ['federation', 'trust', 'domain', 'forest', 'realm', 'directory', 'ldap', 'ad', 'active_directory', 'azure_ad', 'okta', 'ping'],
                    'partial_matches': ['federation', 'trust', 'domain', 'directory', 'ldap', 'ad', 'azure', 'okta'],
                    'description': 'Measure federated identity and trust relationship monitoring',
                    'visibility_query': 'What percentage of federated authentication events include trust validation and cross-domain risk assessment?',
                    'business_impact': 'Critical for hybrid cloud security and partner access management',
                    'threat_context': 'Federated identity attacks can bypass traditional security controls'
                }
            },
            'Application': {
                'Application Security Intelligence': {
                    'synonyms': ['application', 'app', 'web', 'api', 'service', 'microservice', 'container', 'kubernetes', 'docker', 'runtime', 'rasp', 'waf'],
                    'partial_matches': ['app', 'web', 'api', 'service', 'container', 'kubernetes', 'runtime', 'waf'],
                    'description': 'Measure application security monitoring with runtime protection and API visibility',
                    'visibility_query': 'What percentage of applications have runtime security monitoring with API traffic analysis?',
                    'business_impact': 'Critical for preventing application-layer attacks and data breaches',
                    'threat_context': 'Application vulnerabilities are the most common attack surface'
                },
                'Database Activity Intelligence': {
                    'synonyms': ['database', 'db', 'sql', 'query', 'transaction', 'table', 'schema', 'data', 'record', 'dam', 'database_activity_monitoring'],
                    'partial_matches': ['database', 'db', 'sql', 'query', 'transaction', 'table', 'data', 'dam'],
                    'description': 'Measure database activity monitoring with query analysis and data classification',
                    'visibility_query': 'What percentage of database operations are monitored with query pattern analysis and data sensitivity tagging?',
                    'business_impact': 'Essential for data loss prevention and regulatory compliance',
                    'threat_context': 'Database breaches result in the highest cost per record lost'
                },
                'Cloud Application Intelligence': {
                    'synonyms': ['saas', 'cloud_app', 'office365', 'salesforce', 'workday', 'slack', 'zoom', 'casb', 'cloud_access_security_broker'],
                    'partial_matches': ['saas', 'cloud', 'office365', 'salesforce', 'slack', 'casb'],
                    'description': 'Measure SaaS application visibility and shadow IT discovery',
                    'visibility_query': 'What percentage of SaaS applications are monitored with CASB integration and risk assessment?',
                    'business_impact': 'Critical for cloud security posture and data governance',
                    'threat_context': 'Unmanaged SaaS applications create data leakage and compliance risks'
                },
                'DevOps & CI/CD Intelligence': {
                    'synonyms': ['devops', 'cicd', 'pipeline', 'deployment', 'build', 'artifact', 'repository', 'git', 'jenkins', 'github', 'gitlab', 'container_registry'],
                    'partial_matches': ['devops', 'cicd', 'pipeline', 'deployment', 'build', 'git', 'jenkins', 'container'],
                    'description': 'Measure DevOps pipeline security and supply chain visibility',
                    'visibility_query': 'What percentage of CI/CD pipelines have security scanning and artifact integrity verification?',
                    'business_impact': 'Essential for supply chain security and secure software delivery',
                    'threat_context': 'Supply chain attacks can compromise entire software ecosystems'
                }
            },
            'Cloud': {
                'Multi-Cloud Security Posture Intelligence': {
                    'synonyms': ['cloud', 'aws', 'azure', 'gcp', 'multi_cloud', 'hybrid', 'cspm', 'cloud_security_posture', 'configuration', 'compliance', 'governance'],
                    'partial_matches': ['cloud', 'aws', 'azure', 'gcp', 'multi', 'hybrid', 'cspm', 'posture', 'compliance'],
                    'description': 'Measure cloud security posture across all cloud environments with configuration drift detection',
                    'visibility_query': 'What percentage of cloud resources are monitored for security posture with real-time compliance validation?',
                    'business_impact': 'Critical for cloud governance and regulatory compliance',
                    'threat_context': 'Cloud misconfigurations expose sensitive data to public internet'
                },
                'Container & Kubernetes Intelligence': {
                    'synonyms': ['container', 'docker', 'kubernetes', 'k8s', 'pod', 'namespace', 'cluster', 'orchestration', 'runtime_security', 'image_scanning'],
                    'partial_matches': ['container', 'docker', 'kubernetes', 'k8s', 'pod', 'cluster', 'runtime', 'image'],
                    'description': 'Measure container security with runtime protection and image vulnerability scanning',
                    'visibility_query': 'What percentage of containers have runtime security monitoring with image vulnerability correlation?',
                    'business_impact': 'Essential for cloud-native application security',
                    'threat_context': 'Container escapes can compromise entire Kubernetes clusters'
                },
                'Serverless & Function Intelligence': {
                    'synonyms': ['serverless', 'lambda', 'function', 'azure_functions', 'cloud_functions', 'faas', 'function_as_a_service', 'event_driven'],
                    'partial_matches': ['serverless', 'lambda', 'function', 'faas', 'event'],
                    'description': 'Measure serverless function security and event-driven architecture monitoring',
                    'visibility_query': 'What percentage of serverless functions have security monitoring with execution tracing?',
                    'business_impact': 'Critical for modern application security architecture',
                    'threat_context': 'Serverless functions can be exploited for cryptomining and data exfiltration'
                },
                'Cloud Storage Intelligence': {
                    'synonyms': ['storage', 's3', 'blob', 'bucket', 'object_storage', 'file_storage', 'block_storage', 'data_lake', 'backup', 'archive'],
                    'partial_matches': ['storage', 's3', 'blob', 'bucket', 'object', 'file', 'block', 'data_lake'],
                    'description': 'Measure cloud storage security with access monitoring and data classification',
                    'visibility_query': 'What percentage of cloud storage has access logging with data sensitivity classification?',
                    'business_impact': 'Essential for data protection and privacy compliance',
                    'threat_context': 'Misconfigured cloud storage is the leading cause of data breaches'
                }
            },
            'Data': {
                'Data Discovery & Classification Intelligence': {
                    'synonyms': ['data_discovery', 'classification', 'labeling', 'tagging', 'dlp', 'data_loss_prevention', 'sensitive_data', 'pii', 'phi', 'pci', 'gdpr'],
                    'partial_matches': ['data', 'discovery', 'classification', 'dlp', 'sensitive', 'pii', 'phi', 'gdpr'],
                    'description': 'Measure data discovery and classification coverage across all data stores',
                    'visibility_query': 'What percentage of organizational data is discovered, classified, and continuously monitored for sensitive content?',
                    'business_impact': 'Critical for regulatory compliance and data governance',
                    'threat_context': 'Unclassified sensitive data cannot be properly protected'
                },
                'Data Flow & Lineage Intelligence': {
                    'synonyms': ['data_flow', 'lineage', 'movement', 'transfer', 'migration', 'replication', 'synchronization', 'etl', 'pipeline', 'streaming'],
                    'partial_matches': ['flow', 'lineage', 'movement', 'transfer', 'migration', 'etl', 'pipeline', 'streaming'],
                    'description': 'Measure data flow visibility and lineage tracking for governance and security',
                    'visibility_query': 'What percentage of data movements are tracked with full lineage and impact analysis?',
                    'business_impact': 'Essential for data governance and breach impact assessment',
                    'threat_context': 'Data exfiltration often follows legitimate data flow patterns'
                },
                'Encryption & Key Management Intelligence': {
                    'synonyms': ['encryption', 'decryption', 'key_management', 'kms', 'hsm', 'certificate', 'pki', 'crypto', 'cipher', 'hash', 'signature'],
                    'partial_matches': ['encryption', 'key', 'kms', 'hsm', 'certificate', 'pki', 'crypto', 'cipher'],
                    'description': 'Measure encryption coverage and key management security across all data states',
                    'visibility_query': 'What percentage of sensitive data is encrypted with centralized key management and rotation?',
                    'business_impact': 'Critical for data protection and regulatory compliance',
                    'threat_context': 'Unencrypted data is immediately valuable to attackers'
                }
            },
            'Threat_Intelligence': {
                'Indicator Correlation Intelligence': {
                    'synonyms': ['ioc', 'indicator', 'threat_intelligence', 'ti', 'feed', 'reputation', 'blacklist', 'watchlist', 'signature', 'yara', 'sigma'],
                    'partial_matches': ['ioc', 'indicator', 'threat', 'intelligence', 'feed', 'reputation', 'yara', 'sigma'],
                    'description': 'Measure threat intelligence integration and IOC correlation across all security tools',
                    'visibility_query': 'What percentage of security events are enriched with threat intelligence and IOC correlation?',
                    'business_impact': 'Critical for threat hunting and incident prioritization',
                    'threat_context': 'Contextual threat intelligence reduces false positives and improves response times'
                },
                'Attack Pattern Intelligence': {
                    'synonyms': ['mitre', 'att&ck', 'ttp', 'tactics', 'techniques', 'procedures', 'kill_chain', 'attack_pattern', 'behavior', 'campaign'],
                    'partial_matches': ['mitre', 'attack', 'ttp', 'tactics', 'techniques', 'kill_chain', 'behavior'],
                    'description': 'Measure attack pattern detection and MITRE ATT&CK framework coverage',
                    'visibility_query': 'What percentage of security events are mapped to MITRE ATT&CK techniques with threat actor attribution?',
                    'business_impact': 'Essential for strategic threat assessment and defense planning',
                    'threat_context': 'Understanding adversary TTPs enables proactive defense strategies'
                }
            }
        }

    def load_results(self):
        try:
            with open(self.mapping_results_file, 'r') as f:
                self.mapping_data = json.load(f)
            logger.info(f"Loaded mapping results from {self.mapping_results_file}")
            
            with open(self.original_data_file, 'r') as f:
                self.original_data = json.load(f)
            logger.info(f"Loaded original data from {self.original_data_file}")
            
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            raise

    def get_table_size_info(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        if ('datasets' in self.original_data and 
            dataset_id in self.original_data['datasets'] and
            'tables' in self.original_data['datasets'][dataset_id] and
            table_id in self.original_data['datasets'][dataset_id]['tables']):
            
            table_info = self.original_data['datasets'][dataset_id]['tables'][table_id]
            
            size_info = {
                'row_count': 0,
                'size_bytes': 0,
                'size_category': 'unknown'
            }
            
            if 'table_info' in table_info:
                table_metadata = table_info['table_info']
                
                for field in ['num_rows', 'row_count', 'rows', 'numRows']:
                    if field in table_metadata and table_metadata[field] is not None:
                        try:
                            size_info['row_count'] = int(table_metadata[field])
                            break
                        except (ValueError, TypeError):
                            continue
                
                for field in ['num_bytes', 'size_bytes', 'bytes', 'numBytes']:
                    if field in table_metadata and table_metadata[field] is not None:
                        try:
                            size_info['size_bytes'] = int(table_metadata[field])
                            break
                        except (ValueError, TypeError):
                            continue
            
            if size_info['row_count'] == 0 and 'sample_data' in table_info:
                sample_count = len(table_info['sample_data']) if table_info['sample_data'] else 0
                if sample_count > 0:
                    size_info['row_count'] = sample_count * 1000
            
            if size_info['row_count'] > 100000000:
                size_info['size_category'] = 'ultra_large'
                size_info['priority_score'] = 6
            elif size_info['row_count'] > 10000000:
                size_info['size_category'] = 'very_large'
                size_info['priority_score'] = 5
            elif size_info['row_count'] > 1000000:
                size_info['size_category'] = 'large'
                size_info['priority_score'] = 4
            elif size_info['row_count'] > 100000:
                size_info['size_category'] = 'medium'
                size_info['priority_score'] = 3
            elif size_info['row_count'] > 10000:
                size_info['size_category'] = 'small'
                size_info['priority_score'] = 2
            elif size_info['row_count'] > 0:
                size_info['size_category'] = 'very_small'
                size_info['priority_score'] = 1
            else:
                size_info['size_category'] = 'empty'
                size_info['priority_score'] = 0
            
            return size_info
        
        return {'row_count': 0, 'size_bytes': 0, 'size_category': 'unknown', 'priority_score': 0}

    def get_available_data_sources(self) -> Dict[str, Dict[str, Any]]:
        available_sources = {}
        
        for role, requirements in self.mapping_data['matches']['log_types'].items():
            available_sources[role] = {}
            
            for log_type, matches in requirements.items():
                if matches['table_names']:
                    tables_info = []
                    
                    for table_match in matches['table_names']:
                        table_columns = []
                        for column_match in matches['column_names']:
                            if (column_match['dataset_id'] == table_match['dataset_id'] and 
                                column_match['table_id'] == table_match['table_id']):
                                table_columns.append(column_match['name'])
                        
                        size_info = self.get_table_size_info(table_match['dataset_id'], table_match['table_id'])
                        
                        tables_info.append({
                            'table_name': table_match['name'],
                            'dataset': table_match['dataset_id'],
                            'columns': table_columns,
                            'row_count': size_info['row_count'],
                            'size_bytes': size_info['size_bytes'],
                            'size_category': size_info['size_category'],
                            'size_priority_score': size_info['priority_score']
                        })
                    
                    tables_info.sort(key=lambda x: x['size_priority_score'], reverse=True)
                    
                    available_sources[role][log_type] = {
                        'tables': tables_info,
                        'total_columns': len(matches['column_names'])
                    }
        
        return available_sources

    def map_metrics_to_data(self) -> Dict[str, List[Dict[str, Any]]]:
        available_sources = self.get_available_data_sources()
        ao1_visibility_recommendations = {}
        
        for role, log_types in available_sources.items():
            ao1_visibility_recommendations[role] = []
            
            # Map to AO1 visibility requirements instead of generic metrics
            if role in self.ao1_visibility_requirements:
                ao1_requirements = self.ao1_visibility_requirements[role]
                
                for log_type, data_info in log_types.items():
                    for table_info in data_info['tables']:
                        table_columns = [col.lower() for col in table_info['columns']]
                        
                        # Test each AO1 visibility requirement
                        for visibility_factor, factor_info in ao1_requirements.items():
                            
                            # Find columns that match AO1 visibility synonyms and partial matches
                            visibility_matches = []
                            
                            # Check synonyms
                            for synonym in factor_info['synonyms']:
                                synonym_results = self.nlp_matcher.ultra_intelligent_match(synonym, table_columns, threshold=0.2)
                                for result in synonym_results:
                                    visibility_matches.append({
                                        'matched_column': result['candidate'],
                                        'ao1_requirement': visibility_factor,
                                        'match_term': synonym,
                                        'match_type': 'synonym',
                                        'confidence': result['confidence'],
                                        'evidence': result['evidence']
                                    })
                            
                            # Check partial matches
                            for partial in factor_info['partial_matches']:
                                for column in table_columns:
                                    if partial.lower() in column.lower():
                                        visibility_matches.append({
                                            'matched_column': column,
                                            'ao1_requirement': visibility_factor,
                                            'match_term': partial,
                                            'match_type': 'partial',
                                            'confidence': 0.8,  # High confidence for partial matches
                                            'evidence': ['partial_word_match']
                                        })
                            
                            if visibility_matches:
                                # Calculate AO1 visibility feasibility score
                                avg_confidence = sum(match['confidence'] for match in visibility_matches) / len(visibility_matches)
                                
                                # Boost for table size (bigger tables = better visibility measurement)
                                size_multiplier = 1 + (table_info['size_priority_score'] * 0.15)
                                
                                # Boost for multiple matching columns (better coverage)
                                coverage_multiplier = 1 + (len(visibility_matches) * 0.1)
                                
                                final_feasibility = min(avg_confidence * size_multiplier * coverage_multiplier, 1.0)
                                
                                # Calculate intelligence score based on match quality
                                intelligence_score = self._calculate_intelligence_score(visibility_matches, table_info)
                                
                                ao1_visibility_recommendations[role].append({
                                    'ao1_visibility_factor': visibility_factor,
                                    'log_type': log_type,
                                    'table_name': table_info['table_name'],
                                    'dataset': table_info['dataset'],
                                    'row_count': table_info['row_count'],
                                    'size_category': table_info['size_category'],
                                    'size_priority_score': table_info['size_priority_score'],
                                    'feasibility_score': final_feasibility,
                                    'intelligence_score': intelligence_score,  # ADD THIS LINE
                                    'description': factor_info['description'],
                                    'visibility_query': factor_info['visibility_query'],
                                    'matched_columns': visibility_matches,
                                    'column_count': len(visibility_matches),
                                    'implementation_difficulty': 'AO1_Trivial' if final_feasibility > 0.8 else 'AO1_Easy' if final_feasibility > 0.6 else 'AO1_Medium'
                                })
        
        return ao1_visibility_recommendations

    def _calculate_intelligence_score(self, visibility_matches, table_info):
        """Calculate an intelligence score based on match quality and table characteristics"""
        if not visibility_matches:
            return 0.0
        
        # Base score from match confidences
        avg_confidence = sum(match['confidence'] for match in visibility_matches) / len(visibility_matches)
        
        # Bonus for ultra_semantic matches
        ultra_semantic_count = sum(1 for match in visibility_matches if match['match_type'] == 'ultra_semantic')
        semantic_bonus = ultra_semantic_count * 0.2
        
        # Bonus for table size (larger tables = more intelligence value)
        size_bonus = min(table_info['size_priority_score'] * 0.1, 0.3)
        
        # Bonus for multiple matches (better coverage)
        coverage_bonus = min(len(visibility_matches) * 0.05, 0.2)
        
        final_score = min(avg_confidence + semantic_bonus + size_bonus + coverage_bonus, 1.0)
        return round(final_score, 3)

    def prioritize_recommendations(self, recommendations: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        all_recommendations = []
        
        for role, role_recommendations in recommendations.items():
            for rec in role_recommendations:
                rec['role'] = role
                all_recommendations.append(rec)
        
        return sorted(all_recommendations, 
                     key=lambda x: (-x['feasibility_score'], 
                                   -x['size_priority_score'],
                                   -x.get('intelligence_score', 0),  # Use .get() for safety
                                   x['implementation_difficulty']))

    def generate_implementation_guide(self, recommendations: List[Dict[str, Any]]) -> str:
        guide = []
        guide.append("=" * 90)
        guide.append("AO1 VISIBILITY METRICS IMPLEMENTATION GUIDE")
        guide.append("=" * 90)
        guide.append("")
        
        guide.append("AI ANALYSIS SUMMARY:")
        guide.append("-" * 50)
        
        trivial_count = len([r for r in recommendations if r['implementation_difficulty'] == 'AO1_Trivial'])
        easy_count = len([r for r in recommendations if r['implementation_difficulty'] == 'AO1_Easy'])
        medium_count = len([r for r in recommendations if r['implementation_difficulty'] == 'AO1_Medium'])
        
        ultra_semantic_count = len([r for r in recommendations if any(m['match_type'] == 'ultra_semantic' for m in r['matched_columns'])])
        
        guide.append(f"Total AO1 Visibility Metrics Discovered: {len(recommendations)}")
        guide.append(f"Ultra-Semantic AI Matches: {ultra_semantic_count}")
        guide.append(f"Trivial Implementation: {trivial_count}")
        guide.append(f"Easy Implementation: {easy_count}")
        guide.append(f"Medium Complexity: {medium_count}")
        guide.append("")
        
        avg_intelligence = sum(r.get('intelligence_score', 0) for r in recommendations) / len(recommendations) if recommendations else 0
        guide.append(f"Average AI Intelligence Score: {avg_intelligence:.1f}")
        guide.append("")
        
        for difficulty in ['AO1_Trivial', 'AO1_Easy', 'AO1_Medium']:
            difficulty_recs = [r for r in recommendations if r['implementation_difficulty'] == difficulty]
            if difficulty_recs:
                display_name = difficulty.replace('AO1_', '').upper()
                guide.append(f"{display_name} IMPLEMENTATION METRICS:")
                guide.append("-" * 60)
                
                for i, rec in enumerate(difficulty_recs[:8], 1):
                    guide.append(f"{i}. {rec['ao1_visibility_factor']} ({rec['role']} - {rec['log_type']})")
                    guide.append(f"   Data Source: {rec['dataset']}.{rec['table_name']}")
                    guide.append(f"   Table Size: {rec['row_count']:,} rows ({rec['size_category']})")
                    guide.append(f"   Description: {rec['description']}")
                    guide.append(f"   Visibility Query: {rec['visibility_query']}")
                    guide.append(f"   AI Confidence: {rec['feasibility_score']:.3f} (Intelligence: {rec.get('intelligence_score', 0)})")
                    
                    if rec['matched_columns']:
                        guide.append("   🎯 Matched Columns:")
                        for col_match in rec['matched_columns'][:3]:  # Show top 3 matches
                            if col_match['match_type'] == 'ultra_semantic':
                                indicator = "🧠🚀"
                            elif col_match['match_type'] == 'synonym':
                                indicator = "🎯"
                            else:
                                indicator = "📝"
                            
                            confidence_pct = int(col_match['confidence'] * 100)
                            evidence_str = ', '.join(col_match['evidence'][:2]) if col_match['evidence'] else 'direct_match'
                            guide.append(f"     {indicator} {col_match['matched_column']} ← {col_match['match_term']} ({confidence_pct}% | {evidence_str})")
                    
                    guide.append("")
                
                if len(difficulty_recs) > 8:
                    guide.append(f"   ... and {len(difficulty_recs) - 8} more {display_name.lower()} metrics available")
                    guide.append("")
        
        return "\n".join(guide)

    def generate_quick_start_recommendations(self) -> str:
        recommendations = self.map_metrics_to_data()
        prioritized = self.prioritize_recommendations(recommendations)
        
        quick_start = []
        quick_start.append("🚀 AO1 VISIBILITY QUICK START RECOMMENDATIONS")
        quick_start.append("=" * 90)
        quick_start.append("")
        
        trivial_wins = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Trivial'][:3]
        easy_wins = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Easy'][:5]
        
        if trivial_wins:
            quick_start.append("🎯 INSTANT IMPLEMENTATION - TRIVIAL DIFFICULTY:")
            quick_start.append("-" * 50)
            
            for i, rec in enumerate(trivial_wins, 1):
                quick_start.append(f"{i}. 🚀 IMPLEMENT: {rec['ao1_visibility_factor']}")
                quick_start.append(f"   📊 USE TABLE: {rec['dataset']}.{rec['table_name']} ({rec['row_count']:,} rows - {rec['size_category']})")
                quick_start.append(f"   📈 MEASURE: {rec['description']}")
                quick_start.append(f"   💡 VISIBILITY QUERY: {rec['visibility_query']}")
                quick_start.append(f"   🤖 AI CONFIDENCE: {rec['feasibility_score']:.3f} (Intelligence Score: {rec.get('intelligence_score', 0)})")
                
                if rec['matched_columns']:
                    quick_start.append("   🔑 KEY COLUMNS TO USE:")
                    for col_match in rec['matched_columns'][:3]:  # Show top 3 matches
                        match_type_desc = {
                            'ultra_semantic': 'Ultra-AI semantic match',
                            'synonym': 'Synonym match', 
                            'partial': 'Partial match'
                        }.get(col_match['match_type'], 'Unknown match')
                        
                        confidence_pct = int(col_match['confidence'] * 100)
                        evidence_summary = ', '.join(col_match['evidence'][:2]) if col_match['evidence'] else 'exact_match'
                        quick_start.append(f"     • Use '{col_match['matched_column']}' for {col_match['ao1_requirement']} ({match_type_desc}, {confidence_pct}% confidence)")
                        quick_start.append(f"       Evidence: {evidence_summary}")
                
                quick_start.append("")
        
        if easy_wins:
            quick_start.append("⚡ EASY WINS - HIGH IMPACT, LOW EFFORT:")
            quick_start.append("-" * 50)
            
            for i, rec in enumerate(easy_wins, 1):
                quick_start.append(f"{i}. ⚡ IMPLEMENT: {rec['ao1_visibility_factor']}")
                quick_start.append(f"   📊 USE TABLE: {rec['dataset']}.{rec['table_name']} ({rec['row_count']:,} rows - {rec['size_category']})")
                quick_start.append(f"   📈 MEASURE: {rec['description']}")
                quick_start.append(f"   💡 VISIBILITY QUERY: {rec['visibility_query']}")
                quick_start.append(f"   🤖 AI CONFIDENCE: {rec['feasibility_score']:.3f} (Intelligence Score: {rec.get('intelligence_score', 0)})")
                
                ultra_matches = [m for m in rec['matched_columns'] if m['match_type'] == 'ultra_semantic']
                if ultra_matches:
                    quick_start.append(f"   🧠🚀 ULTRA-SEMANTIC MATCHES: {len(ultra_matches)} detected")
                
                quick_start.append("")
        
        if not trivial_wins and not easy_wins:
            quick_start.append("⚠️  NO TRIVIAL OR EASY IMPLEMENTATIONS FOUND")
            quick_start.append("Consider data enrichment or additional log source integration.")
            quick_start.append("")
            
            medium_recs = [r for r in prioritized if r['implementation_difficulty'] == 'AO1_Medium'][:3]
            if medium_recs:
                quick_start.append("🔧 BEST MEDIUM-COMPLEXITY OPTIONS:")
                for i, rec in enumerate(medium_recs, 1):
                    quick_start.append(f"{i}. {rec['ao1_visibility_factor']} (Confidence: {rec['feasibility_score']:.3f})")
        
        return "\n".join(quick_start)

    def save_recommendations(self, output_file: str = "ao1_visibility_metrics_recommendations.json"):
        recommendations = self.map_metrics_to_data()
        prioritized = self.prioritize_recommendations(recommendations)
        
        output_data = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'ai_analysis_summary': {
                'total_metrics_available': len(prioritized),
                'ultra_semantic_matches': len([r for r in prioritized if any(m['match_type'] == 'ultra_semantic' for m in r['matched_columns'])]),
                'trivial_implementation': len([r for r in prioritized if r['implementation_difficulty'] == 'AO1_Trivial']),
                'easy_implementation': len([r for r in prioritized if r['implementation_difficulty'] == 'AO1_Easy']),
                'medium_implementation': len([r for r in prioritized if r['implementation_difficulty'] == 'AO1_Medium']),
                'average_intelligence_score': sum(r.get('intelligence_score', 0) for r in prioritized) / len(prioritized) if prioritized else 0
            },
            'recommendations_by_role': recommendations,
            'prioritized_recommendations': prioritized,
            'nlp_engine_stats': {
                'cache_size': len(self.nlp_matcher.similarity_cache),
                'security_taxonomy_domains': len(self.nlp_matcher.security_taxonomy),
                'semantic_embeddings': len(self.nlp_matcher.semantic_embeddings),
                'abbreviation_mappings': len(self.nlp_matcher.abbreviation_engine)
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"AO1 visibility recommendations saved to {output_file}")

if __name__ == "__main__":
    analyzer = DataDrivenMetricsRecommender()
    
    quick_start = analyzer.generate_quick_start_recommendations()
    print(quick_start)
    print("\n" + "="*90 + "\n")
    
    recommendations = analyzer.map_metrics_to_data()
    prioritized = analyzer.prioritize_recommendations(recommendations)
    full_guide = analyzer.generate_implementation_guide(prioritized)
    print(full_guide)
    
    analyzer.save_recommendations()