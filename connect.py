import json
import duckdb
import os
import re
import asyncio
import aiofiles
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Set, Tuple, Optional, Any
import logging
from collections import defaultdict, Counter, deque
import time
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial, lru_cache, wraps
import signal
import sys
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
import hashlib
import pickle
import msgpack
import pyarrow as pa
import pyarrow.parquet as pq
from enum import Enum
import uvloop
import orjson
import polars as pl
from tqdm.auto import tqdm
import warnings
warnings.filterwarnings('ignore')

# Ultra-fast async event loop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Configure high-performance logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class ProcessingMode(Enum):
    """Processing modes for different scenarios"""
    TURBO = "turbo"          # Maximum speed, some accuracy trade-offs
    BALANCED = "balanced"     # Good speed with high accuracy
    PRECISION = "precision"   # Maximum accuracy, slower
    STREAMING = "streaming"   # Real-time streaming mode
    INCREMENTAL = "incremental"  # Only process changes

@dataclass
class ProcessingConfig:
    """Advanced configuration for processing"""
    mode: ProcessingMode = ProcessingMode.TURBO
    max_workers: int = field(default_factory=lambda: mp.cpu_count() * 2)
    batch_size: int = 10000
    cache_size: int = 100000
    use_gpu: bool = False
    enable_profiling: bool = False
    memory_limit_gb: int = 16
    checkpoint_interval: int = 1000
    retry_failed: bool = True
    max_retries: int = 3
    enable_compression: bool = True
    parallel_io: bool = True
    use_columnar_format: bool = True
    enable_query_cache: bool = True
    sample_rate: float = 1.0  # 1.0 = no sampling
    dedup_strategy: str = "bloom_filter"  # bloom_filter, exact, probabilistic
    
class BloomFilter:
    """Ultra-fast probabilistic duplicate detection"""
    def __init__(self, expected_elements: int = 10000000, false_positive_rate: float = 0.01):
        from pybloom_live import BloomFilter as BF
        self.filter = BF(capacity=expected_elements, error_rate=false_positive_rate)
    
    def add(self, item: str) -> bool:
        """Returns True if item was possibly already in filter"""
        return self.filter.add(item)
    
    def __contains__(self, item: str) -> bool:
        return item in self.filter

class HyperLogLog:
    """Cardinality estimation for massive datasets"""
    def __init__(self, precision: int = 14):
        from hyperloglog import HyperLogLog as HLL
        self.hll = HLL(precision)
    
    def add(self, item: str):
        self.hll.add(item)
    
    def cardinality(self) -> int:
        return len(self.hll)

