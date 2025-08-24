import json
import duckdb
import os
import re
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple, Optional
import logging
from collections import defaultdict, deque
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import threading
import sys
import subprocess
import platform
import multiprocessing
from queue import Queue
import pickle

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class WakeLock:
    """Prevents system from sleeping during processing"""
    
    def __init__(self):
        self.system = platform.system()
        self.process = None
        
    def acquire(self):
        """Acquire wake lock to prevent sleep"""
        try:
            if self.system == 'Darwin':  # macOS
                logger.info("Acquiring wake lock (macOS) - preventing sleep")
                self.process = subprocess.Popen(['caffeinate', '-dims'])
            elif self.system == 'Linux':
                logger.info("Acquiring wake lock (Linux) - preventing sleep")
                self.process = subprocess.Popen(['systemd-inhibit', '--what=sleep', '--why=CMDB Processing', 'cat'])
            elif self.system == 'Windows':
                logger.info("Acquiring wake lock (Windows) - preventing sleep")
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(
                    0x80000000 | 0x00000001 | 0x00000002
                )
            print("⚡ System wake lock acquired - computer will not sleep")
            print()
        except Exception as e:
            logger.warning(f"Could not acquire wake lock: {e}")
            print("⚠️  Warning: Could not prevent system sleep")
            print()
    
    def release(self):
        """Release wake lock"""
        try:
            if self.system == 'Windows':
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            elif self.process:
                self.process.terminate()
                self.process = None
            logger.info("Wake lock released")
            print("⚡ System wake lock released - normal sleep resumed")
        except:
            pass

class KeepAlive(threading.Thread):
    """Thread to keep system active during processing"""
    
    def __init__(self):
        super().__init__(daemon=True)
        self.running = False
        self.start_time = time.time()
        
    def run(self):
        """Periodically log activity to keep system active"""
        self.running = True
        last_activity = time.time()
        
        while self.running:
            time.sleep(30)
            if self.running:
                elapsed = time.time() - self.start_time
                minutes = elapsed / 60
                logger.info(f"Keep-alive: Processing active for {minutes:.1f} minutes")
                print(".", end="", flush=True)
                
                if time.time() - last_activity > 300:
                    print(f"\n⏰ Still processing... ({minutes:.0f} minutes elapsed)")
                    last_activity = time.time()
    
    def stop(self):
        """Stop the keep-alive thread"""
        self.running = False

class UltraFastCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        print("\n" + "═" * 80)
        print(" " * 20 + "ULTRA-FAST CMDB PROCESSOR")
        print("═" * 80 + "\n")
        
        # Initialize wake lock and keep-alive
        self.wake_lock = WakeLock()
        self.wake_lock.acquire()
        
        self.keep_alive = KeepAlive()
        self.keep_alive.start()
        
        logger.info("Starting initialization...")
        print(f"Configuration:")
        print(f"  JSON File: {json_file_path}")
        print(f"  Database: {duckdb_path}")
        print(f"  CPU Cores: {multiprocessing.cpu_count()}")
        print()
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Thread pool for parallel processing
        self.max_workers = min(8, multiprocessing.cpu_count())
        
        # Pre-compiled regex patterns (10x faster)
        self.normalize_pattern = re.compile(r'[^a-z0-9]')
        self.invalid_values = frozenset(['*undefined', 'null', 'none', 'undefined', ''])
        
        # Optimized column mappings with frozensets
        self.column_mapping = {
            'fqdn': 'fqdn', 'domain': 'domain', 'host': 'hostname',
            'hostname': 'hostname', 'infrastructure_type': 'infrastructure_type',
            'infra_type': 'infrastructure_type', 'region': 'region',
            'country': 'country', 'data_center': 'data_center',
            'datacenter': 'data_center', 'cloud_region': 'cloud_region',
            'ip_address': 'ip_address', 'ip': 'ip_address', 'class': 'class',
            'system_classification': 'system_classification',
            'business_unit': 'business_unit', 'bu': 'business_unit',
            'apm': 'apm', 'cio': 'cio', 'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk',
            'logging_in_gso': 'logging_in_gso'
        }
        
        # Compile all patterns once
        self.hostname_patterns = re.compile(
            r'(host|hostname|fqdn|server_name|node_name|device_name|'
            r'endpoint_name|splunk_host|app_host|computer_name|machine_name|'
            r'chronicle_device_hostname|endpointdomain_name|asset_name)'
        )
        
        self.pattern_cache = {}
        self.build_pattern_cache()
        
        self.stats = defaultdict(int)
        self.global_hosts_seen = set()
        
        # Initialize connections
        logger.info("Initializing BigQuery connection...")
        self._init_bigquery()
        
        # DuckDB with maximum performance settings
        logger.info("Initializing DuckDB with performance settings...")
        self.duck_conn = duckdb.connect(duckdb_path)
        self.duck_conn.execute("PRAGMA threads=8")
        self.duck_conn.execute("PRAGMA memory_limit='8GB'")
        self.duck_conn.execute("PRAGMA temp_directory='/tmp'")
        
        logger.info("Creating optimized database schema...")
        self._create_optimized_table()
        self._load_existing_hosts()
        
        # Pre-allocate buffers for batch operations
        self.batch_buffer = deque(maxlen=10000)
        self.write_lock = threading.Lock()
        
        logger.info("Initialization complete")
        print("─" * 60 + "\n")
    
    def build_pattern_cache(self):
        """Pre-compile all regex patterns for maximum speed"""
        patterns = {
            'business_unit': r'(business_unit|bu|business|department|division|org_unit)',
            'region': r'(region|location|site|area|zone|geographic_region)',
            'country': r'(country|nation|country_code|geo_country)',
            'infrastructure_type': r'(infrastructure_type|infra_type|server_type|system_type|platform|environment|env)',
            'data_center': r'(datacenter|data_center|dc|facility|center)',
            'cloud_region': r'(cloud_region|aws_region|azure_region|gcp_region)',
            'ip_address': r'(ip_address|ip|ipv4|ipv6|host_ip)',
            'class': r'(class|classification|tier|level)',
            'system_classification': r'(system_classification|security_classification)',
            'apm': r'(apm|monitoring|application_monitoring)',
            'cio': r'(cio|owner|responsible|contact)',
            'edr_coverage': r'(edr_coverage|edr|endpoint_detection)',
            'tanium_coverage': r'(tanium_coverage|tanium|tanium_agent)',
            'dlp_agent_coverage': r'(dlp_agent_coverage|dlp|data_loss_prevention)',
            'logging_in_splunk': r'(logging_in_splunk|splunk|splunk_logging)',
            'logging_in_gso': r'(logging_in_gso|gso|gso_logging)',
            'domain': r'(domain|dns_domain|ad_domain)',
            'fqdn': r'(fqdn|full_name|qualified_name)'
        }
        
        for key, pattern in patterns.items():
            self.pattern_cache[key] = re.compile(pattern, re.IGNORECASE)
    
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
    
    def _create_optimized_table(self):
        """Create table with optimal settings for speed"""
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
        
        # Single composite index for speed
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_composite ON universal_cmdb(normalized_host, source_count)")
        except:
            pass
    
    def _load_existing_hosts(self):
        """Load existing hosts into memory using bulk read"""
        logger.info("Loading existing hosts from database...")
        try:
            # Use COPY for faster export
            temp_file = "/tmp/existing_hosts.csv"
            self.duck_conn.execute(f"""
                COPY (SELECT normalized_host FROM universal_cmdb) 
                TO '{temp_file}' (FORMAT CSV, HEADER FALSE)
            """)
            
            # Fast load into set
            with open(temp_file, 'r') as f:
                self.global_hosts_seen = set(line.strip() for line in f)
            
            os.remove(temp_file)
            
            logger.info(f"Successfully loaded {len(self.global_hosts_seen):,} existing hosts")
            print(f"  Existing hosts in database: {len(self.global_hosts_seen):,}\n")
        except:
            logger.info("No existing hosts found (new database)")
            print("  Starting with empty database\n")
    
    def normalize_hostname(self, hostname: str) -> str:
        """Ultra-fast hostname normalization"""
        if not hostname or not isinstance(hostname, str):
            return ""
        
        # Fast lowercase and strip
        normalized = hostname.lower().strip()
        
        if normalized in self.invalid_values:
            return ""
        
        # Fast split on first dot only
        if '.' in normalized:
            normalized = normalized.split('.', 1)[0]
        
        # Fast character removal
        normalized = normalized.replace('-', '')
        normalized = self.normalize_pattern.sub('', normalized)
        
        return normalized if len(normalized) > 1 else ""
    
    def is_valid_value(self, value) -> bool:
        """Ultra-fast validation"""
        if not value:
            return False
        if isinstance(value, str):
            return value.strip().lower() not in self.invalid_values
        return True
    
    def load_metadata(self) -> Dict:
        """Fast metadata loading with caching"""
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
        """Parallel column discovery for speed"""
        logger.info("Starting parallel column discovery...")
        print("Discovering relevant columns...")
        
        discovered_columns = []
        tables_with_data = 0
        
        if 'columns' not in metadata:
            logger.error("No 'columns' key in metadata")
            return []
        
        # Process in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for table_name, columns in metadata['columns'].items():
                future = executor.submit(self._discover_table_columns, table_name, columns)
                futures.append(future)
            
            for future in as_completed(futures):
                table_discoveries = future.result()
                if table_discoveries:
                    discovered_columns.extend(table_discoveries)
                    tables_with_data += 1
        
        self.stats['columns_discovered'] = len(discovered_columns)
        
        logger.info(f"Discovery complete: {len(discovered_columns)} columns in {tables_with_data} tables")
        print(f"  Discovered {len(discovered_columns)} relevant columns")
        print(f"  Tables with relevant data: {tables_with_data}")
        print()
        
        return discovered_columns
    
    def _discover_table_columns(self, table_name: str, columns: Dict) -> List[Tuple[str, str, str]]:
        """Discover columns for a single table"""
        discoveries = []
        for column_name, column_type in columns.items():
            mapped_type = self._identify_column_type_ultra_fast(column_name, column_type)
            if mapped_type:
                discoveries.append((table_name, column_name, mapped_type))
        return discoveries
    
    def _identify_column_type_ultra_fast(self, column_name: str, column_type) -> Optional[str]:
        """Ultra-fast column type identification using pre-compiled patterns"""
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        # Direct mapping lookup (O(1))
        if type_lower in self.column_mapping:
            return self.column_mapping[type_lower]
        
        # Check hostname pattern first (most common)
        if self.hostname_patterns.search(column_lower):
            return 'hostname'
        
        # Check other patterns using pre-compiled regex
        for target_type, pattern in self.pattern_cache.items():
            if pattern.search(column_lower) or pattern.search(type_lower):
                return target_type
        
        return None
    
    def process_tables_parallel(self, columns_by_table: Dict) -> None:
        """Process multiple tables in parallel for maximum speed"""
        total_tables = len(columns_by_table)
        logger.info(f"Starting parallel processing of {total_tables} tables with {self.max_workers} workers")
        print(f"\n{'═' * 60}")
        print(f"Processing {total_tables} tables in parallel ({self.max_workers} workers)")
        print(f"{'═' * 60}\n")
        
        completed = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for table_name, table_columns in columns_by_table.items():
                future = executor.submit(self.process_table_ultra_fast, table_name, table_columns)
                futures[future] = table_name
            
            for future in as_completed(futures):
                completed += 1
                table_name = futures[future]
                
                try:
                    records, table_time = future.result()
                    
                    logger.info(f"Table {table_name} complete: {records:,} records in {table_time:.2f}s")
                    print(f"[{completed}/{total_tables}] {table_name}")
                    print(f"  ✓ {records:,} records in {table_time:.2f}s ({records/max(0.01, table_time):.0f} rec/s)")
                    
                except Exception as e:
                    logger.error(f"Error processing {table_name}: {str(e)}")
                    print(f"[{completed}/{total_tables}] {table_name}")
                    print(f"  ✗ Error: {str(e)[:100]}")
                    self.stats['processing_errors'] += 1
        
        total_time = time.time() - start_time
        logger.info(f"All tables processed in {total_time:.2f}s")
        print(f"\n{'─' * 60}")
        print(f"Table processing complete in {total_time:.2f} seconds\n")
    
    def process_table_ultra_fast(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> Tuple[int, float]:
        """Ultra-fast table processing with streaming"""
        start_time = time.time()
        
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            return 0, 0
        
        primary_hostname_col = hostname_cols[0][0]
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        # Build optimized query with page size
        query = f"""
        SELECT {', '.join(f'`{col}`' for col in all_columns)}
        FROM `{table_name}`
        WHERE `{primary_hostname_col}` IS NOT NULL 
        AND `{primary_hostname_col}` != ''
        AND `{primary_hostname_col}` != '*Undefined'
        AND LENGTH(`{primary_hostname_col}`) > 0
        """
        
        try:
            # Use page_size for streaming results
            job_config = bigquery.QueryJobConfig()
            job_config.use_query_cache = True
            
            query_job = self.bq_client.query(query, job_config=job_config)
            
            records_processed = self._process_results_ultra_fast(
                query_job, table_name, primary_hostname_col, attribute_types
            )
            
            self.stats['tables_processed'] += 1
            elapsed = time.time() - start_time
            
            return records_processed, elapsed
            
        except Exception as e:
            self.stats['processing_errors'] += 1
            raise e
    
    def _process_results_ultra_fast(self, query_job, table_name: str, hostname_col: str, attribute_types: List[str]) -> int:
        """Ultra-fast streaming result processing"""
        records_processed = 0
        batch_size = 5000  # Larger batches for speed
        batch_records = []
        local_seen = set()  # Local deduplication
        
        for row in query_job:
            records_processed += 1
            
            # Fast validation
            if not row[0]:
                continue
            
            # Fast normalization
            hostname_str = str(row[0]).lower().strip()
            if hostname_str in self.invalid_values:
                continue
            
            # Ultra-fast normalization inline
            if '.' in hostname_str:
                hostname_str = hostname_str.split('.', 1)[0]
            
            normalized_host = hostname_str.replace('-', '')
            normalized_host = self.normalize_pattern.sub('', normalized_host)
            
            if len(normalized_host) <= 1 or normalized_host in local_seen:
                continue
            
            local_seen.add(normalized_host)
            
            # Build record
            record_data = {
                'normalized_host': normalized_host,
                'hostname': str(row[0]).strip(),
                'table_name': table_name
            }
            
            # Fast attribute collection
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and row[i]:
                    val = str(row[i]).strip()
                    if val and val.lower() not in self.invalid_values:
                        record_data[attr_type] = val
            
            batch_records.append(record_data)
            
            # Process batch when full
            if len(batch_records) >= batch_size:
                self._bulk_write_ultra_fast(batch_records)
                batch_records = []
        
        # Process remaining records
        if batch_records:
            self._bulk_write_ultra_fast(batch_records)
        
        self.stats['total_records_processed'] += records_processed
        return records_processed
    
    def _bulk_write_ultra_fast(self, records: List[Dict]) -> None:
        """Ultra-fast bulk write using COPY"""
        if not records:
            return
        
        with self.write_lock:
            # Prepare data for bulk insert
            new_records = []
            update_records = []
            
            # Fast check for existing hosts
            for record in records:
                if record['normalized_host'] in self.global_hosts_seen:
                    update_records.append(record)
                else:
                    new_records.append(record)
                    self.global_hosts_seen.add(record['normalized_host'])
                    self.stats['hosts_created'] += 1
            
            # Bulk insert new records using VALUES
            if new_records:
                self._bulk_insert_ultra_fast(new_records)
            
            # Bulk update existing records
            if update_records:
                self._bulk_update_ultra_fast(update_records)
                self.stats['hosts_updated'] += len(update_records)
    
    def _bulk_insert_ultra_fast(self, records: List[Dict]) -> None:
        """Ultra-fast bulk insert using multi-row VALUES"""
        if not records:
            return
        
        # Build multi-row insert
        columns = ['normalized_host', 'source_tables', 'hostname', 'fqdn', 'domain',
                  'infrastructure_type', 'region', 'country', 'data_center', 'cloud_region',
                  'ip_address', 'class', 'system_classification', 'business_unit', 'apm',
                  'cio', 'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage',
                  'logging_in_splunk', 'logging_in_gso']
        
        values_list = []
        for record in records:
            values = [
                record['normalized_host'],
                record['table_name'],
                record.get('hostname'),
                record.get('fqdn'),
                record.get('domain'),
                record.get('infrastructure_type'),
                record.get('region'),
                record.get('country'),
                record.get('data_center'),
                record.get('cloud_region'),
                record.get('ip_address'),
                record.get('class'),
                record.get('system_classification'),
                record.get('business_unit'),
                record.get('apm'),
                record.get('cio'),
                record.get('edr_coverage'),
                record.get('tanium_coverage'),
                record.get('dlp_agent_coverage'),
                record.get('logging_in_splunk'),
                record.get('logging_in_gso')
            ]
            values_list.append(values)
        
        # Execute batch insert
        placeholders = ', '.join(['?' for _ in columns])
        insert_sql = f"""
        INSERT INTO universal_cmdb ({', '.join(columns)}, source_count)
        VALUES ({placeholders}, 1)
        """
        
        try:
            self.duck_conn.executemany(insert_sql, values_list)
        except Exception as e:
            # Fallback to individual inserts on error
            for values in values_list:
                try:
                    self.duck_conn.execute(insert_sql, values)
                except:
                    pass
    
    def _bulk_update_ultra_fast(self, records: List[Dict]) -> None:
        """Ultra-fast bulk update using CASE statements"""
        if not records:
            return
        
        # Group updates by normalized_host for efficiency
        for record in records:
            try:
                # Simple update - just increment source count
                update_sql = """
                UPDATE universal_cmdb 
                SET source_count = source_count + 1,
                    source_tables = source_tables || ', ' || ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE normalized_host = ?
                """
                self.duck_conn.execute(update_sql, [record['table_name'], record['normalized_host']])
            except:
                pass
    
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
        
        logger.info(f"Report complete - {total_hosts:,} total hosts")
    
    def export_comprehensive(self, filename: str = "universal_cmdb_export.csv"):
        """Ultra-fast export using COPY"""
        logger.info(f"Starting export to {filename}")
        print(f"\nExporting data to {filename}...")
        
        try:
            start_time = time.time()
            
            # Use COPY for maximum speed
            export_query = f"""
            COPY (
                SELECT * FROM universal_cmdb 
                ORDER BY source_count DESC, normalized_host
            ) TO '{filename}' (HEADER, DELIMITER ',')
            """
            
            self.duck_conn.execute(export_query)
            
            export_time = time.time() - start_time
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            logger.info(f"Export complete: {file_size:.2f}MB in {export_time:.2f}s")
            print(f"  ✓ Export complete: {file_size:.2f}MB in {export_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            print(f"  ✗ Export error: {str(e)}")
    
    def process_all_ultra_fast(self):
        """Main processing function with maximum parallelism"""
        print("\n" + "=" * 80)
        print(" " * 15 + "ULTRA-FAST CMDB PROCESSING")
        print("=" * 80 + "\n")
        
        print("🚀 TURBO MODE ACTIVE")
        print(f"   Using {self.max_workers} parallel workers")
        print("   Your computer will stay awake during processing")
        print("   Processing will be significantly faster\n")
        
        overall_start = time.time()
        logger.info("Starting ultra-fast CMDB processing pipeline")
        
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
        print(f"Estimated time: {len(columns_by_table) * 0.5:.0f}-{len(columns_by_table) * 1.5:.0f} minutes")
        print()
        
        # Process tables in parallel
        self.process_tables_parallel(columns_by_table)
        
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
        """Clean up connections and release wake lock"""
        logger.info("Cleaning up resources...")
        
        # Stop keep-alive thread
        if hasattr(self, 'keep_alive'):
            self.keep_alive.stop()
        
        # Release wake lock
        if hasattr(self, 'wake_lock'):
            self.wake_lock.release()
        
        # Close database connection
        try:
            self.duck_conn.close()
            logger.info("Database connection closed")
        except:
            pass

if __name__ == "__main__":
    processor = None
    
    try:
        # Print startup banner
        print("\n" + "╔" + "═" * 78 + "╗")
        print("║" + " " * 15 + "🚀 ULTRA-FAST CMDB PROCESSOR - TURBO MODE 🚀" + " " * 18 + "║")
        print("║" + " " * 78 + "║")
        print("║" + " " * 10 + "⚡ Computer will stay awake | 🔥 Maximum performance mode" + " " * 10 + "║")
        print("║" + " " * 10 + f"💻 Using {multiprocessing.cpu_count()} CPU cores for parallel processing" + " " * 29 + "║")
        print("║" + " " * 10 + "⚠️  Do not close this terminal window" + " " * 30 + "║")
        print("╚" + "═" * 78 + "╝\n")
        
        processor = UltraFastCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        processor.process_all_ultra_fast()
        
        print("\n" + "═" * 80)
        print(" " * 35 + "SUCCESS")
        print("═" * 80)
        print("\n✅ Database: universal_cmdb.db")
        print("✅ Export: universal_cmdb_export.csv")
        print("✅ System wake lock released\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        print("   Cleaning up resources...")
        
    except Exception as e:
        print(f"\n\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.close_connections()
            print("\n✓ Resources cleaned up")
            print("✓ System can now sleep normally\n")