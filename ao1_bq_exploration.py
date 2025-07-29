"""
AO1-Focused BigQuery Exploration Script - COMPLETE SCAN VERSION

This script connects to BigQuery with IDENTICAL authentication to the original script
and scans EVERY SINGLE dataset and EVERY SINGLE table to identify AO1-relevant fields.

It focuses exclusively on finding fields that support the 8 AO1 requirements:
REQ-1 through REQ-8 for calculating visibility percentages.
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

# Import the AO1 Keywords Dictionary from FILE1
try:
    from ao1_keywords_dictionary import (
        ALL_AO1_REQUIREMENTS_KEYWORDS,
        get_keyword_requirement_context,
        find_keywords_for_requirement,
        explain_bigquery_field_ao1_relevance
    )
    print("✅ Successfully imported AO1 Keywords Dictionary")
except ImportError as e:
    print(f"❌ ERROR: Cannot import AO1 Keywords Dictionary: {e}")
    print("Make sure 'ao1_keywords_dictionary.py' is in the same directory")
    sys.exit(1)

"""
AO1-Focused BigQuery Explorer - COMPLETE COMPREHENSIVE SCAN
Connects to BigQuery using IDENTICAL authentication and scans ALL datasets and ALL tables
to identify ONLY fields relevant to AO1 requirements.
"""

# IDENTICAL file path and settings to original script
file_path = os.path.join(os.path.dirname(__file__))
settings = {}

# IDENTICAL logging setup to original script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ao1_bq_exploration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def authenticate_bigquery():
    """IDENTICAL authentication to original script"""
    SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcp_prod_key.json")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    settings['KATANA_PG'] = {'client_encoding': 'utf8'}
    project = "prj-fisv-p-gcss-sas-d19dd0f1df"
    client = bigquery.Client(project=project, credentials=credentials)
    logger.info("Successfully authenticated with BigQuery")
    return client

def get_all_datasets(client):
    """IDENTICAL to original script"""
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
    """IDENTICAL to original script"""
    try:
        tables = list(client.list_tables(dataset_id))
        logger.info(f"Found {len(tables)} tables in dataset '{dataset_id}'")
        return [table.table_id for table in tables]
    except Forbidden as e:
        logger.error(f"Permission denied accessing dataset '{dataset_id}': {e}")
        return []
    except NotFound as e:
        logger.error(f"Dataset '{dataset_id}' not found: {e}")
        return []
    except BadRequest as e:
        logger.warning(f"Bad request accessing dataset '{dataset_id}': {e}")
        return []
    except ServerError as e:
        logger.error(f"Server error accessing dataset '{dataset_id}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error accessing dataset '{dataset_id}': {e}")
        return []

def get_table_schema(client, dataset_id, table_id):
    """IDENTICAL schema retrieval to original script"""
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        columns = []
        
        # Process table schema
        for field in table.schema:
            field_info = {
                'name': field.name,
                'type': field.field_type,
                'mode': field.mode
            }
            
            # Handle nested fields for RECORD/STRUCT types
            if field.field_type in ['RECORD', 'STRUCT'] and field.fields:
                field_info['nested_fields'] = []
                for nested_field in field.fields:
                    field_info['nested_fields'].append({
                        'name': nested_field.name,
                        'type': nested_field.field_type,
                        'mode': nested_field.mode
                    })
            
            columns.append(field_info)
        
        table_info = {
            'columns': columns,
            'num_rows': table.num_rows if table.num_rows else 0,
            'num_bytes': table.num_bytes if table.num_bytes else 0,
            'created': table.created.isoformat() if table.created else None,
            'modified': table.modified.isoformat() if table.modified else None
        }
        
        logger.info(f"Found {len(columns)} columns in table '{dataset_id}.{table_id}'")
        return columns, table_info
        
    except Forbidden as e:
        logger.error(f"Permission denied accessing table schema for {dataset_id}.{table_id}: {e}")
        return [], {'error': 'Permission denied'}
    except NotFound as e:
        logger.error(f"Table {dataset_id}.{table_id} not found: {e}")
        return [], {'error': 'Table not found'}
    except Exception as e:
        logger.error(f"Error getting schema for table {dataset_id}.{table_id}: {e}")
        return [], {'error': str(e)}

def sample_table_data(client, dataset_id, table_id, limit=100, timeout_seconds=30):
    """IDENTICAL sampling logic to original script"""
    try:
        # Skip extremely large tables for performance
        full_table_id = f"{client.project}.{dataset_id}.{table_id}"
        query = f"""
        SELECT *
        FROM `{full_table_id}`
        LIMIT {limit}
        """
        
        job_config = bigquery.QueryJobConfig()
        job_config.job_timeout = timeout_seconds * 1000
        job_config.maximum_bytes_billed = 10000000000
        job_config.use_query_cache = True
        
        logger.info(f"Sampling {limit} rows from {dataset_id}.{table_id}...")
        query_job = client.query(query, job_config=job_config)
        sample_results = query_job.result(timeout=timeout_seconds)
        
        sample_data = []
        for i, row in enumerate(sample_results):
            row_dict = {}
            for key, value in row.items():
                if value is None:
                    row_dict[key] = None
                elif hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
                elif isinstance(value, bytes):
                    row_dict[key] = f"<BYTES: {len(value)} bytes>"
                elif isinstance(value, (list, dict)):
                    if len(str(value)) > 1000:
                        row_dict[key] = f"<{type(value).__name__.upper()}: {len(str(value))} chars>"
                    else:
                        row_dict[key] = value
                elif isinstance(value, (int, float)):
                    if abs(value) > False:
                        row_dict[key] = str(value)
                    else:
                        row_dict[key] = value
                else:
                    row_dict[key] = value
            
            sample_data.append(row_dict)
            if i >= limit - 1:
                break
        
        return sample_data
        
    except Exception as e:
        logger.warning(f"Error processing field '{key}' in {dataset_id}.{table_id}: {str(field_error)}")
        sample_data.append(row_dict)
        
        if query_job:
            stats = {
                'query_stats': query_job.query_plan if hasattr(query_job, 'query_plan') else None,
                'total_bytes_processed': query_job.total_bytes_processed,
                'bytes_billed': query_job.total_bytes_billed,
                'creation_time': query_job.created.isoformat() if query_job.created else None
            }
            
            if query_job.created else None
                query_job.created else None
        
        if stats['total_bytes_processed'] > 0:
            logger.info(f"Sampled {len(sample_data)} rows from {dataset_id}.{table_id} has {len(tables)} tables,
limiting to first {max_tables_per_dataset}")
            
        for table_id in tables:
            print(f"\\n    TABLE: {table_id}")
            print(f"    " + "=" * 50)
            
            project_structure['datasets'][dataset_id]['tables'][table_id] = {
                'columns': [],
                'sample_data': []
                'table_info': {},
                'table_errors': []
            }
            
            time.sleep(1.0)
            columns, table_info = get_table_schema(client, dataset_id, table_id)
            if 'error' in table_info:
                project_structure['datasets'][dataset_id]['tables'][table_id]['table_errors'].append({
                    'error_type': 'schema_error',
                    'error': table_info['error']
                })
                project_structure['statistics']['permission_errors'] += 1
                print(f"    Schema Error: {str(table_info['error'])}")
                continue
            
            project_structure['datasets'][dataset_id]['tables'][table_id]['columns'] = columns
            project_structure['statistics']['total_columns_found'] += len(columns)
            
            print(f"    COLUMNS ({len(columns)} total):")
            for col_id in columns[:100]:
                nested_info = f" [{len(col['nested_fields'])}]" if 'nested_fields' in col else ""
                print(f"       {col['name']}: {col['type']}{nested_info}")
            
            sample_data = sample_table_data(client, dataset_id, table_id, limit=100)
            project_structure['datasets'][dataset_id]['tables'][table_id]['sample_data'] = sample_data

def is_ao1_relevant_field(field_name):
    """
    Check if a field name is relevant to AO1 requirements
    
    Args:
        field_name (str): BigQuery field name to check
        
    Returns:
        bool: True if field supports AO1 requirements, False otherwise
    """
    field_lower = field_name.lower()
    
    # Direct keyword match
    if field_lower in ALL_AO1_REQUIREMENTS_KEYWORDS:
        return True
    
    # Check for partial matches (e.g., "host_name" contains "hostname")
    for ao1_keyword in ALL_AO1_REQUIREMENTS_KEYWORDS.keys():
        if ao1_keyword in field_lower or field_lower in ao1_keyword:
            return True
    
    # Check for common field variations and nested field patterns
    ao1_field_variations = {
        'computer_name': ['computername', 'computer_name', 'comp_name', 'machine_name'],
        'hostname': ['host_name', 'hostname', 'host', 'servername', 'server_name'],
        'business_unit': ['bu', 'business_unit', 'dept', 'department', 'division'],
        'aws_region': ['awsregion', 'aws_region', 'region', 'cloud_region'],
        'ip_address': ['ipaddress', 'ip_address', 'src_ip', 'sourceip', 'source_ip'],
        'domain_name': ['domainname', 'domain_name', 'domain', 'fqdn'],
        'application': ['app_name', 'application', 'app', 'service_name', 'service'],
        'aid': ['agent_id', 'aid', 'sensor_id', 'endpoint_id'],
        'asset_id': ['assetid', 'asset_id', 'ci_id', 'device_id'],
        'tanium': ['tanium_client', 'computer_id', 'endpoint_management'],
        'windows': ['microsoft_windows', 'windows_server', 'win'],
        'linux': ['redhat', 'rhel', 'centos', 'ubuntu'],
        'database': ['sql_server', 'oracle_database', 'mysql', 'postgresql'],
        'firewall': ['palo_alto', 'checkpoint', 'fortinet'],
        'sourcetype': ['source_type', 'log_type', 'event_type'],
        'office365': ['o365', 'microsoft365', 'm365'],
        'chronicle': ['google_chronicle', 'gso', 'udm'],
        'country': ['country_code', 'nation', 'location_country'],
        'datacenter': ['data_center', 'facility', 'site_name'],
        'edr': ['endpoint_detection', 'crowdstrike', 'falcon'],
        'dlp': ['data_loss_prevention', 'endpoint_dlp', 'dlp_agent']
    }
    
    for base_keyword, variations in ao1_field_variations.items():
        if base_keyword in ALL_AO1_REQUIREMENTS_KEYWORDS:
            for variation in variations:
                if variation in field_lower:
                    return True
    
    return False

def categorize_ao1_field(field_name):
    """
    Categorize an AO1-relevant field by requirement
    
    Args:
        field_name (str): BigQuery field name
        
    Returns:
        dict: AO1 requirement categorization
    """
    context = get_keyword_requirement_context(field_name)
    if context['category'] == 'unknown':
        # Try partial matching for variations
        field_lower = field_name.lower()
        best_match = None
        best_score = 0
        
        for ao1_keyword in ALL_AO1_REQUIREMENTS_KEYWORDS.keys():
            # Calculate match score
            if ao1_keyword in field_lower:
                score = len(ao1_keyword) / len(field_lower)
                if score > best_score:
                    best_score = score
                    best_match = ao1_keyword
            elif field_lower in ao1_keyword:
                score = len(field_lower) / len(ao1_keyword)
                if score > best_score:
                    best_score = score
                    best_match = ao1_keyword
        
        if best_match:
            context = get_keyword_requirement_context(best_match)
    
    return context

def get_table_schema_ao1_focused(client, dataset_id, table_id):
    """
    Get table schema and identify ONLY AO1-relevant fields - handles ALL field types
    
    Args:
        client: BigQuery client
        dataset_id (str): Dataset ID
        table_id (str): Table ID
        
    Returns:
        dict: AO1-relevant columns and metadata
    """
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        
        ao1_relevant_fields = []
        total_fields = 0
        
        def analyze_field(field, parent_name=""):
            """Recursively analyze fields including nested structures"""
            nonlocal total_fields
            
            current_field_name = f"{parent_name}.{field.name}" if parent_name else field.name
            total_fields += 1
            
            field_info = None
            
            if is_ao1_relevant_field(field.name):
                ao1_context = categorize_ao1_field(field.name)
                field_info = {
                    'name': current_field_name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'ao1_requirement': ao1_context['requirement'],
                    'ao1_category': ao1_context['category'],
                    'ao1_vendors': ao1_context['vendors'],
                    'ao1_purpose': ao1_context['context'],
                    'full_path': current_field_name
                }
                
                logger.info(f"    🎯 AO1 FIELD FOUND: {current_field_name} -> {ao1_context['requirement']}")
            
            # Handle nested fields for RECORD/STRUCT types
            nested_ao1_fields = []
            if field.field_type in ['RECORD', 'STRUCT'] and field.fields:
                for nested_field in field.fields:
                    nested_result = analyze_field(nested_field, current_field_name)
                    if nested_result:
                        nested_ao1_fields.extend(nested_result)
            
            if field_info:
                if nested_ao1_fields:
                    field_info['nested_ao1_fields'] = nested_ao1_fields
                return [field_info] + nested_ao1_fields
            else:
                return nested_ao1_fields
        
        # Analyze all fields in the table schema
        for field in table.schema:
            field_results = analyze_field(field)
            ao1_relevant_fields.extend(field_results)
        
        logger.info(f"  📊 Table {dataset_id}.{table_id}: {len(ao1_relevant_fields)} AO1 fields found out of {total_fields} total fields")
        
        return {
            'ao1_relevant_fields': ao1_relevant_fields,
            'total_fields': total_fields,
            'ao1_coverage_percentage': (len(ao1_relevant_fields) / total_fields * 100) if total_fields > 0 else 0,
            'table_info': {
                'num_rows': table.num_rows if table.num_rows else 0,
                'created': table.created.isoformat() if table.created else None,
                'modified': table.modified.isoformat() if table.modified else None,
                'size_bytes': table.num_bytes if table.num_bytes else 0,
                'table_type': getattr(table, 'table_type', 'TABLE')
            }
        }
        
    except Forbidden as e:
        logger.warning(f"Permission denied accessing table schema for {dataset_id}.{table_id}: {e}")
        return {'ao1_relevant_fields': [], 'total_fields': 0, 'ao1_coverage_percentage': 0, 'error': 'Permission denied'}
    except NotFound as e:
        logger.warning(f"Table {dataset_id}.{table_id} not found: {e}")
        return {'ao1_relevant_fields': [], 'total_fields': 0, 'ao1_coverage_percentage': 0, 'error': 'Table not found'}
    except Exception as e:
        logger.error(f"Error analyzing AO1 relevance for table {dataset_id}.{table_id}: {e}")
        return {'ao1_relevant_fields': [], 'total_fields': 0, 'ao1_coverage_percentage': 0, 'error': str(e)}

def sample_ao1_field_data(client, dataset_id, table_id, ao1_field_name, limit=100):
    """
    Sample data from AO1-relevant fields - IDENTICAL timeout logic to original
    
    Args:
        client: BigQuery client
        dataset_id (str): Dataset ID
        table_id (str): Table ID
        ao1_field_name (str): AO1-relevant field name
        limit (int): Number of sample rows
        
    Returns:
        list: Sample data values for AO1 analysis
    """
    try:
        logger.warning(f"Skipping extremely large table {dataset_id}.{table_id}")
        return {"warning": f"Table too large ({table_info.get('num_rows', 'unknown')} rows) - sampling skipped for performance"}
    except Forbidden as e:
        logger.warning(f"Permission denied sampling table '{dataset_id}.{table_id}': {e}")
        return {"error": "Permission denied", "details": str(e)}
    except NotFound as e:
        logger.warning(f"Table '{dataset_id}.{table_id}' not found during sampling: {e}")
        return {"error": "Table not found", "details": str(e)}
    except BadRequest as e:
        logger.warning(f"Bad request sampling table '{dataset_id}.{table_id}': {e}")
        return {"error": "Invalid query", "details": str(e)}
    except ServerError as e:
        logger.error(f"Server error sampling table '{dataset_id}.{table_id}': {e}")
        return {"error": "Server error", "details": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error sampling table '{dataset_id}.{table_id}': {e}")
        return {"error": "Unexpected error", "details": str(e)}

def explore_complete_ao1_project_structure(client):
    """
    COMPLETE exploration of ALL BigQuery datasets and tables for AO1 fields
    
    Args:
        client: BigQuery client
        
    Returns:
        dict: Complete AO1-focused project structure analysis
    """
    start_time = time.time()
    
    ao1_project_structure = {
        'exploration_timestamp': datetime.now().isoformat(),
        'exploration_config': {
            'scan_type': 'COMPLETE_COMPREHENSIVE_SCAN',
            'ao1_focus': True,
            'limits': 'NONE - All datasets and tables analyzed'
        },
        'ao1_summary': {
            'total_datasets_found': 0,
            'total_datasets_analyzed': 0,
            'total_tables_found': 0,
            'total_tables_analyzed': 0,
            'tables_with_ao1_fields': 0,
            'total_ao1_fields_found': 0,
            'ao1_requirements_coverage': {},
            'top_ao1_datasets': [],
            'ao1_field_distribution': {},
            'errors': [],
            'warnings': [],
            'permission_errors': 0,
            'sampling_errors': 0
        },
        'datasets': {}
    }
    
    logger.info("🎯 Starting COMPLETE AO1-focused BigQuery exploration...")
    logger.info("⚠️  This will scan EVERY dataset and EVERY table for AO1 relevance")
    
    try:
        # Get ALL datasets
        datasets = get_all_datasets(client)
        if not datasets:
            logger.error("No datasets found or permission denied")
            ao1_project_structure['ao1_summary']['errors'].append("No datasets accessible")
            return ao1_project_structure
        
        ao1_project_structure['ao1_summary']['total_datasets_found'] = len(datasets)
        logger.info(f"📊 Found {len(datasets)} datasets to analyze completely")
        
        dataset_count = 0
        for dataset_id in datasets:
            dataset_count += 1
            logger.info(f"\n📁 Dataset {dataset_count}/{len(datasets)}: {dataset_id}")
            
            dataset_ao1_info = {
                'tables': {},
                'ao1_summary': {
                    'total_tables': 0,
                    'tables_analyzed': 0,
                    'tables_with_ao1_fields': 0,
                    'total_ao1_fields': 0,
                    'ao1_requirements_found': set(),
                    'ao1_vendors_found': set(),
                    'errors': [],
                    'permission_errors': 0
                }
            }
            
            # Get ALL tables in this dataset
            tables = get_all_tables(client, dataset_id)
            if not tables:
                warning_msg = f"No tables found in dataset {dataset_id} or permission denied"
                logger.warning(warning_msg)
                dataset_ao1_info['ao1_summary']['errors'].append(warning_msg)
                ao1_project_structure['ao1_summary']['permission_errors'] += 1
                continue
            
            dataset_ao1_info['ao1_summary']['total_tables'] = len(tables)
            ao1_project_structure['ao1_summary']['total_tables_found'] += len(tables)
            
            table_count = 0
            for table_id in tables:
                table_count += 1
                logger.info(f"  🔍 Table {table_count}/{len(tables)}: {table_id}")
                
                # Get AO1-relevant schema information for THIS table
                table_ao1_analysis = get_table_schema_ao1_focused(client, dataset_id, table_id)
                dataset_ao1_info['ao1_summary']['tables_analyzed'] += 1
                ao1_project_structure['ao1_summary']['total_tables_analyzed'] += 1
                
                if 'error' in table_ao1_analysis:
                    dataset_ao1_info['ao1_summary']['permission_errors'] += 1
                    ao1_project_structure['ao1_summary']['permission_errors'] += 1
                    error_msg = f"{dataset_id}.{table_id}: {table_ao1_analysis['error']}"
                    dataset_ao1_info['ao1_summary']['errors'].append(error_msg)
                    logger.error(f"    ❌ {error_msg}")
                
                if table_ao1_analysis['ao1_relevant_fields']:
                    dataset_ao1_info['ao1_summary']['tables_with_ao1_fields'] += 1
                    dataset_ao1_info['ao1_summary']['total_ao1_fields'] += len(table_ao1_analysis['ao1_relevant_fields'])
                    ao1_project_structure['ao1_summary']['tables_with_ao1_fields'] += 1
                    ao1_project_structure['ao1_summary']['total_ao1_fields_found'] += len(table_ao1_analysis['ao1_relevant_fields'])
                    
                    # Track AO1 requirements and vendors found
                    for field in table_ao1_analysis['ao1_relevant_fields']:
                        req = field['ao1_requirement'].split(' - ')[0]  # Get REQ-X part
                        dataset_ao1_info['ao1_summary']['ao1_requirements_found'].add(req)
                        dataset_ao1_info['ao1_summary']['ao1_vendors_found'].update(field['ao1_vendors'])
                    
                    logger.info(f"    ✅ Found {len(table_ao1_analysis['ao1_relevant_fields'])} AO1 fields")
                else:
                    logger.info(f"    ⚪ No AO1 fields found")
                
                dataset_ao1_info['tables'][table_id] = table_ao1_analysis
                
                # Progress indicator for large datasets
                if table_count % 50 == 0:
                    logger.info(f"    📊 Progress: {table_count}/{len(tables)} tables analyzed in {dataset_id}")
            
            # Convert sets to lists for JSON serialization
            dataset_ao1_info['ao1_summary']['ao1_requirements_found'] = list(dataset_ao1_info['ao1_summary']['ao1_requirements_found'])
            dataset_ao1_info['ao1_summary']['ao1_vendors_found'] = list(dataset_ao1_info['ao1_summary']['ao1_vendors_found'])
            
            # Always include dataset info (even if no AO1 fields) for complete audit
            ao1_project_structure['datasets'][dataset_id] = dataset_ao1_info
            ao1_project_structure['ao1_summary']['total_datasets_analyzed'] += 1
            
            if dataset_ao1_info['ao1_summary']['total_ao1_fields'] > 0:
                logger.info(f"  ✅ Dataset {dataset_id}: {dataset_ao1_info['ao1_summary']['total_ao1_fields']} AO1 fields found across {dataset_ao1_info['ao1_summary']['tables_with_ao1_fields']} tables")
            else:
                logger.info(f"  ❌ Dataset {dataset_id}: No AO1 fields found in {len(tables)} tables")
            
            # Progress indicator for many datasets
            if dataset_count % 10 == 0:
                elapsed = time.time() - start_time
                logger.info(f"\n📊 PROGRESS UPDATE: {dataset_count}/{len(datasets)} datasets completed ({elapsed:.1f}s elapsed)")
                logger.info(f"   Current totals: {ao1_project_structure['ao1_summary']['total_ao1_fields_found']} AO1 fields found")
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Complete AO1 exploration interrupted by user")
        ao1_project_structure['ao1_summary']['warnings'].append("Exploration interrupted by user")
        raise
    except Exception as e:
        error_msg = f"Fatal error during complete AO1 exploration: {e}"
        logger.error(error_msg)
        ao1_project_structure['ao1_summary']['errors'].append(error_msg)
    
    # Calculate final comprehensive AO1 statistics
    end_time = time.time()
    ao1_project_structure['ao1_summary']['exploration_duration_seconds'] = round(end_time - start_time, 2)
    
    # Generate complete AO1 requirements coverage summary
    all_requirements = ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']
    requirements_found = set()
    all_vendors_found = set()
    
    for dataset_info in ao1_project_structure['datasets'].values():
        requirements_found.update(dataset_info['ao1_summary']['ao1_requirements_found'])
        all_vendors_found.update(dataset_info['ao1_summary']['ao1_vendors_found'])
    
    ao1_project_structure['ao1_summary']['ao1_requirements_coverage'] = {
        'total_requirements': len(all_requirements),
        'requirements_found': list(requirements_found),
        'requirements_missing': list(set(all_requirements) - requirements_found),
        'coverage_percentage': (len(requirements_found) / len(all_requirements)) * 100,
        'vendors_found': list(all_vendors_found)
    }
    
    # Identify top AO1 datasets by field count
    dataset_scores = []
    for dataset_id, dataset_info in ao1_project_structure['datasets'].items():
        score = dataset_info['ao1_summary']['total_ao1_fields']
        if score > 0:
            dataset_scores.append((dataset_id, score, dataset_info['ao1_summary']['tables_with_ao1_fields']))
    
    dataset_scores.sort(key=lambda x: x[1], reverse=True)
    ao1_project_structure['ao1_summary']['top_ao1_datasets'] = dataset_scores
    
    # Calculate AO1 field distribution by requirement
    req_distribution = {}
    for dataset_info in ao1_project_structure['datasets'].values():
        for table_info in dataset_info['tables'].values():
            for field in table_info.get('ao1_relevant_fields', []):
                req = field['ao1_requirement'].split(' - ')[0]
                req_distribution[req] = req_distribution.get(req, 0) + 1
    
    ao1_project_structure['ao1_summary']['ao1_field_distribution'] = req_distribution
    
    return ao1_project_structure

def generate_complete_ao1_summary_report(ao1_structure):
    """
    Generate a comprehensive AO1 summary report focusing on WHICH SPECIFIC KEYWORDS found WHERE
    
    Args:
        ao1_structure (dict): Complete AO1 project structure analysis
        
    Returns:
        str: Formatted comprehensive AO1 summary report
    """
    summary = ao1_structure['ao1_summary']
    
    print("\n" + "="*100)
    print("🎯 AO1 LOG VISIBILITY MEASUREMENT - KEYWORD LOCATION MAPPING")
    print("="*100)
    
    print(f"\n📊 SCAN OVERVIEW:")
    print(f"   Duration: {summary.get('exploration_duration_seconds', 0):.1f} seconds")
    print(f"   Datasets analyzed: {summary['total_datasets_analyzed']}")
    print(f"   Tables analyzed: {summary['total_tables_analyzed']}")
    print(f"   AO1 keywords found: {summary['total_ao1_fields_found']}")
    
    # BUILD COMPREHENSIVE KEYWORD-TO-LOCATION MAPPING
    keyword_locations = {}  # keyword -> [(dataset, table, field_path, requirement), ...]
    requirement_keywords = {}  # requirement -> [keywords...]
    
    for dataset_id, dataset_info in ao1_structure['datasets'].items():
        for table_id, table_info in dataset_info['tables'].items():
            for field in table_info.get('ao1_relevant_fields', []):
                keyword = field['name'].split('.')[-1].lower()  # Get base field name
                requirement = field['ao1_requirement'].split(' - ')[0]  # Get REQ-X
                
                if keyword not in keyword_locations:
                    keyword_locations[keyword] = []
                
                keyword_locations[keyword].append({
                    'dataset': dataset_id,
                    'table': table_id, 
                    'field_path': field['full_path'],
                    'requirement': requirement,
                    'purpose': field['ao1_purpose']
                })
                
                if requirement not in requirement_keywords:
                    requirement_keywords[requirement] = set()
                requirement_keywords[requirement].add(keyword)
    
    print(f"\n🎯 AO1 REQUIREMENTS COVERAGE:")
    coverage = summary['ao1_requirements_coverage']
    print(f"   Requirements covered: {len(coverage['requirements_found'])}/8 ({coverage['coverage_percentage']:.1f}%)")
    
    for req in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
        if req in coverage['requirements_found']:
            keywords_for_req = sorted(requirement_keywords.get(req, []))
            print(f"   ✅ {req}: {len(keywords_for_req)} keywords found: {', '.join(keywords_for_req[:5])}{'...' if len(keywords_for_req) > 5 else ''}")
        else:
            print(f"   ❌ {req}: NO KEYWORDS FOUND")
    
    print(f"\n🔑 TOP AO1 KEYWORDS BY LOCATION COUNT:")
    # Sort keywords by how many locations they appear in
    keyword_counts = [(kw, len(locs)) for kw, locs in keyword_locations.items()]
    keyword_counts.sort(key=lambda x: x[1], reverse=True)
    
    for i, (keyword, count) in enumerate(keyword_counts[:15], 1):
        locations = keyword_locations[keyword]
        datasets = set(loc['dataset'] for loc in locations)
        requirements = set(loc['requirement'] for loc in locations)
        print(f"   {i:2d}. '{keyword}': {count} locations, {len(datasets)} datasets, {', '.join(sorted(requirements))}")
    
    print(f"\n📍 DETAILED KEYWORD-TO-LOCATION MAPPING:")
    
    # Group by requirement for organized display
    for req in sorted(requirement_keywords.keys()):
        req_keywords = sorted(requirement_keywords[req])
        print(f"\n   📋 {req} KEYWORDS ({len(req_keywords)} found):")
        
        for keyword in req_keywords[:10]:  # Show top 10 keywords per requirement
            locations = keyword_locations[keyword]
            req_locations = [loc for loc in locations if loc['requirement'] == req]
            
            print(f"      🔑 '{keyword}':")
            for loc in req_locations[:3]:  # Show first 3 locations
                print(f"         📁 {loc['dataset']}.{loc['table']} → {loc['field_path']}")
            if len(req_locations) > 3:
                print(f"         ... and {len(req_locations) - 3} more locations")
    
    print(f"\n🏆 BEST DATASETS FOR AO1 VISIBILITY CALCULATIONS:")
    # Identify datasets with the most diverse AO1 keyword coverage
    dataset_analysis = {}
    
    for dataset_id, dataset_info in ao1_structure['datasets'].items():
        if dataset_info['ao1_summary']['total_ao1_fields'] > 0:
            keywords_in_dataset = set()
            requirements_in_dataset = set()
            tables_with_keywords = []
            
            for table_id, table_info in dataset_info['tables'].items():
                table_keywords = []
                for field in table_info.get('ao1_relevant_fields', []):
                    keyword = field['name'].split('.')[-1].lower()
                    requirement = field['ao1_requirement'].split(' - ')[0]
                    keywords_in_dataset.add(keyword)
                    requirements_in_dataset.add(requirement)
                    table_keywords.append(keyword)
                
                if table_keywords:
                    tables_with_keywords.append((table_id, table_keywords))
            
            dataset_analysis[dataset_id] = {
                'unique_keywords': len(keywords_in_dataset),
                'requirements_covered': len(requirements_in_dataset),
                'tables_with_keywords': tables_with_keywords,
                'keywords': sorted(keywords_in_dataset),
                'requirements': sorted(requirements_in_dataset)
            }
    
    # Sort by keyword diversity and requirement coverage
    best_datasets = sorted(dataset_analysis.items(), 
                          key=lambda x: (x[1]['requirements_covered'], x[1]['unique_keywords']), 
                          reverse=True)
    
    for i, (dataset_id, analysis) in enumerate(best_datasets[:10], 1):
        print(f"   {i:2d}. 📁 {dataset_id}:")
        print(f"       Requirements: {', '.join(analysis['requirements'])} ({analysis['requirements_covered']}/8)")
        print(f"       Keywords: {', '.join(analysis['keywords'][:8])}{'...' if len(analysis['keywords']) > 8 else ''} ({analysis['unique_keywords']} total)")
        print(f"       Best tables: {', '.join([t[0] for t in analysis['tables_with_keywords'][:3]])}")
    
    if summary['total_ao1_fields_found'] > 0:
        print(f"\n✅ AO1 KEYWORD DISCOVERY SUCCESS:")
        print(f"   🎯 Found {len(keyword_locations)} unique AO1 keywords")
        print(f"   📊 Covering {len(coverage['requirements_found'])}/8 AO1 requirements")
        print(f"   📁 Distributed across {len([d for d in ao1_structure['datasets'].values() if d['ao1_summary']['total_ao1_fields'] > 0])} datasets")
        
        # Identify the most valuable keywords for each requirement
        print(f"\n💎 MOST VALUABLE KEYWORDS BY REQUIREMENT:")
        for req in sorted(requirement_keywords.keys()):
            req_keywords = [(kw, len(keyword_locations[kw])) for kw in requirement_keywords[req]]
            req_keywords.sort(key=lambda x: x[1], reverse=True)
            top_keyword = req_keywords[0] if req_keywords else None
            if top_keyword:
                print(f"   {req}: '{top_keyword[0]}' ({top_keyword[1]} locations)")
        
    else:
        print(f"\n❌ NO AO1 KEYWORDS FOUND:")
        print(f"   No AO1-relevant field names found in {summary['total_tables_analyzed']} tables")
        print(f"   Consider:")
        print(f"   • Checking field naming conventions vs AO1 dictionary")
        print(f"   • Expanding keyword variations in dictionary")
        print(f"   • Verifying data source ingestion")
    
    return f"AO1 Keyword Mapping: {len(keyword_locations)} unique keywords found across {summary['total_datasets_analyzed']} datasets"

def save_complete_ao1_results(ao1_structure, filename="complete_ao1_bq_exploration.json"):
    """Save complete AO1-focused results to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(ao1_structure, f, indent=2, default=str)
        logger.info(f"\n💾 Complete AO1 results saved to: {filename}")
        print(f"📁 Full complete AO1 analysis saved to: {filename}")
        
        # Also save a comprehensive summary CSV
        summary_filename = filename.replace('.json', '_complete_summary.csv')
        save_complete_ao1_summary_csv(ao1_structure, summary_filename)
        
        # Save requirements coverage report
        coverage_filename = filename.replace('.json', '_requirements_coverage.json')
        save_ao1_requirements_report(ao1_structure, coverage_filename)
        
    except Exception as e:
        logger.error(f"Error saving complete AO1 results to file: {e}")

