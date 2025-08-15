import duckdb
import json
import logging
import time
import os
from typing import Dict, List, Any
from datetime import datetime
from core.types import HyperAsset, QuantumDiscovery

logger = logging.getLogger(__name__)

class MaximumIntensityDatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._connect_and_setup()
    
    def _connect_and_setup(self):
        try:
            self.conn = duckdb.connect(self.db_path)
            self.conn.execute("PRAGMA memory_limit='4GB'")
            self.conn.execute("PRAGMA threads=8")
            logger.info(f"Database connection established: {self.db_path}")
            self._setup_simple_schema()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def _setup_simple_schema(self):
        try:
            self.conn.execute("DROP TABLE IF EXISTS maximum_intensity_assets")
            self.conn.execute("DROP TABLE IF EXISTS discovery_metadata")
            
            logger.info("Creating simple asset schema")
            
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
                    in_chronicle BOOLEAN DEFAULT FALSE,
                    in_crowdstrike BOOLEAN DEFAULT FALSE,
                    in_original_cmdb BOOLEAN DEFAULT FALSE,
                    in_splunk BOOLEAN DEFAULT FALSE,
                    in_tanium BOOLEAN DEFAULT FALSE,
                    in_dlp BOOLEAN DEFAULT FALSE,
                    source_count INTEGER DEFAULT 0,
                    total_rows INTEGER DEFAULT 0,
                    source_tables JSON,
                    all_attributes JSON,
                    first_seen TIMESTAMP,
                    last_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE discovery_metadata (
                    id VARCHAR PRIMARY KEY,
                    discovery_type VARCHAR,
                    total_hosts_discovered INTEGER,
                    total_rows_processed INTEGER,
                    processing_time_minutes DOUBLE,
                    stats JSON,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            self.conn.commit()
            logger.info("Simple schema created successfully")
            
            tables = self.conn.execute("SHOW TABLES").fetchall()
            logger.info(f"Verified tables: {[table[0] for table in tables]}")
            
            self.test_insert()
            
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise
    
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]):
        try:
            all_attrs = host_data.get('all_attributes', {})
            coverage = host_data.get('coverage_flags', {})
            
            def get_first_value(attr_key: str, default: str = '') -> str:
                values = all_attrs.get(attr_key, set())
                if isinstance(values, (list, set)) and values:
                    return str(list(values)[0])
                elif values:
                    return str(values)
                return default
            
            insert_sql = """
                INSERT OR REPLACE INTO maximum_intensity_assets (
                    asset_id, hostname, ip_address, fqdn, mac_address,
                    infrastructure_type, operating_system, system_classification, environment,
                    region, country, datacenter, cloud_region,
                    business_unit, application, owner, criticality,
                    in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                    source_count, total_rows, source_tables, all_attributes, first_seen, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                hostname,
                host_data.get('hostname', hostname),
                get_first_value('ip_address'),
                get_first_value('fqdn'),
                get_first_value('mac_address'),
                get_first_value('infrastructure_type'),
                get_first_value('operating_system'),
                get_first_value('system_classification'),
                get_first_value('environment'),
                get_first_value('region'),
                get_first_value('country'),
                get_first_value('datacenter'),
                get_first_value('cloud_region'),
                get_first_value('business_unit'),
                get_first_value('application'),
                get_first_value('owner'),
                get_first_value('criticality'),
                coverage.get('in_chronicle', False),
                coverage.get('in_crowdstrike', False),
                coverage.get('in_original_cmdb', False),
                coverage.get('in_splunk', False),
                coverage.get('in_tanium', False),
                coverage.get('in_dlp', False),
                host_data.get('source_count', 0),
                host_data.get('total_rows', 0),
                json.dumps(list(host_data.get('source_tables', [])), default=list),
                json.dumps(all_attrs, default=list),
                host_data.get('first_seen'),
                datetime.now().isoformat()
            )
            
            logger.debug(f"Executing insert with {len(values)} values for {len(insert_sql.count('?'))} placeholders")
            self.conn.execute(insert_sql, values)
            self.conn.commit()
            logger.info(f"Successfully stored {hostname} to database")
            return True
            
        except Exception as e:
            logger.error(f"Host storage failed for {hostname}: {e}")
            logger.error(f"Values count: {len(values) if 'values' in locals() else 'undefined'}")
            return False
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        if not assets:
            logger.warning("No assets to store")
            return 0
        
        logger.info(f"Storing {len(assets):,} assets to database")
        
        stored_count = 0
        batch_size = 1000
        current_batch = []
        
        try:
            self.conn.begin()
            
            for asset_id, asset_data in assets.items():
                try:
                    all_attrs = asset_data.get('all_attributes', {})
                    coverage = asset_data.get('coverage_flags', {})
                    
                    def get_first_value(attr_key: str, default: str = '') -> str:
                        values = all_attrs.get(attr_key, set())
                        if isinstance(values, (list, set)) and values:
                            return str(list(values)[0])
                        elif values:
                            return str(values)
                        return default
                    
                    asset_row = {
                        'asset_id': asset_id,
                        'hostname': asset_data.get('hostname', asset_id),
                        'ip_address': get_first_value('ip_address'),
                        'fqdn': get_first_value('fqdn'),
                        'mac_address': get_first_value('mac_address'),
                        'infrastructure_type': get_first_value('infrastructure_type'),
                        'operating_system': get_first_value('operating_system'),
                        'system_classification': get_first_value('system_classification'),
                        'environment': get_first_value('environment'),
                        'region': get_first_value('region'),
                        'country': get_first_value('country'),
                        'datacenter': get_first_value('datacenter'),
                        'cloud_region': get_first_value('cloud_region'),
                        'business_unit': get_first_value('business_unit'),
                        'application': get_first_value('application'),
                        'owner': get_first_value('owner'),
                        'criticality': get_first_value('criticality'),
                        'in_chronicle': coverage.get('in_chronicle', False),
                        'in_crowdstrike': coverage.get('in_crowdstrike', False),
                        'in_original_cmdb': coverage.get('in_original_cmdb', False),
                        'in_splunk': coverage.get('in_splunk', False),
                        'in_tanium': coverage.get('in_tanium', False),
                        'in_dlp': coverage.get('in_dlp', False),
                        'source_count': asset_data.get('source_count', 0),
                        'total_rows': asset_data.get('total_rows', 0),
                        'source_tables': json.dumps(asset_data.get('source_tables', [])),
                        'all_attributes': json.dumps(all_attrs, default=list),
                        'first_seen': asset_data.get('first_seen'),
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    current_batch.append(asset_row)
                    
                    if len(current_batch) >= batch_size:
                        batch_stored = self._insert_batch(current_batch)
                        stored_count += batch_stored
                        current_batch = []
                        logger.info(f"Batch stored: {stored_count:,} assets so far")
                    
                except Exception as e:
                    logger.error(f"Failed to prepare asset {asset_id}: {e}")
                    continue
            
            if current_batch:
                batch_stored = self._insert_batch(current_batch)
                stored_count += batch_stored
            
            self._store_discovery_metadata(stats)
            self.conn.commit()
            
            actual_count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            
            logger.info("Database storage complete")
            logger.info(f"Assets processed: {stored_count:,}")
            logger.info(f"Verified in database: {actual_count:,}")
            
            return actual_count
            
        except Exception as e:
            logger.error(f"Database storage transaction failed: {e}")
            try:
                self.conn.rollback()
            except:
                pass
            raise
        finally:
            pass
    
    def _insert_batch(self, batch: List[Dict[str, Any]]) -> int:
        try:
            insert_sql = """
                INSERT INTO maximum_intensity_assets (
                    asset_id, hostname, ip_address, fqdn, mac_address,
                    infrastructure_type, operating_system, system_classification, environment,
                    region, country, datacenter, cloud_region,
                    business_unit, application, owner, criticality,
                    in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                    source_count, total_rows, source_tables, all_attributes, first_seen, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            batch_data = []
            for asset in batch:
                row_tuple = (
                    asset['asset_id'], asset['hostname'], asset['ip_address'], 
                    asset['fqdn'], asset['mac_address'], asset['infrastructure_type'],
                    asset['operating_system'], asset['system_classification'], asset['environment'],
                    asset['region'], asset['country'], asset['datacenter'], asset['cloud_region'],
                    asset['business_unit'], asset['application'], asset['owner'], asset['criticality'],
                    asset['in_chronicle'], asset['in_crowdstrike'], asset['in_original_cmdb'],
                    asset['in_splunk'], asset['in_tanium'], asset['in_dlp'],
                    asset['source_count'], asset['total_rows'], asset['source_tables'], 
                    asset['all_attributes'], asset['first_seen'], asset['last_updated']
                )
                batch_data.append(row_tuple)
            
            self.conn.executemany(insert_sql, batch_data)
            return len(batch)
            
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return 0
    
    def _store_discovery_metadata(self, stats: Dict[str, Any]):
        try:
            discovery_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.conn.execute("""
                INSERT INTO discovery_metadata (
                    id, discovery_type, total_hosts_discovered, total_rows_processed,
                    processing_time_minutes, stats
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                discovery_id,
                "maximum_intensity_discovery",
                stats.get('total_unique_hosts', 0),
                stats.get('total_rows_processed', 0),
                stats.get('processing_time_minutes', 0),
                json.dumps(stats)
            ])
            
            logger.info(f"Discovery metadata stored: {discovery_id}")
            
        except Exception as e:
            logger.error(f"Metadata storage failed: {e}")
    
    def query_assets(self, query: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def get_live_stats(self) -> Dict[str, Any]:
        try:
            total_count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            
            return {
                'total_hosts_in_db': total_count,
                'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            }
            
        except Exception as e:
            return {'error': str(e), 'total_hosts_in_db': 0}
    
    def show_sample_hosts(self, limit: int = 5) -> List[str]:
        try:
            results = self.conn.execute(f"""
                SELECT hostname, ip_address, infrastructure_type, in_chronicle, in_crowdstrike
                FROM maximum_intensity_assets 
                ORDER BY created_at DESC 
                LIMIT {limit}
            """).fetchall()
            
            sample_hosts = []
            for row in results:
                hostname, ip, infra, chronicle, cs = row
                coverage_info = []
                if chronicle:
                    coverage_info.append("Chronicle")
                if cs:
                    coverage_info.append("CrowdStrike")
                
                coverage_str = f" [{', '.join(coverage_info)}]" if coverage_info else ""
                host_info = f"{hostname}"
                if ip:
                    host_info += f" ({ip})"
                if infra:
                    host_info += f" [{infra}]"
                host_info += coverage_str
                
                sample_hosts.append(host_info)
            
            return sample_hosts
            
        except Exception as e:
            logger.error(f"Sample hosts query failed: {e}")
            return []
    
    def test_insert(self):
        try:
            logger.info("Testing database insert functionality")
            test_host_data = {
                'hostname': 'TEST-SERVER-01',
                'all_attributes': {
                    'ip_address': {'192.168.1.100'},
                    'infrastructure_type': {'Windows Server'},
                    'business_unit': {'IT Operations'}
                },
                'coverage_flags': {
                    'in_crowdstrike': True,
                    'in_splunk': False,
                    'in_chronicle': False,
                    'in_original_cmdb': False,
                    'in_tanium': False,
                    'in_dlp': False
                },
                'source_count': 1,
                'total_rows': 1,
                'source_tables': ['test_table'],
                'first_seen': datetime.now().isoformat()
            }
            
            result = self.store_single_host_immediately('TEST-SERVER-01', test_host_data)
            if result:
                count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
                logger.info(f"TEST SUCCESS: Total rows in database: {count}")
                
                test_row = self.conn.execute("SELECT hostname, ip_address, infrastructure_type FROM maximum_intensity_assets WHERE hostname = 'TEST-SERVER-01'").fetchone()
                if test_row:
                    logger.info(f"TEST ROW: {test_row}")
                else:
                    logger.error("Test row not found after insert")
            else:
                logger.error("Test insert failed")
        except Exception as e:
            logger.error(f"Test insert error: {e}")
    
    def close(self):
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Database close failed: {e}")

class QuantumEnhancedDatabaseManager(MaximumIntensityDatabaseManager):
    def store_comprehensive_discovery(self, quantum_discovery: QuantumDiscovery) -> int:
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
        
        stats = quantum_discovery.intelligence_metrics or {}
        return self.store_maximum_intensity_discovery(assets_dict, stats)

DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager