from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np
from collections import Counter

class DBSCANClusterer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.cluster_properties = {}
        self.feature_to_cluster = {}
        
    def train(self, df, existing_assets):
        X = []
        hostnames = []
        
        for hostname in existing_assets.keys():
            features = self._extract_features(hostname)
            X.append(features)
            hostnames.append(hostname)
        
        if X:
            X = np.array(X)
            X_scaled = self.scaler.fit_transform(X)
            
            self.model = DBSCAN(eps=0.5, min_samples=3)
            clusters = self.model.fit_predict(X_scaled)
            
            for i, (hostname, cluster_id) in enumerate(zip(hostnames, clusters)):
                if cluster_id != -1:
                    if cluster_id not in self.cluster_properties:
                        self.cluster_properties[cluster_id] = []
                    
                    self.cluster_properties[cluster_id].append(existing_assets[hostname])
                    self.feature_to_cluster[tuple(X[i])] = cluster_id
    
    def _extract_features(self, hostname):
        features = []
        
        features.append(len(hostname))
        features.append(hostname.count('.'))
        features.append(hostname.count('-'))
        features.append(hostname.count('_'))
        
        segments = hostname.replace('.', '-').replace('_', '-').split('-')
        features.append(len(segments))
        features.append(max([len(s) for s in segments]) if segments else 0)
        features.append(min([len(s) for s in segments]) if segments else 0)
        
        numeric_segments = sum(1 for s in segments if any(c.isdigit() for c in s))
        features.append(numeric_segments)
        
        alpha_segments = sum(1 for s in segments if s.isalpha())
        features.append(alpha_segments)
        
        features.append(1 if hostname.startswith('srv') or hostname.startswith('server') else 0)
        features.append(1 if 'prod' in hostname else 0)
        features.append(1 if 'dev' in hostname else 0)
        
        return np.array(features)
    
    def _find_nearest_cluster(self, features):
        if not self.feature_to_cluster:
            return None
        
        min_distance = float('inf')
        nearest_cluster = None
        
        for feature_tuple, cluster_id in self.feature_to_cluster.items():
            distance = np.linalg.norm(features - np.array(feature_tuple))
            if distance < min_distance:
                min_distance = distance
                nearest_cluster = cluster_id
        
        if min_distance < 2.0:
            return nearest_cluster
        return None
    
    def predict(self, candidate, existing_assets):
        if not self.model:
            return {'confidence': 0.0, 'properties': {}, 'algorithm': 'DBSCANClusterer'}
        
        hostname = candidate['hostname']
        features = self._extract_features(hostname)
        features_scaled = self.scaler.transform([features])
        
        nearest_cluster = self._find_nearest_cluster(features)
        
        confidence = 0.0
        properties = {}
        
        if nearest_cluster is not None and nearest_cluster in self.cluster_properties:
            cluster_size = len(self.cluster_properties[nearest_cluster])
            confidence = min(0.3 + (cluster_size / 100), 0.9)
            
            property_votes = {
                'domain': Counter(),
                'region': Counter(),
                'country': Counter(),
                'business_unit': Counter(),
                'data_center': Counter()
            }
            
            for asset_props in self.cluster_properties[nearest_cluster][:30]:
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
            'algorithm': 'DBSCANClusterer'
        }