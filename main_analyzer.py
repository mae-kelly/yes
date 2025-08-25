#!/usr/bin/env python3

import duckdb
import pandas as pd
import numpy as np
from collections import Counter
import json
from datetime import datetime

from algorithm_1_sequential import SequentialPatternMiner
from algorithm_2_ngram import NGramAnalyzer  
from algorithm_3_lstm import LSTMPredictor
from algorithm_4_isolation import IsolationForestDetector
from algorithm_5_clustering import DBSCANClusterer
from algorithm_6_markov import MarkovChainPredictor
from algorithm_7_autoencoder import AutoencoderDetector
from algorithm_8_random_forest import RandomForestPredictor
from algorithm_9_gradient_boost import GradientBoostPredictor
from algorithm_10_svm import SVMClassifier

class DatabasePatternAnalyzer:
    def __init__(self, db_path='universal_cmdb.db'):
        self.db_path = db_path
        self.algorithms = []
        self.existing_assets = {}
        self.predictions = []
        
    def load_database(self):
        print("Loading database...")
        conn = duckdb.connect(self.db_path)
        
        query = """
        SELECT * FROM universal_cmdb 
        ORDER BY host
        """
        
        df = conn.execute(query).df()
        conn.close()
        
        print(f"Loaded {len(df)} assets")
        
        for _, row in df.iterrows():
            hostname = str(row['host']).lower() if pd.notna(row['host']) else None
            if hostname:
                self.existing_assets[hostname] = {
                    'domain': self._extract_domain(hostname),
                    'region': row.get('region'),
                    'country': row.get('country'),
                    'business_unit': row.get('business_unit'),
                    'data_center': row.get('data_center'),
                    'cloud_region': row.get('cloud_region'),
                    'system_classification': row.get('system_classification'),
                    'infrastructure_type': row.get('infrastructure_type')
                }
        
        return df
    
    def _extract_domain(self, hostname):
        parts = hostname.split('.')
        if len(parts) > 1:
            return '.'.join(parts[1:])
        return None
    
    def initialize_algorithms(self, df):
        print("\nInitializing 10 ML algorithms...")
        
        self.algorithms = [
            SequentialPatternMiner(min_pattern_size=3),
            NGramAnalyzer(n=3),
            LSTMPredictor(),
            IsolationForestDetector(),
            DBSCANClusterer(),
            MarkovChainPredictor(),
            AutoencoderDetector(),
            RandomForestPredictor(),
            GradientBoostPredictor(),
            SVMClassifier()
        ]
        
        print("Training algorithms on existing data...")
        for i, algo in enumerate(self.algorithms):
            print(f"  {i+1}. Training {algo.__class__.__name__}...")
            algo.train(df, self.existing_assets)
    
    def find_patterns(self):
        print("\nFinding patterns in hostnames...")
        
        hostname_patterns = {}
        
        for hostname in self.existing_assets.keys():
            pattern = self._get_pattern(hostname)
            if pattern not in hostname_patterns:
                hostname_patterns[pattern] = []
            hostname_patterns[pattern].append(hostname)
        
        legitimate_patterns = {}
        for pattern, hosts in hostname_patterns.items():
            if len(hosts) >= 3:
                legitimate_patterns[pattern] = hosts
                print(f"  Pattern: {pattern} ({len(hosts)} instances)")
        
        return legitimate_patterns
    
    def _get_pattern(self, hostname):
        import re
        pattern = re.sub(r'\d+', 'NUM', hostname)
        return pattern
    
    def generate_candidates(self, patterns):
        print("\nGenerating missing asset candidates...")
        
        candidates = []
        
        for pattern, existing_hosts in patterns.items():
            numbers_in_pattern = self._extract_numbers_from_hosts(existing_hosts)
            
            for pos, numbers in numbers_in_pattern.items():
                if numbers:
                    min_num, max_num = min(numbers), max(numbers)
                    
                    for num in range(min_num, max_num + 1):
                        if num not in numbers:
                            candidate = self._create_candidate(pattern, pos, num)
                            if candidate not in self.existing_assets:
                                candidates.append({
                                    'hostname': candidate,
                                    'pattern': pattern,
                                    'similar_hosts': existing_hosts[:5]
                                })
        
        print(f"  Generated {len(candidates)} candidates")
        return candidates
    
    def _extract_numbers_from_hosts(self, hosts):
        import re
        numbers_by_position = {}
        
        for host in hosts:
            matches = list(re.finditer(r'\d+', host))
            for i, match in enumerate(matches):
                if i not in numbers_by_position:
                    numbers_by_position[i] = set()
                numbers_by_position[i].add(int(match.group()))
        
        return numbers_by_position
    
    def _create_candidate(self, pattern, position, number):
        import re
        parts = pattern.split('NUM')
        
        result = parts[0]
        for i in range(len(parts) - 1):
            if i == position:
                result += str(number)
            else:
                result += 'NUM'
            if i + 1 < len(parts):
                result += parts[i + 1]
        
        return result
    
    def predict_properties(self, candidates):
        print("\nPredicting properties for missing assets...")
        
        predictions = []
        
        for candidate in candidates[:1000]:
            print(f"\n  Analyzing: {candidate['hostname']}")
            
            votes = []
            properties = {}
            
            for algo in self.algorithms:
                prediction = algo.predict(candidate, self.existing_assets)
                votes.append(prediction['confidence'])
                
                if 'properties' in prediction:
                    for key, value in prediction['properties'].items():
                        if key not in properties:
                            properties[key] = []
                        properties[key].append(value)
            
            consensus_confidence = np.mean(votes)
            
            consensus_properties = {}
            for key, values in properties.items():
                value_counts = Counter(values)
                if value_counts:
                    consensus_properties[key] = value_counts.most_common(1)[0][0]
            
            if consensus_confidence > 0.5:
                result = {
                    'hostname': candidate['hostname'],
                    'confidence': consensus_confidence,
                    'individual_scores': votes,
                    'pattern': candidate['pattern'],
                    'similar_to': candidate['similar_hosts'][:3],
                    'predicted_properties': consensus_properties
                }
                
                predictions.append(result)
                
                print(f"    Confidence: {consensus_confidence:.2%}")
                print(f"    Predicted domain: {consensus_properties.get('domain', 'unknown')}")
                print(f"    Predicted region: {consensus_properties.get('region', 'unknown')}")
        
        return predictions
    
    def save_results(self, predictions):
        print(f"\nSaving results...")
        
        predictions_sorted = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"missing_assets_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'total_existing_assets': len(self.existing_assets),
                'missing_assets_found': len(predictions_sorted),
                'predictions': predictions_sorted[:100]
            }, f, indent=2, default=str)
        
        print(f"  Results saved to {filename}")
        
        print(f"\nTop 10 Missing Assets:")
        print("-" * 80)
        for i, pred in enumerate(predictions_sorted[:10]):
            print(f"{i+1}. {pred['hostname']}")
            print(f"   Confidence: {pred['confidence']:.2%}")
            print(f"   Domain: {pred['predicted_properties'].get('domain', 'unknown')}")
            print(f"   Region: {pred['predicted_properties'].get('region', 'unknown')}")
            print(f"   Country: {pred['predicted_properties'].get('country', 'unknown')}")
            print()
    
    def run(self):
        df = self.load_database()
        self.initialize_algorithms(df)
        patterns = self.find_patterns()
        candidates = self.generate_candidates(patterns)
        predictions = self.predict_properties(candidates)
        self.save_results(predictions)

if __name__ == "__main__":
    analyzer = DatabasePatternAnalyzer()
    analyzer.run()