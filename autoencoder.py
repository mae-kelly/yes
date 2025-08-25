import torch
import torch.nn as nn
import numpy as np
from sklearn.preprocessing import StandardScaler
from collections import Counter

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

class Autoencoder(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8)
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim)
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

class AutoencoderDetector:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = None
        self.feature_property_map = {}
        
    def train(self, df, existing_assets):
        X = []
        hostnames = []
        
        for hostname in existing_assets.keys():
            features = self._extract_features(hostname)
            X.append(features)
            hostnames.append(hostname)
            
            feature_key = tuple(features[:5].astype(int))
            if feature_key not in self.feature_property_map:
                self.feature_property_map[feature_key] = []
            self.feature_property_map[feature_key].append(existing_assets[hostname])
        
        if X:
            X = np.array(X)
            X_scaled = self.scaler.fit_transform(X)
            
            self.model = Autoencoder(X.shape[1]).to(device)
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            X_tensor = torch.FloatTensor(X_scaled).to(device)
            
            self.model.train()
            for epoch in range(30):
                optimizer.zero_grad()
                reconstructed = self.model(X_tensor)
                loss = criterion(reconstructed, X_tensor)
                loss.backward()
                optimizer.step()
            
            self.model.eval()
            with torch.no_grad():
                reconstructed = self.model(X_tensor)
                errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1).cpu().numpy()
            
            self.threshold = np.percentile(errors, 95)
    
    def _extract_features(self, hostname):
        features = []
        
        features.append(len(hostname))
        features.append(hostname.count('.'))
        features.append(hostname.count('-'))
        features.append(hostname.count('_'))
        features.append(len([c for c in hostname if c.isdigit()]))
        features.append(len([c for c in hostname if c.isalpha()]))
        
        parts = hostname.split('.')
        features.append(len(parts))
        features.append(len(parts[0]) if parts else 0)
        
        segments = hostname.replace('.', '-').replace('_', '-').split('-')
        features.append(len(segments))
        features.append(np.mean([len(s) for s in segments]) if segments else 0)
        
        return np.array(features[:20])
    
    def predict(self, candidate, existing_assets):
        if not self.model or self.threshold is None:
            return {'confidence': 0.0, 'properties': {}, 'algorithm': 'AutoencoderDetector'}
        
        hostname = candidate['hostname']
        features = self._extract_features(hostname)
        features_scaled = self.scaler.transform([features])
        features_tensor = torch.FloatTensor(features_scaled).to(device)
        
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(features_tensor)
            error = torch.mean((features_tensor - reconstructed) ** 2).cpu().item()
        
        confidence = 0.0
        if error < self.threshold:
            confidence = 1.0 - (error / self.threshold)
            confidence = min(confidence, 0.95)
        
        properties = {}
        feature_key = tuple(features[:5].astype(int))
        
        similar_keys = []
        for key in self.feature_property_map:
            if np.linalg.norm(np.array(key) - features[:5]) < 2:
                similar_keys.append(key)
        
        if similar_keys:
            property_votes = {
                'domain': Counter(),
                'region': Counter(),
                'country': Counter(),
                'business_unit': Counter()
            }
            
            for key in similar_keys:
                for asset_props in self.feature_property_map[key][:10]:
                    for prop in property_votes:
                        value = asset_props.get(prop)
                        if value:
                            property_votes[prop][value] += 1
            
            for prop, counter in property_votes.items():
                if counter:
                    properties[prop] = counter.most_common(1)[0][0]
        
        return {
            'confidence': confidence,
            'properties': properties,
            'algorithm': 'AutoencoderDetector'
        }