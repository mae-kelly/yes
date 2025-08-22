#!/usr/bin/env python3
"""
Script to filter out tables that don't have any 'host' columns 
from reviewed_labeled_columns.json
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HostTableFilter:
    def __init__(self, input_file: str = 'reviewed_labeled_columns.json'):
        self.input_file = Path(input_file)
        self.output_file = Path('reviewed_labeled_columns_host_only.json')
        self.removed_tables_file = Path('removed_tables_no_host.json')
        
        # Load the reviewed data
        self.reviewed_data = self._load_reviewed_data()
        
        # Initialize filtered data structure
        self.filtered_data = {}
        
        # Track removed tables
        self.removed_tables = {
            'removal_metadata': {
                'removal_timestamp': datetime.now().isoformat(),
                'original_file': str(self.input_file),
                'removal_reason': 'no_host_column'
            },
            'removed_tables': {},
            'removal_statistics': {
                'total_tables_original': 0,
                'total_tables_kept': 0,
                'total_tables_removed': 0,
                'columns_in_removed_tables': defaultdict(int)
            }
        }
    
    def _load_reviewed_data(self) -> Dict[str, Any]:
        """Load the reviewed_labeled_columns.json file"""
        if not self.input_file.exists():
            logger.error(f"Input file {self.input_file} not found!")
            return {}
        
        try:
            with open(self.input_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded reviewed data from {self.input_file}")
                return data
        except Exception as e:
            logger.error(f"Failed to load {self.input_file}: {e}")
            return {}
    
    def filter_tables_with_host(self):
        """Filter to keep only tables that have at least one 'host' column"""
        if not self.reviewed_data:
            logger.error("No data to filter!")
            return
        
        print("\n" + "="*80)
        print("FILTERING TABLES WITHOUT HOST COLUMNS")
        print("="*80)
        
        # Copy all non-columns data first
        self.filtered_data = {
            key: value for key, value in self.reviewed_data.items()
            if key != 'columns'
        }
        
        # Add new filtering metadata
        if 'filter_metadata' not in self.filtered_data:
            self.filtered_data['filter_metadata'] = {}
        
        self.filtered_data['filter_metadata']['host_table_filter'] = {
            'filter_timestamp': datetime.now().isoformat(),
            'filter_type': 'remove_tables_without_host',
            'original_file': str(self.input_file)
        }
        
        # Initialize filtered columns
        self.filtered_data['columns'] = {}
        
        # Process each table
        columns_data = self.reviewed_data.get('columns', {})
        self.removed_tables['removal_statistics']['total_tables_original'] = len(columns_data)
        
        tables_with_host = []
        tables_without_host = []
        
        for table_path, table_columns in columns_data.items():
            # Check if this table has any 'host' columns
            has_host = any(col_type == 'host' for col_type in table_columns.values())
            
            if has_host:
                # Keep this table
                self.filtered_data['columns'][table_path] = table_columns
                tables_with_host.append(table_path)
                
                # Count host columns in this table
                host_count = sum(1 for col_type in table_columns.values() if col_type == 'host')
                other_count = len(table_columns) - host_count
                
                logger.debug(f"✅ Keeping {table_path} - has {host_count} host column(s)")
            else:
                # Remove this table
                tables_without_host.append(table_path)
                self.removed_tables['removed_tables'][table_path] = {
                    'columns': table_columns,
                    'column_count': len(table_columns),
                    'removed_at': datetime.now().isoformat()
                }
                
                # Track what types of columns were in removed tables
                for col_type in table_columns.values():
                    self.removed_tables['removal_statistics']['columns_in_removed_tables'][col_type] += 1
                
                logger.debug(f"❌ Removing {table_path} - no host columns")
        
        # Update statistics
        self.removed_tables['removal_statistics']['total_tables_kept'] = len(tables_with_host)
        self.removed_tables['removal_statistics']['total_tables_removed'] = len(tables_without_host)
        
        # Update labeling history to only include kept tables
        if 'labeling_history' in self.filtered_data:
            original_history = self.filtered_data['labeling_history']
            self.filtered_data['labeling_history'] = [
                entry for entry in original_history
                if entry.get('table') in tables_with_host
            ]
        
        # Update patterns if they exist
        if 'patterns' in self.filtered_data:
            # Filter patterns to only include those from kept tables
            kept_table_set = set(tables_with_host)
            for pattern_type, pattern_list in self.filtered_data['patterns'].items():
                if isinstance(pattern_list, list):
                    filtered_patterns = []
                    for pattern in pattern_list:
                        if isinstance(pattern, dict) and 'table' in pattern:
                            if pattern['table'] in kept_table_set:
                                filtered_patterns.append(pattern)
                        else:
                            # Keep patterns without table references
                            filtered_patterns.append(pattern)
                    self.filtered_data['patterns'][pattern_type] = filtered_patterns
        
        # Update review statistics if they exist
        if 'review_statistics' in self.filtered_data:
            self.filtered_data['review_statistics']['tables_after_host_filter'] = len(tables_with_host)
            self.filtered_data['review_statistics']['tables_removed_no_host'] = len(tables_without_host)
        
        # Show results
        self._show_filter_results(tables_with_host, tables_without_host)
        
        # Save the filtered data
        self._save_results()
    
    def _show_filter_results(self, tables_with_host: list, tables_without_host: list):
        """Display the filtering results"""
        print(f"\nFILTERING COMPLETE")
        print("-" * 50)
        print(f"Original tables: {self.removed_tables['removal_statistics']['total_tables_original']}")
        print(f"Tables with host columns (kept): {len(tables_with_host)}")
        print(f"Tables without host columns (removed): {len(tables_without_host)}")
        
        if len(tables_without_host) > 0:
            keep_rate = (len(tables_with_host) / self.removed_tables['removal_statistics']['total_tables_original']) * 100
            print(f"Table retention rate: {keep_rate:.1f}%")
            
            print(f"\nColumn types in removed tables:")
            for col_type, count in sorted(
                self.removed_tables['removal_statistics']['columns_in_removed_tables'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  {col_type:25} {count:6} columns")
            
            # Show sample of removed tables
            print(f"\nSample of removed tables (first 10):")
            for table in tables_without_host[:10]:
                columns_in_table = len(self.removed_tables['removed_tables'][table]['columns'])
                print(f"  - {table} ({columns_in_table} columns)")
            
            if len(tables_without_host) > 10:
                print(f"  ... and {len(tables_without_host) - 10} more")
        
        # Count total columns in kept tables
        total_columns_kept = 0
        host_columns_kept = 0
        for table_columns in self.filtered_data['columns'].values():
            total_columns_kept += len(table_columns)
            host_columns_kept += sum(1 for col_type in table_columns.values() if col_type == 'host')
        
        print(f"\nColumns in kept tables:")
        print(f"  Total columns: {total_columns_kept}")
        print(f"  Host columns: {host_columns_kept}")
        print(f"  Other columns: {total_columns_kept - host_columns_kept}")
    
    def _save_results(self):
        """Save the filtered data and removed tables information"""
        # Save filtered data
        with open(self.output_file, 'w') as f:
            json.dump(self.filtered_data, f, indent=2, default=str)
        
        # Save removed tables information
        with open(self.removed_tables_file, 'w') as f:
            json.dump(self.removed_tables, f, indent=2, default=str)
        
        print(f"\n📁 Results saved:")
        print(f"  Filtered data: {self.output_file}")
        print(f"  Removed tables info: {self.removed_tables_file}")
        
        logger.info(f"Saved filtered data to {self.output_file}")
        logger.info(f"Saved removed tables to {self.removed_tables_file}")
    
    def show_table_analysis(self):
        """Show detailed analysis of tables with and without host columns"""
        if not self.reviewed_data:
            print("No data loaded!")
            return
        
        columns_data = self.reviewed_data.get('columns', {})
        
        # Analyze each table
        tables_with_host_details = []
        tables_without_host_details = []
        
        for table_path, table_columns in columns_data.items():
            host_count = sum(1 for col_type in table_columns.values() if col_type == 'host')
            
            table_info = {
                'table': table_path,
                'total_columns': len(table_columns),
                'host_columns': host_count,
                'column_types': defaultdict(int)
            }
            
            for col_type in table_columns.values():
                table_info['column_types'][col_type] += 1
            
            if host_count > 0:
                tables_with_host_details.append(table_info)
            else:
                tables_without_host_details.append(table_info)
        
        print("\n" + "="*80)
        print("TABLE ANALYSIS - HOST COLUMN DISTRIBUTION")
        print("="*80)
        
        print(f"\nTABLES WITH HOST COLUMNS: {len(tables_with_host_details)}")
        print("-" * 50)
        
        # Sort by number of host columns
        tables_with_host_details.sort(key=lambda x: x['host_columns'], reverse=True)
        
        for i, table_info in enumerate(tables_with_host_details[:20], 1):
            print(f"{i:3}. {table_info['table']}")
            print(f"     Host columns: {table_info['host_columns']}, Total: {table_info['total_columns']}")
        
        if len(tables_with_host_details) > 20:
            print(f"     ... and {len(tables_with_host_details) - 20} more tables with host columns")
        
        print(f"\nTABLES WITHOUT HOST COLUMNS: {len(tables_without_host_details)}")
        print("-" * 50)
        
        if tables_without_host_details:
            # Show what types of columns these tables have
            all_types_in_no_host = defaultdict(int)
            for table_info in tables_without_host_details:
                for col_type, count in table_info['column_types'].items():
                    all_types_in_no_host[col_type] += count
            
            print("Column types in tables without host columns:")
            for col_type, count in sorted(all_types_in_no_host.items(), key=lambda x: x[1], reverse=True):
                print(f"  {col_type:25} {count:6} columns")
            
            print(f"\nFirst 10 tables without host columns:")
            for i, table_info in enumerate(tables_without_host_details[:10], 1):
                types_str = ', '.join([f"{t}({c})" for t, c in table_info['column_types'].items()])
                print(f"{i:3}. {table_info['table']}")
                print(f"     Columns: {types_str}")
            
            if len(tables_without_host_details) > 10:
                print(f"     ... and {len(tables_without_host_details) - 10} more tables without host columns")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Filter reviewed_labeled_columns.json to keep only tables with host columns'
    )
    parser.add_argument(
        '--input',
        default='reviewed_labeled_columns.json',
        help='Input file with reviewed labels (default: reviewed_labeled_columns.json)'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Show detailed analysis of tables with/without host columns before filtering'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be filtered without actually saving files'
    )
    
    args = parser.parse_args()
    
    filter_tool = HostTableFilter(input_file=args.input)
    
    if args.analyze:
        filter_tool.show_table_analysis()
        print("\nRun without --analyze flag to perform the actual filtering.")
    elif args.dry_run:
        print("DRY RUN MODE - No files will be saved")
        filter_tool.show_table_analysis()
    else:
        filter_tool.filter_tables_with_host()
        print("\n✅ Filtering complete! Tables without host columns have been removed.")

if __name__ == "__main__":
    main()