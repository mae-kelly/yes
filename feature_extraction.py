"""
Feature extraction module for comprehensive asset analysis
Implements hostname features, n-gram models, and contextual feature engineering
"""

import numpy as np
import pandas as pd
import re
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from config import FEATURE_CONFIG, PATTERN_CONFIG

class ComprehensiveFeatureExtractor:
    """
    Advanced feature extraction for IT asset discovery
    Implements multiple feature engineering techniques
    """
    
    def __init__(self):
        self.feature_dim = FEATURE_CONFIG['total_features']
        self.ngram_vectorizers = {}
        self.markov_models = {}
        self.feature_cache = {}
        self.initialize_extractors()
    
    def initialize_extractors(self):
        """Initialize n-gram and other extractors"""
        for n in PATTERN_CONFIG['ngram_sizes']:
            self.ngram_vectorizers[n] = TfidfVectorizer(
                analyzer='char',
                ngram_range=(n, n),
                max_features=20
            )
    
    def extract_hostname_features(self, hostname: str) -> np.ndarray:
        """
        Extract comprehensive features from hostname
        Returns 100-dimensional feature vector
        """
        if not hostname:
            return np.zeros(100)
        
        # Check cache
        cache_key = hashlib.md5(hostname.encode()).hexdigest()
        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]
        
        hostname_lower = hostname.lower().strip()
        features = []
        
        # 1. Basic string metrics (15 features)
        features.extend([
            len(hostname),
            hostname.count('.'),
            hostname.count('-'),
            hostname.count('_'),
            len(re.findall(r'\d', hostname)),
            len(re.findall(r'[a-z]', hostname)),
            len(re.findall(r'[A-Z]', hostname)),
            1 if hostname[0].isdigit() else 0,
            1 if hostname[-1].isdigit() else 0,
            len(hostname.split('.')),
            len(hostname.split('-')),
            len(hostname.split('_')),
            self._calculate_entropy(hostname),
            len(set(hostname)),  # Unique characters
            self._longest_common_substring_length(hostname)
        ])
        
        # 2. Pattern indicators (20 features)
        pattern_features = [
            1 if re.match(r'^[a-z]{2,4}\d{2,4}', hostname_lower) else 0,
            1 if re.search(r'\d{2,4}$', hostname_lower) else 0,
            1 if re.search(r'^\d', hostname_lower) else 0,
            1 if re.match(r'^[a-z]+-[a-z]+-\d+', hostname_lower) else 0,
            1 if re.match(r'^[a-z]+\d+[a-z]+\d+', hostname_lower) else 0,
            1 if bool(re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', hostname)) else 0,  # IP pattern
            1 if bool(re.search(r'[0-9a-f]{12}', hostname_lower)) else 0,  # MAC pattern
            1 if bool(re.search(r'v\d+', hostname_lower)) else 0,  # Version pattern
            1 if bool(re.search(r'\d{4}-\d{2}-\d{2}', hostname)) else 0,  # Date pattern
            self._count_consecutive_digits(hostname),
            self._count_consecutive_letters(hostname),
            self._max_digit_sequence_length(hostname),
            self._count_camel_case_words(hostname),
            1 if self._is_sequential_pattern(hostname) else 0,
            1 if self._has_padding_zeros(hostname) else 0,
            self._get_numbering_style(hostname),  # 0=none, 1=single, 2=multiple
            1 if bool(re.search(r'[a-z]{3}\d{3}', hostname_lower)) else 0,
            1 if bool(re.search(r'rack\d+', hostname_lower)) else 0,
            1 if bool(re.search(r'blade\d+', hostname_lower)) else 0,
            1 if bool(re.search(r'node\d+', hostname_lower)) else 0
        ]
        features.extend(pattern_features)
        
        # 3. Infrastructure keywords (50 features)
        keywords = [
            # Network devices
            ['fw', 'firewall', 'asa', 'palo', 'fortinet'],
            ['lb', 'loadbalancer', 'f5', 'haproxy', 'nginx'],
            ['sw', 'switch', 'nexus', 'catalyst'],
            ['rt', 'router', 'rtr', 'bgp'],
            ['vpn', 'ipsec', 'openvpn', 'wireguard'],
            
            # Security devices
            ['ids', 'ips', 'snort', 'suricata'],
            ['waf', 'modsec', 'cloudflare'],
            ['proxy', 'squid', 'px', 'prx'],
            ['siem', 'splunk', 'qradar', 'arcsight'],
            ['edr', 'crowdstrike', 'sentinel', 'defender'],
            
            # Servers by function
            ['web', 'www', 'http', 'apache', 'iis'],
            ['app', 'application', 'tomcat', 'jboss', 'websphere'],
            ['db', 'database', 'sql', 'mysql', 'postgres', 'oracle', 'mongo'],
            ['cache', 'redis', 'memcache', 'varnish', 'hazelcast'],
            ['queue', 'mq', 'rabbit', 'kafka', 'sqs', 'amqp'],
            
            # Infrastructure services
            ['dns', 'bind', 'named', 'ns'],
            ['dhcp', 'bootp'],
            ['ntp', 'time', 'chrony'],
            ['ldap', 'ad', 'dc', 'activedirectory', 'domain'],
            ['mail', 'smtp', 'imap', 'pop3', 'exchange', 'postfix'],
            
            # Storage and backup
            ['san', 'storage', 'nas', 'nfs', 'iscsi'],
            ['backup', 'bkp', 'bak', 'veeam', 'netbackup'],
            ['archive', 'arc', 'retention'],
            
            # Monitoring and logging
            ['monitor', 'mon', 'nagios', 'zabbix', 'prometheus'],
            ['log', 'syslog', 'rsyslog', 'elk', 'elastic'],
            ['metric', 'grafana', 'influx'],
            
            # Development and CI/CD
            ['jenkins', 'ci', 'cd', 'build', 'compile'],
            ['git', 'svn', 'repo', 'repository', 'bitbucket'],
            ['test', 'testing', 'tst', 'qa'],
            ['dev', 'development', 'develop'],
            ['stage', 'staging', 'stg', 'preprod'],
            
            # Environments
            ['prod', 'production', 'prd', 'live'],
            ['uat', 'acceptance'],
            ['demo', 'poc', 'pilot'],
            ['dr', 'disaster', 'recovery'],
            ['lab', 'experiment'],
            
            # Geographic indicators
            ['us', 'usa', 'america', 'united'],
            ['eu', 'europe', 'emea'],
            ['uk', 'london', 'britain'],
            ['apac', 'asia', 'pacific', 'singapore'],
            ['china', 'cn', 'beijing', 'shanghai'],
            
            # Cloud and virtualization
            ['aws', 'ec2', 'lambda', 's3', 'rds'],
            ['azure', 'az', 'microsoft'],
            ['gcp', 'google', 'gke', 'bigquery'],
            ['cloud', 'saas', 'paas', 'iaas'],
            ['vm', 'virtual', 'virt', 'vmware', 'hyperv'],
            ['docker', 'container', 'k8s', 'kubernetes', 'pod'],
            
            # Data center indicators
            ['dc1', 'dc2', 'datacenter', 'colo'],
            ['rack', 'cabinet', 'cage'],
            ['blade', 'chassis'],
            ['core', 'edge', 'dmz', 'perimeter']
        ]
        
        for keyword_group in keywords:
            features.append(1 if any(kw in hostname_lower for kw in keyword_group) else 0)
        
        # 4. N-gram features (10 features)
        ngram_features = self._extract_ngram_features(hostname_lower)
        features.extend(ngram_features[:10])
        
        # 5. Statistical features (5 features)
        features.extend([
            self._calculate_vowel_consonant_ratio(hostname),
            self._calculate_digit_letter_ratio(hostname),
            self._calculate_special_char_ratio(hostname),
            self._calculate_uppercase_ratio(hostname),
            self._calculate_repetition_score(hostname)
        ])
        
        # Ensure exactly 100 features
        features = features[:100]
        while len(features) < 100:
            features.append(0)
        
        feature_array = np.array(features, dtype=np.float32)
        
        # Cache the result
        self.feature_cache[cache_key] = feature_array
        
        return feature_array
    
    def extract_context_features(self, row: pd.Series) -> np.ndarray:
        """
        Extract contextual features from CMDB record
        Returns 25-dimensional feature vector
        """
        features = []
        
        # Business and organizational features
        features.append(1 if pd.notna(row.get('business_unit')) else 0)
        features.append(1 if pd.notna(row.get('region')) else 0)
        features.append(1 if pd.notna(row.get('country')) else 0)
        features.append(1 if pd.notna(row.get('data_center')) else 0)
        features.append(1 if pd.notna(row.get('cloud_region')) else 0)
        
        # System classification features
        sys_class = str(row.get('system_classification', '')).lower()
        features.append(1 if 'server' in sys_class else 0)
        features.append(1 if 'windows' in sys_class else 0)
        features.append(1 if 'linux' in sys_class else 0)
        features.append(1 if 'network' in sys_class else 0)
        features.append(1 if 'security' in sys_class else 0)
        
        # Infrastructure type features
        infra_type = str(row.get('infrastructure_type', '')).lower()
        features.append(1 if 'cloud' in infra_type else 0)
        features.append(1 if 'physical' in infra_type else 0)
        features.append(1 if 'virtual' in infra_type else 0)
        features.append(1 if 'container' in infra_type else 0)
        
        # Quality and source features
        features.append(float(row.get('data_quality_score', 0)))
        features.append(int(row.get('source_count', 0)))
        
        # Management features
        features.append(1 if pd.notna(row.get('cio')) else 0)
        features.append(1 if pd.notna(row.get('apm')) else 0)
        
        # Coverage features
        features.append(1 if row.get('logging_in_splunk') == 'yes' else 0)
        features.append(1 if row.get('logging_in_gso') == 'yes' else 0)
        features.append(1 if row.get('present_in_cmdb') == 'yes' else 0)
        features.append(1 if pd.notna(row.get('edr_coverage')) and row.get('edr_coverage') != 'none' else 0)
        features.append(1 if row.get('tanium_coverage') == 'yes' else 0)
        features.append(1 if row.get('dlp_agent_coverage') == 'yes' else 0)
        
        # Criticality indicator (derived)
        criticality = 0
        if pd.notna(row.get('business_unit')):
            bu = str(row.get('business_unit')).lower()
            if any(critical in bu for critical in ['finance', 'security', 'core', 'infrastructure']):
                criticality = 1
        features.append(criticality)
        
        # Ensure exactly 25 features
        features = features[:25]
        while len(features) < 25:
            features.append(0)
        
        return np.array(features, dtype=np.float32)
    
    def extract_temporal_features(self, row: pd.Series) -> np.ndarray:
        """
        Extract temporal features from timestamps
        Returns 10-dimensional feature vector
        """
        features = []
        
        try:
            # Parse timestamps
            first_seen = pd.to_datetime(row.get('first_seen'))
            last_updated = pd.to_datetime(row.get('last_updated'))
            current_time = pd.Timestamp.now()
            
            if pd.notna(first_seen):
                # Age features
                age_days = (current_time - first_seen).days
                features.append(min(age_days / 365, 10))  # Years, capped at 10
                features.append(1 if age_days < 30 else 0)  # New asset
                features.append(1 if age_days > 365 else 0)  # Old asset
            else:
                features.extend([0, 0, 0])
            
            if pd.notna(last_updated):
                # Update recency
                update_days = (current_time - last_updated).days
                features.append(min(update_days / 365, 10))  # Years since update
                features.append(1 if update_days < 7 else 0)  # Recently updated
                features.append(1 if update_days > 90 else 0)  # Stale
            else:
                features.extend([0, 0, 0])
            
            if pd.notna(first_seen) and pd.notna(last_updated):
                # Update frequency
                lifespan_days = max((last_updated - first_seen).days, 1)
                update_frequency = row.get('source_count', 1) / lifespan_days
                features.append(min(update_frequency * 100, 1))  # Normalized frequency
                
                # Consistency
                features.append(1 if update_days < 30 else 0)  # Actively maintained
            else:
                features.extend([0, 0])
            
            # Day of week and month indicators
            if pd.notna(first_seen):
                features.append(first_seen.dayofweek / 6)  # Normalized day of week
                features.append(first_seen.month / 12)  # Normalized month
            else:
                features.extend([0, 0])
                
        except Exception:
            features = [0] * 10
        
        # Ensure exactly 10 features
        features = features[:10]
        while len(features) < 10:
            features.append(0)
        
        return np.array(features, dtype=np.float32)
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0
        prob = [float(text.count(c)) / len(text) for c in set(text)]
        return -sum(p * np.log2(p) for p in prob if p > 0)
    
    def _longest_common_substring_length(self, text: str) -> int:
        """Find length of longest repeating substring"""
        if len(text) < 2:
            return 0
        
        n = len(text)
        dp = [[0] * n for _ in range(n)]
        max_len = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                if text[i] == text[j]:
                    if i == 0:
                        dp[i][j] = 1
                    else:
                        dp[i][j] = dp[i-1][j-1] + 1
                    max_len = max(max_len, dp[i][j])
        
        return max_len
    
    def _count_consecutive_digits(self, text: str) -> int:
        """Count maximum consecutive digits"""
        if not text:
            return 0
        max_count = 0
        current = 0
        for char in text:
            if char.isdigit():
                current += 1
                max_count = max(max_count, current)
            else:
                current = 0
        return max_count
    
    def _count_consecutive_letters(self, text: str) -> int:
        """Count maximum consecutive letters"""
        if not text:
            return 0
        max_count = 0
        current = 0
        for char in text:
            if char.isalpha():
                current += 1
                max_count = max(max_count, current)
            else:
                current = 0
        return max_count
    
    def _max_digit_sequence_length(self, text: str) -> int:
        """Find maximum digit sequence length"""
        sequences = re.findall(r'\d+', text)
        return max(len(seq) for seq in sequences) if sequences else 0
    
    def _count_camel_case_words(self, text: str) -> int:
        """Count camel case words"""
        return len(re.findall(r'[A-Z][a-z]+', text))
    
    def _is_sequential_pattern(self, text: str) -> bool:
        """Check if hostname follows sequential pattern"""
        numbers = re.findall(r'\d+', text)
        if len(numbers) < 2:
            return False
        
        try:
            nums = [int(n) for n in numbers]
            diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
            return all(d == diffs[0] for d in diffs)
        except:
            return False
    
    def _has_padding_zeros(self, text: str) -> bool:
        """Check if numbers have padding zeros"""
        numbers = re.findall(r'\d+', text)
        return any(num.startswith('0') and len(num) > 1 for num in numbers)
    
    def _get_numbering_style(self, text: str) -> int:
        """Get numbering style: 0=none, 1=single, 2=multiple"""
        numbers = re.findall(r'\d+', text)
        if not numbers:
            return 0
        elif len(numbers) == 1:
            return 1
        else:
            return 2
    
    def _extract_ngram_features(self, text: str) -> List[float]:
        """Extract n-gram based features"""
        features = []
        
        for n in PATTERN_CONFIG['ngram_sizes']:
            if n <= len(text):
                ngrams = [text[i:i+n] for i in range(len(text) - n + 1)]
                unique_ratio = len(set(ngrams)) / len(ngrams) if ngrams else 0
                features.append(unique_ratio)
                
                # Most common n-gram frequency
                if ngrams:
                    counter = Counter(ngrams)
                    most_common_freq = counter.most_common(1)[0][1] / len(ngrams)
                    features.append(most_common_freq)
                else:
                    features.append(0)
            else:
                features.extend([0, 0])
        
        # Pad to expected size
        while len(features) < 10:
            features.append(0)
        
        return features
    
    def _calculate_vowel_consonant_ratio(self, text: str) -> float:
        """Calculate vowel to consonant ratio"""
        vowels = sum(1 for c in text.lower() if c in 'aeiou')
        consonants = sum(1 for c in text.lower() if c.isalpha() and c not in 'aeiou')
        return vowels / (consonants + 1)
    
    def _calculate_digit_letter_ratio(self, text: str) -> float:
        """Calculate digit to letter ratio"""
        digits = sum(1 for c in text if c.isdigit())
        letters = sum(1 for c in text if c.isalpha())
        return digits / (letters + 1)
    
    def _calculate_special_char_ratio(self, text: str) -> float:
        """Calculate special character ratio"""
        special = sum(1 for c in text if not c.isalnum())
        return special / (len(text) + 1)
    
    def _calculate_uppercase_ratio(self, text: str) -> float:
        """Calculate uppercase letter ratio"""
        uppercase = sum(1 for c in text if c.isupper())
        letters = sum(1 for c in text if c.isalpha())
        return uppercase / (letters + 1)
    
    def _calculate_repetition_score(self, text: str) -> float:
        """Calculate character repetition score"""
        if len(text) < 2:
            return 0
        
        repetitions = 0
        for i in range(1, len(text)):
            if text[i] == text[i-1]:
                repetitions += 1
        
        return repetitions / (len(text) - 1)
    
    def combine_features(self, hostname_features: np.ndarray, 
                         context_features: np.ndarray,
                         temporal_features: np.ndarray = None,
                         graph_features: np.ndarray = None) -> np.ndarray:
        """
        Combine all feature types into single vector
        """
        combined = [hostname_features, context_features]
        
        if temporal_features is not None:
            combined.append(temporal_features)
        else:
            combined.append(np.zeros(10))
        
        if graph_features is not None:
            combined.append(graph_features)
        else:
            combined.append(np.zeros(20))
        
        return np.concatenate(combined)


class MarkovChainAnalyzer:
    """
    Markov chain based sequence analysis for hostname patterns
    Implements the RFfiller algorithm concepts
    """
    
    def __init__(self, order: int = 2):
        self.order = order
        self.transition_matrix = defaultdict(lambda: defaultdict(int))
        self.initial_states = defaultdict(int)
        
    def train(self, sequences: List[str]):
        """Train Markov chain on hostname sequences"""
        for seq in sequences:
            # Process each sequence
            tokens = self._tokenize(seq)
            
            if len(tokens) > self.order:
                # Initial state
                initial = tuple(tokens[:self.order])
                self.initial_states[initial] += 1
                
                # Transitions
                for i in range(len(tokens) - self.order):
                    current_state = tuple(tokens[i:i+self.order])
                    next_token = tokens[i+self.order]
                    self.transition_matrix[current_state][next_token] += 1
    
    def predict_next(self, sequence: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Predict next token in sequence"""
        tokens = self._tokenize(sequence)
        
        if len(tokens) < self.order:
            return []
        
        current_state = tuple(tokens[-self.order:])
        
        if current_state not in self.transition_matrix:
            return []
        
        # Get transition probabilities
        transitions = self.transition_matrix[current_state]
        total = sum(transitions.values())
        
        if total == 0:
            return []
        
        # Calculate probabilities
        probs = [(token, count/total) for token, count in transitions.items()]
        probs.sort(key=lambda x: x[1], reverse=True)
        
        return probs[:top_k]
    
    def calculate_sequence_probability(self, sequence: str) -> float:
        """Calculate probability of entire sequence"""
        tokens = self._tokenize(sequence)
        
        if len(tokens) <= self.order:
            return 0.0
        
        # Initial probability
        initial = tuple(tokens[:self.order])
        if initial not in self.initial_states:
            return 0.0
        
        total_initial = sum(self.initial_states.values())
        prob = self.initial_states[initial] / total_initial
        
        # Transition probabilities
        for i in range(len(tokens) - self.order):
            current_state = tuple(tokens[i:i+self.order])
            next_token = tokens[i+self.order]
            
            if current_state not in self.transition_matrix:
                return 0.0
            
            transitions = self.transition_matrix[current_state]
            if next_token not in transitions:
                return 0.0
            
            total = sum(transitions.values())
            prob *= transitions[next_token] / total
        
        return prob
    
    def find_anomalies(self, sequences: List[str], threshold: float = 0.01) -> List[str]:
        """Find anomalous sequences based on probability"""
        anomalies = []
        
        for seq in sequences:
            prob = self.calculate_sequence_probability(seq)
            if prob < threshold:
                anomalies.append(seq)
        
        return anomalies
    
    def _tokenize(self, sequence: str) -> List[str]:
        """Tokenize hostname into components"""
        # Split on delimiters but keep them
        tokens = re.split(r'([.-_])', sequence)
        # Also split numbers and letters
        result = []
        for token in tokens:
            if token:
                # Further split alphanumeric
                subtokens = re.findall(r'[a-zA-Z]+|\d+|[^a-zA-Z\d]', token)
                result.extend(subtokens)
        return result