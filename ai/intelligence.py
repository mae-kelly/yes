# ai/intelligence.py

import numpy as np
import asyncio
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import statistics
import logging
from .neural import SemanticEmbedder, PatternRecognizer, FieldClassifier
from .content import ContentAnalyzer, ValidationEngine
from core.types import Intelligence, FieldMapping, Discovery

logger = logging.getLogger(__name__)

class IntelligenceEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.embedder = SemanticEmbedder()
        self.recognizer = PatternRecognizer()
        self.analyzer = ContentAnalyzer()
        self.validator = ValidationEngine()
        self.intelligence = Intelligence()
        
        self.field_priorities = {
            'hostname': 100, 'fqdn': 95, 'ip_address': 90, 'mac_address': 85,
            'infrastructure_type': 80, 'system_classification': 75,
            'global_region': 70, 'business_unit': 65, 'country': 60
        }
        
        self.learning_enabled = config.get('enable_machine_learning', False)
        self.prediction_cache = {}
        self.strategy_history = []
    
    async def analyze_field_intelligently(self, column_name: str, samples: List[str], 
                                        context: Dict[str, Any] = None) -> Optional[FieldMapping]:
        
        basic_analysis = self.analyzer.analyze_column(column_name, samples, context)
        if not basic_analysis:
            return None
        
        field_type, confidence, metadata = basic_analysis
        
        semantic_score = self.embedder.semantic_similarity(column_name, field_type)
        validation_score = self.validator.validate_field(field_type, samples)
        
        pattern_confidence, pattern_info = self.recognizer.recognize_pattern(field_type, {
            'column_name': column_name,
            'sample_count': len(samples),
            'avg_length': statistics.mean([len(s) for s in samples]) if samples else 0
        })
        
        enhanced_confidence = (
            confidence * 0.4 +
            semantic_score * 0.3 +
            validation_score * 0.2 +
            pattern_confidence * 0.1
        )
        
        if enhanced_confidence < 0.5:
            return None
        
        mapping = FieldMapping(
            field_type=field_type,
            column=column_name,
            confidence=enhanced_confidence,
            samples=samples[:10]
        )
        
        self.recognizer.learn_pattern(field_type, {
            'column_name': column_name,
            'sample_count': len(samples),
            'confidence': enhanced_confidence
        }, enhanced_confidence > 0.7)
        
        return mapping
    
    async def predict_discovery_outcomes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cache_key = str(hash(str(context)))
        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]
        
        dataset_count = context.get('dataset_count', 0)
        table_count = context.get('table_count', 0)
        
        asset_prediction = self._predict_asset_count(dataset_count, table_count, context)
        time_prediction = self._predict_processing_time(dataset_count, table_count, context)
        success_prediction = self._predict_success_rate(context)
        
        predictions = {
            'estimated_assets': asset_prediction,
            'processing_time_seconds': time_prediction,
            'success_probability': success_prediction,
            'confidence_intervals': self._calculate_confidence_intervals(context)
        }
        
        self.prediction_cache[cache_key] = predictions
        return predictions
    
    def _predict_asset_count(self, datasets: int, tables: int, context: Dict[str, Any]) -> int:
        base_multipliers = {'small': 200, 'medium': 1000, 'large': 5000, 'enterprise': 25000}
        
        scale = self._determine_scale(datasets, tables)
        base_count = base_multipliers[scale]
        
        multiplier = 1.0
        if context.get('has_security_data', False):
            multiplier *= 1.5
        if context.get('has_log_data', False):
            multiplier *= 1.3
        if context.get('cloud_native', False):
            multiplier *= 1.2
        
        return int(base_count * multiplier * max(1, datasets / 10))
    
    def _predict_processing_time(self, datasets: int, tables: int, context: Dict[str, Any]) -> float:
        base_time = 120
        dataset_time = datasets * 8
        table_time = tables * 0.8
        
        total_time = base_time + dataset_time + table_time
        
        workers = context.get('parallel_workers', 16)
        parallelism_factor = min(1.0, workers / 32)
        
        return max(60, total_time * (1 - parallelism_factor * 0.6))
    
    def _predict_success_rate(self, context: Dict[str, Any]) -> float:
        base_rate = 0.7
        
        factors = {
            'auth_available': 0.15,
            'permissions_granted': 0.1,
            'network_stable': 0.08,
            'data_quality_good': 0.07
        }
        
        for factor, boost in factors.items():
            if context.get(factor, False):
                base_rate += boost
        
        return min(0.95, max(0.3, base_rate))
    
    def _determine_scale(self, datasets: int, tables: int) -> str:
        complexity = datasets + (tables / 20)
        
        if complexity < 15:
            return 'small'
        elif complexity < 75:
            return 'medium'
        elif complexity < 300:
            return 'large'
        else:
            return 'enterprise'
    
    def _calculate_confidence_intervals(self, context: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        uncertainty = max(0.15, min(0.4, 1.0 / max(context.get('dataset_count', 1), 1)))
        
        return {
            'asset_count': {'lower': 0.7, 'upper': 1.4},
            'processing_time': {'lower': 0.6, 'upper': 1.8},
            'success_rate': {'lower': 1.0 - uncertainty, 'upper': 1.0}
        }
    
    async def recommend_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        predictions = await self.predict_discovery_outcomes(context)
        
        estimated_assets = predictions['estimated_assets']
        processing_time = predictions['processing_time_seconds']
        
        if estimated_assets > 50000:
            strategy = 'enterprise_parallel'
            params = {
                'batch_size': 2500,
                'parallel_workers': 48,
                'timeout_seconds': 900,
                'memory_limit_mb': 4096
            }
        elif estimated_assets > 10000:
            strategy = 'large_scale'
            params = {
                'batch_size': 1500,
                'parallel_workers': 24,
                'timeout_seconds': 600,
                'memory_limit_mb': 2048
            }
        elif processing_time > 1800:
            strategy = 'long_running'
            params = {
                'batch_size': 1000,
                'parallel_workers': 16,
                'timeout_seconds': 450,
                'checkpoint_interval': 300
            }
        else:
            strategy = 'standard'
            params = {
                'batch_size': 800,
                'parallel_workers': 12,
                'timeout_seconds': 300
            }
        
        return {
            'strategy': strategy,
            'parameters': params,
            'reasoning': self._explain_strategy(strategy, context, predictions),
            'confidence': min(0.9, predictions['success_probability'])
        }
    
    def _explain_strategy(self, strategy: str, context: Dict[str, Any], predictions: Dict[str, Any]) -> str:
        explanations = {
            'enterprise_parallel': f"Large dataset ({predictions['estimated_assets']:,} assets) requires maximum parallelization",
            'large_scale': f"Medium-large scale ({predictions['estimated_assets']:,} assets) benefits from increased resources",
            'long_running': f"Extended processing time ({predictions['processing_time_seconds']/60:.1f}min) needs checkpointing",
            'standard': "Balanced approach for typical dataset size and complexity"
        }
        return explanations.get(strategy, "Standard processing approach")
    
    async def generate_insights(self, discovery: Discovery) -> List[Dict[str, Any]]:
        insights = []
        
        if discovery.assets:
            asset_insights = self._analyze_asset_distribution(discovery.assets)
            insights.extend(asset_insights)
        
        if discovery.schemas:
            schema_insights = self._analyze_schema_quality(discovery.schemas)
            insights.extend(schema_insights)
        
        coverage_insights = self._analyze_coverage(discovery.assets)
        insights.extend(coverage_insights)
        
        return insights
    
    def _analyze_asset_distribution(self, assets: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        
        total_assets = len(assets)
        high_quality = sum(1 for asset in assets.values() if asset.quality > 0.8)
        multi_source = sum(1 for asset in assets.values() if asset.sources > 1)
        
        insights.append({
            'type': 'asset_quality',
            'title': 'Asset Quality Analysis',
            'content': f"Discovered {total_assets:,} assets with {high_quality:,} high-quality entries",
            'metrics': {
                'total_assets': total_assets,
                'high_quality_count': high_quality,
                'quality_rate': high_quality / max(total_assets, 1),
                'multi_source_count': multi_source
            },
            'confidence': 0.9
        })
        
        return insights
    
    def _analyze_schema_quality(self, schemas: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        
        if not schemas:
            return insights
        
        avg_quality = statistics.mean([schema.quality for schema in schemas.values()])
        high_quality_schemas = sum(1 for schema in schemas.values() if schema.quality > 0.8)
        
        insights.append({
            'type': 'schema_analysis',
            'title': 'Schema Quality Assessment',
            'content': f"Analyzed {len(schemas)} schemas with average quality {avg_quality:.2f}",
            'metrics': {
                'total_schemas': len(schemas),
                'avg_quality': avg_quality,
                'high_quality_schemas': high_quality_schemas
            },
            'confidence': 0.85
        })
        
        return insights
    
    def _analyze_coverage(self, assets: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        
        if not assets:
            return insights
        
        coverage_stats = {
            'cmdb': sum(1 for asset in assets.values() if asset.cmdb),
            'splunk': sum(1 for asset in assets.values() if asset.splunk),
            'chronicle': sum(1 for asset in assets.values() if asset.chronicle),
            'crowdstrike': sum(1 for asset in assets.values() if asset.crowdstrike)
        }
        
        total = len(assets)
        coverage_rates = {k: v / total for k, v in coverage_stats.items()}
        
        insights.append({
            'type': 'coverage_analysis',
            'title': 'Data Source Coverage',
            'content': f"Coverage rates: CMDB {coverage_rates['cmdb']:.1%}, Splunk {coverage_rates['splunk']:.1%}",
            'metrics': coverage_rates,
            'confidence': 0.95
        })
        
        return insights
    
    async def learn_from_results(self, discovery: Discovery, predictions: Dict[str, Any]) -> Dict[str, Any]:
        if not self.learning_enabled:
            return {'status': 'learning_disabled'}
        
        learning_results = {}
        
        if predictions and discovery.assets:
            actual_assets = len(discovery.assets)
            predicted_assets = predictions.get('estimated_assets', 0)
            
            if predicted_assets > 0:
                accuracy = 1.0 - abs(actual_assets - predicted_assets) / predicted_assets
                learning_results['prediction_accuracy'] = accuracy
        
        strategy_used = discovery.stats.get('strategy_used')
        if strategy_used:
            success_rate = discovery.stats.get('success_rate', 0.5)
            self.strategy_history.append({
                'strategy': strategy_used,
                'success_rate': success_rate,
                'timestamp': datetime.now(),
                'context': discovery.stats.get('context', {})
            })
        
        learning_results['patterns_learned'] = len(self.recognizer.learned_patterns)
        learning_results['strategy_evaluations'] = len(self.strategy_history)
        
        return learning_results