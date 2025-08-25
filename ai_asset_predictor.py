# /src/ml/ai_asset_predictor.py

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
from typing import List, Dict, Any, Optional

# Set device - will fallback to CPU if MPS is not available
try:
    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
except:
    device = torch.device("cpu")

class HostnamePatternNet(nn.Module):
    """Neural network for predicting hostname existence probability."""
    
    def __init__(self, input_size: int):
        super(HostnamePatternNet, self).__init__()
        self.fc1 = nn.Linear(input_size, 512)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.3)
        self.fc2 = nn.Linear(512, 256)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.3)
        self.fc3 = nn.Linear(256, 128)
        self.relu3 = nn.ReLU()
        self.fc4 = nn.Linear(128, 64)
        self.relu4 = nn.ReLU()
        self.output = nn.Linear(64, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        x = self.dropout1(self.relu1(self.fc1(x)))
        x = self.dropout2(self.relu2(self.fc2(x)))
        x = self.relu3(self.fc3(x))
        x = self.relu4(self.fc4(x))
        return self.sigmoid(self.output(x))

class LogVisibilityPredictor(nn.Module):
    """Neural network for predicting log visibility types."""
    
    def __init__(self, input_size: int):
        super(LogVisibilityPredictor, self).__init__()
        self.fc1 = nn.Linear(input_size, 256)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.2)
        self.fc2 = nn.Linear(256, 128)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.2)
        self.fc3 = nn.Linear(128, 64)
        self.relu3 = nn.ReLU()
        self.fc4 = nn.Linear(64, 32)
        self.relu4 = nn.ReLU()
        self.output = nn.Linear(32, 5)  # 5 visibility categories
        self.softmax = nn.Softmax(dim=1)
        
    def forward(self, x):
        x = self.dropout1(self.relu1(self.fc1(x)))
        x = self.dropout2(self.relu2(self.fc2(x)))
        x = self.relu3(self.fc3(x))
        x = self.relu4(self.fc4(x))
        return self.softmax(self.output(x))

