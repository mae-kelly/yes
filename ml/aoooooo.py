import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import yaml

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class ConfigurationError(Exception):
    pass

@dataclass
class BigQueryConfig:
    auth_project_id: str
    target_project_id: str
    service_account_path: str
    query_timeout: int = 300
    max_concurrent_queries: int = 10
    location: str = "US"
    use_query_cache: bool = True
    
    def __post_init__(self):
        if not os.path.exists(self.service_account_path):
            raise ConfigurationError(f"Service account file not found: {self.service_account_path}")

@dataclass
class RedisConfig:
    host: str
    port: int
    password: Optional[str] = None
    db: int = 0
    default_ttl: int = 3600
    max_connections: int = 100
    socket_timeout: int = 30
    
    def __post_init__(self):
        if not 1 <= self.port <= 65535:
            raise ConfigurationError(f"Invalid Redis port: {self.port}")

@dataclass
class DiscoveryConfig:
    confidence_threshold: float = 0.3
    max_datasets: int = 50
    max_tables_per_dataset: int = 25
    max_fields_per_table: int = 500
    enable_data_sampling: bool = True
    sample_size: int = 100
    ml_model_cache_ttl: int = 86400
    enable_semantic_analysis: bool = True
    
    def __post_init__(self):
        if not 0 <= self.confidence_threshold <= 1:
            raise ConfigurationError(f"Confidence threshold must be between 0 and 1: {self.confidence_threshold}")

@dataclass
class PerformanceConfig:
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    cache_memory_limit_mb: int = 500
    query_chunk_size: int = 100
    max_workers: int = 10
    request_rate_limit: int = 100
    
    def __post_init__(self):
        if self.circuit_breaker_threshold <= 0:
            raise ConfigurationError("Circuit breaker threshold must be positive")

@dataclass
class IntegrationConfig:
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_token: Optional[str] = None
    enabled: bool = False
    timeout: int = 30
    retry_attempts: int = 3

@dataclass
class MonitoringConfig:
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_port: int = 8080
    health_check_port: int = 8081
    enable_tracing: bool = False
    jaeger_endpoint: Optional[str] = None
    
    def __post_init__(self):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ConfigurationError(f"Invalid log level: {self.log_level}")

@dataclass
class SecurityConfig:
    enable_encryption: bool = True
    encryption_key_path: Optional[str] = None
    enable_audit_logging: bool = True
    max_query_results: int = 1000000
    allowed_datasets: Optional[List[str]] = None
    blocked_datasets: Optional[List[str]] = None

