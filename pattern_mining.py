import re
import logging
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Set
import itertools

logger = logging.getLogger(__name__)

class PatternMiningEngine:
    def __init__(self):
        self.min_frequency = 2
        self.max_gap_size = 10000
        logger.info("Pattern Mining Engine initialized with PrefixSpan, SPADE, SPIRIT algorithms")
        
    def discover_basic_patterns(self, hostnames: List[str]) -> List[Dict]:
        logger.info(f"Starting basic pattern discovery on {len(hostnames)} hostnames")
        pattern_groups = defaultdict(list)
        
        for hostname in hostnames:
            hostname_lower = hostname.lower().strip()
            if re.search(r'\d', hostname_lower):
                template = re.sub(r'\d+', 'XXX', hostname_lower)
                numbers = [int(m.group()) for m in re.finditer(r'\d+', hostname_lower)]
                pattern_groups[template].append({
                    'hostname': hostname_lower,
                    'numbers': numbers
                })
        
        patterns = []
        for template, hosts in pattern_groups.items():
            if len(hosts) >= self.min_frequency:
                patterns.append(self._analyze_pattern(template, hosts))
        
        logger.info(f"Discovered {len(patterns)} basic sequential patterns")
        return patterns
    
    def mine_advanced_patterns(self, hostnames: List[str]) -> Dict:
        results = {
            'prefixspan': self._prefixspan_mining(hostnames),
            'spade': self._spade_mining(hostnames),
            'spirit': self._spirit_mining(hostnames)
        }
        
        total = sum(len(v) for v in results.values())
        logger.info(f"Advanced pattern mining discovered {total} patterns total")
        return results
    
    def _prefixspan_mining(self, hostnames: List[str]) -> List[Dict]:
        logger.info("Running PrefixSpan algorithm for sequential pattern mining")
        sequences = []
        
        for hostname in hostnames:
            tokens = re.split(r'[-._]', hostname.lower())
            sequences.append(tokens)
        
        frequent_sequences = self._find_frequent_sequences(sequences)
        patterns = []
        
        for seq, support in frequent_sequences.items():
            if support >= self.min_frequency:
                patterns.append({
                    'type': 'prefixspan',
                    'sequence': seq,
                    'support': support,
                    'confidence': support / len(hostnames)
                })
        
        logger.info(f"PrefixSpan discovered {len(patterns)} sequential patterns")
        return patterns
    
    def _spade_mining(self, hostnames: List[str]) -> List[Dict]:
        logger.info("Running SPADE algorithm for vertical pattern mining")
        vertical_db = defaultdict(list)
        
        for idx, hostname in enumerate(hostnames):
            tokens = re.split(r'[-._]', hostname.lower())
            for pos, token in enumerate(tokens):
                vertical_db[token].append((idx, pos))
        
        patterns = []
        for token, occurrences in vertical_db.items():
            if len(occurrences) >= self.min_frequency:
                patterns.append({
                    'type': 'spade',
                    'token': token,
                    'support': len(occurrences),
                    'positions': occurrences[:10]
                })
        
        for token1, occ1 in vertical_db.items():
            for token2, occ2 in vertical_db.items():
                if token1 < token2:
                    co_occurrences = self._find_co_occurrences(occ1, occ2)
                    if len(co_occurrences) >= self.min_frequency:
                        patterns.append({
                            'type': 'spade_pair',
                            'tokens': (token1, token2),
                            'support': len(co_occurrences)
                        })
        
        logger.info(f"SPADE discovered {len(patterns)} vertical patterns")
        return patterns
    
    def _spirit_mining(self, hostnames: List[str]) -> List[Dict]:
        logger.info("Running SPIRIT algorithm with regex constraints")
        
        regex_patterns = [
            (r'^([a-z]+)-([a-z]+)-(\d+)\.', 'type-env-number'),
            (r'^([a-z]+)(\d+)([a-z]+)(\d+)', 'prefix-num-middle-num'),
            (r'^([a-z]{2,4})([a-z]{3})(\d{2,4})', 'region-type-number'),
            (r'^(\w+)\.(\w+)\.(\d+)', 'word.word.number'),
            (r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})', 'ip-like'),
            (r'^([a-z]+)-(\d{4})-([a-z]+)', 'type-year-suffix'),
            (r'^([a-z]{3})(\d{2})([a-z]{2})(\d{3})', 'complex-pattern')
        ]
        
        patterns = []
        for regex, description in regex_patterns:
            matching_hosts = []
            for hostname in hostnames:
                if re.match(regex, hostname.lower()):
                    matching_hosts.append(hostname)
            
            if len(matching_hosts) >= self.min_frequency:
                patterns.append({
                    'type': 'spirit',
                    'regex': regex,
                    'description': description,
                    'support': len(matching_hosts),
                    'samples': matching_hosts[:5]
                })
        
        logger.info(f"SPIRIT discovered {len(patterns)} regex-constrained patterns")
        return patterns
    
    def generate_sequential_candidates(self, patterns: List[Dict], existing: Set[str]) -> List[Dict]:
        logger.info("Generating sequential pattern candidates")
        candidates = []
        
        for pattern in patterns:
            if 'template' in pattern and 'missing_numbers' in pattern:
                template = pattern['template']
                for pos, missing_nums in pattern['missing_numbers'].items():
                    for num in missing_nums[:100]:
                        candidate = template.replace('XXX', str(num), 1)
                        if candidate not in existing:
                            candidates.append({
                                'hostname': candidate,
                                'source': 'sequential',
                                'pattern': template
                            })
        
        logger.info(f"Generated {len(candidates)} sequential candidates")
        return candidates
    
    def generate_ngram_candidates(self, existing: Set[str]) -> List[Dict]:
        logger.info("Generating n-gram based candidates")
        all_ngrams = Counter()
        n = 3
        
        for hostname in existing:
            if len(hostname) >= n:
                for i in range(len(hostname) - n + 1):
                    all_ngrams[hostname[i:i+n]] += 1
        
        candidates = []
        common_ngrams = [ng for ng, count in all_ngrams.most_common(100) if count >= 5]
        
        for ng1 in common_ngrams[:20]:
            for ng2 in common_ngrams[:20]:
                candidate = ng1 + ng2
                if candidate not in existing and len(candidates) < 1000:
                    candidates.append({
                        'hostname': candidate,
                        'source': 'ngram',
                        'ngrams': [ng1, ng2]
                    })
        
        logger.info(f"Generated {len(candidates)} n-gram candidates")
        return candidates
    
    def generate_markov_candidates(self, existing: Set[str]) -> List[Dict]:
        logger.info("Generating Markov chain based candidates (RFfiller algorithm)")
        transitions = defaultdict(Counter)
        
        for hostname in existing:
            hostname = hostname.lower()
            for i in range(len(hostname) - 1):
                current = hostname[i]
                next_char = hostname[i + 1]
                transitions[current][next_char] += 1
        
        candidates = []
        for start_char in 'abcdefghijklmnopqrstuvwxyz0123456789':
            if start_char in transitions:
                candidate = start_char
                for _ in range(10):
                    if candidate[-1] in transitions:
                        next_chars = transitions[candidate[-1]]
                        if next_chars:
                            next_char = max(next_chars, key=next_chars.get)
                            candidate += next_char
                
                if candidate not in existing and len(candidate) > 3:
                    candidates.append({
                        'hostname': candidate,
                        'source': 'markov',
                        'chain_length': len(candidate)
                    })
        
        logger.info(f"Generated {len(candidates)} Markov chain candidates")
        return candidates[:500]
    
    def _analyze_pattern(self, template: str, hosts: List[Dict]) -> Dict:
        number_sequences = defaultdict(list)
        
        for host_data in hosts:
            for i, num in enumerate(host_data['numbers']):
                number_sequences[i].append(num)
        
        pattern_info = {
            'template': template,
            'host_count': len(hosts),
            'sample_hosts': [h['hostname'] for h in hosts[:5]],
            'missing_numbers': {}
        }
        
        for pos, nums in number_sequences.items():
            unique_nums = sorted(set(nums))
            if len(unique_nums) > 1:
                min_val, max_val = min(unique_nums), max(unique_nums)
                missing = []
                
                for i in range(min_val, min(max_val + 1, min_val + self.max_gap_size)):
                    if i not in unique_nums:
                        missing.append(i)
                
                if missing:
                    pattern_info['missing_numbers'][pos] = missing
                    density = len(unique_nums) / (max_val - min_val + 1) if max_val > min_val else 1.0
                    pattern_info[f'density_pos_{pos}'] = density
        
        return pattern_info
    
    def _find_frequent_sequences(self, sequences: List[List[str]]) -> Dict:
        pattern_counts = Counter()
        
        for seq in sequences:
            for length in range(1, min(len(seq) + 1, 5)):
                for i in range(len(seq) - length + 1):
                    pattern = tuple(seq[i:i+length])
                    pattern_counts[pattern] += 1
        
        return dict(pattern_counts)
    
    def _find_co_occurrences(self, occ1: List, occ2: List) -> List:
        co_occurrences = []
        
        for idx1, pos1 in occ1:
            for idx2, pos2 in occ2:
                if idx1 == idx2 and abs(pos1 - pos2) == 1:
                    co_occurrences.append((idx1, pos1, pos2))
        
        return co_occurrences