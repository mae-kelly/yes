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
import sqlite3

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

# Global connection state
CONNECTION_INFO = {
    'db_path': None,
    'db_type': None,  # 'duckdb' or 'sqlite'
    'table_name': None,
    'columns': {},
    'connection_method': None
}

def find_database_files():
    """Find all possible database files"""
    search_patterns = [
        "universal_cmdb.db",
        "*.db",
        "../universal_cmdb.db", 
        "../*.db",
        "../../universal_cmdb.db",
        "../../*.db",
        "server/universal_cmdb.db",
        "./server/universal_cmdb.db",
        "database/universal_cmdb.db",
        "data/universal_cmdb.db",
        "db/universal_cmdb.db"
    ]
    
    found_files = []
    for pattern in search_patterns:
        matches = glob.glob(pattern)
        for match in matches:
            if os.path.isfile(match):
                found_files.append(os.path.abspath(match))
    
    # Remove duplicates and sort by preference
    found_files = list(set(found_files))
    
    # Prioritize files with 'universal_cmdb' in name
    priority_files = [f for f in found_files if 'universal_cmdb' in f.lower()]
    other_files = [f for f in found_files if 'universal_cmdb' not in f.lower()]
    
    return priority_files + other_files

def try_duckdb_connection(db_path):
    """Try connecting with DuckDB using multiple methods"""
    methods = [
        lambda: duckdb.connect(db_path, read_only=True),
        lambda: duckdb.connect(db_path),
        lambda: duckdb.connect(f"file:{db_path}", read_only=True),
        lambda: duckdb.connect(f"file:{db_path}"),
    ]
    
    for i, method in enumerate(methods):
        try:
            conn = method()
            logger.info(f"DuckDB connection successful with method {i+1}")
            return conn, f"duckdb_method_{i+1}"
        except Exception as e:
            logger.debug(f"DuckDB method {i+1} failed: {str(e)}")
            continue
    
    return None, None

