#!/usr/bin/env python3
"""
Script to review specific high-value tables and their columns
Allows users to decide (1=yes, 2=no) whether to include each column in the labeled dataset
Focuses on key security and infrastructure tables:
- CrowdStrike (V_DIM_ENDPOINTAGENT)
- CMDB (V_DIM_ENDPOINT) 
- Splunk (V_SPL_ENDPOINT_LOG)
- Chronicle (events)
"""

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

class SpecificTableReviewer:
    def __init__(self):
        # Target tables with their descriptions
        self.target_tables = {
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINTAGENT': {
                'description': 'CrowdStrike Endpoint Agent Data',
                'category': 'security',
                'priority': 'high'
            },
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINT': {
                'description': 'CMDB Endpoint Data',
                'category': 'cmdb',
                'priority': 'critical'
            },
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG': {
                'description': 'Splunk Endpoint Logging Data',
                'category': 'logging',
                'priority': 'high'
            },
            'chronicle-fisv.datalake.events': {
                'description': 'Chronicle Security Events',
                'category': 'security_events',
                'priority': 'critical'
            }
        }
        
        # Column type mapping (same as auto_labeler)
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
        
        # Output files
        self.labeled_data_path = Path('specific_tables_labeled.json')
        self.model_path = Path('specific_tables_classifier.pkl')
        
        # Initialize data structure
        self.labeled_columns = self._load_labeled_data()
        
        # Statistics tracking
        self.statistics = {
            'total_tables_processed': 0,
            'total_columns_reviewed': 0,
            'columns_labeled': 0,
            'columns_skipped': 0,
            'tables_completed': [],
            'tables_failed': [],
            'start_time': datetime.now()
        }
        
        # Connect to projects
        self.client_managers = {}
        self._connect_to_projects()
    
    def _connect_to_projects(self):
        """Connect to the required projects"""
        # Extract unique project IDs from target tables
        project_ids = set()
        for table_path in self.target_tables.keys():
            project_id = table_path.split('.')[0]
            project_ids.add(project_id)
        
        logger.info(f"Connecting to projects: {list(project_ids)}")
        
        for project_id in project_ids:
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
            raise RuntimeError("Failed to connect to any required projects")
    
    def _load_labeled_data(self) -> Dict[str, Any]:
        """Load existing labeled data or create new structure"""
        if self.labeled_data_path.exists():
            with open(self.labeled_data_path, 'r') as f:
                return json.load(f)
        
        return {
            'metadata': {
                'creation_timestamp': datetime.now().isoformat(),
                'source': 'specific_table_reviewer',
                'target_tables': list(self.target_tables.keys())
            },
            'columns': {},
            'patterns': defaultdict(list),
            'labeling_history': [],
            'statistics': {},
            'table_info': {}
        }
    
    def _save_labeled_data(self):
        """Save labeled data to file"""
        with open(self.labeled_data_path, 'w') as f:
            json.dump(self.labeled_columns, f, indent=2, default=str)
        logger.info(f"💾 Saved labeled data to {self.labeled_data_path}")
    
    def review_all_target_tables(self):
        """Review all target tables interactively"""
        print("\n" + "="*80)
        print("SPECIFIC HIGH-VALUE TABLE REVIEWER")
        print("="*80)
        print("Review columns from key security and infrastructure tables")
        print("\nTarget Tables:")
        for i, (table_path, info) in enumerate(self.target_tables.items(), 1):
            print(f"  {i}. {info['description']}")
            print(f"     Table: {table_path}")
            print(f"     Category: {info['category']} | Priority: {info['priority']}")
        
        print("\nColumn Types:")
        for num, col_type in self.column_types.items():
            if num % 6 == 1:
                print()
            print(f"{num:2}. {col_type:20}", end="  ")
        print("\n\n" + "="*80)
        
        # Ask for confirmation
        confirm = input("\nReady to start reviewing? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Review cancelled.")
            return
        
        # Process each table
        for i, (table_path, table_info) in enumerate(self.target_tables.items(), 1):
            print(f"\n" + "="*70)
            print(f"TABLE {i}/{len(self.target_tables)}: {table_info['description']}")
            print("="*70)
            print(f"Path: {table_path}")
            print(f"Category: {table_info['category']} | Priority: {table_info['priority']}")
            
            try:
                if table_path in self.labeled_columns.get('columns', {}):
                    print("✓ Already reviewed, skipping...")
                    continue
                
                success = self._review_table(table_path, table_info)
                if success:
                    self.statistics['tables_completed'].append(table_path)
                else:
                    self.statistics['tables_failed'].append(table_path)
                
                self.statistics['total_tables_processed'] += 1
                self._save_labeled_data()
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Review interrupted. Saving progress...")
                self._save_labeled_data()
                self._print_final_statistics()
                return
            except Exception as e:
                logger.error(f"❌ Failed to process {table_path}: {e}")
                self.statistics['tables_failed'].append(table_path)
        
        self._print_final_statistics()
        self._save_labeled_data()
    
    def _review_table(self, table_path: str, table_info: Dict[str, Any]) -> bool:
        """Review a specific table and its columns"""
        project_id = table_path.split('.')[0]
        manager = self.client_managers.get(project_id)
        
        if not manager:
            logger.error(f"No client manager for project {project_id}")
            return False
        
        try:
            with manager.get_client() as client:
                # Get table metadata
                table = client.get_table(table_path)
                
                if table.num_rows == 0:
                    print("  (Empty table, skipping)")
                    return True
                
                columns = [field.name for field in table.schema]
                print(f"  📊 {len(columns)} columns, {table.num_rows:,} rows")
                
                # Store table information
                self.labeled_columns['table_info'][table_path] = {
                    'description': table_info['description'],
                    'category': table_info['category'],
                    'priority': table_info['priority'],
                    'num_rows': table.num_rows,
                    'num_columns': len(columns),
                    'schema_fields': [
                        {
                            'name': field.name,
                            'type': field.field_type,
                            'mode': field.mode,
                            'description': field.description
                        } for field in table.schema
                    ]
                }
                
                # Get sample data
                sample_data = self._get_sample_data(client, table_path, columns)
                
                # Review each column
                table_labels = {}
                
                for col_idx, column in enumerate(columns, 1):
                    print(f"\n  Column [{col_idx}/{len(columns)}]: {column}")
                    
                    # Show column metadata
                    field = next((f for f in table.schema if f.name == column), None)
                    if field:
                        print(f"    Type: {field.field_type}")
                        if field.description:
                            print(f"    Description: {field.description}")
                        if field.mode:
                            print(f"    Mode: {field.mode}")
                    
                    # Show sample values
                    if sample_data:
                        print("    Sample values:")
                        sample_values = []
                        for i, row in enumerate(sample_data[:8], 1):
                            value = row.get(column)
                            if value is not None:
                                value_str = str(value)[:100]
                                print(f"      {i}. {value_str}")
                                sample_values.append(value_str)
                            else:
                                print(f"      {i}. (null)")
                                sample_values.append(None)
                    else:
                        print("    (No sample data available)")
                        sample_values = []
                    
                    # Get user decision
                    while True:
                        try:
                            print("\n    Options:")
                            print("      1-17: Label with specific type")
                            print("      18: Skip this column")
                            print("      0: Show column types again")
                            print("      s: Skip this table")
                            
                            choice = input(f"\n    Decision for '{column}': ").strip()
                            
                            if choice == '0':
                                self._show_column_types()
                                continue
                            
                            if choice.lower() == 's':
                                print("    ⏭️ Skipping entire table")
                                return False
                            
                            choice_num = int(choice)
                            
                            if choice_num in self.column_types:
                                label = self.column_types[choice_num]
                                table_labels[column] = label
                                
                                if label != 'skip':
                                    print(f"    ✓ Labeled as: {label}")
                                    self.statistics['columns_labeled'] += 1
                                    
                                    # Store pattern information
                                    self.labeled_columns['patterns'][label].append({
                                        'column': column,
                                        'table': table_path,
                                        'samples': sample_values[:5],
                                        'table_category': table_info['category']
                                    })
                                else:
                                    print("    ✓ Skipped")
                                    self.statistics['columns_skipped'] += 1
                                
                                self.statistics['total_columns_reviewed'] += 1
                                break
                            else:
                                print("    Invalid choice. Please enter 1-18, 0, or 's'")
                        
                        except ValueError:
                            print("    Please enter a valid number or 's'")
                        except KeyboardInterrupt:
                            raise
                
                # Store table labels
                self.labeled_columns['columns'][table_path] = table_labels
                
                # Add to labeling history
                self.labeled_columns['labeling_history'].append({
                    'table': table_path,
                    'table_info': table_info,
                    'labels': table_labels,
                    'timestamp': datetime.now().isoformat(),
                    'rows': table.num_rows,
                    'columns_labeled': len([l for l in table_labels.values() if l != 'skip']),
                    'columns_skipped': len([l for l in table_labels.values() if l == 'skip'])
                })
                
                print(f"\n  ✅ Table '{table_info['description']}' labeled successfully!")
                print(f"    Columns labeled: {len([l for l in table_labels.values() if l != 'skip'])}")
                print(f"    Columns skipped: {len([l for l in table_labels.values() if l == 'skip'])}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error processing table {table_path}: {e}")
            return False
    
    def _get_sample_data(self, client, table_path: str, columns: List[str]) -> List[Dict[str, Any]]:
        """Get sample data from the table"""
        try:
            # Build safe column names
            safe_columns = [f"`{col}`" for col in columns]
            
            query = f"""
            SELECT {', '.join(safe_columns)}
            FROM `{table_path}`
            WHERE RAND() < 0.01  -- Sample 1% of data
            LIMIT 10
            """
            
            query_job = client.query(query)
            results = list(query_job.result(timeout=60))
            
            sample_data = []
            for row in results:
                row_dict = {}
                for col in columns:
                    try:
                        value = getattr(row, col, None)
                        row_dict[col] = value
                    except:
                        row_dict[col] = None
                sample_data.append(row_dict)
            
            return sample_data
            
        except Exception as e:
            logger.debug(f"Failed to get sample data for {table_path}: {e}")
            return []
    
    def _show_column_types(self):
        """Display column types"""
        print("\n    Column Types:")
        for num, col_type in self.column_types.items():
            if num % 6 == 1:
                print()
            print(f"    {num:2}. {col_type:20}", end="  ")
        print()
    
    def _print_final_statistics(self):
        """Print final statistics"""
        total_time = (datetime.now() - self.statistics['start_time']).total_seconds()
        
        print("\n" + "="*80)
        print("SPECIFIC TABLE REVIEW COMPLETE")
        print("="*80)
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"Tables processed: {self.statistics['total_tables_processed']}")
        print(f"Tables completed: {len(self.statistics['tables_completed'])}")
        print(f"Tables failed: {len(self.statistics['tables_failed'])}")
        print(f"Columns reviewed: {self.statistics['total_columns_reviewed']}")
        print(f"Columns labeled: {self.statistics['columns_labeled']}")
        print(f"Columns skipped: {self.statistics['columns_skipped']}")
        
        if self.statistics['total_columns_reviewed'] > 0:
            label_rate = (self.statistics['columns_labeled'] / self.statistics['total_columns_reviewed']) * 100
            print(f"Labeling rate: {label_rate:.1f}%")
        
        print("\nTables completed:")
        for table in self.statistics['tables_completed']:
            table_info = self.target_tables.get(table, {})
            print(f"  ✓ {table_info.get('description', table)}")
        
        if self.statistics['tables_failed']:
            print("\nTables failed:")
            for table in self.statistics['tables_failed']:
                table_info = self.target_tables.get(table, {})
                print(f"  ✗ {table_info.get('description', table)}")
        
        print("\nColumn type distribution:")
        type_counts = defaultdict(int)
        for table_labels in self.labeled_columns['columns'].values():
            for label in table_labels.values():
                if label != 'skip':
                    type_counts[label] += 1
        
        for col_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {col_type:30} {count:6}")
        
        # Update final statistics in data
        self.labeled_columns['statistics'] = {
            'total_tables_processed': self.statistics['total_tables_processed'],
            'total_columns_reviewed': self.statistics['total_columns_reviewed'],
            'columns_labeled': self.statistics['columns_labeled'],
            'columns_skipped': self.statistics['columns_skipped'],
            'processing_time_minutes': total_time/60,
            'tables_completed': self.statistics['tables_completed'],
            'tables_failed': self.statistics['tables_failed'],
            'type_distribution': dict(type_counts),
            'completion_timestamp': datetime.now().isoformat()
        }
    
    def show_current_progress(self):
        """Show current progress"""
        print("\n" + "="*60)
        print("CURRENT PROGRESS")
        print("n" + "="*60)
        
        completed_tables = len(self.labeled_columns.get('columns', {}))
        total_tables = len(self.target_tables)
        
        print(f"Tables completed: {completed_tables}/{total_tables}")
        
        for table_path, table_info in self.target_tables.items():
            status = "✓ Completed" if table_path in self.labeled_columns.get('columns', {}) else "⏳ Pending"
            print(f"  {status} {table_info['description']}")
        
        if completed_tables > 0:
            total_columns = sum(len(labels) for labels in self.labeled_columns['columns'].values())
            labeled_columns = sum(1 for labels in self.labeled_columns['columns'].values() 
                                for label in labels.values() if label != 'skip')
            
            print(f"\nColumns reviewed: {total_columns}")
            print(f"Columns labeled: {labeled_columns}")
            print(f"Columns skipped: {total_columns - labeled_columns}")

def main():
    """Main entry point"""
    reviewer = SpecificTableReviewer()
    
    print("\nThis will review specific high-value tables for column labeling.")
    print("You can press Ctrl+C at any time to pause and save progress.")
    
    # Check current progress
    if reviewer.labeled_columns.get('columns'):
        print("\nFound existing progress:")
        reviewer.show_current_progress()
        
        resume = input("\nContinue from where you left off? (y/n): ").lower().strip()
        if resume != 'y':
            print("Starting fresh review.")
            reviewer.labeled_columns = reviewer._load_labeled_data()
    
    # Start the review process
    reviewer.review_all_target_tables()
    
    print(f"\n✅ Review complete!")
    print(f"📁 Results saved to: {reviewer.labeled_data_path}")

if __name__ == "__main__":
    main()