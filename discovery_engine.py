#!/usr/bin/env python3

import os
import asyncio
import logging
import duckdb
import time
import threading
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import networkx as nx
import ipaddress
import re
import json
import hashlib
from typing import Dict, List, Any, Tuple, Set, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import statistics
from itertools import combinations
import pickle

from gcp_client import BigQueryClientManager
from intelligent_content_matcher import IntelligentContentMatcher
from intelligent_cache_manager import IntelligentCacheManager
from progress_tracker import ProgressTracker
from checkpoint_manager import CheckpointManager
from signal_handler import SignalHandler

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

logger = logging.getLogger(__name__)

class PrettyLogger:
    @staticmethod
    def info(msg: str):
        print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   {msg}")
    
    @staticmethod
    def success(msg: str):
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   {msg}")
    
    @staticmethod
    def warning(msg: str):
        print(f"   ⚠°｡⋆⸜ ♡   {msg}")
    
    @staticmethod
    def error(msg: str):
        print(f"   ✗°｡⋆⸜ ♡   {msg}")

@dataclass
class HostFingerprint:
    primary_id: str
    normalized_hostnames: Set[str]
    ip_addresses: Set[str]
    mac_addresses: Set[str]
    domain_names: Set[str]
    serial_numbers: Set[str]
    asset_tags: Set[str]
    network_segments: Set[str]
    temporal_signatures: List[datetime]
    semantic_patterns: Dict[str, float]
    confidence_score: float = 0.0
    source_tables: Set[str] = None
    
    def __post_init__(self):
        if self.source_tables is None:
            self.source_tables = set()

