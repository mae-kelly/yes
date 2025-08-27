from flask import jsonify, request
import logging
from collections import Counter, defaultdict
from database_utils import *

logger = logging.getLogger(__name__)

def get_source_tables_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(source_tables, 'unknown') as source_tables,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts,
                COALESCE(source_count, 1) as source_count
            FROM universal_cmdb 
            GROUP BY source_tables, source_count
            ORDER BY frequency DESC
        """).fetchall()
        
        source_intelligence = {}
        source_details = []
        total_mentions = 0
        
        for row in result:
            source_tables, frequency, unique_hosts, source_count = row
            if source_tables and source_tables != 'unknown':
                source_values = parse_comma_separated_values(source_tables)
                for source in source_values:
                    source_intelligence[source] = source_intelligence.get(source, 0) + frequency
                    total_mentions += frequency
        
        for source, frequency in source_intelligence.items():
            percentage = (frequency / total_mentions * 100) if total_mentions > 0 else 0
            source_details.append({
                'source': source,
                'frequency': frequency,
                'percentage': round(percentage, 2),
                'threat_level': calculate_threat_level(percentage)['level']
            })
        
        source_details.sort(key=lambda x: x['frequency'], reverse=True)
        conn.close()
        
        return jsonify({
            'source_intelligence': source_intelligence,
            'detailed_data': source_details,
            'unique_sources': len(source_intelligence),
            'total_mentions': total_mentions,
            'top_10_sources': source_details[:10],
            'source_concentration': source_details[0]['percentage'] if source_details else 0
        })
    except Exception as e:
        logger.error(f"Source tables error: {e}")
        return jsonify({'error': str(e)}), 500

def get_domain_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(host, 'unknown') as host,
                COALESCE(domain, '') as domain
            FROM universal_cmdb
        """).fetchall()
        
        domain_counter = Counter({'1dc': 0, 'fead': 0, 'other': 0})
        unique_domains = set()
        multi_domain_hosts = 0
        
        for row in result:
            host, domain = row
            if domain:
                domain_values = parse_pipe_separated_values(domain)
                host_domains = {'1dc': False, 'fead': False, 'other': False}
                
                for d in domain_values:
                    unique_domains.add(d)
                    if '1dc' in d.lower():
                        host_domains['1dc'] = True
                    elif 'fead' in d.lower():
                        host_domains['fead'] = True
                    else:
                        host_domains['other'] = True
                
                domain_count = sum(1 for present in host_domains.values() if present)
                if domain_count > 1:
                    multi_domain_hosts += 1
                
                for domain_type, present in host_domains.items():
                    if present:
                        domain_counter[domain_type] += 1
        
        total_analyzed = sum(domain_counter.values())
        
        domain_analytics = {}
        for domain_type, count in domain_counter.items():
            percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
            domain_analytics[domain_type] = {
                'count': count,
                'percentage': round(percentage, 2),
                'threat_level': calculate_threat_level(percentage)['level']
            }
        
        conn.close()
        
        return jsonify({
            'domain_analysis': dict(domain_counter),
            'domain_analytics': domain_analytics,
            'multi_domain_assets': multi_domain_hosts,
            'unique_domains': list(unique_domains)[:100],
            'total_analyzed': total_analyzed,
            'warfare_intelligence': {
                'dominant_domain': max(domain_counter, key=domain_counter.get),
                'domain_balance': abs(domain_counter['1dc'] - domain_counter['fead']),
                'tactical_status': 'BALANCED' if abs(domain_counter['1dc'] - domain_counter['fead']) < total_analyzed * 0.1 else 'DOMINANT'
            }
        })
    except Exception as e:
        logger.error(f"Domain metrics error: {e}")
        return jsonify({'error': str(e)}), 500