def try_sqlite_connection(db_path):
    """Try connecting with SQLite as fallback"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.info("SQLite connection successful")
        return conn, "sqlite"
    except Exception as e:
        logger.debug(f"SQLite connection failed: {str(e)}")
        return None, None

def find_cmdb_table(conn, db_type):
    """Find table containing CMDB data using multiple strategies"""
    
    if db_type.startswith('duckdb'):
        show_tables_query = "SHOW TABLES"
    else:  # sqlite
        show_tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
    
    try:
        if db_type.startswith('duckdb'):
            tables = [row[0] for row in conn.execute(show_tables_query).fetchall()]
        else:
            cursor = conn.execute(show_tables_query)
            tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found tables: {tables}")
        
        # Strategy 1: Look for exact match
        if 'universal_cmdb' in tables:
            return 'universal_cmdb'
        
        # Strategy 2: Look for tables with 'cmdb' in name
        cmdb_tables = [t for t in tables if 'cmdb' in t.lower()]
        if cmdb_tables:
            return cmdb_tables[0]
        
        # Strategy 3: Look for tables with typical CMDB columns
        for table in tables:
            try:
                if db_type.startswith('duckdb'):
                    columns = conn.execute(f'DESCRIBE "{table}"').fetchall()
                    col_names = [col[0].lower() for col in columns]
                else:
                    cursor = conn.execute(f'PRAGMA table_info("{table}")')
                    col_names = [col[1].lower() for col in cursor.fetchall()]
                
                # Check for CMDB-like column patterns
                cmdb_indicators = ['host', 'hostname', 'domain', 'infrastructure_type', 'business_unit', 'region']
                matches = sum(1 for indicator in cmdb_indicators if any(indicator in col for col in col_names))
                
                if matches >= 3:  # If at least 3 CMDB-like columns found
                    logger.info(f"Found CMDB-like table: {table} with {matches} matching columns")
                    return table
                    
            except Exception as e:
                logger.debug(f"Error checking table {table}: {str(e)}")
                continue
        
        # Strategy 4: Just use the first table if nothing else works
        if tables:
            logger.warning(f"No obvious CMDB table found, using first table: {tables[0]}")
            return tables[0]
            
    except Exception as e:
        logger.error(f"Error finding tables: {str(e)}")
        
    return None

def analyze_table_structure(conn, table_name, db_type):
    """Analyze table structure and map columns"""
    column_info = {}
    
    try:
        # Get column information
        if db_type.startswith('duckdb'):
            columns = conn.execute(f'DESCRIBE "{table_name}"').fetchall()
            for col in columns:
                column_info[col[0]] = {'type': col[1], 'nullable': col[2]}
        else:  # sqlite
            cursor = conn.execute(f'PRAGMA table_info("{table_name}")')
            for col in cursor.fetchall():
                column_info[col[1]] = {'type': col[2], 'nullable': not col[3]}
        
        logger.info(f"Table {table_name} has columns: {list(column_info.keys())}")
        
        # Create smart column mapping
        col_names_lower = [col.lower() for col in column_info.keys()]
        column_mapping = {}
        
        mapping_patterns = {
            'host': ['host', 'hostname', 'fqdn', 'server_name', 'computer_name', 'machine_name'],
            'domain': ['domain', 'dns_domain', 'ad_domain'],
            'region': ['region', 'location', 'geographic_region', 'area'],
            'country': ['country', 'nation', 'country_code'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type', 'platform'],
            'business_unit': ['business_unit', 'bu', 'business', 'department'],
            'present_in_cmdb': ['present_in_cmdb', 'cmdb_present', 'in_cmdb', 'cmdb_status', 'cmdb'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk_logging', 'splunk', 'logs_in_splunk'],
            'logging_in_gso': ['logging_in_gso', 'gso_logging', 'gso'],
            'edr_coverage': ['edr_coverage', 'crowdstrike_coverage', 'endpoint_detection', 'edr'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'tanium_agent'],
            'apm': ['apm', 'application_monitoring', 'monitoring']
        }
        
        for field, patterns in mapping_patterns.items():
            for pattern in patterns:
                for actual_col in column_info.keys():
                    if pattern.lower() in actual_col.lower():
                        column_mapping[field] = actual_col
                        break
                if field in column_mapping:
                    break
        
        logger.info(f"Column mapping: {column_mapping}")
        return column_info, column_mapping
        
    except Exception as e:
        logger.error(f"Error analyzing table structure: {str(e)}")
        return {}, {}

def establish_connection():
    """Try all strategies to establish database connection"""
    global CONNECTION_INFO
    
    if CONNECTION_INFO['db_path']:  # Already connected
        return True
    
    logger.info("Attempting to establish database connection...")
    
    db_files = find_database_files()
    logger.info(f"Found potential database files: {db_files}")
    
    for db_path in db_files:
        logger.info(f"Trying database file: {db_path}")
        
        # Try DuckDB first
        conn, method = try_duckdb_connection(db_path)
        db_type = method
        
        # If DuckDB fails, try SQLite
        if not conn:
            conn, method = try_sqlite_connection(db_path)
            db_type = method
        
        if conn:
            logger.info(f"Connected to {db_path} using {method}")
            
            # Find the CMDB table
            table_name = find_cmdb_table(conn, db_type)
            
            if table_name:
                logger.info(f"Found CMDB table: {table_name}")
                
                # Analyze table structure
                columns, column_mapping = analyze_table_structure(conn, table_name, db_type)
                
                if columns:
                    # Store connection info
                    CONNECTION_INFO = {
                        'db_path': db_path,
                        'db_type': db_type,
                        'table_name': table_name,
                        'columns': columns,
                        'column_mapping': column_mapping,
                        'connection_method': method
                    }
                    
                    # Test a basic query
                    try:
                        if db_type.startswith('duckdb'):
                            test_count = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
                        else:
                            cursor = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                            test_count = cursor.fetchone()[0]
                        
                        logger.info(f"Connection successful! Table has {test_count} rows")
                        conn.close()
                        return True
                        
                    except Exception as e:
                        logger.error(f"Test query failed: {str(e)}")
            
            conn.close()
    
    logger.error("Failed to establish any database connection")
    return False

def get_connection():
    """Get database connection using established method"""
    if not CONNECTION_INFO['db_path']:
        if not establish_connection():
            raise Exception("No database connection available")
    
    db_path = CONNECTION_INFO['db_path']
    db_type = CONNECTION_INFO['db_type']
    
    if db_type.startswith('duckdb'):
        return duckdb.connect(db_path, read_only=True)
    else:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=None):
    """Execute query with proper error handling"""
    conn = get_connection()
    try:
        if CONNECTION_INFO['db_type'].startswith('duckdb'):
            if params:
                result = conn.execute(query, params).fetchall()
            else:
                result = conn.execute(query).fetchall()
        else:  # sqlite
            cursor = conn.execute(query, params or [])
            result = cursor.fetchall()
        
        return result
    finally:
        conn.close()

def get_column_name(field_name):
    """Get actual column name for a field"""
    return CONNECTION_INFO['column_mapping'].get(field_name, field_name)

def calculate_coverage_percentage(count, total):
    return round((count / total) * 100, 2) if total > 0 else 0

@app.route('/api/health')
def health_check():
    try:
        if not establish_connection():
            raise Exception("Cannot establish database connection")
        
        table_name = CONNECTION_INFO['table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM "{table_name}"')[0][0]
        
        # Test key column detection
        detection_tests = {}
        
        for field in ['logging_in_splunk', 'present_in_cmdb', 'edr_coverage']:
            col_name = get_column_name(field)
            if col_name and col_name in CONNECTION_INFO['columns']:
                try:
                    count = execute_query(f'SELECT COUNT(*) FROM "{table_name}" WHERE LOWER("{col_name}") = ?', ['yes'])[0][0]
                    detection_tests[field] = count
                except:
                    detection_tests[field] = 'query_failed'
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'connection_info': CONNECTION_INFO,
            'total_hosts': total_hosts,
            'detection_tests': detection_tests,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'connection_attempts': CONNECTION_INFO,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/global-view')
def global_view():
    try:
        if not establish_connection():
            raise Exception("No database connection")
        
        table_name = CONNECTION_INFO['table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM "{table_name}"')[0][0]
        
        coverage = {}
        
        # Check each coverage type
        coverage_fields = {
            'splunk_logging': 'logging_in_splunk',
            'cmdb_present': 'present_in_cmdb',
            'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage',
            'apm_coverage': 'apm'
        }
        
        for coverage_name, field in coverage_fields.items():
            col_name = get_column_name(field)
            if col_name and col_name in CONNECTION_INFO['columns']:
                try:
                    # Try different detection patterns
                    if field in ['logging_in_splunk', 'present_in_cmdb']:
                        count = execute_query(f'SELECT COUNT(*) FROM "{table_name}" WHERE LOWER("{col_name}") = ?', ['yes'])[0][0]
                    elif 'coverage' in field or field == 'edr_coverage':
                        count = execute_query(f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" IS NOT NULL AND "{col_name}" != ?', [''])[0][0]
                    else:
                        count = execute_query(f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" IS NOT NULL AND "{col_name}" != ?', [''])[0][0]
                    
                    coverage[coverage_name] = {
                        'count': count,
                        'percentage': calculate_coverage_percentage(count, total_hosts)
                    }
                except Exception as e:
                    logger.error(f"Error calculating {coverage_name}: {str(e)}")
                    coverage[coverage_name] = {
                        'count': 0,
                        'percentage': 0,
                        'error': str(e)
                    }
        
        return jsonify({
            'total_hosts': total_hosts,
            'coverage': coverage,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Global view failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regional-country-view')
def regional_country_view():
    try:
        if not establish_connection():
            raise Exception("No database connection")
        
        table_name = CONNECTION_INFO['table_name']
        region_col = get_column_name('region')
        country_col = get_column_name('country')
        
        if not region_col and not country_col:
            return jsonify({'regions': {}, 'countries': {}, 'message': 'No regional data columns found'})
        
        # Simple regional analysis
        regions = defaultdict(lambda: {'total': 0})
        
        if region_col:
            region_data = execute_query(f'SELECT "{region_col}" FROM "{table_name}" WHERE "{region_col}" IS NOT NULL')
            
            for row in region_data:
                region = row[0] if row[0] else 'Unknown'
                regions[region]['total'] += 1
        
        # Convert to percentage format
        region_result = {}
        for region, data in regions.items():
            region_result[region] = {
                'total': data['total'],
                'cmdb_coverage': 0,  # Placeholder
                'splunk_coverage': 0,  # Placeholder
                'edr_coverage': 0,  # Placeholder
                'overall_coverage': 0
            }
        
        return jsonify({
            'regions': region_result,
            'countries': {}  # Placeholder
        })
        
    except Exception as e:
        logger.error(f"Regional view failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add other endpoints with similar multi-strategy approach...

if __name__ == '__main__':
    logger.info("Starting multi-strategy Flask server")
    app.run(debug=True, host='0.0.0.0', port=5000)