#!/usr/bin/env python3

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    @staticmethod
    def load_config(config_file: str = None) -> Dict[str, Any]:
        default_config = {
            'max_workers': min(32, os.cpu_count() * 2),
            'max_cost_per_query': 1.0,
            'max_total_cost': 100.0,
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