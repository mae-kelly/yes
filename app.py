def load_table_mappings():
    """
    Load and parse the reviewed_labeled_columns.json file to extract table and column mappings.
    
    Returns:
        Dictionary with table names as keys and column mappings as values
        
    The JSON structure is:
    {
      "table_name": {
        "ORIGINAL_COLUMN_NAME": "label",  // e.g. "ENDPOINT_NAME": "host"
        "OTHER_COLUMN": "domain"          // e.g. "DOMAIN_NAME": "domain"
      }
    }
    
    We look for columns where the LABEL (value) is "host", not where the column name is "host"
    """
    try:
        mapping_file = os.path.join(file_path, "reviewed_labeled_columns.json")
        
        if not os.path.exists(mapping_file):
            print(f"ERROR: {mapping_file} not found!")
            return {}
        
        print(f"Loading table mappings from: {mapping_file}")
        
        with open(mapping_file, 'r') as f:
            raw_mappings = json.load(f)
        
        print(f"Loaded JSON with {len(raw_mappings)} tables")
        
        # Process the mappings to find tables with hostname columns
        processed_mappings = {}
        tables_with_hosts = 0
        total_host_columns = 0
        
        for table_name, column_mappings in raw_mappings.items():
            if isinstance(column_mappings, dict):
                # Find columns where the LABEL is "host" 
                hostname_columns = []
                for column_name, label in column_mappings.items():
                    if label == "host":
                        hostname_columns.append(column_name)
                
                if hostname_columns:
                    tables_with_hosts += 1
                    total_host_columns += len(hostname_columns)
                    processed_mappings[table_name] = column_mappings
                    print(f"✓ Found hostname table: {table_name}")
                    print(f"  Host columns: {hostname_columns}")
            else:
                print(f"⚠ Skipping {table_name}: invalid structure")
        
        print(f"\n*** SUMMARY ***")
        print(f"Total tables in JSON: {len(raw_mappings)}")
        print(f"Tables with hostname columns (label='host'): {tables_with_hosts}")
        print(f"Total hostname columns found: {total_host_columns}")
        
        return processed_mappings
        
    except Exception as e:
        print(f"Error loading table mappings: {e}")
        return {}#!/usr/bin/env python3
"""
Hostname Normalization Application
=================================

A Flask application specifically built to create and manage a comprehensive
hostname inventory across all BigQuery tables. This app reads table mappings,
normalizes hostnames, and creates a master DuckDB for asset visibility.

Built in the same style as the Log Lens application but focused specifically
on hostname normalization and inventory management.

Author: Based on Log Lens by Jonathan Tomasulo
"""

import os
import json
import re
import threading
import datetime
from functools import wraps
from collections import defaultdict
from typing import Dict, List, Set, Any
import concurrent.futures

# Flask and web framework imports
from flask import Flask, send_from_directory, request, Response, session, jsonify, redirect, url_for
from flask_compress import Compress
from flask_session import Session

# Authentication and security
from authlib.integrations.flask_client import OAuth
from identity.flask import Auth

# Database and data processing
import duckdb
import pandas as pd
import pandas_gbq

# Google Cloud services
from google.cloud import bigquery
from google.oauth2 import service_account

# Scheduling and background tasks
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Utilities
import redis
import requests
from io import StringIO

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

app = Flask(__name__)

# Load configuration from settings file
file_path = os.path.abspath(os.path.dirname(__file__))
settings = json.load(open(os.path.join(file_path, "settings.json")))
Compress(app)

# Security configuration
app.secret_key = os.getenv("FLASK_SECRET_KEY")
pd.set_option('future.no_silent_downcasting', True)

# ============================================================================
# EXTERNAL SERVICE CONFIGURATIONS
# ============================================================================

# Microsoft Entra (Azure AD) Configuration
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.StrictRedis(host='nexia.idc.com', port=6379, db=0)

# OAuth setup for authentication
auth = Auth(
    app,
    authority=os.getenv("AUTHORITY"),
    client_id=os.getenv("CLIENT_ID"),
    client_credentials=os.getenv("CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
)

# Google Cloud BigQuery Configuration
SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcp_prod_key.json")
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def writeToLocalDB(df, table_name):
    """
    Save data to local DuckDB database for fast querying.
    
    Args:
        df: Pandas DataFrame containing the data
        table_name: Name of the table to create/replace
        
    This function connects to a local DuckDB file and saves the data,
    making it available for fast SQL queries later.
    """
    try:
        conn = duckdb.connect(os.path.join(file_path, "hostname_inventory.duckdb"))
        # Check if table exists and get schema info
        table_exists = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [table_name]).fetchone()[0] > 0
        
        if table_exists:
            print(f"Dropping existing table: {table_name}")
            conn.execute(f"DROP TABLE {table_name}")
        
        print(f"Creating new table: {table_name}")
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
        conn.close()
        
    except Exception as e:
        print(f"Error writing to database: {e}")
        if 'conn' in locals():
            conn.close()


