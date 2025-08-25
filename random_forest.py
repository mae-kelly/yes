from sklearn.ensemble import RandomForestClassifier
import numpy as np
from collections import Counter

class RandomForestPredictor:
    def __init__(self):
        self.model = None
        self.property_models = {}
        self.label_encoders = {}
        
    def train(self, df, existing_assets):
        X = []
        y_exists = []
        y_properties = {
            'region': [],
            'country': [],
            'business_unit': []
        }
        
        for hostname in existing_assets.keys():
            features = self._extract_features(hostname)
            X.append(features)
            y_exists.append(1)
            
            for prop in y_properties:
                value = existing_assets[hostname].get(prop, 'unknown')
                y_properties[prop].append(value)
        
        if X and len(set(y_exists)) > 0:
            X = np.array(X)
            
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X, y_exists)
            
            for prop, values in y_properties.items():
                unique_values = list(set(values))
                if len(unique_values) > 1:
                    self.label_encoders[prop] = {v: i for i, v in enumerate(unique_values)}
                    encoded_values = [self.label_encoders[prop].get(v, 0) for v in values]
                    
                    self.property_models[prop] = RandomForestClassifier(n_estimators=50, random_state=42)
                    self.property_models[prop].fit(X, encoded_values)
    
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
        features.append(len(parts[-1]) if parts else 0)
        
        segments = hostname.replace('.', '-').replace('_', '-').split('-')
        features.append(len(segments))
        
        features.append(1 if any(s.isdigit() for s in segments) else 0)
        features.append(1 if 'srv' in hostname or 'server' in hostname else 0)
        features.append(1 if 'prod' in hostname else 0)
        features.append(1 if 'dev' in hostname else 0)
        features.append(1 if 'test' in hostname else 0)
        
        return np.array(features)
    
    def predict(self, candidate, existing_assets):
        if not self.model:
            return {'confidence': 0.0, 'properties': {}, 'algorithm': 'RandomForestPredictor'}
        
        hostname = candidate['hostname']
        features = self._extract_features(hostname)
        
        confidence = self.model.predict_proba([features])[0][1] if 1 in self.model.classes_ else 0.0
        
        properties = {}
        
        for prop, model in self.property_models.items():
            if prop in self.label_encoders:
                predicted_encoded = model.predict([features])[0]
                reverse_encoder = {v: k for k, v in self.label_encoders[prop].items()}
                if predicted_encoded in reverse_encoder:
                    properties[prop] = reverse_encoder[predicted_encoded]
        
        if candidate.get('similar_hosts'):
            property_votes = {'domain': Counter()}
            
            for similar_host in candidate['similar_hosts'][:5]:
                if similar_host in existing_assets:
                    domain = existing_assets[similar_host].get('domain')
                    if domain:
                        property_votes['domain'][domain] += 1
            
            if property_votes['domain']:
                properties['domain'] = property_votes['domain'].most_common(1)[0][0]
        
        return {
            'confidence': confidence,
            'properties': properties,
            'algorithm': 'RandomForestPredictor'
        }