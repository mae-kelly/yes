# discovery/core.py - enhanced version

import asyncio
import logging
import hashlib
import statistics
import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
from core.types import Asset, TableSchema, Discovery, FieldMapping
from ai.intelligence import EnhancedIntelligenceEngine
import ipaddress
import re

logger = logging.getLogger(__name__)

class EntityResolver:
    def __init__(self):
        self.identity_graph = nx.Graph()
        self.hostname_patterns = [
            r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)$',
            r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        ]
        self.identity_clusters = {}
        self.confidence_thresholds = {
            'exact_match': 1.0,
            'hostname_variant': 0.95,
            'ip_correlation': 0.8,
            'subnet_correlation': 0.6,
            'name_similarity': 0.7
        }
    
    def add_asset_evidence(self, identifiers: Dict[str, str], source: str, confidence: float = 1.0):
        primary_id = self._generate_primary_id(identifiers)
        
        for id_type, value in identifiers.items():
            if value and self._is_valid_identifier(id_type, value):
                normalized = self._normalize_identifier(id_type, value)
                self.identity_graph.add_node(normalized, type=id_type, source=source, confidence=confidence)
                
                for other_type, other_value in identifiers.items():
                    if other_type != id_type and other_value:
                        other_normalized = self._normalize_identifier(other_type, other_value)
                        similarity = self._calculate_identity_similarity(
                            (id_type, normalized), (other_type, other_normalized)
                        )
                        if similarity > 0.5:
                            self.identity_graph.add_edge(normalized, other_normalized, 
                                                       weight=similarity, evidence=source)
    
    def resolve_entities(self) -> Dict[str, Set[str]]:
        communities = list(nx.community.greedy_modularity_communities(self.identity_graph))
        
        entity_groups = {}
        for i, community in enumerate(communities):
            canonical_id = f"entity_{i:06d}"
            entity_groups[canonical_id] = community
        
        return entity_groups
    
    def _generate_primary_id(self, identifiers: Dict[str, str]) -> str:
        if 'hostname' in identifiers and identifiers['hostname']:
            return f"host_{identifiers['hostname'].upper()}"
        elif 'ip_address' in identifiers and identifiers['ip_address']:
            return f"ip_{identifiers['ip_address']}"
        elif 'fqdn' in identifiers and identifiers['fqdn']:
            return f"fqdn_{identifiers['fqdn'].lower()}"
        else:
            return f"unknown_{hash(str(identifiers)) % 1000000:06d}"
    
    def _is_valid_identifier(self, id_type: str, value: str) -> bool:
        if not value or value.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '']:
            return False
        
        if id_type == 'hostname':
            return any(re.match(pattern, value, re.IGNORECASE) for pattern in self.hostname_patterns)
        elif id_type == 'ip_address':
            try:
                ipaddress.ip_address(value.strip())
                return True
            except:
                return False
        elif id_type == 'fqdn':
            return '.' in value and len(value.split('.')) >= 2
        elif id_type == 'mac_address':
            return re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', value)
        
        return True
    
    def _normalize_identifier(self, id_type: str, value: str) -> str:
        value = value.strip()
        
        if id_type == 'hostname':
            return value.upper()
        elif id_type == 'ip_address':
            try:
                return str(ipaddress.ip_address(value))
            except:
                return value
        elif id_type == 'fqdn':
            return value.lower()
        elif id_type == 'mac_address':
            return value.upper().replace('-', ':')
        
        return value.upper()
    
    def _calculate_identity_similarity(self, id1: Tuple[str, str], id2: Tuple[str, str]) -> float:
        type1, value1 = id1
        type2, value2 = id2
        
        if type1 == type2:
            if value1 == value2:
                return self.confidence_thresholds['exact_match']
            elif type1 == 'hostname':
                return self._hostname_similarity(value1, value2)
            else:
                return 0.0
        
        if (type1 == 'hostname' and type2 == 'fqdn') or (type1 == 'fqdn' and type2 == 'hostname'):
            short_name = value1 if type1 == 'hostname' else value2
            fqdn = value2 if type1 == 'hostname' else value1
            
            if fqdn.upper().startswith(short_name.upper() + '.'):
                return self.confidence_thresholds['hostname_variant']
        
        if type1 == 'ip_address' and type2 == 'ip_address':
            return self._ip_similarity(value1, value2)
        
        return 0.0
    
    def _hostname_similarity(self, hostname1: str, hostname2: str) -> float:
        if hostname1 == hostname2:
            return 1.0
        
        h1_parts = re.split(r'[-_.]', hostname1.lower())
        h2_parts = re.split(r'[-_.]', hostname2.lower())
        
        common_parts = set(h1_parts) & set(h2_parts)
        total_parts = set(h1_parts) | set(h2_parts)
        
        if len(total_parts) == 0:
            return 0.0
        
        similarity = len(common_parts) / len(total_parts)
        
        if similarity > 0.7:
            return self.confidence_thresholds['name_similarity']
        
        return similarity * 0.5
    
    def _ip_similarity(self, ip1: str, ip2: str) -> float:
        if ip1 == ip2:
            return self.confidence_thresholds['exact_match']
        
        try:
            addr1 = ipaddress.ip_address(ip1)
            addr2 = ipaddress.ip_address(ip2)
            
            for prefix_len in [24, 16, 8]:
                net1 = ipaddress.ip_network(f"{addr1}/{prefix_len}", strict=False)
                net2 = ipaddress.ip_network(f"{addr2}/{prefix_len}", strict=False)
                
                if net1 == net2:
                    return self.confidence_thresholds['subnet_correlation'] * (prefix_len / 24)
            
        except:
            pass
        
        return 0.0

