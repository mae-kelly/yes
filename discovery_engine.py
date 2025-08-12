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
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import statistics
from itertools import combinations, islice
import pickle
import multiprocessing as mp
from functools import partial
import asyncpg
import aiofiles

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

@dataclass
class BatchedHostData:
    hostnames: List[str]
    enrichment_data: Dict[str, Dict[str, Any]]
    source_tables: Set[str]
    processing_time: float = 0.0

class BatchedFieldExtractor:
    def __init__(self, client_manager: BigQueryClientManager, matcher: IntelligentContentMatcher, batch_size: int = 500):
        self.client_manager = client_manager
        self.matcher = matcher
        self.batch_size = batch_size
        self.field_extraction_cache = {}
        self.table_analysis_cache = {}
        
    async def extract_fields_batch(self, hostnames: List[str], table_metadata: List[Dict]) -> BatchedHostData:
        start_time = time.time()
        batch_data = BatchedHostData(
            hostnames=hostnames,
            enrichment_data={},
            source_tables=set()
        )
        
        hostname_variants = {}
        for hostname in hostnames:
            variants = self._generate_hostname_variants(hostname)
            hostname_variants[hostname] = variants
        
        all_variants = set()
        for variants in hostname_variants.values():
            all_variants.update(variants)
        
        extraction_tasks = []
        for table_meta in table_metadata:
            if self._table_contains_any_hostname(table_meta, all_variants):
                task = self._extract_batch_from_table(all_variants, table_meta, hostname_variants)
                extraction_tasks.append(task)
        
        if extraction_tasks:
            batch_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, dict):
                    for hostname, host_data in result.items():
                        if hostname not in batch_data.enrichment_data:
                            batch_data.enrichment_data[hostname] = {}
                        self._merge_host_data(batch_data.enrichment_data[hostname], host_data)
                        if 'source_table' in host_data:
                            batch_data.source_tables.add(host_data['source_table'])
        
        batch_data.processing_time = time.time() - start_time
        return batch_data
    
    async def _extract_batch_from_table(self, all_variants: Set[str], table_meta: Dict, hostname_mapping: Dict) -> Dict[str, Dict]:
        table_path = table_meta['full_table_path']
        hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
        column_analysis = table_meta.get('column_analysis', {})
        
        if not hostname_column:
            return {}
        
        project_id = table_meta['project_id']
        client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
        
        hostname_variants_list = list(all_variants)[:1000]
        hostname_filter = "', '".join([h.replace("'", "''") for h in hostname_variants_list])
        
        select_fields = [f"UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname"]
        field_mappings = {}
        
        priority_fields = {
            'operating_system': ['os', 'operating', 'platform', 'system_type', 'osversion', 'os_name'],
            'criticality': ['critical', 'priority', 'tier', 'importance', 'level', 'class'],
            'cost_center': ['cost', 'billing', 'charge', 'budget', 'financial', 'accounting'],
            'owner': ['owner', 'responsible', 'admin', 'contact', 'manager', 'user'],
            'system_classification': ['classification', 'category', 'type', 'class', 'kind', 'nature'],
            'country': ['country', 'nation', 'countrycode', 'cc', 'nationality'],
            'data_center': ['datacenter', 'dc', 'facility', 'site', 'location_detail'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region', 'region_cloud'],
            'cio': ['cio', 'chief', 'information', 'officer'],
            'apm': ['apm', 'application', 'performance', 'monitoring'],
            'serial_number': ['serial', 'sn', 'serialno', 'serialnumber', 'asset_tag'],
            'model': ['model', 'hardware', 'device_model', 'machine_type'],
            'manufacturer': ['manufacturer', 'vendor', 'make', 'brand', 'oem'],
            'location': ['location', 'physical', 'building', 'floor', 'room'],
            'department': ['department', 'dept', 'division', 'team', 'group'],
            'function': ['function', 'purpose', 'role', 'service_type'],
            'compliance': ['compliance', 'regulation', 'standard', 'certification'],
            'backup_status': ['backup', 'backup_status', 'protected', 'recovery'],
            'patching_group': ['patch', 'update', 'maintenance', 'group'],
            'support_group': ['support', 'support_group', 'team_support'],
            'monitoring_group': ['monitoring', 'monitor', 'observation'],
            'network_zone': ['zone', 'network_zone', 'security_zone', 'segment'],
            'vlan': ['vlan', 'network', 'subnet_vlan', 'net_id'],
            'domain': ['domain', 'ad_domain', 'dns_domain', 'realm'],
            'cluster': ['cluster', 'cluster_name', 'group_cluster'],
            'virtualization': ['virtual', 'hypervisor', 'vm_host', 'container_host'],
            'licensing': ['license', 'licensing', 'software_license'],
            'encryption': ['encryption', 'encrypted', 'crypto', 'secure'],
            'antivirus': ['antivirus', 'av', 'endpoint_protection', 'security_agent'],
            'installed_software': ['software', 'applications', 'installed', 'programs'],
            'cpu_info': ['cpu', 'processor', 'cores', 'cpu_model'],
            'memory_gb': ['memory', 'ram', 'mem_gb', 'total_memory'],
            'disk_gb': ['disk', 'storage', 'disk_gb', 'total_disk'],
            'last_boot': ['boot', 'startup', 'last_boot', 'uptime'],
            'install_date': ['install', 'installation', 'deployed', 'created'],
            'last_seen': ['seen', 'last_seen', 'last_contact', 'heartbeat'],
            'status': ['status', 'state', 'condition', 'health'],
            'availability': ['availability', 'uptime_pct', 'sla', 'available']
        }
        
        for column, analysis in column_analysis.items():
            if column == hostname_column:
                continue
            
            field_type, confidence, metadata = analysis
            if confidence > 0.2:
                safe_column = column.replace('`', '``')
                select_fields.append(f"CAST(`{safe_column}` AS STRING) as `{safe_column}`")
                field_mappings[safe_column] = field_type
        
        for column in table_meta.get('all_columns', []):
            if column == hostname_column or column in field_mappings:
                continue
            
            column_lower = column.lower()
            for target_field, keywords in priority_fields.items():
                if any(keyword in column_lower for keyword in keywords):
                    safe_column = column.replace('`', '``')
                    select_fields.append(f"CAST(`{safe_column}` AS STRING) as `{safe_column}`")
                    field_mappings[safe_column] = target_field
                    break
        
        if len(select_fields) == 1:
            return {}
        
        partition_filter = ""
        if table_meta.get('is_partitioned') and table_meta.get('partition_field'):
            partition_field = table_meta['partition_field']
            partition_filter = f"AND `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
        
        query = f"""
        SELECT {', '.join(select_fields)}
        FROM `{table_path}`
        WHERE UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) IN ('{hostname_filter}')
            AND `{hostname_column}` IS NOT NULL
            AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) >= 2
            {partition_filter}
        LIMIT 10000
        """
        
        try:
            with client_mgr.get_client() as client:
                job_config = bigquery.QueryJobConfig(
                    dry_run=True,
                    use_query_cache=False,
                    maximum_bytes_billed=200 * 1024 * 1024
                )
                
                dry_run_job = client.query(query, job_config=job_config)
                
                if dry_run_job.total_bytes_processed > 100 * 1024 * 1024:
                    return {}
                
                job_config = bigquery.QueryJobConfig(
                    dry_run=False,
                    use_query_cache=True,
                    maximum_bytes_billed=200 * 1024 * 1024
                )
                
                job = client.query(query, job_config=job_config)
                results = list(job.result())
                
                host_data_map = defaultdict(lambda: {'source_table': table_path})
                
                for row in results:
                    if not row[0]:
                        continue
                    
                    row_hostname = self._normalize_hostname(str(row[0]))
                    if not row_hostname:
                        continue
                    
                    original_hostname = None
                    for hostname, variants in hostname_mapping.items():
                        if row_hostname in variants:
                            original_hostname = hostname
                            break
                    
                    if not original_hostname:
                        continue
                    
                    for i, field_name in enumerate(select_fields[1:], 1):
                        if i < len(row) and row[i]:
                            clean_field_name = field_name.split(' as ')[-1].strip('`')
                            field_type = field_mappings.get(clean_field_name, 'unknown')
                            value = str(row[i]).strip()
                            
                            if value and len(value) > 0 and value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '', 'NAN']:
                                processed_value = self._process_field_value(field_type, value, clean_field_name)
                                if processed_value:
                                    host_data_map[original_hostname][field_type] = processed_value
                
                return dict(host_data_map)
                
        except Exception as e:
            return {}
    
    def _process_field_value(self, field_type: str, value: str, column_name: str) -> Optional[str]:
        value = value.strip()
        column_lower = column_name.lower()
        
        if field_type == 'operating_system' or any(os_term in column_lower for os_term in ['os', 'operating', 'platform']):
            os_mappings = {
                'windows': 'Windows', 'win': 'Windows', 'microsoft': 'Windows',
                'linux': 'Linux', 'ubuntu': 'Ubuntu', 'centos': 'CentOS', 'rhel': 'Red Hat',
                'redhat': 'Red Hat', 'debian': 'Debian', 'suse': 'SUSE', 'fedora': 'Fedora',
                'macos': 'macOS', 'darwin': 'macOS', 'osx': 'macOS',
                'unix': 'Unix', 'aix': 'AIX', 'solaris': 'Solaris', 'freebsd': 'FreeBSD'
            }
            value_lower = value.lower()
            for pattern, normalized in os_mappings.items():
                if pattern in value_lower:
                    return normalized
            return value if len(value) > 2 else None
        
        elif field_type == 'criticality' or any(crit_term in column_lower for crit_term in ['critical', 'priority', 'tier']):
            crit_mappings = {
                'critical': 'Critical', 'high': 'High', 'medium': 'Medium', 'low': 'Low',
                'tier1': 'Tier 1', 'tier2': 'Tier 2', 'tier3': 'Tier 3',
                'production': 'Critical', 'prod': 'Critical', 'mission': 'Critical'
            }
            value_lower = value.lower()
            for pattern, normalized in crit_mappings.items():
                if pattern in value_lower:
                    return normalized
            return value if len(value) > 1 else None
        
        elif field_type == 'environment' or 'env' in column_lower:
            env_mappings = {
                'production': 'Production', 'prod': 'Production',
                'development': 'Development', 'dev': 'Development',
                'test': 'Test', 'testing': 'Test', 'qa': 'QA',
                'staging': 'Staging', 'stage': 'Staging', 'preprod': 'Pre-Production',
                'uat': 'UAT', 'sit': 'SIT', 'demo': 'Demo', 'sandbox': 'Sandbox'
            }
            value_lower = value.lower()
            for pattern, normalized in env_mappings.items():
                if pattern in value_lower:
                    return normalized
            return value if len(value) > 1 else None
        
        elif field_type == 'infrastructure_type' or any(infra_term in column_lower for infra_term in ['type', 'infra', 'platform']):
            infra_mappings = {
                'physical': 'Physical', 'bare': 'Physical', 'metal': 'Physical',
                'virtual': 'Virtual', 'vm': 'Virtual', 'vmware': 'Virtual',
                'cloud': 'Cloud', 'aws': 'AWS', 'azure': 'Azure', 'gcp': 'GCP',
                'container': 'Container', 'docker': 'Container', 'kubernetes': 'Container'
            }
            value_lower = value.lower()
            for pattern, normalized in infra_mappings.items():
                if pattern in value_lower:
                    return normalized
            return value if len(value) > 2 else None
        
        elif field_type == 'region' or any(region_term in column_lower for region_term in ['region', 'location', 'geo']):
            region_mappings = {
                'us-east': 'US East', 'us-west': 'US West', 'us-central': 'US Central',
                'eu-west': 'EU West', 'eu-central': 'EU Central', 'eu-north': 'EU North',
                'ap-southeast': 'AP Southeast', 'ap-northeast': 'AP Northeast'
            }
            value_lower = value.lower()
            for pattern, normalized in region_mappings.items():
                if pattern in value_lower:
                    return normalized
            return value if len(value) > 1 else None
        
        elif field_type == 'status' or 'status' in column_lower:
            status_mappings = {
                'active': 'Active', 'running': 'Active', 'online': 'Online',
                'inactive': 'Inactive', 'offline': 'Offline', 'down': 'Down',
                'maintenance': 'Maintenance', 'maint': 'Maintenance'
            }
            value_lower = value.lower()
            for pattern, normalized in status_mappings.items():
                if pattern in value_lower:
                    return normalized
            return value if len(value) > 1 else None
        
        elif any(numeric_term in column_lower for numeric_term in ['memory', 'disk', 'cpu', 'cores']):
            numeric_value = re.search(r'(\d+(?:\.\d+)?)', value)
            if numeric_value:
                return numeric_value.group(1)
            return None
        
        return value if len(value) > 0 and len(value) < 500 else None
    
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
        hostname = re.sub(r'[^A-Z0-9]+$', '', hostname)
        
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Z0-9\-]', '', hostname)
        
        if len(hostname) < 2:
            return ""
        
        return hostname
    
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
    
    def _table_contains_any_hostname(self, table_meta: Dict, hostname_variants: Set[str]) -> bool:
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
    
    def _merge_host_data(self, base_data: Dict, new_data: Dict):
        for field, value in new_data.items():
            if field == 'source_table':
                continue
            if field not in base_data or not base_data[field]:
                base_data[field] = value

