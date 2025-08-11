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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

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

class MLEntityMatcher(nn.Module):
    def __init__(self, input_dim=50, hidden_dim=128):
        super().__init__()
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 64)
        self.fc4 = nn.Linear(64, 1)
        self.dropout = nn.Dropout(0.3)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
        self.to(self.device)
        
    def forward(self, x):
        x = x.to(self.device)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.relu(self.fc3(x))
        x = self.sigmoid(self.fc4(x))
        return x

class NetworkTopologyEngine:
    def __init__(self):
        self.network_graph = nx.Graph()
        self.subnet_mapping = {}
        self.communication_patterns = defaultdict(set)
        self.temporal_connections = defaultdict(list)
        
    def add_network_observation(self, src_ip: str, dst_ip: str, timestamp: datetime, protocol: str = None):
        try:
            src_addr = ipaddress.ip_address(src_ip)
            dst_addr = ipaddress.ip_address(dst_ip)
            
            if src_addr.is_private and dst_addr.is_private:
                self.network_graph.add_edge(src_ip, dst_ip, 
                                          weight=1, 
                                          protocol=protocol,
                                          last_seen=timestamp)
                
                self.communication_patterns[src_ip].add(dst_ip)
                self.temporal_connections[src_ip].append((dst_ip, timestamp))
                
                self._update_subnet_mapping(src_ip)
                self._update_subnet_mapping(dst_ip)
                
        except ValueError:
            pass
    
    def _update_subnet_mapping(self, ip: str):
        try:
            addr = ipaddress.ip_address(ip)
            if addr.is_private:
                for prefix_len in [24, 16, 8]:
                    subnet = ipaddress.ip_network(f"{addr}/{prefix_len}", strict=False)
                    subnet_key = str(subnet)
                    if subnet_key not in self.subnet_mapping:
                        self.subnet_mapping[subnet_key] = set()
                    self.subnet_mapping[subnet_key].add(ip)
        except ValueError:
            pass
    
    def calculate_network_proximity(self, ip1: str, ip2: str) -> float:
        try:
            addr1 = ipaddress.ip_address(ip1)
            addr2 = ipaddress.ip_address(ip2)
            
            if addr1 == addr2:
                return 1.0
            
            for prefix_len in [24, 16, 8]:
                subnet1 = ipaddress.ip_network(f"{addr1}/{prefix_len}", strict=False)
                subnet2 = ipaddress.ip_network(f"{addr2}/{prefix_len}", strict=False)
                if subnet1 == subnet2:
                    return 1.0 - (prefix_len / 32.0)
            
            if nx.has_path(self.network_graph, ip1, ip2):
                path_length = nx.shortest_path_length(self.network_graph, ip1, ip2)
                return max(0.1, 1.0 - (path_length * 0.2))
            
            return 0.0
            
        except (ValueError, nx.NetworkXNoPath):
            return 0.0
    
    def find_network_clusters(self) -> Dict[str, Set[str]]:
        clusters = {}
        communities = nx.community.greedy_modularity_communities(self.network_graph)
        
        for i, community in enumerate(communities):
            cluster_id = f"cluster_{i}"
            clusters[cluster_id] = set(community)
        
        return clusters

class SemanticPatternLearner:
    def __init__(self):
        self.hostname_patterns = {}
        self.pattern_clusters = {}
        self.naming_conventions = {}
        self.tfidf_vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
        self.pattern_confidence = {}
        
    def learn_hostname_patterns(self, hostnames: List[str]) -> Dict[str, Any]:
        if len(hostnames) < 10:
            return {}
        
        cleaned_hostnames = [h.upper() for h in hostnames if len(h) > 2]
        
        structural_patterns = self._extract_structural_patterns(cleaned_hostnames)
        semantic_patterns = self._extract_semantic_patterns(cleaned_hostnames)
        cluster_patterns = self._cluster_similar_hostnames(cleaned_hostnames)
        
        self.hostname_patterns = {
            'structural': structural_patterns,
            'semantic': semantic_patterns,
            'clusters': cluster_patterns
        }
        
        return self.hostname_patterns
    
    def _extract_structural_patterns(self, hostnames: List[str]) -> Dict[str, float]:
        patterns = defaultdict(int)
        
        for hostname in hostnames:
            pattern = re.sub(r'[A-Z]+', 'ALPHA', hostname)
            pattern = re.sub(r'[0-9]+', 'NUM', pattern)
            pattern = re.sub(r'[-_]+', 'SEP', pattern)
            patterns[pattern] += 1
        
        total = len(hostnames)
        pattern_frequencies = {p: count/total for p, count in patterns.items() if count >= 3}
        
        return dict(sorted(pattern_frequencies.items(), key=lambda x: x[1], reverse=True))
    
    def _extract_semantic_patterns(self, hostnames: List[str]) -> Dict[str, Set[str]]:
        semantic_groups = {
            'environments': set(),
            'functions': set(),
            'locations': set(),
            'technologies': set()
        }
        
        env_keywords = ['PROD', 'DEV', 'TEST', 'STG', 'UAT', 'QA', 'DR']
        function_keywords = ['WEB', 'APP', 'DB', 'SQL', 'SRV', 'SVR', 'SERVER']
        location_keywords = ['NYC', 'LAX', 'CHI', 'LON', 'TKY', 'US', 'EU', 'AP']
        tech_keywords = ['WIN', 'LNX', 'LINUX', 'UNIX', 'VM', 'ESX', 'DOCKER']
        
        for hostname in hostnames:
            for keyword in env_keywords:
                if keyword in hostname:
                    semantic_groups['environments'].add(keyword)
            
            for keyword in function_keywords:
                if keyword in hostname:
                    semantic_groups['functions'].add(keyword)
            
            for keyword in location_keywords:
                if keyword in hostname:
                    semantic_groups['locations'].add(keyword)
            
            for keyword in tech_keywords:
                if keyword in hostname:
                    semantic_groups['technologies'].add(keyword)
        
        return {k: v for k, v in semantic_groups.items() if v}
    
    def _cluster_similar_hostnames(self, hostnames: List[str]) -> Dict[str, List[str]]:
        if len(hostnames) < 5:
            return {}
        
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(hostnames)
            
            clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
            cluster_labels = clustering.fit_predict(tfidf_matrix.toarray())
            
            clusters = defaultdict(list)
            for hostname, label in zip(hostnames, cluster_labels):
                if label != -1:
                    clusters[f"cluster_{label}"].append(hostname)
            
            return dict(clusters)
            
        except Exception:
            return {}

class SuperIntelligentHostLinker:
    def __init__(self, cache_manager: IntelligentCacheManager):
        self.cache = cache_manager
        self.network_engine = NetworkTopologyEngine()
        self.pattern_learner = SemanticPatternLearner()
        self.fingerprints = {}
        self.discovered_links = defaultdict(set)
        self._lock = threading.RLock()
        
    def build_comprehensive_fingerprints(self, all_table_metadata: List[Dict]) -> Dict[str, HostFingerprint]:
        PrettyLogger.info("Building multi-dimensional host fingerprints")
        
        raw_observations = self._extract_all_observations(all_table_metadata)
        
        fingerprints = {}
        for primary_id, observations in raw_observations.items():
            fingerprint = self._create_fingerprint(primary_id, observations)
            if fingerprint:
                fingerprints[primary_id] = fingerprint
        
        all_hostnames = []
        for fp in fingerprints.values():
            all_hostnames.extend(fp.normalized_hostnames)
        
        learned_patterns = self.pattern_learner.learn_hostname_patterns(all_hostnames)
        PrettyLogger.success(f"Learned {len(learned_patterns)} hostname patterns")
        
        for fingerprint in fingerprints.values():
            fingerprint.semantic_patterns = self._extract_semantic_features(
                fingerprint.normalized_hostnames, learned_patterns
            )
        
        self.fingerprints = fingerprints
        PrettyLogger.success(f"Built {len(fingerprints)} comprehensive fingerprints")
        
        return fingerprints
    
    def _extract_all_observations(self, table_metadata: List[Dict]) -> Dict[str, List[Dict]]:
        observations = defaultdict(list)
        
        for table_meta in table_metadata:
            hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
            if not hostname_column:
                continue
            
            sample_data = table_meta.get('sample_data', {})
            hostnames = sample_data.get(hostname_column, [])
            
            for hostname in hostnames:
                normalized = self._normalize_hostname_advanced(hostname)
                if normalized:
                    observation = {
                        'original_hostname': hostname,
                        'normalized_hostname': normalized,
                        'table_source': table_meta['full_table_path'],
                        'all_data': {col: values for col, values in sample_data.items()},
                        'timestamp': datetime.now(),
                        'table_metadata': table_meta
                    }
                    observations[normalized].append(observation)
        
        return dict(observations)
    
    def _normalize_hostname_advanced(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.strip().upper()
        
        if len(normalized) < 2 or len(normalized) > 253:
            return ""
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, normalized):
                return ""
        
        normalized = re.sub(r'^[^A-Z0-9]+', '', normalized)
        normalized = re.sub(r'[^A-Z0-9\-\.]+$', '', normalized)
        
        if '.' in normalized:
            parts = normalized.split('.')
            if len(parts) > 1 and all(part.isdigit() for part in parts):
                return ""
            normalized = parts[0]
        
        if len(normalized) < 2:
            return ""
        
        return normalized
    
    def _create_fingerprint(self, primary_id: str, observations: List[Dict]) -> Optional[HostFingerprint]:
        if not observations:
            return None
        
        normalized_hostnames = set()
        ip_addresses = set()
        mac_addresses = set()
        domain_names = set()
        serial_numbers = set()
        asset_tags = set()
        network_segments = set()
        temporal_signatures = []
        source_tables = set()
        
        for obs in observations:
            normalized_hostnames.add(obs['normalized_hostname'])
            source_tables.add(obs['table_source'])
            temporal_signatures.append(obs['timestamp'])
            
            variants = self._extract_hostname_variants(obs['original_hostname'])
            normalized_hostnames.update(variants)
            
            network_data = self._extract_network_identifiers(obs['all_data'])
            ip_addresses.update(network_data.get('ips', set()))
            mac_addresses.update(network_data.get('macs', set()))
            domain_names.update(network_data.get('domains', set()))
            
            for ip in ip_addresses:
                try:
                    addr = ipaddress.ip_address(ip)
                    if addr.is_private:
                        network = ipaddress.ip_network(f"{addr}/24", strict=False)
                        network_segments.add(str(network))
                except ValueError:
                    pass
        
        confidence_score = self._calculate_fingerprint_confidence(
            normalized_hostnames, ip_addresses, mac_addresses, source_tables
        )
        
        return HostFingerprint(
            primary_id=primary_id,
            normalized_hostnames=normalized_hostnames,
            ip_addresses=ip_addresses,
            mac_addresses=mac_addresses,
            domain_names=domain_names,
            serial_numbers=serial_numbers,
            asset_tags=asset_tags,
            network_segments=network_segments,
            temporal_signatures=temporal_signatures,
            semantic_patterns={},
            confidence_score=confidence_score,
            source_tables=source_tables
        )
    
    def _extract_hostname_variants(self, hostname: str) -> Set[str]:
        variants = set()
        
        if not hostname:
            return variants
        
        base = hostname.upper().strip()
        variants.add(base)
        
        if '.' in base:
            fqdn_parts = base.split('.')
            variants.add(fqdn_parts[0])
            if len(fqdn_parts) > 1:
                variants.add('.'.join(fqdn_parts[:2]))
        
        if '-' in base:
            variants.add(base.replace('-', ''))
            parts = base.split('-')
            if len(parts) > 1:
                variants.add(parts[0])
        
        if '_' in base:
            variants.add(base.replace('_', ''))
            variants.add(base.replace('_', '-'))
        
        number_pattern = re.search(r'(\d+)$', base)
        if number_pattern:
            base_without_num = base[:number_pattern.start()]
            current_num = int(number_pattern.group(1))
            
            for offset in [-2, -1, 1, 2]:
                new_num = current_num + offset
                if new_num > 0:
                    new_variant = base_without_num + str(new_num).zfill(len(number_pattern.group(1)))
                    variants.add(new_variant)
        
        return {v for v in variants if len(v) >= 2}
    
    def _extract_network_identifiers(self, data: Dict[str, List[str]]) -> Dict[str, Set[str]]:
        identifiers = {'ips': set(), 'macs': set(), 'domains': set()}
        
        for column, values in data.items():
            for value in values:
                if not value:
                    continue
                
                value_str = str(value).strip()
                
                ip_matches = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', value_str)
                for ip in ip_matches:
                    try:
                        ipaddress.ip_address(ip)
                        identifiers['ips'].add(ip)
                    except ValueError:
                        pass
                
                mac_patterns = [
                    r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',
                    r'\b(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}\b'
                ]
                for pattern in mac_patterns:
                    mac_matches = re.findall(pattern, value_str)
                    identifiers['macs'].update(mac_matches)
                
                domain_pattern = r'\b[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}\b'
                domain_matches = re.findall(domain_pattern, value_str)
                for domain in domain_matches:
                    if '.' in domain and not domain.replace('.', '').isdigit():
                        identifiers['domains'].add(domain.lower())
        
        return identifiers
    
    def _calculate_fingerprint_confidence(self, hostnames: Set[str], ips: Set[str], 
                                        macs: Set[str], sources: Set[str]) -> float:
        confidence_factors = []
        
        hostname_factor = min(1.0, len(hostnames) / 3.0)
        confidence_factors.append(hostname_factor * 0.3)
        
        ip_factor = min(1.0, len(ips) / 2.0)
        confidence_factors.append(ip_factor * 0.3)
        
        mac_factor = min(1.0, len(macs))
        confidence_factors.append(mac_factor * 0.2)
        
        source_factor = min(1.0, len(sources) / 3.0)
        confidence_factors.append(source_factor * 0.2)
        
        return sum(confidence_factors)
    
    def _extract_semantic_features(self, hostnames: Set[str], patterns: Dict) -> Dict[str, float]:
        features = {}
        
        for hostname in hostnames:
            for pattern_type, pattern_data in patterns.items():
                if pattern_type == 'structural':
                    for pattern, frequency in pattern_data.items():
                        hostname_pattern = self._extract_structural_pattern(hostname)
                        if hostname_pattern == pattern:
                            features[f"struct_{pattern}"] = frequency
                
                elif pattern_type == 'semantic':
                    for category, keywords in pattern_data.items():
                        for keyword in keywords:
                            if keyword in hostname:
                                features[f"sem_{category}_{keyword}"] = 1.0
        
        return features
    
    def _extract_structural_pattern(self, hostname: str) -> str:
        pattern = re.sub(r'[A-Z]+', 'ALPHA', hostname)
        pattern = re.sub(r'[0-9]+', 'NUM', pattern)
        pattern = re.sub(r'[-_]+', 'SEP', pattern)
        return pattern
    
    def execute_multi_strategy_linking(self) -> Dict[str, Set[str]]:
        PrettyLogger.info("Executing multi-strategy entity linking")
        
        exact_links = self._find_exact_matches()
        fuzzy_links = self._find_fuzzy_matches()
        
        combined_links = self._combine_link_strategies([
            (exact_links, 1.0),
            (fuzzy_links, 0.8)
        ])
        
        resolved_links = self._resolve_conflicts(combined_links)
        
        PrettyLogger.success(f"Linked {len(resolved_links)} entity clusters")
        return resolved_links
    
    def _find_exact_matches(self) -> Dict[str, Set[str]]:
        links = defaultdict(set)
        
        for id1, fp1 in self.fingerprints.items():
            for id2, fp2 in self.fingerprints.items():
                if id1 >= id2:
                    continue
                
                if fp1.ip_addresses & fp2.ip_addresses:
                    links[id1].add(id2)
                    links[id2].add(id1)
                
                if fp1.mac_addresses & fp2.mac_addresses:
                    links[id1].add(id2)
                    links[id2].add(id1)
                
                if fp1.normalized_hostnames & fp2.normalized_hostnames:
                    links[id1].add(id2)
                    links[id2].add(id1)
        
        return dict(links)
    
    def _find_fuzzy_matches(self) -> Dict[str, Set[str]]:
        links = defaultdict(set)
        
        for id1, fp1 in self.fingerprints.items():
            for id2, fp2 in self.fingerprints.items():
                if id1 >= id2:
                    continue
                
                hostname_similarity = self._calculate_hostname_fuzzy_similarity(
                    fp1.normalized_hostnames, fp2.normalized_hostnames
                )
                
                if hostname_similarity > 0.8:
                    links[id1].add(id2)
                    links[id2].add(id1)
        
        return dict(links)
    
    def _calculate_hostname_fuzzy_similarity(self, hostnames1: Set[str], hostnames2: Set[str]) -> float:
        if not hostnames1 or not hostnames2:
            return 0.0
        
        max_similarity = 0.0
        for h1 in hostnames1:
            for h2 in hostnames2:
                similarity = self._string_similarity(h1, h2)
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        if s1 == s2:
            return 1.0
        
        if not s1 or not s2:
            return 0.0
        
        longer = s1 if len(s1) > len(s2) else s2
        shorter = s2 if len(s1) > len(s2) else s1
        
        if len(longer) == 0:
            return 1.0
        
        edit_distance = self._levenshtein_distance(longer, shorter)
        return (len(longer) - edit_distance) / len(longer)
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _combine_link_strategies(self, strategy_results: List[Tuple[Dict[str, Set[str]], float]]) -> Dict[str, Dict[str, float]]:
        combined_scores = defaultdict(lambda: defaultdict(float))
        
        for links, weight in strategy_results:
            for id1, connected_ids in links.items():
                for id2 in connected_ids:
                    combined_scores[id1][id2] += weight
        
        return dict(combined_scores)
    
    def _resolve_conflicts(self, combined_links: Dict[str, Dict[str, float]]) -> Dict[str, Set[str]]:
        resolved = defaultdict(set)
        
        threshold = 1.0
        
        for id1, connections in combined_links.items():
            for id2, score in connections.items():
                if score >= threshold:
                    resolved[id1].add(id2)
        
        return dict(resolved)

