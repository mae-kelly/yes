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
    
    error_msg = """
    ❌ Database file 'universal_cmdb.db' not found!
    
    Please ensure:
    1. Your database file is named 'universal_cmdb.db'
    2. It's placed in the project root directory 
    3. It contains a table named 'universal_cmdb'
    4. The table has the expected columns for analysis
    
    Searched locations:
    {}
    """.format('\n    '.join(db_paths))
    
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
            detailed_data.append({
                'source': source_name,
                'frequency': frequency,
                'unique_hosts': unique_hosts if 'unique_hosts' in locals() else 1,
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
            SELECT 
                COALESCE(host, 'unknown') as host,
                COALESCE(domain, 'unknown') as domain,
                'other' as domain_type
            FROM universal_cmdb 
            """
        ]
        
        rows = None
        for i, query in enumerate(queries_to_try):
            try:
                logger.info(f"Trying domain query {i+1}")
                rows = conn.execute(query).fetchall()
                if rows:
                    logger.info(f"Domain query {i+1} succeeded with {len(rows)} results")
                    break
            except Exception as e:
                logger.warning(f"Domain query {i+1} failed: {e}")
                continue
        
        domain_counter = Counter()
        unique_domains = set()
        
        if rows:
            for row in rows:
                host, domain, domain_type = row
                
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
                                domain_counter['other'] += 1
                else:
                    if str(domain).strip() and str(domain).strip().lower() != 'unknown':
                        unique_domains.add(str(domain).strip())
                        if '1dc' in str(domain).lower():
                            domain_counter['1dc'] += 1
                        elif 'fead' in str(domain).lower():
                            domain_counter['fead'] += 1
                        else:
                            domain_counter['other'] += 1
        
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
            SELECT 
                COALESCE(infrastructure_type, 'unknown') as infrastructure_type, 
                COUNT(*) as frequency
            FROM universal_cmdb 
            GROUP BY infrastructure_type
            ORDER BY frequency DESC
        """).fetchall()
        
        infrastructure_matrix = {}
        detailed_data = []
        total_count = 0
        
        for row in result:
            infra_type, frequency = row
            
            if infra_type and infra_type != 'unknown':
                if '|' in str(infra_type):
                    for i_type in str(infra_type).split('|'):
                        i_type = i_type.strip()
                        if i_type:
                            infrastructure_matrix[i_type] = infrastructure_matrix.get(i_type, 0) + frequency
                            total_count += frequency
                else:
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
        logger.error(f"Infrastructure type error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/region_metrics')
def region_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT 
                COALESCE(region, 'unknown') as region, 
                COUNT(*) as frequency
            FROM universal_cmdb 
            GROUP BY region
            ORDER BY frequency DESC
        """).fetchall()
        
        region_counter = {'north america': 0, 'emea': 0, 'latam': 0, 'apac': 0}
        region_details = {'north america': [], 'emea': [], 'latam': [], 'apac': []}
        raw_regions = []
        
        for row in result:
            region, frequency = row
            if region and region != 'unknown':
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
                    normalized = normalize_region(str(region))
                    if normalized in region_counter:
                        region_counter[normalized] += frequency
                        region_details[normalized].append({
                            'original': str(region),
                            'frequency': frequency
                        })
        
        total_coverage = sum(region_counter.values())
        
        conn.close()
        
        return jsonify({
            'global_surveillance': region_counter,
            'region_details': region_details,
            'raw_regions': raw_regions,
            'total_coverage': total_coverage,
            'regional_distribution': {
                region: {
                    'count': count,
                    'percentage': round((count / total_coverage * 100), 2) if total_coverage > 0 else 0
                }
                for region, count in region_counter.items()
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
                COUNT(*) as frequency
            FROM universal_cmdb 
            GROUP BY country
            ORDER BY frequency DESC
        """).fetchall()
        
        country_counter = Counter()
        
        for row in result:
            country, frequency = row
            if country and country != 'unknown':
                if '|' in str(country):
                    for c in str(country).split('|'):
                        c = c.strip()
                        if c:
                            normalized = normalize_country(c)
                            country_counter[normalized] += frequency
                else:
                    normalized = normalize_country(str(country))
                    country_counter[normalized] += frequency
        
        conn.close()
        
        return jsonify({
            'global_intelligence': dict(country_counter),
            'total_countries': len(country_counter),
            'country_distribution': {
                country: {
                    'count': count,
                    'percentage': round((count / sum(country_counter.values()) * 100), 2) if sum(country_counter.values()) > 0 else 0
                }
                for country, count in country_counter.most_common()
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
                COUNT(*) as frequency
            FROM universal_cmdb 
            GROUP BY data_center
            ORDER BY frequency DESC
        """).fetchall()
        
        facility_intelligence = {}
        
        for row in result:
            data_center, frequency = row
            if data_center and data_center != 'unknown':
                first_word = str(data_center).split()[0] if str(data_center).split() else str(data_center)
                facility_intelligence[first_word] = facility_intelligence.get(first_word, 0) + frequency
        
        conn.close()
        
        return jsonify({
            'facility_intelligence': facility_intelligence,
            'total_facilities': len(facility_intelligence),
            'datacenter_analysis': {
                'unique_facilities': len(facility_intelligence),
                'total_instances': sum(facility_intelligence.values())
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
            SELECT DISTINCT 
                COALESCE(cloud_region, 'unknown') as cloud_region
            FROM universal_cmdb 
            WHERE cloud_region IS NOT NULL AND cloud_region != ''
            ORDER BY cloud_region
        """).fetchall()
        
        cloud_matrix = []
        for row in result:
            cloud_region = row[0]
            if cloud_region and cloud_region != 'unknown':
                cloud_matrix.append(cloud_region)
        
        conn.close()
        
        return jsonify({
            'cloud_matrix': cloud_matrix,
            'total_regions': len(cloud_matrix)
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
                class_matches = re.findall(r'class\s*(\d+)', str(class_name).lower())
                if class_matches:
                    for match in class_matches:
                        classification_matrix[f"class{match}"] = classification_matrix.get(f"class{match}", 0) + frequency
                else:
                    classification_matrix[str(class_name)] = frequency
        
        conn.close()
        
        return jsonify({
            'classification_matrix': classification_matrix,
            'total_classes': len(classification_matrix)
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
                COUNT(*) as frequency
            FROM universal_cmdb 
            GROUP BY system
            ORDER BY frequency DESC
        """).fetchall()
        
        system_matrix = {}
        
        for row in result:
            system_name, frequency = row
            if system_name and system_name != 'unknown':
                if '|' in str(system_name):
                    for s in str(system_name).split('|'):
                        s = s.strip()
                        if s:
                            system_matrix[s] = system_matrix.get(s, 0) + frequency
                else:
                    system_matrix[str(system_name)] = frequency
        
        conn.close()
        
        return jsonify({
            'system_matrix': system_matrix,
            'total_systems': len(system_matrix)
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
                COUNT(*) as frequency
            FROM universal_cmdb 
            GROUP BY business_unit
            ORDER BY frequency DESC
        """).fetchall()
        
        business_intelligence = {}
        
        for row in result:
            bu_name, frequency = row
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
        
        conn.close()
        
        return jsonify({
            'business_intelligence': business_intelligence,
            'total_business_units': len(business_intelligence)
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
                COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE cio IS NOT NULL AND cio != ''
            GROUP BY cio
            ORDER BY frequency DESC
        """).fetchall()
        
        operative_intelligence = {}
        
        for row in result:
            cio_name, frequency = row
            if cio_name and cio_name != 'unknown':
                if '|' in str(cio_name):
                    for c in str(cio_name).split('|'):
                        c = c.strip()
                        if c and re.search(r'[a-zA-Z]', c):
                            operative_intelligence[c] = operative_intelligence.get(c, 0) + frequency
                else:
                    if re.search(r'[a-zA-Z]', str(cio_name)):
                        operative_intelligence[str(cio_name)] = frequency
        
        conn.close()
        
        return jsonify({
            'operative_intelligence': operative_intelligence,
            'total_cio_entries': len(operative_intelligence)
        })
    except Exception as e:
        logger.error(f"CIO metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tanium_coverage')
def tanium_coverage():
    try:
        conn = get_db_connection()
        
        tanium_count = conn.execute("""
            SELECT COUNT(*) 
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%'
        """).fetchone()[0]
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        coverage_percentage = (tanium_count / total_count * 100) if total_count > 0 else 0
        
        status_breakdown = conn.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%' THEN 'deployed'
                    ELSE 'not_deployed'
                END as status,
                COUNT(*) as count
            FROM universal_cmdb
            GROUP BY CASE WHEN LOWER(COALESCE(tanium_coverage, '')) LIKE '%tanium%' THEN 'deployed' ELSE 'not_deployed' END
        """).fetchall()
        
        status_data = {}
        for row in status_breakdown:
            status, count = row
            percentage = (count / total_count * 100) if total_count > 0 else 0
            status_data[status] = {'count': count, 'percentage': round(percentage, 2)}
        
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
        logger.error(f"Tanium coverage error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cmdb_presence')
def cmdb_presence():
    try:
        conn = get_db_connection()
        
        yes_count = conn.execute("""
            SELECT COUNT(*) 
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%'
        """).fetchone()[0]
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        registration_rate = (yes_count / total_count * 100) if total_count > 0 else 0
        
        presence_breakdown = conn.execute("""
            SELECT 
                CASE 
                    WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 'registered'
                    ELSE 'not_registered'
                END as status,
                COUNT(*) as count
            FROM universal_cmdb
            GROUP BY CASE WHEN LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%' THEN 'registered' ELSE 'not_registered' END
        """).fetchall()
        
        status_data = {}
        for row in presence_breakdown:
            status, count = row
            percentage = (count / total_count * 100) if total_count > 0 else 0
            status_data[status] = {'count': count, 'percentage': round(percentage, 2)}
        
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
        logger.error(f"CMDB presence error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/host_search')
def host_search():
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
                COALESCE(source_tables, 'none') as source_tables,
                COALESCE(domain, 'none') as domain,
                COALESCE(data_center, 'unknown') as data_center,
                COALESCE(present_in_cmdb, 'unknown') as present_in_cmdb,
                COALESCE(tanium_coverage, 'unknown') as tanium_coverage
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(host, '')) LIKE LOWER(?) 
            ORDER BY host 
            LIMIT 500
        """, [f'%{search_term}%']).fetchall()
        
        conn.close()
        
        hosts = []
        for row in result:
            hosts.append({
                'host': row[0],
                'region': row[1],
                'country': row[2],
                'infrastructure_type': row[3],
                'source_tables': row[4],
                'domain': row[5],
                'data_center': row[6],
                'present_in_cmdb': row[7],
                'tanium_coverage': row[8]
            })
        
        return jsonify({
            'hosts': hosts[:100],
            'total_found': len(hosts),
            'search_term': search_term,
            'search_summary': {
                'regions': list(set([h['region'] for h in hosts if h['region'] != 'unknown'])),
                'countries': list(set([h['country'] for h in hosts if h['country'] != 'unknown'])),
                'infrastructure_types': list(set([h['infrastructure_type'] for h in hosts if h['infrastructure_type'] != 'unknown']))
            }
        })
    except Exception as e:
        logger.error(f"Host search error: {e}")
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