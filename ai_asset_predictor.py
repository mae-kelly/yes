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
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import DBSCAN
from datetime import datetime
import os
import pickle
import gc
import json
from typing import List, Dict, Optional, Tuple, Set
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

if torch.cuda.is_available():
   device = torch.device("cuda")
   print("Using NVIDIA GPU (CUDA)")
elif torch.backends.mps.is_available():
   device = torch.device("mps")
   print("Using Apple Silicon GPU (MPS)")
else:
   raise RuntimeError("GPU required. CPU mode not supported for performance reasons.")

class HostnameLSTM(nn.Module):
   def __init__(self, vocab_size, embedding_dim=128, hidden_dim=256, num_layers=2):
       super().__init__()
       self.embedding = nn.Embedding(vocab_size, embedding_dim)
       self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers, 
                          batch_first=True, dropout=0.3, bidirectional=True)
       self.fc = nn.Linear(hidden_dim * 2, vocab_size)
       self.dropout = nn.Dropout(0.3)
       
   def forward(self, x):
       embedded = self.dropout(self.embedding(x))
       lstm_out, _ = self.lstm(embedded)
       output = self.fc(lstm_out)
       return output

class AssetAnomalyAutoencoder(nn.Module):
   def __init__(self, input_dim, encoding_dim=32):
       super().__init__()
       self.encoder = nn.Sequential(
           nn.Linear(input_dim, 256),
           nn.ReLU(),
           nn.BatchNorm1d(256),
           nn.Dropout(0.2),
           nn.Linear(256, 128),
           nn.ReLU(),
           nn.BatchNorm1d(128),
           nn.Dropout(0.2),
           nn.Linear(128, 64),
           nn.ReLU(),
           nn.Linear(64, encoding_dim)
       )
       self.decoder = nn.Sequential(
           nn.Linear(encoding_dim, 64),
           nn.ReLU(),
           nn.Linear(64, 128),
           nn.ReLU(),
           nn.BatchNorm1d(128),
           nn.Linear(128, 256),
           nn.ReLU(),
           nn.BatchNorm1d(256),
           nn.Linear(256, input_dim)
       )
       
   def forward(self, x):
       encoded = self.encoder(x)
       decoded = self.decoder(encoded)
       return decoded

