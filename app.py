# /server/app.py
import duckdb
from flask import Flask, jsonify
from flask_cors import CORS
import re
from collections import defaultdict
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return duckdb.connect('universal_cmdb.db')

def parse_multi_values(value, delimiters=['|', ',']):
    if not value or value == 'null':
        return []
    for delimiter in delimiters:
        if delimiter in str(value):
            return [v.strip() for v in str(value).split(delimiter) if v.strip()]
    return [str(value).strip()]

@app.route('/api/global-view')
def global_view():
    conn = get_db_connection()
    
    total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
    
    coverage_matrix = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk_count,
            SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb_count,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr_count,
            SUM(CASE WHEN tanium_coverage LIKE '%tanium%' THEN 1 ELSE 0 END) as tanium_count,
            SUM(CASE WHEN logging_in_splunk = 'yes' AND present_in_cmdb = 'yes' AND edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as triple_coverage,
            SUM(CASE WHEN logging_in_splunk != 'yes' AND present_in_cmdb != 'yes' AND edr_coverage NOT LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as zero_coverage
        FROM universal_cmdb
    """).fetchone()
    
    visibility_by_hour = conn.execute("""
        SELECT 
            EXTRACT(hour FROM CAST(last_updated AS TIMESTAMP)) as hour,
            COUNT(*) as discoveries,
            AVG(data_quality_score) as avg_quality
        FROM universal_cmdb 
        WHERE last_updated IS NOT NULL
        GROUP BY EXTRACT(hour FROM CAST(last_updated AS TIMESTAMP))
        ORDER BY hour
    """).fetchall()
    
    infrastructure_heatmap = conn.execute("""
        SELECT 
            infrastructure_type,
            region,
            COUNT(*) as asset_count,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as splunk_coverage,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as edr_coverage,
            AVG(data_quality_score) as quality_score
        FROM universal_cmdb 
        WHERE infrastructure_type IS NOT NULL AND region IS NOT NULL
        GROUP BY infrastructure_type, region
        HAVING asset_count > 5
        ORDER BY asset_count DESC
        LIMIT 100
    """).fetchall()
    
    risk_correlation = conn.execute("""
        SELECT 
            business_unit,
            COUNT(*) as assets,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as log_rate,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as security_rate,
            COUNT(DISTINCT country) as geographic_spread,
            COUNT(DISTINCT infrastructure_type) as infra_diversity
        FROM universal_cmdb 
        WHERE business_unit IS NOT NULL
        GROUP BY business_unit
        HAVING assets > 100
        ORDER BY (log_rate + security_rate) / 2 ASC
        LIMIT 15
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        'executive_summary': {
            'total_assets': total_assets,
            'visibility_score': round(((coverage_matrix[1] + coverage_matrix[2] + coverage_matrix[3]) / (3 * total_assets)) * 100, 2),
            'security_posture': round(((coverage_matrix[3] + coverage_matrix[4]) / (2 * total_assets)) * 100, 2),
            'triple_coverage': coverage_matrix[5],
            'blind_spots': coverage_matrix[6]
        },
        'coverage_breakdown': {
            'splunk': {'count': coverage_matrix[1], 'percentage': round((coverage_matrix[1] / total_assets) * 100, 2)},
            'cmdb': {'count': coverage_matrix[2], 'percentage': round((coverage_matrix[2] / total_assets) * 100, 2)},
            'edr': {'count': coverage_matrix[3], 'percentage': round((coverage_matrix[3] / total_assets) * 100, 2)},
            'tanium': {'count': coverage_matrix[4], 'percentage': round((coverage_matrix[4] / total_assets) * 100, 2)}
        },
        'discovery_timeline': [
            {
                'hour': row[0],
                'discoveries': row[1],
                'quality_score': round(row[2], 2) if row[2] else 0
            } for row in visibility_by_hour
        ],
        'infrastructure_heatmap': [
            {
                'infrastructure': row[0],
                'region': row[1],
                'asset_count': row[2],
                'splunk_coverage': round(row[3], 1),
                'edr_coverage': round(row[4], 1),
                'quality_score': round(row[5], 1) if row[5] else 0,
                'risk_score': round(100 - ((row[3] + row[4]) / 2), 1)
            } for row in infrastructure_heatmap
        ],
        'business_risk_analysis': [
            {
                'business_unit': row[0],
                'asset_count': row[1],
                'logging_coverage': round(row[2] * 100, 1),
                'security_coverage': round(row[3] * 100, 1),
                'geographic_footprint': row[4],
                'infrastructure_complexity': row[5],
                'risk_score': round((1 - ((row[2] + row[3]) / 2)) * 100, 1)
            } for row in risk_correlation
        ]
    })

