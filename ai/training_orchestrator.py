import asyncio
import logging
import torch
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from .bigquery_scanner import BigQueryPublicDatasetScanner
from .neural_field_classifier import M1OptimizedFieldClassifier, ContinualFieldLearner, SmartFieldTypeInference
from concurrent.futures import ThreadPoolExecutor
import schedule
import threading
import time

logger = logging.getLogger(__name__)

class IntensiveTrainingOrchestrator:
    def __init__(self, cache_dir: str = ".ml_training_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.scanner = BigQueryPublicDatasetScanner(cache_dir)
        
        self.model = M1OptimizedFieldClassifier()
        self.learner = ContinualFieldLearner(self.model, cache_dir)
        self.inference_engine = SmartFieldTypeInference()
        
        self.model_save_path = self.cache_dir / "field_classifier_model.pt"
        
        self.training_config = {
            'initial_training_epochs': 10,
            'continual_learning_epochs': 2,
            'batch_size': 32,
            'learning_rate': 2e-5,
            'pattern_update_frequency': 50,
            'model_save_frequency': 100
        }
        
        self.training_stats = {
            'total_training_time': 0.0,
            'samples_processed': 0,
            'model_accuracy': 0.0,
            'last_training_update': None,
            'pattern_memory_updates': 0
        }
        
        self.performance_metrics = {
            'hostname_accuracy': 0.0,
            'ip_address_accuracy': 0.0,
            'overall_confidence': 0.0,
            'inference_speed_ms': 0.0
        }
        
        self.continuous_learning_active = False
        self.learning_thread = None
        
    async def perform_intensive_initial_training(self):
        logger.info("Starting intensive initial training process")
        start_time = datetime.now()
        
        logger.info("Phase 1: Scanning public BigQuery datasets for training patterns")
        total_patterns = await self.scanner.scan_all_public_datasets()
        
        if total_patterns == 0:
            logger.warning("No training patterns collected from public datasets")
            return False
        
        logger.info(f"Phase 2: Retrieved {total_patterns} training patterns")
        training_data = self.scanner.get_training_data()
        
        if not training_data:
            logger.warning("No usable training data available")
            return False
        
        logger.info(f"Phase 3: Training neural model on {len(training_data)} samples")
        self.learner.train_on_dataset(
            training_data,
            epochs=self.training_config['initial_training_epochs'],
            batch_size=self.training_config['batch_size']
        )
        
        logger.info("Phase 4: Evaluating model performance")
        test_split = len(training_data) // 5
        train_data = training_data[:-test_split]
        test_data = training_data[-test_split:]
        
        evaluation_results = self.learner.evaluate_on_test_data(test_data)
        
        self.training_stats['model_accuracy'] = evaluation_results['overall_accuracy']
        self.training_stats['samples_processed'] = len(training_data)
        self.training_stats['last_training_update'] = datetime.now()
        
        self.performance_metrics.update(evaluation_results.get('field_type_accuracies', {}))
        
        logger.info(f"Phase 5: Saving trained model")
        self.learner.save_model(str(self.model_save_path))
        
        training_time = (datetime.now() - start_time).total_seconds()
        self.training_stats['total_training_time'] = training_time
        
        logger.info(f"Initial training completed in {training_time:.2f} seconds")
        logger.info(f"Model accuracy: {self.training_stats['model_accuracy']:.4f}")
        
        return True
    
    def start_continuous_learning(self):
        if self.continuous_learning_active:
            logger.warning("Continuous learning already active")
            return
        
        self.continuous_learning_active = True
        
        schedule.every(6).hours.do(self._scheduled_model_update)
        schedule.every(24).hours.do(self._scheduled_dataset_rescan)
        schedule.every().week.do(self._scheduled_performance_evaluation)
        
        self.learning_thread = threading.Thread(target=self._continuous_learning_loop, daemon=True)
        self.learning_thread.start()
        
        logger.info("Continuous learning system activated")
    
    def stop_continuous_learning(self):
        self.continuous_learning_active = False
        if self.learning_thread:
            self.learning_thread.join(timeout=5.0)
        logger.info("Continuous learning system deactivated")
    
    def _continuous_learning_loop(self):
        while self.continuous_learning_active:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in continuous learning loop: {e}")
                time.sleep(300)
    
    def _scheduled_model_update(self):
        logger.info("Performing scheduled model update")
        
        try:
            new_training_data = self.scanner.get_training_data()
            
            recent_threshold = datetime.now() - timedelta(days=1)
            recent_data = [
                item for item in new_training_data
                if 'created_at' in item and datetime.fromisoformat(item['created_at']) > recent_threshold
            ]
            
            if recent_data:
                self.learner.continual_learning_update(recent_data)
                self.learner.save_model(str(self.model_save_path))
                logger.info(f"Model updated with {len(recent_data)} new samples")
        
        except Exception as e:
            logger.error(f"Scheduled model update failed: {e}")
    
    def _scheduled_dataset_rescan(self):
        logger.info("Performing scheduled dataset rescan")
        
        try:
            asyncio.run(self.scanner.scan_all_public_datasets())
            logger.info("Dataset rescan completed")
        
        except Exception as e:
            logger.error(f"Scheduled dataset rescan failed: {e}")
    
    def _scheduled_performance_evaluation(self):
        logger.info("Performing scheduled performance evaluation")
        
        try:
            test_data = self.scanner.get_training_data()[-1000:]
            
            if test_data:
                start_time = time.time()
                evaluation_results = self.learner.evaluate_on_test_data(test_data)
                evaluation_time = (time.time() - start_time) * 1000
                
                self.performance_metrics.update({
                    'overall_accuracy': evaluation_results['overall_accuracy'],
                    'inference_speed_ms': evaluation_time / len(test_data)
                })
                
                logger.info(f"Performance evaluation: Accuracy={evaluation_results['overall_accuracy']:.4f}")
        
        except Exception as e:
            logger.error(f"Performance evaluation failed: {e}")
    
    async def train_on_user_data(self, user_training_examples: List[Dict[str, Any]]):
        logger.info(f"Training on user-provided data: {len(user_training_examples)} examples")
        
        if not user_training_examples:
            return
        
        enriched_examples = []
        
        for example in user_training_examples:
            enriched_example = {
                'column_name': example.get('column_name', ''),
                'data_samples': example.get('data_samples', []),
                'field_type': example.get('field_type', 'unknown'),
                'context_columns': example.get('context_columns', []),
                'confidence': example.get('confidence', 1.0),
                'user_provided': True,
                'created_at': datetime.now().isoformat()
            }
            enriched_examples.append(enriched_example)
        
        self.learner.continual_learning_update(enriched_examples)
        
        self.training_stats['samples_processed'] += len(enriched_examples)
        self.training_stats['last_training_update'] = datetime.now()
        
        logger.info("User data training completed")
    
    def get_intelligent_field_prediction(self, column_name: str, data_samples: List[str], 
                                       context_columns: List[str] = None) -> Dict[str, Any]:
        
        start_time = time.time()
        
        predicted_type, confidence = self.inference_engine.analyze_column(
            column_name, data_samples, context_columns
        )
        
        inference_time = (time.time() - start_time) * 1000
        
        pattern_analysis = self._analyze_data_patterns(data_samples)
        context_analysis = self._analyze_context_relevance(column_name, context_columns or [])
        
        return {
            'predicted_field_type': predicted_type,
            'confidence_score': confidence,
            'inference_time_ms': inference_time,
            'pattern_analysis': pattern_analysis,
            'context_analysis': context_analysis,
            'model_version': self.training_stats.get('last_training_update', 'unknown'),
            'samples_analyzed': len(data_samples)
        }
    
    def _analyze_data_patterns(self, data_samples: List[str]) -> Dict[str, Any]:
        if not data_samples:
            return {'pattern_count': 0, 'consistency': 0.0}
        
        patterns = {
            'numeric_count': sum(1 for s in data_samples if str(s).replace('.', '').isdigit()),
            'alpha_count': sum(1 for s in data_samples if str(s).isalpha()),
            'alphanumeric_count': sum(1 for s in data_samples if str(s).replace('-', '').replace('_', '').isalnum()),
            'contains_dots': sum(1 for s in data_samples if '.' in str(s)),
            'contains_dashes': sum(1 for s in data_samples if '-' in str(s)),
            'avg_length': sum(len(str(s)) for s in data_samples) / len(data_samples),
            'unique_count': len(set(data_samples))
        }
        
        consistency = patterns['unique_count'] / len(data_samples) if data_samples else 0.0
        
        return {
            'patterns': patterns,
            'consistency': consistency,
            'sample_size': len(data_samples)
        }
    
    def _analyze_context_relevance(self, column_name: str, context_columns: List[str]) -> Dict[str, Any]:
        column_lower = column_name.lower()
        context_lower = [col.lower() for col in context_columns]
        
        relevance_indicators = {
            'network_context': any(term in ' '.join(context_lower) for term in ['ip', 'mac', 'network', 'subnet']),
            'identity_context': any(term in ' '.join(context_lower) for term in ['user', 'account', 'identity', 'person']),
            'infrastructure_context': any(term in ' '.join(context_lower) for term in ['server', 'host', 'machine', 'device']),
            'temporal_context': any(term in ' '.join(context_lower) for term in ['date', 'time', 'created', 'updated']),
            'geographic_context': any(term in ' '.join(context_lower) for term in ['location', 'region', 'country', 'zone'])
        }
        
        context_strength = sum(relevance_indicators.values()) / len(relevance_indicators)
        
        return {
            'relevance_indicators': relevance_indicators,
            'context_strength': context_strength,
            'context_column_count': len(context_columns)
        }
    
    def provide_learning_feedback(self, column_name: str, data_samples: List[str], 
                                correct_field_type: str, context_columns: List[str] = None):
        
        self.inference_engine.learn_from_feedback(
            column_name, data_samples, correct_field_type, context_columns
        )
        
        logger.info(f"Learning feedback provided: {column_name} -> {correct_field_type}")
    
    def get_training_statistics(self) -> Dict[str, Any]:
        return {
            'training_stats': self.training_stats.copy(),
            'performance_metrics': self.performance_metrics.copy(),
            'model_info': {
                'parameters': sum(p.numel() for p in self.model.parameters()),
                'device': str(self.model.device),
                'model_size_mb': self.model_save_path.stat().st_size / (1024 * 1024) if self.model_save_path.exists() else 0
            },
            'continuous_learning_active': self.continuous_learning_active
        }
    
    def benchmark_inference_speed(self, num_samples: int = 1000) -> Dict[str, float]:
        logger.info(f"Benchmarking inference speed with {num_samples} samples")
        
        test_cases = [
            ('hostname', ['server01', 'web-prod-001', 'db-cluster-node-1']),
            ('ip_address', ['192.168.1.1', '10.0.0.1', '172.16.0.1']),
            ('email', ['user@example.com', 'admin@company.org', 'test@domain.net']),
            ('identifier', ['abc123', 'id-456789', 'uuid-abc-def-123'])
        ]
        
        total_time = 0.0
        
        for _ in range(num_samples // len(test_cases)):
            for field_type, samples in test_cases:
                start_time = time.time()
                
                self.inference_engine.analyze_column(f"test_{field_type}", samples)
                
                total_time += time.time() - start_time
        
        avg_time_per_prediction = (total_time / num_samples) * 1000
        predictions_per_second = 1000 / avg_time_per_prediction if avg_time_per_prediction > 0 else 0
        
        return {
            'avg_prediction_time_ms': avg_time_per_prediction,
            'predictions_per_second': predictions_per_second,
            'total_benchmark_time_s': total_time,
            'samples_tested': num_samples
        }

class AdvancedContentAnalyzer:
    def __init__(self, training_orchestrator: IntensiveTrainingOrchestrator):
        self.orchestrator = training_orchestrator
        self.analysis_cache = {}
        
    def analyze_column_quantum_intelligently(self, name: str, values: List[str], 
                                           context: Dict = None) -> Optional[tuple]:
        
        if not values or len(values) < 2:
            return None
        
        cache_key = f"{name}:{hash(tuple(values[:10]))}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        context_columns = []
        if context and 'column_names' in context:
            context_columns = context['column_names']
        
        prediction_result = self.orchestrator.get_intelligent_field_prediction(
            name, values, context_columns
        )
        
        field_type = prediction_result['predicted_field_type']
        confidence = prediction_result['confidence_score']
        
        analysis_metadata = {
            'method': 'neural_field_classifier',
            'inference_time_ms': prediction_result['inference_time_ms'],
            'pattern_analysis': prediction_result['pattern_analysis'],
            'context_analysis': prediction_result['context_analysis'],
            'model_enhanced': True
        }
        
        result = (field_type, confidence, analysis_metadata)
        self.analysis_cache[cache_key] = result
        
        return result
    
    def analyze_column(self, name: str, values: List[str], context: Dict = None):
        return self.analyze_column_quantum_intelligently(name, values, context)