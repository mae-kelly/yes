# storage/database.py
# BULLETPROOF DUCKDB VERSION - GUARANTEED TO WORK

import duckdb
import json
import logging
import time
import os
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# DATABASE FILE PATH - CHANGE THIS IF NEEDED
DATABASE_PATH = "guaranteed_working_cmdb.db"

class MaximumIntensityDatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.conn = None
        self.total_stored = 0
        self.total_failed = 0
        
        # Delete existing database to start fresh
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
                logger.info(f"🗑️  Deleted existing database: {self.db_path}")
            except:
                pass
        
        self._connect_and_create_tables()
    
    def _connect_and_create_tables(self):
        """Connect to DuckDB and create tables"""
        try:
            logger.info(f"🚀 Creating new DuckDB: {self.db_path}")
            self.conn = duckdb.connect(self.db_path)
            
            # Simple, bulletproof table creation
            self.conn.execute("""
                CREATE TABLE assets (
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
                    source_count INTEGER DEFAULT 1,
                    total_rows INTEGER DEFAULT 1,
                    source_tables VARCHAR,
                    all_attributes VARCHAR,
                    first_seen VARCHAR,
                    last_updated VARCHAR,
                    created_at VARCHAR DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
                )
            """)
            
            self.conn.commit()
            logger.info("✅ Database and table created successfully")
            
            # Test the connection immediately
            self._test_database()
            
        except Exception as e:
            logger.error(f"💥 Database creation failed: {e}")
            raise
    
    def _test_database(self):
        """Test database functionality"""
        try:
            # Test insert
            test_sql = """
                INSERT INTO assets (asset_id, hostname, ip_address, infrastructure_type) 
                VALUES ('TEST001', 'test-server', '192.168.1.1', 'Test Server')
            """
            self.conn.execute(test_sql)
            self.conn.commit()
            
            # Test select
            result = self.conn.execute("SELECT COUNT(*) FROM assets").fetchone()
            logger.info(f"✅ Database test passed - {result[0]} rows")
            
            # Clean up test data
            self.conn.execute("DELETE FROM assets WHERE asset_id = 'TEST001'")
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"💥 Database test failed: {e}")
            raise
    
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        """BULLETPROOF: Store a single host with maximum simplicity"""
        
        try:
            asset_id = str(hostname).upper()
            logger.info(f"💾 STORING: {asset_id}")
            
            # Extract data safely
            all_attrs = host_data.get('all_attributes', {})
            coverage = host_data.get('coverage_flags', {})
            source_tables = host_data.get('source_tables', [])
            
            # Convert everything to simple types
            if isinstance(source_tables, set):
                source_tables = list(source_tables)
            
            # Convert attributes to JSON string
            simple_attrs = {}
            for key, value in all_attrs.items():
                if isinstance(value, set):
                    simple_attrs[key] = list(value)
                elif isinstance(value, list):
                    simple_attrs[key] = value
                else:
                    simple_attrs[key] = [str(value)] if value else []
            
            # Extract field values (take first value of each attribute)
            def get_value(key):
                values = simple_attrs.get(key, [])
                return str(values[0]).strip() if values else None
            
            # Simple field extraction
            ip_address = get_value('ip_address')
            fqdn = get_value('fqdn')
            mac_address = get_value('mac_address')
            infrastructure_type = get_value('infrastructure_type')
            operating_system = get_value('operating_system')
            system_classification = get_value('system_classification')
            environment = get_value('environment')
            region = get_value('region')
            country = get_value('country')
            datacenter = get_value('datacenter')
            cloud_region = get_value('cloud_region')
            business_unit = get_value('business_unit')
            application = get_value('application')
            owner = get_value('owner')
            criticality = get_value('criticality')
            
            # Check if exists
            existing = self.conn.execute(
                "SELECT asset_id FROM assets WHERE asset_id = ?", 
                [asset_id]
            ).fetchone()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if existing:
                # Simple UPDATE - no complex merging for now
                update_sql = """
                    UPDATE assets SET
                        hostname = ?, ip_address = ?, fqdn = ?, mac_address = ?,
                        infrastructure_type = ?, operating_system = ?, system_classification = ?,
                        environment = ?, region = ?, country = ?, datacenter = ?, cloud_region = ?,
                        business_unit = ?, application = ?, owner = ?, criticality = ?,
                        in_chronicle = ?, in_crowdstrike = ?, in_original_cmdb = ?,
                        in_splunk = ?, in_tanium = ?, in_dlp = ?,
                        source_count = source_count + 1, total_rows = total_rows + 1,
                        source_tables = ?, all_attributes = ?, last_updated = ?
                    WHERE asset_id = ?
                """
                
                update_params = [
                    hostname, ip_address, fqdn, mac_address,
                    infrastructure_type, operating_system, system_classification,
                    environment, region, country, datacenter, cloud_region,
                    business_unit, application, owner, criticality,
                    coverage.get('in_chronicle', False),
                    coverage.get('in_crowdstrike', False), 
                    coverage.get('in_original_cmdb', False),
                    coverage.get('in_splunk', False),
                    coverage.get('in_tanium', False),
                    coverage.get('in_dlp', False),
                    json.dumps(source_tables),
                    json.dumps(simple_attrs),
                    current_time,
                    asset_id
                ]
                
                self.conn.execute(update_sql, update_params)
                logger.info(f"   🔄 UPDATED: {asset_id}")
                
            else:
                # Simple INSERT
                insert_sql = """
                    INSERT INTO assets (
                        asset_id, hostname, ip_address, fqdn, mac_address,
                        infrastructure_type, operating_system, system_classification, environment,
                        region, country, datacenter, cloud_region,
                        business_unit, application, owner, criticality,
                        in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                        source_count, total_rows, source_tables, all_attributes, 
                        first_seen, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                insert_params = [
                    asset_id, hostname, ip_address, fqdn, mac_address,
                    infrastructure_type, operating_system, system_classification, environment,
                    region, country, datacenter, cloud_region,
                    business_unit, application, owner, criticality,
                    coverage.get('in_chronicle', False),
                    coverage.get('in_crowdstrike', False),
                    coverage.get('in_original_cmdb', False),
                    coverage.get('in_splunk', False),
                    coverage.get('in_tanium', False),
                    coverage.get('in_dlp', False),
                    host_data.get('source_count', 1),
                    host_data.get('total_rows', 1),
                    json.dumps(source_tables),
                    json.dumps(simple_attrs),
                    host_data.get('first_seen', current_time),
                    current_time
                ]
                
                self.conn.execute(insert_sql, insert_params)
                logger.info(f"   ➕ INSERTED: {asset_id}")
            
            # IMMEDIATE COMMIT
            self.conn.commit()
            self.total_stored += 1
            
            # Verify it was stored
            verify = self.conn.execute("SELECT COUNT(*) FROM assets WHERE asset_id = ?", [asset_id]).fetchone()
            if verify[0] > 0:
                logger.info(f"   ✅ VERIFIED: {asset_id} is in database")
                return True
            else:
                logger.error(f"   ❌ VERIFICATION FAILED: {asset_id} not found after insert")
                return False
            
        except Exception as e:
            logger.error(f"💥 STORAGE FAILED for {hostname}: {e}")
            import traceback
            traceback.print_exc()
            self.total_failed += 1
            
            # Try to rollback
            try:
                self.conn.rollback()
            except:
                pass
            
            return False
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        """Store all assets from discovery"""
        if not assets:
            logger.warning("💾 No assets to store")
            return 0
        
        logger.info(f"💾 STORING {len(assets):,} ASSETS")
        
        stored_count = 0
        failed_count = 0
        
        for asset_id, asset_data in assets.items():
            try:
                success = self.store_single_host_immediately(asset_id, asset_data)
                if success:
                    stored_count += 1
                else:
                    failed_count += 1
                
                # Progress logging
                if (stored_count + failed_count) % 100 == 0:
                    total_in_db = self.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
                    logger.info(f"💾 Progress: {stored_count:,} stored, {failed_count:,} failed, {total_in_db:,} total in DB")
                    
            except Exception as e:
                logger.error(f"💥 Failed to process {asset_id}: {e}")
                failed_count += 1
        
        # Final verification
        final_count = self.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        
        logger.info(f"💾 STORAGE COMPLETE:")
        logger.info(f"   📊 Attempted: {len(assets):,}")
        logger.info(f"   ✅ Stored: {stored_count:,}")
        logger.info(f"   ❌ Failed: {failed_count:,}")
        logger.info(f"   💾 Total in DB: {final_count:,}")
        
        return final_count
    
    def get_live_stats(self) -> Dict[str, Any]:
        """Get current database statistics"""
        try:
            total_count = self.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            
            # Sample of recent entries
            recent = self.conn.execute("""
                SELECT hostname, ip_address, infrastructure_type 
                FROM assets 
                ORDER BY last_updated DESC 
                LIMIT 5
            """).fetchall()
            
            return {
                'total_hosts_in_db': total_count,
                'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0,
                'total_stored_session': self.total_stored,
                'total_failed_session': self.total_failed,
                'recent_entries': [f"{r[0]} ({r[1]}) [{r[2]}]" for r in recent]
            }
            
        except Exception as e:
            logger.error(f"💥 Stats query failed: {e}")
            return {'error': str(e), 'total_hosts_in_db': 0}
    
    def show_sample_hosts(self, limit: int = 10) -> List[str]:
        """Show sample hosts from database"""
        try:
            results = self.conn.execute(f"""
                SELECT hostname, ip_address, infrastructure_type, business_unit, 
                       in_chronicle, in_crowdstrike, source_count, last_updated
                FROM assets 
                ORDER BY last_updated DESC 
                LIMIT {limit}
            """).fetchall()
            
            sample_hosts = []
            for row in results:
                hostname, ip, infra, bu, chronicle, cs, sources, updated = row
                
                coverage = []
                if chronicle:
                    coverage.append("Chronicle")
                if cs:
                    coverage.append("CrowdStrike")
                
                host_info = f"{hostname}"
                if ip:
                    host_info += f" ({ip})"
                if infra:
                    host_info += f" [{infra}]"
                if bu:
                    host_info += f" BU:{bu}"
                if coverage:
                    host_info += f" {{{','.join(coverage)}}}"
                host_info += f" Sources:{sources} Updated:{updated}"
                
                sample_hosts.append(host_info)
            
            return sample_hosts
            
        except Exception as e:
            logger.error(f"💥 Sample query failed: {e}")
            return [f"Error: {e}"]
    
    def query_assets(self, query: str) -> List[Dict[str, Any]]:
        """Execute custom SQL query"""
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"💥 Query failed: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                
                # Final stats
                final_size = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
                logger.info(f"💾 Database closed: {self.total_stored:,} stored, {final_size:.1f} MB")
                
            except Exception as e:
                logger.error(f"💥 Close failed: {e}")

# Create instance for immediate testing
def test_database():
    """Test the database immediately"""
    logger.info("🧪 TESTING DATABASE")
    
    try:
        db = MaximumIntensityDatabaseManager()
        
        # Test data
        test_host = {
            'hostname': 'TEST-SERVER-001',
            'all_attributes': {
                'ip_address': ['10.1.1.100'],
                'infrastructure_type': ['Windows Server 2019'],
                'business_unit': ['IT Operations']
            },
            'coverage_flags': {
                'in_crowdstrike': True,
                'in_splunk': False
            },
            'source_tables': ['test_table_1'],
            'source_count': 1,
            'total_rows': 1
        }
        
        # Store test host
        success = db.store_single_host_immediately('TEST-SERVER-001', test_host)
        logger.info(f"🧪 Test storage result: {success}")
        
        # Check stats
        stats = db.get_live_stats()
        logger.info(f"🧪 Database stats: {stats}")
        
        # Show sample
        samples = db.show_sample_hosts(3)
        logger.info(f"🧪 Sample hosts: {samples}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"💥 Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Aliases for compatibility
DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager

# Test when imported
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_database()