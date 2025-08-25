from collections import Counter
import numpy as np

class NGramAnalyzer:
    def __init__(self, n=3):
        self.n = n
        self.ngram_model = {}
        self.hostname_properties = {}
        
    def train(self, df, existing_assets):
        all_ngrams = Counter()
        
        for hostname in existing_assets.keys():
            if len(hostname) >= self.n:
                for i in range(len(hostname) - self.n + 1):
                    ngram = hostname[i:i+self.n]
                    all_ngrams[ngram] += 1
                    
                    if ngram not in self.hostname_properties:
                        self.hostname_properties[ngram] = []
                    self.hostname_properties[ngram].append(existing_assets[hostname])
        
        self.ngram_model = dict(all_ngrams)
        
    def predict(self, candidate, existing_assets):
        hostname = candidate['hostname']
        confidence = 0.0
        properties = {}
        
        ngram_scores = []
        property_votes = {
            'domain': Counter(),
            'region': Counter(),
            'country': Counter(),
            'business_unit': Counter(),
            'data_center': Counter()
        }
        
        if len(hostname) >= self.n:
            for i in range(len(hostname) - self.n + 1):
                ngram = hostname[i:i+self.n]
                
                if ngram in self.ngram_model:
                    frequency = self.ngram_model[ngram]
                    ngram_scores.append(min(frequency / 100, 1.0))
                    
                    if ngram in self.hostname_properties:
                        for asset_props in self.hostname_properties[ngram][:10]:
                            for key in property_votes:
                                if asset_props.get(key):
                                    property_votes[key][asset_props[key]] += 1
        
        if ngram_scores:
            confidence = np.mean(ngram_scores)
            
            for key, counter in property_votes.items():
                if counter:
                    most_common = counter.most_common(1)[0][0]
                    properties[key] = most_common
        
        return {
            'confidence': confidence,
            'properties': properties,
            'algorithm': 'NGramAnalyzer'
        }