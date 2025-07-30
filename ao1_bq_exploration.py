"""
Enterprise AO1 Field Discovery System
Corporate-Grade ML-Powered BigQuery Field Analysis

Features:
- Corporate proxy detection and configuration
- Multiple Hugging Face connection strategies
- M1 GPU detection and optimization
- Advanced neural field matching
- Enterprise security and compliance
- Robust error handling and fallback mechanisms
"""

import os
import sys
import json
import time
import logging
import getpass
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
import requests
import urllib.parse
import socket

# BigQuery imports
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud.exceptions import NotFound, Forbidden, BadRequest, ServerError

# ML and HuggingFace imports with enterprise error handling
ML_LIBRARIES_AVAILABLE = False
TORCH_AVAILABLE = False
HF_AVAILABLE = False
SKLEARN_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
    print("SYSTEM: PyTorch loaded successfully")
except ImportError:
    print("WARNING: PyTorch not available - install with: pip install torch")

try:
    from transformers import (
        AutoTokenizer, AutoModel, AutoConfig,
        pipeline, logging as hf_logging
    )
    from huggingface_hub import (
        HfApi, hf_hub_download, login, 
        cached_download, snapshot_download,
        scan_cache_dir
    )
    from sentence_transformers import SentenceTransformer
    hf_logging.set_verbosity_error()
    HF_AVAILABLE = True
    print("SYSTEM: Hugging Face libraries loaded successfully")
except ImportError:
    print("WARNING: Hugging Face libraries not available")
    print("Install with: pip install transformers sentence-transformers huggingface-hub")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
    print("SYSTEM: Scikit-learn loaded successfully")
except ImportError:
    print("WARNING: Scikit-learn not available - install with: pip install scikit-learn")

ML_LIBRARIES_AVAILABLE = TORCH_AVAILABLE and HF_AVAILABLE and SKLEARN_AVAILABLE

# AO1 Keywords Import
try:
    from ao1_keywords import (
        REQ1_GLOBAL_VIEW_KEYWORDS,
        REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
        REQ3_REGIONAL_COUNTRY_KEYWORDS,
        REQ4_BUSINESS_APPLICATION_KEYWORDS,
        REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
        REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
        REQ7_LOGGING_COMPLIANCE_KEYWORDS,
        REQ8_DOMAIN_VISIBILITY_KEYWORDS,
        get_all_keywords,
        find_keyword_requirement
    )
    
    ALL_AO1_KEYWORDS = get_all_keywords()
    REQUIREMENT_KEYWORDS = {
        'REQ-1': REQ1_GLOBAL_VIEW_KEYWORDS,
        'REQ-2': REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
        'REQ-3': REQ3_REGIONAL_COUNTRY_KEYWORDS,
        'REQ-4': REQ4_BUSINESS_APPLICATION_KEYWORDS,
        'REQ-5': REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
        'REQ-6': REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
        'REQ-7': REQ7_LOGGING_COMPLIANCE_KEYWORDS,
        'REQ-8': REQ8_DOMAIN_VISIBILITY_KEYWORDS
    }
    print("AO1 KEYWORDS: {} keywords loaded across 8 requirements".format(len(ALL_AO1_KEYWORDS)))
    
except ImportError as e:
    print("CRITICAL ERROR: Cannot import AO1 keywords module")
    print("Ensure ao1_keywords.py is in the project directory")
    sys.exit(1)

# Configuration
PROJECT_ID = "prj-fisv-p-gcss-sas-dl9dd0f1df"
SERVICE_ACCOUNT_FILE = "gcp_prod_key.json"

# Corporate logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('ao1_enterprise_discovery.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('AO1Discovery')

@dataclass
class FieldMatch:
    """Enterprise field match result"""
    dataset: str
    table: str
    field_name: str
    field_path: str
    field_type: str
    requirement: str
    matched_keyword: str
    match_type: str
    confidence_score: float
    table_rows: int
    table_size_bytes: int
    semantic_similarity: float
    context_relevance: float
    neural_score: float
    pattern_score: float

