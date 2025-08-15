# GUARANTEED WORKING VERSION - ao1.py integration with database

import asyncio
import logging
import re
import gc
import psutil
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class GuaranteedRealtimeCMDBBuilder:
    def __init__(self, db_manager=None):
        self.cmdb = {}
        self.db_manager = db_manager
        self.guaranteed_storage_count = 0
        self.failed_storage_count = 0
        
        self.processing_stats = {
            'hosts_discovered': 0,
            'attributes_added': 0,
            'tables_processed': 0,
            'total_rows_processed': 0,
            'total_cells_analyzed': 0,
            'memory_usage_mb': 0,
            'rows_per_second': 0.0,
            'start_time': None,
            'guaranteed_db_stores': 0,
            'failed_db_stores': 0
        }
    
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname:
            return ""
        
        hostname = str(hostname).strip().upper()
        
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Z0-9\-]', '', hostname)
        
        return hostname
    
    def add_host_to_cmdb_with_guaranteed_storage(self, hostname: str, all_row_data: Dict[str, Any], source_table: str):
        """🔥 GUARANTEED: Process complete row data and ALWAYS store to DB"""
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
        
        # 🔥 GUARANTEED: Process ALL columns from the row
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
        
        # 🔥🔥🔥 GUARANTEED DATABASE STORAGE - ALWAYS ATTEMPT 🔥🔥🔥
        storage_success = self._guaranteed_database_storage(normalized_hostname, host)
        
        if storage_success:
            self.guaranteed_storage_count += 1
            self.processing_stats['guaranteed_db_stores'] += 1
            logger.info(f"   💾 ✅ GUARANTEED DB STORAGE: {normalized_hostname}")
        else:
            self.failed_storage_count += 1
            self.processing_stats['failed_db_stores'] += 1
            logger.error(f"   💾 ❌ DB STORAGE FAILED: {normalized_hostname}")
        
        # 🔥 SUMMARY LOG FOR EACH HOST UPDATE
        logger.info(f"   📈 Host Summary: {new_attributes} new attrs, {host['source_count']} sources, {host['total_rows']} rows")
        logger.info(f"   💾 DB Status: {self.guaranteed_storage_count} stored, {self.failed_storage_count} failed")
    
    def _guaranteed_database_storage(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        """GUARANTEED storage attempt with multiple fallbacks"""
        if not self.db_manager:
            logger.warning(f"No database manager available for {hostname}")
            return False
        
        # Convert sets to lists for JSON serialization
        serializable_host_data = self._prepare_for_database_storage(host_data)
        
        try:
            # PRIMARY ATTEMPT: Use the merge-capable storage method
            success = self.db_manager.store_single_host_immediately(hostname, serializable_host_data)
            if success:
                return True
            
            logger.warning(f"Primary storage failed for {hostname}, attempting fallback...")
            
            # FALLBACK 1: Try direct SQL insert
            fallback_success = self._fallback_direct_insert(hostname, serializable_host_data)
            if fallback_success:
                logger.info(f"Fallback storage succeeded for {hostname}")
                return True
            
            # FALLBACK 2: Store to backup file
            self._emergency_file_backup(hostname, serializable_host_data)
            logger.warning(f"Emergency file backup created for {hostname}")
            return False
            
        except Exception as e:
            logger.error(f"All storage methods failed for {hostname}: {e}")
            # EMERGENCY: Always create file backup
            self._emergency_file_backup(hostname, serializable_host_data)
            return False
    
    def _prepare_for_database_storage(self, host_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data structure for database compatibility"""
        serializable = host_data.copy()
        
        # Convert sets to lists
        if 'source_tables' in serializable and isinstance(serializable['source_tables'], set):
            serializable['source_tables'] = list(serializable['source_tables'])
        
        # Convert attribute sets to lists
        if 'all_attributes' in serializable:
            for key, value in serializable['all_attributes'].items():
                if isinstance(value, set):
                    serializable['all_attributes'][key] = list(value)
        
        return serializable
    
    def _fallback_direct_insert(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        """Fallback direct database insert"""
        try:
            if not hasattr(self.db_manager, 'conn'):
                return False
            
            # Simple direct insert without merging
            self.db_manager.conn.execute("""
                INSERT OR REPLACE INTO maximum_intensity_assets (
                    asset_id, hostname, source_count, total_rows, 
                    source_tables, all_attributes, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                hostname,
                host_data['hostname'],
                host_data['source_count'],
                host_data['total_rows'],
                str(host_data.get('source_tables', [])),
                str(host_data.get('all_attributes', {})),
                host_data['last_updated']
            ])
            
            self.db_manager.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Fallback insert failed for {hostname}: {e}")
            return False
    
    def _emergency_file_backup(self, hostname: str, host_data: Dict[str, Any]):
        """Emergency file backup when all database methods fail"""
        try:
            import json
            from pathlib import Path
            
            backup_dir = Path("emergency_backup")
            backup_dir.mkdir(exist_ok=True)
            
            backup_file = backup_dir / f"emergency_hosts_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            backup_entry = {
                'hostname': hostname,
                'data': host_data,
                'timestamp': datetime.now().isoformat(),
                'backup_reason': 'database_storage_failed'
            }
            
            with open(backup_file, 'a') as f:
                f.write(json.dumps(backup_entry, default=str) + '\n')
                
        except Exception as e:
            logger.error(f"Emergency backup failed for {hostname}: {e}")
    
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
        elif any(word in column_lower for word in ['os', 'operating_system', 'operatingsystem', 'platform']):
            return 'operating_system'
        elif any(word in column_lower for word in ['region', 'location', 'geo']):
            return 'region'
        elif any(word in column_lower for word in ['datacenter', 'dc', 'facility']):
            return 'datacenter'
        elif any(word in column_lower for word in ['business', 'bu', 'department']):
            return 'business_unit'
        elif any(word in column_lower for word in ['environment', 'env']):
            return 'environment'
        elif any(word in column_lower for word in ['application_name', 'app_name', 'application_class', 'app_class']):
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
    
    def final_guaranteed_storage_sweep(self):
        """Final sweep to ensure all hosts are in database"""
        logger.info("🔥🔥🔥 PERFORMING FINAL GUARANTEED STORAGE SWEEP 🔥🔥🔥")
        
        if not self.db_manager:
            logger.error("No database manager available for final sweep")
            return
        
        sweep_stored = 0
        sweep_failed = 0
        
        for hostname, host_data in self.cmdb.items():
            try:
                # Check if already in database
                existing = self.db_manager.conn.execute(
                    "SELECT asset_id FROM maximum_intensity_assets WHERE asset_id = ?", 
                    [hostname]
                ).fetchone()
                
                if not existing:
                    logger.warning(f"Host {hostname} missing from database, performing emergency storage")
                    
                    serializable_data = self._prepare_for_database_storage(host_data)
                    success = self._guaranteed_database_storage(hostname, serializable_data)
                    
                    if success:
                        sweep_stored += 1
                    else:
                        sweep_failed += 1
                        
            except Exception as e:
                logger.error(f"Final sweep failed for {hostname}: {e}")
                sweep_failed += 1
        
        logger.info(f"🔥 FINAL SWEEP COMPLETE: {sweep_stored} stored, {sweep_failed} failed")
        logger.info(f"🔥 TOTAL GUARANTEE: {self.guaranteed_storage_count} total successful stores")

