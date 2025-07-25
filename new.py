#!/usr/bin/env python3
"""
BigQuery Project Explorer - Robust Edition
Discovers all datasets, tables, columns, and samples data from the project
Uses identical authentication to the original script
Handles all edge cases gracefully
"""

import os
import json
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime
import logging
import time
import sys
from google.cloud.exceptions import NotFound, Forbidden, BadRequest, ServerError

# EXACT SAME SETUP AS ORIGINAL SCRIPT
file_path = os.path.join(os.path.dirname(__file__))
settings = {}

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bigquery_exploration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def authenticate_bigquery():
    """
    Authenticate with BigQuery using the exact same method as the original script
    """
    # EXACT SAME AUTHENTICATION AS ORIGINAL SCRIPT
    SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcr_prod_key.json")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    settings['KATANA_PG'] = {'client_encoding': 'utf8'}
    
    # Chronicle-fisv
    project = "chronicle-fisv"
    client = bigquery.Client(project=project, credentials=credentials)
    
    logger.info("Successfully authenticated with BigQuery")
    return client

def get_all_datasets(client):
    """
    Get all datasets in the project with comprehensive error handling
    """
    try:
        datasets = list(client.list_datasets())
        logger.info(f"Found {len(datasets)} datasets")
        return [dataset.dataset_id for dataset in datasets]
    except Forbidden as e:
        logger.error(f"Permission denied listing datasets: {e}")
        return []
    except NotFound as e:
        logger.error(f"Project not found: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error listing datasets: {e}")
        return []

def get_all_tables(client, dataset_id):
    """
    Get all tables in a dataset with comprehensive error handling
    """
    try:
        tables = list(client.list_tables(dataset_id))
        logger.info(f"Found {len(tables)} tables in dataset '{dataset_id}'")
        return [table.table_id for table in tables]
    except Forbidden as e:
        logger.warning(f"Permission denied accessing dataset '{dataset_id}': {e}")
        return []
    except NotFound as e:
        logger.warning(f"Dataset '{dataset_id}' not found: {e}")
        return []
    except Exception as e:
        logger.error(f"Error listing tables in dataset '{dataset_id}': {e}")
        return []

def get_table_schema(client, dataset_id, table_id):
    """
    Get schema (columns) for a table with comprehensive error handling
    """
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        
        columns = []
        for field in table.schema:
            # Handle nested/complex field types
            field_info = {
                'name': field.name,
                'type': field.field_type,
                'mode': field.mode,
                'description': field.description or 'No description'
            }
            
            # Handle nested fields (STRUCT/RECORD types)
            if field.field_type in ['RECORD', 'STRUCT'] and field.fields:
                field_info['nested_fields'] = []
                for nested_field in field.fields:
                    field_info['nested_fields'].append({
                        'name': nested_field.name,
                        'type': nested_field.field_type,
                        'mode': nested_field.mode
                    })
            
            columns.append(field_info)
        
        # Get additional table metadata
        table_info = {
            'num_rows': table.num_rows,
            'num_bytes': table.num_bytes,
            'created': table.created.isoformat() if table.created else None,
            'modified': table.modified.isoformat() if table.modified else None,
            'table_type': getattr(table, 'table_type', 'TABLE'),
            'partitioning': str(table.time_partitioning) if table.time_partitioning else None
        }
        
        logger.info(f"Found {len(columns)} columns in table '{dataset_id}.{table_id}' ({table.num_rows} rows)")
        return columns, table_info
        
    except Forbidden as e:
        logger.warning(f"Permission denied accessing table schema '{dataset_id}.{table_id}': {e}")
        return [], {'error': 'Permission denied'}
    except NotFound as e:
        logger.warning(f"Table '{dataset_id}.{table_id}' not found: {e}")
        return [], {'error': 'Table not found'}
    except Exception as e:
        logger.error(f"Error getting schema for table '{dataset_id}.{table_id}': {e}")
        return [], {'error': str(e)}