def get_infrastructure_type_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type, 
                COUNT(*) as frequency,
                COALESCE(region, 'unknown') as region
            FROM universal_cmdb 
            GROUP BY infrastructure_type, region
            ORDER BY frequency DESC
        """).fetchall()
        
        infrastructure_matrix = {}
        regional_infrastructure = defaultdict(lambda: defaultdict(int))
        total_count = 0
        
        for row in result:
            infra_type, frequency, region = row
            if infra_type and infra_type != 'unknown':
                infra_values = parse_pipe_separated_values(infra_type)
                for i_type in infra_values:
                    infrastructure_matrix[i_type] = infrastructure_matrix.get(i_type, 0) + frequency
                    total_count += frequency
                    regional_infrastructure[normalize_region(region)][i_type] += frequency
        
        detailed_data = []
        for infra_type, frequency in infrastructure_matrix.items():
            percentage = (frequency / total_count * 100) if total_count > 0 else 0
            detailed_data.append({
                'type': infra_type,
                'frequency': frequency,
                'percentage': round(percentage, 2),
                'threat_level': calculate_threat_level(percentage)['level']
            })
        
        detailed_data.sort(key=lambda x: x['frequency'], reverse=True)
        
        modernization_score = sum(1 for item in detailed_data if any(keyword in item['type'].lower() for keyword in ['cloud', 'saas', 'api', 'container']))
        modernization_percentage = (modernization_score / len(detailed_data) * 100) if detailed_data else 0
        
        conn.close()
        
        return jsonify({
            'infrastructure_matrix': infrastructure_matrix,
            'detailed_data': detailed_data,
            'regional_analysis': dict(regional_infrastructure),
            'total_types': len(infrastructure_matrix),
            'modernization_analysis': {
                'modernization_score': modernization_score,
                'modernization_percentage': round(modernization_percentage, 2),
                'legacy_systems': len([item for item in detailed_data if any(keyword in item['type'].lower() for keyword in ['legacy', 'mainframe', 'old'])]),
                'cloud_adoption': len([item for item in detailed_data if 'cloud' in item['type'].lower()])
            }
        })
    except Exception as e:
        logger.error(f"Infrastructure type error: {e}")
        return jsonify({'error': str(e)}), 500

def get_region_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(region, 'unknown') as region, 
                COUNT(*) as frequency,
                COALESCE(present_in_cmdb, 'unknown') as cmdb_status,
                COALESCE(tanium_coverage, 'unknown') as tanium_status
            FROM universal_cmdb 
            GROUP BY region, cmdb_status, tanium_status
            ORDER BY frequency DESC
        """).fetchall()
        
        region_counter = {'north america': 0, 'emea': 0, 'latam': 0, 'apac': 0}
        regional_security = defaultdict(lambda: {'total': 0, 'cmdb_registered': 0, 'tanium_deployed': 0})
        
        for row in result:
            region, frequency, cmdb_status, tanium_status = row
            if region and region != 'unknown':
                region_values = parse_pipe_separated_values(region)
                for r in region_values:
                    normalized = normalize_region(r)
                    if normalized in region_counter:
                        region_counter[normalized] += frequency
                        regional_security[normalized]['total'] += frequency
                        
                        if 'yes' in str(cmdb_status).lower():
                            regional_security[normalized]['cmdb_registered'] += frequency
                        if 'tanium' in str(tanium_status).lower():
                            regional_security[normalized]['tanium_deployed'] += frequency
        
        total_coverage = sum(region_counter.values())
        
        regional_analytics = {}
        for region, count in region_counter.items():
            security_data = regional_security[region]
            cmdb_percentage = (security_data['cmdb_registered'] / security_data['total'] * 100) if security_data['total'] > 0 else 0
            tanium_percentage = (security_data['tanium_deployed'] / security_data['total'] * 100) if security_data['total'] > 0 else 0
            security_score = (cmdb_percentage + tanium_percentage) / 2
            
            regional_analytics[region] = {
                'count': count,
                'percentage': round((count / total_coverage * 100), 2) if total_coverage > 0 else 0,
                'cmdb_coverage': round(cmdb_percentage, 2),
                'tanium_coverage': round(tanium_percentage, 2),
                'security_score': round(security_score, 2),
                'threat_level': calculate_threat_level(100 - security_score)['level']
            }
        
        conn.close()
        
        return jsonify({
            'global_surveillance': region_counter,
            'regional_analytics': regional_analytics,
            'total_coverage': total_coverage,
            'threat_assessment': {
                'highest_risk_region': min(regional_analytics.keys(), key=lambda k: regional_analytics[k]['security_score']),
                'most_secure_region': max(regional_analytics.keys(), key=lambda k: regional_analytics[k]['security_score']),
                'regional_balance': max(regional_analytics.values(), key=lambda x: x['percentage'])['percentage']
            }
        })
    except Exception as e:
        logger.error(f"Region metrics error: {e}")
        return jsonify({'error': str(e)}), 500