def save_complete_ao1_summary_csv(ao1_structure, filename):
    """Save complete AO1 keyword-to-location mapping as CSV"""
    try:
        ao1_findings = []
        
        for dataset_id, dataset_info in ao1_structure['datasets'].items():
            for table_id, table_info in dataset_info['tables'].items():
                for field in table_info.get('ao1_relevant_fields', []):
                    ao1_findings.append({
                        'dataset': dataset_id,
                        'table': table_id,
                        'field_name': field['name'],
                        'field_path': field['full_path'],
                        'field_type': field['type'],
                        'ao1_keyword': field['name'].split('.')[-1].lower(),
                        'ao1_requirement': field['ao1_requirement'].split(' - ')[0],
                        'ao1_requirement_full': field['ao1_requirement'],
                        'ao1_category': field['ao1_category'],
                        'ao1_vendors': ', '.join(field['ao1_vendors']),
                        'ao1_purpose': field['ao1_purpose'],
                        'location_key': f"{dataset_id}.{table_id}.{field['name']}",
                        'table_rows': table_info.get('table_info', {}).get('num_rows', 0),
                        'table_size_bytes': table_info.get('table_info', {}).get('size_bytes', 0)
                    })
        
        if ao1_findings:
            df = pd.DataFrame(ao1_findings)
            # Sort by requirement, then by keyword, then by dataset
            df = df.sort_values(['ao1_requirement', 'ao1_keyword', 'dataset', 'table'])
            df.to_csv(filename, index=False)
            logger.info(f"📊 Complete AO1 keyword mapping CSV saved: {filename}")
            print(f"📊 Complete AO1 keyword-to-location mapping saved to: {filename}")
            
            # Also create a summary by keyword
            keyword_summary_filename = filename.replace('_complete_summary.csv', '_keyword_summary.csv')
            keyword_summary = df.groupby(['ao1_keyword', 'ao1_requirement']).agg({
                'dataset': 'count',
                'location_key': lambda x: '; '.join(x.head(5).tolist()) + ('...' if len(x) > 5 else ''),
                'ao1_purpose': 'first'
            }).reset_index()
            keyword_summary.columns = ['ao1_keyword', 'ao1_requirement', 'location_count', 'sample_locations', 'ao1_purpose']
            keyword_summary = keyword_summary.sort_values(['ao1_requirement', 'location_count'], ascending=[True, False])
            keyword_summary.to_csv(keyword_summary_filename, index=False)
            print(f"📈 AO1 keyword frequency summary saved to: {keyword_summary_filename}")
        
    except Exception as e:
        logger.error(f"Error saving complete AO1 CSV summary: {e}")

