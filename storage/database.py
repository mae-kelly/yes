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
        self._connect_and_setup()
    
    def _connect_and_setup(self):
        try:
            self.conn = duckdb.connect(self.db_path)
            self.conn.execute("PRAGMA memory_limit='4GB'")
            self.conn.execute("PRAGMA threads=8")
            logger.info(f"Database connection established: {self.db_path}")
            self._setup_optimized_schema()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def _setup_optimized_schema(self):
        try:
            # Drop and recreate tables for clean start
            self.conn.execute("DROP TABLE IF EXISTS maximum_intensity_assets")
            self.conn.execute("DROP TABLE IF EXISTS discovery_metadata")
            self.conn.execute("DROP TABLE IF EXISTS storage_audit_log")
            
            logger.info("Creating optimized asset schema with audit trail")
            
            # Main assets table with comprehensive columns
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
                    created_at TIMESTAMP DEFAULT NOW(),
                    storage_method VARCHAR DEFAULT 'guaranteed_merge'
                )
            """)
            
            # Discovery metadata table
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
            
            # Storage audit log for tracking all operations
            self.conn.execute("""
                CREATE TABLE storage_audit_log (
                    id INTEGER PRIMARY KEY,
                    asset_id VARCHAR,
                    operation VARCHAR,
                    success BOOLEAN,
                    method_used VARCHAR,
                    changes_made TEXT,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create indexes for performance
            self.conn.execute("CREATE INDEX idx_hostname ON maximum_intensity_assets(hostname)")
            self.conn.execute("CREATE INDEX idx_ip_address ON maximum_intensity_assets(ip_address)")
            self.conn.execute("CREATE INDEX idx_last_updated ON maximum_intensity_assets(last_updated)")
            self.conn.execute("CREATE INDEX idx_source_count ON maximum_intensity_assets(source_count)")
            
            logger.info("Optimized schema created successfully with indexes")
            
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise
    
    def _log_storage_operation(self, asset_id: str, operation: str, success: bool, 
                              method_used: str, changes_made: str = None, error_message: str = None):
        """Log all storage operations for audit trail"""
        try:
            self.conn.execute("""
                INSERT INTO storage_audit_log (
                    asset_id, operation, success, method_used, changes_made, error_message
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [asset_id, operation, success, method_used, changes_made, error_message])
        except Exception as e:
            logger.error(f"Failed to log storage operation: {e}")
    
    def _merge_column_value(self, existing_value: str, new_value: str, column_name: str) -> tuple:
        """
        Merge column values with comma separation for discrepancies
        Returns: (merged_value, has_changes, change_description)
        """
        if not existing_value:
            return new_value, True, f"Added {column_name}: {new_value}"
        if not new_value:
            return existing_value, False, None
        
        # Clean values
        existing_clean = str(existing_value).strip()
        new_clean = str(new_value).strip()
        
        if existing_clean.lower() == new_clean.lower():
            return existing_clean, False, None  # Same value, no change
        
        # Different values - check if new value is already in existing (comma-separated)
        existing_parts = [part.strip() for part in existing_clean.split(',')]
        
        # Check if new value already exists in the list
        for part in existing_parts:
            if part.lower() == new_clean.lower():
                return existing_clean, False, None  # Already exists, no change
        
        # New discrepant value - append with comma
        merged = f"{existing_clean},{new_clean}"
        change_desc = f"Conflict in {column_name}: '{existing_clean}' + '{new_clean}'"
        logger.info(f"   🔀 DISCREPANCY in {column_name}: '{existing_clean}' + '{new_clean}' = '{merged}'")
        return merged, True, change_desc
    
    def store_single_host_immediately(self, hostname: str, host_data: Dict[str, Any]) -> bool:
        """Store or update a single host with guaranteed smart value merging"""
        changes_made = []
        
        try:
            asset_id = str(hostname).upper()
            all_attrs = host_data.get('all_attributes', {})
            coverage = host_data.get('coverage_flags', {})
            
            # Extract new values from attributes
            def get_first_value(attr_key: str) -> str:
                values = all_attrs.get(attr_key, set())
                if isinstance(values, (list, set)) and values:
                    return str(list(values)[0]).strip()
                elif values:
                    return str(values).strip()
                return ''
            
            new_values = {
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
                'criticality': get_first_value('criticality')
            }
            
            # Check if host already exists
            existing = self.conn.execute("""
                SELECT ip_address, fqdn, mac_address, infrastructure_type, operating_system,
                       system_classification, environment, region, country, datacenter, cloud_region,
                       business_unit, application, owner, criticality, source_tables, source_count,
                       total_rows, in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, 
                       in_tanium, in_dlp, all_attributes
                FROM maximum_intensity_assets WHERE asset_id = ?
            """, [asset_id]).fetchone()
            
            if existing:
                # MERGE WITH EXISTING DATA
                (existing_ip, existing_fqdn, existing_mac, existing_infra, existing_os,
                 existing_sys_class, existing_env, existing_region, existing_country, 
                 existing_dc, existing_cloud_region, existing_bu, existing_app, 
                 existing_owner, existing_crit, existing_tables_str, existing_source_count,
                 existing_total_rows, existing_chronicle, existing_cs, existing_cmdb,
                 existing_splunk, existing_tanium, existing_dlp, existing_attrs_str) = existing
                
                # Merge each column value and track changes
                merged_values = {}
                for field_name, new_value in new_values.items():
                    existing_value = locals().get(f'existing_{field_name.replace("_", "_")}') or locals().get(f'existing_{field_name}')
                    if field_name == 'ip_address':
                        existing_value = existing_ip
                    elif field_name == 'fqdn':
                        existing_value = existing_fqdn
                    elif field_name == 'mac_address':
                        existing_value = existing_mac
                    elif field_name == 'infrastructure_type':
                        existing_value = existing_infra
                    elif field_name == 'operating_system':
                        existing_value = existing_os
                    elif field_name == 'system_classification':
                        existing_value = existing_sys_class
                    elif field_name == 'environment':
                        existing_value = existing_env
                    elif field_name == 'region':
                        existing_value = existing_region
                    elif field_name == 'country':
                        existing_value = existing_country
                    elif field_name == 'datacenter':
                        existing_value = existing_dc
                    elif field_name == 'cloud_region':
                        existing_value = existing_cloud_region
                    elif field_name == 'business_unit':
                        existing_value = existing_bu
                    elif field_name == 'application':
                        existing_value = existing_app
                    elif field_name == 'owner':
                        existing_value = existing_owner
                    elif field_name == 'criticality':
                        existing_value = existing_crit
                    
                    merged_value, has_change, change_desc = self._merge_column_value(
                        existing_value or '', new_value, field_name
                    )
                    merged_values[field_name] = merged_value
                    
                    if has_change:
                        changes_made.append(change_desc)
                
                # Merge source tables
                try:
                    existing_tables = json.loads(existing_tables_str) if existing_tables_str else []
                except:
                    existing_tables = []
                
                new_tables = host_data.get('source_tables', [])
                if isinstance(new_tables, set):
                    new_tables = list(new_tables)
                
                merged_tables = list(set(existing_tables + new_tables))
                merged_source_count = len(merged_tables)
                merged_total_rows = existing_total_rows + host_data.get('total_rows', 1)
                
                if len(merged_tables) > len(existing_tables):
                    changes_made.append(f"Added {len(merged_tables) - len(existing_tables)} new source tables")
                
                # Merge coverage flags (OR logic - if either is True, result is True)
                merged_coverage = {
                    'in_chronicle': existing_chronicle or coverage.get('in_chronicle', False),
                    'in_crowdstrike': existing_cs or coverage.get('in_crowdstrike', False),
                    'in_original_cmdb': existing_cmdb or coverage.get('in_original_cmdb', False),
                    'in_splunk': existing_splunk or coverage.get('in_splunk', False),
                    'in_tanium': existing_tanium or coverage.get('in_tanium', False),
                    'in_dlp': existing_dlp or coverage.get('in_dlp', False)
                }
                
                # Track coverage changes
                coverage_changes = []
                if merged_coverage['in_chronicle'] and not existing_chronicle:
                    coverage_changes.append("Chronicle")
                if merged_coverage['in_crowdstrike'] and not existing_cs:
                    coverage_changes.append("CrowdStrike")
                if merged_coverage['in_original_cmdb'] and not existing_cmdb:
                    coverage_changes.append("CMDB")
                if merged_coverage['in_splunk'] and not existing_splunk:
                    coverage_changes.append("Splunk")
                if merged_coverage['in_tanium'] and not existing_tanium:
                    coverage_changes.append("Tanium")
                if merged_coverage['in_dlp'] and not existing_dlp:
                    coverage_changes.append("DLP")
                
                if coverage_changes:
                    changes_made.append(f"New coverage: {', '.join(coverage_changes)}")
                
                # Merge all_attributes JSON
                try:
                    existing_all_attrs = json.loads(existing_attrs_str) if existing_attrs_str else {}
                except:
                    existing_all_attrs = {}
                
                merged_all_attrs = existing_all_attrs.copy()
                new_attr_count = 0
                
                for key, values in all_attrs.items():
                    if key not in merged_all_attrs:
                        merged_all_attrs[key] = []
                        new_attr_count += 1
                    
                    # Ensure it's a list
                    if not isinstance(merged_all_attrs[key], list):
                        merged_all_attrs[key] = [merged_all_attrs[key]] if merged_all_attrs[key] else []
                    
                    # Add new values
                    if isinstance(values, (list, set)):
                        for v in values:
                            if str(v).strip() and str(v).strip() not in merged_all_attrs[key]:
                                merged_all_attrs[key].append(str(v).strip())
                                new_attr_count += 1
                    elif values and str(values).strip() not in merged_all_attrs[key]:
                        merged_all_attrs[key].append(str(values).strip())
                        new_attr_count += 1
                
                if new_attr_count > 0:
                    changes_made.append(f"Added {new_attr_count} new attribute values")
                
                # Update existing record
                update_sql = """
                    UPDATE maximum_intensity_assets SET
                        ip_address = ?, fqdn = ?, mac_address = ?, infrastructure_type = ?,
                        operating_system = ?, system_classification = ?, environment = ?,
                        region = ?, country = ?, datacenter = ?, cloud_region = ?,
                        business_unit = ?, application = ?, owner = ?, criticality = ?,
                        in_chronicle = ?, in_crowdstrike = ?, in_original_cmdb = ?,
                        in_splunk = ?, in_tanium = ?, in_dlp = ?,
                        source_count = ?, total_rows = ?, source_tables = ?,
                        all_attributes = ?, last_updated = ?, storage_method = ?
                    WHERE asset_id = ?
                """
                
                update_values = (
                    merged_values['ip_address'] or None,
                    merged_values['fqdn'] or None,
                    merged_values['mac_address'] or None,
                    merged_values['infrastructure_type'] or None,
                    merged_values['operating_system'] or None,
                    merged_values['system_classification'] or None,
                    merged_values['environment'] or None,
                    merged_values['region'] or None,
                    merged_values['country'] or None,
                    merged_values['datacenter'] or None,
                    merged_values['cloud_region'] or None,
                    merged_values['business_unit'] or None,
                    merged_values['application'] or None,
                    merged_values['owner'] or None,
                    merged_values['criticality'] or None,
                    merged_coverage['in_chronicle'],
                    merged_coverage['in_crowdstrike'],
                    merged_coverage['in_original_cmdb'],
                    merged_coverage['in_splunk'],
                    merged_coverage['in_tanium'],
                    merged_coverage['in_dlp'],
                    merged_source_count,
                    merged_total_rows,
                    json.dumps(merged_tables),
                    json.dumps(merged_all_attrs, default=str),
                    datetime.now().isoformat(),
                    'guaranteed_merge_update',
                    asset_id
                )
                
                self.conn.execute(update_sql, update_values)
                
                operation_desc = f"UPDATED: {hostname} (sources: {existing_source_count} → {merged_source_count})"
                if changes_made:
                    operation_desc += f" - Changes: {'; '.join(changes_made)}"
                
                logger.info(f"   🔄 {operation_desc}")
                
                # Log the operation
                self._log_storage_operation(
                    asset_id, 'UPDATE', True, 'guaranteed_merge_update', 
                    '; '.join(changes_made) if changes_made else 'No changes'
                )
                
            else:
                # INSERT NEW RECORD
                source_tables = host_data.get('source_tables', [])
                if isinstance(source_tables, set):
                    source_tables = list(source_tables)
                
                insert_sql = """
                    INSERT INTO maximum_intensity_assets (
                        asset_id, hostname, ip_address, fqdn, mac_address,
                        infrastructure_type, operating_system, system_classification, environment,
                        region, country, datacenter, cloud_region,
                        business_unit, application, owner, criticality,
                        in_chronicle, in_crowdstrike, in_original_cmdb, in_splunk, in_tanium, in_dlp,
                        source_count, total_rows, source_tables, all_attributes, first_seen, 
                        last_updated, storage_method
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                insert_values = (
                    asset_id,
                    hostname,
                    new_values['ip_address'] or None,
                    new_values['fqdn'] or None,
                    new_values['mac_address'] or None,
                    new_values['infrastructure_type'] or None,
                    new_values['operating_system'] or None,
                    new_values['system_classification'] or None,
                    new_values['environment'] or None,
                    new_values['region'] or None,
                    new_values['country'] or None,
                    new_values['datacenter'] or None,
                    new_values['cloud_region'] or None,
                    new_values['business_unit'] or None,
                    new_values['application'] or None,
                    new_values['owner'] or None,
                    new_values['criticality'] or None,
                    coverage.get('in_chronicle', False),
                    coverage.get('in_crowdstrike', False),
                    coverage.get('in_original_cmdb', False),
                    coverage.get('in_splunk', False),
                    coverage.get('in_tanium', False),
                    coverage.get('in_dlp', False),
                    host_data.get('source_count', 1),
                    host_data.get('total_rows', 1),
                    json.dumps(source_tables),
                    json.dumps(all_attrs, default=str),
                    host_data.get('first_seen', datetime.now().isoformat()),
                    datetime.now().isoformat(),
                    'guaranteed_merge_insert'
                )
                
                self.conn.execute(insert_sql, insert_values)
                logger.info(f"   ➕ INSERTED: {hostname}")
                
                # Log the operation
                self._log_storage_operation(
                    asset_id, 'INSERT', True, 'guaranteed_merge_insert', 
                    f"New host with {len(all_attrs)} attributes"
                )
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"💥 DB OPERATION FAILED for {hostname}: {e}")
            
            # Log the failed operation
            self._log_storage_operation(
                hostname, 'FAILED', False, 'guaranteed_merge', None, str(e)
            )
            
            try:
                self.conn.rollback()
            except:
                pass
            return False
    
    def store_maximum_intensity_discovery(self, assets: Dict[str, Any], stats: Dict[str, Any]) -> int:
        """Store all assets using the single host method for consistency"""
        if not assets:
            logger.warning("No assets to store")
            return 0
        
        logger.info(f"Storing {len(assets):,} assets to database")
        stored_count = 0
        failed_count = 0
        
        start_time = time.time()
        
        try:
            for asset_id, asset_data in assets.items():
                success = self.store_single_host_immediately(asset_id, asset_data)
                if success:
                    stored_count += 1
                else:
                    failed_count += 1
                
                if (stored_count + failed_count) % 1000 == 0:
                    logger.info(f"Progress: {stored_count:,} stored, {failed_count:,} failed")
            
            # Update stats with storage results
            stats['guaranteed_stores'] = stored_count
            stats['failed_stores'] = failed_count
            stats['storage_success_rate'] = stored_count / (stored_count + failed_count) if (stored_count + failed_count) > 0 else 0
            
            self._store_discovery_metadata(stats)
            
            actual_count = self.conn.execute("SELECT COUNT(*) FROM maximum_intensity_assets").fetchone()[0]
            processing_time = time.time() - start_time
            
            logger.info(f"Database storage complete in {processing_time:.1f}s")
            logger.info(f"Successfully stored: {stored_count:,}")
            logger.info(f"Failed to store: {failed_count:,}")
            logger.info(f"Verified in database: {actual_count:,}")
            
            return actual_count
            
        except Exception as e:
            logger.error(f"Bulk storage failed: {e}")
            return stored_count
    
    def _store_discovery_metadata(self, stats: Dict[str, Any]):
        try:
            discovery_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.conn.execute("""
                INSERT INTO discovery_metadata (
                    id, discovery_type, total_hosts_discovered, total_rows_processed,
                    processing_time_minutes, guaranteed_stores, failed_stores, stats
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                discovery_id,
                "maximum_intensity_discovery",
                stats.get('total_unique_hosts', 0),
                stats.get('total_rows_processed', 0),
                stats.get('processing_time_minutes', 0),
                stats.get('guaranteed_stores', 0),
                stats.get('failed_stores', 0),
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
            
            # Get some stats about discrepancies
            discrepancy_stats = {}
            columns_to_check = ['ip_address', 'infrastructure_type', 'business_unit', 'region']
            
            for col in columns_to_check:
                count = self.conn.execute(f"SELECT COUNT(*) FROM maximum_intensity_assets WHERE {col} LIKE '%,%'").fetchone()[0]
                discrepancy_stats[f'{col}_discrepancies'] = count
            
            # Get storage operation stats
            storage_stats = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_operations,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
                    COUNT(DISTINCT asset_id) as unique_assets_touched
                FROM storage_audit_log
            """).fetchone()
            
            return {
                'total_hosts_in_db': total_count,
                'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0,
                'discrepancy_stats': discrepancy_stats,
                'storage_operations': {
                    'total': storage_stats[0] if storage_stats else 0,
                    'successful': storage_stats[1] if storage_stats else 0,
                    'unique_assets': storage_stats[2] if storage_stats else 0
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'total_hosts_in_db': 0}
    
    def show_sample_hosts(self, limit: int = 5) -> List[str]:
        try:
            results = self.conn.execute(f"""
                SELECT hostname, ip_address, infrastructure_type, business_unit, 
                       in_chronicle, in_crowdstrike, source_count, storage_method
                FROM maximum_intensity_assets 
                ORDER BY last_updated DESC 
                LIMIT {limit}
            """).fetchall()
            
            sample_hosts = []
            for row in results:
                hostname, ip, infra, bu, chronicle, cs, sources, storage_method = row
                
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
                if storage_method:
                    host_info += f" ({storage_method})"
                
                sample_hosts.append(host_info)
            
            return sample_hosts
            
        except Exception as e:
            logger.error(f"Sample hosts query failed: {e}")
            return []
    
    def get_discrepancy_report(self) -> Dict[str, Any]:
        """Get a comprehensive report of all hosts with data discrepancies"""
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
            
            # Get summary stats
            summary_stats = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_discrepant_hosts,
                    AVG(source_count) as avg_sources_discrepant,
                    MAX(source_count) as max_sources_discrepant
                FROM maximum_intensity_assets 
                WHERE ip_address LIKE '%,%' 
                   OR infrastructure_type LIKE '%,%'
                   OR business_unit LIKE '%,%'
                   OR region LIKE '%,%'
            """).fetchone()
            
            return {
                'total_discrepant_hosts': summary_stats[0] if summary_stats else 0,
                'avg_sources_discrepant': summary_stats[1] if summary_stats else 0,
                'max_sources_discrepant': summary_stats[2] if summary_stats else 0,
                'discrepancies': discrepancies[:100]  # Top 100
            }
            
        except Exception as e:
            logger.error(f"Discrepancy report failed: {e}")
            return {'error': str(e)}
    
    def get_storage_audit_report(self) -> Dict[str, Any]:
        """Get audit report of all storage operations"""
        try:
            # Recent operations
            recent_ops = self.conn.execute("""
                SELECT asset_id, operation, success, method_used, changes_made, 
                       error_message, timestamp
                FROM storage_audit_log 
                ORDER BY timestamp DESC 
                LIMIT 50
            """).fetchall()
            
            # Summary stats
            summary = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_operations,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
                    COUNT(DISTINCT asset_id) as unique_assets,
                    COUNT(DISTINCT method_used) as methods_used
                FROM storage_audit_log
            """).fetchone()
            
            # Method breakdown
            method_stats = self.conn.execute("""
                SELECT method_used, COUNT(*) as count, 
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                FROM storage_audit_log 
                GROUP BY method_used
                ORDER BY count DESC
            """).fetchall()
            
            return {
                'summary': {
                    'total_operations': summary[0] if summary else 0,
                    'successful_operations': summary[1] if summary else 0,
                    'success_rate': (summary[1] / summary[0] * 100) if summary and summary[0] > 0 else 0,
                    'unique_assets': summary[2] if summary else 0,
                    'methods_used': summary[3] if summary else 0
                },
                'method_breakdown': [
                    {
                        'method': row[0], 
                        'total': row[1], 
                        'successful': row[2],
                        'success_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0
                    } for row in method_stats
                ],
                'recent_operations': [
                    {
                        'asset_id': row[0],
                        'operation': row[1],
                        'success': row[2],
                        'method': row[3],
                        'changes': row[4],
                        'error': row[5],
                        'timestamp': row[6]
                    } for row in recent_ops
                ]
            }
            
        except Exception as e:
            logger.error(f"Storage audit report failed: {e}")
            return {'error': str(e)}
    
    def cleanup_and_optimize(self):
        """Cleanup and optimize database"""
        try:
            logger.info("Starting database cleanup and optimization")
            
            # Analyze tables for better query performance
            self.conn.execute("ANALYZE")
            
            # Get database stats before cleanup
            before_stats = self.get_live_stats()
            
            # Clean up old audit log entries (keep last 10000)
            self.conn.execute("""
                DELETE FROM storage_audit_log 
                WHERE id NOT IN (
                    SELECT id FROM storage_audit_log 
                    ORDER BY timestamp DESC 
                    LIMIT 10000
                )
            """)
            
            # Vacuum to reclaim space
            self.conn.execute("VACUUM")
            
            after_stats = self.get_live_stats()
            
            logger.info(f"Database optimization complete")
            logger.info(f"Size before: {before_stats.get('database_size_mb', 0):.1f} MB")
            logger.info(f"Size after: {after_stats.get('database_size_mb', 0):.1f} MB")
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
    
    def close(self):
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Database close failed: {e}")

# Aliases for compatibility
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