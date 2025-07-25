#!/usr/bin/env python3
"""
BigQuery Project Explorer - AO1 Metrics Mapper
Discovers all datasets, tables, columns, and maps them to AO1 Log Visibility Measurement requirements
Prioritizes larger tables and provides field recommendations for each metric
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
import re

# EXACT SAME SETUP AS ORIGINAL SCRIPT
file_path = os.path.join(os.path.dirname(__file__))
settings = {}

# AO1 Requirements Mapping
AO1_METRICS_REQUIREMENTS = {
    'network_metrics': {
        'url_fqdn_coverage': {
            'description': 'URL/FQDN coverage from web traffic logs',
            'required_log_types': ['PROXY', 'DNS', 'WAF', 'FIREWALL_TRAFFIC'],
            'key_fields': ['url', 'fqdn', 'domain', 'hostname', 'dns_query', 'http_host', 'request_url'],
            'priority': 'HIGH'
        },
        'network_cmdb_visibility': {
            'description': 'Network device visibility in CMDB',
            'required_log_types': ['FIREWALL_TRAFFIC', 'IDS_IPS', 'NDR', 'PROXY', 'DNS', 'WAF'],
            'key_fields': ['device_name', 'hostname', 'ip_address', 'network_device', 'asset_id'],
            'priority': 'HIGH'
        },
        'network_zones_coverage': {
            'description': 'Coverage across network zones/spans',
            'required_log_types': ['FIREWALL_TRAFFIC', 'IDS_IPS', 'NDR'],
            'key_fields': ['zone', 'location', 'region', 'network_segment', 'vlan', 'subnet'],
            'priority': 'MEDIUM'
        },
        'ipam_coverage': {
            'description': 'IPAM Public IP Coverage',
            'required_log_types': ['FIREWALL_TRAFFIC', 'DNS', 'PROXY'],
            'key_fields': ['public_ip', 'external_ip', 'source_ip', 'destination_ip', 'nat_ip'],
            'priority': 'HIGH'
        },
        'geolocation_coverage': {
            'description': 'Geographic distribution coverage',
            'required_log_types': ['FIREWALL_TRAFFIC', 'PROXY', 'DNS'],
            'key_fields': ['country', 'region', 'city', 'location', 'geo_location', 'geography'],
            'priority': 'MEDIUM'
        },
        'vpc_coverage': {
            'description': 'VPC network visibility',
            'required_log_types': ['GCE_INSTANCE', 'AWS_CLOUDTRAIL', 'AZURE'],
            'key_fields': ['vpc_id', 'vpc_name', 'network_id', 'virtual_network', 'cloud_network'],
            'priority': 'MEDIUM'
        },
        'log_volume_percentage': {
            'description': 'Network log ingest volume metrics',
            'required_log_types': ['FIREWALL_TRAFFIC', 'IDS_IPS', 'NDR', 'PROXY', 'DNS', 'WAF'],
            'key_fields': ['timestamp', 'log_time', 'event_time', 'collected_time', 'ingested_time'],
            'priority': 'LOW'
        }
    },
    'endpoint_metrics': {
        'endpoint_cmdb_visibility': {
            'description': 'Endpoint visibility in CMDB',
            'required_log_types': ['WINEVT_XML', 'LINUX_SYSLOG', 'EDR', 'DLP', 'FIM'],
            'key_fields': ['computer_name', 'hostname', 'device_name', 'endpoint_name', 'machine_name'],
            'priority': 'HIGH'
        },
        'crowdstrike_coverage': {
            'description': 'CrowdStrike agent coverage',
            'required_log_types': ['EDR', 'CROWDSTRIKE'],
            'key_fields': ['agent_id', 'sensor_id', 'device_id', 'crowdstrike_id', 'falcon_id'],
            'priority': 'HIGH'
        },
        'endpoint_log_volume': {
            'description': 'Endpoint log volume percentage',
            'required_log_types': ['WINEVT_XML', 'LINUX_SYSLOG', 'EDR'],
            'key_fields': ['timestamp', 'log_time', 'event_time', 'system_time'],
            'priority': 'LOW'
        }
    },
    'cloud_metrics': {
        'vpc_coverage': {
            'description': 'Cloud VPC coverage',
            'required_log_types': ['GCE_INSTANCE', 'AWS_CLOUDTRAIL', 'AZURE'],
            'key_fields': ['vpc_id', 'network_id', 'resource_id', 'instance_id'],
            'priority': 'MEDIUM'
        },
        'cloud_asset_visibility': {
            'description': 'Cloud asset visibility across platforms',
            'required_log_types': ['GCE_INSTANCE', 'AWS_CLOUDTRAIL', 'AZURE'],
            'key_fields': ['resource_name', 'instance_name', 'asset_name', 'cloud_resource'],
            'priority': 'MEDIUM'
        }
    }
}

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

def analyze_table_for_ao1_metrics(dataset_id, table_id, columns, table_info, sample_data):
    """
    Analyze a table to determine which AO1 metrics it can support
    """
    recommendations = {
        'table_priority': 'LOW',
        'suitable_metrics': [],
        'field_mappings': {},
        'confidence_scores': {},
        'row_count': table_info.get('num_rows', 0)
    }
    
    # Prioritize tables by size (more rows = higher priority)
    row_count = table_info.get('num_rows', 0)
    if row_count > 1000000:  # >1M rows
        recommendations['table_priority'] = 'HIGH'
    elif row_count > 100000:  # >100K rows
        recommendations['table_priority'] = 'MEDIUM'
    else:
        recommendations['table_priority'] = 'LOW'
    
    # Get column names for analysis
    column_names = [col['name'].lower() for col in columns]
    column_types = {col['name'].lower(): col['type'] for col in columns}
    
    # Analyze against each AO1 metric
    for category, metrics in AO1_METRICS_REQUIREMENTS.items():
        for metric_name, metric_req in metrics.items():
            confidence_score = 0
            matched_fields = []
            
            # Check for key field matches
            for required_field in metric_req['key_fields']:
                for col_name in column_names:
                    # Fuzzy matching for field names
                    if (required_field.lower() in col_name or 
                        col_name in required_field.lower() or
                        any(word in col_name for word in required_field.lower().split('_'))):
                        matched_fields.append({
                            'required': required_field,
                            'actual': col_name,
                            'type': column_types[col_name]
                        })
                        confidence_score += 10
            
            # Bonus points for table/dataset naming patterns
            table_name_lower = f"{dataset_id}.{table_id}".lower()
            
            # Network-related tables
            if category == 'network_metrics':
                if any(keyword in table_name_lower for keyword in ['firewall', 'network', 'dns', 'proxy', 'traffic', 'connection']):
                    confidence_score += 20
                if any(keyword in table_name_lower for keyword in ['security', 'log', 'event']):
                    confidence_score += 10
            
            # Endpoint-related tables  
            elif category == 'endpoint_metrics':
                if any(keyword in table_name_lower for keyword in ['endpoint', 'device', 'computer', 'host', 'workstation']):
                    confidence_score += 20
                if any(keyword in table_name_lower for keyword in ['crowdstrike', 'edr', 'agent']):
                    confidence_score += 25
            
            # Cloud-related tables
            elif category == 'cloud_metrics':
                if any(keyword in table_name_lower for keyword in ['cloud', 'gcp', 'aws', 'azure', 'instance']):
                    confidence_score += 20
                if any(keyword in table_name_lower for keyword in ['vpc', 'network', 'resource']):
                    confidence_score += 15
            
            # Check sample data for patterns (if available)
            if sample_data and not any('error' in str(row) for row in sample_data):
                for row in sample_data[:3]:  # Check first 3 rows
                    if isinstance(row, dict):
                        for key, value in row.items():
                            if key.startswith('_'):  # Skip metadata
                                continue
                            if value and str(value).strip():
                                # Look for IP addresses
                                if metric_name == 'ipam_coverage' and re.match(r'\d+\.\d+\.\d+\.\d+', str(value)):
                                    confidence_score += 5
                                # Look for URLs/domains
                                if metric_name == 'url_fqdn_coverage' and ('.' in str(value) and len(str(value)) > 5):
                                    confidence_score += 5
                                # Look for timestamps
                                if 'log_volume' in metric_name and ('timestamp' in key.lower() or 'time' in key.lower()):
                                    confidence_score += 5
            
            # Only include metrics with reasonable confidence
            if confidence_score >= 15 and matched_fields:
                recommendations['suitable_metrics'].append({
                    'category': category,
                    'metric': metric_name,
                    'description': metric_req['description'],
                    'priority': metric_req['priority'],
                    'confidence_score': confidence_score
                })
                recommendations['field_mappings'][metric_name] = matched_fields
                recommendations['confidence_scores'][metric_name] = confidence_score
    
    return recommendations

def generate_ao1_recommendations(project_structure):
    """
    Generate comprehensive AO1 implementation recommendations
    """
    recommendations = {
        'summary': {
            'total_tables_analyzed': 0,
            'high_priority_tables': 0,
            'metrics_coverage': {},
            'top_recommendations': []
        },
        'by_metric': {},
        'by_table': {},
        'implementation_guide': {}
    }
    
    all_table_recommendations = []
    
    # Analyze each table
    for dataset_id, dataset_info in project_structure['datasets'].items():
        for table_id, table_info in dataset_info['tables'].items():
            if 'columns' in table_info and table_info['columns']:
                recommendations['summary']['total_tables_analyzed'] += 1
                
                table_rec = analyze_table_for_ao1_metrics(
                    dataset_id, table_id, 
                    table_info['columns'], 
                    table_info.get('table_info', {}),
                    table_info.get('sample_data', [])
                )
                
                if table_rec['table_priority'] == 'HIGH':
                    recommendations['summary']['high_priority_tables'] += 1
                
                table_key = f"{dataset_id}.{table_id}"
                recommendations['by_table'][table_key] = table_rec
                all_table_recommendations.append((table_key, table_rec))
    
    # Sort tables by priority and row count
    all_table_recommendations.sort(key=lambda x: (
        x[1]['table_priority'] == 'HIGH',
        x[1]['table_priority'] == 'MEDIUM',
        x[1]['row_count']
    ), reverse=True)
    
    # Generate metric-specific recommendations
    for category, metrics in AO1_METRICS_REQUIREMENTS.items():
        for metric_name, metric_req in metrics.items():
            metric_recommendations = []
            
            for table_key, table_rec in all_table_recommendations:
                for suitable_metric in table_rec['suitable_metrics']:
                    if suitable_metric['metric'] == metric_name:
                        metric_recommendations.append({
                            'table': table_key,
                            'confidence': suitable_metric['confidence_score'],
                            'row_count': table_rec['row_count'],
                            'priority': table_rec['table_priority'],
                            'fields': table_rec['field_mappings'].get(metric_name, [])
                        })
            
            # Sort by confidence and row count
            metric_recommendations.sort(key=lambda x: (x['confidence'], x['row_count']), reverse=True)
            
            if metric_recommendations:
                recommendations['by_metric'][metric_name] = {
                    'description': metric_req['description'],
                    'priority': metric_req['priority'],
                    'recommended_tables': metric_recommendations[:5],  # Top 5 tables
                    'total_candidates': len(metric_recommendations)
                }
    
    # Generate top recommendations
    for table_key, table_rec in all_table_recommendations[:10]:  # Top 10 tables
        if table_rec['suitable_metrics']:
            recommendations['summary']['top_recommendations'].append({
                'table': table_key,
                'row_count': table_rec['row_count'],
                'priority': table_rec['table_priority'],
                'metrics_supported': len(table_rec['suitable_metrics']),
                'best_metrics': [m['metric'] for m in sorted(table_rec['suitable_metrics'], 
                                                           key=lambda x: x['confidence_score'], reverse=True)[:3]]
            })
    
    return recommendations
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

def sample_table_data(client, dataset_id, table_id, limit=5, timeout_seconds=60):
    """
    Get sample data from a table with strategies to ensure successful sampling
    """
    try:
        # First check if table exists and get basic info
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        
        # Handle empty tables
        if table.num_rows == 0:
            logger.info(f"Table {dataset_id}.{table_id} is empty (0 rows)")
            return [{"info": "Table is empty - no data to sample"}]
        
        # Use the same project ID format as your original script
        full_table_id = f"chronicle-fisv.{dataset_id}.{table_id}"
        
        # Strategy 1: Try simple TABLESAMPLE for large tables
        if table.num_rows and table.num_rows > 100000000:  # >100M rows
            query = f"""
            SELECT *
            FROM `{full_table_id}` TABLESAMPLE SYSTEM (0.001 PERCENT)
            LIMIT {limit}
            """
            strategy = "TABLESAMPLE"
        # Strategy 2: Use column sampling for wide tables or when we know columns
        elif len(table.schema) > 50:  # Very wide table
            # Sample only first 10 columns to avoid byte limits
            column_names = [field.name for field in table.schema[:10]]
            columns_str = ', '.join([f'`{col}`' for col in column_names])
            query = f"""
            SELECT {columns_str}
            FROM `{full_table_id}`
            LIMIT {limit}
            """
            strategy = "COLUMN_SUBSET"
        else:
            # Strategy 3: Standard sampling
            query = f"""
            SELECT *
            FROM `{full_table_id}`
            LIMIT {limit}
            """
            strategy = "STANDARD"
        
        # Configure job with more generous limits
        job_config = bigquery.QueryJobConfig()
        job_config.job_timeout_ms = timeout_seconds * 1000
        job_config.maximum_bytes_billed = 1000000000  # 1GB max (increased from 100MB)
        job_config.use_query_cache = True
        job_config.use_legacy_sql = False
        
        logger.info(f"Sampling {limit} rows from {dataset_id}.{table_id} using {strategy} strategy...")
        
        query_job = client.query(query, job_config=job_config)
        results = query_job.result(timeout=timeout_seconds)
        
        # If first strategy fails, try fallback strategies
        if not results:
            logger.info(f"First strategy failed, trying fallback for {dataset_id}.{table_id}")
            
            # Fallback 1: Just get a few key columns
            key_columns = []
            for field in table.schema[:5]:  # First 5 columns only
                if field.field_type in ['STRING', 'INTEGER', 'FLOAT', 'TIMESTAMP', 'DATE']:
                    key_columns.append(f'`{field.name}`')
            
            if key_columns:
                query = f"""
                SELECT {', '.join(key_columns)}
                FROM `{full_table_id}`
                WHERE RAND() < 0.01
                LIMIT {limit}
                """
                job_config.maximum_bytes_billed = 50000000  # Reduce to 50MB
                query_job = client.query(query, job_config=job_config)
                results = query_job.result(timeout=30)
        
        # Convert to list of dictionaries with data type handling
        sample_data = []
        row_count = 0
        
        for row in results:
            row_count += 1
            row_dict = {"_row_number": row_count, "_sampling_strategy": strategy}
            
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
                        try:
                            # Try to decode as UTF-8 first
                            row_dict[key] = value.decode('utf-8')[:200]
                        except UnicodeDecodeError:
                            row_dict[key] = f"<BYTES: {len(value)} bytes>"
                    # Handle complex nested data (arrays, structs)
                    elif isinstance(value, (list, dict)):
                        str_value = str(value)
                        if len(str_value) > 300:
                            row_dict[key] = str_value[:300] + "...[TRUNCATED]"
                        else:
                            row_dict[key] = str_value
                    # Handle very long strings
                    elif isinstance(value, str) and len(value) > 500:
                        row_dict[key] = value[:500] + "...[TRUNCATED]"
                    # Handle numbers that might be too large for JSON
                    elif isinstance(value, (int, float)):
                        if isinstance(value, float) and (value != value):  # NaN check
                            row_dict[key] = "NaN"
                        elif abs(value) > 1e15:  # Very large numbers
                            row_dict[key] = str(value)
                        else:
                            row_dict[key] = value
                    else:
                        row_dict[key] = str(value)[:500]  # Convert everything else to string, truncated
                        
                except Exception as field_error:
                    logger.warning(f"Error processing field '{key}' in {dataset_id}.{table_id}: {field_error}")
                    row_dict[key] = f"<ERROR: {str(field_error)[:100]}>"
            
            sample_data.append(row_dict)
            
            if row_count >= limit:
                break
        
        # Add query statistics if available
        if query_job.done() and sample_data:
            stats = {
                "_query_stats": {
                    "sampling_strategy": strategy,
                    "bytes_processed": query_job.total_bytes_processed or 0,
                    "bytes_billed": query_job.total_bytes_billed or 0,
                    "slot_ms": query_job.slot_millis or 0,
                    "rows_returned": len(sample_data)
                }
            }
            sample_data.insert(0, stats)
        
        if sample_data:
            logger.info(f"✅ Successfully retrieved {len(sample_data)-1} sample rows from '{dataset_id}.{table_id}' using {strategy}")
        else:
            logger.warning(f"⚠️  No data returned from '{dataset_id}.{table_id}' but query succeeded")
            return [{"warning": "Query succeeded but returned no data"}]
            
        return sample_data
        
    except Forbidden as e:
        logger.warning(f"❌ Permission denied sampling table '{dataset_id}.{table_id}': {e}")
        return [{"error": "Permission denied", "details": str(e)}]
    except NotFound as e:
        logger.warning(f"❌ Table '{dataset_id}.{table_id}' not found during sampling: {e}")
        return [{"error": "Table not found", "details": str(e)}]
    except BadRequest as e:
        # Try one more fallback for bad requests - just get first row of first few columns
        logger.warning(f"⚠️  Bad request, trying minimal sampling for '{dataset_id}.{table_id}': {e}")
        try:
            table_ref = client.dataset(dataset_id).table(table_id)
            table = client.get_table(table_ref)
            
            # Get just the first non-complex column
            simple_columns = []
            for field in table.schema[:3]:
                if field.field_type in ['STRING', 'INTEGER', 'FLOAT', 'BOOLEAN']:
                    simple_columns.append(f'`{field.name}`')
                if len(simple_columns) >= 2:  # Just get 2 columns
                    break
            
            if simple_columns:
                full_table_id = f"chronicle-fisv.{dataset_id}.{table_id}"
                query = f"SELECT {', '.join(simple_columns)} FROM `{full_table_id}` LIMIT 1"
                
                job_config = bigquery.QueryJobConfig()
                job_config.maximum_bytes_billed = 10000000  # 10MB limit
                job_config.job_timeout_ms = 15000  # 15 seconds
                
                query_job = client.query(query, job_config=job_config)
                results = query_job.result(timeout=15)
                
                sample_data = []
                for row in results:
                    row_dict = {"_minimal_sample": True}
                    for key, value in row.items():
                        row_dict[key] = str(value)[:100] if value is not None else None
                    sample_data.append(row_dict)
                
                if sample_data:
                    logger.info(f"✅ Minimal sampling successful for '{dataset_id}.{table_id}'")
                    return sample_data
                    
        except Exception as fallback_error:
            logger.error(f"❌ All sampling strategies failed for '{dataset_id}.{table_id}': {fallback_error}")
        
        return [{"error": "All sampling strategies failed", "original_error": str(e)}]
        
    except ServerError as e:
        logger.warning(f"❌ Server error sampling table '{dataset_id}.{table_id}': {e}")
        return [{"error": "Server error - table may be too large or complex", "details": str(e)}]
    except Exception as e:
        logger.error(f"❌ Unexpected error sampling table '{dataset_id}.{table_id}': {e}")
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
        
        # Generate AO1 Recommendations
        print(f"\n🎯 GENERATING AO1 METRICS RECOMMENDATIONS...")
        print("="*60)
        
        ao1_recommendations = generate_ao1_recommendations(project_structure)
        project_structure['ao1_recommendations'] = ao1_recommendations
        
        # Display key recommendations
        print(f"📊 ANALYSIS SUMMARY:")
        print(f"   • Tables Analyzed: {ao1_recommendations['summary']['total_tables_analyzed']}")
        print(f"   • High Priority Tables: {ao1_recommendations['summary']['high_priority_tables']}")
        print(f"   • Metrics with Coverage: {len(ao1_recommendations['by_metric'])}")
        
        print(f"\n🏆 TOP RECOMMENDED TABLES FOR AO1 METRICS:")
        for i, rec in enumerate(ao1_recommendations['summary']['top_recommendations'][:5], 1):
            print(f"   {i}. {rec['table']} ({rec['row_count']:,} rows)")
            print(f"      Priority: {rec['priority']} | Supports {rec['metrics_supported']} metrics")
            print(f"      Best for: {', '.join(rec['best_metrics'])}")
            print()
        
        print(f"\n📋 KEY METRIC RECOMMENDATIONS:")
        priority_metrics = ['url_fqdn_coverage', 'network_cmdb_visibility', 'endpoint_cmdb_visibility', 'crowdstrike_coverage', 'ipam_coverage']
        
        for metric in priority_metrics:
            if metric in ao1_recommendations['by_metric']:
                metric_info = ao1_recommendations['by_metric'][metric]
                print(f"\n   🎯 {metric.upper().replace('_', ' ')}")
                print(f"      Description: {metric_info['description']}")
                if metric_info['recommended_tables']:
                    best_table = metric_info['recommended_tables'][0]
                    print(f"      ✅ Best Table: {best_table['table']} ({best_table['row_count']:,} rows)")
                    print(f"      🔑 Recommended Fields:")
                    for field in best_table['fields'][:3]:
                        print(f"         • {field['actual']} ({field['type']}) -> {field['required']}")
                else:
                    print(f"      ❌ No suitable tables found")
        
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
        filename = f"bigquery_ao1_analysis_{timestamp}.json"
        save_results_to_file(project_structure, filename)
        
        # Print comprehensive summary
        stats = project_structure['statistics']
        ao1_stats = project_structure.get('ao1_recommendations', {}).get('summary', {})
        
        print("\n" + "="*80)
        print("📊 FINAL EXPLORATION & AO1 ANALYSIS SUMMARY")
        print("="*80)
        print(f"⏱️  Duration: {stats.get('exploration_duration_seconds', 0):.1f} seconds")
        print(f"📁 Datasets: {stats['total_datasets_processed']}/{stats['total_datasets_found']} processed")
        print(f"📊 Tables: {stats['total_tables_processed']}/{stats['total_tables_found']} processed")
        print(f"🔑 Total Columns: {stats['total_columns_found']:,}")
        print(f"🎯 AO1 Analysis: {ao1_stats.get('total_tables_analyzed', 0)} tables analyzed")
        print(f"🏆 High Priority Tables: {ao1_stats.get('high_priority_tables', 0)}")
        print(f"📋 Metrics with Coverage: {len(project_structure.get('ao1_recommendations', {}).get('by_metric', {}))}")
        print(f"💾 Results saved to: {filename}")
        
        print(f"\n🎯 IMPLEMENTATION PRIORITIES:")
        ao1_recs = project_structure.get('ao1_recommendations', {})
        if 'by_metric' in ao1_recs:
            priority_order = []
            for metric, info in ao1_recs['by_metric'].items():
                if info['recommended_tables']:
                    best_table = info['recommended_tables'][0]
                    priority_order.append((
                        metric, 
                        best_table['table'], 
                        best_table['row_count'],
                        best_table['confidence']
                    ))
            
            # Sort by row count (prioritize larger tables)
            priority_order.sort(key=lambda x: x[2], reverse=True)
            
            print(f"   START WITH THESE HIGH-VOLUME TABLES:")
            for i, (metric, table, rows, confidence) in enumerate(priority_order[:5], 1):
                print(f"   {i}. {table} ({rows:,} rows) -> {metric.replace('_', ' ').title()}")
        
        if project_structure.get('warnings'):
            print(f"\n⚠️  Warnings ({len(project_structure['warnings'])}):")
            for warning in project_structure['warnings'][:3]:
                print(f"   • {warning}")
        
        if project_structure.get('errors'):
            print(f"\n❌ Errors ({len(project_structure['errors'])}):")
            for error in project_structure['errors'][:2]:
                print(f"   • {error}")
        
        print("="*80)
        
        # Final success message
        if stats['total_tables_processed'] > 0:
            print("✅ AO1 Analysis completed successfully!")
            print(f"📋 Check the JSON files for complete implementation guidance")
            print(f"🚀 Prioritize tables with >1M rows for immediate AO1 metric implementation")
        else:
            print("⚠️  Analysis completed but no tables were successfully processed")
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