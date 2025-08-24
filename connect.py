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
import multiprocessing
from queue import Queue
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa

# Minimal logging setup
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class UltraFastCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        print("\n═══ ULTRA-FAST CMDB PROCESSOR ═══\n")
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Pre-compiled regex patterns for faster matching
        self.normalize_pattern = re.compile(r'[^a-z0-9]')
        self.hostname_split_pattern = re.compile(r'\.')
        
        # Optimized column mappings with frozen sets for O(1) lookups
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
        
        # Frozen sets for O(1) membership testing
        self.hostname_patterns = frozenset([
            'host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name',
            'endpoint_name', 'splunk_host', 'app_host', 'computer_name', 'machine_name',
            'chronicle_device_hostname', 'endpointdomain_name', 'asset_name'
        ])
        
        # Pre-compiled pattern sets for faster lookups
        self.advanced_patterns = {
            'business_unit': frozenset(['business_unit', 'bu', 'business', 'department', 'division', 'org_unit']),
            'region': frozenset(['region', 'location', 'site', 'area', 'zone', 'geographic_region']),
            'country': frozenset(['country', 'nation', 'country_code', 'geo_country']),
            'infrastructure_type': frozenset(['infrastructure_type', 'infra_type', 'server_type', 'system_type', 'platform']),
            'data_center': frozenset(['datacenter', 'data_center', 'dc', 'facility', 'center']),
            'cloud_region': frozenset(['cloud_region', 'aws_region', 'azure_region', 'gcp_region']),
            'ip_address': frozenset(['ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip']),
            'class': frozenset(['class', 'classification', 'tier', 'level']),
            'system_classification': frozenset(['system_classification', 'security_classification']),
            'apm': frozenset(['apm', 'monitoring', 'application_monitoring']),
            'cio': frozenset(['cio', 'owner', 'responsible', 'contact']),
            'edr_coverage': frozenset(['edr_coverage', 'edr', 'endpoint_detection']),
            'tanium_coverage': frozenset(['tanium_coverage', 'tanium', 'tanium_agent']),
            'dlp_agent_coverage': frozenset(['dlp_agent_coverage', 'dlp', 'data_loss_prevention']),
            'logging_in_splunk': frozenset(['logging_in_splunk', 'splunk', 'splunk_logging']),
            'logging_in_gso': frozenset(['logging_in_gso', 'gso', 'gso_logging']),
            'domain': frozenset(['domain', 'dns_domain', 'ad_domain']),
            'fqdn': frozenset(['fqdn', 'full_name', 'qualified_name'])
        }
        
        self.stats = defaultdict(int)
        self.duplicate_tracker = set()
        
        # Initialize connections
        self._init_bigquery()
        
        # Use WAL mode for better concurrency
        self.duck_conn = duckdb.connect(duckdb_path)
        self.duck_conn.execute("PRAGMA threads=8")  # Use multiple threads
        self.duck_conn.execute("PRAGMA memory_limit='8GB'")  # Increase memory limit
        
        self._create_optimized_table()
        
        # Pre-create prepared statements for better performance
        self._prepare_statements()
        
        print("Initialization complete. Ready for ultra-fast processing.\n")
    
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
    
    def _create_optimized_table(self):
        # Create table with optimal column types and compression
        create_sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR PRIMARY KEY,
            source_tables VARCHAR,
            hostname VARCHAR,
            fqdn VARCHAR,
            domain VARCHAR,
            infrastructure_type VARCHAR,
            region VARCHAR,
            country VARCHAR,
            data_center VARCHAR,
            cloud_region VARCHAR,
            ip_address VARCHAR,
            class VARCHAR,
            system_classification VARCHAR,
            business_unit VARCHAR,
            apm VARCHAR,
            cio VARCHAR,
            edr_coverage VARCHAR,
            tanium_coverage VARCHAR,
            dlp_agent_coverage VARCHAR,
            logging_in_splunk VARCHAR,
            logging_in_gso VARCHAR,
            data_quality_score DOUBLE DEFAULT 1.0,
            source_count INTEGER DEFAULT 1,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(create_sql)
        
        # Create indexes in parallel
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_source_count ON universal_cmdb(source_count)"
        ]
        
        for idx in indexes:
            try:
                self.duck_conn.execute(idx)
            except:
                pass
    
    def _prepare_statements(self):
        """Pre-prepare statements for better performance"""
        self.duck_conn.execute("""
            PREPARE select_existing AS 
            SELECT source_tables, data_quality_score, source_count,
                   hostname, fqdn, domain, infrastructure_type, region, country, data_center,
                   cloud_region, ip_address, class, system_classification, business_unit,
                   apm, cio, edr_coverage, tanium_coverage, dlp_agent_coverage,
                   logging_in_splunk, logging_in_gso
            FROM universal_cmdb WHERE normalized_host = $1
        """)
    
    def normalize_hostname(self, hostname: str) -> str:
        """Optimized hostname normalization"""
        if not hostname or not isinstance(hostname, str) or hostname.strip() == '*Undefined':
            return ""
        
        normalized = hostname.lower().strip()
        
        # Use pre-compiled regex
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
        print("Loading metadata...")
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        
        if 'columns' in metadata:
            table_count = len(metadata['columns'])
            print(f"Found {table_count} tables\n")
        
        return metadata
    
    def discover_columns_comprehensive(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        """Optimized column discovery using set operations"""
        print("Discovering columns...")
        
        discovered_columns = []
        
        if 'columns' not in metadata:
            return []
        
        for table_name, columns in metadata['columns'].items():
            for column_name, column_type in columns.items():
                mapped_type = self._identify_column_type_fast(column_name, column_type)
                
                if mapped_type:
                    discovered_columns.append((table_name, column_name, mapped_type))
        
        self.stats['columns_discovered'] = len(discovered_columns)
        print(f"Discovered {len(discovered_columns)} relevant columns\n")
        
        return discovered_columns
    
    def _identify_column_type_fast(self, column_name: str, column_type) -> Optional[str]:
        """Ultra-fast column type identification using sets"""
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        # Direct mapping lookup (O(1))
        if isinstance(column_type, str) and type_lower in self.column_mapping:
            return self.column_mapping[type_lower]
        
        # Check hostname patterns using set intersection
        for pattern in self.hostname_patterns:
            if pattern in column_lower:
                return 'hostname'
        
        # Check advanced patterns using set operations
        for target_type, patterns in self.advanced_patterns.items():
            for pattern in patterns:
                if pattern in column_lower or pattern in type_lower:
                    return target_type
        
        return None
    
    def process_tables_parallel(self, columns_by_table: Dict) -> None:
        """Process multiple tables in parallel using ThreadPoolExecutor"""
        print(f"Processing {len(columns_by_table)} tables in parallel...\n")
        
        max_workers = min(8, len(columns_by_table))  # Limit concurrent BigQuery requests
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for table_name, table_columns in columns_by_table.items():
                future = executor.submit(self.process_table_optimized, table_name, table_columns)
                futures[future] = table_name
            
            for future in as_completed(futures):
                table_name = futures[future]
                try:
                    records = future.result()
                    print(f"✓ {table_name}: {records:,} records")
                except Exception as e:
                    print(f"✗ {table_name}: Error - {str(e)[:50]}")
                    self.stats['processing_errors'] += 1
    
    def process_table_optimized(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        """Optimized table processing with batch operations"""
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            return 0
        
        primary_hostname_col = hostname_cols[0][0]
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        query = self._build_optimized_query(table_name, all_columns, primary_hostname_col)
        
        try:
            # Use BigQuery's batch mode for better performance
            job_config = bigquery.QueryJobConfig()
            job_config.use_query_cache = True
            job_config.use_legacy_sql = False
            
            query_job = self.bq_client.query(query, job_config=job_config)
            
            # Process results in batches
            records_processed = self._process_results_batch(
                query_job, table_name, primary_hostname_col, attribute_types
            )
            
            self.stats['tables_processed'] += 1
            return records_processed
            
        except Exception as e:
            self.stats['processing_errors'] += 1
            return 0
    
    def _build_optimized_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        """Build optimized query with better filtering"""
        column_selects = [f"`{col}`" for col in columns]
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND `{hostname_col}` != '*Undefined'
        AND LENGTH(`{hostname_col}`) > 0
        LIMIT 1000000
        """
    
    def _process_results_batch(self, query_job, table_name: str, hostname_col: str, attribute_types: List[str]) -> int:
        """Process query results in large batches for better performance"""
        records_processed = 0
        batch_size = 10000  # Larger batch size
        batch_records = []
        table_hostnames_seen = set()
        
        # Convert to pandas for faster processing
        try:
            df = query_job.to_dataframe()
            
            if df.empty:
                return 0
            
            records_processed = len(df)
            
            # Vectorized operations for faster processing
            df['normalized_host'] = df.iloc[:, 0].apply(self.normalize_hostname)
            
            # Remove invalid hosts
            df = df[df['normalized_host'] != '']
            
            # Remove duplicates within table
            df = df.drop_duplicates(subset=['normalized_host'])
            
            # Process in chunks
            for chunk_start in range(0, len(df), batch_size):
                chunk_end = min(chunk_start + batch_size, len(df))
                chunk = df.iloc[chunk_start:chunk_end]
                
                batch_data = []
                for _, row in chunk.iterrows():
                    record_data = {
                        'normalized_host': row['normalized_host'],
                        'hostname': str(row.iloc[0]).strip(),
                        'table_name': table_name
                    }
                    
                    for i, attr_type in enumerate(attribute_types, 1):
                        if i < len(row) and self.is_valid_value(row.iloc[i]):
                            record_data[attr_type] = str(row.iloc[i]).strip()
                    
                    batch_data.append(record_data)
                
                if batch_data:
                    self._bulk_insert_or_update(batch_data)
            
            self.stats['total_records_processed'] += records_processed
            
        except Exception as e:
            # Fallback to row-by-row processing if pandas fails
            for row in query_job:
                records_processed += 1
                
                if not row[0] or not self.is_valid_value(row[0]):
                    continue
                
                normalized_host = self.normalize_hostname(row[0])
                if not normalized_host or normalized_host in table_hostnames_seen:
                    continue
                
                table_hostnames_seen.add(normalized_host)
                
                record_data = {
                    'normalized_host': normalized_host,
                    'hostname': str(row[0]).strip(),
                    'table_name': table_name
                }
                
                for i, attr_type in enumerate(attribute_types, 1):
                    if i < len(row) and self.is_valid_value(row[i]):
                        record_data[attr_type] = str(row[i]).strip()
                
                batch_records.append(record_data)
                
                if len(batch_records) >= batch_size:
                    self._bulk_insert_or_update(batch_records)
                    batch_records.clear()
            
            if batch_records:
                self._bulk_insert_or_update(batch_records)
            
            self.stats['total_records_processed'] += records_processed
        
        return records_processed
    
    def _bulk_insert_or_update(self, records: List[Dict]) -> None:
        """Bulk insert/update using DuckDB's efficient operations"""
        if not records:
            return
        
        # Prepare bulk data
        new_records = []
        update_records = []
        
        # Check existing hosts in batch
        normalized_hosts = [r['normalized_host'] for r in records]
        placeholders = ','.join(['?' for _ in normalized_hosts])
        
        existing_query = f"""
        SELECT normalized_host, source_tables, source_count
        FROM universal_cmdb 
        WHERE normalized_host IN ({placeholders})
        """
        
        existing_hosts = {}
        for row in self.duck_conn.execute(existing_query, normalized_hosts).fetchall():
            existing_hosts[row[0]] = {'source_tables': row[1], 'source_count': row[2]}
        
        for record in records:
            normalized_host = record['normalized_host']
            
            if normalized_host in existing_hosts:
                # Update existing
                existing = existing_hosts[normalized_host]
                table_name = record['table_name']
                
                if table_name not in (existing['source_tables'] or ''):
                    update_records.append(record)
                    self.stats['hosts_updated'] += 1
            else:
                # New record
                new_records.append(record)
                self.stats['hosts_created'] += 1
                self.duplicate_tracker.add(normalized_host)
        
        # Bulk insert new records
        if new_records:
            self._bulk_insert_new(new_records)
        
        # Bulk update existing records
        if update_records:
            self._bulk_update_existing(update_records)
    
    def _bulk_insert_new(self, records: List[Dict]) -> None:
        """Efficient bulk insert for new records"""
        if not records:
            return
        
        # Prepare values for bulk insert
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
        
        # Use DuckDB's efficient bulk insert
        insert_sql = """
        INSERT INTO universal_cmdb (
            normalized_host, source_tables, hostname, fqdn, domain,
            infrastructure_type, region, country, data_center, cloud_region,
            ip_address, class, system_classification, business_unit, apm,
            cio, edr_coverage, tanium_coverage, dlp_agent_coverage,
            logging_in_splunk, logging_in_gso
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.duck_conn.executemany(insert_sql, values_list)
    
    def _bulk_update_existing(self, records: List[Dict]) -> None:
        """Efficient bulk update for existing records"""
        # For simplicity, update one by one (can be optimized further with CASE statements)
        for record in records:
            self._update_single_host(record)
    
    def _update_single_host(self, record: Dict) -> None:
        """Update a single host record"""
        normalized_host = record['normalized_host']
        
        # Get existing data
        existing = self.duck_conn.execute(
            "EXECUTE select_existing($1)", 
            [normalized_host]
        ).fetchone()
        
        if not existing:
            return
        
        updates = []
        values = []
        
        # Update source tables
        current_tables = existing[0] if existing[0] else ""
        table_name = record['table_name']
        
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            
            new_source_count = (existing[2] or 0) + 1
            updates.append("source_count = ?")
            values.append(new_source_count)
        
        # Update other fields
        column_names = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for i, col_name in enumerate(column_names, 3):
            if col_name in record:
                new_value = record[col_name]
                existing_value = existing[i] if i < len(existing) else None
                
                if new_value and new_value != existing_value:
                    updates.append(f"{col_name} = ?")
                    values.append(new_value)
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            self.duck_conn.execute(update_sql, values)
    
    def generate_report(self):
        """Fast report generation"""
        print("\n═══ PROCESSING REPORT ═══\n")
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"Total Unique Hosts: {total_hosts:,}")
        print(f"Tables Processed: {self.stats['tables_processed']}")
        print(f"Records Processed: {self.stats['total_records_processed']:,}")
        print(f"New Hosts Created: {self.stats['hosts_created']:,}")
        print(f"Hosts Updated: {self.stats['hosts_updated']:,}")
        
        if self.stats['processing_errors'] > 0:
            print(f"Processing Errors: {self.stats['processing_errors']}")
        
        print("\nData coverage analysis available in database.\n")
    
    def export_to_parquet(self, filename: str = "universal_cmdb.parquet"):
        """Export to Parquet for faster future processing"""
        print(f"Exporting to {filename}...")
        
        export_query = """
        COPY (
            SELECT * FROM universal_cmdb 
            ORDER BY source_count DESC, normalized_host
        ) TO ? (FORMAT PARQUET, COMPRESSION 'SNAPPY')
        """
        
        self.duck_conn.execute(export_query, [filename])
        print(f"Export complete: {filename}\n")
    
    def process_all_ultra_fast(self):
        """Main processing function with maximum performance"""
        print("\n═══ STARTING ULTRA-FAST PROCESSING ═══\n")
        
        start_time = time.time()
        
        # Load and discover
        metadata = self.load_metadata()
        discovered_columns = self.discover_columns_comprehensive(metadata)
        
        if not discovered_columns:
            print("No processable columns discovered")
            return
        
        # Organize by table
        columns_by_table = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((table_name, column_name, column_type))
        
        # Process tables in parallel
        self.process_tables_parallel(columns_by_table)
        
        # Generate report
        self.generate_report()
        
        # Export to efficient format
        self.export_to_parquet()
        
        total_time = time.time() - start_time
        
        print(f"\n═══ PROCESSING COMPLETE ═══")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Processing Rate: {self.stats['total_records_processed']/max(1, total_time):.0f} records/second\n")
    
    def close_connections(self):
        """Clean up connections"""
        try:
            self.duck_conn.close()
        except:
            pass

if __name__ == "__main__":
    processor = None
    
    try:
        processor = UltraFastCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        processor.process_all_ultra_fast()
        
        print("═══ SUCCESS ═══")
        print("Database: universal_cmdb.db")
        print("Export: universal_cmdb.parquet\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.close_connections()