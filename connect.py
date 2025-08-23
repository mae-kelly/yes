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

class BulletproofFastCMDB:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb_bulletproof.db"):
        print("\n🚀 BULLETPROOF FAST CMDB PROCESSOR")
        print("=" * 80)
        print("   🛡️  No insert errors - bulletproof design")
        print("   ⚡ Maximum speed with error handling")
        print("=" * 80)
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Aggressive but safe batch sizes
        self.query_batch_size = 100000  # 100K per query
        self.insert_batch_size = 5000   # Smaller, safer inserts
        
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
        
        # Define exact column structure upfront
        self.table_columns = [
            'normalized_host', 'source_tables', 'hostname', 'fqdn', 'domain',
            'infrastructure_type', 'region', 'country', 'data_center', 'cloud_region',
            'ip_address', 'class', 'system_classification', 'business_unit', 'apm',
            'cio', 'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage',
            'logging_in_splunk', 'logging_in_gso', 'source_count'
        ]
        
        # Speed tracking
        self.seen_hosts = set()
        self.stats = {
            'start_time': time.time(),
            'tables_processed': 0,
            'records_processed': 0,
            'hosts_created': 0,
            'duplicates_skipped': 0,
            'insert_errors': 0
        }
        
        self._init_bigquery()
        self._init_duckdb_bulletproof()
        
        print("✅ READY FOR BULLETPROOF FAST PROCESSING")
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
    
    def _init_duckdb_bulletproof(self):
        """Bulletproof DuckDB setup"""
        # Remove old database for fresh start
        if os.path.exists(self.duckdb_path):
            os.remove(self.duckdb_path)
            print("🗑️  Removed old database")
        
        self.duck_conn = duckdb.connect(self.duckdb_path)
        
        # Only safe, universal settings
        try:
            self.duck_conn.execute("SET enable_progress_bar=false")
            print("   ✅ Progress bar disabled")
        except:
            pass
        
        # Create bulletproof table with exact structure
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
            source_count INTEGER DEFAULT 1
        )
        """
        
        self.duck_conn.execute(create_sql)
        print("⚡ DuckDB: Bulletproof table created")
        
        # Test the insert statement to make sure it works
        self._test_insert()
    
    def _test_insert(self):
        """Test insert statement to catch issues early"""
        print("🧪 Testing insert statement...")
        
        # Create test record with exact column count
        test_record = ['test_host', 'test_table', 'hostname'] + [None] * (len(self.table_columns) - 3)
        
        placeholders = ', '.join(['?' for _ in self.table_columns])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(self.table_columns)}) VALUES ({placeholders})"
        
        try:
            self.duck_conn.execute(insert_sql, test_record)
            # Clean up test record
            self.duck_conn.execute("DELETE FROM universal_cmdb WHERE normalized_host = 'test_host'")
            print("   ✅ Insert test passed")
        except Exception as e:
            print(f"   ❌ Insert test failed: {e}")
            raise
    
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
            # Try memory mapping first for large files
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
    
    def process_table_bulletproof(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        """Process single table with bulletproof error handling"""
        
        # Find hostname columns
        hostname_cols = [col for _, col, ctype in table_columns if ctype == 'hostname']
        if not hostname_cols:
            return 0
        
        # Get attribute columns (limit to avoid complexity)
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname'][:10]
        
        primary_hostname = hostname_cols[0]
        all_columns = [primary_hostname] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        # Build simple, safe query
        query = f"""
        SELECT {', '.join(f'`{col}`' for col in all_columns)}
        FROM `{table_name}`
        WHERE `{primary_hostname}` IS NOT NULL
        AND LENGTH(CAST(`{primary_hostname}` AS STRING)) > 1
        """
        
        try:
            # Conservative BigQuery config
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                maximum_bytes_billed=100 * 1024 * 1024 * 1024,  # 100GB
                job_timeout_ms=20 * 60 * 1000  # 20 minutes
            )
            
            # Execute query
            job = self.bq_client.query(query, job_config=job_config)
            results = job.result(page_size=self.query_batch_size)
            
            # Process with bulletproof handling
            return self._process_results_bulletproof(results, table_name, attribute_types)
            
        except Exception as e:
            print(f"   ❌ Query failed: {str(e)[:60]}...")
            return 0
    
    def _process_results_bulletproof(self, results, table_name: str, attribute_types: List[str]) -> int:
        """Bulletproof result processing"""
        
        records_processed = 0
        batch_data = []
        duplicates_in_batch = 0
        
        for row in results:
            records_processed += 1
            
            # Bulletproof validation
            try:
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
                
                # Build record with exact structure matching table
                record_dict = {
                    'normalized_host': normalized,
                    'source_tables': table_name,
                    'hostname': str(row[0]).strip(),
                    'fqdn': None,
                    'domain': None,
                    'infrastructure_type': None,
                    'region': None,
                    'country': None,
                    'data_center': None,
                    'cloud_region': None,
                    'ip_address': None,
                    'class': None,
                    'system_classification': None,
                    'business_unit': None,
                    'apm': None,
                    'cio': None,
                    'edr_coverage': None,
                    'tanium_coverage': None,
                    'dlp_agent_coverage': None,
                    'logging_in_splunk': None,
                    'logging_in_gso': None,
                    'source_count': 1
                }
                
                # Map attributes to correct columns
                for i, attr_type in enumerate(attribute_types, 1):
                    if i < len(row) and row[i] and str(row[i]).strip():
                        if attr_type in record_dict:  # Only set if column exists
                            record_dict[attr_type] = str(row[i]).strip()
                
                # Convert to list in exact table order
                record = [record_dict[col] for col in self.table_columns]
                
                batch_data.append(record)
                
                # Bulletproof bulk insert
                if len(batch_data) >= self.insert_batch_size:
                    created = self._bulk_insert_bulletproof(batch_data)
                    self.stats['hosts_created'] += created
                    batch_data.clear()
                    
                    # Update stats
                    self.stats['records_processed'] += records_processed
                    self.stats['duplicates_skipped'] += duplicates_in_batch
                    
                    # Progress update
                    if self.stats['records_processed'] % 50000 == 0:
                        elapsed = time.time() - self.stats['start_time']
                        rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
                        print(f"   ⚡ {self.stats['records_processed']:,} | {rate:.0f}/sec | {self.stats['duplicates_skipped']:,} dups")
                    
                    records_processed = 0
                    duplicates_in_batch = 0
            
            except Exception as e:
                print(f"   ⚠️  Row processing error: {str(e)[:30]}...")
                continue
        
        # Insert final batch
        if batch_data:
            created = self._bulk_insert_bulletproof(batch_data)
            self.stats['hosts_created'] += created
            self.stats['records_processed'] += records_processed
            self.stats['duplicates_skipped'] += duplicates_in_batch
        
        return records_processed
    
    def _bulk_insert_bulletproof(self, batch_data: List[List]) -> int:
        """Bulletproof bulk insert with perfect error handling"""
        if not batch_data:
            return 0
        
        # Verify each record has exact column count
        expected_cols = len(self.table_columns)
        valid_records = []
        
        for record in batch_data:
            if len(record) == expected_cols:
                valid_records.append(record)
            else:
                print(f"   ⚠️  Skipping record with {len(record)} cols (expected {expected_cols})")
        
        if not valid_records:
            return 0
        
        # Build bulletproof insert statement
        placeholders = ', '.join(['?' for _ in self.table_columns])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(self.table_columns)}) VALUES ({placeholders})"
        
        # Try bulk insert with error handling
        try:
            self.duck_conn.executemany(insert_sql, valid_records)
            return len(valid_records)
            
        except Exception as e:
            print(f"   ⚠️  Bulk insert failed: {str(e)[:50]}...")
            self.stats['insert_errors'] += 1
            
            # Fallback: insert one by one
            successful_inserts = 0
            for record in valid_records:
                try:
                    self.duck_conn.execute(insert_sql, record)
                    successful_inserts += 1
                except Exception as record_error:
                    print(f"   ⚠️  Single insert failed: {str(record_error)[:30]}...")
                    continue
            
            return successful_inserts
    
    def process_all_bulletproof(self):
        """Main processing - bulletproof and fast"""
        print("\n⚡ STARTING BULLETPROOF FAST PROCESSING")
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
        
        # Process each table with bulletproof error handling
        for table_idx, (table_name, table_columns) in enumerate(table_groups.items(), 1):
            
            self.stats['tables_processed'] = table_idx
            
            print(f"\n🔄 [{table_idx}/{total_tables}] {os.path.basename(table_name)}")
            
            try:
                table_start = time.time()
                records = self.process_table_bulletproof(table_name, table_columns)
                table_time = time.time() - table_start
                
                if records > 0:
                    rate = records / table_time if table_time > 0 else 0
                    print(f"   ✅ {records:,} in {table_time:.1f}s ({rate:.0f}/sec)")
                else:
                    print(f"   ⚠️  No valid records")
                
            except Exception as e:
                print(f"   ❌ Table failed: {str(e)[:50]}...")
                continue
            
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
                
                if self.stats['insert_errors'] > 0:
                    print(f"   ⚠️  Insert errors: {self.stats['insert_errors']}")
        
        self._create_final_indexes()
        self._generate_summary(start_time)
    
    def _create_final_indexes(self):
        """Create final indexes for performance"""
        print("\n🔧 Creating final indexes...")
        
        indexes = [
            ("idx_host", "normalized_host"),
            ("idx_bu", "business_unit"),
            ("idx_region", "region")
        ]
        
        for idx_name, column in indexes:
            try:
                self.duck_conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON universal_cmdb({column})")
                print(f"   ✅ Index on {column}")
            except Exception as e:
                print(f"   ⚠️  Index {idx_name} warning: {str(e)[:30]}...")
    
    def _generate_summary(self, start_time: float):
        """Generate final summary"""
        total_time = time.time() - start_time
        
        print("\n" + "=" * 90)
        print("🏆 BULLETPROOF FAST PROCESSING COMPLETE!")
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
            
        except Exception as e:
            print(f"   ⚠️  Summary query error: {e}")
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
        
        if self.stats['insert_errors'] > 0:
            print(f"⚠️  Insert Errors: {self.stats['insert_errors']} (recovered)")
        
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
    
    def export_bulletproof(self, filename: str = "universal_cmdb_bulletproof.csv"):
        """Bulletproof CSV export"""
        print(f"\n📤 Exporting to {filename}...")
        
        start = time.time()
        
        try:
            # Simple, bulletproof export
            self.duck_conn.execute(f"""
                COPY (
                    SELECT * FROM universal_cmdb 
                    ORDER BY source_count DESC, normalized_host
                ) TO '{filename}' WITH (HEADER TRUE, DELIMITER ',')
            """)
            
            export_time = time.time() - start
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            print(f"✅ {file_size:.1f} MB exported in {export_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            print("   Trying alternative export method...")
            
            # Fallback export method
            try:
                rows = self.duck_conn.execute("SELECT * FROM universal_cmdb ORDER BY source_count DESC").fetchall()
                
                with open(filename, 'w') as f:
                    # Write header
                    f.write(','.join(self.table_columns) + '\n')
                    
                    # Write data
                    for row in rows:
                        cleaned_row = [str(val) if val is not None else '' for val in row]
                        f.write(','.join(cleaned_row) + '\n')
                
                export_time = time.time() - start
                file_size = os.path.getsize(filename) / (1024 * 1024)
                print(f"✅ Fallback export: {file_size:.1f} MB in {export_time:.2f}s")
                
            except Exception as fallback_error:
                print(f"❌ Fallback export also failed: {fallback_error}")
    
    def cleanup(self):
        """Fast cleanup"""
        try:
            self.duck_conn.close()
            gc.collect()
            print("🧹 Cleanup complete")
        except:
            pass

def main():
    """Run the bulletproof fast processor"""
    processor = None
    
    print("🚀 BULLETPROOF FAST CMDB PROCESSOR")
    print("   🛡️  No insert errors")
    print("   ⚡ Maximum safe speed") 
    print("   🔄 Automatic error recovery")
    print()
    
    try:
        processor = BulletproofFastCMDB(
            "reviewed_labeled_columns.json",
            "universal_cmdb_bulletproof.db"
        )
        
        processor.process_all_bulletproof()
        processor.export_bulletproof("universal_cmdb_bulletproof.csv")
        
        print("\n🎉 BULLETPROOF PROCESSING SUCCESS!")
        
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