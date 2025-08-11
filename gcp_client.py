#!/usr/bin/env python3

import os
import logging
import time
import threading
import queue
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
        self._client_pool = queue.Queue(maxsize=5)
        self._pool_lock = threading.Lock()
        self._client_creation_delay = 2.0
        self._last_client_creation = 0
        
        for _ in range(3):
            client = self._create_single_client()
            self._client_pool.put(client)
        
        logger.info(f"Initialized BigQuery client pool with 3 clients for project: {project_id}")
    
    def _create_single_client(self) -> bigquery.Client:
        with self._pool_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_client_creation
            if time_since_last < self._client_creation_delay:
                time.sleep(self._client_creation_delay - time_since_last)
            
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
                                maximum_bytes_billed=None
                            )
                        )
                        list(client.list_datasets(max_results=1))
                        self._last_client_creation = time.time()
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
                        maximum_bytes_billed=None
                    )
                )
                list(client.list_datasets(max_results=1))
                self._last_client_creation = time.time()
                return client
            except Exception as e:
                logger.error(f"All authentication methods failed: {e}")
                raise
    
    @contextmanager
    def get_client(self):
        client = None
        try:
            client = self._client_pool.get(timeout=30)
            yield client
        except queue.Empty:
            logger.warning("Client pool exhausted, creating temporary client")
            temp_client = self._create_single_client()
            try:
                yield temp_client
            finally:
                temp_client.close()
        except Exception as e:
            if "Connection pool is full" in str(e) or "ConnectionError" in str(e):
                logger.warning("Connection pool issue, creating new client")
                time.sleep(3)
                new_client = self._create_single_client()
                try:
                    yield new_client
                finally:
                    new_client.close()
            else:
                raise
        finally:
            if client:
                try:
                    self._client_pool.put_nowait(client)
                except queue.Full:
                    client.close()
    
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
    
    def close_all(self):
        while not self._client_pool.empty():
            try:
                client = self._client_pool.get_nowait()
                client.close()
            except queue.Empty:
                break