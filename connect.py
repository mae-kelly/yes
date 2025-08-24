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

class AO1CompleteProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "ao1_complete_cmdb.db"):
        print("\n" + "=" * 80)
        print("AO1 COMPLETE PROCESSOR WITH DYNAMIC NORMALIZATION")
        print("Objective: Process all data and dynamically normalize")
        print("Created: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
        print("=" * 80 + "\n")
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.db_lock = threading.Lock()
        self.max_workers = min(8, multiprocessing.cpu_count())
        
        self.normalize_pattern = re.compile(r'[^a-z0-9]')
        self.invalid_values = frozenset(['*undefined', 'null', 'none', 'undefined', ''])
        
        # Column mapping from original processor
        self.column_mapping = {
            'fqdn': 'fqdn', 'domain': 'domain', 'host': 'hostname',
            'hostname': 'hostname', 'infrastructure_type': 'infrastructure_type',
            'infra_type': 'infrastructure_type', 'region': 'region',
            'country': 'country', 'data_center': 'data_center',
            'datacenter': 'data_center', 'cloud_region': 'cloud_region',
            'ip_address': 'ip_address', 'ip': 'ip_address', 'class': 'class',
            'system_classification': 'system_classification',
            'business_unit': 'business_unit', 'bu': 'business_unit',
            'apm': 'apm', 'cio': 'cio', 'edr_coverage': 'edr_coverage',
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
            'business_unit': ['business_unit', 'bu', 'business', 'department', 'division', 'org_unit'],
            'region': ['region', 'location', 'site', 'area', 'zone', 'geographic_region'],
            'country': ['country', 'nation', 'country_code', 'geo_country'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type', 'system_type', 'platform', 'environment', 'env'],
            'data_center': ['datacenter', 'data_center', 'dc', 'facility', 'center'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip'],
            'class': ['class', 'classification', 'tier', 'level'],
            'system_classification': ['system_classification', 'security_classification'],
            'apm': ['apm', 'monitoring', 'application_monitoring'],
            'cio': ['cio', 'owner', 'responsible', 'contact'],
            'edr_coverage': ['edr_coverage', 'edr', 'endpoint_detection'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'tanium_agent'],
            'dlp_agent_coverage': ['dlp_agent_coverage', 'dlp', 'data_loss_prevention'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk', 'splunk_logging'],
            'logging_in_gso': ['logging_in_gso', 'gso', 'gso_logging'],
            'domain': ['domain', 'dns_domain', 'ad_domain'],
            'fqdn': ['fqdn', 'full_name', 'qualified_name']
        }
        
        self.special_tables = {
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINTAGENT': 'present_in_crowdstrike',
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINT': 'present_in_cmdb',
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG': 'logging_in_splunk'
        }
        
        # Dynamic value tracking
        self.unique_values = defaultdict(lambda: defaultdict(int))
        self.normalized_groups = defaultdict(lambda: defaultdict(set))
        
        self.stats = defaultdict(int)
        self.existing_hosts = {}
        
        self._init_bigquery()
        
        self.duck_conn = duckdb.connect(duckdb_path)
        self.duck_conn.execute("PRAGMA threads=8")
        self.duck_conn.execute("PRAGMA memory_limit='8GB'")
        
        self._create_table()
        self._load_existing_hosts()
        
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
            infrastructure_type_normalized TEXT,
            region TEXT,
            region_normalized TEXT,
            country TEXT,
            country_normalized TEXT,
            data_center TEXT,
            cloud_region TEXT,
            ip_address TEXT,
            class TEXT,
            class_normalized TEXT,
            system_classification TEXT,
            system_classification_normalized TEXT,
            business_unit TEXT,
            business_unit_normalized TEXT,
            apm TEXT,
            cio TEXT,
            edr_coverage TEXT,
            tanium_coverage TEXT,
            dlp_agent_coverage TEXT,
            logging_in_splunk TEXT,
            logging_in_gso TEXT,
            present_in_crowdstrike TEXT,
            present_in_cmdb TEXT,
            visibility_score FLOAT DEFAULT 0.0,
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
    
    def _load_existing_hosts(self):
        try:
            query = """
            SELECT normalized_host, source_tables, source_count
            FROM universal_cmdb
            """
            result = self.duck_conn.execute(query).fetchall()
            
            for row in result:
                self.existing_hosts[row[0]] = {
                    'source_tables': row[1],
                    'source_count': row[2]
                }
        except:
            pass
    
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str) or hostname.strip() == '*Undefined':
            return ""
        normalized = hostname.lower().strip()
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        normalized = normalized.replace('-', '')
        normalized = self.normalize_pattern.sub('', normalized)
        return normalized if len(normalized) > 1 else ""
    
    def is_valid_value(self, value) -> bool:
        if not value:
            return False
        if isinstance(value, str):
            stripped = value.strip()
            return stripped != '' and stripped != '*Undefined' and stripped.lower() not in ['null', 'none', 'undefined']
        return True
    
    def identify_column_type(self, column_name: str, column_type) -> Optional[str]:
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
    
    def normalize_value_dynamic(self, value: str, column_type: str) -> str:
        """Dynamically normalize based on patterns found in data"""
        if not value or not isinstance(value, str):
            return "unknown"
        
        normalized = value.lower().strip()
        
        if column_type == 'infrastructure_type':
            if any(term in normalized for term in ['cloud', 'aws', 'azure', 'gcp', 'ec2']):
                return "cloud"
            elif any(term in normalized for term in ['prem', 'onprem', 'datacenter']):
                return "on_premise"
            elif any(term in normalized for term in ['saas', 'application']):
                return "saas"
            elif any(term in normalized for term in ['api', 'endpoint']):
                return "api"
            else:
                return re.sub(r'[^a-z0-9_]', '_', normalized)[:30]
        
        elif column_type in ['system_classification', 'class']:
            if any(term in normalized for term in ['web', 'apache', 'nginx', 'iis']):
                return "web_server"
            elif any(term in normalized for term in ['windows', 'win', 'microsoft']):
                return "windows_server"
            elif any(term in normalized for term in ['linux', 'unix', 'ubuntu', 'redhat']):
                return "linux_server"
            elif any(term in normalized for term in ['database', 'db', 'oracle', 'sql']):
                return "database"
            elif any(term in normalized for term in ['network', 'firewall', 'router']):
                return "network_device"
            else:
                return re.sub(r'[^a-z0-9_]', '_', normalized)[:30]
        
        else:
            # Generic normalization
            return re.sub(r'[^a-z0-9_]', '_', normalized)[:30]
    
    def load_metadata(self) -> Dict:
        print("Loading metadata...")
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        if 'columns' in metadata:
            print(f"Found {len(metadata['columns'])} tables\n")
        return metadata
    
    def discover_columns(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        print("Discovering columns...")
        discovered = []
        
        for table_name, columns in metadata.get('columns', {}).items():
            for column_name, column_type in columns.items():
                mapped_type = self.identify_column_type(column_name, column_type)
                if mapped_type:
                    discovered.append((table_name, column_name, mapped_type))
        
        print(f"Discovered {len(discovered)} relevant columns\n")
        return discovered
    
    def process_all_parallel(self):
        print("Starting processing...\n")
        start_time = time.time()
        
        metadata = self.load_metadata()
        discovered_columns = self.discover_columns(metadata)
        
        if not discovered_columns:
            print("No processable columns found")
            return
        
        columns_by_table = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((table_name, column_name, column_type))
        
        print(f"Processing {len(columns_by_table)} tables\n")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for table_name, table_columns in columns_by_table.items():
                future = executor.submit(self.process_table, table_name, table_columns)
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
        self.export_data()
        
        total_time = time.time() - start_time
        print(f"\nProcessing complete in {total_time:.2f} seconds")
    
    def process_table(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            return 0
        
        primary_hostname_col = hostname_cols[0][0]
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        query = f"""
        SELECT {', '.join(f'`{col}`' for col in all_columns)}
        FROM `{table_name}`
        WHERE `{primary_hostname_col}` IS NOT NULL 
        AND `{primary_hostname_col}` != ''
        AND `{primary_hostname_col}` != '*Undefined'
        LIMIT 500000
        """
        
        try:
            query_job = self.bq_client.query(query)
            return self.process_results(query_job, table_name, attribute_types)
        except Exception as e:
            raise e
    
    def process_results(self, query_job, table_name: str, attribute_types: List[str]) -> int:
        records_processed = 0
        batch_records = []
        batch_size = 5000
        
        special_column = self.special_tables.get(table_name)
        
        for row in query_job:
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
            
            if special_column:
                record_data[special_column] = 'yes'
            
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and self.is_valid_value(row[i]):
                    val = str(row[i]).strip()
                    record_data[attr_type] = val
                    
                    # Track unique values
                    self.unique_values[attr_type][val] += 1
                    
                    # Add normalized version for key fields
                    if attr_type in ['infrastructure_type', 'system_classification', 'class', 
                                    'region', 'country', 'business_unit']:
                        normalized_val = self.normalize_value_dynamic(val, attr_type)
                        record_data[f"{attr_type}_normalized"] = normalized_val
                        self.normalized_groups[attr_type][normalized_val].add(val)
            
            if table_name == 'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG':
                record_data['logging_in_splunk'] = 'yes'
            
            batch_records.append(record_data)
            
            if len(batch_records) >= batch_size:
                self.save_batch(batch_records)
                batch_records = []
        
        if batch_records:
            self.save_batch(batch_records)
        
        self.stats['total_records_processed'] += records_processed
        return records_processed
    
    def save_batch(self, records: List[Dict]):
        with self.db_lock:
            for record in records:
                normalized_host = record['normalized_host']
                
                if normalized_host in self.existing_hosts:
                    self.update_host(normalized_host, record)
                else:
                    self.insert_host(record)
                    self.existing_hosts[normalized_host] = {
                        'source_tables': record['table_name'],
                        'source_count': 1
                    }
    
    def insert_host(self, record: Dict):
        columns = ['normalized_host', 'source_tables', 'source_count']
        values = [record['normalized_host'], record['table_name'], 1]
        
        all_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'infrastructure_type_normalized',
            'region', 'region_normalized', 'country', 'country_normalized',
            'data_center', 'cloud_region', 'ip_address', 'class', 'class_normalized',
            'system_classification', 'system_classification_normalized',
            'business_unit', 'business_unit_normalized', 'apm', 'cio',
            'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage',
            'logging_in_splunk', 'logging_in_gso', 'present_in_crowdstrike', 'present_in_cmdb'
        ]
        
        for col in all_columns:
            if col in record and record[col]:
                columns.append(col)
                values.append(record[col])
        
        placeholders = ', '.join(['?' for _ in values])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            self.duck_conn.execute(insert_sql, values)
            self.stats['hosts_created'] += 1
        except Exception as e:
            if "duplicate" not in str(e).lower():
                logger.debug(f"Insert error: {e}")
    
    def update_host(self, normalized_host: str, record: Dict):
        existing = self.existing_hosts[normalized_host]
        updates = []
        values = []
        
        current_tables = existing.get('source_tables', '')
        table_name = record['table_name']
        
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            updates.append("source_count = source_count + 1")
            existing['source_tables'] = new_tables
        
        update_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'infrastructure_type_normalized',
            'region', 'region_normalized', 'country', 'country_normalized',
            'data_center', 'cloud_region', 'ip_address', 'class', 'class_normalized',
            'system_classification', 'system_classification_normalized',
            'business_unit', 'business_unit_normalized', 'apm', 'cio',
            'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage',
            'logging_in_splunk', 'logging_in_gso', 'present_in_crowdstrike', 'present_in_cmdb'
        ]
        
        for col in update_columns:
            if col in record and record[col]:
                if col in ['present_in_crowdstrike', 'present_in_cmdb', 'logging_in_splunk', 'logging_in_gso']:
                    if record[col] == 'yes':
                        updates.append(f"{col} = ?")
                        values.append('yes')
                else:
                    updates.append(f"{col} = COALESCE({col}, ?)")
                    values.append(record[col])
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            
            try:
                self.duck_conn.execute(update_sql, values)
                self.stats['hosts_updated'] += 1
            except Exception as e:
                logger.debug(f"Update error: {e}")
    
    def generate_report(self):
        print("\n" + "=" * 80)
        print("AO1 REQUIREMENTS REPORT WITH DYNAMIC NORMALIZATION")
        print("=" * 80)
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"\nTotal Unique Hosts: {total_hosts:,}")
        print(f"Tables Processed: {self.stats['tables_processed']}")
        print(f"Records Processed: {self.stats['total_records_processed']:,}")
        print(f"New Hosts Created: {self.stats['hosts_created']:,}")
        print(f"Hosts Updated: {self.stats['hosts_updated']:,}")
        
        # Show dynamic values discovered
        print("\n" + "=" * 80)
        print("DYNAMIC VALUES DISCOVERED")
        print("=" * 80)
        
        for col_type in sorted(self.unique_values.keys()):
            unique_count = len(self.unique_values[col_type])
            print(f"\n{col_type.upper()}:")
            print(f"  Unique values found: {unique_count}")
            
            if col_type in self.normalized_groups:
                print(f"  Normalized groups: {len(self.normalized_groups[col_type])}")
                print("  Top normalized groups:")
                for norm_val, raw_vals in sorted(self.normalized_groups[col_type].items(), 
                                                key=lambda x: len(x[1]), reverse=True)[:5]:
                    print(f"    {norm_val}: {len(raw_vals)} values")
            
            print("  Top 5 raw values:")
            for val, count in sorted(self.unique_values[col_type].items(), 
                                    key=lambda x: x[1], reverse=True)[:5]:
                print(f"    {val}: {count:,}")
        
        # Requirements metrics
        print("\n" + "=" * 80)
        print("REQUIREMENTS METRICS")
        print("=" * 80)
        
        print("\n1. GLOBAL VIEW:")
        for col in ['hostname', 'fqdn', 'ip_address', 'domain']:
            count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL").fetchone()[0]
            print(f"  {col}: {count:,} ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n2. INFRASTRUCTURE TYPE:")
        infra_query = """
        SELECT infrastructure_type_normalized, COUNT(*) as cnt 
        FROM universal_cmdb 
        WHERE infrastructure_type_normalized IS NOT NULL 
        GROUP BY infrastructure_type_normalized 
        ORDER BY cnt DESC
        """
        for row in self.duck_conn.execute(infra_query).fetchall():
            if row[0]:
                print(f"  {row[0]}: {row[1]:,} ({row[1]/max(1,total_hosts)*100:.1f}%)")
        
        print("\n3. SECURITY CONTROL COVERAGE:")
        crowdstrike = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_crowdstrike = 'yes'").fetchone()[0]
        cmdb = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE present_in_cmdb = 'yes'").fetchone()[0]
        splunk = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb WHERE logging_in_splunk = 'yes'").fetchone()[0]
        
        print(f"  CrowdStrike: {crowdstrike:,} ({crowdstrike/max(1,total_hosts)*100:.1f}%)")
        print(f"  CMDB: {cmdb:,} ({cmdb/max(1,total_hosts)*100:.1f}%)")
        print(f"  Splunk Logging: {splunk:,} ({splunk/max(1,total_hosts)*100:.1f}%)")
    
    def export_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ao1_complete_{timestamp}.csv"
        
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
        processor = AO1CompleteProcessor("reviewed_labeled_columns.json", "ao1_complete_cmdb.db")
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