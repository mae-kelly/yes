# /server/app.py
import duckdb
from flask import Flask, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return duckdb.connect('universal_cmdb.db')

def parse_multi_values(value, delimiters=['|', ',']):
    if not value or value == 'null':
        return []
    for delimiter in delimiters:
        if delimiter in str(value):
            return [v.strip() for v in str(value).split(delimiter) if v.strip()]
    return [str(value).strip()]

def extract_class_numbers(value):
    if not value or value == 'null':
        return []
    classes = []
    for part in parse_multi_values(value):
        matches = re.findall(r'class\s*(\d+)', part.lower())
        classes.extend([int(match) for match in matches])
    return classes

def standardize_region(region):
    if not region:
        return 'unknown'
    region_lower = str(region).lower()
    if any(term in region_lower for term in ['north america', 'na', 'us', 'united states', 'canada']):
        return 'North America'
    elif any(term in region_lower for term in ['latam', 'latin america', 'south america', 'brazil', 'mexico']):
        return 'LATAM'
    elif any(term in region_lower for term in ['emea', 'europe', 'middle east', 'africa']):
        return 'EMEA'
    elif any(term in region_lower for term in ['apac', 'asia', 'pacific', 'australia', 'japan']):
        return 'APAC'
    return region

def calculate_coverage_metrics(total, splunk, cmdb, crowdstrike, tanium=0, dlp=0):
    if total == 0:
        return {'total': 0, 'splunk_coverage': 0, 'cmdb_coverage': 0, 'edr_coverage': 0, 'tanium_coverage': 0, 'dlp_coverage': 0, 'overall_coverage': 0}
    
    splunk_pct = round((splunk / total) * 100, 2)
    cmdb_pct = round((cmdb / total) * 100, 2)
    edr_pct = round((crowdstrike / total) * 100, 2)
    tanium_pct = round((tanium / total) * 100, 2)
    dlp_pct = round((dlp / total) * 100, 2)
    overall_pct = round((splunk_pct + cmdb_pct + edr_pct) / 3, 2)
    
    return {
        'total': total,
        'splunk_coverage': splunk_pct,
        'cmdb_coverage': cmdb_pct,
        'edr_coverage': edr_pct,
        'tanium_coverage': tanium_pct,
        'dlp_coverage': dlp_pct,
        'overall_coverage': overall_pct
    }

@app.route('/api/global-view')
def global_view():
    conn = get_db_connection()
    
    total_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
    
    splunk_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_splunk = 'yes'").fetchone()[0]
    cmdb_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_cmdb = 'yes'").fetchone()[0]
    crowdstrike_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike agent%'").fetchone()[0]
    tanium_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%'").fetchone()[0]
    apm_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE apm LIKE '%apm%'").fetchone()[0]
    chronicle_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_chronicle = 'yes'").fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_hosts': total_hosts,
        'coverage': {
            'splunk': {'count': splunk_count, 'percentage': round((splunk_count / total_hosts) * 100, 2)},
            'chronicle': {'count': chronicle_count, 'percentage': round((chronicle_count / total_hosts) * 100, 2)},
            'cmdb': {'count': cmdb_count, 'percentage': round((cmdb_count / total_hosts) * 100, 2)},
            'crowdstrike': {'count': crowdstrike_count, 'percentage': round((crowdstrike_count / total_hosts) * 100, 2)},
            'tanium': {'count': tanium_count, 'percentage': round((tanium_count / total_hosts) * 100, 2)},
            'apm': {'count': apm_count, 'percentage': round((apm_count / total_hosts) * 100, 2)}
        }
    })

