# discovery/ao1.py - MAXIMUM INTENSITY FIXED VERSION

import asyncio
import logging
import re
import gc
import psutil
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class MaximumIntensityRealtimeCMDBBuilder:
    def __init__(self):
        self.cmdb = {}
        self.processing_stats = {
            'hosts_discovered': 0,
            'attributes_added': 0,
            'tables_processed': 0,
            'total_rows_processed': 0,
            'total_cells_analyzed': 0,
            'memory_usage_mb': 0,
            'rows_per_second': 0.0,
            'start_time': None
        }
    
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname:
            return ""
        
        hostname = str(hostname).strip().upper()
        
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Z0-9\-]', '', hostname)
        
        return hostname
    
    def add_host_to_cmdb_maximum_intensity(self, hostname: str, all_row_data: Dict[str, Any], source_table: str, db_manager=None):
        """🔥 MAXIMUM INTENSITY: Process complete row data and IMMEDIATELY log + store to DB"""
        normalized_hostname = self.normalize_hostname(hostname)
        
        if not normalized_hostname or len(normalized_hostname) < 2:
            return
        
        is_new_host = normalized_hostname not in self.cmdb
        
        if is_new_host:
            self.cmdb[normalized_hostname] = {
                'hostname': normalized_hostname,
                'source_tables': set(),
                'all_attributes': {},
                'coverage_flags': {
                    'in_chronicle': False,
                    'in_crowdstrike': False,
                    'in_original_cmdb': False,
                    'in_splunk': False,
                    'in_tanium': False,
                    'in_dlp': False
                },
                'first_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'source_count': 0,
                'total_rows': 0
            }
            self.processing_stats['hosts_discovered'] += 1
            
            # 🔥 IMMEDIATE CONSOLE LOGGING FOR NEW HOST DISCOVERY
            logger.info(f"🎉 NEW HOST DISCOVERED: {normalized_hostname}")
            logger.info(f"   📊 Total Unique Hosts: {self.processing_stats['hosts_discovered']:,}")
            logger.info(f"   📋 Source Table: {source_table}")
        
        host = self.cmdb[normalized_hostname]
        
        # 🔥 MAXIMUM INTENSITY: Process ALL columns from the row
        new_attributes = 0
        for column_name, value in all_row_data.items():
            if value is not None and str(value).strip():
                clean_value = str(value).strip()
                
                # Smart attribute mapping with deduplication
                attribute_key = self._map_column_to_attribute(column_name)
                
                if attribute_key not in host['all_attributes']:
                    host['all_attributes'][attribute_key] = set()
                
                old_size = len(host['all_attributes'][attribute_key])
                host['all_attributes'][attribute_key].add(clean_value)
                new_size = len(host['all_attributes'][attribute_key])
                
                if new_size > old_size:
                    self.processing_stats['attributes_added'] += 1
                    new_attributes += 1
                    # 🔥 LOG NEW ATTRIBUTE DISCOVERIES
                    logger.info(f"   ➕ NEW {attribute_key.upper()}: {clean_value}")
        
        # Track source information
        host['source_tables'].add(source_table)
        host['source_count'] = len(host['source_tables'])
        host['total_rows'] += 1
        
        # Set coverage flags based on source table
        coverage_before = dict(host['coverage_flags'])
        self._set_coverage_flags(host, source_table)
        
        # 🔥 LOG COVERAGE CHANGES
        for flag, current_value in host['coverage_flags'].items():
            if current_value and not coverage_before[flag]:
                logger.info(f"   🛡️  NEW COVERAGE: {flag.upper()} = TRUE")
        
        host['last_updated'] = datetime.now().isoformat()
        self.processing_stats['total_cells_analyzed'] += len(all_row_data)
        
        # 🔥 IMMEDIATE DATABASE STORAGE if db_manager provided
        if db_manager and is_new_host:
            try:
                db_manager.store_single_host_immediately(normalized_hostname, host)
                logger.info(f"   💾 STORED TO DATABASE: {normalized_hostname}")
            except Exception as e:
                logger.error(f"   💥 DB STORAGE FAILED: {e}")
        
        # 🔥 SUMMARY LOG FOR EACH HOST UPDATE
        logger.info(f"   📈 Host Summary: {new_attributes} new attrs, {host['source_count']} sources, {host['total_rows']} rows")
    
    def _map_column_to_attribute(self, column_name: str) -> str:
        """🔥 INTELLIGENT COLUMN MAPPING FOR MAXIMUM DATA EXTRACTION"""
        column_lower = column_name.lower()
        
        # Primary identity mapping
        if any(word in column_lower for word in ['hostname', 'host_name', 'computername', 'computer_name']):
            return 'hostname'
        elif any(word in column_lower for word in ['ip', 'ipaddress', 'ip_address']):
            return 'ip_address'
        elif any(word in column_lower for word in ['fqdn', 'fully_qualified']):
            return 'fqdn'
        elif any(word in column_lower for word in ['mac', 'mac_address', 'ethernet']):
            return 'mac_address'
        
        # Infrastructure mapping
        elif any(word in column_lower for word in ['infrastructure', 'hosting', 'deployment']):
            return 'infrastructure_type'
        elif any(word in column_lower for word in ['os', 'operating', 'system']):
            return 'operating_system'
        elif any(word in column_lower for word in ['region', 'location', 'geo']):
            return 'region'
        elif any(word in column_lower for word in ['datacenter', 'dc', 'facility']):
            return 'datacenter'
        elif any(word in column_lower for word in ['business', 'bu', 'department']):
            return 'business_unit'
        elif any(word in column_lower for word in ['environment', 'env']):
            return 'environment'
        elif any(word in column_lower for word in ['application', 'app']):
            return 'application'
        elif any(word in column_lower for word in ['owner', 'responsible']):
            return 'owner'
        elif any(word in column_lower for word in ['criticality', 'critical', 'priority']):
            return 'criticality'
        
        # Default to original column name for unmapped columns
        return column_name
    
    def _set_coverage_flags(self, host: Dict, source_table: str):
        """🔥 ENHANCED COVERAGE FLAG DETECTION"""
        table_lower = source_table.lower()
        
        if 'chronicle' in table_lower:
            host['coverage_flags']['in_chronicle'] = True
        if 'crowdstrike' in table_lower or 'cs_' in table_lower or 'falcon' in table_lower:
            host['coverage_flags']['in_crowdstrike'] = True
        if 'cmdb' in table_lower or 'v_dim_endpoint' in table_lower:
            host['coverage_flags']['in_original_cmdb'] = True
        if 'splunk' in table_lower or 'spl_' in table_lower:
            host['coverage_flags']['in_splunk'] = True
        if 'tanium' in table_lower:
            host['coverage_flags']['in_tanium'] = True
        if 'dlp' in table_lower:
            host['coverage_flags']['in_dlp'] = True
    
    def get_serializable_cmdb(self) -> Dict[str, Any]:
        """🔥 CONVERT SETS TO LISTS FOR JSON SERIALIZATION"""
        serializable_cmdb = {}
        
        for hostname, host_data in self.cmdb.items():
            serializable_cmdb[hostname] = {
                'asset_id': hostname,
                'hostname': host_data['hostname'],
                'source_tables': list(host_data['source_tables']),
                'all_attributes': {k: list(v) for k, v in host_data['all_attributes'].items()},
                'coverage_flags': host_data['coverage_flags'],
                'first_seen': host_data['first_seen'],
                'last_updated': host_data['last_updated'],
                'source_count': host_data['source_count'],
                'total_rows': host_data['total_rows'],
                'total_unique_attributes': sum(len(v) for v in host_data['all_attributes'].values())
            }
        
        return serializable_cmdb
    
    def update_processing_stats(self):
        """🔥 REAL-TIME PERFORMANCE MONITORING"""
        if self.processing_stats['start_time']:
            elapsed = (datetime.now() - self.processing_stats['start_time']).total_seconds()
            if elapsed > 0:
                self.processing_stats['rows_per_second'] = self.processing_stats['total_rows_processed'] / elapsed
        
        self.processing_stats['memory_usage_mb'] = psutil.Process().memory_info().rss / 1024 / 1024

