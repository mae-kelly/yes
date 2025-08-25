#!/usr/bin/env python3
"""
AI Asset Predictor - Automated Comprehensive Missing IT Asset Discovery
Runs full analysis automatically without user interaction
"""

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
from datetime import datetime
import os
import pickle
import gc
import json
from typing import List, Dict, Optional, Tuple, Set
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# Device configuration
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("🚀 Using NVIDIA GPU (CUDA)")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
    print("🚀 Using Apple Silicon GPU (MPS)")
else:
    device = torch.device("cpu")
    print("⚠️  Using CPU - Training will be slower")

class HostnamePatternNet(nn.Module):
    """Enhanced neural network for hostname pattern analysis"""
    def __init__(self, input_size: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        return self.layers(x)

class LogVisibilityPredictor(nn.Module):
    """Multi-class predictor for system visibility"""
    def __init__(self, input_size: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 5),
            nn.Softmax(dim=1)
        )
        
    def forward(self, x):
        return self.layers(x)

class ComprehensiveAssetPredictor:
    """
    Fully automated ML system for missing asset discovery
    """
    
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        self.hostname_net = None
        self.log_visibility_net = None
        self.feature_scaler = StandardScaler()
        self.isolation_forest = None
        self.trained = False
        self.db_path = db_path
        self.model_version = "Auto-Asset-Predictor-v3.0"
        self.training_metrics = {}
        self.model_dir = 'models'
        
        # Comprehensive scan configuration
        self.min_pattern_frequency = 2
        self.max_gap_size = 10000
        self.max_candidates_to_analyze = 10000  # Analyze many more
        self.batch_size_prediction = 500
        
        # Multi-level thresholds for comprehensive results
        self.confidence_levels = {
            'critical': 0.85,
            'high': 0.70,
            'medium': 0.50,
            'low': 0.30,
            'experimental': 0.15
        }
        
        # Statistics
        self.analysis_stats = defaultdict(int)
        
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
    def get_db_connection(self):
        """Get DuckDB connection"""
        try:
            return duckdb.connect(self.db_path)
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def extract_hostname_features(self, hostname: str) -> np.ndarray:
        """Extract comprehensive features from hostname"""
        if not hostname:
            return np.zeros(65)
        
        hostname = hostname.lower().strip()
        
        # Enhanced feature extraction
        features = [
            len(hostname),
            hostname.count('.'),
            hostname.count('-'),
            hostname.count('_'),
            len(re.findall(r'\d', hostname)),
            len(re.findall(r'[a-z]', hostname)),
            len(re.findall(r'[A-Z]', hostname.upper())),
            1 if hostname[0].isdigit() else 0,
            1 if hostname[-1].isdigit() else 0,
            len(hostname.split('.')),
            len(hostname.split('-')),
            len(hostname.split('_')),
            1 if re.match(r'^[a-z]{2,4}\d{2,4}', hostname) else 0,
            1 if re.search(r'\d{2,4}$', hostname) else 0,
            1 if re.search(r'^\d', hostname) else 0
        ]
        
        # Comprehensive keyword features
        keywords = [
            ['srv', 'server'], ['web', 'www'], ['db', 'database', 'sql', 'mysql', 'postgres', 'oracle'],
            ['app', 'application'], ['dc', 'datacenter'], ['prod', 'production', 'prd'],
            ['dev', 'development'], ['test', 'testing', 'tst'], ['stage', 'staging', 'stg'],
            ['uat', 'preprod', 'pre-prod'], ['.com'], ['.local'], ['.net'], ['.org'],
            ['1dc'], ['2dc'], ['3dc'], ['fead'], ['fiserv'], ['firewall', 'fw'],
            ['ids', 'ips'], ['ndr', 'detection'], ['proxy', 'px', 'prx'],
            ['dns', 'domain', 'ns'], ['waf', 'gateway', 'gw'], 
            ['north', 'south', 'east', 'west', 'central'],
            ['us', 'usa', 'america'], ['eu', 'emea', 'europe'], ['uk', 'london'],
            ['apac', 'asia', 'pacific'], ['vm', 'virtual', 'virt'], ['docker', 'container', 'k8s'],
            ['aws', 'ec2', 'lambda', 's3'], ['azure', 'az'], ['gcp', 'google'], ['cloud'],
            ['backup', 'bkp', 'bak'], ['monitor', 'mon', 'nagios'], ['log', 'logging', 'syslog'],
            ['cache', 'redis', 'memcache'], ['queue', 'mq', 'rabbit', 'kafka', 'sqs'],
            ['lb', 'loadbalancer', 'haproxy', 'f5'], ['vpn', 'ipsec', 'openvpn'],
            ['mail', 'smtp', 'imap', 'exchange'], ['ntp', 'time'], ['ldap', 'ad', 'activedirectory'],
            ['jenkins', 'ci', 'cd', 'build'], ['git', 'svn', 'repo'], ['elastic', 'elk', 'kibana'],
            ['switch', 'sw', 'nexus'], ['router', 'rt', 'rtr'], ['san', 'storage', 'nas']
        ]
        
        for keyword_group in keywords:
            features.append(1 if any(kw in hostname for kw in keyword_group) else 0)
        
        # Pad to 65 features
        while len(features) < 65:
            features.append(0)
        
        return np.array(features[:65])
    
    def get_cmdb_data(self) -> pd.DataFrame:
        """Fetch CMDB data"""
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
            print(f"✅ Loaded {len(df):,} records from database")
            return df
        except Exception as e:
            print(f"❌ Error: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def discover_all_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Discover ALL hostname patterns aggressively"""
        print("\n🔍 Discovering hostname patterns...")
        
        pattern_groups = defaultdict(list)
        
        for hostname in df['host'].dropna():
            hostname = str(hostname).lower().strip()
            if hostname and re.search(r'\d', hostname):
                pattern_template = re.sub(r'\d+', 'XXX', hostname)
                
                numbers = []
                for match in re.finditer(r'\d+', hostname):
                    numbers.append({
                        'value': int(match.group()),
                        'position': match.start(),
                        'length': len(match.group()),
                        'padded': match.group()[0] == '0' and len(match.group()) > 1
                    })
                
                pattern_groups[pattern_template].append({
                    'hostname': hostname,
                    'template': pattern_template,
                    'numbers': numbers
                })
        
        discovered_patterns = []
        
        for template, hostnames in pattern_groups.items():
            if len(hostnames) >= self.min_pattern_frequency:
                number_sequences = defaultdict(list)
                
                for host_data in hostnames:
                    for i, num_data in enumerate(host_data['numbers']):
                        number_sequences[i].append(num_data)
                
                pattern_info = {
                    'template': template,
                    'host_count': len(hostnames),
                    'sample_hosts': [h['hostname'] for h in hostnames[:10]],
                    'number_sequences': {}
                }
                
                for pos, num_list in number_sequences.items():
                    values = [n['value'] for n in num_list]
                    unique_values = sorted(set(values))
                    
                    if len(unique_values) > 1:
                        min_val, max_val = min(unique_values), max(unique_values)
                        
                        missing = []
                        for i in range(min_val, min(max_val + 1, min_val + self.max_gap_size)):
                            if i not in unique_values:
                                missing.append(i)
                        
                        density = len(unique_values) / (max_val - min_val + 1) if max_val > min_val else 1.0
                        padding = max([n['length'] for n in num_list]) if num_list else 0
                        is_padded = any([n['padded'] for n in num_list])
                        
                        pattern_info['number_sequences'][pos] = {
                            'existing_values': unique_values,
                            'range': (min_val, max_val),
                            'missing_values': missing,
                            'density': density,
                            'padding': padding if is_padded else 0
                        }
                
                if pattern_info['number_sequences']:
                    discovered_patterns.append(pattern_info)
        
        print(f"   Found {len(discovered_patterns)} patterns with {sum(len(p['number_sequences']) for p in discovered_patterns)} sequences")
        return discovered_patterns

    def generate_all_candidates(self, patterns: List[Dict], existing_hostnames: Set[str]) -> List[Dict]:
        """Generate ALL possible missing candidates"""
        print("\n🔧 Generating missing hostname candidates...")
        
        missing_candidates = []
        
        for pattern_idx, pattern in enumerate(patterns):
            template = pattern['template']
            
            if len(pattern['number_sequences']) == 1:
                pos = list(pattern['number_sequences'].keys())[0]
                seq_info = pattern['number_sequences'][pos]
                
                for missing_num in seq_info['missing_values']:
                    if seq_info.get('padding', 0) > 0:
                        num_str = str(missing_num).zfill(seq_info['padding'])
                    else:
                        num_str = str(missing_num)
                    
                    candidate_hostname = template.replace('XXX', num_str, 1)
                    
                    if candidate_hostname not in existing_hostnames:
                        missing_candidates.append({
                            'hostname': candidate_hostname,
                            'pattern_template': template,
                            'pattern_density': seq_info['density'],
                            'existing_hosts_count': pattern['host_count'],
                            'sample_existing': pattern['sample_hosts'][:3]
                        })
            
            elif len(pattern['number_sequences']) == 2:
                positions = list(pattern['number_sequences'].keys())
                seq1 = pattern['number_sequences'][positions[0]]
                seq2 = pattern['number_sequences'][positions[1]]
                
                for num1 in seq1['missing_values'][:100]:  # Limit for dual sequences
                    for num2 in seq2['missing_values'][:100]:
                        candidate_hostname = template
                        
                        num1_str = str(num1).zfill(seq1.get('padding', 0)) if seq1.get('padding', 0) else str(num1)
                        num2_str = str(num2).zfill(seq2.get('padding', 0)) if seq2.get('padding', 0) else str(num2)
                        
                        candidate_hostname = candidate_hostname.replace('XXX', num1_str, 1)
                        candidate_hostname = candidate_hostname.replace('XXX', num2_str, 1)
                        
                        if candidate_hostname not in existing_hostnames:
                            missing_candidates.append({
                                'hostname': candidate_hostname,
                                'pattern_template': template,
                                'pattern_density': (seq1['density'] + seq2['density']) / 2,
                                'existing_hosts_count': pattern['host_count'],
                                'sample_existing': pattern['sample_hosts'][:3]
                            })
        
        print(f"   Generated {len(missing_candidates):,} unique candidates")
        return missing_candidates
    
    def prepare_training_data(self, df: pd.DataFrame) -> tuple:
        """Prepare training data"""
        features, existence_labels, visibility_labels = [], [], []
        
        print(f"\n📊 Processing {len(df):,} records for training...")
        
        for idx, row in df.iterrows():
            if idx % 200000 == 0 and idx > 0:
                print(f"   Processed {idx:,} records...")
                
            hostname_features = self.extract_hostname_features(row['host']) if pd.notna(row['host']) else self.extract_hostname_features("")
            
            additional_features = [
                1 if pd.notna(row['business_unit']) else 0,
                1 if pd.notna(row['region']) else 0,
                1 if pd.notna(row['country']) else 0,
                1 if pd.notna(row['data_center']) else 0,
                1 if pd.notna(row['cloud_region']) else 0,
                1 if pd.notna(row['system_classification']) and 'server' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['system_classification']) and 'windows' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['system_classification']) and 'linux' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['infrastructure_type']) and 'cloud' in str(row['infrastructure_type']).lower() else 0,
                1 if pd.notna(row['infrastructure_type']) and 'physical' in str(row['infrastructure_type']).lower() else 0,
                1 if pd.notna(row['infrastructure_type']) and 'virtual' in str(row['infrastructure_type']).lower() else 0,
                float(row['data_quality_score']) if pd.notna(row['data_quality_score']) else 0.0,
                int(row['source_count']) if pd.notna(row['source_count']) else 0,
                1 if pd.notna(row['cio']) else 0,
                1 if pd.notna(row['apm']) else 0
            ]
            
            combined_features = np.concatenate([hostname_features, additional_features])
            features.append(combined_features)
            
            # Existence score
            existence_score = 0.0
            if pd.notna(row['logging_in_splunk']) and row['logging_in_splunk'] == 'yes':
                existence_score += 0.35
            if pd.notna(row['present_in_cmdb']) and row['present_in_cmdb'] == 'yes':
                existence_score += 0.35
            if pd.notna(row['edr_coverage']) and row['edr_coverage'] != 'none':
                existence_score += 0.20
            if pd.notna(row['tanium_coverage']) and row['tanium_coverage'] == 'yes':
                existence_score += 0.05
            if pd.notna(row['dlp_agent_coverage']) and row['dlp_agent_coverage'] == 'yes':
                existence_score += 0.05
            
            existence_labels.append(min(existence_score, 1.0))
            
            # Visibility classification
            visibility_type = 0
            splunk = pd.notna(row['logging_in_splunk']) and row['logging_in_splunk'] == 'yes'
            gso = pd.notna(row['logging_in_gso']) and row['logging_in_gso'] == 'yes'
            cmdb = pd.notna(row['present_in_cmdb']) and row['present_in_cmdb'] == 'yes'
            
            if splunk and gso and cmdb:
                visibility_type = 4
            elif splunk and (gso or cmdb):
                visibility_type = 3
            elif splunk or gso:
                visibility_type = 2
            elif cmdb:
                visibility_type = 1
            
            visibility_labels.append(visibility_type)
        
        return np.array(features), np.array(existence_labels), np.array(visibility_labels)
    
    def train_or_load_models(self):
        """Automatically train or load models"""
        model_files = [
            f'{self.model_dir}/hostname_net.pth',
            f'{self.model_dir}/log_visibility_net.pth',
            f'{self.model_dir}/feature_scaler.pkl'
        ]
        
        if all(os.path.exists(f) for f in model_files):
            print("\n📂 Loading existing models...")
            try:
                sample_features = self.extract_hostname_features("sample")
                additional_features = [0] * 15
                input_size = len(np.concatenate([sample_features, additional_features]))
                
                self.hostname_net = HostnamePatternNet(input_size).to(device)
                self.log_visibility_net = LogVisibilityPredictor(input_size).to(device)
                
                self.hostname_net.load_state_dict(torch.load(model_files[0], map_location=device))
                self.log_visibility_net.load_state_dict(torch.load(model_files[1], map_location=device))
                
                with open(model_files[2], 'rb') as f:
                    self.feature_scaler = pickle.load(f)
                
                self.trained = True
                print("✅ Models loaded successfully!")
                return
            except Exception as e:
                print(f"⚠️  Failed to load models: {e}")
        
        print("\n🤖 Training new models...")
        df = self.get_cmdb_data()
        if df.empty:
            print("❌ No data for training!")
            return
        
        X, existence_y, visibility_y = self.prepare_training_data(df)
        
        X_train, X_val, existence_y_train, existence_y_val, visibility_y_train, visibility_y_val = train_test_split(
            X, existence_y, visibility_y, test_size=0.20, random_state=42
        )
        
        del X, existence_y, visibility_y
        gc.collect()
        
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        input_size = X_train_scaled.shape[1]
        self.hostname_net = HostnamePatternNet(input_size).to(device)
        self.log_visibility_net = LogVisibilityPredictor(input_size).to(device)
        
        optimizer1 = optim.AdamW(self.hostname_net.parameters(), lr=0.001)
        optimizer2 = optim.AdamW(self.log_visibility_net.parameters(), lr=0.001)
        
        criterion1 = nn.BCELoss()
        criterion2 = nn.CrossEntropyLoss()
        
        batch_size = 4096 if device.type != 'cpu' else 512
        epochs = 50
        
        print(f"Training on {len(X_train_scaled):,} samples...")
        
        for epoch in range(epochs):
            self.hostname_net.train()
            self.log_visibility_net.train()
            
            total_loss = 0.0
            
            for i in range(0, len(X_train_scaled), batch_size):
                batch_end = min(i + batch_size, len(X_train_scaled))
                
                X_batch = torch.FloatTensor(X_train_scaled[i:batch_end]).to(device)
                existence_y_batch = torch.FloatTensor(existence_y_train[i:batch_end]).reshape(-1, 1).to(device)
                visibility_y_batch = torch.LongTensor(visibility_y_train[i:batch_end]).to(device)
                
                optimizer1.zero_grad()
                existence_outputs = self.hostname_net(X_batch)
                loss1 = criterion1(existence_outputs, existence_y_batch)
                loss1.backward()
                optimizer1.step()
                
                optimizer2.zero_grad()
                visibility_outputs = self.log_visibility_net(X_batch)
                loss2 = criterion2(visibility_outputs, visibility_y_batch)
                loss2.backward()
                optimizer2.step()
                
                total_loss += loss1.item() + loss2.item()
            
            if epoch % 10 == 0:
                print(f'   Epoch {epoch+1}/{epochs}, Loss: {total_loss/(len(X_train_scaled)/batch_size):.4f}')
        
        # Save models
        torch.save(self.hostname_net.state_dict(), model_files[0])
        torch.save(self.log_visibility_net.state_dict(), model_files[1])
        with open(model_files[2], 'wb') as f:
            pickle.dump(self.feature_scaler, f)
        
        self.trained = True
        print("✅ Training completed and models saved!")
    
    def analyze_all_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Analyze ALL candidates with neural networks"""
        print(f"\n🤖 Analyzing {len(candidates):,} candidates with AI...")
        
        predicted_assets = []
        self.hostname_net.eval()
        self.log_visibility_net.eval()
        
        with torch.no_grad():
            for i in range(0, len(candidates), self.batch_size_prediction):
                if i % 5000 == 0 and i > 0:
                    print(f"   Analyzed {i:,} candidates...")
                
                batch_end = min(i + self.batch_size_prediction, len(candidates))
                batch_candidates = candidates[i:batch_end]
                
                batch_features = []
                for candidate in batch_candidates:
                    features = self.extract_hostname_features(candidate['hostname'])
                    additional_features = [1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 7.5, 3, 1, 1]
                    combined_features = np.concatenate([features, additional_features])
                    batch_features.append(combined_features)
                
                batch_features_scaled = self.feature_scaler.transform(batch_features)
                features_tensor = torch.FloatTensor(batch_features_scaled).to(device)
                
                existence_probs = self.hostname_net(features_tensor).cpu().numpy()
                visibility_probs = self.log_visibility_net(features_tensor).cpu().numpy()
                
                for j, candidate in enumerate(batch_candidates):
                    existence_prob = float(existence_probs[j][0])
                    visibility_prob_vector = visibility_probs[j]
                    
                    # Calculate comprehensive scores
                    pattern_score = candidate.get('pattern_density', 0.5)
                    combined_score = (existence_prob * 0.6 + pattern_score * 0.4)
                    
                    # Determine confidence level
                    confidence_level = 'none'
                    for level, threshold in sorted(self.confidence_levels.items(), key=lambda x: x[1], reverse=True):
                        if combined_score >= threshold:
                            confidence_level = level
                            break
                    
                    if confidence_level != 'none':
                        risk_score = self.calculate_risk(candidate['hostname'], existence_prob, visibility_prob_vector)
                        
                        predicted_assets.append({
                            'hostname': candidate['hostname'],
                            'confidence_score': float(combined_score),
                            'confidence_level': confidence_level,
                            'existence_probability': existence_prob,
                            'risk_score': risk_score,
                            'risk_level': self.get_risk_level(risk_score),
                            'predicted_role': self.classify_role(candidate['hostname']),
                            'pattern_template': candidate['pattern_template'][:50] + '...' if len(candidate['pattern_template']) > 50 else candidate['pattern_template'],
                            'pattern_density': f"{candidate['pattern_density']:.1%}",
                            'similar_hosts': candidate['sample_existing'],
                            'existing_count': candidate['existing_hosts_count'],
                            'splunk_probability': float(visibility_prob_vector[3] + visibility_prob_vector[4]),
                            'cmdb_probability': float(sum(visibility_prob_vector[1:]))
                        })
        
        print(f"   Found {len(predicted_assets):,} missing assets across all confidence levels")
        return predicted_assets
    
    def classify_role(self, hostname: str) -> str:
        """Classify asset role"""
        hostname_lower = hostname.lower()
        
        role_patterns = [
            (['fw', 'firewall', 'asa'], 'Firewall'),
            (['lb', 'loadbalancer', 'f5'], 'Load Balancer'),
            (['sw', 'switch'], 'Switch'),
            (['rt', 'router'], 'Router'),
            (['db', 'database', 'sql'], 'Database'),
            (['web', 'www', 'nginx'], 'Web Server'),
            (['app', 'application'], 'App Server'),
            (['cache', 'redis'], 'Cache'),
            (['queue', 'mq', 'kafka'], 'Queue'),
            (['mail', 'smtp'], 'Mail Server'),
            (['backup', 'bkp'], 'Backup'),
            (['monitor', 'mon'], 'Monitoring'),
            (['log', 'syslog'], 'Logging'),
            (['dns'], 'DNS'),
            (['proxy'], 'Proxy'),
            (['srv', 'server'], 'Server')
        ]
        
        for patterns, role in role_patterns:
            if any(p in hostname_lower for p in patterns):
                return role
        return 'Unknown'
    
    def calculate_risk(self, hostname: str, existence_prob: float, visibility_probs: np.ndarray) -> float:
        """Calculate risk score"""
        hostname_lower = hostname.lower()
        
        risk = 0.0
        
        # Environment risk
        if 'prod' in hostname_lower or 'prd' in hostname_lower:
            risk = 0.9
        elif 'uat' in hostname_lower or 'stage' in hostname_lower:
            risk = 0.6
        elif 'test' in hostname_lower:
            risk = 0.4
        elif 'dev' in hostname_lower:
            risk = 0.2
        else:
            risk = 0.5
        
        # Role criticality
        role = self.classify_role(hostname)
        critical_roles = {'Firewall': 0.9, 'Database': 0.9, 'Load Balancer': 0.8}
        risk = max(risk, critical_roles.get(role, 0.3))
        
        # Visibility gap
        no_visibility = visibility_probs[0]
        risk += no_visibility * 0.3
        
        return min(risk, 1.0)
    
    def get_risk_level(self, risk_score: float) -> str:
        """Get risk level"""
        if risk_score >= 0.8:
            return 'CRITICAL'
        elif risk_score >= 0.6:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def run_comprehensive_analysis(self):
        """Run complete analysis automatically"""
        print("\n" + "="*80)
        print("COMPREHENSIVE MISSING ASSET DISCOVERY")
        print("="*80)
        
        start_time = datetime.now()
        
        # Load or train models
        self.train_or_load_models()
        if not self.trained:
            print("❌ Cannot proceed without trained models")
            return
        
        # Load CMDB data
        df = self.get_cmdb_data()
        if df.empty:
            print("❌ No CMDB data available")
            return
        
        existing_hostnames = set(df['host'].dropna().str.lower())
        print(f"📝 Existing hosts: {len(existing_hostnames):,}")
        
        # Discover patterns
        patterns = self.discover_all_patterns(df)
        
        # Generate candidates
        candidates = self.generate_all_candidates(patterns, existing_hostnames)
        
        # Analyze with AI
        predictions = self.analyze_all_candidates(candidates)
        
        # Display results
        self.display_comprehensive_results(predictions)
        
        # Export results
        self.export_results(predictions)
        
        total_time = (datetime.now() - start_time).total_seconds()
        print(f"\n⏱️  Total analysis time: {total_time:.1f} seconds")
        print("="*80)
    
    def display_comprehensive_results(self, predictions: List[Dict]):
        """Display all results grouped by confidence and risk"""
        if not predictions:
            print("\n❌ No missing assets found")
            return
        
        print("\n" + "="*120)
        print("MISSING ASSETS REPORT")
        print("="*120)
        
        # Group by confidence level
        by_confidence = defaultdict(list)
        for asset in predictions:
            by_confidence[asset['confidence_level']].append(asset)
        
        # Display each confidence level
        for level in ['critical', 'high', 'medium', 'low', 'experimental']:
            if level in by_confidence:
                assets = by_confidence[level]
                
                # Further group by risk
                by_risk = defaultdict(list)
                for asset in assets:
                    by_risk[asset['risk_level']].append(asset)
                
                print(f"\n{'='*120}")
                print(f"{level.upper()} CONFIDENCE ({len(assets):,} assets)")
                print(f"{'='*120}")
                
                for risk_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    if risk_level in by_risk:
                        risk_assets = by_risk[risk_level][:20]  # Top 20 per category
                        
                        print(f"\n{risk_level} RISK ({len(by_risk[risk_level]):,} total):")
                        print("-"*120)
                        
                        for asset in risk_assets:
                            print(f"  {asset['hostname']:<50} "
                                  f"Conf: {asset['confidence_score']:.1%} "
                                  f"Risk: {asset['risk_score']:.2f} "
                                  f"Role: {asset['predicted_role']:<15}")
        
        # Summary statistics
        print("\n" + "="*120)
        print("SUMMARY")
        print("="*120)
        
        total = len(predictions)
        critical_conf = len(by_confidence.get('critical', []))
        high_conf = len(by_confidence.get('high', []))
        medium_conf = len(by_confidence.get('medium', []))
        
        critical_risk = len([a for a in predictions if a['risk_level'] == 'CRITICAL'])
        high_risk = len([a for a in predictions if a['risk_level'] == 'HIGH'])
        
        print(f"Total missing assets: {total:,}")
        print(f"\nBy Confidence:")
        print(f"  Critical: {critical_conf:,}")
        print(f"  High: {high_conf:,}")
        print(f"  Medium: {medium_conf:,}")
        print(f"\nBy Risk:")
        print(f"  Critical: {critical_risk:,}")
        print(f"  High: {high_risk:,}")
        
        # Role distribution
        role_dist = Counter(a['predicted_role'] for a in predictions)
        print(f"\nTop Asset Types:")
        for role, count in role_dist.most_common(10):
            print(f"  {role}: {count:,}")
    
    def export_results(self, predictions: List[Dict]):
        """Export results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON export
        json_file = f"reports/missing_assets_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_assets': len(predictions),
                'predictions': predictions
            }, f, indent=2, default=str)
        
        # CSV export
        csv_file = f"reports/missing_assets_{timestamp}.csv"
        pd.DataFrame(predictions).to_csv(csv_file, index=False)
        
        print(f"\n💾 Results exported:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")

def main():
    """Main execution - runs everything automatically"""
    print("\n" + "="*80)
    print("   AI ASSET PREDICTOR - FULLY AUTOMATED")
    print("="*80)
    print(f"Device: {device}")
    print("="*80)
    
    try:
        predictor = ComprehensiveAssetPredictor()
        predictor.run_comprehensive_analysis()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()