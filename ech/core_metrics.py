from flask import jsonify
import logging
import duckdb
from collections import Counter, defaultdict
import re
import os

logger = logging.getLogger(__name__)

def get_db_connection():
    """Shared database connection function"""
    db_paths = ['universal_cmdb.db', './universal_cmdb.db', '../universal_cmdb.db', os.path.join(os.getcwd(), 'universal_cmdb.db')]
    
    for db_path in db_paths:
        try:
            if os.path.exists(db_path):
                conn = duckdb.connect(db_path, read_only=True)
                tables = conn.execute("SHOW TABLES").fetchall()
                if any('universal_cmdb' in str(table).lower() for table in tables):
                    return conn
                conn.close()
        except Exception:
            continue
    raise Exception("Database not found")

def parse_pipe_separated(value):
    """Parse pipe-separated values safely"""
    if not value or str(value).lower() in ['null', 'none', 'unknown', '']:
        return []
    return [v.strip() for v in str(value).split('|') if v.strip()]

def parse_comma_separated(value):
    """Parse comma-separated values safely"""
    if not value or str(value).lower() in ['null', 'none', 'unknown', '']:
        return []
    return [v.strip() for v in str(value).split(',') if v.strip()]

def normalize_region(region):
    """Normalize regions to North America, EMEA, LATAM, APAC"""
    if not region:
        return 'Unknown'
    region_lower = region.lower().strip()
    
    if any(x in region_lower for x in ['us', 'usa', 'united states', 'canada', 'north america', 'mexico']):
        return 'North America'
    elif any(x in region_lower for x in ['europe', 'emea', 'uk', 'germany', 'france', 'spain', 'italy']):
        return 'EMEA' 
    elif any(x in region_lower for x in ['asia', 'apac', 'pacific', 'japan', 'china', 'india', 'australia']):
        return 'APAC'
    elif any(x in region_lower for x in ['latin', 'latam', 'south america', 'brazil', 'argentina']):
        return 'LATAM'
    return 'Other'

def get_global_visibility_metrics():
    """1. Global View - CSOC able to view X% of all assets globally"""
    try:
        conn = get_db_connection()
        
        # Total assets
        total_assets = conn.execute("SELECT COUNT(DISTINCT host) FROM universal_cmdb").fetchone()[0]
        
        # Assets with logging coverage (Splunk OR GSO)
        logging_covered = conn.execute("""
            SELECT COUNT(DISTINCT host) FROM universal_cmdb 
            WHERE LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
               OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
               OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%yes%'
               OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%gso%'
        """).fetchone()[0]
        
        # CMDB registered assets  
        cmdb_registered = conn.execute("""
            SELECT COUNT(DISTINCT host) FROM universal_cmdb 
            WHERE LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%'
        """).fetchone()[0]
        
        # Security monitored assets (Tanium)
        tanium_covered = conn.execute("""
            SELECT COUNT(DISTINCT host) FROM universal_cmdb 
            WHERE LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%'
        """).fetchone()[0]
        
        # Calculate visibility percentages
        global_logging_visibility = (logging_covered / total_assets * 100) if total_assets > 0 else 0
        cmdb_visibility = (cmdb_registered / total_assets * 100) if total_assets > 0 else 0
        security_visibility = (tanium_covered / total_assets * 100) if total_assets > 0 else 0
        
        # Overall CSOC visibility (primary metric)
        overall_visibility = global_logging_visibility  # Primary focus on logging per requirements
        
        # Threat assessment based on visibility gaps
        threat_level = 'CRITICAL' if overall_visibility < 60 else 'HIGH' if overall_visibility < 80 else 'NOMINAL'
        
        conn.close()
        
        return jsonify({
            'neural_status': 'ACTIVE',
            'global_metrics': {
                'total_assets': total_assets,
                'logging_visibility_percentage': round(global_logging_visibility, 2),
                'cmdb_visibility_percentage': round(cmdb_visibility, 2),
                'security_visibility_percentage': round(security_visibility, 2),
                'overall_csoc_visibility': round(overall_visibility, 2)
            },
            'coverage_breakdown': {
                'logging_covered_assets': logging_covered,
                'cmdb_registered_assets': cmdb_registered, 
                'tanium_covered_assets': tanium_covered,
                'visibility_gap': total_assets - logging_covered
            },
            'threat_assessment': {
                'current_threat_level': threat_level,
                'visibility_status': 'OPTIMAL' if overall_visibility >= 90 else 'ACCEPTABLE' if overall_visibility >= 75 else 'SUBOPTIMAL',
                'assets_at_risk': total_assets - logging_covered
            }
        })
    except Exception as e:
        logger.error(f"Global visibility error: {e}")
        return jsonify({'error': str(e), 'neural_status': 'COMPROMISED'}), 500

