import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
import hashlib
import re
import os
import ssl
import certifi
import warnings
import logging
import pickle
import json
from dataclasses import dataclass
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, Counter
from scipy import spatial, stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD, PCA, FastICA
from sklearn.manifold import TSNE
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import annoy
import hnswlib

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

os.environ['TOKENIZERS_PARALLELISM'] = 'false'
ssl._create_default_https_context = ssl._create_unverified_context

TRANSFORMER_BACKEND = None
transformer_model = None
tokenizer = None

class QuantumAttentionMechanism(nn.Module):
    def __init__(self, dim, num_heads=16, qkv_bias=False, attn_drop=0.1, proj_drop=0.1):
        super().__init__()
        self.num_heads = num_heads
        self.scale = (dim // num_heads) ** -0.5
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)
        self.norm = nn.LayerNorm(dim)
        
    def forward(self, x):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)
        
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)
        
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return self.norm(x)

class TransformerEncoderBlock(nn.Module):
    def __init__(self, dim, num_heads, mlp_ratio=4.0, drop=0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = QuantumAttentionMechanism(dim, num_heads=num_heads, attn_drop=drop, proj_drop=drop)
        self.norm2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, int(dim * mlp_ratio)),
            nn.GELU(),
            nn.Dropout(drop),
            nn.Linear(int(dim * mlp_ratio), dim),
            nn.Dropout(drop)
        )
        
    def forward(self, x):
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x