def sample_table_data(client, dataset_id, table_id, limit=5, timeout_seconds=30):
    """
    Get sample data from a table with comprehensive error handling and edge cases
    """
    try:
        # First check if table exists and get basic info
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        
        # Handle empty tables
        if table.num_rows == 0:
            logger.info(f"Table {dataset_id}.{table_id} is empty (0 rows)")
            return [{"info": "Table is empty - no data to sample"}]
        
        # Handle extremely large tables (>10B rows) - skip sampling
        if table.num_rows and table.num_rows > 10000000000:
            logger.warning(f"Skipping extremely large table {dataset_id}.{table_id} ({table.num_rows:,} rows)")
            return [{"warning": f"Table too large ({table.num_rows:,} rows) - sampling skipped for performance"}]
        
        # Handle views differently than tables
        if getattr(table, 'table_type', 'TABLE') == 'VIEW':
            logger.info(f"Sampling view {dataset_id}.{table_id}")
            # Views might be slow, reduce sample size
            limit = min(limit, 3)
        
        # Use the same project ID format as your original script
        full_table_id = f"chronicle-fisv.{dataset_id}.{table_id}"
        
        # Build query with safety checks
        query = f"""
        SELECT *
        FROM `{full_table_id}`
        LIMIT {limit}
        """
        
        # Set job config with timeout and other safety measures
        job_config = bigquery.QueryJobConfig()
        job_config.job_timeout_ms = timeout_seconds * 1000
        job_config.maximum_bytes_billed = 100000000  # 100MB max query cost
        job_config.use_query_cache = True
        
        logger.info(f"Sampling {limit} rows from {dataset_id}.{table_id}...")
        
        query_job = client.query(query, job_config=job_config)
        results = query_job.result(timeout=timeout_seconds)
        
        # Convert to list of dictionaries with data type handling
        sample_data = []
        for row_num, row in enumerate(results):
            row_dict = {"_row_number": row_num + 1}
            
            for key, value in row.items():
                try:
                    # Handle None/NULL values
                    if value is None:
                        row_dict[key] = None
                    # Handle datetime objects
                    elif hasattr(value, 'isoformat'):
                        row_dict[key] = value.isoformat()
                    # Handle bytes objects
                    elif isinstance(value, bytes):
                        row_dict[key] = f"<BYTES: {len(value)} bytes>"
                    # Handle complex nested data (arrays, structs)
                    elif isinstance(value, (list, dict)):
                        str_value = str(value)
                        if len(str_value) > 500:
                            row_dict[key] = str_value[:500] + "...[TRUNCATED]"
                        else:
                            row_dict[key] = str_value
                    # Handle very long strings
                    elif isinstance(value, str) and len(value) > 1000:
                        row_dict[key] = value[:1000] + "...[TRUNCATED]"
                    # Handle numbers that might be too large for JSON
                    elif isinstance(value, (int, float)):
                        if abs(value) > 1e15:  # Very large numbers
                            row_dict[key] = str(value)
                        else:
                            row_dict[key] = value
                    else:
                        row_dict[key] = value
                        
                except Exception as field_error:
                    logger.warning(f"Error processing field '{key}' in {dataset_id}.{table_id}: {field_error}")
                    row_dict[key] = f"<ERROR: {str(field_error)}>"
            
            sample_data.append(row_dict)
        
        # Add query statistics if available
        if query_job.done():
            stats = {
                "_query_stats": {
                    "bytes_processed": query_job.total_bytes_processed,
                    "bytes_billed": query_job.total_bytes_billed,
                    "slot_ms": query_job.slot_millis,
                    "creation_time": query_job.created.isoformat() if query_job.created else None
                }
            }
            sample_data.insert(0, stats)
        
        logger.info(f"Retrieved {len(sample_data)-1} sample rows from '{dataset_id}.{table_id}'")
        return sample_data
        
    except Forbidden as e:
        logger.warning(f"Permission denied sampling table '{dataset_id}.{table_id}': {e}")
        return [{"error": "Permission denied", "details": str(e)}]
    except NotFound as e:
        logger.warning(f"Table '{dataset_id}.{table_id}' not found during sampling: {e}")
        return [{"error": "Table not found", "details": str(e)}]
    except BadRequest as e:
        logger.warning(f"Bad request sampling table '{dataset_id}.{table_id}': {e}")
        return [{"error": "Invalid query", "details": str(e)}]
    except ServerError as e:
        logger.warning(f"Server error sampling table '{dataset_id}.{table_id}': {e}")
        return [{"error": "Server error", "details": str(e)}]
    except Exception as e:
        logger.error(f"Unexpected error sampling table '{dataset_id}.{table_id}': {e}")
        return [{"error": "Unexpected error", "details": str(e)}]

