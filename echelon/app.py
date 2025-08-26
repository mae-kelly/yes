from flask import Flask, jsonify, request
from flask_cors import CORS
import duckdb
import re
from collections import Counter, defaultdict

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return duckdb.connect('universal_cmdb.db')

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
    emea_indicators = ['europe', 'emea', 'eu', 'middle east', 'africa', 'uk', 'gb', 'britain', 'germany', 'de', 'france', 'fr', 'spain', 'es', 'italy', 'it', 'netherlands', 'nl', 'belgium', 'be', 'switzerland', 'ch', 'austria', 'at', 'sweden', 'se', 'norway', 'no', 'denmark', 'dk', 'finland', 'fi', 'ireland', 'ie', 'portugal', 'pt', 'greece', 'gr', 'poland', 'pl', 'czech', 'cz', 'slovakia', 'sk', 'hungary', 'hu', 'romania', 'ro', 'bulgaria', 'bg', 'russia', 'ru', 'turkey', 'tr', 'ukraine', 'ua', 'israel', 'il', 'uae', 'ae', 'saudi', 'sa', 'egypt', 'eg', 'south africa', 'za', 'nigeria', 'ng']
    latam_indicators = ['latin america', 'latam', 'south america', 'central america', 'brazil', 'br', 'argentina', 'ar', 'chile', 'cl', 'colombia', 'co', 'peru', 'pe', 'ecuador', 'ec', 'venezuela', 've', 'uruguay', 'uy', 'paraguay', 'py', 'bolivia', 'bo', 'costa rica', 'cr', 'panama', 'pa', 'guatemala', 'gt', 'honduras', 'hn', 'el salvador', 'sv', 'nicaragua', 'ni']
    apac_indicators = ['asia pacific', 'apac', 'asia', 'pacific', 'australia', 'au', 'new zealand', 'nz', 'japan', 'jp', 'china', 'cn', 'india', 'in', 'singapore', 'sg', 'malaysia', 'my', 'thailand', 'th', 'vietnam', 'vn', 'indonesia', 'id', 'philippines', 'ph', 'south korea', 'kr', 'taiwan', 'tw', 'hong kong', 'hk']
    
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
        
        result = conn.execute("""
            WITH split_sources AS (
                SELECT 
                    host,
                    UNNEST(string_split(source_tables, ',')) as source_table,
                    source_tables as original_source_tables
                FROM universal_cmdb 
                WHERE source_tables IS NOT NULL 
                AND source_tables != ''
            ),
            cleaned_sources AS (
                SELECT 
                    host,
                    TRIM(source_table) as clean_source_table,
                    original_source_tables
                FROM split_sources
                WHERE TRIM(source_table) != ''
            )
            SELECT 
                clean_source_table,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
            FROM cleaned_sources
            GROUP BY clean_source_table
            ORDER BY frequency DESC
        """).fetchall()
        
        total_mentions = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE source_tables IS NOT NULL").fetchone()[0]
        unique_sources = len(result)
        
        data = {}
        detailed_data = []
        
        for row in result:
            source_name, frequency, unique_hosts, percentage = row
            data[source_name] = frequency
            detailed_data.append({
                'source': source_name,
                'frequency': frequency,
                'unique_hosts': unique_hosts,
                'percentage': percentage
            })
        
        conn.close()
        
        return jsonify({
            'data': data,
            'detailed_data': detailed_data,
            'total_sources': unique_sources,
            'total_mentions': sum(data.values()),
            'unique_hosts_with_sources': total_mentions
        })
    except Exception as e:
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
                region,
                country,
                infrastructure_type
            FROM universal_cmdb 
            WHERE source_tables LIKE ?
            LIMIT 100
        """, [f'%{source}%']).fetchall()
        
        conn.close()
        
        hosts_with_source = []
        for row in result:
            hosts_with_source.append({
                'host': row[0],
                'source_tables': row[1],
                'region': row[2],
                'country': row[3],
                'infrastructure_type': row[4]
            })
        
        return jsonify({'hosts': hosts_with_source})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/domain_metrics')
def domain_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH domain_analysis AS (
                SELECT 
                    host,
                    domain,
                    CASE 
                        WHEN domain LIKE '%1dc%' THEN '1dc'
                        WHEN domain LIKE '%fead%' THEN 'fead'
                        ELSE 'other'
                    END as domain_type
                FROM universal_cmdb 
                WHERE domain IS NOT NULL AND domain != ''
            )
            SELECT 
                domain_type,
                COUNT(*) as count,
                COUNT(DISTINCT host) as unique_hosts,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
            FROM domain_analysis
            GROUP BY domain_type
            ORDER BY count DESC
        """).fetchall()
        
        domain_breakdown = conn.execute("""
            WITH split_domains AS (
                SELECT 
                    host,
                    UNNEST(string_split(domain, '|')) as individual_domain
                FROM universal_cmdb 
                WHERE domain IS NOT NULL AND domain != ''
            )
            SELECT 
                TRIM(individual_domain) as domain_name,
                COUNT(*) as frequency
            FROM split_domains
            WHERE TRIM(individual_domain) != ''
            GROUP BY TRIM(individual_domain)
            ORDER BY frequency DESC
            LIMIT 20
        """).fetchall()
        
        conn.close()
        
        domain_analysis = {}
        domain_details = {}
        
        for row in result:
            domain_type, count, unique_hosts, percentage = row
            domain_analysis[domain_type] = count
            domain_details[domain_type] = {
                'count': count,
                'unique_hosts': unique_hosts,
                'percentage': percentage
            }
        
        top_domains = {}
        for row in domain_breakdown:
            domain_name, frequency = row
            top_domains[domain_name] = frequency
        
        return jsonify({
            'domain_analysis': domain_analysis,
            'domain_details': domain_details,
            'top_domains': top_domains,
            'total_analyzed': sum(domain_analysis.values())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/infrastructure_type')
def infrastructure_type_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH split_infrastructure AS (
                SELECT 
                    host,
                    UNNEST(string_split(infrastructure_type, '|')) as infra_type
                FROM universal_cmdb 
                WHERE infrastructure_type IS NOT NULL AND infrastructure_type != ''
            )
            SELECT 
                TRIM(infra_type) as infrastructure_type,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
            FROM split_infrastructure
            WHERE TRIM(infra_type) != ''
            GROUP BY TRIM(infra_type)
            ORDER BY frequency DESC
        """).fetchall()
        
        conn.close()
        
        infrastructure_matrix = {}
        detailed_data = []
        
        for row in result:
            infra_type, frequency, unique_hosts, percentage = row
            infrastructure_matrix[infra_type] = frequency
            detailed_data.append({
                'type': infra_type,
                'frequency': frequency,
                'unique_hosts': unique_hosts,
                'percentage': percentage
            })
        
        return jsonify({
            'infrastructure_matrix': infrastructure_matrix,
            'detailed_data': detailed_data,
            'total_types': len(infrastructure_matrix)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/region_metrics')
def region_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH split_regions AS (
                SELECT 
                    host,
                    UNNEST(string_split(region, '|')) as region_part
                FROM universal_cmdb 
                WHERE region IS NOT NULL AND region != ''
            )
            SELECT 
                TRIM(LOWER(region_part)) as normalized_region,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts
            FROM split_regions
            WHERE TRIM(region_part) != ''
            GROUP BY TRIM(LOWER(region_part))
        """).fetchall()
        
        conn.close()
        
        region_counter = {'north america': 0, 'emea': 0, 'latam': 0, 'apac': 0}
        region_details = {'north america': [], 'emea': [], 'latam': [], 'apac': []}
        
        for row in result:
            region_part, frequency, unique_hosts = row
            normalized = normalize_region(region_part)
            if normalized in region_counter:
                region_counter[normalized] += frequency
                region_details[normalized].append({
                    'original': region_part,
                    'frequency': frequency,
                    'unique_hosts': unique_hosts
                })
        
        return jsonify({
            'global_surveillance': region_counter,
            'region_details': region_details,
            'total_coverage': sum(region_counter.values())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/country_metrics')
def country_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH split_countries AS (
                SELECT 
                    host,
                    UNNEST(string_split(country, '|')) as country_part
                FROM universal_cmdb 
                WHERE country IS NOT NULL AND country != ''
            )
            SELECT 
                TRIM(LOWER(country_part)) as country_name,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts
            FROM split_countries
            WHERE TRIM(country_part) != ''
            GROUP BY TRIM(LOWER(country_part))
            ORDER BY frequency DESC
        """).fetchall()
        
        conn.close()
        
        country_counter = Counter()
        detailed_data = []
        
        for row in result:
            country_name, frequency, unique_hosts = row
            normalized = normalize_country(country_name)
            country_counter[normalized] += frequency
            detailed_data.append({
                'original': country_name,
                'normalized': normalized,
                'frequency': frequency,
                'unique_hosts': unique_hosts
            })
        
        return jsonify({
            'global_intelligence': dict(country_counter.most_common()),
            'detailed_data': detailed_data,
            'monitored_nations': len(country_counter)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data_center_metrics')
def data_center_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH first_word_extraction AS (
                SELECT 
                    host,
                    data_center,
                    CASE 
                        WHEN data_center IS NOT NULL AND data_center != '' 
                        THEN TRIM(string_split(data_center, ' ')[1])
                        ELSE NULL
                    END as first_word
                FROM universal_cmdb 
                WHERE data_center IS NOT NULL AND data_center != ''
            )
            SELECT 
                first_word,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
            FROM first_word_extraction
            WHERE first_word IS NOT NULL AND first_word != ''
            GROUP BY first_word
            ORDER BY frequency DESC
        """).fetchall()
        
        conn.close()
        
        facility_intelligence = {}
        detailed_data = []
        
        for row in result:
            first_word, frequency, unique_hosts, percentage = row
            facility_intelligence[first_word] = frequency
            detailed_data.append({
                'facility': first_word,
                'frequency': frequency,
                'unique_hosts': unique_hosts,
                'percentage': percentage
            })
        
        return jsonify({
            'facility_intelligence': facility_intelligence,
            'detailed_data': detailed_data,
            'total_facilities': len(facility_intelligence)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cloud_region_metrics')
def cloud_region_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH split_cloud_regions AS (
                SELECT 
                    host,
                    UNNEST(string_split(cloud_region, '|')) as region_part
                FROM universal_cmdb 
                WHERE cloud_region IS NOT NULL AND cloud_region != ''
            )
            SELECT 
                TRIM(region_part) as cloud_region,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts
            FROM split_cloud_regions
            WHERE TRIM(region_part) != ''
            GROUP BY TRIM(region_part)
            ORDER BY frequency DESC
        """).fetchall()
        
        conn.close()
        
        cloud_matrix = []
        detailed_data = []
        
        for row in result:
            cloud_region, frequency, unique_hosts = row
            cloud_matrix.append(cloud_region)
            detailed_data.append({
                'region': cloud_region,
                'frequency': frequency,
                'unique_hosts': unique_hosts
            })
        
        return jsonify({
            'cloud_matrix': cloud_matrix,
            'detailed_data': detailed_data,
            'unique_regions': len(cloud_matrix)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/class_metrics')
def class_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH class_extraction AS (
                SELECT 
                    host,
                    class,
                    regexp_extract_all(LOWER(class), 'class\\s+(\\d+)') as class_numbers
                FROM universal_cmdb 
                WHERE class IS NOT NULL AND class != ''
                AND class ILIKE '%class%'
            )
            SELECT 
                'class ' || UNNEST(class_numbers) as class_type,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts
            FROM class_extraction
            WHERE len(class_numbers) > 0
            GROUP BY UNNEST(class_numbers)
            ORDER BY UNNEST(class_numbers)
        """).fetchall()
        
        conn.close()
        
        classification_matrix = {}
        detailed_data = []
        
        for row in result:
            class_type, frequency, unique_hosts = row
            classification_matrix[class_type] = frequency
            detailed_data.append({
                'class': class_type,
                'frequency': frequency,
                'unique_hosts': unique_hosts
            })
        
        return jsonify({
            'classification_matrix': classification_matrix,
            'detailed_data': detailed_data,
            'total_classes': len(classification_matrix)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_classification_metrics')
def system_classification_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH split_classifications AS (
                SELECT 
                    host,
                    UNNEST(string_split(system_classification, '|')) as classification
                FROM universal_cmdb 
                WHERE system_classification IS NOT NULL AND system_classification != ''
            )
            SELECT 
                TRIM(classification) as system_type,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
            FROM split_classifications
            WHERE TRIM(classification) != ''
            GROUP BY TRIM(classification)
            ORDER BY frequency DESC
        """).fetchall()
        
        conn.close()
        
        system_matrix = {}
        detailed_data = []
        
        for row in result:
            system_type, frequency, unique_hosts, percentage = row
            system_matrix[system_type] = frequency
            detailed_data.append({
                'system': system_type,
                'frequency': frequency,
                'unique_hosts': unique_hosts,
                'percentage': percentage
            })
        
        return jsonify({
            'system_matrix': system_matrix,
            'detailed_data': detailed_data[:50],
            'total_systems': len(system_matrix)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business_unit_metrics')
def business_unit_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH split_units AS (
                SELECT 
                    host,
                    regexp_split_to_table(business_unit, '[,|]') as unit_part
                FROM universal_cmdb 
                WHERE business_unit IS NOT NULL AND business_unit != ''
            )
            SELECT 
                TRIM(unit_part) as business_unit,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
            FROM split_units
            WHERE TRIM(unit_part) != ''
            GROUP BY TRIM(unit_part)
            ORDER BY frequency DESC
        """).fetchall()
        
        conn.close()
        
        business_intelligence = {}
        detailed_data = []
        
        for row in result:
            business_unit, frequency, unique_hosts, percentage = row
            business_intelligence[business_unit] = frequency
            detailed_data.append({
                'unit': business_unit,
                'frequency': frequency,
                'unique_hosts': unique_hosts,
                'percentage': percentage
            })
        
        return jsonify({
            'business_intelligence': business_intelligence,
            'detailed_data': detailed_data,
            'operational_units': len(business_intelligence)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cio_metrics')
def cio_metrics():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
            WITH split_cio AS (
                SELECT 
                    host,
                    UNNEST(string_split(cio, '|')) as cio_part
                FROM universal_cmdb 
                WHERE cio IS NOT NULL AND cio != ''
            ),
            filtered_cio AS (
                SELECT 
                    host,
                    TRIM(cio_part) as cio_value
                FROM split_cio
                WHERE TRIM(cio_part) != '' 
                AND TRIM(cio_part) ~ '[a-zA-Z]+'
                AND NOT (TRIM(cio_part) ~ '^[0-9]+$')
            )
            SELECT 
                cio_value,
                COUNT(*) as frequency,
                COUNT(DISTINCT host) as unique_hosts
            FROM filtered_cio
            GROUP BY cio_value
            ORDER BY frequency DESC
        """).fetchall()
        
        conn.close()
        
        operative_intelligence = {}
        detailed_data = []
        
        for row in result:
            cio_value, frequency, unique_hosts = row
            operative_intelligence[cio_value] = frequency
            detailed_data.append({
                'cio': cio_value,
                'frequency': frequency,
                'unique_hosts': unique_hosts
            })
        
        return jsonify({
            'operative_intelligence': operative_intelligence,
            'detailed_data': detailed_data,
            'classified_personnel': len(operative_intelligence)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tanium_coverage')
def tanium_coverage():
    try:
        conn = get_db_connection()
        
        tanium_count = conn.execute("""
            SELECT COUNT(*) 
            FROM universal_cmdb 
            WHERE tanium_coverage ILIKE '%tanium%'
        """).fetchone()[0]
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        coverage_details = conn.execute("""
            SELECT 
                CASE 
                    WHEN tanium_coverage ILIKE '%tanium%' THEN 'deployed'
                    ELSE 'not_deployed'
                END as status,
                COUNT(*) as count,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
            FROM universal_cmdb
            GROUP BY CASE WHEN tanium_coverage ILIKE '%tanium%' THEN 'deployed' ELSE 'not_deployed' END
        """).fetchall()
        
        coverage_by_region = conn.execute("""
            WITH region_tanium AS (
                SELECT 
                    COALESCE(region, 'unknown') as region,
                    CASE WHEN tanium_coverage ILIKE '%tanium%' THEN 1 ELSE 0 END as has_tanium
                FROM universal_cmdb
            )
            SELECT 
                region,
                COUNT(*) as total_hosts,
                SUM(has_tanium) as tanium_deployed,
                ROUND((SUM(has_tanium) * 100.0 / COUNT(*)), 2) as coverage_percentage
            FROM region_tanium
            GROUP BY region
            ORDER BY coverage_percentage DESC
        """).fetchall()
        
        conn.close()
        
        coverage_percentage = (tanium_count / total_count * 100) if total_count > 0 else 0
        
        status_breakdown = {}
        for row in coverage_details:
            status, count, percentage = row
            status_breakdown[status] = {'count': count, 'percentage': percentage}
        
        regional_coverage = {}
        for row in coverage_by_region:
            region, total_hosts, deployed, coverage_pct = row
            regional_coverage[region] = {
                'total_hosts': total_hosts,
                'deployed': deployed,
                'coverage_percentage': coverage_pct
            }
        
        return jsonify({
            'tanium_deployed': tanium_count,
            'total_assets': total_count,
            'coverage_percentage': round(coverage_percentage, 2),
            'status_breakdown': status_breakdown,
            'regional_coverage': regional_coverage
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cmdb_presence')
def cmdb_presence():
    try:
        conn = get_db_connection()
        
        yes_count = conn.execute("""
            SELECT COUNT(*) 
            FROM universal_cmdb 
            WHERE present_in_cmdb ILIKE '%yes%'
        """).fetchone()[0]
        
        total_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        presence_details = conn.execute("""
            SELECT 
                CASE 
                    WHEN present_in_cmdb ILIKE '%yes%' THEN 'registered'
                    ELSE 'not_registered'
                END as status,
                COUNT(*) as count,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()), 2) as percentage
            FROM universal_cmdb
            GROUP BY CASE WHEN present_in_cmdb ILIKE '%yes%' THEN 'registered' ELSE 'not_registered' END
        """).fetchall()
        
        presence_by_region = conn.execute("""
            WITH region_cmdb AS (
                SELECT 
                    COALESCE(region, 'unknown') as region,
                    CASE WHEN present_in_cmdb ILIKE '%yes%' THEN 1 ELSE 0 END as in_cmdb
                FROM universal_cmdb
            )
            SELECT 
                region,
                COUNT(*) as total_hosts,
                SUM(in_cmdb) as registered,
                ROUND((SUM(in_cmdb) * 100.0 / COUNT(*)), 2) as registration_percentage
            FROM region_cmdb
            GROUP BY region
            ORDER BY registration_percentage DESC
        """).fetchall()
        
        conn.close()
        
        registration_rate = (yes_count / total_count * 100) if total_count > 0 else 0
        
        status_breakdown = {}
        for row in presence_details:
            status, count, percentage = row
            status_breakdown[status] = {'count': count, 'percentage': percentage}
        
        regional_presence = {}
        for row in presence_by_region:
            region, total_hosts, registered, reg_pct = row
            regional_presence[region] = {
                'total_hosts': total_hosts,
                'registered': registered,
                'registration_percentage': reg_pct
            }
        
        return jsonify({
            'cmdb_registered': yes_count,
            'total_assets': total_count,
            'registration_rate': round(registration_rate, 2),
            'status_breakdown': status_breakdown,
            'regional_presence': regional_presence
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
            WHERE host ILIKE ? 
            ORDER BY host 
            LIMIT 100
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
        
        return jsonify({'hosts': hosts, 'count': len(hosts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)