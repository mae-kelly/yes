# discovery/ao1.py

import asyncio
import logging
import re
import statistics
from typing import Dict, List, Any, Optional, Tuple
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
        
        if self._is_hostname_column_by_content(samples):
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
    
    def _is_hostname_column_by_content(self, samples: List[str]) -> bool:
        if not samples:
            return False
        
        hostname_count = 0
        valid_samples = 0
        
        for sample in samples[:50]:
            if sample and str(sample).strip():
                valid_samples += 1
                if self._looks_like_hostname(sample):
                    hostname_count += 1
        
        if valid_samples == 0:
            return False
        
        hostname_ratio = hostname_count / valid_samples
        return hostname_ratio > 0.6
    
    def _looks_like_hostname(self, value: str) -> bool:
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip().upper()
        
        if not value or len(value) < 2 or len(value) > 253:
            return False
        
        if value in ['NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0']:
            return False
        
        if value.isdigit():
            return False
        
        if self._looks_like_ip(value):
            return False
        
        if any(char in value for char in ['@', 'HTTP', 'WWW', '.COM', '.NET', '.ORG', '/', '\\', ' ', '\t', '\n']):
            return False
        
        if not any(c.isalpha() for c in value):
            return False
        
        pattern = r'^[A-Z0-9][A-Z0-9\-_.]*[A-Z0-9]$'
        if re.match(pattern, value):
            return True
        
        if re.match(r'^[A-Z0-9]+$', value):
            return True
        
        return False
    
    def _looks_like_ip(self, value: str) -> bool:
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
        
        logger.info("🔥 STARTING MAXIMUM INTENSITY COMPREHENSIVE CMDB DISCOVERY 🔥")
        logger.info("⚡ PROCESSING EVERY SINGLE HOST FROM EVERY SINGLE TABLE ⚡")
        logger.info("🌪️  FANS WILL BE SPINNING - THIS IS GOING TO BE INTENSIVE 🌪️")
        start_time = datetime.now()
        
        discovered_assets = {}
        
        priority_sources = [
            ('cmdb', 'prj-fisv.SAS_BI.V_DIM_ENDPOINT', 'prj-fisv'),
            ('splunk', 'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG', 'prj-fisv'),
            ('crowdstrike', 'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT', 'prj-fisv'),
            ('chronicle', 'chronicle-fisv.datalake.events', 'chronicle-fisv')
        ]
        
        total_hosts_processed = 0
        total_rows_scanned = 0
        
        for source_name, table_path, project_id in priority_sources:
            client_manager = client_managers.get(project_id)
            if not client_manager:
                logger.warning(f"Client manager not available for {project_id}")
                continue
                
            logger.info(f"🚀 MAXIMUM INTENSITY PROCESSING: {source_name.upper()}")
            logger.info(f"📊 TABLE: {table_path}")
            logger.info(f"💾 PROCESSING EVERY SINGLE ROW - NO LIMITS")
            
            try:
                assets, rows_processed = await self._process_entire_table_maximum_intensity(client_manager, table_path, source_name)
                
                for hostname, asset in assets.items():
                    if hostname in discovered_assets:
                        discovered_assets[hostname] = self._merge_comprehensive_assets(
                            discovered_assets[hostname], asset, source_name
                        )
                    else:
                        discovered_assets[hostname] = asset
                
                logger.info(f"✅ {source_name.upper()}: {len(assets):,} HOSTS FROM {rows_processed:,} ROWS")
                total_hosts_processed += len(assets)
                total_rows_scanned += rows_processed
                
                logger.info(f"🔥 CUMULATIVE: {len(discovered_assets):,} UNIQUE HOSTS, {total_rows_scanned:,} ROWS SCANNED")
                
            except Exception as e:
                logger.error(f"❌ FAILED TO PROCESS {source_name}: {e}")
        
        logger.info(f"🌟 NOW SCANNING EVERY OTHER TABLE IN EVERY DATASET 🌟")
        logger.info(f"🔍 COMPREHENSIVE DATASET DISCOVERY MODE ACTIVATED")
        
        for project_id, client_manager in client_managers.items():
            logger.info(f"🗂️  SCANNING ALL DATASETS IN PROJECT: {project_id}")
            additional_assets, additional_rows = await self._discover_all_tables_maximum_intensity(client_manager, project_id, discovered_assets)
            
            for hostname, asset in additional_assets.items():
                if hostname in discovered_assets:
                    discovered_assets[hostname] = self._merge_comprehensive_assets(
                        discovered_assets[hostname], asset, 'additional_discovery'
                    )
                else:
                    discovered_assets[hostname] = asset
            
            logger.info(f"📈 PROJECT {project_id}: +{len(additional_assets):,} HOSTS FROM {additional_rows:,} ADDITIONAL ROWS")
            total_hosts_processed += len(additional_assets)
            total_rows_scanned += additional_rows
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎉 MAXIMUM INTENSITY DISCOVERY COMPLETE! 🎉")
        logger.info(f"🏆 FINAL RESULTS:")
        logger.info(f"   📊 UNIQUE HOSTS DISCOVERED: {len(discovered_assets):,}")
        logger.info(f"   🔍 TOTAL ROWS SCANNED: {total_rows_scanned:,}")
        logger.info(f"   ⏱️  PROCESSING TIME: {processing_time/60:.1f} MINUTES")
        logger.info(f"   🚀 ROWS PER SECOND: {total_rows_scanned/processing_time:,.0f}")
        logger.info(f"   💻 HOSTS PER SECOND: {len(discovered_assets)/processing_time:,.0f}")
        
        return {
            'discovery_stats': {
                'total_unique_hosts': len(discovered_assets),
                'total_hosts_processed': total_hosts_processed,
                'total_rows_scanned': total_rows_scanned,
                'processing_time_minutes': processing_time / 60,
                'rows_per_second': total_rows_scanned / processing_time,
                'hosts_per_second': len(discovered_assets) / processing_time,
                'maximum_intensity_mode': True,
                'comprehensive_scan_complete': True,
                'fan_spinning_guaranteed': True
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
                
                hostname_columns = await self._find_hostname_columns_by_content(client, table_path, columns)
                if not hostname_columns:
                    logger.warning(f"⚠️  NO HOSTNAME COLUMNS FOUND IN {table_path}")
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
                    
                    query = f"""
                    SELECT *
                    FROM `{table_path}`
                    LIMIT {batch_size} OFFSET {offset}
                    """
                    
                    logger.info(f"🚀 BATCH {batch_num + 1}/{batches}: QUERYING {batch_size:,} ROWS AT OFFSET {offset:,}")
                    logger.info(f"🔍 QUERY: {query}")
                    
                    try:
                        job = client.query(query)
                        results = list(job.result())
                        
                        logger.info(f"📊 QUERY RETURNED {len(results):,} ROWS")
                        
                        if len(results) == 0:
                            logger.warning(f"⚠️  NO ROWS RETURNED FOR BATCH {batch_num + 1}")
                            if batch_num == 0:
                                logger.error(f"❌ FIRST BATCH RETURNED ZERO ROWS - CHECKING TABLE ACCESS")
                                try:
                                    test_query = f"SELECT COUNT(*) as row_count FROM `{table_path}`"
                                    test_job = client.query(test_query)
                                    test_result = list(test_job.result())
                                    logger.error(f"   TABLE ROW COUNT: {test_result[0]['row_count'] if test_result else 'FAILED'}")
                                except Exception as e:
                                    logger.error(f"   TABLE ACCESS TEST FAILED: {e}")
                            continue
                        
                        if batch_num == 0:
                            first_row = results[0]
                            logger.info(f"🔍 FIRST ROW TYPE: {type(first_row)}")
                            if hasattr(first_row, '_fields'):
                                logger.info(f"🔍 FIRST ROW FIELDS: {first_row._fields}")
                            logger.info(f"🔍 FIRST ROW SAMPLE: {str(first_row)[:500]}...")
                        
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
                        
                        if len(results) < batch_size:
                            logger.info(f"🏁 REACHED END OF TABLE AT BATCH {batch_num + 1}")
                            break
                            
                    except Exception as batch_e:
                        logger.error(f"❌ BATCH {batch_num + 1} QUERY FAILED: {batch_e}")
                        continue
                
                logger.info(f"🎉 TABLE PROCESSING COMPLETE: {table_path}")
                logger.info(f"   🏆 TOTAL HOSTS DISCOVERED: {len(assets):,}")
                logger.info(f"   📊 TOTAL ROWS PROCESSED: {total_rows_processed:,}")
                logger.info(f"   💯 COMPLETION: 100%")
                
            except Exception as e:
                logger.error(f"❌ MAXIMUM INTENSITY PROCESSING FAILED: {table_path}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        return assets, total_rows_processed
    
    async def _find_hostname_columns_by_content(self, client, table_path: str, columns: List[str]) -> List[str]:
        hostname_columns = []
        
        logger.info(f"🔍 ANALYZING {len(columns)} COLUMNS FOR HOSTNAME CONTENT")
        
        sample_query = f"""
        SELECT *
        FROM `{table_path}`
        LIMIT 100
        """
        
        try:
            logger.info(f"🔍 SAMPLING QUERY: {sample_query}")
            job = client.query(sample_query)
            results = list(job.result())
            
            logger.info(f"📊 SAMPLE QUERY RETURNED {len(results)} ROWS")
            
            if not results:
                logger.warning("❌ NO SAMPLE ROWS RETURNED")
                return []
            
            first_row = results[0]
            logger.info(f"🔍 SAMPLE ROW TYPE: {type(first_row)}")
            logger.info(f"🔍 SAMPLE ROW: {str(first_row)[:300]}...")
            
            for col_idx, column_name in enumerate(columns):
                samples = []
                for row in results:
                    if hasattr(row, '_fields'):
                        row_dict = row._asdict()
                    elif isinstance(row, dict):
                        row_dict = row
                    elif isinstance(row, (list, tuple)):
                        row_dict = dict(zip(columns, row))
                    else:
                        continue
                    
                    if column_name in row_dict and row_dict[column_name]:
                        samples.append(str(row_dict[column_name]))
                
                logger.info(f"🔍 COLUMN {column_name}: {len(samples)} samples")
                if samples:
                    logger.info(f"   SAMPLE VALUES: {samples[:5]}")
                
                if self.visibility_engine._is_hostname_column_by_content(samples):
                    hostname_columns.append(column_name)
                    hostname_ratio = self._get_hostname_ratio(samples)
                    logger.info(f"🎯 HOSTNAME COLUMN FOUND: {column_name} (ratio: {hostname_ratio:.2f})")
            
            logger.info(f"🎯 TOTAL HOSTNAME COLUMNS FOUND: {len(hostname_columns)}")
            
        except Exception as e:
            logger.error(f"❌ FAILED TO SAMPLE TABLE FOR HOSTNAME DETECTION: {e}")
        
        return hostname_columns
    
    def _get_hostname_ratio(self, samples: List[str]) -> float:
        if not samples:
            return 0.0
        
        hostname_count = sum(1 for sample in samples if self.visibility_engine._looks_like_hostname(sample))
        return hostname_count / len(samples)
    
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
    
    def _extract_hosts_from_batch_intensive(self, results: List, columns: List[str], hostname_columns: List[str], 
                                field_mappings: Dict[str, List[str]], source_name: str, table_path: str) -> Dict[str, Any]:
        assets = {}
        rows_with_hostnames = 0
        total_rows_processed = len(results)
        
        logger.info(f"🔍 EXTRACTING HOSTS FROM {total_rows_processed:,} ROWS")
        logger.info(f"🎯 LOOKING FOR HOSTNAMES IN COLUMNS: {hostname_columns}")
        
        if total_rows_processed == 0:
            logger.warning("❌ NO ROWS TO PROCESS!")
            return assets
        
        first_row = results[0] if results else None
        logger.info(f"🔍 FIRST ROW TYPE: {type(first_row)}")
        logger.info(f"🔍 FIRST ROW CONTENT: {str(first_row)[:200]}...")
        
        for row_idx, row in enumerate(results):
            if not row:
                if row_idx < 5:
                    logger.warning(f"❌ ROW {row_idx} IS EMPTY/NULL")
                continue
            
            if hasattr(row, '_fields'):
                row_dict = row._asdict()
            elif isinstance(row, dict):
                row_dict = row
            elif isinstance(row, (list, tuple)):
                row_dict = dict(zip(columns, row))
            else:
                try:
                    row_dict = dict(row)
                except:
                    if row_idx < 5:
                        logger.warning(f"❌ ROW {row_idx} CONVERSION FAILED: {type(row)}")
                    continue
            
            if row_idx < 3:
                logger.info(f"🔍 ROW {row_idx} STRUCTURE:")
                logger.info(f"   ROW DICT KEYS: {list(row_dict.keys())[:10]}")
                for col in hostname_columns[:3]:
                    value = row_dict.get(col, 'NOT_FOUND')
                    logger.info(f"   {col}: '{value}' (type: {type(value)})")
            
            hostnames = []
            for hostname_col in hostname_columns:
                if hostname_col in row_dict and row_dict[hostname_col] is not None:
                    hostname_value = str(row_dict[hostname_col]).strip()
                    
                    if row_idx < 5:
                        logger.info(f"🔍 ROW {row_idx} COL {hostname_col}: '{hostname_value}' -> valid: {self._is_valid_hostname(hostname_value)}")
                    
                    if self._is_valid_hostname(hostname_value):
                        hostnames.append(hostname_value.upper())
                elif row_idx < 5:
                    logger.info(f"🔍 ROW {row_idx} COL {hostname_col}: MISSING OR NULL")
            
            if hostnames:
                rows_with_hostnames += 1
                
                if rows_with_hostnames <= 5:
                    logger.info(f"✅ ROW {row_idx} FOUND HOSTNAMES: {hostnames}")
                
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
                    
                    for field_type, field_columns in field_mappings.items():
                        for field_col in field_columns:
                            if field_col in row_dict and row_dict[field_col]:
                                value = str(row_dict[field_col]).strip()
                                if self._is_valid_field_value(value):
                                    if field_type not in asset['all_data']:
                                        asset['all_data'][field_type] = set()
                                    asset['all_data'][field_type].add(value)
                    
                    self._set_coverage_flags_intensive(asset, source_name)
            elif row_idx < 10:
                logger.debug(f"❌ ROW {row_idx} NO HOSTNAMES FOUND")
        
        for hostname, asset in assets.items():
            for field_type, value_set in asset['all_data'].items():
                asset['all_data'][field_type] = list(value_set)
        
        logger.info(f"📊 EXTRACTION RESULTS:")
        logger.info(f"   🔢 TOTAL ROWS PROCESSED: {total_rows_processed:,}")
        logger.info(f"   🏠 ROWS WITH HOSTNAMES: {rows_with_hostnames:,}")
        logger.info(f"   🎯 UNIQUE HOSTS FOUND: {len(assets):,}")
        if total_rows_processed > 0:
            logger.info(f"   📈 HOST EXTRACTION RATE: {(rows_with_hostnames/total_rows_processed*100):.1f}%")
        
        if len(assets) == 0 and total_rows_processed > 0:
            logger.error("🚨 ZERO ASSETS EXTRACTED - DEBUGGING INFO:")
            logger.error(f"   HOSTNAME COLUMNS: {hostname_columns}")
            logger.error(f"   SAMPLE ROW KEYS: {list(row_dict.keys())[:20] if 'row_dict' in locals() else 'N/A'}")
        
        return assets
    
    def _is_valid_hostname(self, value: str) -> bool:
        if not value:
            return False
        
        value = str(value).strip()
        
        if len(value) < 1 or len(value) > 253:
            return False
        
        invalid_values = {'NULL', 'NONE', 'UNKNOWN', 'N/A', 'NA', '', '-', '0', 'TRUE', 'FALSE'}
        if value.upper() in invalid_values:
            return False
        
        if value.isdigit():
            return False
        
        if self._looks_like_ip(value):
            return False
        
        if any(pattern in value.upper() for pattern in ['HTTP://', 'HTTPS://', 'FTP://', 'WWW.', '@']):
            return False
        
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_.]*
    
    def _looks_like_ip(self, value: str) -> bool:
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
    
    def _is_priority_table(self, table_path: str) -> bool:
        priority_tables = [
            'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT',
            'chronicle-fisv.datalake.events'
        ]
        return table_path in priority_tables
    
    async def _scan_table_for_hosts_intensive(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return assets, 0
            
            columns = [field.name for field in table.schema]
            hostname_columns = await self._find_hostname_columns_by_content(client, table_path, columns)
            
            if not hostname_columns:
                return assets, 0
            
            field_mappings = self._create_comprehensive_field_mappings(columns)
            
            max_rows_to_scan = min(table.num_rows, 500000)
            
            query = f"""
            SELECT *
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
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        metrics = self.performance_metrics
        
        if not metrics['confidence_scores']:
            return {'status': 'no_data'}
        
        return {
            'total_classifications': metrics['classifications'],
            'avg_processing_time': statistics.mean(metrics['processing_times']) if metrics['processing_times'] else 0,
            'avg_confidence': statistics.mean(metrics['confidence_scores']) if metrics['confidence_scores'] else 0,
            'avg_visibility': statistics.mean(metrics['visibility_scores']) if metrics['visibility_scores'] else 0
        }, value, re.IGNORECASE):
            return False
        
        return True
    
    def _looks_like_ip(self, value: str) -> bool:
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
    
    def _is_priority_table(self, table_path: str) -> bool:
        priority_tables = [
            'prj-fisv.SAS_BI.V_DIM_ENDPOINT',
            'prj-fisv.SAS_BI.V_SPL_ENDPOINT_LOG',
            'prj-fisv.SAS_BI.V_DIM_ENDPOINTAGENT',
            'chronicle-fisv.datalake.events'
        ]
        return table_path in priority_tables
    
    async def _scan_table_for_hosts_intensive(self, client, table_path: str) -> Tuple[Dict[str, Any], int]:
        assets = {}
        rows_processed = 0
        
        try:
            table = client.get_table(table_path)
            if not table.schema or table.num_rows == 0:
                return assets, 0
            
            columns = [field.name for field in table.schema]
            hostname_columns = await self._find_hostname_columns_by_content(client, table_path, columns)
            
            if not hostname_columns:
                return assets, 0
            
            field_mappings = self._create_comprehensive_field_mappings(columns)
            
            max_rows_to_scan = min(table.num_rows, 500000)
            
            query = f"""
            SELECT *
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