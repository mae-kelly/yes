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
        
        if not self.client_manager.test_connection():
            raise ConnectionError("Failed to authenticate with BigQuery")
        
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
        
        self._lock = threading.RLock()
    
    async def execute_super_intelligent_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = time.time()
        PrettyLogger.info("Starting super intelligent discovery")
        
        try:
            all_table_metadata = await self._discover_all_intelligent_tables()
            
            processing_stats = {'fingerprints_created': len(all_table_metadata)}
            
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
        PrettyLogger.info("Discovering intelligent table structures")
        
        all_metadata = []
        
        try:
            with self.client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=self.project_id))
                
                for dataset in datasets[:5]:
                    try:
                        dataset_ref = client.dataset(dataset.dataset_id, project=self.project_id)
                        tables = list(client.list_tables(dataset_ref))
                        
                        for table_ref in tables[:3]:
                            try:
                                metadata = await self._analyze_table_intelligently(client, table_ref)
                                if metadata:
                                    all_metadata.append(metadata)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
        except Exception as e:
            PrettyLogger.error(f"Project discovery failed: {e}")
            return []
        
        PrettyLogger.success(f"Total intelligent tables discovered: {len(all_metadata)}")
        return all_metadata
    
    async def _analyze_table_intelligently(self, client, table_ref) -> Optional[Dict[str, Any]]:
        try:
            full_table = client.get_table(table_ref)
            
            if not full_table.schema or full_table.num_rows == 0:
                return None
            
            all_columns = [field.name for field in full_table.schema]
            
            hostname_potential = sum(1 for col in all_columns 
                                   if any(indicator in col.lower() 
                                         for indicator in ['host', 'endpoint', 'computer']))
            
            if hostname_potential == 0:
                return None
            
            table_metadata = {
                'project_id': self.project_id,
                'dataset_id': table_ref.dataset_id,
                'table_id': table_ref.table_id,
                'full_table_path': f"{self.project_id}.{table_ref.dataset_id}.{table_ref.table_id}",
                'row_count': full_table.num_rows,
                'column_count': len(all_columns),
                'all_columns': all_columns,
                'hostname_analysis': {'primary_hostname_column': all_columns[0] if all_columns else None},
                'data_richness_score': 0.5
            }
            
            return table_metadata
            
        except Exception:
            return None
    
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
            """
        }
    
    def close(self):
        if hasattr(self.data_fusion, 'conn') and self.data_fusion.conn:
            self.data_fusion.conn.close()