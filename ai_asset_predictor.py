# /src/ml/ao1_missing_asset_discovery.py

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import re
import duckdb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from flask import Flask, jsonify, request
import threading
from datetime import datetime
import os
import pickle
import gc
from typing import List, Dict, Optional, Tuple, Set
from collections import Counter, defaultdict
import itertools

if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("AO1 Missing Asset Discovery - Using Apple Silicon GPU")
else:
    print("ERROR: GPU required for AO1 Missing Asset Discovery")
    exit(1)

class HostnamePatternNet(nn.Module):
    def __init__(self, input_size: int):
        super().__init__()
        self.pattern_encoder = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU()
        )
        
        self.existence_predictor = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(), 
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        self.logging_predictor = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 6),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        encoded = self.pattern_encoder(x)
        existence_prob = self.existence_predictor(encoded)
        logging_probs = self.logging_predictor(encoded)
        return existence_prob, logging_probs

class AO1MissingAssetDiscovery:
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        self.model = None
        self.feature_scaler = StandardScaler()
        self.trained = False
        self.db_path = db_path
        self.model_version = "AO1-Asset-Discovery-2025.1"
        self.model_dir = 'models'
        
        self.min_pattern_frequency = 3
        self.max_gap_size = 1000
        self.confidence_threshold = 0.85
        
        os.makedirs(self.model_dir, exist_ok=True)
        print("AO1 Missing Asset Discovery System Initialized")
        
        # Auto-initialize on startup
        self.initialize_system()
        
    def get_db_connection(self):
        try:
            return duckdb.connect(self.db_path)
        except Exception as e:
            print(f"Database connection error: {e}")
            return None

    def extract_hostname_patterns(self, hostname: str) -> Dict:
        if not hostname:
            hostname = ""
        
        hostname = str(hostname).lower().strip()
        
        features = {
            'length': len(hostname),
            'dots': hostname.count('.'),
            'dashes': hostname.count('-'),
            'underscores': hostname.count('_'),
            'digits': len(re.findall(r'\d', hostname)),
            'letters': len(re.findall(r'[a-z]', hostname))
        }
        
        numbers = re.findall(r'\d+', hostname)
        if numbers:
            features['has_numbers'] = 1
            features['num_count'] = len(numbers)
            features['max_number'] = max([int(n) for n in numbers])
            features['min_number'] = min([int(n) for n in numbers])
            features['number_positions'] = [hostname.find(n) for n in numbers]
        else:
            features['has_numbers'] = 0
            features['num_count'] = 0
            features['max_number'] = 0
            features['min_number'] = 0
            features['number_positions'] = []
        
        features['pattern_template'] = re.sub(r'\d+', 'XXX', hostname)
        
        parts = hostname.split('.')
        features['subdomain_count'] = len(parts) - 1 if len(parts) > 1 else 0
        features['tld'] = parts[-1] if len(parts) > 1 else ''
        
        env_indicators = ['prod', 'dev', 'test', 'stage', 'uat', 'qa']
        features['environment'] = next((env for env in env_indicators if env in hostname), 'unknown')
        
        infra_types = ['srv', 'server', 'web', 'app', 'db', 'fw', 'lb', 'proxy']
        features['infra_type'] = next((infra for infra in infra_types if infra in hostname), 'unknown')
        
        return features

    def discover_hostname_patterns(self, df: pd.DataFrame) -> List[Dict]:
        print("Discovering hostname patterns...")
        
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
                        'original': match.group()
                    })
                
                pattern_groups[pattern_template].append({
                    'hostname': hostname,
                    'template': pattern_template,
                    'numbers': numbers
                })
        
        discovered_patterns = []
        
        for template, hostnames in pattern_groups.items():
            if len(hostnames) >= self.min_pattern_frequency:
                print(f"   Pattern: {template} ({len(hostnames)} hosts)")
                
                number_sequences = defaultdict(list)
                
                for host_data in hostnames:
                    for i, num_data in enumerate(host_data['numbers']):
                        number_sequences[i].append(num_data['value'])
                
                pattern_info = {
                    'template': template,
                    'host_count': len(hostnames),
                    'sample_hosts': [h['hostname'] for h in hostnames[:5]],
                    'number_sequences': {},
                    'potential_gaps': []
                }
                
                for pos, values in number_sequences.items():
                    values = sorted(set(values))
                    if len(values) > 2:
                        min_val, max_val = min(values), max(values)
                        
                        missing = []
                        for i in range(min_val, min(max_val + 1, min_val + self.max_gap_size)):
                            if i not in values:
                                missing.append(i)
                        
                        pattern_info['number_sequences'][pos] = {
                            'existing_values': values,
                            'range': (min_val, max_val),
                            'missing_values': missing[:100],
                            'density': len(values) / (max_val - min_val + 1) if max_val > min_val else 1.0
                        }
                
                if pattern_info['number_sequences']:
                    discovered_patterns.append(pattern_info)
        
        print(f"Discovered {len(discovered_patterns)} viable hostname patterns")
        return discovered_patterns

    def generate_missing_hostnames(self, patterns: List[Dict]) -> List[Dict]:
        print("Generating potential missing hostnames...")
        
        missing_candidates = []
        
        for pattern in patterns:
            template = pattern['template']
            
            if len(pattern['number_sequences']) == 1:
                pos = list(pattern['number_sequences'].keys())[0]
                seq_info = pattern['number_sequences'][pos]
                
                for missing_num in seq_info['missing_values'][:50]:
                    candidate_hostname = template.replace('XXX', str(missing_num), 1)
                    
                    missing_candidates.append({
                        'hostname': candidate_hostname,
                        'pattern_template': template,
                        'missing_numbers': [missing_num],
                        'pattern_density': seq_info['density'],
                        'existing_hosts_count': pattern['host_count'],
                        'sample_existing': pattern['sample_hosts'][:3]
                    })
            
            elif len(pattern['number_sequences']) == 2:
                positions = list(pattern['number_sequences'].keys())
                seq1 = pattern['number_sequences'][positions[0]]
                seq2 = pattern['number_sequences'][positions[1]]
                
                missing1 = seq1['missing_values'][:20]
                missing2 = seq2['missing_values'][:20] 
                
                for num1 in missing1:
                    for num2 in missing2:
                        candidate_hostname = template
                        replacements = [str(num1), str(num2)]
                        
                        for replacement in replacements:
                            candidate_hostname = candidate_hostname.replace('XXX', replacement, 1)
                        
                        missing_candidates.append({
                            'hostname': candidate_hostname,
                            'pattern_template': template,
                            'missing_numbers': [num1, num2],
                            'pattern_density': (seq1['density'] + seq2['density']) / 2,
                            'existing_hosts_count': pattern['host_count'],
                            'sample_existing': pattern['sample_hosts'][:3]
                        })
        
        print(f"Generated {len(missing_candidates)} missing hostname candidates")
        return missing_candidates

    def extract_features_for_hostname(self, hostname: str) -> np.ndarray:
        pattern_data = self.extract_hostname_patterns(hostname)
        
        features = [
            pattern_data['length'],
            pattern_data['dots'],
            pattern_data['dashes'],
            pattern_data['underscores'],
            pattern_data['digits'],
            pattern_data['letters'],
            pattern_data['has_numbers'],
            pattern_data['num_count'],
            pattern_data['max_number'] / 10000.0,
            pattern_data['min_number'] / 1000.0,
            pattern_data['subdomain_count'],
        ]
        
        envs = ['prod', 'dev', 'test', 'stage', 'uat', 'qa', 'unknown']
        for env in envs:
            features.append(1 if pattern_data['environment'] == env else 0)
        
        infra_types = ['srv', 'server', 'web', 'app', 'db', 'fw', 'lb', 'proxy', 'unknown']
        for infra in infra_types:
            features.append(1 if pattern_data['infra_type'] == infra else 0)
        
        common_tlds = ['com', 'local', 'net', 'org', 'unknown']
        for tld in common_tlds:
            features.append(1 if pattern_data['tld'] == tld else 0)
        
        return np.array(features, dtype=np.float32)

    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        print(f"Preparing training data from {len(df)} assets...")
        
        features = []
        existence_labels = []
        logging_labels = []
        
        for idx, row in df.iterrows():
            if idx % 50000 == 0 and idx > 0:
                print(f"   Processed {idx:,} assets...")
            
            hostname = row['host']
            if pd.notna(hostname) and hostname.strip():
                host_features = self.extract_features_for_hostname(hostname)
                features.append(host_features)
                
                existence_labels.append(1.0)
                
                logging = [
                    1.0 if row.get('logging_in_splunk') == 'yes' else 0.0,
                    1.0 if row.get('logging_in_gso') == 'yes' else 0.0,
                    0.8 if (row.get('logging_in_splunk') == 'yes' and row.get('logging_in_gso') == 'yes') else 0.0,
                    1.0 if 'crowdstrike' in str(row.get('edr_coverage', '')).lower() else 0.0,
                    1.0 if row.get('tanium_coverage') == 'yes' else 0.0,
                    1.0 if row.get('present_in_cmdb') == 'yes' else 0.0
                ]
                logging_labels.append(logging)
        
        print(f"Prepared {len(features):,} training samples")
        return (np.array(features, dtype=np.float32), 
                np.array(existence_labels, dtype=np.float32),
                np.array(logging_labels, dtype=np.float32))

    def train_missing_asset_model(self):
        print("Training AO1 Missing Asset Discovery Model...")
        
        conn = self.get_db_connection()
        if not conn:
            return
        
        df = conn.execute("SELECT * FROM universal_cmdb LIMIT 300000").df()
        conn.close()
        
        if df.empty:
            print("No data available!")
            return
        
        print(f"Loaded {len(df):,} assets from CMDB")
        
        X, existence_y, logging_y = self.prepare_training_data(df)
        
        if len(X) == 0:
            print("No features extracted!")
            return
        
        X_train, X_val, exist_y_train, exist_y_val, log_y_train, log_y_val = train_test_split(
            X, existence_y, logging_y, test_size=0.15, random_state=42
        )
        
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        input_size = X_train_scaled.shape[1]
        self.model = HostnamePatternNet(input_size).to(device)
        
        optimizer = optim.AdamW(self.model.parameters(), lr=0.001, weight_decay=1e-4)
        existence_criterion = nn.BCELoss()
        logging_criterion = nn.BCELoss()
        
        batch_size = 4096
        epochs = 100
        
        print(f"Training model: {len(X_train_scaled):,} samples, {epochs} epochs")
        
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0
            
            for i in range(0, len(X_train_scaled), batch_size):
                batch_end = min(i + batch_size, len(X_train_scaled))
                
                X_batch = torch.FloatTensor(X_train_scaled[i:batch_end]).to(device)
                exist_batch = torch.FloatTensor(exist_y_train[i:batch_end]).reshape(-1, 1).to(device)
                log_batch = torch.FloatTensor(log_y_train[i:batch_end]).to(device)
                
                optimizer.zero_grad()
                
                exist_pred, log_pred = self.model(X_batch)
                
                loss_exist = existence_criterion(exist_pred, exist_batch)
                loss_log = logging_criterion(log_pred, log_batch)
                
                total_loss_batch = loss_exist + 2.0 * loss_log
                total_loss_batch.backward()
                
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                
                total_loss += total_loss_batch.item()
                
                del X_batch, exist_batch, log_batch
            
            if epoch % 20 == 0:
                avg_loss = total_loss / (len(X_train_scaled) / batch_size)
                print(f"Epoch {epoch}/{epochs}, Loss: {avg_loss:.4f}")
                gc.collect()
        
        self.trained = True
        self.save_models()
        print("Missing Asset Discovery model training completed!")

    def save_models(self):
        try:
            torch.save(self.model.state_dict(), f'{self.model_dir}/missing_asset_model.pth')
            with open(f'{self.model_dir}/missing_asset_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            print("Models saved successfully!")
        except Exception as e:
            print(f"Error saving models: {e}")

    def load_models(self):
        try:
            if not (os.path.exists(f'{self.model_dir}/missing_asset_model.pth') and 
                    os.path.exists(f'{self.model_dir}/missing_asset_scaler.pkl')):
                return False
            
            sample_features = self.extract_features_for_hostname("sample-host-01.example.com")
            input_size = len(sample_features)
            
            self.model = HostnamePatternNet(input_size).to(device)
            self.model.load_state_dict(torch.load(f'{self.model_dir}/missing_asset_model.pth', map_location=device))
            
            with open(f'{self.model_dir}/missing_asset_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            
            self.trained = True
            print("Missing asset models loaded!")
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False

    def initialize_system(self):
        print("Initializing AO1 Missing Asset Discovery System...")
        
        if self.load_models():
            print("Existing models loaded successfully!")
        else:
            print("No existing models found. Training new models...")
            self.train_missing_asset_model()

    def discover_missing_assets(self, limit: int = 500) -> List[Dict]:
        if not self.trained:
            print("Models not trained! Training now...")
            self.train_missing_asset_model()
        
        print("Discovering Missing Assets...")
        
        conn = self.get_db_connection()
        if not conn:
            return []
        
        df = conn.execute("SELECT host FROM universal_cmdb WHERE host IS NOT NULL").df()
        conn.close()
        
        existing_hosts = set(df['host'].str.lower())
        print(f"Found {len(existing_hosts):,} existing hosts")
        
        patterns = self.discover_hostname_patterns(df)
        
        candidates = self.generate_missing_hostnames(patterns)
        
        new_candidates = [c for c in candidates if c['hostname'] not in existing_hosts]
        print(f"{len(new_candidates):,} potential missing assets identified")
        
        missing_assets = []
        self.model.eval()
        
        print("AI analyzing missing asset candidates...")
        
        with torch.no_grad():
            for i, candidate in enumerate(new_candidates[:limit * 3]):
                if i % 1000 == 0 and i > 0:
                    print(f"   Analyzed {i:,} candidates...")
                
                features = self.extract_features_for_hostname(candidate['hostname'])
                features_scaled = self.feature_scaler.transform([features])
                features_tensor = torch.FloatTensor(features_scaled).to(device)
                
                existence_prob, logging_probs = self.model(features_tensor)
                
                existence_confidence = existence_prob.cpu().item()
                logging_scores = logging_probs.cpu().numpy()[0]
                
                if existence_confidence >= self.confidence_threshold:
                    missing_assets.append({
                        'hostname': candidate['hostname'],
                        'existence_confidence': f"{existence_confidence:.1%}",
                        'pattern_template': candidate['pattern_template'],
                        'similar_existing_hosts': candidate['sample_existing'],
                        'pattern_density': f"{candidate['pattern_density']:.1%}",
                        'existing_pattern_count': candidate['existing_hosts_count'],
                        'logging_predictions': {
                            'splunk_likely': f"{logging_scores[0]:.1%}",
                            'gso_likely': f"{logging_scores[1]:.1%}",
                            'chronicle_likely': f"{logging_scores[2]:.1%}",
                            'edr_likely': f"{logging_scores[3]:.1%}",
                            'tanium_likely': f"{logging_scores[4]:.1%}",
                            'cmdb_likely': f"{logging_scores[5]:.1%}"
                        },
                        'visibility_gap_risk': f"{1.0 - np.mean(logging_scores):.1%}",
                        'recommended_actions': self.get_remediation_actions(candidate['hostname'], logging_scores)
                    })
        
        missing_assets.sort(key=lambda x: float(x['existence_confidence'].rstrip('%')), reverse=True)
        
        result = missing_assets[:limit]
        print(f"Identified {len(result)} high-confidence missing assets!")
        
        return result

    def get_remediation_actions(self, hostname: str, logging_scores: np.ndarray) -> List[str]:
        actions = [f"Verify if {hostname} actually exists in your environment"]
        
        platform_names = ['Splunk', 'GSO', 'Chronicle', 'EDR', 'Tanium', 'CMDB']
        
        for i, (platform, score) in enumerate(zip(platform_names, logging_scores)):
            if score < 0.5:
                if platform == 'Splunk':
                    actions.append(f"Configure log forwarding to Splunk for {hostname}")
                elif platform == 'GSO':
                    actions.append(f"Enable GSO logging collection for {hostname}")
                elif platform == 'EDR':
                    actions.append(f"Deploy EDR agent on {hostname}")
                elif platform == 'CMDB':
                    actions.append(f"Add {hostname} to CMDB inventory")
        
        return actions

    def generate_executive_report(self) -> Dict:
        print("Generating Executive Missing Asset Report...")
        
        missing_assets = self.discover_missing_assets(limit=200)
        
        if not missing_assets:
            return {
                'error': 'No missing assets discovered',
                'total_missing_assets': 0
            }
        
        high_confidence = [a for a in missing_assets if float(a['existence_confidence'].rstrip('%')) > 90]
        high_risk = [a for a in missing_assets if float(a['visibility_gap_risk'].rstrip('%')) > 70]
        
        pattern_analysis = defaultdict(int)
        for asset in missing_assets:
            pattern_analysis[asset['pattern_template']] += 1
        
        top_patterns = sorted(pattern_analysis.items(), key=lambda x: x[1], reverse=True)[:10]
        
        report = {
            'executive_summary': {
                'total_missing_assets_discovered': len(missing_assets),
                'high_confidence_assets': len(high_confidence),
                'high_risk_visibility_gaps': len(high_risk),
                'top_missing_patterns': [{'pattern': p[0], 'missing_count': p[1]} for p in top_patterns[:5]],
                'generated_timestamp': datetime.now().isoformat()
            },
            'detailed_findings': missing_assets[:50],
            'pattern_analysis': {
                'total_patterns_analyzed': len(pattern_analysis),
                'pattern_breakdown': [{'pattern': p[0], 'missing_assets': p[1]} for p in top_patterns]
            },
            'remediation_summary': {
                'immediate_verification_needed': len([a for a in missing_assets if float(a['existence_confidence'].rstrip('%')) > 95]),
                'splunk_integration_needed': len([a for a in missing_assets if float(a['logging_predictions']['splunk_likely'].rstrip('%')) < 50]),
                'edr_deployment_needed': len([a for a in missing_assets if float(a['logging_predictions']['edr_likely'].rstrip('%')) < 50])
            }
        }
        
        print("Executive report generated successfully!")
        return report

app = Flask(__name__)
discovery_system = AO1MissingAssetDiscovery()

@app.route('/api/ao1/discover-missing-assets')
def discover_missing_assets():
    try:
        limit = int(request.args.get('limit', 100))
        missing_assets = discovery_system.discover_missing_assets(limit=limit)
        
        return jsonify({
            'total_missing_assets_found': len(missing_assets),
            'confidence_threshold': f"{discovery_system.confidence_threshold:.0%}",
            'missing_assets': missing_assets,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ao1/executive-report')
def executive_report():
    try:
        report = discovery_system.generate_executive_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ao1/discovery-status')
def discovery_status():
    return jsonify({
        'system': 'AO1 Missing Asset Discovery',
        'version': discovery_system.model_version,
        'trained': discovery_system.trained,
        'confidence_threshold': discovery_system.confidence_threshold,
        'max_gap_size': discovery_system.max_gap_size,
        'device': str(device)
    })

if __name__ == '__main__':
    print("Starting AO1 Missing Asset Discovery System...")
    print("System initialized and ready!")
    
    app.run(debug=True, port=5001, host='0.0.0.0')