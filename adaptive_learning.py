#!/usr/bin/env python3

import statistics
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from ai_insights import IntelligenceInsight

class AdaptiveLearningSystem:
    def __init__(self):
        self.pattern_weights = defaultdict(float)
        self.success_history = []
        self.performance_metrics = defaultdict(list)
        self.strategy_effectiveness = defaultdict(lambda: {'attempts': 0, 'successes': 0})
        self.learning_rate = 0.1
        
    def update_pattern_weights(self, patterns: Dict[str, float], success_rate: float):
        for pattern, weight in patterns.items():
            current_weight = self.pattern_weights[pattern]
            self.pattern_weights[pattern] = (
                current_weight * (1 - self.learning_rate) + 
                weight * success_rate * self.learning_rate
            )
    
    def record_strategy_outcome(self, strategy_name: str, success: bool, metadata: Dict[str, Any] = None):
        self.strategy_effectiveness[strategy_name]['attempts'] += 1
        if success:
            self.strategy_effectiveness[strategy_name]['successes'] += 1
        
        outcome_record = {
            'strategy': strategy_name,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.success_history.append(outcome_record)
        
        if len(self.success_history) > 1000:
            self.success_history = self.success_history[-500:]
    
    def get_strategy_confidence(self, strategy_name: str) -> float:
        stats = self.strategy_effectiveness[strategy_name]
        if stats['attempts'] == 0:
            return 0.5
        return stats['successes'] / stats['attempts']
    
    def recommend_optimal_strategy(self, context: Dict[str, Any]) -> Tuple[str, float]:
        strategy_scores = {}
        
        for strategy, stats in self.strategy_effectiveness.items():
            if stats['attempts'] > 0:
                base_score = stats['successes'] / stats['attempts']
                
                context_boost = self._calculate_context_boost(strategy, context)
                strategy_scores[strategy] = base_score * (1 + context_boost)
        
        if not strategy_scores:
            return 'default', 0.5
        
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
        return best_strategy[0], best_strategy[1]
    
    def _calculate_context_boost(self, strategy: str, context: Dict[str, Any]) -> float:
        boost = 0.0
        
        recent_successes = [h for h in self.success_history[-50:] 
                          if h['strategy'] == strategy and h['success']]
        
        if len(recent_successes) > 5:
            boost += 0.2
        
        if 'project_size' in context:
            project_size = context['project_size']
            if strategy == 'parallel_processing' and project_size > 1000:
                boost += 0.3
            elif strategy == 'sequential_processing' and project_size < 100:
                boost += 0.3
        
        return boost
    
    def generate_learning_insights(self) -> List[IntelligenceInsight]:
        insights = []
        
        if len(self.success_history) > 10:
            recent_success_rate = sum(1 for h in self.success_history[-20:] if h['success']) / 20
            
            insights.append(IntelligenceInsight(
                insight_type="learning_performance",
                content=f"Recent success rate: {recent_success_rate:.1%}",
                confidence_score=0.9,
                evidence=[f"Based on {len(self.success_history)} learning iterations"],
                recommendations=self._generate_performance_recommendations(recent_success_rate)
            ))
        
        strategy_performance = {}
        for strategy, stats in self.strategy_effectiveness.items():
            if stats['attempts'] > 5:
                success_rate = stats['successes'] / stats['attempts']
                strategy_performance[strategy] = success_rate
        
        if strategy_performance:
            best_strategy = max(strategy_performance.items(), key=lambda x: x[1])
            worst_strategy = min(strategy_performance.items(), key=lambda x: x[1])
            
            insights.append(IntelligenceInsight(
                insight_type="strategy_effectiveness",
                content=f"Most effective strategy: {best_strategy[0]} ({best_strategy[1]:.1%})",
                confidence_score=0.8,
                evidence=[f"Compared {len(strategy_performance)} strategies"],
                recommendations=[f"Prioritize {best_strategy[0]} approach", f"Investigate issues with {worst_strategy[0]}"]
            ))
        
        return insights
    
    def _generate_performance_recommendations(self, success_rate: float) -> List[str]:
        if success_rate > 0.8:
            return ["Performance is excellent", "Consider expanding to more complex scenarios"]
        elif success_rate > 0.6:
            return ["Good performance", "Monitor for optimization opportunities"]
        elif success_rate > 0.4:
            return ["Moderate performance", "Review strategy selection logic"]
        else:
            return ["Performance needs improvement", "Analyze failure patterns", "Increase learning data"]