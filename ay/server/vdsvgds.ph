# Add ALL these endpoints to your app.py file, right before the if __name__ == '__main__': line

@app.route('/api/logging-compliance-gso-splunk')
def logging_compliance_gso_splunk():
    try:
        if not DB_CONFIG['db_path']:
            if not try_connection_methods():
                raise Exception("Database not available")
        
        table_name = DB_CONFIG['full_table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM {table_name}')[0][0]
        
        summary = {}
        
        # Splunk only coverage
        try:
            query = f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE LOWER(logging_in_splunk) = 'yes' 
                AND (LOWER(logging_in_gso) != 'yes' OR logging_in_gso IS NULL)
            """
            splunk_only = execute_query(query)[0][0]
            summary['splunk_coverage'] = {
                'count': splunk_only,
                'percentage': calculate_coverage_percentage(splunk_only, total_hosts)
            }
        except:
            summary['splunk_coverage'] = {'count': 0, 'percentage': 0}
        
        # Chronicle/GSO coverage  
        try:
            query = f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE LOWER(logging_in_gso) = 'yes' 
                AND (LOWER(logging_in_splunk) != 'yes' OR logging_in_splunk IS NULL)
            """
            chronicle_only = execute_query(query)[0][0]
            summary['chronicle_coverage'] = {
                'count': chronicle_only,
                'percentage': calculate_coverage_percentage(chronicle_only, total_hosts)
            }
        except:
            summary['chronicle_coverage'] = {'count': 0, 'percentage': 0}
        
        # Dual platform
        try:
            query = f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE LOWER(logging_in_splunk) = 'yes' 
                AND LOWER(logging_in_gso) = 'yes'
            """
            dual_platform = execute_query(query)[0][0]
            summary['dual_platform'] = {
                'count': dual_platform,
                'percentage': calculate_coverage_percentage(dual_platform, total_hosts)
            }
        except:
            summary['dual_platform'] = {'count': 0, 'percentage': 0}
        
        # No logging
        try:
            query = f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE (LOWER(logging_in_splunk) != 'yes' OR logging_in_splunk IS NULL)
                AND (LOWER(logging_in_gso) != 'yes' OR logging_in_gso IS NULL)
            """
            no_logging = execute_query(query)[0][0]
            summary['no_logging'] = {
                'count': no_logging,
                'percentage': calculate_coverage_percentage(no_logging, total_hosts)
            }
        except:
            summary['no_logging'] = {'count': 0, 'percentage': 0}
        
        # Regional compliance
        regional_compliance = {}
        try:
            regions_query = f"""
                SELECT DISTINCT region 
                FROM {table_name} 
                WHERE region IS NOT NULL AND region != ''
            """
            regions = execute_query(regions_query)
            
            for region_row in regions[:10]:  # Limit to 10 regions for performance
                region = region_row[0]
                
                stats_query = f"""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END) as splunk_count,
                        SUM(CASE WHEN LOWER(logging_in_gso) = 'yes' THEN 1 ELSE 0 END) as chronicle_count,
                        SUM(CASE WHEN LOWER(logging_in_splunk) = 'yes' OR LOWER(logging_in_gso) = 'yes' THEN 1 ELSE 0 END) as any_logging
                    FROM {table_name}
                    WHERE region = '{region}'
                """
                
                stats = execute_query(stats_query)[0]
                total, splunk_count, chronicle_count, any_logging = stats
                
                regional_compliance[region] = {
                    'total': total,
                    'splunk_percentage': calculate_coverage_percentage(splunk_count, total),
                    'chronicle_percentage': calculate_coverage_percentage(chronicle_count, total),
                    'overall_compliance': calculate_coverage_percentage(any_logging, total)
                }
        except Exception as e:
            logger.error(f"Regional compliance error: {str(e)}")
        
        return jsonify({
            'summary': summary,
            'regional_compliance': regional_compliance,
            'total_hosts': total_hosts,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Logging compliance failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/security-control-coverage')
def security_control_coverage():
    try:
        if not DB_CONFIG['db_path']:
            if not try_connection_methods():
                raise Exception("Database not available")
        
        table_name = DB_CONFIG['full_table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM {table_name}')[0][0]
        
        coverage = {}
        
        # EDR coverage
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE edr_coverage IS NOT NULL AND edr_coverage != ''"
            count = execute_query(query)[0][0]
            coverage['edr'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except:
            coverage['edr'] = {'count': 0, 'percentage': 0}
        
        # Tanium coverage
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE tanium_coverage IS NOT NULL AND tanium_coverage != ''"
            count = execute_query(query)[0][0]
            coverage['tanium'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except:
            coverage['tanium'] = {'count': 0, 'percentage': 0}
        
        # DLP coverage
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE dlp_agent_coverage IS NOT NULL AND dlp_agent_coverage != ''"
            count = execute_query(query)[0][0]
            coverage['dlp'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except:
            coverage['dlp'] = {'count': 0, 'percentage': 0}
        
        # Overlaps
        overlaps = {}
        
        # EDR + Tanium
        try:
            query = f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE edr_coverage IS NOT NULL AND edr_coverage != ''
                AND tanium_coverage IS NOT NULL AND tanium_coverage != ''
            """
            count = execute_query(query)[0][0]
            overlaps['edr_tanium'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except:
            overlaps['edr_tanium'] = {'count': 0, 'percentage': 0}
        
        # EDR + DLP
        try:
            query = f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE edr_coverage IS NOT NULL AND edr_coverage != ''
                AND dlp_agent_coverage IS NOT NULL AND dlp_agent_coverage != ''
            """
            count = execute_query(query)[0][0]
            overlaps['edr_dlp'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except:
            overlaps['edr_dlp'] = {'count': 0, 'percentage': 0}
        
        # All three
        try:
            query = f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE edr_coverage IS NOT NULL AND edr_coverage != ''
                AND tanium_coverage IS NOT NULL AND tanium_coverage != ''
                AND dlp_agent_coverage IS NOT NULL AND dlp_agent_coverage != ''
            """
            count = execute_query(query)[0][0]
            overlaps['all_three'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except:
            overlaps['all_three'] = {'count': 0, 'percentage': 0}
        
        return jsonify({
            'total_hosts': total_hosts,
            'coverage': coverage,
            'overlaps': overlaps,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Security control coverage failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/domain-visibility')
def domain_visibility():
    try:
        if not DB_CONFIG['db_path']:
            if not try_connection_methods():
                raise Exception("Database not available")
        
        table_name = DB_CONFIG['full_table_name']
        
        data = {'1dc': {}, 'fead': {}}
        
        # 1DC domain
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN LOWER(present_in_cmdb) = 'yes' THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN edr_coverage IS NOT NULL AND edr_coverage != '' THEN 1 ELSE 0 END) as edr_count
                FROM {table_name}
                WHERE LOWER(domain) LIKE '%1dc%'
            """
            result = execute_query(query)[0]
            total, splunk, cmdb, edr = result
            
            data['1dc'] = {
                'total': total,
                'splunk_coverage': calculate_coverage_percentage(splunk, total),
                'cmdb_coverage': calculate_coverage_percentage(cmdb, total),
                'edr_coverage': calculate_coverage_percentage(edr, total),
                'overall_coverage': calculate_coverage_percentage((splunk + cmdb + edr) / 3, total)
            }
        except:
            data['1dc'] = {'total': 0, 'splunk_coverage': 0, 'cmdb_coverage': 0, 'edr_coverage': 0, 'overall_coverage': 0}
        
        # FEAD domain
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN LOWER(present_in_cmdb) = 'yes' THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN edr_coverage IS NOT NULL AND edr_coverage != '' THEN 1 ELSE 0 END) as edr_count
                FROM {table_name}
                WHERE LOWER(domain) LIKE '%fead%'
            """
            result = execute_query(query)[0]
            total, splunk, cmdb, edr = result
            
            data['fead'] = {
                'total': total,
                'splunk_coverage': calculate_coverage_percentage(splunk, total),
                'cmdb_coverage': calculate_coverage_percentage(cmdb, total),
                'edr_coverage': calculate_coverage_percentage(edr, total),
                'overall_coverage': calculate_coverage_percentage((splunk + cmdb + edr) / 3, total)
            }
        except:
            data['fead'] = {'total': 0, 'splunk_coverage': 0, 'cmdb_coverage': 0, 'edr_coverage': 0, 'overall_coverage': 0}
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Domain visibility failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/infrastructure-type')
def infrastructure_type():
    try:
        if not DB_CONFIG['db_path']:
            if not try_connection_methods():
                raise Exception("Database not available")
        
        table_name = DB_CONFIG['full_table_name']
        
        query = f"""
            SELECT 
                infrastructure_type,
                COUNT(*) as total,
                SUM(CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END) as splunk_count,
                SUM(CASE WHEN LOWER(present_in_cmdb) = 'yes' THEN 1 ELSE 0 END) as cmdb_count,
                SUM(CASE WHEN edr_coverage IS NOT NULL AND edr_coverage != '' THEN 1 ELSE 0 END) as edr_count
            FROM {table_name}
            WHERE infrastructure_type IS NOT NULL AND infrastructure_type != ''
            GROUP BY infrastructure_type
            LIMIT 50
        """
        
        results = execute_query(query)
        
        infrastructure_data = {}
        for row in results:
            infra_type, total, splunk, cmdb, edr = row
            infrastructure_data[infra_type] = {
                'total': total,
                'splunk_coverage': calculate_coverage_percentage(splunk, total),
                'cmdb_coverage': calculate_coverage_percentage(cmdb, total),
                'edr_coverage': calculate_coverage_percentage(edr, total),
                'overall_coverage': calculate_coverage_percentage((splunk + cmdb + edr) / 3, total)
            }
        
        return jsonify(infrastructure_data)
        
    except Exception as e:
        logger.error(f"Infrastructure type failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regional-country-view')
def regional_country_view():
    try:
        if not DB_CONFIG['db_path']:
            if not try_connection_methods():
                raise Exception("Database not available")
        
        table_name = DB_CONFIG['full_table_name']
        
        data = {'regions': {}, 'countries': {}}
        
        # Regional data
        try:
            query = f"""
                SELECT 
                    region,
                    COUNT(*) as total,
                    SUM(CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN LOWER(present_in_cmdb) = 'yes' THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN edr_coverage IS NOT NULL AND edr_coverage != '' THEN 1 ELSE 0 END) as edr_count
                FROM {table_name}
                WHERE region IS NOT NULL AND region != ''
                GROUP BY region
                LIMIT 20
            """
            
            results = execute_query(query)
            for row in results:
                region, total, splunk, cmdb, edr = row
                data['regions'][region] = {
                    'total': total,
                    'splunk_coverage': calculate_coverage_percentage(splunk, total),
                    'cmdb_coverage': calculate_coverage_percentage(cmdb, total),
                    'edr_coverage': calculate_coverage_percentage(edr, total),
                    'overall_coverage': calculate_coverage_percentage((splunk + cmdb + edr) / 3, total)
                }
        except Exception as e:
            logger.error(f"Regional data error: {str(e)}")
        
        # Country data
        try:
            query = f"""
                SELECT 
                    country,
                    COUNT(*) as total,
                    SUM(CASE WHEN LOWER(logging_in_splunk) = 'yes' THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN LOWER(