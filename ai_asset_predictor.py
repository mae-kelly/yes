import duckdb
import pandas as pd

def diagnose_query_issues():
    db_file = 'universal_cmdb.db'  # Use the working file from previous test
    conn = duckdb.connect(db_file)
    
    print("=== QUERY DIAGNOSTICS ===")
    
    # Step 1: Basic count
    total_records = conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
    print(f"Total records in table: {total_records:,}")
    
    # Step 2: Check fqdn column
    print(f"\n--- FQDN Column Analysis ---")
    fqdn_stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(fqdn) as fqdn_not_null,
            SUM(CASE WHEN fqdn = '' THEN 1 ELSE 0 END) as fqdn_empty,
            SUM(CASE WHEN fqdn IS NOT NULL AND fqdn != '' THEN 1 ELSE 0 END) as fqdn_valid
        FROM universal_cmdb
    """).fetchone()
    print(f"Total: {fqdn_stats[0]:,}, Not NULL: {fqdn_stats[1]:,}, Empty: {fqdn_stats[2]:,}, Valid: {fqdn_stats[3]:,}")
    
    # Step 3: Check data_quality_score column
    print(f"\n--- Data Quality Score Analysis ---")
    quality_stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(data_quality_score) as score_not_null,
            MIN(data_quality_score) as min_score,
            MAX(data_quality_score) as max_score,
            AVG(data_quality_score) as avg_score,
            SUM(CASE WHEN data_quality_score > 3.0 THEN 1 ELSE 0 END) as above_3
        FROM universal_cmdb
    """).fetchone()
    print(f"Total: {quality_stats[0]:,}, Not NULL: {quality_stats[1]:,}")
    print(f"Min: {quality_stats[2]}, Max: {quality_stats[3]}, Avg: {quality_stats[4]:.2f}")
    print(f"Records with score > 3.0: {quality_stats[5]:,}")
    
    # Step 4: Check the combination
    print(f"\n--- Combined Filter Analysis ---")
    combined_stats = conn.execute("""
        SELECT 
            SUM(CASE WHEN fqdn IS NOT NULL THEN 1 ELSE 0 END) as fqdn_not_null,
            SUM(CASE WHEN fqdn != '' THEN 1 ELSE 0 END) as fqdn_not_empty,
            SUM(CASE WHEN data_quality_score > 3.0 THEN 1 ELSE 0 END) as score_above_3,
            SUM(CASE WHEN fqdn IS NOT NULL AND fqdn != '' AND data_quality_score > 3.0 THEN 1 ELSE 0 END) as all_conditions
        FROM universal_cmdb
    """).fetchone()
    print(f"FQDN not null: {combined_stats[0]:,}")
    print(f"FQDN not empty: {combined_stats[1]:,}")  
    print(f"Score > 3.0: {combined_stats[2]:,}")
    print(f"All conditions met: {combined_stats[3]:,}")
    
    # Step 5: Sample the data to see what we're working with
    print(f"\n--- Sample Data ---")
    sample = conn.execute("SELECT fqdn, data_quality_score FROM universal_cmdb LIMIT 10").fetchall()
    for i, row in enumerate(sample, 1):
        print(f"{i:2d}. FQDN: '{row[0]}', Score: {row[1]}")
    
    # Step 6: Try different thresholds
    print(f"\n--- Different Quality Score Thresholds ---")
    for threshold in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]:
        count = conn.execute(f"""
            SELECT COUNT(*) FROM universal_cmdb 
            WHERE fqdn IS NOT NULL AND fqdn != '' AND data_quality_score > {threshold}
        """).fetchone()[0]
        print(f"Score > {threshold}: {count:,} records")
    
    # Step 7: Try without quality score filter
    print(f"\n--- Without Quality Score Filter ---")
    no_quality_filter = conn.execute("""
        SELECT COUNT(*) FROM universal_cmdb 
        WHERE fqdn IS NOT NULL AND fqdn != ''
    """).fetchone()[0]
    print(f"Just FQDN filters: {no_quality_filter:,} records")
    
    # Step 8: Check for NaN or other issues
    print(f"\n--- Data Type Issues ---")
    data_types = conn.execute("DESCRIBE universal_cmdb").fetchall()
    for col_name, col_type, *_ in data_types:
        if col_name in ['fqdn', 'data_quality_score']:
            print(f"{col_name}: {col_type}")
    
    # Step 9: Try the actual query with relaxed filters
    print(f"\n--- Testing Relaxed Query ---")
    relaxed_query = """
        SELECT 
            fqdn, business_unit, data_quality_score
        FROM universal_cmdb
        WHERE fqdn IS NOT NULL AND fqdn != ''
        LIMIT 10
    """
    relaxed_result = conn.execute(relaxed_query).fetchall()
    print(f"Relaxed query returned: {len(relaxed_result)} records")
    for i, row in enumerate(relaxed_result, 1):
        print(f"{i:2d}. FQDN: '{row[0]}', BU: '{row[1]}', Score: {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    diagnose_query_issues()