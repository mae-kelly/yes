import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import pandas as pd
import re
import duckdb
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import StratifiedKFold
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
import psutil

if torch.backends.mps.is_available():
    device = torch.device("mps")
    print(f"[INIT] Using Apple Silicon GPU (MPS)")
    print(f"[INIT] MPS Memory: {torch.mps.driver_allocated_memory() / 1e9:.2f} GB allocated")
else:
    print("[ERROR] MPS not available!")
    exit(1)

def log_memory(tag=""):
    if device.type == 'mps':
        allocated = torch.mps.driver_allocated_memory() / 1e9
        print(f"[MEMORY] {tag} - MPS: {allocated:.2f} GB allocated")
    
    process = psutil.Process(os.getpid())
    ram = process.memory_info().rss / 1e9
    print(f"[MEMORY] {tag} - RAM: {ram:.2f} GB")
    
def clear_memory():
    gc.collect()
    if device.type == 'mps':
        torch.mps.empty_cache()
        torch.mps.synchronize()
    print("[MEMORY] Cleared caches")

@dataclass
class ModelConfig:
    hidden_dims: List[int] = None
    dropout_rates: List[float] = None
    activation: str = 'gelu'
    use_batch_norm: bool = False
    use_layer_norm: bool = True
    residual_connections: bool = True
    attention_heads: int = 2
    batch_size: int = 16
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [256, 128, 64]
        if self.dropout_rates is None:
            self.dropout_rates = [0.2, 0.25, 0.3]

class SimplifiedAttention(nn.Module):
    def __init__(self, embed_dim: int):
        super().__init__()
        self.embed_dim = embed_dim
        self.qkv = nn.Linear(embed_dim, embed_dim * 3, bias=False)
        self.o = nn.Linear(embed_dim, embed_dim)
        self.scale = embed_dim ** -0.5
        
    def forward(self, x):
        B = x.shape[0]
        qkv = self.qkv(x).reshape(B, 3, self.embed_dim)
        q, k, v = qkv[:, 0], qkv[:, 1], qkv[:, 2]
        
        attn = (q @ k.T) * self.scale
        attn = F.softmax(attn, dim=-1)
        
        x = attn @ v
        return self.o(x)

class LightweightBlock(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, dropout: float = 0.2):
        super().__init__()
        self.fc = nn.Linear(in_dim, out_dim)
        self.norm = nn.LayerNorm(out_dim)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()
        
    def forward(self, x):
        x = self.fc(x)
        x = self.norm(x)
        x = self.activation(x)
        x = self.dropout(x)
        return x

class CompactTransformer(nn.Module):
    def __init__(self, input_dim: int, config: ModelConfig, output_dim: int = 1):
        super().__init__()
        print(f"[MODEL] Building CompactTransformer: input={input_dim}, output={output_dim}")
        self.config = config
        
        self.input_projection = nn.Sequential(
            nn.Linear(input_dim, config.hidden_dims[0]),
            nn.LayerNorm(config.hidden_dims[0]),
            nn.GELU(),
            nn.Dropout(0.1)
        )
        
        self.attention = SimplifiedAttention(config.hidden_dims[0])
        
        self.blocks = nn.ModuleList()
        for i in range(len(config.hidden_dims) - 1):
            self.blocks.append(
                LightweightBlock(
                    config.hidden_dims[i],
                    config.hidden_dims[i + 1],
                    config.dropout_rates[i]
                )
            )
        
        self.output_head = nn.Linear(config.hidden_dims[-1], output_dim)
        
        self._init_weights()
        print(f"[MODEL] Total parameters: {sum(p.numel() for p in self.parameters()):,}")
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=0.5)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        x = self.input_projection(x)
        x = x + self.attention(x)
        
        for block in self.blocks:
            x = block(x)
        
        return self.output_head(x)

class SimpleMoE(nn.Module):
    def __init__(self, input_dim: int, num_experts: int = 2, output_dim: int = 5):
        super().__init__()
        print(f"[MODEL] Building SimpleMoE: input={input_dim}, experts={num_experts}, output={output_dim}")
        self.num_experts = num_experts
        
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, 128),
                nn.GELU(),
                nn.Dropout(0.2),
                nn.Linear(128, output_dim)
            ) for _ in range(num_experts)
        ])
        
        self.gating = nn.Sequential(
            nn.Linear(input_dim, num_experts),
            nn.Softmax(dim=-1)
        )
        
        print(f"[MODEL] MoE parameters: {sum(p.numel() for p in self.parameters()):,}")
    
    def forward(self, x):
        gates = self.gating(x)
        expert_outputs = torch.stack([expert(x) for expert in self.experts], dim=1)
        return torch.sum(gates.unsqueeze(-1) * expert_outputs, dim=1)

