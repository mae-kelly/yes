#!/usr/bin/env python3

import re
import hashlib
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime
import statistics
import json
import logging

logger = logging.getLogger(__name__)

class DeepPatternRecognizer:
    def __init__(self):
        self.learned_patterns = defaultdict(list)
        self.pattern_success_rates = defaultdict(lambda: {'hits': 0, 'total': 0})
        self.contextual_patterns = defaultdict(dict)
        self.temporal_patterns = defaultdict(list)
        self.similarity_cache = {}
        
    def learn_pattern(self, pattern_type: str, pattern_data: Dict[str, Any], success: bool):
        pattern_signature = self._generate_pattern_signature(pattern_data)
        
        self.learned_patterns[pattern_type].append({
            'signature': pattern_signature,
            'data': pattern_data,
            'timestamp': datetime.now(),
            'success': success
        })
        
        self.pattern_success_rates[pattern_signature]['total'] += 1
        if success:
            self.pattern_success_rates[pattern_signature]['hits'] += 1
    
    def _generate_pattern_signature(self, pattern_data: Dict[str, Any]) -> str:
        normalized_data = {}
        for key, value in pattern_data.items():
            if isinstance(value, str):
                normalized_data[key] = re.sub(r'[0-9]+', 'N', value.lower())
            else:
                normalized_data[key] = str(value)
        
        signature_string = json.dumps(normalized_data, sort_keys=True)
        return hashlib.md5(signature_string.encode()).hexdigest()[:12]
    
    def recognize_pattern(self, pattern_type: str, candidate_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        candidate_signature = self._generate_pattern_signature(candidate_data)
        
        if candidate_signature in self.pattern_success_rates:
            rates = self.pattern_success_rates[candidate_signature]
            confidence = rates['hits'] / max(rates['total'], 1)
            return confidence, {'known_pattern': True, 'signature': candidate_signature}
        
        best_match_confidence = 0.0
        best_match_info = {}
        
        for pattern in self.learned_patterns[pattern_type]:
            similarity = self._calculate_pattern_similarity(candidate_data, pattern['data'])
            
            if similarity > best_match_confidence and similarity > 0.7:
                best_match_confidence = similarity
                best_match_info = {
                    'similar_pattern': True,
                    'similarity': similarity,
                    'reference_pattern': pattern['signature']
                }
        
        return best_match_confidence, best_match_info
    
    def _calculate_pattern_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        cache_key = f"{id(data1)}:{id(data2)}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        common_keys = set(data1.keys()) & set(data2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            val1, val2 = str(data1[key]), str(data2[key])
            
            if val1 == val2:
                similarities.append(1.0)
            else:
                char_similarity = self._string_similarity(val1, val2)
                similarities.append(char_similarity)
        
        result = statistics.mean(similarities) if similarities else 0.0
        self.similarity_cache[cache_key] = result
        return result
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        if not s1 or not s2:
            return 0.0
        
        s1_norm = re.sub(r'[0-9]+', 'N', s1.lower())
        s2_norm = re.sub(r'[0-9]+', 'N', s2.lower())
        
        if s1_norm == s2_norm:
            return 1.0
        
        common_chars = sum(1 for c in s1_norm if c in s2_norm)
        max_length = max(len(s1_norm), len(s2_norm))
        
        return common_chars / max_length if max_length > 0 else 0.0