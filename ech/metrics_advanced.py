from flask import jsonify, request
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from database_utils import *
import json

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
            'temporal_analytics': temporal_analytics,
            'staleness_ratio': round((temporal_patterns['stale_assets'] / total_temporal_assets * 100), 2) if total_temporal_assets > 0 else 0
        })
    except Exception as e:
        logger.error(f"Temporal analysis error: {e}")
        return jsonify({'error': str(e)}), 500

def get_data_quality_analysis():
    try:
        conn = get_db_connection()
        
        # Check for null/empty values in critical fields
        critical_fields = ['host', 'region', 'country', 'infrastructure_type', 'present_in_cmdb', 'tanium_coverage']
        quality_metrics = {}
        
        total_records = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        for field in critical_fields:
            null_count = conn.execute(f"""
                SELECT COUNT(*) 
                FROM universal_cmdb 
                WHERE {field} IS NULL 
                   OR {field} = '' 
                   OR LOWER({field}) = 'unknown'
                   OR LOWER({field}) = 'null'
            """).fetchone()[0]
            
            completeness = ((total_records - null_count) / total_records * 100) if total_records > 0 else 0
            quality_metrics[field] = {
                'completeness': round(completeness, 2),
                'missing_count': null_count,
                'quality_score': 'HIGH' if completeness >= 90 else 'MEDIUM' if completeness >= 70 else 'LOW'
            }
        
        overall_completeness = sum(m['completeness'] for m in quality_metrics.values()) / len(quality_metrics)
        
        conn.close()
        
        return jsonify({
            'quality_metrics': quality_metrics,
            'overall_data_quality': round(overall_completeness, 2),
            'total_records': total_records,
            'quality_assessment': 'EXCELLENT' if overall_completeness >= 90 else 'GOOD' if overall_completeness >= 75 else 'NEEDS_IMPROVEMENT'
        })
    except Exception as e:
        logger.error(f"Data quality analysis error: {e}")
        return jsonify({'error': str(e)}), 500

