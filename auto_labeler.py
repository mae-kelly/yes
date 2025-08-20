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

class ManualCompleteLabeler:
    def __init__(self):
        self.project_ids = ['prj-fisv-p-gcss-sas-dl9dd0f1df', 'chronicle-fisv']
        self.client_managers = {}
        self.labeled_data_path = Path('manual_labeled_columns.json')
        self.model_path = Path('manual_column_classifier.pkl')
        
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
            18: 'skip'
        }
        
        self.labeled_columns = self._load_labeled_data()
        self.statistics = {
            'total_tables': 0,
            'total_columns': 0,
            'labeled_columns': 0,
            'skipped_columns': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"Initializing labeler for projects: {', '.join(self.project_ids)}")
        self._connect_to_projects()
    
    def _connect_to_projects(self):
        for project_id in self.project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                if manager.test_connection():
                    self.client_managers[project_id] = manager
                    logger.info(f"✅ Connected to project: {project_id}")
                else:
                    logger.error(f"❌ Failed to connect to project: {project_id}")
            except Exception as e:
                logger.error(f"❌ Connection error for {project_id}: {e}")
        
        if not self.client_managers:
            raise RuntimeError("Failed to connect to any projects")
    
    def _load_labeled_data(self) -> Dict[str, Any]:
        if self.labeled_data_path.exists():
            with open(self.labeled_data_path, 'r') as f:
                return json.load(f)
        return {
            'columns': {},
            'patterns': defaultdict(list),
            'labeling_history': [],
            'statistics': {}
        }
    
    def _save_labeled_data(self):
        with open(self.labeled_data_path, 'w') as f:
            json.dump(self.labeled_columns, f, indent=2, default=str)
        logger.info(f"💾 Saved labeled data to {self.labeled_data_path}")
    
    def label_all_tables_manually(self):
        print("\n" + "="*80)
        print("MANUAL COMPLETE PROJECT LABELING")
        print("="*80)
        print(f"Projects: {', '.join(self.project_ids)}")
        print("\nYou will label EVERY column in EVERY table")
        print("\nColumn Types:")
        for num, col_type in self.column_types.items():
            print(f"{num:2}. {col_type}")
        print("="*80 + "\n")
        
        total_start = time.time()
        
        try:
            for project_id, manager in self.client_managers.items():
                self._label_entire_project(project_id, manager)
        except KeyboardInterrupt:
            print("\n\n⚠️  Labeling interrupted. Saving progress...")
            self._save_labeled_data()
            print("Progress saved. You can resume later.")
            return
        
        total_time = time.time() - total_start
        
        self._print_final_statistics(total_time)
        self._save_labeled_data()
    
    def _label_entire_project(self, project_id: str, manager):
        print(f"\n📁 PROJECT: {project_id}")
        print("="*60)
        
        with manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            print(f"Found {len(datasets)} datasets\n")
            
            for dataset_idx, dataset in enumerate(datasets, 1):
                dataset_id = dataset.dataset_id if hasattr(dataset, 'dataset_id') else str(dataset).split('.')[-1]
                print(f"\n📂 Dataset [{dataset_idx}/{len(datasets)}]: {dataset_id}")
                print("-"*50)
                
                try:
                    tables = list(client.list_tables(f"{project_id}.{dataset_id}"))
                    print(f"Found {len(tables)} tables")
                    
                    for table_idx, table_ref in enumerate(tables, 1):
                        table_id = table_ref.table_id if hasattr(table_ref, 'table_id') else str(table_ref).split('.')[-1]
                        table_path = f"{project_id}.{dataset_id}.{table_id}"
                        
                        print(f"\n📊 Table [{table_idx}/{len(tables)}]: {table_id}")
                        
                        if table_path in self.labeled_columns.get('columns', {}):
                            print("  ✓ Already labeled, skipping...")
                            continue
                        
                        self._label_table_manually(client, table_path)
                        self.statistics['total_tables'] += 1
                        
                        if self.statistics['total_tables'] % 5 == 0:
                            self._save_labeled_data()
                            print("  💾 Progress saved")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process dataset {dataset_id}: {e}")
    
    def _label_table_manually(self, client, table_path: str):
        try:
            table = client.get_table(table_path)
            
            if table.num_rows == 0:
                print("  (Empty table, skipping)")
                return
            
            columns = [field.name for field in table.schema]
            print(f"  {len(columns)} columns, {table.num_rows:,} rows")
            
            sample_data = None
            try:
                query = f"""
                SELECT *
                FROM `{table_path}`
                LIMIT 5
                """
                query_job = client.query(query)
                results = list(query_job.result(timeout=30))
                
                sample_data = []
                for row in results:
                    row_dict = {}
                    for col in columns:
                        try:
                            row_dict[col] = getattr(row, col, None)
                        except:
                            row_dict[col] = None
                    sample_data.append(row_dict)
            except Exception as e:
                logger.debug(f"Could not get sample data: {e}")
                sample_data = []
            
            table_labels = {}
            
            for col_idx, column in enumerate(columns, 1):
                print(f"\n  Column [{col_idx}/{len(columns)}]: {column}")
                
                if sample_data:
                    print("  Sample values:")
                    for i, row in enumerate(sample_data[:5], 1):
                        value = row.get(column)
                        if value is not None:
                            value_str = str(value)[:100]
                            print(f"    {i}. {value_str}")
                        else:
                            print(f"    {i}. (null)")
                else:
                    print("  (No sample data available)")
                
                while True:
                    try:
                        choice = input("\n  Label (1-17 or 18 to skip): ").strip()
                        
                        if not choice:
                            print("  Please enter a number")
                            continue
                        
                        choice_num = int(choice)
                        
                        if choice_num in self.column_types:
                            label = self.column_types[choice_num]
                            table_labels[column] = label
                            
                            if label != 'skip':
                                print(f"  ✓ Labeled as: {label}")
                                self.statistics['labeled_columns'] += 1
                            else:
                                print("  ✓ Skipped")
                                self.statistics['skipped_columns'] += 1
                            
                            self.statistics['total_columns'] += 1
                            break
                        else:
                            print("  Invalid choice. Please enter 1-18")
                    
                    except ValueError:
                        print("  Please enter a valid number")
                    except KeyboardInterrupt:
                        raise
            
            self.labeled_columns['columns'][table_path] = table_labels
            
            self.labeled_columns['labeling_history'].append({
                'table': table_path,
                'labels': table_labels,
                'timestamp': datetime.now().isoformat(),
                'rows': table.num_rows
            })
            
            for column, label in table_labels.items():
                if label != 'skip':
                    self.labeled_columns['patterns'][label].append({
                        'column': column,
                        'table': table_path
                    })
            
            print(f"\n  ✅ Table labeled successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error labeling table {table_path}: {e}")
    
    def _print_final_statistics(self, total_time: float):
        print("\n" + "="*80)
        print("LABELING COMPLETE")
        print("="*80)
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"Tables processed: {self.statistics['total_tables']}")
        print(f"Columns analyzed: {self.statistics['total_columns']}")
        print(f"Columns labeled: {self.statistics['labeled_columns']}")
        print(f"Columns skipped: {self.statistics['skipped_columns']}")
        
        if self.statistics['total_columns'] > 0:
            print(f"Labeling rate: {self.statistics['labeled_columns']/self.statistics['total_columns']*100:.1f}%")
        
        print("\nColumn type distribution:")
        type_counts = defaultdict(int)
        for table_labels in self.labeled_columns['columns'].values():
            for label in table_labels.values():
                if label != 'skip':
                    type_counts[label] += 1
        
        for col_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {col_type:30} {count:6}")
        
        self.labeled_columns['statistics'] = {
            'total_tables': self.statistics['total_tables'],
            'total_columns': self.statistics['total_columns'],
            'labeled_columns': self.statistics['labeled_columns'],
            'skipped_columns': self.statistics['skipped_columns'],
            'processing_time_minutes': total_time/60,
            'projects': self.project_ids,
            'type_distribution': dict(type_counts)
        }

def main():
    labeler = ManualCompleteLabeler()
    
    print("\nThis will label every column in every table across both projects.")
    print("You can press Ctrl+C at any time to pause and save progress.")
    
    confirm = input("\nReady to start? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    labeler.label_all_tables_manually()
    
    print("\n✅ Labeling complete!")
    print(f"📁 Results saved to: manual_labeled_columns.json")

if __name__ == "__main__":
    main()