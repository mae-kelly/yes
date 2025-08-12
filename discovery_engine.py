#!/usr/bin/env python3

import os
import asyncio
import logging
import duckdb
import time
import threading
import re
import json
import hashlib
from typing import Dict, List, Any, Tuple, Set, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from pathlib import Path
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import statistics
import multiprocessing as mp
from contextlib import asynccontextmanager
import functools

from gcp_client import BigQueryClientManager
from intelligent_content_matcher import IntelligentContentMatcher
from intelligent_cache_manager import IntelligentCacheManager

# Simplified intelligence engine for compatibility
class SimpleIntelligenceEngine:
    def __init__(self, config=None):
        self.config = config or {}
        
    async def enhance_discovery_intelligence(self, context):
        return {
            'strategy_recommendation': {
                'strategy_name': 'simple_reliable',
                'parameters': {
                    'batch_size': 500,
                    'parallel_workers': 8,
                    'timeout_seconds': 300,
                    'validation_level': 'standard'
                }
            },
            'predictions': {'estimated_assets': 1000},
            'insights': [],
            'explanations': {}
        }
    
    async def learn_from_discovery_results(self, results, predictions=None):
        return {'learned_patterns': {}, 'updated_strategies': {}}
    
    def get_intelligence_summary(self):
        return {'intelligence_status': 'simple', 'learning_iterations': 0}

try:
    from intelligence_engine import IntelligenceEngine
except ImportError:
    IntelligenceEngine = SimpleIntelligenceEngine

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound, Forbidden, BadRequest
except ImportError:
    bigquery = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ao1_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleProgressReporter:
    @staticmethod
    def info(msg: str):
        print(f"   {msg}")
        logger.info(msg)
    
    @staticmethod
    def success(msg: str):
        print(f"   ✅ {msg}")
        logger.info(msg)
    
    @staticmethod
    def warning(msg: str):
        print(f"   ⚠️ {msg}")
        logger.warning(msg)
    
    @staticmethod
    def error(msg: str):
        print(f"   ❌ {msg}")
        logger.error(msg)
    
    @staticmethod
    def progress(step: int, total: int, msg: str):
        pct = (step / total * 100) if total > 0 else 0
        print(f"   {pct:5.1f}% ({step:,}/{total:,}) {msg}")

class SimpleOptimizedAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        SimpleProgressReporter.info("Initializing simple discovery with enhanced reliability...")
        
        self.client_manager = BigQueryClientManager(project_id)
        
        # Test BigQuery connection immediately
        if not self.client_manager.test_connection():
            raise Exception("Failed to connect to BigQuery - check authentication")
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
            if not self.chronicle_client_manager.test_connection():
                self.chronicle_client_manager = None
                SimpleProgressReporter.warning("Chronicle access not available")
        except:
            self.chronicle_client_manager = None
            SimpleProgressReporter.warning("Chronicle access not available")
        
        self.matcher = IntelligentContentMatcher()
        self.cache = IntelligentCacheManager(
            cache_dir=self.config.get('cache_dir', '.cache'),
            max_memory_mb=self.config.get('max_memory_mb', 512),
            max_disk_gb=self.config.get('max_disk_gb', 5)
        )
        
        self.intelligence_engine = IntelligenceEngine(self.config)
        
        self.db_path = self.config.get('database_path', 'ao1_simple_cmdb.db')
        SimpleProgressReporter.info(f"Database will be created at: {self.db_path}")
        
        # Initialize database with enhanced error checking
        self._setup_database_with_verification()
        
        SimpleProgressReporter.success("Simple discovery with enhanced reliability ready")
    
    def _setup_database_with_verification(self):
        """Setup database with proper error checking and verification"""
        try:
            # Remove existing database if it exists and is corrupted
            if os.path.exists(self.db_path):
                try:
                    test_conn = duckdb.connect(self.db_path)
                    test_conn.execute("SELECT 1").fetchone()
                    test_conn.close()
                except:
                    SimpleProgressReporter.warning(f"Removing corrupted database: {self.db_path}")
                    os.remove(self.db_path)
            
            self.conn = duckdb.connect(self.db_path)
            self.conn.execute("PRAGMA threads=4")
            self.conn.execute("PRAGMA memory_limit='1GB'")
            
            # Create enhanced table with better schema
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS ao1_discovery_inventory (
                hostname VARCHAR PRIMARY KEY,
                fqdn VARCHAR DEFAULT '',
                ip_address VARCHAR DEFAULT '',
                infrastructure_type VARCHAR DEFAULT '',
                system_classification VARCHAR DEFAULT '',
                global_region VARCHAR DEFAULT '',
                business_unit VARCHAR DEFAULT '',
                in_splunk BOOLEAN DEFAULT FALSE,
                in_chronicle BOOLEAN DEFAULT FALSE,
                in_gso BOOLEAN DEFAULT FALSE,
                edr_coverage VARCHAR DEFAULT 'No',
                tanium_coverage VARCHAR DEFAULT 'No',
                dlp_coverage VARCHAR DEFAULT 'No',
                source_systems TEXT DEFAULT '',
                source_count INTEGER DEFAULT 0,
                coverage_completeness_score DOUBLE DEFAULT 0.0,
                visibility_gap_severity VARCHAR DEFAULT 'unknown',
                data_quality_score DOUBLE DEFAULT 0.0,
                discovery_timestamp TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW()
            )
            """
            
            self.conn.execute(create_table_sql)
            
            # Create indexes for performance
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_hostname ON ao1_discovery_inventory(hostname)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_coverage_score ON ao1_discovery_inventory(coverage_completeness_score)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_source_count ON ao1_discovery_inventory(source_count)")
            
            # Verify table creation
            result = self.conn.execute("SELECT COUNT(*) FROM ao1_discovery_inventory").fetchone()
            SimpleProgressReporter.success(f"Database initialized with {result[0]} existing records")
            
            # Commit the schema changes
            self.conn.commit()
            
        except Exception as e:
            SimpleProgressReporter.error(f"Database setup failed: {e}")
            raise
    
    async def execute_simple_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        SimpleProgressReporter.info("Starting enhanced simple discovery")
        
        try:
            SimpleProgressReporter.info("Phase 1: Intelligence analysis")
            discovery_context = {
                'project_id': self.project_id,
                'discovery_type': 'simple_enhanced',
                'timestamp': datetime.now().isoformat()
            }
            
            intelligence_results = await self.intelligence_engine.enhance_discovery_intelligence(discovery_context)
            strategy_params = intelligence_results['strategy_recommendation']['parameters']
            
            SimpleProgressReporter.info("Phase 2: Finding suitable tables with enhanced detection")
            table_metadata = await self._discover_tables_enhanced()
            
            if not table_metadata:
                SimpleProgressReporter.error("No suitable tables found")
                return {'error': 'No suitable tables found', 'total_assets': 0}, {}
            
            SimpleProgressReporter.success(f"Found {len(table_metadata)} suitable tables")
            
            SimpleProgressReporter.info("Phase 3: Extracting hostnames with enhanced validation")
            all_hostnames = await self._extract_hostnames_enhanced(table_metadata)
            
            if not all_hostnames:
                SimpleProgressReporter.error("No hostnames extracted from tables")
                return {'error': 'No hostnames found', 'total_assets': 0}, {}
            
            SimpleProgressReporter.success(f"Extracted {len(all_hostnames)} unique hostnames")
            
            SimpleProgressReporter.info("Phase 4: Building enhanced asset inventory")
            asset_count = await self._build_enhanced_inventory(all_hostnames, table_metadata)
            
            SimpleProgressReporter.info("Phase 5: Learning from results")
            learning_results = await self.intelligence_engine.learn_from_discovery_results({
                'total_assets': asset_count,
                'processing_time': time.time() - start_time,
                'strategy_used': intelligence_results['strategy_recommendation']['strategy_name']
            })
            
            # Verify database contents
            verification_result = self._verify_database_contents()
            
            processing_time = time.time() - start_time
            stats = {
                'processing_time': processing_time,
                'total_assets': asset_count,
                'verified_assets': verification_result['total_records'],
                'tables_processed': len(table_metadata),
                'database_path': self.db_path,
                'database_size_mb': verification_result['file_size_mb'],
                'discovery_method': 'simple_enhanced',
                'engine_type': 'SimpleEnhanced',
                'intelligence_results': intelligence_results,
                'learning_results': learning_results,
                'intelligence_summary': self.intelligence_engine.get_intelligence_summary(),
                'verification': verification_result
            }
            
            queries = self._create_enhanced_queries()
            
            SimpleProgressReporter.success(f"Enhanced simple discovery complete: {asset_count} assets in {processing_time:.1f}s")
            return stats, queries
            
        except Exception as e:
            SimpleProgressReporter.error(f"Simple discovery failed: {e}")
            logger.exception("Discovery failed with exception:")
            return {'error': str(e), 'total_assets': 0}, {}
    
    async def _discover_tables_enhanced(self) -> List[Dict]:
        """Enhanced table discovery with better hostname detection"""
        tables = []
        
        try:
            with self.client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=self.project_id))
                SimpleProgressReporter.info(f"Found {len(datasets)} datasets")
                
                if not datasets:
                    SimpleProgressReporter.error("No datasets found in project")
                    return []
                
                for i, dataset in enumerate(datasets):
                    SimpleProgressReporter.progress(i+1, len(datasets), f"Analyzing {dataset.dataset_id}")
                    
                    try:
                        dataset_ref = client.dataset(dataset.dataset_id)
                        dataset_tables = list(client.list_tables(dataset_ref))
                        
                        SimpleProgressReporter.info(f"Dataset {dataset.dataset_id} has {len(dataset_tables)} tables")
                        
                        for table_ref in dataset_tables:
                            try:
                                full_table = client.get_table(table_ref)
                                if not full_table.schema or full_table.num_rows == 0:
                                    continue
                                
                                columns = [field.name for field in full_table.schema]
                                hostname_col = self._find_hostname_column_enhanced(columns)
                                
                                if hostname_col:
                                    table_info = {
                                        'project_id': self.project_id,
                                        'dataset_id': dataset.dataset_id,
                                        'table_path': f"{self.project_id}.{dataset.dataset_id}.{table_ref.table_id}",
                                        'hostname_column': hostname_col,
                                        'table_id': table_ref.table_id,
                                        'row_count': full_table.num_rows,
                                        'all_columns': columns
                                    }
                                    tables.append(table_info)
                                    SimpleProgressReporter.info(f"Added table {table_ref.table_id} with hostname column '{hostname_col}'")
                                    
                            except Exception as table_error:
                                SimpleProgressReporter.warning(f"Failed to analyze table {table_ref.table_id}: {table_error}")
                                continue
                                
                    except Exception as dataset_error:
                        SimpleProgressReporter.warning(f"Failed to analyze dataset {dataset.dataset_id}: {dataset_error}")
                        continue
                        
        except Exception as e:
            SimpleProgressReporter.error(f"Table discovery failed: {e}")
            logger.exception("Table discovery failed:")
        
        SimpleProgressReporter.success(f"Found {len(tables)} usable tables with hostname columns")
        return tables
    
    def _find_hostname_column_enhanced(self, columns: List[str]) -> Optional[str]:
        """Enhanced hostname column detection"""
        # Primary hostname indicators (exact matches first)
        primary_indicators = [
            'hostname', 'host_name', 'computer_name', 'machine_name', 'device_name',
            'endpoint_name', 'server_name', 'asset_name', 'node_name', 'system_name'
        ]
        
        # Secondary indicators (partial matches)
        secondary_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system'
        ]
        
        # Additional indicators for specific systems
        system_indicators = [
            'workstation', 'pc', 'laptop', 'desktop', 'vm', 'instance', 'appliance'
        ]
        
        # Check exact matches first
        for col in columns:
            col_lower = col.lower()
            if col_lower in primary_indicators:
                SimpleProgressReporter.info(f"Found exact hostname match: {col}")
                return col
        
        # Check partial matches
        for col in columns:
            col_lower = col.lower()
            for indicator in secondary_indicators:
                if indicator in col_lower and 'id' not in col_lower and 'count' not in col_lower:
                    SimpleProgressReporter.info(f"Found hostname indicator match: {col}")
                    return col
        
        # Check system indicators
        for col in columns:
            col_lower = col.lower()
            for indicator in system_indicators:
                if indicator in col_lower and 'id' not in col_lower:
                    SimpleProgressReporter.info(f"Found system indicator match: {col}")
                    return col
        
        # Check for any column that might contain hostnames (last resort)
        for col in columns:
            col_lower = col.lower()
            if ('name' in col_lower and 
                'user' not in col_lower and 
                'file' not in col_lower and 
                'display' not in col_lower and
                len(col_lower) < 20):
                SimpleProgressReporter.info(f"Found potential hostname field: {col}")
                return col
        
        return None
    
    async def _extract_hostnames_enhanced(self, tables: List[Dict]) -> List[str]:
        """Enhanced hostname extraction with better error handling"""
        all_hostnames = set()
        
        for i, table in enumerate(tables):
            SimpleProgressReporter.progress(i+1, len(tables), f"Extracting from {table['table_id']}")
            
            row_count = table.get('row_count', 0)
            sampling_clause = ""
            
            # Adjust sampling based on table size
            if row_count > 50000000:
                sampling_clause = "TABLESAMPLE SYSTEM (1 PERCENT)"
            elif row_count > 10000000:
                sampling_clause = "TABLESAMPLE SYSTEM (5 PERCENT)"
            elif row_count > 1000000:
                sampling_clause = "TABLESAMPLE SYSTEM (10 PERCENT)"
            
            # Build query with proper escaping and validation
            hostname_col = table['hostname_column']
            table_path = table['table_path']
            
            query = f"""
            SELECT DISTINCT 
                UPPER(TRIM(CAST(`{hostname_col}` AS STRING))) as hostname
            FROM `{table_path}` {sampling_clause}
            WHERE `{hostname_col}` IS NOT NULL
                AND LENGTH(TRIM(CAST(`{hostname_col}` AS STRING))) >= 2
                AND LENGTH(TRIM(CAST(`{hostname_col}` AS STRING))) <= 253
                AND TRIM(CAST(`{hostname_col}` AS STRING)) NOT LIKE '%@%'
                AND TRIM(CAST(`{hostname_col}` AS STRING)) NOT LIKE 'http%'
                AND UPPER(TRIM(CAST(`{hostname_col}` AS STRING))) NOT IN ('UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY')
            LIMIT 10000
            """
            
            try:
                with self.client_manager.get_client() as client:
                    SimpleProgressReporter.info(f"Querying {table_path} for hostnames...")
                    
                    # Add timeout and retry logic
                    job_config = bigquery.QueryJobConfig(
                        job_timeout_ms=120000,  # 2 minutes
                        use_query_cache=True
                    )
                    
                    job = client.query(query, job_config=job_config)
                    results = list(job.result())
                    
                    table_hostnames = 0
                    for row in results:
                        if row[0]:
                            hostname = str(row[0]).strip()
                            if self._is_valid_hostname_enhanced(hostname):
                                all_hostnames.add(hostname)
                                table_hostnames += 1
                    
                    SimpleProgressReporter.success(f"Extracted {table_hostnames} hostnames from {table['table_id']}")
                    
            except Exception as e:
                SimpleProgressReporter.error(f"Hostname extraction failed for {table['table_id']}: {e}")
                logger.exception(f"Query failed for table {table_path}:")
                continue
        
        SimpleProgressReporter.success(f"Total unique hostnames extracted: {len(all_hostnames)}")
        return list(all_hostnames)
    
    def _is_valid_hostname_enhanced(self, hostname: str) -> bool:
        """Enhanced hostname validation"""
        if not hostname or len(hostname) < 2 or len(hostname) > 253:
            return False
        
        # Remove common invalid values
        invalid_values = [
            'UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 'TEST', 'EXAMPLE', 
            'LOCALHOST', 'DUMMY', 'SAMPLE', 'PLACEHOLDER', 'DEFAULT',
            'ERROR', 'INVALID', 'MISSING', 'UNDEFINED', 'TEMP', 'TMP'
        ]
        
        if hostname.upper() in invalid_values:
            return False
        
        # Check for obvious non-hostname patterns
        if any(char in hostname for char in ['@', '/', '\\', ' ', '\t', '\n', '|', '"', "'"]):
            return False
        
        # Must contain at least one letter
        if not any(c.isalpha() for c in hostname):
            return False
        
        # Check for reasonable hostname patterns
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$', hostname):
            return True
        
        # Allow simple alphanumeric hostnames
        if re.match(r'^[a-zA-Z0-9]+$', hostname) and len(hostname) >= 3:
            return True
        
        return False
    
    async def _build_enhanced_inventory(self, hostnames: List[str], tables: List[Dict]) -> int:
        """Enhanced inventory building with better error handling and verification"""
        assets = []
        
        SimpleProgressReporter.info(f"Building inventory for {len(hostnames)} hostnames")
        
        # Determine source system coverage
        source_systems = set()
        for table in tables:
            table_path = table['table_path'].lower()
            if 'splunk' in table_path:
                source_systems.add('splunk')
            if 'chronicle' in table_path:
                source_systems.add('chronicle')
            if 'crowdstrike' in table_path:
                source_systems.add('crowdstrike')
            if 'gso' in table_path:
                source_systems.add('gso')
        
        for i, hostname in enumerate(hostnames):
            if i % 100 == 0:
                SimpleProgressReporter.progress(i+1, len(hostnames), "Building assets")
            
            # Enhanced asset profile
            asset = {
                'hostname': hostname,
                'fqdn': self._generate_fqdn_if_missing(hostname),
                'ip_address': '',  # Could be enriched later
                'infrastructure_type': self._infer_infrastructure_type(hostname),
                'system_classification': self._infer_system_classification(hostname),
                'global_region': self._infer_region(hostname),
                'business_unit': '',
                'in_splunk': 'splunk' in source_systems,
                'in_chronicle': 'chronicle' in source_systems,
                'in_gso': 'gso' in source_systems,
                'edr_coverage': 'Yes' if 'crowdstrike' in source_systems else 'No',
                'tanium_coverage': 'No',  # Could be enhanced with tanium detection
                'dlp_coverage': 'No',     # Could be enhanced with DLP detection
                'source_systems': ','.join(sorted(source_systems)),
                'source_count': len(tables),
                'coverage_completeness_score': self._calculate_coverage_score(source_systems),
                'visibility_gap_severity': self._calculate_gap_severity(source_systems),
                'data_quality_score': self._calculate_data_quality_score(hostname, source_systems),
                'discovery_timestamp': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            assets.append(asset)
        
        # Insert into database with proper error handling
        if assets:
            return await self._insert_assets_with_verification(assets)
        else:
            SimpleProgressReporter.error("No assets to insert")
            return 0
    
    async def _insert_assets_with_verification(self, assets: List[Dict]) -> int:
        """Insert assets with proper error handling and verification"""
        try:
            SimpleProgressReporter.info(f"Inserting {len(assets)} assets into database")
            
            # Prepare columns and placeholders
            columns = list(assets[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            insert_query = f"INSERT OR REPLACE INTO ao1_discovery_inventory ({column_names}) VALUES ({placeholders})"
            
            # Prepare values
            values_list = []
            for asset in assets:
                values = []
                for col in columns:
                    value = asset[col]
                    # Handle boolean values properly for DuckDB
                    if isinstance(value, bool):
                        values.append(value)
                    elif value is None:
                        values.append('')
                    else:
                        values.append(str(value))
                values_list.append(values)
            
            # Execute the insert in batches
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(values_list), batch_size):
                batch = values_list[i:i + batch_size]
                try:
                    self.conn.executemany(insert_query, batch)
                    total_inserted += len(batch)
                    
                    if i % (batch_size * 5) == 0:  # Progress every 5 batches
                        SimpleProgressReporter.progress(i + len(batch), len(values_list), "Inserting assets")
                        
                except Exception as batch_error:
                    SimpleProgressReporter.error(f"Batch insert failed at position {i}: {batch_error}")
                    # Try inserting one by one in this batch
                    for j, single_values in enumerate(batch):
                        try:
                            self.conn.execute(insert_query, single_values)
                            total_inserted += 1
                        except Exception as single_error:
                            SimpleProgressReporter.warning(f"Failed to insert single record {i+j}: {single_error}")
            
            # Commit the transaction
            self.conn.commit()
            
            # Verify the insertion
            verification_query = "SELECT COUNT(*) FROM ao1_discovery_inventory"
            result = self.conn.execute(verification_query).fetchone()
            actual_count = result[0] if result else 0
            
            SimpleProgressReporter.success(f"Successfully inserted {total_inserted} assets")
            SimpleProgressReporter.info(f"Database now contains {actual_count} total records")
            
            return total_inserted
            
        except Exception as e:
            SimpleProgressReporter.error(f"Asset insertion failed: {e}")
            logger.exception("Asset insertion failed:")
            
            # Try to rollback
            try:
                self.conn.rollback()
            except:
                pass
            
            return 0
    
    def _generate_fqdn_if_missing(self, hostname: str) -> str:
        """Generate a potential FQDN if hostname doesn't contain domain"""
        if '.' in hostname:
            return hostname
        # Could be enhanced with domain mapping logic
        return hostname
    
    def _infer_infrastructure_type(self, hostname: str) -> str:
        """Infer infrastructure type from hostname patterns"""
        hostname_lower = hostname.lower()
        
        if any(x in hostname_lower for x in ['cloud', 'aws', 'azure', 'gcp']):
            return 'Cloud'
        elif any(x in hostname_lower for x in ['vm', 'virtual']):
            return 'Virtual'
        elif any(x in hostname_lower for x in ['api', 'service']):
            return 'API/Service'
        else:
            return 'On-Premises'
    
    def _infer_system_classification(self, hostname: str) -> str:
        """Infer system classification from hostname patterns"""
        hostname_lower = hostname.lower()
        
        if any(x in hostname_lower for x in ['web', 'www', 'apache', 'nginx', 'iis']):
            return 'Web Server'
        elif any(x in hostname_lower for x in ['db', 'database', 'sql', 'oracle', 'mysql']):
            return 'Database Server'
        elif any(x in hostname_lower for x in ['app', 'application']):
            return 'Application Server'
        elif any(x in hostname_lower for x in ['dc', 'domain', 'ad']):
            return 'Domain Controller'
        elif any(x in hostname_lower for x in ['fw', 'firewall', 'proxy']):
            return 'Security Appliance'
        elif any(x in hostname_lower for x in ['win', 'windows']):
            return 'Windows Server'
        elif any(x in hostname_lower for x in ['lin', 'linux', 'ubuntu', 'centos']):
            return 'Linux Server'
        else:
            return 'Generic Server'
    
    def _infer_region(self, hostname: str) -> str:
        """Infer region from hostname patterns"""
        hostname_lower = hostname.lower()
        
        if any(x in hostname_lower for x in ['us', 'usa', 'america']):
            return 'US'
        elif any(x in hostname_lower for x in ['eu', 'europe']):
            return 'EU'
        elif any(x in hostname_lower for x in ['ap', 'asia', 'pacific']):
            return 'APAC'
        else:
            return 'Unknown'
    
    def _calculate_coverage_score(self, source_systems: Set[str]) -> float:
        """Calculate coverage completeness score"""
        max_sources = 4  # splunk, chronicle, crowdstrike, gso
        score = (len(source_systems) / max_sources) * 100
        return min(100.0, score)
    
    def _calculate_gap_severity(self, source_systems: Set[str]) -> str:
        """Calculate visibility gap severity"""
        coverage_score = self._calculate_coverage_score(source_systems)
        
        if coverage_score >= 75:
            return 'low'
        elif coverage_score >= 50:
            return 'medium'
        elif coverage_score >= 25:
            return 'high'
        else:
            return 'critical'
    
    def _calculate_data_quality_score(self, hostname: str, source_systems: Set[str]) -> float:
        """Calculate data quality score"""
        score = 50.0  # Base score
        
        # Hostname quality factors
        if len(hostname) >= 3:
            score += 10
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', hostname):
            score += 15
        
        # Source diversity bonus
        score += len(source_systems) * 10
        
        return min(100.0, score)
    
    def _verify_database_contents(self) -> Dict[str, Any]:
        """Verify database contents and return statistics"""
        try:
            # Check if database file exists
            if not os.path.exists(self.db_path):
                return {'error': 'Database file does not exist'}
            
            # Get file size
            file_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            
            # Check table existence and record count
            tables_info = {}
            
            # Get table list
            tables_result = self.conn.execute("SHOW TABLES").fetchall()
            
            total_records = 0
            for (table_name,) in tables_result:
                try:
                    count_result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                    record_count = count_result[0] if count_result else 0
                    tables_info[table_name] = record_count
                    total_records += record_count
                except Exception as e:
                    tables_info[table_name] = f'Error: {e}'
            
            # Get sample data for verification
            sample_data = None
            if total_records > 0:
                try:
                    sample_result = self.conn.execute("SELECT hostname, infrastructure_type, system_classification FROM ao1_discovery_inventory LIMIT 3").fetchall()
                    sample_data = [dict(zip(['hostname', 'infrastructure_type', 'system_classification'], row)) for row in sample_result]
                except Exception as e:
                    sample_data = f'Sample query failed: {e}'
            
            verification = {
                'database_exists': True,
                'file_size_mb': round(file_size_mb, 2),
                'total_records': total_records,
                'tables': tables_info,
                'sample_data': sample_data,
                'verification_timestamp': datetime.now().isoformat()
            }
            
            SimpleProgressReporter.success(f"Database verification complete: {total_records} total records")
            return verification
            
        except Exception as e:
            SimpleProgressReporter.error(f"Database verification failed: {e}")
            return {'error': f'Database verification failed: {e}'}
    
    def _create_enhanced_queries(self) -> Dict[str, str]:
        """Create enhanced analysis queries"""
        return {
            'overview': f"""
                -- AO1 Discovery Overview
                SELECT 
                    COUNT(*) as total_assets,
                    COUNT(DISTINCT infrastructure_type) as infrastructure_types,
                    COUNT(DISTINCT system_classification) as system_types,
                    AVG(coverage_completeness_score) as avg_coverage_score,
                    AVG(data_quality_score) as avg_quality_score
                FROM ao1_discovery_inventory;
            """,
            
            'coverage_summary': f"""
                -- Coverage Summary by Source System
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                    SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                    SUM(CASE WHEN in_gso THEN 1 ELSE 0 END) as gso_coverage,
                    SUM(CASE WHEN edr_coverage = 'Yes' THEN 1 ELSE 0 END) as edr_coverage,
                    AVG(coverage_completeness_score) as avg_coverage_score
                FROM ao1_discovery_inventory;
            """,
            
            'visibility_gaps': f"""
                -- Visibility Gap Analysis
                SELECT 
                    visibility_gap_severity,
                    COUNT(*) as asset_count,
                    ROUND(AVG(coverage_completeness_score), 2) as avg_score,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ao1_discovery_inventory), 2) as percentage
                FROM ao1_discovery_inventory
                GROUP BY visibility_gap_severity
                ORDER BY 
                    CASE visibility_gap_severity 
                        WHEN 'critical' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        WHEN 'low' THEN 4 
                        ELSE 5 
                    END;
            """,
            
            'infrastructure_breakdown': f"""
                -- Infrastructure Type Breakdown
                SELECT 
                    infrastructure_type,
                    COUNT(*) as count,
                    ROUND(AVG(coverage_completeness_score), 2) as avg_coverage,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ao1_discovery_inventory), 2) as percentage
                FROM ao1_discovery_inventory
                WHERE infrastructure_type != ''
                GROUP BY infrastructure_type
                ORDER BY count DESC;
            """,
            
            'system_classification': f"""
                -- System Classification Analysis
                SELECT 
                    system_classification,
                    COUNT(*) as count,
                    ROUND(AVG(coverage_completeness_score), 2) as avg_coverage,
                    SUM(CASE WHEN edr_coverage = 'Yes' THEN 1 ELSE 0 END) as edr_protected
                FROM ao1_discovery_inventory
                WHERE system_classification != ''
                GROUP BY system_classification
                ORDER BY count DESC;
            """,
            
            'top_assets': f"""
                -- Top Assets by Coverage Score
                SELECT 
                    hostname, 
                    infrastructure_type, 
                    system_classification,
                    coverage_completeness_score,
                    data_quality_score,
                    visibility_gap_severity,
                    source_systems
                FROM ao1_discovery_inventory
                ORDER BY coverage_completeness_score DESC, data_quality_score DESC
                LIMIT 25;
            """,
            
            'gap_analysis': f"""
                -- Assets with Critical Visibility Gaps
                SELECT 
                    hostname,
                    infrastructure_type,
                    system_classification,
                    coverage_completeness_score,
                    visibility_gap_severity,
                    CASE 
                        WHEN NOT in_splunk THEN 'Missing Splunk, '
                        ELSE ''
                    END ||
                    CASE 
                        WHEN NOT in_chronicle THEN 'Missing Chronicle, '
                        ELSE ''
                    END ||
                    CASE 
                        WHEN edr_coverage = 'No' THEN 'Missing EDR, '
                        ELSE ''
                    END as missing_coverage
                FROM ao1_discovery_inventory
                WHERE visibility_gap_severity IN ('critical', 'high')
                ORDER BY 
                    CASE visibility_gap_severity WHEN 'critical' THEN 1 ELSE 2 END,
                    coverage_completeness_score ASC
                LIMIT 50;
            """
        }
    
    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                SimpleProgressReporter.info("Database connection closed")
        except Exception as e:
            SimpleProgressReporter.warning(f"Error closing database: {e}")

