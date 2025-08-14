import duckdb
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict
from core.types import HyperAsset, QuantumDiscovery

logger = logging.getLogger(__name__)

class QuantumEnhancedDatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_quantum_comprehensive_schema()
    
    def _setup_quantum_comprehensive_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS quantum_comprehensive_assets")
        self.conn.execute("DROP TABLE IF EXISTS quantum_asset_identities")
        self.conn.execute("DROP TABLE IF EXISTS quantum_asset_evidence")
        self.conn.execute("DROP TABLE IF EXISTS quantum_coverage_metrics")
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
            CREATE TABLE quantum_asset_identities (
                id VARCHAR PRIMARY KEY,
                entity_id VARCHAR,
                identifier_type VARCHAR,
                identifier_value VARCHAR,
                normalized_value VARCHAR,
                confidence DOUBLE,
                source_table VARCHAR,
                source_system VARCHAR,
                quantum_signature VARCHAR,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (entity_id) REFERENCES quantum_comprehensive_assets(entity_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE quantum_asset_evidence (
                id VARCHAR PRIMARY KEY,
                entity_id VARCHAR,
                source_table VARCHAR,
                source_system VARCHAR,
                evidence_type VARCHAR,
                field_name VARCHAR,
                field_value VARCHAR,
                confidence DOUBLE,
                reliability_score DOUBLE,
                quantum_coherence_score DOUBLE,
                emergence_probability DOUBLE,
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (entity_id) REFERENCES quantum_comprehensive_assets(entity_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE quantum_coverage_metrics (
                id VARCHAR PRIMARY KEY,
                entity_id VARCHAR,
                metric_type VARCHAR,
                metric_name VARCHAR,
                metric_value DOUBLE,
                calculation_method VARCHAR,
                quantum_enhanced BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (entity_id) REFERENCES quantum_comprehensive_assets(entity_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE quantum_discovery_meta (
                id VARCHAR PRIMARY KEY,
                discovery_type VARCHAR,
                discovery_mode VARCHAR,
                quantum_entity_resolution_applied BOOLEAN DEFAULT FALSE,
                total_hyper_assets INTEGER,
                total_evidence_pieces INTEGER,
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
            json.dumps(getattr(hyper_asset, 'network_log_types', [])),
            json.dumps(getattr(hyper_asset, 'endpoint_log_types', [])),
            json.dumps(getattr(hyper_asset, 'cloud_log_types', [])),
            json.dumps(getattr(hyper_asset, 'application_log_types', [])),
            json.dumps(getattr(hyper_asset, 'identity_log_types', [])),
            getattr(hyper_asset, 'url_fqdn_coverage', False),
            getattr(hyper_asset, 'public_ip_coverage', False),
            ','.join(hyper_asset.network_zones) if hyper_asset.network_zones else '',
            getattr(hyper_asset, 'vpc_coverage', False),
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
                network_log_types, endpoint_log_types, cloud_log_types,
                application_log_types, identity_log_types, url_fqdn_coverage,
                public_ip_coverage, network_zones, vpc_coverage,
                source_count, evidence_count, intelligence_quotient,
                quality_coefficient, confidence_index, visibility_score, 
                entropy_measure, quantum_coherence, entity_resolved, 
                quantum_enhanced, emergence_detected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    
    def get_quantum_comprehensive_visibility_queries(self) -> Dict[str, str]:
        return {
            'quantum_comprehensive_summary': """
                SELECT 
                    COUNT(*) as total_hyper_assets,
                    SUM(CASE WHEN cmdb_visibility THEN 1 ELSE 0 END) as cmdb_coverage,
                    SUM(CASE WHEN splunk_coverage THEN 1 ELSE 0 END) as splunk_coverage,
                    SUM(CASE WHEN chronicle_coverage THEN 1 ELSE 0 END) as chronicle_coverage,
                    SUM(CASE WHEN crowdstrike_coverage THEN 1 ELSE 0 END) as crowdstrike_coverage,
                    SUM(CASE WHEN edr_coverage THEN 1 ELSE 0 END) as edr_coverage,
                    SUM(CASE WHEN dlp_coverage THEN 1 ELSE 0 END) as dlp_coverage,
                    SUM(CASE WHEN tanium_coverage THEN 1 ELSE 0 END) as tanium_coverage,
                    SUM(CASE WHEN source_count > 1 THEN 1 ELSE 0 END) as multi_source,
                    SUM(CASE WHEN quantum_enhanced THEN 1 ELSE 0 END) as quantum_enhanced,
                    SUM(CASE WHEN emergence_detected THEN 1 ELSE 0 END) as emergence_detected,
                    ROUND(AVG(intelligence_quotient), 3) as avg_intelligence_quotient,
                    ROUND(AVG(quality_coefficient), 3) as avg_quality_coefficient,
                    ROUND(AVG(confidence_index), 3) as avg_confidence_index,
                    ROUND(AVG(visibility_score), 3) as avg_visibility_score,
                    ROUND(AVG(entropy_measure), 3) as avg_entropy_measure,
                    ROUND(AVG(quantum_coherence), 3) as avg_quantum_coherence
                FROM quantum_comprehensive_assets
            """,
            
            'quantum_infrastructure_visibility': """
                SELECT 
                    infrastructure_type,
                    COUNT(*) as asset_count,
                    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM quantum_comprehensive_assets), 2) as percentage,
                    SUM(CASE WHEN cmdb_visibility THEN 1 ELSE 0 END) as cmdb_covered,
                    SUM(CASE WHEN edr_coverage THEN 1 ELSE 0 END) as edr_covered,
                    SUM(CASE WHEN quantum_enhanced THEN 1 ELSE 0 END) as quantum_enhanced_count,
                    ROUND(AVG(intelligence_quotient), 3) as avg_intelligence_quotient,
                    ROUND(AVG(visibility_score), 3) as avg_visibility_score
                FROM quantum_comprehensive_assets
                WHERE infrastructure_type IS NOT NULL AND infrastructure_type != ''
                GROUP BY infrastructure_type
                ORDER BY asset_count DESC
            """,
            
            'quantum_emergence_analysis': """
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN emergence_detected THEN 1 ELSE 0 END) as emergence_detected_count,
                    ROUND(100.0 * SUM(CASE WHEN emergence_detected THEN 1 ELSE 0 END) / COUNT(*), 2) as emergence_percentage,
                    AVG(CASE WHEN emergence_detected THEN intelligence_quotient ELSE NULL END) as avg_emergence_intelligence,
                    AVG(CASE WHEN emergence_detected THEN visibility_score ELSE NULL END) as avg_emergence_visibility,
                    AVG(CASE WHEN emergence_detected THEN quantum_coherence ELSE NULL END) as avg_emergence_coherence
                FROM quantum_comprehensive_assets
            """,
            
            'quantum_high_value_assets': """
                SELECT entity_id, primary_identity, hostname, infrastructure_type, system_classification,
                       global_region, business_unit, source_count, evidence_count,
                       intelligence_quotient, quality_coefficient, confidence_index, visibility_score,
                       quantum_coherence, emergence_detected,
                       cmdb_visibility, edr_coverage, splunk_coverage, chronicle_coverage
                FROM quantum_comprehensive_assets 
                WHERE quality_coefficient > 0.85 AND intelligence_quotient > 0.8 AND quantum_enhanced = TRUE
                ORDER BY quality_coefficient DESC, intelligence_quotient DESC, visibility_score DESC
                LIMIT 100
            """,
            
            'quantum_visibility_gaps': """
                SELECT entity_id, primary_identity, hostname, infrastructure_type, global_region, business_unit,
                       source_count, intelligence_quotient, quality_coefficient, visibility_score,
                       cmdb_visibility, edr_coverage, dlp_coverage, tanium_coverage,
                       splunk_coverage, chronicle_coverage, quantum_enhanced, emergence_detected
                FROM quantum_comprehensive_assets 
                WHERE (NOT cmdb_visibility 
                   OR (NOT edr_coverage AND NOT dlp_coverage AND NOT tanium_coverage)
                   OR source_count = 1
                   OR visibility_score < 0.5)
                   AND quantum_enhanced = TRUE
                ORDER BY quality_coefficient DESC, intelligence_quotient DESC
                LIMIT 200
            """
        }
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Quantum query execution failed: {e}")
            return []
    
    def get_quantum_comprehensive_coverage_report(self) -> Dict[str, Any]:
        queries = self.get_quantum_comprehensive_visibility_queries()
        report = {}
        
        for query_name, query_sql in queries.items():
            try:
                result = self.execute_query(query_sql)
                report[query_name] = result
            except Exception as e:
                logger.error(f"Failed to execute quantum {query_name}: {e}")
                report[query_name] = []
        
        return report
    
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