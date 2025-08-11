#!/usr/bin/env python3

import os
import logging
import time
import threading
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

class BigQueryClientManager:
    def __init__(self, project_id: str):
        if not BIGQUERY_AVAILABLE:
            raise ImportError("google-cloud-bigquery is required")
            
        self.project_id = project_id
        self._client = None
        self._client_lock = threading.Lock()
        self._last_creation = 0
        self._min_creation_interval = 1.0
        
        logger.info(f"Initializing BigQuery client for project: {project_id}")
    
    def _create_client(self) -> bigquery.Client:
        current_time = time.time()
        
        if current_time - self._last_creation < self._min_creation_interval:
            time.sleep(self._min_creation_interval - (current_time - self._last_creation))
        
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
                            job_timeout_ms=600000,
                            maximum_bytes_billed=None,
                            use_legacy_sql=False,
                            dry_run=False
                        )
                    )
                    list(client.list_datasets(max_results=1))
                    self._last_creation = time.time()
                    return client
                except Exception as e:
                    logger.debug(f"Service account {path} failed: {e}")
                    continue
        
        try:
            client = bigquery.Client(
                project=self.project_id,
                default_query_job_config=bigquery.QueryJobConfig(
                    use_query_cache=False,
                    job_timeout_ms=600000,
                    maximum_bytes_billed=None,
                    use_legacy_sql=False,
                    dry_run=False
                )
            )
            list(client.list_datasets(max_results=1))
            self._last_creation = time.time()
            return client
        except Exception as e:
            logger.error(f"All authentication methods failed: {e}")
            raise
    
    @contextmanager
    def get_client(self):
        with self._client_lock:
            if self._client is None:
                self._client = self._create_client()
            
            try:
                yield self._client
            except Exception as e:
                error_str = str(e).lower()
                if any(term in error_str for term in ["connection pool", "httperror", "timeout", "maximum_bytes_billed"]):
                    logger.warning(f"BigQuery error, recreating client: {e}")
                    time.sleep(random.uniform(1, 3))
                    self._client = self._create_client()
                    yield self._client
                else:
                    raise
    
    def create_unlimited_client(self) -> bigquery.Client:
        """Create a client with no cost limits for critical queries"""
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
    
    def execute_query_unlimited(self, query: str):
        """Execute query with no cost limits"""
        client = self.create_unlimited_client()
        
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