def save_ao1_requirements_report(ao1_structure, filename):
    """Save detailed AO1 requirements coverage report"""
    try:
        # Build detailed requirements analysis
        requirements_analysis = {}
        
        for req_id in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
            requirements_analysis[req_id] = {
                'keywords_found': [],
                'total_locations': 0,
                'datasets_with_data': [],
                'best_tables': [],
                'coverage_status': 'MISSING'
            }
        
        # Analyze each dataset and table for requirement coverage
        for dataset_id, dataset_info in ao1_structure['datasets'].items():
            for table_id, table_info in dataset_info['tables'].items():
                for field in table_info.get('ao1_relevant_fields', []):
                    req_id = field['ao1_requirement'].split(' - ')[0]
                    keyword = field['name'].split('.')[-1].lower()
                    
                    if req_id in requirements_analysis:
                        requirements_analysis[req_id]['coverage_status'] = 'FOUND'
                        requirements_analysis[req_id]['total_locations'] += 1
                        
                        if keyword not in requirements_analysis[req_id]['keywords_found']:
                            requirements_analysis[req_id]['keywords_found'].append(keyword)
                        
                        if dataset_id not in requirements_analysis[req_id]['datasets_with_data']:
                            requirements_analysis[req_id]['datasets_with_data'].append(dataset_id)
                        
                        table_key = f"{dataset_id}.{table_id}"
                        if table_key not in [t['table'] for t in requirements_analysis[req_id]['best_tables']]:
                            requirements_analysis[req_id]['best_tables'].append({
                                'table': table_key,
                                'keywords': [keyword],
                                'field_path': field['full_path']
                            })
                        else:
                            # Add keyword to existing table entry
                            for table_entry in requirements_analysis[req_id]['best_tables']:
                                if table_entry['table'] == table_key:
                                    if keyword not in table_entry['keywords']:
                                        table_entry['keywords'].append(keyword)
        
        # Save detailed analysis
        with open(filename, 'w') as f:
            json.dump(requirements_analysis, f, indent=2, default=str)
        
        logger.info(f"📋 AO1 requirements coverage report saved: {filename}")
        print(f"📋 Detailed AO1 requirements analysis saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error saving AO1 requirements report: {e}")