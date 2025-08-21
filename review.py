#!/usr/bin/env python3
"""
Schema-Based Column Reviewer for High-Value Tables
Focuses on column names and schema information rather than encrypted/complex data values
Designed for tables with encrypted data or complex formatting
"""

import sys
import os
sys.path.insert(0, '/Users/maeve.kelly/Downloads/logLens2')

from gcp.client import BigQueryClientManager
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaBasedReviewer:
    def __init__(self):
        # Target tables with descriptions and expected column patterns
        self.target_tables = {
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINTAGENT': {
                'description': 'CrowdStrike Endpoint Agent Data',
                'category': 'security_agent',
                'priority': 'high',
                'expected_patterns': {
                    'host': ['hostname', 'computer', 'device', 'endpoint', 'machine', 'host'],
                    'domain': ['domain', 'dns', 'fqdn'],
                    'edr_coverage': ['crowdstrike', 'agent', 'sensor', 'protection', 'coverage'],
                    'system_classification': ['os', 'operating', 'platform', 'version'],
                    'region': ['region', 'location', 'site', 'geography'],
                    'business_unit': ['unit', 'org', 'department', 'division'],
                    'infrastructure_type': ['infra', 'type', 'category', 'class']
                }
            },
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINT': {
                'description': 'CMDB Endpoint Data',
                'category': 'cmdb',
                'priority': 'critical',
                'expected_patterns': {
                    'host': ['hostname', 'name', 'computer', 'device', 'endpoint', 'asset'],
                    'infrastructure_type': ['type', 'category', 'class', 'model'],
                    'region': ['region', 'location', 'site', 'zone', 'geography'],
                    'country': ['country', 'nation', 'locale'],
                    'business_unit': ['unit', 'org', 'department', 'owner', 'responsible'],
                    'system_classification': ['os', 'operating', 'platform', 'environment'],
                    'domain': ['domain', 'dns', 'fqdn'],
                    'data_center': ['datacenter', 'center', 'facility', 'rack']
                }
            },
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG': {
                'description': 'Splunk Endpoint Logging Data',
                'category': 'logging',
                'priority': 'high',
                'expected_patterns': {
                    'host': ['host', 'hostname', 'source', 'endpoint', 'computer'],
                    'logging_in_splunk': ['splunk', 'log', 'event', 'index', 'source'],
                    'domain': ['domain', 'dns'],
                    'system_classification': ['os', 'operating', 'platform'],
                    'region': ['region', 'location', 'site'],
                    'infrastructure_type': ['type', 'category', 'sourcetype']
                }
            },
            'chronicle-fisv.datalake.events': {
                'description': 'Chronicle Security Events',
                'category': 'security_events',
                'priority': 'critical',
                'expected_patterns': {
                    'host': ['host', 'hostname', 'source', 'target', 'endpoint', 'principal'],
                    'domain': ['domain', 'dns', 'network'],
                    'system_classification': ['os', 'platform', 'asset'],
                    'region': ['region', 'location', 'geography'],
                    'logging_in_gso': ['chronicle', 'security', 'event', 'log'],
                    'infrastructure_type': ['type', 'category', 'class']
                }
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
            18: 'skip'
        }
        
        # Output file
        self.output_file = Path('schema_based_labels.json')
        
        # Data structure
        self.labeled_data = self._load_existing_data()
        
        # Statistics
        self.stats = {
            'tables_processed': 0,
            'columns_reviewed': 0,
            'columns_labeled': 0,
            'auto_suggestions_accepted': 0,
            'manual_overrides': 0,
            'start_time': datetime.now()
        }
        
        # Connect to projects
        self.client_managers = {}
        self._connect_to_projects()
    
    def _load_existing_data(self) -> Dict[str, Any]:
        """Load existing labeled data or create new structure"""
        if self.output_file.exists():
            with open(self.output_file, 'r') as f:
                return json.load(f)
        
        return {
            'metadata': {
                'creation_timestamp': datetime.now().isoformat(),
                'source': 'schema_based_reviewer',
                'approach': 'schema_and_pattern_based_classification'
            },
            'tables': {},
            'patterns': defaultdict(list),
            'statistics': {},
            'suggestions': {}
        }
    
    def _connect_to_projects(self):
        """Connect to required projects"""
        project_ids = set()
        for table_path in self.target_tables.keys():
            project_id = table_path.split('.')[0]
            project_ids.add(project_id)
        
        for project_id in project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                if manager.test_connection():
                    self.client_managers[project_id] = manager
                    logger.info(f"✅ Connected to {project_id}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to {project_id}: {e}")
        
        if not self.client_managers:
            raise RuntimeError("No project connections available")
    
    def _save_data(self):
        """Save labeled data"""
        with open(self.output_file, 'w') as f:
            json.dump(self.labeled_data, f, indent=2, default=str)
        logger.info(f"💾 Saved to {self.output_file}")
    
    def _analyze_column_name(self, column_name: str, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze column name and suggest classification"""
        column_lower = column_name.lower()
        suggestions = []
        confidence_scores = {}
        
        # Check against expected patterns for this table type
        expected_patterns = table_info.get('expected_patterns', {})
        
        for field_type, patterns in expected_patterns.items():
            score = 0
            matches = []
            
            for pattern in patterns:
                if pattern in column_lower:
                    score += 1
                    matches.append(pattern)
            
            if score > 0:
                confidence = min(0.95, score * 0.3 + 0.4)
                confidence_scores[field_type] = confidence
                suggestions.append({
                    'type': field_type,
                    'confidence': confidence,
                    'matches': matches,
                    'reason': f"Matches patterns: {', '.join(matches)}"
                })
        
        # Additional generic pattern matching
        generic_patterns = {
            'host': ['host', 'name', 'computer', 'device', 'machine', 'endpoint', 'asset'],
            'domain': ['domain', 'dns', 'fqdn', 'realm'],
            'region': ['region', 'location', 'zone', 'site', 'geo', 'area'],
            'country': ['country', 'nation', 'locale', 'territory'],
            'infrastructure_type': ['type', 'kind', 'category', 'class', 'model'],
            'system_classification': ['os', 'operating', 'platform', 'system', 'environment'],
            'business_unit': ['unit', 'org', 'department', 'division', 'group', 'team'],
            'edr_coverage': ['edr', 'endpoint', 'protection', 'antivirus', 'security', 'agent'],
            'logging_in_splunk': ['splunk', 'log', 'logging', 'index', 'forwarder'],
            'logging_in_gso': ['gso', 'chronicle', 'security', 'siem']
        }
        
        for field_type, patterns in generic_patterns.items():
            if field_type not in confidence_scores:  # Don't override table-specific matches
                for pattern in patterns:
                    if pattern in column_lower:
                        confidence = 0.7
                        suggestions.append({
                            'type': field_type,
                            'confidence': confidence,
                            'matches': [pattern],
                            'reason': f"Generic pattern match: {pattern}"
                        })
                        break
        
        # Sort suggestions by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'suggestions': suggestions[:3],  # Top 3 suggestions
            'top_suggestion': suggestions[0] if suggestions else None,
            'analysis': {
                'column_name': column_name,
                'length': len(column_name),
                'has_underscore': '_' in column_name,
                'has_numbers': any(c.isdigit() for c in column_name),
                'all_caps': column_name.isupper(),
                'camel_case': any(c.isupper() for c in column_name[1:])
            }
        }
    
    def review_all_tables(self):
        """Review all target tables using schema-based approach"""
        print("\n" + "="*80)
        print("SCHEMA-BASED COLUMN REVIEWER")
        print("="*80)
        print("🔍 Intelligent column classification using schema analysis")
        print("📋 Designed for encrypted/complex data where values aren't readable")
        print("\n🎯 Target Tables:")
        
        for i, (table_path, info) in enumerate(self.target_tables.items(), 1):
            print(f"  {i}. {info['description']}")
            print(f"     Category: {info['category']} | Priority: {info['priority']}")
        
        print(f"\n📊 Column Types Available:")
        self._show_column_types_compact()
        
        print("\n" + "="*80)
        
        # Start processing
        for table_path, table_info in self.target_tables.items():
            if table_path in self.labeled_data.get('tables', {}):
                print(f"\n✅ {table_info['description']} already processed")
                continue
            
            print(f"\n" + "🔄 " + "="*70)
            print(f"PROCESSING: {table_info['description']}")
            print("="*70)
            
            try:
                success = self._process_table_schema(table_path, table_info)
                if success:
                    self.stats['tables_processed'] += 1
                    self._save_data()
            except KeyboardInterrupt:
                print("\n⚠️ Interrupted - saving progress...")
                self._save_data()
                return
            except Exception as e:
                logger.error(f"❌ Failed to process {table_path}: {e}")
        
        self._show_final_summary()
        self._save_data()
    
    def _process_table_schema(self, table_path: str, table_info: Dict[str, Any]) -> bool:
        """Process a table using schema information only"""
        project_id = table_path.split('.')[0]
        manager = self.client_managers.get(project_id)
        
        if not manager:
            print(f"❌ No connection to project {project_id}")
            return False
        
        try:
            with manager.get_client() as client:
                table = client.get_table(table_path)
                
                print(f"📊 Table Info:")
                print(f"   Rows: {table.num_rows:,}" if table.num_rows else "   Rows: Unknown")
                print(f"   Columns: {len(table.schema)}")
                print(f"   Type: {table.table_type}")
                
                # Store table metadata
                table_data = {
                    'table_path': table_path,
                    'description': table_info['description'],
                    'category': table_info['category'],
                    'num_rows': table.num_rows,
                    'num_columns': len(table.schema),
                    'columns': {},
                    'processing_timestamp': datetime.now().isoformat()
                }
                
                print(f"\n🔍 Analyzing {len(table.schema)} columns...")
                
                # Process each column
                for i, field in enumerate(table.schema, 1):
                    print(f"\n📋 Column {i}/{len(table.schema)}: {field.name}")
                    print(f"   Type: {field.field_type}")
                    if field.mode:
                        print(f"   Mode: {field.mode}")
                    if field.description:
                        print(f"   Description: {field.description}")
                    
                    # Analyze column name and suggest classification
                    analysis = self._analyze_column_name(field.name, table_info)
                    
                    if analysis['top_suggestion']:
                        suggestion = analysis['top_suggestion']
                        print(f"   🤖 AI Suggestion: {suggestion['type']} ({suggestion['confidence']:.0%} confidence)")
                        print(f"   💡 Reason: {suggestion['reason']}")
                    
                    # Show all suggestions
                    if len(analysis['suggestions']) > 1:
                        print(f"   📋 Other suggestions:")
                        for j, sugg in enumerate(analysis['suggestions'][1:], 2):
                            print(f"      {j}. {sugg['type']} ({sugg['confidence']:.0%})")
                    
                    # Get user decision
                    while True:
                        try:
                            print(f"\n   🏷️ Options for '{field.name}':")
                            print(f"      a = Accept AI suggestion ({analysis['top_suggestion']['type']})" if analysis['top_suggestion'] else "      (no AI suggestion)")
                            print(f"      1-17 = Specific type")
                            print(f"      18 = Skip")
                            print(f"      0 = Show all types")
                            print(f"      s = Skip entire table")
                            
                            choice = input(f"   Choice: ").strip().lower()
                            
                            if choice == 's':
                                print("   ⏭️ Skipping table")
                                return False
                            
                            if choice == '0':
                                self._show_column_types()
                                continue
                            
                            if choice == 'a' and analysis['top_suggestion']:
                                # Accept AI suggestion
                                label = analysis['top_suggestion']['type']
                                table_data['columns'][field.name] = {
                                    'label': label,
                                    'method': 'ai_suggestion',
                                    'confidence': analysis['top_suggestion']['confidence'],
                                    'field_type': field.field_type,
                                    'reason': analysis['top_suggestion']['reason']
                                }
                                print(f"   ✅ Accepted AI suggestion: {label}")
                                self.stats['auto_suggestions_accepted'] += 1
                                break
                            
                            # Manual choice
                            try:
                                choice_num = int(choice)
                                if choice_num in self.column_types:
                                    label = self.column_types[choice_num]
                                    table_data['columns'][field.name] = {
                                        'label': label,
                                        'method': 'manual',
                                        'confidence': 1.0,
                                        'field_type': field.field_type,
                                        'reason': 'manual_selection'
                                    }
                                    
                                    if label != 'skip':
                                        print(f"   ✅ Labeled as: {label}")
                                        self.stats['columns_labeled'] += 1
                                        if analysis['top_suggestion'] and label != analysis['top_suggestion']['type']:
                                            self.stats['manual_overrides'] += 1
                                    else:
                                        print(f"   ⏭️ Skipped")
                                    
                                    self.stats['columns_reviewed'] += 1
                                    break
                                else:
                                    print(f"   ❌ Invalid number. Use 1-18")
                            except ValueError:
                                print(f"   ❌ Invalid input. Use 'a', number, or 's'")
                        
                        except KeyboardInterrupt:
                            raise
                
                # Store processed table
                self.labeled_data['tables'][table_path] = table_data
                
                # Update patterns
                for col_name, col_data in table_data['columns'].items():
                    if col_data['label'] != 'skip':
                        self.labeled_data['patterns'][col_data['label']].append({
                            'column_name': col_name,
                            'table_path': table_path,
                            'table_category': table_info['category'],
                            'field_type': col_data['field_type'],
                            'method': col_data['method'],
                            'confidence': col_data['confidence']
                        })
                
                labeled_count = sum(1 for col in table_data['columns'].values() if col['label'] != 'skip')
                print(f"\n✅ {table_info['description']} processed!")
                print(f"   📊 {labeled_count} columns labeled, {len(table_data['columns']) - labeled_count} skipped")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error processing {table_path}: {e}")
            return False
    
    def _show_column_types_compact(self):
        """Show column types in compact format"""
        for i in range(0, len(self.column_types), 6):
            line_types = list(self.column_types.items())[i:i+6]
            print("  " + "  ".join(f"{num}={name}" for num, name in line_types))
    
    def _show_column_types(self):
        """Show all column types"""
        print("\n   📋 Column Types:")
        for num, col_type in self.column_types.items():
            print(f"      {num:2}. {col_type}")
        print()
    
    def _show_final_summary(self):
        """Show final processing summary"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*80)
        print("SCHEMA-BASED REVIEW COMPLETE")
        print("="*80)
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"📊 Tables processed: {self.stats['tables_processed']}")
        print(f"📋 Columns reviewed: {self.stats['columns_reviewed']}")
        print(f"🏷️  Columns labeled: {self.stats['columns_labeled']}")
        print(f"🤖 AI suggestions accepted: {self.stats['auto_suggestions_accepted']}")
        print(f"✋ Manual overrides: {self.stats['manual_overrides']}")
        
        if self.stats['columns_reviewed'] > 0:
            ai_acceptance = (self.stats['auto_suggestions_accepted'] / self.stats['columns_reviewed']) * 100
            print(f"📈 AI acceptance rate: {ai_acceptance:.1f}%")
        
        # Show label distribution
        print(f"\n📊 Label Distribution:")
        type_counts = defaultdict(int)
        for table_data in self.labeled_data['tables'].values():
            for col_data in table_data['columns'].values():
                if col_data['label'] != 'skip':
                    type_counts[col_data['label']] += 1
        
        for label, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {label:25} {count:3}")
        
        print(f"\n💾 Results saved to: {self.output_file}")
    
    def show_progress(self):
        """Show current progress"""
        completed = len(self.labeled_data.get('tables', {}))
        total = len(self.target_tables)
        
        print(f"\n📊 Progress: {completed}/{total} tables completed")
        
        for table_path, table_info in self.target_tables.items():
            status = "✅" if table_path in self.labeled_data.get('tables', {}) else "⏳"
            print(f"   {status} {table_info['description']}")

def main():
    """Main entry point"""
    reviewer = SchemaBasedReviewer()
    
    print("🔍 Schema-Based Column Reviewer")
    print("   Perfect for tables with encrypted/complex data")
    print("   Uses AI pattern matching + manual review")
    
    # Show progress if any
    if reviewer.labeled_data.get('tables'):
        reviewer.show_progress()
        resume = input("\nContinue from where you left off? (y/n): ").strip().lower()
        if resume != 'y':
            reviewer.labeled_data = reviewer._load_existing_data()
    
    # Start review
    try:
        reviewer.review_all_tables()
        print("\n🎉 All done! Check the output file for results.")
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted - progress saved")

if __name__ == "__main__":
    main()