@app.route('/api/security-control-coverage')
def security_control_coverage():
    conn = get_db_connection()
    
    control_effectiveness = conn.execute("""
        SELECT 
            infrastructure_type,
            COUNT(*) as total_assets,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr_deployed,
            SUM(CASE WHEN tanium_coverage LIKE '%tanium%' THEN 1 ELSE 0 END) as tanium_deployed,
            SUM(CASE WHEN dlp_agent_coverage LIKE '%dlp%' THEN 1 ELSE 0 END) as dlp_deployed,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as logging_enabled,
            AVG(data_quality_score) as avg_data_quality
        FROM universal_cmdb 
        WHERE infrastructure_type IS NOT NULL
        GROUP BY infrastructure_type
        HAVING total_assets > 50
        ORDER BY total_assets DESC
    """).fetchall()
    
    security_stack_analysis = conn.execute("""
        SELECT 
            CASE 
                WHEN edr_coverage LIKE '%crowdstrike%' AND tanium_coverage LIKE '%tanium%' AND dlp_agent_coverage LIKE '%dlp%' AND logging_in_splunk = 'yes' THEN 'full_stack'
                WHEN edr_coverage LIKE '%crowdstrike%' AND tanium_coverage LIKE '%tanium%' AND logging_in_splunk = 'yes' THEN 'core_security'
                WHEN edr_coverage LIKE '%crowdstrike%' AND logging_in_splunk = 'yes' THEN 'basic_security'
                WHEN logging_in_splunk = 'yes' THEN 'logging_only'
                ELSE 'unprotected'
            END as security_tier,
            COUNT(*) as asset_count,
            AVG(data_quality_score) as avg_quality
        FROM universal_cmdb
        GROUP BY security_tier
    """).fetchall()
    
    geographic_security_map = conn.execute("""
        SELECT 
            region,
            country,
            COUNT(*) as assets,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as edr_coverage,
            AVG(CASE WHEN tanium_coverage LIKE '%tanium%' THEN 100.0 ELSE 0.0 END) as tanium_coverage,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as logging_coverage,
            COUNT(DISTINCT infrastructure_type) as infra_diversity
        FROM universal_cmdb 
        WHERE region IS NOT NULL AND country IS NOT NULL
        GROUP BY region, country
        HAVING assets > 20
        ORDER BY assets DESC
        LIMIT 50
    """).fetchall()
    
    threat_surface_analysis = conn.execute("""
        SELECT 
            system_classification,
            COUNT(*) as total,
            COUNT(CASE WHEN ip_address LIKE '10.%' OR ip_address LIKE '192.168.%' OR ip_address LIKE '172.%' THEN 1 END) as internal_ips,
            COUNT(CASE WHEN ip_address NOT LIKE '10.%' AND ip_address NOT LIKE '192.168.%' AND ip_address NOT LIKE '172.%' AND ip_address IS NOT NULL THEN 1 END) as external_ips,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as edr_protection,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as monitored
        FROM universal_cmdb 
        WHERE system_classification IS NOT NULL
        GROUP BY system_classification
        HAVING total > 10
        ORDER BY external_ips DESC, total DESC
        LIMIT 30
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        'control_effectiveness': [
            {
                'infrastructure': row[0],
                'total_assets': row[1],
                'edr_coverage': round((row[2] / row[1]) * 100, 1),
                'tanium_coverage': round((row[3] / row[1]) * 100, 1),
                'dlp_coverage': round((row[4] / row[1]) * 100, 1),
                'logging_coverage': round((row[5] / row[1]) * 100, 1),
                'data_quality': round(row[6], 1) if row[6] else 0,
                'security_score': round(((row[2] + row[3] + row[4] + row[5]) / (4 * row[1])) * 100, 1)
            } for row in control_effectiveness
        ],
        'security_stack_tiers': [
            {
                'tier': row[0],
                'asset_count': row[1],
                'data_quality': round(row[2], 1) if row[2] else 0,
                'tier_percentage': round((row[1] / sum([r[1] for r in security_stack_analysis])) * 100, 1)
            } for row in security_stack_analysis
        ],
        'geographic_security_map': [
            {
                'region': row[0],
                'country': row[1],
                'asset_count': row[2],
                'edr_coverage': round(row[3], 1),
                'tanium_coverage': round(row[4], 1),
                'logging_coverage': round(row[5], 1),
                'infrastructure_diversity': row[6],
                'composite_security_score': round((row[3] + row[4] + row[5]) / 3, 1)
            } for row in geographic_security_map
        ],
        'threat_surface': [
            {
                'system_type': row[0],
                'total_systems': row[1],
                'internal_exposure': row[2],
                'external_exposure': row[3],
                'exposure_ratio': round((row[3] / row[1]) * 100, 1) if row[1] > 0 else 0,
                'edr_protection': round(row[4], 1),
                'monitoring_coverage': round((row[5] / row[1]) * 100, 1),
                'threat_level': 'critical' if row[3] > row[2] else 'medium' if row[3] > 0 else 'low'
            } for row in threat_surface_analysis
        ]
    })

@app.route('/api/infrastructure-type')
def infrastructure_type():
    conn = get_db_connection()
    
    infrastructure_performance = conn.execute("""
        SELECT 
            infrastructure_type,
            COUNT(*) as total,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as logging_rate,
            AVG(CASE WHEN present_in_cmdb = 'yes' THEN 100.0 ELSE 0.0 END) as cmdb_rate,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as edr_rate,
            AVG(data_quality_score) as quality_score,
            COUNT(DISTINCT region) as geographic_spread,
            COUNT(DISTINCT business_unit) as business_spread,
            MIN(CAST(first_seen AS DATE)) as first_discovered,
            MAX(CAST(last_updated AS DATE)) as last_activity
        FROM universal_cmdb 
        WHERE infrastructure_type IS NOT NULL
        GROUP BY infrastructure_type
        HAVING total > 10
        ORDER BY total DESC
    """).fetchall()
    
    infrastructure_correlation = conn.execute("""
        WITH infra_pairs AS (
            SELECT 
                i1.infrastructure_type as type1,
                i2.infrastructure_type as type2,
                COUNT(*) as co_occurrence,
                AVG(CASE WHEN i1.logging_in_splunk = 'yes' AND i2.logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as joint_logging
            FROM universal_cmdb i1
            JOIN universal_cmdb i2 ON i1.business_unit = i2.business_unit 
            WHERE i1.infrastructure_type != i2.infrastructure_type 
                AND i1.infrastructure_type IS NOT NULL 
                AND i2.infrastructure_type IS NOT NULL
            GROUP BY i1.infrastructure_type, i2.infrastructure_type
            HAVING co_occurrence > 20
        )
        SELECT * FROM infra_pairs ORDER BY co_occurrence DESC LIMIT 25
    """).fetchall()
    
    deployment_timeline = conn.execute("""
        SELECT 
            DATE_TRUNC('month', CAST(first_seen AS DATE)) as month,
            infrastructure_type,
            COUNT(*) as new_deployments
        FROM universal_cmdb 
        WHERE first_seen IS NOT NULL AND infrastructure_type IS NOT NULL
        GROUP BY DATE_TRUNC('month', CAST(first_seen AS DATE)), infrastructure_type
        ORDER BY month DESC, new_deployments DESC
        LIMIT 200
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        'infrastructure_analytics': [
            {
                'type': row[0],
                'total_assets': row[1],
                'logging_coverage': round(row[2], 1),
                'cmdb_coverage': round(row[3], 1),
                'edr_coverage': round(row[4], 1),
                'data_quality': round(row[5], 1) if row[5] else 0,
                'geographic_presence': row[6],
                'business_penetration': row[7],
                'age_days': (datetime.now() - datetime.strptime(str(row[8]), '%Y-%m-%d')).days if row[8] else 0,
                'last_activity_days': (datetime.now() - datetime.strptime(str(row[9]), '%Y-%m-%d')).days if row[9] else 0,
                'security_maturity': round((row[2] + row[3] + row[4]) / 3, 1),
                'risk_exposure': round(100 - ((row[2] + row[4]) / 2), 1)
            } for row in infrastructure_performance
        ],
        'infrastructure_relationships': [
            {
                'primary_type': row[0],
                'secondary_type': row[1],
                'co_occurrence_count': row[2],
                'joint_logging_rate': round(row[3], 1),
                'relationship_strength': round((row[2] / 1000) * 100, 1)
            } for row in infrastructure_correlation
        ],
        'deployment_timeline': [
            {
                'month': row[0].strftime('%Y-%m') if row[0] else 'unknown',
                'infrastructure': row[1],
                'deployments': row[2]
            } for row in deployment_timeline
        ]
    })

