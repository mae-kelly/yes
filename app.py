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
    settings = {}

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
# BIGQUERY AUTHENTICATION
# ============================================================================

def initialize_bigquery_client():
    """
    Initialize BigQuery client with service account authentication.
    
    Returns:
        Authenticated BigQuery client
    """
    try:
        service_account_file = os.path.join(file_path, "gcp_prod_key.json")
        
        if not os.path.exists(service_account_file):
            print(f"ERROR: Service account file not found: {service_account_file}")
            return None
        
        print("Authenticating to BigQuery...")
        credentials = service_account.Credentials.from_service_account_file(service_account_file)
        client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        
        # Test connection
        test_query = "SELECT 1 as test LIMIT 1"
        list(client.query(test_query).result())
        
        print("✓ BigQuery authentication successful")
        return client
        
    except Exception as e:
        print(f"ERROR: BigQuery authentication failed: {e}")
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
        df: Pandas DataFrame
        table_name: Name of table to create
    """
    try:
        db_path = os.path.join(file_path, "hostname_inventory.duckdb")
        conn = duckdb.connect(db_path)
        
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.register("temp_df", df)
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df")
        conn.close()
        
        print(f"✓ Saved {len(df)} records to {table_name}")
        
    except Exception as e:
        print(f"ERROR: Failed to save to database: {e}")


def runLocalDBQuery(query, params=None):
    """
    Execute SQL query against hostname inventory DuckDB.
    
    Args:
        query: SQL query string
        params: Optional query parameters
        
    Returns:
        List of dictionaries with results
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
        print(f"ERROR: Query failed: {e}")
        return []

# ============================================================================
# JSON MAPPING PROCESSING
# ============================================================================

def loadTableMappings():
    """
    Load reviewed_labeled_columns.json and extract table/column mappings.
    
    Returns:
        Dictionary of tables that have hostname columns (label="host")
        
    The JSON format is:
    {
      "table_name": {
        "COLUMN_NAME": "label",  // e.g. "ENDPOINT_NAME": "host"
        "OTHER_COL": "domain"    // e.g. "DOMAIN_NAME": "domain"
      }
    }
    """
    try:
        json_file = os.path.join(file_path, "reviewed_labeled_columns.json")
        
        if not os.path.exists(json_file):
            print(f"ERROR: {json_file} not found!")
            return {}
        
        print(f"Loading table mappings from: {json_file}")
        
        with open(json_file, 'r') as f:
            all_mappings = json.load(f)
        
        # Filter to only tables with hostname columns
        hostname_tables = {}
        total_hostname_columns = 0
        
        for table_name, column_mappings in all_mappings.items():
            if isinstance(column_mappings, dict):
                # Find columns labeled as "host"
                hostname_cols = [col for col, label in column_mappings.items() if label == "host"]
                
                if hostname_cols:
                    hostname_tables[table_name] = column_mappings
                    total_hostname_columns += len(hostname_cols)
                    print(f"✓ {table_name}: {hostname_cols}")
        
        print(f"\n*** SUMMARY ***")
        print(f"Total tables in JSON: {len(all_mappings)}")
        print(f"Tables with hostname columns: {len(hostname_tables)}")
        print(f"Total hostname columns: {total_hostname_columns}")
        
        return hostname_tables
        
    except Exception as e:
        print(f"ERROR: Failed to load JSON mappings: {e}")
        return {}

# ============================================================================
# HOSTNAME NORMALIZATION
# ============================================================================

