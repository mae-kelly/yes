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
    last_updated: str = ""

class UltraIntelligentFieldDetector:
    def __init__(self):
        self.conservative_patterns = {
            'hostname': {
                'exact_names': ['hostname', 'host_name', 'computername', 'computer_name', 'endpoint_name'],
                'content_validators': [self._is_hostname_content]
            },
            'fqdn': {
                'exact_names': ['fqdn', 'full_qualified_domain_name', 'dns_name', 'domain_name'],
                'content_validators': [self._is_fqdn_content]
            },
            'ip_address': {
                'exact_names': ['ip_address', 'ip_addr', 'ipaddress', 'host_ip', 'endpoint_ip'],
                'content_validators': [self._is_ip_content]
            },
            'mac_address': {
                'exact_names': ['mac_address', 'mac_addr', 'macaddress', 'physical_address'],
                'content_validators': [self._is_mac_content]
            },
            'infrastructure_type': {
                'exact_names': ['infrastructure_type', 'infra_type', 'platform_type', 'deployment_type'],
                'content_validators': [self._is_infrastructure_content]
            },
            'system_classification': {
                'exact_names': ['system_classification', 'os_type', 'operating_system', 'platform'],
                'content_validators': [self._is_system_classification_content]
            },
            'global_region': {
                'exact_names': ['global_region', 'region', 'geo_region', 'geographic_region'],
                'content_validators': [self._is_region_content]
            },
            'country': {
                'exact_names': ['country', 'country_code', 'nation'],
                'content_validators': [self._is_country_content]
            },
            'business_unit': {
                'exact_names': ['business_unit', 'bu', 'organization', 'org_unit'],
                'content_validators': [self._is_business_unit_content]
            },
            'edr_coverage': {
                'exact_names': ['crowdstrike_status', 'edr_status', 'cs_agent', 'falcon_status'],
                'content_validators': [self._is_coverage_content]
            }
        }
    
    def _is_hostname_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        hostname_count = 0
        for value in values[:20]:
            if self._validate_hostname(value):
                hostname_count += 1
        
        return hostname_count / min(len(values), 20)
    
    def _is_fqdn_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        fqdn_count = 0
        for value in values[:20]:
            if self._validate_fqdn(value):
                fqdn_count += 1
        
        return fqdn_count / min(len(values), 20)
    
    def _is_ip_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        ip_count = 0
        for value in values[:20]:
            if self._validate_ip(value):
                ip_count += 1
        
        return ip_count / min(len(values), 20)
    
    def _is_mac_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        mac_count = 0
        for value in values[:20]:
            if self._validate_mac(value):
                mac_count += 1
        
        return mac_count / min(len(values), 20)
    
    def _is_infrastructure_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        infra_keywords = ['cloud', 'on-prem', 'saas', 'api', 'physical', 'virtual', 'aws', 'azure', 'gcp']
        match_count = 0
        
        for value in values[:20]:
            if any(keyword in str(value).lower() for keyword in infra_keywords):
                match_count += 1
        
        return match_count / min(len(values), 20)
    
    def _is_system_classification_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        os_keywords = ['windows', 'linux', 'unix', 'server', 'workstation', 'database', 'web']
        match_count = 0
        
        for value in values[:20]:
            if any(keyword in str(value).lower() for keyword in os_keywords):
                match_count += 1
        
        return match_count / min(len(values), 20)
    
    def _is_region_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        region_keywords = ['us', 'eu', 'apac', 'america', 'europe', 'asia', 'north', 'south', 'east', 'west']
        match_count = 0
        
        for value in values[:20]:
            if any(keyword in str(value).lower() for keyword in region_keywords):
                match_count += 1
        
        return match_count / min(len(values), 20)
    
    def _is_country_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        country_keywords = ['usa', 'canada', 'uk', 'germany', 'france', 'japan', 'australia']
        match_count = 0
        
        for value in values[:20]:
            value_str = str(value).lower()
            if any(keyword in value_str for keyword in country_keywords) or len(value_str) == 2:
                match_count += 1
        
        return match_count / min(len(values), 20)
    
    def _is_business_unit_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        bu_keywords = ['finance', 'marketing', 'sales', 'operations', 'hr', 'it', 'engineering']
        match_count = 0
        
        for value in values[:20]:
            if any(keyword in str(value).lower() for keyword in bu_keywords):
                match_count += 1
        
        return match_count / min(len(values), 20)
    
    def _is_coverage_content(self, values: List[str]) -> float:
        if not values:
            return 0.0
        
        coverage_keywords = ['yes', 'no', 'true', 'false', 'enabled', 'disabled', 'active', 'inactive']
        match_count = 0
        
        for value in values[:20]:
            if str(value).lower() in coverage_keywords:
                match_count += 1
        
        return match_count / min(len(values), 20)
    
    def _validate_hostname(self, value: str) -> bool:
        if not value or not isinstance(value, str):
            return False
        
        value = str(value).strip()
        if len(value) < 2 or len(value) > 253:
            return False
        
        if value.upper() in ['UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY']:
            return False
        
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', value):
            return False
        
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', value) or re.match(r'^[a-zA-Z0-9]+$', value):
            return True
        
        return False
    
    def _validate_fqdn(self, value: str) -> bool:
        if not value or not isinstance(value, str):
            return False
        
        value = str(value).strip()
        if '.' not in value or len(value) < 4:
            return False
        
        return re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', value) is not None
    
    def _validate_ip(self, value: str) -> bool:
        if not value:
            return False
        
        try:
            ipaddress.ip_address(str(value).strip())
            return True
        except:
            return False
    
    def _validate_mac(self, value: str) -> bool:
        if not value:
            return False
        
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$'
        ]
        
        return any(re.match(pattern, str(value).strip()) for pattern in mac_patterns)
    
    def analyze_column(self, column_name: str, sample_values: List[str]) -> Dict[str, float]:
        results = {}
        column_lower = column_name.lower()
        
        for field_type, config in self.conservative_patterns.items():
            score = 0.0
            
            if any(exact_name == column_lower for exact_name in config['exact_names']):
                score = 10.0
            elif any(exact_name in column_lower for exact_name in config['exact_names']):
                score = 5.0
            
            if config['content_validators'] and sample_values:
                for validator in config['content_validators']:
                    content_score = validator(sample_values)
                    if content_score > 0.7:
                        score += 8.0
                    elif content_score > 0.5:
                        score += 5.0
                    elif content_score > 0.3:
                        score += 2.0
            
            if score > 0:
                results[field_type] = score
        
        return results

class UltraIntelligentAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        self.field_detector = UltraIntelligentFieldDetector()
        
        from gcp_client import BigQueryClientManager
        self.client_manager = BigQueryClientManager(project_id)
        
        try:
            self.chronicle_client_manager = BigQueryClientManager("chronicle-fisv")
        except:
            self.chronicle_client_manager = None
            logging.warning("Chronicle access not available")
        
        self.db_path = self.config.get('database_path', 'ao1_ultra_intelligent.db')
        self.conn = duckdb.connect(self.db_path)
        self._setup_ultra_schema()
        
        self.known_tables = {
            'cmdb': 'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'splunk': 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'crowdstrike': 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT',
            'chronicle': 'chronicle-fisv.datalake.events'
        }
        
        logging.info(f"UltraIntelligentAO1Discovery initialized with known tables: {list(self.known_tables.keys())}")
    
    def _setup_ultra_schema(self):
        self.conn.execute("DROP TABLE IF EXISTS ao1_ultra_assets")
        
        self.conn.execute("""
            CREATE TABLE ao1_ultra_assets (
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
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logging.info("Created ao1_ultra_assets table")
    
    def discover_and_populate_ultra_intelligent(self) -> Dict[str, Any]:
        logging.info("Starting ultra-intelligent AO1 discovery")
        
        master_assets = {}
        tables_processed = 0
        
        for source_name, table_path in self.known_tables.items():
            logging.info(f"Processing {source_name} table: {table_path}")
            
            try:
                if source_name == 'chronicle' and self.chronicle_client_manager:
                    client_manager = self.chronicle_client_manager
                else:
                    client_manager = self.client_manager
                
                table_data = self._analyze_and_extract_from_table(client_manager, table_path, source_name)
                
                if table_data:
                    logging.info(f"Extracted {len(table_data)} records from {source_name}")
                    
                    for hostname, asset_data in table_data.items():
                        if hostname not in master_assets:
                            master_assets[hostname] = AO1AssetRecord(hostname=hostname)
                        
                        self._merge_asset_data_intelligently(master_assets[hostname], asset_data, source_name)
                    
                    tables_processed += 1
                else:
                    logging.warning(f"No data extracted from {source_name}")
            
            except Exception as e:
                logging.error(f"Failed to process {source_name}: {e}")
                continue
        
        if not master_assets:
            return {'error': 'No assets discovered from any table', 'total_assets': 0}
        
        for asset in master_assets.values():
            self._calculate_asset_scores(asset)
        
        inserted_count = self._upsert_assets_intelligently(list(master_assets.values()))
        
        verification = self._verify_ultra_database()
        
        return {
            'total_assets': len(master_assets),
            'inserted_count': inserted_count,
            'tables_processed': tables_processed,
            'database_path': self.db_path,
            'verification': verification
        }
    
    def _analyze_and_extract_from_table(self, client_manager, table_path: str, source_name: str) -> Dict[str, Dict[str, Any]]:
        try:
            with client_manager.get_client() as client:
                table_ref = client.get_table(table_path)
                
                if not table_ref.schema or table_ref.num_rows == 0:
                    logging.warning(f"Table {table_path} is empty or has no schema")
                    return {}
                
                columns = [field.name for field in table_ref.schema]
                logging.info(f"Analyzing {len(columns)} columns in {table_path}")
                
                schema_analysis = self._sample_and_analyze_schema(client, table_path, columns)
                
                field_mappings = self._create_field_mappings(schema_analysis)
                
                if 'hostname' not in field_mappings:
                    logging.warning(f"No hostname field found in {table_path}")
                    return {}
                
                return self._extract_all_data_from_table(client, table_path, field_mappings)
        
        except Exception as e:
            logging.error(f"Failed to analyze table {table_path}: {e}")
            return {}
    
    def _sample_and_analyze_schema(self, client, table_path: str, columns: List[str]) -> Dict[str, Dict[str, Any]]:
        sample_query = f"""
        SELECT {', '.join([f'`{col}`' for col in columns[:50]])}
        FROM `{table_path}`
        WHERE RAND() < 0.001
        LIMIT 100
        """
        
        schema_analysis = {}
        
        try:
            job = client.query(sample_query)
            results = list(job.result())
            
            for col_idx, column_name in enumerate(columns[:50]):
                sample_values = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        sample_values.append(str(row[col_idx]))
                
                if sample_values:
                    field_scores = self.field_detector.analyze_column(column_name, sample_values)
                    if field_scores:
                        schema_analysis[column_name] = {
                            'field_scores': field_scores,
                            'sample_values': sample_values[:10]
                        }
        
        except Exception as e:
            logging.error(f"Failed to sample schema for {table_path}: {e}")
        
        return schema_analysis
    
    def _create_field_mappings(self, schema_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        field_mappings = {}
        
        field_candidates = defaultdict(list)
        
        for column_name, analysis in schema_analysis.items():
            for field_type, score in analysis['field_scores'].items():
                if score >= 5.0:
                    field_candidates[field_type].append((column_name, score))
        
        for field_type, candidates in field_candidates.items():
            if candidates:
                best_candidate = max(candidates, key=lambda x: x[1])
                field_mappings[field_type] = best_candidate[0]
                logging.info(f"Mapped {field_type} to {best_candidate[0]} (score: {best_candidate[1]:.1f})")
        
        return field_mappings
    
    def _extract_all_data_from_table(self, client, table_path: str, field_mappings: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
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
        LIMIT 50000
        """
        
        extracted_data = {}
        
        try:
            job = client.query(query)
            results = list(job.result())
            
            for row in results:
                hostname = row[0] if row[0] else None
                
                if hostname and self.field_detector._validate_hostname(hostname):
                    asset_data = {'hostname': hostname}
                    
                    for idx, (field_type, _) in enumerate(field_mappings.items()):
                        if field_type != 'hostname' and idx < len(row) and row[idx]:
                            asset_data[field_type] = str(row[idx]).strip()
                    
                    extracted_data[hostname] = asset_data
        
        except Exception as e:
            logging.error(f"Failed to extract data from {table_path}: {e}")
        
        return extracted_data
    
    def _merge_asset_data_intelligently(self, asset: AO1AssetRecord, new_data: Dict[str, Any], source_name: str):
        for field_name, new_value in new_data.items():
            if field_name == 'hostname' or not new_value:
                continue
            
            if hasattr(asset, field_name):
                current_value = getattr(asset, field_name)
                
                if not current_value or current_value in ['', 'No', 'unknown', 'Unknown']:
                    setattr(asset, field_name, new_value)
                elif current_value != new_value and new_value not in ['', 'No', 'unknown', 'Unknown']:
                    if len(str(new_value)) > len(str(current_value)):
                        setattr(asset, field_name, new_value)
        
        if source_name == 'cmdb':
            asset.found_in_cmdb = True
        elif source_name == 'splunk':
            asset.found_in_splunk = True
            asset.in_splunk = True
        elif source_name == 'chronicle':
            asset.found_in_chronicle = True
            asset.in_chronicle = True
        elif source_name == 'crowdstrike':
            asset.found_in_crowdstrike = True
            asset.edr_coverage = 'Yes'
        
        asset.last_updated = datetime.now().isoformat()
    
    def _calculate_asset_scores(self, asset: AO1AssetRecord):
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
        if asset.infrastructure_type and asset.infrastructure_type != '':
            cmdb_score += 30.0
        if asset.system_classification and asset.system_classification != '':
            cmdb_score += 30.0
        
        asset.cmdb_asset_visibility_score = cmdb_score
        
        if asset.host_parity_score >= 75:
            asset.visibility_gap_severity = 'low'
        elif asset.host_parity_score >= 50:
            asset.visibility_gap_severity = 'medium'
        elif asset.host_parity_score >= 25:
            asset.visibility_gap_severity = 'high'
        else:
            asset.visibility_gap_severity = 'critical'
    
    def _upsert_assets_intelligently(self, assets: List[AO1AssetRecord]) -> int:
        if not assets:
            return 0
        
        upsert_query = """
        INSERT OR REPLACE INTO ao1_ultra_assets (
            hostname, fqdn, ip_address, mac_address, infrastructure_type, 
            system_classification, global_region, country, data_center, cloud_region,
            business_unit, cio, apm, application_class, edr_coverage, tanium_coverage,
            dlp_coverage, in_splunk, in_chronicle, in_gso, network_log_types,
            endpoint_log_types, cloud_log_types, application_log_types, identity_log_types,
            found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike,
            source_count, host_parity_score, cmdb_asset_visibility_score,
            visibility_gap_severity, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
        """
        
        inserted = 0
        
        for asset in assets:
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
                    asset.cmdb_asset_visibility_score, asset.visibility_gap_severity
                ]
                
                self.conn.execute(upsert_query, values)
                inserted += 1
            
            except Exception as e:
                logging.error(f"Failed to upsert asset {asset.hostname}: {e}")
        
        self.conn.commit()
        logging.info(f"Successfully upserted {inserted} assets")
        return inserted
    
    def _verify_ultra_database(self) -> Dict[str, Any]:
        try:
            count_result = self.conn.execute("SELECT COUNT(*) FROM ao1_ultra_assets").fetchone()
            total_count = count_result[0] if count_result else 0
            
            sample_result = self.conn.execute("""
                SELECT hostname, infrastructure_type, global_region, edr_coverage, 
                       found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike
                FROM ao1_ultra_assets LIMIT 10
            """).fetchall()
            
            coverage_stats = self.conn.execute("""
                SELECT 
                    SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_count,
                    SUM(CASE WHEN found_in_splunk THEN 1 ELSE 0 END) as splunk_count,
                    SUM(CASE WHEN found_in_chronicle THEN 1 ELSE 0 END) as chronicle_count,
                    SUM(CASE WHEN found_in_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_count,
                    AVG(host_parity_score) as avg_parity_score,
                    AVG(cmdb_asset_visibility_score) as avg_cmdb_score
                FROM ao1_ultra_assets
            """).fetchone()
            
            gap_analysis = self.conn.execute("""
                SELECT visibility_gap_severity, COUNT(*) as count
                FROM ao1_ultra_assets
                GROUP BY visibility_gap_severity
                ORDER BY 
                    CASE visibility_gap_severity 
                        WHEN 'critical' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        WHEN 'low' THEN 4 
                    END
            """).fetchall()
            
            return {
                'total_records': total_count,
                'sample_records': sample_result,
                'coverage_statistics': {
                    'cmdb_coverage': coverage_stats[0],
                    'splunk_coverage': coverage_stats[1],
                    'chronicle_coverage': coverage_stats[2],
                    'crowdstrike_coverage': coverage_stats[3],
                    'avg_parity_score': round(coverage_stats[4], 2) if coverage_stats[4] else 0,
                    'avg_cmdb_score': round(coverage_stats[5], 2) if coverage_stats[5] else 0
                },
                'gap_analysis': gap_analysis
            }
        
        except Exception as e:
            logging.error(f"Database verification failed: {e}")
            return {'error': str(e)}
    
    def get_ultra_queries(self) -> Dict[str, str]:
        return {
            'ao1_summary': """
                SELECT 
                    COUNT(*) as total_assets,
                    AVG(host_parity_score) as avg_host_parity,
                    AVG(cmdb_asset_visibility_score) as avg_cmdb_visibility,
                    SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_assets,
                    SUM(CASE WHEN found_in_splunk THEN 1 ELSE 0 END) as splunk_assets,
                    SUM(CASE WHEN found_in_chronicle THEN 1 ELSE 0 END) as chronicle_assets,
                    SUM(CASE WHEN found_in_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_assets
                FROM ao1_ultra_assets;
            """,
            
            'visibility_gaps_detailed': """
                SELECT 
                    visibility_gap_severity,
                    COUNT(*) as asset_count,
                    ROUND(AVG(host_parity_score), 2) as avg_parity,
                    ROUND(AVG(cmdb_asset_visibility_score), 2) as avg_cmdb_score,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ao1_ultra_assets), 2) as percentage
                FROM ao1_ultra_assets
                GROUP BY visibility_gap_severity
                ORDER BY asset_count DESC;
            """,
            
            'missing_cmdb_critical': """
                SELECT hostname, infrastructure_type, global_region, edr_coverage
                FROM ao1_ultra_assets
                WHERE NOT found_in_cmdb AND (found_in_splunk OR found_in_chronicle OR found_in_crowdstrike)
                ORDER BY host_parity_score DESC
                LIMIT 50;
            """,
            
            'multi_source_assets': """
                SELECT hostname, infrastructure_type, global_region, source_count,
                       found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike
                FROM ao1_ultra_assets
                WHERE source_count >= 2
                ORDER BY source_count DESC, host_parity_score DESC
                LIMIT 100;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()