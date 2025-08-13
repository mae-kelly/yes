#!/usr/bin/env python3

import asyncio
import logging
import json
import numpy as np
import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import statistics
import re
import networkx as nx
from collections import defaultdict, Counter
import pickle
import threading
import ipaddress
from scipy import stats

logger = logging.getLogger(__name__)

@dataclass
class AIInsight:
    insight_type: str
    confidence: float
    content: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reasoning_chain: List[str] = field(default_factory=list)
    predicted_impact: float = 0.0
    certainty_level: str = "medium"

class VisibilityTransformerClassifier(nn.Module):
    def __init__(self, input_dim=384, hidden_dim=256, num_classes=15):
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, num_classes),
            nn.Softmax(dim=1)
        )
        
        self.field_types = [
            'hostname', 'ip_address', 'log_type', 'system_classification',
            'infrastructure_type', 'business_unit', 'global_region', 'country',
            'edr_coverage', 'dlp_coverage', 'vulnerability_status', 'compliance_status',
            'network_zone', 'application_class', 'visibility_factor'
        ]
        
    def forward(self, embeddings):
        return self.classifier(embeddings)

class AO1VisibilityPatternRecognizer:
    def __init__(self):
        self.device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
        self.sentence_model = SentenceTransformer('all-MiniLM-L12-v2')
        self.field_classifier = VisibilityTransformerClassifier()
        self.field_classifier.to(self.device)
        
        self.pattern_embeddings = {}
        self.learned_patterns = defaultdict(list)
        self.training_examples = []
        self.training_lock = threading.Lock()
        
        self.visibility_patterns = {
            'hostname': [r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', r'srv\d+', r'host\d+', r'web\d+', r'app\d+'],
            'ip_address': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
            'log_type': [r'firewall', r'ids', r'ips', r'proxy', r'dns', r'waf', r'syslog', r'winlog', r'edr'],
            'system_classification': [r'windows', r'linux', r'unix', r'database', r'web.*server', r'mainframe'],
            'infrastructure_type': [r'on.?prem', r'cloud', r'saas', r'api', r'physical', r'virtual'],
            'business_unit': [r'finance', r'marketing', r'sales', r'hr', r'operations', r'legal'],
            'global_region': [r'us', r'usa', r'eu', r'europe', r'apac', r'asia', r'americas', r'emea'],
            'edr_coverage': [r'crowdstrike', r'defender', r'edr', r'endpoint.*detection'],
            'dlp_coverage': [r'dlp', r'data.*loss.*prevention'],
            'network_zone': [r'dmz', r'internal', r'external', r'vlan', r'subnet']
        }
        
    async def classify_visibility_field(self, column_name: str, sample_values: List[str], 
                                      context: Dict[str, Any] = None) -> Tuple[str, float, Dict[str, Any]]:
        context_text = self._create_visibility_context(column_name, sample_values, context)
        embeddings = self.sentence_model.encode([context_text])
        
        tokens_tensor = torch.tensor(embeddings).to(self.device)
        
        with torch.no_grad():
            predictions = self.field_classifier(tokens_tensor)
            probabilities = predictions.cpu().numpy()[0]
        
        top_idx = np.argmax(probabilities)
        confidence = float(probabilities[top_idx])
        field_type = self.field_classifier.field_types[top_idx] if top_idx < len(self.field_classifier.field_types) else 'unknown'
        
        content_analysis = await self._analyze_visibility_content(sample_values, field_type)
        
        final_confidence = (confidence * 0.6) + (content_analysis['confidence'] * 0.4)
        
        metadata = {
            'ai_confidence': confidence,
            'content_confidence': content_analysis['confidence'],
            'visibility_patterns': content_analysis['patterns'],
            'pattern_matches': content_analysis['pattern_matches'],
            'log_visibility_score': self._calculate_log_visibility_score(sample_values, field_type),
            'cmdb_alignment_score': self._calculate_cmdb_alignment_score(sample_values, field_type),
            'security_relevance': self._assess_security_relevance(sample_values, field_type),
            'alternative_predictions': self._get_alternative_predictions(probabilities)
        }
        
        return field_type, final_confidence, metadata
    
    def _create_visibility_context(self, column_name: str, sample_values: List[str], 
                                 context: Dict[str, Any] = None) -> str:
        context_parts = [f"Column: {column_name}"]
        
        if sample_values:
            unique_values = list(set(sample_values[:8]))
            context_parts.append(f"Values: {', '.join(unique_values)}")
            
            avg_length = statistics.mean([len(str(v)) for v in sample_values])
            context_parts.append(f"Length: {avg_length:.1f}")
            
            patterns = self._detect_visibility_patterns(sample_values)
            if patterns:
                context_parts.append(f"Patterns: {', '.join(patterns)}")
        
        if context:
            table_name = context.get('table_name', '')
            if table_name:
                context_parts.append(f"Table: {table_name}")
            
            source = context.get('source', '')
            if source:
                context_parts.append(f"Source: {source}")
        
        return ". ".join(context_parts)
    
    async def _analyze_visibility_content(self, sample_values: List[str], field_type: str) -> Dict[str, Any]:
        if not sample_values:
            return {'confidence': 0.0, 'patterns': [], 'pattern_matches': {}}
        
        pattern_matches = {}
        for pattern_type, patterns in self.visibility_patterns.items():
            matches = 0
            for pattern in patterns:
                matches += sum(1 for value in sample_values if re.search(pattern, str(value), re.IGNORECASE))
            pattern_matches[pattern_type] = matches / len(sample_values) if sample_values else 0.0
        
        field_type_score = pattern_matches.get(field_type, 0.0)
        
        format_consistency = self._assess_format_consistency(sample_values)
        data_quality = self._assess_data_quality(sample_values)
        
        combined_confidence = (field_type_score * 0.5) + (format_consistency * 0.3) + (data_quality * 0.2)
        
        detected_patterns = [pattern for pattern, score in pattern_matches.items() if score > 0.3]
        
        return {
            'confidence': combined_confidence,
            'patterns': detected_patterns,
            'pattern_matches': pattern_matches,
            'format_consistency': format_consistency,
            'data_quality': data_quality
        }
    
    def _detect_visibility_patterns(self, values: List[str]) -> List[str]:
        patterns = []
        
        if any(re.match(r'^[A-Z]{2,5}\d+', str(v)) for v in values):
            patterns.append('code_pattern')
        
        if any('.' in str(v) and len(str(v).split('.')) > 1 for v in values):
            patterns.append('dotted_notation')
        
        if any(re.search(r'\d+\.\d+\.\d+\.\d+', str(v)) for v in values):
            patterns.append('ip_pattern')
        
        if any(re.search(r'[a-zA-Z]+\d+', str(v)) for v in values):
            patterns.append('alphanumeric')
        
        if all(str(v).isupper() for v in values if v):
            patterns.append('uppercase')
        elif all(str(v).islower() for v in values if v):
            patterns.append('lowercase')
        
        return patterns
    
    def _calculate_log_visibility_score(self, values: List[str], field_type: str) -> float:
        log_indicators = ['log', 'event', 'syslog', 'winlog', 'audit', 'security', 'firewall', 'proxy']
        
        if field_type == 'log_type':
            return 1.0
        
        log_matches = sum(1 for value in values 
                         for indicator in log_indicators 
                         if indicator in str(value).lower())
        
        return min(1.0, log_matches / max(len(values), 1))
    
    def _calculate_cmdb_alignment_score(self, values: List[str], field_type: str) -> float:
        cmdb_fields = ['hostname', 'ip_address', 'system_classification', 'infrastructure_type', 'business_unit']
        
        if field_type in cmdb_fields:
            return 0.9
        
        cmdb_indicators = ['asset', 'inventory', 'cmdb', 'configuration', 'management']
        cmdb_matches = sum(1 for value in values 
                          for indicator in cmdb_indicators 
                          if indicator in str(value).lower())
        
        return min(1.0, cmdb_matches / max(len(values), 1))
    
    def _assess_security_relevance(self, values: List[str], field_type: str) -> float:
        security_fields = ['edr_coverage', 'dlp_coverage', 'vulnerability_status', 'compliance_status']
        
        if field_type in security_fields:
            return 1.0
        
        security_indicators = ['security', 'threat', 'vulnerability', 'compliance', 'risk', 'protection']
        security_matches = sum(1 for value in values 
                              for indicator in security_indicators 
                              if indicator in str(value).lower())
        
        return min(1.0, security_matches / max(len(values), 1))
    
    def _assess_format_consistency(self, values: List[str]) -> float:
        if len(values) < 2:
            return 1.0
        
        format_signatures = []
        for value in values:
            signature = re.sub(r'[a-zA-Z]', 'A', str(value))
            signature = re.sub(r'[0-9]', '9', signature)
            format_signatures.append(signature)
        
        signature_counts = Counter(format_signatures)
        most_common_ratio = signature_counts.most_common(1)[0][1] / len(values) if signature_counts else 0
        
        return most_common_ratio
    
    def _assess_data_quality(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        valid_values = [v for v in values if v and str(v).strip() and str(v).upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE']]
        completeness = len(valid_values) / len(values)
        
        uniqueness = len(set(valid_values)) / len(valid_values) if valid_values else 0
        
        return (completeness * 0.7) + (uniqueness * 0.3)
    
    def _get_alternative_predictions(self, probabilities: np.ndarray, top_k: int = 3) -> List[Tuple[str, float]]:
        top_indices = np.argsort(probabilities)[-top_k:][::-1]
        alternatives = []
        
        for idx in top_indices:
            if idx < len(self.field_classifier.field_types):
                field_type = self.field_classifier.field_types[idx]
                confidence = float(probabilities[idx])
                alternatives.append((field_type, confidence))
        
        return alternatives

class AO1AssetGraphAnalyzer:
    def __init__(self):
        self.asset_graph = nx.Graph()
        self.relationship_weights = {
            'same_hostname': 1.0,
            'same_ip': 0.9,
            'same_subnet': 0.7,
            'same_domain': 0.6,
            'same_business_unit': 0.5,
            'same_region': 0.4,
            'same_log_source': 0.8,
            'same_security_zone': 0.7
        }
    
    def build_visibility_graph(self, assets: List[Dict[str, Any]]) -> nx.Graph:
        self.asset_graph.clear()
        
        for asset in assets:
            asset_id = asset.get('master_asset_id', asset.get('hostname', 'unknown'))
            self.asset_graph.add_node(asset_id, **asset)
        
        asset_list = list(assets)
        for i, asset1 in enumerate(asset_list):
            for asset2 in asset_list[i+1:]:
                relationships = self._find_visibility_relationships(asset1, asset2)
                
                if relationships:
                    weight = sum(self.relationship_weights.get(rel, 0.1) for rel in relationships)
                    if weight > 0.3:
                        id1 = asset1.get('master_asset_id', asset1.get('hostname'))
                        id2 = asset2.get('master_asset_id', asset2.get('hostname'))
                        self.asset_graph.add_edge(id1, id2, weight=weight, relationships=relationships)
        
        return self.asset_graph
    
    def _find_visibility_relationships(self, asset1: Dict[str, Any], asset2: Dict[str, Any]) -> List[str]:
        relationships = []
        
        if (asset1.get('hostname', '').upper() == asset2.get('hostname', '').upper() 
            and asset1.get('hostname')):
            relationships.append('same_hostname')
        
        if (asset1.get('ip_address') == asset2.get('ip_address') 
            and asset1.get('ip_address')):
            relationships.append('same_ip')
        
        if self._same_subnet(asset1.get('ip_address'), asset2.get('ip_address')):
            relationships.append('same_subnet')
        
        if self._same_domain(asset1.get('fqdn'), asset2.get('fqdn')):
            relationships.append('same_domain')
        
        if (asset1.get('business_unit') == asset2.get('business_unit') 
            and asset1.get('business_unit')):
            relationships.append('same_business_unit')
        
        if (asset1.get('global_region') == asset2.get('global_region') 
            and asset1.get('global_region')):
            relationships.append('same_region')
        
        if self._same_log_source(asset1, asset2):
            relationships.append('same_log_source')
        
        if self._same_security_zone(asset1, asset2):
            relationships.append('same_security_zone')
        
        return relationships
    
    def _same_subnet(self, ip1: str, ip2: str) -> bool:
        if not ip1 or not ip2:
            return False
        
        try:
            octets1 = ip1.split('.')
            octets2 = ip2.split('.')
            
            if len(octets1) == 4 and len(octets2) == 4:
                return octets1[:3] == octets2[:3]
        except:
            pass
        
        return False
    
    def _same_domain(self, fqdn1: str, fqdn2: str) -> bool:
        if not fqdn1 or not fqdn2:
            return False
        
        try:
            domain1 = '.'.join(fqdn1.split('.')[1:])
            domain2 = '.'.join(fqdn2.split('.')[1:])
            return domain1 == domain2 and domain1
        except:
            pass
        
        return False
    
    def _same_log_source(self, asset1: Dict[str, Any], asset2: Dict[str, Any]) -> bool:
        log_sources1 = set()
        log_sources2 = set()
        
        if asset1.get('found_in_splunk'):
            log_sources1.add('splunk')
        if asset1.get('found_in_chronicle'):
            log_sources1.add('chronicle')
        if asset1.get('in_gso'):
            log_sources1.add('gso')
        
        if asset2.get('found_in_splunk'):
            log_sources2.add('splunk')
        if asset2.get('found_in_chronicle'):
            log_sources2.add('chronicle')
        if asset2.get('in_gso'):
            log_sources2.add('gso')
        
        return bool(log_sources1 & log_sources2)
    
    def _same_security_zone(self, asset1: Dict[str, Any], asset2: Dict[str, Any]) -> bool:
        zone1 = asset1.get('network_zones', '')
        zone2 = asset2.get('network_zones', '')
        
        return zone1 == zone2 and zone1
    
    def find_visibility_clusters(self) -> List[List[str]]:
        communities = nx.community.greedy_modularity_communities(self.asset_graph)
        return [list(community) for community in communities]
    
    def get_visibility_centrality(self) -> Dict[str, float]:
        if not self.asset_graph.nodes():
            return {}
        
        return nx.degree_centrality(self.asset_graph)
    
    def find_visibility_gaps(self) -> List[str]:
        centrality = self.get_visibility_centrality()
        if not centrality:
            return []
        
        mean_centrality = statistics.mean(centrality.values())
        std_centrality = statistics.stdev(centrality.values()) if len(centrality) > 1 else 0
        
        threshold = mean_centrality - (2 * std_centrality)
        
        return [asset_id for asset_id, cent in centrality.items() if cent < threshold]

class AO1VisibilityAnomalyDetector:
    def __init__(self):
        self.scaler = StandardScaler()
        self.anomaly_threshold = 0.1
    
    def detect_visibility_anomalies(self, assets: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        anomalies = {
            'visibility_gaps': self._detect_visibility_gaps(assets),
            'log_coverage_anomalies': self._detect_log_coverage_anomalies(assets),
            'cmdb_inconsistencies': self._detect_cmdb_inconsistencies(assets),
            'security_coverage_gaps': self._detect_security_coverage_gaps(assets),
            'compliance_anomalies': self._detect_compliance_anomalies(assets),
            'network_anomalies': self._detect_network_anomalies(assets)
        }
        
        return anomalies
    
    def _detect_visibility_gaps(self, assets: List[Dict[str, Any]]) -> List[str]:
        gaps = []
        
        for asset in assets:
            asset_id = asset.get('master_asset_id', asset.get('hostname', 'unknown'))
            
            log_sources = 0
            if asset.get('found_in_splunk'):
                log_sources += 1
            if asset.get('found_in_chronicle'):
                log_sources += 1
            if asset.get('in_gso'):
                log_sources += 1
            
            if log_sources == 0:
                gaps.append(asset_id)
            
            if not asset.get('found_in_cmdb') and log_sources > 0:
                gaps.append(asset_id)
        
        return gaps
    
    def _detect_log_coverage_anomalies(self, assets: List[Dict[str, Any]]) -> List[str]:
        anomalies = []
        
        for asset in assets:
            asset_id = asset.get('master_asset_id', asset.get('hostname', 'unknown'))
            
            has_critical_logs = (
                asset.get('network_log_types') or 
                asset.get('endpoint_log_types') or 
                asset.get('application_log_types')
            )
            
            if not has_critical_logs and asset.get('found_in_splunk'):
                anomalies.append(asset_id)
            
            log_type_count = sum(1 for log_type in [
                asset.get('network_log_types'),
                asset.get('endpoint_log_types'),
                asset.get('cloud_log_types'),
                asset.get('application_log_types'),
                asset.get('identity_log_types')
            ] if log_type)
            
            if log_type_count == 1 and asset.get('infrastructure_type') == 'cloud':
                anomalies.append(asset_id)
        
        return anomalies
    
    def _detect_cmdb_inconsistencies(self, assets: List[Dict[str, Any]]) -> List[str]:
        inconsistencies = []
        
        for asset in assets:
            asset_id = asset.get('master_asset_id', asset.get('hostname', 'unknown'))
            
            if asset.get('found_in_cmdb'):
                required_cmdb_fields = ['infrastructure_type', 'system_classification', 'business_unit']
                missing_fields = sum(1 for field in required_cmdb_fields if not asset.get(field))
                
                if missing_fields > 1:
                    inconsistencies.append(asset_id)
            
            if not asset.get('found_in_cmdb') and asset.get('source_count', 0) > 2:
                inconsistencies.append(asset_id)
        
        return inconsistencies
    
    def _detect_security_coverage_gaps(self, assets: List[Dict[str, Any]]) -> List[str]:
        gaps = []
        
        for asset in assets:
            asset_id = asset.get('master_asset_id', asset.get('hostname', 'unknown'))
            
            security_coverage = sum([
                asset.get('edr_coverage', False),
                asset.get('tanium_coverage', False),
                asset.get('dlp_coverage', False)
            ])
            
            if security_coverage == 0 and asset.get('system_classification') in ['Windows Server', 'Linux Server']:
                gaps.append(asset_id)
            
            if asset.get('infrastructure_type') == 'cloud' and not asset.get('cloud_log_types'):
                gaps.append(asset_id)
        
        return gaps
    
    def _detect_compliance_anomalies(self, assets: List[Dict[str, Any]]) -> List[str]:
        anomalies = []
        
        business_unit_requirements = {
            'finance': ['edr_coverage', 'dlp_coverage'],
            'hr': ['dlp_coverage'],
            'legal': ['dlp_coverage', 'edr_coverage']
        }
        
        for asset in assets:
            asset_id = asset.get('master_asset_id', asset.get('hostname', 'unknown'))
            business_unit = asset.get('business_unit', '').lower()
            
            if business_unit in business_unit_requirements:
                required_coverage = business_unit_requirements[business_unit]
                missing_coverage = [req for req in required_coverage if not asset.get(req)]
                
                if missing_coverage:
                    anomalies.append(asset_id)
        
        return anomalies
    
    def _detect_network_anomalies(self, assets: List[Dict[str, Any]]) -> List[str]:
        anomalies = []
        
        ip_subnets = defaultdict(list)
        for asset in assets:
            ip = asset.get('ip_address')
            if ip:
                try:
                    octets = ip.split('.')
                    if len(octets) == 4:
                        subnet = f"{octets[0]}.{octets[1]}.{octets[2]}.0"
                        ip_subnets[subnet].append(asset.get('master_asset_id', asset.get('hostname')))
                except:
                    pass
        
        for subnet, asset_ids in ip_subnets.items():
            if len(asset_ids) == 1 and len(ip_subnets) > 5:
                anomalies.extend(asset_ids)
        
        return anomalies

class AO1SuperIntelligentEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pattern_recognizer = AO1VisibilityPatternRecognizer()
        self.graph_analyzer = AO1AssetGraphAnalyzer()
        self.anomaly_detector = AO1VisibilityAnomalyDetector()
        
        self.performance_metrics = {
            'classification_accuracy': [],
            'processing_times': [],
            'confidence_scores': [],
            'visibility_scores': []
        }
        
    async def enhanced_visibility_classification(self, column_name: str, sample_values: List[str], 
                                               context: Dict[str, Any] = None) -> Dict[str, Any]:
        start_time = datetime.now()
        
        field_type, confidence, metadata = await self.pattern_recognizer.classify_visibility_field(
            column_name, sample_values, context
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        self.performance_metrics['processing_times'].append(processing_time)
        self.performance_metrics['confidence_scores'].append(confidence)
        
        visibility_score = self._calculate_visibility_score(field_type, metadata)
        self.performance_metrics['visibility_scores'].append(visibility_score)
        
        enhanced_metadata = {
            **metadata,
            'processing_time_ms': processing_time * 1000,
            'visibility_score': visibility_score,
            'ao1_enhanced': True,
            'classification_method': 'ao1_visibility_transformer'
        }
        
        return {
            'field_type': field_type,
            'confidence': confidence,
            'metadata': enhanced_metadata
        }
    
    def _calculate_visibility_score(self, field_type: str, metadata: Dict[str, Any]) -> float:
        base_score = metadata.get('content_confidence', 0.5)
        
        log_visibility = metadata.get('log_visibility_score', 0.0)
        cmdb_alignment = metadata.get('cmdb_alignment_score', 0.0)
        security_relevance = metadata.get('security_relevance', 0.0)
        
        visibility_score = (
            base_score * 0.4 +
            log_visibility * 0.3 +
            cmdb_alignment * 0.2 +
            security_relevance * 0.1
        )
        
        return min(1.0, visibility_score)
    
    async def analyze_asset_visibility_relationships(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        asset_graph = self.graph_analyzer.build_visibility_graph(assets)
        
        clusters = self.graph_analyzer.find_visibility_clusters()
        centrality = self.graph_analyzer.get_visibility_centrality()
        visibility_gaps = self.graph_analyzer.find_visibility_gaps()
        
        return {
            'asset_graph': {
                'nodes': asset_graph.number_of_nodes(),
                'edges': asset_graph.number_of_edges(),
                'density': nx.density(asset_graph)
            },
            'visibility_clusters': clusters,
            'centrality_scores': centrality,
            'visibility_gaps': visibility_gaps,
            'network_insights': self._generate_visibility_insights(asset_graph, clusters)
        }
    
    def _generate_visibility_insights(self, graph: nx.Graph, clusters: List[List[str]]) -> List[str]:
        insights = []
        
        if graph.number_of_nodes() == 0:
            return ["No assets to analyze for visibility"]
        
        if clusters:
            largest_cluster = max(clusters, key=len)
            insights.append(f"Found {len(clusters)} visibility clusters, largest has {len(largest_cluster)} assets")
        
        if nx.is_connected(graph):
            insights.append("All assets are connected in visibility network")
        else:
            components = list(nx.connected_components(graph))
            insights.append(f"Assets form {len(components)} disconnected visibility groups")
        
        density = nx.density(graph)
        if density > 0.7:
            insights.append("High asset visibility interconnectivity detected")
        elif density < 0.3:
            insights.append("Low visibility interconnectivity - potential blind spots")
        
        return insights
    
    async def detect_comprehensive_visibility_anomalies(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        anomalies = self.anomaly_detector.detect_visibility_anomalies(assets)
        
        all_anomalies = []
        for anomaly_type, anomaly_list in anomalies.items():
            for asset_id in anomaly_list:
                all_anomalies.append({
                    'asset_id': asset_id,
                    'anomaly_type': anomaly_type,
                    'severity': self._calculate_visibility_anomaly_severity(anomaly_type)
                })
        
        asset_anomalies = defaultdict(list)
        for anomaly in all_anomalies:
            asset_anomalies[anomaly['asset_id']].append(anomaly)
        
        return {
            'anomalies_by_type': anomalies,
            'anomalies_by_asset': dict(asset_anomalies),
            'anomaly_summary': self._create_visibility_anomaly_summary(anomalies),
            'recommendations': self._generate_visibility_recommendations(anomalies)
        }
    
    def _calculate_visibility_anomaly_severity(self, anomaly_type: str) -> str:
        severity_map = {
            'visibility_gaps': 'critical',
            'security_coverage_gaps': 'high',
            'log_coverage_anomalies': 'high',
            'cmdb_inconsistencies': 'medium',
            'compliance_anomalies': 'high',
            'network_anomalies': 'medium'
        }
        
        return severity_map.get(anomaly_type, 'medium')
    
    def _create_visibility_anomaly_summary(self, anomalies: Dict[str, List[str]]) -> Dict[str, Any]:
        total_anomalies = sum(len(anomaly_list) for anomaly_list in anomalies.values())
        
        critical_anomalies = (
            len(anomalies.get('visibility_gaps', [])) + 
            len(anomalies.get('security_coverage_gaps', []))
        )
        
        return {
            'total_anomalies': total_anomalies,
            'critical_anomalies': critical_anomalies,
            'anomaly_types': len(anomalies),
            'most_common_type': max(anomalies.keys(), key=lambda k: len(anomalies[k])) if anomalies else None,
            'visibility_coverage_issues': len(anomalies.get('visibility_gaps', [])),
            'security_issues': len(anomalies.get('security_coverage_gaps', []))
        }
    
    def _generate_visibility_recommendations(self, anomalies: Dict[str, List[str]]) -> List[str]:
        recommendations = []
        
        if anomalies.get('visibility_gaps'):
            recommendations.append("Address critical visibility gaps - assets without log coverage detected")
        
        if anomalies.get('security_coverage_gaps'):
            recommendations.append("Implement security controls for uncovered assets")
        
        if anomalies.get('log_coverage_anomalies'):
            recommendations.append("Review log collection configuration for incomplete coverage")
        
        if anomalies.get('cmdb_inconsistencies'):
            recommendations.append("Update CMDB with missing asset information")
        
        if anomalies.get('compliance_anomalies'):
            recommendations.append("Address compliance gaps based on business unit requirements")
        
        if anomalies.get('network_anomalies'):
            recommendations.append("Review network segmentation and asset placement")
        
        return recommendations
    
    def get_ao1_performance_summary(self) -> Dict[str, Any]:
        metrics = self.performance_metrics
        
        if not metrics['confidence_scores']:
            return {'status': 'no_data'}
        
        return {
            'avg_confidence': statistics.mean(metrics['confidence_scores']),
            'avg_visibility_score': statistics.mean(metrics['visibility_scores']),
            'avg_processing_time_ms': statistics.mean(metrics['processing_times']) * 1000,
            'total_classifications': len(metrics['confidence_scores']),
            'high_confidence_rate': sum(1 for c in metrics['confidence_scores'] if c > 0.8) / len(metrics['confidence_scores']),
            'high_visibility_rate': sum(1 for v in metrics['visibility_scores'] if v > 0.7) / len(metrics['visibility_scores']),
            'performance_trend': 'improving' if len(metrics['confidence_scores']) > 5 and 
                                statistics.mean(metrics['confidence_scores'][-5:]) > statistics.mean(metrics['confidence_scores'][:-5]) 
                                else 'stable'
        }