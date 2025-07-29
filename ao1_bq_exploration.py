"""
AO1-Focused BigQuery Exploration Script

This script connects to BigQuery and identifies only the fields that are relevant
to AO1 Log Visibility Measurement requirements by importing and using the 
AO1 Keywords Dictionary from FILE1.

It focuses exclusively on finding fields that support the 8 AO1 requirements:
REQ-1 through REQ-8 for calculating visibility percentages.
"""

import os
import json
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import import datetime
import logging
import time
import sys
from google.cloud.exceptions import NotFound, Forbidden, BadRequest, ServerError

# Import the AO1 Keywords Dictionary from FILE1
from ao1_keywords_dictionary import (
    ALL_AO1_REQUIREMENTS_KEYWORDS,
    get_keyword_requirement_context,
    find_keywords_for_requirement,
    explain_bigquery_field_ao1_relevance
)

"""
AO1-Focused BigQuery Explorer
Connects to BigQuery and identifies ONLY fields relevant to AO1 requirements,
using the keywords dictionary to filter and categorize findings.
"""

# Set up logging for AO1-focused exploration
file_path = os.path.join(os.path.dirname(__file__))
settings = {}
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
    """Authenticate with BigQuery using service account"""
    SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcp_prod_key.json")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    settings['KATANA_PG'] = {'client_encoding': 'utf8'}
    project = "prj-fisv-p-gcss-sas-d19dd0f1df"
    client = bigquery.Client(project=project, credentials=credentials)
    logger.info("Successfully authenticated with BigQuery for AO1 exploration")
    return client

