#!/usr/bin/env python3
"""
Hostname Normalizer Application
==============================

A Flask application that creates a master hostname inventory by:
1. Reading table/column mappings from reviewed_labeled_columns.json
2. Authenticating to BigQuery using service account credentials
3. Querying each table to extract hostname data (where label="host")
4. Normalizing all hostnames using consistent rules
5. Creating a master DuckDB with normalized hostnames and source tracking

Author: Based on Log Lens architecture
"""

import os
import json
import re
import threading
import datetime
from functools import wraps
from collections import defaultdict
from typing import Dict, List, Set, Any

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
settings_file = os.path.join(file_path, "settings.json")

if os.path.exists(settings_file):
    with open(settings_file, 'r') as f:
        settings = json.load(f)
else:
    settings = {}  # Default empty settings

Compress(app)

# Security configuration
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "dev-secret-key-change-in-production"
pd.set_option('future.no_silent_downcasting', True)

# ============================================================================
# AUTHENTICATION CONFIGURATION
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

# ============================================================================
# BIGQUERY AUTHENTICATION AND CONNECTION
# ============================================================================

def initialize_bigquery_client():
    """
    Initialize and authenticate BigQuery client using service account credentials.
    
    Returns:
        Authenticated BigQuery client or None if authentication fails
    """
    try:
        service_account_file = os.path.join(file_path, "gcp_prod_key.json")
        
        if not os.path.exists(service_account_file):
            print(f"ERROR: BigQuery service account file not found: {service_account_file}")
            print("Please ensure gcp_prod_key.json is in the application directory")
            return None
        
        print(f"Authenticating to BigQuery using: {service_account_file}")
        
        credentials = service_account.Credentials.from_service_account_file(service_account_file)
        client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        
        # Test the connection
        query = "SELECT 1 as test_connection LIMIT 1"
        test_result = client.query(query).result()
        
        print("✓ BigQuery authentication successful")
        return client
        
    except Exception as e:
        print(f"ERROR: Failed to authenticate to BigQuery: {e}")
        return None

# Initialize BigQuery client
bq_client = initialize_bigquery_client()

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def writeToLocalDB(df, table_name):
    """
    Save DataFrame to local DuckDB database.
    
    Args:
        df: Pandas DataFrame containing the data
        table_name: Name of the table to create/replace
    """
    try:
        db_path = os.path.join(file_path, "hostname_inventory.duckdb")
        conn = duckdb.connect(db_path)
        
        # Drop existing table if it exists
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        print(f"Creating table: {table_name}")
        
        # Create new table from DataFrame
        conn.register("temp_df", df)
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df")
        
        conn.close()
        print(f"✓ Saved {len(df)} records to {table_name}")
        
    except Exception as e:
        print(f"ERROR: Failed to write to database: {e}")
        if 'conn' in locals():
            conn.close()


def runLocalDBQuery(query, params=None):
    """
    Execute SQL queries against the hostname inventory DuckDB.
    
    Args:
        query: SQL query string
        params: Optional parameters for the query
        
    Returns:
        List of dictionaries with query results
    """
    try:
        db_path = os.path.join(file_path, "hostname_inventory.duckdb")
        conn = duckdb.connect(db_path)
        
        if params:
            result = conn.execute(query, params).df()
        else:
            result = conn.execute(query).df()
        
        conn.close()
        return result.to_dict(orient="records")
        
    except Exception as e:
        print(f"ERROR: Database query failed: {e}")
        if 'conn' in locals():
            conn.close()
        return []

# ============================================================================
# JSON MAPPING FILE PROCESSING
# ============================================================================

