#!/usr/bin/env python3

import asyncio
import logging
import json
import hashlib
import re
import ipaddress
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, Counter
import statistics
import duckdb
import unicodedata

logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveAsset:
    master_asset_id: str
    hostname: str = ""
    normalized_hostname: str = ""
    hostname_variants: List[str] = field(default_factory=list)
    fqdn: str = ""
    ip_address: str = ""
    mac_address: str = ""
    infrastructure_type: str = ""
    system_classification: str = ""
    global_region: str = ""
    country: str = ""
    data_center: str = ""
    cloud_region: str = ""
    business_unit: str = ""
    cio: str = ""
    apm: str = ""
    application_class: str = ""
    found_in_original_cmdb: bool = False
    found_in_splunk: bool = False
    found_in_chronicle: bool = False
    found_in_crowdstrike: bool = False
    edr_coverage: bool = False
    tanium_coverage: bool = False
    dlp_coverage: bool = False
    network_log_types: str = ""
    endpoint_log_types: str = ""
    cloud_log_types: str = ""
    application_log_types: str = ""
    identity_log_types: str = ""
    source_tables: List[str] = field(default_factory=list)
    source_count: int = 0
    correlation_score: float = 0.0
    confidence_score: float = 0.0
    discovery_metadata: Dict[str, Any] = field(default_factory=dict)
    cross_table_matches: Dict[str, List[str]] = field(default_factory=dict)

class AdvancedHostnameNormalizer:
    def __init__(self):
        self.normalization_patterns = [
            (r'\..*$', ''),
            (r'[^a-zA-Z0-9\-]', ''),
            (r'\-+', '-'),
            (r'^-|-$', ''),
        ]
        
        self.variation_generators = [
            self._generate_domain_variants,
            self._generate_prefix_variants,
            self._generate_number_variants,
            self._generate_environment_variants
        ]
        
        self.common_prefixes = ['srv', 'web', 'app', 'db', 'sql', 'mail', 'dc', 'vm', 'host']
        self.common_suffixes = ['prod', 'dev', 'test', 'stage', 'uat', 'qa']
        self.environment_indicators = ['p', 'd', 't', 's', 'prod', 'dev', 'test', 'stage']
        
    def normalize_hostname(self, hostname: str) -> str:
        if not hostname:
            return ""
        
        normalized = hostname.strip().upper()
        normalized = unicodedata.normalize('NFKD', normalized)
        normalized = ''.join(c for c in normalized if ord(c) < 128)
        
        for pattern, replacement in self.normalization_patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized
    
    def generate_hostname_variants(self, hostname: str) -> List[str]:
        if not hostname:
            return []
        
        variants = set()
        base_hostname = self.normalize_hostname(hostname)
        variants.add(base_hostname)
        
        for generator in self.variation_generators:
            variants.update(generator(base_hostname))
        
        return list(variants)
    
    def _generate_domain_variants(self, hostname: str) -> Set[str]:
        variants = set()
        if '.' in hostname:
            parts = hostname.split('.')
            variants.add(parts[0])
            if len(parts) > 2:
                variants.add('.'.join(parts[:2]))
        return variants
    
    def _generate_prefix_variants(self, hostname: str) -> Set[str]:
        variants = set()
        for prefix in self.common_prefixes:
            if hostname.lower().startswith(prefix):
                variants.add(hostname[len(prefix):])
                if hostname[len(prefix):len(prefix)+1] in ['-', '_']:
                    variants.add(hostname[len(prefix)+1:])
        return variants
    
    def _generate_number_variants(self, hostname: str) -> Set[str]:
        variants = set()
        number_pattern = r'(\d+)$'
        match = re.search(number_pattern, hostname)
        if match:
            base = hostname[:match.start()]
            variants.add(base)
            number = int(match.group(1))
            for i in range(max(1, number-5), number+6):
                if i != number:
                    variants.add(f"{base}{i:02d}")
                    variants.add(f"{base}{i}")
        return variants
    
    def _generate_environment_variants(self, hostname: str) -> Set[str]:
        variants = set()
        for env in self.environment_indicators:
            if hostname.lower().endswith(env):
                base = hostname[:-len(env)]
                if base.endswith('-') or base.endswith('_'):
                    base = base[:-1]
                variants.add(base)
        return variants
    
    def calculate_hostname_similarity(self, hostname1: str, hostname2: str) -> float:
        if not hostname1 or not hostname2:
            return 0.0
        
        norm1 = self.normalize_hostname(hostname1)
        norm2 = self.normalize_hostname(hostname2)
        
        if norm1 == norm2:
            return 1.0
        
        variants1 = self.generate_hostname_variants(hostname1)
        variants2 = self.generate_hostname_variants(hostname2)
        
        for v1 in variants1:
            for v2 in variants2:
                if v1 == v2 and len(v1) > 3:
                    return 0.9
        
        if len(norm1) > 4 and len(norm2) > 4:
            if norm1 in norm2 or norm2 in norm1:
                return 0.7
        
        common_chars = sum(1 for c in norm1 if c in norm2)
        max_len = max(len(norm1), len(norm2))
        return common_chars / max_len if max_len > 0 else 0.0