def get_all_datasets(client):
    """Get all available datasets"""
    try:
        datasets = list(client.list_datasets())
        logger.info(f"Found {len(datasets)} datasets for AO1 analysis")
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
    """Get all tables in a dataset"""
    try:
        tables = list(client.list_tables(dataset_id))
        logger.info(f"Found {len(tables)} tables in dataset '{dataset_id}'")
        return [table.table_id for table in tables]
    except Forbidden as e:
        logger.error(f"Permission denied sampling table '{dataset_id}.{table_id}': {e}")
        return []
    except NotFound as e:
        logger.error(f"Table '{dataset_id}.{table_id}' not found during sampling: {e}")
        return []
    except BadRequest as e:
        logger.warning(f"Bad request sampling table '{dataset_id}.{table_id}': {e}")
        return []
    except ServerError as e:
        logger.error(f"Server error sampling table '{dataset_id}.{table_id}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error sampling table '{dataset_id}.{table_id}': {e}")
        return []

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
    
    # Check for common field variations
    ao1_field_variations = {
        'computer_name': ['computername', 'computer_name', 'comp_name'],
        'hostname': ['host_name', 'hostname', 'host', 'servername'],
        'business_unit': ['bu', 'business_unit', 'dept', 'department'],
        'aws_region': ['awsregion', 'aws_region', 'region'],
        'ip_address': ['ipaddress', 'ip_address', 'src_ip', 'sourceip'],
        'domain_name': ['domainname', 'domain_name', 'domain'],
        'application': ['app_name', 'application', 'app', 'service_name']
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
        for ao1_keyword in ALL_AO1_REQUIREMENTS_KEYWORDS.keys():
            if ao1_keyword in field_lower or field_lower in ao1_keyword:
                context = get_keyword_requirement_context(ao1_keyword)
                break
    
    return context

def get_table_schema_ao1_focused(client, dataset_id, table_id):
    """
    Get table schema and identify only AO1-relevant fields
    
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
        
        # Analyze each field for AO1 relevance
        for field in table.schema:
            total_fields += 1
            
            if is_ao1_relevant_field(field.name):
                ao1_context = categorize_ao1_field(field.name)
                field_info = {
                    'name': field.name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'ao1_requirement': ao1_context['requirement'],
                    'ao1_category': ao1_context['category'],
                    'ao1_vendors': ao1_context['vendors'],
                    'ao1_purpose': ao1_context['context']
                }
                
                # Handle nested fields for complex types
                if field.field_type in ['RECORD', 'STRUCT'] and field.fields:
                    nested_ao1_fields = []
                    for nested_field in field.fields:
                        nested_name = f"{field.name}.{nested_field.name}"
                        if is_ao1_relevant_field(nested_field.name):
                            nested_context = categorize_ao1_field(nested_field.name)
                            nested_ao1_fields.append({
                                'name': nested_name,
                                'type': nested_field.field_type,
                                'ao1_requirement': nested_context['requirement'],
                                'ao1_purpose': nested_context['context']
                            })
                    
                    if nested_ao1_fields:
                        field_info['nested_ao1_fields'] = nested_ao1_fields
                
                ao1_relevant_fields.append(field_info)
        
        logger.info(f"Found {len(ao1_relevant_fields)} AO1-relevant fields out of {total_fields} total fields in {dataset_id}.{table_id}")
        
        return {
            'ao1_relevant_fields': ao1_relevant_fields,
            'total_fields': total_fields,
            'ao1_coverage_percentage': (len(ao1_relevant_fields) / total_fields * 100) if total_fields > 0 else 0,
            'table_info': {
                'num_rows': table.num_rows if table.num_rows else 0,
                'created': table.created.isoformat() if table.created else None,
                'modified': table.modified.isoformat() if table.modified else None,
                'size_bytes': table.num_bytes if table.num_bytes else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing AO1 relevance for table {dataset_id}.{table_id}: {e}")
        return {
            'ao1_relevant_fields': [],
            'total_fields': 0,
            'ao1_coverage_percentage': 0,
            'error': str(e)
        }

def sample_ao1_field_data(client, dataset_id, table_id, ao1_field_name, limit=5):
    """
    Sample data from AO1-relevant fields to understand content patterns
    
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
        # Escape field name for BigQuery
        escaped_field = f"`{ao1_field_name}`"
        
        query = f"""
        SELECT {escaped_field}
        FROM `{dataset_id}.{table_id}`
        WHERE {escaped_field} IS NOT NULL
        LIMIT {limit}
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        sample_values = []
        for row in results:
            value = row[0]
            if value is not None:
                # Truncate long values for display
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:100] + "..."
                sample_values.append(str_value)
        
        return sample_values
        
    except Exception as e:
        logger.warning(f"Could not sample AO1 field {ao1_field_name} from {dataset_id}.{table_id}: {e}")
        return []

def explore_ao1_project_structure(client, max_tables_per_dataset=10, max_datasets=20):
    """
    Explore BigQuery project structure focusing only on AO1-relevant fields
    
    Args:
        client: BigQuery client
        max_tables_per_dataset (int): Maximum tables to analyze per dataset
        max_datasets (int): Maximum datasets to analyze
        
    Returns:
        dict: AO1-focused project structure analysis
    """
    start_time = time.time()
    
    ao1_project_structure = {
        'exploration_timestamp': datetime.now().isoformat(),
        'exploration_config': {
            'max_datasets': max_datasets,
            'max_tables_per_dataset': max_tables_per_dataset,
            'ao1_focus': True
        },
        'ao1_summary': {
            'total_datasets_analyzed': 0,
            'total_tables_analyzed': 0,
            'tables_with_ao1_fields': 0,
            'total_ao1_fields_found': 0,
            'ao1_requirements_coverage': {},
            'top_ao1_datasets': [],
            'ao1_field_types': {}
        },
        'datasets': {}
    }
    
    logger.info("🎯 Starting AO1-focused BigQuery exploration...")
    
    try:
        # Get datasets
        datasets = get_all_datasets(client)
        if not datasets:
            logger.warning("No datasets found or permission denied")
            return ao1_project_structure
        
        # Limit datasets for focused analysis
        datasets_to_analyze = datasets[:max_datasets]
        ao1_project_structure['ao1_summary']['total_datasets_analyzed'] = len(datasets_to_analyze)
        
        for dataset_id in datasets_to_analyze:
            logger.info(f"\n📊 Analyzing dataset: {dataset_id} for AO1 relevance")
            
            dataset_ao1_info = {
                'tables': {},
                'ao1_summary': {
                    'total_tables': 0,
                    'tables_with_ao1_fields': 0,
                    'total_ao1_fields': 0,
                    'ao1_requirements_found': set(),
                    'ao1_vendors_found': set()
                }
            }
            
            # Get tables in dataset
            tables = get_all_tables(client, dataset_id)
            if not tables:
                logger.warning(f"No tables found in dataset {dataset_id}")
                continue
            
            # Limit tables per dataset
            tables_to_analyze = tables[:max_tables_per_dataset]
            dataset_ao1_info['ao1_summary']['total_tables'] = len(tables_to_analyze)
            
            for table_id in tables_to_analyze:
                logger.info(f"  🔍 Analyzing table: {table_id}")
                
                # Get AO1-relevant schema information
                table_ao1_analysis = get_table_schema_ao1_focused(client, dataset_id, table_id)
                
                if table_ao1_analysis['ao1_relevant_fields']:
                    dataset_ao1_info['ao1_summary']['tables_with_ao1_fields'] += 1
                    dataset_ao1_info['ao1_summary']['total_ao1_fields'] += len(table_ao1_analysis['ao1_relevant_fields'])
                    
                    # Track AO1 requirements and vendors found
                    for field in table_ao1_analysis['ao1_relevant_fields']:
                        req = field['ao1_requirement'].split(' - ')[0]  # Get REQ-X part
                        dataset_ao1_info['ao1_summary']['ao1_requirements_found'].add(req)
                        dataset_ao1_info['ao1_summary']['ao1_vendors_found'].update(field['ao1_vendors'])
                    
                    # Sample some AO1 field data for context
                    for field in table_ao1_analysis['ao1_relevant_fields'][:3]:  # Sample first 3 AO1 fields
                        sample_data = sample_ao1_field_data(client, dataset_id, table_id, field['name'], limit=3)
                        if sample_data:
                            field['sample_values'] = sample_data
                
                dataset_ao1_info['tables'][table_id] = table_ao1_analysis
                ao1_project_structure['ao1_summary']['total_tables_analyzed'] += 1
            
            # Convert sets to lists for JSON serialization
            dataset_ao1_info['ao1_summary']['ao1_requirements_found'] = list(dataset_ao1_info['ao1_summary']['ao1_requirements_found'])
            dataset_ao1_info['ao1_summary']['ao1_vendors_found'] = list(dataset_ao1_info['ao1_summary']['ao1_vendors_found'])
            
            # Only include datasets that have AO1-relevant data
            if dataset_ao1_info['ao1_summary']['total_ao1_fields'] > 0:
                ao1_project_structure['datasets'][dataset_id] = dataset_ao1_info
                ao1_project_structure['ao1_summary']['tables_with_ao1_fields'] += dataset_ao1_info['ao1_summary']['tables_with_ao1_fields']
                ao1_project_structure['ao1_summary']['total_ao1_fields_found'] += dataset_ao1_info['ao1_summary']['total_ao1_fields']
                
                logger.info(f"  ✅ Dataset {dataset_id}: {dataset_ao1_info['ao1_summary']['total_ao1_fields']} AO1 fields found")
            else:
                logger.info(f"  ❌ Dataset {dataset_id}: No AO1-relevant fields found")
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ AO1 exploration interrupted by user")
        raise
    except Exception as e:
        error_msg = f"Fatal error during AO1 exploration: {e}"
        logger.error(error_msg)
        ao1_project_structure['ao1_summary']['exploration_error'] = error_msg
    
    # Calculate final AO1 statistics
    end_time = time.time()
    ao1_project_structure['ao1_summary']['exploration_duration_seconds'] = round(end_time - start_time, 2)
    
    # Generate AO1 requirements coverage summary
    all_requirements = ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']
    requirements_found = set()
    
    for dataset_info in ao1_project_structure['datasets'].values():
        requirements_found.update(dataset_info['ao1_summary']['ao1_requirements_found'])
    
    ao1_project_structure['ao1_summary']['ao1_requirements_coverage'] = {
        'total_requirements': len(all_requirements),
        'requirements_found': list(requirements_found),
        'requirements_missing': list(set(all_requirements) - requirements_found),
        'coverage_percentage': (len(requirements_found) / len(all_requirements)) * 100
    }
    
    # Identify top AO1 datasets
    dataset_scores = []
    for dataset_id, dataset_info in ao1_project_structure['datasets'].items():
        score = dataset_info['ao1_summary']['total_ao1_fields']
        dataset_scores.append((dataset_id, score))
    
    dataset_scores.sort(key=lambda x: x[1], reverse=True)
    ao1_project_structure['ao1_summary']['top_ao1_datasets'] = dataset_scores[:5]
    
    return ao1_project_structure

def generate_ao1_summary_report(ao1_structure):
    """
    Generate a focused AO1 summary report
    
    Args:
        ao1_structure (dict): AO1 project structure analysis
        
    Returns:
        str: Formatted AO1 summary report
    """
    summary = ao1_structure['ao1_summary']
    
    print("\n" + "="*80)
    print("🎯 AO1 LOG VISIBILITY MEASUREMENT - BIGQUERY ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"\n📊 EXPLORATION OVERVIEW:")
    print(f"   Duration: {summary.get('exploration_duration_seconds', 0):.1f} seconds")
    print(f"   Datasets analyzed: {summary['total_datasets_analyzed']}")
    print(f"   Tables analyzed: {summary['total_tables_analyzed']}")
    print(f"   Tables with AO1 fields: {summary['tables_with_ao1_fields']}")
    print(f"   Total AO1-relevant fields found: {summary['total_ao1_fields_found']}")
    
    print(f"\n🎯 AO1 REQUIREMENTS COVERAGE:")
    coverage = summary['ao1_requirements_coverage']
    print(f"   Requirements found: {len(coverage['requirements_found'])}/8 ({coverage['coverage_percentage']:.1f}%)")
    print(f"   Found: {', '.join(coverage['requirements_found'])}")
    if coverage['requirements_missing']:
        print(f"   Missing: {', '.join(coverage['requirements_missing'])}")
    
    print(f"\n🏆 TOP AO1 DATASETS:")
    for i, (dataset_id, field_count) in enumerate(summary['top_ao1_datasets'][:5], 1):
        print(f"   {i}. {dataset_id}: {field_count} AO1 fields")
    
    if summary['total_ao1_fields_found'] > 0:
        print(f"\n✅ SUCCESS: Found {summary['total_ao1_fields_found']} AO1-relevant fields!")
        print(f"   These fields support AO1 visibility calculations.")
        print(f"   Coverage spans {len(coverage['requirements_found'])} of 8 AO1 requirements.")
    else:
        print(f"\n❌ NO AO1 DATA: No AO1-relevant fields found in analyzed datasets.")
        print(f"   Consider expanding the search scope or verifying data sources.")
    
    # Show requirement-specific findings
    print(f"\n📋 DETAILED AO1 FINDINGS BY REQUIREMENT:")
    for dataset_id, dataset_info in ao1_structure['datasets'].items():
        if dataset_info['ao1_summary']['total_ao1_fields'] > 0:
            reqs_found = dataset_info['ao1_summary']['ao1_requirements_found']
            print(f"   📁 {dataset_id}: {', '.join(reqs_found)}")
    
    return f"AO1 Analysis Complete: {summary['total_ao1_fields_found']} relevant fields found"

def save_ao1_results(ao1_structure, filename="ao1_bq_exploration.json"):
    """Save AO1-focused results to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(ao1_structure, f, indent=2, default=str)
        logger.info(f"\n💾 AO1 results saved to: {filename}")
        print(f"📁 Full AO1 analysis saved to: {filename}")
        
        # Also save a summary CSV for easy analysis
        summary_filename = filename.replace('.json', '_summary.csv')
        save_ao1_summary_csv(ao1_structure, summary_filename)
        
    except Exception as e:
        logger.error(f"Error saving AO1 results to file: {e}")

def save_ao1_summary_csv(ao1_structure, filename):
    """Save AO1 findings summary as CSV"""
    try:
        ao1_findings = []
        
        for dataset_id, dataset_info in ao1_structure['datasets'].items():
            for table_id, table_info in dataset_info['tables'].items():
                for field in table_info.get('ao1_relevant_fields', []):
                    ao1_findings.append({
                        'dataset': dataset_id,
                        'table': table_id,
                        'field_name': field['name'],
                        'field_type': field['type'],
                        'ao1_requirement': field['ao1_requirement'],
                        'ao1_category': field['ao1_category'],
                        'ao1_vendors': ', '.join(field['ao1_vendors']),
                        'sample_values': ', '.join(field.get('sample_values', [])[:3])
                    })
        
        if ao1_findings:
            df = pd.DataFrame(ao1_findings)
            df.to_csv(filename, index=False)
            logger.info(f"📊 AO1 summary CSV saved: {filename}")
            print(f"📊 AO1 field summary saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error saving AO1 CSV summary: {e}")

def main():
    """Main AO1-focused BigQuery exploration"""
    print("🚀 AO1-FOCUSED BIGQUERY EXPLORATION STARTING...")
    
    try:
        # Authenticate
        client = authenticate_bigquery()
        
        # Configuration options for AO1 exploration
        print("\n🔧 AO1 EXPLORATION CONFIGURATION:")
        print("1. Quick AO1 scan (5 datasets, 10 tables each)")
        print("2. Medium AO1 scan (20 datasets, 50 tables each)")  
        print("3. Deep AO1 scan (100 datasets, 100 tables each)")
        print("4. Custom AO1 limits")
        
        try:
            choice = input("\nSelect AO1 exploration depth (1-4): ").strip()
            
            if choice == "1":
                max_datasets, max_tables = 5, 10
            elif choice == "2":
                max_datasets, max_tables = 20, 50
            elif choice == "3":
                max_datasets, max_tables = 100, 100
            elif choice == "4":
                max_datasets = int(input("Max datasets to explore: "))
                max_tables = int(input("Max tables per dataset: "))
            else:
                print("Invalid choice, using default AO1 configuration")
                max_datasets, max_tables = 5, 10
                
        except (ValueError, KeyboardInterrupt):
            print("Using default AO1 configuration")
            max_datasets, max_tables = 5, 10
        
        print(f"\n🎯 Starting AO1 exploration with limits: {max_datasets} datasets, {max_tables} tables per dataset")
        print("⏱️ You can interrupt anytime with Ctrl+C to get partial AO1 results")
        
        # Run AO1-focused exploration
        ao1_structure = explore_ao1_project_structure(client, max_tables, max_datasets)
        
        # Generate and display AO1 summary
        summary_result = generate_ao1_summary_report(ao1_structure)
        
        # Save AO1 results
        filename = f"ao1_bq_exploration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_ao1_results(ao1_structure, filename)
        
        print(f"\n🎉 AO1 EXPLORATION COMPLETE!")
        print(f"✅ Check the log file and JSON output for detailed AO1 field mappings")
        
        # Show key AO1 recommendations
        total_ao1_fields = ao1_structure['ao1_summary']['total_ao1_fields_found']
        
        if total_ao1_fields > 0:
            print(f"\n💡 AO1 NEXT STEPS:")
            print(f"1. Review the {total_ao1_fields} AO1-relevant fields found")
            print(f"2. Map these fields to your AO1 visibility calculations")
            print(f"3. Focus data collection on the identified AO1-supporting tables")
            print(f"4. Use the field samples to understand data quality")
        else:
            print(f"\n⚠️ AO1 RECOMMENDATIONS:")
            print(f"1. No AO1-relevant fields found in analyzed scope")
            print(f"2. Consider expanding search to more datasets/tables")
            print(f"3. Verify that logging data sources are properly ingested")
            print(f"4. Check field naming conventions against AO1 keyword dictionary")
            
    except KeyboardInterrupt:
        print("\n⚠️ AO1 exploration interrupted by user")
        logger.info("AO1 exploration interrupted by user")
    except Exception as e:
        error_msg = f"Fatal error during AO1 exploration: {e}"
        print(f"\n❌ {error_msg}")
        logger.error(error_msg)
        print("💡 Check the log file for detailed error information")
        sys.exit(1)

if __name__ == "__main__":
    main()