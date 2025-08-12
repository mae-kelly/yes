#!/usr/bin/env python3

import os
import asyncio
import logging
import duckdb
import time
import threading
import re
import json
import hashlib
from typing import Dict, List, Any, Tuple, Set, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from pathlib import Path
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import statistics
import multiprocessing as mp
from contextlib import asynccontextmanager
import functools

from gcp_client import BigQueryClientManager
from intelligent_content_matcher import IntelligentContentMatcher
from intelligent_cache_manager import IntelligentCacheManager
from progress_tracker import ProgressTracker
from checkpoint_manager import CheckpointManager
from signal_handler import SignalHandler

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound, Forbidden, BadRequest
except ImportError:
    bigquery = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ao1_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BatchedHostData:
    hostnames: List[str]
    enrichment_data: Dict[str, Dict[str, Any]]
    source_tables: Set[str]
    processing_time: float = 0.0
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    data_quality_metrics: Dict[str, Any] = field(default_factory=dict)
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TableAnalysisResult:
    table_path: str
    hostname_columns: List[Dict[str, Any]]
    enrichment_potential: float
    data_quality_score: float
    processing_cost_estimate: int
    recommended_strategy: str
    column_mappings: Dict[str, str]
    sample_hostnames: List[str]

class IntelligentFieldExtractor:
    
    def __init__(self, client_manager: BigQueryClientManager, matcher: IntelligentContentMatcher, 
                 chronicle_client_manager: Optional[BigQueryClientManager] = None, batch_size: int = 500):
        self.client_manager = client_manager
        self.chronicle_client_manager = chronicle_client_manager
        self.matcher = matcher
        self.batch_size = batch_size
        
        self.field_extraction_cache = {}
        self.table_analysis_cache = {}
        self.hostname_intelligence = defaultdict(lambda: {
            'variants': set(),
            'confidence': 0.0,
            'first_seen': None,
            'last_seen': None,
            'source_count': 0
        })
        
        self.query_optimizer = QueryOptimizer()
        self.semantic_analyzer = SemanticFieldAnalyzer()
        
        self.ao1_field_intelligence = self._initialize_ao1_intelligence()
        
    def _initialize_ao1_intelligence(self) -> Dict[str, Dict[str, Any]]:
        return {
            'infrastructure_type': {
                'table_keywords': ['infrastructure', 'platform', 'environment', 'deployment', 'hosting'],
                'column_keywords': ['type', 'infra', 'infrastructure', 'platform', 'onprem', 'cloud', 'saas', 'api'],
                'semantic_patterns': [
                    r'(on.?prem|physical|bare.?metal)',
                    r'(cloud|aws|azure|gcp|public.?cloud)',
                    r'(saas|software.?as.?service)',
                    r'(api|interface|gateway)'
                ],
                'normalization_map': {
                    'onprem': 'On-Premises', 'physical': 'On-Premises', 'bare': 'On-Premises',
                    'cloud': 'Cloud', 'aws': 'Cloud', 'azure': 'Cloud', 'gcp': 'Cloud',
                    'saas': 'SaaS', 'software': 'SaaS', 'service': 'SaaS',
                    'api': 'API', 'interface': 'API', 'gateway': 'API'
                }
            },
            'system_classification': {
                'table_keywords': ['system', 'os', 'operating', 'server', 'classification'],
                'column_keywords': ['classification', 'category', 'class', 'type', 'os', 'system'],
                'semantic_patterns': [
                    r'(web.?server|iis|apache|nginx)',
                    r'(windows|win|microsoft|ms)',
                    r'(linux|unix|centos|ubuntu|redhat)',
                    r'(mainframe|mf|zos|z\/os)',
                    r'(database|db|sql|oracle|mysql)',
                    r'(appliance|firewall|switch|router)'
                ],
                'normalization_map': {
                    'web': 'Web Server', 'webserver': 'Web Server', 'iis': 'Web Server', 'apache': 'Web Server',
                    'windows': 'Windows Server', 'win': 'Windows Server', 'microsoft': 'Windows Server',
                    'linux': 'Linux Server', 'unix': 'Linux Server', 'centos': 'Linux Server',
                    'mainframe': 'Mainframe', 'mf': 'Mainframe', 'zos': 'Mainframe',
                    'database': 'Database', 'db': 'Database', 'sql': 'Database',
                    'appliance': 'Network Appliance', 'firewall': 'Network Appliance'
                }
            },
            'edr_coverage': {
                'table_keywords': ['crowdstrike', 'defender', 'sentinel', 'edr', 'endpoint', 'carbon', 'blackberry', 'cylance'],
                'column_keywords': ['edr', 'endpoint', 'detection', 'response', 'crowdstrike', 'defender'],
                'boolean_mapping': True,
                'presence_indicators': ['agent', 'installed', 'deployed', 'active', 'running']
            },
            'tanium_coverage': {
                'table_keywords': ['tanium'],
                'column_keywords': ['tanium', 'tanium_agent', 'tanium_client'],
                'boolean_mapping': True,
                'presence_indicators': ['agent', 'client', 'installed', 'deployed']
            },
            'dlp_coverage': {
                'table_keywords': ['dlp', 'symantec', 'forcepoint', 'microsoft_purview', 'data_loss'],
                'column_keywords': ['dlp', 'data_loss', 'prevention', 'symantec', 'forcepoint'],
                'boolean_mapping': True,
                'presence_indicators': ['agent', 'policy', 'rule', 'monitor']
            },
            'network_log_types': {
                'table_keywords': ['firewall', 'palo_alto', 'checkpoint', 'fortinet', 'cisco_asa', 'ids', 'ips', 'ndr', 'proxy', 'dns', 'waf'],
                'column_keywords': ['firewall', 'ids', 'ips', 'ndr', 'proxy', 'dns', 'waf'],
                'log_categories': ['firewall', 'ids', 'ips', 'ndr', 'proxy', 'dns', 'waf']
            },
            'endpoint_log_types': {
                'table_keywords': ['syslog', 'winlog', 'windows_event', 'linux_log', 'edr_log', 'dlp_log', 'fim', 'osquery'],
                'column_keywords': ['syslog', 'winlog', 'edr_log', 'dlp_log', 'fim'],
                'log_categories': ['syslog', 'winlog', 'edr_log', 'dlp_log', 'fim']
            },
            'cloud_log_types': {
                'table_keywords': ['cloudtrail', 'cloudconfig', 'azure_log', 'gcp_log', 'aws_config', 'azure_activity', 'gcp_audit'],
                'column_keywords': ['cloudtrail', 'cloudconfig', 'azure_log', 'gcp_log'],
                'log_categories': ['cloudtrail', 'cloudconfig', 'azure_log', 'gcp_log']
            },
            'application_log_types': {
                'table_keywords': ['weblog', 'apache_log', 'iis_log', 'nginx_log', 'applog', 'api_gateway', 'tomcat'],
                'column_keywords': ['weblog', 'applog', 'api_gateway', 'tomcat'],
                'log_categories': ['weblog', 'applog', 'api_gateway', 'tomcat']
            },
            'identity_log_types': {
                'table_keywords': ['auth', 'authentication', 'active_directory', 'ldap', 'okta', 'azure_ad', 'identity'],
                'column_keywords': ['auth', 'identity', 'authentication', 'ldap', 'ad'],
                'log_categories': ['auth', 'identity', 'authentication', 'ldap', 'ad']
            },
            'global_region': {
                'table_keywords': ['region', 'location', 'geography', 'datacenter'],
                'column_keywords': ['region', 'global_region', 'location', 'geo', 'area'],
                'normalization_map': {
                    'us': 'US', 'usa': 'US', 'america': 'US', 'north america': 'US',
                    'eu': 'EU', 'europe': 'EU', 'emea': 'EU',
                    'ap': 'APAC', 'asia': 'APAC', 'pacific': 'APAC', 'apac': 'APAC'
                }
            },
            'business_unit': {
                'table_keywords': ['business', 'organization', 'department', 'division'],
                'column_keywords': ['business_unit', 'bu', 'org', 'organization', 'department']
            },
            'network_zones': {
                'table_keywords': ['network', 'vlan', 'subnet', 'zone', 'segment'],
                'column_keywords': ['zone', 'network_zone', 'security_zone', 'vlan']
            }
        }
    
    async def extract_fields_batch_intelligent(self, hostnames: List[str], 
                                              table_metadata: List[Dict]) -> BatchedHostData:
        start_time = time.time()
        
        batch_data = BatchedHostData(
            hostnames=hostnames,
            enrichment_data={},
            source_tables=set(),
            data_quality_metrics={
                'hostname_coverage': 0.0,
                'field_completeness': 0.0,
                'confidence_score': 0.0,
                'data_freshness': 0.0
            }
        )
        
        hostname_intelligence = await self._generate_hostname_intelligence(hostnames)
        all_variants = set()
        for intel in hostname_intelligence.values():
            all_variants.update(intel['variants'])
        
        logger.info(f"Generated {len(all_variants)} hostname variants from {len(hostnames)} original hostnames")
        
        prioritized_tables = self._prioritize_tables_for_extraction(table_metadata, all_variants)
        
        extraction_tasks = []
        for table_meta in prioritized_tables:
            if await self._should_extract_from_table(table_meta, all_variants):
                task = self._extract_intelligent_batch_from_table(
                    all_variants, table_meta, hostname_intelligence
                )
                extraction_tasks.append(task)
        
        if extraction_tasks:
            logger.info(f"Executing {len(extraction_tasks)} intelligent extraction tasks")
            batch_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, dict) and 'enrichment_data' in result:
                    self._merge_intelligent_results(batch_data, result)
                elif isinstance(result, Exception):
                    logger.warning(f"Extraction task failed: {result}")
        
        batch_data.processing_time = time.time() - start_time
        batch_data.data_quality_metrics = self._calculate_batch_quality_metrics(batch_data)
        
        logger.info(f"Batch processing complete: {len(batch_data.enrichment_data)} hosts enriched in {batch_data.processing_time:.2f}s")
        return batch_data
    
    async def _generate_hostname_intelligence(self, hostnames: List[str]) -> Dict[str, Dict[str, Any]]:
        intelligence = {}
        
        for hostname in hostnames:
            variants = self._generate_smart_hostname_variants(hostname)
            
            intelligence[hostname] = {
                'variants': variants,
                'normalized': self._normalize_hostname_intelligent(hostname),
                'confidence': self._calculate_hostname_confidence(hostname),
                'semantic_category': self._classify_hostname_semantically(hostname),
                'extraction_priority': self._calculate_extraction_priority(hostname)
            }
        
        return intelligence
    
    def _generate_smart_hostname_variants(self, hostname: str) -> Set[str]:
        variants = {hostname}
        hostname_upper = hostname.upper()
        
        if '-' in hostname_upper:
            variants.update([
                hostname_upper.replace('-', ''),
                hostname_upper.replace('-', '_'),
                hostname_upper.replace('-', '.')
            ])
        
        if '_' in hostname_upper:
            variants.update([
                hostname_upper.replace('_', ''),
                hostname_upper.replace('_', '-'),
                hostname_upper.replace('_', '.')
            ])
        
        number_match = re.search(r'(\d+)$', hostname_upper)
        if number_match:
            base = hostname_upper[:number_match.start()]
            current_num = int(number_match.group(1))
            num_length = len(number_match.group(1))
            
            for offset in [-2, -1, 1, 2]:
                new_num = current_num + offset
                if new_num > 0:
                    variants.add(base + str(new_num).zfill(num_length))
        
        if '.' in hostname_upper:
            parts = hostname_upper.split('.')
            variants.add(parts[0])
            if len(parts) > 2:
                variants.add('.'.join(parts[-2:]))
        
        if len(hostname_upper) > 12:
            variants.add(hostname_upper[:8])
            variants.add(hostname_upper[:15])
        
        semantic_patterns = [
            (r'^(SRV|SERVER)(\d+)$', r'SV\2'),
            (r'^(WEB)(\d+)$', r'W\2'),
            (r'^(APP)(\d+)$', r'A\2'),
            (r'^(DB|DATABASE)(\d+)$', r'D\2')
        ]
        
        for pattern, replacement in semantic_patterns:
            match = re.match(pattern, hostname_upper)
            if match:
                variants.add(re.sub(pattern, replacement, hostname_upper))
        
        return variants
    
    def _normalize_hostname_intelligent(self, hostname: str) -> str:
        if not hostname:
            return ""
        
        normalized = str(hostname).strip().upper()
        
        if len(normalized) < 2 or len(normalized) > 253:
            return ""
        
        invalid_indicators = [
            '@', 'HTTP', 'HTTPS', '://', 'WWW.',
            'UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 
            'TEST', 'EXAMPLE', 'LOCALHOST', 'DUMMY', 
            'SAMPLE', 'PLACEHOLDER', 'DEFAULT'
        ]
        
        for indicator in invalid_indicators:
            if indicator in normalized:
                return ""
        
        normalized = re.sub(r'^[^A-Z0-9]+', '', normalized)
        normalized = re.sub(r'[^A-Z0-9]+$', '', normalized)
        
        if '.' in normalized and not normalized.replace('.', '').isdigit():
            normalized = normalized.split('.')[0]
        
        normalized = re.sub(r'[^A-Z0-9\-]', '', normalized)
        
        return normalized if len(normalized) >= 2 else ""
    
    def _calculate_hostname_confidence(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.5
        hostname_upper = hostname.upper()
        
        if 3 <= len(hostname_upper) <= 15:
            score += 0.2
        elif 16 <= len(hostname_upper) <= 63:
            score += 0.1
        
        if re.match(r'^[A-Z]{2,}[0-9]+$', hostname_upper):
            score += 0.3
        elif re.match(r'^[A-Z]+-[A-Z0-9]+$', hostname_upper):
            score += 0.25
        elif re.match(r'^[A-Z0-9]+\-[A-Z0-9]+$', hostname_upper):
            score += 0.2
        
        semantic_indicators = [
            'SERVER', 'SRV', 'WEB', 'APP', 'DB', 'DC', 'WIN', 'LIN', 
            'PROD', 'DEV', 'TEST', 'STAGE', 'UAT'
        ]
        
        for indicator in semantic_indicators:
            if indicator in hostname_upper:
                score += 0.1
                break
        
        return min(score, 1.0)
    
    def _classify_hostname_semantically(self, hostname: str) -> str:
        hostname_upper = hostname.upper()
        
        if any(x in hostname_upper for x in ['WEB', 'HTTP', 'IIS', 'APACHE']):
            return 'web_server'
        elif any(x in hostname_upper for x in ['DB', 'DATABASE', 'SQL', 'ORACLE']):
            return 'database_server'
        elif any(x in hostname_upper for x in ['APP', 'APPLICATION', 'TOMCAT']):
            return 'application_server'
        elif any(x in hostname_upper for x in ['DC', 'DOMAIN', 'AD', 'LDAP']):
            return 'domain_controller'
        elif any(x in hostname_upper for x in ['FW', 'FIREWALL', 'PROXY']):
            return 'security_appliance'
        elif any(x in hostname_upper for x in ['SWITCH', 'ROUTER', 'GATEWAY']):
            return 'network_device'
        elif any(x in hostname_upper for x in ['DESKTOP', 'PC', 'WORKSTATION']):
            return 'endpoint'
        elif any(x in hostname_upper for x in ['SERVER', 'SRV', 'HOST']):
            return 'generic_server'
        else:
            return 'unknown'
    
    def _calculate_extraction_priority(self, hostname: str) -> int:
        hostname_upper = hostname.upper()
        priority = 50
        
        high_priority_terms = ['PROD', 'PRODUCTION', 'CRITICAL', 'CORE', 'PRIMARY']
        if any(term in hostname_upper for term in high_priority_terms):
            priority += 30
        
        medium_priority_terms = ['SERVER', 'SRV', 'DB', 'WEB', 'APP']
        if any(term in hostname_upper for term in medium_priority_terms):
            priority += 20
        
        low_priority_terms = ['TEST', 'DEV', 'SANDBOX', 'TEMP']
        if any(term in hostname_upper for term in low_priority_terms):
            priority -= 20
        
        return max(0, min(100, priority))
    
    def _prioritize_tables_for_extraction(self, table_metadata: List[Dict], variants: Set[str]) -> List[Dict]:
        scored_tables = []
        
        for table_meta in table_metadata:
            score = 0
            
            score += table_meta.get('data_richness_score', 0) * 30
            
            sample_data = table_meta.get('sample_data', {})
            hostname_column = table_meta.get('hostname_analysis', {}).get('primary_hostname_column')
            
            if hostname_column and hostname_column in sample_data:
                hostnames_in_table = set()
                for hostname in sample_data[hostname_column]:
                    normalized = self._normalize_hostname_intelligent(hostname)
                    if normalized:
                        hostnames_in_table.add(normalized)
                
                coverage = len(variants & hostnames_in_table) / max(len(variants), 1)
                score += coverage * 40
            
            if table_meta.get('row_count', 0) > 1000:
                score += 10
            if table_meta.get('is_partitioned'):
                score += 5
            
            table_name = table_meta.get('table_id', '').lower()
            dataset_name = table_meta.get('dataset_id', '').lower()
            full_table_path = table_meta.get('full_table_path', '').lower()
            
            ao1_table_keywords = []
            for field_info in self.ao1_field_intelligence.values():
                if isinstance(field_info, dict) and 'table_keywords' in field_info:
                    ao1_table_keywords.extend(field_info['table_keywords'])
            
            for keyword in set(ao1_table_keywords):
                if (keyword in table_name or keyword in dataset_name or keyword in full_table_path):
                    score += 25
                    break
            
            scored_tables.append((table_meta, score))
        
        scored_tables.sort(key=lambda x: x[1], reverse=True)
        return [table for table, score in scored_tables]
    
    async def _should_extract_from_table(self, table_meta: Dict, variants: Set[str]) -> bool:
        table_path = table_meta.get('full_table_path', '')
        cache_key = f"extract_decision_{hashlib.md5(table_path.encode()).hexdigest()}"
        
        if cache_key in self.table_analysis_cache:
            return self.table_analysis_cache[cache_key]
        
        data_richness = table_meta.get('data_richness_score', 0)
        if data_richness < 0.1:
            self.table_analysis_cache[cache_key] = False
            return False
        
        hostname_analysis = table_meta.get('hostname_analysis', {})
        if not hostname_analysis.get('primary_hostname_column'):
            self.table_analysis_cache[cache_key] = False
            return False
        
        sample_data = table_meta.get('sample_data', {})
        hostname_column = hostname_analysis['primary_hostname_column']
        
        if hostname_column in sample_data:
            sample_hostnames = set()
            for hostname in sample_data[hostname_column]:
                normalized = self._normalize_hostname_intelligent(hostname)
                if normalized:
                    sample_hostnames.add(normalized)
            
            overlap = len(variants & sample_hostnames)
            decision = overlap > 0
        else:
            decision = False
        
        self.table_analysis_cache[cache_key] = decision
        return decision
    
    async def _extract_intelligent_batch_from_table(self, all_variants: Set[str], 
                                                   table_meta: Dict, 
                                                   hostname_intelligence: Dict) -> Dict[str, Any]:
        table_path = table_meta['full_table_path']
        hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
        column_analysis = table_meta.get('column_analysis', {})
        
        if not hostname_column:
            return {'enrichment_data': {}, 'metadata': {'error': 'No hostname column'}}
        
        project_id = table_meta['project_id']
        client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
        
        query_components = self._build_intelligent_query_components(
            table_path, hostname_column, all_variants, column_analysis, table_meta
        )
        
        if not query_components['select_fields'] or len(query_components['select_fields']) == 1:
            return {'enrichment_data': {}, 'metadata': {'error': 'No extractable fields'}}
        
        try:
            extraction_result = await self._execute_intelligent_extraction_query(
                client_mgr, query_components, hostname_intelligence, table_path
            )
            
            return {
                'enrichment_data': extraction_result['host_data'],
                'metadata': {
                    'table_path': table_path,
                    'rows_processed': extraction_result['rows_processed'],
                    'fields_extracted': len(query_components['field_mappings']),
                    'extraction_time': extraction_result['execution_time']
                }
            }
            
        except Exception as e:
            logger.warning(f"Extraction failed for {table_path}: {e}")
            return {'enrichment_data': {}, 'metadata': {'error': str(e)}}
    
    def _build_intelligent_query_components(self, table_path: str, hostname_column: str, 
                                           variants: Set[str], column_analysis: Dict, 
                                           table_meta: Dict) -> Dict[str, Any]:
        select_fields = [f"UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname"]
        field_mappings = {}
        
        for column, analysis in column_analysis.items():
            if column == hostname_column:
                continue
                
            field_type, confidence, metadata = analysis
            if confidence > 0.2:
                safe_column = column.replace('`', '``')
                select_fields.append(f"CAST(`{safe_column}` AS STRING) as `{safe_column}`")
                field_mappings[safe_column] = field_type
        
        all_columns = table_meta.get('all_columns', [])
        table_name = table_meta.get('table_id', '').lower()
        dataset_name = table_meta.get('dataset_id', '').lower()
        full_table_path_lower = table_path.lower()
        
        for column in all_columns:
            if column == hostname_column or column in field_mappings:
                continue
                
            matched_field = self._match_column_and_table_to_ao1_field(
                column, table_name, dataset_name, full_table_path_lower
            )
            if matched_field:
                safe_column = column.replace('`', '``')
                select_fields.append(f"CAST(`{safe_column}` AS STRING) as `{safe_column}`")
                field_mappings[safe_column] = matched_field
        
        for ao1_field, field_info in self.ao1_field_intelligence.items():
            if isinstance(field_info, dict) and 'table_keywords' in field_info:
                table_keywords = field_info['table_keywords']
                
                table_matches_field = any(
                    keyword in table_name or keyword in dataset_name or keyword in full_table_path_lower
                    for keyword in table_keywords
                )
                
                if table_matches_field:
                    if ao1_field not in field_mappings.values():
                        presence_column = f"'Yes' as {ao1_field}_from_table_presence"
                        select_fields.append(presence_column)
                        field_mappings[f"{ao1_field}_from_table_presence"] = ao1_field
        
        variant_list = list(variants)
        hostname_filter = "', '".join([h.replace("'", "''") for h in variant_list])
        
        partition_filter = ""
        if table_meta.get('is_partitioned') and table_meta.get('partition_field'):
            partition_field = table_meta['partition_field']
            partition_filter = f"AND `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
        
        row_count = table_meta.get('row_count', 0)
        sampling_clause = ""
        if row_count > 10000000:
            sampling_clause = "TABLESAMPLE SYSTEM (10 PERCENT)"
        
        query = f"""
        SELECT {', '.join(select_fields)}
        FROM `{table_path}` {sampling_clause}
        WHERE UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) IN ('{hostname_filter}')
        AND `{hostname_column}` IS NOT NULL
        AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) >= 2
        AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) <= 253
        {partition_filter}
        """
        
        return {
            'query': query,
            'select_fields': select_fields,
            'field_mappings': field_mappings,
            'hostname_filter': hostname_filter
        }
    
    def _match_column_and_table_to_ao1_field(self, column_name: str, table_name: str, 
                                           dataset_name: str, full_table_path: str) -> Optional[str]:
        column_lower = column_name.lower()
        
        for ao1_field, field_info in self.ao1_field_intelligence.items():
            if isinstance(field_info, dict):
                
                column_keywords = field_info.get('column_keywords', [])
                for keyword in column_keywords:
                    if keyword in column_lower:
                        return ao1_field
                
                table_keywords = field_info.get('table_keywords', [])
                for keyword in table_keywords:
                    if (keyword in table_name or keyword in dataset_name or keyword in full_table_path):
                        
                        if 'boolean_mapping' in field_info and field_info['boolean_mapping']:
                            presence_indicators = field_info.get('presence_indicators', [])
                            if any(indicator in column_lower for indicator in presence_indicators):
                                return ao1_field
                            if any(indicator in column_lower for indicator in ['status', 'state', 'enabled', 'active']):
                                return ao1_field
                        else:
                            return ao1_field
        
        semantic_mappings = {
            r'(environment|env)': 'infrastructure_type',
            r'(operating.?system|os.?type)': 'system_classification',
            r'(location|site|region)': 'global_region',
            r'(business.?unit|org|department)': 'business_unit',
            r'(security.?tool|protection)': 'edr_coverage',
            r'(monitoring|agent)': 'tanium_coverage',
            r'(network.?zone|subnet|vlan)': 'network_zones',
            r'(application|app.?type)': 'application_class'
        }
        
        for pattern, ao1_field in semantic_mappings.items():
            if re.search(pattern, column_lower):
                return ao1_field
        
        return None
    
    async def _execute_intelligent_extraction_query(self, client_mgr, query_components: Dict, 
                                                   hostname_intelligence: Dict, 
                                                   table_path: str) -> Dict[str, Any]:
        start_time = time.time()
        
        with client_mgr.get_client() as client:
            job_config = bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False
            )
            
            dry_run_job = client.query(query_components['query'], job_config=job_config)
            
            job_config = bigquery.QueryJobConfig(
                dry_run=False,
                use_query_cache=True,
                job_timeout_ms=120000
            )
            
            job = client.query(query_components['query'], job_config=job_config)
            results = list(job.result())
            
            host_data_map = defaultdict(lambda: {'source_table': table_path})
            rows_processed = 0
            
            for row in results:
                if not row or not row[0]:
                    continue
                
                rows_processed += 1
                row_hostname = self._normalize_hostname_intelligent(str(row[0]))
                if not row_hostname:
                    continue
                
                original_hostname = self._find_original_hostname(row_hostname, hostname_intelligence)
                if not original_hostname:
                    continue
                
                for i, field_name in enumerate(query_components['select_fields'][1:], 1):
                    if i < len(row) and row[i]:
                        clean_field_name = field_name.split(' as ')[-1].strip('`')
                        field_type = query_components['field_mappings'].get(clean_field_name, 'unknown')
                        raw_value = str(row[i]).strip()
                        
                        processed_value = self._process_field_value_intelligently(
                            field_type, raw_value, clean_field_name
                        )
                        
                        if processed_value:
                            host_data_map[original_hostname][field_type] = processed_value
            
            execution_time = time.time() - start_time
            
            return {
                'host_data': dict(host_data_map),
                'rows_processed': rows_processed,
                'execution_time': execution_time
            }
    
    def _find_original_hostname(self, normalized_hostname: str, hostname_intelligence: Dict) -> Optional[str]:
        for original, intel in hostname_intelligence.items():
            if normalized_hostname in intel['variants']:
                return original
        return None
    
    def _process_field_value_intelligently(self, field_type: str, value: str, column_name: str) -> Optional[str]:
        if not value or len(value.strip()) == 0:
            return None
        
        value = value.strip()
        
        invalid_values = ['NULL', 'N/A', 'UNKNOWN', 'NONE', '', 'NAN', 'EMPTY', 'UNDEFINED']
        if value.upper() in invalid_values:
            return None
        
        if len(value) > 500:
            return None
        
        if field_type in self.ao1_field_intelligence:
            field_info = self.ao1_field_intelligence[field_type]
            
            if 'normalization_map' in field_info:
                value_lower = value.lower()
                for pattern, normalized in field_info['normalization_map'].items():
                    if pattern in value_lower:
                        return normalized
            
            if 'semantic_patterns' in field_info:
                for pattern in field_info['semantic_patterns']:
                    if re.search(pattern, value, re.IGNORECASE):
                        match = re.search(pattern, value, re.IGNORECASE)
                        if match:
                            matched_text = match.group(0).lower()
                            if 'normalization_map' in field_info:
                                for key, norm_value in field_info['normalization_map'].items():
                                    if key in matched_text:
                                        return norm_value
                            return value
        
        if 'coverage' in field_type or field_type.endswith('_coverage'):
            return self._normalize_boolean_coverage(value)
        
        if 'log_types' in field_type:
            return self._normalize_log_type(value, field_type)
        
        if field_type in ['global_region', 'country']:
            return self._normalize_geographic_value(value)
        
        return value if len(value) > 0 else None
    
    def _normalize_boolean_coverage(self, value: str) -> str:
        value_lower = value.lower()
        
        true_indicators = ['true', 'yes', 'y', '1', 'enabled', 'active', 'installed', 'covered', 'on']
        false_indicators = ['false', 'no', 'n', '0', 'disabled', 'inactive', 'not installed', 'not covered', 'off']
        
        for indicator in true_indicators:
            if indicator in value_lower:
                return 'Yes'
        
        for indicator in false_indicators:
            if indicator in value_lower:
                return 'No'
        
        if any(term in value_lower for term in ['agent', 'client', 'service', 'tool']):
            return 'Yes'
        
        return 'No'
    
    def _normalize_log_type(self, value: str, field_type: str) -> Optional[str]:
        value_lower = value.lower()
        
        log_category = field_type.replace('_log_types', '_log_types')
        if field_type in self.ao1_field_intelligence:
            relevant_types = self.ao1_field_intelligence[field_type].get('log_categories', [])
            
            for log_type in relevant_types:
                if log_type in value_lower:
                    return self._standardize_log_type_name(log_type)
        
        if len(value) > 2 and not any(char in value for char in ['<', '>', '{', '}', '[', ']']):
            return value.title()
        
        return None
    
    def _standardize_log_type_name(self, log_type: str) -> str:
        standardization_map = {
            'firewall': 'Firewall Traffic',
            'ids': 'IDS/IPS',
            'ips': 'IDS/IPS',
            'ndr': 'NDR',
            'proxy': 'Proxy',
            'dns': 'DNS',
            'waf': 'WAF',
            'syslog': 'OS logs (WinEvt, Linux syslog)',
            'winlog': 'OS logs (WinEvt, Linux syslog)',
            'edr': 'EDR',
            'dlp': 'DLP',
            'fim': 'FIM',
            'cloudtrail': 'Cloud Event',
            'weblog': 'Web Logs (HTTP Access)',
            'auth': 'Authentication attempts'
        }
        
        return standardization_map.get(log_type, log_type.title())
    
    def _normalize_geographic_value(self, value: str) -> str:
        value_lower = value.lower()
        
        region_mappings = {
            'us': 'US', 'usa': 'US', 'america': 'US', 'north america': 'US',
            'eu': 'EU', 'europe': 'EU', 'emea': 'EU',
            'ap': 'APAC', 'asia': 'APAC', 'pacific': 'APAC', 'apac': 'APAC',
            'latam': 'LATAM', 'latin america': 'LATAM', 'south america': 'LATAM'
        }
        
        for pattern, normalized in region_mappings.items():
            if pattern in value_lower:
                return normalized
        
        return value.title() if len(value) > 1 else value
    
    def _merge_intelligent_results(self, batch_data: BatchedHostData, result: Dict[str, Any]):
        enrichment_data = result.get('enrichment_data', {})
        metadata = result.get('metadata', {})
        
        for hostname, host_data in enrichment_data.items():
            if hostname not in batch_data.enrichment_data:
                batch_data.enrichment_data[hostname] = {}
            
            for field, value in host_data.items():
                if field == 'source_table':
                    if 'source_tables' not in batch_data.enrichment_data[hostname]:
                        batch_data.enrichment_data[hostname]['source_tables'] = set()
                    batch_data.enrichment_data[hostname]['source_tables'].add(value)
                    batch_data.source_tables.add(value)
                    continue
                
                existing_value = batch_data.enrichment_data[hostname].get(field)
                
                if not existing_value:
                    batch_data.enrichment_data[hostname][field] = value
                elif existing_value != value:
                    resolved_value = self._resolve_field_conflict(field, existing_value, value)
                    batch_data.enrichment_data[hostname][field] = resolved_value
    
    def _resolve_field_conflict(self, field_type: str, existing_value: str, new_value: str) -> str:
        generic_terms = ['unknown', 'other', 'generic', 'standard', 'default']
        
        existing_is_generic = any(term in existing_value.lower() for term in generic_terms)
        new_is_generic = any(term in new_value.lower() for term in generic_terms)
        
        if existing_is_generic and not new_is_generic:
            return new_value
        elif not existing_is_generic and new_is_generic:
            return existing_value
        
        if len(new_value) > len(existing_value) * 1.5:
            return new_value
        elif len(existing_value) > len(new_value) * 1.5:
            return existing_value
        
        if field_type in ['system_classification', 'infrastructure_type']:
            specificity_order = ['Server', 'Appliance', 'Database', 'Web Server', 'Application Server']
            
            for specific_type in specificity_order:
                if specific_type in new_value:
                    return new_value
                elif specific_type in existing_value:
                    return existing_value
        
        return existing_value
    
    def _calculate_batch_quality_metrics(self, batch_data: BatchedHostData) -> Dict[str, float]:
        if not batch_data.enrichment_data:
            return {
                'hostname_coverage': 0.0,
                'field_completeness': 0.0,
                'confidence_score': 0.0,
                'data_freshness': 0.0
            }
        
        total_hostnames = len(batch_data.hostnames)
        enriched_hostnames = len(batch_data.enrichment_data)
        hostname_coverage = enriched_hostnames / max(total_hostnames, 1)
        
        total_fields = 0
        populated_fields = 0
        
        key_fields = [
            'infrastructure_type', 'system_classification', 'global_region',
            'business_unit', 'edr_coverage', 'tanium_coverage', 'dlp_coverage'
        ]
        
        for hostname, data in batch_data.enrichment_data.items():
            for field in key_fields:
                total_fields += 1
                if field in data and data[field] and data[field] not in ['', 'unknown', 'null']:
                    populated_fields += 1
        
        field_completeness = populated_fields / max(total_fields, 1)
        
        confidence_scores = []
        for hostname in batch_data.hostnames:
            if hostname in batch_data.confidence_scores:
                confidence_scores.append(batch_data.confidence_scores[hostname])
            else:
                if hostname in batch_data.enrichment_data:
                    data_points = len([v for v in batch_data.enrichment_data[hostname].values() if v])
                    confidence_scores.append(min(data_points / 10.0, 1.0))
                else:
                    confidence_scores.append(0.0)
        
        avg_confidence = sum(confidence_scores) / max(len(confidence_scores), 1)
        
        data_freshness = 0.8
        
        return {
            'hostname_coverage': hostname_coverage,
            'field_completeness': field_completeness,
            'confidence_score': avg_confidence,
            'data_freshness': data_freshness
        }

