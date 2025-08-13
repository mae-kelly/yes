# storage/database.py

import duckdb
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from core.types import Asset, Discovery

logger = logging.getLogger(__name__)

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