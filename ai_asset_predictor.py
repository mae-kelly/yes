import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import pandas as pd
import re
import duckdb
from sklearn.preprocessing import StandardScaler
from flask import Flask, jsonify
import threading
from datetime import datetime
import os
import pickle
import json
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
from functools import lru_cache
import gc
import time

if torch.backends.mps.is_available():
    device = torch.device("mps")
    torch.mps.empty_cache()
    torch.mps.set_per_process_memory_fraction(0.9)
    print(f"[GPU] Apple Silicon MPS activated - 18GB limit enforced")
else:
    device = torch.device("cpu")
    print("[CPU] Fallback mode")

@dataclass
class ModelConfig:
    hidden_dims: List[int] = None
    batch_size: int = 256
    learning_rate: float = 0.002
    epochs: int = 50
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [384, 256, 128, 64]

class DataCache:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_file = f'{cache_dir}/processed_data.pkl'
        self.metadata_file = f'{cache_dir}/metadata.json'
        
    def get_table_hash(self, df: pd.DataFrame) -> str:
        return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()
    
    def is_cached(self, df: pd.DataFrame) -> bool:
        if not os.path.exists(self.metadata_file):
            return False
        
        current_hash = self.get_table_hash(df)
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if metadata.get('table_hash') == current_hash:
            print(f"[CACHE] Data unchanged since {metadata['timestamp']}")
            return True
        return False
    
    def save(self, df: pd.DataFrame, features: np.ndarray, labels: Tuple):
        print("[CACHE] Saving processed data...")
        with open(self.cache_file, 'wb') as f:
            pickle.dump({
                'features': features,
                'labels': labels
            }, f)
        
        metadata = {
            'table_hash': self.get_table_hash(df),
            'timestamp': datetime.now().isoformat(),
            'rows': len(df),
            'feature_dim': features.shape[1] if len(features.shape) > 1 else 0
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f)
        print(f"[CACHE] Saved {len(df)} processed records")
    
    def load(self) -> Tuple[np.ndarray, Tuple]:
        print("[CACHE] Loading processed data...")
        with open(self.cache_file, 'rb') as f:
            data = pickle.load(f)
        return data['features'], data['labels']

class FastTransformer(nn.Module):
    def __init__(self, input_dim: int, config: ModelConfig):
        super().__init__()
        
        layers = []
        current_dim = input_dim
        
        for hidden_dim in config.hidden_dims:
            layers.extend([
                nn.Linear(current_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU(),
                nn.Dropout(0.1)
            ])
            current_dim = hidden_dim
        
        layers.append(nn.Linear(current_dim, 1))
        
        self.network = nn.Sequential(*layers)
        self.to(device)
        
        params = sum(p.numel() for p in self.parameters())
        print(f"[MODEL] FastTransformer: {params:,} parameters")
    
    def forward(self, x):
        return self.network(x)

class FastMoE(nn.Module):
    def __init__(self, input_dim: int, num_classes: int = 5):
        super().__init__()
        
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, 128),
                nn.GELU(),
                nn.Linear(128, num_classes)
            ) for _ in range(3)
        ])
        
        self.gate = nn.Linear(input_dim, 3)
        self.to(device)
        
        params = sum(p.numel() for p in self.parameters())
        print(f"[MODEL] FastMoE: {params:,} parameters")
    
    def forward(self, x):
        gates = F.softmax(self.gate(x), dim=1)
        expert_outputs = torch.stack([expert(x) for expert in self.experts], dim=1)
        return torch.einsum('bi,bij->bj', gates, expert_outputs)

