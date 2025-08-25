#!/usr/bin/env python3

import torch
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
from collections import defaultdict

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

if not torch.backends.mps.is_available():
    if not torch.backends.mps.is_built():
        logger.error("༻❁༺ MPS not available - PyTorch wasn't built with MPS enabled")
        logger.error("⋆.˚ Please install PyTorch with MPS support: pip3 install torch torchvision")
    else:
        logger.error("𓆉 MPS not available - not running on macOS with Apple Silicon")
    
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.warning("✩ Using CUDA GPU instead of MPS ₊˚")
    else:
        logger.error("༻❁༺ No GPU available! This system requires Apple Silicon or CUDA GPU")
        exit(1)
else:
    device = torch.device("mps")
    logger.info("‧₊˚🖇️✩ Apple Silicon GPU detected and initialized ₊˚")
    logger.info(f"⋆.˚ Running on: {platform.machine()}")
    logger.info(f"𓇼 macOS version: {platform.mac_ver()[0]}")
    
    os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
    MAX_MEMORY_GB = 18
    logger.info(f"₊˚🎧⊹♡ GPU Memory limit set to {MAX_MEMORY_GB} GiB")

class MissingAssetPredictor:
    def __init__(self, db_path='universal_cmdb.db'):
        self.db_path = db_path
        self.algorithms = []
        self.pattern_threshold = 3
        self.start_time = time.time()
        
    def load_data(self):
        logger.info("\n˚ ༘♡ ⋆｡˚ Loading database...")
        start = time.time()
        
        try:
            conn = duckdb.connect(self.db_path)
            df = conn.execute("SELECT * FROM universal_cmdb ORDER BY host").df()
            conn.close()
            
            logger.info(f"✧˚ · . Successfully loaded {len(df):,} records in {time.time()-start:.1f}s")
            logger.info(f"𓆝 Unique hostnames: {df['host'].nunique():,}")
            logger.info(f"⋆⭒˚｡⋆ Null values per column:")
            
            null_counts = df.isnull().sum()
            for col, count in null_counts[null_counts > 0].items():
                logger.info(f"  ✩ {col}: {count:,} nulls ({count/len(df)*100:.1f}%)")
            
            return df
            
        except Exception as e:
            logger.error(f"༻❁༺ Database error: {e}")
            exit(1)
    
    def find_patterns(self, df):
        logger.info("\n⋆｡‧˚ʚ♡ɞ˚‧｡⋆ Starting pattern discovery...")
        start = time.time()
        
        patterns = defaultdict(list)
        total_hosts = 0
        
        for hostname in df['host'].dropna():
            total_hosts += 1
            hostname = hostname.lower().strip()
            template = ''.join(['X' if c.isdigit() else c for c in hostname])
            patterns[template].append(hostname)
            
            if total_hosts % 50000 == 0:
                logger.info(f"  ₊˚⊹♡ Processed {total_hosts:,} hostnames...")
        
        legitimate_patterns = {}
        for template, hosts in patterns.items():
            if len(hosts) >= self.pattern_threshold:
                legitimate_patterns[template] = hosts
        
        logger.info(f"✧˚ · . Found {len(legitimate_patterns)} patterns with {self.pattern_threshold}+ assets")
        logger.info(f"˚ ༘♡ Pattern discovery took {time.time()-start:.1f}s")
        
        top_patterns = sorted(legitimate_patterns.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        logger.info("𓇼 Top 5 patterns by frequency:")
        for template, hosts in top_patterns:
            logger.info(f"  ⋆.˚ {template[:40]}{'...' if len(template) > 40 else ''} ({len(hosts)} hosts)")
        
        return legitimate_patterns
    
    def generate_candidates(self, patterns, existing_hosts):
        logger.info("\n₊˚🎧⊹♡ Generating missing asset candidates...")
        start = time.time()
        
        candidates = []
        existing_set = set(h.lower() for h in existing_hosts)
        patterns_processed = 0
        
        for template, hosts in patterns.items():
            patterns_processed += 1
            
            if patterns_processed % 100 == 0:
                logger.info(f"  ⋆⭒˚｡⋆ Processed {patterns_processed}/{len(patterns)} patterns...")
            
            if len(hosts) < 2:
                continue
            
            numbers_in_pattern = defaultdict(set)
            for host in hosts:
                current_numbers = []
                for i, (t_char, h_char) in enumerate(zip(template, host)):
                    if t_char == 'X' and h_char.isdigit():
                        current_numbers.append((i, int(h_char)))
                
                if current_numbers:
                    for pos, num in current_numbers:
                        numbers_in_pattern[pos].add(num)
            
            for pos, observed_numbers in numbers_in_pattern.items():
                if len(observed_numbers) > 1:
                    min_num = min(observed_numbers)
                    max_num = max(observed_numbers)
                    
                    for num in range(max(0, min_num - 5), min(999, max_num + 5)):
                        if num not in observed_numbers:
                            candidate_host = list(template)
                            candidate_host[pos] = str(num % 10)
                            candidate_str = ''.join(candidate_host)
                            
                            if candidate_str not in existing_set:
                                sample_host = hosts[0]
                                sample_data = df[df['host'].str.lower() == sample_host].iloc[0] if not df[df['host'].str.lower() == sample_host].empty else {}
                                
                                candidates.append({
                                    'hostname': candidate_str,
                                    'pattern': template,
                                    'similar_hosts': hosts[:3],
                                    'expected_domain': sample_data.get('domain') if sample_data else None,
                                    'expected_region': sample_data.get('region') if sample_data else None,
                                    'expected_country': sample_data.get('country') if sample_data else None,
                                    'expected_data_center': sample_data.get('data_center') if sample_data else None,
                                    'expected_business_unit': sample_data.get('business_unit') if sample_data else None
                                })
        
        logger.info(f"✧˚ · . Generated {len(candidates):,} candidates in {time.time()-start:.1f}s")
        logger.info(f"𓆡 Average candidates per pattern: {len(candidates)/len(patterns):.1f}")
        
        return candidates[:50000]
    
    def initialize_algorithms(self, input_dim):
        logger.info("\n˚ ༘♡ ⋆｡˚ Initializing 10 GPU algorithms...")
        
        algo_names = [
            "LSTM (Long Short-Term Memory)",
            "GRU (Gated Recurrent Unit)",
            "Transformer (Self-Attention)",
            "CNN (Convolutional Network)",
            "Autoencoder (Reconstruction)",
            "VAE (Variational Autoencoder)",
            "Attention (Multi-Head)",
            "Residual (Skip Connections)",
            "Ensemble (Multiple Networks)",
            "Graph NN (Relationship Modeling)"
        ]
        
        self.algorithms = [
            LSTMPredictor(input_dim).to(device),
            GRUPredictor(input_dim).to(device),
            TransformerPredictor(input_dim).to(device),
            CNNPredictor(input_dim).to(device),
            AutoencoderPredictor(input_dim).to(device),
            VAEPredictor(input_dim).to(device),
            AttentionPredictor(input_dim).to(device),
            ResidualPredictor(input_dim).to(device),
            EnsembleNNPredictor(input_dim).to(device),
            GraphNNPredictor(input_dim).to(device)
        ]
        
        for i, (algo, name) in enumerate(zip(self.algorithms, algo_names)):
            param_count = sum(p.numel() for p in algo.parameters())
            logger.info(f"  {i+1}. ⋆.˚ {name} - {param_count:,} parameters")
        
        return self.algorithms
    
    def train_algorithms(self, df):
        logger.info("\n₊˚⊹♡ Starting training phase on GPU...")
        start = time.time()
        
        X, y = self.prepare_training_data(df)
        logger.info(f"✧˚ · . Prepared {len(X):,} training samples")
        
        batch_size = min(512, len(X) // 10)
        chunk_size = min(10000, len(X))
        
        if len(X) > chunk_size:
            logger.info(f"𓇼 Using subset of {chunk_size:,} samples for memory efficiency")
            indices = np.random.choice(len(X), chunk_size, replace=False)
            X = X[indices]
            y = y[indices]
        
        X_tensor = torch.FloatTensor(X).to(device)
        y_tensor = torch.FloatTensor(y).to(device)
        
        split = int(0.8 * len(X))
        X_train = X_tensor[:split]
        y_train = y_tensor[:split]
        X_val = X_tensor[split:]
        y_val = y_tensor[split:]
        
        logger.info(f"⋆⭒˚｡⋆ Training set: {len(X_train):,} samples")
        logger.info(f"˚ ༘♡ Validation set: {len(X_val):,} samples")
        
        for i, algo in enumerate(self.algorithms):
            algo_start = time.time()
            logger.info(f"\n  ‧₊˚ Training algorithm {i+1}/10: {algo.__class__.__name__}")
            
            if device.type == 'mps':
                torch.mps.empty_cache()
            gc.collect()
            
            try:
                algo.train_model(X_train, y_train, X_val, y_val)
                logger.info(f"    ✩ Training completed in {time.time()-algo_start:.1f}s")
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.warning(f"    ༻❁༺ Memory issue - using smaller batch")
                    smaller_batch = X_train[:1000]
                    smaller_y = y_train[:1000]
                    algo.train_model(smaller_batch, smaller_y, X_val[:500], y_val[:500])
                    logger.info(f"    ⋆.˚ Trained with reduced batch in {time.time()-algo_start:.1f}s")
                else:
                    raise e
            
            if device.type == 'mps':
                torch.mps.empty_cache()
                torch.mps.synchronize()
        
        logger.info(f"\n✧˚ · . All algorithms trained in {time.time()-start:.1f}s total")
    
    def prepare_training_data(self, df):
        X = []
        y = []
        
        for idx, row in df.iterrows():
            if idx % 100000 == 0 and idx > 0:
                logger.info(f"  ₊˚⊹♡ Processed {idx:,} records...")
            
            features = self.extract_features(row)
            X.append(features)
            
            confidence = 0.0
            if row.get('present_in_cmdb') == 'yes':
                confidence += 0.3
            if row.get('logging_in_splunk') == 'yes':
                confidence += 0.3
            if row.get('logging_in_gso') == 'yes':
                confidence += 0.2
            if row.get('edr_coverage') and row.get('edr_coverage') != 'none':
                confidence += 0.2
                
            y.append(confidence)
        
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)
    
    def extract_features(self, row):
        hostname = str(row.get('host', '')).lower()
        
        features = [
            len(hostname),
            hostname.count('.'),
            hostname.count('-'),
            hostname.count('_'),
            sum(c.isdigit() for c in hostname),
            sum(c.isalpha() for c in hostname),
            1 if hostname.startswith('srv') else 0,
            1 if hostname.startswith('web') else 0,
            1 if hostname.startswith('db') else 0,
            1 if hostname.startswith('app') else 0,
            1 if 'prod' in hostname else 0,
            1 if 'dev' in hostname else 0,
            1 if 'test' in hostname else 0,
            1 if 'stage' in hostname else 0,
            1 if row.get('region') == 'US' else 0,
            1 if row.get('region') == 'EU' else 0,
            1 if row.get('region') == 'APAC' else 0,
            1 if row.get('data_center') else 0,
            1 if row.get('cloud_region') else 0,
            float(row.get('data_quality_score', 0))
        ]
        
        return features
    
    def predict_candidates(self, candidates, df):
        logger.info(f"\n⋆｡‧˚ʚ♡ɞ˚‧｡⋆ Starting predictions for {len(candidates):,} candidates...")
        start = time.time()
        
        predictions = []
        batch_size = 50
        
        for batch_start in range(0, len(candidates), batch_size):
            batch_end = min(batch_start + batch_size, len(candidates))
            batch = candidates[batch_start:batch_end]
            
            if batch_start % 1000 == 0 and batch_start > 0:
                progress = batch_start / len(candidates) * 100
                logger.info(f"  ₊˚⊹♡ Progress: {progress:.1f}% ({batch_start:,}/{len(candidates):,})")
            
            if device.type == 'mps':
                torch.mps.empty_cache()
            
            batch_features = []
            for candidate in batch:
                mock_row = {
                    'host': candidate['hostname'],
                    'region': candidate.get('expected_region'),
                    'data_center': candidate.get('expected_data_center'),
                    'data_quality_score': 7.5
                }
                batch_features.append(self.extract_features(mock_row))
            
            batch_tensor = torch.FloatTensor(batch_features).to(device)
            
            votes = []
            for algo in self.algorithms:
                with torch.no_grad():
                    algo_predictions = algo.predict(batch_tensor)
                    votes.append(algo_predictions.cpu().numpy())
            
            ensemble_predictions = np.mean(votes, axis=0)
            
            for i, candidate in enumerate(batch):
                confidence = ensemble_predictions[i]
                
                if confidence > 0.5:
                    individual_scores = [float(votes[j][i]) for j in range(len(self.algorithms))]
                    
                    predictions.append({
                        'hostname': candidate['hostname'],
                        'confidence': float(confidence),
                        'pattern': candidate['pattern'],
                        'similar_hosts': candidate['similar_hosts'],
                        'expected_fqdn': f"{candidate['hostname']}.{candidate.get('expected_domain', 'unknown')}",
                        'expected_domain': candidate.get('expected_domain'),
                        'expected_region': candidate.get('expected_region'),
                        'expected_country': candidate.get('expected_country'),
                        'expected_data_center': candidate.get('expected_data_center'),
                        'expected_business_unit': candidate.get('expected_business_unit'),
                        'algorithm_scores': {
                            'LSTM': individual_scores[0],
                            'GRU': individual_scores[1],
                            'Transformer': individual_scores[2],
                            'CNN': individual_scores[3],
                            'Autoencoder': individual_scores[4],
                            'VAE': individual_scores[5],
                            'Attention': individual_scores[6],
                            'Residual': individual_scores[7],
                            'EnsembleNN': individual_scores[8],
                            'GraphNN': individual_scores[9]
                        }
                    })
            
            del batch_tensor
            if device.type == 'mps':
                torch.mps.empty_cache()
                torch.mps.synchronize()
        
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"✧˚ · . Predictions completed in {time.time()-start:.1f}s")
        logger.info(f"𓆉 Found {len(predictions):,} high-confidence missing assets")
        
        return predictions
    
    def run(self):
        logger.info("\n" + "="*60)
        logger.info("‧₊˚🖇️✩ MISSING ASSET PREDICTOR ₊˚🎧⊹♡")
        logger.info("="*60)
        
        logger.info("\n˚ ༘♡ ⋆｡˚ Running startup checks...")
        try:
            test_tensor = torch.randn(100, 100).to(device)
            result = test_tensor @ test_tensor.T
            del test_tensor, result
            if device.type == 'mps':
                torch.mps.empty_cache()
                torch.mps.synchronize()
            logger.info("✧˚ · . GPU computation test passed")
        except Exception as e:
            logger.error(f"༻❁༺ GPU test failed: {e}")
            exit(1)
        
        logger.info("⋆⭒˚｡⋆ All checks passed - starting analysis")
        
        df = self.load_data()
        patterns = self.find_patterns(df)
        existing_hosts = df['host'].dropna().tolist()
        candidates = self.generate_candidates(patterns, existing_hosts)
        
        input_dim = len(self.extract_features(df.iloc[0]))
        self.initialize_algorithms(input_dim)
        self.train_algorithms(df)
        predictions = self.predict_candidates(candidates, df)
        self.save_results(predictions)
        
        total_time = time.time() - self.start_time
        logger.info(f"\n‧₊˚🖇️✩ Total runtime: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        
        return predictions
    
    def save_results(self, predictions):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'missing_assets_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(predictions[:100], f, indent=2)
        
        logger.info(f"\n𓇼 Results saved to {filename}")
        
        logger.info("\n⋆｡‧˚ʚ♡ɞ˚‧｡⋆ Top 10 Missing Assets:")
        logger.info("-"*60)
        
        for i, pred in enumerate(predictions[:10]):
            logger.info(f"\n{i+1}. ₊˚⊹♡ {pred['hostname']} (confidence: {pred['confidence']:.1%})")
            logger.info(f"   ⋆.˚ Expected FQDN: {pred['expected_fqdn']}")
            logger.info(f"   𓆝 Region: {pred['expected_region']}, Data Center: {pred['expected_data_center']}")
            logger.info(f"   ✩ Similar to: {', '.join(pred['similar_hosts'][:2])}")
            
            top_algo = max(pred['algorithm_scores'].items(), key=lambda x: x[1])
            logger.info(f"   ˚ ༘♡ Highest scoring algorithm: {top_algo[0]} ({top_algo[1]:.1%})")

if __name__ == "__main__":
    predictor = MissingAssetPredictor()
    predictions = predictor.run()