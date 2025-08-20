import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
import sys

# Add gcp module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gcp.client import BigQueryClientManager
from core.quantum_types import QuantumAsset, LogMapping, DiscoveryMetrics
from ai.neural_engine import HyperIntelligence

logger = logging.getLogger(__name__)

class QuantumDiscoveryEngine:
    def __init__(self, project_ids: List[str], config: Dict[str, Any]):
        self.project_ids = project_ids
        self.config = config
        self.intelligence = HyperIntelligence()
        self.assets: Dict[str, QuantumAsset] = {}
        self.metrics = DiscoveryMetrics()
        self.processed_tables: Set[str] = set()
        
        # Use BigQueryClientManager for each project
        self.client_managers = {}
        self.clients = {}
        
        for project_id in project_ids:
            try:
                # Create client manager for each project
                manager = BigQueryClientManager(project_id)
                self.client_managers[project_id] = manager
                
                # Get the actual client from the manager
                with manager.get_client() as client:
                    self.clients[project_id] = client
                    logger.info(f"✅ Connected to project: {project_id}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to connect to project {project_id}: {e}")
                logger.error(f"Skipping project {project_id}")
                continue
        
        if not self.clients:
            raise RuntimeError("Failed to connect to any BigQuery projects. Please check authentication.")
        
        self.sampling_config = {
            'max_sample_size': config.get('discovery_settings', {}).get('max_sample_size', 10000),
            'sample_ratio': config.get('discovery_settings', {}).get('sample_ratio', 0.1),
            'min_confidence': config.get('discovery_settings', {}).get('min_confidence', 0.7),
            'batch_size': config.get('discovery_settings', {}).get('batch_size', 5000),
            'max_workers': config.get('discovery_settings', {}).get('max_workers', 32)
        }
        
        self.coverage_patterns = {
            'edr': ['edr', 'endpoint_detection', 'crowdstrike', 'carbon_black', 'sentinel'],
            'tanium': ['tanium', 'endpoint_platform'],
            'dlp': ['dlp', 'data_loss', 'forcepoint', 'symantec_dlp'],
            'splunk': ['splunk', 'spl_', 'universal_forwarder'],
            'chronicle': ['chronicle', 'backstory', 'google_security'],
            'cmdb': ['cmdb', 'servicenow', 'asset_management', 'configuration_management']
        }
    
    async def discover_all_assets(self) -> Dict[str, QuantumAsset]:
        logger.info(f"Starting quantum discovery across {len(self.clients)} connected projects")
        
        with ThreadPoolExecutor(max_workers=self.sampling_config['max_workers']) as executor:
            futures = []
            
            for project_id in self.clients.keys():
                future = executor.submit(self._discover_project_assets, project_id)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    project_assets = future.result()
                    self._merge_project_assets(project_assets)
                except Exception as e:
                    logger.error(f"Project discovery failed: {e}")
        
        self._calculate_metrics()
        self._identify_gaps()
        
        logger.info(f"Discovery complete: {len(self.assets)} unique assets found")
        return self.assets
    
    def _discover_project_assets(self, project_id: str) -> Dict[str, QuantumAsset]:
        project_assets = {}
        
        # Get client through manager
        manager = self.client_managers.get(project_id)
        if not manager:
            logger.error(f"No client manager for project {project_id}")
            return project_assets
        
        try:
            with manager.get_client() as client:
                # List datasets
                datasets = list(client.list_datasets(project=project_id))
                logger.info(f"Found {len(datasets)} datasets in project {project_id}")
                
                for dataset in datasets:
                    try:
                        tables = list(client.list_tables(dataset))
                        logger.info(f"Found {len(tables)} tables in dataset {dataset.dataset_id}")
                        
                        for table_ref in tables:
                            table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                            
                            if table_path in self.processed_tables:
                                continue
                            
                            try:
                                table_assets = self._process_table(client, table_path)
                                
                                for asset_id, asset in table_assets.items():
                                    if asset_id in project_assets:
                                        project_assets[asset_id] = project_assets[asset_id].merge_with(asset)
                                    else:
                                        project_assets[asset_id] = asset
                                
                                self.processed_tables.add(table_path)
                                
                            except Exception as e:
                                logger.warning(f"Table processing failed for {table_path}: {e}")
                    
                    except Exception as e:
                        logger.error(f"Failed to process dataset {dataset.dataset_id}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Failed to discover assets in project {project_id}: {e}")
        
        logger.info(f"Discovered {len(project_assets)} assets in project {project_id}")
        return project_assets
    
    def _process_table(self, client, table_path: str) -> Dict[str, QuantumAsset]:
        table_assets = {}
        
        try:
            table = client.get_table(table_path)
            if table.num_rows == 0:
                logger.debug(f"Table {table_path} is empty, skipping")
                return table_assets
            
            columns = [field.name for field in table.schema]
            
            # Skip tables that are likely not asset-related
            if 'log_types' in table_path.lower() or 'metadata' in table_path.lower():
                logger.debug(f"Skipping metadata/config table: {table_path}")
                return table_assets
            
            column_classifications = self._classify_columns(columns, table_path, client)
            
            if 'hostname' not in column_classifications:
                logger.debug(f"No hostname column found in {table_path}, skipping")
                return table_assets
            
            hostname_col = column_classifications['hostname']
            
            sample_size = min(self.sampling_config['max_sample_size'], 
                             int(table.num_rows * self.sampling_config['sample_ratio']))
            
            query = f"""
            SELECT *
            FROM `{table_path}`
            WHERE {hostname_col} IS NOT NULL
            AND RAND() < {self.sampling_config['sample_ratio']}
            LIMIT {sample_size}
            """
            
            query_job = client.query(query)
            results = query_job.result()
            
            # Get log type info with error handling
            try:
                log_type_info = self.intelligence.identify_log_type(table_path, columns)
            except Exception as e:
                logger.warning(f"Failed to identify log type for {table_path}: {e}")
                log_type_info = {
                    'role': 'unknown',
                    'confidence': 0.5,
                    'log_types': [],
                    'visibility_factors': []
                }
            
            row_count = 0
            for row in results:
                try:
                    hostname = getattr(row, hostname_col, None)
                    if not hostname or not self._is_valid_hostname(str(hostname)):
                        continue
                    
                    asset = self._create_asset_from_row(row, column_classifications, table_path, log_type_info)
                    asset_id = asset.get_unique_id()
                    
                    if asset_id in table_assets:
                        table_assets[asset_id] = table_assets[asset_id].merge_with(asset)
                    else:
                        table_assets[asset_id] = asset
                    
                    row_count += 1
                    
                except Exception as e:
                    logger.debug(f"Failed to process row in {table_path}: {e}")
                    continue
            
            logger.info(f"Processed {row_count} assets from {table_path}")
            
        except Exception as e:
            logger.error(f"Error processing table {table_path}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return table_assets
    
    def _classify_columns(self, columns: List[str], table_path: str, client) -> Dict[str, str]:
        classifications = {}
        
        # Quick check for common patterns first
        for column in columns:
            column_lower = column.lower()
            
            # Priority patterns for quick matching
            if any(pattern in column_lower for pattern in ['hostname', 'host_name', 'computer_name', 'server_name']):
                classifications['hostname'] = column
                break
        
        # If no hostname found in quick check, try ML classification
        if 'hostname' not in classifications:
            sample_query = f"""
            SELECT *
            FROM `{table_path}`
            LIMIT 100
            """
            
            try:
                query_job = client.query(sample_query)
                sample_rows = list(query_job.result())
                
                if sample_rows:
                    for column in columns:
                        # Skip obvious non-hostname columns
                        if column.lower() in ['log_types', 'timestamp', 'date', 'time', 'id', 'index']:
                            continue
                        
                        sample_values = []
                        for row in sample_rows:
                            value = getattr(row, column, None)
                            if value is not None:
                                sample_values.append(str(value))
                        
                        if sample_values:
                            try:
                                field_type, confidence, metadata = self.intelligence.classify_column(column, sample_values)
                                
                                if confidence >= self.sampling_config['min_confidence']:
                                    classifications[field_type] = column
                                    
                                    # If we found hostname, we can continue with other fields
                                    if field_type == 'hostname':
                                        logger.debug(f"Found hostname column: {column} with confidence {confidence}")
                            except Exception as e:
                                logger.debug(f"Failed to classify column {column}: {e}")
                                continue
                
            except Exception as e:
                logger.warning(f"Failed to run sample query for {table_path}: {e}")
        
        # Final fallback for hostname if still not found
        if 'hostname' not in classifications:
            for column in columns:
                column_lower = column.lower()
                # Extended pattern matching
                if any(pattern in column_lower for pattern in ['host', 'name', 'server', 'node', 'computer', 'machine', 'device']):
                    classifications['hostname'] = column
                    logger.debug(f"Using fallback hostname column: {column}")
                    break
        
        return classifications
    
    def _create_asset_from_row(self, row: Any, classifications: Dict[str, str], 
                              table_path: str, log_type_info: Dict[str, Any]) -> QuantumAsset:
        
        hostname = str(getattr(row, classifications.get('hostname', ''), ''))
        
        asset = QuantumAsset(hostname=hostname)
        
        for field_type, column_name in classifications.items():
            if field_type == 'hostname':
                continue
            
            value = getattr(row, column_name, None)
            if value:
                if field_type == 'infrastructure_type':
                    asset.infrastructure_type = self.intelligence.classify_infrastructure(str(value))
                elif field_type == 'system_classification':
                    asset.system_classification = self.intelligence.classify_system(str(value))
                elif field_type == 'region':
                    asset.region = self.intelligence.map_region(str(value))
                elif hasattr(asset, field_type):
                    setattr(asset, field_type, str(value))
        
        asset.source_tables.add(table_path)
        
        self._detect_coverage_flags(asset, table_path, classifications)
        
        # Fix: Properly handle log_types assignment
        if log_type_info and isinstance(log_type_info, dict):
            role = log_type_info.get('role', 'unknown')
            log_types_list = log_type_info.get('log_types', [])
            
            # Ensure log_types is a dictionary
            if not isinstance(asset.log_types, dict):
                asset.log_types = {}
            
            # Store log types as a list under the role key
            asset.log_types[role] = log_types_list
            
            # Handle visibility factors
            visibility_factors = log_type_info.get('visibility_factors', [])
            if visibility_factors and isinstance(visibility_factors, list):
                for factor in visibility_factors:
                    asset.visibility_factors[factor] = log_type_info.get('confidence', 0.5)
            
            # Set ML confidence
            asset.ml_confidence = log_type_info.get('confidence', 0.5)
        
        asset.calculate_visibility_score()
        
        return asset
    
    def _detect_coverage_flags(self, asset: QuantumAsset, table_path: str, classifications: Dict[str, str]):
        table_lower = table_path.lower()
        
        for coverage_type, patterns in self.coverage_patterns.items():
            if any(pattern in table_lower for pattern in patterns):
                if coverage_type == 'edr':
                    asset.edr_coverage = True
                elif coverage_type == 'tanium':
                    asset.tanium_coverage = True
                elif coverage_type == 'dlp':
                    asset.dlp_coverage = True
                elif coverage_type == 'splunk':
                    asset.splunk_logging = True
                elif coverage_type == 'chronicle':
                    asset.chronicle_coverage = True
                elif coverage_type == 'cmdb':
                    asset.cmdb_visibility = True
        
        if 'gso' in table_lower or 'global_security' in table_lower:
            asset.gso_logging = True
        
        if 'crowdstrike' in table_lower or 'falcon' in table_lower:
            asset.crowdstrike_coverage = True
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        if not hostname or len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_chars = ['@', '/', '\\', ' ', '\t', '\n', '|', ';', '"', "'"]
        if any(char in hostname for char in invalid_chars):
            return False
        
        invalid_values = ['null', 'none', 'unknown', 'n/a', 'test', 'localhost', '127.0.0.1']
        if hostname.lower() in invalid_values:
            return False
        
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        return bool(re.match(hostname_pattern, hostname, re.IGNORECASE))
    
    def _merge_project_assets(self, project_assets: Dict[str, QuantumAsset]):
        for asset_id, asset in project_assets.items():
            if asset_id in self.assets:
                self.assets[asset_id] = self.assets[asset_id].merge_with(asset)
            else:
                self.assets[asset_id] = asset
    
    def _calculate_metrics(self):
        if not self.assets:
            return
        
        self.metrics.total_assets = len(self.assets)
        
        cmdb_count = sum(1 for a in self.assets.values() if a.cmdb_visibility)
        self.metrics.cmdb_coverage = cmdb_count / self.metrics.total_assets
        
        url_fqdn_count = sum(1 for a in self.assets.values() if a.fqdn or 'url_fqdn_coverage' in a.visibility_factors)
        self.metrics.url_fqdn_coverage = url_fqdn_count / self.metrics.total_assets
        
        public_ip_count = sum(1 for a in self.assets.values() if a.ipam_public_ip)
        self.metrics.public_ip_coverage = public_ip_count / self.metrics.total_assets
        
        endpoint_count = sum(1 for a in self.assets.values() if a.edr_coverage or a.tanium_coverage)
        self.metrics.endpoint_coverage = endpoint_count / self.metrics.total_assets
        
        cloud_count = sum(1 for a in self.assets.values() if a.infrastructure_type == 'cloud')
        self.metrics.cloud_coverage = cloud_count / self.metrics.total_assets
        
        for asset in self.assets.values():
            if asset.infrastructure_type:
                self.metrics.infrastructure_distribution[asset.infrastructure_type] = \
                    self.metrics.infrastructure_distribution.get(asset.infrastructure_type, 0) + 1
            
            if asset.region:
                self.metrics.regional_distribution[asset.region] = \
                    self.metrics.regional_distribution.get(asset.region, 0) + 1
            
            if asset.business_unit:
                self.metrics.business_unit_distribution[asset.business_unit] = \
                    self.metrics.business_unit_distribution.get(asset.business_unit, 0) + 1
            
            if asset.system_classification:
                self.metrics.system_classification_distribution[asset.system_classification] = \
                    self.metrics.system_classification_distribution.get(asset.system_classification, 0) + 1
    
    def _identify_gaps(self):
        for asset in self.assets.values():
            if not asset.edr_coverage and not asset.tanium_coverage:
                self.metrics.security_gaps.append({
                    'hostname': asset.hostname,
                    'gap_type': 'no_endpoint_protection',
                    'risk_level': 'high'
                })
            
            if not asset.splunk_logging and not asset.gso_logging:
                self.metrics.logging_gaps.append({
                    'hostname': asset.hostname,
                    'gap_type': 'no_logging',
                    'risk_level': 'critical'
                })
            
            if asset.visibility_score < 0.5:
                self.metrics.compliance_issues.append({
                    'hostname': asset.hostname,
                    'issue_type': 'low_visibility',
                    'visibility_score': asset.visibility_score
                })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        return {
            'total_assets': self.metrics.total_assets,
            'coverage': {
                'cmdb': f"{self.metrics.cmdb_coverage:.1%}",
                'url_fqdn': f"{self.metrics.url_fqdn_coverage:.1%}",
                'public_ip': f"{self.metrics.public_ip_coverage:.1%}",
                'endpoint': f"{self.metrics.endpoint_coverage:.1%}",
                'cloud': f"{self.metrics.cloud_coverage:.1%}"
            },
            'distributions': {
                'infrastructure': self.metrics.infrastructure_distribution,
                'region': self.metrics.regional_distribution,
                'business_unit': self.metrics.business_unit_distribution,
                'system_class': self.metrics.system_classification_distribution
            },
            'gaps': {
                'security': len(self.metrics.security_gaps),
                'logging': len(self.metrics.logging_gaps),
                'compliance': len(self.metrics.compliance_issues)
            }
        }
    
    def test_authentication(self) -> Dict[str, bool]:
        """Test authentication for all projects"""
        auth_status = {}
        
        for project_id, manager in self.client_managers.items():
            auth_status[project_id] = manager.test_connection()
        
        return auth_status