class AO1VisibilityPredictor:
    """Main AI predictor class for visibility analysis."""
    
    def __init__(self, db_path: str = 'data/universal_cmdb.duckdb'):
        self.hostname_net = None
        self.log_visibility_net = None
        self.feature_scaler = StandardScaler()
        self.trained = False
        self.db_path = db_path
        self.model_version = "1.0.0"
        self.training_metrics = {}
        
        # Create model directory
        self.model_dir = 'models'
        os.makedirs(self.model_dir, exist_ok=True)
        
    def get_db_connection(self) -> Optional[duckdb.DuckDBPyConnection]:
        """Get DuckDB connection."""
        try:
            return duckdb.connect(self.db_path)
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def extract_hostname_features(self, hostname: str) -> np.ndarray:
        """Extract features from hostname for ML model."""
        if not hostname:
            return np.zeros(40)
        
        hostname = hostname.lower().strip()
        features = []
        
        # Basic string features
        features.append(len(hostname))
        features.append(hostname.count('.'))
        features.append(hostname.count('-'))
        features.append(hostname.count('_'))
        features.append(len(re.findall(r'\d', hostname)))
        features.append(len(re.findall(r'[a-z]', hostname)))
        
        # Server/infrastructure keywords
        features.append(1 if any(x in hostname for x in ['srv', 'server']) else 0)
        features.append(1 if any(x in hostname for x in ['web', 'www']) else 0)
        features.append(1 if any(x in hostname for x in ['db', 'database', 'sql']) else 0)
        features.append(1 if any(x in hostname for x in ['app', 'application']) else 0)
        features.append(1 if any(x in hostname for x in ['dc', 'datacenter']) else 0)
        
        # Environment indicators
        features.append(1 if any(x in hostname for x in ['prod', 'production']) else 0)
        features.append(1 if any(x in hostname for x in ['dev', 'development']) else 0)
        features.append(1 if any(x in hostname for x in ['test', 'testing']) else 0)
        features.append(1 if any(x in hostname for x in ['stage', 'staging']) else 0)
        features.append(1 if any(x in hostname for x in ['uat', 'preprod']) else 0)
        
        # Number pattern analysis
        number_groups = re.findall(r'\d+', hostname)
        features.append(len(number_groups))
        if number_groups:
            try:
                max_num = max([int(n) for n in number_groups])
                min_num = min([int(n) for n in number_groups])
                features.append(max_num)
                features.append(min_num)
                features.append(1 if max_num > 100 else 0)
            except ValueError:
                features.extend([0, 0, 0])
        else:
            features.extend([0, 0, 0])
        
        # Domain extensions
        features.append(1 if hostname.endswith('.com') else 0)
        features.append(1 if hostname.endswith('.local') else 0)
        features.append(1 if hostname.endswith('.net') else 0)
        
        # Company-specific patterns
        features.append(1 if '1dc' in hostname else 0)
        features.append(1 if 'fead' in hostname else 0)
        features.append(1 if 'fiserv' in hostname else 0)
        
        # Security/network appliance indicators
        features.append(1 if any(x in hostname for x in ['firewall', 'fw']) else 0)
        features.append(1 if any(x in hostname for x in ['ids', 'ips']) else 0)
        features.append(1 if any(x in hostname for x in ['ndr', 'detection']) else 0)
        features.append(1 if any(x in hostname for x in ['proxy', 'px']) else 0)
        features.append(1 if any(x in hostname for x in ['dns', 'domain']) else 0)
        features.append(1 if any(x in hostname for x in ['waf', 'gateway']) else 0)
        
        # Geographic indicators
        features.append(1 if any(x in hostname for x in ['north', 'south', 'east', 'west']) else 0)
        features.append(1 if any(x in hostname for x in ['us', 'usa', 'america']) else 0)
        features.append(1 if any(x in hostname for x in ['eu', 'emea', 'europe']) else 0)
        features.append(1 if any(x in hostname for x in ['apac', 'asia']) else 0)
        features.append(1 if any(x in hostname for x in ['latam', 'latin']) else 0)
        
        # Virtualization/cloud indicators
        features.append(1 if any(x in hostname for x in ['vm', 'virtual']) else 0)
        features.append(1 if any(x in hostname for x in ['docker', 'container']) else 0)
        features.append(1 if any(x in hostname for x in ['aws', 'azure', 'gcp', 'cloud']) else 0)
        features.append(1 if any(x in hostname for x in ['k8s', 'kubernetes']) else 0)
        
        return np.array(features[:40])
    
    def get_cmdb_data(self) -> pd.DataFrame:
        """Fetch training data from DuckDB."""
        conn = self.get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        query = """
        SELECT 
            fqdn, business_unit, region, country, data_center, cloud_region,
            system_classification, infrastructure_type, cio, apm,
            logging_in_splunk, logging_in_gso, present_in_cmdb, 
            edr_coverage, sas_coverage, tanium_coverage, dlp_agent_coverage,
            first_seen_ts, last_updated_ts, data_quality_score, source_count
        FROM universal_cmdb_copy2
        WHERE fqdn IS NOT NULL AND fqdn != ''
            AND data_quality_score > 3.0
        ORDER BY data_quality_score DESC
        LIMIT 50000
        """
        
        try:
            df = conn.execute(query).df()
            conn.close()
            return df
        except Exception as e:
            print(f"Error fetching CMDB data: {e}")
            conn.close()
            return pd.DataFrame()
    
    def prepare_training_data(self, df: pd.DataFrame) -> tuple:
        """Prepare training data from CMDB dataframe."""
        features = []
        existence_labels = []
        visibility_labels = []
        
        for idx, row in df.iterrows():
            hostname_features = self.extract_hostname_features(row['fqdn'])
            
            # Additional contextual features
            additional_features = [
                1 if pd.notna(row['business_unit']) else 0,
                1 if pd.notna(row['region']) else 0,
                1 if pd.notna(row['system_classification']) and 'server' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['system_classification']) and 'windows' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['system_classification']) and 'linux' in str(row['system_classification']).lower() else 0,
                1 if pd.notna(row['infrastructure_type']) and 'cloud' in str(row['infrastructure_type']).lower() else 0,
                1 if pd.notna(row['infrastructure_type']) and 'server' in str(row['infrastructure_type']).lower() else 0,
                float(row['data_quality_score']) if pd.notna(row['data_quality_score']) else 0.0,
                int(row['source_count']) if pd.notna(row['source_count']) else 0,
                1 if pd.notna(row['cio']) else 0
            ]
            
            combined_features = np.concatenate([hostname_features, additional_features])
            features.append(combined_features)
            
            # Calculate existence score based on multiple factors
            existence_score = min(sum([
                1 if row['logging_in_splunk'] == 'yes' else 0,
                1 if row['present_in_cmdb'] == 'yes' else 0,
                1 if pd.notna(row['edr_coverage']) and 'crowdstrike agent' in str(row['edr_coverage']).lower() else 0
            ]) / 3.0, 1.0)
            
            existence_labels.append(existence_score)
            
            # Determine visibility category
            visibility_type = 0  # No visibility
            if row['logging_in_splunk'] == 'yes' and row['logging_in_gso'] == 'yes':
                visibility_type = 4  # Full visibility
            elif row['logging_in_splunk'] == 'yes':
                visibility_type = 3  # Splunk only
            elif row['logging_in_gso'] == 'yes':
                visibility_type = 2  # GSO only
            elif row['present_in_cmdb'] == 'yes':
                visibility_type = 1  # CMDB only
            
            visibility_labels.append(visibility_type)
        
        return np.array(features), np.array(existence_labels), np.array(visibility_labels)
    
    def train_models(self):
        """Train both neural networks."""
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
        
        # Split data for validation
        X_train, X_val, existence_y_train, existence_y_val, visibility_y_train, visibility_y_val = train_test_split(
            X, existence_y, visibility_y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train_scaled).to(device)
        X_val_tensor = torch.FloatTensor(X_val_scaled).to(device)
        existence_y_train_tensor = torch.FloatTensor(existence_y_train.reshape(-1, 1)).to(device)
        existence_y_val_tensor = torch.FloatTensor(existence_y_val.reshape(-1, 1)).to(device)
        visibility_y_train_tensor = torch.LongTensor(visibility_y_train).to(device)
        visibility_y_val_tensor = torch.LongTensor(visibility_y_val).to(device)
        
        # Initialize networks
        input_size = X_train_scaled.shape[1]
        self.hostname_net = HostnamePatternNet(input_size).to(device)
        self.log_visibility_net = LogVisibilityPredictor(input_size).to(device)
        
        # Optimizers and loss functions
        optimizer1 = optim.Adam(self.hostname_net.parameters(), lr=0.001, weight_decay=1e-5)
        optimizer2 = optim.Adam(self.log_visibility_net.parameters(), lr=0.001, weight_decay=1e-5)
        
        criterion1 = nn.BCELoss()
        criterion2 = nn.CrossEntropyLoss()
        
        scheduler1 = optim.lr_scheduler.ReduceLROnPlateau(optimizer1, patience=20, factor=0.5)
        scheduler2 = optim.lr_scheduler.ReduceLROnPlateau(optimizer2, patience=20, factor=0.5)
        
        print(f"Training models on {device}...")
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(500):
            # Training phase
            self.hostname_net.train()
            self.log_visibility_net.train()
            
            # Train hostname existence model
            optimizer1.zero_grad()
            existence_outputs = self.hostname_net(X_train_tensor)
            loss1 = criterion1(existence_outputs, existence_y_train_tensor)
            loss1.backward()
            optimizer1.step()
            
            # Train log visibility model
            optimizer2.zero_grad()
            visibility_outputs = self.log_visibility_net(X_train_tensor)
            loss2 = criterion2(visibility_outputs, visibility_y_train_tensor)
            loss2.backward()
            optimizer2.step()
            
            # Validation phase
            if epoch % 10 == 0:
                self.hostname_net.eval()
                self.log_visibility_net.eval()
                
                with torch.no_grad():
                    val_existence_outputs = self.hostname_net(X_val_tensor)
                    val_loss1 = criterion1(val_existence_outputs, existence_y_val_tensor)
                    
                    val_visibility_outputs = self.log_visibility_net(X_val_tensor)
                    val_loss2 = criterion2(val_visibility_outputs, visibility_y_val_tensor)
                    
                    total_val_loss = val_loss1 + val_loss2
                    
                    print(f'Epoch {epoch}, Train Loss: {loss1.item():.4f}, {loss2.item():.4f}, '
                          f'Val Loss: {val_loss1.item():.4f}, {val_loss2.item():.4f}')
                    
                    # Early stopping
                    if total_val_loss < best_val_loss:
                        best_val_loss = total_val_loss
                        patience_counter = 0
                        self.save_models()
                    else:
                        patience_counter += 1
                    
                    if patience_counter >= 30:
                        print("Early stopping triggered!")
                        break
                
                scheduler1.step(val_loss1)
                scheduler2.step(val_loss2)
        
        self.trained = True
        self.training_metrics = {
            'final_train_loss1': loss1.item(),
            'final_train_loss2': loss2.item(),
            'final_val_loss1': val_loss1.item(),
            'final_val_loss2': val_loss2.item(),
            'training_records': len(X_train),
            'validation_records': len(X_val),
            'epochs_trained': epoch + 1,
            'device': str(device)
        }
        
        print(f"Training completed! Final losses - Existence: {loss1.item():.4f}, Visibility: {loss2.item():.4f}")
    
    def save_models(self):
        """Save trained models and scaler."""
        try:
            torch.save(self.hostname_net.state_dict(), f'{self.model_dir}/hostname_net.pth')
            torch.save(self.log_visibility_net.state_dict(), f'{self.model_dir}/log_visibility_net.pth')
            
            with open(f'{self.model_dir}/feature_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
                
            print("Models saved successfully!")
        except Exception as e:
            print(f"Error saving models: {e}")
    
    def load_models(self):
        """Load trained models and scaler."""
        try:
            # Determine input size from a sample
            sample_features = self.extract_hostname_features("sample-host-01.example.com")
            additional_features = [0] * 10  # Match the additional features in training
            combined_features = np.concatenate([sample_features, additional_features])
            input_size = len(combined_features)
            
            self.hostname_net = HostnamePatternNet(input_size).to(device)
            self.log_visibility_net = LogVisibilityPredictor(input_size).to(device)
            
            self.hostname_net.load_state_dict(torch.load(f'{self.model_dir}/hostname_net.pth', map_location=device))
            self.log_visibility_net.load_state_dict(torch.load(f'{self.model_dir}/log_visibility_net.pth', map_location=device))
            
            with open(f'{self.model_dir}/feature_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            
            self.trained = True
            print("Models loaded successfully!")
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def predict_missing_assets(self, business_unit_filter: Optional[str] = None) -> List[Dict]:
        """Predict missing assets using trained models."""
        if not self.trained:
            print("Models not trained yet!")
            return []
        
        df = self.get_cmdb_data()
        if df.empty:
            return []
        
        if business_unit_filter:
            df = df[df['business_unit'] == business_unit_filter]
        
        hostname_patterns = self.analyze_naming_patterns(df)
        predicted_assets = []
        
        for pattern in hostname_patterns[:20]:  # Limit patterns processed
            for i in range(1, 200):  # Reduced range for performance
                for padding in [2, 3, 4]:
                    potential_hostname = pattern['pattern'].replace('XXX', str(i).zfill(padding))
                    
                    if potential_hostname not in df['fqdn'].values:
                        features = self.extract_hostname_features(potential_hostname)
                        additional_features = [
                            1 if business_unit_filter else 0,  # Has business unit
                            1,  # Has region (assume yes for predictions)
                            1,  # Is server
                            0,  # Is Windows
                            1,  # Is Linux  
                            0,  # Is cloud
                            1,  # Has server infrastructure
                            7.5,  # High quality score for predictions
                            3,   # Multiple sources
                            1    # Has CIO
                        ]
                        combined_features = np.concatenate([features, additional_features])
                        combined_features_scaled = self.feature_scaler.transform([combined_features])
                        
                        with torch.no_grad():
                            features_tensor = torch.FloatTensor(combined_features_scaled).to(device)
                            existence_prob = self.hostname_net(features_tensor).cpu().numpy()[0][0]
                            visibility_probs = self.log_visibility_net(features_tensor).cpu().numpy()[0]
                        
                        if existence_prob > 0.75:
                            predicted_assets.append({
                                'predicted_hostname': potential_hostname,
                                'existence_probability': float(existence_prob),
                                'splunk_probability': float(visibility_probs[3] + visibility_probs[4]),
                                'gso_probability': float(visibility_probs[2] + visibility_probs[4]),
                                'cmdb_probability': float(sum(visibility_probs[1:])),
                                'pattern_family': pattern['base_pattern'],
                                'business_unit': business_unit_filter or pattern.get('business_unit', 'Unknown'),
                                'predicted_role': self.classify_role(potential_hostname),
                                'predicted_log_types': self.predict_log_types(potential_hostname),
                                'visibility_risk_score': self.calculate_visibility_risk(potential_hostname, existence_prob, visibility_probs)
                            })
        
        return sorted(predicted_assets, key=lambda x: x['existence_probability'], reverse=True)[:100]
    
    def analyze_naming_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze hostname patterns for prediction."""
        patterns = []
        
        for bu in df['business_unit'].dropna().unique()[:10]:  # Limit business units
            bu_df = df[df['business_unit'] == bu]
            
            pattern_counts = {}
            for hostname in bu_df['fqdn']:
                if not hostname:
                    continue
                
                base_pattern = re.sub(r'\d+', 'XXX', hostname.lower())
                pattern_counts[base_pattern] = pattern_counts.get(base_pattern, 0) + 1
            
            # Only keep patterns with multiple instances
            for pattern, count in pattern_counts.items():
                if count >= 2:
                    patterns.append({
                        'pattern': pattern,
                        'base_pattern': pattern,
                        'business_unit': bu,
                        'count': count
                    })
        
        return sorted(patterns, key=lambda x: x['count'], reverse=True)
    
    def classify_role(self, hostname: str) -> str:
        """Classify the role of a hostname."""
        hostname_lower = hostname.lower()
        if any(keyword in hostname_lower for keyword in ['srv', 'server']):
            return 'Server'
        elif any(keyword in hostname_lower for keyword in ['web', 'www']):
            return 'Web Server'
        elif any(keyword in hostname_lower for keyword in ['db', 'database', 'sql']):
            return 'Database'
        elif any(keyword in hostname_lower for keyword in ['app', 'application']):
            return 'Application'
        elif any(keyword in hostname_lower for keyword in ['fw', 'firewall']):
            return 'Network'
        elif any(keyword in hostname_lower for keyword in ['ids', 'ips', 'ndr']):
            return 'Security'
        else:
            return 'Endpoint'
    
    def predict_log_types(self, hostname: str) -> List[str]:
        """Predict what log types this hostname would generate."""
        hostname_lower = hostname.lower()
        log_types = []
        
        if any(keyword in hostname_lower for keyword in ['fw', 'firewall']):
            log_types.extend(['Firewall Traffic', 'IDS/IPS', 'NDR'])
        elif any(keyword in hostname_lower for keyword in ['web', 'www', 'app']):
            log_types.extend(['Web Logs', 'HTTP Access', 'Application Logs'])
        elif any(keyword in hostname_lower for keyword in ['db', 'database', 'sql']):
            log_types.extend(['OS logs', 'Theom', 'Database Audit'])
        elif any(keyword in hostname_lower for keyword in ['srv', 'server']):
            log_types.extend(['OS logs', 'EDR', 'System Events'])
        else:
            log_types.extend(['OS logs', 'EDR'])
        
        return log_types
    
    def calculate_visibility_risk(self, hostname: str, existence_prob: float, visibility_probs: np.ndarray) -> float:
        """Calculate visibility risk score for a hostname."""
        risk_factors = []
        
        hostname_lower = hostname.lower()
        if 'prod' in hostname_lower:
            risk_factors.append(0.4)
        if any(keyword in hostname_lower for keyword in ['srv', 'server', 'db']):
            risk_factors.append(0.3)
        if '.com' in hostname_lower:
            risk_factors.append(0.2)
        if '1dc' in hostname_lower or 'fead' in hostname_lower:
            risk_factors.append(0.3)
        
        base_risk = sum(risk_factors)
        no_visibility_prob = visibility_probs[0]
        
        return min(base_risk + (existence_prob * 0.3) + (no_visibility_prob * 0.4), 1.0)

# Flask app for AI services
app = Flask(__name__)
ao1_predictor = AO1VisibilityPredictor()

@app.route('/api/train-visibility-model')
def train_visibility_model():
    """Start model training in background thread."""
    try:
        def train_async():
            ao1_predictor.train_models()
        
        threading.Thread(target=train_async, daemon=True).start()
        return jsonify({
            'status': 'training_started', 
            'message': 'AO1 visibility model training initiated',
            'device': str(device)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility')
def predict_missing_visibility():
    """Predict missing assets (all business units)."""
    try:
        predictions = ao1_predictor.predict_missing_assets()
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility/<business_unit>')
def predict_missing_visibility_bu(business_unit):
    """Predict missing assets for specific business unit."""
    try:
        predictions = ao1_predictor.predict_missing_assets(business_unit)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/visibility-model-status')
def visibility_model_status():
    """Get model training status."""
    return jsonify({
        'trained': ao1_predictor.trained,
        'device': str(device),
        'model_version': ao1_predictor.model_version,
        'training_metrics': ao1_predictor.training_metrics,
        'last_training': datetime.now().isoformat() if ao1_predictor.trained else None
    })

@app.route('/api/visibility-gap-analysis')
def visibility_gap_analysis():
    """Comprehensive visibility gap analysis."""
    try:
        predictions = ao1_predictor.predict_missing_assets()
        
        analysis = {
            'critical_visibility_gaps': [p for p in predictions if p['visibility_risk_score'] > 0.8],
            'high_value_targets': [p for p in predictions if p['predicted_role'] in ['Server', 'Database', 'Security']],
            'splunk_gaps': [p for p in predictions if p['splunk_probability'] < 0.5],
            'gso_gaps': [p for p in predictions if p['gso_probability'] < 0.5],
            'total_predicted_assets': len(predictions),
            'avg_existence_probability': float(np.mean([p['existence_probability'] for p in predictions])) if predictions else 0,
            'pattern_coverage': len(set([p['pattern_family'] for p in predictions])),
            'business_unit_distribution': {},
            'role_distribution': {}
        }
        
        # Calculate distributions
        if predictions:
            from collections import Counter
            bu_dist = Counter([p['business_unit'] for p in predictions])
            role_dist = Counter([p['predicted_role'] for p in predictions])
            
            analysis['business_unit_distribution'] = dict(bu_dist.most_common(10))
            analysis['role_distribution'] = dict(role_dist)
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-models')
def load_models():
    """Load pre-trained models."""
    try:
        success = ao1_predictor.load_models()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Models loaded successfully' if success else 'Failed to load models'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Try to load existing models
    ao1_predictor.load_models()
    
    app.run(debug=True, port=5001, host='0.0.0.0')