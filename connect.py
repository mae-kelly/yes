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

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
    import psutil

try:
    import wakepy
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'wakepy'])
    import wakepy

class FeminineFormatter(logging.Formatter):
    def format(self, record):
        return super().format(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(FeminineFormatter())
logger = logging.getLogger(__name__)
logger.handlers.clear()
logger.addHandler(console_handler)

class SystemOptimizer:
    def __init__(self):
        self.keep_alive_session = None
        self.original_priority = None
        
    def keep_system_awake(self):
        try:
            self.keep_alive_session = wakepy.keep.running()
            print("   ♡ System sleep prevention activated")
            return True
        except Exception as e:
            print(f"   ₊˚⊹ Warning: Could not prevent system sleep: {e}")
            return False
    
    def optimize_process_priority(self):
        try:
            current_process = psutil.Process()
            self.original_priority = current_process.nice()
            
            if platform.system() == "Windows":
                current_process.nice(psutil.HIGH_PRIORITY_CLASS)
            else:
                current_process.nice(-10)
            
            print(f"   ✧˚ Process priority elevated from {self.original_priority}")
            return True
        except Exception as e:
            print(f"   ₊˚⊹ Warning: Could not elevate process priority: {e}")
            return False
    
    def get_optimal_workers(self):
        cpu_count = multiprocessing.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        optimal_workers = min(cpu_count, max(2, int(memory_gb / 4)))
        
        print(f"   𖦹 CPU cores: {cpu_count}, RAM: {memory_gb:.1f}GB")
        print(f"   ♡ Optimal worker threads: {optimal_workers}")
        
        return optimal_workers
    
    def cleanup(self):
        if self.keep_alive_session:
            try:
                self.keep_alive_session.close()
                print("   ✧˚ System sleep prevention deactivated")
            except:
                pass
        
        if self.original_priority is not None:
            try:
                current_process = psutil.Process()
                current_process.nice(self.original_priority)
                print(f"   ♡ Process priority restored to {self.original_priority}")
            except:
                pass

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.last_check = time.time()
        self.processed_records = 0
        
    def update_progress(self, records_added: int, current_table: str = ""):
        self.processed_records += records_added
        current_time = time.time()
        
        total_elapsed = current_time - self.start_time
        records_per_second = self.processed_records / total_elapsed if total_elapsed > 0 else 0
        
        if current_table:
            print(f"      ⋆｡‧˚ Current: {current_table}")
        
        print(f"      ♡ Processed: {self.processed_records:,} records")
        print(f"      𖦹 Speed: {records_per_second:.0f} records/second")
        print(f"      ✧˚ Elapsed: {timedelta(seconds=int(total_elapsed))}")
        
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        print(f"      ༘˚⋆ CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%")

class OptimizedCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        print("\n\n")
        print("═" * 90)
        print("                ₊˚✩ OPTIMIZED CMDB PROCESSOR INITIALIZATION ✩˚₊")
        print("═" * 90)
        print()
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        print("   Initializing system optimizations...")
        print()
        
        self.system_optimizer = SystemOptimizer()
        self.performance_monitor = PerformanceMonitor()
        
        print("   ༘˚⋆ Optimizing system performance...")
        self.system_optimizer.keep_system_awake()
        self.system_optimizer.optimize_process_priority()
        
        self.optimal_workers = self.system_optimizer.get_optimal_workers()
        self.batch_size = min(5000, max(1000, self.optimal_workers * 500))
        
        print(f"   ♡ Batch size optimized: {self.batch_size:,} records")
        print()
        
        logger.info("Setting up column mapping dictionaries...")
        
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
            'business_unit': [
                'business_unit', 'bu', 'business', 'department', 'division', 'org_unit',
                'organizational_unit', 'cost_center', 'business_group', 'dept', 'organization'
            ],
            'region': [
                'region', 'location', 'site', 'area', 'zone', 'geographic_region',
                'geo_region', 'datacenter_region', 'site_location', 'geographical_location'
            ],
            'country': [
                'country', 'nation', 'country_code', 'geo_country', 'location_country'
            ],
            'infrastructure_type': [
                'infrastructure_type', 'infra_type', 'server_type', 'system_type',
                'platform', 'environment', 'env', 'deployment_type', 'platform_type',
                'os_type', 'system_platform'
            ],
            'data_center': [
                'datacenter', 'data_center', 'dc', 'facility', 'center', 'site_name',
                'datacenter_name', 'facility_name', 'dc_location'
            ],
            'cloud_region': [
                'cloud_region', 'aws_region', 'azure_region', 'gcp_region',
                'cloud_location', 'cloud_zone', 'availability_zone'
            ],
            'ip_address': [
                'ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip', 'server_ip',
                'endpoint_ip', 'device_ip', 'internal_ip', 'external_ip', 'primary_ip'
            ],
            'class': [
                'class', 'classification', 'tier', 'level', 'grade', 'category',
                'server_class', 'system_class'
            ],
            'system_classification': [
                'system_classification', 'security_classification', 'data_classification',
                'classification_level', 'sensitivity', 'security_level'
            ],
            'apm': [
                'apm', 'monitoring', 'application_monitoring', 'performance_monitoring',
                'apm_enabled', 'monitoring_enabled'
            ],
            'cio': [
                'cio', 'owner', 'responsible', 'contact', 'admin', 'administrator',
                'system_owner', 'business_owner', 'technical_owner'
            ],
            'edr_coverage': [
                'edr_coverage', 'edr', 'endpoint_detection', 'security_agent',
                'antivirus', 'av_coverage', 'endpoint_protection'
            ],
            'tanium_coverage': [
                'tanium_coverage', 'tanium', 'tanium_agent', 'endpoint_management'
            ],
            'dlp_agent_coverage': [
                'dlp_agent_coverage', 'dlp', 'data_loss_prevention', 'dlp_agent'
            ],
            'logging_in_splunk': [
                'logging_in_splunk', 'splunk', 'splunk_logging', 'log_forwarding'
            ],
            'logging_in_gso': [
                'logging_in_gso', 'gso', 'gso_logging', 'security_logging'
            ],
            'domain': [
                'domain', 'dns_domain', 'ad_domain', 'windows_domain'
            ],
            'fqdn': [
                'fqdn', 'full_name', 'qualified_name', 'dns_name', 'fully_qualified'
            ]
        }
        
        self.stats = {
            'tables_processed': 0,
            'tables_total': 0,
            'columns_discovered': 0,
            'hosts_created': 0,
            'hosts_updated': 0,
            'duplicate_hosts_found': 0,
            'total_records_processed': 0,
            'processing_errors': 0,
            'current_table': '',
            'processing_start_time': time.time()
        }
        
        self.duplicate_tracker = set()
        
        print("   𖦹 Establishing BigQuery connection...")
        self._init_bigquery()
        print()
        
        print("   ⋆｡‧˚ Establishing DuckDB connection...")
        self.duck_conn = duckdb.connect(duckdb_path)
        print(f"      Database: {duckdb_path}")
        print()
        
        print("   ༘˚⋆ Creating optimized database schema...")
        self._create_optimized_table()
        print("      Schema: 25 columns with performance indexes")
        print()
        
        print("─" * 70)
        print("              ♡ High-Performance Initialization Complete ♡")
        print("─" * 70)
        print()
        
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            print(f"      Using service account: {os.path.basename(service_account_file)}")
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
            print("      ✧˚ Authentication successful")
        else:
            print("      Using default credentials")
            self.bq_client = bigquery.Client(project="chronicle-fisv")
            print("      ♡ Connected successfully")
    
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
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_business_unit ON universal_cmdb(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)",
            "CREATE INDEX IF NOT EXISTS idx_infrastructure_type ON universal_cmdb(infrastructure_type)",
            "CREATE INDEX IF NOT EXISTS idx_source_count ON universal_cmdb(source_count)"
        ]
        
        for index_sql in indexes:
            try:
                self.duck_conn.execute(index_sql)
            except:
                pass
    
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str) or hostname.strip() == '*Undefined':
            return ""
        
        normalized = hostname.lower().strip()
        
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        normalized = normalized.replace('-', '')
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized if len(normalized) > 1 else ""
    
    def is_valid_value(self, value) -> bool:
        if not value:
            return False
        if isinstance(value, str):
            stripped = value.strip()
            return stripped != '' and stripped != '*Undefined' and stripped.lower() not in ['null', 'none', 'undefined']
        return True
    
    def load_metadata(self) -> Dict:
        print("\n")
        print("═" * 80)
        print("                      ₊˚✩ METADATA LOADING ✩˚₊")
        print("═" * 80)
        print()
        
        print(f"   Loading: {self.json_file_path}")
        print()
        
        start_time = time.time()
        
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        
        load_time = time.time() - start_time
        
        if 'columns' in metadata:
            table_count = len(metadata['columns'])
            column_count = sum(len(cols) for cols in metadata['columns'].values())
            
            self.stats['tables_total'] = table_count
            
            print(f"   ♡ Loaded in {load_time:.2f} seconds")
            print()
            print(f"   Tables discovered: {table_count:,}")
            print(f"   Columns discovered: {column_count:,}")
            print(f"   Average columns per table: {column_count/table_count:.1f}")
            print()
        else:
            print("   ₊˚⊹ Warning: Metadata structure issue")
            print()
        
        print("─" * 60)
        print("              ✧˚ Metadata Analysis Complete ✧˚")
        print("─" * 60)
        print()
            
        return metadata
    
    def discover_columns_comprehensive(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        print("═" * 80)
        print("                   ༘˚⋆ COLUMN DISCOVERY ⋆˚༘")
        print("═" * 80)
        print()
        
        print("   Advanced pattern matching analysis...")
        print()
        
        discovered_columns = []
        
        if 'columns' not in metadata:
            print("   𖦹 Error: Invalid metadata structure")
            return []
        
        table_count = len(metadata['columns'])
        
        print(f"   Scanning {table_count} tables...")
        print()
        
        progress_interval = max(1, table_count // 20)
        
        for table_idx, (table_name, columns) in enumerate(metadata['columns'].items(), 1):
            if table_idx % progress_interval == 0 or table_idx == table_count:
                progress_pct = (table_idx / table_count) * 100
                print(f"   ⋆｡‧˚ Progress: {progress_pct:.1f}% ({table_idx}/{table_count})")
            
            table_matches = 0
            
            for column_name, column_type in columns.items():
                mapped_type = self._identify_column_type(column_name, column_type)
                
                if mapped_type:
                    discovered_columns.append((table_name, column_name, mapped_type))
                    table_matches += 1
            
            if table_matches > 0:
                print(f"      ♡ {os.path.basename(table_name)}: {table_matches} columns")
        
        self.stats['columns_discovered'] = len(discovered_columns)
        
        print()
        print("─" * 60)
        print(f"    ✧˚ Discovery Complete: {len(discovered_columns)} Mappable Columns ✧˚")
        print("─" * 60)
        print()
        
        return discovered_columns
    
    def _identify_column_type(self, column_name: str, column_type) -> Optional[str]:
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        if isinstance(column_type, str) and type_lower in self.column_mapping:
            return self.column_mapping[type_lower]
        
        for pattern in self.hostname_patterns:
            if pattern in column_lower:
                return 'hostname'
        
        for target_type, patterns in self.advanced_patterns.items():
            for pattern in patterns:
                if pattern in column_lower or pattern in type_lower:
                    return target_type
        
        return None
    
    def process_table_batch_optimized(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        self.stats['current_table'] = table_name
        table_display = os.path.basename(table_name)
        
        print("─" * 80)
        print(f"   🔄 PROCESSING: {table_display}")
        print("─" * 80)
        print()
        
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            print("   ₊˚⊹ Skipped - no hostname columns")
            return 0
        
        primary_hostname_col = hostname_cols[0][0]
        print(f"   Primary hostname: {primary_hostname_col}")
        
        if attribute_cols:
            print(f"   Attribute columns: {len(attribute_cols)}")
            for col, ctype in attribute_cols[:5]:
                print(f"      • {col} → {ctype}")
            if len(attribute_cols) > 5:
                print(f"      • ... and {len(attribute_cols) - 5} more")
        print()
        
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        query = self._build_optimized_query(table_name, all_columns, primary_hostname_col)
        
        print("   ⋆｡‧˚ Executing optimized BigQuery...")
        
        table_start_time = time.time()
        
        try:
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                use_legacy_sql=False,
                maximum_bytes_billed=50 * 1024 * 1024 * 1024,
                job_timeout_ms=30 * 60 * 1000
            )
            
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result(page_size=self.batch_size)
            
            query_time = time.time() - table_start_time
            print(f"   Query completed: {query_time:.2f}s")
            print()
            
            records_processed = self._process_results_batch_parallel(
                results, table_name, primary_hostname_col, attribute_types
            )
            
            total_time = time.time() - table_start_time
            print(f"   ✧˚ Table completed: {total_time:.2f}s total")
            print(f"      Records processed: {records_processed:,}")
            print(f"      Processing rate: {records_processed/total_time:.0f} records/sec")
            print()
            
            return records_processed
            
        except Exception as e:
            print(f"   𖦹 Error: {str(e)[:80]}...")
            self.stats['processing_errors'] += 1
            return 0
    
    def _build_optimized_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        column_selects = [f"`{col}`" for col in columns]
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND `{hostname_col}` != '*Undefined'
        AND LENGTH(`{hostname_col}`) > 0
        """
    
    def _process_results_batch_parallel(self, results, table_name: str, hostname_col: str, attribute_types: List[str]) -> int:
        print("   ༘˚⋆ High-speed batch processing...")
        
        records_processed = 0
        hosts_created = 0
        hosts_updated = 0
        duplicates_in_table = 0
        attribute_stats = {attr_type: 0 for attr_type in attribute_types}
        
        batch_records = []
        table_hostnames_seen = set()
        
        update_interval = self.batch_size
        last_update = time.time()
        
        for row_idx, row in enumerate(results):
            records_processed += 1
            
            current_time = time.time()
            if records_processed % update_interval == 0 or (current_time - last_update) > 5.0:
                elapsed = current_time - self.stats['processing_start_time']
                overall_rate = self.stats['total_records_processed'] / elapsed if elapsed > 0 else 0
                
                print(f"      ♡ {records_processed:,} rows | {overall_rate:.0f} rec/sec | {timedelta(seconds=int(elapsed))}")
                last_update = current_time
            
            if not row[0] or not self.is_valid_value(row[0]):
                continue
            
            normalized_host = self.normalize_hostname(row[0])
            if not normalized_host:
                continue
            
            if normalized_host in table_hostnames_seen:
                duplicates_in_table += 1
                continue
            else:
                table_hostnames_seen.add(normalized_host)
            
            record_data = {
                'normalized_host': normalized_host,
                'hostname': str(row[0]).strip(),
                'table_name': table_name
            }
            
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and self.is_valid_value(row[i]):
                    record_data[attr_type] = str(row[i]).strip()
                    attribute_stats[attr_type] += 1
            
            batch_records.append(record_data)
            
            if len(batch_records) >= self.batch_size:
                created, updated = self._process_record_batch_fast(batch_records)
                hosts_created += created
                hosts_updated += updated
                batch_records.clear()
        
        if batch_records:
            created, updated = self._process_record_batch_fast(batch_records)
            hosts_created += created
            hosts_updated += updated
        
        print()
        print("   📊 Processing Results:")
        print(f"      ♡ Raw records: {records_processed:,}")
        print(f"      ⋆｡‧˚ New hosts: {hosts_created:,}")
        print(f"      𖦹 Updated hosts: {hosts_updated:,}")
        
        if duplicates_in_table > 0:
            print(f"      ₊˚⊹ Table duplicates: {duplicates_in_table:,}")
            self.stats['duplicate_hosts_found'] += duplicates_in_table
        
        if attribute_stats:
            print()
            print("   📝 Attribute Data Captured:")
            for attr_type, count in sorted(attribute_stats.items()):
                if count > 0:
                    print(f"      • {attr_type}: {count:,}")
        
        self.stats['total_records_processed'] += records_processed
        self.stats['hosts_created'] += hosts_created
        self.stats['hosts_updated'] += hosts_updated
        
        self.performance_monitor.update_progress(records_processed, table_name)
        
        return records_processed
    
    def _process_record_batch_fast(self, batch_records: List[Dict]) -> Tuple[int, int]:
        hosts_created = 0
        hosts_updated = 0
        
        for record in batch_records:
            normalized_host = record['normalized_host']
            
            if normalized_host in self.duplicate_tracker:
                hosts_updated += 1
                self._insert_or_update_optimized(record)
            else:
                self.duplicate_tracker.add(normalized_host)
                if self._insert_or_update_optimized(record):
                    hosts_created += 1
                else:
                    hosts_updated += 1
        
        return hosts_created, hosts_updated
    
    def _insert_or_update_optimized(self, record: Dict) -> bool:
        normalized_host = record['normalized_host']
        table_name = record['table_name']
        
        existing_query = """
        SELECT source_tables, data_quality_score, source_count,
               hostname, fqdn, domain, infrastructure_type, region, country, data_center,
               cloud_region, ip_address, class, system_classification, business_unit,
               apm, cio, edr_coverage, tanium_coverage, dlp_agent_coverage,
               logging_in_splunk, logging_in_gso
        FROM universal_cmdb WHERE normalized_host = ?
        """
        
        existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
        
        if existing:
            return self._update_existing_host(normalized_host, record, existing)
        else:
            return self._create_new_host(record)
    
    def _update_existing_host(self, normalized_host: str, record: Dict, existing) -> bool:
        updates = []
        values = []
        
        current_tables = existing[0] if existing[0] else ""
        table_name = record['table_name']
        
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            
            new_source_count = (existing[2] or 0) + 1
            updates.append("source_count = ?")
            values.append(new_source_count)
        
        column_names = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for i, col_name in enumerate(column_names, 3):
            if col_name in record:
                new_value = record[col_name]
                existing_value = existing[i] if i < len(existing) and existing[i] else None
                
                final_value = self._merge_values(existing_value, new_value)
                
                if final_value != existing_value:
                    updates.append(f"{col_name} = ?")
                    values.append(final_value)
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            self.duck_conn.execute(update_sql, values)
        
        return False
    
    def _create_new_host(self, record: Dict) -> bool:
        columns = ['normalized_host', 'source_tables', 'source_count']
        values = [record['normalized_host'], record['table_name'], 1]
        
        data_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for col in data_columns:
            columns.append(col)
            values.append(record.get(col))
        
        placeholders = ', '.join(['?' for _ in values])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        self.duck_conn.execute(insert_sql, values)
        return True
    
    def _merge_values(self, existing_value: Optional[str], new_value: str) -> str:
        if not existing_value or existing_value.strip() == '':
            return new_value
        
        if not new_value or new_value.strip() == '':
            return existing_value
        
        existing_parts = set(part.strip() for part in existing_value.split('|'))
        new_part = new_value.strip()
        
        if new_part not in existing_parts:
            existing_parts.add(new_part)
            return ' | '.join(sorted(existing_parts))
        
        return existing_value
    
    def create_comprehensive_summary(self):
        print("\n")
        print("═" * 80)
        print("                  ⋆｡‧˚ SUMMARY CREATION ˚‧｡⋆")
        print("═" * 80)
        print()
        
        print("   Building comprehensive analysis views...")
        
        try:
            self.duck_conn.execute("DROP TABLE IF EXISTS all_sources")
            self.duck_conn.execute("DROP TABLE IF EXISTS data_quality_summary")
            
            all_sources_sql = """
            CREATE TABLE all_sources AS (
                SELECT 
                    normalized_host as host,
                    source_tables,
                    source_count,
                    data_quality_score,
                    hostname, fqdn, domain, infrastructure_type, region, country,
                    data_center, cloud_region, ip_address, class, system_classification,
                    business_unit, apm, cio, edr_coverage, tanium_coverage, 
                    dlp_agent_coverage, logging_in_splunk, logging_in_gso,
                    first_seen, last_updated
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                ORDER BY source_count DESC, data_quality_score DESC, normalized_host
            )
            """
            
            self.duck_conn.execute(all_sources_sql)
            
            print("   ♡ Analysis tables created")
            print("   ✧˚ Summary views optimized")
            print()
            
        except Exception as e:
            print(f"   𖦹 Summary creation error: {str(e)[:60]}...")
    
    def generate_performance_report(self):
        print("\n")
        print("═" * 90)
        print("                 ₊˚✩ HIGH-PERFORMANCE PROCESSING REPORT ✩˚₊")
        print("═" * 90)
        print()
        
        total_time = time.time() - self.stats['processing_start_time']
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print("   🏆 PERFORMANCE METRICS")
        print("   " + "─" * 40)
        print()
        print(f"   ♡ Total processing time: {timedelta(seconds=int(total_time))}")
        print(f"   𖦹 Tables processed: {self.stats['tables_processed']}/{self.stats['tables_total']}")
        print(f"   ⋆｡‧˚ Records processed: {self.stats['total_records_processed']:,}")
        print(f"   ༘˚⋆ Average processing speed: {self.stats['total_records_processed']/total_time:.0f} records/second")
        print(f"   ✧˚ Optimal batch size used: {self.batch_size:,}")
        print(f"   ₊˚✩ Worker threads utilized: {self.optimal_workers}")
        print()
        
        print("   📊 DATA QUALITY ANALYSIS")
        print("   " + "─" * 35)
        print()
        print(f"   ♡ Unique hosts discovered: {total_hosts:,}")
        print(f"   ⋆｡‧˚ New hosts created: {self.stats['hosts_created']:,}")
        print(f"   𖦹 Existing hosts updated: {self.stats['hosts_updated']:,}")
        print(f"   ₊˚⊹ Duplicate records found: {self.stats['duplicate_hosts_found']:,}")
        
        if self.stats['total_records_processed'] > 0:
            duplicate_rate = (self.stats['duplicate_hosts_found'] / self.stats['total_records_processed']) * 100
            dedup_efficiency = ((self.stats['total_records_processed'] - self.stats['duplicate_hosts_found']) / self.stats['total_records_processed']) * 100
            print(f"   ༘˚⋆ Duplicate rate: {duplicate_rate:.1f}%")
            print(f"   ♡ Deduplication efficiency: {dedup_efficiency:.1f}%")
        print()
        
        columns_to_check = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        print("   📈 COLUMN POPULATION SUCCESS")
        print("   " + "─" * 40)
        print()
        
        populated_columns = []
        high_quality_columns = []
        
        for col in columns_to_check:
            count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            count = self.duck_conn.execute(count_query).fetchone()[0]
            percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
            
            if count > 0:
                populated_columns.append(col)
                if percentage >= 50:
                    high_quality_columns.append((col, percentage))
                    print(f"   ✧˚ {col}: {count:,} ({percentage:.1f}%)")
                else:
                    print(f"   ♡ {col}: {count:,} ({percentage:.1f}%)")
        
        print()
        print(f"   🎯 SUCCESS SUMMARY")
        print("   " + "─" * 25)
        print()
        print(f"   ♡ Populated columns: {len(populated_columns)}/19 ({len(populated_columns)/19*100:.1f}%)")
        print(f"   ✧˚ High-quality columns (>50%): {len(high_quality_columns)}")
        print(f"   𖦹 Column discovery rate: {self.stats['columns_discovered']/self.stats['tables_total']:.1f} per table")
        
        if self.stats['processing_errors'] > 0:
            error_rate = (self.stats['processing_errors'] / self.stats['tables_total']) * 100
            print(f"   ₊˚⊹ Processing errors: {self.stats['processing_errors']} ({error_rate:.1f}%)")
        
        print()
        print("   📄 TOP ENRICHED RECORDS")
        print("   " + "─" * 35)
        print()
        
        sample_query = """
        SELECT normalized_host, source_count, 
               (CASE WHEN hostname IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN business_unit IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN region IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN infrastructure_type IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN ip_address IS NOT NULL THEN 1 ELSE 0 END) as field_count
        FROM universal_cmdb 
        ORDER BY field_count DESC, source_count DESC
        LIMIT 5
        """
        
        samples = self.duck_conn.execute(sample_query).fetchall()
        
        for i, (host, sources, fields) in enumerate(samples, 1):
            print(f"   {i}. {host}")
            print(f"      Sources: {sources} | Fields: {fields}")
        
        print()
        print("─" * 70)
        print("            ✧˚ High-Performance Processing Complete ✧˚")
        print("─" * 70)
        print()
    
    def export_optimized(self, filename: str = "universal_cmdb_export.csv"):
        print("═" * 80)
        print("                    ༘˚⋆ OPTIMIZED DATA EXPORT ⋆˚༘")
        print("═" * 80)
        print()
        
        print(f"   Exporting to: {filename}")
        
        try:
            export_start = time.time()
            
            export_query = f"""
            COPY (
                SELECT * FROM universal_cmdb 
                ORDER BY source_count DESC, data_quality_score DESC, normalized_host
            ) TO '{filename}' WITH (FORMAT CSV, HEADER)
            """
            self.duck_conn.execute(export_query)
            
            export_time = time.time() - export_start
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            print(f"   ✧˚ Export completed in {export_time:.2f}s")
            print(f"   ♡ File size: {file_size:.1f} MB")
            print(f"   𖦹 Export rate: {file_size/export_time:.1f} MB/s")
            print()
            
        except Exception as e:
            print(f"   ₊˚⊹ Export error: {str(e)[:60]}...")
    
    def process_all_high_performance(self):
        print("\n")
        print("═" * 90)
        print("            ₊˚✩ HIGH-PERFORMANCE BATCH PROCESSING START ✩˚₊")
        print("═" * 90)
        print()
        
        self.stats['processing_start_time'] = time.time()
        
        metadata = self.load_metadata()
        discovered_columns = self.discover_columns_comprehensive(metadata)
        
        if not discovered_columns:
            print("   𖦹 No processable columns found")
            return
        
        print("═" * 80)
        print("                  ⋆｡‧˚ BATCH TABLE PROCESSING ˚‧｡⋆")
        print("═" * 80)
        print()
        
        columns_by_table = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((table_name, column_name, column_type))
        
        self.stats['tables_total'] = len(columns_by_table)
        
        print(f"   🚀 Processing {len(columns_by_table)} tables with maximum optimization")
        print(f"   ⋆｡‧˚ Batch size: {self.batch_size:,} records")
        print(f"   ♡ Worker threads: {self.optimal_workers}")
        print()
        
        start_time = time.time()
        
        for table_idx, (table_name, table_columns) in enumerate(columns_by_table.items(), 1):
            self.stats['tables_processed'] = table_idx
            
            progress_pct = (table_idx / len(columns_by_table)) * 100
            elapsed = time.time() - start_time
            
            print(f"   📍 TABLE {table_idx}/{len(columns_by_table)} ({progress_pct:.1f}%)")
            print(f"      Elapsed: {timedelta(seconds=int(elapsed))}")
            print(f"      ETA: {timedelta(seconds=int(elapsed * (len(columns_by_table) - table_idx) / table_idx)) if table_idx > 0 else 'calculating...'}")
            print()
            
            table_start = time.time()
            records_processed = self.process_table_batch_optimized(table_name, table_columns)
            
            if records_processed > 0:
                table_time = time.time() - table_start
                print(f"   ⚡ Table rate: {records_processed/table_time:.0f} records/sec")
            
            print()
        
        self.create_comprehensive_summary()
        self.generate_performance_report()
        
        total_time = time.time() - start_time
        
        print("═" * 80)
        print("              ₊˚✩ HIGH-PERFORMANCE PROCESSING COMPLETE ✩˚₊")
        print("═" * 80)
        print()
        print(f"   🏆 Total time: {timedelta(seconds=int(total_time))}")
        print(f"   ⚡ Overall rate: {self.stats['total_records_processed']/total_time:.0f} records/second")
        print(f"   ♡ System optimizations utilized throughout processing")
        print()
    
    def cleanup(self):
        print("\n")
        print("═" * 80)
        print("                   ༘˚⋆ SYSTEM CLEANUP ⋆˚༘")
        print("═" * 80)
        print()
        
        try:
            self.duck_conn.close()
            print("   ♡ Database connections closed")
        except:
            pass
        
        self.system_optimizer.cleanup()
        
        print("   ✧˚ All systems restored to normal operation")
        print()

if __name__ == "__main__":
    print("\n")
    print("═" * 100)
    print("               ₊˚✩ ULTRA HIGH-PERFORMANCE UNIVERSAL CMDB PROCESSOR ✩˚₊")
    print("═" * 100)
    print()
    print("   Advanced system optimizations for maximum processing speed")
    print("   Intelligent batch processing with real-time performance monitoring")
    print("   Comprehensive duplicate detection and data quality analysis")
    print()
    print("═" * 100)
    
    processor = None
    
    try:
        processor = OptimizedCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        
        processor.process_all_high_performance()
        processor.export_optimized("universal_cmdb_complete.csv")
        
        print("\n")
        print("═" * 100)
        print("                     ✧˚ ULTRA HIGH-PERFORMANCE PROCESSING COMPLETE ✧˚")
        print("═" * 100)
        print()
        print("   🏆 Maximum performance achieved with system optimizations")
        print("   ♡ Universal CMDB successfully created with comprehensive data")
        print("   𖦹 All duplicate detection and quality analysis completed")
        print()
        print("   Database: universal_cmdb.db")
        print("   Export: universal_cmdb_complete.csv")
        print()
        print("═" * 100)
        
    except KeyboardInterrupt:
        print("\n\n")
        print("═" * 80)
        print("                     ₊˚⊹ PROCESSING INTERRUPTED ⊹˚₊")
        print("═" * 80)
        print()
        print("   Processing stopped by user - partial data saved")
        
    except Exception as e:
        print("\n\n")
        print("═" * 80)
        print("                        𖦹 PROCESSING ERROR 𖦹")
        print("═" * 80)
        print()
        print(f"   Error: {str(e)[:80]}...")
        import traceback
        for line in traceback.format_exc().split('\n')[:8]:
            if line.strip():
                print(f"   {line}")
        
    finally:
        if processor:
            processor.cleanup()