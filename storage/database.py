# storage/database.py - enhanced version

import duckdb
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict
from core.types import Asset, Discovery

logger = logging.getLogger(__name__)

class EnhancedDatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_comprehensive_schema()
    
    def _setup_comprehensive_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS comprehensive_assets")
        self.conn.execute("DROP TABLE IF EXISTS asset_identities")
        self.conn.execute("DROP TABLE IF EXISTS asset_evidence")
        self.conn.execute("DROP TABLE IF EXISTS coverage_metrics")
        self.conn.execute("DROP TABLE IF EXISTS discovery_meta")
        
        self.conn.execute("""
            CREATE TABLE comprehensive_assets (
                entity_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                ip_address VARCHAR,
                fqdn VARCHAR,
                mac_address VARCHAR,
                infrastructure_type VARCHAR,
                system_classification VARCHAR,
                application_type VARCHAR,
                global_region VARCHAR,
                country VARCHAR,
                datacenter VARCHAR,
                cloud_region VARCHAR,
                business_unit VARCHAR,
                cio VARCHAR,
                apm VARCHAR,
                application_class VARCHAR,
                edr_coverage BOOLEAN DEFAULT FALSE,
                dlp_coverage BOOLEAN DEFAULT FALSE,
                tanium_coverage BOOLEAN DEFAULT FALSE,
                splunk_coverage BOOLEAN DEFAULT FALSE,
                chronicle_coverage BOOLEAN DEFAULT FALSE,
                gso_coverage BOOLEAN DEFAULT FALSE,
                cmdb_visibility BOOLEAN DEFAULT FALSE,
                crowdstrike_coverage BOOLEAN DEFAULT FALSE,
                network_log_types JSON,
                endpoint_log_types JSON,
                cloud_log_types JSON,
                application_log_types JSON,
                identity_log_types JSON,
                url_fqdn_coverage BOOLEAN DEFAULT FALSE,
                public_ip_coverage BOOLEAN DEFAULT FALSE,
                network_zones VARCHAR,
                vpc_coverage BOOLEAN DEFAULT FALSE,
                source_count INTEGER DEFAULT 0,
                evidence_count INTEGER DEFAULT 0,
                intelligence_score DOUBLE DEFAULT 0.0,
                quality_score DOUBLE DEFAULT 0.0,
                confidence_score DOUBLE DEFAULT 0.0,
                entity_resolved BOOLEAN DEFAULT TRUE,
                first_seen TIMESTAMP DEFAULT NOW(),
                last_seen TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE asset_identities (
                id VARCHAR PRIMARY KEY,
                entity_id VARCHAR,
                identifier_type VARCHAR,
                identifier_value VARCHAR,
                normalized_value VARCHAR,
                confidence DOUBLE,
                source_table VARCHAR,
                source_system VARCHAR,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (entity_id) REFERENCES comprehensive_assets(entity_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE asset_evidence (
                id VARCHAR PRIMARY KEY,
                entity_id VARCHAR,
                source_table VARCHAR,
                source_system VARCHAR,
                evidence_type VARCHAR,
                field_name VARCHAR,
                field_value VARCHAR,
                confidence DOUBLE,
                reliability_score DOUBLE,
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (entity_id) REFERENCES comprehensive_assets(entity_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE coverage_metrics (
                id VARCHAR PRIMARY KEY,
                entity_id VARCHAR,
                metric_type VARCHAR,
                metric_name VARCHAR,
                metric_value DOUBLE,
                calculation_method VARCHAR,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (entity_id) REFERENCES comprehensive_assets(entity_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE discovery_meta (
                id VARCHAR PRIMARY KEY,
                discovery_type VARCHAR,
                discovery_mode VARCHAR,
                entity_resolution_applied BOOLEAN DEFAULT FALSE,
                total_assets INTEGER,
                total_evidence_pieces INTEGER,
                processing_time_seconds DOUBLE,
                stats JSON,
                insights JSON,
                recommendations JSON,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info(f"Enhanced database schema initialized: {self.db_path}")
    
    def store_comprehensive_discovery(self, discovery: Discovery) -> int:
        stored_count = 0
        discovery_id = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for asset in discovery.assets.values():
            try:
                self._store_comprehensive_asset(asset)
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store comprehensive asset {asset.id}: {e}")
        
        try:
            self._store_comprehensive_meta(discovery, discovery_id)
        except Exception as e:
            logger.error(f"Failed to store comprehensive discovery metadata: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} comprehensive assets to database")
        return stored_count
    
    def _store_comprehensive_asset(self, asset: Asset):
        values = [
            asset.id, asset.hostname, asset.ip, asset.fqdn, getattr(asset, 'mac', ''),
            asset.infra_type, asset.system_class, getattr(asset, 'application_type', ''),
            asset.region, asset.country, asset.datacenter, asset.cloud_region,
            asset.business_unit, asset.cio, getattr(asset, 'apm', ''), asset.app_class,
            asset.edr, asset.dlp, asset.tanium, asset.splunk, asset.chronicle,
            getattr(asset, 'gso', False), asset.cmdb, asset.crowdstrike,
            json.dumps(getattr(asset, 'network_log_types', [])),
            json.dumps(getattr(asset, 'endpoint_log_types', [])),
            json.dumps(getattr(asset, 'cloud_log_types', [])),
            json.dumps(getattr(asset, 'application_log_types', [])),
            json.dumps(getattr(asset, 'identity_log_types', [])),
            getattr(asset, 'url_fqdn_coverage', False),
            getattr(asset, 'public_ip_coverage', False),
            getattr(asset, 'network_zones', ''),
            getattr(asset, 'vpc_coverage', False),
            asset.sources, getattr(asset, 'evidence_count', 0),
            asset.intelligence, asset.quality, asset.confidence, True
        ]
        
        self.conn.execute("""
            INSERT INTO comprehensive_assets (
                entity_id, hostname, ip_address, fqdn, mac_address,
                infrastructure_type, system_classification, application_type,
                global_region, country, datacenter, cloud_region,
                business_unit, cio, apm, application_class,
                edr_coverage, dlp_coverage, tanium_coverage, splunk_coverage,
                chronicle_coverage, gso_coverage, cmdb_visibility, crowdstrike_coverage,
                network_log_types, endpoint_log_types, cloud_log_types,
                application_log_types, identity_log_types, url_fqdn_coverage,
                public_ip_coverage, network_zones, vpc_coverage,
                source_count, evidence_count, intelligence_score,
                quality_score, confidence_score, entity_resolved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
    
    def _store_comprehensive_meta(self, discovery: Discovery, discovery_id: str):
        self.conn.execute("""
            INSERT INTO discovery_meta (
                id, discovery_type, discovery_mode, entity_resolution_applied,
                total_assets, processing_time_seconds, stats, insights, recommendations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            discovery_id, "comprehensive", "entity_resolution", True,
            len(discovery.assets), discovery.stats.get('processing_time_seconds', 0),
            json.dumps(discovery.stats), json.dumps([dict(i) for i in discovery.insights]),
            json.dumps(discovery.recommendations)
        ])
    
    def get_comprehensive_visibility_queries(self) -> Dict[str, str]:
        return {
            'comprehensive_summary': """
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN cmdb_visibility THEN 1 ELSE 0 END) as cmdb_coverage,
                    SUM(CASE WHEN splunk_coverage THEN 1 ELSE 0 END) as splunk_coverage,
                    SUM(CASE WHEN chronicle_coverage THEN 1 ELSE 0 END) as chronicle_coverage,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                    SUM(CASE WHEN edr_coverage THEN 1 ELSE 0 END) as edr_coverage,
                    SUM(CASE WHEN dlp_coverage THEN 1 ELSE 0 END) as dlp_coverage,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                    SUM(CASE WHEN source_count > 1 THEN 1 ELSE 0 END) as multi_source,
                    ROUND(AVG(intelligence_score), 3) as avg_intelligence,
                    ROUND(AVG(quality_score), 3) as avg_quality,
                    ROUND(AVG(confidence_score), 3) as avg_confidence
                FROM comprehensive_assets
            """,
            
            'infrastructure_visibility': """
                SELECT 
                    infrastructure_type,
                    COUNT(*) as asset_count,
                    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM comprehensive_assets), 2) as percentage,
                    SUM(CASE WHEN cmdb_visibility THEN 1 ELSE 0 END) as cmdb_covered,
                    SUM(CASE WHEN edr_coverage THEN 1 ELSE 0 END) as edr_covered,
                    ROUND(AVG(intelligence_score), 3) as avg_intelligence
                FROM comprehensive_assets
                WHERE infrastructure_type IS NOT NULL AND infrastructure_type != ''
                GROUP BY infrastructure_type
                ORDER BY asset_count DESC
            """,
            
            'regional_visibility': """
                SELECT 
                    global_region,
                    COUNT(*) as asset_count,
                    SUM(CASE WHEN cmdb_visibility THEN 1 ELSE 0 END) as cmdb_covered,
                    SUM(CASE WHEN splunk_coverage THEN 1 ELSE 0 END) as splunk_covered,
                    SUM(CASE WHEN chronicle_coverage THEN 1 ELSE 0 END) as chronicle_covered,
                    ROUND(100.0 * SUM(CASE WHEN cmdb_visibility THEN 1 ELSE 0 END) / COUNT(*), 2) as cmdb_coverage_pct
                FROM comprehensive_assets
                WHERE global_region IS NOT NULL AND global_region != ''
                GROUP BY global_region
                ORDER BY asset_count DESC
            """,
            
            'business_unit_visibility': """
                SELECT 
                    business_unit,
                    COUNT(*) as asset_count,
                    SUM(CASE WHEN edr_coverage THEN 1 ELSE 0 END) as edr_covered,
                    SUM(CASE WHEN dlp_coverage THEN 1 ELSE 0 END) as dlp_covered,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_covered,
                    ROUND(100.0 * SUM(CASE WHEN edr_coverage OR dlp_coverage OR tanium_coverage THEN 1 ELSE 0 END) / COUNT(*), 2) as security_coverage_pct
                FROM comprehensive_assets
                WHERE business_unit IS NOT NULL AND business_unit != ''
                GROUP BY business_unit
                ORDER BY asset_count DESC
            """,
            
            'system_classification_visibility': """
                SELECT 
                    system_classification,
                    COUNT(*) as asset_count,
                    SUM(CASE WHEN cmdb_visibility THEN 1 ELSE 0 END) as cmdb_covered,
                    SUM(CASE WHEN edr_coverage THEN 1 ELSE 0 END) as edr_covered,
                    ROUND(AVG(quality_score), 3) as avg_quality
                FROM comprehensive_assets
                WHERE system_classification IS NOT NULL AND system_classification != ''
                GROUP BY system_classification
                ORDER BY asset_count DESC
            """,
            
            'logging_platform_coverage': """
                SELECT 
                    'Splunk' as platform,
                    SUM(CASE WHEN splunk_coverage THEN 1 ELSE 0 END) as covered_assets,
                    ROUND(100.0 * SUM(CASE WHEN splunk_coverage THEN 1 ELSE 0 END) / COUNT(*), 2) as coverage_percentage
                FROM comprehensive_assets
                UNION ALL
                SELECT 
                    'Chronicle' as platform,
                    SUM(CASE WHEN chronicle_coverage THEN 1 ELSE 0 END) as covered_assets,
                    ROUND(100.0 * SUM(CASE WHEN chronicle_coverage THEN 1 ELSE 0 END) / COUNT(*), 2) as coverage_percentage
                FROM comprehensive_assets
                UNION ALL
                SELECT 
                    'GSO' as platform,
                    SUM(CASE WHEN gso_coverage THEN 1 ELSE 0 END) as covered_assets,
                    ROUND(100.0 * SUM(CASE WHEN gso_coverage THEN 1 ELSE 0 END) / COUNT(*), 2) as coverage_percentage
                FROM comprehensive_assets
                ORDER BY coverage_percentage DESC
            """,
            
            'security_control_coverage': """
                SELECT 
                    'EDR' as control_type,
                    SUM(CASE WHEN edr_coverage THEN 1 ELSE 0 END) as covered_assets,
                    ROUND(100.0 * SUM(CASE WHEN edr_coverage THEN 1 ELSE 0 END) / COUNT(*), 2) as coverage_percentage
                FROM comprehensive_assets
                UNION ALL
                SELECT 
                    'DLP' as control_type,
                    SUM(CASE WHEN dlp_coverage THEN 1 ELSE 0 END) as covered_assets,
                    ROUND(100.0 * SUM(CASE WHEN dlp_coverage THEN 1 ELSE 0 END) / COUNT(*), 2) as coverage_percentage
                FROM comprehensive_assets
                UNION ALL
                SELECT 
                    'Tanium' as control_type,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as covered_assets,
                    ROUND(100.0 * SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) / COUNT(*), 2) as coverage_percentage
                FROM comprehensive_assets
                ORDER BY coverage_percentage DESC
            """,
            
            'visibility_gaps': """
                SELECT entity_id, hostname, infrastructure_type, global_region, business_unit,
                       source_count, intelligence_score, quality_score,
                       cmdb_visibility, edr_coverage, dlp_coverage, tanium_coverage,
                       splunk_coverage, chronicle_coverage
                FROM comprehensive_assets 
                WHERE NOT cmdb_visibility 
                   OR (NOT edr_coverage AND NOT dlp_coverage AND NOT tanium_coverage)
                   OR source_count = 1
                ORDER BY quality_score DESC, intelligence_score DESC
                LIMIT 100
            """,
            
            'high_value_assets': """
                SELECT entity_id, hostname, infrastructure_type, system_classification,
                       global_region, business_unit, source_count, evidence_count,
                       intelligence_score, quality_score, confidence_score,
                       cmdb_visibility, edr_coverage, splunk_coverage, chronicle_coverage
                FROM comprehensive_assets 
                WHERE quality_score > 0.8 AND intelligence_score > 0.7
                ORDER BY quality_score DESC, intelligence_score DESC, source_count DESC
                LIMIT 50
            """,
            
            'entity_resolution_stats': """
                SELECT 
                    COUNT(*) as total_entities,
                    SUM(CASE WHEN entity_resolved THEN 1 ELSE 0 END) as resolved_entities,
                    AVG(source_count) as avg_sources_per_entity,
                    AVG(evidence_count) as avg_evidence_per_entity,
                    MAX(source_count) as max_sources_per_entity,
                    SUM(CASE WHEN source_count > 1 THEN 1 ELSE 0 END) as multi_source_entities
                FROM comprehensive_assets
            """
        }
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def get_comprehensive_coverage_report(self) -> Dict[str, Any]:
        queries = self.get_comprehensive_visibility_queries()
        report = {}
        
        for query_name, query_sql in queries.items():
            try:
                result = self.execute_query(query_sql)
                report[query_name] = result
            except Exception as e:
                logger.error(f"Failed to execute {query_name}: {e}")
                report[query_name] = []
        
        return report
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Enhanced database connection closed")

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_schema()
    
    def _setup_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS assets")
        self.conn.execute("DROP TABLE IF EXISTS discovery_meta")
        
        self.conn.execute("""
            CREATE TABLE assets (
                id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                ip VARCHAR,
                fqdn VARCHAR,
                mac VARCHAR,
                infra_type VARCHAR,
                system_class VARCHAR,
                region VARCHAR,
                country VARCHAR,
                datacenter VARCHAR,
                cloud_region VARCHAR,
                business_unit VARCHAR,
                cio VARCHAR,
                app_class VARCHAR,
                edr BOOLEAN DEFAULT FALSE,
                dlp BOOLEAN DEFAULT FALSE,
                tanium BOOLEAN DEFAULT FALSE,
                splunk BOOLEAN DEFAULT FALSE,
                chronicle BOOLEAN DEFAULT FALSE,
                gso BOOLEAN DEFAULT FALSE,
                cmdb BOOLEAN DEFAULT FALSE,
                crowdstrike BOOLEAN DEFAULT FALSE,
                sources INTEGER DEFAULT 0,
                intelligence DOUBLE DEFAULT 0.0,
                quality DOUBLE DEFAULT 0.0,
                confidence DOUBLE DEFAULT 0.0,
                raw_data JSON,
                metadata JSON,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE discovery_meta (
                id VARCHAR PRIMARY KEY,
                discovery_type VARCHAR,
                stats JSON,
                insights JSON,
                recommendations JSON,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info(f"Database schema initialized: {self.db_path}")
    
    def store_discovery(self, discovery: Discovery, discovery_type: str = "intelligent") -> int:
        stored_count = 0
        
        for asset in discovery.assets.values():
            try:
                self._store_asset(asset)
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store asset {asset.id}: {e}")
        
        try:
            self._store_meta(discovery, discovery_type)
        except Exception as e:
            logger.error(f"Failed to store discovery metadata: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} assets to database")
        return stored_count
    
    def _store_asset(self, asset: Asset):
        values = [
            asset.id, asset.hostname, asset.ip, asset.fqdn, asset.mac,
            asset.infra_type, asset.system_class, asset.region, asset.country,
            asset.datacenter, asset.cloud_region, asset.business_unit,
            asset.cio, asset.app_class, asset.edr, asset.dlp, asset.tanium,
            asset.splunk, asset.chronicle, asset.gso, asset.cmdb, asset.crowdstrike,
            asset.sources, asset.intelligence, asset.quality, asset.confidence,
            json.dumps(asset.raw), json.dumps(asset.meta)
        ]
        
        self.conn.execute("""
            INSERT INTO assets (
                id, hostname, ip, fqdn, mac, infra_type, system_class, region,
                country, datacenter, cloud_region, business_unit, cio, app_class,
                edr, dlp, tanium, splunk, chronicle, gso, cmdb, crowdstrike,
                sources, intelligence, quality, confidence, raw_data, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
    
    def _store_meta(self, discovery: Discovery, discovery_type: str):
        meta_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.conn.execute("""
            INSERT INTO discovery_meta (id, discovery_type, stats, insights, recommendations)
            VALUES (?, ?, ?, ?, ?)
        """, [
            meta_id,
            discovery_type,
            json.dumps(discovery.stats),
            json.dumps([dict(insight) for insight in discovery.insights]),
            json.dumps(discovery.recommendations)
        ])
    
    def get_visibility_queries(self) -> Dict[str, str]:
        return {
            'asset_summary': """
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN cmdb THEN 1 ELSE 0 END) as cmdb_coverage,
                    SUM(CASE WHEN splunk THEN 1 ELSE 0 END) as splunk_coverage,
                    SUM(CASE WHEN chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                    SUM(CASE WHEN crowdstrike THEN 1 ELSE 0 END) as crowdstrike_coverage,
                    SUM(CASE WHEN sources > 1 THEN 1 ELSE 0 END) as multi_source,
                    ROUND(AVG(intelligence), 3) as avg_intelligence,
                    ROUND(AVG(quality), 3) as avg_quality,
                    ROUND(AVG(confidence), 3) as avg_confidence
                FROM assets
            """,
            
            'coverage_percentages': """
                SELECT 
                    ROUND(100.0 * SUM(CASE WHEN cmdb THEN 1 ELSE 0 END) / COUNT(*), 2) as cmdb_pct,
                    ROUND(100.0 * SUM(CASE WHEN splunk THEN 1 ELSE 0 END) / COUNT(*), 2) as splunk_pct,
                    ROUND(100.0 * SUM(CASE WHEN chronicle THEN 1 ELSE 0 END) / COUNT(*), 2) as chronicle_pct,
                    ROUND(100.0 * SUM(CASE WHEN crowdstrike THEN 1 ELSE 0 END) / COUNT(*), 2) as crowdstrike_pct
                FROM assets
            """,
            
            'high_quality_assets': """
                SELECT hostname, infra_type, system_class, sources, intelligence, quality, confidence
                FROM assets 
                WHERE quality > 0.8 
                ORDER BY quality DESC, intelligence DESC
                LIMIT 50
            """,
            
            'coverage_gaps': """
                SELECT hostname, infra_type, sources, intelligence, quality
                FROM assets 
                WHERE NOT cmdb AND sources = 1 AND quality > 0.7
                ORDER BY quality DESC
                LIMIT 50
            """,
            
            'multi_source_assets': """
                SELECT hostname, sources, 
                       CASE WHEN cmdb THEN 'CMDB ' ELSE '' END ||
                       CASE WHEN splunk THEN 'Splunk ' ELSE '' END ||
                       CASE WHEN chronicle THEN 'Chronicle ' ELSE '' END ||
                       CASE WHEN crowdstrike THEN 'CrowdStrike' ELSE '' END as source_list,
                       intelligence, quality, confidence
                FROM assets 
                WHERE sources >= 2
                ORDER BY sources DESC, intelligence DESC
                LIMIT 100
            """,
            
            'asset_distribution': """
                SELECT 
                    infra_type,
                    COUNT(*) as count,
                    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM assets), 2) as percentage,
                    ROUND(AVG(intelligence), 3) as avg_intelligence
                FROM assets
                WHERE infra_type IS NOT NULL AND infra_type != ''
                GROUP BY infra_type
                ORDER BY count DESC
            """,
            
            'region_distribution': """
                SELECT 
                    region,
                    COUNT(*) as count,
                    ROUND(AVG(intelligence), 3) as avg_intelligence,
                    SUM(CASE WHEN cmdb THEN 1 ELSE 0 END) as cmdb_count
                FROM assets
                WHERE region IS NOT NULL AND region != ''
                GROUP BY region
                ORDER BY count DESC
            """,
            
            'security_coverage': """
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN edr THEN 1 ELSE 0 END) as edr_coverage,
                    SUM(CASE WHEN dlp THEN 1 ELSE 0 END) as dlp_coverage,
                    SUM(CASE WHEN tanium THEN 1 ELSE 0 END) as tanium_coverage,
                    ROUND(100.0 * SUM(CASE WHEN edr OR dlp OR tanium THEN 1 ELSE 0 END) / COUNT(*), 2) as any_security_pct
                FROM assets
            """
        }
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def get_asset_counts(self) -> Dict[str, int]:
        summary_query = self.get_visibility_queries()['asset_summary']
        result = self.execute_query(summary_query)
        
        if result:
            return result[0]
        else:
            return {}
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

class ContentDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_content_schema()
    
    def _setup_content_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS content_assets")
        
        self.conn.execute("""
            CREATE TABLE content_assets (
                id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                source_tables JSON,
                all_data JSON,
                confidence_scores JSON,
                sources INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
    
    def store_content_assets(self, assets: Dict[str, Any]) -> int:
        stored_count = 0
        
        for asset_id, asset_data in assets.items():
            try:
                values = [
                    asset_id,
                    asset_data.get('hostname', ''),
                    json.dumps(asset_data.get('source_tables', [])),
                    json.dumps(asset_data.get('all_data', {}), default=str),
                    json.dumps(asset_data.get('confidence_scores', {})),
                    asset_data.get('source_count', 0)
                ]
                
                self.conn.execute("""
                    INSERT INTO content_assets (id, hostname, source_tables, all_data, confidence_scores, sources)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, values)
                
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store content asset {asset_id}: {e}")
        
        self.conn.commit()
        return stored_count
    
    def close(self):
        if self.conn:
            self.conn.close()