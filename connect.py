import json
import duckdb
from google.cloud import bigquery
from typing import Dict, List, Set, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HostDataProcessor:
    def __init__(self, gcp_project_id: str, json_file_path: str, duckdb_path: str = "hosts.duckdb"):
        """
        Initialize the processor with BigQuery and DuckDB connections
        
        Args:
            gcp_project_id: Your Google Cloud Project ID
            json_file_path: Path to your JSON metadata file
            duckdb_path: Path for the DuckDB database file
        """
        self.project_id = gcp_project_id
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=gcp_project_id)
        
        # Initialize DuckDB connection
        self.duck_conn = duckdb.connect(duckdb_path)
        
        # Create the hosts table in DuckDB
        self._create_hosts_table()
    
    def _create_hosts_table(self):
        """Create the hosts table in DuckDB if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS unique_hosts (
            table_name VARCHAR,
            column_name VARCHAR,
            column_type VARCHAR,
            host_value VARCHAR,
            extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (table_name, column_name, host_value)
        )
        """
        self.duck_conn.execute(create_table_sql)
        logger.info("Created/verified hosts table in DuckDB")
    
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
            'server_name', 'node_name', 'device_name'
        ]
        
        column_lower = column_name.lower()
        return any(pattern in column_lower for pattern in host_patterns)
    
    def query_bigquery_hosts(self, table_name: str, column_name: str) -> Set[str]:
        """
        Query BigQuery to get unique host values from a specific table/column
        
        Args:
            table_name: BigQuery table name (format: project.dataset.table)
            column_name: Column name containing host data
            
        Returns:
            Set of unique host values
        """
        # Construct the full table reference
        # The table names in your JSON appear to already include project.dataset.table format
        full_table_name = table_name
        
        query = f"""
        SELECT DISTINCT `{column_name}` as host_value
        FROM `{full_table_name}`
        WHERE `{column_name}` IS NOT NULL 
        AND `{column_name}` != ''
        AND `{column_name}` != 'null'
        AND `{column_name}` != 'NULL'
        AND LENGTH(`{column_name}`) > 0
        LIMIT 50000
        """
        
        try:
            logger.info(f"Querying {full_table_name}.{column_name}")
            logger.debug(f"Query: {query}")
            
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            host_values = set()
            for row in results:
                if row.host_value and isinstance(row.host_value, str):
                    host_values.add(row.host_value.strip())
            
            logger.info(f"Found {len(host_values)} unique hosts in {table_name}.{column_name}")
            return host_values
            
        except Exception as e:
            logger.error(f"Error querying {table_name}.{column_name}: {e}")
            return set()
    
    def insert_hosts_to_duckdb(self, table_name: str, column_name: str, column_type: str, host_values: Set[str]):
        """
        Insert unique host values into DuckDB
        
        Args:
            table_name: Source table name
            column_name: Source column name
            column_type: Type of the column (host, domain, etc.)
            host_values: Set of unique host values
        """
        if not host_values:
            logger.warning(f"No host values to insert for {table_name}.{column_name}")
            return
        
        # Prepare data for insertion
        data_to_insert = [
            (table_name, column_name, column_type, host_value)
            for host_value in host_values
        ]
        
        # Insert with ON CONFLICT DO NOTHING to handle duplicates
        insert_sql = """
        INSERT OR IGNORE INTO unique_hosts (table_name, column_name, column_type, host_value)
        VALUES (?, ?, ?, ?)
        """
        
        try:
            self.duck_conn.executemany(insert_sql, data_to_insert)
            logger.info(f"Inserted {len(data_to_insert)} hosts from {table_name}.{column_name}")
        except Exception as e:
            logger.error(f"Error inserting data: {e}")
    
    def process_all_tables(self):
        """
        Main processing function that orchestrates the entire workflow
        """
        logger.info("Starting host data processing...")
        
        # Load metadata
        metadata = self.load_metadata()
        
        # Extract host column information
        host_columns = self.extract_host_columns(metadata)
        
        if not host_columns:
            logger.warning("No host-related columns found in metadata")
            return
        
        # Process each host column
        total_processed = 0
        for table_name, column_name, column_type in host_columns:
            logger.info(f"Processing {table_name}.{column_name} (type: {column_type})")
            
            # Query BigQuery for unique hosts
            host_values = self.query_bigquery_hosts(table_name, column_name)
            
            # Insert into DuckDB
            self.insert_hosts_to_duckdb(table_name, column_name, column_type, host_values)
            
            total_processed += len(host_values)
        
        logger.info(f"Total host values processed: {total_processed}")
        
        # Print summary
        self.print_summary()
        logger.info("Processing complete!")
    
    def print_summary(self):
        """Print a summary of the collected data"""
        # Table-level summary
        table_summary_query = """
        SELECT 
            table_name,
            column_name,
            column_type,
            COUNT(*) as unique_host_count
        FROM unique_hosts 
        GROUP BY table_name, column_name, column_type
        ORDER BY table_name, unique_host_count DESC
        """
        
        results = self.duck_conn.execute(table_summary_query).fetchall()
        
        print("\n" + "="*80)
        print("SUMMARY OF COLLECTED HOST DATA")
        print("="*80)
        
        current_table = None
        total_hosts = 0
        
        for row in results:
            table_name, column_name, column_type, count = row
            
            if current_table != table_name:
                if current_table is not None:
                    print()  # Add space between tables
                current_table = table_name
                print(f"\nTable: {table_name}")
                print("-" * 60)
            
            print(f"  {column_name} ({column_type}): {count} unique hosts")
            total_hosts += count
        
        print(f"\n{'='*80}")
        print(f"TOTAL UNIQUE HOST ENTRIES: {total_hosts}")
        
        # Overall stats
        stats_query = """
        SELECT 
            COUNT(DISTINCT table_name) as total_tables,
            COUNT(DISTINCT column_name) as total_columns,
            COUNT(DISTINCT host_value) as total_unique_hosts,
            COUNT(*) as total_entries
        FROM unique_hosts
        """
        
        stats = self.duck_conn.execute(stats_query).fetchone()
        if stats:
            print(f"Tables processed: {stats[0]}")
            print(f"Columns processed: {stats[1]}")
            print(f"Unique hosts across all tables: {stats[2]}")
        
        # Show some sample data
        sample_query = "SELECT * FROM unique_hosts LIMIT 5"
        sample_results = self.duck_conn.execute(sample_query).fetchall()
        
        print(f"\nSample host entries:")
        print("-" * 60)
        for row in sample_results:
            print(f"  {row[0]}.{row[1]} ({row[2]}) -> {row[3]}")
    
    def export_results(self, output_file: str = "host_analysis.csv"):
        """Export results to CSV for further analysis"""
        export_query = """
        COPY (
            SELECT table_name, column_name, column_type, host_value, extraction_timestamp
            FROM unique_hosts 
            ORDER BY table_name, column_name, host_value
        ) TO ? WITH (FORMAT CSV, HEADER)
        """
        
        try:
            self.duck_conn.execute(export_query, [output_file])
            logger.info(f"Results exported to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
    
    def close_connections(self):
        """Close database connections"""
        self.duck_conn.close()
        logger.info("Closed database connections")

# Usage example
if __name__ == "__main__":
    # Configuration - UPDATE THESE VALUES
    GCP_PROJECT_ID = "your-gcp-project-id"  # Replace with your GCP project ID
    JSON_FILE_PATH = "reviewed_labeled_columns.json"  # Update with correct path
    DUCKDB_PATH = "hosts.duckdb"  # DuckDB database file path
    
    try:
        # Initialize processor
        processor = HostDataProcessor(
            gcp_project_id=GCP_PROJECT_ID,
            json_file_path=JSON_FILE_PATH,
            duckdb_path=DUCKDB_PATH
        )
        
        # Process all tables
        processor.process_all_tables()
        
        # Optionally export results
        processor.export_results("extracted_hosts.csv")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
    finally:
        # Clean up
        if 'processor' in locals():
            processor.close_connections()