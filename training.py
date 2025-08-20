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
            'processing_warnings': 0,
            'tables_failed': 0  # Added this field
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
                
                for dataset_ref in datasets:
                    # Handle different types of dataset references
                    # dataset_ref might be a DatasetListItem or similar object
                    if hasattr(dataset_ref, 'dataset_id'):
                        dataset_id = dataset_ref.dataset_id
                    elif hasattr(dataset_ref, 'reference'):
                        dataset_id = dataset_ref.reference.dataset_id
                    else:
                        # Try to get dataset_id directly if it's a string or has string representation
                        dataset_id = str(dataset_ref).split('.')[-1] if '.' in str(dataset_ref) else str(dataset_ref)
                    
                    try:
                        # Create proper dataset reference for get_dataset
                        dataset_ref_str = f"{project_id}.{dataset_id}"
                        dataset_obj = client.get_dataset(dataset_ref_str)
                        
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
                        tables = list(client.list_tables(dataset_ref_str, max_results=10000))
                        
                        for table_ref in tables:
                            # Handle different types of table references
                            if hasattr(table_ref, 'table_id'):
                                table_id = table_ref.table_id
                            elif hasattr(table_ref, 'reference'):
                                table_id = table_ref.reference.table_id
                            else:
                                table_id = str(table_ref).split('.')[-1] if '.' in str(table_ref) else str(table_ref)
                            
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
                                    'schema_fields': len(table.schema) if table.schema else 0,
                                    'schema_summary': [
                                        {
                                            'name': field.name,
                                            'type': field.field_type,
                                            'mode': field.mode
                                        } for field in (table.schema or [])
                                    ],
                                    'partitioning': str(table.time_partitioning) if table.time_partitioning else None,
                                    'clustering': table.clustering_fields if table.clustering_fields else None
                                }
                                
                                dataset_info['tables'][table_id] = table_info
                                dataset_info['total_rows'] += table.num_rows or 0
                                dataset_info['total_bytes'] += table.num_bytes or 0
                                
                                all_tables_info.append(table_info)
                                self.processing_stats['tables_discovered'] += 1
                                self.processing_stats['columns_discovered'] += len(table.schema) if table.schema else 0
                                
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
                        else:
                            self.processing_stats['tables_failed'] += 1
                    except Exception as e:
                        logger.debug(f"Sampling failed for {table_path}: {e}")
                        self.processing_stats['processing_warnings'] += 1
                        self.processing_stats['tables_failed'] += 1
            
            # Progress update
            progress = min(100, ((i + batch_size) / len(all_tables)) * 100)
            logger.info(f"📈 Sampling progress: {progress:.1f}% ({i + batch_size}/{len(all_tables)} tables)")
    
    # ... rest of the methods remain the same ...
    # (I'll continue with just the essential parts that need fixing)

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

    # Include all the other methods from the original file that don't need changes
    # (All the analysis methods, pattern detection, etc. remain the same)
    # I'm including just the key ones that complete the class structure:

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

    # Continue with all other helper methods from the original file...
    # (These remain unchanged, so I'll include placeholders for brevity)
    
    def _detect_comprehensive_patterns(self, values: List[str]) -> List[str]:
        # Implementation from original file
        pass
    
    def _analyze_data_formats(self, values: List[str]) -> Dict[str, Any]:
        # Implementation from original file
        pass
    
    def _analyze_semantic_content(self, column_name: str, values: List[str]) -> Dict[str, Any]:
        # Implementation from original file
        pass
    
    def _create_statistical_profile(self, values: List[str]) -> Dict[str, Any]:
        # Implementation from original file
        pass
    
    def _assess_data_quality(self, values: List[str]) -> Dict[str, Any]:
        # Implementation from original file
        pass
    
    def _extract_corporate_terms(self, column_name: str, values: List[str]) -> Dict[str, Any]:
        # Implementation from original file
        pass
    
    def _identify_potential_relationships(self, column_name: str, values: List[str], table_path: str) -> List[Dict[str, Any]]:
        # Implementation from original file
        pass
    
    def _extract_lineage_hints(self, column_name: str, values: List[str], table_path: str) -> Dict[str, Any]:
        # Implementation from original file
        pass
    
    def _extract_table_intelligence(self, table_path: str, columns: List[str], sample_rows: List[Dict]) -> Dict[str, Any]:
        # Implementation from original file
        pass

    # Include all remaining phases and methods...
    async def _perform_deep_pattern_analysis(self):
        # Implementation from original file
        pass
    
    async def _mine_data_relationships(self):
        # Implementation from original file
        pass
    
    async def _extract_corporate_vocabulary(self):
        # Implementation from original file
        pass
    
    async def _perform_cross_table_intelligence(self):
        # Implementation from original file
        pass
    
    async def _create_statistical_universe(self):
        # Implementation from original file
        pass
    
    async def _assemble_final_dataset(self) -> Dict[str, Any]:
        # Implementation from original file
        pass
    
    async def _export_ultimate_dataset(self, dataset: Dict[str, Any]):
        # Implementation from original file
        pass

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