# discovery/core.py

import asyncio
import logging
import hashlib
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from core.types import Asset, TableSchema, Discovery, FieldMapping
from ai.intelligence import EnhancedIntelligenceEngine

logger = logging.getLogger(__name__)

class AdvancedSchemaAnalyzer:
    def __init__(self, intelligence: EnhancedIntelligenceEngine):
        self.intelligence = intelligence
        self.cache = {}
        self.table_insights = {}
    
    async def analyze_table_deeply(self, client, table_path: str) -> Optional[TableSchema]:
        cache_key = f"deep_schema:{table_path}"
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
            
            sample_data = await self._intelligent_sampling(client, table_path, columns)
            
            table_analysis = await self.intelligence.analyze_table_comprehensively(
                table_path, columns, sample_data, {'table_ref': table_ref}
            )
            
            for col_name, classification in table_analysis['field_classifications'].items():
                if classification['confidence'] > 0.4:
                    mapping = FieldMapping(
                        field_type=classification['field_type'],
                        column=col_name,
                        confidence=classification['confidence'],
                        samples=sample_data.get(col_name, [])[:10]
                    )
                    schema.mappings[classification['field_type']] = mapping
            
            schema.quality = self._calculate_advanced_schema_quality(schema, table_analysis)
            
            self.table_insights[table_path] = table_analysis
            self.cache[cache_key] = schema
            
            logger.info(f"Deep analysis of {table_path}: {len(schema.mappings)} fields identified, quality {schema.quality:.3f}")
            
            return schema
            
        except Exception as e:
            logger.warning(f"Deep schema analysis failed for {table_path}: {e}")
            return None
    
    async def _intelligent_sampling(self, client, table_path: str, columns: List[str]) -> Dict[str, List[str]]:
        limited_columns = columns[:100]
        
        base_sample_query = f"""
        SELECT {', '.join([f'`{col}`' for col in limited_columns])}
        FROM `{table_path}`
        WHERE RAND() < 0.02
        LIMIT 1000
        """
        
        sample_data = {}
        
        try:
            job = client.query(base_sample_query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(limited_columns):
                values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        value = str(row[col_idx]).strip()
                        if value and value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE']:
                            values.append(value)
                
                if values:
                    sample_data[column_name] = list(set(values))[:50]
            
            hostname_candidates = self._identify_potential_hostname_columns(sample_data)
            
            if hostname_candidates:
                for candidate in hostname_candidates[:3]:
                    col_name = candidate['column']
                    enhanced_samples = await self._get_enhanced_samples(client, table_path, col_name)
                    if enhanced_samples:
                        sample_data[col_name] = enhanced_samples
                        
        except Exception as e:
            logger.warning(f"Intelligent sampling failed for {table_path}: {e}")
        
        return sample_data
    
    def _identify_potential_hostname_columns(self, sample_data: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        candidates = []
        
        for col_name, samples in sample_data.items():
            hostname_score = self._quick_hostname_assessment(col_name, samples)
            
            if hostname_score > 0.3:
                candidates.append({
                    'column': col_name,
                    'score': hostname_score,
                    'sample_count': len(samples)
                })
        
        return sorted(candidates, key=lambda x: x['score'], reverse=True)
    
    def _quick_hostname_assessment(self, col_name: str, samples: List[str]) -> float:
        name_score = 0.0
        name_lower = col_name.lower()
        
        hostname_indicators = ['hostname', 'host', 'computer', 'machine', 'device', 'endpoint', 'server']
        for indicator in hostname_indicators:
            if indicator in name_lower:
                name_score = len(indicator) / len(name_lower)
                break
        
        if not samples:
            return name_score * 0.5
        
        pattern_score = 0.0
        for sample in samples[:20]:
            if self._looks_like_hostname(sample):
                pattern_score += 1
        
        pattern_score = pattern_score / min(len(samples), 20)
        
        return (name_score * 0.4) + (pattern_score * 0.6)
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        import re
        patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)
    
    async def _get_enhanced_samples(self, client, table_path: str, column_name: str) -> List[str]:
        try:
            enhanced_query = f"""
            SELECT DISTINCT `{column_name}`
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            AND LENGTH(`{column_name}`) BETWEEN 2 AND 253
            LIMIT 200
            """
            
            job = client.query(enhanced_query)
            results = list(job.result())
            
            enhanced_samples = []
            for row in results:
                if row[0]:
                    value = str(row[0]).strip()
                    if value and value.upper() not in ['NULL', 'N/A', 'UNKNOWN', 'NONE']:
                        enhanced_samples.append(value)
            
            return enhanced_samples[:100]
            
        except Exception as e:
            logger.warning(f"Enhanced sampling failed for {column_name}: {e}")
            return []
    
    def _calculate_advanced_schema_quality(self, schema: TableSchema, analysis: Dict[str, Any]) -> float:
        if not schema.mappings:
            return 0.0
        
        critical_fields = ['hostname', 'ip_address', 'infrastructure_type', 'system_classification']
        critical_count = sum(1 for field in critical_fields if field in schema.mappings)
        critical_score = critical_count / len(critical_fields)
        
        avg_confidence = statistics.mean([m.confidence for m in schema.mappings.values()])
        
        table_confidence = analysis.get('confidence_score', 0.5)
        
        hostname_bonus = 0.2 if 'hostname' in schema.mappings and schema.mappings['hostname'].confidence > 0.8 else 0.0
        
        return min(1.0, (critical_score * 0.3 + avg_confidence * 0.4 + table_confidence * 0.3) + hostname_bonus)

class IntelligentAssetExtractor:
    def __init__(self, intelligence: EnhancedIntelligenceEngine):
        self.intelligence = intelligence
        self.extraction_strategies = {
            'direct_extraction': self._direct_extraction,
            'careful_extraction': self._careful_extraction,
            'exploratory_analysis': self._exploratory_analysis,
            'deep_content_scan': self._deep_content_scan
        }
    
    async def extract_assets_intelligently(self, client, schema: TableSchema, 
                                         source_name: str, table_insights: Dict[str, Any] = None) -> Dict[str, Asset]:
        
        if 'hostname' not in schema.mappings:
            logger.info(f"No hostname field identified in {schema.path}, attempting deep extraction")
            return await self._attempt_deep_hostname_extraction(client, schema, source_name)
        
        strategy_info = table_insights.get('processing_strategy', {}) if table_insights else {}
        strategy = strategy_info.get('strategy', 'careful_extraction')
        
        logger.info(f"Using {strategy} for {schema.path}")
        
        extractor = self.extraction_strategies.get(strategy, self._careful_extraction)
        return await extractor(client, schema, source_name, table_insights)
    
    async def _direct_extraction(self, client, schema: TableSchema, source_name: str, 
                               insights: Dict[str, Any] = None) -> Dict[str, Asset]:
        
        hostname_mapping = schema.mappings['hostname']
        assets = {}
        
        try:
            select_fields = [f"CAST(`{hostname_mapping.column}` AS STRING) as hostname"]
            field_mappings = {'hostname': hostname_mapping.column}
            
            for field_type, mapping in schema.mappings.items():
                if field_type != 'hostname':
                    select_fields.append(f"CAST(`{mapping.column}` AS STRING) as {field_type}")
                    field_mappings[field_type] = mapping.column
            
            extraction_query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{schema.path}`
            WHERE `{hostname_mapping.column}` IS NOT NULL
            AND LENGTH(`{hostname_mapping.column}`) BETWEEN 2 AND 253
            LIMIT 1000000
            """
            
            job = client.query(extraction_query)
            results = list(job.result())
            
            for row in results:
                if not row or not row[0]:
                    continue
                
                hostname = str(row[0]).strip().upper()
                if not self._is_valid_hostname_candidate(hostname):
                    continue
                
                asset_id = self._generate_smart_asset_id(hostname, source_name)
                asset = Asset(id=asset_id, hostname=hostname)
                
                for idx, field_type in enumerate(field_mappings.keys()):
                    if idx < len(row) and row[idx]:
                        value = str(row[idx]).strip()
                        if self._is_valid_field_value(value):
                            setattr(asset, self._field_to_attr(field_type), value)
                
                self._enrich_asset_with_intelligence(asset, source_name, insights)
                assets[asset_id] = asset
            
            logger.info(f"Direct extraction from {schema.path}: {len(assets)} assets")
            
        except Exception as e:
            logger.error(f"Direct extraction failed for {schema.path}: {e}")
        
        return assets
    
    async def _careful_extraction(self, client, schema: TableSchema, source_name: str, 
                                insights: Dict[str, Any] = None) -> Dict[str, Asset]:
        
        hostname_mapping = schema.mappings['hostname']
        assets = {}
        
        try:
            validation_query = f"""
            SELECT `{hostname_mapping.column}`, COUNT(*) as cnt
            FROM `{schema.path}`
            WHERE `{hostname_mapping.column}` IS NOT NULL
            AND LENGTH(`{hostname_mapping.column}`) BETWEEN 2 AND 253
            GROUP BY `{hostname_mapping.column}`
            HAVING cnt >= 1
            ORDER BY cnt DESC
            LIMIT 500000
            """
            
            job = client.query(validation_query)
            hostname_candidates = list(job.result())
            
            validated_hostnames = []
            for row in hostname_candidates:
                hostname = str(row[0]).strip().upper()
                if self._validate_hostname_semantically(hostname):
                    validated_hostnames.append(hostname)
            
            if validated_hostnames:
                hostname_list = "', '".join(validated_hostnames[:100000])
                
                select_fields = [f"CAST(`{hostname_mapping.column}` AS STRING) as hostname"]
                field_mappings = {'hostname': hostname_mapping.column}
                
                for field_type, mapping in schema.mappings.items():
                    if field_type != 'hostname':
                        select_fields.append(f"CAST(`{mapping.column}` AS STRING) as {field_type}")
                        field_mappings[field_type] = mapping.column
                
                final_query = f"""
                SELECT {', '.join(select_fields)}
                FROM `{schema.path}`
                WHERE `{hostname_mapping.column}` IN ('{hostname_list}')
                """
                
                job = client.query(final_query)
                results = list(job.result())
                
                for row in results:
                    if not row or not row[0]:
                        continue
                    
                    hostname = str(row[0]).strip().upper()
                    asset_id = self._generate_smart_asset_id(hostname, source_name)
                    asset = Asset(id=asset_id, hostname=hostname)
                    
                    for idx, field_type in enumerate(field_mappings.keys()):
                        if idx < len(row) and row[idx]:
                            value = str(row[idx]).strip()
                            if self._is_valid_field_value(value):
                                setattr(asset, self._field_to_attr(field_type), value)
                    
                    self._enrich_asset_with_intelligence(asset, source_name, insights)
                    assets[asset_id] = asset
            
            logger.info(f"Careful extraction from {schema.path}: {len(assets)} assets")
            
        except Exception as e:
            logger.error(f"Careful extraction failed for {schema.path}: {e}")
        
        return assets
    
    async def _exploratory_analysis(self, client, schema: TableSchema, source_name: str, 
                                  insights: Dict[str, Any] = None) -> Dict[str, Asset]:
        
        if 'hostname' not in schema.mappings:
            return {}
        
        hostname_mapping = schema.mappings['hostname']
        assets = {}
        
        try:
            exploratory_query = f"""
            SELECT `{hostname_mapping.column}`, 
                   COUNT(*) as frequency,
                   MIN(LENGTH(`{hostname_mapping.column}`)) as min_len,
                   MAX(LENGTH(`{hostname_mapping.column}`)) as max_len
            FROM `{schema.path}`
            WHERE `{hostname_mapping.column}` IS NOT NULL
            GROUP BY `{hostname_mapping.column}`
            HAVING frequency >= 1 
            AND min_len >= 2 
            AND max_len <= 253
            ORDER BY frequency DESC
            LIMIT 50000
            """
            
            job = client.query(exploratory_query)
            exploration_results = list(job.result())
            
            high_confidence_hostnames = []
            medium_confidence_hostnames = []
            
            for row in exploration_results:
                hostname = str(row[0]).strip().upper()
                frequency = row[1]
                
                semantic_score = self._calculate_hostname_semantic_score(hostname)
                
                if semantic_score > 0.8 or frequency > 5:
                    high_confidence_hostnames.append(hostname)
                elif semantic_score > 0.5:
                    medium_confidence_hostnames.append(hostname)
            
            selected_hostnames = high_confidence_hostnames[:20000] + medium_confidence_hostnames[:10000]
            
            if selected_hostnames:
                assets = await self._extract_selected_hostnames(
                    client, schema, selected_hostnames, source_name, insights
                )
            
            logger.info(f"Exploratory analysis of {schema.path}: {len(assets)} assets")
            
        except Exception as e:
            logger.error(f"Exploratory analysis failed for {schema.path}: {e}")
        
        return assets
    
    async def _deep_content_scan(self, client, schema: TableSchema, source_name: str, 
                               insights: Dict[str, Any] = None) -> Dict[str, Asset]:
        
        logger.info(f"Performing deep content scan of {schema.path}")
        return await self._attempt_deep_hostname_extraction(client, schema, source_name)
    
    async def _attempt_deep_hostname_extraction(self, client, schema: TableSchema, source_name: str) -> Dict[str, Asset]:
        try:
            table_ref = client.get_table(schema.path)
            columns = [field.name for field in table_ref.schema]
            
            potential_hostname_columns = []
            
            for col_name in columns:
                if self._column_might_contain_hostnames(col_name):
                    potential_hostname_columns.append(col_name)
            
            assets = {}
            
            for col_name in potential_hostname_columns[:10]:
                try:
                    sample_query = f"""
                    SELECT DISTINCT `{col_name}`
                    FROM `{schema.path}`
                    WHERE `{col_name}` IS NOT NULL
                    AND LENGTH(`{col_name}`) BETWEEN 2 AND 253
                    LIMIT 500
                    """
                    
                    job = client.query(sample_query)
                    samples = [str(row[0]).strip() for row in job.result() if row[0]]
                    
                    hostname_probability = await self._assess_hostname_probability_deep(col_name, samples)
                    
                    if hostname_probability > 0.6:
                        logger.info(f"Found potential hostname column {col_name} with probability {hostname_probability:.3f}")
                        
                        column_assets = await self._extract_from_hostname_column(
                            client, schema.path, col_name, source_name
                        )
                        
                        assets.update(column_assets)
                        
                        if len(column_assets) > 1000:
                            break
                            
                except Exception as e:
                    logger.debug(f"Deep scan of column {col_name} failed: {e}")
            
            logger.info(f"Deep content scan of {schema.path}: {len(assets)} assets found")
            return assets
            
        except Exception as e:
            logger.error(f"Deep content scan failed for {schema.path}: {e}")
            return {}
    
    def _column_might_contain_hostnames(self, col_name: str) -> bool:
        name_lower = col_name.lower()
        
        positive_indicators = [
            'host', 'computer', 'machine', 'device', 'endpoint', 'server', 'node',
            'name', 'id', 'asset', 'equipment', 'system', 'workstation', 'desktop'
        ]
        
        negative_indicators = [
            'created', 'updated', 'modified', 'date', 'time', 'timestamp',
            'count', 'total', 'sum', 'avg', 'status', 'type', 'flag', 'bool'
        ]
        
        has_positive = any(indicator in name_lower for indicator in positive_indicators)
        has_negative = any(indicator in name_lower for indicator in negative_indicators)
        
        return has_positive and not has_negative
    
    async def _assess_hostname_probability_deep(self, col_name: str, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        name_score = self._score_column_name_for_hostnames(col_name)
        
        pattern_matches = sum(1 for sample in samples if self._looks_like_hostname(sample))
        pattern_score = pattern_matches / len(samples)
        
        semantic_scores = [self._calculate_hostname_semantic_score(sample) for sample in samples]
        semantic_score = statistics.mean(semantic_scores) if semantic_scores else 0.0
        
        return (name_score * 0.3 + pattern_score * 0.4 + semantic_score * 0.3)
    
    def _score_column_name_for_hostnames(self, col_name: str) -> float:
        name_lower = col_name.lower()
        
        exact_matches = ['hostname', 'host', 'computername', 'computer_name', 'machine_name']
        for match in exact_matches:
            if match == name_lower or match.replace('_', '') == name_lower.replace('_', ''):
                return 1.0
        
        partial_indicators = ['host', 'computer', 'machine', 'device', 'endpoint', 'server']
        for indicator in partial_indicators:
            if indicator in name_lower:
                return 0.7
        
        return 0.1
    
    async def _extract_from_hostname_column(self, client, table_path: str, column_name: str, source_name: str) -> Dict[str, Asset]:
        assets = {}
        
        try:
            extraction_query = f"""
            SELECT DISTINCT `{column_name}`
            FROM `{table_path}`
            WHERE `{column_name}` IS NOT NULL
            AND LENGTH(`{column_name}`) BETWEEN 2 AND 253
            LIMIT 100000
            """
            
            job = client.query(extraction_query)
            results = list(job.result())
            
            for row in results:
                if not row[0]:
                    continue
                
                hostname = str(row[0]).strip().upper()
                
                if self._validate_hostname_semantically(hostname):
                    asset_id = self._generate_smart_asset_id(hostname, source_name)
                    asset = Asset(id=asset_id, hostname=hostname)
                    
                    self._set_source_flags(asset, source_name)
                    asset.sources = 1
                    asset.intelligence = 0.7
                    asset.quality = self._calculate_hostname_quality(hostname)
                    asset.confidence = 0.8
                    
                    assets[asset_id] = asset
            
        except Exception as e:
            logger.error(f"Hostname extraction failed for {table_path}.{column_name}: {e}")
        
        return assets
    
    async def _extract_selected_hostnames(self, client, schema: TableSchema, hostnames: List[str], 
                                        source_name: str, insights: Dict[str, Any] = None) -> Dict[str, Asset]:
        assets = {}
        hostname_mapping = schema.mappings['hostname']
        
        try:
            batch_size = 1000
            for i in range(0, len(hostnames), batch_size):
                batch = hostnames[i:i + batch_size]
                hostname_list = "', '".join(batch)
                
                select_fields = [f"CAST(`{hostname_mapping.column}` AS STRING) as hostname"]
                field_mappings = {'hostname': hostname_mapping.column}
                
                for field_type, mapping in schema.mappings.items():
                    if field_type != 'hostname':
                        select_fields.append(f"CAST(`{mapping.column}` AS STRING) as {field_type}")
                        field_mappings[field_type] = mapping.column
                
                batch_query = f"""
                SELECT {', '.join(select_fields)}
                FROM `{schema.path}`
                WHERE `{hostname_mapping.column}` IN ('{hostname_list}')
                """
                
                job = client.query(batch_query)
                results = list(job.result())
                
                for row in results:
                    if not row or not row[0]:
                        continue
                    
                    hostname = str(row[0]).strip().upper()
                    asset_id = self._generate_smart_asset_id(hostname, source_name)
                    asset = Asset(id=asset_id, hostname=hostname)
                    
                    for idx, field_type in enumerate(field_mappings.keys()):
                        if idx < len(row) and row[idx]:
                            value = str(row[idx]).strip()
                            if self._is_valid_field_value(value):
                                setattr(asset, self._field_to_attr(field_type), value)
                    
                    self._enrich_asset_with_intelligence(asset, source_name, insights)
                    assets[asset_id] = asset
        
        except Exception as e:
            logger.error(f"Selected hostname extraction failed: {e}")
        
        return assets
    
    def _is_valid_hostname_candidate(self, hostname: str) -> bool:
        if not hostname or len(hostname) < 2 or len(hostname) > 253:
            return False
        
        if hostname.upper() in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '', 'NA', '-']:
            return False
        
        import re
        basic_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$|^[a-zA-Z0-9]+$'
        if not re.match(basic_pattern, hostname, re.IGNORECASE):
            return False
        
        return True
    
    def _validate_hostname_semantically(self, hostname: str) -> bool:
        if not self._is_valid_hostname_candidate(hostname):
            return False
        
        semantic_score = self._calculate_hostname_semantic_score(hostname)
        return semantic_score > 0.3
    
    def _calculate_hostname_semantic_score(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        hostname_lower = hostname.lower()
        score = 0.0
        
        semantic_indicators = [
            'srv', 'server', 'host', 'node', 'vm', 'pc', 'ws', 'desktop', 'laptop',
            'web', 'app', 'db', 'sql', 'ad', 'dc', 'dns', 'dhcp', 'proxy', 'fw',
            'prod', 'dev', 'test', 'stage', 'qa', 'demo', 'lab', 'backup', 'dr'
        ]
        
        indicator_matches = sum(1 for indicator in semantic_indicators if indicator in hostname_lower)
        score += min(0.4, indicator_matches * 0.1)
        
        if re.search(r'[0-9]', hostname):
            score += 0.2
        
        if re.search(r'[-_.]', hostname):
            score += 0.1
        
        length_score = 0.3 if 3 <= len(hostname) <= 50 else 0.1
        score += length_score
        
        return min(1.0, score)
    
    def _calculate_hostname_quality(self, hostname: str) -> float:
        if not hostname:
            return 0.0
        
        quality_score = 0.5
        
        if self._is_valid_hostname_candidate(hostname):
            quality_score += 0.3
        
        semantic_score = self._calculate_hostname_semantic_score(hostname)
        quality_score += semantic_score * 0.2
        
        return min(1.0, quality_score)
    
    def _is_valid_field_value(self, value: str) -> bool:
        if not value:
            return False
        
        clean_value = value.strip().upper()
        return clean_value not in ['NULL', 'N/A', 'UNKNOWN', 'NONE', '', 'NA', '-']
    
    def _generate_smart_asset_id(self, hostname: str, source: str) -> str:
        normalized = f"{hostname.upper().strip()}_{source}"
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
            'crowdstrike': {'crowdstrike': True, 'edr': True},
            'tanium': {'tanium': True}
        }
        
        flags = source_flags.get(source, {})
        for attr, value in flags.items():
            setattr(asset, attr, value)
    
    def _enrich_asset_with_intelligence(self, asset: Asset, source: str, insights: Dict[str, Any] = None):
        asset.sources = 1
        
        base_intelligence = 0.6
        if source == 'cmdb':
            base_intelligence = 0.8
        elif source == 'crowdstrike':
            base_intelligence = 0.75
        
        if insights:
            confidence_boost = insights.get('confidence_score', 0.5) * 0.2
            base_intelligence += confidence_boost
        
        asset.intelligence = min(1.0, base_intelligence)
        asset.quality = self._calculate_hostname_quality(asset.hostname)
        asset.confidence = (asset.intelligence + asset.quality) / 2

class EnhancedDiscoveryEngine:
    def __init__(self, project_id: str, config: Dict[str, Any], 
                 cache_manager, intelligence: EnhancedIntelligenceEngine):
        self.project_id = project_id
        self.config = config
        self.cache = cache_manager
        self.intelligence = intelligence
        
        self.schema_analyzer = AdvancedSchemaAnalyzer(intelligence)
        self.asset_extractor = IntelligentAssetExtractor(intelligence)
        
        self.source_tables = {
            'cmdb': 'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'splunk': 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'crowdstrike': 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT'
        }
        
        self.stats = {
            'tables_analyzed': 0,
            'schemas_discovered': 0,
            'assets_extracted': 0,
            'processing_errors': 0,
            'deep_scans_performed': 0
        }
    
    async def discover_assets_intelligently(self, client_managers: Dict[str, Any]) -> Discovery:
        logger.info("Starting enhanced intelligent asset discovery")
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
                
                logger.info(f"Performing intelligent analysis of {source_name}: {table_path}")
                
                with client_manager.get_client() as client:
                    schema = await self.schema_analyzer.analyze_table_deeply(client, table_path)
                    
                    if schema:
                        discovery.schemas[table_path] = schema
                        self.stats['schemas_discovered'] += 1
                        
                        table_insights = self.schema_analyzer.table_insights.get(table_path, {})
                        
                        assets = await self.asset_extractor.extract_assets_intelligently(
                            client, schema, source_name, table_insights
                        )
                        
                        if not assets and schema.rows > 0:
                            logger.info(f"No assets extracted normally, attempting deep scan of {table_path}")
                            assets = await self.asset_extractor._attempt_deep_hostname_extraction(
                                client, schema, source_name
                            )
                            self.stats['deep_scans_performed'] += 1
                        
                        for asset_id, asset in assets.items():
                            if asset_id in all_assets:
                                all_assets[asset_id] = self._merge_assets_intelligently(
                                    all_assets[asset_id], asset
                                )
                            else:
                                all_assets[asset_id] = asset
                                self.stats['assets_extracted'] += 1
                        
                        logger.info(f"Extracted {len(assets)} assets from {source_name}")
                
                self.stats['tables_analyzed'] += 1
                
            except Exception as e:
                logger.error(f"Enhanced processing failed for {source_name}: {e}")
                self.stats['processing_errors'] += 1
        
        logger.info("Performing intelligent asset consolidation")
        discovery.assets = all_assets
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        discovery.stats = {
            'total_assets': len(discovery.assets),
            'high_quality_assets': sum(1 for a in discovery.assets.values() if a.quality > 0.8),
            'multi_source_assets': sum(1 for a in discovery.assets.values() if a.sources > 1),
            'processing_time_seconds': processing_time,
            'performance_stats': self.stats,
            'intelligence_enhanced': True
        }
        
        discovery.insights = await self.intelligence.generate_insights(discovery)
        
        logger.info(f"Enhanced discovery complete: {len(discovery.assets)} unique assets discovered")
        return discovery
    
    def _merge_assets_intelligently(self, primary: Asset, secondary: Asset) -> Asset:
        merged = Asset(id=primary.id)
        
        text_fields = ['hostname', 'ip', 'fqdn', 'mac', 'infra_type', 'system_class',
                      'region', 'country', 'datacenter', 'cloud_region', 'business_unit',
                      'cio', 'app_class']
        
        for field in text_fields:
            primary_val = getattr(primary, field, "")
            secondary_val = getattr(secondary, field, "")
            
            if secondary_val and not primary_val:
                setattr(merged, field, secondary_val)
            elif primary_val:
                setattr(merged, field, primary_val)
            elif secondary_val and primary_val and len(secondary_val) > len(primary_val):
                setattr(merged, field, secondary_val)
            else:
                setattr(merged, field, primary_val)
        
        bool_fields = ['edr', 'dlp', 'tanium', 'splunk', 'chronicle', 'gso', 'cmdb', 'crowdstrike']
        for field in bool_fields:
            primary_val = getattr(primary, field, False)
            secondary_val = getattr(secondary, field, False)
            setattr(merged, field, primary_val or secondary_val)
        
        merged.sources = primary.sources + secondary.sources
        merged.intelligence = max(primary.intelligence, secondary.intelligence)
        merged.quality = max(primary.quality, secondary.quality)
        merged.confidence = (primary.confidence + secondary.confidence) / 2
        
        return merged