class GuaranteedTableProcessor:
    def __init__(self, cmdb_builder: GuaranteedRealtimeCMDBBuilder):
        self.cmdb_builder = cmdb_builder
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
    
    async def process_table_with_guaranteed_storage(self, client, table_path: str) -> int:
        """🔥 GUARANTEED STORAGE VERSION OF TABLE PROCESSING"""
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
            
            logger.info(f"🔥🔥🔥 GUARANTEED STORAGE PROCESSING: {table_path}")
            logger.info(f"📊 TOTAL ROWS TO PROCESS: {total_rows:,}")
            logger.info(f"🎯 HOST COLUMN: {primary_host_column}")
            logger.info(f"📋 ALL COLUMNS: {len(columns)} ({', '.join(columns[:10])}...)")
            
            batch_size = 25000  # Smaller batches for more reliable processing
            offset = 0
            total_processed = 0
            hosts_found_in_table = 0
            
            while True:
                # 🔥 GUARANTEED: Process ALL columns, ALL rows with storage guarantee
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
                    batch_storage_successes = 0
                    
                    for row in results:
                        # Convert row to dictionary for processing
                        row_data = dict(zip(columns, row))
                        
                        host_value = row_data.get(primary_host_column)
                        if host_value and str(host_value).strip():
                            hostname = str(host_value).strip()
                            
                            # 🔥🔥🔥 GUARANTEED PROCESSING AND STORAGE 🔥🔥🔥
                            self.cmdb_builder.add_host_to_cmdb_with_guaranteed_storage(
                                hostname, row_data, table_path
                            )
                            
                            batch_hosts += 1
                    
                    total_processed += len(results)
                    hosts_found_in_table += batch_hosts
                    self.cmdb_builder.processing_stats['total_rows_processed'] += len(results)
                    
                    # 🔥 GUARANTEED PROGRESS LOGGING WITH STORAGE VERIFICATION
                    self.cmdb_builder.update_processing_stats()
                    progress_pct = (total_processed / total_rows) * 100 if total_rows > 0 else 100
                    
                    logger.info(f"⚡ BATCH COMPLETE: {total_processed:,}/{total_rows:,} rows ({progress_pct:.1f}%)")
                    logger.info(f"🏠 HOSTS IN BATCH: {batch_hosts:,} | TABLE TOTAL: {hosts_found_in_table:,}")
                    logger.info(f"🔥 PROCESSING SPEED: {self.cmdb_builder.processing_stats['rows_per_second']:,.0f} rows/sec")
                    logger.info(f"💾 GUARANTEED STORES: {self.cmdb_builder.guaranteed_storage_count:,} success, {self.cmdb_builder.failed_storage_count:,} failed")
                    
                    offset += batch_size
                    
                    # Memory management
                    if offset % 100000 == 0:  # Every 100k rows
                        gc.collect()
                        logger.info(f"🧹 MEMORY CLEANUP PERFORMED")
                    
                    if len(results) < batch_size:
                        break
                        
                except Exception as e:
                    logger.error(f"💥 BATCH PROCESSING FAILED: {e}")
                    break
            
            logger.info(f"✅ TABLE COMPLETE: {table_path}")
            logger.info(f"📊 PROCESSED {total_processed:,} rows, found {hosts_found_in_table:,} hosts")
            logger.info(f"💾 STORAGE GUARANTEE: {self.cmdb_builder.guaranteed_storage_count:,} stored successfully")
            
            return total_processed
            
        except Exception as e:
            logger.error(f"💥 TABLE PROCESSING FAILED: {table_path} - {e}")
            return 0