def runLocalDBQuery(query, params=None):
    """
    Execute SQL queries against the local hostname inventory DuckDB.
    
    Args:
        query: SQL query string
        params: Optional parameters for the query
        
    Returns:
        List of dictionaries with query results
        
    This function handles all database connections and returns results
    for the hostname inventory system.
    """
    try:
        conn = duckdb.connect(os.path.join(file_path, "hostname_inventory.duckdb"))
        if params:
            data = conn.execute(query, params).df()
        else:
            data = conn.execute(query).df()
        conn.close()
        data = data.to_dict(orient="records")
        return data
    except Exception as e:
        print(f"Database query error: {e}")
        if 'conn' in locals():
            conn.close()
        return []

# ============================================================================
# HOSTNAME NORMALIZATION FUNCTIONS
# ============================================================================

def normalize_hostname(hostname):
    """
    Apply comprehensive normalization rules to a hostname.
    
    Args:
        hostname: Original hostname string
        
    Returns:
        Normalized hostname string or None if invalid
        
    This function standardizes hostnames by:
    - Converting to lowercase
    - Removing domain suffixes (everything after first dot)
    - Removing hyphens, underscores, and special characters
    - Removing common prefixes and suffixes
    - Keeping only alphanumeric characters
    """
    if not hostname or pd.isna(hostname) or str(hostname).strip() == '':
        return None
        
    # Start with original hostname, strip whitespace, convert to lowercase
    normalized = str(hostname).strip().lower()
    
    # Skip if it's an IP address
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', normalized):
        return None
        
    # Skip if it's too short or too long to be a valid hostname
    if len(normalized) < 2 or len(normalized) > 63:
        return None
    
    # Normalization rules applied in sequence
    normalization_patterns = [
        # Remove domain suffixes (everything after first dot)
        (r'^([^.]+)\..*$', r'\1'),
        # Remove hyphens and underscores
        (r'[-_]', ''),
        # Remove common prefixes
        (r'^(host|server|srv|ws|pc|desktop|laptop)', ''),
        # Remove environment suffixes
        (r'(prod|dev|test|stage|staging|qa)$', ''),
        # Remove leading zeros from numbers
        (r'^([a-zA-Z]+)0+(\d+)$', r'\1\2'),
        # Remove all non-alphanumeric characters
        (r'[^a-zA-Z0-9]', ''),
    ]
    
    # Apply normalization patterns
    for pattern, replacement in normalization_patterns:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
    # Final cleanup
    normalized = normalized.strip().lower()
    
    # Return None if normalization resulted in empty string or invalid hostname
    if not normalized or len(normalized) < 2 or not re.match(r'^[a-zA-Z0-9]+$', normalized):
        return None
        
    return normalized


def load_table_mappings():
    """
    Load and parse the reviewed_labeled_columns.json file to extract table and column mappings.
    
    Returns:
        Dictionary with table names as keys and column mappings as values
        
    This function reads the JSON file that contains the mapping of:
    - BigQuery table names (keys)
    - Column mappings within each table (values)
    - Orange labels (like "host", "domain") mapped to blue column names
    """
    try:
        mapping_file = os.path.join(file_path, "reviewed_labeled_columns.json")
        
        if not os.path.exists(mapping_file):
            print(f"ERROR: {mapping_file} not found!")
            print("Please ensure reviewed_labeled_columns.json is in the application directory")
            return {}
        
        print(f"Loading table mappings from: {mapping_file}")
        
        with open(mapping_file, 'r') as f:
            raw_mappings = json.load(f)
        
        print(f"Raw JSON type: {type(raw_mappings)}")
        print(f"Raw JSON keys (first 5): {list(raw_mappings.keys())[:5] if isinstance(raw_mappings, dict) else 'Not a dict'}")
        
        # The JSON should be a dictionary where:
        # - Keys are BigQuery table names (like "prj-fisv-p-gcss-sas-d19dd8f1df.SAS_BI.V_DTM_ENDPOINT")
        # - Values are dictionaries mapping column names to labels
        if isinstance(raw_mappings, dict):
            processed_mappings = {}
            
            for table_name, column_mapping in raw_mappings.items():
                if isinstance(column_mapping, dict):
                    # This table has column mappings
                    processed_mappings[table_name] = column_mapping
                    print(f"Table: {table_name} -> {len(column_mapping)} columns")
                else:
                    print(f"Skipping {table_name}: invalid column mapping type {type(column_mapping)}")
            
            print(f"Successfully loaded mappings for {len(processed_mappings)} tables")
            return processed_mappings
            
        else:
            print(f"ERROR: Expected dictionary at root level, got {type(raw_mappings)}")
            return {}
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {}
    except Exception as e:
        print(f"Error loading table mappings: {e}")
        return {}

