#!/usr/bin/env python3
"""
Script to extract sample data for each column from the separated label JSON files
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional
import random

# Add the project root to path to import gcp module
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import the GCP client
try:
    from gcp.client import BigQueryClientManager
    print("✅ Successfully imported BigQueryClientManager")
except ImportError as e:
    print(f"❌ Failed to import BigQueryClientManager: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ColumnSampleExtractor:
    def __init__(self, separated_dir='separated_labels', output_dir='column_samples', sample_size=50):
        self.separated_dir = Path(separated_dir)
        self.output_dir = Path(output_dir)
        self.sample_size = sample_size
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Column type mapping for reference
        self.column_types = {
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
        
        # Initialize BigQuery clients
        self.client_managers = {}
        
    def _initialize_clients(self, project_ids: set) -> bool:
        """Initialize BigQuery clients for unique projects"""
        logger.info(f"Initializing BigQuery clients for {len(project_ids)} projects...")
        
        successful_connections = 0
        for project_id in project_ids:
            if project_id not in self.client_managers:
                try:
                    logger.info(f"Connecting to project: {project_id}")
                    manager = BigQueryClientManager(project_id)
                    
                    if manager.test_connection():
                        self.client_managers[project_id] = manager
                        logger.info(f"✅ Successfully connected to project: {project_id}")
                        successful_connections += 1
                    else:
                        logger.error(f"❌ Failed connection test for project: {project_id}")
                except Exception as e:
                    logger.error(f"❌ Error connecting to project {project_id}: {e}")
        
        if successful_connections == 0:
            logger.error("❌ Failed to connect to any BigQuery projects!")
            return False
        
        logger.info(f"Successfully connected to {successful_connections}/{len(project_ids)} projects")
        return True
    
    def extract_all_samples(self):
        """Extract samples for all separated JSON files"""
        logger.info("=" * 80)
        logger.info("COLUMN SAMPLE EXTRACTION")
        logger.info("=" * 80)
        
        json_files = list(self.separated_dir.glob("*.json"))
        if not json_files:
            logger.error(f"No JSON files found in {self.separated_dir}")
            return
        
        # Process each separated JSON file
        for json_file in sorted(json_files):
            if json_file.name in self.column_types:
                column_type = self.column_types[json_file.name]
                logger.info(f"\n{'='*60}")
                logger.info(f"📁 Processing {json_file.name}")
                logger.info(f"   Column Type: {column_type}")
                
                try:
                    self._extract_samples_for_type(json_file, column_type)
                    logger.info(f"✅ Successfully processed {json_file.name}")
                except Exception as e:
                    logger.error(f"❌ Failed to process {json_file.name}: {e}")
                    import traceback
                    logger.error(f"Full traceback:\n{traceback.format_exc()}")
    
    def _extract_samples_for_type(self, json_file: Path, column_type: str):
        """Extract samples for a specific column type"""
        # Load the JSON file
        logger.info(f"Loading {json_file.name}...")
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Debug: Show what type of data we have
        logger.debug(f"Data type: {type(data)}")
        if isinstance(data, dict):
            logger.debug(f"Data keys: {list(data.keys())[:5]}")  # Show first 5 keys
        
        # Check structure
        if not isinstance(data, dict):
            logger.error(f"Expected dict but got {type(data)} in {json_file.name}")
            return
            
        if 'columns' not in data:
            logger.warning(f"No 'columns' key in {json_file.name}. Keys found: {list(data.keys())}")
            return
        
        columns_dict = data['columns']
        
        # Debug: Check columns_dict type
        logger.debug(f"columns_dict type: {type(columns_dict)}")
        
        if not isinstance(columns_dict, dict):
            logger.error(f"'columns' is not a dict, it's a {type(columns_dict)}")
            return
            
        if not columns_dict:
            logger.warning(f"No columns found in {json_file.name}")
            return
        
        logger.info(f"  Found {len(columns_dict)} table-column mappings")
        
        # Collect all unique projects and valid mappings
        projects = set()
        valid_mappings = {}
        
        # Safely iterate over columns_dict
        try:
            for table_path, column_name in columns_dict.items():
                if column_name and column_name != 'skip':
                    parts = table_path.split('.')
                    if len(parts) >= 3:
                        project_id = parts[0]
                        projects.add(project_id)
                        valid_mappings[table_path] = column_name
        except AttributeError as e:
            logger.error(f"Error iterating over columns_dict: {e}")
            logger.error(f"columns_dict is: {columns_dict}")
            return
        
        if not projects:
            logger.warning("No valid projects found")
            return
        
        logger.info(f"  Projects: {', '.join(sorted(projects))}")
        
        # Initialize clients
        if not self._initialize_clients(projects):
            logger.error("Failed to initialize BigQuery clients")
            return
        
        # Group by column name
        columns_by_name = defaultdict(list)
        for table_path, column_name in valid_mappings.items():
            columns_by_name[column_name].append(table_path)
        
        logger.info(f"  Found {len(columns_by_name)} unique column names")
        
        # Collect samples
        all_samples = {}
        
        for column_name, table_paths in columns_by_name.items():
            logger.info(f"\n  📊 Column: '{column_name}'")
            logger.info(f"     Tables: {len(table_paths)}")
            
            column_samples = self._get_column_samples(column_name, table_paths)
            
            if column_samples and column_samples.get('samples'):
                all_samples[column_name] = column_samples
                logger.info(f"     ✅ Got {len(column_samples['samples'])} samples")
            else:
                logger.warning(f"     ⚠️  No samples for '{column_name}'")
        
        if all_samples:
            # Save samples
            output_file = self.output_dir / f"{column_type}_samples.json"
            self._save_samples(all_samples, output_file, column_type)
            
            # Generate report
            self._generate_summary_report(all_samples, column_type)
    
    def _get_column_samples(self, column_name: str, table_paths: List[str]) -> Dict[str, Any]:
        """Get samples from multiple tables for a specific column"""
        column_data = {
            'column_name': column_name,
            'tables': [],
            'total_tables': len(table_paths),
            'samples': [],
            'unique_values': [],  # Use list instead of set
            'value_counts': {}    # Use dict instead of Counter
        }
        
        samples_needed = self.sample_size
        max_tables = min(5, len(table_paths))
        
        # Select tables to sample
        tables_to_sample = random.sample(table_paths, min(max_tables, len(table_paths)))
        
        for table_path in tables_to_sample:
            if len(column_data['samples']) >= samples_needed:
                break
            
            try:
                parts = table_path.split('.')
                if len(parts) != 3:
                    continue
                
                project_id, dataset_id, table_id = parts
                
                manager = self.client_managers.get(project_id)
                if not manager:
                    continue
                
                with manager.get_client() as client:
                    # Check if column exists
                    try:
                        table = client.get_table(table_path)
                        schema_fields = [field.name for field in table.schema]
                        
                        if column_name not in schema_fields:
                            logger.debug(f"Column '{column_name}' not in {table_path}")
                            continue
                    except Exception as e:
                        logger.debug(f"Cannot access table {table_path}: {e}")
                        continue
                    
                    # Query for samples
                    query = f"""
                    SELECT DISTINCT `{column_name}` as value
                    FROM `{project_id}.{dataset_id}.{table_id}`
                    WHERE `{column_name}` IS NOT NULL
                    LIMIT {min(20, samples_needed - len(column_data['samples']))}
                    """
                    
                    try:
                        query_job = client.query(query)
                        results = list(query_job.result(timeout=30))
                        
                        for row in results:
                            value = row.value
                            if value is not None:
                                # Convert to string
                                if isinstance(value, bytes):
                                    value_str = f"<bytes: {len(value)}>"
                                elif isinstance(value, (dict, list)):
                                    value_str = json.dumps(value)[:200]
                                else:
                                    value_str = str(value)[:500]
                                
                                column_data['samples'].append(value_str)
                                
                                # Track unique values
                                if value_str not in column_data['unique_values']:
                                    column_data['unique_values'].append(value_str)
                                
                                # Count occurrences
                                if value_str in column_data['value_counts']:
                                    column_data['value_counts'][value_str] += 1
                                else:
                                    column_data['value_counts'][value_str] = 1
                        
                        if results:
                            column_data['tables'].append(table_path)
                            
                    except Exception as e:
                        logger.debug(f"Query failed: {str(e)[:100]}")
                        
            except Exception as e:
                logger.debug(f"Error: {e}")
        
        # Limit unique values
        column_data['unique_values'] = column_data['unique_values'][:50]
        
        # Get top values as a list of tuples
        if column_data['value_counts']:
            sorted_values = sorted(column_data['value_counts'].items(), key=lambda x: x[1], reverse=True)
            column_data['top_values'] = sorted_values[:10]
        else:
            column_data['top_values'] = []
        
        # Remove value_counts as we've extracted what we need
        del column_data['value_counts']
        
        return column_data
    
    def _save_samples(self, samples: Dict[str, Any], output_file: Path, column_type: str):
        """Save samples to JSON file"""
        output_data = {
            'metadata': {
                'column_type': column_type,
                'extraction_timestamp': datetime.now().isoformat(),
                'sample_size_requested': self.sample_size,
                'total_unique_columns': len(samples)
            },
            'columns': {}
        }
        
        # Safely iterate over samples
        if isinstance(samples, dict):
            for column_name, column_data in samples.items():
                # Make sure column_data is a dict
                if not isinstance(column_data, dict):
                    logger.warning(f"Skipping non-dict column data for {column_name}: {type(column_data)}")
                    continue
                    
                output_data['columns'][column_name] = {
                    'column_name': column_data.get('column_name', column_name),
                    'tables_sampled': len(column_data.get('tables', [])),
                    'total_tables': column_data.get('total_tables', 0),
                    'samples': column_data.get('samples', [])[:self.sample_size],
                    'sample_count': len(column_data.get('samples', [])),
                    'unique_value_count': len(column_data.get('unique_values', [])),
                    'top_values': column_data.get('top_values', [])
                }
        else:
            logger.error(f"samples is not a dict: {type(samples)}")
            return
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"  💾 Saved to: {output_file}")
    
    def _generate_summary_report(self, samples: Dict[str, Any], column_type: str):
        """Generate summary report"""
        report_file = self.output_dir / f"{column_type}_summary.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"COLUMN TYPE: {column_type.upper()}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Safely check if samples is a dict
            if isinstance(samples, dict):
                f.write(f"Total unique columns: {len(samples)}\n\n")
                
                for column_name, column_data in samples.items():
                    if not isinstance(column_data, dict):
                        continue
                        
                    f.write(f"\nColumn: '{column_name}'\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Tables: {column_data.get('total_tables', 0)}\n")
                    f.write(f"Samples: {len(column_data.get('samples', []))}\n")
                    
                    samples_list = column_data.get('samples', [])
                    if samples_list:
                        f.write("\nSample values (first 10):\n")
                        for i, sample in enumerate(samples_list[:10], 1):
                            display = sample[:80] + "..." if len(sample) > 80 else sample
                            f.write(f"  {i:2}. {display}\n")
                    
                    top_values = column_data.get('top_values', [])
                    if top_values:
                        f.write("\nMost common:\n")
                        for item in top_values[:5]:
                            if isinstance(item, (list, tuple)) and len(item) == 2:
                                value, count = item
                                display = value[:50] + "..." if len(value) > 50 else value
                                f.write(f"  '{display}': {count}x\n")
                    
                    f.write("\n")
            else:
                f.write(f"Error: samples is not a dict (type: {type(samples)})\n")
        
        logger.info(f"  📋 Report: {report_file}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract sample data for labeled columns')
    parser.add_argument('--input-dir', default='separated_labels', help='Directory with separated JSON files')
    parser.add_argument('--output-dir', default='column_samples', help='Output directory for samples')
    parser.add_argument('--sample-size', type=int, default=50, help='Number of samples per column')
    parser.add_argument('--specific-type', help='Process only a specific column type')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check authentication
    logger.info("Checking GCP authentication...")
    
    auth_locations = [
        Path("gcp/gcp_prod_key.json"),
        Path("gcp_prod_key.json"),
    ]
    
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        auth_locations.insert(0, Path(os.environ['GOOGLE_APPLICATION_CREDENTIALS']))
    
    auth_found = False
    for auth_file in auth_locations:
        if auth_file and auth_file.exists():
            logger.info(f"✅ Found auth file: {auth_file}")
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(auth_file)
            auth_found = True
            break
    
    if not auth_found:
        logger.warning("⚠️  No auth file found, trying default credentials")
    
    # Create extractor
    extractor = ColumnSampleExtractor(
        separated_dir=args.input_dir,
        output_dir=args.output_dir,
        sample_size=args.sample_size
    )
    
    if args.specific_type:
        # Process specific type
        type_to_file = {
            'host': 'one_hosts.json',
            'infrastructure_type': 'two_infrastructure_types.json',
            'region': 'three_regions.json',
            # ... rest of mappings
        }
        
        if args.specific_type in type_to_file:
            json_file = Path(args.input_dir) / type_to_file[args.specific_type]
            if json_file.exists():
                logger.info(f"Processing: {args.specific_type}")
                extractor._extract_samples_for_type(json_file, args.specific_type)
            else:
                logger.error(f"File not found: {json_file}")
        else:
            logger.error(f"Unknown type: {args.specific_type}")
    else:
        extractor.extract_all_samples()
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ COMPLETE")
    logger.info(f"📁 Output: {args.output_dir}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()