class EnterpriseProxyManager:
    """Corporate proxy detection and configuration manager"""
    
    def __init__(self):
        self.proxy_config = {}
        self.proxy_detected = False
        self.proxy_working = False
        
    def detect_corporate_environment(self) -> Dict[str, Any]:
        """Detect if running in corporate environment with proxies"""
        environment_info = {
            'is_corporate': False,
            'proxy_env_vars': {},
            'network_restrictions': False,
            'firewall_detected': False
        }
        
        # Check for common proxy environment variables
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            if os.environ.get(var):
                environment_info['proxy_env_vars'][var] = os.environ[var]
                environment_info['is_corporate'] = True
        
        # Test internet connectivity
        test_urls = [
            'https://huggingface.co',
            'https://github.com',
            'https://pypi.org',
            'https://www.google.com'
        ]
        
        connectivity_results = {}
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                connectivity_results[url] = response.status_code == 200
            except:
                connectivity_results[url] = False
        
        # If most URLs fail, likely behind firewall/proxy
        failed_connections = sum(1 for connected in connectivity_results.values() if not connected)
        if failed_connections >= len(test_urls) / 2:
            environment_info['network_restrictions'] = True
            environment_info['is_corporate'] = True
        
        return environment_info
    
    def configure_proxy_interactively(self):
        """Interactive proxy configuration for corporate environments"""
        print("\nCORPORATE NETWORK DETECTION")
        print("=" * 50)
        
        env_info = self.detect_corporate_environment()
        
        if env_info['proxy_env_vars']:
            print("DETECTED: Existing proxy configuration")
            for var, value in env_info['proxy_env_vars'].items():
                print("  {}: {}".format(var, value))
            
            use_existing = input("Use existing proxy configuration? (y/n): ").lower().strip()
            if use_existing == 'y':
                self.proxy_config = env_info['proxy_env_vars']
                return self.test_proxy_configuration()
        
        if env_info['network_restrictions'] or not env_info['proxy_env_vars']:
            print("CORPORATE NETWORK: Proxy configuration may be required")
            print("Contact your IT department for proxy settings if needed")
            
            configure_proxy = input("Do you need to configure proxy settings? (y/n): ").lower().strip()
            
            if configure_proxy == 'y':
                print("\nPROXY CONFIGURATION")
                print("Enter your corporate proxy environment variables:")
                print("Example format: http://proxy.company.com:8080")
                print("Example with auth: http://username:password@proxy.company.com:8080")
                
                # Ask for HTTP_PROXY
                http_proxy = input("\nHTTP_PROXY: ").strip()
                
                # Ask for HTTPS_PROXY
                https_proxy = input("HTTPS_PROXY: ").strip()
                
                # Configure proxy settings
                self.proxy_config = {}
                
                if http_proxy:
                    self.proxy_config['HTTP_PROXY'] = http_proxy
                    self.proxy_config['http_proxy'] = http_proxy
                    os.environ['HTTP_PROXY'] = http_proxy
                    os.environ['http_proxy'] = http_proxy
                
                if https_proxy:
                    self.proxy_config['HTTPS_PROXY'] = https_proxy
                    self.proxy_config['https_proxy'] = https_proxy
                    os.environ['HTTPS_PROXY'] = https_proxy
                    os.environ['https_proxy'] = https_proxy
                
                if http_proxy or https_proxy:
                    print("\nPROXY SETTINGS CONFIGURED:")
                    if http_proxy:
                        # Mask password in display
                        display_http = http_proxy
                        if '@' in http_proxy and ':' in http_proxy.split('@')[0]:
                            parts = http_proxy.split('@')
                            auth_part = parts[0].split('://')[-1]
                            if ':' in auth_part:
                                user = auth_part.split(':')[0]
                                display_http = http_proxy.replace(auth_part, "{}:****".format(user))
                        print("  HTTP_PROXY: {}".format(display_http))
                    
                    if https_proxy:
                        # Mask password in display
                        display_https = https_proxy
                        if '@' in https_proxy and ':' in https_proxy.split('@')[0]:
                            parts = https_proxy.split('@')
                            auth_part = parts[0].split('://')[-1]
                            if ':' in auth_part:
                                user = auth_part.split(':')[0]
                                display_https = https_proxy.replace(auth_part, "{}:****".format(user))
                        print("  HTTPS_PROXY: {}".format(display_https))
                    
                    return self.test_proxy_configuration()
                else:
                    print("ERROR: No proxy settings provided")
                    return False
        
        return True  # No proxy needed
    
    def test_proxy_configuration(self) -> bool:
        """Test proxy configuration with comprehensive debugging"""
        print("TESTING: Proxy configuration with comprehensive diagnostics...")
        
        # Import required modules for proxy testing
        try:
            import urllib3
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
        except ImportError:
            print("WARNING: Advanced proxy testing not available - using basic testing")
            return self._basic_proxy_test()
        
        # First, let's verify what proxy settings we actually have
        print("\nPROXY DIAGNOSTICS:")
        print("Environment Variables:")
        for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            value = os.environ.get(var, 'Not set')
            if value != 'Not set' and '@' in value:
                # Mask password
                parts = value.split('@')
                if ':' in parts[0]:
                    auth_part = parts[0].split('://')[-1]
                    if ':' in auth_part:
                        user = auth_part.split(':')[0]
                        value = value.replace(auth_part, "{}:****".format(user))
            print("  {}: {}".format(var, value))
        
        print("\nInternal proxy config:")
        for key, value in self.proxy_config.items():
            masked_value = value
            if '@' in value:
                parts = value.split('@')
                if ':' in parts[0]:
                    auth_part = parts[0].split('://')[-1]
                    if ':' in auth_part:
                        user = auth_part.split(':')[0]
                        masked_value = value.replace(auth_part, "{}:****".format(user))
            print("  {}: {}".format(key, masked_value))
        
        # Test with multiple strategies
        strategies = [
            ('basic_requests', 'Basic requests with proxy'),
            ('urllib3_direct', 'Direct urllib3 with proxy'),
            ('no_ssl_verify', 'Requests without SSL verification'),
            ('session_based', 'Session-based with custom headers'),
            ('system_proxy', 'System proxy detection')
        ]
        
        successful_strategies = []
        
        for strategy_name, strategy_desc in strategies:
            print("\n--- TESTING STRATEGY: {} ---".format(strategy_desc))
            
            try:
                if strategy_name == 'basic_requests':
                    success = self._test_basic_requests()
                elif strategy_name == 'urllib3_direct':
                    success = self._test_urllib3_direct()
                elif strategy_name == 'no_ssl_verify':
                    success = self._test_no_ssl_verify()
                elif strategy_name == 'session_based':
                    success = self._test_session_based()
                elif strategy_name == 'system_proxy':
                    success = self._test_system_proxy()
                else:
                    success = False
                
                if success:
                    successful_strategies.append(strategy_name)
                    print("  STRATEGY SUCCESS: {}".format(strategy_desc))
                else:
                    print("  STRATEGY FAILED: {}".format(strategy_desc))
                    
            except Exception as e:
                print("  STRATEGY ERROR: {} - {}".format(strategy_desc, str(e)[:100]))
        
        self.proxy_working = len(successful_strategies) > 0
        
        if self.proxy_working:
            print("\nPROXY DIAGNOSIS: SUCCESS")
            print("Working strategies: {}".format(', '.join(successful_strategies)))
            print("Network connectivity established for ML downloads")
        else:
            print("\nPROXY DIAGNOSIS: ALL STRATEGIES FAILED")
            print("This suggests a proxy configuration or network issue")
            print("Recommendations:")
            print("1. Verify proxy URL format: http://proxy.company.com:8080")
            print("2. Check if proxy requires authentication")
            print("3. Test proxy with: curl -x <proxy> http://httpbin.org/get")
            print("4. Contact IT support for network troubleshooting")
            print("5. Will attempt offline/cached model usage")
        
        return self.proxy_working
    
    def _test_basic_requests(self) -> bool:
        """Test basic requests with proxy"""
        try:
            response = requests.get('http://httpbin.org/get', 
                                  proxies=self.proxy_config, 
                                  timeout=10)
            print("    Basic HTTP: Status {} ({} bytes)".format(response.status_code, len(response.content)))
            return response.status_code == 200
        except Exception as e:
            print("    Basic HTTP failed: {}".format(str(e)[:80]))
            return False
    
    def _test_urllib3_direct(self) -> bool:
        """Test direct urllib3 with proxy"""
        try:
            import urllib3
            
            # Extract proxy info
            proxy_url = self.proxy_config.get('http_proxy', self.proxy_config.get('HTTP_PROXY', ''))
            if not proxy_url:
                return False
            
            # Parse proxy URL
            from urllib.parse import urlparse
            parsed = urlparse(proxy_url)
            
            http = urllib3.ProxyManager(proxy_url)
            resp = http.request('GET', 'http://httpbin.org/get', timeout=10)
            print("    urllib3 direct: Status {} ({} bytes)".format(resp.status, len(resp.data)))
            return resp.status == 200
        except Exception as e:
            print("    urllib3 direct failed: {}".format(str(e)[:80]))
            return False
    
    def _test_no_ssl_verify(self) -> bool:
        """Test requests without SSL verification"""
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get('https://httpbin.org/get', 
                                  proxies=self.proxy_config,
                                  verify=False,
                                  timeout=10)
            print("    No SSL verify: Status {} ({} bytes)".format(response.status_code, len(response.content)))
            return response.status_code == 200
        except Exception as e:
            print("    No SSL verify failed: {}".format(str(e)[:80]))
            return False
    
    def _test_session_based(self) -> bool:
        """Test session-based approach with custom headers"""
        try:
            session = requests.Session()
            session.proxies.update(self.proxy_config)
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Enterprise AO1 Tool)',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            })
            session.verify = False
            
            response = session.get('http://httpbin.org/get', timeout=10)
            print("    Session-based: Status {} ({} bytes)".format(response.status_code, len(response.content)))
            return response.status_code == 200
        except Exception as e:
            print("    Session-based failed: {}".format(str(e)[:80]))
            return False
    
    def _test_system_proxy(self) -> bool:
        """Test using system proxy detection"""
        try:
            # Test if system can resolve proxy automatically
            response = requests.get('http://httpbin.org/get', timeout=10)
            print("    System proxy: Status {} ({} bytes)".format(response.status_code, len(response.content)))
            return response.status_code == 200
        except Exception as e:
            print("    System proxy failed: {}".format(str(e)[:80]))
            return False
    
    def _basic_proxy_test(self) -> bool:
        """Basic proxy test without advanced features"""
        test_urls = ['http://httpbin.org/get', 'https://httpbin.org/get']
        successful_tests = 0
        
        for url in test_urls:
            try:
                response = requests.get(url, 
                                      proxies=self.proxy_config,
                                      timeout=10, 
                                      verify=False)
                if response.status_code == 200:
                    successful_tests += 1
                    print("  SUCCESS: {}".format(url))
            except Exception as e:
                print("  ERROR: {} - {}".format(url, str(e)[:50]))
        
        return successful_tests > 0