@app.route('/api/domain-visibility')
def domain_visibility():
    conn = get_db_connection()
    
    dc1_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%'").fetchone()[0]
    fead_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%'").fetchone()[0]
    
    dc1_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%' AND logging_in_splunk = 'yes'").fetchone()[0]
    dc1_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%' AND present_in_cmdb = 'yes'").fetchone()[0]
    dc1_crowdstrike = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%' AND edr_coverage LIKE '%crowdstrike agent%'").fetchone()[0]
    dc1_tanium = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%' AND tanium_coverage LIKE '%tanium%'").fetchone()[0]
    
    fead_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%' AND logging_in_splunk = 'yes'").fetchone()[0]
    fead_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%' AND present_in_cmdb = 'yes'").fetchone()[0]
    fead_crowdstrike = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%' AND edr_coverage LIKE '%crowdstrike agent%'").fetchone()[0]
    fead_tanium = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%' AND tanium_coverage LIKE '%tanium%'").fetchone()[0]
    
    all_domains = conn.execute("SELECT domain FROM universal_cmdb WHERE domain IS NOT NULL").fetchall()
    domain_stats = {}
    
    for row in all_domains:
        domains = parse_multi_values(row[0])
        for domain in domains:
            if domain not in domain_stats:
                domain_stats[domain] = 0
            domain_stats[domain] += 1
    
    conn.close()
    
    return jsonify({
        '1dc': calculate_coverage_metrics(dc1_total, dc1_splunk, dc1_cmdb, dc1_crowdstrike, dc1_tanium),
        'fead': calculate_coverage_metrics(fead_total, fead_splunk, fead_cmdb, fead_crowdstrike, fead_tanium),
        'all_domains': sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)[:20]
    })

@app.route('/api/regional-country-view')
def regional_country_view():
    conn = get_db_connection()
    
    rows = conn.execute("""
        SELECT region, country, logging_in_splunk, present_in_cmdb, 
               edr_coverage, tanium_coverage 
        FROM universal_cmdb
    """).fetchall()
    
    region_stats = {}
    country_stats = {}
    
    for row in rows:
        regions = parse_multi_values(row[0]) if row[0] else ['unknown']
        countries = parse_multi_values(row[1]) if row[1] else ['unknown']
        
        splunk = row[2] == 'yes'
        cmdb = row[3] == 'yes'
        crowdstrike = 'crowdstrike agent' in str(row[4]).lower() if row[4] else False
        tanium = 'tanium' in str(row[5]).lower() if row[5] else False
        
        for region in regions:
            std_region = standardize_region(region)
            if std_region not in region_stats:
                region_stats[std_region] = {'total': 0, 'splunk': 0, 'cmdb': 0, 'crowdstrike': 0, 'tanium': 0}
            region_stats[std_region]['total'] += 1
            if splunk: region_stats[std_region]['splunk'] += 1
            if cmdb: region_stats[std_region]['cmdb'] += 1
            if crowdstrike: region_stats[std_region]['crowdstrike'] += 1
            if tanium: region_stats[std_region]['tanium'] += 1
            
        for country in countries:
            if country not in country_stats:
                country_stats[country] = {'total': 0, 'splunk': 0, 'cmdb': 0, 'crowdstrike': 0, 'tanium': 0}
            country_stats[country]['total'] += 1
            if splunk: country_stats[country]['splunk'] += 1
            if cmdb: country_stats[country]['cmdb'] += 1
            if crowdstrike: country_stats[country]['crowdstrike'] += 1
            if tanium: country_stats[country]['tanium'] += 1
    
    for region in region_stats:
        stats = region_stats[region]
        region_stats[region] = calculate_coverage_metrics(stats['total'], stats['splunk'], stats['cmdb'], stats['crowdstrike'], stats['tanium'])
    
    for country in country_stats:
        stats = country_stats[country]
        country_stats[country] = calculate_coverage_metrics(stats['total'], stats['splunk'], stats['cmdb'], stats['crowdstrike'], stats['tanium'])
    
    conn.close()
    
    return jsonify({
        'regions': region_stats,
        'countries': dict(sorted(country_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:15])
    })

@app.route('/api/infrastructure-type')
def infrastructure_type():
    conn = get_db_connection()
    
    rows = conn.execute("""
        SELECT infrastructure_type, logging_in_splunk, present_in_cmdb, 
               edr_coverage, tanium_coverage 
        FROM universal_cmdb 
        WHERE infrastructure_type IS NOT NULL
    """).fetchall()
    
    infra_stats = {}
    
    for row in rows:
        types = parse_multi_values(row[0])
        splunk = row[1] == 'yes'
        cmdb = row[2] == 'yes'
        crowdstrike = 'crowdstrike agent' in str(row[3]).lower() if row[3] else False
        tanium = 'tanium' in str(row[4]).lower() if row[4] else False
        
        for infra_type in types:
            if infra_type not in infra_stats:
                infra_stats[infra_type] = {'total': 0, 'splunk': 0, 'cmdb': 0, 'crowdstrike': 0, 'tanium': 0}
            infra_stats[infra_type]['total'] += 1
            if splunk: infra_stats[infra_type]['splunk'] += 1
            if cmdb: infra_stats[infra_type]['cmdb'] += 1
            if crowdstrike: infra_stats[infra_type]['crowdstrike'] += 1
            if tanium: infra_stats[infra_type]['tanium'] += 1
    
    for infra_type in infra_stats:
        stats = infra_stats[infra_type]
        infra_stats[infra_type] = calculate_coverage_metrics(stats['total'], stats['splunk'], stats['cmdb'], stats['crowdstrike'], stats['tanium'])
    
    conn.close()
    
    return jsonify(infra_stats)