class QuantumNeuralNetwork(nn.Module):
    def __init__(self, input_dim=None, hidden_dims=[1024, 512, 256, 128], num_classes=17, num_heads=16, num_layers=4):
        super().__init__()
        
        if input_dim is None:
            input_dim = 768
        
        self.input_dim = input_dim
        self.input_projection = nn.Linear(input_dim, hidden_dims[0])
        
        self.transformer_blocks = nn.ModuleList([
            TransformerEncoderBlock(hidden_dims[0], num_heads=num_heads, drop=0.1)
            for _ in range(num_layers)
        ])
        
        self.encoder = nn.ModuleList()
        for i in range(len(hidden_dims)-1):
            self.encoder.append(nn.Linear(hidden_dims[i], hidden_dims[i+1]))
            self.encoder.append(nn.LayerNorm(hidden_dims[i+1]))
            self.encoder.append(nn.Dropout(0.1))
            self.encoder.append(nn.GELU())
        
        self.attention = nn.MultiheadAttention(hidden_dims[-1], num_heads=8, batch_first=True)
        
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dims[-1], hidden_dims[-1] * 2),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dims[-1] * 2, num_classes)
        )
        
        self.confidence = nn.Sequential(
            nn.Linear(hidden_dims[-1], hidden_dims[-1] // 2),
            nn.GELU(),
            nn.Linear(hidden_dims[-1] // 2, 1),
            nn.Sigmoid()
        )
        
        self.apply(self._init_weights)
        
    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.xavier_uniform_(m.weight)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.LayerNorm):
            nn.init.ones_(m.weight)
            nn.init.zeros_(m.bias)
        
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        x = self.input_projection(x)
        
        for block in self.transformer_blocks:
            x = block(x)
        
        for layer in self.encoder:
            if isinstance(layer, nn.Linear):
                x = layer(x)
            elif isinstance(layer, (nn.LayerNorm, nn.Dropout, nn.GELU)):
                x = layer(x)
        
        attn_output, attn_weights = self.attention(x, x, x)
        x = x + attn_output
        
        if len(x.shape) == 3:
            x = x.mean(dim=1)
        
        logits = self.classifier(x)
        conf = self.confidence(x)
        
        return logits, conf

class HybridEmbeddingModel:
    def __init__(self, dim=768):
        self.dim = dim
        self.tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 3), analyzer='char_wb')
        self.svd = TruncatedSVD(n_components=min(384, dim))
        self.pca = PCA(n_components=min(256, dim))
        self.ica = FastICA(n_components=min(128, dim))
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.embedding_cache = {}
        self.semantic_index = None
        self.build_semantic_space()
        
    def build_semantic_space(self):
        vocab_groups = {
            'infrastructure': ['server', 'hostname', 'host', 'machine', 'computer', 'system', 'node', 'instance', 'vm', 'container'],
            'network': ['network', 'ip', 'address', 'subnet', 'vlan', 'vpc', 'firewall', 'router', 'switch', 'gateway'],
            'security': ['security', 'vulnerability', 'threat', 'risk', 'attack', 'breach', 'malware', 'encryption', 'authentication'],
            'cloud': ['cloud', 'aws', 'azure', 'gcp', 'lambda', 's3', 'ec2', 'kubernetes', 'docker', 'serverless'],
            'database': ['database', 'sql', 'mysql', 'postgres', 'mongodb', 'redis', 'elasticsearch', 'query', 'index'],
            'monitoring': ['monitoring', 'logging', 'metrics', 'alert', 'splunk', 'datadog', 'prometheus', 'grafana'],
            'identity': ['identity', 'user', 'account', 'role', 'permission', 'ldap', 'oauth', 'saml', 'sso'],
            'compliance': ['compliance', 'audit', 'policy', 'regulation', 'gdpr', 'hipaa', 'pci', 'sox']
        }
        
        self.semantic_vectors = {}
        for group, terms in vocab_groups.items():
            group_vec = np.random.randn(self.dim) * 0.1
            for i, term in enumerate(terms):
                term_vec = group_vec + np.random.randn(self.dim) * 0.05
                term_vec[i % self.dim] += 0.2
                self.semantic_vectors[term] = term_vec / np.linalg.norm(term_vec)
        
        if len(self.semantic_vectors) > 0:
            vectors = np.array(list(self.semantic_vectors.values())).astype('float32')
            self.semantic_index = faiss.IndexFlatL2(self.dim)
            self.semantic_index.add(vectors)
    
    def encode(self, texts, convert_to_tensor=False):
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        for text in texts:
            if text in self.embedding_cache:
                embeddings.append(self.embedding_cache[text])
                continue
            
            text_lower = text.lower()
            base_embedding = np.zeros(self.dim)
            
            if not self.is_fitted:
                dummy_texts = ['infrastructure network security', 'database monitoring compliance', 'cloud identity authentication']
                self.tfidf.fit(dummy_texts)
                self.is_fitted = True
            
            try:
                tfidf_features = self.tfidf.transform([text]).toarray()
                svd_features = self.svd.fit_transform(tfidf_features)
                base_embedding[:svd_features.shape[1]] = svd_features[0]
            except:
                pass
            
            semantic_boost = np.zeros(self.dim)
            for term, vec in self.semantic_vectors.items():
                if term in text_lower:
                    semantic_boost += vec * 0.3
            
            char_hash = hashlib.sha256(text.encode()).digest()
            hash_features = np.frombuffer(char_hash, dtype=np.uint8)[:self.dim]
            hash_embedding = np.zeros(self.dim)
            hash_embedding[:len(hash_features)] = hash_features / 255.0
            
            combined = base_embedding * 0.4 + semantic_boost * 0.4 + hash_embedding * 0.2
            combined = combined / (np.linalg.norm(combined) + 1e-8)
            
            self.embedding_cache[text] = combined
            embeddings.append(combined)
        
        embeddings = np.array(embeddings).astype('float32')
        
        if convert_to_tensor:
            return torch.FloatTensor(embeddings)
        return embeddings

class NeuralSemanticEncoder:
    def __init__(self):
        self.models = []
        self.weights = []
        self.init_ensemble()
        
    def init_ensemble(self):
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            self.models.append(model)
            self.weights.append(1.0)
        except:
            pass
        
        try:
            from transformers import AutoModel, AutoTokenizer
            model_name = 'bert-base-uncased'
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            self.models.append((model, tokenizer))
            self.weights.append(0.8)
        except:
            pass
        
        hybrid = HybridEmbeddingModel()
        self.models.append(hybrid)
        self.weights.append(0.5 if len(self.models) > 1 else 1.0)
        
        self.weights = np.array(self.weights) / sum(self.weights)
    
    def encode(self, texts, convert_to_tensor=False):
        all_embeddings = []
        
        for model, weight in zip(self.models, self.weights):
            try:
                if isinstance(model, tuple):
                    model_obj, tokenizer = model
                    inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True)
                    with torch.no_grad():
                        outputs = model_obj(**inputs)
                        embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
                elif hasattr(model, 'encode'):
                    embeddings = model.encode(texts, convert_to_tensor=False)
                else:
                    continue
                
                all_embeddings.append(embeddings * weight)
            except:
                continue
        
        if not all_embeddings:
            hybrid = HybridEmbeddingModel()
            return hybrid.encode(texts, convert_to_tensor)
        
        combined = np.sum(all_embeddings, axis=0)
        
        if convert_to_tensor:
            return torch.FloatTensor(combined)
        return combined

