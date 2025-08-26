from flask import Flask, jsonify, request
from flask_cors import CORS
import duckdb
import re
import os
import sys
from collections import Counter, defaultdict
import logging

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
    
    try:
        logger.info("Attempting in-memory connection with test data")
        conn = duckdb.connect(':memory:')
        return conn
    except Exception as e:
        logger.error(f"All connection methods failed: {e}")
        raise Exception("Unable to connect to database")

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
    region_lower = region.lower().strip()
    
    na_indicators = ['us', 'usa', 'united states', 'canada', 'ca', 'can', 'north america', 'na', 'mexico', 'mx', 'mex']
    emea_indicators = ['europe', 'emea', 'eu', 'middle east', 'africa', 'uk', 'gb', 'britain', 'germany', 'de', 'france', 'fr']
    latam_indicators = ['latin america', 'latam', 'south america', 'central america', 'brazil', 'br', 'argentina', 'ar']
    apac_indicators = ['asia pacific', 'apac', 'asia', 'pacific', 'australia', 'au', 'new zealand', 'nz', 'japan', 'jp', 'china', 'cn', 'india', 'in']
    
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
            SELECT DISTINCT source_tables as source_table, 1 as frequency, 1 as unique_hosts
            FROM universal_cmdb 
            WHERE source_tables IS NOT NULL
            LIMIT 50
            """
        ]
        
        result = None
        for query in queries_to_try:
            try:
                result = conn.execute(query).fetchall()
                if result:
                    break
            except Exception as e:
                logger.warning(f"Query failed: {e}")
                continue
        
        if not result:
            result = []
        
        total_rows = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE source_tables IS NOT NULL").fetchone()[0]
        
        data = {}
        detailed_data = []
        total_mentions = 0
        
        for row in result:
            source_name, frequency, unique_hosts = row
            data[source_name] = frequency
            total_mentions += frequency
            
            percentage = (frequency / total_mentions * 100) if total_mentions > 0 else 0
            detailed_data.append({
                'source': source_name,
                'frequency': frequency,
                'unique_hosts': unique_hosts,
                'percentage': round(percentage, 2)
            })
        
        conn.close()
        
        return jsonify({
            'data': data,
            'detailed_data': detailed_data,
            'total_sources': len(data),
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

@app.route('/api/source_tables_drilldown')
def source_tables_drilldown():
    source = request.args.get('source')
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                host,
                source_tables,
                COALESCE(region, 'unknown') as region,
                COALESCE(country, 'unknown') as country,
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type,
                COALESCE(business_unit, 'unknown') as business_unit
            FROM universal_cmdb 
            WHERE source_tables LIKE ?
            ORDER BY host
            LIMIT 500
        """, [f'%{source}%']).fetchall()
        
        conn.close()
        
        hosts_with_source = []
        region_breakdown = Counter()
        infra_breakdown = Counter()
        
        for row in result:
            host, source_tables, region, country, infrastructure_type, business_unit = row
            hosts_with_source.append({
                'host': host,
                'source_tables': source_tables,
                'region': region,
                'country': country,
                'infrastructure_type': infrastructure_type,
                'business_unit': business_unit
            })
            region_breakdown[region] += 1
            infra_breakdown[infrastructure_type] += 1
        
        return jsonify({
            'hosts': hosts_with_source[:100],
            'total_hosts': len(hosts_with_source),
            'region_breakdown': dict(region_breakdown),
            'infrastructure_breakdown': dict(infra_breakdown),
            'source_analyzed': source
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/domain_metrics')
def domain_metrics():
    try:
        conn = get_db_connection()
        
        queries_to_try = [
            """
            SELECT 
                host,
                domain,
                CASE 
                    WHEN LOWER(domain) LIKE '%1dc%' THEN '1dc'
                    WHEN LOWER(domain) LIKE '%fead%' THEN 'fead'
                    ELSE 'other'
                END as domain_type
            FROM universal_cmdb 
            WHERE domain IS NOT NULL AND domain != ''
            """,
            """
            SELECT host, domain, 'other' as domain_type
            FROM universal_cmdb 
            WHERE domain IS NOT NULL
            LIMIT 1000
            """
        ]
        
        rows = None
        for query in queries_to_try:
            try:
                rows = conn.execute(query).fetchall()
                if rows:
                    break
            except Exception as e:
                logger.warning(f"Domain query failed: {e}")
                continue
        
        domain_counter = Counter()
        detailed_domains = []
        unique_domains = set()
        
        if rows:
            for row in rows:
                host, domain, domain_type = row
                domain_counter[domain_type] += 1
                
                if '|' in str(domain):
                    for d in str(domain).split('|'):
                        d = d.strip()
                        if d:
                            unique_domains.add(d)
                            if '1dc' in d.lower():
                                domain_counter['1dc'] += 1
                            elif 'fead' in d.lower():
                                domain_counter['fead'] += 1
                else:
                    if str(domain).strip():
                        unique_domains.add(str(domain).strip())
        
        total_analyzed = sum(domain_counter.values())
        
        domain_details = {}
        for domain_type, count in domain_counter.items():
            percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
            domain_details[domain_type] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        conn.close()
        
        return jsonify({
            'domain_analysis': dict(domain_counter),
            'domain_details': domain_details,
            'unique_domains': list(unique_domains)[:50],
            'total_analyzed': total_analyzed,
            'domain_distribution': {
                '1dc_percentage': domain_details.get('1dc', {}).get('percentage', 0),
                'fead_percentage': domain_details.get('fead', {}).get('percentage', 0),
                'other_percentage': domain_details.get('other', {}).get('percentage', 0)
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
            SELECT infrastructure_type, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE infrastructure_type IS NOT NULL AND infrastructure_type != ''
            GROUP BY infrastructure_type
            ORDER BY frequency DESC
        """).fetchall()
        
        infrastructure_matrix = {}
        detailed_data = []
        total_count = 0
        
        for row in result:
            infra_type, frequency = row
            
            if '|' in str(infra_type):
                for i_type in str(infra_type).split('|'):
                    i_type = i_type.strip()
                    if i_type:
                        infrastructure_matrix[i_type] = infrastructure_matrix.get(i_type, 0) + frequency
                        total_count += frequency
            else:
                if str(infra_type).strip():
                    infrastructure_matrix[str(infra_type)] = frequency
                    total_count += frequency
        
        for infra_type, frequency in infrastructure_matrix.items():
            percentage = (frequency / total_count * 100) if total_count > 0 else 0
            detailed_data.append({
                'type': infra_type,
                'frequency': frequency,
                'percentage': round(percentage, 2)
            })
        
        detailed_data.sort(key=lambda x: x['frequency'], reverse=True)
        
        conn.close()
        
        return jsonify({
            'infrastructure_matrix': infrastructure_matrix,
            'detailed_data': detailed_data,
            'total_types': len(infrastructure_matrix),
            'distribution_analysis': {
                'top_5': detailed_data[:5],
                'total_instances': total_count,
                'diversity_score': len(infrastructure_matrix)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/region_metrics')
def region_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT region, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE region IS NOT NULL AND region != ''
            GROUP BY region
            ORDER BY frequency DESC
        """).fetchall()
        
        region_counter = {'north america': 0, 'emea': 0, 'latam': 0, 'apac': 0}
        region_details = {'north america': [], 'emea': [], 'latam': [], 'apac': []}
        raw_regions = []
        
        for row in result:
            region, frequency = row
            raw_regions.append({'region': region, 'frequency': frequency})
            
            if '|' in str(region):
                for r in str(region).split('|'):
                    r = r.strip()
                    if r:
                        normalized = normalize_region(r)
                        if normalized in region_counter:
                            region_counter[normalized] += frequency
                            region_details[normalized].append({
                                'original': r,
                                'frequency': frequency
                            })
            else:
                if str(region).strip():
                    normalized = normalize_region(str(region))
                    if normalized in region_counter:
                        region_counter[normalized] += frequency
                        region_details[normalized].append({
                            'original': str(region),
                            'frequency': frequency
                        })
        
        conn.close()
        
        return jsonify({
            'global_surveillance': region_counter,
            'region_details': region_details,
            'raw_regions': raw_regions,
            'total_coverage': sum(region_counter.values()),
            'regional_distribution': {
                region: {
                    'count': count,
                    'percentage': round((count / sum(region_counter.values()) * 100), 2) if sum(region_counter.values()) > 0 else 0
                }
                for region, count in region_counter.items()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tanium_coverage')
def tanium_coverage():
    try:
        conn = get_db_connection()
        
        queries_to_try = [
            "SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(tanium_coverage) LIKE '%tanium%'",
            "SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage IS NOT NULL",
            "SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage = 'yes'"
        ]
        
        tanium_count = 0
        for query in queries_to_try:
            try:
                tanium_count = conn.execute(query).fetchone()[0]
                if tanium_count > 0:
                    break
            except:
                continue
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        coverage_percentage = (tanium_count / total_count * 100) if total_count > 0 else 0
        
        try:
            status_breakdown = conn.execute("""
                SELECT 
                    CASE 
                        WHEN LOWER(tanium_coverage) LIKE '%tanium%' THEN 'deployed'
                        ELSE 'not_deployed'
                    END as status,
                    COUNT(*) as count
                FROM universal_cmdb
                GROUP BY CASE WHEN LOWER(tanium_coverage) LIKE '%tanium%' THEN 'deployed' ELSE 'not_deployed' END
            """).fetchall()
            
            status_data = {}
            for row in status_breakdown:
                status, count = row
                percentage = (count / total_count * 100) if total_count > 0 else 0
                status_data[status] = {'count': count, 'percentage': round(percentage, 2)}
            
        except:
            status_data = {
                'deployed': {'count': tanium_count, 'percentage': round(coverage_percentage, 2)},
                'not_deployed': {'count': total_count - tanium_count, 'percentage': round(100 - coverage_percentage, 2)}
            }
        
        conn.close()
        
        return jsonify({
            'tanium_deployed': tanium_count,
            'total_assets': total_count,
            'coverage_percentage': round(coverage_percentage, 2),
            'status_breakdown': status_data,
            'deployment_analysis': {
                'coverage_status': 'OPTIMAL' if coverage_percentage >= 80 else 'CRITICAL' if coverage_percentage < 60 else 'ACCEPTABLE',
                'deployment_gap': total_count - tanium_count,
                'recommended_action': 'MAINTAIN' if coverage_percentage >= 80 else 'URGENT_DEPLOY' if coverage_percentage < 60 else 'EXPAND_COVERAGE'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cmdb_presence')
def cmdb_presence():
    try:
        conn = get_db_connection()
        
        queries_to_try = [
            "SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(present_in_cmdb) LIKE '%yes%'",
            "SELECT COUNT(*) FROM universal_cmdb WHERE present_in_cmdb IS NOT NULL",
            "SELECT COUNT(*) FROM universal_cmdb WHERE present_in_cmdb = 'yes'"
        ]
        
        yes_count = 0
        for query in queries_to_try:
            try:
                yes_count = conn.execute(query).fetchone()[0]
                if yes_count > 0:
                    break
            except:
                continue
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        registration_rate = (yes_count / total_count * 100) if total_count > 0 else 0
        
        try:
            presence_breakdown = conn.execute("""
                SELECT 
                    CASE 
                        WHEN LOWER(present_in_cmdb) LIKE '%yes%' THEN 'registered'
                        ELSE 'not_registered'
                    END as status,
                    COUNT(*) as count
                FROM universal_cmdb
                GROUP BY CASE WHEN LOWER(present_in_cmdb) LIKE '%yes%' THEN 'registered' ELSE 'not_registered' END
            """).fetchall()
            
            status_data = {}
            for row in presence_breakdown:
                status, count = row
                percentage = (count / total_count * 100) if total_count > 0 else 0
                status_data[status] = {'count': count, 'percentage': round(percentage, 2)}
                
        except:
            status_data = {
                'registered': {'count': yes_count, 'percentage': round(registration_rate, 2)},
                'not_registered': {'count': total_count - yes_count, 'percentage': round(100 - registration_rate, 2)}
            }
        
        conn.close()
        
        return jsonify({
            'cmdb_registered': yes_count,
            'total_assets': total_count,
            'registration_rate': round(registration_rate, 2),
            'status_breakdown': status_data,
            'compliance_analysis': {
                'compliance_status': 'COMPLIANT' if registration_rate >= 90 else 'NON_COMPLIANT' if registration_rate < 70 else 'PARTIAL_COMPLIANCE',
                'registration_gap': total_count - yes_count,
                'improvement_needed': round(90 - registration_rate, 2) if registration_rate < 90 else 0
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/host_search')
def host_search():
    try:
        search_term = request.args.get('q', '')
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT host, region, country, infrastructure_type, 
                   source_tables, domain, data_center, present_in_cmdb, tanium_coverage
            FROM universal_cmdb 
            WHERE LOWER(host) LIKE LOWER(?) 
            ORDER BY host 
            LIMIT 500
        """, [f'%{search_term}%']).fetchall()
        
        conn.close()
        
        hosts = []
        for row in result:
            hosts.append({
                'host': row[0] if row[0] else 'unknown',
                'region': row[1] if row[1] else 'unknown',
                'country': row[2] if row[2] else 'unknown',
                'infrastructure_type': row[3] if row[3] else 'unknown',
                'source_tables': row[4] if row[4] else 'none',
                'domain': row[5] if row[5] else 'none',
                'data_center': row[6] if row[6] else 'unknown',
                'present_in_cmdb': row[7] if row[7] else 'unknown',
                'tanium_coverage': row[8] if row[8] else 'unknown'
            })
        
        return jsonify({
            'hosts': hosts[:100],
            'total_found': len(hosts),
            'search_term': search_term,
            'search_summary': {
                'regions': list(set([h['region'] for h in hosts])),
                'countries': list(set([h['country'] for h in hosts])),
                'infrastructure_types': list(set([h['infrastructure_type'] for h in hosts]))
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        conn = get_db_connection()
        columns, row_count = verify_table_structure(conn)
        conn.close()
        logger.info(f"Database initialized successfully. Columns: {len(columns)}, Rows: {row_count}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)