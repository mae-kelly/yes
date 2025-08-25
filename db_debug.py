import duckdb
import os

def debug_duckdb_connection():
    db_path = 'universal_cmdb.db'
    
    print(f"Checking if file exists: {os.path.exists(db_path)}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    
    # Method 1: Direct connection to file
    try:
        print("\n=== Method 1: Direct connection ===")
        conn = duckdb.connect(db_path)
        tables = conn.execute("SHOW TABLES").df()
        print(f"Tables: {tables}")
        conn.close()
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Method 2: Memory connection with attach
    try:
        print("\n=== Method 2: Memory + ATTACH ===")
        conn = duckdb.connect()
        conn.execute(f"ATTACH '{db_path}' AS cmdb")
        tables = conn.execute("SHOW TABLES").df()
        print(f"Tables after attach: {tables}")
        databases = conn.execute("SHOW DATABASES").df()
        print(f"Databases: {databases}")
        conn.close()
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Method 3: Try to list schemas in the attached database
    try:
        print("\n=== Method 3: List schemas ===")
        conn = duckdb.connect()
        conn.execute(f"ATTACH '{db_path}' AS cmdb")
        schemas = conn.execute("SELECT schema_name FROM cmdb.information_schema.schemata").df()
        print(f"Schemas in cmdb: {schemas}")
        conn.close()
    except Exception as e:
        print(f"Method 3 failed: {e}")
    
    # Method 4: Try different table access patterns
    try:
        print("\n=== Method 4: Test table access patterns ===")
        conn = duckdb.connect()
        conn.execute(f"ATTACH '{db_path}' AS cmdb")
        
        # Try different ways to access the table
        access_patterns = [
            "cmdb.main.universal_cmdb",
            "cmdb.universal_cmdb", 
            "main.universal_cmdb",
            "universal_cmdb"
        ]
        
        for pattern in access_patterns:
            try:
                result = conn.execute(f"SELECT COUNT(*) FROM {pattern}").df()
                print(f"✅ SUCCESS with pattern: {pattern} - Count: {result}")
                
                # If successful, try to get column names
                columns = conn.execute(f"DESCRIBE {pattern}").df()
                print(f"Columns: {columns['column_name'].tolist()}")
                break
            except Exception as e:
                print(f"❌ Failed with pattern {pattern}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"Method 4 failed: {e}")

if __name__ == "__main__":
    debug_duckdb_connection()