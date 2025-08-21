#!/usr/bin/env python3
"""
Script to review and filter manually labeled columns from manual_labeled_columns.json
Allows users to keep (1) or remove (2) each labeled column entry.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ColumnReviewer:
    def __init__(self, input_file: str = 'manual_labeled_columns.json'):
        self.input_file = Path(input_file)
        self.output_file = Path('reviewed_labeled_columns.json')
        self.rejected_file = Path('rejected_columns.json')
        
        # Load the original data
        self.original_data = self._load_original_data()
        
        # Initialize reviewed data structure
        self.reviewed_data = {
            'review_metadata': {
                'review_timestamp': datetime.now().isoformat(),
                'original_file': str(self.input_file),
                'reviewer_version': '1.0.0'
            },
            'columns': {},
            'patterns': defaultdict(list),
            'labeling_history': [],
            'statistics': {},
            'review_statistics': {
                'total_reviewed': 0,
                'kept': 0,
                'removed': 0,
                'by_column_type': defaultdict(lambda: {'kept': 0, 'removed': 0})
            }
        }
        
        # Track rejected items
        self.rejected_data = {
            'rejection_metadata': {
                'rejection_timestamp': datetime.now().isoformat(),
                'original_file': str(self.input_file)
            },
            'rejected_columns': {},
            'rejection_reasons': defaultdict(list),
            'rejection_statistics': defaultdict(int)
        }
        
        # Column type names for display
        self.column_types = {
            'host': 'Host/Hostname',
            'infrastructure_type': 'Infrastructure Type',
            'region': 'Region',
            'country': 'Country',
            'data_center': 'Data Center',
            'cloud_region': 'Cloud Region',
            'business_unit': 'Business Unit',
            'cio': 'CIO',
            'apm': 'APM',
            'app_class': 'Application Class',
            'system_classification': 'System Classification',
            'edr_coverage': 'EDR Coverage',
            'tanium_coverage': 'Tanium Coverage',
            'dlp_agent_coverage': 'DLP Agent Coverage',
            'logging_in_splunk': 'Logging in Splunk',
            'logging_in_gso': 'Logging in GSO',
            'domain': 'Domain',
            'skip': 'Skip (ignored)'
        }
    
    def _load_original_data(self) -> Dict[str, Any]:
        """Load the original manual_labeled_columns.json file"""
        if not self.input_file.exists():
            logger.error(f"Input file {self.input_file} not found!")
            return {}
        
        try:
            with open(self.input_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded original data from {self.input_file}")
                return data
        except Exception as e:
            logger.error(f"Failed to load {self.input_file}: {e}")
            return {}
    
    def start_review_process(self):
        """Start the interactive review process"""
        if not self.original_data:
            logger.error("No data to review!")
            return
        
        print("\n" + "="*80)
        print("COLUMN REVIEW SYSTEM")
        print("="*80)
        print("Review each labeled column and decide whether to keep or remove it.")
        print("\nFor each column, you can:")
        print("  1 = KEEP   (include in final dataset)")
        print("  2 = REMOVE (exclude from final dataset)")
        print("  q = QUIT   (save progress and exit)")
        print("  s = SKIP   (come back to this later)")
        print("  i = INFO   (show more details about this column)")
        print("="*80 + "\n")
        
        # Get overview of what we're reviewing
        self._show_review_overview()
        
        # Review by column type
        self._review_by_column_type()
        
        # Final summary and save
        self._finalize_review()
    
    def _show_review_overview(self):
        """Show an overview of what will be reviewed"""
        columns_data = self.original_data.get('columns', {})
        
        # Count by column type
        type_counts = defaultdict(int)
        total_columns = 0
        
        for table_path, table_labels in columns_data.items():
            for column_name, column_type in table_labels.items():
                if column_type != 'skip':  # Don't review skipped columns
                    type_counts[column_type] += 1
                    total_columns += 1
        
        print("REVIEW OVERVIEW")
        print("-" * 50)
        print(f"Total columns to review: {total_columns}")
        print(f"Tables with labels: {len(columns_data)}")
        print("\nColumns by type:")
        
        for col_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            display_name = self.column_types.get(col_type, col_type)
            print(f"  {display_name:25} {count:6} columns")
        
        print("-" * 50)
        
        # Ask if they want to proceed
        proceed = input("\nProceed with review? (y/n): ").lower().strip()
        if proceed != 'y':
            print("Review cancelled.")
            return False
        
        return True
    
    def _review_by_column_type(self):
        """Review columns organized by type"""
        columns_data = self.original_data.get('columns', {})
        
        # Organize columns by type
        columns_by_type = defaultdict(list)
        
        for table_path, table_labels in columns_data.items():
            for column_name, column_type in table_labels.items():
                if column_type != 'skip':  # Skip the 'skip' columns
                    columns_by_type[column_type].append({
                        'table': table_path,
                        'column': column_name,
                        'type': column_type
                    })
        
        # Review each type
        for column_type in sorted(columns_by_type.keys()):
            columns_list = columns_by_type[column_type]
            display_name = self.column_types.get(column_type, column_type)
            
            print(f"\n" + "="*60)
            print(f"REVIEWING: {display_name.upper()}")
            print("="*60)
            print(f"Found {len(columns_list)} columns of this type")
            
            # Review each column in this type
            for i, column_info in enumerate(columns_list, 1):
                decision = self._review_single_column(column_info, i, len(columns_list))
                
                if decision == 'quit':
                    print("\nQuitting review. Progress saved.")
                    return
                elif decision == 'skip_type':
                    print(f"\nSkipping remaining {display_name} columns.")
                    break
    
    def _review_single_column(self, column_info: Dict[str, Any], index: int, total: int) -> str:
        """Review a single column and get user decision"""
        table_path = column_info['table']
        column_name = column_info['column']
        column_type = column_info['type']
        
        # Create a unique key for this column
        column_key = f"{table_path}#{column_name}"
        
        print(f"\n[{index}/{total}] Column: '{column_name}'")
        print(f"Table: {table_path}")
        print(f"Type: {self.column_types.get(column_type, column_type)}")
        
        # Try to get sample data if available
        self._show_sample_data(table_path, column_name)
        
        while True:
            choice = input("\nDecision (1=keep, 2=remove, i=info, s=skip, q=quit, t=skip type): ").lower().strip()
            
            if choice == '1':
                # Keep this column
                self._keep_column(table_path, column_name, column_type)
                self.reviewed_data['review_statistics']['kept'] += 1
                self.reviewed_data['review_statistics']['by_column_type'][column_type]['kept'] += 1
                print("  ✅ KEPT")
                break
            
            elif choice == '2':
                # Remove this column
                reason = input("  Reason for removal (optional): ").strip()
                self._remove_column(table_path, column_name, column_type, reason)
                self.reviewed_data['review_statistics']['removed'] += 1
                self.reviewed_data['review_statistics']['by_column_type'][column_type]['removed'] += 1
                print("  ❌ REMOVED")
                break
            
            elif choice == 'i':
                # Show more info
                self._show_detailed_info(table_path, column_name, column_type)
                continue
            
            elif choice == 's':
                # Skip this column for now
                print("  ⏭️ SKIPPED")
                return 'skip'
            
            elif choice == 'q':
                # Quit the review
                return 'quit'
            
            elif choice == 't':
                # Skip remaining columns of this type
                return 'skip_type'
            
            else:
                print("  Invalid choice. Please enter 1, 2, i, s, q, or t")
        
        self.reviewed_data['review_statistics']['total_reviewed'] += 1
        return 'continue'
    
    def _show_sample_data(self, table_path: str, column_name: str):
        """Show sample data for this column if available"""
        # Try to find sample data in the original labeling history
        labeling_history = self.original_data.get('labeling_history', [])
        
        for entry in labeling_history:
            if entry.get('table') == table_path:
                print(f"  Table rows: {entry.get('rows', 'unknown')}")
                break
        
        # Try to find pattern examples
        patterns = self.original_data.get('patterns', {})
        for pattern_type, pattern_list in patterns.items():
            if pattern_type == column_name or any(p.get('column') == column_name for p in pattern_list if isinstance(p, dict)):
                print(f"  Found in patterns: {pattern_type}")
                if pattern_list and isinstance(pattern_list[0], dict):
                    sample = pattern_list[0].get('sample')
                    if sample:
                        print(f"  Sample value: {sample}")
                break
    
    def _show_detailed_info(self, table_path: str, column_name: str, column_type: str):
        """Show detailed information about a column"""
        print("\n" + "─" * 50)
        print("DETAILED INFORMATION")
        print("─" * 50)
        print(f"Table: {table_path}")
        print(f"Column: {column_name}")
        print(f"Type: {self.column_types.get(column_type, column_type)}")
        
        # Show project, dataset, table breakdown
        parts = table_path.split('.')
        if len(parts) >= 3:
            print(f"Project: {parts[0]}")
            print(f"Dataset: {parts[1]}")
            print(f"Table Name: {parts[2]}")
        
        # Look for this column in other tables
        columns_data = self.original_data.get('columns', {})
        similar_columns = []
        
        for other_table, other_labels in columns_data.items():
            for other_column, other_type in other_labels.items():
                if other_column == column_name and other_table != table_path:
                    similar_columns.append((other_table, other_type))
        
        if similar_columns:
            print(f"\nSame column name found in {len(similar_columns)} other tables:")
            for other_table, other_type in similar_columns[:5]:  # Show first 5
                print(f"  {other_table} → {other_type}")
            if len(similar_columns) > 5:
                print(f"  ... and {len(similar_columns) - 5} more")
        
        # Show labeling timestamp if available
        labeling_history = self.original_data.get('labeling_history', [])
        for entry in labeling_history:
            if entry.get('table') == table_path:
                timestamp = entry.get('timestamp')
                if timestamp:
                    print(f"Labeled on: {timestamp}")
                break
        
        print("─" * 50)
    
    def _keep_column(self, table_path: str, column_name: str, column_type: str):
        """Keep a column in the reviewed dataset"""
        if table_path not in self.reviewed_data['columns']:
            self.reviewed_data['columns'][table_path] = {}
        
        self.reviewed_data['columns'][table_path][column_name] = column_type
        
        # Also copy to patterns if it exists
        patterns = self.original_data.get('patterns', {})
        if column_type in patterns:
            self.reviewed_data['patterns'][column_type].extend([
                p for p in patterns[column_type] 
                if isinstance(p, dict) and p.get('column') == column_name
            ])
    
    def _remove_column(self, table_path: str, column_name: str, column_type: str, reason: str = ""):
        """Remove a column and track the rejection"""
        column_key = f"{table_path}#{column_name}"
        
        self.rejected_data['rejected_columns'][column_key] = {
            'table': table_path,
            'column': column_name,
            'type': column_type,
            'reason': reason,
            'rejected_at': datetime.now().isoformat()
        }
        
        if reason:
            self.rejected_data['rejection_reasons'][reason].append(column_key)
        
        self.rejected_data['rejection_statistics'][column_type] += 1
    
    def _finalize_review(self):
        """Finalize the review and save results"""
        # Copy over other data that wasn't reviewed
        if 'statistics' in self.original_data:
            self.reviewed_data['statistics'] = self.original_data['statistics']
        
        # Copy labeling history but only for kept tables
        kept_tables = set(self.reviewed_data['columns'].keys())
        original_history = self.original_data.get('labeling_history', [])
        
        self.reviewed_data['labeling_history'] = [
            entry for entry in original_history 
            if entry.get('table') in kept_tables
        ]
        
        # Update statistics
        total_reviewed = self.reviewed_data['review_statistics']['total_reviewed']
        kept = self.reviewed_data['review_statistics']['kept']
        removed = self.reviewed_data['review_statistics']['removed']
        
        print(f"\n" + "="*60)
        print("REVIEW COMPLETE")
        print("="*60)
        print(f"Total reviewed: {total_reviewed}")
        print(f"Kept: {kept} ({kept/total_reviewed*100:.1f}%)")
        print(f"Removed: {removed} ({removed/total_reviewed*100:.1f}%)")
        
        print(f"\nBy column type:")
        for col_type, stats in self.reviewed_data['review_statistics']['by_column_type'].items():
            type_kept = stats['kept']
            type_removed = stats['removed']
            type_total = type_kept + type_removed
            if type_total > 0:
                display_name = self.column_types.get(col_type, col_type)
                print(f"  {display_name:25} Kept: {type_kept:3} Removed: {type_removed:3} ({type_kept/type_total*100:.1f}% kept)")
        
        # Save files
        self._save_results()
        
        print(f"\n📁 Results saved:")
        print(f"  Reviewed data: {self.output_file}")
        print(f"  Rejected data: {self.rejected_file}")
        print("="*60)
    
    def _save_results(self):
        """Save the reviewed and rejected data"""
        # Save reviewed data
        with open(self.output_file, 'w') as f:
            json.dump(self.reviewed_data, f, indent=2, default=str)
        
        # Save rejected data
        with open(self.rejected_file, 'w') as f:
            json.dump(self.rejected_data, f, indent=2, default=str)
        
        logger.info(f"Saved reviewed data to {self.output_file}")
        logger.info(f"Saved rejected data to {self.rejected_file}")
    
    def resume_review(self):
        """Resume a previous review session"""
        if self.output_file.exists():
            print("Found existing review file. Resume from where you left off? (y/n): ")
            if input().lower().strip() == 'y':
                with open(self.output_file, 'r') as f:
                    self.reviewed_data = json.load(f)
                
                if self.rejected_file.exists():
                    with open(self.rejected_file, 'r') as f:
                        self.rejected_data = json.load(f)
                
                print("Resumed from previous session.")
                return True
        
        return False
    
    def show_statistics(self):
        """Show current review statistics"""
        if not self.reviewed_data['review_statistics']['total_reviewed']:
            print("No review progress yet.")
            return
        
        stats = self.reviewed_data['review_statistics']
        print(f"\nCurrent Review Progress:")
        print(f"Total reviewed: {stats['total_reviewed']}")
        print(f"Kept: {stats['kept']}")
        print(f"Removed: {stats['removed']}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Review and filter manually labeled columns')
    parser.add_argument(
        '--input',
        default='manual_labeled_columns.json',
        help='Input file with manual labels (default: manual_labeled_columns.json)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume previous review session'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show current review statistics'
    )
    
    args = parser.parse_args()
    
    reviewer = ColumnReviewer(input_file=args.input)
    
    if args.stats:
        reviewer.show_statistics()
        return
    
    if args.resume and reviewer.resume_review():
        reviewer.start_review_process()
    else:
        reviewer.start_review_process()

if __name__ == "__main__":
    main()