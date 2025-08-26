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
    search_paths = ["*.db", "*.duckdb", "../*.db", "../*.duckdb", "../../*.db", "../../*.duckdb", "server/*.db", "./server/*.db"]
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
            
            # First, let's see what databases/catalogs are attached
            try:
                # Try PRAGMA database_list to see attached databases
                db_list = conn.execute("PRAGMA database_list").fetchall()
                logger.info(f"Attached databases: {db_list}")
            except:
                pass
            
            # Strategy 1: Direct table access in default schema
            try:
                # First check if table exists directly
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [t[0] for t in tables]
                logger.info(f"Tables in current context: {table_names}")
                
                if 'universal_cmdb' in table_names:
                    logger.info("Found universal_cmdb in default context")
                    if test_table_access(conn, 'universal_cmdb', 'universal_cmdb'):
                        DB_CONFIG['db_path'] = db_file
                        DB_CONFIG['full_table_name'] = 'universal_cmdb'
                        DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                        analyze_columns(conn, 'universal_cmdb')
                        conn.close()
                        return True
                        
            except Exception as e:
                logger.debug(f"Default context check failed: {str(e)}")
            
            # Strategy 2: Check main schema explicitly
            try:
                # Try to access as main.universal_cmdb
                if test_table_access(conn, 'main.universal_cmdb', 'universal_cmdb'):
                    DB_CONFIG['db_path'] = db_file
                    DB_CONFIG['full_table_name'] = 'main.universal_cmdb'
                    DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                    analyze_columns(conn, 'main.universal_cmdb')
                    conn.close()
                    return True
            except:
                pass
            
            # Strategy 3: Use information_schema to find the table
            try:
                # Query information_schema for all tables
                all_tables = conn.execute("""
                    SELECT table_catalog, table_schema, table_name 
                    FROM information_schema.tables
                """).fetchall()
                
                logger.info(f"All tables from information_schema: {all_tables}")
                
                for catalog, schema, table in all_tables:
                    if 'cmdb' in table.lower():
                        logger.info(f"Found CMDB-related table: {catalog}.{schema}.{table}")
                        
                        # Try different naming combinations
                        full_names = [
                            f"{table}",
                            f"{schema}.{table}",
                            f"{catalog}.{schema}.{table}",
                            f'"{table}"',
                            f'{schema}."{table}"',
                            f'{catalog}.{schema}."{table}"'
                        ]
                        
                        for full_name in full_names:
                            if test_table_access(conn, full_name, table):
                                DB_CONFIG['db_path'] = db_file
                                DB_CONFIG['full_table_name'] = full_name
                                DB_CONFIG['simple_table_name'] = table
                                analyze_columns(conn, full_name)
                                conn.close()
                                return True
                                
            except Exception as e:
                logger.debug(f"Information schema query failed: {str(e)}")
            
            # Strategy 4: Check all schemas
            try:
                schemas = conn.execute("SELECT DISTINCT schema_name FROM information_schema.schemata").fetchall()
                logger.info(f"Available schemas: {[s[0] for s in schemas]}")
                
                for schema in schemas:
                    schema_name = schema[0]
                    try:
                        # Get tables in this schema
                        tables_query = f"""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = '{schema_name}'
                        """
                        tables = conn.execute(tables_query).fetchall()
                        
                        for table in tables:
                            table_name = table[0]
                            if 'cmdb' in table_name.lower():
                                full_name = f"{schema_name}.{table_name}"
                                logger.info(f"Testing table: {full_name}")
                                
                                if test_table_access(conn, full_name, table_name):
                                    DB_CONFIG['db_path'] = db_file
                                    DB_CONFIG['full_table_name'] = full_name
                                    DB_CONFIG['simple_table_name'] = table_name
                                    analyze_columns(conn, full_name)
                                    conn.close()
                                    return True
                                    
                    except Exception as e:
                        logger.debug(f"Error checking schema {schema_name}: {str(e)}")
                        
            except Exception as e:
                logger.debug(f"Schema enumeration failed: {str(e)}")
            
            # Strategy 5: Try PRAGMA commands to list tables
            try:
                # Use PRAGMA to show all tables
                pragma_tables = conn.execute("PRAGMA show_tables").fetchall()
                logger.info(f"PRAGMA show_tables result: {pragma_tables}")
                
                for table_info in pragma_tables:
                    if isinstance(table_info, tuple) and len(table_info) > 0:
                        table_name = table_info[0]
                        if 'cmdb' in str(table_name).lower():
                            if test_table_access(conn, table_name, table_name):
                                DB_CONFIG['db_path'] = db_file
                                DB_CONFIG['full_table_name'] = table_name
                                DB_CONFIG['simple_table_name'] = table_name
                                analyze_columns(conn, table_name)
                                conn.close()
                                return True
            except Exception as e:
                logger.debug(f"PRAGMA show_tables failed: {str(e)}")
            
            # Strategy 6: Try to create the table from a view or another source
            try:
                # Check if there are any views that might contain the data
                views = conn.execute("SELECT * FROM duckdb_views()").fetchall()
                logger.info(f"Available views: {views}")
                
                for view in views:
                    if 'cmdb' in str(view).lower():
                        logger.info(f"Found CMDB-related view: {view}")
            except:
                pass
            
            # Strategy 7: List all objects using duckdb functions
            try:
                # Try duckdb_tables() function
                duckdb_tables = conn.execute("SELECT * FROM duckdb_tables()").fetchall()
                logger.info(f"DuckDB tables: {duckdb_tables}")
                
                for table_info in duckdb_tables:
                    # table_info typically contains (database, schema, table_name, ...)
                    if len(table_info) >= 3:
                        db_name = table_info[0]
                        schema_name = table_info[1]
                        table_name = table_info[2]
                        
                        if 'cmdb' in str(table_name).lower():
                            # Try different combinations
                            test_names = [
                                table_name,
                                f"{schema_name}.{table_name}",
                                f"{db_name}.{schema_name}.{table_name}"
                            ]
                            
                            for test_name in test_names:
                                if test_table_access(conn, test_name, table_name):
                                    DB_CONFIG['db_path'] = db_file
                                    DB_CONFIG['full_table_name'] = test_name
                                    DB_CONFIG['simple_table_name'] = table_name
                                    analyze_columns(conn, test_name)
                                    conn.close()
                                    return True
                                    
            except Exception as e:
                logger.debug(f"duckdb_tables() failed: {str(e)}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to analyze {db_file}: {str(e)}")
            continue
    
    return False

