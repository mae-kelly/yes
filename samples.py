#!/usr/bin/env python3
"""
Script to extract sample data for each column from the separated label JSON files
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
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
    print(f"Current path: {sys.path}")
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
        self.successfully_initialized = False
        
    def _initialize_clients(self, project_ids: set) -> bool:
        """Initialize BigQuery clients for unique projects"""
        logger.info(f"Initializing BigQuery clients for {len(project_ids)} projects...")
        
        successful_connections = 0
        for project_id in project_ids:
            if project_id not in self.client_managers:
                try:
                    logger.info(f"Connecting to project: {project_id}")
                    manager = BigQueryClientManager(project_id)
                    
                    # Test the connection
                    if manager.test_connection():
                        self.client_managers[project_id] = manager
                        logger.info(f"✅ Successfully connected to project: {project_id}")
                        successful_connections += 1
                    else:
                        logger.error(f"❌ Failed connection test for project: {project_id}")
                except Exception as e:
                    logger.error(f"❌ Error connecting to project {project_id}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
        
        if successful_connections == 0:
            logger.error("❌ Failed to connect to any BigQuery projects!")
            logger.error("Please check:")
            logger.error("1. Your service account key file exists at gcp/gcp_prod_key.json")
            logger.error("2. The GOOGLE_APPLICATION_CREDENTIALS environment variable is set")
            logger.error("3. You have the necessary permissions for these projects")
            return False
        
        logger.info(f"Successfully connected to {successful_connections}/{len(project_ids)} projects")
        self.successfully_initialized = True
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
        
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        # Process each separated JSON file
        for json_file in sorted(json_files):
            if json_file.name in self.column_types:
                column_type = self.column_types[json_file.name]
                logger.info(f"\n{'='*60}")
                logger.info(f"📁 Processing {json_file.name}")
                logger.info(f"   Column Type: {column_type}")
                logger.info(f"{'='*60}")
                
                success = self._extract_samples_for_type(json_file, column_type)
                if success:
                    logger.info(f"✅ Successfully processed {json_file.name}")
                else:
                    logger.warning(f"⚠️  Issues processing {json_file.name}")
            else:
                logger.debug(f"Skipping unknown file: {json_file.name}")
    
    def _extract_samples_for_type(self, json_file: Path, column_type: str) -> bool:
        """Extract samples for a specific column type"""
        try:
            # Load the JSON file
            logger.info(f"Loading {json_file.name}...")
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Check structure
            if not isinstance(data, dict) or 'columns' not in data:
                logger.warning(f"Unexpected structure in {json_file.name}")
                return False
            
            columns_dict = data['columns']
            if not columns_dict:
                logger.warning(f"No columns found in {json_file.name}")
                return False
            
            logger.info(f"  Found {len(columns_dict)} table-column mappings")
            
            # Collect all unique projects
            projects = set()
            valid_mappings = {}
            
            for table_path, column_name in columns_dict.items():
                if column_name and column_name != 'skip':
                    parts = table_path.split('.')
                    if len(parts) >= 3:
                        project_id = parts[0]
                        projects.add(project_id)
                        valid_mappings[table_path] = column_name
            
            if not projects:
                logger.warning("No valid projects found in mappings")
                return False
            
            logger.info(f"  Projects to connect: {', '.join(sorted(projects))}")
            
            # Initialize clients for these projects
            if not self._initialize_clients(projects):
                logger.error("Failed to initialize BigQuery clients")
                return False
            
            # Group by column name
            columns_by_name = defaultdict(list)
            for table_path, column_name in valid_mappings.items():
                columns_by_name[column_name].append(table_path)
            
            logger.info(f"  Found {len(columns_by_name)} unique column names to process")
            
            # Collect samples for each unique column name
            all_samples = {}
            total_processed = 0
            
            for column_name, table_paths in columns_by_name.items():
                logger.info(f"\n  📊 Processing column: '{column_name}'")
                logger.info(f"     Tables with this column: {len(table_paths)}")
                
                column_samples = self._get_column_samples(column_name, table_paths)
                
                if column_samples and column_samples.get('samples'):
                    all_samples[column_name] = column_samples
                    sample_count = len(column_samples['samples'])
                    logger.info(f"     ✅ Collected {sample_count} samples")
                    total_processed += 1
                else:
                    logger.warning(f"     ⚠️  No samples collected for '{column_name}'")
            
            if all_samples:
                # Save samples to file
                output_file = self.output_dir / f"{column_type}_samples.json"
                self._save_samples(all_samples, output_file, column_type)
                
                # Generate summary report
                self._generate_summary_report(all_samples, column_type)
                
                logger.info(f"\n  Summary: Processed {total_processed}/{len(columns_by_name)} columns")
                return True
            else:
                logger.warning(f"  No samples collected for any columns in {json_file.name}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to process {json_file.name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _get_column_samples(self, column_name: str, table_paths: List[str]) -> Dict[str, Any]:
        """Get samples from multiple tables for a specific column"""
        column_data = {
            'column_name': column_name,
            'tables': [],
            'total_tables': len(table_paths),
            'samples': [],
            'unique_values': set(),
            'null_count': 0,
            'total_rows_checked': 0,
            'value_distribution': defaultdict(int),
            'sample_metadata': [],
            'tables_sampled': 0,
            'tables_failed': 0
        }
        
        samples_needed = self.sample_size
        max_tables_to_check = min(5, len(table_paths))
        
        # Select tables to sample
        if len(table_paths) > max_tables_to_check:
            tables_to_sample = random.sample(table_paths, max_tables_to_check)
        else:
            tables_to_sample = table_paths
        
        logger.debug(f"     Will sample from up to {len(tables_to_sample)} tables")
        
        for table_path in tables_to_sample:
            if len(column_data['samples']) >= samples_needed:
                logger.debug(f"     Reached sample limit ({samples_needed})")
                break
            
            try:
                parts = table_path.split('.')
                if len(parts) != 3:
                    logger.warning(f"     Invalid table path format: {table_path}")
                    column_data['tables_failed'] += 1
                    continue
                
                project_id, dataset_id, table_id = parts
                
                manager = self.client_managers.get(project_id)
                if not manager:
                    logger.debug(f"     No client for project {project_id}")
                    column_data['tables_failed'] += 1
                    continue
                
                # Use the client manager's context manager
                with manager.get_client() as client:
                    # Verify table and column exist
                    try:
                        table = client.get_table(table_path)
                        schema_fields = [field.name for field in table.schema]
                        
                        if column_name not in schema_fields:
                            logger.debug(f"     Column '{column_name}' not in {table_path} schema")
                            column_data['tables_failed'] += 1
                            continue
                            
                    except Exception as e:
                        logger.debug(f"     Cannot access table {table_path}: {e}")
                        column_data['tables_failed'] += 1
                        continue
                    
                    # Query for samples
                    samples_per_table = min(20, samples_needed - len(column_data['samples']))
                    
                    query = f"""
                    SELECT DISTINCT `{column_name}` as value
                    FROM `{project_id}.{dataset_id}.{table_id}`
                    WHERE `{column_name}` IS NOT NULL
                    LIMIT {samples_per_table}
                    """
                    
                    try:
                        logger.debug(f"     Querying {table_path}...")
                        query_job = client.query(query)
                        results = list(query_job.result(timeout=30))
                        
                        samples_from_table = 0
                        for row in results:
                            value = row.value
                            if value is not None:
                                # Convert value to string
                                if isinstance(value, bytes):
                                    value_str = f"<bytes: {len(value)} bytes>"
                                elif isinstance(value, (dict, list)):
                                    value_str = json.dumps(value)[:200]
                                else:
                                    value_str = str(value)[:500]
                                
                                column_data['samples'].append(value_str)
                                column_data['unique_values'].add(value_str)
                                column_data['value_distribution'][value_str] += 1
                                samples_from_table += 1
                        
                        if samples_from_table > 0:
                            column_data['tables'].append(table_path)
                            column_data['tables_sampled'] += 1
                            logger.debug(f"     Got {samples_from_table} samples from {table_path}")
                        
                    except Exception as e:
                        logger.debug(f"     Query failed for {table_path}: {str(e)[:100]}")
                        column_data['tables_failed'] += 1
                        continue
                        
            except Exception as e:
                logger.debug(f"     Error processing {table_path}: {e}")
                column_data['tables_failed'] += 1
                continue
        
        # Convert sets to lists and limit
        column_data['unique_values'] = list(column_data['unique_values'])[:50]
        
        # Sort value distribution
        if column_data['value_distribution']:
            column_data['value_distribution'] = dict(sorted(
                column_data['value_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:20])
        
        logger.debug(f"     Final: {len(column_data['samples'])} samples from {column_data['tables_sampled']} tables")
        
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
        
        for column_name, column_data in samples.items():
            output_data['columns'][column_name] = {
                'column_name': column_data['column_name'],
                'tables_sampled': column_data.get('tables_sampled', 0),
                'tables_failed': column_data.get('tables_failed', 0),
                'total_tables': column_data.get('total_tables', 0),
                'samples': column_data.get('samples', [])[:self.sample_size],
                'sample_count': len(column_data.get('samples', [])),
                'unique_value_count': len(column_data.get('unique_values', [])),
                'top_values': list(column_data.get('value_distribution', {}).items())[:10]
            }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"\n  💾 Saved samples to: {output_file}")
    
    def _generate_summary_report(self, samples: Dict[str, Any], column_type: str):
        """Generate a human-readable summary report"""
        report_file = self.output_dir / f"{column_type}_summary.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"COLUMN TYPE: {column_type.upper()}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total unique column names: {len(samples)}\n\n")
            
            for column_name, column_data in samples.items():
                f.write(f"\nColumn: '{column_name}'\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total tables: {column_data.get('total_tables', 0)}\n")
                f.write(f"Tables sampled: {column_data.get('tables_sampled', 0)}\n")
                f.write(f"Samples collected: {len(column_data.get('samples', []))}\n")
                
                if column_data.get('samples'):
                    f.write("\nSample values (first 10):\n")
                    for i, sample in enumerate(column_data['samples'][:10], 1):
                        display_sample = sample[:80] + "..." if len(sample) > 80 else sample
                        f.write(f"  {i:2}. {display_sample}\n")
                
                f.write("\n")
        
        logger.info(f"  📋 Generated summary: {report_file}")

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
    
    # Check if GCP authentication is set up
    logger.info("Checking GCP authentication...")
    
    # Check for authentication file
    auth_locations = [
        Path("gcp/gcp_prod_key.json"),
        Path("gcp_prod_key.json"),
        Path(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''))
    ]
    
    auth_found = False
    for auth_file in auth_locations:
        if auth_file and auth_file.exists():
            logger.info(f"✅ Found authentication file: {auth_file}")
            if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(auth_file)
                logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to {auth_file}")
            auth_found = True
            break
    
    if not auth_found:
        logger.warning("⚠️  No authentication file found. Will try default credentials.")
    
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
            'country': 'four_countries.json',
            'data_center': 'five_data_centers.json',
            'cloud_region': 'six_cloud_regions.json',
            'business_unit': 'seven_business_units.json',
            'cio': 'eight_cios.json',
            'apm': 'nine_apms.json',
            'app_class': 'ten_app_classes.json',
            'system_classification': 'eleven_system_classifications.json',
            'edr_coverage': 'twelve_edr_coverages.json',
            'tanium_coverage': 'thirteen_tanium_coverages.json',
            'dlp_agent_coverage': 'fourteen_dlp_coverages.json',
            'logging_in_splunk': 'fifteen_splunk_loggings.json',
            'logging_in_gso': 'sixteen_gso_loggings.json',
            'domain': 'seventeen_domains.json'
        }
        
        if args.specific_type in type_to_file:
            json_file = Path(args.input_dir) / type_to_file[args.specific_type]
            if json_file.exists():
                logger.info(f"Processing single type: {args.specific_type}")
                extractor._extract_samples_for_type(json_file, args.specific_type)
            else:
                logger.error(f"File not found: {json_file}")
        else:
            logger.error(f"Unknown column type: {args.specific_type}")
    else:
        # Process all types
        extractor.extract_all_samples()
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ SAMPLE EXTRACTION COMPLETE")
    logger.info(f"📁 Output directory: {args.output_dir}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()