def get_country_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(country, 'unknown') as country, 
                COUNT(*) as frequency,
                COALESCE(region, 'unknown') as region,
                COALESCE(present_in_cmdb, 'unknown') as cmdb_status
            FROM universal_cmdb 
            GROUP BY country, region, cmdb_status
            ORDER BY frequency DESC
        """).fetchall()
        
        country_counter = Counter()
        country_analytics = {}
        
        for row in result:
            country, frequency, region, cmdb_status = row
            if country and country != 'unknown':
                country_values = parse_pipe_separated_values(country)
                for c in country_values:
                    normalized = normalize_country(c)
                    country_counter[normalized] += frequency
                    
                    if normalized not in country_analytics:
                        country_analytics[normalized] = {
                            'total': 0,
                            'region': normalize_region(region),
                            'cmdb_registered': 0,
                            'security_score': 0
                        }
                    
                    country_analytics[normalized]['total'] += frequency
                    if 'yes' in str(cmdb_status).lower():
                        country_analytics[normalized]['cmdb_registered'] += frequency
        
        total_assets = sum(country_counter.values())
        
        for country, data in country_analytics.items():
            cmdb_percentage = (data['cmdb_registered'] / data['total'] * 100) if data['total'] > 0 else 0
            data['security_score'] = round(cmdb_percentage, 2)
            data['percentage'] = round((data['total'] / total_assets * 100), 2) if total_assets > 0 else 0
            data['threat_level'] = calculate_threat_level(100 - cmdb_percentage)['level']
        
        conn.close()
        
        return jsonify({
            'global_intelligence': dict(country_counter),
            'country_analytics': country_analytics,
            'total_countries': len(country_counter),
            'threat_intelligence': {
                'highest_threat_countries': [c for c, d in country_analytics.items() if d['threat_level'] == 'CRITICAL'][:10],
                'geographic_concentration': max(country_analytics.values(), key=lambda x: x['percentage'])['percentage'] if country_analytics else 0
            }
        })
    except Exception as e:
        logger.error(f"Country metrics error: {e}")
        return jsonify({'error': str(e)}), 500

def get_data_center_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(data_center, 'unknown') as data_center, 
                COUNT(*) as frequency,
                COALESCE(region, 'unknown') as region
            FROM universal_cmdb 
            GROUP BY data_center, region
            ORDER BY frequency DESC
        """).fetchall()
        
        facility_intelligence = {}
        regional_facilities = defaultdict(list)
        
        for row in result:
            data_center, frequency, region = row
            if data_center and data_center != 'unknown':
                first_word = str(data_center).split()[0] if str(data_center).split() else str(data_center)
                facility_intelligence[first_word] = facility_intelligence.get(first_word, 0) + frequency
                regional_facilities[normalize_region(region)].append({
                    'facility': first_word,
                    'count': frequency,
                    'full_name': data_center
                })
        
        total_facilities = len(facility_intelligence)
        total_assets = sum(facility_intelligence.values())
        
        conn.close()
        
        return jsonify({
            'facility_intelligence': facility_intelligence,
            'regional_facilities': dict(regional_facilities),
            'total_facilities': total_facilities,
            'datacenter_analysis': {
                'unique_facilities': total_facilities,
                'total_instances': total_assets,
                'largest_facility': max(facility_intelligence, key=facility_intelligence.get) if facility_intelligence else 'unknown',
                'facility_concentration': round((max(facility_intelligence.values()) / total_assets * 100), 2) if facility_intelligence and total_assets > 0 else 0
            }
        })
    except Exception as e:
        logger.error(f"Data center metrics error: {e}")
        return jsonify({'error': str(e)}), 500