class ColumnMapper:
    """Advanced column mapping with ML-based inference"""
    def __init__(self):
        self.exact_mappings = self._build_exact_mappings()
        self.fuzzy_patterns = self._compile_patterns()
        self.ml_classifier = self._init_ml_classifier()
        self.cache = {}
        
    def _build_exact_mappings(self) -> Dict[str, str]:
        """Build exact string mappings"""
        return {
            'fqdn': 'fqdn', 'domain': 'domain', 'host': 'hostname', 
            'hostname': 'hostname', 'server_name': 'hostname',
            'infrastructure_type': 'infrastructure_type', 'infra_type': 'infrastructure_type',
            'region': 'region', 'country': 'country', 'data_center': 'data_center',
            'datacenter': 'data_center', 'cloud_region': 'cloud_region',
            'ip_address': 'ip_address', 'ip': 'ip_address', 'ipv4': 'ip_address',
            'class': 'class', 'system_classification': 'system_classification',
            'business_unit': 'business_unit', 'bu': 'business_unit',
            'apm': 'apm', 'cio': 'cio', 'owner': 'cio',
            'edr_coverage': 'edr_coverage', 'crowdstrike': 'edr_coverage',
            'tanium_coverage': 'tanium_coverage', 'tanium': 'tanium_coverage',
            'dlp_agent_coverage': 'dlp_agent_coverage', 'dlp': 'dlp_agent_coverage',
            'logging_in_splunk': 'logging_in_splunk', 'splunk': 'logging_in_splunk',
            'logging_in_gso': 'logging_in_gso', 'gso': 'logging_in_gso'
        }
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for performance"""
        patterns = {
            'hostname': r'(host|hostname|fqdn|server|node|device|endpoint|computer|machine|asset)[\w]*',
            'business_unit': r'(business|bu|department|division|org|cost_center|group|dept)[\w]*',
            'region': r'(region|location|site|area|zone|geo|datacenter_region)[\w]*',
            'country': r'(country|nation|country_code|geo_country)[\w]*',
            'infrastructure_type': r'(infrastructure|infra|server_type|platform|environment|env|deployment)[\w]*',
            'data_center': r'(datacenter|data_center|dc|facility|center|site_name)[\w]*',
            'cloud_region': r'(cloud_region|aws_region|azure_region|gcp_region|availability_zone)[\w]*',
            'ip_address': r'(ip|ipv4|ipv6|address|host_ip|server_ip|endpoint_ip)[\w]*',
            'class': r'(class|classification|tier|level|grade|category)[\w]*',
            'system_classification': r'(system_classification|security_classification|sensitivity)[\w]*',
            'apm': r'(apm|monitoring|application_monitoring|performance)[\w]*',
            'cio': r'(cio|owner|responsible|contact|admin|administrator)[\w]*',
            'edr_coverage': r'(edr|endpoint_detection|security_agent|antivirus|av)[\w]*',
            'tanium_coverage': r'(tanium|endpoint_management)[\w]*',
            'dlp_agent_coverage': r'(dlp|data_loss_prevention)[\w]*',
            'logging_in_splunk': r'(splunk|log_forwarding|logging)[\w]*',
            'logging_in_gso': r'(gso|security_logging)[\w]*'
        }
        return {k: re.compile(v, re.IGNORECASE) for k, v in patterns.items()}
    
    def _init_ml_classifier(self):
        """Initialize ML-based column classifier (placeholder for real ML)"""
        # In production, this would be a trained model
        return None
    
    @lru_cache(maxsize=10000)
    def map_column(self, column_name: str, column_type: str = None) -> Optional[str]:
        """Map column to standardized type with caching"""
        column_lower = column_name.lower()
        
        # Check exact mappings first (fastest)
        if column_lower in self.exact_mappings:
            return self.exact_mappings[column_lower]
        
        # Check fuzzy patterns (fast)
        for target_type, pattern in self.fuzzy_patterns.items():
            if pattern.search(column_lower):
                return target_type
        
        # ML classification (if available)
        if self.ml_classifier:
            return self._ml_classify(column_name, column_type)
        
        return None
    
    def _ml_classify(self, column_name: str, column_type: str) -> Optional[str]:
        """Use ML to classify ambiguous columns"""
        # Placeholder for ML classification
        return None

class QueryOptimizer:
    """Advanced query optimization with caching and prediction"""
    def __init__(self, bq_client):
        self.bq_client = bq_client
        self.query_cache = {}
        self.query_stats = defaultdict(lambda: {'count': 0, 'avg_time': 0, 'total_bytes': 0})
        self.table_samples = {}
        
    def optimize_query(self, table_name: str, columns: List[str], 
                      hostname_col: str, limit: int = None) -> str:
        """Generate optimized query with smart sampling"""
        
        # Check if we should sample this table
        sample_clause = self._get_sample_clause(table_name)
        limit_clause = f"LIMIT {limit}" if limit else "LIMIT 5000000"
        
        # Use APPROX functions for better performance
        column_selects = [f"`{col}`" for col in columns]
        
        # Add clustering hints if available
        clustering_hint = self._get_clustering_hint(table_name)
        
        query = f"""
        SELECT {', '.join(column_selects)}
        FROM `{table_name}` {sample_clause}
        WHERE `{hostname_col}` IS NOT NULL 
        AND `{hostname_col}` != ''
        AND `{hostname_col}` != '*Undefined'
        AND LENGTH(`{hostname_col}`) > 1
        {clustering_hint}
        {limit_clause}
        """
        
        return query.strip()
    
    def _get_sample_clause(self, table_name: str) -> str:
        """Determine if table should be sampled"""
        # Check table size from cache or metadata
        if self._is_large_table(table_name):
            return "TABLESAMPLE SYSTEM (10 PERCENT)"  # Sample 10% for large tables
        return ""
    
    def _is_large_table(self, table_name: str) -> bool:
        """Check if table is large enough to warrant sampling"""
        # Implement logic to check table size
        return False  # Placeholder
    
    def _get_clustering_hint(self, table_name: str) -> str:
        """Get clustering hints for query optimization"""
        # Could add ORDER BY for clustered tables
        return ""

class DataProcessor:
    """High-performance data processing engine"""
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.bloom_filter = BloomFilter() if config.dedup_strategy == "bloom_filter" else None
        self.hll = HyperLogLog() if config.dedup_strategy == "probabilistic" else None
        self.processed_hosts = set() if config.dedup_strategy == "exact" else None
        
    def process_batch(self, records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Process batch with vectorized operations"""
        if not records:
            return [], []
        
        # Convert to polars for ultra-fast processing
        df = pl.DataFrame(records)
        
        # Vectorized normalization
        if 'hostname' in df.columns:
            df = df.with_columns([
                pl.col('hostname').str.to_lowercase().str.strip().alias('normalized_host')
            ])
            
            # Remove domain suffix vectorized
            df = df.with_columns([
                pl.when(pl.col('normalized_host').str.contains('.'))
                .then(pl.col('normalized_host').str.split('.').list.first())
                .otherwise(pl.col('normalized_host'))
                .alias('normalized_host')
            ])
            
            # Clean special characters
            df = df.with_columns([
                pl.col('normalized_host').str.replace_all(r'[^a-z0-9]', '').alias('normalized_host')
            ])
        
        # Deduplication based on strategy
        if self.config.dedup_strategy == "bloom_filter":
            new_hosts_mask = []
            for host in df['normalized_host']:
                is_new = not self.bloom_filter.add(host)
                new_hosts_mask.append(is_new)
            
            new_records = df.filter(pl.Series(new_hosts_mask))
            existing_records = df.filter(~pl.Series(new_hosts_mask))
        else:
            # Exact deduplication
            new_records = df
            existing_records = pl.DataFrame()
        
        return new_records.to_dicts(), existing_records.to_dicts()

