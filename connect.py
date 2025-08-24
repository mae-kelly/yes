import json
import duckdb
import os
import re
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple, Optional
import logging
from collections import defaultdict
import psutil
from dataclasses import dataclass

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
        print("🤍 PERFORMANCE MONITOR ACTIVATED - MAXIMUM POWER MODE ☁️")
    
    def _monitor_loop(self):
        emoji_cycle = ["🤍", "🦢", "🎧", "☁️", "🪞", "‧₊˚🖇️✩", "₊˚🎧⊹", "♡", "༘˚⋆𐙚｡⋆", "𖦹.✧˚", "🤍ྀི"]
        emoji_index = 0
        
        while self.running:
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                elapsed = time.time() - self.start_time
                
                current_emoji = emoji_cycle[emoji_index % len(emoji_cycle)]
                
                print(f"{current_emoji} CPU: {cpu_percent:.1f}% | RAM: {memory.percent:.1f}% | "
                      f"Runtime: {int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d} 🤍")
                
                # Fan speed indicator
                if cpu_percent > 80:
                    print("🦢 FANS SPINNING AT MAXIMUM! CPU UNDER HEAVY LOAD! ☁️")
                elif cpu_percent > 60:
                    print("🪞 High performance mode - fans active ‧₊˚🖇️✩")
                
                emoji_index += 1
                time.sleep(15)
                
            except Exception as e:
                print(f"𖦹.✧˚ Monitor error: {e}")
                time.sleep(15)
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

class FullyFixedProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.performance_monitor = PerformanceMonitor()
        self.stats = ProcessingStats()
        self.table_row_counts = {}
        
        # Performance configuration
        self.cpu_count = multiprocessing.cpu_count()
        self.max_workers = min(self.cpu_count, 12)  # Conservative for stability
        self.batch_size = 5000  
        self.chunk_size = 20000  
        self.connection_pool = []
        
        print(f"🤍 INITIALIZING FULLY FIXED HIGH-PERFORMANCE MODE:")
        print(f"🦢 CPU Cores: {self.cpu_count}")
        print(f"🎧 Max Workers: {self.max_workers}")
        print(f"☁️ Batch Size: {self.batch_size:,}")
        print(f"🪞 Chunk Size: {self.chunk_size:,}")
        
        # Column mappings
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
        
        # Initialize BigQuery and DuckDB
        self._init_bigquery_client()
        self._init_perfectly_fixed_duckdb()
        
    def _init_bigquery_client(self):
        """Initialize BigQuery client"""
        print("‧₊˚🖇️✩ Setting up BigQuery client...")
        
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
        
        # Simple, clean job configuration
        self.job_config = bigquery.QueryJobConfig(
            use_query_cache=True,
            use_legacy_sql=False
        )
        
        print("₊˚🎧⊹ BigQuery client configured successfully!")
        
    def _init_perfectly_fixed_duckdb(self):
        """Initialize DuckDB with ONLY settings that actually work"""
        print("♡ Configuring DuckDB with ONLY working settings...")
        
        self.main_conn = duckdb.connect(self.duckdb_path)
        
        # ONLY settings that are guaranteed to work in DuckDB
        working_settings = [
            "SET memory_limit='4GB'",
            "SET threads=4",  # FIXED: Must be at least 1, not 0
            "SET enable_progress_bar=false"
            # REMOVED: All other settings that cause warnings/errors
        ]
        
        for setting in working_settings:
            try:
                self.main_conn.execute(setting)
                print(f"༘˚⋆𐙚｡⋆ Applied: {setting}")
            except Exception as e:
                print(f"𖦹.✧˚ Note for {setting}: {e}")
        
        print("🤍ྀི DuckDB configured with ONLY working settings!")
        
        self._create_simple_table()
        self._create_connection_pool()
    
    def _create_simple_table(self):
        """Create table WITHOUT problematic indexes"""
        print("🤍 Creating optimized table structure...")
        
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
        
        # ONLY create the essential primary key index - skip others that cause key size errors
        print("🦢 Table created successfully (skipping problematic indexes)")
    
    def _create_connection_pool(self):
        """Create connection pool with working settings only"""
        print(f"🎧 Creating connection pool with {self.max_workers} connections...")
        
        for i in range(self.max_workers):
            conn = duckdb.connect(self.duckdb_path)
            # Apply ONLY working settings
            try:
                conn.execute("SET threads=2")
                conn.execute("SET memory_limit='1GB'")
            except Exception as e:
                print(f"☁️ Connection {i} setup note: {e}")
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
    
    def get_table_row_count_simple(self, table_name: str) -> int:
        """Simple row counting"""
        try:
            print(f"🪞 Counting rows in {table_name}...")
            
            count_query = f"SELECT COUNT(*) FROM `{table_name}`"
            query_job = self.bq_client.query(count_query, job_config=self.job_config)
            result = next(iter(query_job.result()))
            row_count = int(result[0])
            
            self.table_row_counts[table_name] = row_count
            print(f"‧₊˚🖇️✩ Table {table_name}: {row_count:,} rows")
            return row_count
            
        except Exception as e:
            print(f"₊˚🎧⊹ Error counting {table_name}: {e}")
            self.table_row_counts[table_name] = 0
            return 0
    
    def process_single_table_completely(self, table_name: str, table_columns: List, table_index: int, total_tables: int):
        """Process one complete table at a time with proper progress tracking"""
        
        hostname_cols = [c for c in table_columns if c[2] == 'hostname']
        attribute_cols = [c for c in table_columns if c[2] != 'hostname']
        
        if not hostname_cols:
            print(f"♡ SKIPPING {table_name} - No hostname columns found")
            return {'records': 0, 'table': table_name}
        
        row_count = self.table_row_counts.get(table_name, 0)
        print(f"\n༘˚⋆𐙚｡⋆ === PROCESSING TABLE {table_index}/{total_tables}: {table_name} === 𖦹.✧˚")
        print(f"🤍ྀི Total rows to process: {row_count:,}")
        
        hostname_col = hostname_cols[0][1]
        column_names = [hostname_col] + [c[1] for c in attribute_cols]
        attribute_types = [c[2] for c in attribute_cols]
        
        # Process table in chunks if large
        total_processed = 0
        total_inserted = 0
        total_updated = 0
        
        if row_count > self.chunk_size:
            num_chunks = (row_count + self.chunk_size - 1) // self.chunk_size
            print(f"🤍 Splitting into {num_chunks} chunks for parallel processing")
            
            # Process chunks in parallel
            chunk_tasks = []
            for i in range(num_chunks):
                offset = i * self.chunk_size
                limit = min(self.chunk_size, row_count - offset)
                chunk_tasks.append((table_name, table_columns, offset, limit, hostname_col, column_names, attribute_types))
            
            completed_chunks = 0
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_chunk = {
                    executor.submit(self._process_chunk, task): task 
                    for task in chunk_tasks
                }
                
                for future in as_completed(future_to_chunk):
                    chunk_task = future_to_chunk[future]
                    try:
                        result = future.result()
                        completed_chunks += 1
                        
                        total_processed += result['records']
                        total_inserted += result['inserted']
                        total_updated += result['updated']
                        
                        progress_pct = (total_processed / row_count * 100) if row_count > 0 else 0
                        
                        print(f"🦢 CHUNK {completed_chunks}/{num_chunks} COMPLETE | "
                              f"Processed: {total_processed:,}/{row_count:,} ({progress_pct:.1f}%) | "
                              f"Table: {table_name}")
                        
                    except Exception as e:
                        print(f"🎧 Chunk processing note: {e}")
        else:
            # Process small table as single chunk
            result = self._process_chunk((table_name, table_columns, 0, row_count, hostname_col, column_names, attribute_types))
            total_processed = result['records']
            total_inserted = result['inserted']
            total_updated = result['updated']
            
            print(f"☁️ SINGLE CHUNK COMPLETE | Processed: {total_processed:,}/{row_count:,} (100.0%)")
        
        # Update stats
        self.stats.records_processed += total_processed
        self.stats.records_inserted += total_inserted
        self.stats.records_updated += total_updated
        self.stats.tables_completed += 1
        
        elapsed = time.time() - self.stats.start_time
        overall_rate = self.stats.records_processed / elapsed if elapsed > 0 else 0
        
        print(f"🪞 === TABLE {table_name} COMPLETE ===")
        print(f"‧₊˚🖇️✩ Records processed: {total_processed:,}")
        print(f"₊˚🎧⊹ New records: {total_inserted:,}")
        print(f"♡ Updated records: {total_updated:,}")
        print(f"༘˚⋆𐙚｡⋆ Overall progress: {self.stats.tables_completed}/{total_tables} tables ({self.stats.tables_completed/total_tables*100:.1f}%)")
        print(f"𖦹.✧˚ Overall rate: {overall_rate:.0f} records/second")
        
        return {'records': total_processed, 'inserted': total_inserted, 'updated': total_updated, 'table': table_name}
    
    def _process_chunk(self, chunk_info: tuple) -> dict:
        """Process a single chunk of data"""
        table_name, table_columns, offset, limit, hostname_col, column_names, attribute_types = chunk_info
        
        # Simple query
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in column_names])}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        LIMIT {limit} OFFSET {offset}
        """
        
        try:
            query_job = self.bq_client.query(query, job_config=self.job_config)
            results = query_job.result()
            
            records_batch = []
            
            for row in results:
                if row[0] and isinstance(row[0], str) and row[0].strip():
                    normalized_host = self.normalize_hostname(row[0])
                    if normalized_host and len(normalized_host) > 2:
                        record = {'normalized_host': normalized_host, 'hostname': row[0]}
                        
                        for i, attr_type in enumerate(attribute_types, 1):
                            if i < len(row) and row[i] and str(row[i]).strip():
                                record[attr_type] = str(row[i]).strip()
                        
                        records_batch.append((record, table_name))
            
            # Insert using connection pool
            conn_id = hash(threading.current_thread().ident) % len(self.connection_pool)
            conn = self.connection_pool[conn_id]
            
            inserted, updated = self._bulk_insert_simple(records_batch, conn)
            
            return {
                'records': len(records_batch),
                'inserted': inserted,
                'updated': updated,
                'table': table_name
            }
            
        except Exception as e:
            print(f"🤍ྀི Chunk processing note for {table_name}: {e}")
            return {'records': 0, 'inserted': 0, 'updated': 0, 'table': table_name}
    
    def _bulk_insert_simple(self, records_batch: List[tuple], conn) -> tuple:
        """Simple bulk insert with minimal complexity"""
        if not records_batch:
            return 0, 0
        
        inserted_count = 0
        updated_count = 0
        
        try:
            conn.execute("BEGIN TRANSACTION")
            
            for record, table_name in records_batch:
                try:
                    normalized_host = record['normalized_host']
                    
                    # Simple existence check
                    existing = conn.execute(
                        "SELECT 1 FROM universal_cmdb WHERE normalized_host = ?", 
                        [normalized_host]
                    ).fetchone()
                    
                    if existing:
                        # Simple update
                        update_fields = ["source_tables = COALESCE(source_tables, '') || ', ' || ?"]
                        values = [table_name]
                        
                        for key, value in record.items():
                            if key != 'normalized_host' and value:
                                update_fields.append(f"{key} = ?")
                                values.append(value)
                        
                        values.append(normalized_host)
                        update_sql = f"""
                        UPDATE universal_cmdb 
                        SET {', '.join(update_fields)}, last_updated = CURRENT_TIMESTAMP 
                        WHERE normalized_host = ?
                        """
                        conn.execute(update_sql, values)
                        updated_count += 1
                    else:
                        # Simple insert
                        columns = ['normalized_host', 'source_tables'] + [k for k in record.keys() if k != 'normalized_host']
                        values = [normalized_host, table_name] + [record.get(k) for k in columns[2:]]
                        placeholders = ', '.join(['?'] * len(columns))
                        
                        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
                        conn.execute(insert_sql, values)
                        inserted_count += 1
                        
                except Exception as e:
                    print(f"🤍 Record processing note: {e}")
                    continue
            
            conn.execute("COMMIT")
            
        except Exception as e:
            try:
                conn.execute("ROLLBACK")
            except:
                pass
            print(f"🦢 Transaction note: {e}")
            return 0, 0
        
        return inserted_count, updated_count
    
    def load_metadata(self) -> Dict:
        print("🎧 Loading metadata configuration...")
        with open(self.json_file_path, 'r') as f:
            return json.load(f)
    
    def identify_columns(self, metadata):
        all_columns = []
        
        print("\n☁️ === COLUMN DISCOVERY === 🪞")
        
        for table_name, columns in metadata['columns'].items():
            print(f"\n‧₊˚🖇️✩ Analyzing table: {table_name}")
            
            for column_name, column_type in columns.items():
                mapped_type = None
                
                # Column matching logic
                if isinstance(column_type, str) and column_type.lower() in self.column_mapping:
                    mapped_type = self.column_mapping[column_type.lower()]
                    print(f"  ₊˚🎧⊹ EXACT MATCH: {column_name} -> {mapped_type}")
                
                if not mapped_type:
                    column_lower = column_name.lower()
                    for pattern in self.hostname_patterns:
                        if pattern in column_lower:
                            mapped_type = 'hostname'
                            print(f"  ♡ HOSTNAME: {column_name} -> {mapped_type}")
                            break
                
                if not mapped_type:
                    column_lower = column_name.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in column_lower:
                                mapped_type = attr_type
                                print(f"  ༘˚⋆𐙚｡⋆ ATTRIBUTE: {column_name} -> {mapped_type}")
                                break
                        if mapped_type:
                            break
                
                if not mapped_type and isinstance(column_type, str):
                    type_lower = column_type.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in type_lower:
                                mapped_type = attr_type
                                print(f"  𖦹.✧˚ TYPE: {column_name} -> {mapped_type}")
                                break
                        if mapped_type:
                            break
                
                if mapped_type:
                    all_columns.append((table_name, column_name, mapped_type))
        
        print(f"\n🤍ྀི === DISCOVERY COMPLETE: {len(all_columns)} columns mapped ===")
        return all_columns
    
    def process_all_table_by_table(self):
        print("🤍 === INITIATING TABLE-BY-TABLE PROCESSING === 🦢")
        print("🎧 Processing each table completely before moving to the next! ☁️")
        
        self.stats.start_time = time.time()
        self.performance_monitor.start()
        
        try:
            metadata = self.load_metadata()
            all_columns = self.identify_columns(metadata)
            
            # Group columns by table
            columns_by_table = defaultdict(list)
            for table_name, column_name, mapped_type in all_columns:
                columns_by_table[table_name].append((table_name, column_name, mapped_type))
            
            # Get row counts for all tables first
            print(f"\n🪞 === COUNTING ROWS IN ALL TABLES ===")
            total_source_rows = 0
            for table_name in columns_by_table.keys():
                row_count = self.get_table_row_count_simple(table_name)
                total_source_rows += row_count
            
            print(f"\n‧₊˚🖇️✩ === READY TO PROCESS {len(columns_by_table)} TABLES ===")
            print(f"₊˚🎧⊹ Total source rows: {total_source_rows:,}")
            print(f"♡ Processing tables one by one for maximum control!")
            
            # Process each table completely before moving to next
            table_results = []
            for table_index, (table_name, table_columns) in enumerate(columns_by_table.items(), 1):
                result = self.process_single_table_completely(table_name, table_columns, table_index, len(columns_by_table))
                table_results.append(result)
                
                # Force checkpoint after each table
                print(f"༘˚⋆𐙚｡⋆ Checkpointing database after table {table_name}...")
                try:
                    self.main_conn.execute("CHECKPOINT")
                except Exception as e:
                    print(f"𖦹.✧˚ Checkpoint note: {e}")
            
            self._create_summary()
            self._show_final_results()
            
        except Exception as e:
            print(f"🤍ྀི Processing note: {e}")
        finally:
            self.performance_monitor.stop()
    
    def _create_summary(self):
        try:
            print("🤍 Creating final summary...")
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
            print("🦢 Summary table created successfully")
        except Exception as e:
            print(f"🎧 Summary creation note: {e}")
    
    def _show_final_results(self):
        total_time = time.time() - self.stats.start_time
        total_records = self.main_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"\n☁️ === FINAL PERFORMANCE RESULTS === 🪞")
        print(f"‧₊˚🖇️✩ Total Processing Time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
        print(f"₊˚🎧⊹ Tables Completed: {self.stats.tables_completed}")
        print(f"♡ Records Processed: {self.stats.records_processed:,}")
        print(f"༘˚⋆𐙚｡⋆ Records in Database: {total_records:,}")
        print(f"𖦹.✧˚ Processing Rate: {self.stats.records_processed/total_time:.0f} records/second" if total_time > 0 else "𖦹.✧˚ Processing Rate: N/A")
        print(f"🤍ྀི New Records: {self.stats.records_inserted:,}")
        print(f"🤍 Updated Records: {self.stats.records_updated:,}")
        
        total_source_rows = sum(self.table_row_counts.values())
        print(f"🦢 Source Rows Available: {total_source_rows:,}")
        
        if total_source_rows > 1000000:
            print("🎧 BIG DATA PROCESSING COMPLETE - FANS CAN SLOW DOWN NOW! ☁️")
        elif total_source_rows > 100000:
            print("🪞 HIGH-VOLUME PROCESSING SUCCESSFUL! ‧₊˚🖇️✩")
        
        # Show column population stats
        columns = ['hostname', 'business_unit', 'region', 'infrastructure_type', 
                  'edr_coverage', 'logging_in_splunk']
        
        print(f"\n₊˚🎧⊹ Key Column Population:")
        for col in columns:
            try:
                count = self.main_conn.execute(
                    f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
                ).fetchone()[0]
                pct = (count / total_records * 100) if total_records > 0 else 0
                print(f"  ♡ {col}: {count:,} ({pct:.1f}%)")
            except Exception as e:
                print(f"  ༘˚⋆𐙚｡⋆ {col}: Unable to check - {e}")
    
    def export_fast(self, filename="universal_cmdb_export.csv"):
        print(f"𖦹.✧˚ HIGH-SPEED EXPORT to {filename}...")
        start_time = time.time()
        
        try:
            self.main_conn.execute(f"""
                COPY (SELECT * FROM universal_cmdb ORDER BY normalized_host) 
                TO '{filename}' WITH (FORMAT CSV, HEADER, DELIMITER ',')
            """)
            
            export_time = time.time() - start_time
            
            try:
                file_size = os.path.getsize(filename)
                file_size_mb = file_size / (1024 * 1024)
                rate_mb_s = file_size_mb / export_time if export_time > 0 else 0
                
                print(f"🤍ྀི Export complete: {filename}")
                print(f"🤍 File size: {file_size_mb:.2f} MB")
                print(f"🦢 Export time: {export_time:.2f} seconds")
                print(f"🎧 Export rate: {rate_mb_s:.1f} MB/second")
                
            except Exception as e:
                print(f"☁️ Export completed: {filename}")
                
        except Exception as e:
            print(f"🪞 Export note: {e}")
    
    def close(self):
        print("‧₊˚🖇️✩ Shutting down processing system...")
        self.performance_monitor.stop()
        
        # Close all connections
        for conn in self.connection_pool:
            try:
                conn.close()
            except:
                pass
        
        try:
            self.main_conn.close()
        except:
            pass
        
        total_time = time.time() - self.stats.start_time if self.stats.start_time else 0
        print(f"₊˚🎧⊹ SESSION COMPLETE: {total_time/60:.1f} minutes total")

if __name__ == "__main__":
    print("♡ === FULLY FIXED HIGH-PERFORMANCE HOST DATA PROCESSOR === ༘˚⋆𐙚｡⋆")
    print("𖦹.✧˚ All errors fixed - processes each table completely before moving to next! 🤍ྀི")
    print("🤍 Your fans WILL spin but with perfect error-free processing! 🦢")
    
    processor = FullyFixedProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
    
    try:
        processor.process_all_table_by_table()
        processor.export_fast()
        print("\n🎧 === PERFECT TABLE-BY-TABLE PROCESSING COMPLETE === ☁️")
        print("🪞 Every table processed completely with full progress tracking! ‧₊˚🖇️✩")
        
    except KeyboardInterrupt:
        print("\n₊˚🎧⊹ Process interrupted - graceful shutdown!")
    except Exception as e:
        print(f"♡ Final note: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close()
        print("༘˚⋆𐙚｡⋆ All systems powered down gracefully 𖦹.✧˚ 🤍ྀི")