def get_cloud_region_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT DISTINCT 
                COALESCE(cloud_region, 'unknown') as cloud_region,
                COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE cloud_region IS NOT NULL AND cloud_region != ''
            GROUP BY cloud_region
            ORDER BY frequency DESC
        """).fetchall()
        
        cloud_matrix = []
        provider_analysis = defaultdict(int)
        total_cloud_assets = 0
        
        for row in result:
            cloud_region, frequency = row
            if cloud_region and cloud_region != 'unknown':
                cloud_values = parse_pipe_separated_values(cloud_region)
                for cr in cloud_values:
                    if cr not in cloud_matrix:
                        cloud_matrix.append(cr)
                    
                    total_cloud_assets += frequency
                    
                    if any(provider in cr.lower() for provider in ['aws', 'amazon']):
                        provider_analysis['aws'] += frequency
                    elif any(provider in cr.lower() for provider in ['azure', 'microsoft']):
                        provider_analysis['azure'] += frequency
                    elif any(provider in cr.lower() for provider in ['gcp', 'google']):
                        provider_analysis['gcp'] += frequency
                    elif 'oracle' in cr.lower():
                        provider_analysis['oracle'] += frequency
                    else:
                        provider_analysis['other'] += frequency
        
        conn.close()
        
        return jsonify({
            'cloud_matrix': cloud_matrix,
            'provider_distribution': dict(provider_analysis),
            'total_regions': len(cloud_matrix),
            'cloud_intelligence': {
                'total_cloud_assets': total_cloud_assets,
                'unique_providers': len(provider_analysis),
                'multi_cloud_strategy': len(provider_analysis) > 1,
                'dominant_provider': max(provider_analysis, key=provider_analysis.get) if provider_analysis else 'unknown'
            }
        })
    except Exception as e:
        logger.error(f"Cloud region metrics error: {e}")
        return jsonify({'error': str(e)}), 500

def get_class_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(class, 'unknown') as class, 
                COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE class IS NOT NULL AND class != ''
            GROUP BY class
            ORDER BY frequency DESC
        """).fetchall()
        
        classification_matrix = {}
        
        for row in result:
            class_name, frequency = row
            if class_name and class_name != 'unknown':
                class_numbers = extract_class_numbers(class_name)
                if class_numbers:
                    for class_num in class_numbers:
                        classification_matrix[class_num] = classification_matrix.get(class_num, 0) + frequency
                else:
                    classification_matrix[str(class_name)] = frequency
        
        total_classified = sum(classification_matrix.values())
        
        class_analytics = {}
        for class_name, count in classification_matrix.items():
            percentage = (count / total_classified * 100) if total_classified > 0 else 0
            class_analytics[class_name] = {
                'count': count,
                'percentage': round(percentage, 2),
                'threat_level': calculate_threat_level(percentage)['level']
            }
        
        conn.close()
        
        return jsonify({
            'classification_matrix': classification_matrix,
            'class_analytics': class_analytics,
            'total_classes': len(classification_matrix),
            'total_classified_assets': total_classified
        })
    except Exception as e:
        logger.error(f"Class metrics error: {e}")
        return jsonify({'error': str(e)}), 500