# Keep the other classes for compatibility but simplified
class IntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        self.intelligence_engine = SimpleIntelligenceEngine(self.config)
        self.db_path = self.config.get('database_path', 'ao1_intelligent_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        self._setup_basic_tables()
    
    def _setup_basic_tables(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS intelligent_ao1_inventory (hostname VARCHAR PRIMARY KEY, infrastructure_type VARCHAR, system_classification VARCHAR, source_count INTEGER DEFAULT 0, intelligence_score DOUBLE DEFAULT 0.0, discovery_timestamp TIMESTAMP DEFAULT NOW())""")
    
    async def execute_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        
        discovery_context = {
            'project_id': self.project_id,
            'discovery_type': 'intelligent_basic',
            'timestamp': datetime.now().isoformat()
        }
        
        intelligence_results = await self.intelligence_engine.enhance_discovery_intelligence(discovery_context)
        
        learning_results = await self.intelligence_engine.learn_from_discovery_results({
            'total_assets': 0,
            'processing_time': time.time() - start_time,
            'strategy_used': 'intelligent_basic'
        })
        
        stats = {
            'processing_time': time.time() - start_time,
            'total_assets': 0,
            'database_path': self.db_path,
            'discovery_method': 'intelligent_basic',
            'engine_type': 'IntelligentBasic',
            'intelligence_results': intelligence_results,
            'learning_results': learning_results,
            'intelligence_summary': self.intelligence_engine.get_intelligence_summary()
        }
        queries = {
            'intelligent_overview': "SELECT * FROM intelligent_ao1_inventory;"
        }
        return stats, queries
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

# Placeholder for SuperOptimizedAO1Discovery - falls back to SimpleOptimizedAO1Discovery
class SuperOptimizedAO1Discovery(SimpleOptimizedAO1Discovery):
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        super().__init__(project_id, config)
        self.engine_type = "SuperOptimized"
    
    async def execute_super_optimized_discovery(self):
        return await self.execute_simple_discovery()

if __name__ == "__main__":
    import sys
    
    def main():
        if len(sys.argv) < 2:
            print("Usage: python discovery_engine.py <project_id> [discovery_type]")
            sys.exit(1)
        
        project_id = sys.argv[1]
        discovery_type = sys.argv[2] if len(sys.argv) > 2 else "simple"
        
        async def run_discovery():
            if discovery_type.lower() == "super":
                discovery = SuperOptimizedAO1Discovery(project_id)
                stats, queries = await discovery.execute_super_optimized_discovery()
            else:
                discovery = SimpleOptimizedAO1Discovery(project_id)
                stats, queries = await discovery.execute_simple_discovery()
            
            print("\n" + "="*50)
            print("DISCOVERY COMPLETE")
            print("="*50)
            print(f"Processing Time: {stats.get('processing_time', 0):.2f} seconds")
            print(f"Total Assets: {stats.get('total_assets', 0):,}")
            print(f"Database Path: {stats.get('database_path', 'N/A')}")
            
            if 'verification' in stats:
                verification = stats['verification']
                print(f"Verified Records: {verification.get('total_records', 0):,}")
                print(f"Database Size: {verification.get('file_size_mb', 0):.2f} MB")
            
            discovery.close()
        
        asyncio.run(run_discovery())
    
    main()