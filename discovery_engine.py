#!/usr/bin/env python3

import asyncio
import logging
import duckdb
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
import statistics
import ipaddress

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
    url_fqdn_coverage: str = "No"
    public_ip_coverage: str = "No"
    network_zones: str = ""
    ipam_coverage: str = "No"
    geolocation: str = ""
    vpc: str = ""
    internal_external: str = ""
    host_parity_score: float = 0.0
    cmdb_asset_visibility_score: float = 0.0
    network_log_types: str = ""
    endpoint_log_types: str = ""
    cloud_log_types: str = ""
    application_log_types: str = ""
    identity_log_types: str = ""
    found_in_cmdb: bool = None
    found_in_splunk: bool = None
    found_in_chronicle: bool = None
    found_in_crowdstrike: bool = None
    source_count: int = 0
    data_completeness_score: float = 0.0
    visibility_gap_severity: str = "unknown"

class SmartHostnameDetector:
    def __init__(self):
        self.exact_hostname_patterns = [
            'hostname', 'host_name', 'computername', 'computer_name', 'machine_name', 
            'device_name', 'endpoint_name', 'server_name', 'asset_name', 'node_name', 
            'system_name', 'workstation_name', 'appliance_name'
        ]
        
        self.fqdn_patterns = [
            'fqdn', 'full_qualified_domain_name', 'dns_name', 'domain_name',
            'canonical_name', 'qualified_name', 'full_dns_name'
        ]
        
        self.partial_hostname_patterns = [
            'host', 'endpoint', 'computer', 'device', 'server', 'machine', 
            'asset', 'node', 'system', 'workstation', 'appliance', 'vm', 'instance'
        ]
        
        self.security_context_patterns = [
            'crowdstrike_hostname', 'cs_hostname', 'falcon_hostname', 'falcon_device',
            'splunk_host', 'chronicle_hostname', 'cmdb_hostname', 'cmdb_device',
            'agent_hostname', 'sensor_hostname', 'client_name', 'device_id'
        ]
        
        self.network_context_patterns = [
            'src_host', 'dst_host', 'source_host', 'destination_host',
            'origin_host', 'target_host', 'peer_host', 'remote_host'
        ]
        
        self.invalid_indicators = [
            'id', 'key', 'guid', 'uuid', 'token', 'hash', 'count', 'total',
            'sum', 'avg', 'created', 'updated', 'modified', 'deleted',
            'timestamp', 'date', 'time', 'status', 'state', 'flag'
        ]
        
        self.hostname_validation_regex = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]{1,251}[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]{1,63}$',
            r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$',
            r'^[a-zA-Z]{2,}[0-9]{1,}[a-zA-Z0-9\-]*$',
            r'^[a-zA-Z0-9]+[-_][a-zA-Z0-9]+',
            r'^(srv|web|app|db|sql|win|linux|vm|dc|fw)[0-9]+',
        ]
        
        self.invalid_value_patterns = [
            r'^\d+\.\d+\.\d+\.\d+$',
            r'^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}',
            r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}',
            r'^https?://',
            r'^\d+$',
            r'^null$|^none$|^unknown$|^n\/a$|^empty$'
        ]
        
        self.enterprise_hostname_indicators = [
            'prod', 'dev', 'test', 'stage', 'uat', 'qa', 'dr',
            'srv', 'web', 'app', 'db', 'sql', 'dc', 'fw', 'lb',
            'win', 'linux', 'rhel', 'ubuntu', 'centos', 'aix'
        ]

    def analyze_column_for_hostnames(self, column_name: str, sample_values: List[str]) -> float:
        if not column_name or not sample_values:
            return 0.0
        
        column_lower = column_name.lower().replace('_', '').replace('-', '').replace(' ', '')
        
        if any(invalid in column_lower for invalid in self.invalid_indicators):
            return 0.0
        
        score = 0.0
        
        for exact_pattern in self.exact_hostname_patterns:
            exact_clean = exact_pattern.replace('_', '').replace('-', '')
            if exact_clean == column_lower:
                score += 10.0
            elif exact_clean in column_lower:
                score += 8.0
        
        for fqdn_pattern in self.fqdn_patterns:
            fqdn_clean = fqdn_pattern.replace('_', '').replace('-', '')
            if fqdn_clean == column_lower:
                score += 9.0
            elif fqdn_clean in column_lower:
                score += 7.0
        
        for partial_pattern in self.partial_hostname_patterns:
            if partial_pattern in column_lower and len(column_lower) < 20:
                score += 5.0
        
        for security_pattern in self.security_context_patterns:
            security_clean = security_pattern.replace('_', '').replace('-', '')
            if security_clean in column_lower:
                score += 6.0
        
        for network_pattern in self.network_context_patterns:
            network_clean = network_pattern.replace('_', '').replace('-', '')
            if network_clean in column_lower:
                score += 4.0
        
        if 'name' in column_lower and len(column_lower) < 15:
            score += 3.0
        
        cleaned_values = [str(v).strip() for v in sample_values if v and str(v).strip()]
        if not cleaned_values:
            return score * 0.1
        
        valid_hostname_count = 0
        enterprise_pattern_count = 0
        
        for value in cleaned_values[:20]:
            if self.is_valid_hostname_value(value):
                valid_hostname_count += 1
                
                if any(indicator in value.lower() for indicator in self.enterprise_hostname_indicators):
                    enterprise_pattern_count += 1
        
        if cleaned_values:
            validation_ratio = valid_hostname_count / len(cleaned_values[:20])
            enterprise_ratio = enterprise_pattern_count / len(cleaned_values[:20])
            
            score *= validation_ratio
            score += enterprise_ratio * 2.0
        
        return min(score, 15.0)
    
    def is_valid_hostname_value(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 2 or len(value) > 253:
            return False
        
        value_clean = value.strip().upper()
        
        if value_clean in ['UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY', '', 'NAN', 'LOCALHOST']:
            return False
        
        for invalid_pattern in self.invalid_value_patterns:
            if re.match(invalid_pattern, value, re.IGNORECASE):
                return False
        
        if value.count('.') > 10 or value.count('-') > 10:
            return False
        
        for valid_pattern in self.hostname_validation_regex:
            if re.match(valid_pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def find_best_hostname_columns(self, table_schema: Dict[str, List[str]]) -> List[Tuple[str, float]]:
        column_scores = []
        
        for column_name, sample_values in table_schema.items():
            score = self.analyze_column_for_hostnames(column_name, sample_values)
            if score > 2.0:
                column_scores.append((column_name, score))
        
        return sorted(column_scores, key=lambda x: x[1], reverse=True)

class IntelligentFieldMapper:
    def __init__(self):
        self.field_patterns = {
            'infrastructure_type': {
                'columns': ['infrastructure_type', 'infra_type', 'platform_type', 'deployment_type', 'env_type'],
                'values': {
                    'on-prem': ['onprem', 'on-prem', 'on-premises', 'physical', 'bare', 'metal'],
                    'cloud': ['cloud', 'aws', 'azure', 'gcp', 'ec2', 'vm'],
                    'saas': ['saas', 'software', 'service', 'managed'],
                    'api': ['api', 'interface', 'gateway', 'endpoint']
                }
            },
            'system_classification': {
                'columns': ['system_classification', 'os_type', 'platform', 'system_type', 'device_type'],
                'values': {
                    'windows_server': ['windows', 'win', 'microsoft', 'server'],
                    'linux_server': ['linux', 'unix', 'centos', 'ubuntu', 'rhel', 'nix'],
                    'web_server': ['web', 'apache', 'nginx', 'iis', 'http'],
                    'database': ['database', 'db', 'sql', 'oracle', 'mysql', 'postgres'],
                    'mainframe': ['mainframe', 'mf', 'zos', 'mvs'],
                    'appliance': ['appliance', 'firewall', 'switch', 'router', 'device']
                }
            },
            'global_region': {
                'columns': ['region', 'global_region', 'geo_region', 'area', 'location'],
                'values': {
                    'us': ['us', 'usa', 'america', 'north america', 'united states'],
                    'eu': ['eu', 'europe', 'emea', 'european'],
                    'apac': ['ap', 'asia', 'pacific', 'apac', 'asian']
                }
            },
            'business_unit': {
                'columns': ['business_unit', 'bu', 'org', 'organization', 'department', 'division'],
                'values': {}
            },
            'edr_coverage': {
                'columns': ['crowdstrike', 'edr', 'endpoint_protection', 'cs_agent', 'falcon'],
                'values': {
                    'yes': ['true', 'yes', 'enabled', 'active', 'installed', 'protected'],
                    'no': ['false', 'no', 'disabled', 'inactive', 'uninstalled', 'unprotected']
                }
            },
            'network_log_types': {
                'columns': ['log_type', 'source_type', 'event_type', 'data_source'],
                'values': {
                    'firewall': ['firewall', 'fw', 'palo', 'checkpoint', 'fortinet'],
                    'ids_ips': ['ids', 'ips', 'intrusion'],
                    'proxy': ['proxy', 'web_proxy', 'squid'],
                    'dns': ['dns', 'domain'],
                    'waf': ['waf', 'web_application_firewall']
                }
            }
        }
    
    def map_field_value(self, field_type: str, raw_value: str) -> str:
        if not raw_value or field_type not in self.field_patterns:
            return ""
        
        raw_lower = str(raw_value).lower().strip()
        field_config = self.field_patterns[field_type]
        
        for canonical_value, variants in field_config.get('values', {}).items():
            if raw_lower in variants or any(variant in raw_lower for variant in variants):
                return canonical_value.replace('_', ' ').title()
        
        return raw_value
    
    def find_field_columns(self, table_schema: Dict[str, List[str]], field_type: str) -> List[Tuple[str, float]]:
        if field_type not in self.field_patterns:
            return []
        
        field_config = self.field_patterns[field_type]
        column_candidates = []
        
        for column_name, sample_values in table_schema.items():
            score = 0.0
            column_lower = column_name.lower()
            
            for pattern in field_config['columns']:
                if pattern in column_lower:
                    score += 5.0
                elif any(part in column_lower for part in pattern.split('_')):
                    score += 2.0
            
            if field_config.get('values') and sample_values:
                value_matches = 0
                for value in sample_values[:10]:
                    if value:
                        value_lower = str(value).lower()
                        for canonical, variants in field_config['values'].items():
                            if any(variant in value_lower for variant in variants):
                                value_matches += 1
                                break
                
                if sample_values:
                    value_ratio = value_matches / min(len(sample_values), 10)
                    score += value_ratio * 3.0
            
            if score > 1.0:
                column_candidates.append((column_name, score))
        
        return sorted(column_candidates, key=lambda x: x[1], reverse=True)

class AdvancedAO1Discovery:
    def __init__(self, project_id: str, config: Dict[str, Any] = None):
        self.project_id = project_id
        self.config = config or {}
        self.hostname_detector = SmartHostnameDetector()
        self.field_mapper = IntelligentFieldMapper()
        
        try:
            from gcp_client import BigQueryClientManager
            self.client_manager = BigQueryClientManager(project_id)
        except ImportError:
            raise ImportError("BigQueryClientManager not available")
        
        self.db_path = self.config.get('database_path', 'ao1_enhanced_cmdb.db')
        self.conn = duckdb.connect(self.db_path)
        self._setup_ao1_schema()
    
    def _setup_ao1_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ao1_asset_visibility (
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
                url_fqdn_coverage VARCHAR DEFAULT 'No',
                public_ip_coverage VARCHAR DEFAULT 'No',
                network_zones VARCHAR DEFAULT '',
                ipam_coverage VARCHAR DEFAULT 'No',
                geolocation VARCHAR DEFAULT '',
                vpc VARCHAR DEFAULT '',
                internal_external VARCHAR DEFAULT '',
                host_parity_score DOUBLE DEFAULT 0.0,
                cmdb_asset_visibility_score DOUBLE DEFAULT 0.0,
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
                data_completeness_score DOUBLE DEFAULT 0.0,
                visibility_gap_severity VARCHAR DEFAULT 'unknown',
                discovery_timestamp TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_hostname_ao1 ON ao1_asset_visibility(hostname)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_source_systems ON ao1_asset_visibility(found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_visibility_gaps ON ao1_asset_visibility(visibility_gap_severity, host_parity_score)")
        
        self.conn.commit()
    
    async def discover_tables_with_hostnames(self) -> List[Dict[str, Any]]:
        discovered_tables = []
        
        try:
            with self.client_manager.get_client() as client:
                datasets = list(client.list_datasets(project=self.project_id))
                
                for dataset in datasets:
                    dataset_ref = client.dataset(dataset.dataset_id)
                    tables = list(client.list_tables(dataset_ref))
                    
                    for table_ref in tables:
                        try:
                            full_table = client.get_table(table_ref)
                            
                            if not full_table.schema or full_table.num_rows == 0:
                                continue
                            
                            table_path = f"{self.project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                            
                            schema_sample = await self._sample_table_schema(client, table_path, full_table.schema)
                            
                            hostname_candidates = self.hostname_detector.find_best_hostname_columns(schema_sample)
                            
                            if hostname_candidates and hostname_candidates[0][1] > 3.0:
                                best_hostname_col = hostname_candidates[0][0]
                                
                                source_system = self._identify_source_system(table_path, dataset.dataset_id)
                                
                                field_mappings = {}
                                for field_type in ['infrastructure_type', 'system_classification', 'global_region', 
                                                 'business_unit', 'edr_coverage', 'network_log_types']:
                                    field_candidates = self.field_mapper.find_field_columns(schema_sample, field_type)
                                    if field_candidates:
                                        field_mappings[field_type] = field_candidates[0][0]
                                
                                discovered_tables.append({
                                    'table_path': table_path,
                                    'dataset_id': dataset.dataset_id,
                                    'table_id': table_ref.table_id,
                                    'hostname_column': best_hostname_col,
                                    'hostname_score': hostname_candidates[0][1],
                                    'row_count': full_table.num_rows,
                                    'source_system': source_system,
                                    'field_mappings': field_mappings,
                                    'all_columns': list(schema_sample.keys())
                                })
                                
                        except Exception as e:
                            logging.warning(f"Failed to analyze table {table_ref.table_id}: {e}")
                            continue
        
        except Exception as e:
            logging.error(f"Failed to discover tables: {e}")
            raise
        
        return discovered_tables
    
    async def _sample_table_schema(self, client, table_path: str, schema) -> Dict[str, List[str]]:
        columns = [field.name for field in schema]
        column_samples = {}
        
        sample_query = f"""
        SELECT {', '.join([f'`{col}`' for col in columns[:50]])}
        FROM `{table_path}`
        WHERE RAND() < 0.01
        LIMIT 100
        """
        
        try:
            job = client.query(sample_query)
            results = list(job.result())
            
            for col_idx, col_name in enumerate(columns[:50]):
                samples = []
                for row in results:
                    if col_idx < len(row) and row[col_idx] is not None:
                        samples.append(str(row[col_idx]))
                
                column_samples[col_name] = samples[:20]
        
        except Exception as e:
            logging.warning(f"Failed to sample {table_path}: {e}")
            for col_name in columns:
                column_samples[col_name] = []
        
        return column_samples
    
    def _identify_source_system(self, table_path: str, dataset_id: str) -> str:
        path_lower = table_path.lower()
        dataset_lower = dataset_id.lower()
        
        if any(indicator in path_lower for indicator in ['crowdstrike', 'cs_', 'falcon', 'edr']):
            return 'crowdstrike'
        elif any(indicator in path_lower for indicator in ['splunk', 'spl_', 'search']):
            return 'splunk'  
        elif any(indicator in path_lower for indicator in ['chronicle', 'chr_', 'security']):
            return 'chronicle'
        elif any(indicator in path_lower for indicator in ['cmdb', 'asset', 'inventory', 'config']):
            return 'cmdb'
        elif any(indicator in path_lower for indicator in ['gso', 'operations']):
            return 'gso'
        else:
            return 'unknown'
    
    async def extract_and_enrich_assets(self, discovered_tables: List[Dict[str, Any]]) -> int:
        all_assets = {}
        
        for table_info in discovered_tables:
            table_assets = await self._extract_assets_from_table(table_info)
            
            for hostname, asset_data in table_assets.items():
                if hostname not in all_assets:
                    all_assets[hostname] = AO1AssetRecord(hostname=hostname)
                
                self._merge_asset_data(all_assets[hostname], asset_data, table_info['source_system'])
        
        populated_assets = []
        for hostname, asset in all_assets.items():
            self._calculate_asset_scores(asset)
            populated_assets.append(asset)
        
        return await self._store_assets_in_db(populated_assets)
    
    async def _extract_assets_from_table(self, table_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        hostname_col = table_info['hostname_column']
        table_path = table_info['table_path']
        field_mappings = table_info['field_mappings']
        
        select_columns = [f"DISTINCT UPPER(TRIM(`{hostname_col}`)) as hostname"]
        
        for field_type, column_name in field_mappings.items():
            select_columns.append(f"`{column_name}` as {field_type}")
        
        query = f"""
        SELECT {', '.join(select_columns)}
        FROM `{table_path}`
        WHERE `{hostname_col}` IS NOT NULL
        AND LENGTH(TRIM(`{hostname_col}`)) >= 2
        AND LENGTH(TRIM(`{hostname_col}`)) <= 253
        AND UPPER(TRIM(`{hostname_col}`)) NOT IN ('UNKNOWN', 'NULL', 'N/A', 'NONE', 'EMPTY')
        AND TRIM(`{hostname_col}`) NOT LIKE '%@%'
        AND TRIM(`{hostname_col}`) NOT LIKE 'http%'
        LIMIT 50000
        """
        
        assets = {}
        
        try:
            with self.client_manager.get_client() as client:
                job = client.query(query)
                results = list(job.result())
                
                for row in results:
                    hostname = row[0] if row[0] else None
                    
                    if hostname and self.hostname_detector.is_valid_hostname_value(hostname):
                        asset_data = {'hostname': hostname}
                        
                        for idx, (field_type, _) in enumerate(field_mappings.items(), 1):
                            if idx < len(row) and row[idx]:
                                mapped_value = self.field_mapper.map_field_value(field_type, row[idx])
                                asset_data[field_type] = mapped_value
                        
                        assets[hostname] = asset_data
        
        except Exception as e:
            logging.error(f"Failed to extract assets from {table_path}: {e}")
        
        return assets
    
    def _merge_asset_data(self, asset: AO1AssetRecord, new_data: Dict[str, Any], source_system: str):
        for field, value in new_data.items():
            if field == 'hostname':
                continue
            
            if hasattr(asset, field) and value:
                current_value = getattr(asset, field)
                if not current_value or current_value in ['', 'No', 'unknown']:
                    setattr(asset, field, value)
        
        if source_system == 'cmdb':
            asset.found_in_cmdb = True
        elif source_system == 'splunk':
            asset.found_in_splunk = True
            asset.in_splunk = True
        elif source_system == 'chronicle':
            asset.found_in_chronicle = True
            asset.in_chronicle = True
        elif source_system == 'crowdstrike':
            asset.found_in_crowdstrike = True
            asset.edr_coverage = 'Yes'
        elif source_system == 'gso':
            asset.in_gso = True
        
        source_count = sum([
            1 if asset.found_in_cmdb else 0,
            1 if asset.found_in_splunk else 0,
            1 if asset.found_in_chronicle else 0,
            1 if asset.found_in_crowdstrike else 0
        ])
        asset.source_count = source_count
    
    def _calculate_asset_scores(self, asset: AO1AssetRecord):
        completeness_fields = [
            asset.hostname, asset.fqdn, asset.ip_address, asset.infrastructure_type,
            asset.system_classification, asset.global_region, asset.business_unit
        ]
        
        filled_fields = sum(1 for field in completeness_fields if field and field != '')
        asset.data_completeness_score = (filled_fields / len(completeness_fields)) * 100
        
        coverage_score = 0.0
        max_coverage = 4.0
        
        if asset.found_in_cmdb:
            coverage_score += 1.0
        if asset.found_in_splunk:
            coverage_score += 1.0
        if asset.found_in_chronicle:
            coverage_score += 1.0
        if asset.found_in_crowdstrike:
            coverage_score += 1.0
        
        asset.host_parity_score = (coverage_score / max_coverage) * 100
        
        cmdb_visibility = 0.0
        if asset.found_in_cmdb:
            cmdb_visibility += 50.0
        if asset.infrastructure_type and asset.infrastructure_type != '':
            cmdb_visibility += 25.0
        if asset.system_classification and asset.system_classification != '':
            cmdb_visibility += 25.0
        
        asset.cmdb_asset_visibility_score = cmdb_visibility
        
        if asset.host_parity_score >= 75:
            asset.visibility_gap_severity = 'low'
        elif asset.host_parity_score >= 50:
            asset.visibility_gap_severity = 'medium'
        elif asset.host_parity_score >= 25:
            asset.visibility_gap_severity = 'high'
        else:
            asset.visibility_gap_severity = 'critical'
    
    async def _store_assets_in_db(self, assets: List[AO1AssetRecord]) -> int:
        if not assets:
            return 0
        
        insert_query = """
        INSERT OR REPLACE INTO ao1_asset_visibility (
            hostname, fqdn, ip_address, mac_address, infrastructure_type, system_classification,
            global_region, country, data_center, cloud_region, business_unit, cio, apm, 
            application_class, edr_coverage, tanium_coverage, dlp_coverage, in_splunk, 
            in_chronicle, in_gso, url_fqdn_coverage, public_ip_coverage, network_zones,
            ipam_coverage, geolocation, vpc, internal_external, host_parity_score,
            cmdb_asset_visibility_score, network_log_types, endpoint_log_types, 
            cloud_log_types, application_log_types, identity_log_types, found_in_cmdb,
            found_in_splunk, found_in_chronicle, found_in_crowdstrike, source_count,
            data_completeness_score, visibility_gap_severity, discovery_timestamp, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        rows_inserted = 0
        batch_size = 1000
        
        for i in range(0, len(assets), batch_size):
            batch = assets[i:i + batch_size]
            values_batch = []
            
            for asset in batch:
                values = [
                    asset.hostname, asset.fqdn, asset.ip_address, asset.mac_address,
                    asset.infrastructure_type, asset.system_classification, asset.global_region,
                    asset.country, asset.data_center, asset.cloud_region, asset.business_unit,
                    asset.cio, asset.apm, asset.application_class, asset.edr_coverage,
                    asset.tanium_coverage, asset.dlp_coverage, asset.in_splunk, asset.in_chronicle,
                    asset.in_gso, asset.url_fqdn_coverage, asset.public_ip_coverage,
                    asset.network_zones, asset.ipam_coverage, asset.geolocation, asset.vpc,
                    asset.internal_external, asset.host_parity_score, asset.cmdb_asset_visibility_score,
                    asset.network_log_types, asset.endpoint_log_types, asset.cloud_log_types,
                    asset.application_log_types, asset.identity_log_types, asset.found_in_cmdb,
                    asset.found_in_splunk, asset.found_in_chronicle, asset.found_in_crowdstrike,
                    asset.source_count, asset.data_completeness_score, asset.visibility_gap_severity,
                    'NOW()', 'NOW()'
                ]
                values_batch.append(values)
            
            try:
                self.conn.executemany(insert_query, values_batch)
                rows_inserted += len(values_batch)
            except Exception as e:
                logging.error(f"Failed to insert batch: {e}")
                
                for values in values_batch:
                    try:
                        self.conn.execute(insert_query, values)
                        rows_inserted += 1
                    except Exception as single_error:
                        logging.warning(f"Failed to insert single asset: {single_error}")
        
        self.conn.commit()
        return rows_inserted
    
    async def execute_enhanced_discovery(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        start_time = datetime.now()
        
        logging.info("Starting enhanced AO1 discovery with accurate field detection")
        
        discovered_tables = await self.discover_tables_with_hostnames()
        
        if not discovered_tables:
            return {
                'error': 'No tables with hostname columns found',
                'total_assets': 0,
                'tables_analyzed': 0
            }, {}
        
        logging.info(f"Found {len(discovered_tables)} tables with hostname data")
        
        total_assets = await self.extract_and_enrich_assets(discovered_tables)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        stats = {
            'total_assets': total_assets,
            'tables_analyzed': len(discovered_tables),
            'processing_time': processing_time,
            'database_path': self.db_path,
            'discovery_method': 'enhanced_ao1',
            'source_systems_found': list(set(table['source_system'] for table in discovered_tables))
        }
        
        queries = self._generate_ao1_queries()
        
        return stats, queries
    
    def _generate_ao1_queries(self) -> Dict[str, str]:
        return {
            'ao1_overview': """
                SELECT 
                    COUNT(*) as total_assets,
                    AVG(host_parity_score) as avg_host_parity,
                    AVG(cmdb_asset_visibility_score) as avg_cmdb_visibility,
                    AVG(data_completeness_score) as avg_completeness
                FROM ao1_asset_visibility;
            """,
            
            'visibility_gaps': """
                SELECT 
                    visibility_gap_severity,
                    COUNT(*) as asset_count,
                    ROUND(AVG(host_parity_score), 2) as avg_parity_score
                FROM ao1_asset_visibility
                GROUP BY visibility_gap_severity
                ORDER BY 
                    CASE visibility_gap_severity 
                        WHEN 'critical' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        WHEN 'low' THEN 4 
                    END;
            """,
            
            'source_coverage': """
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb_coverage,
                    SUM(CASE WHEN found_in_splunk THEN 1 ELSE 0 END) as splunk_coverage,
                    SUM(CASE WHEN found_in_chronicle THEN 1 ELSE 0 END) as chronicle_coverage,
                    SUM(CASE WHEN found_in_crowdstrike THEN 1 ELSE 0 END) as crowdstrike_coverage,
                    AVG(source_count) as avg_source_count
                FROM ao1_asset_visibility;
            """,
            
            'critical_gaps': """
                SELECT 
                    hostname, infrastructure_type, system_classification,
                    host_parity_score, visibility_gap_severity,
                    found_in_cmdb, found_in_splunk, found_in_chronicle, found_in_crowdstrike
                FROM ao1_asset_visibility
                WHERE visibility_gap_severity IN ('critical', 'high')
                ORDER BY host_parity_score ASC
                LIMIT 50;
            """,
            
            'infrastructure_analysis': """
                SELECT 
                    infrastructure_type,
                    COUNT(*) as count,
                    ROUND(AVG(host_parity_score), 2) as avg_parity,
                    SUM(CASE WHEN edr_coverage = 'Yes' THEN 1 ELSE 0 END) as edr_protected
                FROM ao1_asset_visibility
                WHERE infrastructure_type != ''
                GROUP BY infrastructure_type
                ORDER BY count DESC;
            """
        }
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()