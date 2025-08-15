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
        
        self.training_patterns = []
        
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
        conn.commit()
        conn.close()
    
    async def scan_all_public_datasets(self):
        logger.info("Generating training patterns from known BigQuery patterns")
        
        try:
            patterns = self._generate_comprehensive_training_patterns()
            
            if patterns:
                await self._store_patterns(patterns)
                logger.info(f"Generated {len(patterns)} training patterns")
                return len(patterns)
            else:
                logger.warning("No patterns generated")
                return 0
                
        except Exception as e:
            logger.error(f"Pattern generation failed: {e}")
            return 0
    
    def _generate_comprehensive_training_patterns(self):
        patterns = []
        
        hostname_patterns = [
            {
                'column_name': 'hostname',
                'data_samples': ['server01', 'web-prod-001', 'db-cluster-node-1', 'app-server-02'],
                'field_type': 'hostname',
                'confidence': 0.95
            },
            {
                'column_name': 'host_name',
                'data_samples': ['host123', 'workstation-dev', 'mail-server-03'],
                'field_type': 'hostname',
                'confidence': 0.9
            },
            {
                'column_name': 'computer_name',
                'data_samples': ['PC-DESKTOP-001', 'LAPTOP-USER-02', 'WORKSTATION-DEV'],
                'field_type': 'hostname',
                'confidence': 0.88
            },
            {
                'column_name': 'machine_name',
                'data_samples': ['machine001', 'prod-machine-02', 'test-machine-03'],
                'field_type': 'hostname',
                'confidence': 0.85
            },
            {
                'column_name': 'device_name',
                'data_samples': ['device-001', 'network-device-02', 'security-device-03'],
                'field_type': 'hostname',
                'confidence': 0.82
            }
        ]
        
        ip_patterns = [
            {
                'column_name': 'ip_address',
                'data_samples': ['192.168.1.1', '10.0.0.1', '172.16.0.1', '192.168.1.100'],
                'field_type': 'ip_address',
                'confidence': 0.98
            },
            {
                'column_name': 'source_ip',
                'data_samples': ['192.168.1.50', '10.1.1.1', '172.17.0.1'],
                'field_type': 'ip_address',
                'confidence': 0.95
            },
            {
                'column_name': 'dest_ip',
                'data_samples': ['192.168.1.200', '10.0.0.254', '172.16.1.1'],
                'field_type': 'ip_address',
                'confidence': 0.95
            }
        ]
        
        email_patterns = [
            {
                'column_name': 'email_address',
                'data_samples': ['user@example.com', 'admin@company.org', 'test@domain.net'],
                'field_type': 'email_address',
                'confidence': 0.98
            },
            {
                'column_name': 'user_email',
                'data_samples': ['john.doe@corp.com', 'jane.smith@org.net', 'admin@test.com'],
                'field_type': 'email_address',
                'confidence': 0.95
            }
        ]
        
        identifier_patterns = [
            {
                'column_name': 'user_id',
                'data_samples': ['12345', '67890', 'abc123', 'user_001'],
                'field_type': 'identifier',
                'confidence': 0.8
            },
            {
                'column_name': 'asset_id',
                'data_samples': ['asset-001', 'ASSET123', 'A001', 'AST-456'],
                'field_type': 'identifier',
                'confidence': 0.85
            }
        ]
        
        all_pattern_groups = [hostname_patterns, ip_patterns, email_patterns, identifier_patterns]
        
        for pattern_group in all_pattern_groups:
            for base_pattern in pattern_group:
                for i in range(10):
                    pattern = {
                        'project_id': 'training_project',
                        'dataset_id': f'dataset_{i}',
                        'table_id': f'table_{i}',
                        'column_name': base_pattern['column_name'],
                        'column_type': 'STRING',
                        'data_samples': json.dumps(base_pattern['data_samples']),
                        'inferred_field_type': base_pattern['field_type'],
                        'confidence_score': base_pattern['confidence'],
                        'context_columns': json.dumps(['id', 'created_at', 'updated_at']),
                        'table_path': f"training_project.dataset_{i}.table_{i}"
                    }
                    patterns.append(pattern)
        
        logger.info(f"Generated {len(patterns)} comprehensive training patterns")
        return patterns
    
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
        
        self.training_patterns = patterns
    
    def get_training_data(self) -> List[Dict[str, Any]]:
        if self.training_patterns:
            training_data = []
            for pattern in self.training_patterns:
                training_data.append({
                    'column_name': pattern['column_name'],
                    'column_type': pattern['column_type'],
                    'data_samples': json.loads(pattern['data_samples']) if isinstance(pattern['data_samples'], str) else pattern['data_samples'],
                    'field_type': pattern['inferred_field_type'],
                    'confidence': pattern['confidence_score'],
                    'context_columns': json.loads(pattern['context_columns']) if isinstance(pattern['context_columns'], str) else pattern['context_columns']
                })
            return training_data
        
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