class FeatureEngineering:
    def __init__(self):
        self.pattern_cache = {}
        self.entropy_cache = {}
        print("[FEATURES] Feature engineering initialized")
        
    @lru_cache(maxsize=10000)
    def extract_advanced_features(self, hostname: str) -> np.ndarray:
        if not hostname:
            return np.zeros(96)
        
        hostname = hostname.lower().strip()
        
        structural_features = self._extract_structural_features(hostname)
        semantic_features = self._extract_semantic_features(hostname)
        statistical_features = self._extract_statistical_features(hostname)
        
        return np.concatenate([
            structural_features,
            semantic_features,
            statistical_features
        ])[:96]
    
    def _extract_structural_features(self, hostname: str) -> np.ndarray:
        features = [
            len(hostname),
            len(hostname.split('.')),
            len(hostname.split('-')),
            len(re.findall(r'\d+', hostname)),
            len(re.findall(r'[a-z]+', hostname)),
            len(set(hostname)),
            self._calculate_entropy(hostname),
            max([len(x) for x in hostname.split('.')]) if '.' in hostname else len(hostname),
            min([len(x) for x in hostname.split('.')]) if '.' in hostname else len(hostname),
            hostname.count('.'),
            hostname.count('-'),
            hostname.count('_'),
            len(re.findall(r'\d', hostname)),
            len(re.findall(r'[a-z]', hostname)),
            1 if hostname.startswith('srv') else 0,
            1 if hostname.startswith('web') else 0,
            1 if hostname.startswith('db') else 0,
            1 if hostname.startswith('app') else 0,
            1 if '.com' in hostname else 0,
            1 if '.local' in hostname else 0
        ]
        
        return np.array(features[:32])
    
    def _extract_semantic_features(self, hostname: str) -> np.ndarray:
        semantic_patterns = {
            'infrastructure': ['srv', 'server', 'host', 'node'],
            'network': ['fw', 'firewall', 'router', 'switch', 'gateway'],
            'database': ['db', 'sql', 'mongo', 'redis'],
            'application': ['app', 'api', 'web', 'www'],
            'security': ['ids', 'ips', 'ndr', 'waf'],
            'environment': ['prod', 'dev', 'test', 'staging'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud'],
            'datacenter': ['dc', '1dc', 'fead', 'fiserv']
        }
        
        features = []
        for category, patterns in semantic_patterns.items():
            score = sum([1.0 if p in hostname else 0 for p in patterns])
            features.append(score)
        
        while len(features) < 32:
            features.append(0)
        
        return np.array(features[:32])
    
    def _extract_statistical_features(self, hostname: str) -> np.ndarray:
        features = []
        
        numeric_sequences = re.findall(r'\d+', hostname)
        if numeric_sequences:
            numbers = [int(x) for x in numeric_sequences]
            features.extend([
                np.mean(numbers),
                np.std(numbers) if len(numbers) > 1 else 0,
                np.min(numbers),
                np.max(numbers),
                len(numbers)
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        alpha_sequences = re.findall(r'[a-z]+', hostname)
        if alpha_sequences:
            lengths = [len(x) for x in alpha_sequences]
            features.extend([
                np.mean(lengths),
                np.std(lengths) if len(lengths) > 1 else 0,
                np.min(lengths),
                np.max(lengths),
                len(alpha_sequences)
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        pattern_hash = hashlib.md5(re.sub(r'\d+', 'X', hostname).encode()).hexdigest()
        features.extend([int(pattern_hash[i:i+2], 16) / 255.0 for i in range(0, 16, 2)])
        
        while len(features) < 32:
            features.append(0)
        
        return np.array(features[:32])
    
    def _calculate_entropy(self, s: str) -> float:
        if s in self.entropy_cache:
            return self.entropy_cache[s]
        
        if not s:
            return 0
        
        prob = [float(s.count(c)) / len(s) for c in set(s)]
        entropy = -sum([p * np.log2(p) for p in prob if p > 0])
        self.entropy_cache[s] = entropy
        return entropy

class AO1VisibilityPredictor:
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        print("\n" + "="*60)
        print("[INIT] AO1 Visibility Predictor v2.0")
        print("="*60)
        
        self.existence_model = None
        self.visibility_model = None
        self.feature_engineer = FeatureEngineering()
        self.feature_scaler = RobustScaler()
        self.trained = False
        self.db_path = db_path
        self.model_version = "2.0.0"
        self.training_metrics = {}
        self.model_dir = 'models'
        self.config = ModelConfig()
        
        os.makedirs(self.model_dir, exist_ok=True)
        log_memory("Initialization")
        
    @property
    def models_exist(self) -> bool:
        required_files = [
            f'{self.model_dir}/existence_model.pth',
            f'{self.model_dir}/visibility_model.pth',
            f'{self.model_dir}/feature_scaler.pkl',
            f'{self.model_dir}/feature_engineer.pkl'
        ]
        exists = all(os.path.exists(f) for f in required_files)
        print(f"[CHECK] Models exist: {exists}")
        return exists
    
    def initialize_models(self):
        print("\n[INIT] Starting model initialization...")
        
        if self.models_exist:
            print("[INIT] Found existing models, attempting to load...")
            if self.load_models():
                print("[SUCCESS] Models loaded successfully!")
                return True
            print("[WARNING] Failed to load models, will train new ones...")
        
        print("[INIT] Training new models from scratch...")
        self.train_models()
        return self.trained
    
    def get_db_connection(self):
        try:
            conn = duckdb.connect(self.db_path)
            print(f"[DB] Connected to {self.db_path}")
            return conn
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return None
    
    def get_cmdb_data(self) -> pd.DataFrame:
        print("[DATA] Fetching CMDB data...")
        conn = self.get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        query = """
        SELECT 
            host, business_unit, region, country, data_center, cloud_region,
            system_classification, infrastructure_type, cio, apm,
            logging_in_splunk, logging_in_gso, present_in_cmdb, 
            edr_coverage, tanium_coverage, dlp_agent_coverage,
            first_seen, last_updated, data_quality_score, source_count
        FROM universal_cmdb
        """
        
        try:
            df = conn.execute(query).df()
            print(f"[DATA] Loaded {len(df)} records from universal_cmdb")
            print(f"[DATA] Columns: {', '.join(df.columns[:5])}...")
            print(f"[DATA] Memory usage: {df.memory_usage(deep=True).sum() / 1e6:.2f} MB")
            return df
        except Exception as e:
            print(f"[ERROR] Failed to fetch CMDB data: {e}")
            traceback.print_exc()
            return pd.DataFrame()
        finally:
            conn.close()
            print("[DB] Connection closed")
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        print(f"[PREP] Preparing training data from {len(df)} records...")
        start_time = time.time()
        
        features, existence_labels, visibility_labels = [], [], []
        
        for idx, (_, row) in enumerate(df.iterrows()):
            if idx % 100 == 0:
                print(f"[PREP] Processing record {idx}/{len(df)}...")
            
            hostname_features = self.feature_engineer.extract_advanced_features(row['host'])
            
            contextual_features = self._extract_contextual_features(row)
            combined_features = np.concatenate([hostname_features, contextual_features])
            
            features.append(combined_features)
            
            existence_score = self._calculate_existence_score(row)
            existence_labels.append(existence_score)
            
            visibility_class = self._calculate_visibility_class(row)
            visibility_labels.append(visibility_class)
        
        print(f"[PREP] Data preparation completed in {time.time() - start_time:.2f}s")
        print(f"[PREP] Feature shape: {len(features)} x {len(features[0])}")
        print(f"[PREP] Existence scores - Mean: {np.mean(existence_labels):.3f}, Std: {np.std(existence_labels):.3f}")
        print(f"[PREP] Visibility classes - Distribution: {Counter(visibility_labels)}")
        
        return np.array(features), np.array(existence_labels), np.array(visibility_labels)
    
    def _extract_contextual_features(self, row) -> np.ndarray:
        features = []
        
        categorical_mappings = {
            'business_unit': self._encode_categorical(row.get('business_unit', ''), 4),
            'region': self._encode_categorical(row.get('region', ''), 4),
            'infrastructure_type': self._encode_categorical(row.get('infrastructure_type', ''), 4),
            'system_classification': self._encode_categorical(row.get('system_classification', ''), 4)
        }
        
        for key, encoded in categorical_mappings.items():
            features.extend(encoded)
        
        numerical_features = [
            float(row.get('data_quality_score', 0)),
            np.log1p(float(row.get('source_count', 0))),
            1.0 if pd.notna(row.get('cio')) else 0.0,
            1.0 if pd.notna(row.get('apm')) else 0.0,
            self._calculate_temporal_feature(row.get('first_seen')),
            self._calculate_temporal_feature(row.get('last_updated'))
        ]
        
        features.extend(numerical_features)
        
        while len(features) < 32:
            features.append(0)
        
        return np.array(features[:32])
    
    def _encode_categorical(self, value: str, dim: int) -> np.ndarray:
        if pd.isna(value) or value == '':
            return np.zeros(dim)
        
        hash_val = int(hashlib.md5(str(value).encode()).hexdigest()[:8], 16)
        encoding = np.zeros(dim)
        for i in range(dim):
            encoding[i] = np.sin(hash_val / (10000 ** (2 * i / dim)))
        return encoding
    
    def _calculate_temporal_feature(self, date_val) -> float:
        if pd.isna(date_val):
            return 0.0
        try:
            if isinstance(date_val, str):
                date_obj = datetime.fromisoformat(date_val)
            else:
                date_obj = date_val
            days_ago = (datetime.now() - date_obj).days
            return 1.0 / (1.0 + np.log1p(days_ago))
        except:
            return 0.0
    
    def _calculate_existence_score(self, row) -> float:
        weights = {
            'logging_in_splunk': 0.4,
            'present_in_cmdb': 0.3,
            'edr_coverage': 0.2,
            'tanium_coverage': 0.1
        }
        
        score = 0.0
        for key, weight in weights.items():
            if key == 'edr_coverage':
                if pd.notna(row.get(key)) and 'crowdstrike' in str(row.get(key)).lower():
                    score += weight
            elif row.get(key) == 'yes':
                score += weight
        
        return min(score, 1.0)
    
    def _calculate_visibility_class(self, row) -> int:
        if row.get('logging_in_splunk') == 'yes' and row.get('logging_in_gso') == 'yes':
            return 4
        elif row.get('logging_in_splunk') == 'yes':
            return 3
        elif row.get('logging_in_gso') == 'yes':
            return 2
        elif row.get('present_in_cmdb') == 'yes':
            return 1
        return 0
    
    def train_models(self):
        print("\n" + "="*60)
        print("[TRAIN] Starting model training")
        print("="*60)
        
        print("[TRAIN] Loading CMDB data...")
        df = self.get_cmdb_data()
        
        if df.empty:
            print("[ERROR] No data available for training!")
            return
        
        print(f"[TRAIN] Preparing features from {len(df)} records...")
        X, existence_y, visibility_y = self.prepare_training_data(df)
        
        if len(X) == 0:
            print("[ERROR] No features extracted!")
            return
        
        print("[TRAIN] Scaling features...")
        X_scaled = self.feature_scaler.fit_transform(X)
        print(f"[TRAIN] Scaled feature stats - Mean: {X_scaled.mean():.3f}, Std: {X_scaled.std():.3f}")
        
        input_size = X_scaled.shape[1]
        print(f"[TRAIN] Input dimension: {input_size}")
        
        print("[TRAIN] Building models...")
        self.existence_model = CompactTransformer(input_size, self.config, output_dim=1).to(device)
        self.visibility_model = SimpleMoE(input_size, num_experts=2, output_dim=5).to(device)
        
        log_memory("Models created")
        
        self._train_with_cross_validation(X_scaled, existence_y, visibility_y)
        
        self.trained = True
        print("\n[SUCCESS] Training completed!")
        log_memory("Training completed")
    
    def _train_with_cross_validation(self, X: np.ndarray, existence_y: np.ndarray, visibility_y: np.ndarray):
        print(f"\n[CV] Starting 3-fold cross-validation...")
        kfold = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        
        best_existence_loss = float('inf')
        best_visibility_loss = float('inf')
        
        for fold, (train_idx, val_idx) in enumerate(kfold.split(X, visibility_y)):
            print(f"\n[CV] Training fold {fold + 1}/3")
            print(f"[CV] Train size: {len(train_idx)}, Val size: {len(val_idx)}")
            
            clear_memory()
            log_memory(f"Fold {fold + 1} start")
            
            X_train, X_val = X[train_idx], X[val_idx]
            existence_y_train, existence_y_val = existence_y[train_idx], existence_y[val_idx]
            visibility_y_train, visibility_y_val = visibility_y[train_idx], visibility_y[val_idx]
            
            train_dataset = torch.utils.data.TensorDataset(
                torch.FloatTensor(X_train),
                torch.FloatTensor(existence_y_train.reshape(-1, 1)),
                torch.LongTensor(visibility_y_train)
            )
            
            val_dataset = torch.utils.data.TensorDataset(
                torch.FloatTensor(X_val),
                torch.FloatTensor(existence_y_val.reshape(-1, 1)),
                torch.LongTensor(visibility_y_val)
            )
            
            train_loader = torch.utils.data.DataLoader(
                train_dataset, batch_size=self.config.batch_size, shuffle=True, pin_memory=False
            )
            
            val_loader = torch.utils.data.DataLoader(
                val_dataset, batch_size=self.config.batch_size, shuffle=False, pin_memory=False
            )
            
            print(f"[CV] Batches - Train: {len(train_loader)}, Val: {len(val_loader)}")
            
            optimizer1 = optim.AdamW(self.existence_model.parameters(), lr=0.001, weight_decay=1e-4)
            optimizer2 = optim.AdamW(self.visibility_model.parameters(), lr=0.001, weight_decay=1e-4)
            
            scheduler1 = optim.lr_scheduler.CosineAnnealingLR(optimizer1, T_max=30)
            scheduler2 = optim.lr_scheduler.CosineAnnealingLR(optimizer2, T_max=30)
            
            criterion1 = nn.BCEWithLogitsLoss()
            criterion2 = nn.CrossEntropyLoss(label_smoothing=0.1)
            
            for epoch in range(30):
                epoch_start = time.time()
                
                self.existence_model.train()
                self.visibility_model.train()
                
                train_loss1, train_loss2 = 0, 0
                batch_count = 0
                
                for batch_idx, (batch_x, batch_exist_y, batch_vis_y) in enumerate(train_loader):
                    batch_x = batch_x.to(device)
                    batch_exist_y = batch_exist_y.to(device)
                    batch_vis_y = batch_vis_y.to(device)
                    
                    optimizer1.zero_grad(set_to_none=True)
                    exist_outputs = self.existence_model(batch_x)
                    loss1 = criterion1(exist_outputs, batch_exist_y)
                    loss1.backward()
                    torch.nn.utils.clip_grad_norm_(self.existence_model.parameters(), 1.0)
                    optimizer1.step()
                    train_loss1 += loss1.item()
                    
                    optimizer2.zero_grad(set_to_none=True)
                    vis_outputs = self.visibility_model(batch_x)
                    loss2 = criterion2(vis_outputs, batch_vis_y)
                    loss2.backward()
                    torch.nn.utils.clip_grad_norm_(self.visibility_model.parameters(), 1.0)
                    optimizer2.step()
                    train_loss2 += loss2.item()
                    
                    batch_count += 1
                    
                    del batch_x, batch_exist_y, batch_vis_y, exist_outputs, vis_outputs
                    
                    if batch_idx % 10 == 0:
                        clear_memory()
                
                avg_train_loss1 = train_loss1 / batch_count
                avg_train_loss2 = train_loss2 / batch_count
                
                scheduler1.step()
                scheduler2.step()
                
                if epoch % 5 == 0:
                    val_loss1, val_loss2 = self._validate(val_loader, criterion1, criterion2)
                    
                    print(f"[EPOCH {epoch:2d}] Time: {time.time() - epoch_start:.1f}s | "
                          f"Train Loss: {avg_train_loss1:.4f}/{avg_train_loss2:.4f} | "
                          f"Val Loss: {val_loss1:.4f}/{val_loss2:.4f} | "
                          f"LR: {scheduler1.get_last_lr()[0]:.6f}")
                    
                    if val_loss1 < best_existence_loss:
                        best_existence_loss = val_loss1
                        print(f"[SAVE] New best existence model (loss: {val_loss1:.4f})")
                        self.save_models()
                    
                    if val_loss2 < best_visibility_loss:
                        best_visibility_loss = val_loss2
                        print(f"[SAVE] New best visibility model (loss: {val_loss2:.4f})")
                    
                    log_memory(f"Epoch {epoch}")
                
                clear_memory()
            
            print(f"[CV] Fold {fold + 1} completed")
            log_memory(f"Fold {fold + 1} completed")
        
        print(f"\n[CV] Cross-validation completed")
        print(f"[CV] Best losses - Existence: {best_existence_loss:.4f}, Visibility: {best_visibility_loss:.4f}")
    
    def _validate(self, val_loader, criterion1, criterion2) -> Tuple[float, float]:
        self.existence_model.eval()
        self.visibility_model.eval()
        
        total_loss1, total_loss2 = 0.0, 0.0
        batch_count = 0
        
        with torch.no_grad():
            for batch_x, batch_exist_y, batch_vis_y in val_loader:
                batch_x = batch_x.to(device)
                batch_exist_y = batch_exist_y.to(device)
                batch_vis_y = batch_vis_y.to(device)
                
                exist_outputs = self.existence_model(batch_x)
                vis_outputs = self.visibility_model(batch_x)
                
                total_loss1 += criterion1(exist_outputs, batch_exist_y).item()
                total_loss2 += criterion2(vis_outputs, batch_vis_y).item()
                batch_count += 1
                
                del batch_x, batch_exist_y, batch_vis_y, exist_outputs, vis_outputs
        
        clear_memory()
        return total_loss1 / batch_count, total_loss2 / batch_count
    
    def save_models(self):
        try:
            print(f"[SAVE] Saving models to {self.model_dir}/...")
            torch.save(self.existence_model.state_dict(), f'{self.model_dir}/existence_model.pth')
            torch.save(self.visibility_model.state_dict(), f'{self.model_dir}/visibility_model.pth')
            with open(f'{self.model_dir}/feature_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            with open(f'{self.model_dir}/feature_engineer.pkl', 'wb') as f:
                pickle.dump(self.feature_engineer, f)
            print("[SAVE] Models saved successfully")
        except Exception as e:
            print(f"[ERROR] Failed to save models: {e}")
            traceback.print_exc()
    
    def load_models(self) -> bool:
        try:
            print(f"[LOAD] Loading models from {self.model_dir}/...")
            
            if not self.models_exist:
                print("[ERROR] Model files not found")
                return False
            
            sample_features = self.feature_engineer.extract_advanced_features("sample-host")
            contextual_features = np.zeros(32)
            input_size = len(np.concatenate([sample_features, contextual_features]))
            
            print(f"[LOAD] Initializing models with input size: {input_size}")
            
            self.existence_model = CompactTransformer(input_size, self.config, output_dim=1).to(device)
            self.visibility_model = SimpleMoE(input_size, num_experts=2, output_dim=5).to(device)
            
            print("[LOAD] Loading model weights...")
            self.existence_model.load_state_dict(torch.load(f'{self.model_dir}/existence_model.pth', map_location=device))
            self.visibility_model.load_state_dict(torch.load(f'{self.model_dir}/visibility_model.pth', map_location=device))
            
            print("[LOAD] Loading scalers and encoders...")
            with open(f'{self.model_dir}/feature_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            with open(f'{self.model_dir}/feature_engineer.pkl', 'rb') as f:
                self.feature_engineer = pickle.load(f)
            
            self.trained = True
            print("[SUCCESS] Models loaded successfully")
            log_memory("Models loaded")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load models: {e}")
            traceback.print_exc()
            return False
    
    def predict_missing_assets(self, business_unit_filter: Optional[str] = None) -> List[Dict]:
        print(f"\n[PREDICT] Starting prediction (filter: {business_unit_filter or 'None'})")
        
        if not self.trained:
            print("[PREDICT] Models not trained, attempting to initialize...")
            self.initialize_models()
            if not self.trained:
                print("[ERROR] Unable to initialize models")
                return []
        
        print("[PREDICT] Fetching CMDB data...")
        df = self.get_cmdb_data()
        if df.empty:
            print("[ERROR] No CMDB data available")
            return []
        
        if business_unit_filter:
            df = df[df['business_unit'] == business_unit_filter]
            print(f"[PREDICT] Filtered to {len(df)} records for BU: {business_unit_filter}")
        
        print("[PREDICT] Analyzing hostname patterns...")
        hostname_patterns = self._analyze_advanced_patterns(df)
        print(f"[PREDICT] Found {len(hostname_patterns)} patterns")
        
        predicted_assets = []
        existing_hostnames = set(df['host'].values)
        
        self.existence_model.eval()
        self.visibility_model.eval()
        
        pattern_limit = min(10, len(hostname_patterns))
        print(f"[PREDICT] Processing top {pattern_limit} patterns...")
        
        with torch.no_grad():
            for pattern_idx, pattern in enumerate(hostname_patterns[:pattern_limit]):
                if pattern_idx % 5 == 0:
                    print(f"[PREDICT] Processing pattern {pattern_idx + 1}/{pattern_limit}")
                    clear_memory()
                
                candidates = self._generate_candidates(pattern, existing_hostnames)
                
                for candidate in candidates[:30]:
                    features = self._prepare_prediction_features(candidate, business_unit_filter)
                    features_scaled = self.feature_scaler.transform([features])
                    features_tensor = torch.FloatTensor(features_scaled).to(device)
                    
                    exist_logits = self.existence_model(features_tensor)
                    existence_prob = torch.sigmoid(exist_logits).cpu().item()
                    
                    vis_outputs = self.visibility_model(features_tensor)
                    visibility_probs = F.softmax(vis_outputs, dim=-1).cpu().numpy()[0]
                    
                    if existence_prob > 0.65:
                        predicted_assets.append(self._create_prediction_entry(
                            candidate, existence_prob, visibility_probs, pattern, business_unit_filter
                        ))
                    
                    del features_tensor, exist_logits, vis_outputs
        
        clear_memory()
        print(f"[PREDICT] Generated {len(predicted_assets)} predictions")
        
        sorted_assets = sorted(predicted_assets, key=lambda x: x['existence_probability'] * x['visibility_risk_score'], reverse=True)[:75]
        print(f"[PREDICT] Returning top {len(sorted_assets)} predictions")
        
        return sorted_assets
    
    def _analyze_advanced_patterns(self, df: pd.DataFrame) -> List[Dict]:
        pattern_clusters = defaultdict(list)
        
        for hostname in df['host'].dropna():
            pattern_sig = self._extract_pattern_signature(hostname)
            pattern_clusters[pattern_sig].append(hostname)
        
        patterns = []
        for sig, hostnames in pattern_clusters.items():
            if len(hostnames) >= 2:
                patterns.append({
                    'signature': sig,
                    'pattern': self._reconstruct_pattern(sig),
                    'examples': hostnames[:5],
                    'count': len(hostnames),
                    'entropy': np.mean([self.feature_engineer._calculate_entropy(h) for h in hostnames])
                })
        
        return sorted(patterns, key=lambda x: x['count'] * max(x['entropy'], 0.1), reverse=True)
    
    def _extract_pattern_signature(self, hostname: str) -> str:
        sig = re.sub(r'\d+', 'NUM', hostname.lower())
        sig = re.sub(r'[a-z]{3,}', 'ALPHA', sig)
        return sig
    
    def _reconstruct_pattern(self, signature: str) -> str:
        return signature.replace('NUM', 'XXX').replace('ALPHA', 'name')
    
    def _generate_candidates(self, pattern: Dict, existing: set) -> List[str]:
        candidates = []
        base_pattern = pattern['pattern']
        
        for i in range(1, 50):
            for padding in [2, 3]:
                candidate = base_pattern.replace('XXX', str(i).zfill(padding))
                candidate = candidate.replace('name', self._generate_name_variant())
                
                if candidate not in existing:
                    candidates.append(candidate)
        
        return candidates
    
    def _generate_name_variant(self) -> str:
        variants = ['srv', 'app', 'db', 'web', 'api', 'node']
        return np.random.choice(variants)
    
    def _prepare_prediction_features(self, hostname: str, business_unit: Optional[str]) -> np.ndarray:
        hostname_features = self.feature_engineer.extract_advanced_features(hostname)
        
        contextual_features = np.zeros(32)
        if business_unit:
            contextual_features[:4] = self._encode_categorical(business_unit, 4)
        contextual_features[16:22] = [0.7, 1.6, 0.8, 0.5, 0.9, 0.3]
        
        return np.concatenate([hostname_features, contextual_features])
    
    def _create_prediction_entry(self, hostname: str, exist_prob: float, 
                                 vis_probs: np.ndarray, pattern: Dict, 
                                 business_unit: Optional[str]) -> Dict:
        return {
            'predicted_hostname': hostname,
            'existence_probability': float(exist_prob),
            'splunk_probability': float(vis_probs[3] + vis_probs[4]),
            'gso_probability': float(vis_probs[2] + vis_probs[4]),
            'cmdb_probability': float(sum(vis_probs[1:])),
            'pattern_signature': pattern['signature'],
            'business_unit': business_unit or 'Unknown',
            'predicted_role': self._classify_advanced_role(hostname),
            'predicted_log_types': self._predict_advanced_log_types(hostname),
            'visibility_risk_score': self._calculate_advanced_risk(hostname, exist_prob, vis_probs),
            'confidence_interval': self._calculate_confidence_interval(exist_prob, vis_probs)
        }
    
    def _classify_advanced_role(self, hostname: str) -> str:
        hostname_lower = hostname.lower()
        
        role_scores = {}
        role_patterns = {
            'Database Server': ['db', 'sql', 'mongo', 'redis'],
            'Web Server': ['web', 'www', 'nginx', 'apache'],
            'Application Server': ['app', 'api', 'service'],
            'Security Infrastructure': ['fw', 'firewall', 'ids', 'ips'],
            'Network Infrastructure': ['router', 'switch', 'gateway'],
            'Compute Node': ['node', 'compute', 'worker']
        }
        
        for role, patterns in role_patterns.items():
            score = sum([1.0 if p in hostname_lower else 0 for p in patterns])
            role_scores[role] = score
        
        return max(role_scores, key=role_scores.get) if max(role_scores.values()) > 0 else 'General Server'
    
    def _predict_advanced_log_types(self, hostname: str) -> List[str]:
        role = self._classify_advanced_role(hostname)
        
        log_mapping = {
            'Database Server': ['Database Audit', 'Query Logs', 'Transaction Logs'],
            'Web Server': ['Access Logs', 'Error Logs', 'SSL/TLS Logs'],
            'Application Server': ['Application Logs', 'Performance Metrics', 'API Logs'],
            'Security Infrastructure': ['Security Events', 'Threat Intelligence', 'Flow Logs'],
            'Network Infrastructure': ['Network Flow', 'SNMP Traps', 'Routing Logs'],
            'Compute Node': ['System Logs', 'Resource Metrics', 'Job Logs']
        }
        
        return log_mapping.get(role, ['System Logs', 'Security Events'])
    
    def _calculate_advanced_risk(self, hostname: str, exist_prob: float, vis_probs: np.ndarray) -> float:
        hostname_lower = hostname.lower()
        
        risk_weights = {
            'prod': 0.8,
            'database': 0.7,
            'security': 0.75,
            'critical': 0.9
        }
        
        base_risk = sum([weight for keyword, weight in risk_weights.items() if keyword in hostname_lower])
        base_risk = min(base_risk, 1.0)
        
        visibility_gap = vis_probs[0]
        
        combined_risk = (base_risk * 0.4 + exist_prob * 0.3 + visibility_gap * 0.3)
        
        return min(combined_risk, 1.0)
    
    def _calculate_confidence_interval(self, exist_prob: float, vis_probs: np.ndarray) -> Tuple[float, float]:
        std_dev = np.std(vis_probs) * 0.1
        lower = max(0, exist_prob - 1.96 * std_dev)
        upper = min(1, exist_prob + 1.96 * std_dev)
        return (float(lower), float(upper))

print("\n" + "="*60)
print("STARTING AO1 VISIBILITY PREDICTOR SERVICE")
print("="*60)

app = Flask(__name__)
ao1_predictor = AO1VisibilityPredictor()

@app.route('/api/train-visibility-model')
def train_visibility_model():
    try:
        print(f"\n[API] /train-visibility-model called")
        threading.Thread(target=ao1_predictor.train_models, daemon=True).start()
        return jsonify({
            'status': 'training_started',
            'message': 'Advanced AO1 visibility model training initiated',
            'device': str(device),
            'model_version': ao1_predictor.model_version
        })
    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility')
def predict_missing_visibility():
    try:
        print(f"\n[API] /predict-missing-visibility called")
        if not ao1_predictor.trained:
            return jsonify({
                'error': 'Models not trained yet',
                'message': 'Please train the models first using /api/train-visibility-model'
            }), 503
            
        predictions = ao1_predictor.predict_missing_assets()
        print(f"[API] Returning {len(predictions)} predictions")
        return jsonify(predictions)
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility/<business_unit>')
def predict_missing_visibility_bu(business_unit):
    try:
        print(f"\n[API] /predict-missing-visibility/{business_unit} called")
        if not ao1_predictor.trained:
            return jsonify({
                'error': 'Models not trained yet',
                'message': 'Please train the models first using /api/train-visibility-model'
            }), 503
            
        predictions = ao1_predictor.predict_missing_assets(business_unit)
        print(f"[API] Returning {len(predictions)} predictions for BU: {business_unit}")
        return jsonify(predictions)
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/visibility-model-status')
def visibility_model_status():
    print(f"\n[API] /visibility-model-status called")
    log_memory("Status check")
    return jsonify({
        'trained': ao1_predictor.trained,
        'device': str(device),
        'model_version': ao1_predictor.model_version,
        'training_metrics': ao1_predictor.training_metrics,
        'architecture': 'Compact Transformer + Simple MoE',
        'feature_dimensions': 128,
        'memory_allocated_gb': torch.mps.driver_allocated_memory() / 1e9 if device.type == 'mps' else 0,
        'last_training': datetime.now().isoformat() if ao1_predictor.trained else None
    })

@app.route('/api/visibility-gap-analysis')
def visibility_gap_analysis():
    try:
        print(f"\n[API] /visibility-gap-analysis called")
        if not ao1_predictor.trained:
            return jsonify({
                'error': 'Models not trained yet',
                'message': 'Please initialize models first'
            }), 503
            
        predictions = ao1_predictor.predict_missing_assets()
        
        if not predictions:
            return jsonify({'error': 'No predictions available'}), 204
        
        analysis = {
            'critical_visibility_gaps': [p for p in predictions if p['visibility_risk_score'] > 0.8][:20],
            'high_confidence_predictions': [p for p in predictions if p['existence_probability'] > 0.85][:20],
            'security_infrastructure_gaps': [p for p in predictions if 'Security' in p['predicted_role']][:15],
            'database_gaps': [p for p in predictions if 'Database' in p['predicted_role']][:15],
            'total_predicted_assets': len(predictions),
            'avg_existence_probability': float(np.mean([p['existence_probability'] for p in predictions])),
            'risk_distribution': {
                'critical': len([p for p in predictions if p['visibility_risk_score'] > 0.8]),
                'high': len([p for p in predictions if 0.6 < p['visibility_risk_score'] <= 0.8]),
                'medium': len([p for p in predictions if 0.4 < p['visibility_risk_score'] <= 0.6]),
                'low': len([p for p in predictions if p['visibility_risk_score'] <= 0.4])
            },
            'role_distribution': dict(Counter([p['predicted_role'] for p in predictions]).most_common()),
            'pattern_diversity': len(set([p['pattern_signature'] for p in predictions]))
        }
        
        print(f"[API] Analysis complete - {analysis['total_predicted_assets']} assets analyzed")
        return jsonify(analysis)
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-models')
def load_models():
    try:
        print(f"\n[API] /load-models called")
        success = ao1_predictor.load_models()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Models loaded successfully' if success else 'Failed to load models',
            'architecture': 'Compact Transformer + Simple MoE' if success else None
        })
    except Exception as e:
        print(f"[ERROR] Model loading failed: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("INITIALIZING AO1 VISIBILITY PREDICTOR")
    print(f"Version: {ao1_predictor.model_version}")
    print(f"Device: {device}")
    print(f"Architecture: Compact Transformer + Simple MoE")
    print("="*60 + "\n")
    
    log_memory("Startup")
    
    print("[INIT] Attempting to initialize models...")
    ao1_predictor.initialize_models()
    
    if not ao1_predictor.trained:
        print("\n[WARNING] AI models not ready. Training required.")
        print("[WARNING] Use /api/train-visibility-model endpoint to start training")
    else:
        print("\n[SUCCESS] AI models ready! Advanced inference available.")
    
    print("\n[SERVER] Starting Flask application...")
    print("[SERVER] Listening on http://0.0.0.0:5001")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')