class CrossTableDataEnrichment:
    def __init__(self, client_manager: BigQueryClientManager, matcher: IntelligentContentMatcher):
        self.client_manager = client_manager
        self.matcher = matcher
        self.hostname_to_tables = defaultdict(set)
        self.field_mappings = {}
        self.enrichment_cache = {}
        
    def build_hostname_table_mapping(self, all_table_metadata: List[Dict]) -> Dict[str, Set[str]]:
        PrettyLogger.info("Building hostname to table mapping for cross-enrichment")
        
        hostname_mapping = defaultdict(set)
        
        for table_meta in all_table_metadata:
            hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
            if not hostname_column:
                continue
                
            sample_data = table_meta.get('sample_data', {})
            hostnames = sample_data.get(hostname_column, [])
            table_path = table_meta['full_table_path']
            
            for hostname in hostnames:
                normalized = self._normalize_hostname(hostname)
                if normalized:
                    hostname_mapping[normalized].add(table_path)
        
        PrettyLogger.success(f"Mapped {len(hostname_mapping)} hostnames across tables")
        return dict(hostname_mapping)
    
    def _normalize_hostname(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.strip().upper()
        if len(normalized) < 2 or len(normalized) > 253:
            return ""
        
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        
        normalized = re.sub(r'[^A-Z0-9\-]', '', normalized)
        return normalized if len(normalized) >= 2 else ""
    
    async def enrich_hostname_data(self, hostname: str, all_table_metadata: List[Dict]) -> Dict[str, Any]:
        cache_key = f"enrich:{hostname}"
        if cache_key in self.enrichment_cache:
            return self.enrichment_cache[cache_key]
        
        normalized_hostname = self._normalize_hostname(hostname)
        if not normalized_hostname:
            return {}
        
        enriched_data = {
            'fqdn': '',
            'ip_addresses': [],
            'mac_addresses': [],
            'infrastructure_type': '',
            'global_region': '',
            'country': '',
            'data_center': '',
            'cloud_region': '',
            'business_unit': '',
            'cio': '',
            'apm': '',
            'application_class': '',
            'environment': '',
            'in_splunk': False,
            'in_chronicle': False,
            'in_gso': False,
            'splunk_log_volume': 0,
            'chronicle_event_count': 0,
            'last_splunk_log': None,
            'last_chronicle_event': None,
            'has_edr': False,
            'has_tanium': False,
            'has_dlp': False,
            'has_crowdstrike': False,
            'agent_coverage_score': 0.0,
            'cmdb_last_updated': None,
            'data_quality_score': 0.0,
            'url_fqdn_coverage': False,
            'public_ip_space_mapped': False,
            'domain_visibility': '',
            'ao1_visibility_score': 0.0,
            'ao1_gap_severity': 'unknown',
            'ao1_recommendation': ''
        }
        
        hostname_variants = self._generate_hostname_variants(normalized_hostname)
        
        relevant_tables = []
        for table_meta in all_table_metadata:
            if self._table_contains_hostname(table_meta, hostname_variants):
                relevant_tables.append(table_meta)
        
        PrettyLogger.info(f"Found {len(relevant_tables)} tables containing hostname {normalized_hostname}")
        
        for table_meta in relevant_tables:
            table_enrichment = await self._extract_data_from_table(normalized_hostname, hostname_variants, table_meta)
            enriched_data = self._merge_enrichment_data(enriched_data, table_enrichment, table_meta)
        
        enriched_data = self._calculate_derived_metrics(enriched_data)
        
        self.enrichment_cache[cache_key] = enriched_data
        return enriched_data
    
    def _generate_hostname_variants(self, hostname: str) -> Set[str]:
        variants = {hostname}
        
        if '-' in hostname:
            variants.add(hostname.replace('-', ''))
            variants.add(hostname.replace('-', '_'))
        
        if '_' in hostname:
            variants.add(hostname.replace('_', ''))
            variants.add(hostname.replace('_', '-'))
        
        number_match = re.search(r'(\d+)$', hostname)
        if number_match:
            base = hostname[:number_match.start()]
            current_num = int(number_match.group(1))
            for offset in [-1, 1]:
                new_num = current_num + offset
                if new_num > 0:
                    new_variant = base + str(new_num).zfill(len(number_match.group(1)))
                    variants.add(new_variant)
        
        if len(hostname) > 8:
            variants.add(hostname[:8])
            variants.add(hostname[:10])
        
        return variants
    
    def _table_contains_hostname(self, table_meta: Dict, hostname_variants: Set[str]) -> bool:
        sample_data = table_meta.get('sample_data', {})
        hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
        
        if not hostname_column or hostname_column not in sample_data:
            return False
        
        hostnames_in_table = set()
        for hostname in sample_data[hostname_column]:
            normalized = self._normalize_hostname(hostname)
            if normalized:
                hostnames_in_table.add(normalized)
        
        return bool(hostname_variants & hostnames_in_table)
    
    async def _extract_data_from_table(self, target_hostname: str, hostname_variants: Set[str], table_meta: Dict) -> Dict[str, Any]:
        table_path = table_meta['full_table_path']
        hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
        column_analysis = table_meta.get('column_analysis', {})
        
        extraction_data = {}
        
        project_id = table_meta['project_id']
        client_mgr = self.client_manager
        
        if project_id == 'chronicle-fisv':
            try:
                from gcp_client import BigQueryClientManager
                client_mgr = BigQueryClientManager('chronicle-fisv')
            except:
                return extraction_data
        
        hostname_variants_list = list(hostname_variants)[:20]
        hostname_filter = "', '".join([h.replace("'", "''") for h in hostname_variants_list])
        
        select_fields = [f"UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname"]
        field_mappings = {}
        
        for column, analysis in column_analysis.items():
            if column == hostname_column:
                continue
            
            field_type, confidence, metadata = analysis
            if confidence > 0.3:
                safe_column = column.replace('`', '``')
                select_fields.append(f"CAST(`{safe_column}` AS STRING) as `{safe_column}`")
                field_mappings[safe_column] = field_type
        
        if len(select_fields) == 1:
            return extraction_data
        
        where_conditions = []
        where_conditions.append(f"UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) IN ('{hostname_filter}')")
        where_conditions.append(f"`{hostname_column}` IS NOT NULL")
        where_conditions.append(f"LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) >= 2")
        
        if table_meta.get('is_partitioned') and table_meta.get('partition_field'):
            partition_field = table_meta['partition_field']
            where_conditions.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)")
        
        query = f"""
        SELECT {', '.join(select_fields)}
        FROM `{table_path}`
        WHERE {' AND '.join(where_conditions)}
        LIMIT 100
        """
        
        try:
            with client_mgr.get_client() as client:
                job_config = bigquery.QueryJobConfig(
                    dry_run=True,
                    use_query_cache=False,
                    maximum_bytes_billed=100 * 1024 * 1024
                )
                
                dry_run_job = client.query(query, job_config=job_config)
                
                if dry_run_job.total_bytes_processed > 50 * 1024 * 1024:
                    PrettyLogger.warning(f"Skipping expensive query for {table_path}")
                    return extraction_data
                
                job_config = bigquery.QueryJobConfig(
                    dry_run=False,
                    use_query_cache=True,
                    maximum_bytes_billed=100 * 1024 * 1024
                )
                
                job = client.query(query, job_config=job_config)
                results = list(job.result())
                
                for row in results:
                    row_hostname = self._normalize_hostname(str(row[0])) if row[0] else ""
                    if row_hostname not in hostname_variants:
                        continue
                    
                    for i, field_name in enumerate(select_fields[1:], 1):
                        if i < len(row) and row[i]:
                            clean_field_name = field_name.split(' as ')[-1].strip('`')
                            field_type = field_mappings.get(clean_field_name, 'unknown')
                            value = str(row[i]).strip()
                            
                            if value and len(value) > 0 and value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE']:
                                if clean_field_name not in extraction_data:
                                    extraction_data[clean_field_name] = []
                                extraction_data[clean_field_name].append({
                                    'value': value,
                                    'field_type': field_type,
                                    'table_source': table_path
                                })
                
        except Exception as e:
            PrettyLogger.warning(f"Failed to extract from {table_path}: {e}")
        
        return extraction_data
    
    def _merge_enrichment_data(self, base_data: Dict, new_data: Dict, table_meta: Dict) -> Dict[str, Any]:
        table_path = table_meta['full_table_path']
        table_lower = table_path.lower()
        
        for field_name, field_entries in new_data.items():
            field_lower = field_name.lower()
            
            for entry in field_entries:
                value = entry['value']
                field_type = entry['field_type']
                
                if field_type == 'fqdn' or 'fqdn' in field_lower or 'dns' in field_lower:
                    if not base_data['fqdn'] and '.' in value:
                        base_data['fqdn'] = value
                
                elif field_type == 'ip_address' or 'ip' in field_lower:
                    if self._is_valid_ip(value):
                        if value not in base_data['ip_addresses']:
                            base_data['ip_addresses'].append(value)
                
                elif field_type == 'mac_address' or 'mac' in field_lower:
                    if self._is_valid_mac(value):
                        if value not in base_data['mac_addresses']:
                            base_data['mac_addresses'].append(value)
                
                elif field_type == 'region' or any(term in field_lower for term in ['region', 'location', 'geo', 'site']):
                    if not base_data['global_region']:
                        base_data['global_region'] = value
                
                elif 'country' in field_lower:
                    if not base_data['country']:
                        base_data['country'] = value
                
                elif any(term in field_lower for term in ['datacenter', 'data_center', 'dc']):
                    if not base_data['data_center']:
                        base_data['data_center'] = value
                
                elif 'cloud' in field_lower and 'region' in field_lower:
                    if not base_data['cloud_region']:
                        base_data['cloud_region'] = value
                
                elif field_type == 'business_unit' or any(term in field_lower for term in ['business', 'bu', 'org', 'department']):
                    if not base_data['business_unit']:
                        base_data['business_unit'] = value
                
                elif 'cio' in field_lower:
                    if not base_data['cio']:
                        base_data['cio'] = value
                
                elif 'apm' in field_lower:
                    if not base_data['apm']:
                        base_data['apm'] = value
                
                elif any(term in field_lower for term in ['application', 'app_class', 'class']):
                    if not base_data['application_class']:
                        base_data['application_class'] = value
                
                elif field_type == 'environment' or any(term in field_lower for term in ['env', 'stage', 'tier']):
                    if not base_data['environment']:
                        base_data['environment'] = value
                
                elif field_type == 'infrastructure_type' or any(term in field_lower for term in ['infra', 'type', 'platform']):
                    if not base_data['infrastructure_type']:
                        if any(infra_term in value.lower() for infra_term in ['physical', 'virtual', 'cloud', 'vm', 'container']):
                            base_data['infrastructure_type'] = value
        
        if 'splunk' in table_lower:
            base_data['in_splunk'] = True
            if 'volume' in table_lower or 'count' in table_lower:
                base_data['splunk_log_volume'] = max(base_data['splunk_log_volume'], 1000)
            base_data['last_splunk_log'] = datetime.now().isoformat()
        
        if 'chronicle' in table_lower:
            base_data['in_chronicle'] = True
            if 'event' in table_lower or 'count' in table_lower:
                base_data['chronicle_event_count'] = max(base_data['chronicle_event_count'], 500)
            base_data['last_chronicle_event'] = datetime.now().isoformat()
        
        if 'gso' in table_lower or 'security' in table_lower:
            base_data['in_gso'] = True
        
        if any(term in table_lower for term in ['crowdstrike', 'cs', 'falcon']):
            base_data['has_crowdstrike'] = True
            base_data['has_edr'] = True
        
        if 'tanium' in table_lower:
            base_data['has_tanium'] = True
        
        if 'dlp' in table_lower:
            base_data['has_dlp'] = True
        
        if any(term in table_lower for term in ['edr', 'endpoint']):
            base_data['has_edr'] = True
        
        return base_data
    
    def _is_valid_ip(self, value: str) -> bool:
        try:
            ipaddress.ip_address(value.strip())
            return True
        except ValueError:
            return False
    
    def _is_valid_mac(self, value: str) -> bool:
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$'
        ]
        return any(re.match(pattern, value.strip()) for pattern in mac_patterns)
    
    def _calculate_derived_metrics(self, data: Dict) -> Dict:
        security_tools = [data['has_crowdstrike'], data['has_tanium'], data['has_dlp'], data['has_edr']]
        data['agent_coverage_score'] = sum(security_tools) / len(security_tools) * 100
        
        visibility_factors = [
            data['in_splunk'],
            data['in_chronicle'], 
            data['in_gso'],
            bool(data['ip_addresses']),
            bool(data['fqdn'])
        ]
        data['ao1_visibility_score'] = sum(visibility_factors) / len(visibility_factors) * 100
        
        quality_factors = [
            bool(data['fqdn']),
            bool(data['ip_addresses']),
            bool(data['infrastructure_type']),
            bool(data['global_region']),
            bool(data['business_unit']),
            bool(data['environment'])
        ]
        data['data_quality_score'] = sum(quality_factors) / len(quality_factors) * 100
        
        data['url_fqdn_coverage'] = bool(data['fqdn'])
        data['public_ip_space_mapped'] = any(not ipaddress.ip_address(ip).is_private for ip in data['ip_addresses'] if self._is_valid_ip(ip))
        
        if data['fqdn']:
            data['domain_visibility'] = data['fqdn'].split('.', 1)[-1] if '.' in data['fqdn'] else ''
        
        if data['ao1_visibility_score'] >= 80:
            data['ao1_gap_severity'] = 'low'
            data['ao1_recommendation'] = 'Excellent visibility coverage maintained'
        elif data['ao1_visibility_score'] >= 60:
            data['ao1_gap_severity'] = 'medium'
            data['ao1_recommendation'] = 'Improve security tool coverage and log collection'
        else:
            data['ao1_gap_severity'] = 'high'
            data['ao1_recommendation'] = 'Critical visibility gaps - immediate attention required'
        
        data['cmdb_last_updated'] = datetime.now().isoformat()
        
        return data

