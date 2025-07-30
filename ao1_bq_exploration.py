"""
AO1 BigQuery Field Discovery Script - Clean Results Focus

This script scans BigQuery datasets to find fields relevant to AO1 requirements,
presenting results in a clean, requirement-ordered format with table size prioritization.
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

# Import AO1 Keywords
try:
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
    
    ALL_AO1_KEYWORDS = get_all_keywords()
    
    # Create requirement mapping
    REQUIREMENT_KEYWORDS = {
        'REQ-1': REQ1_GLOBAL_VIEW_KEYWORDS,
        'REQ-2': REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
        'REQ-3': REQ3_REGIONAL_COUNTRY_KEYWORDS,
        'REQ-4': REQ4_BUSINESS_APPLICATION_KEYWORDS,
        'REQ-5': REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
        'REQ-6': REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
        'REQ-7': REQ7_LOGGING_COMPLIANCE_KEYWORDS,
        'REQ-8': REQ8_DOMAIN_VISIBILITY_KEYWORDS
    }
    
    print("✓ AO1 Keywords loaded: {} total keywords".format(len(ALL_AO1_KEYWORDS)))
    
except ImportError as e:
    print("ERROR: Cannot import AO1 keywords module: {}".format(e))
    sys.exit(1)

# Setup
file_path = os.path.join(os.path.dirname(__file__))
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def authenticate_bigquery():
    """Authenticate with BigQuery"""
    SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcp_prod_key.json")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    project = "prj-fisv-p-gcss-sas-d19dd0f1df"
    client = bigquery.Client(project=project, credentials=credentials)
    return client

def get_datasets(client):
    """Get all accessible datasets"""
    try:
        return [dataset.dataset_id for dataset in client.list_datasets()]
    except Exception as e:
        print("Error accessing datasets: {}".format(e))
        return []

def get_tables(client, dataset_id):
    """Get all tables in dataset"""
    try:
        return [table.table_id for table in client.list_tables(dataset_id)]
    except Exception:
        return []

def is_exact_match(field_name):
    """Check for exact AO1 keyword match"""
    return field_name.lower().strip() in ALL_AO1_KEYWORDS

def is_partial_match(field_name):
    """Check for partial/suspected AO1 keyword match"""
    field_lower = field_name.lower().strip()
    
    # Skip if exact match
    if is_exact_match(field_name):
        return False, None
    
    # Look for partial matches
    for keyword in ALL_AO1_KEYWORDS:
        # Field contains keyword
        if keyword in field_lower and len(keyword) >= 3:
            return True, keyword
        # Keyword contains field (for shorter field names)
        if field_lower in keyword and len(field_lower) >= 3:
            return True, keyword
    
    return False, None

def get_requirement_for_keyword(keyword):
    """Get requirement for a keyword"""
    for req, keywords in REQUIREMENT_KEYWORDS.items():
        if keyword in keywords:
            return req
    return "UNKNOWN"

def get_requirement_description(req):
    """Get human-readable requirement description"""
    descriptions = {
        'REQ-1': 'Global View - Asset identifiers for counting unique logging assets vs CMDB',
        'REQ-2': 'Infrastructure Type - Deployment model classification (on-prem, cloud, SaaS)',
        'REQ-3': 'Regional/Country View - Geographic location classification',
        'REQ-4': 'Business/Application View - Organizational classification',
        'REQ-5': 'System Classification - Server function and OS type classification',
        'REQ-6': 'Security Control Coverage - Agent presence for coverage measurement',
        'REQ-7': 'Logging Compliance - GSO (Chronicle) and Splunk platform compliance',
        'REQ-8': 'Domain Visibility - Asset visibility by hostname and domain'
    }
    return descriptions.get(req, req)

def scan_table_schema(client, dataset_id, table_id):
    """Scan table schema for AO1-relevant fields"""
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        
        results = []
        
        def analyze_field(field, parent_path=""):
            field_path = "{}.{}".format(parent_path, field.name) if parent_path else field.name
            
            # Check exact match
            if is_exact_match(field.name):
                keyword = field.name.lower().strip()
                requirement = get_requirement_for_keyword(keyword)
                results.append({
                    'dataset': dataset_id,
                    'table': table_id,
                    'field_name': field.name,
                    'field_path': field_path,
                    'field_type': field.field_type,
                    'matched_keyword': keyword,
                    'requirement': requirement,
                    'match_type': 'EXACT',
                    'table_rows': table.num_rows or 0,
                    'table_size_bytes': table.num_bytes or 0
                })
            
            # Check partial match
            is_partial, matched_keyword = is_partial_match(field.name)
            if is_partial:
                requirement = get_requirement_for_keyword(matched_keyword)
                results.append({
                    'dataset': dataset_id,
                    'table': table_id,
                    'field_name': field.name,
                    'field_path': field_path,
                    'field_type': field.field_type,
                    'matched_keyword': matched_keyword,
                    'requirement': requirement,
                    'match_type': 'PARTIAL',
                    'table_rows': table.num_rows or 0,
                    'table_size_bytes': table.num_bytes or 0
                })
            
            # Recursively check nested fields
            if field.field_type in ['RECORD', 'STRUCT'] and field.fields:
                for nested_field in field.fields:
                    analyze_field(nested_field, field_path)
        
        # Analyze all top-level fields
        for field in table.schema:
            analyze_field(field)
        
        return results
        
    except Exception as e:
        return []

def scan_all_data(client):
    """Scan all datasets and tables for AO1 fields"""
    print("🔍 Scanning BigQuery for AO1-relevant fields...")
    
    all_findings = []
    datasets = get_datasets(client)
    
    total_tables = 0
    processed_tables = 0
    
    # Count total tables first
    print("📊 Counting tables...")
    for dataset_id in datasets:
        tables = get_tables(client, dataset_id)
        total_tables += len(tables)
    
    print("📋 Found {} tables across {} datasets to scan".format(total_tables, len(datasets)))
    
    # Scan all tables
    for dataset_id in datasets:
        tables = get_tables(client, dataset_id)
        
        for table_id in tables:
            processed_tables += 1
            if processed_tables % 100 == 0:
                print("   Progress: {}/{} tables processed...".format(processed_tables, total_tables))
            
            findings = scan_table_schema(client, dataset_id, table_id)
            all_findings.extend(findings)
    
    print("✅ Scan complete: {} AO1-relevant fields found".format(len(all_findings)))
    return all_findings

def generate_clean_report(findings):
    """Generate clean, requirement-ordered report"""
    print("\n" + "="*80)
    print("AO1 FIELD DISCOVERY RESULTS")
    print("="*80)
    
    if not findings:
        print("❌ No AO1-relevant fields found in any tables.")
        return
    
    # Group by requirement and match type
    by_requirement = {}
    for finding in findings:
        req = finding['requirement']
        if req not in by_requirement:
            by_requirement[req] = {'EXACT': [], 'PARTIAL': []}
        by_requirement[req][finding['match_type']].append(finding)
    
    # Sort findings by table size (rows) within each requirement
    for req in by_requirement:
        for match_type in ['EXACT', 'PARTIAL']:
            by_requirement[req][match_type].sort(key=lambda x: x['table_rows'], reverse=True)
    
    # Generate report for each requirement
    for req_num in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
        if req_num not in by_requirement:
            print("\n{}: {} ❌ NO FIELDS FOUND".format(req_num, get_requirement_description(req_num).split(' - ')[1]))
            continue
        
        req_data = by_requirement[req_num]
        exact_count = len(req_data['EXACT'])
        partial_count = len(req_data['PARTIAL'])
        
        print("\n{}: {}".format(req_num, get_requirement_description(req_num).split(' - ')[1]))
        print("   ✅ {} exact matches, 🔍 {} partial matches".format(exact_count, partial_count))
        
        # Show exact matches first
        if req_data['EXACT']:
            print("\n   📍 EXACT MATCHES (ordered by table size):")
            for i, finding in enumerate(req_data['EXACT'][:10], 1):  # Top 10
                rows_info = "{:,} rows".format(finding['table_rows']) if finding['table_rows'] > 0 else "no row data"
                print("      {}. Field '{}' from {}.{} ({})".format(
                    i, finding['field_name'], finding['dataset'], finding['table'], rows_info))
                print("         → This field exactly matches AO1 keyword '{}' and can be used for {} measurement.".format(
                    finding['matched_keyword'], req_num))
            
            if len(req_data['EXACT']) > 10:
                print("         ... and {} more exact matches".format(len(req_data['EXACT']) - 10))
        
        # Show partial matches
        if req_data['PARTIAL']:
            print("\n   🔍 PARTIAL/SUSPECTED MATCHES (ordered by table size):")
            for i, finding in enumerate(req_data['PARTIAL'][:5], 1):  # Top 5
                rows_info = "{:,} rows".format(finding['table_rows']) if finding['table_rows'] > 0 else "no row data"
                print("      {}. Field '{}' from {}.{} ({})".format(
                    i, finding['field_name'], finding['dataset'], finding['table'], rows_info))
                print("         → This field contains '{}' and could potentially be used for {} measurement.".format(
                    finding['matched_keyword'], req_num))
            
            if len(req_data['PARTIAL']) > 5:
                print("         ... and {} more partial matches".format(len(req_data['PARTIAL']) - 5))
    
    # Summary statistics  
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_exact = sum(len(req_data['EXACT']) for req_data in by_requirement.values())
    total_partial = sum(len(req_data['PARTIAL']) for req_data in by_requirement.values())
    
    print("📊 Total findings: {} exact matches, {} partial matches".format(total_exact, total_partial))
    print("📋 Requirements with data: {}/8".format(len(by_requirement)))
    
    # Top datasets by field count
    dataset_counts = {}
    for finding in findings:
        dataset = finding['dataset']
        dataset_counts[dataset] = dataset_counts.get(dataset, 0) + 1
    
    top_datasets = sorted(dataset_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print("🏆 Top datasets by AO1 field count:")
    for i, (dataset, count) in enumerate(top_datasets, 1):
        print("   {}. {}: {} fields".format(i, dataset, count))

def save_results(findings, filename="ao1_field_discovery_results.csv"):
    """Save results to CSV"""
    if not findings:
        print("No results to save.")
        return
    
    df = pd.DataFrame(findings)
    # Sort by requirement, match type (exact first), then table size
    df['req_sort'] = df['requirement'].str.extract('(\d+)').astype(int)
    df['match_sort'] = df['match_type'].map({'EXACT': 0, 'PARTIAL': 1})
    df = df.sort_values(['req_sort', 'match_sort', 'table_rows'], ascending=[True, True, False])
    
    # Clean up columns for output
    output_df = df[[
        'requirement', 'match_type', 'field_name', 'matched_keyword', 
        'dataset', 'table', 'field_path', 'field_type', 'table_rows'
    ]].copy()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = "ao1_discovery_{}.csv".format(timestamp)
    output_df.to_csv(output_filename, index=False)
    print("💾 Results saved to: {}".format(output_filename))

def main():
    """Main execution"""
    print("🚀 AO1 BigQuery Field Discovery")
    print("   Finding fields relevant to AO1 audit requirements...")
    
    try:
        # Connect to BigQuery
        print("🔐 Authenticating with BigQuery...")
        client = authenticate_bigquery()
        print("✅ Connected successfully")
        
        # Test connection
        datasets = get_datasets(client)
        if not datasets:
            print("❌ No datasets accessible")
            return
        
        print("📂 Found {} datasets to scan".format(len(datasets)))
        
        # Scan for AO1 fields
        start_time = time.time()
        findings = scan_all_data(client)
        end_time = time.time()
        
        print("⏱️  Scan completed in {:.1f} seconds".format(end_time - start_time))
        
        # Generate clean report
        generate_clean_report(findings)
        
        # Save results
        save_results(findings)
        
        print("\n🎯 NEXT STEPS:")
        if findings:
            print("   1. Review the exact matches first - these are your best AO1 indicators")
            print("   2. Investigate partial matches to confirm they represent AO1 concepts")
            print("   3. Focus on large tables (high row counts) for maximum visibility impact")
            print("   4. Use the CSV file for detailed analysis and reporting")
        else:
            print("   1. No AO1 fields found - check if field naming follows standard conventions")
            print("   2. Consider expanding the AO1 keyword dictionary")
            print("   3. Verify that logging sources are properly ingested")
        
    except KeyboardInterrupt:
        print("\n⏹️  Scan interrupted by user")
    except Exception as e:
        print("\n❌ Error during scan: {}".format(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()