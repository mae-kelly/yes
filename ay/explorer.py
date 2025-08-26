#!/usr/bin/env python3
import duckdb
import os
import glob

def find_and_explore_db():
    # Find all .db files
    db_files = []
    for pattern in ["*.db", "../*.db", "../../*.db", "server/*.db"]:
        db_files.extend(glob.glob(pattern))
    
    print(f"Found .db files: {db_files}")
    
    for db_file in db_files:
        print(f"\n{'='*60}")
        print(f"EXPLORING: {db_file}")
        print(f"{'='*60}")
        
        try:
            conn = duckdb.connect(db_file, read_only=True)
            
            # List all tables
            tables = conn.execute("SHOW TABLES").fetchall()
            print(f"Tables found: {len(tables)}")
            
            for table in tables:
                table_name = table[0]
                print(f"\n--- TABLE: {table_name} ---")
                
                # Get columns - try different quoting methods
                try:
                    # Try different ways to quote the table name
                    queries_to_try = [
                        f'DESCRIBE "{table_name}"',
                        f"DESCRIBE '{table_name}'", 
                        f"DESCRIBE `{table_name}`",
                        f"DESCRIBE {table_name}",
                        f'PRAGMA table_info("{table_name}")'
                    ]
                    
                    columns = None
                    for query in queries_to_try:
                        try:
                            columns = conn.execute(query).fetchall()
                            print(f"Successful query: {query}")
                            break
                        except Exception as e:
                            continue
                    
                    if columns:
                        print(f"Columns ({len(columns)}):")
                        for col in columns:
                            print(f"  - {col[0]} ({col[1]})")
                        
                        # Get row count - try different quoting
                        count = None
                        count_queries = [
                            f'SELECT COUNT(*) FROM "{table_name}"',
                            f"SELECT COUNT(*) FROM '{table_name}'",
                            f"SELECT COUNT(*) FROM `{table_name}`",
                            f"SELECT COUNT(*) FROM {table_name}"
                        ]
                        
                        for count_query in count_queries:
                            try:
                                count = conn.execute(count_query).fetchone()[0]
                                break
                            except:
                                continue
                        
                        if count is not None:
                            print(f"Rows: {count:,}")
                            
                            # Show sample data
                            if count > 0:
                                sample_queries = [
                                    f'SELECT * FROM "{table_name}" LIMIT 3',
                                    f"SELECT * FROM '{table_name}' LIMIT 3",
                                    f"SELECT * FROM `{table_name}` LIMIT 3",
                                    f"SELECT * FROM {table_name} LIMIT 3"
                                ]
                                
                                for sample_query in sample_queries:
                                    try:
                                        sample = conn.execute(sample_query).fetchall()
                                        print("Sample data:")
                                        for i, row in enumerate(sample):
                                            print(f"  Row {i+1}: {row[:5]}...")  # First 5 columns
                                        break
                                    except:
                                        continue
                        else:
                            print("Could not get row count")
                    else:
                        print("Could not get column information")
                    
                except Exception as e:
                    print(f"Error exploring table {table_name}: {e}")
            
            conn.close()
            
        except Exception as e:
            print(f"Error with {db_file}: {e}")

if __name__ == "__main__":
    find_and_explore_db()