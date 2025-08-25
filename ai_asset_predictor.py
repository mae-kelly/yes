# /src/ml/ao1_visibility_intelligence.py
# AO1 Log Visibility Measurement - AI-Powered Cybersecurity Visibility Intelligence

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
import json

if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("🚀 AO1 Visibility Intelligence - Using Apple Silicon GPU (MPS)")
else:
    print("❌ ERROR: GPU acceleration required for AO1 Visibility Intelligence")
    exit(1)

# AO1 ROLE-BASED LOG TYPE MAPPINGS (FROM PROJECT REQUIREMENTS)
AO1_ROLE_LOG_MAPPING = {
    'Network': {
        'log_types': ['Firewall Traffic', 'IDS/IPS', 'NDR', 'Proxy', 'DNS', 'WAF'],
        'data_fields': ['IP (source, target)', 'Protocol', 'Detection Signature', 'Port', 'DNS record/FQDN', 'HTTP Headers'],
        'visibility_factors': ['URL/FQDN coverage', 'CMDB Asset Visibility', 'Network Zones/spans', 'IPAM Public IP Coverage', 'Geolocation', 'VPC', '%log ingest volume'],
        'critical_for_detection': True,
        'compliance_weight': 0.9
    },
    'Endpoint': {
        'log_types': ['OS logs (WinEVT, Linux syslog)', 'EDR', 'DLP', 'FIM'],
        'data_fields': ['system name', 'IP', 'filename'],
        'visibility_factors': ['CMDB Asset Visibility', 'Crowdstrike Agent Coverage', '%log ingest volume'],
        'critical_for_detection': True,
        'compliance_weight': 0.85
    },
    'Cloud': {
        'log_types': ['Cloud Event', 'Cloud Load Balancer', 'Cloud Config', 'Theom', 'Wiz', 'Cloud Security'],
        'data_fields': ['VPC', 'IPAM Public IP Coverage', 'URL/FQDN coverage'],
        'visibility_factors': ['VPC', 'IPAM Public IP Coverage', 'URL/FQDN coverage', 'Crowdstrike Agent Coverage'],
        'critical_for_detection': True,
        'compliance_weight': 0.8
    },
    'Application': {
        'log_types': ['Web Logs (HTTP Access)', 'API Gateway'],
        'data_fields': ['URL/FQDN coverage', 'Control Coverage'],
        'visibility_factors': ['URL/FQDN coverage', 'Control Coverage'],
        'critical_for_detection': False,
        'compliance_weight': 0.7
    },
    'Identity_Auth': {
        'log_types': ['Authentication attempts', 'Privilege escalation', 'Identity create/modify/destroy'],
        'data_fields': ['Domain', 'Internal', 'External', 'Controls'],
        'visibility_factors': ['Domain', 'Internal', 'External', 'Controls'],
        'critical_for_detection': True,
        'compliance_weight': 0.95
    }
}

# AO1 INFRASTRUCTURE TYPE CLASSIFICATIONS
AO1_INFRASTRUCTURE_TYPES = ['On-Prem', 'Cloud', 'SaaS', 'API']

# AO1 SYSTEM CLASSIFICATIONS  
AO1_SYSTEM_CLASSIFICATIONS = ['Web Server', 'Windows Server', 'Linux Server', '*Nix (AIX, Solaris, etc)', 
                              'Mainframe', 'Database', 'Network Appliance (FW, NDR, switch, router, etc)']

