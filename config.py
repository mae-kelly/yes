"""
Configuration module for the comprehensive AI Asset Discovery System
Contains all configuration parameters, constants, and shared settings
"""

import torch
import os
from datetime import datetime

# Device configuration
if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    DEVICE_NAME = "NVIDIA GPU (CUDA)"
elif torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
    DEVICE_NAME = "Apple Silicon GPU (MPS)"
else:
    DEVICE = torch.device("cpu")
    DEVICE_NAME = "CPU"

# Database configuration
DB_PATH = 'universal_cmdb.db'
DB_TIMEOUT = 30

# Model directories
MODEL_DIR = 'models'
REPORTS_DIR = 'reports'
CACHE_DIR = 'cache'
LOGS_DIR = 'logs'

# Create directories
for directory in [MODEL_DIR, REPORTS_DIR, CACHE_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Pattern discovery configuration
PATTERN_CONFIG = {
    'min_pattern_frequency': 2,
    'max_gap_size': 10000,
    'max_sequence_length': 1000,
    'min_density_threshold': 0.1,
    'pattern_cache_ttl': 3600,  # seconds
    'enable_regex_patterns': True,
    'enable_ngram_analysis': True,
    'ngram_sizes': [2, 3, 4],
    'markov_order': 2
}

# Neural network configuration
NN_CONFIG = {
    'hostname_net': {
        'hidden_sizes': [512, 256, 128, 64, 32],
        'dropout_rates': [0.3, 0.3, 0.2, 0.1, 0.1],
        'use_batch_norm': True,
        'activation': 'relu'
    },
    'lstm_config': {
        'hidden_size': 256,
        'num_layers': 3,
        'bidirectional': True,
        'dropout': 0.2,
        'attention': True
    },
    'transformer_config': {
        'num_heads': 8,
        'hidden_size': 512,
        'num_layers': 6,
        'dropout': 0.1,
        'max_seq_length': 512
    },
    'autoencoder_config': {
        'encoder_sizes': [128, 64, 32, 16],
        'decoder_sizes': [16, 32, 64, 128],
        'latent_dim': 16,
        'variational': True
    }
}

# Training configuration
TRAINING_CONFIG = {
    'batch_size_gpu': 4096,
    'batch_size_cpu': 512,
    'epochs': 100,
    'learning_rate': 0.001,
    'weight_decay': 1e-4,
    'early_stopping_patience': 15,
    'validation_split': 0.2,
    'test_split': 0.1,
    'gradient_clip': 1.0,
    'use_mixed_precision': True,
    'num_workers': 4,
    'pin_memory': True
}

# Anomaly detection configuration
ANOMALY_CONFIG = {
    'isolation_forest': {
        'n_estimators': 200,
        'contamination': 0.1,
        'max_features': 1.0,
        'bootstrap': False
    },
    'one_class_svm': {
        'kernel': 'rbf',
        'gamma': 'auto',
        'nu': 0.05,
        'degree': 3
    },
    'lof': {
        'n_neighbors': 20,
        'contamination': 0.1,
        'novelty': True,
        'metric': 'minkowski'
    },
    'dbscan': {
        'eps': 0.5,
        'min_samples': 5,
        'metric': 'euclidean'
    }
}

# Time series configuration
TIMESERIES_CONFIG = {
    'arima': {
        'max_p': 5,
        'max_d': 2,
        'max_q': 5,
        'seasonal': True,
        'seasonal_period': 7,
        'information_criterion': 'aic',
        'stepwise': True
    },
    'prophet': {
        'yearly_seasonality': True,
        'weekly_seasonality': True,
        'daily_seasonality': False,
        'changepoint_prior_scale': 0.05,
        'seasonality_prior_scale': 10,
        'holidays_prior_scale': 10,
        'interval_width': 0.95
    },
    'change_detection': {
        'methods': ['cusum', 'pelt', 'binseg'],
        'penalty': 'BIC',
        'min_segment_size': 10,
        'jump': 5
    }
}

# Graph neural network configuration
GRAPH_CONFIG = {
    'gnn': {
        'hidden_channels': 256,
        'num_layers': 3,
        'dropout': 0.2,
        'aggregation': 'mean',
        'use_attention': True
    },
    'topology': {
        'max_nodes': 100000,
        'edge_threshold': 0.5,
        'community_detection': 'louvain',
        'centrality_measures': ['degree', 'betweenness', 'closeness', 'eigenvector']
    }
}

# Network scanning configuration
SCANNING_CONFIG = {
    'protocols': {
        'snmp': {
            'version': '2c',
            'community': 'public',
            'timeout': 5,
            'retries': 3,
            'port': 161
        },
        'wmi': {
            'timeout': 30,
            'namespace': 'root\\cimv2'
        },
        'ssh': {
            'port': 22,
            'timeout': 10,
            'key_file': None
        },
        'api': {
            'timeout': 30,
            'max_retries': 3,
            'backoff_factor': 1.0
        }
    },
    'discovery': {
        'parallel_workers': 10,
        'batch_size': 100,
        'rate_limit': 100,  # requests per second
        'scan_interval': 3600  # seconds
    }
}

# NLP configuration
NLP_CONFIG = {
    'tokenizer': 'bert-base-uncased',
    'max_length': 512,
    'embedding_dim': 768,
    'use_pretrained': True,
    'fine_tune': False,
    'doc_types': ['runbook', 'config', 'ticket', 'wiki'],
    'entity_recognition': True,
    'relation_extraction': True
}

# Distributed processing configuration
DISTRIBUTED_CONFIG = {
    'kafka': {
        'bootstrap_servers': 'localhost:9092',
        'topic_prefix': 'asset_discovery',
        'consumer_group': 'ml_processors',
        'auto_offset_reset': 'earliest',
        'enable_auto_commit': True
    },
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
        'socket_timeout': 5
    },
    'ray': {
        'num_cpus': None,  # Auto-detect
        'num_gpus': None,  # Auto-detect
        'object_store_memory': None,  # Auto
        'dashboard_host': '0.0.0.0'
    }
}