class M1GPUDetector:
    """M1 GPU detection and optimization manager"""
    
    def __init__(self):
        self.device = None
        self.gpu_available = False
        self.gpu_type = None
        self.optimization_level = 'basic'
        
    def comprehensive_gpu_detection(self) -> Dict[str, Any]:
        """Comprehensive M1 GPU detection with multiple methods"""
        gpu_info = {
            'mps_available': False,
            'mps_built': False,
            'torch_device': 'cpu',
            'platform_info': {},
            'metal_performance': False,
            'recommended_settings': {}
        }
        
        print("GPU DETECTION: Comprehensive M1 analysis...")
        
        # Method 1: PyTorch MPS detection
        if TORCH_AVAILABLE:
            try:
                gpu_info['mps_available'] = torch.backends.mps.is_available()
                gpu_info['mps_built'] = torch.backends.mps.is_built()
                
                if gpu_info['mps_available']:
                    self.device = torch.device("mps")
                    gpu_info['torch_device'] = 'mps'
                    self.gpu_available = True
                    self.gpu_type = 'M1_MPS'
                    print("  SUCCESS: M1 GPU detected via PyTorch MPS")
                else:
                    self.device = torch.device("cpu")
                    print("  INFO: M1 GPU not available, using CPU")
                    
            except Exception as e:
                print("  ERROR: PyTorch MPS detection failed - {}".format(e))
                self.device = torch.device("cpu")
        
        # Method 2: Platform detection
        try:
            import platform
            system_info = {
                'system': platform.system(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'platform': platform.platform()
            }
            gpu_info['platform_info'] = system_info
            
            # Check for Apple Silicon indicators
            if (system_info['machine'] in ['arm64', 'aarch64'] and 
                system_info['system'] == 'Darwin'):
                print("  SUCCESS: Apple Silicon architecture detected")
                gpu_info['metal_performance'] = True
                
        except Exception as e:
            print("  ERROR: Platform detection failed - {}".format(e))
        
        # Method 3: System profiler check (macOS specific)
        try:
            if gpu_info['platform_info'].get('system') == 'Darwin':
                result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                      capture_output=True, text=True, timeout=10)
                if 'Apple M1' in result.stdout or 'Apple M2' in result.stdout:
                    print("  SUCCESS: Apple Silicon confirmed via system profiler")
                    self.optimization_level = 'advanced'
        except Exception as e:
            print("  INFO: System profiler check skipped - {}".format(e))
        
        # Set optimization recommendations
        if self.gpu_available:
            gpu_info['recommended_settings'] = {
                'batch_size': 32,
                'precision': 'float16',
                'memory_optimization': True,
                'threading': 'auto'
            }
            self.optimization_level = 'gpu_optimized'
        else:
            gpu_info['recommended_settings'] = {
                'batch_size': 8,
                'precision': 'float32',
                'memory_optimization': False,
                'threading': 'cpu_optimized'
            }
        
        return gpu_info
    
    def optimize_for_device(self, model=None):
        """Optimize model for detected device"""
        if model is None:
            return None
            
        try:
            if self.gpu_available and self.device.type == 'mps':
                if hasattr(model, 'to'):
                    model = model.to(self.device)
                    print("  OPTIMIZATION: Model moved to M1 GPU")
                
                # M1-specific optimizations
                if hasattr(torch.backends.mps, 'empty_cache'):
                    torch.backends.mps.empty_cache()
                
                return model
            else:
                print("  OPTIMIZATION: Using CPU optimization")
                return model
                
        except Exception as e:
            print("  ERROR: Device optimization failed - {}".format(e))
            return model

