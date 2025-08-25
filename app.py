# /src/app.py

from flask import Flask, jsonify, request, render_template
import duckdb
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import os
from typing import Dict, List, Any

app = Flask(__name__)

# Database configuration
DB_PATH = 'data/universal_cmdb.duckdb'

def get_db_connection():
    """Create and return a DuckDB connection."""
    try:
        return duckdb.connect(DB_PATH)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """Execute a query and return results as a list of dictionaries."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        if params:
            result = conn.execute(query, params).fetchall()
        else:
            result = conn.execute(query).fetchall()
        
        # Get column names
        columns = [desc[0] for desc in conn.description]
        
        # Convert to list of dictionaries
        data = [dict(zip(columns, row)) for row in result]
        
        conn.close()
        return data
        
    except Exception as e:
        print(f"Query execution error: {e}")
        conn.close()
        return []

def execute_single_query(query: str, params: tuple = None) -> Dict:
    """Execute a query and return a single result as a dictionary."""
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        if params:
            result = conn.execute(query, params).fetchone()
        else:
            result = conn.execute(query).fetchone()
        
        if result:
            columns = [desc[0] for desc in conn.description]
            data = dict(zip(columns, result))
        else:
            data = {}
        
        conn.close()
        return data
        
    except Exception as e:
        print(f"Single query execution error: {e}")
        conn.close()
        return {}

@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')

@app.route('/api/overall-coverage-totals')
def get_overall_coverage_totals():
    """Get overall coverage statistics for all monitoring tools."""
    query = """
    SELECT 
        COUNT(*) as total_hosts,
        COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as total_splunk_logging,
        ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_coverage_pct,
        COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as total_cmdb_present,
        ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_coverage_pct,
        COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as total_crowdstrike,
        ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_coverage_pct,
        COUNT(CASE WHEN LOWER(tanium_coverage) LIKE '%tanium%' THEN 1 END) as total_tanium,
        ROUND(COUNT(CASE WHEN LOWER(tanium_coverage) LIKE '%tanium%' THEN 1 END) * 100.0 / COUNT(*), 2) as tanium_coverage_pct,
        COUNT(CASE WHEN LOWER(apm) LIKE '%apm%' THEN 1 END) as total_apm,
        ROUND(COUNT(CASE WHEN LOWER(apm) LIKE '%apm%' THEN 1 END) * 100.0 / COUNT(*), 2) as apm_coverage_pct
    FROM universal_cmdb_copy2
    """
    
    data = execute_single_query(query)
    
    # Add AI predictions if service is available
    try:
        ai_response = requests.get('http://localhost:5001/api/predict-missing-visibility', timeout=2)
        if ai_response.status_code == 200:
            predicted_assets = ai_response.json()
            data['ai_predicted_missing'] = len(predicted_assets)
            data['high_risk_predictions'] = len([p for p in predicted_assets if p.get('visibility_risk_score', 0) > 0.8])
        else:
            data['ai_predicted_missing'] = 0
            data['high_risk_predictions'] = 0
    except:
        data['ai_predicted_missing'] = 0
        data['high_risk_predictions'] = 0
    
    return jsonify(data)

@app.route('/api/domain-analysis')
def get_domain_analysis():
    """Analyze coverage by domain (1DC and FEAD)."""
    query = """
    SELECT 
        '1DC Domain Analysis' as analysis_type,
        COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END) as total_hosts,
        COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND logging_in_splunk = 'yes' THEN 1 END) as splunk_covered,
        COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND present_in_cmdb = 'yes' THEN 1 END) as cmdb_covered,
        COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_covered,
        ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND logging_in_splunk = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END), 0), 2) as splunk_pct,
        ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND present_in_cmdb = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END), 0), 2) as cmdb_pct
    FROM universal_cmdb_copy2
    
    UNION ALL
    
    SELECT 
        'FEAD Domain Analysis' as analysis_type,
        COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END) as total_hosts,
        COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND logging_in_splunk = 'yes' THEN 1 END) as splunk_covered,
        COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND present_in_cmdb = 'yes' THEN 1 END) as cmdb_covered,
        COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_covered,
        ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND logging_in_splunk = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END), 0), 2) as splunk_pct,
        ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND present_in_cmdb = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END), 0), 2) as cmdb_pct
    FROM universal_cmdb_copy2
    """
    
    data = execute_query(query)
    return jsonify(data)

@app.route('/api/regional-analysis')
def get_regional_analysis():
    """Get coverage analysis by geographical region."""
    query = """
    SELECT 
        CASE 
            WHEN LOWER(region) LIKE '%north america%' OR LOWER(region) LIKE '%usa%' OR LOWER(region) LIKE '%us%' THEN 'North America'
            WHEN LOWER(region) LIKE '%latam%' OR LOWER(region) LIKE '%latin%' OR LOWER(region) LIKE '%south america%' THEN 'LATAM'
            WHEN LOWER(region) LIKE '%emea%' OR LOWER(region) LIKE '%europe%' OR LOWER(region) LIKE '%africa%' OR LOWER(region) LIKE '%middle east%' THEN 'EMEA'
            WHEN LOWER(region) LIKE '%apac%' OR LOWER(region) LIKE '%asia%' OR LOWER(region) LIKE '%pacific%' THEN 'APAC'
            ELSE COALESCE(region, 'Unknown')
        END as standardized_region,
        COUNT(*) as total_hosts_region,
        COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_covered_region,
        ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_region_pct,
        COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_covered_region,
        ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_region_pct,
        COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_covered_region,
        ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_region_pct
    FROM universal_cmdb_copy2
    GROUP BY standardized_region
    ORDER BY total_hosts_region DESC
    """
    
    data = execute_query(query)
    return jsonify(data)

@app.route('/api/cio-analysis')
def get_cio_analysis():
    """Get coverage analysis by CIO organization."""
    query = """
    SELECT 
        cio,
        COUNT(*) as total_hosts_cio,
        COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_coverage_cio,
        COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_coverage_cio,
        COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_coverage_cio,
        ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_cio_pct,
        ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_cio_pct,
        ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_cio_pct
    FROM universal_cmdb_copy2
    WHERE cio IS NOT NULL 
        AND TRIM(cio) != '' 
        AND regexp_matches(cio, '^[A-Za-z ]+$')
    GROUP BY cio
    ORDER BY total_hosts_cio DESC
    """
    
    data = execute_query(query)
    return jsonify(data)

@app.route('/api/business-unit-analysis')
def get_business_unit_analysis():
    """Get coverage analysis by business unit."""
    query = """
    SELECT 
        TRIM(business_unit) as business_unit_clean,
        COUNT(*) as total_hosts_bu,
        COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_coverage_bu,
        COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_coverage_bu,
        COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_coverage_bu,
        ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_bu_pct,
        ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_bu_pct,
        ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_bu_pct
    FROM universal_cmdb_copy2
    WHERE business_unit IS NOT NULL AND TRIM(business_unit) != ''
    GROUP BY TRIM(business_unit)
    ORDER BY total_hosts_bu DESC
    """
    
    data = execute_query(query)
    return jsonify(data)

@app.route('/api/system-classification-analysis')
def get_system_classification_analysis():
    """Get coverage analysis by system classification."""
    query = """
    SELECT 
        TRIM(system_classification) as system_class_clean,
        COUNT(*) as total_hosts_class,
        COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_coverage_class,
        COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_coverage_class,
        COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_coverage_class,
        COUNT(CASE WHEN LOWER(tanium_coverage) LIKE '%tanium%' THEN 1 END) as tanium_coverage_class,
        COUNT(CASE WHEN LOWER(dlp_agent_coverage) LIKE '%dlp%' THEN 1 END) as dlp_coverage_class,
        ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_class_pct,
        ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_class_pct,
        ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_class_pct,
        ROUND(COUNT(CASE WHEN LOWER(tanium_coverage) LIKE '%tanium%' THEN 1 END) * 100.0 / COUNT(*), 2) as tanium_class_pct,
        ROUND(COUNT(CASE WHEN LOWER(dlp_agent_coverage) LIKE '%dlp%' THEN 1 END) * 100.0 / COUNT(*), 2) as dlp_class_pct
    FROM universal_cmdb_copy2
    WHERE system_classification IS NOT NULL AND TRIM(system_classification) != ''
    GROUP BY TRIM(system_classification)
    ORDER BY total_hosts_class DESC
    """
    
    data = execute_query(query)
    return jsonify(data)

@app.route('/api/log-type-visibility')
def get_log_type_visibility():
    """Get visibility analysis by predicted log type."""
    query = """
    SELECT 
        CASE 
            WHEN LOWER(system_classification) LIKE '%firewall%' OR LOWER(fqdn) LIKE '%fw%' THEN 'Firewall Traffic'
            WHEN LOWER(system_classification) LIKE '%server%' THEN 'OS logs'
            WHEN LOWER(system_classification) LIKE '%cloud%' OR LOWER(infrastructure_type) LIKE '%cloud%' THEN 'Cloud Event'
            WHEN LOWER(fqdn) LIKE '%web%' OR LOWER(fqdn) LIKE '%www%' THEN 'Web Logs'
            WHEN LOWER(system_classification) LIKE '%auth%' OR LOWER(fqdn) LIKE '%auth%' THEN 'Authentication attempts'
            WHEN LOWER(system_classification) LIKE '%database%' OR LOWER(fqdn) LIKE '%db%' THEN 'Theom'
            WHEN LOWER(system_classification) LIKE '%network%' OR LOWER(fqdn) LIKE '%ndr%' THEN 'NDR'
            WHEN LOWER(system_classification) LIKE '%endpoint%' OR LOWER(system_classification) LIKE '%workstation%' THEN 'EDR'
            ELSE 'Other'
        END as predicted_log_type,
        COUNT(*) as total_assets,
        COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_visibility,
        COUNT(CASE WHEN logging_in_gso = 'yes' THEN 1 END) as gso_visibility,
        ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_coverage_pct,
        ROUND(COUNT(CASE WHEN logging_in_gso = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as gso_coverage_pct
    FROM universal_cmdb_copy2
    GROUP BY predicted_log_type
    ORDER BY total_assets DESC
    """
    
    data = execute_query(query)
    return jsonify(data)

@app.route('/api/visibility-factor-metrics')
def get_visibility_factor_metrics():
    """Get various visibility factor metrics."""
    query = """
    SELECT 
        'Host Parity Coverage' as metric_type,
        COUNT(*) as total_hosts,
        COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_mapped_hosts,
        ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as host_parity_pct
    FROM universal_cmdb_copy2
    
    UNION ALL
    
    SELECT 
        'URL/FQDN Coverage' as metric_type,
        COUNT(CASE WHEN fqdn IS NOT NULL AND fqdn != '' THEN 1 END) as total_with_fqdn,
        COUNT(CASE WHEN fqdn IS NOT NULL AND fqdn != '' AND logging_in_splunk = 'yes' THEN 1 END) as fqdn_logged,
        ROUND(COUNT(CASE WHEN fqdn IS NOT NULL AND fqdn != '' AND logging_in_splunk = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN fqdn IS NOT NULL AND fqdn != '' THEN 1 END), 0), 2) as url_fqdn_coverage_pct
    FROM universal_cmdb_copy2
    
    UNION ALL
    
    SELECT 
        'Security Control Coverage' as metric_type,
        COUNT(*) as total_assets,
        COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' 
                    OR LOWER(tanium_coverage) LIKE '%tanium%' 
                    OR LOWER(dlp_agent_coverage) LIKE '%dlp%' THEN 1 END) as security_covered,
        ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' 
                          OR LOWER(tanium_coverage) LIKE '%tanium%' 
                          OR LOWER(dlp_agent_coverage) LIKE '%dlp%' THEN 1 END) * 100.0 / COUNT(*), 2) as security_coverage_pct
    FROM universal_cmdb_copy2
    """
    
    data = execute_query(query)
    return jsonify(data)

@app.route('/api/search-assets')
def search_assets():
    """Search for assets based on query parameters."""
    search_term = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100 results
    
    if not search_term:
        return jsonify([])
    
    query = """
    SELECT 
        fqdn,
        business_unit,
        system_classification,
        region,
        logging_in_splunk,
        present_in_cmdb,
        edr_coverage,
        data_quality_score
    FROM universal_cmdb_copy2
    WHERE LOWER(fqdn) LIKE LOWER(?) 
       OR LOWER(business_unit) LIKE LOWER(?)
       OR LOWER(system_classification) LIKE LOWER(?)
    ORDER BY data_quality_score DESC, fqdn ASC
    LIMIT ?
    """
    
    search_pattern = f'%{search_term}%'
    data = execute_query(query, (search_pattern, search_pattern, search_pattern, limit))
    return jsonify(data)

@app.route('/api/asset-details/<asset_id>')
def get_asset_details(asset_id):
    """Get detailed information about a specific asset."""
    query = """
    SELECT *
    FROM universal_cmdb_copy2
    WHERE fqdn = ?
    LIMIT 1
    """
    
    data = execute_single_query(query, (asset_id,))
    if not data:
        return jsonify({'error': 'Asset not found'}), 404
    
    return jsonify(data)

# AI Integration Endpoints
@app.route('/api/ai-visibility-insights')
def get_ai_visibility_insights():
    """Get AI-generated visibility insights."""
    try:
        ai_response = requests.get('http://localhost:5001/api/visibility-gap-analysis', timeout=10)
        if ai_response.status_code == 200:
            return ai_response.json()
        else:
            return jsonify({'error': 'AI visibility service unavailable'}), 503
    except Exception as e:
        return jsonify({'error': 'AI visibility service connection failed'}), 503

@app.route('/api/missing-asset-predictions')
def get_missing_asset_predictions():
    """Get AI predictions for missing assets."""
    try:
        business_unit = request.args.get('business_unit')
        if business_unit:
            ai_response = requests.get(f'http://localhost:5001/api/predict-missing-visibility/{business_unit}', timeout=10)
        else:
            ai_response = requests.get('http://localhost:5001/api/predict-missing-visibility', timeout=10)
        
        if ai_response.status_code == 200:
            return ai_response.json()
        else:
            return jsonify([])
    except Exception as e:
        return jsonify([])

@app.route('/api/train-visibility-ai')
def train_visibility_ai():
    """Trigger AI model training."""
    try:
        response = requests.get('http://localhost:5001/api/train-visibility-model', timeout=5)
        return response.json()
    except Exception as e:
        return jsonify({'error': 'AI visibility service unavailable'}), 503

# Database Management Endpoints
@app.route('/api/database-stats')
def get_database_stats():
    """Get database statistics and health information."""
    stats_query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT fqdn) as unique_hostnames,
        COUNT(DISTINCT business_unit) as unique_business_units,
        COUNT(DISTINCT system_classification) as unique_system_classes,
        COUNT(DISTINCT region) as unique_regions,
        MIN(first_seen_ts) as earliest_record,
        MAX(last_updated_ts) as latest_update,
        AVG(data_quality_score) as avg_quality_score
    FROM universal_cmdb_copy2
    """
    
    coverage_query = """
    SELECT 
        ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_coverage,
        ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_coverage,
        ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as edr_coverage
    FROM universal_cmdb_copy2
    """
    
    stats_data = execute_single_query(stats_query)
    coverage_data = execute_single_query(coverage_query)
    
    # Combine results
    result = {**stats_data, **coverage_data}
    result['database_path'] = DB_PATH
    result['database_exists'] = os.path.exists(DB_PATH)
    
    return jsonify(result)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        if conn:
            # Test database connection
            conn.execute("SELECT 1").fetchone()
            conn.close()
            db_status = 'healthy'
        else:
            db_status = 'unhealthy'
    except:
        db_status = 'error'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)