def explore_project_structure(client, max_tables_per_dataset=50, max_datasets=20):
    """
    Main function to explore the entire project structure with comprehensive edge case handling
    """
    start_time = time.time()
    
    project_structure = {
        'project_id': 'chronicle-fisv',
        'exploration_timestamp': datetime.now().isoformat(),
        'exploration_config': {
            'max_datasets': max_datasets,
            'max_tables_per_dataset': max_tables_per_dataset,
            'sample_size': 5
        },
        'datasets': {},
        'warnings': [],
        'errors': [],
        'statistics': {
            'total_datasets_found': 0,
            'total_datasets_processed': 0,
            'total_tables_found': 0,
            'total_tables_processed': 0,
            'total_columns_found': 0,
            'permission_errors': 0,
            'sampling_errors': 0
        }
    }
    
    print("="*80)
    print(f"🔍 EXPLORING BIGQUERY PROJECT: {project_structure['project_id']}")
    print(f"⏰ Started: {project_structure['exploration_timestamp']}")
    print(f"⚙️  Limits: Max {max_datasets} datasets, {max_tables_per_dataset} tables per dataset")
    print("="*80)
    
    try:
        # Get all datasets
        datasets = get_all_datasets(client)
        project_structure['statistics']['total_datasets_found'] = len(datasets)
        
        if not datasets:
            print("❌ No datasets found or permission denied")
            return project_structure
        
        if len(datasets) > max_datasets:
            warning_msg = f"Found {len(datasets)} datasets, limiting to first {max_datasets}"
            project_structure['warnings'].append(warning_msg)
            print(f"⚠️  {warning_msg}")
            datasets = datasets[:max_datasets]
        
        # Process each dataset
        for dataset_num, dataset_id in enumerate(datasets, 1):
            print(f"\n📁 DATASET {dataset_num}/{len(datasets)}: {dataset_id}")
            print("-" * 60)
            
            try:
                project_structure['datasets'][dataset_id] = {
                    'tables': {},
                    'dataset_errors': [],
                    'dataset_warnings': []
                }
                
                # Add small delay to avoid rate limiting
                if dataset_num > 1:
                    time.sleep(0.5)
                
                # Get all tables in the dataset
                tables = get_all_tables(client, dataset_id)
                
                if not tables:
                    warning_msg = f"No tables found in dataset '{dataset_id}' or permission denied"
                    project_structure['datasets'][dataset_id]['dataset_warnings'].append(warning_msg)
                    print(f"  ⚠️  {warning_msg}")
                    continue
                
                project_structure['statistics']['total_tables_found'] += len(tables)
                
                if len(tables) > max_tables_per_dataset:
                    warning_msg = f"Dataset {dataset_id} has {len(tables)} tables, limiting to first {max_tables_per_dataset}"
                    project_structure['datasets'][dataset_id]['dataset_warnings'].append(warning_msg)
                    print(f"  ⚠️  {warning_msg}")
                    tables = tables[:max_tables_per_dataset]
                
                # Process each table
                for table_num, table_id in enumerate(tables, 1):
                    print(f"\n  📊 TABLE {table_num}/{len(tables)}: {table_id}")
                    print("  " + "-" * 50)
                    
                    try:
                        project_structure['datasets'][dataset_id]['tables'][table_id] = {
                            'columns': [],
                            'table_info': {},
                            'sample_data': [],
                            'table_errors': []
                        }
                        
                        # Small delay between table operations
                        time.sleep(0.2)
                        
                        # Get table schema (columns)
                        columns, table_info = get_table_schema(client, dataset_id, table_id)
                        
                        if 'error' in table_info:
                            project_structure['datasets'][dataset_id]['tables'][table_id]['table_errors'].append(table_info['error'])
                            project_structure['statistics']['permission_errors'] += 1
                            print(f"    ❌ Schema Error: {table_info['error']}")
                            continue
                        
                        project_structure['datasets'][dataset_id]['tables'][table_id]['columns'] = columns
                        project_structure['datasets'][dataset_id]['tables'][table_id]['table_info'] = table_info
                        project_structure['statistics']['total_columns_found'] += len(columns)
                        
                        # Display column information
                        print(f"    🔑 COLUMNS ({len(columns)} total):")
                        for col in columns[:10]:  # Show first 10 columns
                            nested_info = ""
                            if 'nested_fields' in col:
                                nested_info = f" [{len(col['nested_fields'])} nested fields]"
                            print(f"      • {col['name']} ({col['type']}{nested_info}) - {col['description'][:50]}...")
                        
                        if len(columns) > 10:
                            print(f"      ... and {len(columns) - 10} more columns")
                        
                        # Display table info
                        if table_info.get('num_rows') is not None:
                            print(f"    📈 TABLE INFO: {table_info['num_rows']:,} rows, {table_info.get('num_bytes', 0):,} bytes")
                            if table_info.get('table_type'):
                                print(f"      Type: {table_info['table_type']}")
                        
                        # Get sample data
                        print(f"    🔬 Sampling data...")
                        sample_data = sample_table_data(client, dataset_id, table_id, limit=5)
                        project_structure['datasets'][dataset_id]['tables'][table_id]['sample_data'] = sample_data
                        
                        # Display sample data
                        if sample_data and not any('error' in str(row) for row in sample_data[:1]):
                            print(f"    📋 SAMPLE DATA:")
                            for i, row in enumerate(sample_data[:3]):  # Show first 3 rows
                                if '_query_stats' in row:
                                    continue
                                print(f"      Row {row.get('_row_number', i+1)}:")
                                row_items = list(row.items())[:5]  # Show first 5 columns
                                for key, value in row_items:
                                    if key == '_row_number':
                                        continue
                                    display_value = str(value)
                                    if len(display_value) > 80:
                                        display_value = display_value[:80] + "..."
                                    print(f"        {key}: {display_value}")
                                if len(row) > 6:  # 5 + _row_number
                                    print(f"        ... and {len(row) - 6} more columns")
                                print()
                        else:
                            # Check for errors in sample data
                            error_found = False
                            for row in sample_data:
                                if isinstance(row, dict) and 'error' in row:
                                    print(f"    ❌ Sampling Error: {row['error']}")
                                    project_structure['statistics']['sampling_errors'] += 1
                                    error_found = True
                                    break
                                elif isinstance(row, dict) and 'warning' in row:
                                    print(f"    ⚠️  Sampling Warning: {row['warning']}")
                                    break
                            
                            if not error_found and not sample_data:
                                print("    📋 No sample data available")
                        
                        project_structure['statistics']['total_tables_processed'] += 1
                        
                    except KeyboardInterrupt:
                        print(f"\n⏹️  Exploration interrupted by user")
                        raise
                    except Exception as table_error:
                        error_msg = f"Unexpected error processing table {table_id}: {str(table_error)}"
                        project_structure['datasets'][dataset_id]['tables'][table_id]['table_errors'].append(error_msg)
                        project_structure['errors'].append(error_msg)
                        logger.error(error_msg)
                        print(f"    ❌ Table Error: {str(table_error)}")
                
                project_structure['statistics']['total_datasets_processed'] += 1
                
            except KeyboardInterrupt:
                print(f"\n⏹️  Exploration interrupted by user")
                raise
            except Exception as dataset_error:
                error_msg = f"Error processing dataset {dataset_id}: {str(dataset_error)}"
                project_structure['errors'].append(error_msg)
                logger.error(error_msg)
                print(f"  ❌ Dataset Error: {str(dataset_error)}")
        
        # Calculate final statistics
        end_time = time.time()
        project_structure['statistics']['exploration_duration_seconds'] = round(end_time - start_time, 2)
        project_structure['completion_timestamp'] = datetime.now().isoformat()
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Exploration interrupted by user after {time.time() - start_time:.1f} seconds")
        project_structure['interrupted'] = True
        project_structure['completion_timestamp'] = datetime.now().isoformat()
    except Exception as e:
        error_msg = f"Fatal error during project exploration: {str(e)}"
        project_structure['errors'].append(error_msg)
        logger.error(error_msg)
        print(f"💥 Fatal Error: {str(e)}")
    
    return project_structure
    
    for dataset_id in datasets:
        print(f"\n📁 DATASET: {dataset_id}")
        print("-" * 50)
        
        project_structure['datasets'][dataset_id] = {
            'tables': {}
        }
        
        # Get all tables in the dataset
        tables = get_all_tables(client, dataset_id)
        
        if len(tables) > max_tables_per_dataset:
            project_structure['warnings'].append(f"Dataset {dataset_id} has {len(tables)} tables, limiting to first {max_tables_per_dataset}")
            tables = tables[:max_tables_per_dataset]
        
        for table_id in tables:
            print(f"\n  📊 TABLE: {table_id}")
            print("  " + "-" * 40)
            
            project_structure['datasets'][dataset_id]['tables'][table_id] = {
                'columns': [],
                'sample_data': []
            }
            
            # Get table schema (columns)
            columns = get_table_schema(client, dataset_id, table_id)
            project_structure['datasets'][dataset_id]['tables'][table_id]['columns'] = columns
            
            print(f"    🔑 COLUMNS ({len(columns)} total):")
            for col in columns:
                print(f"      • {col['name']} ({col['type']}) - {col['description']}")
            
            # Get sample data
            sample_data = sample_table_data(client, dataset_id, table_id, limit=5)
            project_structure['datasets'][dataset_id]['tables'][table_id]['sample_data'] = sample_data
            
            if sample_data:
                print(f"\n    📋 SAMPLE DATA (5 rows):")
                for i, row in enumerate(sample_data, 1):
                    print(f"      Row {i}:")
                    for key, value in row.items():
                        # Truncate long values for readability
                        display_value = str(value)
                        if len(display_value) > 100:
                            display_value = display_value[:100] + "..."
                        print(f"        {key}: {display_value}")
                    print()
            else:
                print("    📋 SAMPLE DATA: No data available or table is empty")
            
            print()
    
    return project_structure

