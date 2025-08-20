import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import hashlib
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import pickle
import os
import statistics
import gzip
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

class UltimateDatasetGenerator:
    def __init__(self, project_ids: List[str], config: Dict[str, Any]):
        self.project_ids = project_ids
        self.config = config
        
        # Ultimate sampling configuration
        self.samples_per_table = config.get('samples_per_table', 50)
        self.max_tables_per_project = config.get('max_tables_per_project', 999999)
        self.include_large_tables = config.get('include_large_tables', True)
        self.deep_analysis_mode = config.get('deep_analysis_mode', True)
        
        # Master dataset structure
        self.ultimate_dataset = {
            'generation_metadata': {
                'creation_timestamp': datetime.now().isoformat(),
                'generator_version': '1.0.0',
                'configuration': config,
                'projects_targeted': project_ids
            },
            'project_catalog': {},
            'dataset_catalog': {},
            'table_catalog': {},
            'column_universe': {},
            'pattern_universe': {},
            'relationship_graph': {},
            'statistical_universe': {},
            'raw_table_samples': {},
            'cross_table_analysis': {},
            'corporate_vocabulary': {},
            'data_lineage_hints': {}
        }
        
        # Processing statistics
        self.processing_stats = {
            'start_time': time.time(),
            'projects_discovered': 0,
            'datasets_discovered': 0,
            'tables_discovered': 0,
            'columns_discovered': 0,
            'rows_sampled': 0,
            'patterns_detected': 0,
            'relationships_identified': 0,
            'processing_errors': 0,
            'processing_warnings': 0
        }
        
        # Global pattern tracking
        self.global_patterns = {
            'column_names': Counter(),
            'data_formats': Counter(),
            'naming_conventions': Counter(),
            'value_patterns': Counter(),
            'table_naming_patterns': Counter(),
            'dataset_naming_patterns': Counter(),
            'cross_table_relationships': defaultdict(list)
        }
        
        # Corporate vocabulary extraction
        self.corporate_vocab = {
            'technical_terms': set(),
            'business_terms': set(),
            'product_names': set(),
            'location_names': set(),
            'department_names': set(),
            'system_names': set(),
            'naming_patterns': defaultdict(list)
        }
        
        from gcp.client import BigQueryClientManager
        self.client_managers = {}
        self.authenticated_projects = []
        
        for project_id in project_ids:
            try:
                manager = BigQueryClientManager(project_id)
                if manager.test_connection():
                    self.client_managers[project_id] = manager
                    self.authenticated_projects.append(project_id)
                    logger.info(f"✅ Authenticated to: {project_id}")
                else:
                    logger.warning(f"⚠️ Authentication failed: {project_id}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to {project_id}: {e}")
        
        if not self.authenticated_projects:
            raise RuntimeError("No projects accessible for dataset generation")
        
        logger.info(f"🚀 Ultimate Dataset Generator initialized for {len(self.authenticated_projects)} projects")
    
    async def generate_ultimate_dataset(self) -> Dict[str, Any]:
        logger.info("🎯 Generating ULTIMATE AI training dataset...")
        logger.info("This will capture EVERYTHING across your BigQuery environment")
        
        # Phase 1: Complete Infrastructure Discovery
        await self._discover_complete_infrastructure()
        
        # Phase 2: Exhaustive Data Sampling
        await self._perform_exhaustive_sampling()
        
        # Phase 3: Deep Pattern Analysis
        await self._perform_deep_pattern_analysis()
        
        # Phase 4: Relationship Mining
        await self._mine_data_relationships()
        
        # Phase 5: Corporate Vocabulary Extraction
        await self._extract_corporate_vocabulary()
        
        # Phase 6: Cross-Table Intelligence
        await self._perform_cross_table_intelligence()
        
        # Phase 7: Statistical Universe Creation
        await self._create_statistical_universe()
        
        # Phase 8: Final Dataset Assembly
        final_dataset = await self._assemble_final_dataset()
        
        # Phase 9: Multi-Format Export
        await self._export_ultimate_dataset(final_dataset)
        
        return final_dataset
    
    async def _discover_complete_infrastructure(self):
        logger.info("📡 Phase 1: Discovering complete BigQuery infrastructure...")
        
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = []
            
            for project_id, manager in self.client_managers.items():
                future = executor.submit(self._discover_project_infrastructure, project_id, manager)
                futures.append((project_id, future))
            
            for project_id, future in futures:
                try:
                    project_catalog = future.result()
                    self.ultimate_dataset['project_catalog'][project_id] = project_catalog
                    self.processing_stats['projects_discovered'] += 1
                    logger.info(f"📊 {project_id}: {project_catalog['total_datasets']} datasets, {project_catalog['total_tables']} tables")
                except Exception as e:
                    logger.error(f"❌ Infrastructure discovery failed for {project_id}: {e}")
                    self.processing_stats['processing_errors'] += 1
    
    def _discover_project_infrastructure(self, project_id: str, manager) -> Dict[str, Any]:
        project_catalog = {
            'project_id': project_id,
            'discovery_timestamp': datetime.now().isoformat(),
            'datasets': {},
            'total_datasets': 0,
            'total_tables': 0,
            'total_estimated_rows': 0,
            'total_estimated_bytes': 0,
            'largest_tables': [],
            'newest_tables': [],
            'oldest_tables': []
        }
        
        try:
            with manager.get_client() as client:
                # Get project information
                try:
                    project = client.get_project(project_id)
                    project_catalog['project_info'] = {
                        'friendly_name': project.friendly_name,
                        'description': project.description,
                        'location': getattr(project, 'location', None)
                    }
                except:
                    project_catalog['project_info'] = {'friendly_name': project_id}
                
                # Discover all datasets
                datasets = list(client.list_datasets(project=project_id, max_results=10000))
                
                all_tables_info = []
                
                for dataset in datasets:
                    dataset_id = dataset.dataset_id
                    
                    try:
                        dataset_obj = client.get_dataset(dataset)
                        
                        dataset_info = {
                            'dataset_id': dataset_id,
                            'description': dataset_obj.description,
                            'created': dataset_obj.created.isoformat() if dataset_obj.created else None,
                            'modified': dataset_obj.modified.isoformat() if dataset_obj.modified else None,
                            'location': dataset_obj.location,
                            'tables': {},
                            'total_tables': 0,
                            'total_rows': 0,
                            'total_bytes': 0
                        }
                        
                        # Get all tables in dataset
                        tables = list(client.list_tables(dataset, max_results=10000))
                        
                        for table_ref in tables:
                            table_id = table_ref.table_id
                            table_path = f"{project_id}.{dataset_id}.{table_id}"
                            
                            try:
                                table = client.get_table(table_path)
                                
                                table_info = {
                                    'table_id': table_id,
                                    'full_path': table_path,
                                    'table_type': table.table_type,
                                    'num_rows': table.num_rows,
                                    'num_bytes': table.num_bytes,
                                    'created': table.created.isoformat() if table.created else None,
                                    'modified': table.modified.isoformat() if table.modified else None,
                                    'expires': table.expires.isoformat() if table.expires else None,
                                    'description': table.description,
                                    'schema_fields': len(table.schema),
                                    'schema_summary': [
                                        {
                                            'name': field.name,
                                            'type': field.field_type,
                                            'mode': field.mode
                                        } for field in table.schema
                                    ],
                                    'partitioning': str(table.time_partitioning) if table.time_partitioning else None,
                                    'clustering': table.clustering_fields if table.clustering_fields else None
                                }
                                
                                dataset_info['tables'][table_id] = table_info
                                dataset_info['total_rows'] += table.num_rows or 0
                                dataset_info['total_bytes'] += table.num_bytes or 0
                                
                                all_tables_info.append(table_info)
                                self.processing_stats['tables_discovered'] += 1
                                self.processing_stats['columns_discovered'] += len(table.schema)
                                
                            except Exception as e:
                                logger.debug(f"Failed to get table info for {table_path}: {e}")
                                self.processing_stats['processing_warnings'] += 1
                        
                        dataset_info['total_tables'] = len(dataset_info['tables'])
                        project_catalog['datasets'][dataset_id] = dataset_info
                        project_catalog['total_tables'] += dataset_info['total_tables']
                        project_catalog['total_estimated_rows'] += dataset_info['total_rows']
                        project_catalog['total_estimated_bytes'] += dataset_info['total_bytes']
                        
                        self.processing_stats['datasets_discovered'] += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to process dataset {dataset_id}: {e}")
                        self.processing_stats['processing_warnings'] += 1
                
                project_catalog['total_datasets'] = len(project_catalog['datasets'])
                
                # Identify largest, newest, and oldest tables
                if all_tables_info:
                    project_catalog['largest_tables'] = sorted(
                        all_tables_info, 
                        key=lambda x: x['num_bytes'] or 0, 
                        reverse=True
                    )[:20]
                    
                    tables_with_dates = [t for t in all_tables_info if t['created']]
                    if tables_with_dates:
                        project_catalog['newest_tables'] = sorted(
                            tables_with_dates,
                            key=lambda x: x['created'],
                            reverse=True
                        )[:20]
                        
                        project_catalog['oldest_tables'] = sorted(
                            tables_with_dates,
                            key=lambda x: x['created']
                        )[:20]
        
        except Exception as e:
            logger.error(f"Failed to discover infrastructure for {project_id}: {e}")
            self.processing_stats['processing_errors'] += 1
        
        return project_catalog
    
    async def _perform_exhaustive_sampling(self):
        logger.info("🔬 Phase 2: Performing exhaustive data sampling...")
        
        all_tables = []
        for project_id, project_catalog in self.ultimate_dataset['project_catalog'].items():
            for dataset_id, dataset_info in project_catalog['datasets'].items():
                for table_id, table_info in dataset_info['tables'].items():
                    all_tables.append({
                        'project_id': project_id,
                        'dataset_id': dataset_id,
                        'table_id': table_id,
                        'full_path': table_info['full_path'],
                        'num_rows': table_info['num_rows'],
                        'num_bytes': table_info['num_bytes'],
                        'schema_fields': table_info['schema_fields']
                    })
        
        logger.info(f"📋 Sampling {len(all_tables)} tables...")
        
        # Process tables in batches
        batch_size = 50
        for i in range(0, len(all_tables), batch_size):
            batch = all_tables[i:i+batch_size]
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                
                for table_info in batch:
                    project_id = table_info['project_id']
                    manager = self.client_managers.get(project_id)
                    if manager:
                        future = executor.submit(
                            self._sample_table_exhaustively, 
                            manager, 
                            table_info
                        )
                        futures.append((table_info['full_path'], future))
                
                for table_path, future in futures:
                    try:
                        sample_data = future.result()
                        if sample_data:
                            self.ultimate_dataset['raw_table_samples'][table_path] = sample_data
                            self.processing_stats['rows_sampled'] += len(sample_data.get('sample_rows', []))
                    except Exception as e:
                        logger.debug(f"Sampling failed for {table_path}: {e}")
                        self.processing_stats['processing_warnings'] += 1
            
            # Progress update
            progress = min(100, ((i + batch_size) / len(all_tables)) * 100)
            logger.info(f"📈 Sampling progress: {progress:.1f}% ({i + batch_size}/{len(all_tables)} tables)")
    
    def _sample_table_exhaustively(self, manager, table_info: Dict[str, Any]) -> Dict[str, Any]:
        table_path = table_info['full_path']
        num_rows = table_info['num_rows'] or 0
        
        if num_rows == 0:
            return None
        
        try:
            with manager.get_client() as client:
                table = client.get_table(table_path)
                
                # Build comprehensive sampling query
                columns = [field.name for field in table.schema]
                if not columns:
                    return None
                
                safe_columns = [f"`{col}`" for col in columns]
                
                # Dynamic sampling strategy based on table size
                if num_rows <= 1000:
                    # Small table: sample everything
                    sample_ratio = 1.0
                    limit = num_rows
                elif num_rows <= 10000:
                    # Medium table: sample 50%
                    sample_ratio = 0.5
                    limit = min(self.samples_per_table * 2, num_rows)
                else:
                    # Large table: intelligent sampling
                    sample_ratio = min(0.1, self.samples_per_table / num_rows)
                    limit = self.samples_per_table
                
                # Multiple sampling strategies for comprehensive coverage
                queries = []
                
                # Random sampling
                queries.append(f"""
                SELECT {', '.join(safe_columns)}
                FROM `{table_path}`
                WHERE RAND() < {sample_ratio}
                LIMIT {limit}
                """)
                
                # Recent data sampling (if has timestamp columns)
                timestamp_columns = [col for col in columns if any(
                    word in col.lower() for word in ['time', 'date', 'timestamp', 'created', 'modified']
                )]
                
                if timestamp_columns and num_rows > 1000:
                    timestamp_col = timestamp_columns[0]
                    queries.append(f"""
                    SELECT {', '.join(safe_columns)}
                    FROM `{table_path}`
                    ORDER BY `{timestamp_col}` DESC
                    LIMIT {min(20, limit // 3)}
                    """)
                
                # Collect all samples
                all_sample_rows = []
                schema_info = []
                
                for field in table.schema:
                    schema_info.append({
                        'name': field.name,
                        'type': field.field_type,
                        'mode': field.mode,
                        'description': field.description,
                        'fields': [subfield.name for subfield in field.fields] if field.fields else None
                    })
                
                for query in queries:
                    try:
                        query_job = client.query(query)
                        results = query_job.result(timeout=120)
                        
                        for row in results:
                            row_dict = {}
                            for col in columns:
                                value = getattr(row, col, None)
                                if value is not None:
                                    # Handle complex data types
                                    if isinstance(value, (list, dict)):
                                        row_dict[col] = json.dumps(value) if len(str(value)) < 1000 else str(value)[:1000]
                                    elif isinstance(value, bytes):
                                        row_dict[col] = base64.b64encode(value).decode('utf-8')[:500]
                                    else:
                                        row_dict[col] = str(value)[:1000]  # Limit field length
                                else:
                                    row_dict[col] = None
                            
                            all_sample_rows.append(row_dict)
                        
                    except Exception as e:
                        logger.debug(f"Query failed for {table_path}: {e}")
                        continue
                
                if not all_sample_rows:
                    return None
                
                # Comprehensive analysis of sampled data
                comprehensive_analysis = self._perform_comprehensive_column_analysis(
                    columns, all_sample_rows, table_path
                )
                
                return {
                    'table_metadata': {
                        'full_path': table_path,
                        'total_rows': num_rows,
                        'total_bytes': table_info['num_bytes'],
                        'schema_fields_count': table_info['schema_fields'],
                        'sampling_timestamp': datetime.now().isoformat(),
                        'sampling_strategy': 'exhaustive_multi_method',
                        'sample_coverage_ratio': len(all_sample_rows) / max(num_rows, 1)
                    },
                    'schema_detailed': schema_info,
                    'columns': columns,
                    'sample_rows': all_sample_rows[:self.samples_per_table],  # Limit final output
                    'total_samples_collected': len(all_sample_rows),
                    'comprehensive_analysis': comprehensive_analysis,
                    'table_intelligence': self._extract_table_intelligence(
                        table_path, columns, all_sample_rows
                    )
                }
                
        except Exception as e:
            logger.debug(f"Exhaustive sampling failed for {table_path}: {e}")
            return None
    
    def _perform_comprehensive_column_analysis(self, columns: List[str], sample_rows: List[Dict], table_path: str) -> Dict[str, Any]:
        analysis = {}
        
        for column in columns:
            values = [row.get(column) for row in sample_rows]
            non_null_values = [v for v in values if v is not None]
            string_values = [str(v) for v in non_null_values if v is not None]
            
            column_analysis = {
                # Basic statistics
                'total_samples': len(values),
                'non_null_count': len(non_null_values),
                'null_percentage': ((len(values) - len(non_null_values)) / len(values)) * 100 if values else 0,
                'unique_count': len(set(string_values)),
                'uniqueness_ratio': len(set(string_values)) / len(string_values) if string_values else 0,
                
                # Sample data
                'sample_values': string_values[:30],
                'unique_values': list(set(string_values))[:50],
                'most_common_values': dict(Counter(string_values).most_common(20)),
                
                # Advanced pattern detection
                'detected_patterns': self._detect_comprehensive_patterns(string_values),
                'format_analysis': self._analyze_data_formats(string_values),
                'semantic_analysis': self._analyze_semantic_content(column, string_values),
                'statistical_profile': self._create_statistical_profile(string_values),
                'quality_indicators': self._assess_data_quality(string_values),
                'corporate_terminology': self._extract_corporate_terms(column, string_values),
                
                # Relationship hints
                'potential_relationships': self._identify_potential_relationships(column, string_values, table_path),
                'data_lineage_hints': self._extract_lineage_hints(column, string_values, table_path)
            }
            
            analysis[column] = column_analysis
            
            # Update global patterns
            self.global_patterns['column_names'][column] += 1
            for pattern in column_analysis['detected_patterns']:
                self.global_patterns['data_formats'][pattern] += 1
        
        return analysis
    
    def _detect_comprehensive_patterns(self, values: List[str]) -> List[str]:
        if not values:
            return []
        
        patterns = []
        
        # Network patterns
        if any(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', v) for v in values):
            patterns.append('ipv4_addresses')
        if any(re.match(r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$', v) for v in values):
            patterns.append('ipv6_addresses')
        if any(re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', v) for v in values):
            patterns.append('mac_addresses')
        
        # Hostname patterns
        if any(re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', v) for v in values):
            if any('.' in v for v in values):
                patterns.append('fqdn_hostnames')
            patterns.append('hostnames')
        
        # Temporal patterns
        if any(re.match(r'^\d{4}-\d{2}-\d{2}$', v) for v in values):
            patterns.append('iso_dates')
        if any(re.match(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', v) for v in values):
            patterns.append('iso_datetimes')
        if any(re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', v) for v in values):
            patterns.append('us_dates')
        if any(re.match(r'^\d+$', v) and len(v) == 10 for v in values):
            patterns.append('unix_timestamps')
        
        # Identifier patterns
        if any(re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', v) for v in values):
            patterns.append('uuids')
        if any(re.match(r'^[A-Z0-9]{6,20}$', v) for v in values):
            patterns.append('alphanumeric_ids')
        if any(re.match(r'^\d{5,20}$', v) for v in values):
            patterns.append('numeric_ids')
        
        # Security patterns
        if any(v.lower() in ['true', 'false', 'yes', 'no', '1', '0', 'enabled', 'disabled', 'active', 'inactive'] for v in values):
            patterns.append('boolean_flags')
        if any('hash' in v.lower() or len(v) in [32, 40, 64, 128] and all(c in '0123456789abcdefABCDEF' for c in v) for v in values):
            patterns.append('hash_values')
        
        # Communication patterns
        if any(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v) for v in values):
            patterns.append('email_addresses')
        if any(v.startswith(('http://', 'https://')) for v in values):
            patterns.append('urls')
        if any(re.match(r'^\+?[\d\s\-\(\)]+$', v) and len(v) >= 10 for v in values):
            patterns.append('phone_numbers')
        
        # Naming convention patterns
        if any('_' in v and v.islower() for v in values):
            patterns.append('snake_case')
        if any(re.match(r'^[a-z][a-zA-Z0-9]*$', v) for v in values):
            patterns.append('camel_case')
        if any(re.match(r'^[A-Z][a-z]+([A-Z][a-z]*)*$', v) for v in values):
            patterns.append('pascal_case')
        if any('-' in v and v.islower() for v in values):
            patterns.append('kebab_case')
        if any(v.isupper() and '_' in v for v in values):
            patterns.append('constant_case')
        
        # Data structure patterns
        if any(v.startswith(('{', '[')) for v in values):
            patterns.append('json_data')
        if any('<' in v and '>' in v for v in values):
            patterns.append('xml_data')
        if any(',' in v and len(v.split(',')) > 2 for v in values):
            patterns.append('csv_data')
        
        # File system patterns
        if any(v.startswith('/') or '\\' in v for v in values):
            patterns.append('file_paths')
        if any('.' in v and v.split('.')[-1].lower() in ['txt', 'csv', 'json', 'xml', 'log', 'exe', 'dll', 'so'] for v in values):
            patterns.append('file_names')
        
        # Business patterns
        if any(re.match(r'^\$?[\d,]+\.?\d*$', v) for v in values):
            patterns.append('currency_amounts')
        if any(re.match(r'^\d{3}-\d{2}-\d{4}$', v) for v in values):
            patterns.append('ssn_format')
        if any(re.match(r'^\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}$', v) for v in values):
            patterns.append('credit_card_format')
        
        return patterns
    
    def _analyze_data_formats(self, values: List[str]) -> Dict[str, Any]:
        if not values:
            return {}
        
        format_analysis = {
            'length_distribution': dict(Counter(len(v) for v in values)),
            'character_sets': {
                'numeric_only': sum(1 for v in values if v.isdigit()),
                'alpha_only': sum(1 for v in values if v.isalpha()),
                'alphanumeric_only': sum(1 for v in values if v.isalnum()),
                'contains_spaces': sum(1 for v in values if ' ' in v),
                'contains_special_chars': sum(1 for v in values if not v.isalnum() and not v.isspace()),
                'all_uppercase': sum(1 for v in values if v.isupper()),
                'all_lowercase': sum(1 for v in values if v.islower()),
                'mixed_case': sum(1 for v in values if any(c.isupper() for c in v) and any(c.islower() for c in v))
            },
            'common_prefixes': dict(Counter(v[:3] for v in values if len(v) >= 3).most_common(10)),
            'common_suffixes': dict(Counter(v[-3:] for v in values if len(v) >= 3).most_common(10)),
            'regex_patterns': self._extract_regex_patterns(values),
            'encoding_hints': self._detect_encoding_patterns(values)
        }
        
        return format_analysis
    
    def _analyze_semantic_content(self, column_name: str, values: List[str]) -> Dict[str, Any]:
        column_lower = column_name.lower()
        
        semantic_indicators = {
            'infrastructure_related': any(word in column_lower for word in [
                'host', 'server', 'machine', 'computer', 'node', 'device', 'system', 'instance'
            ]),
            'security_related': any(word in column_lower for word in [
                'security', 'auth', 'permission', 'access', 'role', 'edr', 'antivirus', 'firewall', 'dlp'
            ]),
            'network_related': any(word in column_lower for word in [
                'network', 'ip', 'port', 'dns', 'url', 'domain', 'subnet', 'vlan'
            ]),
            'business_related': any(word in column_lower for word in [
                'business', 'department', 'unit', 'organization', 'company', 'revenue', 'cost', 'budget'
            ]),
            'temporal_related': any(word in column_lower for word in [
                'time', 'date', 'timestamp', 'created', 'modified', 'updated', 'deleted'
            ]),
            'location_related': any(word in column_lower for word in [
                'region', 'location', 'datacenter', 'site', 'facility', 'zone', 'area'
            ]),
            'identity_related': any(word in column_lower for word in [
                'user', 'account', 'person', 'employee', 'customer', 'client', 'contact'
            ])
        }
        
        # Analyze values for semantic content
        value_semantics = {
            'contains_technical_terms': sum(1 for v in values[:20] if any(
                tech_term in v.lower() for tech_term in [
                    'server', 'database', 'application', 'service', 'api', 'web', 'mobile'
                ]
            )),
            'contains_location_indicators': sum(1 for v in values[:20] if any(
                location in v.lower() for location in [
                    'east', 'west', 'north', 'south', 'central', 'us', 'eu', 'asia', 'america'
                ]
            )),
            'contains_environment_indicators': sum(1 for v in values[:20] if any(
                env in v.lower() for env in [
                    'prod', 'production', 'dev', 'development', 'test', 'staging', 'qa'
                ]
            ))
        }
        
        return {
            'column_semantic_indicators': semantic_indicators,
            'value_semantic_analysis': value_semantics,
            'semantic_confidence': sum(semantic_indicators.values()) / len(semantic_indicators)
        }
    
    def _create_statistical_profile(self, values: List[str]) -> Dict[str, Any]:
        if not values:
            return {}
        
        # Try to extract numeric values
        numeric_values = []
        for v in values:
            try:
                # Handle various numeric formats
                clean_val = re.sub(r'[^\d.-]', '', v)
                if clean_val:
                    numeric_values.append(float(clean_val))
            except:
                continue
        
        profile = {
            'total_values': len(values),
            'unique_values': len(set(values)),
            'uniqueness_ratio': len(set(values)) / len(values),
            'average_length': statistics.mean(len(v) for v in values),
            'length_variance': statistics.variance([len(v) for v in values]) if len(values) > 1 else 0
        }
        
        if numeric_values and len(numeric_values) > 1:
            profile.update({
                'numeric_values_count': len(numeric_values),
                'numeric_percentage': len(numeric_values) / len(values) * 100,
                'min_numeric': min(numeric_values),
                'max_numeric': max(numeric_values),
                'mean_numeric': statistics.mean(numeric_values),
                'median_numeric': statistics.median(numeric_values),
                'stdev_numeric': statistics.stdev(numeric_values),
                'numeric_range': max(numeric_values) - min(numeric_values)
            })
        
        return profile
    
    def _assess_data_quality(self, values: List[str]) -> Dict[str, Any]:
        if not values:
            return {'quality_score': 0}
        
        quality_indicators = {
            'completeness': (len([v for v in values if v and v.strip()]) / len(values)) * 100,
            'consistency': 0,  # Will be calculated
            'validity': 0,     # Will be calculated
            'uniqueness': (len(set(values)) / len(values)) * 100
        }
        
        # Consistency check (similar formats)
        if values:
            length_consistency = 1 - (statistics.stdev([len(v) for v in values]) / statistics.mean([len(v) for v in values])) if len(values) > 1 else 1
            quality_indicators['consistency'] = max(0, length_consistency * 100)
        
        # Validity check (no obvious bad data)
        valid_values = len([v for v in values if v and not v.lower() in ['null', 'none', 'n/a', 'unknown', 'error']])
        quality_indicators['validity'] = (valid_values / len(values)) * 100
        
        # Overall quality score
        quality_score = (
            quality_indicators['completeness'] * 0.3 +
            quality_indicators['consistency'] * 0.2 +
            quality_indicators['validity'] * 0.3 +
            quality_indicators['uniqueness'] * 0.2
        )
        
        quality_indicators['quality_score'] = quality_score
        
        return quality_indicators
    
    def _extract_corporate_terms(self, column_name: str, values: List[str]) -> Dict[str, Any]:
        # Extract corporate-specific terminology
        corporate_terms = {
            'technical_terms': set(),
            'business_terms': set(),
            'product_names': set(),
            'system_names': set()
        }
        
        # Analyze column name
        column_words = re.findall(r'[a-zA-Z]+', column_name.lower())
        for word in column_words:
            if len(word) > 2:
                if any(tech in word for tech in ['server', 'database', 'network', 'system']):
                    corporate_terms['technical_terms'].add(word)
                elif any(biz in word for biz in ['business', 'department', 'organization']):
                    corporate_terms['business_terms'].add(word)
        
        # Analyze values
        for value in values[:20]:  # Sample first 20 values
            if value and isinstance(value, str):
                words = re.findall(r'[a-zA-Z]+', value.lower())
                for word in words:
                    if len(word) > 3:
                        # Identify potential corporate terms
                        if word.endswith('corp') or word.endswith('inc') or word.endswith('ltd'):
                            corporate_terms['business_terms'].add(word)
                        elif word in ['aws', 'azure', 'gcp', 'oracle', 'cisco', 'microsoft']:
                            corporate_terms['technical_terms'].add(word)
        
        return {k: list(v) for k, v in corporate_terms.items()}
    
    def _identify_potential_relationships(self, column_name: str, values: List[str], table_path: str) -> List[Dict[str, Any]]:
        relationships = []
        
        # Foreign key patterns
        if column_name.lower().endswith('_id') or column_name.lower().startswith('id_'):
            relationships.append({
                'type': 'potential_foreign_key',
                'confidence': 0.8,
                'target_table_hint': column_name.replace('_id', '').replace('id_', '')
            })
        
        # Reference patterns
        if any(ref_word in column_name.lower() for ref_word in ['ref', 'reference', 'key', 'link']):
            relationships.append({
                'type': 'potential_reference',
                'confidence': 0.6,
                'description': f"Column {column_name} appears to reference other entities"
            })
        
        # Hierarchical patterns
        if any(hier_word in column_name.lower() for hier_word in ['parent', 'child', 'level', 'depth']):
            relationships.append({
                'type': 'hierarchical_relationship',
                'confidence': 0.7,
                'description': f"Column {column_name} suggests hierarchical data structure"
            })
        
        return relationships
    
    def _extract_lineage_hints(self, column_name: str, values: List[str], table_path: str) -> Dict[str, Any]:
        # Extract hints about data lineage and transformations
        lineage_hints = {
            'source_system_hints': [],
            'transformation_hints': [],
            'data_flow_hints': []
        }
        
        # Check for source system indicators in values
        for value in values[:10]:
            if value and isinstance(value, str):
                if any(source in value.lower() for source in ['etl', 'extract', 'load', 'transform']):
                    lineage_hints['transformation_hints'].append(f"ETL process indicator in {column_name}")
                
                if any(system in value.lower() for system in ['sap', 'oracle', 'salesforce', 'workday']):
                    lineage_hints['source_system_hints'].append(f"External system reference: {value}")
        
        # Check table path for pipeline indicators
        if any(pipeline_word in table_path.lower() for pipeline_word in ['staging', 'raw', 'processed', 'curated']):
            lineage_hints['data_flow_hints'].append(f"Pipeline stage indicator in table path")
        
        return lineage_hints
    
    def _extract_regex_patterns(self, values: List[str]) -> List[str]:
        # Extract common regex patterns from the data
        patterns = []
        
        if not values:
            return patterns
        
        # Sample a few values to generate patterns
        sample_values = values[:10]
        
        for value in sample_values:
            if not value:
                continue
            
            # Generate pattern for this value
            pattern = ""
            for char in value:
                if char.isdigit():
                    pattern += r'\d'
                elif char.isalpha():
                    if char.isupper():
                        pattern += r'[A-Z]'
                    else:
                        pattern += r'[a-z]'
                elif char in '.-_':
                    pattern += re.escape(char)
                else:
                    pattern += r'.'
            
            if pattern and pattern not in patterns:
                patterns.append(pattern)
        
        return patterns[:5]  # Return top 5 patterns
    
    def _detect_encoding_patterns(self, values: List[str]) -> List[str]:
        encoding_hints = []
        
        for value in values[:10]:
            if not value:
                continue
            
            # Check for base64
            try:
                if len(value) % 4 == 0 and re.match(r'^[A-Za-z0-9+/]*={0,2}$', value):
                    base64.b64decode(value)
                    encoding_hints.append('base64')
                    break
            except:
                pass
            
            # Check for hex encoding
            if all(c in '0123456789abcdefABCDEF' for c in value) and len(value) % 2 == 0:
                encoding_hints.append('hexadecimal')
                break
            
            # Check for URL encoding
            if '%' in value and re.search(r'%[0-9A-Fa-f]{2}', value):
                encoding_hints.append('url_encoded')
                break
        
        return list(set(encoding_hints))
    
    def _extract_table_intelligence(self, table_path: str, columns: List[str], sample_rows: List[Dict]) -> Dict[str, Any]:
        intelligence = {
            'table_purpose': self._infer_table_purpose(table_path, columns),
            'data_characteristics': self._analyze_data_characteristics(sample_rows),
            'business_context': self._extract_business_context(table_path, columns),
            'technical_context': self._extract_technical_context(table_path, columns),
            'update_patterns': self._analyze_update_patterns(columns, sample_rows),
            'relationship_indicators': self._find_relationship_indicators(columns)
        }
        
        return intelligence
    
    def _infer_table_purpose(self, table_path: str, columns: List[str]) -> Dict[str, Any]:
        table_name = table_path.split('.')[-1].lower()
        
        purpose_indicators = {
            'is_log_table': any(word in table_name for word in ['log', 'event', 'audit', 'history', 'trace']),
            'is_config_table': any(word in table_name for word in ['config', 'setting', 'parameter', 'option']),
            'is_user_table': any(word in table_name for word in ['user', 'account', 'person', 'employee', 'customer']),
            'is_asset_table': any(word in table_name for word in ['asset', 'device', 'machine', 'server', 'host']),
            'is_transaction_table': any(word in table_name for word in ['transaction', 'order', 'payment', 'invoice']),
            'is_reference_table': any(word in table_name for word in ['ref', 'lookup', 'code', 'type', 'category']),
            'is_metrics_table': any(word in table_name for word in ['metric', 'stat', 'count', 'measure', 'kpi']),
            'is_security_table': any(word in table_name for word in ['security', 'auth', 'permission', 'access', 'role'])
        }
        
        # Column-based inference
        column_indicators = {
            'has_timestamp_columns': any(word in col.lower() for col in columns for word in ['time', 'date', 'timestamp']),
            'has_id_columns': any(word in col.lower() for col in columns for word in ['id', 'key', 'uuid']),
            'has_status_columns': any(word in col.lower() for col in columns for word in ['status', 'state', 'flag']),
            'has_amount_columns': any(word in col.lower() for col in columns for word in ['amount', 'price', 'cost', 'value'])
        }
        
        return {
            'table_purpose_indicators': purpose_indicators,
            'column_purpose_indicators': column_indicators,
            'confidence_score': sum(purpose_indicators.values()) / len(purpose_indicators)
        }
    
    def _analyze_data_characteristics(self, sample_rows: List[Dict]) -> Dict[str, Any]:
        if not sample_rows:
            return {}
        
        characteristics = {
            'row_completeness': [],
            'data_density': 0,
            'value_diversity': {},
            'temporal_distribution': {}
        }
        
        # Analyze row completeness
        for row in sample_rows[:20]:
            non_null_fields = sum(1 for v in row.values() if v is not None)
            total_fields = len(row)
            completeness = non_null_fields / total_fields if total_fields > 0 else 0
            characteristics['row_completeness'].append(completeness)
        
        # Calculate data density
        if characteristics['row_completeness']:
            characteristics['data_density'] = statistics.mean(characteristics['row_completeness'])
        
        return characteristics
    
    def _extract_business_context(self, table_path: str, columns: List[str]) -> Dict[str, Any]:
        business_indicators = {
            'department_indicators': [],
            'function_indicators': [],
            'domain_indicators': []
        }
        
        # Check for business domain indicators
        business_domains = {
            'finance': ['finance', 'accounting', 'budget', 'revenue', 'cost', 'expense'],
            'hr': ['hr', 'human', 'employee', 'payroll', 'benefit', 'performance'],
            'sales': ['sales', 'customer', 'order', 'deal', 'opportunity', 'lead'],
            'marketing': ['marketing', 'campaign', 'lead', 'conversion', 'engagement'],
            'operations': ['operations', 'production', 'manufacturing', 'supply', 'logistics'],
            'it': ['it', 'infrastructure', 'system', 'server', 'network', 'security']
        }
        
        table_text = f"{table_path} {' '.join(columns)}".lower()
        
        for domain, keywords in business_domains.items():
            if any(keyword in table_text for keyword in keywords):
                business_indicators['domain_indicators'].append(domain)
        
        return business_indicators
    
    def _extract_technical_context(self, table_path: str, columns: List[str]) -> Dict[str, Any]:
        technical_indicators = {
            'technology_stack': [],
            'data_source_hints': [],
            'processing_hints': []
        }
        
        # Check for technology indicators
        technologies = ['aws', 'azure', 'gcp', 'kubernetes', 'docker', 'apache', 'nginx', 'mysql', 'postgres', 'oracle', 'mongodb']
        table_text = f"{table_path} {' '.join(columns)}".lower()
        
        for tech in technologies:
            if tech in table_text:
                technical_indicators['technology_stack'].append(tech)
        
        # Check for data source hints
        if any(word in table_text for word in ['raw', 'staging', 'processed', 'curated']):
            technical_indicators['processing_hints'].append('data_pipeline_table')
        
        if any(word in table_text for word in ['stream', 'kafka', 'kinesis', 'pubsub']):
            technical_indicators['data_source_hints'].append('streaming_data')
        
        return technical_indicators
    
    def _analyze_update_patterns(self, columns: List[str], sample_rows: List[Dict]) -> Dict[str, Any]:
        update_indicators = {
            'has_version_columns': any(word in col.lower() for col in columns for word in ['version', 'revision', 'sequence']),
            'has_audit_columns': any(word in col.lower() for col in columns for word in ['created', 'modified', 'updated', 'deleted']),
            'has_etl_columns': any(word in col.lower() for col in columns for word in ['etl', 'batch', 'load', 'extract']),
            'append_only_indicators': any(word in col.lower() for col in columns for word in ['id', 'sequence', 'timestamp'])
        }
        
        return update_indicators
    
    def _find_relationship_indicators(self, columns: List[str]) -> List[Dict[str, Any]]:
        relationships = []
        
        # Foreign key patterns
        fk_columns = [col for col in columns if col.lower().endswith('_id') or col.lower().startswith('id_')]
        for fk_col in fk_columns:
            relationships.append({
                'type': 'foreign_key_candidate',
                'column': fk_col,
                'target_hint': fk_col.replace('_id', '').replace('id_', '')
            })
        
        # Reference patterns
        ref_columns = [col for col in columns if any(word in col.lower() for word in ['ref', 'reference', 'link', 'pointer'])]
        for ref_col in ref_columns:
            relationships.append({
                'type': 'reference_column',
                'column': ref_col
            })
        
        return relationships
    
    async def _perform_deep_pattern_analysis(self):
        logger.info("🔍 Phase 3: Performing deep pattern analysis...")
        
        # Analyze patterns across all collected data
        pattern_analysis = {
            'global_column_patterns': self._analyze_global_column_patterns(),
            'cross_table_patterns': self._analyze_cross_table_patterns(),
            'naming_convention_analysis': self._analyze_naming_conventions(),
            'data_type_evolution': self._analyze_data_type_evolution(),
            'schema_similarity_analysis': self._analyze_schema_similarities()
        }
        
        self.ultimate_dataset['pattern_universe'] = pattern_analysis
        self.processing_stats['patterns_detected'] = len(pattern_analysis)
    
    def _analyze_global_column_patterns(self) -> Dict[str, Any]:
        # Analyze patterns across all columns in all tables
        all_column_data = {}
        
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            if 'comprehensive_analysis' in table_data:
                for column_name, column_analysis in table_data['comprehensive_analysis'].items():
                    if column_name not in all_column_data:
                        all_column_data[column_name] = {
                            'occurrences': 0,
                            'tables': [],
                            'all_patterns': Counter(),
                            'all_values': [],
                            'format_consistency': {}
                        }
                    
                    all_column_data[column_name]['occurrences'] += 1
                    all_column_data[column_name]['tables'].append(table_path)
                    
                    # Aggregate patterns
                    for pattern in column_analysis.get('detected_patterns', []):
                        all_column_data[column_name]['all_patterns'][pattern] += 1
                    
                    # Aggregate sample values
                    all_column_data[column_name]['all_values'].extend(
                        column_analysis.get('sample_values', [])[:5]
                    )
        
        return {
            'total_unique_columns': len(all_column_data),
            'most_common_columns': dict(Counter(
                {col: data['occurrences'] for col, data in all_column_data.items()}
            ).most_common(50)),
            'column_patterns': {
                col: {
                    'occurrences': data['occurrences'],
                    'common_patterns': dict(data['all_patterns'].most_common(5)),
                    'sample_values': data['all_values'][:20]
                }
                for col, data in all_column_data.items()
                if data['occurrences'] > 1  # Only include columns that appear in multiple tables
            }
        }
    
    def _analyze_cross_table_patterns(self) -> Dict[str, Any]:
        # Find patterns that span across multiple tables
        table_similarities = {}
        column_cooccurrence = defaultdict(Counter)
        
        # Build column co-occurrence matrix
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            columns = table_data.get('columns', [])
            
            # Track column co-occurrence
            for i, col1 in enumerate(columns):
                for col2 in columns[i+1:]:
                    column_cooccurrence[col1][col2] += 1
                    column_cooccurrence[col2][col1] += 1
        
        return {
            'column_cooccurrence': {
                col: dict(cooccur.most_common(10))
                for col, cooccur in column_cooccurrence.items()
                if len(cooccur) > 1
            },
            'common_column_combinations': self._find_common_column_combinations()
        }
    
    def _find_common_column_combinations(self) -> List[Dict[str, Any]]:
        # Find sets of columns that commonly appear together
        column_sets = []
        
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            columns = set(table_data.get('columns', []))
            if len(columns) > 1:
                column_sets.append(columns)
        
        # Find common combinations
        common_combinations = []
        
        # Check for common 2-column combinations
        two_column_combos = Counter()
        for column_set in column_sets:
            for col1 in column_set:
                for col2 in column_set:
                    if col1 != col2:
                        combo = tuple(sorted([col1, col2]))
                        two_column_combos[combo] += 1
        
        for combo, count in two_column_combos.most_common(20):
            if count > 2:  # Appears in at least 3 tables
                common_combinations.append({
                    'columns': list(combo),
                    'frequency': count,
                    'type': 'two_column_combination'
                })
        
        return common_combinations
    
    def _analyze_naming_conventions(self) -> Dict[str, Any]:
        # Analyze naming conventions across the entire environment
        naming_patterns = {
            'table_naming': {
                'snake_case': 0,
                'camel_case': 0,
                'all_lowercase': 0,
                'contains_underscores': 0,
                'contains_prefixes': Counter(),
                'contains_suffixes': Counter()
            },
            'column_naming': {
                'snake_case': 0,
                'camel_case': 0,
                'all_lowercase': 0,
                'all_uppercase': 0,
                'common_prefixes': Counter(),
                'common_suffixes': Counter()
            }
        }
        
        # Analyze table names
        for table_path in self.ultimate_dataset['raw_table_samples'].keys():
            table_name = table_path.split('.')[-1]
            
            if '_' in table_name and table_name.islower():
                naming_patterns['table_naming']['snake_case'] += 1
            if table_name.islower():
                naming_patterns['table_naming']['all_lowercase'] += 1
            if '_' in table_name:
                naming_patterns['table_naming']['contains_underscores'] += 1
            
            # Extract prefixes and suffixes
            if '_' in table_name:
                parts = table_name.split('_')
                if len(parts) > 1:
                    naming_patterns['table_naming']['contains_prefixes'][parts[0]] += 1
                    naming_patterns['table_naming']['contains_suffixes'][parts[-1]] += 1
        
        # Analyze column names
        all_columns = []
        for table_data in self.ultimate_dataset['raw_table_samples'].values():
            all_columns.extend(table_data.get('columns', []))
        
        for column_name in all_columns:
            if '_' in column_name and column_name.islower():
                naming_patterns['column_naming']['snake_case'] += 1
            if column_name.islower():
                naming_patterns['column_naming']['all_lowercase'] += 1
            if column_name.isupper():
                naming_patterns['column_naming']['all_uppercase'] += 1
            
            # Extract prefixes and suffixes
            if '_' in column_name:
                parts = column_name.split('_')
                if len(parts) > 1:
                    naming_patterns['column_naming']['common_prefixes'][parts[0]] += 1
                    naming_patterns['column_naming']['common_suffixes'][parts[-1]] += 1
        
        # Convert Counters to dicts for JSON serialization
        naming_patterns['table_naming']['contains_prefixes'] = dict(
            naming_patterns['table_naming']['contains_prefixes'].most_common(20)
        )
        naming_patterns['table_naming']['contains_suffixes'] = dict(
            naming_patterns['table_naming']['contains_suffixes'].most_common(20)
        )
        naming_patterns['column_naming']['common_prefixes'] = dict(
            naming_patterns['column_naming']['common_prefixes'].most_common(20)
        )
        naming_patterns['column_naming']['common_suffixes'] = dict(
            naming_patterns['column_naming']['common_suffixes'].most_common(20)
        )
        
        return naming_patterns
    
    def _analyze_data_type_evolution(self) -> Dict[str, Any]:
        # Analyze how data types are used across the environment
        data_type_usage = {}
        
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            if 'schema_detailed' in table_data:
                for field_info in table_data['schema_detailed']:
                    field_type = field_info['type']
                    field_name = field_info['name']
                    
                    if field_type not in data_type_usage:
                        data_type_usage[field_type] = {
                            'total_usage': 0,
                            'common_column_names': Counter(),
                            'tables_used_in': []
                        }
                    
                    data_type_usage[field_type]['total_usage'] += 1
                    data_type_usage[field_type]['common_column_names'][field_name] += 1
                    data_type_usage[field_type]['tables_used_in'].append(table_path)
        
        # Convert to serializable format
        for field_type, usage_data in data_type_usage.items():
            usage_data['common_column_names'] = dict(usage_data['common_column_names'].most_common(10))
            usage_data['unique_tables'] = len(set(usage_data['tables_used_in']))
            usage_data['tables_used_in'] = usage_data['tables_used_in'][:10]  # Limit for size
        
        return data_type_usage
    
    def _analyze_schema_similarities(self) -> List[Dict[str, Any]]:
        # Find tables with similar schemas
        schema_groups = []
        
        # Group tables by similar column sets
        column_signatures = {}
        
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            columns = table_data.get('columns', [])
            if len(columns) > 2:  # Only consider tables with multiple columns
                column_signature = tuple(sorted(columns))
                
                if column_signature not in column_signatures:
                    column_signatures[column_signature] = []
                
                column_signatures[column_signature].append(table_path)
        
        # Find groups with multiple tables
        for column_signature, tables in column_signatures.items():
            if len(tables) > 1:
                schema_groups.append({
                    'columns': list(column_signature),
                    'tables': tables,
                    'table_count': len(tables),
                    'similarity_type': 'exact_schema_match'
                })
        
        return schema_groups
    
    async def _mine_data_relationships(self):
        logger.info("🕸️ Phase 4: Mining data relationships...")
        
        relationship_analysis = {
            'potential_foreign_keys': self._identify_potential_foreign_keys(),
            'lookup_table_relationships': self._identify_lookup_relationships(),
            'hierarchical_relationships': self._identify_hierarchical_relationships(),
            'temporal_relationships': self._identify_temporal_relationships()
        }
        
        self.ultimate_dataset['relationship_graph'] = relationship_analysis
        self.processing_stats['relationships_identified'] = sum(
            len(relationships) for relationships in relationship_analysis.values()
        )
    
    def _identify_potential_foreign_keys(self) -> List[Dict[str, Any]]:
        # Identify potential foreign key relationships
        potential_fks = []
        
        # Find ID columns
        id_columns = {}
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            for column in table_data.get('columns', []):
                if column.lower().endswith('_id') or column.lower() == 'id':
                    if column not in id_columns:
                        id_columns[column] = []
                    id_columns[column].append(table_path)
        
        # Find potential relationships
        for column, tables in id_columns.items():
            if len(tables) > 1:
                potential_fks.append({
                    'column_name': column,
                    'tables': tables,
                    'relationship_type': 'potential_foreign_key',
                    'confidence': 0.7 if column.endswith('_id') else 0.5
                })
        
        return potential_fks
    
    def _identify_lookup_relationships(self) -> List[Dict[str, Any]]:
        # Identify potential lookup/reference table relationships
        lookup_relationships = []
        
        # Find small tables that might be lookup tables
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            row_count = table_data.get('table_metadata', {}).get('total_rows', 0)
            column_count = len(table_data.get('columns', []))
            
            # Heuristic: small tables with few columns might be lookup tables
            if row_count < 1000 and column_count <= 5:
                # Check if other tables have columns that might reference this
                table_name = table_path.split('.')[-1]
                
                referencing_tables = []
                
                # Look for columns in other tables that might reference this lookup table
                for other_table_path, other_table_data in self.ultimate_dataset['raw_table_samples'].items():
                    if other_table_path != table_path:
                        for column in other_table_data.get('columns', []):
                            if table_name.lower() in column.lower() or column.lower().endswith(f'_{table_name.lower()}'):
                                referencing_tables.append({
                                    'table': other_table_path,
                                    'column': column
                                })
                
                if referencing_tables:
                    lookup_relationships.append({
                        'lookup_table': table_path,
                        'lookup_table_rows': row_count,
                        'referencing_tables': referencing_tables,
                        'relationship_type': 'lookup_table',
                        'confidence': 0.6
                    })
        
        return lookup_relationships
    
    def _identify_hierarchical_relationships(self) -> List[Dict[str, Any]]:
        # Identify potential hierarchical relationships
        hierarchical_relationships = []
        
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            columns = table_data.get('columns', [])
            
            # Look for parent/child relationship indicators
            parent_columns = [col for col in columns if any(word in col.lower() for word in ['parent', 'parent_id'])]
            level_columns = [col for col in columns if any(word in col.lower() for word in ['level', 'depth', 'hierarchy'])]
            path_columns = [col for col in columns if any(word in col.lower() for word in ['path', 'lineage', 'ancestry'])]
            
            if parent_columns or level_columns or path_columns:
                hierarchical_relationships.append({
                    'table': table_path,
                    'parent_columns': parent_columns,
                    'level_columns': level_columns,
                    'path_columns': path_columns,
                    'relationship_type': 'hierarchical',
                    'confidence': 0.8 if parent_columns else 0.6
                })
        
        return hierarchical_relationships
    
    def _identify_temporal_relationships(self) -> List[Dict[str, Any]]:
        # Identify temporal relationships and time-based patterns
        temporal_relationships = []
        
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            columns = table_data.get('columns', [])
            
            # Find timestamp columns
            timestamp_columns = [col for col in columns if any(
                word in col.lower() for word in ['time', 'date', 'timestamp', 'created', 'modified', 'updated']
            )]
            
            if len(timestamp_columns) >= 2:
                temporal_relationships.append({
                    'table': table_path,
                    'timestamp_columns': timestamp_columns,
                    'relationship_type': 'temporal_tracking',
                    'pattern': 'audit_trail' if any(word in ' '.join(timestamp_columns).lower() for word in ['created', 'modified']) else 'temporal_data'
                })
        
        return temporal_relationships
    
    async def _extract_corporate_vocabulary(self):
        logger.info("📚 Phase 5: Extracting corporate vocabulary...")
        
        vocabulary = {
            'technical_terms': set(),
            'business_terms': set(),
            'product_names': set(),
            'location_indicators': set(),
            'department_names': set(),
            'system_names': set(),
            'environment_indicators': set(),
            'security_terms': set()
        }
        
        # Extract from table names, column names, and sample values
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            # Extract from table path
            path_parts = table_path.replace('.', ' ').replace('_', ' ').split()
            for part in path_parts:
                if len(part) > 2:
                    self._categorize_term(part.lower(), vocabulary)
            
            # Extract from column names
            for column in table_data.get('columns', []):
                column_parts = column.replace('_', ' ').split()
                for part in column_parts:
                    if len(part) > 2:
                        self._categorize_term(part.lower(), vocabulary)
            
            # Extract from sample values
            if 'comprehensive_analysis' in table_data:
                for column_name, analysis in table_data['comprehensive_analysis'].items():
                    sample_values = analysis.get('sample_values', [])[:10]
                    for value in sample_values:
                        if value and isinstance(value, str) and len(value) < 50:
                            value_parts = re.findall(r'[a-zA-Z]+', value.lower())
                            for part in value_parts:
                                if len(part) > 3:
                                    self._categorize_term(part, vocabulary)
        
        # Convert sets to lists and get top terms
        self.ultimate_dataset['corporate_vocabulary'] = {
            category: list(terms)[:100]  # Limit to top 100 per category
            for category, terms in vocabulary.items()
        }
    
    def _categorize_term(self, term: str, vocabulary: Dict[str, set]):
        # Categorize terms into different vocabularies
        
        # Technical terms
        if any(tech in term for tech in ['server', 'database', 'network', 'system', 'application', 'service', 'api', 'web', 'mobile', 'cloud', 'container', 'kubernetes', 'docker']):
            vocabulary['technical_terms'].add(term)
        
        # Business terms
        elif any(biz in term for biz in ['business', 'department', 'organization', 'company', 'revenue', 'cost', 'budget', 'finance', 'sales', 'marketing', 'customer']):
            vocabulary['business_terms'].add(term)
        
        # Product names (often capitalized or have specific patterns)
        elif any(prod in term for prod in ['product', 'solution', 'platform', 'suite', 'enterprise', 'professional', 'standard']):
            vocabulary['product_names'].add(term)
        
        # Location indicators
        elif any(loc in term for loc in ['east', 'west', 'north', 'south', 'central', 'region', 'zone', 'datacenter', 'facility', 'site']):
            vocabulary['location_indicators'].add(term)
        
        # Environment indicators
        elif term in ['prod', 'production', 'dev', 'development', 'test', 'testing', 'staging', 'qa', 'demo', 'sandbox']:
            vocabulary['environment_indicators'].add(term)
        
        # Security terms
        elif any(sec in term for sec in ['security', 'auth', 'permission', 'access', 'role', 'edr', 'antivirus', 'firewall', 'dlp', 'encryption']):
            vocabulary['security_terms'].add(term)
        
        # Department names
        elif term in ['finance', 'hr', 'it', 'operations', 'sales', 'marketing', 'legal', 'compliance', 'audit']:
            vocabulary['department_names'].add(term)
        
        # System names (often specific technologies)
        elif term in ['splunk', 'tableau', 'salesforce', 'workday', 'oracle', 'sap', 'microsoft', 'google', 'aws', 'azure']:
            vocabulary['system_names'].add(term)
    
    async def _perform_cross_table_intelligence(self):
        logger.info("🧠 Phase 6: Performing cross-table intelligence analysis...")
        
        cross_table_analysis = {
            'schema_evolution_patterns': self._analyze_schema_evolution(),
            'data_quality_patterns': self._analyze_data_quality_patterns(),
            'naming_consistency_analysis': self._analyze_naming_consistency(),
            'value_domain_analysis': self._analyze_value_domains(),
            'table_relationship_network': self._build_table_relationship_network()
        }
        
        self.ultimate_dataset['cross_table_analysis'] = cross_table_analysis
    
    def _analyze_schema_evolution(self) -> Dict[str, Any]:
        # Analyze how schemas evolve across similar tables
        evolution_patterns = {
            'common_column_additions': Counter(),
            'common_column_removals': Counter(),
            'schema_versioning_patterns': []
        }
        
        # Group tables by similarity
        similar_table_groups = {}
        
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            table_name = table_path.split('.')[-1]
            base_name = re.sub(r'(_v\d+|_\d{4}\d{2}\d{2}|_backup|_archive)', '', table_name)
            
            if base_name not in similar_table_groups:
                similar_table_groups[base_name] = []
            
            similar_table_groups[base_name].append({
                'path': table_path,
                'columns': set(table_data.get('columns', [])),
                'creation_date': table_data.get('table_metadata', {}).get('creation_date')
            })
        
        # Analyze evolution within groups
        for base_name, tables in similar_table_groups.items():
            if len(tables) > 1:
                # Sort by creation date if available
                tables_with_dates = [t for t in tables if t['creation_date']]
                if len(tables_with_dates) > 1:
                    sorted_tables = sorted(tables_with_dates, key=lambda x: x['creation_date'])
                    
                    for i in range(1, len(sorted_tables)):
                        prev_columns = sorted_tables[i-1]['columns']
                        curr_columns = sorted_tables[i]['columns']
                        
                        added = curr_columns - prev_columns
                        removed = prev_columns - curr_columns
                        
                        for col in added:
                            evolution_patterns['common_column_additions'][col] += 1
                        
                        for col in removed:
                            evolution_patterns['common_column_removals'][col] += 1
        
        return {
            'common_column_additions': dict(evolution_patterns['common_column_additions'].most_common(20)),
            'common_column_removals': dict(evolution_patterns['common_column_removals'].most_common(20)),
            'table_groups_analyzed': len([g for g in similar_table_groups.values() if len(g) > 1])
        }
    
    def _analyze_data_quality_patterns(self) -> Dict[str, Any]:
        # Analyze data quality patterns across tables
        quality_patterns = {
            'high_quality_tables': [],
            'low_quality_tables': [],
            'common_quality_issues': Counter(),
            'quality_by_table_type': defaultdict(list)
        }
        
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            if 'comprehensive_analysis' not in table_data:
                continue
            
            # Calculate overall table quality score
            column_quality_scores = []
            quality_issues = []
            
            for column_name, analysis in table_data['comprehensive_analysis'].items():
                quality_indicators = analysis.get('quality_indicators', {})
                quality_score = quality_indicators.get('quality_score', 0)
                column_quality_scores.append(quality_score)
                
                # Identify quality issues
                if quality_indicators.get('null_percentage', 0) > 30:
                    quality_issues.append('high_null_percentage')
                
                if quality_indicators.get('uniqueness_percentage', 0) < 10 and 'id' not in column_name.lower():
                    quality_issues.append('low_uniqueness')
                
                if quality_indicators.get('completeness', 0) < 70:
                    quality_issues.append('low_completeness')
            
            if column_quality_scores:
                avg_quality = statistics.mean(column_quality_scores)
                
                table_quality_info = {
                    'table_path': table_path,
                    'average_quality_score': avg_quality,
                    'quality_issues': quality_issues
                }
                
                if avg_quality > 80:
                    quality_patterns['high_quality_tables'].append(table_quality_info)
                elif avg_quality < 50:
                    quality_patterns['low_quality_tables'].append(table_quality_info)
                
                # Count quality issues
                for issue in quality_issues:
                    quality_patterns['common_quality_issues'][issue] += 1
        
        return {
            'high_quality_tables': quality_patterns['high_quality_tables'][:20],
            'low_quality_tables': quality_patterns['low_quality_tables'][:20],
            'common_quality_issues': dict(quality_patterns['common_quality_issues'])
        }
    
    def _analyze_naming_consistency(self) -> Dict[str, Any]:
        # Analyze naming consistency across the environment
        consistency_analysis = {
            'consistent_column_names': {},
            'inconsistent_patterns': [],
            'naming_standards_compliance': {}
        }
        
        # Analyze column naming consistency
        column_variants = defaultdict(set)
        
        for table_data in self.ultimate_dataset['raw_table_samples'].values():
            for column in table_data.get('columns', []):
                # Normalize column name to find variants
                normalized = re.sub(r'[_\-\s]+', '', column.lower())
                column_variants[normalized].add(column)
        
        # Find consistent vs inconsistent naming
        for normalized_name, variants in column_variants.items():
            if len(variants) == 1:
                consistency_analysis['consistent_column_names'][normalized_name] = list(variants)[0]
            elif len(variants) > 1:
                consistency_analysis['inconsistent_patterns'].append({
                    'concept': normalized_name,
                    'variants': list(variants),
                    'variant_count': len(variants)
                })
        
        return consistency_analysis
    
    def _analyze_value_domains(self) -> Dict[str, Any]:
        # Analyze value domains across similar columns
        domain_analysis = {}
        
        # Group columns by name across all tables
        column_values = defaultdict(list)
        
        for table_data in self.ultimate_dataset['raw_table_samples'].values():
            if 'comprehensive_analysis' in table_data:
                for column_name, analysis in table_data['comprehensive_analysis'].items():
                    sample_values = analysis.get('sample_values', [])
                    column_values[column_name].extend(sample_values[:10])
        
        # Analyze domains for columns that appear in multiple tables
        for column_name, all_values in column_values.items():
            if len(all_values) > 5:  # Only analyze if we have enough data
                unique_values = list(set(all_values))
                
                domain_analysis[column_name] = {
                    'total_values_collected': len(all_values),
                    'unique_values_count': len(unique_values),
                    'sample_domain': unique_values[:50],
                    'domain_size_estimate': len(unique_values),
                    'is_constrained_domain': len(unique_values) < len(all_values) * 0.5,
                    'common_values': dict(Counter(all_values).most_common(10))
                }
        
        return domain_analysis
    
    def _build_table_relationship_network(self) -> Dict[str, Any]:
        # Build a network representation of table relationships
        network = {
            'nodes': [],
            'edges': [],
            'clusters': []
        }
        
        # Create nodes for each table
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            node = {
                'id': table_path,
                'label': table_path.split('.')[-1],
                'project': table_path.split('.')[0],
                'dataset': table_path.split('.')[1],
                'column_count': len(table_data.get('columns', [])),
                'row_count': table_data.get('table_metadata', {}).get('total_rows', 0),
                'table_type': self._classify_table_type(table_path, table_data)
            }
            network['nodes'].append(node)
        
        # Create edges based on potential relationships
        relationships = self.ultimate_dataset.get('relationship_graph', {})
        
        # Add foreign key relationships as edges
        for fk_relationship in relationships.get('potential_foreign_keys', []):
            tables = fk_relationship.get('tables', [])
            if len(tables) > 1:
                for i, table1 in enumerate(tables):
                    for table2 in tables[i+1:]:
                        network['edges'].append({
                            'source': table1,
                            'target': table2,
                            'type': 'potential_foreign_key',
                            'column': fk_relationship.get('column_name'),
                            'confidence': fk_relationship.get('confidence', 0.5)
                        })
        
        # Add lookup table relationships as edges
        for lookup_relationship in relationships.get('lookup_table_relationships', []):
            lookup_table = lookup_relationship.get('lookup_table')
            for ref_info in lookup_relationship.get('referencing_tables', []):
                network['edges'].append({
                    'source': ref_info['table'],
                    'target': lookup_table,
                    'type': 'lookup_reference',
                    'column': ref_info['column'],
                    'confidence': lookup_relationship.get('confidence', 0.6)
                })
        
        return network
    
    def _classify_table_type(self, table_path: str, table_data: Dict[str, Any]) -> str:
        # Classify table type based on patterns
        table_name = table_path.split('.')[-1].lower()
        columns = table_data.get('columns', [])
        
        if any(word in table_name for word in ['log', 'event', 'audit', 'history']):
            return 'log_table'
        elif any(word in table_name for word in ['config', 'setting', 'parameter']):
            return 'configuration_table'
        elif any(word in table_name for word in ['ref', 'lookup', 'code', 'type']):
            return 'reference_table'
        elif any(word in table_name for word in ['fact', 'measure', 'metric']):
            return 'fact_table'
        elif any(word in table_name for word in ['dim', 'dimension']):
            return 'dimension_table'
        elif len(columns) <= 5 and table_data.get('table_metadata', {}).get('total_rows', 0) < 1000:
            return 'lookup_table'
        else:
            return 'data_table'
    
    async def _create_statistical_universe(self):
        logger.info("📊 Phase 7: Creating statistical universe...")
        
        statistical_analysis = {
            'global_statistics': self._calculate_global_statistics(),
            'distribution_analysis': self._analyze_distributions(),
            'correlation_analysis': self._analyze_correlations(),
            'trend_analysis': self._analyze_trends()
        }
        
        self.ultimate_dataset['statistical_universe'] = statistical_analysis
    
    def _calculate_global_statistics(self) -> Dict[str, Any]:
        # Calculate comprehensive global statistics
        stats = {
            'total_projects': len(self.ultimate_dataset['project_catalog']),
            'total_datasets': sum(
                len(project['datasets']) 
                for project in self.ultimate_dataset['project_catalog'].values()
            ),
            'total_tables': len(self.ultimate_dataset['raw_table_samples']),
            'total_columns': sum(
                len(table_data.get('columns', []))
                for table_data in self.ultimate_dataset['raw_table_samples'].values()
            ),
            'total_sample_rows': sum(
                len(table_data.get('sample_rows', []))
                for table_data in self.ultimate_dataset['raw_table_samples'].values()
            ),
            'average_columns_per_table': 0,
            'average_rows_per_table': 0,
            'data_size_distribution': {},
            'schema_complexity_distribution': {}
        }
        
        # Calculate averages
        if stats['total_tables'] > 0:
            stats['average_columns_per_table'] = stats['total_columns'] / stats['total_tables']
        
        # Analyze data size distribution
        table_sizes = []
        schema_complexities = []
        
        for table_data in self.ultimate_dataset['raw_table_samples'].values():
            row_count = table_data.get('table_metadata', {}).get('total_rows', 0)
            column_count = len(table_data.get('columns', []))
            
            table_sizes.append(row_count)
            schema_complexities.append(column_count)
        
        if table_sizes:
            stats['average_rows_per_table'] = statistics.mean(table_sizes)
            stats['data_size_distribution'] = {
                'min_rows': min(table_sizes),
                'max_rows': max(table_sizes),
                'median_rows': statistics.median(table_sizes),
                'large_tables_count': sum(1 for size in table_sizes if size > 1000000),
                'medium_tables_count': sum(1 for size in table_sizes if 1000 <= size <= 1000000),
                'small_tables_count': sum(1 for size in table_sizes if size < 1000)
            }
        
        if schema_complexities:
            stats['schema_complexity_distribution'] = {
                'min_columns': min(schema_complexities),
                'max_columns': max(schema_complexities),
                'median_columns': statistics.median(schema_complexities),
                'simple_schemas_count': sum(1 for complexity in schema_complexities if complexity <= 5),
                'medium_schemas_count': sum(1 for complexity in schema_complexities if 5 < complexity <= 20),
                'complex_schemas_count': sum(1 for complexity in schema_complexities if complexity > 20)
            }
        
        return stats
    
    def _analyze_distributions(self) -> Dict[str, Any]:
        # Analyze various distributions across the dataset
        distributions = {
            'project_distribution': {},
            'dataset_distribution': {},
            'table_type_distribution': Counter(),
            'column_type_distribution': Counter(),
            'data_pattern_distribution': Counter()
        }
        
        # Project distribution
        for project_id, project_data in self.ultimate_dataset['project_catalog'].items():
            distributions['project_distribution'][project_id] = {
                'datasets': project_data['total_datasets'],
                'tables': project_data['total_tables'],
                'estimated_rows': project_data['total_estimated_rows']
            }
        
        # Table type distribution
        for table_path, table_data in self.ultimate_dataset['raw_table_samples'].items():
            table_type = self._classify_table_type(table_path, table_data)
            distributions['table_type_distribution'][table_type] += 1
        
        # Convert Counters to dicts
        distributions['table_type_distribution'] = dict(distributions['table_type_distribution'])
        distributions['column_type_distribution'] = dict(distributions['column_type_distribution'])
        distributions['data_pattern_distribution'] = dict(distributions['data_pattern_distribution'])
        
        return distributions
    
    def _analyze_correlations(self) -> Dict[str, Any]:
        # Analyze correlations between different aspects of the data
        correlations = {
            'table_size_vs_schema_complexity': self._calculate_size_complexity_correlation(),
            'naming_convention_consistency': self._calculate_naming_consistency_correlation(),
            'data_quality_correlations': self._calculate_quality_correlations()
        }
        
        return correlations
    
    def _calculate_size_complexity_correlation(self) -> Dict[str, Any]:
        # Calculate correlation between table size and schema complexity
        sizes = []
        complexities = []
        
        for table_data in self.ultimate_dataset['raw_table_samples'].values():
            row_count = table_data.get('table_metadata', {}).get('total_rows', 0)
            column_count = len(table_data.get('columns', []))
            
            if row_count > 0:  # Only include tables with data
                sizes.append(row_count)
                complexities.append(column_count)
        
        correlation = {'correlation': 0, 'sample_size': len(sizes)}
        
        if len(sizes) > 1:
            try:
                correlation_coeff = np.corrcoef(sizes, complexities)[0, 1]
                correlation['correlation'] = float(correlation_coeff) if not np.isnan(correlation_coeff) else 0
            except:
                correlation['correlation'] = 0
        
        return correlation
    
    def _calculate_naming_consistency_correlation(self) -> Dict[str, Any]:
        # Calculate correlation between naming consistency and data quality
        return {'analysis': 'naming_consistency_analysis', 'status': 'placeholder'}
    
    def _calculate_quality_correlations(self) -> Dict[str, Any]:
        # Calculate correlations between different quality metrics
        return {'analysis': 'quality_correlations', 'status': 'placeholder'}
    
    def _analyze_trends(self) -> Dict[str, Any]:
        # Analyze trends in the data
        trends = {
            'temporal_patterns': self._analyze_temporal_patterns(),
            'growth_patterns': self._analyze_growth_patterns(),
            'usage_patterns': self._analyze_usage_patterns()
        }
        
        return trends
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        # Analyze temporal patterns in table creation and modification
        temporal_patterns = {
            'creation_timeline': [],
            'modification_timeline': [],
            'seasonal_patterns': {}
        }
        
        # Collect temporal data
        creation_dates = []
        modification_dates = []
        
        for project_data in self.ultimate_dataset['project_catalog'].values():
            for dataset_data in project_data['datasets'].values():
                for table_data in dataset_data['tables'].values():
                    if table_data['created']:
                        creation_dates.append(table_data['created'])
                    if table_data['modified']:
                        modification_dates.append(table_data['modified'])
        
        temporal_patterns['creation_timeline'] = sorted(creation_dates)[:100]  # Limit for size
        temporal_patterns['modification_timeline'] = sorted(modification_dates)[:100]  # Limit for size
        
        return temporal_patterns
    
    def _analyze_growth_patterns(self) -> Dict[str, Any]:
        # Analyze growth patterns in data volume and complexity
        return {'analysis': 'growth_patterns', 'status': 'placeholder'}
    
    def _analyze_usage_patterns(self) -> Dict[str, Any]:
        # Analyze usage patterns based on table characteristics
        return {'analysis': 'usage_patterns', 'status': 'placeholder'}
    
    async def _assemble_final_dataset(self) -> Dict[str, Any]:
        logger.info("🔧 Phase 8: Assembling final ultimate dataset...")
        
        # Calculate final processing statistics
        end_time = time.time()
        self.processing_stats['total_processing_time'] = end_time - self.processing_stats['start_time']
        self.processing_stats['processing_rate'] = (
            self.processing_stats['tables_discovered'] / 
            max(self.processing_stats['total_processing_time'], 1)
        )
        
        # Add final metadata
        self.ultimate_dataset['generation_metadata'].update({
            'completion_timestamp': datetime.now().isoformat(),
            'processing_statistics': self.processing_stats,
            'dataset_quality_score': self._calculate_dataset_quality_score(),
            'ai_readiness_score': self._calculate_ai_readiness_score()
        })
        
        return self.ultimate_dataset
    
    def _calculate_dataset_quality_score(self) -> float:
        # Calculate overall dataset quality score
        quality_factors = {
            'completeness': min(100, (self.processing_stats['tables_discovered'] / 
                                   max(self.processing_stats['tables_discovered'] + self.processing_stats['tables_failed'], 1)) * 100),
            'coverage': min(100, len(self.ultimate_dataset['raw_table_samples']) / 
                         max(self.processing_stats['tables_discovered'], 1) * 100),
            'depth': min(100, self.processing_stats['rows_sampled'] / 
                       max(len(self.ultimate_dataset['raw_table_samples']), 1)),
            'diversity': min(100, len(self.ultimate_dataset.get('corporate_vocabulary', {}).get('technical_terms', [])))
        }
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _calculate_ai_readiness_score(self) -> float:
        # Calculate how ready this dataset is for AI training
        ai_factors = {
            'pattern_richness': min(100, len(self.ultimate_dataset.get('pattern_universe', {}))),
            'relationship_depth': min(100, self.processing_stats['relationships_identified']),
            'vocabulary_richness': min(100, sum(
                len(vocab) for vocab in self.ultimate_dataset.get('corporate_vocabulary', {}).values()
            ) / 10),
            'statistical_completeness': 100 if 'statistical_universe' in self.ultimate_dataset else 0
        }
        
        return sum(ai_factors.values()) / len(ai_factors)
    
    async def _export_ultimate_dataset(self, dataset: Dict[str, Any]):
        logger.info("💾 Phase 9: Exporting ultimate dataset in multiple formats...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Complete JSON export
        main_file = f"ultimate_ai_training_dataset_{timestamp}.json"
        with open(main_file, 'w') as f:
            json.dump(dataset, f, indent=2, default=str)
        
        # 2. Compressed pickle export
        compressed_file = f"ultimate_ai_training_dataset_{timestamp}.pkl.gz"
        with gzip.open(compressed_file, 'wb') as f:
            pickle.dump(dataset, f)
        
        # 3. Executive summary
        summary_file = f"ultimate_dataset_summary_{timestamp}.json"
        summary = {
            'generation_metadata': dataset['generation_metadata'],
            'key_statistics': {
                'total_projects': len(dataset['project_catalog']),
                'total_tables_sampled': len(dataset['raw_table_samples']),
                'total_patterns_detected': len(dataset.get('pattern_universe', {})),
                'total_relationships_found': self.processing_stats['relationships_identified'],
                'corporate_vocabulary_size': sum(
                    len(vocab) for vocab in dataset.get('corporate_vocabulary', {}).values()
                )
            },
            'ai_training_readiness': {
                'dataset_quality_score': dataset['generation_metadata']['dataset_quality_score'],
                'ai_readiness_score': dataset['generation_metadata']['ai_readiness_score']
            }
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # 4. Sample data for quick analysis
        sample_file = f"ultimate_dataset_samples_{timestamp}.json"
        sample_data = {}
        
        # Include 10 sample tables with their complete analysis
        sample_tables = list(dataset['raw_table_samples'].items())[:10]
        for table_path, table_data in sample_tables:
            sample_data[table_path] = table_data
        
        with open(sample_file, 'w') as f:
            json.dump(sample_data, f, indent=2, default=str)
        
        logger.info(f"🎉 Ultimate dataset exported successfully!")
        logger.info(f"📁 Main file: {main_file} ({os.path.getsize(main_file) / 1024 / 1024:.1f} MB)")
        logger.info(f"📁 Compressed: {compressed_file} ({os.path.getsize(compressed_file) / 1024 / 1024:.1f} MB)")
        logger.info(f"📁 Summary: {summary_file}")
        logger.info(f"📁 Samples: {sample_file}")
        
        # Final statistics
        print("\n" + "="*80)
        print("🎯 ULTIMATE AI TRAINING DATASET GENERATION COMPLETE!")
        print("="*80)
        print(f"📊 Processing Statistics:")
        print(f"   • Projects analyzed: {self.processing_stats['projects_discovered']}")
        print(f"   • Datasets discovered: {self.processing_stats['datasets_discovered']}")
        print(f"   • Tables sampled: {len(dataset['raw_table_samples'])}")
        print(f"   • Columns analyzed: {self.processing_stats['columns_discovered']}")
        print(f"   • Sample rows collected: {self.processing_stats['rows_sampled']:,}")
        print(f"   • Patterns detected: {len(dataset.get('pattern_universe', {}))}")
        print(f"   • Relationships identified: {self.processing_stats['relationships_identified']}")
        print(f"   • Processing time: {self.processing_stats['total_processing_time']:.1f} seconds")
        print(f"\n🎯 Dataset Quality: {dataset['generation_metadata']['dataset_quality_score']:.1f}%")
        print(f"🤖 AI Readiness: {dataset['generation_metadata']['ai_readiness_score']:.1f}%")
        print("\n💡 This dataset contains EVERYTHING needed for AI to understand your corporate data!")
        print("="*80)

async def main():
    import yaml
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Enhanced configuration for ultimate dataset generation
    config.update({
        'samples_per_table': 50,
        'include_large_tables': True,
        'deep_analysis_mode': True,
        'max_tables_per_project': 999999
    })
    
    project_ids = config['project_ids']
    
    generator = UltimateDatasetGenerator(project_ids, config)
    ultimate_dataset = await generator.generate_ultimate_dataset()
    
    return ultimate_dataset

if __name__ == "__main__":
    asyncio.run(main())