# /server/app.py
import duckdb
from flask import Flask, jsonify
from flask_cors import CORS
import re
from collections import defaultdict

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return duckdb.connect('universal_cmdb.db')

def parse_multi_values(value, delimiters=['|', ',']):
    if not value or value == 'null' or str(value).lower() == 'null':
        return []
    for delimiter in delimiters:
        if delimiter in str(value):
            return [v.strip() for v in str(value).split(delimiter) if v.strip() and v.strip().lower() != 'null']
    return [str(value).strip()] if str(value).strip().lower() != 'null' else []

@app.route('/api/global-view')
def global_view():
    conn = get_db_connection()
    
    total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
    splunk_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_splunk = 'yes'").fetchone()[0]
    cmdb_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_cmdb = 'yes'").fetchone()[0]
    edr_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike%'").fetchone()[0]
    
    infrastructure_breakdown = conn.execute("""
        SELECT 
            infrastructure_type,
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk_count,
            SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb_count,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr_count
        FROM universal_cmdb 
        WHERE infrastructure_type IS NOT NULL AND infrastructure_type != 'null'
        GROUP BY infrastructure_type
        HAVING total > 10
        ORDER BY total DESC
    """).fetchall()
    
    regional_breakdown = conn.execute("""
        SELECT 
            region,
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk_count,
            SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb_count,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr_count
        FROM universal_cmdb 
        WHERE region IS NOT NULL AND region != 'null'
        GROUP BY region
        ORDER BY total DESC
    """).fetchall()
    
    conn.close()
    
    infrastructure_data = {}
    for row in infrastructure_breakdown:
        infrastructure_data[row[0]] = {
            'total': row[1],
            'splunk_coverage': round((row[2] / row[1]) * 100, 1),
            'cmdb_coverage': round((row[3] / row[1]) * 100, 1), 
            'edr_coverage': round((row[4] / row[1]) * 100, 1),
            'overall_coverage': round(((row[2] + row[3] + row[4]) / (3 * row[1])) * 100, 1)
        }
    
    regional_data = {}
    for row in regional_breakdown:
        regional_data[row[0]] = {
            'total': row[1],
            'splunk_coverage': round((row[2] / row[1]) * 100, 1),
            'cmdb_coverage': round((row[3] / row[1]) * 100, 1),
            'edr_coverage': round((row[4] / row[1]) * 100, 1),
            'overall_coverage': round(((row[2] + row[3] + row[4]) / (3 * row[1])) * 100, 1)
        }
    
    return jsonify({
        'global_summary': {
            'total_assets': total_assets,
            'splunk_coverage': round((splunk_total / total_assets) * 100, 1),
            'cmdb_coverage': round((cmdb_total / total_assets) * 100, 1),
            'edr_coverage': round((edr_total / total_assets) * 100, 1),
            'overall_visibility': round(((splunk_total + cmdb_total + edr_total) / (3 * total_assets)) * 100, 1)
        },
        'infrastructure_breakdown': infrastructure_data,
        'regional_breakdown': regional_data
    })

