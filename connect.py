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
        
        # Define expected column types and their normalized names
        self.column_type_mapping = {
            'fqdn': 'fqdn',
            'domain': 'domain', 
            'infrastructure_type': 'infrastructure_type',
            'infra_type': 'infrastructure_type',  # Merge with infrastructure_type
            'region': 'region',
            'country': 'country',
            'ip_address': 'ip_address',
            'class': 'class',
            'apm': 'apm',
            'business_unit': 'business_unit',
            'system_classification': 'system_classification',
            'cio': 'cio',
            'data_center': 'data_center',
            'cloud_region': 'cloud_region',
            'logging_in_splunk': 'logging_in_splunk',
            'logging_in_gso': 'logging_in_gso',
            'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage'
        }
        
        # Track discovered columns
        self.discovered_columns = set(['normalized_host', 'source_tables'])
        
        # Cache for existing normalized hosts to speed up lookups
        self.existing_hosts_cache = set()
        
        # First scan to discover all column types, then create table
        self._discover_and_create_table()
    
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
    
    def _discover_and_create_table(self):
        """Discover all column types from metadata and create table with appropriate schema"""
        try:
            metadata = self.load_metadata()
            host_columns = self.extract_host_columns(metadata)
            
            # Discover all unique column types
            for table_name, column_name, column_type in host_columns:
                normalized_type = self.column_type_mapping.get(column_type.lower())
                if normalized_type:
                    self.discovered_columns.add(normalized_type)
            
            logger.info(f"Discovered column types: {sorted(list(self.discovered_columns))}")
            
            # Create table with discovered columns
            self._create_cmdb_table()
            
            # Load existing hosts
            self.existing_hosts_cache = self._load_existing_hosts()
            
        except Exception as e:
            logger.error(f"Error in discovery and table creation: {e}")
            raise
    
    def _create_cmdb_table(self):
        """Create the universal CMDB table in DuckDB with dynamic schema based on discovered columns"""
        # Build column definitions
        column_definitions = [
            "normalized_host VARCHAR PRIMARY KEY",
            "source_tables TEXT"
        ]
        
        # Add discovered columns (excluding the mandatory ones)
        for col in sorted(self.discovered_columns):
            if col not in ['normalized_host', 'source_tables']:
                column_definitions.append(f"{col} TEXT")
        
        # Add timestamp columns
        column_definitions.extend([
            "last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ])
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            {', '.join(column_definitions)}
        )
        """
        
        self.duck_conn.execute(create_table_sql)
        
        # Create indexes for faster lookups
        try:
            self.duck_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_normalized_host 
                ON universal_cmdb(normalized_host)
            """)
            
            # Create indexes on discovered columns
            for col in self.discovered_columns:
                if col not in ['normalized_host', 'source_tables']:
                    try:
                        self.duck_conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS idx_{col}
                            ON universal_cmdb({col})
                        """)
                    except:
                        pass  # Index might already exist or column might not exist yet
        except:
            pass  # Indexes might already exist
        
        logger.info(f"Created/verified universal CMDB table with columns: {sorted(list(self.discovered_columns))}")
    
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
                # Check if this column type is one we're looking for
                if isinstance(column_type, str):
                    normalized_type = self.column_type_mapping.get(column_type.lower())
                    if normalized_type:
                        host_columns.append((table_name, column_name, column_type))
                        logger.info(f"  Found host column: {column_name} (type: {column_type})")
                
                # Also check for host-related column names that might contain actual hostnames
                elif self._is_host_column_name(column_name):
                    host_columns.append((table_name, column_name, 'host'))
                    logger.info(f"  Found host column by name: {column_name} (inferred type: host)")
        
        logger.info(f"Total host-related columns found: {len(host_columns)}")
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
    
    def append_source_table(self, normalized_host: str, table_name: str):
        """
        Append a new source table to the existing source_tables field
        """
        try:
            # Get current source_tables value
            query = "SELECT source_tables FROM universal_cmdb WHERE normalized_host = ?"
            result = self.duck_conn.execute(query, [normalized_host]).fetchone()
            
            if result and result[0]:
                current_tables = result[0]
                # Check if this table is already in the list
                if table_name not in current_tables.split(', '):
                    new_tables = f"{current_tables}, {table_name}"
                else:
                    return  # Table already exists, no update needed
            else:
                new_tables = table_name
            
            # Update the record
            update_query = """
            UPDATE universal_cmdb 
            SET source_tables = ?, last_updated = CURRENT_TIMESTAMP
            WHERE normalized_host = ?
            """
            self.duck_conn.execute(update_query, [new_tables, normalized_host])
            
        except Exception as e:
            logger.error(f"Error appending source table for {normalized_host}: {e}")
    
    def process_and_insert_hosts_incrementally(self, table_name: str, column_name: str, column_type: str):
        """
        Query BigQuery and incrementally insert data into DuckDB
        
        Args:
            table_name: BigQuery table name (format: project.dataset.table)
            column_name: Column name containing data
            column_type: Type of the column (fqdn, domain, infrastructure_type, etc.)
        """
        query = f"""
        SELECT DISTINCT `{column_name}` as column_value
        FROM `{table_name}`
        WHERE `{column_name}` IS NOT NULL 
        AND `{column_name}` != ''
        AND `{column_name}` != 'null'
        AND `{column_name}` != 'NULL'
        AND LENGTH(`{column_name}`) > 0
        LIMIT 100000
        """
        
        try:
            logger.info(f"Querying {table_name}.{column_name} (type: {column_type})")
            
            # Use the same query execution pattern as your Flask app
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            new_hosts_added = 0
            existing_hosts_updated = 0
            data_updates = 0
            
            # Get the normalized column type
            normalized_column_type = self.column_type_mapping.get(column_type.lower())
            
            # Process each value
            for row in results:
                if row.column_value and isinstance(row.column_value, str):
                    column_value = row.column_value.strip()
                    
                    # If this is a host-related column (contains hostnames), extract normalized_host
                    if column_type.lower() in ['host', 'hostname', 'fqdn'] or self._is_host_column_name(column_name):
                        normalized_host = self.normalize_hostname(column_value)
                        
                        # Only process if normalization produced something meaningful
                        if normalized_host and len(normalized_host) > 0:
                            if not self.check_host_exists_in_db(normalized_host):
                                # This is a new unique host, insert it
                                self._insert_new_host(normalized_host, table_name, column_value, normalized_column_type)
                                new_hosts_added += 1
                                self.existing_hosts_cache.add(normalized_host)
                                
                                if new_hosts_added % 100 == 0:
                                    logger.info(f"  Added {new_hosts_added} new unique hosts so far...")
                            else:
                                # Host exists, append this table to source_tables and update data
                                self.append_source_table(normalized_host, table_name)
                                if normalized_column_type:
                                    self._update_host_data(normalized_host, normalized_column_type, column_value)
                                    data_updates += 1
                                existing_hosts_updated += 1
                    else:
                        # This is attribute data, we need to find hosts to attach it to
                        # For now, we'll skip standalone attribute processing
                        # You might want to implement logic to match this data to existing hosts
                        logger.debug(f"Skipping standalone attribute data: {column_value} (type: {column_type})")
            
            logger.info(f"Completed {table_name}.{column_name}:")
            logger.info(f"  - New unique hosts added: {new_hosts_added}")
            logger.info(f"  - Existing hosts updated: {existing_hosts_updated}")
            logger.info(f"  - Data field updates: {data_updates}")
            logger.info(f"  - Total unique hosts in DB now: {len(self.existing_hosts_cache)}")
            
        except Exception as e:
            logger.error(f"Error processing {table_name}.{column_name}: {e}")
    
    def _insert_new_host(self, normalized_host: str, table_name: str, original_value: str, column_type: str = None):
        """Insert a new host record into the database with initial values"""
        try:
            # Start with basic insert
            columns = ['normalized_host', 'source_tables']
            values = [normalized_host, table_name]
            placeholders = ['?', '?']
            
            # Add the column data if we have a column type
            if column_type and column_type in self.discovered_columns:
                columns.append(column_type)
                values.append(original_value)
                placeholders.append('?')
            
            insert_sql = f"""
            INSERT OR IGNORE INTO universal_cmdb 
            ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            """
            
            self.duck_conn.execute(insert_sql, values)
        except Exception as e:
            logger.error(f"Error inserting host {normalized_host}: {e}")
    
    def _update_host_data(self, normalized_host: str, column_type: str, value: str):
        """Update a specific data field for an existing host"""
        if column_type not in self.discovered_columns:
            return
        
        try:
            update_sql = f"""
            UPDATE universal_cmdb 
            SET {column_type} = ?, last_updated = CURRENT_TIMESTAMP
            WHERE normalized_host = ?
            """
            self.duck_conn.execute(update_sql, [value, normalized_host])
        except Exception as e:
            logger.error(f"Error updating {column_type} for host {normalized_host}: {e}")
    
    def create_all_sources_table(self):
        """Create an all_sources summary table"""
        try:
            # Drop and recreate the all_sources table
            drop_sql = "DROP TABLE IF EXISTS all_sources"
            self.duck_conn.execute(drop_sql)
            
            # Build dynamic column list
            data_columns = [col for col in self.discovered_columns 
                           if col not in ['normalized_host', 'source_tables', 'last_updated', 'created_at']]
            
            column_list = ['normalized_host as host', 'source_tables'] + data_columns
            column_list.append("LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count")
            column_list.append('last_updated')
            
            create_sql = f"""
            CREATE TABLE all_sources AS (
                SELECT {', '.join(column_list)}
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                AND normalized_host != ''
                ORDER BY source_count DESC, normalized_host
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
        logger.info(f"Table schema includes columns: {sorted(list(self.discovered_columns))}")
        
        # Load metadata (already loaded during initialization)
        metadata = self.load_metadata()
        
        # Extract host column information
        host_columns = self.extract_host_columns(metadata)
        
        if not host_columns:
            logger.warning("No host-related columns found in metadata")
            return
        
        # Process each column incrementally
        for idx, (table_name, column_name, column_type) in enumerate(host_columns, 1):
            logger.info(f"\nProcessing table {idx}/{len(host_columns)}: {table_name}.{column_name} (type: {column_type})")
            
            # Process and insert data incrementally
            self.process_and_insert_hosts_incrementally(table_name, column_name, column_type)
        
        logger.info(f"\nTotal unique normalized hosts in database: {len(self.existing_hosts_cache)}")
        
        # Create summary tables
        self.create_all_sources_table()
        
        # Print summary
        self.print_summary()
        logger.info("Universal CMDB creation complete!")
    
    def print_summary(self):
        """Print a summary of the collected data"""
        # Get table structure
        columns_query = "PRAGMA table_info(universal_cmdb)"
        columns_info = self.duck_conn.execute(columns_query).fetchall()
        
        print("\n" + "="*80)
        print("UNIVERSAL CMDB SUMMARY")
        print("="*80)
        print(f"Table columns: {[col[1] for col in columns_info]}")
        
        # Overall stats
        stats_query = "SELECT COUNT(*) as total_hosts FROM universal_cmdb"
        stats = self.duck_conn.execute(stats_query).fetchone()
        
        if stats:
            print(f"Total unique hosts: {stats[0]}")
        
        # Show data population for each discovered column
        for col in sorted(self.discovered_columns):
            if col not in ['normalized_host', 'source_tables', 'last_updated', 'created_at']:
                count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
                try:
                    count = self.duck_conn.execute(count_query).fetchone()
                    if count:
                        percentage = (count[0] / stats[0] * 100) if stats[0] > 0 else 0
                        print(f"Hosts with {col}: {count[0]} ({percentage:.1f}%)")
                except Exception as e:
                    logger.warning(f"Could not get count for column {col}: {e}")
        
        # Top hosts by source count
        top_hosts_query = """
        SELECT 
            normalized_host, 
            LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count,
            source_tables
        FROM universal_cmdb
        ORDER BY source_count DESC, normalized_host
        LIMIT 10
        """
        
        top_hosts = self.duck_conn.execute(top_hosts_query).fetchall()
        
        print(f"\nTop 10 hosts by source count:")
        print("-" * 100)
        for host, count, tables in top_hosts:
            print(f"  {host}: appears in {count} different tables")
            print(f"    Tables: {tables[:80]}{'...' if len(tables) > 80 else ''}")
        
        # Sample data
        sample_query = f"SELECT * FROM universal_cmdb LIMIT 3"
        sample_results = self.duck_conn.execute(sample_query).fetchall()
        
        if sample_results:
            print(f"\nSample entries:")
            print("-" * 120)
            column_names = [col[1] for col in columns_info]
            for row in sample_results:
                for i, value in enumerate(row):
                    if value and str(value).strip():
                        print(f"  {column_names[i]}: {value}")
                print()
    
    def export_results(self, output_file: str = "universal_cmdb_export.csv"):
        """Export results to CSV for further analysis"""
        export_query = """
        COPY (
            SELECT * FROM universal_cmdb 
            ORDER BY normalized_host
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
            LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count,
            source_tables
        FROM universal_cmdb
        WHERE LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 > 1
        ORDER BY source_count DESC, normalized_host
        LIMIT 20
        """
        
        results = self.duck_conn.execute(coverage_query).fetchall()
        
        print(f"\nTop 20 hosts appearing in multiple sources:")
        print("-" * 120)
        for host, source_count, tables in results:
            print(f"  {host}: {source_count} sources")
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