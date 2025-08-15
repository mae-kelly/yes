import duckdb
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SmartDuckDBStorage:
    def __init__(self, db_path: str = "smart_assets.db"):
        self.db_path = os.path.abspath(db_path)
        self.conn = None
        self.init_database()
    
    def init_database(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            
            self.conn = duckdb.connect(self.db_path)
            
            self.conn.execute("""
                CREATE TABLE assets (
                    hostname VARCHAR PRIMARY KEY,
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
                    source_count INTEGER DEFAULT 1,
                    total_rows INTEGER DEFAULT 1,
                    source_tables VARCHAR,
                    all_data VARCHAR,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            logger.info(f"Database created: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database init failed: {e}")
            return False
    
    def store_host(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        if not self.conn or not hostname:
            return False
        
        try:
            clean_hostname = str(hostname).strip().upper()
            
            all_attrs = host_data.get('all_attributes', {})
            coverage = host_data.get('coverage_flags', {})
            
            def extract_value(key: str) -> str:
                values = all_attrs.get(key, [])
                if isinstance(values, (list, set)):
                    return str(list(values)[0]) if values else ""
                return str(values) if values else ""
            
            ip_addr = extract_value('ip_address')
            fqdn_val = extract_value('fqdn')
            mac_addr = extract_value('mac_address')
            infra_type = extract_value('infrastructure_type')
            os_val = extract_value('operating_system')
            sys_class = extract_value('system_classification')
            env_val = extract_value('environment')
            region_val = extract_value('region')
            country_val = extract_value('country')
            dc_val = extract_value('datacenter')
            cloud_reg = extract_value('cloud_region')
            bu_val = extract_value('business_unit')
            app_val = extract_value('application')
            owner_val = extract_value('owner')
            crit_val = extract_value('criticality')
            
            source_tables = host_data.get('source_tables', [])
            if isinstance(source_tables, set):
                source_tables = list(source_tables)
            
            existing = self.conn.execute("SELECT hostname FROM assets WHERE hostname = ?", [clean_hostname]).fetchone()
            
            if existing:
                current_data = self.conn.execute("""
                    SELECT ip_address, fqdn, mac_address, infrastructure_type, operating_system,
                           system_classification, environment, region, country, datacenter, 
                           cloud_region, business_unit, application, owner, criticality,
                           source_tables, source_count, total_rows, in_chronicle, in_crowdstrike,
                           in_original_cmdb, in_splunk, in_tanium, in_dlp
                    FROM assets WHERE hostname = ?
                """, [clean_hostname]).fetchone()
                
                def merge_field(old_val, new_val):
                    if not old_val:
                        return new_val
                    if not new_val:
                        return old_val
                    if old_val.lower() == new_val.lower():
                        return old_val
                    return f"{old_val},{new_val}"
                
                merged_ip = merge_field(current_data[0] or "", ip_addr)
                merged_fqdn = merge_field(current_data[1] or "", fqdn_val)
                merged_mac = merge_field(current_data[2] or "", mac_addr)
                merged_infra = merge_field(current_data[3] or "", infra_type)
                merged_os = merge_field(current_data[4] or "", os_val)
                merged_sys = merge_field(current_data[5] or "", sys_class)
                merged_env = merge_field(current_data[6] or "", env_val)
                merged_region = merge_field(current_data[7] or "", region_val)
                merged_country = merge_field(current_data[8] or "", country_val)
                merged_dc = merge_field(current_data[9] or "", dc_val)
                merged_cloud = merge_field(current_data[10] or "", cloud_reg)
                merged_bu = merge_field(current_data[11] or "", bu_val)
                merged_app = merge_field(current_data[12] or "", app_val)
                merged_owner = merge_field(current_data[13] or "", owner_val)
                merged_crit = merge_field(current_data[14] or "", crit_val)
                
                existing_tables = json.loads(current_data[15]) if current_data[15] else []
                merged_tables = list(set(existing_tables + source_tables))
                new_source_count = len(merged_tables)
                new_total_rows = current_data[17] + 1
                
                new_chronicle = current_data[18] or coverage.get('in_chronicle', False)
                new_cs = current_data[19] or coverage.get('in_crowdstrike', False)
                new_cmdb = current_data[20] or coverage.get('in_original_cmdb', False)
                new_splunk = current_data[21] or coverage.get('in_splunk', False)
                new_tanium = current_data[22] or coverage.get('in_tanium', False)
                new_dlp = current_data[23] or coverage.get('in_dlp', False)
                
                self.conn.execute("""
                    UPDATE assets SET
                        ip_address = ?, fqdn = ?, mac_address = ?, infrastructure_type = ?,
                        operating_system = ?, system_classification = ?, environment = ?,
                        region = ?, country = ?, datacenter = ?, cloud_region = ?,
                        business_unit = ?, application = ?, owner = ?, criticality = ?,
                        in_chronicle = ?, in_crowdstrike = ?, in_original_cmdb = ?,
                        in_splunk = ?, in_tanium = ?, in_dlp = ?,
                        source_count = ?, total_rows = ?, source_tables = ?,
                        all_data = ?, updated_at = NOW()
                    WHERE hostname = ?
                """, [
                    merged_ip or None, merged_fqdn or None, merged_mac or None, merged_infra or None,
                    merged_os or None, merged_sys or None, merged_env or None,
                    merged_region or None, merged_country or None, merged_dc or None, merged_cloud or None,
                    merged_bu or None, merged_app or None, merged_owner or None, merged_crit or None,
                    new_chronicle, new_cs, new_cmdb, new_splunk, new_tanium, new_dlp,
                    new_source_count, new_total_rows, json.dumps(merged_tables),
                    json.dumps(all_attrs, default=str), clean_hostname
                ])
                
            else:
                self.conn.execute("""
                    INSERT INTO assets (
                        hostname, ip_address, fqdn, mac_address, infrastructure_type,
                        operating_system, system_classification, environment, region, country,
                        datacenter, cloud_region, business_unit, application, owner, criticality,
                        in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                        source_count, total_rows, source_tables, all_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    clean_hostname, ip_addr or None, fqdn_val or None, mac_addr or None, infra_type or None,
                    os_val or None, sys_class or None, env_val or None, region_val or None, country_val or None,
                    dc_val or None, cloud_reg or None, bu_val or None, app_val or None, owner_val or None, crit_val or None,
                    coverage.get('in_chronicle', False), coverage.get('in_crowdstrike', False),
                    coverage.get('in_original_cmdb', False), coverage.get('in_splunk', False),
                    coverage.get('in_tanium', False), coverage.get('in_dlp', False),
                    len(source_tables), 1, json.dumps(source_tables), json.dumps(all_attrs, default=str)
                ])
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Store failed for {hostname}: {e}")
            return False
    
    def get_count(self) -> int:
        try:
            return self.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        except:
            return 0
    
    def get_sample(self, limit: int = 5) -> List[Dict]:
        try:
            results = self.conn.execute(f"""
                SELECT hostname, ip_address, infrastructure_type, business_unit, source_count
                FROM assets ORDER BY updated_at DESC LIMIT {limit}
            """).fetchall()
            return [{'hostname': r[0], 'ip': r[1], 'infra': r[2], 'bu': r[3], 'sources': r[4]} for r in results]
        except:
            return []
    
    def close(self):
        if self.conn:
            self.conn.close()

class MaximumIntensityDatabaseManager:
    def __init__(self, db_path: str):
        self.storage = SmartDuckDBStorage(db_path)
        self.stored_count = 0
        self.failed_count = 0
    
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        success = self.storage.store_host(hostname, host_data)
        if success:
            self.stored_count += 1
        else:
            self.failed_count += 1
        return success
    
    def get_live_stats(self) -> Dict[str, Any]:
        return {
            'total_hosts_in_db': self.storage.get_count(),
            'stored_count': self.stored_count,
            'failed_count': self.failed_count
        }
    
    def show_sample_hosts(self, limit: int = 5) -> List[str]:
        samples = self.storage.get_sample(limit)
        return [f"{s['hostname']} [{s['ip']}] ({s['sources']} sources)" for s in samples]
    
    def close(self):
        self.storage.close()

DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager