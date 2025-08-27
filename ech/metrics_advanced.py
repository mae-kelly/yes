from flask import jsonify
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from database_utils import *

logger = logging.getLogger(__name__)

def get_splunk_coverage():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
                         OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%' THEN 'deployed'
                    ELSE 'not_deployed'
                END as status,
                COUNT(*) as count,
                COALESCE(region, 'unknown') as region
            FROM universal_cmdb
            GROUP BY 
                CASE WHEN LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
                          OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%' THEN 'deployed' 
                     ELSE 'not_deployed' END,
                region
        """).fetchall()
        
        splunk_deployed = 0
        total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        regional_coverage = defaultdict(lambda: {'deployed': 0, 'total': 0})
        
        for row in result:
            status, count, region = row
            if status == 'deployed':
                splunk_deployed += count
            
            normalized_region = normalize_region(region)
            regional_coverage[normalized_region]['total'] += count
            if status == 'deployed':
                regional_coverage[normalized_region]['deployed'] += count
        
        coverage_percentage = (splunk_deployed / total_assets * 100) if total_assets > 0 else 0
        
        conn.close()
        
        return jsonify({
            'splunk_deployed': splunk_deployed,
            'total_assets': total_assets,
            'coverage_percentage': round(coverage_percentage, 2),
            'regional_coverage': dict(regional_coverage),
            'deployment_status': 'OPTIMAL' if coverage_percentage >= 80 else 'CRITICAL' if coverage_percentage < 60 else 'ACCEPTABLE'
        })
    except Exception as e:
        logger.error(f"Splunk coverage error: {e}")
        return jsonify({'error': str(e)}), 500

def get_logging_platforms():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(logging_in_splunk, 'unknown') as splunk_status,
                COALESCE(logging_in_gso, 'unknown') as gso_status,
                COUNT(*) as count
            FROM universal_cmdb
            GROUP BY logging_in_splunk, logging_in_gso
        """).fetchall()
        
        platform_matrix = {'splunk_only': 0, 'gso_only': 0, 'both_platforms': 0, 'no_logging': 0}
        
        for row in result:
            splunk_status, gso_status, count = row
            
            splunk_enabled = 'yes' in str(splunk_status).lower() or 'splunk' in str(splunk_status).lower()
            gso_enabled = 'yes' in str(gso_status).lower() or 'gso' in str(gso_status).lower()
            
            if splunk_enabled and gso_enabled:
                platform_matrix['both_platforms'] += count
            elif splunk_enabled:
                platform_matrix['splunk_only'] += count
            elif gso_enabled:
                platform_matrix['gso_only'] += count
            else:
                platform_matrix['no_logging'] += count
        
        total_assets = sum(platform_matrix.values())
        
        platform_analytics = {}
        for platform, count in platform_matrix.items():
            percentage = (count / total_assets * 100) if total_assets > 0 else 0
            platform_analytics[platform] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        conn.close()
        
        return jsonify({
            'platform_matrix': platform_matrix,
            'platform_analytics': platform_analytics,
            'logging_coverage': {
                'total_with_logging': platform_matrix['splunk_only'] + platform_matrix['gso_only'] + platform_matrix['both_platforms'],
                'dual_platform_coverage': platform_matrix['both_platforms'],
                'logging_gap': platform_matrix['no_logging']
            }
        })
    except Exception as e:
        logger.error(f"Logging platforms error: {e}")
        return jsonify({'error': str(e)}), 500

