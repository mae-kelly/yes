from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import numpy as np
from collections import Counter

class SVMClassifier:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.hostname_patterns = {}
        
    def train(self, df, existing_assets):
        X = []
        y = []
        
        for hostname in existing_assets.keys():
            features = self._extract_features(hostname)
            X.append(features)
            y.append(1)
            
            base_pattern = self._get_base_pattern(hostname)
            if base_pattern not in self.hostname_patterns:
                self.hostname_patterns[base_pattern] = []
            self.hostname_patterns[base_pattern].append({
                'hostname': hostname,
                'properties': existing_assets[hostname]
            })
        
        if X:
            X = np.array(X)
            X_scaled = self.scaler.fit_transform(X)
            
            self.model = SVC(kernel='rbf', probability=True, gamma='scale', random_state=42)
            self.model.fit(X_scaled, y)
    
    def _extract_features(self, hostname):
        features = []
        
        features.append(len(hostname))
        features.append(hostname.count('.'))
        features.append(hostname.count('-'))
        features.append(hostname.count('_'))
        
        parts = hostname.split('.')
        features.append(len(parts))
        
        if parts:
            features.append(len(parts[0]))
            features.append(len(parts[-1]) if len(parts) > 1 else 0)
        else:
            features.extend([0, 0])
        
        segments = hostname.replace('.', '-').replace('_', '-').split('-')
        features.append(len(segments))
        
        numeric_segments = sum(1 for s in segments if any(c.isdigit() for c in s))
        alpha_segments = sum(1 for s in segments if s.isalpha())
        features.append(numeric_segments)
        features.append(alpha_segments)
        
        features.append(1 if hostname[:3].isalpha() else 0)
        features.append(1 if hostname[-3:].isalpha() else 0)
        
        keywords = ['srv', 'server', 'web', 'db', 'app', 'prod', 'dev', 'test']
        keyword_count = sum(1 for kw in keywords if kw in hostname.lower())
        features.append(keyword_count)
        
        has_domain = 1 if hostname.count('.') >= 1 else 0
        features.append(has_domain)
        
        digit_ratio = len([c for c in hostname if c.isdigit()]) / len(hostname) if hostname else 0
        features.append(digit_ratio)
        
        return np.array(features)
    
    def _get_base_pattern(self, hostname):
        import re
        pattern = re.sub(r'\d+', '#', hostname)
        pattern = re.sub(r'##+', '#', pattern)
        return pattern[:30]
    
    def predict(self, candidate, existing_assets):
        if not self.model:
            return {'confidence': 0.0, 'properties': {}, 'algorithm': 'SVMClassifier'}
        
        hostname = candidate['hostname']
        features = self._extract_features(hostname)
        features_scaled = self.scaler.transform([features])
        
        decision_score = self.model.decision_function(features_scaled)[0]
        confidence = self.model.predict_proba(features_scaled)[0][1] if 1 in self.model.classes_ else 0.0
        
        confidence = (confidence + (1 / (1 + np.exp(-decision_score)))) / 2
        
        properties = {}
        base_pattern = self._get_base_pattern(hostname)
        
        matching_patterns = []
        for pattern, hosts in self.hostname_patterns.items():
            similarity = self._calculate_pattern_similarity(pattern, base_pattern)
            if similarity > 0.6:
                matching_patterns.extend(hosts[:15])
        
        if matching_patterns:
            property_votes = {
                'domain': Counter(),
                'region': Counter(),
                'country': Counter(),
                'business_unit': Counter(),
                'data_center': Counter(),
                'cloud_region': Counter()
            }
            
            for pattern_info in matching_patterns:
                for prop in property_votes:
                    value = pattern_info['properties'].get(prop)
                    if value:
                        property_votes[prop][value] += 1
            
            for prop, counter in property_votes.items():
                if counter:
                    properties[prop] = counter.most_common(1)[0][0]
        
        return {
            'confidence': confidence,
            'properties': properties,
            'algorithm': 'SVMClassifier'
        }
    
    def _calculate_pattern_similarity(self, pattern1, pattern2):
        if not pattern1 or not pattern2:
            return 0.0
        
        min_len = min(len(pattern1), len(pattern2))
        matches = sum(1 for i in range(min_len) if pattern1[i] == pattern2[i])
        
        return matches / max(len(pattern1), len(pattern2))