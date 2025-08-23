import json
import duckdb
import os
import re
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple
import logging
from collections import defaultdict
import time

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

class HostDataProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        logger.info("₊˚✩ Initializing CMDB Processor...")
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        logger.info("༘˚⋆ Setting up column mappings...")
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
        
        logger.info("𖦹 Connecting to BigQuery...")
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            logger.info(f"⋆｡‧˚ Using service account file: {service_account_file}")
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
            logger.info("✧˚ BigQuery connected with service account")
        else:
            logger.warning(f"₊˚⊹ Service account file not found: {service_account_file}")
            logger.info("𐙚 Attempting default credentials...")
            self.bq_client = bigquery.Client(project="chronicle-fisv")
            logger.info("♡ BigQuery connected with default credentials")
        
        logger.info(f"⋆𖦹 Connecting to DuckDB: {duckdb_path}")
        self.duck_conn = duckdb.connect(duckdb_path)
        logger.info("✧˚ DuckDB connected successfully")
        
        logger.info("༘˚⋆ Creating database table...")
        self._create_table()
        logger.info("₊˚✩ Database table ready")
        
    def _create_table(self):
        logger.info("⋆｡‧˚ Defining table schema...")
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
        
        logger.info("𖦹 Executing table creation...")
        self.duck_conn.execute(sql)
        
        logger.info("✧˚ Creating database indexes...")
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)")
            logger.info("♡ Primary index created")
        except Exception as e:
            logger.warning(f"₊˚⊹ Index creation skipped: {e}")
            
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
        logger.info(f"༘˚⋆ Loading metadata from: {self.json_file_path}")
        start_time = time.time()
        
        try:
            with open(self.json_file_path, 'r') as f:
                metadata = json.load(f)
            
            load_time = time.time() - start_time
            logger.info(f"✧˚ Metadata loaded successfully in {load_time:.2f}s")
            
            if 'columns' in metadata:
                total_tables = len(metadata['columns'])
                total_columns = sum(len(columns) for columns in metadata['columns'].values())
                logger.info(f"𖦹 Found {total_tables} tables with {total_columns} total columns")
            else:
                logger.warning("₊˚⊹ No 'columns' key found in metadata")
                
            return metadata
        except Exception as e:
            logger.error(f"𐙚 Failed to load metadata: {e}")
            raise
    
    def identify_columns(self, metadata):
        logger.info("⋆｡‧˚ Starting column identification process...")
        all_columns = []
        
        if 'columns' not in metadata:
            logger.error("𐙚 No 'columns' key found in metadata")
            return []
        
        table_count = len(metadata['columns'])
        logger.info(f"༘˚⋆ Analyzing {table_count} tables for column patterns...")
        
        for table_idx, (table_name, columns) in enumerate(metadata['columns'].items(), 1):
            logger.info(f"₊˚✩ [{table_idx}/{table_count}] Analyzing table: {table_name}")
            
            column_count = len(columns)
            matches_found = 0
            
            for column_name, column_type in columns.items():
                mapped_type = None
                match_reason = ""
                
                if isinstance(column_type, str) and column_type.lower() in self.column_mapping:
                    mapped_type = self.column_mapping[column_type.lower()]
                    match_reason = f"exact type match: '{column_type}'"
                
                if not mapped_type:
                    column_lower = column_name.lower()
                    for pattern in self.hostname_patterns:
                        if pattern in column_lower:
                            mapped_type = 'hostname'
                            match_reason = f"hostname pattern: '{pattern}'"
                            break
                
                if not mapped_type:
                    column_lower = column_name.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in column_lower:
                                mapped_type = attr_type
                                match_reason = f"attribute pattern: '{pattern}'"
                                break
                        if mapped_type:
                            break
                
                if not mapped_type and isinstance(column_type, str):
                    type_lower = column_type.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in type_lower:
                                mapped_type = attr_type
                                match_reason = f"type pattern: '{pattern}'"
                                break
                        if mapped_type:
                            break
                
                if mapped_type:
                    all_columns.append((table_name, column_name, mapped_type))
                    matches_found += 1
                    logger.info(f"  ♡ {column_name} -> {mapped_type} ({match_reason})")
                else:
                    logger.debug(f"  ₊˚⊹ {column_name} ({column_type}) -> no match")
            
            logger.info(f"  𖦹 Table summary: {matches_found}/{column_count} columns matched")
        
        logger.info(f"✧˚ Column identification complete: {len(all_columns)} total matches found")
        return all_columns
    
    def process_table_completely(self, table_name, all_columns_for_table):
        logger.info(f"\n⋆｡‧˚ Processing table: {table_name}")
        
        hostname_cols = [c for c in all_columns_for_table if c[2] == 'hostname']
        attribute_cols = [c for c in all_columns_for_table if c[2] != 'hostname']
        
        logger.info(f"  ༘˚⋆ Found {len(hostname_cols)} hostname columns, {len(attribute_cols)} attribute columns")
        
        for col in hostname_cols:
            logger.info(f"    𖦹 Hostname: {col[1]} -> {col[2]}")
        for col in attribute_cols:
            logger.info(f"    ♡ Attribute: {col[1]} -> {col[2]}")
        
        if not hostname_cols:
            logger.warning(f"  ₊˚⊹ Skipping {table_name} - no hostname columns found")
            return
        
        hostname_col = hostname_cols[0][1]
        logger.info(f"  ✧˚ Using primary hostname column: {hostname_col}")
        
        column_names = [hostname_col] + [c[1] for c in attribute_cols]
        attribute_types = [c[2] for c in attribute_cols]
        
        logger.info(f"  𐙚 Query will select {len(column_names)} columns: {column_names}")
        
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in column_names])}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND LENGTH(`{hostname_col}`) > 0
        LIMIT 50000
        """
        
        logger.info(f"  ⋆｡‧˚ Executing BigQuery for {table_name}...")
        start_time = time.time()
        
        try:
            query_job = self.bq_client.query(query)
            logger.info(f"    ₊˚✩ Query submitted, waiting for results...")
            results = query_job.result()
            
            query_time = time.time() - start_time
            logger.info(f"    ♡ Query completed in {query_time:.2f}s")
            
            records = []
            attribute_data_found = {attr_type: 0 for attr_type in attribute_types}
            
            logger.info(f"    ༘˚⋆ Processing query results...")
            row_count = 0
            
            for row in results:
                row_count += 1
                if row_count % 1000 == 0:
                    logger.info(f"      𖦹 Processed {row_count} rows...")
                    
                if row[0] and isinstance(row[0], str):
                    normalized_host = self.normalize_hostname(row[0])
                    if normalized_host and len(normalized_host) > 2:
                        record = {'normalized_host': normalized_host, 'hostname': row[0]}
                        
                        for i, attr_type in enumerate(attribute_types, 1):
                            if i < len(row) and row[i] and str(row[i]).strip():
                                record[attr_type] = str(row[i]).strip()
                                attribute_data_found[attr_type] += 1
                        
                        records.append(record)
            
            logger.info(f"    ✧˚ Processing complete: {len(records)} valid host records found")
            
            for attr_type, count in attribute_data_found.items():
                if count > 0:
                    logger.info(f"      ♡ {attr_type}: {count} non-empty values")
            
            logger.info(f"    ⋆｡‧˚ Writing {len(records)} records to database...")
            records_written = 0
            
            for i, record in enumerate(records):
                if i % 500 == 0 and i > 0:
                    logger.info(f"      𐙚 Written {i}/{len(records)} records...")
                    
                self._insert_or_update_host(record, table_name)
                records_written += 1
            
            logger.info(f"    ₊˚✩ Successfully wrote {records_written} records from {table_name}")
            
            logger.info(f"    ༘˚⋆ Verifying data in database...")
            for attr_type in attribute_types:
                if attribute_data_found[attr_type] > 0:
                    count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {attr_type} IS NOT NULL AND {attr_type} != ''"
                    try:
                        db_count = self.duck_conn.execute(count_query).fetchone()[0]
                        logger.info(f"      ♡ {attr_type}: {db_count} records confirmed in database")
                    except Exception as e:
                        logger.warning(f"      ₊˚⊹ Could not verify {attr_type}: {e}")
            
        except Exception as e:
            logger.error(f"  𐙚 Error processing {table_name}: {e}")
            import traceback
            logger.error(f"  ⋆｡‧˚ Full traceback: {traceback.format_exc()}")
    
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
        logger.info("₊˚✩ Starting complete CMDB processing...")
        
        logger.info("༘˚⋆ Step 1: Loading metadata...")
        metadata = self.load_metadata()
        
        logger.info("⋆｡‧˚ Step 2: Identifying relevant columns...")
        all_columns = self.identify_columns(metadata)
        
        if not all_columns:
            logger.error("𐙚 No columns found to process!")
            return
        
        logger.info("𖦹 Step 3: Grouping columns by table...")
        columns_by_table = defaultdict(list)
        for table_name, column_name, mapped_type in all_columns:
            columns_by_table[table_name].append((table_name, column_name, mapped_type))
        
        total_tables = len(columns_by_table)
        logger.info(f"✧˚ Found {total_tables} tables to process")
        
        logger.info("♡ Step 4: Processing each table...")
        for table_idx, (table_name, table_columns) in enumerate(columns_by_table.items(), 1):
            logger.info(f"\n⋆｡‧˚ [{table_idx}/{total_tables}] Starting table: {table_name}")
            start_time = time.time()
            
            self.process_table_completely(table_name, table_columns)
            
            process_time = time.time() - start_time
            logger.info(f"₊˚⊹ Table {table_name} completed in {process_time:.2f}s")
        
        logger.info("༘˚⋆ Step 5: Creating summary tables...")
        self._create_summary()
        
        logger.info("𖦹 Step 6: Generating final results...")
        self._show_results()
        
        logger.info("✧˚ Complete CMDB processing finished!")
    
    def _create_summary(self):
        logger.info("⋆｡‧˚ Creating summary table...")
        try:
            logger.info("  𐙚 Dropping existing summary table...")
            self.duck_conn.execute("DROP TABLE IF EXISTS all_sources")
            
            logger.info("  ༘˚⋆ Building new summary table...")
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
            logger.info("  ♡ Summary table created successfully")
        except Exception as e:
            logger.error(f"  𐙚 Summary table creation failed: {e}")
    
    def _show_results(self):
        logger.info("₊˚✩ Generating final verification report...")
        
        total_query = "SELECT COUNT(*) FROM universal_cmdb"
        total = self.duck_conn.execute(total_query).fetchone()[0]
        logger.info(f"⋆｡‧˚ Total hosts in database: {total:,}")
        
        columns = ['hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
                  'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
                  'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage', 
                  'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso']
        
        logger.info("༘˚⋆ Column population verification:")
        populated_columns = []
        empty_columns = []
        
        for col in columns:
            count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            count = self.duck_conn.execute(count_query).fetchone()[0]
            pct = (count / total * 100) if total > 0 else 0
            
            if count > 0:
                populated_columns.append(col)
                logger.info(f"  ♡ {col}: {count:,} records ({pct:.1f}%)")
                
                sample_query = f"SELECT DISTINCT {col} FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != '' LIMIT 3"
                samples = self.duck_conn.execute(sample_query).fetchall()
                sample_values = [str(s[0])[:30] for s in samples]
                logger.info(f"     𖦹 Samples: {', '.join(sample_values)}")
            else:
                empty_columns.append(col)
                logger.warning(f"  ₊˚⊹ {col}: 0 records (empty)")
        
        logger.info(f"\n✧˚ SUCCESS SUMMARY:")
        logger.info(f"  ♡ Columns with data: {len(populated_columns)}")
        logger.info(f"  ₊˚⊹ Empty columns: {len(empty_columns)}")
        
        if populated_columns:
            logger.info(f"  𖦹 Populated columns: {', '.join(populated_columns)}")
        
        if empty_columns:
            logger.warning(f"  ⋆｡‧˚ Empty columns: {', '.join(empty_columns)}")
        
        logger.info("༘˚⋆ Sample complete records:")
        sample_query = """
        SELECT * FROM universal_cmdb 
        WHERE normalized_host IS NOT NULL
        ORDER BY (
            CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 ELSE 0 END +
            CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 ELSE 0 END +
            CASE WHEN region IS NOT NULL AND region != '' THEN 1 ELSE 0 END +
            CASE WHEN infrastructure_type IS NOT NULL AND infrastructure_type != '' THEN 1 ELSE 0 END
        ) DESC
        LIMIT 3
        """
        samples = self.duck_conn.execute(sample_query).fetchall()
        
        column_names = ['normalized_host', 'source_tables'] + columns + ['last_updated', 'created_at']
        
        for i, sample in enumerate(samples, 1):
            logger.info(f"  ⋆｡‧˚ Record {i}: {sample[0]}")
            fields_with_data = 0
            for j, col_name in enumerate(column_names[1:], 1):
                if j < len(sample) and sample[j] and str(sample[j]).strip() and col_name not in ['last_updated', 'created_at']:
                    logger.info(f"    ♡ {col_name}: {str(sample[j])[:50]}")
                    fields_with_data += 1
            logger.info(f"    𖦹 Total populated fields: {fields_with_data}")
    
    def export(self, filename="universal_cmdb_export.csv"):
        logger.info(f"༘˚⋆ Exporting data to {filename}...")
        try:
            self.duck_conn.execute(f"COPY (SELECT * FROM universal_cmdb ORDER BY normalized_host) TO '{filename}' WITH (FORMAT CSV, HEADER)")
            logger.info(f"✧˚ Export completed: {filename}")
        except Exception as e:
            logger.error(f"𐙚 Export failed: {e}")
    
    def close(self):
        logger.info("₊˚⊹ Closing database connections...")
        try:
            self.duck_conn.close()
            logger.info("♡ Database connections closed")
        except Exception as e:
            logger.warning(f"⋆｡‧˚ Error closing connections: {e}")

if __name__ == "__main__":
    logger.info("₊˚✩ UNIVERSAL CMDB PROCESSOR STARTING")
    logger.info("═══════════════════════════════════════════════════════════")
    
    start_time = time.time()
    processor = None
    
    try:
        processor = HostDataProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        
        processor.process_all()
        processor.export()
        
        total_time = time.time() - start_time
        logger.info(f"\n✧˚ PROCESSING COMPLETE!")
        logger.info(f"⋆｡‧˚ Total execution time: {total_time:.2f} seconds")
        
    except KeyboardInterrupt:
        logger.warning("\n₊˚⊹ Processing interrupted by user")
    except Exception as e:
        logger.error(f"𐙚 Processing failed: {e}")
        import traceback
        logger.error(f"༘˚⋆ Full error traceback:\n{traceback.format_exc()}")
    finally:
        if processor:
            processor.close()

class HostDataProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        logger.info("🚀 Initializing CMDB Processor...")
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        logger.info("📋 Setting up column mappings...")
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
        
        logger.info("🔌 Connecting to BigQuery...")
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            logger.info(f"📝 Using service account file: {service_account_file}")
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
            logger.info("✅ BigQuery connected with service account")
        else:
            logger.warning(f"⚠️  Service account file not found: {service_account_file}")
            logger.info("🔄 Attempting default credentials...")
            self.bq_client = bigquery.Client(project="chronicle-fisv")
            logger.info("✅ BigQuery connected with default credentials")
        
        logger.info(f"🗄️  Connecting to DuckDB: {duckdb_path}")
        self.duck_conn = duckdb.connect(duckdb_path)
        logger.info("✅ DuckDB connected successfully")
        
        logger.info("🏗️  Creating database table...")
        self._create_table()
        logger.info("✅ Database table ready")
        
    def _create_table(self):
        logger.info("📊 Defining table schema...")
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
        
        logger.info("🔨 Executing table creation...")
        self.duck_conn.execute(sql)
        
        logger.info("🔍 Creating database indexes...")
        try:
            self.duck_conn.execute("CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)")
            logger.info("✅ Primary index created")
        except Exception as e:
            logger.warning(f"⚠️  Index creation skipped: {e}")
            
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
        logger.info(f"📖 Loading metadata from: {self.json_file_path}")
        start_time = time.time()
        
        try:
            with open(self.json_file_path, 'r') as f:
                metadata = json.load(f)
            
            load_time = time.time() - start_time
            logger.info(f"✅ Metadata loaded successfully in {load_time:.2f}s")
            
            if 'columns' in metadata:
                total_tables = len(metadata['columns'])
                total_columns = sum(len(columns) for columns in metadata['columns'].values())
                logger.info(f"📊 Found {total_tables} tables with {total_columns} total columns")
            else:
                logger.warning("⚠️  No 'columns' key found in metadata")
                
            return metadata
        except Exception as e:
            logger.error(f"❌ Failed to load metadata: {e}")
            raise
    
    def identify_columns(self, metadata):
        logger.info("🔍 Starting column identification process...")
        all_columns = []
        
        if 'columns' not in metadata:
            logger.error("❌ No 'columns' key found in metadata")
            return []
        
        table_count = len(metadata['columns'])
        logger.info(f"📋 Analyzing {table_count} tables for column patterns...")
        
        for table_idx, (table_name, columns) in enumerate(metadata['columns'].items(), 1):
            logger.info(f"🔍 [{table_idx}/{table_count}] Analyzing table: {table_name}")
            
            column_count = len(columns)
            matches_found = 0
            
            for column_name, column_type in columns.items():
                mapped_type = None
                match_reason = ""
                
                if isinstance(column_type, str) and column_type.lower() in self.column_mapping:
                    mapped_type = self.column_mapping[column_type.lower()]
                    match_reason = f"exact type match: '{column_type}'"
                
                if not mapped_type:
                    column_lower = column_name.lower()
                    for pattern in self.hostname_patterns:
                        if pattern in column_lower:
                            mapped_type = 'hostname'
                            match_reason = f"hostname pattern: '{pattern}'"
                            break
                
                if not mapped_type:
                    column_lower = column_name.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in column_lower:
                                mapped_type = attr_type
                                match_reason = f"attribute pattern: '{pattern}'"
                                break
                        if mapped_type:
                            break
                
                if not mapped_type and isinstance(column_type, str):
                    type_lower = column_type.lower()
                    for attr_type, patterns in self.attribute_patterns.items():
                        for pattern in patterns:
                            if pattern in type_lower:
                                mapped_type = attr_type
                                match_reason = f"type pattern: '{pattern}'"
                                break
                        if mapped_type:
                            break
                
                if mapped_type:
                    all_columns.append((table_name, column_name, mapped_type))
                    matches_found += 1
                    logger.info(f"  ✅ {column_name} -> {mapped_type} ({match_reason})")
                else:
                    logger.debug(f"  ❌ {column_name} ({column_type}) -> no match")
            
            logger.info(f"  📊 Table summary: {matches_found}/{column_count} columns matched")
        
        logger.info(f"🎯 Column identification complete: {len(all_columns)} total matches found")
        return all_columns
    
    def process_table_completely(self, table_name, all_columns_for_table):
        logger.info(f"\n🔄 Processing table: {table_name}")
        
        hostname_cols = [c for c in all_columns_for_table if c[2] == 'hostname']
        attribute_cols = [c for c in all_columns_for_table if c[2] != 'hostname']
        
        logger.info(f"  📋 Found {len(hostname_cols)} hostname columns, {len(attribute_cols)} attribute columns")
        
        for col in hostname_cols:
            logger.info(f"    🏠 Hostname: {col[1]} -> {col[2]}")
        for col in attribute_cols:
            logger.info(f"    📝 Attribute: {col[1]} -> {col[2]}")
        
        if not hostname_cols:
            logger.warning(f"  ⚠️  Skipping {table_name} - no hostname columns found")
            return
        
        hostname_col = hostname_cols[0][1]
        logger.info(f"  🎯 Using primary hostname column: {hostname_col}")
        
        column_names = [hostname_col] + [c[1] for c in attribute_cols]
        attribute_types = [c[2] for c in attribute_cols]
        
        logger.info(f"  📊 Query will select {len(column_names)} columns: {column_names}")
        
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in column_names])}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND LENGTH(`{hostname_col}`) > 0
        LIMIT 50000
        """
        
        logger.info(f"  🔍 Executing BigQuery for {table_name}...")
        start_time = time.time()
        
        try:
            query_job = self.bq_client.query(query)
            logger.info(f"    ⏳ Query submitted, waiting for results...")
            results = query_job.result()
            
            query_time = time.time() - start_time
            logger.info(f"    ✅ Query completed in {query_time:.2f}s")
            
            records = []
            attribute_data_found = {attr_type: 0 for attr_type in attribute_types}
            
            logger.info(f"    🔄 Processing query results...")
            row_count = 0
            
            for row in results:
                row_count += 1
                if row_count % 1000 == 0:
                    logger.info(f"      📊 Processed {row_count} rows...")
                    
                if row[0] and isinstance(row[0], str):
                    normalized_host = self.normalize_hostname(row[0])
                    if normalized_host and len(normalized_host) > 2:
                        record = {'normalized_host': normalized_host, 'hostname': row[0]}
                        
                        for i, attr_type in enumerate(attribute_types, 1):
                            if i < len(row) and row[i] and str(row[i]).strip():
                                record[attr_type] = str(row[i]).strip()
                                attribute_data_found[attr_type] += 1
                        
                        records.append(record)
            
            logger.info(f"    📊 Processing complete: {len(records)} valid host records found")
            
            for attr_type, count in attribute_data_found.items():
                if count > 0:
                    logger.info(f"      📝 {attr_type}: {count} non-empty values")
            
            logger.info(f"    💾 Writing {len(records)} records to database...")
            records_written = 0
            
            for i, record in enumerate(records):
                if i % 500 == 0 and i > 0:
                    logger.info(f"      💾 Written {i}/{len(records)} records...")
                    
                self._insert_or_update_host(record, table_name)
                records_written += 1
            
            logger.info(f"    ✅ Successfully wrote {records_written} records from {table_name}")
            
            logger.info(f"    🔍 Verifying data in database...")
            for attr_type in attribute_types:
                if attribute_data_found[attr_type] > 0:
                    count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {attr_type} IS NOT NULL AND {attr_type} != ''"
                    try:
                        db_count = self.duck_conn.execute(count_query).fetchone()[0]
                        logger.info(f"      ✅ {attr_type}: {db_count} records confirmed in database")
                    except Exception as e:
                        logger.warning(f"      ⚠️  Could not verify {attr_type}: {e}")
            
        except Exception as e:
            logger.error(f"  ❌ Error processing {table_name}: {e}")
            import traceback
            logger.error(f"  🔍 Full traceback: {traceback.format_exc()}")
    
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
        logger.info("🚀 Starting complete CMDB processing...")
        
        logger.info("📖 Step 1: Loading metadata...")
        metadata = self.load_metadata()
        
        logger.info("🔍 Step 2: Identifying relevant columns...")
        all_columns = self.identify_columns(metadata)
        
        if not all_columns:
            logger.error("❌ No columns found to process!")
            return
        
        logger.info("📊 Step 3: Grouping columns by table...")
        columns_by_table = defaultdict(list)
        for table_name, column_name, mapped_type in all_columns:
            columns_by_table[table_name].append((table_name, column_name, mapped_type))
        
        total_tables = len(columns_by_table)
        logger.info(f"🎯 Found {total_tables} tables to process")
        
        logger.info("🔄 Step 4: Processing each table...")
        for table_idx, (table_name, table_columns) in enumerate(columns_by_table.items(), 1):
            logger.info(f"\n📋 [{table_idx}/{total_tables}] Starting table: {table_name}")
            start_time = time.time()
            
            self.process_table_completely(table_name, table_columns)
            
            process_time = time.time() - start_time
            logger.info(f"⏱️  Table {table_name} completed in {process_time:.2f}s")
        
        logger.info("📊 Step 5: Creating summary tables...")
        self._create_summary()
        
        logger.info("🎯 Step 6: Generating final results...")
        self._show_results()
        
        logger.info("✅ Complete CMDB processing finished!")
    
    def _create_summary(self):
        logger.info("🔄 Creating summary table...")
        try:
            logger.info("  🗑️  Dropping existing summary table...")
            self.duck_conn.execute("DROP TABLE IF EXISTS all_sources")
            
            logger.info("  🏗️  Building new summary table...")
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
            logger.info("  ✅ Summary table created successfully")
        except Exception as e:
            logger.error(f"  ❌ Summary table creation failed: {e}")
    
    def _show_results(self):
        logger.info("📊 Generating final verification report...")
        
        total_query = "SELECT COUNT(*) FROM universal_cmdb"
        total = self.duck_conn.execute(total_query).fetchone()[0]
        logger.info(f"🏠 Total hosts in database: {total:,}")
        
        columns = ['hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
                  'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
                  'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage', 
                  'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso']
        
        logger.info("🔍 Column population verification:")
        populated_columns = []
        empty_columns = []
        
        for col in columns:
            count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            count = self.duck_conn.execute(count_query).fetchone()[0]
            pct = (count / total * 100) if total > 0 else 0
            
            if count > 0:
                populated_columns.append(col)
                logger.info(f"  ✅ {col}: {count:,} records ({pct:.1f}%)")
                
                sample_query = f"SELECT DISTINCT {col} FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != '' LIMIT 3"
                samples = self.duck_conn.execute(sample_query).fetchall()
                sample_values = [str(s[0])[:30] for s in samples]
                logger.info(f"     📋 Samples: {', '.join(sample_values)}")
            else:
                empty_columns.append(col)
                logger.warning(f"  ❌ {col}: 0 records (empty)")
        
        logger.info(f"\n🎉 SUCCESS SUMMARY:")
        logger.info(f"  ✅ Columns with data: {len(populated_columns)}")
        logger.info(f"  ❌ Empty columns: {len(empty_columns)}")
        
        if populated_columns:
            logger.info(f"  🎯 Populated columns: {', '.join(populated_columns)}")
        
        if empty_columns:
            logger.warning(f"  ⚠️  Empty columns: {', '.join(empty_columns)}")
        
        logger.info("📋 Sample complete records:")
        sample_query = """
        SELECT * FROM universal_cmdb 
        WHERE normalized_host IS NOT NULL
        ORDER BY (
            CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 ELSE 0 END +
            CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 ELSE 0 END +
            CASE WHEN region IS NOT NULL AND region != '' THEN 1 ELSE 0 END +
            CASE WHEN infrastructure_type IS NOT NULL AND infrastructure_type != '' THEN 1 ELSE 0 END
        ) DESC
        LIMIT 3
        """
        samples = self.duck_conn.execute(sample_query).fetchall()
        
        column_names = ['normalized_host', 'source_tables'] + columns + ['last_updated', 'created_at']
        
        for i, sample in enumerate(samples, 1):
            logger.info(f"  📄 Record {i}: {sample[0]}")
            fields_with_data = 0
            for j, col_name in enumerate(column_names[1:], 1):
                if j < len(sample) and sample[j] and str(sample[j]).strip() and col_name not in ['last_updated', 'created_at']:
                    logger.info(f"    • {col_name}: {str(sample[j])[:50]}")
                    fields_with_data += 1
            logger.info(f"    📊 Total populated fields: {fields_with_data}")
    
    def export(self, filename="universal_cmdb_export.csv"):
        logger.info(f"📤 Exporting data to {filename}...")
        try:
            self.duck_conn.execute(f"COPY (SELECT * FROM universal_cmdb ORDER BY normalized_host) TO '{filename}' WITH (FORMAT CSV, HEADER)")
            logger.info(f"✅ Export completed: {filename}")
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
    
    def close(self):
        logger.info("🔌 Closing database connections...")
        try:
            self.duck_conn.close()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.warning(f"⚠️  Error closing connections: {e}")

