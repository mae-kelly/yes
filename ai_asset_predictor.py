import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import pandas as pd
import re
import duckdb
from sklearn.preprocessing import RobustScaler
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

if torch.backends.mps.is_available():
    device = torch.device("mps")
    torch.mps.empty_cache()
    torch.mps.set_per_process_memory_fraction(0.95)
    print(f"[GPU] Using Apple Silicon GPU (MPS) - FULL GPU MODE")
    print(f"[GPU] Maximum memory: 18.13 GB available")
    print(f"[GPU] Target usage: 17.0 GB (leaving 1GB buffer)")
else:
    print("[ERROR] MPS not available!")
    exit(1)

def log_gpu_memory(tag=""):
    allocated = torch.mps.driver_allocated_memory() / 1e9
    cached = torch.mps.current_allocated_memory() / 1e9 if hasattr(torch.mps, 'current_allocated_memory') else 0
    remaining = 18.13 - allocated
    print(f"[GPU-MEM] {tag}: {allocated:.2f}GB used | {remaining:.2f}GB free")
    
    # Only clear if we're really close to the limit
    if allocated > 17.0:
        print(f"[WARNING] GPU memory critical: {allocated:.2f}GB - emergency cleanup")
        torch.mps.empty_cache()
        torch.mps.synchronize()
        new_allocated = torch.mps.driver_allocated_memory() / 1e9
        print(f"[GPU-MEM] After cleanup: {new_allocated:.2f}GB")
    elif tag.startswith("CLEANUP"):
        # Explicit cleanup request
        torch.mps.empty_cache()
        torch.mps.synchronize()
    
    return allocated

def periodic_cleanup(epoch, batch_idx):
    # Only cleanup every 50 batches or at epoch boundaries
    if batch_idx % 50 == 0 or batch_idx == 0:
        torch.mps.empty_cache()
        if batch_idx == 0:
            print(f"[GPU-MEM] Epoch {epoch} cleanup")
        return True
    return False

@dataclass
class ModelConfig:
    hidden_dims: List[int] = None
    dropout_rates: List[float] = None
    batch_size: int = 64
    accumulation_steps: int = 4
    mixed_precision: bool = True
    num_workers: int = 0
    pin_memory: bool = False
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [512, 384, 256, 192, 128, 64]
        if self.dropout_rates is None:
            self.dropout_rates = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35]

class GPUOptimizedAttention(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int = 4):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        self.qkv = nn.Linear(embed_dim, embed_dim * 3, bias=False, device=device)
        self.proj = nn.Linear(embed_dim, embed_dim, device=device)
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, x):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)
        
        attn = (q @ k.transpose(-2, -1)) * (self.head_dim ** -0.5)
        attn = attn.softmax(dim=-1)
        attn = self.dropout(attn)
        
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        return x

class GPUResidualBlock(nn.Module):
    def __init__(self, in_features: int, out_features: int, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, out_features * 2, device=device),
            nn.LayerNorm(out_features * 2, device=device),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(out_features * 2, out_features, device=device),
            nn.LayerNorm(out_features, device=device)
        )
        self.shortcut = nn.Linear(in_features, out_features, device=device) if in_features != out_features else nn.Identity()
        self.activation = nn.GELU()
        
    def forward(self, x):
        return self.activation(self.net(x) + self.shortcut(x))

