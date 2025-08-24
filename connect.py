import json
import duckdb
import os
import re
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple, Optional
import logging
from collections import defaultdict
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class FastCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        print("\n" + "═" * 80)
        print(" " * 25 + "FAST CMDB PROCESSOR")
        print("═" * 80 + "\n")
        
        logger.info("Starting initialization...")
        print(f"Configuration:")
        print(f"  JSON File: {json_file_path}")
        print(f"  Database: {duckdb_path}")
        print()
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Thread-safe lock for database operations
        self.db_lock = threading.Lock()
        
        # Pre-compiled regex patterns
        self.normalize_pattern = re.compile(r'[^a-z0-9]')
        
        # Column mappings
        self.column_mapping = {
            'fqdn': 'fqdn',
            'domain': 'domain',
            'host': 'hostname',
            'hostname': 'hostname',
            'infrastructure_type': 'infrastructure_type',
            'infra_type': 'infrastructure_type',
            'region': 'region',
            'country': 'country',
            'data_center': 'data_center',
            'datacenter': 'data_center',
            'cloud_region': 'cloud_region',
            'ip_address': 'ip_address',
            'ip': 'ip_address',
            'class': 'class',
            'system_classification': 'system_classification',
            'business_unit': 'business_unit',
            'bu': 'business_unit',
            'apm': 'apm',
            'cio': 'cio',
            'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk',
            'logging_in_gso': 'logging_in_gso'
        }
        
        self.hostname_patterns = [
            'host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name',
            'endpoint_name', 'splunk_host', 'app_host', 'computer_name', 'machine_name',
            'chronicle_device_hostname', 'endpointdomain_name', 'asset_name'
        ]
        
        self.advanced_patterns = {
            'business_unit': ['business_unit', 'bu', 'business', 'department', 'division', 'org_unit'],
            'region': ['region', 'location', 'site', 'area', 'zone', 'geographic_region'],
            'country': ['country', 'nation', 'country_code', 'geo_country'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type', 'system_type', 'platform', 'environment', 'env'],
            'data_center': ['datacenter', 'data_center', 'dc', 'facility', 'center'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip'],
            'class': ['class', 'classification', 'tier', 'level'],
            'system_classification': ['system_classification', 'security_classification'],
            'apm': ['apm', 'monitoring', 'application_monitoring'],
            'cio': ['cio', 'owner', 'responsible', 'contact'],
            'edr_coverage': ['edr_coverage', 'edr', 'endpoint_detection'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'tanium_agent'],
            'dlp_agent_coverage': ['dlp_agent_coverage', 'dlp', 'data_loss_prevention'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk', 'splunk_logging'],
            'logging_in_gso': ['logging_in_gso', 'gso', 'gso_logging'],
            'domain': ['domain', 'dns_domain', 'ad_domain'],
            'fqdn': ['fqdn', 'full_name', 'qualified_name']
        }
        
        self.stats = defaultdict(int)
        self.global_hosts_seen = set()  # Track all hosts globally
        
        # Initialize connections
        logger.info("Initializing BigQuery connection...")
        self._init_bigquery()
        
        # Single DuckDB connection (not thread-safe, will use lock)
        logger.info("Initializing DuckDB connection...")
        self.duck_conn = duckdb.connect(duckdb_path)
        logger.info("Creating database schema...")
        
        self._create_optimized_table()
        self._load_existing_hosts()
        
        logger.info("Initialization complete")
        print("─" * 60 + "\n")
    
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
    
    def _create_optimized_table(self):
        create_sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR PRIMARY KEY,
            source_tables TEXT,
            hostname TEXT,
            fqdn TEXT,
            domain TEXT,
            infrastructure_type TEXT,
            region TEXT,
            country TEXT,
            data_center TEXT,
            cloud_region TEXT,
            ip_address TEXT,
            class TEXT,
            system_classification TEXT,
            business_unit TEXT,
            apm TEXT,
            cio TEXT,
            edr_coverage TEXT,
            tanium_coverage TEXT,
            dlp_agent_coverage TEXT,
            logging_in_splunk TEXT,
            logging_in_gso TEXT,
            data_quality_score FLOAT DEFAULT 1.0,
            source_count INTEGER DEFAULT 1,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(create_sql)
        
        # Create indexes
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)")
        except:
            pass
    
    def _load_existing_hosts(self):
        """Load existing hosts into memory to prevent duplicates"""
        logger.info("Loading existing hosts from database...")
        try:
            existing = self.duck_conn.execute("SELECT normalized_host FROM universal_cmdb").fetchall()
            self.global_hosts_seen = set(row[0] for row in existing)
            logger.info(f"Successfully loaded {len(self.global_hosts_seen):,} existing hosts")
            print(f"  Existing hosts in database: {len(self.global_hosts_seen):,}\n")
        except:
            logger.info("No existing hosts found (new database)")
            print("  Starting with empty database\n")
    
    def normalize_hostname(self, hostname: str) -> str:
        """Optimized hostname normalization"""
        if not hostname or not isinstance(hostname, str) or hostname.strip() == '*Undefined':
            return ""
        
        normalized = hostname.lower().strip()
        
        if '.' in normalized:
            normalized = normalized.split('.', 1)[0]
        
        normalized = normalized.replace('-', '')
        normalized = self.normalize_pattern.sub('', normalized)
        
        return normalized if len(normalized) > 1 else ""
    
    def is_valid_value(self, value) -> bool:
        """Optimized validation"""
        if not value:
            return False
        if isinstance(value, str):
            stripped = value.strip()
            return stripped and stripped != '*Undefined' and stripped.lower() not in {'null', 'none', 'undefined'}
        return True
    
    def load_metadata(self) -> Dict:
        """Fast metadata loading"""
        logger.info(f"Loading metadata from {self.json_file_path}")
        print(f"Loading metadata...")
        
        start_time = time.time()
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        
        load_time = time.time() - start_time
        
        if 'columns' in metadata:
            table_count = len(metadata['columns'])
            total_columns = sum(len(cols) for cols in metadata['columns'].values())
            logger.info(f"Metadata loaded in {load_time:.2f}s - {table_count} tables, {total_columns} columns")
            print(f"  Found {table_count} tables with {total_columns:,} total columns")
            print(f"  Load time: {load_time:.2f} seconds\n")
        
        return metadata
    
    def discover_columns_comprehensive(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        """Optimized column discovery"""
        logger.info("Starting column discovery process...")
        print("Discovering relevant columns...")
        
        discovered_columns = []
        tables_with_data = 0
        
        if 'columns' not in metadata:
            logger.error("No 'columns' key in metadata")
            return []
        
        for table_name, columns in metadata['columns'].items():
            table_discoveries = 0
            for column_name, column_type in columns.items():
                mapped_type = self._identify_column_type_fast(column_name, column_type)
                
                if mapped_type:
                    discovered_columns.append((table_name, column_name, mapped_type))
                    table_discoveries += 1
            
            if table_discoveries > 0:
                tables_with_data += 1
        
        self.stats['columns_discovered'] = len(discovered_columns)
        
        logger.info(f"Discovery complete: {len(discovered_columns)} columns in {tables_with_data} tables")
        print(f"  Discovered {len(discovered_columns)} relevant columns")
        print(f"  Tables with relevant data: {tables_with_data}")
        print()
        
        return discovered_columns
    
    def _identify_column_type_fast(self, column_name: str, column_type) -> Optional[str]:
        """Fast column type identification"""
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        # Direct mapping lookup
        if isinstance(column_type, str) and type_lower in self.column_mapping:
            return self.column_mapping[type_lower]
        
        # Check hostname patterns
        for pattern in self.hostname_patterns:
            if pattern in column_lower:
                return 'hostname'
        
        # Check advanced patterns
        for target_type, patterns in self.advanced_patterns.items():
            for pattern in patterns:
                if pattern in column_lower or pattern in type_lower:
                    return target_type
        
        return None
    
    def process_tables_sequential(self, columns_by_table: Dict) -> None:
        """Process tables sequentially to avoid concurrency issues"""
        total_tables = len(columns_by_table)
        logger.info(f"Starting sequential processing of {total_tables} tables")
        print(f"\n{'═' * 60}")
        print(f"Processing {total_tables} tables")
        print(f"{'═' * 60}\n")
        
        completed = 0
        start_time = time.time()
        
        for table_name, table_columns in columns_by_table.items():
            completed += 1
            table_start = time.time()
            
            logger.info(f"Processing table {completed}/{total_tables}: {table_name}")
            print(f"[{completed}/{total_tables}] Processing: {table_name}")
            
            # Show column details
            hostname_cols = [col for _, col, ctype in table_columns if ctype == 'hostname']
            attr_cols = [col for _, col, ctype in table_columns if ctype != 'hostname']
            print(f"  Hostname columns: {', '.join(hostname_cols) if hostname_cols else 'None'}")
            print(f"  Attribute columns: {len(attr_cols)}")
            
            try:
                records = self.process_table_optimized(table_name, table_columns)
                table_time = time.time() - table_start
                
                logger.info(f"Table {table_name} complete: {records:,} records in {table_time:.2f}s")
                print(f"  ✓ Processed {records:,} records in {table_time:.2f}s")
                print(f"  Rate: {records/max(0.01, table_time):.0f} records/second\n")
                
            except Exception as e:
                table_time = time.time() - table_start
                logger.error(f"Error processing {table_name}: {str(e)}")
                print(f"  ✗ Error after {table_time:.2f}s: {str(e)[:100]}\n")
                self.stats['processing_errors'] += 1
        
        total_time = time.time() - start_time
        logger.info(f"All tables processed in {total_time:.2f}s")
        print(f"{'─' * 60}")
        print(f"Table processing complete in {total_time:.2f} seconds\n")
    
    def process_table_optimized(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        """Optimized table processing"""
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            return 0
        
        primary_hostname_col = hostname_cols[0][0]
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        query = self._build_query(table_name, all_columns, primary_hostname_col)
        
        try:
            query_job = self.bq_client.query(query)
            records_processed = self._process_results_batch(
                query_job, table_name, primary_hostname_col, attribute_types
            )
            
            self.stats['tables_processed'] += 1
            return records_processed
            
        except Exception as e:
            self.stats['processing_errors'] += 1
            raise e
    
    def _build_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        """Build optimized query"""
        column_selects = [f"`{col}`" for col in columns]
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND `{hostname_col}` != '*Undefined'
        AND LENGTH(`{hostname_col}`) > 0
        """
    
    def _process_results_batch(self, query_job, table_name: str, hostname_col: str, attribute_types: List[str]) -> int:
        """Process query results in batches"""
        records_processed = 0
        batch_size = 1000
        batch_records = []
        new_hosts = 0
        updated_hosts = 0
        skipped_invalid = 0
        
        logger.info(f"Processing query results for {table_name}")
        
        for row in query_job:
            records_processed += 1
            
            # Log progress every 10k records
            if records_processed % 10000 == 0:
                logger.info(f"  Processed {records_processed:,} rows from {table_name}")
            
            if not row[0] or not self.is_valid_value(row[0]):
                skipped_invalid += 1
                continue
            
            normalized_host = self.normalize_hostname(row[0])
            if not normalized_host:
                skipped_invalid += 1
                continue
            
            # Track if this is new or existing
            if normalized_host in self.global_hosts_seen:
                updated_hosts += 1
            else:
                new_hosts += 1
                self.global_hosts_seen.add(normalized_host)
            
            record_data = {
                'normalized_host': normalized_host,
                'hostname': str(row[0]).strip(),
                'table_name': table_name
            }
            
            # Collect attributes
            attributes_found = 0
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and self.is_valid_value(row[i]):
                    record_data[attr_type] = str(row[i]).strip()
                    attributes_found += 1
            
            batch_records.append(record_data)
            
            if len(batch_records) >= batch_size:
                logger.debug(f"Processing batch of {len(batch_records)} records")
                with self.db_lock:
                    self._safe_bulk_insert_or_update(batch_records)
                batch_records.clear()
        
        # Process remaining records
        if batch_records:
            logger.debug(f"Processing final batch of {len(batch_records)} records")
            with self.db_lock:
                self._safe_bulk_insert_or_update(batch_records)
        
        logger.info(f"Table {table_name} results: {records_processed:,} total, {new_hosts:,} new, {updated_hosts:,} existing, {skipped_invalid:,} invalid")
        
        self.stats['total_records_processed'] += records_processed
        return records_processed
    
    def _safe_bulk_insert_or_update(self, records: List[Dict]) -> None:
        """Thread-safe bulk insert/update with proper duplicate handling"""
        if not records:
            return
        
        for record in records:
            normalized_host = record['normalized_host']
            
            try:
                # Check if exists
                existing_query = """
                SELECT source_tables, source_count
                FROM universal_cmdb 
                WHERE normalized_host = ?
                """
                
                existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
                
                if existing:
                    # Update existing - use MERGE logic
                    self._safe_update_host(record, existing)
                else:
                    # Insert new - use INSERT OR IGNORE
                    self._safe_insert_host(record)
                    self.stats['hosts_created'] += 1
                    
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    # If duplicate key error, try to update instead
                    try:
                        existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
                        if existing:
                            self._safe_update_host(record, existing)
                    except:
                        pass  # Skip this record
                else:
                    # Other errors, just skip
                    pass
    
    def _safe_insert_host(self, record: Dict) -> None:
        """Safe insert with duplicate handling"""
        columns = ['normalized_host', 'source_tables', 'source_count']
        values = [record['normalized_host'], record['table_name'], 1]
        
        data_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for col in data_columns:
            if col in record:
                columns.append(col)
                values.append(record[col])
        
        placeholders = ', '.join(['?' for _ in values])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            self.duck_conn.execute(insert_sql, values)
        except Exception as e:
            if "duplicate key" not in str(e).lower():
                raise  # Re-raise if not a duplicate key error
    
    def _safe_update_host(self, record: Dict, existing) -> None:
        """Safe update of existing host"""
        normalized_host = record['normalized_host']
        updates = []
        values = []
        
        # Update source tables
        current_tables = existing[0] if existing[0] else ""
        table_name = record['table_name']
        
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            
            new_source_count = (existing[1] or 0) + 1
            updates.append("source_count = ?")
            values.append(new_source_count)
        
        # Update other fields
        data_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for col in data_columns:
            if col in record:
                updates.append(f"{col} = COALESCE({col}, ?)")
                values.append(record[col])
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            
            try:
                self.duck_conn.execute(update_sql, values)
            except:
                pass  # Skip if update fails
    
    def generate_report(self):
        """Generate summary report"""
        print("\n" + "═" * 80)
        print(" " * 30 + "PROCESSING REPORT")
        print("═" * 80 + "\n")
        
        logger.info("Generating final report...")
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print("Summary Statistics:")
        print("─" * 40)
        print(f"  Total Unique Hosts: {total_hosts:,}")
        print(f"  Tables Processed: {self.stats['tables_processed']}")
        print(f"  Records Processed: {self.stats['total_records_processed']:,}")
        print(f"  New Hosts Created: {self.stats['hosts_created']:,}")
        print(f"  Hosts Updated: {self.stats['hosts_updated']:,}")
        
        if self.stats['processing_errors'] > 0:
            print(f"  Processing Errors: {self.stats['processing_errors']}")
        
        # Data quality metrics
        print("\nData Coverage Analysis:")
        print("─" * 40)
        
        columns_to_check = [
            'hostname', 'business_unit', 'region', 'infrastructure_type', 
            'ip_address', 'country', 'data_center', 'domain'
        ]
        
        for col in columns_to_check:
            count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            count = self.duck_conn.execute(count_query).fetchone()[0]
            percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
            
            if count > 0:
                print(f"  {col:20s}: {count:8,} records ({percentage:5.1f}%)")
                
                # Get sample values
                sample_query = f"SELECT DISTINCT {col} FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != '' LIMIT 2"
                samples = self.duck_conn.execute(sample_query).fetchall()
                if samples:
                    sample_values = [str(s[0])[:30] for s in samples]
                    print(f"    Examples: {', '.join(sample_values)}")
        
        # Top source tables
        print("\nTop Source Tables by Host Count:")
        print("─" * 40)
        
        source_query = """
        SELECT source_tables, COUNT(*) as cnt 
        FROM universal_cmdb 
        WHERE source_tables IS NOT NULL
        GROUP BY source_tables
        ORDER BY cnt DESC
        LIMIT 5
        """
        
        for row in self.duck_conn.execute(source_query).fetchall():
            if row[0]:
                tables = row[0][:60] + "..." if len(row[0]) > 60 else row[0]
                print(f"  {tables}: {row[1]:,} hosts")
        
        logger.info(f"Report complete - {total_hosts:,} total hosts")
    
    def export_comprehensive(self, filename: str = "universal_cmdb_export.csv"):
        """Export to CSV"""
        logger.info(f"Starting export to {filename}")
        print(f"\nExporting data to {filename}...")
        
        try:
            start_time = time.time()
            
            # Get row count first
            row_count = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
            print(f"  Exporting {row_count:,} rows...")
            
            export_query = f"""
            COPY (
                SELECT * FROM universal_cmdb 
                ORDER BY source_count DESC, normalized_host
            ) TO '{filename}' (HEADER, DELIMITER ',')
            """
            
            self.duck_conn.execute(export_query)
            
            export_time = time.time() - start_time
            file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
            
            logger.info(f"Export complete: {row_count:,} rows, {file_size:.2f}MB in {export_time:.2f}s")
            print(f"  ✓ Export complete: {file_size:.2f}MB in {export_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            print(f"  ✗ Export error: {str(e)}")
    
    def process_all_fast(self):
        """Main processing function"""
        print("\n" + "=" * 80)
        print(" " * 20 + "STARTING CMDB PROCESSING")
        print("=" * 80 + "\n")
        
        overall_start = time.time()
        logger.info("Starting CMDB processing pipeline")
        
        # Load and discover
        metadata = self.load_metadata()
        discovered_columns = self.discover_columns_comprehensive(metadata)
        
        if not discovered_columns:
            logger.error("No processable columns discovered")
            print("ERROR: No processable columns discovered")
            return
        
        # Organize by table
        logger.info("Organizing columns by source table...")
        columns_by_table = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((table_name, column_name, column_type))
        
        print(f"Tables to process: {len(columns_by_table)}")
        print(f"Average columns per table: {len(discovered_columns) / len(columns_by_table):.1f}")
        
        # Process tables sequentially
        self.process_tables_sequential(columns_by_table)
        
        # Generate report
        self.generate_report()
        
        # Export
        self.export_comprehensive()
        
        total_time = time.time() - overall_start
        
        print("\n" + "=" * 80)
        print(" " * 25 + "PROCESSING COMPLETE")
        print("=" * 80)
        
        print(f"\nPerformance Metrics:")
        print(f"  Total Time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
        print(f"  Processing Rate: {self.stats['total_records_processed']/max(1, total_time):.0f} records/second")
        print(f"  Average per Table: {total_time/max(1, len(columns_by_table)):.2f} seconds")
        
        logger.info(f"Pipeline complete in {total_time:.2f}s - {self.stats['total_records_processed']:,} records processed")
    
    def close_connections(self):
        """Clean up connections"""
        try:
            self.duck_conn.close()
        except:
            pass

if __name__ == "__main__":
    processor = None
    
    try:
        processor = FastCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        processor.process_all_fast()
        
        print("\n═══ SUCCESS ═══")
        print("Database: universal_cmdb.db")
        print("Export: universal_cmdb_export.csv\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.close_connections()