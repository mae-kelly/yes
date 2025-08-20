import json
import pickle
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainedConfidenceSystem:
    def __init__(self):
        self.labeled_data_path = Path('labeled_columns.json')
        self.model_path = Path('column_classifier_model.pkl')
        self.labeled_data = self._load_labeled_data()
        self.model = self._load_model()
        self.confidence_boosts = {
            'exact_match': 0.95,
            'pattern_match': 0.85,
            'model_prediction': 0.75,
            'similarity_match': 0.65
        }
    
    def _load_labeled_data(self) -> Dict[str, Any]:
        if self.labeled_data_path.exists():
            with open(self.labeled_data_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_model(self):
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def calculate_confidence(self, entity_data: Dict[str, Any], column_mappings: Dict[str, str]) -> Tuple[float, Dict[str, Any]]:
        confidence_components = []
        confidence_details = {}
        
        labeled_match_score = self._check_labeled_matches(entity_data, column_mappings)
        confidence_components.append(labeled_match_score['score'])
        confidence_details['labeled_matches'] = labeled_match_score
        
        data_completeness = self._calculate_completeness(entity_data, column_mappings)
        confidence_components.append(data_completeness['score'])
        confidence_details['completeness'] = data_completeness
        
        known_patterns = self._check_known_patterns(entity_data, column_mappings)
        confidence_components.append(known_patterns['score'])
        confidence_details['pattern_matches'] = known_patterns
        
        critical_fields = self._check_critical_fields(entity_data, column_mappings)
        confidence_components.append(critical_fields['score'])
        confidence_details['critical_fields'] = critical_fields
        
        consistency = self._check_consistency(entity_data, column_mappings)
        confidence_components.append(consistency['score'])
        confidence_details['consistency'] = consistency
        
        final_confidence = self._calculate_weighted_confidence(confidence_components)
        
        if column_mappings.get('host') in entity_data and entity_data[column_mappings['host']]:
            final_confidence *= 1.1
        
        if self._has_security_coverage(entity_data, column_mappings):
            final_confidence *= 1.05
        
        final_confidence = min(0.99, final_confidence)
        
        confidence_details['final_score'] = final_confidence
        confidence_details['components'] = confidence_components
        
        return final_confidence, confidence_details
    
    def _check_labeled_matches(self, entity_data: Dict[str, Any], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        if not self.labeled_data or 'columns' not in self.labeled_data:
            return {'score': 0.5, 'matched': 0, 'total': 0}
        
        matched = 0
        total = len(column_mappings)
        
        for expected_type, actual_column in column_mappings.items():
            if actual_column in entity_data:
                for table_path, table_labels in self.labeled_data['columns'].items():
                    if actual_column in table_labels and table_labels[actual_column] == expected_type:
                        matched += 1
                        break
        
        score = (matched / total) if total > 0 else 0.5
        
        if matched == total and total > 5:
            score = 0.95
        elif matched > total * 0.8:
            score = 0.85
        
        return {
            'score': score,
            'matched': matched,
            'total': total,
            'percentage': (matched / total * 100) if total > 0 else 0
        }
    
    def _calculate_completeness(self, entity_data: Dict[str, Any], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        critical_fields = ['host', 'infrastructure_type', 'environment', 'edr_coverage', 
                          'logging_in_splunk', 'criticality', 'region']
        
        found = 0
        for field in critical_fields:
            if field in column_mappings:
                column = column_mappings[field]
                if column in entity_data and entity_data[column] not in [None, '', 'null', 'unknown']:
                    found += 1
        
        completeness = found / len(critical_fields)
        
        non_null_values = sum(1 for v in entity_data.values() if v not in [None, '', 'null', 'unknown'])
        data_density = non_null_values / len(entity_data) if entity_data else 0
        
        score = completeness * 0.7 + data_density * 0.3
        
        return {
            'score': score,
            'critical_fields_found': found,
            'critical_fields_total': len(critical_fields),
            'data_density': data_density
        }
    
    def _check_known_patterns(self, entity_data: Dict[str, Any], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        patterns_found = []
        
        if 'host' in column_mappings:
            hostname = str(entity_data.get(column_mappings['host'], '')).lower()
            
            if 'prod' in hostname and column_mappings.get('environment') in entity_data:
                if 'prod' in str(entity_data[column_mappings['environment']]).lower():
                    patterns_found.append(('consistent_environment', 0.9))
            
            if '-' in hostname:
                parts = hostname.split('-')
                if len(parts) >= 3:
                    patterns_found.append(('structured_hostname', 0.85))
        
        if 'ip_address' in column_mappings and column_mappings['ip_address'] in entity_data:
            ip = str(entity_data[column_mappings['ip_address']])
            if ip.startswith('10.') or ip.startswith('192.168.'):
                patterns_found.append(('private_ip', 0.8))
        
        if self.labeled_data and 'patterns' in self.labeled_data:
            for pattern_type, examples in self.labeled_data['patterns'].items():
                if pattern_type in column_mappings:
                    column = column_mappings[pattern_type]
                    if column in entity_data:
                        value = str(entity_data[column])
                        for example in examples[:5]:
                            if example.get('sample') and value.startswith(str(example['sample'])[:3]):
                                patterns_found.append((f'learned_{pattern_type}', 0.7))
                                break
        
        if not patterns_found:
            return {'score': 0.6, 'patterns': []}
        
        avg_score = sum(score for _, score in patterns_found) / len(patterns_found)
        
        return {
            'score': avg_score,
            'patterns': [p[0] for p in patterns_found],
            'count': len(patterns_found)
        }
    
    def _check_critical_fields(self, entity_data: Dict[str, Any], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        critical_score = 0.7
        critical_present = []
        
        if 'host' in column_mappings and column_mappings['host'] in entity_data:
            if entity_data[column_mappings['host']]:
                critical_score += 0.15
                critical_present.append('host')
        
        security_fields = ['edr_coverage', 'tanium_coverage', 'logging_in_splunk', 'logging_in_gso']
        security_count = 0
        for field in security_fields:
            if field in column_mappings and column_mappings[field] in entity_data:
                security_count += 1
                critical_present.append(field)
        
        if security_count >= 2:
            critical_score += 0.1
        
        if 'criticality' in column_mappings and column_mappings['criticality'] in entity_data:
            critical_score += 0.05
            critical_present.append('criticality')
        
        return {
            'score': min(0.95, critical_score),
            'critical_fields': critical_present,
            'security_coverage': security_count
        }
    
    def _check_consistency(self, entity_data: Dict[str, Any], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        consistency_checks = []
        
        if 'host' in column_mappings and 'environment' in column_mappings:
            hostname = str(entity_data.get(column_mappings['host'], '')).lower()
            environment = str(entity_data.get(column_mappings['environment'], '')).lower()
            
            if ('prod' in hostname and 'prod' in environment) or \
               ('dev' in hostname and 'dev' in environment) or \
               ('test' in hostname and 'test' in environment):
                consistency_checks.append(('hostname_environment_match', True))
        
        if 'criticality' in column_mappings and 'environment' in column_mappings:
            criticality = str(entity_data.get(column_mappings['criticality'], '')).lower()
            environment = str(entity_data.get(column_mappings['environment'], '')).lower()
            
            if ('prod' in environment and criticality in ['high', 'critical']) or \
               ('dev' in environment and criticality in ['low', 'medium']):
                consistency_checks.append(('criticality_environment_match', True))
        
        consistency_score = 0.7 + (len(consistency_checks) * 0.15)
        
        return {
            'score': min(0.95, consistency_score),
            'checks_passed': len(consistency_checks),
            'consistency_types': [c[0] for c in consistency_checks]
        }
    
    def _has_security_coverage(self, entity_data: Dict[str, Any], column_mappings: Dict[str, str]) -> bool:
        security_fields = ['edr_coverage', 'tanium_coverage', 'dlp_agent_coverage', 
                          'logging_in_splunk', 'logging_in_gso']
        
        coverage_count = 0
        for field in security_fields:
            if field in column_mappings:
                column = column_mappings[field]
                if column in entity_data:
                    value = entity_data[column]
                    if value in [True, 'true', 'True', '1', 1, 'yes', 'Yes']:
                        coverage_count += 1
        
        return coverage_count >= 2
    
    def _calculate_weighted_confidence(self, components: List[float]) -> float:
        if not components:
            return 0.5
        
        weights = [1.3, 1.2, 1.1, 1.0, 0.9][:len(components)]
        weights = np.array(weights) / sum(weights)
        
        weighted_avg = np.average(components, weights=weights)
        
        if all(c > 0.8 for c in components):
            weighted_avg *= 1.1
        
        return min(0.99, weighted_avg)

class IntelligentDiscoveryWithLabels:
    def __init__(self):
        self.confidence_system = TrainedConfidenceSystem()
        self.labeled_columns_path = Path('labeled_columns.json')
        
    def analyze_with_high_confidence(self, entity_data: Dict[str, Any], table_path: str) -> Dict[str, Any]:
        column_mappings = self._get_column_mappings(table_path)
        
        confidence, details = self.confidence_system.calculate_confidence(entity_data, column_mappings)
        
        inferences = self._generate_inferences(entity_data, column_mappings, confidence)
        
        return {
            'confidence': confidence,
            'confidence_details': details,
            'column_mappings': column_mappings,
            'inferences': inferences,
            'risk_score': self._calculate_risk(entity_data, column_mappings, inferences)
        }
    
    def _get_column_mappings(self, table_path: str) -> Dict[str, str]:
        if self.labeled_columns_path.exists():
            with open(self.labeled_columns_path, 'r') as f:
                labeled_data = json.load(f)
            
            if table_path in labeled_data.get('columns', {}):
                table_labels = labeled_data['columns'][table_path]
                
                mappings = {}
                for column, label in table_labels.items():
                    if label != 'skip' and label != 'other':
                        mappings[label] = column
                
                return mappings
        
        return {}
    
    def _generate_inferences(self, entity_data: Dict[str, Any], mappings: Dict[str, str], confidence: float) -> List[str]:
        inferences = []
        
        if confidence > 0.9:
            inferences.append('high_confidence_entity')
        
        if 'host' in mappings and mappings['host'] in entity_data:
            hostname = str(entity_data[mappings['host']]).lower()
            if 'prod' in hostname:
                inferences.append('production_system')
        
        if 'edr_coverage' in mappings and mappings['edr_coverage'] in entity_data:
            if not entity_data[mappings['edr_coverage']]:
                inferences.append('no_edr_coverage')
        
        if 'logging_in_splunk' in mappings and mappings['logging_in_splunk'] in entity_data:
            if not entity_data[mappings['logging_in_splunk']]:
                inferences.append('no_splunk_logging')
        
        if 'production_system' in inferences and 'no_edr_coverage' in inferences:
            inferences.append('critical_security_gap')
        
        return inferences
    
    def _calculate_risk(self, entity_data: Dict[str, Any], mappings: Dict[str, str], inferences: List[str]) -> float:
        risk = 30
        
        if 'critical_security_gap' in inferences:
            risk += 40
        if 'no_edr_coverage' in inferences:
            risk += 20
        if 'no_splunk_logging' in inferences:
            risk += 15
        if 'production_system' in inferences:
            risk += 10
        
        return min(100, risk)