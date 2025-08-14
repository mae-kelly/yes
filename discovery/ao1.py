# discovery/ao1.py

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartKeywordProcessor:
    def __init__(self):
        self.keyword_patterns = {
            'host': ['host'],
            'hostname': ['hostname', 'computer', 'machine', 'device', 'endpoint', 'asset', 'server', 'workstation'],
            'ip_address': ['ip', 'addr', 'address'],
            'fqdn': ['fqdn', 'domain', 'dns'],
            'mac_address': ['mac', 'physical'],
            'system': ['system', 'os', 'platform'],
            'location': ['location', 'site', 'datacenter', 'region'],
            'owner': ['owner', 'user', 'contact'],
            'environment': ['env', 'environment', 'stage']
        }
        
        self.stats = {
            'keywords_found': {},
            'columns_processed': 0,
            'values_extracted': 0,
            'tables_scanned': 0
        }
    
    def find_keyword_columns(self, columns: List[str]) -> Dict[str, List[str]]:
        keyword_columns = {}
        
        for keyword, patterns in self.keyword_patterns.items():
            matching_columns = []
            
            for column in columns:
                column_lower = column.lower()
                
                if keyword == 'host':
                    if 'host' in column_lower and not any(other in column_lower for other in ['hostname', 'ghost']):
                        matching_columns.append(column)
                else:
                    if any(pattern in column_lower for pattern in patterns):
                        matching_columns.append(column)
            
            if matching_columns:
                keyword_columns[keyword] = matching_columns
                self.stats['keywords_found'][keyword] = len(matching_columns)
        
        self.stats['columns_processed'] += len(columns)
        return keyword_columns

