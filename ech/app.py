from flask import Flask, jsonify, request
from flask_cors import CORS
import duckdb
import re
import os
import sys
from collections import Counter, defaultdict
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    db_paths = [
        'universal_cmdb.db',
        './universal_cmdb.db',
        '../universal_cmdb.db',
        '/app/universal_cmdb.db',
        os.path.join(os.getcwd(), 'universal_cmdb.db')
    ]
    
    for db_path in db_paths:
        try:
            if os.path.exists(db_path):
                logger.info(f"Attempting to connect to: {db_path}")
                conn = duckdb.connect(db_path, read_only=True)
                
                tables = conn.execute("SHOW TABLES").fetchall()
                logger.info(f"Available tables: {tables}")
                
                if any('universal_cmdb' in str(table).lower() for table in tables):
                    logger.info(f"Successfully connected to DuckDB at: {db_path}")
                    return conn
                else:
                    conn.close()
        except Exception as e:
            logger.error(f"Failed to connect to {db_path}: {e}")
            continue
    
    error_msg = f"""Database file 'universal_cmdb.db' not found!
    
    Please ensure:
    1. Your database file is named 'universal_cmdb.db'
    2. It's placed in the project root directory 
    3. It contains a table named 'universal_cmdb'
    4. The table has the expected columns for analysis
    
    Searched locations:
    {chr(10).join(f'    {path}' for path in db_paths)}
    """
    
    raise Exception(error_msg)

def verify_table_structure(conn):
    try:
        result = conn.execute("DESCRIBE universal_cmdb").fetchall()
        columns = [row[0] for row in result]
        logger.info(f"Table columns: {columns}")
        
        row_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        logger.info(f"Total rows in universal_cmdb: {row_count}")
        
        return columns, row_count
    except Exception as e:
        logger.error(f"Error verifying table structure: {e}")
        return [], 0

def normalize_country(country):
    if not country:
        return 'unknown'
    
    country_mapping = {
        'us': 'united states', 'usa': 'united states', 'america': 'united states',
        'ca': 'canada', 'can': 'canada', 'mx': 'mexico', 'mex': 'mexico',
        'uk': 'united kingdom', 'gb': 'united kingdom', 'britain': 'united kingdom',
        'de': 'germany', 'deu': 'germany', 'fr': 'france', 'fra': 'france',
        'it': 'italy', 'ita': 'italy', 'es': 'spain', 'esp': 'spain',
        'nl': 'netherlands', 'nld': 'netherlands', 'be': 'belgium', 'bel': 'belgium',
        'ch': 'switzerland', 'che': 'switzerland', 'at': 'austria', 'aut': 'austria',
        'se': 'sweden', 'swe': 'sweden', 'no': 'norway', 'nor': 'norway',
        'dk': 'denmark', 'dnk': 'denmark', 'fi': 'finland', 'fin': 'finland',
        'ie': 'ireland', 'irl': 'ireland', 'pt': 'portugal', 'prt': 'portugal',
        'gr': 'greece', 'grc': 'greece', 'pl': 'poland', 'pol': 'poland',
        'cz': 'czech republic', 'cze': 'czech republic', 'sk': 'slovakia', 'svk': 'slovakia',
        'hu': 'hungary', 'hun': 'hungary', 'ro': 'romania', 'rou': 'romania',
        'bg': 'bulgaria', 'bgr': 'bulgaria', 'hr': 'croatia', 'hrv': 'croatia',
        'si': 'slovenia', 'svn': 'slovenia', 'lt': 'lithuania', 'ltu': 'lithuania',
        'lv': 'latvia', 'lva': 'latvia', 'ee': 'estonia', 'est': 'estonia',
        'ru': 'russia', 'rus': 'russia', 'tr': 'turkey', 'tur': 'turkey',
        'ua': 'ukraine', 'ukr': 'ukraine', 'il': 'israel', 'isr': 'israel',
        'ae': 'united arab emirates', 'are': 'united arab emirates', 'uae': 'united arab emirates',
        'sa': 'saudi arabia', 'sau': 'saudi arabia', 'eg': 'egypt', 'egy': 'egypt',
        'za': 'south africa', 'zaf': 'south africa', 'ng': 'nigeria', 'nga': 'nigeria',
        'ke': 'kenya', 'ken': 'kenya', 'ma': 'morocco', 'mar': 'morocco',
        'jp': 'japan', 'jpn': 'japan', 'cn': 'china', 'chn': 'china', 'prc': 'china',
        'kr': 'south korea', 'kor': 'south korea', 'in': 'india', 'ind': 'india',
        'au': 'australia', 'aus': 'australia', 'nz': 'new zealand', 'nzl': 'new zealand',
        'sg': 'singapore', 'sgp': 'singapore', 'my': 'malaysia', 'mys': 'malaysia',
        'th': 'thailand', 'tha': 'thailand', 'vn': 'vietnam', 'vnm': 'vietnam',
        'id': 'indonesia', 'idn': 'indonesia', 'ph': 'philippines', 'phl': 'philippines',
        'bd': 'bangladesh', 'bgd': 'bangladesh', 'pk': 'pakistan', 'pak': 'pakistan',
        'lk': 'sri lanka', 'lka': 'sri lanka', 'mm': 'myanmar', 'mmr': 'myanmar',
        'kh': 'cambodia', 'khm': 'cambodia', 'la': 'laos', 'lao': 'laos',
        'tw': 'taiwan', 'twn': 'taiwan', 'hk': 'hong kong', 'hkg': 'hong kong',
        'br': 'brazil', 'bra': 'brazil', 'ar': 'argentina', 'arg': 'argentina',
        'cl': 'chile', 'chl': 'chile', 'co': 'colombia', 'col': 'colombia',
        'pe': 'peru', 'per': 'peru', 'ec': 'ecuador', 'ecu': 'ecuador',
        've': 'venezuela', 'ven': 'venezuela', 'uy': 'uruguay', 'ury': 'uruguay',
        'py': 'paraguay', 'pry': 'paraguay', 'bo': 'bolivia', 'bol': 'bolivia',
        'cr': 'costa rica', 'cri': 'costa rica', 'pa': 'panama', 'pan': 'panama'
    }
    
    country_lower = country.lower().strip()
    return country_mapping.get(country_lower, country_lower)

def normalize_region(region):
    if not region:
        return 'unknown'
    
    region_lower = region.lower().strip()
    
    na_indicators = ['us', 'usa', 'united states', 'canada', 'ca', 'can', 'north america', 'na', 'america', 'mexico', 'mx', 'mex']
    emea_indicators = ['europe', 'emea', 'eu', 'middle east', 'africa', 'uk', 'gb', 'britain', 'germany', 'de', 'france', 'fr', 'italy', 'spain', 'netherlands', 'belgium', 'switzerland', 'austria', 'sweden', 'norway', 'denmark', 'finland', 'ireland', 'portugal', 'greece', 'poland', 'czech', 'slovakia', 'hungary', 'romania', 'bulgaria', 'croatia', 'slovenia', 'lithuania', 'latvia', 'estonia', 'russia', 'turkey', 'ukraine', 'israel', 'uae', 'emirates', 'saudi', 'egypt', 'south africa', 'nigeria', 'kenya', 'morocco']
    latam_indicators = ['latin america', 'latam', 'south america', 'central america', 'brazil', 'br', 'argentina', 'ar', 'chile', 'colombia', 'peru', 'ecuador', 'venezuela', 'uruguay', 'paraguay', 'bolivia', 'costa rica', 'panama']
    apac_indicators = ['asia pacific', 'apac', 'asia', 'pacific', 'australia', 'au', 'new zealand', 'nz', 'japan', 'jp', 'china', 'cn', 'india', 'in', 'singapore', 'malaysia', 'thailand', 'vietnam', 'indonesia', 'philippines', 'bangladesh', 'pakistan', 'sri lanka', 'myanmar', 'cambodia', 'laos', 'taiwan', 'hong kong', 'korea']
    
    if any(indicator in region_lower for indicator in na_indicators):
        return 'north america'
    elif any(indicator in region_lower for indicator in emea_indicators):
        return 'emea'
    elif any(indicator in region_lower for indicator in latam_indicators):
        return 'latam'
    elif any(indicator in region_lower for indicator in apac_indicators):
        return 'apac'
    else:
        return region_lower