# ============================================================================
# BIGQUERY DATA COLLECTION
# ============================================================================

def collect_hostnames_from_table(table_name, column_mappings):
    """
    Collect hostnames and metadata from a specific BigQuery table.
    
    Args:
        table_name: Full BigQuery table name (project.dataset.table)
        column_mappings: Dictionary mapping column names to their purposes
        
    Returns:
        DataFrame with hostnames and metadata from this table
        
    This function queries a single BigQuery table to extract all hostname
    data and associated metadata like domain, region, business unit, etc.
    """
    try:
        # Ensure column_mappings is a dictionary
        if not isinstance(column_mappings, dict):
            print(f"Invalid column mappings for table {table_name}: expected dict, got {type(column_mappings)}")
            return pd.DataFrame()
        
        # Build SELECT clause based on column mappings
        select_clauses = []
        hostname_columns = []
        where_conditions = []
        
        for original_col, label in column_mappings.items():
            if label == "host":
                alias = f"hostname_{len(hostname_columns)}"
                select_clauses.append(f"CAST({original_col} AS STRING) as {alias}")
                hostname_columns.append(alias)
                where_conditions.append(f"{original_col} IS NOT NULL AND TRIM(CAST({original_col} AS STRING)) != ''")
            elif label in ["domain", "region", "business_unit", "infrastructure_type", 
                          "system_classification", "app", "application", "country", "platform"]:
                alias = f"{label}_{len(select_clauses)}"
                select_clauses.append(f"CAST({original_col} AS STRING) as {alias}")
        
        if not hostname_columns:
            print(f"No hostname columns found for table: {table_name}")
            return pd.DataFrame()
        
        if not where_conditions:
            print(f"No valid WHERE conditions for table: {table_name}")
            return pd.DataFrame()
        
        # Build and execute query
        query = f"""
        SELECT DISTINCT
            {', '.join(select_clauses)}
        FROM `{table_name}`
        WHERE {' OR '.join(where_conditions)}
        LIMIT 50000
        """
        
        print(f"Querying table: {table_name}")
        df = bq_client.query(query).to_dataframe()
        
        # Add source table tracking
        df['source_table'] = table_name
        df['collection_timestamp'] = datetime.datetime.now()
        
        print(f"Collected {len(df)} rows from {table_name}")
        return df
        
    except Exception as e:
        print(f"Error collecting from table {table_name}: {e}")
        return pd.DataFrame()


def process_collected_data(df, source_table):
    """
    Process collected data and extract normalized hostnames with metadata.
    
    Args:
        df: DataFrame from BigQuery table
        source_table: Name of the source table
        
    Returns:
        List of processed hostname records
        
    This function takes raw BigQuery data and extracts all hostnames,
    normalizes them, and packages the metadata for the master inventory.
    """
    processed_records = []
    
    if df.empty:
        return processed_records
    
    for _, row in df.iterrows():
        # Extract all hostname columns from this row
        hostnames = []
        for col in df.columns:
            if col.startswith('hostname_') and pd.notna(row[col]) and str(row[col]).strip():
                hostnames.append(str(row[col]).strip())
        
        # Process each hostname found
        for original_hostname in hostnames:
            normalized = normalize_hostname(original_hostname)
            
            if normalized:
                # Create record for this hostname
                record = {
                    'normalized_host': normalized,
                    'original_hostname': original_hostname,
                    'source_table': source_table,
                    'collection_timestamp': row.get('collection_timestamp', datetime.datetime.now())
                }
                
                # Extract metadata fields
                metadata_fields = ['domain', 'region', 'business_unit', 'infrastructure_type',
                                 'system_classification', 'app', 'application', 'country', 'platform']
                
                for field in metadata_fields:
                    values = []
                    for col in df.columns:
                        if col.startswith(f'{field}_') and pd.notna(row[col]) and str(row[col]).strip():
                            values.append(str(row[col]).strip())
                    record[field] = '|'.join(values) if values else None
                
                processed_records.append(record)
    
    return processed_records


