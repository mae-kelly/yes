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

class OptimizedCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        print("\n\n")
        print("═" * 80)
        print("                    ₊˚✩ CMDB PROCESSOR INITIALIZATION ✩˚₊")
        print("═" * 80)
        print()
        
        logger.info("Starting initialization process...")
        print()
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        
        logger.info("༘˚⋆ Setting up column mapping dictionaries")
        print("   Building comprehensive attribute patterns...")
        print()
        
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
        
        self.hostname_patterns = [
            'host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name',
            'endpoint_name', 'splunk_host', 'app_host', 'computer_name', 'machine_name',
            'chronicle_device_hostname', 'endpointdomain_name', 'asset_name'
        ]
        
        self.advanced_patterns = {
            'business_unit': [
                'business_unit', 'bu', 'business', 'department', 'division', 'org_unit',
                'organizational_unit', 'cost_center', 'business_group', 'dept', 'organization'
            ],
            'region': [
                'region', 'location', 'site', 'area', 'zone', 'geographic_region',
                'geo_region', 'datacenter_region', 'site_location', 'geographical_location'
            ],
            'country': [
                'country', 'nation', 'country_code', 'geo_country', 'location_country'
            ],
            'infrastructure_type': [
                'infrastructure_type', 'infra_type', 'server_type', 'system_type',
                'platform', 'environment', 'env', 'deployment_type', 'platform_type',
                'os_type', 'system_platform'
            ],
            'data_center': [
                'datacenter', 'data_center', 'dc', 'facility', 'center', 'site_name',
                'datacenter_name', 'facility_name', 'dc_location'
            ],
            'cloud_region': [
                'cloud_region', 'aws_region', 'azure_region', 'gcp_region',
                'cloud_location', 'cloud_zone', 'availability_zone'
            ],
            'ip_address': [
                'ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip', 'server_ip',
                'endpoint_ip', 'device_ip', 'internal_ip', 'external_ip', 'primary_ip'
            ],
            'class': [
                'class', 'classification', 'tier', 'level', 'grade', 'category',
                'server_class', 'system_class'
            ],
            'system_classification': [
                'system_classification', 'security_classification', 'data_classification',
                'classification_level', 'sensitivity', 'security_level'
            ],
            'apm': [
                'apm', 'monitoring', 'application_monitoring', 'performance_monitoring',
                'apm_enabled', 'monitoring_enabled'
            ],
            'cio': [
                'cio', 'owner', 'responsible', 'contact', 'admin', 'administrator',
                'system_owner', 'business_owner', 'technical_owner'
            ],
            'edr_coverage': [
                'edr_coverage', 'edr', 'endpoint_detection', 'security_agent',
                'antivirus', 'av_coverage', 'endpoint_protection'
            ],
            'tanium_coverage': [
                'tanium_coverage', 'tanium', 'tanium_agent', 'endpoint_management'
            ],
            'dlp_agent_coverage': [
                'dlp_agent_coverage', 'dlp', 'data_loss_prevention', 'dlp_agent'
            ],
            'logging_in_splunk': [
                'logging_in_splunk', 'splunk', 'splunk_logging', 'log_forwarding'
            ],
            'logging_in_gso': [
                'logging_in_gso', 'gso', 'gso_logging', 'security_logging'
            ],
            'domain': [
                'domain', 'dns_domain', 'ad_domain', 'windows_domain'
            ],
            'fqdn': [
                'fqdn', 'full_name', 'qualified_name', 'dns_name', 'fully_qualified'
            ]
        }
        
        self.stats = {
            'tables_processed': 0,
            'columns_discovered': 0,
            'hosts_created': 0,
            'hosts_updated': 0,
            'total_records_processed': 0,
            'processing_errors': 0
        }
        
        print("   ♡ Pattern dictionaries configured")
        print()
        
        logger.info("𖦹 Establishing BigQuery connection")
        self._init_bigquery()
        print()
        
        logger.info("⋆｡‧˚ Establishing DuckDB connection")
        self.duck_conn = duckdb.connect(duckdb_path)
        print("   Database file:", duckdb_path)
        print()
        
        logger.info("༘˚⋆ Creating optimized database schema")
        self._create_optimized_table()
        print("   Schema with 25 columns and indexes created")
        print()
        
        print("─" * 60)
        print("                ♡ Initialization Complete ♡")
        print("─" * 60)
        print("\n\n")
        
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            logger.info(f"   Using service account authentication")
            print(f"   File: {service_account_file}")
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
            print("   ✧˚ Authentication successful")
        else:
            logger.info("   Using default BigQuery credentials")
            self.bq_client = bigquery.Client(project="chronicle-fisv")
            print("   ♡ Connected with default credentials")
            
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
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_business_unit ON universal_cmdb(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)",
            "CREATE INDEX IF NOT EXISTS idx_infrastructure_type ON universal_cmdb(infrastructure_type)",
            "CREATE INDEX IF NOT EXISTS idx_source_count ON universal_cmdb(source_count)"
        ]
        
        for index_sql in indexes:
            try:
                self.duck_conn.execute(index_sql)
            except:
                pass
                
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str) or hostname.strip() == '*Undefined':
            return ""
        
        normalized = hostname.lower().strip()
        
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        normalized = normalized.replace('-', '')
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized if len(normalized) > 1 else ""
    
    def is_valid_value(self, value) -> bool:
        if not value:
            return False
        if isinstance(value, str):
            stripped = value.strip()
            return stripped != '' and stripped != '*Undefined' and stripped.lower() not in ['null', 'none', 'undefined']
        return True
    
    def load_metadata(self) -> Dict:
        print("\n")
        print("═" * 80)
        print("                      ₊˚✩ METADATA LOADING ✩˚₊")
        print("═" * 80)
        print()
        
        logger.info(f"Loading metadata file...")
        print(f"   Source: {self.json_file_path}")
        print()
        
        start_time = time.time()
        
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        
        load_time = time.time() - start_time
        
        if 'columns' in metadata:
            table_count = len(metadata['columns'])
            column_count = sum(len(cols) for cols in metadata['columns'].values())
            
            print(f"   ♡ Successfully loaded in {load_time:.2f} seconds")
            print()
            print(f"   Tables found: {table_count:,}")
            print(f"   Total columns: {column_count:,}")
            print()
        else:
            print("   ₊˚⊹ Warning: Metadata missing 'columns' key")
            print()
        
        print("─" * 60)
        print("              ✧˚ Metadata Loading Complete ✧˚")
        print("─" * 60)
        print("\n\n")
            
        return metadata
    
    def discover_columns_comprehensive(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        print("═" * 80)
        print("                   ༘˚⋆ COLUMN DISCOVERY ⋆˚༘")
        print("═" * 80)
        print()
        
        logger.info("Starting comprehensive column analysis...")
        print("   Using advanced pattern matching across all table columns")
        print()
        
        discovered_columns = []
        
        if 'columns' not in metadata:
            print("   𖦹 Error: No columns found in metadata structure")
            return []
        
        table_count = len(metadata['columns'])
        print(f"   Analyzing {table_count} tables for relevant data...")
        print()
        
        for table_idx, (table_name, columns) in enumerate(metadata['columns'].items(), 1):
            print(f"   Table {table_idx:2d}/{table_count}: {table_name}")
            
            table_matches = 0
            
            for column_name, column_type in columns.items():
                mapped_type = self._identify_column_type(column_name, column_type)
                
                if mapped_type:
                    discovered_columns.append((table_name, column_name, mapped_type))
                    table_matches += 1
                    
                    match_reason = self._get_match_reason(column_name, column_type, mapped_type)
                    print(f"      ♡ {column_name} → {mapped_type}")
                    print(f"         ({match_reason})")
            
            if table_matches > 0:
                print(f"      𖦹 Found {table_matches} relevant columns")
            else:
                print(f"      ₊˚⊹ No relevant columns found")
            print()
        
        self.stats['columns_discovered'] = len(discovered_columns)
        
        print("─" * 60)
        print(f"         ✧˚ Discovery Complete: {len(discovered_columns)} Columns ✧˚")
        print("─" * 60)
        print("\n\n")
        
        return discovered_columns
    
    def _identify_column_type(self, column_name: str, column_type) -> Optional[str]:
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
    
    def _get_match_reason(self, column_name: str, column_type, mapped_type: str) -> str:
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        if isinstance(column_type, str) and type_lower in self.column_mapping:
            return f"exact type match: '{column_type}'"
        
        if mapped_type == 'hostname':
            for pattern in self.hostname_patterns:
                if pattern in column_lower:
                    return f"hostname pattern: '{pattern}'"
        
        for target_type, patterns in self.advanced_patterns.items():
            if target_type == mapped_type:
                for pattern in patterns:
                    if pattern in column_lower:
                        return f"column name pattern: '{pattern}'"
                    if pattern in type_lower:
                        return f"column type pattern: '{pattern}'"
        
        return "advanced pattern match"
    
    def process_table_optimized(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        print("─" * 70)
        print(f"   Processing: {table_name}")
        print("─" * 70)
        print()
        
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            print("   ₊˚⊹ Skipping table - no hostname columns detected")
            print()
            return 0
        
        primary_hostname_col = hostname_cols[0][0]
        print(f"   Primary hostname column: {primary_hostname_col}")
        print()
        
        if attribute_cols:
            print(f"   Attribute columns ({len(attribute_cols)}):")
            for col, ctype in attribute_cols:
                print(f"      ♡ {col} → {ctype}")
            print()
        
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        query = self._build_comprehensive_query(table_name, all_columns, primary_hostname_col)
        
        print("   ⋆｡‧˚ Executing comprehensive BigQuery...")
        start_time = time.time()
        
        try:
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            query_time = time.time() - start_time
            print(f"   Query completed in {query_time:.2f} seconds")
            print()
            
            records_processed = self._process_query_results(results, table_name, primary_hostname_col, attribute_types)
            
            print(f"   ✧˚ Table processing complete")
            print(f"      Total records: {records_processed:,}")
            print()
            
            return records_processed
            
        except Exception as e:
            print(f"   𖦹 Query execution failed")
            print(f"      Error: {str(e)[:100]}...")
            print()
            self.stats['processing_errors'] += 1
            return 0
    
    def _build_comprehensive_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        column_selects = []
        for col in columns:
            column_selects.append(f"`{col}`")
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND `{hostname_col}` != '*Undefined'
        AND LENGTH(`{hostname_col}`) > 0
        """
    
    def _process_query_results(self, results, table_name: str, hostname_col: str, attribute_types: List[str]) -> int:
        print("   ༘˚⋆ Processing query results...")
        print()
        
        records_processed = 0
        hosts_created = 0
        hosts_updated = 0
        attribute_stats = {attr_type: 0 for attr_type in attribute_types}
        
        batch_records = []
        batch_size = 1000
        
        for row_idx, row in enumerate(results):
            records_processed += 1
            
            if records_processed % 10000 == 0:
                print(f"      Processing: {records_processed:,} rows...")
            
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
            
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and self.is_valid_value(row[i]):
                    record_data[attr_type] = str(row[i]).strip()
                    attribute_stats[attr_type] += 1
            
            batch_records.append(record_data)
            
            if len(batch_records) >= batch_size:
                created, updated = self._process_record_batch(batch_records)
                hosts_created += created
                hosts_updated += updated
                batch_records.clear()
        
        if batch_records:
            created, updated = self._process_record_batch(batch_records)
            hosts_created += created
            hosts_updated += updated
        
        print()
        print("   Results Summary:")
        print(f"      ♡ Records processed: {records_processed:,}")
        print(f"      ⋆｡‧˚ New hosts created: {hosts_created:,}")
        print(f"      𖦹 Existing hosts updated: {hosts_updated:,}")
        print()
        
        if attribute_stats:
            print("   Attribute Data Found:")
            for attr_type, count in attribute_stats.items():
                if count > 0:
                    print(f"      ♡ {attr_type}: {count:,} values")
            print()
        
        self.stats['total_records_processed'] += records_processed
        self.stats['hosts_created'] += hosts_created
        self.stats['hosts_updated'] += hosts_updated
        
        return records_processed
    
    def _process_record_batch(self, batch_records: List[Dict]) -> Tuple[int, int]:
        hosts_created = 0
        hosts_updated = 0
        
        for record in batch_records:
            if self._insert_or_update_optimized(record):
                hosts_created += 1
            else:
                hosts_updated += 1
        
        return hosts_created, hosts_updated
    
    def _insert_or_update_optimized(self, record: Dict) -> bool:
        normalized_host = record['normalized_host']
        table_name = record['table_name']
        
        existing_query = """
        SELECT source_tables, data_quality_score, source_count,
               hostname, fqdn, domain, infrastructure_type, region, country, data_center,
               cloud_region, ip_address, class, system_classification, business_unit,
               apm, cio, edr_coverage, tanium_coverage, dlp_agent_coverage,
               logging_in_splunk, logging_in_gso
        FROM universal_cmdb WHERE normalized_host = ?
        """
        
        existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
        
        if existing:
            return self._update_existing_host(normalized_host, record, existing)
        else:
            return self._create_new_host(record)
    
    def _update_existing_host(self, normalized_host: str, record: Dict, existing) -> bool:
        updates = []
        values = []
        
        current_tables = existing[0] if existing[0] else ""
        table_name = record['table_name']
        
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            
            new_source_count = (existing[2] or 0) + 1
            updates.append("source_count = ?")
            values.append(new_source_count)
        
        column_names = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for i, col_name in enumerate(column_names, 3):
            if col_name in record:
                new_value = record[col_name]
                existing_value = existing[i] if i < len(existing) and existing[i] else None
                
                final_value = self._merge_values(existing_value, new_value)
                
                if final_value != existing_value:
                    updates.append(f"{col_name} = ?")
                    values.append(final_value)
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            self.duck_conn.execute(update_sql, values)
        
        return False
    
    def _create_new_host(self, record: Dict) -> bool:
        columns = ['normalized_host', 'source_tables', 'source_count']
        values = [record['normalized_host'], record['table_name'], 1]
        
        data_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for col in data_columns:
            columns.append(col)
            values.append(record.get(col))
        
        placeholders = ', '.join(['?' for _ in values])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        self.duck_conn.execute(insert_sql, values)
        return True
    
    def _merge_values(self, existing_value: Optional[str], new_value: str) -> str:
        if not existing_value or existing_value.strip() == '':
            return new_value
        
        if not new_value or new_value.strip() == '':
            return existing_value
        
        existing_parts = set(part.strip() for part in existing_value.split('|'))
        new_part = new_value.strip()
        
        if new_part not in existing_parts:
            existing_parts.add(new_part)
            return ' | '.join(sorted(existing_parts))
        
        return existing_value
    
    def create_comprehensive_summary(self):
        print("\n")
        print("═" * 80)
        print("                  ⋆｡‧˚ SUMMARY CREATION ˚‧｡⋆")
        print("═" * 80)
        print()
        
        logger.info("Creating comprehensive analysis tables...")
        print("   Building summary views for data analysis")
        print()
        
        try:
            self.duck_conn.execute("DROP TABLE IF EXISTS all_sources")
            self.duck_conn.execute("DROP TABLE IF EXISTS data_quality_summary")
            self.duck_conn.execute("DROP TABLE IF EXISTS coverage_analysis")
            
            all_sources_sql = """
            CREATE TABLE all_sources AS (
                SELECT 
                    normalized_host as host,
                    source_tables,
                    source_count,
                    data_quality_score,
                    hostname, fqdn, domain, infrastructure_type, region, country,
                    data_center, cloud_region, ip_address, class, system_classification,
                    business_unit, apm, cio, edr_coverage, tanium_coverage, 
                    dlp_agent_coverage, logging_in_splunk, logging_in_gso,
                    first_seen, last_updated
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                ORDER BY source_count DESC, data_quality_score DESC, normalized_host
            )
            """
            
            quality_summary_sql = """
            CREATE TABLE data_quality_summary AS (
                SELECT 
                    'hostname' as column_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) as populated_records,
                    ROUND(COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) * 100.0 / COUNT(*), 2) as population_percentage
                FROM universal_cmdb
                
                UNION ALL
                
                SELECT 'business_unit', COUNT(*), COUNT(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 END),
                       ROUND(COUNT(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 END) * 100.0 / COUNT(*), 2)
                FROM universal_cmdb
                
                UNION ALL
                
                SELECT 'region', COUNT(*), COUNT(CASE WHEN region IS NOT NULL AND region != '' THEN 1 END),
                       ROUND(COUNT(CASE WHEN region IS NOT NULL AND region != '' THEN 1 END) * 100.0 / COUNT(*), 2)
                FROM universal_cmdb
                
                ORDER BY population_percentage DESC
            )
            """
            
            self.duck_conn.execute(all_sources_sql)
            self.duck_conn.execute(quality_summary_sql)
            
            print("   ♡ Summary tables created successfully")
            print("   ⋆｡‧˚ Data quality metrics calculated")
            print()
            
        except Exception as e:
            print(f"   𖦹 Summary creation encountered an error:")
            print(f"      {str(e)[:100]}...")
            print()
    
    def generate_comprehensive_report(self):
        print("\n")
        print("═" * 80)
        print("                 ₊˚✩ COMPREHENSIVE REPORT ✩˚₊")
        print("═" * 80)
        print()
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        print(f"   Total Unique Hosts Discovered: {total_hosts:,}")
        print()
        
        columns_to_check = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        print("   Column Population Analysis:")
        print("   " + "─" * 50)
        print()
        
        populated_columns = []
        empty_columns = []
        
        for col in columns_to_check:
            count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            count = self.duck_conn.execute(count_query).fetchone()[0]
            percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
            
            if count > 0:
                populated_columns.append(col)
                print(f"   ♡ {col}")
                print(f"      Records: {count:,} ({percentage:.1f}% coverage)")
                
                sample_query = f"SELECT DISTINCT {col} FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != '' LIMIT 3"
                samples = self.duck_conn.execute(sample_query).fetchall()
                sample_values = [str(s[0])[:25] for s in samples]
                print(f"      Examples: {', '.join(sample_values)}")
                print()
            else:
                empty_columns.append(col)
                print(f"   ₊˚⊹ {col}: No data found")
                print()
        
        print("\n")
        print("   Processing Statistics:")
        print("   " + "─" * 30)
        print()
        print(f"   ♡ Tables processed: {self.stats['tables_processed']}")
        print(f"   𖦹 Columns analyzed: {self.stats['columns_discovered']}")
        print(f"   ⋆｡‧˚ Records processed: {self.stats['total_records_processed']:,}")
        print(f"   ༘˚⋆ New hosts created: {self.stats['hosts_created']:,}")
        print(f"   ₊˚✩ Existing hosts updated: {self.stats['hosts_updated']:,}")
        
        if self.stats['processing_errors'] > 0:
            print(f"   ₊˚⊹ Processing errors encountered: {self.stats['processing_errors']}")
        print()
        
        print("\n")
        print("   Success Summary:")
        print("   " + "─" * 20)
        print()
        print(f"   ♡ Columns with data: {len(populated_columns)}")
        print(f"   ₊˚⊹ Empty columns: {len(empty_columns)}")
        print()
        
        if populated_columns:
            print(f"   ✧˚ Successfully populated:")
            chunk_size = 5
            for i in range(0, len(populated_columns), chunk_size):
                chunk = populated_columns[i:i+chunk_size]
                print(f"      {', '.join(chunk)}")
            print()
        
        print("   Sample Enriched Records:")
        print("   " + "─" * 30)
        print()
        
        sample_query = """
        SELECT * FROM universal_cmdb 
        WHERE normalized_host IS NOT NULL
        ORDER BY source_count DESC, data_quality_score DESC
        LIMIT 3
        """
        
        samples = self.duck_conn.execute(sample_query).fetchall()
        column_names = [
            'normalized_host', 'source_tables', 'hostname', 'fqdn', 'domain',
            'infrastructure_type', 'region', 'country', 'data_center', 'cloud_region',
            'ip_address', 'class', 'system_classification', 'business_unit', 'apm',
            'cio', 'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage',
            'logging_in_splunk', 'logging_in_gso'
        ]
        
        for i, sample in enumerate(samples, 1):
            print(f"   Record {i}: {sample[0]}")
            populated_fields = 0
            for j, col_name in enumerate(column_names[1:], 1):
                if j < len(sample) and sample[j] and str(sample[j]).strip():
                    if col_name not in ['data_quality_score', 'source_count', 'first_seen', 'last_updated', 'created_at']:
                        print(f"      ♡ {col_name}: {str(sample[j])[:40]}")
                        populated_fields += 1
            print(f"      𖦹 Total populated fields: {populated_fields}")
            print()
        
        print("─" * 60)
        print("              ✧˚ Report Generation Complete ✧˚")
        print("─" * 60)
        print("\n\n")
    
    def export_comprehensive(self, filename: str = "universal_cmdb_export.csv"):
        print("═" * 80)
        print("                    ༘˚⋆ DATA EXPORT ⋆˚༘")
        print("═" * 80)
        print()
        
        logger.info(f"Exporting comprehensive dataset...")
        print(f"   Output file: {filename}")
        print()
        
        try:
            export_query = f"""
            COPY (
                SELECT * FROM universal_cmdb 
                ORDER BY source_count DESC, data_quality_score DESC, normalized_host
            ) TO '{filename}' WITH (FORMAT CSV, HEADER)
            """
            self.duck_conn.execute(export_query)
            
            print("   ✧˚ Export completed successfully")
            print("   ♡ Data sorted by source count and quality score")
            print()
            
        except Exception as e:
            print(f"   𖦹 Export encountered an error:")
            print(f"      {str(e)[:100]}...")
            print()
    
    def process_all_comprehensive(self):
        print("\n\n")
        print("═" * 80)
        print("              ₊˚✩ COMPREHENSIVE PROCESSING START ✩˚₊")
        print("═" * 80)
        print()
        
        start_time = time.time()
        
        metadata = self.load_metadata()
        discovered_columns = self.discover_columns_comprehensive(metadata)
        
        if not discovered_columns:
            print("   𖦹 Error: No processable columns discovered")
            print("   Unable to continue with processing")
            print()
            return
        
        print("═" * 80)
        print("                    ⋆｡‧˚ TABLE PROCESSING ˚‧｡⋆")
        print("═" * 80)
        print()
        
        logger.info("Organizing discovered columns by source table...")
        columns_by_table = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((table_name, column_name, column_type))
        
        table_count = len(columns_by_table)
        print(f"   Tables to process: {table_count}")
        print()
        
        for table_idx, (table_name, table_columns) in enumerate(columns_by_table.items(), 1):
            print(f"\n   [{table_idx:2d} of {table_count}]")
            
            table_start = time.time()
            records_processed = self.process_table_optimized(table_name, table_columns)
            table_time = time.time() - table_start
            
            print(f"   ✧˚ Table completed in {table_time:.2f} seconds")
            print(f"      Records processed: {records_processed:,}")
            self.stats['tables_processed'] += 1
            print()
        
        self.create_comprehensive_summary()
        self.generate_comprehensive_report()
        
        total_time = time.time() - start_time
        
        print("═" * 80)
        print("                ₊˚✩ PROCESSING COMPLETE ✩˚₊")
        print("═" * 80)
        print()
        print(f"   Total execution time: {total_time:.2f} seconds")
        print(f"   Average time per table: {total_time/max(1, self.stats['tables_processed']):.2f} seconds")
        print()
        print("   ♡ All data successfully integrated into universal CMDB")
        print()
    
    def close_connections(self):
        print("\n")
        print("═" * 80)
        print("                   ༘˚⋆ SESSION CLEANUP ⋆˚༘")
        print("═" * 80)
        print()
        
        logger.info("Closing database connections...")
        try:
            self.duck_conn.close()
            print("   ♡ Database connections closed successfully")
            print("   ✧˚ Session cleanup complete")
        except Exception as e:
            print(f"   ₊˚⊹ Warning during cleanup: {e}")
        print()

if __name__ == "__main__":
    print("\n\n")
    print("═" * 90)
    print("                   ₊˚✩ OPTIMIZED UNIVERSAL CMDB PROCESSOR ✩˚₊")
    print("═" * 90)
    print()
    print("   A comprehensive system for discovering, analyzing, and")
    print("   integrating host data from multiple BigQuery sources")
    print()
    print("═" * 90)
    
    processor = None
    
    try:
        processor = OptimizedCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        
        processor.process_all_comprehensive()
        processor.export_comprehensive("universal_cmdb_complete.csv")
        
        print("\n\n")
        print("═" * 90)
        print("                      ✧˚ PROCESSING COMPLETE ✧˚")
        print("═" * 90)
        print()
        print("   Your universal CMDB has been successfully created and populated")
        print("   with comprehensive host data from all discovered sources.")
        print()
        print("   Database file: universal_cmdb.db")
        print("   Export file: universal_cmdb_complete.csv")
        print()
        print("═" * 90)
        print()
        
    except KeyboardInterrupt:
        print("\n\n")
        print("═" * 80)
        print("                     ₊˚⊹ USER INTERRUPTION ⊹˚₊")
        print("═" * 80)
        print()
        print("   Processing was interrupted by user request.")
        print("   Partial data may have been saved to the database.")
        print()
        
    except Exception as e:
        print("\n\n")
        print("═" * 80)
        print("                        𖦹 ERROR OCCURRED 𖦹")
        print("═" * 80)
        print()
        print("   An error occurred during processing:")
        print(f"   {str(e)[:100]}...")
        print()
        import traceback
        print("   Detailed error information:")
        for line in traceback.format_exc().split('\n')[:10]:
            if line.strip():
                print(f"   {line}")
        print()
        
    finally:
        if processor:
            processor.close_connections()
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
        
        self.hostname_patterns = [
            'host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name',
            'endpoint_name', 'splunk_host', 'app_host', 'computer_name', 'machine_name',
            'chronicle_device_hostname', 'endpointdomain_name', 'asset_name'
        ]
        
        self.advanced_patterns = {
            'business_unit': [
                'business_unit', 'bu', 'business', 'department', 'division', 'org_unit',
                'organizational_unit', 'cost_center', 'business_group', 'dept', 'organization'
            ],
            'region': [
                'region', 'location', 'site', 'area', 'zone', 'geographic_region',
                'geo_region', 'datacenter_region', 'site_location', 'geographical_location'
            ],
            'country': [
                'country', 'nation', 'country_code', 'geo_country', 'location_country'
            ],
            'infrastructure_type': [
                'infrastructure_type', 'infra_type', 'server_type', 'system_type',
                'platform', 'environment', 'env', 'deployment_type', 'platform_type',
                'os_type', 'system_platform'
            ],
            'data_center': [
                'datacenter', 'data_center', 'dc', 'facility', 'center', 'site_name',
                'datacenter_name', 'facility_name', 'dc_location'
            ],
            'cloud_region': [
                'cloud_region', 'aws_region', 'azure_region', 'gcp_region',
                'cloud_location', 'cloud_zone', 'availability_zone'
            ],
            'ip_address': [
                'ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip', 'server_ip',
                'endpoint_ip', 'device_ip', 'internal_ip', 'external_ip', 'primary_ip'
            ],
            'class': [
                'class', 'classification', 'tier', 'level', 'grade', 'category',
                'server_class', 'system_class'
            ],
            'system_classification': [
                'system_classification', 'security_classification', 'data_classification',
                'classification_level', 'sensitivity', 'security_level'
            ],
            'apm': [
                'apm', 'monitoring', 'application_monitoring', 'performance_monitoring',
                'apm_enabled', 'monitoring_enabled'
            ],
            'cio': [
                'cio', 'owner', 'responsible', 'contact', 'admin', 'administrator',
                'system_owner', 'business_owner', 'technical_owner'
            ],
            'edr_coverage': [
                'edr_coverage', 'edr', 'endpoint_detection', 'security_agent',
                'antivirus', 'av_coverage', 'endpoint_protection'
            ],
            'tanium_coverage': [
                'tanium_coverage', 'tanium', 'tanium_agent', 'endpoint_management'
            ],
            'dlp_agent_coverage': [
                'dlp_agent_coverage', 'dlp', 'data_loss_prevention', 'dlp_agent'
            ],
            'logging_in_splunk': [
                'logging_in_splunk', 'splunk', 'splunk_logging', 'log_forwarding'
            ],
            'logging_in_gso': [
                'logging_in_gso', 'gso', 'gso_logging', 'security_logging'
            ],
            'domain': [
                'domain', 'dns_domain', 'ad_domain', 'windows_domain'
            ],
            'fqdn': [
                'fqdn', 'full_name', 'qualified_name', 'dns_name', 'fully_qualified'
            ]
        }
        
        self.stats = {
            'tables_processed': 0,
            'columns_discovered': 0,
            'hosts_created': 0,
            'hosts_updated': 0,
            'total_records_processed': 0,
            'processing_errors': 0
        }
        
        logger.info("𖦹 Establishing BigQuery connection")
        self._init_bigquery()
        
        logger.info("⋆｡‧˚ Establishing DuckDB connection")
        self.duck_conn = duckdb.connect(duckdb_path)
        
        logger.info("༘˚⋆ Creating optimized database schema")
        self._create_optimized_table()
        
        logger.info("♡ Processor initialization complete")
        
    def _init_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            logger.info(f"⋆｡‧˚ Using service account: {service_account_file}")
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            logger.info("₊˚⊹ Using default BigQuery credentials")
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
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_business_unit ON universal_cmdb(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)",
            "CREATE INDEX IF NOT EXISTS idx_infrastructure_type ON universal_cmdb(infrastructure_type)",
            "CREATE INDEX IF NOT EXISTS idx_source_count ON universal_cmdb(source_count)"
        ]
        
        for index_sql in indexes:
            try:
                self.duck_conn.execute(index_sql)
            except:
                pass
                
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str) or hostname.strip() == '*Undefined':
            return ""
        
        normalized = hostname.lower().strip()
        
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        normalized = normalized.replace('-', '')
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized if len(normalized) > 1 else ""
    
    def is_valid_value(self, value) -> bool:
        if not value:
            return False
        if isinstance(value, str):
            stripped = value.strip()
            return stripped != '' and stripped != '*Undefined' and stripped.lower() not in ['null', 'none', 'undefined']
        return True
    
    def load_metadata(self) -> Dict:
        logger.info(f"⋆𖦹 Loading metadata from: {self.json_file_path}")
        start_time = time.time()
        
        with open(self.json_file_path, 'r') as f:
            metadata = json.load(f)
        
        load_time = time.time() - start_time
        
        if 'columns' in metadata:
            table_count = len(metadata['columns'])
            column_count = sum(len(cols) for cols in metadata['columns'].values())
            logger.info(f"✧˚ Loaded {table_count} tables with {column_count} columns in {load_time:.2f}s")
        else:
            logger.warning("₊˚⊹ Metadata missing 'columns' key")
            
        return metadata
    
    def discover_columns_comprehensive(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        logger.info("༘˚⋆ Starting comprehensive column discovery")
        discovered_columns = []
        
        if 'columns' not in metadata:
            logger.error("𖦹 No columns found in metadata")
            return []
        
        table_count = len(metadata['columns'])
        
        for table_idx, (table_name, columns) in enumerate(metadata['columns'].items(), 1):
            logger.info(f"₊˚✩ [{table_idx:2d}/{table_count}] Analyzing: {table_name}")
            
            table_matches = 0
            
            for column_name, column_type in columns.items():
                mapped_type = self._identify_column_type(column_name, column_type)
                
                if mapped_type:
                    discovered_columns.append((table_name, column_name, mapped_type))
                    table_matches += 1
                    
                    match_reason = self._get_match_reason(column_name, column_type, mapped_type)
                    logger.info(f"    ♡ {column_name} → {mapped_type} ({match_reason})")
            
            logger.info(f"    𖦹 Found {table_matches} relevant columns")
        
        self.stats['columns_discovered'] = len(discovered_columns)
        logger.info(f"✧˚ Discovery complete: {len(discovered_columns)} total columns identified")
        
        return discovered_columns
    
    def _identify_column_type(self, column_name: str, column_type) -> Optional[str]:
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
    
    def _get_match_reason(self, column_name: str, column_type, mapped_type: str) -> str:
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        if isinstance(column_type, str) and type_lower in self.column_mapping:
            return f"exact type: '{column_type}'"
        
        if mapped_type == 'hostname':
            for pattern in self.hostname_patterns:
                if pattern in column_lower:
                    return f"hostname pattern: '{pattern}'"
        
        for target_type, patterns in self.advanced_patterns.items():
            if target_type == mapped_type:
                for pattern in patterns:
                    if pattern in column_lower:
                        return f"name pattern: '{pattern}'"
                    if pattern in type_lower:
                        return f"type pattern: '{pattern}'"
        
        return "pattern match"
    
    def process_table_optimized(self, table_name: str, table_columns: List[Tuple[str, str, str]]) -> int:
        logger.info(f"⋆｡‧˚ Processing table: {table_name}")
        
        hostname_cols = [(col, ctype) for _, col, ctype in table_columns if ctype == 'hostname']
        attribute_cols = [(col, ctype) for _, col, ctype in table_columns if ctype != 'hostname']
        
        if not hostname_cols:
            logger.info(f"    ₊˚⊹ Skipping - no hostname columns")
            return 0
        
        primary_hostname_col = hostname_cols[0][0]
        logger.info(f"    ♡ Primary hostname: {primary_hostname_col}")
        logger.info(f"    𖦹 Attribute columns: {len(attribute_cols)}")
        
        for col, ctype in attribute_cols:
            logger.info(f"      ⋆｡‧˚ {col} → {ctype}")
        
        all_columns = [primary_hostname_col] + [col for col, _ in attribute_cols]
        attribute_types = [ctype for _, ctype in attribute_cols]
        
        query = self._build_comprehensive_query(table_name, all_columns, primary_hostname_col)
        
        logger.info(f"    ༘˚⋆ Executing comprehensive query")
        start_time = time.time()
        
        try:
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            query_time = time.time() - start_time
            logger.info(f"    ✧˚ Query completed in {query_time:.2f}s")
            
            return self._process_query_results(results, table_name, primary_hostname_col, attribute_types)
            
        except Exception as e:
            logger.error(f"    𖦹 Query failed: {e}")
            self.stats['processing_errors'] += 1
            return 0
    
    def _build_comprehensive_query(self, table_name: str, columns: List[str], hostname_col: str) -> str:
        column_selects = []
        for col in columns:
            column_selects.append(f"`{col}`")
        
        return f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}`
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND `{hostname_col}` != '*Undefined'
        AND LENGTH(`{hostname_col}`) > 0
        """
    
    def _process_query_results(self, results, table_name: str, hostname_col: str, attribute_types: List[str]) -> int:
        logger.info(f"    ⋆𖦹 Processing query results")
        
        records_processed = 0
        hosts_created = 0
        hosts_updated = 0
        attribute_stats = {attr_type: 0 for attr_type in attribute_types}
        
        batch_records = []
        batch_size = 1000
        
        for row_idx, row in enumerate(results):
            records_processed += 1
            
            if records_processed % 5000 == 0:
                logger.info(f"      ♡ Processed {records_processed:,} rows")
            
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
            
            for i, attr_type in enumerate(attribute_types, 1):
                if i < len(row) and self.is_valid_value(row[i]):
                    record_data[attr_type] = str(row[i]).strip()
                    attribute_stats[attr_type] += 1
            
            batch_records.append(record_data)
            
            if len(batch_records) >= batch_size:
                created, updated = self._process_record_batch(batch_records)
                hosts_created += created
                hosts_updated += updated
                batch_records.clear()
        
        if batch_records:
            created, updated = self._process_record_batch(batch_records)
            hosts_created += created
            hosts_updated += updated
        
        logger.info(f"    ✧˚ Results: {records_processed:,} processed")
        logger.info(f"    ♡ Hosts: {hosts_created} created, {hosts_updated} updated")
        
        for attr_type, count in attribute_stats.items():
            if count > 0:
                logger.info(f"      𖦹 {attr_type}: {count:,} values")
        
        self.stats['total_records_processed'] += records_processed
        self.stats['hosts_created'] += hosts_created
        self.stats['hosts_updated'] += hosts_updated
        
        return records_processed
    
    def _process_record_batch(self, batch_records: List[Dict]) -> Tuple[int, int]:
        hosts_created = 0
        hosts_updated = 0
        
        for record in batch_records:
            if self._insert_or_update_optimized(record):
                hosts_created += 1
            else:
                hosts_updated += 1
        
        return hosts_created, hosts_updated
    
    def _insert_or_update_optimized(self, record: Dict) -> bool:
        normalized_host = record['normalized_host']
        table_name = record['table_name']
        
        existing_query = """
        SELECT source_tables, data_quality_score, source_count,
               hostname, fqdn, domain, infrastructure_type, region, country, data_center,
               cloud_region, ip_address, class, system_classification, business_unit,
               apm, cio, edr_coverage, tanium_coverage, dlp_agent_coverage,
               logging_in_splunk, logging_in_gso
        FROM universal_cmdb WHERE normalized_host = ?
        """
        
        existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
        
        if existing:
            return self._update_existing_host(normalized_host, record, existing)
        else:
            return self._create_new_host(record)
    
    def _update_existing_host(self, normalized_host: str, record: Dict, existing) -> bool:
        updates = []
        values = []
        
        current_tables = existing[0] if existing[0] else ""
        table_name = record['table_name']
        
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            
            new_source_count = (existing[2] or 0) + 1
            updates.append("source_count = ?")
            values.append(new_source_count)
        
        column_names = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for i, col_name in enumerate(column_names, 3):
            if col_name in record:
                new_value = record[col_name]
                existing_value = existing[i] if i < len(existing) and existing[i] else None
                
                final_value = self._merge_values(existing_value, new_value)
                
                if final_value != existing_value:
                    updates.append(f"{col_name} = ?")
                    values.append(final_value)
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)} WHERE normalized_host = ?"
            self.duck_conn.execute(update_sql, values)
        
        return False
    
    def _create_new_host(self, record: Dict) -> bool:
        columns = ['normalized_host', 'source_tables', 'source_count']
        values = [record['normalized_host'], record['table_name'], 1]
        
        data_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        for col in data_columns:
            columns.append(col)
            values.append(record.get(col))
        
        placeholders = ', '.join(['?' for _ in values])
        insert_sql = f"INSERT INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        
        self.duck_conn.execute(insert_sql, values)
        return True
    
    def _merge_values(self, existing_value: Optional[str], new_value: str) -> str:
        if not existing_value or existing_value.strip() == '':
            return new_value
        
        if not new_value or new_value.strip() == '':
            return existing_value
        
        existing_parts = set(part.strip() for part in existing_value.split('|'))
        new_part = new_value.strip()
        
        if new_part not in existing_parts:
            existing_parts.add(new_part)
            return ' | '.join(sorted(existing_parts))
        
        return existing_value
    
    def create_comprehensive_summary(self):
        logger.info("⋆｡‧˚ Creating comprehensive summary tables")
        
        try:
            self.duck_conn.execute("DROP TABLE IF EXISTS all_sources")
            self.duck_conn.execute("DROP TABLE IF EXISTS data_quality_summary")
            self.duck_conn.execute("DROP TABLE IF EXISTS coverage_analysis")
            
            all_sources_sql = """
            CREATE TABLE all_sources AS (
                SELECT 
                    normalized_host as host,
                    source_tables,
                    source_count,
                    data_quality_score,
                    hostname, fqdn, domain, infrastructure_type, region, country,
                    data_center, cloud_region, ip_address, class, system_classification,
                    business_unit, apm, cio, edr_coverage, tanium_coverage, 
                    dlp_agent_coverage, logging_in_splunk, logging_in_gso,
                    first_seen, last_updated
                FROM universal_cmdb
                WHERE normalized_host IS NOT NULL 
                ORDER BY source_count DESC, data_quality_score DESC, normalized_host
            )
            """
            
            quality_summary_sql = """
            CREATE TABLE data_quality_summary AS (
                SELECT 
                    'hostname' as column_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) as populated_records,
                    ROUND(COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) * 100.0 / COUNT(*), 2) as population_percentage
                FROM universal_cmdb
                
                UNION ALL
                
                SELECT 'business_unit', COUNT(*), COUNT(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 END),
                       ROUND(COUNT(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 END) * 100.0 / COUNT(*), 2)
                FROM universal_cmdb
                
                UNION ALL
                
                SELECT 'region', COUNT(*), COUNT(CASE WHEN region IS NOT NULL AND region != '' THEN 1 END),
                       ROUND(COUNT(CASE WHEN region IS NOT NULL AND region != '' THEN 1 END) * 100.0 / COUNT(*), 2)
                FROM universal_cmdb
                
                ORDER BY population_percentage DESC
            )
            """
            
            self.duck_conn.execute(all_sources_sql)
            self.duck_conn.execute(quality_summary_sql)
            
            logger.info("    ♡ Summary tables created successfully")
            
        except Exception as e:
            logger.error(f"    𖦹 Summary creation failed: {e}")
    
    def generate_comprehensive_report(self):
        logger.info("₊˚✩ Generating comprehensive verification report")
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        logger.info(f"༘˚⋆ Total unique hosts: {total_hosts:,}")
        
        columns_to_check = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage',
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        logger.info("𖦹 Column population analysis:")
        populated_columns = []
        empty_columns = []
        
        for col in columns_to_check:
            count_query = f"SELECT COUNT(*) FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != ''"
            count = self.duck_conn.execute(count_query).fetchone()[0]
            percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
            
            if count > 0:
                populated_columns.append(col)
                logger.info(f"  ♡ {col}: {count:,} records ({percentage:.1f}%)")
                
                sample_query = f"SELECT DISTINCT {col} FROM universal_cmdb WHERE {col} IS NOT NULL AND {col} != '' LIMIT 3"
                samples = self.duck_conn.execute(sample_query).fetchall()
                sample_values = [str(s[0])[:25] for s in samples]
                logger.info(f"     ⋆｡‧˚ Samples: {', '.join(sample_values)}")
            else:
                empty_columns.append(col)
                logger.info(f"  ₊˚⊹ {col}: No data")
        
        logger.info(f"\n✧˚ Processing Statistics:")
        logger.info(f"  ♡ Tables processed: {self.stats['tables_processed']}")
        logger.info(f"  𖦹 Columns discovered: {self.stats['columns_discovered']}")
        logger.info(f"  ⋆｡‧˚ Records processed: {self.stats['total_records_processed']:,}")
        logger.info(f"  ༘˚⋆ Hosts created: {self.stats['hosts_created']:,}")
        logger.info(f"  ₊˚✩ Hosts updated: {self.stats['hosts_updated']:,}")
        
        if self.stats['processing_errors'] > 0:
            logger.warning(f"  ₊˚⊹ Processing errors: {self.stats['processing_errors']}")
        
        logger.info(f"\n⋆𖦹 Success Summary:")
        logger.info(f"  ♡ Populated columns: {len(populated_columns)}")
        logger.info(f"  ₊˚⊹ Empty columns: {len(empty_columns)}")
        
        if populated_columns:
            logger.info(f"  ✧˚ Data found in: {', '.join(populated_columns)}")
        
        logger.info("༘˚⋆ Sample enriched records:")
        sample_query = """
        SELECT * FROM universal_cmdb 
        WHERE normalized_host IS NOT NULL
        ORDER BY source_count DESC, data_quality_score DESC
        LIMIT 3
        """
        
        samples = self.duck_conn.execute(sample_query).fetchall()
        column_names = [
            'normalized_host', 'source_tables', 'hostname', 'fqdn', 'domain',
            'infrastructure_type', 'region', 'country', 'data_center', 'cloud_region',
            'ip_address', 'class', 'system_classification', 'business_unit', 'apm',
            'cio', 'edr_coverage', 'tanium_coverage', 'dlp_agent_coverage',
            'logging_in_splunk', 'logging_in_gso'
        ]
        
        for i, sample in enumerate(samples, 1):
            logger.info(f"  ⋆｡‧˚ Record {i}: {sample[0]}")
            populated_fields = 0
            for j, col_name in enumerate(column_names[1:], 1):
                if j < len(sample) and sample[j] and str(sample[j]).strip():
                    if col_name not in ['data_quality_score', 'source_count', 'first_seen', 'last_updated', 'created_at']:
                        logger.info(f"    ♡ {col_name}: {str(sample[j])[:40]}")
                        populated_fields += 1
            logger.info(f"    𖦹 Fields populated: {populated_fields}")
    
    def export_comprehensive(self, filename: str = "universal_cmdb_export.csv"):
        logger.info(f"༘˚⋆ Exporting comprehensive data to {filename}")
        try:
            export_query = f"""
            COPY (
                SELECT * FROM universal_cmdb 
                ORDER BY source_count DESC, data_quality_score DESC, normalized_host
            ) TO '{filename}' WITH (FORMAT CSV, HEADER)
            """
            self.duck_conn.execute(export_query)
            logger.info(f"✧˚ Export completed successfully")
        except Exception as e:
            logger.error(f"𖦹 Export failed: {e}")
    
    def process_all_comprehensive(self):
        logger.info("₊˚✩ Starting comprehensive CMDB processing")
        
        start_time = time.time()
        
        metadata = self.load_metadata()
        discovered_columns = self.discover_columns_comprehensive(metadata)
        
        if not discovered_columns:
            logger.error("𖦹 No processable columns discovered")
            return
        
        logger.info("⋆｡‧˚ Organizing columns by table")
        columns_by_table = defaultdict(list)
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((table_name, column_name, column_type))
        
        table_count = len(columns_by_table)
        logger.info(f"༘˚⋆ Processing {table_count} tables comprehensively")
        
        for table_idx, (table_name, table_columns) in enumerate(columns_by_table.items(), 1):
            logger.info(f"\n♡ [{table_idx:2d}/{table_count}] Processing: {table_name}")
            
            table_start = time.time()
            records_processed = self.process_table_optimized(table_name, table_columns)
            table_time = time.time() - table_start
            
            logger.info(f"    ✧˚ Completed in {table_time:.2f}s ({records_processed:,} records)")
            self.stats['tables_processed'] += 1
        
        logger.info("⋆𖦹 Creating comprehensive summaries")
        self.create_comprehensive_summary()
        
        logger.info("𖦹 Generating final report")
        self.generate_comprehensive_report()
        
        total_time = time.time() - start_time
        logger.info(f"\n₊˚✩ Processing completed in {total_time:.2f} seconds")
    
    def close_connections(self):
        logger.info("༘˚⋆ Closing database connections")
        try:
            self.duck_conn.close()
            logger.info("♡ Connections closed successfully")
        except Exception as e:
            logger.warning(f"₊˚⊹ Error closing connections: {e}")

if __name__ == "__main__":
    logger.info("₊˚✩ OPTIMIZED UNIVERSAL CMDB PROCESSOR")
    logger.info("═══════════════════════════════════════════════════════")
    
    processor = None
    
    try:
        processor = OptimizedCMDBProcessor("reviewed_labeled_columns.json", "universal_cmdb.db")
        
        processor.process_all_comprehensive()
        processor.export_comprehensive("universal_cmdb_complete.csv")
        
        logger.info("\n✧˚ COMPREHENSIVE PROCESSING COMPLETE")
        
    except KeyboardInterrupt:
        logger.warning("\n₊˚⊹ Processing interrupted by user")
    except Exception as e:
        logger.error(f"𖦹 Processing failed: {e}")
        import traceback
        logger.error(f"⋆｡‧˚ Error details:\n{traceback.format_exc()}")
    finally:
        if processor:
            processor.close_connections()