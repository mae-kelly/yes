# ech/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import duckdb
import re
import os
import logging
from collections import Counter, defaultdict

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
                if any('universal_cmdb' in str(table).lower() for table in tables):
                    logger.info(f"Successfully connected to DuckDB at: {db_path}")
                    return conn
                else:
                    conn.close()
        except Exception as e:
            logger.error(f"Failed to connect to {db_path}: {e}")
            continue
    
    raise Exception("Database file 'universal_cmdb.db' not found!")

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

@app.route('/api/source_tables')
def source_tables_metrics():
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                TRIM(UNNEST(STRING_SPLIT(source_tables, ','))) as source_table,
                COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE source_tables IS NOT NULL AND source_tables != ''
            GROUP BY TRIM(UNNEST(STRING_SPLIT(source_tables, ',')))
            HAVING TRIM(UNNEST(STRING_SPLIT(source_tables, ','))) != ''
            ORDER BY frequency DESC
        """
        
        try:
            result = conn.execute(query).fetchall()
        except:
            fallback_query = """
                SELECT 
                    source_tables as source_table,
                    COUNT(*) as frequency
                FROM universal_cmdb 
                WHERE source_tables IS NOT NULL AND source_tables != ''
                GROUP BY source_tables
                ORDER BY frequency DESC
            """
            result = conn.execute(fallback_query).fetchall()
        
        source_intelligence = {}
        total_mentions = 0
        
        for row in result:
            source_name, frequency = row
            if source_name and source_name.strip():
                source_intelligence[source_name.strip()] = frequency
                total_mentions += frequency
        
        conn.close()
        
        return jsonify({
            'source_intelligence': source_intelligence,
            'total_mentions': total_mentions,
            'unique_sources': len(source_intelligence),
            'top_sources': dict(list(source_intelligence.items())[:20])
        })
    except Exception as e:
        logger.error(f"Source tables error: {e}")
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

@app.route('/api/domain_metrics')
def domain_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT host, domain
            FROM universal_cmdb 
            WHERE domain IS NOT NULL AND domain != ''
        """).fetchall()
        
        domain_battle = {'1dc': 0, 'fead': 0, 'other': 0}
        domain_details = []
        
        for row in result:
            host, domain = row
            
            if '|' in str(domain):
                domains = [d.strip() for d in str(domain).split('|') if d.strip()]
            else:
                domains = [str(domain).strip()] if str(domain).strip() else []
            
            has_1dc = any('1dc' in d.lower() for d in domains if d)
            has_fead = any('fead' in d.lower() for d in domains if d)
            
            if has_1dc:
                domain_battle['1dc'] += 1
                classification = '1dc'
            elif has_fead:
                domain_battle['fead'] += 1
                classification = 'fead'
            else:
                domain_battle['other'] += 1
                classification = 'other'
            
            domain_details.append({
                'host': host,
                'domains': domains,
                'classification': classification
            })
        
        total_analyzed = sum(domain_battle.values())
        
        conn.close()
        
        return jsonify({
            'domain_battle': domain_battle,
            'total_analyzed': total_analyzed,
            'battle_percentages': {
                '1dc_percentage': round((domain_battle['1dc'] / total_analyzed * 100), 2) if total_analyzed > 0 else 0,
                'fead_percentage': round((domain_battle['fead'] / total_analyzed * 100), 2) if total_analyzed > 0 else 0,
                'other_percentage': round((domain_battle['other'] / total_analyzed * 100), 2) if total_analyzed > 0 else 0
            },
            'domain_details': domain_details[:100]
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
        
        for row in result:
            infra_type, frequency = row
            if infra_type and '|' in str(infra_type):
                for i_type in str(infra_type).split('|'):
                    i_type = i_type.strip()
                    if i_type:
                        infrastructure_matrix[i_type] = infrastructure_matrix.get(i_type, 0) + frequency
            else:
                if infra_type:
                    infrastructure_matrix[str(infra_type).strip()] = frequency
        
        conn.close()
        
        return jsonify({
            'infrastructure_matrix': infrastructure_matrix,
            'total_types': len(infrastructure_matrix),
            'infrastructure_distribution': {
                infra_type: {
                    'count': count,
                    'percentage': round((count / sum(infrastructure_matrix.values()) * 100), 2) if sum(infrastructure_matrix.values()) > 0 else 0
                }
                for infra_type, count in sorted(infrastructure_matrix.items(), key=lambda x: x[1], reverse=True)
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
            SELECT region, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE region IS NOT NULL AND region != ''
            GROUP BY region
            ORDER BY frequency DESC
        """).fetchall()
        
        global_regions = {'north america': 0, 'emea': 0, 'latam': 0, 'apac': 0}
        
        for row in result:
            region, frequency = row
            if region and '|' in str(region):
                for r in str(region).split('|'):
                    r = r.strip()
                    if r:
                        normalized = normalize_region(r)
                        if normalized in global_regions:
                            global_regions[normalized] += frequency
            else:
                if region:
                    normalized = normalize_region(str(region))
                    if normalized in global_regions:
                        global_regions[normalized] += frequency
        
        total_coverage = sum(global_regions.values())
        
        conn.close()
        
        return jsonify({
            'global_regions': global_regions,
            'total_coverage': total_coverage,
            'regional_distribution': {
                region: {
                    'count': count,
                    'percentage': round((count / total_coverage * 100), 2) if total_coverage > 0 else 0
                }
                for region, count in global_regions.items()
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
            SELECT country, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE country IS NOT NULL AND country != ''
            GROUP BY country
            ORDER BY frequency DESC
        """).fetchall()
        
        country_intelligence = {}
        
        for row in result:
            country, frequency = row
            if country and '|' in str(country):
                for c in str(country).split('|'):
                    c = c.strip()
                    if c:
                        normalized = normalize_country(c)
                        country_intelligence[normalized] = country_intelligence.get(normalized, 0) + frequency
            else:
                if country:
                    normalized = normalize_country(str(country))
                    country_intelligence[normalized] = frequency
        
        conn.close()
        
        return jsonify({
            'country_intelligence': country_intelligence,
            'total_countries': len(country_intelligence),
            'country_distribution': {
                country: {
                    'count': count,
                    'percentage': round((count / sum(country_intelligence.values()) * 100), 2) if sum(country_intelligence.values()) > 0 else 0
                }
                for country, count in sorted(country_intelligence.items(), key=lambda x: x[1], reverse=True)
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
            SELECT data_center, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE data_center IS NOT NULL AND data_center != ''
            GROUP BY data_center
            ORDER BY frequency DESC
        """).fetchall()
        
        facility_intelligence = {}
        
        for row in result:
            data_center, frequency = row
            if data_center:
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
            SELECT cloud_region, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE cloud_region IS NOT NULL AND cloud_region != ''
            GROUP BY cloud_region
            ORDER BY frequency DESC
        """).fetchall()
        
        cloud_matrix = {}
        
        for row in result:
            cloud_region, frequency = row
            if cloud_region and '|' in str(cloud_region):
                for region in str(cloud_region).split('|'):
                    region = region.strip()
                    if region:
                        cloud_matrix[region] = cloud_matrix.get(region, 0) + frequency
            else:
                if cloud_region:
                    cloud_matrix[str(cloud_region).strip()] = frequency
        
        conn.close()
        
        return jsonify({
            'cloud_matrix': cloud_matrix,
            'unique_regions': list(cloud_matrix.keys()),
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
            SELECT class, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE class IS NOT NULL AND class != ''
            GROUP BY class
            ORDER BY frequency DESC
        """).fetchall()
        
        class_analysis = {}
        
        for row in result:
            class_name, frequency = row
            if class_name:
                class_matches = re.findall(r'class\s*(\d+)', str(class_name).lower())
                if class_matches:
                    for match in class_matches:
                        class_key = f"class{match}"
                        class_analysis[class_key] = class_analysis.get(class_key, 0) + frequency
                else:
                    class_analysis[str(class_name)] = frequency
        
        conn.close()
        
        return jsonify({
            'class_analysis': class_analysis,
            'total_classes': len(class_analysis),
            'class_distribution': sorted(class_analysis.items(), key=lambda x: x[1], reverse=True)
        })
    except Exception as e:
        logger.error(f"Class metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_classification_metrics')
def system_classification_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT system_classification, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE system_classification IS NOT NULL AND system_classification != ''
            GROUP BY system_classification
            ORDER BY frequency DESC
        """).fetchall()
        
        system_matrix = {}
        
        for row in result:
            system_name, frequency = row
            if system_name and '|' in str(system_name):
                for s in str(system_name).split('|'):
                    s = s.strip()
                    if s:
                        system_matrix[s] = system_matrix.get(s, 0) + frequency
            else:
                if system_name:
                    system_matrix[str(system_name).strip()] = frequency
        
        conn.close()
        
        return jsonify({
            'system_matrix': system_matrix,
            'total_systems': len(system_matrix),
            'system_distribution': sorted(system_matrix.items(), key=lambda x: x[1], reverse=True)
        })
    except Exception as e:
        logger.error(f"System classification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/business_unit_metrics')
def business_unit_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT business_unit, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE business_unit IS NOT NULL AND business_unit != ''
            GROUP BY business_unit
            ORDER BY frequency DESC
        """).fetchall()
        
        business_intelligence = {}
        
        for row in result:
            bu_name, frequency = row
            if bu_name:
                units = [bu_name]
                for sep in [',', '|']:
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
            'total_business_units': len(business_intelligence),
            'bu_distribution': sorted(business_intelligence.items(), key=lambda x: x[1], reverse=True)
        })
    except Exception as e:
        logger.error(f"Business unit metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cio_metrics')
def cio_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            SELECT cio, COUNT(*) as frequency
            FROM universal_cmdb 
            WHERE cio IS NOT NULL AND cio != ''
            GROUP BY cio
            ORDER BY frequency DESC
        """).fetchall()
        
        cio_intelligence = {}
        
        for row in result:
            cio_name, frequency = row
            if cio_name and '|' in str(cio_name):
                for c in str(cio_name).split('|'):
                    c = c.strip()
                    if c and re.search(r'[a-zA-Z]', c):
                        cio_intelligence[c] = cio_intelligence.get(c, 0) + frequency
            else:
                if cio_name and re.search(r'[a-zA-Z]', str(cio_name)):
                    cio_intelligence[str(cio_name).strip()] = frequency
        
        conn.close()
        
        return jsonify({
            'cio_intelligence': cio_intelligence,
            'total_cio_entries': len(cio_intelligence),
            'cio_distribution': sorted(cio_intelligence.items(), key=lambda x: x[1], reverse=True)
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
        
        coverage_percentage = round((tanium_count / total_count * 100), 2) if total_count > 0 else 0
        
        conn.close()
        
        return jsonify({
            'tanium_deployed': tanium_count,
            'total_assets': total_count,
            'coverage_percentage': coverage_percentage,
            'deployment_gap': total_count - tanium_count,
            'threat_level': 'LOW' if coverage_percentage >= 80 else 'CRITICAL' if coverage_percentage < 60 else 'MEDIUM'
        })
    except Exception as e:
        logger.error(f"Tanium coverage error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cmdb_presence')
def cmdb_presence():
    try:
        conn = get_db_connection()
        
        registered_count = conn.execute("""
            SELECT COUNT(*) 
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(present_in_cmdb, '')) LIKE '%yes%'
        """).fetchone()[0]
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        registration_rate = round((registered_count / total_count * 100), 2) if total_count > 0 else 0
        
        conn.close()
        
        return jsonify({
            'cmdb_registered': registered_count,
            'total_assets': total_count,
            'registration_rate': registration_rate,
            'registration_gap': total_count - registered_count,
            'compliance_status': 'COMPLIANT' if registration_rate >= 90 else 'NON_COMPLIANT' if registration_rate < 70 else 'PARTIAL'
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
            SELECT host, region, country, infrastructure_type, source_tables, domain,
                   data_center, present_in_cmdb, tanium_coverage, business_unit, cio
            FROM universal_cmdb 
            WHERE LOWER(COALESCE(host, '')) LIKE LOWER(?) 
            ORDER BY host 
            LIMIT 100
        """, [f'%{search_term}%']).fetchall()
        
        hosts = []
        for row in result:
            hosts.append({
                'host': row[0] or 'unknown',
                'region': row[1] or 'unknown',
                'country': row[2] or 'unknown',
                'infrastructure_type': row[3] or 'unknown',
                'source_tables': row[4] or 'none',
                'domain': row[5] or 'none',
                'data_center': row[6] or 'unknown',
                'present_in_cmdb': row[7] or 'unknown',
                'tanium_coverage': row[8] or 'unknown',
                'business_unit': row[9] or 'unknown',
                'cio': row[10] or 'unknown'
            })
        
        conn.close()
        
        return jsonify({
            'hosts': hosts,
            'total_found': len(hosts),
            'search_term': search_term
        })
    except Exception as e:
        logger.error(f"Host search error: {e}")