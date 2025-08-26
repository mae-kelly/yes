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

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'universal_cmdb.db')
    logger.info(f"Connecting to database at: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        logger.error(f"Database file does not exist at: {os.path.abspath(db_path)}")
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    try:
        conn = duckdb.connect(db_path, read_only=True)
        logger.info("Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

def parse_multi_values(value, delimiters=['|', ',']):
    """Parse multi-value cells by splitting on delimiters"""
    if not value or value == 'null' or str(value).lower() == 'null':
        return []
    value_str = str(value).strip()
    if not value_str:
        return []
    
    for delimiter in delimiters:
        if delimiter in value_str:
            return [v.strip() for v in value_str.split(delimiter) if v.strip() and v.strip().lower() != 'null']
    return [value_str] if value_str and value_str.lower() != 'null' else []

def extract_class_numbers(value):
    """Extract class numbers from class column"""
    if not value:
        return []
    classes = []
    parts = parse_multi_values(value, ['|'])
    for part in parts:
        matches = re.findall(r'class\s*(\d+)', part.lower())
        classes.extend([int(match) for match in matches])
    return classes

def standardize_region(region):
    """Standardize regions to North America, LATAM, EMEA, APAC"""
    if not region:
        return 'Unknown'
    
    region_lower = str(region).lower()
    if any(term in region_lower for term in ['north america', 'na', 'us', 'united states', 'canada']):
        return 'North America'
    elif any(term in region_lower for term in ['latam', 'latin america', 'south america', 'brazil', 'mexico']):
        return 'LATAM'
    elif any(term in region_lower for term in ['emea', 'europe', 'middle east', 'africa']):
        return 'EMEA'
    elif any(term in region_lower for term in ['apac', 'asia', 'pacific', 'australia', 'japan']):
        return 'APAC'
    return 'Other'

def is_valid_cio(value):
    """Check if CIO value is valid (letters only, no numbers)"""
    if not value:
        return False
    value_str = str(value).strip()
    return value_str.replace(' ', '').replace('-', '').replace('_', '').isalpha()

def calculate_coverage_percentage(count, total):
    return round((count / total) * 100, 2) if total > 0 else 0

@app.route('/api/health')
def health_check():
    try:
        conn = get_db_connection()
        row_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        # Test all detection rules
        splunk_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        cmdb_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(present_in_cmdb) = 'yes'").fetchone()[0]
        crowdstrike_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(edr_coverage) LIKE '%crowdstrike agent%'").fetchone()[0]
        tanium_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(tanium_coverage) LIKE '%tanium%'").fetchone()[0]
        apm_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(apm) LIKE '%apm%'").fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'total_hosts': row_count,
            'detection_test': {
                'splunk_logging': splunk_count,
                'cmdb_present': cmdb_count,
                'crowdstrike_coverage': crowdstrike_count,
                'tanium_coverage': tanium_count,
                'apm_coverage': apm_count
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/global-view')
def global_view():
    """Overall Coverage Totals - Primary Metrics #1"""
    try:
        conn = get_db_connection()
        
        total_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        # Apply exact detection rules
        splunk_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        cmdb_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(present_in_cmdb) = 'yes'").fetchone()[0]
        crowdstrike_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(edr_coverage) LIKE '%crowdstrike agent%'").fetchone()[0]
        tanium_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(tanium_coverage) LIKE '%tanium%'").fetchone()[0]
        apm_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(apm) LIKE '%apm%'").fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_hosts': total_hosts,
            'coverage': {
                'splunk_logging': {
                    'count': splunk_count,
                    'percentage': calculate_coverage_percentage(splunk_count, total_hosts)
                },
                'cmdb_present': {
                    'count': cmdb_count,
                    'percentage': calculate_coverage_percentage(cmdb_count, total_hosts)
                },
                'crowdstrike_coverage': {
                    'count': crowdstrike_count,
                    'percentage': calculate_coverage_percentage(crowdstrike_count, total_hosts)
                },
                'tanium_coverage': {
                    'count': tanium_count,
                    'percentage': calculate_coverage_percentage(tanium_count, total_hosts)
                },
                'apm_coverage': {
                    'count': apm_count,
                    'percentage': calculate_coverage_percentage(apm_count, total_hosts)
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"global_view failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/domain-visibility')
def domain_visibility():
    """Domain Analysis - Primary Metrics #2"""
    try:
        conn = get_db_connection()
        
        # 1DC domains - search for "1dc" keyword
        dc1_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(domain) LIKE '%1dc%'").fetchone()[0]
        dc1_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(domain) LIKE '%1dc%' AND LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        dc1_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(domain) LIKE '%1dc%' AND LOWER(present_in_cmdb) = 'yes'").fetchone()[0]
        dc1_crowdstrike = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(domain) LIKE '%1dc%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%'").fetchone()[0]
        
        # FEAD domains - search for "fead" keyword  
        fead_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(domain) LIKE '%fead%'").fetchone()[0]
        fead_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(domain) LIKE '%fead%' AND LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        fead_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(domain) LIKE '%fead%' AND LOWER(present_in_cmdb) = 'yes'").fetchone()[0]
        fead_crowdstrike = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(domain) LIKE '%fead%' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%'").fetchone()[0]
        
        conn.close()
        
        return jsonify({
            '1dc': {
                'total': dc1_total,
                'splunk_coverage': calculate_coverage_percentage(dc1_splunk, dc1_total),
                'cmdb_coverage': calculate_coverage_percentage(dc1_cmdb, dc1_total),
                'crowdstrike_coverage': calculate_coverage_percentage(dc1_crowdstrike, dc1_total),
                'overall_coverage': calculate_coverage_percentage(dc1_splunk + dc1_cmdb + dc1_crowdstrike, dc1_total * 3)
            },
            'fead': {
                'total': fead_total,
                'splunk_coverage': calculate_coverage_percentage(fead_splunk, fead_total),
                'cmdb_coverage': calculate_coverage_percentage(fead_cmdb, fead_total),
                'crowdstrike_coverage': calculate_coverage_percentage(fead_crowdstrike, fead_total),
                'overall_coverage': calculate_coverage_percentage(fead_splunk + fead_cmdb + fead_crowdstrike, fead_total * 3)
            }
        })
        
    except Exception as e:
        logger.error(f"domain_visibility failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regional-country-view')
def regional_country_view():
    """Regional Analysis and Geographic Breakdown - Primary Metrics #3 & #4"""
    try:
        conn = get_db_connection()
        
        # Get all region data
        region_data = conn.execute("""
            SELECT region, country, data_center, cloud_region,
                   CASE WHEN LOWER(present_in_cmdb) = 'yes' THEN 1 ELSE 0 END as cmdb,
                   CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END as splunk,
                   CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 ELSE 0 END as crowdstrike
            FROM universal_cmdb 
            WHERE region IS NOT NULL
        """).fetchall()
        
        # Regional analysis with standardization
        regions = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        countries = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        data_centers = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        cloud_regions = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        
        for row in region_data:
            region_raw, country_raw, dc_raw, cloud_raw, cmdb, splunk, crowdstrike = row
            
            # Process regions with standardization
            if region_raw:
                region_parts = parse_multi_values(region_raw, ['|', ','])
                for region_part in region_parts:
                    std_region = standardize_region(region_part)
                    regions[std_region]['total'] += 1
                    regions[std_region]['cmdb'] += cmdb
                    regions[std_region]['splunk'] += splunk
                    regions[std_region]['crowdstrike'] += crowdstrike
            
            # Process countries (split by , and |)
            if country_raw:
                country_parts = parse_multi_values(country_raw, ['|', ','])
                for country in country_parts:
                    countries[country]['total'] += 1
                    countries[country]['cmdb'] += cmdb
                    countries[country]['splunk'] += splunk
                    countries[country]['crowdstrike'] += crowdstrike
            
            # Process data centers (split by , and |)
            if dc_raw:
                dc_parts = parse_multi_values(dc_raw, ['|', ','])
                for dc in dc_parts:
                    data_centers[dc]['total'] += 1
                    data_centers[dc]['cmdb'] += cmdb
                    data_centers[dc]['splunk'] += splunk
                    data_centers[dc]['crowdstrike'] += crowdstrike
            
            # Process cloud regions (split by , and |)
            if cloud_raw:
                cloud_parts = parse_multi_values(cloud_raw, ['|', ','])
                for cloud in cloud_parts:
                    cloud_regions[cloud]['total'] += 1
                    cloud_regions[cloud]['cmdb'] += cmdb
                    cloud_regions[cloud]['splunk'] += splunk
                    cloud_regions[cloud]['crowdstrike'] += crowdstrike
        
        # Calculate percentages for all categories
        def calculate_stats(data_dict):
            result = {}
            for key, stats in data_dict.items():
                total = stats['total']
                result[key] = {
                    'total': total,
                    'cmdb_coverage': calculate_coverage_percentage(stats['cmdb'], total),
                    'splunk_coverage': calculate_coverage_percentage(stats['splunk'], total),
                    'crowdstrike_coverage': calculate_coverage_percentage(stats['crowdstrike'], total),
                    'overall_coverage': calculate_coverage_percentage(stats['cmdb'] + stats['splunk'] + stats['crowdstrike'], total * 3)
                }
            return result
        
        conn.close()
        
        return jsonify({
            'regions': calculate_stats(regions),
            'countries': calculate_stats(dict(sorted(countries.items(), key=lambda x: x[1]['total'], reverse=True)[:20])),
            'data_centers': calculate_stats(dict(sorted(data_centers.items(), key=lambda x: x[1]['total'], reverse=True)[:15])),
            'cloud_regions': calculate_stats(dict(sorted(cloud_regions.items(), key=lambda x: x[1]['total'], reverse=True)[:10]))
        })
        
    except Exception as e:
        logger.error(f"regional_country_view failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bu-application-view')
def bu_application_view():
    """Organizational Metrics - Primary Metrics #5"""
    try:
        conn = get_db_connection()
        
        # Get all organizational data
        org_data = conn.execute("""
            SELECT cio, business_unit, system_classification,
                   CASE WHEN LOWER(present_in_cmdb) = 'yes' THEN 1 ELSE 0 END as cmdb,
                   CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END as splunk,
                   CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 ELSE 0 END as crowdstrike
            FROM universal_cmdb
        """).fetchall()
        
        # CIO Analysis (letters only, no numbers)
        cio_stats = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        
        # Business Unit Analysis (split by commas)
        bu_stats = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        
        # System Classification Analysis (split by pipes)
        sys_class_stats = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        
        for row in org_data:
            cio_raw, bu_raw, sys_class_raw, cmdb, splunk, crowdstrike = row
            
            # Process CIO (only alphabetic values)
            if cio_raw and is_valid_cio(cio_raw):
                cio_stats[str(cio_raw).strip()]['total'] += 1
                cio_stats[str(cio_raw).strip()]['cmdb'] += cmdb
                cio_stats[str(cio_raw).strip()]['splunk'] += splunk
                cio_stats[str(cio_raw).strip()]['crowdstrike'] += crowdstrike
            
            # Process Business Units (split by commas)
            if bu_raw:
                bu_parts = parse_multi_values(bu_raw, [','])
                for bu in bu_parts:
                    bu_stats[bu]['total'] += 1
                    bu_stats[bu]['cmdb'] += cmdb
                    bu_stats[bu]['splunk'] += splunk
                    bu_stats[bu]['crowdstrike'] += crowdstrike
            
            # Process System Classifications (split by pipes)
            if sys_class_raw:
                sys_parts = parse_multi_values(sys_class_raw, ['|'])
                for sys_class in sys_parts:
                    sys_class_stats[sys_class]['total'] += 1
                    sys_class_stats[sys_class]['cmdb'] += cmdb
                    sys_class_stats[sys_class]['splunk'] += splunk
                    sys_class_stats[sys_class]['crowdstrike'] += crowdstrike
        
        def calculate_org_stats(data_dict):
            result = {}
            for key, stats in data_dict.items():
                total = stats['total']
                result[key] = {
                    'total': total,
                    'cmdb_coverage': calculate_coverage_percentage(stats['cmdb'], total),
                    'splunk_coverage': calculate_coverage_percentage(stats['splunk'], total),
                    'crowdstrike_coverage': calculate_coverage_percentage(stats['crowdstrike'], total),
                    'overall_coverage': calculate_coverage_percentage(stats['cmdb'] + stats['splunk'] + stats['crowdstrike'], total * 3)
                }
            return result
        
        conn.close()
        
        return jsonify({
            'cio_analysis': calculate_org_stats(dict(sorted(cio_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:20])),
            'business_units': calculate_org_stats(dict(sorted(bu_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:25])),
            'system_classifications': calculate_org_stats(dict(sorted(sys_class_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:30]))
        })
        
    except Exception as e:
        logger.error(f"bu_application_view failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-classification')
def system_classification():
    """Class Analysis and Infrastructure Type Analysis - Primary Metrics #6"""
    try:
        conn = get_db_connection()
        
        # Get class and infrastructure data
        class_data = conn.execute("""
            SELECT class, infrastructure_type,
                   CASE WHEN LOWER(present_in_cmdb) = 'yes' THEN 1 ELSE 0 END as cmdb,
                   CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END as splunk,
                   CASE WHEN LOWER(edr_coverage) LIKE '%crowdstrike agent%' THEN 1 ELSE 0 END as crowdstrike
            FROM universal_cmdb
        """).fetchall()
        
        # Class Analysis - extract class numbers
        class_numbers = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        
        # Infrastructure Type Analysis (split by pipes)
        infra_types = defaultdict(lambda: {'total': 0, 'cmdb': 0, 'splunk': 0, 'crowdstrike': 0})
        
        for row in class_data:
            class_raw, infra_raw, cmdb, splunk, crowdstrike = row
            
            # Process class numbers
            if class_raw:
                class_nums = extract_class_numbers(class_raw)
                for class_num in class_nums:
                    class_numbers[class_num]['total'] += 1
                    class_numbers[class_num]['cmdb'] += cmdb
                    class_numbers[class_num]['splunk'] += splunk
                    class_numbers[class_num]['crowdstrike'] += crowdstrike
            
            # Process infrastructure types (split by pipes)
            if infra_raw:
                infra_parts = parse_multi_values(infra_raw, ['|'])
                for infra_type in infra_parts:
                    infra_types[infra_type]['total'] += 1
                    infra_types[infra_type]['cmdb'] += cmdb
                    infra_types[infra_type]['splunk'] += splunk
                    infra_types[infra_type]['crowdstrike'] += crowdstrike
        
        def calculate_system_stats(data_dict):
            result = {}
            for key, stats in data_dict.items():
                total = stats['total']
                result[key] = {
                    'total': total,
                    'cmdb_coverage': calculate_coverage_percentage(stats['cmdb'], total),
                    'splunk_coverage': calculate_coverage_percentage(stats['splunk'], total),
                    'crowdstrike_coverage': calculate_coverage_percentage(stats['crowdstrike'], total),
                    'overall_coverage': calculate_coverage_percentage(stats['cmdb'] + stats['splunk'] + stats['crowdstrike'], total * 3)
                }
            return result
        
        conn.close()
        
        return jsonify({
            'class_numbers': calculate_system_stats(dict(sorted(class_numbers.items(), key=lambda x: x[0]))),
            'infrastructure_types': calculate_system_stats(dict(sorted(infra_types.items(), key=lambda x: x[1]['total'], reverse=True)[:25]))
        })
        
    except Exception as e:
        logger.error(f"system_classification failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/security-control-coverage')
def security_control_coverage():
    """Security Control Coverage Analysis"""
    try:
        conn = get_db_connection()
        
        total_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        # Individual tool coverage
        cmdb_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(present_in_cmdb) = 'yes'").fetchone()[0]
        crowdstrike_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(edr_coverage) LIKE '%crowdstrike agent%'").fetchone()[0]
        splunk_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        tanium_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(tanium_coverage) LIKE '%tanium%'").fetchone()[0]
        
        # Overlap analysis
        cmdb_crowdstrike = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(present_in_cmdb) = 'yes' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%'").fetchone()[0]
        cmdb_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(present_in_cmdb) = 'yes' AND LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        crowdstrike_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(edr_coverage) LIKE '%crowdstrike agent%' AND LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        triple_coverage = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(present_in_cmdb) = 'yes' AND LOWER(edr_coverage) LIKE '%crowdstrike agent%' AND LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_hosts': total_hosts,
            'individual_coverage': {
                'cmdb': {
                    'count': cmdb_count,
                    'percentage': calculate_coverage_percentage(cmdb_count, total_hosts)
                },
                'crowdstrike': {
                    'count': crowdstrike_count,
                    'percentage': calculate_coverage_percentage(crowdstrike_count, total_hosts)
                },
                'splunk': {
                    'count': splunk_count,
                    'percentage': calculate_coverage_percentage(splunk_count, total_hosts)
                },
                'tanium': {
                    'count': tanium_count,
                    'percentage': calculate_coverage_percentage(tanium_count, total_hosts)
                }
            },
            'overlap_analysis': {
                'cmdb_crowdstrike': {
                    'count': cmdb_crowdstrike,
                    'percentage': calculate_coverage_percentage(cmdb_crowdstrike, total_hosts)
                },
                'cmdb_splunk': {
                    'count': cmdb_splunk,
                    'percentage': calculate_coverage_percentage(cmdb_splunk, total_hosts)
                },
                'crowdstrike_splunk': {
                    'count': crowdstrike_splunk,
                    'percentage': calculate_coverage_percentage(crowdstrike_splunk, total_hosts)
                },
                'triple_coverage': {
                    'count': triple_coverage,
                    'percentage': calculate_coverage_percentage(triple_coverage, total_hosts)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"security_control_coverage failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logging-compliance-gso-splunk')
def logging_compliance_gso_splunk():
    """Logging Compliance Analysis"""
    try:
        conn = get_db_connection()
        
        total_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        # Logging platform coverage
        splunk_only = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(logging_in_splunk) = 'yes' AND (LOWER(logging_in_gso) != 'yes' OR logging_in_gso IS NULL)").fetchone()[0]
        gso_only = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(logging_in_gso) = 'yes' AND (LOWER(logging_in_splunk) != 'yes' OR logging_in_splunk IS NULL)").fetchone()[0]
        both_platforms = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(logging_in_splunk) = 'yes' AND LOWER(logging_in_gso) = 'yes'").fetchone()[0]
        no_logging = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE (LOWER(logging_in_splunk) != 'yes' OR logging_in_splunk IS NULL) AND (LOWER(logging_in_gso) != 'yes' OR logging_in_gso IS NULL)").fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_hosts': total_hosts,
            'logging_distribution': {
                'splunk_only': {
                    'count': splunk_only,
                    'percentage': calculate_coverage_percentage(splunk_only, total_hosts)
                },
                'gso_only': {
                    'count': gso_only,
                    'percentage': calculate_coverage_percentage(gso_only, total_hosts)
                },
                'both_platforms': {
                    'count': both_platforms,
                    'percentage': calculate_coverage_percentage(both_platforms, total_hosts)
                },
                'no_logging': {
                    'count': no_logging,
                    'percentage': calculate_coverage_percentage(no_logging, total_hosts)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"logging_compliance_gso_splunk failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/log-type-priority')
def log_type_priority():
    """Log Type Priority Analysis"""
    try:
        conn = get_db_connection()
        
        # APM coverage analysis
        total_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        apm_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(apm) LIKE '%apm%'").fetchone()[0]
        apm_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(apm) LIKE '%apm%' AND LOWER(logging_in_splunk) = 'yes'").fetchone()[0]
        apm_gso = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(apm) LIKE '%apm%' AND LOWER(logging_in_gso) = 'yes'").fetchone()[0]
        apm_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(apm) LIKE '%apm%' AND LOWER(present_in_cmdb) = 'yes'").fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_hosts': total_hosts,
            'apm_analysis': {
                'total_apm_hosts': apm_hosts,
                'apm_percentage': calculate_coverage_percentage(apm_hosts, total_hosts),
                'apm_splunk_coverage': calculate_coverage_percentage(apm_splunk, apm_hosts),
                'apm_gso_coverage': calculate_coverage_percentage(apm_gso, apm_hosts),
                'apm_cmdb_coverage': calculate_coverage_percentage(apm_cmdb, apm_hosts),
                'overall_apm_priority': calculate_coverage_percentage(apm_splunk + apm_gso + apm_cmdb, apm_hosts * 3)
            }
        })
        
    except Exception as e:
        logger.error(f"log_type_priority failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application with complete CMDB metrics")
    app.run(debug=True, host='0.0.0.0', port=5000)