def load_table_mappings():
    """
    Load and parse the reviewed_labeled_columns.json file.
    
    Returns:
        Dictionary with table names as keys and column mappings as values
        
    The JSON structure is:
    {
      "table_name": {
        "ORIGINAL_COLUMN_NAME": "label",  // e.g. "ENDPOINT_NAME": "host"
        "OTHER_COLUMN": "domain"          // e.g. "DOMAIN_NAME": "domain"  
      }
    }
    """
    try:
        mapping_file = os.path.join(file_path, "reviewed_labeled_columns.json")
        
        if not os.path.exists(mapping_file):
            print(f"ERROR: {mapping_file} not found!")
            print("Please place reviewed_labeled_columns.json in the application directory")
            return {}
        
        print(f"Loading table mappings from: {mapping_file}")
        
        with open(mapping_file, 'r') as f:
            raw_mappings = json.load(f)
        
        if not isinstance(raw_mappings, dict):
            print(f"ERROR: Expected JSON object at root level, got {type(raw_mappings)}")
            return {}
        
        print(f"✓ Loaded JSON with {len(raw_mappings)} table definitions")
        
        # Filter to only tables that have hostname columns (where label="host")
        hostname_tables = {}
        total_host_columns = 0
        
        for table_name, column_mappings in raw_mappings.items():
            if isinstance(column_mappings, dict):
                # Find columns labeled as "host"
                hostname_columns = [col_name for col_name, label in column_mappings.items() if label == "host"]
                
                if hostname_columns:
                    hostname_tables[table_name] = column_mappings
                    total_host_columns += len(hostname_columns)
                    print(f"✓ {table_name}: {len(hostname_columns)} hostname column(s)")
            else:
                print(f"⚠ Skipping {table_name}: invalid column mapping structure")
        
        print(f"\n*** MAPPING SUMMARY ***")
        print(f"Total tables in JSON: {len(raw_mappings)}")
        print(f"Tables with hostname columns: {len(hostname_tables)}")
        print(f"Total hostname columns found: {total_host_columns}")
        
        return hostname_tables
        
    except Exception as e:
        print(f"ERROR: Failed to load table mappings: {e}")
        return {}

# ============================================================================
# HOSTNAME NORMALIZATION
# ============================================================================

def normalize_hostname(hostname):
    """
    Apply comprehensive normalization rules to hostname.
    
    Args:
        hostname: Original hostname string
        
    Returns:
        Normalized hostname string or None if invalid
        
    Normalization rules:
    - Convert to lowercase
    - Remove domain suffixes (everything after first dot)
    - Remove hyphens, underscores, special characters
    - Remove common prefixes (host, server, etc.)
    - Remove environment suffixes (prod, dev, etc.)
    - Keep only alphanumeric characters
    """
    if not hostname or pd.isna(hostname) or str(hostname).strip() == '':
        return None
    
    # Convert to string and lowercase
    normalized = str(hostname).strip().lower()
    
    # Skip IP addresses
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', normalized):
        return None
    
    # Skip if too short or too long
    if len(normalized) < 2 or len(normalized) > 63:
        return None
    
    # Apply normalization patterns
    patterns = [
        (r'^([^.]+)\..*$', r'\1'),              # Remove domain suffix
        (r'[-_]', ''),                          # Remove hyphens and underscores
        (r'^(host|server|srv|ws|pc|desktop|laptop)', ''),  # Remove prefixes
        (r'(prod|dev|test|stage|staging|qa)$', ''),         # Remove suffixes
        (r'^([a-zA-Z]+)0+(\d+)$', r'\1\2'),     # Remove leading zeros
        (r'[^a-zA-Z0-9]', ''),                  # Keep only alphanumeric
    ]
    
    for pattern, replacement in patterns:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # Final validation
    normalized = normalized.strip().lower()
    if not normalized or len(normalized) < 2 or not re.match(r'^[a-zA-Z0-9]+$', normalized):
        return None
    
    return normalized

# ============================================================================
# BIGQUERY DATA COLLECTION
# ============================================================================