def save_results_to_file(project_structure, filename="bigquery_exploration_results.json"):
    """
    Save the exploration results to a JSON file
    """
    try:
        with open(filename, 'w') as f:
            json.dump(project_structure, f, indent=2, default=str)
        logger.info(f"Results saved to {filename}")
        print(f"\n💾 Full results saved to: {filename}")
    except Exception as e:
        logger.error(f"Error saving results to file: {e}")

def main():
    """
    Main execution function with comprehensive error handling
    """
    print("🚀 Starting BigQuery Project Explorer...")
    
    try:
        # Authenticate with BigQuery (using identical method to your script)
        print("🔐 Authenticating with BigQuery...")
        client = authenticate_bigquery()
        
        # Ask user for exploration limits
        print("\n⚙️  Configuration Options:")
        print("1. Quick exploration (5 datasets, 10 tables each)")
        print("2. Medium exploration (20 datasets, 50 tables each)")  
        print("3. Full exploration (50+ datasets, 100+ tables each)")
        print("4. Custom limits")
        
        while True:
            try:
                choice = input("\nSelect option (1-4): ").strip()
                if choice == "1":
                    max_datasets, max_tables = 5, 10
                    break
                elif choice == "2":
                    max_datasets, max_tables = 20, 50
                    break
                elif choice == "3":
                    max_datasets, max_tables = 100, 200
                    break
                elif choice == "4":
                    max_datasets = int(input("Max datasets to explore: "))
                    max_tables = int(input("Max tables per dataset: "))
                    break
                else:
                    print("Please enter 1, 2, 3, or 4")
            except ValueError:
                print("Please enter valid numbers")
            except KeyboardInterrupt:
                print("\nExiting...")
                return
        
        print(f"\n🎯 Starting exploration with limits: {max_datasets} datasets, {max_tables} tables per dataset")
        print("💡 You can interrupt anytime with Ctrl+C to get partial results")
        
        # Explore the entire project structure
        project_structure = explore_project_structure(client, max_tables_per_dataset=max_tables, max_datasets=max_datasets)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bigquery_exploration_results_{timestamp}.json"
        save_results_to_file(project_structure, filename)
        
        # Print comprehensive summary
        stats = project_structure['statistics']
        print("\n" + "="*80)
        print("📊 EXPLORATION SUMMARY")
        print("="*80)
        print(f"⏱️  Duration: {stats.get('exploration_duration_seconds', 0):.1f} seconds")
        print(f"📁 Datasets: {stats['total_datasets_processed']}/{stats['total_datasets_found']} processed")
        print(f"📊 Tables: {stats['total_tables_processed']}/{stats['total_tables_found']} processed")
        print(f"🔑 Total Columns: {stats['total_columns_found']:,}")
        print(f"❌ Permission Errors: {stats['permission_errors']}")
        print(f"⚠️  Sampling Errors: {stats['sampling_errors']}")
        print(f"💾 Results saved to: {filename}")
        
        if project_structure.get('warnings'):
            print(f"\n⚠️  Warnings ({len(project_structure['warnings'])}):")
            for warning in project_structure['warnings'][:5]:
                print(f"   • {warning}")
            if len(project_structure['warnings']) > 5:
                print(f"   • ... and {len(project_structure['warnings']) - 5} more warnings")
        
        if project_structure.get('errors'):
            print(f"\n❌ Errors ({len(project_structure['errors'])}):")
            for error in project_structure['errors'][:3]:
                print(f"   • {error}")
            if len(project_structure['errors']) > 3:
                print(f"   • ... and {len(project_structure['errors']) - 3} more errors")
        
        print("="*80)
        
        # Final success message
        if stats['total_tables_processed'] > 0:
            print("✅ Exploration completed successfully!")
            print(f"📋 Check the JSON file for complete details of all {stats['total_tables_processed']} tables")
        else:
            print("⚠️  Exploration completed but no tables were successfully processed")
            print("🔍 Check the log file and error messages above for details")
        
        logger.info("Project exploration completed successfully")
        
    except KeyboardInterrupt:
        print("\n⏹️  Exploration interrupted by user")
        logger.info("Exploration interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during exploration: {e}")
        print(f"\n💥 Fatal Error: {e}")
        print("📝 Check bigquery_exploration.log for detailed error information")
        sys.exit(1)

if __name__ == "__main__":
    main()