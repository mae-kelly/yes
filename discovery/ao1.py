import asyncio
import logging
import re
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class AO1VisibilityEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_weights = {
            'log_coverage': 0.4,
            'cmdb_coverage': 0.3,
            'security_coverage': 0.2,
            'field_completeness': 0.1
        }
    
    async def enhanced_classification(self, column_name: str, samples: List[str], 
                                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        
        if self._is_hostname_column(column_name, samples):
            return {
                'field_type': 'hostname',
                'confidence': 0.95,
                'metadata': {
                    'ai_confidence': 0.95,
                    'content_confidence': 0.95,
                    'visibility_score': 1.0,
                    'ao1_enhanced': True
                }
            }
        
        content_analysis = await self._analyze_visibility_content(samples, 'unknown')
        final_confidence = content_analysis['confidence']
        
        metadata = {
            'ai_confidence': final_confidence,
            'content_confidence': content_analysis['confidence'],
            'visibility_score': self._calculate_visibility_score(samples, 'unknown'),
            'log_visibility_score': self._calculate_log_visibility(samples, 'unknown'),
            'cmdb_alignment_score': self._calculate_cmdb_alignment(samples, 'unknown'),
            'security_relevance': self._assess_security_relevance(samples, 'unknown'),
            'ao1_enhanced': True
        }
        
        return {
            'field_type': 'unknown',
            'confidence': final_confidence,
            'metadata': metadata
        }
    
    def _is_hostname_column(self, column_name: str, samples: List[str]) -> bool:
        name_lower = column_name.lower()
        hostname_indicators = ['hostname', 'host', 'computername', 'endpoint', 'device', 'machine', 'computer']
        
        for indicator in hostname_indicators:
            if indicator in name_lower:
                return True
        
        if not samples:
            return False
        
        hostname_count = 0
        for sample in samples[:20]:
            if self._looks_like_hostname(sample):
                hostname_count += 1
        
        return (hostname_count / min(len(samples), 20)) > 0.7
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str) or not (2 <= len(value) <= 253):
            return False
        
        if any(char in value for char in ['@', '/', '\\', ' ', '\t', '\n']):
            return False
        
        patterns = [
            r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$',
            r'^[a-zA-Z0-9]+$'
        ]
        
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)
    
    async def _analyze_visibility_content(self, samples: List[str], field_type: str) -> Dict[str, Any]:
        if not samples:
            return {'confidence': 0.0, 'patterns': [], 'pattern_matches': {}}
        
        visibility_patterns = {
            'hostname': [r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$'],
            'ip_address': [r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'],
            'log_type': [r'firewall|ids|ips|proxy|dns|syslog|winlog'],
            'security': [r'edr|dlp|crowdstrike|security|auth']
        }
        
        patterns = visibility_patterns.get(field_type, [])
        matches = 0
        
        for pattern in patterns:
            matches += sum(1 for value in samples if re.search(pattern, str(value), re.IGNORECASE))
        
        pattern_score = matches / len(samples) if samples else 0.0
        format_consistency = self._assess_format_consistency(samples)
        data_quality = self._assess_data_quality(samples)
        
        combined_confidence = (pattern_score * 0.5) + (format_consistency * 0.3) + (data_quality * 0.2)
        
        return {
            'confidence': combined_confidence,
            'patterns': [field_type] if pattern_score > 0.3 else [],
            'pattern_matches': {field_type: pattern_score},
            'format_consistency': format_consistency,
            'data_quality': data_quality
        }
    
    def _calculate_visibility_score(self, samples: List[str], field_type: str) -> float:
        if field_type in ['hostname', 'ip_address', 'fqdn']:
            return 0.9
        elif field_type in ['log_type', 'network_log_types', 'endpoint_log_types']:
            return 0.8
        elif field_type in ['edr_coverage', 'dlp_coverage', 'security']:
            return 0.7
        return 0.5
    
    def _calculate_log_visibility(self, samples: List[str], field_type: str) -> float:
        if field_type in ['log_type', 'network_log_types', 'endpoint_log_types']:
            return 1.0
        
        log_indicators = ['log', 'event', 'syslog', 'audit', 'firewall']
        matches = sum(1 for value in samples 
                     for indicator in log_indicators 
                     if indicator in str(value).lower())
        
        return min(1.0, matches / max(len(samples), 1))
    
    def _calculate_cmdb_alignment(self, samples: List[str], field_type: str) -> float:
        cmdb_fields = ['hostname', 'ip_address', 'system_classification', 'infrastructure_type']
        
        if field_type in cmdb_fields:
            return 0.9
        
        return 0.3
    
    def _assess_security_relevance(self, samples: List[str], field_type: str) -> float:
        security_fields = ['edr_coverage', 'dlp_coverage', 'security', 'auth']
        
        if field_type in security_fields:
            return 1.0
        
        security_terms = ['security', 'threat', 'vulnerability', 'compliance']
        matches = sum(1 for value in samples 
                     for term in security_terms 
                     if term in str(value).lower())
        
        return min(1.0, matches / max(len(samples), 1))
    
    def _assess_format_consistency(self, samples: List[str]) -> float:
        if len(samples) < 2:
            return 1.0
        
        from collections import Counter
        
        patterns = []
        for value in samples:
            pattern = re.sub(r'[a-zA-Z]', 'A', str(value))
            pattern = re.sub(r'[0-9]', '9', pattern)
            patterns.append(pattern)
        
        pattern_counts = Counter(patterns)
        most_common_ratio = pattern_counts.most_common(1)[0][1] / len(patterns) if pattern_counts else 0
        
        return most_common_ratio
    
    def _assess_data_quality(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        valid_samples = [s for s in samples if s and str(s).strip() and str(s).upper() not in ['NULL', 'N/A']]
        completeness = len(valid_samples) / len(samples)
        
        uniqueness = len(set(valid_samples)) / len(valid_samples) if valid_samples else 0
        
        return (completeness * 0.7) + (uniqueness * 0.3)

class AO1SuperEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.visibility_engine = AO1VisibilityEngine(config)
        
        self.performance_metrics = {
            'classifications': 0,
            'processing_times': [],
            'confidence_scores': [],
            'visibility_scores': []
        }
    
    async def enhanced_discovery(self, client_managers: Dict[str, Any], 
                               intelligence_result: Dict[str, Any] = None) -> Dict[str, Any]:
        
        logger.info("Starting COMPREHENSIVE CMDB discovery - processing ALL hosts from ALL tables")
        start_time = datetime.now()
        
        discovered_assets = {}
        
        priority_sources = [
            ('cmdb', 'prj-fisv.SAS_BI.V_DIM_ENDPOINT', 'prj-fisv'),
            ('splunk', 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG', 'prj-fisv'),
            ('crowdstrike', 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT', 'prj-fisv'),
            ('chronicle', 'chronicle-fisv.datalake.events', 'chronicle-fisv')
        ]
        
        total_hosts_processed = 0
        
        for source_name, table_path, project_id in priority_sources:
            client_manager = client_managers.get(project_id)
            if not client_manager:
                logger.warning(f"Client manager not available for {project_id}")
                continue
                
            logger.info(f"PROCESSING ALL HOSTS FROM {source_name.upper()}: {table_path}")
            
            try:
                assets = await self._process_entire_table_comprehensive(client_manager, table_path, source_name)
                
                for hostname, asset in assets.items():
                    if hostname in discovered_assets:
                        discovered_assets[hostname] = self._merge_comprehensive_assets(
                            discovered_assets[hostname], asset, source_name
                        )
                    else:
                        discovered_assets[hostname] = asset
                
                logger.info(f"Processed {len(assets):,} hosts from {source_name}")
                total_hosts_processed += len(assets)
                
            except Exception as e:
                logger.error(f"Failed to process {source_name}: {e}")
        
        logger.info(f"NOW PROCESSING ALL OTHER TABLES IN ALL DATASETS")
        
        for project_id, client_manager in client_managers.items():
            additional_assets = await self._discover_all_tables_comprehensive(client_manager, project_id, discovered_assets)
            
            for hostname, asset in additional_assets.items():
                if hostname in discovered_assets:
                    discovered_assets[hostname] = self._merge_comprehensive_assets(
                        discovered_assets[hostname], asset, 'additional_tables'
                    )
                else:
                    discovered_assets[hostname] = asset
            
            logger.info(f"Found {len(additional_assets):,} additional hosts from {project_id}")
            total_hosts_processed += len(additional_assets)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"COMPREHENSIVE DISCOVERY COMPLETE: {len(discovered_assets):,} UNIQUE HOSTS")
        logger.info(f"Total hosts processed: {total_hosts_processed:,}")
        logger.info(f"Processing time: {processing_time/60:.1f} minutes")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(discovered_assets),
                'total_hosts_processed': total_hosts_processed,
                'processing_time_minutes': processing_time / 60,
                'comprehensive_mode': True
            },
            'assets': discovered_assets,
            'performance_metrics': self._get_performance_summary()
        }
    
    async def _process_entire_table_maximum_intensity(self, client_manager, table_path: str, source_name: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        total_rows_processed = 0
        
        with client_manager.get_client() as client:
            try:
                table = client.get_table(table_path)
                if not table.schema:
                    return assets, 0
                
                columns = [field.name for field in table.schema]
                total_rows = table.num_rows
                
                logger.info(f"🔥 MAXIMUM INTENSITY MODE: {table_path}")
                logger.info(f"📋 COLUMNS: {len(columns)}")
                logger.info(f"📊 TOTAL ROWS: {total_rows:,}")
                logger.info(f"💾 PROCESSING EVERY SINGLE ROW - FANS WILL SPIN!")
                
                hostname_columns = self._find_hostname_columns(columns)
                if not hostname_columns:
                    logger.warning(f"⚠️  NO HOSTNAME COLUMNS FOUND IN {table_path}")
                    logger.info(f"📋 AVAILABLE COLUMNS: {columns[:20]}")
                    return assets, 0
                
                logger.info(f"🎯 HOSTNAME COLUMNS DETECTED: {hostname_columns}")
                
                field_mappings = self._create_comprehensive_field_mappings(columns)
                logger.info(f"🗺️  FIELD MAPPINGS CREATED FOR {len(field_mappings)} FIELD TYPES")
                
                batch_size = 50000
                batches = (total_rows + batch_size - 1) // batch_size
                
                logger.info(f"⚡ PROCESSING {batches} BATCHES OF {batch_size:,} ROWS EACH")
                logger.info(f"🌪️  MAXIMUM INTENSITY BATCHING - THIS WILL BE INTENSIVE!")
                
                for batch_num in range(batches):
                    offset = batch_num * batch_size
                    
                    select_fields = []
                    for col in columns:
                        select_fields.append(f"CAST(`{col}` AS STRING) as `{col}`")
                    
                    # FIXED: Remove WHERE clause to get ALL rows, then filter in Python
                    query = f"""
                    SELECT {', '.join(select_fields)}
                    FROM `{table_path}`
                    LIMIT {batch_size} OFFSET {offset}
                    """
                    
                    logger.info(f"🚀 BATCH {batch_num + 1}/{batches}: QUERYING {batch_size:,} ROWS AT OFFSET {offset:,}")
                    
                    job = client.query(query)
                    results = list(job.result())
                    
                    logger.info(f"📊 QUERY RETURNED {len(results):,} ROWS")
                    
                    if len(results) == 0:
                        logger.warning(f"⚠️  NO ROWS RETURNED FOR BATCH {batch_num + 1}")
                        continue
                    
                    batch_assets = self._extract_hosts_from_batch_intensive(results, columns, hostname_columns, field_mappings, source_name, table_path)
                    
                    for hostname, asset in batch_assets.items():
                        if hostname in assets:
                            assets[hostname] = self._merge_batch_assets(assets[hostname], asset)
                        else:
                            assets[hostname] = asset
                    
                    total_rows_processed += len(results)
                    
                    logger.info(f"✅ BATCH {batch_num + 1}/{batches} COMPLETE:")
                    logger.info(f"   📊 ROWS PROCESSED: {len(results):,}")
                    logger.info(f"   🏠 HOSTS IN BATCH: {len(batch_assets):,}")
                    logger.info(f"   📈 CUMULATIVE HOSTS: {len(assets):,}")
                    logger.info(f"   🔢 CUMULATIVE ROWS: {total_rows_processed:,}")
                    logger.info(f"   📊 PROGRESS: {((batch_num + 1) / batches * 100):.1f}%")
                    
                    # If we got fewer rows than expected, we've hit the end
                    if len(results) < batch_size:
                        logger.info(f"🏁 REACHED END OF TABLE AT BATCH {batch_num + 1}")
                        break
                
                logger.info(f"🎉 TABLE PROCESSING COMPLETE: {table_path}")
                logger.info(f"   🏆 TOTAL HOSTS DISCOVERED: {len(assets):,}")
                logger.info(f"   📊 TOTAL ROWS PROCESSED: {total_rows_processed:,}")
                logger.info(f"   💯 COMPLETION: 100%")
                
            except Exception as e:
                logger.error(f"❌ MAXIMUM INTENSITY PROCESSING FAILED: {table_path}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        return assets, total_rows_processed
    
    def _extract_hosts_from_batch_intensive(self, results: List, columns: List[str], hostname_columns: List[str], 
                                field_mappings: Dict[str, List[str]], source_name: str, table_path: str) -> Dict[str, Any]:
        assets = {}
        rows_with_hostnames = 0
        total_rows_processed = len(results)
        
        logger.info(f"🔍 EXTRACTING HOSTS FROM {total_rows_processed:,} ROWS")
        logger.info(f"🎯 LOOKING FOR HOSTNAMES IN COLUMNS: {hostname_columns}")
        
        for row_idx, row in enumerate(results):
            if not row:
                continue
            
            row_dict = dict(zip(columns, row))
            
            # Find ALL potential hostnames in this row
            hostnames = []
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col]:
                    hostname_value = str(row_dict[hostname_col]).strip().upper()
                    if self._is_valid_hostname(hostname_value):
                        hostnames.append(hostname_value)
            
            # If we found hostnames in this row, process it
            if hostnames:
                rows_with_hostnames += 1
                
                for hostname in hostnames:
                    if hostname not in assets:
                        assets[hostname] = {
                            'hostname': hostname,
                            'sources': [],
                            'tables_found_in': [],
                            'all_data': {},
                            'row_count': 0
                        }
                    
                    asset = assets[hostname]
                    asset['row_count'] += 1
                    
                    if source_name not in asset['sources']:
                        asset['sources'].append(source_name)
                    
                    if table_path not in asset['tables_found_in']:
                        asset['tables_found_in'].append(table_path)
                    
                    # Extract ALL field data from this row
                    for field_type, field_columns in field_mappings.items():
                        for field_col in field_columns:
                            if field_col in row_dict and row_dict[field_col]:
                                value = str(row_dict[field_col]).strip()
                                if self._is_valid_field_value(value):
                                    if field_type not in asset['all_data']:
                                        asset['all_data'][field_type] = set()
                                    asset['all_data'][field_type].add(value)
                    
                    self._set_coverage_flags_intensive(asset, source_name)
        
        # Convert sets back to lists for JSON serialization
        for hostname, asset in assets.items():
            for field_type, value_set in asset['all_data'].items():
                asset['all_data'][field_type] = list(value_set)
        
        logger.info(f"📊 EXTRACTION RESULTS:")
        logger.info(f"   🔢 TOTAL ROWS PROCESSED: {total_rows_processed:,}")
        logger.info(f"   🏠 ROWS WITH HOSTNAMES: {rows_with_hostnames:,}")
        logger.info(f"   🎯 UNIQUE HOSTS FOUND: {len(assets):,}")
        logger.info(f"   📈 HOST EXTRACTION RATE: {(rows_with_hostnames/total_rows_processed*100):.1f}%")
        
        return assets
    
    def _is_valid_hostname(self, value: str) -> bool:
        """Check if a value looks like a valid hostname"""
        if not value or len(value) < 2 or len(value) > 253:
            return False
        
        # Skip obviously invalid values
        invalid_values = ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0', 'null', 'none']
        if value.upper() in invalid_values:
            return False
        
        # Skip pure numbers
        if value.isdigit():
            return False
        
        # Skip IP addresses (they're not hostnames)
        if self._looks_like_ip(value):
            return False
        
        # Basic hostname pattern check
        import re
        hostname_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]*[a-zA-Z0-9]
    
    def _set_coverage_flags_intensive(self, asset: Dict[str, Any], source: str):
        coverage_flags = {
            'cmdb': {'cmdb_visibility': True, 'cmdb_coverage': True},
            'splunk': {'splunk_coverage': True, 'siem_coverage': True},
            'chronicle': {'chronicle_coverage': True, 'siem_coverage': True, 'google_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True, 'endpoint_protection': True}
        }
        
        flags = coverage_flags.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_batch_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        merged['row_count'] = merged.get('row_count', 0) + secondary.get('row_count', 0)
        
        for source in secondary.get('sources', []):
            if source not in merged['sources']:
                merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage', 'siem_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    def _find_hostname_columns(self, columns: List[str]) -> List[str]:
        hostname_indicators = [
            'hostname', 'host', 'computername', 'computer_name', 'endpoint', 'device', 
            'machine', 'server', 'asset', 'equipment', 'node', 'system', 'workstation',
            'name', 'device_name', 'system_name', 'machine_name', 'server_name',
            'endpoint_name', 'asset_name', 'equipment_name', 'appliance', 'instance'
        ]
        
        hostname_cols = []
        
        # Check for exact matches first
        for col in columns:
            col_lower = col.lower()
            if col_lower in ['hostname', 'host', 'computername', 'device_name', 'machine_name']:
                hostname_cols.append(col)
        
        # If no exact matches, look for partial matches
        if not hostname_cols:
            for col in columns:
                col_lower = col.lower()
                for indicator in hostname_indicators:
                    if indicator in col_lower and len(col_lower) <= 50:  # Avoid very long column names
                        hostname_cols.append(col)
                        break
        
        # If still no matches, look for any column with 'name' in it (but not *_name_*)
        if not hostname_cols:
            for col in columns:
                col_lower = col.lower()
                if 'name' in col_lower and not any(x in col_lower for x in ['file', 'path', 'url', 'description', 'type']):
                    hostname_cols.append(col)
        
        logger.info(f"🔍 HOSTNAME COLUMN DETECTION:")
        logger.info(f"   📋 TOTAL COLUMNS: {len(columns)}")
        logger.info(f"   🎯 HOSTNAME COLUMNS FOUND: {len(hostname_cols)}")
        logger.info(f"   📝 HOSTNAME COLUMNS: {hostname_cols}")
        
        if not hostname_cols:
            logger.info(f"   📄 SAMPLE COLUMNS: {columns[:10]}")
        
        return hostname_cols
    
    def _create_comprehensive_field_mappings(self, columns: List[str]) -> Dict[str, List[str]]:
        mappings = {
            'hostname': [],
            'ip_address': [],
            'fqdn': [],
            'country': [],
            'region': [],
            'business_unit': [],
            'cio': [],
            'datacenter': [],
            'application_class': [],
            'infrastructure_type': [],
            'system_classification': [],
            'mac_address': []
        }
        
        field_patterns = {
            'hostname': ['hostname', 'host', 'computer', 'endpoint', 'device', 'machine', 'server'],
            'ip_address': ['ip', 'ipaddress', 'address'],
            'fqdn': ['fqdn', 'domain', 'dns'],
            'country': ['country', 'ctry'],
            'region': ['region', 'geo', 'location'],
            'business_unit': ['business', 'unit', 'bu', 'org'],
            'cio': ['cio', 'chief'],
            'datacenter': ['datacenter', 'dc', 'site'],
            'application_class': ['application', 'app', 'class'],
            'infrastructure_type': ['infrastructure', 'infra', 'type'],
            'system_classification': ['system', 'classification', 'class'],
            'mac_address': ['mac', 'physical']
        }
        
        for col in columns:
            col_lower = col.lower()
            for field_type, patterns in field_patterns.items():
                for pattern in patterns:
                    if pattern in col_lower:
                        mappings[field_type].append(col)
                        break
        
        return mappings
    
    def _extract_hosts_from_batch(self, results: List, columns: List[str], hostname_columns: List[str], 
                                field_mappings: Dict[str, List[str]], source_name: str, table_path: str) -> Dict[str, Any]:
        assets = {}
        
        for row in results:
            if not row:
                continue
            
            row_dict = dict(zip(columns, row))
            
            hostnames = []
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col]:
                    hostname = str(row_dict[hostname_col]).strip().upper()
                    if hostname and len(hostname) > 1 and hostname not in ['NULL', 'NONE', 'UNKNOWN', 'N/A']:
                        hostnames.append(hostname)
            
            for hostname in hostnames:
                if hostname not in assets:
                    assets[hostname] = {
                        'hostname': hostname,
                        'sources': [],
                        'tables_found_in': [],
                        'all_data': {}
                    }
                
                asset = assets[hostname]
                
                if source_name not in asset['sources']:
                    asset['sources'].append(source_name)
                
                if table_path not in asset['tables_found_in']:
                    asset['tables_found_in'].append(table_path)
                
                for field_type, field_columns in field_mappings.items():
                    for field_col in field_columns:
                        if field_col in row_dict and row_dict[field_col]:
                            value = str(row_dict[field_col]).strip()
                            if value and value.upper() not in ['NULL', 'NONE', 'UNKNOWN', 'N/A', '']:
                                if field_type not in asset['all_data']:
                                    asset['all_data'][field_type] = []
                                if value not in asset['all_data'][field_type]:
                                    asset['all_data'][field_type].append(value)
                
                self._set_coverage_flags(asset, source_name)
        
        return assets
    
    async def _discover_all_tables_maximum_intensity(self, client_manager, project_id: str, existing_assets: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        additional_assets = {}
        total_additional_rows = 0
        
        logger.info(f"🌟 MAXIMUM INTENSITY DATASET SCAN: {project_id}")
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            logger.info(f"📂 DATASETS FOUND: {len(datasets)}")
            
            for dataset_idx, dataset in enumerate(datasets):
                logger.info(f"🗂️  DATASET {dataset_idx + 1}/{len(datasets)}: {dataset.dataset_id}")
                
                tables = list(client.list_tables(dataset))
                logger.info(f"📋 TABLES IN DATASET: {len(tables)}")
                
                for table_idx, table_ref in enumerate(tables):
                    table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                    
                    if self._is_priority_table(table_path):
                        logger.info(f"⏭️  SKIPPING PRIORITY TABLE: {table_path}")
                        continue
                    
                    try:
                        logger.info(f"🔍 TABLE {table_idx + 1}/{len(tables)}: {table_ref.table_id}")
                        table_assets, table_rows = await self._scan_table_for_hosts_intensive(client, table_path)
                        
                        for hostname, asset in table_assets.items():
                            if hostname not in existing_assets and hostname not in additional_assets:
                                additional_assets[hostname] = asset
                            elif hostname in additional_assets:
                                additional_assets[hostname] = self._merge_batch_assets(additional_assets[hostname], asset)
                        
                        total_additional_rows += table_rows
                        
                        if len(table_assets) > 0:
                            logger.info(f"✅ FOUND {len(table_assets):,} NEW HOSTS FROM {table_rows:,} ROWS")
                        
                    except Exception as e:
                        logger.debug(f"⚠️  FAILED TO SCAN {table_path}: {e}")
                
                logger.info(f"📊 DATASET {dataset.dataset_id} COMPLETE: {len(additional_assets):,} TOTAL NEW HOSTS")
        
        logger.info(f"🎯 PROJECT {project_id} SCAN COMPLETE:")
        logger.info(f"   🏠 NEW HOSTS DISCOVERED: {len(additional_assets):,}")
        logger.info(f"   📊 ADDITIONAL ROWS SCANNED: {total_additional_rows:,}")
        
        return additional_assets, total_additional_rows
    
    async def _scan_table_for_hosts_intensive(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return assets, 0
            
            columns = [field.name for field in table.schema]
            hostname_columns = self._find_hostname_columns(columns)
            
            if not hostname_columns:
                return assets, 0
            
            field_mappings = self._create_comprehensive_field_mappings(columns)
            
            max_rows_to_scan = min(table.num_rows, 500000)  # Increased from 1M to process more
            
            select_fields = []
            for col in columns:
                select_fields.append(f"CAST(`{col}` AS STRING) as `{col}`")
            
            # FIXED: Remove WHERE clause to get ALL rows
            query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{table_path}`
            LIMIT {max_rows_to_scan}
            """
            
            job = client.query(query)
            results = list(job.result())
            
            if len(results) > 0:
                assets = self._extract_hosts_from_batch_intensive(results, columns, hostname_columns, field_mappings, 'additional_discovery', table_path)
                rows_processed = len(results)
                
                if len(assets) > 0:
                    logger.info(f"🎯 {table_path}: {len(assets):,} hosts from {rows_processed:,} rows")
            
        except Exception as e:
            logger.debug(f"Failed to scan table {table_path}: {e}")
        
        return assets, rows_processed
    
    def _is_priority_table(self, table_path: str) -> bool:
        priority_tables = [
            'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT',
            'chronicle-fisv.datalake.events'
        ]
        return table_path in priority_tables
    
    async def _scan_table_for_hosts(self, client, table_path: str) -> Dict[str, Any]:
        assets = {}
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return assets
            
            columns = [field.name for field in table.schema]
            hostname_columns = self._find_hostname_columns(columns)
            
            if not hostname_columns:
                return assets
            
            field_mappings = self._create_comprehensive_field_mappings(columns)
            
            select_fields = []
            for col in columns:
                select_fields.append(f"CAST(`{col}` AS STRING) as `{col}`")
            
            query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{table_path}`
            WHERE {' OR '.join([f'`{col}` IS NOT NULL' for col in hostname_columns])}
            """
            
            job = client.query(query)
            results = list(job.result())
            
            assets = self._extract_hosts_from_batch(results, columns, hostname_columns, field_mappings, 'additional', table_path)
            
        except Exception as e:
            logger.debug(f"Failed to scan table {table_path}: {e}")
        
        return assets
    
    def _set_coverage_flags(self, asset: Dict[str, Any], source: str):
        coverage_flags = {
            'cmdb': {'cmdb_visibility': True},
            'splunk': {'splunk_coverage': True},
            'chronicle': {'chronicle_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True}
        }
        
        flags = coverage_flags.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_comprehensive_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any], source: str) -> Dict[str, Any]:
        merged = primary.copy()
        
        if source not in merged['sources']:
            merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    async def _extract_ao1_assets(self, client, table_path: str, mappings: Dict[str, str], 
                                metadata: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        
        hostname_col = mappings['hostname']
        assets = {}
        
        try:
            select_fields = [f"CAST(`{hostname_col}` AS STRING) as hostname"]
            
            for field_type, column_name in mappings.items():
                if field_type != 'hostname':
                    select_fields.append(f"CAST(`{column_name}` AS STRING) as {field_type}")
            
            query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{table_path}`
            WHERE `{hostname_col}` IS NOT NULL
            LIMIT 10000
            """
            
            job = client.query(query)
            results = list(job.result())
            
            for row in results:
                if not row or not row[0]:
                    continue
                
                hostname = str(row[0]).strip().upper()
                if not hostname or len(hostname) < 1:
                    continue
                
                asset_id = f"ao1_{hostname}_{source_name}"
                
                asset = {
                    'id': asset_id,
                    'hostname': hostname,
                    'ao1_enhanced': True,
                    'ao1_metadata': metadata,
                    'source': source_name
                }
                
                for idx, field_type in enumerate(mappings.keys()):
                    if idx < len(row) and row[idx]:
                        value = str(row[idx]).strip()
                        if value:
                            asset[field_type] = value
                
                self._set_ao1_source_flags(asset, source_name)
                asset['visibility_score'] = self._calculate_ao1_visibility_score(asset, metadata)
                
                assets[asset_id] = asset
                
        except Exception as e:
            logger.error(f"AO1 asset extraction failed: {e}")
        
        return assets
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        metrics = self.performance_metrics
        
        if not metrics['confidence_scores']:
            return {'status': 'no_data'}
        
        return {
            'total_classifications': metrics['classifications'],
            'avg_processing_time': statistics.mean(metrics['processing_times']) if metrics['processing_times'] else 0,
            'avg_confidence': statistics.mean(metrics['confidence_scores']) if metrics['confidence_scores'] else 0,
            'avg_visibility': statistics.mean(metrics['visibility_scores']) if metrics['visibility_scores'] else 0
        }
        if not re.match(hostname_pattern, value, re.IGNORECASE):
            return False
        
        return True
    
    def _looks_like_ip(self, value: str) -> bool:
        """Check if value looks like an IP address"""
        parts = value.split('.')
        if len(parts) == 4:
            try:
                for part in parts:
                    num = int(part)
                    if not (0 <= num <= 255):
                        return False
                return True
            except:
                return False
        return False
    
    def _is_valid_field_value(self, value: str) -> bool:
        """Check if a field value is valid (not null/empty)"""
        if not value:
            return False
        
        invalid_values = ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', 'null', 'none', '0']
        return value.upper() not in invalid_values
    
    def _set_coverage_flags_intensive(self, asset: Dict[str, Any], source: str):
        coverage_flags = {
            'cmdb': {'cmdb_visibility': True, 'cmdb_coverage': True},
            'splunk': {'splunk_coverage': True, 'siem_coverage': True},
            'chronicle': {'chronicle_coverage': True, 'siem_coverage': True, 'google_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True, 'endpoint_protection': True}
        }
        
        flags = coverage_flags.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_batch_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = primary.copy()
        
        merged['row_count'] = merged.get('row_count', 0) + secondary.get('row_count', 0)
        
        for source in secondary.get('sources', []):
            if source not in merged['sources']:
                merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage', 'siem_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    def _find_hostname_columns(self, columns: List[str]) -> List[str]:
        hostname_indicators = [
            'hostname', 'host', 'computername', 'computer_name', 'endpoint', 'device', 
            'machine', 'server', 'asset', 'equipment', 'node', 'system', 'workstation'
        ]
        
        hostname_cols = []
        for col in columns:
            col_lower = col.lower()
            for indicator in hostname_indicators:
                if indicator in col_lower:
                    hostname_cols.append(col)
                    break
        
        return hostname_cols
    
    def _create_comprehensive_field_mappings(self, columns: List[str]) -> Dict[str, List[str]]:
        mappings = {
            'hostname': [],
            'ip_address': [],
            'fqdn': [],
            'country': [],
            'region': [],
            'business_unit': [],
            'cio': [],
            'datacenter': [],
            'application_class': [],
            'infrastructure_type': [],
            'system_classification': [],
            'mac_address': []
        }
        
        field_patterns = {
            'hostname': ['hostname', 'host', 'computer', 'endpoint', 'device', 'machine', 'server'],
            'ip_address': ['ip', 'ipaddress', 'address'],
            'fqdn': ['fqdn', 'domain', 'dns'],
            'country': ['country', 'ctry'],
            'region': ['region', 'geo', 'location'],
            'business_unit': ['business', 'unit', 'bu', 'org'],
            'cio': ['cio', 'chief'],
            'datacenter': ['datacenter', 'dc', 'site'],
            'application_class': ['application', 'app', 'class'],
            'infrastructure_type': ['infrastructure', 'infra', 'type'],
            'system_classification': ['system', 'classification', 'class'],
            'mac_address': ['mac', 'physical']
        }
        
        for col in columns:
            col_lower = col.lower()
            for field_type, patterns in field_patterns.items():
                for pattern in patterns:
                    if pattern in col_lower:
                        mappings[field_type].append(col)
                        break
        
        return mappings
    
    def _extract_hosts_from_batch(self, results: List, columns: List[str], hostname_columns: List[str], 
                                field_mappings: Dict[str, List[str]], source_name: str, table_path: str) -> Dict[str, Any]:
        assets = {}
        
        for row in results:
            if not row:
                continue
            
            row_dict = dict(zip(columns, row))
            
            hostnames = []
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col]:
                    hostname = str(row_dict[hostname_col]).strip().upper()
                    if hostname and len(hostname) > 1 and hostname not in ['NULL', 'NONE', 'UNKNOWN', 'N/A']:
                        hostnames.append(hostname)
            
            for hostname in hostnames:
                if hostname not in assets:
                    assets[hostname] = {
                        'hostname': hostname,
                        'sources': [],
                        'tables_found_in': [],
                        'all_data': {}
                    }
                
                asset = assets[hostname]
                
                if source_name not in asset['sources']:
                    asset['sources'].append(source_name)
                
                if table_path not in asset['tables_found_in']:
                    asset['tables_found_in'].append(table_path)
                
                for field_type, field_columns in field_mappings.items():
                    for field_col in field_columns:
                        if field_col in row_dict and row_dict[field_col]:
                            value = str(row_dict[field_col]).strip()
                            if value and value.upper() not in ['NULL', 'NONE', 'UNKNOWN', 'N/A', '']:
                                if field_type not in asset['all_data']:
                                    asset['all_data'][field_type] = []
                                if value not in asset['all_data'][field_type]:
                                    asset['all_data'][field_type].append(value)
                
                self._set_coverage_flags(asset, source_name)
        
        return assets
    
    async def _discover_all_tables_maximum_intensity(self, client_manager, project_id: str, existing_assets: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        additional_assets = {}
        total_additional_rows = 0
        
        logger.info(f"🌟 MAXIMUM INTENSITY DATASET SCAN: {project_id}")
        
        with client_manager.get_client() as client:
            datasets = list(client.list_datasets(project=project_id))
            
            logger.info(f"📂 DATASETS FOUND: {len(datasets)}")
            
            for dataset_idx, dataset in enumerate(datasets):
                logger.info(f"🗂️  DATASET {dataset_idx + 1}/{len(datasets)}: {dataset.dataset_id}")
                
                tables = list(client.list_tables(dataset))
                logger.info(f"📋 TABLES IN DATASET: {len(tables)}")
                
                for table_idx, table_ref in enumerate(tables):
                    table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                    
                    if self._is_priority_table(table_path):
                        logger.info(f"⏭️  SKIPPING PRIORITY TABLE: {table_path}")
                        continue
                    
                    try:
                        logger.info(f"🔍 TABLE {table_idx + 1}/{len(tables)}: {table_ref.table_id}")
                        table_assets, table_rows = await self._scan_table_for_hosts_intensive(client, table_path)
                        
                        for hostname, asset in table_assets.items():
                            if hostname not in existing_assets and hostname not in additional_assets:
                                additional_assets[hostname] = asset
                            elif hostname in additional_assets:
                                additional_assets[hostname] = self._merge_batch_assets(additional_assets[hostname], asset)
                        
                        total_additional_rows += table_rows
                        
                        if len(table_assets) > 0:
                            logger.info(f"✅ FOUND {len(table_assets):,} NEW HOSTS FROM {table_rows:,} ROWS")
                        
                    except Exception as e:
                        logger.debug(f"⚠️  FAILED TO SCAN {table_path}: {e}")
                
                logger.info(f"📊 DATASET {dataset.dataset_id} COMPLETE: {len(additional_assets):,} TOTAL NEW HOSTS")
        
        logger.info(f"🎯 PROJECT {project_id} SCAN COMPLETE:")
        logger.info(f"   🏠 NEW HOSTS DISCOVERED: {len(additional_assets):,}")
        logger.info(f"   📊 ADDITIONAL ROWS SCANNED: {total_additional_rows:,}")
        
        return additional_assets, total_additional_rows
    
    async def _scan_table_for_hosts_intensive(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return assets, 0
            
            columns = [field.name for field in table.schema]
            hostname_columns = self._find_hostname_columns(columns)
            
            if not hostname_columns:
                return assets, 0
            
            field_mappings = self._create_comprehensive_field_mappings(columns)
            
            max_rows_to_scan = min(table.num_rows, 1000000)
            
            select_fields = []
            for col in columns:
                select_fields.append(f"CAST(`{col}` AS STRING) as `{col}`")
            
            query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{table_path}`
            WHERE {' OR '.join([f'`{col}` IS NOT NULL' for col in hostname_columns])}
            LIMIT {max_rows_to_scan}
            """
            
            job = client.query(query)
            results = list(job.result())
            
            assets = self._extract_hosts_from_batch_intensive(results, columns, hostname_columns, field_mappings, 'additional_discovery', table_path)
            rows_processed = len(results)
            
        except Exception as e:
            logger.debug(f"Failed to scan table {table_path}: {e}")
        
        return assets, rows_processed
    
    def _is_priority_table(self, table_path: str) -> bool:
        priority_tables = [
            'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT',
            'chronicle-fisv.datalake.events'
        ]
        return table_path in priority_tables
    
    async def _scan_table_for_hosts(self, client, table_path: str) -> Dict[str, Any]:
        assets = {}
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return assets
            
            columns = [field.name for field in table.schema]
            hostname_columns = self._find_hostname_columns(columns)
            
            if not hostname_columns:
                return assets
            
            field_mappings = self._create_comprehensive_field_mappings(columns)
            
            select_fields = []
            for col in columns:
                select_fields.append(f"CAST(`{col}` AS STRING) as `{col}`")
            
            query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{table_path}`
            WHERE {' OR '.join([f'`{col}` IS NOT NULL' for col in hostname_columns])}
            """
            
            job = client.query(query)
            results = list(job.result())
            
            assets = self._extract_hosts_from_batch(results, columns, hostname_columns, field_mappings, 'additional', table_path)
            
        except Exception as e:
            logger.debug(f"Failed to scan table {table_path}: {e}")
        
        return assets
    
    def _set_coverage_flags(self, asset: Dict[str, Any], source: str):
        coverage_flags = {
            'cmdb': {'cmdb_visibility': True},
            'splunk': {'splunk_coverage': True},
            'chronicle': {'chronicle_coverage': True},
            'crowdstrike': {'crowdstrike_coverage': True, 'edr_coverage': True}
        }
        
        flags = coverage_flags.get(source, {})
        for flag, value in flags.items():
            asset[flag] = value
    
    def _merge_comprehensive_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any], source: str) -> Dict[str, Any]:
        merged = primary.copy()
        
        if source not in merged['sources']:
            merged['sources'].append(source)
        
        for table in secondary.get('tables_found_in', []):
            if table not in merged['tables_found_in']:
                merged['tables_found_in'].append(table)
        
        for field_type, values in secondary.get('all_data', {}).items():
            if field_type not in merged['all_data']:
                merged['all_data'][field_type] = []
            
            for value in values:
                if value not in merged['all_data'][field_type]:
                    merged['all_data'][field_type].append(value)
        
        for flag in ['cmdb_visibility', 'splunk_coverage', 'chronicle_coverage', 'crowdstrike_coverage', 'edr_coverage']:
            if secondary.get(flag, False):
                merged[flag] = True
        
        return merged
    
    async def _extract_ao1_assets(self, client, table_path: str, mappings: Dict[str, str], 
                                metadata: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        
        hostname_col = mappings['hostname']
        assets = {}
        
        try:
            select_fields = [f"CAST(`{hostname_col}` AS STRING) as hostname"]
            
            for field_type, column_name in mappings.items():
                if field_type != 'hostname':
                    select_fields.append(f"CAST(`{column_name}` AS STRING) as {field_type}")
            
            query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{table_path}`
            WHERE `{hostname_col}` IS NOT NULL
            LIMIT 10000
            """
            
            job = client.query(query)
            results = list(job.result())
            
            for row in results:
                if not row or not row[0]:
                    continue
                
                hostname = str(row[0]).strip().upper()
                if not hostname or len(hostname) < 1:
                    continue
                
                asset_id = f"ao1_{hostname}_{source_name}"
                
                asset = {
                    'id': asset_id,
                    'hostname': hostname,
                    'ao1_enhanced': True,
                    'ao1_metadata': metadata,
                    'source': source_name
                }
                
                for idx, field_type in enumerate(mappings.keys()):
                    if idx < len(row) and row[idx]:
                        value = str(row[idx]).strip()
                        if value:
                            asset[field_type] = value
                
                self._set_ao1_source_flags(asset, source_name)
                asset['visibility_score'] = self._calculate_ao1_visibility_score(asset, metadata)
                
                assets[asset_id] = asset
                
        except Exception as e:
            logger.error(f"AO1 asset extraction failed: {e}")
        
        return assets
    
    def _set_ao1_source_flags(self, asset: Dict[str, Any], source: str):
        flags = {
            'cmdb': {'cmdb': True},
            'splunk': {'splunk': True},
            'chronicle': {'chronicle': True},
            'crowdstrike': {'crowdstrike': True, 'edr': True}
        }
        
        source_flags = flags.get(source, {})
        for flag, value in source_flags.items():
            asset[flag] = value
    
    def _calculate_ao1_visibility_score(self, asset: Dict[str, Any], metadata: Dict[str, Any]) -> float:
        factors = []
        
        log_sources = sum([
            asset.get('splunk', False),
            asset.get('chronicle', False),
            asset.get('gso', False)
        ])
        log_score = min(1.0, log_sources / 3.0)
        factors.append(('log_coverage', log_score, 0.4))
        
        cmdb_score = 1.0 if asset.get('cmdb') else 0.0
        factors.append(('cmdb_coverage', cmdb_score, 0.3))
        
        security_coverage = sum([
            asset.get('edr', False),
            asset.get('dlp', False),
            asset.get('tanium', False)
        ])
        security_score = min(1.0, security_coverage / 3.0)
        factors.append(('security_coverage', security_score, 0.2))
        
        field_completeness = len([f for f in ['hostname', 'ip_address', 'infra_type'] 
                                if asset.get(f)]) / 3.0
        factors.append(('field_completeness', field_completeness, 0.1))
        
        total_score = sum(score * weight for _, score, weight in factors)
        
        if metadata:
            ai_boost = statistics.mean([m.get('visibility_score', 0) for m in metadata.values()])
            total_score = total_score * (1 + ai_boost * 0.2)
        
        return min(1.0, total_score)
    
    def _merge_ao1_assets(self, primary: Dict[str, Any], secondary: Dict[str, Any], source: str) -> Dict[str, Any]:
        merged = primary.copy()
        
        for key, value in secondary.items():
            if key not in merged or not merged[key]:
                merged[key] = value
        
        merged['sources'] = merged.get('sources', 1) + 1
        merged['source_list'] = f"{merged.get('source_list', primary.get('source', ''))},{source}"
        
        primary_vis = primary.get('visibility_score', 0)
        secondary_vis = secondary.get('visibility_score', 0)
        merged['visibility_score'] = max(primary_vis, secondary_vis)
        
        return merged
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        metrics = self.performance_metrics
        
        if not metrics['confidence_scores']:
            return {'status': 'no_data'}
        
        return {
            'total_classifications': metrics['classifications'],
            'avg_processing_time': statistics.mean(metrics['processing_times']) if metrics['processing_times'] else 0,
            'avg_confidence': statistics.mean(metrics['confidence_scores']) if metrics['confidence_scores'] else 0,
            'avg_visibility': statistics.mean(metrics['visibility_scores']) if metrics['visibility_scores'] else 0
        }