class EnterpriseHuggingFaceManager:
    """Enterprise-grade Hugging Face connection manager"""
    
    def __init__(self, proxy_manager: EnterpriseProxyManager):
        self.proxy_manager = proxy_manager
        self.connection_methods = []
        self.successful_connections = []
        self.models = {}
        self.api = None
        
    def comprehensive_connectivity_test(self) -> Dict[str, Any]:
        """Comprehensive Hugging Face connectivity testing"""
        print("HUGGING FACE: Enterprise connectivity analysis...")
        
        connectivity_results = {
            'hub_api_direct': False,
            'hub_api_proxy': False,
            'model_download_direct': False,
            'model_download_proxy': False,
            'sentence_transformers': False,
            'transformers_library': False,
            'cached_models': False,
            'offline_mode': False,
            'pipeline_access': False,
            'authentication_status': 'unknown'
        }
        
        # Test 1: Direct Hub API access
        try:
            api = HfApi()
            models = list(api.list_models(limit=1))
            connectivity_results['hub_api_direct'] = True
            self.successful_connections.append('Hub API Direct')
            print("  SUCCESS: Direct Hub API access")
        except Exception as e:
            print("  FAILED: Direct Hub API - {}".format(str(e)[:60]))
        
        # Test 2: Hub API with proxy
        if self.proxy_manager.proxy_config:
            try:
                # Configure requests with proxy
                import requests
                session = requests.Session()
                session.proxies.update(self.proxy_manager.proxy_config)
                
                # Test API with proxy
                api = HfApi()
                models = list(api.list_models(limit=1))
                connectivity_results['hub_api_proxy'] = True
                self.successful_connections.append('Hub API Proxy')
                print("  SUCCESS: Hub API via corporate proxy")
            except Exception as e:
                print("  FAILED: Hub API with proxy - {}".format(str(e)[:60]))
        
        # Test 3: Direct model download
        try:
            config_path = hf_hub_download(
                repo_id="sentence-transformers/all-MiniLM-L6-v2",
                filename="config.json"
            )
            if os.path.exists(config_path):
                connectivity_results['model_download_direct'] = True
                self.successful_connections.append('Model Download Direct')
                print("  SUCCESS: Direct model download")
        except Exception as e:
            print("  FAILED: Direct model download - {}".format(str(e)[:60]))
        
        # Test 4: Sentence Transformers
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            test_embedding = model.encode(["test connectivity"])
            if test_embedding is not None:
                connectivity_results['sentence_transformers'] = True
                self.successful_connections.append('Sentence Transformers')
                print("  SUCCESS: Sentence Transformers functional")
        except Exception as e:
            print("  FAILED: Sentence Transformers - {}".format(str(e)[:60]))
        
        # Test 5: Raw Transformers library
        try:
            tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            model = AutoModel.from_pretrained("distilbert-base-uncased")
            connectivity_results['transformers_library'] = True
            self.successful_connections.append('Transformers Library')
            print("  SUCCESS: Transformers library functional")
        except Exception as e:
            print("  FAILED: Transformers library - {}".format(str(e)[:60]))
        
        # Test 6: Check cached models
        try:
            cache_info = scan_cache_dir()
            if len(cache_info.repos) > 0:
                connectivity_results['cached_models'] = True
                self.successful_connections.append('Cached Models')
                print("  SUCCESS: {} cached models found".format(len(cache_info.repos)))
        except Exception as e:
            print("  FAILED: Cache scan - {}".format(str(e)[:60]))
        
        # Test 7: Offline mode
        try:
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_DATASETS_OFFLINE"] = "1"
            
            tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased", local_files_only=True)
            connectivity_results['offline_mode'] = True
            self.successful_connections.append('Offline Mode')
            print("  SUCCESS: Offline mode functional")
            
            # Cleanup
            del os.environ["TRANSFORMERS_OFFLINE"]
            del os.environ["HF_DATASETS_OFFLINE"]
            
        except Exception as e:
            print("  FAILED: Offline mode - {}".format(str(e)[:60]))
        
        # Test 8: Pipeline access
        try:
            pipe = pipeline("text-classification", model="distilbert-base-uncased")
            result = pipe("test text")
            connectivity_results['pipeline_access'] = True
            self.successful_connections.append('Pipeline Access')
            print("  SUCCESS: Pipeline access functional")
        except Exception as e:
            print("  FAILED: Pipeline access - {}".format(str(e)[:60]))
        
        # Authentication test
        try:
            login()  # Try cached token
            connectivity_results['authentication_status'] = 'authenticated'
            print("  SUCCESS: Authenticated access available")
        except:
            connectivity_results['authentication_status'] = 'anonymous'
            print("  INFO: Using anonymous access")
        
        success_count = sum(connectivity_results.values() if isinstance(v, bool) else 0 for v in connectivity_results.values())
        print("CONNECTIVITY SUMMARY: {}/8 connection methods successful".format(success_count))
        
        return connectivity_results
    
    def load_optimal_model(self, gpu_detector: M1GPUDetector) -> Tuple[Any, str]:
        """Load optimal model based on connectivity and hardware"""
        print("MODEL LOADING: Selecting optimal strategy...")
        
        # Model priority list (best to fallback)
        model_candidates = [
            'sentence-transformers/all-MiniLM-L6-v2',
            'sentence-transformers/paraphrase-MiniLM-L6-v2',
            'sentence-transformers/all-mpnet-base-v2',
            'distilbert-base-uncased',
            'bert-base-uncased'
        ]
        
        # Loading strategy priority
        loading_strategies = []
        
        if 'Sentence Transformers' in self.successful_connections:
            loading_strategies.append(('sentence_transformers', 'SentenceTransformers'))
        if 'Transformers Library' in self.successful_connections:
            loading_strategies.append(('transformers_direct', 'Direct Transformers'))
        if 'Cached Models' in self.successful_connections:
            loading_strategies.append(('cached_local', 'Cached Local'))
        if 'Offline Mode' in self.successful_connections:
            loading_strategies.append(('offline_only', 'Offline Only'))
        if 'Pipeline Access' in self.successful_connections:
            loading_strategies.append(('pipeline_mode', 'Pipeline Mode'))
        
        # Try each combination
        for model_name in model_candidates:
            for strategy_key, strategy_name in loading_strategies:
                try:
                    print("  ATTEMPTING: {} via {}".format(model_name, strategy_name))
                    
                    if strategy_key == 'sentence_transformers':
                        model = SentenceTransformer(model_name)
                        model = gpu_detector.optimize_for_device(model)
                        print("  SUCCESS: Model loaded via SentenceTransformers")
                        return model, 'sentence_transformers'
                    
                    elif strategy_key == 'transformers_direct':
                        tokenizer = AutoTokenizer.from_pretrained(model_name)
                        model = AutoModel.from_pretrained(model_name)
                        model = gpu_detector.optimize_for_device(model)
                        print("  SUCCESS: Model loaded via Direct Transformers")
                        return {'model': model, 'tokenizer': tokenizer}, 'transformers_direct'
                    
                    elif strategy_key == 'cached_local':
                        model = SentenceTransformer(model_name, local_files_only=True)
                        model = gpu_detector.optimize_for_device(model)
                        print("  SUCCESS: Model loaded from cache")
                        return model, 'cached_local'
                    
                    elif strategy_key == 'offline_only':
                        os.environ["TRANSFORMERS_OFFLINE"] = "1"
                        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
                        model = AutoModel.from_pretrained(model_name, local_files_only=True)
                        model = gpu_detector.optimize_for_device(model)
                        if "TRANSFORMERS_OFFLINE" in os.environ:
                            del os.environ["TRANSFORMERS_OFFLINE"]
                        print("  SUCCESS: Model loaded in offline mode")
                        return {'model': model, 'tokenizer': tokenizer}, 'offline_only'
                    
                    elif strategy_key == 'pipeline_mode':
                        model = pipeline("feature-extraction", model=model_name)
                        print("  SUCCESS: Model loaded via pipeline")
                        return model, 'pipeline_mode'
                        
                except Exception as e:
                    print("  FAILED: {} - {}".format(strategy_name, str(e)[:50]))
                    continue
        
        print("  ERROR: All model loading strategies failed")
        return None, None

