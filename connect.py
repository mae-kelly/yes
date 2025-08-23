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
from datetime import datetime, timedelta
import gc
import mmap
import psutil
import platform

# Disable all logging for maximum speed
logging.disable(logging.CRITICAL)

class LightningFastCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb_lightning.db"):
        print("\n🚀 LIGHTNING FAST CMDB PROCESSOR - SINGLE THREAD MAXIMUM SPEED")
        print("=" * 90)
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Set process priority to maximum
        self._set_max_priority()
        
        # Ultra-aggressive batch sizes
        self.query_batch_size = 200000  # Massive query batches
        self.insert_batch_size = 50000  # Huge insert batches
        self.progress_interval = 100000  # Less frequent progress updates
        
        print(f"⚡ Query batch: {self.query_batch_size:,}")
        print(f"🔥 Insert batch: {self.insert_batch_size:,}")
        
        # Pre-compiled regex for ultra-fast hostname cleaning
        self.hostname_cleaner = re.compile(r'[^a-z0-9]')
        self.invalid_values = {'', '*undefined', 'null', 'none', 'undefined'}
        
        # Lightning-fast column mapping (exact matches only)
        self.speed_column_map = {
            'hostname': 'hostname', 'host': 'hostname', 'fqdn': 'fqdn',
            'domain': 'domain', 'region': 'region', 'country': 'country', 
            'business_unit': 'business_unit', 'bu': 'business_unit',
            'infrastructure_type': 'infrastructure_type', 'infra_type': 'infrastructure_type',
            'data_center': 'data_center', 'datacenter': 'data_center',
            'ip_address': 'ip_address', 'ip': 'ip_address',
            'class': 'class', 'system_classification': 'system_classification',
            'apm': 'apm', 'cio': 'cio', 'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage', 'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk', 'logging_in_gso': 'logging_in_gso',
            'cloud_region': 'cloud_region'
        }
        
        # Ultra-fast duplicate tracking
        self.seen_hosts = set()
        
        # Lightning stats
        self.stats = {
            'start_time': time.time(),
            'last_update': time.time(),
            'tables_processed': 0,
            'total_tables': 0,
            'records_processed': 0,
            'hosts_created': 0,
            'duplicates_skipped': 0,
            'current_table': ''
        }
        
        # Initialize connections
        self._init_bigquery_lightning()
        self._init_duckdb_lightning()
        
        print("✅ LIGHTNING PROCESSOR READY - MAXIMUM SPEED ENGAGED")
        print("=" * 90)
    
    def _set_max_priority(self):
        """Set process to maximum priority"""
        try:
            current_process = psutil.Process()
            if platform.system() == "Windows":
                current_process.nice(psutil.HIGH_PRIORITY_CLASS)
            else:
                current_process.nice(-20)  # Maximum priority on Unix
            print("🔥 Process priority: MAXIMUM")
        except Exception as e:
            print(f"⚠️  Priority warning: {e}")
    
    def _init_bigquery_lightning(self):
        """Lightning-fast BigQuery setup"""
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        try:
            if os.path.exists(service_account_file):
                credentials = service_account.Credentials.from_service_account_file(service_account_file)
                self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
                print("⚡ BigQuery: Service Account Connected")
            else:
                self.bq_client = bigquery.Client(project="chronicle-fisv")
                print("⚡ BigQuery: Default Credentials Connected")
        except Exception as e:
            print(f"❌ BigQuery connection failed: {e}")
            raise
    
    def _init_duckdb_lightning(self):
        """Lightning-fast DuckDB with EXTREME performance settings"""
        # Remove existing database for fresh start
        if os.path.exists(self.duckdb_path):
            os.remove(self.duckdb_path)
        
        self.duck_conn = duckdb.connect(self.duckdb_path)
        
        # EXTREME PERFORMANCE SETTINGS - MAXIMUM SPEED
        extreme_settings = [
            "SET memory_limit='90%'",  # Use 90% of RAM
            f"SET threads TO {psutil.cpu_count()}",
            "SET max_memory='100GB'",
            "SET enable_progress_bar=false",
            "SET enable_profiling=false", 
            "SET checkpoint_threshold='5GB'",
            "SET wal_autocheckpoint=100000",
            "PRAGMA journal_mode=OFF",      # NO JOURNAL - MAXIMUM SPEED
            "PRAGMA synchronous=OFF",       # NO SYNC - MAXIMUM SPEED  
            "PRAGMA cache_size=5000000",    # 5M pages cache
            "PRAGMA temp_store=MEMORY",
            "PRAGMA mmap_size=5000000000",  # 5GB memory map
            "PRAGMA page_size=65536",       # Large pages
            "PRAGMA auto_vacuum=NONE"       # No auto vacuum
        ]
        
        for setting in extreme_settings:
            try:
                self.duck_conn.execute(setting)
            except Exception as e:
                print(f"⚠️  Setting warning: {setting} - {e}")
        
        # Create ultra-minimal table structure for speed
        create_sql = """
        CREATE TABLE universal_cmdb (
            normalized_host TEXT NOT NULL,
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
            source_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self.duck_conn.execute(create_sql)
        
        print("⚡ DuckDB: EXTREME SPEED MODE ACTIVATED")
        print("   - Journal: OFF (DANGEROUS BUT FAST)")  
        print("   - Sync: OFF (MAXIMUM SPEED)")
        print("   - Cache: 5M pages")
        print("   - Memory Map: 5GB")
    
    def normalize_hostname_lightning(self, hostname: str) -> str:
        """Lightning-fast hostname normalization"""
        if not hostname:
            return ""
        
        # Ultra-fast string processing
        h = str(hostname).lower().strip()
        
        if len(h) < 2 or h in self.invalid_values:
            return ""
        
        # Lightning-fast FQDN extraction
        if '.' in h:
            h = h.split('.', 1)[0]
        
        # Single regex operation
        h = self.hostname_cleaner.sub('', h)
        
        return h if len(h) > 1 else ""
    
    def load_metadata_lightning(self) -> Dict:
        """Lightning-fast metadata loading with memory mapping"""
        print("📂 Loading metadata with memory mapping...")
        start = time.time()
        
        try:
            # Memory map the entire file for maximum speed
            with open(self.json_file_path, 'rb') as f:
                file_size = os.path.getsize(self.json_file_path)
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    metadata = json.loads(mm.read().decode('utf-8'))
            
            load_time = time.time() - start
            table_count = len(metadata.get('columns', {}))
            
            print(f"✅ {table_count:,} tables loaded in {load_time:.2f}s ({file_size/1024/1024:.1f} MB)")
            return metadata
            
        except Exception as e:
            print(f"❌ Metadata loading failed: {e}")
            raise
    
    def discover_columns_lightning(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        """Lightning-fast column discovery"""
        print("🔍 Lightning column discovery...")
        start = time.time()
        
        discovered = []
        
        if 'columns' not in metadata:
            return []
        
        # Ultra-fast direct matching only
        for table_name, columns in metadata['columns'].items():
            for col_name in columns:
                col_lower = col_name.lower()
                
                # Direct hash lookup for maximum speed
                if col_lower in self.speed_column_map:
                    mapped_type = self.speed_column_map[col_lower]
                    discovered.append((table_name, col_name, mapped_type))
                # Quick hostname patterns
                elif any(pattern in col_lower for pattern in ['host', 'fqdn', 'server', 'node']):
                    discovered.append((table_name, col_name, 'hostname'))
        
        discovery_time = time.time() - start
        print(f"✅ {len(discovered):,} columns discovered in {discovery_time:.2f}s")
        
        return discovered
    
    def build_lightning_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        """Build ultra-optimized query"""
        # Only select what we absolutely need
        column_selects = [f"`{col}`" for col in columns[:15]]  # Limit columns for speed
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND LENGTH(TRIM(`{hostname_col}`)) > 1
        AND `{hostname_col}` NOT IN ('*Undefined', '', 'NULL', 'null')
        """
    
    def process_table_lightning(self, table_name: str, table_columns: List[Tuple[str, str, str]], 
                              table_index: int, total_tables: int) -> int:
        """Process table at lightning speed"""
        
        self.stats['current_table'] = table_name
        self.stats['tables_processed'] = table_index
        
        # Quick filter for hostname columns
        hostname_cols = [col for col, ctype in [(col, ctype) for _, col, ctype in table_columns] if ctype == 'hostname']
        if not hostname_cols:
            return 0
        
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        primary_hostname_col = hostname_cols[0]
        
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols[:10]]  # Limit for speed
        attribute_types = [ctype for _, ctype in attribute_cols[:10]]
        
        query = self.build_lightning_query(table_name, all_columns, primary_hostname_col)
        
        try:
            # Ultra-aggressive BigQuery job config
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                use_legacy_sql=False,
                maximum_bytes_billed=500 * 1024 * 1024 * 1024,  # 500GB limit
                job_timeout_ms=20 * 60 * 1000,  # 20 minutes
                dry_run=False
            )
            
            # Execute query
            query_start = time.time()
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result(page_size=self.query_batch_size)
            query_time = time.time() - query_start
            
            # Process results at lightning speed
            records_processed = self._process_results_lightning(
                results, table_name, primary_hostname_col, attribute_types, table_index, total_tables
            )
            
            return records_processed
            
        except Exception as e:
            print(f"❌ {os.path.basename(table_name)}: {str(e)[:60]}...")
            return 0
    
    def _process_results_lightning(self, results, table_name: str, hostname_col: str, 
                                 attribute_types: List[str], table_index: int, total_tables: int) -> int:
        """Lightning-fast result processing"""
        
        records_processed = 0
        batch_data = []
        local_duplicates = 0
        
        process_start = time.time()
        
        # Process all rows at maximum speed
        for row in results:
            records_processed += 1
            
            # Lightning-fast validation
            if not row[0]:
                continue
                
            normalized_host = self.normalize_hostname_lightning(row[0])
            if not normalized_host:
                continue
            
            # Ultra-fast duplicate check
            if normalized_host in self.seen_hosts:
                local_duplicates += 1
                continue
            
            self.seen_hosts.add(normalized_host)
            
            # Build record at lightning speed
            record = [
                normalized_host,
                table_name,
                str(row[0]).strip()
            ]
            
            # Add attributes (up to 10 for speed)
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and row[i]:
                    record.append(str(row[i]).strip())
                else:
                    record.append(None)
            
            # Pad to match table structure
            while len(record) < 23:  # Total columns in table
                record.append(None)
            
            batch_data.append(record)
            
            # Lightning-fast bulk insert
            if len(batch_data) >= self.insert_batch_size:
                self._lightning_bulk_insert(batch_data)
                batch_data.clear()
                
                # Update stats and show progress
                self.stats['records_processed'] += records_processed
                self.stats['duplicates_skipped'] += local_duplicates
                self._show_lightning_progress(table_index, total_tables)
                
                records_processed = 0
                local_duplicates = 0
        
        # Insert remaining data
        if batch_data:
            self._lightning_bulk_insert(batch_data)
            self.stats['records_processed'] += records_processed
            self.stats['duplicates_skipped'] += local_duplicates
        
        process_time = time.time() - process_start
        rate = records_processed / process_time if process_time > 0 else 0
        
        return records_processed
    
    def _lightning_bulk_insert(self, batch_data: List[List]) -> None:
        """Ultra-fast bulk insert"""
        if not batch_data:
            return
        
        # Prepare column list
        columns = [
            'normalized_host', 'source_tables', 'hostname', 'fqdn', 'domain',
            'infrastructure_type', 'region', 'country', 'data_center', 'cloud_region',
            'ip_address', 'class', 'system_classification', 'business_unit', 'apm',
            'cio', 'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage',
            'logging_in_splunk', 'logging_in_gso', 'source_count', 'created_at'
        ]
        
        # Lightning-fast bulk insert using prepared statements
        placeholders = ', '.join(['?' for _ in columns])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            # Use transaction for maximum speed
            self.duck_conn.execute("BEGIN")
            self.duck_conn.executemany(insert_sql, batch_data)
            self.duck_conn.execute("COMMIT")
            
            self.stats['hosts_created'] += len(batch_data)
            
        except Exception as e:
            self.duck_conn.execute("ROLLBACK")
            print(f"⚠️  Bulk insert error: {str(e)[:40]}...")
    
    def _show_lightning_progress(self, table_index: int, total_tables: int):
        """Show lightning-fast progress updates"""
        current_time = time.time()
        
        # Only update every few seconds for speed
        if current_time - self.stats['last_update'] < 3.0:
            return
        
        self.stats['last_update'] = current_time
        
        elapsed = current_time - self.stats['start_time']
        progress_pct = (table_index / total_tables) * 100 if total_tables > 0 else 0
        
        records_rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
        hosts_rate = self.stats['hosts_created'] / elapsed if elapsed > 0 else 0
        
        # ETA calculation
        if progress_pct > 0:
            eta_seconds = (elapsed * (100 - progress_pct)) / progress_pct
            eta_str = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta_str = "calculating..."
        
        print(f"⚡ {table_index}/{total_tables} ({progress_pct:.1f}%) | "
              f"{self.stats['records_processed']:,} recs | {self.stats['hosts_created']:,} hosts | "
              f"{records_rate:.0f} r/s | {hosts_rate:.0f} h/s | ETA: {eta_str}")
        print(f"   📂 {os.path.basename(self.stats['current_table'])}")
    
    def process_all_lightning(self):
        """Main lightning-fast processing"""
        print("\n⚡ STARTING LIGHTNING-FAST PROCESSING")
        print("=" * 80)
        
        # Load and discover at maximum speed
        metadata = self.load_metadata_lightning()
        discovered_columns = self.discover_columns_lightning(metadata)
        
        if not discovered_columns:
            print("❌ No processable columns found!")
            return
        
        # Group columns by table
        columns_by_table = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((table_name, column_name, column_type))
        
        self.stats['total_tables'] = len(columns_by_table)
        
        print(f"🎯 Processing {len(columns_by_table):,} tables at LIGHTNING SPEED")
        print(f"⚡ Single-threaded maximum optimization")
        print("=" * 80)
        
        # Process each table sequentially but at maximum speed
        processing_start = time.time()
        
        for table_index, (table_name, table_columns) in enumerate(columns_by_table.items(), 1):
            
            table_start = time.time()
            records_processed = self.process_table_lightning(
                table_name, table_columns, table_index, len(columns_by_table)
            )
            table_time = time.time() - table_start
            
            if records_processed > 0:
                table_rate = records_processed / table_time if table_time > 0 else 0
                print(f"   ✅ {records_processed:,} records in {table_time:.2f}s ({table_rate:.0f}/sec)")
        
        # Create essential indexes for final performance
        print("\n🔧 Creating essential indexes...")
        index_start = time.time()
        
        try:
            self.duck_conn.execute("CREATE INDEX idx_host ON universal_cmdb(normalized_host)")
            print("   ✅ Host index created")
        except Exception as e:
            print(f"   ⚠️  Index warning: {e}")
        
        index_time = time.time() - index_start
        
        self._generate_lightning_summary(processing_start)
    
    def _generate_lightning_summary(self, start_time: float):
        """Generate lightning-fast final summary"""
        total_time = time.time() - start_time
        
        print("\n" + "=" * 90)
        print("🏆 LIGHTNING-FAST PROCESSING COMPLETE!")
        print("=" * 90)
        
        try:
            # Get final counts
            total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
            
            # Quick quality metrics
            with_business_unit = self.duck_conn.execute(
                "SELECT COUNT(*) FROM universal_cmdb WHERE business_unit IS NOT NULL"
            ).fetchone()[0]
            
            with_region = self.duck_conn.execute(
                "SELECT COUNT(*) FROM universal_cmdb WHERE region IS NOT NULL"
            ).fetchone()[0]
            
        except Exception as e:
            print(f"Summary query error: {e}")
            total_hosts = self.stats['hosts_created']
            with_business_unit = 0
            with_region = 0
        
        # Performance metrics
        records_per_sec = self.stats['records_processed'] / total_time if total_time > 0 else 0
        hosts_per_sec = total_hosts / total_time if total_time > 0 else 0
        
        print(f"⏱️  Total Time: {timedelta(seconds=int(total_time))}")
        print(f"📊 Raw Records: {self.stats['records_processed']:,}")
        print(f"🎯 Unique Hosts: {total_hosts:,}")
        print(f"🚀 Duplicates: {self.stats['duplicates_skipped']:,}")
        print(f"⚡ Speed: {records_per_sec:.0f} records/sec | {hosts_per_sec:.0f} hosts/sec")
        
        # Quality metrics
        if total_hosts > 0:
            bu_pct = (with_business_unit / total_hosts) * 100
            region_pct = (with_region / total_hosts) * 100
            print(f"📈 Business Units: {with_business_unit:,} ({bu_pct:.1f}%)")
            print(f"🌍 Regions: {with_region:,} ({region_pct:.1f}%)")
        
        # Success message
        if total_time < 600:  # Under 10 minutes
            print(f"🎉 INCREDIBLE SPEED - Done in {total_time/60:.1f} minutes!")
        elif total_time < 1800:  # Under 30 minutes  
            print(f"🔥 EXCELLENT TIME - Done in {total_time/60:.1f} minutes!")
        else:
            print(f"✅ Completed in {total_time/60:.1f} minutes")
        
        print("=" * 90)
    
    def export_lightning(self, filename: str = "universal_cmdb_lightning.csv"):
        """Lightning-fast export"""
        print(f"\n📤 Lightning export to {filename}...")
        
        start_time = time.time()
        
        try:
            # Ultra-fast CSV export
            export_sql = f"""
            COPY (
                SELECT * FROM universal_cmdb 
                ORDER BY source_count DESC, normalized_host
            ) TO '{filename}' WITH (FORMAT CSV, HEADER TRUE)
            """
            
            self.duck_conn.execute(export_sql)
            
            export_time = time.time() - start_time
            file_size = os.path.getsize(filename) / (1024 * 1024)  # MB
            export_rate = file_size / export_time if export_time > 0 else 0
            
            print(f"✅ Exported {file_size:.1f} MB in {export_time:.2f}s ({export_rate:.1f} MB/s)")
            
        except Exception as e:
            print(f"❌ Export error: {e}")
    
    def cleanup(self):
        """Lightning cleanup"""
        try:
            if hasattr(self, 'duck_conn'):
                self.duck_conn.close()
            gc.collect()
            print("🧹 Lightning cleanup complete")
        except:
            pass

def main():
    """Run the lightning-fast processor"""
    processor = None
    
    print("🚀 LIGHTNING FAST CMDB PROCESSOR")
    print("⚠️  WARNING: Using EXTREME speed settings - database safety OFF!")
    print("=" * 80)
    
    try:
        processor = LightningFastCMDBProcessor(
            "reviewed_labeled_columns.json", 
            "universal_cmdb_lightning.db"
        )
        
        processor.process_all_lightning()
        processor.export_lightning("universal_cmdb_lightning.csv")
        
        print("\n🎉 LIGHTNING PROCESSING SUCCESS!")
        
    except KeyboardInterrupt:
        print("\n⚠️  PROCESSING INTERRUPTED BY USER")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.cleanup()

if __name__ == "__main__":
    main()