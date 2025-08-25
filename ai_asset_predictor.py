import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.cuda.amp import autocast, GradScaler
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

if torch.backends.mps.is_available():
    device = torch.device("mps")
    torch.mps.empty_cache()
    print("Using Apple Silicon GPU (MPS)")
else:
    print("ERROR: MPS not available!")
    exit(1)

@dataclass
class ModelConfig:
    hidden_dims: List[int] = None
    dropout_rates: List[float] = None
    activation: str = 'gelu'
    use_batch_norm: bool = True
    use_layer_norm: bool = True
    residual_connections: bool = True
    attention_heads: int = 4
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [768, 512, 384, 256, 128]
        if self.dropout_rates is None:
            self.dropout_rates = [0.15, 0.2, 0.25, 0.3, 0.35]

class SelfAttention(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int = 4):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        assert self.head_dim * num_heads == embed_dim
        
        self.qkv = nn.Linear(embed_dim, embed_dim * 3, bias=False)
        self.o = nn.Linear(embed_dim, embed_dim)
        self.scale = self.head_dim ** -0.5
        
    def forward(self, x):
        B, L, D = x.shape
        qkv = self.qkv(x).reshape(B, L, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = F.softmax(attn, dim=-1)
        
        x = (attn @ v).transpose(1, 2).reshape(B, L, D)
        return self.o(x)

class ResidualBlock(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, dropout: float = 0.2, 
                 use_batch_norm: bool = True, use_layer_norm: bool = True):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, out_dim * 2)
        self.fc2 = nn.Linear(out_dim * 2, out_dim)
        self.shortcut = nn.Linear(in_dim, out_dim) if in_dim != out_dim else nn.Identity()
        
        self.norm1 = nn.LayerNorm(out_dim * 2) if use_layer_norm else nn.Identity()
        self.norm2 = nn.LayerNorm(out_dim) if use_layer_norm else nn.Identity()
        self.batch_norm = nn.BatchNorm1d(out_dim) if use_batch_norm else nn.Identity()
        
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()
        
    def forward(self, x):
        residual = self.shortcut(x)
        
        x = self.fc1(x)
        x = self.norm1(x)
        x = self.activation(x)
        x = self.dropout(x)
        
        x = self.fc2(x)
        x = self.norm2(x)
        
        x = x + residual
        x = self.activation(x)
        
        if x.dim() == 2 and x.size(0) > 1:
            x = self.batch_norm(x)
        
        return x

class TransformerEncoder(nn.Module):
    def __init__(self, input_dim: int, config: ModelConfig, output_dim: int = 1):
        super().__init__()
        self.config = config
        
        self.input_projection = nn.Sequential(
            nn.Linear(input_dim, config.hidden_dims[0]),
            nn.LayerNorm(config.hidden_dims[0]),
            nn.GELU()
        )
        
        self.attention_layers = nn.ModuleList([
            SelfAttention(config.hidden_dims[0], config.attention_heads)
            for _ in range(2)
        ])
        
        self.residual_blocks = nn.ModuleList()
        for i in range(len(config.hidden_dims) - 1):
            self.residual_blocks.append(
                ResidualBlock(
                    config.hidden_dims[i],
                    config.hidden_dims[i + 1],
                    config.dropout_rates[i],
                    config.use_batch_norm,
                    config.use_layer_norm
                )
            )
        
        self.output_head = nn.Sequential(
            nn.Linear(config.hidden_dims[-1], config.hidden_dims[-1] // 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(config.hidden_dims[-1] // 2, output_dim)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=nn.init.calculate_gain('relu'))
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        x = self.input_projection(x)
        
        if x.dim() == 2:
            x = x.unsqueeze(1)
        
        for attn in self.attention_layers:
            x = x + attn(x)
        
        x = x.squeeze(1) if x.size(1) == 1 else x.mean(dim=1)
        
        for block in self.residual_blocks:
            x = block(x)
        
        return self.output_head(x)

class MixtureOfExperts(nn.Module):
    def __init__(self, input_dim: int, num_experts: int = 4, output_dim: int = 5):
        super().__init__()
        self.num_experts = num_experts
        
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, 256),
                nn.GELU(),
                nn.Dropout(0.2),
                nn.Linear(256, 128),
                nn.GELU(),
                nn.Linear(128, output_dim)
            ) for _ in range(num_experts)
        ])
        
        self.gating = nn.Sequential(
            nn.Linear(input_dim, num_experts),
            nn.Softmax(dim=-1)
        )
    
    def forward(self, x):
        gates = self.gating(x)
        expert_outputs = torch.stack([expert(x) for expert in self.experts], dim=1)
        return torch.sum(gates.unsqueeze(-1) * expert_outputs, dim=1)

