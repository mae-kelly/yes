from collections import defaultdict, Counter
import numpy as np

class MarkovChainPredictor:
    def __init__(self):
        self.transitions = defaultdict(Counter)
        self.property_associations = {}
        
    def train(self, df, existing_assets):
        for hostname in existing_assets.keys():
            for i in range(len(hostname) - 1):
                current = hostname[i]
                next_char = hostname[i + 1]
                self.transitions[current][next_char] += 1
            
            segments = hostname.replace('.', '-').replace('_', '-').split('-')
            for i in range(len(segments) - 1):
                segment_key = segments[i]
                if segment_key not in self.property_associations:
                    self.property_associations[segment_key] = []
                self.property_associations[segment_key].append(existing_assets[hostname])
    
    def _calculate_transition_probability(self, hostname):
        if len(hostname) < 2:
            return 0.0
        
        probabilities = []
        for i in range(len(hostname) - 1):
            current = hostname[i]
            next_char = hostname[i + 1]
            
            if current in self.transitions:
                total = sum(self.transitions[current].values())
                count = self.transitions[current].get(next_char, 0)
                prob = count / total if total > 0 else 0
                probabilities.append(prob)
        
        return np.mean(probabilities) if probabilities else 0.0
    
    def predict(self, candidate, existing_assets):
        hostname = candidate['hostname']
        
        transition_prob = self._calculate_transition_probability(hostname)
        confidence = min(transition_prob * 2, 0.9)
        
        properties = {}
        segments = hostname.replace('.', '-').replace('_', '-').split('-')
        
        property_votes = {
            'domain': Counter(),
            'region': Counter(),
            'country': Counter(),
            'business_unit': Counter(),
            'data_center': Counter()
        }
        
        for segment in segments:
            if segment in self.property_associations:
                for asset_props in self.property_associations[segment][:20]:
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
            'algorithm': 'MarkovChainPredictor'
        }