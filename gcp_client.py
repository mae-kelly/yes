#!/usr/bin/env python3

import os
import logging
import time
import threading
import queue
from contextlib import contextmanager
from typing import Optional
import gc

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
        self._total_clients = 0
        self._max_clients = 3
        self._client_timeout = 30
        
        try:
            for _ in range(2):
                client = self._create_fresh_client()
                self._client_pool.put(client)
                self._total_clients += 1
            logger.info(f"Initialized connection pool with {self._total_clients} clients")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client pool: {e}")
            raise
    
    def _create_fresh_client(self) -> bigquery.Client:
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
                            use_query_cache=True,
                            job_timeout_ms=30000,
                            maximum_bytes_billed=None
                        )
                    )
                    list(client.list_datasets(max_results=1))
                    return client
                except Exception as e:
                    logger.debug(f"Service account {path} failed: {e}")
                    continue
        
        try:
            client = bigquery.Client(
                project=self.project_id,
                default_query_job_config=bigquery.QueryJobConfig(
                    use_query_cache=True,
                    job_timeout_ms=30000,
                    maximum_bytes_billed=None
                )
            )
            list(client.list_datasets(max_results=1))
            return client
        except Exception as e:
            logger.error(f"All authentication methods failed: {e}")
            raise
    
    @contextmanager
    def get_client(self):
        client = None
        acquired_from_pool = False
        
        try:
            try:
                client = self._client_pool.get(timeout=5)
                acquired_from_pool = True
            except queue.Empty:
                with self._pool_lock:
                    if self._total_clients < self._max_clients:
                        client = self._create_fresh_client()
                        self._total_clients += 1
                        logger.debug(f"Created new client, total: {self._total_clients}")
                    else:
                        client = self._client_pool.get(timeout=10)
                        acquired_from_pool = True
            
            yield client
            
        except Exception as e:
            if "Connection pool is full" in str(e) or "pool" in str(e).lower():
                logger.warning("Connection pool issue, creating temporary client")
                time.sleep(2)
                temp_client = self._create_fresh_client()
                yield temp_client
                temp_client.close()
                del temp_client
                gc.collect()
            else:
                raise
        finally:
            if client and acquired_from_pool:
                try:
                    self._client_pool.put(client, timeout=1)
                except queue.Full:
                    client.close()
                    del client
                    with self._pool_lock:
                        self._total_clients -= 1
    
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
                del client
            except queue.Empty:
                break
        gc.collect()
        logger.info("Closed all BigQuery client connections")