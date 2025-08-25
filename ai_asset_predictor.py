import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import pandas as pd
import re
import duckdb
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from flask import Flask, jsonify
import threading
from datetime import datetime
import os
import pickle
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
from functools import lru_cache
import gc
import time
import traceback

if torch.backends.mps.is_available():
    device = torch.device("mps")
    torch.mps.empty_cache()
    print(f"[GPU] Apple Silicon GPU (MPS) Initialized")
    print(f"[GPU] Maximum memory: 18.13 GB")
else:
    device = torch.device("cpu")
    print("[CPU] MPS not available, using CPU")

def log_memory(tag="", verbose=True):
    if device.type == 'mps':
        allocated = torch.mps.driver_allocated_memory() / 1e9
        remaining = 18.13 - allocated
        if verbose:
            print(f"[MEM] {tag}: {allocated:.2f}GB used | {remaining:.2f}GB free")
        return allocated
    return 0

@dataclass
class ModelConfig:
    hidden_dims: List[int] = None
    dropout_rate: float = 0.2
    batch_size: int = 32
    learning_rate: float = 0.001
    epochs: int = 50
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [512, 256, 128, 64]

class AttentionBlock(nn.Module):
    def __init__(self, embed_dim: int):
        super().__init__()
        self.attention = nn.MultiheadAttention(embed_dim, num_heads=4, batch_first=True)
        self.norm = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        attn_out, _ = self.attention(x, x, x)
        x = self.norm(x + self.dropout(attn_out))
        return x.squeeze(1) if x.size(1) == 1 else x.mean(dim=1)

class HostnameTransformer(nn.Module):
    def __init__(self, input_dim: int, config: ModelConfig, output_dim: int = 1):
        super().__init__()
        
        layers = []
        current_dim = input_dim
        
        for hidden_dim in config.hidden_dims:
            layers.extend([
                nn.Linear(current_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU(),
                nn.Dropout(config.dropout_rate)
            ])
            current_dim = hidden_dim
        
        self.encoder = nn.Sequential(*layers)
        self.attention = AttentionBlock(config.hidden_dims[-1])
        self.output = nn.Linear(config.hidden_dims[-1], output_dim)
        
    def forward(self, x):
        x = self.encoder(x)
        x = self.attention(x)
        return self.output(x)

class VisibilityMoE(nn.Module):
    def __init__(self, input_dim: int, num_classes: int = 5):
        super().__init__()
        
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, 128),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(128, num_classes)
            ) for _ in range(3)
        ])
        
        self.gate = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 3),
            nn.Softmax(dim=-1)
        )
        
    def forward(self, x):
        gate_weights = self.gate(x)
        expert_outputs = torch.stack([expert(x) for expert in self.experts], dim=1)
        return torch.einsum('bi,bij->bj', gate_weights, expert_outputs)

