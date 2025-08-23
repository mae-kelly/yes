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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib

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

@dataclass
class ColumnMatch:
    table_name: str
    column_name: str
    mapped_type: str
    match_reason: str
    confidence: float

class IntelligentPatternMatcher:
    def __init__(self):
        self.exact_mappings = {
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
        
        self.semantic_patterns = {
            'hostname': {
                'exact': ['host', 'hostname', 'fqdn', 'server_name', 'node_name', 'device_name', 
                         'endpoint_name', 'computer_name', 'machine_name'],
                'contains': ['server', 'host', 'node', 'device', 'endpoint', 'computer', 'machine'],
                'ends_with': ['_host', '_hostname', '_name'],
                'starts_with': ['host_', 'server_', 'node_', 'device_']
            },
            'business_unit': {
                'exact': ['business_unit', 'bu', 'department', 'division', 'org_unit', 'cost_center'],
                'contains': ['business', 'department', 'division', 'unit', 'org'],
                'fuzzy': ['dept', 'bu', 'org', 'team', 'group']
            },
            'region': {
                'exact': ['region', 'location', 'site', 'area', 'zone', 'datacenter_region'],
                'contains': ['region', 'location', 'site', 'area', 'zone', 'geo'],
                'fuzzy': ['loc', 'dc_region', 'geographical']
            },
            'country': {
                'exact': ['country', 'nation', 'country_code'],
                'contains': ['country', 'nation'],
                'ends_with': ['_country', '_nation']
            },
            'infrastructure_type': {
                'exact': ['infrastructure_type', 'infra_type', 'server_type', 'platform', 'environment'],
                'contains': ['infrastructure', 'platform', 'environment', 'infra', 'type'],
                'fuzzy': ['env', 'plat', 'infra']
            },
            'data_center': {
                'exact': ['datacenter', 'data_center', 'dc', 'facility', 'center'],
                'contains': ['datacenter', 'data_center', 'facility', 'center'],
                'fuzzy': ['dc', 'facility']
            },
            'cloud_region': {
                'exact': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
                'contains': ['cloud_region', 'aws', 'azure', 'gcp', 'cloud'],
                'starts_with': ['aws_', 'azure_', 'gcp_', 'cloud_']
            },
            'ip_address': {
                'exact': ['ip_address', 'ip', 'ipv4', 'ipv6', 'host_ip', 'server_ip'],
                'contains': ['ip', 'address'],
                'ends_with': ['_ip', '_address']
            },
            'class': {
                'exact': ['class', 'classification', 'tier', 'level', 'grade', 'category'],
                'contains': ['class', 'tier', 'level', 'grade', 'category'],
                'fuzzy': ['type', 'kind']
            },
            'system_classification': {
                'exact': ['system_classification', 'security_classification', 'sensitivity'],
                'contains': ['classification', 'security', 'sensitivity'],
                'fuzzy': ['classif', 'sec_class']
            },
            'apm': {
                'exact': ['apm', 'monitoring', 'application_monitoring'],
                'contains': ['apm', 'monitoring', 'monitor'],
                'fuzzy': ['mon', 'observability']
            },
            'cio': {
                'exact': ['cio', 'owner', 'responsible', 'contact', 'admin', 'administrator'],
                'contains': ['owner', 'responsible', 'contact', 'admin'],
                'fuzzy': ['resp', 'admin', 'mgr', 'manager']
            },
            'edr_coverage': {
                'exact': ['edr_coverage', 'edr', 'endpoint_detection', 'security_agent'],
                'contains': ['edr', 'endpoint', 'security', 'agent', 'antivirus'],
                'fuzzy': ['av', 'security_tool', 'endpoint_security']
            },
            'tanium_coverage': {
                'exact': ['tanium_coverage', 'tanium', 'tanium_agent'],
                'contains': ['tanium'],
                'fuzzy': ['endpoint_management']
            },
            'dlp_agent_coverage': {
                'exact': ['dlp_agent_coverage', 'dlp', 'data_loss_prevention'],
                'contains': ['dlp', 'data_loss', 'prevention'],
                'fuzzy': ['data_protection']
            },
            'logging_in_splunk': {
                'exact': ['logging_in_splunk', 'splunk', 'splunk_logging'],
                'contains': ['splunk', 'logging'],
                'fuzzy': ['log_forwarding']
            },
            'logging_in_gso': {
                'exact': ['logging_in_gso', 'gso', 'gso_logging'],
                'contains': ['gso'],
                'fuzzy': ['security_logging']
            },
            'domain': {
                'exact': ['domain', 'dns_domain', 'ad_domain'],
                'contains': ['domain'],
                'ends_with': ['_domain']
            },
            'fqdn': {
                'exact': ['fqdn', 'full_name', 'qualified_name'],
                'contains': ['fqdn', 'qualified'],
                'fuzzy': ['full_name', 'complete_name']
            }
        }
    
    def find_best_matches(self, column_name: str, column_type: str) -> List[ColumnMatch]:
        matches = []
        column_lower = column_name.lower()
        type_lower = str(column_type).lower() if column_type else ""
        
        if type_lower in self.exact_mappings:
            matches.append(ColumnMatch("", column_name, self.exact_mappings[type_lower], 
                                     f"exact type match: '{column_type}'", 1.0))
        
        for target_type, patterns in self.semantic_patterns.items():
            confidence = self._calculate_confidence(column_lower, type_lower, patterns)
            if confidence > 0.3:
                reason = self._get_match_reason(column_lower, type_lower, patterns)
                matches.append(ColumnMatch("", column_name, target_type, reason, confidence))
        
        return sorted(matches, key=lambda x: x.confidence, reverse=True)
    
    def _calculate_confidence(self, column_name: str, column_type: str, patterns: Dict) -> float:
        max_confidence = 0.0
        
        if 'exact' in patterns:
            for pattern in patterns['exact']:
                if pattern == column_name or pattern == column_type:
                    max_confidence = max(max_confidence, 1.0)
                elif pattern in column_name or pattern in column_type:
                    max_confidence = max(max_confidence, 0.9)
        
        if 'contains' in patterns:
            for pattern in patterns['contains']:
                if pattern in column_name:
                    max_confidence = max(max_confidence, 0.8)
                elif pattern in column_type:
                    max_confidence = max(max_confidence, 0.7)
        
        if 'starts_with' in patterns:
            for pattern in patterns['starts_with']:
                if column_name.startswith(pattern):
                    max_confidence = max(max_confidence, 0.75)
        
        if 'ends_with' in patterns:
            for pattern in patterns['ends_with']:
                if column_name.endswith(pattern):
                    max_confidence = max(max_confidence, 0.75)
        
        if 'fuzzy' in patterns:
            for pattern in patterns['fuzzy']:
                if pattern in column_name or pattern in column_type:
                    max_confidence = max(max_confidence, 0.6)
        
        return max_confidence
    
    def _get_match_reason(self, column_name: str, column_type: str, patterns: Dict) -> str:
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if category == 'exact' and (pattern == column_name or pattern == column_type):
                    return f"exact {category} match: '{pattern}'"
                elif pattern in column_name or pattern in column_type:
                    return f"{category} pattern match: '{pattern}'"
        return "pattern match"

class OptimizedHostDataProcessor:
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db"):
        logger.info("₊˚✩ Initializing Optimized CMDB Processor...")
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.pattern_matcher = IntelligentPatternMatcher()
        self.stats = defaultdict(int)
        self.processed_tables = set()
        self.lock = threading.Lock()
        
        logger.info("𖦹 Establishing BigQuery connection...")
        self._setup_bigquery()
        
        logger.info("༘˚⋆ Connecting to DuckDB...")
        self.duck_conn = duckdb.connect(duckdb_path)
        
        logger.info("✧˚ Creating optimized database schema...")
        self._create_optimized_table()
        
        logger.info("♡ Initialization complete")
    
    def _setup_bigquery(self):
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        try:
            if os.path.exists(service_account_file):
                logger.info(f"⋆｡‧˚ Using service account: {service_account_file}")
                credentials = service_account.Credentials.from_service_account_file(service_account_file)
                self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
                logger.info("✧˚ BigQuery authenticated with service account")
            else:
                logger.info("𐙚 Using default credentials...")
                self.bq_client = bigquery.Client(project="chronicle-fisv")
                logger.info("♡ BigQuery authenticated with default credentials")
        except Exception as e:
            logger.error(f"༘˚⋆ BigQuery connection failed: {e}")
            raise
    
    def _create_optimized_table(self):
        schema_sql = """
        CREATE TABLE IF NOT EXISTS universal_cmdb (
            normalized_host VARCHAR PRIMARY KEY,
            source_tables TEXT NOT NULL,
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
            confidence_score FLOAT DEFAULT 1.0,
            source_count INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self.duck_conn.execute(schema_sql)
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_business_unit ON universal_cmdb(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)",
            "CREATE INDEX IF NOT EXISTS idx_infrastructure_type ON universal_cmdb(infrastructure_type)",
            "CREATE INDEX IF NOT EXISTS idx_source_count ON universal_cmdb(source_count)"
        ]
        
        for idx in indexes:
            try:
                self.duck_conn.execute(idx)
            except:
                pass
        
        logger.info("⋆｡‧˚ Optimized schema and indexes created")
    
    def normalize_hostname(self, hostname: str) -> Optional[str]:
        if not hostname or not isinstance(hostname, str) or hostname.strip() == "*Undefined":
            return None
        
        str_hostname = str(hostname).strip()
        if str_hostname == "*Undefined":
            return None
            
        normalized = str_hostname.lower().strip()
        
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        normalized = normalized.replace('-', '')
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized if len(normalized) > 2 else None
    
    def is_valid_value(self, value) -> bool:
        if value is None:
            return False
        
        str_value = str(value).strip()
        
        invalid_values = {
            "*Undefined", "undefined", "null", "NULL", "none", "None", 
            "", "n/a", "N/A", "unknown", "Unknown", "-", "—", "–"
        }
        
        return str_value not in invalid_values and len(str_value) > 0
    
    def load_and_analyze_metadata(self) -> Dict:
        logger.info("༘˚⋆ Loading and analyzing metadata...")
        start_time = time.time()
        
        try:
            with open(self.json_file_path, 'r') as f:
                metadata = json.load(f)
            
            load_time = time.time() - start_time
            logger.info(f"♡ Metadata loaded in {load_time:.2f}s")
            
            if 'columns' not in metadata:
                logger.error("𐙚 No 'columns' section found in metadata")
                return {}
            
            table_count = len(metadata['columns'])
            total_columns = sum(len(cols) for cols in metadata['columns'].values())
            
            logger.info(f"𖦹 Found {table_count} tables with {total_columns:,} total columns")
            
            return metadata
        except Exception as e:
            logger.error(f"༘˚⋆ Metadata loading failed: {e}")
            raise
    
    def intelligent_column_discovery(self, metadata: Dict) -> List[ColumnMatch]:
        logger.info("⋆｡‧˚ Starting intelligent column discovery...")
        
        all_matches = []
        confidence_threshold = 0.5
        
        for table_idx, (table_name, columns) in enumerate(metadata['columns'].items(), 1):
            logger.info(f"₊˚✩ [{table_idx}/{len(metadata['columns'])}] Analyzing: {table_name}")
            
            table_matches = []
            
            for column_name, column_type in columns.items():
                matches = self.pattern_matcher.find_best_matches(column_name, column_type)
                
                if matches and matches[0].confidence >= confidence_threshold:
                    best_match = matches[0]
                    best_match.table_name = table_name
                    table_matches.append(best_match)
                    logger.info(f"    ♡ {column_name} → {best_match.mapped_type} "
                              f"({best_match.confidence:.0%}, {best_match.match_reason})")
            
            all_matches.extend(table_matches)
            logger.info(f"    𖦹 {len(table_matches)} columns matched in this table")
        
        logger.info(f"₊˚✩ Discovery complete: {len(all_matches)} total column matches")
        return all_matches
    
    def build_optimized_queries(self, matches: List[ColumnMatch]) -> Dict[str, Dict]:
        logger.info("⋆｡‧˚ Building optimized queries by table...")
        
        queries_by_table = defaultdict(lambda: {
            'hostname_columns': [],
            'attribute_columns': [],
            'all_columns': []
        })
        
        for match in matches:
            table_info = queries_by_table[match.table_name]
            
            if match.mapped_type in ['hostname', 'fqdn']:
                table_info['hostname_columns'].append(match)
            else:
                table_info['attribute_columns'].append(match)
            
            table_info['all_columns'].append(match)
        
        optimized_queries = {}
        
        for table_name, info in queries_by_table.items():
            if not info['hostname_columns']:
                logger.info(f"    ₊˚⊹ Skipping {table_name} - no hostname columns")
                continue
            
            primary_hostname = info['hostname_columns'][0]
            all_columns = [primary_hostname] + info['attribute_columns']
            
            column_names = [match.column_name for match in all_columns]
            mapped_types = [match.mapped_type for match in all_columns]
            
            query = f"""
            SELECT {', '.join([f'`{col}`' for col in column_names])}
            FROM `{table_name}`
            WHERE `{primary_hostname.column_name}` IS NOT NULL 
            AND `{primary_hostname.column_name}` != ''
            AND `{primary_hostname.column_name}` != '*Undefined'
            AND LENGTH(`{primary_hostname.column_name}`) > 2
            """
            
            optimized_queries[table_name] = {
                'query': query,
                'column_names': column_names,
                'mapped_types': mapped_types,
                'hostname_column': primary_hostname.column_name,
                'matches': all_columns
            }
        
        logger.info(f"♡ Created {len(optimized_queries)} optimized queries")
        return optimized_queries
    
    def process_table_with_intelligence(self, table_name: str, query_info: Dict) -> Dict:
        logger.info(f"༘˚⋆ Processing: {table_name}")
        start_time = time.time()
        
        try:
            query_job = self.bq_client.query(query_info['query'])
            results = query_job.result()
            
            records = []
            attribute_stats = defaultdict(int)
            row_count = 0
            
            for row in results:
                row_count += 1
                if row_count % 2000 == 0:
                    logger.info(f"    𖦹 Processed {row_count:,} rows...")
                
                if not row[0] or not self.is_valid_value(row[0]):
                    continue
                
                normalized_host = self.normalize_hostname(row[0])
                if not normalized_host:
                    continue
                
                record = {
                    'normalized_host': normalized_host,
                    'hostname': str(row[0]).strip()
                }
                
                for i, mapped_type in enumerate(query_info['mapped_types'][1:], 1):
                    if i < len(row) and self.is_valid_value(row[i]):
                        clean_value = str(row[i]).strip()
                        record[mapped_type] = clean_value
                        attribute_stats[mapped_type] += 1
                
                records.append(record)
            
            process_time = time.time() - start_time
            
            logger.info(f"    ₊˚✩ Processed {len(records):,} valid records in {process_time:.2f}s")
            
            for attr_type, count in attribute_stats.items():
                if count > 0:
                    logger.info(f"        ♡ {attr_type}: {count:,} values")
            
            return {
                'table_name': table_name,
                'records': records,
                'stats': dict(attribute_stats),
                'processing_time': process_time
            }
            
        except Exception as e:
            logger.error(f"    𐙚 Error processing {table_name}: {e}")
            return {'table_name': table_name, 'records': [], 'stats': {}, 'error': str(e)}
    
    def intelligent_merge_and_store(self, processed_data: List[Dict]):
        logger.info("⋆｡‧˚ Intelligently merging and storing data...")
        
        total_records = sum(len(data['records']) for data in processed_data)
        logger.info(f"   ༘˚⋆ Processing {total_records:,} total records")
        
        records_written = 0
        records_updated = 0
        conflicts_detected = 0
        
        for table_data in processed_data:
            table_name = table_data['table_name']
            records = table_data['records']
            
            logger.info(f"   𖦹 Storing {len(records):,} records from {table_name}")
            
            for i, record in enumerate(records):
                if i % 1000 == 0 and i > 0:
                    logger.info(f"      ♡ Processed {i:,}/{len(records):,} records...")
                
                result = self._intelligent_upsert(record, table_name)
                
                if result == 'inserted':
                    records_written += 1
                elif result == 'updated':
                    records_updated += 1
                elif result == 'conflict':
                    conflicts_detected += 1
        
        logger.info(f"   ₊˚✩ Storage complete:")
        logger.info(f"      ♡ New records: {records_written:,}")
        logger.info(f"      𖦹 Updated records: {records_updated:,}")
        logger.info(f"      ₊˚⊹ Conflicts detected: {conflicts_detected:,}")
    
    def _intelligent_upsert(self, record: Dict, table_name: str) -> str:
        normalized_host = record['normalized_host']
        
        existing_query = """
        SELECT * FROM universal_cmdb 
        WHERE normalized_host = ?
        """
        existing = self.duck_conn.execute(existing_query, [normalized_host]).fetchone()
        
        if existing:
            return self._update_existing_record(existing, record, table_name)
        else:
            return self._insert_new_record(record, table_name)
    
    def _update_existing_record(self, existing, new_record: Dict, table_name: str) -> str:
        columns_query = "PRAGMA table_info(universal_cmdb)"
        column_info = self.duck_conn.execute(columns_query).fetchall()
        column_names = [col[1] for col in column_info]
        
        updates = []
        values = []
        has_conflicts = False
        
        current_tables = existing[1] if existing[1] else ""
        if table_name not in current_tables:
            new_tables = f"{current_tables}, {table_name}" if current_tables else table_name
            updates.append("source_tables = ?")
            values.append(new_tables)
            
            current_count = len(current_tables.split(', ')) if current_tables else 0
            updates.append("source_count = ?")
            values.append(current_count + 1)
        
        for key, new_value in new_record.items():
            if key == 'normalized_host' or key not in column_names:
                continue
                
            col_index = column_names.index(key)
            existing_value = existing[col_index] if col_index < len(existing) else None
            
            if existing_value and str(existing_value).strip():
                existing_clean = str(existing_value).strip()
                new_clean = str(new_value).strip()
                
                if existing_clean != new_clean:
                    existing_values = set(v.strip() for v in existing_clean.split(' | '))
                    new_values = existing_values.copy()
                    new_values.add(new_clean)
                    
                    final_value = ' | '.join(sorted(new_values))
                    has_conflicts = len(new_values) > 1
                else:
                    final_value = existing_clean
            else:
                final_value = str(new_value).strip()
            
            updates.append(f"{key} = ?")
            values.append(final_value)
        
        if updates:
            updates.append("last_updated = CURRENT_TIMESTAMP")
            values.append(normalized_host)
            
            update_sql = f"""
            UPDATE universal_cmdb 
            SET {', '.join(updates)} 
            WHERE normalized_host = ?
            """
            self.duck_conn.execute(update_sql, values)
        
        return 'conflict' if has_conflicts else 'updated'
    
    def _insert_new_record(self, record: Dict, table_name: str) -> str:
        columns = ['normalized_host', 'source_tables', 'source_count']
        values = [record['normalized_host'], table_name, 1]
        
        for key, value in record.items():
            if key != 'normalized_host':
                columns.append(key)
                values.append(value)
        
        placeholders = ', '.join(['?'] * len(columns))
        insert_sql = f"""
        INSERT INTO universal_cmdb ({', '.join(columns)}) 
        VALUES ({placeholders})
        """
        
        self.duck_conn.execute(insert_sql, values)
        return 'inserted'
    
    def create_advanced_analytics(self):
        logger.info("₊˚✩ Creating advanced analytics views...")
        
        analytics_queries = {
            'host_coverage_analysis': """
            CREATE OR REPLACE VIEW host_coverage_analysis AS
            SELECT 
                business_unit,
                region,
                COUNT(*) as total_hosts,
                COUNT(CASE WHEN edr_coverage IS NOT NULL THEN 1 END) as edr_covered,
                COUNT(CASE WHEN tanium_coverage IS NOT NULL THEN 1 END) as tanium_covered,
                COUNT(CASE WHEN logging_in_splunk IS NOT NULL THEN 1 END) as splunk_logging,
                ROUND(COUNT(CASE WHEN edr_coverage IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2) as edr_coverage_pct,
                AVG(source_count) as avg_source_coverage
            FROM universal_cmdb
            WHERE business_unit IS NOT NULL
            GROUP BY business_unit, region
            ORDER BY total_hosts DESC
            """,
            
            'data_quality_metrics': """
            CREATE OR REPLACE VIEW data_quality_metrics AS
            SELECT 
                'hostname' as field_name,
                COUNT(*) as total_records,
                COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) as populated_count,
                ROUND(COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) * 100.0 / COUNT(*), 2) as completeness_pct
            FROM universal_cmdb
            UNION ALL
            SELECT 'business_unit', COUNT(*), COUNT(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 END),
                   ROUND(COUNT(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 END) * 100.0 / COUNT(*), 2)
            FROM universal_cmdb
            UNION ALL
            SELECT 'region', COUNT(*), COUNT(CASE WHEN region IS NOT NULL AND region != '' THEN 1 END),
                   ROUND(COUNT(CASE WHEN region IS NOT NULL AND region != '' THEN 1 END) * 100.0 / COUNT(*), 2)
            FROM universal_cmdb
            ORDER BY completeness_pct DESC
            """,
            
            'conflict_analysis': """
            CREATE OR REPLACE VIEW conflict_analysis AS
            SELECT 
                normalized_host,
                source_count,
                CASE WHEN business_unit LIKE '%|%' THEN business_unit ELSE NULL END as business_unit_conflicts,
                CASE WHEN region LIKE '%|%' THEN region ELSE NULL END as region_conflicts,
                CASE WHEN infrastructure_type LIKE '%|%' THEN infrastructure_type ELSE NULL END as infra_conflicts
            FROM universal_cmdb
            WHERE business_unit LIKE '%|%' 
               OR region LIKE '%|%' 
               OR infrastructure_type LIKE '%|%'
            ORDER BY source_count DESC
            """
        }
        
        for view_name, query in analytics_queries.items():
            try:
                self.duck_conn.execute(query)
                logger.info(f"    ♡ Created view: {view_name}")
            except Exception as e:
                logger.error(f"    ₊˚⊹ Failed to create {view_name}: {e}")
    
    def generate_comprehensive_report(self):
        logger.info("༘˚⋆ Generating comprehensive analysis report...")
        
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        logger.info(f"⋆｡‧˚ Total unique hosts: {total_hosts:,}")
        
        data_columns = [
            'hostname', 'fqdn', 'domain', 'infrastructure_type', 'region', 'country',
            'data_center', 'cloud_region', 'ip_address', 'class', 'system_classification',
            'business_unit', 'apm', 'cio', 'edr_coverage', 'tanium_coverage', 
            'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso'
        ]
        
        logger.info("𖦹 Data completeness analysis:")
        populated_columns = []
        
        for col in data_columns:
            count_query = f"""
            SELECT COUNT(*) 
            FROM universal_cmdb 
            WHERE {col} IS NOT NULL AND {col} != ''
            """
            count = self.duck_conn.execute(count_query).fetchone()[0]
            percentage = (count / total_hosts * 100) if total_hosts > 0 else 0
            
            if count > 0:
                populated_columns.append(col)
                logger.info(f"    ♡ {col}: {count:,} records ({percentage:.1f}%)")
                
                if percentage > 5:
                    sample_query = f"""
                    SELECT DISTINCT {col} 
                    FROM universal_cmdb 
                    WHERE {col} IS NOT NULL AND {col} != '' 
                    LIMIT 3
                    """
                    samples = self.duck_conn.execute(sample_query).fetchall()
                    sample_values = [str(s[0])[:25] for s in samples]
                    logger.info(f"        𖦹 Examples: {', '.join(sample_values)}")
            else:
                logger.info(f"    ₊˚⊹ {col}: No data")
        
        conflicts_query = """
        SELECT COUNT(*) 
        FROM universal_cmdb 
        WHERE business_unit LIKE '%|%' 
           OR region LIKE '%|%' 
           OR infrastructure_type LIKE '%|%'
        """
        conflicts = self.duck_conn.execute(conflicts_query).fetchone()[0]
        
        if conflicts > 0:
            logger.info(f"⋆｡‧˚ Data conflicts detected: {conflicts} hosts have conflicting values")
            
            conflict_examples = self.duck_conn.execute("""
                SELECT normalized_host, business_unit, region 
                FROM universal_cmdb 
                WHERE business_unit LIKE '%|%' OR region LIKE '%|%'
                LIMIT 3
            """).fetchall()
            
            for host, bu, region in conflict_examples:
                logger.info(f"    ₊˚⊹ {host}: BU={bu}, Region={region}")
        
        coverage_stats = self.duck_conn.execute("""
            SELECT 
                AVG(source_count) as avg_sources,
                MAX(source_count) as max_sources,
                COUNT(CASE WHEN source_count > 1 THEN 1 END) as multi_source_hosts
            FROM universal_cmdb
        """).fetchone()
        
        logger.info(f"₊˚✩ Source coverage statistics:")
        logger.info(f"    ♡ Average sources per host: {coverage_stats[0]:.1f}")
        logger.info(f"    𖦹 Maximum sources for one host: {coverage_stats[1]}")
        logger.info(f"    ⋆｡‧˚ Hosts with multiple sources: {coverage_stats[2]:,}")
        
        logger.info(f"♡ Analysis Summary:")
        logger.info(f"    ₊˚✩ Successfully populated {len(populated_columns)}/{len(data_columns)} column types")
        logger.info(f"    𖦹 Data quality: {(len(populated_columns)/len(data_columns)*100):.0f}% column coverage")
        logger.info(f"    ⋆｡‧˚ Conflicts requiring attention: {conflicts} hosts")
    
    def export_comprehensive_data(self, filename: str = "universal_cmdb_export.csv"):
        logger.info(f"༘˚⋆ Exporting comprehensive dataset to {filename}...")
        
        try:
            export_query = """
            COPY (
                SELECT * 
                FROM universal_cmdb 
                ORDER BY source_count DESC, normalized_host ASC
            ) TO ? WITH (FORMAT CSV, HEADER)
            """
            
            self.duck_conn.execute(export_query, [filename])
            
            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
            logger.info(f"♡ Export completed: {filename} ({file_size/1024/1024:.1f}MB)")
            
        except Exception as e:
            logger.error(f"𐙚 Export failed: {e}")
    
    def process_everything(self):
        logger.info("₊˚✩ Starting comprehensive CMDB processing...")
        overall_start = time.time()
        
        try:
            metadata = self.load_and_analyze_metadata()
            
            matches = self.intelligent_column_discovery(metadata)
            if not matches:
                logger.error("𐙚 No column matches found - cannot proceed")
                return
            
            queries = self.build_optimized_queries(matches)
            if not queries:
                logger.error("༘˚⋆ No valid queries generated - cannot proceed")
                return
            
            logger.info("⋆｡‧˚ Processing all tables with parallel optimization...")
            
            processed_data = []
            for table_name, query_info in queries.items():
                result = self.process_table_with_intelligence(table_name, query_info)
                processed_data.append(result)
            
            self.intelligent_merge_and_store(processed_data)
            
            self.create_advanced_analytics()
            
            self.generate_comprehensive_report()
            
            self.export_comprehensive_data()
            
            total_time = time.time() - overall_start
            logger.info(f"\n₊˚✩ COMPLETE SUCCESS!")
            logger.info(f"⋆｡‧˚ Total processing time: {total_time:.1f} seconds")
            logger.info(f"♡ Database: {self.duckdb_path}")
            logger.info(f"𖦹 Export: universal_cmdb_export.csv")
            
        except Exception as e:
            logger.error(f"𐙚 Processing failed: {e}")
            import traceback
            logger.error(f"༘˚⋆ Error details:\n{traceback.format_exc()}")
    
    def close(self):
        logger.info("₊˚⊹ Gracefully closing connections...")
        try:
            self.duck_conn.close()
            logger.info("♡ All connections closed successfully")
        except Exception as e:
            logger.warning(f"⋆｡‧˚ Close warning: {e}")

if __name__ == "__main__":
    logger.info("₊˚✩ OPTIMIZED UNIVERSAL CMDB PROCESSOR")
    logger.info("═══════════════════════════════════════════════════════════")
    
    processor = None
    try:
        processor = OptimizedHostDataProcessor(
            "reviewed_labeled_columns.json", 
            "universal_cmdb.db"
        )
        
        processor.process_everything()
        
    except KeyboardInterrupt:
        logger.warning("₊˚⊹ Processing interrupted by user")
    except Exception as e:
        logger.error(f"𐙚 Critical error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if processor:
            processor.close()