class ConfigurationManager:
    
    def __init__(self, environment: Optional[Union[str, Environment]] = None):
        if isinstance(environment, str):
            self.environment = Environment(environment.lower())
        elif isinstance(environment, Environment):
            self.environment = environment
        else:
            env_str = os.getenv('ENVIRONMENT', 'development').lower()
            self.environment = Environment(env_str)
        
        self.config_cache = {}
        self.logger = logging.getLogger(__name__)
    
    def get_config(self) -> Dict[str, Any]:
        if self.environment in self.config_cache:
            return self.config_cache[self.environment]
        
        base_config = self._get_base_config()
        env_config = self._get_environment_config()
        file_config = self._load_config_file()
        
        merged_config = self._merge_configs(base_config, env_config, file_config)
        validated_config = self._validate_and_convert_config(merged_config)
        
        self.config_cache[self.environment] = validated_config
        return validated_config
    
    def _get_base_config(self) -> Dict[str, Any]:
        return {
            'bigquery': {
                'auth_project_id': 'chronicle-fisv',
                'target_project_id': 'prj-fisv-p-gcss-sas-dl',
                'service_account_path': './gcp_key.json',
                'query_timeout': 300,
                'max_concurrent_queries': 10,
                'location': 'US',
                'use_query_cache': True
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'password': None,
                'db': 0,
                'default_ttl': 3600,
                'max_connections': 100,
                'socket_timeout': 30
            },
            'discovery': {
                'confidence_threshold': 0.3,
                'max_datasets': 50,
                'max_tables_per_dataset': 25,
                'max_fields_per_table': 500,
                'enable_data_sampling': True,
                'sample_size': 100,
                'ml_model_cache_ttl': 86400,
                'enable_semantic_analysis': True
            },
            'performance': {
                'circuit_breaker_threshold': 5,
                'circuit_breaker_timeout': 60,
                'cache_memory_limit_mb': 500,
                'query_chunk_size': 100,
                'max_workers': 10,
                'request_rate_limit': 100
            },
            'integrations': {
                'collibra': {
                    'base_url': None,
                    'api_key': None,
                    'enabled': False,
                    'timeout': 30,
                    'retry_attempts': 3
                },
                'alation': {
                    'base_url': None,
                    'api_token': None,
                    'enabled': False,
                    'timeout': 30,
                    'retry_attempts': 3
                },
                'datahub': {
                    'kafka_servers': None,
                    'schema_registry': None,
                    'enabled': False,
                    'timeout': 30,
                    'retry_attempts': 3
                }
            },
            'monitoring': {
                'log_level': 'INFO',
                'enable_metrics': True,
                'metrics_port': 8080,
                'health_check_port': 8081,
                'enable_tracing': False,
                'jaeger_endpoint': None
            },
            'security': {
                'enable_encryption': True,
                'encryption_key_path': None,
                'enable_audit_logging': True,
                'max_query_results': 1000000,
                'allowed_datasets': None,
                'blocked_datasets': None
            }
        }
    
    def _get_environment_config(self) -> Dict[str, Any]:
        if self.environment == Environment.PRODUCTION:
            return self._get_production_config()
        elif self.environment == Environment.STAGING:
            return self._get_staging_config()
        else:
            return self._get_development_config()
    
    def _get_production_config(self) -> Dict[str, Any]:
        return {
            'bigquery': {
                'auth_project_id': os.getenv('BIGQUERY_AUTH_PROJECT_ID', 'chronicle-fisv'),
                'target_project_id': os.getenv('BIGQUERY_TARGET_PROJECT_ID', 'prj-fisv-p-gcss-sas-dl'),
                'service_account_path': os.getenv('BIGQUERY_SERVICE_ACCOUNT_PATH', './gcp_prod_key.json'),
                'query_timeout': int(os.getenv('BIGQUERY_TIMEOUT', 600)),
                'max_concurrent_queries': int(os.getenv('BIGQUERY_MAX_QUERIES', 20)),
                'location': os.getenv('BIGQUERY_LOCATION', 'US'),
                'use_query_cache': os.getenv('BIGQUERY_USE_CACHE', 'true').lower() == 'true'
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'redis-prod.internal'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'password': os.getenv('REDIS_PASSWORD'),
                'db': int(os.getenv('REDIS_DB', 0)),
                'default_ttl': int(os.getenv('REDIS_TTL', 7200)),
                'max_connections': int(os.getenv('REDIS_MAX_CONN', 200)),
                'socket_timeout': int(os.getenv('REDIS_TIMEOUT', 30))
            },
            'discovery': {
                'confidence_threshold': float(os.getenv('DISCOVERY_CONFIDENCE', 0.5)),
                'max_datasets': int(os.getenv('DISCOVERY_MAX_DATASETS', 100)),
                'max_tables_per_dataset': int(os.getenv('DISCOVERY_MAX_TABLES', 50)),
                'max_fields_per_table': int(os.getenv('DISCOVERY_MAX_FIELDS', 1000)),
                'enable_data_sampling': os.getenv('DISCOVERY_SAMPLING', 'true').lower() == 'true',
                'sample_size': int(os.getenv('DISCOVERY_SAMPLE_SIZE', 500)),
                'ml_model_cache_ttl': int(os.getenv('ML_CACHE_TTL', 86400)),
                'enable_semantic_analysis': os.getenv('SEMANTIC_ANALYSIS', 'true').lower() == 'true'
            },
            'performance': {
                'circuit_breaker_threshold': int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', 10)),
                'circuit_breaker_timeout': int(os.getenv('CIRCUIT_BREAKER_TIMEOUT', 120)),
                'cache_memory_limit_mb': int(os.getenv('CACHE_MEMORY_LIMIT', 1024)),
                'query_chunk_size': int(os.getenv('QUERY_CHUNK_SIZE', 200)),
                'max_workers': int(os.getenv('MAX_WORKERS', 20)),
                'request_rate_limit': int(os.getenv('RATE_LIMIT', 500))
            },
            'integrations': {
                'collibra': {
                    'base_url': os.getenv('COLLIBRA_URL'),
                    'api_key': os.getenv('COLLIBRA_API_KEY'),
                    'enabled': os.getenv('COLLIBRA_ENABLED', 'false').lower() == 'true',
                    'timeout': int(os.getenv('COLLIBRA_TIMEOUT', 60)),
                    'retry_attempts': int(os.getenv('COLLIBRA_RETRIES', 5))
                },
                'alation': {
                    'base_url': os.getenv('ALATION_URL'),
                    'api_token': os.getenv('ALATION_TOKEN'),
                    'enabled': os.getenv('ALATION_ENABLED', 'false').lower() == 'true',
                    'timeout': int(os.getenv('ALATION_TIMEOUT', 60)),
                    'retry_attempts': int(os.getenv('ALATION_RETRIES', 5))
                },
                'datahub': {
                    'kafka_servers': os.getenv('DATAHUB_KAFKA_SERVERS'),
                    'schema_registry': os.getenv('DATAHUB_SCHEMA_REGISTRY'),
                    'enabled': os.getenv('DATAHUB_ENABLED', 'false').lower() == 'true',
                    'timeout': int(os.getenv('DATAHUB_TIMEOUT', 60)),
                    'retry_attempts': int(os.getenv('DATAHUB_RETRIES', 5))
                }
            },
            'monitoring': {
                'log_level': os.getenv('LOG_LEVEL', 'WARNING'),
                'enable_metrics': os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
                'metrics_port': int(os.getenv('METRICS_PORT', 8080)),
                'health_check_port': int(os.getenv('HEALTH_PORT', 8081)),
                'enable_tracing': os.getenv('ENABLE_TRACING', 'true').lower() == 'true',
                'jaeger_endpoint': os.getenv('JAEGER_ENDPOINT')
            },
            'security': {
                'enable_encryption': os.getenv('ENABLE_ENCRYPTION', 'true').lower() == 'true',
                'encryption_key_path': os.getenv('ENCRYPTION_KEY_PATH'),
                'enable_audit_logging': os.getenv('ENABLE_AUDIT', 'true').lower() == 'true',
                'max_query_results': int(os.getenv('MAX_QUERY_RESULTS', 10000000)),
                'allowed_datasets': self._parse_list_env('ALLOWED_DATASETS'),
                'blocked_datasets': self._parse_list_env('BLOCKED_DATASETS')
            }
        }
    
    def _get_staging_config(self) -> Dict[str, Any]:
        config = self._get_production_config()
        config['bigquery']['service_account_path'] = os.getenv('BIGQUERY_SERVICE_ACCOUNT_PATH', './gcp_staging_key.json')
        config['redis']['host'] = os.getenv('REDIS_HOST', 'redis-staging.internal')
        config['monitoring']['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
        config['discovery']['confidence_threshold'] = float(os.getenv('DISCOVERY_CONFIDENCE', 0.3))
        return config
    
    def _get_development_config(self) -> Dict[str, Any]:
        config = self._get_base_config()
        config['bigquery']['service_account_path'] = os.getenv('BIGQUERY_SERVICE_ACCOUNT_PATH', './gcp_dev_key.json')
        config['monitoring']['log_level'] = os.getenv('LOG_LEVEL', 'DEBUG')
        config['monitoring']['enable_tracing'] = True
        config['discovery']['confidence_threshold'] = float(os.getenv('DISCOVERY_CONFIDENCE', 0.1))
        config['discovery']['max_datasets'] = int(os.getenv('DISCOVERY_MAX_DATASETS', 10))
        return config
    
    def _load_config_file(self) -> Dict[str, Any]:
        config_paths = [
            f'config/{self.environment.value}.yaml',
            f'config/{self.environment.value}.yml',
            f'config/{self.environment.value}.json',
            'config/config.yaml',
            'config/config.yml',
            'config/config.json'
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        if config_path.endswith('.json'):
                            return json.load(f)
                        else:
                            return yaml.safe_load(f) or {}
                except Exception as e:
                    self.logger.warning(f"Failed to load config file {config_path}: {e}")
        
        return {}
    
    def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        merged = {}
        for config in configs:
            merged = self._deep_merge(merged, config)
        return merged
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _validate_and_convert_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        errors = self.validate_config(config)
        if errors:
            raise ConfigurationError(f"Configuration validation failed: {', '.join(errors)}")
        
        validated_config = {
            'bigquery': BigQueryConfig(**config['bigquery']),
            'redis': RedisConfig(**config['redis']),
            'discovery': DiscoveryConfig(**config['discovery']),
            'performance': PerformanceConfig(**config['performance']),
            'monitoring': MonitoringConfig(**config['monitoring']),
            'security': SecurityConfig(**config['security']),
            'integrations': {
                name: IntegrationConfig(**integration_config)
                for name, integration_config in config['integrations'].items()
            }
        }
        
        return validated_config
    
    def _parse_list_env(self, env_var: str) -> Optional[List[str]]:
        value = os.getenv(env_var)
        if value:
            return [item.strip() for item in value.split(',') if item.strip()]
        return None
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        errors = []
        
        bigquery_config = config.get('bigquery', {})
        if not bigquery_config.get('auth_project_id'):
            errors.append("BigQuery auth_project_id is required")
        
        if not bigquery_config.get('target_project_id'):
            errors.append("BigQuery target_project_id is required")
        
        service_account_path = bigquery_config.get('service_account_path')
        if not service_account_path:
            errors.append("BigQuery service account path is required")
        elif not os.path.exists(service_account_path):
            errors.append(f"BigQuery service account file not found: {service_account_path}")
        
        redis_config = config.get('redis', {})
        redis_port = redis_config.get('port')
        if not isinstance(redis_port, int) or not 1 <= redis_port <= 65535:
            errors.append("Redis port must be an integer between 1 and 65535")
        
        discovery_config = config.get('discovery', {})
        confidence_threshold = discovery_config.get('confidence_threshold', 0)
        if not isinstance(confidence_threshold, (int, float)) or not 0 <= confidence_threshold <= 1:
            errors.append("Confidence threshold must be a number between 0 and 1")
        
        performance_config = config.get('performance', {})
        circuit_breaker_threshold = performance_config.get('circuit_breaker_threshold', 0)
        if not isinstance(circuit_breaker_threshold, int) or circuit_breaker_threshold <= 0:
            errors.append("Circuit breaker threshold must be a positive integer")
        
        monitoring_config = config.get('monitoring', {})
        log_level = monitoring_config.get('log_level', '').upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level not in valid_levels:
            errors.append(f"Log level must be one of: {', '.join(valid_levels)}")
        
        metrics_port = monitoring_config.get('metrics_port')
        health_port = monitoring_config.get('health_check_port')
        if isinstance(metrics_port, int) and isinstance(health_port, int):
            if metrics_port == health_port:
                errors.append("Metrics port and health check port cannot be the same")
        
        security_config = config.get('security', {})
        max_query_results = security_config.get('max_query_results', 0)
        if not isinstance(max_query_results, int) or max_query_results <= 0:
            errors.append("Max query results must be a positive integer")
        
        return errors
    
    def get_ao1_discovery_config(self) -> 'AO1DiscoveryConfig':
        config = self.get_config()
        
        return AO1DiscoveryConfig(
            project_id=config['bigquery'].target_project_id,
            credentials_path=config['bigquery'].service_account_path,
            redis_host=config['redis'].host,
            redis_port=config['redis'].port,
            redis_password=config['redis'].password,
            redis_db=config['redis'].db,
            cache_ttl=config['redis'].default_ttl,
            max_workers=config['performance'].max_workers,
            sample_size=config['discovery'].sample_size,
            confidence_threshold=config['discovery'].confidence_threshold,
            enable_ml=config['discovery'].enable_semantic_analysis,
            enable_caching=True,
            enable_tracing=config['monitoring'].enable_tracing,
            circuit_breaker_threshold=config['performance'].circuit_breaker_threshold,
            circuit_breaker_timeout=config['performance'].circuit_breaker_timeout,
            query_timeout=config['bigquery'].query_timeout,
            max_concurrent_queries=config['bigquery'].max_concurrent_queries,
            allowed_datasets=config['security'].allowed_datasets,
            blocked_datasets=config['security'].blocked_datasets,
            max_query_results=config['security'].max_query_results
        )
    
    def export_config(self, output_path: str, format: str = 'yaml'):
        config = self.get_config()
        
        config_dict = {}
        for key, value in config.items():
            if hasattr(value, '__dict__'):
                config_dict[key] = value.__dict__
            elif isinstance(value, dict):
                config_dict[key] = {k: v.__dict__ if hasattr(v, '__dict__') else v for k, v in value.items()}
            else:
                config_dict[key] = value
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            if format.lower() == 'json':
                json.dump(config_dict, f, indent=2, default=str)
            else:
                yaml.dump(config_dict, f, default_flow_style=False)
    
    def reload_config(self):
        if self.environment in self.config_cache:
            del self.config_cache[self.environment]
        return self.get_config()

@dataclass
class AO1DiscoveryConfig:
    project_id: str
    credentials_path: str
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    cache_ttl: int = 3600
    max_workers: int = 10
    sample_size: int = 1000
    confidence_threshold: float = 0.7
    enable_ml: bool = True
    enable_caching: bool = True
    enable_tracing: bool = False
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    query_timeout: int = 300
    max_concurrent_queries: int = 10
    allowed_datasets: Optional[List[str]] = None
    blocked_datasets: Optional[List[str]] = None
    max_query_results: int = 1000000

def create_config_manager(environment: Optional[str] = None) -> ConfigurationManager:
    return ConfigurationManager(environment)

def get_ao1_config(environment: Optional[str] = None) -> AO1DiscoveryConfig:
    config_manager = create_config_manager(environment)
    return config_manager.get_ao1_discovery_config()

if __name__ == "__main__":
    import sys
    
    env = sys.argv[1] if len(sys.argv) > 1 else None
    config_manager = create_config_manager(env)
    
    try:
        config = config_manager.get_config()
        print(f"Configuration loaded successfully for environment: {config_manager.environment.value}")
        
        ao1_config = config_manager.get_ao1_discovery_config()
        print(f"AO1 Discovery Config: Project ID = {ao1_config.project_id}")
        print(f"Confidence Threshold: {ao1_config.confidence_threshold}")
        print(f"ML Enabled: {ao1_config.enable_ml}")
        
        output_path = f"config/validated_{config_manager.environment.value}.yaml"
        config_manager.export_config(output_path)
        print(f"Configuration exported to: {output_path}")
        
    except ConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)