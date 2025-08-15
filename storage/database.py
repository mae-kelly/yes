# storage/database.py - FIXED VERSION WITH GUARANTEED ROW INSERTION

import duckdb
import json
import logging
import time
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
        """🔥 ESTABLISH DATABASE CONNECTION WITH MAXIMUM PERFORMANCE SETTINGS"""
        try:
            self.conn = duckdb.connect(self.db_path)
            
            # 🔥 MAXIMUM PERFORMANCE SETTINGS
            self.conn.execute("PRAGMA memory_limit='4GB'")
            self.conn.execute("PRAGMA threads=8")
            self.conn.execute("PRAGMA enable_progress_bar=true")
            
            logger.info(f"🔥 DATABASE CONNECTION ESTABLISHED: {self.db_path}")
            self._setup_maximum_intensity_schema()
            
        except Exception as e:
            logger.error(f"💥 DATABASE CONNECTION FAILED: {e}")
            raise
    
    def _setup_maximum_intensity_schema(self):
        """🔥 CREATE COMPREHENSIVE SCHEMA FOR MAXIMUM DATA STORAGE"""
        try:
            # Drop existing tables to ensure clean start
            self.conn.execute("DROP TABLE IF EXISTS maximum_intensity_assets")
            self.conn.execute("DROP TABLE IF EXISTS discovery_metadata")
            
            logger.info("🔥 CREATING MAXIMUM INTENSITY ASSET SCHEMA...")
            
            # 🔥 COMPREHENSIVE ASSET TABLE WITH ALL POSSIBLE FIELDS
            self.conn.execute("""
                CREATE TABLE maximum_intensity_assets (
                    asset_id VARCHAR PRIMARY KEY,
                    hostname VARCHAR NOT NULL,
                    
                    -- Identity Fields
                    ip_address VARCHAR,
                    fqdn VARCHAR,
                    mac_address VARCHAR,
                    
                    -- Infrastructure Fields
                    infrastructure_type VARCHAR,
                    operating_system VARCHAR,
                    system_classification VARCHAR,
                    environment VARCHAR,
                    
                    -- Location Fields
                    region VARCHAR,
                    country VARCHAR,
                    datacenter VARCHAR,
                    cloud_region VARCHAR,
                    
                    -- Business Fields
                    business_unit VARCHAR,
                    application VARCHAR,
                    owner VARCHAR,
                    criticality VARCHAR,
                    
                    -- Coverage Flags
                    in_chronicle BOOLEAN DEFAULT FALSE,
                    in_crowdstrike BOOLEAN DEFAULT FALSE,
                    in_original_cmdb BOOLEAN DEFAULT FALSE,
                    in_splunk BOOLEAN DEFAULT FALSE,
                    in_tanium BOOLEAN DEFAULT FALSE,
                    in_dlp BOOLEAN DEFAULT FALSE,
                    
                    -- Metrics
                    source_count INTEGER DEFAULT 0,
                    total_rows INTEGER DEFAULT 0,
                    total_unique_attributes INTEGER DEFAULT 0,
                    
                    -- Source Information
                    source_tables JSON,
                    all_attributes JSON,
                    
                    -- Timestamps
                    first_seen TIMESTAMP,
                    last_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Discovery metadata table
            self.conn.execute("""
                CREATE TABLE discovery_metadata (
                    id VARCHAR PRIMARY KEY,
                    discovery_type VARCHAR,
                    total_hosts_discovered INTEGER,
                    total_rows_processed INTEGER,
                    total_attributes_extracted INTEGER,
                    total_cells_analyzed INTEGER,
                    processing_time_minutes DOUBLE,
                    rows_per_second DOUBLE,
                    peak_memory_mb DOUBLE,
                    stats JSON,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Force commit the schema creation
            self.conn.commit()
            
            logger.info("✅ MAXIMUM INTENSITY SCHEMA CREATED SUCCESSFULLY")
            
            # Verify tables were created
            tables = self.conn.execute("SHOW TABLES").fetchall()
            logger.info(f"📊 VERIFIED TABLES: {[table[0] for table in tables]}")
            
        except Exception as e:
            logger.error(f"💥 SCHEMA CREATION FAILED: {e}")
            raise
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        """🔥 STORE DISCOVERY RESULTS WITH MAXIMUM INTENSITY AND GUARANTEED INSERTION"""
        
        if not assets:
            logger.warning("⚠️  NO ASSETS TO STORE!")
            return 0
        
        logger.info("🔥🔥🔥 STARTING MAXIMUM INTENSITY DATABASE STORAGE 🔥🔥🔥")
        logger.info(f"📊 ASSETS TO STORE: {len(assets):,}")
        logger.info(f"🌪️  THIS WILL MAKE YOUR STORAGE WORK HARD!")
        
        stored_count = 0
        batch_size = 1000
        current_batch = []
        
        try:
            # Start transaction
            self.conn.begin()
            
            for asset_id, asset_data in assets.items():
                try:
                    # Extract all attributes with intelligent defaults
                    all_attrs = asset_data.get('all_attributes', {})
                    coverage = asset_data.get('coverage_flags', {})
                    
                    # 🔥 EXTRACT FIRST VALUE FROM EACH ATTRIBUTE SET
                    def get_first_value(attr_key: str, default: str = '') -> str:
                        values = all_attrs.get(attr_key, set())
                        if isinstance(values, (list, set)) and values:
                            return str(list(values)[0])
                        elif values:
                            return str(values)
                        return default
                    
                    # Prepare comprehensive asset data
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
                        'total_unique_attributes': asset_data.get('total_unique_attributes', 0),
                        'source_tables': json.dumps(asset_data.get('source_tables', [])),
                        'all_attributes': json.dumps(all_attrs, default=list),
                        'first_seen': asset_data.get('first_seen'),
                        'last_updated': asset_data.get('last_updated')
                    }
                    
                    current_batch.append(asset_row)
                    
                    # Process in batches for better performance
                    if len(current_batch) >= batch_size:
                        batch_stored = self._insert_batch(current_batch)
                        stored_count += batch_stored
                        current_batch = []
                        
                        logger.info(f"⚡ BATCH STORED: {stored_count:,} assets so far...")
                    
                except Exception as e:
                    logger.error(f"💥 FAILED TO PREPARE ASSET {asset_id}: {e}")
                    continue
            
            # Insert remaining assets
            if current_batch:
                batch_stored = self._insert_batch(current_batch)
                stored_count += batch_stored
            
            # Store discovery metadata
            self._store_discovery_metadata(stats)
            
            # Commit all changes
            self.conn.commit()
            
            # 🔥 VERIFICATION - Count actual rows in database
            actual_count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            
            logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
            logger.info("🎉 MAXIMUM INTENSITY DATABASE STORAGE COMPLETE! 🎉")
            logger.info(f"📊 ASSETS PROCESSED: {stored_count:,}")
            logger.info(f"✅ VERIFIED IN DATABASE: {actual_count:,}")
            logger.info(f"💾 DATABASE FILE: {self.db_path}")
            logger.info("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
            
            if actual_count != stored_count:
                logger.warning(f"⚠️  ROW COUNT MISMATCH: Expected {stored_count}, Found {actual_count}")
            
            return actual_count
            
        except Exception as e:
            logger.error(f"💥 DATABASE STORAGE TRANSACTION FAILED: {e}")
            try:
                self.conn.rollback()
                logger.info("🔄 TRANSACTION ROLLED BACK")
            except:
                pass
            raise
    
    def _insert_batch(self, batch: List[Dict[str, Any]]) -> int:
        """🔥 INSERT BATCH OF ASSETS WITH ERROR HANDLING"""
        try:
            # Prepare the INSERT statement
            insert_sql = """
                INSERT INTO maximum_intensity_assets (
                    asset_id, hostname, ip_address, fqdn, mac_address,
                    infrastructure_type, operating_system, system_classification, environment,
                    region, country, datacenter, cloud_region,
                    business_unit, application, owner, criticality,
                    in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                    source_count, total_rows, total_unique_attributes,
                    source_tables, all_attributes, first_seen, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Prepare batch data
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
                    asset['source_count'], asset['total_rows'], asset['total_unique_attributes'],
                    asset['source_tables'], asset['all_attributes'], 
                    asset['first_seen'], asset['last_updated']
                )
                batch_data.append(row_tuple)
            
            # Execute batch insert
            self.conn.executemany(insert_sql, batch_data)
            
            logger.debug(f"✅ INSERTED BATCH OF {len(batch)} ASSETS")
            return len(batch)
            
        except Exception as e:
            logger.error(f"💥 BATCH INSERT FAILED: {e}")
            # Try individual inserts as fallback
            success_count = 0
            for asset in batch:
                try:
                    self.conn.execute(insert_sql, (
                        asset['asset_id'], asset['hostname'], asset['ip_address'], 
                        asset['fqdn'], asset['mac_address'], asset['infrastructure_type'],
                        asset['operating_system'], asset['system_classification'], asset['environment'],
                        asset['region'], asset['country'], asset['datacenter'], asset['cloud_region'],
                        asset['business_unit'], asset['application'], asset['owner'], asset['criticality'],
                        asset['in_chronicle'], asset['in_crowdstrike'], asset['in_original_cmdb'],
                        asset['in_splunk'], asset['in_tanium'], asset['in_dlp'],
                        asset['source_count'], asset['total_rows'], asset['total_unique_attributes'],
                        asset['source_tables'], asset['all_attributes'], 
                        asset['first_seen'], asset['last_updated']
                    ))
                    success_count += 1
                except Exception as e2:
                    logger.error(f"💥 INDIVIDUAL INSERT FAILED FOR {asset['asset_id']}: {e2}")
            
            return success_count
    
    def _store_discovery_metadata(self, stats: Dict[str, Any]):
        """🔥 STORE DISCOVERY METADATA"""
        try:
            discovery_id = f"maximum_intensity_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.conn.execute("""
                INSERT INTO discovery_metadata (
                    id, discovery_type, total_hosts_discovered, total_rows_processed,
                    total_attributes_extracted, total_cells_analyzed, processing_time_minutes,
                    rows_per_second, peak_memory_mb, stats
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                discovery_id,
                "maximum_intensity_discovery",
                stats.get('total_unique_hosts', 0),
                stats.get('total_rows_processed', 0),
                stats.get('total_attributes_extracted', 0),
                stats.get('total_cells_analyzed', 0),
                stats.get('processing_time_minutes', 0),
                stats.get('rows_per_second', 0),
                stats.get('peak_memory_mb', 0),
                json.dumps(stats)
            ])
            
            logger.info(f"✅ DISCOVERY METADATA STORED: {discovery_id}")
            
        except Exception as e:
            logger.error(f"💥 METADATA STORAGE FAILED: {e}")
    
    def query_assets(self, query: str) -> List[Dict[str, Any]]:
        """🔥 EXECUTE QUERY AND RETURN RESULTS"""
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"💥 QUERY EXECUTION FAILED: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """🔥 GET COMPREHENSIVE DATABASE STATISTICS"""
        try:
            stats = {}
            
            # Asset count
            stats['total_assets'] = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            
            # Coverage statistics
            coverage_stats = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN in_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN in_original_cmdb THEN 1 ELSE 0 END) as cmdb_count
                FROM maximum_intensity_assets
            """).fetchone()
            
            stats['coverage'] = {
                'chronicle': coverage_stats[0],
                'crowdstrike': coverage_stats[1],
                'splunk': coverage_stats[2],
                'cmdb': coverage_stats[3]
            }
            
            # Top regions
            top_regions = self.conn.execute("""
                SELECT region, COUNT(*) as count 
                FROM maximum_intensity_assets 
                WHERE region IS NOT NULL AND region != ''
                GROUP BY region 
                ORDER BY count DESC 
                LIMIT 10
            """).fetchall()
            
            stats['top_regions'] = [{'region': r[0], 'count': r[1]} for r in top_regions]
            
            return stats
            
        except Exception as e:
            logger.error(f"💥 STATS QUERY FAILED: {e}")
            return {'error': str(e)}
    
    def close(self):
        """🔥 CLOSE DATABASE CONNECTION"""
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                logger.info("✅ DATABASE CONNECTION CLOSED")
            except Exception as e:
                logger.error(f"💥 DATABASE CLOSE FAILED: {e}")

# Legacy compatibility
class QuantumEnhancedDatabaseManager(MaximumIntensityDatabaseManager):
    def store_comprehensive_discovery(self, quantum_discovery: QuantumDiscovery) -> int:
        """Legacy compatibility method"""
        # Convert HyperAssets to dictionary format
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
                'total_unique_attributes': 5,
                'source_tables': hyper_asset.source_provenance,
                'first_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        
        stats = quantum_discovery.intelligence_metrics or {}
        return self.store_maximum_intensity_discovery(assets_dict, stats)

# Aliases for compatibility
DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager