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
        
        for table_name, columns in metadata['columns'].items():
            for column_name, column_type in columns.items():
                mapped_type = None
                
                if isinstance(column_type, str) and column_type.lower() in self.column_mapping:
                    mapped_type = self.column_mapping[column_type.lower()]
                else:
                    column_lower = column_name.lower()
                    for pattern in self.hostname_patterns:
                        if pattern in column_lower:
                            mapped_type = 'hostname'
                            break
                    
                    if not mapped_type:
                        for orig_type, norm_type in self.column_mapping.items():
                            if orig_type in column_lower:
                                mapped_type = norm_type
                                break
                
                if mapped_type:
                    all_columns.append((table_name, column_name, mapped_type))
                    print(f"Found: {table_name}.{column_name} -> {mapped_type}")
        
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
        
        existing = self.duck_conn.execute(
            "SELECT * FROM universal_cmdb WHERE normalized_host = ?", 
            [normalized_host]
        ).fetchone()
        
        if existing:
            updates = []
            values = []
            
            current_tables = existing[1] if existing[1] else ""
            if table_name not in current_tables:
                new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
                updates.append("source_tables = ?")
                values.append(new_tables)
            
            for key, value in record.items():
                if key != 'normalized_host' and value:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
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