@app.route('/api/infrastructure-type')
def infrastructure_type():
    conn = get_db_connection()
    
    rows = conn.execute("SELECT infrastructure_type FROM universal_cmdb WHERE infrastructure_type IS NOT NULL").fetchall()
    
    infra_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    
    for row in rows:
        types = parse_multi_values(row[0])
        for infra_type in types:
            if infra_type and infra_type != 'null':
                type_data = conn.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk,
                        SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb,
                        SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr
                    FROM universal_cmdb 
                    WHERE infrastructure_type LIKE '%{infra_type}%'
                """).fetchone()
                
                if type_data[0] > 0:
                    infra_stats[infra_type] = {
                        'total': type_data[0],
                        'splunk_coverage': round((type_data[1] / type_data[0]) * 100, 1),
                        'cmdb_coverage': round((type_data[2] / type_data[0]) * 100, 1),
                        'edr_coverage': round((type_data[3] / type_data[0]) * 100, 1),
                        'overall_coverage': round(((type_data[1] + type_data[2] + type_data[3]) / (3 * type_data[0])) * 100, 1)
                    }
    
    conn.close()
    return jsonify(dict(infra_stats))

@app.route('/api/regional-country-view')
def regional_country_view():
    conn = get_db_connection()
    
    regional_data = conn.execute("""
        SELECT 
            region,
            country,
            data_center,
            cloud_region,
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk,
            SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr
        FROM universal_cmdb 
        WHERE region IS NOT NULL OR country IS NOT NULL OR data_center IS NOT NULL OR cloud_region IS NOT NULL
        GROUP BY region, country, data_center, cloud_region
        HAVING total > 5
        ORDER BY total DESC
    """).fetchall()
    
    region_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    country_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    datacenter_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    cloudregion_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    
    for row in regional_data:
        regions = parse_multi_values(row[0]) if row[0] else []
        countries = parse_multi_values(row[1]) if row[1] else []
        datacenters = parse_multi_values(row[2]) if row[2] else []
        cloudregions = parse_multi_values(row[3]) if row[3] else []
        
        for region in regions:
            region_stats[region]['total'] += row[4]
            region_stats[region]['splunk'] += row[5] 
            region_stats[region]['cmdb'] += row[6]
            region_stats[region]['edr'] += row[7]
        
        for country in countries:
            country_stats[country]['total'] += row[4]
            country_stats[country]['splunk'] += row[5]
            country_stats[country]['cmdb'] += row[6] 
            country_stats[country]['edr'] += row[7]
        
        for dc in datacenters:
            datacenter_stats[dc]['total'] += row[4]
            datacenter_stats[dc]['splunk'] += row[5]
            datacenter_stats[dc]['cmdb'] += row[6]
            datacenter_stats[dc]['edr'] += row[7]
        
        for cr in cloudregions:
            cloudregion_stats[cr]['total'] += row[4]
            cloudregion_stats[cr]['splunk'] += row[5]
            cloudregion_stats[cr]['cmdb'] += row[6]
            cloudregion_stats[cr]['edr'] += row[7]
    
    for stats_dict in [region_stats, country_stats, datacenter_stats, cloudregion_stats]:
        for key, stats in stats_dict.items():
            if stats['total'] > 0:
                stats['splunk_coverage'] = round((stats['splunk'] / stats['total']) * 100, 1)
                stats['cmdb_coverage'] = round((stats['cmdb'] / stats['total']) * 100, 1)
                stats['edr_coverage'] = round((stats['edr'] / stats['total']) * 100, 1)
                stats['overall_coverage'] = round(((stats['splunk'] + stats['cmdb'] + stats['edr']) / (3 * stats['total'])) * 100, 1)
    
    conn.close()
    
    return jsonify({
        'regions': dict(region_stats),
        'countries': dict(country_stats), 
        'datacenters': dict(datacenter_stats),
        'cloud_regions': dict(cloudregion_stats)
    })

@app.route('/api/bu-application-view')
def bu_application_view():
    conn = get_db_connection()
    
    bu_data = conn.execute("""
        SELECT 
            business_unit,
            cio,
            apm,
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk,
            SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr
        FROM universal_cmdb 
        GROUP BY business_unit, cio, apm
        HAVING total > 1
        ORDER BY total DESC
    """).fetchall()
    
    bu_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    cio_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    apm_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    
    for row in bu_data:
        bus = parse_multi_values(row[0], [',']) if row[0] else []
        cios = parse_multi_values(row[1]) if row[1] else []
        apms = parse_multi_values(row[2]) if row[2] else []
        
        for bu in bus:
            if bu and str(bu).replace(' ', '').replace('-', '').isalpha():
                bu_stats[bu]['total'] += row[3]
                bu_stats[bu]['splunk'] += row[4]
                bu_stats[bu]['cmdb'] += row[5]
                bu_stats[bu]['edr'] += row[6]
        
        for cio in cios:
            if cio and str(cio).replace(' ', '').replace('-', '').isalpha():
                cio_stats[cio]['total'] += row[3]
                cio_stats[cio]['splunk'] += row[4]
                cio_stats[cio]['cmdb'] += row[5]
                cio_stats[cio]['edr'] += row[6]
        
        for apm in apms:
            if apm and 'apm' in str(apm).lower():
                apm_stats[apm]['total'] += row[3]
                apm_stats[apm]['splunk'] += row[4]
                apm_stats[apm]['cmdb'] += row[5]
                apm_stats[apm]['edr'] += row[6]
    
    for stats_dict in [bu_stats, cio_stats, apm_stats]:
        for key, stats in stats_dict.items():
            if stats['total'] > 0:
                stats['splunk_coverage'] = round((stats['splunk'] / stats['total']) * 100, 1)
                stats['cmdb_coverage'] = round((stats['cmdb'] / stats['total']) * 100, 1)
                stats['edr_coverage'] = round((stats['edr'] / stats['total']) * 100, 1)
                stats['overall_coverage'] = round(((stats['splunk'] + stats['cmdb'] + stats['edr']) / (3 * stats['total'])) * 100, 1)
    
    conn.close()
    
    return jsonify({
        'business_units': dict(bu_stats),
        'cio_oversight': dict(cio_stats),
        'apm_coverage': dict(apm_stats)
    })

@app.route('/api/system-classification')
def system_classification():
    conn = get_db_connection()
    
    system_data = conn.execute("""
        SELECT 
            system_classification,
            class,
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk,
            SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr
        FROM universal_cmdb 
        GROUP BY system_classification, class
        HAVING total > 1
        ORDER BY total DESC
    """).fetchall()
    
    system_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    class_stats = defaultdict(lambda: {'total': 0, 'splunk': 0, 'cmdb': 0, 'edr': 0})
    
    for row in system_data:
        systems = parse_multi_values(row[0], ['|']) if row[0] else []
        classes_raw = parse_multi_values(row[1], ['|']) if row[1] else []
        
        for system in systems:
            if system:
                system_stats[system]['total'] += row[2]
                system_stats[system]['splunk'] += row[3]
                system_stats[system]['cmdb'] += row[4]
                system_stats[system]['edr'] += row[5]
        
        for class_raw in classes_raw:
            matches = re.findall(r'class\s*(\d+)', str(class_raw).lower())
            for class_num in matches:
                class_key = f"class_{class_num}"
                class_stats[class_key]['total'] += row[2]
                class_stats[class_key]['splunk'] += row[3]
                class_stats[class_key]['cmdb'] += row[4]
                class_stats[class_key]['edr'] += row[5]
    
    for stats_dict in [system_stats, class_stats]:
        for key, stats in stats_dict.items():
            if stats['total'] > 0:
                stats['splunk_coverage'] = round((stats['splunk'] / stats['total']) * 100, 1)
                stats['cmdb_coverage'] = round((stats['cmdb'] / stats['total']) * 100, 1)
                stats['edr_coverage'] = round((stats['edr'] / stats['total']) * 100, 1)
                stats['overall_coverage'] = round(((stats['splunk'] + stats['cmdb'] + stats['edr']) / (3 * stats['total'])) * 100, 1)
    
    conn.close()
    
    return jsonify({
        'system_classifications': dict(system_stats),
        'class_breakdown': dict(class_stats)
    })

@app.route('/api/security-control-coverage')
def security_control_coverage():
    conn = get_db_connection()
    
    total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
    edr_coverage = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike%'").fetchone()[0]
    tanium_coverage = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%'").fetchone()[0]
    dlp_coverage = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE dlp_agent_coverage LIKE '%dlp%'").fetchone()[0]
    
    overlap_analysis = {
        'edr_cmdb': conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike%' AND present_in_cmdb = 'yes'").fetchone()[0],
        'edr_splunk': conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike%' AND logging_in_splunk = 'yes'").fetchone()[0],
        'tanium_cmdb': conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%' AND present_in_cmdb = 'yes'").fetchone()[0],
        'tanium_splunk': conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE tanium_coverage LIKE '%tanium%' AND logging_in_splunk = 'yes'").fetchone()[0],
        'all_controls': conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE edr_coverage LIKE '%crowdstrike%' AND tanium_coverage LIKE '%tanium%' AND logging_in_splunk = 'yes'").fetchone()[0]
    }
    
    conn.close()
    
    return jsonify({
        'coverage_summary': {
            'total_assets': total_assets,
            'edr_coverage': round((edr_coverage / total_assets) * 100, 1),
            'tanium_coverage': round((tanium_coverage / total_assets) * 100, 1),
            'dlp_coverage': round((dlp_coverage / total_assets) * 100, 1),
            'overall_security': round(((edr_coverage + tanium_coverage + dlp_coverage) / (3 * total_assets)) * 100, 1)
        },
        'control_overlaps': {
            'edr_cmdb_overlap': round((overlap_analysis['edr_cmdb'] / total_assets) * 100, 1),
            'edr_splunk_overlap': round((overlap_analysis['edr_splunk'] / total_assets) * 100, 1),
            'tanium_cmdb_overlap': round((overlap_analysis['tanium_cmdb'] / total_assets) * 100, 1),
            'tanium_splunk_overlap': round((overlap_analysis['tanium_splunk'] / total_assets) * 100, 1),
            'full_stack_coverage': round((overlap_analysis['all_controls'] / total_assets) * 100, 1)
        }
    })

@app.route('/api/domain-visibility')
def domain_visibility():
    conn = get_db_connection()
    
    dc1_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%'").fetchone()[0]
    dc1_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%' AND logging_in_splunk = 'yes'").fetchone()[0]
    dc1_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%' AND present_in_cmdb = 'yes'").fetchone()[0]
    dc1_edr = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%1dc%' AND edr_coverage LIKE '%crowdstrike%'").fetchone()[0]
    
    fead_total = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%'").fetchone()[0]
    fead_splunk = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%' AND logging_in_splunk = 'yes'").fetchone()[0]
    fead_cmdb = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%' AND present_in_cmdb = 'yes'").fetchone()[0]
    fead_edr = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain LIKE '%fead%' AND edr_coverage LIKE '%crowdstrike%'").fetchone()[0]
    
    domain_breakdown = conn.execute("""
        SELECT 
            domain,
            COUNT(*) as total,
            SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk,
            SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb,
            SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr
        FROM universal_cmdb 
        WHERE domain IS NOT NULL AND domain != 'null'
        GROUP BY domain
        HAVING total > 10
        ORDER BY total DESC
        LIMIT 50
    """).fetchall()
    
    domain_stats = {}
    for row in domain_breakdown:
        domain_stats[row[0]] = {
            'total': row[1],
            'splunk_coverage': round((row[2] / row[1]) * 100, 1),
            'cmdb_coverage': round((row[3] / row[1]) * 100, 1),
            'edr_coverage': round((row[4] / row[1]) * 100, 1),
            'overall_coverage': round(((row[2] + row[3] + row[4]) / (3 * row[1])) * 100, 1)
        }
    
    conn.close()
    
    return jsonify({
        'domain_summary': {
            '1dc': {
                'total': dc1_total,
                'splunk_coverage': round((dc1_splunk / dc1_total) * 100, 1) if dc1_total > 0 else 0,
                'cmdb_coverage': round((dc1_cmdb / dc1_total) * 100, 1) if dc1_total > 0 else 0,
                'edr_coverage': round((dc1_edr / dc1_total) * 100, 1) if dc1_total > 0 else 0
            },
            'fead': {
                'total': fead_total,
                'splunk_coverage': round((fead_splunk / fead_total) * 100, 1) if fead_total > 0 else 0,
                'cmdb_coverage': round((fead_cmdb / fead_total) * 100, 1) if fead_total > 0 else 0,
                'edr_coverage': round((fead_edr / fead_total) * 100, 1) if fead_total > 0 else 0
            }
        },
        'all_domains': domain_stats
    })

@app.route('/api/logging-compliance')
def logging_compliance():
    conn = get_db_connection()
    
    total_assets = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
    splunk_only = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_splunk = 'yes' AND (logging_in_chronicle != 'yes' OR logging_in_chronicle IS NULL)").fetchone()[0]
    chronicle_only = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_chronicle = 'yes' AND (logging_in_splunk != 'yes' OR logging_in_splunk IS NULL)").fetchone()[0]
    both_platforms = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_splunk = 'yes' AND logging_in_chronicle = 'yes'").fetchone()[0]
    no_logging = conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE (logging_in_splunk != 'yes' OR logging_in_splunk IS NULL) AND (logging_in_chronicle != 'yes' OR logging_in_chronicle IS NULL)").fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'platform_breakdown': {
            'total_assets': total_assets,
            'splunk_only': {'count': splunk_only, 'percentage': round((splunk_only / total_assets) * 100, 1)},
            'chronicle_only': {'count': chronicle_only, 'percentage': round((chronicle_only / total_assets) * 100, 1)},
            'dual_platform': {'count': both_platforms, 'percentage': round((both_platforms / total_assets) * 100, 1)},
            'no_logging': {'count': no_logging, 'percentage': round((no_logging / total_assets) * 100, 1)},
            'total_compliance': round(((splunk_only + chronicle_only + both_platforms) / total_assets) * 100, 1)
        }
    })

@app.route('/api/log-type-priority')
def log_type_priority():
    conn = get_db_connection()
    
    priority_analysis = {}
    
    critical_systems = conn.execute("""
        SELECT COUNT(*) as total,
        SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk,
        SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb,
        SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr
        FROM universal_cmdb 
        WHERE infrastructure_type LIKE '%database%' OR infrastructure_type LIKE '%domain controller%' OR infrastructure_type LIKE '%exchange%'
    """).fetchone()
    
    high_priority = conn.execute("""
        SELECT COUNT(*) as total,
        SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk,
        SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb,
        SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr
        FROM universal_cmdb 
        WHERE infrastructure_type LIKE '%server%' OR infrastructure_type LIKE '%firewall%'
    """).fetchone()
    
    medium_priority = conn.execute("""
        SELECT COUNT(*) as total,
        SUM(CASE WHEN logging_in_splunk = 'yes' THEN 1 ELSE 0 END) as splunk,
        SUM(CASE WHEN present_in_cmdb = 'yes' THEN 1 ELSE 0 END) as cmdb,
        SUM(CASE WHEN edr_coverage LIKE '%crowdstrike%' THEN 1 ELSE 0 END) as edr
        FROM universal_cmdb 
        WHERE infrastructure_type LIKE '%workstation%' OR infrastructure_type LIKE '%desktop%'
    """).fetchone()
    
    for priority, data_row in [('critical', critical_systems), ('high', high_priority), ('medium', medium_priority)]:
        if data_row[0] > 0:
            priority_analysis[priority] = {
                'total': data_row[0],
                'splunk_coverage': round((data_row[1] / data_row[0]) * 100, 1),
                'cmdb_coverage': round((data_row[2] / data_row[0]) * 100, 1),
                'edr_coverage': round((data_row[3] / data_row[0]) * 100, 1),
                'overall_coverage': round(((data_row[1] + data_row[2] + data_row[3]) / (3 * data_row[0])) * 100, 1)
            }
    
    conn.close()
    
    return jsonify(priority_analysis)

if __name__ == '__main__':
    app.run(debug=True, port=5000)