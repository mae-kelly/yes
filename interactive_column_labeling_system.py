import sys
import os
sys.path.insert(0, '/Users/maeve.kelly/Downloads/logLens2')

from gcp.client import BigQueryClientManager
import json
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from collections import defaultdict
import numpy as np
from smart_claude_intelligence import ClaudeLevelIntelligence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractiveColumnLabeler:
    def __init__(self, project_ids: List[str]):
        self.project_ids = project_ids
        self.client_managers = {}
        self.labeled_data_path = Path('labeled_columns.json')
        self.model_path = Path('column_classifier_model.pkl')
        self.intelligence = ClaudeLevelIntelligence()
        
        self.column_types = {
            1: 'host',
            2: 'infrastructure_type',
            3: 'region',
            4: 'country',
            5: 'data_center',
            6: 'cloud_region',
            7: 'business_unit',
            8: 'cio',
            9: 'apm',
            10: 'app_class',
            11: 'system_classification',
            12: 'edr_coverage',
            13: 'tanium_coverage',
            14: 'dlp_agent_coverage',
            15: 'logging_in_splunk',
            16: 'logging_in_gso',
            17: 'domain',
            18: 'ip_address',
            19: 'mac_address',
            20: 'os_type',
            21: 'os_version',
            22: 'patch_level',
            23: 'owner',
            24: 'criticality',
            25: 'environment',
            26: 'last_patch_date',
            27: 'created_date',
            28: 'modified_date',
            29: 'other',
            30: 'skip'
        }
        
        self.labeled_columns = self._load_labeled_data()
        self.training_data = defaultdict(list)
        
        for project_id in project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                if manager.test_connection():
                    self.client_managers[project_id] = manager
                    logger.info(f"Connected to project: {project_id}")
            except Exception as e:
                logger.error(f"Failed to connect to {project_id}: {e}")
    
    def _load_labeled_data(self) -> Dict[str, Any]:
        if self.labeled_data_path.exists():
            with open(self.labeled_data_path, 'r') as f:
                return json.load(f)
        return {
            'columns': {},
            'patterns': defaultdict(list),
            'confidence_scores': {},
            'labeling_history': []
        }
    
    def _save_labeled_data(self):
        with open(self.labeled_data_path, 'w') as f:
            json.dump(self.labeled_columns, f, indent=2, default=str)
    
    def start_interactive_labeling(self, max_tables_per_project: int = 5):
        print("\n" + "="*80)
        print("INTERACTIVE COLUMN LABELING SYSTEM")
        print("="*80)
        print("\nI'll show you columns with sample data.")
        print("You tell me what each column represents by entering a number.\n")
        print("Column Types:")
        for num, col_type in self.column_types.items():
            if num % 5 == 1:
                print()
            print(f"{num:2}. {col_type:20}", end="  ")
        print("\n\n" + "="*80)
        
        tables_labeled = 0
        
        for project_id, manager in self.client_managers.items():
            print(f"\n📁 PROJECT: {project_id}")
            print("-"*60)
            
            with manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                for dataset in datasets[:3]:
                    dataset_id = dataset.dataset_id if hasattr(dataset, 'dataset_id') else str(dataset).split('.')[-1]
                    print(f"\n  📂 Dataset: {dataset_id}")
                    
                    try:
                        tables = list(client.list_tables(f"{project_id}.{dataset_id}"))
                        
                        for table_ref in tables[:max_tables_per_project]:
                            table_id = table_ref.table_id if hasattr(table_ref, 'table_id') else str(table_ref).split('.')[-1]
                            table_path = f"{project_id}.{dataset_id}.{table_id}"
                            
                            if table_path in self.labeled_columns.get('columns', {}):
                                print(f"    ✓ Table {table_id} already labeled")
                                continue
                            
                            self._label_table(client, table_path)
                            tables_labeled += 1
                            
                            if tables_labeled >= max_tables_per_project:
                                break
                    
                    except Exception as e:
                        logger.debug(f"Failed to process dataset {dataset_id}: {e}")
        
        print(f"\n✅ Labeled {tables_labeled} tables")
        self._train_model()
    
    def _label_table(self, client, table_path: str):
        print(f"\n    📊 Table: {table_path.split('.')[-1]}")
        print("    " + "-"*50)
        
        try:
            table = client.get_table(table_path)
            
            if table.num_rows == 0:
                print("      (Empty table, skipping)")
                return
            
            columns = [field.name for field in table.schema]
            
            query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 5
            """
            
            query_job = client.query(query)
            results = list(query_job.result())
            
            if not results:
                print("      (No data, skipping)")
                return
            
            table_labels = {}
            
            for column in columns:
                print(f"\n    Column: '{column}'")
                print("    Sample values:")
                
                samples = []
                for i, row in enumerate(results[:5]):
                    value = getattr(row, column, None)
                    if value is not None:
                        value_str = str(value)[:100]
                        print(f"      {i+1}. {value_str}")
                        samples.append(value_str)
                    else:
                        print(f"      {i+1}. (null)")
                        samples.append(None)
                
                initial_guess = self._predict_column_type(column, samples)
                if initial_guess:
                    print(f"\n    💡 My guess: {initial_guess}")
                
                while True:
                    try:
                        choice = input("\n    What is this column? (Enter number, or 0 to see options again): ")
                        
                        if choice == '0':
                            for num, col_type in self.column_types.items():
                                if num % 5 == 1:
                                    print()
                                print(f"    {num:2}. {col_type:20}", end="  ")
                            print()
                            continue
                        
                        choice_num = int(choice)
                        
                        if choice_num in self.column_types:
                            label = self.column_types[choice_num]
                            table_labels[column] = label
                            
                            self._record_training_example(column, samples, label)
                            
                            if label != 'skip':
                                print(f"    ✓ Labeled as: {label}")
                            else:
                                print("    ✓ Skipped")
                            break
                        else:
                            print("    Invalid choice. Please enter a valid number.")
                    
                    except ValueError:
                        print("    Please enter a number.")
                    except KeyboardInterrupt:
                        print("\n    Pausing... (Press Ctrl+C again to exit)")
                        return
            
            self.labeled_columns['columns'][table_path] = table_labels
            
            self.labeled_columns['labeling_history'].append({
                'table': table_path,
                'labels': table_labels,
                'timestamp': datetime.now().isoformat()
            })
            
            self._save_labeled_data()
            
            print(f"\n    ✅ Table labeled successfully!")
            
        except Exception as e:
            logger.error(f"Failed to label table {table_path}: {e}")
    
    def _predict_column_type(self, column_name: str, samples: List[Any]) -> Optional[str]:
        column_lower = column_name.lower()
        
        if 'host' in column_lower or 'computer' in column_lower or 'server' in column_lower:
            return 'host'
        elif 'ip' in column_lower and 'address' in column_lower:
            return 'ip_address'
        elif 'mac' in column_lower:
            return 'mac_address'
        elif 'region' in column_lower:
            return 'region'
        elif 'country' in column_lower:
            return 'country'
        elif 'domain' in column_lower:
            return 'domain'
        elif 'owner' in column_lower:
            return 'owner'
        elif 'environment' in column_lower or 'env' == column_lower:
            return 'environment'
        elif 'critical' in column_lower:
            return 'criticality'
        elif 'edr' in column_lower:
            return 'edr_coverage'
        elif 'tanium' in column_lower:
            return 'tanium_coverage'
        elif 'dlp' in column_lower:
            return 'dlp_agent_coverage'
        elif 'splunk' in column_lower:
            return 'logging_in_splunk'
        elif 'gso' in column_lower:
            return 'logging_in_gso'
        
        if samples and samples[0]:
            sample = str(samples[0])
            if '.' in sample and sample.replace('.', '').isdigit():
                if sample.count('.') == 3:
                    return 'ip_address'
        
        return None
    
    def _record_training_example(self, column_name: str, samples: List[Any], label: str):
        training_example = {
            'column_name': column_name,
            'samples': samples,
            'label': label,
            'features': self._extract_features(column_name, samples)
        }
        
        self.training_data[label].append(training_example)
        
        self.labeled_columns['patterns'][label].append({
            'column': column_name,
            'sample': samples[0] if samples else None
        })
    
    def _extract_features(self, column_name: str, samples: List[Any]) -> Dict[str, Any]:
        features = {
            'column_name_lower': column_name.lower(),
            'has_underscore': '_' in column_name,
            'has_camelcase': any(c.isupper() for c in column_name[1:]),
            'length': len(column_name),
            'non_null_samples': sum(1 for s in samples if s is not None),
            'unique_samples': len(set(str(s) for s in samples if s is not None))
        }
        
        if samples:
            non_null_samples = [s for s in samples if s is not None]
            if non_null_samples:
                sample_str = str(non_null_samples[0])
                features['sample_has_dash'] = '-' in sample_str
                features['sample_has_dot'] = '.' in sample_str
                features['sample_is_numeric'] = sample_str.replace('.', '').replace('-', '').isdigit()
                features['sample_length'] = len(sample_str)
        
        return features
    
    def _train_model(self):
        if not self.training_data:
            print("\nNo training data available yet.")
            return
        
        print("\n🧠 Training column classifier model...")
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        X = []
        y = []
        
        for label, examples in self.training_data.items():
            for example in examples:
                feature_vector = []
                
                feature_vector.append(len(example['column_name']))
                feature_vector.append(1 if '_' in example['column_name'] else 0)
                feature_vector.append(1 if '-' in example['column_name'] else 0)
                feature_vector.append(example['features'].get('non_null_samples', 0))
                feature_vector.append(example['features'].get('unique_samples', 0))
                feature_vector.append(example['features'].get('sample_is_numeric', 0))
                
                X.append(feature_vector)
                y.append(label)
        
        if len(set(y)) < 2:
            print("Need at least 2 different column types to train.")
            return
        
        classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        classifier.fit(X, y)
        
        column_name_vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
        column_names = [ex['column_name'] for examples in self.training_data.values() for ex in examples]
        column_name_vectorizer.fit(column_names)
        
        model_data = {
            'classifier': classifier,
            'vectorizer': column_name_vectorizer,
            'label_examples': self.training_data,
            'feature_extractor': self._extract_features
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✅ Model trained on {len(X)} examples across {len(set(y))} column types")
        
        accuracy = classifier.score(X, y)
        print(f"📊 Training accuracy: {accuracy:.2%}")
    
    def auto_label_with_model(self, table_path: str, client) -> Dict[str, str]:
        if not self.model_path.exists():
            return {}
        
        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        classifier = model_data['classifier']
        
        try:
            table = client.get_table(table_path)
            columns = [field.name for field in table.schema]
            
            query = f"SELECT * FROM `{table_path}` LIMIT 5"
            query_job = client.query(query)
            results = list(query_job.result())
            
            predictions = {}
            
            for column in columns:
                samples = [getattr(row, column, None) for row in results]
                
                features = self._extract_features(column, samples)
                feature_vector = [
                    len(column),
                    1 if '_' in column else 0,
                    1 if '-' in column else 0,
                    features.get('non_null_samples', 0),
                    features.get('unique_samples', 0),
                    features.get('sample_is_numeric', 0)
                ]
                
                prediction = classifier.predict([feature_vector])[0]
                confidence = max(classifier.predict_proba([feature_vector])[0])
                
                predictions[column] = {
                    'type': prediction,
                    'confidence': confidence
                }
            
            return predictions
        
        except Exception as e:
            logger.error(f"Failed to auto-label {table_path}: {e}")
            return {}
    
    def get_labeled_statistics(self) -> Dict[str, Any]:
        stats = {
            'total_tables_labeled': len(self.labeled_columns.get('columns', {})),
            'total_columns_labeled': sum(len(labels) for labels in self.labeled_columns.get('columns', {}).values()),
            'column_type_distribution': defaultdict(int),
            'most_common_patterns': {}
        }
        
        for table_labels in self.labeled_columns.get('columns', {}).values():
            for column, label in table_labels.items():
                stats['column_type_distribution'][label] += 1
        
        for label, patterns in self.labeled_columns.get('patterns', {}).items():
            if patterns:
                most_common = Counter(p['column'] for p in patterns).most_common(3)
                stats['most_common_patterns'][label] = most_common
        
        return stats

def main():
    import yaml
    
    config_path = Path('/Users/maeve.kelly/Downloads/logLens2/config.yaml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        project_ids = config.get('project_ids', [])
    else:
        project_ids = input("Enter project IDs (comma-separated): ").split(',')
        project_ids = [p.strip() for p in project_ids]
    
    labeler = InteractiveColumnLabeler(project_ids)
    
    print("\nWhat would you like to do?")
    print("1. Start interactive labeling")
    print("2. View labeling statistics")
    print("3. Auto-label a new project with trained model")
    
    choice = input("\nChoice: ")
    
    if choice == '1':
        max_tables = int(input("How many tables to label per project? (default 5): ") or "5")
        labeler.start_interactive_labeling(max_tables)
        
        stats = labeler.get_labeled_statistics()
        print("\n" + "="*60)
        print("LABELING COMPLETE!")
        print("="*60)
        print(f"Tables labeled: {stats['total_tables_labeled']}")
        print(f"Columns labeled: {stats['total_columns_labeled']}")
        print("\nColumn type distribution:")
        for col_type, count in stats['column_type_distribution'].items():
            print(f"  {col_type}: {count}")
    
    elif choice == '2':
        stats = labeler.get_labeled_statistics()
        print("\n" + "="*60)
        print("LABELING STATISTICS")
        print("="*60)
        print(f"Tables labeled: {stats['total_tables_labeled']}")
        print(f"Columns labeled: {stats['total_columns_labeled']}")
        print("\nColumn type distribution:")
        for col_type, count in sorted(stats['column_type_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {col_type:25} {count:4}")
    
    elif choice == '3':
        print("\nAuto-labeling feature coming soon!")

if __name__ == "__main__":
    main()