class FeatureExtractor:
    def __init__(self):
        self.dim = 64
        self.cache = {}
        
    @lru_cache(maxsize=100000)
    def extract(self, hostname: str) -> np.ndarray:
        if not hostname:
            return np.zeros(self.dim)
        
        h = hostname.lower()
        
        features = [
            len(h) / 50.0,
            h.count('.') / 5.0,
            h.count('-') / 5.0,
            len(re.findall(r'\d+', h)) / 5.0,
            len(set(h)) / len(h),
            self._entropy(h),
        ]
        
        keywords = ['srv', 'web', 'db', 'app', 'prod', 'dev', 'test', 'cloud', 
                   'fw', 'api', 'node', 'host', '1dc', 'fead', 'aws', 'azure']
        for kw in keywords:
            features.append(1.0 if kw in h else 0.0)
        
        numbers = re.findall(r'\d+', h)
        if numbers:
            nums = [float(n) for n in numbers]
            features.extend([
                np.mean(nums) / 100.0,
                np.std(nums) / 100.0 if len(nums) > 1 else 0,
                np.max(nums) / 100.0,
                len(nums) / 10.0
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        pattern_hash = int(hashlib.md5(re.sub(r'\d+', 'X', h).encode()).hexdigest()[:8], 16)
        for i in range(8):
            features.append(np.sin(pattern_hash / (10000 ** (i / 8))))
        
        while len(features) < self.dim:
            features.append(0.0)
        
        return np.array(features[:self.dim], dtype=np.float32)
    
    def _entropy(self, s: str) -> float:
        if not s:
            return 0
        prob = [s.count(c) / len(s) for c in set(s)]
        return -sum([p * np.log2(p) for p in prob if p > 0])

class AO1Predictor:
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        print("\n" + "="*60)
        print("AO1 PREDICTOR v4.0 - ULTRA FAST GPU")
        print("="*60)
        
        self.db_path = db_path
        self.model_dir = 'models'
        self.config = ModelConfig()
        self.cache = DataCache()
        self.feature_extractor = FeatureExtractor()
        self.scaler = StandardScaler()
        
        self.existence_model = None
        self.visibility_model = None
        self.trained = False
        self.training_time = 0
        
        os.makedirs(self.model_dir, exist_ok=True)
        self._log_memory("Init")
    
    def _log_memory(self, tag=""):
        if device.type == 'mps':
            used = torch.mps.driver_allocated_memory() / 1e9
            free = 18.0 - used
            print(f"[MEM] {tag}: {used:.1f}GB used, {free:.1f}GB free")
            if used > 16:
                torch.mps.empty_cache()
                print("[MEM] Cache cleared")
    
    def get_data(self) -> pd.DataFrame:
        print("[DATA] Loading from database...")
        try:
            conn = duckdb.connect(self.db_path)
            df = conn.execute("""
                SELECT host, business_unit, region, system_classification,
                       logging_in_splunk, logging_in_gso, present_in_cmdb,
                       edr_coverage, data_quality_score, source_count
                FROM universal_cmdb
            """).df()
            conn.close()
            print(f"[DATA] Loaded {len(df)} records")
            return df
        except Exception as e:
            print(f"[ERROR] {e}")
            return pd.DataFrame()
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.cache.is_cached(df):
            return self.cache.load()
        
        print("[PREP] Processing data...")
        start = time.time()
        
        features = []
        exist_labels = []
        vis_labels = []
        
        for idx, row in df.iterrows():
            if idx % 1000 == 0:
                print(f"[PREP] {idx}/{len(df)} records processed")
            
            host_features = self.feature_extractor.extract(row['host'])
            
            context = np.array([
                1 if pd.notna(row.get('business_unit')) else 0,
                1 if pd.notna(row.get('region')) else 0,
                1 if pd.notna(row.get('system_classification')) else 0,
                float(row.get('data_quality_score', 0)) / 10,
                np.log1p(float(row.get('source_count', 0))) / 5,
            ], dtype=np.float32)
            
            combined = np.concatenate([host_features, context])
            features.append(combined)
            
            exist_score = 0
            if row.get('logging_in_splunk') == 'yes':
                exist_score += 0.4
            if row.get('present_in_cmdb') == 'yes':
                exist_score += 0.3
            if pd.notna(row.get('edr_coverage')):
                exist_score += 0.3
            exist_labels.append(min(exist_score, 1.0))
            
            vis_class = 0
            if row.get('logging_in_splunk') == 'yes' and row.get('logging_in_gso') == 'yes':
                vis_class = 4
            elif row.get('logging_in_splunk') == 'yes':
                vis_class = 3
            elif row.get('logging_in_gso') == 'yes':
                vis_class = 2
            elif row.get('present_in_cmdb') == 'yes':
                vis_class = 1
            vis_labels.append(vis_class)
        
        X = np.array(features, dtype=np.float32)
        y_exist = np.array(exist_labels, dtype=np.float32)
        y_vis = np.array(vis_labels, dtype=np.int64)
        
        print(f"[PREP] Completed in {time.time() - start:.1f}s")
        
        self.cache.save(df, X, (y_exist, y_vis))
        
        return X, y_exist, y_vis
    
    def train(self):
        print("\n[TRAIN] Starting fast training...")
        start = time.time()
        
        df = self.get_data()
        if df.empty:
            return
        
        X, y_exist, y_vis = self.prepare_data(df)
        X = self.scaler.fit_transform(X)
        
        input_dim = X.shape[1]
        print(f"[TRAIN] Input dimension: {input_dim}")
        
        self.existence_model = FastTransformer(input_dim, self.config)
        self.visibility_model = FastMoE(input_dim, num_classes=5)
        
        self._log_memory("Models built")
        
        X_tensor = torch.tensor(X, dtype=torch.float32, device=device)
        y_exist_tensor = torch.tensor(y_exist.reshape(-1, 1), dtype=torch.float32, device=device)
        y_vis_tensor = torch.tensor(y_vis, dtype=torch.long, device=device)
        
        dataset = torch.utils.data.TensorDataset(X_tensor, y_exist_tensor, y_vis_tensor)
        
        train_size = int(0.85 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(42)
        )
        
        train_loader = torch.utils.data.DataLoader(
            train_dataset, 
            batch_size=self.config.batch_size,
            shuffle=True
        )
        
        val_loader = torch.utils.data.DataLoader(
            val_dataset,
            batch_size=self.config.batch_size * 2,
            shuffle=False
        )
        
        opt1 = optim.AdamW(self.existence_model.parameters(), lr=self.config.learning_rate)
        opt2 = optim.AdamW(self.visibility_model.parameters(), lr=self.config.learning_rate)
        
        criterion1 = nn.BCEWithLogitsLoss()
        criterion2 = nn.CrossEntropyLoss()
        
        best_loss = float('inf')
        patience = 0
        
        print(f"[TRAIN] Training for {self.config.epochs} epochs...")
        
        for epoch in range(self.config.epochs):
            epoch_start = time.time()
            
            self.existence_model.train()
            self.visibility_model.train()
            
            train_loss1 = 0
            train_loss2 = 0
            
            for batch_x, batch_y_exist, batch_y_vis in train_loader:
                opt1.zero_grad()
                out1 = self.existence_model(batch_x)
                loss1 = criterion1(out1, batch_y_exist)
                loss1.backward()
                opt1.step()
                train_loss1 += loss1.item()
                
                opt2.zero_grad()
                out2 = self.visibility_model(batch_x)
                loss2 = criterion2(out2, batch_y_vis)
                loss2.backward()
                opt2.step()
                train_loss2 += loss2.item()
            
            if epoch % 5 == 0:
                val_loss1, val_loss2 = self._validate(val_loader, criterion1, criterion2)
                total_val_loss = val_loss1 + val_loss2
                
                print(f"[EPOCH {epoch:2d}] {time.time() - epoch_start:.1f}s | "
                      f"Train: {train_loss1/len(train_loader):.3f}/{train_loss2/len(train_loader):.3f} | "
                      f"Val: {val_loss1:.3f}/{val_loss2:.3f}")
                
                if total_val_loss < best_loss:
                    best_loss = total_val_loss
                    patience = 0
                    self.save_models()
                else:
                    patience += 1
                    if patience > 5:
                        print("[TRAIN] Early stopping")
                        break
                
                self._log_memory(f"Epoch {epoch}")
        
        self.trained = True
        self.training_time = time.time() - start
        print(f"\n[SUCCESS] Training completed in {self.training_time:.1f}s")
    
    def _validate(self, loader, crit1, crit2):
        self.existence_model.eval()
        self.visibility_model.eval()
        
        loss1 = 0
        loss2 = 0
        
        with torch.no_grad():
            for batch_x, batch_y_exist, batch_y_vis in loader:
                out1 = self.existence_model(batch_x)
                out2 = self.visibility_model(batch_x)
                loss1 += crit1(out1, batch_y_exist).item()
                loss2 += crit2(out2, batch_y_vis).item()
        
        return loss1 / len(loader), loss2 / len(loader)
    
    def save_models(self):
        print("[SAVE] Saving models...")
        torch.save({
            'existence': self.existence_model.state_dict(),
            'visibility': self.visibility_model.state_dict(),
            'scaler': self.scaler,
            'config': self.config,
            'feature_extractor': self.feature_extractor
        }, f'{self.model_dir}/models.pth')
    
    def load_models(self):
        try:
            print("[LOAD] Loading models...")
            checkpoint = torch.load(f'{self.model_dir}/models.pth', map_location=device)
            
            self.scaler = checkpoint['scaler']
            self.config = checkpoint['config']
            self.feature_extractor = checkpoint['feature_extractor']
            
            input_dim = self.feature_extractor.dim + 5
            
            self.existence_model = FastTransformer(input_dim, self.config)
            self.visibility_model = FastMoE(input_dim, num_classes=5)
            
            self.existence_model.load_state_dict(checkpoint['existence'])
            self.visibility_model.load_state_dict(checkpoint['visibility'])
            
            self.trained = True
            print("[LOAD] Models loaded successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Load failed: {e}")
            return False
    
    def predict(self, business_unit: Optional[str] = None) -> List[Dict]:
        print(f"\n[PREDICT] Generating predictions...")
        start = time.time()
        
        if not self.trained:
            if os.path.exists(f'{self.model_dir}/models.pth'):
                self.load_models()
            else:
                print("[PREDICT] Training models first...")
                self.train()
        
        df = self.get_data()
        if df.empty:
            return []
        
        if business_unit:
            df = df[df['business_unit'] == business_unit]
        
        existing = set(df['host'].values)
        patterns = self._get_patterns(df)
        
        predictions = []
        self.existence_model.eval()
        self.visibility_model.eval()
        
        with torch.no_grad():
            for pattern in patterns[:10]:
                candidates = self._generate_candidates(pattern, existing)
                
                features = []
                hostnames = []
                
                for hostname in candidates[:100]:
                    host_feat = self.feature_extractor.extract(hostname)
                    context = np.array([1 if business_unit else 0, 1, 0, 0.7, 0.5], dtype=np.float32)
                    combined = np.concatenate([host_feat, context])
                    features.append(combined)
                    hostnames.append(hostname)
                
                if features:
                    X = self.scaler.transform(np.array(features))
                    X_tensor = torch.tensor(X, dtype=torch.float32, device=device)
                    
                    exist_logits = self.existence_model(X_tensor)
                    exist_probs = torch.sigmoid(exist_logits).cpu().numpy().flatten()
                    
                    vis_logits = self.visibility_model(X_tensor)
                    vis_probs = F.softmax(vis_logits, dim=1).cpu().numpy()
                    
                    for i, hostname in enumerate(hostnames):
                        if exist_probs[i] > 0.6:
                            predictions.append({
                                'hostname': hostname,
                                'existence_prob': float(exist_probs[i]),
                                'splunk_prob': float(vis_probs[i][3] + vis_probs[i][4]),
                                'gso_prob': float(vis_probs[i][2] + vis_probs[i][4]),
                                'risk_score': self._risk_score(hostname, exist_probs[i], vis_probs[i]),
                                'role': self._classify_role(hostname)
                            })
        
        predictions = sorted(predictions, key=lambda x: x['risk_score'], reverse=True)[:75]
        
        print(f"[PREDICT] Generated {len(predictions)} predictions in {time.time() - start:.1f}s")
        return predictions
    
    def _get_patterns(self, df):
        patterns = defaultdict(int)
        for host in df['host'].dropna():
            pattern = re.sub(r'\d+', 'NUM', host.lower())
            patterns[pattern] += 1
        return [p for p, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True) if count >= 2]
    
    def _generate_candidates(self, pattern, existing):
        candidates = []
        for i in range(1, 200):
            for pad in [2, 3]:
                hostname = pattern.replace('NUM', str(i).zfill(pad))
                if hostname not in existing:
                    candidates.append(hostname)
        return candidates
    
    def _risk_score(self, hostname, exist_prob, vis_probs):
        score = exist_prob * 0.3
        score += vis_probs[0] * 0.3
        if 'prod' in hostname.lower():
            score += 0.2
        if any(x in hostname.lower() for x in ['db', 'database', 'sql']):
            score += 0.2
        return min(score, 1.0)
    
    def _classify_role(self, hostname):
        h = hostname.lower()
        if any(x in h for x in ['db', 'sql', 'mongo']):
            return 'Database'
        elif any(x in h for x in ['web', 'www']):
            return 'Web'
        elif any(x in h for x in ['app', 'api']):
            return 'Application'
        elif any(x in h for x in ['fw', 'firewall']):
            return 'Security'
        return 'Server'

app = Flask(__name__)
predictor = AO1Predictor()

@app.route('/api/train')
def train():
    print(f"\n[API] Training requested")
    threading.Thread(target=predictor.train, daemon=True).start()
    return jsonify({'status': 'training_started'})

@app.route('/api/predict')
def predict():
    print(f"\n[API] Prediction requested")
    predictions = predictor.predict()
    return jsonify(predictions)

@app.route('/api/predict/<business_unit>')
def predict_bu(business_unit):
    print(f"\n[API] Prediction for {business_unit}")
    predictions = predictor.predict(business_unit)
    return jsonify(predictions)

@app.route('/api/status')
def status():
    used = torch.mps.driver_allocated_memory() / 1e9 if device.type == 'mps' else 0
    return jsonify({
        'trained': predictor.trained,
        'device': str(device),
        'gpu_memory_gb': used,
        'training_time_seconds': predictor.training_time,
        'cache_exists': os.path.exists('cache/processed_data.pkl')
    })

@app.route('/api/clear-cache')
def clear_cache():
    print(f"\n[API] Clearing cache")
    import shutil
    if os.path.exists('cache'):
        shutil.rmtree('cache')
        os.makedirs('cache')
    torch.mps.empty_cache() if device.type == 'mps' else None
    return jsonify({'status': 'cache_cleared'})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("AO1 ULTRA-FAST PREDICTOR")
    print("="*60)
    print(f"Device: {device}")
    print(f"Cache: {'Enabled' if os.path.exists('cache') else 'Empty'}")
    
    if os.path.exists(f'{predictor.model_dir}/models.pth'):
        predictor.load_models()
        print("[READY] Models loaded from disk")
    else:
        print("[READY] Models need training - use /api/train")
    
    print("\n[SERVER] Starting on http://0.0.0.0:5001")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')