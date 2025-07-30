#!/usr/bin/env python3
"""
AO1 Configuration and Logging Setup
==================================
Core configuration, logging, and constants for AO1 system.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Configuration exactly like original working script
file_path = os.path.join(os.path.dirname(__file__))
settings = {}

# Logging setup matching original
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ao1_discovery.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# AO1 Project Configuration
AO1_CONFIG = {
    'project_id': 'prj-fisv-p-gcss-sas-d19dd0f1df',
    'service_account_file': 'gcp_prod_key.json',
    'max_retries': 3,
    'timeout_seconds': 30,
    'batch_size': 100
}

# AO1 Requirements metadata
AO1_REQUIREMENTS_META = {
    'REQ-1': {
        'name': 'Global View',
        'description': 'Asset identifiers for CMDB comparison',
        'priority': 'HIGH',
        'table_indicators': ['cmdb', 'asset', 'inventory', 'device']
    },
    'REQ-2': {
        'name': 'Infrastructure Type', 
        'description': 'Deployment model classification',
        'priority': 'HIGH',
        'table_indicators': ['cloud', 'infrastructure', 'vm', 'instance']
    },
    'REQ-3': {
        'name': 'Regional/Country View',
        'description': 'Geographic classification',
        'priority': 'MEDIUM',
        'table_indicators': ['region', 'location', 'geo', 'country']
    },
    'REQ-4': {
        'name': 'Business/Application View',
        'description': 'Organizational classification',
        'priority': 'MEDIUM', 
        'table_indicators': ['business', 'application', 'service', 'org']
    },
    'REQ-5': {
        'name': 'System Classification',
        'description': 'Server function and OS classification',
        'priority': 'MEDIUM',
        'table_indicators': ['system', 'server', 'os', 'platform']
    },
    'REQ-6': {
        'name': 'Security Control Coverage',
        'description': 'Agent presence measurement',
        'priority': 'HIGH',
        'table_indicators': ['security', 'agent', 'edr', 'endpoint']
    },
    'REQ-7': {
        'name': 'Logging Compliance', 
        'description': 'SIEM platform compliance',
        'priority': 'HIGH',
        'table_indicators': ['log', 'siem', 'chronicle', 'splunk']
    },
    'REQ-8': {
        'name': 'Domain Visibility',
        'description': 'DNS and domain visibility',
        'priority': 'MEDIUM',
        'table_indicators': ['domain', 'dns', 'hostname', 'fqdn']
    }
}

def get_config() -> Dict[str, Any]:
    """Get AO1 configuration."""
    return AO1_CONFIG.copy()

def get_requirements_meta() -> Dict[str, Any]:
    """Get AO1 requirements metadata."""
    return AO1_REQUIREMENTS_META.copy()

def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Setup logging with specified level."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)
    return logger