class AggressiveCrossTableCorrelator:
    def __init__(self, hostname_normalizer):
        self.hostname_normalizer = hostname_normalizer
        self.correlation_cache = {}
        self.network_correlations = defaultdict(set)
        self.business_correlations = defaultdict(set)
        self.temporal_correlations = defaultdict(set)
        
    def correlate_across_tables(self, assets: Dict[str, ComprehensiveAsset]) -> Dict[str, ComprehensiveAsset]:
        correlated_assets = {}
        
        hostname_groups = self._group_by_hostname_similarity(assets)
        ip_groups = self._group_by_ip_similarity(assets)
        network_groups = self._group_by_network_proximity(assets)
        business_groups = self._group_by_business_context(assets)
        
        all_groups = [hostname_groups, ip_groups, network_groups, business_groups]
        
        processed_ids = set()
        
        for groups in all_groups:
            for group in groups:
                if len(group) <= 1:
                    continue
                
                primary_asset = self._select_primary_asset(group, assets)
                if primary_asset.master_asset_id in processed_ids:
                    continue
                
                merged_asset = primary_asset
                for asset_id in group:
                    if asset_id != primary_asset.master_asset_id and asset_id not in processed_ids:
                        secondary_asset = assets[asset_id]
                        merged_asset = self._merge_correlated_assets(merged_asset, secondary_asset)
                        processed_ids.add(asset_id)
                
                merged_asset.correlation_score = self._calculate_correlation_confidence(group, assets)
                correlated_assets[merged_asset.master_asset_id] = merged_asset
                processed_ids.add(merged_asset.master_asset_id)
        
        for asset_id, asset in assets.items():
            if asset_id not in processed_ids:
                correlated_assets[asset_id] = asset
        
        return correlated_assets
    
    def _group_by_hostname_similarity(self, assets: Dict[str, ComprehensiveAsset]) -> List[List[str]]:
        groups = []
        processed = set()
        
        for asset_id, asset in assets.items():
            if asset_id in processed or not asset.hostname:
                continue
            
            group = [asset_id]
            processed.add(asset_id)
            
            for other_id, other_asset in assets.items():
                if other_id in processed or not other_asset.hostname:
                    continue
                
                similarity = self.hostname_normalizer.calculate_hostname_similarity(
                    asset.hostname, other_asset.hostname
                )
                
                if similarity >= 0.8:
                    group.append(other_id)
                    processed.add(other_id)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _group_by_ip_similarity(self, assets: Dict[str, ComprehensiveAsset]) -> List[List[str]]:
        ip_groups = defaultdict(list)
        
        for asset_id, asset in assets.items():
            if asset.ip_address:
                try:
                    ip = ipaddress.ip_address(asset.ip_address)
                    if ip.version == 4:
                        subnet = str(ipaddress.ip_network(f"{ip}/24", strict=False).network_address)
                        ip_groups[subnet].append(asset_id)
                except:
                    continue
        
        return [group for group in ip_groups.values() if len(group) > 1]
    
    def _group_by_network_proximity(self, assets: Dict[str, ComprehensiveAsset]) -> List[List[str]]:
        network_groups = defaultdict(list)
        
        for asset_id, asset in assets.items():
            network_key = self._generate_network_key(asset)
            if network_key:
                network_groups[network_key].append(asset_id)
        
        return [group for group in network_groups.values() if len(group) > 1]
    
    def _group_by_business_context(self, assets: Dict[str, ComprehensiveAsset]) -> List[List[str]]:
        business_groups = defaultdict(list)
        
        for asset_id, asset in assets.items():
            business_key = f"{asset.business_unit}:{asset.global_region}:{asset.infrastructure_type}"
            if business_key != "::":
                business_groups[business_key].append(asset_id)
        
        return [group for group in business_groups.values() if len(group) > 3]
    
    def _generate_network_key(self, asset: ComprehensiveAsset) -> str:
        key_parts = []
        
        if asset.fqdn:
            domain_parts = asset.fqdn.split('.')
            if len(domain_parts) > 1:
                key_parts.append('.'.join(domain_parts[-2:]))
        
        if asset.data_center:
            key_parts.append(asset.data_center)
        
        if asset.cloud_region:
            key_parts.append(asset.cloud_region)
        
        return ':'.join(key_parts) if key_parts else ""
    
    def _select_primary_asset(self, group: List[str], assets: Dict[str, ComprehensiveAsset]) -> ComprehensiveAsset:
        group_assets = [assets[asset_id] for asset_id in group]
        
        scored_assets = []
        for asset in group_assets:
            score = 0
            score += asset.source_count * 10
            score += len([f for f in [asset.hostname, asset.ip_address, asset.fqdn] if f]) * 5
            score += asset.confidence_score * 20
            if asset.found_in_original_cmdb:
                score += 50
            scored_assets.append((score, asset))
        
        return max(scored_assets, key=lambda x: x[0])[1]
    
    def _merge_correlated_assets(self, primary: ComprehensiveAsset, secondary: ComprehensiveAsset) -> ComprehensiveAsset:
        merged = ComprehensiveAsset(master_asset_id=primary.master_asset_id)
        
        string_fields = [
            'hostname', 'fqdn', 'ip_address', 'mac_address', 'infrastructure_type',
            'system_classification', 'global_region', 'country', 'data_center',
            'cloud_region', 'business_unit', 'cio', 'apm', 'application_class',
            'network_log_types', 'endpoint_log_types', 'cloud_log_types',
            'application_log_types', 'identity_log_types'
        ]
        
        for field in string_fields:
            primary_val = getattr(primary, field, "")
            secondary_val = getattr(secondary, field, "")
            
            if primary_val and secondary_val:
                if len(primary_val) >= len(secondary_val):
                    setattr(merged, field, primary_val)
                else:
                    setattr(merged, field, secondary_val)
            elif primary_val:
                setattr(merged, field, primary_val)
            elif secondary_val:
                setattr(merged, field, secondary_val)
            else:
                setattr(merged, field, "")
        
        boolean_fields = [
            'found_in_original_cmdb', 'found_in_splunk', 'found_in_chronicle',
            'found_in_crowdstrike', 'edr_coverage', 'tanium_coverage', 'dlp_coverage'
        ]
        
        for field in boolean_fields:
            primary_val = getattr(primary, field, False)
            secondary_val = getattr(secondary, field, False)
            setattr(merged, field, primary_val or secondary_val)
        
        merged.source_tables = list(set(primary.source_tables + secondary.source_tables))
        merged.source_count = primary.source_count + secondary.source_count
        merged.confidence_score = max(primary.confidence_score, secondary.confidence_score)
        
        merged.cross_table_matches = {**primary.cross_table_matches, **secondary.cross_table_matches}
        
        return merged
    
    def _calculate_correlation_confidence(self, group: List[str], assets: Dict[str, ComprehensiveAsset]) -> float:
        if len(group) <= 1:
            return 0.0
        
        confidence_factors = []
        
        hostname_similarities = []
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                asset1 = assets[group[i]]
                asset2 = assets[group[j]]
                if asset1.hostname and asset2.hostname:
                    sim = self.hostname_normalizer.calculate_hostname_similarity(
                        asset1.hostname, asset2.hostname
                    )
                    hostname_similarities.append(sim)
        
        if hostname_similarities:
            confidence_factors.append(statistics.mean(hostname_similarities))
        
        source_diversity = len(set(assets[aid].source_tables[0].split('.')[0] 
                                 for aid in group if assets[aid].source_tables))
        confidence_factors.append(min(1.0, source_diversity / 2.0))
        
        field_overlap = 0
        total_comparisons = 0
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                asset1 = assets[group[i]]
                asset2 = assets[group[j]]
                
                shared_fields = 0
                compared_fields = 0
                
                for field in ['ip_address', 'fqdn', 'business_unit', 'global_region']:
                    val1 = getattr(asset1, field, "")
                    val2 = getattr(asset2, field, "")
                    if val1 and val2:
                        compared_fields += 1
                        if val1 == val2:
                            shared_fields += 1
                
                if compared_fields > 0:
                    field_overlap += shared_fields / compared_fields
                    total_comparisons += 1
        
        if total_comparisons > 0:
            confidence_factors.append(field_overlap / total_comparisons)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5

