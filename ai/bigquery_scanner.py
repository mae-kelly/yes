# ai/bigquery_scanner.py

import asyncio
import aiohttp
import json
import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path
import sqlite3
from collections import defaultdict, Counter
import numpy as np
import requests
import urllib3
import ssl
import socket
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class BigQueryPublicDatasetScanner:
    def __init__(self, cache_dir: str = ".bq_training_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.db_path = self.cache_dir / "training_patterns.db"
        self._init_training_db()
        
        self.proxy = "http://proxy-na.fiserv.one:8080"
        self._setup_ssl_and_proxy()
        
        self.public_datasets = [
            "bigquery-public-data.austin_311.311_service_requests",
            "bigquery-public-data.chicago_crime.crime",
            "bigquery-public-data.github_repos.commits",
            "bigquery-public-data.hacker_news.stories",
            "bigquery-public-data.new_york_citibike.citibike_trips",
            "bigquery-public-data.stackoverflow.posts_questions",
            "bigquery-public-data.samples.gsod",
            "bigquery-public-data.samples.natality",
            "bigquery-public-data.thelook_ecommerce.users",
            "bigquery-public-data.usa_names.usa_1910_current",
            "bigquery-public-data.cloud_storage_geo_index.landsat_index",
            "bigquery-public-data.crypto_bitcoin.blocks",
            "bigquery-public-data.ethereum_blockchain.blocks",
            "bigquery-public-data.fda_food.food_enforcement",
            "bigquery-public-data.medicare.inpatient_charges_2014",
            "bigquery-public-data.noaa_gsod.gsod2020",
            "bigquery-public-data.san_francisco.bikeshare_trips",
            "bigquery-public-data.london_bicycles.cycle_hire",
            "bigquery-public-data.census_bureau_usa.population_by_zip_2010",
            "bigquery-public-data.covid19_public_forecasts.county_14d",
            "bigquery-public-data.deps_dev_v1.Dependencies",
            "bigquery-public-data.epa_historical_air_quality.pm25_daily_summary",
            "bigquery-public-data.fec.committee_disbursements_2020",
            "bigquery-public-data.geo_census_tracts.census_tracts_new_york",
            "bigquery-public-data.google_trends.top_terms",
            "bigquery-public-data.irs_990.irs_990_2019",
            "bigquery-public-data.ml_datasets.penguins",
            "bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2020",
            "bigquery-public-data.open_targets_platform.molecule",
            "bigquery-public-data.patent_landscapes.publications",
            "bigquery-public-data.world_bank_health_population.health_nutrition_population"
        ]
        
        self.schema_cache = {}
        self.pattern_stats = defaultdict(Counter)
        
    def _setup_ssl_and_proxy(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        
        import os
        os.environ['HTTP_PROXY'] = self.proxy
        os.environ['HTTPS_PROXY'] = self.proxy
        os.environ['http_proxy'] = self.proxy
        os.environ['https_proxy'] = self.proxy
        
    def _init_training_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS schema_patterns (
                id INTEGER PRIMARY KEY,
                project_id TEXT,
                dataset_id TEXT,
                table_id TEXT,
                column_name TEXT,
                column_type TEXT,
                data_samples TEXT,
                inferred_field_type TEXT,
                confidence_score REAL,
                context_columns TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pattern_frequencies (
                pattern_type TEXT,
                pattern_value TEXT,
                field_type TEXT,
                frequency INTEGER,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (pattern_type, pattern_value, field_type)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS column_contexts (
                table_signature TEXT,
                column_name TEXT,
                sibling_columns TEXT,
                inferred_type TEXT,
                confidence REAL,
                PRIMARY KEY (table_signature, column_name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def scan_all_public_datasets(self):
        logger.info(f"Starting scan of {len(self.public_datasets)} public datasets")
        
        total_patterns = 0
        
        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            timeout=aiohttp.ClientTimeout(total=300)
        )
        
        try:
            for dataset_path in self.public_datasets:
                try:
                    patterns = await self._scan_single_dataset_aggressive(session, dataset_path)
                    total_patterns += len(patterns)
                    
                    if patterns:
                        await self._store_patterns(patterns)
                        logger.info(f"Scanned {dataset_path}: {len(patterns)} patterns")
                    
                except Exception as e:
                    logger.warning(f"Failed to scan {dataset_path}: {e}")
        finally:
            await session.close()
        
        logger.info(f"Total patterns collected: {total_patterns}")
        await self._analyze_pattern_distributions()
        
        return total_patterns
    
    async def _scan_single_dataset_aggressive(self, session: aiohttp.ClientSession, dataset_path: str) -> List[Dict[str, Any]]:
        parts = dataset_path.split('.')
        if len(parts) != 3:
            return []
        
        project_id, dataset_id, table_id = parts
        
        schema_info = await self._get_table_schema_info_aggressive(session, project_id, dataset_id, table_id)
        if not schema_info:
            return []
        
        data_samples = await self._get_table_sample_data_aggressive(session, project_id, dataset_id, table_id)
        
        patterns = []
        column_names = [col['name'] for col in schema_info.get('fields', [])]
        
        for column_info in schema_info.get('fields', []):
            column_name = column_info['name']
            column_type = column_info['type']
            
            samples = data_samples.get(column_name, [])
            
            inferred_type, confidence = self._infer_field_type(
                column_name, samples, column_names, dataset_path
            )
            
            pattern = {
                'project_id': project_id,
                'dataset_id': dataset_id,
                'table_id': table_id,
                'column_name': column_name,
                'column_type': column_type,
                'data_samples': json.dumps(samples[:50]),
                'inferred_field_type': inferred_type,
                'confidence_score': confidence,
                'context_columns': json.dumps(column_names),
                'table_path': dataset_path
            }
            
            patterns.append(pattern)
        
        return patterns
    
    async def _get_table_schema_info_aggressive(self, session: aiohttp.ClientSession, project_id: str, dataset_id: str, table_id: str) -> Optional[Dict]:
        urls = [
            f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}",
            f"https://content-bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}",
            f"https://www.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"
        ]
        
        for url in urls:
            try:
                proxy_configs = [
                    {'http': self.proxy, 'https': self.proxy},
                    None
                ]
                
                for proxy_config in proxy_configs:
                    connector = aiohttp.TCPConnector(ssl=False)
                    if proxy_config:
                        connector = aiohttp.TCPConnector(ssl=False)
                    
                    async with aiohttp.ClientSession(connector=connector) as temp_session:
                        if proxy_config:
                            temp_session._connector._proxy_url = self.proxy
                        
                        async with temp_session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data.get('schema')
            except Exception as e:
                logger.debug(f"Schema fetch failed for {project_id}.{dataset_id}.{table_id}: {e}")
                continue
        
        return None
    
    async def _get_table_sample_data_aggressive(self, session: aiohttp.ClientSession, project_id: str, dataset_id: str, table_id: str) -> Dict[str, List]:
        samples = {}
        
        query_urls = [
            f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/queries",
            f"https://content-bigquery.googleapis.com/bigquery/v2/projects/{project_id}/queries",
            f"https://www.googleapis.com/bigquery/v2/projects/{project_id}/queries"
        ]
        
        query = f"""
        SELECT *
        FROM `{project_id}.{dataset_id}.{table_id}`
        WHERE RAND() < 0.01
        LIMIT 100
        """
        
        query_data = {'query': query, 'useLegacySql': False}
        
        for query_url in query_urls:
            try:
                proxy_configs = [
                    {'http': self.proxy, 'https': self.proxy},
                    None
                ]
                
                for proxy_config in proxy_configs:
                    connector = aiohttp.TCPConnector(ssl=False)
                    if proxy_config:
                        connector = aiohttp.TCPConnector(ssl=False)
                    
                    async with aiohttp.ClientSession(connector=connector) as temp_session:
                        if proxy_config:
                            temp_session._connector._proxy_url = self.proxy
                        
                        async with temp_session.post(query_url, json=query_data, timeout=aiohttp.ClientTimeout(total=120)) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if 'rows' in data:
                                    schema_fields = data.get('schema', {}).get('fields', [])
                                    field_names = [f['name'] for f in schema_fields]
                                    
                                    for row in data['rows']:
                                        row_values = row.get('f', [])
                                        for i, value_obj in enumerate(row_values):
                                            if i < len(field_names):
                                                field_name = field_names[i]
                                                value = value_obj.get('v')
                                                
                                                if value is not None:
                                                    if field_name not in samples:
                                                        samples[field_name] = []
                                                    samples[field_name].append(str(value))
                                
                                return samples
            except Exception as e:
                logger.debug(f"Sample data fetch failed: {e}")
                continue
        
        return samples
    
    def _infer_field_type(self, column_name: str, samples: List[str], 
                         context_columns: List[str], table_path: str) -> Tuple[str, float]:
        
        name_lower = column_name.lower()
        
        hostname_indicators = ['host', 'hostname', 'computer', 'machine', 'device', 'endpoint', 'asset', 'server']
        ip_indicators = ['ip', 'address', 'addr', 'ipv4', 'ipv6']
        mac_indicators = ['mac', 'ethernet', 'physical']
        id_indicators = ['id', 'key', 'uuid', 'guid']
        
        confidence = 0.5
        field_type = 'unknown'
        
        if any(indicator in name_lower for indicator in hostname_indicators):
            if self._validate_hostname_samples(samples):
                field_type = 'hostname'
                confidence = 0.9
        
        elif any(indicator in name_lower for indicator in ip_indicators):
            if self._validate_ip_samples(samples):
                field_type = 'ip_address'
                confidence = 0.9
        
        elif any(indicator in name_lower for indicator in mac_indicators):
            if self._validate_mac_samples(samples):
                field_type = 'mac_address'
                confidence = 0.9
        
        elif any(indicator in name_lower for indicator in id_indicators):
            field_type = 'identifier'
            confidence = 0.7
        
        elif 'email' in name_lower:
            if self._validate_email_samples(samples):
                field_type = 'email_address'
                confidence = 0.9
        
        elif any(word in name_lower for word in ['region', 'location', 'zone']):
            field_type = 'location'
            confidence = 0.7
        
        elif any(word in name_lower for word in ['type', 'class', 'category']):
            field_type = 'classification'
            confidence = 0.6
        
        elif any(word in name_lower for word in ['name', 'title', 'description']):
            field_type = 'text_content'
            confidence = 0.6
        
        elif any(word in name_lower for word in ['count', 'number', 'quantity', 'amount']):
            field_type = 'numeric'
            confidence = 0.7
        
        elif any(word in name_lower for word in ['date', 'time', 'timestamp', 'created', 'updated']):
            field_type = 'temporal'
            confidence = 0.8
        
        confidence = self._adjust_confidence_by_context(field_type, context_columns, confidence)
        confidence = self._adjust_confidence_by_samples(field_type, samples, confidence)
        
        return field_type, confidence
    
    def _validate_hostname_samples(self, samples: List[str]) -> bool:
        if not samples:
            return False
        
        hostname_patterns = [
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$',
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,253}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        ]
        
        valid_count = 0
        for sample in samples[:20]:
            if any(re.match(pattern, str(sample)) for pattern in hostname_patterns):
                valid_count += 1
        
        return (valid_count / min(len(samples), 20)) > 0.7
    
    def _validate_ip_samples(self, samples: List[str]) -> bool:
        if not samples:
            return False
        
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        
        valid_count = 0
        for sample in samples[:20]:
            if re.match(ip_pattern, str(sample)):
                valid_count += 1
        
        return (valid_count / min(len(samples), 20)) > 0.8
    
    def _validate_mac_samples(self, samples: List[str]) -> bool:
        if not samples:
            return False
        
        mac_patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$',
            r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$'
        ]
        
        valid_count = 0
        for sample in samples[:20]:
            if any(re.match(pattern, str(sample)) for pattern in mac_patterns):
                valid_count += 1
        
        return (valid_count / min(len(samples), 20)) > 0.8
    
    def _validate_email_samples(self, samples: List[str]) -> bool:
        if not samples:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        valid_count = 0
        for sample in samples[:20]:
            if re.match(email_pattern, str(sample)):
                valid_count += 1
        
        return (valid_count / min(len(samples), 20)) > 0.8
    
    def _adjust_confidence_by_context(self, field_type: str, context_columns: List[str], base_confidence: float) -> float:
        context_lower = [col.lower() for col in context_columns]
        
        if field_type == 'hostname':
            if any('ip' in col or 'address' in col for col in context_lower):
                base_confidence += 0.1
            if any('mac' in col for col in context_lower):
                base_confidence += 0.1
        
        elif field_type == 'ip_address':
            if any('host' in col or 'machine' in col for col in context_lower):
                base_confidence += 0.1
            if any('subnet' in col or 'network' in col for col in context_lower):
                base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _adjust_confidence_by_samples(self, field_type: str, samples: List[str], base_confidence: float) -> float:
        if not samples:
            return base_confidence * 0.5
        
        if field_type == 'hostname':
            avg_length = np.mean([len(str(s)) for s in samples])
            if 5 <= avg_length <= 50:
                base_confidence += 0.05
        
        elif field_type == 'ip_address':
            if all(str(s).count('.') == 3 for s in samples[:10]):
                base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    async def _store_patterns(self, patterns: List[Dict[str, Any]]):
        conn = sqlite3.connect(self.db_path)
        
        for pattern in patterns:
            conn.execute('''
                INSERT OR REPLACE INTO schema_patterns 
                (project_id, dataset_id, table_id, column_name, column_type, 
                 data_samples, inferred_field_type, confidence_score, context_columns)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern['project_id'], pattern['dataset_id'], pattern['table_id'],
                pattern['column_name'], pattern['column_type'], pattern['data_samples'],
                pattern['inferred_field_type'], pattern['confidence_score'], pattern['context_columns']
            ))
        
        conn.commit()
        conn.close()
    
    async def _analyze_pattern_distributions(self):
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute('''
            SELECT inferred_field_type, COUNT(*) as frequency
            FROM schema_patterns
            GROUP BY inferred_field_type
            ORDER BY frequency DESC
        ''')
        
        distributions = cursor.fetchall()
        
        logger.info("Field type distributions:")
        for field_type, frequency in distributions:
            logger.info(f"  {field_type}: {frequency}")
        
        cursor = conn.execute('''
            SELECT column_name, inferred_field_type, COUNT(*) as frequency
            FROM schema_patterns
            WHERE confidence_score > 0.8
            GROUP BY column_name, inferred_field_type
            HAVING frequency > 1
            ORDER BY frequency DESC
            LIMIT 20
        ''')
        
        common_patterns = cursor.fetchall()
        
        logger.info("Most common high-confidence patterns:")
        for column_name, field_type, frequency in common_patterns:
            logger.info(f"  {column_name} -> {field_type}: {frequency}")
        
        conn.close()
    
    def get_training_data(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute('''
            SELECT * FROM schema_patterns
            WHERE confidence_score > 0.6
            ORDER BY confidence_score DESC
        ''')
        
        training_data = []
        for row in cursor.fetchall():
            training_data.append({
                'column_name': row[4],
                'column_type': row[5],
                'data_samples': json.loads(row[6]) if row[6] else [],
                'field_type': row[7],
                'confidence': row[8],
                'context_columns': json.loads(row[9]) if row[9] else []
            })
        
        conn.close()
        return training_data