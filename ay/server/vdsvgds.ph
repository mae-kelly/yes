# Replace your existing /api/global-view endpoint in app.py with this corrected version:

@app.route('/api/global-view')
def global_view():
    try:
        if not DB_CONFIG['db_path']:
            if not try_connection_methods():
                raise Exception("Database not available after 20+ attempts")
        
        table_name = DB_CONFIG['full_table_name']
        total_hosts = execute_query(f'SELECT COUNT(*) FROM {table_name}')[0][0]
        
        coverage = {}
        
        # Splunk coverage (note: key is 'splunk', not 'splunk_logging')
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE LOWER(logging_in_splunk) = 'yes'"
            count = execute_query(query)[0][0]
            coverage['splunk'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except Exception as e:
            logger.error(f"Error calculating splunk coverage: {str(e)}")
            coverage['splunk'] = {'count': 0, 'percentage': 0}
        
        # CMDB coverage (note: key is 'cmdb', not 'cmdb_present')
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE LOWER(present_in_cmdb) = 'yes'"
            count = execute_query(query)[0][0]
            coverage['cmdb'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except Exception as e:
            logger.error(f"Error calculating cmdb coverage: {str(e)}")
            coverage['cmdb'] = {'count': 0, 'percentage': 0}
        
        # CrowdStrike/EDR coverage (note: key is 'crowdstrike')
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE edr_coverage IS NOT NULL AND edr_coverage != ''"
            count = execute_query(query)[0][0]
            coverage['crowdstrike'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except Exception as e:
            logger.error(f"Error calculating crowdstrike coverage: {str(e)}")
            coverage['crowdstrike'] = {'count': 0, 'percentage': 0}
        
        # Tanium coverage
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE tanium_coverage IS NOT NULL AND tanium_coverage != ''"
            count = execute_query(query)[0][0]
            coverage['tanium'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except Exception as e:
            logger.error(f"Error calculating tanium coverage: {str(e)}")
            coverage['tanium'] = {'count': 0, 'percentage': 0}
        
        # APM coverage
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE apm IS NOT NULL AND apm != ''"
            count = execute_query(query)[0][0]
            coverage['apm'] = {
                'count': count,
                'percentage': calculate_coverage_percentage(count, total_hosts)
            }
        except Exception as e:
            logger.error(f"Error calculating apm coverage: {str(e)}")
            coverage['apm'] = {'count': 0, 'percentage': 0}
        
        return jsonify({
            'total_hosts': total_hosts,
            'coverage': coverage,
            'connection_method': DB_CONFIG['connection_method'],
            'table': table_name,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Global view failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500