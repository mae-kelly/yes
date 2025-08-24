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
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

class AO1DynamicProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "ao1_universal_cmdb.db"):
        print("\n" + "=" * 80)
        print("AO1 LOG VISIBILITY MEASUREMENT - DYNAMIC CMDB PROCESSOR")
        print("Objective: Measure visibility across ALL critical logging domains")
        print("Processing ALL columns dynamically from metadata")
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
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG': 'present_in_splunk_log'
        }
        
        self.all_columns = set()
        self.column_type_mapping = {}
        self.stats = defaultdict(int)
        self.existing_hosts = {}
        
        self._init_bigquery()
        
        self.duck_conn = duckdb.connect(duckdb_path)
        self.duck_conn.execute("PRAGMA threads=8")
        self.duck_conn.execute("PRAGMA memory_limit='8GB'")
        
        print(f"Using {self.max_workers} parallel workers")
        print("Discovering all unique columns from metadata...\n")
    
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
    
    def discover_all_columns(self, metadata: Dict):
        print("Discovering ALL unique columns across all tables...")
        
        for table_name, columns in metadata.get('columns', {}).items():
            for column_name, column_type in columns.items():
                if column_type and column_type != 'unknown':
                    normalized_type = self.normalize_column_type(column_type)
                    self.all_columns.add(normalized_type)
                    
                    if column_type not in self.column_type_mapping:
                        self.column_type_mapping[column_type] = normalized_type
        
        self.all_columns.add('normalized_host')
        self.all_columns.add('source_tables')
        self.all_columns.add('source_count')
        self.all_columns.add('visibility_score')
        self.all_columns.add('present_in_crowdstrike')
        self.all_columns.add('present_in_cmdb')
        self.all_columns.add('present_in_splunk_log')
        self.all_columns.add('first_seen')
        self.all_columns.add('last_updated')
        
        print(f"Discovered {len(self.all_columns)} unique column types")
        print(f"Column types found: {', '.join(sorted(self.all_columns)[:20])}")
        if len(self.all_columns) > 20:
            print(f"... and {len(self.all_columns) - 20} more columns")
        print()
    
    def normalize_column_type(self, column_type: str) -> str:
        if not column_type:
            return 'unknown'
        
        normalized = column_type.lower().strip()
        normalized = normalized.replace(' ', '_')
        normalized = normalized.replace('-', '_')
        normalized = re.sub(r'[^a-z0-9_]', '', normalized)
        
        if normalized.startswith(tuple('0123456789')):
            normalized = 'col_' + normalized
        
        return normalized if normalized else 'unknown'
    
    def create_dynamic_table(self):
        print("Creating dynamic table with ALL discovered columns...")
        
        column_definitions = [
            "normalized_host VARCHAR PRIMARY KEY",
            "source_tables TEXT",
            "source_count INTEGER DEFAULT 1",
            "visibility_score FLOAT DEFAULT 0.0",
            "present_in_crowdstrike TEXT",
            "present_in_cmdb TEXT",
            "present_in_splunk_log TEXT",
            "first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ]
        
        for col in sorted(self.all_columns):
            if col not in ['normalized_host', 'source_tables', 'source_count', 'visibility_score', 
                          'present_in_crowdstrike', 'present_in_cmdb', 'present_in_splunk_log',
                          'first_seen', 'last_updated']:
                column_definitions.append(f"{col} TEXT")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            {', '.join(column_definitions)}
        )
        """
        
        try:
            self.duck_conn.execute("DROP TABLE IF EXISTS universal_cmdb")
            self.duck_conn.execute(create_sql)
            print(f"Created table with {len(column_definitions)} columns")
            
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized ON universal_cmdb(normalized_host)")
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_visibility ON universal_cmdb(visibility_score)")
            
        except Exception as e:
            print(f"Error creating table: {e}")
    
    def load_existing_hosts(self):
        try:
            columns_str = ', '.join(sorted(self.all_columns))
            query = f"SELECT {columns_str} FROM universal_cmdb"
            result = self.duck_conn.execute(query).fetchall()
            
            for row in result:
                self.existing_hosts[row[0]] = {col: row[i] for i, col in enumerate(sorted(self.all_columns))}
            
            print(f"Loaded {len(self.existing_hosts)} existing hosts")
        except:
            print("No existing hosts found (new database)")
    
    def normalize_hostname(self, hostname: str) -> str:
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
    
    def calculate_visibility_score(self, record: Dict) -> float:
        score = 0.0
        total_fields = 0
        populated_fields = 0
        
        critical_fields = {
            'hostname': 10,
            'fqdn': 10,
            'ip_address': 10,
            'domain': 5,
            'infrastructure_type': 10,
            'region': 5,
            'country': 5,
            'business_unit': 10,
            'logging_in_splunk': 15,
            'logging_in_gso': 10,
            'present_in_crowdstrike': 10,
            'present_in_cmdb': 10
        }
        
        for field in record:
            total_fields += 1
            if record.get(field) and str(record[field]).strip() not in self.invalid_values:
                populated_fields += 1
                
                for critical_field, weight in critical_fields.items():
                    if critical_field in field.lower():
                        score += weight
                        break
        
        data_completeness = (populated_fields / max(1, total_fields)) * 50
        critical_score = min(50, score / 2)
        
        return round(data_completeness + critical_score, 2)
    
    def load_metadata(self) -> Dict:
        print("Loading metadata...")
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        if 'columns' in metadata:
            print(f"Found {len(metadata['columns'])} tables\n")
        return metadata
    
    def process_all_parallel(self):
        print("Starting AO1 Dynamic Processing...\n")
        start_time = time.time()
        
        metadata = self.load_metadata()
        
        self.discover_all_columns(metadata)
        self.create_dynamic_table()
        self.load_existing_hosts()
        
        columns_by_table = self.organize_columns_by_table(metadata)
        
        if not columns_by_table:
            print("No processable tables found")
            return
        
        print(f"\nProcessing {len(columns_by_table)} tables in parallel\n")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for table_name, table_columns in columns_by_table.items():
                future = executor.submit(self.process_table_dynamic, table_name, table_columns)
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
        
        self.generate_ao1_report()
        self.export_visibility_data()
        
        total_time = time.time() - start_time
        print(f"\nProcessing complete in {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
        print(f"Rate: {self.stats['total_records_processed']/max(1, total_time):.0f} records/second")
    
    def organize_columns_by_table(self, metadata: Dict) -> Dict:
        columns_by_table = defaultdict(list)
        
        for table_name, columns in metadata.get('columns', {}).items():
            for column_name, column_type in columns.items():
                if column_type and column_type != 'unknown':
                    columns_by_table[table_name].append((column_name, column_type))
        
        return columns_by_table
    
    def process_table_dynamic(self, table_name: str, table_columns: List[Tuple[str, str]]) -> int:
        hostname_cols = []
        all_cols = []
        col_type_map = {}
        
        for col_name, col_type in table_columns:
            all_cols.append(col_name)
            normalized_type = self.normalize_column_type(col_type)
            col_type_map[col_name] = normalized_type
            
            if col_type == 'hostname':
                hostname_cols.append(col_name)
        
        if not hostname_cols:
            return 0
        
        primary_hostname = hostname_cols[0]
        
        query = f"""
        SELECT {', '.join(f'`{col}`' for col in all_cols)}
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
            return self.process_results_dynamic(query_job, table_name, all_cols, col_type_map, primary_hostname)
            
        except Exception as e:
            raise e
    
    def process_results_dynamic(self, query_job, table_name: str, columns: List[str], 
                                col_type_map: Dict, primary_hostname: str) -> int:
        records_processed = 0
        batch_records = []
        batch_size = 5000
        
        special_column = self.special_tables.get(table_name)
        
        try:
            results = list(query_job.result(timeout=300))
        except:
            return 0
        
        for row in results:
            records_processed += 1
            
            hostname_idx = columns.index(primary_hostname)
            if not row[hostname_idx]:
                continue
            
            normalized_host = self.normalize_hostname(row[hostname_idx])
            if not normalized_host:
                continue
            
            record_data = {
                'normalized_host': normalized_host,
                'table_name': table_name
            }
            
            if special_column:
                record_data[special_column] = 'yes'
            
            for i, col_name in enumerate(columns):
                if i < len(row) and row[i]:
                    val = str(row[i]).strip()
                    if val.lower() not in self.invalid_values:
                        normalized_col_type = col_type_map.get(col_name, 'unknown')
                        record_data[normalized_col_type] = val
            
            record_data['visibility_score'] = self.calculate_visibility_score(record_data)
            
            batch_records.append(record_data)
            
            if len(batch_records) >= batch_size:
                self.save_batch_dynamic(batch_records)
                batch_records = []
        
        if batch_records:
            self.save_batch_dynamic(batch_records)
        
        self.stats['total_records_processed'] += records_processed
        
        return records_processed
    
    def save_batch_dynamic(self, records: List[Dict]):
        with self.db_lock:
            for record in records:
                normalized_host = record['normalized_host']
                
                if normalized_host in self.existing_hosts:
                    self.update_host_dynamic(record)
                else:
                    self.insert_host_dynamic(record)
                    self.existing_hosts[normalized_host] = record
    
    def insert_host_dynamic(self, record: Dict):
        columns = []
        values = []
        
        for col in record:
            if col in self.all_columns:
                columns.append(col)
                values.append(record[col])
        
        if 'source_tables' not in columns:
            columns.append('source_tables')
            values.append(record.get('table_name', ''))
        
        placeholders = ', '.join(['?' for _ in values])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            self.duck_conn.execute(insert_sql, values)
            self.stats['hosts_created'] += 1
        except:
            pass
    
    def update_host_dynamic(self, record: Dict):
        normalized_host = record['normalized_host']
        existing = self.existing_hosts.get(normalized_host, {})
        
        updates = []
        values = []
        
        current_tables = existing.get('source_tables', '')
        table_name = record.get('table_name', '')
        
        if table_name and table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            updates.append("source_count = source_count + 1")
        
        for col in record:
            if col in self.all_columns and col not in ['normalized_host', 'source_tables', 'source_count']:
                new_value = record[col]
                existing_value = existing.get(col)
                
                if col in ['present_in_crowdstrike', 'present_in_cmdb', 'present_in_splunk_log']:
                    if new_value == 'yes' and existing_value != 'yes':
                        updates.append(f"{col} = ?")
                        values.append('yes')
                elif existing_value and new_value not in str(existing_value):
                    merged = f"{existing_value} | {new_value}"
                    updates.append(f"{col} = ?")
                    values.append(merged)
                elif not existing_value:
                    updates.append(f"{col} = ?")
                    values.append(new_value)
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            
            try:
                self.duck_conn.execute(update_sql, values)
                self.stats['hosts_updated'] += 1
            except:
                pass
    
    def generate_ao1_report(self):
        print("\n" + "=" * 80)
        print("AO1 LOG VISIBILITY MEASUREMENT REPORT")
        print("Requirements Section Analysis")
        print("=" * 80)
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"\nTotal Unique Assets: {total_hosts:,}")
        print(f"Tables Processed: {self.stats['tables_processed']}")
        print(f"Records Processed: {self.stats['total_records_processed']:,}")
        
        print("\n--- REQUIREMENTS VISIBILITY METRICS ---")
        
        print("\n1. GLOBAL VIEW - CSOC Visibility (x% of all assets globally):")
        
        for col in ['hostname', 'fqdn', 'ip_address', 'domain']:
            if col in self.all_columns:
                count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
                print(f"   {col}: {count:,} hosts ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n2. INFRASTRUCTURE TYPE - CSOC Display (% visibility by type):")
        
        if 'infrastructure_type' in self.all_columns:
            infra_query = """
            SELECT infrastructure_type, COUNT(*) as cnt 
            FROM universal_cmdb 
            WHERE infrastructure_type IS NOT NULL 
            GROUP BY infrastructure_type 
            ORDER BY cnt DESC 
            LIMIT 10
            """
            for row in self.duck_conn.execute(infra_query).fetchall():
                if row[0]:
                    print(f"   {row[0]}: {row[1]:,} hosts")
        
        cloud_cols = [col for col in self.all_columns if 'cloud' in col.lower()]
        onprem_cols = [col for col in self.all_columns if 'prem' in col.lower()]
        saas_cols = [col for col in self.all_columns if 'saas' in col.lower() or 'application' in col.lower()]
        api_cols = [col for col in self.all_columns if 'api' in col.lower()]
        
        print(f"   Cloud-related columns: {len(cloud_cols)}")
        print(f"   On-Premise columns: {len(onprem_cols)}")
        print(f"   SaaS/Application columns: {len(saas_cols)}")
        print(f"   API columns: {len(api_cols)}")
        
        print("\n3. REGIONAL AND COUNTRY VIEW - Visibility by location:")
        
        for col in ['region', 'country', 'data_center', 'cloud_region']:
            if col in self.all_columns:
                count = self.duck_conn.execute(f"SELECT COUNT(DISTINCT {col}) FROM universal_cmdb WHERE {col} IS NOT NULL").fetchone()[0]
                total = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL").fetchone()[0]
                print(f"   {col}: {count} unique values, {total:,} hosts covered")
        
        print("\n4. BU AND APPLICATION VIEW:")
        
        for col in ['business_unit', 'cio', 'apm', 'application_class']:
            if col in self.all_columns:
                count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
                print(f"   {col}: {count:,} hosts ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n5. SYSTEM CLASSIFICATION:")
        
        server_cols = [col for col in self.all_columns if 'server' in col.lower()]
        windows_cols = [col for col in self.all_columns if 'windows' in col.lower()]
        linux_cols = [col for col in self.all_columns if 'linux' in col.lower() or 'unix' in col.lower()]
        mainframe_cols = [col for col in self.all_columns if 'mainframe' in col.lower()]
        database_cols = [col for col in self.all_columns if 'database' in col.lower() or 'db' in col.lower()]
        network_cols = [col for col in self.all_columns if 'network' in col.lower() or 'appliance' in col.lower()]
        
        print(f"   Web Server columns: {len(server_cols)}")
        print(f"   Windows Server columns: {len(windows_cols)}")
        print(f"   Linux Server columns: {len(linux_cols)}")
        print(f"   Mainframe columns: {len(mainframe_cols)}")
        print(f"   Database columns: {len(database_cols)}")
        print(f"   Network Appliance columns: {len(network_cols)}")
        
        print("\n6. SECURITY CONTROL COVERAGE - Agent based:")
        
        for col in ['edr_coverage', 'tanium_coverage', 'dlp_agent_coverage']:
            if col in self.all_columns:
                count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
                print(f"   {col}: {count:,} hosts ({count/max(1,total_hosts)*100:.1f}%)")
        
        crowdstrike = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_crowdstrike = 'yes'").fetchone()[0]
        print(f"   CrowdStrike (Axonius/Console): {crowdstrike:,} hosts ({crowdstrike/max(1,total_hosts)*100:.1f}%)")
        
        print("\n7. LOGGING COMPLIANCE IN GSO AND SPLUNK - Ensure:")
        
        for col in ['logging_in_gso', 'logging_in_splunk']:
            if col in self.all_columns:
                count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
                print(f"   {col}: {count:,} hosts ({count/max(1,total_hosts)*100:.1f}%)")
        
        splunk_log = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_splunk_log = 'yes'").fetchone()[0]
        print(f"   Present in Splunk Log Table: {splunk_log:,} hosts")
        
        print("\n8. DOMAIN VISIBILITY:")
        
        if 'domain' in self.all_columns:
            domain_count = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE domain IS NOT NULL AND domain != ''").fetchone()[0]
            unique_domains = self.duck_conn.execute("SELECT COUNT(DISTINCT domain) FROM universal_cmdb WHERE domain IS NOT NULL").fetchone()[0]
            print(f"   Asset visibility by domain: {domain_count:,} hosts")
            print(f"   Unique domains: {unique_domains}")
        
        print("\n9. VISIBILITY SCORE ANALYSIS:")
        
        avg_score = self.duck_conn.execute("SELECT AVG(visibility_score) FROM universal_cmdb").fetchone()[0]
        high = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE visibility_score >= 70").fetchone()[0]
        medium = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE visibility_score >= 40 AND visibility_score < 70").fetchone()[0]
        low = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE visibility_score < 40").fetchone()[0]
        
        print(f"   Average Visibility Score: {avg_score:.1f}%")
        print(f"   High Visibility (≥70%): {high:,} hosts")
        print(f"   Medium Visibility (40-69%): {medium:,} hosts") 
        print(f"   Low Visibility (<40%): {low:,} hosts")
        
        print("\n10. DATA QUALITY METRICS:")
        
        print(f"   Total unique columns discovered: {len(self.all_columns)}")
        print(f"   New hosts created: {self.stats['hosts_created']:,}")
        print(f"   Existing hosts updated: {self.stats['hosts_updated']:,}")
        
        empty_cols = []
        populated_cols = []
        
        for col in self.all_columns:
            if col not in ['first_seen', 'last_updated']:
                count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
                if count == 0:
                    empty_cols.append(col)
                else:
                    populated_cols.append((col, count))
        
        print(f"   Columns with data: {len(populated_cols)}")
        print(f"   Empty columns: {len(empty_cols)}")
        
        print("\nASSUMPTIONS (per AO1 requirements):")
        print("  ✓ CMDB is accurate and complete")
        print("  ✓ CMDB incorporates asset inventory from Asset Management")
        print("  ✓ CMDB incorporates all discovery scanning")
        print("  ✓ CMDB incorporates DHCP records for IP mapping")
        print("  ✓ CMDB integrates Vulnerability Scanning")
        print("  ✓ CMDB incorporates Cloud Hosting controls")
        print("  ✓ CMDB incorporates external discovery services")
    
    def export_visibility_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"ao1_dynamic_visibility_{timestamp}.csv"
        print(f"\nExporting ALL columns to {filename}...")
        
        columns_str = ', '.join(sorted(self.all_columns))
        
        export_query = f"""
        COPY (
            SELECT {columns_str}
            FROM universal_cmdb 
            ORDER BY visibility_score DESC, source_count DESC, normalized_host
        ) TO '{filename}' (HEADER, DELIMITER ',')
        """
        
        self.duck_conn.execute(export_query)
        print(f"Export complete: {filename}")
        
        print(f"\nExported {len(self.all_columns)} columns including all dynamically discovered fields")
    
    def close(self):
        self.duck_conn.close()

if __name__ == "__main__":
    processor = None
    
    try:
        print("\n" + "=" * 80)
        print("AO1 DYNAMIC LOG VISIBILITY MEASUREMENT")
        print("Processing ALL columns from metadata")
        print("=" * 80 + "\n")
        
        processor = AO1DynamicProcessor("reviewed_labeled_columns.json", "ao1_universal_cmdb.db")
        processor.process_all_parallel()
        
        print("\n" + "=" * 80)
        print("DYNAMIC VISIBILITY MEASUREMENT COMPLETE")
        print("=" * 80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.close()