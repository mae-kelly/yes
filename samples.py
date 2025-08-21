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

def extract_samples_for_file(json_file_path, column_type):
    """Extract samples for a single JSON file"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {json_file_path}")
    logger.info('='*60)
    
    # Import BigQuery client
    try:
        from gcp.client import BigQueryClientManager
    except ImportError as e:
        logger.error(f"Cannot import BigQueryClientManager: {e}")
        return
    
    # Load the JSON file
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # The structure is {"columns": {"table_path": "column_name", ...}}
    if not isinstance(data, dict):
        logger.error(f"Root is not a dict, it's: {type(data)}")
        return
        
    if 'columns' not in data:
        logger.error(f"No 'columns' key. Keys are: {list(data.keys())}")
        return
    
    columns_mapping = data['columns']
    
    if not isinstance(columns_mapping, dict):
        logger.error(f"'columns' is not a dict, it's: {type(columns_mapping)}")
        return
    
    logger.info(f"Found {len(columns_mapping)} table-column mappings")
    
    # Group tables by column name (reverse the mapping)
    from collections import defaultdict
    column_to_tables = defaultdict(list)
    
    for table_path, column_name in columns_mapping.items():
        if column_name and column_name != 'skip':
            column_to_tables[column_name].append(table_path)
    
    logger.info(f"Unique column names: {list(column_to_tables.keys())}")
    
    # Get unique projects
    projects = set()
    for table_path in columns_mapping.keys():
        if '.' in table_path:
            project = table_path.split('.')[0]
            projects.add(project)
    
    logger.info(f"Projects needed: {projects}")
    
    # Connect to BigQuery
    clients = {}
    for project in projects:
        try:
            manager = BigQueryClientManager(project)
            if manager.test_connection():
                clients[project] = manager
                logger.info(f"✅ Connected to {project}")
        except Exception as e:
            logger.error(f"❌ Cannot connect to {project}: {e}")
    
    if not clients:
        logger.error("No successful BigQuery connections")
        return
    
    # Collect samples for each column
    output_data = {
        'column_type': column_type,
        'timestamp': datetime.now().isoformat(),
        'columns': {}
    }
    
    for column_name, table_list in column_to_tables.items():
        logger.info(f"\n📊 Getting samples for column: '{column_name}'")
        logger.info(f"   Found in {len(table_list)} tables")
        
        all_samples = []
        tables_sampled = 0
        
        # Sample from up to 3 tables
        for table_path in table_list[:3]:
            parts = table_path.split('.')
            if len(parts) != 3:
                continue
            
            project_id = parts[0]
            dataset_id = parts[1]
            table_id = parts[2]
            
            if project_id not in clients:
                continue
            
            manager = clients[project_id]
            
            try:
                with manager.get_client() as client:
                    # Build query
                    query = f"""
                    SELECT `{column_name}` as value
                    FROM `{project_id}.{dataset_id}.{table_id}`
                    WHERE `{column_name}` IS NOT NULL
                    LIMIT 20
                    """
                    
                    # Execute query
                    query_job = client.query(query)
                    results = list(query_job.result(timeout=30))
                    
                    for row in results:
                        if row.value is not None:
                            value_str = str(row.value)[:500]
                            all_samples.append(value_str)
                    
                    tables_sampled += 1
                    logger.info(f"   ✅ Got {len(results)} samples from {table_path}")
                    
            except Exception as e:
                logger.debug(f"   ❌ Failed to query {table_path}: {str(e)[:100]}")
        
        output_data['columns'][column_name] = {
            'total_tables': len(table_list),
            'tables_sampled': tables_sampled,
            'sample_count': len(all_samples),
            'samples': all_samples[:50]  # Limit to 50 samples
        }
    
    return output_data

def main():
    """Process all separated JSON files"""
    
    separated_dir = Path('separated_labels')
    output_dir = Path('column_samples')
    output_dir.mkdir(exist_ok=True)
    
    # Mapping of files to column types
    file_mappings = {
        'one_hosts.json': 'host',
        'two_infrastructure_types.json': 'infrastructure_type',
        'three_regions.json': 'region',
        'four_countries.json': 'country',
        'five_data_centers.json': 'data_center',
        'six_cloud_regions.json': 'cloud_region',
        'seven_business_units.json': 'business_unit',
        'eight_cios.json': 'cio',
        'nine_apms.json': 'apm',
        'ten_app_classes.json': 'app_class',
        'eleven_system_classifications.json': 'system_classification',
        'twelve_edr_coverages.json': 'edr_coverage',
        'thirteen_tanium_coverages.json': 'tanium_coverage',
        'fourteen_dlp_coverages.json': 'dlp_agent_coverage',
        'fifteen_splunk_loggings.json': 'logging_in_splunk',
        'sixteen_gso_loggings.json': 'logging_in_gso',
        'seventeen_domains.json': 'domain'
    }
    
    # Process each file
    for filename, column_type in file_mappings.items():
        json_file = separated_dir / filename
        
        if not json_file.exists():
            logger.warning(f"File not found: {json_file}")
            continue
        
        try:
            result = extract_samples_for_file(json_file, column_type)
            
            if result:
                # Save JSON output
                output_file = output_dir / f"{column_type}_samples.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"💾 Saved: {output_file}")
                
                # Save text summary
                summary_file = output_dir / f"{column_type}_summary.txt"
                with open(summary_file, 'w') as f:
                    f.write(f"Column Type: {column_type}\n")
                    f.write("="*60 + "\n\n")
                    
                    for col_name, col_data in result['columns'].items():
                        f.write(f"Column: {col_name}\n")
                        f.write(f"Tables: {col_data['total_tables']}\n")
                        f.write(f"Samples collected: {col_data['sample_count']}\n")
                        f.write("Sample values:\n")
                        
                        for i, sample in enumerate(col_data['samples'][:10], 1):
                            display = sample[:80] + "..." if len(sample) > 80 else sample
                            f.write(f"  {i}. {display}\n")
                        f.write("\n" + "-"*40 + "\n\n")
                
                logger.info(f"📄 Summary: {summary_file}")
                
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("\n" + "="*60)
    logger.info("✅ DONE")
    logger.info(f"📁 Output directory: {output_dir}")

if __name__ == "__main__":
    # Set up authentication
    auth_file = Path("gcp/gcp_prod_key.json")
    if auth_file.exists():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(auth_file)
        logger.info(f"Using auth file: {auth_file}")
    
    main()