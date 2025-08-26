#!/usr/bin/env python3
"""
Database Inspector Script
Analyzes the universal_cmdb.db file to show table structure, columns, and sample data
"""

import duckdb
import os
import sys

def inspect_database(db_path="universal_cmdb.db"):
    """Inspect the database and show complete structure"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    print(f"🔍 Inspecting database: {db_path}")
    print(f"📁 File size: {os.path.getsize(db_path):,} bytes")
    print("=" * 80)
    
    try:
        conn = duckdb.connect(db_path, read_only=True)
        
        # 1. Show all tables
        print("\n📊 TABLES IN DATABASE:")
        tables = conn.execute("SHOW TABLES").fetchall()
        
        if not tables:
            print("   No tables found!")
            return
            
        for table in tables:
            print(f"   • {table[0]}")
        
        # 2. For each table, show structure
        for table in tables:
            table_name = table[0]
            print(f"\n🏗️  TABLE: {table_name}")
            print("-" * 60)
            
            # Get column info
            try:
                columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                print(f"   Columns ({len(columns)} total):")
                for col in columns:
                    col_name, col_type, nullable, key, default, extra = col
                    key_info = " (PRIMARY KEY)" if key else ""
                    print(f"     • {col_name:<25} {col_type:<15} {key_info}")
                
                # Get row count
                row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                print(f"   \n📈 Total rows: {row_count:,}")
                
                # Show sample data (first 5 rows)
                if row_count > 0:
                    print(f"\n🔬 SAMPLE DATA (first 5 rows):")
                    sample_data = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
                    
                    # Print header
                    col_names = [col[0] for col in columns]
                    header = " | ".join(f"{name[:15]:<15}" for name in col_names)
                    print(f"   {header}")
                    print(f"   {'-' * len(header)}")
                    
                    # Print sample rows
                    for row in sample_data:
                        row_str = " | ".join(f"{str(val)[:15]:<15}" if val is not None else f"{'NULL':<15}" for val in row)
                        print(f"   {row_str}")
                
                # Show data quality for key columns
                if table_name == 'universal_cmdb':
                    print(f"\n📊 DATA QUALITY ANALYSIS:")
                    
                    key_columns = [
                        'host', 'domain', 'region', 'country', 'infrastructure_type', 
                        'business_unit', 'present_in_cmdb', 'logging_in_splunk', 
                        'edr_coverage', 'tanium_coverage'
                    ]
                    
                    for col in key_columns:
                        try:
                            filled_count = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
                            percentage = (filled_count / row_count * 100) if row_count > 0 else 0
                            print(f"     • {col:<25} {filled_count:>8,} ({percentage:>5.1f}%)")
                        except:
                            print(f"     • {col:<25} {'Column not found':>15}")
                
                # Show unique values for key categorical columns
                if table_name == 'universal_cmdb' and row_count > 0:
                    print(f"\n🏷️  UNIQUE VALUES IN KEY COLUMNS:")
                    
                    categorical_cols = ['region', 'country', 'infrastructure_type', 'business_unit']
                    for col in categorical_cols:
                        try:
                            unique_query = f"""
                            SELECT {col}, COUNT(*) as count 
                            FROM {table_name} 
                            WHERE {col} IS NOT NULL AND {col} != ''
                            GROUP BY {col} 
                            ORDER BY count DESC 
                            LIMIT 10
                            """
                            unique_values = conn.execute(unique_query).fetchall()
                            
                            if unique_values:
                                print(f"\n     {col.upper()} (top 10):")
                                for value, count in unique_values:
                                    print(f"       • {str(value)[:30]:<30} {count:>6,}")
                        except Exception as e:
                            print(f"     • {col}: Error - {str(e)}")
                
            except Exception as e:
                print(f"   ❌ Error analyzing table {table_name}: {str(e)}")
        
        # 3. Show database metadata
        print(f"\n💾 DATABASE METADATA:")
        try:
            db_info = conn.execute("PRAGMA database_list").fetchall()
            for db in db_info:
                print(f"   Database: {db[1]} (file: {db[2]})")
        except:
            pass
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        return

def check_specific_queries():
    """Test the specific queries that are failing"""
    print(f"\n🧪 TESTING SPECIFIC QUERIES:")
    print("=" * 50)
    
    try:
        conn = duckdb.connect("universal_cmdb.db", read_only=True)
        
        # Test the failing query patterns
        test_queries = [
            "SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(present_in_cmdb) = 'yes'",
            "SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(logging_in_splunk) = 'yes'", 
            "SELECT COUNT(*) FROM universal_cmdb WHERE LOWER(edr_coverage) LIKE '%crowdstrike%'",
            "SELECT region FROM universal_cmdb WHERE region IS NOT NULL LIMIT 5",
            "SELECT country FROM universal_cmdb WHERE country IS NOT NULL LIMIT 5",
            "SELECT present_in_cmdb FROM universal_cmdb WHERE present_in_cmdb IS NOT NULL LIMIT 5",
            "SELECT logging_in_splunk FROM universal_cmdb WHERE logging_in_splunk IS NOT NULL LIMIT 5"
        ]
        
        for query in test_queries:
            try:
                result = conn.execute(query).fetchall()
                print(f"✅ SUCCESS: {query}")
                print(f"   Result: {result[:5]}")  # Show first 5 results
            except Exception as e:
                print(f"❌ FAILED: {query}")
                print(f"   Error: {str(e)}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Could not connect to database: {str(e)}")

if __name__ == "__main__":
    # Check if database path provided as argument
    db_path = sys.argv[1] if len(sys.argv) > 1 else "universal_cmdb.db"
    
    inspect_database(db_path)
    check_specific_queries()
    
    print(f"\n✅ Database inspection complete!")
    print(f"💡 Run with: python inspect_database.py [path_to_db_file]")