from sklearn.ensemble import GradientBoostingClassifier
import numpy as np
from collections import Counter

class GradientBoostPredictor:
    def __init__(self):
        self.model = None
        self.property_patterns = {}
        
    def train(self, df, existing_assets):
        X = []
        y = []
        
        for hostname in existing_assets.keys():
            features = self._extract_features(hostname)
            X.append(features)
            y.append(1)
            
            pattern_key = self._get_pattern_key(hostname)
            if pattern_key not in self.property_patterns:
                self.property_patterns[pattern_key] = []
            self.property_patterns[pattern_key].append(existing_assets[hostname])
        
        if X:
            X = np.array(X)
            
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
            self.model.fit(X, y)
    
    def _extract_features(self, hostname):
        features = []
        
        features.append(len(hostname))
        features.append(hostname.count('.'))
        features.append(hostname.count('-'))
        features.append(hostname.count('_'))
        
        numeric_chars = len([c for c in hostname if c.isdigit()])
        alpha_chars = len([c for c in hostname if c.isalpha()])
        features.append(numeric_chars)
        features.append(alpha_chars)
        features.append(numeric_chars / (alpha_chars + 1))
        
        parts = hostname.split('.')
        features.append(len(parts))
        
        if parts:
            features.append(len(parts[0]))
            features.append(1 if parts[0].isalpha() else 0)
            features.append(1 if any(c.isdigit() for c in parts[0]) else 0)
        else:
            features.extend([0, 0, 0])
        
        segments = hostname.replace('.', '-').replace('_', '-').split('-')
        features.append(len(segments))
        features.append(max([len(s) for s in segments]) if segments else 0)
        features.append(min([len(s) for s in segments]) if segments else 0)
        
        features.append(1 if hostname.startswith(('srv', 'server', 'web', 'db')) else 0)
        features.append(1 if any(env in hostname for env in ['prod', 'dev', 'test', 'stage']) else 0)
        
        return np.array(features)
    
    def _get_pattern_key(self, hostname):
        import re
        pattern = re.sub(r'\d+', 'N', hostname)
        pattern = pattern[:20]
        return pattern
    
    def predict(self, candidate, existing_assets):
        if not self.model:
            return {'confidence': 0.0, 'properties': {}, 'algorithm': 'GradientBoostPredictor'}
        
        hostname = candidate['hostname']
        features = self._extract_features(hostname)
        
        confidence = self.model.predict_proba([features])[0][1] if 1 in self.model.classes_ else 0.0
        
        properties = {}
        pattern_key = self._get_pattern_key(hostname)
        
        similar_patterns = []
        for key in self.property_patterns:
            if self._pattern_similarity(key, pattern_key) > 0.7:
                similar_patterns.extend(self.property_patterns[key][:10])
        
        if similar_patterns:
            property_votes = {
                'domain': Counter(),
                'region': Counter(),
                'country': Counter(),
                'business_unit': Counter(),
                'data_center': Counter()
            }
            
            for asset_props in similar_patterns:
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
            'algorithm': 'GradientBoostPredictor'
        }
    
    def _pattern_similarity(self, pattern1, pattern2):
        if not pattern1 or not pattern2:
            return 0.0
        
        matches = sum(1 for c1, c2 in zip(pattern1, pattern2) if c1 == c2)
        return matches / max(len(pattern1), len(pattern2))