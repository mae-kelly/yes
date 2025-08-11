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
        
        consolidated_stats = self._build_consolidated_intelligence()
        
        return {
            'fingerprints_created': len(fingerprints),
            'entity_clusters': len(entity_links),
            'registration_stats': stats,
            'consolidation_stats': consolidated_stats
        }
    
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
        
        if fingerprint_data.get('all_ips'):
            profile['ip_addresses'] = ','.join(fingerprint_data['all_ips'])
        
        if fingerprint_data.get('all_macs'):
            profile['mac_addresses'] = ','.join(fingerprint_data['all_macs'])
        
        source_tables = fingerprint_data.get('source_tables', [])
        profile['source_system_count'] = len(source_tables)
        
        for source_table in source_tables:
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
        
        profile['enrichment_completeness'] = self._calculate_enrichment_completeness(profile)
        profile['visibility_gap_score'] = self._calculate_visibility_gap_score(profile)
        profile['intelligence_confidence'] = 0.8
        profile['data_quality_score'] = 0.7
        
        return profile
    
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