# Confidence thresholds
CONFIDENCE_LEVELS = {
    'critical': 0.90,
    'high': 0.75,
    'medium': 0.60,
    'low': 0.40,
    'experimental': 0.20
}

# Risk scoring weights
RISK_WEIGHTS = {
    'environment': {
        'production': 0.9,
        'staging': 0.6,
        'uat': 0.5,
        'test': 0.3,
        'development': 0.2
    },
    'role_criticality': {
        'firewall': 0.95,
        'database': 0.95,
        'load_balancer': 0.90,
        'authentication': 0.90,
        'dns': 0.85,
        'web_server': 0.75,
        'app_server': 0.75,
        'cache': 0.60,
        'monitoring': 0.50,
        'default': 0.30
    },
    'visibility_gap': 0.4,
    'pattern_reliability': 0.2,
    'anomaly_score': 0.3
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    'max_memory_gb': 16,
    'max_processing_time_seconds': 3600,
    'max_candidates_to_analyze': 50000,
    'batch_timeout_seconds': 300,
    'cache_size_mb': 1024
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': f'{LOGS_DIR}/asset_discovery_{datetime.now().strftime("%Y%m%d")}.log',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5
}

# Feature extraction configuration
FEATURE_CONFIG = {
    'hostname_features': 100,  # Expanded from 65
    'context_features': 25,
    'temporal_features': 10,
    'graph_features': 20,
    'total_features': 155
}

# Export configuration
EXPORT_CONFIG = {
    'formats': ['json', 'csv', 'parquet', 'excel'],
    'compression': 'gzip',
    'include_metadata': True,
    'timestamp_format': '%Y%m%d_%H%M%S'
}

# Integration endpoints
INTEGRATION_ENDPOINTS = {
    'servicenow': {
        'url': 'https://instance.service-now.com/api',
        'auth_type': 'basic',
        'verify_ssl': True
    },
    'splunk': {
        'url': 'https://splunk.example.com:8089',
        'auth_type': 'token',
        'verify_ssl': True
    },
    'azure': {
        'resource_graph_url': 'https://management.azure.com/providers/Microsoft.ResourceGraph/resources',
        'auth_type': 'oauth2'
    }
}

# Model versioning
MODEL_VERSION = "Comprehensive-Asset-Discovery-v4.0"
SCHEMA_VERSION = "2.0"

# Success metrics targets
SUCCESS_METRICS = {
    'detection_accuracy': 0.95,  # 95% target
    'false_positive_rate': 0.05,  # 5% max
    'processing_time_hours': 1,  # 1 hour max
    'coverage_percentage': 0.99,  # 99% coverage
    'roi_multiplier': 3.0  # 3x ROI minimum
}