@app.route('/api/bu-application-view')
def bu_application_view():
    conn = get_db_connection()
    
    rows = conn.execute("""
        SELECT cio, business_unit, apm, logging_in_splunk, present_in_cmdb, 
               edr_coverage, tanium_coverage 
        FROM universal_cmdb
    """).fetchall()
    
    cio_stats = {}
    bu_stats = {}
    apm_stats = {'total': 0, 'splunk': 0, 'cmdb': 0, 'crowdstrike': 0, 'tanium': 0}
    
    for row in rows:
        splunk = row[3] == 'yes'
        cmdb = row[4] == 'yes'
        crowdstrike = 'crowdstrike agent' in str(row[5]).lower() if row[5] else False
        tanium = 'tanium' in str(row[6]).lower() if row[6] else False
        
        if row[0] and row[0] != 'null' and str(row[0]).replace(' ', '').isalpha():
            cios = parse_multi_values(row[0])
            for cio in cios:
                if cio not in cio_stats:
                    cio_stats[cio] = {'total': 0, 'splunk': 0, 'cmdb': 0, 'crowdstrike': 0, 'tanium': 0}
                cio_stats[cio]['total'] += 1
                if splunk: cio_stats[cio]['splunk'] += 1
                if cmdb: cio_stats[cio]['cmdb'] += 1
                if crowdstrike: cio_stats[cio]['crowdstrike'] += 1
                if tanium: cio_stats[cio]['tanium'] += 1
        
        if row[1] and row[1] != 'null':
            bus = parse_multi_values(row[1], [','])
            for bu in bus:
                if bu not in bu_stats:
                    bu_stats[bu] = {'total': 0, 'splunk': 0, 'cmdb': 0, 'crowdstrike': 0, 'tanium': 0}
                bu_stats[bu]['total'] += 1
                if splunk: bu_stats[bu]['splunk'] += 1
                if cmdb: bu_stats[bu]['cmdb'] += 1
                if crowdstrike: bu_stats[bu]['crowdstrike'] += 1
                if tanium: bu_stats[bu]['tanium'] += 1
        
        if row[2] and 'apm' in str(row[2]).lower():
            apm_stats['total'] += 1
            if splunk: apm_stats['splunk'] += 1
            if cmdb: apm_stats['cmdb'] += 1
            if crowdstrike: apm_stats['crowdstrike'] += 1
            if tanium: apm_stats['tanium'] += 1
    
    for cio in cio_stats:
        stats = cio_stats[cio]
        cio_stats[cio] = calculate_coverage_metrics(stats['total'], stats['splunk'], stats['cmdb'], stats['crowdstrike'], stats['tanium'])
    
    for bu in bu_stats:
        stats = bu_stats[bu]
        bu_stats[bu] = calculate_coverage_metrics(stats['total'], stats['splunk'], stats['cmdb'], stats['crowdstrike'], stats['tanium'])
    
    apm_coverage = calculate_coverage_metrics(apm_stats['total'], apm_stats['splunk'], apm_stats['cmdb'], apm_stats['crowdstrike'], apm_stats['tanium'])
    
    conn.close()
    
    return jsonify({
        'cio': dict(sorted(cio_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:15]),
        'business_units': dict(sorted(bu_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:20]),
        'apm_coverage': apm_coverage
    })