def collect_hostname_data_from_table(table_name, column_mappings):
    """
    Query a BigQuery table to extract hostname data and metadata.
    
    Args:
        table_name: Full BigQuery table name (project.dataset.table)
        column_mappings: Dictionary mapping column names to labels
        
    Returns:
        DataFrame with hostname data from this table
    """
    if not bq_client:
        print(f"ERROR: BigQuery client not initialized, skipping {table_name}")
        return pd.DataFrame()
    
    try:
        print(f"Querying BigQuery table: {table_name}")
        
        # Build SELECT clause based on column mappings
        select_clauses = []
        hostname_columns = []
        metadata_columns = []
        
        for column_name, label in column_mappings.items():
            if label == "host":
                alias = f"hostname_{len(hostname_columns)}"
                select_clauses.append(f"CAST({column_name} AS STRING) as {alias}")
                hostname_columns.append(column_name)
            elif label in ["domain", "region", "business_unit", "infrastructure_type", 
                          "system_classification", "app", "application", "country", "platform"]:
                alias = f"{label}_{len(metadata_columns)}"
                select_clauses.append(f"CAST({column_name} AS STRING) as {alias}")
                metadata_columns.append((column_name, label))
        
        if not hostname_columns:
            print(f"⚠ No hostname columns found in {table_name}")
            return pd.DataFrame()
        
        # Build WHERE clause to filter null/empty hostnames
        where_conditions = []
        for col_name in hostname_columns:
            where_conditions.append(f"{col_name} IS NOT NULL AND TRIM(CAST({col_name} AS STRING)) != ''")
        
        # Construct BigQuery SQL
        query = f"""
        SELECT DISTINCT
            {', '.join(select_clauses)}
        FROM `{table_name}`
        WHERE {' OR '.join(where_conditions)}
        LIMIT 100000
        """
        
        print(f"Executing query on {table_name}...")
        
        # Execute BigQuery query
        query_job = bq_client.query(query)
        df = query_job.to_dataframe()
        
        # Add source tracking
        df['source_table'] = table_name
        df['collection_timestamp'] = datetime.datetime.now()
        
        print(f"✓ Retrieved {len(df)} rows from {table_name}")
        return df
        
    except Exception as e:
        print(f"ERROR: Failed to query {table_name}: {e}")
        return pd.DataFrame()


def process_hostname_records(df, source_table):
    """
    Process DataFrame from BigQuery and extract normalized hostname records.
    
    Args:
        df: DataFrame from BigQuery table
        source_table: Name of the source table
        
    Returns:
        List of processed hostname records
    """
    if df.empty:
        return []
    
    records = []
    
    for _, row in df.iterrows():
        # Extract hostnames from hostname columns
        hostnames = []
        for col in df.columns:
            if col.startswith('hostname_') and pd.notna(row[col]) and str(row[col]).strip():
                hostnames.append(str(row[col]).strip())
        
        # Process each hostname
        for original_hostname in hostnames:
            normalized = normalize_hostname(original_hostname)
            
            if normalized:
                # Create record
                record = {
                    'normalized_host': normalized,
                    'original_hostname': original_hostname,
                    'source_table': source_table,
                    'collection_timestamp': row.get('collection_timestamp', datetime.datetime.now())
                }
                
                # Extract metadata
                for col in df.columns:
                    if '_' in col and not col.startswith('hostname_'):
                        if pd.notna(row[col]) and str(row[col]).strip():
                            record[col] = str(row[col]).strip()
                
                records.append(record)
    
    return records

# ============================================================================
# MASTER HOSTNAME INVENTORY CREATION
# ============================================================================