def get_coverage_correlation():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(region, 'unknown') as region,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                SUM(CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 1 ELSE 0 END) as cmdb_count,
                SUM(CASE WHEN LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%' THEN 1 ELSE 0 END) as tanium_count,
                SUM(CASE WHEN LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' OR 
                           LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%' THEN 1 ELSE 0 END) as splunk_count,
                COUNT(*) as total_count
            FROM universal_cmdb
            GROUP BY region, infrastructure_type
            ORDER BY total_count DESC
            LIMIT 50
        """).fetchall()
        
        correlation_analysis = []
        high_risk_combinations = []
        
        for row in result:
            region, infra_type, cmdb_count, tanium_count, splunk_count, total = row
            
            cmdb_coverage = (cmdb_count / total * 100) if total > 0 else 0
            tanium_coverage = (tanium_count / total * 100) if total > 0 else 0
            splunk_coverage = (splunk_count / total * 100) if total > 0 else 0
            
            security_score = (cmdb_coverage + tanium_coverage + splunk_coverage) / 3
            
            analysis_entry = {
                'region': normalize_region(region),
                'infrastructure_type': infra_type,
                'cmdb_coverage': round(cmdb_coverage, 2),
                'tanium_coverage': round(tanium_coverage, 2),
                'splunk_coverage': round(splunk_coverage, 2),
                'security_score': round(security_score, 2),
                'asset_count': total,
                'risk_category': 'LOW' if security_score >= 75 else 'MEDIUM' if security_score >= 50 else 'HIGH'
            }
            
            correlation_analysis.append(analysis_entry)
            
            if security_score < 50 and total > 10:
                high_risk_combinations.append(analysis_entry)
        
        # Calculate diversity metrics
        region_diversity = len(set(r['region'] for r in correlation_analysis))
        infra_diversity = len(set(r['infrastructure_type'] for r in correlation_analysis))
        
        conn.close()
        
        return jsonify({
            'correlation_analysis': correlation_analysis,
            'high_risk_combinations': high_risk_combinations,
            'diversity_metrics': {
                'region_diversity': region_diversity,
                'infrastructure_diversity': infra_diversity,
                'total_combinations': len(correlation_analysis)
            }
        })
    except Exception as e:
        logger.error(f"Coverage correlation error: {e}")
        return jsonify({'error': str(e)}), 500

def get_security_stack_analysis():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                SUM(CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 1 ELSE 0 END) as cmdb_yes,
                SUM(CASE WHEN LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%' THEN 1 ELSE 0 END) as tanium_yes,
                SUM(CASE WHEN LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' OR 
                           LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%' THEN 1 ELSE 0 END) as splunk_yes,
                SUM(CASE WHEN LOWER(COALESCE(dlp_agent_coverage, '')) LIKE '%dlp%' OR 
                           LOWER(COALESCE(dlp_agent_coverage, '')) LIKE '%agent%' THEN 1 ELSE 0 END) as dlp_yes,
                SUM(CASE WHEN LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%yes%' OR 
                           LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as crowdstrike_yes,
                COUNT(*) as total
            FROM universal_cmdb
        """).fetchone()
        
        if result:
            cmdb, tanium, splunk, dlp, crowdstrike, total = result
            
            security_layers = {
                'cmdb_registration': {
                    'count': cmdb,
                    'coverage': round((cmdb / total * 100), 2) if total > 0 else 0
                },
                'tanium_deployment': {
                    'count': tanium,
                    'coverage': round((tanium / total * 100), 2) if total > 0 else 0
                },
                'splunk_logging': {
                    'count': splunk,
                    'coverage': round((splunk / total * 100), 2) if total > 0 else 0
                },
                'dlp_protection': {
                    'count': dlp,
                    'coverage': round((dlp / total * 100), 2) if total > 0 else 0
                },
                'crowdstrike_edr': {
                    'count': crowdstrike,
                    'coverage': round((crowdstrike / total * 100), 2) if total > 0 else 0
                }
            }
            
            # Calculate overall security posture
            avg_coverage = sum(layer['coverage'] for layer in security_layers.values()) / len(security_layers)
            
            security_posture = {
                'overall_coverage': round(avg_coverage, 2),
                'security_maturity': 'ADVANCED' if avg_coverage >= 80 else 'INTERMEDIATE' if avg_coverage >= 60 else 'BASIC',
                'weakest_layer': min(security_layers.keys(), key=lambda k: security_layers[k]['coverage']),
                'strongest_layer': max(security_layers.keys(), key=lambda k: security_layers[k]['coverage'])
            }
        else:
            security_layers = {}
            security_posture = {}
        
        conn.close()
        
        return jsonify({
            'security_layers': security_layers,
            'security_posture': security_posture,
            'total_assets': total if result else 0
        })
    except Exception as e:
        logger.error(f"Security stack analysis error: {e}")
        return jsonify({'error': str(e)}), 500

def get_modernization_analysis():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(system, 'unknown') as system,
                COUNT(*) as count
            FROM universal_cmdb
            GROUP BY infrastructure_type, system
            ORDER BY count DESC
            LIMIT 100
        """).fetchall()
        
        modernization_metrics = {
            'cloud_native': 0,
            'hybrid': 0,
            'legacy': 0,
            'containerized': 0,
            'virtualized': 0
        }
        
        for row in result:
            infra_type, system, count = row
            
            infra_lower = infra_type.lower()
            system_lower = system.lower()
            
            if any(term in infra_lower for term in ['cloud', 'saas', 'paas', 'iaas', 'serverless']):
                modernization_metrics['cloud_native'] += count
            elif any(term in infra_lower for term in ['hybrid', 'multi-cloud']):
                modernization_metrics['hybrid'] += count
            elif any(term in infra_lower for term in ['legacy', 'mainframe', 'as400']):
                modernization_metrics['legacy'] += count
            
            if any(term in system_lower for term in ['container', 'docker', 'kubernetes', 'k8s']):
                modernization_metrics['containerized'] += count
            elif any(term in system_lower for term in ['vmware', 'virtual', 'vm', 'hyperv']):
                modernization_metrics['virtualized'] += count
        
        total_assets = sum(modernization_metrics.values())
        
        modernization_score = 0
        if total_assets > 0:
            modern_assets = modernization_metrics['cloud_native'] + modernization_metrics['containerized']
            modernization_score = (modern_assets / total_assets * 100)
        
        conn.close()
        
        return jsonify({
            'modernization_metrics': modernization_metrics,
            'modernization_score': round(modernization_score, 2),
            'modernization_level': 'HIGH' if modernization_score >= 60 else 'MEDIUM' if modernization_score >= 30 else 'LOW',
            'transformation_priority': 'LOW' if modernization_score >= 60 else 'MEDIUM' if modernization_score >= 30 else 'HIGH'
        })
    except Exception as e:
        logger.error(f"Modernization analysis error: {e}")
        return jsonify({'error': str(e)}), 500

def get_compliance_analysis():
    try:
        conn = get_db_connection()
        
        # Define compliance requirements
        compliance_requirements = {
            'cmdb_registration': 90,  # 90% required
            'security_monitoring': 85,  # 85% required (Tanium)
            'logging_enabled': 95,  # 95% required (Splunk/GSO)
            'dlp_protection': 80,  # 80% required
            'edr_coverage': 85  # 85% required (CrowdStrike)
        }
        
        total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        compliance_status = {}
        
        # Check CMDB compliance
        cmdb_compliant = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%'
        """).fetchone()[0]
        cmdb_percentage = (cmdb_compliant / total_assets * 100) if total_assets > 0 else 0
        compliance_status['cmdb_registration'] = {
            'percentage': round(cmdb_percentage, 2),
            'required': compliance_requirements['cmdb_registration'],
            'compliant': cmdb_percentage >= compliance_requirements['cmdb_registration'],
            'gap': max(0, compliance_requirements['cmdb_registration'] - cmdb_percentage)
        }
        
        # Check Security Monitoring compliance
        tanium_compliant = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%'
        """).fetchone()[0]
        tanium_percentage = (tanium_compliant / total_assets * 100) if total_assets > 0 else 0
        compliance_status['security_monitoring'] = {
            'percentage': round(tanium_percentage, 2),
            'required': compliance_requirements['security_monitoring'],
            'compliant': tanium_percentage >= compliance_requirements['security_monitoring'],
            'gap': max(0, compliance_requirements['security_monitoring'] - tanium_percentage)
        }
        
        # Check Logging compliance
        logging_compliant = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
               OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
               OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%yes%'
               OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%gso%'
        """).fetchone()[0]
        logging_percentage = (logging_compliant / total_assets * 100) if total_assets > 0 else 0
        compliance_status['logging_enabled'] = {
            'percentage': round(logging_percentage, 2),
            'required': compliance_requirements['logging_enabled'],
            'compliant': logging_percentage >= compliance_requirements['logging_enabled'],
            'gap': max(0, compliance_requirements['logging_enabled'] - logging_percentage)
        }
        
        # Overall compliance score
        compliance_scores = [status['percentage'] / status['required'] * 100 
                           for status in compliance_status.values()]
        overall_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        conn.close()
        
        return jsonify({
            'compliance_status': compliance_status,
            'overall_compliance_score': round(min(100, overall_compliance), 2),
            'compliance_level': 'COMPLIANT' if overall_compliance >= 90 else 'PARTIAL' if overall_compliance >= 70 else 'NON_COMPLIANT',
            'critical_gaps': [k for k, v in compliance_status.items() if not v['compliant']]
        })
    except Exception as e:
        logger.error(f"Compliance analysis error: {e}")
        return jsonify({'error': str(e)}), 500

