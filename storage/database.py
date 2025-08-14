import duckdb
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from core.types import HyperAsset, QuantumDiscovery

logger = logging.getLogger(__name__)

class QuantumEnhancedDatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_quantum_comprehensive_schema()
    
    def _setup_quantum_comprehensive_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS comprehensive_hosts")
        self.conn.execute("DROP TABLE IF EXISTS discovery_meta")
        
        self.conn.execute("""
            CREATE TABLE comprehensive_hosts (
                hostname VARCHAR PRIMARY KEY,
                country VARCHAR,
                region VARCHAR,
                business_unit VARCHAR,
                cio VARCHAR,
                datacenter VARCHAR,
                application_class VARCHAR,
                infrastructure_type VARCHAR,
                system_classification VARCHAR,
                ip_address VARCHAR,
                fqdn VARCHAR,
                source_tables JSON,
                sources_count INTEGER DEFAULT 0,
                cmdb_coverage BOOLEAN DEFAULT FALSE,
                splunk_coverage BOOLEAN DEFAULT FALSE,
                chronicle_coverage BOOLEAN DEFAULT FALSE,
                crowdstrike_coverage BOOLEAN DEFAULT FALSE,
                edr_coverage BOOLEAN DEFAULT FALSE,
                dlp_coverage BOOLEAN DEFAULT FALSE,
                tanium_coverage BOOLEAN DEFAULT FALSE,
                visibility_score DOUBLE DEFAULT 0.0,
                raw_data JSON,
                first_seen TIMESTAMP,
                last_updated TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE discovery_meta (
                id VARCHAR PRIMARY KEY,
                discovery_type VARCHAR,
                total_tables_processed INTEGER,
                unique_hosts_discovered INTEGER,
                total_host_instances INTEGER,
                processing_time_seconds DOUBLE,
                comprehensive_mode BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info(f"Comprehensive hosts database schema initialized: {self.db_path}")
    
    def store_comprehensive_hosts(self, hosts_data: Dict[str, Any], discovery_stats: Dict[str, Any]) -> int:
        stored_count = 0
        discovery_id = f"comprehensive_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for hostname, host_data in hosts_data.items():
            try:
                values = [
                    hostname,
                    host_data.get('country', ''),
                    host_data.get('region', ''),
                    host_data.get('business_unit', ''),
                    host_data.get('cio', ''),
                    host_data.get('datacenter', ''),
                    host_data.get('application_class', ''),
                    host_data.get('infrastructure_type', ''),
                    host_data.get('system_classification', ''),
                    host_data.get('ip_address', ''),
                    host_data.get('fqdn', ''),
                    json.dumps(host_data.get('source_tables', [])),
                    host_data.get('sources_count', 0),
                    host_data.get('cmdb_coverage', False),
                    host_data.get('splunk_coverage', False),
                    host_data.get('chronicle_coverage', False),
                    host_data.get('crowdstrike_coverage', False),
                    host_data.get('edr_coverage', False),
                    host_data.get('dlp_coverage', False),
                    host_data.get('tanium_coverage', False),
                    host_data.get('visibility_score', 0.0),
                    json.dumps(host_data.get('raw_data', {}), default=str),
                    host_data.get('first_seen', datetime.now())
                ]
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO comprehensive_hosts (
                        hostname, country, region, business_unit, cio, datacenter,
                        application_class, infrastructure_type, system_classification,
                        ip_address, fqdn, source_tables, sources_count,
                        cmdb_coverage, splunk_coverage, chronicle_coverage, crowdstrike_coverage,
                        edr_coverage, dlp_coverage, tanium_coverage, visibility_score,
                        raw_data, first_seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, values)
                
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store host {hostname}: {e}")
        
        try:
            self.conn.execute("""
                INSERT INTO discovery_meta (
                    id, discovery_type, total_tables_processed, unique_hosts_discovered,
                    total_host_instances, processing_time_seconds, comprehensive_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                discovery_id, "comprehensive_cmdb", 
                discovery_stats.get('total_tables_processed', 0),
                discovery_stats.get('unique_hosts_discovered', 0),
                discovery_stats.get('total_host_instances', 0),
                discovery_stats.get('processing_time', 0),
                True
            ])
        except Exception as e:
            logger.error(f"Failed to store discovery metadata: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} comprehensive hosts to database")
        return stored_count
    
    def get_comprehensive_queries(self) -> Dict[str, str]:
        return {
            'summary': """
                SELECT 
                    COUNT(*) as total_hosts,
                    COUNT(CASE WHEN cmdb_coverage THEN 1 END) as cmdb_covered,
                    COUNT(CASE WHEN splunk_coverage THEN 1 END) as splunk_covered,
                    COUNT(CASE WHEN chronicle_coverage THEN 1 END) as chronicle_covered,
                    COUNT(CASE WHEN edr_coverage THEN 1 END) as edr_covered,
                    COUNT(CASE WHEN sources_count > 1 THEN 1 END) as multi_source,
                    ROUND(AVG(visibility_score), 3) as avg_visibility,
                    ROUND(AVG(sources_count), 1) as avg_sources_per_host
                FROM comprehensive_hosts
            """,
            
            'by_business_unit': """
                SELECT 
                    business_unit,
                    COUNT(*) as host_count,
                    ROUND(AVG(visibility_score), 3) as avg_visibility,
                    COUNT(CASE WHEN cmdb_coverage THEN 1 END) as cmdb_covered
                FROM comprehensive_hosts
                WHERE business_unit IS NOT NULL AND business_unit != ''
                GROUP BY business_unit
                ORDER BY host_count DESC
            """,
            
            'visibility_gaps': """
                SELECT hostname, country, region, business_unit, sources_count, visibility_score,
                       cmdb_coverage, edr_coverage, splunk_coverage
                FROM comprehensive_hosts 
                WHERE visibility_score < 0.5 OR sources_count = 1
                ORDER BY visibility_score ASC, sources_count ASC
                LIMIT 500
            """,
            
            'top_coverage': """
                SELECT hostname, country, region, business_unit, sources_count, visibility_score,
                       cmdb_coverage, edr_coverage, splunk_coverage, chronicle_coverage
                FROM comprehensive_hosts 
                WHERE visibility_score > 0.8 AND sources_count > 3
                ORDER BY visibility_score DESC, sources_count DESC
                LIMIT 100
            """
        }
        self.conn.execute("DROP TABLE IF EXISTS quantum_comprehensive_assets")
        self.conn.execute("DROP TABLE IF EXISTS quantum_discovery_meta")
        
        self.conn.execute("""
            CREATE TABLE quantum_comprehensive_assets (
                entity_id VARCHAR PRIMARY KEY,
                primary_identity VARCHAR,
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
                source_count INTEGER DEFAULT 0,
                evidence_count INTEGER DEFAULT 0,
                intelligence_quotient DOUBLE DEFAULT 0.0,
                quality_coefficient DOUBLE DEFAULT 0.0,
                confidence_index DOUBLE DEFAULT 0.0,
                visibility_score DOUBLE DEFAULT 0.0,
                entropy_measure DOUBLE DEFAULT 0.0,
                quantum_coherence DOUBLE DEFAULT 0.0,
                entity_resolved BOOLEAN DEFAULT TRUE,
                quantum_enhanced BOOLEAN DEFAULT TRUE,
                emergence_detected BOOLEAN DEFAULT FALSE,
                first_seen TIMESTAMP DEFAULT NOW(),
                last_seen TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE quantum_discovery_meta (
                id VARCHAR PRIMARY KEY,
                discovery_type VARCHAR,
                discovery_mode VARCHAR,
                quantum_entity_resolution_applied BOOLEAN DEFAULT FALSE,
                total_hyper_assets INTEGER,
                processing_time_seconds DOUBLE,
                quantum_cells_analyzed INTEGER,
                quantum_emergence_events INTEGER,
                intelligence_metrics JSON,
                emergence_insights JSON,
                strategic_recommendations JSON,
                quantum_coherence DOUBLE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info(f"Quantum enhanced database schema initialized: {self.db_path}")
    
    def store_comprehensive_discovery(self, quantum_discovery: QuantumDiscovery) -> int:
        stored_count = 0
        discovery_id = f"quantum_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for hyper_asset in quantum_discovery.hyper_assets.values():
            try:
                self._store_quantum_comprehensive_asset(hyper_asset)
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store quantum comprehensive asset {hyper_asset.id}: {e}")
        
        try:
            self._store_quantum_comprehensive_meta(quantum_discovery, discovery_id)
        except Exception as e:
            logger.error(f"Failed to store quantum comprehensive discovery metadata: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} quantum comprehensive assets to database")
        return stored_count
    
    def _store_quantum_comprehensive_asset(self, hyper_asset: HyperAsset):
        values = [
            hyper_asset.id, hyper_asset.primary_identity, hyper_asset.hostname, 
            hyper_asset.ip, hyper_asset.fqdn, getattr(hyper_asset, 'mac', ''),
            hyper_asset.infrastructure_type, hyper_asset.system_classification, 
            getattr(hyper_asset, 'application_type', ''),
            hyper_asset.region, getattr(hyper_asset, 'country', ''), 
            hyper_asset.datacenter, hyper_asset.cloud_region,
            hyper_asset.business_unit, hyper_asset.cio, 
            getattr(hyper_asset, 'apm', ''), hyper_asset.application_class,
            hyper_asset.edr_coverage, hyper_asset.dlp_coverage, hyper_asset.tanium_coverage, 
            hyper_asset.splunk_coverage, hyper_asset.chronicle_coverage,
            getattr(hyper_asset, 'gso_coverage', False), hyper_asset.cmdb_visibility, 
            hyper_asset.crowdstrike_coverage,
            len(hyper_asset.source_provenance), len(hyper_asset.evidence_chains),
            hyper_asset.intelligence_quotient, hyper_asset.quality_coefficient, 
            hyper_asset.confidence_index, hyper_asset.visibility_score, 
            hyper_asset.entropy_measure, hyper_asset.quantum_state.get('coherence', 0.0),
            True, True, len(hyper_asset.emergence_patterns) > 0
        ]
        
        self.conn.execute("""
            INSERT INTO quantum_comprehensive_assets (
                entity_id, primary_identity, hostname, ip_address, fqdn, mac_address,
                infrastructure_type, system_classification, application_type,
                global_region, country, datacenter, cloud_region,
                business_unit, cio, apm, application_class,
                edr_coverage, dlp_coverage, tanium_coverage, splunk_coverage,
                chronicle_coverage, gso_coverage, cmdb_visibility, crowdstrike_coverage,
                source_count, evidence_count, intelligence_quotient,
                quality_coefficient, confidence_index, visibility_score, 
                entropy_measure, quantum_coherence, entity_resolved, 
                quantum_enhanced, emergence_detected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
    
    def _store_quantum_comprehensive_meta(self, quantum_discovery: QuantumDiscovery, discovery_id: str):
        self.conn.execute("""
            INSERT INTO quantum_discovery_meta (
                id, discovery_type, discovery_mode, quantum_entity_resolution_applied,
                total_hyper_assets, processing_time_seconds, quantum_cells_analyzed,
                quantum_emergence_events, intelligence_metrics, emergence_insights, strategic_recommendations,
                quantum_coherence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            discovery_id, "quantum_comprehensive", "quantum_entity_resolution", True,
            len(quantum_discovery.hyper_assets), 
            quantum_discovery.intelligence_metrics.get('processing_time_seconds', 0),
            quantum_discovery.intelligence_metrics.get('total_cells_analyzed', 0),
            quantum_discovery.intelligence_metrics.get('quantum_emergence_events', 0),
            json.dumps(quantum_discovery.intelligence_metrics), 
            json.dumps([dict(i) for i in quantum_discovery.emergence_insights]),
            json.dumps(quantum_discovery.strategic_recommendations),
            quantum_discovery.quantum_coherence
        ])
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Quantum query execution failed: {e}")
            return []
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Quantum enhanced database connection closed")

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

EnhancedDatabaseManager = QuantumEnhancedDatabaseManager