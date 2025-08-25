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
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
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
                logger.error("✗ no gpu available - cannot proceed")
                exit(1)
        
        device = torch.device("mps")
        logger.info(f"✓ ‧₊˚🖇️✩ mps gpu detected on {platform.machine()}")
        logger.info(f"⋆.˚ 𓆉 macos version: {platform.mac_ver()[0]}")
        
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
        logger.info("₊˚🎧⊹♡ memory limit enforced at 18 gib")
        
        return device
    
    def _verify_gpu(self):
        logger.info("\n༻❁༺ running gpu verification tests...")
        try:
            test = torch.randn(1000, 1000, device=self.device)
            result = torch.matmul(test, test.T)
            del test, result
            
            if self.device.type == 'mps':
                torch.mps.empty_cache()
                torch.mps.synchronize()
            
            logger.info("✓ ⋆.˚ gpu computation verified successfully")
        except Exception as e:
            logger.error(f"✗ gpu test failed: {e}")
            exit(1)
    
    def load_data(self) -> pd.DataFrame:
        logger.info("\n⊹ ࣪ ˖ loading asset database...")
        start_time = time.time()
        
        conn = duckdb.connect(self.db_path, read_only=True)
        df = conn.execute("""
            SELECT * FROM universal_cmdb 
            WHERE host IS NOT NULL 
            ORDER BY host
        """).df()
        conn.close()
        
        logger.info(f"✓ ˚₊· loaded {len(df):,} records in {time.time()-start_time:.2f}s")
        logger.info(f"  𓇼 unique hostnames: {df['host'].nunique():,}")
        logger.info(f"  𓆉 business units: {df['business_unit'].nunique()}")
        logger.info(f"  𓆝 regions: {df['region'].nunique()}")
        
        return df
    
    def find_patterns_optimized(self, df: pd.DataFrame) -> Dict:
        logger.info("\n⋆˙⟡♡ discovering hostname patterns...")
        start_time = time.time()
        
        patterns = defaultdict(list)
        pattern_metadata = {}
        
        hostnames = df['host'].dropna().str.lower().str.strip()
        
        for idx, hostname in enumerate(hostnames):
            if idx % 50000 == 0 and idx > 0:
                logger.info(f"  ₊˚⊹ processed {idx:,}/{len(hostnames):,} hostnames")
            
            template = self._extract_template(hostname)
            patterns[template].append(hostname)
        
        legitimate = {}
        for template, hosts in patterns.items():
            if len(hosts) >= self.pattern_threshold:
                legitimate[template] = hosts
                pattern_metadata[template] = self._analyze_pattern_metadata(hosts, df)
        
        logger.info(f"✓ ˚₊· found {len(legitimate)} patterns in {time.time()-start_time:.2f}s")
        logger.info(f"  ⋆.˚ patterns with 3+ assets: {len(legitimate)}")
        logger.info(f"  𓆡 largest pattern: {max(len(h) for h in legitimate.values())} hosts")
        
        self.pattern_cache = legitimate
        return {'patterns': legitimate, 'metadata': pattern_metadata}
    
    def _extract_template(self, hostname: str) -> str:
        import re
        
        template = re.sub(r'\d+', 'NUM', hostname)
        
        template = re.sub(r'NUM(NUM)+', 'NUM', template)
        
        return template
    
    def _analyze_pattern_metadata(self, hosts: List[str], df: pd.DataFrame) -> Dict:
        sample_data = df[df['host'].str.lower().isin(hosts)]
        
        metadata = {
            'count': len(hosts),
            'regions': sample_data['region'].mode().iloc[0] if not sample_data['region'].empty else None,
            'business_units': sample_data['business_unit'].mode().iloc[0] if not sample_data['business_unit'].empty else None,
            'data_centers': sample_data['data_center'].mode().iloc[0] if not sample_data['data_center'].empty else None,
            'domains': self._extract_common_domain(hosts),
            'avg_quality_score': sample_data['data_quality_score'].mean() if 'data_quality_score' in sample_data else 0
        }
        
        return metadata
    
    def _extract_common_domain(self, hosts: List[str]) -> Optional[str]:
        domains = []
        for host in hosts[:10]:
            parts = host.split('.')
            if len(parts) > 1:
                domains.append('.'.join(parts[1:]))
        
        if domains:
            from collections import Counter
            most_common = Counter(domains).most_common(1)
            return most_common[0][0] if most_common else None
        return None
    
    def generate_smart_candidates(self, pattern_data: Dict, existing: set) -> List[Dict]:
        logger.info("\n༊*·˚ generating intelligent missing asset candidates...")
        start_time = time.time()
        
        candidates = []
        patterns = pattern_data['patterns']
        metadata = pattern_data['metadata']
        
        for template, hosts in patterns.items():
            if len(hosts) < 2:
                continue
            
            numbers_found = self._extract_number_sequences(hosts)
            
            for seq_pos, seq_values in numbers_found.items():
                gaps = self._find_intelligent_gaps(seq_values)
                
                for gap in gaps[:50]:
                    candidate = self._create_candidate(
                        template, gap, seq_pos, hosts[0], 
                        metadata.get(template, {}), existing
                    )
                    
                    if candidate and candidate['hostname'] not in existing:
                        candidates.append(candidate)
        
        candidates = self._rank_candidates_by_likelihood(candidates)
        
        logger.info(f"✓ ⋆.ೃ࿔*:･ generated {len(candidates)} candidates in {time.time()-start_time:.2f}s")
        logger.info(f"  ˚₊· high probability: {sum(1 for c in candidates if c.get('likelihood', 0) > 0.7)}")
        
        return candidates
    
    def _extract_number_sequences(self, hosts: List[str]) -> Dict:
        import re
        sequences = defaultdict(set)
        
        for host in hosts:
            for match in re.finditer(r'\d+', host):
                sequences[match.start()].add(int(match.group()))
        
        return {k: sorted(v) for k, v in sequences.items()}
    
    def _find_intelligent_gaps(self, sequence: List[int]) -> List[int]:
        if len(sequence) < 2:
            return []
        
        gaps = []
        
        for i in range(len(sequence) - 1):
            if sequence[i+1] - sequence[i] > 1:
                for missing in range(sequence[i] + 1, min(sequence[i+1], sequence[i] + 10)):
                    gaps.append(missing)
        
        if len(sequence) >= 3:
            diffs = [sequence[i+1] - sequence[i] for i in range(len(sequence)-1)]
            common_diff = max(set(diffs), key=diffs.count)
            
            if common_diff > 0:
                next_expected = sequence[-1] + common_diff
                if next_expected not in sequence and next_expected < 1000:
                    gaps.append(next_expected)
                
                prev_expected = sequence[0] - common_diff
                if prev_expected > 0 and prev_expected not in sequence:
                    gaps.append(prev_expected)
        
        return gaps
    
    def _create_candidate(self, template: str, number: int, position: int, 
                         sample_host: str, metadata: Dict, existing: set) -> Optional[Dict]:
        import re
        
        candidate_host = template
        num_str = str(number)
        
        if len(str(number)) == len(re.findall(r'\d+', sample_host)[0]) - 1:
            num_str = num_str.zfill(len(re.findall(r'\d+', sample_host)[0]))
        
        candidate_host = re.sub('NUM', num_str, candidate_host, count=1)
        
        if candidate_host in existing:
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
            'pattern_strength': metadata.get('count', 0) / 100.0,
            'quality_score': metadata.get('avg_quality_score', 0),
            'likelihood': 0.5
        }
    
    def _rank_candidates_by_likelihood(self, candidates: List[Dict]) -> List[Dict]:
        for candidate in candidates:
            score = 0.5
            
            if candidate.get('pattern_strength', 0) > 0.1:
                score += 0.2
            
            if candidate.get('quality_score', 0) > 7:
                score += 0.1
            
            if candidate.get('expected_region'):
                score += 0.1
            
            if candidate.get('expected_business_unit'):
                score += 0.1
            
            candidate['likelihood'] = min(score, 1.0)
        
        return sorted(candidates, key=lambda x: x['likelihood'], reverse=True)
    
    def initialize_algorithms(self, input_dim: int):
        logger.info("\n⋆｡‧˚ʚ initializing 10 neural architectures on gpu ɞ˚‧｡⋆")
        
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
    
    def train_optimized(self, df: pd.DataFrame):
        logger.info("\n˚ ༘♡ ⋆｡˚ training neural ensemble...")
        start_time = time.time()
        
        X, y = self._prepare_efficient_features(df)
        
        max_samples = 8000
        if len(X) > max_samples:
            logger.info(f"  ⋆.˚ sampling {max_samples} from {len(X)} for memory efficiency")
            indices = np.random.choice(len(X), max_samples, replace=False)
            X = X[indices]
            y = y[indices]
        
        split_idx = int(0.8 * len(X))
        X_train = torch.FloatTensor(X[:split_idx]).to(self.device)
        y_train = torch.FloatTensor(y[:split_idx]).to(self.device)
        X_val = torch.FloatTensor(X[split_idx:]).to(self.device)
        y_val = torch.FloatTensor(y[split_idx:]).to(self.device)
        
        for i, (name, model) in enumerate(self.algorithms):
            logger.info(f"  ₊˚🎧⊹ training {name} ({i+1}/10)...")
            
            if self.device.type == 'mps':
                torch.mps.empty_cache()
            
            try:
                model.train_model(X_train, y_train, X_val, y_val, epochs=20)
                logger.info(f"    ✓ {name} converged successfully")
            except RuntimeError as e:
                if "memory" in str(e).lower():
                    logger.warning(f"    ⋆ reducing batch for {name}")
                    model.train_model(X_train[:1000], y_train[:1000], 
                                    X_val[:200], y_val[:200], epochs=10)
                else:
                    raise e
            
            if self.device.type == 'mps':
                torch.mps.synchronize()
        
        logger.info(f"✓ ༊*·˚ ensemble training complete in {time.time()-start_time:.1f}s")
    
    def _prepare_efficient_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        if 'features' in self.feature_cache:
            return self.feature_cache['features']
        
        X = []
        y = []
        
        for idx, row in df.iterrows():
            if idx % 100000 == 0 and idx > 0:
                logger.info(f"    ₊˚⊹ feature extraction: {idx:,}/{len(df):,}")
            
            features = self._extract_optimized_features(row)
            X.append(features)
            
            confidence = self._calculate_confidence_score(row)
            y.append(confidence)
        
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)
        
        self.feature_cache['features'] = (X, y)
        
        return X, y
    
    def _extract_optimized_features(self, row) -> np.ndarray:
        hostname = str(row.get('host', '')).lower()
        
        features = np.zeros(20, dtype=np.float32)
        
        features[0] = len(hostname) / 50.0
        features[1] = hostname.count('.') / 5.0
        features[2] = hostname.count('-') / 5.0
        features[3] = hostname.count('_') / 5.0
        features[4] = sum(c.isdigit() for c in hostname) / 10.0
        features[5] = sum(c.isalpha() for c in hostname) / 30.0
        
        prefixes = ['srv', 'web', 'db', 'app', 'fw', 'lb', 'api']
        for i, prefix in enumerate(prefixes):
            features[6 + i] = 1.0 if hostname.startswith(prefix) else 0.0
        
        envs = ['prod', 'dev', 'test', 'stage']
        for i, env in enumerate(envs):
            features[13 + i] = 1.0 if env in hostname else 0.0
        
        features[17] = 1.0 if row.get('region') == 'US' else 0.5 if row.get('region') else 0.0
        features[18] = 1.0 if row.get('data_center') else 0.0
        features[19] = float(row.get('data_quality_score', 5.0)) / 10.0
        
        return features
    
    def _calculate_confidence_score(self, row) -> float:
        score = 0.0
        
        weights = {
            'present_in_cmdb': 0.3,
            'logging_in_splunk': 0.3,
            'logging_in_gso': 0.2,
            'edr_coverage': 0.1,
            'tanium_coverage': 0.1
        }
        
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
        logger.info(f"\n⋆.˚ 𓆉 𓆝 predicting {len(candidates)} candidates with ensemble voting...")
        start_time = time.time()
        
        predictions = []
        batch_size = 32
        
        for batch_idx in range(0, len(candidates), batch_size):
            if batch_idx % 256 == 0 and batch_idx > 0:
                logger.info(f"  ₊˚⊹ processed {batch_idx:,}/{len(candidates):,} candidates")
            
            batch = candidates[batch_idx:batch_idx + batch_size]
            batch_features = np.array([self._candidate_to_features(c) for c in batch])
            batch_tensor = torch.FloatTensor(batch_features).to(self.device)
            
            votes = []
            with torch.no_grad():
                for name, model in self.algorithms:
                    model.eval()
                    pred = model.predict(batch_tensor)
                    votes.append(pred.cpu().numpy())
            
            ensemble_scores = np.mean(votes, axis=0)
            
            for i, candidate in enumerate(batch):
                if ensemble_scores[i] > self.confidence_threshold:
                    prediction = candidate.copy()
                    prediction['confidence'] = float(ensemble_scores[i])
                    prediction['algorithm_scores'] = {
                        name: float(votes[j][i]) 
                        for j, (name, _) in enumerate(self.algorithms)
                    }
                    
                    prediction['unanimous'] = all(v[i] > 0.5 for v in votes)
                    prediction['agreement'] = sum(v[i] > 0.5 for v in votes) / len(votes)
                    
                    predictions.append(prediction)
            
            if self.device.type == 'mps':
                torch.mps.empty_cache()
        
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"✓ ˚₊· found {len(predictions)} missing assets in {time.time()-start_time:.1f}s")
        logger.info(f"  ⋆.˚ high confidence (>0.8): {sum(1 for p in predictions if p['confidence'] > 0.8)}")
        logger.info(f"  𓇼 unanimous agreement: {sum(1 for p in predictions if p.get('unanimous'))}")
        
        return predictions
    
    def _candidate_to_features(self, candidate: Dict) -> np.ndarray:
        mock_row = {
            'host': candidate['hostname'],
            'region': candidate.get('expected_region'),
            'data_center': candidate.get('expected_data_center'),
            'data_quality_score': candidate.get('quality_score', 7.5)
        }
        return self._extract_optimized_features(mock_row)
    
    def save_results(self, predictions: List[Dict]):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        output = {
            'generated_at': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'high_confidence': sum(1 for p in predictions if p['confidence'] > 0.8),
            'unanimous': sum(1 for p in predictions if p.get('unanimous')),
            'predictions': predictions[:100]
        }
        
        filename = f'missing_assets_{timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        logger.info(f"\n✓ ༻❁༺ results saved to {filename}")
        
        logger.info("\n⋆｡‧˚ʚ top 10 missing assets ɞ˚‧｡⋆")
        for i, pred in enumerate(predictions[:10]):
            logger.info(f"  {i+1}. {pred['hostname']} ({pred['confidence']:.1%} confidence)")
            logger.info(f"     ₊˚⊹ expected: {pred.get('expected_region')}, {pred.get('expected_data_center')}")
            logger.info(f"     ⋆.˚ agreement: {pred.get('agreement', 0):.1%} of algorithms")
    
    def run(self):
        logger.info("\n" + "="*60)
        logger.info("˚₊· ͟͟͞͞➳❥ INTELLIGENT MISSING ASSET DISCOVERY SYSTEM")
        logger.info("⋆｡‧˚ʚ♡ɞ˚‧｡⋆ version 3.0 - optimized for apple silicon")
        logger.info("="*60)
        
        self._verify_gpu()
        
        logger.info("\n༊*·˚ starting comprehensive analysis...")
        total_start = time.time()
        
        df = self.load_data()
        
        pattern_data = self.find_patterns_optimized(df)
        
        existing_hosts = set(df['host'].dropna().str.lower())
        candidates = self.generate_smart_candidates(pattern_data, existing_hosts)
        
        if candidates:
            input_dim = 20
            self.initialize_algorithms(input_dim)
            
            self.train_optimized(df)
            
            predictions = self.predict_ensemble(candidates)
            
            self.save_results(predictions)
            
            total_time = time.time() - total_start
            logger.info(f"\n✓ ⋆.ೃ࿔*:･ analysis completed in {total_time:.1f} seconds")
            logger.info(f"  ₊˚🎧⊹ discovered {len(predictions)} missing assets")
            
            return predictions
        else:
            logger.warning("\n⋆.˚ no candidates generated - all assets may be documented")
            return []

if __name__ == "__main__":
    predictor = OptimizedAssetPredictor()
    predictions = predictor.run()