def get_risk_assessment():
    try:
        conn = get_db_connection()
        
        # Risk factors based on missing security controls
        result = conn.execute("""
            SELECT 
                COALESCE(region, 'unknown') as region,
                COUNT(*) as total_assets,
                SUM(CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) NOT LIKE '%yes%' THEN 1 ELSE 0 END) as no_cmdb,
                SUM(CASE WHEN LOWER(COALESCE(tanium_coverage, '')) NOT LIKE '%tanium%' THEN 1 ELSE 0 END) as no_tanium,
                SUM(CASE WHEN LOWER(COALESCE(logging_in_splunk, '')) NOT LIKE '%yes%' 
                        AND LOWER(COALESCE(logging_in_splunk, '')) NOT LIKE '%splunk%' 
                        AND LOWER(COALESCE(logging_in_gso, '')) NOT LIKE '%yes%' 
                        AND LOWER(COALESCE(logging_in_gso, '')) NOT LIKE '%gso%' THEN 1 ELSE 0 END) as no_logging
            FROM universal_cmdb
            GROUP BY region
            ORDER BY total_assets DESC
        """).fetchall()
        
        risk_matrix = []
        critical_risks = []
        
        for row in result:
            region, total, no_cmdb, no_tanium, no_logging = row
            
            # Calculate risk score (0-100, higher is worse)
            cmdb_risk = (no_cmdb / total * 30) if total > 0 else 0
            tanium_risk = (no_tanium / total * 35) if total > 0 else 0
            logging_risk = (no_logging / total * 35) if total > 0 else 0
            
            total_risk_score = cmdb_risk + tanium_risk + logging_risk
            
            risk_assessment = {
                'region': normalize_region(region),
                'total_assets': total,
                'unprotected_assets': no_tanium,
                'unmonitored_assets': no_logging,
                'unregistered_assets': no_cmdb,
                'risk_score': round(total_risk_score, 2),
                'risk_level': 'CRITICAL' if total_risk_score >= 70 else 'HIGH' if total_risk_score >= 50 else 'MEDIUM' if total_risk_score >= 30 else 'LOW'
            }
            
            risk_matrix.append(risk_assessment)
            
            if total_risk_score >= 70 and total > 50:
                critical_risks.append(risk_assessment)
        
        # Calculate enterprise risk
        total_enterprise_assets = sum(r['total_assets'] for r in risk_matrix)
        total_unprotected = sum(r['unprotected_assets'] for r in risk_matrix)
        total_unmonitored = sum(r['unmonitored_assets'] for r in risk_matrix)
        
        enterprise_risk_score = 0
        if total_enterprise_assets > 0:
            protection_gap = (total_unprotected / total_enterprise_assets * 35)
            monitoring_gap = (total_unmonitored / total_enterprise_assets * 35)
            enterprise_risk_score = protection_gap + monitoring_gap
        
        conn.close()
        
        return jsonify({
            'risk_matrix': risk_matrix,
            'critical_risks': critical_risks,
            'enterprise_risk': {
                'overall_risk_score': round(enterprise_risk_score, 2),
                'risk_level': 'CRITICAL' if enterprise_risk_score >= 70 else 'HIGH' if enterprise_risk_score >= 50 else 'MEDIUM' if enterprise_risk_score >= 30 else 'LOW',
                'total_assets_at_risk': total_unprotected,
                'percentage_at_risk': round((total_unprotected / total_enterprise_assets * 100), 2) if total_enterprise_assets > 0 else 0
            }
        })
    except Exception as e:
        logger.error(f"Risk assessment error: {e}")
        return jsonify({'error': str(e)}), 500

