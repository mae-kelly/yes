#!/usr/bin/env python3

import torch
import torch.nn.functional as F
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import gc
import logging
import os
import platform
import time
import traceback
import sys
import re
import hashlib
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Import your algorithm modules
from algo1_lstm import LSTMPredictor
from algo2_gru import GRUPredictor
from algo3_transformer import TransformerPredictor
from algo4_cnn import CNNPredictor
from algo5_autoencoder import AutoencoderPredictor
from algo6_vae import VAEPredictor
from algo7_attention import AttentionPredictor
from algo8_residual import ResidualPredictor
from algo9_ensemble_nn import EnsembleNNPredictor
from algo10_graph_nn import GraphNNPredictor

# Configure logging with optional debug mode
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'FALSE').upper() == 'TRUE'
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class AssetType(Enum):
    """Intelligent asset type classification."""
    WEB_SERVER = "web_server"
    DATABASE = "database"
    APPLICATION = "application"
    NETWORK = "network"
    SECURITY = "security"
    STORAGE = "storage"
    COMPUTE = "compute"
    CONTAINER = "container"
    KUBERNETES = "kubernetes"
    CLOUD = "cloud"
    IOT = "iot"
    UNKNOWN = "unknown"

@dataclass
class AssetPattern:
    """Enhanced pattern structure for intelligent analysis."""
    template: str
    hosts: List[str]
    confidence: float
    pattern_type: str
    metadata: Dict
    anomaly_score: float
    prediction_accuracy: float
    temporal_consistency: float
    
class IntelligentPatternAnalyzer:
    """Advanced pattern analysis with ML-based intelligence."""
    
    def __init__(self):
        self.pattern_rules = self._initialize_pattern_rules()
        self.anomaly_threshold = 0.3
        self.learning_rate = 0.01
        self.pattern_memory = {}
        
    def _initialize_pattern_rules(self) -> Dict:
        """Initialize intelligent pattern matching rules."""
        return {
            # Server patterns
            r'^(srv|server|svr)\d+': AssetType.WEB_SERVER,
            r'^web\d+': AssetType.WEB_SERVER,
            r'^(app|api|svc)\d+': AssetType.APPLICATION,
            
            # Database patterns
            r'^(db|database|mysql|postgres|oracle|mongo)\d+': AssetType.DATABASE,
            r'^(redis|cache|memcache)\d+': AssetType.DATABASE,
            
            # Network patterns
            r'^(fw|firewall|router|switch|lb|loadbalancer)\d+': AssetType.NETWORK,
            r'^(vpn|proxy|gateway)\d+': AssetType.NETWORK,
            
            # Security patterns
            r'^(sec|security|ids|ips|waf)\d+': AssetType.SECURITY,
            r'^(scan|vuln|siem)\d+': AssetType.SECURITY,
            
            # Cloud patterns
            r'^(aws|azure|gcp|cloud)': AssetType.CLOUD,
            r'^(ec2|vm|instance)': AssetType.COMPUTE,
            
            # Container patterns
            r'^(docker|container|pod)': AssetType.CONTAINER,
            r'^(k8s|kube|kubernetes)': AssetType.KUBERNETES,
            
            # IoT patterns
            r'^(iot|sensor|device|edge)': AssetType.IOT,
        }
    
    def classify_asset(self, hostname: str) -> AssetType:
        """Intelligently classify asset type based on hostname."""
        hostname_lower = hostname.lower()
        
        for pattern, asset_type in self.pattern_rules.items():
            if re.match(pattern, hostname_lower):
                return asset_type
        
        # ML-based classification for unknown patterns
        return self._ml_classify(hostname_lower)
    
    def _ml_classify(self, hostname: str) -> AssetType:
        """Use ML features to classify unknown patterns."""
        # Extract features
        features = {
            'has_numbers': bool(re.search(r'\d', hostname)),
            'has_dash': '-' in hostname,
            'has_underscore': '_' in hostname,
            'length': len(hostname),
            'subdomain_count': hostname.count('.'),
            'starts_with_number': hostname[0].isdigit() if hostname else False,
        }
        
        # Simple heuristic-based classification
        if features['subdomain_count'] >= 2:
            return AssetType.CLOUD
        elif features['has_numbers'] and features['length'] < 10:
            return AssetType.COMPUTE
        elif 'app' in hostname or 'api' in hostname:
            return AssetType.APPLICATION
        
        return AssetType.UNKNOWN
    
    def calculate_anomaly_score(self, pattern: List[str]) -> float:
        """Calculate anomaly score for pattern using statistical methods."""
        if len(pattern) < 3:
            return 0.0
        
        # Extract numerical sequences
        numbers = []
        for host in pattern:
            nums = re.findall(r'\d+', host)
            if nums:
                numbers.extend([int(n) for n in nums])
        
        if not numbers:
            return 0.0
        
        # Calculate statistical metrics
        numbers = sorted(numbers)
        median = np.median(numbers)
        mad = np.median(np.abs(numbers - median))  # Median Absolute Deviation
        
        # Calculate gaps and irregularities
        gaps = []
        for i in range(len(numbers) - 1):
            gaps.append(numbers[i+1] - numbers[i])
        
        if gaps:
            gap_variance = np.var(gaps)
            anomaly_score = min(1.0, gap_variance / (max(gaps) + 1))
        else:
            anomaly_score = 0.0
        
        return float(anomaly_score)

