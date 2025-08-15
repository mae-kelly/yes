import duckdb
import json
import logging
import os
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MaximumIntensityDatabaseManager:
    def __init__(self, db_path: str = "smart_cmdb.db"):
        self.db_path = db_path
        self.conn = duckdb.connect(self.db_path)
        self.setup_tables()
        self.stored_count = 0
        self.failed_count = 0
        
    def setup_tables(self):
        self.conn.execute("DROP TABLE IF EXISTS maximum_intensity_assets")
        self.conn.execute("""
            CREATE TABLE maximum_intensity_assets (
                asset_id VARCHAR PRIMARY KEY,
                hostname VARCHAR,
                ip_address VARCHAR,
                fqdn VARCHAR,
                mac_address VARCHAR,
                infrastructure_type VARCHAR,
                operating_system VARCHAR,
                system_classification VARCHAR,
                environment VARCHAR,
                region VARCHAR,
                country VARCHAR,
                datacenter VARCHAR,
                cloud_region VARCHAR,
                business_unit VARCHAR,
                application VARCHAR,
                owner VARCHAR,
                criticality VARCHAR,
                in_chronicle BOOLEAN DEFAULT FALSE,
                in_crowdstrike BOOLEAN DEFAULT FALSE,
                in_original_cmdb BOOLEAN DEFAULT FALSE,
                in_splunk BOOLEAN DEFAULT FALSE,
                in_tanium BOOLEAN DEFAULT FALSE,
                in_dlp BOOLEAN DEFAULT FALSE,
                source_count INTEGER DEFAULT 0,
                total_rows INTEGER DEFAULT 0,
                source_tables TEXT,
                all_attributes TEXT,
                first_seen VARCHAR,
                last_updated VARCHAR,
                created_at VARCHAR DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
            )
        """)
        self.conn.commit()
        
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        try:
            asset_id = hostname.upper()
            attrs = host_data.get('all_attributes', {})
            flags = host_data.get('coverage_flags', {})
            tables = host_data.get('source_tables', set())
            
            if isinstance(tables, set):
                tables = list(tables)
                
            clean_attrs = {}
            for k, v in attrs.items():
                if isinstance(v, set):
                    clean_attrs[k] = list(v)
                elif isinstance(v, list):
                    clean_attrs[k] = v
                else:
                    clean_attrs[k] = [str(v)] if v else []
            
            def first_val(key):
                vals = clean_attrs.get(key, [])
                return str(vals[0]).strip() if vals else None
            
            existing = self.conn.execute("SELECT * FROM maximum_intensity_assets WHERE asset_id = ?", [asset_id]).fetchone()
            
            if existing:
                old_attrs = json.loads(existing[26]) if existing[26] else {}
                old_tables = json.loads(existing[25]) if existing[25] else []
                
                for k, v in clean_attrs.items():
                    if k not in old_attrs:
                        old_attrs[k] = []
                    for val in v:
                        if val and val not in old_attrs[k]:
                            old_attrs[k].append(val)
                
                new_tables = list(set(old_tables + tables))
                
                def merge_field(old_val, new_val):
                    if not old_val:
                        return new_val
                    if not new_val:
                        return old_val
                    if old_val.lower() == new_val.lower():
                        return old_val
                    if new_val not in old_val.split(','):
                        return f"{old_val},{new_val}"
                    return old_val
                
                self.conn.execute("""
                    UPDATE maximum_intensity_assets SET
                        ip_address = COALESCE(?, ip_address),
                        fqdn = COALESCE(?, fqdn),
                        mac_address = COALESCE(?, mac_address),
                        infrastructure_type = ?,
                        operating_system = COALESCE(?, operating_system),
                        system_classification = COALESCE(?, system_classification),
                        environment = COALESCE(?, environment),
                        region = COALESCE(?, region),
                        country = COALESCE(?, country),
                        datacenter = COALESCE(?, datacenter),
                        cloud_region = COALESCE(?, cloud_region),
                        business_unit = ?,
                        application = COALESCE(?, application),
                        owner = COALESCE(?, owner),
                        criticality = COALESCE(?, criticality),
                        in_chronicle = ? OR in_chronicle,
                        in_crowdstrike = ? OR in_crowdstrike,
                        in_original_cmdb = ? OR in_original_cmdb,
                        in_splunk = ? OR in_splunk,
                        in_tanium = ? OR in_tanium,
                        in_dlp = ? OR in_dlp,
                        source_count = ?,
                        total_rows = total_rows + ?,
                        source_tables = ?,
                        all_attributes = ?,
                        last_updated = ?
                    WHERE asset_id = ?
                """, [
                    first_val('ip_address'),
                    first_val('fqdn'),
                    first_val('mac_address'),
                    merge_field(existing[4] or '', first_val('infrastructure_type') or ''),
                    first_val('operating_system'),
                    first_val('system_classification'),
                    first_val('environment'),
                    first_val('region'),
                    first_val('country'),
                    first_val('datacenter'),
                    first_val('cloud_region'),
                    merge_field(existing[14] or '', first_val('business_unit') or ''),
                    first_val('application'),
                    first_val('owner'),
                    first_val('criticality'),
                    flags.get('in_chronicle', False),
                    flags.get('in_crowdstrike', False),
                    flags.get('in_original_cmdb', False),
                    flags.get('in_splunk', False),
                    flags.get('in_tanium', False),
                    flags.get('in_dlp', False),
                    len(new_tables),
                    host_data.get('total_rows', 1),
                    json.dumps(new_tables),
                    json.dumps(old_attrs),
                    datetime.now().isoformat(),
                    asset_id
                ])
            else:
                self.conn.execute("""
                    INSERT INTO maximum_intensity_assets (
                        asset_id, hostname, ip_address, fqdn, mac_address,
                        infrastructure_type, operating_system, system_classification, environment,
                        region, country, datacenter, cloud_region, business_unit, application,
                        owner, criticality, in_chronicle, in_crowdstrike, in_original_cmdb,
                        in_splunk, in_tanium, in_dlp, source_count, total_rows,
                        source_tables, all_attributes, first_seen, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    asset_id, hostname,
                    first_val('ip_address'),
                    first_val('fqdn'),
                    first_val('mac_address'),
                    first_val('infrastructure_type'),
                    first_val('operating_system'),
                    first_val('system_classification'),
                    first_val('environment'),
                    first_val('region'),
                    first_val('country'),
                    first_val('datacenter'),
                    first_val('cloud_region'),
                    first_val('business_unit'),
                    first_val('application'),
                    first_val('owner'),
                    first_val('criticality'),
                    flags.get('in_chronicle', False),
                    flags.get('in_crowdstrike', False),
                    flags.get('in_original_cmdb', False),
                    flags.get('in_splunk', False),
                    flags.get('in_tanium', False),
                    flags.get('in_dlp', False),
                    host_data.get('source_count', 1),
                    host_data.get('total_rows', 1),
                    json.dumps(tables),
                    json.dumps(clean_attrs),
                    host_data.get('first_seen', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ])
            
            self.conn.commit()
            self.stored_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Store failed for {hostname}: {e}")
            self.failed_count += 1
            return False
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        for asset_id, asset_data in assets.items():
            self.store_single_host_immediately(asset_id, asset_data)
        return self.stored_count
    
    def get_live_stats(self):
        try:
            count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            return {
                'total_hosts_in_db': count,
                'database_size_mb': os.path.getsize(self.db_path) / 1048576 if os.path.exists(self.db_path) else 0,
                'stored_count': self.stored_count,
                'failed_count': self.failed_count
            }
        except:
            return {'total_hosts_in_db': 0, 'stored_count': 0, 'failed_count': 0}
    
    def show_sample_hosts(self, limit: int = 5):
        try:
            results = self.conn.execute(f"SELECT hostname, ip_address, source_count FROM maximum_intensity_assets ORDER BY last_updated DESC LIMIT {limit}").fetchall()
            return [f"{r[0]} ({r[1]}) sources:{r[2]}" for r in results]
        except:
            return []
    
    def query_assets(self, query: str):
        try:
            return [dict(zip([d[0] for d in self.conn.description], row)) for row in self.conn.execute(query).fetchall()]
        except:
            return []
    
    def get_discrepancy_report(self):
        try:
            results = self.conn.execute("""
                SELECT hostname, ip_address, infrastructure_type, business_unit, source_count
                FROM maximum_intensity_assets 
                WHERE ip_address LIKE '%,%' OR infrastructure_type LIKE '%,%' OR business_unit LIKE '%,%'
                ORDER BY source_count DESC LIMIT 50
            """).fetchall()
            return {
                'total_discrepant_hosts': len(results),
                'discrepancies': [{'hostname': r[0], 'issues': [f"IP:{r[1]}" if ',' in (r[1] or '') else '', f"INFRA:{r[2]}" if ',' in (r[2] or '') else '', f"BU:{r[3]}" if ',' in (r[3] or '') else ''], 'source_count': r[4]} for r in results]
            }
        except:
            return {'total_discrepant_hosts': 0, 'discrepancies': []}
    
    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()

DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager

class QuantumEnhancedDatabaseManager(MaximumIntensityDatabaseManager):
    def store_comprehensive_discovery(self, quantum_discovery):
        assets_dict = {}
        for asset_id, hyper_asset in quantum_discovery.hyper_assets.items():
            assets_dict[asset_id] = {
                'hostname': hyper_asset.hostname,
                'all_attributes': {
                    'ip_address': [hyper_asset.ip] if hyper_asset.ip else [],
                    'fqdn': [hyper_asset.fqdn] if hyper_asset.fqdn else [],
                    'infrastructure_type': [hyper_asset.infrastructure_type] if hyper_asset.infrastructure_type else [],
                    'business_unit': [hyper_asset.business_unit] if hyper_asset.business_unit else [],
                    'region': [hyper_asset.region] if hyper_asset.region else []
                },
                'coverage_flags': {
                    'in_chronicle': hyper_asset.chronicle_coverage,
                    'in_crowdstrike': hyper_asset.crowdstrike_coverage,
                    'in_splunk': hyper_asset.splunk_coverage,
                    'in_original_cmdb': hyper_asset.cmdb_visibility
                },
                'source_count': len(hyper_asset.source_provenance),
                'total_rows': 1,
                'source_tables': hyper_asset.source_provenance,
                'first_seen': datetime.now().isoformat()
            }
        return self.store_maximum_intensity_discovery(assets_dict, quantum_discovery.intelligence_metrics or {})