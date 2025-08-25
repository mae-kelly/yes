import re
import numpy as np
from collections import defaultdict

class SequentialPatternMiner:
    def __init__(self, min_pattern_size=3):
        self.min_pattern_size = min_pattern_size
        self.patterns = {}
        self.sequence_rules = {}
        
    def train(self, df, existing_assets):
        hostnames = list(existing_assets.keys())
        
        pattern_groups = defaultdict(list)
        for hostname in hostnames:
            pattern = re.sub(r'\d+', 'XXX', hostname)
            numbers = [int(m.group()) for m in re.finditer(r'\d+', hostname)]
            pattern_groups[pattern].append({'host': hostname, 'numbers': numbers})
        
        for pattern, hosts in pattern_groups.items():
            if len(hosts) >= self.min_pattern_size:
                self.patterns[pattern] = hosts
                
                number_sequences = defaultdict(list)
                for host_info in hosts:
                    for i, num in enumerate(host_info['numbers']):
                        number_sequences[i].append(num)
                
                self.sequence_rules[pattern] = {}
                for pos, nums in number_sequences.items():
                    if nums:
                        self.sequence_rules[pattern][pos] = {
                            'min': min(nums),
                            'max': max(nums),
                            'step': self._find_common_step(nums)
                        }
    
    def _find_common_step(self, numbers):
        if len(numbers) < 2:
            return 1
        sorted_nums = sorted(numbers)
        diffs = [sorted_nums[i+1] - sorted_nums[i] for i in range(len(sorted_nums)-1)]
        if diffs:
            return min(diffs) if min(diffs) > 0 else 1
        return 1
    
    def predict(self, candidate, existing_assets):
        hostname = candidate['hostname']
        pattern = re.sub(r'\d+', 'XXX', hostname)
        
        confidence = 0.0
        properties = {}
        
        if pattern in self.patterns:
            similar_hosts = [h['host'] for h in self.patterns[pattern]]
            
            numbers = [int(m.group()) for m in re.finditer(r'\d+', hostname)]
            for i, num in enumerate(numbers):
                if i in self.sequence_rules.get(pattern, {}):
                    rule = self.sequence_rules[pattern][i]
                    if rule['min'] <= num <= rule['max']:
                        if (num - rule['min']) % rule['step'] == 0:
                            confidence += 0.3
            
            if confidence > 0:
                confidence = min(confidence + 0.4, 1.0)
                
                for host in similar_hosts[:10]:
                    if host in existing_assets:
                        asset_props = existing_assets[host]
                        for key in ['domain', 'region', 'country', 'business_unit']:
                            if asset_props.get(key):
                                if key not in properties:
                                    properties[key] = []
                                properties[key].append(asset_props[key])
                
                for key in properties:
                    if properties[key]:
                        most_common = max(set(properties[key]), key=properties[key].count)
                        properties[key] = most_common
        
        return {
            'confidence': confidence,
            'properties': properties,
            'algorithm': 'SequentialPatternMiner'
        }