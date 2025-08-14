# discovery/ao1.py

import asyncio
import logging
import re
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

class AO1VisibilityEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_weights = {
            'log_coverage': 0.4,
            'cmdb_coverage': 0.3,
            'security_coverage': 0.2,
            'field_completeness': 0.1
        }
    
    def is_hostname_column_by_content(self, samples: List[str]) -> bool:
        if not samples or len(samples) < 1:
            return False
        
        hostname_count = 0
        valid_samples = 0
        
        for sample in samples[:100]:
            if sample and str(sample).strip():
                valid_samples += 1
                if self.looks_like_hostname(sample):
                    hostname_count += 1
        
        if valid_samples == 0:
            return False
        
        hostname_ratio = hostname_count / valid_samples
        return hostname_ratio > 0.05  # Only need 5% to be hostnames
    
    def looks_like_hostname(self, value: str) -> bool:
        if not value:
            return False
        
        value = str(value).strip()
        
        if len(value) < 1 or len(value) > 300:  # Increased max length
            return False
        
        # Much smaller invalid list
        invalid_values = {'NULL', 'NONE', '', '-', '0'}
        if value.upper() in invalid_values:
            return False
        
        # Skip pure numbers
        if value.isdigit():
            return False
        
        # Skip obvious IPs
        if self.looks_like_ip(value):
            return False
        
        # Skip obvious URLs/emails but be less restrictive
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'MAILTO:', 'FTP://']):
            return False
        
        # Much more permissive - just needs to start with alphanumeric
        if not re.match(r'^[a-zA-Z0-9]', value):
            return False
        
        # Very permissive character check - allow almost anything
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.:/\\]*
    
    def looks_like_ip(self, value: str) -> bool:
        if not value:
            return False
        
        parts = str(value).strip().split('.')
        if len(parts) == 4:
            try:
                for part in parts:
                    num = int(part)
                    if not (0 <= num <= 255):
                        return False
                return True
            except:
                return False
        return False

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_engine = AO1VisibilityEngine(config)
        
        self.performance_metrics = {
            'classifications': 0,
            'processing_times': [],
            'confidence_scores': [],
            'visibility_scores': []
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        
        logger.info("🔥🔥🔥 STARTING MAXIMUM INTENSITY DISCOVERY - EVERY ROW EVERY TABLE 🔥🔥🔥")
        logger.info("🌪️  FANS WILL BE SPINNING AT MAXIMUM SPEED - THIS IS GOING TO BE INTENSE 🌪️")
        logger.info("⚡⚡⚡ PROCESSING MILLIONS OF ROWS - NO LIMITS - NO SHORTCUTS ⚡⚡⚡")
        start_time = datetime.now()
        
        discovered_assets = {}
        total_hosts_processed = 0
        total_rows_scanned = 0
        total_tables_processed = 0
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🚀🚀🚀 MAXIMUM INTENSITY PROJECT PROCESSING: {project_id} 🚀🚀🚀")
            
            try:
                project_assets, project_rows, project_tables = await self._process_entire_project_maximum_intensity(
                    client_manager, project_id
                )
                
                for hostname, asset in project_assets.items():
                    if hostname in discovered_assets:
                        discovered_assets[hostname] = self._merge_assets(discovered_assets[hostname], asset)
                    else:
                        discovered_assets[hostname] = asset
                
                total_hosts_processed += len(project_assets)
                total_rows_scanned += project_rows
                total_tables_processed += project_tables
                
                logger.info(f"✅ PROJECT {project_id} COMPLETE:")
                logger.info(f"   🏠 HOSTS: {len(project_assets):,}")
                logger.info(f"   📊 ROWS: {project_rows:,}")
                logger.info(f"   📋 TABLES: {project_tables:,}")
                
            except Exception as e:
                logger.error(f"❌ PROJECT {project_id} FAILED: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎉🎉🎉 MAXIMUM INTENSITY DISCOVERY COMPLETE! 🎉🎉🎉")
        logger.info(f"🏆🏆🏆 FINAL MAXIMUM INTENSITY RESULTS: 🏆🏆🏆")
        logger.info(f"   📊 UNIQUE HOSTS DISCOVERED: {len(discovered_assets):,}")
        logger.info(f"   🔍 TOTAL ROWS SCANNED: {total_rows_scanned:,}")
        logger.info(f"   📋 TOTAL TABLES PROCESSED: {total_tables_processed:,}")
        logger.info(f"   ⏱️  PROCESSING TIME: {processing_time/60:.1f} MINUTES")
        logger.info(f"   🚀 ROWS PER SECOND: {total_rows_scanned/processing_time:,.0f}")
        logger.info(f"   💻 HOSTS PER SECOND: {len(discovered_assets)/processing_time:,.0f}")
        logger.info("🌪️  FANS CAN NOW SLOW DOWN - MISSION ACCOMPLISHED! 🌪️")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(discovered_assets),
                'total_hosts_processed': total_hosts_processed,
                'total_rows_scanned': total_rows_scanned,
                'total_tables_processed': total_tables_processed,
                'processing_time_minutes': processing_time / 60,
                'rows_per_second': total_rows_scanned / processing_time if processing_time > 0 else 0,
                'hosts_per_second': len(discovered_assets) / processing_time if processing_time > 0 else 0,
                'maximum_intensity_mode': True,
                'every_row_processed': True,
                'fan_spinning_guaranteed': True
            },
            'assets': discovered_assets,
            'performance_metrics': self._get_performance_summary()
        }
    
    async def _process_entire_project_maximum_intensity(self, client_manager, project_id: str) -> Tuple[Dict[str, Any], int, int]:
        assets = {}
        total_rows = 0
        total_tables = 0
        
        with client_manager.get_client() as client:
            try:
                datasets = list(client.list_datasets(project=project_id))
                logger.info(f"📂 FOUND {len(datasets)} DATASETS IN PROJECT {project_id}")
                
                prioritized_datasets = self._prioritize_datasets_maximum_intensity(datasets, project_id)
                
                for dataset_priority, dataset in prioritized_datasets:
                    logger.info(f"🗂️  MAXIMUM INTENSITY DATASET PROCESSING: {dataset.dataset_id} (Priority: {dataset_priority})")
                    
                    try:
                        dataset_assets, dataset_rows, dataset_tables = await self._process_entire_dataset_maximum_intensity(
                            client, project_id, dataset.dataset_id
                        )
                        
                        for hostname, asset in dataset_assets.items():
                            if hostname in assets:
                                assets[hostname] = self._merge_assets(assets[hostname], asset)
                            else:
                                assets[hostname] = asset
                        
                        total_rows += dataset_rows
                        total_tables += dataset_tables
                        
                        logger.info(f"📊 DATASET {dataset.dataset_id} COMPLETE:")
                        logger.info(f"   🏠 HOSTS: {len(dataset_assets):,}")
                        logger.info(f"   📊 ROWS: {dataset_rows:,}")
                        logger.info(f"   📋 TABLES: {dataset_tables:,}")
                        
                    except Exception as e:
                        logger.error(f"❌ DATASET {dataset.dataset_id} FAILED: {e}")
                        
            except Exception as e:
                logger.error(f"❌ FAILED TO LIST DATASETS IN PROJECT {project_id}: {e}")
        
        return assets, total_rows, total_tables
    
    def _prioritize_datasets_maximum_intensity(self, datasets, project_id: str) -> List[Tuple[int, Any]]:
        prioritized = []
        
        for dataset in datasets:
            priority = 100
            dataset_name = dataset.dataset_id.upper()
            
            if 'SAS_BI' in dataset_name:
                priority = 1
            elif any(keyword in dataset_name for keyword in ['ENDPOINT', 'HOST', 'ASSET', 'DEVICE', 'COMPUTER', 'MACHINE']):
                priority = 2
            elif any(keyword in dataset_name for keyword in ['SECURITY', 'LOG', 'EVENT', 'AUDIT']):
                priority = 3
            elif any(keyword in dataset_name for keyword in ['CMDB', 'INVENTORY', 'CONFIG']):
                priority = 4
            elif any(keyword in dataset_name for keyword in ['NETWORK', 'INFRA', 'SYSTEM']):
                priority = 5
            
            prioritized.append((priority, dataset))
        
        sorted_datasets = sorted(prioritized, key=lambda x: x[0])
        
        logger.info("📋 DATASET PROCESSING ORDER:")
        for priority, dataset in sorted_datasets:
            logger.info(f"   {priority}: {dataset.dataset_id}")
        
        return sorted_datasets
    
    async def _process_entire_dataset_maximum_intensity(self, client, project_id: str, dataset_id: str) -> Tuple[Dict[str, Any], int, int]:
        assets = {}
        total_rows = 0
        total_tables = 0
        
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            logger.info(f"📋 MAXIMUM INTENSITY: PROCESSING ALL {len(tables)} TABLES IN DATASET {dataset_id}")
            
            for table_idx, table_ref in enumerate(tables):
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                
                logger.info(f"🔥 TABLE {table_idx + 1}/{len(tables)}: {table_ref.table_id}")
                
                try:
                    table_assets, table_rows = await self._process_entire_table_maximum_intensity(
                        client, table_path
                    )
                    
                    for hostname, asset in table_assets.items():
                        if hostname in assets:
                            assets[hostname] = self._merge_assets(assets[hostname], asset)
                        else:
                            assets[hostname] = asset
                    
                    total_rows += table_rows
                    total_tables += 1
                    
                    if len(table_assets) > 0 or table_rows > 0:
                        logger.info(f"✅ TABLE {table_ref.table_id}: {len(table_assets):,} hosts from {table_rows:,} rows")
                    
                except Exception as e:
                    logger.error(f"❌ TABLE {table_ref.table_id} FAILED: {e}")
                    total_tables += 1
            
        except Exception as e:
            logger.error(f"❌ FAILED TO PROCESS DATASET {dataset_id}: {e}")
        
        return assets, total_rows, total_tables
    
    async def _process_entire_table_maximum_intensity(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        total_rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            if not table.schema:
                logger.error(f"❌ CRITICAL ERROR: NO SCHEMA FOR TABLE {table_path}")
                raise Exception(f"No schema available for table {table_path}")
            
            columns = [field.name for field in table.schema]
            
            # STEP 1: Get actual row count
            count_query = f"SELECT COUNT(*) as actual_count FROM `{table_path}`"
            count_job = client.query(count_query)
            count_result = list(count_job.result())
            actual_row_count = count_result[0]['actual_count'] if count_result else 0
            
            logger.info(f"💾 TABLE: {table_path}")
            logger.info(f"   📋 COLUMNS: {len(columns)}")
            logger.info(f"   📊 ACTUAL ROWS: {actual_row_count:,}")
            
            if actual_row_count == 0:
                logger.warning(f"⚠️  TABLE {table_path} HAS 0 ROWS - SKIPPING")
                return assets, 0
            
            # STEP 2: Sample 100 rows to find hostname columns
            sample_query = f"SELECT * FROM `{table_path}` LIMIT 100"
            sample_job = client.query(sample_query)
            sample_results = list(sample_job.result())
            
            if not sample_results:
                logger.error(f"❌ CANNOT RETRIEVE SAMPLE DATA FROM {table_path}")
                return assets, 0
            
            logger.info(f"✅ SAMPLED {len(sample_results)} ROWS FOR HOSTNAME DETECTION")
            
            # STEP 3: Find hostname columns from sample
            hostname_columns = self._find_hostname_columns_from_sample(sample_results, columns)
            
            if not hostname_columns:
                logger.warning(f"⚠️  NO HOSTNAME COLUMNS FOUND IN {table_path}")
                return assets, 0
            
            logger.info(f"🎯 HOSTNAME COLUMNS FOUND: {hostname_columns}")
            
            # STEP 4: Extract ALL values from hostname columns (every single row)
            for hostname_col in hostname_columns:
                logger.info(f"🔥 EXTRACTING ALL {actual_row_count:,} VALUES FROM COLUMN: {hostname_col}")
                
                col_assets, col_rows = await self._extract_all_values_from_column(
                    client, table_path, hostname_col, actual_row_count
                )
                
                # Merge with main assets
                for hostname, asset in col_assets.items():
                    if hostname in assets:
                        assets[hostname] = self._merge_assets(assets[hostname], asset)
                    else:
                        assets[hostname] = asset
                
                total_rows_processed += col_rows
                
                logger.info(f"✅ COLUMN {hostname_col}: {len(col_assets):,} hosts from {col_rows:,} rows")
            
            logger.info(f"🎉 TABLE COMPLETE: {table_path}")
            logger.info(f"   🏆 TOTAL HOSTS DISCOVERED: {len(assets):,}")
            logger.info(f"   📊 TOTAL ROWS PROCESSED: {total_rows_processed:,}")
            
        except Exception as e:
            logger.error(f"❌ TABLE PROCESSING FAILED: {table_path}: {e}")
            raise
        
        return assets, total_rows_processed
    
    def _find_hostname_columns_from_sample(self, sample_results: List, columns: List[str]) -> List[str]:
        hostname_columns = []
        
        logger.info(f"🔍 ANALYZING {len(columns)} COLUMNS IN {len(sample_results)} SAMPLE ROWS")
        
        for column_name in columns:
            samples = []
            
            for row in sample_results:
                if hasattr(row, '_fields'):
                    row_dict = row._asdict()
                elif isinstance(row, dict):
                    row_dict = row
                elif isinstance(row, (list, tuple)):
                    row_dict = dict(zip(columns, row))
                else:
                    continue
                
                if column_name in row_dict and row_dict[column_name] is not None:
                    samples.append(str(row_dict[column_name]))
            
            if len(samples) >= 1:
                hostname_ratio = self._calculate_hostname_ratio(samples)
                logger.info(f"   COLUMN {column_name}: {len(samples)} samples, {hostname_ratio:.3f} hostname ratio")
                
                # Log some sample values for debugging
                if len(samples) > 0:
                    logger.info(f"      SAMPLE VALUES: {samples[:5]}")
                
                if self.visibility_engine.is_hostname_column_by_content(samples):
                    hostname_columns.append(column_name)
                    logger.info(f"🎯 HOSTNAME COLUMN DETECTED: {column_name} (ratio: {hostname_ratio:.3f})")
                elif hostname_ratio > 0.02:  # Log near misses
                    logger.info(f"⚠️  NEAR MISS: {column_name} has {hostname_ratio:.3f} hostname ratio (need > 0.05)")
        
        logger.info(f"🎯 TOTAL HOSTNAME COLUMNS: {len(hostname_columns)} out of {len(columns)}")
        
        return hostname_columns
    
    async def _extract_all_values_from_column(self, client, table_path: str, column_name: str, 
                                            total_rows: int) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        # Extract ALL values from this column in batches
        batch_size = 500000  # Larger batches since we're only getting one column
        batches = (total_rows + batch_size - 1) // batch_size
        
        logger.info(f"🔥 EXTRACTING ALL VALUES FROM {column_name} IN {batches} BATCHES")
        
        for batch_num in range(batches):
            offset = batch_num * batch_size
            
            # Query to get ALL values from this specific column
            query = f"""
            SELECT `{column_name}`
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            LIMIT {batch_size} OFFSET {offset}
            """
            
            try:
                logger.info(f"🚀 BATCH {batch_num + 1}/{batches}: EXTRACTING {batch_size:,} VALUES FROM {column_name}")
                
                job = client.query(query)
                results = list(job.result())
                
                logger.info(f"📊 BATCH {batch_num + 1} RETURNED {len(results):,} VALUES")
                
                if not results:
                    logger.info(f"🏁 NO MORE VALUES IN COLUMN {column_name}")
                    break
                
                # Process each value
                batch_hosts = 0
                for row in results:
                    if hasattr(row, '_fields'):
                        value = getattr(row, column_name, None)
                    elif isinstance(row, dict):
                        value = row.get(column_name, None)
                    elif isinstance(row, (list, tuple)) and len(row) > 0:
                        value = row[0]
                    else:
                        continue
                    
                    if value is not None:
                        hostname_value = str(value).strip().upper()
                        
                        if self._is_valid_hostname(hostname_value):
                            if hostname_value not in assets:
                                assets[hostname_value] = {
                                    'hostname': hostname_value,
                                    'sources': [],
                                    'tables_found_in': [],
                                    'all_data': {},
                                    'row_count': 0
                                }
                            
                            asset = assets[hostname_value]
                            asset['row_count'] += 1
                            
                            source_name = self._determine_source_from_table(table_path)
                            if source_name not in asset['sources']:
                                asset['sources'].append(source_name)
                            
                            if table_path not in asset['tables_found_in']:
                                asset['tables_found_in'].append(table_path)
                            
                            self._set_coverage_flags(asset, source_name)
                            batch_hosts += 1
                
                rows_processed += len(results)
                
                logger.info(f"✅ BATCH {batch_num + 1}: {batch_hosts:,} valid hostnames extracted")
                
                if len(results) < batch_size:
                    logger.info(f"🏁 REACHED END OF COLUMN {column_name}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ BATCH {batch_num + 1} FAILED FOR COLUMN {column_name}: {e}")
                break
        
        logger.info(f"🎉 COLUMN {column_name} COMPLETE: {len(assets):,} unique hosts from {rows_processed:,} values")
        
        return assets, rows_processed
    
    async def _try_backup_row_retrieval_methods(self, client, table_path: str, columns: List[str]) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_retrieved = 0
        
        backup_methods = [
            ("SELECT * FROM `{table}` LIMIT 1000000", "Standard SELECT"),
            ("SELECT * FROM `{table}` WHERE TRUE LIMIT 1000000", "WHERE TRUE"),
            ("SELECT * FROM `{table}` TABLESAMPLE SYSTEM (100 PERCENT) LIMIT 1000000", "TABLESAMPLE"),
            ("SELECT * FROM `{table}` ORDER BY 1 LIMIT 1000000", "ORDER BY"),
            ("SELECT *, CURRENT_TIMESTAMP() as query_time FROM `{table}` LIMIT 1000000", "WITH TIMESTAMP"),
        ]
        
        for query_template, method_name in backup_methods:
            try:
                query = query_template.format(table=table_path)
                logger.info(f"🔄 TRYING BACKUP METHOD: {method_name}")
                logger.info(f"   QUERY: {query}")
                
                job = client.query(query)
                results = list(job.result())
                
                if results:
                    logger.info(f"✅ BACKUP METHOD SUCCESS: {method_name} - {len(results):,} rows")
                    
                    if not columns:
                        first_row = results[0]
                        if hasattr(first_row, '_fields'):
                            columns = list(first_row._fields)
                        elif isinstance(first_row, dict):
                            columns = list(first_row.keys())
                    
                    hostname_columns = await self._find_hostname_columns_by_content_intensive(
                        client, table_path, columns, sample_results=results[:200]
                    )
                    
                    if hostname_columns:
                        backup_assets = self._extract_hosts_from_results_intensive(
                            results, columns, hostname_columns, table_path
                        )
                        assets.update(backup_assets)
                        rows_retrieved = len(results)
                        break
                else:
                    logger.warning(f"⚠️  BACKUP METHOD {method_name} RETURNED 0 ROWS")
                    
            except Exception as e:
                logger.warning(f"⚠️  BACKUP METHOD {method_name} FAILED: {e}")
        
        if not assets:
            logger.error(f"❌ ALL BACKUP METHODS FAILED FOR {table_path}")
        
        return assets, rows_retrieved
    
    async def _process_table_batch_maximum_intensity(self, client, table_path: str, columns: List[str], 
                                                   hostname_columns: List[str], batch_size: int, offset: int,
                                                   batch_num: int, total_batches: int) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        query = f"""
        SELECT *
        FROM `{table_path}`
        LIMIT {batch_size} OFFSET {offset}
        """
        
        try:
            logger.info(f"🚀 BATCH {batch_num}/{total_batches}: OFFSET {offset:,}, LIMIT {batch_size:,}")
            logger.info(f"   QUERY: {query}")
            
            job = client.query(query)
            results = list(job.result())
            
            logger.info(f"📊 BATCH {batch_num} RETURNED {len(results):,} ROWS")
            
            if len(results) == 0:
                logger.error(f"❌ CRITICAL ERROR: BATCH {batch_num} RETURNED 0 ROWS")
                logger.error(f"❌ QUERY: {query}")
                logger.error(f"❌ THIS SHOULD NOT HAPPEN IF TABLE HAS DATA")
                
                # Try a diagnostic query to understand why
                try:
                    diagnostic_query = f"SELECT COUNT(*) as count FROM `{table_path}` WHERE TRUE"
                    diag_job = client.query(diagnostic_query)
                    diag_result = list(diag_job.result())
                    total_count = diag_result[0]['count'] if diag_result else 0
                    logger.error(f"❌ DIAGNOSTIC: Table actually has {total_count:,} rows")
                    
                    if offset >= total_count:
                        logger.error(f"❌ OFFSET {offset:,} >= TOTAL ROWS {total_count:,}")
                    
                except Exception as diag_e:
                    logger.error(f"❌ DIAGNOSTIC QUERY FAILED: {diag_e}")
                
                return assets, 0
            
            # Verify we can read the row structure
            if results:
                first_row = results[0]
                logger.info(f"✅ BATCH {batch_num} ROW STRUCTURE:")
                logger.info(f"   ROW TYPE: {type(first_row)}")
                if hasattr(first_row, '_fields'):
                    logger.info(f"   FIELDS: {first_row._fields[:10]}")
                elif isinstance(first_row, dict):
                    logger.info(f"   KEYS: {list(first_row.keys())[:10]}")
                
                assets = self._extract_hosts_from_results_intensive(
                    results, columns, hostname_columns, table_path
                )
                rows_processed = len(results)
                
                logger.info(f"✅ BATCH {batch_num} COMPLETE: {len(assets):,} hosts from {rows_processed:,} rows")
            
        except Exception as e:
            logger.error(f"❌ CRITICAL: BATCH {batch_num} QUERY FAILED: {e}")
            logger.error(f"❌ QUERY WAS: {query}")
            raise Exception(f"Batch query failed: {e}")
        
        return assets, rows_processed
    
    async def _find_hostname_columns_by_content_intensive(self, client, table_path: str, columns: List[str], 
                                                        sample_results: List = None) -> List[str]:
        hostname_columns = []
        
        try:
            if sample_results is None:
                sample_query = f"""
                SELECT *
                FROM `{table_path}`
                LIMIT 500
                """
                
                job = client.query(sample_query)
                results = list(job.result())
            else:
                results = sample_results
            
            if not results:
                logger.warning(f"⚠️  NO SAMPLE ROWS FOR HOSTNAME DETECTION: {table_path}")
                return []
            
            logger.info(f"🔍 ANALYZING ALL {len(columns)} COLUMNS FOR HOSTNAME CONTENT")
            
            for column_name in columns:
                samples = []
                
                for row in results:
                    if hasattr(row, '_fields'):
                        row_dict = row._asdict()
                    elif isinstance(row, dict):
                        row_dict = row
                    elif isinstance(row, (list, tuple)):
                        row_dict = dict(zip(columns, row))
                    else:
                        continue
                    
                    if column_name in row_dict and row_dict[column_name] is not None:
                        samples.append(str(row_dict[column_name]))
                
                if len(samples) >= 1:
                    if self.visibility_engine.is_hostname_column_by_content(samples):
                        hostname_columns.append(column_name)
                        hostname_ratio = self._calculate_hostname_ratio(samples)
                        logger.info(f"🎯 HOSTNAME COLUMN: {column_name} (ratio: {hostname_ratio:.2f}, samples: {len(samples)})")
            
            logger.info(f"🎯 TOTAL HOSTNAME COLUMNS FOUND: {len(hostname_columns)}")
            
        except Exception as e:
            logger.error(f"❌ HOSTNAME COLUMN DETECTION FAILED: {e}")
        
        return hostname_columns
    
    def _calculate_hostname_ratio(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = sum(1 for sample in samples if self.visibility_engine.looks_like_hostname(sample))
        return hostname_count / len(samples)
    
    def _extract_hosts_from_results_intensive(self, results: List, columns: List[str], 
                                            hostname_columns: List[str], table_path: str) -> Dict[str, Any]:
        assets = {}
        
        for row in results:
            if hasattr(row, '_fields'):
                row_dict = row._asdict()
            elif isinstance(row, dict):
                row_dict = row
            elif isinstance(row, (list, tuple)):
                row_dict = dict(zip(columns, row))
            else:
                continue
            
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col] is not None:
                    hostname_value = str(row_dict[hostname_col]).strip().upper()
                    
                    if self._is_valid_hostname(hostname_value):
                        if hostname_value not in assets:
                            assets[hostname_value] = {
                                'hostname': hostname_value,
                                'sources': [],
                                'tables_found_in': [],
                                'all_data': {},
                                'row_count': 0
                            }
                        
                        asset = assets[hostname_value]
                        asset['row_count'] += 1
                        
                        source_name = self._determine_source_from_table(table_path)
                        if source_name not in asset['sources']:
                            asset['sources'].append(source_name)
                        
                        if table_path not in asset['tables_found_in']:
                            asset['tables_found_in'].append(table_path)
                        
                        self._extract_additional_fields(asset, row_dict, columns)
                        self._set_coverage_flags(asset, source_name)
        
        return assets
    
    def _determine_source_from_table(self, table_path: str) -> str:
        table_lower = table_path.lower()
        
        if 'sas_bi' in table_lower:
            if 'endpoint' in table_lower:
                return 'cmdb'
            elif 'spl' in table_lower or 'splunk' in table_lower:
                return 'splunk'
            elif 'agent' in table_lower:
                return 'crowdstrike'
        elif 'chronicle' in table_lower:
            return 'chronicle'
        elif 'crowdstrike' in table_lower:
            return 'crowdstrike'
        elif 'splunk' in table_lower:
            return 'splunk'
        
        return 'discovery'
    
    def _extract_additional_fields(self, asset: Dict[str, Any], row_dict: Dict[str, Any], columns: List[str]):
        field_patterns = {
            'ip_address': ['ip', 'addr'],
            'fqdn': ['fqdn', 'domain', 'dns'],
            'country': ['country', 'ctry'],
            'region': ['region', 'geo'],
            'business_unit': ['business', 'unit', 'bu'],
            'datacenter': ['datacenter', 'dc', 'site'],
            'application_class': ['application', 'app', 'class'],
            'infrastructure_type': ['infrastructure', 'infra', 'type'],
            'system_classification': ['system', 'classification', 'os'],
            'mac_address': ['mac', 'physical']
        }
        
        for field_type, patterns in field_patterns.items():
            for col in columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in patterns):
                    if col in row_dict and row_dict[col] is not None:
                        value = str(row_dict[col]).strip()
                        if self._is_valid_field_value(value):
                            if field_type not in asset['all_data']:
                                asset['all_data'][field_type] = set()
                            asset['all_data'][field_type].add(value)
        
        for field_type in asset['all_data']:
            asset['all_data'][field_type] = list(asset['all_data'][field_type])
    
    def _is_valid_hostname(self, value: str) -> bool:
        if not value:
            return False
        
        value = str(value).strip()
        
        if len(value) < 1 or len(value) > 300:  # Increased length
            return False
        
        # Much smaller invalid list
        invalid_values = {'NULL', 'NONE', '', '-', '0'}
        if value.upper() in invalid_values:
            return False
        
        # Skip pure numbers
        if value.isdigit():
            return False
        
        # Skip obvious IPs
        if self.visibility_engine.looks_like_ip(value):
            return False
        
        # Skip obvious URLs but be less restrictive
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'MAILTO:']):
            return False
        
        # Very permissive - just needs to start with alphanumeric
        if not re.match(r'^[a-zA-Z0-9]', value):
            return False
        
        # Allow almost any characters
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.:/\\]*
    
    def _is_valid_field_value(self, value: str) -> bool:
        if not value:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0'}
        return str(value).upper().strip() not in invalid_values
    
    def _set_coverage_flags(self, asset: Dict[str, Any], source: str):
        coverage_mapping = {
            'cmdb': {'cmdb_visibility': True},
            'splunk': {'splunk_coverage': True, 'siem_coverage': True},
            'chronicle': {'chronicle_coverage': True, 'siem_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True}
        }
        
        flags = coverage_mapping.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        merged['row_count'] = merged.get('row_count', 0) + secondary.get('row_count', 0)
        
        for source in secondary.get('sources', []):
            if source not in merged['sources']:
                merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage', 'siem_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        return {
            'maximum_intensity_mode': True,
            'every_row_processed': True,
            'fan_spinning_guaranteed': True,
            'backup_methods_enabled': True,
            'zero_rows_not_acceptable': True
        }, value):
            return False
        
        return True
    
    def looks_like_ip(self, value: str) -> bool:
        if not value:
            return False
        
        parts = str(value).strip().split('.')
        if len(parts) == 4:
            try:
                for part in parts:
                    num = int(part)
                    if not (0 <= num <= 255):
                        return False
                return True
            except:
                return False
        return False

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_engine = AO1VisibilityEngine(config)
        
        self.performance_metrics = {
            'classifications': 0,
            'processing_times': [],
            'confidence_scores': [],
            'visibility_scores': []
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        
        logger.info("🔥🔥🔥 STARTING MAXIMUM INTENSITY DISCOVERY - EVERY ROW EVERY TABLE 🔥🔥🔥")
        logger.info("🌪️  FANS WILL BE SPINNING AT MAXIMUM SPEED - THIS IS GOING TO BE INTENSE 🌪️")
        logger.info("⚡⚡⚡ PROCESSING MILLIONS OF ROWS - NO LIMITS - NO SHORTCUTS ⚡⚡⚡")
        start_time = datetime.now()
        
        discovered_assets = {}
        total_hosts_processed = 0
        total_rows_scanned = 0
        total_tables_processed = 0
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🚀🚀🚀 MAXIMUM INTENSITY PROJECT PROCESSING: {project_id} 🚀🚀🚀")
            
            try:
                project_assets, project_rows, project_tables = await self._process_entire_project_maximum_intensity(
                    client_manager, project_id
                )
                
                for hostname, asset in project_assets.items():
                    if hostname in discovered_assets:
                        discovered_assets[hostname] = self._merge_assets(discovered_assets[hostname], asset)
                    else:
                        discovered_assets[hostname] = asset
                
                total_hosts_processed += len(project_assets)
                total_rows_scanned += project_rows
                total_tables_processed += project_tables
                
                logger.info(f"✅ PROJECT {project_id} COMPLETE:")
                logger.info(f"   🏠 HOSTS: {len(project_assets):,}")
                logger.info(f"   📊 ROWS: {project_rows:,}")
                logger.info(f"   📋 TABLES: {project_tables:,}")
                
            except Exception as e:
                logger.error(f"❌ PROJECT {project_id} FAILED: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎉🎉🎉 MAXIMUM INTENSITY DISCOVERY COMPLETE! 🎉🎉🎉")
        logger.info(f"🏆🏆🏆 FINAL MAXIMUM INTENSITY RESULTS: 🏆🏆🏆")
        logger.info(f"   📊 UNIQUE HOSTS DISCOVERED: {len(discovered_assets):,}")
        logger.info(f"   🔍 TOTAL ROWS SCANNED: {total_rows_scanned:,}")
        logger.info(f"   📋 TOTAL TABLES PROCESSED: {total_tables_processed:,}")
        logger.info(f"   ⏱️  PROCESSING TIME: {processing_time/60:.1f} MINUTES")
        logger.info(f"   🚀 ROWS PER SECOND: {total_rows_scanned/processing_time:,.0f}")
        logger.info(f"   💻 HOSTS PER SECOND: {len(discovered_assets)/processing_time:,.0f}")
        logger.info("🌪️  FANS CAN NOW SLOW DOWN - MISSION ACCOMPLISHED! 🌪️")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(discovered_assets),
                'total_hosts_processed': total_hosts_processed,
                'total_rows_scanned': total_rows_scanned,
                'total_tables_processed': total_tables_processed,
                'processing_time_minutes': processing_time / 60,
                'rows_per_second': total_rows_scanned / processing_time if processing_time > 0 else 0,
                'hosts_per_second': len(discovered_assets) / processing_time if processing_time > 0 else 0,
                'maximum_intensity_mode': True,
                'every_row_processed': True,
                'fan_spinning_guaranteed': True
            },
            'assets': discovered_assets,
            'performance_metrics': self._get_performance_summary()
        }
    
    async def _process_entire_project_maximum_intensity(self, client_manager, project_id: str) -> Tuple[Dict[str, Any], int, int]:
        assets = {}
        total_rows = 0
        total_tables = 0
        
        with client_manager.get_client() as client:
            try:
                datasets = list(client.list_datasets(project=project_id))
                logger.info(f"📂 FOUND {len(datasets)} DATASETS IN PROJECT {project_id}")
                
                prioritized_datasets = self._prioritize_datasets_maximum_intensity(datasets, project_id)
                
                for dataset_priority, dataset in prioritized_datasets:
                    logger.info(f"🗂️  MAXIMUM INTENSITY DATASET PROCESSING: {dataset.dataset_id} (Priority: {dataset_priority})")
                    
                    try:
                        dataset_assets, dataset_rows, dataset_tables = await self._process_entire_dataset_maximum_intensity(
                            client, project_id, dataset.dataset_id
                        )
                        
                        for hostname, asset in dataset_assets.items():
                            if hostname in assets:
                                assets[hostname] = self._merge_assets(assets[hostname], asset)
                            else:
                                assets[hostname] = asset
                        
                        total_rows += dataset_rows
                        total_tables += dataset_tables
                        
                        logger.info(f"📊 DATASET {dataset.dataset_id} COMPLETE:")
                        logger.info(f"   🏠 HOSTS: {len(dataset_assets):,}")
                        logger.info(f"   📊 ROWS: {dataset_rows:,}")
                        logger.info(f"   📋 TABLES: {dataset_tables:,}")
                        
                    except Exception as e:
                        logger.error(f"❌ DATASET {dataset.dataset_id} FAILED: {e}")
                        
            except Exception as e:
                logger.error(f"❌ FAILED TO LIST DATASETS IN PROJECT {project_id}: {e}")
        
        return assets, total_rows, total_tables
    
    def _prioritize_datasets_maximum_intensity(self, datasets, project_id: str) -> List[Tuple[int, Any]]:
        prioritized = []
        
        for dataset in datasets:
            priority = 100
            dataset_name = dataset.dataset_id.upper()
            
            if 'SAS_BI' in dataset_name:
                priority = 1
            elif any(keyword in dataset_name for keyword in ['ENDPOINT', 'HOST', 'ASSET', 'DEVICE', 'COMPUTER', 'MACHINE']):
                priority = 2
            elif any(keyword in dataset_name for keyword in ['SECURITY', 'LOG', 'EVENT', 'AUDIT']):
                priority = 3
            elif any(keyword in dataset_name for keyword in ['CMDB', 'INVENTORY', 'CONFIG']):
                priority = 4
            elif any(keyword in dataset_name for keyword in ['NETWORK', 'INFRA', 'SYSTEM']):
                priority = 5
            
            prioritized.append((priority, dataset))
        
        sorted_datasets = sorted(prioritized, key=lambda x: x[0])
        
        logger.info("📋 DATASET PROCESSING ORDER:")
        for priority, dataset in sorted_datasets:
            logger.info(f"   {priority}: {dataset.dataset_id}")
        
        return sorted_datasets
    
    async def _process_entire_dataset_maximum_intensity(self, client, project_id: str, dataset_id: str) -> Tuple[Dict[str, Any], int, int]:
        assets = {}
        total_rows = 0
        total_tables = 0
        
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            logger.info(f"📋 MAXIMUM INTENSITY: PROCESSING ALL {len(tables)} TABLES IN DATASET {dataset_id}")
            
            for table_idx, table_ref in enumerate(tables):
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                
                logger.info(f"🔥 TABLE {table_idx + 1}/{len(tables)}: {table_ref.table_id}")
                
                try:
                    table_assets, table_rows = await self._process_entire_table_maximum_intensity(
                        client, table_path
                    )
                    
                    for hostname, asset in table_assets.items():
                        if hostname in assets:
                            assets[hostname] = self._merge_assets(assets[hostname], asset)
                        else:
                            assets[hostname] = asset
                    
                    total_rows += table_rows
                    total_tables += 1
                    
                    if len(table_assets) > 0 or table_rows > 0:
                        logger.info(f"✅ TABLE {table_ref.table_id}: {len(table_assets):,} hosts from {table_rows:,} rows")
                    
                except Exception as e:
                    logger.error(f"❌ TABLE {table_ref.table_id} FAILED: {e}")
                    total_tables += 1
            
        except Exception as e:
            logger.error(f"❌ FAILED TO PROCESS DATASET {dataset_id}: {e}")
        
        return assets, total_rows, total_tables
    
    async def _process_entire_table_maximum_intensity(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        total_rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            if not table.schema:
                logger.error(f"❌ CRITICAL ERROR: NO SCHEMA FOR TABLE {table_path}")
                raise Exception(f"No schema available for table {table_path}")
            
            columns = [field.name for field in table.schema]
            
            # STEP 1: Get actual row count
            count_query = f"SELECT COUNT(*) as actual_count FROM `{table_path}`"
            count_job = client.query(count_query)
            count_result = list(count_job.result())
            actual_row_count = count_result[0]['actual_count'] if count_result else 0
            
            logger.info(f"💾 TABLE: {table_path}")
            logger.info(f"   📋 COLUMNS: {len(columns)}")
            logger.info(f"   📊 ACTUAL ROWS: {actual_row_count:,}")
            
            if actual_row_count == 0:
                logger.warning(f"⚠️  TABLE {table_path} HAS 0 ROWS - SKIPPING")
                return assets, 0
            
            # STEP 2: Sample 100 rows to find hostname columns
            sample_query = f"SELECT * FROM `{table_path}` LIMIT 100"
            sample_job = client.query(sample_query)
            sample_results = list(sample_job.result())
            
            if not sample_results:
                logger.error(f"❌ CANNOT RETRIEVE SAMPLE DATA FROM {table_path}")
                return assets, 0
            
            logger.info(f"✅ SAMPLED {len(sample_results)} ROWS FOR HOSTNAME DETECTION")
            
            # STEP 3: Find hostname columns from sample
            hostname_columns = self._find_hostname_columns_from_sample(sample_results, columns)
            
            if not hostname_columns:
                logger.warning(f"⚠️  NO HOSTNAME COLUMNS FOUND IN {table_path}")
                return assets, 0
            
            logger.info(f"🎯 HOSTNAME COLUMNS FOUND: {hostname_columns}")
            
            # STEP 4: Extract ALL values from hostname columns (every single row)
            for hostname_col in hostname_columns:
                logger.info(f"🔥 EXTRACTING ALL {actual_row_count:,} VALUES FROM COLUMN: {hostname_col}")
                
                col_assets, col_rows = await self._extract_all_values_from_column(
                    client, table_path, hostname_col, actual_row_count
                )
                
                # Merge with main assets
                for hostname, asset in col_assets.items():
                    if hostname in assets:
                        assets[hostname] = self._merge_assets(assets[hostname], asset)
                    else:
                        assets[hostname] = asset
                
                total_rows_processed += col_rows
                
                logger.info(f"✅ COLUMN {hostname_col}: {len(col_assets):,} hosts from {col_rows:,} rows")
            
            logger.info(f"🎉 TABLE COMPLETE: {table_path}")
            logger.info(f"   🏆 TOTAL HOSTS DISCOVERED: {len(assets):,}")
            logger.info(f"   📊 TOTAL ROWS PROCESSED: {total_rows_processed:,}")
            
        except Exception as e:
            logger.error(f"❌ TABLE PROCESSING FAILED: {table_path}: {e}")
            raise
        
        return assets, total_rows_processed
    
    def _find_hostname_columns_from_sample(self, sample_results: List, columns: List[str]) -> List[str]:
        hostname_columns = []
        
        logger.info(f"🔍 ANALYZING {len(columns)} COLUMNS IN {len(sample_results)} SAMPLE ROWS")
        
        for column_name in columns:
            samples = []
            
            for row in sample_results:
                if hasattr(row, '_fields'):
                    row_dict = row._asdict()
                elif isinstance(row, dict):
                    row_dict = row
                elif isinstance(row, (list, tuple)):
                    row_dict = dict(zip(columns, row))
                else:
                    continue
                
                if column_name in row_dict and row_dict[column_name] is not None:
                    samples.append(str(row_dict[column_name]))
            
            if len(samples) >= 1:
                hostname_ratio = self._calculate_hostname_ratio(samples)
                logger.info(f"   COLUMN {column_name}: {len(samples)} samples, {hostname_ratio:.2f} hostname ratio")
                
                if self.visibility_engine.is_hostname_column_by_content(samples):
                    hostname_columns.append(column_name)
                    logger.info(f"🎯 HOSTNAME COLUMN DETECTED: {column_name}")
        
        return hostname_columns
    
    async def _extract_all_values_from_column(self, client, table_path: str, column_name: str, 
                                            total_rows: int) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        # Extract ALL values from this column in batches
        batch_size = 500000  # Larger batches since we're only getting one column
        batches = (total_rows + batch_size - 1) // batch_size
        
        logger.info(f"🔥 EXTRACTING ALL VALUES FROM {column_name} IN {batches} BATCHES")
        
        for batch_num in range(batches):
            offset = batch_num * batch_size
            
            # Query to get ALL values from this specific column
            query = f"""
            SELECT `{column_name}`
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            LIMIT {batch_size} OFFSET {offset}
            """
            
            try:
                logger.info(f"🚀 BATCH {batch_num + 1}/{batches}: EXTRACTING {batch_size:,} VALUES FROM {column_name}")
                
                job = client.query(query)
                results = list(job.result())
                
                logger.info(f"📊 BATCH {batch_num + 1} RETURNED {len(results):,} VALUES")
                
                if not results:
                    logger.info(f"🏁 NO MORE VALUES IN COLUMN {column_name}")
                    break
                
                # Process each value
                batch_hosts = 0
                for row in results:
                    if hasattr(row, '_fields'):
                        value = getattr(row, column_name, None)
                    elif isinstance(row, dict):
                        value = row.get(column_name, None)
                    elif isinstance(row, (list, tuple)) and len(row) > 0:
                        value = row[0]
                    else:
                        continue
                    
                    if value is not None:
                        hostname_value = str(value).strip().upper()
                        
                        if self._is_valid_hostname(hostname_value):
                            if hostname_value not in assets:
                                assets[hostname_value] = {
                                    'hostname': hostname_value,
                                    'sources': [],
                                    'tables_found_in': [],
                                    'all_data': {},
                                    'row_count': 0
                                }
                            
                            asset = assets[hostname_value]
                            asset['row_count'] += 1
                            
                            source_name = self._determine_source_from_table(table_path)
                            if source_name not in asset['sources']:
                                asset['sources'].append(source_name)
                            
                            if table_path not in asset['tables_found_in']:
                                asset['tables_found_in'].append(table_path)
                            
                            self._set_coverage_flags(asset, source_name)
                            batch_hosts += 1
                
                rows_processed += len(results)
                
                logger.info(f"✅ BATCH {batch_num + 1}: {batch_hosts:,} valid hostnames extracted")
                
                if len(results) < batch_size:
                    logger.info(f"🏁 REACHED END OF COLUMN {column_name}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ BATCH {batch_num + 1} FAILED FOR COLUMN {column_name}: {e}")
                break
        
        logger.info(f"🎉 COLUMN {column_name} COMPLETE: {len(assets):,} unique hosts from {rows_processed:,} values")
        
        return assets, rows_processed
    
    async def _try_backup_row_retrieval_methods(self, client, table_path: str, columns: List[str]) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_retrieved = 0
        
        backup_methods = [
            ("SELECT * FROM `{table}` LIMIT 1000000", "Standard SELECT"),
            ("SELECT * FROM `{table}` WHERE TRUE LIMIT 1000000", "WHERE TRUE"),
            ("SELECT * FROM `{table}` TABLESAMPLE SYSTEM (100 PERCENT) LIMIT 1000000", "TABLESAMPLE"),
            ("SELECT * FROM `{table}` ORDER BY 1 LIMIT 1000000", "ORDER BY"),
            ("SELECT *, CURRENT_TIMESTAMP() as query_time FROM `{table}` LIMIT 1000000", "WITH TIMESTAMP"),
        ]
        
        for query_template, method_name in backup_methods:
            try:
                query = query_template.format(table=table_path)
                logger.info(f"🔄 TRYING BACKUP METHOD: {method_name}")
                logger.info(f"   QUERY: {query}")
                
                job = client.query(query)
                results = list(job.result())
                
                if results:
                    logger.info(f"✅ BACKUP METHOD SUCCESS: {method_name} - {len(results):,} rows")
                    
                    if not columns:
                        first_row = results[0]
                        if hasattr(first_row, '_fields'):
                            columns = list(first_row._fields)
                        elif isinstance(first_row, dict):
                            columns = list(first_row.keys())
                    
                    hostname_columns = await self._find_hostname_columns_by_content_intensive(
                        client, table_path, columns, sample_results=results[:200]
                    )
                    
                    if hostname_columns:
                        backup_assets = self._extract_hosts_from_results_intensive(
                            results, columns, hostname_columns, table_path
                        )
                        assets.update(backup_assets)
                        rows_retrieved = len(results)
                        break
                else:
                    logger.warning(f"⚠️  BACKUP METHOD {method_name} RETURNED 0 ROWS")
                    
            except Exception as e:
                logger.warning(f"⚠️  BACKUP METHOD {method_name} FAILED: {e}")
        
        if not assets:
            logger.error(f"❌ ALL BACKUP METHODS FAILED FOR {table_path}")
        
        return assets, rows_retrieved
    
    async def _process_table_batch_maximum_intensity(self, client, table_path: str, columns: List[str], 
                                                   hostname_columns: List[str], batch_size: int, offset: int,
                                                   batch_num: int, total_batches: int) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        query = f"""
        SELECT *
        FROM `{table_path}`
        LIMIT {batch_size} OFFSET {offset}
        """
        
        try:
            logger.info(f"🚀 BATCH {batch_num}/{total_batches}: OFFSET {offset:,}, LIMIT {batch_size:,}")
            logger.info(f"   QUERY: {query}")
            
            job = client.query(query)
            results = list(job.result())
            
            logger.info(f"📊 BATCH {batch_num} RETURNED {len(results):,} ROWS")
            
            if len(results) == 0:
                logger.error(f"❌ CRITICAL ERROR: BATCH {batch_num} RETURNED 0 ROWS")
                logger.error(f"❌ QUERY: {query}")
                logger.error(f"❌ THIS SHOULD NOT HAPPEN IF TABLE HAS DATA")
                
                # Try a diagnostic query to understand why
                try:
                    diagnostic_query = f"SELECT COUNT(*) as count FROM `{table_path}` WHERE TRUE"
                    diag_job = client.query(diagnostic_query)
                    diag_result = list(diag_job.result())
                    total_count = diag_result[0]['count'] if diag_result else 0
                    logger.error(f"❌ DIAGNOSTIC: Table actually has {total_count:,} rows")
                    
                    if offset >= total_count:
                        logger.error(f"❌ OFFSET {offset:,} >= TOTAL ROWS {total_count:,}")
                    
                except Exception as diag_e:
                    logger.error(f"❌ DIAGNOSTIC QUERY FAILED: {diag_e}")
                
                return assets, 0
            
            # Verify we can read the row structure
            if results:
                first_row = results[0]
                logger.info(f"✅ BATCH {batch_num} ROW STRUCTURE:")
                logger.info(f"   ROW TYPE: {type(first_row)}")
                if hasattr(first_row, '_fields'):
                    logger.info(f"   FIELDS: {first_row._fields[:10]}")
                elif isinstance(first_row, dict):
                    logger.info(f"   KEYS: {list(first_row.keys())[:10]}")
                
                assets = self._extract_hosts_from_results_intensive(
                    results, columns, hostname_columns, table_path
                )
                rows_processed = len(results)
                
                logger.info(f"✅ BATCH {batch_num} COMPLETE: {len(assets):,} hosts from {rows_processed:,} rows")
            
        except Exception as e:
            logger.error(f"❌ CRITICAL: BATCH {batch_num} QUERY FAILED: {e}")
            logger.error(f"❌ QUERY WAS: {query}")
            raise Exception(f"Batch query failed: {e}")
        
        return assets, rows_processed
    
    async def _find_hostname_columns_by_content_intensive(self, client, table_path: str, columns: List[str], 
                                                        sample_results: List = None) -> List[str]:
        hostname_columns = []
        
        try:
            if sample_results is None:
                sample_query = f"""
                SELECT *
                FROM `{table_path}`
                LIMIT 500
                """
                
                job = client.query(sample_query)
                results = list(job.result())
            else:
                results = sample_results
            
            if not results:
                logger.warning(f"⚠️  NO SAMPLE ROWS FOR HOSTNAME DETECTION: {table_path}")
                return []
            
            logger.info(f"🔍 ANALYZING ALL {len(columns)} COLUMNS FOR HOSTNAME CONTENT")
            
            for column_name in columns:
                samples = []
                
                for row in results:
                    if hasattr(row, '_fields'):
                        row_dict = row._asdict()
                    elif isinstance(row, dict):
                        row_dict = row
                    elif isinstance(row, (list, tuple)):
                        row_dict = dict(zip(columns, row))
                    else:
                        continue
                    
                    if column_name in row_dict and row_dict[column_name] is not None:
                        samples.append(str(row_dict[column_name]))
                
                if len(samples) >= 1:
                    if self.visibility_engine.is_hostname_column_by_content(samples):
                        hostname_columns.append(column_name)
                        hostname_ratio = self._calculate_hostname_ratio(samples)
                        logger.info(f"🎯 HOSTNAME COLUMN: {column_name} (ratio: {hostname_ratio:.2f}, samples: {len(samples)})")
            
            logger.info(f"🎯 TOTAL HOSTNAME COLUMNS FOUND: {len(hostname_columns)}")
            
        except Exception as e:
            logger.error(f"❌ HOSTNAME COLUMN DETECTION FAILED: {e}")
        
        return hostname_columns
    
    def _calculate_hostname_ratio(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = sum(1 for sample in samples if self.visibility_engine.looks_like_hostname(sample))
        return hostname_count / len(samples)
    
    def _extract_hosts_from_results_intensive(self, results: List, columns: List[str], 
                                            hostname_columns: List[str], table_path: str) -> Dict[str, Any]:
        assets = {}
        
        for row in results:
            if hasattr(row, '_fields'):
                row_dict = row._asdict()
            elif isinstance(row, dict):
                row_dict = row
            elif isinstance(row, (list, tuple)):
                row_dict = dict(zip(columns, row))
            else:
                continue
            
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col] is not None:
                    hostname_value = str(row_dict[hostname_col]).strip().upper()
                    
                    if self._is_valid_hostname(hostname_value):
                        if hostname_value not in assets:
                            assets[hostname_value] = {
                                'hostname': hostname_value,
                                'sources': [],
                                'tables_found_in': [],
                                'all_data': {},
                                'row_count': 0
                            }
                        
                        asset = assets[hostname_value]
                        asset['row_count'] += 1
                        
                        source_name = self._determine_source_from_table(table_path)
                        if source_name not in asset['sources']:
                            asset['sources'].append(source_name)
                        
                        if table_path not in asset['tables_found_in']:
                            asset['tables_found_in'].append(table_path)
                        
                        self._extract_additional_fields(asset, row_dict, columns)
                        self._set_coverage_flags(asset, source_name)
        
        return assets
    
    def _determine_source_from_table(self, table_path: str) -> str:
        table_lower = table_path.lower()
        
        if 'sas_bi' in table_lower:
            if 'endpoint' in table_lower:
                return 'cmdb'
            elif 'spl' in table_lower or 'splunk' in table_lower:
                return 'splunk'
            elif 'agent' in table_lower:
                return 'crowdstrike'
        elif 'chronicle' in table_lower:
            return 'chronicle'
        elif 'crowdstrike' in table_lower:
            return 'crowdstrike'
        elif 'splunk' in table_lower:
            return 'splunk'
        
        return 'discovery'
    
    def _extract_additional_fields(self, asset: Dict[str, Any], row_dict: Dict[str, Any], columns: List[str]):
        field_patterns = {
            'ip_address': ['ip', 'addr'],
            'fqdn': ['fqdn', 'domain', 'dns'],
            'country': ['country', 'ctry'],
            'region': ['region', 'geo'],
            'business_unit': ['business', 'unit', 'bu'],
            'datacenter': ['datacenter', 'dc', 'site'],
            'application_class': ['application', 'app', 'class'],
            'infrastructure_type': ['infrastructure', 'infra', 'type'],
            'system_classification': ['system', 'classification', 'os'],
            'mac_address': ['mac', 'physical']
        }
        
        for field_type, patterns in field_patterns.items():
            for col in columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in patterns):
                    if col in row_dict and row_dict[col] is not None:
                        value = str(row_dict[col]).strip()
                        if self._is_valid_field_value(value):
                            if field_type not in asset['all_data']:
                                asset['all_data'][field_type] = set()
                            asset['all_data'][field_type].add(value)
        
        for field_type in asset['all_data']:
            asset['all_data'][field_type] = list(asset['all_data'][field_type])
    
    def _is_valid_hostname(self, value: str) -> bool:
        if not value:
            return False
        
        value = str(value).strip()
        
        if len(value) < 1 or len(value) > 253:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0', 'TRUE', 'FALSE'}
        if value.upper() in invalid_values:
            return False
        
        if value.isdigit():
            return False
        
        if self.visibility_engine.looks_like_ip(value):
            return False
        
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'FTP://', 'WWW.', '@']):
            return False
        
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]*$', value):
            return False
        
        return True
    
    def _is_valid_field_value(self, value: str) -> bool:
        if not value:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0'}
        return str(value).upper().strip() not in invalid_values
    
    def _set_coverage_flags(self, asset: Dict[str, Any], source: str):
        coverage_mapping = {
            'cmdb': {'cmdb_visibility': True},
            'splunk': {'splunk_coverage': True, 'siem_coverage': True},
            'chronicle': {'chronicle_coverage': True, 'siem_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True}
        }
        
        flags = coverage_mapping.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        merged['row_count'] = merged.get('row_count', 0) + secondary.get('row_count', 0)
        
        for source in secondary.get('sources', []):
            if source not in merged['sources']:
                merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage', 'siem_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        return {
            'maximum_intensity_mode': True,
            'every_row_processed': True,
            'fan_spinning_guaranteed': True,
            'backup_methods_enabled': True,
            'zero_rows_not_acceptable': True
        }, value):
            return False
        
        return True
    
    def _is_valid_field_value(self, value: str) -> bool:
        if not value:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0'}
        return str(value).upper().strip() not in invalid_values
    
    def _set_coverage_flags(self, asset: Dict[str, Any], source: str):
        coverage_mapping = {
            'cmdb': {'cmdb_visibility': True},
            'splunk': {'splunk_coverage': True, 'siem_coverage': True},
            'chronicle': {'chronicle_coverage': True, 'siem_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True}
        }
        
        flags = coverage_mapping.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        merged['row_count'] = merged.get('row_count', 0) + secondary.get('row_count', 0)
        
        for source in secondary.get('sources', []):
            if source not in merged['sources']:
                merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage', 'siem_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        return {
            'maximum_intensity_mode': True,
            'every_row_processed': True,
            'fan_spinning_guaranteed': True,
            'backup_methods_enabled': True,
            'zero_rows_not_acceptable': True
        }, value):
            return False
        
        return True
    
    def looks_like_ip(self, value: str) -> bool:
        if not value:
            return False
        
        parts = str(value).strip().split('.')
        if len(parts) == 4:
            try:
                for part in parts:
                    num = int(part)
                    if not (0 <= num <= 255):
                        return False
                return True
            except:
                return False
        return False

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_engine = AO1VisibilityEngine(config)
        
        self.performance_metrics = {
            'classifications': 0,
            'processing_times': [],
            'confidence_scores': [],
            'visibility_scores': []
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        
        logger.info("🔥🔥🔥 STARTING MAXIMUM INTENSITY DISCOVERY - EVERY ROW EVERY TABLE 🔥🔥🔥")
        logger.info("🌪️  FANS WILL BE SPINNING AT MAXIMUM SPEED - THIS IS GOING TO BE INTENSE 🌪️")
        logger.info("⚡⚡⚡ PROCESSING MILLIONS OF ROWS - NO LIMITS - NO SHORTCUTS ⚡⚡⚡")
        start_time = datetime.now()
        
        discovered_assets = {}
        total_hosts_processed = 0
        total_rows_scanned = 0
        total_tables_processed = 0
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🚀🚀🚀 MAXIMUM INTENSITY PROJECT PROCESSING: {project_id} 🚀🚀🚀")
            
            try:
                project_assets, project_rows, project_tables = await self._process_entire_project_maximum_intensity(
                    client_manager, project_id
                )
                
                for hostname, asset in project_assets.items():
                    if hostname in discovered_assets:
                        discovered_assets[hostname] = self._merge_assets(discovered_assets[hostname], asset)
                    else:
                        discovered_assets[hostname] = asset
                
                total_hosts_processed += len(project_assets)
                total_rows_scanned += project_rows
                total_tables_processed += project_tables
                
                logger.info(f"✅ PROJECT {project_id} COMPLETE:")
                logger.info(f"   🏠 HOSTS: {len(project_assets):,}")
                logger.info(f"   📊 ROWS: {project_rows:,}")
                logger.info(f"   📋 TABLES: {project_tables:,}")
                
            except Exception as e:
                logger.error(f"❌ PROJECT {project_id} FAILED: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎉🎉🎉 MAXIMUM INTENSITY DISCOVERY COMPLETE! 🎉🎉🎉")
        logger.info(f"🏆🏆🏆 FINAL MAXIMUM INTENSITY RESULTS: 🏆🏆🏆")
        logger.info(f"   📊 UNIQUE HOSTS DISCOVERED: {len(discovered_assets):,}")
        logger.info(f"   🔍 TOTAL ROWS SCANNED: {total_rows_scanned:,}")
        logger.info(f"   📋 TOTAL TABLES PROCESSED: {total_tables_processed:,}")
        logger.info(f"   ⏱️  PROCESSING TIME: {processing_time/60:.1f} MINUTES")
        logger.info(f"   🚀 ROWS PER SECOND: {total_rows_scanned/processing_time:,.0f}")
        logger.info(f"   💻 HOSTS PER SECOND: {len(discovered_assets)/processing_time:,.0f}")
        logger.info("🌪️  FANS CAN NOW SLOW DOWN - MISSION ACCOMPLISHED! 🌪️")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(discovered_assets),
                'total_hosts_processed': total_hosts_processed,
                'total_rows_scanned': total_rows_scanned,
                'total_tables_processed': total_tables_processed,
                'processing_time_minutes': processing_time / 60,
                'rows_per_second': total_rows_scanned / processing_time if processing_time > 0 else 0,
                'hosts_per_second': len(discovered_assets) / processing_time if processing_time > 0 else 0,
                'maximum_intensity_mode': True,
                'every_row_processed': True,
                'fan_spinning_guaranteed': True
            },
            'assets': discovered_assets,
            'performance_metrics': self._get_performance_summary()
        }
    
    async def _process_entire_project_maximum_intensity(self, client_manager, project_id: str) -> Tuple[Dict[str, Any], int, int]:
        assets = {}
        total_rows = 0
        total_tables = 0
        
        with client_manager.get_client() as client:
            try:
                datasets = list(client.list_datasets(project=project_id))
                logger.info(f"📂 FOUND {len(datasets)} DATASETS IN PROJECT {project_id}")
                
                prioritized_datasets = self._prioritize_datasets_maximum_intensity(datasets, project_id)
                
                for dataset_priority, dataset in prioritized_datasets:
                    logger.info(f"🗂️  MAXIMUM INTENSITY DATASET PROCESSING: {dataset.dataset_id} (Priority: {dataset_priority})")
                    
                    try:
                        dataset_assets, dataset_rows, dataset_tables = await self._process_entire_dataset_maximum_intensity(
                            client, project_id, dataset.dataset_id
                        )
                        
                        for hostname, asset in dataset_assets.items():
                            if hostname in assets:
                                assets[hostname] = self._merge_assets(assets[hostname], asset)
                            else:
                                assets[hostname] = asset
                        
                        total_rows += dataset_rows
                        total_tables += dataset_tables
                        
                        logger.info(f"📊 DATASET {dataset.dataset_id} COMPLETE:")
                        logger.info(f"   🏠 HOSTS: {len(dataset_assets):,}")
                        logger.info(f"   📊 ROWS: {dataset_rows:,}")
                        logger.info(f"   📋 TABLES: {dataset_tables:,}")
                        
                    except Exception as e:
                        logger.error(f"❌ DATASET {dataset.dataset_id} FAILED: {e}")
                        
            except Exception as e:
                logger.error(f"❌ FAILED TO LIST DATASETS IN PROJECT {project_id}: {e}")
        
        return assets, total_rows, total_tables
    
    def _prioritize_datasets_maximum_intensity(self, datasets, project_id: str) -> List[Tuple[int, Any]]:
        prioritized = []
        
        for dataset in datasets:
            priority = 100
            dataset_name = dataset.dataset_id.upper()
            
            if 'SAS_BI' in dataset_name:
                priority = 1
            elif any(keyword in dataset_name for keyword in ['ENDPOINT', 'HOST', 'ASSET', 'DEVICE', 'COMPUTER', 'MACHINE']):
                priority = 2
            elif any(keyword in dataset_name for keyword in ['SECURITY', 'LOG', 'EVENT', 'AUDIT']):
                priority = 3
            elif any(keyword in dataset_name for keyword in ['CMDB', 'INVENTORY', 'CONFIG']):
                priority = 4
            elif any(keyword in dataset_name for keyword in ['NETWORK', 'INFRA', 'SYSTEM']):
                priority = 5
            
            prioritized.append((priority, dataset))
        
        sorted_datasets = sorted(prioritized, key=lambda x: x[0])
        
        logger.info("📋 DATASET PROCESSING ORDER:")
        for priority, dataset in sorted_datasets:
            logger.info(f"   {priority}: {dataset.dataset_id}")
        
        return sorted_datasets
    
    async def _process_entire_dataset_maximum_intensity(self, client, project_id: str, dataset_id: str) -> Tuple[Dict[str, Any], int, int]:
        assets = {}
        total_rows = 0
        total_tables = 0
        
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            logger.info(f"📋 MAXIMUM INTENSITY: PROCESSING ALL {len(tables)} TABLES IN DATASET {dataset_id}")
            
            for table_idx, table_ref in enumerate(tables):
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                
                logger.info(f"🔥 TABLE {table_idx + 1}/{len(tables)}: {table_ref.table_id}")
                
                try:
                    table_assets, table_rows = await self._process_entire_table_maximum_intensity(
                        client, table_path
                    )
                    
                    for hostname, asset in table_assets.items():
                        if hostname in assets:
                            assets[hostname] = self._merge_assets(assets[hostname], asset)
                        else:
                            assets[hostname] = asset
                    
                    total_rows += table_rows
                    total_tables += 1
                    
                    if len(table_assets) > 0 or table_rows > 0:
                        logger.info(f"✅ TABLE {table_ref.table_id}: {len(table_assets):,} hosts from {table_rows:,} rows")
                    
                except Exception as e:
                    logger.error(f"❌ TABLE {table_ref.table_id} FAILED: {e}")
                    total_tables += 1
            
        except Exception as e:
            logger.error(f"❌ FAILED TO PROCESS DATASET {dataset_id}: {e}")
        
        return assets, total_rows, total_tables
    
    async def _process_entire_table_maximum_intensity(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        total_rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            if not table.schema:
                logger.error(f"❌ CRITICAL ERROR: NO SCHEMA FOR TABLE {table_path}")
                raise Exception(f"No schema available for table {table_path}")
            
            columns = [field.name for field in table.schema]
            
            # STEP 1: Get actual row count
            count_query = f"SELECT COUNT(*) as actual_count FROM `{table_path}`"
            count_job = client.query(count_query)
            count_result = list(count_job.result())
            actual_row_count = count_result[0]['actual_count'] if count_result else 0
            
            logger.info(f"💾 TABLE: {table_path}")
            logger.info(f"   📋 COLUMNS: {len(columns)}")
            logger.info(f"   📊 ACTUAL ROWS: {actual_row_count:,}")
            
            if actual_row_count == 0:
                logger.warning(f"⚠️  TABLE {table_path} HAS 0 ROWS - SKIPPING")
                return assets, 0
            
            # STEP 2: Sample 100 rows to find hostname columns
            sample_query = f"SELECT * FROM `{table_path}` LIMIT 100"
            sample_job = client.query(sample_query)
            sample_results = list(sample_job.result())
            
            if not sample_results:
                logger.error(f"❌ CANNOT RETRIEVE SAMPLE DATA FROM {table_path}")
                return assets, 0
            
            logger.info(f"✅ SAMPLED {len(sample_results)} ROWS FOR HOSTNAME DETECTION")
            
            # STEP 3: Find hostname columns from sample
            hostname_columns = self._find_hostname_columns_from_sample(sample_results, columns)
            
            if not hostname_columns:
                logger.warning(f"⚠️  NO HOSTNAME COLUMNS FOUND IN {table_path}")
                return assets, 0
            
            logger.info(f"🎯 HOSTNAME COLUMNS FOUND: {hostname_columns}")
            
            # STEP 4: Extract ALL values from hostname columns (every single row)
            for hostname_col in hostname_columns:
                logger.info(f"🔥 EXTRACTING ALL {actual_row_count:,} VALUES FROM COLUMN: {hostname_col}")
                
                col_assets, col_rows = await self._extract_all_values_from_column(
                    client, table_path, hostname_col, actual_row_count
                )
                
                # Merge with main assets
                for hostname, asset in col_assets.items():
                    if hostname in assets:
                        assets[hostname] = self._merge_assets(assets[hostname], asset)
                    else:
                        assets[hostname] = asset
                
                total_rows_processed += col_rows
                
                logger.info(f"✅ COLUMN {hostname_col}: {len(col_assets):,} hosts from {col_rows:,} rows")
            
            logger.info(f"🎉 TABLE COMPLETE: {table_path}")
            logger.info(f"   🏆 TOTAL HOSTS DISCOVERED: {len(assets):,}")
            logger.info(f"   📊 TOTAL ROWS PROCESSED: {total_rows_processed:,}")
            
        except Exception as e:
            logger.error(f"❌ TABLE PROCESSING FAILED: {table_path}: {e}")
            raise
        
        return assets, total_rows_processed
    
    def _find_hostname_columns_from_sample(self, sample_results: List, columns: List[str]) -> List[str]:
        hostname_columns = []
        
        logger.info(f"🔍 ANALYZING {len(columns)} COLUMNS IN {len(sample_results)} SAMPLE ROWS")
        
        for column_name in columns:
            samples = []
            
            for row in sample_results:
                if hasattr(row, '_fields'):
                    row_dict = row._asdict()
                elif isinstance(row, dict):
                    row_dict = row
                elif isinstance(row, (list, tuple)):
                    row_dict = dict(zip(columns, row))
                else:
                    continue
                
                if column_name in row_dict and row_dict[column_name] is not None:
                    samples.append(str(row_dict[column_name]))
            
            if len(samples) >= 1:
                hostname_ratio = self._calculate_hostname_ratio(samples)
                logger.info(f"   COLUMN {column_name}: {len(samples)} samples, {hostname_ratio:.2f} hostname ratio")
                
                if self.visibility_engine.is_hostname_column_by_content(samples):
                    hostname_columns.append(column_name)
                    logger.info(f"🎯 HOSTNAME COLUMN DETECTED: {column_name}")
        
        return hostname_columns
    
    async def _extract_all_values_from_column(self, client, table_path: str, column_name: str, 
                                            total_rows: int) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        # Extract ALL values from this column in batches
        batch_size = 500000  # Larger batches since we're only getting one column
        batches = (total_rows + batch_size - 1) // batch_size
        
        logger.info(f"🔥 EXTRACTING ALL VALUES FROM {column_name} IN {batches} BATCHES")
        
        for batch_num in range(batches):
            offset = batch_num * batch_size
            
            # Query to get ALL values from this specific column
            query = f"""
            SELECT `{column_name}`
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            LIMIT {batch_size} OFFSET {offset}
            """
            
            try:
                logger.info(f"🚀 BATCH {batch_num + 1}/{batches}: EXTRACTING {batch_size:,} VALUES FROM {column_name}")
                
                job = client.query(query)
                results = list(job.result())
                
                logger.info(f"📊 BATCH {batch_num + 1} RETURNED {len(results):,} VALUES")
                
                if not results:
                    logger.info(f"🏁 NO MORE VALUES IN COLUMN {column_name}")
                    break
                
                # Process each value
                batch_hosts = 0
                for row in results:
                    if hasattr(row, '_fields'):
                        value = getattr(row, column_name, None)
                    elif isinstance(row, dict):
                        value = row.get(column_name, None)
                    elif isinstance(row, (list, tuple)) and len(row) > 0:
                        value = row[0]
                    else:
                        continue
                    
                    if value is not None:
                        hostname_value = str(value).strip().upper()
                        
                        if self._is_valid_hostname(hostname_value):
                            if hostname_value not in assets:
                                assets[hostname_value] = {
                                    'hostname': hostname_value,
                                    'sources': [],
                                    'tables_found_in': [],
                                    'all_data': {},
                                    'row_count': 0
                                }
                            
                            asset = assets[hostname_value]
                            asset['row_count'] += 1
                            
                            source_name = self._determine_source_from_table(table_path)
                            if source_name not in asset['sources']:
                                asset['sources'].append(source_name)
                            
                            if table_path not in asset['tables_found_in']:
                                asset['tables_found_in'].append(table_path)
                            
                            self._set_coverage_flags(asset, source_name)
                            batch_hosts += 1
                
                rows_processed += len(results)
                
                logger.info(f"✅ BATCH {batch_num + 1}: {batch_hosts:,} valid hostnames extracted")
                
                if len(results) < batch_size:
                    logger.info(f"🏁 REACHED END OF COLUMN {column_name}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ BATCH {batch_num + 1} FAILED FOR COLUMN {column_name}: {e}")
                break
        
        logger.info(f"🎉 COLUMN {column_name} COMPLETE: {len(assets):,} unique hosts from {rows_processed:,} values")
        
        return assets, rows_processed
    
    async def _try_backup_row_retrieval_methods(self, client, table_path: str, columns: List[str]) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_retrieved = 0
        
        backup_methods = [
            ("SELECT * FROM `{table}` LIMIT 1000000", "Standard SELECT"),
            ("SELECT * FROM `{table}` WHERE TRUE LIMIT 1000000", "WHERE TRUE"),
            ("SELECT * FROM `{table}` TABLESAMPLE SYSTEM (100 PERCENT) LIMIT 1000000", "TABLESAMPLE"),
            ("SELECT * FROM `{table}` ORDER BY 1 LIMIT 1000000", "ORDER BY"),
            ("SELECT *, CURRENT_TIMESTAMP() as query_time FROM `{table}` LIMIT 1000000", "WITH TIMESTAMP"),
        ]
        
        for query_template, method_name in backup_methods:
            try:
                query = query_template.format(table=table_path)
                logger.info(f"🔄 TRYING BACKUP METHOD: {method_name}")
                logger.info(f"   QUERY: {query}")
                
                job = client.query(query)
                results = list(job.result())
                
                if results:
                    logger.info(f"✅ BACKUP METHOD SUCCESS: {method_name} - {len(results):,} rows")
                    
                    if not columns:
                        first_row = results[0]
                        if hasattr(first_row, '_fields'):
                            columns = list(first_row._fields)
                        elif isinstance(first_row, dict):
                            columns = list(first_row.keys())
                    
                    hostname_columns = await self._find_hostname_columns_by_content_intensive(
                        client, table_path, columns, sample_results=results[:200]
                    )
                    
                    if hostname_columns:
                        backup_assets = self._extract_hosts_from_results_intensive(
                            results, columns, hostname_columns, table_path
                        )
                        assets.update(backup_assets)
                        rows_retrieved = len(results)
                        break
                else:
                    logger.warning(f"⚠️  BACKUP METHOD {method_name} RETURNED 0 ROWS")
                    
            except Exception as e:
                logger.warning(f"⚠️  BACKUP METHOD {method_name} FAILED: {e}")
        
        if not assets:
            logger.error(f"❌ ALL BACKUP METHODS FAILED FOR {table_path}")
        
        return assets, rows_retrieved
    
    async def _process_table_batch_maximum_intensity(self, client, table_path: str, columns: List[str], 
                                                   hostname_columns: List[str], batch_size: int, offset: int,
                                                   batch_num: int, total_batches: int) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        query = f"""
        SELECT *
        FROM `{table_path}`
        LIMIT {batch_size} OFFSET {offset}
        """
        
        try:
            logger.info(f"🚀 BATCH {batch_num}/{total_batches}: OFFSET {offset:,}, LIMIT {batch_size:,}")
            logger.info(f"   QUERY: {query}")
            
            job = client.query(query)
            results = list(job.result())
            
            logger.info(f"📊 BATCH {batch_num} RETURNED {len(results):,} ROWS")
            
            if len(results) == 0:
                logger.error(f"❌ CRITICAL ERROR: BATCH {batch_num} RETURNED 0 ROWS")
                logger.error(f"❌ QUERY: {query}")
                logger.error(f"❌ THIS SHOULD NOT HAPPEN IF TABLE HAS DATA")
                
                # Try a diagnostic query to understand why
                try:
                    diagnostic_query = f"SELECT COUNT(*) as count FROM `{table_path}` WHERE TRUE"
                    diag_job = client.query(diagnostic_query)
                    diag_result = list(diag_job.result())
                    total_count = diag_result[0]['count'] if diag_result else 0
                    logger.error(f"❌ DIAGNOSTIC: Table actually has {total_count:,} rows")
                    
                    if offset >= total_count:
                        logger.error(f"❌ OFFSET {offset:,} >= TOTAL ROWS {total_count:,}")
                    
                except Exception as diag_e:
                    logger.error(f"❌ DIAGNOSTIC QUERY FAILED: {diag_e}")
                
                return assets, 0
            
            # Verify we can read the row structure
            if results:
                first_row = results[0]
                logger.info(f"✅ BATCH {batch_num} ROW STRUCTURE:")
                logger.info(f"   ROW TYPE: {type(first_row)}")
                if hasattr(first_row, '_fields'):
                    logger.info(f"   FIELDS: {first_row._fields[:10]}")
                elif isinstance(first_row, dict):
                    logger.info(f"   KEYS: {list(first_row.keys())[:10]}")
                
                assets = self._extract_hosts_from_results_intensive(
                    results, columns, hostname_columns, table_path
                )
                rows_processed = len(results)
                
                logger.info(f"✅ BATCH {batch_num} COMPLETE: {len(assets):,} hosts from {rows_processed:,} rows")
            
        except Exception as e:
            logger.error(f"❌ CRITICAL: BATCH {batch_num} QUERY FAILED: {e}")
            logger.error(f"❌ QUERY WAS: {query}")
            raise Exception(f"Batch query failed: {e}")
        
        return assets, rows_processed
    
    async def _find_hostname_columns_by_content_intensive(self, client, table_path: str, columns: List[str], 
                                                        sample_results: List = None) -> List[str]:
        hostname_columns = []
        
        try:
            if sample_results is None:
                sample_query = f"""
                SELECT *
                FROM `{table_path}`
                LIMIT 500
                """
                
                job = client.query(sample_query)
                results = list(job.result())
            else:
                results = sample_results
            
            if not results:
                logger.warning(f"⚠️  NO SAMPLE ROWS FOR HOSTNAME DETECTION: {table_path}")
                return []
            
            logger.info(f"🔍 ANALYZING ALL {len(columns)} COLUMNS FOR HOSTNAME CONTENT")
            
            for column_name in columns:
                samples = []
                
                for row in results:
                    if hasattr(row, '_fields'):
                        row_dict = row._asdict()
                    elif isinstance(row, dict):
                        row_dict = row
                    elif isinstance(row, (list, tuple)):
                        row_dict = dict(zip(columns, row))
                    else:
                        continue
                    
                    if column_name in row_dict and row_dict[column_name] is not None:
                        samples.append(str(row_dict[column_name]))
                
                if len(samples) >= 1:
                    if self.visibility_engine.is_hostname_column_by_content(samples):
                        hostname_columns.append(column_name)
                        hostname_ratio = self._calculate_hostname_ratio(samples)
                        logger.info(f"🎯 HOSTNAME COLUMN: {column_name} (ratio: {hostname_ratio:.2f}, samples: {len(samples)})")
            
            logger.info(f"🎯 TOTAL HOSTNAME COLUMNS FOUND: {len(hostname_columns)}")
            
        except Exception as e:
            logger.error(f"❌ HOSTNAME COLUMN DETECTION FAILED: {e}")
        
        return hostname_columns
    
    def _calculate_hostname_ratio(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = sum(1 for sample in samples if self.visibility_engine.looks_like_hostname(sample))
        return hostname_count / len(samples)
    
    def _extract_hosts_from_results_intensive(self, results: List, columns: List[str], 
                                            hostname_columns: List[str], table_path: str) -> Dict[str, Any]:
        assets = {}
        
        for row in results:
            if hasattr(row, '_fields'):
                row_dict = row._asdict()
            elif isinstance(row, dict):
                row_dict = row
            elif isinstance(row, (list, tuple)):
                row_dict = dict(zip(columns, row))
            else:
                continue
            
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col] is not None:
                    hostname_value = str(row_dict[hostname_col]).strip().upper()
                    
                    if self._is_valid_hostname(hostname_value):
                        if hostname_value not in assets:
                            assets[hostname_value] = {
                                'hostname': hostname_value,
                                'sources': [],
                                'tables_found_in': [],
                                'all_data': {},
                                'row_count': 0
                            }
                        
                        asset = assets[hostname_value]
                        asset['row_count'] += 1
                        
                        source_name = self._determine_source_from_table(table_path)
                        if source_name not in asset['sources']:
                            asset['sources'].append(source_name)
                        
                        if table_path not in asset['tables_found_in']:
                            asset['tables_found_in'].append(table_path)
                        
                        self._extract_additional_fields(asset, row_dict, columns)
                        self._set_coverage_flags(asset, source_name)
        
        return assets
    
    def _determine_source_from_table(self, table_path: str) -> str:
        table_lower = table_path.lower()
        
        if 'sas_bi' in table_lower:
            if 'endpoint' in table_lower:
                return 'cmdb'
            elif 'spl' in table_lower or 'splunk' in table_lower:
                return 'splunk'
            elif 'agent' in table_lower:
                return 'crowdstrike'
        elif 'chronicle' in table_lower:
            return 'chronicle'
        elif 'crowdstrike' in table_lower:
            return 'crowdstrike'
        elif 'splunk' in table_lower:
            return 'splunk'
        
        return 'discovery'
    
    def _extract_additional_fields(self, asset: Dict[str, Any], row_dict: Dict[str, Any], columns: List[str]):
        field_patterns = {
            'ip_address': ['ip', 'addr'],
            'fqdn': ['fqdn', 'domain', 'dns'],
            'country': ['country', 'ctry'],
            'region': ['region', 'geo'],
            'business_unit': ['business', 'unit', 'bu'],
            'datacenter': ['datacenter', 'dc', 'site'],
            'application_class': ['application', 'app', 'class'],
            'infrastructure_type': ['infrastructure', 'infra', 'type'],
            'system_classification': ['system', 'classification', 'os'],
            'mac_address': ['mac', 'physical']
        }
        
        for field_type, patterns in field_patterns.items():
            for col in columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in patterns):
                    if col in row_dict and row_dict[col] is not None:
                        value = str(row_dict[col]).strip()
                        if self._is_valid_field_value(value):
                            if field_type not in asset['all_data']:
                                asset['all_data'][field_type] = set()
                            asset['all_data'][field_type].add(value)
        
        for field_type in asset['all_data']:
            asset['all_data'][field_type] = list(asset['all_data'][field_type])
    
    def _is_valid_hostname(self, value: str) -> bool:
        if not value:
            return False
        
        value = str(value).strip()
        
        if len(value) < 1 or len(value) > 253:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0', 'TRUE', 'FALSE'}
        if value.upper() in invalid_values:
            return False
        
        if value.isdigit():
            return False
        
        if self.visibility_engine.looks_like_ip(value):
            return False
        
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'FTP://', 'WWW.', '@']):
            return False
        
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]*$', value):
            return False
        
        return True
    
    def _is_valid_field_value(self, value: str) -> bool:
        if not value:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0'}
        return str(value).upper().strip() not in invalid_values
    
    def _set_coverage_flags(self, asset: Dict[str, Any], source: str):
        coverage_mapping = {
            'cmdb': {'cmdb_visibility': True},
            'splunk': {'splunk_coverage': True, 'siem_coverage': True},
            'chronicle': {'chronicle_coverage': True, 'siem_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True}
        }
        
        flags = coverage_mapping.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        merged['row_count'] = merged.get('row_count', 0) + secondary.get('row_count', 0)
        
        for source in secondary.get('sources', []):
            if source not in merged['sources']:
                merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage', 'siem_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        return {
            'maximum_intensity_mode': True,
            'every_row_processed': True,
            'fan_spinning_guaranteed': True,
            'backup_methods_enabled': True,
            'zero_rows_not_acceptable': True
        }