class QueryOptimizer:
    
    @staticmethod
    def estimate_query_cost(query: str, table_size_bytes: int) -> int:
        base_cost = table_size_bytes * 0.1
        
        if 'JOIN' in query.upper():
            base_cost *= 2
        if 'GROUP BY' in query.upper():
            base_cost *= 1.5
        if 'ORDER BY' in query.upper():
            base_cost *= 1.2
        
        return int(base_cost)
    
    @staticmethod
    def optimize_partition_filter(table_meta: Dict) -> str:
        if not table_meta.get('is_partitioned'):
            return ""
        
        partition_field = table_meta.get('partition_field')
        if not partition_field:
            return ""
        
        row_count = table_meta.get('row_count', 0)
        
        if row_count > 100_000_000:
            days = 3
        elif row_count > 10_000_000:
            days = 7
        else:
            days = 30
        
        return f"AND `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)"

class SemanticFieldAnalyzer:
    
    def __init__(self):
        self.semantic_patterns = self._initialize_semantic_patterns()
    
    def _initialize_semantic_patterns(self) -> Dict[str, List[str]]:
        return {
            'hostname_patterns': [
                r'^[A-Z]{2,4}\d{2,4}$',
                r'^[A-Z]+-[A-Z0-9]+$',
                r'^[A-Z]+\d+-[A-Z]+$',
            ],
            'ip_patterns': [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
            ],
            'mac_patterns': [
                r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
            ],
            'fqdn_patterns': [
                r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$',
            ]
        }
    
    def analyze_field_semantics(self, field_name: str, sample_values: List[str]) -> Dict[str, Any]:
        analysis = {
            'data_type': 'string',
            'semantic_type': 'unknown',
            'confidence': 0.0,
            'patterns': [],
            'quality_score': 0.0
        }
        
        if not sample_values:
            return analysis
        
        for pattern_type, patterns in self.semantic_patterns.items():
            matches = 0
            for pattern in patterns:
                for value in sample_values:
                    if re.search(pattern, str(value)):
                        matches += 1
            
            if matches > len(sample_values) * 0.5:
                analysis['semantic_type'] = pattern_type.replace('_patterns', '')
                analysis['confidence'] = matches / len(sample_values)
                break
        
        non_null_values = [v for v in sample_values if v and str(v).strip()]
        unique_values = len(set(non_null_values))
        
        analysis['quality_score'] = unique_values / max(len(sample_values), 1)
        
        return analysis

