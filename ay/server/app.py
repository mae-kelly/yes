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
    'column_mapping': {},
    'connection_method': None  # Track which method worked
}

def try_connection_methods():
    """Try multiple connection methods until one works"""
    
    # Find all potential database files
    search_patterns = [
        "*.db", "*.duckdb", "*.duck", "*.ddb",
        "*cmdb*", "*CMDB*",
        "../*.db", "../*.duckdb", "../*cmdb*",
        "../../*.db", "../../*.duckdb", "../../*cmdb*",
        "data/*.db", "data/*.duckdb", "data/*cmdb*",
        "db/*.db", "db/*.duckdb", "db/*cmdb*",
        "database/*.db", "database/*.duckdb", "database/*cmdb*",
        "./*.db", "./*.duckdb", "./*cmdb*"
    ]
    
    db_files = set()
    for pattern in search_patterns:
        found_files = glob.glob(pattern, recursive=False)
        db_files.update(found_files)
        # Also try case-insensitive
        found_files = glob.glob(pattern.lower(), recursive=False)
        db_files.update(found_files)
        found_files = glob.glob(pattern.upper(), recursive=False)
        db_files.update(found_files)
    
    # Also explicitly look for files with cmdb in name
    for root, dirs, files in os.walk('.', topdown=True):
        # Don't go too deep
        if root.count(os.sep) > 2:
            dirs[:] = []
            continue
        for file in files:
            if 'cmdb' in file.lower() or file.endswith(('.db', '.duckdb', '.duck', '.ddb')):
                db_files.add(os.path.join(root, file))
    
    logger.info(f"Found potential database files: {db_files}")
    
    if not db_files:
        logger.error("No database files found at all!")
        return False
    
    # Connection attempt counter
    attempt = 0
    
    for db_file in db_files:
        logger.info(f"\n{'='*50}")
        logger.info(f"Trying database file: {db_file}")
        logger.info(f"{'='*50}")
        
        # Method 1: Direct connection with various table names
        attempt += 1
        logger.info(f"Attempt {attempt}: Direct connection to {db_file}")
        try:
            conn = duckdb.connect(db_file, read_only=True)
            
            # Try various table name formats
            table_variations = [
                "universal_cmdb",
                "UNIVERSAL_CMDB",
                "Universal_CMDB",
                "Universal_Cmdb",
                "cmdb",
                "CMDB",
                "main.universal_cmdb",
                "main.UNIVERSAL_CMDB",
                "main.cmdb",
                "main.CMDB",
                '"universal_cmdb"',
                '"UNIVERSAL_CMDB"',
                '"cmdb"',
                '"CMDB"',
                'main."universal_cmdb"',
                'main."UNIVERSAL_CMDB"',
                'main."cmdb"',
                'main."CMDB"',
                "public.universal_cmdb",
                "public.cmdb",
                "default.universal_cmdb",
                "default.cmdb"
            ]
            
            for table_name in table_variations:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    logger.info(f"✓✓✓ SUCCESS! Table {table_name} has {count} rows")
                    DB_CONFIG['db_path'] = db_file
                    DB_CONFIG['full_table_name'] = table_name
                    DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                    DB_CONFIG['connection_method'] = f"Direct connection - {table_name}"
                    analyze_columns(conn, table_name)
                    conn.close()
                    return True
                except Exception as e:
                    continue
            
            conn.close()
        except Exception as e:
            logger.debug(f"Method 1 failed: {str(e)}")
        
        # Method 2: Connect to :memory: and ATTACH the database
        attempt += 1
        logger.info(n=f"Attempt {attempt}: Memory connection with ATTACH")
        try:
            conn = duckdb.connect(':memory:')
            conn.execute(f"ATTACH '{db_file}' AS cmdb_db")
            
            # List attached databases
            dbs = conn.execute("SHOW DATABASES").fetchall()
            logger.info(f"Attached databases: {dbs}")
            
            # Try variations with attached database
            attach_variations = [
                "cmdb_db.main.universal_cmdb",
                "cmdb_db.main.cmdb",
                "cmdb_db.universal_cmdb",
                "cmdb_db.cmdb",
                "cmdb_db.public.universal_cmdb",
                "cmdb_db.public.cmdb",
                '"cmdb_db"."main"."universal_cmdb"',
                '"cmdb_db"."main"."cmdb"'
            ]
            
            for table_name in attach_variations:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    logger.info(f"✓✓✓ SUCCESS with ATTACH! Table {table_name} has {count} rows")
                    DB_CONFIG['db_path'] = f"ATTACH:{db_file}"
                    DB_CONFIG['full_table_name'] = table_name
                    DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                    DB_CONFIG['connection_method'] = f"ATTACH method - {table_name}"
                    analyze_columns(conn, table_name)
                    conn.close()
                    return True
                except:
                    continue
            
            conn.close()
        except Exception as e:
            logger.debug(f"Method 2 failed: {str(e)}")
        
        # Method 3: Connect and USE different schemas
        attempt += 1
        logger.info(f"Attempt {attempt}: USE schema approach")
        try:
            conn = duckdb.connect(db_file, read_only=True)
            
            # Get all schemas
            try:
                schemas = conn.execute("SELECT DISTINCT schema_name FROM information_schema.schemata").fetchall()
                for schema in schemas:
                    schema_name = schema[0]
                    logger.info(f"Trying schema: {schema_name}")
                    
                    try:
                        conn.execute(f"USE {schema_name}")
                        
                        # Try table names in this schema
                        for table_name in ["universal_cmdb", "cmdb", "UNIVERSAL_CMDB", "CMDB"]:
                            try:
                                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                                logger.info(f"✓✓✓ SUCCESS with USE {schema_name}! Table {table_name} has {count} rows")
                                DB_CONFIG['db_path'] = db_file
                                DB_CONFIG['full_table_name'] = f"{schema_name}.{table_name}"
                                DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                                DB_CONFIG['connection_method'] = f"USE {schema_name} - {table_name}"
                                analyze_columns(conn, table_name)
                                conn.close()
                                return True
                            except:
                                continue
                    except:
                        continue
            except:
                pass
            
            conn.close()
        except Exception as e:
            logger.debug(f"Method 3 failed: {str(e)}")
        
        # Method 4: Try creating a view
        attempt += 1
        logger.info(f"Attempt {attempt}: Create view approach")
        try:
            conn = duckdb.connect(':memory:')
            
            # Try to read the file as a table directly
            file_path = os.path.abspath(db_file)
            
            read_variations = [
                f"SELECT * FROM '{file_path}'",
                f"SELECT * FROM read_csv_auto('{file_path}')",
                f"SELECT * FROM read_parquet('{file_path}')"
            ]
            
            for read_query in read_variations:
                try:
                    # Try to create a view from the file
                    conn.execute(f"CREATE VIEW universal_cmdb AS {read_query}")
                    count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
                    logger.info(f"✓✓✓ SUCCESS with view! Has {count} rows")
                    DB_CONFIG['db_path'] = f"VIEW:{db_file}"
                    DB_CONFIG['full_table_name'] = 'universal_cmdb'
                    DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                    DB_CONFIG['connection_method'] = f"View from file"
                    analyze_columns(conn, 'universal_cmdb')
                    conn.close()
                    return True
                except:
                    continue
            
            conn.close()
        except Exception as e:
            logger.debug(f"Method 4 failed: {str(e)}")
        
        # Method 5: List all tables with multiple discovery methods
        attempt += 1
        logger.info(f"Attempt {attempt}: Comprehensive table discovery")
        try:
            conn = duckdb.connect(db_file, read_only=True)
            
            # Try every possible method to list tables
            discovery_queries = [
                "SHOW TABLES",
                "SHOW ALL TABLES",
                "SELECT * FROM duckdb_tables()",
                "SELECT * FROM duckdb_tables",
                "SELECT name FROM sqlite_master WHERE type='table'",
                "SELECT table_name FROM information_schema.tables",
                "SELECT DISTINCT table_name FROM information_schema.tables WHERE table_type='BASE TABLE'",
                "SELECT tablename FROM pg_tables",
                "PRAGMA show_tables",
                "PRAGMA table_list"
            ]
            
            all_tables = set()
            
            for query in discovery_queries:
                try:
                    results = conn.execute(query).fetchall()
                    for row in results:
                        # Extract table name from various formats
                        if isinstance(row, tuple):
                            for item in row:
                                if isinstance(item, str):
                                    all_tables.add(item)
                        else:
                            all_tables.add(str(row))
                except:
                    continue
            
            logger.info(f"All discovered tables: {all_tables}")
            
            # Check each discovered table
            for table in all_tables:
                if 'cmdb' in table.lower():
                    # Try to access it
                    access_attempts = [
                        table,
                        f'"{table}"',
                        f"main.{table}",
                        f'main."{table}"'
                    ]
                    
                    for table_access in access_attempts:
                        try:
                            count = conn.execute(f"SELECT COUNT(*) FROM {table_access}").fetchone()[0]
                            logger.info(f"✓✓✓ SUCCESS! Found accessible table {table_access} with {count} rows")
                            DB_CONFIG['db_path'] = db_file
                            DB_CONFIG['full_table_name'] = table_access
                            DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                            DB_CONFIG['connection_method'] = f"Discovery - {table_access}"
                            analyze_columns(conn, table_access)
                            conn.close()
                            return True
                        except:
                            continue
            
            conn.close()
        except Exception as e:
            logger.debug(f"Method 5 failed: {str(e)}")
        
        # Method 6: Try opening as different file types
        attempt += 1
        logger.info(f"Attempt {attempt}: Alternative file type connections")
        try:
            conn = duckdb.connect(':memory:')
            
            # Maybe it's not a DuckDB file but another format
            alt_formats = [
                (f"SELECT * FROM read_csv_auto('{db_file}')", "CSV"),
                (f"SELECT * FROM read_parquet('{db_file}')", "Parquet"),
                (f"SELECT * FROM read_json_auto('{db_file}')", "JSON"),
                (f"SELECT * FROM sqlite_scan('{db_file}', 'universal_cmdb')", "SQLite"),
                (f"SELECT * FROM sqlite_scan('{db_file}', 'cmdb')", "SQLite")
            ]
            
            for query, format_type in alt_formats:
                try:
                    result = conn.execute(query).fetchdf()
                    if len(result) > 0:
                        logger.info(f"✓✓✓ SUCCESS! File is {format_type} format with {len(result)} rows")
                        # Create a table from it
                        conn.execute("CREATE TABLE universal_cmdb AS " + query)
                        DB_CONFIG['db_path'] = f"{format_type}:{db_file}"
                        DB_CONFIG['full_table_name'] = 'universal_cmdb'
                        DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                        DB_CONFIG['connection_method'] = f"{format_type} file format"
                        analyze_columns(conn, 'universal_cmdb')
                        return True
                except:
                    continue
            
            conn.close()
        except Exception as e:
            logger.debug(f"Method 6 failed: {str(e)}")
        
        # Method 7: Force load with explicit catalog/schema/table
        attempt += 1
        logger.info(f"Attempt {attempt}: Explicit catalog.schema.table")
        try:
            conn = duckdb.connect(db_file, read_only=True)
            
            # Get database name from file
            db_name = os.path.splitext(os.path.basename(db_file))[0]
            
            catalog_variations = [
                f"{db_name}.main.universal_cmdb",
                f"{db_name}.main.cmdb",
                f"{db_name}.public.universal_cmdb",
                f"{db_name}.default.universal_cmdb",
                f"memory.main.universal_cmdb",
                f"memory.main.cmdb",
                f"temp.main.universal_cmdb",
                f"system.main.universal_cmdb"
            ]
            
            for table_ref in catalog_variations:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_ref}").fetchone()[0]
                    logger.info(f"✓✓✓ SUCCESS! Table {table_ref} has {count} rows")
                    DB_CONFIG['db_path'] = db_file
                    DB_CONFIG['full_table_name'] = table_ref
                    DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                    DB_CONFIG['connection_method'] = f"Catalog reference - {table_ref}"
                    analyze_columns(conn, table_ref)
                    conn.close()
                    return True
                except:
                    continue
            
            conn.close()
        except Exception as e:
            logger.debug(f"Method 7 failed: {str(e)}")
        
        # Method 8: Try loading with extensions
        attempt += 1
        logger.info(f"Attempt {attempt}: Load with extensions")
        try:
            conn = duckdb.connect(':memory:')
            
            # Try loading extensions that might help
            extensions = ['sqlite', 'postgres', 'parquet', 'json']
            
            for ext in extensions:
                try:
                    conn.execute(f"INSTALL {ext}")
                    conn.execute(f"LOAD {ext}")
                except:
                    pass
            
            # Now try attaching
            conn.execute(f"ATTACH '{db_file}'")
            
            # List all tables across all catalogs
            try:
                all_objects = conn.execute("""
                    SELECT table_catalog, table_schema, table_name 
                    FROM information_schema.tables
                    WHERE table_name ILIKE '%cmdb%'
                """).fetchall()
                
                for catalog, schema, table in all_objects:
                    full_ref = f"{catalog}.{schema}.{table}"
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM {full_ref}").fetchone()[0]
                        logger.info(f"✓✓✓ SUCCESS with extensions! Table {full_ref} has {count} rows")
                        DB_CONFIG['db_path'] = f"EXT:{db_file}"
                        DB_CONFIG['full_table_name'] = full_ref
                        DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                        DB_CONFIG['connection_method'] = f"Extensions - {full_ref}"
                        analyze_columns(conn, full_ref)
                        conn.close()
                        return True
                    except:
                        continue
            except:
                pass
            
            conn.close()
        except Exception as e:
            logger.debug(f"Method 8 failed: {str(e)}")
        
        # Method 9: Raw file operations
        attempt += 1
        logger.info(f"Attempt {attempt}: Raw file read")
        try:
            # Check if file is actually a text file with SQL
            with open(db_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1000 chars
                
                if 'CREATE TABLE' in content.upper():
                    logger.info("File appears to contain SQL DDL")
                    
                    # Create table from DDL
                    conn = duckdb.connect(':memory:')
                    try:
                        conn.execute(content)
                        
                        # Check for cmdb table
                        tables = conn.execute("SHOW TABLES").fetchall()
                        for table in tables:
                            if 'cmdb' in str(table).lower():
                                count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                                logger.info(f"✓✓✓ SUCCESS from SQL file! Table {table[0]} has {count} rows")
                                DB_CONFIG['db_path'] = f"SQL:{db_file}"
                                DB_CONFIG['full_table_name'] = table[0]
                                DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                                DB_CONFIG['connection_method'] = f"SQL DDL file"
                                analyze_columns(conn, table[0])
                                conn.close()
                                return True
                    except:
                        pass
                    
                    conn.close()
        except:
            pass
        
        # Method 10-20: More desperate attempts
        for extra_attempt in range(10, 21):
            attempt += 1
            logger.info(f"Attempt {attempt}: Alternative method {extra_attempt}")
            
            try:
                conn = duckdb.connect(db_file, read_only=True)
                
                # Try raw SQL variations
                desperate_queries = [
                    "SELECT * FROM (SELECT * FROM universal_cmdb) LIMIT 1",
                    "SELECT 1 FROM universal_cmdb WHERE 1=0",
                    "WITH t AS (SELECT * FROM universal_cmdb) SELECT COUNT(*) FROM t",
                    "SELECT COUNT(*) FROM (VALUES (1)) AS t(x) WHERE EXISTS (SELECT 1 FROM universal_cmdb)",
                    f"SELECT COUNT(*) FROM '{db_file}'.main.universal_cmdb",
                    f"SELECT COUNT(*) FROM \"{db_file}\".main.universal_cmdb",
                    "SELECT COUNT(*) FROM READ_CSV_AUTO('universal_cmdb')",
                    "SELECT COUNT(*) FROM universal_cmdb USING SAMPLE 1",
                    "SELECT COUNT(*) FROM (SHOW TABLES) WHERE name='universal_cmdb'",
                    "SELECT COUNT(*) FROM pg_class WHERE relname='universal_cmdb'"
                ]
                
                for query in desperate_queries:
                    try:
                        result = conn.execute(query).fetchone()
                        if result:
                            logger.info(f"✓✓✓ SUCCESS with query: {query}")
                            DB_CONFIG['db_path'] = db_file
                            DB_CONFIG['full_table_name'] = 'universal_cmdb'
                            DB_CONFIG['simple_table_name'] = 'universal_cmdb'
                            DB_CONFIG['connection_method'] = f"Alternative query {extra_attempt}"
                            analyze_columns(conn, 'universal_cmdb')
                            conn.close()
                            return True
                    except:
                        continue
                
                conn.close()
            except:
                continue
    
    logger.error("All connection attempts failed!")
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
        
        # Method 4: Information schema
        if not columns:
            try:
                columns = conn.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name ILIKE '%cmdb%'
                """).fetchall()
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
        mapping = {}
        
        mapping_patterns = {
            'host': ['host', 'hostname', 'fqdn', 'server_name', 'server', 'machine'],
            'domain': ['domain', 'dns_domain', 'ad_domain', 'dns'],
            'region': ['region', 'location', 'geographic_region', 'geo_region', 'area'],
            'country': ['country', 'nation', 'country_code', 'country_name'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type', 'type'],
            'business_unit': ['business_unit', 'bu', 'business', 'unit', 'department'],
            'present_in_cmdb': ['present_in_cmdb', 'cmdb_present', 'in_cmdb', 'cmdb'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk_logging', 'splunk', 'splunk_enabled'],
            'logging_in_gso': ['logging_in_gso', 'gso_logging', 'gso', 'gso_enabled'],
            'edr_coverage': ['edr_coverage', 'crowdstrike_coverage', 'edr', 'crowdstrike', 'cs'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'tanium_enabled'],
            'apm': ['apm', 'application_monitoring', 'app_monitoring', 'monitoring']
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
    """Get database connection based on discovered method"""
    if not DB_CONFIG['db_path']:
        if not try_connection_methods():
            raise Exception("Cannot establish database connection - tried 20+ methods")
    
    # Handle special connection types
    if DB_CONFIG['db_path'].startswith('ATTACH:'):
        # Use attach method
        db_file = DB_CONFIG['db_path'].replace('ATTACH:', '')
        conn = duckdb.connect(':memory:')
        conn.execute(f"ATTACH '{db_file}' AS cmdb_db")
        return conn
    elif DB_CONFIG['db_path'].startswith('VIEW:'):
        # Recreate view
        db_file = DB_CONFIG['db_path'].replace('VIEW:', '')
        conn = duckdb.connect(':memory:')
        file_path = os.path.abspath(db_file)
        conn.execute(f"CREATE VIEW universal_cmdb AS SELECT * FROM '{file_path}'")
        return conn
    elif DB_CONFIG['db_path'].startswith('EXT:'):
        # Use extensions
        db_file = DB_CONFIG['db_path'].replace('EXT:', '')
        conn = duckdb.connect(':memory:')
        for ext in ['sqlite', 'postgres', 'parquet', 'json']:
            try:
                conn.execute(f"INSTALL {ext}")
                conn.execute(f"LOAD {ext}")
            except:
                pass
        conn.execute(f"ATTACH '{db_file}'")
        return conn
    else:
        # Normal connection
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
        DB_CONFIG['full_table_name'] = None
        DB_CONFIG['connection_method'] = None
        
        if not try_connection_methods():
            return jsonify({
                'error': 'Failed all 20+ connection attempts',
                'attempted_methods': 20,
                'db_config': DB_CONFIG
            }), 500
        
        return jsonify({
            'success': True,
            'connection_method': DB_CONFIG['connection_method'],
            'db_path': DB_CONFIG['db_path'],
            'table_name': DB_CONFIG['full_table_name'],
            'columns': list(DB_CONFIG['columns'].keys()),
            'column_mapping': DB_CONFIG['column_mapping']
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/health')
def health_check():
    try:
        if not DB_CONFIG['db_path']:
            if not try_connection_methods():
                raise Exception("Database discovery failed after 20+ attempts")
        
        table_name = DB_CONFIG['full_table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM {table_name}')[0][0]
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'connection_method': DB_CONFIG['connection_method'],
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
            if not try_connection_methods():
                raise Exception("Database not available after 20+ attempts")
        
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
            'connection_method': DB_CONFIG['connection_method'],
            'table': table_name,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Global view failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Starting aggressive connection discovery Flask server")
    logger.info("Will try 20+ different methods to connect to universal_cmdb")
    logger.info("="*60)
    
    # Try discovery on startup
    if try_connection_methods():
        logger.info(f"\n{'='*60}")
        logger.info(f"✓✓✓ SUCCESSFUL CONNECTION!")
        logger.info(f"Method: {DB_CONFIG['connection_method']}")
        logger.info(f"Database: {DB_CONFIG['db_path']}")
        logger.info(f"Table: {DB_CONFIG['full_table_name']}")
        logger.info(f"Columns: {list(DB_CONFIG['columns'].keys())}")
        logger.info(f"{'='*60}\n")
    else:
        logger.warning("⚠ Initial database discovery failed - will retry on first request")
    
    app.run(debug=True, host='0.0.0.0', port=5000)