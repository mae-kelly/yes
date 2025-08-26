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

# Global connection state
DB_CONFIG = {
    'db_path': None,
    'full_table_name': None,  # e.g., "main.universal_cmdb" or "catalog.schema.table"
    'simple_table_name': None,  # e.g., "universal_cmdb"
    'columns': {},
    'column_mapping': {}
}

def discover_schema_structure():
    """Discover database, catalogs, schemas, and tables"""
    
    # Find database files
    search_paths = ["*.db", "../*.db", "../../*.db", "server/*.db", "./server/*.db"]
    db_files = []
    for pattern in search_paths:
        db_files.extend(glob.glob(pattern))
    
    if not db_files:
        raise Exception("No database files found")
    
    # Try each database
    for db_file in db_files:
        logger.info(f"Analyzing database: {db_file}")
        
        try:
            conn = duckdb.connect(db_file, read_only=True)
            
            # Strategy 1: Check catalogs and schemas
            try:
                catalogs = conn.execute("SHOW DATABASES").fetchall()
                logger.info(f"Available catalogs: {[c[0] for c in catalogs]}")
                
                for catalog in catalogs:
                    catalog_name = catalog[0]
                    try:
                        # Switch to catalog
                        conn.execute(f"USE {catalog_name}")
                        
                        # Check schemas
                        schemas = conn.execute("SHOW SCHEMAS").fetchall()
                        logger.info(f"Schemas in {catalog_name}: {[s[0] for s in schemas]}")
                        
                        for schema in schemas:
                            schema_name = schema[0]
                            try:
                                # Check tables in this schema
                                conn.execute(f"USE {schema_name}")
                                tables = conn.execute("SHOW TABLES").fetchall()
                                table_names = [t[0] for t in tables]
                                logger.info(f"Tables in {catalog_name}.{schema_name}: {table_names}")
                                
                                # Look for our table
                                if 'universal_cmdb' in table_names:
                                    full_name = f"{catalog_name}.{schema_name}.universal_cmdb"
                                    logger.info(f"Found table at: {full_name}")
                                    
                                    # Test the table
                                    if test_table_access(conn, full_name, 'universal_cmdb'):
                                        DB_CONFIG['db_path'] = db_file
                                        DB_CONFIG['full_table_name'] = full_name
                                        DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                                        analyze_columns(conn, full_name)
                                        conn.close()
                                        return True
                                        
                            except Exception as e:
                                logger.debug(f"Error in schema {schema_name}: {str(e)}")
                                continue
                                
                    except Exception as e:
                        logger.debug(f"Error in catalog {catalog_name}: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Catalog/schema discovery failed: {str(e)}")
            
            # Strategy 2: Try default context
            try:
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [t[0] for t in tables]
                logger.info(f"Tables in default context: {table_names}")
                
                if 'universal_cmdb' in table_names:
                    if test_table_access(conn, 'universal_cmdb', 'universal_cmdb'):
                        DB_CONFIG['db_path'] = db_file
                        DB_CONFIG['full_table_name'] = 'universal_cmdb'
                        DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                        analyze_columns(conn, 'universal_cmdb')
                        conn.close()
                        return True
                        
            except Exception as e:
                logger.debug(f"Default context failed: {str(e)}")
            
            # Strategy 3: Try information schema queries
            try:
                info_tables = conn.execute("""
                    SELECT table_catalog, table_schema, table_name 
                    FROM information_schema.tables 
                    WHERE table_name LIKE '%cmdb%'
                """).fetchall()
                
                logger.info(f"Information schema results: {info_tables}")
                
                for catalog, schema, table in info_tables:
                    if table.lower() == 'universal_cmdb':
                        full_name = f"{catalog}.{schema}.{table}"
                        if test_table_access(conn, full_name, table):
                            DB_CONFIG['db_path'] = db_file
                            DB_CONFIG['full_table_name'] = full_name
                            DB_CONFIG['simple_table_name'] = table
                            analyze_columns(conn, full_name)
                            conn.close()
                            return True
                            
            except Exception as e:
                logger.debug(f"Information schema query failed: {str(e)}")
            
            # Strategy 4: Brute force with different name variations
            name_variations = [
                'universal_cmdb',
                '"universal_cmdb"',
                'main.universal_cmdb',
                'main."universal_cmdb"',
                'memory.main.universal_cmdb',
                'temp.main.universal_cmdb'
            ]
            
            for name_var in name_variations:
                if test_table_access(conn, name_var, 'universal_cmdb'):
                    DB_CONFIG['db_path'] = db_file
                    DB_CONFIG['full_table_name'] = name_var
                    DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                    analyze_columns(conn, name_var)
                    conn.close()
                    return True
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to analyze {db_file}: {str(e)}")
            continue
    
    return False

def test_table_access(conn, table_name, simple_name):
    """Test if we can access a table"""
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        logger.info(f"Successfully accessed {table_name} with {count} rows")
        return True
    except Exception as e:
        logger.debug(f"Cannot access {table_name}: {str(e)}")
        return False

