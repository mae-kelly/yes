# discovery/core.py

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from core.types import HyperAsset, QuantumDiscovery

logger = logging.getLogger(__name__)

class QuantumHyperDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        
        self.discovered_assets = {}
        self.processing_stats = {
            'datasets_scanned': 0,
            'tables_analyzed': 0,
            'assets_discovered': 0,
            'processing_errors': 0,
            'start_time': datetime.now()
        }
    
    async def discover_assets_quantum_intensively(self, client_managers: Dict[str, Any]) -> QuantumDiscovery:
        logger.info("Starting quantum hyper discovery")
        
        quantum_discovery = QuantumDiscovery()
        
        for project_id, client_manager in client_managers.items():
            try:
                with client_manager.get_client() as client:
                    datasets = list(client.list_datasets(project=project_id))
                    self.processing_stats['datasets_scanned'] += len(datasets)
                    
                    for dataset in datasets:
                        try:
                            tables = list(client.list_tables(dataset))
                            self.processing_stats['tables_analyzed'] += len(tables)
                            
                            for table_ref in tables:
                                try:
                                    await self._analyze_table_for_assets(
                                        client, f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                                    )
                                except Exception as e:
                                    logger.warning(f"Table analysis failed: {e}")
                                    self.processing_stats['processing_errors'] += 1
                        
                        except Exception as e:
                            logger.warning(f"Dataset analysis failed: {e}")
                            self.processing_stats['processing_errors'] += 1
            
            except Exception as e:
                logger.error(f"Project processing failed for {project_id}: {e}")
                self.processing_stats['processing_errors'] += 1
        
        for asset_id, asset_data in self.discovered_assets.items():
            hyper_asset = self._create_hyper_asset(asset_id, asset_data)
            quantum_discovery.hyper_assets[asset_id] = hyper_asset
        
        quantum_discovery.processing_metadata = self.processing_stats
        self.processing_stats['assets_discovered'] = len(quantum_discovery.hyper_assets)
        
        logger.info(f"Quantum discovery completed: {len(quantum_discovery.hyper_assets)} assets")
        return quantum_discovery
    
    async def _analyze_table_for_assets(self, client, table_path: str):
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return
            
            columns = [field.name for field in table.schema]
            hostname_columns = [col for col in columns if 'hostname' in col.lower() or 'host' in col.lower()]
            
            if hostname_columns:
                query = f"""
                SELECT {', '.join([f'`{col}`' for col in columns])}
                FROM `{table_path}`
                WHERE `{hostname_columns[0]}` IS NOT NULL
                LIMIT 1000
                """
                
                job = client.query(query)
                results = list(job.result())
                
                for row in results:
                    row_data = dict(zip(columns, row))
                    hostname = row_data.get(hostname_columns[0])
                    
                    if hostname and str(hostname).strip():
                        asset_id = str(hostname).strip().upper()
                        
                        if asset_id not in self.discovered_assets:
                            self.discovered_assets[asset_id] = {
                                'hostname': asset_id,
                                'all_data': defaultdict(list),
                                'source_tables': set(),
                                'coverage_flags': {}
                            }
                        
                        asset = self.discovered_assets[asset_id]
                        
                        for col_name, value in row_data.items():
                            if value and str(value).strip():
                                asset['all_data'][col_name].append(str(value).strip())
                        
                        asset['source_tables'].add(table_path)
                        asset['coverage_flags'].update(self._determine_coverage_flags(table_path))
        
        except Exception as e:
            logger.warning(f"Table analysis failed for {table_path}: {e}")
    
    def _determine_coverage_flags(self, table_path: str) -> Dict[str, bool]:
        table_lower = table_path.lower()
        
        flags = {}
        if 'chronicle' in table_lower:
            flags['chronicle_coverage'] = True
        if 'crowdstrike' in table_lower:
            flags['crowdstrike_coverage'] = True
        if 'cmdb' in table_lower:
            flags['cmdb_visibility'] = True
        if 'splunk' in table_lower:
            flags['splunk_coverage'] = True
        if 'tanium' in table_lower:
            flags['tanium_coverage'] = True
        if 'dlp' in table_lower:
            flags['dlp_coverage'] = True
        
        return flags
    
    def _create_hyper_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> HyperAsset:
        all_data = asset_data.get('all_data', {})
        coverage_flags = asset_data.get('coverage_flags', {})
        
        def get_first_value(key: str) -> str:
            values = all_data.get(key, [])
            return values[0] if values else ""
        
        hyper_asset = HyperAsset(
            id=asset_id,
            hostname=asset_data.get('hostname', ''),
            primary_identity=asset_data.get('hostname', ''),
            
            ip=get_first_value('ip_address') or get_first_value('ip'),
            fqdn=get_first_value('fqdn') or get_first_value('dns_name'),
            mac=get_first_value('mac_address') or get_first_value('mac'),
            
            infrastructure_type=get_first_value('infrastructure_type'),
            system_classification=get_first_value('system_classification'),
            business_unit=get_first_value('business_unit'),
            region=get_first_value('region') or get_first_value('global_region'),
            country=get_first_value('country'),
            datacenter=get_first_value('datacenter'),
            cio=get_first_value('cio'),
            application_class=get_first_value('application_class'),
            
            edr_coverage=coverage_flags.get('edr_coverage', False),
            dlp_coverage=coverage_flags.get('dlp_coverage', False),
            tanium_coverage=coverage_flags.get('tanium_coverage', False),
            splunk_coverage=coverage_flags.get('splunk_coverage', False),
            chronicle_coverage=coverage_flags.get('chronicle_coverage', False),
            crowdstrike_coverage=coverage_flags.get('crowdstrike_coverage', False),
            cmdb_visibility=coverage_flags.get('cmdb_visibility', False),
            
            visibility_score=self._calculate_visibility_score(coverage_flags),
            quality_score=self._calculate_quality_score(all_data),
            confidence_score=0.8,
            intelligence_quotient=0.7,
            
            tables_found_in=list(asset_data.get('source_tables', [])),
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        return hyper_asset
    
    def _calculate_visibility_score(self, coverage_flags: Dict[str, bool]) -> float:
        total_flags = len(coverage_flags)
        true_flags = sum(1 for v in coverage_flags.values() if v)
        return (true_flags / total_flags) if total_flags > 0 else 0.0
    
    def _calculate_quality_score(self, all_data: Dict[str, List[str]]) -> float:
        filled_fields = sum(1 for v in all_data.values() if v)
        total_possible = 20
        return min(1.0, filled_fields / total_possible)

class IntensiveEntityResolver:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def resolve_entities(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        return assets