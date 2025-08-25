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
from flask import Flask, jsonify
import threading
from datetime import datetime
import os
import pickle
from typing import List, Dict, Optional
from collections import Counter

device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")

class HostnamePatternNet(nn.Module):
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

class AO1VisibilityPredictor:
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        self.hostname_net = None
        self.log_visibility_net = None
        self.feature_scaler = StandardScaler()
        self.trained = False
        self.db_path = db_path
        self.model_version = "1.0.1"
        self.training_metrics = {}
        self.model_dir = 'models'
        
        os.makedirs(self.model_dir, exist_ok=True)
        
    @property
    def models_exist(self) -> bool:
        required_files = [
            f'{self.model_dir}/hostname_net.pth',
            f'{self.model_dir}/log_visibility_net.pth', 
            f'{self.model_dir}/feature_scaler.pkl'
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
    
    def extract_hostname_features(self, hostname: str) -> np.ndarray:
        if not hostname:
            return np.zeros(35)
        
        hostname = hostname.lower().strip()
        
        features = [
            len(hostname),
            hostname.count('.'),
            hostname.count('-'),
            hostname.count('_'),
            len(re.findall(r'\d', hostname)),
            len(re.findall(r'[a-z]', hostname))
        ]
        
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
    
    def prepare_training_data(self, df: pd.DataFrame) -> tuple:
        features, existence_labels, visibility_labels = [], [], []
        
        for _, row in df.iterrows():
            hostname_features = self.extract_hostname_features(row['host'])
            
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
            
            existence_score = min(sum([
                1 if row['logging_in_splunk'] == 'yes' else 0,
                1 if row['present_in_cmdb'] == 'yes' else 0,
                1 if pd.notna(row['edr_coverage']) and 'crowdstrike' in str(row['edr_coverage']).lower() else 0
            ]) / 3.0, 1.0)
            
            existence_labels.append(existence_score)
            
            visibility_type = 0
            if row['logging_in_splunk'] == 'yes' and row['logging_in_gso'] == 'yes':
                visibility_type = 4
            elif row['logging_in_splunk'] == 'yes':
                visibility_type = 3
            elif row['logging_in_gso'] == 'yes':
                visibility_type = 2
            elif row['present_in_cmdb'] == 'yes':
                visibility_type = 1
            
            visibility_labels.append(visibility_type)
        
        return np.array(features), np.array(existence_labels), np.array(visibility_labels)
    
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
        
        X_train, X_val, existence_y_train, existence_y_val, visibility_y_train, visibility_y_val = train_test_split(
            X, existence_y, visibility_y, test_size=0.2, random_state=42
        )
        
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        X_train_tensor = torch.FloatTensor(X_train_scaled).to(device)
        X_val_tensor = torch.FloatTensor(X_val_scaled).to(device)
        existence_y_train_tensor = torch.FloatTensor(existence_y_train.reshape(-1, 1)).to(device)
        existence_y_val_tensor = torch.FloatTensor(existence_y_val.reshape(-1, 1)).to(device)
        visibility_y_train_tensor = torch.LongTensor(visibility_y_train).to(device)
        visibility_y_val_tensor = torch.LongTensor(visibility_y_val).to(device)
        
        input_size = X_train_scaled.shape[1]
        self.hostname_net = HostnamePatternNet(input_size).to(device)
        self.log_visibility_net = LogVisibilityPredictor(input_size).to(device)
        
        optimizer1 = optim.AdamW(self.hostname_net.parameters(), lr=0.001, weight_decay=1e-4)
        optimizer2 = optim.AdamW(self.log_visibility_net.parameters(), lr=0.001, weight_decay=1e-4)
        
        criterion1 = nn.BCELoss()
        criterion2 = nn.CrossEntropyLoss()
        
        scheduler1 = optim.lr_scheduler.ReduceLROnPlateau(optimizer1, patience=15, factor=0.7)
        scheduler2 = optim.lr_scheduler.ReduceLROnPlateau(optimizer2, patience=15, factor=0.7)
        
        print(f"Training models on {device}...")
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(300):
            self.hostname_net.train()
            self.log_visibility_net.train()
            
            optimizer1.zero_grad()
            existence_outputs = self.hostname_net(X_train_tensor)
            loss1 = criterion1(existence_outputs, existence_y_train_tensor)
            loss1.backward()
            torch.nn.utils.clip_grad_norm_(self.hostname_net.parameters(), 1.0)
            optimizer1.step()
            
            optimizer2.zero_grad()
            visibility_outputs = self.log_visibility_net(X_train_tensor)
            loss2 = criterion2(visibility_outputs, visibility_y_train_tensor)
            loss2.backward()
            torch.nn.utils.clip_grad_norm_(self.log_visibility_net.parameters(), 1.0)
            optimizer2.step()
            
            if epoch % 10 == 0:
                self.hostname_net.eval()
                self.log_visibility_net.eval()
                
                with torch.no_grad():
                    val_existence_outputs = self.hostname_net(X_val_tensor)
                    val_loss1 = criterion1(val_existence_outputs, existence_y_val_tensor)
                    
                    val_visibility_outputs = self.log_visibility_net(X_val_tensor)
                    val_loss2 = criterion2(val_visibility_outputs, visibility_y_val_tensor)
                    
                    total_val_loss = val_loss1 + val_loss2
                    
                    print(f'Epoch {epoch}, Train: {loss1.item():.4f}/{loss2.item():.4f}, Val: {val_loss1.item():.4f}/{val_loss2.item():.4f}')
                    
                    if total_val_loss < best_val_loss:
                        best_val_loss = total_val_loss
                        patience_counter = 0
                        self.save_models()
                    else:
                        patience_counter += 1
                    
                    if patience_counter >= 25:
                        print("Early stopping triggered!")
                        break
                
                scheduler1.step(val_loss1)
                scheduler2.step(val_loss2)
        
        self.trained = True
        self.training_metrics = {
            'final_losses': [loss1.item(), loss2.item(), val_loss1.item(), val_loss2.item()],
            'training_records': len(X_train),
            'validation_records': len(X_val),
            'epochs_trained': epoch + 1,
            'device': str(device)
        }
        
        print(f"Training completed! Final losses - Existence: {loss1.item():.4f}, Visibility: {loss2.item():.4f}")
    
    def save_models(self):
        try:
            torch.save(self.hostname_net.state_dict(), f'{self.model_dir}/hostname_net.pth')
            torch.save(self.log_visibility_net.state_dict(), f'{self.model_dir}/log_visibility_net.pth')
            with open(f'{self.model_dir}/feature_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
        except Exception as e:
            print(f"Error saving models: {e}")
    
    def load_models(self):
        try:
            if not self.models_exist:
                return False
            
            sample_features = self.extract_hostname_features("sample-host-01.example.com")
            additional_features = [0] * 9
            input_size = len(np.concatenate([sample_features, additional_features]))
            
            self.hostname_net = HostnamePatternNet(input_size).to(device)
            self.log_visibility_net = LogVisibilityPredictor(input_size).to(device)
            
            self.hostname_net.load_state_dict(torch.load(f'{self.model_dir}/hostname_net.pth', map_location=device))
            self.log_visibility_net.load_state_dict(torch.load(f'{self.model_dir}/log_visibility_net.pth', map_location=device))
            
            with open(f'{self.model_dir}/feature_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            
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
                print("Unable to train models - no data available or training failed")
                return []
        
        df = self.get_cmdb_data()
        if df.empty:
            return []
        
        if business_unit_filter:
            df = df[df['business_unit'] == business_unit_filter]
        
        hostname_patterns = self.analyze_naming_patterns(df)
        predicted_assets = []
        existing_hostnames = set(df['host'].values)
        
        for pattern in hostname_patterns[:15]:
            for i in range(1, 150):
                for padding in [2, 3, 4]:
                    potential_hostname = pattern['pattern'].replace('XXX', str(i).zfill(padding))
                    
                    if potential_hostname not in existing_hostnames:
                        features = self.extract_hostname_features(potential_hostname)
                        additional_features = [
                            1 if business_unit_filter else 0,
                            1, 1, 0, 1, 0,
                            7.5, 3, 1
                        ]
                        combined_features = np.concatenate([features, additional_features])
                        combined_features_scaled = self.feature_scaler.transform([combined_features])
                        
                        with torch.no_grad():
                            features_tensor = torch.FloatTensor(combined_features_scaled).to(device)
                            existence_prob = self.hostname_net(features_tensor).cpu().item()
                            visibility_probs = self.log_visibility_net(features_tensor).cpu().numpy()[0]
                        
                        if existence_prob > 0.7:
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
        
        return sorted(predicted_assets, key=lambda x: x['existence_probability'], reverse=True)[:75]
    
    def analyze_naming_patterns(self, df: pd.DataFrame) -> List[Dict]:
        patterns = []
        
        for bu in df['business_unit'].dropna().unique()[:8]:
            bu_df = df[df['business_unit'] == bu]
            pattern_counts = {}
            
            for hostname in bu_df['host']:
                if hostname:
                    base_pattern = re.sub(r'\d+', 'XXX', hostname.lower())
                    pattern_counts[base_pattern] = pattern_counts.get(base_pattern, 0) + 1
            
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
        hostname_lower = hostname.lower()
        role_keywords = {
            'Server': ['srv', 'server'],
            'Web Server': ['web', 'www'],
            'Database': ['db', 'database', 'sql'],
            'Application': ['app', 'application'],
            'Network': ['fw', 'firewall'],
            'Security': ['ids', 'ips', 'ndr']
        }
        
        for role, keywords in role_keywords.items():
            if any(kw in hostname_lower for kw in keywords):
                return role
        return 'Endpoint'
    
    def predict_log_types(self, hostname: str) -> List[str]:
        hostname_lower = hostname.lower()
        
        log_type_map = {
            ['fw', 'firewall']: ['Firewall Traffic', 'IDS/IPS', 'NDR'],
            ['web', 'www', 'app']: ['Web Logs', 'HTTP Access', 'Application Logs'],
            ['db', 'database', 'sql']: ['OS logs', 'Theom', 'Database Audit'],
            ['srv', 'server']: ['OS logs', 'EDR', 'System Events']
        }
        
        for keywords, log_types in log_type_map.items():
            if any(kw in hostname_lower for kw in keywords):
                return log_types
        
        return ['OS logs', 'EDR']
    
    def calculate_visibility_risk(self, hostname: str, existence_prob: float, visibility_probs: np.ndarray) -> float:
        hostname_lower = hostname.lower()
        
        risk_factors = [
            0.4 if 'prod' in hostname_lower else 0,
            0.3 if any(kw in hostname_lower for kw in ['srv', 'server', 'db']) else 0,
            0.2 if '.com' in hostname_lower else 0,
            0.3 if any(kw in hostname_lower for kw in ['1dc', 'fead']) else 0
        ]
        
        base_risk = sum(risk_factors)
        no_visibility_prob = visibility_probs[0]
        
        return min(base_risk + (existence_prob * 0.3) + (no_visibility_prob * 0.4), 1.0)

app = Flask(__name__)
ao1_predictor = AO1VisibilityPredictor()

@app.route('/api/train-visibility-model')
def train_visibility_model():
    try:
        threading.Thread(target=ao1_predictor.train_models, daemon=True).start()
        return jsonify({
            'status': 'training_started', 
            'message': 'AO1 visibility model training initiated',
            'device': str(device)
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
        'last_training': datetime.now().isoformat() if ao1_predictor.trained else None
    })

@app.route('/api/visibility-gap-analysis')
def visibility_gap_analysis():
    try:
        if not ao1_predictor.trained:
            return jsonify({
                'error': 'Models not trained yet',
                'critical_visibility_gaps': [],
                'high_value_targets': [],
                'splunk_gaps': [],
                'gso_gaps': [],
                'total_predicted_assets': 0,
                'avg_existence_probability': 0,
                'pattern_coverage': 0,
                'business_unit_distribution': {},
                'role_distribution': {}
            })
            
        predictions = ao1_predictor.predict_missing_assets()
        
        analysis = {
            'critical_visibility_gaps': [p for p in predictions if p['visibility_risk_score'] > 0.8],
            'high_value_targets': [p for p in predictions if p['predicted_role'] in ['Server', 'Database', 'Security']],
            'splunk_gaps': [p for p in predictions if p['splunk_probability'] < 0.5],
            'gso_gaps': [p for p in predictions if p['gso_probability'] < 0.5],
            'total_predicted_assets': len(predictions),
            'avg_existence_probability': float(np.mean([p['existence_probability'] for p in predictions])) if predictions else 0,
            'pattern_coverage': len(set([p['pattern_family'] for p in predictions])),
            'business_unit_distribution': dict(Counter([p['business_unit'] for p in predictions]).most_common(10)) if predictions else {},
            'role_distribution': dict(Counter([p['predicted_role'] for p in predictions])) if predictions else {}
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
            'message': 'Models loaded successfully' if success else 'Failed to load models'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Initializing AO1 Visibility Predictor...")
    ao1_predictor.initialize_models()
    
    if not ao1_predictor.trained:
        print("WARNING: AI models not ready. Some endpoints may not work.")
    else:
        print("AI models ready!")
    
    app.run(debug=True, port=5001, host='0.0.0.0')