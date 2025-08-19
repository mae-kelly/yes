# discovery/content.py

import asyncio
import logging
import hashlib
import re
import gc
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.types import HyperAsset
from ai.content import QuantumContentAnalyzer

logger = logging.getLogger(__name__)

class QuantumContentBasedEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], cache_manager, intelligence):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.content_analyzer = QuantumContentAnalyzer()
        
        self.discovered_assets = {}
        self.processing_stats = {
            'datasets_scanned': 0,
            'tables_analyzed': 0,
            'columns_analyzed': 0,
            'hostname_columns_found': 0,
            'total_assets_discovered': 0,
            'processing_errors': 0,
            'ml_predictions_made': 0,
            'high_confidence_predictions': 0,
            'start_time': datetime.now()
        }
        
        self.hostname_detection_patterns = self._initialize_hostname_patterns()
        self.field_mappings = self._initialize_field_mappings()
    
    def _initialize_hostname_patterns(self) -> List[re.Pattern]:
        patterns = [
            re.compile(r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$', re.IGNORECASE),
            re.compile(r'^[a-zA-Z0-9]{2,63}$', re.IGNORECASE),
            re.compile(r'^[a-zA-Z]{2,6}[0-9]{1,8}$', re.IGNORECASE),
            re.compile(r'^[a-zA-Z]+[\-_][a-zA-Z0-9]+[\-_][a-zA-Z0-9]+$', re.IGNORECASE),
            re.compile(r'^(srv|web|app|db|sql|dc|vm|host|pc|ws|node|server)\-?[a-zA-Z0-9]+', re.IGNORECASE)
        ]
        return patterns
    
    def _initialize_field_mappings(self) -> Dict[str, List[str]]:
        return {
            'hostname': ['hostname', 'host_name', 'computername', 'computer_name', 'device_name', 'endpoint_name', 'asset_name', 'machine_name'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'host_ip', 'device_ip', 'internal_ip', 'private_ip'],
            'fqdn': ['fqdn', 'fully_qualified_domain_name', 'dns_name', 'domain_name', 'qualified_name'],
            'mac_address': ['mac_address', 'mac', 'physical_address', 'ethernet_address', 'hardware_address'],
            'infrastructure_type': ['infrastructure_type', 'hosting_type', 'deployment_type', 'platform_type'],
            'system_classification': ['system_classification', 'os_type', 'operating_system', 'platform'],
            'business_unit': ['business_unit', 'bu', 'department', 'division', 'org_unit'],
            'region': ['region', 'global_region', 'geo_region', 'location', 'geography'],
            'datacenter': ['datacenter', 'dc', 'site', 'facility', 'location_name'],
            'environment': ['environment', 'env', 'tier', 'stage', 'lifecycle'],
            'owner': ['owner', 'responsible_party', 'asset_owner', 'business_owner'],
            'criticality': ['criticality', 'priority', 'importance', 'tier', 'classification']
        }
    
    async def discover_all_quantum_content(self, client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting quantum content-based discovery")
        start_time = datetime.now()
        
        try:
            datasets = await self._discover_all_datasets(client_managers)
            await self._analyze_content_comprehensively(datasets)
            merged_count = await self._merge_and_enrich_assets()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            final_results = {
                'total_unique_assets': len(self.discovered_assets),
                'datasets_scanned': self.processing_stats['datasets_scanned'],
                'tables_analyzed': self.processing_stats['tables_analyzed'],
                'columns_analyzed': self.processing_stats['columns_analyzed'],
                'hostname_columns_found': self.processing_stats['hostname_columns_found'],
                'processing_time_seconds': processing_time,
                'ml_predictions_made': self.processing_stats['ml_predictions_made'],
                'high_confidence_predictions': self.processing_stats['high_confidence_predictions'],
                'quantum_assets': self.discovered_assets,
                'processing_stats': self.processing_stats
            }
            
            logger.info(f"Content discovery completed: {len(self.discovered_assets)} assets discovered")
            return final_results
            
        except Exception as e:
            logger.error(f"Content-based discovery failed: {e}")
            return {'error': str(e), 'stats': self.processing_stats}
    
    async def _discover_all_datasets(self, client_managers: Dict[str, Any]) -> List[Dict[str, Any]]:
        all_datasets = []
        
        for project_id, client_manager in client_managers.items():
            try:
                with client_manager.get_client() as client:
                    project_datasets = list(client.list_datasets(project=project_id))
                    
                    for dataset in project_datasets:
                        all_datasets.append({
                            'project_id': project_id,
                            'dataset_id': dataset.dataset_id,
                            'client_manager': client_manager
                        })
                
                self.processing_stats['datasets_scanned'] += len(project_datasets)
                logger.info(f"Found {len(project_datasets)} datasets in {project_id}")
                
            except Exception as e:
                logger.error(f"Failed to discover datasets in {project_id}: {e}")
                self.processing_stats['processing_errors'] += 1
        
        return all_datasets
    
    async def _analyze_content_comprehensively(self, datasets: List[Dict[str, Any]]):
        with ThreadPoolExecutor(max_workers=self.config.get('max_workers', 16)) as executor:
            futures = []
            
            for dataset_info in datasets:
                future = executor.submit(
                    asyncio.run,
                    self._analyze_single_dataset_content(dataset_info)
                )
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    future.result(timeout=600)
                except Exception as e:
                    logger.error(f"Dataset analysis failed: {e}")
                    self.processing_stats['processing_errors'] += 1
    
    async def _analyze_single_dataset_content(self, dataset_info: Dict[str, Any]):
        dataset_id = dataset_info['dataset_id']
        project_id = dataset_info['project_id']
        client_manager = dataset_info['client_manager']
        
        logger.info(f"Analyzing dataset content: {project_id}.{dataset_id}")
        
        try:
            with client_manager.get_client() as client:
                dataset_ref = client.dataset(dataset_id, project=project_id)
                tables = list(client.list_tables(dataset_ref))
                
                for table_ref in tables:
                    try:
                        await self._analyze_table_content_thoroughly(
                            client, project_id, dataset_id, table_ref.table_id
                        )
                    except Exception as e:
                        logger.warning(f"Table analysis failed for {table_ref.table_id}: {e}")
                        self.processing_stats['processing_errors'] += 1
                
                logger.info(f"Completed dataset analysis: {project_id}.{dataset_id}")
                
        except Exception as e:
            logger.error(f"Dataset content analysis failed: {project_id}.{dataset_id} - {e}")
            self.processing_stats['processing_errors'] += 1
    
    async def _analyze_table_content_thoroughly(self, client, project_id: str, 
                                              dataset_id: str, table_id: str):
        table_path = f"{project_id}.{dataset_id}.{table_id}"
        
        try:
            table = client.get_table(table_path)
            
            if not table.schema or table.num_rows == 0:
                return
            
            columns = [field.name for field in table.schema]
            column_samples = await self._sample_table_columns_intelligently(client, table_path, columns)
            
            hostname_columns = await self._detect_hostname_columns_advanced(columns, column_samples)
            
            self.processing_stats['columns_analyzed'] += len(columns)
            self.processing_stats['hostname_columns_found'] += len(hostname_columns)
            
            if hostname_columns:
                await self._extract_assets_from_table_comprehensive(
                    client, table_path, hostname_columns, column_samples
                )
            
            self.processing_stats['tables_analyzed'] += 1
            
        except Exception as e:
            logger.warning(f"Table content analysis failed for {table_path}: {e}")
            self.processing_stats['processing_errors'] += 1
    
    async def _sample_table_columns_intelligently(self, client, table_path: str, 
                                                 columns: List[str]) -> Dict[str, List[str]]:
        
        sample_size = min(500, max(100, len(columns) * 10))
        
        query = f"""
        SELECT {', '.join([f'`{col}`' for col in columns])}
        FROM `{table_path}`
        WHERE RAND() < 0.02
        LIMIT {sample_size}
        """
        
        column_data = {}
        try:
            job = client.query(query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(columns):
                values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        value = str(row[col_idx]).strip()
                        if value and len(value) < 500:
                            values.append(value)
                
                column_data[column_name] = values[:100]
        
        except Exception as e:
            logger.warning(f"Column sampling failed for {table_path}: {e}")
        
        return column_data
    
    async def _detect_hostname_columns_advanced(self, columns: List[str], 
                                               column_samples: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        hostname_columns = []
        
        for column_name in columns:
            samples = column_samples.get(column_name, [])
            if not samples:
                continue
            
            hostname_score = await self._calculate_hostname_probability(column_name, samples)
            
            if hostname_score['is_hostname'] and hostname_score['confidence'] > 0.6:
                hostname_columns.append({
                    'column_name': column_name,
                    'confidence': hostname_score['confidence'],
                    'samples': samples,
                    'detection_method': hostname_score['method'],
                    'ml_enhanced': hostname_score.get('ml_enhanced', False)
                })
        
        return sorted(hostname_columns, key=lambda x: x['confidence'], reverse=True)
    
    async def _calculate_hostname_probability(self, column_name: str, 
                                            samples: List[str]) -> Dict[str, Any]:
        
        if self.content_analyzer:
            try:
                ml_analysis = self.content_analyzer.analyze_column_quantum_intelligently(
                    column_name, samples
                )
                
                if ml_analysis and ml_analysis[0] == 'hostname' and ml_analysis[1] > 0.7:
                    self.processing_stats['ml_predictions_made'] += 1
                    if ml_analysis[1] > 0.8:
                        self.processing_stats['high_confidence_predictions'] += 1
                    
                    return {
                        'is_hostname': True,
                        'confidence': ml_analysis[1],
                        'method': 'ml_analysis',
                        'ml_enhanced': True,
                        'metadata': ml_analysis[2]
                    }
            except Exception as e:
                logger.debug(f"ML analysis failed for {column_name}: {e}")
        
        name_score = self._calculate_name_hostname_score(column_name)
        content_score = self._calculate_content_hostname_score(samples)
        pattern_score = self._calculate_pattern_hostname_score(samples)
        
        combined_confidence = (name_score * 0.4) + (content_score * 0.4) + (pattern_score * 0.2)
        
        return {
            'is_hostname': combined_confidence > 0.6,
            'confidence': combined_confidence,
            'method': 'pattern_analysis',
            'ml_enhanced': False,
            'name_score': name_score,
            'content_score': content_score,
            'pattern_score': pattern_score
        }
    
    def _calculate_name_hostname_score(self, column_name: str) -> float:
        name_lower = column_name.lower()
        hostname_indicators = self.field_mappings['hostname']
        
        exact_matches = [indicator for indicator in hostname_indicators if indicator == name_lower]
        if exact_matches:
            return 1.0
        
        partial_matches = [indicator for indicator in hostname_indicators if indicator in name_lower]
        if partial_matches:
            best_match = max(partial_matches, key=len)
            return min(1.0, len(best_match) / len(name_lower))
        
        return 0.0
    
    def _calculate_content_hostname_score(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = 0
        for sample in samples[:30]:
            if self._looks_like_hostname(sample):
                hostname_count += 1
        
        return hostname_count / min(len(samples), 30)
    
    def _calculate_pattern_hostname_score(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        pattern_matches = 0
        for sample in samples[:20]:
            for pattern in self.hostname_detection_patterns:
                if pattern.match(sample):
                    pattern_matches += 1
                    break
        
        return pattern_matches / min(len(samples), 20)
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n', '|', ';', '"', "'"]):
            return False
        
        if value.upper() in ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NIL', 'LOCALHOST']:
            return False
        
        return any(pattern.match(value) for pattern in self.hostname_detection_patterns)
    
    async def _extract_assets_from_table_comprehensive(self, client, table_path: str,
                                                      hostname_columns: List[Dict[str, Any]],
                                                      all_column_samples: Dict[str, List[str]]):
        
        for hostname_col_info in hostname_columns:
            hostname_column = hostname_col_info['column_name']
            
            try:
                extraction_query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{hostname_column}` IS NOT NULL
                AND TRIM(`{hostname_column}`) != ''
                LIMIT 100000
                """
                
                job = client.query(extraction_query)
                results = list(job.result())
                
                table_ref = client.get_table(table_path)
                all_columns = [field.name for field in table_ref.schema]
                
                for row in results:
                    hostname_idx = all_columns.index(hostname_column)
                    if hostname_idx < len(row) and row[hostname_idx]:
                        hostname = str(row[hostname_idx]).strip().upper()
                        
                        if not hostname or not self._looks_like_hostname(hostname):
                            continue
                        
                        asset_id = self._generate_asset_id(hostname)
                        
                        if asset_id not in self.discovered_assets:
                            self.discovered_assets[asset_id] = {
                                'hostname': hostname,
                                'primary_identity': hostname,
                                'all_data': defaultdict(set),
                                'source_tables': set(),
                                'coverage_flags': {},
                                'discovery_metadata': {},
                                'quality_metrics': {},
                                'first_seen': datetime.now().isoformat(),
                                'source_count': 0
                            }
                            self.processing_stats['total_assets_discovered'] += 1
                        
                        asset = self.discovered_assets[asset_id]
                        
                        for col_idx, column_name in enumerate(all_columns):
                            if col_idx < len(row) and row[col_idx] is not None:
                                value = str(row[col_idx]).strip()
                                if value and value != hostname:
                                    mapped_field = self._map_column_to_field(column_name)
                                    asset['all_data'][mapped_field].add(value)
                        
                        asset['source_tables'].add(table_path)
                        asset['source_count'] = len(asset['source_tables'])
                        asset['coverage_flags'] = self._determine_coverage_flags(table_path)
                        asset['last_updated'] = datetime.now().isoformat()
                
                logger.info(f"Extracted {len(results)} rows from {table_path} using column {hostname_column}")
                
            except Exception as e:
                logger.error(f"Asset extraction failed for {table_path}: {e}")
                self.processing_stats['processing_errors'] += 1
    
    def _generate_asset_id(self, hostname: str) -> str:
        normalized = hostname.upper().strip()
        return f"content_{hashlib.md5(normalized.encode()).hexdigest()[:12]}"
    
    def _map_column_to_field(self, column_name: str) -> str:
        column_lower = column_name.lower()
        
        for field_type, indicators in self.field_mappings.items():
            for indicator in indicators:
                if indicator in column_lower:
                    return field_type
        
        return column_name
    
    def _determine_coverage_flags(self, table_path: str) -> Dict[str, bool]:
        table_lower = table_path.lower()
        
        coverage_mappings = {
            'in_chronicle': ['chronicle', 'backstory', 'google_security'],
            'in_crowdstrike': ['crowdstrike', 'cs_', 'falcon', 'crwd'],
            'in_original_cmdb': ['cmdb', 'v_dim_endpoint', 'servicenow', 'remedy'],
            'in_splunk': ['splunk', 'spl_', 'universal_forwarder'],
            'in_tanium': ['tanium', 'tan_', 'endpoint_platform'],
            'in_dlp': ['dlp', 'data_loss', 'symantec_dlp', 'forcepoint']
        }
        
        flags = {}
        for flag, keywords in coverage_mappings.items():
            flags[flag] = any(keyword in table_lower for keyword in keywords)
        
        return flags
    
    async def _merge_and_enrich_assets(self) -> int:
        logger.info(f"Merging and enriching {len(self.discovered_assets)} assets")
        
        enriched_count = 0
        
        for asset_id, asset_data in self.discovered_assets.items():
            try:
                asset_data['all_data'] = {k: list(v) for k, v in asset_data['all_data'].items()}
                asset_data['source_tables'] = list(asset_data['source_tables'])
                
                asset_data['quality_metrics'] = self._calculate_asset_quality(asset_data)
                asset_data['enrichment_data'] = self._apply_intelligent_enrichment(asset_data)
                
                enriched_count += 1
                
            except Exception as e:
                logger.error(f"Asset enrichment failed for {asset_id}: {e}")
        
        logger.info(f"Enriched {enriched_count} assets")
        return enriched_count
    
    def _calculate_asset_quality(self, asset_data: Dict[str, Any]) -> Dict[str, float]:
        all_data = asset_data.get('all_data', {})
        coverage_flags = asset_data.get('coverage_flags', {})
        
        data_completeness = len([v for v in all_data.values() if v]) / max(len(self.field_mappings), 1)
        coverage_score = sum(1 for v in coverage_flags.values() if v) / max(len(coverage_flags), 1)
        source_reliability = min(1.0, asset_data.get('source_count', 0) / 3.0)
        
        overall_quality = (data_completeness * 0.4 + coverage_score * 0.4 + source_reliability * 0.2)
        
        return {
            'data_completeness': data_completeness,
            'coverage_score': coverage_score,
            'source_reliability': source_reliability,
            'overall_quality': overall_quality
        }
    
    def _apply_intelligent_enrichment(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        enrichment = {}
        hostname = asset_data.get('hostname', '')
        all_data = asset_data.get('all_data', {})
        
        hostname_lower = hostname.lower()
        
        cloud_indicators = {
            'aws': ['aws', 'ec2', 'amazon'],
            'azure': ['azure', 'microsoft'],
            'gcp': ['gcp', 'google', 'compute']
        }
        
        for provider, keywords in cloud_indicators.items():
            if any(keyword in hostname_lower for keyword in keywords):
                enrichment['cloud_provider'] = provider
                enrichment['infrastructure_type'] = 'cloud'
                break
        
        environment_indicators = {
            'production': ['prod', 'production', 'live', 'prd'],
            'development': ['dev', 'development', 'devel'],
            'test': ['test', 'testing', 'tst', 'qa'],
            'staging': ['stage', 'staging', 'stg', 'uat']
        }
        
        for env, keywords in environment_indicators.items():
            if any(keyword in hostname_lower for keyword in keywords):
                enrichment['environment'] = env
                break
        
        if 'region' in all_data and all_data['region']:
            enrichment['detected_region'] = True
        
        if 'business_unit' in all_data and all_data['business_unit']:
            enrichment['has_business_context'] = True
        
        return enrichment
    
    def get_discovery_summary(self) -> Dict[str, Any]:
        processing_time = (datetime.now() - self.processing_stats['start_time']).total_seconds()
        
        return {
            'engine_name': 'QuantumContentBasedEngine',
            'total_assets_discovered': len(self.discovered_assets),
            'processing_time_minutes': processing_time / 60,
            'assets_per_minute': len(self.discovered_assets) / (processing_time / 60) if processing_time > 0 else 0,
            'ml_enhancement_rate': (self.processing_stats['ml_predictions_made'] / max(self.processing_stats['columns_analyzed'], 1)) * 100,
            'high_confidence_rate': (self.processing_stats['high_confidence_predictions'] / max(self.processing_stats['ml_predictions_made'], 1)) * 100,
            'processing_stats': self.processing_stats,
            'field_mappings_used': len(self.field_mappings)
        }

class SmartColumnDetector:
    def __init__(self):
        self.hostname_patterns = [
            r'^[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$',
            r'^[a-zA-Z]{2,4}[0-9]{1,8}$'
        ]
        
        self.hostname_indicators = [
            'hostname', 'host', 'computer', 'machine', 'device', 'endpoint',
            'server', 'workstation', 'node', 'asset', 'equipment'
        ]
    
    def detect_hostname_columns(self, table_samples: Dict[str, List[str]]) -> List[Tuple[str, float]]:
        candidates = []
        
        for column_name, samples in table_samples.items():
            if not samples:
                continue
            
            name_score = self._score_column_name(column_name)
            content_score = self._score_content(samples)
            pattern_score = self._score_patterns(samples)
            
            combined_score = (name_score * 0.4 + content_score * 0.4 + pattern_score * 0.2)
            
            if combined_score > 0.5:
                candidates.append((column_name, combined_score))
        
        return sorted(candidates, key=lambda x: x[1], reverse=True)
    
    def _score_column_name(self, name: str) -> float:
        name_lower = name.lower()
        
        for indicator in self.hostname_indicators:
            if indicator in name_lower:
                return min(1.0, len(indicator) / len(name_lower))
        
        return 0.0
    
    def _score_content(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = 0
        for sample in samples[:25]:
            if self._looks_like_hostname(sample):
                hostname_count += 1
        
        return hostname_count / min(len(samples), 25)
    
    def _score_patterns(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        pattern_matches = 0
        for sample in samples[:20]:
            for pattern in self.hostname_patterns:
                if re.match(pattern, str(sample), re.IGNORECASE):
                    pattern_matches += 1
                    break
        
        return pattern_matches / min(len(samples), 20)
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        for pattern in self.hostname_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                return True
        
        return False

ContentBasedEngine = QuantumContentBasedEngine
UniversalTableScanner = QuantumContentBasedEngine