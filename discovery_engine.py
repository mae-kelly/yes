#!/usr/bin/env python3

import logging
import duckdb
import asyncio
import json
import hashlib
import re
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

@dataclass
class UniversalAsset:
    asset_id: str
    hostname: str = ""
    ip_address: str = ""
    fqdn: str = ""
    mac_address: str = ""
    infrastructure_type: str = ""
    system_classification: str = ""
    global_region: str = ""
    country: str = ""
    business_unit: str = ""
    found_in_cmdb: bool = False
    found_in_splunk: bool = False
    found_in_chronicle: bool = False
    found_in_crowdstrike: bool = False
    has_crowdstrike: bool = False
    in_splunk: bool = False
    in_chronicle: bool = False
    source_count: int = 0
    confidence_score: float = 0.0
    data_quality_score: float = 0.0
    source_systems: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

class UltimateCMDBBuilder:
    def __init__(self, config: Dict[str, Any], content_matcher, cache_manager):
        self.config = config
        self.content_matcher = content_matcher
        self.cache_manager = cache_manager
        
        self.db_path = config.get('database_path', 'ultimate_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        
        self.discovered_assets = {}
        self.processing_lock = threading.RLock()
        
        self.processing_stats = {
            'projects_processed': 0,
            'datasets_scanned': 0,
            'tables_analyzed': 0,
            'assets_discovered': 0,
            'assets_merged': 0,
            'processing_errors': 0
        }
        
        self._setup_ultimate_schema()
        logger.info("Ultimate CMDB Builder initialized")
    
    def _setup_ultimate_schema(self):
        """Create the ultimate universal CMDB schema"""
        self.conn.execute("DROP TABLE IF EXISTS ultimate_universal_endpoint")
        
        self.conn.execute("""
            CREATE TABLE ultimate_universal_endpoint (
                asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                ip_address VARCHAR,
                fqdn VARCHAR,
                mac_address VARCHAR,
                infrastructure_type VARCHAR,
                system_classification VARCHAR,
                global_region VARCHAR,
                country VARCHAR,
                business_unit VARCHAR,
                found_in_cmdb BOOLEAN DEFAULT FALSE,
                found_in_splunk BOOLEAN DEFAULT FALSE,
                found_in_chronicle BOOLEAN DEFAULT FALSE,
                found_in_crowdstrike BOOLEAN DEFAULT FALSE,
                has_crowdstrike BOOLEAN DEFAULT FALSE,
                in_splunk BOOLEAN DEFAULT FALSE,
                in_chronicle BOOLEAN DEFAULT FALSE,
                source_count INTEGER DEFAULT 0,
                confidence_score DOUBLE DEFAULT 0.0,
                data_quality_score DOUBLE DEFAULT 0.0,
                source_systems VARCHAR,
                raw_data JSON,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info("Ultimate CMDB schema created")
    
    async def build_ultimate_cmdb(self, projects: List[str], client_managers: Dict[str, Any]) -> Dict[str, Any]:
        """Build the ultimate CMDB by scanning all projects and tables"""
        logger.info(f"Building Ultimate CMDB across {len(projects)} projects")
        
        start_time = datetime.now()
        
        # Define known source tables across projects
        source_table_patterns = {
            'cmdb': [
                'SAS_BI.V_DIM_ENDPOINT',
                'SAS_BI.DIM_ENDPOINT',
                'cmdb.endpoints',
                'cmdb.assets'
            ],
            'splunk': [
                'SAS_BI.V_SPL_ENDPOINT_LOG',
                'SAS_BI.SPL_ENDPOINT_LOG',
                'splunk.endpoint_logs',
                'splunk.events'
            ],
            'crowdstrike': [
                'SAS_BI.V_DIM_ENDPOINTAGENT',
                'SAS_BI.DIM_ENDPOINTAGENT',
                'crowdstrike.agents',
                'security.endpoint_agents'
            ],
            'chronicle': [
                'datalake.events',
                'chronicle.events',
                'security.events'
            ]
        }
        
        all_discovered_assets = {}
        
        for project_id in projects:
            if project_id not in client_managers:
                logger.warning(f"No client manager for project {project_id}")
                continue
            
            logger.info(f"Processing project: {project_id}")
            
            try:
                project_assets = await self._scan_project_exhaustively(
                    project_id, client_managers[project_id], source_table_patterns
                )
                
                # Merge project assets into global collection
                for asset_id, asset in project_assets.items():
                    if asset_id in all_discovered_assets:
                        all_discovered_assets[asset_id] = self._merge_assets(
                            all_discovered_assets[asset_id], asset
                        )
                        self.processing_stats['assets_merged'] += 1
                    else:
                        all_discovered_assets[asset_id] = asset
                        self.processing_stats['assets_discovered'] += 1
                
                self.processing_stats['projects_processed'] += 1
                logger.info(f"Project {project_id} processed: {len(project_assets)} assets")
                
            except Exception as e:
                logger.error(f"Failed to process project {project_id}: {e}")
                self.processing_stats['processing_errors'] += 1
        
        # Store all assets in ultimate database
        stored_count = await self._store_ultimate_assets(all_discovered_assets)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'total_assets': len(all_discovered_assets),
            'stored_assets': stored_count,
            'projects_processed': self.processing_stats['projects_processed'],
            'datasets_scanned': self.processing_stats['datasets_scanned'],
            'tables_analyzed': self.processing_stats['tables_analyzed'],
            'assets_merged': self.processing_stats['assets_merged'],
            'processing_errors': self.processing_stats['processing_errors'],
            'processing_time_seconds': processing_time,
            'database_path': self.db_path,
            'coverage_summary': self._calculate_coverage_summary(all_discovered_assets)
        }
    
    async def _scan_project_exhaustively(self, project_id: str, client_manager, 
                                       source_patterns: Dict[str, List[str]]) -> Dict[str, UniversalAsset]:
        """Scan a project exhaustively for all endpoint data"""
        project_assets = {}
        
        with client_manager.get_client() as client:
            # Get all datasets in the project
            datasets = list(client.list_datasets(project=project_id))
            self.processing_stats['datasets_scanned'] += len(datasets)
            
            for dataset in datasets:
                dataset_id = dataset.dataset_id
                logger.info(f"Scanning dataset: {project_id}.{dataset_id}")
                
                try:
                    # Get all tables in the dataset
                    dataset_ref = client.dataset(dataset_id, project=project_id)
                    tables = list(client.list_tables(dataset_ref))
                    
                    for table_ref in tables:
                        table_id = table_ref.table_id
                        table_path = f"{project_id}.{dataset_id}.{table_id}"
                        
                        # Determine source type from table name/path
                        source_type = self._identify_source_type(table_path, source_patterns)
                        
                        if source_type:
                            logger.info(f"Processing {source_type} table: {table_path}")
                            
                            table_assets = await self._extract_assets_from_table(
                                client, table_path, source_type
                            )
                            
                            # Merge table assets into project collection
                            for asset_id, asset in table_assets.items():
                                if asset_id in project_assets:
                                    project_assets[asset_id] = self._merge_assets(
                                        project_assets[asset_id], asset
                                    )
                                else:
                                    project_assets[asset_id] = asset
                            
                            self.processing_stats['tables_analyzed'] += 1
                        
                        else:
                            # Try to analyze unknown table for hostname data
                            unknown_assets = await self._analyze_unknown_table(
                                client, table_path
                            )
                            
                            for asset_id, asset in unknown_assets.items():
                                if asset_id in project_assets:
                                    project_assets[asset_id] = self._merge_assets(
                                        project_assets[asset_id], asset
                                    )
                                else:
                                    project_assets[asset_id] = asset
                            
                            if unknown_assets:
                                self.processing_stats['tables_analyzed'] += 1
                
                except Exception as e:
                    logger.warning(f"Failed to scan dataset {dataset_id}: {e}")
                    self.processing_stats['processing_errors'] += 1
        
        return project_assets
    
    def _identify_source_type(self, table_path: str, source_patterns: Dict[str, List[str]]) -> Optional[str]:
        """Identify the source type of a table based on its path"""
        table_path_lower = table_path.lower()
        
        for source_type, patterns in source_patterns.items():
            for pattern in patterns:
                if pattern.lower() in table_path_lower:
                    return source_type
        
        return None
    
    async def _extract_assets_from_table(self, client, table_path: str, source_type: str) -> Dict[str, UniversalAsset]:
        """Extract assets from a known source table"""
        assets = {}
        
        try:
            # Get table schema
            table_ref = client.get_table(table_path)
            if not table_ref.schema:
                return assets
            
            columns = [field.name for field in table_ref.schema]
            
            # Sample the table to understand column contents
            sample_query = f"""
            SELECT {', '.join([f'`{col}`' for col in columns[:20]])}
            FROM `{table_path}`
            WHERE RAND() < 0.01
            LIMIT 100
            """
            
            job = client.query(sample_query)
            sample_results = list(job.result())
            
            if not sample_results:
                return assets
            
            # Analyze columns to find field mappings
            field_mappings = {}
            for col_idx, column_name in enumerate(columns[:20]):
                sample_values = []
                for row in sample_results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        sample_values.append(str(row[col_idx]))
                
                if sample_values:
                    analysis = self.content_matcher.analyze_column_intelligently(
                        column_name, sample_values
                    )
                    
                    if analysis:
                        field_type, confidence, metadata = analysis
                        if confidence > 0.6:
                            field_mappings[field_type] = column_name
            
            # Extract assets if we found a hostname field
            if 'hostname' in field_mappings:
                hostname_col = field_mappings['hostname']
                
                # Build extraction query
                select_fields = [f"UPPER(TRIM(`{hostname_col}`)) as hostname"]
                field_to_column = {'hostname': hostname_col}
                
                for field_type, column_name in field_mappings.items():
                    if field_type != 'hostname':
                        select_fields.append(f"`{column_name}` as {field_type}")
                        field_to_column[field_type] = column_name
                
                extraction_query = f"""
                SELECT {', '.join(select_fields)}
                FROM `{table_path}`
                WHERE `{hostname_col}` IS NOT NULL
                AND TRIM(`{hostname_col}`) != ''
                LIMIT 100000
                """
                
                job = client.query(extraction_query)
                results = list(job.result())
                
                for row in results:
                    if not row or not row[0]:
                        continue
                    
                    hostname = str(row[0]).strip().upper()
                    if not hostname or len(hostname) < 1:
                        continue
                    
                    asset_id = self._generate_asset_id(hostname)
                    
                    asset = UniversalAsset(
                        asset_id=asset_id,
                        hostname=hostname,
                        source_count=1,
                        source_systems=source_type
                    )
                    
                    # Populate fields from row data
                    for idx, field_type in enumerate(field_to_column.keys()):
                        if idx < len(row) and row[idx]:
                            value = str(row[idx]).strip()
                            if hasattr(asset, field_type) and value:
                                setattr(asset, field_type, value)
                    
                    # Set source flags
                    self._set_source_flags(asset, source_type)
                    
                    # Calculate quality scores
                    asset.confidence_score = self._calculate_confidence_score(asset)
                    asset.data_quality_score = self._calculate_data_quality_score(asset)
                    
                    assets[asset_id] = asset
        
        except Exception as e:
            logger.warning(f"Failed to extract from {table_path}: {e}")
        
        return assets
    
    async def _analyze_unknown_table(self, client, table_path: str) -> Dict[str, UniversalAsset]:
        """Analyze an unknown table for potential hostname data"""
        assets = {}
        
        try:
            table_ref = client.get_table(table_path)
            if not table_ref.schema or table_ref.num_rows == 0:
                return assets
            
            columns = [field.name for field in table_ref.schema]
            
            # Quick sample to check for hostname-like data
            sample_query = f"""
            SELECT {', '.join([f'`{col}`' for col in columns[:10]])}
            FROM `{table_path}`
            WHERE RAND() < 0.01
            LIMIT 50
            """
            
            job = client.query(sample_query)
            sample_results = list(job.result())
            
            if not sample_results:
                return assets
            
            # Look for hostname columns
            hostname_columns = []
            for col_idx, column_name in enumerate(columns[:10]):
                sample_values = []
                for row in sample_results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        sample_values.append(str(row[col_idx]))
                
                if sample_values:
                    # Check if this looks like a hostname column
                    hostname_like_count = sum(1 for value in sample_values 
                                            if self._looks_like_hostname(value))
                    
                    if hostname_like_count > len(sample_values) * 0.5:
                        hostname_columns.append(column_name)
            
            # Extract from the best hostname column
            if hostname_columns:
                best_hostname_col = hostname_columns[0]
                
                extraction_query = f"""
                SELECT UPPER(TRIM(`{best_hostname_col}`)) as hostname
                FROM `{table_path}`
                WHERE `{best_hostname_col}` IS NOT NULL
                AND TRIM(`{best_hostname_col}`) != ''
                LIMIT 10000
                """
                
                job = client.query(extraction_query)
                results = list(job.result())
                
                for row in results:
                    if not row or not row[0]:
                        continue
                    
                    hostname = str(row[0]).strip().upper()
                    if not hostname or len(hostname) < 1:
                        continue
                    
                    asset_id = self._generate_asset_id(hostname)
                    
                    asset = UniversalAsset(
                        asset_id=asset_id,
                        hostname=hostname,
                        source_count=1,
                        source_systems='unknown'
                    )
                    
                    asset.confidence_score = 0.5  # Lower confidence for unknown tables
                    asset.data_quality_score = 0.5
                    
                    assets[asset_id] = asset
        
        except Exception as e:
            logger.debug(f"Could not analyze unknown table {table_path}: {e}")
        
        return assets
    
    def _looks_like_hostname(self, value: str) -> bool:
        """Quick check if a value looks like a hostname"""
        if not isinstance(value, str) or len(value) < 2 or len(value) > 253:
            return False
        
        # Basic hostname pattern check
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', value):
            return True
        
        # Check for server-like names
        if any(indicator in value.lower() for indicator in ['srv', 'host', 'server', 'pc', 'ws']):
            return True
        
        return False
    
    def _generate_asset_id(self, hostname: str) -> str:
        """Generate a consistent asset ID from hostname"""
        normalized = hostname.upper().strip()
        return f"asset_{hashlib.md5(normalized.encode()).hexdigest()[:12]}"
    
    def _set_source_flags(self, asset: UniversalAsset, source_type: str):
        """Set appropriate source flags on the asset"""
        if source_type == 'cmdb':
            asset.found_in_cmdb = True
        elif source_type == 'splunk':
            asset.found_in_splunk = True
            asset.in_splunk = True
        elif source_type == 'chronicle':
            asset.found_in_chronicle = True
            asset.in_chronicle = True
        elif source_type == 'crowdstrike':
            asset.found_in_crowdstrike = True
            asset.has_crowdstrike = True
    
    def _merge_assets(self, primary: UniversalAsset, secondary: UniversalAsset) -> UniversalAsset:
        """Merge two assets intelligently"""
        merged = UniversalAsset(
            asset_id=primary.asset_id,
            hostname=primary.hostname or secondary.hostname
        )
        
        # Merge all string fields, preferring non-empty values
        string_fields = ['ip_address', 'fqdn', 'mac_address', 'infrastructure_type',
                        'system_classification', 'global_region', 'country', 'business_unit']
        
        for field in string_fields:
            primary_val = getattr(primary, field, "")
            secondary_val = getattr(secondary, field, "")
            setattr(merged, field, primary_val or secondary_val)
        
        # Merge boolean flags (OR operation)
        bool_fields = ['found_in_cmdb', 'found_in_splunk', 'found_in_chronicle',
                      'found_in_crowdstrike', 'has_crowdstrike', 'in_splunk', 'in_chronicle']
        
        for field in bool_fields:
            primary_val = getattr(primary, field, False)
            secondary_val = getattr(secondary, field, False)
            setattr(merged, field, primary_val or secondary_val)
        
        # Merge source information
        merged.source_count = primary.source_count + secondary.source_count
        
        primary_sources = set(primary.source_systems.split(','))
        secondary_sources = set(secondary.source_systems.split(','))
        all_sources = primary_sources | secondary_sources
        merged.source_systems = ','.join(sorted(all_sources))
        
        # Recalculate scores
        merged.confidence_score = max(primary.confidence_score, secondary.confidence_score)
        merged.data_quality_score = (primary.data_quality_score + secondary.data_quality_score) / 2
        
        return merged
    
    def _calculate_confidence_score(self, asset: UniversalAsset) -> float:
        """Calculate confidence score for an asset"""
        score = 0.5  # Base score
        
        # Boost for multiple sources
        if asset.source_count > 1:
            score += 0.2
        
        # Boost for CMDB presence
        if asset.found_in_cmdb:
            score += 0.2
        
        # Boost for security tool presence
        if asset.has_crowdstrike:
            score += 0.1
        
        # Boost for log presence
        if asset.in_splunk or asset.in_chronicle:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_data_quality_score(self, asset: UniversalAsset) -> float:
        """Calculate data quality score for an asset"""
        quality_factors = []
        
        # Check hostname quality
        if asset.hostname and len(asset.hostname) > 1:
            quality_factors.append(0.8)
        
        # Check for additional identifying information
        if asset.ip_address:
            quality_factors.append(0.7)
        
        if asset.fqdn:
            quality_factors.append(0.6)
        
        # Check for classification information
        if asset.infrastructure_type:
            quality_factors.append(0.5)
        
        if asset.system_classification:
            quality_factors.append(0.5)
        
        return statistics.mean(quality_factors) if quality_factors else 0.3
    
    async def _store_ultimate_assets(self, assets: Dict[str, UniversalAsset]) -> int:
        """Store all assets in the ultimate database"""
        stored_count = 0
        
        insert_query = """
        INSERT INTO ultimate_universal_endpoint (
            asset_id, hostname, ip_address, fqdn, mac_address, infrastructure_type,
            system_classification, global_region, country, business_unit,
            found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike,
            has_crowdstrike, in_splunk, in_chronicle, source_count, confidence_score,
            data_quality_score, source_systems, raw_data, discovery_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
        """
        
        for asset in assets.values():
            try:
                values = [
                    asset.asset_id, asset.hostname, asset.ip_address, asset.fqdn,
                    asset.mac_address, asset.infrastructure_type, asset.system_classification,
                    asset.global_region, asset.country, asset.business_unit,
                    asset.found_in_cmdb, asset.found_in_splunk, asset.found_in_chronicle,
                    asset.found_in_crowdstrike, asset.has_crowdstrike, asset.in_splunk,
                    asset.in_chronicle, asset.source_count, asset.confidence_score,
                    asset.data_quality_score, asset.source_systems,
                    json.dumps(asset.raw_data)
                ]
                
                self.conn.execute(insert_query, values)
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store asset {asset.asset_id}: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} ultimate assets")
        return stored_count
    
    def _calculate_coverage_summary(self, assets: Dict[str, UniversalAsset]) -> Dict[str, Any]:
        """Calculate coverage summary statistics"""
        if not assets:
            return {}
        
        total_assets = len(assets)
        
        return {
            'total_assets': total_assets,
            'cmdb_coverage': sum(1 for a in assets.values() if a.found_in_cmdb),
            'splunk_coverage': sum(1 for a in assets.values() if a.found_in_splunk),
            'chronicle_coverage': sum(1 for a in assets.values() if a.found_in_chronicle),
            'crowdstrike_coverage': sum(1 for a in assets.values() if a.found_in_crowdstrike),
            'multi_source_assets': sum(1 for a in assets.values() if a.source_count > 1),
            'high_confidence_assets': sum(1 for a in assets.values() if a.confidence_score > 0.8),
            'avg_confidence_score': statistics.mean([a.confidence_score for a in assets.values()]),
            'avg_data_quality_score': statistics.mean([a.data_quality_score for a in assets.values()])
        }
    
    def get_visibility_queries(self) -> Dict[str, str]:
        """Get useful visibility analysis queries"""
        return {
            'visibility_summary': """
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as in_cmdb,
                    SUM(CASE WHEN found_in_splunk THEN 1 ELSE 0 END) as in_splunk,
                    SUM(CASE WHEN found_in_chronicle THEN 1 ELSE 0 END) as in_chronicle,
                    SUM(CASE WHEN found_in_crowdstrike THEN 1 ELSE 0 END) as in_crowdstrike,
                    SUM(CASE WHEN source_count > 1 THEN 1 ELSE 0 END) as multi_source
                FROM ultimate_universal_endpoint
            """,
            
            'coverage_percentages': """
                SELECT 
                    ROUND(100.0 * SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) / COUNT(*), 2) as cmdb_percentage,
                    ROUND(100.0 * SUM(CASE WHEN found_in_splunk THEN 1 ELSE 0 END) / COUNT(*), 2) as splunk_percentage,
                    ROUND(100.0 * SUM(CASE WHEN found_in_chronicle THEN 1 ELSE 0 END) / COUNT(*), 2) as chronicle_percentage,
                    ROUND(100.0 * SUM(CASE WHEN found_in_crowdstrike THEN 1 ELSE 0 END) / COUNT(*), 2) as crowdstrike_percentage
                FROM ultimate_universal_endpoint
            """,
            
            'missing_from_cmdb': """
                SELECT hostname, source_systems, confidence_score
                FROM ultimate_universal_endpoint 
                WHERE NOT found_in_cmdb 
                ORDER BY confidence_score DESC
                LIMIT 100
            """,
            
            'visibility_gaps': """
                SELECT hostname, source_systems, confidence_score
                FROM ultimate_universal_endpoint 
                WHERE source_count = 1 AND confidence_score > 0.7
                ORDER BY confidence_score DESC
                LIMIT 50
            """,
            
            'best_visibility': """
                SELECT hostname, source_systems, source_count, confidence_score
                FROM ultimate_universal_endpoint 
                WHERE source_count >= 3
                ORDER BY confidence_score DESC
                LIMIT 50
            """,
            
            'source_distribution': """
                SELECT 
                    source_systems,
                    COUNT(*) as asset_count
                FROM ultimate_universal_endpoint
                GROUP BY source_systems
                ORDER BY asset_count DESC
            """
        }
    
    def close(self):
        """Close the database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logger.info("Ultimate CMDB Builder closed")