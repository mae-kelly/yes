import json
import duckdb
import os
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple, Optional
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass
import sqlite3
from queue import Queue
import hashlib

class FeminineFormatter(logging.Formatter):
    def format(self, record):
        return super().format(record)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
console_handler = logging.StreamHandler()
console_handler.setFormatter(FeminineFormatter())
logger = logging.getLogger(__name__)
logger.handlers.clear()
logger.addHandler(console_handler)

@dataclass
class ColumnMatch:
    table_name: str
    column_name: str
    column_type: str
    mapped_type: str
    confidence: float
    match_reason: str

@dataclass
class ProcessingStats:
    tables_processed: int = 0
    columns_matched: int = 0
    rows_processed: int = 0
    hosts_created: int = 0
    hosts_updated: int = 0
    attributes_populated: int = 0
    conflicts_detected: int = 0
    processing_time: float = 0.0

class IntelligentColumnMatcher:
    def __init__(self):
        self.exact_mappings = {
            'fqdn': 'fqdn', 'domain': 'domain', 'host': 'hostname', 'hostname': 'hostname',
            'infrastructure_type': 'infrastructure_type', 'infra_type': 'infrastructure_type',
            'region': 'region', 'country': 'country', 'data_center': 'data_center',
            'cloud_region': 'cloud_region', 'ip_address': 'ip_address', 'class': 'class',
            'system_classification': 'system_classification', 'business_unit': 'business_unit',
            'apm': 'apm', 'cio': 'cio', 'edr_coverage': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage', 'dlp_agent_coverage': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk', 'logging_in_gso': 'logging_in_gso'
        }
        
        self.pattern_mappings = {
            'hostname': {
                'patterns': ['host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name', 
                           'endpoint_name', 'splunk_host', 'app_host', 'computer_name', 'machine_name',
                           'chronicle_device_hostname', 'endpointdomain_name'],
                'weight': 1.0
            },
            'business_unit': {
                'patterns': ['business_unit', 'bu', 'business', 'department', 'division', 'org_unit', 
                           'cost_center', 'organizational_unit', 'business_group', 'dept'],
                'weight': 0.95
            },
            'region': {
                'patterns': ['region', 'location', 'site', 'area', 'zone', 'geographic', 'geo_region',
                           'datacenter_region', 'aws_region', 'azure_region', 'gcp_region'],
                'weight': 0.9
            },
            'infrastructure_type': {
                'patterns': ['infrastructure_type', 'infra_type', 'server_type', 'platform', 
                           'environment', 'env', 'system_type', 'deployment_type', 'os_type'],
                'weight': 0.9
            },
            'ip_address': {
                'patterns': ['ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip', 'server_ip',
                           'endpoint_ip', 'device_ip', 'internal_ip', 'external_ip', 'private_ip'],
                'weight': 0.95
            },
            'country': {
                'patterns': ['country', 'nation', 'country_code', 'geo_country', 'location_country'],
                'weight': 0.85
            },
            'data_center': {
                'patterns': ['datacenter', 'data_center', 'dc', 'facility', 'center', 'site_name',
                           'datacenter_name', 'facility_name'],
                'weight': 0.85
            },
            'cloud_region': {
                'patterns': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region',
                           'cloud_location', 'cloud_zone', 'availability_zone'],
                'weight': 0.8
            },
            'system_classification': {
                'patterns': ['system_classification', 'security_classification', 'data_classification',
                           'classification_level', 'sensitivity', 'security_level'],
                'weight': 0.8
            },
            'apm': {
                'patterns': ['apm', 'monitoring', 'application_monitoring', 'performance_monitoring',
                           'app_monitoring', 'monitor'],
                'weight': 0.75
            },
            'cio': {
                'patterns': ['cio', 'owner', 'responsible', 'contact', 'admin', 'administrator',
                           'responsible_party', 'system_owner', 'business_owner'],
                'weight': 0.7
            },
            'edr_coverage': {
                'patterns': ['edr_coverage', 'edr', 'endpoint_detection', 'security_agent',
                           'antivirus', 'av_coverage', 'endpoint_protection'],
                'weight': 0.85
            },
            'tanium_coverage': {
                'patterns': ['tanium_coverage', 'tanium', 'tanium_agent', 'endpoint_management'],
                'weight': 0.9
            },
            'dlp_agent_coverage': {
                'patterns': ['dlp_agent_coverage', 'dlp', 'data_loss_prevention', 'dlp_agent'],
                'weight': 0.9
            },
            'logging_in_splunk': {
                'patterns': ['logging_in_splunk', 'splunk', 'splunk_logging', 'log_forwarding'],
                'weight': 0.85
            },
            'logging_in_gso': {
                'patterns': ['logging_in_gso', 'gso', 'gso_logging', 'security_logging'],
                'weight': 0.85
            },
            'domain': {
                'patterns': ['domain', 'dns_domain', 'ad_domain', 'active_directory', 'fqdn_domain'],
                'weight': 0.8
            },
            'fqdn': {
                'patterns': ['fqdn', 'full_name', 'qualified_name', 'fully_qualified'],
                'weight': 0.9
            },
            'class': {
                'patterns': ['class', 'classification', 'tier', 'level', 'grade', 'category', 'type'],
                'weight': 0.7
            }
        }
        
        self.fuzzy_keywords = {
            'server': 'infrastructure_type', 'windows': 'infrastructure_type', 'linux': 'infrastructure_type',
            'database': 'infrastructure_type', 'web': 'infrastructure_type', 'application': 'infrastructure_type',
            'production': 'infrastructure_type', 'prod': 'infrastructure_type', 'test': 'infrastructure_type',
            'dev': 'infrastructure_type', 'staging': 'infrastructure_type', 'qa': 'infrastructure_type',
            'finance': 'business_unit', 'marketing': 'business_unit', 'sales': 'business_unit',
            'hr': 'business_unit', 'it': 'business_unit', 'engineering': 'business_unit',
            'operations': 'business_unit', 'security': 'business_unit', 'compliance': 'business_unit',
            'us': 'region', 'europe': 'region', 'asia': 'region', 'americas': 'region',
            'east': 'region', 'west': 'region', 'north': 'region', 'south': 'region',
            'central': 'region', 'pacific': 'region', 'atlantic': 'region'
        }

    def analyze_column(self, table_name: str, column_name: str, column_type: str) -> Optional[ColumnMatch]:
        matches = []
        
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        if type_lower in self.exact_mappings:
            matches.append(ColumnMatch(
                table_name, column_name, column_type, self.exact_mappings[type_lower],
                1.0, f"exact type match: '{column_type}'"
            ))
        
        for target_type, config in self.pattern_mappings.items():
            for pattern in config['patterns']:
                if pattern in column_lower:
                    confidence = config['weight'] * (len(pattern) / len(column_lower))
                    matches.append(ColumnMatch(
                        table_name, column_name, column_type, target_type,
                        confidence, f"column name pattern: '{pattern}'"
                    ))
                
                if pattern in type_lower:
                    confidence = config['weight'] * 0.8
                    matches.append(ColumnMatch(
                        table_name, column_name, column_type, target_type,
                        confidence, f"column type pattern: '{pattern}'"
                    ))
        
        for keyword, target_type in self.fuzzy_keywords.items():
            if keyword in column_lower:
                confidence = 0.6 * (len(keyword) / len(column_lower))
                matches.append(ColumnMatch(
                    table_name, column_name, column_type, target_type,
                    confidence, f"fuzzy keyword: '{keyword}'"
                ))
        
        if matches:
            best_match = max(matches, key=lambda x: x.confidence)
            if best_match.confidence > 0.5:
                return best_match
        
        return None

class OptimizedCMDBProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db", max_workers: int = 4):
        logger.info("₊˚✩ Initializing Optimized CMDB Processor...")
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.max_workers = max_workers
        self.matcher = IntelligentColumnMatcher()
        self.stats = ProcessingStats()
        self.processing_queue = Queue()
        self.data_cache = {}
        
        logger.info("𖦹 Connecting to BigQuery...")
        self.bq_client = self._initialize_bigquery()
        
        logger.info("⋆｡‧˚ Connecting to DuckDB...")
        self.duck_conn = duckdb.connect(duckdb_path)
        
        logger.info("༘˚⋆ Setting up optimized database schema...")
        self._setup_optimized_database()
        
        logger.info("♡ Processor initialization complete!")

    def _initialize_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            logger.info(f"✧˚ Using service account: {service_account_file}")
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            return bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            logger.warning("₊˚⊹ Using default credentials")
            return bigquery.Client(project="chronicle-fisv")

    def _setup_optimized_database(self):
        base_schema = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR PRIMARY KEY,
            source_tables TEXT,
            data_hash VARCHAR,
            confidence_score FLOAT DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(base_schema)
        
        self.dynamic_columns = set()
        self._create_indexes()
        
    def _create_indexes(self):
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_confidence_score ON universal_cmdb(confidence_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_last_updated ON universal_cmdb(last_updated DESC)"
        ]
        
        for idx in indexes:
            try:
                self.duck_conn.execute(idx)
            except:
                pass

    def _ensure_column_exists(self, column_name: str) -> bool:
        if column_name in self.dynamic_columns:
            return True
            
        if column_name in ['normalized_host', 'source_tables', 'data_hash', 'confidence_score', 'last_updated', 'created_at']:
            return True
            
        try:
            alter_sql = f"ALTER TABLE universal_cmdb ADD COLUMN {column_name} TEXT"
            self.duck_conn.execute(alter_sql)
            self.dynamic_columns.add(column_name)
            logger.info(f"    ♡ Added dynamic column: {column_name}")
            
            try:
                self.duck_conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{column_name} ON universal_cmdb({column_name})")
            except:
                pass
                
            return True
        except Exception as e:
            logger.warning(f"₊˚⊹ Failed to add column {column_name}: {e}")
            return False

    def normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.lower().strip()
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        normalized = normalized.replace('-', '')
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        return normalized

    def load_and_analyze_metadata(self) -> List[ColumnMatch]:
        logger.info("༘˚⋆ Loading and analyzing metadata...")
        start_time = time.time()
        
        try:
            with open(self.json_file_path, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"𐙚 Failed to load metadata: {e}")
            raise

        if 'columns' not in metadata:
            logger.error("𐙚 No 'columns' key in metadata")
            return []

        all_matches = []
        total_tables = len(metadata['columns'])
        total_columns = sum(len(cols) for cols in metadata['columns'].values())
        
        logger.info(f"⋆｡‧˚ Analyzing {total_tables} tables with {total_columns} columns...")

        for table_idx, (table_name, columns) in enumerate(metadata['columns'].items(), 1):
            logger.info(f"₊˚✩ [{table_idx}/{total_tables}] {table_name}")
            
            table_matches = 0
            for column_name, column_type in columns.items():
                match = self.matcher.analyze_column(table_name, column_name, column_type)
                if match:
                    all_matches.append(match)
                    table_matches += 1
                    logger.info(f"  ♡ {column_name} -> {match.mapped_type} ({match.confidence:.2f}) - {match.match_reason}")
            
            logger.info(f"  𖦹 {table_matches}/{len(columns)} columns matched")
            self.stats.columns_matched += table_matches

        analysis_time = time.time() - start_time
        logger.info(f"✧˚ Analysis complete: {len(all_matches)} matches in {analysis_time:.2f}s")
        
        return all_matches

    def _build_optimized_query(self, table_name: str, columns: List[ColumnMatch]) -> str:
        hostname_cols = [c for c in columns if c.mapped_type == 'hostname']
        if not hostname_cols:
            return None
            
        primary_hostname = max(hostname_cols, key=lambda x: x.confidence)
        
        select_columns = [f"`{primary_hostname.column_name}` as primary_hostname"]
        column_mappings = {'primary_hostname': 'hostname'}
        
        for col in columns:
            if col.mapped_type != 'hostname':
                select_columns.append(f"`{col.column_name}`")
                column_mappings[col.column_name] = col.mapped_type
        
        query = f"""
        SELECT {', '.join(select_columns)}
        FROM `{table_name}`
        WHERE `{primary_hostname.column_name}` IS NOT NULL 
        AND `{primary_hostname.column_name}` != ''
        AND LENGTH(`{primary_hostname.column_name}`) > 0
        LIMIT 100000
        """
        
        return query, column_mappings

    def process_table_batch(self, table_name: str, columns: List[ColumnMatch]) -> Dict:
        logger.info(f"⋆｡‧˚ Processing: {table_name}")
        
        query_result = self._build_optimized_query(table_name, columns)
        if not query_result:
            logger.warning(f"₊˚⊹ Skipping {table_name} - no hostname columns")
            return {'processed': 0, 'created': 0, 'updated': 0}
        
        query, column_mappings = query_result
        
        start_time = time.time()
        try:
            logger.info(f"  𖦹 Executing BigQuery...")
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            query_time = time.time() - start_time
            logger.info(f"  ✧˚ Query completed in {query_time:.2f}s")
            
            return self._process_query_results(results, table_name, column_mappings)
            
        except Exception as e:
            logger.error(f"  𐙚 Query failed for {table_name}: {e}")
            return {'processed': 0, 'created': 0, 'updated': 0}

    def _process_query_results(self, results, table_name: str, column_mappings: Dict) -> Dict:
        logger.info(f"  ༘˚⋆ Processing query results...")
        
        processed = created = updated = 0
        batch_data = []
        
        for row_idx, row in enumerate(results):
            if row_idx % 2000 == 0 and row_idx > 0:
                logger.info(f"    𖦹 Processed {row_idx} rows...")
            
            if not row[0] or not isinstance(row[0], str):
                continue
                
            normalized_host = self.normalize_hostname(row[0])
            if not normalized_host or len(normalized_host) <= 2:
                continue
            
            record_data = {
                'normalized_host': normalized_host,
                'hostname': row[0]
            }
            
            for i, (original_col, mapped_type) in enumerate(column_mappings.items(), 0):
                if i < len(row) and row[i] and original_col != 'primary_hostname':
                    self._ensure_column_exists(mapped_type)
                    record_data[mapped_type] = str(row[i]).strip()
            
            batch_data.append(record_data)
            processed += 1
            
            if len(batch_data) >= 1000:
                batch_results = self._insert_batch_data(batch_data, table_name)
                created += batch_results['created']
                updated += batch_results['updated']
                batch_data = []
        
        if batch_data:
            batch_results = self._insert_batch_data(batch_data, table_name)
            created += batch_results['created']
            updated += batch_results['updated']
        
        logger.info(f"  ♡ Completed: {processed} processed, {created} created, {updated} updated")
        return {'processed': processed, 'created': created, 'updated': updated}

    def _insert_batch_data(self, batch_data: List[Dict], table_name: str) -> Dict:
        created = updated = 0
        
        for record in batch_data:
            normalized_host = record['normalized_host']
            
            existing_query = "SELECT * FROM universal_cmdb WHERE normalized_host = ?"
            existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
            
            if existing:
                updated += self._update_existing_host(existing, record, table_name)
            else:
                created += self._create_new_host(record, table_name)
        
        return {'created': created, 'updated': updated}

    def _update_existing_host(self, existing, record: Dict, table_name: str) -> int:
        columns_query = "PRAGMA table_info(universal_cmdb)"
        column_info = self.duck_conn.execute(columns_query).fetchall()
        existing_columns = {col[1]: i for i, col in enumerate(column_info)}
        
        updates = []
        values = []
        conflicts = 0
        
        current_tables = existing[1] if existing[1] else ""
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
        
        for key, new_value in record.items():
            if key == 'normalized_host' or not new_value:
                continue
                
            if key in existing_columns:
                col_index = existing_columns[key]
                existing_value = existing[col_index] if col_index < len(existing) else None
                
                if existing_value and existing_value.strip():
                    existing_vals = set(v.strip() for v in str(existing_value).split(' | '))
                    if new_value.strip() not in existing_vals:
                        final_value = ' | '.join(sorted(existing_vals | {new_value.strip()}))
                        conflicts += 1
                        self.stats.conflicts_detected += 1
                    else:
                        continue
                else:
                    final_value = new_value.strip()
                
                updates.append(f"{key} = ?")
                values.append(final_value)
        
        if updates:
            values.append(record['normalized_host'])
            update_sql = f"UPDATE universal_cmdb SET {', '.join(updates)}, last_updated = CURRENT_TIMESTAMP WHERE normalized_host = ?"
            self.duck_conn.execute(update_sql, values)
            self.stats.attributes_populated += len(updates) - (1 if 'source_tables = ?' in updates else 0)
            return 1
        
        return 0

    def _create_new_host(self, record: Dict, table_name: str) -> int:
        record_copy = record.copy()
        record_copy['source_tables'] = table_name
        
        data_string = json.dumps(sorted(record_copy.items()), sort_keys=True)
        record_copy['data_hash'] = hashlib.md5(data_string.encode()).hexdigest()
        record_copy['confidence_score'] = self._calculate_confidence_score(record_copy)
        
        columns = list(record_copy.keys())
        values = list(record_copy.values())
        placeholders = ', '.join(['?'] * len(columns))
        
        for col in columns:
            self._ensure_column_exists(col)
        
        insert_sql = f"INSERT OR IGNORE INTO universal_cmdb ({', '.join(columns)}) VALUES ({placeholders})"
        self.duck_conn.execute(insert_sql, values)
        
        self.stats.attributes_populated += len([v for v in values if v and str(v).strip()]) - 3
        return 1

    def _calculate_confidence_score(self, record: Dict) -> float:
        base_score = 0.5
        field_bonus = min(len([v for v in record.values() if v and str(v).strip()]) * 0.05, 0.3)
        hostname_bonus = 0.1 if record.get('hostname') else 0.0
        attribute_bonus = 0.1 if len(record) > 4 else 0.0
        
        return min(base_score + field_bonus + hostname_bonus + attribute_bonus, 1.0)

    def process_all_tables(self):
        logger.info("₊˚✩ Starting comprehensive CMDB processing...")
        overall_start = time.time()
        
        matches = self.load_and_analyze_metadata()
        if not matches:
            logger.error("𐙚 No column matches found!")
            return
        
        tables_by_name = defaultdict(list)
        for match in matches:
            tables_by_name[match.table_name].append(match)
        
        logger.info(f"༘˚⋆ Processing {len(tables_by_name)} tables with {len(matches)} total column matches...")
        
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(tables_by_name))) as executor:
            future_to_table = {
                executor.submit(self.process_table_batch, table_name, columns): table_name
                for table_name, columns in tables_by_name.items()
            }
            
            for future in as_completed(future_to_table):
                table_name = future_to_table[future]
                try:
                    result = future.result()
                    self.stats.tables_processed += 1
                    self.stats.rows_processed += result['processed']
                    self.stats.hosts_created += result['created']
                    self.stats.hosts_updated += result['updated']
                    
                    logger.info(f"✧˚ Completed {table_name}: {result}")
                except Exception as e:
                    logger.error(f"𐙚 Failed {table_name}: {e}")
        
        self.stats.processing_time = time.time() - overall_start
        
        logger.info("𖦹 Creating optimized summary tables...")
        self._create_advanced_summaries()
        
        logger.info("♡ Generating comprehensive verification...")
        self._generate_comprehensive_report()

    def _create_advanced_summaries(self):
        try:
            self.duck_conn.execute("DROP TABLE IF EXISTS host_summary")
            
            summary_sql = """
            CREATE TABLE host_summary AS (
                SELECT 
                    normalized_host,
                    source_tables,
                    confidence_score,
                    LENGTH(source_tables) - LENGTH(REPLACE(source_tables, ',', '')) + 1 as source_count,
                    CASE 
                        WHEN confidence_score >= 0.8 THEN 'HIGH'
                        WHEN confidence_score >= 0.6 THEN 'MEDIUM' 
                        ELSE 'LOW'
                    END as confidence_level,
                    last_updated,
                    created_at
                FROM universal_cmdb
                ORDER BY confidence_score DESC, source_count DESC
            )
            """
            self.duck_conn.execute(summary_sql)
            
            self.duck_conn.execute("DROP TABLE IF EXISTS data_quality_metrics")
            
            quality_sql = """
            CREATE TABLE data_quality_metrics AS (
                SELECT 
                    'hostname' as attribute,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) as populated_records,
                    ROUND(COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) * 100.0 / COUNT(*), 2) as population_percentage
                FROM universal_cmdb
            )
            """
            self.duck_conn.execute(quality_sql)
            
            for column in self.dynamic_columns:
                if column not in ['normalized_host', 'source_tables', 'data_hash', 'confidence_score']:
                    insert_sql = f"""
                    INSERT INTO data_quality_metrics
                    SELECT 
                        '{column}' as attribute,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN {column} IS NOT NULL AND {column} != '' THEN 1 END) as populated_records,
                        ROUND(COUNT(CASE WHEN {column} IS NOT NULL AND {column} != '' THEN 1 END) * 100.0 / COUNT(*), 2) as population_percentage
                    FROM universal_cmdb
                    """
                    self.duck_conn.execute(insert_sql)
            
            logger.info("  ♡ Advanced summary tables created")
        except Exception as e:
            logger.error(f"  𐙚 Summary creation failed: {e}")

    def _generate_comprehensive_report(self):
        logger.info("₊˚✩ COMPREHENSIVE PROCESSING REPORT")
        logger.info("═" * 70)
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        logger.info(f"⋆｡‧˚ Processing Statistics:")
        logger.info(f"  ♡ Tables processed: {self.stats.tables_processed}")
        logger.info(f"  ♡ Total unique hosts: {total_hosts:,}")
        logger.info(f"  ♡ Rows processed: {self.stats.rows_processed:,}")
        logger.info(f"  ♡ New hosts created: {self.stats.hosts_created:,}")
        logger.info(f"  ♡ Existing hosts updated: {self.stats.hosts_updated:,}")
        logger.info(f"  ♡ Attributes populated: {self.stats.attributes_populated:,}")
        logger.info(f"  ♡ Conflicts detected: {self.stats.conflicts_detected:,}")
        logger.info(f"  ♡ Processing time: {self.stats.processing_time:.2f}s")
        
        confidence_dist = self.duck_conn.execute("""
            SELECT confidence_level, COUNT(*) 
            FROM host_summary 
            GROUP BY confidence_level
        """).fetchall()
        
        logger.info(f"\n༘˚⋆ Data Quality Distribution:")
        for level, count in confidence_dist:
            percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
            logger.info(f"  𖦹 {level} confidence: {count:,} hosts ({percentage:.1f}%)")
        
        quality_metrics = self.duck_conn.execute("""
            SELECT attribute, populated_records, population_percentage 
            FROM data_quality_metrics 
            WHERE populated_records > 0
            ORDER BY population_percentage DESC
        """).fetchall()
        
        logger.info(f"\n✧˚ Attribute Population Report:")
        populated_attrs = 0
        for attr, count, pct in quality_metrics:
            logger.info(f"  ♡ {attr}: {count:,} records ({pct}%)")
            populated_attrs += 1
        
        empty_attrs = len(self.dynamic_columns) - populated_attrs
        logger.info(f"\n𖦹 SUCCESS METRICS:")
        logger.info(f"  ✧˚ Populated attributes: {populated_attrs}")
        logger.info(f"  ₊˚⊹ Empty attributes: {empty_attrs}")
        logger.info(f"  ♡ Overall success rate: {(populated_attrs/(populated_attrs+empty_attrs)*100):.1f}%")
        
        top_hosts = self.duck_conn.execute("""
            SELECT normalized_host, source_count, confidence_score
            FROM host_summary
            ORDER BY source_count DESC, confidence_score DESC
            LIMIT 5
        """).fetchall()
        
        logger.info(f"\n⋆｡‧˚ Top Multi-Source Hosts:")
        for host, sources, confidence in top_hosts:
            logger.info(f"  𖦹 {host}: {sources} sources (confidence: {confidence:.2f})")

    def export_comprehensive_data(self, base_filename: str = "universal_cmdb"):
        logger.info(f"༘˚⋆ Exporting comprehensive dataset...")
        
        exports = [
            (f"{base_filename}_complete.csv", "SELECT * FROM universal_cmdb ORDER BY confidence_score DESC, normalized_host"),
            (f"{base_filename}_summary.csv", "SELECT * FROM host_summary"),
            (f"{base_filename}_quality_metrics.csv", "SELECT * FROM data_quality_metrics"),
            (f"{base_filename}_high_confidence.csv", "SELECT * FROM universal_cmdb WHERE confidence_score >= 0.8 ORDER BY confidence_score DESC")
        ]
        
        for filename, query in exports:
            try:
                self.duck_conn.execute(f"COPY ({query}) TO '{filename}' WITH (FORMAT CSV, HEADER)")
                logger.info(f"  ♡ Exported: {filename}")
            except Exception as e:
                logger.error(f"  𐙚 Export failed for {filename}: {e}")

    def close(self):
        logger.info("₊˚⊹ Closing connections...")
        try:
            self.duck_conn.close()
            logger.info("♡ Database connections closed gracefully")
        except Exception as e:
            logger.warning(f"⋆｡‧˚ Warning during cleanup: {e}")

if __name__ == "__main__":
    logger.info("₊˚✩ OPTIMIZED UNIVERSAL CMDB PROCESSOR")
    logger.info("═" * 80)
    
    processor = None
    try:
        processor = OptimizedCMDBProcessor(
            json_file_path="reviewed_labeled_columns.json",
            duckdb_path="universal_cmdb.db",
            max_workers=4
        )
        
        processor.process_all_tables()
        processor.export_comprehensive_data()
        
        logger.info("\n✧˚ PROCESSING SUCCESSFULLY COMPLETED!")
        
    except KeyboardInterrupt:
        logger.warning("\n₊˚⊹ Processing interrupted by user")
    except Exception as e:
        logger.error(f"𐙚 Critical error: {e}")
        import traceback
        logger.error(f"༘˚⋆ Traceback:\n{traceback.format_exc()}")
    finally:
        if processor:
            processor.close()