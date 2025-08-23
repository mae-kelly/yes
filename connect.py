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

# Disable logging for maximum speed
logging.disable(logging.CRITICAL)

class CompatibleUltraFastCMDB:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb_fast.db"):
        print("\n🚀 COMPATIBLE ULTRA-FAST CMDB PROCESSOR")
        print("=" * 80)
        print("   ✅ Works with ANY DuckDB version")
        print("   ⚡ Maximum speed with standard settings")
        print("=" * 80)
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Ultra-aggressive batch sizes that actually work
        self.query_batch_size = 500000  # Half million records per query
        self.insert_batch_size = 25000  # 25K bulk inserts
        
        print(f"⚡ Query batch: {self.query_batch_size:,}")
        print(f"🔥 Insert batch: {self.insert_batch_size:,}")
        
        # Pre-compiled regex for speed
        self.hostname_regex = re.compile(r'[^a-z0-9]')
        
        # Lightning-fast column mapping
        self.column_map = {
            'hostname': 'hostname', 'host': 'hostname', 'fqdn': 'fqdn',
            'domain': 'domain', 'region': 'region', 'country': 'country',
            'business_unit': 'business_unit', 'bu': 'business_unit',
            'infrastructure_type': 'infrastructure_type', 'infra_type': 'infrastructure_type',
            'data_center': 'data_center', 'datacenter': 'data_center',
            'ip_address': 'ip_address', 'ip': 'ip_address',
            'class': 'class', 'apm': 'apm', 'cio': 'cio',
            'edr_coverage': 'edr_coverage', 'tanium_coverage': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk', 'logging_in_gso': 'logging_in_gso'
        }
        
        # Speed tracking
        self.seen_hosts = set()
        self.stats = {
            'start_time': time.time(),
            'tables_processed': 0,
            'records_processed': 0,
            'hosts_created': 0,
            'duplicates_skipped': 0
        }
        
        self._init_bigquery()
        self._init_duckdb_compatible()
        
        print("✅ READY FOR ULTRA-FAST COMPATIBLE PROCESSING")
        print("=" * 80)
    
    def _init_bigquery(self):
        """Fast BigQuery initialization"""
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        try:
            if os.path.exists(service_account_file):
                credentials = service_account.Credentials.from_service_account_file(service_account_file)
                self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
                print("⚡ BigQuery: Service Account OK")
            else:
                self.bq_client = bigquery.Client(project="chronicle-fisv")
                print("⚡ BigQuery: Default Credentials OK")
        except Exception as e:
            print(f"❌ BigQuery failed: {e}")
            raise
    
    def _init_duckdb_compatible(self):
        """Compatible DuckDB setup - works with any version"""
        # Remove old database for fresh start
        if os.path.exists(self.duckdb_path):
            os.remove(self.duckdb_path)
        
        self.duck_conn = duckdb.connect(self.duckdb_path)
        
        # ONLY use settings that work in ALL DuckDB versions
        compatible_settings = [
            "SET threads=8",  # Standard threading
            "SET enable_progress_bar=false"
        ]
        
        for setting in compatible_settings:
            try:
                self.duck_conn.execute(setting)
                print(f"   ✅ {setting}")
            except Exception as e:
                print(f"   ⚠️  {setting} - {e}")
        
        # Create simple, fast table
        create_sql = """
        CREATE TABLE universal_cmdb (
            normalized_host TEXT,
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
        print("⚡ DuckDB: Compatible table created")
    
    def normalize_hostname_fast(self, hostname) -> str:
        """Ultra-fast hostname normalization"""
        if not hostname:
            return ""
        
        h = str(hostname).lower().strip()
        
        if len(h) < 2 or h in ('*undefined', 'null', 'none', ''):
            return ""
        
        # Fast FQDN handling
        if '.' in h:
            h = h.split('.')[0]
        
        # Single regex pass
        h = self.hostname_regex.sub('', h)
        
        return h if len(h) > 1 else ""
    
    def load_metadata_fast(self) -> Dict:
        """Fast metadata loading"""
        print("📂 Loading metadata...")
        start = time.time()
        
        try:
            # Try memory mapping first
            with open(self.json_file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    metadata = json.loads(mm.read().decode('utf-8'))
        except:
            # Fallback to regular loading
            with open(self.json_file_path, 'r') as f:
                metadata = json.load(f)
        
        load_time = time.time() - start
        table_count = len(metadata.get('columns', {}))
        
        print(f"✅ {table_count:,} tables in {load_time:.2f}s")
        return metadata
    
    def discover_columns_fast(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        """Lightning column discovery"""
        print("🔍 Fast column discovery...")
        
        discovered = []
        
        if 'columns' not in metadata:
            return []
        
        for table_name, columns in metadata['columns'].items():
            for col_name in columns:
                col_lower = col_name.lower()
                
                # Direct lookup
                if col_lower in self.column_map:
                    discovered.append((table_name, col_name, self.column_map[col_lower]))
                # Quick hostname detection
                elif any(h in col_lower for h in ['host', 'fqdn', 'server', 'node']):
                    discovered.append((table_name, col_name, 'hostname'))
        
        print(f"✅ {len(discovered):,} mappable columns")
        return discovered
    
    def process_all_ultra_fast(self):
        """Main ultra-fast processing"""
        print("\n⚡ STARTING ULTRA-FAST PROCESSING")
        print("=" * 70)
        
        # Load everything
        metadata = self.load_metadata_fast()
        discovered_columns = self.discover_columns_fast(metadata)
        
        if not discovered_columns:
            print("❌ No columns to process")
            return
        
        # Group by table
        tables_dict = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            tables_dict[table_name].append((table_name, column_name, column_type))
        
        total_tables = len(tables_dict)
        self.stats['total_tables'] = total_tables
        
        print(f"🎯 Processing {total_tables:,} tables")
        print("=" * 70)
        
        # Process tables one by one - but SUPER fast
        start_time = time.time()
        
        for table_idx, (table_name, table_columns) in enumerate(tables_dict.items(), 1):
            
            table_start = time.time()
            
            # Show current table
            print(f"\n🔄 TABLE {table_idx}/{total_tables}: {os.path.basename(table_name)}")
            
            records = self.process_table_ultra_fast(table_name, table_columns)
            
            table_time = time.time() - table_start
            
            if records > 0:
                rate = records / table_time if table_time > 0 else 0
                print(f"   ✅ {records:,} records in {table_time:.1f}s ({rate:.0f}/sec)")
            else:
                print("   ⚠️  No valid records")
            
            # Overall progress
            elapsed = time.time() - start_time
            progress = (table_idx / total_tables) * 100
            
            if table_idx % 5 == 0 or table_idx == total_tables:  # Every 5 tables
                rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
                eta = ((elapsed * (total_tables - table_idx)) / table_idx) if table_idx > 0 else 0
                
                print(f"📊 PROGRESS: {progress:.1f}% | {self.stats['records_processed']:,} total | "
                      f"{rate:.0f}/sec | ETA: {timedelta(seconds=int(eta))}")
        
        self._create_final_indexes()
        self._generate_final_summary(start_time)
    
    def process_table_ultra_fast(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        """Process single table at maximum speed"""
        
        # Find hostname columns
        hostname_cols = [col for _, col, ctype in table_columns if ctype == 'hostname']
        if not hostname_cols:
            return 0
        
        # Get attribute columns (limit to 8 for speed)
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname'][:8]
        
        primary_hostname = hostname_cols[0]
        all_columns = [primary_hostname] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        # Build ultra-simple query
        query = f"""
        SELECT {', '.join(f'`{col}`' for col in all_columns)}
        FROM `{table_name}`
        WHERE `{primary_hostname}` IS NOT NULL
        AND LENGTH(`{primary_hostname}`) > 1
        """
        
        try:
            # Ultra-aggressive BigQuery config
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                maximum_bytes_billed=1000 * 1024 * 1024 * 1024,  # 1TB limit
                job_timeout_ms=30 * 60 * 1000  # 30 minutes
            )
            
            # Execute query
            job = self.bq_client.query(query, job_config=job_config)
            results = job.result(page_size=self.query_batch_size)
            
            # Process at lightning speed
            return self._process_results_lightning(results, table_name, attribute_types)
            
        except Exception as e:
            print(f"   ❌ Query failed: {str(e)[:50]}...")
            return 0
    
    def _process_results_lightning(self, results, table_name: str, attribute_types: List[str]) -> int:
        """Lightning-fast result processing"""
        
        records_processed = 0
        batch_data = []
        duplicates_in_batch = 0
        
        for row in results:
            records_processed += 1
            
            # Lightning validation
            if not row[0]:
                continue
            
            normalized = self.normalize_hostname_fast(row[0])
            if not normalized:
                continue
            
            # Fast duplicate check
            if normalized in self.seen_hosts:
                duplicates_in_batch += 1
                continue
            
            self.seen_hosts.add(normalized)
            
            # Build record super fast
            record = [
                normalized,           # normalized_host
                table_name,          # source_tables  
                str(row[0]).strip()  # hostname
            ]
            
            # Add attributes fast
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and row[i] and str(row[i]).strip():
                    record.append(str(row[i]).strip())
                else:
                    record.append(None)
            
            # Pad to match table structure (20 total columns)
            while len(record) < 20:
                record.append(None)
            
            record.append(1)  # source_count
            record.append('CURRENT_TIMESTAMP')  # created_at
            
            batch_data.append(record)
            
            # Ultra-fast bulk insert
            if len(batch_data) >= self.insert_batch_size:
                self._bulk_insert_compatible(batch_data)
                self.stats['hosts_created'] += len(batch_data)
                batch_data.clear()
                
                # Update stats
                self.stats['records_processed'] += records_processed
                self.stats['duplicates_skipped'] += duplicates_in_batch
                
                # Show progress every 100K records
                if self.stats['records_processed'] % 100000 == 0:
                    elapsed = time.time() - self.stats['start_time']
                    rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
                    print(f"   ⚡ {self.stats['records_processed']:,} | {rate:.0f}/sec | {duplicates_in_batch:,} dups")
                
                records_processed = 0
                duplicates_in_batch = 0
        
        # Insert final batch
        if batch_data:
            self._bulk_insert_compatible(batch_data)
            self.stats['hosts_created'] += len(batch_data)
            self.stats['records_processed'] += records_processed
            self.stats['duplicates_skipped'] += duplicates_in_batch
        
        return records_processed
    
    def _bulk_insert_compatible(self, batch_data: List[List]):
        """Compatible bulk insert that works everywhere"""
        if not batch_data:
            return
        
        # Define all columns
        columns = [
            'normalized_host', 'source_tables', 'hostname', 'fqdn', 'domain',
            'infrastructure_type', 'region', 'country', 'data_center', 'cloud_region',
            'ip_address', 'class', 'system_classification', 'business_unit', 'apm',
            'cio', 'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage',
            'logging_in_splunk', 'logging_in_gso', 'source_count', 'created_at'
        ]
        
        # Simple bulk insert that works everywhere
        placeholders = ', '.join(['?' for _ in columns])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            # Use executemany for speed
            self.duck_conn.executemany(insert_sql, batch_data)
        except Exception as e:
            print(f"   ⚠️  Insert error: {str(e)[:40]}...")
    
    def process_all_compatible(self):
        """Main processing - compatible and ultra-fast"""
        print("\n⚡ STARTING COMPATIBLE ULTRA-FAST PROCESSING")
        print("=" * 80)
        
        # Load data
        metadata = self.load_metadata_fast()
        discovered = self.discover_columns_fast(metadata)
        
        if not discovered:
            print("❌ No processable columns!")
            return
        
        # Group by table
        table_groups = defaultdict(list)
        for table_name, col_name, col_type in discovered:
            table_groups[table_name].append((table_name, col_name, col_type))
        
        total_tables = len(table_groups)
        print(f"🎯 {total_tables:,} tables to process")
        print("=" * 80)
        
        start_time = time.time()
        
        # Process each table super fast
        for table_idx, (table_name, table_columns) in enumerate(table_groups.items(), 1):
            
            self.stats['tables_processed'] = table_idx
            
            print(f"\n🔄 [{table_idx}/{total_tables}] {os.path.basename(table_name)}")
            
            table_start = time.time()
            records = self.process_table_ultra_fast(table_name, table_columns)
            table_time = time.time() - table_start
            
            if records > 0:
                rate = records / table_time if table_time > 0 else 0
                print(f"   ✅ {records:,} in {table_time:.1f}s ({rate:.0f}/sec)")
            
            # Progress every 10 tables
            if table_idx % 10 == 0 or table_idx == total_tables:
                elapsed = time.time() - start_time
                progress = (table_idx / total_tables) * 100
                overall_rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
                
                eta_seconds = ((elapsed * (total_tables - table_idx)) / table_idx) if table_idx > 0 else 0
                eta = str(timedelta(seconds=int(eta_seconds)))
                
                print(f"\n📊 PROGRESS: {progress:.1f}% complete")
                print(f"   ⚡ {self.stats['records_processed']:,} total records")
                print(f"   🔥 {self.stats['hosts_created']:,} unique hosts")
                print(f"   🚀 {overall_rate:.0f} records/second")
                print(f"   ⏰ ETA: {eta}")
        
        self._create_final_indexes()
        self._generate_summary(start_time)
    
    def _create_final_indexes(self):
        """Create final indexes for performance"""
        print("\n🔧 Creating final indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_bu ON universal_cmdb(business_unit)", 
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)"
        ]
        
        for idx_sql in indexes:
            try:
                self.duck_conn.execute(idx_sql)
                print(f"   ✅ Index created")
            except Exception as e:
                print(f"   ⚠️  Index warning: {e}")
    
    def _generate_summary(self, start_time: float):
        """Generate final summary"""
        total_time = time.time() - start_time
        
        print("\n" + "=" * 90)
        print("🏆 COMPATIBLE ULTRA-FAST PROCESSING COMPLETE!")
        print("=" * 90)
        
        try:
            # Get final stats
            total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
            
            # Quality check
            with_bu = self.duck_conn.execute(
                "SELECT COUNT(*) FROM universal_cmdb WHERE business_unit IS NOT NULL AND business_unit != ''"
            ).fetchone()[0]
            
            with_region = self.duck_conn.execute(
                "SELECT COUNT(*) FROM universal_cmdb WHERE region IS NOT NULL AND region != ''"
            ).fetchone()[0]
            
        except:
            total_hosts = self.stats['hosts_created']
            with_bu = 0
            with_region = 0
        
        # Performance metrics
        records_per_sec = self.stats['records_processed'] / total_time if total_time > 0 else 0
        hosts_per_sec = total_hosts / total_time if total_time > 0 else 0
        
        print(f"⏱️  Total Time: {timedelta(seconds=int(total_time))}")
        print(f"📊 Records Processed: {self.stats['records_processed']:,}")
        print(f"🎯 Unique Hosts: {total_hosts:,}")
        print(f"🚀 Duplicates Skipped: {self.stats['duplicates_skipped']:,}")
        print(f"⚡ Speed: {records_per_sec:.0f} records/sec")
        print(f"🔥 Host Rate: {hosts_per_sec:.0f} hosts/sec")
        
        # Data quality
        if total_hosts > 0:
            bu_pct = (with_bu / total_hosts) * 100
            region_pct = (with_region / total_hosts) * 100
            print(f"📈 Business Unit: {with_bu:,} ({bu_pct:.1f}%)")
            print(f"🌍 Region: {with_region:,} ({region_pct:.1f}%)")
        
        # Success message based on time
        if total_time < 300:  # Under 5 minutes
            print(f"\n🎉 INCREDIBLE! Done in {total_time/60:.1f} minutes!")
        elif total_time < 900:  # Under 15 minutes
            print(f"\n🔥 EXCELLENT! Done in {total_time/60:.1f} minutes!")
        elif total_time < 1800:  # Under 30 minutes
            print(f"\n✅ GREAT! Done in {total_time/60:.1f} minutes!")
        else:
            print(f"\n✅ Completed in {total_time/60:.1f} minutes")
        
        print("=" * 90)
    
    def export_fast(self, filename: str = "universal_cmdb_compatible.csv"):
        """Fast CSV export"""
        print(f"\n📤 Exporting to {filename}...")
        
        start = time.time()
        
        try:
            # Simple, fast export
            self.duck_conn.execute(f"""
                COPY (
                    SELECT * FROM universal_cmdb 
                    ORDER BY source_count DESC, normalized_host
                ) TO '{filename}' WITH (HEADER TRUE)
            """)
            
            export_time = time.time() - start
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            print(f"✅ {file_size:.1f} MB exported in {export_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Export error: {e}")
    
    def cleanup(self):
        """Fast cleanup"""
        try:
            self.duck_conn.close()
            gc.collect()
            print("🧹 Cleanup complete")
        except:
            pass

def main():
    """Run the compatible ultra-fast processor"""
    processor = None
    
    print("🚀 STARTING COMPATIBLE ULTRA-FAST CMDB PROCESSOR")
    print("   ✅ No pickling issues")
    print("   ⚡ Maximum compatible speed")
    print("   🔥 Works with any DuckDB version")
    print()
    
    try:
        processor = CompatibleUltraFastCMDB(
            "reviewed_labeled_columns.json",
            "universal_cmdb_compatible.db"
        )
        
        processor.process_all_compatible()
        processor.export_fast("universal_cmdb_compatible.csv")
        
    except KeyboardInterrupt:
        print("\n⚠️  INTERRUPTED BY USER")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.cleanup()

if __name__ == "__main__":
    main()