def gatherAllHostnames():
    """
    Main function to gather hostnames from all BigQuery tables.
    
    This function:
    1. Loads the table mappings from reviewed_labeled_columns.json
    2. Identifies tables with hostname columns (where label = "host")
    3. Queries each table to extract hostnames and metadata
    4. Normalizes all hostnames using consistent rules
    5. Aggregates data and creates the master hostname inventory
    
    This is the core data collection function that runs on a schedule.
    """
    print("Starting comprehensive hostname collection...")
    
    # Step 1: Load table mappings from JSON file
    table_mappings = load_table_mappings()
    if not table_mappings:
        print("Error: Could not load table mappings from reviewed_labeled_columns.json")
        return
    
    print(f"Loaded {len(table_mappings)} tables from JSON mapping file")
    
    # Step 2: Filter to only tables that have hostname columns (labeled as "host")
    hostname_tables = {}
    for table_name, column_mappings in table_mappings.items():
        if isinstance(column_mappings, dict):
            # Check if any column is labeled as "host"
            hostname_columns = [col for col, label in column_mappings.items() if label == "host"]
            if hostname_columns:
                hostname_tables[table_name] = column_mappings
                print(f"Found hostname table: {table_name} with columns: {hostname_columns}")
        else:
            print(f"Skipping {table_name}: invalid column mapping structure")
    
    print(f"Found {len(hostname_tables)} tables with hostname columns")
    
    if not hostname_tables:
        print("ERROR: No tables with hostname columns found in JSON mapping")
        return
    
    # Step 3: Process each table to collect hostname data
    all_processed_records = []
    
    for table_name, column_mappings in hostname_tables.items():
        print(f"Processing table: {table_name}")
        try:
            # Collect data from this table
            df = collect_hostnames_from_table(table_name, column_mappings)
            if not df.empty:
                records = process_collected_data(df, table_name)
                all_processed_records.extend(records)
                print(f"✓ Processed {len(records)} hostname records from {table_name}")
            else:
                print(f"⚠ No hostname data found in {table_name}")
        except Exception as e:
            print(f"✗ Error processing table {table_name}: {e}")
            continue
    
    if not all_processed_records:
        print("ERROR: No hostname records collected from any table")
        return
    
    print(f"Total hostname records collected: {len(all_processed_records)}")
    
    # Step 4: Aggregate records by normalized hostname
    print("Aggregating and creating master hostname inventory...")
    hostname_aggregation = defaultdict(lambda: {
        'normalized_host': '',
        'locations_across_bq': set(),
        'original_hostnames': set(),
        'domains': set(),
        'regions': set(),
        'business_units': set(),
        'infrastructure_types': set(),
        'system_classifications': set(),
        'applications': set(),
        'countries': set(),
        'platforms': set(),
        'first_seen': None,
        'last_seen': None,
        'record_count': 0
    })
    
    # Process all collected records
    for record in all_processed_records:
        normalized_host = record['normalized_host']
        aggregated = hostname_aggregation[normalized_host]
        
        # Set normalized hostname
        aggregated['normalized_host'] = normalized_host
        
        # Track source information
        aggregated['locations_across_bq'].add(record['source_table'])
        aggregated['original_hostnames'].add(record['original_hostname'])
        aggregated['record_count'] += 1
        
        # Update timestamps
        timestamp = record['collection_timestamp']
        if aggregated['first_seen'] is None or timestamp < aggregated['first_seen']:
            aggregated['first_seen'] = timestamp
        if aggregated['last_seen'] is None or timestamp > aggregated['last_seen']:
            aggregated['last_seen'] = timestamp
        
        # Aggregate metadata
        metadata_fields = ['domain', 'region', 'business_unit', 'infrastructure_type',
                          'system_classification', 'app', 'application', 'country', 'platform']
        
        for field in metadata_fields:
            if record.get(field):
                if field == 'app' or field == 'application':
                    aggregated['applications'].add(record[field])
                else:
                    field_set_name = f"{field}s" if not field.endswith('s') else field
                    if field_set_name in aggregated:
                        aggregated[field_set_name].add(record[field])
    
    # Step 5: Convert aggregated data to DataFrame and save
    final_records = []
    for hostname, data in hostname_aggregation.items():
        final_record = {
            'host': data['normalized_host'],
            'locations_across_bq': ','.join(sorted(data['locations_across_bq'])),
            'original_hostnames': '|'.join(sorted(data['original_hostnames'])),
            'domains': ','.join(sorted(data['domains'])) if data['domains'] else None,
            'regions': ','.join(sorted(data['regions'])) if data['regions'] else None,
            'business_units': ','.join(sorted(data['business_units'])) if data['business_units'] else None,
            'infrastructure_types': ','.join(sorted(data['infrastructure_types'])) if data['infrastructure_types'] else None,
            'system_classifications': ','.join(sorted(data['system_classifications'])) if data['system_classifications'] else None,
            'applications': ','.join(sorted(data['applications'])) if data['applications'] else None,
            'countries': ','.join(sorted(data['countries'])) if data['countries'] else None,
            'platforms': ','.join(sorted(data['platforms'])) if data['platforms'] else None,
            'table_count': len(data['locations_across_bq']),
            'record_count': data['record_count'],
            'first_seen': data['first_seen'],
            'last_seen': data['last_seen']
        }
        final_records.append(final_record)
    
    # Save to DuckDB
    if final_records:
        master_df = pd.DataFrame(final_records)
        writeToLocalDB(master_df, "master_hostnames")
        
        # Create indexes for performance
        try:
            conn = duckdb.connect(os.path.join(file_path, "hostname_inventory.duckdb"))
            conn.execute("CREATE INDEX IF NOT EXISTS idx_host ON master_hostnames(host)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_table_count ON master_hostnames(table_count)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_record_count ON master_hostnames(record_count)")
            conn.close()
        except Exception as e:
            print(f"Error creating indexes: {e}")
        
        print(f"✓ Master hostname inventory created with {len(final_records)} unique hostnames")
        print(f"✓ Average tables per hostname: {master_df['table_count'].mean():.2f}")
        print(f"✓ Hostnames in multiple tables: {len(master_df[master_df['table_count'] > 1])}")
    else:
        print("ERROR: No valid hostname records to save")

# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def clear_hostname_cache():
    """
    Clear all cached hostname data to force fresh collection.
    
    This function removes cached data to ensure the next collection
    pulls fresh information from all BigQuery tables.
    """
    print("Clearing hostname inventory cache...")
    
    # Clear any cached data by recreating relevant tables
    try:
        conn = duckdb.connect(os.path.join(file_path, "hostname_inventory.duckdb"))
        conn.execute("DROP TABLE IF EXISTS master_hostnames")
        conn.close()
        print("Cleared hostname cache tables")
    except Exception as e:
        print(f"Error clearing cache: {e}")

# ============================================================================
# AUTHENTICATION (Same as Log Lens)
# ============================================================================

def login_required(f):
    """
    Decorator to require user authentication for protected routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "_logged_in_user" not in session:
            return redirect(url_for("login_page"), 302)
        return f(*args, **kwargs)
    return decorated_function


def roles_required(roles_required):
    """
    Decorator to require specific user roles for access control.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "_logged_in_user" not in session:
                return redirect(url_for("login"))
            
            user_roles = session["_logged_in_user"].get("roles", [])
            
            if not any(role in user_roles for role in roles_required):
                return "You do not have permission to access this resource", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def logActivity(request, status_code, description):
    """
    Log user activities for audit and security monitoring.
    """
    user_data = session.get("_logged_in_user", {})
    log_data = {
        "base_app": "Nexia",
        "app": "HostnameNormalizer",
        "host": request.host,
        "method": request.method,
        "path": request.path,
        "query_string": request.query_string.decode('utf-8'),
        "remote_addr": request.remote_addr,
        "email": user_data.get('preferred_username', 'N/A'),
        "timestamp": datetime.datetime.now().isoformat(),
        "status_code": status_code,
        "description": description
    }
    
    # Log to Chronicle in background
    threading.Thread(target=log_task, args=(log_data,)).start()

# ============================================================================
# FLASK ROUTES FOR HOSTNAME INVENTORY
# ============================================================================

@app.route('/')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def root(context=None):
    """
    Main dashboard page for the Hostname Normalization application.
    
    This serves the primary interface where users can view the master
    hostname inventory, search for specific hosts, and analyze coverage.
    """
    response = send_from_directory('../client/dist', 'index.html')
    logActivity(request, response.status_code, "Served hostname normalizer main page")
    return response


@app.route('/getHostnameStats')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def getHostnameStats(context=None):
    """
    Get comprehensive statistics about the hostname inventory.
    
    Returns:
        JSON with statistics including:
        - Total unique normalized hostnames
        - Hostnames appearing in multiple tables
        - Table coverage distribution
        - Metadata completeness statistics
    """
    try:
        # Basic statistics
        total_hosts = runLocalDBQuery("SELECT COUNT(*) as count FROM master_hostnames")[0]['count']
        
        multi_table_hosts = runLocalDBQuery("""
            SELECT COUNT(*) as count FROM master_hostnames WHERE table_count > 1
        """)[0]['count']
        
        avg_table_coverage = runLocalDBQuery("""
            SELECT AVG(table_count) as avg_coverage FROM master_hostnames
        """)[0]['avg_coverage']
        
        max_table_coverage = runLocalDBQuery("""
            SELECT MAX(table_count) as max_coverage FROM master_hostnames
        """)[0]['max_coverage']
        
        # Metadata completeness
        domain_coverage = runLocalDBQuery("""
            SELECT COUNT(*) as count FROM master_hostnames WHERE domains IS NOT NULL
        """)[0]['count']
        
        region_coverage = runLocalDBQuery("""
            SELECT COUNT(*) as count FROM master_hostnames WHERE regions IS NOT NULL
        """)[0]['count']
        
        business_unit_coverage = runLocalDBQuery("""
            SELECT COUNT(*) as count FROM master_hostnames WHERE business_units IS NOT NULL
        """)[0]['count']
        
        # Top tables by hostname count
        top_tables = runLocalDBQuery("""
            SELECT 
                unnest(string_split(locations_across_bq, ',')) as table_name,
                COUNT(*) as hostname_count
            FROM master_hostnames
            GROUP BY table_name
            ORDER BY hostname_count DESC
            LIMIT 10
        """)
        
        stats = {
            'total_hostnames': total_hosts,
            'multi_table_hostnames': multi_table_hosts,
            'single_table_hostnames': total_hosts - multi_table_hosts,
            'avg_table_coverage': round(avg_table_coverage, 2),
            'max_table_coverage': max_table_coverage,
            'domain_coverage_percent': round((domain_coverage / total_hosts) * 100, 2),
            'region_coverage_percent': round((region_coverage / total_hosts) * 100, 2),
            'business_unit_coverage_percent': round((business_unit_coverage / total_hosts) * 100, 2),
            'top_tables': top_tables
        }
        
        response = json.dumps(stats), 200
        logActivity(request, response[1], "Fetched hostname statistics")
        return response
        
    except Exception as e:
        print(f"Error getting hostname stats: {e}")
        response = json.dumps({'error': 'Failed to get statistics'}), 500
        logActivity(request, response[1], "Error fetching hostname statistics")
        return response


