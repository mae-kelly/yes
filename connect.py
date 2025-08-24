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
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import multiprocessing

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

class UltraFastCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        print("\n" + "=" * 80)
        print("ULTRA-FAST CMDB PROCESSOR")
        print("=" * 80 + "\n")
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.db_lock = threading.Lock()
        self.max_workers = min(8, multiprocessing.cpu_count())
        
        self.normalize_pattern = re.compile(r'[^a-z0-9]')
        self.invalid_values = frozenset(['*undefined', 'null', 'none', 'undefined', ''])
        
        self.special_tables = {
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINTAGENT': 'present_in_crowdstrike',
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINT': 'present_in_cmdb',
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG': 'logging_in_splunk'
        }
        
        self.stats = defaultdict(int)
        self.existing_hosts = {}
        
        self._init_bigquery()
        
        self.duck_conn = duckdb.connect(duckdb_path)
        self.duck_conn.execute("PRAGMA threads=8")
        self.duck_conn.execute("PRAGMA memory_limit='8GB'")
        
        self._create_table()
        self._load_existing_hosts_fast()
        
        print(f"Loaded {len(self.existing_hosts)} existing hosts")
        print(f"Using {self.max_workers} parallel workers\n")
    
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
    
    def _create_table(self):
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
            present_in_crowdstrike TEXT,
            present_in_cmdb TEXT,
            data_quality_score FLOAT DEFAULT 1.0,
            source_count INTEGER DEFAULT 1,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(create_sql)
        
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized ON universal_cmdb(normalized_host, source_count)")
        except:
            pass
    
    def _load_existing_hosts_fast(self):
        try:
            query = """
            SELECT normalized_host, source_tables, hostname, fqdn, domain,
                   infrastructure_type, region, country, data_center, cloud_region,
                   ip_address, class, system_classification, business_unit, apm,
                   cio, edr_coverage, tanium_coverage, dlp_agent_coverage,
                   logging_in_splunk, logging_in_gso, present_in_crowdstrike,
                   present_in_cmdb, source_count
            FROM universal_cmdb
            """
            result = self.duck_conn.execute(query).fetchall()
            
            for row in result:
                self.existing_hosts[row[0]] = list(row[1:])
        except:
            pass
    
    def normalize_hostname_fast(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        normalized = hostname.lower().strip()
        if normalized in self.invalid_values:
            return ""
        if '.' in normalized:
            normalized = normalized.split('.', 1)[0]
        normalized = normalized.replace('-', '')
        normalized = self.normalize_pattern.sub('', normalized)
        return normalized if len(normalized) > 1 else ""
    
    def load_metadata(self) -> Dict:
        print("Loading metadata...")
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        if 'columns' in metadata:
            print(f"Found {len(metadata['columns'])} tables\n")
        return metadata
    
    def discover_columns_fast(self, metadata: Dict) -> Dict:
        print("Organizing columns by table...")
        columns_by_table = defaultdict(list)
        
        for table_name, columns in metadata.get('columns', {}).items():
            for column_name, column_type in columns.items():
                if column_type and column_type != 'unknown':
                    columns_by_table[table_name].append((column_name, column_type))
        
        print(f"Found {len(columns_by_table)} tables with typed columns\n")
        return columns_by_table
    
    def process_all_parallel(self):
        print("Starting parallel CMDB processing...\n")
        start_time = time.time()
        
        metadata = self.load_metadata()
        columns_by_table = self.discover_columns_fast(metadata)
        
        if not columns_by_table:
            print("No processable tables found")
            return
        
        print(f"Processing {len(columns_by_table)} tables in parallel\n")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for table_name, table_columns in columns_by_table.items():
                future = executor.submit(self.process_table_fast, table_name, table_columns)
                futures[future] = table_name
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                table_name = futures[future]
                
                try:
                    records = future.result(timeout=300)
                    print(f"[{completed}/{len(columns_by_table)}] {table_name}: {records:,} records")
                    self.stats['tables_processed'] += 1
                    
                except Exception as e:
                    print(f"[{completed}/{len(columns_by_table)}] {table_name}: ERROR - {str(e)[:100]}")
                    self.stats['processing_errors'] += 1
        
        self.generate_report()
        self.export_csv()
        
        total_time = time.time() - start_time
        print(f"\nProcessing complete in {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
        print(f"Rate: {self.stats['total_records_processed']/max(1, total_time):.0f} records/second")
    
    def process_table_fast(self, table_name: str, table_columns: List[Tuple[str, str]]) -> int:
        hostname_cols = [col for col, ctype in table_columns if ctype == 'hostname']
        
        if not hostname_cols:
            return 0
        
        primary_hostname = hostname_cols[0]
        all_columns = [col for col, _ in table_columns]
        column_types = {col: ctype for col, ctype in table_columns}
        
        query = f"""
        SELECT {', '.join(f'`{col}`' for col in all_columns)}
        FROM `{table_name}`
        WHERE `{primary_hostname}` IS NOT NULL 
        AND `{primary_hostname}` != ''
        AND `{primary_hostname}` != '*Undefined'
        LIMIT 500000
        """
        
        try:
            job_config = bigquery.QueryJobConfig()
            job_config.use_query_cache = True
            
            query_job = self.bq_client.query(query, job_config=job_config)
            return self.process_results_batch(query_job, table_name, all_columns, column_types)
            
        except Exception as e:
            raise e
    
    def process_results_batch(self, query_job, table_name: str, columns: List[str], column_types: Dict) -> int:
        records_processed = 0
        batch_records = []
        batch_size = 5000
        duplicates = 0
        
        special_column = self.special_tables.get(table_name)
        
        results = list(query_job.result(timeout=300))
        
        for row in results:
            records_processed += 1
            
            hostname_idx = None
            for i, col in enumerate(columns):
                if column_types.get(col) == 'hostname':
                    hostname_idx = i
                    break
            
            if hostname_idx is None or not row[hostname_idx]:
                continue
            
            normalized_host = self.normalize_hostname_fast(row[hostname_idx])
            if not normalized_host:
                continue
            
            record_data = {
                'normalized_host': normalized_host,
                'hostname': str(row[hostname_idx]).strip(),
                'table_name': table_name
            }
            
            if special_column:
                record_data[special_column] = 'yes'
            
            for i, col in enumerate(columns):
                if i < len(row) and row[i]:
                    val = str(row[i]).strip().lower()
                    if val not in self.invalid_values:
                        col_type = column_types.get(col)
                        if col_type and col_type != 'hostname':
                            if col_type == 'logging_in_splunk' and table_name == 'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG':
                                record_data[col_type] = 'yes'
                            else:
                                record_data[col_type] = str(row[i]).strip()
            
            batch_records.append(record_data)
            
            if len(batch_records) >= batch_size:
                dups = self.save_batch_fast(batch_records)
                duplicates += dups
                batch_records = []
        
        if batch_records:
            dups = self.save_batch_fast(batch_records)
            duplicates += dups
        
        self.stats['total_records_processed'] += records_processed
        self.stats['duplicate_hosts_found'] += duplicates
        
        return records_processed
    
    def save_batch_fast(self, records: List[Dict]) -> int:
        duplicates = 0
        new_records = []
        update_records = []
        
        with self.db_lock:
            for record in records:
                normalized_host = record['normalized_host']
                
                if normalized_host in self.existing_hosts:
                    duplicates += 1
                    update_records.append(record)
                else:
                    new_records.append(record)
                    self.existing_hosts[normalized_host] = [record['table_name']] + [None] * 22
            
            if new_records:
                self.bulk_insert_fast(new_records)
            
            if update_records:
                self.bulk_update_fast(update_records)
        
        return duplicates
    
    def bulk_insert_fast(self, records: List[Dict]):
        if not records:
            return
        
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
                record.get('logging_in_gso'),
                record.get('present_in_crowdstrike'),
                record.get('present_in_cmdb')
            ]
            values_list.append(values)
        
        insert_sql = """
        INSERT INTO universal_cmdb (
            normalized_host, source_tables, hostname, fqdn, domain,
            infrastructure_type, region, country, data_center, cloud_region,
            ip_address, class, system_classification, business_unit, apm,
            cio, edr_coverage, tanium_coverage, dlp_agent_coverage,
            logging_in_splunk, logging_in_gso, present_in_crowdstrike, present_in_cmdb
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            self.duck_conn.executemany(insert_sql, values_list)
            self.stats['hosts_created'] += len(values_list)
        except:
            for values in values_list:
                try:
                    self.duck_conn.execute(insert_sql, values)
                    self.stats['hosts_created'] += 1
                except:
                    pass
    
    def bulk_update_fast(self, records: List[Dict]):
        for record in records:
            normalized_host = record['normalized_host']
            existing = self.existing_hosts.get(normalized_host)
            
            if not existing:
                continue
            
            updates = []
            values = []
            
            current_tables = existing[0] if existing[0] else ""
            table_name = record['table_name']
            
            if table_name not in current_tables:
                new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
                updates.append("source_tables = ?")
                values.append(new_tables)
                updates.append("source_count = source_count + 1")
                existing[0] = new_tables
            
            attribute_map = {
                'hostname': 1, 'fqdn': 2, 'domain': 3, 'infrastructure_type': 4,
                'region': 5, 'country': 6, 'data_center': 7, 'cloud_region': 8,
                'ip_address': 9, 'class': 10, 'system_classification': 11,
                'business_unit': 12, 'apm': 13, 'cio': 14, 'edr_coverage': 15,
                'tanium_coverage': 16, 'dlp_agent_coverage': 17,
                'logging_in_splunk': 18, 'logging_in_gso': 19,
                'present_in_crowdstrike': 20, 'present_in_cmdb': 21
            }
            
            for col, idx in attribute_map.items():
                if col in record and record[col]:
                    new_value = record[col]
                    
                    if col in ['present_in_crowdstrike', 'present_in_cmdb', 'logging_in_splunk'] and new_value == 'yes':
                        if existing[idx] != 'yes':
                            updates.append(f"{col} = ?")
                            values.append('yes')
                            existing[idx] = 'yes'
                    elif existing[idx] and new_value not in str(existing[idx]):
                        merged = f"{existing[idx]} | {new_value}"
                        updates.append(f"{col} = ?")
                        values.append(merged)
                        existing[idx] = merged
                    elif not existing[idx]:
                        updates.append(f"{col} = ?")
                        values.append(new_value)
                        existing[idx] = new_value
            
            if updates:
                values.append(normalized_host)
                update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
                
                try:
                    self.duck_conn.execute(update_sql, values)
                    self.stats['hosts_updated'] += 1
                except:
                    pass
    
    def generate_report(self):
        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"\nTotal unique hosts: {total_hosts:,}")
        print(f"Tables processed: {self.stats['tables_processed']}")
        print(f"Records processed: {self.stats['total_records_processed']:,}")
        print(f"New hosts created: {self.stats['hosts_created']:,}")
        print(f"Existing hosts updated: {self.stats['hosts_updated']:,}")
        print(f"Duplicate hosts merged: {self.stats['duplicate_hosts_found']:,}")
        
        print("\nSpecial coverage:")
        
        crowdstrike = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_crowdstrike = 'yes'").fetchone()[0]
        cmdb = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_cmdb = 'yes'").fetchone()[0]
        splunk = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_splunk = 'yes'").fetchone()[0]
        
        print(f"  Hosts in CrowdStrike: {crowdstrike:,}")
        print(f"  Hosts in CMDB: {cmdb:,}")
        print(f"  Hosts logging to Splunk: {splunk:,}")
    
    def export_csv(self, filename: str = "universal_cmdb_export.csv"):
        print(f"\nExporting to {filename}...")
        
        export_query = f"""
        COPY (
            SELECT * FROM universal_cmdb 
            ORDER BY source_count DESC, normalized_host
        ) TO '{filename}' (HEADER, DELIMITER ',')
        """
        
        self.duck_conn.execute(export_query)
        print(f"Export complete: {filename}")
    
    def close(self):
        self.duck_conn.close()

if __name__ == "__main__":
    processor = None
    
    try:
        processor = UltraFastCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        processor.process_all_parallel()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.close()