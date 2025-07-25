import json
import pandas as pd
import statistics
import logging
from collections import Counter
from datetime import datetime
from typing import Dict, List, Any
from nlp_matcher import UltraIntelligentNLPMatcher
from ao1_requirements import AO1_VISIBILITY_REQUIREMENTS
from data_analyzer import DataAnalyzer

logger = logging.getLogger(__name__)

class MetricsRecommender:
    def __init__(self, mapping_file: str = "security_mapping_results.json", data_file: str = "new.json"):
        self.mapping_file = mapping_file
        self.data_file = data_file
        self.nlp_matcher = UltraIntelligentNLPMatcher()
        self.data_analyzer = DataAnalyzer()
        self.ao1_requirements = AO1_VISIBILITY_REQUIREMENTS
        self.recommendation_stats = {'total': 0, 'high_confidence': 0, 'ultra_semantic': 0, 'ml_enhanced': 0}
        self.priority_matrix = {'CRITICAL': 1.0, 'HIGH': 0.8, 'MEDIUM': 0.6, 'LOW': 0.4}
        self.complexity_factors = {'LOW': 1.0, 'MEDIUM': 0.85, 'HIGH': 0.7, 'VERY_HIGH': 0.5}
        self.load_data()

    def load_data(self):
        with open(self.mapping_file, 'r') as f:
            self.mapping_data = json.load(f)
        with open(self.data_file, 'r') as f:
            self.original_data = json.load(f)

    def map_metrics_to_data(self) -> Dict[str, List[Dict[str, Any]]]:
        available_sources = self.data_analyzer.get_available_data_sources(
            self.mapping_data, self.original_data
        )
        recommendations = {}
        
        for role, log_types in available_sources.items():
            recommendations[role] = []
            
            if role in self.ao1_requirements:
                ao1_reqs = self.ao1_requirements[role]
                
                for log_type, data_info in log_types.items():
                    for table_info in data_info['tables']:
                        table_columns = [col.lower() for col in table_info['columns']]
                        
                        for vis_factor, factor_info in ao1_reqs.items():
                            matches = self._find_column_matches(
                                factor_info, table_columns, vis_factor
                            )
                            
                            if matches:
                                rec = self._create_recommendation(
                                    vis_factor, factor_info, matches, table_info, log_type, role
                                )
                                recommendations[role].append(rec)
        
        return recommendations

    def _find_column_matches(self, factor_info, table_columns, vis_factor):
        matches = []
        
        for synonym in factor_info['synonyms']:
            results = self.nlp_matcher.ultra_intelligent_match(
                synonym, table_columns, threshold=0.15
            )
            for result in results:
                matches.append({
                    'matched_column': result['candidate'],
                    'ao1_requirement': vis_factor,
                    'match_term': synonym,
                    'match_type': result['match_type'],
                    'confidence': result['confidence'],
                    'evidence': result['evidence'],
                    'ml_confidence': result.get('ml_confidence', 0.0)
                })
        
        for partial in factor_info['partial_matches']:
            for column in table_columns:
                if partial.lower() in column.lower():
                    quality = len(partial) / len(column)
                    confidence = 0.7 + (quality * 0.2)
                    matches.append({
                        'matched_column': column,
                        'ao1_requirement': vis_factor,
                        'match_term': partial,
                        'match_type': 'partial',
                        'confidence': confidence,
                        'evidence': ['partial_word_match'],
                        'ml_confidence': quality
                    })
        
        return matches

    def _create_recommendation(self, vis_factor, factor_info, matches, table_info, log_type, role):
        feasibility = self._calculate_feasibility(matches, table_info, factor_info)
        intelligence = self._calculate_intelligence(matches, table_info, factor_info)
        
        return {
            'ao1_visibility_factor': vis_factor,
            'log_type': log_type,
            'role': role,
            'table_name': table_info['table_name'],
            'dataset': table_info['dataset'],
            'row_count': table_info['row_count'],
            'size_category': table_info['size_category'],
            'size_priority_score': table_info['size_priority_score'],
            'feasibility_score': feasibility['final_score'],
            'intelligence_score': intelligence,
            'confidence_score': feasibility['confidence'],
            'description': factor_info['description'],
            'visibility_query': factor_info['visibility_query'],
            'business_impact': factor_info['business_impact'],
            'threat_context': factor_info['threat_context'],
            'priority': factor_info.get('priority', 'MEDIUM'),
            'complexity': factor_info.get('complexity', 'MEDIUM'),
            'matched_columns': matches,
            'implementation_difficulty': self._determine_difficulty(
                feasibility['final_score'], intelligence, factor_info
            ),
            'recommendation_rank': self._calculate_rank(
                feasibility, intelligence, table_info, factor_info
            )
        }

    def _calculate_feasibility(self, matches, table_info, factor_info):
        components = {
            'base_confidence': statistics.mean([m['confidence'] for m in matches]) if matches else 0,
            'size_factor': min(table_info['size_priority_score'] / 10, 1.0),
            'coverage_factor': min(len(matches) / 5, 1.0),
            'ml_factor': statistics.mean([m.get('ml_confidence', 0) for m in matches]) if matches else 0,
            'priority_factor': self.priority_matrix.get(factor_info.get('priority', 'MEDIUM'), 0.6)
        }
        
        complexity = factor_info.get('complexity', 'MEDIUM')
        multiplier = self.complexity_factors.get(complexity, 0.85)
        
        weighted_score = (
            components['base_confidence'] * 0.3 +
            components['size_factor'] * 0.25 +
            components['coverage_factor'] * 0.2 +
            components['ml_factor'] * 0.15 +
            components['priority_factor'] * 0.1
        ) * multiplier
        
        components['final_score'] = min(weighted_score, 1.0)
        components['confidence'] = statistics.mean([v for v in components.values() if v > 0])
        
        return components

    def _calculate_intelligence(self, matches, table_info, factor_info):
        components = []
        
        if matches:
            ultra_count = sum(1 for m in matches if m['match_type'] == 'ultra_semantic')
            semantic_count = sum(1 for m in matches if m['match_type'] == 'semantic')
            match_intel = (ultra_count * 1.0 + semantic_count * 0.7) / len(matches)
            components.append(match_intel)
        
        data_intel = min(table_info['size_priority_score'] / 10, 1.0) * 0.6
        components.append(data_intel)
        
        priority_intel = self.priority_matrix.get(factor_info.get('priority', 'MEDIUM'), 0.6)
        components.append(priority_intel)
        
        return round(statistics.mean(components) if components else 0.0, 3)

    def _determine_difficulty(self, feasibility, intelligence, factor_info):
        complexity = factor_info.get('complexity', 'MEDIUM')
        combined = (feasibility + intelligence) / 2
        
        if combined > 0.8 and complexity == 'LOW':
            return 'AO1_Trivial'
        elif combined > 0.7 and complexity in ['LOW', 'MEDIUM']:
            return 'AO1_Easy'
        elif combined > 0.5:
            return 'AO1_Medium'
        elif combined > 0.3:
            return 'AO1_Hard'
        else:
            return 'AO1_Very_Hard'

    def _calculate_rank(self, feasibility, intelligence, table_info, factor_info):
        factors = {
            'feasibility': feasibility['final_score'] * 0.25,
            'intelligence': intelligence * 0.20,
            'priority': self.priority_matrix.get(factor_info.get('priority', 'MEDIUM'), 0.6) * 0.20,
            'data_size': min(table_info['size_priority_score'] / 10, 1.0) * 0.15,
            'complexity_bonus': (1.0 - self.complexity_factors.get(
                factor_info.get('complexity', 'MEDIUM'), 0.85)) * 0.20
        }
        return round(sum(factors.values()), 3)

    def prioritize_recommendations(self, recommendations: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        all_recs = []
        for role, recs in recommendations.items():
            all_recs.extend(recs)
        
        prioritized = sorted(all_recs, key=lambda x: (
            -x.get('recommendation_rank', 0),
            -x['feasibility_score'],
            -x.get('intelligence_score', 0),
            -x['size_priority_score']
        ))
        
        self.recommendation_stats.update({
            'total': len(prioritized),
            'high_confidence': len([r for r in prioritized if r.get('confidence_score', 0) > 0.8]),
            'ultra_semantic': len([r for r in prioritized if any(
                m['match_type'] == 'ultra_semantic' for m in r['matched_columns']
            )]),
            'ml_enhanced': len([r for r in prioritized if any(
                m.get('ml_confidence', 0) > 0.5 for m in r['matched_columns']
            )])
        })
        
        return prioritized

    def save_recommendations(self, recommendations, output_file: str = "ao1_recommendations.json"):
        prioritized = self.prioritize_recommendations(recommendations)
        
        output_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'analysis_type': 'ultra_intelligent_ao1_visibility'
            },
            'executive_summary': {
                'total_metrics': len(prioritized),
                'implementation_ready': len([r for r in prioritized if r['implementation_difficulty'] in ['AO1_Trivial', 'AO1_Easy']]),
                'high_priority': len([r for r in prioritized if r.get('priority') in ['CRITICAL', 'HIGH']]),
                'avg_feasibility': statistics.mean([r['feasibility_score'] for r in prioritized]) if prioritized else 0,
                'avg_intelligence': statistics.mean([r.get('intelligence_score', 0) for r in prioritized]) if prioritized else 0
            },
            'ai_analysis_summary': self.recommendation_stats,
            'recommendations_by_role': recommendations,
            'prioritized_recommendations': prioritized
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"Saved {len(prioritized)} recommendations to {output_file}")
        return output_data