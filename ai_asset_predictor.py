# /src/ml/ai_asset_predictor.py

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import re
import duckdb
from sklearn.preprocessing import StandardScaler
from flask import Flask, jsonify
import threading
from datetime import datetime

device = torch.device("mps")

class HostnamePatternNet(nn.Module):
    def __init__(self, input_size):
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
    def __init__(self, input_size):
        super(LogVisibilityPredictor, self).__init__()
        self.fc1 = nn.Linear(input_size, 256)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(256, 128)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(128, 64)
        self.relu3 = nn.ReLU()
        self.fc4 = nn.Linear(64, 32)
        self.relu4 = nn.ReLU()
        self.output = nn.Linear(32, 5)
        self.softmax = nn.Softmax(dim=1)
        
    def forward(self, x):
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        x = self.relu3(self.fc3(x))
        x = self.relu4(self.fc4(x))
        return self.softmax(self.output(x))

class AO1VisibilityPredictor:
    def __init__(self):
        self.hostname_net = None
        self.log_visibility_net = None
        self.feature_scaler = StandardScaler()
        self.trained = False
        self.db_path = 'data/universal_cmdb.duckdb'
        
    def extract_hostname_features(self, hostname):
        if not hostname:
            return np.zeros(40)
        
        hostname = hostname.lower().strip()
        features = []
        
        features.append(len(hostname))
        features.append(hostname.count('.'))
        features.append(hostname.count('-'))
        features.append(hostname.count('_'))
        features.append(len(re.findall(r'\d', hostname)))
        features.append(len(re.findall(r'[a-z]', hostname)))
        
        features.append(1 if any(x in hostname for x in ['srv', 'server']) else 0)
        features.append(1 if any(x in hostname for x in ['web', 'www']) else 0)
        features.append(1 if any(x in hostname for x in ['db', 'database', 'sql']) else 0)
        features.append(1 if any(x in hostname for x in ['app', 'application']) else 0)
        features.append(1 if any(x in hostname for x in ['dc', 'datacenter']) else 0)
        features.append(1 if any(x in hostname for x in ['prod', 'production']) else 0)
        features.append(1 if any(x in hostname for x in ['dev', 'development']) else 0)
        features.append(1 if any(x in hostname for x in ['test', 'testing']) else 0)
        features.append(1 if any(x in hostname for x in ['stage', 'staging']) else 0)
        features.append(1 if any(x in hostname for x in ['uat', 'preprod']) else 0)
        
        number_groups = re.findall(r'\d+', hostname)
        features.append(len(number_groups))
        if number_groups:
            max_num = max([int(n) for n in number_groups])
            min_num = min([int(n) for n in number_groups])
            features.append(max_num)
            features.append(min_num)
            features.append(1 if max_num > 100 else 0)
        else:
            features.extend([0, 0, 0])
        
        features.append(1 if hostname.endswith('.com') else 0)
        features.append(1 if hostname.endswith('.local') else 0)
        features.append(1 if hostname.endswith('.net') else 0)
        features.append(1 if '1dc' in hostname else 0)
        features.append(1 if 'fead' in hostname else 0)
        features.append(1 if 'fiserv' in hostname else 0)
        
        features.append(1 if any(x in hostname for x in ['firewall', 'fw']) else 0)
        features.append(1 if any(x in hostname for x in ['ids', 'ips']) else 0)
        features.append(1 if any(x in hostname for x in ['ndr', 'detection']) else 0)
        features.append(1 if any(x in hostname for x in ['proxy', 'px']) else 0)
        features.append(1 if any(x in hostname for x in ['dns', 'domain']) else 0)
        features.append(1 if any(x in hostname for x in ['waf', 'gateway']) else 0)
        
        features.append(1 if any(x in hostname for x in ['north', 'south', 'east', 'west']) else 0)
        features.append(1 if any(x in hostname for x in ['us', 'usa', 'america']) else 0)
        features.append(1 if any(x in hostname for x in ['eu', 'emea', 'europe']) else 0)
        features.append(1 if any(x in hostname for x in ['apac', 'asia']) else 0)
        features.append(1 if any(x in hostname for x in ['latam', 'latin']) else 0)
        
        features.append(1 if any(x in hostname for x in ['vm', 'virtual']) else 0)
        features.append(1 if any(x in hostname for x in ['docker', 'container']) else 0)
        features.append(1 if any(x in hostname for x in ['aws', 'azure', 'gcp', 'cloud']) else 0)
        features.append(1 if any(x in hostname for x in ['k8s', 'kubernetes']) else 0)
        
        return np.array(features[:40])
    
    def get_cmdb_data(self):
        conn = duckdb.connect(self.db_path)
        
        query = """
        SELECT 
            fqdn, business_unit, region, country, data_center, cloud_region,
            system_classification, infrastructure_type, cio, apm,
            logging_in_splunk, logging_in_gso, present_in_cmdb, 
            edr_coverage, sas_coverage, tanium_coverage, dlp_agent_coverage,
            first_seen_ts, last_updated_ts, data_quality_score, source_count
        FROM universal_cmdb_copy2
        WHERE fqdn IS NOT NULL AND fqdn != ''
        """
        
        df = conn.execute(query).df()
        conn.close()
        return df
    
    def prepare_training_data(self, df):
        features = []
        existence_labels = []
        visibility_labels = []
        
        for idx, row in df.iterrows():
            hostname_features = self.extract_hostname_features(row['fqdn'])
            
            additional_features = [
                1 if row['business_unit'] else 0,
                1 if row['region'] else 0,
                1 if row['system_classification'] and 'server' in str(row['system_classification']).lower() else 0,
                1 if row['system_classification'] and 'windows' in str(row['system_classification']).lower() else 0,
                1 if row['system_classification'] and 'linux' in str(row['system_classification']).lower() else 0,
                1 if row['infrastructure_type'] and 'cloud' in str(row['infrastructure_type']).lower() else 0,
                1 if row['infrastructure_type'] and 'server' in str(row['infrastructure_type']).lower() else 0,
                row['data_quality_score'] if row['data_quality_score'] else 0,
                row['source_count'] if row['source_count'] else 0,
                1 if row['cio'] else 0
            ]
            
            combined_features = np.concatenate([hostname_features, additional_features])
            features.append(combined_features)
            
            existence_score = min(sum([
                1 if row['logging_in_splunk'] == 'yes' else 0,
                1 if row['present_in_cmdb'] == 'yes' else 0,
                1 if row['edr_coverage'] and 'crowdstrike agent' in str(row['edr_coverage']).lower() else 0
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
        df = self.get_cmdb_data()
        X, existence_y, visibility_y = self.prepare_training_data(df)
        
        X = self.feature_scaler.fit_transform(X)
        
        X_tensor = torch.FloatTensor(X).to(device)
        existence_y_tensor = torch.FloatTensor(existence_y.reshape(-1, 1)).to(device)
        visibility_y_tensor = torch.LongTensor(visibility_y).to(device)
        
        self.hostname_net = HostnamePatternNet(X.shape[1]).to(device)
        self.log_visibility_net = LogVisibilityPredictor(X.shape[1]).to(device)
        
        optimizer1 = optim.Adam(self.hostname_net.parameters(), lr=0.001, weight_decay=1e-5)
        optimizer2 = optim.Adam(self.log_visibility_net.parameters(), lr=0.001, weight_decay=1e-5)
        
        criterion1 = nn.BCELoss()
        criterion2 = nn.CrossEntropyLoss()
        
        for epoch in range(300):
            self.hostname_net.train()
            self.log_visibility_net.train()
            
            optimizer1.zero_grad()
            existence_outputs = self.hostname_net(X_tensor)
            loss1 = criterion1(existence_outputs, existence_y_tensor)
            loss1.backward()
            optimizer1.step()
            
            optimizer2.zero_grad()
            visibility_outputs = self.log_visibility_net(X_tensor)
            loss2 = criterion2(visibility_outputs, visibility_y_tensor)
            loss2.backward()
            optimizer2.step()
            
            if epoch % 50 == 0:
                print(f'Epoch {epoch}, Existence Loss: {loss1.item():.4f}, Visibility Loss: {loss2.item():.4f}')
        
        self.trained = True
    
    def predict_missing_assets(self, business_unit_filter=None):
        if not self.trained:
            return []
        
        df = self.get_cmdb_data()
        if business_unit_filter:
            df = df[df['business_unit'] == business_unit_filter]
        
        hostname_patterns = self.analyze_naming_patterns(df)
        predicted_assets = []
        
        for pattern in hostname_patterns:
            for i in range(1, 500):
                for padding in [2, 3, 4]:
                    potential_hostname = pattern['pattern'].replace('XXX', str(i).zfill(padding))
                    
                    if potential_hostname not in df['fqdn'].values:
                        features = self.extract_hostname_features(potential_hostname)
                        additional_features = [0, 1, 1, 0, 0, 0, 1, 5.0, 1, 1]
                        combined_features = np.concatenate([features, additional_features])
                        combined_features = self.feature_scaler.transform([combined_features])
                        
                        with torch.no_grad():
                            features_tensor = torch.FloatTensor(combined_features).to(device)
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
        
        return sorted(predicted_assets, key=lambda x: x['existence_probability'], reverse=True)[:150]
    
    def analyze_naming_patterns(self, df):
        patterns = []
        
        for bu in df['business_unit'].dropna().unique():
            bu_df = df[df['business_unit'] == bu]
            
            for hostname in bu_df['fqdn']:
                if not hostname:
                    continue
                
                base_pattern = re.sub(r'\d+', 'XXX', hostname.lower())
                
                similar_count = sum(1 for h in bu_df['fqdn'] if h and re.sub(r'\d+', 'XXX', h.lower()) == base_pattern)
                
                if similar_count >= 2:
                    patterns.append({
                        'pattern': base_pattern,
                        'base_pattern': base_pattern,
                        'business_unit': bu,
                        'count': similar_count
                    })
        
        return list({p['base_pattern']: p for p in patterns}.values())
    
    def classify_role(self, hostname):
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
            return 'Network'
        else:
            return 'Endpoint'
    
    def predict_log_types(self, hostname):
        hostname_lower = hostname.lower()
        log_types = []
        
        if any(keyword in hostname_lower for keyword in ['fw', 'firewall']):
            log_types.extend(['Firewall Traffic', 'IDS/IPS', 'NDR'])
        elif any(keyword in hostname_lower for keyword in ['web', 'www', 'app']):
            log_types.extend(['Web Logs', 'HTTP Access'])
        elif any(keyword in hostname_lower for keyword in ['db', 'database', 'sql']):
            log_types.extend(['OS logs', 'Theom', 'Cloud Event'])
        elif any(keyword in hostname_lower for keyword in ['srv', 'server']):
            log_types.extend(['OS logs', 'EDR', 'DLP'])
        else:
            log_types.extend(['OS logs', 'EDR'])
        
        return log_types
    
    def calculate_visibility_risk(self, hostname, existence_prob, visibility_probs):
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

app = Flask(__name__)
ao1_predictor = AO1VisibilityPredictor()

@app.route('/api/train-visibility-model')
def train_visibility_model():
    try:
        threading.Thread(target=ao1_predictor.train_models, daemon=True).start()
        return jsonify({'status': 'training_started', 'message': 'AO1 visibility model training initiated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility')
def predict_missing_visibility():
    try:
        predictions = ao1_predictor.predict_missing_assets()
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-missing-visibility/<business_unit>')
def predict_missing_visibility_bu(business_unit):
    try:
        predictions = ao1_predictor.predict_missing_assets(business_unit)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/visibility-model-status')
def visibility_model_status():
    return jsonify({
        'trained': ao1_predictor.trained,
        'device': str(device),
        'last_training': datetime.now().isoformat() if ao1_predictor.trained else None
    })

@app.route('/api/visibility-gap-analysis')
def visibility_gap_analysis():
    try:
        predictions = ao1_predictor.predict_missing_assets()
        
        analysis = {
            'critical_visibility_gaps': [p for p in predictions if p['visibility_risk_score'] > 0.8],
            'high_value_targets': [p for p in predictions if p['predicted_role'] in ['Server', 'Database', 'Network']],
            'splunk_gaps': [p for p in predictions if p['splunk_probability'] < 0.5],
            'gso_gaps': [p for p in predictions if p['gso_probability'] < 0.5],
            'total_predicted_assets': len(predictions),
            'avg_existence_probability': np.mean([p['existence_probability'] for p in predictions]) if predictions else 0,
            'pattern_coverage': len(set([p['pattern_family'] for p in predictions]))
        }
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)