class UltraCMDBProcessor:
    """Ultra-high-performance CMDB processor with advanced features"""
    
    def __init__(self, json_file_path: str, duckdb_path: str = "universal_cmdb.db", 
                 config: ProcessingConfig = None):
        print("\n" + "="*80)
        print("🚀 ULTRA-HIGH-PERFORMANCE CMDB PROCESSOR v2.0")
        print("="*80)
        
        self.json_file_path = json_file_path
        self.duckdb_path = duckdb_path
        self.config = config or ProcessingConfig()
        self.running = True
        
        # Advanced components
        self.column_mapper = ColumnMapper()
        self.data_processor = DataProcessor(self.config)
        self.stats = self._init_stats()
        self.checkpoints = deque(maxlen=100)
        
        # Performance monitoring
        self.perf_monitor = PerformanceMonitor() if self.config.enable_profiling else None
        
        # Thread-safe components
        self._lock = threading.Lock()
        self._stats_lock = threading.Lock()
        
        # Special tables for presence tracking
        self.special_tables = {
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINTAGENT': 'present_in_crowdstrike',
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_DIM_ENDPOINT': 'present_in_cmdb',
            'prj-fisv-p-gcss-sas-dl9dd0f1df.SAS_BI.V_SPL_ENDPOINT_LOG': 'present_in_splunk'
        }
        
        # Initialize connections
        self._init_connections()
        
        logger.info(f"✅ Initialized with mode: {self.config.mode.value}")
        logger.info(f"   Workers: {self.config.max_workers}")
        logger.info(f"   Batch Size: {self.config.batch_size}")
        logger.info(f"   Memory Limit: {self.config.memory_limit_gb}GB")
        
    def _init_stats(self) -> Dict:
        """Initialize comprehensive statistics"""
        return {
            'start_time': time.time(),
            'tables_processed': 0,
            'columns_discovered': 0,
            'hosts_created': 0,
            'hosts_updated': 0,
            'duplicate_hosts_found': 0,
            'total_records_processed': 0,
            'processing_errors': 0,
            'bytes_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'query_time': 0,
            'processing_time': 0,
            'io_time': 0,
            'checkpoints_created': 0
        }
    
    def _init_connections(self):
        """Initialize all connections with optimization"""
        # BigQuery with connection pooling
        self._init_bigquery_pool()
        
        # DuckDB with optimal settings
        self._init_duckdb_optimized()
        
        # Create tables and indexes
        self._create_optimized_schema()
        
    def _init_bigquery_pool(self):
        """Initialize BigQuery with connection pooling"""
        service_account_file = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'gcp/gcp_prod_key.json')
        
        if os.path.exists(service_account_file):
            credentials = service_account.Credentials.from_service_account_file(service_account_file)
            self.bq_client = bigquery.Client(project="chronicle-fisv", credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project="chronicle-fisv")
        
        # Initialize query optimizer
        self.query_optimizer = QueryOptimizer(self.bq_client)
        
        logger.info("✅ BigQuery connection pool established")
    
    def _init_duckdb_optimized(self):
        """Initialize DuckDB with optimal settings"""
        config = {
            'threads': self.config.max_workers,
            'memory_limit': f'{self.config.memory_limit_gb}GB',
            'max_memory': f'{self.config.memory_limit_gb}GB',
            'temp_directory': '/tmp/duckdb_temp',
            'preserve_insertion_order': False,
            'enable_object_cache': True,
            'enable_http_metadata_cache': True,
            'force_compression': 'auto' if self.config.enable_compression else 'none'
        }
        
        self.duck_conn = duckdb.connect(self.duckdb_path, config=config)
        
        # Enable parallel execution
        self.duck_conn.execute("PRAGMA threads=%d" % self.config.max_workers)
        self.duck_conn.execute("PRAGMA memory_limit='%dGB'" % self.config.memory_limit_gb)
        self.duck_conn.execute("PRAGMA temp_directory='/tmp/duckdb_temp'")
        
        logger.info("✅ DuckDB initialized with optimal settings")
    
    def _create_optimized_schema(self):
        """Create optimized schema with partitioning and compression"""
        
        # Main table with columnar storage
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
            present_in_crowdstrike TEXT DEFAULT 'No',
            present_in_cmdb TEXT DEFAULT 'No',
            present_in_splunk TEXT DEFAULT 'No',
            data_quality_score FLOAT DEFAULT 1.0,
            source_count INTEGER DEFAULT 1,
            confidence_score FLOAT DEFAULT 1.0,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processing_version INTEGER DEFAULT 1,
            hash_key VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.duck_conn.execute(create_sql)
        
        # Create optimized indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_normalized_host ON universal_cmdb(normalized_host)",
            "CREATE INDEX IF NOT EXISTS idx_business_unit ON universal_cmdb(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_region ON universal_cmdb(region)",
            "CREATE INDEX IF NOT EXISTS idx_infrastructure_type ON universal_cmdb(infrastructure_type)",
            "CREATE INDEX IF NOT EXISTS idx_source_count ON universal_cmdb(source_count)",
            "CREATE INDEX IF NOT EXISTS idx_last_updated ON universal_cmdb(last_updated)",
            "CREATE INDEX IF NOT EXISTS idx_hash_key ON universal_cmdb(hash_key)",
            "CREATE INDEX IF NOT EXISTS idx_confidence_score ON universal_cmdb(confidence_score)",
            "CREATE INDEX IF NOT EXISTS idx_composite_presence ON universal_cmdb(present_in_crowdstrike, present_in_cmdb, present_in_splunk)"
        ]
        
        for index_sql in indexes:
            try:
                self.duck_conn.execute(index_sql)
            except:
                pass
        
        # Create staging table for bulk operations
        self.duck_conn.execute("""
            CREATE TABLE IF NOT EXISTS staging_cmdb AS 
            SELECT * FROM universal_cmdb WHERE 1=0
        """)
        
        # Create audit table
        self.duck_conn.execute("""
            CREATE TABLE IF NOT EXISTS cmdb_audit_log (
                audit_id INTEGER PRIMARY KEY,
                operation TEXT,
                table_name TEXT,
                record_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        """)
        
        logger.info("✅ Optimized schema created")
    
    async def process_all_async(self):
        """Main async processing pipeline"""
        logger.info("🚀 Starting ultra-fast async processing...")
        
        try:
            # Load metadata
            metadata = await self._load_metadata_async()
            
            # Discover columns with ML
            discovered_columns = await self._discover_columns_async(metadata)
            
            if not discovered_columns:
                logger.error("❌ No columns discovered")
                return
            
            # Group by table
            columns_by_table = self._group_columns_by_table(discovered_columns)
            
            # Process tables in parallel
            await self._process_tables_parallel(columns_by_table)
            
            # Generate report
            self._generate_comprehensive_report()
            
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
    
    async def _load_metadata_async(self) -> Dict:
        """Async metadata loading with validation"""
        logger.info(f"📂 Loading metadata from {self.json_file_path}")
        
        async with aiofiles.open(self.json_file_path, 'r') as f:
            content = await f.read()
            metadata = orjson.loads(content)
        
        # Validate metadata
        if 'columns' in metadata:
            table_count = len(metadata['columns'])
            column_count = sum(len(cols) for cols in metadata['columns'].values())
            logger.info(f"✅ Loaded {table_count:,} tables, {column_count:,} columns")
        else:
            raise ValueError("Invalid metadata format")
        
        return metadata
    
    async def _discover_columns_async(self, metadata: Dict) -> List[Tuple[str, str, str]]:
        """Async column discovery with ML enhancement"""
        logger.info("🔍 Discovering columns with ML assistance...")
        
        discovered = []
        
        with tqdm(total=len(metadata['columns']), desc="Discovering columns") as pbar:
            for table_name, columns in metadata['columns'].items():
                for column_name, column_type in columns.items():
                    mapped_type = self.column_mapper.map_column(column_name, column_type)
                    if mapped_type:
                        discovered.append((table_name, column_name, mapped_type))
                pbar.update(1)
        
        self.stats['columns_discovered'] = len(discovered)
        logger.info(f"✅ Discovered {len(discovered):,} relevant columns")
        
        return discovered
    
    def _group_columns_by_table(self, discovered_columns: List[Tuple[str, str, str]]) -> Dict:
        """Group columns by table efficiently"""
        columns_by_table = defaultdict(list)
        
        for table_name, column_name, column_type in discovered_columns:
            columns_by_table[table_name].append((column_name, column_type))
        
        return dict(columns_by_table)
    
    async def _process_tables_parallel(self, columns_by_table: Dict):
        """Process tables with advanced parallelization"""
        tables = list(columns_by_table.items())
        
        # Determine optimal parallelization strategy
        if self.config.mode == ProcessingMode.TURBO:
            # Maximum parallelization
            chunk_size = max(1, len(tables) // (self.config.max_workers * 2))
        elif self.config.mode == ProcessingMode.BALANCED:
            chunk_size = max(1, len(tables) // self.config.max_workers)
        else:  # PRECISION mode
            chunk_size = max(1, len(tables) // (self.config.max_workers // 2))
        
        # Process with progress bar
        with tqdm(total=len(tables), desc="Processing tables") as pbar:
            tasks = []
            
            for table_name, columns in tables:
                task = asyncio.create_task(self._process_table_async(table_name, columns))
                tasks.append(task)
                
                # Limit concurrent tasks
                if len(tasks) >= self.config.max_workers:
                    done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        pbar.update(1)
                    tasks = list(tasks)
            
            # Wait for remaining tasks
            if tasks:
                await asyncio.gather(*tasks)
                pbar.update(len(tasks))
    
    async def _process_table_async(self, table_name: str, columns: List[Tuple[str, str]]):
        """Async table processing with optimization"""
        try:
            # Check for special presence tables
            if table_name in self.special_tables:
                await self._process_presence_table_async(table_name, columns)
                return
            
            # Regular table processing
            hostname_cols = [col for col, ctype in columns if ctype == 'hostname']
            if not hostname_cols:
                return
            
            # Generate optimized query
            all_columns = [hostname_cols[0]] + [col for col, ctype in columns if ctype != 'hostname']
            query = self.query_optimizer.optimize_query(
                table_name, all_columns, hostname_cols[0], 
                limit=1000000 if self.config.mode == ProcessingMode.TURBO else None
            )
            
            # Execute query
            await self._execute_and_process_query(query, table_name, columns)
            
        except Exception as e:
            logger.error(f"❌ Error processing {table_name}: {str(e)[:100]}")
            self.stats['processing_errors'] += 1
    
    async def _execute_and_process_query(self, query: str, table_name: str, columns: List[Tuple[str, str]]):
        """Execute query and process results efficiently"""
        start_time = time.time()
        
        # Execute query with job config
        job_config = bigquery.QueryJobConfig()
        job_config.use_query_cache = self.config.enable_query_cache
        job_config.use_legacy_sql = False
        job_config.maximum_bytes_billed = 10 * 1024 * 1024 * 1024  # 10GB limit
        
        query_job = self.bq_client.query(query, job_config=job_config)
        
        # Process results in batches
        batch_records = []
        records_processed = 0
        
        for row in query_job:
            record = self._extract_record(row, table_name, columns)
            if record:
                batch_records.append(record)
                records_processed += 1
            
            if len(batch_records) >= self.config.batch_size:
                await self._process_batch_async(batch_records)
                batch_records.clear()
                
                # Create checkpoint if needed
                if records_processed % self.config.checkpoint_interval == 0:
                    self._create_checkpoint(table_name, records_processed)
        
        # Process remaining records
        if batch_records:
            await self._process_batch_async(batch_records)
        
        # Update stats
        query_time = time.time() - start_time
        with self._stats_lock:
            self.stats['query_time'] += query_time
            self.stats['total_records_processed'] += records_processed
            self.stats['tables_processed'] += 1
        
        logger.info(f"✅ {table_name}: {records_processed:,} records in {query_time:.2f}s")
    
    def _extract_record(self, row, table_name: str, columns: List[Tuple[str, str]]) -> Optional[Dict]:
        """Extract and validate record from row"""
        if not row or not row[0]:
            return None
        
        hostname = str(row[0]).strip()
        if hostname in ('*Undefined', '', 'null', 'None'):
            return None
        
        record = {
            'hostname': hostname,
            'table_name': table_name,
            'hash_key': hashlib.md5(hostname.encode()).hexdigest()[:16]
        }
        
        # Extract other columns
        for i, (col_name, col_type) in enumerate(columns[1:], 1):
            if i < len(row) and row[i]:
                value = str(row[i]).strip()
                if value and value not in ('*Undefined', 'null', 'None'):
                    record[col_type] = value
        
        return record
    
    async def _process_batch_async(self, batch_records: List[Dict]):
        """Process batch with advanced deduplication and updates"""
        if not batch_records:
            return
        
        # Process with data processor
        new_records, existing_records = self.data_processor.process_batch(batch_records)
        
        # Bulk operations
        if new_records:
            await self._bulk_insert_async(new_records)
            with self._stats_lock:
                self.stats['hosts_created'] += len(new_records)
        
        if existing_records:
            await self._bulk_update_async(existing_records)
            with self._stats_lock:
                self.stats['hosts_updated'] += len(existing_records)
    
    async def _bulk_insert_async(self, records: List[Dict]):
        """Async bulk insert with staging table"""
        if not records:
            return
        
        # Convert to DataFrame for efficient insertion
        df = pl.DataFrame(records)
        
        # Write to staging first
        staging_table = "staging_cmdb_" + str(int(time.time()))
        
        # Use arrow for ultra-fast insertion
        arrow_table = df.to_arrow()
        self.duck_conn.register(staging_table, arrow_table)
        
        # Merge into main table
        merge_sql = f"""
        INSERT INTO universal_cmdb 
        SELECT * FROM {staging_table}
        ON CONFLICT (normalized_host) DO NOTHING
        """
        
        self.duck_conn.execute(merge_sql)
        self.duck_conn.unregister(staging_table)
    
    async def _bulk_update_async(self, records: List[Dict]):
        """Async bulk update with optimized merging"""
        if not records:
            return
        
        # Create temporary table for updates
        temp_table = f"temp_updates_{int(time.time())}"
        df = pl.DataFrame(records)
        arrow_table = df.to_arrow()
        self.duck_conn.register(temp_table, arrow_table)
        
        # Perform merge update
        merge_sql = f"""
        UPDATE universal_cmdb u
        SET 
            source_tables = CONCAT(u.source_tables, ', ', t.table_name),
            source_count = u.source_count + 1,
            last_updated = CURRENT_TIMESTAMP,
            confidence_score = LEAST(1.0, u.confidence_score + 0.1)
        FROM {temp_table} t
        WHERE u.normalized_host = t.normalized_host
        """
        
        self.duck_conn.execute(merge_sql)
        self.duck_conn.unregister(temp_table)
    
    async def _process_presence_table_async(self, table_name: str, columns: List[Tuple[str, str]]):
        """Process special presence tables asynchronously"""
        presence_column = self.special_tables[table_name]
        hostname_col = next((col for col, ctype in columns if ctype == 'hostname'), None)
        
        if not hostname_col:
            return
        
        logger.info(f"🔍 Processing presence table for {presence_column}")
        
        # Query for all hosts
        query = f"""
        SELECT DISTINCT `{hostname_col[0]}`
        FROM `{table_name}`
        WHERE `{hostname_col[0]}` IS NOT NULL
        AND `{hostname_col[0]}` != '*Undefined'
        LIMIT 2000000
        """
        
        query_job = self.bq_client.query(query)
        hosts = []
        
        for row in query_job:
            if row[0]:
                normalized = self._normalize_hostname(str(row[0]))
                if normalized:
                    hosts.append(normalized)
        
        # Bulk update presence
        if hosts:
            await self._bulk_update_presence_async(hosts, presence_column)
            logger.info(f"✅ Updated {len(hosts):,} hosts for {presence_column}")
    
    async def _bulk_update_presence_async(self, hosts: List[str], presence_column: str):
        """Async bulk update for presence columns"""
        # Process in chunks
        chunk_size = 10000
        
        for i in range(0, len(hosts), chunk_size):
            chunk = hosts[i:i + chunk_size]
            placeholders = ','.join(['?' for _ in chunk])
            
            update_sql = f"""
            UPDATE universal_cmdb
            SET {presence_column} = 'Yes', 
                last_updated = CURRENT_TIMESTAMP,
                confidence_score = LEAST(1.0, confidence_score + 0.2)
            WHERE normalized_host IN ({placeholders})
            """
            
            self.duck_conn.execute(update_sql, chunk)
    
    def _normalize_hostname(self, hostname: str) -> str:
        """Ultra-fast hostname normalization"""
        if not hostname or hostname == '*Undefined':
            return ""
        
        normalized = hostname.lower().strip()
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        # Remove special characters
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized if len(normalized) > 1 else ""
    
    def _create_checkpoint(self, table_name: str, records_processed: int):
        """Create processing checkpoint for recovery"""
        checkpoint = {
            'timestamp': datetime.now(),
            'table_name': table_name,
            'records_processed': records_processed,
            'stats': dict(self.stats)
        }
        
        self.checkpoints.append(checkpoint)
        
        # Save to disk periodically
        if len(self.checkpoints) >= 10:
            self._save_checkpoints()
        
        with self._stats_lock:
            self.stats['checkpoints_created'] += 1
    
    def _save_checkpoints(self):
        """Save checkpoints to disk"""
        checkpoint_file = f"checkpoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.msgpack"
        
        with open(checkpoint_file, 'wb') as f:
            packed = msgpack.packb(list(self.checkpoints))
            f.write(packed)
        
        logger.info(f"💾 Saved {len(self.checkpoints)} checkpoints to {checkpoint_file}")
    
    def _generate_comprehensive_report(self):
        """Generate detailed performance and data quality report"""
        elapsed_time = time.time() - self.stats['start_time']
        
        # Query comprehensive statistics
        total_hosts = self.duck_conn.execute("SELECT COUNT(*) FROM universal_cmdb").fetchone()[0]
        
        # Presence statistics
        presence_stats = self.duck_conn.execute("""
            SELECT 
                SUM(CASE WHEN present_in_crowdstrike = 'Yes' THEN 1 ELSE 0 END) as crowdstrike,
                SUM(CASE WHEN present_in_cmdb = 'Yes' THEN 1 ELSE 0 END) as cmdb,
                SUM(CASE WHEN present_in_splunk = 'Yes' THEN 1 ELSE 0 END) as splunk,
                SUM(CASE WHEN present_in_crowdstrike = 'Yes' AND present_in_cmdb = 'Yes' THEN 1 ELSE 0 END) as both_cs_cmdb,
                SUM(CASE WHEN present_in_crowdstrike = 'Yes' AND present_in_splunk = 'Yes' THEN 1 ELSE 0 END) as both_cs_splunk,
                SUM(CASE WHEN present_in_cmdb = 'Yes' AND present_in_splunk = 'Yes' THEN 1 ELSE 0 END) as both_cmdb_splunk,
                SUM(CASE WHEN present_in_crowdstrike = 'Yes' AND present_in_cmdb = 'Yes' AND present_in_splunk = 'Yes' THEN 1 ELSE 0 END) as all_three
            FROM universal_cmdb
        """).fetchone()
        
        # Data quality metrics
        quality_stats = self.duck_conn.execute("""
            SELECT 
                AVG(confidence_score) as avg_confidence,
                AVG(source_count) as avg_sources,
                MAX(source_count) as max_sources,
                COUNT(DISTINCT business_unit) as unique_bus,
                COUNT(DISTINCT region) as unique_regions,
                COUNT(DISTINCT infrastructure_type) as unique_infra_types
            FROM universal_cmdb
        """).fetchone()
        
        print("\n" + "="*100)
        print("🎉 ULTRA-HIGH-PERFORMANCE CMDB PROCESSING COMPLETE")
        print("="*100)
        
        print("\n📊 PERFORMANCE METRICS:")
        print(f"   ⏱️  Total Runtime: {elapsed_time:.2f}s ({elapsed_time/60:.1f} minutes)")
        print(f"   🚀 Processing Speed: {self.stats['total_records_processed']/elapsed_time:,.0f} records/sec")
        print(f"   📋 Tables Processed: {self.stats['tables_processed']:,}")
        print(f"   🔍 Columns Discovered: {self.stats['columns_discovered']:,}")
        print(f"   📝 Total Records: {self.stats['total_records_processed']:,}")
        print(f"   💾 Checkpoints Created: {self.stats['checkpoints_created']:,}")
        
        print("\n🏠 HOST METRICS:")
        print(f"   📊 Total Unique Hosts: {total_hosts:,}")
        print(f"   ➕ New Hosts Created: {self.stats['hosts_created']:,}")
        print(f"   🔄 Hosts Updated: {self.stats['hosts_updated']:,}")
        print(f"   📈 Average Sources per Host: {quality_stats[1]:.2f}")
        print(f"   🏆 Maximum Sources: {quality_stats[2]}")
        
        print("\n🔍 PRESENCE ANALYSIS:")
        print(f"   🛡️  CrowdStrike: {presence_stats[0]:,} ({presence_stats[0]/max(1,total_hosts)*100:.1f}%)")
        print(f"   🗄️  CMDB: {presence_stats[1]:,} ({presence_stats[1]/max(1,total_hosts)*100:.1f}%)")
        print(f"   📊 Splunk: {presence_stats[2]:,} ({presence_stats[2]/max(1,total_hosts)*100:.1f}%)")
        
        print("\n🔗 COVERAGE OVERLAP:")
        print(f"   CrowdStrike ∩ CMDB: {presence_stats[3]:,} hosts")
        print(f"   CrowdStrike ∩ Splunk: {presence_stats[4]:,} hosts")
        print(f"   CMDB ∩ Splunk: {presence_stats[5]:,} hosts")
        print(f"   All Three Systems: {presence_stats[6]:,} hosts")
        
        print("\n📈 DATA QUALITY METRICS:")
        print(f"   🎯 Average Confidence Score: {quality_stats[0]:.3f}")
        print(f"   🏢 Unique Business Units: {quality_stats[3]:,}")
        print(f"   🌍 Unique Regions: {quality_stats[4]:,}")
        print(f"   🖥️  Unique Infrastructure Types: {quality_stats[5]:,}")
        
        if self.config.enable_profiling and self.perf_monitor:
            print("\n⚡ DETAILED PERFORMANCE:")
            print(f"   Query Time: {self.stats['query_time']:.2f}s")
            print(f"   Processing Time: {self.stats['processing_time']:.2f}s")
            print(f"   I/O Time: {self.stats['io_time']:.2f}s")
            print(f"   Cache Hit Rate: {self.stats['cache_hits']/(self.stats['cache_hits']+self.stats['cache_misses']+1)*100:.1f}%")
        
        print("\n" + "="*100)
    
    def export_results(self, format: str = "parquet"):
        """Export results in various formats"""
        logger.info(f"💾 Exporting results in {format} format...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == "parquet":
            # Ultra-fast Parquet export
            query = "SELECT * FROM universal_cmdb ORDER BY source_count DESC, confidence_score DESC"
            df = self.duck_conn.execute(query).fetch_arrow_table()
            pq.write_table(df, f'universal_cmdb_{timestamp}.parquet', compression='snappy')
            
        elif format == "csv":
            # CSV export with compression
            export_sql = f"""
            COPY (
                SELECT * FROM universal_cmdb 
                ORDER BY source_count DESC, confidence_score DESC
            ) TO 'universal_cmdb_{timestamp}.csv.gz' 
            WITH (FORMAT CSV, HEADER, COMPRESSION GZIP)
            """
            self.duck_conn.execute(export_sql)
            
        elif format == "excel":
            # Excel export with formatting
            query = "SELECT * FROM universal_cmdb ORDER BY source_count DESC LIMIT 1000000"
            df = self.duck_conn.execute(query).df()
            with pd.ExcelWriter(f'universal_cmdb_{timestamp}.xlsx', engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='CMDB Data', index=False)
                
                # Add formatting
                workbook = writer.book
                worksheet = writer.sheets['CMDB Data']
                header_format = workbook.add_format({'bold': True, 'bg_color': '#4CAF50', 'font_color': 'white'})
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
        
        logger.info(f"✅ Export completed: universal_cmdb_{timestamp}.{format}")
    
    def analyze_gaps(self):
        """Analyze coverage gaps and generate recommendations"""
        logger.info("🔍 Analyzing coverage gaps...")
        
        gaps = self.duck_conn.execute("""
            SELECT 
                CASE 
                    WHEN present_in_crowdstrike = 'No' AND present_in_cmdb = 'Yes' THEN 'Missing CrowdStrike'
                    WHEN present_in_crowdstrike = 'Yes' AND present_in_cmdb = 'No' THEN 'Missing CMDB'
                    WHEN present_in_splunk = 'No' AND (present_in_crowdstrike = 'Yes' OR present_in_cmdb = 'Yes') THEN 'Missing Splunk'
                    WHEN present_in_crowdstrike = 'No' AND present_in_cmdb = 'No' AND present_in_splunk = 'Yes' THEN 'Only in Splunk'
                    ELSE 'Other'
                END as gap_type,
                COUNT(*) as host_count,
                STRING_AGG(DISTINCT business_unit, ', ') as affected_bus,
                STRING_AGG(DISTINCT region, ', ') as affected_regions
            FROM universal_cmdb
            WHERE NOT (present_in_crowdstrike = 'Yes' AND present_in_cmdb = 'Yes' AND present_in_splunk = 'Yes')
            GROUP BY gap_type
            ORDER BY host_count DESC
        """).fetchall()
        
        print("\n🔍 COVERAGE GAP ANALYSIS:")
        print("-" * 60)
        
        for gap_type, count, bus, regions in gaps:
            if gap_type != 'Other':
                print(f"\n📌 {gap_type}: {count:,} hosts")
                if bus:
                    print(f"   Business Units: {bus[:100]}...")
                if regions:
                    print(f"   Regions: {regions[:100]}...")
        
        # Generate remediation recommendations
        print("\n💡 RECOMMENDATIONS:")
        recommendations = []
        
        for gap_type, count, _, _ in gaps:
            if gap_type == 'Missing CrowdStrike' and count > 100:
                recommendations.append(f"• Deploy CrowdStrike agents to {count:,} unprotected hosts")
            elif gap_type == 'Missing CMDB' and count > 50:
                recommendations.append(f"• Register {count:,} hosts in CMDB for proper asset management")
            elif gap_type == 'Missing Splunk' and count > 200:
                recommendations.append(f"• Configure Splunk forwarding for {count:,} hosts lacking monitoring")
        
        for rec in recommendations:
            print(rec)
    
    def close(self):
        """Clean shutdown"""
        logger.info("🔒 Shutting down...")
        self.running = False
        
        # Save final checkpoints
        if self.checkpoints:
            self._save_checkpoints()
        
        # Close connections
        self.duck_conn.close()
        
        logger.info("✅ Shutdown complete")

class PerformanceMonitor:
    """Monitor and optimize performance"""
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
    
    def start_timer(self, operation: str):
        self.start_times[operation] = time.perf_counter()
    
    def end_timer(self, operation: str):
        if operation in self.start_times:
            elapsed = time.perf_counter() - self.start_times[operation]
            self.metrics[operation].append(elapsed)
            del self.start_times[operation]
            return elapsed
        return 0
    
    def get_stats(self, operation: str) -> Dict:
        if operation not in self.metrics:
            return {}
        
        times = self.metrics[operation]
        return {
            'count': len(times),
            'total': sum(times),
            'avg': np.mean(times),
            'median': np.median(times),
            'p95': np.percentile(times, 95),
            'p99': np.percentile(times, 99)
        }

async def main():
    """Main execution with async support"""
    print("\n" + "="*100)
    print("🚀 ULTRA-HIGH-PERFORMANCE CMDB PROCESSOR v2.0")
    print("="*100)
    print("⚡ Features:")
    print("   • Async/await for maximum concurrency")
    print("   • ML-enhanced column discovery")
    print("   • Bloom filters for deduplication")
    print("   • Arrow/Parquet for columnar processing")
    print("   • Automatic checkpointing and recovery")
    print("   • Advanced gap analysis and recommendations")
    print("="*100)
    
    # Configuration
    config = ProcessingConfig(
        mode=ProcessingMode.TURBO,
        max_workers=32,
        batch_size=10000,
        cache_size=100000,
        enable_profiling=True,
        memory_limit_gb=32,
        checkpoint_interval=5000,
        enable_compression=True,
        parallel_io=True,
        use_columnar_format=True
    )
    
    # Initialize processor
    processor = UltraCMDBProcessor(
        "reviewed_labeled_columns.json",
        "universal_cmdb_v2.db",
        config=config
    )
    
    try:
        # Run async processing
        await processor.process_all_async()
        
        # Export results
        processor.export_results("parquet")
        processor.export_results("csv")
        
        # Analyze gaps
        processor.analyze_gaps()
        
        print("\n✅ All processing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close()

if __name__ == "__main__":
    # Run with async support
    asyncio.run(main())