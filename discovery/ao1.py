import asyncio
import logging
import re
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class AO1VisibilityEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_weights = {
            'log_coverage': 0.4,
            'cmdb_coverage': 0.3,
            'security_coverage': 0.2,
            'field_completeness': 0.1
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
        
        content_analysis = await self._analyze_visibility_content(samples, 'unknown')
        final_confidence = content_analysis['confidence']
        
        metadata = {
            'ai_confidence': final_confidence,
            'content_confidence': content_analysis['confidence'],
            'visibility_score': self._calculate_visibility_score(samples, 'unknown'),
            'log_visibility_score': self._calculate_log_visibility(samples, 'unknown'),
            'cmdb_alignment_score': self._calculate_cmdb_alignment(samples, 'unknown'),
            'security_relevance': self._assess_security_relevance(samples, 'unknown'),
            'ao1_enhanced': True
        }
        
        return {
            'field_type': 'unknown',
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
        
        patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)
    
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
        if field_type in ['hostname', 'ip_address', 'fqdn']:
            return 0.9
        elif field_type in ['log_type', 'network_log_types', 'endpoint_log_types']:
            return 0.8
        elif field_type in ['edr_coverage', 'dlp_coverage', 'security']:
            return 0.7
        return 0.5
    
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

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_engine = AO1VisibilityEngine(config)
        
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
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'discovery_stats': {
                'total_assets': len(discovered_assets),
                'processing_time': processing_time,
                'ao1_classifications': self.performance_metrics['classifications']
            },
            'assets': discovered_assets,
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