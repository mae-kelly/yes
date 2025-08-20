import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from gcp.client import BigQueryClientManager
from smart_claude_intelligence import ClaudeLevelIntelligence
from true_intelligence_confidence import TrueIntelligenceConfidence
import pickle
import json
from pathlib import Path
from typing import Dict, List, Any
import asyncio
import logging
from datetime import datetime
from collections import defaultdict
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BigQueryIntelligenceTrainer:
    def __init__(self, project_ids: List[str]):
        self.project_ids = project_ids
        self.intelligence = ClaudeLevelIntelligence()
        self.training_data = []
        self.learned_patterns = defaultdict(list)
        self.model_path = Path('trained_intelligence.pkl')
        self.training_stats = {
            'tables_processed': 0,
            'rows_analyzed': 0,
            'patterns_learned': 0,
            'confidence_improvements': []
        }
        
        self.client_managers = {}
        for project_id in project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                if manager.test_connection():
                    self.client_managers[project_id] = manager
                    logger.info(f"Connected to project: {project_id}")
            except Exception as e:
                logger.error(f"Failed to connect to {project_id}: {e}")
    
    async def train_on_bigquery_data(self, sample_size: int = 1000):
        logger.info("Starting BigQuery training...")
        
        for project_id, manager in self.client_managers.items():
            await self._train_on_project(project_id, manager, sample_size)
        
        self._consolidate_learning()
        self._save_trained_model()
        
        logger.info(f"Training complete. Stats: {self.training_stats}")
        return self.training_stats
    
    async def _train_on_project(self, project_id: str, manager, sample_size: int):
        with manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            for dataset in datasets[:5]:
                dataset_id = dataset.dataset_id if hasattr(dataset, 'dataset_id') else str(dataset).split('.')[-1]
                
                try:
                    tables = list(client.list_tables(f"{project_id}.{dataset_id}"))
                    
                    for table_ref in tables[:10]:
                        table_id = table_ref.table_id if hasattr(table_ref, 'table_id') else str(table_ref).split('.')[-1]
                        table_path = f"{project_id}.{dataset_id}.{table_id}"
                        
                        await self._train_on_table(client, table_path, sample_size)
                        
                except Exception as e:
                    logger.debug(f"Failed to process dataset {dataset_id}: {e}")
    
    async def _train_on_table(self, client, table_path: str, sample_size: int):
        try:
            table = client.get_table(table_path)
            
            if table.num_rows == 0:
                return
            
            columns = [field.name for field in table.schema]
            
            table_metadata = {
                'table_name': table_path,
                'columns': columns,
                'row_count': table.num_rows
            }
            
            initial_understanding = self.intelligence.understand_table_semantically(table_metadata, [])
            initial_confidence = initial_understanding['understanding_confidence']
            
            query = f"""
            SELECT *
            FROM `{table_path}`
            WHERE RAND() < {min(1.0, sample_size / table.num_rows)}
            LIMIT {sample_size}
            """
            
            query_job = client.query(query)
            results = list(query_job.result())
            
            sample_data = []
            for row in results:
                row_dict = {}
                for col in columns:
                    value = getattr(row, col, None)
                    row_dict[col] = value
                sample_data.append(row_dict)
            
            if sample_data:
                self._learn_from_samples(table_path, columns, sample_data)
                
                post_understanding = self.intelligence.understand_table_semantically(table_metadata, sample_data)
                post_confidence = post_understanding['understanding_confidence']
                
                confidence_improvement = post_confidence - initial_confidence
                self.training_stats['confidence_improvements'].append(confidence_improvement)
                
                logger.info(f"Trained on {table_path}: confidence {initial_confidence:.2%} -> {post_confidence:.2%}")
                
                self.training_stats['tables_processed'] += 1
                self.training_stats['rows_analyzed'] += len(sample_data)
        
        except Exception as e:
            logger.debug(f"Failed to train on {table_path}: {e}")
    
    def _learn_from_samples(self, table_path: str, columns: List[str], samples: List[Dict[str, Any]]):
        host_columns = [col for col in columns if 'host' in col.lower()]
        
        for sample in samples:
            if self._is_host_like(sample):
                concept = self.intelligence.knowledge_graph.understand_entity(sample)
                
                if concept.confidence > 0.7:
                    self._record_high_confidence_pattern(sample, concept)
                
                for pattern_type in concept.inferences:
                    self.learned_patterns[pattern_type].append({
                        'source': table_path,
                        'confidence': concept.confidence,
                        'example': sample
                    })
        
        self._learn_column_relationships(columns, samples)
        self._learn_value_patterns(samples)
    
    def _is_host_like(self, sample: Dict[str, Any]) -> bool:
        host_indicators = ['hostname', 'host', 'server', 'ip', 'device', 'computer']
        return any(indicator in key.lower() for key in sample.keys() for indicator in host_indicators)
    
    def _record_high_confidence_pattern(self, sample: Dict[str, Any], concept):
        pattern = {
            'fields_present': list(sample.keys()),
            'concept_type': concept.concept_type,
            'confidence': concept.confidence,
            'inferences': concept.inferences,
            'timestamp': datetime.now()
        }
        
        self.intelligence.knowledge_graph.confidence_system.observed_patterns['high_confidence'][str(pattern)] += 1
        self.training_stats['patterns_learned'] += 1
    
    def _learn_column_relationships(self, columns: List[str], samples: List[Dict[str, Any]]):
        for i, col1 in enumerate(columns):
            for col2 in columns[i+1:]:
                correlation = self._calculate_column_correlation(col1, col2, samples)
                
                if correlation > 0.7:
                    self.intelligence.knowledge_graph.confidence_system.field_correlations[col1][col2] = correlation
    
    def _calculate_column_correlation(self, col1: str, col2: str, samples: List[Dict[str, Any]]) -> float:
        paired_values = []
        
        for sample in samples:
            val1 = sample.get(col1)
            val2 = sample.get(col2)
            
            if val1 is not None and val2 is not None:
                paired_values.append((val1, val2))
        
        if not paired_values:
            return 0.0
        
        both_present = len(paired_values) / len(samples)
        
        if col1.lower() in col2.lower() or col2.lower() in col1.lower():
            return min(0.9, both_present * 1.2)
        
        return both_present
    
    def _learn_value_patterns(self, samples: List[Dict[str, Any]]):
        for sample in samples:
            for field, value in sample.items():
                if value is not None:
                    value_str = str(value)
                    
                    if 'host' in field.lower() and '-' in value_str:
                        parts = value_str.split('-')
                        if len(parts) >= 3:
                            pattern = f"{len(parts)}_part_hostname"
                            self.learned_patterns[pattern].append(value_str)
                    
                    if 'ip' in field.lower() and '.' in value_str:
                        if value_str.startswith('10.'):
                            self.learned_patterns['private_ip_10'].append(value_str)
                        elif value_str.startswith('192.168.'):
                            self.learned_patterns['private_ip_192'].append(value_str)
    
    def _consolidate_learning(self):
        confidence_system = self.intelligence.knowledge_graph.confidence_system
        
        for pattern_type, examples in self.learned_patterns.items():
            if len(examples) >= 3:
                confidence_system.pattern_discovery_engine.discovered_patterns.append({
                    'type': pattern_type,
                    'frequency': len(examples),
                    'learned': True
                })
        
        if self.training_stats['confidence_improvements']:
            avg_improvement = np.mean(self.training_stats['confidence_improvements'])
            logger.info(f"Average confidence improvement: {avg_improvement:.2%}")
    
    def _save_trained_model(self):
        model_data = {
            'learned_patterns': dict(self.learned_patterns),
            'field_correlations': dict(self.intelligence.knowledge_graph.confidence_system.field_correlations),
            'observed_patterns': dict(self.intelligence.knowledge_graph.confidence_system.observed_patterns),
            'training_stats': self.training_stats,
            'training_timestamp': datetime.now().isoformat()
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Saved trained model to {self.model_path}")
    
    def load_trained_model(self):
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            confidence_system = self.intelligence.knowledge_graph.confidence_system
            
            for field1, correlations in model_data['field_correlations'].items():
                for field2, correlation in correlations.items():
                    confidence_system.field_correlations[field1][field2] = correlation
            
            for pattern_type, pattern_data in model_data['observed_patterns'].items():
                confidence_system.observed_patterns[pattern_type] = defaultdict(int, pattern_data)
            
            logger.info(f"Loaded trained model from {self.model_path}")
            return True
        return False

async def train_intelligence():
    import yaml
    
    config_path = Path('/Users/maeve.kelly/Downloads/logLens2/config.yaml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        project_ids = config.get('project_ids', [])
    else:
        project_ids = ['your-project-id']
    
    trainer = BigQueryIntelligenceTrainer(project_ids)
    
    if trainer.load_trained_model():
        logger.info("Loaded existing trained model")
    
    await trainer.train_on_bigquery_data(sample_size=500)
    
    test_host = {
        'hostname': 'prod-web-01',
        'ip_address': '10.0.0.1',
        'environment': 'production'
    }
    
    concept = trainer.intelligence.knowledge_graph.understand_entity(test_host)
    print(f"\nPost-training confidence: {concept.confidence:.2%}")
    print(f"Inferences: {concept.inferences}")

def test_with_real_data():
    trainer = BigQueryIntelligenceTrainer(['your-project-id'])
    
    if trainer.load_trained_model():
        print("Using trained model")
        
        test_cases = [
            {'hostname': 'prod-db-01', 'environment': 'production'},
            {'hostname': 'dev-test-02', 'environment': 'development'},
            {'hostname': 'srv-app-03', 'ip_address': '10.1.2.3'}
        ]
        
        for test in test_cases:
            concept = trainer.intelligence.knowledge_graph.understand_entity(test)
            print(f"\n{test['hostname']}: {concept.confidence:.2%}")
    else:
        print("No trained model found. Run training first.")

if __name__ == "__main__":
    asyncio.run(train_intelligence())