class AdvancedDataFusion:
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_advanced_tables()
        self._lock = threading.RLock()
        self.batch_insert_cache = defaultdict(list)
        self.batch_size = 1000
        
    def _setup_advanced_tables(self):
        self.conn.execute("PRAGMA threads=8")
        self.conn.execute("PRAGMA memory_limit='4GB'")
        self.conn.execute("PRAGMA temp_directory='/tmp'")
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS intelligent_endpoints (
                primary_hostname VARCHAR PRIMARY KEY,
                original_hostnames TEXT,
                hostname_variants TEXT,
                semantic_category VARCHAR,
                confidence_score DOUBLE DEFAULT 1.0,
                extraction_priority INTEGER DEFAULT 50,
                data_quality_score DOUBLE DEFAULT 0.0,
                discovery_timestamp TIMESTAMP DEFAULT NOW(),
                last_seen TIMESTAMP DEFAULT NOW(),
                seen_count INTEGER DEFAULT 1,
                intelligence_metadata JSON
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ao1_log_visibility_inventory (
                hostname VARCHAR PRIMARY KEY,
                fqdn VARCHAR,
                ip_address VARCHAR,
                mac_address VARCHAR,
                infrastructure_type VARCHAR,
                system_classification VARCHAR,
                semantic_category VARCHAR,
                global_region VARCHAR,
                country VARCHAR,
                data_center VARCHAR,
                cloud_region VARCHAR,
                business_unit VARCHAR,
                cio VARCHAR,
                apm VARCHAR,
                application_class VARCHAR,
                edr_coverage VARCHAR DEFAULT 'No',
                tanium_coverage VARCHAR DEFAULT 'No',
                dlp_coverage VARCHAR DEFAULT 'No',
                network_log_types TEXT,
                endpoint_log_types TEXT,
                cloud_log_types TEXT,
                application_log_types TEXT,
                identity_log_types TEXT,
                url_fqdn_coverage VARCHAR DEFAULT 'No',
                public_ip_coverage VARCHAR DEFAULT 'No',
                cmdb_asset_visibility VARCHAR DEFAULT 'No',
                network_zones VARCHAR,
                ipam_coverage VARCHAR DEFAULT 'No',
                geolocation VARCHAR,
                vpc VARCHAR,
                domain_visibility VARCHAR,
                internal_external VARCHAR,
                controls VARCHAR,
                in_splunk BOOLEAN DEFAULT FALSE,
                in_chronicle BOOLEAN DEFAULT FALSE,
                in_gso BOOLEAN DEFAULT FALSE,
                found_in_cmdb BOOLEAN DEFAULT FALSE,
                log_volume_score DOUBLE DEFAULT 0.0,
                coverage_completeness_score DOUBLE DEFAULT 0.0,
                visibility_gap_severity VARCHAR DEFAULT 'unknown',
                ao1_recommendations TEXT,
                source_systems TEXT,
                source_count INTEGER DEFAULT 0,
                discovery_timestamp TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_hostname_seen ON intelligent_endpoints(seen_count DESC)",
            "CREATE INDEX IF NOT EXISTS idx_coverage_score ON ao1_log_visibility_inventory(coverage_completeness_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_visibility_gap ON ao1_log_visibility_inventory(visibility_gap_severity)"
        ]
        
        for index_sql in indexes:
            self.conn.execute(index_sql)
    
    def build_intelligent_inventory(self, batch_data: List[BatchedHostData]) -> Dict[str, Any]:
        with self._lock:
            start_time = time.time()
            
            stats = {
                'processed_endpoints': 0,
                'high_coverage_assets': 0,
                'complete_visibility_assets': 0,
                'total_data_points': 0
            }
            
            all_asset_profiles = []
            
            for batch in batch_data:
                for hostname, enrichment_data in batch.enrichment_data.items():
                    asset_profile = self._build_asset_profile(hostname, enrichment_data, batch.source_tables)
                    if asset_profile:
                        all_asset_profiles.append(asset_profile)
                        stats['processed_endpoints'] += 1
                        
                        if asset_profile.get('coverage_completeness_score', 0) > 70:
                            stats['high_coverage_assets'] += 1
                        
                        if asset_profile.get('source_count', 0) > 3:
                            stats['complete_visibility_assets'] += 1
            
            if all_asset_profiles:
                self._bulk_insert_assets(all_asset_profiles)
            
            processing_time = time.time() - start_time
            stats['processing_time'] = processing_time
            stats['total_data_points'] = self.conn.execute(
                "SELECT COUNT(*) FROM ao1_log_visibility_inventory"
            ).fetchone()[0]
            
            return stats
    
    def _build_asset_profile(self, hostname: str, enrichment_data: Dict, source_tables: Set[str]) -> Dict[str, Any]:
        source_tables_list = list(source_tables) if source_tables else []
        
        asset_profile = {
            'hostname': hostname,
            'fqdn': enrichment_data.get('fqdn', ''),
            'ip_address': enrichment_data.get('ip_address', ''),
            'mac_address': enrichment_data.get('mac_address', ''),
            'infrastructure_type': enrichment_data.get('infrastructure_type', ''),
            'system_classification': enrichment_data.get('system_classification', ''),
            'global_region': enrichment_data.get('global_region', ''),
            'country': enrichment_data.get('country', ''),
            'data_center': enrichment_data.get('data_center', ''),
            'cloud_region': enrichment_data.get('cloud_region', ''),
            'business_unit': enrichment_data.get('business_unit', ''),
            'cio': enrichment_data.get('cio', ''),
            'apm': enrichment_data.get('apm', ''),
            'application_class': enrichment_data.get('application_class', ''),
            'edr_coverage': enrichment_data.get('edr_coverage', 'No'),
            'tanium_coverage': enrichment_data.get('tanium_coverage', 'No'),
            'dlp_coverage': enrichment_data.get('dlp_coverage', 'No'),
            'network_log_types': enrichment_data.get('network_log_types', ''),
            'endpoint_log_types': enrichment_data.get('endpoint_log_types', ''),
            'cloud_log_types': enrichment_data.get('cloud_log_types', ''),
            'application_log_types': enrichment_data.get('application_log_types', ''),
            'identity_log_types': enrichment_data.get('identity_log_types', ''),
            'url_fqdn_coverage': enrichment_data.get('url_fqdn_coverage', 'No'),
            'public_ip_coverage': enrichment_data.get('public_ip_coverage', 'No'),
            'cmdb_asset_visibility': enrichment_data.get('cmdb_asset_visibility', 'No'),
            'network_zones': enrichment_data.get('network_zones', ''),
            'ipam_coverage': enrichment_data.get('ipam_coverage', 'No'),
            'geolocation': enrichment_data.get('geolocation', ''),
            'vpc': enrichment_data.get('vpc', ''),
            'domain_visibility': enrichment_data.get('domain_visibility', ''),
            'internal_external': enrichment_data.get('internal_external', ''),
            'controls': enrichment_data.get('controls', ''),
            'in_splunk': any('splunk' in str(table).lower() for table in source_tables_list),
            'in_chronicle': any('chronicle' in str(table).lower() for table in source_tables_list),
            'in_gso': any('gso' in str(table).lower() for table in source_tables_list),
            'found_in_cmdb': len(source_tables_list) > 0,
            'source_systems': ','.join(sorted(source_tables_list)),
            'source_count': len(source_tables_list)
        }
        
        log_coverage_factors = [
            bool(asset_profile['network_log_types']),
            bool(asset_profile['endpoint_log_types']),
            bool(asset_profile['cloud_log_types']),
            bool(asset_profile['application_log_types']),
            bool(asset_profile['identity_log_types'])
        ]
        log_coverage_score = sum(log_coverage_factors) / len(log_coverage_factors) * 100
        
        security_coverage_factors = [
            asset_profile['edr_coverage'] == 'Yes',
            asset_profile['tanium_coverage'] == 'Yes', 
            asset_profile['dlp_coverage'] == 'Yes'
        ]
        security_coverage_score = sum(security_coverage_factors) / len(security_coverage_factors) * 100
        
        visibility_factors = [
            asset_profile['in_splunk'],
            asset_profile['in_chronicle'],
            asset_profile['in_gso'],
            asset_profile['url_fqdn_coverage'] == 'Yes',
            asset_profile['cmdb_asset_visibility'] == 'Yes'
        ]
        visibility_score = sum(visibility_factors) / len(visibility_factors) * 100
        
        asset_profile['log_volume_score'] = log_coverage_score
        asset_profile['coverage_completeness_score'] = (log_coverage_score + security_coverage_score + visibility_score) / 3
        
        if asset_profile['coverage_completeness_score'] >= 80:
            asset_profile['visibility_gap_severity'] = 'low'
            asset_profile['ao1_recommendations'] = 'Excellent log visibility coverage across all domains'
        elif asset_profile['coverage_completeness_score'] >= 60:
            asset_profile['visibility_gap_severity'] = 'medium'
            asset_profile['ao1_recommendations'] = 'Good coverage with opportunities to improve security control visibility'
        elif asset_profile['coverage_completeness_score'] >= 40:
            asset_profile['visibility_gap_severity'] = 'high'
            asset_profile['ao1_recommendations'] = 'Significant visibility gaps - expand log collection and security tool coverage'
        else:
            asset_profile['visibility_gap_severity'] = 'critical'
            asset_profile['ao1_recommendations'] = 'Critical visibility gaps - immediate action required for CSOC monitoring'
        
        return asset_profile
    
    def _bulk_insert_assets(self, asset_data_list: List[Dict]):
        if not asset_data_list:
            return
        
        columns = list(asset_data_list[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        query = f"INSERT OR REPLACE INTO ao1_log_visibility_inventory ({column_names}) VALUES ({placeholders})"
        
        values_list = []
        for asset_data in asset_data_list:
            values = []
            for col in columns:
                value = asset_data[col]
                if isinstance(value, bool):
                    values.append(value)
                elif value is None:
                    values.append(None)
                else:
                    values.append(value)
            values_list.append(values)
        
        try:
            self.conn.executemany(query, values_list)
        except Exception as e:
            logger.error(f"Failed to insert assets: {e}")

class SuperOptimizedAO1Discovery:
    
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        self.client_manager = BigQueryClientManager(project_id)
        self.chronicle_client_manager = None
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
            if not self.chronicle_client_manager.test_connection():
                self.chronicle_client_manager = None
        except:
            self.chronicle_client_manager = None
        
        self.matcher = IntelligentContentMatcher()
        self.cache = IntelligentCacheManager(
            cache_dir=self.config.get('cache_dir', '.cache'),
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.db_path = self.config.get('database_path', 'ao1_optimized_cmdb.db')
        self.data_fusion = AdvancedDataFusion(self.db_path)
        
        self.batch_extractor = IntelligentFieldExtractor(
            self.client_manager, 
            self.matcher, 
            self.chronicle_client_manager,
            batch_size=self.config.get('batch_size', 500)
        )
        
        self.max_workers = min(self.config.get('max_workers', 16), mp.cpu_count() * 2)
        self.batch_size = self.config.get('batch_size', 500)
        
    async def execute_super_optimized_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        print("   Starting SuperOptimized AO1 Discovery...")
        
        try:
            print("   Step 1: Discovering prioritized tables...")
            all_table_metadata = await asyncio.wait_for(
                self._discover_prioritized_tables(), 
                timeout=600
            )
            print(f"   Found {len(all_table_metadata)} prioritized tables")
            
            if not all_table_metadata:
                print("   No tables found - check permissions")
                return {'error': 'No tables found', 'total_assets': 0}, {}
            
            print("   Step 2: Batch hostname discovery...")
            all_hostnames = await asyncio.wait_for(
                self._batch_hostname_discovery(all_table_metadata),
                timeout=1200
            )
            print(f"   Discovered {len(all_hostnames)} unique hostnames")
            
            if not all_hostnames:
                print("   No hostnames found")
                return {'error': 'No hostnames found', 'total_assets': 0}, {}
            
            print("   Step 3: Parallel batch enrichment...")
            batched_enrichment_data = await asyncio.wait_for(
                self._parallel_batch_enrichment(all_hostnames, all_table_metadata),
                timeout=1800
            )
            print(f"   Processed {len(batched_enrichment_data)} enrichment batches")
            
            print("   Step 4: Building intelligent inventory...")
            inventory_stats = self.data_fusion.build_intelligent_inventory(batched_enrichment_data)
            print(f"   Built inventory with {inventory_stats.get('processed_endpoints', 0)} assets")
            
            print("   Step 5: Cache optimization...")
            cache_optimization = self.cache.optimize()
            print("   Cache optimized")
            
            final_stats = self._generate_optimized_stats(time.time() - start_time, inventory_stats)
            analysis_queries = self._create_optimized_queries()
            
            return final_stats, analysis_queries
            
        except asyncio.TimeoutError as timeout_error:
            print(f"   SuperOptimized discovery timed out: {timeout_error}")
            return {'error': 'Discovery timed out', 'total_assets': 0}, {}
        except Exception as e:
            print(f"   SuperOptimized discovery failed: {e}")
            import traceback
            print("   Full traceback:")
            traceback.print_exc()
            raise
    
    async def _discover_prioritized_tables(self) -> List[Dict[str, Any]]:
        print("   Starting table discovery across projects...")
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
            print("   Will analyze both primary project and Chronicle")
        else:
            print("   Will analyze primary project only")
        
        all_metadata = []
        
        for i, project_id in enumerate(projects_to_analyze):
            print(f"   Processing project {i+1}/{len(projects_to_analyze)}: {project_id}")
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=400
                )
                all_metadata.extend(project_metadata)
                print(f"   Project {project_id} contributed {len(project_metadata)} tables")
            except asyncio.TimeoutError:
                print(f"   Project {project_id} timed out after 400s")
            except Exception as e:
                print(f"   Project {project_id} failed: {e}")
        
        print(f"   Total tables collected: {len(all_metadata)}")
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        print(f"   Starting discovery for project: {project_id}")
        try:
            with client_manager.get_client() as client:
                print(f"   Getting datasets for {project_id}...")
                
                try:
                    datasets = list(client.list_datasets(project=project_id))
                    print(f"   Found {len(datasets)} datasets in {project_id}")
                except Exception as e:
                    print(f"   Failed to list datasets in {project_id}: {e}")
                    return []
                
                if not datasets:
                    print(f"   No datasets found in {project_id}")
                    return []
                
                priority_datasets = self._prioritize_datasets([d.dataset_id for d in datasets])
                print(f"   Will analyze {len(priority_datasets)} priority datasets")
                
                all_metadata = []
                
                for j, dataset_id in enumerate(priority_datasets):
                    print(f"   Dataset {j+1}/{len(priority_datasets)}: {dataset_id}")
                    
                    try:
                        dataset_metadata = await asyncio.wait_for(
                            self._analyze_dataset_tables(client, project_id, dataset_id),
                            timeout=120
                        )
                        all_metadata.extend(dataset_metadata)
                        print(f"   Dataset {dataset_id} contributed {len(dataset_metadata)} tables")
                    except asyncio.TimeoutError:
                        print(f"   Dataset {dataset_id} timed out")
                    except Exception as e:
                        print(f"   Dataset {dataset_id} failed: {e}")
                
                print(f"   Project {project_id} complete: {len(all_metadata)} total tables")
                return all_metadata
                
        except Exception as e:
            print(f"   Project {project_id} discovery failed: {e}")
            return []
    
    async def _analyze_dataset_tables(self, client, project_id: str, dataset_id: str) -> List[Dict[str, Any]]:
        print(f"   Analyzing dataset: {project_id}.{dataset_id}")
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            print(f"   Dataset {dataset_id} has {len(tables)} tables")
            
            if not tables:
                return []
            
            table_metadata = []
            analyzed_count = 0
            
            for table_ref in tables:
                try:
                    full_table = client.get_table(table_ref)
                    
                    if not full_table.schema or full_table.num_rows == 0:
                        continue
                    
                    all_columns = [field.name for field in full_table.schema]
                    
                    hostname_indicators = ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node', 'system']
                    has_hostname = any(
                        any(indicator in col.lower() for indicator in hostname_indicators)
                        for col in all_columns
                    )
                    
                    if not has_hostname:
                        continue
                    
                    analyzed_count += 1
                    print(f"   Analyzing table {analyzed_count}: {table_ref.table_id}")
                    
                    sample_data = await self._get_optimized_sample(client, full_table)
                    
                    if not sample_data:
                        print(f"   No sample data for {table_ref.table_id}")
                        continue
                    
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
                        print(f"   No hostname column found in {table_ref.table_id}")
                        continue
                    
                    hostname_analysis = self._find_best_hostname_column(column_analysis, sample_data)
                    
                    if not hostname_analysis['primary_hostname_column']:
                        print(f"   No primary hostname column in {table_ref.table_id}")
                        continue
                    
                    data_richness = len(column_analysis) / max(len(all_columns), 1)
                    
                    table_metadata.append({
                        'project_id': project_id,
                        'dataset_id': dataset_id,
                        'table_id': table_ref.table_id,
                        'full_table_path': f"{project_id}.{dataset_id}.{table_ref.table_id}",
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
                    })
                    print(f"   Added table {table_ref.table_id} with richness {data_richness:.2f}")
                    
                except Exception as table_error:
                    print(f"   Table analysis failed for {table_ref.table_id}: {table_error}")
                    continue
            
            print(f"   Dataset {dataset_id} analysis complete: {len(table_metadata)} usable tables")
            return table_metadata
        except Exception as dataset_error:
            print(f"   Dataset {dataset_id} analysis failed: {dataset_error}")
            return []
    
    async def _get_optimized_sample(self, client, table_ref) -> Dict[str, List[str]]:
        try:
            sample_query = f"SELECT * FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`"
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                sample_query += f" WHERE `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)"
            
            sample_query += " LIMIT 5"
            
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
                        if len(str_value) > 0 and len(str_value) < 200:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
        except Exception:
            return {}
    
    def _find_best_hostname_column(self, column_analysis: Dict, sample_data: Dict) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_hostname_score(samples)
                final_score = confidence * hostname_score
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'final_score': final_score
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates
        }
    
    def _calculate_hostname_score(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        valid_count = sum(1 for sample in samples if self.matcher._validate_hostname(sample))
        unique_count = len(set(samples))
        
        return (valid_count / len(samples)) * (unique_count / len(samples))
    
    def _prioritize_datasets(self, dataset_ids: List[str]) -> List[str]:
        priority_keywords = [
            ('cmdb', 100), ('endpoint', 95), ('asset', 90), ('inventory', 85),
            ('security', 80), ('crowdstrike', 75), ('splunk', 70), ('chronicle', 65),
            ('monitoring', 60), ('infrastructure', 55), ('network', 50), ('server', 45)
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
    
    async def _batch_hostname_discovery(self, table_metadata: List[Dict]) -> List[str]:
        hostname_discovery_tasks = []
        
        for table_meta in table_metadata:
            task = self._discover_table_hostnames(table_meta)
            hostname_discovery_tasks.append(task)
        
        if hostname_discovery_tasks:
            hostname_results = await asyncio.gather(*hostname_discovery_tasks, return_exceptions=True)
            
            all_hostnames = set()
            
            for result in hostname_results:
                if isinstance(result, list):
                    for hostname in result:
                        normalized = self._normalize_hostname(hostname)
                        if normalized and normalized not in all_hostnames:
                            all_hostnames.add(normalized)
            
            return list(all_hostnames)
        
        return []
    
    async def _discover_table_hostnames(self, table_meta: Dict) -> List[str]:
        hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
        if not hostname_column:
            return []
        
        project_id = table_meta['project_id']
        table_path = table_meta['full_table_path']
        
        client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
        
        partition_filter = ""
        if table_meta.get('is_partitioned') and table_meta.get('partition_field'):
            partition_field = table_meta['partition_field']
            partition_filter = f"AND `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
        
        row_count = table_meta.get('row_count', 0)
        sampling_clause = ""
        if row_count > 50000000:
            sampling_clause = "TABLESAMPLE SYSTEM (5 PERCENT)"
        
        query = f"""
        SELECT DISTINCT UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname
        FROM `{table_path}` {sampling_clause}
        WHERE `{hostname_column}` IS NOT NULL
        AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) >= 2
        AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) <= 253
        AND TRIM(CAST(`{hostname_column}` AS STRING)) NOT LIKE '%@%'
        AND TRIM(CAST(`{hostname_column}` AS STRING)) NOT LIKE 'http%'
        AND TRIM(CAST(`{hostname_column}` AS STRING)) NOT LIKE '%/%'
        AND UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) NOT IN ('UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 'TEST', 'EXAMPLE', 'LOCALHOST')
        {partition_filter}
        ORDER BY hostname
        """
        
        try:
            with client_mgr.get_client() as client:
                job_config = bigquery.QueryJobConfig(
                    dry_run=True,
                    use_query_cache=False
                )
                
                dry_run_job = client.query(query, job_config=job_config)
                bytes_processed = dry_run_job.total_bytes_processed
                
                print(f"   Querying {table_path} (will process {bytes_processed / (1024*1024):.1f}MB)")
                
                job_config = bigquery.QueryJobConfig(
                    dry_run=False,
                    use_query_cache=True,
                    job_timeout_ms=60000
                )
                
                job = client.query(query, job_config=job_config)
                results = list(job.result())
                
                hostnames = []
                invalid_patterns = [
                    r'^\d+',
                    r'^[^a-zA-Z0-9]',
                    r'[^a-zA-Z0-9\-]',
                    r'\.{2,}',
                    r'\-{2,}',
                ]
                
                for row in results:
                    if not row[0]:
                        continue
                    
                    hostname = str(row[0]).strip()
                    
                    if not hostname or len(hostname) < 2 or len(hostname) > 253:
                        continue
                    
                    is_valid = True
                    for pattern in invalid_patterns:
                        if re.search(pattern, hostname):
                            is_valid = False
                            break
                    
                    if is_valid:
                        if self._is_likely_hostname(hostname):
                            hostnames.append(hostname)
                
                print(f"   Found {len(hostnames)} valid hostnames in {table_path}")
                return hostnames
                
        except Exception as e:
            print(f"   Hostname discovery failed for {table_path}: {e}")
            return []
    
    def _is_likely_hostname(self, hostname: str) -> bool:
        hostname = hostname.upper()
        
        reject_patterns = [
            'UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 'TEST', 'EXAMPLE', 
            'LOCALHOST', 'DUMMY', 'SAMPLE', 'PLACEHOLDER', 'DEFAULT',
            'ERROR', 'INVALID', 'MISSING', 'UNDEFINED', 'TEMP', 'TMP'
        ]
        
        if any(pattern in hostname for pattern in reject_patterns):
            return False
        
        error_indicators = ['ERROR', 'EXCEPTION', 'FAILED', 'TIMEOUT', 'CONNECTION']
        if any(indicator in hostname for indicator in error_indicators):
            return False
        
        if '\\' in hostname or hostname.count('/') > 1:
            return False
        
        if hostname.startswith('.') or hostname.endswith('.'):
            return False
        
        hostname_indicators = [
            r'^[A-Z]{2,}[0-9]+',
            r'^[A-Z]+-[A-Z0-9]',
            r'^[A-Z0-9]+\-[A-Z0-9]',
            r'(SERVER|SRV|WEB|APP|DB|DC|WIN|LIN)',
        ]
        
        for pattern in hostname_indicators:
            if re.search(pattern, hostname):
                return True
        
        if re.match(r'^[A-Z0-9\-]+', hostname) and 3 <= len(hostname) <= 64:
            if not hostname.isdigit() and len(set(hostname.replace('-', ''))) > 1:
                return True
        
        return False
    
    def _normalize_hostname(self, hostname: str) -> str:
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
        hostname = re.sub(r'[^A-Z0-9]+', '', hostname)
        
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Z0-9\-]', '', hostname)
        
        if len(hostname) < 2:
            return ""
        
        return hostname
    
    async def _parallel_batch_enrichment(self, hostnames: List[str], table_metadata: List[Dict]) -> List[BatchedHostData]:
        print(f"   Starting parallel enrichment for {len(hostnames)} hostnames using {len(table_metadata)} tables")
        
        hostname_batches = []
        for i in range(0, len(hostnames), self.batch_size):
            batch = hostnames[i:i + self.batch_size]
            hostname_batches.append(batch)
        
        print(f"   Created {len(hostname_batches)} hostname batches")
        
        enrichment_tasks = []
        for batch in hostname_batches:
            task = self.batch_extractor.extract_fields_batch_intelligent(batch, table_metadata)
            enrichment_tasks.append(task)
        
        if enrichment_tasks:
            batch_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            
            valid_results = []
            for result in batch_results:
                if isinstance(result, BatchedHostData):
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    print(f"   Batch enrichment failed: {result}")
            
            print(f"   Enrichment complete: {len(valid_results)} successful batches")
            return valid_results
        
        return []
    
    def _generate_optimized_stats(self, processing_time: float, inventory_stats: Dict) -> Dict[str, Any]:
        return {
            'processing_time': processing_time,
            'total_assets': inventory_stats.get('processed_endpoints', 0),
            'high_coverage_assets': inventory_stats.get('high_coverage_assets', 0),
            'complete_visibility_assets': inventory_stats.get('complete_visibility_assets', 0),
            'total_data_points': inventory_stats.get('total_data_points', 0),
            'database_path': self.db_path,
            'discovery_method': 'super_optimized',
            'engine_type': 'SuperOptimized',
            'cache_stats': self.cache.get_stats() if hasattr(self.cache, 'get_stats') else {}
        }
    
    def _create_optimized_queries(self) -> Dict[str, str]:
        return {
            'overview': """
                SELECT * FROM ao1_log_visibility_inventory 
                ORDER BY coverage_completeness_score DESC
                LIMIT 100;
            """,
            'coverage_summary': """
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                    SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                    SUM(CASE WHEN edr_coverage = 'Yes' THEN 1 ELSE 0 END) as edr_coverage,
                    AVG(coverage_completeness_score) as avg_coverage_score
                FROM ao1_log_visibility_inventory;
            """,
            'visibility_gaps': """
                SELECT 
                    visibility_gap_severity,
                    COUNT(*) as asset_count,
                    AVG(coverage_completeness_score) as avg_score
                FROM ao1_log_visibility_inventory
                GROUP BY visibility_gap_severity
                ORDER BY avg_score DESC;
            """,
            'top_assets': """
                SELECT hostname, infrastructure_type, system_classification, 
                       coverage_completeness_score, visibility_gap_severity
                FROM ao1_log_visibility_inventory
                WHERE coverage_completeness_score > 70
                ORDER BY coverage_completeness_score DESC
                LIMIT 20;
            """,
            'infrastructure_breakdown': """
                SELECT 
                    infrastructure_type,
                    COUNT(*) as count,
                    AVG(coverage_completeness_score) as avg_coverage
                FROM ao1_log_visibility_inventory
                WHERE infrastructure_type != ''
                GROUP BY infrastructure_type
                ORDER BY count DESC;
            """,
            'endpoint_intelligence': """
                SELECT 
                    primary_hostname,
                    original_hostnames,
                    seen_count,
                    confidence_score
                FROM intelligent_endpoints
                ORDER BY seen_count DESC
                LIMIT 50;
            """
        }
    
    def close(self):
        if hasattr(self, 'data_fusion') and self.data_fusion:
            if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
                self.data_fusion.conn.close()

class SimpleProgressReporter:
    @staticmethod
    def info(msg: str):
        print(f"   {msg}")
    
    @staticmethod
    def success(msg: str):
        print(f"   {msg}")
    
    @staticmethod
    def progress(step: int, total: int, msg: str):
        pct = (step / total * 100) if total > 0 else 0
        print(f"   {pct:5.1f}% ({step:,}/{total:,})   {msg}")

class SimpleOptimizedAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        SimpleProgressReporter.info("Initializing simple discovery components...")
        
        self.client_manager = BigQueryClientManager(project_id)
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
            if not self.chronicle_client_manager.test_connection():
                self.chronicle_client_manager = None
        except:
            self.chronicle_client_manager = None
        
        self.matcher = IntelligentContentMatcher()
        self.cache = IntelligentCacheManager(
            cache_dir=self.config.get('cache_dir', '.cache'),
            max_memory_mb=self.config.get('max_memory_mb', 512),
            max_disk_gb=self.config.get('max_disk_gb', 5)
        )
        
        self.db_path = self.config.get('database_path', 'ao1_simple_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        self._setup_simple_tables()
        
        SimpleProgressReporter.success("Simple discovery components ready")
    
    def _setup_simple_tables(self):
        self.conn.execute("PRAGMA threads=4")
        self.conn.execute("PRAGMA memory_limit='1GB'")
        
        self.conn.execute("""CREATE TABLE IF NOT EXISTS simple_ao1_inventory (hostname VARCHAR PRIMARY KEY, infrastructure_type VARCHAR, system_classification VARCHAR, global_region VARCHAR, business_unit VARCHAR, in_splunk BOOLEAN DEFAULT FALSE, in_chronicle BOOLEAN DEFAULT FALSE, edr_coverage VARCHAR DEFAULT 'No', source_count INTEGER DEFAULT 0, coverage_completeness_score DOUBLE DEFAULT 0.0, visibility_gap_severity VARCHAR DEFAULT 'unknown', discovery_timestamp TIMESTAMP DEFAULT NOW())""")
    
    async def execute_simple_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        SimpleProgressReporter.info("Starting simple optimized discovery")
        
        try:
            SimpleProgressReporter.info("Phase 1: Finding suitable tables")
            table_metadata = await self._discover_simple_tables()
            
            if not table_metadata:
                return {'error': 'No suitable tables found', 'total_assets': 0}, {}
            
            SimpleProgressReporter.info("Phase 2: Extracting hostnames")
            all_hostnames = await self._extract_simple_hostnames(table_metadata)
            
            if not all_hostnames:
                return {'error': 'No hostnames found', 'total_assets': 0}, {}
            
            SimpleProgressReporter.info("Phase 3: Building asset inventory")
            asset_count = self._build_simple_inventory(all_hostnames, table_metadata)
            
            processing_time = time.time() - start_time
            stats = {
                'processing_time': processing_time,
                'total_assets': asset_count,
                'database_path': self.db_path,
                'discovery_method': 'simple_optimized',
                'engine_type': 'SimpleOptimized'
            }
            
            queries = {
                'simple_overview': "SELECT * FROM simple_ao1_inventory ORDER BY coverage_completeness_score DESC;",
                'coverage_summary': "SELECT COUNT(*) as total, SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk, SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle, SUM(CASE WHEN edr_coverage = 'Yes' THEN 1 ELSE 0 END) as edr_coverage FROM simple_ao1_inventory;"
            }
            
            SimpleProgressReporter.success(f"Simple discovery complete: {asset_count} assets in {processing_time:.1f}s")
            return stats, queries
            
        except Exception as e:
            SimpleProgressReporter.info(f"Simple discovery failed: {e}")
            return {'error': str(e), 'total_assets': 0}, {}
    
    async def _discover_simple_tables(self) -> List[Dict]:
        tables = []
        
        try:
            with self.client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=self.project_id))
                SimpleProgressReporter.info(f"Found {len(datasets)} datasets")
                
                for i, dataset in enumerate(datasets):
                    SimpleProgressReporter.progress(i+1, len(datasets), f"Checking {dataset.dataset_id}")
                    
                    try:
                        dataset_ref = client.dataset(dataset.dataset_id)
                        dataset_tables = list(client.list_tables(dataset_ref))
                        
                        for table_ref in dataset_tables:
                            try:
                                full_table = client.get_table(table_ref)
                                if full_table.num_rows and full_table.num_rows > 0:
                                    columns = [field.name for field in full_table.schema]
                                    hostname_col = self._find_hostname_column(columns)
                                    if hostname_col:
                                        tables.append({
                                            'project_id': self.project_id,
                                            'table_path': f"{self.project_id}.{dataset.dataset_id}.{table_ref.table_id}",
                                            'hostname_column': hostname_col,
                                            'table_id': table_ref.table_id,
                                            'row_count': full_table.num_rows
                                        })
                            except:
                                continue
                    except:
                        continue
        except Exception as e:
            SimpleProgressReporter.info(f"Table discovery failed: {e}")
        
        SimpleProgressReporter.success(f"Found {len(tables)} usable tables")
        return tables
    
    def _find_hostname_column(self, columns: List[str]) -> Optional[str]:
        for col in columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['host', 'endpoint', 'computer', 'device', 'server', 'machine']):
                return col
        return None
    
    async def _extract_simple_hostnames(self, tables: List[Dict]) -> List[str]:
        all_hostnames = set()
        
        for i, table in enumerate(tables):
            SimpleProgressReporter.progress(i+1, len(tables), f"Extracting from {table['table_id']}")
            
            row_count = table.get('row_count', 0)
            sampling_clause = ""
            if row_count > 10000000:
                sampling_clause = "TABLESAMPLE SYSTEM (10 PERCENT)"
            
            query = f"SELECT DISTINCT UPPER(TRIM(`{table['hostname_column']}`)) as hostname FROM `{table['table_path']}` {sampling_clause} WHERE `{table['hostname_column']}` IS NOT NULL"
            
            try:
                with self.client_manager.get_client() as client:
                    job = client.query(query)
                    results = list(job.result())
                    
                    for row in results:
                        hostname = str(row[0]) if row[0] else ""
                        if hostname and len(hostname) > 2:
                            all_hostnames.add(hostname)
            except:
                continue
        
        SimpleProgressReporter.success(f"Extracted {len(all_hostnames)} unique hostnames")
        return list(all_hostnames)
    
    def _build_simple_inventory(self, hostnames: List[str], tables: List[Dict]) -> int:
        assets = []
        
        for i, hostname in enumerate(hostnames):
            if i % 50 == 0:
                SimpleProgressReporter.progress(i+1, len(hostnames), "Building assets")
            
            asset = {
                'hostname': hostname,
                'infrastructure_type': '',
                'system_classification': '',
                'global_region': '',
                'business_unit': '',
                'in_splunk': any('splunk' in t['table_path'].lower() for t in tables),
                'in_chronicle': any('chronicle' in t['table_path'].lower() for t in tables),
                'edr_coverage': 'Yes' if any('crowdstrike' in t['table_path'].lower() for t in tables) else 'No',
                'source_count': len(tables),
                'coverage_completeness_score': 50.0,
                'visibility_gap_severity': 'medium'
            }
            assets.append(asset)
        
        if assets:
            SimpleProgressReporter.info("Inserting assets into database")
            columns = list(assets[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT OR REPLACE INTO simple_ao1_inventory ({', '.join(columns)}) VALUES ({placeholders})"
            
            try:
                values_list = [[asset[col] for col in columns] for asset in assets]
                self.conn.executemany(query, values_list)
            except Exception as e:
                SimpleProgressReporter.info(f"Database insert failed: {e}")
        
        return len(assets)
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

class IntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        self.client_manager = BigQueryClientManager(project_id)
        self.matcher = IntelligentContentMatcher()
        self.cache = IntelligentCacheManager()
        self.db_path = self.config.get('database_path', 'ao1_intelligent_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        self._setup_basic_tables()
    
    def _setup_basic_tables(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS intelligent_ao1_inventory (hostname VARCHAR PRIMARY KEY, infrastructure_type VARCHAR, system_classification VARCHAR, source_count INTEGER DEFAULT 0, discovery_timestamp TIMESTAMP DEFAULT NOW())""")
    
    async def execute_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        stats = {
            'processing_time': time.time() - start_time,
            'total_assets': 0,
            'database_path': self.db_path,
            'discovery_method': 'intelligent',
            'engine_type': 'Intelligent'
        }
        queries = {
            'intelligent_overview': "SELECT * FROM intelligent_ao1_inventory;"
        }
        return stats, queries
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

if __name__ == "__main__":
    import sys
    
    def main():
        if len(sys.argv) < 2:
            print("Usage: python script.py <project_id> [discovery_type]")
            print("Discovery types: simple, super (default: simple)")
            sys.exit(1)
        
        project_id = sys.argv[1]
        discovery_type = sys.argv[2] if len(sys.argv) > 2 else "simple"
        
        async def run_discovery():
            if discovery_type.lower() == "super":
                print("Starting SuperOptimized AO1 Discovery...")
                discovery = SuperOptimizedAO1Discovery(project_id)
                stats, queries = await discovery.execute_super_optimized_discovery()
            else:
                print("Starting Simple AO1 Discovery...")
                discovery = SimpleOptimizedAO1Discovery(project_id)
                stats, queries = await discovery.execute_simple_discovery()
            
            print("\n" + "="*50)
            print("DISCOVERY COMPLETE")
            print("="*50)
            print(f"Processing Time: {stats.get('processing_time', 0):.2f} seconds")
            print(f"Total Assets: {stats.get('total_assets', 0):,}")
            print(f"Database Path: {stats.get('database_path', 'N/A')}")
            print(f"Discovery Method: {stats.get('discovery_method', 'N/A')}")
            
            if 'high_coverage_assets' in stats:
                print(f"High Coverage Assets: {stats['high_coverage_assets']:,}")
            
            print("\nSample Queries:")
            for name, query in queries.items():
                print(f"\n-- {name.upper()} --")
                print(query.strip())
            
            discovery.close()
        
        asyncio.run(run_discovery())
    
    main()