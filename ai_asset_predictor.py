#!/usr/bin/env python3

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import re
import duckdb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.cluster import DBSCAN
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime
import os
import pickle
import gc
import json
import networkx as nx
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

class LSTMPredictor(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_size * 2, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        lstm_out, _ = self.lstm(x)
        return self.sigmoid(self.fc(lstm_out[:, -1, :]))

class TransformerPredictor(nn.Module):
    def __init__(self, input_size, d_model=256, nhead=8):
        super().__init__()
        self.embedding = nn.Linear(input_size, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=4)
        self.fc = nn.Linear(d_model, 1)
        
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        x = self.embedding(x)
        x = self.transformer(x)
        return torch.sigmoid(self.fc(x.mean(dim=1)))

class Autoencoder(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 32)
        )
        self.decoder = nn.Sequential(
            nn.Linear(32, 128),
            nn.ReLU(),
            nn.Linear(128, input_size)
        )
        
    def forward(self, x):
        return self.decoder(self.encoder(x))
    
    def get_error(self, x):
        recon = self.forward(x)
        return ((recon - x) ** 2).mean(dim=1)

class ComprehensiveAssetDiscovery:
    def __init__(self):
        self.models = {
            'lstm': None,
            'transformer': None,
            'autoencoder': None,
            'isolation_forest': None,
            'lof': None,
            'ocsvm': None
        }
        self.scaler = StandardScaler()
        self.graph = nx.Graph()
        self.patterns = []
        
    def extract_features(self, hostname):
        if not hostname:
            return np.zeros(100)
        
        h = hostname.lower()
        features = [
            len(h),
            h.count('.'), h.count('-'), h.count('_'),
            len(re.findall(r'\d', h)),
            len(re.findall(r'[a-z]', h)),
            1 if h[0].isdigit() else 0,
            1 if h[-1].isdigit() else 0,
            self._entropy(h),
            self._ngram_score(h, 2),
            self._ngram_score(h, 3)
        ]
        
        keywords = ['srv', 'web', 'db', 'app', 'prod', 'dev', 'test', 'stage',
                   'fw', 'lb', 'cache', 'queue', 'api', 'dns', 'mail', 'backup',
                   'vm', 'docker', 'k8s', 'aws', 'azure', 'gcp', 'cloud',
                   '1dc', '2dc', 'fead', 'fiserv', 'north', 'south', 'east', 'west']
        
        for kw in keywords:
            features.append(1 if kw in h else 0)
        
        tokens = re.split(r'[-._]', h)
        features.append(len(tokens))
        features.append(max([len(t) for t in tokens]) if tokens else 0)
        features.append(np.mean([len(t) for t in tokens]) if tokens else 0)
        
        while len(features) < 100:
            features.append(0)
            
        return np.array(features[:100])
    
    def _entropy(self, s):
        counts = Counter(s)
        probs = [c/len(s) for c in counts.values()]
        return -sum(p * np.log2(p) for p in probs if p > 0)
    
    def _ngram_score(self, s, n):
        if len(s) < n:
            return 0
        ngrams = [s[i:i+n] for i in range(len(s)-n+1)]
        return len(set(ngrams)) / len(ngrams) if ngrams else 0
    
    def discover_patterns(self, hostnames):
        patterns = self._sequential_patterns(hostnames)
        patterns.extend(self._prefix_span(hostnames))
        patterns.extend(self._spade_patterns(hostnames))
        return patterns
    
    def _sequential_patterns(self, hostnames):
        groups = defaultdict(list)
        
        for h in hostnames:
            h = h.lower()
            if re.search(r'\d', h):
                template = re.sub(r'\d+', 'XXX', h)
                numbers = [int(m.group()) for m in re.finditer(r'\d+', h)]
                groups[template].append({'hostname': h, 'numbers': numbers})
        
        patterns = []
        for template, hosts in groups.items():
            if len(hosts) >= 2:
                all_numbers = defaultdict(list)
                for h in hosts:
                    for i, num in enumerate(h['numbers']):
                        all_numbers[i].append(num)
                
                missing = {}
                for pos, nums in all_numbers.items():
                    nums = sorted(set(nums))
                    if len(nums) > 1:
                        gaps = []
                        for i in range(min(nums), max(nums)+1):
                            if i not in nums:
                                gaps.append(i)
                        missing[pos] = gaps[:1000]
                
                if missing:
                    patterns.append({
                        'template': template,
                        'count': len(hosts),
                        'missing': missing,
                        'samples': [h['hostname'] for h in hosts[:5]]
                    })
        
        return patterns
    
    def _prefix_span(self, hostnames):
        sequences = []
        for h in hostnames:
            tokens = re.split(r'[-._]', h.lower())
            sequences.append(tokens)
        
        pattern_counts = Counter()
        for seq in sequences:
            for length in range(1, min(len(seq)+1, 4)):
                for i in range(len(seq)-length+1):
                    pattern = tuple(seq[i:i+length])
                    pattern_counts[pattern] += 1
        
        patterns = []
        for pattern, count in pattern_counts.items():
            if count >= 3 and not all(p.isdigit() for p in pattern):
                patterns.append({
                    'type': 'prefix',
                    'pattern': pattern,
                    'count': count
                })
        
        return patterns[:100]
    
    def _spade_patterns(self, hostnames):
        vertical_db = defaultdict(list)
        
        for idx, h in enumerate(hostnames):
            tokens = re.split(r'[-._]', h.lower())
            for pos, token in enumerate(tokens):
                vertical_db[token].append((idx, pos))
        
        patterns = []
        for token, occurrences in vertical_db.items():
            if len(occurrences) >= 5 and not token.isdigit():
                patterns.append({
                    'type': 'spade',
                    'token': token,
                    'count': len(occurrences)
                })
        
        return patterns[:50]
    
    def train_models(self, df):
        print("\nTraining comprehensive models...")
        
        X = []
        y_existence = []
        y_visibility = []
        
        for _, row in df.iterrows():
            features = self.extract_features(row.get('host', ''))
            X.append(features)
            
            existence = 0
            if row.get('logging_in_splunk') == 'yes':
                existence += 0.4
            if row.get('present_in_cmdb') == 'yes':
                existence += 0.4
            if row.get('edr_coverage') and row.get('edr_coverage') != 'none':
                existence += 0.2
            y_existence.append(min(existence, 1.0))
            
            visibility = 0
            if row.get('logging_in_splunk') == 'yes' and row.get('logging_in_gso') == 'yes':
                visibility = 4
            elif row.get('logging_in_splunk') == 'yes':
                visibility = 3
            elif row.get('logging_in_gso') == 'yes':
                visibility = 2
            elif row.get('present_in_cmdb') == 'yes':
                visibility = 1
            y_visibility.append(visibility)
        
        X = np.array(X)
        y_existence = np.array(y_existence)
        
        X_train, X_val, y_train, y_val = train_test_split(X, y_existence, test_size=0.2)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        print(f"Training on {len(X_train)} samples...")
        
        self.models['lstm'] = LSTMPredictor(100).to(device)
        self.models['transformer'] = TransformerPredictor(100).to(device)
        self.models['autoencoder'] = Autoencoder(100).to(device)
        
        for name, model in [('lstm', self.models['lstm']), 
                           ('transformer', self.models['transformer'])]:
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.BCELoss()
            
            print(f"Training {name}...")
            for epoch in range(20):
                model.train()
                
                for i in range(0, len(X_train_scaled), 512):
                    batch_X = torch.FloatTensor(X_train_scaled[i:i+512]).to(device)
                    batch_y = torch.FloatTensor(y_train[i:i+512]).unsqueeze(1).to(device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
        
        ae_optimizer = optim.Adam(self.models['autoencoder'].parameters())
        ae_criterion = nn.MSELoss()
        
        print("Training autoencoder...")
        for epoch in range(20):
            self.models['autoencoder'].train()
            
            for i in range(0, len(X_train_scaled), 512):
                batch_X = torch.FloatTensor(X_train_scaled[i:i+512]).to(device)
                
                ae_optimizer.zero_grad()
                reconstructed = self.models['autoencoder'](batch_X)
                loss = ae_criterion(reconstructed, batch_X)
                loss.backward()
                ae_optimizer.step()
        
        print("Training anomaly detectors...")
        self.models['isolation_forest'] = IsolationForest(contamination=0.1, random_state=42)
        self.models['isolation_forest'].fit(X_train_scaled)
        
        self.models['lof'] = LocalOutlierFactor(n_neighbors=20, contamination=0.1, novelty=True)
        self.models['lof'].fit(X_train_scaled)
        
        self.models['ocsvm'] = OneClassSVM(nu=0.1, gamma='scale')
        self.models['ocsvm'].fit(X_train_scaled)
        
        print("Models trained successfully!")
    
    def analyze_time_series(self, df):
        ts_data = df.groupby(pd.to_datetime(df['first_seen']).dt.date).size()
        
        if len(ts_data) > 10:
            try:
                model = ARIMA(ts_data.values, order=(1,1,1))
                fitted = model.fit()
                forecast = fitted.forecast(steps=30)
                
                growth_rate = np.mean(np.diff(ts_data.values))
                changepoints = self._detect_changepoints(ts_data.values)
                
                return {
                    'forecast': forecast,
                    'growth_rate': growth_rate,
                    'changepoints': changepoints
                }
            except:
                pass
        
        return {}
    
    def _detect_changepoints(self, data):
        changepoints = []
        window = 5
        
        for i in range(window, len(data) - window):
            before = data[i-window:i]
            after = data[i:i+window]
            
            if np.mean(after) > np.mean(before) * 1.5:
                changepoints.append(i)
        
        return changepoints
    
    def build_network_graph(self, df):
        for _, row in df.iterrows():
            hostname = row.get('host', '')
            if hostname:
                self.graph.add_node(hostname)
                
                tokens = re.split(r'[-._]', hostname.lower())
                for token in tokens:
                    if not token.isdigit():
                        for _, row2 in df.iterrows():
                            h2 = row2.get('host', '')
                            if h2 and h2 != hostname and token in h2.lower():
                                self.graph.add_edge(hostname, h2)
                                break
        
        return self.graph
    
    def predict_missing(self, df):
        print("\nDiscovering missing assets...")
        
        existing = set(df['host'].dropna().str.lower())
        patterns = self.discover_patterns(list(existing))
        
        candidates = []
        for pattern in patterns[:100]:
            if 'missing' in pattern:
                template = pattern['template']
                for pos, missing_nums in pattern['missing'].items():
                    for num in missing_nums[:100]:
                        candidate = template.replace('XXX', str(num), 1)
                        if candidate not in existing:
                            candidates.append({
                                'hostname': candidate,
                                'pattern': template,
                                'similar': pattern['samples']
                            })
        
        print(f"Analyzing {len(candidates)} candidates...")
        
        predictions = []
        self.models['lstm'].eval()
        self.models['transformer'].eval()
        self.models['autoencoder'].eval()
        
        with torch.no_grad():
            for candidate in candidates[:10000]:
                features = self.extract_features(candidate['hostname'])
                features_scaled = self.scaler.transform([features])
                features_tensor = torch.FloatTensor(features_scaled).to(device)
                
                lstm_score = self.models['lstm'](features_tensor).cpu().item()
                transformer_score = self.models['transformer'](features_tensor).cpu().item()
                
                ae_error = self.models['autoencoder'].get_error(features_tensor).cpu().item()
                ae_score = 1 / (1 + ae_error)
                
                if_score = self.models['isolation_forest'].decision_function(features_scaled)[0]
                lof_score = self.models['lof'].decision_function(features_scaled)[0]
                ocsvm_score = self.models['ocsvm'].decision_function(features_scaled)[0]
                
                ensemble_score = (lstm_score * 0.25 + 
                                transformer_score * 0.25 + 
                                ae_score * 0.2 +
                                (if_score + 1) * 0.1 +
                                (lof_score + 1) * 0.1 +
                                (ocsvm_score + 1) * 0.1)
                
                if ensemble_score > 0.4:
                    predictions.append({
                        'hostname': candidate['hostname'],
                        'confidence': ensemble_score,
                        'lstm_score': lstm_score,
                        'transformer_score': transformer_score,
                        'autoencoder_score': ae_score,
                        'anomaly_scores': {
                            'isolation_forest': if_score,
                            'lof': lof_score,
                            'ocsvm': ocsvm_score
                        },
                        'pattern': candidate['pattern'],
                        'similar_hosts': candidate['similar']
                    })
        
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return predictions

def main():
    print("="*80)
    print("COMPREHENSIVE ASSET DISCOVERY SYSTEM")
    print("Implementing all techniques from research document")
    print("="*80)
    
    discovery = ComprehensiveAssetDiscovery()
    
    conn = duckdb.connect('universal_cmdb.db')
    df = conn.execute("SELECT * FROM universal_cmdb").df()
    conn.close()
    
    print(f"Loaded {len(df)} records")
    
    discovery.train_models(df)
    
    ts_analysis = discovery.analyze_time_series(df)
    if ts_analysis:
        print(f"Time series growth rate: {ts_analysis.get('growth_rate', 0):.2f} assets/day")
    
    graph = discovery.build_network_graph(df)
    print(f"Network graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    predictions = discovery.predict_missing(df)
    
    print(f"\nFound {len(predictions)} missing assets")
    
    for i, pred in enumerate(predictions[:50]):
        print(f"\n{i+1}. {pred['hostname']}")
        print(f"   Confidence: {pred['confidence']:.2%}")
        print(f"   LSTM: {pred['lstm_score']:.2%} | Transformer: {pred['transformer_score']:.2%}")
        print(f"   Similar: {', '.join(pred['similar_hosts'][:3])}")
    
    with open(f'missing_assets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(predictions, f, indent=2)
    
    print(f"\nResults saved to JSON file")

if __name__ == '__main__':
    main()