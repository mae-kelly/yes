#!/usr/bin/env python3

import re
import hashlib
import numpy as np
from typing import Dict, Any

class AdvancedSemanticMatcher:
    def __init__(self):
        self.embedding_cache = {}
        self.concept_embeddings = self._initialize_embeddings()
        self.context_vectors = {}
        
    def _initialize_embeddings(self) -> Dict[str, np.ndarray]:
        return {
            'hostname': np.array([1.0, 0.9, 0.7, 0.4, 0.2, 0.1, 0.3, 0.5]),
            'ip_address': np.array([0.3, 1.0, 0.8, 0.2, 0.1, 0.4, 0.6, 0.3]),
            'infrastructure': np.array([0.5, 0.4, 1.0, 0.8, 0.6, 0.3, 0.7, 0.2]),
            'business': np.array([0.2, 0.1, 0.3, 1.0, 0.9, 0.7, 0.4, 0.6]),
            'security': np.array([0.4, 0.3, 0.6, 0.5, 1.0, 0.8, 0.2, 0.7]),
            'location': np.array([0.1, 0.2, 0.4, 0.6, 0.3, 1.0, 0.9, 0.5]),
            'network': np.array([0.7, 0.8, 0.5, 0.2, 0.4, 0.3, 1.0, 0.6]),
            'classification': np.array([0.6, 0.4, 0.8, 0.7, 0.5, 0.4, 0.3, 1.0])
        }
    
    def calculate_semantic_similarity(self, text1: str, text2: str, context: str = "") -> float:
        cache_key = f"{text1}:{text2}:{context}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        vec1 = self._text_to_vector(text1, context)
        vec2 = self._text_to_vector(text2, context)
        
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        similarity = max(0.0, min(1.0, similarity))
        
        self.embedding_cache[cache_key] = similarity
        return similarity
    
    def _text_to_vector(self, text: str, context: str = "") -> np.ndarray:
        base_vector = np.zeros(8)
        text_lower = text.lower()
        
        concept_weights = {
            'hostname': ['host', 'endpoint', 'computer', 'device', 'server', 'machine'],
            'ip_address': ['ip', 'address', 'addr', 'inet'],
            'infrastructure': ['cloud', 'onprem', 'saas', 'api', 'platform'],
            'business': ['unit', 'org', 'department', 'business', 'company'],
            'security': ['security', 'auth', 'firewall', 'vpn', 'edr'],
            'location': ['region', 'country', 'location', 'geo', 'datacenter'],
            'network': ['network', 'subnet', 'vlan', 'dns', 'domain'],
            'classification': ['type', 'class', 'category', 'system', 'os']
        }
        
        for i, (concept, keywords) in enumerate(concept_weights.items()):
            weight = sum(1 for keyword in keywords if keyword in text_lower)
            if weight > 0:
                base_vector[i] = weight / len(keywords)
        
        if context:
            context_boost = self._get_context_boost(text_lower, context.lower())
            base_vector = base_vector * (1 + context_boost * 0.2)
        
        return base_vector / (np.linalg.norm(base_vector) + 1e-8)
    
    def _get_context_boost(self, text: str, context: str) -> float:
        context_mappings = {
            'cmdb': ['asset', 'inventory', 'management'],
            'security': ['protection', 'monitoring', 'threat'],
            'network': ['connectivity', 'infrastructure', 'topology'],
            'business': ['organization', 'operational', 'enterprise']
        }
        
        boost = 0.0
        for context_type, keywords in context_mappings.items():
            if any(keyword in context for keyword in keywords):
                if any(keyword in text for keyword in keywords):
                    boost += 0.3
        
        return min(1.0, boost)