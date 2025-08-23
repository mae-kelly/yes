#!/usr/bin/env python3
"""
Simple Table Extractor - extract_tables.py
Reads reviewed_labeled_columns.json and creates a clean JSON with just table paths and their column mappings
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_tables_simple(input_file='reviewed_labeled_columns.json', output_file='extracted_tables.json'):
    """Extract tables and columns to a clean JSON format"""
    
    # Load the input JSON
    input_path = Path(input_file)
    if not input_path.exists():
        logger.error(f"File {input_file} not found!")
        return
    
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
        logger.info(f"✅ Loaded {input_file}")
    except Exception as e:
        logger.error(f"❌ Failed to load {input_file}: {e}")
        return
    
    # Extract just the columns section
    columns_data = data.get('columns', {})
    
    if not columns_data:
        logger.error("No columns data found in JSON!")
        return
    
    print(f"\n📊 Found {len(columns_data)} tables")
    
    # Create the clean output - just the table mappings
    clean_data = {}
    
    for table_path, table_columns in columns_data.items():
        print(f"📋 {table_path} → {len(table_columns)} columns")
        clean_data[table_path] = table_columns
    
    # Save the clean JSON
    with open(output_file, 'w') as f:
        json.dump(clean_data, f, indent=2)
    
    logger.info(f"💾 Saved clean table mappings to {output_file}")
    print(f"\n✅ Extraction complete!")
    print(f"📁 Output: {output_file}")
    print(f"📊 Tables: {len(clean_data)}")
    
    # Show sample of what was extracted
    if clean_data:
        sample_table = next(iter(clean_data.keys()))
        sample_columns = clean_data[sample_table]
        print(f"\n📋 Sample table: {sample_table}")
        for col_name, col_type in list(sample_columns.items())[:3]:
            print(f"   {col_name} → {col_type}")
        if len(sample_columns) > 3:
            print(f"   ... and {len(sample_columns) - 3} more columns")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract clean table mappings from reviewed_labeled_columns.json')
    parser.add_argument(
        '--input',
        default='reviewed_labeled_columns.json',
        help='Input JSON file (default: reviewed_labeled_columns.json)'
    )
    parser.add_argument(
        '--output',
        default='extracted_tables.json',
        help='Output JSON file (default: extracted_tables.json)'
    )
    
    args = parser.parse_args()
    
    extract_tables_simple(args.input, args.output)

if __name__ == "__main__":
    main()