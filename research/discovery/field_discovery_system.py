import time
import logging
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
from datetime import datetime

from models import EnhancedMatch
from core.circuit_breaker import CircuitBreaker
from core.cache_manager import CacheManager
from semantic.enhanced_semantic_engine import EnhancedSemanticEngine
from prioritization.table_prioritizer import EnhancedTablePrioritizer

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False

logger = logging.getLogger(__name__)

class EnhancedFieldDiscoverySystem:
    def __init__(self, 
                 service_account_file: str = None,
                 auth_project_id: str = None,
                 target_project_id: str = None,
                 redis_host: str = "localhost",
                 redis_port: int = 6379):
        
        self.client = None
        self.target_project_id = target_project_id or "prj-fisv-p-gcss-sas-dl9dd0f1df"
        
        if BIGQUERY_AVAILABLE and service_account_file and auth_project_id:
            try:
                credentials = service_account.Credentials.from_service_account_file(service_account_file)
                self.client = bigquery.Client(project=auth_project_id, credentials=credentials)
                logger.info(f"BigQuery client initialized for auth project: {auth_project_id}")
                logger.info(f"Target project for discovery: {self.target_project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize BigQuery client: {e}")
        
        self.semantic_engine = EnhancedSemanticEngine()
        self.table_prioritizer = EnhancedTablePrioritizer()
        self.cache_manager = CacheManager(redis_host, redis_port)
        self.circuit_breaker = CircuitBreaker()
        
        self.performance_metrics = {
            'fields_processed': 0,
            'tables_analyzed': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'processing_time': 0.0
        }
    
    async def discover_fields(self, 
                            target_project: str = None,
                            max_datasets: int = 20,
                            max_tables_per_dataset: int = 10,
                            confidence_threshold: float = 0.3) -> Tuple[List[EnhancedMatch], Dict[str, Any]]:
        
        if not self.client:
            raise ValueError("BigQuery client not initialized")
        
        # Use provided target project or default
        project_to_scan = target_project or self.target_project_id
        
        start_time = time.time()
        
        try:
            datasets = await self._get_prioritized_datasets(project_to_scan, max_datasets)
            
            all_matches = []
            discovery_stats = {
                'datasets_processed': 0,
                'tables_processed': 0,
                'fields_analyzed': 0,
                'high_confidence_matches': 0,
                'requirement_coverage': Counter(),
                'confidence_distribution': Counter(),
                'processing_errors': []
            }
            
            for dataset in datasets:
                try:
                    dataset_matches = await self._process_dataset(
                        dataset, max_tables_per_dataset, confidence_threshold
                    )
                    
                    all_matches.extend(dataset_matches)
                    discovery_stats['datasets_processed'] += 1
                    
                    for match in dataset_matches:
                        discovery_stats['requirement_coverage'][match.requirement] += 1
                        if match.score >= 0.8:
                            discovery_stats['high_confidence_matches'] += 1
                        
                        if match.score >= 0.8:
                            discovery_stats['confidence_distribution']['HIGH'] += 1
                        elif match.score >= 0.5:
                            discovery_stats['confidence_distribution']['MEDIUM'] += 1
                        else:
                            discovery_stats['confidence_distribution']['LOW'] += 1
                    
                except Exception as e:
                    error_msg = f"Dataset {dataset.dataset_id} processing failed: {e}"
                    logger.error(error_msg)
                    discovery_stats['processing_errors'].append(error_msg)
                    continue
            
            all_matches.sort(key=lambda x: (x.score, x.semantic_depth), reverse=True)
            
            self.performance_metrics['processing_time'] = time.time() - start_time
            discovery_stats['performance_metrics'] = self.performance_metrics
            discovery_stats['cache_performance'] = self.cache_manager.get_stats()
            
            logger.info(f"Discovery complete: {len(all_matches)} matches found in {self.performance_metrics['processing_time']:.2f}s")
            
            return all_matches, discovery_stats
            
        except Exception as e:
            logger.error(f"Field discovery failed: {e}")
            raise
    
    async def _get_prioritized_datasets(self, project_id: str, max_count: int) -> List[Any]:
        cache_key = f"datasets_{project_id}_{max_count}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            self.performance_metrics['cache_hits'] += 1
            return cached_result
        
        try:
            all_datasets = list(self.client.list_datasets(project=project_id))
            self.performance_metrics['api_calls'] += 1
            
            neural_priorities = {
                'chronicle': 100, 'security': 90, 'asset': 85, 'log': 80, 'audit': 75,
                'infrastructure': 70, 'edr': 65, 'device': 60, 'host': 55, 'network': 50,
                'compliance': 45, 'monitoring': 40, 'splunk': 85, 'crowdstrike': 70,
                'tanium': 65, 'axonius': 60, 'production': 50, 'prod': 45
            }
            
            scored_datasets = []
            for dataset in all_datasets:
                dataset_lower = dataset.dataset_id.lower()
                
                base_score = sum(weight for keyword, weight in neural_priorities.items() 
                               if keyword in dataset_lower)
                
                keyword_density = sum(1 for keyword in neural_priorities if keyword in dataset_lower)
                if keyword_density >= 2:
                    base_score *= 1.5
                elif keyword_density >= 3:
                    base_score *= 2.0
                
                recency_bonus = 0
                for year in ['2024', '2023', '2025']:
                    if year in dataset.dataset_id:
                        recency_bonus += 20
                
                if any(term in dataset_lower for term in ['prod', 'production']):
                    base_score += 30
                elif any(term in dataset_lower for term in ['test', 'dev', 'sandbox']):
                    base_score *= 0.3
                
                final_score = base_score + recency_bonus
                scored_datasets.append((dataset, final_score))
            
            scored_datasets.sort(key=lambda x: x[1], reverse=True)
            selected_datasets = [d for d, s in scored_datasets[:max_count]]
            
            self.cache_manager.set(cache_key, selected_datasets, ttl=1800)
            
            return selected_datasets
            
        except Exception as e:
            logger.error(f"Failed to get datasets for project {project_id}: {e}")
            raise
    
    async def _process_dataset(self, 
                             dataset: Any, 
                             max_tables: int, 
                             confidence_threshold: float) -> List[EnhancedMatch]:
        
        dataset_id = dataset.dataset_id
        matches = []
        
        try:
            tables = self.circuit_breaker.call(list, self.client.list_tables(dataset.reference))
            self.performance_metrics['api_calls'] += 1
            
            if not tables:
                return matches
            
            prioritized_tables = self.table_prioritizer.prioritize_tables_mcda(
                tables, dataset_id, self.client
            )
            
            selected_tables = prioritized_tables[:max_tables]
            
            for table, table_score, table_scores in selected_tables:
                try:
                    table_matches = await self._analyze_table_fields(
                        table, dataset_id, table_score, table_scores, confidence_threshold
                    )
                    matches.extend(table_matches)
                    self.performance_metrics['tables_analyzed'] += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze table {table.table_id}: {e}")
                    continue
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset_id}: {e}")
            return matches
    
    async def _analyze_table_fields(self, 
                                  table: Any, 
                                  dataset_id: str, 
                                  table_score: float,
                                  table_scores: Dict[str, float],
                                  confidence_threshold: float) -> List[EnhancedMatch]:
        
        matches = []
        
        try:
            table_ref = self.circuit_breaker.call(self.client.get_table, table.reference)
            self.performance_metrics['api_calls'] += 1
            
            table_context = {
                'table_name': table_ref.table_id,
                'dataset_name': dataset_id,
                'full_path': f"{table_ref.project}.{dataset_id}.{table_ref.table_id}",
                'row_count': table_ref.num_rows or 0,
                'schema_complexity': len(table_ref.schema),
                'table_score': table_score,
                'table_scores': table_scores,
                'table_metrics': {
                    'size_bytes': table_ref.num_bytes or 0,
                    'created': table_ref.created,
                    'modified': table_ref.modified
                }
            }
            
            for field in table_ref.schema:
                self.performance_metrics['fields_processed'] += 1
                
                semantic_results = self.semantic_engine.analyze_field_semantics(
                    field.name, table_context
                )
                
                if not semantic_results:
                    continue
                
                best_concept = max(semantic_results.items(), key=lambda x: x[1]['score'])
                concept_name, analysis = best_concept
                
                if analysis['score'] < confidence_threshold:
                    continue
                
                match = EnhancedMatch(
                    field=field.name,
                    table=f"{dataset_id}.{table_ref.table_id}",
                    dataset=dataset_id,
                    requirement=self._map_concept_to_requirement(concept_name),
                    score=analysis['score'],
                    semantic_depth=analysis['semantic_depth'],
                    reasoning=analysis['reasoning'],
                    business_priority=analysis['business_priority'],
                    table_metrics=table_context['table_metrics']
                )
                
                match.calibrated_confidence = self._calibrate_confidence(match, analysis)
                
                matches.append(match)
        
        except Exception as e:
            logger.warning(f"Failed to analyze table {table.table_id}: {e}")
        
        return matches
    
    def _map_concept_to_requirement(self, concept_name: str) -> str:
        mapping = {
            'asset_identity': 'GLOBAL_ASSET_IDENTITY',
            'infrastructure_classification': 'INFRASTRUCTURE_TYPE',
            'geographic_context': 'REGIONAL_COUNTRY',
            'security_posture': 'SECURITY_COVERAGE',
            'logging_telemetry': 'LOGGING_COMPLIANCE',
            'business_context': 'BUSINESS_CONTEXT',
            'temporal_context': 'TEMPORAL_CONTEXT'
        }
        return mapping.get(concept_name, concept_name.upper())
    
    def _calibrate_confidence(self, match: EnhancedMatch, analysis: Dict[str, Any]) -> float:
        raw_confidence = analysis.get('confidence_raw', match.score)
        
        temperature = self.semantic_engine.confidence_calibrator['temperature_scaling']
        calibrated = raw_confidence / temperature
        
        calibrated = 1 / (1 + np.exp(-5 * (calibrated - 0.5)))
        
        return min(calibrated, 1.0)
    
    def generate_discovery_report(self, 
                                matches: List[EnhancedMatch], 
                                stats: Dict[str, Any]) -> Dict[str, Any]:
        
        matches_by_requirement = defaultdict(list)
        for match in matches:
            matches_by_requirement[match.requirement].append(match)
        
        total_matches = len(matches)
        high_confidence = len([m for m in matches if m.score >= 0.8])
        medium_confidence = len([m for m in matches if 0.5 <= m.score < 0.8])
        
        report = {
            'discovery_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_matches': total_matches,
                'high_confidence_matches': high_confidence,
                'medium_confidence_matches': medium_confidence,
                'requirements_covered': len(matches_by_requirement),
                'performance_metrics': self.performance_metrics,
                'cache_performance': self.cache_manager.get_stats()
            },
            'requirement_analysis': {},
            'top_discoveries': [],
            'implementation_roadmap': [],
            'quality_insights': {
                'confidence_distribution': dict(stats.get('confidence_distribution', {})),
                'semantic_depth_analysis': self._analyze_semantic_depth(matches),
                'table_coverage_analysis': self._analyze_table_coverage(matches),
                'data_quality_indicators': self._analyze_data_quality(matches)
            }
        }
        
        for req_code, req_matches in matches_by_requirement.items():
            req_matches.sort(key=lambda x: x.score, reverse=True)
            
            report['requirement_analysis'][req_code] = {
                'total_matches': len(req_matches),
                'top_candidates': [
                    {
                        'field': m.field,
                        'table': m.table,
                        'score': round(m.score, 4),
                        'calibrated_confidence': round(m.calibrated_confidence, 4),
                        'semantic_depth': m.semantic_depth,
                        'reasoning': m.reasoning[:3]
                    }
                    for m in req_matches[:10]
                ],
                'confidence_breakdown': {
                    'high': len([m for m in req_matches if m.score >= 0.8]),
                    'medium': len([m for m in req_matches if 0.5 <= m.score < 0.8]),
                    'low': len([m for m in req_matches if m.score < 0.5])
                },
                'implementation_readiness': self._assess_implementation_readiness(req_matches)
            }
        
        top_matches = sorted(matches, key=lambda x: x.score, reverse=True)[:20]
        report['top_discoveries'] = [
            {
                'rank': i + 1,
                'field': m.field,
                'table': m.table,
                'requirement': m.requirement,
                'score': round(m.score, 4),
                'semantic_depth': m.semantic_depth,
                'business_priority': m.business_priority,
                'key_reasons': m.reasoning[:2]
            }
            for i, m in enumerate(top_matches)
        ]
        
        return report
    
    def _analyze_semantic_depth(self, matches: List[EnhancedMatch]) -> Dict[str, Any]:
        depth_counts = Counter(m.semantic_depth for m in matches)
        total = len(matches)
        
        return {
            'distribution': dict(depth_counts),
            'average_depth': sum(m.semantic_depth for m in matches) / total if total > 0 else 0,
            'deep_semantic_matches': len([m for m in matches if m.semantic_depth >= 2])
        }
    
    def _analyze_table_coverage(self, matches: List[EnhancedMatch]) -> Dict[str, Any]:
        table_counts = Counter(m.table for m in matches)
        
        return {
            'unique_tables': len(table_counts),
            'max_matches_per_table': max(table_counts.values()) if table_counts else 0,
            'average_matches_per_table': sum(table_counts.values()) / len(table_counts) if table_counts else 0,
            'high_value_tables': [table for table, count in table_counts.most_common(10)]
        }
    
    def _analyze_data_quality(self, matches: List[EnhancedMatch]) -> Dict[str, Any]:
        return {
            'calibrated_vs_raw_confidence': {
                'average_raw': sum(m.score for m in matches) / len(matches) if matches else 0,
                'average_calibrated': sum(m.calibrated_confidence for m in matches) / len(matches) if matches else 0
            },
            'business_priority_distribution': dict(Counter(m.business_priority for m in matches)),
            'reasoning_complexity': {
                'average_reasons_per_match': sum(len(m.reasoning) for m in matches) / len(matches) if matches else 0,
                'most_common_reasoning_types': Counter(
                    reason.split(':')[0] for m in matches for reason in m.reasoning
                ).most_common(5)
            }
        }
    
    def _assess_implementation_readiness(self, matches: List[EnhancedMatch]) -> str:
        if not matches:
            return "NOT_READY"
        
        high_confidence_count = len([m for m in matches if m.score >= 0.8])
        medium_confidence_count = len([m for m in matches if 0.5 <= m.score < 0.8])
        
        if high_confidence_count >= 3:
            return "READY"
        elif high_confidence_count >= 1 or medium_confidence_count >= 5:
            return "PARTIALLY_READY"
        else:
            return "NEEDS_VALIDATION"