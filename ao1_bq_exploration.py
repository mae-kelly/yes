"""
AO1-Focused BigQuery Exploration Script - EXACT MATCHES ONLY

This script connects to BigQuery with identical authentication to the original script
and scans every dataset and table to identify AO1-relevant fields using EXACT keyword matches only.
No loose associations or substring matching.
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

# Import the AO1 Keywords Dictionary - MODIFIED to use exact matches from our consolidated module
try:
    # Import our consolidated AO1 keywords (update this import to match your keyword module)
    from ao1_keywords import (
        REQ1_GLOBAL_VIEW_KEYWORDS,
        REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
        REQ3_REGIONAL_COUNTRY_KEYWORDS,
        REQ4_BUSINESS_APPLICATION_KEYWORDS,
        REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
        REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
        REQ7_LOGGING_COMPLIANCE_KEYWORDS,
        REQ8_DOMAIN_VISIBILITY_KEYWORDS,
        get_all_keywords,
        find_keyword_requirement
    )
    
    # Create consolidated keyword set for exact matching
    ALL_AO1_KEYWORDS = get_all_keywords()
    
    print("Successfully imported AO1 Keywords Dictionary")
    print("Total keywords loaded: {}".format(len(ALL_AO1_KEYWORDS)))
    
    # Test the import by showing a few sample keywords
    sample_keywords = list(ALL_AO1_KEYWORDS)[:5]
    print("Sample keywords: {}".format(sample_keywords))
    
    # Test a keyword lookup
    test_keyword = 'hostname'
    if test_keyword in ALL_AO1_KEYWORDS:
        test_result = find_keyword_requirement(test_keyword)
        print("Test lookup for '{}': {}".format(test_keyword, test_result))
    
except ImportError as e:
    print("ERROR: Cannot import AO1 Keywords Dictionary: {}".format(e))
    print("Make sure the AO1 keywords module is in the same directory")
    sys.exit(1)
except Exception as e:
    print("ERROR: Problem with AO1 Keywords Dictionary: {}".format(e))
    sys.exit(1)

# File path and settings - identical to original script
file_path = os.path.join(os.path.dirname(__file__))
settings = {}

# Logging setup - identical to original script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ao1_bq_exploration_exact.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def authenticate_bigquery():
    """Authentication identical to original script"""
    SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcp_prod_key.json")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    settings['KATANA_PG'] = {'client_encoding': 'utf8'}
    project = "prj-fisv-p-gcss-sas-d19dd0f1df"
    client = bigquery.Client(project=project, credentials=credentials)
    logger.info("Successfully authenticated with BigQuery")
    return client

def get_all_datasets(client):
    """Get all datasets - identical to original script"""
    try:
        datasets = list(client.list_datasets())
        logger.info("Found {} datasets".format(len(datasets)))
        return [dataset.dataset_id for dataset in datasets]
    except Forbidden as e:
        logger.error("Permission denied listing datasets: {}".format(e))
        return []
    except NotFound as e:
        logger.error("Project not found: {}".format(e))
        return []
    except Exception as e:
        logger.error("Unexpected error listing datasets: {}".format(e))
        return []

def get_all_tables(client, dataset_id):
    """Get all tables in dataset - identical to original script"""
    try:
        tables = list(client.list_tables(dataset_id))
        logger.info("Found {} tables in dataset '{}'".format(len(tables), dataset_id))
        return [table.table_id for table in tables]
    except Forbidden as e:
        logger.error("Permission denied accessing dataset '{}': {}".format(dataset_id, e))
        return []
    except NotFound as e:
        logger.error("Dataset '{}' not found: {}".format(dataset_id, e))
        return []
    except BadRequest as e:
        logger.warning("Bad request accessing dataset '{}': {}".format(dataset_id, e))
        return []
    except ServerError as e:
        logger.error("Server error accessing dataset '{}': {}".format(dataset_id, e))
        return []
    except Exception as e:
        logger.error("Unexpected error accessing dataset '{}': {}".format(dataset_id, e))
        return []

def is_ao1_relevant_field(field_name):
    """
    Check if a field name is relevant to AO1 requirements using EXACT MATCHES ONLY.
    No substring matching or loose associations.
    """
    if not field_name:
        return False
        
    # Clean the field name and check for exact match
    field_lower = field_name.lower().strip()
    
    # EXACT MATCH ONLY - check if field name exactly matches any AO1 keyword
    if field_lower in ALL_AO1_KEYWORDS:
        logger.info("EXACT MATCH: Field '{}' matches AO1 keyword '{}'".format(field_name, field_lower))
        return True
    
    # No match found
    logger.debug("NO EXACT MATCH: Field '{}' not found in AO1 keywords".format(field_name))
    return False

def categorize_ao1_field(field_name):
    """Categorize an AO1-relevant field by requirement using EXACT MATCHES ONLY"""
    if not field_name:
        return {
            'category': 'unknown', 
            'requirement': 'No requirement', 
            'vendors': [], 
            'context': 'Invalid field name'
        }
    
    field_lower = field_name.lower().strip()
    
    # Only proceed if exact match exists
    if field_lower not in ALL_AO1_KEYWORDS:
        logger.warning("NO EXACT MATCH: Field '{}' not found in AO1 keywords".format(field_name))
        return {
            'category': 'unknown', 
            'requirement': 'No AO1 requirement mapping identified', 
            'vendors': [], 
            'context': 'Field not an exact match to any AO1 keyword'
        }
    
    # Find which requirements contain this exact keyword
    requirements = find_keyword_requirement(field_lower)
    
    if requirements:
        # Use the first requirement if multiple found
        primary_requirement = requirements[0]
        
        # Extract vendors and category info based on the requirement
        vendors = []
        category = 'general'
        context = "Exact match to AO1 keyword"
        
        if 'REQ-6' in primary_requirement:
            # Security control coverage - identify vendors
            if any(vendor in field_lower for vendor in ['crowdstrike', 'falcon']):
                vendors = ['CrowdStrike']
            elif 'tanium' in field_lower:
                vendors = ['Tanium']
            elif 'dlp' in field_lower:
                vendors = ['DLP']
            elif 'axonius' in field_lower:
                vendors = ['Axonius']
            category = 'security_control'
            
        elif 'REQ-7' in primary_requirement:
            # Logging platforms
            if 'splunk' in field_lower:
                vendors = ['Splunk']
            elif any(chronicle in field_lower for chronicle in ['chronicle', 'gso']):
                vendors = ['Google Chronicle']
            category = 'logging_platform'
            
        elif 'REQ-2' in primary_requirement:
            # Infrastructure type
            if any(cloud in field_lower for cloud in ['aws', 'azure', 'gcp']):
                vendors = ['Cloud']
            category = 'infrastructure'
            
        elif 'REQ-5' in primary_requirement:
            # System classification
            if any(os in field_lower for os in ['windows', 'linux', 'unix']):
                vendors = ['Operating System']
            category = 'system_type'
        
        result = {
            'category': category,
            'requirement': primary_requirement,
            'vendors': vendors,
            'context': context
        }
        
        logger.info("EXACT CATEGORIZATION: Field '{}' -> {}".format(field_name, primary_requirement))
        return result
    
    # This shouldn't happen if the field was found in ALL_AO1_KEYWORDS
    logger.error("CATEGORIZATION ERROR: Field '{}' found in keywords but no requirements returned".format(field_name))
    return {
        'category': 'error', 
        'requirement': 'Categorization error', 
        'vendors': [], 
        'context': 'Internal error in categorization'
    }

def test_ao1_keyword_detection():
    """Test AO1 keyword detection with sample field names using EXACT MATCHES ONLY"""
    print("Testing AO1 EXACT keyword detection...")
    
    # Test with some exact AO1 keywords that should match
    test_fields = [
        'hostname', 'host_name', 'computer_name', 'aid', 'business_unit', 
        'aws_region', 'sourcetype', 'ip_address', 'domain_name', 'application',
        'windows', 'linux', 'edr', 'crowdstrike', 'tanium', 'office365',
        # Test some fields that should NOT match (not exact AO1 keywords)
        'custom_hostname_field', 'hostname_backup', 'my_computer_name'
    ]
    
    exact_matches_found = 0
    for field in test_fields:
        is_relevant = is_ao1_relevant_field(field)
        if is_relevant:
            context = categorize_ao1_field(field)
            print("  EXACT MATCH: '{}' -> {}".format(field, context['requirement']))
            exact_matches_found += 1
        else:
            print("  NO EXACT MATCH: '{}'".format(field))
    
    print("Test completed: {}/{} fields had EXACT matches to AO1 keywords".format(exact_matches_found, len(test_fields)))
    
    if exact_matches_found == 0:
        print("WARNING: No test fields had exact matches - there may be an issue with keyword detection")
        return False
    
    return True

def get_table_schema_ao1_focused(client, dataset_id, table_id):
    """Get table schema and identify ONLY AO1-relevant fields using EXACT MATCHES"""
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        
        ao1_relevant_fields = []
        total_fields = 0
        
        def analyze_field(field, parent_name=""):
            """Recursively analyze fields including nested structures using EXACT MATCHES ONLY"""
            nonlocal total_fields
            
            current_field_name = "{}.{}".format(parent_name, field.name) if parent_name else field.name
            total_fields += 1
            
            field_info = None
            
            # EXACT MATCH CHECK ONLY
            if is_ao1_relevant_field(field.name):
                ao1_context = categorize_ao1_field(field.name)
                field_info = {
                    'name': current_field_name,
                    'base_field_name': field.name,  # Store the actual field name that matched
                    'type': field.field_type,
                    'mode': field.mode,
                    'ao1_requirement': ao1_context['requirement'],
                    'ao1_category': ao1_context['category'],
                    'ao1_vendors': ao1_context['vendors'],
                    'ao1_purpose': ao1_context['context'],
                    'full_path': current_field_name,
                    'match_type': 'EXACT'  # Indicate this was an exact match
                }
                
                logger.info("    AO1 EXACT MATCH FOUND: {} -> {}".format(current_field_name, ao1_context['requirement']))
            
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
        
        logger.info("  Table {}.{}: {} AO1 EXACT MATCHES found out of {} total fields".format(
            dataset_id, table_id, len(ao1_relevant_fields), total_fields))
        
        return {
            'ao1_relevant_fields': ao1_relevant_fields,
            'total_fields': total_fields,
            'ao1_coverage_percentage': (len(ao1_relevant_fields) / total_fields * 100) if total_fields > 0 else 0,
            'match_strategy': 'EXACT_ONLY',
            'table_info': {
                'num_rows': table.num_rows if table.num_rows else 0,
                'created': table.created.isoformat() if table.created else None,
                'modified': table.modified.isoformat() if table.modified else None,
                'size_bytes': table.num_bytes if table.num_bytes else 0,
                'table_type': getattr(table, 'table_type', 'TABLE')
            }
        }
        
    except Forbidden as e:
        logger.warning("Permission denied accessing table schema for {}.{}: {}".format(dataset_id, table_id, e))
        return {'ao1_relevant_fields': [], 'total_fields': 0, 'ao1_coverage_percentage': 0, 'error': 'Permission denied'}
    except NotFound as e:
        logger.warning("Table {}.{} not found: {}".format(dataset_id, table_id, e))
        return {'ao1_relevant_fields': [], 'total_fields': 0, 'ao1_coverage_percentage': 0, 'error': 'Table not found'}
    except Exception as e:
        logger.error("Error analyzing AO1 relevance for table {}.{}: {}".format(dataset_id, table_id, e))
        return {'ao1_relevant_fields': [], 'total_fields': 0, 'ao1_coverage_percentage': 0, 'error': str(e)}

def explore_complete_ao1_project_structure(client):
    """Complete exploration of ALL BigQuery datasets and tables for AO1 fields using EXACT MATCHES ONLY"""
    start_time = time.time()
    
    ao1_project_structure = {
        'exploration_timestamp': datetime.now().isoformat(),
        'exploration_config': {
            'scan_type': 'COMPLETE_COMPREHENSIVE_SCAN',
            'ao1_focus': True,
            'match_strategy': 'EXACT_MATCHES_ONLY',
            'limits': 'NONE - All datasets and tables analyzed',
            'note': 'Only exact keyword matches counted - no substring or loose matching'
        },
        'ao1_summary': {
            'total_datasets_found': 0,
            'total_datasets_analyzed': 0,
            'total_tables_found': 0,
            'total_tables_analyzed': 0,
            'tables_with_ao1_fields': 0,
            'total_ao1_exact_matches': 0,
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
    
    logger.info("Starting COMPLETE AO1-focused BigQuery exploration with EXACT MATCHES ONLY...")
    logger.info("This will scan EVERY dataset and EVERY table for EXACT AO1 keyword matches")
    
    try:
        # Get ALL datasets
        datasets = get_all_datasets(client)
        if not datasets:
            logger.error("No datasets found or permission denied")
            ao1_project_structure['ao1_summary']['errors'].append("No datasets accessible")
            return ao1_project_structure
        
        ao1_project_structure['ao1_summary']['total_datasets_found'] = len(datasets)
        logger.info("Found {} datasets to analyze for EXACT matches".format(len(datasets)))
        
        dataset_count = 0
        for dataset_id in datasets:
            dataset_count += 1
            logger.info("Dataset {}/{}: {}".format(dataset_count, len(datasets), dataset_id))
            
            dataset_ao1_info = {
                'tables': {},
                'ao1_summary': {
                    'total_tables': 0,
                    'tables_analyzed': 0,
                    'tables_with_ao1_fields': 0,
                    'total_ao1_exact_matches': 0,
                    'ao1_requirements_found': set(),
                    'ao1_vendors_found': set(),
                    'errors': [],
                    'permission_errors': 0
                }
            }
            
            # Get ALL tables in this dataset
            tables = get_all_tables(client, dataset_id)
            if not tables:
                warning_msg = "No tables found in dataset {} or permission denied".format(dataset_id)
                logger.warning(warning_msg)
                dataset_ao1_info['ao1_summary']['errors'].append(warning_msg)
                ao1_project_structure['ao1_summary']['permission_errors'] += 1
                continue
            
            dataset_ao1_info['ao1_summary']['total_tables'] = len(tables)
            ao1_project_structure['ao1_summary']['total_tables_found'] += len(tables)
            
            table_count = 0
            for table_id in tables:
                table_count += 1
                logger.info("  Table {}/{}: {}".format(table_count, len(tables), table_id))
                
                # Get AO1-relevant schema information for THIS table (EXACT MATCHES ONLY)
                table_ao1_analysis = get_table_schema_ao1_focused(client, dataset_id, table_id)
                dataset_ao1_info['ao1_summary']['tables_analyzed'] += 1
                ao1_project_structure['ao1_summary']['total_tables_analyzed'] += 1
                
                if 'error' in table_ao1_analysis:
                    dataset_ao1_info['ao1_summary']['permission_errors'] += 1
                    ao1_project_structure['ao1_summary']['permission_errors'] += 1
                    error_msg = "{}.{}: {}".format(dataset_id, table_id, table_ao1_analysis['error'])
                    dataset_ao1_info['ao1_summary']['errors'].append(error_msg)
                    logger.error("    {}".format(error_msg))
                
                if table_ao1_analysis['ao1_relevant_fields']:
                    dataset_ao1_info['ao1_summary']['tables_with_ao1_fields'] += 1
                    dataset_ao1_info['ao1_summary']['total_ao1_exact_matches'] += len(table_ao1_analysis['ao1_relevant_fields'])
                    ao1_project_structure['ao1_summary']['tables_with_ao1_fields'] += 1
                    ao1_project_structure['ao1_summary']['total_ao1_exact_matches'] += len(table_ao1_analysis['ao1_relevant_fields'])
                    
                    # Track AO1 requirements and vendors found
                    for field in table_ao1_analysis['ao1_relevant_fields']:
                        req = field['ao1_requirement'].split(' - ')[0]  # Get REQ-X part
                        dataset_ao1_info['ao1_summary']['ao1_requirements_found'].add(req)
                        dataset_ao1_info['ao1_summary']['ao1_vendors_found'].update(field['ao1_vendors'])
                    
                    logger.info("    Found {} AO1 EXACT MATCHES".format(len(table_ao1_analysis['ao1_relevant_fields'])))
                else:
                    logger.info("    No AO1 exact matches found")
                
                dataset_ao1_info['tables'][table_id] = table_ao1_analysis
                
                # Progress indicator for large datasets
                if table_count % 50 == 0:
                    logger.info("    Progress: {}/{} tables analyzed in {}".format(table_count, len(tables), dataset_id))
            
            # Convert sets to lists for JSON serialization
            dataset_ao1_info['ao1_summary']['ao1_requirements_found'] = list(dataset_ao1_info['ao1_summary']['ao1_requirements_found'])
            dataset_ao1_info['ao1_summary']['ao1_vendors_found'] = list(dataset_ao1_info['ao1_summary']['ao1_vendors_found'])
            
            # Always include dataset info (even if no AO1 fields) for complete audit
            ao1_project_structure['datasets'][dataset_id] = dataset_ao1_info
            ao1_project_structure['ao1_summary']['total_datasets_analyzed'] += 1
            
            if dataset_ao1_info['ao1_summary']['total_ao1_exact_matches'] > 0:
                logger.info("  Dataset {}: {} AO1 EXACT MATCHES found across {} tables".format(
                    dataset_id, 
                    dataset_ao1_info['ao1_summary']['total_ao1_exact_matches'], 
                    dataset_ao1_info['ao1_summary']['tables_with_ao1_fields']
                ))
            else:
                logger.info("  Dataset {}: No AO1 exact matches found in {} tables".format(dataset_id, len(tables)))
            
            # Progress indicator for many datasets
            if dataset_count % 10 == 0:
                elapsed = time.time() - start_time
                logger.info("PROGRESS UPDATE: {}/{} datasets completed ({:.1f}s elapsed)".format(dataset_count, len(datasets), elapsed))
                logger.info("   Current totals: {} AO1 EXACT MATCHES found".format(ao1_project_structure['ao1_summary']['total_ao1_exact_matches']))
    
    except KeyboardInterrupt:
        logger.info("Complete AO1 exploration interrupted by user")
        ao1_project_structure['ao1_summary']['warnings'].append("Exploration interrupted by user")
        raise
    except Exception as e:
        error_msg = "Fatal error during complete AO1 exploration: {}".format(e)
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
    
    # Identify top AO1 datasets by exact match count
    dataset_scores = []
    for dataset_id, dataset_info in ao1_project_structure['datasets'].items():
        score = dataset_info['ao1_summary']['total_ao1_exact_matches']
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
    """Generate comprehensive AO1 summary report focusing on EXACT KEYWORD MATCHES ONLY"""
    summary = ao1_structure['ao1_summary']
    
    print("\n" + "="*100)
    print("AO1 LOG VISIBILITY MEASUREMENT - EXACT KEYWORD MATCHES ONLY")
    print("="*100)
    
    print("\nSCAN OVERVIEW:")
    print("   Match Strategy: EXACT KEYWORDS ONLY")
    print("   Duration: {:.1f} seconds".format(summary.get('exploration_duration_seconds', 0)))
    print("   Datasets analyzed: {}".format(summary['total_datasets_analyzed']))
    print("   Tables analyzed: {}".format(summary['total_tables_analyzed']))
    print("   AO1 exact matches found: {}".format(summary['total_ao1_exact_matches']))
    
    # BUILD COMPREHENSIVE EXACT KEYWORD-TO-LOCATION MAPPING
    keyword_locations = {}  # keyword -> [(dataset, table, field_path, requirement), ...]
    requirement_keywords = {}  # requirement -> [keywords...]
    
    for dataset_id, dataset_info in ao1_structure['datasets'].items():
        for table_id, table_info in dataset_info['tables'].items():
            for field in table_info.get('ao1_relevant_fields', []):
                keyword = field['base_field_name'].lower()  # Use the actual field name that matched
                requirement = field['ao1_requirement'].split(' - ')[0]  # Get REQ-X
                
                if keyword not in keyword_locations:
                    keyword_locations[keyword] = []
                
                keyword_locations[keyword].append({
                    'dataset': dataset_id,
                    'table': table_id, 
                    'field_path': field['full_path'],
                    'requirement': requirement,
                    'purpose': field['ao1_purpose'],
                    'match_type': 'EXACT'
                })
                
                if requirement not in requirement_keywords:
                    requirement_keywords[requirement] = set()
                requirement_keywords[requirement].add(keyword)
    
    print("\nAO1 REQUIREMENTS COVERAGE (EXACT MATCHES ONLY):")
    coverage = summary['ao1_requirements_coverage']
    print("   Requirements covered: {}/8 ({:.1f}%)".format(len(coverage['requirements_found']), coverage['coverage_percentage']))
    
    for req in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
        if req in coverage['requirements_found']:
            keywords_for_req = sorted(requirement_keywords.get(req, []))
            keyword_display = ', '.join(keywords_for_req[:5])
            if len(keywords_for_req) > 5:
                keyword_display += '...'
            print("   {} {}: {} exact keywords found: {}".format("FOUND", req, len(keywords_for_req), keyword_display))
        else:
            print("   {} {}: NO EXACT KEYWORDS FOUND".format("MISSING", req))
    
    print("\nTOP AO1 EXACT KEYWORDS BY LOCATION COUNT:")
    # Sort keywords by how many locations they appear in
    keyword_counts = [(kw, len(locs)) for kw, locs in keyword_locations.items()]
    keyword_counts.sort(key=lambda x: x[1], reverse=True)
    
    for i, (keyword, count) in enumerate(keyword_counts[:15], 1):
        locations = keyword_locations[keyword]
        datasets = set(loc['dataset'] for loc in locations)
        requirements = set(loc['requirement'] for loc in locations)
        print("   {:2d}. '{}': {} locations, {} datasets, {}".format(i, keyword, count, len(datasets), ', '.join(sorted(requirements))))
    
    print("\nDETAILED EXACT KEYWORD-TO-LOCATION MAPPING:")
    
    # Group by requirement for organized display
    for req in sorted(requirement_keywords.keys()):
        req_keywords = sorted(requirement_keywords[req])
        print("\n   {} EXACT KEYWORDS ({} found):".format(req, len(req_keywords)))
        
        for keyword in req_keywords[:10]:  # Show top 10 keywords per requirement
            locations = keyword_locations[keyword]
            req_locations = [loc for loc in locations if loc['requirement'] == req]
            
            print("      EXACT KEYWORD '{}':".format(keyword))
            for loc in req_locations[:3]:  # Show first 3 locations
                print("         {}.{} -> {}".format(loc['dataset'], loc['table'], loc['field_path']))
            if len(req_locations) > 3:
                print("         ... and {} more locations".format(len(req_locations) - 3))
    
    return "AO1 Exact Keyword Mapping: {} unique exact keywords found across {} datasets".format(len(keyword_locations), summary['total_datasets_analyzed'])

def save_complete_ao1_results(ao1_structure, filename="complete_ao1_bq_exploration_exact.json"):
    """Save complete AO1-focused results to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(ao1_structure, f, indent=2, default=str)
        logger.info("Complete AO1 EXACT MATCH results saved to: {}".format(filename))
        print("Full complete AO1 exact match analysis saved to: {}".format(filename))
        
        # Also save a comprehensive summary CSV
        summary_filename = filename.replace('.json', '_exact_summary.csv')
        save_complete_ao1_summary_csv(ao1_structure, summary_filename)
        
    except Exception as e:
        logger.error("Error saving complete AO1 results to file: {}".format(e))