def parse_pipe_separated_values(value):
    if not value or str(value).lower() in ['null', 'none', 'unknown', '']:
        return []
    return [v.strip() for v in str(value).split('|') if v.strip()]

def parse_comma_separated_values(value):
    if not value or str(value).lower() in ['null', 'none', 'unknown', '']:
        return []
    return [v.strip() for v in str(value).split(',') if v.strip()]

def extract_class_numbers(value):
    if not value:
        return []
    matches = re.findall(r'class\s*(\d+)', str(value).lower())
    return [f"class {match}" for match in matches]

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
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/source_tables')
def source_tables_metrics():
    try:
        conn = get_db_connection()
        
        queries_to_try = [
            """
            SELECT 
                TRIM(value) as source_table,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts
            FROM (
                SELECT host, UNNEST(STRING_SPLIT(source_tables, ',')) as value
                FROM universal_cmdb 
                WHERE source_tables IS NOT NULL AND source_tables != ''
            )
            WHERE TRIM(value) != ''
            GROUP BY TRIM(value)
            ORDER BY frequency DESC
            """,
            """
            SELECT 
                source_tables as source_table,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts
            FROM universal_cmdb 
            WHERE source_tables IS NOT NULL AND source_tables != ''
            GROUP BY source_tables
            ORDER BY frequency DESC
            """,
            """
            SELECT 
                COALESCE(source_tables, 'unknown') as source_table,
                COUNT(*) as frequency,
                COUNT(DISTINCT COALESCE(host, 'unknown')) as unique_hosts
            FROM universal_cmdb 
            GROUP BY source_tables
            ORDER BY frequency DESC
            """
        ]
        
        result = None
        for i, query in enumerate(queries_to_try):
            try:
                logger.info(f"Trying query {i+1} for source tables")
                result = conn.execute(query).fetchall()
                if result:
                    logger.info(f"Query {i+1} succeeded with {len(result)} results")
                    break
            except Exception as e:
                logger.warning(f"Query {i+1} failed: {e}")
                continue
        
        if not result:
            logger.error("All source table queries failed")
            conn.close()
            return jsonify({'error': 'No source table data found'}), 500
        
        total_rows = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE source_tables IS NOT NULL").fetchone()[0]
        
        data = {}
        detailed_data = []
        total_mentions = 0
        
        for row in result:
            source_name, frequency, unique_hosts = row
            if source_name:
                data[source_name] = frequency
                total_mentions += frequency
        
        for source_name, frequency in data.items():
            percentage = (frequency / total_mentions * 100) if total_mentions > 0 else 0
            unique_hosts_val = unique_hosts if 'unique_hosts' in locals() else 1
            detailed_data.append({
                'source': source_name,
                'frequency': frequency,
                'unique_hosts': unique_hosts_val,
                'percentage': round(percentage, 2)
            })
        
        detailed_data.sort(key=lambda x: x['frequency'], reverse=True)
        
        conn.close()
        
        return jsonify({
            'source_intelligence': data,
            'detailed_data': detailed_data,
            'unique_sources': len(data),
            'total_mentions': total_mentions,
            'unique_hosts_with_sources': total_rows,
            'top_10': detailed_data[:10],
            'risk_analysis': {
                'high_frequency': [d for d in detailed_data if d['percentage'] > 10],
                'medium_frequency': [d for d in detailed_data if 5 <= d['percentage'] <= 10],
                'low_frequency': [d for d in detailed_data if d['percentage'] < 5]
            }
        })
    except Exception as e:
        logger.error(f"Source tables error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/domain_metrics')
def domain_metrics():
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
        host_domain_map = {}
        
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
                
                for domain_type, present in host_domains.items():
                    if present:
                        domain_counter[domain_type] += 1
                        host_domain_map[host] = domain_type
        
        total_analyzed = sum(domain_counter.values())
        
        domain_details = {}
        for domain_type, count in domain_counter.items():
            percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
            domain_details[domain_type] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        multi_domain_hosts = len([h for h, d in host_domain_map.items() if '1dc' in str(d) and 'fead' in str(d)])
        
        conn.close()
        
        return jsonify({
            'domain_analysis': dict(domain_counter),
            'domain_details': domain_details,
            'unique_domains': list(unique_domains)[:100],
            'total_analyzed': total_analyzed,
            'multi_domain_assets': multi_domain_hosts,
            'domain_distribution': {
                '1dc_percentage': domain_details.get('1dc', {}).get('percentage', 0),
                'fead_percentage': domain_details.get('fead', {}).get('percentage', 0),
                'other_percentage': domain_details.get('other', {}).get('percentage', 0)
            },
            'warfare_intelligence': {
                'dominant_domain': max(domain_counter, key=domain_counter.get),
                'domain_balance': abs(domain_counter['1dc'] - domain_counter['fead']),
                'tactical_status': 'BALANCED' if abs(domain_counter['1dc'] - domain_counter['fead']) < total_analyzed * 0.1 else 'DOMINANT'
            }
        })
    except Exception as e:
        logger.error(f"Domain metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/infrastructure_type')
def infrastructure_type_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type, 
                COUNT(*) as frequency,
                COALESCE(region, 'unknown') as region,
                COALESCE(business_unit, 'unknown') as business_unit
            FROM universal_cmdb 
            GROUP BY infrastructure_type, region, business_unit
            ORDER BY frequency DESC
        """).fetchall()
        
        infrastructure_matrix = {}
        infrastructure_by_region = defaultdict(lambda: defaultdict(int))
        infrastructure_by_bu = defaultdict(lambda: defaultdict(int))
        total_count = 0
        
        for row in result:
            infra_type, frequency, region, bu = row
            
            if infra_type and infra_type != 'unknown':
                infra_values = parse_pipe_separated_values(infra_type)
                for i_type in infra_values:
                    infrastructure_matrix[i_type] = infrastructure_matrix.get(i_type, 0) + frequency
                    total_count += frequency
                    
                    if region != 'unknown':
                        infrastructure_by_region[normalize_region(region)][i_type] += frequency
                    
                    if bu != 'unknown':
                        infrastructure_by_bu[bu][i_type] += frequency
        
        detailed_data = []
        for infra_type, frequency in infrastructure_matrix.items():
            percentage = (frequency / total_count * 100) if total_count > 0 else 0
            detailed_data.append({
                'type': infra_type,
                'frequency': frequency,
                'percentage': round(percentage, 2),
                'threat_level': 'CRITICAL' if percentage > 40 else 'HIGH' if percentage > 25 else 'MEDIUM' if percentage > 10 else 'LOW'
            })
        
        detailed_data.sort(key=lambda x: x['frequency'], reverse=True)
        
        modernization_score = sum(1 for item in detailed_data if 'cloud' in item['type'].lower() or 'saas' in item['type'].lower() or 'api' in item['type'].lower())
        modernization_percentage = (modernization_score / len(detailed_data) * 100) if detailed_data else 0
        
        conn.close()
        
        return jsonify({
            'infrastructure_matrix': infrastructure_matrix,
            'detailed_data': detailed_data,
            'regional_analysis': dict(infrastructure_by_region),
            'business_unit_analysis': dict(infrastructure_by_bu),
            'total_types': len(infrastructure_matrix),
            'modernization_analysis': {
                'modernization_score': modernization_score,
                'modernization_percentage': round(modernization_percentage, 2),
                'legacy_systems': len([item for item in detailed_data if 'legacy' in item['type'].lower() or 'mainframe' in item['type'].lower()]),
                'cloud_adoption': len([item for item in detailed_data if 'cloud' in item['type'].lower()])
            },
            'distribution_analysis': {
                'top_5': detailed_data[:5],
                'total_instances': total_count,
                'diversity_score': len(infrastructure_matrix),
                'concentration_risk': detailed_data[0]['percentage'] if detailed_data else 0
            }
        })
    except Exception as e:
        logger.error(f"Infrastructure type error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/region_metrics')
def region_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(region, 'unknown') as region, 
                COUNT(*) as frequency,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(present_in_cmdb, 'unknown') as cmdb_status,
                COALESCE(tanium_coverage, 'unknown') as tanium_status
            FROM universal_cmdb 
            GROUP BY region, infrastructure_type, cmdb_status, tanium_status
            ORDER BY frequency DESC
        """).fetchall()
        
        region_counter = {'north america': 0, 'emea': 0, 'latam': 0, 'apac': 0}
        region_details = {'north america': [], 'emea': [], 'latam': [], 'apac': []}
        regional_infrastructure = defaultdict(lambda: defaultdict(int))
        regional_cmdb_coverage = defaultdict(lambda: {'registered': 0, 'total': 0})
        regional_tanium_coverage = defaultdict(lambda: {'deployed': 0, 'total': 0})
        raw_regions = []
        
        for row in result:
            region, frequency, infra_type, cmdb_status, tanium_status = row
            if region and region != 'unknown':
                raw_regions.append({'region': region, 'frequency': frequency})
                
                region_values = parse_pipe_separated_values(region)
                for r in region_values:
                    normalized = normalize_region(r)
                    if normalized in region_counter:
                        region_counter[normalized] += frequency
                        region_details[normalized].append({
                            'original': r,
                            'frequency': frequency,
                            'infrastructure': infra_type,
                            'cmdb_registered': 'yes' in str(cmdb_status).lower(),
                            'tanium_deployed': 'tanium' in str(tanium_status).lower()
                        })
                        
                        regional_infrastructure[normalized][infra_type] += frequency
                        
                        regional_cmdb_coverage[normalized]['total'] += frequency
                        if 'yes' in str(cmdb_status).lower():
                            regional_cmdb_coverage[normalized]['registered'] += frequency
                        
                        regional_tanium_coverage[normalized]['total'] += frequency
                        if 'tanium' in str(tanium_status).lower():
                            regional_tanium_coverage[normalized]['deployed'] += frequency
        
        total_coverage = sum(region_counter.values())
        
        regional_analytics = {}
        for region, count in region_counter.items():
            cmdb_data = regional_cmdb_coverage[region]
            tanium_data = regional_tanium_coverage[region]
            
            cmdb_percentage = (cmdb_data['registered'] / cmdb_data['total'] * 100) if cmdb_data['total'] > 0 else 0
            tanium_percentage = (tanium_data['deployed'] / tanium_data['total'] * 100) if tanium_data['total'] > 0 else 0
            
            regional_analytics[region] = {
                'count': count,
                'percentage': round((count / total_coverage * 100), 2) if total_coverage > 0 else 0,
                'cmdb_coverage': round(cmdb_percentage, 2),
                'tanium_coverage': round(tanium_percentage, 2),
                'infrastructure_diversity': len(regional_infrastructure[region]),
                'security_score': round((cmdb_percentage + tanium_percentage) / 2, 2)
            }
        
        conn.close()
        
        return jsonify({
            'global_surveillance': region_counter,
            'region_details': region_details,
            'regional_analytics': regional_analytics,
            'regional_infrastructure': dict(regional_infrastructure),
            'raw_regions': raw_regions,
            'total_coverage': total_coverage,
            'threat_assessment': {
                'highest_risk_region': min(regional_analytics.keys(), key=lambda k: regional_analytics[k]['security_score']),
                'most_secure_region': max(regional_analytics.keys(), key=lambda k: regional_analytics[k]['security_score']),
                'geographic_balance': max(regional_analytics.values(), key=lambda x: x['percentage'])['percentage'] - min(regional_analytics.values(), key=lambda x: x['percentage'])['percentage']
            }
        })
    except Exception as e:
        logger.error(f"Region metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/country_metrics')
def country_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(country, 'unknown') as country, 
                COUNT(*) as frequency,
                COALESCE(region, 'unknown') as region,
                COALESCE(present_in_cmdb, 'unknown') as cmdb_status,
                COALESCE(tanium_coverage, 'unknown') as tanium_status
            FROM universal_cmdb 
            GROUP BY country, region, cmdb_status, tanium_status
            ORDER BY frequency DESC
        """).fetchall()
        
        country_counter = Counter()
        country_regional_map = {}
        country_security_scores = {}
        
        for row in result:
            country, frequency, region, cmdb_status, tanium_status = row
            if country and country != 'unknown':
                country_values = parse_pipe_separated_values(country)
                for c in country_values:
                    normalized = normalize_country(c)
                    country_counter[normalized] += frequency
                    country_regional_map[normalized] = normalize_region(region)
                    
                    cmdb_score = 50 if 'yes' in str(cmdb_status).lower() else 0
                    tanium_score = 50 if 'tanium' in str(tanium_status).lower() else 0
                    
                    if normalized not in country_security_scores:
                        country_security_scores[normalized] = {'cmdb': 0, 'tanium': 0, 'total': 0}
                    
                    country_security_scores[normalized]['cmdb'] += cmdb_score
                    country_security_scores[normalized]['tanium'] += tanium_score
                    country_security_scores[normalized]['total'] += frequency
        
        total_assets = sum(country_counter.values())
        
        country_analysis = {}
        for country, count in country_counter.most_common():
            security_data = country_security_scores.get(country, {'cmdb': 0, 'tanium': 0, 'total': 1})
            
            cmdb_coverage = security_data['cmdb'] / security_data['total'] if security_data['total'] > 0 else 0
            tanium_coverage = security_data['tanium'] / security_data['total'] if security_data['total'] > 0 else 0
            overall_security = (cmdb_coverage + tanium_coverage) / 2
            
            country_analysis[country] = {
                'count': count,
                'percentage': round((count / total_assets * 100), 2) if total_assets > 0 else 0,
                'region': country_regional_map.get(country, 'unknown'),
                'security_score': round(overall_security, 2),
                'threat_level': 'CRITICAL' if overall_security < 25 else 'HIGH' if overall_security < 50 else 'MEDIUM' if overall_security < 75 else 'LOW'
            }
        
        regional_country_distribution = defaultdict(list)
        for country, data in country_analysis.items():
            regional_country_distribution[data['region']].append({
                'country': country,
                'count': data['count'],
                'percentage': data['percentage']
            })
        
        conn.close()
        
        return jsonify({
            'global_intelligence': dict(country_counter),
            'total_countries': len(country_counter),
            'country_analysis': country_analysis,
            'regional_distribution': dict(regional_country_distribution),
            'threat_intelligence': {
                'highest_threat_countries': [c for c, d in country_analysis.items() if d['threat_level'] == 'CRITICAL'][:5],
                'most_secure_countries': [c for c, d in country_analysis.items() if d['threat_level'] == 'LOW'][:5],
                'geographic_concentration': country_analysis[max(country_counter, key=country_counter.get)]['percentage'] if country_counter else 0
            },
            'coverage_gaps': {
                'unprotected_countries': len([c for c, d in country_analysis.items() if d['security_score'] < 50]),
                'total_gap_assets': sum(d['count'] for c, d in country_analysis.items() if d['security_score'] < 50)
            }
        })
    except Exception as e:
        logger.error(f"Country metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data_center_metrics')
def data_center_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(data_center, 'unknown') as data_center, 
                COUNT(*) as frequency,
                COALESCE(region, 'unknown') as region,
                COALESCE(country, 'unknown') as country,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type
            FROM universal_cmdb 
            GROUP BY data_center, region, country, infrastructure_type
            ORDER BY frequency DESC
        """).fetchall()
        
        facility_intelligence = {}
        facility_details = {}
        regional_facilities = defaultdict(list)
        
        for row in result:
            data_center, frequency, region, country, infra_type = row
            if data_center and data_center != 'unknown':
                first_word = str(data_center).split()[0] if str(data_center).split() else str(data_center)
                facility_intelligence[first_word] = facility_intelligence.get(first_word, 0) + frequency
                
                if first_word not in facility_details:
                    facility_details[first_word] = {
                        'total_assets': 0,
                        'regions': set(),
                        'countries': set(),
                        'infrastructure_types': set(),
                        'full_names': set()
                    }
                
                facility_details[first_word]['total_assets'] += frequency
                facility_details[first_word]['regions'].add(normalize_region(region))
                facility_details[first_word]['countries'].add(normalize_country(country))
                facility_details[first_word]['infrastructure_types'].add(infra_type)
                facility_details[first_word]['full_names'].add(data_center)
                
                regional_facilities[normalize_region(region)].append({
                    'facility': first_word,
                    'count': frequency,
                    'full_name': data_center
                })
        
        facility_analytics = {}
        for facility, details in facility_details.items():
            facility_analytics[facility] = {
                'total_assets': details['total_assets'],
                'geographic_spread': len(details['regions']),
                'country_presence': len(details['countries']),
                'infrastructure_diversity': len(details['infrastructure_types']),
                'regions': list(details['regions']),
                'countries': list(details['countries']),
                'infrastructure_types': list(details['infrastructure_types']),
                'redundancy_score': len(details['full_names'])
            }
        
        total_facilities = len(facility_intelligence)
        total_assets = sum(facility_intelligence.values())
        
        conn.close()
        
        return jsonify({
            'facility_intelligence': facility_intelligence,
            'facility_analytics': facility_analytics,
            'regional_facilities': dict(regional_facilities),
            'total_facilities': total_facilities,
            'datacenter_analysis': {
                'unique_facilities': total_facilities,
                'total_instances': total_assets,
                'geographic_distribution': len(set().union(*[details['regions'] for details in facility_details.values()])),
                'largest_facility': max(facility_intelligence, key=facility_intelligence.get) if facility_intelligence else 'unknown',
                'facility_concentration': round((max(facility_intelligence.values()) / total_assets * 100), 2) if facility_intelligence and total_assets > 0 else 0
            },
            'redundancy_analysis': {
                'multi_region_facilities': len([f for f, a in facility_analytics.items() if a['geographic_spread'] > 1]),
                'single_point_of_failure': len([f for f, a in facility_analytics.items() if a['redundancy_score'] == 1])
            }
        })
    except Exception as e:
        logger.error(f"Data center metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cloud_region_metrics')
def cloud_region_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(cloud_region, 'unknown') as cloud_region,
                COUNT(*) as frequency,
                COALESCE(region, 'unknown') as geographic_region,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type
            FROM universal_cmdb 
            WHERE cloud_region IS NOT NULL AND cloud_region != ''
            GROUP BY cloud_region, geographic_region, infrastructure_type
            ORDER BY frequency DESC
        """).fetchall()
        
        cloud_matrix = []
        cloud_analytics = {}
        provider_analysis = defaultdict(int)
        regional_cloud_mapping = defaultdict(list)
        
        for row in result:
            cloud_region, frequency, geo_region, infra_type = row
            if cloud_region and cloud_region != 'unknown':
                cloud_values = parse_pipe_separated_values(cloud_region)
                for cr in cloud_values:
                    if cr not in cloud_matrix:
                        cloud_matrix.append(cr)
                    
                    if cr not in cloud_analytics:
                        cloud_analytics[cr] = {
                            'total_assets': 0,
                            'geographic_regions': set(),
                            'infrastructure_types': set(),
                            'provider': 'unknown'
                        }
                    
                    cloud_analytics[cr]['total_assets'] += frequency
                    cloud_analytics[cr]['geographic_regions'].add(normalize_region(geo_region))
                    cloud_analytics[cr]['infrastructure_types'].add(infra_type)
                    
                    if 'aws' in cr.lower() or 'amazon' in cr.lower():
                        cloud_analytics[cr]['provider'] = 'aws'
                        provider_analysis['aws'] += frequency
                    elif 'azure' in cr.lower() or 'microsoft' in cr.lower():
                        cloud_analytics[cr]['provider'] = 'azure'
                        provider_analysis['azure'] += frequency
                    elif 'gcp' in cr.lower() or 'google' in cr.lower():
                        cloud_analytics[cr]['provider'] = 'gcp'
                        provider_analysis['gcp'] += frequency
                    elif 'oracle' in cr.lower():
                        cloud_analytics[cr]['provider'] = 'oracle'
                        provider_analysis['oracle'] += frequency
                    else:
                        cloud_analytics[cr]['provider'] = 'other'
                        provider_analysis['other'] += frequency
                    
                    regional_cloud_mapping[normalize_region(geo_region)].append({
                        'cloud_region': cr,
                        'count': frequency,
                        'provider': cloud_analytics[cr]['provider']
                    })
        
        for cr, analytics in cloud_analytics.items():
            analytics['geographic_regions'] = list(analytics['geographic_regions'])
            analytics['infrastructure_types'] = list(analytics['infrastructure_types'])
            analytics['multi_region'] = len(analytics['geographic_regions']) > 1
        
        total_cloud_assets = sum(analytics['total_assets'] for analytics in cloud_analytics.values())
        
        conn.close()
        
        return jsonify({
            'cloud_matrix': cloud_matrix,
            'cloud_analytics': cloud_analytics,
            'provider_distribution': dict(provider_analysis),
            'regional_cloud_mapping': dict(regional_cloud_mapping),
            'total_regions': len(cloud_matrix),
            'cloud_intelligence': {
                'total_cloud_assets': total_cloud_assets,
                'unique_providers': len(provider_analysis),
                'multi_cloud_strategy': len(provider_analysis) > 1,
                'dominant_provider': max(provider_analysis, key=provider_analysis.get) if provider_analysis else 'unknown',
                'provider_diversity_score': len(provider_analysis)
            },
            'geographic_distribution': {
                'regions_with_cloud': len(regional_cloud_mapping),
                'cloud_concentration': len([cr for cr, a in cloud_analytics.items() if not a['multi_region']])
            }
        })
    except Exception as e:
        logger.error(f"Cloud region metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/class_metrics')
def class_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(class, 'unknown') as class, 
                COUNT(*) as frequency,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(region, 'unknown') as region
            FROM universal_cmdb 
            WHERE class IS NOT NULL AND class != ''
            GROUP BY class, infrastructure_type, region
            ORDER BY frequency DESC
        """).fetchall()
        
        classification_matrix = {}
        class_details = defaultdict(lambda: {
            'total': 0,
            'infrastructure_types': set(),
            'regions': set(),
            'risk_level': 'unknown'
        })
        
        for row in result:
            class_name, frequency, infra_type, region = row
            if class_name and class_name != 'unknown':
                class_numbers = extract_class_numbers(class_name)
                
                if class_numbers:
                    for class_num in class_numbers:
                        classification_matrix[class_num] = classification_matrix.get(class_num, 0) + frequency
                        class_details[class_num]['total'] += frequency
                        class_details[class_num]['infrastructure_types'].add(infra_type)
                        class_details[class_num]['regions'].add(normalize_region(region))
                        
                        class_level = int(re.findall(r'\d+', class_num)[0])
                        if class_level <= 2:
                            class_details[class_num]['risk_level'] = 'CRITICAL'
                        elif class_level <= 4:
                            class_details[class_num]['risk_level'] = 'HIGH'
                        elif class_level <= 6:
                            class_details[class_num]['risk_level'] = 'MEDIUM'
                        else:
                            class_details[class_num]['risk_level'] = 'LOW'
                else:
                    classification_matrix[str(class_name)] = classification_matrix.get(str(class_name), 0) + frequency
                    class_details[str(class_name)]['total'] += frequency
                    class_details[str(class_name)]['infrastructure_types'].add(infra_type)
                    class_details[str(class_name)]['regions'].add(normalize_region(region))
                    class_details[str(class_name)]['risk_level'] = 'UNKNOWN'
        
        class_analytics = {}
        total_classified_assets = sum(classification_matrix.values())
        
        for class_name, details in class_details.items():
            class_analytics[class_name] = {
                'total_assets': details['total'],
                'percentage': round((details['total'] / total_classified_assets * 100), 2) if total_classified_assets > 0 else 0,
                'infrastructure_diversity': len(details['infrastructure_types']),
                'geographic_spread': len(details['regions']),
                'risk_level': details['risk_level'],
                'infrastructure_types': list(details['infrastructure_types']),
                'regions': list(details['regions'])
            }
        
        risk_distribution = defaultdict(int)
        for class_name, analytics in class_analytics.items():
            risk_distribution[analytics['risk_level']] += analytics['total_assets']
        
        conn.close()
        
        return jsonify({
            'classification_matrix': classification_matrix,
            'class_analytics': class_analytics,
            'total_classes': len(classification_matrix),
            'classification_intelligence': {
                'total_classified_assets': total_classified_assets,
                'risk_distribution': dict(risk_distribution),
                'highest_risk_class': max(class_analytics.keys(), key=lambda k: class_analytics[k]['total_assets'] if class_analytics[k]['risk_level'] == 'CRITICAL' else 0) if any(a['risk_level'] == 'CRITICAL' for a in class_analytics.values()) else 'none',
                'classification_coverage': len(classification_matrix)
            },
            'compliance_analysis': {
                'critical_assets': sum(a['total_assets'] for a in class_analytics.values() if a['risk_level'] == 'CRITICAL'),
                'unclassified_risk': risk_distribution.get('UNKNOWN', 0),
                'security_priority': sorted(class_analytics.items(), key=lambda x: (x[1]['risk_level'] == 'CRITICAL', x[1]['total_assets']), reverse=True)[:5]
            }
        })
    except Exception as e:
        logger.error(f"Class metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_classification_metrics')
def system_classification_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(system, 'unknown') as system, 
                COUNT(*) as frequency,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(region, 'unknown') as region,
                COALESCE(business_unit, 'unknown') as business_unit
            FROM universal_cmdb 
            GROUP BY system, infrastructure_type, region, business_unit
            ORDER BY frequency DESC
        """).fetchall()
        
        system_matrix = {}
        system_analytics = defaultdict(lambda: {
            'total': 0,
            'infrastructure_types': set(),
            'regions': set(),
            'business_units': set(),
            'os_family': 'unknown',
            'version_info': [],
            'security_category': 'unknown'
        })
        
        os_distribution = defaultdict(int)
        version_analysis = defaultdict(list)
        
        for row in result:
            system_name, frequency, infra_type, region, bu = row
            if system_name and system_name != 'unknown':
                system_values = parse_pipe_separated_values(system_name)
                
                for s in system_values:
                    system_matrix[s] = system_matrix.get(s, 0) + frequency
                    system_analytics[s]['total'] += frequency
                    system_analytics[s]['infrastructure_types'].add(infra_type)
                    system_analytics[s]['regions'].add(normalize_region(region))
                    system_analytics[s]['business_units'].add(bu)
                    
                    s_lower = s.lower()
                    if 'windows' in s_lower:
                        system_analytics[s]['os_family'] = 'windows'
                        os_distribution['windows'] += frequency
                        
                        version_match = re.search(r'(windows\s+\d+|server\s+\d+)', s_lower)
                        if version_match:
                            version_analysis['windows'].append(version_match.group(1))
                    elif 'linux' in s_lower:
                        system_analytics[s]['os_family'] = 'linux'
                        os_distribution['linux'] += frequency
                        
                        version_match = re.search(r'(ubuntu|centos|rhel|debian|suse)[\s\d.]*', s_lower)
                        if version_match:
                            version_analysis['linux'].append(version_match.group(0))
                    elif 'unix' in s_lower or 'aix' in s_lower or 'solaris' in s_lower:
                        system_analytics[s]['os_family'] = 'unix'
                        os_distribution['unix'] += frequency
                    elif 'vmware' in s_lower:
                        system_analytics[s]['os_family'] = 'virtual'
                        os_distribution['virtual'] += frequency
                    else:
                        system_analytics[s]['os_family'] = 'other'
                        os_distribution['other'] += frequency
                    
                    if any(keyword in s_lower for keyword in ['2008', '2012', '2016', 'xp', 'vista', '7', '8']):
                        system_analytics[s]['security_category'] = 'legacy'
                    elif any(keyword in s_lower for keyword in ['2019', '2022', '10', '11', 'latest']):
                        system_analytics[s]['security_category'] = 'modern'
                    else:
                        system_analytics[s]['security_category'] = 'standard'
        
        security_distribution = defaultdict(int)
        modernization_candidates = []
        
        for system_name, analytics in system_analytics.items():
            analytics['infrastructure_types'] = list(analytics['infrastructure_types'])
            analytics['regions'] = list(analytics['regions'])
            analytics['business_units'] = list(analytics['business_units'])
            
            security_distribution[analytics['security_category']] += analytics['total']
            
            if analytics['security_category'] == 'legacy':
                modernization_candidates.append({
                    'system': system_name,
                    'count': analytics['total'],
                    'regions': analytics['regions']
                })
        
        total_systems = sum(system_matrix.values())
        
        conn.close()
        
        return jsonify({
            'system_matrix': system_matrix,
            'system_analytics': dict(system_analytics),
            'os_distribution': dict(os_distribution),
            'version_analysis': dict(version_analysis),
            'security_distribution': dict(security_distribution),
            'total_systems': len(system_matrix),
            'modernization_analysis': {
                'legacy_systems': len(modernization_candidates),
                'legacy_assets': sum(c['count'] for c in modernization_candidates),
                'modernization_priority': sorted(modernization_candidates, key=lambda x: x['count'], reverse=True)[:10],
                'modernization_percentage': round((security_distribution.get('legacy', 0) / total_systems * 100), 2) if total_systems > 0 else 0
            },
            'taxonomy_intelligence': {
                'os_diversity': len(os_distribution),
                'dominant_os': max(os_distribution, key=os_distribution.get) if os_distribution else 'unknown',
                'system_sprawl': len(system_matrix),
                'standardization_score': round((max(os_distribution.values()) / total_systems * 100), 2) if os_distribution and total_systems > 0 else 0
            }
        })
    except Exception as e:
        logger.error(f"System classification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/business_unit_metrics')
def business_unit_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(business_unit, 'unknown') as business_unit, 
                COUNT(*) as frequency,
                COALESCE(region, 'unknown') as region,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(present_in_cmdb, 'unknown') as cmdb_status,
                COALESCE(tanium_coverage, 'unknown') as tanium_status
            FROM universal_cmdb 
            GROUP BY business_unit, region, infrastructure_type, cmdb_status, tanium_status
            ORDER BY frequency DESC
        """).fetchall()
        
        business_intelligence = {}
        bu_analytics = defaultdict(lambda: {
            'total_assets': 0,
            'regions': set(),
            'infrastructure_types': set(),
            'cmdb_registered': 0,
            'tanium_deployed': 0,
            'security_score': 0
        })
        
        regional_bu_distribution = defaultdict(lambda: defaultdict(int))
        
        for row in result:
            bu_name, frequency, region, infra_type, cmdb_status, tanium_status = row
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
                        bu_analytics[unit]['total_assets'] += frequency
                        bu_analytics[unit]['regions'].add(normalize_region(region))
                        bu_analytics[unit]['infrastructure_types'].add(infra_type)
                        
                        if 'yes' in str(cmdb_status).lower():
                            bu_analytics[unit]['cmdb_registered'] += frequency
                        
                        if 'tanium' in str(tanium_status).lower():
                            bu_analytics[unit]['tanium_deployed'] += frequency
                        
                        regional_bu_distribution[normalize_region(region)][unit] += frequency
        
        bu_security_analysis = {}
        for unit, analytics in bu_analytics.items():
            total = analytics['total_assets']
            cmdb_percentage = (analytics['cmdb_registered'] / total * 100) if total > 0 else 0
            tanium_percentage = (analytics['tanium_deployed'] / total * 100) if total > 0 else 0
            security_score = (cmdb_percentage + tanium_percentage) / 2
            
            bu_security_analysis[unit] = {
                'total_assets': total,
                'geographic_spread': len(analytics['regions']),
                'infrastructure_diversity': len(analytics['infrastructure_types']),
                'cmdb_coverage': round(cmdb_percentage, 2),
                'tanium_coverage': round(tanium_percentage, 2),
                'security_score': round(security_score, 2),
                'regions': list(analytics['regions']),
                'infrastructure_types': list(analytics['infrastructure_types']),
                'security_status': 'SECURE' if security_score >= 80 else 'AT_RISK' if security_score >= 50 else 'VULNERABLE'
            }
        
        total_bu_assets = sum(business_intelligence.values())
        
        security_priority = sorted(bu_security_analysis.items(), key=lambda x: (x[1]['security_status'] == 'VULNERABLE', -x[1]['security_score'], -x[1]['total_assets']))
        
        conn.close()
        
        return jsonify({
            'business_intelligence': business_intelligence,
            'bu_security_analysis': bu_security_analysis,
            'regional_distribution': dict(regional_bu_distribution),
            'total_business_units': len(business_intelligence),
            'organizational_analytics': {
                'total_assets': total_bu_assets,
                'largest_bu': max(business_intelligence, key=business_intelligence.get) if business_intelligence else 'unknown',
                'most_distributed_bu': max(bu_security_analysis.keys(), key=lambda k: bu_security_analysis[k]['geographic_spread']) if bu_security_analysis else 'unknown',
                'security_leaders': [unit for unit, data in bu_security_analysis.items() if data['security_status'] == 'SECURE'],
                'vulnerable_units': [unit for unit, data in bu_security_analysis.items() if data['security_status'] == 'VULNERABLE']
            },
            'risk_assessment': {
                'high_risk_units': len([unit for unit, data in bu_security_analysis.items() if data['security_score'] < 50]),
                'assets_at_risk': sum(data['total_assets'] for unit, data in bu_security_analysis.items() if data['security_score'] < 50),
                'security_priority_list': [{'unit': unit, 'assets': data['total_assets'], 'score': data['security_score']} for unit, data in security_priority[:10]]
            }
        })
    except Exception as e:
        logger.error(f"Business unit metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cio_metrics')
def cio_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(cio, 'unknown') as cio, 
                COUNT(*) as frequency,
                COALESCE(business_unit, 'unknown') as business_unit,
                COALESCE(region, 'unknown') as region
            FROM universal_cmdb 
            WHERE cio IS NOT NULL AND cio != ''
            GROUP BY cio, business_unit, region
            ORDER BY frequency DESC
        """).fetchall()
        
        operative_intelligence = {}
        cio_analytics = defaultdict(lambda: {
            'total_assets': 0,
            'business_units': set(),
            'regions': set(),
            'span_of_control': 0
        })
        
        for row in result:
            cio_name, frequency, bu, region = row
            if cio_name and cio_name != 'unknown':
                cio_values = parse_pipe_separated_values(cio_name)
                
                for c in cio_values:
                    c = c.strip()
                    if c and re.search(r'[a-zA-Z]', c) and not c.isdigit():
                        operative_intelligence[c] = operative_intelligence.get(c, 0) + frequency
                        cio_analytics[c]['total_assets'] += frequency
                        cio_analytics[c]['business_units'].add(bu)
                        cio_analytics[c]['regions'].add(normalize_region(region))
        
        leadership_analysis = {}
        for cio, analytics in cio_analytics.items():
            span_of_control = len(analytics['business_units']) * len(analytics['regions'])
            
            leadership_analysis[cio] = {
                'total_assets': analytics['total_assets'],
                'business_units': len(analytics['business_units']),
                'geographic_regions': len(analytics['regions']),
                'span_of_control': span_of_control,
                'business_unit_list': list(analytics['business_units']),
                'region_list': list(analytics['regions']),
                'leadership_tier': 'EXECUTIVE' if span_of_control >= 10 else 'SENIOR' if span_of_control >= 5 else 'MANAGER'
            }
        
        total_cio_assets = sum(operative_intelligence.values())
        
        governance_metrics = {
            'executive_leaders': len([cio for cio, data in leadership_analysis.items() if data['leadership_tier'] == 'EXECUTIVE']),
            'senior_leaders': len([cio for cio, data in leadership_analysis.items() if data['leadership_tier'] == 'SENIOR']),
            'managers': len([cio for cio, data in leadership_analysis.items() if data['leadership_tier'] == 'MANAGER']),
            'largest_portfolio': max(leadership_analysis.values(), key=lambda x: x['total_assets'])['total_assets'] if leadership_analysis else 0,
            'most_distributed': max(leadership_analysis.values(), key=lambda x: x['span_of_control'])['span_of_control'] if leadership_analysis else 0
        }
        
        conn.close()
        
        return jsonify({
            'operative_intelligence': operative_intelligence,
            'leadership_analysis': leadership_analysis,
            'total_cio_entries': len(operative_intelligence),
            'governance_analytics': {
                'total_assets_under_management': total_cio_assets,
                'unique_leaders': len(operative_intelligence),
                'governance_distribution': governance_metrics,
                'average_portfolio_size': round(total_cio_assets / len(operative_intelligence), 0) if operative_intelligence else 0
            },
            'executive_summary': {
                'top_executives': sorted(leadership_analysis.items(), key=lambda x: x[1]['total_assets'], reverse=True)[:5],
                'most_distributed_leaders': sorted(leadership_analysis.items(), key=lambda x: x[1]['span_of_control'], reverse=True)[:5],
                'leadership_effectiveness': len([cio for cio, data in leadership_analysis.items() if data['span_of_control'] >= 5])
            }
        })
    except Exception as e:
        logger.error(f"CIO metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tanium_coverage')
def tanium_coverage():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%' THEN 'deployed'
                    ELSE 'not_deployed'
                END as status,
                COUNT(*) as count,
                COALESCE(region, 'unknown') as region,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(business_unit, 'unknown') as business_unit
            FROM universal_cmdb
            GROUP BY 
                CASE WHEN LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%' THEN 'deployed' ELSE 'not_deployed' END,
                region, infrastructure_type, business_unit
        """).fetchall()
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        tanium_count = 0
        
        regional_coverage = defaultdict(lambda: {'deployed': 0, 'total': 0})
        infrastructure_coverage = defaultdict(lambda: {'deployed': 0, 'total': 0})
        bu_coverage = defaultdict(lambda: {'deployed': 0, 'total': 0})
        status_breakdown = {'deployed': 0, 'not_deployed': 0}
        
        for row in result:
            status, count, region, infra_type, bu = row
            
            status_breakdown[status] += count
            if status == 'deployed':
                tanium_count += count
            
            normalized_region = normalize_region(region)
            regional_coverage[normalized_region]['total'] += count
            if status == 'deployed':
                regional_coverage[normalized_region]['deployed'] += count
            
            infrastructure_coverage[infra_type]['total'] += count
            if status == 'deployed':
                infrastructure_coverage[infra_type]['deployed'] += count
            
            bu_coverage[bu]['total'] += count
            if status == 'deployed':
                bu_coverage[bu]['deployed'] += count
        
        coverage_percentage = (tanium_count / total_count * 100) if total_count > 0 else 0
        
        regional_analysis = {}
        for region, data in regional_coverage.items():
            coverage_pct = (data['deployed'] / data['total'] * 100) if data['total'] > 0 else 0
            regional_analysis[region] = {
                'deployed': data['deployed'],
                'total': data['total'],
                'coverage_percentage': round(coverage_pct, 2),
                'status': 'OPTIMAL' if coverage_pct >= 80 else 'ACCEPTABLE' if coverage_pct >= 60 else 'CRITICAL'
            }
        
        infrastructure_analysis = {}
        for infra_type, data in infrastructure_coverage.items():
            coverage_pct = (data['deployed'] / data['total'] * 100) if data['total'] > 0 else 0
            infrastructure_analysis[infra_type] = {
                'deployed': data['deployed'],
                'total': data['total'],
                'coverage_percentage': round(coverage_pct, 2),
                'priority': 'HIGH' if coverage_pct < 50 else 'MEDIUM' if coverage_pct < 80 else 'LOW'
            }
        
        bu_analysis = {}
        for bu, data in bu_coverage.items():
            coverage_pct = (data['deployed'] / data['total'] * 100) if data['total'] > 0 else 0
            bu_analysis[bu] = {
                'deployed': data['deployed'],
                'total': data['total'],
                'coverage_percentage': round(coverage_pct, 2),
                'risk_level': 'CRITICAL' if coverage_pct < 40 else 'HIGH' if coverage_pct < 70 else 'LOW'
            }
        
        deployment_gaps = {
            'unprotected_regions': len([r for r, d in regional_analysis.items() if d['status'] == 'CRITICAL']),
            'high_risk_infrastructure': len([i for i, d in infrastructure_analysis.items() if d['priority'] == 'HIGH']),
            'vulnerable_business_units': len([b for b, d in bu_analysis.items() if d['risk_level'] == 'CRITICAL']),
            'total_unprotected_assets': total_count - tanium_count
        }
        
        deployment_recommendations = []
        
        for region, data in regional_analysis.items():
            if data['status'] == 'CRITICAL':
                deployment_recommendations.append({
                    'type': 'regional',
                    'target': region,
                    'priority': 'HIGH',
                    'assets': data['total'] - data['deployed'],
                    'reason': f"Only {data['coverage_percentage']}% coverage in {region}"
                })
        
        for infra_type, data in infrastructure_analysis.items():
            if data['priority'] == 'HIGH':
                deployment_recommendations.append({
                    'type': 'infrastructure',
                    'target': infra_type,
                    'priority': 'HIGH',
                    'assets': data['total'] - data['deployed'],
                    'reason': f"Critical infrastructure type with {data['coverage_percentage']}% coverage"
                })
        
        conn.close()
        
        return jsonify({
            'tanium_deployed': tanium_count,
            'total_assets': total_count,
            'coverage_percentage': round(coverage_percentage, 2),
            'status_breakdown': status_breakdown,
            'regional_coverage': dict(regional_analysis),
            'infrastructure_coverage': dict(infrastructure_analysis),
            'business_unit_coverage': dict(bu_analysis),
            'deployment_gaps': deployment_gaps,
            'deployment_recommendations': sorted(deployment_recommendations, key=lambda x: x['assets'], reverse=True)[:10],
            'deployment_analysis': {
                'coverage_status': 'OPTIMAL' if coverage_percentage >= 80 else 'ACCEPTABLE' if coverage_percentage >= 60 else 'CRITICAL',
                'deployment_gap': total_count - tanium_count,
                'recommended_action': 'MAINTAIN' if coverage_percentage >= 80 else 'EXPAND' if coverage_percentage >= 60 else 'URGENT_DEPLOY',
                'security_risk_level': 'LOW' if coverage_percentage >= 80 else 'MEDIUM' if coverage_percentage >= 60 else 'HIGH'
            },
            'trend_analysis': {
                'coverage_trend': 'improving',
                'deployment_velocity': 'steady',
                'risk_trajectory': 'decreasing' if coverage_percentage >= 70 else 'increasing'
            }
        })
    except Exception as e:
        logger.error(f"Tanium coverage error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cmdb_presence')
def cmdb_presence():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 'registered'
                    ELSE 'not_registered'
                END as status,
                COUNT(*) as count,
                COALESCE(region, 'unknown') as region,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(business_unit, 'unknown') as business_unit,
                COALESCE(data_center, 'unknown') as data_center
            FROM universal_cmdb
            GROUP BY 
                CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 'registered' ELSE 'not_registered' END,
                region, infrastructure_type, business_unit, data_center
        """).fetchall()
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        yes_count = 0
        
        regional_presence = defaultdict(lambda: {'registered': 0, 'total': 0})
        infrastructure_presence = defaultdict(lambda: {'registered': 0, 'total': 0})
        bu_presence = defaultdict(lambda: {'registered': 0, 'total': 0})
        datacenter_presence = defaultdict(lambda: {'registered': 0, 'total': 0})
        status_breakdown = {'registered': 0, 'not_registered': 0}
        
        for row in result:
            status, count, region, infra_type, bu, dc = row
            
            status_breakdown[status] += count
            if status == 'registered':
                yes_count += count
            
            normalized_region = normalize_region(region)
            regional_presence[normalized_region]['total'] += count
            if status == 'registered':
                regional_presence[normalized_region]['registered'] += count
            
            infrastructure_presence[infra_type]['total'] += count
            if status == 'registered':
                infrastructure_presence[infra_type]['registered'] += count
            
            bu_presence[bu]['total'] += count
            if status == 'registered':
                bu_presence[bu]['registered'] += count
            
            if dc != 'unknown':
                first_word = str(dc).split()[0] if str(dc).split() else str(dc)
                datacenter_presence[first_word]['total'] += count
                if status == 'registered':
                    datacenter_presence[first_word]['registered'] += count
        
        registration_rate = (yes_count / total_count * 100) if total_count > 0 else 0
        
        regional_compliance = {}
        for region, data in regional_presence.items():
            compliance_pct = (data['registered'] / data['total'] * 100) if data['total'] > 0 else 0
            regional_compliance[region] = {
                'registered': data['registered'],
                'total': data['total'],
                'compliance_percentage': round(compliance_pct, 2),
                'status': 'COMPLIANT' if compliance_pct >= 90 else 'PARTIAL' if compliance_pct >= 70 else 'NON_COMPLIANT'
            }
        
        infrastructure_compliance = {}
        for infra_type, data in infrastructure_presence.items():
            compliance_pct = (data['registered'] / data['total'] * 100) if data['total'] > 0 else 0
            infrastructure_compliance[infra_type] = {
                'registered': data['registered'],
                'total': data['total'],
                'compliance_percentage': round(compliance_pct, 2),
                'priority': 'URGENT' if compliance_pct < 60 else 'HIGH' if compliance_pct < 80 else 'MEDIUM'
            }
        
        bu_compliance = {}
        for bu, data in bu_presence.items():
            compliance_pct = (data['registered'] / data['total'] * 100) if data['total'] > 0 else 0
            bu_compliance[bu] = {
                'registered': data['registered'],
                'total': data['total'],
                'compliance_percentage': round(compliance_pct, 2),
                'governance_status': 'EXCELLENT' if compliance_pct >= 95 else 'GOOD' if compliance_pct >= 85 else 'POOR'
            }
        
        datacenter_compliance = {}
        for dc, data in datacenter_presence.items():
            compliance_pct = (data['registered'] / data['total'] * 100) if data['total'] > 0 else 0
            datacenter_compliance[dc] = {
                'registered': data['registered'],
                'total': data['total'],
                'compliance_percentage': round(compliance_pct, 2),
                'facility_status': 'MANAGED' if compliance_pct >= 90 else 'UNMANAGED'
            }
        
        compliance_gaps = {
            'non_compliant_regions': len([r for r, d in regional_compliance.items() if d['status'] == 'NON_COMPLIANT']),
            'urgent_infrastructure': len([i for i, d in infrastructure_compliance.items() if d['priority'] == 'URGENT']),
            'poor_governance_bus': len([b for b, d in bu_compliance.items() if d['governance_status'] == 'POOR']),
            'unmanaged_datacenters': len([dc for dc, d in datacenter_compliance.items() if d['facility_status'] == 'UNMANAGED']),
            'total_unregistered_assets': total_count - yes_count
        }
        
        improvement_recommendations = []
        
        for region, data in regional_compliance.items():
            if data['status'] == 'NON_COMPLIANT':
                improvement_recommendations.append({
                    'type': 'regional',
                    'target': region,
                    'priority': 'CRITICAL',
                    'assets_to_register': data['total'] - data['registered'],
                    'current_compliance': data['compliance_percentage'],
                    'target_compliance': 90
                })
        
        for bu, data in bu_compliance.items():
            if data['governance_status'] == 'POOR':
                improvement_recommendations.append({
                    'type': 'business_unit',
                    'target': bu,
                    'priority': 'HIGH',
                    'assets_to_register': data['total'] - data['registered'],
                    'current_compliance': data['compliance_percentage'],
                    'target_compliance': 85
                })
        
        conn.close()
        
        return jsonify({
            'cmdb_registered': yes_count,
            'total_assets': total_count,
            'registration_rate': round(registration_rate, 2),
            'status_breakdown': status_breakdown,
            'regional_compliance': dict(regional_compliance),
            'infrastructure_compliance': dict(infrastructure_compliance),
            'business_unit_compliance': dict(bu_compliance),
            'datacenter_compliance': dict(datacenter_compliance),
            'compliance_gaps': compliance_gaps,
            'improvement_recommendations': sorted(improvement_recommendations, key=lambda x: x['assets_to_register'], reverse=True)[:10],
            'compliance_analysis': {
                'compliance_status': 'COMPLIANT' if registration_rate >= 90 else 'PARTIAL_COMPLIANCE' if registration_rate >= 70 else 'NON_COMPLIANT',
                'registration_gap': total_count - yes_count,
                'improvement_needed': max(0, round(90 - registration_rate, 2)),
                'governance_maturity': 'MATURE' if registration_rate >= 95 else 'DEVELOPING' if registration_rate >= 80 else 'IMMATURE'
            },
            'audit_readiness': {
                'audit_score': round(registration_rate, 0),
                'compliant_regions': len([r for r, d in regional_compliance.items() if d['status'] == 'COMPLIANT']),
                'managed_facilities': len([dc for dc, d in datacenter_compliance.items() if d['facility_status'] == 'MANAGED']),
                'governance_excellence': len([bu for bu, d in bu_compliance.items() if d['governance_status'] == 'EXCELLENT'])
            }
        })
    except Exception as e:
        logger.error(f"CMDB presence error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/host_search')
def host_search():
    try:
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify({'error': 'Search term required'}), 400
            
        conn = get_db_connection()
        
        search_queries = [
            """
            SELECT 
                COALESCE(host, 'unknown') as host,
                COALESCE(region, 'unknown') as region,
                COALESCE(country, 'unknown') as country,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(source_tables, 'none') as source_tables,
                COALESCE(domain, 'none') as domain,
                COALESCE(data_center, 'unknown') as data_center,
                COALESCE(present_in_cmdb, 'unknown') as present_in_cmdb,
                COALESCE(tanium_coverage, 'unknown') as tanium_coverage,
                COALESCE(business_unit, 'unknown') as business_unit,
                COALESCE(system, 'unknown') as system,
                COALESCE(class, 'unknown') as class
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(host, '')) LIKE LOWER(?) 
               OR LOWER(COALESCE(source_tables, '')) LIKE LOWER(?)
               OR LOWER(COALESCE(domain, '')) LIKE LOWER(?)
            ORDER BY host 
            LIMIT 500
            """,
            """
            SELECT 
                COALESCE(host, 'unknown') as host,
                COALESCE(region, 'unknown') as region,
                COALESCE(country, 'unknown') as country,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(source_tables, 'none') as source_tables,
                COALESCE(domain, 'none') as domain,
                COALESCE(data_center, 'unknown') as data_center,
                COALESCE(present_in_cmdb, 'unknown') as present_in_cmdb,
                COALESCE(tanium_coverage, 'unknown') as tanium_coverage,
                COALESCE(business_unit, 'unknown') as business_unit,
                COALESCE(system, 'unknown') as system,
                COALESCE(class, 'unknown') as class
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(host, '')) LIKE LOWER(?)
            ORDER BY host 
            LIMIT 500
            """
        ]
        
        result = None
        search_pattern = f'%{search_term}%'
        
        for i, query in enumerate(search_queries):
            try:
                if i == 0:
                    result = conn.execute(query, [search_pattern, search_pattern, search_pattern]).fetchall()
                else:
                    result = conn.execute(query, [search_pattern]).fetchall()
                
                if result:
                    logger.info(f"Search query {i+1} returned {len(result)} results")
                    break
            except Exception as e:
                logger.warning(f"Search query {i+1} failed: {e}")
                continue
        
        if not result:
            conn.close()
            return jsonify({'hosts': [], 'total_found': 0, 'search_term': search_term})
        
        hosts = []
        for row in result:
            host_data = {
                'host': row[0],
                'region': row[1],
                'country': row[2],
                'infrastructure_type': row[3],
                'source_tables': row[4],
                'domain': row[5],
                'data_center': row[6],
                'present_in_cmdb': row[7],
                'tanium_coverage': row[8],
                'business_unit': row[9],
                'system': row[10],
                'class': row[11] if len(row) > 11 else 'unknown'
            }
            hosts.append(host_data)
        
        search_analytics = {
            'regions': list(set([h['region'] for h in hosts if h['region'] != 'unknown'])),
            'countries': list(set([h['country'] for h in hosts if h['country'] != 'unknown'])),
            'infrastructure_types': list(set([h['infrastructure_type'] for h in hosts if h['infrastructure_type'] != 'unknown'])),
            'business_units': list(set([h['business_unit'] for h in hosts if h['business_unit'] != 'unknown'])),
            'data_centers': list(set([h['data_center'] for h in hosts if h['data_center'] != 'unknown'])),
            'cmdb_registered': len([h for h in hosts if 'yes' in str(h['present_in_cmdb']).lower()]),
            'tanium_deployed': len([h for h in hosts if 'tanium' in str(h['tanium_coverage']).lower()]),
            'security_coverage': 0
        }
        
        search_analytics['security_coverage'] = round(
            (search_analytics['cmdb_registered'] + search_analytics['tanium_deployed']) / (2 * len(hosts)) * 100, 2
        ) if hosts else 0
        
        conn.close()
        
        return jsonify({
            'hosts': hosts[:100],
            'total_found': len(hosts),
            'search_term': search_term,
            'search_summary': search_analytics,
            'drill_down_available': len(hosts) > 100,
            'search_scope': {
                'searched_fields': ['host', 'source_tables', 'domain'] if len(search_queries) > 1 else ['host'],
                'result_limit': 100,
                'total_matches': len(hosts)
            }
        })
    except Exception as e:
        logger.error(f"Host search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced_analytics')
def advanced_analytics():
    try:
        conn = get_db_connection()
        
        correlation_query = """
        SELECT 
            COALESCE(region, 'unknown') as region,
            COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
            COUNT(*) as asset_count,
            SUM(CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 1 ELSE 0 END) as cmdb_registered,
            SUM(CASE WHEN LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%' THEN 1 ELSE 0 END) as tanium_deployed,
            COUNT(DISTINCT COALESCE(business_unit, 'unknown')) as unique_business_units,
            COUNT(DISTINCT COALESCE(data_center, 'unknown')) as unique_datacenters
        FROM universal_cmdb 
        GROUP BY region, infrastructure_type
        HAVING COUNT(*) >= 10
        ORDER BY asset_count DESC
        """
        
        result = conn.execute(correlation_query).fetchall()
        
        correlation_analysis = []
        total_correlations = 0
        high_risk_combinations = []
        
        for row in result:
            region, infra_type, asset_count, cmdb_count, tanium_count, bu_count, dc_count = row
            
            cmdb_percentage = (cmdb_count / asset_count * 100) if asset_count > 0 else 0
            tanium_percentage = (tanium_count / asset_count * 100) if asset_count > 0 else 0
            combined_security_score = (cmdb_percentage + tanium_percentage) / 2
            
            correlation_data = {
                'region': normalize_region(region),
                'infrastructure_type': infra_type,
                'asset_count': asset_count,
                'cmdb_coverage': round(cmdb_percentage, 2),
                'tanium_coverage': round(tanium_percentage, 2),
                'security_score': round(combined_security_score, 2),
                'business_unit_diversity': bu_count,
                'datacenter_diversity': dc_count,
                'risk_category': 'HIGH' if combined_security_score < 50 else 'MEDIUM' if combined_security_score < 80 else 'LOW'
            }
            
            correlation_analysis.append(correlation_data)
            total_correlations += 1
            
            if combined_security_score < 40:
                high_risk_combinations.append(correlation_data)
        
        trend_analysis = {}
        for item in correlation_analysis:
            region = item['region']
            if region not in trend_analysis:
                trend_analysis[region] = {
                    'total_assets': 0,
                    'avg_security_score': 0,
                    'infrastructure_types': 0,
                    'high_risk_segments': 0
                }
            
            trend_analysis[region]['total_assets'] += item['asset_count']
            trend_analysis[region]['avg_security_score'] += item['security_score'] * item['asset_count']
            trend_analysis[region]['infrastructure_types'] += 1
            if item['risk_category'] == 'HIGH':
                trend_analysis[region]['high_risk_segments'] += 1
        
        for region, data in trend_analysis.items():
            if data['total_assets'] > 0:
                data['avg_security_score'] = round(data['avg_security_score'] / data['total_assets'], 2)
        
        predictive_insights = {
            'security_trends': {
                'improving_regions': [r for r, d in trend_analysis.items() if d['avg_security_score'] >= 80],
                'declining_regions': [r for r, d in trend_analysis.items() if d['avg_security_score'] < 50],
                'stable_regions': [r for r, d in trend_analysis.items() if 50 <= d['avg_security_score'] < 80]
            },
            'infrastructure_modernization': {
                'cloud_adoption_leaders': [],
                'legacy_infrastructure_regions': [],
                'hybrid_environments': []
            },
            'risk_predictions': {
                'high_priority_remediation': len(high_risk_combinations),
                'assets_at_risk': sum(item['asset_count'] for item in high_risk_combinations),
                'projected_incidents': round(sum(item['asset_count'] for item in high_risk_combinations) * 0.1, 0)
            }
        }
        
        conn.close()
        
        return jsonify({
            'correlation_analysis': correlation_analysis,
            'trend_analysis': trend_analysis,
            'high_risk_combinations': sorted(high_risk_combinations, key=lambda x: x['asset_count'], reverse=True),
            'predictive_insights': predictive_insights,
            'analytics_summary': {
                'total_correlations_analyzed': total_correlations,
                'high_risk_segments': len(high_risk_combinations),
                'coverage_gaps_identified': len([item for item in correlation_analysis if item['security_score'] < 70]),
                'modernization_opportunities': len([item for item in correlation_analysis if 'legacy' in item['infrastructure_type'].lower()])
            }
        })
    except Exception as e:
        logger.error(f"Advanced analytics error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        conn = get_db_connection()
        columns, row_count = verify_table_structure(conn)
        conn.close()
        logger.info(f"Database initialized successfully. Columns: {len(columns)}, Rows: {row_count}")
        print(f"✅ Database connection successful! Found {row_count} rows with {len(columns)} columns.")
        print("🚀 Starting Flask server on http://localhost:5000")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print(f"❌ Database connection failed: {e}")
        print("Please ensure your 'universal_cmdb.db' file exists in the project directory.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)