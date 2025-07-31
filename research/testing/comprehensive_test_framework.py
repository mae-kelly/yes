import time
import logging
from typing import Dict, Any
from collections import Counter

from models import EnhancedMatch
from discovery.field_discovery_system import EnhancedFieldDiscoverySystem
from analysis.data_pattern_analyzer import DataPatternAnalyzer
from integrations.enterprise_integration_manager import EnterpriseIntegrationManager

logger = logging.getLogger(__name__)

class ComprehensiveTestFramework:
    def __init__(self, discovery_system: EnhancedFieldDiscoverySystem):
        self.discovery_system = discovery_system
        self.test_results = {}
        self.benchmark_data = {}
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        test_suite = {
            'semantic_analysis_tests': await self._test_semantic_analysis(),
            'pattern_recognition_tests': await self._test_pattern_recognition(),
            'confidence_calibration_tests': await self._test_confidence_calibration(),
            'performance_tests': await self._test_performance(),
            'edge_case_tests': await self._test_edge_cases(),
            'integration_tests': await self._test_integrations()
        }
        
        test_scores = [result.get('score', 0.0) for result in test_suite.values()]
        overall_score = sum(test_scores) / len(test_scores) if test_scores else 0.0
        
        test_suite['overall_results'] = {
            'overall_score': overall_score,
            'tests_passed': sum(1 for result in test_suite.values() if result.get('status') == 'passed'),
            'total_tests': len(test_suite),
            'recommendation': 'PRODUCTION_READY' if overall_score >= 0.85 else 'NEEDS_IMPROVEMENT'
        }
        
        return test_suite
    
    async def _test_semantic_analysis(self) -> Dict[str, Any]:
        test_cases = [
            ('asset_hostname', 'GLOBAL_ASSET_IDENTITY', 0.8),
            ('device_serial_number', 'GLOBAL_ASSET_IDENTITY', 0.85),
            ('infrastructure_type', 'INFRASTRUCTURE_TYPE', 0.8),
            ('country_code', 'REGIONAL_COUNTRY', 0.75),
            ('security_agent_status', 'SECURITY_COVERAGE', 0.8),
            ('log_ingestion_timestamp', 'LOGGING_COMPLIANCE', 0.7),
            ('unrelated_field_xyz', None, 0.0)
        ]
        
        correct_predictions = 0
        total_predictions = len(test_cases)
        
        table_context = {
            'table_name': 'test_table',
            'dataset_name': 'test_dataset',
            'full_path': 'project.test_dataset.test_table',
            'row_count': 10000,
            'schema_complexity': 50
        }
        
        for field_name, expected_requirement, min_expected_score in test_cases:
            results = self.discovery_system.semantic_engine.analyze_field_semantics(field_name, table_context)
            
            if expected_requirement is None:
                if not results or max(r['score'] for r in results.values()) < 0.3:
                    correct_predictions += 1
            else:
                if results:
                    best_match = max(results.items(), key=lambda x: x[1]['score'])
                    predicted_req = self.discovery_system._map_concept_to_requirement(best_match[0])
                    
                    if predicted_req == expected_requirement and best_match[1]['score'] >= min_expected_score:
                        correct_predictions += 1
        
        accuracy = correct_predictions / total_predictions
        
        return {
            'status': 'passed' if accuracy >= 0.8 else 'failed',
            'score': accuracy,
            'correct_predictions': correct_predictions,
            'total_predictions': total_predictions,
            'accuracy_percent': accuracy * 100
        }
    
    async def _test_pattern_recognition(self) -> Dict[str, Any]:
        pattern_analyzer = DataPatternAnalyzer()
        
        test_patterns = [
            (['550e8400-e29b-41d4-a716-446655440000', '6ba7b810-9dad-11d1-80b4-00c04fd430c8'], 'uuid'),
            (['DESKTOP-ABC123', 'LAPTOP-XYZ789', 'SERVER-DEF456'], 'hostname'),
            (['192.168.1.1', '10.0.0.1', '172.16.0.1'], 'ip_address'),
            (['installed', 'enabled', 'active', 'disabled'], 'security_status'),
            (['aws', 'azure', 'gcp', 'onprem'], 'infrastructure_type')
        ]
        
        correct_detections = 0
        
        for values, expected_pattern in test_patterns:
            result = pattern_analyzer._detect_format_patterns(values)
            
            if expected_pattern in result.get('pattern_type', '') or result.get('confidence', 0) > 0.7:
                correct_detections += 1
        
        accuracy = correct_detections / len(test_patterns)
        
        return {
            'status': 'passed' if accuracy >= 0.7 else 'failed',
            'score': accuracy,
            'correct_detections': correct_detections,
            'total_patterns': len(test_patterns),
            'detection_accuracy_percent': accuracy * 100
        }
    
    async def _test_confidence_calibration(self) -> Dict[str, Any]:
        mock_matches = [
            EnhancedMatch(
                field=f"test_field_{i}", table="test.table", dataset="test",
                requirement="TEST_REQ", score=i/10.0, semantic_depth=2,
                reasoning=["test"], business_priority=5
            )
            for i in range(1, 11)
        ]
        
        calibration_errors = []
        for match in mock_matches:
            analysis = {'confidence_raw': match.score}
            calibrated = self.discovery_system._calibrate_confidence(match, analysis)
            
            if 0.0 <= calibrated <= 1.0 and abs(calibrated - match.score) >= 0.01:
                calibration_errors.append(abs(calibrated - match.score))
        
        avg_calibration_change = sum(calibration_errors) / len(calibration_errors) if calibration_errors else 0
        
        return {
            'status': 'passed' if 0.05 <= avg_calibration_change <= 0.3 else 'failed',
            'score': 1.0 if 0.05 <= avg_calibration_change <= 0.3 else 0.5,
            'average_calibration_change': avg_calibration_change,
            'calibrated_matches': len(calibration_errors),
            'total_matches': len(mock_matches)
        }
    
    async def _test_performance(self) -> Dict[str, Any]:
        start_time = time.time()
        
        semantic_start = time.time()
        for i in range(100):
            field_name = f"test_asset_hostname_{i}"
            table_context = {'table_name': 'perf_test', 'dataset_name': 'test'}
            self.discovery_system.semantic_engine.analyze_field_semantics(field_name, table_context)
        
        semantic_time = time.time() - semantic_start
        semantic_throughput = 100 / semantic_time
        
        pattern_start = time.time()
        for i in range(50):
            test_term = f"test_term_{i}"
            self.discovery_system.semantic_engine.generate_morphological_variants(test_term)
        
        pattern_time = time.time() - pattern_start
        
        total_time = time.time() - start_time
        
        semantic_threshold = 100
        total_time_threshold = 5.0
        
        performance_score = min(semantic_throughput / semantic_threshold, 1.0)
        
        return {
            'status': 'passed' if semantic_throughput >= semantic_threshold and total_time <= total_time_threshold else 'failed',
            'score': performance_score,
            'semantic_throughput_fps': round(semantic_throughput, 2),
            'pattern_generation_time': round(pattern_time, 3),
            'total_benchmark_time': round(total_time, 3),
            'performance_grade': 'EXCELLENT' if performance_score >= 0.9 else 'GOOD' if performance_score >= 0.7 else 'NEEDS_OPTIMIZATION'
        }
    
    async def _test_edge_cases(self) -> Dict[str, Any]:
        edge_cases = [
            ('', 'empty_field_name'),
            ('a', 'single_character'),
            ('field_with_very_long_name_that_exceeds_typical_database_limits_' + 'x' * 100, 'very_long_name'),
            ('field-with-special-chars!@#$%^&*()', 'special_characters'),
            ('FIELD_ALL_CAPS_WITH_NUMBERS_123_456', 'all_caps_with_numbers'),
            ('field.with.dots.and.periods', 'dots_and_periods'),
            ('🏢📊💼', 'unicode_emojis')
        ]
        
        handled_cases = 0
        
        for field_name, case_type in edge_cases:
            try:
                table_context = {'table_name': 'edge_test', 'dataset_name': 'test'}
                results = self.discovery_system.semantic_engine.analyze_field_semantics(field_name, table_context)
                
                if isinstance(results, dict):
                    handled_cases += 1
                    
            except Exception as e:
                logger.warning(f"Edge case {case_type} failed: {e}")
        
        edge_case_score = handled_cases / len(edge_cases)
        
        return {
            'status': 'passed' if edge_case_score >= 0.8 else 'failed',
            'score': edge_case_score,
            'handled_cases': handled_cases,
            'total_edge_cases': len(edge_cases),
            'robustness_percent': edge_case_score * 100
        }
    
    async def _test_integrations(self) -> Dict[str, Any]:
        integration_manager = EnterpriseIntegrationManager()
        
        integration_manager.setup_collibra_integration('https://mock-collibra.com', 'test-key')
        integration_manager.setup_alation_integration('https://mock-alation.com', 'test-token')
        integration_manager.setup_datahub_integration('localhost:9092', 'http://localhost:8081')
        
        mock_matches = [
            EnhancedMatch(
                field="integration_test_field", table="test.integration", dataset="test",
                requirement="GLOBAL_ASSET_IDENTITY", score=0.85, semantic_depth=2,
                reasoning=["integration_test"], business_priority=8
            )
        ]
        
        sync_results = await integration_manager.sync_discoveries_to_catalogs(mock_matches)
        
        successful_syncs = sum(1 for result in sync_results.values() 
                             if result.get('status') in ['success', 'partial_success'])
        
        integration_score = successful_syncs / len(sync_results) if sync_results else 0
        
        return {
            'status': 'passed' if integration_score >= 0.8 else 'failed',
            'score': integration_score,
            'successful_integrations': successful_syncs,
            'total_integrations': len(sync_results),
            'sync_results': sync_results
        }