class SuperIntelligentDataFusion:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_advanced_tables()
        self._lock = threading.RLock()
        self.host_linker = None
        
    def _setup_advanced_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS master_entity_registry (
            entity_id VARCHAR PRIMARY KEY,
            primary_hostname VARCHAR,
            confidence_score DOUBLE DEFAULT 0.0,
            fingerprint_data TEXT,
            linked_identities TEXT,
            creation_timestamp TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS entity_observations (
            observation_id VARCHAR PRIMARY KEY,
            entity_id VARCHAR,
            source_table VARCHAR,
            observation_type VARCHAR,
            field_name VARCHAR,
            field_value TEXT,
            confidence_score DOUBLE DEFAULT 0.0,
            validation_score DOUBLE DEFAULT 0.0,
            temporal_score DOUBLE DEFAULT 0.0,
            network_score DOUBLE DEFAULT 0.0,
            semantic_score DOUBLE DEFAULT 0.0,
            ml_score DOUBLE DEFAULT 0.0,
            observation_timestamp TIMESTAMP DEFAULT NOW()
        )
        """)
        
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS consolidated_asset_intelligence (
            asset_id VARCHAR PRIMARY KEY,
            hostname VARCHAR,
            fqdn VARCHAR,
            ip_addresses TEXT,
            mac_addresses TEXT,
            infrastructure_type VARCHAR,
            system_classification VARCHAR,
            operating_system VARCHAR,
            global_region VARCHAR,
            country VARCHAR,
            data_center VARCHAR,
            business_unit VARCHAR,
            cost_center VARCHAR,
            environment VARCHAR,
            criticality_level VARCHAR,
            owner VARCHAR,
            application VARCHAR,
            status VARCHAR,
            serial_number VARCHAR,
            asset_tag VARCHAR,
            vendor VARCHAR,
            model VARCHAR,
            version VARCHAR,
            cpu_info VARCHAR,
            memory_info VARCHAR,
            storage_info VARCHAR,
            network_info VARCHAR,
            network_segment VARCHAR,
            patch_level VARCHAR,
            compliance_info VARCHAR,
            backup_info VARCHAR,
            monitoring_info VARCHAR,
            license_info VARCHAR,
            custom_fields TEXT,
            cmdb_presence BOOLEAN DEFAULT FALSE,
            splunk_visibility BOOLEAN DEFAULT FALSE,
            chronicle_visibility BOOLEAN DEFAULT FALSE,
            crowdstrike_coverage BOOLEAN DEFAULT FALSE,
            tanium_coverage BOOLEAN DEFAULT FALSE,
            visibility_gap_score DOUBLE DEFAULT 0.0,
            data_quality_score DOUBLE DEFAULT 0.0,
            intelligence_confidence DOUBLE DEFAULT 0.0,
            enrichment_completeness DOUBLE DEFAULT 0.0,
            network_connectivity_map TEXT,
            source_system_count INTEGER DEFAULT 0,
            total_fields_populated INTEGER DEFAULT 0,
            last_observation TIMESTAMP,
            enrichment_timestamp TIMESTAMP DEFAULT NOW()
        )
        """)
    
    def initialize_super_intelligent_linking(self, cache_manager: IntelligentCacheManager):
        self.host_linker = SuperIntelligentHostLinker(cache_manager)
        
    def process_table_metadata_intelligently(self, all_table_metadata: List[Dict]) -> Dict[str, Any]:
        if not self.host_linker:
            raise RuntimeError("Super intelligent linking not initialized")
        
        PrettyLogger.info("Processing table metadata with advanced intelligence")
        
        fingerprints = self.host_linker.build_comprehensive_fingerprints(all_table_metadata)
        
        entity_links = self.host_linker.execute_multi_strategy_linking()
        
        stats = self._register_entities_and_observations(fingerprints, entity_links, all_table_metadata)
        
        enrichment_stats = self._enrich_entities_from_all_tables(fingerprints, all_table_metadata)
        
        consolidated_stats = self._build_consolidated_intelligence()
        
        return {
            'fingerprints_created': len(fingerprints),
            'entity_clusters': len(entity_links),
            'registration_stats': stats,
            'enrichment_stats': enrichment_stats,
            'consolidation_stats': consolidated_stats
        }
    
    def _enrich_entities_from_all_tables(self, fingerprints: Dict[str, HostFingerprint], 
                                       all_table_metadata: List[Dict]) -> Dict[str, int]:
        PrettyLogger.info("Enriching entities with data from ALL columns in ALL tables")
        
        enrichment_stats = {
            'total_enrichments': 0,
            'columns_processed': 0,
            'tables_processed': 0,
            'unique_fields_discovered': set()
        }
        
        for table_meta in all_table_metadata:
            hostname_column = table_meta['hostname_analysis']['primary_hostname_column']
            if not hostname_column:
                continue
            
            sample_data = table_meta.get('sample_data', {})
            hostname_samples = sample_data.get(hostname_column, [])
            
            if not hostname_samples:
                continue
            
            enrichment_stats['tables_processed'] += 1
            
            for column_name in table_meta.get('all_columns', []):
                if column_name == hostname_column:
                    continue
                
                enrichment_stats['columns_processed'] += 1
                column_values = sample_data.get(column_name, [])
                
                if not column_values:
                    continue
                
                field_type = self._determine_field_type_from_name_and_values(column_name, column_values)
                enrichment_stats['unique_fields_discovered'].add(field_type)
                
                for i, sample_hostname in enumerate(hostname_samples):
                    normalized_hostname = self.host_linker._normalize_hostname_advanced(sample_hostname)
                    if not normalized_hostname:
                        continue
                    
                    matching_fingerprint = self._find_matching_fingerprint(normalized_hostname, fingerprints)
                    if not matching_fingerprint:
                        continue
                    
                    entity_id = f"entity_{matching_fingerprint.primary_id}"
                    
                    if i < len(column_values) and column_values[i]:
                        value = str(column_values[i]).strip()
                        if self._is_valid_enrichment_value(value):
                            
                            confidence = self._calculate_field_confidence(field_type, value, column_name)
                            
                            observation_id = hashlib.md5(
                                f"{entity_id}_{table_meta['full_table_path']}_{column_name}_{value}".encode()
                            ).hexdigest()
                            
                            self._insert_comprehensive_observation(
                                observation_id, entity_id, table_meta['full_table_path'],
                                field_type, column_name, value, confidence, table_meta
                            )
                            
                            enrichment_stats['total_enrichments'] += 1
        
        enrichment_stats['unique_fields_discovered'] = len(enrichment_stats['unique_fields_discovered'])
        PrettyLogger.success(f"Processed {enrichment_stats['columns_processed']} columns from {enrichment_stats['tables_processed']} tables")
        PrettyLogger.success(f"Added {enrichment_stats['total_enrichments']} comprehensive enrichments")
        return enrichment_stats
    
    def _find_matching_fingerprint(self, normalized_hostname: str, fingerprints: Dict[str, HostFingerprint]) -> Optional[HostFingerprint]:
        for fp_id, fingerprint in fingerprints.items():
            if normalized_hostname in fingerprint.normalized_hostnames:
                return fingerprint
            
            for variant in fingerprint.normalized_hostnames:
                if self._hostnames_are_similar(normalized_hostname, variant):
                    return fingerprint
        
        return None
    
    def _hostnames_are_similar(self, hostname1: str, hostname2: str) -> bool:
        if hostname1 == hostname2:
            return True
        
        if hostname1.replace('-', '') == hostname2.replace('-', ''):
            return True
        
        if hostname1.replace('_', '') == hostname2.replace('_', ''):
            return True
        
        if len(hostname1) > 3 and len(hostname2) > 3:
            if hostname1[:len(hostname1)-2] == hostname2[:len(hostname2)-2]:
                return True
        
        return False
    
    def _determine_field_type_from_name_and_values(self, column_name: str, values: List[str]) -> str:
        column_lower = column_name.lower()
        
        if not values:
            return f"unknown_{column_lower}"
        
        sample_values = [str(v).strip() for v in values[:5] if v]
        if not sample_values:
            return f"unknown_{column_lower}"
        
        if any(keyword in column_lower for keyword in ['fqdn', 'domain', 'dns']):
            if any('.' in v and not v.replace('.', '').isdigit() for v in sample_values):
                return 'fqdn'
        
        if any(keyword in column_lower for keyword in ['ip', 'addr', 'address']):
            if any(self._looks_like_ip(v) for v in sample_values):
                return 'ip_address'
        
        if any(keyword in column_lower for keyword in ['mac', 'ethernet', 'physical']):
            if any(self._looks_like_mac(v) for v in sample_values):
                return 'mac_address'
        
        if any(keyword in column_lower for keyword in ['os', 'operating', 'platform']):
            return 'operating_system'
        
        if any(keyword in column_lower for keyword in ['region', 'location', 'geo', 'site']):
            return 'region'
        
        if any(keyword in column_lower for keyword in ['country', 'nation']):
            return 'country'
        
        if any(keyword in column_lower for keyword in ['datacenter', 'data_center', 'dc', 'facility']):
            return 'data_center'
        
        if any(keyword in column_lower for keyword in ['env', 'environment', 'stage', 'tier']):
            return 'environment'
        
        if any(keyword in column_lower for keyword in ['business', 'unit', 'org', 'department']):
            return 'business_unit'
        
        if any(keyword in column_lower for keyword in ['cost', 'center', 'billing']):
            return 'cost_center'
        
        if any(keyword in column_lower for keyword in ['owner', 'contact', 'responsible']):
            return 'owner'
        
        if any(keyword in column_lower for keyword in ['type', 'category', 'class', 'kind']):
            if any(v.lower() in ['physical', 'virtual', 'cloud', 'container'] for v in sample_values):
                return 'infrastructure_type'
            else:
                return 'system_classification'
        
        if any(keyword in column_lower for keyword in ['app', 'application', 'service', 'software']):
            return 'application'
        
        if any(keyword in column_lower for keyword in ['status', 'state', 'condition']):
            return 'status'
        
        if any(keyword in column_lower for keyword in ['criticality', 'priority', 'importance']):
            return 'criticality_level'
        
        if any(keyword in column_lower for keyword in ['serial', 'sn', 'serialnumber']):
            return 'serial_number'
        
        if any(keyword in column_lower for keyword in ['tag', 'asset', 'inventory']):
            return 'asset_tag'
        
        if any(keyword in column_lower for keyword in ['vendor', 'manufacturer', 'make']):
            return 'vendor'
        
        if any(keyword in column_lower for keyword in ['model', 'type', 'product']):
            return 'model'
        
        if any(keyword in column_lower for keyword in ['version', 'release', 'build']):
            return 'version'
        
        if any(keyword in column_lower for keyword in ['cpu', 'processor', 'cores']):
            return 'cpu_info'
        
        if any(keyword in column_lower for keyword in ['memory', 'ram', 'mem']):
            return 'memory_info'
        
        if any(keyword in column_lower for keyword in ['disk', 'storage', 'drive']):
            return 'storage_info'
        
        if any(keyword in column_lower for keyword in ['network', 'nic', 'interface']):
            return 'network_info'
        
        if any(keyword in column_lower for keyword in ['vlan', 'subnet', 'segment']):
            return 'network_segment'
        
        if any(keyword in column_lower for keyword in ['patch', 'update', 'hotfix']):
            return 'patch_level'
        
        if any(keyword in column_lower for keyword in ['compliance', 'policy', 'standard']):
            return 'compliance_info'
        
        if any(keyword in column_lower for keyword in ['backup', 'snapshot', 'archive']):
            return 'backup_info'
        
        if any(keyword in column_lower for keyword in ['monitor', 'agent', 'sensor']):
            return 'monitoring_info'
        
        if any(keyword in column_lower for keyword in ['license', 'subscription', 'entitlement']):
            return 'license_info'
        
        return f"custom_{column_lower.replace(' ', '_').replace('-', '_')}"
    
    def _looks_like_ip(self, value: str) -> bool:
        try:
            ipaddress.ip_address(value.strip())
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False
    
    def _looks_like_mac(self, value: str) -> bool:
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})
    
    def _insert_enrichment_observation(self, observation_id: str, entity_id: str, source_table: str,
                                     field_type: str, column: str, value: str, confidence: float,
                                     validation_score: float, semantic_score: float):
        
        temporal_score = 1.0
        network_score = 0.8 if any(keyword in source_table.lower() 
                                 for keyword in ['network', 'firewall', 'dns']) else 0.5
        ml_score = confidence * 0.8
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO entity_observations 
            (observation_id, entity_id, source_table, observation_type, field_name, field_value,
             confidence_score, validation_score, temporal_score, network_score, semantic_score, ml_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observation_id, entity_id, source_table, field_type,
                column, value, confidence, validation_score, temporal_score,
                network_score, semantic_score, ml_score
            ))
    
    def _register_entities_and_observations(self, fingerprints: Dict[str, HostFingerprint], 
                                          entity_links: Dict[str, Set[str]],
                                          all_table_metadata: List[Dict]) -> Dict[str, int]:
        
        entity_clusters = self._build_entity_clusters(entity_links)
        
        stats = {
            'entities_registered': 0,
            'observations_recorded': 0,
            'clusters_created': len(entity_clusters)
        }
        
        for cluster_id, fingerprint_ids in entity_clusters.items():
            primary_fingerprint = self._select_primary_fingerprint(fingerprint_ids, fingerprints)
            
            entity_id = f"entity_{cluster_id}"
            
            self._register_master_entity(entity_id, primary_fingerprint, fingerprint_ids, fingerprints)
            stats['entities_registered'] += 1
        
        return stats
    
    def _build_entity_clusters(self, entity_links: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        visited = set()
        clusters = {}
        cluster_counter = 0
        
        def dfs(node, cluster):
            if node in visited:
                return
            visited.add(node)
            cluster.add(node)
            
            for neighbor in entity_links.get(node, set()):
                dfs(neighbor, cluster)
        
        for node in entity_links:
            if node not in visited:
                cluster = set()
                dfs(node, cluster)
                if cluster:
                    clusters[cluster_counter] = cluster
                    cluster_counter += 1
        
        for fp_id in self.host_linker.fingerprints:
            if fp_id not in visited:
                clusters[cluster_counter] = {fp_id}
                cluster_counter += 1
        
        return clusters
    
    def _select_primary_fingerprint(self, fingerprint_ids: Set[str], 
                                  fingerprints: Dict[str, HostFingerprint]) -> HostFingerprint:
        
        candidates = [(fp_id, fingerprints[fp_id]) for fp_id in fingerprint_ids]
        
        best_fp = max(candidates, key=lambda x: (
            x[1].confidence_score,
            len(x[1].source_tables),
            len(x[1].ip_addresses),
            len(x[1].normalized_hostnames)
        ))
        
        return best_fp[1]
    
    def _register_master_entity(self, entity_id: str, primary_fp: HostFingerprint, 
                              all_fp_ids: Set[str], all_fingerprints: Dict[str, HostFingerprint]):
        
        primary_hostname = next(iter(primary_fp.normalized_hostnames)) if primary_fp.normalized_hostnames else entity_id
        
        fingerprint_data = {
            'all_hostnames': list(primary_fp.normalized_hostnames),
            'all_ips': list(primary_fp.ip_addresses),
            'all_macs': list(primary_fp.mac_addresses),
            'all_domains': list(primary_fp.domain_names),
            'network_segments': list(primary_fp.network_segments),
            'source_tables': list(primary_fp.source_tables)
        }
        
        linked_identities = {fp_id: list(all_fingerprints[fp_id].normalized_hostnames) 
                           for fp_id in all_fp_ids}
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO master_entity_registry 
            (entity_id, primary_hostname, confidence_score, fingerprint_data, linked_identities)
            VALUES (?, ?, ?, ?, ?)
            """, (
                entity_id,
                primary_hostname,
                primary_fp.confidence_score,
                json.dumps(fingerprint_data),
                json.dumps(linked_identities)
            ))
    
    def _build_consolidated_intelligence(self) -> Dict[str, Any]:
        PrettyLogger.info("Building consolidated asset intelligence from ALL DuckDB tables")
        
        # First get all entities
        entities = self.conn.execute("""
        SELECT entity_id, primary_hostname, confidence_score, fingerprint_data, linked_identities
        FROM master_entity_registry
        """).fetchall()
        
        # Get all DuckDB tables for comprehensive enrichment
        all_duckdb_tables = self._get_all_duckdb_tables()
        
        consolidated_count = 0
        
        for entity_id, primary_hostname, confidence_score, fingerprint_data_json, linked_identities_json in entities:
            try:
                fingerprint_data = json.loads(fingerprint_data_json)
                linked_identities = json.loads(linked_identities_json)
                
                # Enrich from ALL DuckDB tables
                comprehensive_data = self._extract_from_all_duckdb_tables(
                    primary_hostname, fingerprint_data, linked_identities, all_duckdb_tables
                )
                
                consolidated_asset = self._build_comprehensive_asset_profile(
                    entity_id, primary_hostname, fingerprint_data, comprehensive_data
                )
                
                if consolidated_asset:
                    self._insert_consolidated_asset(consolidated_asset)
                    consolidated_count += 1
                    
            except Exception as e:
                PrettyLogger.warning(f"Failed to consolidate entity {entity_id}: {e}")
        
        stats = {
            'consolidated_assets': consolidated_count,
            'total_entities': len(entities),
            'duckdb_tables_processed': len(all_duckdb_tables)
        }
        
        PrettyLogger.success(f"Consolidated {consolidated_count} assets from {len(all_duckdb_tables)} DuckDB tables")
        return stats
    
    def _get_all_duckdb_tables(self) -> List[Dict[str, Any]]:
        """Get metadata for all tables in the DuckDB database"""
        try:
            # Get all table names
            tables_query = """
            SELECT table_name, table_schema 
            FROM information_schema.tables 
            WHERE table_type = 'BASE TABLE' 
            AND table_schema NOT IN ('information_schema', 'pg_catalog')
            """
            
            tables = self.conn.execute(tables_query).fetchall()
            
            table_metadata = []
            for table_name, schema_name in tables:
                try:
                    # Get column information for each table
                    columns_query = f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND table_schema = '{schema_name}'
                    ORDER BY ordinal_position
                    """
                    
                    columns = self.conn.execute(columns_query).fetchall()
                    
                    # Get row count
                    count_query = f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
                    row_count = self.conn.execute(count_query).fetchone()[0]
                    
                    if row_count > 0:  # Only process non-empty tables
                        table_metadata.append({
                            'table_name': table_name,
                            'schema_name': schema_name,
                            'full_table_name': f"{schema_name}.{table_name}",
                            'columns': [col_name for col_name, col_type in columns],
                            'row_count': row_count
                        })
                        
                except Exception as e:
                    PrettyLogger.warning(f"Failed to analyze DuckDB table {table_name}: {e}")
                    continue
            
            PrettyLogger.info(f"Found {len(table_metadata)} DuckDB tables to process")
            return table_metadata
            
        except Exception as e:
            PrettyLogger.error(f"Failed to get DuckDB table metadata: {e}")
            return []
    
    def _extract_from_all_duckdb_tables(self, primary_hostname: str, fingerprint_data: Dict, 
                                      linked_identities: Dict, all_tables: List[Dict]) -> Dict[str, List[Dict]]:
        """Extract data from every column in every DuckDB table for this hostname"""
        
        comprehensive_data = defaultdict(list)
        
        # Get all possible hostname variants for this entity
        all_hostnames = set([primary_hostname])
        all_hostnames.update(fingerprint_data.get('all_hostnames', []))
        
        # Add hostnames from linked identities
        for fp_id, hostnames in linked_identities.items():
            all_hostnames.update(hostnames)
        
        # Normalize all hostnames for matching
        normalized_hostnames = set()
        for hostname in all_hostnames:
            if hostname:
                normalized = self.host_linker._normalize_hostname_advanced(hostname)
                if normalized:
                    normalized_hostnames.add(normalized.upper())
                    normalized_hostnames.add(hostname.upper())
        
        PrettyLogger.info(f"Searching for {len(normalized_hostnames)} hostname variants across {len(all_tables)} DuckDB tables")
        
        for table_meta in all_tables:
            table_name = table_meta['full_table_name']
            columns = table_meta['columns']
            
            try:
                # Look for hostname matches in ANY column of this table
                hostname_conditions = []
                for column in columns:
                    for hostname in normalized_hostnames:
                        hostname_conditions.append(f"UPPER(CAST({column} AS VARCHAR)) LIKE '%{hostname}%'")
                
                if not hostname_conditions:
                    continue
                
                # Create query to find rows containing any of our hostnames
                hostname_filter = " OR ".join(hostname_conditions)
                
                query = f"""
                SELECT * 
                FROM {table_name} 
                WHERE ({hostname_filter})
                LIMIT 100
                """
                
                results = self.conn.execute(query).fetchall()
                
                if not results:
                    continue
                
                PrettyLogger.info(f"Found {len(results)} matching rows in {table_name}")
                
                # Extract data from ALL columns for matching rows
                for row in results:
                    for i, column_name in enumerate(columns):
                        if i < len(row) and row[i] is not None:
                            value = str(row[i]).strip()
                            
                            if self._is_valid_enrichment_value(value):
                                field_type = self._determine_field_type_from_name_and_values(column_name, [value])
                                confidence = self._calculate_field_confidence(field_type, value, column_name)
                                
                                comprehensive_data[field_type].append({
                                    'value': value,
                                    'column': column_name,
                                    'table': table_name,
                                    'confidence': confidence,
                                    'source_type': 'duckdb'
                                })
                
            except Exception as e:
                PrettyLogger.warning(f"Failed to extract from DuckDB table {table_name}: {e}")
                continue
        
        total_extractions = sum(len(values) for values in comprehensive_data.values())
        PrettyLogger.success(f"Extracted {total_extractions} data points from DuckDB tables")
        
        return dict(comprehensive_data)
    
    def _build_comprehensive_asset_profile(self, entity_id: str, primary_hostname: str, 
                                         fingerprint_data: Dict, duckdb_data: Dict) -> Optional[Dict]:
        """Build asset profile using both entity observations and DuckDB extractions"""
        
        # Get existing observations from entity_observations table
        observations = self.conn.execute("""
        SELECT observation_type, field_value, confidence_score, validation_score, 
               temporal_score, network_score, semantic_score, ml_score, source_table
        FROM entity_observations 
        WHERE entity_id = ?
        ORDER BY confidence_score DESC, validation_score DESC
        """, (entity_id,)).fetchall()
        
        profile = {
            'asset_id': entity_id,
            'hostname': primary_hostname,
            'fqdn': '',
            'ip_addresses': '',
            'mac_addresses': '',
            'infrastructure_type': '',
            'system_classification': '',
            'operating_system': '',
            'global_region': '',
            'country': '',
            'data_center': '',
            'business_unit': '',
            'cost_center': '',
            'environment': '',
            'criticality_level': '',
            'owner': '',
            'application': '',
            'status': '',
            'serial_number': '',
            'asset_tag': '',
            'vendor': '',
            'model': '',
            'version': '',
            'cpu_info': '',
            'memory_info': '',
            'storage_info': '',
            'network_info': '',
            'network_segment': '',
            'patch_level': '',
            'compliance_info': '',
            'backup_info': '',
            'monitoring_info': '',
            'license_info': '',
            'custom_fields': '',
            'cmdb_presence': False,
            'splunk_visibility': False,
            'chronicle_visibility': False,
            'crowdstrike_coverage': False,
            'tanium_coverage': False,
            'visibility_gap_score': 0.0,
            'data_quality_score': 0.0,
            'intelligence_confidence': 0.0,
            'enrichment_completeness': 0.0,
            'network_connectivity_map': '',
            'source_system_count': 0,
            'total_fields_populated': 0,
            'last_observation': None
        }
        
        # Combine data from entity observations and DuckDB extractions
        field_values = defaultdict(list)
        source_systems = set()
        all_confidence_scores = []
        custom_fields = {}
        
        # Process existing entity observations
        for obs_type, field_value, conf_score, val_score, temp_score, net_score, sem_score, ml_score, source_table in observations:
            if not field_value or str(field_value).strip().upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY']:
                continue
            
            combined_score = (conf_score * 0.4) + (val_score * 0.3) + (temp_score * 0.1) + (net_score * 0.1) + (sem_score * 0.05) + (ml_score * 0.05)
            
            field_values[obs_type].append({
                'value': str(field_value).strip(),
                'confidence': conf_score,
                'combined_score': combined_score,
                'source': source_table,
                'source_type': 'entity_observation'
            })
            
            source_systems.add(source_table)
            all_confidence_scores.append(conf_score)
        
        # Process DuckDB extractions
        for field_type, extractions in duckdb_data.items():
            for extraction in extractions:
                combined_score = extraction['confidence'] * 0.8  # Slightly lower weight for DuckDB extractions
                
                field_values[field_type].append({
                    'value': extraction['value'],
                    'confidence': extraction['confidence'],
                    'combined_score': combined_score,
                    'source': extraction['table'],
                    'source_type': 'duckdb_extraction'
                })
                
                source_systems.add(extraction['table'])
                all_confidence_scores.append(extraction['confidence'])
        
        # Populate profile fields with best values
        for field_type, candidates in field_values.items():
            if not candidates:
                continue
            
            # Sort by combined score and take the best value
            candidates.sort(key=lambda x: x['combined_score'], reverse=True)
            best_value = candidates[0]['value']
            
            # Map to profile fields
            if field_type == 'fqdn':
                profile['fqdn'] = best_value
            elif field_type == 'ip_address':
                unique_ips = list(set([c['value'] for c in candidates[:10] if self._is_valid_ip(c['value'])]))
                profile['ip_addresses'] = ','.join(unique_ips)
            elif field_type == 'mac_address':
                unique_macs = list(set([c['value'] for c in candidates[:5] if self._is_valid_mac(c['value'])]))
                profile['mac_addresses'] = ','.join(unique_macs)
            elif field_type in ['infrastructure_type', 'system_classification', 'operating_system', 
                              'global_region', 'country', 'data_center', 'business_unit', 'cost_center',
                              'environment', 'criticality_level', 'owner', 'application', 'status',
                              'serial_number', 'asset_tag', 'vendor', 'model', 'version', 'cpu_info',
                              'memory_info', 'storage_info', 'network_info', 'network_segment',
                              'patch_level', 'compliance_info', 'backup_info', 'monitoring_info', 'license_info']:
                if field_type == 'global_region':
                    profile['global_region'] = best_value
                else:
                    profile[field_type] = best_value
            elif field_type.startswith('custom_'):
                custom_fields[field_type] = best_value
        
        if custom_fields:
            profile['custom_fields'] = json.dumps(custom_fields)
        
        # Enhance with fingerprint data
        if fingerprint_data.get('all_ips'):
            existing_ips = profile['ip_addresses'].split(',') if profile['ip_addresses'] else []
            all_ips = list(set(existing_ips + fingerprint_data['all_ips']))
            profile['ip_addresses'] = ','.join([ip for ip in all_ips if ip.strip() and self._is_valid_ip(ip)])
        
        if fingerprint_data.get('all_macs'):
            existing_macs = profile['mac_addresses'].split(',') if profile['mac_addresses'] else []
            all_macs = list(set(existing_macs + fingerprint_data['all_macs']))
            profile['mac_addresses'] = ','.join([mac for mac in all_macs if mac.strip() and self._is_valid_mac(mac)])
        
        # Calculate metrics
        source_tables = fingerprint_data.get('source_tables', [])
        all_sources = source_systems.union(set(source_tables))
        profile['source_system_count'] = len(all_sources)
        
        populated_fields = sum(1 for key, value in profile.items() 
                             if key not in ['asset_id', 'source_system_count', 'total_fields_populated', 'last_observation', 'enrichment_timestamp'] 
                             and value and str(value).strip())
        profile['total_fields_populated'] = populated_fields
        
        # Set visibility flags
        for source_table in all_sources:
            source_lower = source_table.lower()
            if any(keyword in source_lower for keyword in ['cmdb', 'asset', 'inventory']):
                profile['cmdb_presence'] = True
            if any(keyword in source_lower for keyword in ['splunk', 'spl', 'log']):
                profile['splunk_visibility'] = True
            if any(keyword in source_lower for keyword in ['chronicle', 'security']):
                profile['chronicle_visibility'] = True
            if any(keyword in source_lower for keyword in ['crowdstrike', 'cs', 'falcon']):
                profile['crowdstrike_coverage'] = True
            if any(keyword in source_lower for keyword in ['tanium', 'tan']):
                profile['tanium_coverage'] = True
        
        # Calculate scores
        if all_confidence_scores:
            profile['intelligence_confidence'] = sum(all_confidence_scores) / len(all_confidence_scores)
        else:
            profile['intelligence_confidence'] = 0.5
        
        profile['data_quality_score'] = self._calculate_data_quality_from_observations(field_values)
        profile['enrichment_completeness'] = self._calculate_comprehensive_enrichment_completeness(profile)
        profile['visibility_gap_score'] = self._calculate_visibility_gap_score(profile)
        
        return profile
    
    def _build_asset_profile(self, entity_id: str, primary_hostname: str, fingerprint_data: Dict) -> Optional[Dict]:
        
        observations = self.conn.execute("""
        SELECT observation_type, field_value, confidence_score, validation_score, 
               temporal_score, network_score, semantic_score, ml_score, source_table
        FROM entity_observations 
        WHERE entity_id = ?
        ORDER BY confidence_score DESC, validation_score DESC
        """, (entity_id,)).fetchall()
        
        profile = {
            'asset_id': entity_id,
            'hostname': primary_hostname,
            'fqdn': '',
            'ip_addresses': '',
            'mac_addresses': '',
            'infrastructure_type': '',
            'system_classification': '',
            'operating_system': '',
            'global_region': '',
            'country': '',
            'data_center': '',
            'business_unit': '',
            'cost_center': '',
            'environment': '',
            'criticality_level': '',
            'owner': '',
            'application': '',
            'status': '',
            'serial_number': '',
            'asset_tag': '',
            'vendor': '',
            'model': '',
            'version': '',
            'cpu_info': '',
            'memory_info': '',
            'storage_info': '',
            'network_info': '',
            'network_segment': '',
            'patch_level': '',
            'compliance_info': '',
            'backup_info': '',
            'monitoring_info': '',
            'license_info': '',
            'custom_fields': '',
            'cmdb_presence': False,
            'splunk_visibility': False,
            'chronicle_visibility': False,
            'crowdstrike_coverage': False,
            'tanium_coverage': False,
            'visibility_gap_score': 0.0,
            'data_quality_score': 0.0,
            'intelligence_confidence': 0.0,
            'enrichment_completeness': 0.0,
            'network_connectivity_map': '',
            'source_system_count': 0,
            'total_fields_populated': 0,
            'last_observation': None
        }
        
        field_values = defaultdict(list)
        source_systems = set()
        all_confidence_scores = []
        custom_fields = {}
        
        for obs_type, field_value, conf_score, val_score, temp_score, net_score, sem_score, ml_score, source_table in observations:
            if not field_value or str(field_value).strip().upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY']:
                continue
            
            combined_score = (conf_score * 0.4) + (val_score * 0.3) + (temp_score * 0.1) + (net_score * 0.1) + (sem_score * 0.05) + (ml_score * 0.05)
            
            field_values[obs_type].append({
                'value': str(field_value).strip(),
                'confidence': conf_score,
                'combined_score': combined_score,
                'source': source_table
            })
            
            source_systems.add(source_table)
            all_confidence_scores.append(conf_score)
        
        for field_type, candidates in field_values.items():
            if not candidates:
                continue
            
            candidates.sort(key=lambda x: x['combined_score'], reverse=True)
            best_value = candidates[0]['value']
            
            if field_type == 'fqdn':
                profile['fqdn'] = best_value
            elif field_type == 'ip_address':
                unique_ips = list(set([c['value'] for c in candidates[:5] if self._is_valid_ip(c['value'])]))
                profile['ip_addresses'] = ','.join(unique_ips)
            elif field_type == 'mac_address':
                unique_macs = list(set([c['value'] for c in candidates[:3] if self._is_valid_mac(c['value'])]))
                profile['mac_addresses'] = ','.join(unique_macs)
            elif field_type == 'infrastructure_type':
                profile['infrastructure_type'] = best_value
            elif field_type == 'system_classification':
                profile['system_classification'] = best_value
            elif field_type == 'operating_system':
                profile['operating_system'] = best_value
            elif field_type == 'region':
                profile['global_region'] = best_value
            elif field_type == 'country':
                profile['country'] = best_value
            elif field_type == 'data_center':
                profile['data_center'] = best_value
            elif field_type == 'business_unit':
                profile['business_unit'] = best_value
            elif field_type == 'cost_center':
                profile['cost_center'] = best_value
            elif field_type == 'environment':
                profile['environment'] = best_value
            elif field_type == 'criticality_level':
                profile['criticality_level'] = best_value
            elif field_type == 'owner':
                profile['owner'] = best_value
            elif field_type == 'application':
                profile['application'] = best_value
            elif field_type == 'status':
                profile['status'] = best_value
            elif field_type == 'serial_number':
                profile['serial_number'] = best_value
            elif field_type == 'asset_tag':
                profile['asset_tag'] = best_value
            elif field_type == 'vendor':
                profile['vendor'] = best_value
            elif field_type == 'model':
                profile['model'] = best_value
            elif field_type == 'version':
                profile['version'] = best_value
            elif field_type == 'cpu_info':
                profile['cpu_info'] = best_value
            elif field_type == 'memory_info':
                profile['memory_info'] = best_value
            elif field_type == 'storage_info':
                profile['storage_info'] = best_value
            elif field_type == 'network_info':
                profile['network_info'] = best_value
            elif field_type == 'network_segment':
                profile['network_segment'] = best_value
            elif field_type == 'patch_level':
                profile['patch_level'] = best_value
            elif field_type == 'compliance_info':
                profile['compliance_info'] = best_value
            elif field_type == 'backup_info':
                profile['backup_info'] = best_value
            elif field_type == 'monitoring_info':
                profile['monitoring_info'] = best_value
            elif field_type == 'license_info':
                profile['license_info'] = best_value
            elif field_type.startswith('custom_'):
                custom_fields[field_type] = best_value
        
        if custom_fields:
            profile['custom_fields'] = json.dumps(custom_fields)
        
        if fingerprint_data.get('all_ips'):
            existing_ips = profile['ip_addresses'].split(',') if profile['ip_addresses'] else []
            all_ips = list(set(existing_ips + fingerprint_data['all_ips']))
            profile['ip_addresses'] = ','.join([ip for ip in all_ips if ip.strip() and self._is_valid_ip(ip)])
        
        if fingerprint_data.get('all_macs'):
            existing_macs = profile['mac_addresses'].split(',') if profile['mac_addresses'] else []
            all_macs = list(set(existing_macs + fingerprint_data['all_macs']))
            profile['mac_addresses'] = ','.join([mac for mac in all_macs if mac.strip() and self._is_valid_mac(mac)])
        
        source_tables = fingerprint_data.get('source_tables', [])
        all_sources = source_systems.union(set(source_tables))
        profile['source_system_count'] = len(all_sources)
        
        populated_fields = sum(1 for key, value in profile.items() 
                             if key not in ['asset_id', 'source_system_count', 'total_fields_populated', 'last_observation', 'enrichment_timestamp'] 
                             and value and str(value).strip())
        profile['total_fields_populated'] = populated_fields
        
        for source_table in all_sources:
            source_lower = source_table.lower()
            if any(keyword in source_lower for keyword in ['cmdb', 'asset', 'inventory']):
                profile['cmdb_presence'] = True
            if any(keyword in source_lower for keyword in ['splunk', 'spl', 'log']):
                profile['splunk_visibility'] = True
            if any(keyword in source_lower for keyword in ['chronicle', 'security']):
                profile['chronicle_visibility'] = True
            if any(keyword in source_lower for keyword in ['crowdstrike', 'cs', 'falcon']):
                profile['crowdstrike_coverage'] = True
            if any(keyword in source_lower for keyword in ['tanium', 'tan']):
                profile['tanium_coverage'] = True
        
        if all_confidence_scores:
            profile['intelligence_confidence'] = sum(all_confidence_scores) / len(all_confidence_scores)
        else:
            profile['intelligence_confidence'] = 0.5
        
        profile['data_quality_score'] = self._calculate_data_quality_from_observations(field_values)
        profile['enrichment_completeness'] = self._calculate_comprehensive_enrichment_completeness(profile)
        profile['visibility_gap_score'] = self._calculate_visibility_gap_score(profile)
        
        return profile
    
    def _calculate_comprehensive_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system', 'fqdn',
            'system_classification', 'owner', 'status'
        ]
        
        populated_critical = sum(1 for field in critical_fields if profile.get(field))
        
        all_enrichment_fields = [
            'fqdn', 'ip_addresses', 'mac_addresses', 'infrastructure_type', 'system_classification',
            'operating_system', 'global_region', 'country', 'data_center', 'business_unit',
            'cost_center', 'environment', 'criticality_level', 'owner', 'application', 'status',
            'serial_number', 'asset_tag', 'vendor', 'model', 'version', 'cpu_info', 'memory_info',
            'storage_info', 'network_info', 'network_segment', 'patch_level', 'compliance_info',
            'backup_info', 'monitoring_info', 'license_info'
        ]
        
        populated_all = sum(1 for field in all_enrichment_fields if profile.get(field))
        
        critical_score = (populated_critical / len(critical_fields)) * 60
        comprehensive_score = (populated_all / len(all_enrichment_fields)) * 40
        
        return critical_score + comprehensive_score
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        try:
            ipaddress.ip_address(ip_str.strip())
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False
    
    def _is_valid_mac(self, mac_str: str) -> bool:
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 50"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
            if dry_run_job.total_bytes_processed > 100 * 1024 * 1024:
                sample_query = f"{base_query} {where_clause} ORDER BY RAND() LIMIT 20"
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            enriched_sample = self._enhance_sample_with_lookups(sample_data, hostname_columns)
            
            return enriched_sample
            
        except Exception:
            return {}
    
    def _enhance_sample_with_lookups(self, sample_data: Dict[str, List[str]], hostname_columns: List[str]) -> Dict[str, List[str]]:
        
        enhanced_data = defaultdict(list)
        
        for column, values in sample_data.items():
            enhanced_data[column] = values
        
        for hostname_col in hostname_columns:
            if hostname_col in sample_data:
                hostnames = sample_data[hostname_col]
                
                for hostname in hostnames:
                    normalized = self._normalize_hostname_for_sample(hostname)
                    if normalized and normalized != hostname:
                        enhanced_data[hostname_col].append(normalized)
                    
                    if '.' in hostname:
                        fqdn_detected = hostname
                        short_hostname = hostname.split('.')[0]
                        enhanced_data['detected_fqdn'] = enhanced_data.get('detected_fqdn', []) + [fqdn_detected]
                        enhanced_data['detected_short_hostname'] = enhanced_data.get('detected_short_hostname', []) + [short_hostname]
                    
                    ip_pattern = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', hostname)
                    if ip_pattern:
                        detected_ip = ip_pattern.group()
                        try:
                            ipaddress.ip_address(detected_ip)
                            enhanced_data['detected_ip'] = enhanced_data.get('detected_ip', []) + [detected_ip]
                        except ValueError:
                            pass
        
        return dict(enhanced_data)
    
    def _normalize_hostname_for_sample(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.strip().upper()
        
        if len(normalized) < 2 or len(normalized) > 253:
            return ""
        
        normalized = re.sub(r'^[^A-Z0-9]+', '', normalized)
        normalized = re.sub(r'[^A-Z0-9\-\.]+
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(),
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()
        ]
        return any(re.match(pattern, mac_str.strip()) for pattern in mac_patterns)
    
    def _looks_like_country(self, value: str) -> bool:
        if len(value) == 2 and value.isupper():
            return True
        
        countries = ['US', 'USA', 'CANADA', 'UK', 'GERMANY', 'FRANCE', 'JAPAN', 'CHINA', 'INDIA', 'BRAZIL']
        return value.upper() in countries
    
    def _looks_like_datacenter(self, value: str) -> bool:
        datacenter_patterns = [
            r'.*DC\d+.*',
            r'.*DATACENTER.*',
            r'.*CENTER.*'
        ]
        return any(re.match(pattern, value.upper()) for pattern in datacenter_patterns)
    
    def _calculate_data_quality_from_observations(self, field_values: Dict) -> float:
        if not field_values:
            return 0.0
        
        quality_scores = []
        for field_type, candidates in field_values.items():
            if candidates:
                avg_confidence = sum(c['confidence'] for c in candidates) / len(candidates)
                quality_scores.append(avg_confidence)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(), '', normalized)
        
        if '.' in normalized:
            parts = normalized.split('.')
            if len(parts) > 1 and all(part.isdigit() for part in parts):
                return ""
            normalized = parts[0]
        
        if len(normalized) < 2:
            return ""
        
        return normalized
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(),
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()
        ]
        return any(re.match(pattern, mac_str.strip()) for pattern in mac_patterns)
    
    def _looks_like_country(self, value: str) -> bool:
        if len(value) == 2 and value.isupper():
            return True
        
        countries = ['US', 'USA', 'CANADA', 'UK', 'GERMANY', 'FRANCE', 'JAPAN', 'CHINA', 'INDIA', 'BRAZIL']
        return value.upper() in countries
    
    def _looks_like_datacenter(self, value: str) -> bool:
        datacenter_patterns = [
            r'.*DC\d+.*',
            r'.*DATACENTER.*',
            r'.*CENTER.*'
        ]
        return any(re.match(pattern, value.upper()) for pattern in datacenter_patterns)
    
    def _calculate_data_quality_from_observations(self, field_values: Dict) -> float:
        if not field_values:
            return 0.0
        
        quality_scores = []
        for field_type, candidates in field_values.items():
            if candidates:
                avg_confidence = sum(c['confidence'] for c in candidates) / len(candidates)
                quality_scores.append(avg_confidence)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(),
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})
    
    def _insert_enrichment_observation(self, observation_id: str, entity_id: str, source_table: str,
                                     field_type: str, column: str, value: str, confidence: float,
                                     validation_score: float, semantic_score: float):
        
        temporal_score = 1.0
        network_score = 0.8 if any(keyword in source_table.lower() 
                                 for keyword in ['network', 'firewall', 'dns']) else 0.5
        ml_score = confidence * 0.8
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO entity_observations 
            (observation_id, entity_id, source_table, observation_type, field_name, field_value,
             confidence_score, validation_score, temporal_score, network_score, semantic_score, ml_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observation_id, entity_id, source_table, field_type,
                column, value, confidence, validation_score, temporal_score,
                network_score, semantic_score, ml_score
            ))
    
    def _register_entities_and_observations(self, fingerprints: Dict[str, HostFingerprint], 
                                          entity_links: Dict[str, Set[str]],
                                          all_table_metadata: List[Dict]) -> Dict[str, int]:
        
        entity_clusters = self._build_entity_clusters(entity_links)
        
        stats = {
            'entities_registered': 0,
            'observations_recorded': 0,
            'clusters_created': len(entity_clusters)
        }
        
        for cluster_id, fingerprint_ids in entity_clusters.items():
            primary_fingerprint = self._select_primary_fingerprint(fingerprint_ids, fingerprints)
            
            entity_id = f"entity_{cluster_id}"
            
            self._register_master_entity(entity_id, primary_fingerprint, fingerprint_ids, fingerprints)
            stats['entities_registered'] += 1
        
        return stats
    
    def _build_entity_clusters(self, entity_links: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        visited = set()
        clusters = {}
        cluster_counter = 0
        
        def dfs(node, cluster):
            if node in visited:
                return
            visited.add(node)
            cluster.add(node)
            
            for neighbor in entity_links.get(node, set()):
                dfs(neighbor, cluster)
        
        for node in entity_links:
            if node not in visited:
                cluster = set()
                dfs(node, cluster)
                if cluster:
                    clusters[cluster_counter] = cluster
                    cluster_counter += 1
        
        for fp_id in self.host_linker.fingerprints:
            if fp_id not in visited:
                clusters[cluster_counter] = {fp_id}
                cluster_counter += 1
        
        return clusters
    
    def _select_primary_fingerprint(self, fingerprint_ids: Set[str], 
                                  fingerprints: Dict[str, HostFingerprint]) -> HostFingerprint:
        
        candidates = [(fp_id, fingerprints[fp_id]) for fp_id in fingerprint_ids]
        
        best_fp = max(candidates, key=lambda x: (
            x[1].confidence_score,
            len(x[1].source_tables),
            len(x[1].ip_addresses),
            len(x[1].normalized_hostnames)
        ))
        
        return best_fp[1]
    
    def _register_master_entity(self, entity_id: str, primary_fp: HostFingerprint, 
                              all_fp_ids: Set[str], all_fingerprints: Dict[str, HostFingerprint]):
        
        primary_hostname = next(iter(primary_fp.normalized_hostnames)) if primary_fp.normalized_hostnames else entity_id
        
        fingerprint_data = {
            'all_hostnames': list(primary_fp.normalized_hostnames),
            'all_ips': list(primary_fp.ip_addresses),
            'all_macs': list(primary_fp.mac_addresses),
            'all_domains': list(primary_fp.domain_names),
            'network_segments': list(primary_fp.network_segments),
            'source_tables': list(primary_fp.source_tables)
        }
        
        linked_identities = {fp_id: list(all_fingerprints[fp_id].normalized_hostnames) 
                           for fp_id in all_fp_ids}
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO master_entity_registry 
            (entity_id, primary_hostname, confidence_score, fingerprint_data, linked_identities)
            VALUES (?, ?, ?, ?, ?)
            """, (
                entity_id,
                primary_hostname,
                primary_fp.confidence_score,
                json.dumps(fingerprint_data),
                json.dumps(linked_identities)
            ))
    
    def _build_consolidated_intelligence(self) -> Dict[str, Any]:
        PrettyLogger.info("Building consolidated asset intelligence")
        
        entities = self.conn.execute("""
        SELECT entity_id, primary_hostname, confidence_score, fingerprint_data, linked_identities
        FROM master_entity_registry
        """).fetchall()
        
        consolidated_count = 0
        
        for entity_id, primary_hostname, confidence_score, fingerprint_data_json, linked_identities_json in entities:
            try:
                fingerprint_data = json.loads(fingerprint_data_json)
                
                consolidated_asset = self._build_asset_profile(
                    entity_id, primary_hostname, fingerprint_data
                )
                
                if consolidated_asset:
                    self._insert_consolidated_asset(consolidated_asset)
                    consolidated_count += 1
                    
            except Exception as e:
                PrettyLogger.warning(f"Failed to consolidate entity {entity_id}: {e}")
        
        stats = {
            'consolidated_assets': consolidated_count,
            'total_entities': len(entities)
        }
        
        PrettyLogger.success(f"Consolidated {consolidated_count} intelligent assets")
        return stats
    
    def _build_asset_profile(self, entity_id: str, primary_hostname: str, fingerprint_data: Dict) -> Optional[Dict]:
        
        observations = self.conn.execute("""
        SELECT observation_type, field_value, confidence_score, validation_score, 
               temporal_score, network_score, semantic_score, ml_score, source_table
        FROM entity_observations 
        WHERE entity_id = ?
        ORDER BY confidence_score DESC, validation_score DESC
        """, (entity_id,)).fetchall()
        
        profile = {
            'asset_id': entity_id,
            'hostname': primary_hostname,
            'fqdn': '',
            'ip_addresses': '',
            'mac_addresses': '',
            'infrastructure_type': '',
            'system_classification': '',
            'operating_system': '',
            'global_region': '',
            'country': '',
            'data_center': '',
            'business_unit': '',
            'cost_center': '',
            'environment': '',
            'criticality_level': '',
            'cmdb_presence': False,
            'splunk_visibility': False,
            'chronicle_visibility': False,
            'crowdstrike_coverage': False,
            'tanium_coverage': False,
            'visibility_gap_score': 0.0,
            'data_quality_score': 0.0,
            'intelligence_confidence': 0.0,
            'enrichment_completeness': 0.0,
            'network_connectivity_map': '',
            'source_system_count': 0,
            'last_observation': None
        }
        
        field_values = defaultdict(list)
        source_systems = set()
        all_confidence_scores = []
        
        for obs_type, field_value, conf_score, val_score, temp_score, net_score, sem_score, ml_score, source_table in observations:
            if not field_value or str(field_value).strip().upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY']:
                continue
            
            combined_score = (conf_score * 0.4) + (val_score * 0.3) + (temp_score * 0.1) + (net_score * 0.1) + (sem_score * 0.05) + (ml_score * 0.05)
            
            field_values[obs_type].append({
                'value': str(field_value).strip(),
                'confidence': conf_score,
                'combined_score': combined_score,
                'source': source_table
            })
            
            source_systems.add(source_table)
            all_confidence_scores.append(conf_score)
        
        for field_type, candidates in field_values.items():
            if not candidates:
                continue
            
            candidates.sort(key=lambda x: x['combined_score'], reverse=True)
            
            if field_type == 'fqdn':
                profile['fqdn'] = candidates[0]['value']
            elif field_type == 'ip_address':
                unique_ips = list(set([c['value'] for c in candidates[:5] if self._is_valid_ip(c['value'])]))
                profile['ip_addresses'] = ','.join(unique_ips)
            elif field_type == 'mac_address':
                unique_macs = list(set([c['value'] for c in candidates[:3] if self._is_valid_mac(c['value'])]))
                profile['mac_addresses'] = ','.join(unique_macs)
            elif field_type == 'infrastructure_type':
                profile['infrastructure_type'] = candidates[0]['value']
            elif field_type == 'operating_system':
                profile['operating_system'] = candidates[0]['value']
            elif field_type == 'region':
                profile['global_region'] = candidates[0]['value']
                if self._looks_like_country(candidates[0]['value']):
                    profile['country'] = candidates[0]['value']
                elif self._looks_like_datacenter(candidates[0]['value']):
                    profile['data_center'] = candidates[0]['value']
            elif field_type == 'business_unit':
                profile['business_unit'] = candidates[0]['value']
            elif field_type == 'environment':
                profile['environment'] = candidates[0]['value']
        
        if fingerprint_data.get('all_ips'):
            existing_ips = profile['ip_addresses'].split(',') if profile['ip_addresses'] else []
            all_ips = list(set(existing_ips + fingerprint_data['all_ips']))
            profile['ip_addresses'] = ','.join([ip for ip in all_ips if ip.strip() and self._is_valid_ip(ip)])
        
        if fingerprint_data.get('all_macs'):
            existing_macs = profile['mac_addresses'].split(',') if profile['mac_addresses'] else []
            all_macs = list(set(existing_macs + fingerprint_data['all_macs']))
            profile['mac_addresses'] = ','.join([mac for mac in all_macs if mac.strip() and self._is_valid_mac(mac)])
        
        source_tables = fingerprint_data.get('source_tables', [])
        all_sources = source_systems.union(set(source_tables))
        profile['source_system_count'] = len(all_sources)
        
        for source_table in all_sources:
            source_lower = source_table.lower()
            if any(keyword in source_lower for keyword in ['cmdb', 'asset', 'inventory']):
                profile['cmdb_presence'] = True
            if any(keyword in source_lower for keyword in ['splunk', 'spl', 'log']):
                profile['splunk_visibility'] = True
            if any(keyword in source_lower for keyword in ['chronicle', 'security']):
                profile['chronicle_visibility'] = True
            if any(keyword in source_lower for keyword in ['crowdstrike', 'cs', 'falcon']):
                profile['crowdstrike_coverage'] = True
            if any(keyword in source_lower for keyword in ['tanium', 'tan']):
                profile['tanium_coverage'] = True
        
        if all_confidence_scores:
            profile['intelligence_confidence'] = sum(all_confidence_scores) / len(all_confidence_scores)
        else:
            profile['intelligence_confidence'] = 0.5
        
        profile['data_quality_score'] = self._calculate_data_quality_from_observations(field_values)
        profile['enrichment_completeness'] = self._calculate_enrichment_completeness(profile)
        profile['visibility_gap_score'] = self._calculate_visibility_gap_score(profile)
        
        return profile
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        try:
            ipaddress.ip_address(ip_str.strip())
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False
    
    def _is_valid_mac(self, mac_str: str) -> bool:
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 50"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
            if dry_run_job.total_bytes_processed > 100 * 1024 * 1024:
                sample_query = f"{base_query} {where_clause} ORDER BY RAND() LIMIT 20"
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            enriched_sample = self._enhance_sample_with_lookups(sample_data, hostname_columns)
            
            return enriched_sample
            
        except Exception:
            return {}
    
    def _enhance_sample_with_lookups(self, sample_data: Dict[str, List[str]], hostname_columns: List[str]) -> Dict[str, List[str]]:
        
        enhanced_data = defaultdict(list)
        
        for column, values in sample_data.items():
            enhanced_data[column] = values
        
        for hostname_col in hostname_columns:
            if hostname_col in sample_data:
                hostnames = sample_data[hostname_col]
                
                for hostname in hostnames:
                    normalized = self._normalize_hostname_for_sample(hostname)
                    if normalized and normalized != hostname:
                        enhanced_data[hostname_col].append(normalized)
                    
                    if '.' in hostname:
                        fqdn_detected = hostname
                        short_hostname = hostname.split('.')[0]
                        enhanced_data['detected_fqdn'] = enhanced_data.get('detected_fqdn', []) + [fqdn_detected]
                        enhanced_data['detected_short_hostname'] = enhanced_data.get('detected_short_hostname', []) + [short_hostname]
                    
                    ip_pattern = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', hostname)
                    if ip_pattern:
                        detected_ip = ip_pattern.group()
                        try:
                            ipaddress.ip_address(detected_ip)
                            enhanced_data['detected_ip'] = enhanced_data.get('detected_ip', []) + [detected_ip]
                        except ValueError:
                            pass
        
        return dict(enhanced_data)
    
    def _normalize_hostname_for_sample(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.strip().upper()
        
        if len(normalized) < 2 or len(normalized) > 253:
            return ""
        
        normalized = re.sub(r'^[^A-Z0-9]+', '', normalized)
        normalized = re.sub(r'[^A-Z0-9\-\.]+
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(),
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()
        ]
        return any(re.match(pattern, mac_str.strip()) for pattern in mac_patterns)
    
    def _looks_like_country(self, value: str) -> bool:
        if len(value) == 2 and value.isupper():
            return True
        
        countries = ['US', 'USA', 'CANADA', 'UK', 'GERMANY', 'FRANCE', 'JAPAN', 'CHINA', 'INDIA', 'BRAZIL']
        return value.upper() in countries
    
    def _looks_like_datacenter(self, value: str) -> bool:
        datacenter_patterns = [
            r'.*DC\d+.*',
            r'.*DATACENTER.*',
            r'.*CENTER.*'
        ]
        return any(re.match(pattern, value.upper()) for pattern in datacenter_patterns)
    
    def _calculate_data_quality_from_observations(self, field_values: Dict) -> float:
        if not field_values:
            return 0.0
        
        quality_scores = []
        for field_type, candidates in field_values.items():
            if candidates:
                avg_confidence = sum(c['confidence'] for c in candidates) / len(candidates)
                quality_scores.append(avg_confidence)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(), '', normalized)
        
        if '.' in normalized:
            parts = normalized.split('.')
            if len(parts) > 1 and all(part.isdigit() for part in parts):
                return ""
            normalized = parts[0]
        
        if len(normalized) < 2:
            return ""
        
        return normalized
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(),
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()
        ]
        return any(re.match(pattern, mac_str.strip()) for pattern in mac_patterns)
    
    def _looks_like_country(self, value: str) -> bool:
        if len(value) == 2 and value.isupper():
            return True
        
        countries = ['US', 'USA', 'CANADA', 'UK', 'GERMANY', 'FRANCE', 'JAPAN', 'CHINA', 'INDIA', 'BRAZIL']
        return value.upper() in countries
    
    def _looks_like_datacenter(self, value: str) -> bool:
        datacenter_patterns = [
            r'.*DC\d+.*',
            r'.*DATACENTER.*',
            r'.*CENTER.*'
        ]
        return any(re.match(pattern, value.upper()) for pattern in datacenter_patterns)
    
    def _calculate_data_quality_from_observations(self, field_values: Dict) -> float:
        if not field_values:
            return 0.0
        
        quality_scores = []
        for field_type, candidates in field_values.items():
            if candidates:
                avg_confidence = sum(c['confidence'] for c in candidates) / len(candidates)
                quality_scores.append(avg_confidence)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()
        ]
        return any(re.match(pattern, value.strip()) for pattern in mac_patterns)
    
    def _is_valid_enrichment_value(self, value: str) -> bool:
        if not value or not value.strip():
            return False
        
        value_upper = value.strip().upper()
        invalid_values = ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY', '', 'NAN', 'UNDEFINED', '0', '-', 'TBD', 'TODO']
        
        if value_upper in invalid_values:
            return False
        
        if len(value.strip()) < 1 or len(value.strip()) > 500:
            return False
        
        return True
    
    def _calculate_field_confidence(self, field_type: str, value: str, column_name: str) -> float:
        confidence = 0.5
        
        if field_type == 'ip_address' and self._looks_like_ip(value):
            confidence = 0.95
        elif field_type == 'mac_address' and self._looks_like_mac(value):
            confidence = 0.95
        elif field_type == 'fqdn' and '.' in value and not value.replace('.', '').isdigit():
            confidence = 0.9
        elif field_type.startswith('custom_'):
            confidence = 0.3
        elif any(keyword in field_type for keyword in ['operating_system', 'environment', 'business_unit']):
            confidence = 0.8
        else:
            confidence = 0.6
        
        column_lower = column_name.lower()
        if any(keyword in column_lower for keyword in field_type.split('_')):
            confidence += 0.1
        
        return min(0.99, confidence)
    
    def _insert_comprehensive_observation(self, observation_id: str, entity_id: str, source_table: str,
                                        field_type: str, column_name: str, value: str, confidence: float, table_meta: Dict):
        
        validation_score = 0.8 if confidence > 0.7 else 0.5
        semantic_score = 0.7 if not field_type.startswith('custom_') else 0.4
        temporal_score = 1.0
        network_score = 0.8 if any(keyword in source_table.lower() 
                                 for keyword in ['network', 'firewall', 'dns', 'dhcp']) else 0.5
        ml_score = confidence * 0.8
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO entity_observations 
            (observation_id, entity_id, source_table, observation_type, field_name, field_value,
             confidence_score, validation_score, temporal_score, network_score, semantic_score, ml_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observation_id, entity_id, source_table, field_type,
                column_name, value, confidence, validation_score, temporal_score,
                network_score, semantic_score, ml_score
            ))
    
    def _insert_enrichment_observation(self, observation_id: str, entity_id: str, source_table: str,
                                     field_type: str, column: str, value: str, confidence: float,
                                     validation_score: float, semantic_score: float):
        
        temporal_score = 1.0
        network_score = 0.8 if any(keyword in source_table.lower() 
                                 for keyword in ['network', 'firewall', 'dns']) else 0.5
        ml_score = confidence * 0.8
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO entity_observations 
            (observation_id, entity_id, source_table, observation_type, field_name, field_value,
             confidence_score, validation_score, temporal_score, network_score, semantic_score, ml_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observation_id, entity_id, source_table, field_type,
                column, value, confidence, validation_score, temporal_score,
                network_score, semantic_score, ml_score
            ))
    
    def _register_entities_and_observations(self, fingerprints: Dict[str, HostFingerprint], 
                                          entity_links: Dict[str, Set[str]],
                                          all_table_metadata: List[Dict]) -> Dict[str, int]:
        
        entity_clusters = self._build_entity_clusters(entity_links)
        
        stats = {
            'entities_registered': 0,
            'observations_recorded': 0,
            'clusters_created': len(entity_clusters)
        }
        
        for cluster_id, fingerprint_ids in entity_clusters.items():
            primary_fingerprint = self._select_primary_fingerprint(fingerprint_ids, fingerprints)
            
            entity_id = f"entity_{cluster_id}"
            
            self._register_master_entity(entity_id, primary_fingerprint, fingerprint_ids, fingerprints)
            stats['entities_registered'] += 1
        
        return stats
    
    def _build_entity_clusters(self, entity_links: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        visited = set()
        clusters = {}
        cluster_counter = 0
        
        def dfs(node, cluster):
            if node in visited:
                return
            visited.add(node)
            cluster.add(node)
            
            for neighbor in entity_links.get(node, set()):
                dfs(neighbor, cluster)
        
        for node in entity_links:
            if node not in visited:
                cluster = set()
                dfs(node, cluster)
                if cluster:
                    clusters[cluster_counter] = cluster
                    cluster_counter += 1
        
        for fp_id in self.host_linker.fingerprints:
            if fp_id not in visited:
                clusters[cluster_counter] = {fp_id}
                cluster_counter += 1
        
        return clusters
    
    def _select_primary_fingerprint(self, fingerprint_ids: Set[str], 
                                  fingerprints: Dict[str, HostFingerprint]) -> HostFingerprint:
        
        candidates = [(fp_id, fingerprints[fp_id]) for fp_id in fingerprint_ids]
        
        best_fp = max(candidates, key=lambda x: (
            x[1].confidence_score,
            len(x[1].source_tables),
            len(x[1].ip_addresses),
            len(x[1].normalized_hostnames)
        ))
        
        return best_fp[1]
    
    def _register_master_entity(self, entity_id: str, primary_fp: HostFingerprint, 
                              all_fp_ids: Set[str], all_fingerprints: Dict[str, HostFingerprint]):
        
        primary_hostname = next(iter(primary_fp.normalized_hostnames)) if primary_fp.normalized_hostnames else entity_id
        
        fingerprint_data = {
            'all_hostnames': list(primary_fp.normalized_hostnames),
            'all_ips': list(primary_fp.ip_addresses),
            'all_macs': list(primary_fp.mac_addresses),
            'all_domains': list(primary_fp.domain_names),
            'network_segments': list(primary_fp.network_segments),
            'source_tables': list(primary_fp.source_tables)
        }
        
        linked_identities = {fp_id: list(all_fingerprints[fp_id].normalized_hostnames) 
                           for fp_id in all_fp_ids}
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO master_entity_registry 
            (entity_id, primary_hostname, confidence_score, fingerprint_data, linked_identities)
            VALUES (?, ?, ?, ?, ?)
            """, (
                entity_id,
                primary_hostname,
                primary_fp.confidence_score,
                json.dumps(fingerprint_data),
                json.dumps(linked_identities)
            ))
    
    def _build_consolidated_intelligence(self) -> Dict[str, Any]:
        PrettyLogger.info("Building consolidated asset intelligence")
        
        entities = self.conn.execute("""
        SELECT entity_id, primary_hostname, confidence_score, fingerprint_data, linked_identities
        FROM master_entity_registry
        """).fetchall()
        
        consolidated_count = 0
        
        for entity_id, primary_hostname, confidence_score, fingerprint_data_json, linked_identities_json in entities:
            try:
                fingerprint_data = json.loads(fingerprint_data_json)
                
                consolidated_asset = self._build_asset_profile(
                    entity_id, primary_hostname, fingerprint_data
                )
                
                if consolidated_asset:
                    self._insert_consolidated_asset(consolidated_asset)
                    consolidated_count += 1
                    
            except Exception as e:
                PrettyLogger.warning(f"Failed to consolidate entity {entity_id}: {e}")
        
        stats = {
            'consolidated_assets': consolidated_count,
            'total_entities': len(entities)
        }
        
        PrettyLogger.success(f"Consolidated {consolidated_count} intelligent assets")
        return stats
    
    def _build_asset_profile(self, entity_id: str, primary_hostname: str, fingerprint_data: Dict) -> Optional[Dict]:
        
        observations = self.conn.execute("""
        SELECT observation_type, field_value, confidence_score, validation_score, 
               temporal_score, network_score, semantic_score, ml_score, source_table
        FROM entity_observations 
        WHERE entity_id = ?
        ORDER BY confidence_score DESC, validation_score DESC
        """, (entity_id,)).fetchall()
        
        profile = {
            'asset_id': entity_id,
            'hostname': primary_hostname,
            'fqdn': '',
            'ip_addresses': '',
            'mac_addresses': '',
            'infrastructure_type': '',
            'system_classification': '',
            'operating_system': '',
            'global_region': '',
            'country': '',
            'data_center': '',
            'business_unit': '',
            'cost_center': '',
            'environment': '',
            'criticality_level': '',
            'cmdb_presence': False,
            'splunk_visibility': False,
            'chronicle_visibility': False,
            'crowdstrike_coverage': False,
            'tanium_coverage': False,
            'visibility_gap_score': 0.0,
            'data_quality_score': 0.0,
            'intelligence_confidence': 0.0,
            'enrichment_completeness': 0.0,
            'network_connectivity_map': '',
            'source_system_count': 0,
            'last_observation': None
        }
        
        field_values = defaultdict(list)
        source_systems = set()
        all_confidence_scores = []
        
        for obs_type, field_value, conf_score, val_score, temp_score, net_score, sem_score, ml_score, source_table in observations:
            if not field_value or str(field_value).strip().upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', 'EMPTY']:
                continue
            
            combined_score = (conf_score * 0.4) + (val_score * 0.3) + (temp_score * 0.1) + (net_score * 0.1) + (sem_score * 0.05) + (ml_score * 0.05)
            
            field_values[obs_type].append({
                'value': str(field_value).strip(),
                'confidence': conf_score,
                'combined_score': combined_score,
                'source': source_table
            })
            
            source_systems.add(source_table)
            all_confidence_scores.append(conf_score)
        
        for field_type, candidates in field_values.items():
            if not candidates:
                continue
            
            candidates.sort(key=lambda x: x['combined_score'], reverse=True)
            
            if field_type == 'fqdn':
                profile['fqdn'] = candidates[0]['value']
            elif field_type == 'ip_address':
                unique_ips = list(set([c['value'] for c in candidates[:5] if self._is_valid_ip(c['value'])]))
                profile['ip_addresses'] = ','.join(unique_ips)
            elif field_type == 'mac_address':
                unique_macs = list(set([c['value'] for c in candidates[:3] if self._is_valid_mac(c['value'])]))
                profile['mac_addresses'] = ','.join(unique_macs)
            elif field_type == 'infrastructure_type':
                profile['infrastructure_type'] = candidates[0]['value']
            elif field_type == 'operating_system':
                profile['operating_system'] = candidates[0]['value']
            elif field_type == 'region':
                profile['global_region'] = candidates[0]['value']
                if self._looks_like_country(candidates[0]['value']):
                    profile['country'] = candidates[0]['value']
                elif self._looks_like_datacenter(candidates[0]['value']):
                    profile['data_center'] = candidates[0]['value']
            elif field_type == 'business_unit':
                profile['business_unit'] = candidates[0]['value']
            elif field_type == 'environment':
                profile['environment'] = candidates[0]['value']
        
        if fingerprint_data.get('all_ips'):
            existing_ips = profile['ip_addresses'].split(',') if profile['ip_addresses'] else []
            all_ips = list(set(existing_ips + fingerprint_data['all_ips']))
            profile['ip_addresses'] = ','.join([ip for ip in all_ips if ip.strip() and self._is_valid_ip(ip)])
        
        if fingerprint_data.get('all_macs'):
            existing_macs = profile['mac_addresses'].split(',') if profile['mac_addresses'] else []
            all_macs = list(set(existing_macs + fingerprint_data['all_macs']))
            profile['mac_addresses'] = ','.join([mac for mac in all_macs if mac.strip() and self._is_valid_mac(mac)])
        
        source_tables = fingerprint_data.get('source_tables', [])
        all_sources = source_systems.union(set(source_tables))
        profile['source_system_count'] = len(all_sources)
        
        for source_table in all_sources:
            source_lower = source_table.lower()
            if any(keyword in source_lower for keyword in ['cmdb', 'asset', 'inventory']):
                profile['cmdb_presence'] = True
            if any(keyword in source_lower for keyword in ['splunk', 'spl', 'log']):
                profile['splunk_visibility'] = True
            if any(keyword in source_lower for keyword in ['chronicle', 'security']):
                profile['chronicle_visibility'] = True
            if any(keyword in source_lower for keyword in ['crowdstrike', 'cs', 'falcon']):
                profile['crowdstrike_coverage'] = True
            if any(keyword in source_lower for keyword in ['tanium', 'tan']):
                profile['tanium_coverage'] = True
        
        if all_confidence_scores:
            profile['intelligence_confidence'] = sum(all_confidence_scores) / len(all_confidence_scores)
        else:
            profile['intelligence_confidence'] = 0.5
        
        profile['data_quality_score'] = self._calculate_data_quality_from_observations(field_values)
        profile['enrichment_completeness'] = self._calculate_enrichment_completeness(profile)
        profile['visibility_gap_score'] = self._calculate_visibility_gap_score(profile)
        
        return profile
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        try:
            ipaddress.ip_address(ip_str.strip())
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False
    
    def _is_valid_mac(self, mac_str: str) -> bool:
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 50"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
            if dry_run_job.total_bytes_processed > 100 * 1024 * 1024:
                sample_query = f"{base_query} {where_clause} ORDER BY RAND() LIMIT 20"
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            enriched_sample = self._enhance_sample_with_lookups(sample_data, hostname_columns)
            
            return enriched_sample
            
        except Exception:
            return {}
    
    def _enhance_sample_with_lookups(self, sample_data: Dict[str, List[str]], hostname_columns: List[str]) -> Dict[str, List[str]]:
        
        enhanced_data = defaultdict(list)
        
        for column, values in sample_data.items():
            enhanced_data[column] = values
        
        for hostname_col in hostname_columns:
            if hostname_col in sample_data:
                hostnames = sample_data[hostname_col]
                
                for hostname in hostnames:
                    normalized = self._normalize_hostname_for_sample(hostname)
                    if normalized and normalized != hostname:
                        enhanced_data[hostname_col].append(normalized)
                    
                    if '.' in hostname:
                        fqdn_detected = hostname
                        short_hostname = hostname.split('.')[0]
                        enhanced_data['detected_fqdn'] = enhanced_data.get('detected_fqdn', []) + [fqdn_detected]
                        enhanced_data['detected_short_hostname'] = enhanced_data.get('detected_short_hostname', []) + [short_hostname]
                    
                    ip_pattern = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', hostname)
                    if ip_pattern:
                        detected_ip = ip_pattern.group()
                        try:
                            ipaddress.ip_address(detected_ip)
                            enhanced_data['detected_ip'] = enhanced_data.get('detected_ip', []) + [detected_ip]
                        except ValueError:
                            pass
        
        return dict(enhanced_data)
    
    def _normalize_hostname_for_sample(self, hostname: str) -> str:
        if not hostname or not isinstance(hostname, str):
            return ""
        
        normalized = hostname.strip().upper()
        
        if len(normalized) < 2 or len(normalized) > 253:
            return ""
        
        normalized = re.sub(r'^[^A-Z0-9]+', '', normalized)
        normalized = re.sub(r'[^A-Z0-9\-\.]+
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(),
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()
        ]
        return any(re.match(pattern, mac_str.strip()) for pattern in mac_patterns)
    
    def _looks_like_country(self, value: str) -> bool:
        if len(value) == 2 and value.isupper():
            return True
        
        countries = ['US', 'USA', 'CANADA', 'UK', 'GERMANY', 'FRANCE', 'JAPAN', 'CHINA', 'INDIA', 'BRAZIL']
        return value.upper() in countries
    
    def _looks_like_datacenter(self, value: str) -> bool:
        datacenter_patterns = [
            r'.*DC\d+.*',
            r'.*DATACENTER.*',
            r'.*CENTER.*'
        ]
        return any(re.match(pattern, value.upper()) for pattern in datacenter_patterns)
    
    def _calculate_data_quality_from_observations(self, field_values: Dict) -> float:
        if not field_values:
            return 0.0
        
        quality_scores = []
        for field_type, candidates in field_values.items():
            if candidates:
                avg_confidence = sum(c['confidence'] for c in candidates) / len(candidates)
                quality_scores.append(avg_confidence)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(), '', normalized)
        
        if '.' in normalized:
            parts = normalized.split('.')
            if len(parts) > 1 and all(part.isdigit() for part in parts):
                return ""
            normalized = parts[0]
        
        if len(normalized) < 2:
            return ""
        
        return normalized
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close(),
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()
        ]
        return any(re.match(pattern, mac_str.strip()) for pattern in mac_patterns)
    
    def _looks_like_country(self, value: str) -> bool:
        if len(value) == 2 and value.isupper():
            return True
        
        countries = ['US', 'USA', 'CANADA', 'UK', 'GERMANY', 'FRANCE', 'JAPAN', 'CHINA', 'INDIA', 'BRAZIL']
        return value.upper() in countries
    
    def _looks_like_datacenter(self, value: str) -> bool:
        datacenter_patterns = [
            r'.*DC\d+.*',
            r'.*DATACENTER.*',
            r'.*CENTER.*'
        ]
        return any(re.match(pattern, value.upper()) for pattern in datacenter_patterns)
    
    def _calculate_data_quality_from_observations(self, field_values: Dict) -> float:
        if not field_values:
            return 0.0
        
        quality_scores = []
        for field_type, candidates in field_values.items():
            if candidates:
                avg_confidence = sum(c['confidence'] for c in candidates) / len(candidates)
                quality_scores.append(avg_confidence)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_enrichment_completeness(self, profile: Dict) -> float:
        critical_fields = [
            'hostname', 'ip_addresses', 'infrastructure_type', 'global_region',
            'business_unit', 'environment', 'operating_system'
        ]
        
        populated_fields = sum(1 for field in critical_fields if profile.get(field))
        return (populated_fields / len(critical_fields)) * 100
    
    def _calculate_visibility_gap_score(self, profile: Dict) -> float:
        visibility_systems = ['cmdb_presence', 'splunk_visibility', 'chronicle_visibility', 'crowdstrike_coverage', 'tanium_coverage']
        visible_systems = sum(1 for system in visibility_systems if profile.get(system, False))
        
        return (visible_systems / len(visibility_systems)) * 100
    
    def _insert_consolidated_asset(self, asset_profile: Dict):
        with self._lock:
            columns = list(asset_profile.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            values = [asset_profile[col] for col in columns]
            
            query = f"""
            INSERT OR REPLACE INTO consolidated_asset_intelligence ({column_names})
            VALUES ({placeholders})
            """
            
            self.conn.execute(query, values)
    
    def get_comprehensive_intelligence_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_entities'] = self.conn.execute("""
                SELECT COUNT(*) FROM master_entity_registry
            """).fetchone()[0]
            
            stats['consolidated_assets'] = self.conn.execute("""
                SELECT COUNT(*) FROM consolidated_asset_intelligence
            """).fetchone()[0]
            
            stats['avg_intelligence_confidence'] = self.conn.execute("""
                SELECT AVG(intelligence_confidence) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_data_quality'] = self.conn.execute("""
                SELECT AVG(data_quality_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            stats['avg_visibility_coverage'] = self.conn.execute("""
                SELECT AVG(visibility_gap_score) FROM consolidated_asset_intelligence
            """).fetchone()[0] or 0.0
            
            visibility_breakdown = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_count
                FROM consolidated_asset_intelligence
            """).fetchone()
            
            if visibility_breakdown:
                stats['visibility_breakdown'] = {
                    'cmdb_coverage': visibility_breakdown[0],
                    'splunk_coverage': visibility_breakdown[1],
                    'chronicle_coverage': visibility_breakdown[2],
                    'crowdstrike_coverage': visibility_breakdown[3],
                    'tanium_coverage': visibility_breakdown[4]
                }
            
            return stats
            
        except Exception as e:
            PrettyLogger.error(f"Failed to generate intelligence stats: {e}")
            return {'error': str(e)}

class SuperIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        
        print("\n" + "="*90)
        print("   ♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Super Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡")
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
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            max_disk_gb=self.config.get('max_disk_gb', 10)
        )
        
        self.progress = ProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.signal_handler = SignalHandler()
        
        self.db_path = self.config.get('database_path', 'ao1_super_intelligent_cmdb.db')
        self.data_fusion = SuperIntelligentDataFusion(self.db_path)
        self.data_fusion.initialize_super_intelligent_linking(self.cache)
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent multi-dimensional discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = self.data_fusion.process_table_metadata_intelligently(all_table_metadata)
            
            cache_optimization = self.cache.optimize()
            PrettyLogger.info(f"Cache optimized: {cache_optimization}")
            
            final_stats = self._generate_super_intelligent_stats(time.time() - start_time, processing_stats)
            analysis_queries = self._create_super_intelligent_queries()
            
            PrettyLogger.success("Super intelligent discovery completed successfully")
            return final_stats, analysis_queries
            
        except Exception as e:
            PrettyLogger.error(f"Super intelligent discovery failed: {e}")
            raise
        finally:
            if hasattr(self.data_fusion, 'conn'):
                self.data_fusion.conn.close()
    
    async def _discover_all_intelligent_tables(self) -> List[Dict[str, Any]]:
        PrettyLogger.info("Discovering intelligent table structures with enhanced analysis")
        
        all_metadata = []
        
        projects_to_analyze = [self.project_id]
        if self.chronicle_client_manager:
            projects_to_analyze.append('chronicle-fisv')
        
        for project_id in projects_to_analyze:
            client_mgr = self.chronicle_client_manager if project_id == 'chronicle-fisv' else self.client_manager
            
            try:
                PrettyLogger.info(f"Analyzing project: {project_id}")
                
                project_metadata = await asyncio.wait_for(
                    self._discover_project_tables(client_mgr, project_id),
                    timeout=600
                )
                
                all_metadata.extend(project_metadata)
                PrettyLogger.success(f"Project {project_id}: {len(project_metadata)} intelligent tables")
                
            except asyncio.TimeoutError:
                PrettyLogger.warning(f"Project {project_id} analysis timed out after 10 minutes")
            except Exception as e:
                PrettyLogger.warning(f"Project {project_id} analysis failed: {e}")
        
        if not all_metadata:
            PrettyLogger.warning("No intelligent tables found - check permissions and data")
            return []
        
        all_metadata.sort(key=lambda x: x.get('data_richness_score', 0), reverse=True)
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _discover_project_tables(self, client_manager: BigQueryClientManager, project_id: str) -> List[Dict[str, Any]]:
        cache_key = f"super_table_metadata:{project_id}"
        cached_metadata = self.cache.get(cache_key)
        
        if cached_metadata:
            PrettyLogger.info(f"Using cached table metadata for {project_id}")
            return cached_metadata
        
        all_metadata = []
        
        try:
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                if not datasets:
                    return []
                
                priority_datasets = self._prioritize_datasets_advanced([d.dataset_id for d in datasets])
                
                for dataset_id in priority_datasets[:10]:
                    try:
                        dataset_ref = client.dataset(dataset_id, project=project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        if not tables:
                            continue
                        
                        for table_ref in tables[:5]:
                            try:
                                metadata = await self._analyze_table_super_intelligently(client, table_ref, project_id)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project {project_id} discovery failed: {e}")
            return []
        
        self.cache.set(cache_key, all_metadata, ttl_hours=8)
        return all_metadata
    
    def _prioritize_datasets_advanced(self, dataset_ids: List[str]) -> List[str]:
        priority_scores = {}
        
        priority_patterns = [
            (r'.*cmdb.*', 1000),
            (r'.*asset.*', 950),
            (r'.*inventory.*', 900),
            (r'.*endpoint.*', 850),
            (r'.*security.*', 800),
            (r'.*crowdstrike.*', 750),
            (r'.*splunk.*', 700),
            (r'.*chronicle.*', 650),
            (r'.*monitoring.*', 600),
            (r'.*infrastructure.*', 550),
            (r'.*network.*', 500),
            (r'.*server.*', 450)
        ]
        
        for dataset_id in dataset_ids:
            score = 0
            dataset_lower = dataset_id.lower()
            
            for pattern, points in priority_patterns:
                if re.match(pattern, dataset_lower):
                    score = max(score, points)
            
            priority_scores[dataset_id] = score
        
        return sorted(dataset_ids, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    async def _analyze_table_super_intelligently(self, client, table_ref, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            if full_table.num_rows and full_table.num_rows > 50000000:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = self._assess_hostname_potential(all_columns)
            if hostname_potential < 0.3:
                return None
            
            sample_data = await self._get_enhanced_sample(client, full_table, project_id)
            
            if not sample_data:
                return None
            
            column_analysis = {}
            for column in all_columns:
                samples = sample_data.get(column, [])
                if samples:
                    analysis = self.matcher.analyze_column_intelligently(column, samples)
                    if analysis:
                        column_analysis[column] = analysis
            
            hostname_analysis = self._find_optimal_hostname_columns(column_analysis, sample_data)
            
            if not hostname_analysis['primary_hostname_column']:
                return None
            
            data_richness = self._calculate_advanced_data_richness(column_analysis, sample_data, full_table)
            
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
            
        except Exception:
            return None
    
    def _assess_hostname_potential(self, columns: List[str]) -> float:
        hostname_indicators = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'name', 'fqdn'
        ]
        
        potential_score = 0.0
        for column in columns:
            column_lower = column.lower()
            for indicator in hostname_indicators:
                if indicator in column_lower:
                    if indicator == 'host' and 'hostname' in column_lower:
                        potential_score += 1.0
                    elif indicator == 'endpoint':
                        potential_score += 0.9
                    elif indicator in ['computer', 'device', 'server']:
                        potential_score += 0.8
                    else:
                        potential_score += 0.5
                    break
        
        return min(1.0, potential_score)
    
    async def _get_enhanced_sample(self, client, table_ref, project_id: str) -> Dict[str, List[str]]:
        try:
            base_query = f"""
            SELECT *
            FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
            """
            
            where_clauses = []
            
            if table_ref.time_partitioning and table_ref.time_partitioning.field:
                partition_field = table_ref.time_partitioning.field
                where_clauses.append(f"`{partition_field}` >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)")
            
            hostname_columns = []
            for field in table_ref.schema:
                field_lower = field.name.lower()
                if any(indicator in field_lower for indicator in ['host', 'endpoint', 'computer', 'device']):
                    hostname_columns.append(field.name)
                    where_clauses.append(f"`{field.name}` IS NOT NULL")
                    where_clauses.append(f"LENGTH(TRIM(CAST(`{field.name}` AS STRING))) >= 2")
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            sample_query = f"{base_query} {where_clause} LIMIT 10"
            
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = client.query(sample_query, job_config=job_config)
            
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
                        if len(str_value) > 0 and len(str_value) < 1000:
                            sample_data[column_name].append(str_value)
            
            return dict(sample_data)
            
        except Exception:
            return {}
    
    def _find_optimal_hostname_columns(self, column_analysis: Dict[str, Tuple], sample_data: Dict[str, List[str]]) -> Dict[str, Any]:
        hostname_candidates = []
        
        for column, analysis in column_analysis.items():
            field_type, confidence, metadata = analysis
            
            if field_type in ['hostname', 'fqdn']:
                samples = sample_data.get(column, [])
                hostname_score = self._calculate_advanced_hostname_quality(samples)
                uniqueness_score = len(set(samples)) / max(len(samples), 1)
                
                final_score = (confidence * 0.4) + (hostname_score * 0.4) + (uniqueness_score * 0.2)
                
                hostname_candidates.append({
                    'column': column,
                    'field_type': field_type,
                    'confidence': confidence,
                    'hostname_score': hostname_score,
                    'uniqueness_score': uniqueness_score,
                    'final_score': final_score,
                    'metadata': metadata
                })
        
        hostname_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            'primary_hostname_column': hostname_candidates[0]['column'] if hostname_candidates else None,
            'all_hostname_candidates': hostname_candidates,
            'hostname_column_count': len(hostname_candidates)
        }
    
    def _calculate_advanced_hostname_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        quality_factors = {}
        
        valid_count = sum(1 for sample in samples if self._is_valid_hostname_advanced(sample))
        quality_factors['validity'] = valid_count / len(samples)
        
        unique_count = len(set(samples))
        quality_factors['uniqueness'] = unique_count / len(samples)
        
        lengths = [len(s) for s in samples if s]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            quality_factors['length_consistency'] = max(0.0, 1.0 - (length_variance / 100))
        else:
            quality_factors['length_consistency'] = 0.0
        
        pattern_scores = []
        for sample in samples:
            pattern_score = self._analyze_hostname_pattern_quality(sample)
            pattern_scores.append(pattern_score)
        
        quality_factors['pattern_quality'] = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.0
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _is_valid_hostname_advanced(self, hostname: str) -> bool:
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 2 or len(hostname) > 253:
            return False
        
        invalid_patterns = [
            r'^[0-9\.\:]+$',
            r'.*@.*',
            r'.*(HTTP|HTTPS|FTP|SMTP).*',
            r'.*(UNKNOWN|NULL|NONE|EMPTY|TEST|EXAMPLE|LOCALHOST).*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, hostname.upper()):
                return False
        
        valid_patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        if any(re.match(pattern, hostname, re.IGNORECASE) for pattern in valid_patterns):
            return True
        
        hostname_indicators = [
            'srv', 'web', 'app', 'db', 'sql', 'win', 'linux', 'server', 
            'host', 'vm', 'node', 'dev', 'prod', 'test', 'stage'
        ]
        
        hostname_lower = hostname.lower()
        return any(indicator in hostname_lower for indicator in hostname_indicators)
    
    def _analyze_hostname_pattern_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        score = 0.0
        
        if re.search(r'[a-zA-Z]', hostname):
            score += 0.3
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if '-' in hostname or '_' in hostname:
            score += 0.1
        
        if '.' in hostname and not hostname.replace('.', '').isdigit():
            score += 0.2
        
        if 3 <= len(hostname) <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_advanced_data_richness(self, column_analysis: Dict, sample_data: Dict, table_info) -> float:
        if not column_analysis:
            return 0.0
        
        richness_factors = {}
        
        field_type_diversity = len(set(field_type for field_type, _, _ in column_analysis.values() if field_type))
        max_possible_types = 10
        richness_factors['field_diversity'] = field_type_diversity / max_possible_types
        
        high_confidence_fields = sum(1 for _, conf, _ in column_analysis.values() if conf > 0.7)
        richness_factors['confidence_quality'] = high_confidence_fields / len(column_analysis)
        
        data_completeness = self._calculate_data_completeness(sample_data)
        richness_factors['data_completeness'] = data_completeness
        
        table_size_factor = min(1.0, (table_info.num_rows or 0) / 100000)
        richness_factors['table_size_factor'] = table_size_factor
        
        return sum(richness_factors.values()) / len(richness_factors)
    
    def _calculate_data_completeness(self, sample_data: Dict[str, List[str]]) -> float:
        if not sample_data:
            return 0.0
        
        total_cells = sum(len(samples) for samples in sample_data.values())
        filled_cells = sum(
            len([s for s in samples if s and str(s).strip() and str(s).strip().upper() not in ['NULL', 'N/A', 'UNKNOWN']])
            for samples in sample_data.values()
        )
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_super_intelligent_stats(self, processing_time: float, processing_stats: Dict) -> Dict[str, Any]:
        intelligence_stats = self.data_fusion.get_comprehensive_intelligence_stats()
        cache_stats = self.cache.get_stats()
        
        return {
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'super_intelligent_multi_dimensional_fusion',
            'processing_stats': processing_stats,
            'intelligence_stats': intelligence_stats,
            'cache_performance': cache_stats,
            'system_capabilities': {
                'ml_entity_matching': True,
                'network_topology_analysis': True,
                'semantic_pattern_learning': True,
                'cross_table_correlation': True,
                'temporal_analysis': True,
                'advanced_fingerprinting': True
            }
        }
    
    def _create_super_intelligent_queries(self) -> Dict[str, str]:
        return {
            'super_intelligent_asset_overview': """
            SELECT 
                asset_id, hostname, fqdn, ip_addresses, infrastructure_type, 
                global_region, business_unit, environment, operating_system,
                cmdb_presence, splunk_visibility, chronicle_visibility, 
                crowdstrike_coverage, tanium_coverage,
                visibility_gap_score, data_quality_score, intelligence_confidence,
                enrichment_completeness, source_system_count
            FROM consolidated_asset_intelligence 
            ORDER BY intelligence_confidence DESC, data_quality_score DESC;
            """,
            
            'intelligence_quality_distribution': """
            SELECT 
                CASE 
                    WHEN intelligence_confidence >= 0.95 THEN 'Exceptional Intelligence (95%+)'
                    WHEN intelligence_confidence >= 0.85 THEN 'Excellent Intelligence (85-94%)'
                    WHEN intelligence_confidence >= 0.75 THEN 'High Intelligence (75-84%)'
                    WHEN intelligence_confidence >= 0.60 THEN 'Good Intelligence (60-74%)'
                    WHEN intelligence_confidence >= 0.40 THEN 'Fair Intelligence (40-59%)'
                    ELSE 'Low Intelligence (<40%)'
                END as intelligence_tier,
                COUNT(*) as asset_count,
                ROUND(AVG(intelligence_confidence), 4) as avg_intelligence,
                ROUND(AVG(data_quality_score), 4) as avg_quality,
                ROUND(AVG(visibility_gap_score), 4) as avg_visibility,
                ROUND(AVG(enrichment_completeness), 4) as avg_completeness
            FROM consolidated_asset_intelligence
            GROUP BY intelligence_tier
            ORDER BY avg_intelligence DESC;
            """,
            
            'comprehensive_visibility_analysis': """
            SELECT 
                business_unit,
                environment,
                infrastructure_type,
                COUNT(*) as total_assets,
                SUM(CASE WHEN cmdb_presence THEN 1 ELSE 0 END) as cmdb_coverage,
                SUM(CASE WHEN splunk_visibility THEN 1 ELSE 0 END) as splunk_coverage,
                SUM(CASE WHEN chronicle_visibility THEN 1 ELSE 0 END) as chronicle_coverage,
                SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                ROUND(AVG(visibility_gap_score), 2) as avg_visibility_score,
                ROUND(AVG(intelligence_confidence), 2) as avg_intelligence
            FROM consolidated_asset_intelligence
            WHERE business_unit IS NOT NULL AND environment IS NOT NULL
            GROUP BY business_unit, environment, infrastructure_type
            ORDER BY total_assets DESC;
            """,
            
            'entity_linking_effectiveness': """
            SELECT 
                primary_hostname,
                confidence_score,
                fingerprint_data,
                linked_identities
            FROM master_entity_registry
            WHERE confidence_score > 0.8
            ORDER BY confidence_score DESC;
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()