#!/usr/bin/env python3

import os
import logging
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
        self.client = None
        
        try:
            self.client = self._create_client()
            logger.info(f"Connected to BigQuery project: {project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
    
    def _create_client(self) -> bigquery.Client:
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
                    client = bigquery.Client(project=self.project_id, credentials=credentials)
                    list(client.list_datasets(max_results=1))
                    logger.info(f"Successfully authenticated using service account: {path}")
                    return client
                except Exception as e:
                    logger.debug(f"Service account {path} failed: {e}")
                    continue
        
        try:
            logger.info("Attempting default credentials authentication")
            client = bigquery.Client(project=self.project_id)
            list(client.list_datasets(max_results=1))
            logger.info("Successfully authenticated using default credentials")
            return client
        except Exception as e:
            logger.error(f"All authentication methods failed: {e}")
            logger.error("Authentication methods tried:")
            logger.error("1. Service account key: gcp_prod_key.json")
            logger.error("2. GOOGLE_APPLICATION_CREDENTIALS environment variable")
            logger.error("3. Default gcloud credentials")
            raise
    
    @contextmanager
    def get_client(self):
        if self.client is None:
            try:
                self.client = self._create_client()
            except Exception as e:
                logger.error(f"Failed to create BigQuery client: {e}")
                raise
        try:
            yield self.client
        except Exception as e:
            logger.error(f"BigQuery operation failed: {e}")
            raise
        finally:
            pass
    
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