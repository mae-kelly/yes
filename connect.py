import json
import duckdb
import os
import re
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple, Optional
import logging
from collections import defaultdict, Counter
import time
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import subprocess
import sys
import platform
import asyncio
import gc
import mmap
from queue import Queue

# Disable logging for max speed
logging.disable(logging.CRITICAL)

class UltraFastCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        print("🚀 ULTRA-FAST CMDB PROCESSOR - MAXIMUM SPEED MODE")
        print("=" * 80)
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Get all CPU cores - use threading instead of multiprocessing
        self.cpu_count = multiprocessing.cpu_count()
        self.max_workers = min(20, self.cpu_count * 3)  # Cap at 20 threads max
        
        # Massive batch sizes for speed
        self.batch_size = 100000  # Even bigger batches
        self.insert_batch_size = 20000  # Huge bulk inserts
        
        print(f"🔥 Using {self.cpu_count} CPU cores with {self.max_workers} worker threads")
        print(f"⚡ Batch size: {self.batch_size:,} | Insert batch: {self.insert_batch_size:,}")
        
        # Pre-compiled regex for speed
        self.hostname_cleaner = re.compile(r'[^a-z0-9]')
        
        # Fast column mapping (no complex patterns - just exact matches)
        self.fast_column_map = {
            'hostname': 'hostname', 'host': 'hostname', 'fqdn': 'fqdn',
            'domain': 'domain', 'region': 'region', 'country': 'country',
            'business_unit': 'business_unit', 'bu': 'business_unit',
            'infrastructure_type': 'infrastructure_type', 'infra_type': 'infrastructure_type',
            'data_center': 'data_center', 'datacenter': 'data_center',
            'ip_address': 'ip_address', 'ip': 'ip_address',
            'class': 'class', 'system_classification': 'system_classification',
            'apm': 'apm', 'cio': 'cio', 'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage', 'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk', 'logging_in_gso': 'logging_in_gso'
        }
        
        # Thread-safe caches for speed
        self.seen_hosts = set()
        self.seen_hosts_lock = threading.Lock()
        
        # Stats tracking
        self.stats = {
            'start_time': time.time(),
            'tables_processed': 0,
            'records_processed': 0,
            'hosts_created': 0,
            'hosts_updated': 0,
            'duplicates_skipped': 0,
            'stats_lock': threading.Lock()
        }
        
        # Thread-local storage for BigQuery clients
        self.thread_local = threading.local()
        
        self._init_duckdb_ultra_fast()
        
        print("✅ Initialization complete - READY FOR MAXIMUM SPEED")
        print("=" * 80)
    
    def _get_bq_client(self):
        """Get thread-local BigQuery client"""
        if not hasattr(self.thread_local, 'bq_client'):
            service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
            
            if os.path.exists(service_account_file):
                credentials = service_account.Credentials.from_service_account_file(service_account_file)
                self.thread_local.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
            else:
                self.thread_local.bq_client = bigquery.Client(project="chronicle-fisv")
        
        return self.thread_local.bq_client
    
    def _init_duckdb_ultra_fast(self):
        """Ultra-fast DuckDB setup with performance optimizations"""
        self.duck_conn = duckdb.connect(self.duckdb_path)
        
        # MAXIMUM PERFORMANCE SETTINGS
        performance_settings = [
            "SET memory_limit='80%'",  # Use 80% of available RAM
            f"SET threads TO {self.cpu_count}",
            "SET max_memory='80GB'",
            "SET enable_progress_bar=false",
            "SET enable_profiling=false",
            "SET checkpoint_threshold='2GB'",
            "SET wal_autocheckpoint=50000",
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=OFF",  # DANGEROUS BUT FAST
            "PRAGMA cache_size=2000000",  # 2M pages in cache
            "PRAGMA temp_store=MEMORY",
            "PRAGMA mmap_size=2000000000"  # 2GB memory map
        ]
        
        for setting in performance_settings:
            try:
                self.duck_conn.execute(setting)
            except:
                pass
        
        # Create table with minimal constraints for speed
        create_sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(create_sql)
        
        # Defer index creation until the end for speed
        print("⚡ DuckDB optimized for MAXIMUM SPEED (indexes deferred)")
    
    def normalize_hostname_fast(self, hostname: str) -> str:
        """Ultra-fast hostname normalization"""
        if not hostname or len(hostname) < 2:
            return ""
        
        # Fast string operations
        normalized = hostname.lower().strip()
        
        # Quick FQDN check
        dot_pos = normalized.find('.')
        if dot_pos > 0:
            normalized = normalized[:dot_pos]
        
        # Single regex pass
        normalized = self.hostname_cleaner.sub('', normalized)
        
        return normalized if len(normalized) > 1 else ""
    
    def load_metadata_fast(self) -> Dict:
        """Lightning-fast metadata loading"""
        print("📂 Loading metadata...")
        start = time.time()
        
        # Use memory mapping for large files
        try:
            with open(self.json_file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    metadata = json.loads(mm.read().decode('utf-8'))
        except:
            # Fallback to regular loading
            with open(self.json_file_path, 'r') as f:
                metadata = json.load(f)
        
        load_time = time.time() - start
        table_count = len(metadata.get('columns', {}))
        
        print(f"✅ Loaded {table_count:,} tables in {load_time:.2f}s")
        return metadata
    
    def discover_columns_fast(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        """Ultra-fast column discovery - no complex pattern matching"""
        print("🔍 Fast column discovery...")
        
        discovered = []
        
        if 'columns' not in metadata:
            return []
        
        # Simple, fast matching
        for table_name, columns in metadata['columns'].items():
            for col_name, col_type in columns.items():
                col_lower = col_name.lower()
                
                # Direct lookup for speed
                if col_lower in self.fast_column_map:
                    mapped_type = self.fast_column_map[col_lower]
                    discovered.append((table_name, col_name, mapped_type))
                # Quick hostname detection
                elif 'host' in col_lower or 'fqdn' in col_lower:
                    discovered.append((table_name, col_name, 'hostname'))
        
        print(f"✅ Found {len(discovered):,} mappable columns")
        return discovered
    
    def build_ultra_fast_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        """Build optimized query for maximum speed"""
        # Select only what we need
        column_selects = [f"`{col}`" for col in columns]
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND LENGTH(`{hostname_col}`) > 1
        AND `{hostname_col}` != '*Undefined'
        """
    
    def process_table_ultra_fast(self, table_info: Tuple) -> int:
        """Process a single table at maximum speed"""
        table_name, table_columns = table_info
        
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        if not hostname_cols:
            return 0
        
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        primary_hostname_col = hostname_cols[0][0]
        
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        query = self.build_ultra_fast_query(table_name, all_columns, primary_hostname_col)
        
        try:
            # Get thread-local BigQuery client
            bq_client = self._get_bq_client()
            
            # Ultra-aggressive BigQuery settings
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                use_legacy_sql=False,
                maximum_bytes_billed=200 * 1024 * 1024 * 1024,  # 200GB limit
                job_timeout_ms=15 * 60 * 1000,  # 15 minutes max
                dry_run=False
            )
            
            query_job = bq_client.query(query, job_config=job_config)
            results = query_job.result(page_size=self.batch_size)
            
            return self._process_results_ultra_fast(results, table_name, attribute_types)
            
        except Exception as e:
            print(f"❌ Error in {os.path.basename(table_name)}: {str(e)[:50]}...")
            return 0
    
    def _process_results_ultra_fast(self, results, table_name: str, attribute_types: List[str]) -> int:
        """Ultra-fast result processing with bulk operations"""
        records_processed = 0
        batch_records = []
        local_duplicates = 0
        
        for row in results:
            records_processed += 1
            
            # Quick validation
            if not row[0] or len(str(row[0])) < 2:
                continue
            
            normalized_host = self.normalize_hostname_fast(str(row[0]))
            if not normalized_host:
                continue
            
            # Thread-safe duplicate check
            is_duplicate = False
            with self.seen_hosts_lock:
                if normalized_host in self.seen_hosts:
                    is_duplicate = True
                    local_duplicates += 1
                else:
                    self.seen_hosts.add(normalized_host)
            
            if is_duplicate:
                continue
            
            # Build record data
            record_data = {
                'normalized_host': normalized_host,
                'hostname': str(row[0]).strip(),
                'source_tables': table_name
            }
            
            # Fast attribute extraction
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and row[i] and str(row[i]).strip():
                    record_data[attr_type] = str(row[i]).strip()
            
            batch_records.append(record_data)
            
            # Bulk insert when batch is full
            if len(batch_records) >= self.insert_batch_size:
                created = self._bulk_insert_ultra_fast(batch_records)
                batch_records.clear()
                
                # Update stats
                with self.stats['stats_lock']:
                    self.stats['records_processed'] += records_processed
                    self.stats['hosts_created'] += created
                    self.stats['duplicates_skipped'] += local_duplicates
                
                # Quick progress update
                if self.stats['records_processed'] % 100000 == 0:
                    elapsed = time.time() - self.stats['start_time']
                    rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
                    print(f"⚡ {self.stats['records_processed']:,} processed | {rate:.0f}/sec | {local_duplicates:,} dups")
                
                records_processed = 0
                local_duplicates = 0
        
        # Insert remaining records
        if batch_records:
            created = self._bulk_insert_ultra_fast(batch_records)
            
            # Final stats update
            with self.stats['stats_lock']:
                self.stats['records_processed'] += records_processed
                self.stats['hosts_created'] += created
                self.stats['duplicates_skipped'] += local_duplicates
        
        return records_processed
    
    def _bulk_insert_ultra_fast(self, batch_records: List[Dict]) -> int:
        """Ultra-fast bulk insert using DuckDB's native bulk loading"""
        if not batch_records:
            return 0
        
        # Prepare bulk insert data
        columns = ['normalized_host', 'source_tables', 'hostname']
        data_columns = ['fqdn', 'domain', 'infrastructure_type', 'region', 'country',
                       'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
                       'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
                       'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso']
        
        all_columns = columns + data_columns
        
        # Build values for bulk insert
        values_list = []
        for record in batch_records:
            row_values = [
                record['normalized_host'],
                record['source_tables'],
                record['hostname']
            ]
            
            # Add data columns
            for col in data_columns:
                row_values.append(record.get(col))
            
            values_list.append(row_values)
        
        # Ultra-fast bulk insert with connection pooling
        placeholders = ', '.join(['?' for _ in all_columns])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(all_columns)}, source_count) VALUES ({placeholders}, 1)"
        
        try:
            # Use a transaction for maximum speed
            self.duck_conn.execute("BEGIN TRANSACTION")
            self.duck_conn.executemany(insert_sql, values_list)
            self.duck_conn.execute("COMMIT")
            return len(batch_records)
        except Exception as e:
            self.duck_conn.execute("ROLLBACK")
            print(f"⚠️  Bulk insert error: {str(e)[:50]}...")
            return 0
    
    def process_all_ultra_fast(self):
        """Main processing function - MAXIMUM SPEED with threading"""
        print("\n🚀 STARTING ULTRA-FAST THREADED PROCESSING")
        print("=" * 60)
        
        # Load metadata
        metadata = self.load_metadata_fast()
        discovered_columns = self.discover_columns_fast(metadata)
        
        if not discovered_columns:
            print("❌ No processable columns found")
            return
        
        # Group by table
        columns_by_table = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((table_name, column_name, column_type))
        
        total_tables = len(columns_by_table)
        print(f"🎯 Processing {total_tables:,} tables with {self.max_workers} threads")
        
        # Process tables in parallel using ThreadPoolExecutor
        start_time = time.time()
        completed_tables = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tables
            future_to_table = {
                executor.submit(self.process_table_ultra_fast, table_info): table_name
                for table_name, table_info in [(name, (name, cols)) for name, cols in columns_by_table.items()]
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_table):
                table_name = future_to_table[future]
                completed_tables += 1
                
                try:
                    records_processed = future.result()
                    
                    elapsed = time.time() - start_time
                    progress = (completed_tables / total_tables) * 100
                    
                    with self.stats['stats_lock']:
                        total_processed = self.stats['records_processed']
                        total_hosts = self.stats['hosts_created']
                        total_dups = self.stats['duplicates_skipped']
                    
                    rate = total_processed / elapsed if elapsed > 0 else 0
                    
                    print(f"🔥 {completed_tables}/{total_tables} ({progress:.1f}%) | "
                          f"{total_processed:,} records | {total_hosts:,} hosts | "
                          f"{rate:.0f}/sec | {os.path.basename(table_name)}")
                    
                except Exception as e:
                    print(f"❌ Table error {os.path.basename(table_name)}: {str(e)[:30]}...")
        
        # Create indexes now for better query performance
        print("\n🔧 Creating final indexes...")
        index_start = time.time()
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_business_unit ON universal_cmdb(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)"
        ]
        
        for index_sql in indexes:
            try:
                self.duck_conn.execute(index_sql)
            except Exception as e:
                print(f"⚠️  Index creation warning: {str(e)[:30]}...")
        
        index_time = time.time() - index_start
        print(f"✅ Indexes created in {index_time:.2f}s")
        
        self._generate_ultra_fast_summary(start_time)
    
    def _generate_ultra_fast_summary(self, start_time: float):
        """Generate final summary at maximum speed"""
        total_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("🏆 ULTRA-FAST PROCESSING COMPLETE!")
        print("=" * 80)
        
        # Get final stats
        try:
            total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
            
            # Quick data quality check
            business_unit_count = self.duck_conn.execute(
                "SELECT COUNT(*) FROM universal_cmdb WHERE business_unit IS NOT NULL"
            ).fetchone()[0]
            
            region_count = self.duck_conn.execute(
                "SELECT COUNT(*) FROM universal_cmdb WHERE region IS NOT NULL"
            ).fetchone()[0]
            
        except:
            total_hosts = self.stats['hosts_created']
            business_unit_count = 0
            region_count = 0
        
        with self.stats['stats_lock']:
            total_processed = self.stats['records_processed']
            total_duplicates = self.stats['duplicates_skipped']
        
        print(f"⏱️  Total time: {timedelta(seconds=int(total_time))}")
        print(f"📊 Records processed: {total_processed:,}")
        print(f"🎯 Unique hosts: {total_hosts:,}")
        print(f"⚡ Processing speed: {total_processed/total_time:.0f} records/second")
        print(f"🔥 Host creation rate: {total_hosts/total_time:.0f} hosts/second")
        print(f"🚀 Duplicates skipped: {total_duplicates:,}")
        
        # Data quality summary
        if total_hosts > 0:
            bu_pct = (business_unit_count / total_hosts) * 100
            region_pct = (region_count / total_hosts) * 100
            print(f"📈 Business Unit coverage: {business_unit_count:,} ({bu_pct:.1f}%)")
            print(f"🌍 Region coverage: {region_count:,} ({region_pct:.1f}%)")
        
        if total_time < 1800:  # Less than 30 minutes
            print(f"🎉 MISSION ACCOMPLISHED - Completed in {total_time/60:.1f} minutes!")
        elif total_time < 3600:  # Less than 1 hour
            print(f"✅ Excellent time - Completed in {total_time/60:.1f} minutes!")
        else:
            print(f"✅ Completed in {total_time/3600:.1f} hours")
        
        print("=" * 80)
    
    def export_ultra_fast(self, filename: str = "universal_cmdb_ultra_fast.csv"):
        """Ultra-fast export"""
        print(f"📤 Ultra-fast export to {filename}...")
        
        start_time = time.time()
        
        export_query = f"""
        COPY (
            SELECT * FROM universal_cmdb 
            ORDER BY source_count DESC, normalized_host
        ) TO '{filename}' WITH (FORMAT CSV, HEADER)
        """
        
        self.duck_conn.execute(export_query)
        
        export_time = time.time() - start_time
        file_size = os.path.getsize(filename) / (1024 * 1024)
        
        print(f"✅ Exported {file_size:.1f} MB in {export_time:.2f}s ({file_size/export_time:.1f} MB/s)")
    
    def cleanup(self):
        """Fast cleanup"""
        try:
            self.duck_conn.close()
        except:
            pass
        
        # Force garbage collection
        gc.collect()
        
        print("🧹 Cleanup complete")

def run_ultra_fast_processor():
    """Run the ultra-fast processor"""
    processor = None
    
    try:
        processor = UltraFastCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb_ultra.db")
        processor.process_all_ultra_fast()
        processor.export_ultra_fast("universal_cmdb_ultra_fast.csv")
        
    except KeyboardInterrupt:
        print("\n⚠️  PROCESSING INTERRUPTED")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.cleanup()

if __name__ == "__main__":
    # Set process priority to high
    try:
        import psutil
        current_process = psutil.Process()
        if platform.system() == "Windows":
            current_process.nice(psutil.HIGH_PRIORITY_CLASS)
        else:
            current_process.nice(-10)
        print("🔥 Process priority set to HIGH")
    except:
        pass
    
    run_ultra_fast_processor()