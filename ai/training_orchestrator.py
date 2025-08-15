import asyncio
import logging
import torch
import os
import ssl
import requests
import urllib3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from .bigquery_scanner import BigQueryPublicDatasetScanner
from .neural_field_classifier import M1OptimizedFieldClassifier, ContinualFieldLearner, SmartFieldTypeInference
from .corporate_tokenizer_loader import load_corporate_tokenizer
from concurrent.futures import ThreadPoolExecutor
import schedule
import threading
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class CorporateProxyManager:
    def __init__(self):
        self.proxies = [
            "http://proxy-na.fiserv.one:8080",
            "http://proxy.corp.fiserv.com:8080",
            "http://proxy.fiserv.com:8080",
            "http://webproxy.fiserv.com:3128",
            "http://gateway.fiserv.com:8080"
        ]
        self.working_proxy = None
        self._test_proxies()
    
    def _test_proxies(self):
        for proxy in self.proxies:
            try:
                response = requests.get(
                    'https://httpbin.org/ip',
                    proxies={'http': proxy, 'https': proxy},
                    timeout=10,
                    verify=False
                )
                if response.status_code == 200:
                    self.working_proxy = proxy
                    logger.info(f"Working proxy found: {proxy}")
                    break
            except:
                continue
        
        if not self.working_proxy:
            logger.warning("No working proxy found, using direct connection")
    
    def setup_environment(self):
        if self.working_proxy:
            os.environ['HTTP_PROXY'] = self.working_proxy
            os.environ['HTTPS_PROXY'] = self.working_proxy
            os.environ['http_proxy'] = self.working_proxy
            os.environ['https_proxy'] = self.working_proxy
        
        ssl._create_default_https_context = ssl._create_unverified_context
        
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['SSL_CERT_FILE'] = ''
        os.environ['SSL_CERT_DIR'] = ''
    
    def get_session(self):
        session = requests.Session()
        if self.working_proxy:
            session.proxies = {'http': self.working_proxy, 'https': self.working_proxy}
        session.verify = False
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return session