@app.route('/searchHostnames')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def searchHostnames(context=None):
    """
    Search the master hostname inventory.
    
    Query Parameters:
        term: Search term to find in hostnames or table names
        page: Page number for pagination
        limit: Number of results per page
        
    Returns:
        JSON with paginated search results including hostname data and metadata
    """
    try:
        search_term = request.args.get('term', '')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 25, type=int)
        offset = (page - 1) * limit
        
        if search_term:
            # Search in hostnames, original hostnames, and table locations
            search_query = f"""
            SELECT 
                host,
                locations_across_bq,
                original_hostnames,
                domains,
                regions,
                business_units,
                infrastructure_types,
                table_count,
                record_count,
                first_seen,
                last_seen
            FROM master_hostnames
            WHERE 
                host LIKE '%{search_term.lower()}%' 
                OR locations_across_bq LIKE '%{search_term}%'
                OR original_hostnames LIKE '%{search_term}%'
            ORDER BY table_count DESC, record_count DESC
            LIMIT {limit} OFFSET {offset}
            """
            
            count_query = f"""
            SELECT COUNT(*) as total
            FROM master_hostnames
            WHERE 
                host LIKE '%{search_term.lower()}%' 
                OR locations_across_bq LIKE '%{search_term}%'
                OR original_hostnames LIKE '%{search_term}%'
            """
        else:
            # Return all hostnames when no search term
            search_query = f"""
            SELECT 
                host,
                locations_across_bq,
                original_hostnames,
                domains,
                regions,
                business_units,
                infrastructure_types,
                table_count,
                record_count,
                first_seen,
                last_seen
            FROM master_hostnames
            ORDER BY table_count DESC, record_count DESC
            LIMIT {limit} OFFSET {offset}
            """
            
            count_query = "SELECT COUNT(*) as total FROM master_hostnames"
        
        # Execute queries
        results = runLocalDBQuery(search_query)
        total_count = runLocalDBQuery(count_query)[0]['total']
        total_pages = (total_count + limit - 1) // limit
        
        response_data = {
            'results': results,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'limit': limit
            },
            'search_term': search_term
        }
        
        response = json.dumps(response_data, default=str), 200
        logActivity(request, response[1], f"Searched hostnames with term: {search_term}")
        return response
        
    except Exception as e:
        print(f"Error searching hostnames: {e}")
        response = json.dumps({'error': 'Search failed'}), 500
        logActivity(request, response[1], "Error searching hostnames")
        return response


@app.route('/getTopHostnames')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def getTopHostnames(context=None):
    """
    Get the top hostnames by table coverage and record count.
    
    Returns:
        JSON with the most widely distributed hostnames across BigQuery tables
        
    This helps identify the most important/common hostnames in your infrastructure.
    """
    try:
        query = """
        SELECT 
            host,
            table_count,
            record_count,
            locations_across_bq,
            domains,
            regions,
            business_units
        FROM master_hostnames
        ORDER BY table_count DESC, record_count DESC
        LIMIT 50
        """
        
        data = runLocalDBQuery(query)
        
        response = json.dumps(data, default=str), 200
        logActivity(request, response[1], "Fetched top hostnames")
        return response
        
    except Exception as e:
        print(f"Error getting top hostnames: {e}")
        response = json.dumps({'error': 'Failed to get top hostnames'}), 500
        logActivity(request, response[1], "Error fetching top hostnames")
        return response


