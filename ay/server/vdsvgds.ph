# Add this debug endpoint to your app.py to see what's happening

@app.route('/api/debug/current-state')
def debug_current_state():
    """Show current DB_CONFIG state and test query"""
    try:
        # Show current config
        debug_info = {
            'db_config': {
                'db_path': DB_CONFIG.get('db_path'),
                'full_table_name': DB_CONFIG.get('full_table_name'),
                'simple_table_name': DB_CONFIG.get('simple_table_name'),
                'connection_method': DB_CONFIG.get('connection_method'),
                'columns': list(DB_CONFIG.get('columns', {}).keys())[:10]  # First 10 columns
            }
        }
        
        # Try to connect and query
        if DB_CONFIG.get('db_path'):
            try:
                conn = get_connection()
                
                # Try the stored table name
                if DB_CONFIG.get('full_table_name'):
                    try:
                        query = f"SELECT COUNT(*) FROM {DB_CONFIG['full_table_name']}"
                        count = conn.execute(query).fetchone()[0]
                        debug_info['query_test'] = {
                            'query': query,
                            'result': count,
                            'status': 'SUCCESS'
                        }
                    except Exception as e:
                        debug_info['query_test'] = {
                            'query': query,
                            'error': str(e),
                            'status': 'FAILED'
                        }
                
                # List actual tables in database
                try:
                    tables = conn.execute("SHOW TABLES").fetchall()
                    debug_info['actual_tables'] = [str(t[0]) for t in tables]
                except:
                    debug_info['actual_tables'] = []
                
                conn.close()
            except Exception as e:
                debug_info['connection_error'] = str(e)
        else:
            debug_info['error'] = 'No DB_CONFIG path set - discovery may not have run'
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500