def _show_column_types(self):
        """Display column types"""
        print("\n    📋 Column Types Reference:")
        print("    " + "="*60)
        
        categories = {
            "Identity & Location": [(1, 'host'), (17, 'domain')],
            "Infrastructure": [(2, 'infrastructure_type'), (11, 'system_classification')],
            "Geography": [(3, 'region'), (4, 'country'), (5, 'data_center'), (6, 'cloud_region')],
            "Organization": [(7, 'business_unit'), (8, 'cio'), (10, 'app_class')],
            "Security Tools": [(12, 'edr_coverage'), (13, 'tanium_coverage'), (14, 'dlp_agent_coverage')],
            "Logging": [(15, 'logging_in_splunk'), (16, 'logging_in_gso')],
            "Monitoring": [(9, 'apm')],
            "Other": [(18, 'skip')]
        }
        
        for category, items in categories.items():
            print(f"\n    {category}:")
            for num, col_type in items:
                print(f"      {num:2}. {col_type}")
        
        print("    " + "="*60)#!/usr/bin/env python3
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
    
    def test_table_access(self):
        """Test access to all target tables"""
        print("\n" + "="*60)
        print("TESTING TABLE ACCESS")
        print("="*60)
        
        for table_path, table_info in self.target_tables.items():
            project_id = table_path.split('.')[0]
            manager = self.client_managers.get(project_id)
            
            print(f"\n📋 Testing: {table_info['description']}")
            print(f"   Path: {table_path}")
            
            if not manager:
                print(f"   ❌ No client manager for project {project_id}")
                continue
            
            try:
                with manager.get_client() as client:
                    # Test if table exists and get basic info
                    table = client.get_table(table_path)
                    print(f"   ✅ Table exists")
                    print(f"   📊 Reported rows: {table.num_rows:,}" if table.num_rows else "   📊 Reported rows: Unknown")
                    print(f"   📏 Columns: {len(table.schema)}")
                    print(f"   🏷️ Table type: {table.table_type}")
                    
                    # Test a simple query
                    try:
                        query = f"SELECT COUNT(*) as row_count FROM `{table_path}`"
                        print(f"   🔍 Testing query: {query}")
                        query_job = client.query(query)
                        result = list(query_job.result(timeout=30))
                        actual_rows = result[0].row_count if result else 0
                        print(f"   🔢 Actual row count: {actual_rows:,}")
                        
                        if actual_rows > 0:
                            print(f"   ✅ Table has data and is queryable")
                        else:
                            print(f"   ⚠️ Table is empty")
                        
                    except Exception as e:
                        print(f"   ❌ Query test failed: {str(e)}")
                        print(f"   📋 Error type: {type(e).__name__}")
                        
                        # Check if it's a permission error
                        if "403" in str(e) or "permission" in str(e).lower() or "access" in str(e).lower():
                            print(f"   🔒 This appears to be a permissions issue")
                            print(f"   💡 You may need BigQuery Data Viewer role or table-specific access")
                        elif "not found" in str(e).lower():
                            print(f"   🔍 Table path might be incorrect or table doesn't exist")
                        else:
                            print(f"   🤔 Unexpected error - continuing anyway")
                        
                        # Try to proceed with schema-only review
                        print(f"   🎯 Will attempt schema-only review (no sample data)")
                        
            except Exception as e:
                print(f"   ❌ Table access failed: {e}")
    
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
                
                print(f"  📋 Table info:")
                print(f"    Rows: {table.num_rows:,}" if table.num_rows else "    Rows: Unknown")
                print(f"    Size: {table.num_bytes:,} bytes" if table.num_bytes else "    Size: Unknown")
                print(f"    Created: {table.created}" if table.created else "    Created: Unknown")
                print(f"    Modified: {table.modified}" if table.modified else "    Modified: Unknown")
                
                # Don't skip based on num_rows being 0, as it might be inaccurate for views
                if table.num_rows is not None and table.num_rows == 0:
                    print("  ⚠️ Table reports 0 rows, but this might be a view - continuing anyway...")
                
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
                print("  🔍 Attempting to get sample data...")
                sample_data = self._get_sample_data(client, table_path, columns)
                
                if not sample_data:
                    print("  ⚠️ Could not retrieve sample data, but proceeding with column review")
                    print("    You can still label columns based on names and schema information")
                else:
                    print(f"  ✅ Retrieved {len(sample_data)} sample rows for analysis")
                
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
                    
                    # Analyze column for hints even without good sample data
                    column_hints = self._analyze_column_hints(column, field, sample_data)
                    
                    # Show column analysis
                    print(f"    🔍 Column Analysis:")
                    if field:
                        print(f"      Type: {field.field_type}")
                        if field.mode:
                            print(f"      Mode: {field.mode}")
                        if field.description:
                            print(f"      Description: {field.description}")
                    
                    # Show intelligent suggestions
                    suggestions = column_hints.get('suggestions', [])
                    if suggestions:
                        print(f"    💡 Suggested labels:")
                        for i, (label_num, label_name, reason) in enumerate(suggestions[:3], 1):
                            print(f"      {label_num}. {label_name} - {reason}")
                    
                    # Show sample values with better handling
                    if sample_data:
                        print("    📋 Sample values:")
                        sample_values = []
                        actual_values = 0
                        
                        for i, row in enumerate(sample_data[:5], 1):
                            value = row.get(column)
                            if value is not None and value != "<not sampled>":
                                value_str = str(value)[:100]
                                
                                # Check if value looks encrypted/hashed
                                if self._looks_encrypted_or_hashed(value_str):
                                    print(f"      {i}. {value_str[:20]}... (appears encrypted/hashed)")
                                elif len(value_str) == 0:
                                    print(f"      {i}. (empty string)")
                                else:
                                    print(f"      {i}. {value_str}")
                                    actual_values += 1
                                sample_values.append(value_str)
                            else:
                                print(f"      {i}. (null)")
                                sample_values.append(None)
                        
                        if actual_values == 0:
                            print("      ⚠️ All values appear to be null, empty, or encrypted")
                    else:
                        print("    ⚠️ No sample data available")
                        sample_values = []
                    
                    print(f"    📋 Base your decision on:")
                    print(f"      • Column name: '{column}'")
                    print(f"      • Data type: {field.field_type if field else 'unknown'}")
                    print(f"      • Table context: {table_info['description']}")
                    if suggestions:
                        print(f"      • AI suggestions above")
                    
                    # Get user decision
                    while True:
                        try:
                            print("\n    📋 Labeling Options:")
                            print("      1-17: Label with specific column type")
                            print("      18: Skip this column") 
                            print("      0: Show column types reference")
                            print("      s: Skip this entire table")
                            print("      i: Show detailed column info")
                            if suggestions:
                                print("      auto: Use first AI suggestion")
                            
                            choice = input(f"\n    🏷️ Label for '{column}': ").strip()
                            
                            if choice == '0':
                                self._show_column_types()
                                continue
                            
                            if choice.lower() == 's':
                                print("    ⏭️ Skipping entire table")
                                return False
                            
                            if choice.lower() == 'i':
                                # Show additional column info
                                print(f"\n    📋 Detailed Info for '{column}':")
                                print(f"      Column Name: {column}")
                                if field:
                                    print(f"      Data Type: {field.field_type}")
                                    print(f"      Mode: {field.mode}")
                                    if field.description:
                                        print(f"      Description: {field.description}")
                                    if hasattr(field, 'fields') and field.fields:
                                        print(f"      Nested fields: {[f.name for f in field.fields]}")
                                
                                # Show context
                                print(f"      Table: {table_info['description']} ({table_info['category']})")
                                print(f"      Position: Column {col_idx} of {len(columns)}")
                                
                                # Show name analysis
                                print(f"\n      🔍 Name Analysis:")
                                name_parts = column.lower().replace('_', ' ').split()
                                print(f"      Word parts: {name_parts}")
                                
                                # Show similar columns from other tables
                                similar_cols = self._find_similar_columns(column)
                                if similar_cols:
                                    print(f"\n      🔗 Similar columns in other tables:")
                                    for sim_col, sim_table, sim_label in similar_cols[:3]:
                                        print(f"        '{sim_col}' in {sim_table} → labeled as '{sim_label}'")
                                
                                continue
                            
                            if choice.lower() == 'auto':
                                # Auto-label based on suggestions
                                if suggestions:
                                    auto_choice = suggestions[0][0]  # Take first suggestion
                                    choice_num = auto_choice
                                    print(f"    🤖 Auto-selected: {suggestions[0][1]} (suggestion #{auto_choice})")
                                else:
                                    print("    ❌ No auto-suggestions available")
                                    continue
                            else:
                                choice_num = int(choice)
                            
                            if choice_num in self.column_types:
                                label = self.column_types[choice_num]
                                table_labels[column] = label
                                
                                if label != 'skip':
                                    print(f"    ✅ Labeled as: {label}")
                                    self.statistics['columns_labeled'] += 1
                                    
                                    # Store pattern information
                                    self.labeled_columns['patterns'][label].append({
                                        'column': column,
                                        'table': table_path,
                                        'samples': sample_values[:5] if 'sample_values' in locals() else [],
                                        'table_category': table_info['category'],
                                        'field_type': field.field_type if field else 'unknown',
                                        'has_sample_data': bool(sample_data)
                                    })
                                else:
                                    print("    ⏭️ Skipped")
                                    self.statistics['columns_skipped'] += 1
                                
                                self.statistics['total_columns_reviewed'] += 1
                                break
                            else:
                                print("    ❌ Invalid choice. Please enter 1-18, 0, 's', 'i', or 'auto'")
                        
                        except ValueError:
                            print("    ❌ Please enter a valid number, 's', 'i', or 'auto'")
    def _find_similar_columns(self, column_name: str) -> List[Tuple[str, str, str]]:
        """Find similar columns that have already been labeled"""
        similar = []
        column_lower = column_name.lower()
        
        for table_path, table_labels in self.labeled_columns.get('columns', {}).items():
            for col_name, label in table_labels.items():
                if col_name.lower() == column_lower:
                    # Exact match
                    similar.append((col_name, table_path, label))
                elif any(word in col_name.lower() for word in column_lower.split('_')):
                    # Partial word match
                    similar.append((col_name, table_path, label))
        
        return similar[:5]  # Return top 5 matches
                
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
        """Get sample data from the table using multiple fallback strategies"""
        sample_data = []
        
        # Strategy 1: Simple LIMIT query (most reliable)
        try:
            # Limit to first 10 columns to avoid complex types
            safe_columns = []
            for col in columns[:10]:
                safe_columns.append(f"`{col}`")
            
            query = f"""
            SELECT {', '.join(safe_columns)}
            FROM `{table_path}`
            LIMIT 5
            """
            
            logger.info(f"🔍 Trying simple LIMIT query for {table_path}")
            print(f"    🔍 Query: {query}")
            
            query_job = client.query(query)
            results = list(query_job.result(timeout=45))
            
            for row in results:
                row_dict = {}
                for col in columns[:10]:
                    try:
                        value = getattr(row, col, None)
                        # Convert complex types to strings
                        if value is not None:
                            if isinstance(value, (dict, list)):
                                row_dict[col] = str(value)[:200]
                            else:
                                row_dict[col] = str(value)[:200]
                        else:
                            row_dict[col] = None
                    except Exception as e:
                        logger.debug(f"Error getting column {col}: {e}")
                        row_dict[col] = f"<error: {type(e).__name__}>"
                sample_data.append(row_dict)
            
            if sample_data:
                logger.info(f"✅ Got {len(sample_data)} sample rows using simple LIMIT")
                return sample_data
                
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Simple LIMIT query failed for {table_path}: {error_msg}")
            print(f"    ❌ Simple query failed: {error_msg}")
            
            # Check for specific error types
            if "403" in error_msg or "permission" in error_msg.lower():
                print(f"    🔒 Permission denied - you may not have query access to this table")
                return []
            elif "timeout" in error_msg.lower():
                print(f"    ⏰ Query timeout - table might be very large")
            elif "not found" in error_msg.lower():
                print(f"    🔍 Table not found - check table path")
                return []
        
        # Strategy 2: Try selecting just one column
        try:
            if columns:
                first_col = columns[0]
                query = f"""
                SELECT `{first_col}`
                FROM `{table_path}`
                LIMIT 3
                """
                
                logger.info(f"🔍 Trying single column query for {table_path}")
                print(f"    🔍 Trying single column: {first_col}")
                
                query_job = client.query(query)
                results = list(query_job.result(timeout=30))
                
                for row in results:
                    row_dict = {}
                    try:
                        value = getattr(row, first_col, None)
                        row_dict[first_col] = str(value)[:200] if value is not None else None
                        # Fill other columns with placeholder
                        for col in columns[1:]:
                            row_dict[col] = "<not sampled>"
                    except:
                        row_dict[first_col] = "<error>"
                    sample_data.append(row_dict)
                
                if sample_data:
                    logger.info(f"✅ Got {len(sample_data)} sample rows using single column")
                    print(f"    ✅ Single column sampling worked")
                    return sample_data
                    
        except Exception as e:
            logger.warning(f"Single column query failed for {table_path}: {e}")
            print(f"    ❌ Single column query also failed: {e}")
        
        # Strategy 3: Return empty but don't fail
        logger.error(f"❌ All sampling strategies failed for {table_path}")
        print(f"    ⚠️ Cannot access table data - proceeding with schema-only review")
        return []
    
    def _looks_encrypted_or_hashed(self, value: str) -> bool:
        """Check if a value looks encrypted, hashed, or obfuscated"""
        if not value or len(value) < 10:
            return False
        
        # Common hash/encryption patterns
        patterns = [
            r'^[a-f0-9]{32}
    
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
    
    print("\nSpecific Table Reviewer - High-Value Security & Infrastructure Tables")
    
    # Test table access first
    print("\nTesting access to target tables...")
    reviewer.test_table_access()
    
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
    
    # Ask if user wants to proceed after seeing test results
    proceed = input("\nProceed with the review? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Review cancelled.")
        return
    
    # Start the review process
    reviewer.review_all_target_tables()
    
    print(f"\n✅ Review complete!")
    print(f"📁 Results saved to: {reviewer.labeled_data_path}")

if __name__ == "__main__":
    main(),  # MD5
            r'^[a-f0-9]{40}
    
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
    
    print("\nSpecific Table Reviewer - High-Value Security & Infrastructure Tables")
    
    # Test table access first
    print("\nTesting access to target tables...")
    reviewer.test_table_access()
    
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
    
    # Ask if user wants to proceed after seeing test results
    proceed = input("\nProceed with the review? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Review cancelled.")
        return
    
    # Start the review process
    reviewer.review_all_target_tables()
    
    print(f"\n✅ Review complete!")
    print(f"📁 Results saved to: {reviewer.labeled_data_path}")

if __name__ == "__main__":
    main(),  # SHA1
            r'^[a-f0-9]{64}
    
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
    
    print("\nSpecific Table Reviewer - High-Value Security & Infrastructure Tables")
    
    # Test table access first
    print("\nTesting access to target tables...")
    reviewer.test_table_access()
    
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
    
    # Ask if user wants to proceed after seeing test results
    proceed = input("\nProceed with the review? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Review cancelled.")
        return
    
    # Start the review process
    reviewer.review_all_target_tables()
    
    print(f"\n✅ Review complete!")
    print(f"📁 Results saved to: {reviewer.labeled_data_path}")

if __name__ == "__main__":
    main(),  # SHA256
            r'^[A-Za-z0-9+/]{20,}={0,2}
    
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
    
    print("\nSpecific Table Reviewer - High-Value Security & Infrastructure Tables")
    
    # Test table access first
    print("\nTesting access to target tables...")
    reviewer.test_table_access()
    
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
    
    # Ask if user wants to proceed after seeing test results
    proceed = input("\nProceed with the review? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Review cancelled.")
        return
    
    # Start the review process
    reviewer.review_all_target_tables()
    
    print(f"\n✅ Review complete!")
    print(f"📁 Results saved to: {reviewer.labeled_data_path}")

if __name__ == "__main__":
    main(),  # Base64
            r'^[A-Za-z0-9\-_]{20,}
    
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
    
    print("\nSpecific Table Reviewer - High-Value Security & Infrastructure Tables")
    
    # Test table access first
    print("\nTesting access to target tables...")
    reviewer.test_table_access()
    
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
    
    # Ask if user wants to proceed after seeing test results
    proceed = input("\nProceed with the review? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Review cancelled.")
        return
    
    # Start the review process
    reviewer.review_all_target_tables()
    
    print(f"\n✅ Review complete!")
    print(f"📁 Results saved to: {reviewer.labeled_data_path}")

if __name__ == "__main__":
    main(),  # URL-safe base64 or tokens
        ]
        
        for pattern in patterns:
            if re.match(pattern, value):
                return True
        
        # Check for high entropy (random-looking strings)
        unique_chars = len(set(value.lower()))
        if len(value) > 20 and unique_chars > len(value) * 0.6:
            return True
        
        return False
    
    def _analyze_column_hints(self, column_name: str, field, sample_data: List[Dict]) -> Dict[str, Any]:
        """Analyze column to provide intelligent labeling suggestions"""
        suggestions = []
        column_lower = column_name.lower()
        
        # Host/hostname patterns
        if any(term in column_lower for term in ['host', 'computer', 'machine', 'device', 'endpoint', 'system', 'server', 'node']):
            suggestions.append((1, 'host', f"Column name contains host-related terms"))
        
        # Infrastructure patterns
        if any(term in column_lower for term in ['infra', 'platform', 'deploy', 'env', 'environment']):
            suggestions.append((2, 'infrastructure_type', f"Column name suggests infrastructure classification"))
        
        # Geographic patterns
        if any(term in column_lower for term in ['region', 'location', 'geo', 'zone', 'area']):
            suggestions.append((3, 'region', f"Column name suggests geographic location"))
        
        if any(term in column_lower for term in ['country', 'nation', 'ctry']):
            suggestions.append((4, 'country', f"Column name suggests country"))
        
        # Datacenter patterns
        if any(term in column_lower for term in ['datacenter', 'data_center', 'dc', 'facility', 'site']):
            suggestions.append((5, 'data_center', f"Column name suggests datacenter"))
        
        # Cloud patterns
        if any(term in column_lower for term in ['cloud', 'aws', 'azure', 'gcp', 'availability']):
            suggestions.append((6, 'cloud_region', f"Column name suggests cloud infrastructure"))
        
        # Business patterns
        if any(term in column_lower for term in ['business', 'bu', 'org', 'department', 'div', 'unit']):
            suggestions.append((7, 'business_unit', f"Column name suggests organizational unit"))
        
        # Technical ownership patterns
        if any(term in column_lower for term in ['cio', 'it_org', 'tech']):
            suggestions.append((8, 'cio', f"Column name suggests IT organization"))
        
        # Monitoring patterns
        if any(term in column_lower for term in ['apm', 'monitor', 'performance', 'health']):
            suggestions.append((9, 'apm', f"Column name suggests monitoring/APM"))
        
        # Application patterns
        if any(term in column_lower for term in ['app', 'application', 'service', 'class']):
            suggestions.append((10, 'app_class', f"Column name suggests application classification"))
        
        # System classification patterns
        if any(term in column_lower for term in ['system', 'sys', 'os', 'operating', 'classification']):
            suggestions.append((11, 'system_classification', f"Column name suggests system type"))
        
        # Security tool patterns
        if any(term in column_lower for term in ['edr', 'endpoint', 'crowdstrike', 'falcon', 'security']):
            suggestions.append((12, 'edr_coverage', f"Column name suggests EDR/endpoint security"))
        
        if any(term in column_lower for term in ['tanium', 'endpoint_platform', 'management']):
            suggestions.append((13, 'tanium_coverage', f"Column name suggests Tanium coverage"))
        
        if any(term in column_lower for term in ['dlp', 'data_loss', 'protection', 'leak']):
            suggestions.append((14, 'dlp_agent_coverage', f"Column name suggests DLP coverage"))
        
        if any(term in column_lower for term in ['splunk', 'log', 'logging', 'spl']):
            suggestions.append((15, 'logging_in_splunk', f"Column name suggests Splunk logging"))
        
        if any(term in column_lower for term in ['gso', 'global_security', 'siem']):
            suggestions.append((16, 'logging_in_gso', f"Column name suggests GSO logging"))
        
        # Domain patterns
        if any(term in column_lower for term in ['domain', 'dns', 'fqdn', 'ad']):
            suggestions.append((17, 'domain', f"Column name suggests domain/DNS"))
        
        # Analyze data type
        data_type_hints = []
        if field:
            if field.field_type == 'BOOLEAN':
                if any(term in column_lower for term in ['coverage', 'enabled', 'active', 'installed']):
                    data_type_hints.append("Boolean type suggests coverage/status field")
            elif field.field_type == 'STRING':
                data_type_hints.append("String type - could be name, identifier, or classification")
            elif field.field_type == 'INTEGER':
                data_type_hints.append("Integer type - could be count, ID, or numeric classification")
            elif field.field_type == 'TIMESTAMP':
                data_type_hints.append("Timestamp type - likely not a core entity attribute")
        
        return {
            'suggestions': suggestions[:3],  # Top 3 suggestions
            'data_type_hints': data_type_hints,
            'confidence': 'high' if suggestions else 'low'
        }
    
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
    
    print("\nSpecific Table Reviewer - High-Value Security & Infrastructure Tables")
    
    # Test table access first
    print("\nTesting access to target tables...")
    reviewer.test_table_access()
    
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
    
    # Ask if user wants to proceed after seeing test results
    proceed = input("\nProceed with the review? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Review cancelled.")
        return
    
    # Start the review process
    reviewer.review_all_target_tables()
    
    print(f"\n✅ Review complete!")
    print(f"📁 Results saved to: {reviewer.labeled_data_path}")

if __name__ == "__main__":
    main()