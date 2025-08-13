# ai/neural.py

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import statistics
import hashlib
import re
from datetime import datetime

class FieldClassifier(nn.Module):
    def __init__(self, input_dim=512, hidden_dim=256, num_classes=25):
        super().__init__()
        self.encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=input_dim, nhead=8, batch_first=True),
            num_layers=3
        )
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, num_classes),
            nn.Softmax(dim=1)
        )
        self.field_types = [
            'hostname', 'ip_address', 'fqdn', 'mac_address', 'infrastructure_type',
            'system_classification', 'global_region', 'country', 'datacenter',
            'cloud_region', 'business_unit', 'cio', 'app_class', 'edr_coverage',
            'dlp_coverage', 'tanium_coverage', 'network_log_types', 'endpoint_log_types',
            'cloud_log_types', 'app_log_types', 'identity_log_types', 'network_zones',
            'geolocation', 'vpc', 'controls'
        ]
    
    def forward(self, x):
        encoded = self.encoder(x)
        return self.classifier(encoded.mean(dim=1))

class SemanticEmbedder:
    def __init__(self):
        self.cache = {}
        self.concept_vectors = self._init_concepts()
        self.pattern_cache = {}
    
    def _init_concepts(self):
        return {
            'hostname': np.array([1.0, 0.9, 0.7, 0.5, 0.3, 0.2, 0.4, 0.6]),
            'network': np.array([0.3, 1.0, 0.8, 0.4, 0.2, 0.5, 0.7, 0.4]),
            'security': np.array([0.2, 0.4, 1.0, 0.8, 0.6, 0.3, 0.5, 0.7]),
            'business': np.array([0.1, 0.2, 0.3, 1.0, 0.9, 0.7, 0.4, 0.3]),
            'infrastructure': np.array([0.5, 0.6, 0.4, 0.3, 1.0, 0.8, 0.2, 0.5]),
            'location': np.array([0.2, 0.3, 0.2, 0.4, 0.3, 1.0, 0.9, 0.2]),
            'application': np.array([0.4, 0.3, 0.5, 0.6, 0.4, 0.2, 1.0, 0.8]),
            'identity': np.array([0.3, 0.2, 0.7, 0.5, 0.2, 0.3, 0.6, 1.0])
        }
    
    def embed_text(self, text: str, context: str = "") -> np.ndarray:
        cache_key = hashlib.md5(f"{text}:{context}".encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        vector = np.zeros(8)
        text_lower = text.lower()
        
        feature_groups = {
            0: ['host', 'server', 'endpoint', 'device', 'machine', 'computer'],
            1: ['ip', 'address', 'network', 'subnet', 'dns', 'domain'],
            2: ['security', 'auth', 'firewall', 'vpn', 'ssl', 'tls'],
            3: ['business', 'customer', 'product', 'sales', 'revenue', 'org'],
            4: ['infrastructure', 'cloud', 'datacenter', 'platform', 'service'],
            5: ['location', 'region', 'country', 'geo', 'area', 'zone'],
            6: ['application', 'app', 'software', 'program', 'system'],
            7: ['identity', 'user', 'account', 'login', 'credential']
        }
        
        for i, features in feature_groups.items():
            score = sum(1 for feature in features if feature in text_lower)
            vector[i] = score / len(features)
        
        if context:
            context_boost = self._analyze_context(context.lower())
            vector = vector * (1 + context_boost * 0.3)
        
        # Safe normalization
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        else:
            # Return a small random vector if all zeros
            vector = np.random.random(8) * 0.01
            vector = vector / np.linalg.norm(vector)
        
        self.cache[cache_key] = vector
        return vector
    
    def _analyze_context(self, context: str) -> float:
        context_indicators = {
            'technical': ['table', 'database', 'schema', 'column', 'data'],
            'network': ['network', 'topology', 'infrastructure', 'connectivity'],
            'security': ['security', 'monitoring', 'protection', 'compliance'],
            'business': ['business', 'organization', 'enterprise', 'company']
        }
        
        scores = []
        for category, keywords in context_indicators.items():
            score = sum(1 for keyword in keywords if keyword in context)
            scores.append(score / len(keywords))
        
        return max(scores) if scores else 0.0
    
    def semantic_similarity(self, text1: str, text2: str, context: str = "") -> float:
        vec1 = self.embed_text(text1, context)
        vec2 = self.embed_text(text2, context)
        
        # Calculate norms
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        # Handle zero vectors to avoid division by zero
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        
        # Calculate similarity safely
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        
        # Ensure result is valid and in range [0, 1]
        if np.isnan(similarity) or np.isinf(similarity):
            return 0.0
        
        return max(0.0, min(1.0, similarity))

class PatternRecognizer:
    def __init__(self):
        self.learned_patterns = defaultdict(list)
        self.success_rates = defaultdict(lambda: {'hits': 0, 'total': 0})
        self.pattern_weights = defaultdict(float)
        self.temporal_patterns = defaultdict(list)
    
    def learn_pattern(self, pattern_type: str, pattern_data: Dict[str, Any], success: bool):
        signature = self._generate_signature(pattern_data)
        
        self.learned_patterns[pattern_type].append({
            'signature': signature,
            'data': pattern_data,
            'timestamp': datetime.now(),
            'success': success
        })
        
        self.success_rates[signature]['total'] += 1
        if success:
            self.success_rates[signature]['hits'] += 1
    
    def _generate_signature(self, data: Dict[str, Any]) -> str:
        normalized = {}
        for key, value in data.items():
            if isinstance(value, str):
                normalized[key] = re.sub(r'[0-9]+', 'N', value.lower())
            else:
                normalized[key] = str(value)
        
        import json
        signature_string = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(signature_string.encode()).hexdigest()[:12]
    
    def recognize_pattern(self, pattern_type: str, candidate: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        signature = self._generate_signature(candidate)
        
        if signature in self.success_rates:
            rates = self.success_rates[signature]
            confidence = rates['hits'] / max(rates['total'], 1)
            return confidence, {'known_pattern': True, 'signature': signature}
        
        best_confidence = 0.0
        best_info = {}
        
        for pattern in self.learned_patterns[pattern_type]:
            similarity = self._calculate_similarity(candidate, pattern['data'])
            
            if similarity > best_confidence and similarity > 0.7:
                best_confidence = similarity
                best_info = {
                    'similar_pattern': True,
                    'similarity': similarity,
                    'reference': pattern['signature']
                }
        
        return best_confidence, best_info
    
    def _calculate_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        common_keys = set(data1.keys()) & set(data2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            val1, val2 = str(data1[key]), str(data2[key])
            
            if val1 == val2:
                similarities.append(1.0)
            else:
                char_sim = self._string_similarity(val1, val2)
                similarities.append(char_sim)
        
        return statistics.mean(similarities) if similarities else 0.0
    
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