class IntelligentHostnameNormalizer:
    @staticmethod
    def normalize_aggressively(hostname: str) -> str:
        if not hostname:
            return ""
        
        hostname = str(hostname).strip().upper()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return ""
        
        invalid_indicators = [
            '@', 'HTTP', 'HTTPS', 'UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 
            'TEST', 'EXAMPLE', 'LOCALHOST', 'DUMMY', 'SAMPLE', 'PLACEHOLDER'
        ]
        if any(indicator in hostname for indicator in invalid_indicators):
            return ""
        
        hostname = re.sub(r'^[^A-Z0-9]+', '', hostname)
        hostname = re.sub(r'[^A-Z0-9]+$', '', hostname)
        
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Z0-9\-]', '', hostname)
        
        if len(hostname) < 2:
            return ""
        
        return hostname

class IntelligentTableDiscovery:
    def __init__(self, matcher: IntelligentContentMatcher, cache: IntelligentCacheManager):
        self.matcher = matcher
        self.cache = cache
        self.table_metadata_cache = {}
        
    async def discover_intelligent_table_metadata(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        PrettyLogger.info(f"Discovering table structures in {project_id}")
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                PrettyLogger.info("Listing datasets...")
                datasets = list(client.list_datasets(project=project_id))
                PrettyLogger.success(f"Found {len(datasets)} datasets")
                
                if not datasets:
                    PrettyLogger.warning(f"No datasets found in {project_id}")
                    return []
                
                priority_datasets = self._prioritize_datasets([d.dataset_id for d in datasets])
                PrettyLogger.info(f"Analyzing {len(priority_datasets)} prioritized datasets")
                
                total_tables_found = 0
                total_intelligent_tables = 0
                
                for i, dataset_id in enumerate(priority_datasets):
                    try:
                        PrettyLogger.info(f"Dataset {i+1}/{len(priority_datasets)}: {dataset_id}")
                        
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        
                        try:
                            tables = list(client.list_tables(dataset_ref))
                            total_tables_found += len(tables)
                            PrettyLogger.info(f"  Found {len(tables)} tables")
                            
                            if not tables:
                                continue
                                
                        except Exception as e:
                            PrettyLogger.warning(f"  Cannot list tables in {dataset_id}: {e}")
                            continue
                        
                        dataset_intelligent_tables = 0
                        
                        for j, table_ref in enumerate(tables):
                            try:
                                if j > 0 and j % 20 == 0:
                                    PrettyLogger.info(f"    Analyzed {j}/{len(tables)} tables...")
                                
                                metadata = await self._analyze_table_intelligence(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                                    dataset_intelligent_tables += 1
                                    total_intelligent_tables += 1
                                    
                            except Exception as e:
                                continue
                        
                        if dataset_intelligent_tables > 0:
                            PrettyLogger.success(f"  {dataset_id}: {dataset_intelligent_tables} intelligent tables")
                        else:
                            PrettyLogger.info(f"  {dataset_id}: No intelligent tables found")
                            
                    except Exception as e:
                        PrettyLogger.warning(f"Dataset {dataset_id} analysis failed: {e}")
                        continue
                
                PrettyLogger.success(f"Discovery complete: {total_intelligent_tables} intelligent tables from {total_tables_found} total tables")
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=6)
        PrettyLogger.success(f"Cached {len(all_metadata)} intelligent table structures")
        
        return all_metadata
    
    def _prioritize_datasets(self, dataset_ids: List[str]) -> List[str]:
        priority_keywords = [
            ('cmdb', 100), ('endpoint', 95), ('asset', 90), ('inventory', 85),
            ('security', 80), ('crowdstrike', 75), ('splunk', 70), ('chronicle', 65),
            ('monitoring', 60), ('infrastructure', 55), ('network', 50), ('server', 45),
            ('gso', 40), ('tanium', 35), ('dlp', 30), ('edr', 25)
        ]
        
        scored_datasets = []
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for keyword, points in priority_keywords:
                if keyword in dataset_lower:
                    score += points
            
            scored_datasets.append((dataset_id, score))
        
        scored_datasets.sort(key=lambda x: x[1], reverse=True)
        return [dataset_id for dataset_id, _ in scored_datasets]
    
    async def _analyze_table_intelligence(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema:
                return None
                
            if full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_indicators = ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system']
            has_potential_hostname = any(
                any(indicator in col.lower() for indicator in hostname_indicators)
                for col in all_columns
            )
            
            if not has_potential_hostname:
                return None
            
            sample_data = await self._get_intelligent_sample(client, full_table)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            hostname_found = False
            
            for column in all_columns:
                samples = sample_data.get(column, [])
                if not samples:
                    continue
                    
                analysis = self.matcher.analyze_column_intelligently(column, samples)
                if analysis:
                    field_type, confidence, metadata = analysis
                    column_analysis[column] = analysis
                    
                    if field_type in ['hostname', 'fqdn'] and confidence > 0.3:
                        hostname_found = True
            
            if not hostname_found:
                return None
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_data_richness(column_analysis, sample_data)
            
            table_metadata = {
                'project_id': project_id,
                'dataset_id': table_ref.dataset_id,
                'table_id': table_ref.table_id,
                'full_table_path': f"{project_id}.{table_ref.dataset_id}.{table_ref.table_id}",
                'row_count': full_table.num_rows,
                'size_bytes': full_table.num_bytes or 0,
                'column_count': len(all_columns),
                'all_columns': all_columns,
                'column_analysis': column_analysis,
                'hostname_analysis': hostname_analysis,
                'data_richness_score': data_richness,
                'sample_data': sample_data,
                'is_partitioned': full_table.time_partitioning is not None,
                'partition_field': full_table.time_partitioning.field if full_table.time_partitioning else None
            }
            
            return table_metadata
            
        except Exception as e:
            return None
    
    async def _get_intelligent_sample(self, client, table_ref) -> Dict[str, List[str]]:
        try:
            sample_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                sample_query += f" WHERE `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
            
            sample_query += " LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            job = client.query(sample_query, job_config=job_config)
            
            job_config = bigquery.QueryJobConfig(dry_run=False, use_query_cache=True)
            job = client.query(sample_query, job_config=job_config)
            results = list(job.result())
            
            if not results:
                return {}
            
            sample_data = defaultdict(list)
            for row in results:
                for i, value in enumerate(row):
                    if i < len(table_ref.schema) and value is not None:
                        column_name = table_ref.schema[i].name
                        str_value = str(value)
                        if len(str_value) > 0 and len(str_value) < 500:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception as e:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_hostname_quality_score(samples)
                
                final_score = confidence * hostname_score
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_hostname_quality_score(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {
            'valid_hostnames': 0,
            'unique_ratio': 0,
            'length_consistency': 0,
            'pattern_consistency': 0
        }
        
        valid_count = sum(1 for sample in samples if self.matcher._validate_hostname(sample))
        quality_factors['valid_hostnames'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['unique_ratio'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            length_variance = max(lengths) - min(lengths)
            quality_factors['length_consistency'] = max(0, 1 - (length_variance / 20))
        
        pattern_score = self._analyze_hostname_patterns(samples)
        quality_factors['pattern_consistency'] = pattern_score
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _analyze_hostname_patterns(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        patterns = []
        for sample in samples:
            if not sample:
                continue
            
            pattern = ""
            for char in sample:
                if char.isalpha():
                    pattern += "A"
                elif char.isdigit():
                    pattern += "N"
                elif char in ['-', '_']:
                    pattern += "-"
                else:
                    pattern += "X"
            
            patterns.append(pattern)
        
        if not patterns:
            return 0.0
        
        pattern_counts = Counter(patterns)
        most_common_count = pattern_counts.most_common(1)[0][1]
        
        return most_common_count / len(patterns)
    
    def _calculate_data_richness(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {
            'identified_fields': len(column_analysis) / max(len(sample_data), 1),
            'high_confidence_fields': sum(1 for _, (_, conf, _) in column_analysis.items() if conf > 0.7) / len(column_analysis),
            'data_completeness': self._calculate_completeness(sample_data),
            'field_diversity': self._calculate_field_diversity(column_analysis)
        }
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(len([s for s in samples if s and str(s).strip()]) for samples in sample_data.values())
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _calculate_field_diversity(self, column_analysis: Dict[str, Tuple]) -> float:
        field_types = set()
        for _, (field_type, _, _) in column_analysis.items():
            if field_type:
                field_types.add(field_type)
        
        max_possible_types = len(self.matcher.semantic_patterns)
        return len(field_types) / max_possible_types

class IntelligentDataFusion:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_intelligence_tables()
        self._lock = threading.RLock()
        self.hostname_normalizer = IntelligentHostnameNormalizer()
        
    def _setup_intelligence_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS intelligent_endpoints (
            primary_hostname VARCHAR PRIMARY KEY,
            original_hostnames TEXT,
            hostname_variants TEXT,
            confidence_score DOUBLE DEFAULT 1.0,
            discovery_timestamp TIMESTAMP DEFAULT NOW(),
            last_seen TIMESTAMP DEFAULT NOW(),
            seen_count INTEGER DEFAULT 1
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS intelligent_endpoint_data (
            primary_hostname VARCHAR,
            field_name VARCHAR,
            field_value TEXT,
            data_source VARCHAR,
            table_source VARCHAR,
            confidence_score DOUBLE DEFAULT 1.0,
            validation_score DOUBLE DEFAULT 1.0,
            semantic_score DOUBLE DEFAULT 1.0,
            last_updated TIMESTAMP DEFAULT NOW(),
            update_count INTEGER DEFAULT 1,
            PRIMARY KEY (primary_hostname, field_name, data_source, table_source)
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS intelligent_asset_inventory (
            hostname VARCHAR PRIMARY KEY,
            fqdn VARCHAR,
            ip_addresses TEXT,
            mac_addresses TEXT,
            infrastructure_type VARCHAR,
            system_classification VARCHAR,
            operating_system VARCHAR,
            global_region VARCHAR,
            country VARCHAR,
            data_center VARCHAR,
            cloud_region VARCHAR,
            business_unit VARCHAR,
            cio VARCHAR,
            apm VARCHAR,
            application_class VARCHAR,
            cost_center VARCHAR,
            owner VARCHAR,
            environment VARCHAR,
            criticality VARCHAR,
            
            in_splunk BOOLEAN DEFAULT FALSE,
            in_chronicle BOOLEAN DEFAULT FALSE,
            in_gso BOOLEAN DEFAULT FALSE,
            has_crowdstrike BOOLEAN DEFAULT FALSE,
            found_in_cmdb BOOLEAN DEFAULT FALSE,
            
            splunk_log_volume INTEGER DEFAULT 0,
            chronicle_event_count INTEGER DEFAULT 0,
            last_splunk_log TIMESTAMP,
            last_chronicle_event TIMESTAMP,
            
            has_edr BOOLEAN DEFAULT FALSE,
            has_tanium BOOLEAN DEFAULT FALSE,
            has_dlp BOOLEAN DEFAULT FALSE,
            agent_coverage_score DOUBLE DEFAULT 0.0,
            
            cmdb_last_updated TIMESTAMP,
            data_quality_score DOUBLE DEFAULT 0.0,
            url_fqdn_coverage BOOLEAN DEFAULT FALSE,
            public_ip_space_mapped BOOLEAN DEFAULT FALSE,
            domain_visibility VARCHAR,
            ao1_visibility_score DOUBLE DEFAULT 0.0,
            ao1_gap_severity VARCHAR DEFAULT 'unknown',
            ao1_recommendation TEXT,
            
            source_systems TEXT,
            source_count INTEGER DEFAULT 0,
            data_completeness_score DOUBLE DEFAULT 0.0,
            intelligence_score DOUBLE DEFAULT 0.0,
            
            discovery_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW(),
            enrichment_metadata TEXT
        )
        """)
    
    def register_intelligent_endpoint(self, hostname: str, original_hostname: str = None) -> bool:
        primary_hostname = self.hostname_normalizer.normalize_aggressively(hostname)
        if not primary_hostname:
            return False
        
        with self._lock:
            try:
                existing = self.conn.execute("""
                    SELECT original_hostnames, hostname_variants, seen_count 
                    FROM intelligent_endpoints 
                    WHERE primary_hostname = ?
                """, (primary_hostname,)).fetchone()
                
                if existing:
                    orig_hostnames = set((existing[0] or "").split(","))
                    orig_variants = set((existing[1] or "").split(","))
                    seen_count = existing[2]
                    
                    if original_hostname:
                        orig_hostnames.add(original_hostname)
                    
                    self.conn.execute("""
                        UPDATE intelligent_endpoints 
                        SET original_hostnames = ?, hostname_variants = ?, 
                            last_seen = CURRENT_TIMESTAMP, seen_count = ?
                        WHERE primary_hostname = ?
                    """, (",".join(orig_hostnames), ",".join(orig_variants), seen_count + 1, primary_hostname))
                else:
                    self.conn.execute("""
                        INSERT INTO intelligent_endpoints 
                        (primary_hostname, original_hostnames, hostname_variants, confidence_score)
                        VALUES (?, ?, ?, ?)
                    """, (primary_hostname, original_hostname or hostname, "", 1.0))
                
                return True
                
            except Exception:
                return False
    
    def add_intelligent_data(self, hostname: str, field_name: str, field_value: str, 
                           data_source: str, table_source: str, 
                           confidence: float = 1.0, validation_score: float = 1.0,
                           semantic_score: float = 1.0) -> bool:
        primary_hostname = self.hostname_normalizer.normalize_aggressively(hostname)
        if not primary_hostname or not field_value or not field_value.strip():
            return False
        
        clean_value = str(field_value).strip()
        if not clean_value or clean_value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY']:
            return False
        
        with self._lock:
            try:
                existing = self.conn.execute("""
                    SELECT field_value, confidence_score, update_count
                    FROM intelligent_endpoint_data
                    WHERE primary_hostname = ? AND field_name = ? AND data_source = ? AND table_source = ?
                """, (primary_hostname, field_name, data_source, table_source)).fetchone()
                
                if existing:
                    existing_value, existing_confidence, update_count = existing
                    
                    if clean_value != existing_value and confidence > existing_confidence:
                        self.conn.execute("""
                            UPDATE intelligent_endpoint_data
                            SET field_value = ?, confidence_score = ?, validation_score = ?,
                                semantic_score = ?, last_updated = CURRENT_TIMESTAMP, update_count = ?
                            WHERE primary_hostname = ? AND field_name = ? AND data_source = ? AND table_source = ?
                        """, (clean_value, confidence, validation_score, semantic_score, 
                              update_count + 1, primary_hostname, field_name, data_source, table_source))
                else:
                    self.conn.execute("""
                        INSERT INTO intelligent_endpoint_data
                        (primary_hostname, field_name, field_value, data_source, table_source,
                         confidence_score, validation_score, semantic_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (primary_hostname, field_name, clean_value, data_source, table_source,
                          confidence, validation_score, semantic_score))
                
                return True
                
            except Exception:
                return False
    
    def build_intelligent_inventory_with_enrichment(self, enrichment_engine: CrossTableDataEnrichment, all_table_metadata: List[Dict]) -> Dict[str, int]:
        with self._lock:
            try:
                endpoints = self.conn.execute("""
                    SELECT primary_hostname, seen_count 
                    FROM intelligent_endpoints 
                    ORDER BY seen_count DESC, last_seen DESC
                """).fetchall()
                
                stats = {
                    'processed_endpoints': 0,
                    'high_quality_assets': 0,
                    'enriched_assets': 0,
                    'total_data_points': 0
                }
                
                for primary_hostname, seen_count in endpoints:
                    PrettyLogger.info(f"Processing endpoint: {primary_hostname}")
                    
                    try:
                        enriched_data = asyncio.run(
                            enrichment_engine.enrich_hostname_data(primary_hostname, all_table_metadata)
                        )
                        
                        asset_data = self._build_intelligent_asset_profile_with_enrichment(
                            primary_hostname, enriched_data
                        )
                        
                        if asset_data:
                            self._insert_intelligent_inventory(primary_hostname, asset_data)
                            stats['processed_endpoints'] += 1
                            
                            if asset_data.get('data_quality_score', 0) > 70:
                                stats['high_quality_assets'] += 1
                            
                            if asset_data.get('source_count', 0) > 2:
                                stats['enriched_assets'] += 1
                    
                    except Exception as e:
                        PrettyLogger.warning(f"Failed to enrich {primary_hostname}: {e}")
                        continue
                
                total_data_points = self.conn.execute("""
                    SELECT COUNT(*) FROM intelligent_endpoint_data
                """).fetchone()[0]
                stats['total_data_points'] = total_data_points
                
                return stats
                
            except Exception as e:
                PrettyLogger.error(f"Inventory building failed: {e}")
                return {'error': str(e)}
    
    def _build_intelligent_asset_profile_with_enrichment(self, primary_hostname: str, enriched_data: Dict) -> Dict[str, Any]:
        try:
            asset_profile = {
                'hostname': primary_hostname,
                'fqdn': enriched_data.get('fqdn', ''),
                'ip_addresses': ','.join(enriched_data.get('ip_addresses', [])),
                'mac_addresses': ','.join(enriched_data.get('mac_addresses', [])),
                'infrastructure_type': enriched_data.get('infrastructure_type', ''),
                'system_classification': '',
                'operating_system': '',
                'global_region': enriched_data.get('global_region', ''),
                'country': enriched_data.get('country', ''),
                'data_center': enriched_data.get('data_center', ''),
                'cloud_region': enriched_data.get('cloud_region', ''),
                'business_unit': enriched_data.get('business_unit', ''),
                'cio': enriched_data.get('cio', ''),
                'apm': enriched_data.get('apm', ''),
                'application_class': enriched_data.get('application_class', ''),
                'cost_center': '',
                'owner': '',
                'environment': enriched_data.get('environment', ''),
                'criticality': '',
                
                'in_splunk': enriched_data.get('in_splunk', False),
                'in_chronicle': enriched_data.get('in_chronicle', False),
                'in_gso': enriched_data.get('in_gso', False),
                'has_crowdstrike': enriched_data.get('has_crowdstrike', False),
                'found_in_cmdb': True,
                
                'splunk_log_volume': enriched_data.get('splunk_log_volume', 0),
                'chronicle_event_count': enriched_data.get('chronicle_event_count', 0),
                'last_splunk_log': enriched_data.get('last_splunk_log'),
                'last_chronicle_event': enriched_data.get('last_chronicle_event'),
                
                'has_edr': enriched_data.get('has_edr', False),
                'has_tanium': enriched_data.get('has_tanium', False),
                'has_dlp': enriched_data.get('has_dlp', False),
                'agent_coverage_score': enriched_data.get('agent_coverage_score', 0.0),
                
                'cmdb_last_updated': enriched_data.get('cmdb_last_updated'),
                'data_quality_score': enriched_data.get('data_quality_score', 0.0),
                'url_fqdn_coverage': enriched_data.get('url_fqdn_coverage', False),
                'public_ip_space_mapped': enriched_data.get('public_ip_space_mapped', False),
                'domain_visibility': enriched_data.get('domain_visibility', ''),
                'ao1_visibility_score': enriched_data.get('ao1_visibility_score', 0.0),
                'ao1_gap_severity': enriched_data.get('ao1_gap_severity', 'unknown'),
                'ao1_recommendation': enriched_data.get('ao1_recommendation', ''),
                
                'source_systems': '',
                'source_count': 0,
                'data_completeness_score': 0.0,
                'intelligence_score': 0.0,
                'enrichment_metadata': json.dumps(enriched_data)
            }
            
            source_systems = set()
            data_sources = self.conn.execute("""
                SELECT DISTINCT data_source FROM intelligent_endpoint_data
                WHERE primary_hostname = ?
            """, (primary_hostname,)).fetchall()
            
            for source_row in data_sources:
                source_systems.add(source_row[0])
            
            asset_profile['source_systems'] = ','.join(sorted(source_systems))
            asset_profile['source_count'] = len(source_systems)
            
            critical_fields = [
                'fqdn', 'ip_addresses', 'infrastructure_type', 'global_region',
                'business_unit', 'environment'
            ]
            populated_fields = sum(1 for field in critical_fields if asset_profile.get(field))
            asset_profile['data_completeness_score'] = (populated_fields / len(critical_fields)) * 100
            
            intelligence_factors = [
                asset_profile['data_quality_score'] / 100,
                asset_profile['data_completeness_score'] / 100,
                asset_profile['ao1_visibility_score'] / 100,
                min(asset_profile['source_count'] / 5, 1.0)
            ]
            asset_profile['intelligence_score'] = sum(intelligence_factors) / len(intelligence_factors)
            
            return asset_profile
            
        except Exception:
            return {}
    
    def _insert_intelligent_inventory(self, hostname: str, data: Dict[str, Any]):
        try:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = []
            for col in columns:
                value = data[col]
                if isinstance(value, bool):
                    values.append(value)
                elif value is None:
                    values.append(None)
                else:
                    values.append(value)
            
            query = f"""
            INSERT OR REPLACE INTO intelligent_asset_inventory ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
        except Exception as e:
            PrettyLogger.warning(f"Failed to insert asset {hostname}: {e}")
    
    def get_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_endpoints'] = self.conn.execute("""
                SELECT COUNT(*) FROM intelligent_endpoints
            """).fetchone()[0]
            
            stats['total_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM intelligent_asset_inventory
            """).fetchone()[0]
            
            stats['total_data_points'] = self.conn.execute("""
                SELECT COUNT(*) FROM intelligent_endpoint_data
            """).fetchone()[0]
            
            stats['avg_intelligence_score'] = self.conn.execute("""
                SELECT AVG(intelligence_score) FROM intelligent_asset_inventory
            """).fetchone()[0] or 0.0
            
            stats['high_quality_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM intelligent_asset_inventory WHERE data_quality_score > 80
            """).fetchone()[0]
            
            return stats
            
        except Exception:
            return {}

class IntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*90)
        
        self.client_manager = BigQueryClientManager(project_id)
        self.chronicle_client_manager = None
        
        if not self.client_manager.test_connection():
            raise ConnectionError("Failed to authenticate with BigQuery")
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
            if not self.chronicle_client_manager.test_connection():
                PrettyLogger.warning("Chronicle unavailable - continuing with primary project")
                self.chronicle_client_manager = None
        except:
            self.chronicle_client_manager = None
        
        self.matcher = IntelligentContentMatcher()
        self.cache = IntelligentCacheManager(
            cache_dir=self.config.get('cache_dir', '.cache'),
            max_memory_mb=self.config.get('max_memory_mb', 512),
            max_disk_gb=self.config.get('max_disk_gb', 5)
        )
        
        self.table_discovery = IntelligentTableDiscovery(self.matcher, self.cache)
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_intelligent_cmdb.db')
        self.data_fusion = IntelligentDataFusion(self.db_path)
        
        self.discovered_hostnames = set()
        self.processed_tables = set()
        self._lock = threading.RLock()
    
    async def execute_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting intelligent multi-dimensional discovery with cross-table enrichment")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            await self._execute_intelligent_hostname_discovery(all_table_metadata)
            
            enrichment_engine = CrossTableDataEnrichment(self.client_manager, self.matcher)
            
            PrettyLogger.info("Building intelligent asset inventory with cross-table enrichment")
            inventory_stats = self.data_fusion.build_intelligent_inventory_with_enrichment(
                enrichment_engine, all_table_metadata
            )
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_intelligent_stats(time.time() - start_time, inventory_stats)
            analysis_queries = self._create_intelligent_queries()
            
            PrettyLogger.success("Intelligent discovery with enrichment completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self.table_discovery.discover_intelligent_table_metadata(client_mgr, project_id),
                    timeout=300
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 5 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x['data_richness_score'], reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        
        if len(all_metadata) > 0:
            PrettyLogger.info("Top intelligent tables:")
            for i, table in enumerate(all_metadata[:5]):
                richness = table['data_richness_score']
                table_name = table['table_id']
                PrettyLogger.info(f"  {i+1}. {table_name} (richness: {richness:.2f})")
        
        return all_metadata
    
    async def _execute_intelligent_hostname_discovery(self, table_metadata: List[Dict[str, Any]]):
        PrettyLogger.info("Phase 1: Intelligent hostname discovery")
        
        critical_tables = [t for t in table_metadata if t['data_richness_score'] > 0.5]
        supplementary_tables = [t for t in table_metadata if t['data_richness_score'] <= 0.5]
        
        processing_order = critical_tables + supplementary_tables
        
        total_discovered = 0
        
        for table_meta in processing_order:
            if self.signal_handler.shutdown_requested:
                break
            
            try:
                discovered_count = await self._discover_hostnames_intelligently(table_meta)
                total_discovered += discovered_count
                
                if discovered_count > 0:
                    table_name = table_meta['table_id']
                    PrettyLogger.info(f"{table_name}: {discovered_count} hostnames discovered")
                
            except Exception as e:
                PrettyLogger.error(f"Hostname discovery failed for {table_meta['table_id']}: {e}")
        
        PrettyLogger.success(f"Discovered {total_discovered:,} unique intelligent endpoints")
    
    async def _discover_hostnames_intelligently(self, table_meta: Dict[str, Any]) -> int:
        hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
        if not hostname_column:
            return 0
        
        project_id = table_meta['project_id']
        table_path = table_meta['full_table_path']
        
        client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
        
        partition_filter = ""
        if table_meta['is_partitioned'] and table_meta['partition_field']:
            partition_filter = f"WHERE `{table_meta['partition_field']}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY) AND"
        else:
            partition_filter = "WHERE"
        
        safe_hostname_column = hostname_column.replace('`', '``')
        
        hostname_query = f"""
        SELECT DISTINCT 
            UPPER(TRIM(CAST(`{safe_hostname_column}` AS STRING))) as hostname
        FROM `{table_path}`
        {partition_filter} `{safe_hostname_column}` IS NOT NULL
            AND LENGTH(TRIM(CAST(`{safe_hostname_column}` AS STRING))) >= 2
            AND TRIM(CAST(`{safe_hostname_column}` AS STRING)) NOT REGEXP r'^[0-9\\.]+$'
        LIMIT 50000
        """
        
        try:
            with client_mgr.get_client() as client:
                job_config = bigquery.QueryJobConfig(
                    dry_run=True,
                    use_query_cache=False,
                    maximum_bytes_billed=100 * 1024 * 1024
                )
                
                dry_run_job = client.query(hostname_query, job_config=job_config)
                
                if dry_run_job.total_bytes_processed > 50 * 1024 * 1024:
                    PrettyLogger.warning(f"Skipping expensive hostname query for {table_path}")
                    return 0
                
                job_config = bigquery.QueryJobConfig(
                    dry_run=False,
                    use_query_cache=True,
                    maximum_bytes_billed=100 * 1024 * 1024
                )
                
                job = client.query(hostname_query, job_config=job_config)
                results = list(job.result())
                
                discovered_count = 0
                for row in results:
                    original_hostname = row[0]
                    
                    if self.data_fusion.register_intelligent_endpoint(original_hostname, original_hostname):
                        with self._lock:
                            normalized = self.data_fusion.hostname_normalizer.normalize_aggressively(original_hostname)
                            if normalized:
                                self.discovered_hostnames.add(normalized)
                                discovered_count += 1
                
                return discovered_count
                
        except Exception as e:
            PrettyLogger.warning(f"Hostname discovery failed for {table_path}: {e}")
            return 0
    
    def _generate_intelligent_stats(self, processing_time: float, inventory_stats: Dict[str, int]) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
    def _generate_intelligent_stats(self, processing_time: float, inventory_stats: Dict[str, int]) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'intelligent_multi_dimensional_with_cross_table_enrichment',
            'total_endpoints_discovered': intelligence_stats.get('total_endpoints', 0),
            'consolidated_assets': intelligence_stats.get('total_assets', 0),
            'total_data_points': intelligence_stats.get('total_data_points', 0),
            'avg_intelligence_score': intelligence_stats.get('avg_intelligence_score', 0.0),
            'high_quality_assets': intelligence_stats.get('high_quality_assets', 0),
            'unique_hostnames_discovered': len(self.discovered_hostnames),
            'tables_analyzed': len(self.processed_tables),
            'cache_performance': cache_stats,
            'inventory_build_stats': inventory_stats,
            'enrichment_capabilities': {
                'cross_table_data_fusion': True,
                'advanced_field_mapping': True,
                'multi_source_correlation': True,
                'intelligent_gap_analysis': True,
                'ao1_visibility_scoring': True,
                'agent_coverage_analysis': True
            }
        }
    
    def _create_intelligent_queries(self) -> Dict[str, str]:
        return {
            'intelligent_asset_overview': """
            SELECT 
                hostname, fqdn, ip_addresses, infrastructure_type, global_region,
                business_unit, environment, found_in_cmdb, has_crowdstrike,
                in_splunk, in_chronicle, in_gso, data_quality_score,
                intelligence_score, source_systems, source_count,
                ao1_visibility_score, ao1_gap_severity, ao1_recommendation
            FROM intelligent_asset_inventory 
            ORDER BY intelligence_score DESC, data_quality_score DESC;
            """,
            
            'ao1_visibility_analysis': """
            SELECT 
                CASE 
                    WHEN ao1_visibility_score >= 90 THEN 'Excellent Visibility (90%+)'
                    WHEN ao1_visibility_score >= 70 THEN 'Good Visibility (70-89%)'
                    WHEN ao1_visibility_score >= 50 THEN 'Fair Visibility (50-69%)'
                    WHEN ao1_visibility_score >= 30 THEN 'Poor Visibility (30-49%)'
                    ELSE 'Critical Visibility Gap (<30%)'
                END as visibility_tier,
                COUNT(*) as asset_count,
                AVG(ao1_visibility_score) as avg_visibility,
                AVG(data_quality_score) as avg_quality,
                AVG(agent_coverage_score) as avg_agent_coverage
            FROM intelligent_asset_inventory
            GROUP BY visibility_tier
            ORDER BY avg_visibility DESC;
            """,
            
            'comprehensive_coverage_analysis': """
            SELECT 
                business_unit,
                environment,
                COUNT(*) as total_assets,
                SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN in_gso THEN 1 ELSE 0 END) as gso_coverage,
                SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN has_tanium THEN 1 ELSE 0 END) as tanium_coverage,
                SUM(CASE WHEN has_dlp THEN 1 ELSE 0 END) as dlp_coverage,
                SUM(CASE WHEN has_edr THEN 1 ELSE 0 END) as edr_coverage,
                ROUND(AVG(ao1_visibility_score), 2) as avg_ao1_score,
                ROUND(AVG(agent_coverage_score), 2) as avg_agent_score
            FROM intelligent_asset_inventory
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment
            ORDER BY total_assets DESC;
            """,
            
            'data_quality_intelligence': """
            SELECT 
                CASE 
                    WHEN data_quality_score >= 90 THEN 'Excellent Quality (90%+)'
                    WHEN data_quality_score >= 75 THEN 'High Quality (75-89%)'
                    WHEN data_quality_score >= 60 THEN 'Good Quality (60-74%)'
                    WHEN data_quality_score >= 40 THEN 'Fair Quality (40-59%)'
                    ELSE 'Poor Quality (<40%)'
                END as quality_tier,
                COUNT(*) as asset_count,
                AVG(data_quality_score) as avg_quality,
                AVG(intelligence_score) as avg_intelligence,
                AVG(source_count) as avg_sources
            FROM intelligent_asset_inventory
            GROUP BY quality_tier
            ORDER BY avg_quality DESC;
            """,
            
            'gap_analysis_recommendations': """
            SELECT 
                ao1_gap_severity,
                COUNT(*) as asset_count,
                ao1_recommendation,
                AVG(ao1_visibility_score) as avg_visibility,
                AVG(agent_coverage_score) as avg_agent_coverage,
                STRING_AGG(DISTINCT business_unit, ', ') as affected_business_units
            FROM intelligent_asset_inventory
            WHERE ao1_gap_severity IS NOT NULL
            GROUP BY ao1_gap_severity, ao1_recommendation
            ORDER BY 
                CASE ao1_gap_severity 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                    ELSE 4 
                END,
                asset_count DESC;
            """,
            
            'enrichment_effectiveness': """
            SELECT 
                'FQDN Coverage' as metric,
                SUM(CASE WHEN fqdn IS NOT NULL AND fqdn != '' THEN 1 ELSE 0 END) as populated,
                COUNT(*) as total,
                ROUND(SUM(CASE WHEN fqdn IS NOT NULL AND fqdn != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as coverage_percent
            FROM intelligent_asset_inventory
            UNION ALL
            SELECT 
                'IP Address Coverage' as metric,
                SUM(CASE WHEN ip_addresses IS NOT NULL AND ip_addresses != '' THEN 1 ELSE 0 END) as populated,
                COUNT(*) as total,
                ROUND(SUM(CASE WHEN ip_addresses IS NOT NULL AND ip_addresses != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as coverage_percent
            FROM intelligent_asset_inventory
            UNION ALL
            SELECT 
                'Infrastructure Type Coverage' as metric,
                SUM(CASE WHEN infrastructure_type IS NOT NULL AND infrastructure_type != '' THEN 1 ELSE 0 END) as populated,
                COUNT(*) as total,
                ROUND(SUM(CASE WHEN infrastructure_type IS NOT NULL AND infrastructure_type != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as coverage_percent
            FROM intelligent_asset_inventory
            UNION ALL
            SELECT 
                'Business Unit Coverage' as metric,
                SUM(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 ELSE 0 END) as populated,
                COUNT(*) as total,
                ROUND(SUM(CASE WHEN business_unit IS NOT NULL AND business_unit != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as coverage_percent
            FROM intelligent_asset_inventory
            UNION ALL
            SELECT 
                'Environment Coverage' as metric,
                SUM(CASE WHEN environment IS NOT NULL AND environment != '' THEN 1 ELSE 0 END) as populated,
                COUNT(*) as total,
                ROUND(SUM(CASE WHEN environment IS NOT NULL AND environment != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as coverage_percent
            FROM intelligent_asset_inventory
            ORDER BY coverage_percent DESC;
            """,
            
            'security_tool_coverage': """
            SELECT 
                business_unit,
                environment,
                COUNT(*) as total_assets,
                SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_count,
                SUM(CASE WHEN has_tanium THEN 1 ELSE 0 END) as tanium_count,
                SUM(CASE WHEN has_dlp THEN 1 ELSE 0 END) as dlp_count,
                SUM(CASE WHEN has_edr THEN 1 ELSE 0 END) as edr_count,
                ROUND(AVG(agent_coverage_score), 2) as avg_agent_coverage,
                COUNT(*) - SUM(CASE WHEN has_edr THEN 1 ELSE 0 END) as edr_gap,
                COUNT(*) - SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_gap
            FROM intelligent_asset_inventory
            WHERE business_unit IS NOT NULL
            GROUP BY business_unit, environment
            ORDER BY edr_gap DESC, crowdstrike_gap DESC;
            """,
            
            'cross_table_enrichment_success': """
            SELECT 
                source_count,
                COUNT(*) as asset_count,
                AVG(data_quality_score) as avg_quality,
                AVG(ao1_visibility_score) as avg_visibility,
                AVG(intelligence_score) as avg_intelligence,
                STRING_AGG(DISTINCT 
                    CASE 
                        WHEN fqdn IS NOT NULL AND fqdn != '' THEN 'FQDN'
                        ELSE NULL 
                    END, ', ') as enriched_fields_sample
            FROM intelligent_asset_inventory
            GROUP BY source_count
            ORDER BY source_count DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()