class AO1VisibilityIntelligenceNet(nn.Module):
    def __init__(self, input_size: int):
        super().__init__()
        # Specialized architecture for cybersecurity visibility prediction
        self.role_classifier = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, len(AO1_ROLE_LOG_MAPPING)),
            nn.Softmax(dim=1)
        )
        
        self.visibility_predictor = nn.Sequential(
            nn.Linear(input_size + len(AO1_ROLE_LOG_MAPPING), 256),
            nn.ReLU(), 
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 7),  # Splunk, GSO, Chronicle, EDR, Tanium, DLP, CMDB
            nn.Sigmoid()
        )
        
        self.risk_assessor = nn.Sequential(
            nn.Linear(input_size + len(AO1_ROLE_LOG_MAPPING) + 7, 128),
            nn.ReLU(),
            nn.Linear(128, 64), 
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        role_probs = self.role_classifier(x)
        
        # Concatenate role predictions with original features
        visibility_input = torch.cat([x, role_probs], dim=1)
        visibility_probs = self.visibility_predictor(visibility_input)
        
        # Risk assessment using all features
        risk_input = torch.cat([x, role_probs, visibility_probs], dim=1)
        risk_score = self.risk_assessor(risk_input)
        
        return role_probs, visibility_probs, risk_score

class AO1VisibilityIntelligenceSystem:
    def __init__(self, db_path: str = 'universal_cmdb.db'):
        self.model = None
        self.feature_scaler = StandardScaler()
        self.trained = False
        self.db_path = db_path
        self.model_version = "AO1-2025.1"
        self.training_metrics = {}
        self.model_dir = 'models'
        
        # AO1-specific configuration
        self.ao1_config = {
            'min_confidence_threshold': 0.75,
            'critical_roles_weight': 1.5,
            'compliance_threshold': 0.8,
            'visibility_gap_threshold': 0.6
        }
        
        os.makedirs(self.model_dir, exist_ok=True)
        print("🔒 AO1 Log Visibility Intelligence System Initialized")
        
    @property
    def models_exist(self) -> bool:
        required_files = [f'{self.model_dir}/ao1_visibility_model.pth', f'{self.model_dir}/ao1_scaler.pkl']
        return all(os.path.exists(f) for f in required_files)

    def get_db_connection(self):
        try:
            return duckdb.connect(self.db_path)
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None

    def extract_ao1_features(self, host: str, cmdb_data: pd.Series) -> np.ndarray:
        """Extract AO1-specific cybersecurity visibility features"""
        if not host:
            host = ""
        
        host = str(host).lower().strip()
        features = []
        
        # Basic hostname analysis
        features.extend([
            len(host),
            host.count('.'),
            host.count('-'),
            len(re.findall(r'\d', host)),
            len(re.findall(r'[a-z]', host))
        ])
        
        # AO1 Infrastructure Type Classification
        infra_type = str(cmdb_data.get('infrastructure_type', '')).lower()
        for ao1_type in AO1_INFRASTRUCTURE_TYPES:
            features.append(1 if ao1_type.lower() in infra_type else 0)
        
        # AO1 System Classification Detection
        sys_class = str(cmdb_data.get('system_classification', '')).lower()
        for ao1_sys in AO1_SYSTEM_CLASSIFICATIONS:
            key_words = ao1_sys.lower().split()
            features.append(1 if any(word in sys_class or word in host for word in key_words) else 0)
        
        # AO1 Role-based Detection Patterns
        network_indicators = ['fw', 'firewall', 'proxy', 'dns', 'waf', 'ids', 'ips', 'ndr']
        endpoint_indicators = ['srv', 'server', 'desktop', 'laptop', 'workstation']
        cloud_indicators = ['aws', 'azure', 'gcp', 'cloud', 'ec2', 'vm']
        app_indicators = ['web', 'www', 'app', 'api', 'gateway']
        auth_indicators = ['ad', 'ldap', 'auth', 'sso', 'identity']
        
        features.extend([
            1 if any(ind in host for ind in network_indicators) else 0,
            1 if any(ind in host for ind in endpoint_indicators) else 0,
            1 if any(ind in host for ind in cloud_indicators) else 0,
            1 if any(ind in host for ind in app_indicators) else 0,
            1 if any(ind in host for ind in auth_indicators) else 0
        ])
        
        # AO1 Business Context
        features.extend([
            1 if pd.notna(cmdb_data.get('business_unit')) else 0,
            1 if pd.notna(cmdb_data.get('cio')) else 0,
            1 if pd.notna(cmdb_data.get('apm')) else 0,
            float(cmdb_data.get('data_quality_score', 0)) / 10.0,  # Normalize to 0-1
            min(int(cmdb_data.get('source_count', 0)) / 10.0, 1.0)  # Cap at 1.0
        ])
        
        # AO1 Geographic/Regional Indicators
        region = str(cmdb_data.get('region', '')).lower()
        country = str(cmdb_data.get('country', '')).lower()
        dc = str(cmdb_data.get('data_center', '')).lower()
        
        features.extend([
            1 if any(geo in region or geo in country for geo in ['us', 'america', 'north']) else 0,
            1 if any(geo in region or geo in country for geo in ['eu', 'europe', 'emea']) else 0,
            1 if any(geo in region or geo in country for geo in ['apac', 'asia']) else 0,
            1 if 'prod' in host or 'production' in str(cmdb_data.get('infrastructure_type', '')).lower() else 0
        ])
        
        return np.array(features, dtype=np.float32)

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
        LIMIT 400000
        """
        
        try:
            df = conn.execute(query).df()
            print(f"📊 Loaded {len(df):,} assets for AO1 visibility analysis")
            return df
        except Exception as e:
            print(f"❌ Error loading CMDB data: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def prepare_ao1_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training data specifically for AO1 visibility intelligence"""
        features = []
        role_labels = []
        visibility_labels = []
        risk_labels = []
        
        print(f"🔄 Processing {len(df):,} assets for AO1 training...")
        
        role_mapping = {role: idx for idx, role in enumerate(AO1_ROLE_LOG_MAPPING.keys())}
        
        for idx, row in df.iterrows():
            if idx % 50000 == 0:
                print(f"   Processed {idx:,} assets...")
            
            # Extract AO1-specific features
            ao1_features = self.extract_ao1_features(row['host'], row)
            features.append(ao1_features)
            
            # Determine primary role based on AO1 classification
            role = self.classify_ao1_role(row['host'], row)
            role_label = np.zeros(len(AO1_ROLE_LOG_MAPPING))
            if role in role_mapping:
                role_label[role_mapping[role]] = 1.0
            role_labels.append(role_label)
            
            # AO1 Visibility Assessment (7 categories)
            visibility = self.assess_ao1_visibility(row)
            visibility_labels.append(visibility)
            
            # AO1 Risk Assessment
            risk_score = self.calculate_ao1_risk(row['host'], row, role, visibility)
            risk_labels.append(risk_score)
        
        print(f"✅ Prepared {len(features):,} training samples for AO1 Intelligence")
        return (np.array(features, dtype=np.float32), 
                np.array(role_labels, dtype=np.float32),
                np.array(visibility_labels, dtype=np.float32), 
                np.array(risk_labels, dtype=np.float32))

    def classify_ao1_role(self, host: str, cmdb_data: pd.Series) -> str:
        """Classify asset role according to AO1 requirements"""
        host = str(host).lower()
        sys_class = str(cmdb_data.get('system_classification', '')).lower()
        infra_type = str(cmdb_data.get('infrastructure_type', '')).lower()
        
        # Network role detection (highest priority for security)
        if any(indicator in host or indicator in sys_class for indicator in 
               ['firewall', 'fw', 'proxy', 'dns', 'waf', 'ids', 'ips', 'ndr', 'router', 'switch']):
            return 'Network'
        
        # Identity & Authentication
        if any(indicator in host for indicator in ['ad', 'ldap', 'auth', 'sso', 'identity']):
            return 'Identity_Auth'
        
        # Cloud detection
        if ('cloud' in infra_type or 
            any(indicator in host for indicator in ['aws', 'azure', 'gcp', 'cloud', 'ec2'])):
            return 'Cloud'
        
        # Application detection
        if any(indicator in host for indicator in ['web', 'www', 'app', 'api', 'gateway']):
            return 'Application'
        
        # Default to Endpoint
        return 'Endpoint'

    def assess_ao1_visibility(self, row: pd.Series) -> np.ndarray:
        """Assess current visibility across AO1 platforms"""
        visibility = np.zeros(7, dtype=np.float32)
        
        # Splunk visibility
        visibility[0] = 1.0 if row.get('logging_in_splunk') == 'yes' else 0.0
        
        # GSO visibility  
        visibility[1] = 1.0 if row.get('logging_in_gso') == 'yes' else 0.0
        
        # Chronicle (inferred from modern logging practices)
        visibility[2] = 0.8 if (row.get('logging_in_splunk') == 'yes' and 
                               row.get('logging_in_gso') == 'yes') else 0.0
        
        # EDR Coverage (Crowdstrike)
        edr = str(row.get('edr_coverage', '')).lower()
        visibility[3] = 1.0 if 'crowdstrike' in edr or 'agent' in edr else 0.0
        
        # Tanium Coverage
        visibility[4] = 1.0 if row.get('tanium_coverage') == 'yes' else 0.0
        
        # DLP Coverage  
        visibility[5] = 1.0 if row.get('dlp_agent_coverage') == 'yes' else 0.0
        
        # CMDB Presence
        visibility[6] = 1.0 if row.get('present_in_cmdb') == 'yes' else 0.0
        
        return visibility

    def calculate_ao1_risk(self, host: str, cmdb_data: pd.Series, role: str, visibility: np.ndarray) -> float:
        """Calculate cybersecurity risk based on AO1 methodology"""
        base_risk = 0.0
        
        # Role-based risk weighting (from AO1 requirements)
        role_weights = {
            'Network': 0.95,      # Critical for detection
            'Identity_Auth': 0.9, # Critical for detection  
            'Endpoint': 0.85,     # Critical for detection
            'Cloud': 0.8,         # Critical for detection
            'Application': 0.7    # Less critical
        }
        
        base_risk = role_weights.get(role, 0.5)
        
        # Visibility gap penalty
        expected_visibility = AO1_ROLE_LOG_MAPPING.get(role, {}).get('compliance_weight', 0.8)
        actual_visibility = np.mean(visibility)
        visibility_gap = max(0, expected_visibility - actual_visibility)
        
        # Production environment multiplier
        prod_multiplier = 1.3 if 'prod' in str(host).lower() else 1.0
        
        # Data quality factor
        quality_factor = float(cmdb_data.get('data_quality_score', 5)) / 10.0
        
        final_risk = min(base_risk + (visibility_gap * 0.4) * prod_multiplier * quality_factor, 1.0)
        return final_risk

    def train_ao1_intelligence(self):
        """Train the AO1 Visibility Intelligence model"""
        print("🚀 Starting AO1 Visibility Intelligence Training...")
        
        df = self.get_cmdb_data()
        if df.empty:
            print("❌ No data available for training!")
            return
        
        X, role_y, visibility_y, risk_y = self.prepare_ao1_training_data(df)
        
        if len(X) == 0:
            print("❌ No features extracted!")
            return
        
        # Split data for training
        X_train, X_val, role_y_train, role_y_val, vis_y_train, vis_y_val, risk_y_train, risk_y_val = train_test_split(
            X, role_y, visibility_y, risk_y, test_size=0.15, random_state=42, stratify=risk_y > 0.7
        )
        
        # Memory cleanup
        del X, role_y, visibility_y, risk_y, df
        gc.collect()
        
        # Scale features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        # Initialize model
        input_size = X_train_scaled.shape[1]
        self.model = AO1VisibilityIntelligenceNet(input_size).to(device)
        
        optimizer = optim.AdamW(self.model.parameters(), lr=0.001, weight_decay=1e-4)
        
        role_criterion = nn.BCELoss()
        visibility_criterion = nn.BCELoss() 
        risk_criterion = nn.BCELoss()
        
        batch_size = 4096
        epochs = 150
        
        print(f"🔥 Training AO1 model: {len(X_train_scaled):,} samples, batch size {batch_size}")
        
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0
            
            # Training batches
            for i in range(0, len(X_train_scaled), batch_size):
                batch_end = min(i + batch_size, len(X_train_scaled))
                
                X_batch = torch.FloatTensor(X_train_scaled[i:batch_end]).to(device)
                role_batch = torch.FloatTensor(role_y_train[i:batch_end]).to(device)
                vis_batch = torch.FloatTensor(vis_y_train[i:batch_end]).to(device)
                risk_batch = torch.FloatTensor(risk_y_train[i:batch_end]).reshape(-1, 1).to(device)
                
                optimizer.zero_grad()
                
                role_pred, vis_pred, risk_pred = self.model(X_batch)
                
                loss_role = role_criterion(role_pred, role_batch)
                loss_vis = visibility_criterion(vis_pred, vis_batch)
                loss_risk = risk_criterion(risk_pred, risk_batch)
                
                # Weighted loss (prioritize risk assessment)
                total_loss_batch = loss_role + 2.0 * loss_vis + 3.0 * loss_risk
                
                total_loss_batch.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                
                total_loss += total_loss_batch.item()
                
                del X_batch, role_batch, vis_batch, risk_batch
                
                if i % (batch_size * 20) == 0:
                    gc.collect()
            
            if epoch % 25 == 0:
                print(f"🎯 Epoch {epoch}/{epochs}, Loss: {total_loss/len(X_train_scaled)*batch_size:.4f}")
        
        self.trained = True
        self.save_ao1_models()
        print("✅ AO1 Visibility Intelligence training completed!")

    def save_ao1_models(self):
        try:
            torch.save(self.model.state_dict(), f'{self.model_dir}/ao1_visibility_model.pth')
            with open(f'{self.model_dir}/ao1_scaler.pkl', 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            print("💾 AO1 models saved successfully!")
        except Exception as e:
            print(f"❌ Error saving models: {e}")

    def load_ao1_models(self):
        try:
            if not self.models_exist:
                return False
            
            # Determine input size
            sample_series = pd.Series({'host': 'sample', 'infrastructure_type': '', 'system_classification': ''})
            sample_features = self.extract_ao1_features('sample', sample_series)
            input_size = len(sample_features)
            
            self.model = AO1VisibilityIntelligenceNet(input_size).to(device)
            self.model.load_state_dict(torch.load(f'{self.model_dir}/ao1_visibility_model.pth', map_location=device))
            
            with open(f'{self.model_dir}/ao1_scaler.pkl', 'rb') as f:
                self.feature_scaler = pickle.load(f)
            
            self.trained = True
            print("✅ AO1 models loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False

    def generate_ao1_visibility_report(self) -> Dict:
        """Generate comprehensive AO1 visibility analysis report"""
        if not self.trained:
            if not self.load_ao1_models():
                return {'error': 'AO1 models not available'}
        
        print("📈 Generating AO1 Comprehensive Visibility Report...")
        
        df = self.get_cmdb_data()
        if df.empty:
            return {'error': 'No data available'}
        
        report = {
            'ao1_executive_summary': {},
            'visibility_by_role': {},
            'infrastructure_coverage': {},
            'regional_visibility': {},
            'security_control_gaps': {},
            'business_unit_analysis': {},
            'compliance_assessment': {},
            'remediation_priorities': [],
            'generated_timestamp': datetime.now().isoformat()
        }
        
        # Process all assets
        predictions = []
        for _, row in df.iterrows():
            features = self.extract_ao1_features(row['host'], row)
            features_scaled = self.feature_scaler.transform([features])
            
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features_scaled).to(device)
                role_pred, vis_pred, risk_pred = self.model(features_tensor)
                
                role_probs = role_pred.cpu().numpy()[0]
                vis_probs = vis_pred.cpu().numpy()[0]
                risk_score = risk_pred.cpu().item()
                
            predictions.append({
                'host': row['host'],
                'role': list(AO1_ROLE_LOG_MAPPING.keys())[np.argmax(role_probs)],
                'role_confidence': float(np.max(role_probs)),
                'visibility_scores': {
                    'Splunk': float(vis_probs[0]),
                    'GSO': float(vis_probs[1]), 
                    'Chronicle': float(vis_probs[2]),
                    'EDR': float(vis_probs[3]),
                    'Tanium': float(vis_probs[4]),
                    'DLP': float(vis_probs[5]),
                    'CMDB': float(vis_probs[6])
                },
                'risk_score': float(risk_score),
                'business_unit': row.get('business_unit', 'Unknown'),
                'infrastructure_type': row.get('infrastructure_type', 'Unknown'),
                'region': row.get('region', 'Unknown'),
                'actual_logging_in_splunk': row.get('logging_in_splunk', 'unknown'),
                'actual_logging_in_gso': row.get('logging_in_gso', 'unknown')
            })
        
        # Executive Summary
        total_assets = len(predictions)
        high_risk_assets = len([p for p in predictions if p['risk_score'] > 0.8])
        avg_visibility = np.mean([np.mean(list(p['visibility_scores'].values())) for p in predictions])
        
        report['ao1_executive_summary'] = {
            'total_assets_analyzed': total_assets,
            'high_risk_visibility_gaps': high_risk_assets,
            'overall_visibility_score': f"{avg_visibility:.1%}",
            'critical_findings': high_risk_assets,
            'compliance_status': 'NEEDS_ATTENTION' if avg_visibility < 0.8 else 'GOOD'
        }
        
        # Role-based Analysis
        role_stats = defaultdict(list)
        for pred in predictions:
            role_stats[pred['role']].append(pred)
        
        for role, role_preds in role_stats.items():
            role_config = AO1_ROLE_LOG_MAPPING[role]
            avg_vis = np.mean([np.mean(list(p['visibility_scores'].values())) for p in role_preds])
            high_risk_count = len([p for p in role_preds if p['risk_score'] > 0.8])
            
            report['visibility_by_role'][role] = {
                'asset_count': len(role_preds),
                'average_visibility': f"{avg_vis:.1%}",
                'high_risk_assets': high_risk_count,
                'expected_log_types': role_config['log_types'],
                'compliance_weight': role_config['compliance_weight'],
                'visibility_gap': f"{max(0, role_config['compliance_weight'] - avg_vis):.1%}"
            }
        
        # Security Control Gaps
        platform_gaps = {
            'Splunk': len([p for p in predictions if p['visibility_scores']['Splunk'] < 0.5]),
            'GSO': len([p for p in predictions if p['visibility_scores']['GSO'] < 0.5]),
            'EDR': len([p for p in predictions if p['visibility_scores']['EDR'] < 0.5]),
            'Tanium': len([p for p in predictions if p['visibility_scores']['Tanium'] < 0.5])
        }
        
        report['security_control_gaps'] = {
            'platform_coverage_gaps': platform_gaps,
            'total_gap_percentage': f"{sum(platform_gaps.values()) / (total_assets * 4):.1%}",
            'priority_platforms': sorted(platform_gaps.items(), key=lambda x: x[1], reverse=True)[:2]
        }
        
        # Business Unit Analysis
        bu_stats = defaultdict(list)
        for pred in predictions:
            bu_stats[pred['business_unit']].append(pred)
        
        for bu, bu_preds in bu_stats.items():
            if len(bu_preds) > 10:  # Only include BUs with significant asset count
                avg_vis = np.mean([np.mean(list(p['visibility_scores'].values())) for p in bu_preds])
                high_risk = len([p for p in bu_preds if p['risk_score'] > 0.8])
                
                report['business_unit_analysis'][bu] = {
                    'asset_count': len(bu_preds),
                    'visibility_score': f"{avg_vis:.1%}",
                    'high_risk_assets': high_risk,
                    'needs_attention': high_risk > len(bu_preds) * 0.2
                }
        
        # Top Remediation Priorities
        high_risk_assets = sorted([p for p in predictions if p['risk_score'] > 0.7], 
                                key=lambda x: x['risk_score'], reverse=True)[:20]
        
        for asset in high_risk_assets:
            gaps = []
            for platform, score in asset['visibility_scores'].items():
                if score < 0.5:
                    gaps.append(platform)
            
            report['remediation_priorities'].append({
                'hostname': asset['host'],
                'role': asset['role'],
                'risk_score': f"{asset['risk_score']:.1%}",
                'business_unit': asset['business_unit'],
                'visibility_gaps': gaps,
                'recommended_actions': self.get_ao1_recommendations(asset['role'], gaps)
            })
        
        print("✅ AO1 Comprehensive Visibility Report Generated!")
        return report

    def get_ao1_recommendations(self, role: str, gaps: List[str]) -> List[str]:
        """Generate specific remediation recommendations based on AO1 requirements"""
        recommendations = []
        
        role_config = AO1_ROLE_LOG_MAPPING.get(role, {})
        expected_logs = role_config.get('log_types', [])
        
        if 'Splunk' in gaps:
            recommendations.append(f"Configure {', '.join(expected_logs)} forwarding to Splunk")
        
        if 'GSO' in gaps:
            recommendations.append("Enable GSO logging collection for this asset")
        
        if 'EDR' in gaps and role in ['Endpoint', 'Network']:
            recommendations.append("Deploy Crowdstrike EDR agent")
        
        if 'Tanium' in gaps:
            recommendations.append("Install Tanium agent for enhanced visibility")
        
        if not recommendations:
            recommendations.append("Review log source configuration and data ingestion")
        
        return recommendations

# Flask Application
app = Flask(__name__)
ao1_system = AO1VisibilityIntelligenceSystem()

@app.route('/api/ao1/train-intelligence')
def train_ao1_intelligence():
    try:
        def train_async():
            ao1_system.train_ao1_intelligence()
        
        threading.Thread(target=train_async, daemon=True).start()
        return jsonify({
            'status': 'training_started',
            'message': 'AO1 Visibility Intelligence training initiated',
            'model_version': ao1_system.model_version,
            'device': str(device)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ao1/visibility-report')
def generate_ao1_report():
    try:
        report = ao1_system.generate_ao1_visibility_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ao1/status')
def ao1_status():
    return jsonify({
        'system': 'AO1 Log Visibility Intelligence',
        'version': ao1_system.model_version,
        'trained': ao1_system.trained,
        'device': str(device),
        'supported_roles': list(AO1_ROLE_LOG_MAPPING.keys()),
        'infrastructure_types': AO1_INFRASTRUCTURE_TYPES,
        'system_classifications': AO1_SYSTEM_CLASSIFICATIONS
    })

@app.route('/api/ao1/role-requirements')
def ao1_role_requirements():
    return jsonify(AO1_ROLE_LOG_MAPPING)

if __name__ == '__main__':
    print("🔐 Starting AO1 Log Visibility Intelligence System...")
    
    if ao1_system.models_exist:
        ao1_system.load_ao1_models()
    
    if not ao1_system.trained:
        print("⚠️  AO1 models not ready. Use /api/ao1/train-intelligence to train.")
    else:
        print("✅ AO1 Visibility Intelligence System Ready!")
    
    app.run(debug=True, port=5001, host='0.0.0.0')