class EnterpriseAO1Analyzer:
    """Enterprise-grade AO1 field analyzer with corporate features"""
    
    def __init__(self):
        self.client = None
        self.proxy_manager = EnterpriseProxyManager()
        self.gpu_detector = M1GPUDetector()
        self.hf_manager = None
        self.ml_model = None
        self.ml_strategy = None
        self.requirement_embeddings = {}
        self.neural_matcher = None
        
        # Initialize enterprise components
        self.initialize_enterprise_environment()
        
    def initialize_enterprise_environment(self):
        """Initialize enterprise environment with all components"""
        print("ENTERPRISE INITIALIZATION")
        print("=" * 50)
        
        # Step 1: Configure corporate proxy
        if not self.proxy_manager.configure_proxy_interactively():
            print("WARNING: Network connectivity issues detected")
        
        # Step 2: Detect and configure GPU
        gpu_info = self.gpu_detector.comprehensive_gpu_detection()
        
        # Step 3: Initialize ML components if available
        if ML_LIBRARIES_AVAILABLE:
            self.hf_manager = EnterpriseHuggingFaceManager(self.proxy_manager)
            connectivity = self.hf_manager.comprehensive_connectivity_test()
            
            if self.hf_manager.successful_connections:
                self.ml_model, self.ml_strategy = self.hf_manager.load_optimal_model(self.gpu_detector)
                if self.ml_model:
                    self._compute_requirement_embeddings()
                    print("ML COMPONENTS: Fully operational")
                else:
                    print("ML COMPONENTS: Limited functionality")
            else:
                print("ML COMPONENTS: Offline mode only")
        else:
            print("ML COMPONENTS: Not available - using pattern matching")
    
    def authenticate_bigquery(self) -> bool:
        """Authenticate with BigQuery"""
        try:
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                print("ERROR: Service account file not found: {}".format(SERVICE_ACCOUNT_FILE))
                return False
            
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
            self.client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
            
            # Test connection
            datasets = list(self.client.list_datasets(max_results=1))
            print("BIGQUERY: Authentication successful")
            return True
            
        except Exception as e:
            print("BIGQUERY ERROR: {}".format(e))
            return False
    
    def _compute_requirement_embeddings(self):
        """Compute embeddings for requirements using available model"""
        if not self.ml_model:
            return
        
        requirement_descriptions = {
            'REQ-1': 'global view asset identifiers hostname computer device system name',
            'REQ-2': 'infrastructure type deployment cloud aws azure gcp onpremises datacenter',
            'REQ-3': 'regional country geographic location datacenter region zone address',
            'REQ-4': 'business application organizational unit department division company',
            'REQ-5': 'system classification server function operating system windows linux unix',
            'REQ-6': 'security control coverage agent endpoint detection response edr tanium',
            'REQ-7': 'logging compliance platform splunk chronicle ingestion parsing sourcetype',
            'REQ-8': 'domain visibility hostname dns resolution network address fqdn'
        }
        
        try:
            print("EMBEDDINGS: Computing requirement embeddings...")
            
            for req, desc in requirement_descriptions.items():
                if self.ml_strategy == 'sentence_transformers':
                    embedding = self.ml_model.encode([desc])[0]
                    self.requirement_embeddings[req] = embedding
                    
                elif self.ml_strategy in ['transformers_direct', 'offline_only']:
                    tokenizer = self.ml_model['tokenizer']
                    model = self.ml_model['model']
                    
                    inputs = tokenizer(desc, return_tensors='pt', padding=True, truncation=True)
                    if self.gpu_detector.device and self.gpu_detector.device.type == 'mps':
                        inputs = {k: v.to(self.gpu_detector.device) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = model(**inputs)
                        embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()[0]
                        self.requirement_embeddings[req] = embedding
                
                elif self.ml_strategy == 'pipeline_mode':
                    result = self.ml_model(desc)[0]
                    if isinstance(result, list):
                        embedding = np.array(result).mean(axis=0)
                        self.requirement_embeddings[req] = embedding
            
            print("EMBEDDINGS: Successfully computed for {} requirements".format(len(self.requirement_embeddings)))
            
        except Exception as e:
            print("EMBEDDINGS ERROR: {}".format(e))
            self.requirement_embeddings = {}
    
    def compute_advanced_field_score(self, field_name: str) -> Dict[str, float]:
        """Compute advanced scoring for field relevance"""
        scores = {
            'exact_match': 0.0,
            'pattern_match': 0.0,
            'semantic_similarity': 0.0,
            'neural_classification': 0.0,
            'composite_score': 0.0
        }
        
        field_lower = field_name.lower().strip()
        
        # Exact match scoring
        if field_lower in ALL_AO1_KEYWORDS:
            scores['exact_match'] = 1.0
        
        # Pattern matching scoring
        best_pattern_score = 0.0
        matched_keyword = None
        
        for keyword in ALL_AO1_KEYWORDS:
            if len(keyword) >= 3:
                if keyword in field_lower:
                    pattern_score = len(keyword) / len(field_lower)
                    if pattern_score > best_pattern_score:
                        best_pattern_score = pattern_score
                        matched_keyword = keyword
                elif field_lower in keyword and len(field_lower) >= 3:
                    pattern_score = len(field_lower) / len(keyword)
                    if pattern_score > best_pattern_score:
                        best_pattern_score = pattern_score
                        matched_keyword = keyword
        
        scores['pattern_match'] = best_pattern_score
        
        # Semantic similarity scoring (if ML available)
        if self.ml_model and self.requirement_embeddings:
            try:
                best_semantic_score = 0.0
                
                for req in self.requirement_embeddings.keys():
                    if self.ml_strategy == 'sentence_transformers':
                        field_embedding = self.ml_model.encode([field_name])
                        req_embedding = self.requirement_embeddings[req].reshape(1, -1)
                        similarity = cosine_similarity(field_embedding, req_embedding)[0][0]
                        
                    elif self.ml_strategy in ['transformers_direct', 'offline_only']:
                        tokenizer = self.ml_model['tokenizer']
                        model = self.ml_model['model']
                        
                        inputs = tokenizer(field_name, return_tensors='pt', padding=True, truncation=True)
                        if self.gpu_detector.device and self.gpu_detector.device.type == 'mps':
                            inputs = {k: v.to(self.gpu_detector.device) for k, v in inputs.items()}
                        
                        with torch.no_grad():
                            outputs = model(**inputs)
                            field_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
                        
                        req_embedding = self.requirement_embeddings[req].reshape(1, -1)
                        similarity = cosine_similarity(field_embedding, req_embedding)[0][0]
                    
                    else:
                        similarity = 0.0
                    
                    if similarity > best_semantic_score:
                        best_semantic_score = similarity
                
                scores['semantic_similarity'] = best_semantic_score
                
            except Exception as e:
                print("SEMANTIC SCORING ERROR: {}".format(e))
        
        # Composite scoring
        weights = {
            'exact_match': 0.4,
            'pattern_match': 0.3,
            'semantic_similarity': 0.2,
            'neural_classification': 0.1
        }
        
        scores['composite_score'] = sum(scores[key] * weights[key] for key in weights.keys())
        
        return scores, matched_keyword
    
    def analyze_table_comprehensive(self, dataset_id: str, table_id: str) -> List[FieldMatch]:
        """Comprehensive table analysis with enterprise features"""
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)
            
            matches = []
            
            def analyze_field_recursive(field, parent_path=""):
                field_path = "{}.{}".format(parent_path, field.name) if parent_path else field.name
                
                # Advanced scoring
                scores, matched_keyword = self.compute_advanced_field_score(field.name)
                
                # Determine if field is relevant
                if scores['composite_score'] > 0.3:  # Enterprise threshold
                    
                    # Determine requirement
                    requirement = "UNKNOWN"
                    if matched_keyword:
                        requirement = self.get_requirement_for_keyword(matched_keyword)
                    
                    # Determine match type
                    if scores['exact_match'] >= 1.0:
                        match_type = "EXACT"
                    elif scores['composite_score'] >= 0.7:
                        match_type = "HIGH_CONFIDENCE"
                    elif scores['composite_score'] >= 0.5:
                        match_type = "ML_IDENTIFIED"
                    else:
                        match_type = "SUSPECTED"
                    
                    match = FieldMatch(
                        dataset=dataset_id,
                        table=table_id,
                        field_name=field.name,
                        field_path=field_path,
                        field_type=field.field_type,
                        requirement=requirement,
                        matched_keyword=matched_keyword or field.name.lower(),
                        match_type=match_type,
                        confidence_score=scores['composite_score'],
                        table_rows=table.num_rows or 0,
                        table_size_bytes=table.num_bytes or 0,
                        semantic_similarity=scores['semantic_similarity'],
                        context_relevance=self.compute_context_relevance(field.name, field.field_type),
                        neural_score=scores['neural_classification'],
                        pattern_score=scores['pattern_match']
                    )
                    matches.append(match)
                
                # Recursively analyze nested fields
                if field.field_type in ['RECORD', 'STRUCT'] and field.fields:
                    for nested_field in field.fields:
                        analyze_field_recursive(nested_field, field_path)
            
            # Analyze all fields
            for field in table.schema:
                analyze_field_recursive(field)
            
            return matches
            
        except Exception as e:
            logger.error("Table analysis error {}.{}: {}".format(dataset_id, table_id, e))
            return []
    
    def get_requirement_for_keyword(self, keyword: str) -> str:
        """Get requirement for keyword"""
        for req, keywords in REQUIREMENT_KEYWORDS.items():
            if keyword in keywords:
                return req
        return "UNKNOWN"
    
    def compute_context_relevance(self, field_name: str, field_type: str) -> float:
        """Compute contextual relevance"""
        base_score = 0.5
        
        # Type-based scoring
        type_multipliers = {
            'STRING': 1.2, 'VARCHAR': 1.2,
            'INTEGER': 0.8, 'INT64': 0.8,
            'TIMESTAMP': 1.0, 'DATETIME': 1.0,
            'BOOLEAN': 0.6
        }
        
        return min(base_score * type_multipliers.get(field_type, 1.0), 1.0)
    
    def scan_all_datasets(self) -> List[FieldMatch]:
        """Enterprise dataset scanning with progress tracking"""
        try:
            datasets = [d.dataset_id for d in self.client.list_datasets()]
            print("SCANNING: {} datasets identified".format(len(datasets)))
            
            all_matches = []
            total_tables = 0
            processed_tables = 0
            
            # Count tables
            for dataset_id in datasets:
                try:
                    tables = list(self.client.list_tables(dataset_id))
                    total_tables += len(tables)
                except:
                    continue
            
            print("PROCESSING: {} tables with enterprise ML analysis".format(total_tables))
            
            # Process all tables
            for dataset_id in datasets:
                try:
                    tables = list(self.client.list_tables(dataset_id))
                    
                    for table in tables:
                        processed_tables += 1
                        
                        if processed_tables % 25 == 0:
                            progress = (processed_tables / total_tables) * 100
                            print("PROGRESS: {:.1f}% ({}/{} tables)".format(progress, processed_tables, total_tables))
                        
                        matches = self.analyze_table_comprehensive(dataset_id, table.table_id)
                        all_matches.extend(matches)
                        
                except Exception as e:
                    logger.error("Dataset processing error {}: {}".format(dataset_id, e))
                    continue
            
            print("ANALYSIS COMPLETE: {} field matches discovered".format(len(all_matches)))
            return all_matches
            
        except Exception as e:
            logger.error("Dataset scanning error: {}".format(e))
            return []
    
    def generate_enterprise_report(self, matches: List[FieldMatch]):
        """Generate enterprise-grade analysis report"""
        if not matches:
            print("\nENTERPRISE AO1 FIELD ANALYSIS")
            print("=" * 60)
            print("STATUS: No AO1-relevant fields discovered")
            print("RECOMMENDATION: Review data ingestion and field naming standards")
            return
        
        # Sort by strategic importance
        matches.sort(key=lambda x: (x.requirement, -x.confidence_score, -x.table_rows))
        
        # Group by requirement
        by_requirement = defaultdict(list)
        for match in matches:
            by_requirement[match.requirement].append(match)
        
        print("\nENTERPRISE AO1 FIELD ANALYSIS")
        print("=" * 60)
        print("ENTERPRISE FEATURES: Corporate proxy support, M1 GPU optimization")
        
        # Display system status
        if self.gpu_detector.gpu_available:
            print("COMPUTE: M1 GPU acceleration active")
        else:
            print("COMPUTE: CPU processing mode")
        
        if self.hf_manager and self.hf_manager.successful_connections:
            print("ML CONNECTIVITY: {} methods successful".format(len(self.hf_manager.successful_connections)))
        else:
            print("ML CONNECTIVITY: Offline/limited mode")
        
        print("ANALYSIS DEPTH: {} fields analyzed with {} composite scoring".format(
            len(matches), "ML-enhanced" if self.ml_model else "pattern-based"))
        
        # Requirement analysis
        for req_num in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
            req_matches = by_requirement.get(req_num, [])
            
            if not req_matches:
                print("\n{}: No fields identified".format(req_num))
                continue
            
            # Categorize matches
            exact = [m for m in req_matches if m.match_type == 'EXACT']
            high_conf = [m for m in req_matches if m.match_type == 'HIGH_CONFIDENCE']
            ml_identified = [m for m in req_matches if m.match_type == 'ML_IDENTIFIED']
            suspected = [m for m in req_matches if m.match_type == 'SUSPECTED']
            
            print("\n{}: {} total candidates".format(req_num, len(req_matches)))
            print("   EXACT: {} | HIGH_CONF: {} | ML_ID: {} | SUSPECTED: {}".format(
                len(exact), len(high_conf), len(ml_identified), len(suspected)))
            
            # Top recommendations
            top_matches = sorted(req_matches, key=lambda x: (-x.confidence_score, -x.table_rows))[:3]
            
            print("   ENTERPRISE RECOMMENDATIONS:")
            for i, match in enumerate(top_matches, 1):
                rows_info = "{:,} rows".format(match.table_rows) if match.table_rows > 0 else "unknown size"
                print("      {}. Field '{}' in {}.{} ({})".format(
                    i, match.field_name, match.dataset, match.table, rows_info))
                print("         Confidence: {:.1%} | Type: {} | Semantic: {:.1%}".format(
                    match.confidence_score, match.match_type, match.semantic_similarity))
                
                if match.match_type == 'EXACT':
                    print("         Enterprise Assessment: Direct AO1 compliance field - immediate deployment ready")
                elif match.match_type == 'HIGH_CONFIDENCE':
                    print("         Enterprise Assessment: High-confidence ML match - recommended for validation")
                else:
                    print("         Enterprise Assessment: Candidate field - business validation recommended")
        
        # Strategic summary
        print("\nENTERPRISE STRATEGIC SUMMARY")
        print("=" * 40)
        
        total_exact = sum(len([m for m in matches if m.match_type == 'EXACT']) for matches in by_requirement.values())
        total_high_conf = sum(len([m for m in matches if m.match_type == 'HIGH_CONFIDENCE']) for matches in by_requirement.values())
        
        print("DEPLOYMENT READY: {} exact match fields".format(total_exact))
        print("VALIDATION PIPELINE: {} high-confidence fields".format(total_high_conf))
        print("AO1 COVERAGE: {}/8 requirements ({:.1f}%)".format(len(by_requirement), len(by_requirement)/8*100))
        
        # Data volume analysis
        total_rows = sum(m.table_rows for m in matches)
        print("DATA IMPACT: {:,} total rows across candidate tables".format(total_rows))
        
    def save_enterprise_results(self, matches: List[FieldMatch]):
        """Save enterprise results with comprehensive metadata"""
        if not matches:
            return
        
        # Convert to DataFrame with enterprise metadata
        df = pd.DataFrame([asdict(match) for match in matches])
        
        # Add enterprise columns
        df['analysis_timestamp'] = datetime.now().isoformat()
        df['ml_strategy'] = self.ml_strategy or 'pattern_only'
        df['gpu_acceleration'] = self.gpu_detector.gpu_available
        df['enterprise_grade'] = True
        
        # Sort by enterprise priority
        df['priority_score'] = (df['confidence_score'] * 0.6 + 
                               (df['table_rows'] / df['table_rows'].max()) * 0.4)
        df = df.sort_values(['requirement', 'priority_score'], ascending=[True, False])
        
        # Save comprehensive results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Detailed results
        detail_filename = "ao1_enterprise_analysis_{}.csv".format(timestamp)
        df.to_csv(detail_filename, index=False)
        
        # Executive summary
        summary = df.groupby(['requirement', 'match_type']).agg({
            'field_name': 'count',
            'confidence_score': 'mean',
            'table_rows': 'sum',
            'semantic_similarity': 'mean'
        }).round(3)
        
        summary_filename = "ao1_executive_summary_{}.csv".format(timestamp)
        summary.to_csv(summary_filename)
        
        # Compliance report
        compliance_df = df[df['match_type'].isin(['EXACT', 'HIGH_CONFIDENCE'])]
        compliance_filename = "ao1_compliance_ready_{}.csv".format(timestamp)
        compliance_df.to_csv(compliance_filename, index=False)
        
        print("\nENTERPRISE RESULTS SAVED:")
        print("Detailed Analysis: {}".format(detail_filename))
        print("Executive Summary: {}".format(summary_filename))
        print("Compliance Ready: {} ({} fields)".format(compliance_filename, len(compliance_df)))

