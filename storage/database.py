import duckdb
import json
import logging
import time
import os
from typing import Dict, List, Any, Set
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class MaximumIntensityDatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.storage_stats = {
            'successful_stores': 0,
            'failed_stores': 0,
            'updates': 0,
            'inserts': 0
        }
        self._connect_and_setup()
    
    def _connect_and_setup(self):
        try:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.conn = duckdb.connect(self.db_path)
            self.conn.execute("PRAGMA memory_limit='4GB'")
            self.conn.execute("PRAGMA threads=8")
            logger.info(f"✅ Database connected: {self.db_path}")
            self._setup_ao1_aligned_schema()
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _setup_ao1_aligned_schema(self):
        """Schema perfectly aligned with AO1 data structure"""
        try:
            # Drop existing tables
            self.conn.execute("DROP TABLE IF EXISTS maximum_intensity_assets")
            self.conn.execute("DROP TABLE IF EXISTS discovery_metadata")
            
            logger.info("Creating AO1-aligned schema...")
            
            # Main assets table - exactly matching AO1 structure
            self.conn.execute("""
                CREATE TABLE maximum_intensity_assets (
                    asset_id VARCHAR PRIMARY KEY,
                    hostname VARCHAR NOT NULL,
                    
                    -- Core identity fields
                    ip_address TEXT,
                    fqdn TEXT,
                    mac_address TEXT,
                    
                    -- Infrastructure fields  
                    infrastructure_type TEXT,
                    operating_system TEXT,
                    system_classification TEXT,
                    environment TEXT,
                    
                    -- Location fields
                    region TEXT,
                    country TEXT,
                    datacenter TEXT,
                    cloud_region TEXT,
                    
                    -- Business fields
                    business_unit TEXT,
                    application TEXT,
                    owner TEXT,
                    criticality TEXT,
                    
                    -- Coverage flags (exactly as AO1 creates them)
                    in_chronicle BOOLEAN DEFAULT FALSE,
                    in_crowdstrike BOOLEAN DEFAULT FALSE,
                    in_original_cmdb BOOLEAN DEFAULT FALSE,
                    in_splunk BOOLEAN DEFAULT FALSE,
                    in_tanium BOOLEAN DEFAULT FALSE,
                    in_dlp BOOLEAN DEFAULT FALSE,
                    
                    -- Source tracking (exactly as AO1 tracks)
                    source_count INTEGER DEFAULT 0,
                    total_rows INTEGER DEFAULT 0,
                    source_tables TEXT,  -- JSON array of source table names
                    
                    -- All attributes blob (exactly as AO1 creates)
                    all_attributes TEXT,  -- JSON object with all discovered attributes
                    
                    -- Timestamps
                    first_seen TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Discovery metadata table
            self.conn.execute("""
                CREATE TABLE discovery_metadata (
                    id VARCHAR PRIMARY KEY,
                    discovery_type VARCHAR DEFAULT 'maximum_intensity',
                    total_hosts_discovered INTEGER,
                    total_rows_processed INTEGER,
                    processing_time_minutes DOUBLE,
                    stats TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create performance indexes
            self.conn.execute("CREATE INDEX idx_hostname ON maximum_intensity_assets(hostname)")
            self.conn.execute("CREATE INDEX idx_ip_address ON maximum_intensity_assets(ip_address)")
            self.conn.execute("CREATE INDEX idx_source_count ON maximum_intensity_assets(source_count)")
            
            logger.info("✅ AO1-aligned schema created successfully")
            
            # Test the schema
            self._test_schema()
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            raise
    
    def _test_schema(self):
        """Test schema with a sample insert"""
        try:
            test_data = {
                'asset_id': 'TEST-SCHEMA-001',
                'hostname': 'TEST-SCHEMA-001',
                'ip_address': '192.168.1.100',
                'infrastructure_type': 'Test Server',
                'business_unit': 'IT',
                'in_crowdstrike': True,
                'source_count': 1,
                'total_rows': 1,
                'source_tables': '["test_table"]',
                'all_attributes': '{"test_attr": ["test_value"]}',
                'first_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            self.conn.execute("""
                INSERT INTO maximum_intensity_assets (
                    asset_id, hostname, ip_address, infrastructure_type, business_unit,
                    in_crowdstrike, source_count, total_rows, source_tables, 
                    all_attributes, first_seen, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                test_data['asset_id'], test_data['hostname'], test_data['ip_address'],
                test_data['infrastructure_type'], test_data['business_unit'],
                test_data['in_crowdstrike'], test_data['source_count'], test_data['total_rows'],
                test_data['source_tables'], test_data['all_attributes'],
                test_data['first_seen'], test_data['last_updated']
            ])
            
            # Verify the insert
            result = self.conn.execute("SELECT hostname FROM maximum_intensity_assets WHERE asset_id = ?", 
                                     [test_data['asset_id']]).fetchone()
            
            if result:
                logger.info(f"✅ Schema test successful: {result[0]}")
                # Clean up test data
                self.conn.execute("DELETE FROM maximum_intensity_assets WHERE asset_id = ?", [test_data['asset_id']])
                self.conn.commit()
            else:
                logger.error("❌ Schema test failed: no result returned")
                
        except Exception as e:
            logger.error(f"❌ Schema test failed: {e}")
    
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        """Store single host - perfectly aligned with AO1 data structure"""
        
        logger.debug(f"🔄 Storing host: {hostname}")
        logger.debug(f"🔄 Host data keys: {list(host_data.keys())}")
        
        try:
            asset_id = str(hostname).upper()
            
            # Extract data exactly as AO1 provides it
            all_attributes = host_data.get('all_attributes', {})
            coverage_flags = host_data.get('coverage_flags', {})
            source_tables = host_data.get('source_tables', [])
            
            logger.debug(f"🔄 All attributes: {len(all_attributes)} keys")
            logger.debug(f"🔄 Coverage flags: {coverage_flags}")
            logger.debug(f"🔄 Source tables: {source_tables}")
            
            # Convert source_tables to JSON (handle both set and list)
            if isinstance(source_tables, set):
                source_tables = list(source_tables)
            source_tables_json = json.dumps(source_tables)
            
            # Convert all_attributes to JSON (handle both dict with sets/lists)
            serializable_attrs = {}
            for key, value in all_attributes.items():
                if isinstance(value, set):
                    serializable_attrs[key] = list(value)
                elif isinstance(value, list):
                    serializable_attrs[key] = value
                else:
                    serializable_attrs[key] = [str(value)] if value else []
            all_attributes_json = json.dumps(serializable_attrs)
            
            # Extract specific field values using AO1's mapping logic
            def get_field_value(field_mappings: List[str]) -> str:
                """Get first non-empty value from mapped fields"""
                for field_key in field_mappings:
                    if field_key in all_attributes:
                        values = all_attributes[field_key]
                        if isinstance(values, (list, set)) and values:
                            return str(list(values)[0]).strip()
                        elif values:
                            return str(values).strip()
                return ''
            
            # Map fields exactly as AO1 maps them
            extracted_values = {
                'ip_address': get_field_value(['ip_address', 'ip', 'ipaddress']),
                'fqdn': get_field_value(['fqdn', 'fully_qualified']),
                'mac_address': get_field_value(['mac_address', 'mac', 'ethernet']),
                'infrastructure_type': get_field_value(['infrastructure_type', 'infrastructure', 'hosting']),
                'operating_system': get_field_value(['operating_system', 'os', 'platform']),
                'system_classification': get_field_value(['system_classification', 'classification']),
                'environment': get_field_value(['environment', 'env']),
                'region': get_field_value(['region', 'location', 'geo']),
                'country': get_field_value(['country']),
                'datacenter': get_field_value(['datacenter', 'dc', 'facility']),
                'cloud_region': get_field_value(['cloud_region']),
                'business_unit': get_field_value(['business_unit', 'business', 'bu', 'department']),
                'application': get_field_value(['application', 'application_name', 'app_name']),
                'owner': get_field_value(['owner', 'responsible']),
                'criticality': get_field_value(['criticality', 'critical', 'priority'])
            }
            
            logger.debug(f"🔄 Extracted values: {extracted_values}")
            
            # Check if host already exists
            existing = self.conn.execute("""
                SELECT asset_id, source_count, total_rows, all_attributes, source_tables,
                       in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp
                FROM maximum_intensity_assets WHERE asset_id = ?
            """, [asset_id]).fetchone()
            
            if existing:
                # UPDATE EXISTING HOST - merge data exactly like AO1 does
                logger.debug(f"🔄 Updating existing host: {hostname}")
                
                (existing_asset_id, existing_source_count, existing_total_rows, 
                 existing_attrs_json, existing_tables_json,
                 existing_chronicle, existing_cs, existing_cmdb, 
                 existing_splunk, existing_tanium, existing_dlp) = existing
                
                # Merge source tables
                try:
                    existing_tables = json.loads(existing_tables_json) if existing_tables_json else []
                except:
                    existing_tables = []
                
                merged_tables = list(set(existing_tables + source_tables))
                merged_source_count = len(merged_tables)
                merged_total_rows = existing_total_rows + host_data.get('total_rows', 1)
                
                # Merge attributes (additive, like AO1 does)
                try:
                    existing_attrs = json.loads(existing_attrs_json) if existing_attrs_json else {}
                except:
                    existing_attrs = {}
                
                merged_attrs = existing_attrs.copy()
                for key, new_values in serializable_attrs.items():
                    if key not in merged_attrs:
                        merged_attrs[key] = []
                    
                    # Ensure existing is a list
                    if not isinstance(merged_attrs[key], list):
                        merged_attrs[key] = [merged_attrs[key]] if merged_attrs[key] else []
                    
                    # Add new values that don't exist
                    for val in new_values:
                        if str(val).strip() and str(val).strip() not in merged_attrs[key]:
                            merged_attrs[key].append(str(val).strip())
                
                # Merge coverage flags (OR logic like AO1)
                merged_coverage = {
                    'in_chronicle': existing_chronicle or coverage_flags.get('in_chronicle', False),
                    'in_crowdstrike': existing_cs or coverage_flags.get('in_crowdstrike', False),
                    'in_original_cmdb': existing_cmdb or coverage_flags.get('in_original_cmdb', False),
                    'in_splunk': existing_splunk or coverage_flags.get('in_splunk', False),
                    'in_tanium': existing_tanium or coverage_flags.get('in_tanium', False),
                    'in_dlp': existing_dlp or coverage_flags.get('in_dlp', False)
                }
                
                # Merge extracted field values (comma-separated for conflicts)
                update_values = {}
                for field, new_value in extracted_values.items():
                    if new_value:
                        # Get existing value
                        existing_result = self.conn.execute(f"SELECT {field} FROM maximum_intensity_assets WHERE asset_id = ?", [asset_id]).fetchone()
                        existing_value = existing_result[0] if existing_result and existing_result[0] else ''
                        
                        if not existing_value:
                            update_values[field] = new_value
                        elif existing_value.lower() != new_value.lower():
                            # Conflict - comma separate
                            if new_value not in existing_value.split(','):
                                update_values[field] = f"{existing_value},{new_value}"
                                logger.info(f"   🔀 CONFLICT {field}: '{existing_value}' + '{new_value}'")
                            else:
                                update_values[field] = existing_value  # No change needed
                        else:
                            update_values[field] = existing_value  # Same value
                    else:
                        # Keep existing value
                        existing_result = self.conn.execute(f"SELECT {field} FROM maximum_intensity_assets WHERE asset_id = ?", [asset_id]).fetchone()
                        update_values[field] = existing_result[0] if existing_result and existing_result[0] else None
                
                # Execute update
                update_sql = """
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
                """
                
                update_params = [
                    update_values['ip_address'], update_values['fqdn'], update_values['mac_address'],
                    update_values['infrastructure_type'], update_values['operating_system'],
                    update_values['system_classification'], update_values['environment'],
                    update_values['region'], update_values['country'], update_values['datacenter'],
                    update_values['cloud_region'], update_values['business_unit'],
                    update_values['application'], update_values['owner'], update_values['criticality'],
                    merged_coverage['in_chronicle'], merged_coverage['in_crowdstrike'],
                    merged_coverage['in_original_cmdb'], merged_coverage['in_splunk'],
                    merged_coverage['in_tanium'], merged_coverage['in_dlp'],
                    merged_source_count, merged_total_rows, json.dumps(merged_tables),
                    json.dumps(merged_attrs), datetime.now().isoformat(),
                    asset_id
                ]
                
                self.conn.execute(update_sql, update_params)
                self.storage_stats['updates'] += 1
                logger.info(f"   🔄 UPDATED: {hostname} (sources: {existing_source_count} → {merged_source_count})")
                
            else:
                # INSERT NEW HOST
                logger.debug(f"🔄 Inserting new host: {hostname}")
                
                insert_sql = """
                    INSERT INTO maximum_intensity_assets (
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
                    asset_id, hostname,
                    extracted_values['ip_address'] or None, extracted_values['fqdn'] or None,
                    extracted_values['mac_address'] or None, extracted_values['infrastructure_type'] or None,
                    extracted_values['operating_system'] or None, extracted_values['system_classification'] or None,
                    extracted_values['environment'] or None, extracted_values['region'] or None,
                    extracted_values['country'] or None, extracted_values['datacenter'] or None,
                    extracted_values['cloud_region'] or None, extracted_values['business_unit'] or None,
                    extracted_values['application'] or None, extracted_values['owner'] or None,
                    extracted_values['criticality'] or None,
                    coverage_flags.get('in_chronicle', False), coverage_flags.get('in_crowdstrike', False),
                    coverage_flags.get('in_original_cmdb', False), coverage_flags.get('in_splunk', False),
                    coverage_flags.get('in_tanium', False), coverage_flags.get('in_dlp', False),
                    host_data.get('source_count', 1), host_data.get('total_rows', 1),
                    source_tables_json, all_attributes_json,
                    host_data.get('first_seen', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ]
                
                self.conn.execute(insert_sql, insert_params)
                self.storage_stats['inserts'] += 1
                logger.info(f"   ➕ INSERTED: {hostname}")
            
            # Commit immediately for each host
            self.conn.commit()
            self.storage_stats['successful_stores'] += 1
            
            logger.debug(f"✅ Successfully stored: {hostname}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Storage failed for {hostname}: {e}")
            logger.error(f"   Error details: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            
            try:
                self.conn.rollback()
            except:
                pass
            
            self.storage_stats['failed_stores'] += 1
            return False
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        """Store complete discovery results - perfectly aligned with AO1 output"""
        
        if not assets:
            logger.warning("⚠️ No assets to store")
            return 0
        
        logger.info(f"📦 Storing {len(assets):,} assets from AO1 discovery")
        start_time = time.time()
        
        stored_count = 0
        failed_count = 0
        
        try:
            for asset_id, asset_data in assets.items():
                logger.debug(f"📦 Processing asset: {asset_id}")
                logger.debug(f"📦 Asset data: {asset_data}")
                
                success = self.store_single_host_immediately(asset_id, asset_data)
                if success:
                    stored_count += 1
                else:
                    failed_count += 1
                
                # Progress logging
                if (stored_count + failed_count) % 1000 == 0:
                    logger.info(f"📊 Progress: {stored_count:,} stored, {failed_count:,} failed")
            
            # Store discovery metadata
            self._store_discovery_metadata(stats, stored_count, failed_count)
            
            # Final verification
            actual_count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            processing_time = time.time() - start_time
            
            logger.info("✅ Storage complete!")
            logger.info(f"📊 Successfully stored: {stored_count:,}")
            logger.info(f"📊 Failed to store: {failed_count:,}")
            logger.info(f"📊 Database total: {actual_count:,}")
            logger.info(f"⏱️ Processing time: {processing_time:.1f}s")
            logger.info(f"🚀 Storage rate: {stored_count/processing_time:.0f} hosts/sec")
            
            return actual_count
            
        except Exception as e:
            logger.error(f"❌ Bulk storage failed: {e}")
            return stored_count
    
    def _store_discovery_metadata(self, stats: Dict[str, Any], stored_count: int, failed_count: int):
        """Store discovery metadata"""
        try:
            discovery_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Enhance stats with storage results
            enhanced_stats = stats.copy()
            enhanced_stats.update({
                'storage_successful': stored_count,
                'storage_failed': failed_count,
                'storage_success_rate': stored_count / (stored_count + failed_count) if (stored_count + failed_count) > 0 else 0,
                'database_stats': self.storage_stats.copy()
            })
            
            self.conn.execute("""
                INSERT INTO discovery_metadata (
                    id, discovery_type, total_hosts_discovered, total_rows_processed,
                    processing_time_minutes, stats
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                discovery_id,
                "maximum_intensity_ao1_aligned",
                stats.get('total_unique_hosts', stored_count),
                stats.get('total_rows_processed', 0),
                stats.get('processing_time_minutes', 0),
                json.dumps(enhanced_stats)
            ])
            
            logger.info(f"📋 Discovery metadata stored: {discovery_id}")
            
        except Exception as e:
            logger.error(f"❌ Metadata storage failed: {e}")
    
    def get_live_stats(self) -> Dict[str, Any]:
        """Get real-time database statistics"""
        try:
            # Basic counts
            total_hosts = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            
            # Coverage stats
            coverage_stats = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN in_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_count,
                    SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN in_original_cmdb THEN 1 ELSE 0 END) as cmdb_count,
                    AVG(source_count) as avg_sources,
                    MAX(source_count) as max_sources
                FROM maximum_intensity_assets
            """).fetchone()
            
            # Discrepancy stats (comma-separated values)
            discrepancy_stats = {}
            for field in ['ip_address', 'infrastructure_type', 'business_unit', 'region']:
                count = self.conn.execute(f"SELECT COUNT(*) FROM maximum_intensity_assets WHERE {field} LIKE '%,%'").fetchone()[0]
                discrepancy_stats[f'{field}_discrepancies'] = count
            
            return {
                'total_hosts_in_db': total_hosts,
                'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0,
                'coverage_stats': {
                    'chronicle': coverage_stats[0] if coverage_stats else 0,
                    'crowdstrike': coverage_stats[1] if coverage_stats else 0,
                    'splunk': coverage_stats[2] if coverage_stats else 0,
                    'cmdb': coverage_stats[3] if coverage_stats else 0,
                    'avg_sources': coverage_stats[4] if coverage_stats else 0,
                    'max_sources': coverage_stats[5] if coverage_stats else 0
                },
                'discrepancy_stats': discrepancy_stats,
                'storage_stats': self.storage_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"❌ Stats query failed: {e}")
            return {'error': str(e), 'total_hosts_in_db': 0}
    
    def show_sample_hosts(self, limit: int = 5) -> List[str]:
        """Show sample hosts with their data"""
        try:
            results = self.conn.execute(f"""
                SELECT hostname, ip_address, infrastructure_type, business_unit,
                       in_chronicle, in_crowdstrike, source_count, last_updated
                FROM maximum_intensity_assets 
                ORDER BY last_updated DESC 
                LIMIT {limit}
            """).fetchall()
            
            sample_hosts = []
            for row in results:
                hostname, ip, infra, bu, chronicle, cs, sources, last_updated = row
                
                # Build display string
                host_info = f"{hostname} (sources:{sources})"
                
                # Add IP if available and not discrepant
                if ip and ',' not in ip:
                    host_info += f" [{ip}]"
                elif ip and ',' in ip:
                    host_info += f" [IPs:{ip}]"
                
                # Add coverage
                coverage = []
                if chronicle:
                    coverage.append("Chronicle")
                if cs:
                    coverage.append("CrowdStrike")
                if coverage:
                    host_info += f" {{{','.join(coverage)}}}"
                
                # Add discrepancy indicators
                conflicts = []
                if ip and ',' in ip:
                    conflicts.append("IP")
                if infra and ',' in infra:
                    conflicts.append("Infra")
                if bu and ',' in bu:
                    conflicts.append("BU")
                if conflicts:
                    host_info += f" ⚠️{{{','.join(conflicts)}}}"
                
                sample_hosts.append(host_info)
            
            return sample_hosts
            
        except Exception as e:
            logger.error(f"❌ Sample hosts query failed: {e}")
            return [f"Error: {e}"]
    
    def query_assets(self, query: str) -> List[Dict[str, Any]]:
        """Execute custom query"""
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                logger.info("✅ Database connection closed")
            except Exception as e:
                logger.error(f"❌ Database close failed: {e}")

# Compatibility aliases
DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager

class QuantumEnhancedDatabaseManager(MaximumIntensityDatabaseManager):
    """Quantum version - same as base but with different naming"""
    
    def store_comprehensive_discovery(self, quantum_discovery) -> int:
        """Store quantum discovery results"""
        # Convert quantum discovery to standard format
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