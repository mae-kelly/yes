import duckdb
import os
import pandas as pd

def comprehensive_db_test():
    db_files = ['universal_cmdb.db', 'cmdb.db', 'universal_cmdb.duckdb']
    
    print("=== FILE SYSTEM CHECK ===")
    print(f"Current directory: {os.getcwd()}")
    all_files = os.listdir('.')
    db_files_found = [f for f in all_files if f.endswith('.db') or f.endswith('.duckdb')]
    print(f"Database files found: {db_files_found}")
    
    for db_file in db_files_found:
        if os.path.exists(db_file):
            print(f"\n=== TESTING: {db_file} ===")
            print(f"File size: {os.path.getsize(db_file):,} bytes")
            
            # Method 1: Direct connection
            try:
                print(f"\n--- Method 1: Direct connection to {db_file} ---")
                conn = duckdb.connect(db_file)
                
                # Show all tables
                tables_result = conn.execute("SHOW ALL TABLES").fetchall()
                print(f"SHOW ALL TABLES: {tables_result}")
                
                # Show schemas
                try:
                    schemas = conn.execute("SELECT schema_name FROM information_schema.schemata").fetchall()
                    print(f"Schemas: {schemas}")
                except Exception as e:
                    print(f"No schemas query: {e}")
                
                # Try different table access patterns
                table_patterns = [
                    "universal_cmdb",
                    "main.universal_cmdb",
                    "cmdb.universal_cmdb",
                    "cmdb.main.universal_cmdb"
                ]
                
                for pattern in table_patterns:
                    try:
                        count_result = conn.execute(f"SELECT COUNT(*) FROM {pattern}").fetchone()
                        print(f"✅ SUCCESS: {pattern} has {count_result[0]:,} records")
                        
                        # Get column info
                        describe_result = conn.execute(f"DESCRIBE {pattern}").fetchall()
                        columns = [col[0] for col in describe_result]
                        print(f"   Columns ({len(columns)}): {columns[:10]}{'...' if len(columns) > 10 else ''}")
                        
                        # Get sample data
                        sample = conn.execute(f"SELECT * FROM {pattern} LIMIT 3").fetchall()
                        print(f"   Sample record count: {len(sample)}")
                        if sample:
                            print(f"   First record columns: {len(sample[0])}")
                        
                        # Try our specific query
                        our_query = f"""
                        SELECT 
                            fqdn, business_unit, region, country, data_center, cloud_region,
                            system_classification, infrastructure_type, cio, apm,
                            logging_in_splunk, logging_in_gso, present_in_cmdb, 
                            edr_coverage, tanium_coverage, dlp_agent_coverage,
                            first_seen, last_updated, data_quality_score, source_count
                        FROM {pattern}
                        WHERE fqdn IS NOT NULL AND fqdn != ''
                            AND data_quality_score > 3.0
                        ORDER BY data_quality_score DESC
                        LIMIT 5
                        """
                        our_result = conn.execute(our_query).fetchall()
                        print(f"   Our query returned: {len(our_result)} records")
                        
                        # Convert to DataFrame to test
                        df = conn.execute(our_query).df()
                        print(f"   DataFrame shape: {df.shape}")
                        print(f"   DataFrame columns: {list(df.columns)}")
                        if not df.empty:
                            print(f"   Sample FQDN: {df['fqdn'].iloc[0] if 'fqdn' in df.columns else 'No FQDN column'}")
                        
                        break  # Success, no need to try other patterns
                        
                    except Exception as e:
                        print(f"❌ FAILED: {pattern} - {e}")
                
                conn.close()
                
            except Exception as e:
                print(f"Direct connection failed: {e}")
            
            # Method 2: Memory + Attach
            try:
                print(f"\n--- Method 2: Memory + Attach {db_file} ---")
                conn = duckdb.connect()
                conn.execute(f"ATTACH '{db_file}' AS testdb")
                
                # Show databases
                dbs = conn.execute("SHOW DATABASES").fetchall()
                print(f"Databases after attach: {dbs}")
                
                # Show tables in attached database
                tables = conn.execute("SHOW ALL TABLES").fetchall()
                print(f"All tables after attach: {tables}")
                
                # Try accessing with different patterns
                attach_patterns = [
                    "testdb.universal_cmdb",
                    "testdb.main.universal_cmdb",
                    "universal_cmdb",
                    "main.universal_cmdb"
                ]
                
                for pattern in attach_patterns:
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM {pattern}").fetchone()[0]
                        print(f"✅ ATTACH SUCCESS: {pattern} has {count:,} records")
                        break
                    except Exception as e:
                        print(f"❌ ATTACH FAILED: {pattern} - {e}")
                
                conn.close()
                
            except Exception as e:
                print(f"Attach method failed: {e}")
            
            # Method 3: Direct SQL file reading
            try:
                print(f"\n--- Method 3: Direct file inspection ---")
                conn = duckdb.connect()
                
                # Try to read the database file directly
                try:
                    conn.execute(f"INSTALL sqlite_scanner; LOAD sqlite_scanner;")
                    tables = conn.execute(f"SELECT * FROM sqlite_scan('{db_file}', 'sqlite_master')").fetchall()
                    print(f"SQLite scan results: {tables}")
                except Exception as e:
                    print(f"SQLite scanner failed: {e}")
                
                conn.close()
                
            except Exception as e:
                print(f"Direct inspection failed: {e}")
    
    # Method 4: Try pandas with different engines
    print(f"\n=== Method 4: Pandas with different engines ===")
    for db_file in db_files_found:
        try:
            # Try reading with pandas
            conn = duckdb.connect(db_file)
            df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
            print(f"Pandas read from {db_file}: {df}")
            conn.close()
        except Exception as e:
            print(f"Pandas failed on {db_file}: {e}")

if __name__ == "__main__":
    comprehensive_db_test()