from typing import List
from math import log10, sqrt
from datetime import datetime
from models import EnhancedMatch

class ActiveLearningEngine:
    def __init__(self):
        self.training_examples = []
        self.uncertainty_samples = []
        self.feedback_history = []
        self.model_performance = {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0}
    
    def suggest_validation_candidates(self, matches: List[EnhancedMatch], n_suggestions: int = 10) -> List[EnhancedMatch]:
        if len(matches) <= n_suggestions:
            return matches
        
        uncertainty_scores = []
        for match in matches:
            score = match.score
            entropy = -score * log10(score + 1e-10) - (1-score) * log10(1-score + 1e-10)
            
            diversity_score = self._calculate_diversity_score(match, matches)
            
            badge_score = entropy + 0.3 * diversity_score
            uncertainty_scores.append((match, badge_score))
        
        uncertainty_scores.sort(key=lambda x: x[1], reverse=True)
        return [match for match, _ in uncertainty_scores[:n_suggestions]]
    
    def _calculate_diversity_score(self, target_match: EnhancedMatch, all_matches: List[EnhancedMatch]) -> float:
        target_features = self._extract_features(target_match)
        
        min_distance = float('inf')
        for other_match in all_matches:
            if other_match.field == target_match.field and other_match.table == target_match.table:
                continue
            
            other_features = self._extract_features(other_match)
            distance = self._euclidean_distance(target_features, other_features)
            min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else 1.0
    
    def _extract_features(self, match: EnhancedMatch) -> List[float]:
        return [
            match.score,
            match.semantic_depth,
            match.business_priority / 10.0,
            len(match.reasoning),
            hash(match.requirement) % 1000 / 1000.0,
            len(match.field) / 50.0
        ]
    
    def _euclidean_distance(self, features1: List[float], features2: List[float]) -> float:
        return sqrt(sum((a - b) ** 2 for a, b in zip(features1, features2)))
    
    def record_feedback(self, match: EnhancedMatch, is_correct: bool, user_feedback: str = ""):
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'match': {
                'field': match.field,
                'table': match.table,
                'requirement': match.requirement,
                'score': match.score,
                'reasoning': match.reasoning
            },
            'is_correct': is_correct,
            'user_feedback': user_feedback,
            'features': self._extract_features(match)
        }
        
        self.feedback_history.append(feedback_entry)
        
        if len(self.feedback_history) >= 10:
            self._update_performance_estimates()
    
    def _update_performance_estimates(self):
        recent_feedback = self.feedback_history[-50:]
        
        if recent_feedback:
            correct_predictions = sum(1 for f in recent_feedback if f['is_correct'])
            self.model_performance['accuracy'] = correct_predictions / len(recent_feedback)
            
            true_positives = sum(1 for f in recent_feedback if f['is_correct'])
            false_positives = sum(1 for f in recent_feedback if not f['is_correct'])
            
            if true_positives + false_positives > 0:
                self.model_performance['precision'] = true_positives / (true_positives + false_positives)