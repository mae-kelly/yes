#!/usr/bin/env python3

import logging
import duckdb
import re
import ipaddress
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

@dataclass
class AO1AssetRecord:
    hostname: str
    fqdn: str = ""
    ip_address: str = ""
    mac_address: str = ""
    infrastructure_type: str = ""
    system_classification: str = ""
    global_region: str = ""
    country: str = ""
    data_center: str = ""
    cloud_region: str = ""
    business_unit: str = ""
    cio: str = ""
    apm: str = ""
    application_class: str = ""
    edr_coverage: str = "No"
    tanium_coverage: str = "No"
    dlp_coverage: str = "No"
    in_splunk: bool = False
    in_chronicle: bool = False
    in_gso: bool = False
    network_log_types: str = ""
    endpoint_log_types: str = ""
    cloud_log_types: str = ""
    application_log_types: str = ""
    identity_log_types: str = ""
    found_in_cmdb: bool = False
    found_in_splunk: bool = False
    found_in_chronicle: bool = False
    found_in_crowdstrike: bool = False
    source_count: int = 0
    host_parity_score: float = 0.0
    cmdb_asset_visibility_score: float = 0.0
    visibility_gap_severity: str = "unknown"
    raw_data_sources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    completeness_score: float = 0.0

class IntelligentFieldAnalyzer:
    def __init__(self):
        self.field_patterns = {
            'hostname': {
                'name_patterns': ['hostname', 'host_name', 'computername', 'computer_name', 'endpoint_name', 'device_name', 'machine_name'],
                'content_validator': self._validate_hostname_content
            },
            'fqdn': {
                'name_patterns': ['fqdn', 'full_qualified_domain_name', 'dns_name', 'domain_name', 'canonical_name'],
                'content_validator': self._validate_fqdn_content
            },
            'ip_address': {
                'name_patterns': ['ip_address', 'ip_addr', 'ipaddress', 'host_ip', 'endpoint_ip', 'device_ip'],
                'content_validator': self._validate_ip_content
            },
            'mac_address': {
                'name_patterns': ['mac_address', 'mac_addr', 'macaddress', 'physical_address', 'ethernet_address'],
                'content_validator': self._validate_mac_content
            },
            'infrastructure_type': {
                'name_patterns': ['infrastructure_type', 'infra_type', 'platform_type', 'deployment_type', 'env_type'],
                'content_validator': self._validate_infrastructure_content
            },
            'system_classification': {
                'name_patterns': ['system_classification', 'os_type', 'operating_system', 'platform', 'os_name'],
                'content_validator': self._validate_os_content
            },
            'global_region': {
                'name_patterns': ['global_region', 'region', 'geo_region', 'geographic_region', 'location'],
                'content_validator': self._validate_region_content
            },
            'country': {
                'name_patterns': ['country', 'country_code', 'nation', 'country_name'],
                'content_validator': self._validate_country_content
            },
            'business_unit': {
                'name_patterns': ['business_unit', 'bu', 'organization', 'org_unit', 'department'],
                'content_validator': self._validate_business_unit_content
            }
        }

    def _validate_hostname_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        valid_count = 0
        for value in values[:30]:
            if self._is_valid_hostname(value):
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _validate_fqdn_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        valid_count = 0
        for value in values[:30]:
            if self._is_valid_fqdn(value):
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _validate_ip_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        valid_count = 0
        for value in values[:30]:
            if self._is_valid_ip(value):
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _validate_mac_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        valid_count = 0
        for value in values[:30]:
            if self._is_valid_mac(value):
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _validate_infrastructure_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        infra_keywords = [
            'cloud', 'on-prem', 'on-premises', 'saas', 'api', 'physical', 'virtual', 
            'aws', 'azure', 'gcp', 'vmware', 'hyper-v', 'bare-metal'
        ]
        
        valid_count = 0
        for value in values[:30]:
            if any(keyword in str(value).lower() for keyword in infra_keywords):
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _validate_os_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        os_keywords = [
            'windows', 'linux', 'unix', 'server', 'workstation', 'database', 'web',
            'centos', 'ubuntu', 'rhel', 'debian', 'macos', 'aix', 'solaris'
        ]
        
        valid_count = 0
        for value in values[:30]:
            if any(keyword in str(value).lower() for keyword in os_keywords):
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _validate_region_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        region_keywords = [
            'us', 'usa', 'eu', 'europe', 'apac', 'asia', 'pacific', 'americas',
            'north', 'south', 'east', 'west', 'central', 'emea'
        ]
        
        valid_count = 0
        for value in values[:30]:
            if any(keyword in str(value).lower() for keyword in region_keywords):
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _validate_country_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        country_keywords = [
            'usa', 'united states', 'canada', 'uk', 'united kingdom', 'germany', 
            'france', 'japan', 'australia', 'brazil', 'india', 'china'
        ]
        
        valid_count = 0
        for value in values[:30]:
            value_str = str(value).lower()
            if any(keyword in value_str for keyword in country_keywords) or len(value_str.strip()) == 2:
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _validate_business_unit_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        bu_keywords = [
            'finance', 'marketing', 'sales', 'operations', 'hr', 'human resources',
            'it', 'information technology', 'engineering', 'legal', 'compliance'
        ]
        
        valid_count = 0
        for value in values[:30]:
            if any(keyword in str(value).lower() for keyword in bu_keywords):
                valid_count += 1
        
        return valid_count / min(len(values), 30)

    def _is_valid_hostname(self, value: str) -> bool:
        if not value or not isinstance(value, str):
            return False
        
        value = str(value).strip()
        if len(value) < 2 or len(value) > 253:
            return False
        
        if value.upper() in ['UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', 'LOCALHOST']:
            return False
        
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', value):
            return False
        
        if '@' in value or '/' in value or '\\' in value or ' ' in value:
            return False
        
        return re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$', value) or re.match(r'^[a-zA-Z0-9]+$', value)

    def _is_valid_fqdn(self, value: str) -> bool:
        if not value or not isinstance(value, str):
            return False
        
        value = str(value).strip()
        if '.' not in value or len(value) < 4:
            return False
        
        return re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', value) is not None

    def _is_valid_ip(self, value: str) -> bool:
        if not value:
            return False
        
        try:
            ipaddress.ip_address(str(value).strip())
            return True
        except:
            return False

    def _is_valid_mac(self, value: str) -> bool:
        if not value:
            return False
        
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$'
        ]
        
        return any(re.match(pattern, str(value).strip()) for pattern in mac_patterns)

    def analyze_column_for_field_type(self, column_name: str, sample_values: List[str], field_type: str) -> float:
        if field_type not in self.field_patterns:
            return 0.0
        
        config = self.field_patterns[field_type]
        score = 0.0
        
        column_lower = column_name.lower()
        
        for pattern in config['name_patterns']:
            if pattern == column_lower:
                score += 10.0
                break
            elif pattern in column_lower:
                score += 7.0
                break
        
        if sample_values and config['content_validator']:
            content_score = config['content_validator'](sample_values)
            if content_score >= 0.8:
                score += 10.0
            elif content_score >= 0.6:
                score += 8.0
            elif content_score >= 0.4:
                score += 5.0
            elif content_score >= 0.2:
                score += 2.0
        
        return score

