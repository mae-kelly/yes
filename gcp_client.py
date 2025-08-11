#!/usr/bin/env python3

import os
import logging
import time
import threading
from contextlib import contextmanager
from typing import Optional

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
        self._client_lock = threading.Lock()
        self._last_client_creation = 0
        self._client_creation_delay = 1.0
        
        try:
            self.client = self._create_client()
            logger.info(f"Connected to BigQuery project: {project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
    
    def _create_client(self) -> bigquery.Client:
        with self._client_lock:
            current_time = time.time()
            if current_time - self._last_client_creation < self._client_creation_delay:
                time.sleep(self._client_creation_delay - (current_time - self._last_client_creation))
            
            credential_paths = [
                os.path.join(os.path.dirname(__file__), "gcp_prod_key.json"),
                "gcp_prod_key.json",
                os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''),
                os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
            ]
            
            for path in credential_paths:
                if path and os.path.exists(path):
                    try:
                        logger.info(f"Attempting service account authentication: {path}")
                        credentials = service_account.Credentials.from_service_account_file(path)
                        client = bigquery.Client(
                            project=self.project_id, 
                            credentials=credentials,
                            default_query_job_config=bigquery.QueryJobConfig(
                                use_query_cache=True,
                                job_timeout_ms=300000
                            )
                        )
                        list(client.list_datasets(max_results=1))
                        logger.info(f"Successfully authenticated using service account: {path}")
                        self._last_client_creation = time.time()
                        return client
                    except Exception as e:
                        logger.debug(f"Service account {path} failed: {e}")
                        continue
            
            try:
                logger.info("Attempting default credentials authentication")
                client = bigquery.Client(
                    project=self.project_id,
                    default_query_job_config=bigquery.QueryJobConfig(
                        use_query_cache=True,
                        job_timeout_ms=300000
                    )
                )
                list(client.list_datasets(max_results=1))
                logger.info("Successfully authenticated using default credentials")
                self._last_client_creation = time.time()
                return client
            except Exception as e:
                logger.error(f"All authentication methods failed: {e}")
                raise
    
    @contextmanager
    def get_client(self):
        try:
            yield self.client
        except Exception as e:
            if "Connection pool is full" in str(e) or "ConnectionError" in str(e):
                logger.warning("Connection pool issue detected, creating new client")
                time.sleep(2)
                try:
                    self.client = self._create_client()
                    yield self.client
                except Exception as retry_e:
                    logger.error(f"Failed to create new client: {retry_e}")
                    raise
            else:
                logger.error(f"BigQuery operation failed: {e}")
                raise
    
    def test_connection(self) -> bool:
        try:
            with self.get_client() as client:
                datasets = list(client.list_datasets(max_results=1))
                logger.info("BigQuery connection test successful")
                return True
        except Exception as e:
            logger.error(f"BigQuery connection test failed: {e}")
            return False
    
    def get_project_info(self) -> dict:
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