#!/usr/bin/env python3
"""
Script to review and filter ONLY hostname columns from manual_labeled_columns.json
Allows users to keep (1) or remove (2) each labeled hostname column entry.
Shows 10 sample values for each column to aid in decision making.
All other column types are automatically kept without review.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict, Counter
import sys
import os

# Add the project path to find gcp.client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HostColumnReviewer:
    def __init__(self, input_file: str = 'manual_labeled_columns.json'):
        self.input_file = Path(input_file)
        self.output_file = Path('reviewed_labeled_columns.json')
        self.rejected_file = Path('rejected_hostname_columns.json')
        
        # Load the original data first
        self.original_data = self._load_original_data()
        
        # Initialize BigQuery clients for fetching sample data
        self.client_managers = {}
        self._initialize_bigquery_clients()
        
        # Initialize reviewed data structure
        self.reviewed_data = {
            'review_metadata': {
                'review_timestamp': datetime.now().isoformat(),
                'original_file': str(self.input_file),
                'reviewer_version': '1.0.0',
                'review_scope': 'hostname_columns_only'
            },
            'columns': {},
            'patterns': defaultdict(list),
            'labeling_history': [],
            'statistics': {},
            'review_statistics': {
                'total_reviewed': 0,
                'hostname_columns_reviewed': 0,
                'hostname_columns_kept': 0,
                'hostname_columns_removed': 0,
                'other_columns_auto_kept': 0,
                'by_column_type': defaultdict(lambda: {'kept': 0, 'removed': 0, 'auto_kept': 0})
            }
        }
        
        # Track rejected hostname columns only
        self.rejected_data = {
            'rejection_metadata': {
                'rejection_timestamp': datetime.now().isoformat(),
                'original_file': str(self.input_file),
                'rejection_scope': 'hostname_columns_only'
            },
            'rejected_hostname_columns': {},
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
    
    def _initialize_bigquery_clients(self):
        """Initialize BigQuery clients for all projects in the labeled data"""
        try:
            from gcp.client import BigQueryClientManager
        except ImportError:
            logger.warning("BigQuery client not available. Sample data will be limited to cached patterns.")
            return
        
        # Extract project IDs from the labeled data
        columns_data = self.original_data.get('columns', {})
        project_ids = set()
        
        for table_path in columns_data.keys():
            parts = table_path.split('.')
            if len(parts) >= 1:
                project_ids.add(parts[0])
        
        # Initialize clients for each project
        for project_id in project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                if manager.test_connection():
                    self.client_managers[project_id] = manager
                    logger.info(f"✅ Connected to project: {project_id}")
                else:
                    logger.warning(f"⚠️ Failed to connect to project: {project_id}")
            except Exception as e:
                logger.warning(f"❌ Could not connect to {project_id}: {e}")
        
        if self.client_managers:
            logger.info(f"Initialized BigQuery clients for {len(self.client_managers)} projects")
        else:
            logger.warning("No BigQuery connections available. Sample data will be limited.")
    
    def _fetch_sample_values(self, table_path: str, column_name: str, limit: int = 10) -> List[Any]:
        """Fetch sample values from BigQuery for the specified column"""
        if not self.client_managers:
            return []
        
        # Extract project ID from table path
        parts = table_path.split('.')
        if len(parts) < 3:
            return []
        
        project_id = parts[0]
        manager = self.client_managers.get(project_id)
        
        if not manager:
            return []
        
        try:
            with manager.get_client() as client:
                # Build safe query with proper column name escaping
                safe_column = f"`{column_name}`"
                
                query = f"""
                SELECT DISTINCT {safe_column} as sample_value
                FROM `{table_path}`
                WHERE {safe_column} IS NOT NULL
                AND {safe_column} != ''
                AND {safe_column} != 'null'
                AND {safe_column} != 'NULL'
                LIMIT {limit}
                """
                
                query_job = client.query(query)
                results = query_job.result(timeout=30)
                
                samples = []
                for row in results:
                    value = row.sample_value
                    if value is not None:
                        samples.append(value)
                
                return samples
                
        except Exception as e:
            logger.debug(f"Failed to fetch samples for {table_path}.{column_name}: {e}")
            return []
    
    def start_review_process(self):
        """Start the interactive review process for hostname columns only"""
        if not self.original_data:
            logger.error("No data to review!")
            return
        
        print("\n" + "="*80)
        print("HOSTNAME COLUMN REVIEW SYSTEM")
        print("="*80)
        print("Review ONLY hostname columns and decide whether to keep or remove them.")
        print("All other column types will be automatically kept.")
        print("\nFor each HOSTNAME column, you can:")
        print("  1 = KEEP   (include in final dataset)")
        print("  2 = REMOVE (exclude from final dataset)")
        print("  q = QUIT   (save progress and exit)")
        print("  s = SKIP   (come back to this later)")
        print("  i = INFO   (show more details about this column)")
        print("="*80 + "\n")
        
        # Get overview of what we're reviewing
        if not self._show_review_overview():
            return
        
        # Review hostname columns only
        self._review_hostname_columns()
        
        # Final summary and save
        self._finalize_review()
    
    def _show_review_overview(self):
        """Show an overview of what will be reviewed"""
        columns_data = self.original_data.get('columns', {})
        
        # Count hostname columns only
        hostname_columns = 0
        total_all_columns = 0
        type_counts = defaultdict(int)
        
        for table_path, table_labels in columns_data.items():
            for column_name, column_type in table_labels.items():
                if column_type != 'skip':
                    type_counts[column_type] += 1
                    total_all_columns += 1
                    if column_type == 'host':
                        hostname_columns += 1
        
        print("HOSTNAME COLUMN REVIEW OVERVIEW")
        print("-" * 50)
        print(f"🎯 HOSTNAME COLUMNS TO REVIEW: {hostname_columns}")
        print(f"Total columns in dataset: {total_all_columns}")
        print(f"Tables with labels: {len(columns_data)}")
        
        if hostname_columns == 0:
            print("\n❌ No hostname columns found to review!")
            return False
        
        print(f"\nOther column types in dataset (for reference):")
        for col_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            if col_type != 'host':  # Don't show host count again
                display_name = self.column_types.get(col_type, col_type)
                print(f"  {display_name:25} {count:6} columns (will be auto-kept)")
        
        print("-" * 50)
        print("📝 NOTE: Only reviewing HOSTNAME columns (type='host')")
        print("   All other column types will be automatically kept as-is.")
        
        # Ask if they want to proceed
        proceed = input(f"\nProceed with reviewing {hostname_columns} hostname columns? (y/n): ").lower().strip()
        if proceed != 'y':
            print("Review cancelled.")
            return False
        
        return True
    
    def _review_hostname_columns(self):
        """Review hostname columns only"""
        columns_data = self.original_data.get('columns', {})
        
        # Find only hostname columns
        hostname_columns = []
        
        for table_path, table_labels in columns_data.items():
            for column_name, column_type in table_labels.items():
                if column_type == 'host':  # Only review hostname columns
                    hostname_columns.append({
                        'table': table_path,
                        'column': column_name,
                        'type': column_type
                    })
        
        if not hostname_columns:
            print("❌ No hostname columns found to review!")
            return
        
        print(f"\n" + "="*60)
        print(f"REVIEWING: HOSTNAME COLUMNS ONLY")
        print("="*60)
        print(f"Found {len(hostname_columns)} hostname columns to review")
        print("All other column types will be automatically kept as-is.")
        
        # Review each hostname column
        for i, column_info in enumerate(hostname_columns, 1):
            decision = self._review_single_hostname_column(column_info, i, len(hostname_columns))
            
            if decision == 'quit':
                print("\nQuitting review. Progress saved.")
                return
        
        # Automatically copy all non-hostname columns to the reviewed data
        self._copy_non_hostname_columns(columns_data)
    
    def _review_single_hostname_column(self, column_info: Dict[str, Any], index: int, total: int) -> str:
        """Review a single hostname column and get user decision"""
        table_path = column_info['table']
        column_name = column_info['column']
        column_type = column_info['type']
        
        print(f"\n[{index}/{total}] HOSTNAME Column: '{column_name}'")
        print(f"Table: {table_path}")
        print(f"Type: {self.column_types.get(column_type, column_type)}")
        
        # Show sample data for this column
        self._show_sample_data(table_path, column_name)
        
        while True:
            choice = input("\nDecision (1=keep, 2=remove, i=info, s=skip, q=quit): ").lower().strip()
            
            if choice == '1':
                # Keep this hostname column
                self._keep_hostname_column(table_path, column_name, column_type)
                self.reviewed_data['review_statistics']['hostname_columns_kept'] += 1
                self.reviewed_data['review_statistics']['by_column_type'][column_type]['kept'] += 1
                print("  ✅ KEPT")
                break
            
            elif choice == '2':
                # Remove this hostname column
                reason = input("  Reason for removal (optional): ").strip()
                self._remove_hostname_column(table_path, column_name, column_type, reason)
                self.reviewed_data['review_statistics']['hostname_columns_removed'] += 1
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
            
            else:
                print("  Invalid choice. Please enter 1, 2, i, s, or q")
        
        self.reviewed_data['review_statistics']['hostname_columns_reviewed'] += 1
        return 'continue'
    
    def _copy_non_hostname_columns(self, columns_data: Dict[str, Dict[str, str]]):
        """Automatically copy all non-hostname columns to the reviewed dataset"""
        copied_count = 0
        
        print(f"\n📋 Automatically copying all non-hostname columns...")
        
        for table_path, table_labels in columns_data.items():
            for column_name, column_type in table_labels.items():
                if column_type != 'host' and column_type != 'skip':
                    # Automatically keep all non-hostname columns
                    if table_path not in self.reviewed_data['columns']:
                        self.reviewed_data['columns'][table_path] = {}
                    
                    self.reviewed_data['columns'][table_path][column_name] = column_type
                    copied_count += 1
                    
                    # Update statistics
                    self.reviewed_data['review_statistics']['other_columns_auto_kept'] += 1
                    self.reviewed_data['review_statistics']['by_column_type'][column_type]['auto_kept'] += 1
        
        print(f"✅ Automatically kept {copied_count} non-hostname columns")
        print("   (These were not reviewed since you only wanted to review hostnames)")
    
    def _show_sample_data(self, table_path: str, column_name: str):
        """Show sample data for this column"""
        # Try to find sample data in the original labeling history
        labeling_history = self.original_data.get('labeling_history', [])
        
        for entry in labeling_history:
            if entry.get('table') == table_path:
                print(f"  Table rows: {entry.get('rows', 'unknown'):,}")
                break
        
        # Get 10 sample values by querying BigQuery
        samples = self._fetch_sample_values(table_path, column_name, limit=10)
        
        if samples:
            print(f"  Sample hostname values (showing {len(samples)} live samples):")
            for i, sample in enumerate(samples, 1):
                # Truncate very long values
                display_value = str(sample)[:100] + "..." if len(str(sample)) > 100 else str(sample)
                print(f"    {i:2}. {display_value}")
        else:
            # Fallback to pattern examples if we can't get live samples
            print("  (Could not fetch live samples)")
            
            # Try to show cached samples from other columns with same name
            self._show_cached_hostname_samples(column_name)
    
    def _show_cached_hostname_samples(self, column_name: str):
        """Show cached hostname samples from other tables with the same column name"""
        columns_data = self.original_data.get('columns', {})
        found_samples = []
        
        # Look for this column name in other tables and try to get samples
        for other_table, other_labels in columns_data.items():
            if column_name in other_labels and other_labels[column_name] == 'host' and len(found_samples) < 10:
                # Try to get a few samples from this table
                table_samples = self._fetch_sample_values(other_table, column_name, limit=3)
                found_samples.extend(table_samples)
                
                if len(found_samples) >= 10:
                    break
        
        if found_samples:
            print(f"  Sample hostname values from other tables with '{column_name}':")
            for i, sample in enumerate(found_samples[:10], 1):
                display_value = str(sample)[:100] + "..." if len(str(sample)) > 100 else str(sample)
                print(f"    {i:2}. {display_value}")
    
    def _show_detailed_info(self, table_path: str, column_name: str, column_type: str):
        """Show detailed information about a hostname column"""
        print("\n" + "─" * 50)
        print("DETAILED HOSTNAME COLUMN INFORMATION")
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
        
        # Get extended sample data for detailed view
        extended_samples = self._fetch_sample_values(table_path, column_name, limit=20)
        if extended_samples:
            print(f"\nExtended hostname samples ({len(extended_samples)} values):")
            for i, sample in enumerate(extended_samples, 1):
                display_value = str(sample)[:150] + "..." if len(str(sample)) > 150 else str(sample)
                print(f"  {i:2}. {display_value}")
        
        # Look for this hostname column in other tables
        columns_data = self.original_data.get('columns', {})
        similar_columns = []
        
        for other_table, other_labels in columns_data.items():
            for other_column, other_type in other_labels.items():
                if other_column == column_name and other_table != table_path and other_type == 'host':
                    similar_columns.append((other_table, other_type))
        
        if similar_columns:
            print(f"\nSame hostname column found in {len(similar_columns)} other tables:")
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
                    print(f"\nLabeled on: {timestamp}")
                break
        
        print("─" * 50)
    
    def _keep_hostname_column(self, table_path: str, column_name: str, column_type: str):
        """Keep a hostname column in the reviewed dataset"""
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
    
    def _remove_hostname_column(self, table_path: str, column_name: str, column_type: str, reason: str = ""):
        """Remove a hostname column and track the rejection"""
        column_key = f"{table_path}#{column_name}"
        
        self.rejected_data['rejected_hostname_columns'][column_key] = {
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
        hostname_reviewed = self.reviewed_data['review_statistics']['hostname_columns_reviewed']
        hostname_kept = self.reviewed_data['review_statistics']['hostname_columns_kept']
        hostname_removed = self.reviewed_data['review_statistics']['hostname_columns_removed']
        other_kept = self.reviewed_data['review_statistics']['other_columns_auto_kept']
        
        total_reviewed = hostname_reviewed
        total_kept = hostname_kept + other_kept
        
        print(f"\n" + "="*60)
        print("HOSTNAME COLUMN REVIEW COMPLETE")
        print("="*60)
        print(f"Hostname columns reviewed: {hostname_reviewed}")
        print(f"Hostname columns kept: {hostname_kept}")
        print(f"Hostname columns removed: {hostname_removed}")
        print(f"Other columns auto-kept: {other_kept}")
        print(f"Total columns in final dataset: {total_kept}")
        
        if hostname_reviewed > 0:
            hostname_keep_rate = (hostname_kept / hostname_reviewed) * 100
            print(f"Hostname keep rate: {hostname_keep_rate:.1f}%")
        
        print(f"\nBy column type:")
        for col_type, stats in self.reviewed_data['review_statistics']['by_column_type'].items():
            type_kept = stats['kept']
            type_removed = stats['removed']
            type_auto_kept = stats['auto_kept']
            type_total = type_kept + type_removed + type_auto_kept
            
            if type_total > 0:
                display_name = self.column_types.get(col_type, col_type)
                if col_type == 'host':
                    print(f"  {display_name:25} Reviewed: {type_kept + type_removed:3} Kept: {type_kept:3} Removed: {type_removed:3}")
                else:
                    print(f"  {display_name:25} Auto-kept: {type_auto_kept:3} (not reviewed)")
        
        # Save files
        self._save_results()
        
        print(f"\n📁 Results saved:")
        print(f"  Reviewed data: {self.output_file}")
        print(f"  Rejected hostnames: {self.rejected_file}")
        print("\n📝 NOTE: Only hostname columns were reviewed.")
        print("   All other column types were automatically kept.")
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
        logger.info(f"Saved rejected hostname columns to {self.rejected_file}")
    
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
        stats = self.reviewed_data['review_statistics']
        if not stats['hostname_columns_reviewed']:
            print("No hostname review progress yet.")
            return
        
        print(f"\nCurrent Hostname Review Progress:")
        print(f"Hostname columns reviewed: {stats['hostname_columns_reviewed']}")
        print(f"Hostname columns kept: {stats['hostname_columns_kept']}")
        print(f"Hostname columns removed: {stats['hostname_columns_removed']}")
        print(f"Other columns auto-kept: {stats['other_columns_auto_kept']}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Review and filter hostname columns only')
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
    
    reviewer = HostColumnReviewer(input_file=args.input)
    
    if args.stats:
        reviewer.show_statistics()
        return
    
    if args.resume and reviewer.resume_review():
        reviewer.start_review_process()
    else:
        reviewer.start_review_process()

if __name__ == "__main__":
    main()