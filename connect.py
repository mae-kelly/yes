import json
import duckdb
import os
import re
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple, Optional
import logging
from collections import defaultdict
import psutil
import queue
from dataclasses import dataclass
from functools import partial

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    tables_completed: int = 0
    start_time: float = 0
    
class PerformanceMonitor:
    def __init__(self):
        self.running = True
        self.thread = None
        self.start_time = time.time()
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("🔥 PERFORMANCE MONITOR ACTIVATED - MAXIMUM POWER MODE 🚀")
    
    def _monitor_loop(self):
        emoji_cycle = ["🔥", "🚀", "⚡", "💨", "🌪️", "🎯", "⭐", "✨"]
        emoji_index = 0
        
        while self.running:
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                elapsed = time.time() - self.start_time
                
                current_emoji = emoji_cycle[emoji_index % len(emoji_cycle)]
                
                print(f"{current_emoji} CPU: {cpu_percent:.1f}% | RAM: {memory.percent:.1f}% | "
                      f"Runtime: {int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d} 🔥")
                
                # Fan speed indicator
                if cpu_percent > 80:
                    print("🌪️ FANS SPINNING AT MAXIMUM! CPU UNDER HEAVY LOAD! ⚡")
                elif cpu_percent > 60:
                    print("💨 High performance mode - fans active 🚀")
                
                emoji_index += 1
                time.sleep(15)  # More frequent updates for performance mode
                
            except Exception as e:
                print(f"⚡ Monitor error: {e}")
                time.sleep(15)
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

class HighPerformanceHostProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.performance_monitor = PerformanceMonitor()
        self.stats = ProcessingStats()
        self.table_row_counts = {}
        
        # Performance configuration
        self.cpu_count = multiprocessing.cpu_count()
        self.max_workers = min(self.cpu_count * 2, 32)  # Aggressive threading
        self.batch_size = 10000  # Large batch size for bulk operations
        self.chunk_size = 50000  # Process in large chunks
        self.connection_pool = []
        
        print(f"🔥 INITIALIZING HIGH-PERFORMANCE MODE:")
        print(f"⚡ CPU Cores: {self.cpu_count}")
        print(f"🚀 Max Workers: {self.max_workers}")
        print(f"💨 Batch Size: {self.batch_size:,}")
        print(f"🌪️ Chunk Size: {self.chunk_size:,}")
        
        # Column mappings (keeping original logic)
        self.column_mapping = {
            'fqdn': 'fqdn', 'domain': 'domain', 'host': 'hostname', 'hostname': 'hostname',
            'infrastructure_type': 'infrastructure_type', 'infra_type': 'infrastructure_type',
            'region': 'region', 'country': 'country', 'data_center': 'data_center',
            'cloud_region': 'cloud_region', 'ip_address': 'ip_address', 'class': 'class',
            'system_classification': 'system_classification', 'business_unit': 'business_unit',
            'apm': 'apm', 'cio': 'cio', 'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage', 'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk', 'logging_in_gso': 'logging_in_gso'
        }
        
        self.hostname_patterns = ['host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name', 
                                 'endpoint_name', 'splunk_host', 'app_host', 'computer_name']
        
        self.attribute_patterns = {
            'business_unit': ['business_unit', 'bu', 'business', 'department', 'division', 'org_unit', 'cost_center'],
            'region': ['region', 'location', 'site', 'area', 'zone', 'geographic', 'geo_region'],
            'country': ['country', 'nation', 'country_code'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type', 'platform', 'environment', 'env'],
            'data_center': ['datacenter', 'data_center', 'dc', 'facility', 'center'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'host_ip', 'server_ip'],
            'class': ['class', 'classification', 'tier', 'level', 'grade'],
            'system_classification': ['system_classification', 'security_classification', 'sensitivity'],
            'apm': ['apm', 'monitoring', 'application_monitoring'],
            'cio': ['cio', 'owner', 'responsible', 'contact', 'admin', 'administrator'],
            'edr_coverage': ['edr_coverage', 'edr', 'endpoint_detection', 'security_agent', 'antivirus'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'tanium_agent'],
            'dlp_agent_coverage': ['dlp_agent_coverage', 'dlp', 'data_loss_prevention'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk', 'splunk_logging'],
            'logging_in_gso': ['logging_in_gso', 'gso', 'gso_logging'],
            'domain': ['domain', 'dns_domain', 'ad_domain'],
            'fqdn': ['fqdn', 'full_name', 'qualified_name']
        }
        
        # Initialize BigQuery with performance settings
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
        
        # Configure BigQuery for maximum performance
        self.job_config = bigquery.QueryJobConfig(
            use_query_cache=False,
            use_legacy_sql=False,
            maximum_bytes_billed=None,  # Remove billing limits for speed
        )
        
        # Initialize optimized DuckDB connection
        self._init_high_performance_db()
        
    def _init_high_performance_db(self):
        """Initialize DuckDB with performance optimizations"""
        print("🚀 Configuring DuckDB for MAXIMUM PERFORMANCE...")
        
        self.main_conn = duckdb.connect(self.duckdb_path)
        
        # Aggressive performance settings
        performance_settings = [
            "SET memory_limit='8GB'",
            "SET threads=TO_THREADS(0)",  # Use all available cores
            "SET enable_progress_bar=false",
            "SET force_compression='uncompressed'",  # Skip compression for speed
            "SET default_null_order='nulls_first'",
            "SET enable_object_cache=true",
            "SET checkpoint_threshold='1GB'",
            "SET wal_autocheckpoint=0",  # Disable automatic checkpoints for speed
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL",  # Balance between speed and safety
            "PRAGMA cache_size=1000000",  # Large cache
            "PRAGMA temp_store=MEMORY",
            "PRAGMA mmap_size=268435456"  # 256MB mmap
        ]
        
        for setting in performance_settings:
            try:
                self.main_conn.execute(setting)
                print(f"⚡ Applied: {setting}")
            except Exception as e:
                print(f"💨 Warning: {setting} failed: {e}")
        
        self._create_optimized_table()
        self._create_connection_pool()
    
    def _create_optimized_table(self):
        """Create table with performance optimizations"""
        print("🌪️ Creating optimized table structure...")
        
        sql = """
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
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.main_conn.execute(sql)
        
        # Create performance indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_source_tables ON universal_cmdb(source_tables)",
            "CREATE INDEX IF NOT EXISTS idx_hostname ON universal_cmdb(hostname)",
            "CREATE INDEX IF NOT EXISTS idx_business_unit ON universal_cmdb(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)"
        ]
        
        for idx in indexes:
            try:
                self.main_conn.execute(idx)
            except:
                pass
    
    def _create_connection_pool(self):
        """Create a pool of DuckDB connections for parallel processing"""
        print(f"🔥 Creating connection pool with {self.max_workers} connections...")
        
        for i in range(self.max_workers):
            conn = duckdb.connect(self.duckdb_path)
            # Apply same performance settings to each connection
            try:
                conn.execute("SET threads=4")  # Limit per connection to avoid conflicts
                conn.execute("SET memory_limit='1GB'")
                conn.execute("PRAGMA synchronous=NORMAL")
            except:
                pass
            self.connection_pool.append(conn)
    
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.lower().strip()
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        normalized = normalized.replace('-', '')
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        return normalized
    
    def get_table_row_count_fast(self, table_name: str) -> int:
        """Fast row counting with minimal overhead"""
        try:
            # Use approximate count for speed on large tables
            count_query = f"""
            SELECT 
                CASE 
                    WHEN COUNT(*) > 1000000 THEN 
                        (SELECT CAST(table_rows AS INT64) FROM `{table_name.split('.')[0]}`.__TABLES__ WHERE table_id = '{table_name.split('.')[-1]}')
                    ELSE COUNT(*) 
                END as row_count
            FROM `{table_name}` 
            LIMIT 1
            """
            
            # Fallback to simple count
            simple_query = f"SELECT COUNT(*) FROM `{table_name}`"
            
            try:
                query_job = self.bq_client.query(count_query, job_config=self.job_config)
                result = next(iter(query_job.result()))
                row_count = int(result[0]) if result[0] else 0
            except:
                query_job = self.bq_client.query(simple_query, job_config=self.job_config)
                result = next(iter(query_job.result()))
                row_count = int(result[0])
            
            self.table_row_counts[table_name] = row_count
            print(f"🚀 Table {table_name}: {row_count:,} rows")
            return row_count
            
        except Exception as e:
            print(f"⚡ Error counting {table_name}: {e}")
            self.table_row_counts[table_name] = 0
            return 0
    
    def process_table_chunk_parallel(self, table_info: tuple) -> dict:
        """Process a chunk of table data in parallel"""
        table_name, columns_info, offset, limit = table_info
        
        hostname_cols = [c for c in columns_info if c[2] == 'hostname']
        attribute_cols = [c for c in columns_info if c[2] != 'hostname']
        
        if not hostname_cols:
            return {'records': 0, 'table': table_name, 'chunk': f"{offset}-{offset+limit}"}
        
        hostname_col = hostname_cols[0][1]
        column_names = [hostname_col] + [c[1] for c in attribute_cols]
        attribute_types = [c[2] for c in attribute_cols]
        
        # Optimized query with chunking
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in column_names])}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND LENGTH(`{hostname_col}`) > 0
        LIMIT {limit} OFFSET {offset}
        """
        
        try:
            thread_id = threading.current_thread().ident
            print(f"🔥 Thread {thread_id}: Processing {table_name} chunk {offset:,}-{offset+limit:,}")
            
            query_job = self.bq_client.query(query, job_config=self.job_config)
            results = query_job.result()
            
            records_batch = []
            
            for row in results:
                if row[0] and isinstance(row[0], str):
                    normalized_host = self.normalize_hostname(row[0])
                    if normalized_host and len(normalized_host) > 2:
                        record = {'normalized_host': normalized_host, 'hostname': row[0]}
                        
                        for i, attr_type in enumerate(attribute_types, 1):
                            if i < len(row) and row[i] and str(row[i]).strip():
                                record[attr_type] = str(row[i]).strip()
                        
                        records_batch.append((record, table_name))
            
            # Batch insert using available connection
            conn_id = hash(threading.current_thread().ident) % len(self.connection_pool)
            conn = self.connection_pool[conn_id]
            
            inserted, updated = self._bulk_insert_records(records_batch, conn)
            
            print(f"⚡ Thread {thread_id}: Processed {len(records_batch)} records from {table_name}")
            
            return {
                'records': len(records_batch),
                'inserted': inserted,
                'updated': updated,
                'table': table_name,
                'chunk': f"{offset}-{offset+limit}"
            }
            
        except Exception as e:
            print(f"💥 Error in chunk {offset}-{offset+limit} of {table_name}: {e}")
            return {'records': 0, 'inserted': 0, 'updated': 0, 'table': table_name, 'chunk': f"{offset}-{offset+limit}"}
    
    def _bulk_insert_records(self, records_batch: List[tuple], conn) -> tuple:
        """Bulk insert/update records for maximum performance"""
        if not records_batch:
            return 0, 0
        
        inserted_count = 0
        updated_count = 0
        
        try:
            # Begin transaction for batch processing
            conn.execute("BEGIN TRANSACTION")
            
            # Prepare bulk upsert
            for record, table_name in records_batch:
                normalized_host = record['normalized_host']
                
                # Check if exists (optimized with prepared statement would be better)
                existing = conn.execute(
                    "SELECT normalized_host FROM universal_cmdb WHERE normalized_host = ?", 
                    [normalized_host]
                ).fetchone()
                
                if existing:
                    # Update existing record
                    update_fields = []
                    values = []
                    
                    for key, value in record.items():
                        if key != 'normalized_host' and value:
                            update_fields.append(f"{key} = ?")
                            values.append(value)
                    
                    if update_fields:
                        values.append(normalized_host)
                        update_sql = f"""
                        UPDATE universal_cmdb 
                        SET {', '.join(update_fields)}, last_updated = CURRENT_TIMESTAMP 
                        WHERE normalized_host = ?
                        """
                        conn.execute(update_sql, values)
                        updated_count += 1
                else:
                    # Insert new record
                    columns = ['normalized_host', 'source_tables'] + [k for k in record.keys() if k != 'normalized_host']
                    values = [normalized_host, table_name] + [record.get(k) for k in columns[2:]]
                    placeholders = ', '.join(['?'] * len(columns))
                    
                    insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
                    conn.execute(insert_sql, values)
                    inserted_count += 1
            
            conn.execute("COMMIT")
            
        except Exception as e:
            conn.execute("ROLLBACK")
            print(f"💥 Bulk insert error: {e}")
            return 0, 0
        
        return inserted_count, updated_count
    
    def load_metadata(self) -> Dict:
        print("🔥 Loading metadata at MAXIMUM SPEED...")
        with open(self.json_file_path, 'r') as f:
            return json.load(f)
    
    def identify_columns(self, metadata):
        all_columns = []
        
        print("\n🚀 === COLUMN DISCOVERY AT LIGHT SPEED === ⚡")
        
        for table_name, columns in metadata['columns'].items():
            print(f"\n💨 Analyzing table: {table_name}")
            
            # Get row count for this table
            row_count = self.get_table_row_count_fast(table_name)
            
            for column_name, column_type in columns.items():
                mapped_type = None
                
                # Fast column matching (same logic, optimized)
                if isinstance(column_type, str) and column_type.lower() in self.column_mapping:
                    mapped_type = self.column_mapping[column_type.lower()]
                    print(f"  🎯 EXACT MATCH: {column_name} -> {mapped_type}")
                
                if not mapped_type:
                    column_lower = column_name.lower()
                    for pattern in self.hostname_patterns:
                        if pattern in column_lower:
                            mapped_type = 'hostname'
                            print(f"  🌪️ HOSTNAME: {column_name} -> {mapped_type}")
                            break
                
                if not mapped_type:
                    column_lower = column_name.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in column_lower:
                                mapped_type = attr_type
                                print(f"  ⭐ ATTRIBUTE: {column_name} -> {mapped_type}")
                                break
                        if mapped_type:
                            break
                
                if not mapped_type and isinstance(column_type, str):
                    type_lower = column_type.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in type_lower:
                                mapped_type = attr_type
                                print(f"  ✨ TYPE: {column_name} -> {mapped_type}")
                                break
                        if mapped_type:
                            break
                
                if mapped_type:
                    all_columns.append((table_name, column_name, mapped_type))
        
        print(f"\n🔥 === DISCOVERY COMPLETE: {len(all_columns)} columns mapped === 🚀")
        return all_columns
    
    def process_all_parallel(self):
        print("🔥 === INITIATING MAXIMUM PERFORMANCE MODE === 🚀")
        print("⚡ WARNING: CPU USAGE WILL BE EXTREME! FANS WILL SPIN! 🌪️")
        
        self.stats.start_time = time.time()
        self.performance_monitor.start()
        
        try:
            metadata = self.load_metadata()
            all_columns = self.identify_columns(metadata)
            
            columns_by_table = defaultdict(list)
            for table_name, column_name, mapped_type in all_columns:
                columns_by_table[table_name].append((table_name, column_name, mapped_type))
            
            # Create processing chunks for parallel execution
            processing_tasks = []
            
            for table_name, table_columns in columns_by_table.items():
                row_count = self.table_row_counts.get(table_name, 0)
                
                if row_count > self.chunk_size:
                    # Split large tables into chunks
                    num_chunks = (row_count + self.chunk_size - 1) // self.chunk_size
                    print(f"🌪️ Splitting {table_name} ({row_count:,} rows) into {num_chunks} chunks")
                    
                    for i in range(num_chunks):
                        offset = i * self.chunk_size
                        limit = min(self.chunk_size, row_count - offset)
                        processing_tasks.append((table_name, table_columns, offset, limit))
                else:
                    # Process smaller tables as single chunks
                    processing_tasks.append((table_name, table_columns, 0, row_count))
            
            total_tasks = len(processing_tasks)
            print(f"🚀 LAUNCHING {total_tasks} PARALLEL TASKS ACROSS {self.max_workers} WORKERS!")
            print("💨 MAXIMUM PERFORMANCE MODE ENGAGED! 🔥")
            
            # Execute all tasks in parallel
            completed_tasks = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(self.process_table_chunk_parallel, task): task 
                    for task in processing_tasks
                }
                
                # Process completed tasks
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        completed_tasks += 1
                        
                        self.stats.records_processed += result['records']
                        self.stats.records_inserted += result.get('inserted', 0)
                        self.stats.records_updated += result.get('updated', 0)
                        
                        elapsed = time.time() - self.stats.start_time
                        rate = self.stats.records_processed / elapsed if elapsed > 0 else 0
                        
                        print(f"🔥 COMPLETED {completed_tasks}/{total_tasks} | "
                              f"Records: {self.stats.records_processed:,} | "
                              f"Rate: {rate:.0f} rec/sec ⚡")
                        
                    except Exception as e:
                        print(f"💥 Task failed: {task[0]} - {e}")
            
            # Force checkpoint to ensure all data is written
            print("🌪️ Forcing database checkpoint...")
            self.main_conn.execute("CHECKPOINT")
            
            self._create_summary()
            self._show_performance_results()
            
        except Exception as e:
            print(f"💥 CRITICAL ERROR: {e}")
            raise
        finally:
            self.performance_monitor.stop()
    
    def _create_summary(self):
        try:
            print("🚀 Creating performance summary...")
            self.main_conn.execute("DROP TABLE IF EXISTS all_sources")
            
            create_sql = """
            CREATE TABLE all_sources AS (
                SELECT 
                    normalized_host as host,
                    source_tables,
                    hostname, fqdn, domain, infrastructure_type, region, country,
                    data_center, cloud_region, ip_address, class, system_classification,
                    business_unit, apm, cio, edr_coverage, tanium_coverage, 
                    dlp_agent_coverage, logging_in_splunk, logging_in_gso,
                    LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count,
                    last_updated
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                ORDER BY source_count DESC, normalized_host
            )
            """
            self.main_conn.execute(create_sql)
            print("⚡ Summary table created successfully")
        except Exception as e:
            print(f"💥 Error creating summary: {e}")
    
    def _show_performance_results(self):
        total_time = time.time() - self.stats.start_time
        total_records = self.main_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"\n🔥 === PERFORMANCE RESULTS === 🚀")
        print(f"⚡ Total Processing Time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
        print(f"💨 Records Processed: {self.stats.records_processed:,}")
        print(f"🌪️ Records in Database: {total_records:,}")
        print(f"🎯 Processing Rate: {self.stats.records_processed/total_time:.0f} records/second")
        print(f"⭐ New Records: {self.stats.records_inserted:,}")
        print(f"✨ Updated Records: {self.stats.records_updated:,}")
        
        # Performance analysis
        if self.stats.records_processed > 0:
            efficiency = (total_records / self.stats.records_processed) * 100
            print(f"🚀 Data Efficiency: {efficiency:.1f}%")
        
        total_source_rows = sum(self.table_row_counts.values())
        print(f"💥 Source Rows Scanned: {total_source_rows:,}")
        
        if total_source_rows > 1000000:
            print("🔥 BIG DATA PROCESSING COMPLETE - FANS CAN SLOW DOWN NOW! 🌪️")
        elif total_source_rows > 100000:
            print("⚡ HIGH-VOLUME PROCESSING SUCCESSFUL! 💨")
        
        # Show column population stats
        columns = ['hostname', 'business_unit', 'region', 'infrastructure_type', 
                  'edr_coverage', 'logging_in_splunk']
        
        print(f"\n💨 Key Column Population:")
        for col in columns:
            count = self.main_conn.execute(
                f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            ).fetchone()[0]
            pct = (count / total_records * 100) if total_records > 0 else 0
            print(f"  🎯 {col}: {count:,} ({pct:.1f}%)")
    
    def export_fast(self, filename="universal_cmdb_export.csv"):
        print(f"🚀 HIGH-SPEED EXPORT to {filename}...")
        start_time = time.time()
        
        # Use DuckDB's optimized CSV export
        self.main_conn.execute(f"""
            COPY (SELECT * FROM universal_cmdb ORDER BY normalized_host) 
            TO '{filename}' WITH (FORMAT CSV, HEADER, DELIMITER ',')
        """)
        
        export_time = time.time() - start_time
        
        try:
            file_size = os.path.getsize(filename)
            file_size_mb = file_size / (1024 * 1024)
            rate_mb_s = file_size_mb / export_time if export_time > 0 else 0
            
            print(f"⚡ Export complete: {filename}")
            print(f"💨 File size: {file_size_mb:.2f} MB")
            print(f"🔥 Export time: {export_time:.2f} seconds")
            print(f"🌪️ Export rate: {rate_mb_s:.1f} MB/second")
            
        except Exception as e:
            print(f"✨ Export completed: {filename}")
    
    def close(self):
        print("🚀 Shutting down HIGH-PERFORMANCE system...")
        self.performance_monitor.stop()
        
        # Close all connections
        for conn in self.connection_pool:
            try:
                conn.close()
            except:
                pass
        
        self.main_conn.close()
        
        total_time = time.time() - self.stats.start_time if self.stats.start_time else 0
        print(f"🔥 HIGH-PERFORMANCE SESSION COMPLETE: {total_time/60:.1f} minutes total")

if __name__ == "__main__":
    print("🔥 === HIGH-PERFORMANCE HOST DATA PROCESSOR === 🚀")
    print("⚡ WARNING: MAXIMUM CPU USAGE INCOMING! 🌪️")
    print("💨 Your fans WILL spin at maximum speed! 💥")
    
    processor = HighPerformanceHostProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
    
    try:
        processor.process_all_parallel()
        processor.export_fast()
        print("\n🔥 === MAXIMUM PERFORMANCE PROCESSING COMPLETE === 🚀")
        print("⚡ Mission accomplished - your machine survived the intensity! 💥")
        
    except KeyboardInterrupt:
        print("\n🌪️ Process interrupted - emergency shutdown!")
    except Exception as e:
        print(f"💥 Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close()
        print("💨 All systems powered down - fans returning to normal 🔥")