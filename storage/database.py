import duckdb
import json
import logging
import time
import os
from typing import Dict, List, Any, Set
from datetime import datetime
from core.types import HyperAsset, QuantumDiscovery

logger = logging.getLogger(__name__)

class MaximumIntensityDatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.storage_count = 0
        self.failed_count = 0
        self._connect_and_setup()
    
    def _connect_and_setup(self):
        try:
            self.conn = duckdb.connect(self.db_path)
            self.conn.execute("PRAGMA memory_limit='4GB'")
            self.conn.execute("PRAGMA threads=8")
            logger.info(f"💾 Database connection established: {self.db_path}")
            self._setup_ao1_aligned_schema()
        except Exception as e:
            logger.error(f"💥 Database connection failed: {e}")
            raise
    
    def _setup_ao1_aligned_schema(self):
        """Schema perfectly aligned with AO1 data structure"""
        try:
            # Drop existing tables
            self.conn.execute("DROP TABLE IF EXISTS maximum_intensity_assets")
            self.conn.execute("DROP TABLE IF EXISTS discovery_metadata")
            
            logger.info("💾 Creating AO1-aligned schema")
            
            # Main assets table - exactly matching AO1 structure
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
                    source_tables TEXT,
                    all_attributes TEXT,
                    first_seen TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Discovery metadata
            self.conn.execute("""
                CREATE TABLE discovery_metadata (
                    id VARCHAR PRIMARY KEY,
                    discovery_type VARCHAR,
                    total_hosts_discovered INTEGER,
                    total_rows_processed INTEGER,
                    processing_time_minutes DOUBLE,
                    guaranteed_stores INTEGER DEFAULT 0,
                    failed_stores INTEGER DEFAULT 0,
                    stats TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Indexes for performance
            self.conn.execute("CREATE INDEX idx_hostname ON maximum_intensity_assets(hostname)")
            self.conn.execute("CREATE INDEX idx_last_updated ON maximum_intensity_assets(last_updated)")
            
            logger.info("✅ AO1-aligned schema created successfully")
            
        except Exception as e:
            logger.error(f"💥 Schema creation failed: {e}")
            raise
    
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        """
        Store host using EXACT AO1 data structure
        This method is called directly from AO1 with AO1's data format
        """
        try:
            asset_id = str(hostname).upper()
            
            # Extract data exactly as AO1 provides it
            all_attributes = host_data.get('all_attributes', {})
            coverage_flags = host_data.get('coverage_flags', {})
            source_tables = host_data.get('source_tables', set())
            source_count = host_data.get('source_count', 0)
            total_rows = host_data.get('total_rows', 0)
            first_seen = host_data.get('first_seen', datetime.now().isoformat())
            last_updated = host_data.get('last_updated', datetime.now().isoformat())
            
            # Convert source_tables set to list for JSON storage
            if isinstance(source_tables, set):
                source_tables_list = list(source_tables)
            else:
                source_tables_list = source_tables
            
            # Convert all_attributes to database-friendly format
            db_attributes = {}
            for key, value in all_attributes.items():
                if isinstance(value, set):
                    db_attributes[key] = list(value)
                elif isinstance(value, list):
                    db_attributes[key] = value
                else:
                    db_attributes[key] = [str(value)] if value else []
            
            # Extract individual field values (first value from each attribute)
            def get_first_value(attr_key: str) -> str:
                values = db_attributes.get(attr_key, [])
                return str(values[0]).strip() if values else ''
            
            # Map to database columns
            ip_address = get_first_value('ip_address')
            fqdn = get_first_value('fqdn')
            mac_address = get_first_value('mac_address')
            infrastructure_type = get_first_value('infrastructure_type')
            operating_system = get_first_value('operating_system')
            system_classification = get_first_value('system_classification')
            environment = get_first_value('environment')
            region = get_first_value('region')
            country = get_first_value('country')
            datacenter = get_first_value('datacenter')
            cloud_region = get_first_value('cloud_region')
            business_unit = get_first_value('business_unit')
            application = get_first_value('application')
            owner = get_first_value('owner')
            criticality = get_first_value('criticality')
            
            # Check if host already exists
            existing = self.conn.execute(
                "SELECT asset_id FROM maximum_intensity_assets WHERE asset_id = ?", 
                [asset_id]
            ).fetchone()
            
            if existing:
                # UPDATE existing host with AO1 merge logic
                self._update_existing_host_ao1_style(
                    asset_id, hostname, ip_address, fqdn, mac_address, infrastructure_type,
                    operating_system, system_classification, environment, region, country,
                    datacenter, cloud_region, business_unit, application, owner, criticality,
                    coverage_flags, source_count, total_rows, source_tables_list, 
                    db_attributes, last_updated
                )
                logger.info(f"   🔄 UPDATED: {hostname} (sources: {source_count})")
            else:
                # INSERT new host
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
                
                insert_values = (
                    asset_id, hostname, 
                    ip_address or None, fqdn or None, mac_address or None,
                    infrastructure_type or None, operating_system or None, 
                    system_classification or None, environment or None,
                    region or None, country or None, datacenter or None, cloud_region or None,
                    business_unit or None, application or None, owner or None, criticality or None,
                    coverage_flags.get('in_chronicle', False),
                    coverage_flags.get('in_crowdstrike', False),
                    coverage_flags.get('in_original_cmdb', False),
                    coverage_flags.get('in_splunk', False),
                    coverage_flags.get('in_tanium', False),
                    coverage_flags.get('in_dlp', False),
                    source_count, total_rows,
                    json.dumps(source_tables_list),
                    json.dumps(db_attributes, default=str),
                    first_seen, last_updated
                )
                
                self.conn.execute(insert_sql, insert_values)
                logger.info(f"   ➕ INSERTED: {hostname}")
            
            self.conn.commit()
            self.storage_count += 1
            return True
            
        except Exception as e:
            logger.error(f"💥 STORAGE FAILED for {hostname}: {e}")
            try:
                self.conn.rollback()
            except:
                pass
            self.failed_count += 1
            return False
    
    def _update_existing_host_ao1_style(self, asset_id, hostname, ip_address, fqdn, mac_address,
                                       infrastructure_type, operating_system, system_classification,
                                       environment, region, country, datacenter, cloud_region,
                                       business_unit, application, owner, criticality,
                                       coverage_flags, source_count, total_rows, source_tables_list,
                                       db_attributes, last_updated):
        """Update existing host with AO1-style merging"""
        
        # Get existing values
        existing = self.conn.execute("""
            SELECT ip_address, fqdn, mac_address, infrastructure_type, operating_system,
                   system_classification, environment, region, country, datacenter, cloud_region,
                   business_unit, application, owner, criticality, source_tables, all_attributes,
                   in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp
            FROM maximum_intensity_assets WHERE asset_id = ?
        """, [asset_id]).fetchone()
        
        if not existing:
            return
        
        (existing_ip, existing_fqdn, existing_mac, existing_infra, existing_os,
         existing_sys_class, existing_env, existing_region, existing_country,
         existing_dc, existing_cloud_region, existing_bu, existing_app, existing_owner,
         existing_crit, existing_tables_str, existing_attrs_str,
         existing_chronicle, existing_cs, existing_cmdb, existing_splunk, 
         existing_tanium, existing_dlp) = existing
        
        # Merge values with comma separation for conflicts
        def merge_value(existing_val, new_val):
            if not existing_val:
                return new_val
            if not new_val:
                return existing_val
            if existing_val.lower() == new_val.lower():
                return existing_val
            # Check if new value already in comma-separated list
            existing_parts = [p.strip() for p in existing_val.split(',')]
            for part in existing_parts:
                if part.lower() == new_val.lower():
                    return existing_val
            # Add new conflicting value
            return f"{existing_val},{new_val}"
        
        # Merge each field
        merged_ip = merge_value(existing_ip or '', ip_address)
        merged_fqdn = merge_value(existing_fqdn or '', fqdn)
        merged_mac = merge_value(existing_mac or '', mac_address)
        merged_infra = merge_value(existing_infra or '', infrastructure_type)
        merged_os = merge_value(existing_os or '', operating_system)
        merged_sys_class = merge_value(existing_sys_class or '', system_classification)
        merged_env = merge_value(existing_env or '', environment)
        merged_region = merge_value(existing_region or '', region)
        merged_country = merge_value(existing_country or '', country)
        merged_dc = merge_value(existing_dc or '', datacenter)
        merged_cloud_region = merge_value(existing_cloud_region or '', cloud_region)
        merged_bu = merge_value(existing_bu or '', business_unit)
        merged_app = merge_value(existing_app or '', application)
        merged_owner = merge_value(existing_owner or '', owner)
        merged_crit = merge_value(existing_crit or '', criticality)
        
        # Merge source tables
        try:
            existing_tables = json.loads(existing_tables_str) if existing_tables_str else []
        except:
            existing_tables = []
        
        merged_tables = list(set(existing_tables + source_tables_list))
        merged_source_count = len(merged_tables)
        
        # Merge coverage flags (OR logic)
        merged_coverage = {
            'in_chronicle': existing_chronicle or coverage_flags.get('in_chronicle', False),
            'in_crowdstrike': existing_cs or coverage_flags.get('in_crowdstrike', False),
            'in_original_cmdb': existing_cmdb or coverage_flags.get('in_original_cmdb', False),
            'in_splunk': existing_splunk or coverage_flags.get('in_splunk', False),
            'in_tanium': existing_tanium or coverage_flags.get('in_tanium', False),
            'in_dlp': existing_dlp or coverage_flags.get('in_dlp', False)
        }
        
        # Merge all_attributes
        try:
            existing_attrs = json.loads(existing_attrs_str) if existing_attrs_str else {}
        except:
            existing_attrs = {}
        
        merged_attrs = existing_attrs.copy()
        for key, values in db_attributes.items():
            if key not in merged_attrs:
                merged_attrs[key] = []
            
            # Ensure existing is a list
            if not isinstance(merged_attrs[key], list):
                merged_attrs[key] = [merged_attrs[key]] if merged_attrs[key] else []
            
            # Add new values
            for v in values:
                if str(v).strip() and str(v).strip() not in merged_attrs[key]:
                    merged_attrs[key].append(str(v).strip())
        
        # Update the record
        update_sql = """
            UPDATE maximum_intensity_assets SET
                ip_address = ?, fqdn = ?, mac_address = ?, infrastructure_type = ?,
                operating_system = ?, system_classification = ?, environment = ?,
                region = ?, country = ?, datacenter = ?, cloud_region = ?,
                business_unit = ?, application = ?, owner = ?, criticality = ?,
                in_chronicle = ?, in_crowdstrike = ?, in_original_cmdb = ?,
                in_splunk = ?, in_tanium = ?, in_dlp = ?,
                source_count = ?, total_rows = total_rows + ?, source_tables = ?,
                all_attributes = ?, last_updated = ?
            WHERE asset_id = ?
        """
        
        update_values = (
            merged_ip or None, merged_fqdn or None, merged_mac or None, merged_infra or None,
            merged_os or None, merged_sys_class or None, merged_env or None,
            merged_region or None, merged_country or None, merged_dc or None, 
            merged_cloud_region or None, merged_bu or None, merged_app or None, 
            merged_owner or None, merged_crit or None,
            merged_coverage['in_chronicle'], merged_coverage['in_crowdstrike'],
            merged_coverage['in_original_cmdb'], merged_coverage['in_splunk'],
            merged_coverage['in_tanium'], merged_coverage['in_dlp'],
            merged_source_count, total_rows,
            json.dumps(merged_tables), json.dumps(merged_attrs, default=str),
            last_updated, asset_id
        )
        
        self.conn.execute(update_sql, update_values)
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        """Store discovery results using AO1 format"""
        if not assets:
            logger.warning("💾 No assets to store")
            return 0
        
        logger.info(f"💾 Storing {len(assets):,} assets from AO1 discovery")
        
        start_time = time.time()
        
        try:
            for asset_id, asset_data in assets.items():
                success = self.store_single_host_immediately(asset_id, asset_data)
                
                if (self.storage_count + self.failed_count) % 1000 == 0:
                    logger.info(f"💾 Progress: {self.storage_count:,} stored, {self.failed_count:,} failed")
            
            # Store discovery metadata
            stats['guaranteed_stores'] = self.storage_count
            stats['failed_stores'] = self.failed_count
            self._store_discovery_metadata(stats)
            
            actual_count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            processing_time = time.time() - start_time
            
            logger.info(f"💾 AO1 Storage complete in {processing_time:.1f}s")
            logger.info(f"💾 Successfully stored: {self.storage_count:,}")
            logger.info(f"💾 Failed to store: {self.failed_count:,}")
            logger.info(f"💾 Total in database: {actual_count:,}")
            
            return actual_count
            
        except Exception as e:
            logger.error(f"💥 AO1 storage failed: {e}")
            return self.storage_count
    
    def _store_discovery_metadata(self, stats: Dict[str, Any]):
        """Store discovery metadata"""
        try:
            discovery_id = f"ao1_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.conn.execute("""
                INSERT INTO discovery_metadata (
                    id, discovery_type, total_hosts_discovered, total_rows_processed,
                    processing_time_minutes, guaranteed_stores, failed_stores, stats
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                discovery_id,
                "ao1_maximum_intensity_discovery",
                stats.get('total_unique_hosts', 0),
                stats.get('total_rows_processed', 0),
                stats.get('processing_time_minutes', 0),
                stats.get('guaranteed_stores', 0),
                stats.get('failed_stores', 0),
                json.dumps(stats)
            ])
            
            logger.info(f"💾 Discovery metadata stored: {discovery_id}")
            
        except Exception as e:
            logger.error(f"💥 Metadata storage failed: {e}")
    
    def query_assets(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query on assets"""
        try:
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"💥 Query execution failed: {e}")
            return []
    
    def get_live_stats(self) -> Dict[str, Any]:
        """Get live database statistics"""
        try:
            total_count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            
            # Get discrepancy stats
            discrepancy_stats = {}
            columns_to_check = ['ip_address', 'infrastructure_type', 'business_unit', 'region']
            
            for col in columns_to_check:
                count = self.conn.execute(f"SELECT COUNT(*) FROM maximum_intensity_assets WHERE {col} LIKE '%,%'").fetchone()[0]
                discrepancy_stats[f'{col}_discrepancies'] = count
            
            return {
                'total_hosts_in_db': total_count,
                'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0,
                'storage_success_count': self.storage_count,
                'storage_failed_count': self.failed_count,
                'discrepancy_stats': discrepancy_stats
            }
            
        except Exception as e:
            return {'error': str(e), 'total_hosts_in_db': 0}
    
    def show_sample_hosts(self, limit: int = 5) -> List[str]:
        """Show sample hosts with their data"""
        try:
            results = self.conn.execute(f"""
                SELECT hostname, ip_address, infrastructure_type, business_unit, 
                       in_chronicle, in_crowdstrike, source_count
                FROM maximum_intensity_assets 
                ORDER BY last_updated DESC 
                LIMIT {limit}
            """).fetchall()
            
            sample_hosts = []
            for row in results:
                hostname, ip, infra, bu, chronicle, cs, sources = row
                
                # Show discrepancies
                discrepancies = []
                if ip and ',' in ip:
                    discrepancies.append(f"IP:{ip}")
                if infra and ',' in infra:
                    discrepancies.append(f"INFRA:{infra}")
                if bu and ',' in bu:
                    discrepancies.append(f"BU:{bu}")
                
                coverage_info = []
                if chronicle:
                    coverage_info.append("Chronicle")
                if cs:
                    coverage_info.append("CrowdStrike")
                
                host_info = f"{hostname} (sources:{sources})"
                if ip and ',' not in ip:
                    host_info += f" [{ip}]"
                if coverage_info:
                    host_info += f" {{{','.join(coverage_info)}}}"
                if discrepancies:
                    host_info += f" ⚠️{{{','.join(discrepancies)}}}"
                
                sample_hosts.append(host_info)
            
            return sample_hosts
            
        except Exception as e:
            logger.error(f"💥 Sample hosts query failed: {e}")
            return []
    
    def get_discrepancy_report(self) -> Dict[str, Any]:
        """Get report of hosts with data discrepancies"""
        try:
            results = self.conn.execute("""
                SELECT hostname, ip_address, infrastructure_type, business_unit, region, 
                       source_count, last_updated
                FROM maximum_intensity_assets 
                WHERE ip_address LIKE '%,%' 
                   OR infrastructure_type LIKE '%,%'
                   OR business_unit LIKE '%,%'
                   OR region LIKE '%,%'
                ORDER BY source_count DESC, last_updated DESC
            """).fetchall()
            
            discrepancies = []
            for row in results:
                hostname, ip, infra, bu, region, sources, last_updated = row
                
                issues = []
                if ip and ',' in ip:
                    issues.append(f"IP: {ip}")
                if infra and ',' in infra:
                    issues.append(f"Infrastructure: {infra}")
                if bu and ',' in bu:
                    issues.append(f"Business Unit: {bu}")
                if region and ',' in region:
                    issues.append(f"Region: {region}")
                
                discrepancies.append({
                    'hostname': hostname,
                    'source_count': sources,
                    'last_updated': last_updated,
                    'issues': issues
                })
            
            return {
                'total_discrepant_hosts': len(discrepancies),
                'discrepancies': discrepancies[:50]  # Top 50
            }
            
        except Exception as e:
            logger.error(f"💥 Discrepancy report failed: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                logger.info(f"💾 Database closed: {self.storage_count} stored, {self.failed_count} failed")
            except Exception as e:
                logger.error(f"💥 Database close failed: {e}")

# Compatibility aliases
DatabaseManager = MaximumIntensityDatabaseManager
EnhancedDatabaseManager = MaximumIntensityDatabaseManager
ContentDatabase = MaximumIntensityDatabaseManager

class QuantumEnhancedDatabaseManager(MaximumIntensityDatabaseManager):
    def store_comprehensive_discovery(self, quantum_discovery: QuantumDiscovery) -> int:
        """Store quantum discovery results"""
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