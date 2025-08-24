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

# Minimal logging setup
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class FastCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        print("\n═══ FAST CMDB PROCESSOR ═══\n")
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        # Pre-compiled regex patterns for faster matching
        self.normalize_pattern = re.compile(r'[^a-z0-9]')
        
        # Optimized column mappings
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
        
        # Pre-compiled pattern sets
        self.advanced_patterns = {
            'business_unit': frozenset(['business_unit', 'bu', 'business', 'department', 'division', 'org_unit']),
            'region': frozenset(['region', 'location', 'site', 'area', 'zone', 'geographic_region']),
            'country': frozenset(['country', 'nation', 'country_code', 'geo_country']),
            'infrastructure_type': frozenset(['infrastructure_type', 'infra_type', 'server_type', 'system_type', 'platform', 'environment', 'env']),
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
        
        # Use optimized DuckDB settings
        self.duck_conn = duckdb.connect(duckdb_path)
        self.duck_conn.execute("PRAGMA threads=4")
        self.duck_conn.execute("PRAGMA memory_limit='4GB'")
        
        self._create_optimized_table()
        
        print("Initialization complete.\n")
    
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
    
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
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_source_count ON universal_cmdb(source_count)"
        ]
        
        for idx in indexes:
            try:
                self.duck_conn.execute(idx)
            except:
                pass
    
    def normalize_hostname(self, hostname: str) -> str:
        """Optimized hostname normalization"""
        if not hostname or not isinstance(hostname, str) or hostname.strip() == '*Undefined':
            return ""
        
        normalized = hostname.lower().strip()
        
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
        """Optimized column discovery"""
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
        """Fast column type identification"""
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        # Direct mapping lookup
        if isinstance(column_type, str) and type_lower in self.column_mapping:
            return self.column_mapping[type_lower]
        
        # Check hostname patterns
        for pattern in self.hostname_patterns:
            if pattern in column_lower:
                return 'hostname'
        
        # Check advanced patterns
        for target_type, patterns in self.advanced_patterns.items():
            for pattern in patterns:
                if pattern in column_lower or pattern in type_lower:
                    return target_type
        
        return None
    
    def process_tables_parallel(self, columns_by_table: Dict) -> None:
        """Process multiple tables in parallel"""
        print(f"Processing {len(columns_by_table)} tables...\n")
        
        max_workers = min(4, len(columns_by_table))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for table_name, table_columns in columns_by_table.items():
                future = executor.submit(self.process_table_optimized, table_name, table_columns)
                futures[future] = table_name
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                table_name = futures[future]
                try:
                    records = future.result()
                    print(f"[{completed}/{len(columns_by_table)}] {table_name}: {records:,} records")
                except Exception as e:
                    print(f"[{completed}/{len(columns_by_table)}] {table_name}: Error - {str(e)[:50]}")
                    self.stats['processing_errors'] += 1
    
    def process_table_optimized(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        """Optimized table processing"""
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            return 0
        
        primary_hostname_col = hostname_cols[0][0]
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        query = self._build_query(table_name, all_columns, primary_hostname_col)
        
        try:
            query_job = self.bq_client.query(query)
            records_processed = self._process_results_batch(
                query_job, table_name, primary_hostname_col, attribute_types
            )
            
            self.stats['tables_processed'] += 1
            return records_processed
            
        except Exception as e:
            self.stats['processing_errors'] += 1
            raise e
    
    def _build_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        """Build optimized query"""
        column_selects = [f"`{col}`" for col in columns]
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND `{hostname_col}` != '*Undefined'
        AND LENGTH(`{hostname_col}`) > 0
        """
    
    def _process_results_batch(self, query_job, table_name: str, hostname_col: str, attribute_types: List[str]) -> int:
        """Process query results in batches"""
        records_processed = 0
        batch_size = 5000
        batch_records = []
        table_hostnames_seen = set()
        
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
        """Bulk insert/update records"""
        if not records:
            return
        
        for record in records:
            normalized_host = record['normalized_host']
            
            # Check if exists
            existing_query = """
            SELECT source_tables, source_count
            FROM universal_cmdb 
            WHERE normalized_host = ?
            """
            
            existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
            
            if existing:
                # Update existing
                self._update_host(record, existing)
                self.stats['hosts_updated'] += 1
            else:
                # Insert new
                self._insert_host(record)
                self.stats['hosts_created'] += 1
                self.duplicate_tracker.add(normalized_host)
    
    def _insert_host(self, record: Dict) -> None:
        """Insert new host"""
        columns = ['normalized_host', 'source_tables', 'source_count']
        values = [record['normalized_host'], record['table_name'], 1]
        
        data_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for col in data_columns:
            if col in record:
                columns.append(col)
                values.append(record[col])
        
        placeholders = ', '.join(['?' for _ in values])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        self.duck_conn.execute(insert_sql, values)
    
    def _update_host(self, record: Dict, existing) -> None:
        """Update existing host"""
        normalized_host = record['normalized_host']
        updates = []
        values = []
        
        # Update source tables
        current_tables = existing[0] if existing[0] else ""
        table_name = record['table_name']
        
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            
            new_source_count = (existing[1] or 0) + 1
            updates.append("source_count = ?")
            values.append(new_source_count)
        
        # Update other fields if they exist in record
        data_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for col in data_columns:
            if col in record:
                updates.append(f"{col} = COALESCE({col}, ?)")
                values.append(record[col])
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            self.duck_conn.execute(update_sql, values)
    
    def generate_report(self):
        """Generate summary report"""
        print("\n═══ PROCESSING REPORT ═══\n")
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        print(f"Total Unique Hosts: {total_hosts:,}")
        print(f"Tables Processed: {self.stats['tables_processed']}")
        print(f"Records Processed: {self.stats['total_records_processed']:,}")
        print(f"New Hosts Created: {self.stats['hosts_created']:,}")
        print(f"Hosts Updated: {self.stats['hosts_updated']:,}")
        
        if self.stats['processing_errors'] > 0:
            print(f"Processing Errors: {self.stats['processing_errors']}")
        
        # Show data coverage
        columns_to_check = ['hostname', 'business_unit', 'region', 'infrastructure_type', 'ip_address']
        
        print("\nTop Column Coverage:")
        for col in columns_to_check:
            count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            count = self.duck_conn.execute(count_query).fetchone()[0]
            percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
            if count > 0:
                print(f"  {col}: {count:,} ({percentage:.1f}%)")
    
    def export_comprehensive(self, filename: str = "universal_cmdb_export.csv"):
        """Export to CSV"""
        print(f"\nExporting to {filename}...")
        
        export_query = f"""
        COPY (
            SELECT * FROM universal_cmdb 
            ORDER BY source_count DESC, normalized_host
        ) TO '{filename}' (HEADER, DELIMITER ',')
        """
        
        self.duck_conn.execute(export_query)
        print(f"Export complete: {filename}")
    
    def process_all_fast(self):
        """Main processing function"""
        print("\n═══ STARTING FAST PROCESSING ═══\n")
        
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
        
        # Export
        self.export_comprehensive()
        
        total_time = time.time() - start_time
        
        print(f"\n═══ PROCESSING COMPLETE ═══")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Processing Rate: {self.stats['total_records_processed']/max(1, total_time):.0f} records/second")
    
    def close_connections(self):
        """Clean up connections"""
        try:
            self.duck_conn.close()
        except:
            pass

if __name__ == "__main__":
    processor = None
    
    try:
        processor = FastCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        processor.process_all_fast()
        
        print("\n═══ SUCCESS ═══")
        print("Database: universal_cmdb.db")
        print("Export: universal_cmdb_export.csv\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if processor:
            processor.close_connections()