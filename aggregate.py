#!/usr/bin/env python3
"""
Ultimate CMDB Builder App
Creates a comprehensive CMDB by aggregating and normalizing host data 
from all tables listed in reviewed_labeled_columns.json

Key Features:
- Normalizes hostnames (removes domains, dashes, converts to lowercase)
- Aggregates data for each unique host from multiple tables
- Creates standardized CMDB with predefined columns
- Tracks which tables each host appears in
"""

import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set, Optional
import pandas as pd

# Add the project path to find gcp.client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateCMDBBuilder:
    def __init__(self, labels_file: str = 'reviewed_labeled_columns.json'):
        self.labels_file = Path(labels_file)
        self.output_file = Path('ultimate_cmdb.json')
        self.csv_output = Path('ultimate_cmdb.csv')
        
        # Load column mappings
        self.column_mappings = self._load_column_mappings()
        
        # Initialize BigQuery clients
        self.client_managers = {}
        self._initialize_bigquery_clients()
        
        # Define the standard CMDB columns
        self.cmdb_columns = [
            'host',
            'apm', 
            'app_class',
            'business_unit',
            'cio',
            'cloud_region', 
            'country',
            'data_center',
            'domain',
            'edr_coverage',
            'infrastructure_type',
            'region',
            'system_classification',
            'tanium_coverage',
            'featured_in_these_tables'
        ]
        
        # Map column types from labels to CMDB columns
        self.column_type_mapping = {
            'host': 'host',
            'apm': 'apm',
            'app_class': 'app_class', 
            'business_unit': 'business_unit',
            'cio': 'cio',
            'cloud_region': 'cloud_region',
            'country': 'country',
            'data_center': 'data_center',
            'domain': 'domain',
            'edr_coverage': 'edr_coverage',
            'infrastructure_type': 'infrastructure_type',
            'region': 'region',
            'system_classification': 'system_classification',
            'tanium_coverage': 'tanium_coverage'
        }
        
        # Storage for CMDB data
        self.cmdb_data = {}  # normalized_host -> {column: [values], tables: [table_names]}
        
    def _load_column_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load the reviewed labeled columns"""
        if not self.labels_file.exists():
            logger.error(f"Labels file {self.labels_file} not found!")
            return {}
        
        try:
            with open(self.labels_file, 'r') as f:
                data = json.load(f)
                columns = data.get('columns', {})
                logger.info(f"Loaded column mappings from {self.labels_file}")
                logger.info(f"Found {len(columns)} tables with labeled columns")
                return columns
        except Exception as e:
            logger.error(f"Failed to load {self.labels_file}: {e}")
            return {}
    
    def _initialize_bigquery_clients(self):
        """Initialize BigQuery clients for all projects"""
        try:
            from gcp.client import BigQueryClientManager
        except ImportError:
            logger.error("BigQuery client not available. Cannot proceed.")
            sys.exit(1)
        
        # Extract project IDs from the column mappings
        project_ids = set()
        for table_path in self.column_mappings.keys():
            parts = table_path.split('.')
            if len(parts) >= 1:
                project_ids.add(parts[0])
        
        logger.info(f"Initializing BigQuery clients for {len(project_ids)} projects...")
        
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
        
        if not self.client_managers:
            logger.error("No BigQuery connections available. Cannot proceed.")
            sys.exit(1)
        
        logger.info(f"Successfully connected to {len(self.client_managers)} projects")
    
    def normalize_hostname(self, hostname: str) -> str:
        """
        Normalize hostname by:
        1. Converting to lowercase
        2. Removing everything after first dot (domain)
        3. Removing all dashes
        """
        if not hostname or pd.isna(hostname):
            return ""
        
        hostname = str(hostname).strip().lower()
        
        # Remove domain (everything after first dot)
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        # Remove all dashes
        hostname = hostname.replace('-', '')
        
        return hostname
    
    def build_cmdb(self):
        """Main method to build the ultimate CMDB"""
        if not self.column_mappings:
            logger.error("No column mappings available!")
            return
        
        logger.info("🚀 Starting Ultimate CMDB build process...")
        
        # Process each table
        total_tables = len(self.column_mappings)
        for i, (table_path, table_columns) in enumerate(self.column_mappings.items(), 1):
            logger.info(f"Processing table {i}/{total_tables}: {table_path}")
            self._process_table(table_path, table_columns)
        
        # Generate final CMDB
        final_cmdb = self._generate_final_cmdb()
        
        # Save results
        self._save_results(final_cmdb)
        
        # Show statistics
        self._show_statistics(final_cmdb)
    
    def _process_table(self, table_path: str, table_columns: Dict[str, str]):
        """Process a single table and extract relevant data"""
        # Find host columns and other relevant columns
        host_columns = [col for col, col_type in table_columns.items() if col_type == 'host']
        other_columns = {col: col_type for col, col_type in table_columns.items() 
                        if col_type in self.column_type_mapping and col_type != 'host'}
        
        if not host_columns:
            logger.debug(f"No host columns found in {table_path}, skipping")
            return
        
        # Get project ID for BigQuery client
        parts = table_path.split('.')
        if len(parts) < 3:
            logger.warning(f"Invalid table path format: {table_path}")
            return
        
        project_id = parts[0]
        client_manager = self.client_managers.get(project_id)
        
        if not client_manager:
            logger.warning(f"No BigQuery client for project {project_id}")
            return
        
        try:
            # Build query to get data
            query = self._build_table_query(table_path, host_columns, other_columns)
            
            # Execute query
            with client_manager.get_client() as client:
                logger.debug(f"Executing query for {table_path}")
                query_job = client.query(query)
                results = query_job.result(timeout=300)  # 5 minute timeout
                
                # Process results
                row_count = 0
                for row in results:
                    self._process_row(row, table_path, host_columns, other_columns)
                    row_count += 1
                
                logger.info(f"  Processed {row_count:,} rows from {table_path}")
                
        except Exception as e:
            logger.error(f"Failed to process {table_path}: {e}")
    
    def _build_table_query(self, table_path: str, host_columns: List[str], 
                          other_columns: Dict[str, str]) -> str:
        """Build SQL query to extract data from a table"""
        # Select all host columns and other relevant columns
        select_columns = []
        
        # Add host columns
        for col in host_columns:
            select_columns.append(f"`{col}` as host_{col}")
        
        # Add other columns  
        for col, col_type in other_columns.items():
            select_columns.append(f"`{col}` as {col_type}_{col}")
        
        # Build WHERE clause to filter out nulls and empty values
        where_conditions = []
        for col in host_columns:
            where_conditions.append(f"(`{col}` IS NOT NULL AND `{col}` != '' AND `{col}` != 'null')")
        
        where_clause = " OR ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT {', '.join(select_columns)}
        FROM `{table_path}`
        WHERE {where_clause}
        """
        
        return query
    
    def _process_row(self, row, table_path: str, host_columns: List[str], 
                    other_columns: Dict[str, str]):
        """Process a single row from BigQuery results"""
        # Extract and normalize hostnames
        hostnames = []
        for col in host_columns:
            hostname_value = getattr(row, f'host_{col}', None)
            if hostname_value:
                normalized = self.normalize_hostname(hostname_value)
                if normalized:
                    hostnames.append(normalized)
        
        # Process each unique normalized hostname
        for normalized_host in set(hostnames):
            if not normalized_host:
                continue
                
            # Initialize host entry if not exists
            if normalized_host not in self.cmdb_data:
                self.cmdb_data[normalized_host] = {
                    'tables': set(),
                    'data': defaultdict(set)
                }
            
            # Add table to host's table list
            self.cmdb_data[normalized_host]['tables'].add(table_path)
            
            # Add other column data
            for col, col_type in other_columns.items():
                value = getattr(row, f'{col_type}_{col}', None)
                if value and str(value).strip() and str(value).lower() not in ['null', 'none', '']:
                    cmdb_column = self.column_type_mapping.get(col_type)
                    if cmdb_column:
                        self.cmdb_data[normalized_host]['data'][cmdb_column].add(str(value).strip())
    
    def _generate_final_cmdb(self) -> List[Dict[str, Any]]:
        """Generate the final CMDB with standardized columns"""
        logger.info(f"Generating final CMDB for {len(self.cmdb_data):,} unique hosts...")
        
        final_cmdb = []
        
        for normalized_host, host_data in self.cmdb_data.items():
            # Create record for this host
            record = {'host': normalized_host}
            
            # Add all CMDB columns
            for column in self.cmdb_columns[1:-1]:  # Skip 'host' and 'featured_in_these_tables'
                values = list(host_data['data'].get(column, set()))
                
                if not values:
                    record[column] = None
                elif len(values) == 1:
                    record[column] = values[0]
                else:
                    # Multiple values - join with pipe separator
                    record[column] = ' | '.join(sorted(values))
            
            # Add featured tables
            record['featured_in_these_tables'] = ' | '.join(sorted(host_data['tables']))
            
            final_cmdb.append(record)
        
        # Sort by hostname
        final_cmdb.sort(key=lambda x: x['host'])
        
        return final_cmdb
    
    def _save_results(self, final_cmdb: List[Dict[str, Any]]):
        """Save the CMDB results to JSON and CSV"""
        # Prepare metadata
        metadata = {
            'creation_timestamp': datetime.now().isoformat(),
            'source_file': str(self.labels_file),
            'total_unique_hosts': len(final_cmdb),
            'total_tables_processed': len(self.column_mappings),
            'cmdb_columns': self.cmdb_columns,
            'normalization_rules': [
                'Convert to lowercase',
                'Remove domain (everything after first dot)',
                'Remove all dashes'
            ]
        }
        
        # Save JSON
        output_data = {
            'metadata': metadata,
            'cmdb_data': final_cmdb
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"💾 Saved JSON results to {self.output_file}")
        
        # Save CSV
        if final_cmdb:
            df = pd.DataFrame(final_cmdb)
            df.to_csv(self.csv_output, index=False)
            logger.info(f"💾 Saved CSV results to {self.csv_output}")
        
    def _show_statistics(self, final_cmdb: List[Dict[str, Any]]):
        """Show statistics about the generated CMDB"""
        print("\n" + "="*60)
        print("ULTIMATE CMDB GENERATION COMPLETE")
        print("="*60)
        
        print(f"📊 Summary:")
        print(f"  Total unique hosts: {len(final_cmdb):,}")
        print(f"  Tables processed: {len(self.column_mappings):,}")
        print(f"  BigQuery projects: {len(self.client_managers)}")
        
        # Column population statistics
        if final_cmdb:
            print(f"\n📈 Column Population:")
            for column in self.cmdb_columns:
                populated = sum(1 for record in final_cmdb if record.get(column))
                percentage = (populated / len(final_cmdb)) * 100
                print(f"  {column:25} {populated:6,} ({percentage:5.1f}%)")
        
        # Table distribution
        table_counts = Counter()
        for record in final_cmdb:
            tables = record.get('featured_in_these_tables', '')
            if tables:
                table_list = [t.strip() for t in tables.split('|')]
                table_counts.update(table_list)
        
        print(f"\n🏆 Top Tables by Host Count:")
        for table, count in table_counts.most_common(10):
            print(f"  {table:50} {count:6,} hosts")
        
        # Multi-table hosts
        multi_table_hosts = sum(1 for record in final_cmdb 
                               if '|' in record.get('featured_in_these_tables', ''))
        
        print(f"\n🔗 Host Distribution:")
        print(f"  Hosts in multiple tables: {multi_table_hosts:,}")
        print(f"  Hosts in single table: {len(final_cmdb) - multi_table_hosts:,}")
        
        print(f"\n📁 Output Files:")
        print(f"  JSON: {self.output_file}")
        print(f"  CSV:  {self.csv_output}")
        print("="*60)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Build Ultimate CMDB from reviewed labeled columns'
    )
    parser.add_argument(
        '--labels',
        default='reviewed_labeled_columns.json',
        help='Input file with reviewed column labels (default: reviewed_labeled_columns.json)'
    )
    parser.add_argument(
        '--output',
        default='ultimate_cmdb.json',
        help='Output JSON file (default: ultimate_cmdb.json)'
    )
    parser.add_argument(
        '--csv-output', 
        default='ultimate_cmdb.csv',
        help='Output CSV file (default: ultimate_cmdb.csv)'
    )
    
    args = parser.parse_args()
    
    # Create CMDB builder
    builder = UltimateCMDBBuilder(labels_file=args.labels)
    
    # Override output paths if specified
    if args.output != 'ultimate_cmdb.json':
        builder.output_file = Path(args.output)
    if args.csv_output != 'ultimate_cmdb.csv':
        builder.csv_output = Path(args.csv_output)
    
    # Build the CMDB
    try:
        builder.build_cmdb()
        print("\n✅ Ultimate CMDB generation completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Failed to build CMDB: {e}")
        raise

if __name__ == "__main__":
    main()