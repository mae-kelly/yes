import duckdb
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from core.quantum_types import QuantumAsset, DiscoveryMetrics

logger = logging.getLogger(__name__)

class QuantumDatabase:
    def __init__(self, db_path: str = "ao1_visibility.duckdb"):
        self.db_path = db_path
        self.conn = duckdb.connect(database=db_path)
        self._initialize_schema()
    
    def _initialize_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR NOT NULL,
                infrastructure_type VARCHAR,
                region VARCHAR,
                country VARCHAR,
                business_unit VARCHAR,
                datacenter VARCHAR,
                cloud_region VARCHAR,
                cio VARCHAR,
                apm VARCHAR,
                application_class VARCHAR,
                system_classification VARCHAR,
                domain VARCHAR,
                ip_address VARCHAR,
                fqdn VARCHAR,
                mac_address VARCHAR,
                owner VARCHAR,
                criticality VARCHAR,
                environment VARCHAR,
                geolocation VARCHAR,
                vpc VARCHAR,
                
                edr_coverage BOOLEAN DEFAULT FALSE,
                tanium_coverage BOOLEAN DEFAULT FALSE,
                dlp_coverage BOOLEAN DEFAULT FALSE,
                splunk_logging BOOLEAN DEFAULT FALSE,
                gso_logging BOOLEAN DEFAULT FALSE,
                crowdstrike_coverage BOOLEAN DEFAULT FALSE,
                chronicle_coverage BOOLEAN DEFAULT FALSE,
                cmdb_visibility BOOLEAN DEFAULT FALSE,
                ipam_public_ip BOOLEAN DEFAULT FALSE,
                
                visibility_score DOUBLE DEFAULT 0.0,
                confidence_score DOUBLE DEFAULT 0.0,
                risk_score DOUBLE DEFAULT 0.0,
                compliance_score DOUBLE DEFAULT 0.0,
                ml_confidence DOUBLE DEFAULT 0.0,
                
                source_tables TEXT,
                log_types TEXT,
                data_fields TEXT,
                visibility_factors TEXT,
                anomaly_scores TEXT,
                network_zones TEXT,
                
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS discovery_metrics (
                id INTEGER PRIMARY KEY,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_assets INTEGER,
                cmdb_coverage DOUBLE,
                url_fqdn_coverage DOUBLE,
                public_ip_coverage DOUBLE,
                endpoint_coverage DOUBLE,
                cloud_coverage DOUBLE,
                network_coverage DOUBLE,
                application_coverage DOUBLE,
                identity_coverage DOUBLE,
                host_parity DOUBLE,
                infrastructure_distribution TEXT,
                regional_distribution TEXT,
                business_unit_distribution TEXT,
                system_classification_distribution TEXT,
                security_gaps TEXT,
                logging_gaps TEXT,
                compliance_issues TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS log_mappings (
                id INTEGER PRIMARY KEY,
                role VARCHAR,
                log_types TEXT,
                data_fields TEXT,
                visibility_factors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS coverage_analysis (
                id INTEGER PRIMARY KEY,
                analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_hosts INTEGER,
                edr_coverage_count INTEGER,
                tanium_coverage_count INTEGER,
                dlp_coverage_count INTEGER,
                splunk_coverage_count INTEGER,
                gso_coverage_count INTEGER,
                chronicle_coverage_count INTEGER,
                crowdstrike_coverage_count INTEGER,
                cmdb_coverage_count INTEGER,
                
                edr_percentage DOUBLE,
                tanium_percentage DOUBLE,
                dlp_percentage DOUBLE,
                splunk_percentage DOUBLE,
                gso_percentage DOUBLE,
                chronicle_percentage DOUBLE,
                crowdstrike_percentage DOUBLE,
                cmdb_percentage DOUBLE,
                
                infrastructure_gaps TEXT,
                regional_gaps TEXT,
                business_unit_gaps TEXT,
                system_class_gaps TEXT
            )
        """)
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_assets_hostname ON assets(hostname)",
            "CREATE INDEX IF NOT EXISTS idx_assets_infrastructure ON assets(infrastructure_type)",
            "CREATE INDEX IF NOT EXISTS idx_assets_region ON assets(region)",
            "CREATE INDEX IF NOT EXISTS idx_assets_business_unit ON assets(business_unit)",
            "CREATE INDEX IF NOT EXISTS idx_assets_system_class ON assets(system_classification)",
            "CREATE INDEX IF NOT EXISTS idx_assets_visibility ON assets(visibility_score)",
            "CREATE INDEX IF NOT EXISTS idx_assets_edr ON assets(edr_coverage)",
            "CREATE INDEX IF NOT EXISTS idx_assets_splunk ON assets(splunk_logging)",
            "CREATE INDEX IF NOT EXISTS idx_assets_gso ON assets(gso_logging)",
            "CREATE INDEX IF NOT EXISTS idx_assets_cmdb ON assets(cmdb_visibility)"
        ]
        
        for index_sql in indexes:
            self.conn.execute(index_sql)
        
        self.conn.commit()
    
    def store_assets(self, assets: Dict[str, QuantumAsset]) -> int:
        stored_count = 0
        
        for asset_id, asset in assets.items():
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO assets (
                        asset_id, hostname, infrastructure_type, region, country,
                        business_unit, datacenter, cloud_region, cio, apm,
                        application_class, system_classification, domain,
                        ip_address, fqdn, mac_address, owner, criticality,
                        environment, geolocation, vpc,
                        edr_coverage, tanium_coverage, dlp_coverage,
                        splunk_logging, gso_logging, crowdstrike_coverage,
                        chronicle_coverage, cmdb_visibility, ipam_public_ip,
                        visibility_score, confidence_score, risk_score,
                        compliance_score, ml_confidence,
                        source_tables, log_types, data_fields,
                        visibility_factors, anomaly_scores, network_zones,
                        first_seen, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    asset_id, asset.hostname, asset.infrastructure_type, asset.region, asset.country,
                    asset.business_unit, asset.datacenter, asset.cloud_region, asset.cio, asset.apm,
                    asset.application_class, asset.system_classification, asset.domain,
                    asset.ip_address, asset.fqdn, asset.mac_address, asset.owner, asset.criticality,
                    asset.environment, asset.geolocation, asset.vpc,
                    asset.edr_coverage, asset.tanium_coverage, asset.dlp_coverage,
                    asset.splunk_logging, asset.gso_logging, asset.crowdstrike_coverage,
                    asset.chronicle_coverage, asset.cmdb_visibility, asset.ipam_public_ip,
                    asset.visibility_score, asset.confidence_score, asset.risk_score,
                    asset.compliance_score, asset.ml_confidence,
                    json.dumps(list(asset.source_tables)),
                    json.dumps(asset.log_types),
                    json.dumps(asset.data_fields),
                    json.dumps(asset.visibility_factors),
                    json.dumps(asset.anomaly_scores),
                    json.dumps(asset.network_zones),
                    asset.first_seen.isoformat(),
                    asset.last_seen.isoformat()
                ])
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store asset {asset_id}: {e}")
        
        self.conn.commit()
        return stored_count
    
    def store_metrics(self, metrics: DiscoveryMetrics) -> bool:
        try:
            self.conn.execute("""
                INSERT INTO discovery_metrics (
                    total_assets, cmdb_coverage, url_fqdn_coverage,
                    public_ip_coverage, endpoint_coverage, cloud_coverage,
                    network_coverage, application_coverage, identity_coverage,
                    host_parity, infrastructure_distribution, regional_distribution,
                    business_unit_distribution, system_classification_distribution,
                    security_gaps, logging_gaps, compliance_issues
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                metrics.total_assets, metrics.cmdb_coverage, metrics.url_fqdn_coverage,
                metrics.public_ip_coverage, metrics.endpoint_coverage, metrics.cloud_coverage,
                metrics.network_coverage, metrics.application_coverage, metrics.identity_coverage,
                metrics.host_parity,
                json.dumps(metrics.infrastructure_distribution),
                json.dumps(metrics.regional_distribution),
                json.dumps(metrics.business_unit_distribution),
                json.dumps(metrics.system_classification_distribution),
                json.dumps(metrics.security_gaps),
                json.dumps(metrics.logging_gaps),
                json.dumps(metrics.compliance_issues)
            ])
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
            return False
    
    def analyze_coverage(self) -> Dict[str, Any]:
        total_hosts = self.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        
        if total_hosts == 0:
            return {}
        
        coverage_fields = [
            'edr_coverage', 'tanium_coverage', 'dlp_coverage',
            'splunk_logging', 'gso_logging', 'crowdstrike_coverage',
            'chronicle_coverage', 'cmdb_visibility'
        ]
        
        coverage_stats = {}
        for field in coverage_fields:
            count = self.conn.execute(f"SELECT COUNT(*) FROM assets WHERE {field} = true").fetchone()[0]
            percentage = (count / total_hosts) * 100
            coverage_stats[field] = {
                'count': count,
                'percentage': percentage,
                'gap_count': total_hosts - count
            }
        
        infrastructure_gaps = self.conn.execute("""
            SELECT infrastructure_type, COUNT(*) as count,
                   SUM(CASE WHEN edr_coverage = false THEN 1 ELSE 0 END) as no_edr,
                   SUM(CASE WHEN splunk_logging = false THEN 1 ELSE 0 END) as no_splunk
            FROM assets
            GROUP BY infrastructure_type
        """).fetchall()
        
        regional_gaps = self.conn.execute("""
            SELECT region, COUNT(*) as count,
                   SUM(CASE WHEN cmdb_visibility = false THEN 1 ELSE 0 END) as no_cmdb
            FROM assets
            WHERE region IS NOT NULL
            GROUP BY region
        """).fetchall()
        
        try:
            self.conn.execute("""
                INSERT INTO coverage_analysis (
                    total_hosts, edr_coverage_count, tanium_coverage_count,
                    dlp_coverage_count, splunk_coverage_count, gso_coverage_count,
                    chronicle_coverage_count, crowdstrike_coverage_count, cmdb_coverage_count,
                    edr_percentage, tanium_percentage, dlp_percentage,
                    splunk_percentage, gso_percentage, chronicle_percentage,
                    crowdstrike_percentage, cmdb_percentage,
                    infrastructure_gaps, regional_gaps
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                total_hosts,
                coverage_stats['edr_coverage']['count'],
                coverage_stats['tanium_coverage']['count'],
                coverage_stats['dlp_coverage']['count'],
                coverage_stats['splunk_logging']['count'],
                coverage_stats['gso_logging']['count'],
                coverage_stats['chronicle_coverage']['count'],
                coverage_stats['crowdstrike_coverage']['count'],
                coverage_stats['cmdb_visibility']['count'],
                coverage_stats['edr_coverage']['percentage'],
                coverage_stats['tanium_coverage']['percentage'],
                coverage_stats['dlp_coverage']['percentage'],
                coverage_stats['splunk_logging']['percentage'],
                coverage_stats['gso_logging']['percentage'],
                coverage_stats['chronicle_coverage']['percentage'],
                coverage_stats['crowdstrike_coverage']['percentage'],
                coverage_stats['cmdb_visibility']['percentage'],
                json.dumps([dict(zip(['type', 'count', 'no_edr', 'no_splunk'], gap)) for gap in infrastructure_gaps]),
                json.dumps([dict(zip(['region', 'count', 'no_cmdb'], gap)) for gap in regional_gaps])
            ])
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to store coverage analysis: {e}")
        
        return {
            'total_hosts': total_hosts,
            'coverage': coverage_stats,
            'infrastructure_gaps': infrastructure_gaps,
            'regional_gaps': regional_gaps
        }
    
    def get_visibility_report(self) -> Dict[str, Any]:
        report = {}
        
        report['summary'] = self.conn.execute("""
            SELECT 
                COUNT(*) as total_assets,
                AVG(visibility_score) as avg_visibility,
                COUNT(CASE WHEN visibility_score >= 0.8 THEN 1 END) as high_visibility,
                COUNT(CASE WHEN visibility_score < 0.5 THEN 1 END) as low_visibility,
                COUNT(CASE WHEN cmdb_visibility = true THEN 1 END) as in_cmdb,
                COUNT(CASE WHEN splunk_logging = true OR gso_logging = true THEN 1 END) as has_logging
            FROM assets
        """).fetchone()
        
        report['by_infrastructure'] = self.conn.execute("""
            SELECT 
                infrastructure_type,
                COUNT(*) as count,
                AVG(visibility_score) as avg_visibility,
                SUM(CASE WHEN edr_coverage = true THEN 1 ELSE 0 END) as with_edr,
                SUM(CASE WHEN splunk_logging = true THEN 1 ELSE 0 END) as with_splunk
            FROM assets
            WHERE infrastructure_type IS NOT NULL
            GROUP BY infrastructure_type
            ORDER BY count DESC
        """).fetchall()
        
        report['by_region'] = self.conn.execute("""
            SELECT 
                region,
                COUNT(*) as count,
                AVG(visibility_score) as avg_visibility
            FROM assets
            WHERE region IS NOT NULL
            GROUP BY region
            ORDER BY count DESC
        """).fetchall()
        
        report['by_business_unit'] = self.conn.execute("""
            SELECT 
                business_unit,
                COUNT(*) as count,
                AVG(visibility_score) as avg_visibility
            FROM assets
            WHERE business_unit IS NOT NULL
            GROUP BY business_unit
            ORDER BY count DESC
        """).fetchall()
        
        report['system_classification'] = self.conn.execute("""
            SELECT 
                system_classification,
                COUNT(*) as count,
                AVG(visibility_score) as avg_visibility
            FROM assets
            WHERE system_classification IS NOT NULL
            GROUP BY system_classification
            ORDER BY count DESC
        """).fetchall()
        
        report['critical_gaps'] = self.conn.execute("""
            SELECT 
                hostname,
                infrastructure_type,
                region,
                visibility_score
            FROM assets
            WHERE (edr_coverage = false AND tanium_coverage = false)
               OR (splunk_logging = false AND gso_logging = false)
               OR visibility_score < 0.3
            ORDER BY visibility_score ASC
            LIMIT 100
        """).fetchall()
        
        return report
    
    def export_to_csv(self, output_path: str):
        df = self.conn.execute("SELECT * FROM assets").fetchdf()
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(df)} assets to {output_path}")
    
    def close(self):
        self.conn.close()