import json
import duckdb
import os
import re
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

class HostDataProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
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
            'cloud_region': 'cloud_region',
            'ip_address': 'ip_address',
            'class': 'class',
            'system_classification': 'system_classification',
            'business_unit': 'business_unit',
            'apm': 'apm',
            'cio': 'cio',
            'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk',
            'logging_in_gso': 'logging_in_gso'
        }
        
        self.hostname_patterns = ['host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name', 
                                 'endpoint_name', 'splunk_host', 'app_host', 'computer_name']
        
        self.attribute_patterns = {
            'business_unit': ['business_unit', 'bu', 'business', 'department', 'division', 'org_unit', 'cost_center'],
            'region': ['region', 'location', 'site', 'area', 'zone', 'geographic', 'geo_region'],
            'country': ['country', 'nation', 'country_code'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'server_type', 'platform', 'environment', 'env'],
            'data_center': ['datacenter', 'data_center', 'dc', 'facility', 'center'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'host_ip', 'server_ip'],
            'class': ['class', 'classification', 'tier', 'level', 'grade'],
            'system_classification': ['system_classification', 'security_classification', 'sensitivity'],
            'apm': ['apm', 'monitoring', 'application_monitoring'],
            'cio': ['cio', 'owner', 'responsible', 'contact', 'admin', 'administrator'],
            'edr_coverage': ['edr_coverage', 'edr', 'endpoint_detection', 'security_agent', 'antivirus'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'tanium_agent'],
            'dlp_agent_coverage': ['dlp_agent_coverage', 'dlp', 'data_loss_prevention'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk', 'splunk_logging'],
            'logging_in_gso': ['logging_in_gso', 'gso', 'gso_logging'],
            'domain': ['domain', 'dns_domain', 'ad_domain'],
            'fqdn': ['fqdn', 'full_name', 'qualified_name']
        }
        
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
        
        self.duck_conn = duckdb.connect(duckdb_path)
        
        self._create_table()
        
    def _create_table(self):
        sql = """
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
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(sql)
        
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)")
        except:
            pass
            
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.lower().strip()
        
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        normalized = normalized.replace('-', '')
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized
    
    def load_metadata(self) -> Dict:
        with open(self.json_file_path, 'r') as f:
            return json.load(f)
    
    def identify_columns(self, metadata):
        all_columns = []
        
        print("\n=== COLUMN DISCOVERY DEBUG ===")
        
        for table_name, columns in metadata['columns'].items():
            print(f"\nTable: {table_name}")
            for column_name, column_type in columns.items():
                mapped_type = None
                
                # First: exact match on column_type
                if isinstance(column_type, str) and column_type.lower() in self.column_mapping:
                    mapped_type = self.column_mapping[column_type.lower()]
                    print(f"  EXACT TYPE MATCH: {column_name} ({column_type}) -> {mapped_type}")
                
                # Second: check hostname patterns
                if not mapped_type:
                    column_lower = column_name.lower()
                    for pattern in self.hostname_patterns:
                        if pattern in column_lower:
                            mapped_type = 'hostname'
                            print(f"  HOSTNAME PATTERN: {column_name} -> {mapped_type}")
                            break
                
                # Third: check ALL attribute patterns
                if not mapped_type:
                    column_lower = column_name.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in column_lower:
                                mapped_type = attr_type
                                print(f"  ATTRIBUTE PATTERN: {column_name} -> {mapped_type} (matched '{pattern}')")
                                break
                        if mapped_type:
                            break
                
                # Fourth: check if column_type itself matches attribute patterns
                if not mapped_type and isinstance(column_type, str):
                    type_lower = column_type.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in type_lower:
                                mapped_type = attr_type
                                print(f"  TYPE PATTERN: {column_name} ({column_type}) -> {mapped_type} (matched '{pattern}')")
                                break
                        if mapped_type:
                            break
                
                if mapped_type:
                    all_columns.append((table_name, column_name, mapped_type))
                    print(f"  ✅ FINAL: {table_name}.{column_name} -> {mapped_type}")
                else:
                    print(f"  ❌ NO MATCH: {column_name} ({column_type})")
        
        print(f"\n=== SUMMARY: Found {len(all_columns)} mappable columns ===")
        return all_columns
    
    def process_table_completely(self, table_name, all_columns_for_table):
        hostname_cols = [c for c in all_columns_for_table if c[2] == 'hostname']
        attribute_cols = [c for c in all_columns_for_table if c[2] != 'hostname']
        
        if not hostname_cols:
            return
        
        hostname_col = hostname_cols[0][1]
        
        column_names = [hostname_col] + [c[1] for c in attribute_cols]
        attribute_types = [c[2] for c in attribute_cols]
        
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in column_names])}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND LENGTH(`{hostname_col}`) > 0
        LIMIT 50000
        """
        
        try:
            print(f"Processing {table_name} with {len(column_names)} columns...")
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            records = []
            for row in results:
                if row[0] and isinstance(row[0], str):
                    normalized_host = self.normalize_hostname(row[0])
                    if normalized_host and len(normalized_host) > 2:
                        record = {'normalized_host': normalized_host, 'hostname': row[0]}
                        
                        for i, attr_type in enumerate(attribute_types, 1):
                            if i < len(row) and row[i]:
                                record[attr_type] = str(row[i]).strip()
                        
                        records.append(record)
            
            for record in records:
                self._insert_or_update_host(record, table_name)
                
            print(f"Processed {len(records)} records from {table_name}")
            
        except Exception as e:
            print(f"Error processing {table_name}: {e}")
    
    def _insert_or_update_host(self, record, table_name):
        normalized_host = record['normalized_host']
        
        existing_query = "SELECT * FROM universal_cmdb WHERE normalized_host = ?"
        existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
        
        if existing:
            columns_query = "PRAGMA table_info(universal_cmdb)"
            column_info = self.duck_conn.execute(columns_query).fetchall()
            column_names = [col[1] for col in column_info]
            
            updates = []
            values = []
            
            current_tables = existing[1] if existing[1] else ""
            if table_name not in current_tables:
                new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
                updates.append("source_tables = ?")
                values.append(new_tables)
            
            for key, new_value in record.items():
                if key != 'normalized_host' and new_value and key in column_names:
                    col_index = column_names.index(key)
                    existing_value = existing[col_index] if col_index < len(existing) else None
                    
                    if existing_value and existing_value.strip():
                        existing_values = set(v.strip() for v in existing_value.split(' | '))
                        new_values = existing_values.copy()
                        new_values.add(new_value.strip())
                        
                        if len(new_values) > 1:
                            final_value = ' | '.join(sorted(new_values))
                        else:
                            final_value = new_value.strip()
                    else:
                        final_value = new_value.strip()
                    
                    updates.append(f"{key} = ?")
                    values.append(final_value)
            
            if updates:
                values.append(normalized_host)
                update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)}, last_updated = CURRENT_TIMESTAMP WHERE normalized_host = ?"
                self.duck_conn.execute(update_sql, values)
        else:
            columns = ['normalized_host', 'source_tables'] + [k for k in record.keys() if k != 'normalized_host']
            values = [normalized_host, table_name] + [record.get(k) for k in columns[2:]]
            placeholders = ', '.join(['?'] * len(columns))
            
            insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
            self.duck_conn.execute(insert_sql, values)
    
    def process_all(self):
        metadata = self.load_metadata()
        all_columns = self.identify_columns(metadata)
        
        columns_by_table = defaultdict(list)
        for table_name, column_name, mapped_type in all_columns:
            columns_by_table[table_name].append((table_name, column_name, mapped_type))
        
        for table_name, table_columns in columns_by_table.items():
            self.process_table_completely(table_name, table_columns)
        
        self._create_summary()
        self._show_results()
    
    def _create_summary(self):
        try:
            self.duck_conn.execute("DROP TABLE IF EXISTS all_sources")
            
            create_sql = """
            CREATE TABLE all_sources AS (
                SELECT 
                    normalized_host as host,
                    source_tables,
                    hostname, fqdn, domain, infrastructure_type, region, country,
                    data_center, cloud_region, ip_address, class, system_classification,
                    business_unit, apm, cio, edr_coverage, tanium_coverage, 
                    dlp_agent_coverage, logging_in_splunk, logging_in_gso,
                    LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count,
                    last_updated
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                ORDER BY source_count DESC, normalized_host
            )
            """
            self.duck_conn.execute(create_sql)
        except Exception as e:
            print(f"Error creating summary: {e}")
    
    def _show_results(self):
        total = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        print(f"\nTotal hosts: {total}")
        
        columns = ['hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
                  'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
                  'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage', 
                  'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso']
        
        print("\nColumn Population:")
        for col in columns:
            count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {col}: {count} ({pct:.1f}%)")
        
        print("\nSample records:")
        samples = self.duck_conn.execute("SELECT * FROM universal_cmdb LIMIT 3").fetchall()
        for sample in samples:
            print(f"Host: {sample[0]}")
            for i, col in enumerate(['source_tables'] + columns):
                if sample[i+1]:
                    print(f"  {col}: {sample[i+1]}")
    
    def export(self, filename="universal_cmdb_export.csv"):
        self.duck_conn.execute(f"COPY (SELECT * FROM universal_cmdb ORDER BY normalized_host) TO '{filename}' WITH (FORMAT CSV, HEADER)")
        print(f"Exported to {filename}")
    
    def close(self):
        self.duck_conn.close()

if __name__ == "__main__":
    processor = HostDataProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
    
    try:
        processor.process_all()
        processor.export()
        print("\nProcessing complete!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        processor.close()