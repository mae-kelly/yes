#!/usr/bin/env python3

import torch
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime
import json
import gc
import logging

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

if torch.cuda.is_available():
    device = torch.device("cuda")
    torch.cuda.set_per_process_memory_fraction(0.9)
    logger.info(f"Using GPU: {torch.cuda.get_device_name()}")
    logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    logger.error("GPU not available! This system requires GPU.")
    exit(1)

class MissingAssetPredictor:
    def __init__(self, db_path='universal_cmdb.db'):
        self.db_path = db_path
        self.algorithms = []
        self.pattern_threshold = 3
        
    def load_data(self):
        logger.info("Loading data from database...")
        conn = duckdb.connect(self.db_path)
        df = conn.execute("SELECT * FROM universal_cmdb ORDER BY host").df()
        conn.close()
        logger.info(f"Loaded {len(df)} records")
        return df
    
    def find_patterns(self, df):
        logger.info("Finding hostname patterns...")
        patterns = {}
        
        for hostname in df['host'].dropna():
            hostname = hostname.lower().strip()
            template = ''.join(['X' if c.isdigit() else c for c in hostname])
            
            if template not in patterns:
                patterns[template] = []
            patterns[template].append(hostname)
        
        legitimate_patterns = {
            k: v for k, v in patterns.items() 
            if len(v) >= self.pattern_threshold
        }
        
        logger.info(f"Found {len(legitimate_patterns)} patterns with {self.pattern_threshold}+ assets")
        
        return legitimate_patterns
    
    def generate_candidates(self, patterns, existing_hosts):
        logger.info("Generating missing asset candidates...")
        candidates = []
        existing_set = set(h.lower() for h in existing_hosts)
        
        for template, hosts in patterns.items():
            numbers_by_position = {}
            
            for host in hosts:
                for i, (t_char, h_char) in enumerate(zip(template, host)):
                    if t_char == 'X':
                        if i not in numbers_by_position:
                            numbers_by_position[i] = set()
                        numbers_by_position[i].add(h_char)
            
            if len(hosts) < 2:
                continue
                
            for host in hosts:
                host_numbers = []
                for i, char in enumerate(host):
                    if i < len(template) and template[i] == 'X':
                        host_numbers.append(int(char) if char.isdigit() else 0)
                
                if host_numbers:
                    for delta in [-3, -2, -1, 1, 2, 3]:
                        new_numbers = host_numbers.copy()
                        if new_numbers:
                            new_numbers[-1] = new_numbers[-1] + delta
                            
                            if 0 <= new_numbers[-1] <= 999:
                                new_host = list(host)
                                num_idx = 0
                                for i, char in enumerate(template):
                                    if char == 'X' and num_idx < len(new_numbers):
                                        new_host[i] = str(new_numbers[num_idx] % 10)
                                        num_idx += 1
                                
                                candidate_host = ''.join(new_host)
                                
                                if candidate_host not in existing_set:
                                    sample_data = df[df['host'].str.lower() == hosts[0].lower()].iloc[0] if len(df[df['host'].str.lower() == hosts[0].lower()]) > 0 else None
                                    
                                    candidates.append({
                                        'hostname': candidate_host,
                                        'pattern': template,
                                        'similar_hosts': hosts[:3],
                                        'expected_domain': sample_data.get('domain') if sample_data is not None else None,
                                        'expected_region': sample_data.get('region') if sample_data is not None else None,
                                        'expected_country': sample_data.get('country') if sample_data is not None else None,
                                        'expected_data_center': sample_data.get('data_center') if sample_data is not None else None,
                                        'expected_business_unit': sample_data.get('business_unit') if sample_data is not None else None
                                    })
        
        logger.info(f"Generated {len(candidates)} potential missing assets")
        return candidates
    
    def initialize_algorithms(self, input_dim):
        logger.info("Initializing 10 GPU-based ML algorithms...")
        
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
        
        for i, algo in enumerate(self.algorithms):
            logger.info(f"  Algorithm {i+1}: {algo.__class__.__name__}")
        
        return self.algorithms
    
    def train_algorithms(self, df):
        logger.info("Training all algorithms on GPU...")
        
        X, y = self.prepare_training_data(df)
        X_tensor = torch.FloatTensor(X).to(device)
        y_tensor = torch.FloatTensor(y).to(device)
        
        split = int(0.8 * len(X))
        X_train = X_tensor[:split]
        y_train = y_tensor[:split]
        X_val = X_tensor[split:]
        y_val = y_tensor[split:]
        
        for i, algo in enumerate(self.algorithms):
            logger.info(f"Training algorithm {i+1}/{len(self.algorithms)}: {algo.__class__.__name__}")
            algo.train_model(X_train, y_train, X_val, y_val)
            
            torch.cuda.empty_cache()
            gc.collect()
            
            memory_used = torch.cuda.memory_allocated() / 1e9
            logger.info(f"  GPU memory used: {memory_used:.2f} GB")
    
    def prepare_training_data(self, df):
        X = []
        y = []
        
        for _, row in df.iterrows():
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
        
        return np.array(X), np.array(y)
    
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
        logger.info(f"Predicting {len(candidates)} candidates using ensemble voting...")
        
        predictions = []
        
        batch_size = 100
        for batch_start in range(0, len(candidates), batch_size):
            batch_end = min(batch_start + batch_size, len(candidates))
            batch = candidates[batch_start:batch_end]
            
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
                algo_predictions = algo.predict(batch_tensor)
                votes.append(algo_predictions.cpu().numpy())
            
            ensemble_predictions = np.mean(votes, axis=0)
            
            for i, candidate in enumerate(batch):
                confidence = ensemble_predictions[i]
                
                if confidence > 0.5:
                    individual_scores = [votes[j][i] for j in range(len(self.algorithms))]
                    
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
                            'LSTM': float(individual_scores[0]),
                            'GRU': float(individual_scores[1]),
                            'Transformer': float(individual_scores[2]),
                            'CNN': float(individual_scores[3]),
                            'Autoencoder': float(individual_scores[4]),
                            'VAE': float(individual_scores[5]),
                            'Attention': float(individual_scores[6]),
                            'Residual': float(individual_scores[7]),
                            'EnsembleNN': float(individual_scores[8]),
                            'GraphNN': float(individual_scores[9])
                        }
                    })
            
            torch.cuda.empty_cache()
            
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"Found {len(predictions)} high-confidence missing assets")
        
        return predictions
    
    def run(self):
        df = self.load_data()
        
        patterns = self.find_patterns(df)
        
        existing_hosts = df['host'].dropna().tolist()
        candidates = self.generate_candidates(patterns, existing_hosts)
        
        input_dim = len(self.extract_features(df.iloc[0]))
        self.initialize_algorithms(input_dim)
        
        self.train_algorithms(df)
        
        predictions = self.predict_candidates(candidates, df)
        
        self.save_results(predictions)
        
        return predictions
    
    def save_results(self, predictions):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'missing_assets_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(predictions[:100], f, indent=2)
        
        logger.info(f"Results saved to {filename}")
        
        logger.info("\nTop 10 Missing Assets:")
        for i, pred in enumerate(predictions[:10]):
            logger.info(f"{i+1}. {pred['hostname']} (confidence: {pred['confidence']:.2%})")
            logger.info(f"   Expected: {pred['expected_fqdn']}, {pred['expected_region']}, {pred['expected_data_center']}")

if __name__ == "__main__":
    predictor = MissingAssetPredictor()
    predictions = predictor.run()