class ComprehensiveCMDBBuilder:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        self.field_analyzer = IntelligentFieldAnalyzer()
        
        from gcp_client import BigQueryClientManager
        self.client_manager = BigQueryClientManager(project_id)
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
        except:
            self.chronicle_client_manager = None
            logging.warning("Chronicle access not available")
        
        self.db_path = self.config.get('database_path', 'ao1_comprehensive_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        self._setup_comprehensive_schema()
        
        self.source_tables = {
            'cmdb': 'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'splunk': 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG', 
            'crowdstrike': 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT',
            'chronicle': 'chronicle-fisv.datalake.events'
        }
        
        self.master_asset_registry = {}
        
        logging.info("ComprehensiveCMDBBuilder initialized - will build complete asset profiles")

    def _setup_comprehensive_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS ao1_comprehensive_cmdb")
        
        self.conn.execute("""
            CREATE TABLE ao1_comprehensive_cmdb (
                hostname VARCHAR PRIMARY KEY,
                fqdn VARCHAR DEFAULT '',
                ip_address VARCHAR DEFAULT '',
                mac_address VARCHAR DEFAULT '',
                infrastructure_type VARCHAR DEFAULT '',
                system_classification VARCHAR DEFAULT '',
                global_region VARCHAR DEFAULT '',
                country VARCHAR DEFAULT '',
                data_center VARCHAR DEFAULT '',
                cloud_region VARCHAR DEFAULT '',
                business_unit VARCHAR DEFAULT '',
                cio VARCHAR DEFAULT '',
                apm VARCHAR DEFAULT '',
                application_class VARCHAR DEFAULT '',
                edr_coverage VARCHAR DEFAULT 'No',
                tanium_coverage VARCHAR DEFAULT 'No',
                dlp_coverage VARCHAR DEFAULT 'No',
                in_splunk BOOLEAN DEFAULT FALSE,
                in_chronicle BOOLEAN DEFAULT FALSE,
                in_gso BOOLEAN DEFAULT FALSE,
                network_log_types VARCHAR DEFAULT '',
                endpoint_log_types VARCHAR DEFAULT '',
                cloud_log_types VARCHAR DEFAULT '',
                application_log_types VARCHAR DEFAULT '',
                identity_log_types VARCHAR DEFAULT '',
                found_in_cmdb BOOLEAN DEFAULT FALSE,
                found_in_splunk BOOLEAN DEFAULT FALSE,
                found_in_chronicle BOOLEAN DEFAULT FALSE,
                found_in_crowdstrike BOOLEAN DEFAULT FALSE,
                source_count INTEGER DEFAULT 0,
                host_parity_score DOUBLE DEFAULT 0.0,
                cmdb_asset_visibility_score DOUBLE DEFAULT 0.0,
                visibility_gap_severity VARCHAR DEFAULT 'unknown',
                completeness_score DOUBLE DEFAULT 0.0,
                discovery_timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logging.info("Created comprehensive CMDB schema")

    def build_comprehensive_cmdb(self) -> Dict[str, Any]:
        logging.info("Starting comprehensive CMDB build process")
        
        logging.info("PHASE 1: Collecting all raw asset data from source systems")
        raw_data_collected = self._collect_all_raw_data()
        
        logging.info("PHASE 2: Processing each asset row-by-row for intelligent merging")
        processed_assets = self._process_assets_intelligently()
        
        logging.info("PHASE 3: Validating completeness before database insertion")
        complete_assets = self._validate_and_filter_complete_assets(processed_assets)
        
        logging.info("PHASE 4: Inserting only complete, high-quality asset records")
        inserted_count = self._insert_complete_assets(complete_assets)
        
        verification = self._verify_comprehensive_database()
        
        return {
            'raw_data_sources': raw_data_collected,
            'processed_assets': len(processed_assets),
            'complete_assets': len(complete_assets),
            'inserted_count': inserted_count,
            'database_path': self.db_path,
            'verification': verification
        }

    def _collect_all_raw_data(self) -> Dict[str, int]:
        collection_stats = {}
        
        for source_name, table_path in self.source_tables.items():
            logging.info(f"Collecting raw data from {source_name}: {table_path}")
            
            try:
                if source_name == 'chronicle' and self.chronicle_client_manager:
                    client_manager = self.chronicle_client_manager
                else:
                    client_manager = self.client_manager
                
                raw_records = self._extract_all_raw_records(client_manager, table_path, source_name)
                collection_stats[source_name] = len(raw_records)
                
                logging.info(f"Collected {len(raw_records)} raw records from {source_name}")
                
                for hostname, record_data in raw_records.items():
                    if hostname not in self.master_asset_registry:
                        self.master_asset_registry[hostname] = AO1AssetRecord(hostname=hostname)
                    
                    self.master_asset_registry[hostname].raw_data_sources[source_name] = record_data
                    
                    if source_name == 'cmdb':
                        self.master_asset_registry[hostname].found_in_cmdb = True
                    elif source_name == 'splunk':
                        self.master_asset_registry[hostname].found_in_splunk = True
                    elif source_name == 'chronicle':
                        self.master_asset_registry[hostname].found_in_chronicle = True
                    elif source_name == 'crowdstrike':
                        self.master_asset_registry[hostname].found_in_crowdstrike = True
                
            except Exception as e:
                logging.error(f"Failed to collect data from {source_name}: {e}")
                collection_stats[source_name] = 0
        
        logging.info(f"Master registry now contains {len(self.master_asset_registry)} unique hostnames")
        return collection_stats

    def _extract_all_raw_records(self, client_manager, table_path: str, source_name: str) -> Dict[str, Dict[str, Any]]:
        try:
            with client_manager.get_client() as client:
                table_ref = client.get_table(table_path)
                
                if not table_ref.schema or table_ref.num_rows == 0:
                    logging.warning(f"Table {table_path} is empty or has no schema")
                    return {}
                
                columns = [field.name for field in table_ref.schema]
                logging.info(f"Analyzing {len(columns)} columns in {source_name}")
                
                field_mappings = self._analyze_and_map_fields(client, table_path, columns)
                
                if 'hostname' not in field_mappings:
                    logging.warning(f"No hostname field identified in {source_name}")
                    return {}
                
                logging.info(f"Field mappings for {source_name}: {field_mappings}")
                
                return self._extract_complete_records(client, table_path, field_mappings)
        
        except Exception as e:
            logging.error(f"Failed to extract records from {table_path}: {e}")
            return {}

    def _analyze_and_map_fields(self, client, table_path: str, columns: List[str]) -> Dict[str, str]:
        sample_query = f"""
        SELECT {', '.join([f'`{col}`' for col in columns[:60]])}
        FROM `{table_path}`
        WHERE RAND() < 0.001
        LIMIT 200
        """
        
        column_samples = {}
        
        try:
            job = client.query(sample_query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(columns[:60]):
                sample_values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        sample_values.append(str(row[col_idx]))
                
                column_samples[column_name] = sample_values[:50]
        
        except Exception as e:
            logging.error(f"Failed to sample columns for {table_path}: {e}")
            return {}
        
        field_mappings = {}
        field_types = ['hostname', 'fqdn', 'ip_address', 'mac_address', 'infrastructure_type', 
                      'system_classification', 'global_region', 'country', 'business_unit']
        
        for field_type in field_types:
            best_score = 0.0
            best_column = None
            
            for column_name, sample_values in column_samples.items():
                score = self.field_analyzer.analyze_column_for_field_type(column_name, sample_values, field_type)
                
                if score > best_score and score >= 8.0:
                    best_score = score
                    best_column = column_name
            
            if best_column:
                field_mappings[field_type] = best_column
                logging.info(f"Mapped {field_type} to {best_column} (score: {best_score:.1f})")
        
        return field_mappings

    def _extract_complete_records(self, client, table_path: str, field_mappings: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        hostname_col = field_mappings['hostname']
        
        select_parts = [f"UPPER(TRIM(`{hostname_col}`)) as hostname"]
        
        for field_type, column_name in field_mappings.items():
            if field_type != 'hostname':
                select_parts.append(f"`{column_name}` as {field_type}")
        
        query = f"""
        SELECT {', '.join(select_parts)}
        FROM `{table_path}`
        WHERE `{hostname_col}` IS NOT NULL
        AND LENGTH(TRIM(`{hostname_col}`)) >= 2
        AND LENGTH(TRIM(`{hostname_col}`)) <= 253
        AND UPPER(TRIM(`{hostname_col}`)) NOT IN ('UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY')
        LIMIT 100000
        """
        
        extracted_records = {}
        
        try:
            job = client.query(query)
            results = list(job.result())
            
            for row in results:
                hostname = row[0] if row[0] else None
                
                if hostname and self.field_analyzer._is_valid_hostname(hostname):
                    record_data = {'hostname': hostname}
                    
                    for idx, (field_type, _) in enumerate(field_mappings.items()):
                        if field_type != 'hostname' and idx < len(row) and row[idx]:
                            clean_value = str(row[idx]).strip()
                            if clean_value and clean_value.upper() not in ['UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY']:
                                record_data[field_type] = clean_value
                    
                    extracted_records[hostname] = record_data
        
        except Exception as e:
            logging.error(f"Failed to extract complete records from {table_path}: {e}")
        
        return extracted_records

    def _process_assets_intelligently(self) -> List[AO1AssetRecord]:
        logging.info(f"Processing {len(self.master_asset_registry)} assets row-by-row")
        
        processed_assets = []
        
        for hostname, asset in self.master_asset_registry.items():
            logging.debug(f"Processing asset: {hostname}")
            
            self._merge_all_source_data(asset)
            self._calculate_comprehensive_scores(asset)
            
            processed_assets.append(asset)
            
            if len(processed_assets) % 1000 == 0:
                logging.info(f"Processed {len(processed_assets)} assets so far...")
        
        logging.info(f"Completed processing {len(processed_assets)} assets")
        return processed_assets

    def _merge_all_source_data(self, asset: AO1AssetRecord):
        field_priorities = {
            'cmdb': 4,
            'crowdstrike': 3,
            'splunk': 2,
            'chronicle': 1
        }
        
        fields_to_merge = [
            'fqdn', 'ip_address', 'mac_address', 'infrastructure_type', 
            'system_classification', 'global_region', 'country', 'business_unit'
        ]
        
        for field_name in fields_to_merge:
            best_value = ""
            best_priority = 0
            
            for source_name, raw_data in asset.raw_data_sources.items():
                if field_name in raw_data and raw_data[field_name]:
                    value = str(raw_data[field_name]).strip()
                    source_priority = field_priorities.get(source_name, 0)
                    
                    if value and value.upper() not in ['UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY']:
                        if source_priority > best_priority or (source_priority == best_priority and len(value) > len(best_value)):
                            best_value = value
                            best_priority = source_priority
            
            if best_value:
                setattr(asset, field_name, best_value)
        
        if asset.found_in_crowdstrike:
            asset.edr_coverage = 'Yes'
        
        if asset.found_in_splunk:
            asset.in_splunk = True
        
        if asset.found_in_chronicle:
            asset.in_chronicle = True

    def _calculate_comprehensive_scores(self, asset: AO1AssetRecord):
        source_count = sum([
            1 if asset.found_in_cmdb else 0,
            1 if asset.found_in_splunk else 0,
            1 if asset.found_in_chronicle else 0,
            1 if asset.found_in_crowdstrike else 0
        ])
        asset.source_count = source_count
        
        asset.host_parity_score = (source_count / 4.0) * 100
        
        cmdb_score = 0.0
        if asset.found_in_cmdb:
            cmdb_score += 40.0
        if asset.infrastructure_type:
            cmdb_score += 30.0
        if asset.system_classification:
            cmdb_score += 30.0
        
        asset.cmdb_asset_visibility_score = cmdb_score
        
        completeness_fields = [
            asset.hostname, asset.fqdn, asset.ip_address, asset.infrastructure_type,
            asset.system_classification, asset.global_region, asset.business_unit
        ]
        
        filled_fields = sum(1 for field in completeness_fields if field and field.strip())
        asset.completeness_score = (filled_fields / len(completeness_fields)) * 100
        
        if asset.host_parity_score >= 75:
            asset.visibility_gap_severity = 'low'
        elif asset.host_parity_score >= 50:
            asset.visibility_gap_severity = 'medium'
        elif asset.host_parity_score >= 25:
            asset.visibility_gap_severity = 'high'
        else:
            asset.visibility_gap_severity = 'critical'

    def _validate_and_filter_complete_assets(self, processed_assets: List[AO1AssetRecord]) -> List[AO1AssetRecord]:
        complete_assets = []
        
        for asset in processed_assets:
            required_fields = [asset.hostname, asset.infrastructure_type, asset.system_classification]
            
            if all(field and field.strip() for field in required_fields):
                if asset.completeness_score >= 60.0:
                    complete_assets.append(asset)
                    logging.debug(f"Asset {asset.hostname} passed completeness check (score: {asset.completeness_score:.1f}%)")
                else:
                    logging.debug(f"Asset {asset.hostname} rejected - low completeness (score: {asset.completeness_score:.1f}%)")
            else:
                logging.debug(f"Asset {asset.hostname} rejected - missing required fields")
        
        logging.info(f"Filtered to {len(complete_assets)} complete assets from {len(processed_assets)} processed")
        return complete_assets

    def _insert_complete_assets(self, complete_assets: List[AO1AssetRecord]) -> int:
        if not complete_assets:
            logging.warning("No complete assets to insert")
            return 0
        
        insert_query = """
        INSERT INTO ao1_comprehensive_cmdb (
            hostname, fqdn, ip_address, mac_address, infrastructure_type, 
            system_classification, global_region, country, data_center, cloud_region,
            business_unit, cio, apm, application_class, edr_coverage, tanium_coverage,
            dlp_coverage, in_splunk, in_chronicle, in_gso, network_log_types,
            endpoint_log_types, cloud_log_types, application_log_types, identity_log_types,
            found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike,
            source_count, host_parity_score, cmdb_asset_visibility_score,
            visibility_gap_severity, completeness_score, discovery_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
        """
        
        inserted = 0
        
        for asset in complete_assets:
            try:
                values = [
                    asset.hostname, asset.fqdn, asset.ip_address, asset.mac_address,
                    asset.infrastructure_type, asset.system_classification, asset.global_region,
                    asset.country, asset.data_center, asset.cloud_region, asset.business_unit,
                    asset.cio, asset.apm, asset.application_class, asset.edr_coverage,
                    asset.tanium_coverage, asset.dlp_coverage, asset.in_splunk, asset.in_chronicle,
                    asset.in_gso, asset.network_log_types, asset.endpoint_log_types,
                    asset.cloud_log_types, asset.application_log_types, asset.identity_log_types,
                    asset.found_in_cmdb, asset.found_in_splunk, asset.found_in_chronicle,
                    asset.found_in_crowdstrike, asset.source_count, asset.host_parity_score,
                    asset.cmdb_asset_visibility_score, asset.visibility_gap_severity,
                    asset.completeness_score
                ]
                
                self.conn.execute(insert_query, values)
                inserted += 1
                
                if inserted % 500 == 0:
                    logging.info(f"Inserted {inserted} complete assets...")
            
            except Exception as e:
                logging.error(f"Failed to insert asset {asset.hostname}: {e}")
        
        self.conn.commit()
        logging.info(f"Successfully inserted {inserted} complete, high-quality assets")
        return inserted

    def _verify_comprehensive_database(self) -> Dict[str, Any]:
        try:
            count_result = self.conn.execute("SELECT COUNT(*) FROM ao1_comprehensive_cmdb").fetchone()
            total_count = count_result[0] if count_result else 0
            
            completeness_stats = self.conn.execute("""
                SELECT 
                    AVG(completeness_score) as avg_completeness,
                    MIN(completeness_score) as min_completeness,
                    MAX(completeness_score) as max_completeness,
                    AVG(host_parity_score) as avg_parity,
                    AVG(cmdb_asset_visibility_score) as avg_cmdb_score
                FROM ao1_comprehensive_cmdb
            """).fetchone()
            
            source_coverage = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_coverage,
                    SUM(CASE WHEN found_in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                    SUM(CASE WHEN found_in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                    SUM(CASE WHEN found_in_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_coverage
                FROM ao1_comprehensive_cmdb
            """).fetchone()
            
            field_completeness = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN fqdn != '' THEN 1 ELSE 0 END) as fqdn_filled,
                    SUM(CASE WHEN ip_address != '' THEN 1 ELSE 0 END) as ip_filled,
                    SUM(CASE WHEN infrastructure_type != '' THEN 1 ELSE 0 END) as infra_filled,
                    SUM(CASE WHEN system_classification != '' THEN 1 ELSE 0 END) as system_filled,
                    SUM(CASE WHEN global_region != '' THEN 1 ELSE 0 END) as region_filled,
                    SUM(CASE WHEN business_unit != '' THEN 1 ELSE 0 END) as bu_filled
                FROM ao1_comprehensive_cmdb
            """).fetchone()
            
            sample_assets = self.conn.execute("""
                SELECT hostname, infrastructure_type, system_classification, global_region, 
                       completeness_score, found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike
                FROM ao1_comprehensive_cmdb
                ORDER BY completeness_score DESC
                LIMIT 10
            """).fetchall()
            
            return {
                'total_records': total_count,
                'quality_metrics': {
                    'avg_completeness': round(completeness_stats[0], 2) if completeness_stats[0] else 0,
                    'min_completeness': round(completeness_stats[1], 2) if completeness_stats[1] else 0,
                    'max_completeness': round(completeness_stats[2], 2) if completeness_stats[2] else 0,
                    'avg_parity_score': round(completeness_stats[3], 2) if completeness_stats[3] else 0,
                    'avg_cmdb_score': round(completeness_stats[4], 2) if completeness_stats[4] else 0
                },
                'source_coverage': {
                    'cmdb': source_coverage[0],
                    'splunk': source_coverage[1], 
                    'chronicle': source_coverage[2],
                    'crowdstrike': source_coverage[3]
                },
                'field_completeness': {
                    'fqdn_filled': field_completeness[0],
                    'ip_filled': field_completeness[1],
                    'infrastructure_filled': field_completeness[2],
                    'system_filled': field_completeness[3],
                    'region_filled': field_completeness[4],
                    'business_unit_filled': field_completeness[5]
                },
                'top_quality_assets': sample_assets
            }
        
        except Exception as e:
            logging.error(f"Verification failed: {e}")
            return {'error': str(e)}

    def get_comprehensive_queries(self) -> Dict[str, str]:
        return {
            'quality_summary': """
                SELECT 
                    COUNT(*) as total_assets,
                    ROUND(AVG(completeness_score), 2) as avg_completeness,
                    ROUND(AVG(host_parity_score), 2) as avg_parity,
                    COUNT(CASE WHEN completeness_score >= 80 THEN 1 END) as high_quality_assets,
                    COUNT(CASE WHEN source_count >= 3 THEN 1 END) as multi_source_assets
                FROM ao1_comprehensive_cmdb;
            """,
            
            'source_distribution': """
                SELECT 
                    source_count,
                    COUNT(*) as asset_count,
                    ROUND(AVG(completeness_score), 2) as avg_completeness
                FROM ao1_comprehensive_cmdb
                GROUP BY source_count
                ORDER BY source_count DESC;
            """,
            
            'infrastructure_analysis': """
                SELECT 
                    infrastructure_type,
                    COUNT(*) as count,
                    ROUND(AVG(completeness_score), 2) as avg_completeness,
                    SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as in_cmdb,
                    SUM(CASE WHEN edr_coverage = 'Yes' THEN 1 ELSE 0 END) as edr_protected
                FROM ao1_comprehensive_cmdb
                WHERE infrastructure_type != ''
                GROUP BY infrastructure_type
                ORDER BY count DESC;
            """,
            
            'missing_from_cmdb': """
                SELECT hostname, infrastructure_type, system_classification, source_count
                FROM ao1_comprehensive_cmdb
                WHERE NOT found_in_cmdb AND (found_in_splunk OR found_in_chronicle OR found_in_crowdstrike)
                ORDER BY source_count DESC, completeness_score DESC
                LIMIT 100;
            """
        }

    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()