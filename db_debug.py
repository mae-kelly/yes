import duckdb
import os

# Check file existence
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {[f for f in os.listdir('.') if f.endswith('.db')]}")

db_file = 'universal_cmdb.db'
print(f"Database file exists: {os.path.exists(db_file)}")

if os.path.exists(db_file):
    print(f"File size: {os.path.getsize(db_file)} bytes")

# Try different connection methods
methods = [
    ("Direct connection", lambda: duckdb.connect(db_file)),
    ("Memory + attach", lambda: duckdb.connect() and duckdb.connect().execute(f"ATTACH '{db_file}'")),
]

for method_name, connect_func in methods:
    try:
        print(f"\n=== {method_name} ===")
        conn = connect_func()
        
        # Show all tables
        try:
            result = conn.execute("SHOW ALL TABLES").fetchall()
            print(f"All tables: {result}")
        except:
            result = conn.execute("SHOW TABLES").fetchall()
            print(f"Tables: {result}")
        
        # Show databases
        try:
            dbs = conn.execute("SHOW DATABASES").fetchall()
            print(f"Databases: {dbs}")
        except Exception as e:
            print(f"No databases command: {e}")
        
        # Try to access the table different ways
        table_patterns = [
            "universal_cmdb",
            "main.universal_cmdb", 
            "SELECT * FROM pragma_table_info('universal_cmdb')",
        ]
        
        for pattern in table_patterns:
            try:
                if pattern.startswith("SELECT"):
                    result = conn.execute(pattern).fetchall()
                else:
                    result = conn.execute(f"SELECT COUNT(*) FROM {pattern}").fetchall()
                print(f"✅ {pattern}: {result}")
                
                # If this works, get column names
                if not pattern.startswith("SELECT"):
                    cols = conn.execute(f"DESCRIBE {pattern}").fetchall()
                    print(f"Columns for {pattern}: {[col[0] for col in cols]}")
                break
            except Exception as e:
                print(f"❌ {pattern}: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"{method_name} failed completely: {e}")

print("\n=== Raw DuckDB commands ===")
try:
    conn = duckdb.connect(db_file)
    print("Connected successfully!")
    
    # Just see what's in there
    result = conn.execute(".tables").fetchall()
    print(f"Dot tables: {result}")
except Exception as e:
    print(f"Raw connection failed: {e}")
finally:
    try:
        conn.close()
    except:
        pass