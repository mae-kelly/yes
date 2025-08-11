#!/usr/bin/env python3

import os
import asyncio
import logging
import duckdb
import time
import threading
from typing import Dict, List, Any, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dataclasses import asdict
import json
import random
import re
from collections import defaultdict, Counter

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
    
    @staticmethod
    def discovery(source: str, endpoints: int, enrichments: int):
        print(f"   ♡₊˚ 🌸 ⋆｡˚   {source}: {endpoints:,} endpoints, {enrichments:,} enrichments")

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
    
    @staticmethod
    def generate_hostname_variants(hostname: str) -> Set[str]:
        variants = set()
        base = IntelligentHostnameNormalizer.normalize_aggressively(hostname)
        
        if not base:
            return variants
        
        variants.add(base)
        
        if '-' in base:
            variants.add(base.replace('-', ''))
        
        if len(base) > 10:
            variants.add(base[:10])
            variants.add(base[:8])
        
        common_suffixes = ['01', '02', '03', '1', '2', '3', 'A', 'B', 'C']
        for suffix in common_suffixes:
            if base.endswith(suffix):
                variants.add(base[:-len(suffix)])
        
        return {v for v in variants if len(v) >= 2}

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
                datasets = list(client.list_datasets(project=project_id))
                
                priority_datasets = self._prioritize_datasets([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        for table_ref in tables:
                            metadata = await self._analyze_table_intelligence(client, table_ref, project_id)
                            if metadata:
                                all_metadata.append(metadata)
                                
                    except Exception as e:
                        PrettyLogger.warning(f"Dataset {dataset_id} analysis failed: {e}")
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=6)
        PrettyLogger.success(f"Discovered {len(all_metadata)} intelligent table structures")
        
        return all_metadata
    
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
    
    async def _analyze_table_intelligence(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            sample_data = await self._get_intelligent_sample(client, full_table)
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                analysis = self.matcher.analyze_column_intelligently(column, samples)
                if analysis:
                    column_analysis[column] = analysis
            
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
                sample_query += f" WHERE `{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
            
            sample_query += " LIMIT 20"
            
            job = client.query(sample_query)
            results = list(job.result())
            
            sample_data = defaultdict(list)
            for row in results:
                for i, value in enumerate(row):
                    if i < len(table_ref.schema) and value is not None:
                        column_name = table_ref.schema[i].name
                        sample_data[column_name].append(str(value))
            
            return dict(sample_data)
            
        except Exception:
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
            environment VARCHAR,
            cost_center VARCHAR,
            owner VARCHAR,
            criticality VARCHAR,
            
            in_splunk BOOLEAN DEFAULT FALSE,
            in_chronicle BOOLEAN DEFAULT FALSE,
            has_crowdstrike BOOLEAN DEFAULT FALSE,
            found_in_cmdb BOOLEAN DEFAULT FALSE,
            
            source_systems TEXT,
            source_count INTEGER DEFAULT 0,
            data_completeness_score DOUBLE DEFAULT 0.0,
            data_quality_score DOUBLE DEFAULT 0.0,
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
        
        variants = self.hostname_normalizer.generate_hostname_variants(hostname)
        
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
                    orig_variants.update(variants)
                    
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
                    """, (primary_hostname, original_hostname or hostname, ",".join(variants), 1.0))
                
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
    
    def build_intelligent_inventory(self) -> Dict[str, int]:
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
                    asset_data = self._build_intelligent_asset_profile(primary_hostname)
                    
                    if asset_data:
                        self._insert_intelligent_inventory(primary_hostname, asset_data)
                        stats['processed_endpoints'] += 1
                        
                        if asset_data.get('data_quality_score', 0) > 0.8:
                            stats['high_quality_assets'] += 1
                        
                        if asset_data.get('source_count', 0) > 2:
                            stats['enriched_assets'] += 1
                
                total_data_points = self.conn.execute("""
                    SELECT COUNT(*) FROM intelligent_endpoint_data
                """).fetchone()[0]
                stats['total_data_points'] = total_data_points
                
                return stats
                
            except Exception as e:
                PrettyLogger.error(f"Inventory building failed: {e}")
                return {'error': str(e)}
    
    def _build_intelligent_asset_profile(self, primary_hostname: str) -> Dict[str, Any]:
        try:
            data_query = """
            SELECT field_name, field_value, data_source, table_source,
                   confidence_score, validation_score, semantic_score
            FROM intelligent_endpoint_data 
            WHERE primary_hostname = ?
            ORDER BY confidence_score DESC, validation_score DESC, last_updated DESC
            """
            
            results = self.conn.execute(data_query, (primary_hostname,)).fetchall()
            
            if not results:
                return {}
            
            best_data = {}
            source_systems = set()
            confidence_scores = []
            
            field_data = defaultdict(list)
            for field_name, field_value, data_source, table_source, conf, val_score, sem_score in results:
                field_data[field_name].append({
                    'value': field_value,
                    'source': data_source,
                    'table': table_source,
                    'confidence': conf,
                    'validation': val_score,
                    'semantic': sem_score,
                    'combined_score': (conf * 0.5) + (val_score * 0.3) + (sem_score * 0.2)
                })
                source_systems.add(data_source)
                confidence_scores.append(conf)
            
            for field_name, candidates in field_data.items():
                candidates.sort(key=lambda x: x['combined_score'], reverse=True)
                best_candidate = candidates[0]
                
                if best_candidate['combined_score'] > 0.5:
                    best_data[field_name] = best_candidate['value']
            
            network_data = self._extract_intelligent_network_data(field_data)
            best_data.update(network_data)
            
            source_flags = self._determine_intelligent_source_flags(source_systems)
            best_data.update(source_flags)
            
            best_data['source_systems'] = ','.join(sorted(source_systems))
            best_data['source_count'] = len(source_systems)
            best_data['data_quality_score'] = self._calculate_data_quality_score(field_data)
            best_data['data_completeness_score'] = self._calculate_completeness_score(best_data)
            best_data['intelligence_score'] = self._calculate_intelligence_score(field_data, source_systems)
            
            return best_data
            
        except Exception:
            return {}
    
    def _extract_intelligent_network_data(self, field_data: Dict[str, List[Dict]]) -> Dict[str, str]:
        network_data = {}
        
        ip_candidates = []
        for field_name in ['ip_address', 'ip', 'addr', 'inet_addr']:
            if field_name in field_data:
                ip_candidates.extend(field_data[field_name])
        
        if ip_candidates:
            best_ip = max(ip_candidates, key=lambda x: x['combined_score'])
            if best_ip['combined_score'] > 0.6:
                network_data['ip_addresses'] = best_ip['value']
        
        mac_candidates = []
        for field_name in ['mac_address', 'mac', 'ethernet', 'physical_address']:
            if field_name in field_data:
                mac_candidates.extend(field_data[field_name])
        
        if mac_candidates:
            best_mac = max(mac_candidates, key=lambda x: x['combined_score'])
            if best_mac['combined_score'] > 0.6:
                network_data['mac_addresses'] = best_mac['value']
        
        return network_data
    
    def _determine_intelligent_source_flags(self, source_systems: Set[str]) -> Dict[str, bool]:
        flags = {
            'found_in_cmdb': False,
            'has_crowdstrike': False,
            'in_splunk': False,
            'in_chronicle': False
        }
        
        source_indicators = {
            'found_in_cmdb': ['cmdb', 'inventory', 'asset', 'endpoint'],
            'has_crowdstrike': ['crowdstrike', 'cs', 'falcon', 'edr', 'agent'],
            'in_splunk': ['splunk', 'spl', 'log', 'event'],
            'in_chronicle': ['chronicle', 'security', 'siem']
        }
        
        for flag_name, indicators in source_indicators.items():
            for source in source_systems:
                source_lower = source.lower()
                if any(indicator in source_lower for indicator in indicators):
                    flags[flag_name] = True
                    break
        
        return flags
    
    def _calculate_data_quality_score(self, field_data: Dict[str, List[Dict]]) -> float:
        if not field_data:
            return 0.0
        
        quality_factors = []
        
        for field_name, candidates in field_data.items():
            if candidates:
                best_candidate = max(candidates, key=lambda x: x['combined_score'])
                quality_factors.append(best_candidate['combined_score'])
        
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    def _calculate_completeness_score(self, data: Dict[str, Any]) -> float:
        critical_fields = [
            'fqdn', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if data.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_intelligence_score(self, field_data: Dict[str, List[Dict]], sources: Set[str]) -> float:
        intelligence_factors = {
            'source_diversity': min(len(sources) / 4, 1.0),
            'data_richness': min(len(field_data) / 10, 1.0),
            'confidence_level': self._calculate_average_confidence(field_data),
            'validation_quality': self._calculate_average_validation(field_data)
        }
        
        return sum(intelligence_factors.values()) / len(intelligence_factors)
    
    def _calculate_average_confidence(self, field_data: Dict[str, List[Dict]]) -> float:
        all_confidences = []
        for candidates in field_data.values():
            for candidate in candidates:
                all_confidences.append(candidate['confidence'])
        
        return sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    
    def _calculate_average_validation(self, field_data: Dict[str, List[Dict]]) -> float:
        all_validations = []
        for candidates in field_data.values():
            for candidate in candidates:
                all_validations.append(candidate['validation'])
        
        return sum(all_validations) / len(all_validations) if all_validations else 0.0
    
    def _insert_intelligent_inventory(self, hostname: str, data: Dict[str, Any]):
        try:
            self.conn.execute("""
            INSERT OR REPLACE INTO intelligent_asset_inventory (
                hostname, fqdn, ip_addresses, mac_addresses, infrastructure_type,
                system_classification, operating_system, global_region, country,
                data_center, cloud_region, business_unit, environment, cost_center,
                owner, criticality, found_in_cmdb, has_crowdstrike, in_splunk,
                in_chronicle, source_systems, source_count, data_completeness_score,
                data_quality_score, intelligence_score, enrichment_metadata, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                hostname, data.get('fqdn', ''), data.get('ip_addresses', ''),
                data.get('mac_addresses', ''), data.get('infrastructure_type', ''),
                data.get('system_classification', ''), data.get('operating_system', ''),
                data.get('global_region', ''), data.get('country', ''),
                data.get('data_center', ''), data.get('cloud_region', ''),
                data.get('business_unit', ''), data.get('environment', ''),
                data.get('cost_center', ''), data.get('owner', ''),
                data.get('criticality', ''), data.get('found_in_cmdb', False),
                data.get('has_crowdstrike', False), data.get('in_splunk', False),
                data.get('in_chronicle', False), data.get('source_systems', ''),
                data.get('source_count', 0), data.get('data_completeness_score', 0.0),
                data.get('data_quality_score', 0.0), data.get('intelligence_score', 0.0),
                json.dumps({k: v for k, v in data.items() if k.startswith('metadata_')})
            ))
        except Exception:
            pass
    
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
                SELECT COUNT(*) FROM intelligent_asset_inventory WHERE data_quality_score > 0.8
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
        
        self.db_path = self.config.get('database_path', 'ao1_visibility_cmdb.db')
        self.data_fusion = IntelligentDataFusion(self.db_path)
        
        self.discovered_hostnames = set()
        self.processed_tables = set()
        self._lock = threading.RLock()
    
    async def execute_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            await self._execute_intelligent_hostname_discovery(all_table_metadata)
            
            await self._execute_intelligent_data_enrichment(all_table_metadata)
            
            PrettyLogger.info("Building intelligent asset inventory")
            inventory_stats = self.data_fusion.build_intelligent_inventory()
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_intelligent_stats(time.time() - start_time, inventory_stats)
            analysis_queries = self._create_intelligent_queries()
            
            PrettyLogger.success("Intelligent discovery completed successfully")
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
                project_metadata = await self.table_discovery.discover_intelligent_table_metadata(client_mgr, project_id)
                all_metadata.extend(project_metadata)
                
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        all_metadata.sort(key=lambda x: x['data_richness_score'], reverse=True)
        
        PrettyLogger.success(f"Analyzed {len(all_metadata)} tables with intelligent scoring")
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
                    PrettyLogger.discovery(table_name, discovered_count, 0)
                
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
        
        hostname_query = f"""
        SELECT DISTINCT 
            UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname
        FROM `{table_path}`
        {partition_filter} `{hostname_column}` IS NOT NULL
            AND LENGTH(TRIM(CAST(`{hostname_column}` AS STRING))) >= 2
            AND TRIM(CAST(`{hostname_column}` AS STRING)) NOT REGEXP r'^[0-9\\.]+
        LIMIT 50000
        """
        
        try:
            with client_mgr.get_client() as client:
                job = client.query(hostname_query)
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
                
        except Exception:
            return 0
    
    async def _execute_intelligent_data_enrichment(self, table_metadata: List[Dict[str, Any]]):
        PrettyLogger.info("Phase 2: Intelligent data enrichment")
        
        hostname_batches = list(self.discovered_hostnames)
        batch_size = 1000
        
        for i in range(0, len(hostname_batches), batch_size):
            if self.signal_handler.shutdown_requested:
                break
            
            batch = hostname_batches[i:i + batch_size]
            
            for table_meta in table_metadata:
                if self.signal_handler.shutdown_requested:
                    break
                
                try:
                    enrichments = await self._enrich_batch_intelligently(table_meta, batch)
                    
                    if enrichments > 0:
                        table_name = table_meta['table_id']
                        PrettyLogger.info(f"{table_name}: {enrichments} intelligent enrichments")
                        
                except Exception as e:
                    continue
            
            progress_pct = min(100, ((i + batch_size) / len(hostname_batches)) * 100)
            PrettyLogger.info(f"Enrichment progress: {progress_pct:.1f}%")
    
    async def _enrich_batch_intelligently(self, table_meta: Dict[str, Any], target_hostnames: List[str]) -> int:
        hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
        column_analysis = table_meta['column_analysis']
        
        if not column_analysis:
            return 0
        
        project_id = table_meta['project_id']
        table_path = table_meta['full_table_path']
        
        client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
        
        data_columns = {}
        for column, analysis in column_analysis.items():
            if column != hostname_column and analysis:
                field_type, confidence, metadata = analysis
                if confidence > 0.5:
                    data_columns[field_type] = {
                        'column': column,
                        'confidence': confidence,
                        'validation_score': metadata.get('data_quality', {}).get('score', 0.5),
                        'semantic_score': metadata.get('semantic_score', 0.5)
                    }
        
        if not data_columns:
            return 0
        
        hostname_list = "', '".join([h.replace("'", "''") for h in target_hostnames])
        
        select_fields = [f"UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) as hostname"]
        for field_type, col_info in data_columns.items():
            select_fields.append(f"CAST(`{col_info['column']}` AS STRING) as {field_type}")
        
        enrichment_query = f"""
        SELECT {', '.join(select_fields)}
        FROM `{table_path}`
        WHERE UPPER(TRIM(CAST(`{hostname_column}` AS STRING))) IN ('{hostname_list}')
            AND `{hostname_column}` IS NOT NULL
        """
        
        try:
            with client_mgr.get_client() as client:
                job = client.query(enrichment_query)
                results = list(job.result())
                
                data_source = self._determine_intelligent_data_source(table_path)
                enrichments_added = 0
                
                for row in results:
                    hostname = row[0]
                    
                    for i, (field_type, col_info) in enumerate(data_columns.items(), 1):
                        if i < len(row) and row[i]:
                            field_value = str(row[i]).strip()
                            
                            if field_value and len(field_value) > 0:
                                success = self.data_fusion.add_intelligent_data(
                                    hostname, field_type, field_value, data_source, table_path,
                                    col_info['confidence'], col_info['validation_score'], col_info['semantic_score']
                                )
                                
                                if success:
                                    enrichments_added += 1
                
                return enrichments_added
                
        except Exception:
            return 0
    
    def _determine_intelligent_data_source(self, table_path: str) -> str:
        path_lower = table_path.lower()
        
        source_patterns = {
            'cmdb': ['cmdb', 'asset', 'inventory', 'dim_endpoint'],
            'crowdstrike': ['crowdstrike', 'cs', 'falcon', 'agent', 'edr'],
            'splunk': ['splunk', 'spl', 'log', 'event'],
            'chronicle': ['chronicle', 'security', 'siem'],
            'network': ['network', 'net', 'infrastructure', 'infra'],
            'monitoring': ['monitoring', 'monitor', 'performance', 'perf'],
            'compliance': ['compliance', 'audit', 'policy', 'governance']
        }
        
        for source_type, patterns in source_patterns.items():
            if any(pattern in path_lower for pattern in patterns):
                return source_type
        
        return 'discovery'
    
    def _generate_intelligent_stats(self, processing_time: float, inventory_stats: Dict[str, int]) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'intelligent_multi_dimensional',
            'total_endpoints_discovered': intelligence_stats.get('total_endpoints', 0),
            'consolidated_assets': intelligence_stats.get('total_assets', 0),
            'total_data_points': intelligence_stats.get('total_data_points', 0),
            'avg_intelligence_score': intelligence_stats.get('avg_intelligence_score', 0.0),
            'high_quality_assets': intelligence_stats.get('high_quality_assets', 0),
            'unique_hostnames_discovered': len(self.discovered_hostnames),
            'tables_analyzed': len(self.processed_tables),
            'cache_performance': cache_stats,
            'inventory_build_stats': inventory_stats
        }
    
    def _create_intelligent_queries(self) -> Dict[str, str]:
        return {
            'intelligent_asset_overview': """
            SELECT 
                hostname, fqdn, ip_addresses, infrastructure_type, global_region,
                business_unit, environment, found_in_cmdb, has_crowdstrike,
                in_splunk, in_chronicle, data_completeness_score, data_quality_score,
                intelligence_score, source_systems, source_count
            FROM intelligent_asset_inventory 
            ORDER BY intelligence_score DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_analysis': """
            SELECT 
                CASE 
                    WHEN intelligence_score >= 0.9 THEN 'Excellent Intelligence (90%+)'
                    WHEN intelligence_score >= 0.7 THEN 'High Intelligence (70-89%)'
                    WHEN intelligence_score >= 0.5 THEN 'Good Intelligence (50-69%)'
                    WHEN intelligence_score >= 0.3 THEN 'Fair Intelligence (30-49%)'
                    ELSE 'Low Intelligence (<30%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                AVG(intelligence_score) as avg_intelligence,
                AVG(data_quality_score) as avg_quality,
                AVG(data_completeness_score) as avg_completeness
            FROM intelligent_asset_inventory
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'data_source_intelligence': """
            SELECT 
                data_source,
                COUNT(DISTINCT primary_hostname) as unique_endpoints,
                COUNT(*) as total_data_points,
                AVG(confidence_score) as avg_confidence,
                AVG(validation_score) as avg_validation,
                AVG(semantic_score) as avg_semantic,
                COUNT(DISTINCT field_name) as field_types_contributed
            FROM intelligent_endpoint_data
            GROUP BY data_source
            ORDER BY unique_endpoints DESC;
            """,
            
            'enrichment_effectiveness': """
            SELECT 
                field_name,
                COUNT(DISTINCT primary_hostname) as endpoints_enriched,
                COUNT(DISTINCT data_source) as contributing_sources,
                AVG(confidence_score) as avg_confidence,
                MAX(confidence_score) as max_confidence,
                COUNT(*) as total_entries
            FROM intelligent_endpoint_data
            GROUP BY field_name
            ORDER BY endpoints_enriched DESC;
            """,
            
            'hostname_discovery_analysis': """
            SELECT 
                CASE 
                    WHEN seen_count >= 5 THEN 'High Visibility (5+ sources)'
                    WHEN seen_count >= 3 THEN 'Good Visibility (3-4 sources)'
                    WHEN seen_count >= 2 THEN 'Fair Visibility (2 sources)'
                    ELSE 'Single Source'
                END as visibility_tier,
                COUNT(*) as hostname_count,
                AVG(seen_count) as avg_source_count,
                AVG(confidence_score) as avg_confidence
            FROM intelligent_endpoints
            GROUP BY visibility_tier
            ORDER BY avg_source_count DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()