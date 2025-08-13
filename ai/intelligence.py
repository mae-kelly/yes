# ai/intelligence.py

import numpy as np
import asyncio
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import statistics
import logging
from .neural import AdvancedSemanticEmbedder, AdvancedPatternRecognizer
from .content import AdvancedContentAnalyzer, EnhancedValidationEngine
from core.types import Intelligence, FieldMapping, Discovery
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import joblib

logger = logging.getLogger(__name__)

class EnhancedIntelligenceEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.embedder = AdvancedSemanticEmbedder()
        self.recognizer = AdvancedPatternRecognizer()
        self.analyzer = AdvancedContentAnalyzer()
        self.validator = EnhancedValidationEngine()
        self.intelligence = Intelligence()
        
        self.ml_classifier = self._initialize_ml_classifier()
        self.ensemble_weights = {
            'semantic': 0.3,
            'pattern': 0.25,
            'content': 0.25,
            'validation': 0.2
        }
        
        self.learning_enabled = config.get('enable_machine_learning', True)
        self.deep_analysis_enabled = config.get('enable_deep_analysis', True)
        self.prediction_cache = {}
        self.classification_history = []
        
    def _initialize_ml_classifier(self):
        try:
            return MLPClassifier(
                hidden_layer_sizes=(256, 128, 64),
                activation='relu',
                solver='adam',
                alpha=0.001,
                batch_size='auto',
                learning_rate='adaptive',
                max_iter=1000,
                random_state=42
            )
        except:
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
    
    async def analyze_table_comprehensively(self, table_name: str, column_names: List[str], 
                                          sample_data: Dict[str, List[str]], 
                                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        
        table_analysis = self.embedder.analyze_table_semantically(table_name, column_names, sample_data)
        
        field_classifications = {}
        hostname_candidates = []
        
        for col_name, samples in sample_data.items():
            if len(samples) < 2:
                continue
            
            classification = await self._classify_field_with_ensemble(
                col_name, samples, table_analysis, context
            )
            
            if classification and classification['confidence'] > 0.4:
                field_classifications[col_name] = classification
                
                if classification['field_type'] == 'hostname' and classification['confidence'] > 0.7:
                    hostname_candidates.append({
                        'column': col_name,
                        'confidence': classification['confidence'],
                        'samples': samples[:10]
                    })
        
        best_hostname_column = self._select_best_hostname_column(hostname_candidates)
        
        return {
            'table_analysis': table_analysis,
            'field_classifications': field_classifications,
            'hostname_column': best_hostname_column,
            'confidence_score': self._calculate_overall_confidence(field_classifications),
            'processing_strategy': self._determine_processing_strategy(table_analysis, field_classifications)
        }
    
    async def _classify_field_with_ensemble(self, column_name: str, samples: List[str],
                                          table_context: Dict[str, Any], 
                                          global_context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        
        semantic_result = await self._semantic_classification(column_name, samples, table_context)
        pattern_result = self._pattern_classification(column_name, samples)
        content_result = self._content_classification(column_name, samples, global_context)
        validation_result = self._validation_classification(column_name, samples, global_context)
        
        if self.deep_analysis_enabled:
            ml_result = self._ml_classification(column_name, samples, table_context)
            ensemble_result = self._ensemble_classification([
                semantic_result, pattern_result, content_result, validation_result, ml_result
            ])
        else:
            ensemble_result = self._ensemble_classification([
                semantic_result, pattern_result, content_result, validation_result
            ])
        
        if ensemble_result and ensemble_result['confidence'] > 0.5:
            self._record_classification(column_name, samples, ensemble_result)
        
        return ensemble_result
    
    async def _semantic_classification(self, column_name: str, samples: List[str], 
                                     table_context: Dict[str, Any]) -> Dict[str, Any]:
        
        column_classification = table_context.get('column_classifications', {}).get(column_name)
        
        if column_classification:
            return {
                'field_type': column_classification['field_type'],
                'confidence': column_classification['confidence'],
                'method': 'semantic_embedder',
                'features': column_classification.get('features', {})
            }
        
        hostname_prob = self._calculate_advanced_hostname_probability(column_name, samples, table_context)
        
        if hostname_prob > 0.6:
            return {
                'field_type': 'hostname',
                'confidence': hostname_prob,
                'method': 'semantic_analysis',
                'reasoning': self._generate_hostname_reasoning(column_name, samples)
            }
        
        return {'field_type': 'unknown', 'confidence': 0.0, 'method': 'semantic_fallback'}
    
    def _pattern_classification(self, column_name: str, samples: List[str]) -> Dict[str, Any]:
        pattern_result = self.recognizer.predict_classification(column_name, samples)
        
        if pattern_result.get('pattern_based'):
            return pattern_result
        
        basic_patterns = self._apply_basic_pattern_matching(column_name, samples)
        return basic_patterns
    
    def _content_classification(self, column_name: str, samples: List[str], 
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
        
        content_result = self.analyzer.analyze_column_intelligent(column_name, samples, context)
        
        if content_result:
            field_type, confidence, metadata = content_result
            return {
                'field_type': field_type,
                'confidence': confidence,
                'method': 'content_analyzer',
                'metadata': metadata
            }
        
        return {'field_type': 'unknown', 'confidence': 0.0, 'method': 'content_fallback'}
    
    def _validation_classification(self, column_name: str, samples: List[str], 
                                 context: Dict[str, Any] = None) -> Dict[str, Any]:
        
        field_types_to_validate = ['hostname', 'ip_address', 'fqdn', 'mac_address']
        best_validation = {'field_type': 'unknown', 'confidence': 0.0}
        
        for field_type in field_types_to_validate:
            validation_result = self.validator.validate_field_advanced(field_type, samples, context)
            
            if validation_result['confidence'] > best_validation['confidence']:
                best_validation = {
                    'field_type': field_type,
                    'confidence': validation_result['confidence'],
                    'method': 'validation_engine',
                    'validation_details': validation_result
                }
        
        return best_validation
    
    def _ml_classification(self, column_name: str, samples: List[str], 
                         table_context: Dict[str, Any]) -> Dict[str, Any]:
        
        try:
            features = self._extract_ml_features(column_name, samples, table_context)
            
            if hasattr(self.ml_classifier, 'predict_proba') and len(self.classification_history) > 10:
                probabilities = self.ml_classifier.predict_proba([features])[0]
                best_class_idx = np.argmax(probabilities)
                confidence = probabilities[best_class_idx]
                
                field_types = ['hostname', 'ip_address', 'fqdn', 'mac_address', 'infrastructure_type']
                if best_class_idx < len(field_types):
                    return {
                        'field_type': field_types[best_class_idx],
                        'confidence': confidence,
                        'method': 'ml_classifier',
                        'ml_confidence': confidence
                    }
            
            return {'field_type': 'unknown', 'confidence': 0.0, 'method': 'ml_not_ready'}
            
        except Exception as e:
            logger.debug(f"ML classification failed: {e}")
            return {'field_type': 'unknown', 'confidence': 0.0, 'method': 'ml_error'}
    
    def _ensemble_classification(self, classification_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        field_scores = {}
        total_weight = 0
        
        methods_used = []
        
        for i, result in enumerate(classification_results):
            if not result or result['confidence'] < 0.1:
                continue
            
            method = result.get('method', f'method_{i}')
            methods_used.append(method)
            
            weight = self._get_method_weight(method)
            field_type = result['field_type']
            confidence = result['confidence']
            
            if field_type not in field_scores:
                field_scores[field_type] = 0
            
            field_scores[field_type] += confidence * weight
            total_weight += weight
        
        if not field_scores or total_weight == 0:
            return {'field_type': 'unknown', 'confidence': 0.0}
        
        for field_type in field_scores:
            field_scores[field_type] = field_scores[field_type] / total_weight
        
        best_field = max(field_scores.items(), key=lambda x: x[1])
        
        consensus_bonus = self._calculate_consensus_bonus(classification_results, best_field[0])
        final_confidence = min(1.0, best_field[1] + consensus_bonus)
        
        return {
            'field_type': best_field[0],
            'confidence': final_confidence,
            'method': 'ensemble',
            'component_methods': methods_used,
            'score_breakdown': field_scores,
            'consensus_bonus': consensus_bonus
        }
    
    def _get_method_weight(self, method: str) -> float:
        method_weights = {
            'semantic_embedder': self.ensemble_weights['semantic'],
            'semantic_analysis': self.ensemble_weights['semantic'],
            'pattern_classifier': self.ensemble_weights['pattern'],
            'content_analyzer': self.ensemble_weights['content'],
            'validation_engine': self.ensemble_weights['validation'],
            'ml_classifier': 0.4 if self.deep_analysis_enabled else 0.0
        }
        
        return method_weights.get(method, 0.1)
    
    def _calculate_consensus_bonus(self, results: List[Dict[str, Any]], winning_field: str) -> float:
        agreement_count = sum(1 for r in results if r.get('field_type') == winning_field and r.get('confidence', 0) > 0.3)
        total_methods = len([r for r in results if r.get('confidence', 0) > 0.1])
        
        if total_methods < 2:
            return 0.0
        
        consensus_ratio = agreement_count / total_methods
        return min(0.2, consensus_ratio * 0.15)
    
    def _calculate_advanced_hostname_probability(self, column_name: str, samples: List[str], 
                                               table_context: Dict[str, Any]) -> float:
        
        name_indicators = self._analyze_column_name_semantics(column_name)
        content_analysis = self._analyze_content_semantics(samples)
        context_relevance = self._calculate_table_context_relevance(table_context)
        
        base_probability = (
            name_indicators * 0.4 +
            content_analysis * 0.45 +
            context_relevance * 0.15
        )
        
        quality_multiplier = self._calculate_data_quality_multiplier(samples)
        
        return min(1.0, base_probability * quality_multiplier)
    
    def _analyze_column_name_semantics(self, column_name: str) -> float:
        name_lower = column_name.lower()
        
        exact_matches = ['hostname', 'host', 'computername', 'computer_name', 'machine_name', 
                        'device_name', 'endpoint_name', 'server_name', 'node_name']
        
        for match in exact_matches:
            if match == name_lower or match.replace('_', '') == name_lower.replace('_', ''):
                return 1.0
        
        partial_matches = ['host', 'computer', 'machine', 'device', 'endpoint', 'server', 'node']
        partial_score = 0.0
        
        for match in partial_matches:
            if match in name_lower:
                partial_score = max(partial_score, len(match) / len(name_lower))
        
        return partial_score
    
    def _analyze_content_semantics(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        semantic_scores = []
        
        for sample in samples[:30]:
            score = self._score_hostname_semantics(str(sample))
            semantic_scores.append(score)
        
        return statistics.mean(semantic_scores) if semantic_scores else 0.0
    
    def _score_hostname_semantics(self, value: str) -> float:
        if not value or len(value) < 2:
            return 0.0
        
        value_clean = value.strip().upper()
        if value_clean in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
            return 0.0
        
        score = 0.0
        
        if 2 <= len(value) <= 253:
            score += 0.3
        
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', value, re.IGNORECASE):
            score += 0.4
        elif re.match(r'^[a-zA-Z0-9]+$', value, re.IGNORECASE):
            score += 0.3
        
        hostname_indicators = ['srv', 'web', 'app', 'db', 'sql', 'ad', 'dc', 'dns', 'dhcp',
                              'server', 'host', 'node', 'vm', 'pc', 'ws', 'desktop']
        
        value_lower = value.lower()
        indicator_matches = sum(1 for indicator in hostname_indicators if indicator in value_lower)
        score += min(0.3, indicator_matches * 0.1)
        
        return min(1.0, score)
    
    def _calculate_table_context_relevance(self, table_context: Dict[str, Any]) -> float:
        relevance = 0.5
        
        table_analysis = table_context.get('table_context', {})
        
        if table_analysis.get('is_endpoint'):
            relevance += 0.3
        if table_analysis.get('is_asset'):
            relevance += 0.2
        if table_analysis.get('data_source') == 'cmdb':
            relevance += 0.15
        if table_analysis.get('is_inventory'):
            relevance += 0.1
        
        return min(1.0, relevance)
    
    def _calculate_data_quality_multiplier(self, samples: List[str]) -> float:
        if not samples:
            return 0.5
        
        quality_factors = []
        
        non_empty = [s for s in samples if s and str(s).strip()]
        completeness = len(non_empty) / len(samples)
        quality_factors.append(completeness)
        
        if non_empty:
            uniqueness = len(set(non_empty)) / len(non_empty)
            quality_factors.append(uniqueness)
            
            avg_length = statistics.mean([len(str(s)) for s in non_empty])
            length_score = 1.0 if 3 <= avg_length <= 100 else 0.7
            quality_factors.append(length_score)
        
        return statistics.mean(quality_factors) if quality_factors else 0.5
    
    def _select_best_hostname_column(self, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not candidates:
            return None
        
        scored_candidates = []
        
        for candidate in candidates:
            score = candidate['confidence']
            
            col_name = candidate['column'].lower()
            if 'hostname' in col_name or col_name == 'host':
                score += 0.1
            
            samples = candidate['samples']
            if samples:
                avg_quality = statistics.mean([
                    self._score_hostname_semantics(str(s)) for s in samples
                ])
                score += avg_quality * 0.1
            
            scored_candidates.append((candidate, score))
        
        best_candidate = max(scored_candidates, key=lambda x: x[1])
        return best_candidate[0]
    
    def _apply_basic_pattern_matching(self, column_name: str, samples: List[str]) -> Dict[str, Any]:
        field_patterns = {
            'hostname': [r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', r'^[a-zA-Z0-9]+$'],
            'ip_address': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
            'fqdn': [r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$'],
            'mac_address': [r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$']
        }
        
        best_match = {'field_type': 'unknown', 'confidence': 0.0}
        
        for field_type, patterns in field_patterns.items():
            matches = 0
            for sample in samples[:20]:
                for pattern in patterns:
                    if re.match(pattern, str(sample), re.IGNORECASE):
                        matches += 1
                        break
            
            confidence = matches / min(len(samples), 20) if samples else 0.0
            
            if confidence > best_match['confidence']:
                best_match = {
                    'field_type': field_type,
                    'confidence': confidence,
                    'method': 'basic_pattern_matching',
                    'pattern_matches': matches,
                    'sample_size': min(len(samples), 20)
                }
        
        return best_match
    
    def _extract_ml_features(self, column_name: str, samples: List[str], 
                           table_context: Dict[str, Any]) -> List[float]:
        features = []
        
        features.extend([
            len(column_name),
            column_name.lower().count('_'),
            column_name.lower().count('.'),
            int('host' in column_name.lower()),
            int('name' in column_name.lower()),
            int('id' in column_name.lower())
        ])
        
        if samples:
            sample_subset = samples[:10]
            features.extend([
                len(sample_subset),
                statistics.mean([len(str(s)) for s in sample_subset]),
                len(set(sample_subset)) / len(sample_subset),
                sum(1 for s in sample_subset if re.search(r'\d', str(s))) / len(sample_subset),
                sum(1 for s in sample_subset if re.search(r'[-_.]', str(s))) / len(sample_subset)
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        table_analysis = table_context.get('table_context', {})
        features.extend([
            int(table_analysis.get('is_endpoint', False)),
            int(table_analysis.get('is_asset', False)),
            int(table_analysis.get('data_source') == 'cmdb')
        ])
        
        return features
    
    def _record_classification(self, column_name: str, samples: List[str], result: Dict[str, Any]):
        self.classification_history.append({
            'column_name': column_name,
            'sample_count': len(samples),
            'field_type': result['field_type'],
            'confidence': result['confidence'],
            'method': result['method'],
            'timestamp': datetime.now()
        })
        
        if len(self.classification_history) > 1000:
            self.classification_history = self.classification_history[-1000:]
        
        if self.learning_enabled and len(self.classification_history) > 50:
            self._update_ml_model()
    
    def _update_ml_model(self):
        try:
            if len(self.classification_history) < 20:
                return
            
            X = []
            y = []
            
            for record in self.classification_history[-100:]:
                features = [
                    len(record['column_name']),
                    record['column_name'].lower().count('_'),
                    int('host' in record['column_name'].lower()),
                    int('name' in record['column_name'].lower()),
                    record['sample_count'],
                    record['confidence']
                ]
                
                field_type_mapping = {
                    'hostname': 0, 'ip_address': 1, 'fqdn': 2, 
                    'mac_address': 3, 'infrastructure_type': 4
                }
                
                label = field_type_mapping.get(record['field_type'], 5)
                
                X.append(features)
                y.append(label)
            
            if len(set(y)) > 1:
                self.ml_classifier.fit(X, y)
                
        except Exception as e:
            logger.debug(f"ML model update failed: {e}")
    
    def _generate_hostname_reasoning(self, column_name: str, samples: List[str]) -> List[str]:
        reasoning = []
        
        name_lower = column_name.lower()
        if any(indicator in name_lower for indicator in ['hostname', 'host', 'computer', 'machine']):
            reasoning.append(f"Column name '{column_name}' contains hostname indicators")
        
        if samples:
            pattern_matches = sum(1 for s in samples[:10] 
                                if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', str(s), re.IGNORECASE))
            if pattern_matches > len(samples[:10]) * 0.7:
                reasoning.append(f"{pattern_matches}/{len(samples[:10])} samples match hostname patterns")
        
        return reasoning
    
    def _determine_processing_strategy(self, table_analysis: Dict[str, Any], 
                                     field_classifications: Dict[str, Any]) -> Dict[str, str]:
        
        has_hostname = any(f.get('field_type') == 'hostname' for f in field_classifications.values())
        confidence_avg = statistics.mean([f.get('confidence', 0) for f in field_classifications.values()]) if field_classifications else 0
        
        if has_hostname and confidence_avg > 0.8:
            return {'strategy': 'direct_extraction', 'reason': 'high_confidence_hostname_detected'}
        elif has_hostname and confidence_avg > 0.6:
            return {'strategy': 'careful_extraction', 'reason': 'medium_confidence_hostname_detected'}
        elif confidence_avg > 0.5:
            return {'strategy': 'exploratory_analysis', 'reason': 'some_fields_identified'}
        else:
            return {'strategy': 'deep_content_scan', 'reason': 'low_confidence_classifications'}
    
    def _calculate_overall_confidence(self, field_classifications: Dict[str, Any]) -> float:
        if not field_classifications:
            return 0.0
        
        confidences = [f.get('confidence', 0) for f in field_classifications.values()]
        hostname_bonus = 0.1 if any(f.get('field_type') == 'hostname' for f in field_classifications.values()) else 0
        
        return min(1.0, statistics.mean(confidences) + hostname_bonus)
    
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
        base_multipliers = {'small': 500, 'medium': 2500, 'large': 12000, 'enterprise': 50000}
        
        scale = self._determine_scale(datasets, tables)
        base_count = base_multipliers[scale]
        
        multiplier = 1.0
        if context.get('has_security_data', False):
            multiplier *= 1.8
        if context.get('has_log_data', False):
            multiplier *= 1.5
        if context.get('cloud_native', False):
            multiplier *= 1.3
        
        return int(base_count * multiplier * max(1, datasets / 10))
    
    def _predict_processing_time(self, datasets: int, tables: int, context: Dict[str, Any]) -> float:
        base_time = 180
        dataset_time = datasets * 12
        table_time = tables * 1.2
        
        total_time = base_time + dataset_time + table_time
        
        workers = context.get('parallel_workers', 16)
        parallelism_factor = min(1.0, workers / 32)
        
        return max(90, total_time * (1 - parallelism_factor * 0.7))
    
    def _predict_success_rate(self, context: Dict[str, Any]) -> float:
        base_rate = 0.8
        
        factors = {
            'auth_available': 0.15,
            'permissions_granted': 0.1,
            'network_stable': 0.05
        }
        
        for factor, boost in factors.items():
            if context.get(factor, False):
                base_rate += boost
        
        return min(0.95, max(0.4, base_rate))
    
    def _determine_scale(self, datasets: int, tables: int) -> str:
        complexity = datasets + (tables / 20)
        
        if complexity < 20:
            return 'small'
        elif complexity < 100:
            return 'medium'
        elif complexity < 400:
            return 'large'
        else:
            return 'enterprise'
    
    def _calculate_confidence_intervals(self, context: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        uncertainty = max(0.1, min(0.3, 1.0 / max(context.get('dataset_count', 1), 1)))
        
        return {
            'asset_count': {'lower': 0.8, 'upper': 1.6},
            'processing_time': {'lower': 0.7, 'upper': 1.9},
            'success_rate': {'lower': 1.0 - uncertainty, 'upper': 1.0}
        }
    
    async def recommend_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        predictions = await self.predict_discovery_outcomes(context)
        
        estimated_assets = predictions['estimated_assets']
        processing_time = predictions['processing_time_seconds']
        
        if estimated_assets > 75000:
            strategy = 'enterprise_parallel'
            params = {
                'batch_size': 5000,
                'parallel_workers': 64,
                'timeout_seconds': 1200,
                'memory_limit_mb': 8192
            }
        elif estimated_assets > 15000:
            strategy = 'large_scale'
            params = {
                'batch_size': 2500,
                'parallel_workers': 32,
                'timeout_seconds': 900,
                'memory_limit_mb': 4096
            }
        elif processing_time > 2400:
            strategy = 'long_running'
            params = {
                'batch_size': 1500,
                'parallel_workers': 24,
                'timeout_seconds': 600,
                'checkpoint_interval': 450
            }
        else:
            strategy = 'standard'
            params = {
                'batch_size': 1000,
                'parallel_workers': 16,
                'timeout_seconds': 450
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
        
        learning_results['patterns_learned'] = len(self.recognizer.pattern_memory)
        learning_results['classifications_performed'] = len(self.classification_history)
        
        return learning_results
    
    async def analyze_field_intelligently(self, column_name: str, samples: List[str], 
                                        context: Dict[str, Any] = None) -> Optional[FieldMapping]:
        
        classification = await self._classify_field_with_ensemble(
            column_name, samples, {}, context
        )
        
        if not classification or classification['confidence'] < 0.4:
            return None
        
        mapping = FieldMapping(
            field_type=classification['field_type'],
            column=column_name,
            confidence=classification['confidence'],
            samples=samples[:10]
        )
        
        if self.learning_enabled:
            self.recognizer.learn_from_classification(
                column_name, samples, classification, classification['confidence'] > 0.7
            )
        
        return mapping