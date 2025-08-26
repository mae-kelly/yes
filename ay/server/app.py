#!/usr/bin/env python3
import duckdb
from flask import Flask, jsonify
from flask_cors import CORS
import re
import os
import logging
import traceback
from datetime import datetime
from collections import defaultdict
import glob

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('server_debug.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app)
logger = logging.getLogger(__name__)

# Global variables to store discovered database info
DB_PATH = None
TABLE_NAME = None
COLUMN_MAPPING = {}

def discover_database():
    """Auto-discover database file and table with CMDB data"""
    global DB_PATH, TABLE_NAME, COLUMN_MAPPING
    
    logger.info("Starting database auto-discovery...")
    
    # Search for .db files
    search_paths = [
        "*.db",
        "../*.db", 
        "../../*.db",
        "server/*.db",
        "./server/*.db"
    ]
    
    db_files = []
    for pattern in search_paths:
        db_files.extend(glob.glob(pattern))
    
    logger.info(f"Found database files: {db_files}")
    
    if not db_files:
        logger.error("No .db files found!")
        return False
    
    # Try each database file
    for db_file in db_files:
        logger.info(f"Testing database: {db_file}")
        
        try:
            conn = duckdb.connect(db_file, read_only=True)
            
            # Get all tables
            tables = conn.execute("SHOW TABLES").fetchall()
            logger.info(f"Tables in {db_file}: {[t[0] for t in tables]}")
            
            # Look for table with 'cmdb' in name
            cmdb_table = None
            for table in tables:
                table_name = table[0].lower()
                if 'cmdb' in table_name:
                    cmdb_table = table[0]
                    logger.info(f"Found CMDB table: {cmdb_table}")
                    break
            
            if not cmdb_table:
                # If no table with 'cmdb' in name, check if any table has CMDB-like columns
                for table in tables:
                    try:
                        columns = conn.execute(f"DESCRIBE {table[0]}").fetchall()
                        col_names = [col[0].lower() for col in columns]
                        
                        # Check for CMDB-like columns
                        cmdb_indicators = ['host', 'hostname', 'present_in_cmdb', 'cmdb', 'logging_in_splunk', 'edr_coverage']
                        if any(indicator in ' '.join(col_names) for indicator in cmdb_indicators):
                            cmdb_table = table[0]
                            logger.info(f"Found table with CMDB-like columns: {cmdb_table}")
                            break
                    except:
                        continue
            
            if cmdb_table:
                # Discover column mappings
                columns = conn.execute(f"DESCRIBE {cmdb_table}").fetchall()
                col_names = [col[0] for col in columns]
                
                logger.info(f"Columns in {cmdb_table}: {col_names}")
                
                # Map columns to expected names
                COLUMN_MAPPING = discover_column_mapping(col_names)
                
                DB_PATH = db_file
                TABLE_NAME = cmdb_table
                
                # Test basic query
                row_count = conn.execute(f"SELECT COUNT(*) FROM {cmdb_table}").fetchone()[0]
                logger.info(f"Successfully connected to {db_file}, table {cmdb_table}, {row_count} rows")
                
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to {db_file}: {str(e)}")
            continue
    
    logger.error("No usable database found!")
    return False

def discover_column_mapping(col_names):
    """Map actual column names to expected field names"""
    col_names_lower = [col.lower() for col in col_names]
    mapping = {}
    
    # Column mapping patterns
    patterns = {
        'host': ['host', 'hostname', 'fqdn', 'server_name', 'machine_name', 'computer_name'],
        'domain': ['domain', 'dns_domain', 'ad_domain'],
        'region': ['region', 'location', 'geographic_region', 'area', 'zone'],
        'country': ['country', 'nation', 'country_code', 'geo_country'],
        'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type', 'system_type', 'platform'],
        'business_unit': ['business_unit', 'bu', 'business', 'department', 'division'],
        'present_in_cmdb': ['present_in_cmdb', 'cmdb_present', 'in_cmdb', 'cmdb_status', 'cmdb'],
        'logging_in_splunk': ['logging_in_splunk', 'splunk_logging', 'splunk', 'logs_in_splunk'],
        'logging_in_gso': ['logging_in_gso', 'gso_logging', 'gso', 'logs_in_gso'],
        'edr_coverage': ['edr_coverage', 'crowdstrike_coverage', 'endpoint_detection', 'edr'],
        'tanium_coverage': ['tanium_coverage', 'tanium', 'tanium_agent'],
        'apm': ['apm', 'application_monitoring', 'monitoring'],
        'system_classification': ['system_classification', 'classification', 'system_class'],
        'cio': ['cio', 'owner', 'responsible', 'contact'],
        'class': ['class', 'tier', 'level'],
        'data_center': ['data_center', 'datacenter', 'dc', 'facility']
    }
    
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            for i, col_name in enumerate(col_names_lower):
                if pattern in col_name:
                    mapping[field] = col_names[i]  # Use original case
                    logger.info(f"Mapped {field} -> {col_names[i]}")
                    break
            if field in mapping:
                break
    
    return mapping