def get_system_classification_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(system, 'unknown') as system, 
                COUNT(*) as frequency
            FROM universal_cmdb 
            GROUP BY system
            ORDER BY frequency DESC
        """).fetchall()
        
        system_matrix = {}
        os_distribution = defaultdict(int)
        
        for row in result:
            system_name, frequency = row
            if system_name and system_name != 'unknown':
                system_values = parse_pipe_separated_values(system_name)
                for s in system_values:
                    system_matrix[s] = system_matrix.get(s, 0) + frequency
                    
                    s_lower = s.lower()
                    if 'windows' in s_lower:
                        os_distribution['windows'] += frequency
                    elif 'linux' in s_lower:
                        os_distribution['linux'] += frequency
                    elif any(os_type in s_lower for os_type in ['unix', 'aix', 'solaris']):
                        os_distribution['unix'] += frequency
                    elif 'vmware' in s_lower:
                        os_distribution['virtual'] += frequency
                    else:
                        os_distribution['other'] += frequency
        
        total_systems = sum(system_matrix.values())
        
        conn.close()
        
        return jsonify({
            'system_matrix': system_matrix,
            'os_distribution': dict(os_distribution),
            'total_systems': len(system_matrix),
            'taxonomy_intelligence': {
                'os_diversity': len(os_distribution),
                'dominant_os': max(os_distribution, key=os_distribution.get) if os_distribution else 'unknown',
                'system_sprawl': len(system_matrix)
            }
        })
    except Exception as e:
        logger.error(f"System classification error: {e}")
        return jsonify({'error': str(e)}), 500

def get_business_unit_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(business_unit, 'unknown') as business_unit, 
                COUNT(*) as frequency,
                COALESCE(present_in_cmdb, 'unknown') as cmdb_status,
                COALESCE(tanium_coverage, 'unknown') as tanium_status
            FROM universal_cmdb 
            GROUP BY business_unit, cmdb_status, tanium_status
            ORDER BY frequency DESC
        """).fetchall()
        
        business_intelligence = {}
        bu_analytics = defaultdict(lambda: {'total': 0, 'cmdb_registered': 0, 'tanium_deployed': 0})
        
        for row in result:
            bu_name, frequency, cmdb_status, tanium_status = row
            if bu_name and bu_name != 'unknown':
                separators = [',', '|']
                units = [bu_name]
                
                for sep in separators:
                    new_units = []
                    for unit in units:
                        new_units.extend([u.strip() for u in str(unit).split(sep) if u.strip()])
                    units = new_units
                
                for unit in units:
                    if unit:
                        business_intelligence[unit] = business_intelligence.get(unit, 0) + frequency
                        bu_analytics[unit]['total'] += frequency
                        
                        if 'yes' in str(cmdb_status).lower():
                            bu_analytics[unit]['cmdb_registered'] += frequency
                        if 'tanium' in str(tanium_status).lower():
                            bu_analytics[unit]['tanium_deployed'] += frequency
        
        bu_security_analysis = {}
        for unit, analytics in bu_analytics.items():
            total = analytics['total']
            cmdb_percentage = (analytics['cmdb_registered'] / total * 100) if total > 0 else 0
            tanium_percentage = (analytics['tanium_deployed'] / total * 100) if total > 0 else 0
            security_score = (cmdb_percentage + tanium_percentage) / 2
            
            bu_security_analysis[unit] = {
                'total_assets': total,
                'cmdb_coverage': round(cmdb_percentage, 2),
                'tanium_coverage': round(tanium_percentage, 2),
                'security_score': round(security_score, 2),
                'security_status': 'SECURE' if security_score >= 80 else 'AT_RISK' if security_score >= 50 else 'VULNERABLE'
            }
        
        conn.close()
        
        return jsonify({
            'business_intelligence': business_intelligence,
            'bu_security_analysis': bu_security_analysis,
            'total_business_units': len(business_intelligence),
            'organizational_analytics': {
                'largest_bu': max(business_intelligence, key=business_intelligence.get) if business_intelligence else 'unknown',
                'vulnerable_units': [unit for unit, data in bu_security_analysis.items() if data['security_status'] == 'VULNERABLE']
            }
        })
    except Exception as e:
        logger.error(f"Business unit metrics error: {e}")
        return jsonify({'error': str(e)}), 500