class ComprehensiveTableScanner:
    def __init__(self, content_matcher, hostname_normalizer):
        self.content_matcher = content_matcher
        self.hostname_normalizer = hostname_normalizer
        self.scan_cache = {}
        self.table_quality_scores = {}
        
    async def scan_all_tables_in_projects(self, projects: List[str], client_managers: Dict[str, Any]) -> Dict[str, ComprehensiveAsset]:
        all_assets = {}
        
        for project_id in projects:
            client_manager = client_managers.get(project_id)
            if not client_manager:
                continue
            
            logger.info(f"Scanning all tables in project {project_id}")
            project_assets = await self._scan_project_completely(project_id, client_manager)
            
            for asset_id, asset in project_assets.items():
                if asset_id in all_assets:
                    all_assets[asset_id] = self._merge_project_assets(all_assets[asset_id], asset)
                else:
                    all_assets[asset_id] = asset
        
        return all_assets
    
    async def _scan_project_completely(self, project_id: str, client_manager) -> Dict[str, ComprehensiveAsset]:
        project_assets = {}
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            for dataset in datasets:
                dataset_id = dataset.dataset_id
                logger.info(f"Scanning dataset {project_id}.{dataset_id}")
                
                try:
                    dataset_ref = client.dataset(dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    
                    for table_ref in tables:
                        table_id = table_ref.table_id
                        table_path = f"{project_id}.{dataset_id}.{table_id}"
                        
                        try:
                            table_assets = await self._scan_table_for_assets(client, table_path)
                            
                            for asset_id, asset in table_assets.items():
                                if asset_id in project_assets:
                                    project_assets[asset_id] = self._merge_table_assets(
                                        project_assets[asset_id], asset
                                    )
                                else:
                                    project_assets[asset_id] = asset
                        
                        except Exception as e:
                            logger.warning(f"Failed to scan table {table_path}: {e}")
                            continue
                
                except Exception as e:
                    logger.warning(f"Failed to access dataset {dataset_id}: {e}")
                    continue
        
        return project_assets
    
    async def _scan_table_for_assets(self, client, table_path: str) -> Dict[str, ComprehensiveAsset]:
        cache_key = f"table_scan:{table_path}"
        if cache_key in self.scan_cache:
            return self.scan_cache[cache_key]
        
        assets = {}
        
        try:
            table_ref = client.get_table(table_path)
            
            if not table_ref.schema or table_ref.num_rows == 0:
                return assets
            
            columns = [field.name for field in table_ref.schema]
            
            sample_query = f"""
            SELECT {', '.join([f'`{col}`' for col in columns[:30]])}
            FROM `{table_path}`
            WHERE RAND() < 0.1
            LIMIT 1000
            """
            
            job = client.query(sample_query)
            results = list(job.result())
            
            if not results:
                return assets
            
            column_samples = {}
            for col_idx, column_name in enumerate(columns[:30]):
                sample_values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        sample_values.append(str(row[col_idx]))
                column_samples[column_name] = sample_values[:20]
            
            field_mappings = {}
            for column_name, samples in column_samples.items():
                analysis = self.content_matcher.analyze_column_intelligently(column_name, samples)
                if analysis:
                    field_type, confidence, metadata = analysis
                    if confidence > 0.5:
                        field_mappings[field_type] = column_name
            
            if 'hostname' not in field_mappings:
                hostname_candidates = self._find_hostname_candidates(column_samples)
                if hostname_candidates:
                    field_mappings['hostname'] = hostname_candidates[0][0]
            
            if 'hostname' in field_mappings:
                hostname_col = field_mappings['hostname']
                
                extraction_query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{hostname_col}` IS NOT NULL
                AND TRIM(`{hostname_col}`) != ''
                LIMIT 100000
                """
                
                extract_job = client.query(extraction_query)
                extract_results = list(extract_job.result())
                
                all_columns = [field.name for field in table_ref.schema]
                
                for row in extract_results:
                    hostname_idx = all_columns.index(hostname_col)
                    if hostname_idx < len(row) and row[hostname_idx]:
                        hostname = str(row[hostname_idx]).strip()
                        
                        if not self._is_valid_hostname_candidate(hostname):
                            continue
                        
                        normalized_hostname = self.hostname_normalizer.normalize_hostname(hostname)
                        hostname_variants = self.hostname_normalizer.generate_hostname_variants(hostname)
                        
                        asset_id = f"asset_{hashlib.md5(normalized_hostname.encode()).hexdigest()[:12]}"
                        
                        asset = ComprehensiveAsset(
                            master_asset_id=asset_id,
                            hostname=hostname.upper(),
                            normalized_hostname=normalized_hostname,
                            hostname_variants=hostname_variants
                        )
                        
                        for field_type, column_name in field_mappings.items():
                            if field_type != 'hostname':
                                col_idx = all_columns.index(column_name)
                                if col_idx < len(row) and row[col_idx]:
                                    value = str(row[col_idx]).strip()
                                    if value and len(value) > 0:
                                        setattr(asset, field_type, value)
                        
                        self._set_source_flags(asset, table_path)
                        asset.source_tables = [table_path]
                        asset.source_count = 1
                        asset.confidence_score = field_mappings.get('hostname', 0.5)
                        
                        if asset_id in assets:
                            assets[asset_id] = self._merge_table_assets(assets[asset_id], asset)
                        else:
                            assets[asset_id] = asset
            
            self.scan_cache[cache_key] = assets
            
        except Exception as e:
            logger.error(f"Table scan failed for {table_path}: {e}")
        
        return assets
    
    def _find_hostname_candidates(self, column_samples: Dict[str, List[str]]) -> List[Tuple[str, float]]:
        candidates = []
        
        for column_name, samples in column_samples.items():
            if not samples:
                continue
            
            hostname_score = 0.0
            valid_hostnames = 0
            
            for sample in samples[:10]:
                if self._is_valid_hostname_candidate(str(sample)):
                    valid_hostnames += 1
            
            if len(samples) > 0:
                hostname_score = valid_hostnames / min(len(samples), 10)
            
            name_indicators = ['host', 'server', 'computer', 'endpoint', 'machine', 'device', 'asset']
            name_score = sum(1 for indicator in name_indicators if indicator in column_name.lower())
            
            total_score = hostname_score * 0.8 + (name_score / len(name_indicators)) * 0.2
            
            if total_score > 0.3:
                candidates.append((column_name, total_score))
        
        return sorted(candidates, key=lambda x: x[1], reverse=True)
    
    def _is_valid_hostname_candidate(self, value: str) -> bool:
        if not value or len(value) < 1 or len(value) > 253:
            return False
        
        if value.upper() in ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'EMPTY', '']:
            return False
        
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', value):
            return False
        
        if len(re.findall(r'[a-zA-Z]', value)) < 1:
            return False
        
        return True
    
    def _set_source_flags(self, asset: ComprehensiveAsset, table_path: str):
        table_lower = table_path.lower()
        
        if 'cmdb' in table_lower or 'endpoint' in table_lower:
            asset.found_in_original_cmdb = True
        elif 'splunk' in table_lower or 'spl_' in table_lower:
            asset.found_in_splunk = True
        elif 'chronicle' in table_lower:
            asset.found_in_chronicle = True
        elif 'crowdstrike' in table_lower or 'endpointagent' in table_lower:
            asset.found_in_crowdstrike = True
            asset.edr_coverage = True
    
    def _merge_table_assets(self, primary: ComprehensiveAsset, secondary: ComprehensiveAsset) -> ComprehensiveAsset:
        merged = ComprehensiveAsset(master_asset_id=primary.master_asset_id)
        
        string_fields = [
            'hostname', 'fqdn', 'ip_address', 'mac_address', 'infrastructure_type',
            'system_classification', 'global_region', 'country', 'data_center',
            'cloud_region', 'business_unit', 'cio', 'apm', 'application_class'
        ]
        
        for field in string_fields:
            primary_val = getattr(primary, field, "")
            secondary_val = getattr(secondary, field, "")
            
            if primary_val and secondary_val:
                setattr(merged, field, primary_val if len(primary_val) >= len(secondary_val) else secondary_val)
            else:
                setattr(merged, field, primary_val or secondary_val)
        
        boolean_fields = [
            'found_in_original_cmdb', 'found_in_splunk', 'found_in_chronicle',
            'found_in_crowdstrike', 'edr_coverage', 'tanium_coverage', 'dlp_coverage'
        ]
        
        for field in boolean_fields:
            primary_val = getattr(primary, field, False)
            secondary_val = getattr(secondary, field, False)
            setattr(merged, field, primary_val or secondary_val)
        
        merged.hostname_variants = list(set(primary.hostname_variants + secondary.hostname_variants))
        merged.source_tables = list(set(primary.source_tables + secondary.source_tables))
        merged.source_count = primary.source_count + secondary.source_count
        merged.confidence_score = max(primary.confidence_score, secondary.confidence_score)
        merged.normalized_hostname = primary.normalized_hostname or secondary.normalized_hostname
        
        return merged
    
    def _merge_project_assets(self, primary: ComprehensiveAsset, secondary: ComprehensiveAsset) -> ComprehensiveAsset:
        return self._merge_table_assets(primary, secondary)

class UltimateCMDBBuilder:
    def __init__(self, config: Dict[str, Any], content_matcher, cache_manager):
        self.config = config
        self.content_matcher = content_matcher
        self.cache_manager = cache_manager
        
        self.hostname_normalizer = AdvancedHostnameNormalizer()
        self.table_scanner = ComprehensiveTableScanner(content_matcher, self.hostname_normalizer)
        self.correlator = AggressiveCrossTableCorrelator(self.hostname_normalizer)
        
        self.db_path = config.get('database_path', 'ultimate_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        
        self._setup_ultimate_schema()
    
    def _setup_ultimate_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS ultimate_cmdb")
        
        self.conn.execute("""
            CREATE TABLE ultimate_cmdb (
                master_asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                normalized_hostname VARCHAR,
                hostname_variants JSON,
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
                found_in_original_cmdb BOOLEAN DEFAULT FALSE,
                found_in_splunk BOOLEAN DEFAULT FALSE,
                found_in_chronicle BOOLEAN DEFAULT FALSE,
                found_in_crowdstrike BOOLEAN DEFAULT FALSE,
                edr_coverage BOOLEAN DEFAULT FALSE,
                tanium_coverage BOOLEAN DEFAULT FALSE,
                dlp_coverage BOOLEAN DEFAULT FALSE,
                network_log_types VARCHAR,
                endpoint_log_types VARCHAR,
                cloud_log_types VARCHAR,
                application_log_types VARCHAR,
                identity_log_types VARCHAR,
                source_tables JSON,
                source_count INTEGER DEFAULT 0,
                correlation_score DOUBLE DEFAULT 0.0,
                confidence_score DOUBLE DEFAULT 0.0,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
    
    async def build_ultimate_cmdb(self, projects: List[str], client_managers: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Building ultimate CMDB from all tables in all projects")
        start_time = datetime.now()
        
        logger.info("Phase 1: Comprehensive table scanning")
        all_assets = await self.table_scanner.scan_all_tables_in_projects(projects, client_managers)
        
        logger.info(f"Phase 2: Cross-table correlation of {len(all_assets)} assets")
        correlated_assets = self.correlator.correlate_across_tables(all_assets)
        
        logger.info("Phase 3: Storing ultimate CMDB")
        stored_count = await self._store_ultimate_assets(correlated_assets)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        visibility_stats = self._calculate_visibility_statistics(correlated_assets)
        
        return {
            'total_assets_discovered': len(all_assets),
            'correlated_assets': len(correlated_assets),
            'stored_assets': stored_count,
            'processing_time_seconds': processing_time,
            'visibility_statistics': visibility_stats,
            'database_path': self.db_path
        }
    
    async def _store_ultimate_assets(self, assets: Dict[str, ComprehensiveAsset]) -> int:
        stored_count = 0
        
        insert_query = """
        INSERT INTO ultimate_cmdb (
            master_asset_id, hostname, normalized_hostname, hostname_variants,
            fqdn, ip_address, mac_address, infrastructure_type, system_classification,
            global_region, country, data_center, cloud_region, business_unit,
            cio, apm, application_class, found_in_original_cmdb, found_in_splunk,
            found_in_chronicle, found_in_crowdstrike, edr_coverage, tanium_coverage,
            dlp_coverage, network_log_types, endpoint_log_types, cloud_log_types,
            application_log_types, identity_log_types, source_tables, source_count,
            correlation_score, confidence_score, discovery_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
        """
        
        for asset in assets.values():
            try:
                values = [
                    asset.master_asset_id, asset.hostname, asset.normalized_hostname,
                    json.dumps(asset.hostname_variants), asset.fqdn, asset.ip_address,
                    asset.mac_address, asset.infrastructure_type, asset.system_classification,
                    asset.global_region, asset.country, asset.data_center, asset.cloud_region,
                    asset.business_unit, asset.cio, asset.apm, asset.application_class,
                    asset.found_in_original_cmdb, asset.found_in_splunk, asset.found_in_chronicle,
                    asset.found_in_crowdstrike, asset.edr_coverage, asset.tanium_coverage,
                    asset.dlp_coverage, asset.network_log_types, asset.endpoint_log_types,
                    asset.cloud_log_types, asset.application_log_types, asset.identity_log_types,
                    json.dumps(asset.source_tables), asset.source_count, asset.correlation_score,
                    asset.confidence_score
                ]
                
                self.conn.execute(insert_query, values)
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store asset {asset.master_asset_id}: {e}")
        
        self.conn.commit()
        return stored_count
    
    def _calculate_visibility_statistics(self, assets: Dict[str, ComprehensiveAsset]) -> Dict[str, Any]:
        total_assets = len(assets)
        
        if total_assets == 0:
            return {}
        
        cmdb_coverage = sum(1 for asset in assets.values() if asset.found_in_original_cmdb)
        splunk_coverage = sum(1 for asset in assets.values() if asset.found_in_splunk)
        chronicle_coverage = sum(1 for asset in assets.values() if asset.found_in_chronicle)
        crowdstrike_coverage = sum(1 for asset in assets.values() if asset.found_in_crowdstrike)
        
        multi_source = sum(1 for asset in assets.values() if asset.source_count > 1)
        high_correlation = sum(1 for asset in assets.values() if asset.correlation_score > 0.8)
        
        source_combinations = defaultdict(int)
        for asset in assets.values():
            sources = []
            if asset.found_in_original_cmdb:
                sources.append('CMDB')
            if asset.found_in_splunk:
                sources.append('Splunk')
            if asset.found_in_chronicle:
                sources.append('Chronicle')
            if asset.found_in_crowdstrike:
                sources.append('CrowdStrike')
            
            combination = '+'.join(sorted(sources)) if sources else 'None'
            source_combinations[combination] += 1
        
        return {
            'total_assets': total_assets,
            'cmdb_coverage': {
                'count': cmdb_coverage,
                'percentage': (cmdb_coverage / total_assets) * 100
            },
            'splunk_coverage': {
                'count': splunk_coverage,
                'percentage': (splunk_coverage / total_assets) * 100
            },
            'chronicle_coverage': {
                'count': chronicle_coverage,
                'percentage': (chronicle_coverage / total_assets) * 100
            },
            'crowdstrike_coverage': {
                'count': crowdstrike_coverage,
                'percentage': (crowdstrike_coverage / total_assets) * 100
            },
            'multi_source_assets': {
                'count': multi_source,
                'percentage': (multi_source / total_assets) * 100
            },
            'high_correlation_assets': {
                'count': high_correlation,
                'percentage': (high_correlation / total_assets) * 100
            },
            'source_combinations': dict(source_combinations),
            'visibility_gaps': {
                'not_in_cmdb': total_assets - cmdb_coverage,
                'not_in_any_log_source': total_assets - (splunk_coverage + chronicle_coverage),
                'no_security_coverage': total_assets - crowdstrike_coverage
            }
        }
    
    def get_visibility_queries(self) -> Dict[str, str]:
        return {
            'total_assets': "SELECT COUNT(*) as total_assets FROM ultimate_cmdb;",
            
            'visibility_summary': """
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN found_in_original_cmdb THEN 1 ELSE 0 END) as in_cmdb,
                    SUM(CASE WHEN found_in_splunk THEN 1 ELSE 0 END) as in_splunk,
                    SUM(CASE WHEN found_in_chronicle THEN 1 ELSE 0 END) as in_chronicle,
                    SUM(CASE WHEN found_in_crowdstrike THEN 1 ELSE 0 END) as in_crowdstrike,
                    SUM(CASE WHEN source_count > 1 THEN 1 ELSE 0 END) as multi_source
                FROM ultimate_cmdb;
            """,
            
            'coverage_percentages': """
                SELECT 
                    ROUND((SUM(CASE WHEN found_in_original_cmdb THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as cmdb_percentage,
                    ROUND((SUM(CASE WHEN found_in_splunk THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as splunk_percentage,
                    ROUND((SUM(CASE WHEN found_in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as chronicle_percentage,
                    ROUND((SUM(CASE WHEN found_in_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as crowdstrike_percentage
                FROM ultimate_cmdb;
            """,
            
            'missing_from_cmdb': """
                SELECT hostname, ip_address, infrastructure_type, source_count, source_tables
                FROM ultimate_cmdb 
                WHERE NOT found_in_original_cmdb 
                ORDER BY source_count DESC, correlation_score DESC
                LIMIT 100;
            """,
            
            'visibility_gaps': """
                SELECT hostname, 
                       found_in_original_cmdb as in_cmdb,
                       found_in_splunk as in_splunk,
                       found_in_chronicle as in_chronicle,
                       found_in_crowdstrike as in_crowdstrike,
                       source_count
                FROM ultimate_cmdb 
                WHERE source_count = 1
                ORDER BY hostname;
            """,
            
            'best_visibility': """
                SELECT hostname, ip_address, infrastructure_type, business_unit,
                       found_in_original_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike,
                       source_count, correlation_score
                FROM ultimate_cmdb 
                WHERE source_count >= 3
                ORDER BY correlation_score DESC, source_count DESC
                LIMIT 50;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()