class DeepGPUTransformer(nn.Module):
    def __init__(self, input_dim: int, config: ModelConfig, output_dim: int = 1):
        super().__init__()
        print(f"[MODEL] Building DeepGPUTransformer on MPS")
        print(f"[MODEL] Architecture: {input_dim} -> {config.hidden_dims} -> {output_dim}")
        
        layers = []
        current_dim = input_dim
        
        layers.append(nn.Linear(current_dim, config.hidden_dims[0], device=device))
        layers.append(nn.LayerNorm(config.hidden_dims[0], device=device))
        layers.append(nn.GELU())
        
        self.attention_layers = nn.ModuleList([
            GPUOptimizedAttention(config.hidden_dims[0], num_heads=4),
            GPUOptimizedAttention(config.hidden_dims[0], num_heads=4)
        ])
        
        self.residual_blocks = nn.ModuleList()
        for i in range(len(config.hidden_dims) - 1):
            self.residual_blocks.append(
                GPUResidualBlock(
                    config.hidden_dims[i],
                    config.hidden_dims[i + 1],
                    config.dropout_rates[i]
                )
            )
        
        self.input_layers = nn.Sequential(*layers)
        
        self.output_head = nn.Sequential(
            nn.Linear(config.hidden_dims[-1], config.hidden_dims[-1] // 2, device=device),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(config.hidden_dims[-1] // 2, output_dim, device=device)
        )
        
        self.to(device)
        self._init_weights()
        
        total_params = sum(p.numel() for p in self.parameters())
        print(f"[MODEL] Total parameters: {total_params:,} ({total_params * 4 / 1e9:.2f}GB FP32)")
        log_gpu_memory("Model initialized")
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
    def forward(self, x):
        x = self.input_layers(x)
        
        if x.dim() == 2:
            x = x.unsqueeze(1)
        
        for attn_layer in self.attention_layers:
            residual = x
            x = attn_layer(x) + residual
        
        x = x.squeeze(1) if x.size(1) == 1 else x.mean(dim=1)
        
        for block in self.residual_blocks:
            x = block(x)
        
        return self.output_head(x)

class GPUMixtureOfExperts(nn.Module):
    def __init__(self, input_dim: int, num_experts: int = 4, hidden_dim: int = 256, output_dim: int = 5):
        super().__init__()
        print(f"[MODEL] Building GPU MoE: {num_experts} experts")
        self.num_experts = num_experts
        
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, hidden_dim, device=device),
                nn.LayerNorm(hidden_dim, device=device),
                nn.GELU(),
                nn.Dropout(0.2),
                nn.Linear(hidden_dim, hidden_dim // 2, device=device),
                nn.GELU(),
                nn.Linear(hidden_dim // 2, output_dim, device=device)
            ) for _ in range(num_experts)
        ])
        
        self.router = nn.Sequential(
            nn.Linear(input_dim, hidden_dim, device=device),
            nn.GELU(),
            nn.Linear(hidden_dim, num_experts, device=device)
        )
        
        self.to(device)
        total_params = sum(p.numel() for p in self.parameters())
        print(f"[MODEL] MoE parameters: {total_params:,} ({total_params * 4 / 1e9:.2f}GB FP32)")
        log_gpu_memory("MoE initialized")
    
    def forward(self, x):
        router_logits = self.router(x)
        router_probs = F.softmax(router_logits, dim=-1)
        
        expert_outputs = torch.stack([expert(x) for expert in self.experts], dim=1)
        output = torch.einsum('bn,bnd->bd', router_probs, expert_outputs)
        
        return output