def get_ssc_coverage():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(ssc_coverage, 'unknown') as ssc_status,
                COUNT(*) as count
            FROM universal_cmdb
            GROUP BY ssc_coverage
            ORDER BY count DESC
        """).fetchall()
        
        ssc_deployed = 0
        ssc_analytics = {}
        total_assets = sum(row[1] for row in result)
        
        for row in result:
            ssc_status, count = row
            if ssc_status and ssc_status != 'unknown' and 'null' not in str(ssc_status).lower():
                ssc_deployed += count
                ssc_analytics[ssc_status] = {
                    'count': count,
                    'percentage': round((count / total_assets * 100), 2) if total_assets > 0 else 0
                }
        
        coverage_percentage = (ssc_deployed / total_assets * 100) if total_assets > 0 else 0
        
        conn.close()
        
        return jsonify({
            'ssc_deployed': ssc_deployed,
            'total_assets': total_assets,
            'coverage_percentage': round(coverage_percentage, 2),
            'ssc_analytics': ssc_analytics,
            'deployment_status': 'OPTIMAL' if coverage_percentage >= 70 else 'CRITICAL' if coverage_percentage < 30 else 'ACCEPTABLE'
        })
    except Exception as e:
        logger.error(f"SSC coverage error: {e}")
        return jsonify({'error': str(e)}), 500

def get_dlp_coverage():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(COALESCE(dlp_agent_coverage, '')) LIKE '%dlp%' 
                         OR LOWER(COALESCE(dlp_agent_coverage, '')) LIKE '%agent%' THEN 'deployed'
                    ELSE 'not_deployed'
                END as status,
                COUNT(*) as count
            FROM universal_cmdb
            GROUP BY 
                CASE WHEN LOWER(COALESCE(dlp_agent_coverage, '')) LIKE '%dlp%' 
                          OR LOWER(COALESCE(dlp_agent_coverage, '')) LIKE '%agent%' THEN 'deployed' 
                     ELSE 'not_deployed' END
        """).fetchall()
        
        dlp_deployed = 0
        total_assets = sum(row[1] for row in result)
        
        for row in result:
            status, count = row
            if status == 'deployed':
                dlp_deployed = count
        
        coverage_percentage = (dlp_deployed / total_assets * 100) if total_assets > 0 else 0
        
        conn.close()
        
        return jsonify({
            'dlp_deployed': dlp_deployed,
            'total_assets': total_assets,
            'coverage_percentage': round(coverage_percentage, 2),
            'deployment_gap': total_assets - dlp_deployed,
            'deployment_status': 'OPTIMAL' if coverage_percentage >= 80 else 'CRITICAL' if coverage_percentage < 60 else 'ACCEPTABLE'
        })
    except Exception as e:
        logger.error(f"DLP coverage error: {e}")
        return jsonify({'error': str(e)}), 500

def get_crowdstrike_coverage():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%yes%' 
                         OR LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%crowdstrike%' THEN 'deployed'
                    ELSE 'not_deployed'
                END as status,
                COUNT(*) as count
            FROM universal_cmdb
            GROUP BY 
                CASE WHEN LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%yes%' 
                          OR LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%crowdstrike%' THEN 'deployed' 
                     ELSE 'not_deployed' END
        """).fetchall()
        
        crowdstrike_deployed = 0
        total_assets = sum(row[1] for row in result)
        
        for row in result:
            status, count = row
            if status == 'deployed':
                crowdstrike_deployed = count
        
        coverage_percentage = (crowdstrike_deployed / total_assets * 100) if total_assets > 0 else 0
        
        conn.close()
        
        return jsonify({
            'crowdstrike_deployed': crowdstrike_deployed,
            'total_assets': total_assets,
            'coverage_percentage': round(coverage_percentage, 2),
            'deployment_gap': total_assets - crowdstrike_deployed,
            'deployment_status': 'OPTIMAL' if coverage_percentage >= 80 else 'CRITICAL' if coverage_percentage < 60 else 'ACCEPTABLE'
        })
    except Exception as e:
        logger.error(f"Crowdstrike coverage error: {e}")
        return jsonify({'error': str(e)}), 500

def get_temporal_analysis():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(last_detected_ts, '1970-01-01') as last_detected,
                COALESCE(created_ts, '1970-01-01') as created,
                COALESCE(modified_ts, '1970-01-01') as modified,
                COUNT(*) as count
            FROM universal_cmdb
            WHERE last_detected_ts IS NOT NULL OR created_ts IS NOT NULL OR modified_ts IS NOT NULL
            GROUP BY last_detected_ts, created_ts, modified_ts
            ORDER BY count DESC
            LIMIT 100
        """).fetchall()
        
        temporal_patterns = {
            'recently_detected': 0,
            'stale_assets': 0,
            'newly_created': 0,
            'recently_modified': 0
        }
        
        current_time = datetime.now()
        thirty_days_ago = current_time - timedelta(days=30)
        
        for row in result:
            last_detected, created, modified, count = row
            
            try:
                if last_detected != '1970-01-01':
                    last_detected_dt = datetime.strptime(last_detected[:10], '%Y-%m-%d')
                    if last_detected_dt >= thirty_days_ago:
                        temporal_patterns['recently_detected'] += count
                    else:
                        temporal_patterns['stale_assets'] += count
                
                if created != '1970-01-01':
                    created_dt = datetime.strptime(created[:10], '%Y-%m-%d')
                    if created_dt >= thirty_days_ago:
                        temporal_patterns['newly_created'] += count
                
                if modified != '1970-01-01':
                    modified_dt = datetime.strptime(modified[:10], '%Y-%m-%d')
                    if modified_dt >= thirty_days_ago:
                        temporal_patterns['recently_modified'] += count
            except (ValueError, TypeError):
                continue
        
        total_temporal_assets = sum(temporal_patterns.values())
        
        temporal_analytics = {}
        for pattern, count in temporal_patterns.items():
            percentage = (count / total_temporal_assets * 100) if total_temporal_assets > 0 else 0
            temporal_analytics[pattern] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        conn.close()
        
        return jsonify({
            'temporal_patterns': temporal_patterns,
            'temporal_analytics': temporal_analytics})
    