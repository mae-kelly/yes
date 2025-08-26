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
                
                # Get columns
                try:
                    columns = conn.execute(f"DESCRIBE `{table_name}`").fetchall()
                    print(f"Columns ({len(columns)}):")
                    for col in columns:
                        print(f"  - {col[0]} ({col[1]})")
                    
                    # Get row count
                    count = conn.execute(f"SELECT COUNT(*) FROM `{table_name}`").fetchone()[0]
                    print(f"Rows: {count:,}")
                    
                    # Show sample data
                    if count > 0:
                        sample = conn.execute(f"SELECT * FROM `{table_name}` LIMIT 3").fetchall()
                        print("Sample data:")
                        for i, row in enumerate(sample):
                            print(f"  Row {i+1}: {row[:5]}...")  # First 5 columns
                    
                except Exception as e:
                    print(f"Error exploring table {table_name}: {e}")
            
            conn.close()
            
        except Exception as e:
            print(f"Error with {db_file}: {e}")

if __name__ == "__main__":
    find_and_explore_db()