class IntensiveTrainingOrchestrator:
    def __init__(self, cache_dir: str = ".ml_training_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.proxy_manager = CorporateProxyManager()
        self.proxy_manager.setup_environment()
        
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
            'model_save_frequency': 100,
            'proxy_enabled': self.proxy_manager.working_proxy is not None
        }
        
        self.training_stats = {
            'total_training_time': 0.0,
            'samples_processed': 0,
            'model_accuracy': 0.0,
            'last_training_update': None,
            'pattern_memory_updates': 0,
            'proxy_method': self.proxy_manager.working_proxy or 'direct',
            'tokenizer_method': 'not_loaded'
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
        logger.info("Starting intensive initial training with corporate proxy support")
        start_time = datetime.now()
        
        logger.info("Phase 1: Testing corporate network connectivity")
        connectivity_ok = await self._test_corporate_connectivity()
        if not connectivity_ok:
            logger.warning("Corporate connectivity issues detected, proceeding with available resources")
        
        logger.info("Phase 2: Loading tokenizer with proxy support")
        tokenizer_success = self._initialize_tokenizer()
        if tokenizer_success:
            logger.info("Tokenizer loaded successfully")
        else:
            logger.warning("Tokenizer loading failed, using fallback")
        
        logger.info("Phase 3: Scanning public BigQuery datasets for training patterns")
        try:
            total_patterns = await self.scanner.scan_all_public_datasets()
        except Exception as e:
            logger.error(f"Dataset scanning failed: {e}")
            total_patterns = 0
        
        if total_patterns == 0:
            logger.warning("No training patterns collected, generating synthetic data")
            training_data = self._generate_synthetic_training_data()
        else:
            logger.info(f"Phase 4: Retrieved {total_patterns} training patterns")
            training_data = self.scanner.get_training_data()
        
        if not training_data:
            logger.error("No usable training data available")
            return False
        
        logger.info(f"Phase 5: Training neural model on {len(training_data)} samples")
        try:
            self.learner.train_on_dataset(
                training_data,
                epochs=self.training_config['initial_training_epochs'],
                batch_size=self.training_config['batch_size']
            )
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
        
        logger.info("Phase 6: Evaluating model performance")
        test_split = max(1, len(training_data) // 5)
        train_data = training_data[:-test_split]
        test_data = training_data[-test_split:]
        
        try:
            evaluation_results = self.learner.evaluate_on_test_data(test_data)
            
            self.training_stats['model_accuracy'] = evaluation_results['overall_accuracy']
            self.training_stats['samples_processed'] = len(training_data)
            self.training_stats['last_training_update'] = datetime.now()
            
            self.performance_metrics.update(evaluation_results.get('field_type_accuracies', {}))
        except Exception as e:
            logger.warning(f"Evaluation failed: {e}")
            self.training_stats['model_accuracy'] = 0.5
        
        logger.info("Phase 7: Saving trained model")
        try:
            self.learner.save_model(str(self.model_save_path))
        except Exception as e:
            logger.warning(f"Model save failed: {e}")
        
        training_time = (datetime.now() - start_time).total_seconds()
        self.training_stats['total_training_time'] = training_time
        
        logger.info(f"Initial training completed in {training_time:.2f} seconds")
        logger.info(f"Model accuracy: {self.training_stats['model_accuracy']:.4f}")
        logger.info(f"Proxy method: {self.training_stats['proxy_method']}")
        logger.info(f"Tokenizer method: {self.training_stats['tokenizer_method']}")
        
        return True
    
    async def _test_corporate_connectivity(self):
        test_urls = [
            'https://httpbin.org/get',
            'https://api.github.com',
            'https://huggingface.co',
            'https://pypi.org'
        ]
        
        session = self.proxy_manager.get_session()
        working_urls = 0
        
        for url in test_urls:
            try:
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    working_urls += 1
            except:
                continue
        
        connectivity_ratio = working_urls / len(test_urls)
        logger.info(f"Corporate connectivity: {working_urls}/{len(test_urls)} URLs accessible")
        
        return connectivity_ratio > 0.5
    
    def _initialize_tokenizer(self):
        try:
            tokenizer = load_corporate_tokenizer()
            if tokenizer:
                method_used = getattr(tokenizer, 'method_used', 'unknown')
                self.training_stats['tokenizer_method'] = method_used
                logger.info(f"Tokenizer initialized: {method_used}")
                return True
            else:
                self.training_stats['tokenizer_method'] = 'all_methods_failed'
                logger.error("All tokenizer loading methods failed")
                return False
        except Exception as e:
            logger.error(f"Tokenizer initialization failed: {e}")
            self.training_stats['tokenizer_method'] = f'exception_{type(e).__name__}'
            return False
    
    def _generate_synthetic_training_data(self):
        logger.info("Generating synthetic training data for offline training")
        
        synthetic_data = []
        
        hostname_examples = [
            (['server01', 'web-prod-001', 'db-cluster-node-1'], 'hostname'),
            (['host123', 'workstation-dev', 'app-server-02'], 'hostname'),
            (['srv001', 'web001', 'db001'], 'hostname'),
            (['computer-name', 'machine-id', 'device-001'], 'hostname')
        ]
        
        ip_examples = [
            (['192.168.1.1', '10.0.0.1', '172.16.0.1'], 'ip_address'),
            (['192.168.1.100', '10.1.1.1', '172.17.0.1'], 'ip_address'),
            (['10.0.0.254', '192.168.0.1', '172.16.1.1'], 'ip_address')
        ]
        
        email_examples = [
            (['user@example.com', 'admin@company.org', 'test@domain.net'], 'email_address'),
            (['john.doe@corp.com', 'jane.smith@org.net'], 'email_address')
        ]
        
        id_examples = [
            (['12345', '67890', 'abc123'], 'identifier'),
            (['uuid-123-456', 'id-789', 'key-abc'], 'identifier')
        ]
        
        all_examples = hostname_examples + ip_examples + email_examples + id_examples
        
        for samples, field_type in all_examples:
            for i in range(10):
                column_variations = [
                    f'{field_type}', f'{field_type}_name', f'{field_type}_id',
                    f'src_{field_type}', f'dest_{field_type}', f'primary_{field_type}'
                ]
                
                for column_name in column_variations:
                    synthetic_data.append({
                        'column_name': column_name,
                        'data_samples': samples,
                        'field_type': field_type,
                        'context_columns': ['table_id', 'created_at', 'updated_at'],
                        'confidence': 0.9,
                        'synthetic': True
                    })
        
        logger.info(f"Generated {len(synthetic_data)} synthetic training samples")
        return synthetic_data
    
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
        
        logger.info("Continuous learning system activated with proxy support")
    
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
            else:
                logger.info("No new training data available for update")
        
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
            else:
                logger.warning("No test data available for evaluation")
        
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
        
        try:
            self.learner.continual_learning_update(enriched_examples)
            
            self.training_stats['samples_processed'] += len(enriched_examples)
            self.training_stats['last_training_update'] = datetime.now()
            
            logger.info("User data training completed")
        except Exception as e:
            logger.error(f"User data training failed: {e}")
    
    def get_intelligent_field_prediction(self, column_name: str, data_samples: List[str], 
                                       context_columns: List[str] = None) -> Dict[str, Any]:
        
        start_time = time.time()
        
        try:
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
                'samples_analyzed': len(data_samples),
                'proxy_enabled': self.training_config['proxy_enabled'],
                'tokenizer_method': self.training_stats['tokenizer_method']
            }
        except Exception as e:
            logger.error(f"Field prediction failed: {e}")
            return {
                'predicted_field_type': 'unknown',
                'confidence_score': 0.0,
                'inference_time_ms': (time.time() - start_time) * 1000,
                'error': str(e)
            }
    
    def _analyze_data_patterns(self, data_samples: List[str]) -> Dict[str, Any]:
        if not data_samples:
            return {'pattern_count': 0, 'consistency': 0.0}
        
        try:
            patterns = {
                'numeric_count': sum(1 for s in data_samples if str(s).replace('.', '').isdigit()),
                'alpha_count': sum(1 for s in data_samples if str(s).isalpha()),
                'alphanumeric_count': sum(1 for s in data_samples if str(s).replace('-', '').replace('_', '').isalnum()),
                'contains_dots': sum(1 for s in data_samples if '.' in str(s)),
                'contains_dashes': sum(1 for s in data_samples if '-' in str(s)),
                'avg_length': sum(len(str(s)) for s in data_samples) / len(data_samples) if data_samples else 0,
                'unique_count': len(set(str(s) for s in data_samples))
            }
            
            consistency = patterns['unique_count'] / len(data_samples) if data_samples else 0.0
            
            return {
                'patterns': patterns,
                'consistency': consistency,
                'sample_size': len(data_samples)
            }
        except Exception as e:
            logger.warning(f"Pattern analysis failed: {e}")
            return {'error': str(e)}
    
    def _analyze_context_relevance(self, column_name: str, context_columns: List[str]) -> Dict[str, Any]:
        try:
            column_lower = column_name.lower()
            context_lower = [col.lower() for col in context_columns]
            
            relevance_indicators = {
                'network_context': any(term in ' '.join(context_lower) for term in ['ip', 'mac', 'network', 'subnet']),
                'identity_context': any(term in ' '.join(context_lower) for term in ['user', 'account', 'identity', 'person']),
                'infrastructure_context': any(term in ' '.join(context_lower) for term in ['server', 'host', 'machine', 'device']),
                'temporal_context': any(term in ' '.join(context_lower) for term in ['date', 'time', 'created', 'updated']),
                'geographic_context': any(term in ' '.join(context_lower) for term in ['location', 'region', 'country', 'zone'])
            }
            
            context_strength = sum(relevance_indicators.values()) / len(relevance_indicators) if relevance_indicators else 0
            
            return {
                'relevance_indicators': relevance_indicators,
                'context_strength': context_strength,
                'context_column_count': len(context_columns)
            }
        except Exception as e:
            logger.warning(f"Context analysis failed: {e}")
            return {'error': str(e)}
    
    def provide_learning_feedback(self, column_name: str, data_samples: List[str], 
                                correct_field_type: str, context_columns: List[str] = None):
        
        try:
            self.inference_engine.learn_from_feedback(
                column_name, data_samples, correct_field_type, context_columns
            )
            
            logger.info(f"Learning feedback provided: {column_name} -> {correct_field_type}")
        except Exception as e:
            logger.error(f"Learning feedback failed: {e}")
    
    def get_training_statistics(self) -> Dict[str, Any]:
        return {
            'training_stats': self.training_stats.copy(),
            'performance_metrics': self.performance_metrics.copy(),
            'model_info': {
                'parameters': sum(p.numel() for p in self.model.parameters()),
                'device': str(self.model.device),
                'model_size_mb': self.model_save_path.stat().st_size / (1024 * 1024) if self.model_save_path.exists() else 0
            },
            'continuous_learning_active': self.continuous_learning_active,
            'proxy_info': {
                'working_proxy': self.proxy_manager.working_proxy,
                'total_proxies_tested': len(self.proxy_manager.proxies)
            }
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
        successful_predictions = 0
        
        for _ in range(num_samples // len(test_cases)):
            for field_type, samples in test_cases:
                start_time = time.time()
                
                try:
                    self.inference_engine.analyze_column(f"test_{field_type}", samples)
                    successful_predictions += 1
                except Exception as e:
                    logger.debug(f"Benchmark prediction failed: {e}")
                
                total_time += time.time() - start_time
        
        avg_time_per_prediction = (total_time / successful_predictions) * 1000 if successful_predictions > 0 else 0
        predictions_per_second = 1000 / avg_time_per_prediction if avg_time_per_prediction > 0 else 0
        
        return {
            'avg_prediction_time_ms': avg_time_per_prediction,
            'predictions_per_second': predictions_per_second,
            'total_benchmark_time_s': total_time,
            'samples_tested': num_samples,
            'successful_predictions': successful_predictions,
            'success_rate': successful_predictions / num_samples if num_samples > 0 else 0
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
        
        try:
            prediction_result = self.orchestrator.get_intelligent_field_prediction(
                name, values, context_columns
            )
            
            field_type = prediction_result['predicted_field_type']
            confidence = prediction_result['confidence_score']
            
            analysis_metadata = {
                'method': 'neural_field_classifier_with_proxy',
                'inference_time_ms': prediction_result['inference_time_ms'],
                'pattern_analysis': prediction_result.get('pattern_analysis', {}),
                'context_analysis': prediction_result.get('context_analysis', {}),
                'model_enhanced': True,
                'proxy_enabled': prediction_result.get('proxy_enabled', False),
                'tokenizer_method': prediction_result.get('tokenizer_method', 'unknown')
            }
            
            result = (field_type, confidence, analysis_metadata)
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.warning(f"ML analysis failed: {e}")
            return None
    
    def analyze_column(self, name: str, values: List[str], context: Dict = None):
        return self.analyze_column_quantum_intelligently(name, values, context)