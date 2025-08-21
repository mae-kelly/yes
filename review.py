#!/usr/bin/env python3
"""
Enhanced Table Column Reviewer with Smart Sampling
Handles encrypted/encoded data and ensures meaningful samples for each column
Focuses on specific high-value security and infrastructure tables
"""

import sys
import os
sys.path.insert(0, '/Users/maeve.kelly/Downloads/logLens2')

from gcp.client import BigQueryClientManager
import json
import base64
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from collections import defaultdict, Counter
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTableColumnReviewer:
    def __init__(self):
        # Target tables with their descriptions
        self.target_tables = {
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINTAGENT': {
                'description': 'CrowdStrike Endpoint Agent Data',
                'category': 'security',
                'priority': 'high',
                'expected_columns': ['hostname', 'agent_version', 'last_seen', 'status', 'platform']
            },
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINT': {
                'description': 'CMDB Endpoint Data', 
                'category': 'cmdb',
                'priority': 'critical',
                'expected_columns': ['hostname', 'ip_address', 'os_type', 'owner', 'location', 'environment']
            },
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG': {
                'description': 'Splunk Endpoint Logging Data',
                'category': 'logging', 
                'priority': 'high',
                'expected_columns': ['hostname', 'log_source', 'timestamp', 'event_type', 'severity']
            },
            'chronicle-fisv.datalake.events': {
                'description': 'Chronicle Security Events',
                'category': 'security_events',
                'priority': 'critical',
                'expected_columns': ['hostname', 'event_timestamp', 'source_ip', 'event_type', 'severity']
            }
        }
        
        # Column type mapping
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
            19: 'timestamp_field',
            20: 'event_type',
            21: 'severity_level',
            22: 'status_field',
            23: 'owner_field',
            24: 'other',
            25: 'skip'
        }
        
        # Output files
        self.labeled_data_path = Path('enhanced_tables_labeled.json')
        self.raw_samples_path = Path('raw_table_samples.json')
        
        # Initialize data structures
        self.labeled_columns = self._load_labeled_data()
        self.raw_samples = self._load_raw_samples()
        
        # Statistics
        self.statistics = {
            'total_tables_processed': 0,
            'total_columns_reviewed': 0,
            'columns_labeled': 0,
            'columns_skipped': 0,
            'encrypted_columns_found': 0,
            'readable_columns_found': 0,
            'start_time': datetime.now()
        }
        
        # Connect to projects
        self.client_managers = {}
        self._connect_to_projects()
    
    def _connect_to_projects(self):
        """Connect to required projects"""
        project_ids = set()
        for table_path in self.target_tables.keys():
            project_id = table_path.split('.')[0]
            project_ids.add(project_id)
        
        logger.info(f"🔗 Connecting to projects: {list(project_ids)}")
        
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
        """Load existing labeled data"""
        if self.labeled_data_path.exists():
            with open(self.labeled_data_path, 'r') as f:
                return json.load(f)
        
        return {
            'metadata': {
                'creation_timestamp': datetime.now().isoformat(),
                'source': 'enhanced_table_reviewer',
                'target_tables': list(self.target_tables.keys()),
                'handles_encrypted_data': True
            },
            'columns': {},
            'patterns': defaultdict(list),
            'labeling_history': [],
            'statistics': {},
            'table_info': {},
            'column_analysis': {}
        }
    
    def _load_raw_samples(self) -> Dict[str, Any]:
        """Load raw sample data"""
        if self.raw_samples_path.exists():
            with open(self.raw_samples_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_all_data(self):
        """Save both labeled data and raw samples"""
        with open(self.labeled_data_path, 'w') as f:
            json.dump(self.labeled_columns, f, indent=2, default=str)
        
        with open(self.raw_samples_path, 'w') as f:
            json.dump(self.raw_samples, f, indent=2, default=str)
        
        logger.info(f"💾 Saved data to {self.labeled_data_path} and {self.raw_samples_path}")
    
    def analyze_column_data(self, column_name: str, sample_values: List[Any]) -> Dict[str, Any]:
        """Analyze column data to detect encryption, encoding, and patterns"""
        analysis = {
            'column_name': column_name,
            'total_samples': len(sample_values),
            'non_null_samples': len([v for v in sample_values if v is not None]),
            'data_patterns': [],
            'likely_encrypted': False,
            'likely_encoded': False,
            'readable_content': False,
            'suggested_type': 'other',
            'confidence': 0.0
        }
        
        non_null_values = [str(v) for v in sample_values if v is not None and str(v).strip()]
        
        if not non_null_values:
            analysis['suggested_type'] = 'skip'
            analysis['confidence'] = 0.9
            return analysis
        
        # Check for various patterns
        for value in non_null_values[:10]:
            value_str = str(value).strip()
            
            # Check if it looks like encrypted/encoded data
            if self._looks_encrypted(value_str):
                analysis['data_patterns'].append('encrypted_like')
                analysis['likely_encrypted'] = True
            elif self._looks_base64_encoded(value_str):
                analysis['data_patterns'].append('base64_encoded')
                analysis['likely_encoded'] = True
            elif self._looks_readable(value_str):
                analysis['data_patterns'].append('readable_text')
                analysis['readable_content'] = True
            
            # Check for specific patterns
            if self._looks_like_hostname(value_str):
                analysis['data_patterns'].append('hostname_pattern')
                analysis['suggested_type'] = 'host'
                analysis['confidence'] = 0.9
            elif self._looks_like_ip(value_str):
                analysis['data_patterns'].append('ip_pattern')
                analysis['suggested_type'] = 'ip_address'
                analysis['confidence'] = 0.95
            elif self._looks_like_timestamp(value_str):
                analysis['data_patterns'].append('timestamp_pattern')
                analysis['suggested_type'] = 'timestamp_field'
                analysis['confidence'] = 0.8
            elif self._looks_like_status(value_str):
                analysis['data_patterns'].append('status_pattern')
                analysis['suggested_type'] = 'status_field'
                analysis['confidence'] = 0.7
        
        # Analyze column name for hints
        column_lower = column_name.lower()
        if 'host' in column_lower or 'computer' in column_lower or 'server' in column_lower:
            analysis['suggested_type'] = 'host'
            analysis['confidence'] = max(analysis['confidence'], 0.8)
        elif 'ip' in column_lower and 'address' in column_lower:
            analysis['suggested_type'] = 'ip_address'
            analysis['confidence'] = max(analysis['confidence'], 0.8)
        elif 'region' in column_lower or 'location' in column_lower:
            analysis['suggested_type'] = 'region'
            analysis['confidence'] = max(analysis['confidence'], 0.7)
        elif 'owner' in column_lower or 'user' in column_lower:
            analysis['suggested_type'] = 'owner_field'
            analysis['confidence'] = max(analysis['confidence'], 0.7)
        elif 'time' in column_lower or 'date' in column_lower:
            analysis['suggested_type'] = 'timestamp_field'
            analysis['confidence'] = max(analysis['confidence'], 0.7)
        elif 'event' in column_lower and 'type' in column_lower:
            analysis['suggested_type'] = 'event_type'
            analysis['confidence'] = max(analysis['confidence'], 0.7)
        elif 'status' in column_lower or 'state' in column_lower:
            analysis['suggested_type'] = 'status_field'
            analysis['confidence'] = max(analysis['confidence'], 0.7)
        
        return analysis
    
    def _looks_encrypted(self, value: str) -> bool:
        """Check if value looks encrypted"""
        if len(value) < 10:
            return False
        
        # Check for common encrypted data patterns
        patterns = [
            r'^[A-Fa-f0-9]{32,}$',  # Hex strings
            r'^[A-Za-z0-9+/=]{20,}$',  # Base64-like
            r'^[A-Za-z0-9]{40,}$',  # Hash-like
        ]
        
        for pattern in patterns:
            if re.match(pattern, value):
                return True
        
        # Check entropy (random-looking data)
        unique_chars = len(set(value))
        if len(value) > 20 and unique_chars > len(value) * 0.6:
            return True
        
        return False
    
    def _looks_base64_encoded(self, value: str) -> bool:
        """Check if value looks base64 encoded"""
        if len(value) < 4 or len(value) % 4 != 0:
            return False
        
        try:
            # Try to decode as base64
            decoded = base64.b64decode(value)
            # Check if decoded contains readable characters
            readable_chars = sum(1 for c in decoded if 32 <= c <= 126)
            return readable_chars > len(decoded) * 0.7
        except:
            return False
    
    def _looks_readable(self, value: str) -> bool:
        """Check if value contains readable text"""
        if not value:
            return False
        
        # Check for readable characters
        readable_chars = sum(1 for c in value if c.isalnum() or c in ' .-_@')
        return readable_chars > len(value) * 0.8
    
    def _looks_like_hostname(self, value: str) -> bool:
        """Check if value looks like a hostname"""
        patterns = [
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$',
            r'^[a-zA-Z0-9\-]+$'
        ]
        
        return any(re.match(pattern, value) for pattern in patterns) and len(value) > 3
    
    def _looks_like_ip(self, value: str) -> bool:
        """Check if value looks like an IP address"""
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ip_pattern, value))
    
    def _looks_like_timestamp(self, value: str) -> bool:
        """Check if value looks like a timestamp"""
        timestamp_patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # ISO date
            r'^\d{10}$',  # Unix timestamp
            r'^\d{13}$',  # Unix timestamp with milliseconds
            r'^\d{4}/\d{2}/\d{2}',  # Date format
        ]
        
        return any(re.match(pattern, value) for pattern in timestamp_patterns)
    
    def _looks_like_status(self, value: str) -> bool:
        """Check if value looks like a status field"""
        status_values = ['active', 'inactive', 'enabled', 'disabled', 'online', 'offline', 'running', 'stopped', 'up', 'down']
        return value.lower() in status_values
    
    def get_comprehensive_samples(self, client, table_path: str, column_name: str) -> List[Any]:
        """Get comprehensive samples for a specific column using multiple strategies"""
        samples = []
        
        # Strategy 1: Get distinct non-null values
        try:
            query = f"""
            SELECT DISTINCT `{column_name}` as sample_value
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            LIMIT 15
            """
            
            query_job = client.query(query)
            results = list(query_job.result(timeout=30))
            
            for row in results:
                if row.sample_value is not None:
                    samples.append(row.sample_value)
            
            if samples:
                logger.info(f"✅ Got {len(samples)} distinct samples for {column_name}")
                return samples
        
        except Exception as e:
            logger.debug(f"Distinct query failed for {column_name}: {e}")
        
        # Strategy 2: Get random samples
        try:
            query = f"""
            SELECT `{column_name}` as sample_value
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            ORDER BY RAND()
            LIMIT 10
            """
            
            query_job = client.query(query)
            results = list(query_job.result(timeout=30))
            
            for row in results:
                if row.sample_value is not None:
                    samples.append(row.sample_value)
            
            if samples:
                logger.info(f"✅ Got {len(samples)} random samples for {column_name}")
                return samples
        
        except Exception as e:
            logger.debug(f"Random query failed for {column_name}: {e}")
        
        # Strategy 3: Simple limit query
        try:
            query = f"""
            SELECT `{column_name}` as sample_value
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            LIMIT 8
            """
            
            query_job = client.query(query)
            results = list(query_job.result(timeout=20))
            
            for row in results:
                if row.sample_value is not None:
                    samples.append(row.sample_value)
            
            if samples:
                logger.info(f"✅ Got {len(samples)} basic samples for {column_name}")
                return samples
        
        except Exception as e:
            logger.debug(f"Basic query failed for {column_name}: {e}")
        
        logger.warning(f"❌ No samples retrieved for {column_name}")
        return []
    
    def review_all_target_tables(self):
        """Review all target tables with enhanced sampling"""
        print("\n" + "="*80)
        print("ENHANCED TABLE COLUMN REVIEWER")
        print("Handles encrypted/encoded data with smart analysis")
        print("="*80)
        
        print("\n🎯 Target Tables:")
        for i, (table_path, info) in enumerate(self.target_tables.items(), 1):
            print(f"  {i}. {info['description']}")
            print(f"     📍 {table_path}")
            print(f"     🏷️ Category: {info['category']} | Priority: {info['priority']}")
        
        print(f"\n📋 Column Types Available (1-{len(self.column_types)}):")
        self._show_column_types()
        
        confirm = input(f"\n🚀 Ready to start enhanced review? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Review cancelled.")
            return
        
        # Process each table
        for i, (table_path, table_info) in enumerate(self.target_tables.items(), 1):
            print(f"\n" + "="*80)
            print(f"📊 TABLE {i}/{len(self.target_tables)}: {table_info['description']}")
            print("="*80)
            print(f"📍 Path: {table_path}")
            print(f"🏷️ Category: {table_info['category']} | Priority: {table_info['priority']}")
            
            try:
                if table_path in self.labeled_columns.get('columns', {}):
                    print("✅ Already reviewed, skipping...")
                    continue
                
                success = self._review_table_enhanced(table_path, table_info)
                if success:
                    self.statistics['total_tables_processed'] += 1
                
                self._save_all_data()
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Review interrupted. Saving progress...")
                self._save_all_data()
                self._print_final_statistics()
                return
            except Exception as e:
                logger.error(f"❌ Failed to process {table_path}: {e}")
        
        self._print_final_statistics()
        self._save_all_data()
    
    def _review_table_enhanced(self, table_path: str, table_info: Dict[str, Any]) -> bool:
        """Enhanced table review with smart sampling"""
        project_id = table_path.split('.')[0]
        manager = self.client_managers.get(project_id)
        
        if not manager:
            logger.error(f"No client manager for project {project_id}")
            return False
        
        try:
            with manager.get_client() as client:
                # Get table metadata
                table = client.get_table(table_path)
                columns = [field.name for field in table.schema]
                
                print(f"📊 Found {len(columns)} columns, {table.num_rows:,} rows" if table.num_rows else f"📊 Found {len(columns)} columns")
                
                # Store table info
                self.labeled_columns['table_info'][table_path] = {
                    'description': table_info['description'],
                    'category': table_info['category'],
                    'priority': table_info['priority'],
                    'num_rows': table.num_rows,
                    'num_columns': len(columns),
                    'schema_summary': [
                        {
                            'name': field.name,
                            'type': field.field_type,
                            'mode': field.mode
                        } for field in table.schema
                    ]
                }
                
                table_labels = {}
                table_analysis = {}
                
                # Review each column with enhanced sampling
                for col_idx, column in enumerate(columns, 1):
                    print(f"\n📋 Column [{col_idx}/{len(columns)}]: {column}")
                    
                    # Get field info
                    field = next((f for f in table.schema if f.name == column), None)
                    if field:
                        print(f"   📝 Type: {field.field_type} | Mode: {field.mode}")
                        if field.description:
                            print(f"   📄 Description: {field.description}")
                    
                    # Get comprehensive samples for this specific column
                    print(f"   🔍 Getting samples for '{column}'...")
                    samples = self.get_comprehensive_samples(client, table_path, column)
                    
                    # Analyze the samples
                    analysis = self.analyze_column_data(column, samples)
                    table_analysis[column] = analysis
                    
                    # Display analysis results
                    self._display_column_analysis(column, samples, analysis)
                    
                    # Get user decision
                    label = self._get_user_label_decision(column, analysis, table_info)
                    
                    if label == 'skip_table':
                        print("   ⏭️ Skipping entire table")
                        return False
                    
                    table_labels[column] = label
                    
                    # Update statistics
                    if label != 'skip':
                        self.statistics['columns_labeled'] += 1
                        
                        # Store pattern info
                        self.labeled_columns['patterns'][label].append({
                            'column': column,
                            'table': table_path,
                            'samples': samples[:5],
                            'analysis': analysis,
                            'table_category': table_info['category'],
                            'field_type': field.field_type if field else 'unknown'
                        })
                    else:
                        self.statistics['columns_skipped'] += 1
                    
                    self.statistics['total_columns_reviewed'] += 1
                    
                    # Track encryption statistics
                    if analysis['likely_encrypted']:
                        self.statistics['encrypted_columns_found'] += 1
                    elif analysis['readable_content']:
                        self.statistics['readable_columns_found'] += 1
                
                # Store results
                self.labeled_columns['columns'][table_path] = table_labels
                self.labeled_columns['column_analysis'][table_path] = table_analysis
                
                # Store raw samples
                if table_path not in self.raw_samples:
                    self.raw_samples[table_path] = {}
                
                for column in columns:
                    if column not in self.raw_samples[table_path]:
                        samples = self.get_comprehensive_samples(client, table_path, column)
                        self.raw_samples[table_path][column] = samples
                
                # Add to history
                self.labeled_columns['labeling_history'].append({
                    'table': table_path,
                    'table_info': table_info,
                    'labels': table_labels,
                    'analysis_summary': table_analysis,
                    'timestamp': datetime.now().isoformat(),
                    'encrypted_columns': sum(1 for a in table_analysis.values() if a['likely_encrypted']),
                    'readable_columns': sum(1 for a in table_analysis.values() if a['readable_content'])
                })
                
                print(f"\n✅ Table '{table_info['description']}' review complete!")
                labeled_count = len([l for l in table_labels.values() if l != 'skip'])
                encrypted_count = sum(1 for a in table_analysis.values() if a['likely_encrypted'])
                print(f"   📊 Columns labeled: {labeled_count}")
                print(f"   🔒 Encrypted columns found: {encrypted_count}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error processing table {table_path}: {e}")
            return False
    
    def _display_column_analysis(self, column: str, samples: List[Any], analysis: Dict[str, Any]):
        """Display analysis results for a column"""
        print(f"   📊 Analysis Results:")
        print(f"      Samples found: {analysis['non_null_samples']}")
        
        if analysis['likely_encrypted']:
            print(f"      🔒 LIKELY ENCRYPTED/ENCODED DATA")
        elif analysis['readable_content']:
            print(f"      📖 Contains readable content")
        
        if analysis['data_patterns']:
            print(f"      🔍 Patterns: {', '.join(analysis['data_patterns'])}")
        
        if analysis['suggested_type'] != 'other':
            print(f"      💡 Suggested type: {analysis['suggested_type']} (confidence: {analysis['confidence']:.1%})")
        
        # Show samples (handle encrypted/encoded data)
        if samples:
            print(f"   📋 Sample values:")
            for i, sample in enumerate(samples[:8], 1):
                sample_str = str(sample)
                
                # Truncate very long values
                if len(sample_str) > 100:
                    display_sample = sample_str[:100] + "..."
                else:
                    display_sample = sample_str
                
                # Mark encrypted-looking data
                if analysis['likely_encrypted'] and len(sample_str) > 20:
                    print(f"      {i}. 🔒 {display_sample}")
                elif analysis['likely_encoded']:
                    print(f"      {i}. 📎 {display_sample}")
                else:
                    print(f"      {i}. {display_sample}")
        else:
            print(f"   ⚠️ No sample values available")
    
    def _get_user_label_decision(self, column: str, analysis: Dict[str, Any], table_info: Dict[str, Any]) -> str:
        """Get user's labeling decision with smart suggestions"""
        while True:
            try:
                print(f"\n   🏷️ Label options for '{column}':")
                
                # Show smart suggestion if available
                if analysis['suggested_type'] != 'other' and analysis['confidence'] > 0.6:
                    suggested_num = None
                    for num, col_type in self.column_types.items():
                        if col_type == analysis['suggested_type']:
                            suggested_num = num
                            break
                    
                    if suggested_num:
                        print(f"      💡 SUGGESTED: {suggested_num} = {analysis['suggested_type']} (confidence: {analysis['confidence']:.1%})")
                
                print(f"      1-{len(self.column_types)}: Label with specific type")
                print(f"      0: Show all column types")
                print(f"      s: Skip this entire table")
                print(f"      i: Show more info about this column")
                
                choice = input(f"   Decision: ").strip()
                
                if choice == '0':
                    self._show_column_types()
                    continue
                
                if choice.lower() == 's':
                    return 'skip_table'
                
                if choice.lower() == 'i':
                    self._show_column_details(column, analysis, table_info)
                    continue
                
                choice_num = int(choice)
                
                if choice_num in self.column_types:
                    label = self.column_types[choice_num]
                    
                    if label != 'skip':
                        print(f"   ✅ Labeled as: {label}")
                    else:
                        print(f"   ⏭️ Skipped")
                    
                    return label
                else:
                    print(f"   ❌ Invalid choice. Please enter 1-{len(self.column_types)}, 0, 's', or 'i'")
            
            except ValueError:
                print(f"   ❌ Please enter a valid number, 0, 's', or 'i'")
            except KeyboardInterrupt:
                raise
    
    def _show_column_types(self):
        """Display all available column types"""
        print(f"\n   📋 Available Column Types:")
        for num, col_type in self.column_types.items():
            if num % 5 == 1:
                print()
            print(f"   {num:2}. {col_type:20}", end="  ")
        print()
    
    def _show_column_details(self, column: str, analysis: Dict[str, Any], table_info: Dict[str, Any]):
        """Show detailed information about a column"""
        print(f"\n   📋 Detailed Analysis for '{column}':")
        print(f"      Table: {table_info['description']}")
        print(f"      Category: {table_info['category']}")
        print(f"      Total samples: {analysis['total_samples']}")
        print(f"      Non-null samples: {analysis['non_null_samples']}")
        print(f"      Likely encrypted: {analysis['likely_encrypted']}")
        print(f"      Likely encoded: {analysis['likely_encoded']}")
        print(f"      Readable content: {analysis['readable_content']}")
        print(f"      Data patterns: {analysis['data_patterns']}")
        print(f"      Suggested type: {analysis['suggested_type']}")
        print(f"      Confidence: {analysis['confidence']:.1%}")
    
    def _print_final_statistics(self):
        """Print comprehensive final statistics"""
        total_time = (datetime.now() - self.statistics['start_time']).total_seconds()
        
        print("\n" + "="*80)
        print("ENHANCED TABLE REVIEW COMPLETE")
        print("="*80)
        print(f"⏱️ Total time: {total_time/60:.1f} minutes")
        print(f"📊 Tables processed: {self.statistics['total_tables_processed']}")
        print(f"📋 Columns reviewed: {self.statistics['total_columns_reviewed']}")
        print(f"🏷️ Columns labeled: {self.statistics['columns_labeled']}")
        print(f"⏭️ Columns skipped: {self.statistics['columns_skipped']}")
        print(f"🔒 Encrypted columns found: {self.statistics['encrypted_columns_found']}")
        print(f"📖 Readable columns found: {self.statistics['readable_columns_found']}")
        
        if self.statistics['total_columns_reviewed'] > 0:
            label_rate = (self.statistics['columns_labeled'] / self.statistics['total_columns_reviewed']) * 100
            encrypt_rate = (self.statistics['encrypted_columns_found'] / self.statistics['total_columns_reviewed']) * 100
            print(f"📈 Labeling rate: {label_rate:.1f}%")
            print(f"🔐 Encryption rate: {encrypt_rate:.1f}%")
        
        # Show column type distribution
        print(f"\n📊 Column Type Distribution:")
        type_counts = defaultdict(int)
        for table_labels in self.labeled_columns['columns'].values():
            for label in table_labels.values():
                if label != 'skip':
                    type_counts[label] += 1
        
        for col_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {col_type:25} {count:6}")
        
        # Update final statistics
        self.labeled_columns['statistics'] = {
            'total_tables_processed': self.statistics['total_tables_processed'],
            'total_columns_reviewed': self.statistics['total_columns_reviewed'],
            'columns_labeled': self.statistics['columns_labeled'],
            'columns_skipped': self.statistics['columns_skipped'],
            'encrypted_columns_found': self.statistics['encrypted_columns_found'],
            'readable_columns_found': self.statistics['readable_columns_found'],
            'processing_time_minutes': total_time/60,
            'type_distribution': dict(type_counts),
            'completion_timestamp': datetime.now().isoformat()
        }

