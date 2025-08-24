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

class AO1DynamicNormalizer:
    def __init__(self, json_file_path: str, duckdb_path: str = "ao1_normalized_cmdb.db"):
        print("\n" + "=" * 80)
        print("AO1 DYNAMIC NORMALIZER - REQUIREMENTS PROCESSOR")
        print("Objective: Dynamically normalize ALL columns for visibility measurement")
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
        
        # Dynamic value tracking for ALL columns
        self.unique_values = defaultdict(lambda: defaultdict(int))
        self.normalized_values = defaultdict(lambda: defaultdict(set))
        
        self.stats = defaultdict(int)
        self.existing_hosts = {}
        
        self._init_bigquery()
        
        self.duck_conn = duckdb.connect(duckdb_path)
        self.duck_conn.execute("PRAGMA threads=8")
        self.duck_conn.execute("PRAGMA memory_limit='8GB'")
        
        self._create_normalized_table()
        self._load_existing_hosts_fast()
        
        print(f"Loaded {len(self.existing_hosts)} existing hosts")
        print(f"Using {self.max_workers} parallel workers\n")
        print("DYNAMIC NORMALIZATION APPROACH:")
        print("- All columns will be normalized based on actual values found")
        print("- Both raw and normalized values will be tracked")
        print("- Normalization patterns will be discovered, not assumed\n")
    
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
    
    def _create_normalized_table(self):
        create_sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR PRIMARY KEY,
            source_tables TEXT,
            hostname TEXT,
            hostname_normalized TEXT,
            fqdn TEXT,
            fqdn_normalized TEXT,
            domain TEXT,
            domain_normalized TEXT,
            infrastructure_type TEXT,
            infrastructure_type_normalized TEXT,
            region TEXT,
            region_normalized TEXT,
            country TEXT,
            country_normalized TEXT,
            data_center TEXT,
            data_center_normalized TEXT,
            cloud_region TEXT,
            cloud_region_normalized TEXT,
            ip_address TEXT,
            ip_address_normalized TEXT,
            class TEXT,
            class_normalized TEXT,
            system_classification TEXT,
            system_classification_normalized TEXT,
            business_unit TEXT,
            business_unit_normalized TEXT,
            apm TEXT,
            apm_normalized TEXT,
            cio TEXT,
            cio_normalized TEXT,
            edr_coverage TEXT,
            edr_coverage_normalized TEXT,
            tanium_coverage TEXT,
            tanium_coverage_normalized TEXT,
            dlp_agent_coverage TEXT,
            dlp_agent_coverage_normalized TEXT,
            logging_in_splunk TEXT,
            logging_in_splunk_normalized TEXT,
            logging_in_gso TEXT,
            logging_in_gso_normalized TEXT,
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
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized ON universal_cmdb(normalized_host)")
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_visibility ON universal_cmdb(visibility_score)")
        except:
            pass
    
    def _load_existing_hosts_fast(self):
        try:
            query = "SELECT * FROM universal_cmdb"
            result = self.duck_conn.execute(query).fetchall()
            
            for row in result:
                self.existing_hosts[row[0]] = list(row[1:])
        except:
            pass
    
    def normalize_value_dynamic(self, value: str, column_type: str) -> str:
        """Dynamically normalize any value based on patterns found"""
        if not value or not isinstance(value, str):
            return "unknown"
        
        normalized = value.lower().strip()
        
        # Remove special characters but keep spaces for grouping
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)
        
        # Group similar values based on column type
        if column_type == 'infrastructure_type':
            # Group by common infrastructure patterns
            if any(term in normalized for term in ['cloud', 'aws', 'azure', 'gcp', 'ec2']):
                return "cloud_infrastructure"
            elif any(term in normalized for term in ['prem', 'onprem', 'on_prem', 'datacenter', 'dc']):
                return "on_premise"
            elif any(term in normalized for term in ['saas', 'software_as_a_service', 'application']):
                return "saas_application"
            elif any(term in normalized for term in ['api', 'endpoint', 'service', 'rest']):
                return "api_service"
            elif any(term in normalized for term in ['virtual', 'vm', 'virt']):
                return "virtual_infrastructure"
            elif any(term in normalized for term in ['container', 'docker', 'kubernetes', 'k8s']):
                return "containerized"
            else:
                # Keep first 30 chars of normalized value
                return normalized[:30]
        
        elif column_type == 'system_classification' or column_type == 'class':
            # Group by system type patterns
            if any(term in normalized for term in ['web', 'apache', 'nginx', 'iis', 'http']):
                return "web_system"
            elif any(term in normalized for term in ['windows', 'win', 'microsoft', 'ms']):
                return "windows_system"
            elif any(term in normalized for term in ['linux', 'unix', 'ubuntu', 'redhat', 'centos', 'debian']):
                return "linux_unix_system"
            elif any(term in normalized for term in ['aix', 'solaris', 'hpux', 'hp_ux']):
                return "unix_variant_system"
            elif any(term in normalized for term in ['mainframe', 'zos', 'z_os', 'mvs', 'cics']):
                return "mainframe_system"
            elif any(term in normalized for term in ['database', 'db', 'oracle', 'sql', 'postgres', 'mongo', 'mysql']):
                return "database_system"
            elif any(term in normalized for term in ['network', 'firewall', 'router', 'switch', 'fw', 'ndr', 'ids', 'ips']):
                return "network_device"
            elif any(term in normalized for term in ['storage', 'san', 'nas', 'backup']):
                return "storage_system"
            else:
                return normalized[:30]
        
        elif column_type in ['region', 'country', 'data_center', 'cloud_region']:
            # Normalize location data
            # Remove common prefixes/suffixes
            normalized = re.sub(r'^(the|region|country|center|dc|az)_', '', normalized)
            normalized = re.sub(r'_(region|country|center|dc|az)$', '', normalized)
            # Group common variations
            if 'america' in normalized or 'us' in normalized or 'usa' in normalized:
                if 'north' in normalized:
                    return "north_america"
                elif 'south' in normalized:
                    return "south_america"
                else:
                    return "americas"
            elif 'europe' in normalized or 'eu' in normalized:
                return "europe"
            elif 'asia' in normalized or 'apac' in normalized:
                return "asia_pacific"
            elif 'africa' in normalized:
                return "africa"
            elif 'middle_east' in normalized or 'me' in normalized:
                return "middle_east"
            else:
                return normalized[:30]
        
        elif column_type == 'business_unit':
            # Normalize business units
            normalized = re.sub(r'\d+', '', normalized)  # Remove numbers
            normalized = re.sub(r'[_-]+', '_', normalized)  # Standardize separators
            return normalized[:30]
        
        elif column_type in ['edr_coverage', 'tanium_coverage', 'dlp_agent_coverage']:
            # Normalize coverage fields
            if any(term in normalized for term in ['yes', 'true', 'enabled', 'active', 'installed', 'running', '1']):
                return "covered"
            elif any(term in normalized for term in ['no', 'false', 'disabled', 'inactive', 'not_installed', '0']):
                return "not_covered"
            elif any(term in normalized for term in ['partial', 'limited', 'some']):
                return "partial_coverage"
            else:
                return normalized[:30]
        
        elif column_type in ['logging_in_splunk', 'logging_in_gso']:
            # Normalize logging status
            if any(term in normalized for term in ['yes', 'true', 'enabled', 'active', 'logging', '1']):
                return "logging_enabled"
            elif any(term in normalized for term in ['no', 'false', 'disabled', 'inactive', 'not_logging', '0']):
                return "logging_disabled"
            elif any(term in normalized for term in ['partial', 'limited', 'some']):
                return "partial_logging"
            else:
                return normalized[:30]
        
        elif column_type == 'ip_address':
            # Normalize IP addresses to ranges
            if '.' in value:  # IPv4
                parts = value.split('.')
                if len(parts) >= 3:
                    return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            elif ':' in value:  # IPv6
                return "ipv6_address"
            return normalized[:30]
        
        elif column_type == 'domain':
            # Normalize domains
            parts = normalized.split('.')
            if len(parts) >= 2:
                # Keep primary domain
                return '.'.join(parts[-2:])
            return normalized[:30]
        
        else:
            # Generic normalization for other columns
            # Remove version numbers
            normalized = re.sub(r'v?\d+[\.\d]*', '', normalized)
            # Remove common suffixes
            normalized = re.sub(r'_(prod|dev|test|qa|stage|staging|uat)$', '', normalized)
            # Limit length
            return normalized[:30]
    
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
        max_points = 100.0
        
        # Dynamic scoring based on populated fields
        critical_fields = [
            'hostname', 'fqdn', 'domain', 'ip_address', 'infrastructure_type',
            'region', 'country', 'business_unit', 'system_classification',
            'logging_in_splunk', 'logging_in_gso', 'present_in_crowdstrike'
        ]
        
        points_per_field = max_points / len(critical_fields)
        
        for field in critical_fields:
            if record.get(field) and str(record[field]).strip() not in self.invalid_values:
                score += points_per_field
        
        return round(score, 2)
    
    def load_metadata(self) -> Dict:
        print("Loading metadata for dynamic normalization...")
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
        print("Starting Dynamic Normalization Processing...\n")
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
        
        self.generate_dynamic_report()
        self.export_normalized_data()
        
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
            
            # Process and normalize ALL columns dynamically
            for i, col in enumerate(columns):
                if i < len(row) and row[i]:
                    val = str(row[i]).strip()
                    if val.lower() not in self.invalid_values:
                        col_type = column_types.get(col)
                        if col_type and col_type != 'hostname':
                            # Store raw value
                            record_data[col_type] = val
                            
                            # Track unique values
                            self.unique_values[col_type][val] += 1
                            
                            # Normalize and store normalized value
                            normalized_val = self.normalize_value_dynamic(val, col_type)
                            record_data[f"{col_type}_normalized"] = normalized_val
                            
                            # Track normalized groups
                            self.normalized_values[col_type][normalized_val].add(val)
                            
                            # Special handling for Splunk logging table
                            if col_type == 'logging_in_splunk' and table_name == 'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG':
                                record_data[col_type] = 'yes'
                                record_data[f"{col_type}_normalized"] = 'logging_enabled'
            
            record_data['visibility_score'] = self.calculate_visibility_score(record_data)
            
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
        
        with self.db_lock:
            for record in records:
                normalized_host = record['normalized_host']
                
                if normalized_host in self.existing_hosts:
                    duplicates += 1
                    self.update_host_dynamic(record)
                else:
                    self.insert_host_dynamic(record)
                    self.existing_hosts[normalized_host] = []
        
        return duplicates
    
    def insert_host_dynamic(self, record: Dict):
        # Build dynamic insert based on what's in the record
        columns = ['normalized_host', 'source_tables']
        values = [record['normalized_host'], record['table_name']]
        
        # All possible columns (raw and normalized)
        all_columns = [
            'hostname', 'hostname_normalized',
            'fqdn', 'fqdn_normalized',
            'domain', 'domain_normalized',
            'infrastructure_type', 'infrastructure_type_normalized',
            'region', 'region_normalized',
            'country', 'country_normalized',
            'data_center', 'data_center_normalized',
            'cloud_region', 'cloud_region_normalized',
            'ip_address', 'ip_address_normalized',
            'class', 'class_normalized',
            'system_classification', 'system_classification_normalized',
            'business_unit', 'business_unit_normalized',
            'apm', 'apm_normalized',
            'cio', 'cio_normalized',
            'edr_coverage', 'edr_coverage_normalized',
            'tanium_coverage', 'tanium_coverage_normalized',
            'dlp_agent_coverage', 'dlp_agent_coverage_normalized',
            'logging_in_splunk', 'logging_in_splunk_normalized',
            'logging_in_gso', 'logging_in_gso_normalized',
            'present_in_crowdstrike', 'present_in_cmdb',
            'visibility_score'
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
        except:
            pass
    
    def update_host_dynamic(self, record: Dict):
        updates = []
        values = []
        
        # Update with normalized values
        for col_base in ['infrastructure_type', 'system_classification', 'region', 'country',
                        'data_center', 'cloud_region', 'business_unit', 'class',
                        'logging_in_splunk', 'logging_in_gso', 'edr_coverage',
                        'tanium_coverage', 'dlp_agent_coverage']:
            
            if col_base in record:
                updates.append(f"{col_base} = COALESCE({col_base}, ?)")
                values.append(record[col_base])
            
            normalized_col = f"{col_base}_normalized"
            if normalized_col in record:
                updates.append(f"{normalized_col} = ?")
                values.append(record[normalized_col])
        
        if 'visibility_score' in record:
            updates.append("visibility_score = ?")
            values.append(record['visibility_score'])
        
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
        print("DYNAMIC NORMALIZATION REPORT - AO1 REQUIREMENTS")
        print("=" * 80)
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"\nTotal Unique Assets: {total_hosts:,}")
        
        # For each column type, show unique values and their normalized groups
        for col_type in sorted(self.unique_values.keys()):
            print(f"\n{'=' * 60}")
            print(f"COLUMN: {col_type.upper()}")
            print(f"{'=' * 60}")
            
            unique_count = len(self.unique_values[col_type])
            total_occurrences = sum(self.unique_values[col_type].values())
            normalized_groups = len(self.normalized_values[col_type])
            
            print(f"Unique raw values: {unique_count:,}")
            print(f"Total occurrences: {total_occurrences:,}")
            print(f"Normalized groups: {normalized_groups}")
            
            print(f"\nTop 10 Raw Values:")
            for value, count in sorted(self.unique_values[col_type].items(), 
                                      key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {value}: {count:,}")
            
            print(f"\nNormalized Groups and Sample Values:")
            for norm_value in sorted(self.normalized_values[col_type].keys())[:10]:
                raw_values = list(self.normalized_values[col_type][norm_value])[:3]
                print(f"  {norm_value}:")
                print(f"    Examples: {', '.join(raw_values)}")
                print(f"    Total values in group: {len(self.normalized_values[col_type][norm_value])}")
        
        # Requirements-specific reporting
        print("\n" + "=" * 80)
        print("AO1 REQUIREMENTS VISIBILITY METRICS")
        print("=" * 80)
        
        # Requirement 1: Global View
        print("\n1. GLOBAL VIEW:")
        for col in ['hostname', 'fqdn', 'ip_address', 'domain']:
            count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL").fetchone()[0]
            print(f"  {col}: {count:,} ({count/max(1,total_hosts)*100:.1f}%)")
        
        # Requirement 2: Infrastructure Type
        print("\n2. INFRASTRUCTURE TYPE (Normalized Groups):")
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
        
        # Continue with other requirements...
        print("\n3. REGIONAL VIEW (Normalized):")
        region_query = """
        SELECT region_normalized, COUNT(*) as cnt 
        FROM universal_cmdb 
        WHERE region_normalized IS NOT NULL 
        GROUP BY region_normalized 
        ORDER BY cnt DESC
        LIMIT 10
        """
        for row in self.duck_conn.execute(region_query).fetchall():
            if row[0]:
                print(f"  {row[0]}: {row[1]:,}")
        
        print("\n4. BUSINESS UNIT (Normalized):")
        bu_query = """
        SELECT business_unit_normalized, COUNT(*) as cnt 
        FROM universal_cmdb 
        WHERE business_unit_normalized IS NOT NULL 
        GROUP BY business_unit_normalized 
        ORDER BY cnt DESC
        LIMIT 10
        """
        for row in self.duck_conn.execute(bu_query).fetchall():
            if row[0]:
                print(f"  {row[0]}: {row[1]:,}")
        
        print("\n5. SYSTEM CLASSIFICATION (Normalized):")
        sys_query = """
        SELECT system_classification_normalized, COUNT(*) as cnt 
        FROM universal_cmdb 
        WHERE system_classification_normalized IS NOT NULL 
        GROUP BY system_classification_normalized 
        ORDER BY cnt DESC
        """
        for row in self.duck_conn.execute(sys_query).fetchall():
            if row[0]:
                print(f"  {row[0]}: {row[1]:,} ({row[1]/max(1,total_hosts)*100:.1f}%)")
        
        print("\n6. SECURITY CONTROL COVERAGE:")
        for col in ['edr_coverage', 'tanium_coverage', 'dlp_agent_coverage', 'present_in_crowdstrike']:
            count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL").fetchone()[0]
            print(f"  {col}: {count:,} ({count/max(1,total_hosts)*100:.1f}%)")
        
        print("\n7. LOGGING COMPLIANCE (Normalized):")
        for col in ['logging_in_splunk_normalized', 'logging_in_gso_normalized']:
            enabled = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} = 'logging_enabled'").fetchone()[0]
            print(f"  {col.replace('_normalized', '')} enabled: {enabled:,} ({enabled/max(1,total_hosts)*100:.1f}%)")
    
    def export_normalized_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"ao1_normalized_report_{timestamp}.csv"
        print(f"\nExporting normalized data to {filename}...")
        
        export_query = f"""
        COPY (
            SELECT * FROM universal_cmdb 
            ORDER BY visibility_score DESC, source_count DESC, normalized_host
        ) TO '{filename}' (HEADER, DELIMITER ',')
        """
        
        self.duck_conn.execute(export_query)
        print(f"Export complete: {filename}")
        
        # Export normalization mappings
        mapping_filename = f"ao1_normalization_mappings_{timestamp}.json"
        print(f"Exporting normalization mappings to {mapping_filename}...")
        
        mappings = {
            'unique_values_counts': {k: dict(v) for k, v in self.unique_values.items()},
            'normalized_groups': {k: {nv: list(rv) for nv, rv in v.items()} 
                                 for k, v in self.normalized_values.items()}
        }
        
        with open(mapping_filename, 'w') as f:
            json.dump(mappings, f, indent=2)
        
        print(f"Mappings export complete: {mapping_filename}")
    
    def close(self):
        self.duck_conn.close()

if __name__ == "__main__":
    processor = None
    
    try:
        print("\n" + "=" * 80)
        print("AO1 DYNAMIC NORMALIZER - ALL COLUMNS")
        print("=" * 80 + "\n")
        
        processor = AO1DynamicNormalizer("reviewed_labeled_columns.json", "ao1_normalized_cmdb.db")
        processor.process_all_parallel()
        
        print("\n" + "=" * 80)
        print("DYNAMIC NORMALIZATION COMPLETE")
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