def get_infrastructure_visibility_breakdown():
    """2. Infrastructure Type - % visibility by host/log type across infrastructure"""
    try:
        conn = get_db_connection()
        
        # Get infrastructure data with visibility metrics
        result = conn.execute("""
            SELECT 
                COALESCE(infrastructure_type, 'unknown') as infra_type,
                COUNT(DISTINCT host) as total_assets,
                SUM(CASE WHEN LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
                         OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
                         OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%yes%'
                         OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%gso%' THEN 1 ELSE 0 END) as logging_covered,
                SUM(CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 1 ELSE 0 END) as cmdb_registered,
                SUM(CASE WHEN LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%' THEN 1 ELSE 0 END) as tanium_deployed
            FROM universal_cmdb
            GROUP BY infrastructure_type
            ORDER BY total_assets DESC
        """).fetchall()
        
        infrastructure_metrics = {}
        category_rollup = {'On-Prem': 0, 'Cloud': 0, 'SaaS': 0, 'API': 0, 'Other': 0}
        
        for row in result:
            infra_str, total, logging, cmdb, tanium = row
            
            # Parse pipe-separated infrastructure types
            infra_types = parse_pipe_separated(infra_str)
            if not infra_types:
                infra_types = [infra_str if infra_str != 'unknown' else 'Other']
            
            for infra_type in infra_types:
                if infra_type not in infrastructure_metrics:
                    infrastructure_metrics[infra_type] = {'total': 0, 'logging': 0, 'cmdb': 0, 'tanium': 0}
                
                infrastructure_metrics[infra_type]['total'] += total
                infrastructure_metrics[infra_type]['logging'] += logging
                infrastructure_metrics[infra_type]['cmdb'] += cmdb
                infrastructure_metrics[infra_type]['tanium'] += tanium
                
                # Categorize for rollup
                category = 'Other'
                infra_lower = infra_type.lower()
                if any(x in infra_lower for x in ['on-prem', 'onprem', 'server', 'datacenter', 'physical']):
                    category = 'On-Prem'
                elif any(x in infra_lower for x in ['cloud', 'aws', 'azure', 'gcp']):
                    category = 'Cloud'
                elif 'saas' in infra_lower or 'application' in infra_lower:
                    category = 'SaaS'
                elif 'api' in infra_lower:
                    category = 'API'
                
                category_rollup[category] += total
        
        # Calculate visibility percentages
        visibility_analysis = []
        for infra_type, metrics in infrastructure_metrics.items():
            total = metrics['total']
            if total > 0:
                logging_visibility = round((metrics['logging'] / total * 100), 2)
                visibility_analysis.append({
                    'infrastructure_type': infra_type,
                    'total_assets': total,
                    'logging_visibility_percentage': logging_visibility,
                    'cmdb_coverage': round((metrics['cmdb'] / total * 100), 2),
                    'tanium_coverage': round((metrics['tanium'] / total * 100), 2),
                    'visibility_status': 'OPTIMAL' if logging_visibility >= 90 else 'ACCEPTABLE' if logging_visibility >= 75 else 'SUBOPTIMAL'
                })
        
        visibility_analysis.sort(key=lambda x: x['total_assets'], reverse=True)
        
        conn.close()
        
        return jsonify({
            'neural_pathway': 'BETA',
            'infrastructure_visibility': visibility_analysis[:20],  # Top 20
            'category_summary': category_rollup,
            'total_infrastructure_types': len(infrastructure_metrics)
        })
        
    except Exception as e:
        logger.error(f"Infrastructure visibility error: {e}")
        return jsonify({'error': str(e)}), 500

def get_regional_country_visibility():
    """3. Regional and Country View - Visibility by location"""
    try:
        conn = get_db_connection()
        
        # Regional analysis
        regional_data = conn.execute("""
            SELECT 
                COALESCE(region, 'unknown') as region,
                COUNT(DISTINCT host) as total_assets,
                SUM(CASE WHEN LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
                         OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
                         OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%yes%'
                         OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%gso%' THEN 1 ELSE 0 END) as logging_covered,
                SUM(CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 1 ELSE 0 END) as cmdb_registered
            FROM universal_cmdb
            GROUP BY region
        """).fetchall()
        
        regional_aggregates = defaultdict(lambda: {'total': 0, 'logging': 0, 'cmdb': 0})
        
        for region_str, total, logging, cmdb in regional_data:
            regions = parse_pipe_separated(region_str)
            if not regions:
                regions = [region_str]
                
            for region in regions:
                normalized = normalize_region(region)
                regional_aggregates[normalized]['total'] += total
                regional_aggregates[normalized]['logging'] += logging  
                regional_aggregates[normalized]['cmdb'] += cmdb
        
        regional_visibility = []
        for region, metrics in regional_aggregates.items():
            total = metrics['total']
            if total > 0:
                logging_vis = round((metrics['logging'] / total * 100), 2)
                regional_visibility.append({
                    'region': region,
                    'total_assets': total,
                    'logging_visibility_percentage': logging_vis,
                    'cmdb_coverage': round((metrics['cmdb'] / total * 100), 2),
                    'visibility_status': 'OPTIMAL' if logging_vis >= 90 else 'ACCEPTABLE' if logging_vis >= 75 else 'SUBOPTIMAL'
                })
        
        # Country analysis
        country_data = conn.execute("""
            SELECT 
                COALESCE(country, 'unknown') as country,
                COUNT(DISTINCT host) as total_assets,
                SUM(CASE WHEN LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
                         OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
                         OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%yes%'
                         OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%gso%' THEN 1 ELSE 0 END) as logging_covered
            FROM universal_cmdb
            GROUP BY country
            ORDER BY total_assets DESC
            LIMIT 15
        """).fetchall()
        
        country_visibility = []
        for country_str, total, logging in country_data:
            countries = parse_pipe_separated(country_str)
            if not countries:
                countries = [country_str]
                
            for country in countries:
                if country != 'unknown' and total > 0:
                    logging_vis = round((logging / total * 100), 2)
                    country_visibility.append({
                        'country': country.title(),
                        'total_assets': total,
                        'logging_visibility_percentage': logging_vis
                    })
        
        regional_visibility.sort(key=lambda x: x['total_assets'], reverse=True)
        country_visibility.sort(key=lambda x: x['total_assets'], reverse=True)
        
        conn.close()
        
        return jsonify({
            'neural_pathway': 'GAMMA',
            'regional_visibility': regional_visibility,
            'country_visibility': country_visibility[:10],
            'geospatial_coverage': {
                'regions_monitored': len(regional_visibility),
                'countries_tracked': len(country_visibility)
            }
        })
        
    except Exception as e:
        logger.error(f"Regional/Country visibility error: {e}")
        return jsonify({'error': str(e)}), 500

