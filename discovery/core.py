# discovery/core.py

import asyncio
import logging
import hashlib
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from core.types import Asset, TableSchema, Discovery, FieldMapping
from ai.intelligence import IntelligenceEngine

logger = logging.getLogger(__name__)

class SchemaAnalyzer:
    def __init__(self, intelligence: IntelligenceEngine):
        self.intelligence = intelligence
        self.cache = {}
    
    async def analyze_table(self, client, table_path: str) -> Optional[TableSchema]:
        cache_key = f"schema:{table_path}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            table_ref = client.get_table(table_path)
            if not table_ref.schema:
                return None
            
            columns = [field.name for field in table_ref.schema]
            schema = TableSchema(
                path=table_path,
                name=table_path.split('.')[-1],
                rows=table_ref.num_rows or 0,
                columns=len(columns)
            )
            
            samples = await self._sample_table(client, table_path, columns)
            
            for column_name, column_samples in samples.items():
                mapping = await self.intelligence.analyze_field_intelligently(
                    column_name, column_samples, {'table_path': table_path}
                )
                
                if mapping:
                    schema.mappings[mapping.field_type] = mapping
            
            schema.quality = self._calculate_schema_quality(schema)
            
            self.cache[cache_key] = schema
            return schema
            
        except Exception as e:
            logger.warning(f"Schema analysis failed for {table_path}: {e}")
            return None
    
    async def _sample_table(self, client, table_path: str, columns: List[str]) -> Dict[str, List[str]]:
        sample_query = f"""
        SELECT {', '.join([f'`{col}`' for col in columns[:50]])}
        FROM `{table_path}`
        WHERE RAND() < 0.05
        LIMIT 500
        """
        
        samples = {}
        try:
            job = client.query(sample_query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(columns[:50]):
                column_samples = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        column_samples.append(str(row[col_idx]))
                samples[column_name] = column_samples[:20]
                
        except Exception as e:
            logger.warning(f"Sampling failed for {table_path}: {e}")
        
        return samples
    
    def _calculate_schema_quality(self, schema: TableSchema) -> float:
        if not schema.mappings:
            return 0.0
        
        critical_fields = ['hostname', 'ip_address', 'infrastructure_type', 'system_classification']
        critical_count = sum(1 for field in critical_fields if field in schema.mappings)
        critical_score = critical_count / len(critical_fields)
        
        avg_confidence = statistics.mean([m.confidence for m in schema.mappings.values()])
        
        return (critical_score * 0.6) + (avg_confidence * 0.4)

class AssetExtractor:
    def __init__(self, intelligence: IntelligenceEngine):
        self.intelligence = intelligence
        self.similarity_threshold = 0.85
    
    async def extract_assets(self, client, schema: TableSchema, source_name: str) -> Dict[str, Asset]:
        if 'hostname' not in schema.mappings:
            return {}
        
        hostname_mapping = schema.mappings['hostname']
        assets = {}
        
        try:
            select_fields = [f"UPPER(TRIM(`{hostname_mapping.column}`)) as hostname"]
            field_mappings = {'hostname': hostname_mapping.column}
            
            for field_type, mapping in schema.mappings.items():
                if field_type != 'hostname':
                    select_fields.append(f"`{mapping.column}` as {field_type}")
                    field_mappings[field_type] = mapping.column
            
            extraction_query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{schema.path}`
            WHERE `{hostname_mapping.column}` IS NOT NULL
            AND TRIM(`{hostname_mapping.column}`) != ''
            LIMIT 500000
            """
            
            job = client.query(extraction_query)
            results = list(job.result())
            
            for row in results:
                if not row or not row[0]:
                    continue
                
                hostname = str(row[0]).strip().upper()
                if not hostname or len(hostname) < 1:
                    continue
                
                if hostname.upper() in ['NULL', 'NONE', 'UNKNOWN', '']:
                    continue
                
                asset_id = self._generate_asset_id(hostname)
                asset = Asset(id=asset_id, hostname=hostname)
                
                for idx, field_type in enumerate(field_mappings.keys()):
                    if idx < len(row) and row[idx]:
                        value = str(row[idx]).strip()
                        if value:
                            setattr(asset, self._field_to_attr(field_type), value)
                
                self._set_source_flags(asset, source_name)
                asset.sources = 1
                asset.intelligence = self._calculate_intelligence_score(asset)
                asset.quality = self._calculate_quality_score(asset)
                asset.confidence = self._calculate_confidence_score(asset)
                
                assets[asset_id] = asset
            
        except Exception as e:
            logger.error(f"Asset extraction failed for {schema.path}: {e}")
        
        return assets
    
    def _generate_asset_id(self, hostname: str) -> str:
        normalized = hostname.upper().strip()
        return f"asset_{hashlib.md5(normalized.encode()).hexdigest()[:12]}"
    
    def _field_to_attr(self, field_type: str) -> str:
        field_map = {
            'ip_address': 'ip',
            'infrastructure_type': 'infra_type',
            'system_classification': 'system_class',
            'global_region': 'region',
            'cloud_region': 'cloud_region',
            'business_unit': 'business_unit',
            'application_class': 'app_class'
        }
        return field_map.get(field_type, field_type)
    
    def _set_source_flags(self, asset: Asset, source: str):
        source_flags = {
            'cmdb': {'cmdb': True},
            'splunk': {'splunk': True},
            'chronicle': {'chronicle': True},
            'crowdstrike': {'crowdstrike': True, 'edr': True}
        }
        
        flags = source_flags.get(source, {})
        for attr, value in flags.items():
            setattr(asset, attr, value)
    
    def _calculate_intelligence_score(self, asset: Asset) -> float:
        factors = []
        
        critical_fields = [asset.hostname, asset.infra_type, asset.system_class]
        completeness = sum(1 for field in critical_fields if field) / len(critical_fields)
        factors.append(completeness * 0.4)
        
        all_fields = [asset.hostname, asset.ip, asset.fqdn, asset.infra_type, 
                     asset.system_class, asset.region, asset.business_unit]
        overall_completeness = sum(1 for field in all_fields if field) / len(all_fields)
        factors.append(overall_completeness * 0.3)
        
        security_coverage = sum([asset.edr, asset.dlp, asset.tanium]) / 3.0
        factors.append(security_coverage * 0.2)
        
        log_coverage = sum([asset.splunk, asset.chronicle, asset.gso]) / 3.0
        factors.append(log_coverage * 0.1)
        
        return sum(factors)
    
    def _calculate_quality_score(self, asset: Asset) -> float:
        quality_factors = []
        
        if asset.hostname:
            quality_factors.append(0.9 if self._is_valid_hostname(asset.hostname) else 0.3)
        
        if asset.ip:
            quality_factors.append(0.9 if self._is_valid_ip(asset.ip) else 0.1)
        
        if asset.fqdn:
            quality_factors.append(0.8 if self._is_valid_fqdn(asset.fqdn) else 0.2)
        
        consistency = 1.0
        if asset.hostname and asset.fqdn:
            if asset.hostname.lower() not in asset.fqdn.lower():
                consistency *= 0.8
        
        quality_factors.append(consistency)
        
        return statistics.mean(quality_factors) if quality_factors else 0.5
    
    def _calculate_confidence_score(self, asset: Asset) -> float:
        source_weights = {'cmdb': 0.9, 'crowdstrike': 0.85, 'splunk': 0.7, 'chronicle': 0.75}
        
        source_confidence = 0.5
        if asset.cmdb:
            source_confidence = max(source_confidence, source_weights['cmdb'])
        if asset.crowdstrike:
            source_confidence = max(source_confidence, source_weights['crowdstrike'])
        if asset.splunk:
            source_confidence = max(source_confidence, source_weights['splunk'])
        if asset.chronicle:
            source_confidence = max(source_confidence, source_weights['chronicle'])
        
        return (source_confidence * 0.5) + (asset.quality * 0.3) + (asset.intelligence * 0.2)
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        import re
        if not hostname or not (2 <= len(hostname) <= 253):
            return False
        
        patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9],
            r'^[a-zA-Z0-9]+
        ]
        
        return any(re.match(pattern, hostname, re.IGNORECASE) for pattern in patterns)
    
    def _is_valid_ip(self, ip: str) -> bool:
        import ipaddress
        try:
            ipaddress.ip_address(ip.strip())
            return True
        except:
            return False
    
    def _is_valid_fqdn(self, fqdn: str) -> bool:
        import re
        if not fqdn or not (4 <= len(fqdn) <= 253):
            return False
        
        if fqdn.count('.') < 1:
            return False
        
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}
        return bool(re.match(pattern, fqdn, re.IGNORECASE))

class AssetMerger:
    def __init__(self):
        self.similarity_threshold = 0.85
        self.conflict_rules = {'cmdb': 4, 'crowdstrike': 3, 'splunk': 2, 'chronicle': 1}
    
    def merge_assets(self, assets: Dict[str, Asset]) -> Dict[str, Asset]:
        merged = {}
        processed = set()
        
        for asset_id, asset in assets.items():
            if asset_id in processed:
                continue
            
            similar_assets = self._find_similar_assets(asset, assets, processed)
            
            if similar_assets:
                merged_asset = asset
                for similar_id, similar_asset in similar_assets:
                    merged_asset = self._merge_two_assets(merged_asset, similar_asset)
                    processed.add(similar_id)
                
                merged[asset_id] = merged_asset
            else:
                merged[asset_id] = asset
            
            processed.add(asset_id)
        
        return merged
    
    def _find_similar_assets(self, target: Asset, all_assets: Dict[str, Asset], 
                           processed: set) -> List[Tuple[str, Asset]]:
        similar = []
        
        for asset_id, asset in all_assets.items():
            if asset_id in processed or asset_id == target.id:
                continue
            
            similarity = self._calculate_similarity(target, asset)
            if similarity >= self.similarity_threshold:
                similar.append((asset_id, asset))
        
        return similar
    
    def _calculate_similarity(self, asset1: Asset, asset2: Asset) -> float:
        factors = []
        
        if asset1.hostname and asset2.hostname:
            hostname_sim = self._string_similarity(asset1.hostname.upper(), asset2.hostname.upper())
            factors.append(('hostname', hostname_sim, 0.4))
        
        if asset1.ip and asset2.ip:
            if asset1.ip == asset2.ip:
                factors.append(('ip_exact', 1.0, 0.3))
            else:
                ip_sim = self._ip_similarity(asset1.ip, asset2.ip)
                factors.append(('ip_subnet', ip_sim, 0.2))
        
        if asset1.fqdn and asset2.fqdn:
            fqdn_sim = self._string_similarity(asset1.fqdn.lower(), asset2.fqdn.lower())
            factors.append(('fqdn', fqdn_sim, 0.2))
        
        if asset1.mac and asset2.mac:
            if asset1.mac == asset2.mac:
                factors.append(('mac_exact', 1.0, 0.1))
        
        if not factors:
            return 0.0
        
        weighted_score = sum(score * weight for _, score, weight in factors)
        total_weight = sum(weight for _, _, weight in factors)
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        if str1 == str2:
            return 1.0
        
        if not str1 or not str2:
            return 0.0
        
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return 1.0
        
        common_chars = sum(1 for c in shorter if c in longer)
        return common_chars / len(longer)
    
    def _ip_similarity(self, ip1: str, ip2: str) -> float:
        try:
            import ipaddress
            addr1 = ipaddress.ip_address(ip1)
            addr2 = ipaddress.ip_address(ip2)
            
            if addr1.version != addr2.version or addr1.version != 4:
                return 0.0
            
            octets1 = str(addr1).split('.')
            octets2 = str(addr2).split('.')
            
            matching_octets = sum(1 for o1, o2 in zip(octets1, octets2) if o1 == o2)
            return matching_octets / 4
        except:
            return 0.0
    
    def _merge_two_assets(self, primary: Asset, secondary: Asset) -> Asset:
        merged = Asset(id=primary.id)
        
        text_fields = ['hostname', 'ip', 'fqdn', 'mac', 'infra_type', 'system_class',
                      'region', 'country', 'datacenter', 'cloud_region', 'business_unit',
                      'cio', 'app_class']
        
        for field in text_fields:
            primary_val = getattr(primary, field, "")
            secondary_val = getattr(secondary, field, "")
            merged_val = self._resolve_conflict(field, primary_val, secondary_val, primary, secondary)
            setattr(merged, field, merged_val)
        
        bool_fields = ['edr', 'dlp', 'tanium', 'splunk', 'chronicle', 'gso', 'cmdb', 'crowdstrike']
        for field in bool_fields:
            primary_val = getattr(primary, field, False)
            secondary_val = getattr(secondary, field, False)
            setattr(merged, field, primary_val or secondary_val)
        
        merged.sources = primary.sources + secondary.sources
        merged.intelligence = max(primary.intelligence, secondary.intelligence)
        merged.quality = (primary.quality + secondary.quality) / 2
        merged.confidence = max(primary.confidence, secondary.confidence)
        
        return merged
    
    def _resolve_conflict(self, field: str, primary_val: str, secondary_val: str, 
                         primary: Asset, secondary: Asset) -> str:
        if not secondary_val or secondary_val.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE']:
            return primary_val
        
        if not primary_val or primary_val.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE']:
            return secondary_val
        
        if primary_val == secondary_val:
            return primary_val
        
        primary_priority = self._get_source_priority(primary)
        secondary_priority = self._get_source_priority(secondary)
        
        if secondary_priority > primary_priority:
            return secondary_val
        elif secondary_priority < primary_priority:
            return primary_val
        else:
            return secondary_val if len(secondary_val) > len(primary_val) else primary_val
    
    def _get_source_priority(self, asset: Asset) -> int:
        if asset.cmdb:
            return self.conflict_rules['cmdb']
        elif asset.crowdstrike:
            return self.conflict_rules['crowdstrike']
        elif asset.splunk:
            return self.conflict_rules['splunk']
        elif asset.chronicle:
            return self.conflict_rules['chronicle']
        else:
            return 0

class DiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], 
                 cache_manager, intelligence: IntelligenceEngine):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        
        self.schema_analyzer = SchemaAnalyzer(intelligence)
        self.asset_extractor = AssetExtractor(intelligence)
        self.asset_merger = AssetMerger()
        
        self.source_tables = {
            'cmdb': 'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'splunk': 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'crowdstrike': 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT'
        }
        
        self.stats = {
            'tables_analyzed': 0,
            'schemas_discovered': 0,
            'assets_extracted': 0,
            'assets_merged': 0,
            'processing_errors': 0
        }
    
    async def discover_assets(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting intelligent asset discovery")
        start_time = datetime.now()
        
        discovery = Discovery()
        all_assets = {}
        
        for source_name, table_path in self.source_tables.items():
            try:
                client_manager = client_managers.get(self.project_id)
                if source_name == 'chronicle' and 'chronicle-fisv' in client_managers:
                    client_manager = client_managers['chronicle-fisv']
                    table_path = 'chronicle-fisv.datalake.events'
                
                if not client_manager:
                    continue
                
                logger.info(f"Processing {source_name}: {table_path}")
                
                with client_manager.get_client() as client:
                    schema = await self.schema_analyzer.analyze_table(client, table_path)
                    
                    if schema:
                        discovery.schemas[table_path] = schema
                        self.stats['schemas_discovered'] += 1
                        
                        assets = await self.asset_extractor.extract_assets(client, schema, source_name)
                        
                        for asset_id, asset in assets.items():
                            if asset_id in all_assets:
                                all_assets[asset_id] = self.asset_merger._merge_two_assets(
                                    all_assets[asset_id], asset
                                )
                                self.stats['assets_merged'] += 1
                            else:
                                all_assets[asset_id] = asset
                                self.stats['assets_extracted'] += 1
                        
                        logger.info(f"Extracted {len(assets)} assets from {source_name}")
                
                self.stats['tables_analyzed'] += 1
                
            except Exception as e:
                logger.error(f"Failed to process {source_name}: {e}")
                self.stats['processing_errors'] += 1
        
        logger.info("Performing final asset consolidation")
        discovery.assets = self.asset_merger.merge_assets(all_assets)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        discovery.stats = {
            'total_assets': len(discovery.assets),
            'high_quality_assets': sum(1 for a in discovery.assets.values() if a.quality > 0.8),
            'multi_source_assets': sum(1 for a in discovery.assets.values() if a.sources > 1),
            'processing_time_seconds': processing_time,
            'performance_stats': self.stats
        }
        
        discovery.insights = await self.intelligence.generate_insights(discovery)
        
        logger.info(f"Discovery complete: {len(discovery.assets)} unique assets discovered")
        return discovery