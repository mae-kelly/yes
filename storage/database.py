# storage/database.py

import duckdb
import json
import logging
import os
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class QuantumEnhancedDatabaseManager:
    def __init__(self, db_path: str = "quantum_discovery.db"):
        self.db_path = str(db_path)
        self.conn = None
        self.stored_count = 0
        self.updated_count = 0
        self.error_count = 0
        self._initialize_database()
    
    def _initialize_database(self):
        try:
            if os.path.exists(self.db_path):
                backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(self.db_path, backup_path)
                logger.info(f"Backed up existing database to {backup_path}")
            
            self.conn = duckdb.connect(self.db_path)
            self._create_comprehensive_schema()
            logger.info(f"Quantum database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _create_comprehensive_schema(self):
        self.conn.execute("""
            CREATE TABLE assets (
                asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR NOT NULL,
                primary_identity VARCHAR,
                
                ip_address VARCHAR,
                fqdn VARCHAR,
                mac_address VARCHAR,
                
                infrastructure_type VARCHAR,
                system_classification VARCHAR,
                operating_system VARCHAR,
                platform VARCHAR,
                architecture VARCHAR,
                
                business_unit VARCHAR,
                department VARCHAR,
                cost_center VARCHAR,
                application_name VARCHAR,
                application_class VARCHAR,
                criticality VARCHAR,
                
                global_region VARCHAR,
                country VARCHAR,
                state_province VARCHAR,
                city VARCHAR,
                datacenter VARCHAR,
                zone VARCHAR,
                cloud_provider VARCHAR,
                cloud_region VARCHAR,
                availability_zone VARCHAR,
                
                owner VARCHAR,
                technical_contact VARCHAR,
                business_contact VARCHAR,
                manager VARCHAR,
                cio VARCHAR,
                
                environment VARCHAR,
                lifecycle_stage VARCHAR,
                support_tier VARCHAR,
                maintenance_window VARCHAR,
                
                asset_tag VARCHAR,
                serial_number VARCHAR,
                model VARCHAR,
                manufacturer VARCHAR,
                purchase_date VARCHAR,
                warranty_expiration VARCHAR,
                
                network_segment VARCHAR,
                vlan VARCHAR,
                subnet VARCHAR,
                domain VARCHAR,
                forest VARCHAR,
                
                edr_coverage BOOLEAN DEFAULT false,
                edr_agent_version VARCHAR,
                dlp_coverage BOOLEAN DEFAULT false,
                dlp_agent_version VARCHAR,
                tanium_coverage BOOLEAN DEFAULT false,
                tanium_agent_version VARCHAR,
                splunk_coverage BOOLEAN DEFAULT false,
                splunk_forwarder_version VARCHAR,
                chronicle_coverage BOOLEAN DEFAULT false,
                chronicle_collector_version VARCHAR,
                crowdstrike_coverage BOOLEAN DEFAULT false,
                crowdstrike_agent_version VARCHAR,
                cmdb_visibility BOOLEAN DEFAULT false,
                cmdb_last_update VARCHAR,
                
                antivirus_installed BOOLEAN DEFAULT false,
                antivirus_product VARCHAR,
                antivirus_version VARCHAR,
                firewall_enabled BOOLEAN DEFAULT false,
                encryption_status VARCHAR,
                patch_level VARCHAR,
                vulnerability_score REAL,
                
                visibility_score REAL DEFAULT 0.0,
                quality_score REAL DEFAULT 0.0,
                confidence_score REAL DEFAULT 0.0,
                intelligence_quotient REAL DEFAULT 0.0,
                risk_score REAL DEFAULT 0.0,
                compliance_score REAL DEFAULT 0.0,
                
                ml_confidence REAL DEFAULT 0.0,
                ml_field_type VARCHAR,
                ml_processing_method VARCHAR,
                
                source_count INTEGER DEFAULT 0,
                total_rows INTEGER DEFAULT 0,
                source_tables TEXT,
                all_data_json TEXT,
                
                coverage_analysis TEXT,
                risk_assessment TEXT,
                compliance_status TEXT,
                
                first_seen TIMESTAMP,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE discovery_metadata (
                id INTEGER PRIMARY KEY,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                project_id VARCHAR,
                total_assets_discovered INTEGER,
                total_tables_processed INTEGER,
                total_rows_processed INTEGER,
                ml_predictions_made INTEGER,
                high_confidence_predictions INTEGER,
                processing_time_seconds REAL,
                ml_enabled BOOLEAN,
                engines_used TEXT,
                configuration TEXT,
                statistics TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE asset_relationships (
                id INTEGER PRIMARY KEY,
                source_asset_id VARCHAR,
                target_asset_id VARCHAR,
                relationship_type VARCHAR,
                confidence REAL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_asset_id) REFERENCES assets(asset_id),
                FOREIGN KEY (target_asset_id) REFERENCES assets(asset_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE data_sources (
                id INTEGER PRIMARY KEY,
                asset_id VARCHAR,
                table_path VARCHAR,
                column_name VARCHAR,
                sample_value VARCHAR,
                field_type VARCHAR,
                confidence REAL,
                discovery_method VARCHAR,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY,
                asset_id VARCHAR,
                action VARCHAR,
                old_values TEXT,
                new_values TEXT,
                changed_by VARCHAR,
                change_reason VARCHAR,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self._create_indexes()
        self.conn.commit()
    
    def _create_indexes(self):
        indexes = [
            "CREATE INDEX idx_assets_hostname ON assets(hostname)",
            "CREATE INDEX idx_assets_ip ON assets(ip_address)",
            "CREATE INDEX idx_assets_business_unit ON assets(business_unit)",
            "CREATE INDEX idx_assets_region ON assets(global_region)",
            "CREATE INDEX idx_assets_visibility ON assets(visibility_score)",
            "CREATE INDEX idx_assets_risk ON assets(risk_score)",
            "CREATE INDEX idx_assets_criticality ON assets(criticality)",
            "CREATE INDEX idx_assets_environment ON assets(environment)",
            "CREATE INDEX idx_assets_edr ON assets(edr_coverage)",
            "CREATE INDEX idx_assets_chronicle ON assets(chronicle_coverage)",
            "CREATE INDEX idx_assets_last_updated ON assets(last_updated)",
            "CREATE INDEX idx_relationships_source ON asset_relationships(source_asset_id)",
            "CREATE INDEX idx_relationships_target ON asset_relationships(target_asset_id)",
            "CREATE INDEX idx_data_sources_asset ON data_sources(asset_id)",
            "CREATE INDEX idx_data_sources_table ON data_sources(table_path)"
        ]
        
        for index_sql in indexes:
            try:
                self.conn.execute(index_sql)
            except Exception as e:
                logger.debug(f"Index creation skipped: {e}")
    
    def store_comprehensive_discovery_results(self, assets: Dict[str, Any], 
                                            statistics: Dict[str, Any]) -> int:
        logger.info(f"Storing {len(assets)} assets to quantum database")
        
        stored_count = 0
        
        try:
            self.conn.begin()
            
            discovery_id = self._store_discovery_metadata(statistics)
            
            for asset_id, asset_data in assets.items():
                try:
                    if self._store_single_asset(asset_id, asset_data, discovery_id):
                        stored_count += 1
                except Exception as e:
                    logger.error(f"Failed to store asset {asset_id}: {e}")
                    self.error_count += 1
            
            self.conn.commit()
            self.stored_count = stored_count
            logger.info(f"Successfully stored {stored_count} assets")
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            self.conn.rollback()
            raise
        
        return stored_count
    
    def _store_discovery_metadata(self, statistics: Dict[str, Any]) -> int:
        metadata_sql = """
            INSERT INTO discovery_metadata (
                project_id, total_assets_discovered, total_tables_processed,
                total_rows_processed, ml_predictions_made, high_confidence_predictions,
                processing_time_seconds, ml_enabled, engines_used, configuration, statistics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = self.conn.execute(metadata_sql, [
            statistics.get('project_id', ''),
            statistics.get('total_assets_discovered', 0),
            statistics.get('total_tables_processed', 0),
            statistics.get('total_rows_processed', 0),
            statistics.get('ml_predictions_made', 0),
            statistics.get('high_confidence_predictions', 0),
            statistics.get('processing_time_seconds', 0.0),
            statistics.get('ml_enabled', False),
            json.dumps(statistics.get('engines_used', [])),
            json.dumps(statistics.get('configuration', {})),
            json.dumps(statistics)
        ])
        
        return cursor.lastrowid
    
    def _store_single_asset(self, asset_id: str, asset_data: Dict[str, Any], 
                           discovery_id: int) -> bool:
        try:
            all_data = asset_data.get('all_data', {})
            coverage_flags = asset_data.get('coverage_flags', {})
            
            def get_first_value(key: str, default: str = '') -> str:
                values = all_data.get(key, [])
                if isinstance(values, list) and values:
                    return str(values[0])
                elif values:
                    return str(values)
                return default
            
            def get_boolean_value(key: str, default: bool = False) -> bool:
                return bool(coverage_flags.get(key, default))
            
            asset_sql = """
                INSERT OR REPLACE INTO assets (
                    asset_id, hostname, primary_identity,
                    ip_address, fqdn, mac_address,
                    infrastructure_type, system_classification, operating_system,
                    platform, architecture,
                    business_unit, department, cost_center, application_name,
                    application_class, criticality,
                    global_region, country, state_province, city, datacenter,
                    zone, cloud_provider, cloud_region, availability_zone,
                    owner, technical_contact, business_contact, manager, cio,
                    environment, lifecycle_stage, support_tier, maintenance_window,
                    asset_tag, serial_number, model, manufacturer,
                    purchase_date, warranty_expiration,
                    network_segment, vlan, subnet, domain, forest,
                    edr_coverage, edr_agent_version, dlp_coverage, dlp_agent_version,
                    tanium_coverage, tanium_agent_version, splunk_coverage, splunk_forwarder_version,
                    chronicle_coverage, chronicle_collector_version, crowdstrike_coverage, crowdstrike_agent_version,
                    cmdb_visibility, cmdb_last_update,
                    antivirus_installed, antivirus_product, antivirus_version,
                    firewall_enabled, encryption_status, patch_level, vulnerability_score,
                    visibility_score, quality_score, confidence_score, intelligence_quotient,
                    risk_score, compliance_score,
                    ml_confidence, ml_field_type, ml_processing_method,
                    source_count, total_rows, source_tables, all_data_json,
                    coverage_analysis, risk_assessment, compliance_status,
                    first_seen, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = [
                str(asset_id),
                asset_data.get('hostname', ''),
                asset_data.get('primary_identity', ''),
                
                get_first_value('ip_address'),
                get_first_value('fqdn'),
                get_first_value('mac_address'),
                
                get_first_value('infrastructure_type'),
                get_first_value('system_classification'),
                get_first_value('operating_system'),
                get_first_value('platform'),
                get_first_value('architecture'),
                
                get_first_value('business_unit'),
                get_first_value('department'),
                get_first_value('cost_center'),
                get_first_value('application_name'),
                get_first_value('application_class'),
                get_first_value('criticality'),
                
                get_first_value('global_region'),
                get_first_value('country'),
                get_first_value('state_province'),
                get_first_value('city'),
                get_first_value('datacenter'),
                get_first_value('zone'),
                get_first_value('cloud_provider'),
                get_first_value('cloud_region'),
                get_first_value('availability_zone'),
                
                get_first_value('owner'),
                get_first_value('technical_contact'),
                get_first_value('business_contact'),
                get_first_value('manager'),
                get_first_value('cio'),
                
                get_first_value('environment'),
                get_first_value('lifecycle_stage'),
                get_first_value('support_tier'),
                get_first_value('maintenance_window'),
                
                get_first_value('asset_tag'),
                get_first_value('serial_number'),
                get_first_value('model'),
                get_first_value('manufacturer'),
                get_first_value('purchase_date'),
                get_first_value('warranty_expiration'),
                
                get_first_value('network_segment'),
                get_first_value('vlan'),
                get_first_value('subnet'),
                get_first_value('domain'),
                get_first_value('forest'),
                
                get_boolean_value('in_crowdstrike'),
                get_first_value('edr_agent_version'),
                get_boolean_value('in_dlp'),
                get_first_value('dlp_agent_version'),
                get_boolean_value('in_tanium'),
                get_first_value('tanium_agent_version'),
                get_boolean_value('in_splunk'),
                get_first_value('splunk_forwarder_version'),
                get_boolean_value('in_chronicle'),
                get_first_value('chronicle_collector_version'),
                get_boolean_value('in_crowdstrike'),
                get_first_value('crowdstrike_agent_version'),
                get_boolean_value('in_original_cmdb'),
                get_first_value('cmdb_last_update'),
                
                get_boolean_value('antivirus_installed'),
                get_first_value('antivirus_product'),
                get_first_value('antivirus_version'),
                get_boolean_value('firewall_enabled'),
                get_first_value('encryption_status'),
                get_first_value('patch_level'),
                float(asset_data.get('vulnerability_score', 0.0)),
                
                float(asset_data.get('visibility_score', 0.0)),
                float(asset_data.get('quality_score', 0.0)),
                float(asset_data.get('confidence_score', 0.0)),
                float(asset_data.get('intelligence_quotient', 0.0)),
                float(asset_data.get('risk_score', 0.0)),
                float(asset_data.get('compliance_score', 0.0)),
                
                float(asset_data.get('ml_confidence', 0.0)),
                asset_data.get('ml_field_type', ''),
                asset_data.get('ml_processing_method', ''),
                
                int(asset_data.get('source_count', 0)),
                int(asset_data.get('total_rows', 0)),
                json.dumps(asset_data.get('source_tables', [])),
                json.dumps(all_data),
                
                json.dumps(asset_data.get('coverage_analysis', {})),
                json.dumps(asset_data.get('risk_assessment', {})),
                json.dumps(asset_data.get('compliance_status', {})),
                
                asset_data.get('first_seen', datetime.now().isoformat()),
                datetime.now().isoformat()
            ]
            
            self.conn.execute(asset_sql, params)
            
            self._store_data_sources(asset_id, asset_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Asset storage failed for {asset_id}: {e}")
            return False
    
    def _store_data_sources(self, asset_id: str, asset_data: Dict[str, Any]):
        try:
            source_tables = asset_data.get('source_tables', [])
            all_data = asset_data.get('all_data', {})
            
            for table_path in source_tables:
                for column_name, values in all_data.items():
                    if isinstance(values, list) and values:
                        sample_value = str(values[0])
                    elif values:
                        sample_value = str(values)
                    else:
                        continue
                    
                    self.conn.execute("""
                        INSERT OR IGNORE INTO data_sources (
                            asset_id, table_path, column_name, sample_value,
                            field_type, confidence, discovery_method
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, [
                        asset_id, table_path, column_name, sample_value,
                        column_name, 0.8, 'comprehensive_discovery'
                    ])
        except Exception as e:
            logger.debug(f"Data sources storage failed for {asset_id}: {e}")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        try:
            stats = {}
            
            stats['total_assets'] = self.conn.execute(
                "SELECT COUNT(*) FROM assets"
            ).fetchone()[0]
            
            stats['assets_with_edr'] = self.conn.execute(
                "SELECT COUNT(*) FROM assets WHERE edr_coverage = true"
            ).fetchone()[0]
            
            stats['assets_with_chronicle'] = self.conn.execute(
                "SELECT COUNT(*) FROM assets WHERE chronicle_coverage = true"
            ).fetchone()[0]
            
            stats['assets_with_cmdb'] = self.conn.execute(
                "SELECT COUNT(*) FROM assets WHERE cmdb_visibility = true"
            ).fetchone()[0]
            
            stats['high_risk_assets'] = self.conn.execute(
                "SELECT COUNT(*) FROM assets WHERE risk_score > 0.7"
            ).fetchone()[0]
            
            stats['high_visibility_assets'] = self.conn.execute(
                "SELECT COUNT(*) FROM assets WHERE visibility_score > 0.8"
            ).fetchone()[0]
            
            stats['business_units'] = self.conn.execute(
                "SELECT COUNT(DISTINCT business_unit) FROM assets WHERE business_unit != ''"
            ).fetchone()[0]
            
            stats['regions'] = self.conn.execute(
                "SELECT COUNT(DISTINCT global_region) FROM assets WHERE global_region != ''"
            ).fetchone()[0]
            
            stats['infrastructure_types'] = self.conn.execute(
                "SELECT COUNT(DISTINCT infrastructure_type) FROM assets WHERE infrastructure_type != ''"
            ).fetchone()[0]
            
            stats['avg_visibility_score'] = self.conn.execute(
                "SELECT AVG(visibility_score) FROM assets"
            ).fetchone()[0] or 0.0
            
            stats['avg_quality_score'] = self.conn.execute(
                "SELECT AVG(quality_score) FROM assets"
            ).fetchone()[0] or 0.0
            
            stats['avg_risk_score'] = self.conn.execute(
                "SELECT AVG(risk_score) FROM assets"
            ).fetchone()[0] or 0.0
            
            stats['database_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            
            stats['last_discovery'] = self.conn.execute(
                "SELECT MAX(discovery_timestamp) FROM discovery_metadata"
            ).fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Stats calculation failed: {e}")
            return {'error': str(e)}
    
    def query_assets(self, filters: Dict[str, Any] = None, 
                    limit: int = 1000) -> List[Dict[str, Any]]:
        try:
            base_query = "SELECT * FROM assets"
            conditions = []
            params = []
            
            if filters:
                if 'business_unit' in filters:
                    conditions.append("business_unit = ?")
                    params.append(filters['business_unit'])
                
                if 'region' in filters:
                    conditions.append("global_region = ?")
                    params.append(filters['region'])
                
                if 'edr_coverage' in filters:
                    conditions.append("edr_coverage = ?")
                    params.append(filters['edr_coverage'])
                
                if 'min_visibility_score' in filters:
                    conditions.append("visibility_score >= ?")
                    params.append(filters['min_visibility_score'])
                
                if 'risk_level' in filters:
                    if filters['risk_level'] == 'high':
                        conditions.append("risk_score > 0.7")
                    elif filters['risk_level'] == 'medium':
                        conditions.append("risk_score BETWEEN 0.4 AND 0.7")
                    elif filters['risk_level'] == 'low':
                        conditions.append("risk_score < 0.4")
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += f" ORDER BY last_updated DESC LIMIT {limit}"
            
            cursor = self.conn.execute(base_query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def get_asset_by_hostname(self, hostname: str) -> Optional[Dict[str, Any]]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM assets WHERE hostname = ? OR asset_id = ?",
                [hostname, hostname]
            )
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            logger.error(f"Asset lookup failed for {hostname}: {e}")
            return None
    
    def update_asset_coverage(self, asset_id: str, coverage_updates: Dict[str, Any]) -> bool:
        try:
            update_fields = []
            params = []
            
            for field, value in coverage_updates.items():
                if field in ['edr_coverage', 'dlp_coverage', 'tanium_coverage', 
                           'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 
                           'cmdb_visibility']:
                    update_fields.append(f"{field} = ?")
                    params.append(bool(value))
            
            if update_fields:
                update_fields.append("last_updated = ?")
                params.append(datetime.now().isoformat())
                params.append(asset_id)
                
                sql = f"UPDATE assets SET {', '.join(update_fields)} WHERE asset_id = ?"
                self.conn.execute(sql, params)
                self.conn.commit()
                
                self.updated_count += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Coverage update failed for {asset_id}: {e}")
            return False
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        try:
            report = {}
            
            coverage_fields = [
                'edr_coverage', 'dlp_coverage', 'tanium_coverage', 
                'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 
                'cmdb_visibility'
            ]
            
            for field in coverage_fields:
                covered = self.conn.execute(
                    f"SELECT COUNT(*) FROM assets WHERE {field} = true"
                ).fetchone()[0]
                
                total = self.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
                
                report[field] = {
                    'covered_count': covered,
                    'total_count': total,
                    'coverage_percentage': (covered / total * 100) if total > 0 else 0
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Coverage report generation failed: {e}")
            return {}
    
    def export_to_json(self, output_path: str, filters: Dict[str, Any] = None) -> bool:
        try:
            assets = self.query_assets(filters, limit=50000)
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_assets': len(assets),
                'filters_applied': filters or {},
                'assets': assets
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported {len(assets)} assets to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def close(self):
        try:
            if self.conn:
                self.conn.commit()
                self.conn.close()
                logger.info(f"Database closed: {self.stored_count} stored, {self.updated_count} updated")
        except Exception as e:
            logger.error(f"Database close failed: {e}")

DatabaseManager = QuantumEnhancedDatabaseManager
MaximumIntensityDatabaseManager = QuantumEnhancedDatabaseManager
EnhancedDatabaseManager = QuantumEnhancedDatabaseManager
ContentDatabase = QuantumEnhancedDatabaseManager