@app.route('/api/domain-visibility')
def domain_visibility():
    conn = get_db_connection()
    
    domain_risk_assessment = conn.execute("""
        SELECT 
            domain,
            COUNT(*) as assets,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as logging_rate,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as security_rate,
            COUNT(DISTINCT ip_address) as unique_ips,
            COUNT(DISTINCT country) as countries,
            MAX(CAST(last_updated AS DATE)) as last_seen,
            AVG(data_quality_score) as data_quality
        FROM universal_cmdb 
        WHERE domain IS NOT NULL
        GROUP BY domain
        HAVING assets > 5
        ORDER BY assets DESC
        LIMIT 100
    """).fetchall()
    
    dns_security_analysis = conn.execute("""
        SELECT 
            CASE 
                WHEN domain LIKE '%.corp.%' THEN 'corporate'
                WHEN domain LIKE '%.dev.%' THEN 'development' 
                WHEN domain LIKE '%.prod.%' THEN 'production'
                WHEN domain LIKE '%.test.%' THEN 'testing'
                WHEN domain LIKE '%1dc%' THEN 'datacenter'
                WHEN domain LIKE '%fead%' THEN 'federated'
                ELSE 'standard'
            END as domain_category,
            COUNT(*) as domain_count,
            COUNT(DISTINCT domain) as unique_domains,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as avg_logging,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as avg_security
        FROM universal_cmdb 
        WHERE domain IS NOT NULL
        GROUP BY domain_category
        ORDER BY domain_count DESC
    """).fetchall()
    
    subdomain_exposure = conn.execute("""
        SELECT 
            REGEXP_EXTRACT(domain, '([^.]+\.[^.]+)$') as root_domain,
            COUNT(DISTINCT domain) as subdomains,
            COUNT(*) as total_assets,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as protection_rate,
            COUNT(CASE WHEN ip_address NOT LIKE '10.%' AND ip_address NOT LIKE '192.168.%' THEN 1 END) as external_facing
        FROM universal_cmdb 
        WHERE domain IS NOT NULL AND domain LIKE '%.%.%'
        GROUP BY REGEXP_EXTRACT(domain, '([^.]+\.[^.]+)$')
        HAVING subdomains > 3
        ORDER BY external_facing DESC, subdomains DESC
        LIMIT 30
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        'domain_intelligence': [
            {
                'domain': row[0],
                'asset_count': row[1],
                'logging_coverage': round(row[2], 1),
                'security_coverage': round(row[3], 1),
                'ip_diversity': row[4],
                'geographic_spread': row[5],
                'last_activity': str(row[6]) if row[6] else 'unknown',
                'data_quality': round(row[7], 1) if row[7] else 0,
                'exposure_score': round(((row[4] * row[5]) / row[1]) * 10, 1),
                'protection_gap': round(100 - ((row[2] + row[3]) / 2), 1)
            } for row in domain_risk_assessment
        ],
        'domain_categories': [
            {
                'category': row[0],
                'domain_count': row[1],
                'unique_domains': row[2],
                'avg_logging': round(row[3], 1),
                'avg_security': round(row[4], 1),
                'security_posture': round((row[3] + row[4]) / 2, 1)
            } for row in dns_security_analysis
        ],
        'subdomain_analysis': [
            {
                'root_domain': row[0] if row[0] else 'unknown',
                'subdomain_count': row[1],
                'total_assets': row[2],
                'protection_rate': round(row[3], 1),
                'external_exposure': row[4],
                'attack_surface': round((row[1] * row[4]) / max(row[2], 1), 2)
            } for row in subdomain_exposure
        ]
    })

@app.route('/api/regional-country-view')
def regional_country_view():
    conn = get_db_connection()
    
    geopolitical_risk = conn.execute("""
        SELECT 
            region,
            country,
            COUNT(*) as assets,
            COUNT(DISTINCT business_unit) as business_units,
            COUNT(DISTINCT infrastructure_type) as infrastructure_types,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as logging_coverage,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as edr_coverage,
            COUNT(CASE WHEN ip_address NOT LIKE '10.%' AND ip_address NOT LIKE '192.168.%' THEN 1 END) as external_assets,
            AVG(data_quality_score) as data_quality
        FROM universal_cmdb 
        WHERE region IS NOT NULL AND country IS NOT NULL
        GROUP BY region, country
        HAVING assets > 50
        ORDER BY assets DESC
    """).fetchall()
    
    compliance_by_region = conn.execute("""
        SELECT 
            region,
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' OR logging_in_chronicle = 'yes' THEN 1 ELSE 0 END) as compliant_logging,
            SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as documented,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as protected,
            COUNT(DISTINCT business_unit) as business_coverage
        FROM universal_cmdb 
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY total DESC
    """).fetchall()
    
    cross_border_analysis = conn.execute("""
        SELECT 
            b1.business_unit,
            COUNT(DISTINCT b1.country) as countries_count,
            COUNT(DISTINCT b1.region) as regions_count,
            COUNT(*) as total_assets,
            AVG(CASE WHEN b1.logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as global_logging,
            AVG(CASE WHEN b1.edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as global_security
        FROM universal_cmdb b1
        WHERE b1.business_unit IS NOT NULL AND b1.country IS NOT NULL
        GROUP BY b1.business_unit
        HAVING countries_count > 1
        ORDER BY countries_count DESC, total_assets DESC
        LIMIT 20
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        'geopolitical_matrix': [
            {
                'region': row[0],
                'country': row[1],
                'asset_portfolio': row[2],
                'business_diversity': row[3],
                'infrastructure_complexity': row[4],
                'logging_posture': round(row[5], 1),
                'security_posture': round(row[6], 1),
                'external_exposure': row[7],
                'data_integrity': round(row[8], 1) if row[8] else 0,
                'geopolitical_risk': round(((row[7] / max(row[2], 1)) * 100) + (100 - row[5]) + (100 - row[6]), 1),
                'strategic_importance': round((row[2] * row[3] * row[4]) / 10000, 1)
            } for row in geopolitical_risk
        ],
        'regional_compliance': [
            {
                'region': row[0],
                'total_assets': row[1],
                'logging_compliance': round((row[2] / row[1]) * 100, 1),
                'documentation_rate': round((row[3] / row[1]) * 100, 1),
                'protection_rate': round((row[4] / row[1]) * 100, 1),
                'business_coverage': row[5],
                'compliance_score': round(((row[2] + row[3] + row[4]) / (3 * row[1])) * 100, 1)
            } for row in compliance_by_region
        ],
        'multinational_operations': [
            {
                'business_unit': row[0],
                'countries_operated': row[1],
                'regions_operated': row[2],
                'global_asset_count': row[3],
                'standardized_logging': round(row[4], 1),
                'standardized_security': round(row[5], 1),
                'operational_complexity': round((row[1] * row[2]) / 10, 1),
                'governance_risk': round(100 - ((row[4] + row[5]) / 2), 1)
            } for row in cross_border_analysis
        ]
    })

@app.route('/api/bu-application-view')
def bu_application_view():
    conn = get_db_connection()
    
    business_risk_portfolio = conn.execute("""
        SELECT 
            business_unit,
            COUNT(*) as assets,
            COUNT(DISTINCT infrastructure_type) as tech_diversity,
            COUNT(DISTINCT country) as geographic_reach,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as logging_maturity,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as security_maturity,
            SUM(CASE WHEN apm LIKE '%apm%' THEN 1 ELSE 0 END) as apm_coverage,
            AVG(data_quality_score) as data_governance
        FROM universal_cmdb 
        WHERE business_unit IS NOT NULL
        GROUP BY business_unit
        HAVING assets > 100
        ORDER BY assets DESC
    """).fetchall()
    
    application_dependency_map = conn.execute("""
        SELECT 
            apm,
            COUNT(*) as instances,
            COUNT(DISTINCT business_unit) as business_dependencies,
            COUNT(DISTINCT infrastructure_type) as infrastructure_dependencies,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as observability,
            AVG(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 100.0 ELSE 0.0 END) as security_coverage
        FROM universal_cmdb 
        WHERE apm IS NOT NULL AND apm != 'null'
        GROUP BY apm
        HAVING instances > 5
        ORDER BY business_dependencies DESC, instances DESC
        LIMIT 50
    """).fetchall()
    
    cio_governance_metrics = conn.execute("""
        SELECT 
            cio,
            COUNT(*) as managed_assets,
            COUNT(DISTINCT business_unit) as business_units_overseen,
            COUNT(DISTINCT infrastructure_type) as technology_portfolio,
            AVG(CASE WHEN present_in_cmdb = 'yes' THEN 100.0 ELSE 0.0 END) as governance_score,
            AVG(CASE WHEN logging_in_splunk = 'yes' THEN 100.0 ELSE 0.0 END) as monitoring_score,
            AVG(data_quality_score) as data_stewardship
        FROM universal_cmdb 
        WHERE cio IS NOT NULL AND cio != 'null'
        GROUP BY cio
        HAVING managed_assets > 200
        ORDER BY managed_assets DESC
        LIMIT 20
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        'business_portfolio': [
            {
                'unit': row[0],
                'asset_portfolio': row[1],
                'technology_diversification': row[2],
                'global_footprint': row[3],
                'operational_visibility': round(row[4], 1),
                'security_resilience': round(row[5], 1),
                'application_monitoring': row[6],
                'data_governance': round(row[7], 1) if row[7] else 0,
                'business_risk_score': round((100 - row[4]) + (100 - row[5]) + (row[2] * 5) + (row[3] * 3), 1),
                'maturity_index': round((row[4] + row[5] + (row[7] if row[7] else 0)) / 3, 1)
            } for row in business_risk_portfolio
        ],
        'application_architecture': [
            {
                'application': row[0],
                'deployment_scale': row[1],
                'business_criticality': row[2],
                'infrastructure_spread': row[3],
                'observability_score': round(row[4], 1),
                'security_score': round(row[5], 1),
                'dependency_risk': round((row[2] * row[3]) / max(row[1], 1) * 100, 1),
                'resilience_factor': round((row[4] + row[5]) / 2, 1)
            } for row in application_dependency_map
        ],
        'executive_oversight': [
            {
                'cio': row[0],
                'asset_responsibility': row[1],
                'organizational_scope': row[2],
                'technology_breadth': row[3],
                'governance_effectiveness': round(row[4], 1),
                'operational_oversight': round(row[5], 1),
                'data_stewardship': round(row[6], 1) if row[6] else 0,
                'leadership_score': round((row[4] + row[5] + (row[6] if row[6] else 0)) / 3, 1)
            } for row in cio_governance_metrics
        ]
    })

@app.route('/api/logging-compliance')
def logging_compliance():
    conn = get_db_connection()
    
    platform_performance = conn.execute("""
        SELECT 
            infrastructure_type,
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk_logs,
            SUM(CASE WHEN logging_in_chronicle = 'yes' THEN 1 ELSE 0 END) as chronicle_logs,
            SUM(CASE WHEN logging_in_splunk = 'yes' AND logging_in_chronicle = 'yes' THEN 1 ELSE 0 END) as dual_platform,
            AVG(data_quality_score) as log_quality,
            COUNT(DISTINCT business_unit) as business_coverage
        FROM universal_cmdb 
        WHERE infrastructure_type IS NOT NULL
        GROUP BY infrastructure_type
        HAVING total > 20
        ORDER BY total DESC
    """).fetchall()
    
    log_volume_analysis = conn.execute("""
        SELECT 
            business_unit,
            region,
            COUNT(*) as systems,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as logging_systems,
            AVG(data_quality_score) as quality_index,
            COUNT(DISTINCT infrastructure_type) as source_diversity
        FROM universal_cmdb 
        WHERE business_unit IS NOT NULL AND region IS NOT NULL
        GROUP BY business_unit, region
        HAVING systems > 30
        ORDER BY systems DESC
        LIMIT 50
    """).fetchall()
    
    compliance_gaps = conn.execute("""
        SELECT 
            country,
            COUNT(*) as assets,
            SUM(CASE WHEN logging_in_splunk != 'yes' AND logging_in_chronicle != 'yes' THEN 1 ELSE 0 END) as no_logging,
            SUM(CASE WHEN present_in_cmdb != 'yes' THEN 1 ELSE 0 END) as undocumented,
            AVG(data_quality_score) as governance_score
        FROM universal_cmdb 
        WHERE country IS NOT NULL
        GROUP BY country
        HAVING assets > 100 AND (no_logging > assets * 0.2 OR undocumented > assets * 0.3)
        ORDER BY no_logging + undocumented DESC
        LIMIT 20
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        'platform_analytics': [
            {
                'infrastructure': row[0],
                'total_systems': row[1],
                'splunk_adoption': round((row[2] / row[1]) * 100, 1),
                'chronicle_adoption': round((row[3] / row[1]) * 100, 1),
                'dual_platform_rate': round((row[4] / row[1]) * 100, 1),
                'log_quality_index': round(row[5], 1) if row[5] else 0,
                'business_penetration': row[6],
                'platform_maturity': round(((row[2] + row[3]) / (2 * row[1])) * 100, 1)
            } for row in platform_performance
        ],
        'log_volume_heatmap': [
            {
                'business_unit': row[0],
                'region': row[1],
                'system_count': row[2],
                'logging_rate': round((row[3] / row[2]) * 100, 1),
                'quality_score': round(row[4], 1) if row[4] else 0,
                'source_diversity': row[5],
                'volume_risk': round((row[2] - row[3]) / max(row[2], 1) * 100, 1),
                'complexity_factor': round((row[5] * row[2]) / 100, 1)
            } for row in log_volume_analysis
        ],
        'compliance_violations': [
            {
                'country': row[0],
                'total_assets': row[1],
                'logging_violations': row[2],
                'documentation_gaps': row[3],
                'governance_maturity': round(row[4], 1) if row[4] else 0,
                'compliance_risk': round(((row[2] + row[3]) / row[1]) * 100, 1),
                'regulatory_exposure': round((row[1] - (row[1] - row[2] - row[3])) / max(row[1], 1) * 100, 1)
            } for row in compliance_gaps
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)