@app.route('/api/system-classification')
def system_classification():
    conn = get_db_connection()
    
    rows = conn.execute("""
        SELECT system_classification, class, logging_in_splunk, present_in_cmdb, 
               edr_coverage, tanium_coverage 
        FROM universal_cmdb
    """).fetchall()
    
    system_stats = {}
    class_stats = {}
    
    for row in rows:
        splunk = row[2] == 'yes'
        cmdb = row[3] == 'yes'
        crowdstrike = 'crowdstrike agent' in str(row[4]).lower() if row[4] else False
        tanium = 'tanium' in str(row[5]).lower() if row[5] else False
        
        if row[0] and row[0] != 'null':
            systems = parse_multi_values(row[0], ['|'])
            for system in systems:
                if system not in system_stats:
                    system_stats[system] = {'total': 0, 'splunk': 0, 'cmdb': 0, 'crowdstrike': 0, 'tanium': 0}
                system_stats[system]['total'] += 1
                if splunk: system_stats[system]['splunk'] += 1
                if cmdb: system_stats[system]['cmdb'] += 1
                if crowdstrike: system_stats[system]['crowdstrike'] += 1
                if tanium: system_stats[system]['tanium'] += 1
        
        if row[1] and row[1] != 'null':
            classes = extract_class_numbers(row[1])
            for class_num in classes:
                if class_num not in class_stats:
                    class_stats[class_num] = {'total': 0, 'splunk': 0, 'cmdb': 0, 'crowdstrike': 0, 'tanium': 0}
                class_stats[class_num]['total'] += 1
                if splunk: class_stats[class_num]['splunk'] += 1
                if cmdb: class_stats[class_num]['cmdb'] += 1
                if crowdstrike: class_stats[class_num]['crowdstrike'] += 1
                if tanium: class_stats[class_num]['tanium'] += 1
    
    for system in system_stats:
        stats = system_stats[system]
        system_stats[system] = calculate_coverage_metrics(stats['total'], stats['splunk'], stats['cmdb'], stats['crowdstrike'], stats['tanium'])
    
    for class_num in class_stats:
        stats = class_stats[class_num]
        class_stats[class_num] = calculate_coverage_metrics(stats['total'], stats['splunk'], stats['cmdb'], stats['crowdstrike'], stats['tanium'])
    
    conn.close()
    
    return jsonify({
        'system_classifications': dict(sorted(system_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:20]),
        'classes': dict(sorted(class_stats.items(), key=lambda x: x[0]))
    })

@app.route('/api/security-control-coverage')
def security_control_coverage():
    conn = get_db_connection()
    
    total_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
    
    edr_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike agent%'").fetchone()[0]
    tanium_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%'").fetchone()[0]
    dlp_count = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE dlp_agent_coverage LIKE '%dlp agent%'").fetchone()[0]
    
    tanium_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%' AND present_in_cmdb = 'yes'").fetchone()[0]
    tanium_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%' AND logging_in_splunk = 'yes'").fetchone()[0]
    tanium_crowdstrike = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%' AND edr_coverage LIKE '%crowdstrike agent%'").fetchone()[0]
    
    edr_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike agent%' AND present_in_cmdb = 'yes'").fetchone()[0]
    edr_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike agent%' AND logging_in_splunk = 'yes'").fetchone()[0]
    
    triple_coverage = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%' AND edr_coverage LIKE '%crowdstrike agent%' AND logging_in_splunk = 'yes'").fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_hosts': total_hosts,
        'coverage': {
            'edr': {'count': edr_count, 'percentage': round((edr_count / total_hosts) * 100, 2)},
            'tanium': {'count': tanium_count, 'percentage': round((tanium_count / total_hosts) * 100, 2)},
            'dlp': {'count': dlp_count, 'percentage': round((dlp_count / total_hosts) * 100, 2)}
        },
        'overlaps': {
            'tanium_cmdb': {'count': tanium_cmdb, 'percentage': round((tanium_cmdb / tanium_count) * 100, 2) if tanium_count > 0 else 0},
            'tanium_splunk': {'count': tanium_splunk, 'percentage': round((tanium_splunk / tanium_count) * 100, 2) if tanium_count > 0 else 0},
            'tanium_crowdstrike': {'count': tanium_crowdstrike, 'percentage': round((tanium_crowdstrike / tanium_count) * 100, 2) if tanium_count > 0 else 0},
            'edr_cmdb': {'count': edr_cmdb, 'percentage': round((edr_cmdb / edr_count) * 100, 2) if edr_count > 0 else 0},
            'edr_splunk': {'count': edr_splunk, 'percentage': round((edr_splunk / edr_count) * 100, 2) if edr_count > 0 else 0},
            'triple_coverage': {'count': triple_coverage, 'percentage': round((triple_coverage / total_hosts) * 100, 2)}
        }
    })

