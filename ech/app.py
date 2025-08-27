from flask import Flask, jsonify
from flask_cors import CORS
import logging
from database_utils import get_db_connection, verify_table_structure
from metrics_core import *
from metrics_advanced import *

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/database_status')
def database_status():
    try:
        conn = get_db_connection()
        columns, row_count = verify_table_structure(conn)
        conn.close()
        return jsonify({
            'status': 'connected',
            'table': 'universal_cmdb',
            'columns': columns,
            'row_count': row_count,
            'database_type': 'duckdb'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/source_tables')
def source_tables_metrics():
    return get_source_tables_metrics()

@app.route('/api/domain_metrics')
def domain_metrics():
    return get_domain_metrics()

@app.route('/api/infrastructure_type')
def infrastructure_type_metrics():
    return get_infrastructure_type_metrics()

@app.route('/api/region_metrics')
def region_metrics():
    return get_region_metrics()

@app.route('/api/country_metrics')
def country_metrics():
    return get_country_metrics()

@app.route('/api/data_center_metrics')
def data_center_metrics():
    return get_data_center_metrics()

@app.route('/api/cloud_region_metrics')
def cloud_region_metrics():
    return get_cloud_region_metrics()

@app.route('/api/class_metrics')
def class_metrics():
    return get_class_metrics()

@app.route('/api/system_classification_metrics')
def system_classification_metrics():
    return get_system_classification_metrics()

@app.route('/api/business_unit_metrics')
def business_unit_metrics():
    return get_business_unit_metrics()

@app.route('/api/cio_metrics')
def cio_metrics():
    return get_cio_metrics()

@app.route('/api/tanium_coverage')
def tanium_coverage():
    return get_tanium_coverage()

@app.route('/api/cmdb_presence')
def cmdb_presence():
    return get_cmdb_presence()

@app.route('/api/splunk_coverage')
def splunk_coverage():
    return get_splunk_coverage()

@app.route('/api/logging_platforms')
def logging_platforms():
    return get_logging_platforms()

@app.route('/api/ssc_coverage')
def ssc_coverage():
    return get_ssc_coverage()

@app.route('/api/dlp_coverage')
def dlp_coverage():
    return get_dlp_coverage()

@app.route('/api/crowdstrike_coverage')
def crowdstrike_coverage():
    return get_crowdstrike_coverage()

@app.route('/api/temporal_analysis')
def temporal_analysis():
    return get_temporal_analysis()

@app.route('/api/data_quality_analysis')
def data_quality_analysis():
    return get_data_quality_analysis()

@app.route('/api/coverage_correlation')
def coverage_correlation():
    return get_coverage_correlation()

@app.route('/api/security_stack_analysis')
def security_stack_analysis():
    return get_security_stack_analysis()

@app.route('/api/modernization_analysis')
def modernization_analysis():
    return get_modernization_analysis()

@app.route('/api/compliance_analysis')
def compliance_analysis():
    return get_compliance_analysis()

@app.route('/api/risk_assessment')
def risk_assessment():
    return get_risk_assessment()

@app.route('/api/visibility_score')
def visibility_score():
    return get_visibility_score()

@app.route('/api/shadow_it_detection')
def shadow_it_detection():
    return get_shadow_it_detection()

@app.route('/api/host_search')
def host_search():
    return get_host_search()

@app.route('/api/comprehensive_dashboard')
def comprehensive_dashboard():
    return get_comprehensive_dashboard()

if __name__ == '__main__':
    try:
        conn = get_db_connection()
        columns, row_count = verify_table_structure(conn)
        conn.close()
        logger.info(f"Database initialized successfully. Columns: {len(columns)}, Rows: {row_count}")
        print(f"Database connection successful! Found {row_count} rows with {len(columns)} columns.")
        print("Starting Flask server on http://localhost:5000")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print(f"Database connection failed: {e}")
        print("Please ensure your 'universal_cmdb.db' file exists in the project directory.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)