from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import duckdb
import os

# Import metric calculation modules
from core_metrics import *
from advanced_metrics import *

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with multiple path attempts"""
    db_paths = [
        'universal_cmdb.db',
        './universal_cmdb.db', 
        '../universal_cmdb.db',
        os.path.join(os.getcwd(), 'universal_cmdb.db')
    ]
    
    for db_path in db_paths:
        try:
            if os.path.exists(db_path):
                conn = duckdb.connect(db_path, read_only=True)
                tables = conn.execute("SHOW TABLES").fetchall()
                if any('universal_cmdb' in str(table).lower() for table in tables):
                    return conn
                conn.close()
        except Exception as e:
            continue
    
    raise Exception("Database file 'universal_cmdb.db' not found")

@app.route('/api/database_status')
def database_status():
    """Check database connectivity and basic stats"""
    try:
        conn = get_db_connection()
        result = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()
        
        # Get column info for validation
        columns = conn.execute("PRAGMA table_info(universal_cmdb)").fetchall()
        column_names = [col[1] for col in columns]
        
        conn.close()
        
        return jsonify({
            'status': 'OPERATIONAL',
            'total_records': result[0] if result else 0,
            'columns_available': len(column_names),
            'neural_interface': 'ACTIVE',
            'quantum_state': 'STABLE'
        })
    except Exception as e:
        return jsonify({
            'status': 'COMPROMISED', 
            'error': str(e),
            'neural_interface': 'OFFLINE'
        }), 500

# === PRIMARY CSOC VISIBILITY ENDPOINTS ===

@app.route('/api/global_view')
def api_global_view():
    """1. Global View - CSOC able to view X% of all assets globally"""
    return get_global_visibility_metrics()

@app.route('/api/infrastructure_type')  
def api_infrastructure_type():
    """2. Infrastructure Type - % visibility by host/log type across infrastructure"""
    return get_infrastructure_visibility_breakdown()

@app.route('/api/regional_country_view')
def api_regional_country_view():
    """3. Regional and Country View - Visibility by location"""
    return get_regional_country_visibility()

@app.route('/api/bu_application_view')
def api_bu_application_view():
    """4. BU and Application View - Business Unit, CIO, APM, Application Class"""
    return get_bu_application_visibility()

@app.route('/api/system_classification') 
def api_system_classification():
    """5. System Classification - Web/Windows/Linux/*Nix/MF/DB/Network"""
    return get_system_classification_visibility()

@app.route('/api/security_control_coverage')
def api_security_control_coverage():
    """6. Security Control Coverage - EDR/Tanium/DLP agent based"""
    return get_security_control_coverage()

@app.route '/api/logging_compliance')
def api_logging_compliance():
    """7. Logging Compliance in GSO and Splunk - Platform-based visibility"""
    return get_logging_compliance_metrics()

@app.route('/api/domain_visibility')
def api_domain_visibility():
    """8. Domain Visibility - Asset visibility by hostname and domain"""
    return get_domain_visibility_metrics()

# === ADVANCED ANALYTICS ENDPOINTS ===

@app.route('/api/advanced_analytics')
def api_advanced_analytics():
    """Advanced AI-powered threat intelligence and correlation analysis"""
    return get_advanced_analytics()

@app.route('/api/neural_correlations')
def api_neural_correlations():
    """Neural network-style correlation analysis across all dimensions"""
    return get_neural_correlations()

@app.route('/api/threat_prediction')
def api_threat_prediction():
    """Predictive analytics for security gaps and incident probability"""
    return get_threat_predictions()

@app.route('/api/quantum_metrics')
def api_quantum_metrics():
    """Quantum-level analysis of data entanglement and superposition states"""
    return get_quantum_analysis()

# === UTILITY ENDPOINTS ===

@app.route('/api/host_search')
def api_host_search():
    """Search functionality for drilling down into specific hosts"""
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({'error': 'Search term required'}), 400
    return get_host_search_results(search_term)

@app.route('/api/real_time_feed')
def api_real_time_feed():
    """Real-time data feed for live updates"""
    return get_real_time_metrics()

@app.route('/api/visibility_factor_matrix')
def api_visibility_factor_matrix():
    """Complex visibility factor calculations across all dimensions"""
    return get_visibility_factor_matrix()

@app.route('/api/neural_health_check')
def api_neural_health_check():
    """System health and neural pathway status"""
    return get_neural_health_metrics()

if __name__ == '__main__':
    try:
        conn = get_db_connection()
        result = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()
        conn.close()
        print(f"🧠 NEURAL INTERFACE ONLINE - {result[0]} records detected")
        print("🔗 Quantum tunnels established on http://localhost:5000")
        print("⚡ Advanced threat algorithms activated")
    except Exception as e:
        print(f"💥 NEURAL INTERFACE COMPROMISED: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)