def save_complete_ao1_summary_csv(ao1_structure, filename):
    """Save complete AO1 exact keyword-to-location mapping as CSV"""
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
                        'ao1_exact_keyword': field['base_field_name'].lower(),
                        'ao1_requirement': field['ao1_requirement'].split(' - ')[0],
                        'ao1_requirement_full': field['ao1_requirement'],
                        'ao1_category': field['ao1_category'],
                        'ao1_vendors': ', '.join(field['ao1_vendors']),
                        'ao1_purpose': field['ao1_purpose'],
                        'match_type': 'EXACT',
                        'location_key': "{}.{}.{}".format(dataset_id, table_id, field['name']),
                        'table_rows': table_info.get('table_info', {}).get('num_rows', 0),
                        'table_size_bytes': table_info.get('table_info', {}).get('size_bytes', 0)
                    })
        
        if ao1_findings:
            df = pd.DataFrame(ao1_findings)
            # Sort by requirement, then by keyword, then by dataset
            df = df.sort_values(['ao1_requirement', 'ao1_exact_keyword', 'dataset', 'table'])
            df.to_csv(filename, index=False)
            logger.info("Complete AO1 exact keyword mapping CSV saved: {}".format(filename))
            print("Complete AO1 exact keyword-to-location mapping saved to: {}".format(filename))
        
    except Exception as e:
        logger.error("Error saving complete AO1 CSV summary: {}".format(e))

