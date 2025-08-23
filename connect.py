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
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
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
            'dlp_agent_coverage': 'dlp_agent_coverage',
            'host': 'host',  # Special case for hostname data
            'hostname': 'hostname'  # Special case for hostname data
        }
        
        # Define which column types contain hostnames (used to create normalized_host)
        self.hostname_types = {'host', 'hostname', 'fqdn'}
        
        # Track discovered columns
        self.discovered_columns = set(['normalized_host', 'source_tables'])
        
        # Cache for existing normalized hosts to speed up lookups
        self.existing_hosts_cache = set()
        
        # Store all column information for processing
        self.all_columns_info = []
        
        # First scan to discover all column types, then create table
        self._discover_and_create_table()
    
    def _initialize_bigquery_client(self):
        """Initialize BigQuery client using service account like in your Flask app"""
        try:
            # Try to get service account file from environment or settings
            service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
            
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
            self.all_columns_info = self.extract_host_columns(metadata)
            
            # Discover all unique column types
            for table_name, column_name, column_type in self.all_columns_info:
                normalized_type = self.column_type_mapping.get(column_type.lower())
                if normalized_type:
                    self.discovered_columns.add(normalized_type)
                # Also add host-inferred columns
                elif self._is_host_column_name(column_name):
                    self.discovered_columns.add('hostname')
            
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
        Extract ALL columns that have recognized column types from the JSON metadata
        
        Returns:
            List of tuples: (table_name, column_name, column_type)
        """
        all_columns = []
        
        if 'columns' not in metadata:
            logger.error("No 'columns' key found in metadata")
            return all_columns
        
        for table_name, columns in metadata['columns'].items():
            logger.info(f"Processing table: {table_name}")
            
            for column_name, column_type in columns.items():
                # Check if this column type is one we're looking for
                if isinstance(column_type, str):
                    normalized_type = self.column_type_mapping.get(column_type.lower())
                    if normalized_type:
                        all_columns.append((table_name, column_name, column_type))
                        logger.info(f"  Found column: {column_name} (type: {column_type})")
                
                # Also check for host-related column names that might contain actual hostnames
                elif self._is_host_column_name(column_name):
                    all_columns.append((table_name, column_name, 'hostname'))
                    logger.info(f"  Found host column by name: {column_name} (inferred type: hostname)")
        
        logger.info(f"Total relevant columns found: {len(all_columns)}")
        return all_columns
    
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
    
    def get_all_hosts_for_linking(self) -> Dict[str, str]:
        """
        Get all existing hosts and their original values for linking attribute data
        Returns dict: {original_value: normalized_host}
        """
        query = """
        SELECT normalized_host, hostname, fqdn, host 
        FROM universal_cmdb
        """
        
        host_mapping = {}
        try:
            results = self.duck_conn.execute(query).fetchall()
            for row in results:
                normalized_host = row[0]
                # Add mappings for all non-null original values
                for original_value in row[1:]:  # hostname, fqdn, host columns
                    if original_value:
                        host_mapping[original_value.lower()] = normalized_host
                        # Also add normalized version
                        host_mapping[self.normalize_hostname(original_value)] = normalized_host
        except Exception as e:
            logger.error(f"Error getting host mappings: {e}")
        
        return host_mapping
    
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
            normalized_column_type = self.column_type_mapping.get(column_type.lower(), column_type.lower())
            
            # Check if this column type contains hostnames
            is_hostname_column = (column_type.lower() in self.hostname_types or 
                                self._is_host_column_name(column_name))
            
            # For attribute columns, get existing host mappings
            host_mapping = {}
            if not is_hostname_column:
                # For attribute data, we need to get hosts from a hostname query first
                # This is a simplified approach - you might need to modify based on your data relationships
                logger.info(f"  Processing attribute column - getting existing hosts for linking")
                host_mapping = self.get_all_hosts_for_linking()
            
            # Process each value
            processed_count = 0
            for row in results:
                if row.column_value and isinstance(row.column_value, str):
                    column_value = row.column_value.strip()
                    processed_count += 1
                    
                    if processed_count % 1000 == 0:
                        logger.info(f"  Processed {processed_count} values...")
                    
                    if is_hostname_column:
                        # This column contains hostnames - create/update normalized_host entries
                        normalized_host = self.normalize_hostname(column_value)
                        
                        if normalized_host and len(normalized_host) > 0:
                            if not self.check_host_exists_in_db(normalized_host):
                                # New host
                                self._insert_new_host(normalized_host, table_name, column_value, normalized_column_type)
                                new_hosts_added += 1
                                self.existing_hosts_cache.add(normalized_host)
                                
                                if new_hosts_added % 100 == 0:
                                    logger.info(f"  Added {new_hosts_added} new unique hosts so far...")
                            else:
                                # Existing host - update source table and data
                                self.append_source_table(normalized_host, table_name)
                                self._update_host_data(normalized_host, normalized_column_type, column_value)
                                existing_hosts_updated += 1
                    else:
                        # This is attribute data - try to link it to existing hosts
                        linked_hosts = self._find_hosts_for_attribute(column_value, host_mapping, table_name)
                        
                        for linked_host in linked_hosts:
                            self.append_source_table(linked_host, table_name)
                            self._update_host_data(linked_host, normalized_column_type, column_value)
                            data_updates += 1
            
            logger.info(f"Completed {table_name}.{column_name}:")
            logger.info(f"  - New unique hosts added: {new_hosts_added}")
            logger.info(f"  - Existing hosts updated: {existing_hosts_updated}")
            logger.info(f"  - Data field updates: {data_updates}")
            logger.info(f"  - Total values processed: {processed_count}")
            logger.info(f"  - Total unique hosts in DB now: {len(self.existing_hosts_cache)}")
            
        except Exception as e:
            logger.error(f"Error processing {table_name}.{column_name}: {e}")
    
    def _find_hosts_for_attribute(self, attribute_value: str, host_mapping: Dict[str, str], table_name: str) -> List[str]:
        """
        Find hosts that this attribute value should be linked to
        For now, this is a simple approach - you might need more sophisticated linking logic
        """
        # For attribute data, we could:
        # 1. Try to extract hostname from the attribute value if it contains one
        # 2. Look for hosts from the same table
        # 3. Use other linking strategies
        
        linked_hosts = []
        
        # Strategy 1: If the attribute value looks like it contains a hostname, extract it
        if '.' in attribute_value or any(c.isdigit() for c in attribute_value):
            potential_host = self.normalize_hostname(attribute_value)
            if potential_host in host_mapping.values():
                linked_hosts.append(potential_host)
        
        # Strategy 2: Get all hosts that come from the same table
        if not linked_hosts:
            try:
                query = """
                SELECT normalized_host 
                FROM universal_cmdb 
                WHERE source_tables LIKE ?
                LIMIT 1000
                """
                results = self.duck_conn.execute(query, [f"%{table_name}%"]).fetchall()
                linked_hosts = [row[0] for row in results]
            except Exception as e:
                logger.debug(f"Error finding hosts by table: {e}")
        
        return linked_hosts[:100]  # Limit to prevent excessive updates
    
    def _insert_new_host(self, normalized_host: str, table_name: str, original_value: str, column_type: str = None):
        """Insert a new host record into the database with initial values"""
        try:
            # Start with basic insert
            columns = ['normalized_host', 'source_tables']
            values = [normalized_host, table_name]
            placeholders = ['?', '?']
            
            # Add the column data if we have a column type and it exists in our schema
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
            logger.debug(f"Column type {column_type} not in discovered columns, skipping update")
            return
        
        try:
            # Check if column exists in table
            columns_query = "PRAGMA table_info(universal_cmdb)"
            existing_columns = {col[1] for col in self.duck_conn.execute(columns_query).fetchall()}
            
            if column_type not in existing_columns:
                logger.debug(f"Column {column_type} does not exist in table, skipping update")
                return
            
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
        
        if not self.all_columns_info:
            logger.warning("No relevant columns found in metadata")
            return
        
        # Process hostname columns first to establish hosts
        hostname_columns = [(t, c, ct) for t, c, ct in self.all_columns_info 
                           if ct.lower() in self.hostname_types or self._is_host_column_name(c)]
        
        attribute_columns = [(t, c, ct) for t, c, ct in self.all_columns_info 
                            if (t, c, ct) not in hostname_columns]
        
        logger.info(f"Processing {len(hostname_columns)} hostname columns first...")
        
        # Process hostname columns first
        for idx, (table_name, column_name, column_type) in enumerate(hostname_columns, 1):
            logger.info(f"\nProcessing hostname column {idx}/{len(hostname_columns)}: {table_name}.{column_name} (type: {column_type})")
            self.process_and_insert_hosts_incrementally(table_name, column_name, column_type)
        
        logger.info(f"\nProcessing {len(attribute_columns)} attribute columns...")
        
        # Process attribute columns
        for idx, (table_name, column_name, column_type) in enumerate(attribute_columns, 1):
            logger.info(f"\nProcessing attribute column {idx}/{len(attribute_columns)}: {table_name}.{column_name} (type: {column_type})")
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
                    if count and stats:
                        percentage = (count[0] / stats[0] * 100) if stats[0] > 0 else 0
                        print(f"Hosts with {col}: {count[0]} ({percentage:.1f}%)")
                except Exception as e:
                    logger.warning(f"Could not get count for column {col}: {e}")
        
        # Show sample of populated data
        sample_query = """
        SELECT * FROM universal_cmdb 
        WHERE normalized_host IS NOT NULL
        LIMIT 5
        """
        
        try:
            sample_results = self.duck_conn.execute(sample_query).fetchall()
            column_names = [col[1] for col in columns_info]
            
            if sample_results:
                print(f"\nSample entries with data:")
                print("-" * 120)
                for row in sample_results:
                    print(f"Host: {row[0]}")
                    for i, value in enumerate(row[1:], 1):
                        if value and str(value).strip() and column_names[i] not in ['last_updated', 'created_at']:
                            print(f"  {column_names[i]}: {value}")
                    print()
        except Exception as e:
            logger.error(f"Error showing sample data: {e}")
    
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
    DUCKDB_PATH = "universal_cmdb.db"  # Universal CMDB database file path
    
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