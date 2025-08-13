# intelligent_discovery_engine.py

import logging
import duckdb
import asyncio
import json
import hashlib
import re
import ipaddress
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict, Counter
import statistics
import numpy as np

logger = logging.getLogger(__name__)

class CellContentFirstAnalyzer:
    def __init__(self):
        self.hostname_validators = [
            self._is_hostname_like,
            self._is_server_identifier,
            self._is_endpoint_name,
            self._is_domain_name
        ]
        self.content_type_detectors = {
            'hostname': self._detect_hostname_content,
            'ip_address': self._detect_ip_content,
            'fqdn': self._detect_fqdn_content,
            'mac_address': self._detect_mac_content,
            'infrastructure_type': self._detect_infrastructure_content,
            'system_classification': self._detect_system_classification_content,
            'global_region': self._detect_global_region_content,
            'country': self._detect_country_content,
            'data_center': self._detect_data_center_content,
            'cloud_region': self._detect_cloud_region_content,
            'business_unit': self._detect_business_unit_content,
            'cio': self._detect_cio_content,
            'apm': self._detect_apm_content,
            'application_class': self._detect_application_class_content,
            'edr_coverage': self._detect_edr_coverage_content,
            'tanium_coverage': self._detect_tanium_coverage_content,
            'dlp_coverage': self._detect_dlp_coverage_content,
            'network_log_types': self._detect_network_log_types_content,
            'endpoint_log_types': self._detect_endpoint_log_types_content,
            'cloud_log_types': self._detect_cloud_log_types_content,
            'application_log_types': self._detect_application_log_types_content,
            'identity_log_types': self._detect_identity_log_types_content,
            'url_fqdn_coverage': self._detect_url_fqdn_coverage_content,
            'public_ip_coverage': self._detect_public_ip_coverage_content,
            'cmdb_asset_visibility': self._detect_cmdb_asset_visibility_content,
            'network_zones': self._detect_network_zones_content,
            'ipam_coverage': self._detect_ipam_coverage_content,
            'geolocation': self._detect_geolocation_content,
            'vpc': self._detect_vpc_content,
            'domain_visibility': self._detect_domain_visibility_content,
            'internal_external': self._detect_internal_external_content,
            'controls': self._detect_controls_content

class ExhaustiveBigQueryScanner:
    def __init__(self, project_ids: List[str], client_managers: Dict[str, Any]):
        self.project_ids = project_ids
        self.client_managers = client_managers
        self.cell_analyzer = CellContentFirstAnalyzer()
        self.discovered_tables = {}
        self.table_analysis_results = {}
        
    async def scan_all_projects_exhaustively(self) -> Dict[str, Any]:
        logger.info("Starting exhaustive scan of ALL tables in ALL datasets across ALL projects")
        
        all_discovered_data = {}
        
        for project_id in self.project_ids:
            logger.info(f"Scanning project: {project_id}")
            
            client_manager = self.client_managers.get(project_id)
            if not client_manager:
                continue
                
            project_data = await self._scan_project_completely(project_id, client_manager)
            all_discovered_data[project_id] = project_data
            
        return all_discovered_data
    
    async def _scan_project_completely(self, project_id: str, client_manager) -> Dict[str, Any]:
        project_results = {
            'datasets': {},
            'total_tables_found': 0,
            'total_tables_with_data': 0,
            'visibility_data_found': {}
        }
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            for dataset in datasets:
                dataset_id = dataset.dataset_id
                logger.info(f"Scanning dataset: {project_id}.{dataset_id}")
                
                dataset_results = await self._scan_dataset_exhaustively(
                    client, project_id, dataset_id
                )
                
                project_results['datasets'][dataset_id] = dataset_results
                project_results['total_tables_found'] += dataset_results['total_tables']
                project_results['total_tables_with_data'] += dataset_results['tables_with_data']
                
        return project_results
    
    async def _scan_dataset_exhaustively(self, client, project_id: str, dataset_id: str) -> Dict[str, Any]:
        dataset_results = {
            'tables': {},
            'total_tables': 0,
            'tables_with_data': 0,
            'visibility_fields_found': {}
        }
        
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            
            dataset_results['total_tables'] = len(tables)
            
            for table_ref in tables:
                table_id = table_ref.table_id
                table_path = f"{project_id}.{dataset_id}.{table_id}"
                
                logger.info(f"Analyzing table: {table_path}")
                
                table_analysis = await self._analyze_table_cell_content(client, table_path)
                
                if table_analysis['has_useful_data']:
                    dataset_results['tables_with_data'] += 1
                    dataset_results['tables'][table_id] = table_analysis
                    
                    for field_type, field_data in table_analysis['detected_fields'].items():
                        if field_data['score'] > 0.3:
                            if field_type not in dataset_results['visibility_fields_found']:
                                dataset_results['visibility_fields_found'][field_type] = []
                            dataset_results['visibility_fields_found'][field_type].append({
                                'table': table_id,
                                'column': field_data.get('best_column', ''),
                                'score': field_data['score'],
                                'examples': field_data.get('examples', [])
                            })
                            
        except Exception as e:
            logger.error(f"Failed to scan dataset {dataset_id}: {e}")
            
        return dataset_results
    
    async def _analyze_table_cell_content(self, client, table_path: str) -> Dict[str, Any]:
        analysis_result = {
            'table_path': table_path,
            'has_useful_data': False,
            'detected_fields': {},
            'column_analysis': {},
            'sample_data_analyzed': 0
        }
        
        try:
            table_ref = client.get_table(table_path)
            
            if not table_ref.schema or table_ref.num_rows == 0:
        
    def _is_hostname_like(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 253:
            return False
        
        hostname_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]
            
            columns = [field.name for field in table_ref.schema]
            
            sample_query = f"""
            SELECT *
            FROM `{table_path}`
            WHERE RAND() < 0.1
            LIMIT 1000
            """
            
            job = client.query(sample_query)
            results = list(job.result())
            
            if not results:
                return analysis_result
            
            analysis_result['sample_data_analyzed'] = len(results)
            
            for col_idx, column_name in enumerate(columns):
                cell_values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_values.append(row[col_idx])
                
                if len(cell_values) < 5:
                    continue
                    
                column_analysis = self.cell_analyzer.analyze_raw_cell_content(cell_values, ignore_column_name=True)
                analysis_result['column_analysis'][column_name] = column_analysis
                
                if column_analysis.get('best_match'):
                    field_type, field_data = column_analysis['best_match']
                    
                    if field_type not in analysis_result['detected_fields'] or field_data['score'] > analysis_result['detected_fields'][field_type].get('score', 0):
                        analysis_result['detected_fields'][field_type] = {
                            'score': field_data['score'],
                            'best_column': column_name,
                            'examples': field_data.get('examples', []),
                            'confidence': field_data.get('score', 0)
                        }
                        analysis_result['has_useful_data'] = True
                        
        except Exception as e:
            logger.error(f"Failed to analyze table content for {table_path}: {e}")
            
        return analysis_result
        
    def analyze_raw_cell_content(self, cell_values: List[str], ignore_column_name: bool = True) -> Dict[str, Any]:
        if not cell_values:
            return {'content_types': {}, 'confidence': 0.0}
            
        clean_values = []
        for val in cell_values:
            if val is not None:
                str_val = str(val).strip()
                if str_val and str_val.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
                    clean_values.append(str_val)
        
        if len(clean_values) < 1:
            return {'content_types': {}, 'confidence': 0.0}
        
        content_analysis = {}
        for content_type, detector in self.content_type_detectors.items():
            detection_result = detector(clean_values)
            if detection_result['score'] > 0.1:
                content_analysis[content_type] = detection_result
        
        return {
            'content_types': content_analysis,
            'sample_size': len(clean_values),
            'total_analyzed': len(cell_values),
            'best_match': max(content_analysis.items(), key=lambda x: x[1]['score']) if content_analysis else None
        }
    
    def _detect_hostname_content(self, values: List[str]) -> Dict[str, Any]:
        hostname_count = 0
        total_analyzed = min(len(values), 100)
        hostname_examples = []
        
        for value in values[:total_analyzed]:
            is_hostname = any(validator(value) for validator in self.hostname_validators)
            if is_hostname:
                hostname_count += 1
                if len(hostname_examples) < 5:
                    hostname_examples.append(value)
        
        score = hostname_count / total_analyzed if total_analyzed > 0 else 0.0
        
        return {
            'score': score,
            'matches': hostname_count,
            'total': total_analyzed,
            'examples': hostname_examples,,
            r'^[a-zA-Z0-9]+
            
            columns = [field.name for field in table_ref.schema]
            
            sample_query = f"""
            SELECT *
            FROM `{table_path}`
            WHERE RAND() < 0.1
            LIMIT 1000
            """
            
            job = client.query(sample_query)
            results = list(job.result())
            
            if not results:
                return analysis_result
            
            analysis_result['sample_data_analyzed'] = len(results)
            
            for col_idx, column_name in enumerate(columns):
                cell_values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_values.append(row[col_idx])
                
                if len(cell_values) < 5:
                    continue
                    
                column_analysis = self.cell_analyzer.analyze_raw_cell_content(cell_values, ignore_column_name=True)
                analysis_result['column_analysis'][column_name] = column_analysis
                
                if column_analysis.get('best_match'):
                    field_type, field_data = column_analysis['best_match']
                    
                    if field_type not in analysis_result['detected_fields'] or field_data['score'] > analysis_result['detected_fields'][field_type].get('score', 0):
                        analysis_result['detected_fields'][field_type] = {
                            'score': field_data['score'],
                            'best_column': column_name,
                            'examples': field_data.get('examples', []),
                            'confidence': field_data.get('score', 0)
                        }
                        analysis_result['has_useful_data'] = True
                        
        except Exception as e:
            logger.error(f"Failed to analyze table content for {table_path}: {e}")
            
        return analysis_result
        
    def analyze_raw_cell_content(self, cell_values: List[str], ignore_column_name: bool = True) -> Dict[str, Any]:
        if not cell_values:
            return {'content_types': {}, 'confidence': 0.0}
            
        clean_values = []
        for val in cell_values:
            if val is not None:
                str_val = str(val).strip()
                if str_val and str_val.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
                    clean_values.append(str_val)
        
        if len(clean_values) < 1:
            return {'content_types': {}, 'confidence': 0.0}
        
        content_analysis = {}
        for content_type, detector in self.content_type_detectors.items():
            detection_result = detector(clean_values)
            if detection_result['score'] > 0.1:
                content_analysis[content_type] = detection_result
        
        return {
            'content_types': content_analysis,
            'sample_size': len(clean_values),
            'total_analyzed': len(cell_values),
            'best_match': max(content_analysis.items(), key=lambda x: x[1]['score']) if content_analysis else None
        }
    
    def _detect_hostname_content(self, values: List[str]) -> Dict[str, Any]:
        hostname_count = 0
        total_analyzed = min(len(values), 100)
        hostname_examples = []
        
        for value in values[:total_analyzed]:
            is_hostname = any(validator(value) for validator in self.hostname_validators)
            if is_hostname:
                hostname_count += 1
                if len(hostname_examples) < 5:
                    hostname_examples.append(value)
        
        score = hostname_count / total_analyzed if total_analyzed > 0 else 0.0
        
        return {
            'score': score,
            'matches': hostname_count,
            'total': total_analyzed,
            'examples': hostname_examples,
        ]
        
        return any(re.match(pattern, value) for pattern in hostname_patterns)
    
    def _is_server_identifier(self, value: str) -> bool:
        server_indicators = ['srv', 'server', 'web', 'app', 'db', 'sql', 'win', 'linux']
        return any(indicator in value.lower() for indicator in server_indicators)
    
    def _is_endpoint_name(self, value: str) -> bool:
        endpoint_indicators = ['pc', 'laptop', 'desktop', 'workstation', 'endpoint']
        return any(indicator in value.lower() for indicator in endpoint_indicators)
    
    def _is_domain_name(self, value: str) -> bool:
        return '.' in value and len(value.split('.')) >= 2
    
    def _calculate_pattern_confidence(self, examples: List[str]) -> float:
        if not examples:
            return 0.0
        
        pattern_consistency = len(set(len(ex) for ex in examples)) <= 3
        has_common_prefix = len(set(ex[:3] for ex in examples if len(ex) >= 3)) <= 2
        
        confidence = 0.5
        if pattern_consistency:
            confidence += 0.2
        if has_common_prefix:
            confidence += 0.3
            
        return min(1.0, confidence)

class ComprehensiveAssetBuilder:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scanner = None
        self.db_path = config.get('database_path', 'comprehensive_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        self._setup_comprehensive_schema()
    
    def _setup_comprehensive_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS comprehensive_asset_inventory")
        
        self.conn.execute("""
            CREATE TABLE comprehensive_asset_inventory (
                master_asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                fqdn VARCHAR,
                ip_address VARCHAR,
                mac_address VARCHAR,
                infrastructure_type VARCHAR,
                system_classification VARCHAR,
                global_region VARCHAR,
                country VARCHAR,
                data_center VARCHAR,
                cloud_region VARCHAR,
                business_unit VARCHAR,
                cio VARCHAR,
                apm VARCHAR,
                application_class VARCHAR,
                edr_coverage BOOLEAN DEFAULT FALSE,
                tanium_coverage BOOLEAN DEFAULT FALSE,
                dlp_coverage BOOLEAN DEFAULT FALSE,
                network_log_types VARCHAR,
                endpoint_log_types VARCHAR,
                cloud_log_types VARCHAR,
                application_log_types VARCHAR,
                identity_log_types VARCHAR,
                url_fqdn_coverage VARCHAR,
                public_ip_coverage VARCHAR,
                cmdb_asset_visibility VARCHAR,
                network_zones VARCHAR,
                ipam_coverage VARCHAR,
                geolocation VARCHAR,
                vpc VARCHAR,
                domain_visibility VARCHAR,
                internal_external VARCHAR,
                controls VARCHAR,
                found_in_original_cmdb BOOLEAN DEFAULT FALSE,
                found_in_splunk BOOLEAN DEFAULT FALSE,
                found_in_chronicle BOOLEAN DEFAULT FALSE,
                found_in_crowdstrike BOOLEAN DEFAULT FALSE,
                source_tables JSON,
                discovery_confidence DOUBLE DEFAULT 0.0,
                data_quality_score DOUBLE DEFAULT 0.0,
                visibility_completeness DOUBLE DEFAULT 0.0,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info("Comprehensive database schema created")
    
    async def build_comprehensive_cmdb(self, project_ids: List[str], client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Building comprehensive CMDB from exhaustive BigQuery scan")
        
        self.scanner = ExhaustiveBigQueryScanner(project_ids, client_managers)
        
        discovery_results = await self.scanner.scan_all_projects_exhaustively()
        
        consolidated_assets = await self._consolidate_discovered_data(discovery_results)
        
        stored_count = await self._store_comprehensive_assets(consolidated_assets)
        
        return {
            'total_assets': len(consolidated_assets),
            'stored_assets': stored_count,
            'discovery_results': discovery_results,
            'database_path': self.db_path
        }
    
    async def _consolidate_discovered_data(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Consolidating all discovered data into comprehensive assets")
        
        consolidated_assets = {}
        
        for project_id, project_data in discovery_results.items():
            for dataset_id, dataset_data in project_data['datasets'].items():
                for table_id, table_data in dataset_data['tables'].items():
                    
                    if 'hostname' in table_data['detected_fields']:
                        hostname_data = table_data['detected_fields']['hostname']
                        
                        for example_hostname in hostname_data.get('examples', [])[:10]:
                            if not example_hostname:
                                continue
                                
                            master_id = f"asset_{hashlib.md5(str(example_hostname).upper().encode()).hexdigest()[:12]}"
                            
                            if master_id not in consolidated_assets:
                                consolidated_assets[master_id] = {
                                    'master_asset_id': master_id,
                                    'hostname': str(example_hostname).upper(),
                                    'source_tables': [],
                                    'all_data': {},
                                    'visibility_flags': {}
                                }
                            
                            asset = consolidated_assets[master_id]
                            table_path = f"{project_id}.{dataset_id}.{table_id}"
                            asset['source_tables'].append(table_path)
                            
                            for field_type, field_info in table_data['detected_fields'].items():
                                if field_type not in asset['all_data']:
                                    asset['all_data'][field_type] = []
                                asset['all_data'][field_type].extend(field_info.get('examples', []))
                            
                            if 'cmdb' in table_id.lower():
                                asset['visibility_flags']['found_in_original_cmdb'] = True
                            elif 'splunk' in table_id.lower():
                                asset['visibility_flags']['found_in_splunk'] = True
                            elif 'chronicle' in table_id.lower():
                                asset['visibility_flags']['found_in_chronicle'] = True
                            elif 'crowdstrike' in table_id.lower():
                                asset['visibility_flags']['found_in_crowdstrike'] = True
        
        logger.info(f"Consolidated into {len(consolidated_assets)} unique assets")
        return consolidated_assets
    
    async def _store_comprehensive_assets(self, assets: Dict[str, Any]) -> int:
        stored_count = 0
        
        for asset_id, asset_data in assets.items():
            try:
                all_data = asset_data.get('all_data', {})
                visibility_flags = asset_data.get('visibility_flags', {})
                
                values = [
                    asset_data['master_asset_id'],
                    asset_data.get('hostname', ''),
                    ', '.join(all_data.get('fqdn', [])[:3]),
                    ', '.join(all_data.get('ip_address', [])[:3]),
                    ', '.join(all_data.get('mac_address', [])[:3]),
                    ', '.join(all_data.get('infrastructure_type', [])[:3]),
                    ', '.join(all_data.get('system_classification', [])[:3]),
                    ', '.join(all_data.get('global_region', [])[:3]),
                    ', '.join(all_data.get('country', [])[:3]),
                    ', '.join(all_data.get('data_center', [])[:3]),
                    ', '.join(all_data.get('cloud_region', [])[:3]),
                    ', '.join(all_data.get('business_unit', [])[:3]),
                    ', '.join(all_data.get('cio', [])[:3]),
                    ', '.join(all_data.get('apm', [])[:3]),
                    ', '.join(all_data.get('application_class', [])[:3]),
                    'edr_coverage' in all_data or visibility_flags.get('found_in_crowdstrike', False),
                    'tanium_coverage' in all_data,
                    'dlp_coverage' in all_data,
                    ', '.join(all_data.get('network_log_types', [])[:3]),
                    ', '.join(all_data.get('endpoint_log_types', [])[:3]),
                    ', '.join(all_data.get('cloud_log_types', [])[:3]),
                    ', '.join(all_data.get('application_log_types', [])[:3]),
                    ', '.join(all_data.get('identity_log_types', [])[:3]),
                    ', '.join(all_data.get('url_fqdn_coverage', [])[:3]),
                    ', '.join(all_data.get('public_ip_coverage', [])[:3]),
                    ', '.join(all_data.get('cmdb_asset_visibility', [])[:3]),
                    ', '.join(all_data.get('network_zones', [])[:3]),
                    ', '.join(all_data.get('ipam_coverage', [])[:3]),
                    ', '.join(all_data.get('geolocation', [])[:3]),
                    ', '.join(all_data.get('vpc', [])[:3]),
                    ', '.join(all_data.get('domain_visibility', [])[:3]),
                    ', '.join(all_data.get('internal_external', [])[:3]),
                    ', '.join(all_data.get('controls', [])[:3]),
                    visibility_flags.get('found_in_original_cmdb', False),
                    visibility_flags.get('found_in_splunk', False),
                    visibility_flags.get('found_in_chronicle', False),
                    visibility_flags.get('found_in_crowdstrike', False),
                    json.dumps(asset_data.get('source_tables', [])),
                    0.8,
                    0.7,
                    len(all_data) / 32.0
                ]
                
                self.conn.execute("""
                    INSERT INTO comprehensive_asset_inventory (
                        master_asset_id, hostname, fqdn, ip_address, mac_address,
                        infrastructure_type, system_classification, global_region, country,
                        data_center, cloud_region, business_unit, cio, apm, application_class,
                        edr_coverage, tanium_coverage, dlp_coverage, network_log_types,
                        endpoint_log_types, cloud_log_types, application_log_types,
                        identity_log_types, url_fqdn_coverage, public_ip_coverage,
                        cmdb_asset_visibility, network_zones, ipam_coverage, geolocation,
                        vpc, domain_visibility, internal_external, controls,
                        found_in_original_cmdb, found_in_splunk, found_in_chronicle,
                        found_in_crowdstrike, source_tables, discovery_confidence,
                        data_quality_score, visibility_completeness, discovery_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
                """, values)
                
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store asset {asset_id}: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} comprehensive assets")
        return stored_count
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            
            columns = [field.name for field in table_ref.schema]
            
            sample_query = f"""
            SELECT *
            FROM `{table_path}`
            WHERE RAND() < 0.1
            LIMIT 1000
            """
            
            job = client.query(sample_query)
            results = list(job.result())
            
            if not results:
                return analysis_result
            
            analysis_result['sample_data_analyzed'] = len(results)
            
            for col_idx, column_name in enumerate(columns):
                cell_values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        cell_values.append(row[col_idx])
                
                if len(cell_values) < 5:
                    continue
                    
                column_analysis = self.cell_analyzer.analyze_raw_cell_content(cell_values, ignore_column_name=True)
                analysis_result['column_analysis'][column_name] = column_analysis
                
                if column_analysis.get('best_match'):
                    field_type, field_data = column_analysis['best_match']
                    
                    if field_type not in analysis_result['detected_fields'] or field_data['score'] > analysis_result['detected_fields'][field_type].get('score', 0):
                        analysis_result['detected_fields'][field_type] = {
                            'score': field_data['score'],
                            'best_column': column_name,
                            'examples': field_data.get('examples', []),
                            'confidence': field_data.get('score', 0)
                        }
                        analysis_result['has_useful_data'] = True
                        
        except Exception as e:
            logger.error(f"Failed to analyze table content for {table_path}: {e}")
            
        return analysis_result
        
    def analyze_raw_cell_content(self, cell_values: List[str], ignore_column_name: bool = True) -> Dict[str, Any]:
        if not cell_values:
            return {'content_types': {}, 'confidence': 0.0}
            
        clean_values = []
        for val in cell_values:
            if val is not None:
                str_val = str(val).strip()
                if str_val and str_val.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
                    clean_values.append(str_val)
        
        if len(clean_values) < 1:
            return {'content_types': {}, 'confidence': 0.0}
        
        content_analysis = {}
        for content_type, detector in self.content_type_detectors.items():
            detection_result = detector(clean_values)
            if detection_result['score'] > 0.1:
                content_analysis[content_type] = detection_result
        
        return {
            'content_types': content_analysis,
            'sample_size': len(clean_values),
            'total_analyzed': len(cell_values),
            'best_match': max(content_analysis.items(), key=lambda x: x[1]['score']) if content_analysis else None
        }
    
    def _detect_hostname_content(self, values: List[str]) -> Dict[str, Any]:
        hostname_count = 0
        total_analyzed = min(len(values), 100)
        hostname_examples = []
        
        for value in values[:total_analyzed]:
            is_hostname = any(validator(value) for validator in self.hostname_validators)
            if is_hostname:
                hostname_count += 1
                if len(hostname_examples) < 5:
                    hostname_examples.append(value)
        
        score = hostname_count / total_analyzed if total_analyzed > 0 else 0.0
        
        return {
            'score': score,
            'matches': hostname_count,
            'total': total_analyzed,
            'examples': hostname_examples,