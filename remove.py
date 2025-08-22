#!/usr/bin/env python3
"""
Script to remove tables that don't have any 'host' columns 
directly from reviewed_labeled_columns.json (in-place modification)
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def remove_tables_without_host(filename: str = 'reviewed_labeled_columns.json', backup: bool = True):
    """Remove tables without host columns from the file"""
    
    filepath = Path(filename)
    
    # Check if file exists
    if not filepath.exists():
        logger.error(f"File {filename} not found!")
        return
    
    # Load the data
    print(f"\n📂 Loading {filename}...")
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Create backup if requested
    if backup:
        backup_file = filepath.with_suffix('.backup.json')
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"📁 Backup saved to {backup_file}")
    
    # Get columns data
    columns_data = data.get('columns', {})
    original_count = len(columns_data)
    
    print(f"\n🔍 Analyzing {original_count} tables...")
    
    # Find tables to keep (those with host columns)
    tables_to_keep = {}
    tables_to_remove = []
    
    for table_path, table_columns in columns_data.items():
        has_host = any(col_type == 'host' for col_type in table_columns.values())
        
        if has_host:
            tables_to_keep[table_path] = table_columns
        else:
            tables_to_remove.append(table_path)
    
    # Show what will be removed
    print(f"\n📊 Results:")
    print(f"  - Tables with host columns: {len(tables_to_keep)}")
    print(f"  - Tables without host columns: {len(tables_to_remove)}")
    
    if tables_to_remove:
        print(f"\n❌ Removing {len(tables_to_remove)} tables without host columns:")
        for i, table in enumerate(tables_to_remove[:10], 1):
            print(f"  {i:3}. {table}")
        if len(tables_to_remove) > 10:
            print(f"  ... and {len(tables_to_remove) - 10} more")
    
    # Update the columns
    data['columns'] = tables_to_keep
    
    # Update labeling_history to only include kept tables
    if 'labeling_history' in data:
        original_history_count = len(data['labeling_history'])
        data['labeling_history'] = [
            entry for entry in data['labeling_history']
            if entry.get('table') in tables_to_keep
        ]
        removed_history = original_history_count - len(data['labeling_history'])
        if removed_history > 0:
            print(f"\n🔄 Also removed {removed_history} history entries for removed tables")
    
    # Update patterns if they exist - remove references to removed tables
    if 'patterns' in data:
        for pattern_type, pattern_list in data['patterns'].items():
            if isinstance(pattern_list, list):
                filtered_patterns = []
                for pattern in pattern_list:
                    if isinstance(pattern, dict) and 'table' in pattern:
                        if pattern['table'] in tables_to_keep:
                            filtered_patterns.append(pattern)
                    else:
                        filtered_patterns.append(pattern)
                data['patterns'][pattern_type] = filtered_patterns
    
    # Add metadata about this filtering operation
    if 'filter_metadata' not in data:
        data['filter_metadata'] = {}
    
    data['filter_metadata']['removed_tables_without_host'] = {
        'timestamp': datetime.now().isoformat(),
        'tables_removed': len(tables_to_remove),
        'tables_kept': len(tables_to_keep),
        'original_table_count': original_count
    }
    
    # Count total columns
    total_columns = sum(len(cols) for cols in tables_to_keep.values())
    host_columns = sum(sum(1 for c in cols.values() if c == 'host') for cols in tables_to_keep.values())
    
    print(f"\n📈 Final statistics:")
    print(f"  - Tables remaining: {len(tables_to_keep)}")
    print(f"  - Total columns: {total_columns}")
    print(f"  - Host columns: {host_columns}")
    print(f"  - Other columns: {total_columns - host_columns}")
    
    # Save the updated data back to the same file
    print(f"\n💾 Saving changes to {filename}...")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Done! Removed {len(tables_to_remove)} tables without host columns from {filename}")
    
    if backup:
        print(f"\n💡 To restore original: cp {backup_file} {filename}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Remove tables without host columns from reviewed_labeled_columns.json'
    )
    parser.add_argument(
        '--file',
        default='reviewed_labeled_columns.json',
        help='JSON file to modify (default: reviewed_labeled_columns.json)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create a backup file before modifying'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be removed without actually modifying the file'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"❌ File {args.file} not found!")
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        columns_data = data.get('columns', {})
        tables_with_host = []
        tables_without_host = []
        
        for table_path, table_columns in columns_data.items():
            has_host = any(col_type == 'host' for col_type in table_columns.values())
            if has_host:
                tables_with_host.append(table_path)
            else:
                tables_without_host.append(table_path)
        
        print(f"\n📊 Analysis of {args.file}:")
        print(f"  Total tables: {len(columns_data)}")
        print(f"  Tables WITH host columns: {len(tables_with_host)} (would be kept)")
        print(f"  Tables WITHOUT host columns: {len(tables_without_host)} (would be removed)")
        
        if tables_without_host:
            print(f"\nTables that would be removed:")
            for i, table in enumerate(tables_without_host[:20], 1):
                print(f"  {i:3}. {table}")
            if len(tables_without_host) > 20:
                print(f"  ... and {len(tables_without_host) - 20} more")
    else:
        remove_tables_without_host(args.file, backup=not args.no_backup)

if __name__ == "__main__":
    main()