class FeatureEngineering:
    def __init__(self):
        self.char_vocab = {}
        self.ngram_vocab = {}
        self.pattern_cache = {}
        self.entropy_cache = {}
        
    @lru_cache(maxsize=10000)
    def extract_advanced_features(self, hostname: str) -> np.ndarray:
        if not hostname:
            return np.zeros(128)
        
        hostname = hostname.lower().strip()
        
        structural_features = self._extract_structural_features(hostname)
        semantic_features = self._extract_semantic_features(hostname)
        statistical_features = self._extract_statistical_features(hostname)
        pattern_features = self._extract_pattern_features(hostname)
        
        return np.concatenate([
            structural_features,
            semantic_features,
            statistical_features,
            pattern_features
        ])[:128]
    
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
            np.std([len(x) for x in hostname.split('.')]) if '.' in hostname and len(hostname.split('.')) > 1 else 0,
        ]
        
        char_distribution = np.zeros(26)
        for char in hostname:
            if 'a' <= char <= 'z':
                char_distribution[ord(char) - ord('a')] += 1
        char_distribution = char_distribution / (sum(char_distribution) + 1e-10)
        
        features.extend(char_distribution.tolist())
        return np.array(features)
    
    def _extract_semantic_features(self, hostname: str) -> np.ndarray:
        semantic_patterns = {
            'infrastructure': ['srv', 'server', 'host', 'node', 'instance'],
            'network': ['fw', 'firewall', 'router', 'switch', 'gateway', 'proxy'],
            'database': ['db', 'database', 'sql', 'mongo', 'redis', 'postgres'],
            'application': ['app', 'api', 'web', 'www', 'service'],
            'security': ['ids', 'ips', 'ndr', 'siem', 'waf', 'scanner'],
            'environment': ['prod', 'production', 'dev', 'test', 'staging', 'uat'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'k8s', 'docker'],
            'location': ['us', 'eu', 'asia', 'east', 'west', 'north', 'south'],
            'datacenter': ['dc', 'datacenter', '1dc', 'fead', 'fiserv'],
            'criticality': ['critical', 'primary', 'backup', 'dr', 'failover']
        }
        
        features = []
        for category, patterns in semantic_patterns.items():
            score = sum([1.0 / (1 + hostname.find(p)) if p in hostname else 0 for p in patterns])
            features.append(score)
        
        ngram_features = self._extract_ngram_features(hostname, n=3)
        features.extend(ngram_features[:20])
        
        return np.array(features[:30])
    
    def _extract_statistical_features(self, hostname: str) -> np.ndarray:
        features = []
        
        numeric_sequences = re.findall(r'\d+', hostname)
        if numeric_sequences:
            numbers = [int(x) for x in numeric_sequences]
            features.extend([
                np.mean(numbers),
                np.std(numbers),
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
                np.std(lengths),
                np.min(lengths),
                np.max(lengths),
                len(alpha_sequences)
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        transition_matrix = self._calculate_transition_matrix(hostname)
        features.extend(transition_matrix.flatten()[:15])
        
        return np.array(features)
    
    def _extract_pattern_features(self, hostname: str) -> np.ndarray:
        features = []
        
        pattern_hash = hashlib.md5(re.sub(r'\d+', 'X', hostname).encode()).hexdigest()
        features.extend([int(pattern_hash[i:i+2], 16) / 255.0 for i in range(0, 16, 2)])
        
        position_encoding = [np.sin(i / 10000 ** (2 * j / 8)) for i in range(len(hostname)) for j in range(4)]
        features.extend(position_encoding[:20])
        
        return np.array(features[:28])
    
    def _calculate_entropy(self, s: str) -> float:
        if s in self.entropy_cache:
            return self.entropy_cache[s]
        
        prob = [float(s.count(c)) / len(s) for c in set(s)]
        entropy = -sum([p * np.log2(p) for p in prob if p > 0])
        self.entropy_cache[s] = entropy
        return entropy
    
    def _extract_ngram_features(self, s: str, n: int = 3) -> List[float]:
        ngrams = [s[i:i+n] for i in range(len(s) - n + 1)]
        ngram_counts = Counter(ngrams)
        return [ngram_counts.get(ng, 0) / len(ngrams) if ngrams else 0 for ng in list(ngram_counts.keys())[:20]]
    
    def _calculate_transition_matrix(self, s: str) -> np.ndarray:
        matrix = np.zeros((5, 5))
        char_types = {'alpha': 0, 'digit': 1, 'dot': 2, 'dash': 3, 'other': 4}
        
        def get_type(c):
            if c.isalpha():
                return 0
            elif c.isdigit():
                return 1
            elif c == '.':
                return 2
            elif c == '-':
                return 3
            else:
                return 4
        
        for i in range(len(s) - 1):
            matrix[get_type(s[i])][get_type(s[i + 1])] += 1
        
        return matrix / (matrix.sum() + 1e-10)

class AO1VisibilityPredictor:
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        self.existence_model = None
        self.visibility_model = None
        self.feature_engineer = FeatureEngineering()
        self.feature_scaler = RobustScaler()
        self.trained = False
        self.db_path = db_path
        self.model_version = "2.0.0"
        self.training_metrics = {}
        self.model_dir = 'models'
        self.batch_size = 32
        
        os.makedirs(self.model_dir, exist_ok=True)
        
    @property
    def models_exist(self) -> bool:
        required_files = [
            f'{self.model_dir}/existence_model.pth',
            f'{self.model_dir}/visibility_model.pth',
            f'{self.model_dir}/feature_scaler.pkl',
            f'{self.model_dir}/feature_engineer.pkl'
        ]
        return all(os.path.exists(f) for f in required_files)
    
    def initialize_models(self):
        if self.models_exist:
            print("Loading existing models...")
            if self.load_models():
                print("Models loaded successfully!")
                return True
            print("Failed to load models, training new ones...")
        
        print("Training new models...")
        self.train_models()
        return self.trained
    
    def get_db_connection(self):
        try:
            return duckdb.connect(self.db_path)
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def get_cmdb_data(self) -> pd.DataFrame:
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
            print(f"Successfully loaded {len(df)} records from universal_cmdb table")
            return df
        except Exception as e:
            print(f"Error fetching CMDB data: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        features, existence_labels, visibility_labels = [], [], []
        
        for _, row in df.iterrows():
            hostname_features = self.feature_engineer.extract_advanced_features(row['host'])
            
            contextual_features = self._extract_contextual_features(row)
            combined_features = np.concatenate([hostname_features, contextual_features])
            
            features.append(combined_features)
            
            existence_score = self._calculate_existence_score(row)
            existence_labels.append(existence_score)
            
            visibility_class = self._calculate_visibility_class(row)
            visibility_labels.append(visibility_class)
        
        return np.array(features), np.array(existence_labels), np.array(visibility_labels)
    
    def _extract_contextual_features(self, row) -> np.ndarray:
        features = []
        
        categorical_mappings = {
            'business_unit': self._encode_categorical(row.get('business_unit', ''), 8),
            'region': self._encode_categorical(row.get('region', ''), 5),
            'infrastructure_type': self._encode_categorical(row.get('infrastructure_type', ''), 4),
            'system_classification': self._encode_categorical(row.get('system_classification', ''), 6)
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
        print("Loading CMDB data...")
        df = self.get_cmdb_data()
        
        if df.empty:
            print("No data available for training!")
            return
        
        print(f"Preparing training data from {len(df)} records...")
        X, existence_y, visibility_y = self.prepare_training_data(df)
        
        if len(X) == 0:
            print("No features extracted!")
            return
        
        X_scaled = self.feature_scaler.fit_transform(X)
        
        config = ModelConfig()
        input_size = X_scaled.shape[1]
        
        self.existence_model = TransformerEncoder(input_size, config, output_dim=1).to(device)
        self.visibility_model = MixtureOfExperts(input_size, num_experts=4, output_dim=5).to(device)
        
        self._train_with_cross_validation(X_scaled, existence_y, visibility_y)
        
        self.trained = True
        print("Training completed!")
    
    def _train_with_cross_validation(self, X: np.ndarray, existence_y: np.ndarray, visibility_y: np.ndarray):
        kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        best_existence_loss = float('inf')
        best_visibility_loss = float('inf')
        
        for fold, (train_idx, val_idx) in enumerate(kfold.split(X, visibility_y)):
            print(f"Training fold {fold + 1}/5...")
            
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
                train_dataset, batch_size=self.batch_size, shuffle=True, pin_memory=False
            )
            
            val_loader = torch.utils.data.DataLoader(
                val_dataset, batch_size=self.batch_size, shuffle=False, pin_memory=False
            )
            
            optimizer1 = optim.AdamW(self.existence_model.parameters(), lr=0.0005, weight_decay=1e-5)
            optimizer2 = optim.AdamW(self.visibility_model.parameters(), lr=0.0005, weight_decay=1e-5)
            
            scheduler1 = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer1, T_0=10, T_mult=2)
            scheduler2 = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer2, T_0=10, T_mult=2)
            
            criterion1 = nn.BCEWithLogitsLoss()
            criterion2 = nn.CrossEntropyLoss(label_smoothing=0.1)
            
            scaler = GradScaler('cpu')
            
            for epoch in range(50):
                self.existence_model.train()
                self.visibility_model.train()
                
                for batch_x, batch_exist_y, batch_vis_y in train_loader:
                    batch_x = batch_x.to(device)
                    batch_exist_y = batch_exist_y.to(device)
                    batch_vis_y = batch_vis_y.to(device)
                    
                    optimizer1.zero_grad(set_to_none=True)
                    with autocast('cpu'):
                        exist_outputs = self.existence_model(batch_x)
                        loss1 = criterion1(exist_outputs, batch_exist_y)
                    
                    loss1.backward()
                    torch.nn.utils.clip_grad_norm_(self.existence_model.parameters(), 1.0)
                    optimizer1.step()
                    
                    optimizer2.zero_grad(set_to_none=True)
                    with autocast('cpu'):
                        vis_outputs = self.visibility_model(batch_x)
                        loss2 = criterion2(vis_outputs, batch_vis_y)
                    
                    loss2.backward()
                    torch.nn.utils.clip_grad_norm_(self.visibility_model.parameters(), 1.0)
                    optimizer2.step()
                    
                    del batch_x, batch_exist_y, batch_vis_y
                    torch.mps.empty_cache() if device.type == 'mps' else None
                
                scheduler1.step()
                scheduler2.step()
                
                if epoch % 10 == 0:
                    val_loss1, val_loss2 = self._validate(val_loader, criterion1, criterion2)
                    print(f"Fold {fold+1}, Epoch {epoch}: Val Loss - {val_loss1:.4f}/{val_loss2:.4f}")
                    
                    if val_loss1 < best_existence_loss:
                        best_existence_loss = val_loss1
                        self.save_models()
                    
                    if val_loss2 < best_visibility_loss:
                        best_visibility_loss = val_loss2
                
                gc.collect()
                torch.mps.empty_cache() if device.type == 'mps' else None
    
    def _validate(self, val_loader, criterion1, criterion2) -> Tuple[float, float]:
        self.existence_model.eval()
        self.visibility_model.eval()
        
        total_loss1, total_loss2 = 0.0, 0.0
        
        with torch.no_grad():
            for batch_x, batch_exist_y, batch_vis_y in val_loader:
                batch_x = batch_x.to(device)
                batch_exist_y = batch_exist_y.to(device)
                batch_vis_y = batch_vis_y.to(device)
                
                exist_outputs = self.existence_model(batch_x)
                vis_outputs = self.visibility_model(batch_x)
                
                total_loss1 += criterion1(exist_outputs, batch_exist_y).item()
                total_loss2 += criterion2(vis_outputs, batch_vis_y).item()
                
                del batch_x, batch_exist_y, batch_vis_y
                torch.mps.empty_cache() if device.type == 'mps' else None
        
        return total_loss1 / len(val_loader), total_loss2 / len(val_loader)
    
    def save_models(self):
        try:
            torch.save(self.existence_model.state_dict(), f'{self.model_dir}/existence_model.pth')
            torch.save(self.visibility_model.state_dict(), f'{self.model_dir}/visibility_model.pth')
            with open(f'{self.model_dir}/feature_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            with open(f'{self.model_dir}/feature_engineer.pkl', 'wb') as f:
                pickle.dump(self.feature_engineer, f)
        except Exception as e:
            print(f"Error saving models: {e}")
    
    def load_models(self) -> bool:
        try:
            if not self.models_exist:
                return False
            
            sample_features = self.feature_engineer.extract_advanced_features("sample-host")
            contextual_features = np.zeros(32)
            input_size = len(np.concatenate([sample_features, contextual_features]))
            
            config = ModelConfig()
            self.existence_model = TransformerEncoder(input_size, config, output_dim=1).to(device)
            self.visibility_model = MixtureOfExperts(input_size, num_experts=4, output_dim=5).to(device)
            
            self.existence_model.load_state_dict(torch.load(f'{self.model_dir}/existence_model.pth', map_location=device))
            self.visibility_model.load_state_dict(torch.load(f'{self.model_dir}/visibility_model.pth', map_location=device))
            
            with open(f'{self.model_dir}/feature_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            with open(f'{self.model_dir}/feature_engineer.pkl', 'rb') as f:
                self.feature_engineer = pickle.load(f)
            
            self.trained = True
            return True
            
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def predict_missing_assets(self, business_unit_filter: Optional[str] = None) -> List[Dict]:
        if not self.trained:
            print("Models not trained yet! Attempting to initialize...")
            self.initialize_models()
            if not self.trained:
                return []
        
        df = self.get_cmdb_data()
        if df.empty:
            return []
        
        if business_unit_filter:
            df = df[df['business_unit'] == business_unit_filter]
        
        hostname_patterns = self._analyze_advanced_patterns(df)
        predicted_assets = []
        existing_hostnames = set(df['host'].values)
        
        self.existence_model.eval()
        self.visibility_model.eval()
        
        with torch.no_grad():
            for pattern in hostname_patterns[:20]:
                candidates = self._generate_candidates(pattern, existing_hostnames)
                
                for candidate in candidates[:50]:
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
                    
                    torch.mps.empty_cache() if device.type == 'mps' else None
        
        return sorted(predicted_assets, key=lambda x: x['existence_probability'] * x['visibility_risk_score'], reverse=True)[:75]
    
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
        
        return sorted(patterns, key=lambda x: x['count'] * x['entropy'], reverse=True)
    
    def _extract_pattern_signature(self, hostname: str) -> str:
        sig = re.sub(r'\d+', 'NUM', hostname.lower())
        sig = re.sub(r'[a-z]{3,}', 'ALPHA', sig)
        return sig
    
    def _reconstruct_pattern(self, signature: str) -> str:
        return signature.replace('NUM', 'XXX').replace('ALPHA', 'name')
    
    def _generate_candidates(self, pattern: Dict, existing: set) -> List[str]:
        candidates = []
        base_pattern = pattern['pattern']
        
        for i in range(1, 100):
            for padding in [2, 3, 4]:
                candidate = base_pattern.replace('XXX', str(i).zfill(padding))
                candidate = candidate.replace('name', self._generate_name_variant())
                
                if candidate not in existing:
                    candidates.append(candidate)
        
        return candidates
    
    def _generate_name_variant(self) -> str:
        variants = ['srv', 'app', 'db', 'web', 'api', 'node', 'host']
        return np.random.choice(variants)
    
    def _prepare_prediction_features(self, hostname: str, business_unit: Optional[str]) -> np.ndarray:
        hostname_features = self.feature_engineer.extract_advanced_features(hostname)
        
        contextual_features = np.zeros(32)
        if business_unit:
            contextual_features[:8] = self._encode_categorical(business_unit, 8)
        contextual_features[8:13] = [0.7, 1.6, 0.8, 0.5, 0.9]
        
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
            'Database Server': ['db', 'sql', 'mongo', 'redis', 'postgres', 'oracle'],
            'Web Server': ['web', 'www', 'nginx', 'apache', 'iis'],
            'Application Server': ['app', 'api', 'service', 'backend'],
            'Security Infrastructure': ['fw', 'firewall', 'ids', 'ips', 'waf', 'ndr'],
            'Network Infrastructure': ['router', 'switch', 'gateway', 'proxy'],
            'Compute Node': ['node', 'compute', 'worker', 'executor'],
            'Storage System': ['storage', 'nas', 'san', 'backup'],
            'Container Host': ['k8s', 'docker', 'container', 'pod']
        }
        
        for role, patterns in role_patterns.items():
            score = sum([2.0 / (1 + hostname_lower.find(p)) if p in hostname_lower else 0 for p in patterns])
            role_scores[role] = score
        
        return max(role_scores, key=role_scores.get) if max(role_scores.values()) > 0 else 'General Server'
    
    def _predict_advanced_log_types(self, hostname: str) -> List[str]:
        role = self._classify_advanced_role(hostname)
        
        log_mapping = {
            'Database Server': ['Database Audit', 'Query Logs', 'Transaction Logs', 'Replication Logs'],
            'Web Server': ['Access Logs', 'Error Logs', 'SSL/TLS Logs', 'Request Logs'],
            'Application Server': ['Application Logs', 'Performance Metrics', 'Error Traces', 'API Logs'],
            'Security Infrastructure': ['Security Events', 'Threat Intelligence', 'Flow Logs', 'Alert Logs'],
            'Network Infrastructure': ['Network Flow', 'SNMP Traps', 'Routing Logs', 'Interface Stats'],
            'Container Host': ['Container Logs', 'Orchestration Events', 'Resource Metrics', 'Pod Logs'],
            'Storage System': ['Storage Events', 'Capacity Metrics', 'I/O Performance', 'Backup Logs']
        }
        
        return log_mapping.get(role, ['System Logs', 'Security Events', 'Performance Metrics'])
    
    def _calculate_advanced_risk(self, hostname: str, exist_prob: float, vis_probs: np.ndarray) -> float:
        hostname_lower = hostname.lower()
        
        risk_weights = {
            'production': 0.9,
            'database': 0.85,
            'security': 0.8,
            'critical': 0.95,
            'public': 0.75
        }
        
        base_risk = sum([weight for keyword, weight in risk_weights.items() if keyword in hostname_lower])
        
        visibility_gap = vis_probs[0]
        uncertainty = -sum([p * np.log(p + 1e-10) for p in vis_probs])
        
        combined_risk = (base_risk * 0.4 + exist_prob * 0.3 + visibility_gap * 0.2 + uncertainty * 0.1)
        
        return min(combined_risk, 1.0)
    
    def _calculate_confidence_interval(self, exist_prob: float, vis_probs: np.ndarray) -> Tuple[float, float]:
        std_dev = np.std(vis_probs) * 0.1
        lower = max(0, exist_prob - 1.96 * std_dev)
        upper = min(1, exist_prob + 1.96 * std_dev)
        return (float(lower), float(upper))

app = Flask(__name__)
ao1_predictor = AO1VisibilityPredictor()

@app.route('/api/train-visibility-model')
def train_visibility_model():
    try:
        threading.Thread(target=ao1_predictor.train_models, daemon=True).start()
        return jsonify({
            'status': 'training_started',
            'message': 'Advanced AO1 visibility model training initiated',
            'device': str(device),
            'model_version': ao1_predictor.model_version
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility')
def predict_missing_visibility():
    try:
        if not ao1_predictor.trained:
            return jsonify({
                'error': 'Models not trained yet',
                'message': 'Please train the models first using /api/train-visibility-model'
            }), 503
            
        predictions = ao1_predictor.predict_missing_assets()
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility/<business_unit>')
def predict_missing_visibility_bu(business_unit):
    try:
        if not ao1_predictor.trained:
            return jsonify({
                'error': 'Models not trained yet',
                'message': 'Please train the models first using /api/train-visibility-model'
            }), 503
            
        predictions = ao1_predictor.predict_missing_assets(business_unit)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/visibility-model-status')
def visibility_model_status():
    return jsonify({
        'trained': ao1_predictor.trained,
        'device': str(device),
        'model_version': ao1_predictor.model_version,
        'training_metrics': ao1_predictor.training_metrics,
        'architecture': 'Transformer + MoE',
        'feature_dimensions': 160,
        'last_training': datetime.now().isoformat() if ao1_predictor.trained else None
    })

@app.route('/api/visibility-gap-analysis')
def visibility_gap_analysis():
    try:
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
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-models')
def load_models():
    try:
        success = ao1_predictor.load_models()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Models loaded successfully' if success else 'Failed to load models',
            'architecture': 'Transformer + MoE' if success else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Initializing Advanced AO1 Visibility Predictor...")
    print(f"Architecture: Transformer Encoder + Mixture of Experts")
    print(f"Device: {device}")
    
    ao1_predictor.initialize_models()
    
    if not ao1_predictor.trained:
        print("WARNING: AI models not ready. Training required.")
    else:
        print("AI models ready! Advanced inference available.")
    
    app.run(debug=True, port=5001, host='0.0.0.0')