def test_table_access(conn, table_name, simple_name):
    """Test if we can access a table"""
    try:
        # Try a simple count query
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        logger.info(f"✓ Successfully accessed {table_name} with {count} rows")
        return True
    except Exception as e:
        logger.debug(f"✗ Cannot access {table_name}: {str(e)}")
        return False

def analyze_columns(conn, table_name):
    """Analyze table columns and create mapping"""
    try:
        # Try different methods to get column information
        columns = None
        
        # Method 1: DESCRIBE
        try:
            columns = conn.execute(f'DESCRIBE {table_name}').fetchall()
        except:
            pass
        
        # Method 2: PRAGMA table_info
        if not columns:
            try:
                columns = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            except:
                pass
        
        # Method 3: SELECT * LIMIT 0
        if not columns:
            try:
                result = conn.execute(f'SELECT * FROM {table_name} LIMIT 0')
                columns = [(desc[0], desc[1]) for desc in result.description]
            except:
                pass
        
        if columns:
            DB_CONFIG['columns'] = {col[0]: col[1] for col in columns}
        else:
            # Fallback: get columns from a sample query
            result = conn.execute(f'SELECT * FROM {table_name} LIMIT 1')
            DB_CONFIG['columns'] = {desc[0]: 'UNKNOWN' for desc in result.description}
        
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
        logger.error(traceback.format_exc())

def get_connection():
    """Get database connection"""
    if not DB_CONFIG['db_path']:
        if not discover_schema_structure():
            raise Exception("Cannot establish database connection - universal_cmdb table not found")
    
    return duckdb.connect(DB_CONFIG['db_path'], read_only=True)

def execute_query(query):
    """Execute query with error handling"""
    conn = get_connection()
    try:
        logger.debug(f"Executing query: {query}")
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
        # Reset config to force re-discovery
        DB_CONFIG['db_path'] = None
        
        if not discover_schema_structure():
            # Try to provide more debugging info
            conn = None
            debug_info = {'discovery_successful': False, 'debug': {}}
            
            # Find any .db or .duckdb files
            search_paths = ["*.db", "*.duckdb", "../*.db", "../*.duckdb", "../../*.db", "../../*.duckdb"]
            db_files = []
            for pattern in search_paths:
                db_files.extend(glob.glob(pattern))
            
            if db_files:
                db_file = db_files[0]
                try:
                    conn = duckdb.connect(db_file, read_only=True)
                    
                    # Get all available information
                    debug_info['debug']['db_file'] = db_file
                    
                    # Get all tables using multiple methods
                    try:
                        tables = conn.execute("SHOW TABLES").fetchall()
                        debug_info['debug']['show_tables'] = [t[0] for t in tables]
                    except Exception as e:
                        debug_info['debug']['show_tables_error'] = str(e)
                    
                    try:
                        duckdb_tables = conn.execute("SELECT * FROM duckdb_tables()").fetchall()
                        debug_info['debug']['duckdb_tables'] = duckdb_tables
                    except Exception as e:
                        debug_info['debug']['duckdb_tables_error'] = str(e)
                    
                    try:
                        info_tables = conn.execute("""
                            SELECT table_catalog, table_schema, table_name 
                            FROM information_schema.tables
                        """).fetchall()
                        debug_info['debug']['information_schema_tables'] = info_tables
                    except Exception as e:
                        debug_info['debug']['information_schema_error'] = str(e)
                    
                    conn.close()
                except Exception as e:
                    debug_info['debug']['connection_error'] = str(e)
            
            return jsonify(debug_info)
        
        return jsonify({
            'db_config': DB_CONFIG,
            'discovery_successful': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/health')
def health_check():
    try:
        if not DB_CONFIG['db_path']:
            if not discover_schema_structure():
                raise Exception("Database discovery failed - universal_cmdb table not found")
        
        table_name = DB_CONFIG['full_table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM {table_name}')[0][0]
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'table': table_name,
            'total_hosts': total_hosts,
            'columns': list(DB_CONFIG['columns'].keys()),
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
            else:
                logger.warning(f"Column not found for {metric_name}: {field} -> {col_name}")
                coverage[metric_name] = {'count': 0, 'percentage': 0, 'error': 'Column not mapped'}
        
        return jsonify({
            'total_hosts': total_hosts,
            'coverage': coverage,
            'table': table_name,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Global view failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting schema-aware Flask server")
    logger.info("Attempting initial database discovery...")
    
    # Try discovery on startup
    if discover_schema_structure():
        logger.info(f"✓ Successfully connected to database: {DB_CONFIG['db_path']}")
        logger.info(f"✓ Using table: {DB_CONFIG['full_table_name']}")
        logger.info(f"✓ Found columns: {list(DB_CONFIG['columns'].keys())}")
    else:
        logger.warning("⚠ Initial database discovery failed - will retry on first request")
    
    app.run(debug=True, host='0.0.0.0', port=5000)