def normalizeHostname(hostname):
    """
    Normalize hostname using comprehensive rules.
    
    Args:
        hostname: Original hostname
        
    Returns:
        Normalized hostname or None if invalid
    """
    if not hostname or pd.isna(hostname):
        return None
    
    normalized = str(hostname).strip().lower()
    
    # Skip IP addresses
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', normalized):
        return None
    
    # Skip if invalid length
    if len(normalized) < 2 or len(normalized) > 63:
        return None
    
    # Apply normalization rules
    # Remove domain suffix (everything after first dot)
    normalized = re.sub(r'^([^.]+)\..*$', r'\1', normalized)
    
    # Remove hyphens and underscores
    normalized = re.sub(r'[-_]', '', normalized)
    
    # Remove common prefixes
    normalized = re.sub(r'^(host|server|srv|ws|pc|desktop|laptop)', '', normalized)
    
    # Remove environment suffixes
    normalized = re.sub(r'(prod|dev|test|stage|staging|qa)$', '', normalized)
    
    # Remove leading zeros from numbers
    normalized = re.sub(r'^([a-zA-Z]+)0+(\d+)$', r'\1\2', normalized)
    
    # Keep only alphanumeric
    normalized = re.sub(r'[^a-zA-Z0-9]', '', normalized)
    
    # Final validation
    if not normalized or len(normalized) < 2:
        return None
    
    return normalized

# ============================================================================
# BIGQUERY DATA COLLECTION
# ============================================================================

def collectHostnamesFromTable(table_name, column_mappings):
    """
    Query BigQuery table to collect hostname data.
    
    Args:
        table_name: BigQuery table name (project.dataset.table)
        column_mappings: Dictionary mapping columns to labels
        
    Returns:
        DataFrame with hostname data
    """
    if not bq_client:
        print(f"ERROR: BigQuery client not available for {table_name}")
        return pd.DataFrame()
    
    try:
        print(f"Querying BigQuery table: {table_name}")
        
        # Find hostname columns (where label = "host")
        hostname_columns = []
        metadata_columns = []
        select_clauses = []
        
        for column_name, label in column_mappings.items():
            if label == "host":
                hostname_columns.append(column_name)
                select_clauses.append(f"CAST({column_name} AS STRING) as {column_name}")
            elif label in ["domain", "region", "business_unit", "infrastructure_type", 
                          "system_classification", "app", "application", "country", "platform", "ip"]:
                metadata_columns.append((column_name, label))
                select_clauses.append(f"CAST({column_name} AS STRING) as {column_name}")
        
        if not hostname_columns:
            print(f"No hostname columns in {table_name}")
            return pd.DataFrame()
        
        # Build WHERE clause for non-null hostnames
        where_conditions = []
        for col in hostname_columns:
            where_conditions.append(f"{col} IS NOT NULL AND TRIM(CAST({col} AS STRING)) != ''")
        
        # Construct BigQuery SQL
        sql = f"""
        SELECT DISTINCT
            {', '.join(select_clauses)}
        FROM `{table_name}`
        WHERE {' OR '.join(where_conditions)}
        LIMIT 100000
        """
        
        print(f"Executing query on {table_name}...")
        
        # Execute BigQuery
        job = bq_client.query(sql)
        df = job.to_dataframe()
        
        # Add source tracking
        df['source_table'] = table_name
        df['hostname_columns'] = '|'.join(hostname_columns)
        
        print(f"✓ Retrieved {len(df)} rows from {table_name}")
        return df
        
    except Exception as e:
        print(f"ERROR: Failed to query {table_name}: {e}")
        return pd.DataFrame()

# ============================================================================
# MASTER HOSTNAME INVENTORY CREATION
# ============================================================================