class AdvancedFeatureEngineering:
    def __init__(self):
        self.feature_dim = 128
        self.cache = {}
        print(f"[FEATURES] Advanced feature engineering: {self.feature_dim} dimensions")
        
    @lru_cache(maxsize=50000)
    def extract_features(self, hostname: str) -> np.ndarray:
        if not hostname:
            return np.zeros(self.feature_dim)
        
        hostname = hostname.lower().strip()
        
        features = []
        
        features.extend(self._structural_features(hostname))
        features.extend(self._semantic_embeddings(hostname))
        features.extend(self._statistical_features(hostname))
        features.extend(self._pattern_features(hostname))
        features.extend(self._ngram_features(hostname))
        features.extend(self._positional_encoding(hostname))
        
        feature_array = np.array(features[:self.feature_dim])
        if len(feature_array) < self.feature_dim:
            feature_array = np.pad(feature_array, (0, self.feature_dim - len(feature_array)))
        
        return feature_array
    
    def _structural_features(self, hostname: str) -> List[float]:
        return [
            len(hostname) / 100.0,
            hostname.count('.') / 10.0,
            hostname.count('-') / 10.0,
            hostname.count('_') / 10.0,
            len(re.findall(r'\d+', hostname)) / 10.0,
            len(re.findall(r'[a-z]+', hostname)) / 10.0,
            len(set(hostname)) / len(hostname) if hostname else 0,
            self._calculate_entropy(hostname),
            max([len(p) for p in hostname.split('.')]) / 50.0 if '.' in hostname else len(hostname) / 50.0,
            min([len(p) for p in hostname.split('.')]) / 50.0 if '.' in hostname else len(hostname) / 50.0,
            np.std([len(p) for p in hostname.split('.')]) / 10.0 if '.' in hostname and len(hostname.split('.')) > 1 else 0,
            1.0 if hostname.startswith(('srv', 'server')) else 0.0,
            1.0 if hostname.startswith(('web', 'www')) else 0.0,
            1.0 if hostname.startswith(('db', 'database')) else 0.0,
            1.0 if hostname.startswith(('app', 'api')) else 0.0,
            1.0 if 'prod' in hostname else 0.0,
            1.0 if 'dev' in hostname else 0.0,
            1.0 if 'test' in hostname else 0.0,
            1.0 if any(cloud in hostname for cloud in ['aws', 'azure', 'gcp']) else 0.0,
            1.0 if any(dc in hostname for dc in ['dc', '1dc', 'fead']) else 0.0,
        ]
    
    def _semantic_embeddings(self, hostname: str) -> List[float]:
        embeddings = []
        
        semantic_groups = {
            'infrastructure': ['srv', 'server', 'host', 'node', 'instance', 'machine', 'vm', 'virtual'],
            'network': ['fw', 'firewall', 'router', 'switch', 'gateway', 'proxy', 'lb', 'loadbalancer'],
            'database': ['db', 'database', 'sql', 'mongo', 'redis', 'postgres', 'mysql', 'oracle'],
            'application': ['app', 'api', 'web', 'www', 'service', 'microservice', 'backend', 'frontend'],
            'security': ['ids', 'ips', 'ndr', 'waf', 'scanner', 'defender', 'guard', 'shield'],
            'monitoring': ['monitor', 'metric', 'log', 'trace', 'observ', 'telemetry', 'apm', 'siem'],
            'storage': ['storage', 'nas', 'san', 'backup', 'archive', 'vault', 'repo', 'registry'],
            'compute': ['compute', 'worker', 'executor', 'processor', 'calculator', 'solver', 'runner']
        }
        
        for category, keywords in semantic_groups.items():
            scores = [2.0 / (1.0 + hostname.find(kw)) if kw in hostname else 0.0 for kw in keywords]
            embeddings.extend([
                max(scores) if scores else 0.0,
                sum(scores) / len(scores) if scores else 0.0,
                len([s for s in scores if s > 0]) / len(keywords)
            ])
        
        return embeddings
    
    def _statistical_features(self, hostname: str) -> List[float]:
        features = []
        
        numbers = re.findall(r'\d+', hostname)
        if numbers:
            nums = [float(n) for n in numbers]
            features.extend([
                np.mean(nums) / 1000.0,
                np.std(nums) / 1000.0 if len(nums) > 1 else 0.0,
                np.min(nums) / 1000.0,
                np.max(nums) / 1000.0,
                np.median(nums) / 1000.0,
                len(nums) / 10.0
            ])
        else:
            features.extend([0.0] * 6)
        
        alpha_parts = re.findall(r'[a-z]+', hostname)
        if alpha_parts:
            lengths = [len(p) for p in alpha_parts]
            features.extend([
                np.mean(lengths) / 20.0,
                np.std(lengths) / 10.0 if len(lengths) > 1 else 0.0,
                np.min(lengths) / 20.0,
                np.max(lengths) / 20.0,
                len(alpha_parts) / 10.0
            ])
        else:
            features.extend([0.0] * 5)
        
        char_freq = Counter(hostname)
        total_chars = len(hostname)
        for char in 'abcdefghijklmnopqrstuvwxyz0123456789.-_':
            features.append(char_freq.get(char, 0) / total_chars if total_chars > 0 else 0.0)
        
        return features
    
    def _pattern_features(self, hostname: str) -> List[float]:
        pattern_sig = re.sub(r'\d+', 'NUM', hostname)
        pattern_sig = re.sub(r'[a-z]{3,}', 'ALPHA', pattern_sig)
        
        pattern_hash = hashlib.sha256(pattern_sig.encode()).digest()
        features = [float(b) / 255.0 for b in pattern_hash[:32]]
        
        pattern_types = {
            'sequential': r'.*\d{2,}.*',
            'hierarchical': r'.*\..*\..*',
            'segmented': r'.*-.*-.*',
            'mixed': r'.*[a-z]+\d+[a-z]+.*',
            'prefixed': r'^[a-z]{2,5}\d+.*',
            'suffixed': r'.*\d+[a-z]{2,5}$'
        }
        
        for ptype, regex in pattern_types.items():
            features.append(1.0 if re.match(regex, hostname) else 0.0)
        
        return features
    
    def _ngram_features(self, hostname: str, n_values=[2, 3, 4]) -> List[float]:
        features = []
        
        for n in n_values:
            if len(hostname) >= n:
                ngrams = [hostname[i:i+n] for i in range(len(hostname) - n + 1)]
                ngram_counts = Counter(ngrams)
                
                top_ngrams = ngram_counts.most_common(10)
                for ngram, count in top_ngrams:
                    features.append(count / len(ngrams))
                
                for _ in range(10 - len(top_ngrams)):
                    features.append(0.0)
            else:
                features.extend([0.0] * 10)
        
        return features
    
    def _positional_encoding(self, hostname: str, d_model: int = 64) -> List[float]:
        features = []
        max_len = 100
        
        for pos in range(min(len(hostname), max_len)):
            for i in range(d_model // 2):
                angle = pos / (10000 ** (2 * i / d_model))
                features.append(np.sin(angle))
                features.append(np.cos(angle))
                
                if len(features) >= d_model:
                    break
            
            if len(features) >= d_model:
                break
        
        while len(features) < d_model:
            features.append(0.0)
        
        return features[:d_model]
    
    def _calculate_entropy(self, s: str) -> float:
        if not s:
            return 0.0
        prob = [float(s.count(c)) / len(s) for c in set(s)]
        return -sum([p * np.log2(p) for p in prob if p > 0])

class AO1VisibilityPredictor:
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        print("\n" + "="*80)
        print("AO1 VISIBILITY PREDICTOR - FULL GPU MODE")
        print("="*80)
        
        self.db_path = db_path
        self.model_dir = 'models'
        self.model_version = "3.0-GPU"
        self.trained = False
        self.training_metrics = {}
        
        self.config = ModelConfig()
        self.feature_engineer = AdvancedFeatureEngineering()
        self.feature_scaler = RobustScaler()
        
        self.existence_model = None
        self.visibility_model = None
        
        os.makedirs(self.model_dir, exist_ok=True)
        
        log_gpu_memory("Initialization")
        print(f"[INIT] Feature dimensions: {self.feature_engineer.feature_dim}")
        print(f"[INIT] Batch size: {self.config.batch_size}")
        print(f"[INIT] Model directory: {self.model_dir}")
    
    @property
    def models_exist(self) -> bool:
        required = [
            f'{self.model_dir}/existence_model.pth',
            f'{self.model_dir}/visibility_model.pth',
            f'{self.model_dir}/feature_scaler.pkl',
            f'{self.model_dir}/feature_engineer.pkl'
        ]
        exists = all(os.path.exists(f) for f in required)
        print(f"[CHECK] Model files exist: {exists}")
        return exists
    
    def initialize_models(self):
        print("\n[INIT] Initializing models...")
        log_gpu_memory("Before model init")
        
        if self.models_exist:
            print("[INIT] Found saved models, loading...")
            if self.load_models():
                print("[SUCCESS] Models loaded from disk")
                return True
            print("[WARNING] Failed to load, will train new models")
        
        print("[INIT] Training new models...")
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
        print("\n[DATA] Loading CMDB data...")
        conn = self.get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        query = """
        SELECT host, business_unit, region, country, data_center, cloud_region,
               system_classification, infrastructure_type, cio, apm,
               logging_in_splunk, logging_in_gso, present_in_cmdb,
               edr_coverage, tanium_coverage, dlp_agent_coverage,
               first_seen, last_updated, data_quality_score, source_count
        FROM universal_cmdb
        """
        
        try:
            df = conn.execute(query).df()
            print(f"[DATA] Loaded {len(df)} records")
            print(f"[DATA] Memory usage: {df.memory_usage(deep=True).sum() / 1e6:.2f} MB")
            return df
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            traceback.print_exc()
            return pd.DataFrame()
        finally:
            conn.close()
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        print(f"\n[PREP] Preparing {len(df)} records for training...")
        start_time = time.time()
        
        features = []
        existence_labels = []
        visibility_labels = []
        
        for idx, row in df.iterrows():
            if idx % 500 == 0:
                print(f"[PREP] Processing {idx}/{len(df)} records...")
                log_gpu_memory(f"Record {idx}")
            
            hostname_features = self.feature_engineer.extract_features(row['host'])
            context_features = self._extract_context_features(row)
            
            combined = np.concatenate([hostname_features, context_features])
            features.append(combined)
            
            existence_labels.append(self._calculate_existence_score(row))
            visibility_labels.append(self._calculate_visibility_class(row))
        
        X = np.array(features, dtype=np.float32)
        y_exist = np.array(existence_labels, dtype=np.float32)
        y_vis = np.array(visibility_labels, dtype=np.int64)
        
        print(f"[PREP] Completed in {time.time() - start_time:.1f}s")
        print(f"[PREP] Features shape: {X.shape}")
        print(f"[PREP] Existence distribution: mean={y_exist.mean():.3f}, std={y_exist.std():.3f}")
        print(f"[PREP] Visibility distribution: {Counter(y_vis)}")
        
        return X, y_exist, y_vis
    
    def _extract_context_features(self, row) -> np.ndarray:
        features = []
        
        for col in ['business_unit', 'region', 'infrastructure_type', 'system_classification']:
            val = str(row.get(col, '')).lower() if pd.notna(row.get(col)) else ''
            hash_val = int(hashlib.md5(val.encode()).hexdigest()[:8], 16)
            for i in range(8):
                features.append(np.sin(hash_val / (10000 ** (2 * i / 8))))
        
        features.extend([
            float(row.get('data_quality_score', 0)) / 10.0,
            np.log1p(float(row.get('source_count', 0))) / 10.0,
            1.0 if pd.notna(row.get('cio')) else 0.0,
            1.0 if pd.notna(row.get('apm')) else 0.0,
        ])
        
        for col in ['first_seen', 'last_updated']:
            if pd.notna(row.get(col)):
                try:
                    date = datetime.fromisoformat(str(row.get(col)))
                    days_ago = (datetime.now() - date).days
                    features.append(1.0 / (1.0 + np.log1p(days_ago)))
                except:
                    features.append(0.0)
            else:
                features.append(0.0)
        
        while len(features) < 64:
            features.append(0.0)
        
        return np.array(features[:64], dtype=np.float32)
    
    def _calculate_existence_score(self, row) -> float:
        score = 0.0
        weights = {
            'logging_in_splunk': 0.35,
            'present_in_cmdb': 0.35,
            'edr_coverage': 0.2,
            'tanium_coverage': 0.1
        }
        
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
        print("\n" + "="*80)
        print("TRAINING PHASE - GPU OPTIMIZED")
        print("="*80)
        
        # Clean start
        torch.mps.empty_cache()
        torch.mps.synchronize()
        log_gpu_memory("Training start")
        
        df = self.get_cmdb_data()
        if df.empty:
            print("[ERROR] No training data available")
            return
        
        X, y_exist, y_vis = self.prepare_training_data(df)
        
        print("\n[SCALE] Scaling features...")
        X_scaled = self.feature_scaler.fit_transform(X)
        X_scaled = X_scaled.astype(np.float32)
        
        input_dim = X_scaled.shape[1]
        print(f"[MODEL] Input dimension: {input_dim}")
        
        print("\n[BUILD] Creating GPU models...")
        self.existence_model = DeepGPUTransformer(input_dim, self.config, output_dim=1).to(device)
        self.visibility_model = GPUMixtureOfExperts(input_dim, num_experts=4, hidden_dim=256, output_dim=5).to(device)
        
        log_gpu_memory("Models created")
        
        self._train_with_gpu_optimization(X_scaled, y_exist, y_vis)
        
        self.trained = True
        print("\n[SUCCESS] Training completed!")
        log_gpu_memory("Training finished")
    
    def _train_with_gpu_optimization(self, X: np.ndarray, y_exist: np.ndarray, y_vis: np.ndarray):
        print("\n[TRAIN] GPU-optimized training starting...")
        
        X_tensor = torch.tensor(X, dtype=torch.float32, device=device)
        y_exist_tensor = torch.tensor(y_exist.reshape(-1, 1), dtype=torch.float32, device=device)
        y_vis_tensor = torch.tensor(y_vis, dtype=torch.long, device=device)
        
        log_gpu_memory("Data on GPU")
        
        dataset = torch.utils.data.TensorDataset(X_tensor, y_exist_tensor, y_vis_tensor)
        
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
        
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0,
            pin_memory=False
        )
        
        val_loader = torch.utils.data.DataLoader(
            val_dataset,
            batch_size=self.config.batch_size * 2,
            shuffle=False,
            num_workers=0,
            pin_memory=False
        )
        
        print(f"[TRAIN] Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
        
        optimizer1 = optim.AdamW(self.existence_model.parameters(), lr=0.0003, weight_decay=1e-5, betas=(0.9, 0.999))
        optimizer2 = optim.AdamW(self.visibility_model.parameters(), lr=0.0003, weight_decay=1e-5, betas=(0.9, 0.999))
        
        scheduler1 = optim.lr_scheduler.OneCycleLR(
            optimizer1,
            max_lr=0.001,
            total_steps=len(train_loader) * 100,
            pct_start=0.1,
            anneal_strategy='cos'
        )
        scheduler2 = optim.lr_scheduler.OneCycleLR(
            optimizer2,
            max_lr=0.001,
            total_steps=len(train_loader) * 100,
            pct_start=0.1,
            anneal_strategy='cos'
        )
        
        criterion1 = nn.BCEWithLogitsLoss().to(device)
        criterion2 = nn.CrossEntropyLoss(label_smoothing=0.1).to(device)
        
        best_val_loss = float('inf')
        patience = 0
        max_patience = 20
        
        print("\n[TRAIN] Starting training epochs...")
        
        for epoch in range(100):
            epoch_start = time.time()
            
            self.existence_model.train()
            self.visibility_model.train()
            
            train_loss1_total = 0
            train_loss2_total = 0
            
            for batch_idx, (batch_x, batch_y_exist, batch_y_vis) in enumerate(train_loader):
                optimizer1.zero_grad(set_to_none=True)
                exist_out = self.existence_model(batch_x)
                loss1 = criterion1(exist_out, batch_y_exist)
                loss1.backward()
                torch.nn.utils.clip_grad_norm_(self.existence_model.parameters(), 1.0)
                optimizer1.step()
                scheduler1.step()
                train_loss1_total += loss1.item()
                
                optimizer2.zero_grad(set_to_none=True)
                vis_out = self.visibility_model(batch_x)
                loss2 = criterion2(vis_out, batch_y_vis)
                loss2.backward()
                torch.nn.utils.clip_grad_norm_(self.visibility_model.parameters(), 1.0)
                optimizer2.step()
                scheduler2.step()
                train_loss2_total += loss2.item()
                
                # Only cleanup periodically, not every batch
                if periodic_cleanup(epoch, batch_idx):
                    pass  # Cleanup handled in function
            
            avg_train_loss1 = train_loss1_total / len(train_loader)
            avg_train_loss2 = train_loss2_total / len(train_loader)
            
            if epoch % 5 == 0:
                val_loss1, val_loss2 = self._validate_gpu(val_loader, criterion1, criterion2)
                total_val_loss = val_loss1 + val_loss2
                
                current_lr = scheduler1.get_last_lr()[0]
                epoch_time = time.time() - epoch_start
                
                print(f"[EPOCH {epoch:3d}] Time: {epoch_time:.1f}s | "
                      f"Train: {avg_train_loss1:.4f}/{avg_train_loss2:.4f} | "
                      f"Val: {val_loss1:.4f}/{val_loss2:.4f} | "
                      f"LR: {current_lr:.6f}")
                
                if total_val_loss < best_val_loss:
                    best_val_loss = total_val_loss
                    patience = 0
                    print(f"[SAVE] New best model (val_loss: {total_val_loss:.4f})")
                    self.save_models()
                else:
                    patience += 1
                
                if patience >= max_patience:
                    print(f"[STOP] Early stopping at epoch {epoch}")
                    break
                
                # Only cleanup at validation intervals
                if epoch % 10 == 0:
                    torch.mps.empty_cache()
        
        print(f"\n[TRAIN] Completed - Best validation loss: {best_val_loss:.4f}")
    
    def _validate_gpu(self, val_loader, criterion1, criterion2) -> Tuple[float, float]:
        self.existence_model.eval()
        self.visibility_model.eval()
        
        total_loss1 = 0
        total_loss2 = 0
        
        with torch.no_grad():
            for batch_x, batch_y_exist, batch_y_vis in val_loader:
                exist_out = self.existence_model(batch_x)
                vis_out = self.visibility_model(batch_x)
                
                total_loss1 += criterion1(exist_out, batch_y_exist).item()
                total_loss2 += criterion2(vis_out, batch_y_vis).item()
        
        return total_loss1 / len(val_loader), total_loss2 / len(val_loader)
    
    def save_models(self):
        try:
            print(f"[SAVE] Saving models to {self.model_dir}/")
            torch.save(self.existence_model.state_dict(), f'{self.model_dir}/existence_model.pth')
            torch.save(self.visibility_model.state_dict(), f'{self.model_dir}/visibility_model.pth')
            with open(f'{self.model_dir}/feature_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            with open(f'{self.model_dir}/feature_engineer.pkl', 'wb') as f:
                pickle.dump(self.feature_engineer, f)
            print("[SAVE] Models saved successfully")
        except Exception as e:
            print(f"[ERROR] Save failed: {e}")
    
    def load_models(self) -> bool:
        try:
            print("[LOAD] Loading models from disk...")
            
            with open(f'{self.model_dir}/feature_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            with open(f'{self.model_dir}/feature_engineer.pkl', 'rb') as f:
                self.feature_engineer = pickle.load(f)
            
            sample = self.feature_engineer.extract_features("test")
            context = np.zeros(64)
            input_dim = len(np.concatenate([sample, context]))
            
            self.existence_model = DeepGPUTransformer(input_dim, self.config, output_dim=1).to(device)
            self.visibility_model = GPUMixtureOfExperts(input_dim, num_experts=4, hidden_dim=256, output_dim=5).to(device)
            
            self.existence_model.load_state_dict(
                torch.load(f'{self.model_dir}/existence_model.pth', map_location=device)
            )
            self.visibility_model.load_state_dict(
                torch.load(f'{self.model_dir}/visibility_model.pth', map_location=device)
            )
            
            self.trained = True
            print("[LOAD] Models loaded successfully")
            log_gpu_memory("Models loaded")
            return True
            
        except Exception as e:
            print(f"[ERROR] Load failed: {e}")
            traceback.print_exc()
            return False
    
    def predict_missing_assets(self, business_unit_filter: Optional[str] = None) -> List[Dict]:
        print(f"\n[PREDICT] Starting prediction (BU filter: {business_unit_filter or 'None'})")
        
        if not self.trained:
            print("[PREDICT] Models not ready, initializing...")
            self.initialize_models()
            if not self.trained:
                return []
        
        # Single cleanup at start
        torch.mps.empty_cache()
        log_gpu_memory("Prediction start")
        
        df = self.get_cmdb_data()
        if df.empty:
            return []
        
        if business_unit_filter:
            df = df[df['business_unit'] == business_unit_filter]
        
        patterns = self._analyze_patterns(df)
        existing = set(df['host'].values)
        predictions = []
        
        self.existence_model.eval()
        self.visibility_model.eval()
        
        print(f"[PREDICT] Processing {min(20, len(patterns))} patterns...")
        
        with torch.no_grad():
            for idx, pattern in enumerate(patterns[:20]):
                if idx % 10 == 0 and idx > 0:
                    # Only log memory occasionally
                    log_gpu_memory(f"Pattern {idx}")
                
                candidates = self._generate_candidates(pattern, existing)
                
                batch_features = []
                batch_candidates = []
                
                for candidate in candidates[:50]:
                    features = self._prepare_features(candidate, business_unit_filter)
                    batch_features.append(features)
                    batch_candidates.append(candidate)
                    
                    if len(batch_features) >= 32:
                        self._process_batch(
                            batch_features, batch_candidates, predictions,
                            pattern, business_unit_filter
                        )
                        batch_features = []
                        batch_candidates = []
                
                if batch_features:
                    self._process_batch(
                        batch_features, batch_candidates, predictions,
                        pattern, business_unit_filter
                    )
        
        # Final cleanup
        torch.mps.empty_cache()
        
        sorted_predictions = sorted(
            predictions,
            key=lambda x: x['existence_probability'] * x['visibility_risk_score'],
            reverse=True
        )[:100]
        
        print(f"[PREDICT] Returning {len(sorted_predictions)} predictions")
        return sorted_predictions
    
    def _process_batch(self, features, candidates, predictions, pattern, bu_filter):
        features_array = np.array(features, dtype=np.float32)
        features_scaled = self.feature_scaler.transform(features_array)
        features_tensor = torch.tensor(features_scaled, dtype=torch.float32, device=device)
        
        exist_logits = self.existence_model(features_tensor)
        exist_probs = torch.sigmoid(exist_logits).cpu().numpy()
        
        vis_outputs = self.visibility_model(features_tensor)
        vis_probs = F.softmax(vis_outputs, dim=-1).cpu().numpy()
        
        for i, candidate in enumerate(candidates):
            if exist_probs[i] > 0.6:
                predictions.append(self._create_prediction(
                    candidate, exist_probs[i].item(), vis_probs[i],
                    pattern, bu_filter
                ))
    
    def _analyze_patterns(self, df: pd.DataFrame) -> List[Dict]:
        patterns = defaultdict(list)
        
        for hostname in df['host'].dropna():
            sig = re.sub(r'\d+', 'NUM', hostname.lower())
            sig = re.sub(r'[a-z]{3,}', 'ALPHA', sig)
            patterns[sig].append(hostname)
        
        result = []
        for sig, hosts in patterns.items():
            if len(hosts) >= 2:
                result.append({
                    'signature': sig,
                    'pattern': sig.replace('NUM', 'XXX').replace('ALPHA', 'name'),
                    'count': len(hosts),
                    'examples': hosts[:3]
                })
        
        return sorted(result, key=lambda x: x['count'], reverse=True)
    
    def _generate_candidates(self, pattern: Dict, existing: set) -> List[str]:
        candidates = []
        base = pattern['pattern']
        
        for i in range(1, 100):
            for pad in [2, 3]:
                candidate = base.replace('XXX', str(i).zfill(pad))
                candidate = candidate.replace('name', np.random.choice(['srv', 'app', 'db', 'web']))
                
                if candidate not in existing:
                    candidates.append(candidate)
        
        return candidates[:50]
    
    def _prepare_features(self, hostname: str, bu: Optional[str]) -> np.ndarray:
        host_features = self.feature_engineer.extract_features(hostname)
        context_features = np.zeros(64, dtype=np.float32)
        
        if bu:
            hash_val = int(hashlib.md5(bu.encode()).hexdigest()[:8], 16)
            for i in range(8):
                context_features[i] = np.sin(hash_val / (10000 ** (2 * i / 8)))
        
        return np.concatenate([host_features, context_features])
    
    def _create_prediction(self, hostname: str, exist_prob: float,
                          vis_probs: np.ndarray, pattern: Dict,
                          bu: Optional[str]) -> Dict:
        return {
            'predicted_hostname': hostname,
            'existence_probability': float(exist_prob),
            'splunk_probability': float(vis_probs[3] + vis_probs[4]),
            'gso_probability': float(vis_probs[2] + vis_probs[4]),
            'cmdb_probability': float(sum(vis_probs[1:])),
            'pattern_signature': pattern['signature'],
            'business_unit': bu or 'Unknown',
            'predicted_role': self._classify_role(hostname),
            'visibility_risk_score': self._calculate_risk(hostname, exist_prob, vis_probs)
        }
    
    def _classify_role(self, hostname: str) -> str:
        h = hostname.lower()
        if any(x in h for x in ['db', 'sql', 'mongo']):
            return 'Database'
        elif any(x in h for x in ['web', 'www', 'nginx']):
            return 'Web Server'
        elif any(x in h for x in ['app', 'api']):
            return 'Application'
        elif any(x in h for x in ['fw', 'firewall']):
            return 'Security'
        return 'Server'
    
    def _calculate_risk(self, hostname: str, exist_prob: float, vis_probs: np.ndarray) -> float:
        h = hostname.lower()
        risk = 0.0
        
        if 'prod' in h:
            risk += 0.3
        if any(x in h for x in ['db', 'database']):
            risk += 0.25
        if any(x in h for x in ['fw', 'security']):
            risk += 0.2
        
        risk += exist_prob * 0.2
        risk += vis_probs[0] * 0.3
        
        return min(risk, 1.0)

print("\n" + "="*80)
print("AO1 VISIBILITY PREDICTOR - GPU SERVICE")
print("="*80)

app = Flask(__name__)
predictor = AO1VisibilityPredictor()

@app.route('/api/train-visibility-model')
def train_visibility_model():
    try:
        print(f"\n[API] Training requested")
        log_gpu_memory("API call")
        threading.Thread(target=predictor.train_models, daemon=True).start()
        return jsonify({
            'status': 'training_started',
            'device': 'MPS GPU',
            'model_version': predictor.model_version
        })
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility')
def predict_missing_visibility():
    try:
        print(f"\n[API] Prediction requested")
        if not predictor.trained:
            return jsonify({'error': 'Models not trained'}), 503
        predictions = predictor.predict_missing_assets()
        return jsonify(predictions)
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility/<business_unit>')
def predict_missing_visibility_bu(business_unit):
    try:
        print(f"\n[API] Prediction for BU: {business_unit}")
        if not predictor.trained:
            return jsonify({'error': 'Models not trained'}), 503
        predictions = predictor.predict_missing_assets(business_unit)
        return jsonify(predictions)
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/visibility-model-status')
def visibility_model_status():
    mem = torch.mps.driver_allocated_memory() / 1e9
    return jsonify({
        'trained': predictor.trained,
        'device': 'Apple Silicon GPU (MPS)',
        'gpu_memory_gb': mem,
        'gpu_memory_free_gb': 18.13 - mem,
        'model_version': predictor.model_version,
        'architecture': 'DeepGPUTransformer + MoE'
    })

@app.route('/api/visibility-gap-analysis')
def visibility_gap_analysis():
    try:
        print(f"\n[API] Gap analysis requested")
        if not predictor.trained:
            return jsonify({'error': 'Models not trained'}), 503
            
        predictions = predictor.predict_missing_assets()
        
        analysis = {
            'critical_gaps': [p for p in predictions if p['visibility_risk_score'] > 0.7][:25],
            'high_confidence': [p for p in predictions if p['existence_probability'] > 0.8][:25],
            'total_predicted': len(predictions),
            'avg_confidence': np.mean([p['existence_probability'] for p in predictions]) if predictions else 0
        }
        
        return jsonify(analysis)
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-models')
def load_models():
    try:
        print(f"\n[API] Model loading requested")
        success = predictor.load_models()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Models loaded' if success else 'Load failed'
        })
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n[START] Initializing service...")
    print(f"[START] GPU Memory Limit: 18.13 GB")
    print(f"[START] Target Usage: 17.0 GB")
    
    log_gpu_memory("Startup")
    
    predictor.initialize_models()
    
    if predictor.trained:
        print("\n[READY] Models loaded and ready")
    else:
        print("\n[READY] Service ready - models need training")
        print("[READY] Use /api/train-visibility-model to train")
    
    log_gpu_memory("Ready")
    
    print("\n[SERVER] Starting on http://0.0.0.0:5001")
    print("="*80 + "\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')