def create_master_hostname_inventory():
    """
    Main function that orchestrates the complete hostname inventory creation process.
    
    This function:
    1. Loads table mappings from reviewed_labeled_columns.json
    2. Authenticates to BigQuery  
    3. Queries each table to extract hostname data
    4. Normalizes hostnames and aggregates metadata
    5. Creates the master DuckDB with the final inventory
    """
    print("=" * 80)
    print("STARTING MASTER HOSTNAME INVENTORY CREATION")
    print("=" * 80)
    
    # Step 1: Load table mappings
    print("\nStep 1: Loading table mappings from JSON file...")
    table_mappings = load_table_mappings()
    
    if not table_mappings:
        print("ERROR: No table mappings loaded. Cannot proceed.")
        return False
    
    # Step 2: Verify BigQuery connection
    print(f"\nStep 2: Verifying BigQuery connection...")
    if not bq_client:
        print("ERROR: BigQuery client not initialized. Cannot proceed.")
        return False
    
    # Step 3: Process each table
    print(f"\nStep 3: Processing {len(table_mappings)} BigQuery tables...")
    all_records = []
    successful_tables = 0
    
    for i, (table_name, column_mappings) in enumerate(table_mappings.items(), 1):
        print(f"\n[{i}/{len(table_mappings)}] Processing: {table_name}")
        
        try:
            # Query BigQuery table
            df = collect_hostname_data_from_table(table_name, column_mappings)
            
            if not df.empty:
                # Process the data
                records = process_hostname_records(df, table_name)
                all_records.extend(records)
                successful_tables += 1
                print(f"✓ Extracted {len(records)} hostname records")
            else:
                print(f"⚠ No data retrieved from {table_name}")
                
        except Exception as e:
            print(f"✗ Failed to process {table_name}: {e}")
            continue
    
    print(f"\nProcessing complete:")
    print(f"  Tables processed successfully: {successful_tables}/{len(table_mappings)}")
    print(f"  Total hostname records collected: {len(all_records)}")
    
    if not all_records:
        print("ERROR: No hostname records collected. Cannot create inventory.")
        return False
    
    # Step 4: Aggregate and normalize
    print(f"\nStep 4: Aggregating hostnames and creating master inventory...")
    hostname_aggregation = defaultdict(lambda: {
        'normalized_host': '',
        'locations_across_bq': set(),
        'original_hostnames': set(),
        'metadata': defaultdict(set),
        'first_seen': None,
        'last_seen': None,
        'record_count': 0
    })
    
    # Aggregate all records by normalized hostname
    for record in all_records:
        normalized_host = record['normalized_host']
        agg = hostname_aggregation[normalized_host]
        
        # Core fields
        agg['normalized_host'] = normalized_host
        agg['locations_across_bq'].add(record['source_table'])
        agg['original_hostnames'].add(record['original_hostname'])
        agg['record_count'] += 1
        
        # Timestamps
        timestamp = record['collection_timestamp']
        if agg['first_seen'] is None or timestamp < agg['first_seen']:
            agg['first_seen'] = timestamp
        if agg['last_seen'] is None or timestamp > agg['last_seen']:
            agg['last_seen'] = timestamp
        
        # Metadata
        for key, value in record.items():
            if key not in ['normalized_host', 'original_hostname', 'source_table', 'collection_timestamp']:
                agg['metadata'][key].add(value)
    
    # Step 5: Create final DataFrame
    print(f"Step 5: Creating final master hostname inventory...")
    final_records = []
    
    for hostname, data in hostname_aggregation.items():
        record = {
            'host': data['normalized_host'],
            'locations_across_bq': ','.join(sorted(data['locations_across_bq'])),
            'original_hostnames': '|'.join(sorted(data['original_hostnames'])),
            'table_count': len(data['locations_across_bq']),
            'record_count': data['record_count'],
            'first_seen': data['first_seen'],
            'last_seen': data['last_seen']
        }
        
        # Add metadata fields
        for meta_key, meta_values in data['metadata'].items():
            if meta_values:
                record[meta_key] = ','.join(sorted(meta_values))
        
        final_records.append(record)
    
    # Step 6: Save to DuckDB
    print(f"Step 6: Saving master inventory to DuckDB...")
    master_df = pd.DataFrame(final_records)
    writeToLocalDB(master_df, "master_hostnames")
    
    # Create indexes
    try:
        db_path = os.path.join(file_path, "hostname_inventory.duckdb")
        conn = duckdb.connect(db_path)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_host ON master_hostnames(host)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_table_count ON master_hostnames(table_count)")
        conn.close()
        print("✓ Created database indexes")
    except Exception as e:
        print(f"⚠ Warning: Failed to create indexes: {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("MASTER HOSTNAME INVENTORY CREATION COMPLETE")
    print("=" * 80)
    print(f"✓ Unique normalized hostnames: {len(final_records)}")
    print(f"✓ Average tables per hostname: {master_df['table_count'].mean():.2f}")
    print(f"✓ Hostnames in multiple tables: {len(master_df[master_df['table_count'] > 1])}")
    print(f"✓ Database location: {os.path.join(file_path, 'hostname_inventory.duckdb')}")
    
    return True

# ============================================================================
# AUTHENTICATION (Same patterns as Log Lens)
# ============================================================================

def login_required(f):
    """Decorator to require user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "_logged_in_user" not in session:
            return redirect(url_for("login_page"), 302)
        return f(*args, **kwargs)
    return decorated_function


def roles_required(roles_required):
    """Decorator to require specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "_logged_in_user" not in session:
                return redirect(url_for("login"))
            
            user_roles = session["_logged_in_user"].get("roles", [])
            if not any(role in user_roles for role in roles_required):
                return "Access denied", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def logActivity(request, status_code, description):
    """Log user activities for audit purposes."""
    user_data = session.get("_logged_in_user", {})
    log_data = {
        "app": "HostnameNormalizer",
        "user": user_data.get('preferred_username', 'Unknown'),
        "action": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": status_code
    }
    # In production, send to Chronicle or other logging system
    print(f"AUDIT: {log_data}")

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def dashboard():
    """Main dashboard for hostname inventory."""
    logActivity(request, 200, "Accessed hostname normalizer dashboard")
    return send_from_directory('../client/dist', 'index.html')


@app.route('/api/stats')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def get_inventory_stats():
    """Get comprehensive statistics about the hostname inventory."""
    try:
        # Basic counts
        total_hosts = runLocalDBQuery("SELECT COUNT(*) as count FROM master_hostnames")[0]['count']
        multi_table_hosts = runLocalDBQuery("SELECT COUNT(*) as count FROM master_hostnames WHERE table_count > 1")[0]['count']
        
        # Coverage stats
        avg_tables = runLocalDBQuery("SELECT AVG(table_count) as avg FROM master_hostnames")[0]['avg']
        max_tables = runLocalDBQuery("SELECT MAX(table_count) as max FROM master_hostnames")[0]['max']
        
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
            'avg_table_coverage': round(avg_tables, 2),
            'max_table_coverage': max_tables,
            'top_tables': top_tables
        }
        
        logActivity(request, 200, "Retrieved inventory statistics")
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        logActivity(request, 500, f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500


@app.route('/api/search')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def search_hostnames():
    """Search the hostname inventory."""
    try:
        search_term = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit
        
        if search_term:
            query = f"""
            SELECT 
                host,
                locations_across_bq,
                table_count,
                record_count,
                original_hostnames
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
            query = f"""
            SELECT 
                host,
                locations_across_bq,
                table_count,
                record_count,
                original_hostnames
            FROM master_hostnames
            ORDER BY table_count DESC, record_count DESC
            LIMIT {limit} OFFSET {offset}
            """
            count_query = "SELECT COUNT(*) as total FROM master_hostnames"
        
        results = runLocalDBQuery(query)
        total = runLocalDBQuery(count_query)[0]['total']
        
        response_data = {
            'results': results,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }
        
        logActivity(request, 200, f"Searched hostnames: '{search_term}'")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Search error: {e}")
        logActivity(request, 500, f"Search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@app.route('/api/hostname/<hostname>')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def get_hostname_details(hostname):
    """Get detailed information about a specific hostname."""
    try:
        query = "SELECT * FROM master_hostnames WHERE host = ?"
        results = runLocalDBQuery(query, [hostname.lower()])
        
        if results:
            result = results[0]
            # Parse comma/pipe separated fields
            result['locations_list'] = result['locations_across_bq'].split(',')
            result['original_hostnames_list'] = result['original_hostnames'].split('|') if result['original_hostnames'] else []
            
            logActivity(request, 200, f"Retrieved hostname details: {hostname}")
            return jsonify(result)
        else:
            logActivity(request, 404, f"Hostname not found: {hostname}")
            return jsonify({'error': 'Hostname not found'}), 404
            
    except Exception as e:
        print(f"Error getting hostname details: {e}")
        logActivity(request, 500, f"Error getting hostname details: {e}")
        return jsonify({'error': 'Failed to get hostname details'}), 500


@app.route('/api/export')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def export_inventory():
    """Export complete hostname inventory to CSV."""
    try:
        query = "SELECT * FROM master_hostnames ORDER BY table_count DESC, record_count DESC"
        data = runLocalDBQuery(query)
        df = pd.DataFrame(data)
        
        csv_data = StringIO()
        df.to_csv(csv_data, index=False)
        csv_data.seek(0)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hostname_inventory_{timestamp}.csv"
        
        logActivity(request, 200, "Exported hostname inventory")
        return Response(
            csv_data.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"Export error: {e}")
        logActivity(request, 500, f"Export error: {e}")
        return jsonify({'error': 'Export failed'}), 500


@app.route('/api/refresh', methods=['POST'])
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def refresh_inventory():
    """Trigger a manual refresh of the hostname inventory."""
    try:
        # Start refresh in background
        threading.Thread(target=run_inventory_refresh_background).start()
        
        logActivity(request, 202, "Started hostname inventory refresh")
        return jsonify({
            'message': 'Hostname inventory refresh started in background',
            'status': 'started'
        }), 202
        
    except Exception as e:
        print(f"Refresh error: {e}")
        logActivity(request, 500, f"Refresh error: {e}")
        return jsonify({'error': 'Failed to start refresh'}), 500

# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================

def run_inventory_refresh_background():
    """Run hostname inventory creation in background thread."""
    print("Starting background hostname inventory refresh...")
    try:
        success = create_master_hostname_inventory()
        if success:
            print("✓ Background hostname inventory refresh completed successfully")
        else:
            print("✗ Background hostname inventory refresh failed")
    except Exception as e:
        print(f"✗ Background hostname inventory refresh error: {e}")

# ============================================================================
# SCHEDULED TASKS
# ============================================================================

# Schedule hostname inventory refresh every 8 hours
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=create_master_hostname_inventory,
    trigger=CronTrigger(hour='*/8'),  # Every 8 hours
    id='hostname_inventory_refresh',
    name='Hostname Inventory Refresh',
    replace_existing=True
)
scheduler.start()

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    """Application entry point."""
    
    print("=" * 80)
    print("HOSTNAME NORMALIZER APPLICATION STARTING")
    print("=" * 80)
    
    # Verify required files
    required_files = [
        "reviewed_labeled_columns.json",
        "gcp_prod_key.json"
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path_check = os.path.join(file_path, file_name)
        if not os.path.exists(file_path_check):
            missing_files.append(file_name)
    
    if missing_files:
        print("ERROR: Missing required files:")
        for missing_file in missing_files:
            print(f"  - {missing_file}")
        print("\nPlease ensure all required files are in the application directory")
        exit(1)
    
    # Start initial inventory creation in background
    print("Starting initial hostname inventory creation...")
    threading.Thread(target=run_inventory_refresh_background).start()
    
    # Start Flask application
    print("Starting Flask web server on http://localhost:5001")
    app.run(debug=False, host='0.0.0.0', port=5001)