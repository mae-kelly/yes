#!/usr/bin/env python3

import os
import logging
import time
import threading
import queue
from contextlib import contextmanager
from typing import Optional, Dict
import random

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False

logger = logging.getLogger(__name__)

class BigQueryClientPool:
    def __init__(self, project_id: str, pool_size: int = 3):
        if not BIGQUERY_AVAILABLE:
            raise ImportError("google-cloud-bigquery is required")
            
        self.project_id = project_id
        self.pool_size = pool_size
        self._clients = []
        self._available = queue.Queue(maxsize=pool_size)
        self._pool_lock = threading.Lock()
        self._creation_lock = threading.Lock()
        self._last_creation = {}
        self._min_creation_interval = 3.0
        
        self._initialize_pool()
    
    def _create_single_client(self) -> bigquery.Client:
        thread_id = threading.get_ident()
        current_time = time.time()
        
        with self._creation_lock:
            last_time = self._last_creation.get(thread_id, 0)
            if current_time - last_time < self._min_creation_interval:
                time.sleep(self._min_creation_interval - (current_time - last_time))
            
            credential_paths = [
                os.path.join(os.path.dirname(__file__), "gcp_prod_key.json"),
                "gcp_prod_key.json",
                os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''),
                os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
            ]
            
            for path in credential_paths:
                if path and os.path.exists(path):
                    try:
                        credentials = service_account.Credentials.from_service_account_file(path)
                        client = bigquery.Client(
                            project=self.project_id, 
                            credentials=credentials,
                            default_query_job_config=bigquery.QueryJobConfig(
                                use_query_cache=False,
                                job_timeout_ms=300000,
                                maximum_bytes_billed=None,
                                use_legacy_sql=False
                            )
                        )
                        list(client.list_datasets(max_results=1))
                        self._last_creation[thread_id] = time.time()
                        return client
                    except Exception as e:
                        logger.debug(f"Service account {path} failed: {e}")
                        continue
            
            try:
                client = bigquery.Client(
                    project=self.project_id,
                    default_query_job_config=bigquery.QueryJobConfig(
                        use_query_cache=False,
                        job_timeout_ms=300000,
                        maximum_bytes_billed=None,
                        use_legacy_sql=False
                    )
                )
                list(client.list_datasets(max_results=1))
                self._last_creation[thread_id] = time.time()
                return client
            except Exception as e:
                logger.error(f"All authentication methods failed: {e}")
                raise
    
    def _create_unlimited_client(self) -> bigquery.Client:
        """Create a client with no cost limits for critical AO1 queries"""
        credential_paths = [
            os.path.join(os.path.dirname(__file__), "gcp_prod_key.json"),
            "gcp_prod_key.json",
            os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''),
            os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
        ]
        
        for path in credential_paths:
            if path and os.path.exists(path):
                try:
                    credentials = service_account.Credentials.from_service_account_file(path)
                    return bigquery.Client(
                        project=self.project_id, 
                        credentials=credentials,
                        default_query_job_config=None
                    )
                except Exception:
                    continue
        
        return bigquery.Client(
            project=self.project_id,
            default_query_job_config=None
        )
    
    def _initialize_pool(self):
        logger.info(f"Initializing BigQuery client pool with {self.pool_size} clients")
        for i in range(self.pool_size):
            try:
                client = self._create_single_client()
                self._clients.append(client)
                self._available.put(client, block=False)
                logger.debug(f"Created client {i+1}/{self.pool_size}")
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"Failed to create client {i+1}: {e}")
                if i == 0:
                    raise
    
    @contextmanager
    def get_client(self, timeout: float = 60.0):
        client = None
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                try:
                    client = self._available.get(timeout=5.0)
                    break
                except queue.Empty:
                    time.sleep(random.uniform(0.5, 2.0))
                    continue
            
            if client is None:
                logger.warning("All clients busy, creating temporary client")
                temp_client = self._create_single_client()
                yield temp_client
                return
            
            yield client
            
        except Exception as e:
            logger.error(f"Client error: {e}")
            if "Connection pool is full" in str(e) or "ConnectionError" in str(e) or "HttpError" in str(e):
                logger.warning("Connection error detected, creating fresh client")
                time.sleep(random.uniform(2, 5))
                fresh_client = self._create_single_client()
                yield fresh_client
            else:
                raise
        finally:
            if client is not None and client in self._clients:
                try:
                    self._available.put(client, block=False)
                except queue.Full:
                    pass
    
    def execute_query_unlimited(self, query: str):
        """Execute query with no cost limits for critical AO1 discovery"""
        client = self._create_unlimited_client()
        
        job_config = bigquery.QueryJobConfig(
            use_query_cache=False,
            job_timeout_ms=600000,
            maximum_bytes_billed=None,
            use_legacy_sql=False,
            dry_run=False
        )
        
        job = client.query(query, job_config=job_config)
        return job.result()
    
    def test_connection(self) -> bool:
        try:
            with self.get_client() as client:
                datasets = list(client.list_datasets(max_results=1))
                logger.info("BigQuery connection test successful")
                return True
        except Exception as e:
            logger.error(f"BigQuery connection test failed: {e}")
            return False

class BigQueryClientManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.pool = BigQueryClientPool(project_id, pool_size=2)
        logger.info(f"Connected to BigQuery project: {project_id}")
    
    @contextmanager
    def get_client(self):
        with self.pool.get_client() as client:
            yield client
    
    def execute_query_unlimited(self, query: str):
        """Execute query with no cost limits for critical AO1 queries"""
        return self.pool.execute_query_unlimited(query)
    
    def test_connection(self) -> bool:
        return self.pool.test_connection()
    
    def get_project_info(self) -> Dict[str, str]:
        try:
            with self.get_client() as client:
                return {
                    'project_id': client.project,
                    'friendly_name': f"BigQuery Project: {client.project}",
                    'description': f"Connected to BigQuery in project {client.project}"
                }
        except Exception as e:
            logger.error(f"Failed to get project info: {e}")
            return {
                'project_id': self.project_id,
                'friendly_name': f"Project: {self.project_id}",
                'description': "Project info unavailable"
            }