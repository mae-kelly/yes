from sklearn.ensemble import IsolationForest
import numpy as np
from collections import Counter

class IsolationForestDetector:
    def __init__(self):
        self.model = None
        self.feature_patterns = {}
        self.property_clusters = {}
        
    def train(self, df, existing_assets):
        X = []
        hostnames = []
        
        for hostname in existing_assets.keys():
            features = self._extract_features(hostname)
            X.append(features)
            hostnames.append(hostname)
        
        if X:
            X = np.array(X)
            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.model.fit(X)
            
            scores = self.model.decision_function(X)
            
            for i, (hostname, score) in enumerate(zip(hostnames, scores)):
                feature_key = self._get_feature_key(X[i])
                if feature_key not in self.feature_patterns:
                    self.feature_patterns[feature_key] = []
                self.feature_patterns[feature_key].append({
                    'hostname': hostname,
                    'score': score,
                    'properties': existing_assets[hostname]
                })
    
    def _extract_features(self, hostname):
        features = []
        
        features.append(len(hostname))
        features.append(hostname.count('.'))
        features.append(hostname.count('-'))
        features.append(len([c for c in hostname if c.isdigit()]))
        
        parts = hostname.split('.')
        features.append(len(parts))
        features.append(len(parts[0]) if parts else 0)
        
        has_numbers = any(c.isdigit() for c in hostname)
        features.append(1 if has_numbers else 0)
        
        prefix_len = len(hostname.split('-')[0]) if '-' in hostname else len(hostname)
        features.append(prefix_len)
        
        return np.array(features)
    
    def _get_feature_key(self, features):
        return tuple(features.astype(int))
    
    def predict(self, candidate, existing_assets):
        if not self.model:
            return {'confidence': 0.0, 'properties': {}, 'algorithm': 'IsolationForestDetector'}
        
        hostname = candidate['hostname']
        features = self._extract_features(hostname)
        
        score = self.model.decision_function([features])[0]
        prediction = self.model.predict([features])[0]
        
        confidence = 1 / (1 + np.exp(-score)) if prediction == 1 else 1 / (1 + np.exp(score))
        
        feature_key = self._get_feature_key(features)
        properties = {}
        
        similar_patterns = []
        for key in self.feature_patterns:
            if np.linalg.norm(np.array(key) - features) < 3:
                similar_patterns.extend(self.feature_patterns[key])
        
        if similar_patterns:
            property_votes = {
                'domain': Counter(),
                'region': Counter(),
                'country': Counter(),
                'business_unit': Counter()
            }
            
            for pattern in similar_patterns[:20]:
                for prop in property_votes:
                    value = pattern['properties'].get(prop)
                    if value:
                        property_votes[prop][value] += 1
            
            for prop, counter in property_votes.items():
                if counter:
                    properties[prop] = counter.most_common(1)[0][0]
        
        return {
            'confidence': confidence,
            'properties': properties,
            'algorithm': 'IsolationForestDetector'
        }