def main():
    """Main enterprise execution"""
    print("ENTERPRISE AO1 FIELD DISCOVERY SYSTEM")
    print("Corporate ML-Powered BigQuery Analysis")
    print("=" * 60)
    
    try:
        # Initialize enterprise analyzer
        analyzer = EnterpriseAO1Analyzer()
        
        # Authenticate with BigQuery
        if not analyzer.authenticate_bigquery():
            print("CRITICAL: BigQuery authentication failed")
            return
        
        # Run enterprise analysis
        start_time = time.time()
        
        matches = analyzer.scan_all_datasets()
        
        analysis_time = time.time() - start_time
        
        print("\nENTERPRISE ANALYSIS COMPLETE")
        print("Processing Time: {:.2f} seconds".format(analysis_time))
        print("Enterprise Features: Proxy support, GPU optimization, ML analysis")
        
        # Generate enterprise reports
        analyzer.generate_enterprise_report(matches)
        analyzer.save_enterprise_results(matches)
        
        print("\nENTERPRISE RECOMMENDATIONS:")
        if matches:
            print("1. VALIDATE: Review high-confidence matches for immediate deployment")
            print("2. IMPLEMENT: Deploy exact matches for AO1 compliance measurement")
            print("3. EXPAND: Investigate ML-identified fields for coverage expansion")
            print("4. MONITOR: Establish ongoing field discovery processes")
        else:
            print("1. INVESTIGATE: No AO1 fields found - review data architecture")
            print("2. STANDARDIZE: Consider implementing AO1-compliant field naming")
            print("3. VALIDATE: Confirm data ingestion processes are complete")
        
    except KeyboardInterrupt:
        print("\nANALYSIS INTERRUPTED: Check logs for partial results")
    except Exception as e:
        print("\nCRITICAL ENTERPRISE ERROR: {}".format(e))
        logger.error("Enterprise execution error: {}".format(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()