def initialize_transformer():
    global TRANSFORMER_BACKEND, tokenizer, transformer_model
    
    encoders = [
        ('neural_semantic', NeuralSemanticEncoder),
        ('hybrid', lambda: HybridEmbeddingModel(768))
    ]
    
    for backend_name, encoder_class in encoders:
        try:
            transformer_model = encoder_class()
            TRANSFORMER_BACKEND = backend_name
            logger.info(f"Initialized {backend_name} encoder")
            return True
        except Exception as e:
            logger.debug(f"Failed to initialize {backend_name}: {e}")
    
    transformer_model = HybridEmbeddingModel(768)
    TRANSFORMER_BACKEND = 'hybrid_fallback'
    return True

initialize_transformer()

class HyperIntelligence:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.transformer = transformer_model
        self.tokenizer = tokenizer
        
        try:
            test_embedding = self.encode_text('test')
            actual_dim = test_embedding.shape[-1]
        except:
            actual_dim = 768
        
        self.neural_net = QuantumNeuralNetwork(input_dim=actual_dim).to(self.device)
        self.ensemble_classifiers = self._init_ensemble_classifiers()
        
        logger.info(f"HyperIntelligence initialized with backend: {TRANSFORMER_BACKEND}, dim: {actual_dim}")
        
        self.field_mappings = {
            'hostname': ['hostname', 'host_name', 'computer_name', 'device_name', 'machine_name', 'system_name', 'server_name'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'platform_type', 'cloud', 'onprem', 'saas'],
            'region': ['region', 'global_region', 'geo_region', 'geographic_region', 'location_region'],
            'country': ['country', 'nation', 'country_code', 'country_name'],
            'business_unit': ['business_unit', 'bu', 'department', 'division', 'org_unit'],
            'datacenter': ['datacenter', 'data_center', 'dc', 'site', 'facility'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region'],
            'cio': ['cio', 'cio_org', 'it_org', 'technology_org'],
            'apm': ['apm', 'application_monitoring', 'app_performance'],
            'application_class': ['application_class', 'app_class', 'app_type'],
            'system_classification': ['system_class', 'os_type', 'platform', 'operating_system'],
            'domain': ['domain', 'dns_domain', 'ad_domain', 'active_directory'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'ipv6', 'ip_addr'],
            'mac_address': ['mac_address', 'mac', 'physical_address']
        }
        
        self.log_type_patterns = {
            'network': {
                'patterns': ['firewall', 'ids', 'ips', 'ndr', 'proxy', 'dns', 'waf', 'traffic'],
                'fields': ['source_ip', 'dest_ip', 'protocol', 'port'],
                'visibility': ['url_fqdn_coverage', 'cmdb_visibility', 'network_zones']
            },
            'endpoint': {
                'patterns': ['os_logs', 'edr', 'dlp', 'fim', 'winEvt', 'syslog'],
                'fields': ['system_name', 'ip', 'filename'],
                'visibility': ['cmdb_visibility', 'crowdstrike_coverage']
            },
            'cloud': {
                'patterns': ['cloud_event', 'cloud_config', 'theom', 'wiz'],
                'fields': [],
                'visibility': ['vpc', 'ipam_public_ip']
            },
            'application': {
                'patterns': ['web_logs', 'api_gateway', 'http_access'],
                'fields': ['authentication_attempts', 'privilege_escalation'],
                'visibility': ['url_fqdn_coverage', 'control_coverage']
            },
            'identity': {
                'patterns': ['authentication', 'privilege', 'identity', 'access'],
                'fields': ['authentication_attempts', 'identity_operations'],
                'visibility': ['domain', 'internal', 'external']
            }
        }
        
        self.pattern_cache = {}
        self.classification_cache = {}
        
    def _init_ensemble_classifiers(self):
        classifiers = []
        try:
            rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            classifiers.append(rf)
        except:
            pass
        
        try:
            gb = GradientBoostingClassifier(n_estimators=50, max_depth=5, random_state=42)
            classifiers.append(gb)
        except:
            pass
        
        try:
            mlp = MLPClassifier(hidden_layer_sizes=(256, 128), max_iter=100, random_state=42)
            classifiers.append(mlp)
        except:
            pass
        
        return classifiers
    
    @lru_cache(maxsize=1024)
    def encode_text(self, text: str) -> torch.Tensor:
        try:
            embeddings = self.transformer.encode(text, convert_to_tensor=True)
            if len(embeddings.shape) == 1:
                embeddings = embeddings.unsqueeze(0)
            
            if embeddings.shape[-1] != self.neural_net.input_dim:
                current_dim = embeddings.shape[-1]
                target_dim = self.neural_net.input_dim
                
                if current_dim < target_dim:
                    padding = torch.zeros(embeddings.shape[0], target_dim - current_dim).to(self.device)
                    embeddings = torch.cat([embeddings, padding], dim=-1)
                else:
                    embeddings = embeddings[:, :target_dim]
            
            return embeddings.to(self.device)
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return torch.randn(1, self.neural_net.input_dim).to(self.device)
    
    def classify_column(self, column_name: str, sample_values: List[str]) -> Tuple[str, float, Dict[str, Any]]:
        cache_key = f"{column_name}_{str(sample_values[:5])}"
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]
        
        text = f"{column_name} {' '.join(sample_values[:10])}"
        
        try:
            embeddings = self.encode_text(text)
            
            with torch.no_grad():
                logits, confidence = self.neural_net(embeddings)
                probs = F.softmax(logits, dim=-1)
                max_prob, pred_idx = torch.max(probs, dim=-1)
            
            field_types = list(self.field_mappings.keys()) + ['unknown']
            predicted_type = field_types[pred_idx.item() % len(field_types)]
            
            pattern_score = self._calculate_pattern_score(column_name, sample_values, predicted_type)
            semantic_score = self._calculate_semantic_score(text, predicted_type)
            statistical_score = self._calculate_statistical_score(sample_values, predicted_type)
            
            ensemble_pred, ensemble_conf = self._ensemble_predict(column_name, sample_values)
            
            final_confidence = (
                max_prob.item() * 0.3 + 
                pattern_score * 0.2 + 
                semantic_score * 0.2 + 
                statistical_score * 0.15 + 
                ensemble_conf * 0.15
            )
            
            if ensemble_conf > final_confidence:
                predicted_type = ensemble_pred
                final_confidence = ensemble_conf
            
            metadata = {
                'ml_confidence': max_prob.item(),
                'pattern_score': pattern_score,
                'semantic_score': semantic_score,
                'statistical_score': statistical_score,
                'ensemble_confidence': ensemble_conf,
                'neural_confidence': confidence.item(),
                'method': f'quantum_neural_{TRANSFORMER_BACKEND}'
            }
            
            result = (predicted_type, final_confidence, metadata)
            self.classification_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.warning(f"Neural classification failed: {e}")
            return self._pattern_based_classification(column_name, sample_values)
    
    def _ensemble_predict(self, column_name: str, sample_values: List[str]) -> Tuple[str, float]:
        if not self.ensemble_classifiers or not sample_values:
            return 'unknown', 0.0
        
        try:
            features = self._extract_features(column_name, sample_values)
            predictions = []
            confidences = []
            
            for clf in self.ensemble_classifiers:
                if hasattr(clf, 'predict') and hasattr(clf, 'classes_'):
                    pred = clf.predict([features])[0]
                    predictions.append(pred)
                    if hasattr(clf, 'predict_proba'):
                        conf = clf.predict_proba([features]).max()
                        confidences.append(conf)
            
            if predictions:
                most_common = Counter(predictions).most_common(1)[0]
                return most_common[0], np.mean(confidences) if confidences else 0.5
        except:
            pass
        
        return 'unknown', 0.0
    
    def _extract_features(self, column_name: str, sample_values: List[str]) -> np.ndarray:
        features = []
        
        features.append(len(column_name))
        features.append(column_name.count('_'))
        features.append(1 if 'id' in column_name.lower() else 0)
        features.append(1 if 'name' in column_name.lower() else 0)
        features.append(1 if 'type' in column_name.lower() else 0)
        
        if sample_values:
            lengths = [len(str(v)) for v in sample_values]
            features.extend([np.mean(lengths), np.std(lengths), np.min(lengths), np.max(lengths)])
            
            numeric_count = sum(1 for v in sample_values if str(v).replace('.', '').isdigit())
            features.append(numeric_count / len(sample_values))
            
            unique_ratio = len(set(sample_values)) / len(sample_values)
            features.append(unique_ratio)
        else:
            features.extend([0] * 6)
        
        return np.array(features)
    
    def _calculate_pattern_score(self, column_name: str, samples: List[str], field_type: str) -> float:
        if field_type not in self.field_mappings:
            return 0.0
        
        patterns = self.field_mappings[field_type]
        column_lower = column_name.lower()
        
        name_score = max([1.0 if p in column_lower else 0.0 for p in patterns], default=0.0)
        
        content_score = 0.5
        if field_type == 'hostname' and samples:
            hostname_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]{1,253}[a-zA-Z0-9]$'
            valid = sum(1 for s in samples if re.match(hostname_pattern, str(s)))
            content_score = valid / len(samples)
        elif field_type == 'ip_address' and samples:
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            valid = sum(1 for s in samples if re.match(ip_pattern, str(s)))
            content_score = valid / len(samples)
        elif field_type == 'mac_address' and samples:
            mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'
            valid = sum(1 for s in samples if re.match(mac_pattern, str(s)))
            content_score = valid / len(samples)
        
        return name_score * 0.6 + content_score * 0.4
    
    def _calculate_semantic_score(self, text: str, field_type: str) -> float:
        text_lower = text.lower()
        
        semantic_groups = {
            'infrastructure_type': ['cloud', 'aws', 'azure', 'gcp', 'onprem', 'saas', 'virtual', 'physical'],
            'system_classification': ['windows', 'linux', 'unix', 'mainframe', 'server', 'database', 'network'],
            'region': ['north', 'south', 'east', 'west', 'europe', 'asia', 'america', 'pacific']
        }
        
        if field_type in semantic_groups:
            keywords = semantic_groups[field_type]
            matches = sum(1 for kw in keywords if kw in text_lower)
            return min(1.0, matches / max(1, len(keywords) * 0.3))
        
        return 0.5
    
    def _calculate_statistical_score(self, sample_values: List[str], field_type: str) -> float:
        if not sample_values:
            return 0.0
        
        try:
            lengths = [len(str(v)) for v in sample_values]
            
            expected_patterns = {
                'hostname': (5, 30, 0.8),
                'ip_address': (7, 15, 0.9),
                'mac_address': (17, 17, 1.0),
                'region': (2, 20, 0.7),
                'country': (2, 50, 0.7)
            }
            
            if field_type in expected_patterns:
                min_len, max_len, uniformity = expected_patterns[field_type]
                
                mean_len = np.mean(lengths)
                if min_len <= mean_len <= max_len:
                    length_score = 1.0
                else:
                    length_score = max(0, 1 - abs(mean_len - (min_len + max_len) / 2) / max_len)
                
                cv = np.std(lengths) / (np.mean(lengths) + 1e-8)
                uniformity_score = 1 - min(1, cv)
                
                return length_score * 0.5 + uniformity_score * 0.5
            
        except:
            pass
        
        return 0.5
    
    def _pattern_based_classification(self, column_name: str, sample_values: List[str]) -> Tuple[str, float, Dict[str, Any]]:
        column_lower = column_name.lower()
        best_match = ('unknown', 0.0)
        
        for field_type, patterns in self.field_mappings.items():
            score = 0.0
            
            for pattern in patterns:
                if pattern in column_lower:
                    score = 1.0
                    break
            
            if score < 1.0 and sample_values:
                if field_type == 'hostname':
                    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]{1,253}[a-zA-Z0-9]$'
                    valid = sum(1 for s in sample_values if re.match(pattern, str(s)))
                    if valid > len(sample_values) * 0.5:
                        score = 0.8
                elif field_type == 'ip_address':
                    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                    valid = sum(1 for s in sample_values if re.match(pattern, str(s)))
                    if valid > len(sample_values) * 0.5:
                        score = 0.9
            
            if score > best_match[1]:
                best_match = (field_type, score)
        
        return best_match[0], best_match[1], {'method': 'pattern_matching', 'pattern_score': best_match[1]}
    
    def identify_log_type(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        table_lower = table_name.lower()
        columns_lower = [c.lower() for c in columns]
        all_text = f"{table_lower} {' '.join(columns_lower)}"
        
        scores = {}
        for log_role, config in self.log_type_patterns.items():
            pattern_score = sum(1 for p in config['patterns'] if p in all_text) / len(config['patterns'])
            field_score = sum(1 for f in config['fields'] if any(f in c for c in columns_lower)) / max(len(config['fields']), 1)
            scores[log_role] = pattern_score * 0.6 + field_score * 0.4
        
        best_role = max(scores, key=scores.get)
        confidence = scores[best_role]
        
        return {
            'role': best_role,
            'confidence': confidence,
            'log_types': self.log_type_patterns[best_role]['patterns'],
            'visibility_factors': self.log_type_patterns[best_role]['visibility'],
            'scores': scores
        }
    
    def classify_infrastructure(self, text: str) -> str:
        text_lower = text.lower()
        infra_keywords = {
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'ec2', 'lambda', 's3'],
            'on_premise': ['onprem', 'datacenter', 'physical', 'bare_metal'],
            'saas': ['saas', 'software_as_service', 'hosted'],
            'api': ['api', 'endpoint', 'rest', 'graphql']
        }
        
        for infra_type, keywords in infra_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return infra_type
        
        return 'on_premise'
    
    def classify_system(self, text: str) -> str:
        text_lower = text.lower()
        sys_keywords = {
            'web_server': ['web', 'apache', 'nginx', 'iis', 'http'],
            'windows_server': ['windows', 'win', 'server2019', 'server2016'],
            'linux_server': ['linux', 'ubuntu', 'centos', 'rhel', 'debian'],
            'database': ['database', 'sql', 'oracle', 'postgres', 'mysql'],
            'network_appliance': ['firewall', 'router', 'switch', 'proxy']
        }
        
        for sys_class, keywords in sys_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return sys_class
        
        return 'unknown'
    
    def map_region(self, text: str) -> str:
        text_lower = text.lower()
        regions = {
            'na': ['north_america', 'usa', 'canada', 'us-east', 'us-west'],
            'europe': ['europe', 'eu', 'uk', 'germany', 'france'],
            'apac': ['asia', 'pacific', 'japan', 'china', 'india'],
            'latam': ['latin', 'brazil', 'mexico', 'argentina']
        }
        
        for region, keywords in regions.items():
            if any(kw in text_lower for kw in keywords):
                return region
        
        return 'unknown'
    
    def calculate_anomaly_score(self, values: List[Any]) -> float:
        if not values:
            return 0.0
        
        str_values = [str(v) for v in values]
        unique_ratio = len(set(str_values)) / len(str_values)
        
        lengths = [len(v) for v in str_values]
        if lengths:
            cv = np.std(lengths) / (np.mean(lengths) + 1e-8)
        else:
            cv = 0
        
        entropy = stats.entropy(Counter(str_values).values()) if len(set(str_values)) > 1 else 0
        
        return (1 - unique_ratio) * 0.3 + min(cv, 1.0) * 0.3 + min(entropy / 10, 1.0) * 0.4