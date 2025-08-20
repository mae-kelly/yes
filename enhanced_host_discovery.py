import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
import sys

# Add gcp module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gcp.client import BigQueryClientManager
from core.quantum_types import QuantumAsset, LogMapping, DiscoveryMetrics
from ai.neural_engine import HyperIntelligence

logger = logging.getLogger(__name__)

class EnhancedHostDiscoveryEngine:
    def __init__(self, project_ids: List[str], config: Dict[str, Any]):
        self.project_ids = project_ids
        self.config = config
        self.intelligence = HyperIntelligence()
        
        # Host-centric data structure
        self.hosts: Dict[str, Dict[str, Any]] = {}  # hostname -> merged data
        self.host_tables: Dict[str, Set[str]] = defaultdict(set)  # hostname -> set of table paths
        self.processed_tables: Set[str] = set()
        
        # Target columns we're looking for
        self.target_columns = {
            'host': ['host', 'hostname', 'host_name', 'computer_name', 'server_name', 'machine_name', 'device_name', 'node_name'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'platform_type', 'deployment_type', 'hosting_type', 'env_type'],
            'region': ['region', 'geographic_region', 'geo_region', 'location_region', 'aws_region', 'azure_region', 'gcp_region'],
            'country': ['country', 'country_code', 'nation', 'geographic_country'],
            'data_center': ['data_center', 'datacenter', 'dc', 'facility', 'site'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region', 'cloud_zone'],
            'business_unit': ['business_unit', 'bu', 'org_unit', 'organization', 'division', 'department'],
            'cio': ['cio', 'chief_information_officer', 'it_org', 'it_organization'],
            'apm': ['apm', 'application_performance_monitoring', 'app_monitoring'],
            'app_class': ['app_class', 'application_class', 'application_type', 'app_type'],
            'system_classification': ['system_classification', 'sys_class', 'system_type', 'server_type', 'os_type'],
            'edr_coverage': ['edr_coverage', 'edr', 'endpoint_detection', 'crowdstrike', 'carbon_black', 'sentinel_one'],
            'tanium_coverage': ['tanium_coverage', 'tanium', 'endpoint_platform'],
            'dlp_agent_coverage': ['dlp_agent_coverage', 'dlp_coverage', 'dlp', 'data_loss_prevention', 'forcepoint', 'symantec_dlp'],
            'logging_in_splunk': ['logging_in_splunk', 'splunk_logging', 'splunk', 'spl_', 'universal_forwarder'],
            'logging_in_gso': ['logging_in_gso', 'gso_logging', 'gso', 'global_security_operations'],
            'domain': ['domain', 'dns_domain', 'fqdn_domain', 'ad_domain', 'network_domain']
        }
        
        # BigQuery client managers
        self.client_managers = {}
        self.clients = {}
        
        for project_id in project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                self.client_managers[project_id] = manager
                
                with manager.get_client() as client:
                    self.clients[project_id] = client
                    logger.info(f"✅ Connected to project: {project_id}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to connect to project {project_id}: {e}")
                continue
        
        if not self.clients:
            raise RuntimeError("Failed to connect to any BigQuery projects. Please check authentication.")
        
        self.sampling_config = {
            'max_sample_size': config.get('discovery_settings', {}).get('max_sample_size', 50000),  # Increased for better coverage
            'sample_ratio': config.get('discovery_settings', {}).get('sample_ratio', 0.2),  # Increased sampling
            'min_confidence': config.get('discovery_settings', {}).get('min_confidence', 0.6),  # Slightly lower threshold
            'batch_size': config.get('discovery_settings', {}).get('batch_size', 10000),
            'max_workers': config.get('discovery_settings', {}).get('max_workers', 16)  # Reduced for stability
        }
    
    async def discover_all_hosts(self) -> Dict[str, Dict[str, Any]]:
        """Main discovery method that finds all hosts across all projects"""
        logger.info(f"🔍 Starting comprehensive host discovery across {len(self.clients)} projects")
        logger.info(f"📊 Target columns: {list(self.target_columns.keys())}")
        
        # Phase 1: Discover all tables with host columns
        host_tables = {}
        
        with ThreadPoolExecutor(max_workers=self.sampling_config['max_workers']) as executor:
            futures = []
            
            for project_id in self.clients.keys():
                future = executor.submit(self._discover_project_host_tables, project_id)
                futures.append((project_id, future))
            
            for project_id, future in futures:
                try:
                    project_host_tables = future.result()
                    host_tables[project_id] = project_host_tables
                    logger.info(f"📋 Project {project_id}: Found {len(project_host_tables)} tables with host columns")
                except Exception as e:
                    logger.error(f"❌ Failed to discover tables in project {project_id}: {e}")
        
        # Phase 2: Extract host data from all discovered tables
        logger.info("📥 Extracting host data from discovered tables...")
        
        with ThreadPoolExecutor(max_workers=self.sampling_config['max_workers']) as executor:
            futures = []
            
            for project_id, tables in host_tables.items():
                for table_info in tables:
                    future = executor.submit(self._extract_host_data_from_table, project_id, table_info)
                    futures.append(future)
            
            for future in as_completed(futures):
                try:
                    table_hosts = future.result()
                    self._merge_host_data(table_hosts)
                except Exception as e:
                    logger.error(f"❌ Failed to extract host data: {e}")
        
        # Phase 3: Clean and deduplicate hosts
        self._clean_and_deduplicate_hosts()
        
        # Phase 4: Calculate coverage metrics
        self._calculate_host_metrics()
        
        logger.info(f"✅ Discovery complete: {len(self.hosts)} unique hosts found")
        return self.hosts
    
    def _discover_project_host_tables(self, project_id: str) -> List[Dict[str, Any]]:
        """Discover all tables in a project that contain host columns"""
        host_tables = []
        
        manager = self.client_managers.get(project_id)
        if not manager:
            return host_tables
        
        try:
            with manager.get_client() as client:
                # Get all datasets
                datasets = list(client.list_datasets(project=project_id))
                logger.info(f"🗂️  Project {project_id}: Scanning {len(datasets)} datasets")
                
                for dataset in datasets:
                    try:
                        # Get all tables in dataset
                        tables = list(client.list_tables(dataset))
                        
                        for table_ref in tables:
                            table_path = f"{project_id}.{dataset.dataset_id}.{table_ref.table_id}"
                            
                            if table_path in self.processed_tables:
                                continue
                            
                            try:
                                # Get table schema
                                table = client.get_table(table_path)
                                
                                if table.num_rows == 0:
                                    continue
                                
                                # Check for host columns
                                host_columns = self._find_host_columns(table.schema)
                                
                                if host_columns:
                                    # Map all relevant columns
                                    column_mapping = self._map_table_columns(table.schema)
                                    
                                    table_info = {
                                        'table_path': table_path,
                                        'host_columns': host_columns,
                                        'column_mapping': column_mapping,
                                        'row_count': table.num_rows,
                                        'dataset': dataset.dataset_id,
                                        'table_name': table_ref.table_id
                                    }
                                    
                                    host_tables.append(table_info)
                                    logger.info(f"🎯 Found host table: {table_path} ({table.num_rows:,} rows, {len(host_columns)} host columns)")
                                
                                self.processed_tables.add(table_path)
                                
                            except Exception as e:
                                logger.debug(f"❌ Failed to process table {table_path}: {e}")
                                continue
                    
                    except Exception as e:
                        logger.error(f"❌ Failed to process dataset {dataset.dataset_id}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"❌ Failed to discover tables in project {project_id}: {e}")
        
        return host_tables
    
    def _find_host_columns(self, schema) -> List[str]:
        """Find all columns that contain 'host' in their name"""
        host_columns = []
        
        for field in schema:
            column_name = field.name.lower()
            
            # Check if 'host' is in the column name
            if 'host' in column_name:
                host_columns.append(field.name)
        
        return host_columns
    
    def _map_table_columns(self, schema) -> Dict[str, str]:
        """Map table columns to our target columns"""
        column_mapping = {}
        
        for field in schema:
            column_name = field.name.lower()
            
            # Check against each target column pattern
            for target_col, patterns in self.target_columns.items():
                for pattern in patterns:
                    if pattern.lower() in column_name or column_name in pattern.lower():
                        if target_col not in column_mapping:  # Take first match
                            column_mapping[target_col] = field.name
                        break
        
        return column_mapping
    
    def _extract_host_data_from_table(self, project_id: str, table_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract host data from a specific table"""
        table_hosts = {}
        table_path = table_info['table_path']
        host_columns = table_info['host_columns']
        column_mapping = table_info['column_mapping']
        
        manager = self.client_managers.get(project_id)
        if not manager:
            return table_hosts
        
        try:
            with manager.get_client() as client:
                # Build SELECT clause for all mapped columns
                select_columns = []
                
                # Always include host columns
                for host_col in host_columns:
                    select_columns.append(host_col)
                
                # Add mapped columns
                for target_col, actual_col in column_mapping.items():
                    if actual_col not in select_columns:
                        select_columns.append(actual_col)
                
                # Calculate sample size
                row_count = table_info['row_count']
                sample_size = min(self.sampling_config['max_sample_size'], 
                                 int(row_count * self.sampling_config['sample_ratio']))
                
                # Build query with better sampling
                query = f"""
                SELECT {', '.join(select_columns)}
                FROM `{table_path}`
                WHERE {' OR '.join([f"{col} IS NOT NULL" for col in host_columns])}
                  AND RAND() < {min(1.0, sample_size / row_count)}
                LIMIT {sample_size}
                """
                
                logger.debug(f"🔍 Extracting from {table_path}: {sample_size:,} samples")
                
                query_job = client.query(query)
                results = query_job.result()
                
                processed_rows = 0
                for row in results:
                    try:
                        # Extract host values from all host columns
                        for host_col in host_columns:
                            hostname = getattr(row, host_col, None)
                            
                            if hostname and self._is_valid_hostname(str(hostname)):
                                hostname_clean = str(hostname).strip().lower()
                                
                                # Initialize host data
                                if hostname_clean not in table_hosts:
                                    table_hosts[hostname_clean] = {
                                        'hostname': hostname_clean,
                                        'source_tables': set(),
                                        'data_sources': defaultdict(set)
                                    }
                                
                                # Add table source
                                table_hosts[hostname_clean]['source_tables'].add(table_path)
                                
                                # Extract mapped data
                                for target_col, actual_col in column_mapping.items():
                                    value = getattr(row, actual_col, None)
                                    if value is not None and str(value).strip():
                                        clean_value = str(value).strip()
                                        table_hosts[hostname_clean][target_col] = clean_value
                                        table_hosts[hostname_clean]['data_sources'][target_col].add(table_path)
                        
                        processed_rows += 1
                        
                    except Exception as e:
                        logger.debug(f"❌ Failed to process row in {table_path}: {e}")
                        continue
                
                logger.info(f"📊 Extracted {processed_rows:,} rows from {table_path}, found {len(table_hosts)} unique hosts")
                
        except Exception as e:
            logger.error(f"❌ Failed to extract data from {table_path}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return table_hosts
    
    def _merge_host_data(self, table_hosts: Dict[str, Dict[str, Any]]):
        """Merge host data from a table into the global hosts collection"""
        for hostname, host_data in table_hosts.items():
            if hostname not in self.hosts:
                self.hosts[hostname] = {
                    'hostname': hostname,
                    'source_tables': set(),
                    'data_sources': defaultdict(set),
                    'confidence_scores': defaultdict(float)
                }
            
            # Merge source tables
            self.hosts[hostname]['source_tables'].update(host_data['source_tables'])
            
            # Merge data fields with conflict resolution
            for field, value in host_data.items():
                if field in ['hostname', 'source_tables', 'data_sources']:
                    continue
                
                if field not in self.hosts[hostname] or not self.hosts[hostname][field]:
                    # No existing value, use this one
                    self.hosts[hostname][field] = value
                    if field in host_data.get('data_sources', {}):
                        self.hosts[hostname]['data_sources'][field].update(host_data['data_sources'][field])
                elif self.hosts[hostname][field] != value:
                    # Conflict resolution: prefer more recent or more authoritative source
                    current_sources = len(self.hosts[hostname]['data_sources'].get(field, set()))
                    new_sources = len(host_data.get('data_sources', {}).get(field, set()))
                    
                    if new_sources > current_sources:
                        # New value has more sources, use it
                        self.hosts[hostname][field] = value
                        if field in host_data.get('data_sources', {}):
                            self.hosts[hostname]['data_sources'][field].update(host_data['data_sources'][field])
                    else:
                        # Keep existing value but note the conflict
                        if field in host_data.get('data_sources', {}):
                            self.hosts[hostname]['data_sources'][field].update(host_data['data_sources'][field])
    
    def _clean_and_deduplicate_hosts(self):
        """Clean and deduplicate host data"""
        logger.info("🧹 Cleaning and deduplicating host data...")
        
        cleaned_hosts = {}
        
        for hostname, host_data in self.hosts.items():
            # Additional hostname validation
            if not self._is_valid_hostname(hostname):
                continue
            
            # Clean boolean fields
            for bool_field in ['edr_coverage', 'tanium_coverage', 'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso']:
                if bool_field in host_data:
                    value = str(host_data[bool_field]).lower()
                    host_data[bool_field] = value in ['true', '1', 'yes', 'y', 'enabled', 'active']
            
            # Standardize text fields
            for text_field in ['infrastructure_type', 'region', 'country', 'business_unit', 'system_classification']:
                if text_field in host_data and host_data[text_field]:
                    host_data[text_field] = str(host_data[text_field]).strip().lower()
            
            # Calculate confidence score based on data completeness
            total_fields = len(self.target_columns)
            populated_fields = sum(1 for field in self.target_columns.keys() if host_data.get(field))
            confidence = populated_fields / total_fields
            host_data['data_completeness'] = confidence
            
            cleaned_hosts[hostname] = host_data
        
        self.hosts = cleaned_hosts
        logger.info(f"✅ Cleaned data for {len(self.hosts)} hosts")
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """Enhanced hostname validation"""
        if not hostname or not isinstance(hostname, str):
            return False
        
        hostname = hostname.strip()
        
        if len(hostname) < 1 or len(hostname) > 253:
            return False
        
        # Invalid characters
        invalid_chars = ['@', '/', '\\', ' ', '\t', '\n', '|', ';', '"', "'", '(', ')', '[', ']', '{', '}']
        if any(char in hostname for char in invalid_chars):
            return False
        
        # Invalid values
        invalid_values = ['null', 'none', 'unknown', 'n/a', '', 'test', 'localhost', '127.0.0.1', 'undefined']
        if hostname.lower() in invalid_values:
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', hostname):
            return False
        
        return True
    
    def _calculate_host_metrics(self):
        """Calculate metrics for discovered hosts"""
        if not self.hosts:
            return
        
        total_hosts = len(self.hosts)
        
        # Coverage metrics
        coverage_metrics = {}
        for coverage_field in ['edr_coverage', 'tanium_coverage', 'dlp_agent_coverage', 'logging_in_splunk', 'logging_in_gso']:
            covered_count = sum(1 for h in self.hosts.values() if h.get(coverage_field, False))
            coverage_metrics[coverage_field] = {
                'count': covered_count,
                'percentage': (covered_count / total_hosts) * 100,
                'gap_count': total_hosts - covered_count
            }
        
        # Completeness metrics
        completeness_scores = [h.get('data_completeness', 0) for h in self.hosts.values()]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        # Distribution metrics
        distributions = {}
        for field in ['infrastructure_type', 'region', 'country', 'business_unit', 'system_classification']:
            field_values = [h.get(field) for h in self.hosts.values() if h.get(field)]
            distributions[field] = dict(Counter(field_values))
        
        self.metrics = {
            'total_hosts': total_hosts,
            'coverage': coverage_metrics,
            'average_completeness': avg_completeness,
            'distributions': distributions,
            'high_completeness_hosts': sum(1 for s in completeness_scores if s >= 0.8),
            'low_completeness_hosts': sum(1 for s in completeness_scores if s < 0.5)
        }
        
        logger.info(f"📈 Calculated metrics for {total_hosts} hosts (avg completeness: {avg_completeness:.1%})")
    
    def get_hosts_dataframe(self):
        """Convert hosts to a pandas-like structure for easy export"""
        import pandas as pd
        
        rows = []
        for hostname, host_data in self.hosts.items():
            row = {'hostname': hostname}
            
            # Add all target columns
            for col in self.target_columns.keys():
                row[col] = host_data.get(col, '')
            
            # Add metadata
            row['source_table_count'] = len(host_data.get('source_tables', set()))
            row['data_completeness'] = host_data.get('data_completeness', 0)
            row['source_tables'] = ', '.join(host_data.get('source_tables', set()))
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def export_to_csv(self, output_path: str):
        """Export hosts to CSV"""
        df = self.get_hosts_dataframe()
        df.to_csv(output_path, index=False)
        logger.info(f"📁 Exported {len(df)} hosts to {output_path}")
    
    def get_summary_report(self) -> str:
        """Generate a summary report"""
        if not hasattr(self, 'metrics'):
            self._calculate_host_metrics()
        
        report = []
        report.append("="*80)
        report.append("HOST DISCOVERY SUMMARY REPORT")
        report.append("="*80)
        report.append(f"\nTotal Unique Hosts Discovered: {self.metrics['total_hosts']:,}")
        report.append(f"Average Data Completeness: {self.metrics['average_completeness']:.1%}")
        report.append(f"High Completeness Hosts (≥80%): {self.metrics['high_completeness_hosts']:,}")
        report.append(f"Low Completeness Hosts (<50%): {self.metrics['low_completeness_hosts']:,}")
        
        report.append("\n" + "="*50)
        report.append("COVERAGE METRICS")
        report.append("="*50)
        
        for coverage_type, stats in self.metrics['coverage'].items():
            report.append(f"{coverage_type:25} {stats['percentage']:6.1f}% ({stats['count']:,}/{self.metrics['total_hosts']:,})")
        
        report.append("\n" + "="*50)
        report.append("INFRASTRUCTURE DISTRIBUTION")
        report.append("="*50)
        
        infra_dist = self.metrics['distributions'].get('infrastructure_type', {})
        for infra_type, count in sorted(infra_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / self.metrics['total_hosts']) * 100
            report.append(f"{infra_type:25} {count:6,} ({percentage:5.1f}%)")
        
        report.append("\n" + "="*50)
        report.append("REGIONAL DISTRIBUTION")
        report.append("="*50)
        
        region_dist = self.metrics['distributions'].get('region', {})
        for region, count in sorted(region_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / self.metrics['total_hosts']) * 100
            report.append(f"{region:25} {count:6,} ({percentage:5.1f}%)")
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)

# Helper imports
from collections import Counter