def get_visibility_score():
    try:
        conn = get_db_connection()
        
        # Calculate comprehensive visibility score
        total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        visibility_components = {}
        
        # Asset Discovery (CMDB)
        cmdb_registered = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%'
        """).fetchone()[0]
        visibility_components['asset_discovery'] = (cmdb_registered / total_assets * 100) if total_assets > 0 else 0
        
        # Security Monitoring (Tanium)
        tanium_deployed = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%'
        """).fetchone()[0]
        visibility_components['security_monitoring'] = (tanium_deployed / total_assets * 100) if total_assets > 0 else 0
        
        # Log Aggregation (Splunk/GSO)
        logging_enabled = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
               OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
               OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%yes%'
               OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%gso%'
        """).fetchone()[0]
        visibility_components['log_aggregation'] = (logging_enabled / total_assets * 100) if total_assets > 0 else 0
        
        # Endpoint Detection (CrowdStrike)
        crowdstrike_deployed = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%yes%' 
               OR LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%crowdstrike%'
        """).fetchone()[0]
        visibility_components['endpoint_detection'] = (crowdstrike_deployed / total_assets * 100) if total_assets > 0 else 0
        
        # Data Loss Prevention (DLP)
        dlp_deployed = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(dlp_agent_coverage, '')) LIKE '%dlp%' 
               OR LOWER(COALESCE(dlp_agent_coverage, '')) LIKE '%agent%'
        """).fetchone()[0]
        visibility_components['data_protection'] = (dlp_deployed / total_assets * 100) if total_assets > 0 else 0
        
        # Calculate overall visibility score
        overall_visibility = sum(visibility_components.values()) / len(visibility_components)
        
        # Determine visibility gaps
        visibility_gaps = []
        for component, score in visibility_components.items():
            if score < 80:
                gap_severity = 'CRITICAL' if score < 50 else 'HIGH' if score < 70 else 'MEDIUM'
                visibility_gaps.append({
                    'component': component,
                    'current_coverage': round(score, 2),
                    'target_coverage': 80,
                    'gap': round(80 - score, 2),
                    'severity': gap_severity
                })
        
        conn.close()
        
        return jsonify({
            'visibility_score': round(overall_visibility, 2),
            'visibility_components': {k: round(v, 2) for k, v in visibility_components.items()},
            'visibility_level': 'EXCELLENT' if overall_visibility >= 85 else 'GOOD' if overall_visibility >= 70 else 'FAIR' if overall_visibility >= 50 else 'POOR',
            'visibility_gaps': visibility_gaps,
            'total_assets_monitored': total_assets
        })
    except Exception as e:
        logger.error(f"Visibility score error: {e}")
        return jsonify({'error': str(e)}), 500

def get_shadow_it_detection():
    try:
        conn = get_db_connection()
        
        # Detect potential shadow IT (assets not in CMDB but have other coverage)
        result = conn.execute("""
            SELECT 
                COALESCE(region, 'unknown') as region,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COUNT(*) as count
            FROM universal_cmdb
            WHERE LOWER(COALESCE(present_in_cmdb, '')) NOT LIKE '%yes%'
              AND (LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%'
                   OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%'
                   OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
                   OR LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%yes%'
                   OR LOWER(COALESCE(presence_in_crowdstrike, '')) LIKE '%crowdstrike%')
            GROUP BY region, infrastructure_type
            ORDER BY count DESC
        """).fetchall()
        
        shadow_it_indicators = []
        total_shadow_assets = 0
        
        for row in result:
            region, infra_type, count = row
            
            shadow_it_indicators.append({
                'region': normalize_region(region),
                'infrastructure_type': infra_type,
                'asset_count': count,
                'risk_level': 'HIGH' if count > 100 else 'MEDIUM' if count > 50 else 'LOW',
                'discovery_source': 'Security Tools Detection'
            })
            
            total_shadow_assets += count
        
        # Detect unmanaged cloud resources
        unmanaged_cloud = conn.execute("""
            SELECT COUNT(*) 
            FROM universal_cmdb
            WHERE LOWER(COALESCE(infrastructure_type, '')) LIKE '%cloud%'
              AND LOWER(COALESCE(present_in_cmdb, '')) NOT LIKE '%yes%'
        """).fetchone()[0]
        
        total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        shadow_it_percentage = (total_shadow_assets / total_assets * 100) if total_assets > 0 else 0
        
        conn.close()
        
        return jsonify({
            'shadow_it_detected': total_shadow_assets,
            'shadow_it_percentage': round(shadow_it_percentage, 2),
            'shadow_it_indicators': shadow_it_indicators,
            'unmanaged_cloud_resources': unmanaged_cloud,
            'shadow_it_risk': 'CRITICAL' if shadow_it_percentage >= 20 else 'HIGH' if shadow_it_percentage >= 10 else 'MEDIUM' if shadow_it_percentage >= 5 else 'LOW',
            'recommendations': [
                'Implement automated CMDB discovery' if shadow_it_percentage >= 10 else None,
                'Review cloud governance policies' if unmanaged_cloud > 50 else None,
                'Enhance asset registration processes' if total_shadow_assets > 100 else None
            ]
        })
    except Exception as e:
        logger.error(f"Shadow IT detection error: {e}")
        return jsonify({'error': str(e)}), 500

def get_comprehensive_dashboard():
    """Generate comprehensive dashboard data combining all metrics"""
    try:
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'executive_summary': {},
            'security_metrics': {},
            'operational_metrics': {},
            'risk_indicators': {},
            'recommendations': []
        }
        
        # Get key metrics
        conn = get_db_connection()
        total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        # Security coverage
        cmdb_count = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%'
        """).fetchone()[0]
        
        tanium_count = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%'
        """).fetchone()[0]
        
        logging_count = conn.execute("""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE LOWER(COALESCE(logging_in_splunk, '')) LIKE '%yes%' 
               OR LOWER(COALESCE(logging_in_splunk, '')) LIKE '%splunk%'
               OR LOWER(COALESCE(logging_in_gso, '')) LIKE '%yes%'
        """).fetchone()[0]
        
        # Calculate percentages
        cmdb_coverage = (cmdb_count / total_assets * 100) if total_assets > 0 else 0
        tanium_coverage = (tanium_count / total_assets * 100) if total_assets > 0 else 0
        logging_coverage = (logging_count / total_assets * 100) if total_assets > 0 else 0
        
        # Executive Summary
        dashboard_data['executive_summary'] = {
            'total_assets': total_assets,
            'visibility_score': round((cmdb_coverage + tanium_coverage + logging_coverage) / 3, 2),
            'security_posture': 'STRONG' if tanium_coverage >= 80 else 'MODERATE' if tanium_coverage >= 60 else 'WEAK',
            'compliance_status': 'COMPLIANT' if cmdb_coverage >= 90 else 'PARTIAL' if cmdb_coverage >= 70 else 'NON_COMPLIANT'
        }
        
        # Security Metrics
        dashboard_data['security_metrics'] = {
            'cmdb_coverage': round(cmdb_coverage, 2),
            'tanium_coverage': round(tanium_coverage, 2),
            'logging_coverage': round(logging_coverage, 2),
            'unprotected_assets': total_assets - tanium_count,
            'unmonitored_assets': total_assets - logging_count
        }
        
        # Risk Indicators
        risk_score = 100 - ((cmdb_coverage + tanium_coverage + logging_coverage) / 3)
        dashboard_data['risk_indicators'] = {
            'overall_risk_score': round(risk_score, 2),
            'risk_level': 'CRITICAL' if risk_score >= 70 else 'HIGH' if risk_score >= 50 else 'MEDIUM' if risk_score >= 30 else 'LOW',
            'assets_at_risk': total_assets - min(cmdb_count, tanium_count, logging_count)
        }
        
        # Recommendations
        if cmdb_coverage < 90:
            dashboard_data['recommendations'].append({
                'priority': 'HIGH',
                'action': 'Improve CMDB Registration',
                'impact': f"Register {total_assets - cmdb_count} assets",
                'effort': 'MEDIUM'
            })
        
        if tanium_coverage < 80:
            dashboard_data['recommendations'].append({
                'priority': 'CRITICAL',
                'action': 'Deploy Tanium Agents',
                'impact': f"Secure {total_assets - tanium_count} unprotected assets",
                'effort': 'HIGH'
            })
        
        if logging_coverage < 95:
            dashboard_data['recommendations'].append({
                'priority': 'HIGH',
                'action': 'Enable Logging',
                'impact': f"Monitor {total_assets - logging_count} unlogged assets",
                'effort': 'LOW'
            })
        
        conn.close()
        
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Comprehensive dashboard error: {e}")
        return jsonify({'error': str(e)}), 500