@app.route('/api/logging-compliance-gso-splunk')
def logging_compliance_gso_splunk():
    conn = get_db_connection()
    
    total_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
    splunk_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_splunk = 'yes'").fetchone()[0]
    chronicle_hosts = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_chronicle = 'yes'").fetchone()[0]
    both_platforms = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_splunk = 'yes' AND logging_in_chronicle = 'yes'").fetchone()[0]
    no_logging = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE (logging_in_splunk != 'yes' OR logging_in_splunk IS NULL) AND (logging_in_chronicle != 'yes' OR logging_in_chronicle IS NULL)").fetchone()[0]
    
    compliance_by_region = conn.execute("""
        SELECT region, 
               COUNT(*) as total,
               COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk_count,
               COUNT(CASE WHEN logging_in_chronicle = 'yes' THEN 1 END) as chronicle_count
        FROM universal_cmdb 
        WHERE region IS NOT NULL
        GROUP BY region
    """).fetchall()
    
    region_compliance = {}
    for row in compliance_by_region:
        regions = parse_multi_values(row[0])
        for region in regions:
            std_region = standardize_region(region)
            if std_region not in region_compliance:
                region_compliance[std_region] = {'total': 0, 'splunk': 0, 'chronicle': 0}
            region_compliance[std_region]['total'] += row[1]
            region_compliance[std_region]['splunk'] += row[2]
            region_compliance[std_region]['chronicle'] += row[3]
    
    for region in region_compliance:
        stats = region_compliance[region]
        region_compliance[region] = {
            'total': stats['total'],
            'splunk_percentage': round((stats['splunk'] / stats['total']) * 100, 2) if stats['total'] > 0 else 0,
            'chronicle_percentage': round((stats['chronicle'] / stats['total']) * 100, 2) if stats['total'] > 0 else 0,
            'overall_compliance': round(((stats['splunk'] + stats['chronicle']) / (stats['total'] * 2)) * 100, 2) if stats['total'] > 0 else 0
        }
    
    conn.close()
    
    return jsonify({
        'summary': {
            'total_hosts': total_hosts,
            'splunk_coverage': {'count': splunk_hosts, 'percentage': round((splunk_hosts / total_hosts) * 100, 2)},
            'chronicle_coverage': {'count': chronicle_hosts, 'percentage': round((chronicle_hosts / total_hosts) * 100, 2)},
            'dual_platform': {'count': both_platforms, 'percentage': round((both_platforms / total_hosts) * 100, 2)},
            'no_logging': {'count': no_logging, 'percentage': round((no_logging / total_hosts) * 100, 2)}
        },
        'regional_compliance': region_compliance
    })

@app.route('/api/log-type-priority')
def log_type_priority():
    conn = get_db_connection()
    
    log_types = {
        'Network': ['firewall', 'proxy', 'dns', 'waf', 'ids', 'ips'],
        'Endpoint': ['edr', 'dlp', 'fim', 'av'],
        'Cloud': ['aws', 'azure', 'gcp', 'cloud'],
        'Application': ['web', 'api', 'app'],
        'Identity': ['auth', 'ldap', 'sso', 'iam']
    }
    
    priority_stats = {}
    
    for category, keywords in log_types.items():
        total_count = 0
        splunk_count = 0
        chronicle_count = 0
        
        for keyword in keywords:
            query = f"""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN logging_in_splunk = 'yes' THEN 1 END) as splunk,
                       COUNT(CASE WHEN logging_in_chronicle = 'yes' THEN 1 END) as chronicle
                FROM universal_cmdb 
                WHERE system_classification LIKE '%{keyword}%' 
                   OR infrastructure_type LIKE '%{keyword}%'
                   OR apm LIKE '%{keyword}%'
            """
            result = conn.execute(query).fetchone()
            total_count += result[0]
            splunk_count += result[1]
            chronicle_count += result[2]
        
        priority_stats[category] = {
            'total': total_count,
            'splunk_coverage': round((splunk_count / total_count) * 100, 2) if total_count > 0 else 0,
            'chronicle_coverage': round((chronicle_count / total_count) * 100, 2) if total_count > 0 else 0,
            'overall_priority': round(((splunk_count + chronicle_count) / (total_count * 2)) * 100, 2) if total_count > 0 else 0
        }
    
    conn.close()
    
    return jsonify(priority_stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)