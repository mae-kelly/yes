import json
import duckdb
import os
import re
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HostDataProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.duckdb"):
        """
        Initialize the processor with BigQuery and DuckDB connections
        
        Args:
            json_file_path: Path to your JSON metadata file
            duckdb_path: Path for the DuckDB database file
        """
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Initialize BigQuery client using same method as your Flask app
        self.bq_client = self._initialize_bigquery_client()
        
        # Initialize DuckDB connection
        self.duck_conn = duckdb.connect(duckdb_path)
        
        # Create the universal CMDB table in DuckDB
        self._create_cmdb_table()
        
        # Cache for existing normalized hosts to speed up lookups
        self.existing_hosts_cache = self._load_existing_hosts()
    
    def _initialize_bigquery_client(self):
        """Initialize BigQuery client using service account like in your Flask app"""
        try:
            # Try to get service account file from environment or settings
            service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp_prod_key.json')
            
            if os.path.exists(service_account_file):
                credentials = service_account.Credentials.from_service_account_file(service_account_file)
                client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
                logger.info("Initialized BigQuery client with service account")
            else:
                # Fallback to default credentials
                client = bigquery.Client(project="chronicle-fisv")
                logger.info("Initialized BigQuery client with default credentials")
            
            return client
        except Exception as e:
            logger.error(f"Error initializing BigQuery client: {e}")
            raise
    
    def _create_cmdb_table(self):
        """Create the universal CMDB table in DuckDB"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            source_table VARCHAR,
            source_column VARCHAR,
            column_type VARCHAR,
            original_host VARCHAR,
            normalized_host VARCHAR,
            extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source_table, source_column, normalized_host)
        )
        """
        self.duck_conn.execute(create_table_sql)
        
        # Create index for faster lookups
        try:
            self.duck_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_normalized_host 
                ON universal_cmdb(normalized_host)
            """)
        except:
            pass  # Index might already exist
        
        logger.info("Created/verified universal CMDB table in DuckDB")
    
    def _load_existing_hosts(self) -> Set[str]:
        """Load existing normalized hosts into memory for faster lookups"""
        try:
            query = "SELECT DISTINCT normalized_host FROM universal_cmdb"
            results = self.duck_conn.execute(query).fetchall()
            existing_hosts = {row[0] for row in results if row[0]}
            logger.info(f"Loaded {len(existing_hosts)} existing normalized hosts into cache")
            return existing_hosts
        except Exception as e:
            logger.warning(f"Could not load existing hosts (may be first run): {e}")
            return set()
    
    def load_metadata(self) -> Dict:
        """Load and parse the JSON metadata file"""
        try:
            with open(self.json_file_path, 'r') as f:
                metadata = json.load(f)
            logger.info(f"Loaded metadata from {self.json_file_path}")
            return metadata
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            raise
    
    def normalize_hostname(self, hostname: str) -> str:
        """
        Normalize hostname according to your requirements:
        - Convert to lowercase
        - Remove dashes
        - Remove anything after "."
        """
        if not hostname or not isinstance(hostname, str):
            return ""
        
        # Convert to lowercase
        normalized = hostname.lower().strip()
        
        # Remove anything after the first dot
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        # Remove dashes
        normalized = normalized.replace('-', '')
        
        # Remove any remaining special characters except alphanumeric
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized
    
    def extract_host_columns(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        """
        Extract host-related columns from the JSON metadata
        
        Returns:
            List of tuples: (table_name, column_name, column_type)
        """
        host_columns = []
        
        if 'columns' not in metadata:
            logger.error("No 'columns' key found in metadata")
            return host_columns
        
        for table_name, columns in metadata['columns'].items():
            logger.info(f"Processing table: {table_name}")
            
            for column_name, column_type in columns.items():
                # Check if this column contains host data
                # Based on your JSON, host columns have values like "host", "domain"
                if isinstance(column_type, str) and column_type.lower() in ['host', 'domain', 'hostname']:
                    host_columns.append((table_name, column_name, column_type))
                    logger.info(f"  Found host column: {column_name} (type: {column_type})")
                
                # Also check for specific host-related column names
                elif self._is_host_column_name(column_name):
                    host_columns.append((table_name, column_name, str(column_type)))
                    logger.info(f"  Found host column by name: {column_name}")
        
        logger.info(f"Total host columns found: {len(host_columns)}")
        return host_columns
    
    def _is_host_column_name(self, column_name: str) -> bool:
        """Check if column name indicates host data"""
        host_patterns = [
            'host', 'hostname', 'endpoint_name', 'endpointdomain_name',
            'splunk_host', 'app_host', 'chronicle_device_hostname',
            'server_name', 'node_name', 'device_name', 'device_hostname'
        ]
        
        column_lower = column_name.lower()
        return any(pattern in column_lower for pattern in host_patterns)
    
    def check_host_exists_in_db(self, normalized_host: str) -> bool:
        """
        Check if a normalized host already exists in the database
        Uses cache first, then falls back to database query if needed
        """
        # First check cache
        if normalized_host in self.existing_hosts_cache:
            return True
        
        # Double-check database in case cache is out of sync
        query = """
        SELECT COUNT(*) as count 
        FROM universal_cmdb 
        WHERE normalized_host = ?
        """
        
        try:
            result = self.duck_conn.execute(query, [normalized_host]).fetchone()
            exists = result[0] > 0 if result else False
            
            # Update cache if host exists but wasn't in cache
            if exists:
                self.existing_hosts_cache.add(normalized_host)
            
            return exists
        except Exception as e:
            logger.error(f"Error checking host existence: {e}")
            return False
    
    def process_and_insert_hosts_incrementally(self, table_name: str, column_name: str, column_type: str):
        """
        Query BigQuery and incrementally insert only unique hosts into DuckDB
        
        Args:
            table_name: BigQuery table name (format: project.dataset.table)
            column_name: Column name containing host data
            column_type: Type of the column (host, domain, etc.)
        """
        query = f"""
        SELECT DISTINCT `{column_name}` as host_value
        FROM `{table_name}`
        WHERE `{column_name}` IS NOT NULL 
        AND `{column_name}` != ''
        AND `{column_name}` != 'null'
        AND `{column_name}` != 'NULL'
        AND LENGTH(`{column_name}`) > 0
        LIMIT 100000
        """
        
        try:
            logger.info(f"Querying {table_name}.{column_name}")
            
            # Use the same query execution pattern as your Flask app
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            new_hosts_added = 0
            duplicate_hosts_skipped = 0
            
            # Process each host value as it comes
            for row in results:
                if row.host_value and isinstance(row.host_value, str):
                    original_host = row.host_value.strip()
                    normalized_host = self.normalize_hostname(original_host)
                    
                    # Only process if normalization produced something meaningful
                    if normalized_host and len(normalized_host) > 0:
                        # Check if this normalized host already exists in our database
                        if not self.check_host_exists_in_db(normalized_host):
                            # This is a new unique host, insert it
                            self._insert_single_host(table_name, column_name, column_type, 
                                                    original_host, normalized_host)
                            new_hosts_added += 1
                            
                            # Add to cache to avoid duplicate DB checks
                            self.existing_hosts_cache.add(normalized_host)
                            
                            # Log progress every 100 new hosts
                            if new_hosts_added % 100 == 0:
                                logger.info(f"  Added {new_hosts_added} new unique hosts so far...")
                        else:
                            duplicate_hosts_skipped += 1
                            
                            # Optionally, you might want to track which tables also have this host
                            # by inserting a record with the same normalized_host but different source
                            if self._should_track_duplicate_source(table_name, column_name, normalized_host):
                                self._insert_single_host(table_name, column_name, column_type,
                                                        original_host, normalized_host)
            
            logger.info(f"Completed {table_name}.{column_name}:")
            logger.info(f"  - New unique hosts added: {new_hosts_added}")
            logger.info(f"  - Duplicate hosts skipped: {duplicate_hosts_skipped}")
            logger.info(f"  - Total unique hosts in DB now: {len(self.existing_hosts_cache)}")
            
        except Exception as e:
            logger.error(f"Error processing {table_name}.{column_name}: {e}")
    
    def _should_track_duplicate_source(self, table_name: str, column_name: str, normalized_host: str) -> bool:
        """
        Check if we should track this source for an existing normalized host
        (i.e., this table/column combination hasn't been recorded for this host yet)
        """
        query = """
        SELECT COUNT(*) as count
        FROM universal_cmdb
        WHERE source_table = ?
        AND source_column = ?
        AND normalized_host = ?
        """
        
        try:
            result = self.duck_conn.execute(query, [table_name, column_name, normalized_host]).fetchone()
            return result[0] == 0 if result else True
        except Exception as e:
            logger.error(f"Error checking duplicate source: {e}")
            return False
    
    def _insert_single_host(self, table_name: str, column_name: str, column_type: str,
                           original_host: str, normalized_host: str):
        """Insert a single host record into the database"""
        insert_sql = """
        INSERT OR IGNORE INTO universal_cmdb 
        (source_table, source_column, column_type, original_host, normalized_host)
        VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            self.duck_conn.execute(insert_sql, 
                                  [table_name, column_name, column_type, original_host, normalized_host])
        except Exception as e:
            logger.error(f"Error inserting host {normalized_host}: {e}")
    
    def create_all_sources_table(self):
        """Create an all_sources summary table like in your Flask app"""
        try:
            # Drop and recreate the all_sources table
            drop_sql = "DROP TABLE IF EXISTS all_sources"
            self.duck_conn.execute(drop_sql)
            
            create_sql = """
            CREATE TABLE all_sources AS (
                SELECT DISTINCT
                    normalized_host as host,
                    source_table as source_table,
                    source_column as source_column,
                    column_type as type,
                    COUNT(*) OVER (PARTITION BY normalized_host) as source_count
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                AND normalized_host != ''
                ORDER BY normalized_host, source_table
            )
            """
            self.duck_conn.execute(create_sql)
            logger.info("Created all_sources summary table")
        except Exception as e:
            logger.error(f"Error creating all_sources table: {e}")
    
    def process_all_tables(self):
        """
        Main processing function that orchestrates the entire workflow
        """
        logger.info("Starting universal CMDB creation...")
        logger.info(f"Starting with {len(self.existing_hosts_cache)} existing hosts in database")
        
        # Load metadata
        metadata = self.load_metadata()
        
        # Extract host column information
        host_columns = self.extract_host_columns(metadata)
        
        if not host_columns:
            logger.warning("No host-related columns found in metadata")
            return
        
        # Process each host column incrementally
        for idx, (table_name, column_name, column_type) in enumerate(host_columns, 1):
            logger.info(f"\nProcessing table {idx}/{len(host_columns)}: {table_name}.{column_name} (type: {column_type})")
            
            # Process and insert hosts incrementally, checking for uniqueness
            self.process_and_insert_hosts_incrementally(table_name, column_name, column_type)
        
        logger.info(f"\nTotal unique normalized hosts in database: {len(self.existing_hosts_cache)}")
        
        # Create summary tables
        self.create_all_sources_table()
        
        # Print summary
        self.print_summary()
        logger.info("Universal CMDB creation complete!")
    
    def print_summary(self):
        """Print a summary of the collected data"""
        # Overall stats
        stats_query = """
        SELECT 
            COUNT(DISTINCT source_table) as total_tables,
            COUNT(DISTINCT source_column) as total_columns,
            COUNT(DISTINCT normalized_host) as total_unique_normalized_hosts,
            COUNT(DISTINCT original_host) as total_unique_original_hosts,
            COUNT(*) as total_entries
        FROM universal_cmdb
        """
        
        stats = self.duck_conn.execute(stats_query).fetchone()
        
        print("\n" + "="*80)
        print("UNIVERSAL CMDB SUMMARY")
        print("="*80)
        
        if stats:
            print(f"Tables processed: {stats[0]}")
            print(f"Columns processed: {stats[1]}")
            print(f"Unique normalized hosts: {stats[2]}")
            print(f"Unique original hosts: {stats[3]}")
            print(f"Total entries: {stats[4]}")
        
        # Top normalized hosts by source count
        top_hosts_query = """
        SELECT normalized_host, COUNT(DISTINCT source_table) as source_count
        FROM universal_cmdb
        GROUP BY normalized_host
        ORDER BY source_count DESC, normalized_host
        LIMIT 10
        """
        
        top_hosts = self.duck_conn.execute(top_hosts_query).fetchall()
        
        print(f"\nTop 10 hosts by source count:")
        print("-" * 60)
        for host, count in top_hosts:
            print(f"  {host}: appears in {count} different tables")
        
        # Show some sample data
        sample_query = """
        SELECT source_table, source_column, original_host, normalized_host 
        FROM universal_cmdb 
        LIMIT 5
        """
        sample_results = self.duck_conn.execute(sample_query).fetchall()
        
        print(f"\nSample normalized entries:")
        print("-" * 80)
        for row in sample_results:
            print(f"  {row[0]}.{row[1]}: '{row[2]}' -> '{row[3]}'")
        
        # Coverage by table
        coverage_query = """
        SELECT source_table, 
               COUNT(DISTINCT normalized_host) as unique_hosts,
               COUNT(*) as total_entries
        FROM universal_cmdb
        GROUP BY source_table
        ORDER BY unique_hosts DESC
        """
        
        coverage_results = self.duck_conn.execute(coverage_query).fetchall()
        
        print(f"\nCoverage by source table:")
        print("-" * 80)
        for table, unique_hosts, total_entries in coverage_results:
            print(f"  {table}: {unique_hosts} unique hosts ({total_entries} total entries)")
        
        # Show growth statistics
        print(f"\nGrowth Statistics:")
        print("-" * 80)
        print(f"  Started with: {len(self._load_existing_hosts())} hosts")
        print(f"  Ended with: {len(self.existing_hosts_cache)} hosts")
        print(f"  New hosts added: {len(self.existing_hosts_cache) - len(self._load_existing_hosts())}")
    
    def export_results(self, output_file: str = "universal_cmdb_export.csv"):
        """Export results to CSV for further analysis"""
        export_query = """
        COPY (
            SELECT source_table, source_column, column_type, 
                   original_host, normalized_host, extraction_timestamp
            FROM universal_cmdb 
            ORDER BY source_table, source_column, normalized_host
        ) TO ? WITH (FORMAT CSV, HEADER)
        """
        
        try:
            self.duck_conn.execute(export_query, [output_file])
            logger.info(f"Universal CMDB exported to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
    
    def get_host_coverage_stats(self):
        """Get coverage statistics for hosts across different sources"""
        coverage_query = """
        SELECT 
            normalized_host,
            COUNT(DISTINCT source_table) as table_count,
            COUNT(DISTINCT source_column) as column_count,
            STRING_AGG(DISTINCT source_table, ', ') as source_tables
        FROM universal_cmdb
        GROUP BY normalized_host
        HAVING table_count > 1
        ORDER BY table_count DESC, normalized_host
        """
        
        results = self.duck_conn.execute(coverage_query).fetchall()
        
        print(f"\nHosts appearing in multiple sources:")
        print("-" * 100)
        for host, table_count, column_count, tables in results[:20]:  # Show top 20
            print(f"  {host}: {table_count} tables, {column_count} columns")
            print(f"    Sources: {tables}")
            print()
    
    def close_connections(self):
        """Close database connections"""
        self.duck_conn.close()
        logger.info("Closed database connections")

# Usage example
if __name__ == "__main__":
    # Configuration
    JSON_FILE_PATH = "reviewed_labeled_columns.json"  # Update with correct path
    DUCKDB_PATH = "universal_cmdb.duckdb"  # Universal CMDB database file path
    
    try:
        # Initialize processor
        processor = HostDataProcessor(
            json_file_path=JSON_FILE_PATH,
            duckdb_path=DUCKDB_PATH
        )
        
        # Process all tables and create universal CMDB
        processor.process_all_tables()
        
        # Get additional coverage statistics
        processor.get_host_coverage_stats()
        
        # Export results
        processor.export_results("universal_cmdb_export.csv")
        
        print("\n" + "="*80)
        print("UNIVERSAL CMDB CREATION COMPLETE!")
        print(f"Database saved to: {DUCKDB_PATH}")
        print("You can now query the universal_cmdb table or all_sources table")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
    finally:
        # Clean up
        if 'processor' in locals():
            processor.close_connections()