def gatherAllHostnames():
    """
    Main function to create comprehensive hostname inventory.
    
    This function:
    1. Loads table mappings from reviewed_labeled_columns.json
    2. Queries each BigQuery table with hostname columns
    3. Normalizes all hostnames
    4. Creates master DuckDB with aggregated results
    """
    print("=" * 80)
    print("CREATING MASTER HOSTNAME INVENTORY")
    print("=" * 80)
    
    # Step 1: Load JSON mappings
    print("\nStep 1: Loading table mappings...")
    table_mappings = loadTableMappings()
    
    if not table_mappings:
        print("ERROR: No table mappings found")
        return False
    
    # Step 2: Process each table
    print(f"\nStep 2: Processing {len(table_mappings)} tables...")
    all_hostname_records = []
    
    for i, (table_name, column_mappings) in enumerate(table_mappings.items(), 1):
        print(f"\n[{i}/{len(table_mappings)}] {table_name}")
        
        # Query this table
        df = collectHostnamesFromTable(table_name, column_mappings)
        
        if not df.empty:
            # Process each row to extract hostnames
            hostname_columns = [col for col, label in column_mappings.items() if label == "host"]
            
            for _, row in df.iterrows():
                for hostname_col in hostname_columns:
                    if pd.notna(row.get(hostname_col)) and str(row[hostname_col]).strip():
                        original_hostname = str(row[hostname_col]).strip()
                        normalized = normalizeHostname(original_hostname)
                        
                        if normalized:
                            record = {
                                'normalized_host': normalized,
                                'original_hostname': original_hostname,
                                'source_table': table_name,
                                'source_column': hostname_col
                            }
                            
                            # Add metadata
                            for col_name, label in column_mappings.items():
                                if label != "host" and pd.notna(row.get(col_name)):
                                    record[f"meta_{label}"] = str(row[col_name]).strip()
                            
                            all_hostname_records.append(record)
            
            print(f"  ✓ Processed {len([r for r in all_hostname_records if r['source_table'] == table_name])} hostnames")
        else:
            print(f"  ⚠ No data retrieved")
    
    if not all_hostname_records:
        print("ERROR: No hostname records collected")
        return False
    
    print(f"\nStep 3: Aggregating {len(all_hostname_records)} hostname records...")
    
    # Step 3: Aggregate by normalized hostname
    aggregated = defaultdict(lambda: {
        'normalized_host': '',
        'locations_across_bq': set(),
        'original_hostnames': set(),
        'source_columns': set(),
        'metadata': defaultdict(set),
        'record_count': 0
    })
    
    for record in all_hostname_records:
        normalized = record['normalized_host']
        agg = aggregated[normalized]
        
        agg['normalized_host'] = normalized
        agg['locations_across_bq'].add(record['source_table'])
        agg['original_hostnames'].add(record['original_hostname'])
        agg['source_columns'].add(f"{record['source_table']}:{record['source_column']}")
        agg['record_count'] += 1
        
        # Aggregate metadata
        for key, value in record.items():
            if key.startswith('meta_') and value:
                agg['metadata'][key].add(value)
    
    # Step 4: Create final records
    print("Step 4: Creating final master hostname inventory...")
    final_records = []
    
    for hostname, data in aggregated.items():
        record = {
            'host': data['normalized_host'],
            'locations_across_bq': ','.join(sorted(data['locations_across_bq'])),
            'original_hostnames': '|'.join(sorted(data['original_hostnames'])),
            'source_columns': '|'.join(sorted(data['source_columns'])),
            'table_count': len(data['locations_across_bq']),
            'record_count': data['record_count']
        }
        
        # Add metadata
        for meta_key, meta_values in data['metadata'].items():
            record[meta_key] = ','.join(sorted(meta_values))
        
        final_records.append(record)
    
    # Step 5: Save to DuckDB
    print("Step 5: Saving to DuckDB...")
    master_df = pd.DataFrame(final_records)
    writeToLocalDB(master_df, "master_hostnames")
    
    # Create indexes
    try:
        db_path = os.path.join(file_path, "hostname_inventory.duckdb")
        conn = duckdb.connect(db_path)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_host ON master_hostnames(host)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_table_count ON master_hostnames(table_count)")
        conn.close()
    except:
        pass
    
    print("\n" + "=" * 80)
    print("HOSTNAME INVENTORY CREATION COMPLETE")
    print("=" * 80)
    print(f"✓ Unique normalized hostnames: {len(final_records)}")
    print(f"✓ Average tables per hostname: {master_df['table_count'].mean():.2f}")
    print(f"✓ Hostnames in multiple tables: {len(master_df[master_df['table_count'] > 1])}")
    
    return True

# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def login_required(f):
    """Require user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "_logged_in_user" not in session:
            return redirect(url_for("login_page"), 302)
        return f(*args, **kwargs)
    return decorated_function


def roles_required(roles_required):
    """Require specific user roles."""
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
    """Log user activity."""
    user_data = session.get("_logged_in_user", {})
    print(f"AUDIT: {user_data.get('preferred_username', 'Unknown')} - {description} - {status_code}")

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def dashboard():
    """Main dashboard page."""
    logActivity(request, 200, "Accessed hostname dashboard")
    return send_from_directory('../client/dist', 'index.html')


@app.route('/getStats')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def getStats(context=None):
    """Get hostname inventory statistics."""
    try:
        # Basic stats
        total_query = "SELECT COUNT(*) as total FROM master_hostnames"
        total_result = runLocalDBQuery(total_query)
        total_hostnames = total_result[0]['total'] if total_result else 0
        
        # Multi-table hostnames
        multi_query = "SELECT COUNT(*) as multi FROM master_hostnames WHERE table_count > 1"
        multi_result = runLocalDBQuery(multi_query)
        multi_table_hostnames = multi_result[0]['multi'] if multi_result else 0
        
        # Coverage stats
        coverage_query = """
        SELECT 
            AVG(table_count) as avg_tables,
            MAX(table_count) as max_tables,
            MIN(table_count) as min_tables
        FROM master_hostnames
        """
        coverage_result = runLocalDBQuery(coverage_query)
        coverage = coverage_result[0] if coverage_result else {}
        
        # Top tables
        table_query = """
        SELECT 
            unnest(string_split(locations_across_bq, ',')) as table_name,
            COUNT(*) as hostname_count
        FROM master_hostnames
        GROUP BY table_name
        ORDER BY hostname_count DESC
        LIMIT 10
        """
        top_tables = runLocalDBQuery(table_query)
        
        stats = {
            'total_hostnames': total_hostnames,
            'multi_table_hostnames': multi_table_hostnames,
            'single_table_hostnames': total_hostnames - multi_table_hostnames,
            'avg_table_coverage': round(coverage.get('avg_tables', 0), 2),
            'max_table_coverage': coverage.get('max_tables', 0),
            'min_table_coverage': coverage.get('min_tables', 0),
            'top_tables': top_tables
        }
        
        response = json.dumps(stats), 200
        logActivity(request, response[1], "Retrieved hostname statistics")
        return response
        
    except Exception as e:
        print(f"Stats error: {e}")
        response = json.dumps({'error': str(e)}), 500
        logActivity(request, response[1], "Error getting statistics")
        return response


@app.route('/searchHostnames')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def searchHostnames(context=None):
    """Search hostname inventory."""
    try:
        search_term = request.args.get('term', '').strip()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit
        
        if search_term:
            query = f"""
            SELECT 
                host,
                locations_across_bq,
                original_hostnames,
                table_count,
                record_count
            FROM master_hostnames
            WHERE 
                host LIKE '%{search_term.lower()}%'
                OR locations_across_bq LIKE '%{search_term}%'
                OR original_hostnames LIKE '%{search_term}%'
            ORDER BY table_count DESC, record_count DESC
            LIMIT {limit} OFFSET {offset}
            """
            
            count_query = f"""
            SELECT COUNT(*) as total FROM master_hostnames
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
                original_hostnames,
                table_count,
                record_count
            FROM master_hostnames
            ORDER BY table_count DESC, record_count DESC
            LIMIT {limit} OFFSET {offset}
            """
            count_query = "SELECT COUNT(*) as total FROM master_hostnames"
        
        results = runLocalDBQuery(query)
        count_result = runLocalDBQuery(count_query)
        total = count_result[0]['total'] if count_result else 0
        
        response_data = {
            'results': results,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit if total > 0 else 0
            },
            'search_term': search_term
        }
        
        response = json.dumps(response_data), 200
        logActivity(request, response[1], f"Searched hostnames: {search_term}")
        return response
        
    except Exception as e:
        print(f"Search error: {e}")
        response = json.dumps({'error': str(e)}), 500
        logActivity(request, response[1], "Search error")
        return response


@app.route('/exportHostnames')
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def exportHostnames(context=None):
    """Export hostname inventory to CSV."""
    try:
        query = "SELECT * FROM master_hostnames ORDER BY table_count DESC, record_count DESC"
        data = runLocalDBQuery(query)
        
        if not data:
            return json.dumps({'error': 'No data to export'}), 404
        
        df = pd.DataFrame(data)
        csv_data = StringIO()
        df.to_csv(csv_data, index=False)
        csv_data.seek(0)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hostname_inventory_{timestamp}.csv"
        
        response = Response(
            csv_data.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        ), 200
        
        logActivity(request, response[1], "Exported hostname inventory")
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        response = json.dumps({'error': str(e)}), 500
        logActivity(request, response[1], "Export error")
        return response


@app.route('/refreshInventory', methods=['POST'])
@auth.login_required
@roles_required(['admin', 'hostname_admin'])
def refreshInventory(context=None):
    """Trigger manual hostname inventory refresh."""
    try:
        threading.Thread(target=runHostnameCollectionBackground).start()
        
        response = json.dumps({
            'message': 'Hostname inventory refresh started',
            'status': 'started'
        }), 202
        
        logActivity(request, response[1], "Started manual inventory refresh")
        return response
        
    except Exception as e:
        print(f"Refresh error: {e}")
        response = json.dumps({'error': str(e)}), 500
        logActivity(request, response[1], "Refresh error")
        return response

# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================

def runHostnameCollectionBackground():
    """Run hostname collection in background thread."""
    print("Starting background hostname collection...")
    try:
        success = gatherAllHostnames()
        if success:
            print("✓ Background hostname collection completed")
        else:
            print("✗ Background hostname collection failed")
    except Exception as e:
        print(f"✗ Background collection error: {e}")


def log_task(log_data):
    """Background logging task."""
    try:
        # In production, send to Chronicle
        headers = {
            "x-goog-api-key": os.getenv("CHRONICLE_API_KEY"),
            "x-webhook-access-key": os.getenv("CHRONICLE_SECRET_KEY"),
            "Content-Type": "application/json"
        }
        
        if headers["x-goog-api-key"]:
            response = requests.post(os.getenv("CHRONICLE_ENDPOINT"), headers=headers, json=log_data)
            response.raise_for_status()
    except Exception as e:
        print(f"Logging error: {e}")

# ============================================================================
# SCHEDULED TASKS
# ============================================================================

# Schedule hostname collection every 8 hours
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=gatherAllHostnames,
    trigger=CronTrigger(hour='*/8'),
    id='hostname_collection',
    name='Hostname Inventory Collection'
)
scheduler.start()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_cache():
    """Clear hostname inventory cache."""
    try:
        db_path = os.path.join(file_path, "hostname_inventory.duckdb")
        if os.path.exists(db_path):
            conn = duckdb.connect(db_path)
            conn.execute("DROP TABLE IF EXISTS master_hostnames")
            conn.close()
            print("✓ Cleared hostname cache")
    except Exception as e:
        print(f"Cache clear error: {e}")

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    """Application entry point."""
    
    print("=" * 80)
    print("HOSTNAME NORMALIZER APPLICATION")
    print("=" * 80)
    
    # Check required files
    required_files = ["reviewed_labeled_columns.json", "gcp_prod_key.json"]
    missing_files = []
    
    for file_name in required_files:
        if not os.path.exists(os.path.join(file_path, file_name)):
            missing_files.append(file_name)
    
    if missing_files:
        print("ERROR: Missing required files:")
        for missing in missing_files:
            print(f"  - {missing}")
        print("\nPlace these files in the application directory and restart.")
        exit(1)
    
    # Verify BigQuery connection
    if not bq_client:
        print("ERROR: Could not initialize BigQuery client")
        exit(1)
    
    # Start initial collection
    print("Starting initial hostname inventory collection...")
    threading.Thread(target=runHostnameCollectionBackground).start()
    
    # Start Flask server
    print("Starting Flask server on http://localhost:5001")
    print("=" * 80)
    app.run(debug=False, host='0.0.0.0', port=5001)