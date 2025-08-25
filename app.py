# /src/app.py

from flask import Flask, jsonify, request
import duckdb
import numpy as np
from datetime import datetime, timedelta
import requests
import json

app = Flask(__name__)

def get_db_connection():
    return duckdb.connect('data/universal_cmdb.duckdb')

@app.route('/api/overall-coverage-totals')
def get_overall_coverage_totals():
    conn = get_db_connection()
    
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
    
    result = conn.execute(query).fetchone()
    conn.close()
    
    columns = ['total_hosts', 'total_splunk_logging', 'splunk_coverage_pct', 'total_cmdb_present', 
               'cmdb_coverage_pct', 'total_crowdstrike', 'crowdstrike_coverage_pct', 
               'total_tanium', 'tanium_coverage_pct', 'total_apm', 'apm_coverage_pct']
    
    data = dict(zip(columns, result))
    
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
    conn = get_db_connection()
    
    query = """
    SELECT 
        '1DC Domain Analysis' as analysis_type,
        COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END) as total_1dc_hosts,
        COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND logging_in_splunk = 'yes' THEN 1 END) as dc1_splunk_covered,
        COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND present_in_cmdb = 'yes' THEN 1 END) as dc1_cmdb_covered,
        COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as dc1_crowdstrike_covered,
        ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND logging_in_splunk = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END), 0), 2) as dc1_splunk_pct,
        ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' AND present_in_cmdb = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%1dc%' THEN 1 END), 0), 2) as dc1_cmdb_pct
    FROM universal_cmdb_copy2
    
    UNION ALL
    
    SELECT 
        'FEAD Domain Analysis' as analysis_type,
        COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END) as total_fead_hosts,
        COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND logging_in_splunk = 'yes' THEN 1 END) as fead_splunk_covered,
        COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND present_in_cmdb = 'yes' THEN 1 END) as fead_cmdb_covered,
        COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as fead_crowdstrike_covered,
        ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND logging_in_splunk = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END), 0), 2) as fead_splunk_pct,
        ROUND(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' AND present_in_cmdb = 'yes' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(CASE WHEN LOWER(domain) LIKE '%fead%' THEN 1 END), 0), 2) as fead_cmdb_pct
    FROM universal_cmdb_copy2
    """
    
    results = conn.execute(query).fetchall()
    conn.close()
    
    columns = ['analysis_type', 'total_hosts', 'splunk_covered', 'cmdb_covered', 
               'crowdstrike_covered', 'splunk_pct', 'cmdb_pct']
    
    data = [dict(zip(columns, row)) for row in results]
    return jsonify(data)

@app.route('/api/regional-analysis')
def get_regional_analysis():
    conn = get_db_connection()
    
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
    
    results = conn.execute(query).fetchall()
    conn.close()
    
    columns = ['standardized_region', 'total_hosts_region', 'cmdb_covered_region', 'cmdb_region_pct',
               'splunk_covered_region', 'splunk_region_pct', 'crowdstrike_covered_region', 'crowdstrike_region_pct']
    
    data = [dict(zip(columns, row)) for row in results]
    return jsonify(data)

@app.route('/api/cio-analysis')
def get_cio_analysis():
    conn = get_db_connection()
    
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
        AND cio ~ '^[A-Za-z ]+$'
    GROUP BY cio
    ORDER BY total_hosts_cio DESC
    """
    
    results = conn.execute(query).fetchall()
    conn.close()
    
    columns = ['cio', 'total_hosts_cio', 'splunk_coverage_cio', 'cmdb_coverage_cio', 
               'crowdstrike_coverage_cio', 'splunk_cio_pct', 'cmdb_cio_pct', 'crowdstrike_cio_pct']
    
    data = [dict(zip(columns, row)) for row in results]
    return jsonify(data)

@app.route('/api/business-unit-analysis')
def get_business_unit_analysis():
    conn = get_db_connection()
    
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
    
    results = conn.execute(query).fetchall()
    conn.close()
    
    columns = ['business_unit_clean', 'total_hosts_bu', 'cmdb_coverage_bu', 'splunk_coverage_bu',
               'crowdstrike_coverage_bu', 'cmdb_bu_pct', 'splunk_bu_pct', 'crowdstrike_bu_pct']
    
    data = [dict(zip(columns, row)) for row in results]
    return jsonify(data)

@app.route('/api/system-classification-analysis')
def get_system_classification_analysis():
    conn = get_db_connection()
    
    query = """
    SELECT 
        TRIM(system_classification) as system_class_clean,
        COUNT(*) as total_hosts_class,
        COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) as cmdb_coverage_class,
        COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_coverage_class,
        COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) as crowdstrike_coverage_class,
        ROUND(COUNT(CASE WHEN present_in_cmdb = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as cmdb_class_pct,
        ROUND(COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as splunk_class_pct,
        ROUND(COUNT(CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 END) * 100.0 / COUNT(*), 2) as crowdstrike_class_pct
    FROM universal_cmdb_copy2
    WHERE system_classification IS NOT NULL AND TRIM(system_classification) != ''
    GROUP BY TRIM(system_classification)
    ORDER BY total_hosts_class DESC
    """
    
    results = conn.execute(query).fetchall()
    conn.close()
    
    columns = ['system_class_clean', 'total_hosts_class', 'cmdb_coverage_class', 'splunk_coverage_class',
               'crowdstrike_coverage_class', 'cmdb_class_pct', 'splunk_class_pct', 'crowdstrike_class_pct']
    
    data = [dict(zip(columns, row)) for row in results]
    return jsonify(data)

@app.route('/api/log-type-visibility')
def get_log_type_visibility():
    conn = get_db_connection()
    
    query = """
    SELECT 
        CASE 
            WHEN LOWER(system_classification) LIKE '%firewall%' OR LOWER(fqdn) LIKE '%fw%' THEN 'Firewall Traffic'
            WHEN LOWER(system_classification) LIKE '%server%' THEN 'OS logs'
            WHEN LOWER(system_classification) LIKE '%cloud%' OR LOWER(infrastructure_type) LIKE '%cloud%' THEN 'Cloud Event'
            WHEN LOWER(fqdn) LIKE '%web%' OR LOWER(fqdn) LIKE '%www%' THEN 'Web Logs'
            WHEN LOWER(system_classification) LIKE '%auth%' OR LOWER(fqdn) LIKE '%auth%' THEN 'Authentication attempts'
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
    
    results = conn.execute(query).fetchall()
    conn.close()
    
    columns = ['predicted_log_type', 'total_assets', 'splunk_visibility', 'gso_visibility',
               'splunk_coverage_pct', 'gso_coverage_pct']
    
    data = [dict(zip(columns, row)) for row in results]
    return jsonify(data)

@app.route('/api/visibility-factor-metrics')
def get_visibility_factor_metrics():
    conn = get_db_connection()
    
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
              COUNT(CASE WHEN fqdn IS NOT NULL AND fqdn != '' THEN 1 END), 2) as url_fqdn_coverage_pct
    FROM universal_cmdb_copy2
    """
    
    results = conn.execute(query).fetchall()
    conn.close()
    
    columns = ['metric_type', 'total_count', 'covered_count', 'coverage_percentage']
    data = [dict(zip(columns, row)) for row in results]
    return jsonify(data)

@app.route('/api/ai-visibility-insights')
def get_ai_visibility_insights():
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
    try:
        response = requests.get('http://localhost:5001/api/train-visibility-model', timeout=5)
        return response.json()
    except Exception as e:
        return jsonify({'error': 'AI visibility service unavailable'}), 503

if __name__ == '__main__':
    app.run(debug=True)