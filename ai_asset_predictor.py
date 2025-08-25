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
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict

# Device configuration - support for GPU acceleration
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("Using NVIDIA GPU (CUDA)")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using Apple Silicon GPU (MPS)")
else:
    device = torch.device("cpu")
    print("Using CPU - Training will be slower")

class HostnamePatternNet(nn.Module):
    """Neural network for predicting asset existence based on hostname patterns"""
    def __init__(self, input_size: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        return self.layers(x)

class LogVisibilityPredictor(nn.Module):
    """Neural network for predicting logging visibility across different systems"""
    def __init__(self, input_size: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
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

class AIAssetPredictor:
    """
    AI-powered missing IT asset discovery system using ML pattern recognition.
    Combines neural networks, pattern mining, and anomaly detection.
    """
    
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        self.hostname_net = None
        self.log_visibility_net = None
        self.feature_scaler = StandardScaler()
        self.trained = False
        self.db_path = db_path
        self.model_version = "AI-Asset-Predictor-2025.1"
        self.training_metrics = {}
        self.model_dir = 'models'
        
        # Pattern discovery configuration
        self.min_pattern_frequency = 3
        self.max_gap_size = 1000
        self.confidence_threshold = 0.75
        
        # Create model directory
        os.makedirs(self.model_dir, exist_ok=True)
        
    @property
    def models_exist(self) -> bool:
        """Check if trained models exist on disk"""
        required_files = [
            f'{self.model_dir}/hostname_net.pth',
            f'{self.model_dir}/log_visibility_net.pth', 
            f'{self.model_dir}/feature_scaler.pkl'
        ]
        return all(os.path.exists(f) for f in required_files)

    def initialize_models(self):
        """Initialize models - load existing or train new ones"""
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
        """Get DuckDB connection"""
        try:
            return duckdb.connect(self.db_path)
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def extract_hostname_features(self, hostname: str) -> np.ndarray:
        """Extract ML features from hostname string"""
        if not hostname:
            return np.zeros(35)
        
        hostname = hostname.lower().strip()
        
        # Basic string features
        features = [
            len(hostname),
            hostname.count('.'),
            hostname.count('-'),
            hostname.count('_'),
            len(re.findall(r'\d', hostname)),
            len(re.findall(r'[a-z]', hostname))
        ]
        
        # Keyword-based features for common infrastructure patterns
        keywords = [
            ['srv', 'server'], ['web', 'www'], ['db', 'database', 'sql'], 
            ['app', 'application'], ['dc', 'datacenter'], ['prod', 'production'],
            ['dev', 'development'], ['test', 'testing'], ['stage', 'staging'],
            ['uat', 'preprod'], ['.com'], ['.local'], ['.net'],
            ['1dc'], ['fead'], ['fiserv'], ['firewall', 'fw'], 
            ['ids', 'ips'], ['ndr', 'detection'], ['proxy', 'px'],
            ['dns', 'domain'], ['waf', 'gateway'], ['north', 'south', 'east', 'west'],
            ['us', 'usa', 'america'], ['eu', 'emea', 'europe'], 
            ['apac', 'asia'], ['vm', 'virtual'], ['docker', 'container'],
            ['aws', 'azure', 'gcp', 'cloud']
        ]
        
        for keyword_group in keywords:
            features.append(1 if any(kw in hostname for kw in keyword_group) else 0)
        
        return np.array(features[:35])
    
    def get_cmdb_data(self) -> pd.DataFrame:
        """Fetch CMDB data from database"""
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

    def discover_hostname_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Discover sequential patterns in hostnames for gap detection"""
        print("Discovering hostname patterns...")
        
        pattern_groups = defaultdict(list)
        
        # Group hostnames by pattern template
        for hostname in df['host'].dropna():
            hostname = str(hostname).lower().strip()
            if hostname and re.search(r'\d', hostname):
                # Replace numbers with placeholder
                pattern_template = re.sub(r'\d+', 'XXX', hostname)
                
                # Extract number positions and values
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
        
        # Analyze patterns with sufficient frequency
        for template, hostnames in pattern_groups.items():
            if len(hostnames) >= self.min_pattern_frequency:
                print(f"   Pattern: {template} ({len(hostnames)} hosts)")
                
                # Analyze number sequences at each position
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
                
                # Find gaps in number sequences
                for pos, values in number_sequences.items():
                    values = sorted(set(values))
                    if len(values) > 2:
                        min_val, max_val = min(values), max(values)
                        
                        # Identify missing values in sequence
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
        """Generate potential missing hostnames based on discovered patterns"""
        print("Generating potential missing hostnames...")
        
        missing_candidates = []
        
        for pattern in patterns:
            template = pattern['template']
            
            # Handle single number sequence patterns
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
            
            # Handle dual number sequence patterns
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
    
    def prepare_training_data(self, df: pd.DataFrame) -> tuple:
        """Prepare features and labels for model training"""
        features, existence_labels, visibility_labels = [], [], []
        
        print(f"Processing {len(df)} records...")
        
        for idx, row in df.iterrows():
            if idx % 50000 == 0:
                print(f"Processed {idx} records...")
                
            # Extract hostname features
            hostname_features = self.extract_hostname_features(row['host']) if pd.notna(row['host']) else self.extract_hostname_features("")
            
            # Additional context features
            additional_features = [
                1 if pd.notna(row['business_unit']) else 0,
                1 if pd.notna(row['region']) else 0,
                1 if pd.notna(row['system_classification']) and 'server' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['system_classification']) and 'windows' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['system_classification']) and 'linux' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['infrastructure_type']) and 'cloud' in str(row['infrastructure_type']).lower() else 0,
                float(row['data_quality_score']) if pd.notna(row['data_quality_score']) else 0.0,
                int(row['source_count']) if pd.notna(row['source_count']) else 0,
                1 if pd.notna(row['cio']) else 0
            ]
            
            combined_features = np.concatenate([hostname_features, additional_features])
            features.append(combined_features)
            
            # Calculate existence score
            existence_score = min(sum([
                1 if pd.notna(row['logging_in_splunk']) and row['logging_in_splunk'] == 'yes' else 0,
                1 if pd.notna(row['present_in_cmdb']) and row['present_in_cmdb'] == 'yes' else 0,
                1 if pd.notna(row['edr_coverage']) and 'crowdstrike' in str(row['edr_coverage']).lower() else 0
            ]) / 3.0, 1.0)
            
            existence_labels.append(existence_score)
            
            # Determine visibility level
            visibility_type = 0
            if (pd.notna(row['logging_in_splunk']) and row['logging_in_splunk'] == 'yes' and 
                pd.notna(row['logging_in_gso']) and row['logging_in_gso'] == 'yes'):
                visibility_type = 4  # Full visibility
            elif pd.notna(row['logging_in_splunk']) and row['logging_in_splunk'] == 'yes':
                visibility_type = 3  # Splunk only
            elif pd.notna(row['logging_in_gso']) and row['logging_in_gso'] == 'yes':
                visibility_type = 2  # GSO only
            elif pd.notna(row['present_in_cmdb']) and row['present_in_cmdb'] == 'yes':
                visibility_type = 1  # CMDB only
            
            visibility_labels.append(visibility_type)
        
        print(f"Finished processing. Features: {len(features)}, Existence: {len(existence_labels)}, Visibility: {len(visibility_labels)}")
        return np.array(features), np.array(existence_labels), np.array(visibility_labels)
    
    def train_models(self):
        """Train neural networks for asset prediction"""
        print("Loading CMDB data...")
        df = self.get_cmdb_data()
        
        if df.empty:
            print("No data available for training!")
            return
        
        print(f"Preparing training data from {len(df)} records...")
        try:
            X, existence_y, visibility_y = self.prepare_training_data(df)
        except ValueError as e:
            print(f"Error in prepare_training_data: {e}")
            return
        
        if len(X) == 0:
            print("No features extracted!")
            return
        
        # Split data
        X_train, X_val, existence_y_train, existence_y_val, visibility_y_train, visibility_y_val = train_test_split(
            X, existence_y, visibility_y, test_size=0.15, random_state=42
        )
        
        # Clean up memory
        del X, existence_y, visibility_y
        gc.collect()
        
        # Scale features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        # Initialize networks
        input_size = X_train_scaled.shape[1]
        self.hostname_net = HostnamePatternNet(input_size).to(device)
        self.log_visibility_net = LogVisibilityPredictor(input_size).to(device)
        
        # Optimizers
        optimizer1 = optim.AdamW(self.hostname_net.parameters(), lr=0.001, weight_decay=1e-4)
        optimizer2 = optim.AdamW(self.log_visibility_net.parameters(), lr=0.001, weight_decay=1e-4)
        
        # Loss functions
        criterion1 = nn.BCELoss()
        criterion2 = nn.CrossEntropyLoss()
        
        # Training configuration
        batch_size = 8192 if device.type != 'cpu' else 1024
        epochs = 150
        
        print(f"Training models on {device}...")
        print(f"Training: {len(X_train_scaled):,} samples, Validation: {len(X_val_scaled):,} samples")
        print(f"Batch size: {batch_size}, Epochs: {epochs}")
        
        for epoch in range(epochs):
            self.hostname_net.train()
            self.log_visibility_net.train()
            
            total_loss = 0.0
            
            # Training loop
            for i in range(0, len(X_train_scaled), batch_size):
                batch_end = min(i + batch_size, len(X_train_scaled))
                
                X_batch = torch.FloatTensor(X_train_scaled[i:batch_end]).to(device)
                existence_y_batch = torch.FloatTensor(existence_y_train[i:batch_end]).reshape(-1, 1).to(device)
                visibility_y_batch = torch.LongTensor(visibility_y_train[i:batch_end]).to(device)
                
                # Train existence predictor
                optimizer1.zero_grad()
                existence_outputs = self.hostname_net(X_batch)
                loss1 = criterion1(existence_outputs, existence_y_batch)
                loss1.backward()
                torch.nn.utils.clip_grad_norm_(self.hostname_net.parameters(), 1.0)
                optimizer1.step()
                
                # Train visibility predictor
                optimizer2.zero_grad()
                visibility_outputs = self.log_visibility_net(X_batch)
                loss2 = criterion2(visibility_outputs, visibility_y_batch)
                loss2.backward()
                torch.nn.utils.clip_grad_norm_(self.log_visibility_net.parameters(), 1.0)
                optimizer2.step()
                
                total_loss += loss1.item() + loss2.item()
                
                del X_batch, existence_y_batch, visibility_y_batch
                
                if i % (batch_size * 20) == 0:
                    gc.collect()
            
            # Validation every 25 epochs
            if epoch % 25 == 0:
                self.hostname_net.eval()
                self.log_visibility_net.eval()
                
                val_loss1_total, val_loss2_total = 0.0, 0.0
                val_batches = 0
                
                with torch.no_grad():
                    for i in range(0, len(X_val_scaled), batch_size):
                        batch_end = min(i + batch_size, len(X_val_scaled))
                        
                        X_val_batch = torch.FloatTensor(X_val_scaled[i:batch_end]).to(device)
                        existence_y_val_batch = torch.FloatTensor(existence_y_val[i:batch_end]).reshape(-1, 1).to(device)
                        visibility_y_val_batch = torch.LongTensor(visibility_y_val[i:batch_end]).to(device)
                        
                        val_existence_outputs = self.hostname_net(X_val_batch)
                        val_loss1 = criterion1(val_existence_outputs, existence_y_val_batch)
                        
                        val_visibility_outputs = self.log_visibility_net(X_val_batch)
                        val_loss2 = criterion2(val_visibility_outputs, visibility_y_val_batch)
                        
                        val_loss1_total += val_loss1.item()
                        val_loss2_total += val_loss2.item()
                        val_batches += 1
                        
                        del X_val_batch, existence_y_val_batch, visibility_y_val_batch
                
                avg_train_loss = total_loss / (len(X_train_scaled) / batch_size)
                avg_val_loss1 = val_loss1_total / val_batches
                avg_val_loss2 = val_loss2_total / val_batches
                
                print(f'Epoch {epoch}/{epochs}, Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss1:.4f}/{avg_val_loss2:.4f}')
                gc.collect()
        
        self.trained = True
        self.save_models()
        
        # Store training metrics
        self.training_metrics = {
            'final_losses': [avg_train_loss, avg_val_loss1, avg_val_loss2],
            'training_records': len(X_train_scaled),
            'validation_records': len(X_val_scaled),
            'epochs_trained': epochs,
            'device': str(device)
        }
        
        print(f"Training completed! Final train loss: {avg_train_loss:.4f}")
    
    def save_models(self):
        """Save trained models to disk"""
        try:
            torch.save(self.hostname_net.state_dict(), f'{self.model_dir}/hostname_net.pth')
            torch.save(self.log_visibility_net.state_dict(), f'{self.model_dir}/log_visibility_net.pth')
            with open(f'{self.model_dir}/feature_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            print("Models saved successfully!")
        except Exception as e:
            print(f"Error saving models: {e}")
    
    def load_models(self):
        """Load trained models from disk"""
        try:
            if not self.models_exist:
                return False
            
            # Determine input size
            sample_features = self.extract_hostname_features("sample-host-01.example.com")
            additional_features = [0] * 9
            input_size = len(np.concatenate([sample_features, additional_features]))
            
            # Initialize networks
            self.hostname_net = HostnamePatternNet(input_size).to(device)
            self.log_visibility_net = LogVisibilityPredictor(input_size).to(device)
            
            # Load state dicts
            self.hostname_net.load_state_dict(torch.load(f'{self.model_dir}/hostname_net.pth', map_location=device))
            self.log_visibility_net.load_state_dict(torch.load(f'{self.model_dir}/log_visibility_net.pth', map_location=device))
            
            # Load scaler
            with open(f'{self.model_dir}/feature_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            
            self.trained = True
            return True
            
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def predict_missing_assets(self, business_unit_filter: Optional[str] = None) -> List[Dict]:
        """Predict missing assets using trained models"""
        if not self.trained:
            print("Models not trained yet! Attempting to initialize...")
            self.initialize_models()
            if not self.trained:
                print("Unable to train models - no data available or training failed")
                return []
        
        print("Starting missing asset discovery...")
        df = self.get_cmdb_data()
        if df.empty:
            print("No CMDB data available!")
            return []
        
        # Apply business unit filter if specified
        if business_unit_filter:
            df = df[df['business_unit'] == business_unit_filter]
            print(f"Filtered to business unit: {business_unit_filter} ({len(df)} records)")
        
        # Get existing hostnames
        existing_hostnames = set(df['host'].dropna().str.lower())
        print(f"Found {len(existing_hostnames):,} existing hosts")
        
        # Discover patterns
        hostname_patterns = self.discover_hostname_patterns(df)
        if not hostname_patterns:
            print("No hostname patterns discovered!")
            return []
        
        # Generate missing candidates
        missing_candidates = self.generate_missing_hostnames(hostname_patterns)
        if not missing_candidates:
            print("No missing hostname candidates generated!")
            return []
        
        # Filter out existing hostnames
        new_candidates = [c for c in missing_candidates if c['hostname'] not in existing_hostnames]
        print(f"{len(new_candidates):,} potential missing assets identified")
        
        # Predict using neural networks
        predicted_assets = []
        self.hostname_net.eval()
        self.log_visibility_net.eval()
        
        print("AI analyzing missing asset candidates...")
        
        with torch.no_grad():
            for i, candidate in enumerate(new_candidates[:1000]):
                if i % 250 == 0 and i > 0:
                    print(f"   Analyzed {i:,} candidates...")
                
                # Prepare features
                features = self.extract_hostname_features(candidate['hostname'])
                additional_features = [
                    1 if business_unit_filter else 0,
                    1, 1, 0, 1, 0,
                    7.5, 3, 1
                ]
                combined_features = np.concatenate([features, additional_features])
                combined_features_scaled = self.feature_scaler.transform([combined_features])
                
                # Make predictions
                features_tensor = torch.FloatTensor(combined_features_scaled).to(device)
                existence_prob = self.hostname_net(features_tensor).cpu().item()
                visibility_probs = self.log_visibility_net(features_tensor).cpu().numpy()[0]
                
                # Filter by confidence threshold
                if existence_prob > self.confidence_threshold:
                    predicted_assets.append({
                        'predicted_hostname': candidate['hostname'],
                        'existence_probability': float(existence_prob),
                        'splunk_probability': float(visibility_probs[3] + visibility_probs[4]),
                        'gso_probability': float(visibility_probs[2] + visibility_probs[4]),
                        'cmdb_probability': float(sum(visibility_probs[1:])),
                        'pattern_family': candidate['pattern_template'],
                        'business_unit': business_unit_filter or 'Unknown',
                        'predicted_role': self.classify_role(candidate['hostname']),
                        'predicted_log_types': self.predict_log_types(candidate['hostname']),
                        'visibility_risk_score': self.calculate_visibility_risk(candidate['hostname'], existence_prob, visibility_probs),
                        'similar_existing_hosts': candidate['sample_existing'],
                        'pattern_density': f"{candidate['pattern_density']:.1%}",
                        'existing_pattern_count': candidate['existing_hosts_count']
                    })
        
        # Sort by probability and return top results
        result = sorted(predicted_assets, key=lambda x: x['existence_probability'], reverse=True)[:100]
        print(f"Identified {len(result)} high-confidence missing assets!")
        
        return result
    
    def classify_role(self, hostname: str) -> str:
        """Classify asset role based on hostname"""
        hostname_lower = hostname.lower()
        role_keywords = {
            'Server': ['srv', 'server'],
            'Web Server': ['web', 'www'],
            'Database': ['db', 'database', 'sql'],
            'Application': ['app', 'application'],
            'Network': ['fw', 'firewall', 'router', 'switch'],
            'Security': ['ids', 'ips', 'ndr', 'siem']
        }
        
        for role, keywords in role_keywords.items():
            if any(kw in hostname_lower for kw in keywords):
                return role
        return 'Endpoint'
    
    def predict_log_types(self, hostname: str) -> List[str]:
        """Predict log types based on hostname"""
        hostname_lower = hostname.lower()
        
        log_type_map = {
            ['fw', 'firewall']: ['Firewall Traffic', 'IDS/IPS', 'NDR'],
            ['web', 'www', 'app']: ['Web Logs', 'HTTP Access', 'Application Logs'],
            ['db', 'database', 'sql']: ['OS logs', 'Database Audit', 'Query Logs'],
            ['srv', 'server']: ['OS logs', 'EDR', 'System Events']
        }
        
        for keywords, log_types in log_type_map.items():
            if any(kw in hostname_lower for kw in keywords):
                return log_types
        
        return ['OS logs', 'EDR']
    
    def calculate_visibility_risk(self, hostname: str, existence_prob: float, visibility_probs: np.ndarray) -> float:
        """Calculate visibility risk score for missing asset"""
        hostname_lower = hostname.lower()
        
        # Risk factors based on hostname patterns
        risk_factors = [
            0.4 if 'prod' in hostname_lower else 0,
            0.3 if any(kw in hostname_lower for kw in ['srv', 'server', 'db']) else 0,
            0.2 if '.com' in hostname_lower else 0,
            0.3 if any(kw in hostname_lower for kw in ['1dc', 'fead']) else 0
        ]
        
        base_risk = sum(risk_factors)
        no_visibility_prob = visibility_probs[0]
        
        return min(base_risk + (existence_prob * 0.3) + (no_visibility_prob * 0.4), 1.0)

# Flask API Application
app = Flask(__name__)
ai_predictor = AIAssetPredictor()

@app.route('/api/train-model')
def train_model():
    """Endpoint to train the AI models"""
    try:
        threading.Thread(target=ai_predictor.train_models, daemon=True).start()
        return jsonify({
            'status': 'training_started', 
            'message': 'AI asset predictor training initiated',
            'device': str(device)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-assets')
def predict_missing_assets():
    """Endpoint to predict missing assets"""
    try:
        if not ai_predictor.trained:
            return jsonify({
                'error': 'Models not trained yet',
                'message': 'Please train the models first using /api/train-model'
            }), 503
            
        predictions = ai_predictor.predict_missing_assets()
        return jsonify({
            'total_missing_assets': len(predictions),
            'confidence_threshold': f"{ai_predictor.confidence_threshold:.0%}",
            'missing_assets': predictions,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-assets/<business_unit>')
def predict_missing_assets_bu(business_unit):
    """Endpoint to predict missing assets for specific business unit"""
    try:
        if not ai_predictor.trained:
            return jsonify({
                'error': 'Models not trained yet', 
                'message': 'Please train the models first using /api/train-model'
            }), 503
            
        predictions = ai_predictor.predict_missing_assets(business_unit)
        return jsonify({
            'total_missing_assets': len(predictions),
            'business_unit': business_unit,
            'confidence_threshold': f"{ai_predictor.confidence_threshold:.0%}",
            'missing_assets': predictions,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/model-status')
def model_status():
    """Endpoint to check model status"""
    return jsonify({
        'trained': ai_predictor.trained,
        'device': str(device),
        'model_version': ai_predictor.model_version,
        'training_metrics': ai_predictor.training_metrics,
        'confidence_threshold': ai_predictor.confidence_threshold,
        'models_exist': ai_predictor.models_exist
    })

@app.route('/api/load-models')
def load_models():
    """Endpoint to load existing models"""
    try:
        success = ai_predictor.load_models()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Models loaded successfully' if success else 'Failed to load models'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("AI Asset Predictor - Missing IT Asset Discovery System")
    print("=" * 60)
    print(f"Device: {device}")
    print(f"Model Version: {ai_predictor.model_version}")
    
    # Attempt to initialize models
    print("\nInitializing AI models...")
    ai_predictor.initialize_models()
    
    if not ai_predictor.trained:
        print("\nWARNING: AI models not ready. Some endpoints may not work.")
        print("Use /api/train-model endpoint to train the models.")
    else:
        print("\nAI models ready!")
    
    print("\nStarting Flask API server...")
    print("API Endpoints:")
    print("  - GET  /api/model-status")
    print("  - GET  /api/train-model")
    print("  - GET  /api/load-models")
    print("  - GET  /api/predict-missing-assets")
    print("  - GET  /api/predict-missing-assets/<business_unit>")
    print("\n" + "=" * 60)
    
    app.run(debug=True, port=5001, host='0.0.0.0')