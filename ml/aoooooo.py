#!/usr/bin/env python3
import os
import re
import asyncio
import logging
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from itertools import product, combinations
import json
import hashlib
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
except ImportError:
    print("Please install: pip install google-cloud-bigquery")
    bigquery = None

try:
    import redis
    import pickle
except ImportError:
    redis = None
    pickle = None

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import accuracy_score, r2_score
    import pandas as pd
except ImportError:
    print("ML features disabled - install: pip install scikit-learn pandas")
    RandomForestClassifier = None

try:
    from sentence_transformers import SentenceTransformer
    import torch
except ImportError:
    SentenceTransformer = None

@dataclass
class TableInfo:
    project_id: str
    dataset_id: str
    table_id: str
    row_count: int = 0
    size_bytes: int = 0
    last_modified: Optional[datetime] = None
    fields: List[Dict] = field(default_factory=list)
    quality_score: float = 0.0
    authority_score: float = 0.0
    ml_score: float = 0.0

@dataclass
class FieldAnalysis:
    field_name: str
    field_type: str
    table_info: TableInfo
    pattern_matches: Dict[str, float] = field(default_factory=dict)
    semantic_similarity: Dict[str, float] = field(default_factory=dict)
    data_samples: List[Any] = field(default_factory=list)
    completeness: float = 0.0
    uniqueness: float = 0.0
    ml_confidence: float = 0.0
    visibility_metrics: Dict[str, float] = field(default_factory=dict)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'
    
    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
            raise e

class SemanticAnalyzer:
    def __init__(self):
        self.model = None
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except:
                self.model = None
        
        self.visibility_patterns = {
            'host_parity': [
                r'.*host.*name.*', r'.*computer.*', r'.*device.*name.*', r'.*machine.*',
                r'.*endpoint.*', r'.*asset.*id.*', r'.*system.*name.*', r'.*node.*'
            ],
            'network_coverage': [
                r'.*ip.*addr.*', r'.*source.*ip.*', r'.*dest.*ip.*', r'.*client.*ip.*',
                r'.*server.*ip.*', r'.*remote.*addr.*', r'.*inet.*addr.*', r'.*network.*'
            ],
            'public_ip_coverage': [
                r'.*public.*ip.*', r'.*external.*ip.*', r'.*wan.*ip.*', r'.*internet.*',
                r'.*routable.*', r'.*global.*ip.*'
            ],
            'domain_coverage': [
                r'.*domain.*', r'.*fqdn.*', r'.*dns.*name.*', r'.*host.*header.*',
                r'.*server.*name.*', r'.*url.*host.*'
            ],
            'user_coverage': [
                r'.*user.*name.*', r'.*user.*id.*', r'.*account.*', r'.*principal.*',
                r'.*identity.*', r'.*subject.*', r'.*actor.*'
            ],
            'geolocation_coverage': [
                r'.*geo.*', r'.*location.*', r'.*country.*', r'.*city.*', r'.*region.*',
                r'.*latitude.*', r'.*longitude.*', r'.*coordinates.*'
            ],
            'process_coverage': [
                r'.*process.*name.*', r'.*proc.*name.*', r'.*command.*', r'.*executable.*',
                r'.*binary.*', r'.*pid.*', r'.*process.*id.*'
            ],
            'file_coverage': [
                r'.*file.*name.*', r'.*file.*path.*', r'.*document.*', r'.*attachment.*',
                r'.*path.*', r'.*filename.*', r'.*filepath.*'
            ]
        }
    
    def analyze_field_patterns(self, field_name: str, field_type: str, samples: List[Any]) -> Dict[str, float]:
        patterns = {}
        field_lower = field_name.lower()
        
        for metric, regex_patterns in self.visibility_patterns.items():
            max_score = 0.0
            for pattern in regex_patterns:
                if re.match(pattern, field_lower):
                    max_score = max(max_score, 0.9)
            patterns[metric] = max_score
        
        if samples:
            if field_type in ['STRING', 'VARCHAR']:
                sample_str = str(samples[0]) if samples else ""
                
                if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', sample_str):
                    patterns['network_coverage'] = max(patterns.get('network_coverage', 0), 0.95)
                    if self._is_public_ip(sample_str):
                        patterns['public_ip_coverage'] = max(patterns.get('public_ip_coverage', 0), 0.95)
                
                if re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', sample_str):
                    patterns['domain_coverage'] = max(patterns.get('domain_coverage', 0), 0.95)
                
                if re.match(r'^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', sample_str):
                    patterns['user_coverage'] = max(patterns.get('user_coverage', 0), 0.8)
        
        return patterns
    
    def _is_public_ip(self, ip: str) -> bool:
        try:
            parts = [int(x) for x in ip.split('.')]
            if parts[0] == 10:
                return False
            if parts[0] == 172 and 16 <= parts[1] <= 31:
                return False
            if parts[0] == 192 and parts[1] == 168:
                return False
            if parts[0] == 127:
                return False
            return True
        except:
            return False
    
    def compute_semantic_similarity(self, field_name: str, target_concepts: List[str]) -> Dict[str, float]:
        similarities = {}
        field_lower = field_name.lower()
        
        if self.model:
            try:
                field_embedding = self.model.encode([field_lower])
                concept_embeddings = self.model.encode(target_concepts)
                
                from sklearn.metrics.pairwise import cosine_similarity
                scores = cosine_similarity(field_embedding, concept_embeddings)[0]
                
                for concept, score in zip(target_concepts, scores):
                    similarities[concept] = float(score)
            except:
                pass
        
        for concept in target_concepts:
            if concept not in similarities:
                similarities[concept] = self._fuzzy_match(field_lower, concept.lower())
        
        return similarities
    
    def _fuzzy_match(self, s1: str, s2: str) -> float:
        if s2 in s1 or s1 in s2:
            return 0.9
        
        def levenshtein_distance(a, b):
            if len(a) < len(b):
                return levenshtein_distance(b, a)
            if len(b) == 0:
                return len(a)
            
            previous_row = list(range(len(b) + 1))
            for i, c1 in enumerate(a):
                current_row = [i + 1]
                for j, c2 in enumerate(b):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        distance = levenshtein_distance(s1, s2)
        return 1.0 - (distance / max_len)

