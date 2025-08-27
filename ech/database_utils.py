import duckdb
import os
import logging
import re
from collections import Counter, defaultdict

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
                conn = duckdb.connect(db_path, read_only=True)
                tables = conn.execute("SHOW TABLES").fetchall()
                if any('universal_cmdb' in str(table).lower() for table in tables):
                    return conn
                else:
                    conn.close()
        except Exception as e:
            logger.error(f"Failed to connect to {db_path}: {e}")
            continue
    
    raise Exception("Database file 'universal_cmdb.db' not found in any expected location")

def verify_table_structure(conn):
    try:
        result = conn.execute("DESCRIBE universal_cmdb").fetchall()
        columns = [row[0] for row in result]
        row_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        return columns, row_count
    except Exception as e:
        logger.error(f"Error verifying table structure: {e}")
        return [], 0

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

def calculate_threat_level(percentage):
    if percentage >= 80:
        return {'level': 'CRITICAL', 'color': '#ff0066', 'priority': 1}
    elif percentage >= 60:
        return {'level': 'HIGH', 'color': '#ff9900', 'priority': 2}
    elif percentage >= 40:
        return {'level': 'MEDIUM', 'color': '#ffcc00', 'priority': 3}
    else:
        return {'level': 'LOW', 'color': '#00ff85', 'priority': 4}

def calculate_security_score(cmdb_present, tanium_deployed, logging_enabled):
    score = 0
    if cmdb_present:
        score += 33
    if tanium_deployed:
        score += 33
    if logging_enabled:
        score += 34
    return score

def get_data_quality_stats(conn):
    try:
        result = conn.execute("""
            SELECT 
                AVG(CAST(data_quality_score AS FLOAT)) as avg_quality,
                MIN(CAST(data_quality_score AS FLOAT)) as min_quality,
                MAX(CAST(data_quality_score AS FLOAT)) as max_quality,
                COUNT(*) as total_records
            FROM universal_cmdb 
            WHERE data_quality_score IS NOT NULL 
            AND data_quality_score != '' 
            AND data_quality_score != 'null'
        """).fetchone()
        
        return {
            'average_quality': round(result[0] if result[0] else 0, 2),
            'min_quality': round(result[1] if result[1] else 0, 2),
            'max_quality': round(result[2] if result[2] else 0, 2),
            'total_records': result[3] if result[3] else 0
        }
    except Exception as e:
        logger.error(f"Error calculating data quality stats: {e}")
        return {'average_quality': 0, 'min_quality': 0, 'max_quality': 0, 'total_records': 0}