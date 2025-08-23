#!/usr/bin/env python3
"""
Extract Tables Script - extract_tables.py
Reads reviewed_labeled_columns.json and extracts all table information
Shows table paths, column mappings, and generates summaries
"""

import json
import logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TableExtractor:
    def __init__(self, json_file: str = 'reviewed_labeled_columns.json'):
        self.json_file = Path(json_file)
        self.data = self._load_json()
        self.tables = {}
        self.column_summary = defaultdict(list)
        
    def _load_json(self) -> Dict[str, Any]:
        """Load the JSON file"""
        if not self.json_file.exists():
            logger.error(f"File {self.json_file} not found!")
            return {}
        
        try:
            with open(self.json_file, 'r') as f:
                data = json.load(f)
                logger.info(f"✅ Loaded {self.json_file}")
                return data
        except Exception as e:
            logger.error(f"❌ Failed to load {self.json_file}: {e}")
            return {}
    
    def extract_all_tables(self):
        """Extract all table information from the JSON"""
        
        if not self.data:
            logger.error("No data to process!")
            return
        
        columns_data = self.data.get('columns', {})
        
        print("\n" + "="*80)
        print("TABLE EXTRACTION FROM REVIEWED_LABELED_COLUMNS.JSON")
        print("="*80)
        
        if not columns_data:
            print("❌ No tables found in JSON!")
            return
        
        print(f"📊 Found {len(columns_data)} tables in JSON file")
        
        # Extract each table
        for i, (table_path, table_columns) in enumerate(columns_data.items(), 1):
            self._extract_single_table(i, table_path, table_columns)
        
        # Generate summaries
        self._generate_summaries()
        
        # Save extracted data
        self._save_extracted_data()
    
    def _extract_single_table(self, index: int, table_path: str, table_columns: Dict[str, str]):
        """Extract information for a single table"""
        
        print(f"\n📋 TABLE {index}: {table_path}")
        print("-" * 80)
        
        # Parse table path
        path_parts = table_path.split('.')
        project_id = path_parts[0] if len(path_parts) > 0 else 'unknown'
        dataset_id = path_parts[1] if len(path_parts) > 1 else 'unknown'
        table_name = path_parts[2] if len(path_parts) > 2 else 'unknown'
        
        print(f"   🏢 Project: {project_id}")
        print(f"   📦 Dataset: {dataset_id}")
        print(f"   📄 Table: {table_name}")
        print(f"   📊 Columns: {len(table_columns)}")
        
        # Group columns by type
        columns_by_type = defaultdict(list)
        for col_name, col_type in table_columns.items():
            columns_by_type[col_type].append(col_name)
        
        # Show column breakdown
        print(f"   🏷️ Column Types:")
        for col_type, col_names in sorted(columns_by_type.items()):
            print(f"      {col_type:20} → {len(col_names):2} columns: {', '.join(col_names[:3])}{' ...' if len(col_names) > 3 else ''}")
            
            # Track for summary
            for col_name in col_names:
                self.column_summary[col_type].append({
                    'table': table_path,
                    'column': col_name
                })
        
        # Store table info
        self.tables[table_path] = {
            'index': index,
            'project_id': project_id,
            'dataset_id': dataset_id,
            'table_name': table_name,
            'full_path': table_path,
            'total_columns': len(table_columns),
            'columns': table_columns,
            'columns_by_type': dict(columns_by_type),
            'host_columns': columns_by_type.get('host', []),
            'attribute_columns': {k: v for k, v in columns_by_type.items() if k != 'host' and k != 'skip'}
        }
        
        # Highlight important columns
        host_cols = columns_by_type.get('host', [])
        if host_cols:
            print(f"   🎯 HOST COLUMNS: {', '.join(host_cols)}")
        else:
            print(f"   ⚠️  NO HOST COLUMNS FOUND")
        
        # Show key attributes
        key_attrs = ['apm', 'business_unit', 'region', 'country', 'edr_coverage']
        found_attrs = []
        for attr in key_attrs:
            if attr in columns_by_type:
                found_attrs.append(f"{attr}({len(columns_by_type[attr])})")
        
        if found_attrs:
            print(f"   ✨ Key Attributes: {', '.join(found_attrs)}")
    
    def _generate_summaries(self):
        """Generate summary statistics"""
        
        print(f"\n" + "="*80)
        print("EXTRACTION SUMMARY")
        print("="*80)
        
        # Overall stats
        total_tables = len(self.tables)
        total_columns = sum(t['total_columns'] for t in self.tables.values())
        tables_with_hosts = len([t for t in self.tables.values() if t['host_columns']])
        
        print(f"📊 Overall Statistics:")
        print(f"   Total tables: {total_tables}")
        print(f"   Total columns: {total_columns}")
        print(f"   Tables with host columns: {tables_with_hosts}")
        print(f"   Tables without host columns: {total_tables - tables_with_hosts}")
        
        # Project breakdown
        projects = defaultdict(list)
        for table_path, table_info in self.tables.items():
            projects[table_info['project_id']].append(table_path)
        
        print(f"\n🏢 Projects ({len(projects)}):")
        for project_id, table_list in projects.items():
            print(f"   {project_id:50} → {len(table_list):2} tables")
        
        # Column type summary
        print(f"\n🏷️ Column Types Summary:")
        type_counts = Counter()
        for col_type, col_list in self.column_summary.items():
            type_counts[col_type] = len(col_list)
        
        for col_type, count in type_counts.most_common():
            unique_tables = len(set(item['table'] for item in self.column_summary[col_type]))
            print(f"   {col_type:25} → {count:3} columns across {unique_tables:2} tables")
        
        # Tables suitable for CMDB
        print(f"\n🎯 CMDB-Ready Tables (have host columns):")
        cmdb_ready = [t for t in self.tables.values() if t['host_columns']]
        
        if not cmdb_ready:
            print("   ❌ No tables have host columns!")
        else:
            for table in sorted(cmdb_ready, key=lambda x: len(x['host_columns']), reverse=True):
                host_count = len(table['host_columns'])
                attr_count = sum(len(cols) for cols in table['attribute_columns'].values())
                print(f"   {table['full_path']:60} → {host_count} hosts, {attr_count} attributes")
        
        # Show which column types are missing
        expected_types = ['host', 'apm', 'app_class', 'business_unit', 'cio', 'cloud_region', 
                         'country', 'data_center', 'domain', 'edr_coverage', 'infrastructure_type', 
                         'region', 'system_classification', 'tanium_coverage']
        
        missing_types = [t for t in expected_types if t not in type_counts]
        if missing_types:
            print(f"\n⚠️  Missing CMDB Column Types:")
            for missing_type in missing_types:
                print(f"   - {missing_type}")
    
    def _save_extracted_data(self):
        """Save extracted table information"""
        
        # Save detailed table info as JSON
        output_file = 'extracted_tables.json'
        with open(output_file, 'w') as f:
            json.dump({
                'extraction_metadata': {
                    'source_file': str(self.json_file),
                    'total_tables': len(self.tables),
                    'total_columns': sum(t['total_columns'] for t in self.tables.values()),
                    'extraction_timestamp': str(pd.Timestamp.now())
                },
                'tables': self.tables,
                'column_summary': dict(self.column_summary)
            }, f, indent=2, default=str)
        
        print(f"\n💾 Saved detailed extraction to: {output_file}")
        
        # Save tables list as CSV
        csv_data = []
        for table_path, table_info in self.tables.items():
            csv_data.append({
                'table_path': table_path,
                'project_id': table_info['project_id'],
                'dataset_id': table_info['dataset_id'], 
                'table_name': table_info['table_name'],
                'total_columns': table_info['total_columns'],
                'host_columns': len(table_info['host_columns']),
                'host_column_names': ' | '.join(table_info['host_columns']),
                'attribute_types': ' | '.join(table_info['attribute_columns'].keys()),
                'cmdb_ready': 'Yes' if table_info['host_columns'] else 'No'
            })
        
        df = pd.DataFrame(csv_data)
        csv_file = 'extracted_tables.csv'
        df.to_csv(csv_file, index=False)
        print(f"💾 Saved table summary to: {csv_file}")
        
        # Save CMDB-ready tables only
        cmdb_tables = {k: v for k, v in self.tables.items() if v['host_columns']}
        if cmdb_tables:
            cmdb_file = 'cmdb_ready_tables.json'
            with open(cmdb_file, 'w') as f:
                json.dump(cmdb_tables, f, indent=2, default=str)
            print(f"💾 Saved CMDB-ready tables to: {cmdb_file}")
            print(f"   → {len(cmdb_tables)} tables ready for CMDB generation")
    
    def show_table_details(self, table_path: str):
        """Show detailed information for a specific table"""
        
        if table_path not in self.tables:
            print(f"❌ Table not found: {table_path}")
            return
        
        table_info = self.tables[table_path]
        
        print(f"\n" + "="*80)
        print(f"DETAILED VIEW: {table_path}")
        print("="*80)
        
        print(f"Project: {table_info['project_id']}")
        print(f"Dataset: {table_info['dataset_id']}")
        print(f"Table: {table_info['table_name']}")
        print(f"Total Columns: {table_info['total_columns']}")
        
        print(f"\n📋 All Columns:")
        for col_name, col_type in table_info['columns'].items():
            print(f"   {col_name:40} → {col_type}")
        
        print(f"\n🎯 Host Columns ({len(table_info['host_columns'])}):")
        for col in table_info['host_columns']:
            print(f"   - {col}")
        
        print(f"\n✨ Attribute Columns:")
        for col_type, col_names in table_info['attribute_columns'].items():
            print(f"   {col_type:20} → {', '.join(col_names)}")
    
    def list_tables_by_project(self):
        """List all tables grouped by project"""
        
        projects = defaultdict(list)
        for table_path, table_info in self.tables.items():
            projects[table_info['project_id']].append(table_info)
        
        print(f"\n" + "="*80)
        print("TABLES BY PROJECT")
        print("="*80)
        
        for project_id, table_list in projects.items():
            print(f"\n🏢 {project_id} ({len(table_list)} tables)")
            print("-" * 60)
            
            for table_info in sorted(table_list, key=lambda x: x['table_name']):
                host_indicator = "🎯" if table_info['host_columns'] else "❌"
                print(f"   {host_indicator} {table_info['dataset_id']}.{table_info['table_name']:30} → {table_info['total_columns']:2} cols")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract tables from reviewed_labeled_columns.json')
    parser.add_argument(
        '--file',
        default='reviewed_labeled_columns.json',
        help='JSON file to extract from (default: reviewed_labeled_columns.json)'
    )
    parser.add_argument(
        '--table',
        help='Show detailed view of a specific table'
    )
    parser.add_argument(
        '--by-project',
        action='store_true',
        help='List tables grouped by project'
    )
    
    args = parser.parse_args()
    
    # Create extractor
    extractor = TableExtractor(args.file)
    
    if not extractor.data:
        print("❌ No data loaded. Exiting.")
        return
    
    # Extract all tables
    extractor.extract_all_tables()
    
    # Show specific views if requested
    if args.table:
        extractor.show_table_details(args.table)
    
    if args.by_project:
        extractor.list_tables_by_project()
    
    print(f"\n✅ Table extraction complete!")
    print(f"📁 Check extracted_tables.json, extracted_tables.csv, and cmdb_ready_tables.json")

if __name__ == "__main__":
    main()