def main():
    """Main AO1-focused BigQuery exploration using EXACT MATCHES ONLY"""
    print("AO1-FOCUSED BIGQUERY EXPLORATION - EXACT MATCHES ONLY")
    print("Attempting to connect to BigQuery...")
    
    try:
        # Authenticate first and test connection
        print("Authenticating with BigQuery...")
        client = authenticate_bigquery()
        print("BigQuery authentication successful!")
        
        # Test connection with a simple dataset list
        print("Testing BigQuery connection...")
        test_datasets = get_all_datasets(client)
        if not test_datasets:
            print("No datasets accessible - check permissions")
            return
        
        print("Connection verified - found {} datasets".format(len(test_datasets)))
        
        # Test AO1 EXACT keyword detection before running full scan
        print("Testing AO1 EXACT keyword detection...")
        if not test_ao1_keyword_detection():
            print("ERROR: AO1 exact keyword detection test failed")
            return
        
        print("AO1 exact keyword detection test passed - proceeding with full scan")
        
        # Run COMPLETE exploration (no user input needed)
        print("Starting COMPLETE AO1 exploration of ALL datasets and tables...")
        print("This will scan every single dataset and table for EXACT AO1 keyword matches")
        print("NO substring matching or loose associations - EXACT MATCHES ONLY")
        print("This may take several minutes to complete")
        print("Press Ctrl+C anytime to interrupt and get partial results")
        
        # Run comprehensive AO1-focused exploration with exact matching
        ao1_structure = explore_complete_ao1_project_structure(client)
        
        # Generate and display AO1 summary
        summary_result = generate_complete_ao1_summary_report(ao1_structure)
        
        # Save AO1 results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = "complete_ao1_bq_exploration_exact_{}.json".format(timestamp)
        save_complete_ao1_results(ao1_structure, filename)
        
        print("\nCOMPLETE AO1 EXACT MATCH EXPLORATION FINISHED!")
        print("Results saved to files with timestamp: {}".format(timestamp))
        print("Check the CSV files for detailed exact keyword-to-location mappings")
        
        # Show key AO1 recommendations
        total_ao1_exact_matches = ao1_structure['ao1_summary']['total_ao1_exact_matches']
        
        if total_ao1_exact_matches > 0:
            print("\nAO1 NEXT STEPS:")
            print("1. Review the {} AO1-relevant EXACT keyword matches found".format(total_ao1_exact_matches))
            print("2. Use the CSV mapping to build your visibility calculations") 
            print("3. Focus on datasets with highest exact keyword diversity")
            print("4. Address any missing AO1 requirements")
        else:
            print("\nAO1 RECOMMENDATIONS:")
            print("1. No AO1-relevant EXACT keywords found in scanned data")
            print("2. Check field naming conventions in your logging systems")
            print("3. Verify that log sources are properly ingested with standard field names")
            print("4. Consider expanding the AO1 keyword dictionary")
            print("5. Note: This scan used EXACT MATCHES ONLY - no partial matches counted")
            
    except KeyboardInterrupt:
        print("\nAO1 exploration interrupted by user")
        print("Check log file for any partial results")
        logger.info("AO1 exploration interrupted by user")
    except Exception as e:
        error_msg = "Fatal error during AO1 exploration: {}".format(e)
        print("\n{}".format(error_msg))
        logger.error(error_msg)
        print("Check ao1_bq_exploration_exact.log for detailed error information")
        
        # Print the full stack trace for debugging
        import traceback
        print("\nFULL ERROR DETAILS:")
        traceback.print_exc()
        
        sys.exit(1)

if __name__ == "__main__":
    main()