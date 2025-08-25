# /src/ml/ao1_missing_asset_predictor.py
# AO1 Missing Asset Discovery - AI-Powered Asset Gap Detection

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import re
import duckdb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from flask import Flask, jsonify
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
    print("🚀 AO1 Missing Asset Discovery - Using Apple Silicon GPU")
else:
    print("❌ ERROR: GPU required for AO1 Missing Asset Discovery")
    exit(1)

class HostnamePatternNet(nn.Module):
    """Neural network that learns hostname patterns and predicts missing assets"""
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
        
        # Existence predictor - does this hostname pattern exist?
        self.existence_predictor = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(), 
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        # Logging predictor - is this asset being logged?
        self.logging_predictor = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 6),  # Splunk, GSO, Chronicle, EDR, Tanium, CMDB
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
        
        # Pattern discovery settings
        self.min_pattern_frequency = 3  # Need at least 3 hosts to establish pattern
        self.max_gap_size = 1000       # Don't check beyond 1000 missing numbers
        self.confidence_threshold = 0.85  # 85% confidence required
        
        os.makedirs(self.model_dir, exist_ok=True)
        print("🔍 AO1 Missing Asset Discovery System Initialized")
        
    def get_db_connection(self):
        try:
            return duckdb.connect(self.db_path)
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None

    def extract_hostname_patterns(self, hostname: str) -> Dict:
        """Extract detailed hostname pattern features"""
        if not hostname:
            hostname = ""
        
        hostname = str(hostname).lower().strip()
        
        # Basic structure analysis
        features = {
            'length': len(hostname),
            'dots': hostname.count('.'),
            'dashes': hostname.count('-'),
            'underscores': hostname.count('_'),
            'digits': len(re.findall(r'\d', hostname)),
            'letters': len(re.findall(r'[a-z]', hostname))
        }
        
        # Extract number patterns
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
        
        # Pattern template (replace numbers with XXX)
        features['pattern_template'] = re.sub(r'\d+', 'XXX', hostname)
        
        # Domain/suffix analysis
        parts = hostname.split('.')
        features['subdomain_count'] = len(parts) - 1 if len(parts) > 1 else 0
        features['tld'] = parts[-1] if len(parts) > 1 else ''
        
        # Environment indicators
        env_indicators = ['prod', 'dev', 'test', 'stage', 'uat', 'qa']
        features['environment'] = next((env for env in env_indicators if env in hostname), 'unknown')
        
        # Infrastructure indicators
        infra_types = ['srv', 'server', 'web', 'app', 'db', 'fw', 'lb', 'proxy']
        features['infra_type'] = next((infra for infra in infra_types if infra in hostname), 'unknown')
        
        return features

    def discover_hostname_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Discover hostname patterns and identify sequence gaps"""
        print("🔍 Discovering hostname patterns...")
        
        # Group hostnames by pattern template
        pattern_groups = defaultdict(list)
        
        for hostname in df['host'].dropna():
            hostname = str(hostname).lower().strip()
            if hostname and re.search(r'\d', hostname):  # Only hostnames with numbers
                pattern_template = re.sub(r'\d+', 'XXX', hostname)
                
                # Extract numbers and their positions
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
        
        # Find patterns with sufficient frequency
        discovered_patterns = []
        
        for template, hostnames in pattern_groups.items():
            if len(hostnames) >= self.min_pattern_frequency:
                print(f"   Pattern: {template} ({len(hostnames)} hosts)")
                
                # Analyze number sequences for each number position
                number_sequences = defaultdict(list)
                
                for host_data in hostnames:
                    for i, num_data in enumerate(host_data['numbers']):
                        number_sequences[i].append(num_data['value'])
                
                # Find gaps in sequences
                pattern_info = {
                    'template': template,
                    'host_count': len(hostnames),
                    'sample_hosts': [h['hostname'] for h in hostnames[:5]],
                    'number_sequences': {},
                    'potential_gaps': []
                }
                
                for pos, values in number_sequences.items():
                    values = sorted(set(values))
                    if len(values) > 2:  # Need at least 3 different values
                        min_val, max_val = min(values), max(values)
                        
                        # Find missing numbers in range
                        missing = []
                        for i in range(min_val, min(max_val + 1, min_val + self.max_gap_size)):
                            if i not in values:
                                missing.append(i)
                        
                        pattern_info['number_sequences'][pos] = {
                            'existing_values': values,
                            'range': (min_val, max_val),
                            'missing_values': missing[:100],  # Limit missing values
                            'density': len(values) / (max_val - min_val + 1) if max_val > min_val else 1.0
                        }
                
                if pattern_info['number_sequences']:
                    discovered_patterns.append(pattern_info)
        
        print(f"✅ Discovered {len(discovered_patterns)} viable hostname patterns")
        return discovered_patterns

    def generate_missing_hostnames(self, patterns: List[Dict]) -> List[Dict]:
        """Generate potential missing hostnames based on discovered patterns"""
        print("🎯 Generating potential missing hostnames...")
        
        missing_candidates = []
        
        for pattern in patterns:
            template = pattern['template']
            
            # Generate combinations of missing numbers
            if len(pattern['number_sequences']) == 1:
                # Single number sequence
                pos = list(pattern['number_sequences'].keys())[0]
                seq_info = pattern['number_sequences'][pos]
                
                for missing_num in seq_info['missing_values'][:50]:  # Limit candidates
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
                # Two number sequences - generate combinations
                positions = list(pattern['number_sequences'].keys())
                seq1 = pattern['number_sequences'][positions[0]]
                seq2 = pattern['number_sequences'][positions[1]]
                
                # Limit combinations to prevent explosion
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
        
        print(f"🎲 Generated {len(missing_candidates)} missing hostname candidates")
        return missing_candidates

    def extract_features_for_hostname(self, hostname: str) -> np.ndarray:
        """Extract features for a hostname to feed into neural network"""
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
            pattern_data['max_number'] / 10000.0,  # Normalize large numbers
            pattern_data['min_number'] / 1000.0,   # Normalize
            pattern_data['subdomain_count'],
        ]
        
        # Environment one-hot encoding
        envs = ['prod', 'dev', 'test', 'stage', 'uat', 'qa', 'unknown']
        for env in envs:
            features.append(1 if pattern_data['environment'] == env else 0)
        
        # Infrastructure type one-hot encoding
        infra_types = ['srv', 'server', 'web', 'app', 'db', 'fw', 'lb', 'proxy', 'unknown']
        for infra in infra_types:
            features.append(1 if pattern_data['infra_type'] == infra else 0)
        
        # TLD encoding (top common ones)
        common_tlds = ['com', 'local', 'net', 'org', 'unknown']
        for tld in common_tlds:
            features.append(1 if pattern_data['tld'] == tld else 0)
        
        return np.array(features, dtype=np.float32)

    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training data from existing assets"""
        print(f"🔄 Preparing training data from {len(df)} assets...")
        
        features = []
        existence_labels = []
        logging_labels = []
        
        for idx, row in df.iterrows():
            if idx % 50000 == 0 and idx > 0:
                print(f"   Processed {idx:,} assets...")
            
            hostname = row['host']
            if pd.notna(hostname) and hostname.strip():
                # Extract features
                host_features = self.extract_features_for_hostname(hostname)
                features.append(host_features)
                
                # Existence label (1.0 since it exists in CMDB)
                existence_labels.append(1.0)
                
                # Logging labels (6 platforms: Splunk, GSO, Chronicle, EDR, Tanium, CMDB)
                logging = [
                    1.0 if row.get('logging_in_splunk') == 'yes' else 0.0,
                    1.0 if row.get('logging_in_gso') == 'yes' else 0.0,
                    0.8 if (row.get('logging_in_splunk') == 'yes' and row.get('logging_in_gso') == 'yes') else 0.0,  # Chronicle
                    1.0 if 'crowdstrike' in str(row.get('edr_coverage', '')).lower() else 0.0,
                    1.0 if row.get('tanium_coverage') == 'yes' else 0.0,
                    1.0 if row.get('present_in_cmdb') == 'yes' else 0.0
                ]
                logging_labels.append(logging)
        
        print(f"✅ Prepared {len(features):,} training samples")
        return (np.array(features, dtype=np.float32), 
                np.array(existence_labels, dtype=np.float32),
                np.array(logging_labels, dtype=np.float32))

    def train_missing_asset_model(self):
        """Train the missing asset discovery model"""
        print("🚀 Training AO1 Missing Asset Discovery Model...")
        
        # Load data
        conn = self.get_db_connection()
        if not conn:
            return
        
        df = conn.execute("SELECT * FROM universal_cmdb LIMIT 300000").df()
        conn.close()
        
        if df.empty:
            print("❌ No data available!")
            return
        
        print(f"📊 Loaded {len(df):,} assets from CMDB")
        
        # Prepare training data
        X, existence_y, logging_y = self.prepare_training_data(df)
        
        if len(X) == 0:
            print("❌ No features extracted!")
            return
        
        # Train/validation split
        X_train, X_val, exist_y_train, exist_y_val, log_y_train, log_y_val = train_test_split(
            X, existence_y, logging_y, test_size=0.15, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        # Initialize model
        input_size = X_train_scaled.shape[1]
        self.model = HostnamePatternNet(input_size).to(device)
        
        optimizer = optim.AdamW(self.model.parameters(), lr=0.001, weight_decay=1e-4)
        existence_criterion = nn.BCELoss()
        logging_criterion = nn.BCELoss()
        
        batch_size = 4096
        epochs = 100
        
        print(f"🔥 Training model: {len(X_train_scaled):,} samples, {epochs} epochs")
        
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
                
                total_loss_batch = loss_exist + 2.0 * loss_log  # Weight logging prediction more
                total_loss_batch.backward()
                
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                
                total_loss += total_loss_batch.item()
                
                del X_batch, exist_batch, log_batch
            
            if epoch % 20 == 0:
                avg_loss = total_loss / (len(X_train_scaled) / batch_size)
                print(f"🎯 Epoch {epoch}/{epochs}, Loss: {avg_loss:.4f}")
                gc.collect()
        
        self.trained = True
        self.save_models()
        print("✅ Missing Asset Discovery model training completed!")

    def save_models(self):
        try:
            torch.save(self.model.state_dict(), f'{self.model_dir}/missing_asset_model.pth')
            with open(f'{self.model_dir}/missing_asset_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            print("💾 Models saved successfully!")
        except Exception as e:
            print(f"❌ Error saving models: {e}")

    def load_models(self):
        try:
            if not (os.path.exists(f'{self.model_dir}/missing_asset_model.pth') and 
                    os.path.exists(f'{self.model_dir}/missing_asset_scaler.pkl')):
                return False
            
            # Determine input size from sample
            sample_features = self.extract_features_for_hostname("sample-host-01.example.com")
            input_size = len(sample_features)
            
            self.model = HostnamePatternNet(input_size).to(device)
            self.model.load_state_dict(torch.load(f'{self.model_dir}/missing_asset_model.pth', map_location=device))
            
            with open(f'{self.model_dir}/missing_asset_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            
            self.trained = True
            print("✅ Missing asset models loaded!")
            return True
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False

    def discover_missing_assets(self, limit: int = 1000) -> List[Dict]:
        """Main function to discover missing assets"""
        if not self.trained:
            if not self.load_models():
                print("❌ Models not trained! Training now...")
                self.train_missing_asset_model()
        
        print("🔍 Discovering Missing Assets...")
        
        # Load existing assets
        conn = self.get_db_connection()
        if not conn:
            return []
        
        df = conn.execute("SELECT host FROM universal_cmdb WHERE host IS NOT NULL").df()
        conn.close()
        
        existing_hosts = set(df['host'].str.lower())
        print(f"📊 Found {len(existing_hosts):,} existing hosts")
        
        # Discover patterns
        patterns = self.discover_hostname_patterns(df)
        
        # Generate missing hostname candidates
        candidates = self.generate_missing_hostnames(patterns)
        
        # Filter out existing hosts
        new_candidates = [c for c in candidates if c['hostname'] not in existing_hosts]
        print(f"🎯 {len(new_candidates):,} potential missing assets identified")
        
        # Predict existence and logging for candidates
        missing_assets = []
        self.model.eval()
        
        print("🤖 AI analyzing missing asset candidates...")
        
        with torch.no_grad():
            for i, candidate in enumerate(new_candidates[:limit * 3]):  # Process more to get top results
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
        
        # Sort by existence confidence
        missing_assets.sort(key=lambda x: float(x['existence_confidence'].rstrip('%')), reverse=True)
        
        result = missing_assets[:limit]
        print(f"✅ Identified {len(result)} high-confidence missing assets!")
        
        return result

    def get_remediation_actions(self, hostname: str, logging_scores: np.ndarray) -> List[str]:
        """Generate specific remediation actions for missing assets"""
        actions = [f"Verify if {hostname} actually exists in your environment"]
        
        # Check which logging platforms are unlikely
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

# Flask Application
app = Flask(__name__)
discovery_system = AO1MissingAssetDiscovery()

@app.route('/api/ao1/train-discovery')
def train_discovery():
    try:
        def train_async():
            discovery_system.train_missing_asset_model()
        
        threading.Thread(target=train_async, daemon=True).start()
        return jsonify({
            'status': 'training_started',
            'message': 'AO1 Missing Asset Discovery training initiated',
            'version': discovery_system.model_version
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    print("🔍 Starting AO1 Missing Asset Discovery System...")
    
    if discovery_system.load_models():
        print("✅ AO1 Discovery System Ready!")
    else:
        print("⚠️  Models not ready. Use /api/ao1/train-discovery to train.")
    
    app.run(debug=True, port=5001, host='0.0.0.0')