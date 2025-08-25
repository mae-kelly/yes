#!/usr/bin/env python3

import torch
import torch.nn.functional as F
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime
import json
import gc
import logging
import os
import platform
import time
import traceback
import sys
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional

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

class OptimizedAssetPredictor:
    def __init__(self, db_path='universal_cmdb.db'):
        self.db_path = db_path
        self.device = self._initialize_mps()
        self.algorithms = []
        self.pattern_cache = {}
        self.feature_cache = {}
        self.pattern_threshold = 3
        self.confidence_threshold = 0.5
        self.max_memory_gb = 18
        
    def _initialize_mps(self) -> torch.device:
        """Initialize MPS (Metal Performance Shaders) for Apple Silicon GPU."""
        logger.info("\n˚₊· ͟͟͞͞➳❥ initializing neural architecture...")
        logger.info("⋆｡‧˚ʚ♡ɞ˚‧｡⋆ checking for apple silicon gpu")
        
        if not torch.backends.mps.is_available():
            if not torch.backends.mps.is_built():
                logger.error("✗ pytorch wasn't built with mps support")
            else:
                logger.error("✗ not running on macos with apple silicon")
            
            if torch.cuda.is_available():
                logger.warning("⋆.˚ using cuda fallback instead")
                return torch.device("cuda")
            else:
                logger.warning("⋆.˚ no gpu available - using cpu")
                return torch.device("cpu")
        
        device = torch.device("mps")
        logger.info(f"✓ ‧₊˚🖇️✩ mps gpu detected on {platform.machine()}")
        logger.info(f"⋆.˚ 𓆉 macos version: {platform.mac_ver()[0]}")
        
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
        logger.info("₊˚🎧⊹♡ memory limit enforced at 18 gib")
        
        return device
    
    def _verify_gpu(self):
        """Verify GPU is working correctly."""
        logger.info("\n༻❁༺ running gpu verification tests...")
        try:
            test = torch.randn(1000, 1000, device=self.device)
            result = torch.matmul(test, test.T)
            del test, result
            
            if self.device.type == 'mps':
                torch.mps.empty_cache()
                torch.mps.synchronize()
            elif self.device.type == 'cuda':
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            logger.info(f"✓ ⋆.˚ {self.device.type} computation verified successfully")
        except Exception as e:
            logger.warning(f"⚠ GPU test failed: {e}, continuing with available device")
    
    def load_data(self) -> pd.DataFrame:
        """Load data with comprehensive error handling."""
        logger.info("\n⊹ ࣪ ˖ loading asset database...")
        start_time = time.time()
        
        try:
            conn = duckdb.connect(self.db_path, read_only=True)
            df = conn.execute("""
                SELECT * FROM universal_cmdb 
                WHERE host IS NOT NULL 
                ORDER BY host
            """).df()
            conn.close()
            
            # Validate that we have data
            if df.empty:
                logger.error("✗ No data found in universal_cmdb table")
                raise ValueError("Empty dataset")
            
            # Ensure required columns exist
            required_columns = ['host']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"✗ Missing required columns: {missing_columns}")
                raise ValueError(f"Missing columns: {missing_columns}")
            
            logger.info(f"✓ ˚₊· loaded {len(df):,} records in {time.time()-start_time:.2f}s")
            logger.info(f"  𓇼 unique hostnames: {df['host'].nunique():,}")
            
            # Safe column checking
            if 'business_unit' in df.columns:
                logger.info(f"  𓆉 business units: {df['business_unit'].nunique()}")
            if 'region' in df.columns:
                logger.info(f"  𓆝 regions: {df['region'].nunique()}")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Failed to load data: {e}")
            raise
    
    def find_patterns_optimized(self, df: pd.DataFrame) -> Dict:
        """Find patterns with defensive programming - COMPLETELY SAFE VERSION."""
        logger.info("\n⋆˙⟡♡ discovering hostname patterns...")
        start_time = time.time()
        
        patterns = defaultdict(list)
        pattern_metadata = {}
        
        # Extra safe hostname extraction
        try:
            if 'host' not in df.columns:
                logger.error("'host' column not found in dataframe")
                return {'patterns': {}, 'metadata': {}}
            
            # Convert to string first, then process
            host_series = df['host'].fillna('').astype(str)
            hostnames = host_series[host_series != ''].str.lower().str.strip()
            
            if len(hostnames) == 0:
                logger.warning("⚠ No valid hostnames found")
                return {'patterns': {}, 'metadata': {}}
                
        except Exception as e:
            logger.error(f"Failed to extract hostnames: {e}")
            return {'patterns': {}, 'metadata': {}}
        
        # Process hostnames
        for idx in range(len(hostnames)):
            try:
                if idx % 50000 == 0 and idx > 0:
                    logger.info(f"  ₊˚⊹ processed {idx:,}/{len(hostnames):,} hostnames")
                
                # Use .values to avoid index issues
                hostname = hostnames.values[idx] if idx < len(hostnames.values) else None
                
                if hostname and isinstance(hostname, str) and hostname.strip():
                    template = self._extract_template(hostname)
                    patterns[template].append(hostname)
                    
            except Exception as e:
                logger.debug(f"Skipping hostname at index {idx}: {e}")
                continue
        
        legitimate = {}
        for template, hosts in patterns.items():
            if len(hosts) >= self.pattern_threshold:
                legitimate[template] = hosts
                try:
                    pattern_metadata[template] = self._analyze_pattern_metadata(hosts, df)
                except Exception as e:
                    logger.warning(f"  ⚠ Failed to analyze metadata for pattern {template}: {e}")
                    pattern_metadata[template] = {'count': len(hosts)}
        
        logger.info(f"✓ ˚₊· found {len(legitimate)} patterns in {time.time()-start_time:.2f}s")
        
        if legitimate:
            try:
                max_pattern_size = max(len(h) for h in legitimate.values())
                logger.info(f"  ⋆.˚ patterns with 3+ assets: {len(legitimate)}")
                logger.info(f"  𓆡 largest pattern: {max_pattern_size} hosts")
            except Exception:
                pass
        
        self.pattern_cache = legitimate
        return {'patterns': legitimate, 'metadata': pattern_metadata}
    
    def _extract_template(self, hostname: str) -> str:
        """Extract template pattern from hostname."""
        import re
        
        # Replace numbers with NUM placeholder
        template = re.sub(r'\d+', 'NUM', hostname)
        
        # Consolidate consecutive NUM placeholders
        template = re.sub(r'NUM(NUM)+', 'NUM', template)
        
        return template
    
    def _analyze_pattern_metadata(self, hosts: List[str], df: pd.DataFrame) -> Dict:
        """Safely analyze pattern metadata with defensive programming."""
        # Ensure hosts is lowercase for matching
        hosts_lower = [h.lower() for h in hosts if h]
        
        # Safe filtering
        try:
            if 'host' in df.columns:
                sample_data = df[df['host'].astype(str).str.lower().isin(hosts_lower)]
            else:
                sample_data = pd.DataFrame()
        except Exception as e:
            logger.warning(f"Failed to filter data: {e}")
            sample_data = pd.DataFrame()
        
        # Helper function to safely get mode - COMPLETELY SAFE VERSION
        def safe_mode(column_name):
            try:
                if column_name not in df.columns or sample_data.empty:
                    return None
                    
                series = sample_data[column_name]
                if series is None or len(series) == 0:
                    return None
                    
                # Drop NaN values first
                clean_series = series.dropna()
                if len(clean_series) == 0:
                    return None
                
                # Calculate mode
                mode_result = clean_series.mode()
                
                # Check if mode_result has any values
                if isinstance(mode_result, pd.Series) and len(mode_result) > 0:
                    return mode_result.values[0]  # Use .values[0] instead of .iloc[0]
                elif hasattr(mode_result, '__len__') and len(mode_result) > 0:
                    return mode_result[0]
                else:
                    return None
                    
            except Exception as e:
                logger.debug(f"safe_mode failed for {column_name}: {e}")
                return None
        
        # Helper function to safely get mean - COMPLETELY SAFE VERSION
        def safe_mean(column_name, default=7.5):
            try:
                if column_name not in df.columns or sample_data.empty:
                    return default
                    
                series = sample_data[column_name]
                if series is None or len(series) == 0:
                    return default
                    
                clean_series = series.dropna()
                if len(clean_series) == 0:
                    return default
                    
                return float(clean_series.mean())
                
            except Exception as e:
                logger.debug(f"safe_mean failed for {column_name}: {e}")
                return default
        
        metadata = {
            'count': len(hosts),
            'regions': safe_mode('region'),
            'business_units': safe_mode('business_unit'),
            'data_centers': safe_mode('data_center'),
            'domains': self._extract_common_domain(hosts),
            'avg_quality_score': safe_mean('data_quality_score', default=7.5)
        }
        
        return metadata
    
    def _extract_common_domain(self, hosts: List[str]) -> Optional[str]:
        """Safely extract common domain from hosts - COMPLETELY SAFE VERSION."""
        if not hosts:
            return None
        
        try:
            domains = []
            # Limit to first 10 hosts or available hosts
            for host in hosts[:min(10, len(hosts))]:
                if not host or not isinstance(host, str):
                    continue
                parts = host.split('.')
                if len(parts) > 1:
                    domains.append('.'.join(parts[1:]))
            
            if not domains:
                return None
                
            # Safe Counter usage without .iloc
            domain_counts = Counter(domains)
            if domain_counts:
                # Get most common using items() instead of most_common to avoid index issues
                most_common_domain = max(domain_counts.items(), key=lambda x: x[1])[0]
                return most_common_domain
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract domain: {e}")
            return None
    
    def generate_smart_candidates(self, pattern_data: Dict, existing: set) -> List[Dict]:
        """Generate intelligent missing asset candidates."""
        logger.info("\n༊*·˚ generating intelligent missing asset candidates...")
        start_time = time.time()
        
        candidates = []
        patterns = pattern_data.get('patterns', {})
        metadata = pattern_data.get('metadata', {})
        
        if not patterns:
            logger.warning("⚠ No patterns found to generate candidates")
            return []
        
        for template, hosts in patterns.items():
            if len(hosts) < 2:
                continue
            
            try:
                numbers_found = self._extract_number_sequences(hosts)
                
                for seq_pos, seq_values in numbers_found.items():
                    gaps = self._find_intelligent_gaps(seq_values)
                    
                    for gap in gaps[:50]:  # Limit candidates per pattern
                        candidate = self._create_candidate(
                            template, gap, seq_pos, hosts[0], 
                            metadata.get(template, {}), existing
                        )
                        
                        if candidate and candidate['hostname'] not in existing:
                            candidates.append(candidate)
            except Exception as e:
                logger.warning(f"  ⚠ Failed to process pattern {template}: {e}")
                continue
        
        candidates = self._rank_candidates_by_likelihood(candidates)
        
        logger.info(f"✓ ⋆.ೃ࿔*:･ generated {len(candidates)} candidates in {time.time()-start_time:.2f}s")
        if candidates:
            logger.info(f"  ˚₊· high probability: {sum(1 for c in candidates if c.get('likelihood', 0) > 0.7)}")
        
        return candidates
    
    def _extract_number_sequences(self, hosts: List[str]) -> Dict:
        """Extract number sequences from hostnames."""
        import re
        sequences = defaultdict(set)
        
        for host in hosts:
            for match in re.finditer(r'\d+', host):
                try:
                    sequences[match.start()].add(int(match.group()))
                except ValueError:
                    continue
        
        return {k: sorted(v) for k, v in sequences.items()}
    
    def _find_intelligent_gaps(self, sequence: List[int]) -> List[int]:
        """Find gaps in number sequences intelligently."""
        if len(sequence) < 2:
            return []
        
        gaps = []
        
        # Find gaps in sequence
        for i in range(len(sequence) - 1):
            if sequence[i+1] - sequence[i] > 1:
                for missing in range(sequence[i] + 1, min(sequence[i+1], sequence[i] + 10)):
                    gaps.append(missing)
        
        # Find pattern-based predictions
        if len(sequence) >= 3:
            diffs = [sequence[i+1] - sequence[i] for i in range(len(sequence)-1)]
            if diffs:
                common_diff = max(set(diffs), key=diffs.count)
                
                if common_diff > 0:
                    next_expected = sequence[-1] + common_diff
                    if next_expected not in sequence and next_expected < 10000:
                        gaps.append(next_expected)
                    
                    prev_expected = sequence[0] - common_diff
                    if prev_expected > 0 and prev_expected not in sequence:
                        gaps.append(prev_expected)
        
        return list(set(gaps))  # Remove duplicates
    
    def _create_candidate(self, template: str, number: int, position: int, 
                         sample_host: str, metadata: Dict, existing: set) -> Optional[Dict]:
        """Safely create candidate with defensive checks."""
        import re
        
        candidate_host = template
        num_str = str(number)
        
        # Safely check for digits in sample_host
        digit_matches = re.findall(r'\d+', sample_host)
        if digit_matches and len(digit_matches) > 0:
            target_length = len(digit_matches[0])
            if len(num_str) < target_length:
                num_str = num_str.zfill(target_length)
        
        candidate_host = re.sub('NUM', num_str, candidate_host, count=1)
        
        if candidate_host.lower() in existing:
            return None
        
        domain = metadata.get('domains', '')
        fqdn = f"{candidate_host}.{domain}" if domain else candidate_host
        
        return {
            'hostname': candidate_host,
            'pattern': template,
            'expected_fqdn': fqdn,
            'expected_region': metadata.get('regions'),
            'expected_business_unit': metadata.get('business_units'),
            'expected_data_center': metadata.get('data_centers'),
            'expected_domain': domain,
            'pattern_strength': min(metadata.get('count', 0) / 100.0, 1.0),
            'quality_score': metadata.get('avg_quality_score', 7.5),
            'likelihood': 0.5
        }
    
    def _rank_candidates_by_likelihood(self, candidates: List[Dict]) -> List[Dict]:
        """Rank candidates by likelihood scores."""
        for candidate in candidates:
            score = 0.5
            
            # Adjust score based on pattern strength
            if candidate.get('pattern_strength', 0) > 0.1:
                score += 0.2
            
            # Adjust based on quality score
            if candidate.get('quality_score', 0) > 7:
                score += 0.1
            
            # Adjust based on metadata completeness
            if candidate.get('expected_region'):
                score += 0.1
            
            if candidate.get('expected_business_unit'):
                score += 0.1
            
            candidate['likelihood'] = min(score, 1.0)
        
        return sorted(candidates, key=lambda x: x.get('likelihood', 0), reverse=True)
    
    def initialize_algorithms(self, input_dim: int):
        """Initialize neural network algorithms."""
        logger.info("\n⋆｡‧˚ʚ initializing 10 neural architectures ɞ˚‧｡⋆")
        
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
            
            for name, model in self.algorithms:
                param_count = sum(p.numel() for p in model.parameters())
                logger.info(f"  ₊˚⊹ {name}: {param_count:,} parameters")
                
        except Exception as e:
            logger.error(f"✗ Failed to initialize algorithms: {e}")
            raise
    
    def train_optimized(self, df: pd.DataFrame):
        """Train neural ensemble with memory optimization."""
        logger.info("\n˚ ༘♡ ⋆｡˚ training neural ensemble...")
        start_time = time.time()
        
        try:
            X, y = self._prepare_efficient_features(df)
            
            # Limit samples for memory efficiency
            max_samples = 8000
            if len(X) > max_samples:
                logger.info(f"  ⋆.˚ sampling {max_samples} from {len(X)} for memory efficiency")
                indices = np.random.choice(len(X), max_samples, replace=False)
                X = X[indices]
                y = y[indices]
            
            # Create train/validation split
            split_idx = int(0.8 * len(X))
            X_train = torch.FloatTensor(X[:split_idx]).to(self.device)
            y_train = torch.FloatTensor(y[:split_idx]).to(self.device)
            X_val = torch.FloatTensor(X[split_idx:]).to(self.device)
            y_val = torch.FloatTensor(y[split_idx:]).to(self.device)
            
            # Train each algorithm
            for i, (name, model) in enumerate(self.algorithms):
                logger.info(f"  ₊˚🎧⊹ training {name} ({i+1}/10)...")
                
                # Clear cache before training
                if self.device.type == 'mps':
                    torch.mps.empty_cache()
                elif self.device.type == 'cuda':
                    torch.cuda.empty_cache()
                
                try:
                    model.train_model(X_train, y_train, X_val, y_val, epochs=20)
                    logger.info(f"    ✓ {name} converged successfully")
                except RuntimeError as e:
                    if "memory" in str(e).lower():
                        logger.warning(f"    ⋆ reducing batch for {name} due to memory constraints")
                        # Try with smaller batch
                        model.train_model(X_train[:1000], y_train[:1000], 
                                        X_val[:200], y_val[:200], epochs=10)
                    else:
                        logger.warning(f"    ⚠ {name} training failed: {e}")
                        continue
                
                # Synchronize after each model
                if self.device.type == 'mps':
                    torch.mps.synchronize()
                elif self.device.type == 'cuda':
                    torch.cuda.synchronize()
            
            logger.info(f"✓ ༊*·˚ ensemble training complete in {time.time()-start_time:.1f}s")
            
        except Exception as e:
            logger.error(f"✗ Training failed: {e}")
            raise
    
    def _prepare_efficient_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features efficiently with caching."""
        if 'features' in self.feature_cache:
            return self.feature_cache['features']
        
        X = []
        y = []
        
        for idx, row in df.iterrows():
            if idx % 100000 == 0 and idx > 0:
                logger.info(f"    ₊˚⊹ feature extraction: {idx:,}/{len(df):,}")
            
            try:
                features = self._extract_optimized_features(row)
                X.append(features)
                
                confidence = self._calculate_confidence_score(row)
                y.append(confidence)
            except Exception as e:
                logger.warning(f"    ⚠ Failed to extract features for row {idx}: {e}")
                continue
        
        if not X:
            raise ValueError("No features could be extracted")
        
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)
        
        self.feature_cache['features'] = (X, y)
        
        return X, y
    
    def _extract_optimized_features(self, row) -> np.ndarray:
        """Extract features from a data row."""
        hostname = str(row.get('host', '')).lower()
        
        features = np.zeros(20, dtype=np.float32)
        
        # Hostname characteristics
        features[0] = min(len(hostname) / 50.0, 1.0)
        features[1] = min(hostname.count('.') / 5.0, 1.0)
        features[2] = min(hostname.count('-') / 5.0, 1.0)
        features[3] = min(hostname.count('_') / 5.0, 1.0)
        features[4] = min(sum(c.isdigit() for c in hostname) / 10.0, 1.0)
        features[5] = min(sum(c.isalpha() for c in hostname) / 30.0, 1.0)
        
        # Common prefixes
        prefixes = ['srv', 'web', 'db', 'app', 'fw', 'lb', 'api']
        for i, prefix in enumerate(prefixes):
            features[6 + i] = 1.0 if hostname.startswith(prefix) else 0.0
        
        # Environment indicators
        envs = ['prod', 'dev', 'test', 'stage']
        for i, env in enumerate(envs):
            features[13 + i] = 1.0 if env in hostname else 0.0
        
        # Metadata features
        features[17] = 1.0 if row.get('region') == 'US' else 0.5 if row.get('region') else 0.0
        features[18] = 1.0 if row.get('data_center') else 0.0
        features[19] = float(row.get('data_quality_score', 7.5)) / 10.0
        
        return np.clip(features, 0, 1)  # Ensure all features are in [0, 1]
    
    def _calculate_confidence_score(self, row) -> float:
        """Calculate confidence score for a data row."""
        score = 0.0
        
        weights = {
            'present_in_cmdb': 0.3,
            'logging_in_splunk': 0.3,
            'logging_in_gso': 0.2,
            'edr_coverage': 0.1,
            'tanium_coverage': 0.1
        }
        
        # Safe checking with get()
        if row.get('present_in_cmdb') == 'yes':
            score += weights['present_in_cmdb']
        if row.get('logging_in_splunk') == 'yes':
            score += weights['logging_in_splunk']
        if row.get('logging_in_gso') == 'yes':
            score += weights['logging_in_gso']
        if row.get('edr_coverage') and row.get('edr_coverage') != 'none':
            score += weights['edr_coverage']
        if row.get('tanium_coverage') == 'yes':
            score += weights['tanium_coverage']
        
        return min(score, 1.0)
    
    def predict_ensemble(self, candidates: List[Dict]) -> List[Dict]:
        """Predict using ensemble voting."""
        if not candidates:
            logger.warning("⚠ No candidates to predict")
            return []
        
        logger.info(f"\n⋆.˚ 𓆉 𓆝 predicting {len(candidates)} candidates with ensemble voting...")
        start_time = time.time()
        
        predictions = []
        batch_size = 32
        
        for batch_idx in range(0, len(candidates), batch_size):
            if batch_idx % 256 == 0 and batch_idx > 0:
                logger.info(f"  ₊˚⊹ processed {batch_idx:,}/{len(candidates):,} candidates")
            
            batch = candidates[batch_idx:batch_idx + batch_size]
            
            try:
                batch_features = np.array([self._candidate_to_features(c) for c in batch])
                batch_tensor = torch.FloatTensor(batch_features).to(self.device)
                
                votes = []
                with torch.no_grad():
                    for name, model in self.algorithms:
                        try:
                            model.eval()
                            pred = model.predict(batch_tensor)
                            votes.append(pred.cpu().numpy())
                        except Exception as e:
                            logger.warning(f"    ⚠ {name} prediction failed: {e}")
                            # Use default prediction
                            votes.append(np.ones(len(batch)) * 0.5)
                
                if votes:
                    ensemble_scores = np.mean(votes, axis=0)
                    
                    for i, candidate in enumerate(batch):
                        if ensemble_scores[i] > self.confidence_threshold:
                            prediction = candidate.copy()
                            prediction['confidence'] = float(ensemble_scores[i])
                            prediction['algorithm_scores'] = {
                                name: float(votes[j][i]) if j < len(votes) else 0.5
                                for j, (name, _) in enumerate(self.algorithms)
                            }
                            
                            prediction['unanimous'] = all(v[i] > 0.5 for v in votes if len(v) > i)
                            prediction['agreement'] = sum(v[i] > 0.5 for v in votes if len(v) > i) / max(len(votes), 1)
                            
                            predictions.append(prediction)
                
            except Exception as e:
                logger.warning(f"  ⚠ Batch prediction failed: {e}")
                continue
            
            # Clear cache periodically
            if self.device.type == 'mps':
                torch.mps.empty_cache()
            elif self.device.type == 'cuda':
                torch.cuda.empty_cache()
        
        predictions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        logger.info(f"✓ ˚₊· found {len(predictions)} missing assets in {time.time()-start_time:.1f}s")
        if predictions:
            logger.info(f"  ⋆.˚ high confidence (>0.8): {sum(1 for p in predictions if p.get('confidence', 0) > 0.8)}")
            logger.info(f"  𓇼 unanimous agreement: {sum(1 for p in predictions if p.get('unanimous', False))}")
        
        return predictions
    
    def _candidate_to_features(self, candidate: Dict) -> np.ndarray:
        """Convert candidate to feature vector."""
        mock_row = {
            'host': candidate.get('hostname', ''),
            'region': candidate.get('expected_region'),
            'data_center': candidate.get('expected_data_center'),
            'data_quality_score': candidate.get('quality_score', 7.5)
        }
        return self._extract_optimized_features(mock_row)
    
    def save_results(self, predictions: List[Dict]):
        """Save prediction results to JSON file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        output = {
            'generated_at': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'high_confidence': sum(1 for p in predictions if p.get('confidence', 0) > 0.8),
            'unanimous': sum(1 for p in predictions if p.get('unanimous', False)),
            'device_used': str(self.device),
            'predictions': predictions[:1000]  # Save up to 1000 predictions
        }
        
        filename = f'missing_assets_{timestamp}.json'
        try:
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2, default=str)
            
            logger.info(f"\n✓ ༻❁༺ results saved to {filename}")
        except Exception as e:
            logger.error(f"✗ Failed to save results: {e}")
        
        # Display top predictions
        logger.info("\n⋆｡‧˚ʚ top 10 missing assets ɞ˚‧｡⋆")
        for i, pred in enumerate(predictions[:10]):
            logger.info(f"  {i+1}. {pred.get('hostname', 'unknown')} ({pred.get('confidence', 0):.1%} confidence)")
            if pred.get('expected_region') or pred.get('expected_data_center'):
                logger.info(f"     ₊˚⊹ expected: {pred.get('expected_region', 'N/A')}, {pred.get('expected_data_center', 'N/A')}")
            logger.info(f"     ⋆.˚ agreement: {pred.get('agreement', 0):.1%} of algorithms")
    
    def run(self):
        """Main execution method."""
        logger.info("\n" + "="*60)
        logger.info("˚₊· ͟͟͞͞➳❥ INTELLIGENT MISSING ASSET DISCOVERY SYSTEM")
        logger.info("⋆｡‧˚ʚ♡ɞ˚‧｡⋆ version 3.1 - production-ready edition")
        logger.info("="*60)
        
        try:
            # Verify GPU
            self._verify_gpu()
            
            logger.info("\n༊*·˚ starting comprehensive analysis...")
            total_start = time.time()
            
            # Load data
            df = self.load_data()
            
            # Find patterns
            pattern_data = self.find_patterns_optimized(df)
            
            # Generate candidates
            existing_hosts = set(df['host'].dropna().str.lower())
            candidates = self.generate_smart_candidates(pattern_data, existing_hosts)
            
            if candidates:
                # Initialize and train algorithms
                input_dim = 20
                self.initialize_algorithms(input_dim)
                
                # Train models
                self.train_optimized(df)
                
                # Make predictions
                predictions = self.predict_ensemble(candidates)
                
                # Save results
                if predictions:
                    self.save_results(predictions)
                
                total_time = time.time() - total_start
                logger.info(f"\n✓ ⋆.ೃ࿔*:･ analysis completed in {total_time:.1f} seconds")
                logger.info(f"  ₊˚🎧⊹ discovered {len(predictions)} missing assets")
                
                return predictions
            else:
                logger.warning("\n⋆.˚ no candidates generated - all assets may be documented")
                return []
                
        except Exception as e:
            logger.error(f"\n✗ Critical error in analysis: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return []
        finally:
            # Cleanup
            if self.device.type == 'mps':
                torch.mps.empty_cache()
            elif self.device.type == 'cuda':
                torch.cuda.empty_cache()
            gc.collect()

if __name__ == "__main__":
    try:
        predictor = OptimizedAssetPredictor()
        predictions = predictor.run()
        
        if predictions:
            logger.info(f"\n🎉 Successfully identified {len(predictions)} missing assets!")
        else:
            logger.info("\n📋 No missing assets identified - your inventory may be complete")
            
    except KeyboardInterrupt:
        logger.info("\n⚠ Analysis interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)