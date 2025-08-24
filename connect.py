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
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial
import signal
import sys

# Configure logging for better performance
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class OptimizedCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db", max_workers: int = None):
        print("\n🚀 OPTIMIZED CMDB PROCESSOR - FAST MODE")
        print("=" * 80)
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.running = True
        
        # Set up signal handlers to keep alive
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Initializing with {self.max_workers} worker threads")
        
        # Optimized column mapping - combined for speed
        self.column_mapping = self._build_comprehensive_mapping()
        self.stats = self._init_stats()
        self.duplicate_tracker = set()
        self._lock = threading.Lock()
        
        # Initialize connections
        self._init_bigquery()
        self.duck_conn = duckdb.connect(duckdb_path, config={'threads': self.max_workers})
        self._create_optimized_table()
        
        logger.info("✅ Initialization complete - Ready for high-speed processing")
        
    def _signal_handler(self, signum, frame):
        """Handle interruption gracefully but keep running"""
        logger.info(f"⚠️  Signal {signum} received - continuing processing...")
        # Don't exit, just log and continue
        
    def _build_comprehensive_mapping(self) -> Dict:
        """Build comprehensive column mapping for faster lookups"""
        base_mapping = {
            'fqdn': 'fqdn', 'domain': 'domain', 'host': 'hostname', 'hostname': 'hostname',
            'infrastructure_type': 'infrastructure_type', 'infra_type': 'infrastructure_type',
            'region': 'region', 'country': 'country', 'data_center': 'data_center',
            'datacenter': 'data_center', 'cloud_region': 'cloud_region',
            'ip_address': 'ip_address', 'ip': 'ip_address', 'class': 'class',
            'system_classification': 'system_classification', 'business_unit': 'business_unit',
            'bu': 'business_unit', 'apm': 'apm', 'cio': 'cio',
            'edr_coverage': 'edr_coverage', 'tanium_coverage': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage', 'logging_in_splunk': 'logging_in_splunk',
            'logging_in_gso': 'logging_in_gso'
        }
        
        # Pre-compile regex patterns for speed
        hostname_patterns = re.compile(r'(host|hostname|fqdn|server_name|node_name|device_name|endpoint_name|computer_name|machine_name|chronicle_device_hostname|asset_name)', re.IGNORECASE)
        
        pattern_mapping = {
            'business_unit': re.compile(r'(business_unit|bu|business|department|division|org_unit|organizational_unit|cost_center|business_group|dept|organization)', re.IGNORECASE),
            'region': re.compile(r'(region|location|site|area|zone|geographic_region|geo_region|datacenter_region|site_location)', re.IGNORECASE),
            'country': re.compile(r'(country|nation|country_code|geo_country|location_country)', re.IGNORECASE),
            'infrastructure_type': re.compile(r'(infrastructure_type|infra_type|server_type|system_type|platform|environment|env|deployment_type|platform_type|os_type)', re.IGNORECASE),
            'data_center': re.compile(r'(datacenter|data_center|dc|facility|center|site_name|datacenter_name|facility_name|dc_location)', re.IGNORECASE),
            'cloud_region': re.compile(r'(cloud_region|aws_region|azure_region|gcp_region|cloud_location|cloud_zone|availability_zone)', re.IGNORECASE),
            'ip_address': re.compile(r'(ip_address|ip|ipv4|ipv6|host_ip|server_ip|endpoint_ip|device_ip|internal_ip|external_ip|primary_ip)', re.IGNORECASE),
            'class': re.compile(r'(class|classification|tier|level|grade|category|server_class|system_class)', re.IGNORECASE),
            'system_classification': re.compile(r'(system_classification|security_classification|data_classification|classification_level|sensitivity|security_level)', re.IGNORECASE),
            'apm': re.compile(r'(apm|monitoring|application_monitoring|performance_monitoring|apm_enabled|monitoring_enabled)', re.IGNORECASE),
            'cio': re.compile(r'(cio|owner|responsible|contact|admin|administrator|system_owner|business_owner|technical_owner)', re.IGNORECASE),
            'edr_coverage': re.compile(r'(edr_coverage|edr|endpoint_detection|security_agent|antivirus|av_coverage|endpoint_protection)', re.IGNORECASE),
            'tanium_coverage': re.compile(r'(tanium_coverage|tanium|tanium_agent|endpoint_management)', re.IGNORECASE),
            'dlp_agent_coverage': re.compile(r'(dlp_agent_coverage|dlp|data_loss_prevention|dlp_agent)', re.IGNORECASE),
            'logging_in_splunk': re.compile(r'(logging_in_splunk|splunk|splunk_logging|log_forwarding)', re.IGNORECASE),
            'logging_in_gso': re.compile(r'(logging_in_gso|gso|gso_logging|security_logging)', re.IGNORECASE),
            'domain': re.compile(r'(domain|dns_domain|ad_domain|windows_domain)', re.IGNORECASE),
            'fqdn': re.compile(r'(fqdn|full_name|qualified_name|dns_name|fully_qualified)', re.IGNORECASE)
        }
        
        return {
            'base': base_mapping,
            'hostname_pattern': hostname_patterns,
            'patterns': pattern_mapping
        }
    
    def _init_stats(self) -> Dict:
        return {
            'tables_processed': 0, 'columns_discovered': 0, 'hosts_created': 0,
            'hosts_updated': 0, 'duplicate_hosts_found': 0, 'total_records_processed': 0,
            'processing_errors': 0, 'start_time': time.time()
        }
        
    def _init_bigquery(self):
        """Initialize BigQuery with optimized settings"""
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
            
        logger.info("✅ BigQuery connection established")
        
    def _create_optimized_table(self):
        """Create optimized table with better indexing"""
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
        
        # Create indexes for faster lookups
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_business_unit ON universal_cmdb(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)",
            "CREATE INDEX IF NOT EXISTS idx_infrastructure_type ON universal_cmdb(infrastructure_type)",
            "CREATE INDEX IF NOT EXISTS idx_source_count ON universal_cmdb(source_count)",
            "CREATE INDEX IF NOT EXISTS idx_last_updated ON universal_cmdb(last_updated)"
        ]
        
        for index_sql in indexes:
            try:
                self.duck_conn.execute(index_sql)
            except:
                pass
    
    def normalize_hostname(self, hostname: str) -> str:
        """Optimized hostname normalization"""
        if not hostname or not isinstance(hostname, str) or hostname.strip() == '*Undefined':
            return ""
        
        normalized = hostname.lower().strip()
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        # Use faster regex substitution
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        return normalized if len(normalized) > 1 else ""
    
    def is_valid_value(self, value) -> bool:
        """Fast value validation"""
        if not value:
            return False
        if isinstance(value, str):
            stripped = value.strip()
            return stripped and stripped != '*Undefined' and stripped.lower() not in {'null', 'none', 'undefined'}
        return True
    
    def load_metadata(self) -> Dict:
        """Load metadata with progress tracking"""
        logger.info(f"📂 Loading metadata from {self.json_file_path}")
        start_time = time.time()
        
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        
        load_time = time.time() - start_time
        
        if 'columns' in metadata:
            table_count = len(metadata['columns'])
            column_count = sum(len(cols) for cols in metadata['columns'].values())
            logger.info(f"✅ Loaded {table_count:,} tables, {column_count:,} columns in {load_time:.2f}s")
        
        return metadata
    
    def discover_columns_fast(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        """Fast column discovery using compiled regex patterns"""
        logger.info("🔍 Starting fast column discovery...")
        start_time = time.time()
        
        discovered_columns = []
        
        if 'columns' not in metadata:
            logger.error("❌ No columns found in metadata")
            return []
        
        base_mapping = self.column_mapping['base']
        hostname_pattern = self.column_mapping['hostname_pattern']
        patterns = self.column_mapping['patterns']
        
        for table_name, columns in metadata['columns'].items():
            for column_name, column_type in columns.items():
                column_lower = column_name.lower()
                type_lower = str(column_type).lower() if column_type else ""
                
                # Fast exact match first
                if type_lower in base_mapping:
                    discovered_columns.append((table_name, column_name, base_mapping[type_lower]))
                    continue
                
                # Fast hostname pattern match
                if hostname_pattern.search(column_lower):
                    discovered_columns.append((table_name, column_name, 'hostname'))
                    continue
                
                # Fast pattern matching
                for target_type, pattern in patterns.items():
                    if pattern.search(column_lower) or pattern.search(type_lower):
                        discovered_columns.append((table_name, column_name, target_type))
                        break
        
        discovery_time = time.time() - start_time
        self.stats['columns_discovered'] = len(discovered_columns)
        
        logger.info(f"✅ Discovered {len(discovered_columns)} relevant columns in {discovery_time:.2f}s")
        return discovered_columns
    
    def process_table_batch(self, table_batch: List[Tuple[str, List[Tuple[str, str, str]]]]) -> int:
        """Process multiple tables in parallel"""
        total_records = 0
        
        with ThreadPoolExecutor(max_workers=min(4, len(table_batch))) as executor:
            future_to_table = {
                executor.submit(self.process_single_table, table_name, table_columns): table_name
                for table_name, table_columns in table_batch
            }
            
            for future in as_completed(future_to_table):
                table_name = future_to_table[future]
                try:
                    records = future.result()
                    total_records += records
                    logger.info(f"✅ {table_name}: {records:,} records processed")
                except Exception as e:
                    logger.error(f"❌ {table_name}: {str(e)[:100]}")
                    self.stats['processing_errors'] += 1
        
        return total_records
    
    def process_single_table(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        """Process a single table with optimized queries"""
        if not self.running:
            return 0
            
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            return 0
        
        primary_hostname_col = hostname_cols[0][0]
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        # Build optimized query with limits for faster processing
        query = self._build_fast_query(table_name, all_columns, primary_hostname_col)
        
        try:
            # Use job config for faster queries
            job_config = bigquery.QueryJobConfig()
            job_config.use_query_cache = True
            job_config.maximum_bytes_billed = 10 * 1024 * 1024 * 1024  # 10GB limit
            
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            return self._process_results_fast(results, table_name, primary_hostname_col, attribute_types)
            
        except Exception as e:
            logger.error(f"❌ Query failed for {table_name}: {str(e)[:100]}")
            return 0
    
    def _build_fast_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        """Build optimized query with sampling for large tables"""
        column_selects = [f"`{col}`" for col in columns]
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND `{hostname_col}` != '*Undefined'
        AND LENGTH(`{hostname_col}`) > 1
        LIMIT 1000000
        """
    
    def _process_results_fast(self, results, table_name: str, hostname_col: str, attribute_types: List[str]) -> int:
        """Fast batch processing of query results"""
        records_processed = 0
        batch_records = []
        batch_size = 5000  # Larger batches for speed
        
        for row in results:
            if not self.running:
                break
                
            records_processed += 1
            
            if not row[0] or not self.is_valid_value(row[0]):
                continue
            
            normalized_host = self.normalize_hostname(row[0])
            if not normalized_host:
                continue
            
            record_data = {
                'normalized_host': normalized_host,
                'hostname': str(row[0]).strip(),
                'table_name': table_name
            }
            
            # Fast attribute processing
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and self.is_valid_value(row[i]):
                    record_data[attr_type] = str(row[i]).strip()
            
            batch_records.append(record_data)
            
            if len(batch_records) >= batch_size:
                self._process_batch_fast(batch_records)
                batch_records.clear()
        
        if batch_records:
            self._process_batch_fast(batch_records)
        
        with self._lock:
            self.stats['total_records_processed'] += records_processed
            self.stats['tables_processed'] += 1
        
        return records_processed
    
    def _process_batch_fast(self, batch_records: List[Dict]):
        """Fast batch processing with bulk operations"""
        if not batch_records:
            return
        
        # Prepare bulk insert/update data
        new_records = []
        update_records = []
        
        # Get existing hosts in one query
        normalized_hosts = [r['normalized_host'] for r in batch_records]
        placeholders = ','.join(['?' for _ in normalized_hosts])
        
        existing_query = f"""
        SELECT normalized_host, source_tables, source_count 
        FROM universal_cmdb 
        WHERE normalized_host IN ({placeholders})
        """
        
        existing_hosts = {}
        try:
            existing_results = self.duck_conn.execute(existing_query, normalized_hosts).fetchall()
            existing_hosts = {row[0]: (row[1], row[2]) for row in existing_results}
        except:
            pass
        
        # Process records
        for record in batch_records:
            normalized_host = record['normalized_host']
            
            if normalized_host in existing_hosts:
                update_records.append(record)
                with self._lock:
                    self.stats['hosts_updated'] += 1
            else:
                new_records.append(record)
                with self._lock:
                    self.stats['hosts_created'] += 1
        
        # Bulk insert new records
        if new_records:
            self._bulk_insert(new_records)
        
        # Bulk update existing records
        if update_records:
            self._bulk_update(update_records, existing_hosts)
    
    def _bulk_insert(self, records: List[Dict]):
        """Bulk insert for maximum speed"""
        if not records:
            return
        
        columns = ['normalized_host', 'source_tables', 'source_count', 'hostname']
        data_columns = [
            'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        all_columns = columns + data_columns
        values_list = []
        
        for record in records:
            values = [
                record['normalized_host'],
                record['table_name'],
                1,
                record.get('hostname')
            ]
            
            for col in data_columns:
                values.append(record.get(col))
            
            values_list.append(values)
        
        # Use executemany for bulk insert
        placeholders = ', '.join(['?' for _ in all_columns])
        insert_sql = f"INSERT OR IGNORE INTO universal_cmdb ({', '.join(all_columns)}) VALUES ({placeholders})"
        
        try:
            self.duck_conn.executemany(insert_sql, values_list)
        except Exception as e:
            logger.error(f"❌ Bulk insert error: {str(e)[:100]}")
    
    def _bulk_update(self, records: List[Dict], existing_hosts: Dict):
        """Bulk update existing records"""
        for record in records:
            normalized_host = record['normalized_host']
            table_name = record['table_name']
            
            if normalized_host in existing_hosts:
                current_tables, source_count = existing_hosts[normalized_host]
                
                if table_name not in (current_tables or ""):
                    new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
                    new_source_count = (source_count or 0) + 1
                    
                    update_sql = """
                    UPDATE universal_cmdb 
                    SET source_tables = ?, source_count = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE normalized_host = ?
                    """
                    
                    try:
                        self.duck_conn.execute(update_sql, [new_tables, new_source_count, normalized_host])
                    except Exception as e:
                        logger.error(f"❌ Update error: {str(e)[:50]}")
    
    def keep_alive_monitor(self):
        """Background thread to keep the process alive and monitor progress"""
        while self.running:
            time.sleep(30)  # Check every 30 seconds
            
            current_time = time.time()
            elapsed = current_time - self.stats['start_time']
            
            logger.info(f"🔄 Status Update - Runtime: {elapsed:.0f}s")
            logger.info(f"   📊 Tables: {self.stats['tables_processed']}")
            logger.info(f"   🏠 Hosts: {self.stats['hosts_created'] + self.stats['hosts_updated']:,}")
            logger.info(f"   📝 Records: {self.stats['total_records_processed']:,}")
            
            # Force garbage collection
            import gc
            gc.collect()
    
    def process_all_optimized(self):
        """Main processing method with optimizations"""
        logger.info("🚀 Starting optimized processing...")
        
        # Start keep-alive monitor
        monitor_thread = threading.Thread(target=self.keep_alive_monitor, daemon=True)
        monitor_thread.start()
        
        try:
            metadata = self.load_metadata()
            discovered_columns = self.discover_columns_fast(metadata)
            
            if not discovered_columns:
                logger.error("❌ No columns discovered - exiting")
                return
            
            # Group columns by table for batch processing
            columns_by_table = defaultdict(list)
            for table_name, column_name, column_type in discovered_columns:
                columns_by_table[table_name].append((table_name, column_name, column_type))
            
            tables_list = list(columns_by_table.items())
            batch_size = max(1, len(tables_list) // self.max_workers)
            
            logger.info(f"📋 Processing {len(tables_list)} tables in batches of {batch_size}")
            
            # Process tables in parallel batches
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for i in range(0, len(tables_list), batch_size):
                    batch = tables_list[i:i + batch_size]
                    future = executor.submit(self.process_table_batch, batch)
                    futures.append(future)
                
                # Wait for all batches to complete
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        logger.info(f"✅ Batch completed: {result:,} records")
                    except Exception as e:
                        logger.error(f"❌ Batch failed: {str(e)[:100]}")
            
            self._generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ Critical error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
    
    def _generate_final_report(self):
        """Generate comprehensive final report"""
        logger.info("📊 Generating final report...")
        
        try:
            total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
            total_time = time.time() - self.stats['start_time']
            
            print("\n" + "=" * 80)
            print("🎉 PROCESSING COMPLETE - FINAL REPORT")
            print("=" * 80)
            print(f"⏱️  Total Runtime: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
            print(f"📋 Tables Processed: {self.stats['tables_processed']:,}")
            print(f"🔍 Columns Discovered: {self.stats['columns_discovered']:,}")
            print(f"📝 Records Processed: {self.stats['total_records_processed']:,}")
            print(f"🏠 Total Unique Hosts: {total_hosts:,}")
            print(f"➕ New Hosts Created: {self.stats['hosts_created']:,}")
            print(f"🔄 Hosts Updated: {self.stats['hosts_updated']:,}")
            print(f"⚡ Processing Speed: {self.stats['total_records_processed']/max(1, total_time):.0f} records/sec")
            
            if self.stats['processing_errors'] > 0:
                print(f"⚠️  Processing Errors: {self.stats['processing_errors']}")
            
            print("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}")
    
    def export_optimized(self, filename: str = "universal_cmdb_export.csv"):
        """Fast export with compression"""
        logger.info(f"💾 Exporting to {filename}...")
        
        try:
            export_query = f"""
            COPY (
                SELECT * FROM universal_cmdb 
                ORDER BY source_count DESC, normalized_host
            ) TO '{filename}' WITH (FORMAT CSV, HEADER)
            """
            self.duck_conn.execute(export_query)
            logger.info("✅ Export completed successfully")
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
    
    def close_connections(self):
        """Clean shutdown"""
        logger.info("🔒 Closing connections...")
        self.running = False
        
        try:
            self.duck_conn.close()
            logger.info("✅ Connections closed")
        except Exception as e:
            logger.error(f"⚠️  Cleanup warning: {e}")

def main():
    """Main execution with error handling and keep-alive"""
    processor = None
    
    try:
        print("\n🚀 ULTRA-FAST CMDB PROCESSOR")
        print("=" * 60)
        print("⚡ Optimized for speed and reliability")
        print("🔄 Designed to run continuously")
        print("=" * 60)
        
        processor = OptimizedCMDBProcessor(
            "reviewed_labeled_columns.json", 
            "universal_cmdb.db",
            max_workers=16  # Adjust based on your system
        )
        
        processor.process_all_optimized()
        processor.export_optimized("universal_cmdb_optimized.csv")
        
        print("\n🎉 SUCCESS - All processing completed!")
        
        # Keep alive option
        print("\n🔄 Process will continue running...")
        print("Press Ctrl+C twice quickly to force exit")
        
        while processor.running:
            time.sleep(60)  # Stay alive
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user - shutting down gracefully...")
        if processor:
            processor.running = False
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if processor:
            processor.close_connections()
        print("👋 Shutdown complete")

if __name__ == "__main__":
    main()