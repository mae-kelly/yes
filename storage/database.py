# storage/database.py
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
        self.conn = duckdb.connect(self.db_path)
        self.conn.execute("PRAGMA memory_limit='8GB'")
        self.conn.execute("PRAGMA threads=16")
        self._create_tables()
        logger.info(f"Database ready: {self.db_path}")
    
    def _create_tables(self):
        self.conn.execute("DROP TABLE IF EXISTS maximum_intensity_assets")
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
                last_updated VARCHAR DEFAULT CURRENT_TIMESTAMP,
                created_at VARCHAR DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        try:
            asset_id = str(hostname).upper()
            
            all_attributes = host_data.get('all_attributes', {})
            coverage_flags = host_data.get('coverage_flags', {})
            source_tables = host_data.get('source_tables', set())
            source_count = int(host_data.get('source_count', 0))
            total_rows = int(host_data.get('total_rows', 0))
            first_seen = str(host_data.get('first_seen', datetime.now().isoformat()))
            last_updated = str(host_data.get('last_updated', datetime.now().isoformat()))
            
            if isinstance(source_tables, set):
                source_tables_json = json.dumps(list(source_tables))
            else:
                source_tables_json = json.dumps(list(source_tables))
            
            all_attributes_json = json.dumps(self._convert_attributes(all_attributes))
            
            def get_val(key: str) -> str:
                vals = all_attributes.get(key, [])
                if isinstance(vals, set):
                    vals = list(vals)
                if isinstance(vals, list) and len(vals) > 0:
                    return str(vals[0])
                return ""
            
            ip_address = str(get_val('ip_address'))
            fqdn = str(get_val('fqdn'))
            mac_address = str(get_val('mac_address'))
            infrastructure_type = str(get_val('infrastructure_type'))
            operating_system = str(get_val('operating_system'))
            system_classification = str(get_val('system_classification'))
            environment = str(get_val('environment'))
            region = str(get_val('region'))
            country = str(get_val('country'))
            datacenter = str(get_val('datacenter'))
            cloud_region = str(get_val('cloud_region'))
            business_unit = str(get_val('business_unit'))
            application = str(get_val('application'))
            owner = str(get_val('owner'))
            criticality = str(get_val('criticality'))
            
            in_chronicle = bool(coverage_flags.get('in_chronicle', False))
            in_crowdstrike = bool(coverage_flags.get('in_crowdstrike', False))
            in_original_cmdb = bool(coverage_flags.get('in_original_cmdb', False))
            in_splunk = bool(coverage_flags.get('in_splunk', False))
            in_tanium = bool(coverage_flags.get('in_tanium', False))
            in_dlp = bool(coverage_flags.get('in_dlp', False))
            
            check_sql = "SELECT asset_id FROM maximum_intensity_assets WHERE asset_id = ?"
            existing = self.conn.execute(check_sql, [asset_id]).fetchone()
            
            if existing:
                existing_data = self.conn.execute("""
                    SELECT ip_address, fqdn, mac_address, infrastructure_type, operating_system,
                           system_classification, environment, region, country, datacenter, 
                           cloud_region, business_unit, application, owner, criticality,
                           source_tables, all_attributes, source_count, total_rows,
                           in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp
                    FROM maximum_intensity_assets WHERE asset_id = ?
                """, [asset_id]).fetchone()
                
                if existing_data:
                    (e_ip, e_fqdn, e_mac, e_infra, e_os, e_sys, e_env, e_region, e_country, 
                     e_dc, e_cloud, e_bu, e_app, e_owner, e_crit, e_tables, e_attrs, 
                     e_source_count, e_total_rows, e_chron, e_cs, e_cmdb, e_splunk, e_tan, e_dlp) = existing_data
                    
                    merged_ip = self._merge_values(str(e_ip or ""), ip_address)
                    merged_fqdn = self._merge_values(str(e_fqdn or ""), fqdn)
                    merged_mac = self._merge_values(str(e_mac or ""), mac_address)
                    merged_infra = self._merge_values(str(e_infra or ""), infrastructure_type)
                    merged_os = self._merge_values(str(e_os or ""), operating_system)
                    merged_sys = self._merge_values(str(e_sys or ""), system_classification)
                    merged_env = self._merge_values(str(e_env or ""), environment)
                    merged_region = self._merge_values(str(e_region or ""), region)
                    merged_country = self._merge_values(str(e_country or ""), country)
                    merged_dc = self._merge_values(str(e_dc or ""), datacenter)
                    merged_cloud = self._merge_values(str(e_cloud or ""), cloud_region)
                    merged_bu = self._merge_values(str(e_bu or ""), business_unit)
                    merged_app = self._merge_values(str(e_app or ""), application)
                    merged_owner = self._merge_values(str(e_owner or ""), owner)
                    merged_crit = self._merge_values(str(e_crit or ""), criticality)
                    
                    try:
                        e_tables_list = json.loads(str(e_tables)) if e_tables else []
                    except:
                        e_tables_list = []
                    
                    try:
                        new_tables_list = json.loads(source_tables_json)
                    except:
                        new_tables_list = []
                    
                    merged_tables = list(set(e_tables_list + new_tables_list))
                    merged_tables_json = json.dumps(merged_tables)
                    
                    try:
                        e_attrs_dict = json.loads(str(e_attrs)) if e_attrs else {}
                    except:
                        e_attrs_dict = {}
                    
                    try:
                        new_attrs_dict = json.loads(all_attributes_json)
                    except:
                        new_attrs_dict = {}
                    
                    merged_attrs = self._merge_attributes(e_attrs_dict, new_attrs_dict)
                    merged_attrs_json = json.dumps(merged_attrs)
                    
                    new_source_count = int(len(merged_tables))
                    new_total_rows = int(e_total_rows) + int(total_rows)
                    
                    new_chronicle = bool(e_chron) or bool(in_chronicle)
                    new_crowdstrike = bool(e_cs) or bool(in_crowdstrike)
                    new_cmdb = bool(e_cmdb) or bool(in_original_cmdb)
                    new_splunk = bool(e_splunk) or bool(in_splunk)
                    new_tanium = bool(e_tan) or bool(in_tanium)
                    new_dlp = bool(e_dlp) or bool(in_dlp)
                    
                    update_sql = """
                        UPDATE maximum_intensity_assets SET
                            hostname = ?, ip_address = ?, fqdn = ?, mac_address = ?,
                            infrastructure_type = ?, operating_system = ?, system_classification = ?,
                            environment = ?, region = ?, country = ?, datacenter = ?, cloud_region = ?,
                            business_unit = ?, application = ?, owner = ?, criticality = ?,
                            in_chronicle = ?, in_crowdstrike = ?, in_original_cmdb = ?,
                            in_splunk = ?, in_tanium = ?, in_dlp = ?,
                            source_count = ?, total_rows = ?, source_tables = ?,
                            all_attributes = ?, last_updated = ?
                        WHERE asset_id = ?
                    """
                    
                    self.conn.execute(update_sql, [
                        str(hostname), merged_ip, merged_fqdn, merged_mac,
                        merged_infra, merged_os, merged_sys, merged_env, merged_region,
                        merged_country, merged_dc, merged_cloud, merged_bu, merged_app,
                        merged_owner, merged_crit, new_chronicle, new_crowdstrike, new_cmdb,
                        new_splunk, new_tanium, new_dlp, new_source_count, new_total_rows,
                        merged_tables_json, merged_attrs_json, str(last_updated), asset_id
                    ])
            else:
                insert_sql = """
                    INSERT INTO maximum_intensity_assets (
                        asset_id, hostname, ip_address, fqdn, mac_address,
                        infrastructure_type, operating_system, system_classification, environment,
                        region, country, datacenter, cloud_region, business_unit, application,
                        owner, criticality, in_chronicle, in_crowdstrike, in_original_cmdb,
                        in_splunk, in_tanium, in_dlp, source_count, total_rows,
                        source_tables, all_attributes, first_seen, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                self.conn.execute(insert_sql, [
                    asset_id, str(hostname), ip_address, fqdn, mac_address,
                    infrastructure_type, operating_system, system_classification, environment,
                    region, country, datacenter, cloud_region, business_unit, application,
                    owner, criticality, in_chronicle, in_crowdstrike, in_original_cmdb,
                    in_splunk, in_tanium, in_dlp, source_count, total_rows,
                    source_tables_json, all_attributes_json, first_seen, last_updated
                ])
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Storage failed for {hostname}: {e}")
            try:
                self.conn.rollback()
            except:
                pass
            return False
    
    def _convert_attributes(self, attrs: Dict[str, Any]) -> Dict[str, List[str]]:
        result = {}
        for key, value in attrs.items():
            if isinstance(value, set):
                result[key] = [str(x) for x in value if x]
            elif isinstance(value, list):
                result[key] = [str(x) for x in value if x]
            elif value:
                result[key] = [str(value)]
            else:
                result[key] = []
        return result
    
    def _merge_values(self, existing: str, new: str) -> str:
        existing = str(existing).strip()
        new = str(new).strip()
        
        if not existing:
            return new
        if not new:
            return existing
        if existing.lower() == new.lower():
            return existing
        
        existing_parts = [x.strip() for x in existing.split(',')]
        for part in existing_parts:
            if part.lower() == new.lower():
                return existing
        
        return f"{existing},{new}"
    
    def _merge_attributes(self, existing: Dict[str, List[str]], new: Dict[str, List[str]]) -> Dict[str, List[str]]:
        result = existing.copy()
        for key, values in new.items():
            if key not in result:
                result[key] = []
            
            if not isinstance(result[key], list):
                result[key] = [str(result[key])] if result[key] else []
            
            for val in values:
                val_str = str(val).strip()
                if val_str and val_str not in result[key]:
                    result[key].append(val_str)
        
        return result
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        stored = 0
        for asset_id, asset_data in assets.items():
            if self.store_single_host_immediately(asset_id, asset_data):
                stored += 1
        
        count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
        logger.info(f"Stored {stored} assets, total in DB: {count}")
        return int(count)
    
    def get_live_stats(self) -> Dict[str, Any]:
        try:
            count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            
            ip_conflicts = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets WHERE ip_address LIKE '%,%'").fetchone()[0]
            infra_conflicts = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets WHERE infrastructure_type LIKE '%,%'").fetchone()[0]
            bu_conflicts = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets WHERE business_unit LIKE '%,%'").fetchone()[0]
            
            return {
                'total_hosts_in_db': int(count),
                'database_size_mb': float(size_mb),
                'ip_conflicts': int(ip_conflicts),
                'infrastructure_conflicts': int(infra_conflicts),
                'business_unit_conflicts': int(bu_conflicts)
            }
        except Exception as e:
            return {'error': str(e), 'total_hosts_in_db': 0}
    
    def show_sample_hosts(self, limit: int = 5) -> List[str]:
        try:
            results = self.conn.execute(f"""
                SELECT hostname, ip_address, infrastructure_type, business_unit, 
                       in_chronicle, in_crowdstrike, source_count
                FROM maximum_intensity_assets 
                ORDER BY last_updated DESC 
                LIMIT {limit}
            """).fetchall()
            
            hosts = []
            for row in results:
                hostname, ip, infra, bu, chron, cs, sources = row
                
                conflicts = []
                if ip and ',' in str(ip):
                    conflicts.append(f"IP_CONFLICT")
                if infra and ',' in str(infra):
                    conflicts.append(f"INFRA_CONFLICT")
                if bu and ',' in str(bu):
                    conflicts.append(f"BU_CONFLICT")
                
                coverage = []
                if chron:
                    coverage.append("CHRON")
                if cs:
                    coverage.append("CS")
                
                info = f"{hostname}(src:{sources})"
                if ip and ',' not in str(ip):
                    info += f"[{ip}]"
                if coverage:
                    info += f"{{{','.join(coverage)}}}"
                if conflicts:
                    info += f"⚠️{{{','.join(conflicts)}}}"
                
                hosts.append(info)
            
            return hosts
        except Exception as e:
            logger.error(f"Sample query failed: {e}")
            return []
    
    def query_assets(self, query: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def get_discrepancy_report(self) -> Dict[str, Any]:
        try:
            conflicts = self.conn.execute("""
                SELECT hostname, ip_address, infrastructure_type, business_unit, source_count
                FROM maximum_intensity_assets 
                WHERE ip_address LIKE '%,%' 
                   OR infrastructure_type LIKE '%,%'
                   OR business_unit LIKE '%,%'
                ORDER BY source_count DESC
                LIMIT 50
            """).fetchall()
            
            report = []
            for row in conflicts:
                hostname, ip, infra, bu, sources = row
                issues = []
                if ip and ',' in str(ip):
                    issues.append(f"IP:{ip}")
                if infra and ',' in str(infra):
                    issues.append(f"INFRA:{infra}")
                if bu and ',' in str(bu):
                    issues.append(f"BU:{bu}")
                
                report.append({
                    'hostname': str(hostname),
                    'source_count': int(sources),
                    'conflicts': issues
                })
            
            return {
                'total_conflicts': len(report),
                'conflicts': report
            }
        except Exception as e:
            return {'error': str(e)}
    
    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()

DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager

class QuantumEnhancedDatabaseManager(MaximumIntensityDatabaseManager):
    def store_comprehensive_discovery(self, quantum_discovery) -> int:
        assets_dict = {}
        for asset_id, hyper_asset in quantum_discovery.hyper_assets.items():
            assets_dict[asset_id] = {
                'hostname': str(hyper_asset.hostname),
                'all_attributes': {
                    'ip_address': [str(hyper_asset.ip)] if hyper_asset.ip else [],
                    'fqdn': [str(hyper_asset.fqdn)] if hyper_asset.fqdn else [],
                    'infrastructure_type': [str(hyper_asset.infrastructure_type)] if hyper_asset.infrastructure_type else [],
                    'business_unit': [str(hyper_asset.business_unit)] if hyper_asset.business_unit else [],
                    'region': [str(hyper_asset.region)] if hyper_asset.region else []
                },
                'coverage_flags': {
                    'in_chronicle': bool(hyper_asset.chronicle_coverage),
                    'in_crowdstrike': bool(hyper_asset.crowdstrike_coverage),
                    'in_splunk': bool(hyper_asset.splunk_coverage),
                    'in_original_cmdb': bool(hyper_asset.cmdb_visibility)
                },
                'source_count': int(len(hyper_asset.source_provenance)),
                'total_rows': int(1),
                'source_tables': list(hyper_asset.source_provenance),
                'first_seen': str(datetime.now().isoformat())
            }
        
        stats = quantum_discovery.intelligence_metrics or {}
        return self.store_maximum_intensity_discovery(assets_dict, stats)