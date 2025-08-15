import duckdb
import json
import logging
import os
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MaximumIntensityDatabaseManager:
    def __init__(self, db_path: str = "smart_cmdb.db"):
        self.db_path = str(db_path)
        self.conn = None
        self.stored_count = 0
        self._setup()
    
    def _setup(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.conn = duckdb.connect(self.db_path)
            self.conn.execute("""
                CREATE TABLE maximum_intensity_assets (
                    asset_id VARCHAR PRIMARY KEY,
                    hostname VARCHAR NOT NULL,
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
                    in_chronicle BOOLEAN DEFAULT false,
                    in_crowdstrike BOOLEAN DEFAULT false,
                    in_original_cmdb BOOLEAN DEFAULT false,
                    in_splunk BOOLEAN DEFAULT false,
                    in_tanium BOOLEAN DEFAULT false,
                    in_dlp BOOLEAN DEFAULT false,
                    source_count INTEGER DEFAULT 0,
                    total_rows INTEGER DEFAULT 0,
                    source_tables VARCHAR,
                    all_attributes VARCHAR,
                    first_seen VARCHAR,
                    last_updated VARCHAR
                )
            """)
            self.conn.commit()
            logger.info(f"Database created: {self.db_path}")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
    
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        try:
            asset_id = str(hostname).upper()
            
            all_attrs = host_data.get('all_attributes', {})
            coverage = host_data.get('coverage_flags', {})
            source_tables = host_data.get('source_tables', set())
            source_count = int(host_data.get('source_count', 0))
            total_rows = int(host_data.get('total_rows', 0))
            first_seen = str(host_data.get('first_seen', datetime.now().isoformat()))
            last_updated = str(datetime.now().isoformat())
            
            if isinstance(source_tables, set):
                source_tables_str = json.dumps(list(source_tables))
            else:
                source_tables_str = json.dumps(list(source_tables) if source_tables else [])
            
            attrs_dict = {}
            for key, value in all_attrs.items():
                if isinstance(value, set):
                    attrs_dict[str(key)] = list(value)
                elif isinstance(value, list):
                    attrs_dict[str(key)] = value
                else:
                    attrs_dict[str(key)] = [str(value)] if value else []
            
            all_attrs_str = json.dumps(attrs_dict)
            
            def get_val(attr_key: str) -> str:
                vals = attrs_dict.get(str(attr_key), [])
                return str(vals[0]) if vals else ""
            
            ip_address = get_val('ip_address')
            fqdn = get_val('fqdn')
            mac_address = get_val('mac_address')
            infrastructure_type = get_val('infrastructure_type')
            operating_system = get_val('operating_system')
            system_classification = get_val('system_classification')
            environment = get_val('environment')
            region = get_val('region')
            country = get_val('country')
            datacenter = get_val('datacenter')
            cloud_region = get_val('cloud_region')
            business_unit = get_val('business_unit')
            application = get_val('application')
            owner = get_val('owner')
            criticality = get_val('criticality')
            
            in_chronicle = bool(coverage.get('in_chronicle', False))
            in_crowdstrike = bool(coverage.get('in_crowdstrike', False))
            in_original_cmdb = bool(coverage.get('in_original_cmdb', False))
            in_splunk = bool(coverage.get('in_splunk', False))
            in_tanium = bool(coverage.get('in_tanium', False))
            in_dlp = bool(coverage.get('in_dlp', False))
            
            existing = self.conn.execute("SELECT asset_id FROM maximum_intensity_assets WHERE asset_id = ?", [asset_id]).fetchone()
            
            if existing:
                old_data = self.conn.execute("""
                    SELECT ip_address, fqdn, mac_address, infrastructure_type, operating_system,
                           system_classification, environment, region, country, datacenter, cloud_region,
                           business_unit, application, owner, criticality, source_tables, all_attributes,
                           in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                           source_count, total_rows
                    FROM maximum_intensity_assets WHERE asset_id = ?
                """, [asset_id]).fetchone()
                
                if old_data:
                    (old_ip, old_fqdn, old_mac, old_infra, old_os, old_sys_class, old_env, old_region, 
                     old_country, old_dc, old_cloud_region, old_bu, old_app, old_owner, old_crit,
                     old_source_tables_str, old_attrs_str, old_chronicle, old_cs, old_cmdb, old_splunk,
                     old_tanium, old_dlp, old_source_count, old_total_rows) = old_data
                    
                    def merge_val(old_val, new_val):
                        if not old_val:
                            return str(new_val) if new_val else ""
                        if not new_val:
                            return str(old_val)
                        old_str = str(old_val)
                        new_str = str(new_val)
                        if old_str.lower() == new_str.lower():
                            return old_str
                        if new_str in old_str:
                            return old_str
                        return f"{old_str},{new_str}"
                    
                    merged_ip = merge_val(old_ip, ip_address)
                    merged_fqdn = merge_val(old_fqdn, fqdn)
                    merged_mac = merge_val(old_mac, mac_address)
                    merged_infra = merge_val(old_infra, infrastructure_type)
                    merged_os = merge_val(old_os, operating_system)
                    merged_sys_class = merge_val(old_sys_class, system_classification)
                    merged_env = merge_val(old_env, environment)
                    merged_region = merge_val(old_region, region)
                    merged_country = merge_val(old_country, country)
                    merged_dc = merge_val(old_dc, datacenter)
                    merged_cloud_region = merge_val(old_cloud_region, cloud_region)
                    merged_bu = merge_val(old_bu, business_unit)
                    merged_app = merge_val(old_app, application)
                    merged_owner = merge_val(old_owner, owner)
                    merged_crit = merge_val(old_crit, criticality)
                    
                    try:
                        old_tables = json.loads(old_source_tables_str) if old_source_tables_str else []
                        new_tables = json.loads(source_tables_str) if source_tables_str else []
                        merged_tables = list(set(old_tables + new_tables))
                        merged_source_tables_str = json.dumps(merged_tables)
                        merged_source_count = len(merged_tables)
                    except:
                        merged_source_tables_str = source_tables_str
                        merged_source_count = source_count
                    
                    try:
                        old_attrs = json.loads(old_attrs_str) if old_attrs_str else {}
                        new_attrs = json.loads(all_attrs_str) if all_attrs_str else {}
                        for key, values in new_attrs.items():
                            if key not in old_attrs:
                                old_attrs[key] = []
                            if not isinstance(old_attrs[key], list):
                                old_attrs[key] = [old_attrs[key]] if old_attrs[key] else []
                            for v in values:
                                if str(v) not in old_attrs[key]:
                                    old_attrs[key].append(str(v))
                        merged_attrs_str = json.dumps(old_attrs)
                    except:
                        merged_attrs_str = all_attrs_str
                    
                    merged_chronicle = bool(old_chronicle or in_chronicle)
                    merged_cs = bool(old_cs or in_crowdstrike)
                    merged_cmdb = bool(old_cmdb or in_original_cmdb)
                    merged_splunk = bool(old_splunk or in_splunk)
                    merged_tanium = bool(old_tanium or in_tanium)
                    merged_dlp = bool(old_dlp or in_dlp)
                    merged_total_rows = int(old_total_rows) + int(total_rows)
                    
                    self.conn.execute("""
                        UPDATE maximum_intensity_assets SET
                            ip_address = ?, fqdn = ?, mac_address = ?, infrastructure_type = ?,
                            operating_system = ?, system_classification = ?, environment = ?,
                            region = ?, country = ?, datacenter = ?, cloud_region = ?,
                            business_unit = ?, application = ?, owner = ?, criticality = ?,
                            in_chronicle = ?, in_crowdstrike = ?, in_original_cmdb = ?,
                            in_splunk = ?, in_tanium = ?, in_dlp = ?,
                            source_count = ?, total_rows = ?, source_tables = ?,
                            all_attributes = ?, last_updated = ?
                        WHERE asset_id = ?
                    """, [
                        merged_ip, merged_fqdn, merged_mac, merged_infra, merged_os, merged_sys_class,
                        merged_env, merged_region, merged_country, merged_dc, merged_cloud_region,
                        merged_bu, merged_app, merged_owner, merged_crit,
                        merged_chronicle, merged_cs, merged_cmdb, merged_splunk, merged_tanium, merged_dlp,
                        merged_source_count, merged_total_rows, merged_source_tables_str,
                        merged_attrs_str, last_updated, asset_id
                    ])
            else:
                self.conn.execute("""
                    INSERT INTO maximum_intensity_assets (
                        asset_id, hostname, ip_address, fqdn, mac_address,
                        infrastructure_type, operating_system, system_classification, environment,
                        region, country, datacenter, cloud_region,
                        business_unit, application, owner, criticality,
                        in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                        source_count, total_rows, source_tables, all_attributes, first_seen, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    asset_id, str(hostname), ip_address, fqdn, mac_address,
                    infrastructure_type, operating_system, system_classification, environment,
                    region, country, datacenter, cloud_region,
                    business_unit, application, owner, criticality,
                    in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                    source_count, total_rows, source_tables_str, all_attrs_str, first_seen, last_updated
                ])
            
            self.conn.commit()
            self.stored_count += 1
            logger.info(f"STORED: {hostname} (total: {self.stored_count})")
            return True
            
        except Exception as e:
            logger.error(f"STORE FAILED {hostname}: {e}")
            try:
                self.conn.rollback()
            except:
                pass
            return False
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        count = 0
        for asset_id, asset_data in assets.items():
            if self.store_single_host_immediately(asset_id, asset_data):
                count += 1
        return count
    
    def get_live_stats(self) -> Dict[str, Any]:
        try:
            total_count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            return {
                'total_hosts_in_db': int(total_count),
                'database_size_mb': float(os.path.getsize(self.db_path) / (1024 * 1024)) if os.path.exists(self.db_path) else 0.0,
                'stored_count': int(self.stored_count)
            }
        except Exception as e:
            return {'error': str(e), 'total_hosts_in_db': 0}
    
    def show_sample_hosts(self, limit: int = 5) -> List[str]:
        try:
            results = self.conn.execute(f"SELECT hostname, ip_address, source_count FROM maximum_intensity_assets ORDER BY last_updated DESC LIMIT {int(limit)}").fetchall()
            return [f"{row[0]} [{row[1]}] ({row[2]} sources)" for row in results]
        except:
            return []
    
    def query_assets(self, query: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except:
            return []
    
    def close(self):
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                logger.info(f"Database closed: {self.stored_count} stored")
            except:
                pass

DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager
QuantumEnhancedDatabaseManager = MaximumIntensityDatabaseManager