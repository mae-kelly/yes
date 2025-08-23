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
        """Create the universal CMDB table in DuckDB with enhanced schema"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR PRIMARY KEY,
            source_tables TEXT,
            infrastructure_type VARCHAR,
            region VARCHAR,
            country VARCHAR,
            data_center VARCHAR,
            cloud_region VARCHAR,
            business_unit VARCHAR,
            cio VARCHAR,
            apm VARCHAR,
            app_class VARCHAR,
            system_classification VARCHAR,
            edr_coverage VARCHAR,
            tanium_coverage VARCHAR,
            dlp_agent_coverage VARCHAR,
            logging_in_splunk VARCHAR,
            logging_in_gso VARCHAR,
            domain VARCHAR,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(create_table_sql)
        
        # Create indexes for faster lookups
        try:
            self.duck_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_normalized_host 
                ON universal_cmdb(normalized_host)
            """)
            self.duck_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_infrastructure_type 
                ON universal_cmdb(infrastructure_type)
            """)
            self.duck_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_business_unit 
                ON universal_cmdb(business_unit)
            """)
        except:
            pass  # Indexes might already exist
        
        logger.info("Created/verified universal CMDB table in DuckDB with enhanced schema")
    
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
            existing_hosts_updated = 0
            
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
                            self._insert_new_host(normalized_host, table_name, original_host)
                            new_hosts_added += 1
                            
                            # Add to cache to avoid duplicate DB checks
                            self.existing_hosts_cache.add(normalized_host)
                            
                            # Log progress every 100 new hosts
                            if new_hosts_added % 100 == 0:
                                logger.info(f"  Added {new_hosts_added} new unique hosts so far...")
                        else:
                            # Host exists, append this table to source_tables
                            self.append_source_table(normalized_host, table_name)
                            existing_hosts_updated += 1
            
            logger.info(f"Completed {table_name}.{column_name}:")
            logger.info(f"  - New unique hosts added: {new_hosts_added}")
            logger.info(f"  - Existing hosts updated: {existing_hosts_updated}")
            logger.info(f"  - Total unique hosts in DB now: {len(self.existing_hosts_cache)}")
            
        except Exception as e:
            logger.error(f"Error processing {table_name}.{column_name}: {e}")
    
    def _insert_new_host(self, normalized_host: str, table_name: str, original_host: str):
        """Insert a new host record into the database with initial values"""
        insert_sql = """
        INSERT OR IGNORE INTO universal_cmdb 
        (normalized_host, source_tables, domain)
        VALUES (?, ?, ?)
        """
        
        try:
            # Extract domain from original host if it contains a dot
            domain = ""
            if '.' in original_host:
                domain = original_host.lower().split('.', 1)[1] if len(original_host.split('.')) > 1 else ""
            
            self.duck_conn.execute(insert_sql, [normalized_host, table_name, domain])
        except Exception as e:
            logger.error(f"Error inserting host {normalized_host}: {e}")
    
    def create_all_sources_table(self):
        """Create an all_sources summary table"""
        try:
            # Drop and recreate the all_sources table
            drop_sql = "DROP TABLE IF EXISTS all_sources"
            self.duck_conn.execute(drop_sql)
            
            create_sql = """
            CREATE TABLE all_sources AS (
                SELECT 
                    normalized_host as host,
                    source_tables,
                    LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count,
                    infrastructure_type,
                    region,
                    country,
                    business_unit,
                    domain,
                    last_updated
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
    
    def update_host_attributes(self, normalized_host: str, **attributes):
        """
        Update specific attributes for a host
        
        Args:
            normalized_host: The normalized hostname
            **attributes: Key-value pairs of attributes to update
        """
        valid_columns = {
            'infrastructure_type', 'region', 'country', 'data_center', 'cloud_region',
            'business_unit', 'cio', 'apm', 'app_class', 'system_classification',
            'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage', 
            'logging_in_splunk', 'logging_in_gso', 'domain'
        }
        
        # Filter out invalid column names
        valid_attributes = {k: v for k, v in attributes.items() if k in valid_columns}
        
        if not valid_attributes:
            logger.warning(f"No valid attributes provided for update: {list(attributes.keys())}")
            return
        
        # Build dynamic update query
        set_clauses = [f"{col} = ?" for col in valid_attributes.keys()]
        set_clause = ", ".join(set_clauses)
        
        update_sql = f"""
        UPDATE universal_cmdb 
        SET {set_clause}, last_updated = CURRENT_TIMESTAMP
        WHERE normalized_host = ?
        """
        
        try:
            values = list(valid_attributes.values()) + [normalized_host]
            self.duck_conn.execute(update_sql, values)
            logger.info(f"Updated {len(valid_attributes)} attributes for host: {normalized_host}")
        except Exception as e:
            logger.error(f"Error updating host attributes for {normalized_host}: {e}")
    
    def bulk_update_from_csv(self, csv_file_path: str):
        """
        Bulk update host attributes from a CSV file
        Expected CSV columns: normalized_host, infrastructure_type, region, country, etc.
        """
        try:
            import csv
            with open(csv_file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                updated_count = 0
                
                for row in reader:
                    normalized_host = row.get('normalized_host')
                    if not normalized_host:
                        continue
                    
                    # Remove normalized_host from attributes
                    attributes = {k: v for k, v in row.items() 
                                if k != 'normalized_host' and v and v.strip()}
                    
                    if attributes:
                        self.update_host_attributes(normalized_host, **attributes)
                        updated_count += 1
                
                logger.info(f"Bulk updated {updated_count} hosts from {csv_file_path}")
        except Exception as e:
            logger.error(f"Error in bulk update from CSV: {e}")
    
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
            COUNT(*) as total_hosts,
            COUNT(CASE WHEN infrastructure_type IS NOT NULL THEN 1 END) as hosts_with_infrastructure_type,
            COUNT(CASE WHEN region IS NOT NULL THEN 1 END) as hosts_with_region,
            COUNT(CASE WHEN business_unit IS NOT NULL THEN 1 END) as hosts_with_business_unit,
            COUNT(CASE WHEN edr_coverage IS NOT NULL THEN 1 END) as hosts_with_edr_coverage,
            AVG(LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1) as avg_source_count
        FROM universal_cmdb
        """
        
        stats = self.duck_conn.execute(stats_query).fetchone()
        
        print("\n" + "="*80)
        print("UNIVERSAL CMDB SUMMARY")
        print("="*80)
        
        if stats:
            print(f"Total unique hosts: {stats[0]}")
            print(f"Hosts with infrastructure type: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
            print(f"Hosts with region info: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
            print(f"Hosts with business unit: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
            print(f"Hosts with EDR coverage info: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
            print(f"Average sources per host: {stats[5]:.1f}")
        
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
        
        # Show infrastructure type distribution
        infra_query = """
        SELECT infrastructure_type, COUNT(*) as count
        FROM universal_cmdb
        WHERE infrastructure_type IS NOT NULL
        GROUP BY infrastructure_type
        ORDER BY count DESC
        """
        infra_results = self.duck_conn.execute(infra_query).fetchall()
        
        if infra_results:
            print(f"\nInfrastructure Type Distribution:")
            print("-" * 50)
            for infra_type, count in infra_results:
                print(f"  {infra_type}: {count} hosts")
        
        # Show business unit distribution
        bu_query = """
        SELECT business_unit, COUNT(*) as count
        FROM universal_cmdb
        WHERE business_unit IS NOT NULL
        GROUP BY business_unit
        ORDER BY count DESC
        """
        bu_results = self.duck_conn.execute(bu_query).fetchall()
        
        if bu_results:
            print(f"\nBusiness Unit Distribution:")
            print("-" * 50)
            for bu, count in bu_results:
                print(f"  {bu}: {count} hosts")
    
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
            source_tables,
            infrastructure_type,
            business_unit,
            region
        FROM universal_cmdb
        WHERE LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 > 1
        ORDER BY source_count DESC, normalized_host
        LIMIT 20
        """
        
        results = self.duck_conn.execute(coverage_query).fetchall()
        
        print(f"\nTop 20 hosts appearing in multiple sources:")
        print("-" * 120)
        for host, source_count, tables, infra_type, bu, region in results:
            print(f"  {host}: {source_count} sources | {infra_type or 'N/A'} | {bu or 'N/A'} | {region or 'N/A'}")
            print(f"    Sources: {tables}")
            print()
    
    def generate_template_csv(self, output_file: str = "cmdb_template.csv"):
        """Generate a template CSV file for bulk updates"""
        template_query = """
        SELECT 
            normalized_host,
            '' as infrastructure_type,
            '' as region,
            '' as country,
            '' as data_center,
            '' as cloud_region,
            '' as business_unit,
            '' as cio,
            '' as apm,
            '' as app_class,
            '' as system_classification,
            '' as edr_coverage,
            '' as tanium_coverage,
            '' as dlp_agent_coverage,
            '' as logging_in_splunk,
            '' as logging_in_gso,
            domain
        FROM universal_cmdb
        ORDER BY normalized_host
        LIMIT 100
        """
        
        try:
            self.duck_conn.execute(f"COPY ({template_query}) TO '{output_file}' WITH (FORMAT CSV, HEADER)")
            logger.info(f"Template CSV generated: {output_file}")
        except Exception as e:
            logger.error(f"Error generating template CSV: {e}")
    
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
        
        # Generate template for manual updates
        processor.generate_template_csv("cmdb_update_template.csv")
        
        print("\n" + "="*80)
        print("UNIVERSAL CMDB CREATION COMPLETE!")
        print(f"Database saved to: {DUCKDB_PATH}")
        print("You can now query the universal_cmdb table or all_sources table")
        print("Use cmdb_update_template.csv to bulk update host attributes")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
    finally:
        # Clean up
        if 'processor' in locals():
            processor.close_connections()