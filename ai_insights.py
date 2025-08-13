#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class AIInsight:
    insight_type: str
    confidence: float
    content: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reasoning_chain: List[str] = field(default_factory=list)
    predicted_impact: float = 0.0
    certainty_level: str = "medium"

@dataclass
class IntelligenceInsight:
    insight_type: str
    content: str
    confidence_score: float
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AdaptiveLearningResult:
    learned_patterns: Dict[str, float]
    updated_strategies: Dict[str, Any]
    performance_insights: List[IntelligenceInsight]
    optimization_recommendations: List[str] = field(default_factory=list)

@dataclass
class AO1DiscoveryResult:
    discovery_stats: Dict[str, Any]
    ai_insights: List[AIInsight]
    visibility_analysis: Dict[str, Any]
    anomaly_detection: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    confidence_summary: Dict[str, float]
    visibility_metrics: Dict[str, Any]