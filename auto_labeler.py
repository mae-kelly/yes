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
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteInteractiveLabeler:
    def __init__(self):
        self.project_ids = ['prj-fisv-p-gcss-sas-dl9dd0f1df', 'chronicle-fisv']
        self.client_managers = {}
        self.labeled_data_path = Path('complete_labeled_columns.json')
        self.model_path = Path('column_classifier_model.pkl')
        
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
            0: 'skip'
        }
        
        self.labeled_columns = self._load_labeled_data()
        self.statistics = {
            'total_tables': 0,
            'total_columns': 0,
            'labeled_columns': 0,
            'skipped_columns': 0,
            'start_time': datetime.now()
        }
        
        print("\n" + "="*80)
        print("COMPLETE INTERACTIVE LABELING SYSTEM")
        print("="*80)
        print(f"Projects: {', '.join(self.project_ids)}")
        print("This will ask you to label EVERY column in EVERY table")
        print("="*80)
        
        self._connect_to_projects()
    
    def _connect_to_projects(self):
        for project_id in self.project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                if manager.test_connection():
                    self.client_managers[project_id] = manager
                    print(f"✅ Connected to: {project_id}")
                else:
                    print(f"❌ Failed to connect to: {project_id}")
            except Exception as e:
                print(f"❌ Error connecting to {project_id}: {e}")
        
        if not self.client_managers:
            raise RuntimeError("Could not connect to any projects")
    
    def _load_labeled_data(self) -> Dict[str, Any]:
        if self.labeled_data_path.exists():
            with open(self.labeled_data_path, 'r') as f:
                return json.load(f)
        return {
            'columns': {},
            'patterns': defaultdict(list),
            'labeling_history': []
        }
    
    def _save_labeled_data(self):
        with open(self.labeled_data_path, 'w') as f:
            json.dump(self.labeled_columns, f, indent=2, default=str)
    
    def label_all_tables(self):
        print("\nColumn types:")
        print("-" * 50)
        for num, col_type in self.column_types.items():
            if num == 0:
                print(f"\n{num}: {col_type} (not a relevant column)")
            else:
                print(f"{num:2}. {col_type}")
        print("-" * 50)
        print("\nStarting labeling process...\n")
        
        total_start = time.time()
        
        for project_id, manager in self.client_managers.items():
            self._label_project(project_id, manager)
        
        total_time = time.time() - total_start
        
        self._print_statistics(total_time)
        self._train_model()
        self._save_labeled_data()
    
    def _label_project(self, project_id: str, manager):
        print(f"\n{'='*60}")
        print(f"PROJECT: {project_id}")
        print('='*60)
        
        with manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            print(f"Found {len(datasets)} datasets\n")
            
            for dataset_idx, dataset in enumerate(datasets, 1):
                dataset_id = dataset.dataset_id if hasattr(dataset, 'dataset_id') else str(dataset).split('.')[-1]
                print(f"\n[Dataset {dataset_idx}/{len(datasets)}] {dataset_id}")
                print("-" * 40)
                
                try:
                    tables = list(client.list_tables(f"{project_id}.{dataset_id}"))
                    print(f"Found {len(tables)} tables")
                    
                    for table_idx, table_ref in enumerate(tables, 1):
                        table_id = table_ref.table_id if hasattr(table_ref, 'table_id') else str(table_ref).split('.')[-1]
                        table_path = f"{project_id}.{dataset_id}.{table_id}"
                        
                        print(f"\n  [Table {table_idx}/{len(tables)}] {table_id}")
                        
                        if table_path in self.labeled_columns.get('columns', {}):
                            print("    ✓ Already labeled - skipping")
                            continue
                        
                        self._label_table(client, table_path)
                        self.statistics['total_tables'] += 1
                        
                        self._save_labeled_data()
                        
                except Exception as e:
                    print(f"  ❌ Error processing dataset {dataset_id}: {e}")
    
    def _label_table(self, client, table_path: str):
        try:
            table = client.get_table(table_path)
            
            if table.num_rows == 0:
                print("    (Empty table - skipping)")
                return
            
            columns = [field.name for field in table.schema]
            print(f"    {len(columns)} columns, {table.num_rows:,} rows")
            
            query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 5
            """
            
            try:
                query_job = client.query(query)
                results = list(query_job.result(timeout=30))
            except:
                results = []
                print("    ⚠️  Could not fetch sample data")
            
            table_labels = {}
            
            for col_idx, column in enumerate(columns, 1):
                print(f"\n    [{col_idx}/{len(columns)}] Column: '{column}'")
                
                if results:
                    print("    Sample values:")
                    for i, row in enumerate(results[:5], 1):
                        value = getattr(row, column, None)
                        if value is not None:
                            value_str = str(value)[:100]
                            print(f"      {i}. {value_str}")
                        else:
                            print(f"      {i}. (null)")
                else:
                    print("    (No sample data available)")
                
                while True:
                    try:
                        choice = input("\n    Label (1-17, 0 to skip, ? for help): ").strip()
                        
                        if choice == '?':
                            print("\n    Column types:")
                            for num, col_type in self.column_types.items():
                                if num == 0:
                                    print(f"    {num}: {col_type}")
                                else:
                                    print(f"    {num:2}. {col_type}")
                            continue
                        
                        choice_num = int(choice)
                        
                        if choice_num in self.column_types:
                            label = self.column_types[choice_num]
                            table_labels[column] = label
                            
                            if label == 'skip':
                                print("    → Skipped")
                                self.statistics['skipped_columns'] += 1
                            else:
                                print(f"    → Labeled as: {label}")
                                self.statistics['labeled_columns'] += 1
                                
                                self.labeled_columns['patterns'][label].append({
                                    'column': column,
                                    'table': table_path,
                                    'sample': results[0].__dict__.get(column) if results else None
                                })
                            
                            self.statistics['total_columns'] += 1
                            break
                        else:
                            print("    Invalid choice. Enter 1-17 or 0 to skip.")
                    
                    except ValueError:
                        print("    Please enter a number.")
                    except KeyboardInterrupt:
                        print("\n\n⚠️  Interrupted. Saving progress...")
                        self._save_labeled_data()
                        raise
            
            self.labeled_columns['columns'][table_path] = table_labels
            
            self.labeled_columns['labeling_history'].append({
                'table': table_path,
                'labels': table_labels,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"\n    ✅ Table labeled: {len([l for l in table_labels.values() if l != 'skip'])} relevant columns")
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"    ❌ Error labeling table: {e}")
    
    def _train_model(self):
        print("\n" + "="*60)
        print("Training Classification Model")
        print("="*60)
        
        X = []
        y = []
        
        for table_path, table_labels in self.labeled_columns['columns'].items():
            for column, label in table_labels.items():
                if label != 'skip':
                    features = self._extract_features(column)
                    X.append(features)
                    y.append(label)
        
        if len(set(y)) < 2:
            print("Not enough different column types to train model")
            return
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        classifier.fit(X_train, y_train)
        
        train_score = classifier.score(X_train, y_train)
        test_score = classifier.score(X_test, y_test)
        
        print(f"Training examples: {len(X_train)}")
        print(f"Training accuracy: {train_score:.2%}")
        print(f"Test accuracy: {test_score:.2%}")
        
        model_data = {
            'classifier': classifier,
            'column_types': list(set(y)),
            'training_size': len(X_train),
            'test_score': test_score
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {self.model_path}")
    
    def _extract_features(self, column_name: str) -> List[float]:
        features = []
        column_lower = column_name.lower()
        
        features.append(len(column_name))
        features.append(1 if '_' in column_name else 0)
        features.append(column_name.count('_'))
        features.append(1 if any(c.isdigit() for c in column_name) else 0)
        
        keywords = ['host', 'ip', 'region', 'country', 'center', 'cloud', 'business', 
                   'cio', 'apm', 'app', 'system', 'edr', 'tanium', 'dlp', 'splunk', 
                   'gso', 'domain', 'type', 'class', 'coverage', 'logging']
        
        for keyword in keywords:
            features.append(1 if keyword in column_lower else 0)
        
        return features
    
    def _print_statistics(self, total_time: float):
        print("\n" + "="*80)
        print("LABELING COMPLETE")
        print("="*80)
        print(f"Time taken: {total_time/60:.1f} minutes")
        print(f"Tables processed: {self.statistics['total_tables']}")
        print(f"Total columns: {self.statistics['total_columns']}")
        print(f"Labeled columns: {self.statistics['labeled_columns']}")
        print(f"Skipped columns: {self.statistics['skipped_columns']}")
        
        if self.statistics['total_columns'] > 0:
            print(f"Labeling rate: {self.statistics['labeled_columns']/self.statistics['total_columns']*100:.1f}%")
        
        print("\nColumn type distribution:")
        type_counts = defaultdict(int)
        for table_labels in self.labeled_columns['columns'].values():
            for label in table_labels.values():
                if label != 'skip':
                    type_counts[label] += 1
        
        for col_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {col_type:25} {count:5}")
        
        print("\n✅ All labeled data saved to: complete_labeled_columns.json")

def main():
    try:
        labeler = CompleteInteractiveLabeler()
        labeler.label_all_tables()
    except KeyboardInterrupt:
        print("\n\n⚠️  Labeling interrupted by user")
        print("Progress has been saved. Run again to continue.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()