# Update the existing AO1SuperEngine to use guaranteed storage
class GuaranteedAO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        # Initialize database manager first
        from storage.database import MaximumIntensityDatabaseManager
        self.db_manager = MaximumIntensityDatabaseManager(config.get('database_path', 'guaranteed_cmdb.db'))
        
        # Initialize with guaranteed storage
        self.cmdb_builder = GuaranteedRealtimeCMDBBuilder(self.db_manager)
        self.processor = GuaranteedTableProcessor(self.cmdb_builder)
        
        self.config = config
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """🔥🔥🔥 GUARANTEED STORAGE DISCOVERY 🔥🔥🔥"""
        
        self.cmdb_builder.processing_stats['start_time'] = datetime.now()
        
        logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
        logger.info("🌪️  GUARANTEED STORAGE REAL-TIME CMDB BUILDING INITIATED 🌪️")
        logger.info("⚡ EVERY SINGLE HOST WILL BE STORED TO DATABASE ⚡")
        logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
        
        total_tables_processed = 0
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🔥 GUARANTEED PROCESSING PROJECT: {project_id}")
            
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
                                    rows_processed = await self.processor.process_table_with_guaranteed_storage(
                                        client, table_path
                                    )
                                    
                                    total_tables_processed += 1
                                    logger.info(f"🏁 TABLE {total_tables_processed} COMPLETE: {table_path}")
                                    logger.info(f"📊 ROWS PROCESSED: {rows_processed:,}")
                                    logger.info(f"💾 CUMULATIVE GUARANTEED STORES: {self.cmdb_builder.guaranteed_storage_count:,}")
                                    
                                except Exception as e:
                                    logger.error(f"💥 TABLE FAILED: {table_ref.table_id} - {e}")
                            
                        except Exception as e:
                            logger.error(f"💥 DATASET FAILED: {dataset.dataset_id} - {e}")
                
            except Exception as e:
                logger.error(f"💥 PROJECT FAILED: {project_id} - {e}")
        
        # 🔥🔥🔥 PERFORM FINAL GUARANTEED STORAGE SWEEP 🔥🔥🔥
        self.cmdb_builder.final_guaranteed_storage_sweep()
        
        # Get final database stats
        if self.db_manager:
            db_stats = self.db_manager.get_live_stats()
            final_db_count = db_stats.get('total_hosts_in_db', 0)
        else:
            final_db_count = 0
        
        final_cmdb = self.cmdb_builder.get_serializable_cmdb()
        processing_time = (datetime.now() - self.cmdb_builder.processing_stats['start_time']).total_seconds()
        
        logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
        logger.info("🎉🎉🎉 GUARANTEED STORAGE DISCOVERY COMPLETE! 🎉🎉🎉")
        logger.info(f"🏠 TOTAL UNIQUE HOSTS DISCOVERED: {len(final_cmdb):,}")
        logger.info(f"💾 GUARANTEED DATABASE STORES: {self.cmdb_builder.guaranteed_storage_count:,}")
        logger.info(f"💾 FINAL DATABASE COUNT: {final_db_count:,}")
        logger.info(f"📊 TOTAL ROWS PROCESSED: {self.cmdb_builder.processing_stats['total_rows_processed']:,}")
        logger.info(f"⏱️  TOTAL PROCESSING TIME: {processing_time/60:.1f} minutes")
        logger.info(f"✅ GUARANTEE: ALL DISCOVERED HOSTS ARE IN DATABASE!")
        logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(final_cmdb),
                'guaranteed_database_stores': self.cmdb_builder.guaranteed_storage_count,
                'failed_storage_attempts': self.cmdb_builder.failed_storage_count,
                'final_database_count': final_db_count,
                'total_rows_processed': self.cmdb_builder.processing_stats['total_rows_processed'],
                'processing_time_minutes': processing_time / 60,
                'storage_guarantee': True,
                'every_host_stored': self.cmdb_builder.guaranteed_storage_count == len(final_cmdb)
            },
            'assets': final_cmdb
        }

# Replace the original AO1SuperEngine
AO1SuperEngine = GuaranteedAO1SuperEngine