class ComprehensiveAssetBuilder:
    def __init__(self, intelligence: EnhancedIntelligenceEngine):
        self.intelligence = intelligence
        self.entity_resolver = EntityResolver()
        self.field_extractors = {}
        self.source_reliability = {
            'cmdb': 0.95,
            'crowdstrike': 0.9,
            'splunk': 0.85,
            'chronicle': 0.8,
            'tanium': 0.75,
            'network': 0.7
        }
        self.comprehensive_fields = {
            'identity': ['hostname', 'ip_address', 'fqdn', 'mac_address'],
            'infrastructure': ['infrastructure_type', 'system_classification', 'application_type'],
            'location': ['global_region', 'country', 'datacenter', 'cloud_region'],
            'organization': ['business_unit', 'cio', 'apm', 'application_class'],
            'security_coverage': ['edr_coverage', 'dlp_coverage', 'tanium_coverage'],
            'logging_coverage': ['splunk_coverage', 'chronicle_coverage', 'gso_coverage'],
            'log_types': ['network_log_types', 'endpoint_log_types', 'cloud_log_types', 
                         'application_log_types', 'identity_log_types'],
            'visibility': ['cmdb_visibility', 'url_fqdn_coverage', 'public_ip_coverage', 
                          'network_zones', 'vpc_coverage']
        }
    
    async def build_comprehensive_inventory(self, client_managers: Dict[str, Any]) -> Dict[str, Asset]:
        logger.info("Building comprehensive asset inventory with entity resolution")
        
        all_evidence = []
        table_schemas = {}
        
        for project_id, client_manager in client_managers.items():
            with client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=project_id))
                
                for dataset in datasets:
                    tables = list(client.list_tables(dataset))
                    
                    for table_ref in tables:
                        table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                        
                        try:
                            evidence = await self._extract_table_evidence(client, table_path)
                            all_evidence.extend(evidence)
                            
                            schema = await self._analyze_table_schema(client, table_path)
                            if schema:
                                table_schemas[table_path] = schema
                                
                        except Exception as e:
                            logger.warning(f"Failed to process {table_path}: {e}")
        
        logger.info(f"Collected {len(all_evidence)} pieces of evidence from {len(table_schemas)} tables")
        
        for evidence in all_evidence:
            self.entity_resolver.add_asset_evidence(
                evidence['identifiers'], 
                evidence['source'], 
                evidence['confidence']
            )
        
        entity_groups = self.entity_resolver.resolve_entities()
        logger.info(f"Resolved {len(entity_groups)} unique entities")
        
        assets = {}
        for entity_id, identifiers in entity_groups.items():
            asset = await self._build_complete_asset(entity_id, identifiers, all_evidence)
            if asset:
                assets[entity_id] = asset
        
        return assets
    
    async def _extract_table_evidence(self, client, table_path: str) -> List[Dict[str, Any]]:
        evidence = []
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return evidence
            
            columns = [field.name for field in table.schema]
            potential_hostname_cols = self._identify_hostname_columns(columns)
            
            if not potential_hostname_cols:
                return evidence
            
            for hostname_col in potential_hostname_cols[:3]:
                sample_query = f"""
                SELECT *
                FROM `{table_path}`
                WHERE `{hostname_col}` IS NOT NULL
                AND LENGTH(`{hostname_col}`) BETWEEN 2 AND 253
                LIMIT 50000
                """
                
                job = client.query(sample_query)
                results = list(job.result())
                
                for row in results:
                    if not row:
                        continue
                    
                    identifiers = {}
                    properties = {}
                    
                    for col_idx, col_name in enumerate(columns):
                        if col_idx < len(row) and row[col_idx] is not None:
                            value = str(row[col_idx]).strip()
                            
                            field_type = self._classify_field(col_name, value)
                            
                            if field_type in ['hostname', 'ip_address', 'fqdn', 'mac_address']:
                                identifiers[field_type] = value
                            else:
                                properties[col_name] = value
                    
                    if identifiers:
                        evidence.append({
                            'identifiers': identifiers,
                            'properties': properties,
                            'source': table_path,
                            'confidence': self._calculate_evidence_confidence(identifiers, table_path)
                        })
        
        except Exception as e:
            logger.error(f"Evidence extraction failed for {table_path}: {e}")
        
        return evidence
    
    def _identify_hostname_columns(self, columns: List[str]) -> List[str]:
        hostname_candidates = []
        
        exact_matches = ['hostname', 'host', 'computer_name', 'computername', 
                        'device_name', 'endpoint_name', 'machine_name', 'server_name']
        
        for col in columns:
            col_lower = col.lower()
            
            for exact in exact_matches:
                if exact in col_lower:
                    hostname_candidates.append(col)
                    break
        
        partial_indicators = ['host', 'computer', 'machine', 'device', 'endpoint', 'server', 'node']
        
        for col in columns:
            if col in hostname_candidates:
                continue
                
            col_lower = col.lower()
            for indicator in partial_indicators:
                if indicator in col_lower and 'id' not in col_lower and 'count' not in col_lower:
                    hostname_candidates.append(col)
                    break
        
        return hostname_candidates[:5]
    
    def _classify_field(self, column_name: str, value: str) -> str:
        if not value:
            return 'unknown'
        
        col_lower = column_name.lower()
        
        if any(indicator in col_lower for indicator in ['hostname', 'host', 'computer', 'machine', 'device']):
            if self.entity_resolver._is_valid_identifier('hostname', value):
                return 'hostname'
        
        if 'ip' in col_lower or 'address' in col_lower:
            if self.entity_resolver._is_valid_identifier('ip_address', value):
                return 'ip_address'
        
        if 'fqdn' in col_lower or 'domain' in col_lower:
            if self.entity_resolver._is_valid_identifier('fqdn', value):
                return 'fqdn'
        
        if 'mac' in col_lower:
            if self.entity_resolver._is_valid_identifier('mac_address', value):
                return 'mac_address'
        
        return 'property'
    
    def _calculate_evidence_confidence(self, identifiers: Dict[str, str], source: str) -> float:
        base_confidence = self.source_reliability.get(self._extract_source_system(source), 0.5)
        
        identifier_quality = 0.0
        if 'hostname' in identifiers:
            identifier_quality += 0.4
        if 'ip_address' in identifiers:
            identifier_quality += 0.3
        if 'fqdn' in identifiers:
            identifier_quality += 0.2
        if 'mac_address' in identifiers:
            identifier_quality += 0.1
        
        return min(1.0, base_confidence + identifier_quality)
    
    def _extract_source_system(self, table_path: str) -> str:
        path_lower = table_path.lower()
        
        if 'endpoint' in path_lower or 'cmdb' in path_lower:
            return 'cmdb'
        elif 'crowdstrike' in path_lower or 'endpointagent' in path_lower:
            return 'crowdstrike'
        elif 'splunk' in path_lower or 'spl_' in path_lower:
            return 'splunk'
        elif 'chronicle' in path_lower:
            return 'chronicle'
        elif 'tanium' in path_lower:
            return 'tanium'
        else:
            return 'unknown'
    
    async def _analyze_table_schema(self, client, table_path: str) -> Optional[Dict[str, Any]]:
        try:
            table = client.get_table(table_path)
            if not table.schema:
                return None
            
            columns = [field.name for field in table.schema]
            
            schema_analysis = {
                'path': table_path,
                'columns': columns,
                'row_count': table.num_rows,
                'source_system': self._extract_source_system(table_path),
                'hostname_columns': self._identify_hostname_columns(columns),
                'field_types': {}
            }
            
            for col in columns[:50]:
                sample_query = f"""
                SELECT `{col}`
                FROM `{table_path}`
                WHERE `{col}` IS NOT NULL
                LIMIT 100
                """
                
                try:
                    job = client.query(sample_query)
                    samples = [str(row[0]) for row in job.result() if row[0]]
                    
                    if samples:
                        field_type = self._classify_field(col, samples[0])
                        schema_analysis['field_types'][col] = field_type
                        
                except:
                    continue
            
            return schema_analysis
            
        except Exception as e:
            logger.warning(f"Schema analysis failed for {table_path}: {e}")
            return None
    
    async def _build_complete_asset(self, entity_id: str, identifiers: Set[str], 
                                  all_evidence: List[Dict[str, Any]]) -> Optional[Asset]:
        
        relevant_evidence = [
            ev for ev in all_evidence 
            if any(self.entity_resolver._normalize_identifier(k, v) in identifiers 
                  for k, v in ev['identifiers'].items())
        ]
        
        if not relevant_evidence:
            return None
        
        asset = Asset(id=entity_id)
        field_values = defaultdict(list)
        field_sources = defaultdict(list)
        
        for evidence in relevant_evidence:
            for field_name, value in evidence['identifiers'].items():
                if value:
                    field_values[field_name].append({
                        'value': value,
                        'confidence': evidence['confidence'],
                        'source': evidence['source']
                    })
            
            for field_name, value in evidence['properties'].items():
                if value:
                    mapped_field = self._map_field_name(field_name)
                    field_values[mapped_field].append({
                        'value': value,
                        'confidence': evidence['confidence'],
                        'source': evidence['source']
                    })
        
        for field_name, value_list in field_values.items():
            best_value = self._select_best_value(value_list)
            if best_value and hasattr(asset, field_name):
                setattr(asset, field_name, best_value)
        
        self._set_coverage_flags(asset, relevant_evidence)
        self._calculate_asset_metrics(asset, relevant_evidence)
        
        return asset
    
    def _map_field_name(self, original_name: str) -> str:
        name_lower = original_name.lower()
        
        field_mappings = {
            'infrastructure_type': ['infra_type', 'infrastructure', 'server_type'],
            'system_classification': ['system_class', 'os_type', 'platform'],
            'global_region': ['region', 'geo_region'],
            'business_unit': ['bu', 'org_unit', 'department'],
            'application_class': ['app_class', 'application_type'],
            'ip_address': ['ip', 'ip_addr'],
            'mac_address': ['mac', 'physical_address']
        }
        
        for target_field, variants in field_mappings.items():
            if any(variant in name_lower for variant in variants):
                return target_field
        
        return original_name.lower().replace(' ', '_')
    
    def _select_best_value(self, value_list: List[Dict[str, Any]]) -> Optional[str]:
        if not value_list:
            return None
        
        value_list.sort(key=lambda x: (
            x['confidence'],
            self.source_reliability.get(self._extract_source_system(x['source']), 0.5),
            len(x['value'])
        ), reverse=True)
        
        return value_list[0]['value']
    
    def _set_coverage_flags(self, asset: Asset, evidence: List[Dict[str, Any]]):
        sources = set()
        for ev in evidence:
            source_system = self._extract_source_system(ev['source'])
            sources.add(source_system)
        
        asset.cmdb = 'cmdb' in sources
        asset.crowdstrike = 'crowdstrike' in sources
        asset.edr = 'crowdstrike' in sources
        asset.splunk = 'splunk' in sources
        asset.chronicle = 'chronicle' in sources
        asset.tanium = 'tanium' in sources
        asset.dlp = any('dlp' in ev['source'].lower() for ev in evidence)
        
        asset.sources = len(sources)
    
    def _calculate_asset_metrics(self, asset: Asset, evidence: List[Dict[str, Any]]):
        if evidence:
            asset.confidence = statistics.mean([ev['confidence'] for ev in evidence])
            asset.intelligence = min(1.0, len(evidence) / 10.0)
            asset.quality = self._calculate_data_quality(asset)
        else:
            asset.confidence = 0.0
            asset.intelligence = 0.0
            asset.quality = 0.0
    
    def _calculate_data_quality(self, asset: Asset) -> float:
        completeness_score = 0.0
        total_fields = 0
        
        important_fields = ['hostname', 'ip', 'infra_type', 'system_class', 'business_unit']
        
        for field in important_fields:
            total_fields += 1
            if hasattr(asset, field) and getattr(asset, field):
                completeness_score += 1
        
        completeness = completeness_score / total_fields if total_fields > 0 else 0.0
        
        coverage_score = asset.sources / 5.0 if asset.sources <= 5 else 1.0
        
        return (completeness * 0.7) + (coverage_score * 0.3)

class EnhancedDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], 
                 cache_manager, intelligence: EnhancedIntelligenceEngine):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        self.asset_builder = ComprehensiveAssetBuilder(intelligence)
        
        self.stats = {
            'tables_processed': 0,
            'evidence_collected': 0,
            'entities_resolved': 0,
            'assets_built': 0,
            'processing_errors': 0
        }
    
    async def discover_assets_comprehensively(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting comprehensive asset discovery with entity resolution")
        start_time = datetime.now()
        
        discovery = Discovery()
        
        try:
            assets = await self.asset_builder.build_comprehensive_inventory(client_managers)
            discovery.assets = assets
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            discovery.stats = {
                'total_assets': len(assets),
                'high_quality_assets': sum(1 for a in assets.values() if a.quality > 0.8),
                'multi_source_assets': sum(1 for a in assets.values() if a.sources > 1),
                'cmdb_assets': sum(1 for a in assets.values() if a.cmdb),
                'security_covered_assets': sum(1 for a in assets.values() if a.edr or a.dlp or a.tanium),
                'processing_time_seconds': processing_time,
                'comprehensive_discovery': True,
                'entity_resolution_applied': True
            }
            
            discovery.insights = await self.intelligence.generate_insights(discovery)
            
            logger.info(f"Comprehensive discovery complete: {len(assets)} assets discovered")
            
        except Exception as e:
            logger.error(f"Comprehensive discovery failed: {e}")
            discovery.stats = {'error': str(e)}
        
        return discovery