def get_cio_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(cio, 'unknown') as cio, 
                COUNT(*) as frequency,
                COALESCE(business_unit, 'unknown') as business_unit
            FROM universal_cmdb 
            WHERE cio IS NOT NULL AND cio != ''
            GROUP BY cio, business_unit
            ORDER BY frequency DESC
        """).fetchall()
        
        operative_intelligence = {}
        leadership_analysis = defaultdict(lambda: {'total_assets': 0, 'business_units': set()})
        
        for row in result:
            cio_name, frequency, bu = row
            if cio_name and cio_name != 'unknown':
                cio_values = parse_pipe_separated_values(cio_name)
                for c in cio_values:
                    c = c.strip()
                    if c and not c.isdigit() and len(c) > 1:
                        operative_intelligence[c] = operative_intelligence.get(c, 0) + frequency
                        leadership_analysis[c]['total_assets'] += frequency
                        leadership_analysis[c]['business_units'].add(bu)
        
        leadership_intelligence = {}
        for cio, analytics in leadership_analysis.items():
            span_of_control = len(analytics['business_units'])
            leadership_intelligence[cio] = {
                'total_assets': analytics['total_assets'],
                'business_units': span_of_control,
                'span_of_control': span_of_control,
                'leadership_tier': 'EXECUTIVE' if span_of_control >= 5 else 'SENIOR' if span_of_control >= 3 else 'MANAGER'
            }
        
        conn.close()
        
        return jsonify({
            'operative_intelligence': operative_intelligence,
            'leadership_analysis': leadership_intelligence,
            'total_cio_entries': len(operative_intelligence),
            'governance_analytics': {
                'unique_leaders': len(operative_intelligence),
                'executive_leaders': len([cio for cio, data in leadership_intelligence.items() if data['leadership_tier'] == 'EXECUTIVE'])
            }
        })
    except Exception as e:
        logger.error(f"CIO metrics error: {e}")
        return jsonify({'error': str(e)}), 500

def get_tanium_coverage():
    try:
        conn = get_db_connection()
        
        tanium_count = conn.execute("""
            SELECT COUNT(*) 
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%'
        """).fetchone()[0]
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        coverage_percentage = (tanium_count / total_count * 100) if total_count > 0 else 0
        
        conn.close()
        
        return jsonify({
            'tanium_deployed': tanium_count,
            'total_assets': total_count,
            'coverage_percentage': round(coverage_percentage, 2),
            'deployment_gap': total_count - tanium_count,
            'deployment_status': 'OPTIMAL' if coverage_percentage >= 80 else 'CRITICAL' if coverage_percentage < 60 else 'ACCEPTABLE'
        })
    except Exception as e:
        logger.error(f"Tanium coverage error: {e}")
        return jsonify({'error': str(e)}), 500

def get_cmdb_presence():
    try:
        conn = get_db_connection()
        
        yes_count = conn.execute("""
            SELECT COUNT(*) 
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%'
        """).fetchone()[0]
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        registration_rate = (yes_count / total_count * 100) if total_count > 0 else 0
        
        conn.close()
        
        return jsonify({
            'cmdb_registered': yes_count,
            'total_assets': total_count,
            'registration_rate': round(registration_rate, 2),
            'registration_gap': total_count - yes_count,
            'compliance_status': 'COMPLIANT' if registration_rate >= 90 else 'NON_COMPLIANT' if registration_rate < 70 else 'PARTIAL_COMPLIANCE'
        })
    except Exception as e:
        logger.error(f"CMDB presence error: {e}")
        return jsonify({'error': str(e)}), 500

def get_host_search():
    try:
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify({'error': 'Search term required'}), 400
            
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(host, 'unknown') as host,
                COALESCE(region, 'unknown') as region,
                COALESCE(country, 'unknown') as country,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(present_in_cmdb, 'unknown') as present_in_cmdb,
                COALESCE(tanium_coverage, 'unknown') as tanium_coverage
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(host, '')) LIKE LOWER(?) 
            OR LOWER(COALESCE(source_tables, '')) LIKE LOWER(?)
            ORDER BY host 
            LIMIT 100
        """, [f'%{search_term}%', f'%{search_term}%']).fetchall()
        
        hosts = []
        for row in result:
            hosts.append({
                'host': row[0],
                'region': row[1],
                'country': row[2],
                'infrastructure_type': row[3],
                'present_in_cmdb': row[4],
                'tanium_coverage': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'hosts': hosts,
            'total_found': len(hosts),
            'search_term': search_term
        })
    except Exception as e:
        logger.error(f"Host search error: {e}")
        return jsonify({'error': str(e)}), 500