import os
from typing import Dict, Any, List

class ConfigurationManager:
    @staticmethod
    def get_production_config() -> Dict[str, Any]:
        return {
            'bigquery': {
                'auth_project_id': os.getenv('BIGQUERY_AUTH_PROJECT_ID', 'chronicle-fisv'),
                'target_project_id': os.getenv('BIGQUERY_TARGET_PROJECT_ID', 'prj-fisv-p-gcss-sas-dl9dd0f1df'),
                'service_account_path': os.getenv('BIGQUERY_SERVICE_ACCOUNT_PATH', './gcp_prod_key.json'),
                'query_timeout': 300,
                'max_concurrent_queries': 10
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'password': os.getenv('REDIS_PASSWORD'),
                'default_ttl': 3600
            },
            'discovery': {
                'confidence_threshold': 0.3,
                'max_datasets': 50,
                'max_tables_per_dataset': 25,
                'max_fields_per_table': 500,
                'enable_data_sampling': True,
                'sample_size': 100
            },
            'performance': {
                'circuit_breaker_threshold': 5,
                'circuit_breaker_timeout': 60,
                'cache_memory_limit_mb': 500,
                'query_chunk_size': 100
            },
            'integrations': {
                'collibra': {
                    'base_url': os.getenv('COLLIBRA_URL'),
                    'api_key': os.getenv('COLLIBRA_API_KEY'),
                    'enabled': os.getenv('COLLIBRA_ENABLED', 'false').lower() == 'true'
                },
                'alation': {
                    'base_url': os.getenv('ALATION_URL'),
                    'api_token': os.getenv('ALATION_TOKEN'),
                    'enabled': os.getenv('ALATION_ENABLED', 'false').lower() == 'true'
                },
                'datahub': {
                    'kafka_servers': os.getenv('DATAHUB_KAFKA_SERVERS'),
                    'schema_registry': os.getenv('DATAHUB_SCHEMA_REGISTRY'),
                    'enabled': os.getenv('DATAHUB_ENABLED', 'false').lower() == 'true'
                }
            },
            'monitoring': {
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'enable_metrics': True,
                'metrics_port': int(os.getenv('METRICS_PORT', 8080)),
                'health_check_port': int(os.getenv('HEALTH_PORT', 8081))
            }
        }
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        errors = []
        
        if not config.get('bigquery', {}).get('auth_project_id'):
            errors.append("BigQuery auth_project_id is required")
        
        if not config.get('bigquery', {}).get('target_project_id'):
            errors.append("BigQuery target_project_id is required")
        
        if not config.get('bigquery', {}).get('service_account_path'):
            errors.append("BigQuery service account path is required")
        
        redis_config = config.get('redis', {})
        if not isinstance(redis_config.get('port'), int) or redis_config.get('port') <= 0:
            errors.append("Redis port must be a positive integer")
        
        discovery_config = config.get('discovery', {})
        confidence_threshold = discovery_config.get('confidence_threshold', 0)
        if not 0 <= confidence_threshold <= 1:
            errors.append("Confidence threshold must be between 0 and 1")
        
        return errors