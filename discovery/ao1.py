# discovery/ao1.py

import asyncio
import logging
import networkx as nx
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import statistics
from core.types import Asset, Discovery
from ai.neural import FieldClassifier, PatternRecognizer
from ai.intelligence import IntelligenceEngine

logger = logging.getLogger(__name__)

class AO1VisibilityEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.classifier = FieldClassifier()
        self.recognizer = PatternRecognizer()
        self.visibility_weights = {
            'log_coverage': 0.4,
            'cmdb_coverage': 0.3,
            'security_coverage': 0.2,
            'field_completeness': 0.1
        }
        
        self.anomaly_thresholds = {
            'visibility_gap': 0.3,
            'coverage_anomaly': 0.5,
            'consistency_violation': 0.7
        }
    
    async def enhanced_classification(self, column_name: str, samples: List[str], 
                                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        
        if self._is_hostname_column(column_name, samples):
            return {
                'field_type': 'hostname',
                'confidence': 0.95,
                'metadata': {
                    'ai_confidence': 0.95,
                    'content_confidence': 0.95,
                    'visibility_score': 1.0,
                    'ao1_enhanced': True
                }
            }
        
        context_text = self._create_context(column_name, samples, context)
        embeddings = self._text_to_embeddings(context_text)
        
        predictions = self.classifier(embeddings)
        top_idx = np.argmax(predictions.detach().numpy()[0])
        confidence = float(predictions.detach().numpy()[0][top_idx])
        
        field_type = self.classifier.field_types[top_idx] if top_idx < len(self.classifier.field_types) else 'unknown'
        
        content_analysis = await self._analyze_visibility_content(samples, field_type)
        final_confidence = (confidence * 0.6) + (content_analysis['confidence'] * 0.4)
        
        metadata = {
            'ai_confidence': confidence,
            'content_confidence': content_analysis['confidence'],
            'visibility_score': self._calculate_visibility_score(samples, field_type),
            'log_visibility_score': self._calculate_log_visibility(samples, field_type),
            'cmdb_alignment_score': self._calculate_cmdb_alignment(samples, field_type),
            'security_relevance': self._assess_security_relevance(samples, field_type),
            'ao1_enhanced': True
        }
        
        return {
            'field_type': field_type,
            'confidence': final_confidence,
            'metadata': metadata
        }
    
    def _is_hostname_column(self, column_name: str, samples: List[str]) -> bool:
        name_lower = column_name.lower()
        hostname_indicators = ['hostname', 'host', 'computername', 'endpoint', 'device', 'machine', 'computer']
        
        for indicator in hostname_indicators:
            if indicator in name_lower:
                return True
        
        if not samples:
            return False
        
        hostname_count = 0
        for sample in samples[:20]:
            if self._looks_like_hostname(sample):
                hostname_count += 1
        
        return (hostname_count / min(len(samples), 20)) > 0.7
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        import re
        patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)
    
    def _create_context(self, column_name: str, samples: List[str], context: Dict[str, Any] = None) -> str:
        parts = [f"Column: {column_name}"]
        
        if samples:
            unique_samples = list(set(samples[:8]))
            parts.append(f"Values: {', '.join(unique_samples)}")
            
            avg_len = statistics.mean([len(str(v)) for v in samples])
            parts.append(f"AvgLength: {avg_len:.1f}")
        
        if context:
            table_name = context.get('table_name', '')
            source = context.get('source', '')
            if table_name:
                parts.append(f"Table: {table_name}")
            if source:
                parts.append(f"Source: {source}")
        
        return ". ".join(parts)
    
    def _text_to_embeddings(self, text: str) -> np.ndarray:
        import torch
        words = text.lower().split()
        
        vocab_size = 1000
        embed_dim = 512
        
        word_indices = [hash(word) % vocab_size for word in words]
        
        embeddings = np.random.randn(len(word_indices), embed_dim) * 0.1
        for i, idx in enumerate(word_indices):
            np.random.seed(idx)
            embeddings[i] = np.random.randn(embed_dim) * 0.1
        
        if len(embeddings) == 0:
            embeddings = np.zeros((1, embed_dim))
        
        return torch.tensor(embeddings).unsqueeze(0).float()
    
    async def _analyze_visibility_content(self, samples: List[str], field_type: str) -> Dict[str, Any]:
        if not samples:
            return {'confidence': 0.0, 'patterns': [], 'pattern_matches': {}}
        
        visibility_patterns = {
            'hostname': [r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$'],
            'ip_address': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
            'log_type': [r'firewall|ids|ips|proxy|dns|syslog|winlog'],
            'security': [r'edr|dlp|crowdstrike|security|auth']
        }
        
        patterns = visibility_patterns.get(field_type, [])
        matches = 0
        
        for pattern in patterns:
            import re
            matches += sum(1 for value in samples if re.search(pattern, str(value), re.IGNORECASE))
        
        pattern_score = matches / len(samples) if samples else 0.0
        format_consistency = self._assess_format_consistency(samples)
        data_quality = self._assess_data_quality(samples)
        
        combined_confidence = (pattern_score * 0.5) + (format_consistency * 0.3) + (data_quality * 0.2)
        
        return {
            'confidence': combined_confidence,
            'patterns': [field_type] if pattern_score > 0.3 else [],
            'pattern_matches': {field_type: pattern_score},
            'format_consistency': format_consistency,
            'data_quality': data_quality
        }
    
    def _calculate_visibility_score(self, samples: List[str], field_type: str) -> float:
        visibility_factors = []
        
        if field_type in ['hostname', 'ip_address', 'fqdn']:
            visibility_factors.append(('identity', 0.9, 0.4))
        
        if field_type in ['log_type', 'network_log_types', 'endpoint_log_types']:
            visibility_factors.append(('logging', 0.8, 0.3))
        
        if field_type in ['edr_coverage', 'dlp_coverage', 'security']:
            visibility_factors.append(('security', 0.7, 0.3))
        
        if not visibility_factors:
            return 0.5
        
        weighted_score = sum(score * weight for _, score, weight in visibility_factors)
        total_weight = sum(weight for _, _, weight in visibility_factors)
        
        return weighted_score / total_weight if total_weight > 0 else 0.5
    
    def _calculate_log_visibility(self, samples: List[str], field_type: str) -> float:
        if field_type in ['log_type', 'network_log_types', 'endpoint_log_types']:
            return 1.0
        
        log_indicators = ['log', 'event', 'syslog', 'audit', 'firewall']
        matches = sum(1 for value in samples 
                     for indicator in log_indicators 
                     if indicator in str(value).lower())
        
        return min(1.0, matches / max(len(samples), 1))
    
    def _calculate_cmdb_alignment(self, samples: List[str], field_type: str) -> float:
        cmdb_fields = ['hostname', 'ip_address', 'system_classification', 'infrastructure_type']
        
        if field_type in cmdb_fields:
            return 0.9
        
        return 0.3
    
    def _assess_security_relevance(self, samples: List[str], field_type: str) -> float:
        security_fields = ['edr_coverage', 'dlp_coverage', 'security', 'auth']
        
        if field_type in security_fields:
            return 1.0
        
        security_terms = ['security', 'threat', 'vulnerability', 'compliance']
        matches = sum(1 for value in samples 
                     for term in security_terms 
                     if term in str(value).lower())
        
        return min(1.0, matches / max(len(samples), 1))
    
    def _assess_format_consistency(self, samples: List[str]) -> float:
        if len(samples) < 2:
            return 1.0
        
        import re
        from collections import Counter
        
        patterns = []
        for value in samples:
            pattern = re.sub(r'[a-zA-Z]', 'A', str(value))
            pattern = re.sub(r'[0-9]', '9', pattern)
            patterns.append(pattern)
        
        pattern_counts = Counter(patterns)
        most_common_ratio = pattern_counts.most_common(1)[0][1] / len(patterns) if pattern_counts else 0
        
        return most_common_ratio
    
    def _assess_data_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        valid_samples = [s for s in samples if s and str(s).strip() and str(s).upper() not in ['NULL', 'N/A']]
        completeness = len(valid_samples) / len(samples)
        
        uniqueness = len(set(valid_samples)) / len(valid_samples) if valid_samples else 0
        
        return (completeness * 0.7) + (uniqueness * 0.3)

class AssetGraphAnalyzer:
    def __init__(self):
        self.asset_graph = nx.Graph()
        self.relationship_weights = {
            'same_hostname': 1.0,
            'same_ip': 0.9,
            'same_subnet': 0.7,
            'same_domain': 0.6,
            'same_business_unit': 0.5,
            'same_region': 0.4,
            'same_log_source': 0.8
        }
    
    def build_visibility_graph(self, assets: List[Dict[str, Any]]) -> nx.Graph:
        self.asset_graph.clear()
        
        for asset in assets:
            asset_id = asset.get('id', asset.get('hostname', 'unknown'))
            self.asset_graph.add_node(asset_id, **asset)
        
        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                relationships = self._find_relationships(asset1, asset2)
                
                if relationships:
                    weight = sum(self.relationship_weights.get(rel, 0.1) for rel in relationships)
                    if weight > 0.3:
                        id1 = asset1.get('id', asset1.get('hostname'))
                        id2 = asset2.get('id', asset2.get('hostname'))
                        self.asset_graph.add_edge(id1, id2, weight=weight, relationships=relationships)
        
        return self.asset_graph
    
    def _find_relationships(self, asset1: Dict[str, Any], asset2: Dict[str, Any]) -> List[str]:
        relationships = []
        
        if (asset1.get('hostname', '').upper() == asset2.get('hostname', '').upper() 
            and asset1.get('hostname')):
            relationships.append('same_hostname')
        
        if (asset1.get('ip', '') == asset2.get('ip', '') 
            and asset1.get('ip')):
            relationships.append('same_ip')
        
        if self._same_subnet(asset1.get('ip', ''), asset2.get('ip', '')):
            relationships.append('same_subnet')
        
        if self._same_domain(asset1.get('fqdn', ''), asset2.get('fqdn', '')):
            relationships.append('same_domain')
        
        if (asset1.get('business_unit', '') == asset2.get('business_unit', '') 
            and asset1.get('business_unit')):
            relationships.append('same_business_unit')
        
        if (asset1.get('region', '') == asset2.get('region', '') 
            and asset1.get('region')):
            relationships.append('same_region')
        
        if self._same_log_source(asset1, asset2):
            relationships.append('same_log_source')
        
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
        sources1 = set()
        sources2 = set()
        
        if asset1.get('splunk'):
            sources1.add('splunk')
        if asset1.get('chronicle'):
            sources1.add('chronicle')
        if asset1.get('gso'):
            sources1.add('gso')
        
        if asset2.get('splunk'):
            sources2.add('splunk')
        if asset2.get('chronicle'):
            sources2.add('chronicle')
        if asset2.get('gso'):
            sources2.add('gso')
        
        return bool(sources1 & sources2)
    
    def find_visibility_clusters(self) -> List[List[str]]:
        if self.asset_graph.number_of_nodes() == 0:
            return []
        
        communities = nx.community.greedy_modularity_communities(self.asset_graph)
        return [list(community) for community in communities]
    
    def get_visibility_centrality(self) -> Dict[str, float]:
        if self.asset_graph.number_of_nodes() == 0:
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

class VisibilityAnomalyDetector:
    def __init__(self):
        self.anomaly_types = {
            'visibility_gaps': self._detect_visibility_gaps,
            'log_coverage_anomalies': self._detect_log_anomalies,
            'cmdb_inconsistencies': self._detect_cmdb_issues,
            'security_coverage_gaps': self._detect_security_gaps,
            'network_anomalies': self._detect_network_anomalies
        }
    
    def detect_comprehensive_anomalies(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_anomalies = {}
        
        for anomaly_type, detector_func in self.anomaly_types.items():
            try:
                anomalies = detector_func(assets)
                all_anomalies[anomaly_type] = anomalies
            except Exception as e:
                logger.warning(f"Anomaly detection failed for {anomaly_type}: {e}")
                all_anomalies[anomaly_type] = []
        
        return {
            'anomalies_by_type': all_anomalies,
            'anomaly_summary': self._create_summary(all_anomalies),
            'recommendations': self._generate_recommendations(all_anomalies)
        }
    
    def _detect_visibility_gaps(self, assets: List[Dict[str, Any]]) -> List[str]:
        gaps = []
        
        for asset in assets:
            asset_id = asset.get('id', asset.get('hostname', 'unknown'))
            
            log_sources = sum([
                asset.get('splunk', False),
                asset.get('chronicle', False),
                asset.get('gso', False)
            ])
            
            if log_sources == 0:
                gaps.append(asset_id)
            
            if not asset.get('cmdb', False) and log_sources > 0:
                gaps.append(asset_id)
        
        return gaps
    
    def _detect_log_anomalies(self, assets: List[Dict[str, Any]]) -> List[str]:
        anomalies = []
        
        for asset in assets:
            asset_id = asset.get('id', asset.get('hostname', 'unknown'))
            
            has_logs = any([
                asset.get('splunk'),
                asset.get('chronicle'),
                asset.get('gso')
            ])
            
            has_log_types = any([
                asset.get('network_log_types'),
                asset.get('endpoint_log_types'),
                asset.get('application_log_types')
            ])
            
            if has_logs and not has_log_types:
                anomalies.append(asset_id)
        
        return anomalies
    
    def _detect_cmdb_issues(self, assets: List[Dict[str, Any]]) -> List[str]:
        issues = []
        
        for asset in assets:
            asset_id = asset.get('id', asset.get('hostname', 'unknown'))
            
            if asset.get('cmdb'):
                required_fields = ['infra_type', 'system_class', 'business_unit']
                missing_count = sum(1 for field in required_fields if not asset.get(field))
                
                if missing_count > 1:
                    issues.append(asset_id)
            
            if not asset.get('cmdb') and asset.get('sources', 0) > 2:
                issues.append(asset_id)
        
        return issues
    
    def _detect_security_gaps(self, assets: List[Dict[str, Any]]) -> List[str]:
        gaps = []
        
        for asset in assets:
            asset_id = asset.get('id', asset.get('hostname', 'unknown'))
            
            security_coverage = sum([
                asset.get('edr', False),
                asset.get('dlp', False),
                asset.get('tanium', False)
            ])
            
            system_class = asset.get('system_class', '').lower()
            if 'server' in system_class and security_coverage == 0:
                gaps.append(asset_id)
        
        return gaps
    
    def _detect_network_anomalies(self, assets: List[Dict[str, Any]]) -> List[str]:
        anomalies = []
        ip_subnets = defaultdict(list)
        
        for asset in assets:
            ip = asset.get('ip', '')
            if ip:
                try:
                    octets = ip.split('.')
                    if len(octets) == 4:
                        subnet = f"{octets[0]}.{octets[1]}.{octets[2]}.0"
                        asset_id = asset.get('id', asset.get('hostname'))
                        ip_subnets[subnet].append(asset_id)
                except:
                    pass
        
        for subnet, asset_ids in ip_subnets.items():
            if len(asset_ids) == 1 and len(ip_subnets) > 5:
                anomalies.extend(asset_ids)
        
        return anomalies
    
    def _create_summary(self, anomalies: Dict[str, List[str]]) -> Dict[str, Any]:
        total = sum(len(anomaly_list) for anomaly_list in anomalies.values())
        
        critical = (
            len(anomalies.get('visibility_gaps', [])) + 
            len(anomalies.get('security_coverage_gaps', []))
        )
        
        return {
            'total_anomalies': total,
            'critical_anomalies': critical,
            'anomaly_types': len(anomalies),
            'most_common_type': max(anomalies.keys(), key=lambda k: len(anomalies[k])) if anomalies else None
        }
    
    def _generate_recommendations(self, anomalies: Dict[str, List[str]]) -> List[str]:
        recommendations = []
        
        if anomalies.get('visibility_gaps'):
            recommendations.append("Address visibility gaps - assets without log coverage detected")
        
        if anomalies.get('security_coverage_gaps'):
            recommendations.append("Deploy security controls for uncovered assets")
        
        if anomalies.get('log_coverage_anomalies'):
            recommendations.append("Review log collection configuration")
        
        if anomalies.get('cmdb_inconsistencies'):
            recommendations.append("Update CMDB with missing asset information")
        
        if anomalies.get('network_anomalies'):
            recommendations.append("Review network segmentation and asset placement")
        
        return recommendations

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_engine = AO1VisibilityEngine(config)
        self.graph_analyzer = AssetGraphAnalyzer()
        self.anomaly_detector = VisibilityAnomalyDetector()
        
        self.performance_metrics = {
            'classifications': 0,
            'processing_times': [],
            'confidence_scores': [],
            'visibility_scores': []
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        
        logger.info("Starting AO1 enhanced discovery with visibility focus")
        start_time = datetime.now()
        
        discovered_assets = {}
        
        source_tables = {
            'cmdb': 'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'splunk': 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'crowdstrike': 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT'
        }
        
        if 'chronicle-fisv' in client_managers:
            source_tables['chronicle'] = 'chronicle-fisv.datalake.events'
        
        for source_name, table_path in source_tables.items():
            try:
                client_manager = client_managers.get('prj-fisv')
                if source_name == 'chronicle':
                    client_manager = client_managers.get('chronicle-fisv')
                
                if not client_manager:
                    continue
                
                logger.info(f"Processing {source_name} with AO1 enhancement")
                
                assets = await self._process_table_ao1(client_manager, table_path, source_name)
                
                for asset_id, asset in assets.items():
                    if asset_id in discovered_assets:
                        discovered_assets[asset_id] = self._merge_ao1_assets(
                            discovered_assets[asset_id], asset, source_name
                        )
                    else:
                        discovered_assets[asset_id] = asset
                
            except Exception as e:
                logger.error(f"AO1 processing failed for {source_name}: {e}")
        
        logger.info("Performing AO1 visibility analysis")
        asset_list = list(discovered_assets.values())
        
        visibility_analysis = {}
        if len(asset_list) > 1:
            visibility_analysis = await self._analyze_visibility_relationships(asset_list)
        
        anomaly_results = {}
        if len(asset_list) > 5:
            anomaly_results = await self._detect_visibility_anomalies(asset_list)
        
        insights = await self._generate_ao1_insights(discovered_assets, visibility_analysis, anomaly_results)
        recommendations = self._generate_ao1_recommendations(anomaly_results, visibility_analysis)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'discovery_stats': {
                'total_assets': len(discovered_assets),
                'processing_time': processing_time,
                'ao1_classifications': self.performance_metrics['classifications']
            },
            'assets': discovered_assets,
            'visibility_analysis': visibility_analysis,
            'anomaly_detection': anomaly_results,
            'ai_insights': insights,
            'recommendations': recommendations,
            'performance_metrics': self._get_performance_summary()
        }
    
    async def _process_table_ao1(self, client_manager, table_path: str, source_name: str) -> Dict[str, Any]:
        assets = {}
        
        with client_manager.get_client() as client:
            try:
                table = client.get_table(table_path)
                if not table.schema:
                    return assets
                
                columns = [field.name for field in table.schema]
                
                sample_query = f"""
                SELECT {', '.join([f'`{col}`' for col in columns[:20]])}
                FROM `{table_path}`
                WHERE RAND() < 0.01
                LIMIT 100
                """
                
                job = client.query(sample_query)
                results = list(job.result())
                
                if not results:
                    return assets
                
                field_mappings = {}
                ao1_metadata = {}
                
                for col_idx, column_name in enumerate(columns[:20]):
                    sample_values = []
                    for row in results:
                        if col_idx < len(row) and row[col_idx] is not None:
                            sample_values.append(str(row[col_idx]))
                    
                    if sample_values:
                        analysis = await self.visibility_engine.enhanced_classification(
                            column_name, sample_values, 
                            {'table_name': table_path.split('.')[-1], 'source': source_name}
                        )
                        
                        if analysis['confidence'] > 0.6:
                            field_type = analysis['field_type']
                            field_mappings[field_type] = column_name
                            ao1_metadata[field_type] = analysis['metadata']
                            self.performance_metrics['classifications'] += 1
                
                if 'hostname' in field_mappings:
                    assets = await self._extract_ao1_assets(client, table_path, field_mappings, ao1_metadata, source_name)
                
            except Exception as e:
                logger.error(f"AO1 table processing failed for {table_path}: {e}")
        
        return assets
    
    async def _extract_ao1_assets(self, client, table_path: str, mappings: Dict[str, str], 
                                metadata: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        
        hostname_col = mappings['hostname']
        assets = {}
        
        try:
            select_fields = [f"CAST(`{hostname_col}` AS STRING) as hostname"]
            
            for field_type, column_name in mappings.items():
                if field_type != 'hostname':
                    select_fields.append(f"CAST(`{column_name}` AS STRING) as {field_type}")
            
            query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{table_path}`
            WHERE `{hostname_col}` IS NOT NULL
            LIMIT 10000
            """
            
            job = client.query(query)
            results = list(job.result())
            
            for row in results:
                if not row or not row[0]:
                    continue
                
                hostname = str(row[0]).strip().upper()
                if not hostname or len(hostname) < 1:
                    continue
                
                asset_id = f"ao1_{hostname}_{source_name}"
                
                asset = {
                    'id': asset_id,
                    'hostname': hostname,
                    'ao1_enhanced': True,
                    'ao1_metadata': metadata,
                    'source': source_name
                }
                
                for idx, field_type in enumerate(mappings.keys()):
                    if idx < len(row) and row[idx]:
                        value = str(row[idx]).strip()
                        if value:
                            asset[field_type] = value
                
                self._set_ao1_source_flags(asset, source_name)
                asset['visibility_score'] = self._calculate_ao1_visibility_score(asset, metadata)
                
                assets[asset_id] = asset
                
        except Exception as e:
            logger.error(f"AO1 asset extraction failed: {e}")
        
        return assets
    
    def _set_ao1_source_flags(self, asset: Dict[str, Any], source: str):
        flags = {
            'cmdb': {'cmdb': True},
            'splunk': {'splunk': True},
            'chronicle': {'chronicle': True},
            'crowdstrike': {'crowdstrike': True, 'edr': True}
        }
        
        source_flags = flags.get(source, {})
        for flag, value in source_flags.items():
            asset[flag] = value
    
    def _calculate_ao1_visibility_score(self, asset: Dict[str, Any], metadata: Dict[str, Any]) -> float:
        factors = []
        
        log_sources = sum([
            asset.get('splunk', False),
            asset.get('chronicle', False),
            asset.get('gso', False)
        ])
        log_score = min(1.0, log_sources / 3.0)
        factors.append(('log_coverage', log_score, 0.4))
        
        cmdb_score = 1.0 if asset.get('cmdb') else 0.0
        factors.append(('cmdb_coverage', cmdb_score, 0.3))
        
        security_coverage = sum([
            asset.get('edr', False),
            asset.get('dlp', False),
            asset.get('tanium', False)
        ])
        security_score = min(1.0, security_coverage / 3.0)
        factors.append(('security_coverage', security_score, 0.2))
        
        field_completeness = len([f for f in ['hostname', 'ip_address', 'infra_type'] 
                                if asset.get(f)]) / 3.0
        factors.append(('field_completeness', field_completeness, 0.1))
        
        total_score = sum(score * weight for _, score, weight in factors)
        
        if metadata:
            ai_boost = statistics.mean([m.get('visibility_score', 0) for m in metadata.values()])
            total_score = total_score * (1 + ai_boost * 0.2)
        
        return min(1.0, total_score)
    
    def _merge_ao1_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any], source: str) -> Dict[str, Any]:
        merged = primary.copy()
        
        for key, value in secondary.items():
            if key not in merged or not merged[key]:
                merged[key] = value
        
        merged['sources'] = merged.get('sources', 1) + 1
        merged['source_list'] = f"{merged.get('source_list', primary.get('source', ''))},{source}"
        
        primary_vis = primary.get('visibility_score', 0)
        secondary_vis = secondary.get('visibility_score', 0)
        merged['visibility_score'] = max(primary_vis, secondary_vis)
        
        return merged
    
    async def _analyze_visibility_relationships(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        asset_graph = self.graph_analyzer.build_visibility_graph(assets)
        
        clusters = self.graph_analyzer.find_visibility_clusters()
        centrality = self.graph_analyzer.get_visibility_centrality()
        gaps = self.graph_analyzer.find_visibility_gaps()
        
        return {
            'graph_stats': {
                'nodes': asset_graph.number_of_nodes(),
                'edges': asset_graph.number_of_edges(),
                'density': nx.density(asset_graph) if asset_graph.number_of_nodes() > 0 else 0
            },
            'visibility_clusters': clusters,
            'centrality_scores': centrality,
            'visibility_gaps': gaps
        }
    
    async def _detect_visibility_anomalies(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        return await asyncio.to_thread(self.anomaly_detector.detect_comprehensive_anomalies, assets)
    
    async def _generate_ao1_insights(self, assets: Dict[str, Any], visibility_analysis: Dict[str, Any], 
                                   anomaly_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        
        if assets:
            visibility_scores = [asset.get('visibility_score', 0) for asset in assets.values()]
            avg_visibility = statistics.mean(visibility_scores)
            
            insights.append({
                'type': 'ao1_visibility_analysis',
                'content': f"AO1 analysis: Average visibility score {avg_visibility:.2f}",
                'confidence': 0.95,
                'metrics': {
                    'avg_visibility': avg_visibility,
                    'total_assets': len(assets),
                    'ao1_enhanced': sum(1 for a in assets.values() if a.get('ao1_enhanced'))
                }
            })
        
        if visibility_analysis.get('visibility_clusters'):
            clusters = visibility_analysis['visibility_clusters']
            insights.append({
                'type': 'ao1_cluster_analysis',
                'content': f"Identified {len(clusters)} visibility clusters",
                'confidence': 0.85,
                'evidence': [f"Network analysis of {len(assets)} assets completed"]
            })
        
        if anomaly_results.get('anomaly_summary'):
            summary = anomaly_results['anomaly_summary']
            critical = summary.get('critical_anomalies', 0)
            if critical > 0:
                insights.append({
                    'type': 'ao1_anomaly_detection',
                    'content': f"Detected {critical} critical visibility anomalies",
                    'confidence': 0.8,
                    'recommendations': anomaly_results.get('recommendations', [])
                })
        
        return insights
    
    def _generate_ao1_recommendations(self, anomaly_results: Dict[str, Any], 
                                    visibility_analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if anomaly_results.get('recommendations'):
            recommendations.extend(anomaly_results['recommendations'])
        
        gaps = visibility_analysis.get('visibility_gaps', [])
        if len(gaps) > 10:
            recommendations.append("Review visibility architecture - many isolated assets detected")
        
        graph_stats = visibility_analysis.get('graph_stats', {})
        density = graph_stats.get('density', 0)
        if density < 0.3:
            recommendations.append("Low visibility interconnectivity detected")
        
        if not recommendations:
            recommendations = [
                "AO1 visibility analysis completed successfully",
                "Continue monitoring visibility metrics"
            ]
        
        return recommendations
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        metrics = self.performance_metrics
        
        if not metrics['confidence_scores']:
            return {'status': 'no_data'}
        
        return {
            'total_classifications': metrics['classifications'],
            'avg_processing_time': statistics.mean(metrics['processing_times']) if metrics['processing_times'] else 0,
            'avg_confidence': statistics.mean(metrics['confidence_scores']) if metrics['confidence_scores'] else 0,
            'avg_visibility': statistics.mean(metrics['visibility_scores']) if metrics['visibility_scores'] else 0
        }