if __name__ == "__main__":
    logger.info("🌟 UNIVERSAL CMDB PROCESSOR STARTING")
    logger.info("=" * 60)
    
    start_time = time.time()
    processor = None
    
    try:
        processor = HostDataProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        
        processor.process_all()
        processor.export()
        
        total_time = time.time() - start_time
        logger.info(f"\n🎉 PROCESSING COMPLETE!")
        logger.info(f"⏱️  Total execution time: {total_time:.2f} seconds")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Processing interrupted by user")
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        import traceback
        logger.error(f"🔍 Full error traceback:\n{traceback.format_exc()}")
    finally:
        if processor:
            processor.close()

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
        
        print(f"\n=== PROCESSING TABLE: {table_name} ===")
        print(f"Hostname columns: {len(hostname_cols)}")
        print(f"Attribute columns: {len(attribute_cols)}")
        
        for col in hostname_cols:
            print(f"  Hostname: {col[1]} -> {col[2]}")
        for col in attribute_cols:
            print(f"  Attribute: {col[1]} -> {col[2]}")
        
        if not hostname_cols:
            print(f"  ❌ SKIPPING {table_name} - No hostname columns found")
            return
        
        hostname_col = hostname_cols[0][1]
        
        column_names = [hostname_col] + [c[1] for c in attribute_cols]
        attribute_types = [c[2] for c in attribute_cols]
        
        print(f"  Query columns: {column_names}")
        print(f"  Target types: ['hostname'] + {attribute_types}")
        
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in column_names])}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND LENGTH(`{hostname_col}`) > 0
        LIMIT 50000
        """
        
        try:
            print(f"  🔍 Executing BigQuery...")
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            records = []
            attribute_data_found = {attr_type: 0 for attr_type in attribute_types}
            
            for row in results:
                if row[0] and isinstance(row[0], str):
                    normalized_host = self.normalize_hostname(row[0])
                    if normalized_host and len(normalized_host) > 2:
                        record = {'normalized_host': normalized_host, 'hostname': row[0]}
                        
                        for i, attr_type in enumerate(attribute_types, 1):
                            if i < len(row) and row[i] and str(row[i]).strip():
                                record[attr_type] = str(row[i]).strip()
                                attribute_data_found[attr_type] += 1
                        
                        records.append(record)
            
            print(f"  📊 Data found:")
            print(f"    Total records: {len(records)}")
            for attr_type, count in attribute_data_found.items():
                print(f"    {attr_type}: {count} non-empty values")
            
            records_written = 0
            for record in records:
                self._insert_or_update_host(record, table_name)
                records_written += 1
                
            print(f"  ✅ Successfully processed {records_written} records from {table_name}")
            
            # VERIFICATION: Check if data actually made it to the database
            print(f"  🔍 VERIFICATION - Checking database...")
            for attr_type in attribute_types:
                count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {attr_type} IS NOT NULL AND {attr_type} != ''"
                db_count = self.duck_conn.execute(count_query).fetchone()[0]
                print(f"    {attr_type}: {db_count} records in database")
            
        except Exception as e:
            print(f"  ❌ Error processing {table_name}: {e}")
            import traceback
            traceback.print_exc()
    
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
        
        print("\n=== COLUMN VERIFICATION ===")
        populated_columns = []
        empty_columns = []
        
        for col in columns:
            count = self.duck_conn.execute(f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
            pct = (count / total * 100) if total > 0 else 0
            
            if count > 0:
                populated_columns.append(col)
                print(f"✅ VERIFIED: {col} has {count} records ({pct:.1f}%)")
                
                # Show sample values
                sample_query = f"SELECT DISTINCT {col} FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != '' LIMIT 3"
                samples = self.duck_conn.execute(sample_query).fetchall()
                sample_values = [str(s[0])[:30] for s in samples]
                print(f"   Sample values: {', '.join(sample_values)}")
            else:
                empty_columns.append(col)
                print(f"❌ EMPTY: {col} has no data")
        
        print(f"\n📊 VERIFICATION SUMMARY:")
        print(f"   ✅ Columns with data: {len(populated_columns)}")
        print(f"   ❌ Empty columns: {len(empty_columns)}")
        
        if populated_columns:
            print(f"   🎉 SUCCESS: Data verified in: {', '.join(populated_columns)}")
        
        if empty_columns:
            print(f"   ⚠️  WARNING: No data found in: {', '.join(empty_columns)}")
        
        print("\nSample complete records:")
        sample_query = """
        SELECT * FROM universal_cmdb 
        WHERE normalized_host IS NOT NULL
        ORDER BY (
            CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 ELSE 0 END +
            CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 ELSE 0 END +
            CASE WHEN region IS NOT NULL AND region != '' THEN 1 ELSE 0 END +
            CASE WHEN infrastructure_type IS NOT NULL AND infrastructure_type != '' THEN 1 ELSE 0 END
        ) DESC
        LIMIT 3
        """
        samples = self.duck_conn.execute(sample_query).fetchall()
        
        column_names = ['normalized_host', 'source_tables'] + columns + ['last_updated', 'created_at']
        
        for i, sample in enumerate(samples, 1):
            print(f"\nRecord {i}: {sample[0]}")
            fields_with_data = 0
            for j, col_name in enumerate(column_names[1:], 1):
                if j < len(sample) and sample[j] and str(sample[j]).strip() and col_name not in ['last_updated', 'created_at']:
                    print(f"  {col_name}: {str(sample[j])[:50]}")
                    fields_with_data += 1
            print(f"  📈 Total fields populated: {fields_with_data}")
    
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