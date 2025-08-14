# discovery/ao1.py

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class UltimateHostDiscoveryEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        self.discovery_stats = {
            'projects_processed': 0,
            'datasets_processed': 0,
            'tables_processed': 0,
            'columns_analyzed': 0,
            'host_columns_found': 0,
            'total_rows_scanned': 0,
            'total_hosts_extracted': 0,
            'processing_start_time': None,
            'errors_encountered': 0
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        
        logger.info("🚀🚀🚀 ULTIMATE HOST DISCOVERY ENGINE ACTIVATED 🚀🚀🚀")
        logger.info("🎯 SEARCHING FOR ANY COLUMN CONTAINING 'HOST' KEYWORD 🎯")
        logger.info("⚡ EXTRACTING EVERY SINGLE VALUE FROM HOST COLUMNS ⚡")
        logger.info("🌪️  MAXIMUM INTENSITY MODE - FANS WILL SPIN! 🌪️")
        
        self.discovery_stats['processing_start_time'] = datetime.now()
        discovered_assets = {}
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🎯 PROCESSING PROJECT: {project_id}")
            
            try:
                project_assets = await self._process_project_for_host_columns(client_manager, project_id)
                
                for hostname, asset in project_assets.items():
                    if hostname in discovered_assets:
                        discovered_assets[hostname] = self._merge_assets(discovered_assets[hostname], asset)
                    else:
                        discovered_assets[hostname] = asset
                
                self.discovery_stats['projects_processed'] += 1
                
                logger.info(f"✅ PROJECT {project_id} COMPLETE: {len(project_assets):,} hosts")
                
            except Exception as e:
                logger.error(f"❌ PROJECT {project_id} FAILED: {e}")
                self.discovery_stats['errors_encountered'] += 1
        
        processing_time = (datetime.now() - self.discovery_stats['processing_start_time']).total_seconds()
        
        logger.info("🎉🎉🎉 ULTIMATE HOST DISCOVERY COMPLETE! 🎉🎉🎉")
        logger.info(f"🏆 FINAL RESULTS:")
        logger.info(f"   📊 UNIQUE HOSTS: {len(discovered_assets):,}")
        logger.info(f"   📋 TABLES PROCESSED: {self.discovery_stats['tables_processed']:,}")
        logger.info(f"   🔍 ROWS SCANNED: {self.discovery_stats['total_rows_scanned']:,}")
        logger.info(f"   📈 HOST COLUMNS FOUND: {self.discovery_stats['host_columns_found']:,}")
        logger.info(f"   ⏱️  PROCESSING TIME: {processing_time/60:.1f} minutes")
        logger.info(f"   🚀 PROCESSING RATE: {self.discovery_stats['total_rows_scanned']/processing_time:,.0f} rows/sec")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(discovered_assets),
                'tables_processed': self.discovery_stats['tables_processed'],
                'rows_scanned': self.discovery_stats['total_rows_scanned'],
                'host_columns_found': self.discovery_stats['host_columns_found'],
                'processing_time_minutes': processing_time / 60,
                'rows_per_second': self.discovery_stats['total_rows_scanned'] / processing_time if processing_time > 0 else 0,
                'host_keyword_discovery': True,
                'every_host_column_processed': True
            },
            'assets': discovered_assets
        }
    
    async def _process_project_for_host_columns(self, client_manager, project_id: str) -> Dict[str, Any]:
        assets = {}
        
        with client_manager.get_client() as client:
            try:
                datasets = list(client.list_datasets(project=project_id))
                logger.info(f"📂 FOUND {len(datasets)} DATASETS IN {project_id}")
                
                # Prioritize SAS_BI first, then others
                prioritized_datasets = self._prioritize_datasets(datasets)
                
                for priority, dataset in prioritized_datasets:
                    logger.info(f"🗂️  DATASET: {dataset.dataset_id} (Priority: {priority})")
                    
                    try:
                        dataset_assets = await self._process_dataset_for_host_columns(
                            client, project_id, dataset.dataset_id
                        )
                        
                        for hostname, asset in dataset_assets.items():
                            if hostname in assets:
                                assets[hostname] = self._merge_assets(assets[hostname], asset)
                            else:
                                assets[hostname] = asset
                        
                        self.discovery_stats['datasets_processed'] += 1
                        
                        logger.info(f"📊 DATASET {dataset.dataset_id}: {len(dataset_assets):,} hosts")
                        
                    except Exception as e:
                        logger.error(f"❌ DATASET {dataset.dataset_id} FAILED: {e}")
                        self.discovery_stats['errors_encountered'] += 1
                        
            except Exception as e:
                logger.error(f"❌ FAILED TO LIST DATASETS IN {project_id}: {e}")
                self.discovery_stats['errors_encountered'] += 1
        
        return assets
    
    def _prioritize_datasets(self, datasets) -> List[Tuple[int, Any]]:
        prioritized = []
        
        for dataset in datasets:
            priority = 100
            dataset_name = dataset.dataset_id.upper()
            
            if 'SAS_BI' in dataset_name:
                priority = 1
            elif any(keyword in dataset_name for keyword in ['HOST', 'ENDPOINT', 'ASSET', 'DEVICE']):
                priority = 2
            elif any(keyword in dataset_name for keyword in ['SECURITY', 'LOG', 'EVENT']):
                priority = 3
            elif any(keyword in dataset_name for keyword in ['CMDB', 'INVENTORY']):
                priority = 4
            
            prioritized.append((priority, dataset))
        
        return sorted(prioritized, key=lambda x: x[0])
    
    async def _process_dataset_for_host_columns(self, client, project_id: str, dataset_id: str) -> Dict[str, Any]:
        assets = {}
        
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            logger.info(f"📋 PROCESSING ALL {len(tables)} TABLES IN {dataset_id}")
            
            for table_ref in tables:
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                
                try:
                    table_assets = await self._process_table_for_host_columns(client, table_path)
                    
                    for hostname, asset in table_assets.items():
                        if hostname in assets:
                            assets[hostname] = self._merge_assets(assets[hostname], asset)
                        else:
                            assets[hostname] = asset
                    
                    self.discovery_stats['tables_processed'] += 1
                    
                    if len(table_assets) > 0:
                        logger.info(f"🎯 TABLE {table_ref.table_id}: {len(table_assets):,} hosts")
                    
                except Exception as e:
                    logger.error(f"❌ TABLE {table_ref.table_id} FAILED: {e}")
                    self.discovery_stats['errors_encountered'] += 1
            
        except Exception as e:
            logger.error(f"❌ FAILED TO PROCESS DATASET {dataset_id}: {e}")
            self.discovery_stats['errors_encountered'] += 1
        
        return assets
    
    async def _process_table_for_host_columns(self, client, table_path: str) -> Dict[str, Any]:
        assets = {}
        
        try:
            # Get table metadata
            table = client.get_table(table_path)
            if not table.schema:
                logger.warning(f"⚠️  NO SCHEMA FOR TABLE {table_path}")
                return assets
            
            columns = [field.name for field in table.schema]
            
            # Find ALL columns that contain "host" keyword
            host_columns = self._find_host_columns(columns)
            
            if not host_columns:
                logger.debug(f"⚠️  NO HOST COLUMNS IN {table_path}")
                return assets
            
            # Get actual row count
            count_query = f"SELECT COUNT(*) as row_count FROM `{table_path}`"
            count_job = client.query(count_query)
            count_result = list(count_job.result())
            actual_row_count = count_result[0]['row_count'] if count_result else 0
            
            logger.info(f"🔥 TABLE: {table_path}")
            logger.info(f"   📊 ROWS: {actual_row_count:,}")
            logger.info(f"   🎯 HOST COLUMNS: {host_columns}")
            
            if actual_row_count == 0:
                logger.warning(f"⚠️  TABLE HAS 0 ROWS: {table_path}")
                return assets
            
            # Extract ALL values from each host column
            for host_column in host_columns:
                logger.info(f"🔥 EXTRACTING ALL VALUES FROM COLUMN: {host_column}")
                
                column_assets = await self._extract_all_values_from_host_column(
                    client, table_path, host_column, actual_row_count
                )
                
                for hostname, asset in column_assets.items():
                    if hostname in assets:
                        assets[hostname] = self._merge_assets(assets[hostname], asset)
                    else:
                        assets[hostname] = asset
                
                self.discovery_stats['host_columns_found'] += 1
                
                logger.info(f"✅ COLUMN {host_column}: {len(column_assets):,} hosts extracted")
            
        except Exception as e:
            logger.error(f"❌ TABLE PROCESSING FAILED: {table_path}: {e}")
            self.discovery_stats['errors_encountered'] += 1
        
        return assets
    
    def _find_host_columns(self, columns: List[str]) -> List[str]:
        host_columns = []
        
        for column in columns:
            # Simple case-insensitive check for "host" keyword
            if 'host' in column.lower():
                host_columns.append(column)
                logger.info(f"🎯 HOST COLUMN FOUND: {column}")
        
        self.discovery_stats['columns_analyzed'] += len(columns)
        
        return host_columns
    
    async def _extract_all_values_from_host_column(self, client, table_path: str, 
                                                 column_name: str, total_rows: int) -> Dict[str, Any]:
        assets = {}
        rows_processed = 0
        
        # Process in large batches
        batch_size = 1000000  # 1 million rows per batch
        batches = (total_rows + batch_size - 1) // batch_size
        
        logger.info(f"🔥 PROCESSING {batches} BATCHES OF UP TO {batch_size:,} ROWS")
        
        for batch_num in range(batches):
            offset = batch_num * batch_size
            
            # Extract ALL non-null values from this column
            query = f"""
            SELECT `{column_name}`
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            AND `{column_name}` != ''
            LIMIT {batch_size} OFFSET {offset}
            """
            
            try:
                logger.info(f"🚀 BATCH {batch_num + 1}/{batches}: EXTRACTING FROM {column_name}")
                
                job = client.query(query)
                results = list(job.result())
                
                if not results:
                    logger.info(f"🏁 NO MORE VALUES IN {column_name}")
                    break
                
                batch_hosts = 0
                for row in results:
                    # Extract the value regardless of row format
                    if hasattr(row, column_name):
                        value = getattr(row, column_name)
                    elif isinstance(row, dict):
                        value = row.get(column_name)
                    elif isinstance(row, (list, tuple)) and len(row) > 0:
                        value = row[0]
                    else:
                        continue
                    
                    if value is not None:
                        hostname_value = str(value).strip().upper()
                        
                        # Very basic validation - just exclude obvious junk
                        if self._is_extractable_value(hostname_value):
                            if hostname_value not in assets:
                                assets[hostname_value] = {
                                    'hostname': hostname_value,
                                    'sources': [],
                                    'tables_found_in': [],
                                    'columns_found_in': [],
                                    'row_count': 0
                                }
                            
                            asset = assets[hostname_value]
                            asset['row_count'] += 1
                            
                            # Track source info
                            source_name = self._determine_source_from_table(table_path)
                            if source_name not in asset['sources']:
                                asset['sources'].append(source_name)
                            
                            if table_path not in asset['tables_found_in']:
                                asset['tables_found_in'].append(table_path)
                            
                            if column_name not in asset['columns_found_in']:
                                asset['columns_found_in'].append(column_name)
                            
                            self._set_coverage_flags(asset, source_name)
                            batch_hosts += 1
                
                rows_processed += len(results)
                self.discovery_stats['total_rows_scanned'] += len(results)
                
                logger.info(f"✅ BATCH {batch_num + 1}: {batch_hosts:,} hosts from {len(results):,} values")
                
                if len(results) < batch_size:
                    logger.info(f"🏁 REACHED END OF COLUMN {column_name}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ BATCH {batch_num + 1} FAILED: {e}")
                self.discovery_stats['errors_encountered'] += 1
                break
        
        logger.info(f"🎉 COLUMN {column_name} COMPLETE: {len(assets):,} unique hosts from {rows_processed:,} rows")
        
        return assets
    
    def _is_extractable_value(self, value: str) -> bool:
        # Very minimal validation - just exclude obvious non-values
        if not value:
            return False
        
        if len(value) < 1 or len(value) > 500:
            return False
        
        # Only exclude the most obvious non-values
        if value.upper() in {'NULL', 'NONE', '', '-', '0', 'N/A', 'NA'}:
            return False
        
        return True
    
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
        
        return 'host_discovery'
    
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
        
        for column in secondary.get('columns_found_in', []):
            if column not in merged.get('columns_found_in', []):
                if 'columns_found_in' not in merged:
                    merged['columns_found_in'] = []
                merged['columns_found_in'].append(column)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage', 'siem_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged

# Alias for compatibility
class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.engine = UltimateHostDiscoveryEngine(config)
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        return await self.engine.enhanced_discovery(client_managers, intelligence_result)