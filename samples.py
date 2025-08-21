#!/usr/bin/env python3
"""
Simple script to extract BigQuery samples based on labeled columns
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_json_structure():
    """First, let's see what's actually in these JSON files"""
    
    separated_dir = Path('separated_labels')
    
    # Find a test file
    test_files = list(separated_dir.glob('*.json'))
    
    if not test_files:
        logger.error(f"No JSON files found in {separated_dir}")
        return
    
    # Test with the first file
    test_file = test_files[0]
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing with: {test_file.name}")
    logger.info('='*60)
    
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    # Show structure
    logger.info(f"Type of data: {type(data)}")
    
    if isinstance(data, dict):
        logger.info(f"Keys in data: {list(data.keys())}")
        
        if 'columns' in data:
            columns = data['columns']
            logger.info(f"Type of 'columns': {type(columns)}")
            
            if isinstance(columns, dict):
                # Show first few entries
                logger.info(f"Number of entries: {len(columns)}")
                logger.info("\nFirst 3 entries:")
                for i, (k, v) in enumerate(list(columns.items())[:3]):
                    logger.info(f"  {k} -> {v}")
                    
                # Count unique column names
                unique_columns = set(columns.values())
                logger.info(f"\nUnique column names: {unique_columns}")
    
    elif isinstance(data, list):
        logger.info(f"Data is a list with {len(data)} items")
        if data:
            logger.info(f"First item type: {type(data[0])}")
            logger.info(f"First item: {data[0]}")

def simple_extract_samples():
    """Simple extraction without all the complexity"""
    
    separated_dir = Path('separated_labels')
    output_dir = Path('column_samples')
    output_dir.mkdir(exist_ok=True)
    
    # Import BigQuery client
    try:
        from gcp.client import BigQueryClientManager
        logger.info("✅ Imported BigQueryClientManager")
    except ImportError as e:
        logger.error(f"❌ Cannot import BigQueryClientManager: {e}")
        return
    
    # Process one file as a test
    test_file = separated_dir / 'eleven_system_classifications.json'
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {test_file.name}")
    logger.info('='*60)
    
    # Load the file
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, dict) or 'columns' not in data:
        logger.error("Unexpected structure")
        return
    
    columns_dict = data['columns']
    
    # Group by column name
    from collections import defaultdict
    by_column = defaultdict(list)
    
    for table_path, column_name in columns_dict.items():
        if column_name != 'skip':
            by_column[column_name].append(table_path)
    
    logger.info(f"Found {len(by_column)} unique column names")
    
    # For each unique column, get samples
    all_samples = {}
    
    # Get unique projects
    projects = set()
    for table_path in columns_dict.keys():
        if '.' in table_path:
            project = table_path.split('.')[0]
            projects.add(project)
    
    logger.info(f"Projects: {projects}")
    
    # Initialize clients
    clients = {}
    for project in projects:
        try:
            manager = BigQueryClientManager(project)
            if manager.test_connection():
                clients[project] = manager
                logger.info(f"✅ Connected to {project}")
            else:
                logger.error(f"❌ Failed to connect to {project}")
        except Exception as e:
            logger.error(f"❌ Error with {project}: {e}")
    
    if not clients:
        logger.error("No successful connections")
        return
    
    # Now get samples for each column
    for column_name, table_paths in by_column.items():
        logger.info(f"\n📊 Column: {column_name}")
        logger.info(f"   Found in {len(table_paths)} tables")
        
        samples = []
        tables_checked = 0
        max_tables = 3  # Just check a few tables
        
        for table_path in table_paths[:max_tables]:
            if '.' not in table_path:
                continue
                
            parts = table_path.split('.')
            if len(parts) != 3:
                continue
                
            project, dataset, table = parts
            
            if project not in clients:
                continue
            
            manager = clients[project]
            
            try:
                with manager.get_client() as client:
                    # Simple query
                    query = f"""
                    SELECT DISTINCT `{column_name}` as value
                    FROM `{table_path}`
                    WHERE `{column_name}` IS NOT NULL
                    LIMIT 10
                    """
                    
                    logger.info(f"   Querying {table_path}...")
                    
                    query_job = client.query(query)
                    results = list(query_job.result(timeout=30))
                    
                    for row in results:
                        value = row.value
                        if value is not None:
                            samples.append(str(value)[:200])
                    
                    tables_checked += 1
                    logger.info(f"   ✅ Got {len(results)} values")
                    
            except Exception as e:
                logger.error(f"   ❌ Query failed: {str(e)[:100]}")
                continue
        
        all_samples[column_name] = {
            'samples': samples[:20],
            'tables_checked': tables_checked,
            'total_tables': len(table_paths)
        }
        
        logger.info(f"   Total samples collected: {len(samples)}")
    
    # Save results
    output_file = output_dir / 'test_samples.json'
    
    output_data = {
        'file': test_file.name,
        'timestamp': datetime.now().isoformat(),
        'columns': all_samples
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"\n💾 Saved to: {output_file}")
    
    # Also create a simple text report
    report_file = output_dir / 'test_samples.txt'
    with open(report_file, 'w') as f:
        f.write(f"Sample Report\n")
        f.write(f"={'='*60}\n\n")
        
        for col_name, col_data in all_samples.items():
            f.write(f"Column: {col_name}\n")
            f.write(f"Tables: {col_data['total_tables']}\n")
            f.write(f"Samples:\n")
            for i, sample in enumerate(col_data['samples'][:10], 1):
                f.write(f"  {i}. {sample}\n")
            f.write("\n")
    
    logger.info(f"📄 Report saved to: {report_file}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple column sample extractor')
    parser.add_argument('--test-structure', action='store_true', help='Just test JSON structure')
    parser.add_argument('--extract', action='store_true', help='Extract samples')
    
    args = parser.parse_args()
    
    if args.test_structure:
        test_json_structure()
    elif args.extract:
        simple_extract_samples()
    else:
        # Default: do both
        test_json_structure()
        print("\n" + "="*60 + "\n")
        simple_extract_samples()

if __name__ == "__main__":
    main()