def main():
    """Main entry point"""
    print("🚀 Enhanced Table Column Reviewer")
    print("Specialized for encrypted/encoded data analysis")
    
    reviewer = EnhancedTableColumnReviewer()
    
    # Show connection status
    print(f"\n🔗 Connected to {len(reviewer.client_managers)} projects")
    for project_id in reviewer.client_managers:
        print(f"   ✅ {project_id}")
    
    # Check for existing progress
    if reviewer.labeled_columns.get('columns'):
        print(f"\n📋 Found existing progress:")
        completed = len(reviewer.labeled_columns['columns'])
        total = len(reviewer.target_tables)
        print(f"   Tables completed: {completed}/{total}")
        
        if completed < total:
            resume = input(f"\n🔄 Continue from where you left off? (y/n): ").lower().strip()
            if resume != 'y':
                print("Starting fresh review.")
                reviewer.labeled_columns = reviewer._load_labeled_data()
                reviewer.raw_samples = reviewer._load_raw_samples()
    
    # Start review
    try:
        reviewer.review_all_target_tables()
        print(f"\n✅ Review complete!")
        print(f"📁 Labeled data: {reviewer.labeled_data_path}")
        print(f"📁 Raw samples: {reviewer.raw_samples_path}")
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Review interrupted but progress saved!")
    except Exception as e:
        print(f"\n❌ Error during review: {e}")
        reviewer._save_all_data()

if __name__ == "__main__":
    main()