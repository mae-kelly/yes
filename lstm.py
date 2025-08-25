import torch
import torch.nn as nn
import numpy as np
from sklearn.preprocessing import StandardScaler

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_size * 2, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        lstm_out, _ = self.lstm(x)
        output = self.fc(lstm_out[:, -1, :])
        return self.sigmoid(output)

class LSTMPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.trained = False
        self.property_mapping = {}
        
    def train(self, df, existing_assets):
        X = []
        for hostname in existing_assets.keys():
            features = self._extract_features(hostname)
            X.append(features)
            
            for prop in ['domain', 'region', 'country']:
                value = existing_assets[hostname].get(prop)
                if value and prop not in self.property_mapping:
                    self.property_mapping[prop] = {}
                if value and value not in self.property_mapping[prop]:
                    self.property_mapping[prop][value] = []
                if value:
                    self.property_mapping[prop][value].append(features)
        
        if X:
            X = np.array(X)
            X_scaled = self.scaler.fit_transform(X)
            
            self.model = LSTMModel(X.shape[1]).to(device)
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            criterion = nn.BCELoss()
            
            X_tensor = torch.FloatTensor(X_scaled).to(device)
            y_tensor = torch.ones(len(X), 1).to(device)
            
            self.model.train()
            for epoch in range(20):
                optimizer.zero_grad()
                outputs = self.model(X_tensor)
                loss = criterion(outputs, y_tensor)
                loss.backward()
                optimizer.step()
            
            self.trained = True
    
    def _extract_features(self, hostname):
        features = [
            len(hostname),
            hostname.count('.'),
            hostname.count('-'),
            hostname.count('_'),
            len([c for c in hostname if c.isdigit()]),
            len([c for c in hostname if c.isalpha()]),
            1 if hostname[0].isdigit() else 0,
            1 if hostname[-1].isdigit() else 0
        ]
        
        for char in 'abcdefghijklmnopqrstuvwxyz0123456789.-_':
            features.append(hostname.count(char))
        
        return np.array(features[:50])
    
    def predict(self, candidate, existing_assets):
        if not self.trained:
            return {'confidence': 0.0, 'properties': {}, 'algorithm': 'LSTMPredictor'}
        
        hostname = candidate['hostname']
        features = self._extract_features(hostname)
        features_scaled = self.scaler.transform([features])
        features_tensor = torch.FloatTensor(features_scaled).to(device)
        
        self.model.eval()
        with torch.no_grad():
            confidence = self.model(features_tensor).cpu().item()
        
        properties = {}
        for prop, value_features in self.property_mapping.items():
            best_match = None
            best_similarity = -1
            
            for value, feature_list in value_features.items():
                if feature_list:
                    avg_features = np.mean(feature_list, axis=0)
                    similarity = 1 / (1 + np.linalg.norm(features - avg_features))
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = value
            
            if best_match:
                properties[prop] = best_match
        
        return {
            'confidence': confidence,
            'properties': properties,
            'algorithm': 'LSTMPredictor'
        }