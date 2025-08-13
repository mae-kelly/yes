#!/usr/bin/env python3

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_file: str = None) -> Dict[str, Any]:
    default_config = {
        'max_workers': min(32, os.cpu_count() * 2),
        'batch_size': 1000,
        'cache_dir': '.cache',
        'database_path': 'universal_cmdb.db',
        'max_tables_per_dataset': 200,
        'enable_checkpointing': True,
        'checkpoint_interval_minutes': 5,
        'skip_large_tables': True,
        'max_table_size_gb': 50,
        'prioritize_core_datasets': True,
        'parallel_dataset_processing': True,
        'cache_ttl_hours': 24,
        'sample_validation_threshold': 0.4,
        'confidence_threshold': 0.3
    }
    
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    user_config = yaml.safe_load(f)
                else:
                    user_config = json.load(f)
            
            default_config.update(user_config)
        except Exception:
            pass
    
    return default_config

def create_default_config(filename: str = "config.yaml"):
    config = {
        'intelligence_level': 'standard',
        'max_memory_mb': 1024,
        'max_disk_gb': 10,
        'enable_intelligent_caching': True,
        'cache_compression': True,
        'cache_ttl_hours': 24,
        'database_path': 'discovery_cmdb.db',
        'enable_pattern_recognition': True,
        'enable_statistical_analysis': True,
        'semantic_confidence_threshold': 0.5,
        'validation_confidence_threshold': 0.6,
        'data_quality_threshold': 0.7,
        'enable_parallel_processing': True,
        'max_concurrent_tables': 5,
        'enable_intelligent_checkpointing': True,
        'checkpoint_interval_minutes': 2,
        'log_level': 'INFO',
        'enable_performance_logging': True,
        'max_tables_per_dataset': 100,
        'max_rows_per_query': 100000,
        'max_processing_time_hours': 4
    }
    
    with open(filename, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=True)
    
    return config