#!/usr/bin/env python3

import statistics
from typing import Dict, Any
from collections import defaultdict

class AssetCountPredictor:
    def __init__(self):
        self.base_rates = {
            'small_project': 500,
            'medium_project': 2000,
            'large_project': 10000,
            'enterprise_project': 50000
        }
        
        self.multipliers = {
            'high_table_density': 1.5,
            'security_focused': 1.3,
            'multi_region': 1.8,
            'cloud_native': 1.2
        }
    
    def predict(self, context: Dict[str, Any]) -> int:
        dataset_count = context.get('dataset_count', 0)
        table_count = context.get('table_count', 0)
        
        project_scale = self._determine_project_scale(dataset_count, table_count)
        base_count = self.base_rates[project_scale]
        
        multiplier = 1.0
        for factor, factor_multiplier in self.multipliers.items():
            if context.get(factor, False):
                multiplier *= factor_multiplier
        
        predicted_count = int(base_count * multiplier)
        return max(1, predicted_count)
    
    def get_confidence_interval(self, context: Dict[str, Any]) -> Dict[str, float]:
        predicted = self.predict(context)
        uncertainty = 0.3
        
        return {
            'lower': int(predicted * (1 - uncertainty)),
            'upper': int(predicted * (1 + uncertainty))
        }
    
    def _determine_project_scale(self, dataset_count: int, table_count: int) -> str:
        complexity_score = dataset_count + (table_count / 10)
        
        if complexity_score < 20:
            return 'small_project'
        elif complexity_score < 100:
            return 'medium_project'
        elif complexity_score < 500:
            return 'large_project'
        else:
            return 'enterprise_project'

class ProcessingTimePredictor:
    def __init__(self):
        self.time_factors = {
            'base_processing': 60,
            'per_dataset': 5,
            'per_table': 0.5,
            'per_thousand_assets': 10
        }
    
    def predict(self, context: Dict[str, Any]) -> float:
        dataset_count = context.get('dataset_count', 0)
        table_count = context.get('table_count', 0)
        estimated_assets = context.get('estimated_assets', 0)
        
        base_time = self.time_factors['base_processing']
        dataset_time = dataset_count * self.time_factors['per_dataset']
        table_time = table_count * self.time_factors['per_table']
        asset_time = (estimated_assets / 1000) * self.time_factors['per_thousand_assets']
        
        total_time = base_time + dataset_time + table_time + asset_time
        
        parallel_workers = context.get('parallel_workers', 16)
        parallelism_factor = min(1.0, parallel_workers / 32)
        
        return max(30, total_time * (1 - parallelism_factor * 0.7))
    
    def get_confidence_interval(self, context: Dict[str, Any]) -> Dict[str, float]:
        predicted = self.predict(context)
        
        return {
            'lower': predicted * 0.6,
            'upper': predicted * 1.8
        }

class SuccessProbabilityPredictor:
    def __init__(self):
        self.success_factors = {
            'authentication_available': 0.3,
            'sufficient_permissions': 0.25,
            'network_connectivity': 0.2,
            'reasonable_data_size': 0.15,
            'stable_schema': 0.1
        }
    
    def predict(self, context: Dict[str, Any]) -> float:
        success_probability = 0.5
        
        for factor, weight in self.success_factors.items():
            if context.get(factor, False):
                success_probability += weight
            else:
                success_probability -= weight * 0.5
        
        return max(0.1, min(0.95, success_probability))
    
    def get_confidence_interval(self, context: Dict[str, Any]) -> Dict[str, float]:
        predicted = self.predict(context)
        margin = 0.15
        
        return {
            'lower': max(0.0, predicted - margin),
            'upper': min(1.0, predicted + margin)
        }

class PredictiveModeling:
    def __init__(self):
        self.asset_count_model = AssetCountPredictor()
        self.coverage_predictor = CoveragePredictor()
        self.performance_predictor = ProcessingTimePredictor()
        self.success_predictor = SuccessProbabilityPredictor()
        self.historical_data = []
        self.prediction_accuracy = defaultdict(list)
    
    def predict_discovery_outcomes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        predictions = {}
        
        models = {
            'asset_count': self.asset_count_model,
            'processing_time': self.performance_predictor,
            'success_probability': self.success_predictor
        }
        
        for model_name, model in models.items():
            try:
                prediction = model.predict(context)
                confidence_interval = model.get_confidence_interval(context)
                
                predictions[model_name] = {
                    'value': prediction,
                    'confidence_interval': confidence_interval,
                    'model_accuracy': self._get_model_accuracy(model_name)
                }
            except Exception as e:
                predictions[model_name] = {
                    'value': None,
                    'confidence_interval': None,
                    'model_accuracy': 0.0,
                    'error': str(e)
                }
        
        predictions['meta'] = {
            'prediction_timestamp': context.get('timestamp', 'unknown'),
            'context_hash': str(hash(str(context)))[:8],
            'overall_confidence': self._calculate_overall_confidence(predictions)
        }
        
        return predictions
    
    def update_predictions_with_actual(self, predictions: Dict[str, Any], actual_results: Dict[str, Any]):
        for model_name in ['asset_count', 'processing_time', 'success_probability']:
            if model_name in predictions and model_name in actual_results:
                predicted_value = predictions[model_name].get('value')
                actual_value = actual_results[model_name]
                
                if predicted_value is not None and actual_value is not None:
                    accuracy = self._calculate_accuracy(predicted_value, actual_value)
                    self.prediction_accuracy[model_name].append(accuracy)
                    
                    if len(self.prediction_accuracy[model_name]) > 100:
                        self.prediction_accuracy[model_name] = self.prediction_accuracy[model_name][-50:]
    
    def _get_model_accuracy(self, model_name: str) -> float:
        accuracies = self.prediction_accuracy[model_name]
        return statistics.mean(accuracies) if accuracies else 0.5
    
    def _calculate_accuracy(self, predicted: float, actual: float) -> float:
        if predicted == 0 and actual == 0:
            return 1.0
        if predicted == 0 or actual == 0:
            return 0.0
        
        error_ratio = abs(predicted - actual) / max(predicted, actual)
        return max(0.0, 1.0 - error_ratio)
    
    def _calculate_overall_confidence(self, predictions: Dict[str, Any]) -> float:
        model_confidences = []
        
        for model_name, prediction_data in predictions.items():
            if model_name != 'meta' and isinstance(prediction_data, dict):
                accuracy = prediction_data.get('model_accuracy', 0.5)
                model_confidences.append(accuracy)
        
        return statistics.mean(model_confidences) if model_confidences else 0.5

class CoveragePredictor:
    def __init__(self):
        self.base_coverage_rates = {
            'hostname_fields': 0.8,
            'ip_fields': 0.6,
            'infrastructure_fields': 0.4,
            'security_fields': 0.3,
            'business_fields': 0.2
        }
    
    def predict(self, context: Dict[str, Any]) -> float:
        field_types_present = context.get('detected_field_types', [])
        
        if not field_types_present:
            return 0.3
        
        coverage_scores = []
        for field_type in field_types_present:
            base_rate = self.base_coverage_rates.get(field_type, 0.1)
            coverage_scores.append(base_rate)
        
        return min(0.95, max(0.1, statistics.mean(coverage_scores)))