def get_db_connection():
    """Get database connection using discovered settings"""
    if not DB_PATH or not TABLE_NAME:
        raise Exception("Database not discovered. Run discovery first.")
    
    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

def get_column_name(field):
    """Get actual column name for a field"""
    return COLUMN_MAPPING.get(field, field)

def build_query(base_query, **conditions):
    """Build query using discovered table and column names"""
    query = base_query.format(table=TABLE_NAME)
    
    # Replace field names with actual column names
    for field, actual_col in COLUMN_MAPPING.items():
        query = query.replace(f"{{{field}}}", actual_col)
    
    return query

def parse_multi_values(value, delimiters=['|', ',']):
    """Parse multi-value cells by splitting on delimiters"""
    if not value or value == 'null' or str(value).lower() == 'null':
        return []
    value_str = str(value).strip()
    if not value_str:
        return []
    
    for delimiter in delimiters:
        if delimiter in value_str:
            return [v.strip() for v in value_str.split(delimiter) if v.strip() and v.strip().lower() != 'null']
    return [value_str] if value_str and value_str.lower() != 'null' else []

def extract_class_numbers(value):
    """Extract class numbers from class column"""
    if not value:
        return []
    classes = []
    parts = parse_multi_values(value, ['|'])
    for part in parts:
        matches = re.findall(r'class\s*(\d+)', part.lower())
        classes.extend([int(match) for match in matches])
    return classes

def standardize_region(region):
    """Standardize regions to North America, LATAM, EMEA, APAC"""
    if not region:
        return 'Unknown'
    
    region_lower = str(region).lower()
    if any(term in region_lower for term in ['north america', 'na', 'us', 'united states', 'canada']):
        return 'North America'
    elif any(term in region_lower for term in ['latam', 'latin america', 'south america', 'brazil', 'mexico']):
        return 'LATAM'
    elif any(term in region_lower for term in ['emea', 'europe', 'middle east', 'africa']):
        return 'EMEA'
    elif any(term in region_lower for term in ['apac', 'asia', 'pacific', 'australia', 'japan']):
        return 'APAC'
    return 'Other'

def is_valid_cio(value):
    """Check if CIO value is valid (letters only, no numbers)"""
    if not value:
        return False
    value_str = str(value).strip()
    return value_str.replace(' ', '').replace('-', '').replace('_', '').isalpha()

def calculate_coverage_percentage(count, total):
    return round((count / total) * 100, 2) if total > 0 else 0

@app.route('/api/health')
def health_check():
    try:
        if not DB_PATH:
            if not discover_database():
                raise Exception("Database discovery failed")
        
        conn = get_db_connection()
        row_count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
        
        # Test detection patterns with discovered columns
        test_results = {}
        
        # Test various detection patterns
        if get_column_name('logging_in_splunk'):
            col = get_column_name('logging_in_splunk')
            test_results['splunk_test'] = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({col}) = 'yes'").fetchone()[0]
        
        if get_column_name('present_in_cmdb'):
            col = get_column_name('present_in_cmdb')
            test_results['cmdb_test'] = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({col}) = 'yes'").fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'database_file': DB_PATH,
            'table_name': TABLE_NAME,
            'total_hosts': row_count,
            'column_mapping': COLUMN_MAPPING,
            'detection_test': test_results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/global-view')