class OptimizedDataFusion:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_optimized_tables()
        self._lock = threading.RLock()
        self.batch_insert_cache = defaultdict(list)
        self.batch_size = 1000
        
    def _setup_optimized_tables(self):
        self.conn.execute("PRAGMA threads=8")
        self.conn.execute("PRAGMA memory_limit='4GB'")
        
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
            serial_number VARCHAR,
            model VARCHAR,
            manufacturer VARCHAR,
            location VARCHAR,
            department VARCHAR,
            function VARCHAR,
            compliance VARCHAR,
            backup_status VARCHAR,
            patching_group VARCHAR,
            support_group VARCHAR,
            monitoring_group VARCHAR,
            network_zone VARCHAR,
            vlan VARCHAR,
            domain VARCHAR,
            cluster VARCHAR,
            virtualization VARCHAR,
            licensing VARCHAR,
            encryption VARCHAR,
            antivirus VARCHAR,
            installed_software TEXT,
            cpu_info VARCHAR,
            memory_gb INTEGER,
            disk_gb INTEGER,
            last_boot TIMESTAMP,
            install_date TIMESTAMP,
            last_seen TIMESTAMP,
            status VARCHAR,
            availability VARCHAR,
            
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
        
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_hostname_seen ON intelligent_endpoints(seen_count DESC)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_data_quality ON intelligent_asset_inventory(data_quality_score DESC)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_intelligence ON intelligent_asset_inventory(intelligence_score DESC)")
    
    def batch_register_endpoints(self, hostname_data: List[Tuple[str, str]]):
        with self._lock:
            for primary_hostname, original_hostname in hostname_data:
                self.batch_insert_cache['endpoints'].append((primary_hostname, original_hostname))
                
                if len(self.batch_insert_cache['endpoints']) >= self.batch_size:
                    self._flush_endpoint_batch()
    
    def _flush_endpoint_batch(self):
        if not self.batch_insert_cache['endpoints']:
            return
        
        batch = self.batch_insert_cache['endpoints']
        self.batch_insert_cache['endpoints'] = []
        
        try:
            hostname_counts = Counter(item[0] for item in batch)
            
            for primary_hostname, count in hostname_counts.items():
                original_hostnames = [item[1] for item in batch if item[0] == primary_hostname]
                
                existing = self.conn.execute("""
                    SELECT original_hostnames, seen_count 
                    FROM intelligent_endpoints 
                    WHERE primary_hostname = ?
                """, (primary_hostname,)).fetchone()
                
                if existing:
                    orig_hostnames = set((existing[0] or "").split(","))
                    orig_hostnames.update(original_hostnames)
                    seen_count = existing[1] + count
                    
                    self.conn.execute("""
                        UPDATE intelligent_endpoints 
                        SET original_hostnames = ?, last_seen = CURRENT_TIMESTAMP, seen_count = ?
                        WHERE primary_hostname = ?
                    """, (",".join(orig_hostnames), seen_count, primary_hostname))
                else:
                    self.conn.execute("""
                        INSERT INTO intelligent_endpoints 
                        (primary_hostname, original_hostnames, hostname_variants, confidence_score, seen_count)
                        VALUES (?, ?, ?, ?, ?)
                    """, (primary_hostname, ",".join(original_hostnames), "", 1.0, count))
        except Exception:
            pass
    
    def build_optimized_inventory(self, batch_data: List[BatchedHostData]) -> Dict[str, int]:
        with self._lock:
            stats = {
                'processed_endpoints': 0,
                'high_quality_assets': 0,
                'enriched_assets': 0,
                'total_data_points': 0
            }
            
            all_asset_data = []
            
            for batch in batch_data:
                for hostname, enrichment_data in batch.enrichment_data.items():
                    asset_data = self._build_complete_asset_profile(hostname, enrichment_data, batch.source_tables)
                    if asset_data:
                        all_asset_data.append(asset_data)
                        stats['processed_endpoints'] += 1
                        
                        if asset_data.get('data_quality_score', 0) > 70:
                            stats['high_quality_assets'] += 1
                        
                        if asset_data.get('source_count', 0) > 2:
                            stats['enriched_assets'] += 1
            
            if all_asset_data:
                self._batch_insert_assets(all_asset_data)
            
            self._flush_endpoint_batch()
            
            stats['total_data_points'] = self.conn.execute("""
                SELECT COUNT(*) FROM intelligent_endpoint_data
            """).fetchone()[0]
            
            return stats
    
    def _build_complete_asset_profile(self, hostname: str, enrichment_data: Dict, source_tables: Set[str]) -> Dict[str, Any]:
        asset_profile = {
            'hostname': hostname,
            'fqdn': enrichment_data.get('fqdn', ''),
            'ip_addresses': ','.join(enrichment_data.get('ip_addresses', [])),
            'mac_addresses': ','.join(enrichment_data.get('mac_addresses', [])),
            'infrastructure_type': enrichment_data.get('infrastructure_type', ''),
            'system_classification': enrichment_data.get('system_classification', ''),
            'operating_system': enrichment_data.get('operating_system', ''),
            'global_region': enrichment_data.get('global_region', ''),
            'country': enrichment_data.get('country', ''),
            'data_center': enrichment_data.get('data_center', ''),
            'cloud_region': enrichment_data.get('cloud_region', ''),
            'business_unit': enrichment_data.get('business_unit', ''),
            'cio': enrichment_data.get('cio', ''),
            'apm': enrichment_data.get('apm', ''),
            'application_class': enrichment_data.get('application_class', ''),
            'cost_center': enrichment_data.get('cost_center', ''),
            'owner': enrichment_data.get('owner', ''),
            'environment': enrichment_data.get('environment', ''),
            'criticality': enrichment_data.get('criticality', ''),
            'serial_number': enrichment_data.get('serial_number', ''),
            'model': enrichment_data.get('model', ''),
            'manufacturer': enrichment_data.get('manufacturer', ''),
            'location': enrichment_data.get('location', ''),
            'department': enrichment_data.get('department', ''),
            'function': enrichment_data.get('function', ''),
            'compliance': enrichment_data.get('compliance', ''),
            'backup_status': enrichment_data.get('backup_status', ''),
            'patching_group': enrichment_data.get('patching_group', ''),
            'support_group': enrichment_data.get('support_group', ''),
            'monitoring_group': enrichment_data.get('monitoring_group', ''),
            'network_zone': enrichment_data.get('network_zone', ''),
            'vlan': enrichment_data.get('vlan', ''),
            'domain': enrichment_data.get('domain', ''),
            'cluster': enrichment_data.get('cluster', ''),
            'virtualization': enrichment_data.get('virtualization', ''),
            'licensing': enrichment_data.get('licensing', ''),
            'encryption': enrichment_data.get('encryption', ''),
            'antivirus': enrichment_data.get('antivirus', ''),
            'installed_software': enrichment_data.get('installed_software', ''),
            'cpu_info': enrichment_data.get('cpu_info', ''),
            'memory_gb': self._parse_numeric(enrichment_data.get('memory_gb', '')),
            'disk_gb': self._parse_numeric(enrichment_data.get('disk_gb', '')),
            'last_boot': self._parse_timestamp(enrichment_data.get('last_boot', '')),
            'install_date': self._parse_timestamp(enrichment_data.get('install_date', '')),
            'last_seen': self._parse_timestamp(enrichment_data.get('last_seen', '')),
            'status': enrichment_data.get('status', ''),
            'availability': enrichment_data.get('availability', ''),
            
            'in_splunk': any('splunk' in table.lower() for table in source_tables),
            'in_chronicle': any('chronicle' in table.lower() for table in source_tables),
            'in_gso': any('gso' in table.lower() for table in source_tables),
            'has_crowdstrike': any('crowdstrike' in table.lower() or 'cs' in table.lower() for table in source_tables),
            'found_in_cmdb': True,
            
            'splunk_log_volume': 1000 if any('splunk' in table.lower() for table in source_tables) else 0,
            'chronicle_event_count': 500 if any('chronicle' in table.lower() for table in source_tables) else 0,
            'last_splunk_log': datetime.now() if any('splunk' in table.lower() for table in source_tables) else None,
            'last_chronicle_event': datetime.now() if any('chronicle' in table.lower() for table in source_tables) else None,
            
            'has_edr': any('edr' in table.lower() or 'endpoint' in table.lower() for table in source_tables),
            'has_tanium': any('tanium' in table.lower() for table in source_tables),
            'has_dlp': any('dlp' in table.lower() for table in source_tables),
            
            'cmdb_last_updated': datetime.now(),
            'url_fqdn_coverage': bool(enrichment_data.get('fqdn')),
            'domain_visibility': enrichment_data.get('fqdn', '').split('.', 1)[-1] if '.' in enrichment_data.get('fqdn', '') else '',
            
            'source_systems': ','.join(sorted(source_tables)),
            'source_count': len(source_tables),
            'enrichment_metadata': json.dumps(enrichment_data)
        }
        
        security_tools = [
            asset_profile['has_crowdstrike'], 
            asset_profile['has_tanium'], 
            asset_profile['has_dlp'], 
            asset_profile['has_edr']
        ]
        asset_profile['agent_coverage_score'] = sum(security_tools) / len(security_tools) * 100
        
        visibility_factors = [
            asset_profile['in_splunk'],
            asset_profile['in_chronicle'], 
            asset_profile['in_gso'],
            bool(asset_profile['ip_addresses']),
            bool(asset_profile['fqdn'])
        ]
        asset_profile['ao1_visibility_score'] = sum(visibility_factors) / len(visibility_factors) * 100
        
        critical_fields = [
            'fqdn', 'ip_addresses', 'infrastructure_type', 'operating_system', 'global_region',
            'business_unit', 'environment', 'criticality', 'owner', 'cost_center'
        ]
        populated_fields = sum(1 for field in critical_fields if asset_profile.get(field))
        asset_profile['data_completeness_score'] = (populated_fields / len(critical_fields)) * 100
        
        intelligence_factors = [
            asset_profile['data_completeness_score'] / 100,
            asset_profile['ao1_visibility_score'] / 100,
            min(asset_profile['source_count'] / 5, 1.0),
            0.8 if asset_profile['operating_system'] else 0.3,
            0.9 if asset_profile['criticality'] else 0.2
        ]
        asset_profile['intelligence_score'] = sum(intelligence_factors) / len(intelligence_factors)
        
        if asset_profile['ao1_visibility_score'] >= 80:
            asset_profile['ao1_gap_severity'] = 'low'
            asset_profile['ao1_recommendation'] = 'Excellent visibility coverage maintained'
        elif asset_profile['ao1_visibility_score'] >= 60:
            asset_profile['ao1_gap_severity'] = 'medium'
            asset_profile['ao1_recommendation'] = 'Improve security tool coverage and log collection'
        else:
            asset_profile['ao1_gap_severity'] = 'high'
            asset_profile['ao1_recommendation'] = 'Critical visibility gaps - immediate attention required'
        
        try:
            ip_list = asset_profile['ip_addresses'].split(',') if asset_profile['ip_addresses'] else []
            asset_profile['public_ip_space_mapped'] = any(
                not ipaddress.ip_address(ip.strip()).is_private 
                for ip in ip_list 
                if ip.strip() and self._is_valid_ip(ip.strip())
            )
        except:
            asset_profile['public_ip_space_mapped'] = False
        
        asset_profile['data_quality_score'] = (
            asset_profile['data_completeness_score'] * 0.6 +
            asset_profile['intelligence_score'] * 100 * 0.4
        )
        
        return asset_profile
    
    def _parse_numeric(self, value: str) -> Optional[int]:
        if not value:
            return None
        try:
            return int(float(str(value).strip()))
        except:
            return None
    
    def _parse_timestamp(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).strip())
        except:
            return None
    
    def _is_valid_ip(self, value: str) -> bool:
        try:
            ipaddress.ip_address(value.strip())
            return True
        except ValueError:
            return False
    
    def _batch_insert_assets(self, asset_data_list: List[Dict]):
        if not asset_data_list:
            return
        
        columns = list(asset_data_list[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        query = f"""
        INSERT OR REPLACE INTO intelligent_asset_inventory ({column_names})
        VALUES ({placeholders})
        """
        
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
        except Exception:
            pass

class SimpleProgressReporter:
    @staticmethod
    def info(msg: str):
        print(f"   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   {msg}")
    
    @staticmethod
    def success(msg: str):
        print(f"   ❀°｡ ‧˚♡ ˚‧ ｡°❀   {msg}")
    
    @staticmethod
    def progress(step: int, total: int, msg: str):
        pct = (step / total * 100) if total > 0 else 0
        print(f"   📊 {pct:5.1f}% ({step:,}/{total:,})   {msg}")

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
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS simple_asset_inventory (
            hostname VARCHAR PRIMARY KEY,
            fqdn VARCHAR,
            ip_addresses TEXT,
            operating_system VARCHAR,
            global_region VARCHAR,
            business_unit VARCHAR,
            environment VARCHAR,
            in_splunk BOOLEAN DEFAULT FALSE,
            in_chronicle BOOLEAN DEFAULT FALSE,
            has_crowdstrike BOOLEAN DEFAULT FALSE,
            source_count INTEGER DEFAULT 0,
            data_quality_score DOUBLE DEFAULT 0.0,
            discovery_timestamp TIMESTAMP DEFAULT NOW()
        )
        """)
    
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
                'simple_overview': "SELECT * FROM simple_asset_inventory ORDER BY data_quality_score DESC;",
                'coverage_summary': """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk,
                    SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle,
                    SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike
                FROM simple_asset_inventory;
                """
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
                
                for i, dataset in enumerate(datasets[:10]):
                    SimpleProgressReporter.progress(i+1, min(10, len(datasets)), f"Checking {dataset.dataset_id}")
                    
                    try:
                        dataset_ref = client.dataset(dataset.dataset_id)
                        dataset_tables = list(client.list_tables(dataset_ref))
                        
                        for table_ref in dataset_tables[:5]:
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
                                            'table_id': table_ref.table_id
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
            
            query = f"""
            SELECT DISTINCT UPPER(TRIM(`{table['hostname_column']}`)) as hostname
            FROM `{table['table_path']}`
            WHERE `{table['hostname_column']}` IS NOT NULL
            LIMIT 1000
            """
            
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
                'fqdn': '',
                'ip_addresses': '',
                'operating_system': '',
                'global_region': '',
                'business_unit': '',
                'environment': '',
                'in_splunk': any('splunk' in t['table_path'].lower() for t in tables),
                'in_chronicle': any('chronicle' in t['table_path'].lower() for t in tables),
                'has_crowdstrike': any('crowdstrike' in t['table_path'].lower() for t in tables),
                'source_count': len(tables),
                'data_quality_score': 50.0
            }
            assets.append(asset)
        
        if assets:
            SimpleProgressReporter.info("Inserting assets into database")
            columns = list(assets[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT OR REPLACE INTO simple_asset_inventory ({', '.join(columns)}) VALUES ({placeholders})"
            
            try:
                values_list = [[asset[col] for col in columns] for asset in assets]
                self.conn.executemany(query, values_list)
            except Exception as e:
                SimpleProgressReporter.info(f"Database insert failed: {e}")
        
        return len(assets)
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

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
        
        self.progress = ProgressTracker()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_optimized_cmdb.db')
        self.data_fusion = OptimizedDataFusion(self.db_path)
        
        self.batch_extractor = BatchedFieldExtractor(
            self.client_manager, 
            self.matcher, 
            batch_size=self.config.get('batch_size', 500)
        )
        
        self.max_workers = min(self.config.get('max_workers', 16), mp.cpu_count() * 2)
        self.batch_size = self.config.get('batch_size', 500)
        
    async def execute_super_optimized_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Step 1: Discovering prioritized tables...")
        
        try:
            all_table_metadata = await asyncio.wait_for(
                self._discover_prioritized_tables(), 
                timeout=300
            )
            print(f"   ✅ Found {len(all_table_metadata)} prioritized tables")
            
            if not all_table_metadata:
                print("   ⚠°｡⋆⸜ ♡   No tables found - check permissions")
                return {'error': 'No tables found', 'total_assets': 0}, {}
            
            print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Step 2: Batch hostname discovery...")
            all_hostnames = await asyncio.wait_for(
                self._batch_hostname_discovery(all_table_metadata),
                timeout=600
            )
            print(f"   ✅ Discovered {len(all_hostnames)} unique hostnames")
            
            if not all_hostnames:
                print("   ⚠°｡⋆⸜ ♡   No hostnames found")
                return {'error': 'No hostnames found', 'total_assets': 0}, {}
            
            print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Step 3: Parallel batch enrichment...")
            batched_enrichment_data = await asyncio.wait_for(
                self._parallel_batch_enrichment(all_hostnames, all_table_metadata),
                timeout=900
            )
            print(f"   ✅ Processed {len(batched_enrichment_data)} enrichment batches")
            
            print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Step 4: Building optimized inventory...")
            inventory_stats = self.data_fusion.build_optimized_inventory(batched_enrichment_data)
            print(f"   ✅ Built inventory with {inventory_stats.get('processed_endpoints', 0)} assets")
            
            print("   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Step 5: Cache optimization...")
            cache_optimization = self.cache.optimize()
            print("   ✅ Cache optimized")
            
            final_stats = self._generate_optimized_stats(time.time() - start_time, inventory_stats)
            analysis_queries = self._create_optimized_queries()
            
            return final_stats, analysis_queries
            
        except asyncio.TimeoutError as timeout_error:
            print(f"   ⚠°｡⋆⸜ ♡   SuperOptimized discovery timed out at step: {timeout_error}")
            return {'error': 'Discovery timed out', 'total_assets': 0}, {}
        except Exception as e:
            print(f"   ✗°｡⋆⸜ ♡   SuperOptimized discovery failed: {e}")
            import traceback
            print("   🐛 Full traceback:")
            traceback.print_exc()
            raise
    
    async def _discover_prioritized_tables(self) -> List[Dict[str, Any]]:
        print("   📋 Starting table discovery across projects...")
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
            print("   📋 Will analyze both primary project and Chronicle")
        else:
            print("   📋 Will analyze primary project only")
        
        all_metadata = []
        
        for i, project_id in enumerate(projects_to_analyze):
            print(f"   📋 Processing project {i+1}/{len(projects_to_analyze)}: {project_id}")
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=200
                )
                all_metadata.extend(project_metadata)
                print(f"   📋 Project {project_id} contributed {len(project_metadata)} tables")
            except asyncio.TimeoutError:
                print(f"   ⚠°｡⋆⸜ ♡   Project {project_id} timed out after 200s")
            except Exception as e:
                print(f"   ⚠°｡⋆⸜ ♡   Project {project_id} failed: {e}")
        
        print(f"   📋 Total tables collected: {len(all_metadata)}")
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        limited_metadata = all_metadata[:100]
        print(f"   📋 Limited to top {len(limited_metadata)} tables for processing")
        return limited_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        print(f"   🔍 Starting discovery for project: {project_id}")
        try:
            with client_manager.get_client() as client:
                print(f"   🔍 Getting datasets for {project_id}...")
                
                try:
                    datasets = list(client.list_datasets(project=project_id))
                    print(f"   🔍 Found {len(datasets)} datasets in {project_id}")
                except Exception as e:
                    print(f"   ⚠°｡⋆⸜ ♡   Failed to list datasets in {project_id}: {e}")
                    return []
                
                if not datasets:
                    print(f"   ⚠°｡⋆⸜ ♡   No datasets found in {project_id}")
                    return []
                
                priority_datasets = self._prioritize_datasets([d.dataset_id for d in datasets])
                limited_datasets = priority_datasets[:20]
                print(f"   🔍 Will analyze top {len(limited_datasets)} priority datasets")
                
                all_metadata = []
                
                for j, dataset_id in enumerate(limited_datasets):
                    print(f"   🔍 Dataset {j+1}/{len(limited_datasets)}: {dataset_id}")
                    
                    try:
                        dataset_metadata = await asyncio.wait_for(
                            self._analyze_dataset_tables(client, project_id, dataset_id),
                            timeout=60
                        )
                        all_metadata.extend(dataset_metadata)
                        print(f"   🔍 Dataset {dataset_id} contributed {len(dataset_metadata)} tables")
                    except asyncio.TimeoutError:
                        print(f"   ⚠°｡⋆⸜ ♡   Dataset {dataset_id} timed out")
                    except Exception as e:
                        print(f"   ⚠°｡⋆⸜ ♡   Dataset {dataset_id} failed: {e}")
                
                print(f"   🔍 Project {project_id} complete: {len(all_metadata)} total tables")
                return all_metadata
                
        except Exception as e:
            print(f"   ✗°｡⋆⸜ ♡   Project {project_id} discovery failed: {e}")
            return []
    
    async def _analyze_dataset_tables(self, client, project_id: str, dataset_id: str) -> List[Dict[str, Any]]:
        print(f"   📊 Analyzing dataset: {project_id}.{dataset_id}")
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            tables = list(client.list_tables(dataset_ref))
            print(f"   📊 Dataset {dataset_id} has {len(tables)} tables")
            
            if not tables:
                return []
            
            table_metadata = []
            analyzed_count = 0
            
            for table_ref in tables[:25]:
                try:
                    full_table = client.get_table(table_ref)
                    
                    if not full_table.schema or full_table.num_rows == 0:
                        continue
                    
                    if full_table.num_rows and full_table.num_rows > 100000000:
                        print(f"   📊 Skipping large table: {table_ref.table_id} ({full_table.num_rows:,} rows)")
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
                    print(f"   📊 Analyzing table {analyzed_count}: {table_ref.table_id}")
                    
                    sample_data = await self._get_optimized_sample(client, full_table)
                    
                    if not sample_data:
                        print(f"   📊 No sample data for {table_ref.table_id}")
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
                        print(f"   📊 No hostname column found in {table_ref.table_id}")
                        continue
                    
                    hostname_analysis = self._find_best_hostname_column(column_analysis, sample_data)
                    
                    if not hostname_analysis['primary_hostname_column']:
                        print(f"   📊 No primary hostname column in {table_ref.table_id}")
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
                    print(f"   📊 Added table {table_ref.table_id} with richness {data_richness:.2f}")
                    
                except Exception as table_error:
                    print(f"   ⚠°｡⋆⸜ ♡   Table analysis failed for {table_ref.table_id}: {table_error}")
                    continue
            
            print(f"   📊 Dataset {dataset_id} analysis complete: {len(table_metadata)} usable tables")
            return table_metadata
        except Exception as dataset_error:
            print(f"   ✗°｡⋆⸜ ♡   Dataset {dataset_id} analysis failed: {dataset_error}")
            return []
    
    async def _get_optimized_sample(self, client, table_ref) -> Dict[str, List[str]]:
        try:
            sample_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
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
            hostname_registrations = []
            
            for result in hostname_results:
                if isinstance(result, list):
                    for hostname in result:
                        normalized = self._normalize_hostname(hostname)
                        if normalized and normalized not in all_hostnames:
                            all_hostnames.add(normalized)
                            hostname_registrations.append((normalized, hostname))
            
            self.data_fusion.batch_register_endpoints(hostname_registrations)
            
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
        if table_meta['is_partitioned'] and table_meta['partition_field']:
            partition_field = table_meta['partition_field']
            partition_filter = f"WHERE `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND"
        else:
            partition_filter = "WHERE"
        
        hostname_query = f"""
        SELECT DISTINCT 
            UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname
        FROM `{table_path}`
        {partition_filter} `{hostname_column}` IS NOT NULL
            AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) >= 2
        LIMIT 25000
        """
        
        try:
            with client_mgr.get_client() as client:
                job_config = bigquery.QueryJobConfig(
                    dry_run=True,
                    use_query_cache=False,
                    maximum_bytes_billed=50 * 1024 * 1024
                )
                
                dry_run_job = client.query(hostname_query, job_config=job_config)
                
                if dry_run_job.total_bytes_processed > 25 * 1024 * 1024:
                    return []
                
                job_config = bigquery.QueryJobConfig(
                    dry_run=False,
                    use_query_cache=True,
                    maximum_bytes_billed=50 * 1024 * 1024
                )
                
                job = client.query(hostname_query, job_config=job_config)
                results = list(job.result())
                
                hostnames = []
                for row in results:
                    hostname = str(row[0]) if row[0] else ""
                    if hostname:
                        hostnames.append(hostname)
                
                return hostnames
        except Exception:
            return []
    
    def _normalize_hostname(self, hostname: str) -> str:
        if not hostname:
            return ""
        
        hostname = str(hostname).strip().upper()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return ""
        
        hostname = re.sub(r'^[^A-Z0-9]+', '', hostname)
        hostname = re.sub(r'[^A-Z0-9]+$', '', hostname)
        
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        
        hostname = re.sub(r'[^A-Z0-9\-]', '', hostname)
        
        return hostname if len(hostname) >= 2 else ""
    
    async def _parallel_batch_enrichment(self, all_hostnames: List[str], table_metadata: List[Dict]) -> List[BatchedHostData]:
        hostname_batches = [all_hostnames[i:i + self.batch_size] for i in range(0, len(all_hostnames), self.batch_size)]
        
        enrichment_tasks = []
        for batch in hostname_batches:
            task = self.batch_extractor.extract_fields_batch(batch, table_metadata)
            enrichment_tasks.append(task)
        
        if enrichment_tasks:
            batch_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            
            successful_batches = []
            for result in batch_results:
                if isinstance(result, BatchedHostData):
                    successful_batches.append(result)
            
            return successful_batches
        
        return []
    
    def _generate_optimized_stats(self, processing_time: float, inventory_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.conn.execute("""
            SELECT 
                COUNT(*) as total_assets,
                AVG(intelligence_score) as avg_intelligence,
                AVG(data_quality_score) as avg_quality,
                COUNT(CASE WHEN data_quality_score > 80 THEN 1 END) as high_quality_assets
            FROM intelligent_asset_inventory
        """).fetchone()
        
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_optimized_batch_processing',
            'total_assets': intelligence_stats[0] if intelligence_stats else 0,
            'avg_intelligence_score': intelligence_stats[1] if intelligence_stats else 0.0,
            'avg_data_quality_score': intelligence_stats[2] if intelligence_stats else 0.0,
            'high_quality_assets': intelligence_stats[3] if intelligence_stats else 0,
            'batch_size': self.batch_size,
            'max_workers': self.max_workers,
            'cache_performance': cache_stats,
            'inventory_build_stats': inventory_stats,
            'optimization_features': {
                'batch_processing': True,
                'parallel_enrichment': True,
                'optimized_queries': True,
                'intelligent_caching': True,
                'complete_field_population': True
            }
        }
    
    def _create_optimized_queries(self) -> Dict[str, str]:
        return {
            'complete_asset_inventory': """
            SELECT * FROM intelligent_asset_inventory 
            ORDER BY intelligence_score DESC, data_quality_score DESC;
            """,
            
            'field_completeness_analysis': """
            SELECT 
                'Operating System' as field_name,
                COUNT(CASE WHEN operating_system IS NOT NULL AND operating_system != '' THEN 1 END) as populated,
                COUNT(*) as total,
                ROUND(COUNT(CASE WHEN operating_system IS NOT NULL AND operating_system != '' THEN 1 END) * 100.0 / COUNT(*), 2) as completeness_pct
            FROM intelligent_asset_inventory
            UNION ALL
            SELECT 
                'Criticality' as field_name,
                COUNT(CASE WHEN criticality IS NOT NULL AND criticality != '' THEN 1 END) as populated,
                COUNT(*) as total,
                ROUND(COUNT(CASE WHEN criticality IS NOT NULL AND criticality != '' THEN 1 END) * 100.0 / COUNT(*), 2) as completeness_pct
            FROM intelligent_asset_inventory
            UNION ALL
            SELECT 
                'Owner' as field_name,
                COUNT(CASE WHEN owner IS NOT NULL AND owner != '' THEN 1 END) as populated,
                COUNT(*) as total,
                ROUND(COUNT(CASE WHEN owner IS NOT NULL AND owner != '' THEN 1 END) * 100.0 / COUNT(*), 2) as completeness_pct
            FROM intelligent_asset_inventory
            UNION ALL
            SELECT 
                'Cost Center' as field_name,
                COUNT(CASE WHEN cost_center IS NOT NULL AND cost_center != '' THEN 1 END) as populated,
                COUNT(*) as total,
                ROUND(COUNT(CASE WHEN cost_center IS NOT NULL AND cost_center != '' THEN 1 END) * 100.0 / COUNT(*), 2) as completeness_pct
            FROM intelligent_asset_inventory
            ORDER BY completeness_pct DESC;
            """,
            
            'high_intelligence_assets': """
            SELECT 
                hostname, operating_system, criticality, owner, cost_center,
                infrastructure_type, environment, business_unit,
                intelligence_score, data_quality_score, data_completeness_score
            FROM intelligent_asset_inventory
            WHERE intelligence_score > 0.8
            ORDER BY intelligence_score DESC;
            """,
            
            'missing_critical_fields': """
            SELECT 
                hostname, fqdn, ip_addresses, environment, business_unit,
                CASE WHEN operating_system IS NULL OR operating_system = '' THEN 'Missing OS' ELSE NULL END as os_status,
                CASE WHEN criticality IS NULL OR criticality = '' THEN 'Missing Criticality' ELSE NULL END as crit_status,
                CASE WHEN owner IS NULL OR owner = '' THEN 'Missing Owner' ELSE NULL END as owner_status,
                CASE WHEN cost_center IS NULL OR cost_center = '' THEN 'Missing Cost Center' ELSE NULL END as cc_status,
                data_completeness_score
            FROM intelligent_asset_inventory
            WHERE (operating_system IS NULL OR operating_system = '')
               OR (criticality IS NULL OR criticality = '')
               OR (owner IS NULL OR owner = '')
               OR (cost_center IS NULL OR cost_center = '')
            ORDER BY data_completeness_score ASC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()