@app.route('/getHostnameDetails/<hostname>')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def getHostnameDetails(hostname, context=None):
    """
    Get detailed information about a specific hostname.
    
    Args:
        hostname: The normalized hostname to look up
        
    Returns:
        JSON with complete details including all original variants,
        all tables it appears in, and all associated metadata
    """
    try:
        query = """
        SELECT *
        FROM master_hostnames
        WHERE host = ?
        """
        
        data = runLocalDBQuery(query, [hostname.lower()])
        
        if data:
            # Split comma/pipe separated fields into arrays for better display
            result = data[0]
            result['locations_list'] = result['locations_across_bq'].split(',') if result['locations_across_bq'] else []
            result['original_hostnames_list'] = result['original_hostnames'].split('|') if result['original_hostnames'] else []
            result['domains_list'] = result['domains'].split(',') if result['domains'] else []
            result['regions_list'] = result['regions'].split(',') if result['regions'] else []
            
            response = json.dumps(result, default=str), 200
        else:
            response = json.dumps({'error': 'Hostname not found'}), 404
            
        logActivity(request, response[1], f"Fetched details for hostname: {hostname}")
        return response
        
    except Exception as e:
        print(f"Error getting hostname details: {e}")
        response = json.dumps({'error': 'Failed to get hostname details'}), 500
        logActivity(request, response[1], f"Error fetching details for hostname: {hostname}")
        return response


@app.route('/exportHostnames')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def exportHostnames(context=None):
    """
    Export the complete hostname inventory to CSV.
    
    Returns:
        CSV file download with the complete master hostname inventory
        
    This allows users to download the complete normalized hostname
    inventory for offline analysis, reporting, or integration with other tools.
    """
    try:
        query = """
        SELECT *
        FROM master_hostnames
        ORDER BY table_count DESC, record_count DESC
        """
        
        data = runLocalDBQuery(query)
        df = pd.DataFrame(data)
        
        # Convert to CSV
        csv_data = StringIO()
        df.to_csv(csv_data, index=False)
        csv_data.seek(0)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"master_hostname_inventory_{timestamp}.csv"
        
        response = Response(
            csv_data.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        ), 200
        
        logActivity(request, response[1], "Exported complete hostname inventory")
        return response
        
    except Exception as e:
        print(f"Error exporting hostnames: {e}")
        response = json.dumps({'error': 'Export failed'}), 500
        logActivity(request, response[1], "Error exporting hostnames")
        return response


@app.route('/getTableCoverage')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def getTableCoverage(context=None):
    """
    Get coverage analysis showing which BigQuery tables have the most hostnames.
    
    Returns:
        JSON with table coverage statistics
        
    This helps understand which BigQuery tables are the richest sources
    of hostname data and which might need attention.
    """
    try:
        query = """
        SELECT 
            unnest(string_split(locations_across_bq, ',')) as table_name,
            COUNT(*) as unique_hostnames,
            SUM(record_count) as total_records,
            AVG(table_count) as avg_cross_table_presence
        FROM master_hostnames
        GROUP BY table_name
        ORDER BY unique_hostnames DESC
        """
        
        data = runLocalDBQuery(query)
        
        response = json.dumps(data, default=str), 200
        logActivity(request, response[1], "Fetched table coverage analysis")
        return response
        
    except Exception as e:
        print(f"Error getting table coverage: {e}")
        response = json.dumps({'error': 'Failed to get table coverage'}), 500
        logActivity(request, response[1], "Error fetching table coverage")
        return response


@app.route('/refreshHostnames')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def refreshHostnames(context=None):
    """
    Trigger a manual refresh of the hostname inventory.
    
    Returns:
        JSON confirmation that the refresh has been started
        
    This endpoint allows administrators to manually trigger a complete
    refresh of the hostname inventory from all BigQuery tables.
    """
    try:
        # Start refresh in background thread
        threading.Thread(target=run_hostname_collection_background).start()
        
        response = json.dumps({
            'message': 'Hostname inventory refresh started in background',
            'status': 'started'
        }), 202
        
        logActivity(request, response[1], "Triggered manual hostname refresh")
        return response
        
    except Exception as e:
        print(f"Error starting hostname refresh: {e}")
        response = json.dumps({'error': 'Failed to start refresh'}), 500
        logActivity(request, response[1], "Error starting hostname refresh")
        return response

# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================

def run_hostname_collection_background():
    """
    Execute hostname collection in a separate background thread.
    
    This function runs the complete hostname normalization process
    without blocking the web interface.
    """
    print("Starting background hostname collection...")
    try:
        gatherAllHostnames()
        print("Background hostname collection completed successfully")
    except Exception as e:
        print(f"Background hostname collection failed: {e}")


