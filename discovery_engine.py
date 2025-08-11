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
import ipaddress
from typing import Dict, List, Any, Tuple, Set, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path

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

class ComprehensiveFieldExtractor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_comprehensive_tables()
        self._lock = threading.RLock()
        self.field_mappings = self._build_field_mappings()
        
    def _setup_comprehensive_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS comprehensive_asset_data (
            asset_id VARCHAR PRIMARY KEY,
            hostname VARCHAR,
            fqdn VARCHAR,
            ip_addresses TEXT,
            infrastructure_type VARCHAR,
            global_region VARCHAR,
            country VARCHAR,
            data_center VARCHAR,
            cloud_region VARCHAR,
            business_unit VARCHAR,
            cio VARCHAR,
            apm VARCHAR,
            application_class VARCHAR,
            environment VARCHAR,
            in_splunk BOOLEAN DEFAULT FALSE,
            in_chronicle BOOLEAN DEFAULT FALSE,
            in_gso BOOLEAN DEFAULT FALSE,
            splunk_log_volume INTEGER DEFAULT 0,
            chronicle_event_count INTEGER DEFAULT 0,
            last_splunk_log TIMESTAMP,
            last_chronicle_event TIMESTAMP,
            has_edr BOOLEAN DEFAULT FALSE,
            has_tanium BOOLEAN DEFAULT FALSE,
            has_dlp BOOLEAN DEFAULT FALSE,
            has_crowdstrike BOOLEAN DEFAULT FALSE,
            agent_coverage_score DOUBLE DEFAULT 0.0,
            cmdb_last_updated TIMESTAMP,
            data_quality_score DOUBLE DEFAULT 0.0,
            url_fqdn_coverage DOUBLE DEFAULT 0.0,
            public_ip_space_mapped BOOLEAN DEFAULT FALSE,
            domain_visibility DOUBLE DEFAULT 0.0,
            ao1_visibility_score DOUBLE DEFAULT 0.0,
            ao1_gap_severity VARCHAR,
            ao1_recommendation TEXT,
            source_tables TEXT,
            total_data_points INTEGER DEFAULT 0,
            enrichment_timestamp TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS field_extraction_log (
            extraction_id VARCHAR PRIMARY KEY,
            hostname VARCHAR,
            source_table VARCHAR,
            source_column VARCHAR,
            extracted_field VARCHAR,
            extracted_value TEXT,
            confidence_score DOUBLE,
            extraction_method VARCHAR,
            extraction_timestamp TIMESTAMP DEFAULT NOW()
        )
        """)

    def _build_field_mappings(self) -> Dict[str, Dict]:
        return {
            'fqdn': {
                'patterns': [r'fqdn', r'domain', r'dns', r'qualified', r'canonical'],
                'validators': ['_validate_fqdn'],
                'priority': 100
            },
            'ip_addresses': {
                'patterns': [r'ip', r'addr', r'address', r'inet', r'host_ip'],
                'validators': ['_validate_ip'],
                'priority': 95
            },
            'infrastructure_type': {
                'patterns': [r'infra', r'type', r'category', r'class', r'platform', r'kind'],
                'validators': ['_validate_infrastructure'],
                'priority': 90
            },
            'global_region': {
                'patterns': [r'region', r'geo', r'location', r'site', r'area', r'zone'],
                'validators': ['_validate_region'],
                'priority': 85
            },
            'country': {
                'patterns': [r'country', r'nation', r'territory'],
                'validators': ['_validate_country'],
                'priority': 80
            },
            'data_center': {
                'patterns': [r'datacenter', r'data_center', r'dc', r'facility', r'center'],
                'validators': ['_validate_datacenter'],
                'priority': 75
            },
            'cloud_region': {
                'patterns': [r'cloud', r'aws', r'azure', r'gcp', r'region'],
                'validators': ['_validate_cloud_region'],
                'priority': 70
            },
            'business_unit': {
                'patterns': [r'business', r'unit', r'bu', r'org', r'department', r'division'],
                'validators': ['_validate_business_unit'],
                'priority': 65
            },
            'cio': {
                'patterns': [r'cio', r'owner', r'responsible', r'manager'],
                'validators': ['_validate_text'],
                'priority': 60
            },
            'apm': {
                'patterns': [r'apm', r'monitoring', r'performance', r'application'],
                'validators': ['_validate_text'],
                'priority': 55
            },
            'application_class': {
                'patterns': [r'app', r'application', r'class', r'category', r'type'],
                'validators': ['_validate_text'],
                'priority': 50
            },
            'environment': {
                'patterns': [r'env', r'environment', r'stage', r'tier', r'level'],
                'validators': ['_validate_environment'],
                'priority': 45
            }
        }

    def extract_comprehensive_data(self, all_table_metadata: List[Dict]) -> Dict[str, Any]:
        PrettyLogger.info("Starting comprehensive field extraction from ALL columns")
        
        hostname_to_data = defaultdict(lambda: {
            'hostname': '',
            'fqdn': set(),
            'ip_addresses': set(),
            'infrastructure_type': set(),
            'global_region': set(),
            'country': set(),
            'data_center': set(),
            'cloud_region': set(),
            'business_unit': set(),
            'cio': set(),
            'apm': set(),
            'application_class': set(),
            'environment': set(),
            'source_tables': set(),
            'data_points': 0,
            'extraction_logs': []
        })
        
        stats = {
            'tables_processed': 0,
            'columns_processed': 0,
            'extractions_made': 0,
            'hostnames_enriched': 0
        }
        
        for table_meta in all_table_metadata:
            if self._process_table_comprehensively(table_meta, hostname_to_data, stats):
                stats['tables_processed'] += 1
        
        self._build_comprehensive_assets(hostname_to_data, stats)
        
        PrettyLogger.success(f"Comprehensive extraction complete: {stats}")
        return stats

    def _process_table_comprehensively(self, table_meta: Dict, hostname_to_data: Dict, stats: Dict) -> bool:
        hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
        if not hostname_column:
            return False
        
        sample_data = table_meta.get('sample_data', {})
        hostname_samples = sample_data.get(hostname_column, [])
        
        if not hostname_samples:
            return False
        
        table_path = table_meta['full_table_path']
        PrettyLogger.info(f"Processing table: {table_path}")
        
        for column_name in table_meta.get('all_columns', []):
            stats['columns_processed'] += 1
            
            if column_name == hostname_column:
                continue
            
            column_values = sample_data.get(column_name, [])
            if not column_values:
                continue
            
            field_type = self._determine_field_type(column_name, column_values)
            if not field_type:
                continue
            
            for i, hostname in enumerate(hostname_samples):
                if i >= len(column_values):
                    break
                
                value = column_values[i]
                if not self._is_valid_value(value):
                    continue
                
                normalized_hostname = self._normalize_hostname(hostname)
                if not normalized_hostname:
                    continue
                
                confidence = self._calculate_extraction_confidence(field_type, value, column_name)
                
                if self._extract_field_value(normalized_hostname, field_type, value, hostname_to_data, 
                                           table_path, column_name, confidence):
                    stats['extractions_made'] += 1
        
        return True

    def _determine_field_type(self, column_name: str, values: List[str]) -> Optional[str]:
        column_lower = column_name.lower()
        
        for field_type, mapping in self.field_mappings.items():
            for pattern in mapping['patterns']:
                if re.search(pattern, column_lower):
                    if self._validate_field_values(field_type, values):
                        return field_type
        
        return None

    def _validate_field_values(self, field_type: str, values: List[str]) -> bool:
        if not values:
            return False
        
        sample_values = [str(v).strip() for v in values[:3] if v]
        if not sample_values:
            return False
        
        if field_type == 'fqdn':
            return any('.' in v and not self._is_ip_address(v) for v in sample_values)
        elif field_type == 'ip_addresses':
            return any(self._is_ip_address(v) for v in sample_values)
        elif field_type == 'infrastructure_type':
            infra_keywords = ['physical', 'virtual', 'cloud', 'container', 'vm', 'bare', 'metal']
            return any(any(keyword in v.lower() for keyword in infra_keywords) for v in sample_values)
        elif field_type == 'environment':
            env_keywords = ['prod', 'dev', 'test', 'stage', 'qa', 'uat']
            return any(any(keyword in v.lower() for keyword in env_keywords) for v in sample_values)
        elif field_type == 'country':
            return any(len(v) == 2 and v.isupper() or v.upper() in ['USA', 'CANADA', 'UK'] for v in sample_values)
        elif field_type == 'cloud_region':
            cloud_keywords = ['us-east', 'us-west', 'eu-', 'ap-', 'aws', 'azure', 'gcp']
            return any(any(keyword in v.lower() for keyword in cloud_keywords) for v in sample_values)
        
        return True

    def _extract_field_value(self, hostname: str, field_type: str, value: str, hostname_to_data: Dict,
                           table_path: str, column_name: str, confidence: float) -> bool:
        if hostname not in hostname_to_data:
            hostname_to_data[hostname]['hostname'] = hostname
        
        data = hostname_to_data[hostname]
        processed_value = self._process_value_for_field(field_type, value)
        
        if not processed_value:
            return False
        
        if field_type in data:
            data[field_type].add(processed_value)
        
        data['source_tables'].add(table_path)
        data['data_points'] += 1
        
        extraction_log = {
            'table': table_path,
            'column': column_name,
            'field': field_type,
            'value': processed_value,
            'confidence': confidence
        }
        data['extraction_logs'].append(extraction_log)
        
        self._log_extraction(hostname, table_path, column_name, field_type, processed_value, confidence)
        
        return True

    def _process_value_for_field(self, field_type: str, value: str) -> Optional[str]:
        if not value or not isinstance(value, str):
            return None
        
        cleaned_value = str(value).strip()
        
        if field_type == 'fqdn':
            if '.' in cleaned_value and not self._is_ip_address(cleaned_value):
                return cleaned_value.lower()
        elif field_type == 'ip_addresses':
            if self._is_ip_address(cleaned_value):
                return cleaned_value
        elif field_type == 'infrastructure_type':
            infra_mapping = {
                'vm': 'virtual',
                'container': 'container',
                'physical': 'physical',
                'cloud': 'cloud',
                'bare': 'physical',
                'metal': 'physical'
            }
            for key, mapped_value in infra_mapping.items():
                if key in cleaned_value.lower():
                    return mapped_value
            return cleaned_value
        elif field_type == 'environment':
            env_mapping = {
                'prod': 'production',
                'dev': 'development', 
                'test': 'test',
                'stage': 'staging',
                'qa': 'qa',
                'uat': 'uat'
            }
            for key, mapped_value in env_mapping.items():
                if key in cleaned_value.lower():
                    return mapped_value
            return cleaned_value
        elif field_type == 'cloud_region':
            if any(cloud in cleaned_value.lower() for cloud in ['aws', 'azure', 'gcp', 'us-', 'eu-', 'ap-']):
                return cleaned_value
        
        return cleaned_value if len(cleaned_value) > 0 else None

    def _build_comprehensive_assets(self, hostname_to_data: Dict, stats: Dict):
        PrettyLogger.info("Building comprehensive asset profiles")
        
        for hostname, data in hostname_to_data.items():
            asset_profile = self._create_asset_profile(hostname, data)
            self._insert_comprehensive_asset(asset_profile)
            stats['hostnames_enriched'] += 1
        
        self._calculate_visibility_metrics()

    def _create_asset_profile(self, hostname: str, data: Dict) -> Dict:
        profile = {
            'asset_id': f"asset_{hashlib.md5(hostname.encode()).hexdigest()[:16]}",
            'hostname': hostname,
            'fqdn': self._get_best_value(data.get('fqdn', set())),
            'ip_addresses': ','.join(sorted(data.get('ip_addresses', set()))),
            'infrastructure_type': self._get_best_value(data.get('infrastructure_type', set())),
            'global_region': self._get_best_value(data.get('global_region', set())),
            'country': self._get_best_value(data.get('country', set())),
            'data_center': self._get_best_value(data.get('data_center', set())),
            'cloud_region': self._get_best_value(data.get('cloud_region', set())),
            'business_unit': self._get_best_value(data.get('business_unit', set())),
            'cio': self._get_best_value(data.get('cio', set())),
            'apm': self._get_best_value(data.get('apm', set())),
            'application_class': self._get_best_value(data.get('application_class', set())),
            'environment': self._get_best_value(data.get('environment', set())),
            'source_tables': ','.join(sorted(data.get('source_tables', set()))),
            'total_data_points': data.get('data_points', 0)
        }
        
        profile.update(self._determine_platform_presence(data.get('source_tables', set())))
        profile.update(self._calculate_coverage_scores(profile, data))
        
        return profile

    def _get_best_value(self, value_set: Set[str]) -> str:
        if not value_set:
            return ''
        
        values_list = list(value_set)
        if len(values_list) == 1:
            return values_list[0]
        
        return sorted(values_list, key=len, reverse=True)[0]

    def _determine_platform_presence(self, source_tables: Set[str]) -> Dict[str, bool]:
        presence = {
            'in_splunk': False,
            'in_chronicle': False,
            'in_gso': False,
            'has_edr': False,
            'has_tanium': False,
            'has_dlp': False,
            'has_crowdstrike': False
        }
        
        for table in source_tables:
            table_lower = table.lower()
            
            if any(keyword in table_lower for keyword in ['splunk', 'spl', 'log']):
                presence['in_splunk'] = True
            if any(keyword in table_lower for keyword in ['chronicle', 'security']):
                presence['in_chronicle'] = True
            if any(keyword in table_lower for keyword in ['gso', 'operations']):
                presence['in_gso'] = True
            if any(keyword in table_lower for keyword in ['edr', 'endpoint']):
                presence['has_edr'] = True
            if any(keyword in table_lower for keyword in ['tanium', 'tan']):
                presence['has_tanium'] = True
            if any(keyword in table_lower for keyword in ['dlp', 'data_loss']):
                presence['has_dlp'] = True
            if any(keyword in table_lower for keyword in ['crowdstrike', 'cs', 'falcon']):
                presence['has_crowdstrike'] = True
        
        return presence

    def _calculate_coverage_scores(self, profile: Dict, data: Dict) -> Dict[str, Any]:
        scores = {}
        
        populated_fields = sum(1 for key, value in profile.items() 
                             if key not in ['asset_id', 'hostname', 'source_tables', 'total_data_points'] 
                             and value and str(value).strip())
        
        total_fields = 13
        scores['data_quality_score'] = (populated_fields / total_fields) * 100
        
        platform_count = sum(1 for key, value in profile.items() 
                            if key.startswith(('in_', 'has_')) and value)
        scores['agent_coverage_score'] = (platform_count / 7) * 100
        
        if profile.get('fqdn'):
            scores['url_fqdn_coverage'] = 100.0
        else:
            scores['url_fqdn_coverage'] = 0.0
        
        if profile.get('ip_addresses'):
            ip_list = profile['ip_addresses'].split(',')
            public_ips = [ip for ip in ip_list if self._is_public_ip(ip.strip())]
            scores['public_ip_space_mapped'] = len(public_ips) > 0
        else:
            scores['public_ip_space_mapped'] = False
        
        if profile.get('fqdn'):
            scores['domain_visibility'] = 100.0
        else:
            scores['domain_visibility'] = 0.0
        
        visibility_factors = [
            scores['data_quality_score'],
            scores['agent_coverage_score'],
            scores['url_fqdn_coverage'],
            scores['domain_visibility']
        ]
        scores['ao1_visibility_score'] = sum(visibility_factors) / len(visibility_factors)
        
        if scores['ao1_visibility_score'] >= 80:
            scores['ao1_gap_severity'] = 'Low'
            scores['ao1_recommendation'] = 'Excellent visibility coverage'
        elif scores['ao1_visibility_score'] >= 60:
            scores['ao1_gap_severity'] = 'Medium'
            scores['ao1_recommendation'] = 'Good coverage with minor gaps'
        elif scores['ao1_visibility_score'] >= 40:
            scores['ao1_gap_severity'] = 'High'
            scores['ao1_recommendation'] = 'Significant visibility gaps need attention'
        else:
            scores['ao1_gap_severity'] = 'Critical'
            scores['ao1_recommendation'] = 'Critical visibility gaps require immediate action'
        
        return scores

    def _calculate_visibility_metrics(self):
        PrettyLogger.info("Calculating visibility metrics from logs")
        
        splunk_metrics = self.conn.execute("""
        SELECT hostname, COUNT(*) as log_count, MAX(extraction_timestamp) as last_log
        FROM field_extraction_log 
        WHERE source_table LIKE '%splunk%' OR source_table LIKE '%spl%'
        GROUP BY hostname
        """).fetchall()
        
        for hostname, count, last_log in splunk_metrics:
            self.conn.execute("""
            UPDATE comprehensive_asset_data 
            SET splunk_log_volume = ?, last_splunk_log = ?
            WHERE hostname = ?
            """, (count, last_log, hostname))
        
        chronicle_metrics = self.conn.execute("""
        SELECT hostname, COUNT(*) as event_count, MAX(extraction_timestamp) as last_event
        FROM field_extraction_log 
        WHERE source_table LIKE '%chronicle%' OR source_table LIKE '%security%'
        GROUP BY hostname
        """).fetchall()
        
        for hostname, count, last_event in chronicle_metrics:
            self.conn.execute("""
            UPDATE comprehensive_asset_data 
            SET chronicle_event_count = ?, last_chronicle_event = ?
            WHERE hostname = ?
            """, (count, last_event, hostname))

    def _normalize_hostname(self, hostname: str) -> Optional[str]:
        if not hostname or not isinstance(hostname, str):
            return None
        
        normalized = hostname.strip().upper()
        
        if len(normalized) < 2 or len(normalized) > 253:
            return None
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, normalized):
                return None
        
        normalized = re.sub(r'^[^A-Z0-9]+', '', normalized)
        normalized = re.sub(r'[^A-Z0-9\-\.]+$', '', normalized)
        
        if '.' in normalized:
            parts = normalized.split('.')
            if len(parts) > 1 and all(part.isdigit() for part in parts):
                return None
            normalized = parts[0]
        
        if len(normalized) < 2:
            return None
        
        return normalized

    def _is_valid_value(self, value: Any) -> bool:
        if value is None:
            return False
        
        str_value = str(value).strip()
        if not str_value:
            return False
        
        invalid_values = ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY', 'NAN', 'UNDEFINED', '0', '-']
        return str_value.upper() not in invalid_values

    def _is_ip_address(self, value: str) -> bool:
        try:
            ipaddress.ip_address(value.strip())
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False

    def _is_public_ip(self, ip_str: str) -> bool:
        try:
            ip = ipaddress.ip_address(ip_str)
            return not ip.is_private
        except (ValueError, ipaddress.AddressValueError):
            return False

    def _calculate_extraction_confidence(self, field_type: str, value: str, column_name: str) -> float:
        base_confidence = 0.5
        
        if field_type == 'ip_addresses' and self._is_ip_address(value):
            base_confidence = 0.95
        elif field_type == 'fqdn' and '.' in value:
            base_confidence = 0.9
        elif field_type in ['environment', 'infrastructure_type']:
            base_confidence = 0.8
        
        column_lower = column_name.lower()
        field_keywords = field_type.split('_')
        if any(keyword in column_lower for keyword in field_keywords):
            base_confidence += 0.1
        
        return min(0.99, base_confidence)

    def _log_extraction(self, hostname: str, table_path: str, column_name: str, 
                       field_type: str, value: str, confidence: float):
        extraction_id = hashlib.md5(
            f"{hostname}_{table_path}_{column_name}_{field_type}_{value}".encode()
        ).hexdigest()
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO field_extraction_log 
            (extraction_id, hostname, source_table, source_column, extracted_field, 
             extracted_value, confidence_score, extraction_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (extraction_id, hostname, table_path, column_name, field_type, 
                  value, confidence, 'comprehensive_extraction'))

    def _insert_comprehensive_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO comprehensive_asset_data ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)

    def get_extraction_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM comprehensive_asset_data
            """).fetchone()[0]
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM comprehensive_asset_data
            """).fetchone()[0] or 0.0
            
            stats['avg_ao1_visibility'] = self.conn.execute("""
                SELECT AVG(ao1_visibility_score) FROM comprehensive_asset_data
            """).fetchone()[0] or 0.0
            
            field_completeness = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN fqdn != '' THEN 1 ELSE 0 END) as fqdn_count,
                    SUM(CASE WHEN ip_addresses != '' THEN 1 ELSE 0 END) as ip_count,
                    SUM(CASE WHEN infrastructure_type != '' THEN 1 ELSE 0 END) as infra_count,
                    SUM(CASE WHEN global_region != '' THEN 1 ELSE 0 END) as region_count,
                    SUM(CASE WHEN business_unit != '' THEN 1 ELSE 0 END) as bu_count,
                    SUM(CASE WHEN environment != '' THEN 1 ELSE 0 END) as env_count
                FROM comprehensive_asset_data
            """).fetchone()
            
            if field_completeness:
                stats['field_completeness'] = {
                    'fqdn_populated': field_completeness[0],
                    'ip_addresses_populated': field_completeness[1],
                    'infrastructure_type_populated': field_completeness[2],
                    'global_region_populated': field_completeness[3],
                    'business_unit_populated': field_completeness[4],
                    'environment_populated': field_completeness[5]
                }
            
            platform_coverage = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                    SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                    SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_coverage,
                    SUM(CASE WHEN has_tanium THEN 1 ELSE 0 END) as tanium_coverage
                FROM comprehensive_asset_data
            """).fetchone()
            
            if platform_coverage:
                stats['platform_coverage'] = {
                    'splunk_coverage': platform_coverage[0],
                    'chronicle_coverage': platform_coverage[1],
                    'crowdstrike_coverage': platform_coverage[2],
                    'tanium_coverage': platform_coverage[3]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate extraction stats: {e}")
            return {'error': str(e)}

    def close(self):
        if self.conn:
            self.conn.close()

class ComprehensiveAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Comprehensive AO1 Field Discovery   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
        print("="*90)
        
        self.client_manager = BigQueryClientManager(project_id)
        
        if not self.client_manager.test_connection():
            raise ConnectionError("Failed to authenticate with BigQuery")
        
        self.matcher = IntelligentContentMatcher()
        self.cache = IntelligentCacheManager(
            cache_dir=self.config.get('cache_dir', '.cache'),
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.db_path = self.config.get('database_path', 'ao1_comprehensive_cmdb.db')
        self.field_extractor = ComprehensiveFieldExtractor(self.db_path)
        
        self._lock = threading.RLock()

    async def execute_comprehensive_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting comprehensive field discovery")
        
        try:
            all_table_metadata = await self._discover_all_tables()
            
            extraction_stats = self.field_extractor.extract_comprehensive_data(all_table_metadata)
            
            final_stats = self._generate_comprehensive_stats(time.time() - start_time, extraction_stats)
            analysis_queries = self._create_comprehensive_queries()
            
            PrettyLogger.success("Comprehensive field discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Comprehensive discovery failed: {e}")
            raise
        finally:
            self.field_extractor.close()

    async def _discover_all_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering all tables for comprehensive field extraction")
        
        all_metadata = []
        
        try:
            with self.client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=self.project_id))
                
                for dataset in datasets[:20]:
                    try:
                        dataset_ref = client.dataset(dataset.dataset_id, project=self.project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        for table_ref in tables[:10]:
                            try:
                                metadata = await self._analyze_table_for_fields(client, table_ref)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Table discovery failed: {e}")
            return []
        
        PrettyLogger.success(f"Discovered {len(all_metadata)} tables for field extraction")
        return all_metadata

    async def _analyze_table_for_fields(self, client, table_ref) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_column = self._find_hostname_column(all_columns)
            if not hostname_column:
                return None
            
            sample_data = await self._get_comprehensive_sample(client, full_table)
            
            if not sample_data or hostname_column not in sample_data:
                return None
            
            table_metadata = {
                'project_id': self.project_id,
                'dataset_id': table_ref.dataset_id,
                'table_id': table_ref.table_id,
                'full_table_path': f"{self.project_id}.{table_ref.dataset_id}.{table_ref.table_id}",
                'all_columns': all_columns,
                'hostname_analysis': {'primary_hostname_column': hostname_column},
                'sample_data': sample_data
            }
            
            return table_metadata
            
        except Exception:
            return None

    def _find_hostname_column(self, columns: List[str]) -> Optional[str]:
        hostname_indicators = ['host', 'endpoint', 'computer', 'device', 'server', 'machine', 'asset', 'node']
        
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    return column
        
        return None

    async def _get_comprehensive_sample(self, client, table_ref) -> Dict[str, List[str]]:
        try:
            sample_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            LIMIT 100
            """
            
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
                        str_value = str(value).strip()
                        if len(str_value) > 0:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}

    def _generate_comprehensive_stats(self, processing_time: float, extraction_stats: Dict) -> Dict[str, Any]:
        field_stats = self.field_extractor.get_extraction_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'comprehensive_field_extraction',
            'extraction_stats': extraction_stats,
            'field_statistics': field_stats,
            'target_fields_populated': {
                'fqdn': field_stats.get('field_completeness', {}).get('fqdn_populated', 0),
                'ip_addresses': field_stats.get('field_completeness', {}).get('ip_addresses_populated', 0),
                'infrastructure_type': field_stats.get('field_completeness', {}).get('infrastructure_type_populated', 0),
                'global_region': field_stats.get('field_completeness', {}).get('global_region_populated', 0),
                'business_unit': field_stats.get('field_completeness', {}).get('business_unit_populated', 0),
                'environment': field_stats.get('field_completeness', {}).get('environment_populated', 0)
            }
        }

    def _create_comprehensive_queries(self) -> Dict[str, str]:
        return {
            'comprehensive_asset_overview': """
            SELECT 
                hostname, fqdn, ip_addresses, infrastructure_type, global_region,
                country, data_center, cloud_region, business_unit, environment,
                in_splunk, in_chronicle, has_crowdstrike, has_tanium,
                data_quality_score, ao1_visibility_score, ao1_gap_severity,
                total_data_points, source_tables
            FROM comprehensive_asset_data 
            ORDER BY ao1_visibility_score DESC, data_quality_score DESC;
            """,
            
            'field_population_analysis': """
            SELECT 
                'FQDN' as field_name,
                SUM(CASE WHEN fqdn != '' THEN 1 ELSE 0 END) as populated_count,
                COUNT(*) as total_count,
                ROUND(100.0 * SUM(CASE WHEN fqdn != '' THEN 1 ELSE 0 END) / COUNT(*), 2) as population_percentage
            FROM comprehensive_asset_data
            UNION ALL
            SELECT 
                'IP_Addresses' as field_name,
                SUM(CASE WHEN ip_addresses != '' THEN 1 ELSE 0 END) as populated_count,
                COUNT(*) as total_count,
                ROUND(100.0 * SUM(CASE WHEN ip_addresses != '' THEN 1 ELSE 0 END) / COUNT(*), 2) as population_percentage
            FROM comprehensive_asset_data
            UNION ALL
            SELECT 
                'Infrastructure_Type' as field_name,
                SUM(CASE WHEN infrastructure_type != '' THEN 1 ELSE 0 END) as populated_count,
                COUNT(*) as total_count,
                ROUND(100.0 * SUM(CASE WHEN infrastructure_type != '' THEN 1 ELSE 0 END) / COUNT(*), 2) as population_percentage
            FROM comprehensive_asset_data
            ORDER BY population_percentage DESC;
            """,
            
            'visibility_gap_analysis': """
            SELECT 
                ao1_gap_severity,
                COUNT(*) as asset_count,
                AVG(ao1_visibility_score) as avg_visibility_score,
                AVG(data_quality_score) as avg_data_quality,
                STRING_AGG(DISTINCT ao1_recommendation, '; ') as recommendations
            FROM comprehensive_asset_data
            GROUP BY ao1_gap_severity
            ORDER BY 
                CASE ao1_gap_severity 
                    WHEN 'Critical' THEN 1 
                    WHEN 'High' THEN 2 
                    WHEN 'Medium' THEN 3 
                    ELSE 4 
                END;
            """,
            
            'platform_coverage_summary': """
            SELECT 
                business_unit,
                environment,
                COUNT(*) as total_assets,
                SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN has_tanium THEN 1 ELSE 0 END) as tanium_coverage,
                AVG(agent_coverage_score) as avg_agent_coverage
            FROM comprehensive_asset_data
            WHERE business_unit != '' AND environment != ''
            GROUP BY business_unit, environment
            ORDER BY total_assets DESC;
            """
        }

    def close(self):
        if hasattr(self.field_extractor, 'close'):
            self.field_extractor.close()