def get_domain_visibility_metrics():
    """8. Domain Visibility - Asset visibility by hostname and domain""" 
    try:
        conn = get_db_connection()
        
        # Domain analysis (1dc vs fead - one count per row max)
        domain_result = conn.execute("""
            SELECT 
                host,
                COALESCE(domain, '') as domain,
                CASE WHEN LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
                          OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
                          OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%yes%'
                          OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%gso%' THEN 1 ELSE 0 END as has_logging,
                CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 1 ELSE 0 END as in_cmdb
            FROM universal_cmdb
        """).fetchall()
        
        domain_stats = {'1dc': 0, 'fead': 0, 'both': 0, 'other': 0}
        domain_visibility = defaultdict(lambda: {'total': 0, 'logging': 0, 'cmdb': 0})
        
        for host, domain_str, has_logging, in_cmdb in domain_result:
            domains = parse_pipe_separated(domain_str)
            
            has_1dc = any('1dc' in d.lower() for d in domains)
            has_fead = any('fead' in d.lower() for d in domains)
            
            # Count once per row (as specified in requirements)
            if has_1dc and has_fead:
                domain_stats['both'] += 1
                domain_visibility['both']['total'] += 1
                if has_logging:
                    domain_visibility['both']['logging'] += 1
                if in_cmdb:
                    domain_visibility['both']['cmdb'] += 1
            elif has_1dc:
                domain_stats['1dc'] += 1
                domain_visibility['1dc']['total'] += 1
                if has_logging:
                    domain_visibility['1dc']['logging'] += 1
                if in_cmdb:
                    domain_visibility['1dc']['cmdb'] += 1
            elif has_fead:
                domain_stats['fead'] += 1  
                domain_visibility['fead']['total'] += 1
                if has_logging:
                    domain_visibility['fead']['logging'] += 1
                if in_cmdb:
                    domain_visibility['fead']['cmdb'] += 1
            else:
                domain_stats['other'] += 1
                domain_visibility['other']['total'] += 1
                if has_logging:
                    domain_visibility['other']['logging'] += 1
                if in_cmdb:
                    domain_visibility['other']['cmdb'] += 1
        
        # Calculate visibility percentages per domain
        domain_analysis = []
        for domain_type, stats in domain_visibility.items():
            if stats['total'] > 0:
                logging_vis = round((stats['logging'] / stats['total'] * 100), 2)
                domain_analysis.append({
                    'domain_type': domain_type,
                    'total_assets': stats['total'],
                    'logging_visibility_percentage': logging_vis,
                    'cmdb_coverage': round((stats['cmdb'] / stats['total'] * 100), 2),
                    'visibility_status': 'OPTIMAL' if logging_vis >= 90 else 'ACCEPTABLE' if logging_vis >= 75 else 'SUBOPTIMAL'
                })
        
        total_assets = sum(domain_stats.values())
        
        conn.close()
        
        return jsonify({
            'neural_pathway': 'OMEGA',
            'domain_distribution': domain_stats,
            'domain_visibility_analysis': domain_analysis,
            'domain_percentages': {
                '1dc_percentage': round((domain_stats['1dc'] / total_assets * 100), 2) if total_assets > 0 else 0,
                'fead_percentage': round((domain_stats['fead'] / total_assets * 100), 2) if total_assets > 0 else 0,
                'dual_domain_assets': domain_stats['both']
            },
            'warfare_status': '1DC_DOMINANT' if domain_stats['1dc'] > domain_stats['fead'] else 'FEAD_DOMINANT' if domain_stats['fead'] > domain_stats['1dc'] else 'BALANCED'
        })
        
    except Exception as e:
        logger.error(f"Domain visibility error: {e}")
        return jsonify({'error': str(e)}), 500