def log_task(log_data):
    """
    Background task for logging user activities.
    """
    try:
        headers = {
            "x-goog-api-key": os.getenv("CHRONICLE_API_KEY"),
            "x-webhook-access-key": os.getenv("CHRONICLE_SECRET_KEY"),
            "Content-Type": "application/json"
        }
        
        response = requests.post(os.getenv("CHRONICLE_ENDPOINT"), headers=headers, json=log_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send log to Google Chronicle: {e}")

# ============================================================================
# SCHEDULED TASKS
# ============================================================================

# Hostname collection scheduler - runs every 6 hours
scheduler = BackgroundScheduler()
hostname_job = scheduler.add_job(
    gatherAllHostnames,
    trigger=CronTrigger.from_crontab("0 */6 * * *"),  # Every 6 hours
    id='hostname_collection',
    name='Comprehensive Hostname Collection'
)
scheduler.start()

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    """
    Application entry point.
    
    Starts the Flask server and begins background hostname collection.
    """
    print("Starting Hostname Normalization Application...")
    
    # Check if JSON mapping file exists
    mapping_file = os.path.join(file_path, "reviewed_labeled_columns.json")
    if not os.path.exists(mapping_file):
        print(f"ERROR: Missing required file: {mapping_file}")
        print("Please ensure reviewed_labeled_columns.json is in the application directory")
        exit(1)
    
    # Start initial hostname collection in background
    print("Starting initial hostname collection...")
    threading.Thread(target=run_hostname_collection_background).start()
    
    # Run Flask application
    app.run(debug=False, host='0.0.0.0', port=5001)


# ============================================================================
# INTEGRATION FUNCTIONS FOR LOG LENS
# ============================================================================

def get_normalized_hostname_lookup():
    """
    Get a lookup dictionary for hostname normalization in Log Lens.
    
    Returns:
        Dictionary mapping original hostnames to normalized versions
        
    This function can be imported by the main Log Lens application
    to use the comprehensive hostname normalization for better asset correlation.
    """
    try:
        conn = duckdb.connect(os.path.join(file_path, "hostname_inventory.duckdb"))
        query = """
        SELECT host, original_hostnames
        FROM master_hostnames
        """
        
        results = conn.execute(query).fetchall()
        conn.close()
        
        # Create lookup dictionary
        lookup = {}
        for normalized_host, original_hostnames_str in results:
            if original_hostnames_str:
                original_hostnames = original_hostnames_str.split('|')
                for original in original_hostnames:
                    lookup[original.lower()] = normalized_host
        
        return lookup
        
    except Exception as e:
        print(f"Error creating hostname lookup: {e}")
        return {}


def get_hostname_table_coverage(hostname):
    """
    Get all BigQuery tables that contain a specific hostname.
    
    Args:
        hostname: Normalized hostname to look up
        
    Returns:
        List of table names that contain this hostname
        
    This helps with data lineage and understanding where specific
    assets appear across the BigQuery infrastructure.
    """
    try:
        query = """
        SELECT locations_across_bq
        FROM master_hostnames
        WHERE host = ?
        """
        
        result = runLocalDBQuery(query, [hostname.lower()])
        if result and result[0]['locations_across_bq']:
            return result[0]['locations_across_bq'].split(',')
        return []
        
    except Exception as e:
        print(f"Error getting table coverage for {hostname}: {e}")
        return []

# ============================================================================
# SUMMARY AND DOCUMENTATION
# ============================================================================

"""
HOSTNAME NORMALIZATION APPLICATION SUMMARY
=========================================

This Flask application creates a comprehensive hostname inventory by:

1. **Data Collection**:
   - Reads JSON mapping of BigQuery tables with hostname columns
   - Queries all tables in parallel for maximum efficiency
   - Extracts hostnames and rich metadata (domain, region, business unit, etc.)

2. **Hostname Normalization**:
   - Converts to lowercase
   - Removes domain suffixes (.company.com -> server)
   - Removes hyphens and special characters (web-server-01 -> webserver01)
   - Removes common prefixes and suffixes (host-web-prod -> web)
   - Standardizes format for consistent asset identification

3. **Master Inventory Creation**:
   - Creates DuckDB with normalized hostnames as primary key
   - Tracks which BigQuery tables each hostname appears in
   - Maintains rich metadata for asset classification
   - Provides complete data lineage and source tracking

4. **Web Interface**:
   - Search functionality across all hostnames and metadata
   - Statistics and coverage analysis
   - Data export capabilities for offline analysis
   - Integration endpoints for use by other applications (like Log Lens)

5. **Background Processing**:
   - Scheduled data collection every 6 hours
   - Manual refresh capabilities
   - Parallel processing for efficiency with large datasets

The resulting database provides:
- `host`: Normalized hostname (primary identifier)
- `locations_across_bq`: Comma-separated list of BigQuery tables
- Rich metadata fields for asset classification and analysis
- Performance indexes for fast querying

This system solves the core problem of hostname inconsistency across
enterprise BigQuery tables and provides a single source of truth for
asset identification and tracking.
"""