class MaximumIntensityTableProcessor:
    def __init__(self, cmdb_builder: MaximumIntensityRealtimeCMDBBuilder, db_manager=None):
        self.cmdb_builder = cmdb_builder
        self.db_manager = db_manager
        self.host_identifier_patterns = [
            'hostname', 'host_name', 'computername', 'computer_name', 'device_name',
            'endpoint', 'asset_name', 'machine_name', 'system_name'
        ]
    
    def find_host_columns(self, columns: List[str]) -> List[str]:
        """🔥 INTELLIGENT HOST COLUMN DETECTION"""
        host_columns = []
        
        for column in columns:
            column_lower = column.lower()
            for pattern in self.host_identifier_patterns:
                if pattern in column_lower:
                    host_columns.append(column)
                    break
        
        return host_columns
    
    async def process_table_maximum_intensity(self, client, table_path: str) -> int:
        """🔥 MAXIMUM INTENSITY TABLE PROCESSING - PROCESSES EVERY ROW"""
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return 0
            
            columns = [field.name for field in table.schema]
            host_columns = self.find_host_columns(columns)
            
            if not host_columns:
                logger.debug(f"⚠️  No host columns found in {table_path}")
                return 0
            
            primary_host_column = host_columns[0]
            total_rows = table.num_rows
            
            logger.info(f"🔥🔥🔥 MAXIMUM INTENSITY PROCESSING: {table_path}")
            logger.info(f"📊 TOTAL ROWS TO PROCESS: {total_rows:,}")
            logger.info(f"🎯 HOST COLUMN: {primary_host_column}")
            logger.info(f"📋 ALL COLUMNS: {len(columns)} ({', '.join(columns[:10])}...)")
            logger.info(f"🌪️  FANS WILL DEFINITELY SPIN FOR THIS ONE!")
            
            batch_size = 50000  # Smaller batches for more intensive processing
            offset = 0
            total_processed = 0
            hosts_found_in_table = 0
            
            while True:
                # 🔥 MAXIMUM INTENSITY: Process ALL columns, ALL rows
                query = f"""
                SELECT *
                FROM `{table_path}`
                LIMIT {batch_size} OFFSET {offset}
                """
                
                try:
                    job = client.query(query)
                    results = list(job.result())
                    
                    if not results:
                        break
                    
                    batch_hosts = 0
                    hosts_in_batch = []
                    for row in results:
                        # Convert row to dictionary for processing
                        row_data = dict(zip(columns, row))
                        
                        host_value = row_data.get(primary_host_column)
                        if host_value and str(host_value).strip():
                            hostname = str(host_value).strip()
                            
                            # 🔥 IMMEDIATE PROCESSING AND LOGGING
                            self.cmdb_builder.add_host_to_cmdb_maximum_intensity(
                                hostname, row_data, table_path, self.db_manager
                            )
                            
                            batch_hosts += 1
                            hosts_in_batch.append(hostname)
                    
                    total_processed += len(results)
                    hosts_found_in_table += batch_hosts
                    self.cmdb_builder.processing_stats['total_rows_processed'] += len(results)
                    
                    # 🔥 REAL-TIME PROGRESS LOGGING WITH HOST DETAILS AND DB STATS
                    self.cmdb_builder.update_processing_stats()
                    progress_pct = (total_processed / total_rows) * 100 if total_rows > 0 else 100
                    
                    logger.info(f"⚡ BATCH COMPLETE: {total_processed:,}/{total_rows:,} rows ({progress_pct:.1f}%)")
                    logger.info(f"🏠 HOSTS IN BATCH: {batch_hosts:,} | TABLE TOTAL: {hosts_found_in_table:,}")
                    logger.info(f"🔥 PROCESSING SPEED: {self.cmdb_builder.processing_stats['rows_per_second']:,.0f} rows/sec")
                    logger.info(f"💾 MEMORY USAGE: {self.cmdb_builder.processing_stats['memory_usage_mb']:.1f} MB")
                    logger.info(f"🌪️  CUMULATIVE HOSTS: {len(self.cmdb_builder.cmdb):,}")
                    
                    # 🔥 SHOW REAL-TIME DATABASE STATS
                    if self.db_manager:
                        db_stats = self.db_manager.get_live_stats()
                        logger.info(f"💾 DATABASE: {db_stats['total_hosts_in_db']:,} hosts stored ({db_stats['database_size_mb']:.1f} MB)")
                        
                        # Show sample hosts from database every few batches
                        if offset % 150000 == 0:  # Every ~3 batches
                            sample_hosts = self.db_manager.show_sample_hosts(3)
                            if sample_hosts:
                                logger.info("   📋 Recent DB entries:")
                                for host in sample_hosts:
                                    logger.info(f"      🏠 {host}")
                    
                    # 🔥 LOG SAMPLE HOSTS FROM THIS BATCH
                    if hosts_in_batch:
                        sample_hosts = hosts_in_batch[:5]  # Show first 5 hosts
                        logger.info(f"   📋 Sample hosts: {', '.join(sample_hosts)}")
                        if len(hosts_in_batch) > 5:
                            logger.info(f"   📋 ... and {len(hosts_in_batch) - 5} more hosts")
                    
                    offset += batch_size
                    
                    # Memory management
                    if offset % 200000 == 0:  # Every 200k rows
                        gc.collect()
                        logger.info(f"🧹 MEMORY CLEANUP PERFORMED")
                    
                    if len(results) < batch_size:
                        break
                        
                except Exception as e:
                    logger.error(f"💥 BATCH PROCESSING FAILED: {e}")
                    break
            
            logger.info(f"✅ TABLE COMPLETE: {table_path}")
            logger.info(f"📊 PROCESSED {total_processed:,} rows, found {hosts_found_in_table:,} hosts")
            
            # 🔥 FINAL DATABASE VERIFICATION FOR THIS TABLE
            if self.db_manager:
                db_stats = self.db_manager.get_live_stats()
                logger.info(f"💾 DATABASE NOW CONTAINS: {db_stats['total_hosts_in_db']:,} total hosts")
                logger.info(f"💾 DATABASE SIZE: {db_stats['database_size_mb']:.1f} MB")
                
                # Show sample of recent entries
                recent_hosts = self.db_manager.show_sample_hosts(5)
                if recent_hosts:
                    logger.info("   📋 Recent database entries:")
                    for host in recent_hosts:
                        logger.info(f"      🏠 {host}")
            
            self.cmdb_builder.processing_stats['tables_processed'] += 1
            return total_processed
            
        except Exception as e:
            logger.error(f"💥 TABLE PROCESSING FAILED: {table_path} - {e}")
            return 0

class MaximumIntensityOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cmdb_builder = MaximumIntensityRealtimeCMDBBuilder()
        
        # 🔥 INITIALIZE DATABASE MANAGER FOR REAL-TIME STORAGE
        from storage.database import MaximumIntensityDatabaseManager
        self.db_manager = MaximumIntensityDatabaseManager(config.get('database_path', 'maximum_intensity_cmdb.db'))
        
        self.processor = MaximumIntensityTableProcessor(self.cmdb_builder, self.db_manager)
        
        # 🔥 MAXIMUM INTENSITY STATS TRACKING
        self.orchestration_stats = {
            'start_time': None,
            'projects_processed': 0,
            'datasets_processed': 0,
            'tables_processed': 0,
            'total_tables_found': 0,
            'processing_errors': 0,
            'peak_memory_mb': 0
        }
    
    async def execute_maximum_intensity_discovery(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        """🔥🔥🔥 MAXIMUM INTENSITY DISCOVERY - WILL DEFINITELY SPIN YOUR FANS! 🔥🔥🔥"""
        
        self.orchestration_stats['start_time'] = datetime.now()
        self.cmdb_builder.processing_stats['start_time'] = datetime.now()
        
        logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
        logger.info("🌪️  MAXIMUM INTENSITY REAL-TIME CMDB BUILDING INITIATED 🌪️")
        logger.info("⚡ WARNING: THIS WILL PROCESS EVERY SINGLE ROW IN EVERY TABLE ⚡")
        logger.info("🔥 YOUR FANS WILL SPIN - CPU AND MEMORY WILL BE MAXED OUT! 🔥")
        logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
        
        # Count total tables first for progress tracking
        total_tables_count = 0
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                try:
                    datasets = list(client.list_datasets(project=project_id))
                    for dataset in datasets:
                        tables = list(client.list_tables(dataset))
                        total_tables_count += len(tables)
                except Exception as e:
                    logger.error(f"💥 Failed to count tables in {project_id}: {e}")
        
        self.orchestration_stats['total_tables_found'] = total_tables_count
        logger.info(f"🎯 TOTAL TABLES TO PROCESS: {total_tables_count:,}")
        logger.info(f"⚡ ESTIMATED PROCESSING TIME: SEVERAL HOURS")
        
        tables_completed = 0
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🔥 MAXIMUM INTENSITY PROJECT PROCESSING: {project_id}")
            
            try:
                with client_manager.get_client() as client:
                    datasets = list(client.list_datasets(project=project_id))
                    
                    for dataset in datasets:
                        logger.info(f"⚡ DATASET: {project_id}.{dataset.dataset_id}")
                        
                        try:
                            tables = list(client.list_tables(dataset))
                            
                            for table_ref in tables:
                                table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                                
                                try:
                                    rows_processed = await self.processor.process_table_maximum_intensity(
                                        client, table_path
                                    )
                                    
                                    tables_completed += 1
                                    progress_pct = (tables_completed / total_tables_count) * 100
                                    
                                    logger.info(f"🏁 TABLE {tables_completed:,}/{total_tables_count:,} COMPLETE ({progress_pct:.1f}%)")
                                    logger.info(f"📊 ROWS PROCESSED: {rows_processed:,}")
                                    
                                    # Update peak memory tracking
                                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                                    self.orchestration_stats['peak_memory_mb'] = max(
                                        self.orchestration_stats['peak_memory_mb'], current_memory
                                    )
                                    
                                except Exception as e:
                                    logger.error(f"💥 TABLE FAILED: {table_ref.table_id} - {e}")
                                    self.orchestration_stats['processing_errors'] += 1
                            
                            self.orchestration_stats['datasets_processed'] += 1
                            
                        except Exception as e:
                            logger.error(f"💥 DATASET FAILED: {dataset.dataset_id} - {e}")
                            self.orchestration_stats['processing_errors'] += 1
                
                self.orchestration_stats['projects_processed'] += 1
                
            except Exception as e:
                logger.error(f"💥 PROJECT FAILED: {project_id} - {e}")
                self.orchestration_stats['processing_errors'] += 1
        
        # 🔥 FINAL RESULTS COMPILATION
        final_cmdb = self.cmdb_builder.get_serializable_cmdb()
        processing_time = (datetime.now() - self.orchestration_stats['start_time']).total_seconds()
        
        logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
        logger.info("🎉🎉🎉 MAXIMUM INTENSITY DISCOVERY COMPLETE! 🎉🎉🎉")
        logger.info(f"🏠 TOTAL UNIQUE HOSTS DISCOVERED: {len(final_cmdb):,}")
        logger.info(f"📊 TOTAL ROWS PROCESSED: {self.cmdb_builder.processing_stats['total_rows_processed']:,}")
        logger.info(f"📋 TOTAL ATTRIBUTES EXTRACTED: {self.cmdb_builder.processing_stats['attributes_added']:,}")
        logger.info(f"📊 TOTAL CELLS ANALYZED: {self.cmdb_builder.processing_stats['total_cells_analyzed']:,}")
        logger.info(f"⏱️  TOTAL PROCESSING TIME: {processing_time/60:.1f} minutes")
        logger.info(f"⚡ AVERAGE PROCESSING SPEED: {self.cmdb_builder.processing_stats['rows_per_second']:,.0f} rows/sec")
        logger.info(f"💾 PEAK MEMORY USAGE: {self.orchestration_stats['peak_memory_mb']:.1f} MB")
        logger.info(f"🌪️  YOUR FANS CAN NOW SLOW DOWN! 🌪️")
        logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(final_cmdb),
                'total_rows_processed': self.cmdb_builder.processing_stats['total_rows_processed'],
                'total_attributes_extracted': self.cmdb_builder.processing_stats['attributes_added'],
                'total_cells_analyzed': self.cmdb_builder.processing_stats['total_cells_analyzed'],
                'tables_processed': self.orchestration_stats['tables_processed'],
                'processing_time_minutes': processing_time / 60,
                'rows_per_second': self.cmdb_builder.processing_stats['rows_per_second'],
                'peak_memory_mb': self.orchestration_stats['peak_memory_mb'],
                'maximum_intensity_mode': True,
                'fans_were_spinning': True
            },
            'assets': final_cmdb
        }

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.orchestrator = MaximumIntensityOrchestrator(config)
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """🔥 MAXIMUM INTENSITY DISCOVERY ENTRY POINT"""
        return await self.orchestrator.execute_maximum_intensity_discovery(client_managers)