class AdvancedAssetExtractor:
    def __init__(self, keyword_processor: SmartKeywordProcessor):
        self.processor = keyword_processor
        self.extraction_stats = {
            'batches_processed': 0,
            'total_values': 0,
            'unique_assets': 0,
            'extraction_errors': 0
        }
    
    async def extract_all_column_values(self, client, table_path: str, column_name: str, keyword_type: str) -> Dict[str, Any]:
        assets = {}
        total_extracted = 0
        
        count_query = f"SELECT COUNT(*) as total FROM `{table_path}` WHERE `{column_name}` IS NOT NULL"
        count_job = client.query(count_query)
        count_result = list(count_job.result())
        total_values = count_result[0]['total'] if count_result else 0
        
        if total_values == 0:
            return assets
        
        logger.info(f"🔥 EXTRACTING {total_values:,} VALUES FROM {column_name} ({keyword_type})")
        
        batch_size = 2000000
        offset = 0
        
        while True:
            extraction_query = f"""
            SELECT `{column_name}` as value
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            AND `{column_name}` != ''
            LIMIT {batch_size} OFFSET {offset}
            """
            
            try:
                job = client.query(extraction_query)
                results = list(job.result())
                
                if not results:
                    break
                
                batch_assets = self._process_value_batch(results, table_path, column_name, keyword_type)
                
                for asset_id, asset_data in batch_assets.items():
                    if asset_id in assets:
                        assets[asset_id] = self._combine_asset_data(assets[asset_id], asset_data)
                    else:
                        assets[asset_id] = asset_data
                
                total_extracted += len(results)
                offset += batch_size
                
                logger.info(f"📊 EXTRACTED {total_extracted:,}/{total_values:,} values")
                
                if len(results) < batch_size:
                    break
                    
            except Exception as e:
                logger.error(f"❌ EXTRACTION FAILED: {e}")
                self.extraction_stats['extraction_errors'] += 1
                break
        
        self.extraction_stats['total_values'] += total_extracted
        self.extraction_stats['unique_assets'] += len(assets)
        
        return assets
    
    def _process_value_batch(self, results: List, table_path: str, column_name: str, keyword_type: str) -> Dict[str, Any]:
        batch_assets = {}
        
        for row in results:
            value = None
            
            if hasattr(row, 'value'):
                value = row.value
            elif isinstance(row, dict):
                value = row.get('value')
            elif isinstance(row, (list, tuple)) and len(row) > 0:
                value = row[0]
            
            if value is not None:
                clean_value = str(value).strip()
                
                if self._is_valid_asset_value(clean_value):
                    asset_id = clean_value.upper()
                    
                    if asset_id not in batch_assets:
                        batch_assets[asset_id] = self._create_asset_record(asset_id, keyword_type)
                    
                    asset = batch_assets[asset_id]
                    asset['occurrence_count'] += 1
                    asset['source_tables'].add(table_path)
                    asset['source_columns'].add(f"{table_path}:{column_name}")
                    
                    self._update_asset_attributes(asset, keyword_type, clean_value, table_path)
        
        for asset in batch_assets.values():
            asset['source_tables'] = list(asset['source_tables'])
            asset['source_columns'] = list(asset['source_columns'])
        
        return batch_assets
    
    def _create_asset_record(self, asset_id: str, keyword_type: str) -> Dict[str, Any]:
        return {
            'asset_id': asset_id,
            'primary_value': asset_id,
            'keyword_type': keyword_type,
            'occurrence_count': 0,
            'source_tables': set(),
            'source_columns': set(),
            'attributes': {},
            'coverage_flags': {},
            'discovery_metadata': {
                'discovered_at': datetime.now().isoformat(),
                'discovery_method': 'keyword_extraction'
            }
        }
    
    def _update_asset_attributes(self, asset: Dict[str, Any], keyword_type: str, value: str, table_path: str):
        if keyword_type not in asset['attributes']:
            asset['attributes'][keyword_type] = set()
        
        asset['attributes'][keyword_type].add(value)
        
        source_type = self._determine_source_type(table_path)
        if source_type:
            asset['coverage_flags'][f"{source_type}_coverage"] = True
    
    def _determine_source_type(self, table_path: str) -> str:
        path_lower = table_path.lower()
        
        if 'sas_bi' in path_lower:
            if 'endpoint' in path_lower:
                return 'cmdb'
            elif 'splunk' in path_lower or 'spl' in path_lower:
                return 'splunk'
            elif 'agent' in path_lower:
                return 'edr'
        elif 'chronicle' in path_lower:
            return 'chronicle'
        elif 'security' in path_lower:
            return 'security'
        
        return 'discovery'
    
    def _is_valid_asset_value(self, value: str) -> bool:
        if not value or len(value) < 1 or len(value) > 1000:
            return False
        
        if value.upper() in {'NULL', 'NONE', '', '-', '0', 'N/A'}:
            return False
        
        return True
    
    def _combine_asset_data(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        combined = primary.copy()
        
        combined['occurrence_count'] += secondary['occurrence_count']
        combined['source_tables'].extend([t for t in secondary['source_tables'] if t not in combined['source_tables']])
        combined['source_columns'].extend([c for c in secondary['source_columns'] if c not in combined['source_columns']])
        
        for attr_type, values in secondary['attributes'].items():
            if attr_type not in combined['attributes']:
                combined['attributes'][attr_type] = set()
            combined['attributes'][attr_type].update(values)
        
        combined['coverage_flags'].update(secondary['coverage_flags'])
        
        return combined

class ComprehensiveDiscoveryOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.processor = SmartKeywordProcessor()
        self.extractor = AdvancedAssetExtractor(self.processor)
        
        self.orchestration_stats = {
            'projects_processed': 0,
            'datasets_processed': 0,
            'tables_processed': 0,
            'total_assets_discovered': 0,
            'processing_start_time': None,
            'processing_errors': 0
        }
    
    async def execute_comprehensive_discovery(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        self.orchestration_stats['processing_start_time'] = datetime.now()
        
        logger.info("🚀 COMPREHENSIVE KEYWORD-BASED DISCOVERY INITIATED")
        logger.info("🎯 PROCESSING ALL PROJECTS, DATASETS, AND TABLES")
        logger.info("⚡ EXTRACTING ALL VALUES FROM KEYWORD COLUMNS")
        
        all_discovered_assets = {}
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🎯 PROJECT: {project_id}")
            
            try:
                project_assets = await self._process_complete_project(client_manager, project_id)
                
                for asset_id, asset_data in project_assets.items():
                    if asset_id in all_discovered_assets:
                        all_discovered_assets[asset_id] = self.extractor._combine_asset_data(
                            all_discovered_assets[asset_id], asset_data
                        )
                    else:
                        all_discovered_assets[asset_id] = asset_data
                
                self.orchestration_stats['projects_processed'] += 1
                logger.info(f"✅ PROJECT {project_id}: {len(project_assets):,} assets")
                
            except Exception as e:
                logger.error(f"❌ PROJECT {project_id} FAILED: {e}")
                self.orchestration_stats['processing_errors'] += 1
        
        self._finalize_asset_attributes(all_discovered_assets)
        
        processing_time = (datetime.now() - self.orchestration_stats['processing_start_time']).total_seconds()
        
        logger.info("🎉 COMPREHENSIVE DISCOVERY COMPLETE")
        logger.info(f"📊 TOTAL ASSETS: {len(all_discovered_assets):,}")
        logger.info(f"📋 TABLES PROCESSED: {self.orchestration_stats['tables_processed']:,}")
        logger.info(f"⏱️ PROCESSING TIME: {processing_time/60:.1f} minutes")
        
        return {
            'discovery_stats': {
                'total_assets': len(all_discovered_assets),
                'tables_processed': self.orchestration_stats['tables_processed'],
                'processing_time_minutes': processing_time / 60,
                'keyword_discovery_mode': True,
                'comprehensive_extraction': True
            },
            'assets': all_discovered_assets,
            'processing_statistics': {
                'orchestration': self.orchestration_stats,
                'keyword_processing': self.processor.stats,
                'extraction': self.extractor.extraction_stats
            }
        }
    
    async def _process_complete_project(self, client_manager, project_id: str) -> Dict[str, Any]:
        project_assets = {}
        
        with client_manager.get_client() as client:
            try:
                datasets = list(client.list_datasets(project=project_id))
                
                prioritized_datasets = self._prioritize_datasets(datasets)
                
                for priority, dataset in prioritized_datasets:
                    try:
                        dataset_assets = await self._process_complete_dataset(client, project_id, dataset.dataset_id)
                        
                        for asset_id, asset_data in dataset_assets.items():
                            if asset_id in project_assets:
                                project_assets[asset_id] = self.extractor._combine_asset_data(
                                    project_assets[asset_id], asset_data
                                )
                            else:
                                project_assets[asset_id] = asset_data
                        
                        self.orchestration_stats['datasets_processed'] += 1
                        
                    except Exception as e:
                        logger.error(f"❌ DATASET {dataset.dataset_id} FAILED: {e}")
                        self.orchestration_stats['processing_errors'] += 1
                        
            except Exception as e:
                logger.error(f"❌ PROJECT LISTING FAILED: {e}")
                self.orchestration_stats['processing_errors'] += 1
        
        return project_assets
    
    async def _process_complete_dataset(self, client, project_id: str, dataset_id: str) -> Dict[str, Any]:
        dataset_assets = {}
        
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            for table_ref in tables:
                table_path = f"{project_id}.{dataset_id}.{table_ref.table_id}"
                
                try:
                    table_assets = await self._process_complete_table(client, table_path)
                    
                    for asset_id, asset_data in table_assets.items():
                        if asset_id in dataset_assets:
                            dataset_assets[asset_id] = self.extractor._combine_asset_data(
                                dataset_assets[asset_id], asset_data
                            )
                        else:
                            dataset_assets[asset_id] = asset_data
                    
                    self.orchestration_stats['tables_processed'] += 1
                    
                    if len(table_assets) > 0:
                        logger.info(f"🎯 {table_ref.table_id}: {len(table_assets):,} assets")
                    
                except Exception as e:
                    logger.error(f"❌ TABLE {table_ref.table_id} FAILED: {e}")
                    self.orchestration_stats['processing_errors'] += 1
            
        except Exception as e:
            logger.error(f"❌ DATASET PROCESSING FAILED: {e}")
            self.orchestration_stats['processing_errors'] += 1
        
        return dataset_assets
    
    async def _process_complete_table(self, client, table_path: str) -> Dict[str, Any]:
        table_assets = {}
        
        try:
            table = client.get_table(table_path)
            if not table.schema:
                return table_assets
            
            columns = [field.name for field in table.schema]
            keyword_columns = self.processor.find_keyword_columns(columns)
            
            if not keyword_columns:
                return table_assets
            
            logger.info(f"🔥 {table_path}: Found {sum(len(cols) for cols in keyword_columns.values())} keyword columns")
            
            for keyword_type, matching_columns in keyword_columns.items():
                for column_name in matching_columns:
                    try:
                        column_assets = await self.extractor.extract_all_column_values(
                            client, table_path, column_name, keyword_type
                        )
                        
                        for asset_id, asset_data in column_assets.items():
                            if asset_id in table_assets:
                                table_assets[asset_id] = self.extractor._combine_asset_data(
                                    table_assets[asset_id], asset_data
                                )
                            else:
                                table_assets[asset_id] = asset_data
                        
                    except Exception as e:
                        logger.error(f"❌ COLUMN {column_name} EXTRACTION FAILED: {e}")
                        self.orchestration_stats['processing_errors'] += 1
            
        except Exception as e:
            logger.error(f"❌ TABLE SCHEMA ACCESS FAILED: {e}")
            self.orchestration_stats['processing_errors'] += 1
        
        return table_assets
    
    def _prioritize_datasets(self, datasets) -> List[Tuple[int, Any]]:
        prioritized = []
        
        for dataset in datasets:
            priority = 100
            name = dataset.dataset_id.upper()
            
            if 'SAS_BI' in name:
                priority = 1
            elif any(keyword in name for keyword in ['HOST', 'ENDPOINT', 'ASSET']):
                priority = 2
            elif any(keyword in name for keyword in ['SECURITY', 'LOG']):
                priority = 3
            elif 'CMDB' in name:
                priority = 4
            
            prioritized.append((priority, dataset))
        
        return sorted(prioritized, key=lambda x: x[0])
    
    def _finalize_asset_attributes(self, assets: Dict[str, Any]):
        for asset in assets.values():
            for attr_type, value_set in asset['attributes'].items():
                asset['attributes'][attr_type] = list(value_set)
        
        self.orchestration_stats['total_assets_discovered'] = len(assets)

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.orchestrator = ComprehensiveDiscoveryOrchestrator(config)
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        return await self.orchestrator.execute_comprehensive_discovery(client_managers)