def global_view():
    """Overall Coverage Totals"""
    try:
        if not DB_PATH and not discover_database():
            raise Exception("Database not available")
            
        conn = get_db_connection()
        
        total_hosts = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
        
        coverage = {}
        
        # Splunk logging
        if get_column_name('logging_in_splunk'):
            col = get_column_name('logging_in_splunk')
            count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({col}) = 'yes'").fetchone()[0]
            coverage['splunk_logging'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        
        # CMDB presence
        if get_column_name('present_in_cmdb'):
            col = get_column_name('present_in_cmdb')
            count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({col}) = 'yes'").fetchone()[0]
            coverage['cmdb_present'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        
        # EDR Coverage
        if get_column_name('edr_coverage'):
            col = get_column_name('edr_coverage')
            count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({col}) LIKE '%crowdstrike%' OR LOWER({col}) LIKE '%edr%'").fetchone()[0]
            coverage['edr_coverage'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        
        # Tanium coverage
        if get_column_name('tanium_coverage'):
            col = get_column_name('tanium_coverage')
            count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({col}) LIKE '%tanium%'").fetchone()[0]
            coverage['tanium_coverage'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        
        # APM coverage
        if get_column_name('apm'):
            col = get_column_name('apm')
            count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({col}) LIKE '%apm%'").fetchone()[0]
            coverage['apm_coverage'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        
        conn.close()
        
        return jsonify({
            'total_hosts': total_hosts,
            'coverage': coverage,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"global_view failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/domain-visibility')
def domain_visibility():
    """Domain Analysis"""
    try:
        if not DB_PATH and not discover_database():
            raise Exception("Database not available")
            
        conn = get_db_connection()
        
        domain_col = get_column_name('domain')
        splunk_col = get_column_name('logging_in_splunk')
        cmdb_col = get_column_name('present_in_cmdb')
        edr_col = get_column_name('edr_coverage')
        
        result = {}
        
        if domain_col:
            # 1DC domains
            dc1_total = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({domain_col}) LIKE '%1dc%'").fetchone()[0]
            dc1_splunk = 0
            dc1_cmdb = 0 
            dc1_edr = 0
            
            if splunk_col:
                dc1_splunk = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({domain_col}) LIKE '%1dc%' AND LOWER({splunk_col}) = 'yes'").fetchone()[0]
            if cmdb_col:
                dc1_cmdb = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({domain_col}) LIKE '%1dc%' AND LOWER({cmdb_col}) = 'yes'").fetchone()[0]
            if edr_col:
                dc1_edr = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({domain_col}) LIKE '%1dc%' AND LOWER({edr_col}) LIKE '%crowdstrike%'").fetchone()[0]
            
            result['1dc'] = {
                'total': dc1_total,
                'splunk_coverage': calculate_coverage_percentage(dc1_splunk, dc1_total),
                'cmdb_coverage': calculate_coverage_percentage(dc1_cmdb, dc1_total),
                'edr_coverage': calculate_coverage_percentage(dc1_edr, dc1_total),
                'overall_coverage': calculate_coverage_percentage(dc1_splunk + dc1_cmdb + dc1_edr, dc1_total * 3)
            }
            
            # FEAD domains
            fead_total = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({domain_col}) LIKE '%fead%'").fetchone()[0]
            fead_splunk = 0
            fead_cmdb = 0
            fead_edr = 0
            
            if splunk_col:
                fead_splunk = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({domain_col}) LIKE '%fead%' AND LOWER({splunk_col}) = 'yes'").fetchone()[0]
            if cmdb_col:
                fead_cmdb = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({domain_col}) LIKE '%fead%' AND LOWER({cmdb_col}) = 'yes'").fetchone()[0]
            if edr_col:
                fead_edr = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE LOWER({domain_col}) LIKE '%fead%' AND LOWER({edr_col}) LIKE '%crowdstrike%'").fetchone()[0]
            
            result['fead'] = {
                'total': fead_total,
                'splunk_coverage': calculate_coverage_percentage(fead_splunk, fead_total),
                'cmdb_coverage': calculate_coverage_percentage(fead_cmdb, fead_total),
                'edr_coverage': calculate_coverage_percentage(fead_edr, fead_total),
                'overall_coverage': calculate_coverage_percentage(fead_splunk + fead_cmdb + fead_edr, fead_total * 3)
            }
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"domain_visibility failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regional-country-view')
def regional_country_view():
    """Regional Analysis and Geographic Breakdown"""
    try:
        if not DB_PATH and not discover_database():
            raise Exception("Database not available")
            
        conn = get_db_connection()
        
        region_col = get_column_name('region')
        country_col = get_column_name('country')
        cmdb_col = get_column_name('present_in_cmdb')
        splunk_col = get_column_name('logging_in_splunk')
        edr_col = get_column_name('edr_coverage')
        
        regions = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'edr': 0})
        countries = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'edr': 0})
        
        # Build dynamic query based on available columns
        select_cols = [region_col, country_col] if region_col and country_col else [col for col in [region_col, country_col] if col]
        
        if select_cols:
            # Add coverage columns to query
            coverage_selects = []
            if cmdb_col:
                coverage_selects.append(f"CASE WHEN LOWER({cmdb_col}) = 'yes' THEN 1 ELSE 0 END as cmdb")
            if splunk_col:
                coverage_selects.append(f"CASE WHEN LOWER({splunk_col}) = 'yes' THEN 1 ELSE 0 END as splunk")
            if edr_col:
                coverage_selects.append(f"CASE WHEN LOWER({edr_col}) LIKE '%crowdstrike%' THEN 1 ELSE 0 END as edr")
            
            query_cols = select_cols + coverage_selects
            query = f"SELECT {', '.join(query_cols)} FROM {TABLE_NAME} WHERE {select_cols[0]} IS NOT NULL"
            
            regional_data = conn.execute(query).fetchall()
            
            for row in regional_data:
                region_raw = row[0] if region_col else None
                country_raw = row[1] if country_col and len(row) > 1 else None
                
                # Parse coverage values
                cmdb_val = row[len(select_cols)] if cmdb_col and len(row) > len(select_cols) else 0
                splunk_val = row[len(select_cols) + (1 if cmdb_col else 0)] if splunk_col else 0
                edr_val = row[len(select_cols) + (1 if cmdb_col else 0) + (1 if splunk_col else 0)] if edr_col else 0
                
                # Process regions
                if region_raw:
                    region_parts = parse_multi_values(region_raw, ['|', ','])
                    for region_part in region_parts:
                        std_region = standardize_region(region_part)
                        regions[std_region]['total'] += 1
                        regions[std_region]['cmdb'] += cmdb_val
                        regions[std_region]['splunk'] += splunk_val
                        regions[std_region]['edr'] += edr_val
                
                # Process countries
                if country_raw:
                    country_parts = parse_multi_values(country_raw, ['|', ','])
                    for country in country_parts:
                        countries[country]['total'] += 1
                        countries[country]['cmdb'] += cmdb_val
                        countries[country]['splunk'] += splunk_val
                        countries[country]['edr'] += edr_val
        
        # Calculate percentages
        def calculate_stats(data_dict):
            result = {}
            for key, stats in data_dict.items():
                total = stats['total']
                result[key] = {
                    'total': total,
                    'cmdb_coverage': calculate_coverage_percentage(stats['cmdb'], total),
                    'splunk_coverage': calculate_coverage_percentage(stats['splunk'], total),
                    'edr_coverage': calculate_coverage_percentage(stats['edr'], total),
                    'overall_coverage': calculate_coverage_percentage(stats['cmdb'] + stats['splunk'] + stats['edr'], total * 3)
                }
            return result
        
        conn.close()
        
        return jsonify({
            'regions': calculate_stats(regions),
            'countries': calculate_stats(dict(sorted(countries.items(), key=lambda x: x[1]['total'], reverse=True)[:20]))
        })
        
    except Exception as e:
        logger.error(f"regional_country_view failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Initialize database discovery on startup
@app.before_first_request
def initialize():
    discover_database()

if __name__ == '__main__':
    # Try to discover database on startup
    if discover_database():
        logger.info(f"Successfully discovered database: {DB_PATH}, table: {TABLE_NAME}")
    else:
        logger.warning("Database discovery failed - will retry on first request")
    
    logger.info("Starting Flask application with auto-discovery")
    app.run(debug=True, host='0.0.0.0', port=5000)