class AO1FieldDiscovery:
    def __init__(self, config):
        self.config = config
        self.client = self._init_bigquery_client()
        self.cache = self._init_cache()
        self.semantic_analyzer = SemanticAnalyzer()
        self.circuit_breaker = CircuitBreaker()
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _init_bigquery_client(self):
        if not bigquery:
            raise ImportError("BigQuery client not available - install google-cloud-bigquery")
        
        try:
            if hasattr(self.config, 'credentials_path') and self.config.credentials_path:
                if os.path.exists(self.config.credentials_path):
                    credentials = service_account.Credentials.from_service_account_file(
                        self.config.credentials_path
                    )
                    return bigquery.Client(project=self.config.project_id, credentials=credentials)
                else:
                    self.logger.warning(f"Service account file not found: {self.config.credentials_path}")
            
            return bigquery.Client(project=self.config.project_id)
        except Exception as e:
            self.logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
    
    def _init_cache(self):
        if not hasattr(self.config, 'enable_caching') or not self.config.enable_caching or not redis:
            return None
        
        try:
            cache_config = {
                'host': getattr(self.config, 'redis_host', 'localhost'),
                'port': getattr(self.config, 'redis_port', 6379),
                'db': getattr(self.config, 'redis_db', 0),
                'decode_responses': False
            }
            
            if hasattr(self.config, 'redis_password') and self.config.redis_password:
                cache_config['password'] = self.config.redis_password
                
            return redis.Redis(**cache_config)
        except Exception as e:
            self.logger.warning(f"Failed to initialize Redis cache: {e}")
            return None
    
    def _cache_get(self, key: str) -> Optional[Any]:
        if not self.cache or not pickle:
            return None
        
        try:
            cached = self.cache.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
        
        return None
    
    def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None):
        if not self.cache or not pickle:
            return
        
        try:
            ttl = ttl or getattr(self.config, 'cache_ttl', 3600)
            serialized = pickle.dumps(value)
            self.cache.setex(key, ttl, serialized)
        except Exception as e:
            self.logger.warning(f"Cache set error: {e}")
    
    async def discover_tables(self, datasets: Optional[List[str]] = None) -> List[TableInfo]:
        if datasets is None:
            datasets = await self._get_all_datasets()
        
        max_datasets = getattr(self.config, 'max_datasets', 50)
        datasets = datasets[:max_datasets]
        
        all_tables = []
        max_workers = getattr(self.config, 'max_workers', 10)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = []
            for dataset_id in datasets:
                task = executor.submit(self._process_dataset, dataset_id)
                tasks.append(task)
            
            for future in as_completed(tasks):
                try:
                    tables = future.result()
                    all_tables.extend(tables)
                except Exception as e:
                    self.logger.error(f"Error processing dataset: {e}")
        
        ranked_tables = self._rank_tables(all_tables)
        return ranked_tables
    
    async def _get_all_datasets(self) -> List[str]:
        cache_key = f"datasets:{self.config.project_id}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached
        
        try:
            datasets = list(self.client.list_datasets(self.config.project_id))
            dataset_ids = [d.dataset_id for d in datasets]
            
            if hasattr(self.config, 'allowed_datasets') and self.config.allowed_datasets:
                dataset_ids = [d for d in dataset_ids if d in self.config.allowed_datasets]
            
            if hasattr(self.config, 'blocked_datasets') and self.config.blocked_datasets:
                dataset_ids = [d for d in dataset_ids if d not in self.config.blocked_datasets]
            
            self._cache_set(cache_key, dataset_ids, 1800)
            return dataset_ids
        except Exception as e:
            self.logger.error(f"Error listing datasets: {e}")
            return []
    
    def _process_dataset(self, dataset_id: str) -> List[TableInfo]:
        cache_key = f"dataset_tables:{self.config.project_id}:{dataset_id}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached
        
        try:
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            
            max_tables = getattr(self.config, 'max_tables_per_dataset', 25)
            tables = tables[:max_tables]
            
            table_infos = []
            for table in tables:
                try:
                    full_table = self.circuit_breaker.call(self.client.get_table, table.reference)
                    
                    fields = []
                    max_fields = getattr(self.config, 'max_fields_per_table', 500)
                    for field in full_table.schema[:max_fields]:
                        fields.append({
                            'name': field.name,
                            'field_type': field.field_type,
                            'mode': field.mode,
                            'description': field.description
                        })
                    
                    table_info = TableInfo(
                        project_id=self.config.project_id,
                        dataset_id=dataset_id,
                        table_id=table.table_id,
                        row_count=full_table.num_rows or 0,
                        size_bytes=full_table.num_bytes or 0,
                        last_modified=full_table.modified,
                        fields=fields
                    )
                    
                    table_info.quality_score = self._calculate_table_quality(table_info)
                    table_info.authority_score = self._calculate_authority_score(table_info)
                    
                    table_infos.append(table_info)
                
                except Exception as e:
                    self.logger.warning(f"Error processing table {table.table_id}: {e}")
            
            self._cache_set(cache_key, table_infos, 900)
            return table_infos
        
        except Exception as e:
            self.logger.error(f"Error processing dataset {dataset_id}: {e}")
            return []
    
    def _calculate_table_quality(self, table: TableInfo) -> float:
        if not table.fields:
            return 0.0
        
        scores = []
        
        scores.append(min(1.0, table.row_count / 1000000))
        scores.append(min(1.0, len(table.fields) / 50))
        
        if table.last_modified:
            days_old = (datetime.now() - table.last_modified.replace(tzinfo=None)).days
            freshness = max(0.0, 1.0 - (days_old / 365))
            scores.append(freshness)
        
        documented_fields = sum(1 for f in table.fields if f.get('description'))
        documentation_score = documented_fields / len(table.fields)
        scores.append(documentation_score)
        
        naming_quality = self._assess_naming_quality(table)
        scores.append(naming_quality)
        
        return sum(scores) / len(scores)
    
    def _calculate_authority_score(self, table: TableInfo) -> float:
        score = 0.5
        
        table_name = table.table_id.lower()
        
        authority_indicators = ['log', 'event', 'audit', 'security', 'siem', 'raw', 'master', 'prod']
        for indicator in authority_indicators:
            if indicator in table_name:
                score += 0.1
        
        dataset_name = table.dataset_id.lower()
        if any(keyword in dataset_name for keyword in ['security', 'audit', 'log', 'prod']):
            score += 0.1
        
        if table.row_count > 1000000:
            score += 0.1
        
        if table.size_bytes > 1000000000:
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_naming_quality(self, table: TableInfo) -> float:
        if not table.fields:
            return 0.0
        
        consistent_naming = 0
        total_fields = len(table.fields)
        
        snake_case = sum(1 for f in table.fields if '_' in f['name'] and f['name'].islower())
        camel_case = sum(1 for f in table.fields if any(c.isupper() for c in f['name'][1:]) and '_' not in f['name'])
        
        if snake_case > camel_case:
            consistent_naming = snake_case
        else:
            consistent_naming = camel_case
        
        return consistent_naming / total_fields if total_fields > 0 else 0.0
    
    def _rank_tables(self, tables: List[TableInfo]) -> List[TableInfo]:
        for table in tables:
            combined_score = (
                table.quality_score * 0.4 +
                table.authority_score * 0.3 +
                min(1.0, table.row_count / 10000000) * 0.2 +
                min(1.0, len(table.fields) / 100) * 0.1
            )
            table.quality_score = combined_score
        
        return sorted(tables, key=lambda t: t.quality_score, reverse=True)
    
    async def analyze_fields_for_metrics(self, tables: List[TableInfo]) -> Dict[str, List[FieldAnalysis]]:
        results = {metric: [] for metric in self.semantic_analyzer.visibility_patterns.keys()}
        
        all_fields = []
        max_workers = getattr(self.config, 'max_workers', 10)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = []
            for table in tables:
                task = executor.submit(asyncio.run, self._analyze_table_fields(table))
                tasks.append(task)
            
            for future in as_completed(tasks):
                try:
                    table_fields = future.result()
                    all_fields.extend(table_fields)
                except Exception as e:
                    self.logger.error(f"Error analyzing table fields: {e}")
        
        confidence_threshold = getattr(self.config, 'confidence_threshold', 0.7)
        
        for field in all_fields:
            for metric, confidence in field.visibility_metrics.items():
                if confidence >= confidence_threshold:
                    results[metric].append(field)
        
        for metric in results:
            results[metric].sort(key=lambda f: f.ml_confidence, reverse=True)
        
        return results
    
    async def _analyze_table_fields(self, table: TableInfo) -> List[FieldAnalysis]:
        fields = []
        
        for field_info in table.fields:
            field_name = field_info['name']
            field_type = field_info['field_type']
            
            try:
                samples = await self._get_field_samples(table, field_name)
                
                completeness = await self._calculate_completeness(table, field_name)
                uniqueness = await self._calculate_uniqueness(table, field_name, samples)
                
                field_analysis = FieldAnalysis(
                    field_name=field_name,
                    field_type=field_type,
                    table_info=table,
                    data_samples=samples,
                    completeness=completeness,
                    uniqueness=uniqueness
                )
                
                pattern_matches = self.semantic_analyzer.analyze_field_patterns(
                    field_name, field_type, samples
                )
                field_analysis.pattern_matches = pattern_matches
                
                all_concepts = ['host', 'hostname', 'computer', 'device', 'ip', 'address', 'user', 'domain']
                semantic_similarity = self.semantic_analyzer.compute_semantic_similarity(
                    field_name, all_concepts
                )
                field_analysis.semantic_similarity = semantic_similarity
                
                field_analysis.visibility_metrics = pattern_matches
                
                max_confidence = max(field_analysis.visibility_metrics.values()) if field_analysis.visibility_metrics else 0.0
                field_analysis.ml_confidence = max_confidence
                
                fields.append(field_analysis)
            
            except Exception as e:
                self.logger.warning(f"Error analyzing field {field_name} in table {table.table_id}: {e}")
        
        return fields
    
    async def _get_field_samples(self, table: TableInfo, field_name: str) -> List[Any]:
        cache_key = f"samples:{table.project_id}:{table.dataset_id}:{table.table_id}:{field_name}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached
        
        if not hasattr(self.config, 'enable_data_sampling') or not self.config.enable_data_sampling:
            return []
        
        try:
            sample_size = getattr(self.config, 'sample_size', 100)
            query = f"""
            SELECT DISTINCT `{field_name}`
            FROM `{table.project_id}.{table.dataset_id}.{table.table_id}`
            WHERE `{field_name}` IS NOT NULL
            LIMIT {sample_size}
            """
            
            query_job = self.circuit_breaker.call(self.client.query, query)
            results = query_job.result()
            
            samples = [row[0] for row in results if row[0] is not None]
            self._cache_set(cache_key, samples, 1800)
            
            return samples
        
        except Exception as e:
            self.logger.warning(f"Error getting samples for {field_name}: {e}")
            return []
    
    async def _calculate_completeness(self, table: TableInfo, field_name: str) -> float:
        if table.row_count == 0:
            return 0.0
        
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(`{field_name}`) as non_null_rows
            FROM `{table.project_id}.{table.dataset_id}.{table.table_id}`
            """
            
            query_job = self.circuit_breaker.call(self.client.query, query)
            results = list(query_job.result())
            
            if results:
                row = results[0]
                total_rows = row.total_rows
                non_null_rows = row.non_null_rows
                
                if total_rows > 0:
                    return non_null_rows / total_rows
            
        except Exception as e:
            self.logger.warning(f"Error calculating completeness for {field_name}: {e}")
        
        return 0.0
    
    async def _calculate_uniqueness(self, table: TableInfo, field_name: str, samples: List[Any]) -> float:
        if not samples:
            return 0.0
        
        try:
            query = f"""
            SELECT COUNT(DISTINCT `{field_name}`) as unique_count
            FROM `{table.project_id}.{table.dataset_id}.{table.table_id}`
            WHERE `{field_name}` IS NOT NULL
            """
            
            query_job = self.circuit_breaker.call(self.client.query, query)
            results = list(query_job.result())
            
            if results and table.row_count > 0:
                unique_count = results[0].unique_count
                return min(1.0, unique_count / table.row_count)
            
        except Exception as e:
            self.logger.warning(f"Error calculating uniqueness for {field_name}: {e}")
        
        return len(set(samples)) / len(samples) if samples else 0.0
    
    def generate_discovery_report(self, tables: List[TableInfo], field_results: Dict[str, List[FieldAnalysis]]) -> Dict[str, Any]:
        report = {
            "discovery_summary": {
                "total_tables_analyzed": len(tables),
                "total_fields_discovered": sum(len(fields) for fields in field_results.values()),
                "high_confidence_discoveries": sum(
                    len([f for f in fields if f.ml_confidence >= 0.8]) 
                    for fields in field_results.values()
                ),
                "analysis_timestamp": datetime.now().isoformat(),
                "ml_training_status": "pattern_based"
            },
            
            "visibility_metrics": {},
            
            "top_tables": [
                {
                    "table_id": f"{t.project_id}.{t.dataset_id}.{t.table_id}",
                    "quality_score": round(t.quality_score, 3),
                    "authority_score": round(t.authority_score, 3),
                    "row_count": t.row_count,
                    "field_count": len(t.fields),
                    "last_modified": t.last_modified.isoformat() if t.last_modified else None
                }
                for t in tables[:10]
            ],
            
            "implementation_roadmap": {
                "phase_1_immediate": {
                    "description": "High-confidence discoveries ready for immediate dashboard deployment",
                    "tables": []
                },
                "phase_2_validation": {
                    "description": "Medium-confidence discoveries requiring validation before deployment",
                    "tables": []
                },
                "phase_3_exploration": {
                    "description": "Lower-confidence discoveries worth investigating for potential value",
                    "tables": []
                }
            }
        }
        
        for metric, fields in field_results.items():
            if not fields:
                continue
                
            metric_data = {
                "total_candidates": len(fields),
                "high_confidence": len([f for f in fields if f.ml_confidence >= 0.8]),
                "medium_confidence": len([f for f in fields if 0.5 <= f.ml_confidence < 0.8]),
                "low_confidence": len([f for f in fields if f.ml_confidence < 0.5]),
                "top_fields": []
            }
            
            for field in fields[:5]:
                field_data = {
                    "table_id": f"{field.table_info.project_id}.{field.table_info.dataset_id}.{field.table_info.table_id}",
                    "field_name": field.field_name,
                    "field_type": field.field_type,
                    "confidence_score": round(field.ml_confidence, 3),
                    "completeness": round(field.completeness, 3),
                    "uniqueness": round(field.uniqueness, 3),
                    "data_samples": field.data_samples[:3] if field.data_samples else [],
                    "business_applications": self._get_business_applications(metric)
                }
                metric_data["top_fields"].append(field_data)
            
            report["visibility_metrics"][metric] = metric_data
        
        for metric, fields in field_results.items():
            high_conf_fields = [f for f in fields if f.ml_confidence >= 0.8]
            medium_conf_fields = [f for f in fields if 0.5 <= f.ml_confidence < 0.8]
            low_conf_fields = [f for f in fields if 0.3 <= f.ml_confidence < 0.5]
            
            if high_conf_fields:
                phase_1_tables = list(set([
                    f"{f.table_info.project_id}.{f.table_info.dataset_id}.{f.table_info.table_id}" 
                    for f in high_conf_fields
                ]))
                report["implementation_roadmap"]["phase_1_immediate"]["tables"].extend(phase_1_tables)
            
            if medium_conf_fields:
                phase_2_tables = list(set([
                    f"{f.table_info.project_id}.{f.table_info.dataset_id}.{f.table_info.table_id}" 
                    for f in medium_conf_fields
                ]))
                report["implementation_roadmap"]["phase_2_validation"]["tables"].extend(phase_2_tables)
            
            if low_conf_fields:
                phase_3_tables = list(set([
                    f"{f.table_info.project_id}.{f.table_info.dataset_id}.{f.table_info.table_id}" 
                    for f in low_conf_fields
                ]))
                report["implementation_roadmap"]["phase_3_exploration"]["tables"].extend(phase_3_tables)
        
        for phase in report["implementation_roadmap"].values():
            if isinstance(phase, dict) and "tables" in phase:
                phase["tables"] = list(set(phase["tables"]))[:10]
        
        return report
    
    def _get_business_applications(self, metric: str) -> List[str]:
        applications = {
            'host_parity': ["Asset Inventory Management", "Endpoint Coverage Analysis"],
            'network_coverage': ["Network Traffic Analysis", "IP Address Management"],
            'public_ip_coverage': ["External Attack Surface Monitoring", "Internet-facing Asset Discovery"],
            'domain_coverage': ["DNS Security Monitoring", "Domain Reputation Analysis"],
            'user_coverage': ["User Activity Monitoring", "Identity and Access Management"],
            'geolocation_coverage': ["Geographic Risk Analysis", "Location-based Access Control"],
            'process_coverage': ["Process Monitoring and Analysis", "Malware Detection"],
            'file_coverage': ["File Integrity Monitoring", "Data Loss Prevention"]
        }
        
        return applications.get(metric, ["General Security Monitoring"])