class StrategicAssetPredictor:
   def __init__(self, db_path: str = 'universal_cmdb.db', dataset_size: int = None):
       self.db_path = db_path
       self.dataset_size = dataset_size
       self.model_dir = 'models'
       self.lstm_model = None
       self.autoencoder = None
       self.isolation_forest = None
       self.one_class_svm = None
       self.lof = None
       self.random_forest = None
       self.feature_scaler = StandardScaler()
       self.char_to_idx = {}
       self.idx_to_char = {}
       self.trained = False
       
       if dataset_size and dataset_size > 10000000:
           self.min_pattern_support = 10000
           self.anomaly_contamination = 0.01
       elif dataset_size and dataset_size > 1000000:
           self.min_pattern_support = 1000
           self.anomaly_contamination = 0.02
       else:
           self.min_pattern_support = 100
           self.anomaly_contamination = 0.05
           
       self.confidence_threshold = 0.85
       self.max_predictions = 1000
       self.sequence_window = 10
       
       self.pattern_clusters = {}
       self.fake_hosts = set()
       self.validated_patterns = []
       self.high_confidence_gaps = []
       
       os.makedirs(self.model_dir, exist_ok=True)
       os.makedirs('reports', exist_ok=True)
       
   def get_db_connection(self):
       try:
           return duckdb.connect(self.db_path)
       except Exception as e:
           print(f"Database connection error: {e}")
           return None
   
   def load_data(self) -> pd.DataFrame:
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
       WHERE host IS NOT NULL
       AND LENGTH(host) > 3
       """
       
       try:
           df = conn.execute(query).df()
           print(f"Loaded {len(df):,} records from database")
           self.dataset_size = len(df)
           
           if self.dataset_size > 10000000:
               self.min_pattern_support = 10000
               self.anomaly_contamination = 0.01
           elif self.dataset_size > 1000000:
               self.min_pattern_support = 1000
               self.anomaly_contamination = 0.02
               
           return df
       except Exception as e:
           print(f"Error: {e}")
           return pd.DataFrame()
       finally:
           conn.close()
   
   def calculate_entropy(self, hostname: str) -> float:
       if not hostname:
           return 0.0
       probs = [hostname.count(c) / len(hostname) for c in set(hostname)]
       return -sum(p * np.log2(p) if p > 0 else 0 for p in probs)
   
   def extract_features(self, df: pd.DataFrame) -> np.ndarray:
       print("Extracting features from all hosts...")
       features = []
       
       for idx, row in df.iterrows():
           if idx % 500000 == 0 and idx > 0:
               print(f"  Processed {idx:,} records...")
               
           hostname = str(row['host']).lower() if pd.notna(row['host']) else ''
           
           feat = [
               len(hostname),
               hostname.count('.'),
               hostname.count('-'),
               hostname.count('_'),
               len(re.findall(r'\d', hostname)),
               len(re.findall(r'[a-z]', hostname)),
               self.calculate_entropy(hostname),
               1 if hostname and hostname[0].isdigit() else 0,
               1 if hostname and hostname[-1].isdigit() else 0,
               len(hostname.split('.')),
               len(hostname.split('-')),
               len(hostname.split('_'))
           ]
           
           monitoring_score = 0.0
           if pd.notna(row['logging_in_splunk']) and row['logging_in_splunk'] == 'yes':
               monitoring_score += 0.25
           if pd.notna(row['logging_in_gso']) and row['logging_in_gso'] == 'yes':
               monitoring_score += 0.25
           if pd.notna(row['present_in_cmdb']) and row['present_in_cmdb'] == 'yes':
               monitoring_score += 0.25
           if pd.notna(row['edr_coverage']) and row['edr_coverage'] != 'none':
               monitoring_score += 0.25
           
           feat.extend([
               monitoring_score,
               float(row['data_quality_score']) if pd.notna(row['data_quality_score']) else 0.0,
               int(row['source_count']) if pd.notna(row['source_count']) else 0,
               1 if pd.notna(row['business_unit']) else 0,
               1 if pd.notna(row['region']) else 0,
               1 if pd.notna(row['data_center']) else 0,
               1 if pd.notna(row['cloud_region']) else 0,
               1 if pd.notna(row['system_classification']) else 0
           ])
           
           features.append(feat)
           
       return np.array(features)
   
   def identify_fake_hosts_with_ml(self, df: pd.DataFrame):
       print("\nTraining anomaly detection models to identify fake/error hosts...")
       
       features = self.extract_features(df)
       features_scaled = self.feature_scaler.fit_transform(features)
       
       print("  Training Isolation Forest...")
       self.isolation_forest = IsolationForest(
           contamination=self.anomaly_contamination,
           random_state=42,
           n_estimators=100
       )
       iso_predictions = self.isolation_forest.fit_predict(features_scaled)
       
       print("  Training Local Outlier Factor...")
       self.lof = LocalOutlierFactor(
           contamination=self.anomaly_contamination,
           n_neighbors=min(20, len(df) // 100)
       )
       lof_predictions = self.lof.fit_predict(features_scaled)
       
       print("  Training One-Class SVM...")
       sample_size = min(50000, len(features_scaled))
       sample_indices = np.random.choice(len(features_scaled), sample_size, replace=False)
       self.one_class_svm = OneClassSVM(
           gamma='auto',
           nu=self.anomaly_contamination,
           kernel='rbf'
       )
       self.one_class_svm.fit(features_scaled[sample_indices])
       svm_predictions = self.one_class_svm.predict(features_scaled)
       
       print("  Training Autoencoder...")
       input_dim = features_scaled.shape[1]
       self.autoencoder = AssetAnomalyAutoencoder(input_dim).to(device)
       self.train_autoencoder(features_scaled)
       
       reconstruction_errors = self.get_reconstruction_errors(features_scaled)
       threshold = np.percentile(reconstruction_errors, 95)
       autoencoder_predictions = (reconstruction_errors > threshold).astype(int) * -1 + (reconstruction_errors <= threshold).astype(int)
       
       ensemble_scores = (
           (iso_predictions == -1).astype(int) +
           (lof_predictions == -1).astype(int) +
           (svm_predictions == -1).astype(int) +
           (autoencoder_predictions == -1).astype(int)
       )
       
       pattern_groups = self.analyze_hostname_patterns(df)
       
       for idx, row in df.iterrows():
           hostname = str(row['host']).lower() if pd.notna(row['host']) else ''
           pattern = re.sub(r'\d+', 'XXX', hostname)
           
           is_singleton = pattern_groups.get(pattern, 0) == 1
           is_anomaly = ensemble_scores[idx] >= 3
           has_low_monitoring = features[idx][12] < 0.25
           has_low_quality = features[idx][13] < 3.0
           
           suspicious_keywords = ['test', 'temp', 'delete', 'old', 'backup', 'copy', 
                                 'demo', 'sample', 'example', 'dummy', 'fake', 'xxx', 
                                 'aaa', 'zzz', '123', 'asdf']
           has_suspicious_name = any(kw in hostname for kw in suspicious_keywords)
           
           if (is_singleton and is_anomaly) or (is_singleton and has_low_monitoring and has_low_quality) or (is_anomaly and has_suspicious_name):
               self.fake_hosts.add(hostname)
       
       print(f"\nIdentified {len(self.fake_hosts):,} fake/error hosts to exclude")
       
       if len(self.fake_hosts) > 0:
           sample_fakes = list(self.fake_hosts)[:10]
           print("Sample fake hosts:", sample_fakes)
   
   def analyze_hostname_patterns(self, df: pd.DataFrame) -> Dict[str, int]:
       pattern_counts = defaultdict(int)
       
       for hostname in df['host'].dropna():
           hostname = str(hostname).lower()
           pattern = re.sub(r'\d+', 'XXX', hostname)
           pattern_counts[pattern] += 1
           
       return dict(pattern_counts)
   
   def train_autoencoder(self, features: np.ndarray):
       dataset = torch.FloatTensor(features).to(device)
       dataloader = torch.utils.data.DataLoader(dataset, batch_size=256, shuffle=True)
       
       optimizer = optim.Adam(self.autoencoder.parameters(), lr=0.001)
       criterion = nn.MSELoss()
       
       self.autoencoder.train()
       for epoch in range(20):
           total_loss = 0.0
           for batch in dataloader:
               optimizer.zero_grad()
               reconstructed = self.autoencoder(batch)
               loss = criterion(reconstructed, batch)
               loss.backward()
               optimizer.step()
               total_loss += loss.item()
           
           if epoch % 5 == 0:
               print(f"    Epoch {epoch+1}/20, Loss: {total_loss/len(dataloader):.4f}")
   
   def get_reconstruction_errors(self, features: np.ndarray) -> np.ndarray:
       self.autoencoder.eval()
       errors = []
       
       with torch.no_grad():
           for i in range(0, len(features), 1000):
               batch = torch.FloatTensor(features[i:i+1000]).to(device)
               reconstructed = self.autoencoder(batch)
               error = ((batch - reconstructed) ** 2).mean(dim=1).cpu().numpy()
               errors.extend(error)
               
       return np.array(errors)
   
   def discover_valid_patterns(self, df: pd.DataFrame) -> List[Dict]:
       print("\nDiscovering valid hostname patterns...")
       
       df_clean = df[~df['host'].str.lower().isin(self.fake_hosts)]
       print(f"  Working with {len(df_clean):,} validated hosts")
       
       pattern_groups = defaultdict(list)
       
       for hostname in df_clean['host'].dropna():
           hostname = str(hostname).lower()
           if re.search(r'\d', hostname):
               pattern = re.sub(r'\d+', 'XXX', hostname)
               pattern_groups[pattern].append(hostname)
       
       valid_patterns = []
       
       for pattern, hostnames in pattern_groups.items():
           if len(hostnames) >= self.min_pattern_support:
               numbers = []
               for hostname in hostnames:
                   nums = re.findall(r'\d+', hostname)
                   if nums:
                       numbers.extend([int(n) for n in nums])
               
               if numbers:
                   numbers = sorted(set(numbers))
                   density = len(numbers) / (max(numbers) - min(numbers) + 1) if max(numbers) > min(numbers) else 1.0
                   
                   if density > 0.3:
                       valid_patterns.append({
                           'pattern': pattern,
                           'count': len(hostnames),
                           'numbers': numbers,
                           'density': density,
                           'sample_hosts': hostnames[:5]
                       })
       
       print(f"  Found {len(valid_patterns)} valid patterns with sufficient support")
       return valid_patterns
   
   def train_lstm_sequence_predictor(self, patterns: List[Dict]):
       print("\nTraining LSTM for sequence prediction...")
       
       sequences = []
       for pattern in patterns[:100]:
           if pattern['density'] > 0.5:
               numbers = pattern['numbers']
               for i in range(len(numbers) - self.sequence_window):
                   sequences.append(numbers[i:i+self.sequence_window+1])
       
       if not sequences:
           print("  Insufficient sequences for LSTM training")
           return
       
       all_nums = set()
       for seq in sequences:
           all_nums.update(seq)
       
       self.char_to_idx = {num: idx for idx, num in enumerate(sorted(all_nums))}
       self.idx_to_char = {idx: num for num, idx in self.char_to_idx.items()}
       vocab_size = len(self.char_to_idx)
       
       X, y = [], []
       for seq in sequences:
           encoded = [self.char_to_idx.get(n, 0) for n in seq]
           X.append(encoded[:-1])
           y.append(encoded[1:])
       
       X_tensor = torch.LongTensor(X).to(device)
       y_tensor = torch.LongTensor(y).to(device)
       
       self.lstm_model = HostnameLSTM(vocab_size).to(device)
       optimizer = optim.Adam(self.lstm_model.parameters(), lr=0.001)
       criterion = nn.CrossEntropyLoss()
       
       dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
       dataloader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
       
       self.lstm_model.train()
       for epoch in range(30):
           total_loss = 0.0
           for batch_x, batch_y in dataloader:
               optimizer.zero_grad()
               output = self.lstm_model(batch_x)
               loss = criterion(output.view(-1, vocab_size), batch_y.view(-1))
               loss.backward()
               optimizer.step()
               total_loss += loss.item()
           
           if epoch % 10 == 0:
               print(f"  Epoch {epoch+1}/30, Loss: {total_loss/len(dataloader):.4f}")
   
   def predict_missing_assets_strategically(self, df: pd.DataFrame, patterns: List[Dict]) -> List[Dict]:
       print("\nStrategically predicting missing assets...")
       
       existing_hosts = set(df['host'].str.lower().dropna())
       predictions = []
       
       patterns_sorted = sorted(patterns, key=lambda x: x['count'] * x['density'], reverse=True)
       
       for pattern in patterns_sorted[:50]:
           if pattern['density'] < 0.5:
               continue
               
           numbers = pattern['numbers']
           min_num, max_num = min(numbers), max(numbers)
           
           missing = []
           for i in range(min_num, min(max_num + 1, min_num + 100)):
               if i not in numbers:
                   missing.append(i)
           
           if len(missing) > 0 and len(missing) < 50:
               for miss_num in missing:
                   candidate = pattern['pattern'].replace('XXX', str(miss_num), 1)
                   
                   if candidate not in existing_hosts and candidate not in self.fake_hosts:
                       
                       gap_size = min(
                           abs(miss_num - n) for n in numbers 
                           if n != miss_num
                       ) if numbers else float('inf')
                       
                       confidence = 0.0
                       if gap_size == 1:
                           confidence = 0.95
                       elif gap_size == 2:
                           confidence = 0.85
                       elif gap_size <= 5:
                           confidence = 0.70
                       elif gap_size <= 10:
                           confidence = 0.50
                       else:
                           confidence = 0.30
                       
                       confidence *= pattern['density']
                       
                       if confidence >= 0.5:
                           predictions.append({
                               'hostname': candidate,
                               'pattern': pattern['pattern'],
                               'confidence': confidence,
                               'gap_size': gap_size,
                               'pattern_support': pattern['count'],
                               'pattern_density': pattern['density'],
                               'similar_hosts': pattern['sample_hosts'][:3]
                           })
       
       predictions = sorted(predictions, key=lambda x: x['confidence'], reverse=True)[:self.max_predictions]
       
       print(f"  Generated {len(predictions)} high-confidence predictions")
       return predictions
   
   def classify_asset_role(self, hostname: str) -> str:
       hostname_lower = hostname.lower()
       
       role_patterns = [
           (['fw', 'firewall', 'asa', 'palo', 'fortinet'], 'Firewall'),
           (['lb', 'loadbalancer', 'f5', 'haproxy', 'nginx'], 'Load Balancer'),
           (['sw', 'switch', 'nexus', 'catalyst'], 'Switch'),
           (['rt', 'router', 'rtr', 'gw', 'gateway'], 'Router'),
           (['db', 'database', 'sql', 'mysql', 'postgres', 'oracle', 'mongo'], 'Database'),
           (['web', 'www', 'http', 'apache', 'iis'], 'Web Server'),
           (['app', 'application', 'tomcat', 'jboss', 'websphere'], 'App Server'),
           (['cache', 'redis', 'memcache', 'varnish'], 'Cache'),
           (['queue', 'mq', 'kafka', 'rabbit', 'amq', 'sqs'], 'Message Queue'),
           (['mail', 'smtp', 'imap', 'exchange', 'postfix'], 'Mail Server'),
           (['backup', 'bkp', 'bak', 'veeam', 'commvault'], 'Backup'),
           (['monitor', 'mon', 'nagios', 'zabbix', 'prometheus'], 'Monitoring'),
           (['log', 'syslog', 'splunk', 'elastic', 'logstash'], 'Logging'),
           (['dns', 'bind', 'ns'], 'DNS Server'),
           (['proxy', 'squid', 'bluecoat'], 'Proxy'),
           (['dc', 'domain', 'ad', 'ldap'], 'Domain Controller'),
           (['ntp', 'time', 'chrony'], 'Time Server'),
           (['vpn', 'ipsec', 'openvpn', 'anyconnect'], 'VPN'),
           (['storage', 'san', 'nas', 'netapp', 'emc'], 'Storage'),
           (['k8s', 'kubernetes', 'docker', 'container', 'pod'], 'Container')
       ]
       
       for patterns, role in role_patterns:
           if any(p in hostname_lower for p in patterns):
               return role
       return 'Server'
   
   def calculate_risk_score(self, hostname: str, confidence: float) -> float:
       hostname_lower = hostname.lower()
       
       risk = 0.5
       
       if any(env in hostname_lower for env in ['prod', 'prd', 'production']):
           risk = 0.9
       elif any(env in hostname_lower for env in ['stage', 'stg', 'staging', 'uat']):
           risk = 0.7
       elif any(env in hostname_lower for env in ['test', 'tst', 'qa']):
           risk = 0.5
       elif any(env in hostname_lower for env in ['dev', 'development']):
           risk = 0.3
       
       role = self.classify_asset_role(hostname)
       critical_roles = {
           'Firewall': 0.95, 'Database': 0.90, 'Domain Controller': 0.95,
           'Load Balancer': 0.85, 'Router': 0.85, 'Switch': 0.80,
           'VPN': 0.85, 'DNS Server': 0.85, 'Mail Server': 0.75
       }
       role_risk = critical_roles.get(role, 0.5)
       
       risk = max(risk, role_risk)
       
       risk *= (confidence ** 0.5)
       
       return min(risk, 1.0)
   
   def run_analysis(self):
       print("\n" + "="*80)
       print("STRATEGIC ML-BASED MISSING ASSET DISCOVERY")
       print("="*80)
       
       start_time = datetime.now()
       
       df = self.load_data()
       if df.empty:
           print("No data available")
           return
       
       self.identify_fake_hosts_with_ml(df)
       
       valid_patterns = self.discover_valid_patterns(df)
       
       if len(valid_patterns) > 10:
           self.train_lstm_sequence_predictor(valid_patterns)
       
       predictions = self.predict_missing_assets_strategically(df, valid_patterns)
       
       self.display_results(predictions)
       self.export_results(predictions)
       
       total_time = (datetime.now() - start_time).total_seconds()
       print(f"\nTotal analysis time: {total_time:.1f} seconds")
       print("="*80)
   
   def display_results(self, predictions: List[Dict]):
       if not predictions:
           print("\nNo missing assets found with sufficient confidence")
           return
       
       print("\n" + "="*80)
       print("HIGH-CONFIDENCE MISSING ASSETS")
       print("="*80)
       
       critical_assets = []
       high_risk_assets = []
       medium_risk_assets = []
       
       for pred in predictions:
           risk = self.calculate_risk_score(pred['hostname'], pred['confidence'])
           role = self.classify_asset_role(pred['hostname'])
           
           asset_info = {
               'hostname': pred['hostname'],
               'confidence': pred['confidence'],
               'risk': risk,
               'role': role,
               'pattern': pred['pattern'],
               'gap_size': pred['gap_size'],
               'similar': pred['similar_hosts']
           }
           
           if risk >= 0.8:
               critical_assets.append(asset_info)
           elif risk >= 0.6:
               high_risk_assets.append(asset_info)
           else:
               medium_risk_assets.append(asset_info)
       
       if critical_assets:
           print("\nCRITICAL RISK MISSING ASSETS:")
           print("-"*80)
           for asset in critical_assets[:20]:
               print(f"{asset['hostname']:<40} Confidence: {asset['confidence']:.1%} "
                     f"Risk: {asset['risk']:.2f} Role: {asset['role']}")
       
       if high_risk_assets:
           print("\nHIGH RISK MISSING ASSETS:")
           print("-"*80)
           for asset in high_risk_assets[:20]:
               print(f"{asset['hostname']:<40} Confidence: {asset['confidence']:.1%} "
                     f"Risk: {asset['risk']:.2f} Role: {asset['role']}")
       
       print("\n" + "="*80)
       print("SUMMARY")
       print("="*80)
       print(f"Total fake/error hosts identified: {len(self.fake_hosts):,}")
       print(f"Total missing assets predicted: {len(predictions)}")
       print(f"Critical risk assets: {len(critical_assets)}")
       print(f"High risk assets: {len(high_risk_assets)}")
       print(f"Medium risk assets: {len(medium_risk_assets)}")
       
       role_dist = Counter(self.classify_asset_role(p['hostname']) for p in predictions)
       print("\nMissing Assets by Type:")
       for role, count in role_dist.most_common(10):
           print(f"  {role}: {count}")
   
   def export_results(self, predictions: List[Dict]):
       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       
       enriched_predictions = []
       for pred in predictions:
           risk = self.calculate_risk_score(pred['hostname'], pred['confidence'])
           role = self.classify_asset_role(pred['hostname'])
           
           enriched_predictions.append({
               'hostname': pred['hostname'],
               'confidence': pred['confidence'],
               'risk_score': risk,
               'risk_level': 'CRITICAL' if risk >= 0.8 else 'HIGH' if risk >= 0.6 else 'MEDIUM',
               'asset_role': role,
               'pattern': pred['pattern'],
               'pattern_support': pred['pattern_support'],
               'pattern_density': pred['pattern_density'],
               'gap_size': pred['gap_size']
           })
       
       json_file = f"reports/strategic_missing_assets_{timestamp}.json"
       with open(json_file, 'w') as f:
           json.dump({
               'timestamp': datetime.now().isoformat(),
               'total_hosts_analyzed': self.dataset_size,
               'fake_hosts_identified': len(self.fake_hosts),
               'missing_assets_predicted': len(predictions),
               'predictions': enriched_predictions
           }, f, indent=2, default=str)
       
       csv_file = f"reports/strategic_missing_assets_{timestamp}.csv"
       pd.DataFrame(enriched_predictions).to_csv(csv_file, index=False)
       
       print(f"\nResults exported:")
       print(f"  JSON: {json_file}")
       print(f"  CSV: {csv_file}")

def main():
   print("\n" + "="*80)
   print("   STRATEGIC AI ASSET PREDICTOR")
   print("="*80)
   print(f"Device: {device}")
   print("="*80)
   
   try:
       predictor = StrategicAssetPredictor()
       predictor.run_analysis()
   except KeyboardInterrupt:
       print("\n\nAnalysis interrupted by user")
   except Exception as e:
       print(f"\nError: {e}")
       import traceback
       traceback.print_exc()

if __name__ == '__main__':
   main()