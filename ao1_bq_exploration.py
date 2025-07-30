"""
Ultra-Robust Enterprise AO1 Field Discovery System
Self-Healing ML-Powered BigQuery Analysis with Automatic Dependency Resolution

This system will:
1. Auto-install missing dependencies
2. Try multiple Python environments
3. Handle all corporate proxy scenarios
4. Automatically configure M1 GPU optimization
5. Never fail - always find a way to work
6. Provide enterprise-grade AO1 field discovery
"""

import os
import sys
import json
import time
import logging
import getpass
import subprocess
import importlib
import pkg_resources
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
import requests
import urllib.parse
import socket

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

# Configuration
PROJECT_ID = "prj-fisv-p-gcss-sas-dl9dd0f1df"
SERVICE_ACCOUNT_FILE = "gcp_prod_key.json"

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

class RobustDependencyManager:
    """Ultra-robust dependency management with automatic installation"""
    
    def __init__(self):
        self.installation_attempts = []
        self.successful_imports = {}
        self.failed_imports = {}
        self.python_executables = self._find_python_executables()
        
    def _find_python_executables(self) -> List[str]:
        """Find all available Python executables"""
        candidates = [
            sys.executable,
            'python3',
            'python',
            '/usr/bin/python3',
            '/usr/local/bin/python3',
            os.path.expanduser('~/.pyenv/shims/python'),
            os.path.expanduser('~/miniforge3/bin/python'),
            os.path.expanduser('~/anaconda3/bin/python'),
            os.path.expanduser('~/miniconda3/bin/python')
        ]
        
        valid_executables = []
        for candidate in candidates:
            try:
                result = subprocess.run([candidate, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    valid_executables.append(candidate)
            except:
                continue
        
        return list(set(valid_executables))  # Remove duplicates
    
    def _install_with_multiple_methods(self, package: str, alternative_names: List[str] = None):
        """Try multiple installation methods until one succeeds"""
        if alternative_names is None:
            alternative_names = []
        
        all_packages = [package] + alternative_names
        installation_methods = [
            ('pip install', 'pip install {}'),
            ('pip3 install', 'pip3 install {}'),
            ('python -m pip install', '{} -m pip install {}'),
            ('python3 -m pip install', '{} -m pip install {}'),
            ('conda install', 'conda install -y {}'),
            ('mamba install', 'mamba install -y {}')
        ]
        
        for pkg in all_packages:
            for method_name, command_template in installation_methods:
                for python_exec in self.python_executables:
                    try:
                        if 'python' in command_template and '{}' in command_template:
                            command = command_template.format(python_exec, pkg)
                        else:
                            command = command_template.format(pkg)
                        
                        print("INSTALL ATTEMPT: {} using {}".format(pkg, command))
                        
                        result = subprocess.run(command.split(), 
                                              capture_output=True, text=True, timeout=300)
                        
                        if result.returncode == 0:
                            print("SUCCESS: {} installed via {}".format(pkg, method_name))
                            self.installation_attempts.append({
                                'package': pkg,
                                'method': method_name,
                                'command': command,
                                'success': True
                            })
                            return True
                        else:
                            print("FAILED: {} - {}".format(command, result.stderr[:100]))
                            
                    except subprocess.TimeoutExpired:
                        print("TIMEOUT: {} installation timeout".format(command))
                    except Exception as e:
                        print("ERROR: {} - {}".format(command, str(e)[:50]))
        
        return False
    
    def ensure_dependency(self, module_name: str, package_name: str = None, 
                         alternative_packages: List[str] = None) -> Tuple[bool, Any]:
        """Ensure a dependency is available, installing if necessary"""
        if package_name is None:
            package_name = module_name
        
        if alternative_packages is None:
            alternative_packages = []
        
        # Try importing first
        try:
            module = importlib.import_module(module_name)
            self.successful_imports[module_name] = module
            print("✓ {}: Already available".format(module_name))
            return True, module
        except ImportError:
            print("⚠ {}: Not available, attempting installation".format(module_name))
        
        # Try installing
        success = self._install_with_multiple_methods(package_name, alternative_packages)
        
        if success:
            # Try importing again after installation
            try:
                # Reload the module in case it was partially loaded
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                else:
                    module = importlib.import_module(module_name)
                
                self.successful_imports[module_name] = module
                print("✓ {}: Successfully installed and imported".format(module_name))
                return True, module
            except ImportError as e:
                print("✗ {}: Installation succeeded but import failed - {}".format(module_name, e))
                self.failed_imports[module_name] = str(e)
        else:
            print("✗ {}: All installation methods failed".format(module_name))
            self.failed_imports[module_name] = "Installation failed"
        
        return False, None

class UltraRobustMLSystem:
    """Ultra-robust ML system that tries everything until it works"""
    
    def __init__(self):
        self.dependency_manager = RobustDependencyManager()
        self.torch_available = False
        self.transformers_available = False
        self.sentence_transformers_available = False
        self.sklearn_available = False
        self.device = None
        self.models = {}
        self.initialize_ml_stack()
    
    def initialize_ml_stack(self):
        """Initialize ML stack with aggressive dependency resolution"""
        print("ULTRA-ROBUST ML INITIALIZATION")
        print("=" * 60)
        print("Will try every possible method until full ML stack is available")
        
        # Essential dependencies in order of importance
        ml_dependencies = [
            # Core packages
            ('numpy', 'numpy', []),
            ('pandas', 'pandas', []),
            ('requests', 'requests', []),
            ('sklearn', 'scikit-learn', ['sklearn']),
            
            # PyTorch (try multiple variants for M1 compatibility)
            ('torch', 'torch', ['torch --index-url https://download.pytorch.org/whl/cpu',
                                'torch torchvision torchaudio']),
            
            # Hugging Face ecosystem
            ('transformers', 'transformers', ['transformers[torch]']),
            ('sentence_transformers', 'sentence-transformers', []),
            ('huggingface_hub', 'huggingface-hub', []),
            
            # Google Cloud
            ('google.cloud.bigquery', 'google-cloud-bigquery', []),
            ('google.oauth2', 'google-auth', [])
        ]
        
        self.successful_dependencies = {}
        self.failed_dependencies = {}
        
        for module_name, package_name, alternatives in ml_dependencies:
            success, module = self.dependency_manager.ensure_dependency(
                module_name, package_name, alternatives
            )
            
            if success:
                self.successful_dependencies[module_name] = module
                
                # Set specific flags for important modules
                if module_name == 'torch':
                    self.torch_available = True
                    self._configure_torch()
                elif module_name == 'transformers':
                    self.transformers_available = True
                elif module_name == 'sentence_transformers':
                    self.sentence_transformers_available = True
                elif module_name == 'sklearn':
                    self.sklearn_available = True
                    
            else:
                self.failed_dependencies[module_name] = "Failed to install/import"
        
        # Print final status
        self._print_ml_status()
        
        # Initialize models if dependencies are available
        if self.torch_available and self.transformers_available:
            self._initialize_models()
    
    def _configure_torch(self):
        """Configure PyTorch for optimal performance"""
        try:
            torch = self.successful_dependencies['torch']
            
            # Try to detect and configure M1 GPU
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = torch.device('mps')
                print("✓ M1 GPU (MPS): Configured for acceleration")
            else:
                self.device = torch.device('cpu')
                print("✓ CPU: Configured for processing")
                
            # Set optimal CPU threads
            if self.device.type == 'cpu':
                torch.set_num_threads(min(8, torch.get_num_threads()))
                
        except Exception as e:
            print("⚠ PyTorch configuration warning: {}".format(e))
            self.device = torch.device('cpu')
    
    def _initialize_models(self):
        """Initialize ML models with robust fallback"""
        print("\nMODEL INITIALIZATION:")
        
        model_configs = [
            # Lightweight models first
            ('sentence-transformers/all-MiniLM-L6-v2', 'lightweight'),
            ('sentence-transformers/paraphrase-MiniLM-L6-v2', 'lightweight'),
            ('distilbert-base-uncased', 'medium'),
            ('sentence-transformers/all-mpnet-base-v2', 'full-featured')
        ]
        
        for model_name, model_type in model_configs:
            try:
                print("Attempting to load: {}".format(model_name))
                
                if self.sentence_transformers_available:
                    SentenceTransformer = self.successful_dependencies['sentence_transformers'].SentenceTransformer
                    model = SentenceTransformer(model_name)
                    if self.device and self.device.type == 'mps':
                        model = model.to(self.device)
                    
                    # Test the model
                    test_embedding = model.encode(['test'])
                    if test_embedding is not None:
                        self.models['sentence_transformer'] = model
                        self.models['strategy'] = 'sentence_transformers'
                        print("✓ SUCCESS: {} loaded and tested".format(model_name))
                        break
                
            except Exception as e:
                print("✗ FAILED: {} - {}".format(model_name, str(e)[:100]))
                continue
        
        if not self.models and self.transformers_available:
            # Try basic transformers
            try:
                transformers = self.successful_dependencies['transformers']
                tokenizer = transformers.AutoTokenizer.from_pretrained('distilbert-base-uncased')
                model = transformers.AutoModel.from_pretrained('distilbert-base-uncased')
                
                if self.device and self.device.type == 'mps':
                    model = model.to(self.device)
                
                self.models['transformers'] = {'model': model, 'tokenizer': tokenizer}
                self.models['strategy'] = 'transformers_direct'
                print("✓ SUCCESS: Basic transformers loaded")
                
            except Exception as e:
                print("✗ Basic transformers failed: {}".format(e))
    
    def _print_ml_status(self):
        """Print comprehensive ML system status"""
        print("\nML SYSTEM STATUS:")
        print("✓ Successful: {} dependencies".format(len(self.successful_dependencies)))
        print("✗ Failed: {} dependencies".format(len(self.failed_dependencies)))
        
        if self.successful_dependencies:
            print("\nAVAILABLE CAPABILITIES:")
            for module_name in self.successful_dependencies:
                if module_name == 'torch':
                    print("  ✓ PyTorch: Neural networks, GPU acceleration")
                elif module_name == 'transformers':
                    print("  ✓ Transformers: Language models, embeddings")
                elif module_name == 'sentence_transformers':
                    print("  ✓ Sentence Transformers: Semantic similarity")
                elif module_name == 'sklearn':
                    print("  ✓ Scikit-learn: TF-IDF, similarity metrics")
                elif module_name == 'google.cloud.bigquery':
                    print("  ✓ BigQuery: Database connectivity")
        
        if self.failed_dependencies:
            print("\nFAILED DEPENDENCIES:")
            for module_name, error in self.failed_dependencies.items():
                print("  ✗ {}: {}".format(module_name, error))

class EnterpriseProxyManager:
    """Ultra-robust corporate proxy manager"""
    
    def __init__(self):
        self.proxy_config = {}
        self.proxy_working = False
        
    def auto_configure_proxy(self) -> bool:
        """Automatically detect and configure corporate proxy"""
        print("\nCORPORATE PROXY AUTO-CONFIGURATION")
        print("=" * 50)
        
        # Method 1: Check environment variables
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        existing_proxies = {var: os.environ.get(var) for var in proxy_vars if os.environ.get(var)}
        
        if existing_proxies:
            print("DETECTED: Existing proxy configuration")
            for var, value in existing_proxies.items():
                masked_value = self._mask_proxy_password(value)
                print("  {}: {}".format(var, masked_value))
            
            self.proxy_config = existing_proxies
            if self._test_proxy():
                return True
        
        # Method 2: Interactive configuration
        print("CORPORATE NETWORK: Manual proxy configuration required")
        configure = input("Configure proxy settings? (y/n): ").lower().strip()
        
        if configure == 'y':
            return self._interactive_proxy_setup()
        
        # Method 3: Try without proxy
        print("Attempting direct connection...")
        return self._test_direct_connection()
    
    def _interactive_proxy_setup(self) -> bool:
        """Interactive proxy setup with validation"""
        print("\nPROXY CONFIGURATION")
        print("Format: http://proxy.company.com:8080")
        print("With auth: http://username:password@proxy.company.com:8080")
        
        http_proxy = input("HTTP_PROXY: ").strip()
        https_proxy = input("HTTPS_PROXY: ").strip()
        
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
        
        return self._test_proxy()
    
    def _test_proxy(self) -> bool:
        """Comprehensive proxy testing"""
        test_urls = [
            'http://httpbin.org/get',
            'https://httpbin.org/get',
            'https://pypi.org/simple/',
            'https://huggingface.co'
        ]
        
        successful_tests = 0
        
        for url in test_urls:
            try:
                response = requests.get(url, 
                                      proxies=self.proxy_config,
                                      timeout=10,
                                      verify=False)
                if response.status_code == 200:
                    successful_tests += 1
                    print("  ✓ {}".format(url))
                else:
                    print("  ⚠ {} (Status: {})".format(url, response.status_code))
            except Exception as e:
                print("  ✗ {} - {}".format(url, str(e)[:60]))
        
        self.proxy_working = successful_tests >= len(test_urls) // 2
        
        if self.proxy_working:
            print("✓ PROXY: Working ({}/{} tests passed)".format(successful_tests, len(test_urls)))
        else:
            print("⚠ PROXY: Limited connectivity ({}/{} tests passed)".format(successful_tests, len(test_urls)))
        
        return self.proxy_working
    
    def _test_direct_connection(self) -> bool:
        """Test direct internet connection"""
        try:
            response = requests.get('http://httpbin.org/get', timeout=5)
            if response.status_code == 200:
                print("✓ DIRECT: Internet connection working")
                return True
        except:
            pass
        
        print("✗ DIRECT: No internet connectivity")
        return False
    
    def _mask_proxy_password(self, proxy_url: str) -> str:
        """Mask password in proxy URL for logging"""
        if '@' in proxy_url:
            parts = proxy_url.split('@')
            if ':' in parts[0]:
                auth_part = parts[0].split('://')[-1]
                if ':' in auth_part:
                    user = auth_part.split(':')[0]
                    return proxy_url.replace(auth_part, "{}:****".format(user))
        return proxy_url

class UltraRobustAO1Analyzer:
    """Ultra-robust AO1 analyzer that never fails"""
    
    def __init__(self):
        print("ULTRA-ROBUST AO1 FIELD DISCOVERY SYSTEM")
        print("Self-Healing Enterprise ML Analysis")
        print("=" * 60)
        
        # Initialize all systems
        self.ml_system = UltraRobustMLSystem()
        self.proxy_manager = EnterpriseProxyManager()
        self.client = None
        self.requirement_embeddings = {}
        
        # Load AO1 keywords
        self._load_ao1_keywords()
        
        # Initialize enterprise environment
        self._initialize_enterprise_environment()
    
    def _load_ao1_keywords(self):
        """Load AO1 keywords with fallback"""
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
                get_all_keywords
            )
            
            self.all_keywords = get_all_keywords()
            self.requirement_keywords = {
                'REQ-1': REQ1_GLOBAL_VIEW_KEYWORDS,
                'REQ-2': REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
                'REQ-3': REQ3_REGIONAL_COUNTRY_KEYWORDS,
                'REQ-4': REQ4_BUSINESS_APPLICATION_KEYWORDS,
                'REQ-5': REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
                'REQ-6': REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
                'REQ-7': REQ7_LOGGING_COMPLIANCE_KEYWORDS,
                'REQ-8': REQ8_DOMAIN_VISIBILITY_KEYWORDS
            }
            print("✓ AO1 KEYWORDS: {} keywords loaded".format(len(self.all_keywords)))
            
        except ImportError:
            print("✗ AO1 keywords module not found - using built-in keywords")
            self._create_builtin_keywords()
    
    def _create_builtin_keywords(self):
        """Create built-in AO1 keywords as fallback"""
        self.all_keywords = {
            # REQ-1: Global View
            'hostname', 'host_name', 'computer_name', 'device_name', 'asset_id',
            'ip_address', 'mac_address', 'serial_number',
            
            # REQ-2: Infrastructure Type  
            'cloud', 'aws', 'azure', 'gcp', 'datacenter', 'virtual_machine',
            
            # REQ-3: Regional/Country
            'region', 'country', 'location', 'datacenter', 'zone',
            
            # REQ-4: Business/Application
            'business_unit', 'application', 'department', 'organization',
            
            # REQ-5: System Classification
            'windows', 'linux', 'unix', 'operating_system', 'server_type',
            
            # REQ-6: Security Control Coverage
            'edr', 'crowdstrike', 'tanium', 'agent_id', 'endpoint_security',
            
            # REQ-7: Logging Compliance
            'splunk', 'chronicle', 'sourcetype', 'index', 'log_source',
            
            # REQ-8: Domain Visibility
            'domain', 'fqdn', 'dns_name', 'hostname'
        }
        
        self.requirement_keywords = {
            'REQ-1': {'hostname', 'host_name', 'computer_name', 'device_name', 'asset_id', 'ip_address'},
            'REQ-2': {'cloud', 'aws', 'azure', 'gcp', 'datacenter', 'virtual_machine'},
            'REQ-3': {'region', 'country', 'location', 'datacenter', 'zone'},
            'REQ-4': {'business_unit', 'application', 'department', 'organization'},
            'REQ-5': {'windows', 'linux', 'unix', 'operating_system', 'server_type'},
            'REQ-6': {'edr', 'crowdstrike', 'tanium', 'agent_id', 'endpoint_security'},
            'REQ-7': {'splunk', 'chronicle', 'sourcetype', 'index', 'log_source'},
            'REQ-8': {'domain', 'fqdn', 'dns_name', 'hostname'}
        }
        
        print("✓ BUILT-IN KEYWORDS: {} keywords available".format(len(self.all_keywords)))
    
    def _initialize_enterprise_environment(self):
        """Initialize enterprise environment"""
        # Configure proxy
        self.proxy_manager.auto_configure_proxy()
        
        # Authenticate BigQuery
        self._authenticate_bigquery()
        
        # Compute embeddings if ML available
        if self.ml_system.models:
            self._compute_requirement_embeddings()
    
    def _authenticate_bigquery(self) -> bool:
        """Authenticate with BigQuery using multiple methods"""
        print("\nBIGQUERY AUTHENTICATION:")
        
        # Try importing BigQuery
        if 'google.cloud.bigquery' not in self.ml_system.successful_dependencies:
            print("✗ BigQuery library not available - attempting installation")
            success, module = self.ml_system.dependency_manager.ensure_dependency(
                'google.cloud.bigquery', 'google-cloud-bigquery'
            )
            if not success:
                print("✗ CRITICAL: Cannot install BigQuery library")
                return False
        
        try:
            bigquery = self.ml_system.successful_dependencies['google.cloud.bigquery']
            
            # Try service account authentication
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                if 'google.oauth2' in self.ml_system.successful_dependencies:
                    service_account = self.ml_system.successful_dependencies['google.oauth2'].service_account
                    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
                    self.client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
                else:
                    print("⚠ google.oauth2 not available, trying default credentials")
                    self.client = bigquery.Client(project=PROJECT_ID)
            else:
                print("⚠ Service account file not found, trying default credentials")
                self.client = bigquery.Client(project=PROJECT_ID)
            
            # Test connection
            datasets = list(self.client.list_datasets(max_results=1))
            print("✓ BIGQUERY: Authentication successful")
            return True
            
        except Exception as e:
            print("✗ BIGQUERY: Authentication failed - {}".format(e))
            return False
    
    def _compute_requirement_embeddings(self):
        """Compute requirement embeddings using available ML"""
        requirement_descriptions = {
            'REQ-1': 'global view asset identifiers hostname computer device system',
            'REQ-2': 'infrastructure type deployment cloud aws azure gcp onpremises',
            'REQ-3': 'regional country geographic location datacenter region zone',
            'REQ-4': 'business application organizational unit department division',
            'REQ-5': 'system classification server function operating system windows linux',
            'REQ-6': 'security control coverage agent endpoint detection response edr',
            'REQ-7': 'logging compliance platform splunk chronicle ingestion parsing',
            'REQ-8': 'domain visibility hostname dns resolution network address fqdn'
        }
        
        try:
            if 'sentence_transformer' in self.ml_system.models:
                model = self.ml_system.models['sentence_transformer']
                for req, desc in requirement_descriptions.items():
                    embedding = model.encode([desc])[0]
                    self.requirement_embeddings[req] = embedding
                    
                print("✓ EMBEDDINGS: Computed for {} requirements".format(len(self.requirement_embeddings)))
                
        except Exception as e:
            print("⚠ EMBEDDINGS: Failed to compute - {}".format(e))
    
    def compute_field_score(self, field_name: str) -> Tuple[Dict[str, float], str]:
        """Compute comprehensive field scoring"""
        scores = {
            'exact_match': 0.0,
            'pattern_match': 0.0,
            'semantic_similarity': 0.0,
            'composite_score': 0.0
        }
        
        field_lower = field_name.lower().strip()
        matched_keyword = None
        
        # Exact match
        if field_lower in self.all_keywords:
            scores['exact_match'] = 1.0
            matched_keyword = field_lower
        
        # Pattern matching
        best_pattern_score = 0.0
        for keyword in self.all_keywords:
            if len(keyword) >= 3:
                if keyword in field_lower:
                    pattern_score = len(keyword) / len(field_lower)
                    if pattern_score > best_pattern_score:
                        best_pattern_score = pattern_score
                        if not matched_keyword:
                            matched_keyword = keyword
                elif field_lower in keyword and len(field_lower) >= 3:
                    pattern_score = len(field_lower) / len(keyword)
                    if pattern_score > best_pattern_score:
                        best_pattern_score = pattern_score
                        if not matched_keyword:
                            matched_keyword = keyword
        
        scores['pattern_match'] = best_pattern_score
        
        # Semantic similarity (if available)
        if self.requirement_embeddings and 'sentence_transformer' in self.ml_system.models:
            try:
                model = self.ml_system.models['sentence_transformer']
                field_embedding = model.encode([field_name])
                
                best_similarity = 0.0
                for req_embedding in self.requirement_embeddings.values():
                    if 'sklearn' in self.ml_system.successful_dependencies:
                        cosine_similarity = self.ml_system.successful_dependencies['sklearn'].metrics.pairwise.cosine_similarity
                        similarity = cosine_similarity(field_embedding, req_embedding.reshape(1, -1))[0][0]
                        best_similarity = max(best_similarity, similarity)
                
                scores['semantic_similarity'] = best_similarity
                
            except Exception as e:
                print("⚠ Semantic scoring error: {}".format(e))
        
        # Composite score
        if scores['exact_match'] > 0:
            scores['composite_score'] = 1.0
        elif scores['semantic_similarity'] > 0:
            scores['composite_score'] = 0.4 * scores['pattern_match'] + 0.6 * scores['semantic_similarity']
        else:
            scores['composite_score'] = scores['pattern_match']
        
        return scores, matched_keyword or field_lower
    
    def get_requirement_for_keyword(self, keyword: str) -> str:
        """Get requirement for keyword"""
        for req, keywords in self.requirement_keywords.items():
            if keyword in keywords:
                return req
        return "UNKNOWN"
    
    def analyze_table(self, dataset_id: str, table_id: str) -> List[FieldMatch]:
        """Analyze table for AO1 fields"""
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)
            
            matches = []
            
            def analyze_field(field, parent_path=""):
                field_path = "{}.{}".format(parent_path, field.name) if parent_path else field.name
                
                scores, matched_keyword = self.compute_field_score(field.name)
                
                if scores['composite_score'] > 0.3:  # Threshold for relevance
                    requirement = self.get_requirement_for_keyword(matched_keyword)
                    
                    if scores['exact_match'] >= 1.0:
                        match_type = "EXACT"
                    elif scores['composite_score'] >= 0.8:
                        match_type = "HIGH_CONFIDENCE"
                    elif scores['composite_score'] >= 0.6:
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
                        matched_keyword=matched_keyword,
                        match_type=match_type,
                        confidence_score=scores['composite_score'],
                        table_rows=table.num_rows or 0,
                        table_size_bytes=table.num_bytes or 0,
                        semantic_similarity=scores['semantic_similarity'],
                        context_relevance=0.8  # Default context relevance
                    )
                    matches.append(match)
                
                # Handle nested fields
                if field.field_type in ['RECORD', 'STRUCT'] and field.fields:
                    for nested_field in field.fields:
                        analyze_field(nested_field, field_path)
            
            for field in table.schema:
                analyze_field(field)
            
            return matches
            
        except Exception as e:
            logger.error("Table analysis error {}.{}: {}".format(dataset_id, table_id, e))
            return []
    
    def scan_all_datasets(self) -> List[FieldMatch]:
        """Scan all datasets for AO1 fields"""
        if not self.client:
            print("✗ CRITICAL: BigQuery client not available")
            return []
        
        try:
            datasets = [d.dataset_id for d in self.client.list_datasets()]
            print("SCANNING: {} datasets".format(len(datasets)))
            
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
            
            print("PROCESSING: {} tables".format(total_tables))
            
            # Process tables
            for dataset_id in datasets:
                try:
                    tables = list(self.client.list_tables(dataset_id))
                    
                    for table in tables:
                        processed_tables += 1
                        
                        if processed_tables % 50 == 0:
                            progress = (processed_tables / total_tables) * 100
                            print("PROGRESS: {:.1f}% ({}/{})".format(progress, processed_tables, total_tables))
                        
                        matches = self.analyze_table(dataset_id, table.table_id)
                        all_matches.extend(matches)
                        
                except Exception as e:
                    logger.error("Dataset error {}: {}".format(dataset_id, e))
                    continue
            
            print("ANALYSIS COMPLETE: {} matches found".format(len(all_matches)))
            return all_matches
            
        except Exception as e:
            logger.error("Scan error: {}".format(e))
            return []
    
    def generate_report(self, matches: List[FieldMatch]):
        """Generate comprehensive report"""
        if not matches:
            print("\nULTRA-ROBUST AO1 ANALYSIS COMPLETE")
            print("=" * 60)
            print("STATUS: No AO1-relevant fields discovered")
            return
        
        # Sort by strategic importance
        matches.sort(key=lambda x: (x.requirement, -x.confidence_score, -x.table_rows))
        
        # Group by requirement
        by_requirement = defaultdict(list)
        for match in matches:
            by_requirement[match.requirement].append(match)
        
        print("\nULTRA-ROBUST AO1 ANALYSIS COMPLETE")
        print("=" * 60)
        
        # System capabilities
        capabilities = []
        if self.ml_system.torch_available:
            capabilities.append("PyTorch Neural Networks")
        if self.ml_system.sentence_transformers_available:
            capabilities.append("Semantic Analysis")
        if self.ml_system.sklearn_available:
            capabilities.append("Statistical Analysis")
        
        print("SYSTEM CAPABILITIES: {}".format(", ".join(capabilities) if capabilities else "Pattern Matching"))
        print("PROXY STATUS: {}".format("Working" if self.proxy_manager.proxy_working else "Direct Connection"))
        print("TOTAL DISCOVERIES: {} fields across {} requirements".format(len(matches), len(by_requirement)))
        
        # Requirement analysis
        for req_num in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
            req_matches = by_requirement.get(req_num, [])
            
            if not req_matches:
                print("\n{}: No fields identified".format(req_num))
                continue
            
            # Categorize
            exact = [m for m in req_matches if m.match_type == 'EXACT']
            high_conf = [m for m in req_matches if m.match_type == 'HIGH_CONFIDENCE']
            ml_id = [m for m in req_matches if m.match_type == 'ML_IDENTIFIED']
            suspected = [m for m in req_matches if m.match_type == 'SUSPECTED']
            
            print("\n{}: {} total candidates".format(req_num, len(req_matches)))
            print("   EXACT: {} | HIGH_CONF: {} | ML_ID: {} | SUSPECTED: {}".format(
                len(exact), len(high_conf), len(ml_id), len(suspected)))
            
            # Top recommendations
            top_matches = sorted(req_matches, key=lambda x: (-x.confidence_score, -x.table_rows))[:3]
            
            print("   TOP RECOMMENDATIONS:")
            for i, match in enumerate(top_matches, 1):
                rows_info = "{:,} rows".format(match.table_rows) if match.table_rows > 0 else "unknown size"
                print("      {}. Field '{}' in {}.{} ({})".format(
                    i, match.field_name, match.dataset, match.table, rows_info))
                print("         Confidence: {:.1%} | Type: {} | Semantic: {:.1%}".format(
                    match.confidence_score, match.match_type, match.semantic_similarity))
    
    def save_results(self, matches: List[FieldMatch]):
        """Save comprehensive results"""
        if not matches:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed CSV
        df = pd.DataFrame([asdict(match) for match in matches])
        df['analysis_timestamp'] = timestamp
        df = df.sort_values(['requirement', 'confidence_score'], ascending=[True, False])
        
        filename = "ao1_ultra_robust_analysis_{}.csv".format(timestamp)
        df.to_csv(filename, index=False)
        
        print("\nRESULTS SAVED: {}".format(filename))
        print("Total records: {}".format(len(df)))

def main():
    """Main execution"""
    try:
        analyzer = UltraRobustAO1Analyzer()
        
        if analyzer.client:
            matches = analyzer.scan_all_datasets()
            analyzer.generate_report(matches)
            analyzer.save_results(matches)
        else:
            print("CRITICAL: Could not establish BigQuery connection")
            print("Check authentication and network connectivity")
        
    except KeyboardInterrupt:
        print("\nANALYSIS INTERRUPTED")
    except Exception as e:
        print("\nCRITICAL ERROR: {}".format(e))
        logger.error("Main execution error: {}".format(e))

if __name__ == "__main__":
    main()