class FeatureExtractor:
    def __init__(self, feature_dim: int = 128):
        self.feature_dim = feature_dim
        self.cache = {}
        
    @lru_cache(maxsize=10000)
    def extract(self, hostname: str) -> np.ndarray:
        if not hostname:
            return np.zeros(self.feature_dim)
        
        hostname = hostname.lower().strip()
        features = []
        
        # Basic structure
        features.extend([
            len(hostname) / 50.0,
            hostname.count('.') / 5.0,
            hostname.count('-') / 5.0,
            len(re.findall(r'\d+', hostname)) / 5.0,
            len(set(hostname)) / len(hostname) if hostname else 0,
        ])
        
        # Pattern detection
        patterns = {
            'server': ['srv', 'server', 'host'],
            'database': ['db', 'sql', 'mongo'],
            'web': ['web', 'www', 'api'],
            'network': ['fw', 'router', 'switch'],
            'prod': ['prod', 'production'],
            'dev': ['dev', 'test', 'stage']
        }
        
        for category, keywords in patterns.items():
            score = max([1.0 if kw in hostname else 0.0 for kw in keywords] + [0.0])
            features.append(score)
        
        # Numeric patterns
        numbers = re.findall(r'\d+', hostname)
        if numbers:
            nums = [int(n) for n in numbers]
            features.extend([
                np.mean(nums) / 100.0,
                np.std(nums) / 100.0 if len(nums) > 1 else 0,
                min(nums) / 100.0,
                max(nums) / 100.0
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        # Hash embedding for pattern signature
        pattern_sig = re.sub(r'\d+', 'X', hostname)
        hash_val = int(hashlib.md5(pattern_sig.encode()).hexdigest()[:8], 16)
        for i in range(20):
            features.append(np.sin(hash_val / (10000 ** (i / 20))))
        
        # Pad to feature_dim
        while len(features) < self.feature_dim:
            features.append(0.0)
        
        return np.array(features[:self.feature_dim], dtype=np.float32)

class AO1Predictor:
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        print("\n" + "="*60)
        print("AO1 VISIBILITY PREDICTOR v3.0")
        print("="*60)
        
        self.db_path = db_path
        self.model_dir = 'models'
        self.config = ModelConfig()
        self.feature_extractor = FeatureExtractor()
        self.scaler = RobustScaler()
        
        self.existence_model = None
        self.visibility_model = None
        self.trained = False
        
        os.makedirs(self.model_dir, exist_ok=True)
        log_memory("Initialization")
        
    def get_cmdb_data(self) -> pd.DataFrame:
        print("[DATA] Loading CMDB data...")
        try:
            conn = duckdb.connect(self.db_path)
            query = """
            SELECT host, business_unit, region, system_classification,
                   logging_in_splunk, logging_in_gso, present_in_cmdb,
                   edr_coverage, data_quality_score, source_count
            FROM universal_cmdb
            """
            df = conn.execute(query).df()
            conn.close()
            print(f"[DATA] Loaded {len(df)} records")
            return df
        except Exception as e:
            print(f"[ERROR] Database error: {e}")
            return pd.DataFrame()
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        print(f"[PREP] Processing {len(df)} records...")
        
        features = []
        exist_labels = []
        vis_labels = []
        
        for idx, row in df.iterrows():
            if idx % 1000 == 0:
                print(f"[PREP] Progress: {idx}/{len(df)}")
            
            # Extract hostname features
            host_features = self.feature_extractor.extract(row['host'])
            
            # Add context features
            context = np.zeros(32, dtype=np.float32)
            if pd.notna(row.get('business_unit')):
                bu_hash = int(hashlib.md5(str(row['business_unit']).encode()).hexdigest()[:4], 16)
                context[0] = bu_hash / 65535.0
            if pd.notna(row.get('region')):
                reg_hash = int(hashlib.md5(str(row['region']).encode()).hexdigest()[:4], 16)
                context[1] = reg_hash / 65535.0
            context[2] = float(row.get('data_quality_score', 0)) / 10.0
            context[3] = np.log1p(float(row.get('source_count', 0))) / 10.0
            
            combined = np.concatenate([host_features, context])
            features.append(combined)
            
            # Calculate labels
            exist_score = 0.0
            if row.get('logging_in_splunk') == 'yes':
                exist_score += 0.4
            if row.get('present_in_cmdb') == 'yes':
                exist_score += 0.3
            if pd.notna(row.get('edr_coverage')):
                exist_score += 0.3
            exist_labels.append(min(exist_score, 1.0))
            
            # Visibility class
            if row.get('logging_in_splunk') == 'yes' and row.get('logging_in_gso') == 'yes':
                vis_class = 4
            elif row.get('logging_in_splunk') == 'yes':
                vis_class = 3
            elif row.get('logging_in_gso') == 'yes':
                vis_class = 2
            elif row.get('present_in_cmdb') == 'yes':
                vis_class = 1
            else:
                vis_class = 0
            vis_labels.append(vis_class)
        
        X = np.array(features, dtype=np.float32)
        y_exist = np.array(exist_labels, dtype=np.float32)
        y_vis = np.array(vis_labels, dtype=np.int64)
        
        print(f"[PREP] Features shape: {X.shape}")
        print(f"[PREP] Existence mean: {y_exist.mean():.3f}")
        print(f"[PREP] Visibility distribution: {Counter(y_vis)}")
        
        return X, y_exist, y_vis
    
    def train(self):
        print("\n[TRAIN] Starting training...")
        torch.mps.empty_cache() if device.type == 'mps' else None
        
        # Load and prepare data
        df = self.get_cmdb_data()
        if df.empty:
            print("[ERROR] No data available")
            return False
        
        X, y_exist, y_vis = self.prepare_data(df)
        
        # Scale features
        print("[TRAIN] Scaling features...")
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_val, y_exist_train, y_exist_val, y_vis_train, y_vis_val = train_test_split(
            X_scaled, y_exist, y_vis, test_size=0.2, random_state=42, stratify=y_vis
        )
        
        print(f"[TRAIN] Train size: {len(X_train)}, Val size: {len(X_val)}")
        
        # Create models
        input_dim = X_scaled.shape[1]
        print(f"[TRAIN] Creating models (input_dim={input_dim})...")
        
        self.existence_model = HostnameTransformer(input_dim, self.config).to(device)
        self.visibility_model = VisibilityMoE(input_dim).to(device)
        
        log_memory("Models created")
        
        # Create datasets
        train_dataset = torch.utils.data.TensorDataset(
            torch.tensor(X_train, dtype=torch.float32),
            torch.tensor(y_exist_train.reshape(-1, 1), dtype=torch.float32),
            torch.tensor(y_vis_train, dtype=torch.long)
        )
        
        val_dataset = torch.utils.data.TensorDataset(
            torch.tensor(X_val, dtype=torch.float32),
            torch.tensor(y_exist_val.reshape(-1, 1), dtype=torch.float32),
            torch.tensor(y_vis_val, dtype=torch.long)
        )
        
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=self.config.batch_size, shuffle=True
        )
        
        val_loader = torch.utils.data.DataLoader(
            val_dataset, batch_size=self.config.batch_size * 2, shuffle=False
        )
        
        # Optimizers and losses
        opt1 = optim.AdamW(self.existence_model.parameters(), lr=self.config.learning_rate)
        opt2 = optim.AdamW(self.visibility_model.parameters(), lr=self.config.learning_rate)
        
        scheduler1 = optim.lr_scheduler.ReduceLROnPlateau(opt1, patience=5, factor=0.5)
        scheduler2 = optim.lr_scheduler.ReduceLROnPlateau(opt2, patience=5, factor=0.5)
        
        criterion1 = nn.BCEWithLogitsLoss()
        criterion2 = nn.CrossEntropyLoss()
        
        best_val_loss = float('inf')
        patience = 0
        
        print(f"\n[TRAIN] Training for {self.config.epochs} epochs...")
        print("-" * 60)
        
        for epoch in range(self.config.epochs):
            start_time = time.time()
            
            # Training
            self.existence_model.train()
            self.visibility_model.train()
            
            train_loss1, train_loss2 = 0, 0
            
            for batch_idx, (batch_x, batch_y_exist, batch_y_vis) in enumerate(train_loader):
                batch_x = batch_x.to(device)
                batch_y_exist = batch_y_exist.to(device)
                batch_y_vis = batch_y_vis.to(device)
                
                # Existence model
                opt1.zero_grad()
                out1 = self.existence_model(batch_x)
                loss1 = criterion1(out1, batch_y_exist)
                loss1.backward()
                torch.nn.utils.clip_grad_norm_(self.existence_model.parameters(), 1.0)
                opt1.step()
                train_loss1 += loss1.item()
                
                # Visibility model
                opt2.zero_grad()
                out2 = self.visibility_model(batch_x)
                loss2 = criterion2(out2, batch_y_vis)
                loss2.backward()
                torch.nn.utils.clip_grad_norm_(self.visibility_model.parameters(), 1.0)
                opt2.step()
                train_loss2 += loss2.item()
                
                if batch_idx % 50 == 0 and batch_idx > 0:
                    print(f"  Batch {batch_idx}/{len(train_loader)}: "
                          f"Loss1={loss1.item():.4f}, Loss2={loss2.item():.4f}")
            
            train_loss1 /= len(train_loader)
            train_loss2 /= len(train_loader)
            
            # Validation
            self.existence_model.eval()
            self.visibility_model.eval()
            
            val_loss1, val_loss2 = 0, 0
            
            with torch.no_grad():
                for batch_x, batch_y_exist, batch_y_vis in val_loader:
                    batch_x = batch_x.to(device)
                    batch_y_exist = batch_y_exist.to(device)
                    batch_y_vis = batch_y_vis.to(device)
                    
                    out1 = self.existence_model(batch_x)
                    val_loss1 += criterion1(out1, batch_y_exist).item()
                    
                    out2 = self.visibility_model(batch_x)
                    val_loss2 += criterion2(out2, batch_y_vis).item()
            
            val_loss1 /= len(val_loader)
            val_loss2 /= len(val_loader)
            
            # Update schedulers
            scheduler1.step(val_loss1)
            scheduler2.step(val_loss2)
            
            # Print epoch results
            epoch_time = time.time() - start_time
            total_val_loss = val_loss1 + val_loss2
            
            print(f"[EPOCH {epoch+1:2d}/{self.config.epochs}] "
                  f"Time: {epoch_time:.1f}s | "
                  f"Train: {train_loss1:.4f}/{train_loss2:.4f} | "
                  f"Val: {val_loss1:.4f}/{val_loss2:.4f} | "
                  f"LR: {opt1.param_groups[0]['lr']:.6f}")
            
            # Save best model
            if total_val_loss < best_val_loss:
                best_val_loss = total_val_loss
                patience = 0
                self.save_models()
                print(f"  → Saved best model (val_loss={total_val_loss:.4f})")
            else:
                patience += 1
                
            if patience >= 15:
                print(f"\n[STOP] Early stopping at epoch {epoch+1}")
                break
            
            # Memory cleanup every 10 epochs
            if epoch % 10 == 0:
                torch.mps.empty_cache() if device.type == 'mps' else None
                log_memory(f"Epoch {epoch+1}", verbose=False)
        
        self.trained = True
        print(f"\n[TRAIN] Training completed! Best val_loss: {best_val_loss:.4f}")
        log_memory("Training complete")
        return True
    
    def save_models(self):
        try:
            torch.save(self.existence_model.state_dict(), f'{self.model_dir}/existence_model.pth')
            torch.save(self.visibility_model.state_dict(), f'{self.model_dir}/visibility_model.pth')
            with open(f'{self.model_dir}/scaler.pkl', 'wb') as f:
                pickle.dump(self.scaler, f)
            with open(f'{self.model_dir}/feature_extractor.pkl', 'wb') as f:
                pickle.dump(self.feature_extractor, f)
        except Exception as e:
            print(f"[ERROR] Save failed: {e}")
    
    def load_models(self) -> bool:
        try:
            print("[LOAD] Loading saved models...")
            
            # Load components
            with open(f'{self.model_dir}/scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            with open(f'{self.model_dir}/feature_extractor.pkl', 'rb') as f:
                self.feature_extractor = pickle.load(f)
            
            # Determine input size
            sample = self.feature_extractor.extract("test")
            context = np.zeros(32)
            input_dim = len(np.concatenate([sample, context]))
            
            # Create and load models
            self.existence_model = HostnameTransformer(input_dim, self.config).to(device)
            self.visibility_model = VisibilityMoE(input_dim).to(device)
            
            self.existence_model.load_state_dict(
                torch.load(f'{self.model_dir}/existence_model.pth', map_location=device)
            )
            self.visibility_model.load_state_dict(
                torch.load(f'{self.model_dir}/visibility_model.pth', map_location=device)
            )
            
            self.trained = True
            print("[LOAD] Models loaded successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Load failed: {e}")
            return False
    
    def predict(self, business_unit: Optional[str] = None) -> List[Dict]:
        print(f"\n[PREDICT] Starting prediction (BU: {business_unit or 'All'})")
        
        if not self.trained:
            print("[PREDICT] Models not trained")
            return []
        
        # Load data
        df = self.get_cmdb_data()
        if df.empty:
            return []
        
        if business_unit:
            df = df[df['business_unit'] == business_unit]
        
        # Find patterns
        patterns = self._find_patterns(df)
        existing = set(df['host'].values)
        predictions = []
        
        self.existence_model.eval()
        self.visibility_model.eval()
        
        print(f"[PREDICT] Processing {len(patterns)} patterns...")
        
        with torch.no_grad():
            for pattern_idx, pattern in enumerate(patterns[:15]):
                if pattern_idx % 5 == 0:
                    print(f"  Pattern {pattern_idx+1}/{min(15, len(patterns))}")
                
                # Generate candidates
                candidates = self._generate_candidates(pattern, existing)
                
                for candidate in candidates[:30]:
                    # Prepare features
                    host_features = self.feature_extractor.extract(candidate)
                    context = np.zeros(32, dtype=np.float32)
                    if business_unit:
                        bu_hash = int(hashlib.md5(business_unit.encode()).hexdigest()[:4], 16)
                        context[0] = bu_hash / 65535.0
                    
                    features = np.concatenate([host_features, context])
                    features_scaled = self.scaler.transform([features])
                    features_tensor = torch.tensor(features_scaled, dtype=torch.float32).to(device)
                    
                    # Predict
                    exist_logits = self.existence_model(features_tensor)
                    exist_prob = torch.sigmoid(exist_logits).cpu().item()
                    
                    vis_logits = self.visibility_model(features_tensor)
                    vis_probs = F.softmax(vis_logits, dim=-1).cpu().numpy()[0]
                    
                    if exist_prob > 0.6:
                        predictions.append({
                            'hostname': candidate,
                            'existence_prob': float(exist_prob),
                            'splunk_prob': float(vis_probs[3] + vis_probs[4]),
                            'gso_prob': float(vis_probs[2] + vis_probs[4]),
                            'pattern': pattern['signature'],
                            'business_unit': business_unit or 'Unknown',
                            'risk_score': self._calculate_risk(candidate, exist_prob, vis_probs)
                        })
        
        # Sort and return top predictions
        predictions.sort(key=lambda x: x['existence_prob'] * x['risk_score'], reverse=True)
        
        print(f"[PREDICT] Found {len(predictions)} potential missing assets")
        return predictions[:50]
    
    def _find_patterns(self, df: pd.DataFrame) -> List[Dict]:
        patterns = defaultdict(list)
        
        for hostname in df['host'].dropna():
            sig = re.sub(r'\d+', 'NUM', hostname.lower())
            patterns[sig].append(hostname)
        
        result = []
        for sig, hosts in patterns.items():
            if len(hosts) >= 2:
                result.append({
                    'signature': sig,
                    'pattern': sig.replace('NUM', 'XXX'),
                    'count': len(hosts)
                })
        
        return sorted(result, key=lambda x: x['count'], reverse=True)
    
    def _generate_candidates(self, pattern: Dict, existing: set) -> List[str]:
        candidates = []
        base = pattern['pattern']
        
        for i in range(1, 50):
            for padding in [2, 3]:
                candidate = base.replace('XXX', str(i).zfill(padding))
                if candidate not in existing:
                    candidates.append(candidate)
        
        return candidates
    
    def _calculate_risk(self, hostname: str, exist_prob: float, vis_probs: np.ndarray) -> float:
        risk = 0.0
        h = hostname.lower()
        
        if 'prod' in h:
            risk += 0.3
        if any(x in h for x in ['db', 'database', 'sql']):
            risk += 0.2
        if any(x in h for x in ['fw', 'firewall', 'security']):
            risk += 0.2
        
        risk += exist_prob * 0.2
        risk += vis_probs[0] * 0.1  # No visibility
        
        return min(risk, 1.0)
    
    def initialize(self):
        print("[INIT] Initializing predictor...")
        
        # Check for existing models
        model_files = [
            f'{self.model_dir}/existence_model.pth',
            f'{self.model_dir}/visibility_model.pth',
            f'{self.model_dir}/scaler.pkl',
            f'{self.model_dir}/feature_extractor.pkl'
        ]
        
        if all(os.path.exists(f) for f in model_files):
            print("[INIT] Found saved models")
            return self.load_models()
        else:
            print("[INIT] No saved models, training required")
            return self.train()

# Flask API
app = Flask(__name__)
predictor = AO1Predictor()

@app.route('/api/train-visibility-model')
def train_model():
    try:
        print("\n[API] Training requested")
        thread = threading.Thread(target=predictor.train, daemon=True)
        thread.start()
        return jsonify({
            'status': 'training_started',
            'message': 'Model training initiated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility')
def predict():
    try:
        print("\n[API] Prediction requested")
        if not predictor.trained:
            return jsonify({'error': 'Models not trained'}), 503
        
        predictions = predictor.predict()
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility/<business_unit>')
def predict_bu(business_unit):
    try:
        print(f"\n[API] Prediction for BU: {business_unit}")
        if not predictor.trained:
            return jsonify({'error': 'Models not trained'}), 503
        
        predictions = predictor.predict(business_unit)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/visibility-model-status')
def status():
    mem = log_memory("Status", verbose=False)
    return jsonify({
        'trained': predictor.trained,
        'device': str(device),
        'memory_gb': mem,
        'config': {
            'batch_size': predictor.config.batch_size,
            'epochs': predictor.config.epochs,
            'hidden_dims': predictor.config.hidden_dims
        }
    })

@app.route('/api/visibility-gap-analysis')
def gap_analysis():
    try:
        print("\n[API] Gap analysis requested")
        if not predictor.trained:
            return jsonify({'error': 'Models not trained'}), 503
        
        predictions = predictor.predict()
        
        if not predictions:
            return jsonify({'error': 'No predictions available'}), 204
        
        high_risk = [p for p in predictions if p['risk_score'] > 0.7]
        high_confidence = [p for p in predictions if p['existence_prob'] > 0.8]
        
        return jsonify({
            'total_predictions': len(predictions),
            'high_risk_count': len(high_risk),
            'high_confidence_count': len(high_confidence),
            'avg_existence_prob': np.mean([p['existence_prob'] for p in predictions]),
            'top_patterns': Counter([p['pattern'] for p in predictions]).most_common(5),
            'critical_gaps': high_risk[:10],
            'confident_predictions': high_confidence[:10]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-models')
def load_models():
    try:
        print("\n[API] Model loading requested")
        success = predictor.load_models()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Models loaded' if success else 'Failed to load models'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("STARTING AO1 VISIBILITY PREDICTOR SERVICE")
    print("="*60)
    print(f"Device: {device}")
    print(f"Model directory: {predictor.model_dir}")
    
    # Initialize
    predictor.initialize()
    
    if predictor.trained:
        print("\n[READY] Service ready with trained models")
    else:
        print("\n[READY] Service ready - training required")
        print("Use /api/train-visibility-model to start training")
    
    log_memory("Service ready")
    
    print("\n[SERVER] Starting Flask on http://0.0.0.0:5001")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')