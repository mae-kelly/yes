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

class AO1DynamicVisibilityProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "ao1_visibility_cmdb.db"):
        print("\n" + "=" * 80)
        print("AO1 LOG VISIBILITY MEASUREMENT - DYNAMIC PROCESSOR")
        print("Requirements-Driven Column Normalization")
        print("Created: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
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
        
        self.all_discovered_columns = set()
        self.column_type_mapping = {}
        self.normalized_column_names = {}
        self.stats = defaultdict(int)
        self.existing_hosts = {}
        
        self._init_bigquery()
        
        self.duck_conn = duckdb.connect(duckdb_path)
        self.duck_conn.execute("PRAGMA threads=8")
        self.duck_conn.execute("PRAGMA memory_limit='8GB'")
        
        print(f"Using {self.max_workers} parallel workers")
        print("\nObjective: Measure visibility across ALL discovered data domains\n")
    
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
    
    def normalize_column_name(self, column_type: str) -> str:
        if not column_type or column_type == 'unknown':
            return None
        
        normalized = column_type.lower().strip()
        normalized = normalized.replace('_', '')
        normalized = normalized.replace('-', '')
        normalized = normalized.replace(' ', '')
        
        normalization_map = {
            'hostname': 'hostname',
            'host': 'hostname',
            'servername': 'hostname',
            'fqdn': 'fqdn',
            'fullyqualifieddomainname': 'fqdn',
            'domain': 'domain',
            'dnsdomain': 'domain',
            'infrastructuretype': 'infrastructure_type',
            'infratype': 'infrastructure_type',
            'region': 'region',
            'location': 'region',
            'country': 'country',
            'nation': 'country',
            'datacenter': 'data_center',
            'datacentre': 'data_center',
            'dc': 'data_center',
            'cloudregion': 'cloud_region',
            'awsregion': 'cloud_region',
            'azureregion': 'cloud_region',
            'ipaddress': 'ip_address',
            'ip': 'ip_address',
            'class': 'class',
            'classification': 'class',
            'systemclassification': 'system_classification',
            'businessunit': 'business_unit',
            'bu': 'business_unit',
            'apm': 'apm',
            'applicationmonitor': 'apm',
            'cio': 'cio',
            'owner': 'cio',
            'edrcoverage': 'edr_coverage',
            'edr': 'edr_coverage',
            'taniumcoverage': 'tanium_coverage',
            'tanium': 'tanium_coverage',
            'dlpagentcoverage': 'dlp_agent_coverage',
            'dlp': 'dlp_agent_coverage',
            'logginginsplunk': 'logging_in_splunk',
            'splunk': 'logging_in_splunk',
            'logingingso': 'logging_in_gso',
            'gso': 'logging_in_gso'
        }
        
        return normalization_map.get(normalized, column_type)
    
    def discover_all_columns(self, metadata: Dict):
        print("Discovering ALL columns across all tables...")
        
        for table_name, columns in metadata.get('columns', {}).items():
            for column_name, column_type in columns.items():
                if column_type and column_type != 'unknown':
                    normalized = self.normalize_column_name(column_type)
                    if normalized:
                        self.all_discovered_columns.add(normalized)
                        self.column_type_mapping[f"{table_name}.{column_name}"] = normalized
                        
                        if normalized not in self.normalized_column_names:
                            self.normalized_column_names[normalized] = []
                        self.normalized_column_names[normalized].append((table_name, column_name))
        
        print(f"Discovered {len(self.all_discovered_columns)} unique normalized column types")
        print(f"Column types found: {', '.join(sorted(self.all_discovered_columns))}\n")
    
    def _create_dynamic_table(self):
        print("Creating dynamic table with ALL discovered columns...")
        
        base_columns = """
            normalized_host VARCHAR PRIMARY KEY,
            source_tables TEXT,
            source_count INTEGER DEFAULT 1,
            visibility_score FLOAT DEFAULT 0.0,
            data_quality_score FLOAT DEFAULT 1.0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
        
        dynamic_columns = []
        for col in sorted(self.all_discovered_columns):
            if col not in ['normalized_host', 'source_tables', 'source_count']:
                dynamic_columns.append(f"{col} TEXT")
        
        dynamic_columns.append("present_in_crowdstrike TEXT")
        dynamic_columns.append("present_in_cmdb TEXT")
        
        all_columns = base_columns + ",\n" + ",\n".join(dynamic_columns)
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            {all_columns}
        )
        """
        
        self.duck_conn.execute(create_sql)
        
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized ON universal_cmdb(normalized_host)")
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_visibility ON universal_cmdb(visibility_score)")
        except:
            pass
        
        print(f"Created table with {len(self.all_discovered_columns) + 10} columns\n")
    
    def _load_existing_hosts(self):
        try:
            columns = ['normalized_host', 'source_tables'] + sorted(list(self.all_discovered_columns)) + ['present_in_crowdstrike', 'present_in_cmdb', 'source_count']
            
            query = f"""
            SELECT {', '.join(columns)}
            FROM universal_cmdb
            """
            
            result = self.duck_conn.execute(query).fetchall()
            
            for row in result:
                self.existing_hosts[row[0]] = {columns[i]: row[i] for i in range(1, len(columns))}
            
            print(f"Loaded {len(self.existing_hosts)} existing hosts\n")
        except Exception as e:
            print(f"No existing hosts loaded: {str(e)[:100]}\n")
    
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
    
    def calculate_visibility_score(self, record: Dict) -> float:
        score = 0.0
        total_possible = 0.0
        
        weights = {
            'hostname': 10,
            'fqdn': 10,
            'domain': 5,
            'ip_address': 10,
            'infrastructure_type': 10,
            'region': 5,
            'country': 5,
            'data_center': 5,
            'cloud_region': 5,
            'business_unit': 10,
            'cio': 5,
            'apm': 5,
            'class': 5,
            'system_classification': 5,
            'logging_in_splunk': 15,
            'logging_in_gso': 10,
            'edr_coverage': 10,
            'tanium_coverage': 5,
            'dlp_agent_coverage': 5,
            'present_in_crowdstrike': 10,
            'present_in_cmdb': 10
        }
        
        for field in self.all_discovered_columns:
            weight = weights.get(field, 2)
            total_possible += weight
            
            if record.get(field) and str(record[field]).strip() not in self.invalid_values:
                score += weight
        
        for special in ['present_in_crowdstrike', 'present_in_cmdb']:
            if special in weights:
                total_possible += weights[special]
                if record.get(special) == 'yes':
                    score += weights[special]
        
        return round((score / max(1, total_possible)) * 100, 2) if total_possible > 0 else 0.0
    
    def load_and_process(self):
        print("Loading metadata and discovering columns...")
        
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        
        self.discover_all_columns(metadata)
        self._create_dynamic_table()
        self._load_existing_hosts()
        
        columns_by_table = defaultdict(list)
        for table_name, columns in metadata.get('columns', {}).items():
            for column_name, column_type in columns.items():
                if column_type and column_type != 'unknown':
                    normalized = self.normalize_column_name(column_type)
                    if normalized:
                        columns_by_table[table_name].append((column_name, column_type, normalized))
        
        print(f"Processing {len(columns_by_table)} tables with normalized columns\n")
        
        return self.process_all_tables(columns_by_table)
    
    def process_all_tables(self, columns_by_table: Dict):
        start_time = time.time()
        
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
        
        total_time = time.time() - start_time
        print(f"\nProcessing complete in {total_time:.2f} seconds")
        return total_time
    
    def process_table_dynamic(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        hostname_cols = [col for col, ctype, norm in table_columns if norm == 'hostname']
        
        if not hostname_cols:
            return 0
        
        primary_hostname = hostname_cols[0]
        all_columns = [col for col, _, _ in table_columns]
        column_mapping = {col: norm for col, _, norm in table_columns}
        
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
            return self.process_results_dynamic(query_job, table_name, all_columns, column_mapping)
            
        except Exception as e:
            raise e
    
    def process_results_dynamic(self, query_job, table_name: str, columns: List[str], column_mapping: Dict) -> int:
        records_processed = 0
        batch_records = []
        batch_size = 5000
        
        special_column = self.special_tables.get(table_name)
        
        results = list(query_job.result(timeout=300))
        
        for row in results:
            records_processed += 1
            
            hostname_idx = None
            for i, col in enumerate(columns):
                if column_mapping.get(col) == 'hostname':
                    hostname_idx = i
                    break
            
            if hostname_idx is None or not row[hostname_idx]:
                continue
            
            normalized_host = self.normalize_hostname_fast(row[hostname_idx])
            if not normalized_host:
                continue
            
            record_data = {
                'normalized_host': normalized_host,
                'table_name': table_name
            }
            
            if special_column:
                record_data[special_column] = 'yes'
            
            for i, col in enumerate(columns):
                if i < len(row) and row[i]:
                    val = str(row[i]).strip()
                    if val.lower() not in self.invalid_values:
                        normalized_col = column_mapping.get(col)
                        if normalized_col:
                            if normalized_col == 'logging_in_splunk' and table_name == 'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG':
                                record_data[normalized_col] = 'yes'
                            else:
                                record_data[normalized_col] = val
            
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
                    self.update_dynamic_host(record)
                else:
                    self.insert_dynamic_host(record)
                    self.existing_hosts[normalized_host] = {}
    
    def insert_dynamic_host(self, record: Dict):
        columns = ['normalized_host', 'source_tables', 'visibility_score']
        values = [record['normalized_host'], record['table_name'], record.get('visibility_score', 0.0)]
        
        for col in self.all_discovered_columns:
            if col in record:
                columns.append(col)
                values.append(record[col])
        
        for special in ['present_in_crowdstrike', 'present_in_cmdb']:
            if special in record:
                columns.append(special)
                values.append(record[special])
        
        placeholders = ', '.join(['?' for _ in values])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            self.duck_conn.execute(insert_sql, values)
            self.stats['hosts_created'] += 1
        except:
            pass
    
    def update_dynamic_host(self, record: Dict):
        updates = []
        values = []
        
        existing = self.existing_hosts.get(record['normalized_host'], {})
        
        current_tables = existing.get('source_tables', '')
        table_name = record['table_name']
        
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            updates.append("source_count = source_count + 1")
        
        if record.get('visibility_score'):
            updates.append("visibility_score = ?")
            values.append(record['visibility_score'])
        
        for col in self.all_discovered_columns:
            if col in record and record[col]:
                new_value = record[col]
                existing_value = existing.get(col)
                
                if col in ['present_in_crowdstrike', 'present_in_cmdb', 'logging_in_splunk', 'logging_in_gso'] and new_value == 'yes':
                    if existing_value != 'yes':
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
            values.append(record['normalized_host'])
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            
            try:
                self.duck_conn.execute(update_sql, values)
                self.stats['hosts_updated'] += 1
            except:
                pass
    
    def generate_dynamic_report(self):
        print("\n" + "=" * 80)
        print("AO1 DYNAMIC VISIBILITY REPORT")
        print("=" * 80)
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"\nTotal Unique Assets: {total_hosts:,}")
        print(f"Tables Processed: {self.stats['tables_processed']}")
        print(f"Records Processed: {self.stats['total_records_processed']:,}")
        
        print("\n--- REQUIREMENTS-BASED VISIBILITY METRICS ---")
        
        print("\n1. Global View - Infrastructure Type Coverage:")
        if 'infrastructure_type' in self.all_discovered_columns:
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
                    print(f"   {row[0]}: {row[1]:,}")
        
        print("\n2. Regional and Country View:")
        for col in ['region', 'country', 'data_center', 'cloud_region']:
            if col in self.all_discovered_columns:
                count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
                count = self.duck_conn.execute(count_query).fetchone()[0]
                print(f"   {col}: {count:,} ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n3. BU and Application View:")
        for col in ['business_unit', 'cio', 'apm', 'class']:
            if col in self.all_discovered_columns:
                count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
                count = self.duck_conn.execute(count_query).fetchone()[0]
                print(f"   {col}: {count:,} ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n4. System Classification:")
        if 'system_classification' in self.all_discovered_columns:
            class_query = """
            SELECT system_classification, COUNT(*) as cnt 
            FROM universal_cmdb 
            WHERE system_classification IS NOT NULL 
            GROUP BY system_classification 
            ORDER BY cnt DESC 
            LIMIT 5
            """
            for row in self.duck_conn.execute(class_query).fetchall():
                if row[0]:
                    print(f"   {row[0]}: {row[1]:,}")
        
        print("\n5. Security Control Coverage:")
        for col in ['edr_coverage', 'tanium_coverage', 'dlp_agent_coverage']:
            if col in self.all_discovered_columns:
                count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
                count = self.duck_conn.execute(count_query).fetchone()[0]
                print(f"   {col}: {count:,} ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n6. Logging Compliance in GSO and Splunk:")
        for col in ['logging_in_gso', 'logging_in_splunk']:
            if col in self.all_discovered_columns:
                count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} = 'yes'"
                count = self.duck_conn.execute(count_query).fetchone()[0]
                print(f"   {col}: {count:,} ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n7. Domain Visibility:")
        for col in ['hostname', 'fqdn', 'domain', 'ip_address']:
            if col in self.all_discovered_columns:
                count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
                count = self.duck_conn.execute(count_query).fetchone()[0]
                print(f"   {col}: {count:,} ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n8. Special Table Coverage:")
        crowdstrike = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_crowdstrike = 'yes'").fetchone()[0]
        cmdb = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_cmdb = 'yes'").fetchone()[0]
        
        print(f"   CrowdStrike (V_DIM_ENDPOINTAGENT): {crowdstrike:,} ({crowdstrike/max(1,total_hosts)*100:.1f}%)")
        print(f"   CMDB (V_DIM_ENDPOINT): {cmdb:,} ({cmdb/max(1,total_hosts)*100:.1f}%)")
        
        print("\n9. Visibility Score Distribution:")
        avg_score = self.duck_conn.execute("SELECT AVG(visibility_score) FROM universal_cmdb").fetchone()[0]
        high = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE visibility_score >= 70").fetchone()[0]
        medium = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE visibility_score >= 40 AND visibility_score < 70").fetchone()[0]
        low = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE visibility_score < 40").fetchone()[0]
        
        print(f"   Average Score: {avg_score:.1f}%")
        print(f"   High (≥70%): {high:,}")
        print(f"   Medium (40-69%): {medium:,}")
        print(f"   Low (<40%): {low:,}")
        
        print("\n10. Column Coverage Summary:")
        print(f"   Total unique column types discovered: {len(self.all_discovered_columns)}")
        print(f"   Columns with data:")
        
        for col in sorted(self.all_discovered_columns):
            count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            count = self.duck_conn.execute(count_query).fetchone()[0]
            if count > 0:
                print(f"      {col}: {count:,} records")
    
    def export_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ao1_dynamic_visibility_{timestamp}.csv"
        
        print(f"\nExporting to {filename}...")
        
        columns = ['normalized_host'] + sorted(list(self.all_discovered_columns)) + ['present_in_crowdstrike', 'present_in_cmdb', 'visibility_score', 'source_count', 'source_tables']
        
        export_query = f"""
        COPY (
            SELECT {', '.join(columns)}
            FROM universal_cmdb 
            ORDER BY visibility_score DESC, source_count DESC
        ) TO '{filename}' (HEADER, DELIMITER ',')
        """
        
        self.duck_conn.execute(export_query)
        print(f"Export complete: {filename}")
    
    def close(self):
        self.duck_conn.close()

if __name__ == "__main__":
    processor = None
    
    try:
        print("\n" + "=" * 80)
        print("AO1 DYNAMIC VISIBILITY MEASUREMENT")
        print("Requirements-Driven Universal Processing")
        print("=" * 80 + "\n")
        
        processor = AO1DynamicVisibilityProcessor("reviewed_labeled_columns.json")
        
        processing_time = processor.load_and_process()
        processor.generate_dynamic_report()
        processor.export_results()
        
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