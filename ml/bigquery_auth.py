#!/usr/bin/env python3
"""
BigQuery Authentication Module
=============================
Exact authentication method from original working script.
"""

import os
from google.cloud import bigquery
from google.oauth2 import service_account
from ao1_config_and_logging import file_path, settings, logger

def authenticate_bigquery():
    """Authenticate with BigQuery using service account - EXACT from original"""
    SERVICE_ACCOUNT_FILE = os.path.join(file_path, "gcp_prod_key.json")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    settings['KATANA_PG'] = {'client_encoding': 'utf8'}
    project = "prj-fisv-p-gcss-sas-d19dd0f1df"
    client = bigquery.Client(project=project, credentials=credentials)
    logger.info("Successfully authenticated with BigQuery for AO1 exploration")
    return client

def get_bigquery_client():
    """Get authenticated BigQuery client."""
    try:
        return authenticate_bigquery()
    except Exception as e:
        logger.error(f"BigQuery authentication failed: {e}")
        raise