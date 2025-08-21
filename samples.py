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

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gcp.client import BigQueryClientManager

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
        self.project_ids = set()
        
    def _initialize_clients(self, project_ids: set):
        """Initialize BigQuery clients for unique projects"""
        for project_id in project_ids:
            if project_id not in self.client_managers:
                try:
                    manager = BigQueryClientManager(project_id)
                    if manager.test_connection():
                        self.client_managers[project_id] = manager
                        logger.info(f"✅ Connected to project: {project_id}")
                    else:
                        logger.error(f"❌ Failed to connect to project: {project_id}")
                except Exception as e:
                    logger.error(f"❌ Connection error for {project_id}: {e}")
    
    def extract_all_samples(self):
        """Extract samples for all separated JSON files"""
        logger.info("=" * 80)
        logger.info("COLUMN SAMPLE EXTRACTION")
        logger.info("=" * 80)
        
        # Process each separated JSON file
        for json_file in sorted(self.separated_dir.glob("*.json")):
            if json_file.name in self.column_types:
                column_type = self.column_types[json_file.name]
                logger.info(f"\n📁 Processing {json_file.name} ({column_type})")
                self._extract_samples_for_type(json_file, column_type)
            else:
                logger.warning(f"⚠️  Unknown file: {json_file.name}")
    
    def _extract_samples_for_type(self, json_file: Path, column_type: str):
        """Extract samples for a specific column type"""
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # The structure is: {"columns": {"table_path": "column_name", ...}}
            if not isinstance(data, dict) or 'columns' not in data:
                logger.warning(f"Unexpected structure in {json_file.name}")
                return
            
            columns_dict = data['columns']
            logger.info(f"  Found {len(columns_dict)} table-column mappings")
            
            # Collect all unique projects
            projects = set()
            for table_path in columns_dict.keys():
                project_id = table_path.split('.')[0]
                projects.add(project_id)
            
            logger.info(f"  Projects involved: {', '.join(projects)}")
            
            # Initialize clients for these projects
            self._initialize_clients(projects)
            
            # Group by column name (value in the dict)
            columns_by_name = defaultdict(list)
            for table_path, column_name in columns_dict.items():
                if column_name and column_name != 'skip':  # Ignore 'skip' entries
                    columns_by_name[column_name].append(table_path)
            
            logger.info(f"  Found {len(columns_by_name)} unique column names")
            
            # Collect samples for each unique column name
            all_samples = {}
            
            for column_name, table_paths in columns_by_name.items():
                logger.info(f"  📊 Extracting samples for column: '{column_name}'")
                logger.info(f"     Found in {len(table_paths)} tables")
                
                column_samples = self._get_column_samples(column_name, table_paths)
                
                if column_samples and column_samples['samples']:
                    all_samples[column_name] = column_samples
                    logger.info(f"     ✅ Collected {len(column_samples['samples'])} samples")
                else:
                    logger.warning(f"     ⚠️  No samples collected for '{column_name}'")
            
            if all_samples:
                # Save samples to file
                output_file = self.output_dir / f"{column_type}_samples.json"
                self._save_samples(all_samples, output_file, column_type)
                
                # Generate summary report
                self._generate_summary_report(all_samples, column_type)
            else:
                logger.warning(f"  ⚠️  No samples collected for any columns in {json_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {json_file.name}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def _get_column_samples(self, column_name: str, table_paths: List[str]) -> Dict[str, Any]:
        """Get samples from multiple tables for a specific column"""
        column_data = {
            'column_name': column_name,
            'tables': table_paths[:10],  # List first 10 tables
            'total_tables': len(table_paths),
            'samples': [],
            'unique_values': set(),
            'null_count': 0,
            'total_rows_checked': 0,
            'value_distribution': defaultdict(int),
            'sample_metadata': []
        }
        
        samples_needed = self.sample_size
        max_tables_to_check = min(5, len(table_paths))  # Check at most 5 tables
        
        # Randomly select tables to sample from if there are many
        if len(table_paths) > max_tables_to_check:
            tables_to_sample = random.sample(table_paths, max_tables_to_check)
        else:
            tables_to_sample = table_paths
        
        for table_path in tables_to_sample:
            if len(column_data['samples']) >= samples_needed:
                break
            
            try:
                parts = table_path.split('.')
                if len(parts) != 3:
                    logger.warning(f"       Invalid table path format: {table_path}")
                    continue
                    
                project_id = parts[0]
                dataset_id = parts[1]
                table_id = parts[2]
                
                manager = self.client_managers.get(project_id)
                
                if not manager:
                    logger.debug(f"       No client manager for project {project_id}")
                    continue
                
                with manager.get_client() as client:
                    # First check if table exists and has the column
                    try:
                        table = client.get_table(table_path)
                        schema_fields = [field.name for field in table.schema]
                        
                        if column_name not in schema_fields:
                            logger.debug(f"       Column '{column_name}' not found in {table_path}")
                            continue
                    except Exception as e:
                        logger.debug(f"       Cannot access table {table_path}: {e}")
                        continue
                    
                    # Get samples from this table
                    samples_per_table = min(20, samples_needed - len(column_data['samples']))
                    
                    # Build query with proper escaping
                    query = f"""
                    SELECT DISTINCT `{column_name}` as value
                    FROM `{project_id}.{dataset_id}.{table_id}`
                    WHERE `{column_name}` IS NOT NULL
                    LIMIT {samples_per_table * 2}
                    """
                    
                    try:
                        query_job = client.query(query)
                        results = list(query_job.result(timeout=30))
                        
                        samples_collected = 0
                        for row in results:
                            if samples_collected >= samples_per_table:
                                break
                                
                            value = row.value
                            
                            if value is not None:
                                # Handle different data types
                                if isinstance(value, bytes):
                                    value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                                elif isinstance(value, (dict, list)):
                                    value_str = json.dumps(value)[:500]
                                else:
                                    value_str = str(value)[:500]  # Limit length
                                
                                column_data['samples'].append(value_str)
                                column_data['unique_values'].add(value_str)
                                column_data['value_distribution'][value_str] += 1
                                samples_collected += 1
                                
                                # Add metadata about this sample
                                column_data['sample_metadata'].append({
                                    'value': value_str[:100],  # Truncate for metadata
                                    'source_table': table_path,
                                    'data_type': type(value).__name__
                                })
                        
                        if samples_collected > 0:
                            logger.debug(f"       Collected {samples_collected} samples from {table_path}")
                        
                        # Get statistics for this column in this table
                        stats_query = f"""
                        SELECT 
                            COUNT(*) as total_rows,
                            COUNT(`{column_name}`) as non_null_count,
                            COUNT(*) - COUNT(`{column_name}`) as null_count
                        FROM `{project_id}.{dataset_id}.{table_id}`
                        """
                        
                        try:
                            stats_job = client.query(stats_query)
                            stats_result = list(stats_job.result(timeout=30))
                            if stats_result:
                                column_data['total_rows_checked'] += stats_result[0].total_rows
                                column_data['null_count'] += stats_result[0].null_count
                        except:
                            pass  # Statistics are optional
                        
                    except Exception as e:
                        logger.debug(f"       Query failed for {table_path}: {str(e)[:200]}")
                        continue
                    
            except Exception as e:
                logger.debug(f"Failed to process table {table_path}: {e}")
                continue
        
        # Convert sets to lists for JSON serialization
        column_data['unique_values'] = list(column_data['unique_values'])[:100]  # Limit unique values
        
        # Sort and limit value distribution
        if column_data['value_distribution']:
            column_data['value_distribution'] = dict(sorted(
                column_data['value_distribution'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:20])  # Top 20 most common values
        
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
        
        # Process each column's data
        for column_name, column_data in samples.items():
            output_data['columns'][column_name] = {
                'column_name': column_data['column_name'],
                'tables_found_in': column_data.get('tables', [])[:20],  # Limit to 20 tables in output
                'total_tables': column_data.get('total_tables', len(column_data.get('tables', []))),
                'samples': column_data['samples'][:self.sample_size],
                'sample_count': len(column_data['samples']),
                'unique_value_count': len(column_data.get('unique_values', [])),
                'unique_values_sample': column_data.get('unique_values', [])[:20],
                'null_count': column_data.get('null_count', 0),
                'total_rows_checked': column_data.get('total_rows_checked', 0),
                'null_percentage': (column_data.get('null_count', 0) / column_data.get('total_rows_checked', 1) * 100) 
                                  if column_data.get('total_rows_checked', 0) > 0 else 0,
                'top_values': list(column_data.get('value_distribution', {}).items())[:10],
                'sample_metadata': column_data.get('sample_metadata', [])[:10]
            }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"  💾 Saved samples to {output_file}")
    
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
                f.write(f"Found in {column_data.get('total_tables', 0)} tables\n")
                f.write(f"Samples collected: {len(column_data.get('samples', []))}\n")
                f.write(f"Unique values: {len(column_data.get('unique_values', []))}\n")
                
                if column_data.get('total_rows_checked', 0) > 0:
                    null_pct = (column_data.get('null_count', 0) / column_data['total_rows_checked'] * 100)
                    f.write(f"Null percentage: {null_pct:.1f}%\n")
                
                if column_data.get('samples'):
                    f.write("\nSample values (first 10):\n")
                    for i, sample in enumerate(column_data['samples'][:10], 1):
                        # Truncate long samples for readability
                        display_sample = sample[:100] + "..." if len(sample) > 100 else sample
                        f.write(f"  {i:2}. {display_sample}\n")
                
                if column_data.get('value_distribution'):
                    f.write("\nMost common values:\n")
                    for value, count in list(column_data['value_distribution'].items())[:5]:
                        display_value = value[:50] + "..." if len(value) > 50 else value
                        f.write(f"  '{display_value}': {count} occurrences\n")
                
                f.write("\n")
        
        logger.info(f"  📋 Generated summary report: {report_file}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract sample data for labeled columns')
    parser.add_argument('--input-dir', default='separated_labels', help='Directory with separated JSON files')
    parser.add_argument('--output-dir', default='column_samples', help='Output directory for samples')
    parser.add_argument('--sample-size', type=int, default=50, help='Number of samples per column')
    parser.add_argument('--specific-type', help='Process only a specific column type (e.g., "host")')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    extractor = ColumnSampleExtractor(
        separated_dir=args.input_dir,
        output_dir=args.output_dir,
        sample_size=args.sample_size
    )
    
    if args.specific_type:
        # Map type to filename
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
                extractor._extract_samples_for_type(json_file, args.specific_type)
            else:
                logger.error(f"File not found: {json_file}")
        else:
            logger.error(f"Unknown column type: {args.specific_type}")
    else:
        extractor.extract_all_samples()
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ SAMPLE EXTRACTION COMPLETE")
    logger.info(f"📁 Output directory: {args.output_dir}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()