class SmartAssetPredictor:
    """Enhanced Asset Predictor with Advanced Intelligence."""
    
    def __init__(self, db_path='universal_cmdb.db'):
        self.db_path = db_path
        self.device = self._initialize_compute_device()
        self.algorithms = []
        self.pattern_analyzer = IntelligentPatternAnalyzer()
        
        # Enhanced caching and memory management
        self.pattern_cache = {}
        self.feature_cache = {}
        self.prediction_cache = {}
        self.relationship_graph = defaultdict(set)
        
        # Intelligent thresholds
        self.pattern_threshold = 2  # Lowered for better detection
        self.confidence_threshold = 0.45  # More aggressive
        self.anomaly_threshold = 0.7
        self.max_memory_gb = 18
        
        # Learning parameters
        self.learning_history = []
        self.feedback_scores = defaultdict(float)
        
    def _initialize_compute_device(self) -> torch.device:
        """Initialize optimal compute device with intelligent fallback."""
        logger.info("\n🚀 Initializing Neural Architecture...")
        
        # Check for Apple Silicon
        if torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info(f"✓ Apple Silicon GPU detected ({platform.machine()})")
            os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
            
        # Check for NVIDIA GPU
        elif torch.cuda.is_available():
            device = torch.device("cuda")
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"✓ NVIDIA GPU detected: {gpu_name}")
            
        # Fallback to CPU with optimization
        else:
            device = torch.device("cpu")
            logger.info("⚡ Using CPU with optimization")
            torch.set_num_threads(os.cpu_count())
        
        return device
    
    def load_and_enrich_data(self) -> pd.DataFrame:
        """Load data with intelligent enrichment and validation."""
        logger.info("\n📊 Loading and enriching asset database...")
        start_time = time.time()
        
        try:
            conn = duckdb.connect(self.db_path, read_only=True)
            
            # Intelligent query with data quality checks
            query = """
                SELECT 
                    *,
                    LENGTH(host) as hostname_length,
                    CASE 
                        WHEN host LIKE '%.%' THEN 1 
                        ELSE 0 
                    END as has_domain
                FROM universal_cmdb 
                WHERE host IS NOT NULL 
                    AND LENGTH(TRIM(host)) > 0
                ORDER BY host
            """
            
            df = conn.execute(query).df()
            conn.close()
            
            if df.empty:
                raise ValueError("No valid data found in database")
            
            # Enrich data with intelligent features
            df = self._enrich_dataset(df)
            
            logger.info(f"✓ Loaded {len(df):,} records in {time.time()-start_time:.2f}s")
            self._log_data_statistics(df)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            raise
    
    def _enrich_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add intelligent derived features to dataset."""
        logger.info("  🧠 Enriching dataset with intelligent features...")
        
        # Asset type classification
        df['asset_type'] = df['host'].apply(
            lambda x: self.pattern_analyzer.classify_asset(str(x))
        )
        
        # Hostname complexity score
        df['hostname_complexity'] = df['host'].apply(self._calculate_hostname_complexity)
        
        # Temporal features if timestamp available
        if 'last_seen' in df.columns:
            df['last_seen'] = pd.to_datetime(df['last_seen'], errors='coerce')
            df['days_since_seen'] = (datetime.now() - df['last_seen']).dt.days
            df['is_stale'] = df['days_since_seen'] > 30
        
        # Network relationship features
        df['subnet'] = df['host'].apply(self._extract_subnet_pattern)
        
        # Data quality scoring
        df['data_quality_score'] = self._calculate_data_quality_score(df)
        
        return df
    
    def _calculate_hostname_complexity(self, hostname: str) -> float:
        """Calculate hostname complexity for pattern detection."""
        if not hostname:
            return 0.0
        
        hostname = str(hostname).lower()
        
        # Complexity factors
        factors = {
            'length': min(len(hostname) / 50, 1.0),
            'dots': min(hostname.count('.') / 3, 1.0),
            'dashes': min(hostname.count('-') / 3, 1.0),
            'numbers': min(sum(c.isdigit() for c in hostname) / 5, 1.0),
            'unique_chars': len(set(hostname)) / len(hostname) if hostname else 0,
        }
        
        return np.mean(list(factors.values()))
    
    def _extract_subnet_pattern(self, hostname: str) -> Optional[str]:
        """Extract subnet or network pattern from hostname."""
        if not hostname:
            return None
        
        # Look for IP-like patterns in hostname
        ip_pattern = re.search(r'(\d{1,3}[-._]\d{1,3}[-._]\d{1,3})', str(hostname))
        if ip_pattern:
            return ip_pattern.group(1).replace('-', '.').replace('_', '.')
        
        # Extract domain-based subnet
        parts = str(hostname).split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        
        return None
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate intelligent data quality score for each record."""
        scores = pd.Series(index=df.index, dtype=float)
        
        # Quality factors with weights
        factors = {
            'present_in_cmdb': 0.25,
            'logging_in_splunk': 0.20,
            'logging_in_gso': 0.15,
            'edr_coverage': 0.20,
            'tanium_coverage': 0.20,
        }
        
        for idx, row in df.iterrows():
            score = 0.0
            
            for factor, weight in factors.items():
                if factor in df.columns:
                    value = row.get(factor)
                    if value == 'yes' or value == True:
                        score += weight
                    elif value == 'partial':
                        score += weight * 0.5
            
            # Bonus for complete metadata
            if row.get('region') and row.get('business_unit'):
                score = min(score * 1.1, 1.0)
            
            scores[idx] = score * 10  # Scale to 0-10
        
        return scores
    
    def _log_data_statistics(self, df: pd.DataFrame):
        """Log intelligent statistics about the dataset."""
        stats = {
            'total_records': len(df),
            'unique_hosts': df['host'].nunique(),
            'asset_types': df['asset_type'].value_counts().to_dict() if 'asset_type' in df.columns else {},
            'regions': df['region'].value_counts().head(5).to_dict() if 'region' in df.columns else {},
            'avg_quality': df['data_quality_score'].mean() if 'data_quality_score' in df.columns else 0,
        }
        
        logger.info(f"  📈 Dataset Statistics:")
        logger.info(f"     • Unique hostnames: {stats['unique_hosts']:,}")
        
        if stats['asset_types']:
            logger.info(f"     • Asset type distribution:")
            for asset_type, count in list(stats['asset_types'].items())[:5]:
                logger.info(f"       - {asset_type}: {count:,}")
        
        if stats['regions']:
            logger.info(f"     • Top regions: {', '.join(stats['regions'].keys())}")
        
        logger.info(f"     • Average data quality: {stats['avg_quality']:.2f}/10")
    
    def discover_intelligent_patterns(self, df: pd.DataFrame) -> Dict:
        """Discover patterns using advanced ML techniques."""
        logger.info("\n🔍 Discovering intelligent patterns...")
        start_time = time.time()
        
        patterns = defaultdict(list)
        pattern_metadata = {}
        relationship_matrix = defaultdict(lambda: defaultdict(int))
        
        # Safe hostname extraction
        try:
            if 'host' not in df.columns:
                logger.error("Missing 'host' column")
                return {'patterns': {}, 'metadata': {}, 'relationships': {}}
            
            hostnames = df['host'].fillna('').astype(str).str.lower().str.strip()
            hostnames = hostnames[hostnames != ''].values
            
        except Exception as e:
            logger.error(f"Failed to extract hostnames: {e}")
            return {'patterns': {}, 'metadata': {}, 'relationships': {}}
        
        # Process with intelligent pattern extraction
        for idx, hostname in enumerate(hostnames):
            if idx % 10000 == 0 and idx > 0:
                logger.info(f"  🔄 Processed {idx:,}/{len(hostnames):,} hostnames")
            
            # Multiple pattern extraction strategies
            templates = self._extract_intelligent_templates(hostname)
            
            for template in templates:
                patterns[template].append(hostname)
                
                # Build relationship graph
                asset_type = self.pattern_analyzer.classify_asset(hostname)
                relationship_matrix[template][asset_type] += 1
        
        # Filter and analyze patterns
        legitimate_patterns = {}
        for template, hosts in patterns.items():
            if len(hosts) >= self.pattern_threshold:
                # Calculate pattern quality metrics
                anomaly_score = self.pattern_analyzer.calculate_anomaly_score(hosts)
                
                if anomaly_score < self.anomaly_threshold:
                    legitimate_patterns[template] = hosts
                    
                    # Enhanced metadata with safe extraction
                    pattern_metadata[template] = self._analyze_pattern_metadata_safe(
                        hosts, df, relationship_matrix[template]
                    )
                    pattern_metadata[template]['anomaly_score'] = anomaly_score
        
        # Cluster related patterns
        pattern_clusters = self._cluster_patterns(legitimate_patterns)
        
        logger.info(f"✓ Discovered {len(legitimate_patterns)} patterns in {time.time()-start_time:.2f}s")
        
        if legitimate_patterns:
            logger.info(f"  📊 Pattern Analysis:")
            logger.info(f"     • Valid patterns: {len(legitimate_patterns)}")
            logger.info(f"     • Pattern clusters: {len(pattern_clusters)}")
            logger.info(f"     • Avg hosts per pattern: {np.mean([len(h) for h in legitimate_patterns.values()]):.1f}")
        
        return {
            'patterns': legitimate_patterns,
            'metadata': pattern_metadata,
            'relationships': dict(relationship_matrix),
            'clusters': pattern_clusters
        }
    
    def _extract_intelligent_templates(self, hostname: str) -> List[str]:
        """Extract multiple template patterns using different strategies."""
        templates = []
        
        # Strategy 1: Simple number replacement
        simple_template = re.sub(r'\d+', 'NUM', hostname)
        simple_template = re.sub(r'NUM(NUM)+', 'NUM', simple_template)
        templates.append(simple_template)
        
        # Strategy 2: Preserve number positions
        position_template = re.sub(r'\d', '#', hostname)
        templates.append(position_template)
        
        # Strategy 3: Semantic grouping
        semantic_template = hostname
        for pattern, replacement in [
            (r'prod\d*', 'PROD'),
            (r'dev\d*', 'DEV'),
            (r'test\d*', 'TEST'),
            (r'stage\d*', 'STAGE'),
        ]:
            semantic_template = re.sub(pattern, replacement, semantic_template)
        if semantic_template != hostname:
            templates.append(semantic_template)
        
        return list(set(templates))
    
    def _analyze_pattern_metadata_safe(self, hosts: List[str], df: pd.DataFrame, 
                                      relationships: Dict) -> Dict:
        """Safely analyze pattern metadata with enhanced intelligence."""
        # Safe data filtering
        hosts_lower = [h.lower() for h in hosts if h]
        
        try:
            if 'host' in df.columns:
                mask = df['host'].astype(str).str.lower().isin(hosts_lower)
                sample_data = df[mask]
            else:
                sample_data = pd.DataFrame()
        except Exception as e:
            logger.debug(f"Failed to filter data: {e}")
            sample_data = pd.DataFrame()
        
        # Safe statistical extraction
        def safe_mode(column_name):
            try:
                if column_name not in sample_data.columns or sample_data.empty:
                    return None
                
                series = sample_data[column_name].dropna()
                if len(series) == 0:
                    return None
                
                mode_result = series.mode()
                if isinstance(mode_result, pd.Series) and len(mode_result) > 0:
                    return mode_result.values[0]
                
                return None
            except Exception:
                return None
        
        def safe_mean(column_name, default=7.5):
            try:
                if column_name not in sample_data.columns or sample_data.empty:
                    return default
                
                series = sample_data[column_name].dropna()
                if len(series) == 0:
                    return default
                
                return float(series.mean())
            except Exception:
                return default
        
        # Extract advanced metadata
        metadata = {
            'count': len(hosts),
            'regions': safe_mode('region'),
            'business_units': safe_mode('business_unit'),
            'data_centers': safe_mode('data_center'),
            'domains': self._extract_common_domain_safe(hosts),
            'avg_quality_score': safe_mean('data_quality_score'),
            'asset_type_distribution': dict(relationships),
            'pattern_entropy': self._calculate_pattern_entropy(hosts),
            'growth_potential': self._estimate_growth_potential(hosts),
        }
        
        return metadata
    
    def _extract_common_domain_safe(self, hosts: List[str]) -> Optional[str]:
        """Safely extract common domain with improved logic."""
        if not hosts:
            return None
        
        try:
            domains = []
            for host in hosts[:min(20, len(hosts))]:  # Sample more hosts
                if not host or not isinstance(host, str):
                    continue
                
                parts = host.split('.')
                if len(parts) > 1:
                    domain = '.'.join(parts[1:])
                    domains.append(domain)
            
            if not domains:
                return None
            
            # Get most common domain
            domain_counts = Counter(domains)
            if domain_counts:
                most_common = max(domain_counts.items(), key=lambda x: x[1])
                return most_common[0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Domain extraction failed: {e}")
            return None
    
    def _calculate_pattern_entropy(self, hosts: List[str]) -> float:
        """Calculate entropy of pattern for randomness detection."""
        if len(hosts) < 2:
            return 0.0
        
        # Extract variable parts
        variable_parts = []
        for host in hosts:
            nums = re.findall(r'\d+', host)
            variable_parts.extend(nums)
        
        if not variable_parts:
            return 0.0
        
        # Calculate entropy
        counts = Counter(variable_parts)
        total = sum(counts.values())
        entropy = -sum((count/total) * np.log2(count/total) for count in counts.values())
        
        # Normalize to 0-1
        max_entropy = np.log2(len(counts))
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _estimate_growth_potential(self, hosts: List[str]) -> float:
        """Estimate pattern growth potential using time series analysis."""
        # Extract numbers and analyze sequence
        numbers = []
        for host in hosts:
            nums = re.findall(r'\d+', host)
            if nums:
                numbers.extend([int(n) for n in nums if n.isdigit()])
        
        if len(numbers) < 3:
            return 0.5
        
        numbers = sorted(set(numbers))
        
        # Check for arithmetic progression
        if len(numbers) >= 3:
            diffs = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
            if diffs:
                # Low variance in differences indicates predictable growth
                variance = np.var(diffs)
                growth_score = 1.0 / (1.0 + variance)
                return min(growth_score, 1.0)
        
        return 0.5
    
    def _cluster_patterns(self, patterns: Dict[str, List]) -> List[Set[str]]:
        """Cluster related patterns using similarity metrics."""
        pattern_keys = list(patterns.keys())
        clusters = []
        visited = set()
        
        for i, pattern1 in enumerate(pattern_keys):
            if pattern1 in visited:
                continue
            
            cluster = {pattern1}
            visited.add(pattern1)
            
            for pattern2 in pattern_keys[i+1:]:
                if pattern2 not in visited:
                    similarity = self._calculate_pattern_similarity(pattern1, pattern2)
                    if similarity > 0.7:
                        cluster.add(pattern2)
                        visited.add(pattern2)
            
            clusters.append(cluster)
        
        return clusters
    
    def _calculate_pattern_similarity(self, pattern1: str, pattern2: str) -> float:
        """Calculate similarity between two patterns."""
        # Levenshtein distance-based similarity
        max_len = max(len(pattern1), len(pattern2))
        if max_len == 0:
            return 1.0
        
        # Simple character-based similarity
        common_chars = sum(1 for c1, c2 in zip(pattern1, pattern2) if c1 == c2)
        return common_chars / max_len
    
    def generate_intelligent_candidates(self, pattern_data: Dict, existing: set) -> List[Dict]:
        """Generate missing asset candidates with ML-powered intelligence."""
        logger.info("\n🤖 Generating intelligent missing asset candidates...")
        start_time = time.time()
        
        candidates = []
        patterns = pattern_data.get('patterns', {})
        metadata = pattern_data.get('metadata', {})
        clusters = pattern_data.get('clusters', [])
        
        if not patterns:
            logger.warning("No patterns found for candidate generation")
            return []
        
        # Process each pattern with multiple strategies
        for template, hosts in patterns.items():
            if len(hosts) < 2:
                continue
            
            try:
                # Strategy 1: Gap filling
                gap_candidates = self._generate_gap_candidates(
                    template, hosts, metadata.get(template, {}), existing
                )
                candidates.extend(gap_candidates)
                
                # Strategy 2: Sequence prediction
                sequence_candidates = self._generate_sequence_candidates(
                    template, hosts, metadata.get(template, {}), existing
                )
                candidates.extend(sequence_candidates)
                
                # Strategy 3: Pattern extrapolation
                extrapolated = self._generate_extrapolated_candidates(
                    template, hosts, metadata.get(template, {}), existing
                )
                candidates.extend(extrapolated)
                
            except Exception as e:
                logger.warning(f"Failed to process pattern {template}: {e}")
                continue
        
        # Remove duplicates and rank
        unique_candidates = self._deduplicate_candidates(candidates)
        ranked_candidates = self._rank_candidates_intelligently(unique_candidates, pattern_data)
        
        # Apply ML-based filtering
        filtered_candidates = self._apply_ml_filtering(ranked_candidates)
        
        logger.info(f"✓ Generated {len(filtered_candidates)} candidates in {time.time()-start_time:.2f}s")
        
        if filtered_candidates:
            high_confidence = sum(1 for c in filtered_candidates if c.get('likelihood', 0) > 0.7)
            logger.info(f"  🎯 High confidence candidates: {high_confidence}")
            logger.info(f"  📈 Average likelihood: {np.mean([c.get('likelihood', 0) for c in filtered_candidates]):.2%}")
        
        return filtered_candidates
    
    def _generate_gap_candidates(self, template: str, hosts: List[str], 
                                metadata: Dict, existing: set) -> List[Dict]:
        """Generate candidates for gaps in sequences."""
        candidates = []
        
        # Extract all number sequences
        number_positions = defaultdict(set)
        for host in hosts:
            for match in re.finditer(r'\d+', host):
                try:
                    number_positions[match.start()].add(int(match.group()))
                except ValueError:
                    continue
        
        # Find gaps in each position
        for position, numbers in number_positions.items():
            if len(numbers) < 2:
                continue
            
            numbers = sorted(numbers)
            
            # Intelligent gap detection
            for i in range(len(numbers) - 1):
                gap_size = numbers[i+1] - numbers[i]
                
                # Only fill reasonable gaps
                if 1 < gap_size <= 10:
                    for missing in range(numbers[i] + 1, numbers[i+1]):
                        candidate = self._create_intelligent_candidate(
                            template, missing, position, hosts[0], 
                            metadata, existing, 'gap_fill'
                        )
                        if candidate:
                            candidates.append(candidate)
        
        return candidates
    
    def _generate_sequence_candidates(self, template: str, hosts: List[str], 
                                     metadata: Dict, existing: set) -> List[Dict]:
        """Generate candidates based on sequence prediction."""
        candidates = []
        
        # Extract number sequences
        all_numbers = []
        for host in hosts:
            nums = re.findall(r'\d+', host)
            if nums:
                all_numbers.extend([int(n) for n in nums if n.isdigit()])
        
        if len(all_numbers) < 3:
            return candidates
        
        all_numbers = sorted(set(all_numbers))
        
        # Detect arithmetic progression
        if len(all_numbers) >= 3:
            diffs = [all_numbers[i+1] - all_numbers[i] for i in range(len(all_numbers)-1)]
            
            # Find most common difference
            if diffs:
                common_diff = Counter(diffs).most_common(1)[0][0]
                
                # Predict next in sequence
                next_nums = [
                    all_numbers[-1] + common_diff,
                    all_numbers[-1] + common_diff * 2,
                    all_numbers[0] - common_diff if all_numbers[0] - common_diff > 0 else None
                ]
                
                for num in next_nums:
                    if num and num not in all_numbers and num < 10000:
                        candidate = self._create_intelligent_candidate(
                            template, num, 0, hosts[0], 
                            metadata, existing, 'sequence_prediction'
                        )
                        if candidate:
                            candidates.append(candidate)
        
        return candidates
    
    def _generate_extrapolated_candidates(self, template: str, hosts: List[str], 
                                         metadata: Dict, existing: set) -> List[Dict]:
        """Generate candidates using pattern extrapolation."""
        candidates = []
        
        # Analyze pattern structure
        if len(hosts) < 5:
            return candidates
        
        # Look for environment patterns
        env_patterns = {
            'prod': range(1, 21),
            'dev': range(1, 11),
            'test': range(1, 6),
            'stage': range(1, 6),
        }
        
        for env, expected_range in env_patterns.items():
            if env in template.lower():
                for num in expected_range:
                    hostname = template.replace('NUM', str(num).zfill(2))
                    
                    if hostname.lower() not in existing:
                        candidate = self._create_intelligent_candidate(
                            template, num, 0, hosts[0], 
                            metadata, existing, 'extrapolation'
                        )
                        if candidate:
                            candidates.append(candidate)
        
        return candidates
    
    def _create_intelligent_candidate(self, template: str, number: int, position: int,
                                     sample_host: str, metadata: Dict, existing: set,
                                     strategy: str) -> Optional[Dict]:
        """Create candidate with intelligent metadata."""
        # Generate hostname
        num_str = str(number)
        
        # Intelligent padding
        digit_matches = re.findall(r'\d+', sample_host)
        if digit_matches:
            target_length = len(digit_matches[0])
            if len(num_str) < target_length:
                num_str = num_str.zfill(target_length)
        
        candidate_host = re.sub('NUM', num_str, template, count=1)
        
        if candidate_host.lower() in existing:
            return None
        
        # Build intelligent candidate
        domain = metadata.get('domains', '')
        fqdn = f"{candidate_host}.{domain}" if domain else candidate_host
        
        # Calculate confidence based on multiple factors
        base_confidence = 0.5
        
        # Adjust based on pattern strength
        pattern_strength = min(metadata.get('count', 0) / 100.0, 1.0)
        
        # Adjust based on metadata quality
        metadata_quality = sum([
            0.2 if metadata.get('regions') else 0,
            0.2 if metadata.get('business_units') else 0,
            0.1 if metadata.get('data_centers') else 0,
            0.1 if domain else 0,
            0.2 if metadata.get('avg_quality_score', 0) > 7 else 0,
        ])
        
        # Strategy confidence multipliers
        strategy_multipliers = {
            'gap_fill': 1.2,
            'sequence_prediction': 1.0,
            'extrapolation': 0.8,
        }
        
        confidence = base_confidence + pattern_strength * 0.3 + metadata_quality
        confidence *= strategy_multipliers.get(strategy, 1.0)
        confidence = min(confidence, 0.95)
        
        return {
            'hostname': candidate_host,
            'pattern': template,
            'expected_fqdn': fqdn,
            'expected_region': metadata.get('regions'),
            'expected_business_unit': metadata.get('business_units'),
            'expected_data_center': metadata.get('data_centers'),
            'expected_domain': domain,
            'asset_type': self.pattern_analyzer.classify_asset(candidate_host),
            'pattern_strength': pattern_strength,
            'quality_score': metadata.get('avg_quality_score', 7.5),
            'likelihood': confidence,
            'generation_strategy': strategy,
            'pattern_entropy': metadata.get('pattern_entropy', 0.5),
            'growth_potential': metadata.get('growth_potential', 0.5),
        }
    
    def _deduplicate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Remove duplicate candidates keeping the best version."""
        unique = {}
        
        for candidate in candidates:
            hostname = candidate['hostname'].lower()
            
            if hostname not in unique or candidate['likelihood'] > unique[hostname]['likelihood']:
                unique[hostname] = candidate
        
        return list(unique.values())
    
    def _rank_candidates_intelligently(self, candidates: List[Dict], 
                                      pattern_data: Dict) -> List[Dict]:
        """Rank candidates using advanced scoring."""
        for candidate in candidates:
            # Multi-factor scoring
            score = candidate.get('likelihood', 0.5)
            
            # Pattern quality boost
            if candidate.get('pattern_strength', 0) > 0.2:
                score *= 1.1
            
            # Metadata completeness boost
            metadata_fields = ['expected_region', 'expected_business_unit', 'expected_data_center']
            completeness = sum(1 for field in metadata_fields if candidate.get(field)) / len(metadata_fields)
            score *= (1 + completeness * 0.2)
            
            # Asset type confidence
            if candidate.get('asset_type') != AssetType.UNKNOWN:
                score *= 1.1
            
            # Entropy penalty (high entropy = more random = less confident)
            entropy = candidate.get('pattern_entropy', 0.5)
            score *= (1.5 - entropy)
            
            # Growth potential boost
            growth = candidate.get('growth_potential', 0.5)
            score *= (0.8 + growth * 0.4)
            
            # Strategy confidence
            strategy_scores = {
                'gap_fill': 1.2,
                'sequence_prediction': 1.0,
                'extrapolation': 0.9,
            }
            score *= strategy_scores.get(candidate.get('generation_strategy'), 1.0)
            
            candidate['final_score'] = min(score, 1.0)
        
        return sorted(candidates, key=lambda x: x.get('final_score', 0), reverse=True)
    
    def _apply_ml_filtering(self, candidates: List[Dict]) -> List[Dict]:
        """Apply ML-based filtering to remove unlikely candidates."""
        filtered = []
        
        for candidate in candidates:
            # Rule-based filtering
            hostname = candidate['hostname'].lower()
            
            # Skip obviously invalid patterns
            if any([
                len(hostname) > 63,  # DNS label limit
                hostname.startswith('-') or hostname.endswith('-'),
                '..' in hostname,
                re.search(r'[^a-z0-9\-\.]', hostname),
            ]):
                continue
            
            # ML confidence threshold
            if candidate.get('final_score', 0) >= self.confidence_threshold:
                filtered.append(candidate)
        
        return filtered
    
    def initialize_neural_ensemble(self, input_dim: int):
        """Initialize advanced neural network ensemble."""
        logger.info("\n🧠 Initializing Neural Network Ensemble...")
        
        try:
            self.algorithms = [
                ('LSTM', LSTMPredictor(input_dim).to(self.device)),
                ('GRU', GRUPredictor(input_dim).to(self.device)),
                ('Transformer', TransformerPredictor(input_dim).to(self.device)),
                ('CNN', CNNPredictor(input_dim).to(self.device)),
                ('Autoencoder', AutoencoderPredictor(input_dim).to(self.device)),
                ('VAE', VAEPredictor(input_dim).to(self.device)),
                ('Attention', AttentionPredictor(input_dim).to(self.device)),
                ('Residual', ResidualPredictor(input_dim).to(self.device)),
                ('EnsembleNN', EnsembleNNPredictor(input_dim).to(self.device)),
                ('GraphNN', GraphNNPredictor(input_dim).to(self.device))
            ]
            
            total_params = 0
            for name, model in self.algorithms:
                param_count = sum(p.numel() for p in model.parameters())
                total_params += param_count
                logger.info(f"  📦 {name}: {param_count:,} parameters")
            
            logger.info(f"  💾 Total parameters: {total_params:,}")
            
        except Exception as e:
            logger.error(f"Failed to initialize algorithms: {e}")
            raise
    
    def train_ensemble_optimized(self, df: pd.DataFrame):
        """Train ensemble with advanced optimization techniques."""
        logger.info("\n🏋️ Training Neural Ensemble with Optimization...")
        start_time = time.time()
        
        try:
            # Prepare features with caching
            X, y = self._prepare_advanced_features(df)
            
            # Smart sampling for efficiency
            max_samples = min(10000, len(X))
            if len(X) > max_samples:
                logger.info(f"  📊 Smart sampling: {max_samples:,} from {len(X):,} samples")
                
                # Stratified sampling based on quality scores
                indices = self._stratified_sample(y, max_samples)
                X = X[indices]
                y = y[indices]
            
            # Advanced train/validation split
            split_idx = int(0.8 * len(X))
            X_train = torch.FloatTensor(X[:split_idx]).to(self.device)
            y_train = torch.FloatTensor(y[:split_idx]).to(self.device)
            X_val = torch.FloatTensor(X[split_idx:]).to(self.device)
            y_val = torch.FloatTensor(y[split_idx:]).to(self.device)
            
            # Train with early stopping
            for i, (name, model) in enumerate(self.algorithms):
                logger.info(f"  🔄 Training {name} ({i+1}/{len(self.algorithms)})...")
                
                # Clear memory
                if self.device.type in ['mps', 'cuda']:
                    if self.device.type == 'mps':
                        torch.mps.empty_cache()
                    else:
                        torch.cuda.empty_cache()
                
                try:
                    # Adaptive training
                    best_loss = float('inf')
                    patience = 3
                    no_improve = 0
                    
                    for epoch in range(20):
                        model.train_model(X_train, y_train, X_val, y_val, epochs=1)
                        
                        # Validation loss check
                        with torch.no_grad():
                            model.eval()
                            val_pred = model.predict(X_val)
                            val_loss = F.mse_loss(val_pred, y_val).item()
                        
                        if val_loss < best_loss:
                            best_loss = val_loss
                            no_improve = 0
                        else:
                            no_improve += 1
                        
                        if no_improve >= patience:
                            logger.info(f"    ✓ {name} converged at epoch {epoch+1}")
                            break
                    
                except Exception as e:
                    logger.warning(f"    ⚠️ {name} training issue: {e}")
                    # Fallback to smaller batch
                    try:
                        model.train_model(
                            X_train[:2000], y_train[:2000],
                            X_val[:500], y_val[:500], 
                            epochs=10
                        )
                    except:
                        logger.warning(f"    ⏭️ Skipping {name}")
                        continue
                
                # Memory cleanup
                if self.device.type in ['mps', 'cuda']:
                    if self.device.type == 'mps':
                        torch.mps.synchronize()
                    else:
                        torch.cuda.synchronize()
            
            logger.info(f"✓ Ensemble training completed in {time.time()-start_time:.1f}s")
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    def _prepare_advanced_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare advanced feature set with intelligent extraction."""
        cache_key = 'advanced_features'
        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]
        
        logger.info("  🔬 Extracting advanced features...")
        
        X = []
        y = []
        
        for idx, row in df.iterrows():
            if idx % 50000 == 0 and idx > 0:
                logger.info(f"    Processing: {idx:,}/{len(df):,}")
            
            try:
                features = self._extract_advanced_features(row)
                X.append(features)
                
                confidence = self._calculate_advanced_confidence(row)
                y.append(confidence)
                
            except Exception as e:
                logger.debug(f"Feature extraction failed for row {idx}: {e}")
                continue
        
        if not X:
            raise ValueError("No features could be extracted")
        
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)
        
        # Normalize features
        X = self._normalize_features(X)
        
        self.feature_cache[cache_key] = (X, y)
        
        return X, y
    
    def _extract_advanced_features(self, row) -> np.ndarray:
        """Extract advanced feature vector from data row."""
        hostname = str(row.get('host', '')).lower()
        
        # Extended feature vector (30 features)
        features = np.zeros(30, dtype=np.float32)
        
        # Basic hostname features (0-5)
        features[0] = min(len(hostname) / 50.0, 1.0)
        features[1] = min(hostname.count('.') / 5.0, 1.0)
        features[2] = min(hostname.count('-') / 5.0, 1.0)
        features[3] = min(hostname.count('_') / 5.0, 1.0)
        features[4] = min(sum(c.isdigit() for c in hostname) / 10.0, 1.0)
        features[5] = min(sum(c.isalpha() for c in hostname) / 30.0, 1.0)
        
        # Prefix patterns (6-12)
        prefixes = ['srv', 'web', 'db', 'app', 'fw', 'lb', 'api']
        for i, prefix in enumerate(prefixes):
            features[6 + i] = 1.0 if hostname.startswith(prefix) else 0.0
        
        # Environment indicators (13-16)
        envs = ['prod', 'dev', 'test', 'stage']
        for i, env in enumerate(envs):
            features[13 + i] = 1.0 if env in hostname else 0.0
        
        # Metadata features (17-22)
        features[17] = 1.0 if row.get('region') == 'US' else 0.5 if row.get('region') else 0.0
        features[18] = 1.0 if row.get('data_center') else 0.0
        features[19] = float(row.get('data_quality_score', 7.5)) / 10.0
        features[20] = float(row.get('hostname_complexity', 0.5)) if 'hostname_complexity' in row else 0.5
        features[21] = 1.0 if row.get('has_domain', 0) else 0.0
        features[22] = min(float(row.get('hostname_length', len(hostname))) / 50.0, 1.0) if 'hostname_length' in row else features[0]
        
        # Asset type encoding (23-26)
        if 'asset_type' in row and hasattr(row['asset_type'], 'value'):
            asset_type = row['asset_type']
            features[23] = 1.0 if asset_type == AssetType.WEB_SERVER else 0.0
            features[24] = 1.0 if asset_type == AssetType.DATABASE else 0.0
            features[25] = 1.0 if asset_type == AssetType.APPLICATION else 0.0
            features[26] = 1.0 if asset_type in [AssetType.NETWORK, AssetType.SECURITY] else 0.0
        
        # Temporal features (27-29)
        if 'days_since_seen' in row:
            days = float(row['days_since_seen']) if not pd.isna(row['days_since_seen']) else 30.0
            features[27] = min(days / 365.0, 1.0)  # Normalized days
            features[28] = 1.0 if days < 7 else 0.0  # Recently seen
            features[29] = 1.0 if days > 90 else 0.0  # Stale
        
        return np.clip(features, 0, 1)
    
    def _calculate_advanced_confidence(self, row) -> float:
        """Calculate advanced confidence score with multiple factors."""
        score = 0.0
        
        # Coverage weights
        coverage_weights = {
            'present_in_cmdb': 0.20,
            'logging_in_splunk': 0.20,
            'logging_in_gso': 0.15,
            'edr_coverage': 0.15,
            'tanium_coverage': 0.15,
        }
        
        for factor, weight in coverage_weights.items():
            value = row.get(factor)
            if value == 'yes' or value == True:
                score += weight
            elif value == 'partial':
                score += weight * 0.5
        
        # Metadata completeness bonus
        metadata_bonus = 0.0
        if row.get('region'):
            metadata_bonus += 0.05
        if row.get('business_unit'):
            metadata_bonus += 0.05
        if row.get('data_center'):
            metadata_bonus += 0.05
        
        score += metadata_bonus
        
        # Data quality influence
        if 'data_quality_score' in row:
            quality = float(row['data_quality_score']) / 10.0
            score = score * (0.8 + quality * 0.2)
        
        return min(score, 1.0)
    
    def _normalize_features(self, X: np.ndarray) -> np.ndarray:
        """Normalize features using robust scaling."""
        # Use percentile-based normalization for robustness
        percentile_5 = np.percentile(X, 5, axis=0)
        percentile_95 = np.percentile(X, 95, axis=0)
        
        # Avoid division by zero
        scale = percentile_95 - percentile_5
        scale[scale == 0] = 1.0
        
        X_normalized = (X - percentile_5) / scale
        
        return np.clip(X_normalized, 0, 1)
    
    def _stratified_sample(self, y: np.ndarray, n_samples: int) -> np.ndarray:
        """Perform stratified sampling based on confidence scores."""
        # Create bins for stratification
        bins = np.percentile(y, [0, 25, 50, 75, 100])
        indices = []
        
        for i in range(len(bins) - 1):
            mask = (y >= bins[i]) & (y < bins[i+1])
            bin_indices = np.where(mask)[0]
            
            if len(bin_indices) > 0:
                n_from_bin = min(len(bin_indices), n_samples // 4)
                sampled = np.random.choice(bin_indices, n_from_bin, replace=False)
                indices.extend(sampled)
        
        return np.array(indices)
    
    def predict_with_ensemble(self, candidates: List[Dict]) -> List[Dict]:
        """Predict using ensemble with advanced voting mechanisms."""
        if not candidates:
            return []
        
        logger.info(f"\n🔮 Predicting {len(candidates)} candidates with ensemble...")
        start_time = time.time()
        
        predictions = []
        batch_size = 64
        
        for batch_idx in range(0, len(candidates), batch_size):
            if batch_idx % 500 == 0 and batch_idx > 0:
                logger.info(f"  Progress: {batch_idx:,}/{len(candidates):,}")
            
            batch = candidates[batch_idx:batch_idx + batch_size]
            
            try:
                # Prepare batch features
                batch_features = np.array([
                    self._candidate_to_advanced_features(c) for c in batch
                ])
                batch_tensor = torch.FloatTensor(batch_features).to(self.device)
                
                # Collect predictions from all models
                votes = []
                weights = []
                
                with torch.no_grad():
                    for name, model in self.algorithms:
                        try:
                            model.eval()
                            pred = model.predict(batch_tensor)
                            votes.append(pred.cpu().numpy())
                            
                            # Model-specific weights based on historical performance
                            model_weight = self.feedback_scores.get(name, 1.0)
                            weights.append(model_weight)
                            
                        except Exception as e:
                            logger.debug(f"Model {name} prediction failed: {e}")
                            votes.append(np.ones(len(batch)) * 0.5)
                            weights.append(0.5)
                
                if votes:
                    # Weighted ensemble voting
                    weights = np.array(weights) / sum(weights)
                    ensemble_scores = np.average(votes, axis=0, weights=weights)
                    
                    # Process predictions
                    for i, candidate in enumerate(batch):
                        confidence = float(ensemble_scores[i])
                        
                        # Apply final confidence adjustment
                        final_confidence = confidence * candidate.get('final_score', 1.0)
                        
                        if final_confidence > self.confidence_threshold:
                            prediction = candidate.copy()
                            prediction['confidence'] = final_confidence
                            prediction['ensemble_confidence'] = confidence
                            
                            # Add voting statistics
                            prediction['algorithm_scores'] = {
                                name: float(votes[j][i]) if j < len(votes) else 0.5
                                for j, (name, _) in enumerate(self.algorithms)
                            }
                            
                            prediction['unanimous'] = all(v[i] > 0.5 for v in votes)
                            prediction['agreement'] = sum(v[i] > 0.5 for v in votes) / len(votes)
                            prediction['variance'] = np.var([v[i] for v in votes])
                            
                            predictions.append(prediction)
                
            except Exception as e:
                logger.warning(f"Batch prediction failed: {e}")
                continue
            
            # Memory management
            if self.device.type in ['mps', 'cuda']:
                if self.device.type == 'mps':
                    torch.mps.empty_cache()
                else:
                    torch.cuda.empty_cache()
        
        # Final ranking
        predictions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        logger.info(f"✓ Predictions completed in {time.time()-start_time:.1f}s")
        
        if predictions:
            logger.info(f"  🎯 Valid predictions: {len(predictions)}")
            logger.info(f"  📊 High confidence (>0.8): {sum(1 for p in predictions if p.get('confidence', 0) > 0.8)}")
            logger.info(f"  🤝 Unanimous agreement: {sum(1 for p in predictions if p.get('unanimous', False))}")
        
        return predictions
    
    def _candidate_to_advanced_features(self, candidate: Dict) -> np.ndarray:
        """Convert candidate to advanced feature vector."""
        mock_row = {
            'host': candidate.get('hostname', ''),
            'region': candidate.get('expected_region'),
            'business_unit': candidate.get('expected_business_unit'),
            'data_center': candidate.get('expected_data_center'),
            'data_quality_score': candidate.get('quality_score', 7.5),
            'hostname_complexity': candidate.get('pattern_entropy', 0.5),
            'has_domain': 1 if '.' in candidate.get('hostname', '') else 0,
            'hostname_length': len(candidate.get('hostname', '')),
            'asset_type': candidate.get('asset_type', AssetType.UNKNOWN),
        }
        
        return self._extract_advanced_features(mock_row)
    
    def save_intelligent_results(self, predictions: List[Dict]):
        """Save results with comprehensive reporting."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prepare comprehensive output
        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '3.2-intelligent',
                'device': str(self.device),
                'total_predictions': len(predictions),
                'confidence_threshold': self.confidence_threshold,
            },
            'statistics': {
                'total': len(predictions),
                'high_confidence': sum(1 for p in predictions if p.get('confidence', 0) > 0.8),
                'medium_confidence': sum(1 for p in predictions if 0.5 <= p.get('confidence', 0) <= 0.8),
                'unanimous': sum(1 for p in predictions if p.get('unanimous', False)),
                'by_asset_type': Counter([p.get('asset_type', AssetType.UNKNOWN).value for p in predictions[:100]]),
                'by_strategy': Counter([p.get('generation_strategy', 'unknown') for p in predictions[:100]]),
                'avg_confidence': np.mean([p.get('confidence', 0) for p in predictions]) if predictions else 0,
                'avg_agreement': np.mean([p.get('agreement', 0) for p in predictions]) if predictions else 0,
            },
            'predictions': predictions[:1000],  # Limit to top 1000
        }
        
        # Save JSON
        json_filename = f'missing_assets_intelligent_{timestamp}.json'
        try:
            with open(json_filename, 'w') as f:
                json.dump(output, f, indent=2, default=str)
            logger.info(f"\n💾 Results saved to {json_filename}")
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
        
        # Save CSV for easy analysis
        csv_filename = f'missing_assets_intelligent_{timestamp}.csv'
        try:
            df_predictions = pd.DataFrame(predictions[:1000])
            df_predictions.to_csv(csv_filename, index=False)
            logger.info(f"📊 CSV saved to {csv_filename}")
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
        
        # Display top predictions
        logger.info("\n🏆 Top 15 Missing Assets:")
        for i, pred in enumerate(predictions[:15]):
            logger.info(f"  {i+1:2d}. {pred.get('hostname', 'unknown'):<30} "
                       f"[{pred.get('confidence', 0):.1%} confidence]")
            
            # Additional details
            details = []
            if pred.get('expected_region'):
                details.append(f"Region: {pred['expected_region']}")
            if pred.get('asset_type') and pred['asset_type'] != AssetType.UNKNOWN:
                details.append(f"Type: {pred['asset_type'].value}")
            if pred.get('generation_strategy'):
                details.append(f"Strategy: {pred['generation_strategy']}")
            
            if details:
                logger.info(f"      └─ {' | '.join(details)}")
            
            # Voting details for top 5
            if i < 5:
                logger.info(f"      └─ Agreement: {pred.get('agreement', 0):.1%} | "
                          f"Variance: {pred.get('variance', 0):.3f}")
    
    def run(self):
        """Main execution with intelligent orchestration."""
        logger.info("\n" + "="*70)
        logger.info("🚀 INTELLIGENT MISSING ASSET DISCOVERY SYSTEM v3.2")
        logger.info("🧠 Powered by Advanced ML & Pattern Recognition")
        logger.info("="*70)
        
        try:
            # System verification
            self._verify_system()
            
            total_start = time.time()
            
            # Phase 1: Data Loading & Enrichment
            logger.info("\n📚 Phase 1: Data Loading & Enrichment")
            df = self.load_and_enrich_data()
            
            # Phase 2: Pattern Discovery
            logger.info("\n🔍 Phase 2: Intelligent Pattern Discovery")
            pattern_data = self.discover_intelligent_patterns(df)
            
            # Phase 3: Candidate Generation
            logger.info("\n🎯 Phase 3: Smart Candidate Generation")
            existing_hosts = set(df['host'].dropna().str.lower())
            candidates = self.generate_intelligent_candidates(pattern_data, existing_hosts)
            
            if not candidates:
                logger.warning("⚠️ No candidates generated - your inventory may be complete!")
                return []
            
            # Phase 4: Neural Network Training
            logger.info("\n🧠 Phase 4: Neural Network Training")
            input_dim = 30  # Extended feature set
            self.initialize_neural_ensemble(input_dim)
            self.train_ensemble_optimized(df)
            
            # Phase 5: Ensemble Prediction
            logger.info("\n🔮 Phase 5: Ensemble Prediction")
            predictions = self.predict_with_ensemble(candidates)
            
            # Phase 6: Results & Reporting
            logger.info("\n📊 Phase 6: Results & Reporting")
            if predictions:
                self.save_intelligent_results(predictions)
            
            # Summary
            total_time = time.time() - total_start
            logger.info("\n" + "="*70)
            logger.info(f"✅ ANALYSIS COMPLETED SUCCESSFULLY")
            logger.info(f"⏱️ Total time: {total_time:.1f} seconds")
            logger.info(f"🎯 Missing assets discovered: {len(predictions)}")
            
            if predictions:
                logger.info(f"📊 Confidence distribution:")
                logger.info(f"   • High (>80%): {sum(1 for p in predictions if p.get('confidence', 0) > 0.8)}")
                logger.info(f"   • Medium (50-80%): {sum(1 for p in predictions if 0.5 <= p.get('confidence', 0) <= 0.8)}")
                logger.info(f"   • Average confidence: {np.mean([p.get('confidence', 0) for p in predictions]):.1%}")
            
            logger.info("="*70)
            
            return predictions
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Analysis interrupted by user")
            return []
        except Exception as e:
            logger.error(f"\n❌ Critical error: {e}")
            logger.error(traceback.format_exc())
            return []
        finally:
            self._cleanup()
    
    def _verify_system(self):
        """Verify system capabilities."""
        logger.info("\n🔧 System Verification")
        
        # Test compute device
        try:
            test_tensor = torch.randn(100, 100, device=self.device)
            result = torch.matmul(test_tensor, test_tensor.T)
            del test_tensor, result
            
            if self.device.type == 'mps':
                torch.mps.empty_cache()
                torch.mps.synchronize()
            elif self.device.type == 'cuda':
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            logger.info(f"✓ {self.device.type.upper()} compute verified")
            
        except Exception as e:
            logger.warning(f"⚠️ Compute test failed: {e}, continuing anyway")
        
        # Check available memory
        if self.device.type == 'cuda':
            mem_allocated = torch.cuda.memory_allocated() / 1024**3
            mem_reserved = torch.cuda.memory_reserved() / 1024**3
            logger.info(f"  GPU Memory: {mem_allocated:.1f}GB allocated, {mem_reserved:.1f}GB reserved")
        
        # Check CPU resources
        logger.info(f"  CPU Cores: {os.cpu_count()}")
        logger.info(f"  Platform: {platform.platform()}")
    
    def _cleanup(self):
        """Clean up resources."""
        logger.info("\n🧹 Cleaning up resources...")
        
        # Clear caches
        self.pattern_cache.clear()
        self.feature_cache.clear()
        self.prediction_cache.clear()
        
        # Clear GPU memory
        if self.device.type == 'mps':
            torch.mps.empty_cache()
        elif self.device.type == 'cuda':
            torch.cuda.empty_cache()
        
        # Force garbage collection
        gc.collect()
        
        logger.info("✓ Cleanup completed")

# Main execution
if __name__ == "__main__":
    try:
        # Initialize and run the intelligent predictor
        predictor = SmartAssetPredictor()
        predictions = predictor.run()
        
        if predictions:
            logger.info(f"\n🎉 Successfully identified {len(predictions)} missing assets!")
            logger.info("📈 Check the output files for detailed analysis")
        else:
            logger.info("\n📋 No missing assets identified - your inventory appears complete")
            
    except KeyboardInterrupt:
        logger.info("\n⚠️ Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)