def analyze_columns(conn, table_name):
    """Analyze table columns and create mapping"""
    try:
        columns = conn.execute(f'DESCRIBE {table_name}').fetchall()
        DB_CONFIG['columns'] = {col[0]: col[1] for col in columns}
        
        logger.info(f"Table {table_name} columns: {list(DB_CONFIG['columns'].keys())}")
        
        # Create column mapping
        col_names_lower = [col.lower() for col in DB_CONFIG['columns'].keys()]
        mapping = {}
        
        mapping_patterns = {
            'host': ['host', 'hostname', 'fqdn', 'server_name'],
            'domain': ['domain', 'dns_domain', 'ad_domain'],
            'region': ['region', 'location', 'geographic_region'],
            'country': ['country', 'nation', 'country_code'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type'],
            'business_unit': ['business_unit', 'bu', 'business'],
            'present_in_cmdb': ['present_in_cmdb', 'cmdb_present', 'in_cmdb'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk_logging', 'splunk'],
            'logging_in_gso': ['logging_in_gso', 'gso_logging', 'gso'],
            'edr_coverage': ['edr_coverage', 'crowdstrike_coverage', 'edr'],
            'tanium_coverage': ['tanium_coverage', 'tanium'],
            'apm': ['apm', 'application_monitoring']
        }
        
        for field, patterns in mapping_patterns.items():
            for pattern in patterns:
                for actual_col in DB_CONFIG['columns'].keys():
                    if pattern.lower() in actual_col.lower():
                        mapping[field] = actual_col
                        break
                if field in mapping:
                    break
        
        DB_CONFIG['column_mapping'] = mapping
        logger.info(f"Column mapping: {mapping}")
        
    except Exception as e:
        logger.error(f"Error analyzing columns: {str(e)}")

def get_connection():
    """Get database connection"""
    if not DB_CONFIG['db_path']:
        if not discover_schema_structure():
            raise Exception("Cannot establish database connection")
    
    return duckdb.connect(DB_CONFIG['db_path'], read_only=True)

def execute_query(query):
    """Execute query with error handling"""
    conn = get_connection()
    try:
        result = conn.execute(query).fetchall()
        return result
    except Exception as e:
        logger.error(f"Query failed: {query}")
        logger.error(f"Error: {str(e)}")
        raise
    finally:
        conn.close()

def get_column_name(field):
    """Get mapped column name"""
    return DB_CONFIG['column_mapping'].get(field, field)

def calculate_coverage_percentage(count, total):
    return round((count / total) * 100, 2) if total > 0 else 0

@app.route('/api/debug/schema')
def debug_schema():
    """Debug endpoint to show schema discovery"""
    try:
        if not discover_schema_structure():
            return jsonify({'error': 'Schema discovery failed'})
        
        return jsonify({
            'db_config': DB_CONFIG,
            'discovery_successful': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    try:
        if not DB_CONFIG['db_path']:
            if not discover_schema_structure():
                raise Exception("Database discovery failed")
        
        table_name = DB_CONFIG['full_table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM {table_name}')[0][0]
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'db_config': DB_CONFIG,
            'total_hosts': total_hosts,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'db_config': DB_CONFIG,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/global-view')
def global_view():
    try:
        if not DB_CONFIG['db_path']:
            if not discover_schema_structure():
                raise Exception("Database not available")
        
        table_name = DB_CONFIG['full_table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM {table_name}')[0][0]
        
        coverage = {}
        
        # Test each coverage metric
        coverage_tests = {
            'splunk_logging': ('logging_in_splunk', "LOWER({col}) = 'yes'"),
            'cmdb_present': ('present_in_cmdb', "LOWER({col}) = 'yes'"),
            'edr_coverage': ('edr_coverage', "{col} IS NOT NULL AND {col} != ''"),
            'tanium_coverage': ('tanium_coverage', "{col} IS NOT NULL AND {col} != ''"),
            'apm_coverage': ('apm', "{col} IS NOT NULL AND {col} != ''")
        }
        
        for metric_name, (field, condition) in coverage_tests.items():
            col_name = get_column_name(field)
            if col_name and col_name in DB_CONFIG['columns']:
                try:
                    where_clause = condition.format(col=col_name)
                    query = f'SELECT COUNT(*) FROM {table_name} WHERE {where_clause}'
                    count = execute_query(query)[0][0]
                    
                    coverage[metric_name] = {
                        'count': count,
                        'percentage': calculate_coverage_percentage(count, total_hosts)
                    }
                except Exception as e:
                    logger.error(f"Error calculating {metric_name}: {str(e)}")
                    coverage[metric_name] = {'count': 0, 'percentage': 0, 'error': str(e)}
        
        return jsonify({
            'total_hosts': total_hosts,
            'coverage': coverage,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Global view failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting schema-aware Flask server")
    app.run(debug=True, host='0.0.0.0', port=5000)