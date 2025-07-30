#!/usr/bin/env python3
"""
AO1 Field Analyzer
=================
Smart field analysis with business context and ML scoring.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from ao1_keywords import get_all_keywords, find_keyword_requirement, AO1_REQUIREMENTS
from ao1_config_and_logging import logger, AO1_REQUIREMENTS_META

@dataclass
class FieldAnalysis:
    """Field analysis result."""
    field_name: str
    table_name: str
    dataset_name: str
    row_count: int
    match_type: str
    confidence: float
    matching_keywords: List[str]
    matching_requirements: List[str]
    semantic_similarity: float
    business_context: str
    recommendation: str
    strategic_priority: int

class BusinessContextAnalyzer:
    """Analyzes business context of tables."""
    
    def __init__(self):
        self.context_patterns = {
            'cmdb': {
                'patterns': ['cmdb', 'configuration', 'asset', 'inventory'],
                'relevance': 'Critical for asset management',
                'score': 10
            },
            'security': {
                'patterns': ['security', 'edr', 'endpoint', 'agent'],
                'relevance': 'Essential for security posture',
                'score': 9
            },
            'logging': {
                'patterns': ['log', 'event', 'siem', 'splunk', 'chronicle'],
                'relevance': 'Required for compliance',
                'score': 9
            },
            'infrastructure': {
                'patterns': ['infra', 'server', 'vm', 'cloud', 'compute'],
                'relevance': 'Important for infrastructure visibility',
                'score': 7
            },
            'network': {
                'patterns': ['network', 'dns', 'domain', 'fqdn'],
                'relevance': 'Valuable for network tracking',
                'score': 6
            },
            'application': {
                'patterns': ['app', 'application', 'service', 'platform'],
                'relevance': 'Useful for application mapping',
                'score': 5
            }
        }
    
    def analyze(self, table_name: str, dataset_name: str) -> Dict:
        """Analyze table business context."""
        full_name = f"{dataset_name}.{table_name}".lower()
        
        best_match = None
        best_score = 0
        
        for context_type, config in self.context_patterns.items():
            score = sum(1 for pattern in config['patterns'] if pattern in full_name)
            if score > best_score:
                best_score = score
                best_match = context_type
        
        if best_match:
            config = self.context_patterns[best_match]
            return {
                'context': best_match,
                'relevance': config['relevance'],
                'score': config['score'],
                'confidence': min(1.0, best_score / len(config['patterns']))
            }
        
        return {
            'context': 'general',
            'relevance': 'Standard business data',
            'score': 1,
            'confidence': 0.0
        }

class AO1FieldAnalyzer:
    """Advanced AO1 field analyzer."""
    
    def __init__(self, ml_system):
        self.ml_system = ml_system
        self.business_analyzer = BusinessContextAnalyzer()
        self.all_keywords = get_all_keywords()
        
    def analyze_field(self, field_name: str, table_name: str, 
                     dataset_name: str, row_count: int) -> Optional[FieldAnalysis]:
        """Analyze field for AO1 relevance."""
        if not field_name:
            return None
            
        field_lower = field_name.lower().strip()
        
        # Business context
        table_context = self.business_analyzer.analyze(table_name, dataset_name)
        
        # Exact matches
        exact_matches = []
        matching_requirements = []
        
        if field_lower in self.all_keywords:
            exact_matches.append(field_lower)
            matching_requirements.extend(find_keyword_requirement(field_lower))
        
        # Partial matches
        partial_matches = []
        for keyword in self.all_keywords:
            if keyword != field_lower and (keyword in field_lower or field_lower in keyword):
                partial_matches.append(keyword)
                matching_requirements.extend(find_keyword_requirement(keyword))
        
        matching_requirements = list(set(matching_requirements))
        
        # Semantic similarity
        max_similarity = 0.0
        if matching_requirements:
            for req in matching_requirements:
                req_id = req.split(':')[0]
                if req_id in AO1_REQUIREMENTS:
                    keywords = AO1_REQUIREMENTS[req_id]['keywords']
                    similarity = self.ml_system.compute_similarity(field_name, keywords)
                    max_similarity = max(max_similarity, similarity)
        
        # Determine match type and confidence
        if exact_matches:
            match_type = 'EXACT'
            confidence = 100.0
        elif partial_matches and max_similarity > 0.7:
            match_type = 'ML_IDENTIFIED'
            confidence = min(90.0, max_similarity * 100)
        elif partial_matches:
            match_type = 'PARTIAL'
            confidence = min(80.0, len(partial_matches) * 25)
        elif max_similarity > 0.5:
            match_type = 'SUSPECTED'
            confidence = max_similarity * 100
        else:
            return None
        
        # Context boost
        context_boost = table_context['score'] * 2
        confidence = min(100.0, confidence + context_boost)
        
        # Strategic priority
        priority = self._calculate_priority(
            match_type, confidence, row_count, table_context
        )
        
        # Business context
        business_context = self._generate_context(
            field_name, table_name, dataset_name, matching_requirements, table_context
        )
        
        # Recommendation
        recommendation = self._generate_recommendation(
            match_type, confidence, row_count, table_context
        )
        
        return FieldAnalysis(
            field_name=field_name,
            table_name=table_name,
            dataset_name=dataset_name,
            row_count=row_count,
            match_type=match_type,
            confidence=confidence,
            matching_keywords=exact_matches + partial_matches,
            matching_requirements=matching_requirements,
            semantic_similarity=max_similarity,
            business_context=business_context,
            recommendation=recommendation,
            strategic_priority=priority
        )
    
    def _calculate_priority(self, match_type: str, confidence: float, 
                          row_count: int, table_context: Dict) -> int:
        """Calculate strategic priority score."""
        priority = 0
        
        # Match type scoring
        match_scores = {'EXACT': 100, 'ML_IDENTIFIED': 80, 'PARTIAL': 60, 'SUSPECTED': 40}
        priority += match_scores.get(match_type, 0)
        
        # Data volume scoring
        if row_count > 10000000:
            priority += 50
        elif row_count > 1000000:
            priority += 30
        elif row_count > 100000:
            priority += 15
        
        # Confidence scoring
        priority += int(confidence * 0.5)
        
        # Context scoring
        priority += table_context['score'] * 5
        
        return priority
    
    def _generate_context(self, field_name: str, table_name: str, dataset_name: str,
                         requirements: List[str], table_context: Dict) -> str:
        """Generate business context description."""
        context = f"Field '{field_name}' in {dataset_name}.{table_name} "
        context += f"is part of a {table_context['context']} system. "
        context += f"Business relevance: {table_context['relevance']}."
        
        if requirements:
            req_names = [req.split(': ')[1] for req in requirements if ': ' in req]
            if req_names:
                context += f" Supports AO1 requirements: {', '.join(req_names)}."
        
        return context
    
    def _generate_recommendation(self, match_type: str, confidence: float,
                               row_count: int, table_context: Dict) -> str:
        """Generate implementation recommendation."""
        if match_type == 'EXACT' and confidence >= 95:
            rec = "HIGHLY RECOMMENDED - Perfect AO1 match"
        elif match_type == 'EXACT':
            rec = "RECOMMENDED - Direct keyword match"
        elif match_type == 'ML_IDENTIFIED' and confidence >= 85:
            rec = "RECOMMENDED - High ML confidence"
        elif match_type == 'PARTIAL' and confidence >= 75:
            rec = "CONSIDER - Good partial match"
        else:
            rec = "INVESTIGATE - Potential relevance"
        
        # Data volume context
        if row_count > 1000000:
            rec += " - High data volume"
        elif row_count > 100000:
            rec += " - Good data volume"
        else:
            rec += " - Limited data volume"
        
        # Business priority
        if table_context['score'] >= 8:
            rec += " - HIGH BUSINESS PRIORITY"
        
        return rec

def get_field_analyzer(ml_system):
    """Get configured field analyzer."""
    return AO1FieldAnalyzer(ml_system)