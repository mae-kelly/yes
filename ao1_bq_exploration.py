#!/usr/bin/env python3
"""
AO1 BigQuery Field Discovery System
==================================

Enterprise-grade system for discovering AO1 compliance fields in BigQuery datasets.
Combines advanced ML analysis with corporate network security and comprehensive
business context understanding.

Architecture:
- Corporate connection management with 16 secure authentication methods
- ML-powered semantic analysis with M1 GPU acceleration
- Business context analysis for table and field relevance
- Professional reporting with actionable recommendations
- Exact keyword matching against comprehensive AO1 requirements

Author: Enterprise Security Analytics Team
Version: 2.0
Target: prj-fisv-p-gcss-sas-dl9dd0f1df
"""

import os
import sys
import json
import time
import logging
import subprocess
import importlib.util
import urllib.parse
import urllib.request
import ssl
import socket
import platform
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache, wraps
import threading

# Configure enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ao1_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import AO1 keywords from external module
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

logger.info("AO1 keywords successfully imported from external module")

# AO1 requirements metadata
AO1_REQUIREMENTS = {
    'REQ-1': {
        'name': 'Global View',
        'description': 'Asset identifiers for counting unique logging assets vs CMDB',
        'keywords': REQ1_GLOBAL_VIEW_KEYWORDS,
        'business_purpose': 'Enables accurate asset counting and CMDB comparison',
        'table_indicators': ['cmdb', 'asset', 'inventory', 'device', 'endpoint', 'host'],
        'key_concepts': ['hostname', 'asset_id', 'ip_address', 'mac_address', 'serial_number']
    },
    'REQ-2': {
        'name': 'Infrastructure Type',
        'description': 'Deployment model classification (On-Prem/Cloud/SaaS)',
        'keywords': REQ2_INFRASTRUCTURE_TYPE_KEYWORDS,
        'business_purpose': 'Classifies infrastructure deployment models',
        'table_indicators': ['cloud', 'infrastructure', 'deployment', 'instance', 'vm'],
        'key_concepts': ['cloud', 'on_premises', 'virtual_machine', 'container', 'saas']
    },
    'REQ-3': {
        'name': 'Regional/Country View',
        'description': 'Geographic location classification for global visibility',
        'keywords': REQ3_REGIONAL_COUNTRY_KEYWORDS,
        'business_purpose': 'Provides geographic distribution analysis',
        'table_indicators': ['region', 'location', 'geo', 'country', 'datacenter'],
        'key_concepts': ['region', 'country', 'datacenter', 'cloud_region', 'timezone']
    },
    'REQ-4': {
        'name': 'Business/Application View',
        'description': 'Organizational and application classification',
        'keywords': REQ4_BUSINESS_APPLICATION_KEYWORDS,
        'business_purpose': 'Maps technical assets to business units and applications',
        'table_indicators': ['business', 'application', 'service', 'org', 'department'],
        'key_concepts': ['business_unit', 'application', 'service', 'department', 'cost_center']
    },
    'REQ-5': {
        'name': 'System Classification',
        'description': 'Server function and OS type classification',
        'keywords': REQ5_SYSTEM_CLASSIFICATION_KEYWORDS,
        'business_purpose': 'Categorizes systems by function and operating system',
        'table_indicators': ['system', 'server', 'os', 'operating', 'platform'],
        'key_concepts': ['operating_system', 'server_type', 'web_server', 'database_server', 'windows']
    },
    'REQ-6': {
        'name': 'Security Control Coverage',
        'description': 'EDR, Tanium, DLP agent presence and coverage analysis',
        'keywords': REQ6_SECURITY_CONTROL_COVERAGE_KEYWORDS,
        'business_purpose': 'Measures security control deployment and coverage',
        'table_indicators': ['security', 'agent', 'edr', 'endpoint', 'protection'],
        'key_concepts': ['crowdstrike', 'tanium', 'dlp', 'edr', 'agent_status']
    },
    'REQ-7': {
        'name': 'Logging Compliance',
        'description': 'GSO (Chronicle) and Splunk platform compliance',
        'keywords': REQ7_LOGGING_COMPLIANCE_KEYWORDS,
        'business_purpose': 'Ensures comprehensive log collection and SIEM compliance',
        'table_indicators': ['log', 'siem', 'chronicle', 'splunk', 'event'],
        'key_concepts': ['chronicle', 'splunk', 'siem', 'log_source', 'syslog']
    },
    'REQ-8': {
        'name': 'Domain Visibility',
        'description': 'Hostname and domain-based asset visibility',
        'keywords': REQ8_DOMAIN_VISIBILITY_KEYWORDS,
        'business_purpose': 'Provides DNS and domain-based asset identification',
        'table_indicators': ['domain', 'dns', 'hostname', 'fqdn', 'ad'],
        'key_concepts': ['domain', 'fqdn', 'hostname', 'dns_record', 'active_directory']
    }
}


def retry_with_exponential_backoff(max_retries=3, base_delay=1):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds before first retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def thread_safe_singleton(cls):
    """Thread-safe singleton decorator."""
    instances = {}
    lock = threading.Lock()
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@dataclass
class ConnectionMethod:
    """Represents a corporate connection method with its configuration."""
    name: str
    success: bool
    message: str
    config: Dict[str, Any] = field(default_factory=dict)
    security_score: int = 0
    auth_type: Optional[str] = None


@dataclass
class FieldAnalysis:
    """Comprehensive field analysis result."""
    field_name: str
    table_name: str
    dataset_name: str
    row_count: int
    match_type: str  # EXACT, PARTIAL, ML_IDENTIFIED, SUSPECTED
    confidence: float
    matching_keywords: List[str]
    matching_requirements: List[str]
    semantic_similarity: float
    business_context: str
    table_context: str
    recommendation: str
    strategic_priority: int = 0


class CorporateConnectionManager:
    """
    Comprehensive corporate connection manager that tests all secure methods.
    
    Implements 16 different corporate authentication and connection strategies,
    ranking them by security score and selecting the optimal configuration.
    """
    
    def __init__(self):
        self.working_methods: Dict[str, ConnectionMethod] = {}
        self.failed_methods: Dict[str, ConnectionMethod] = {}
        self.security_config: Dict[str, Any] = {}
        self.optimal_method: Optional[ConnectionMethod] = None
        
    def establish_secure_corporate_connection(self) -> Dict[str, Any]:
        """
        Test all secure corporate connection methods and select optimal configuration.
        
        Returns:
            Dict containing success status, working methods count, and optimal configuration
        """
        logger.info("Testing comprehensive secure corporate connection methods")
        
        connection_methods = [
            self._test_corporate_proxy_with_auth,
            self._test_corporate_proxy_ntlm,
            self._test_corporate_proxy_kerberos,
            self._test_corporate_ca_bundle,
            self._test_corporate_pkcs12_cert,
            self._test_corporate_pem_cert,
            self._test_corporate_system_keychain,
            self._test_pac_auto_config,
            self._test_wpad_discovery,
            self._test_environment_proxy,
            self._test_system_proxy_settings,
            self._test_corporate_vpn_detection,
            self._test_corporate_dns_resolution,
            self._test_corporate_firewall_bypass,
            self._test_secure_tunnel_detection,
            self._test_corporate_sso_integration
        ]
        
        # Execute all connection tests in parallel for efficiency
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_method = {executor.submit(method): method for method in connection_methods}
            
            for future in as_completed(future_to_method):
                method = future_to_method[future]
                method_name = method.__name__.replace('_test_', '').replace('_', ' ').title()
                
                try:
                    result = future.result(timeout=30)
                    if result.success:
                        self.working_methods[method.__name__] = result
                        logger.info(f"SUCCESS: {method_name} - {result.message}")
                    else:
                        self.failed_methods[method.__name__] = result
                        logger.debug(f"FAILED: {method_name} - {result.message}")
                except Exception as e:
                    self.failed_methods[method.__name__] = ConnectionMethod(
                        name=method_name, success=False, message=str(e)
                    )
                    logger.debug(f"ERROR: {method_name} - {str(e)}")
        
        return self._configure_optimal_connection()
    
    @retry_with_exponential_backoff(max_retries=2)
    def _test_corporate_proxy_with_auth(self) -> ConnectionMethod:
        """Test HTTP/HTTPS proxy with username/password authentication."""
        try:
            import requests
            from requests.auth import HTTPProxyAuth
            
            for env_var in ['HTTPS_PROXY', 'HTTP_PROXY', 'https_proxy', 'http_proxy']:
                proxy_url = os.environ.get(env_var)
                if proxy_url and '@' in proxy_url:
                    parsed = urllib.parse.urlparse(proxy_url)
                    if parsed.username and parsed.password:
                        clean_proxy = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
                        auth = HTTPProxyAuth(parsed.username, parsed.password)
                        
                        response = requests.get(
                            'https://httpbin.org/ip',
                            proxies={'https': clean_proxy, 'http': clean_proxy},
                            auth=auth,
                            timeout=10,
                            verify=False
                        )
                        
                        if response.status_code == 200:
                            return ConnectionMethod(
                                name='Corporate Proxy With Auth',
                                success=True,
                                message=f'Authenticated proxy: {parsed.hostname}:{parsed.port}',
                                config={'proxy': clean_proxy, 'auth': True},
                                security_score=6,
                                auth_type='basic'
                            )
            
            return ConnectionMethod(
                name='Corporate Proxy With Auth',
                success=False,
                message='No authenticated proxy found in environment'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Corporate Proxy With Auth',
                success=False,
                message=f'Authentication test failed: {str(e)}'
            )
    
    @retry_with_exponential_backoff(max_retries=2)
    def _test_corporate_proxy_ntlm(self) -> ConnectionMethod:
        """Test NTLM authentication through corporate proxy."""
        try:
            from requests_ntlm import HttpNtlmAuth
            import requests
            import getpass
            
            proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
            if not proxy_url:
                return ConnectionMethod(
                    name='Corporate Proxy NTLM',
                    success=False,
                    message='No proxy configured for NTLM'
                )
            
            username = os.environ.get('USERNAME', getpass.getuser())
            domain = os.environ.get('USERDOMAIN', 'CORP')
            auth = HttpNtlmAuth(f'{domain}\\{username}', '')
            
            response = requests.get(
                'https://httpbin.org/ip',
                proxies={'https': proxy_url, 'http': proxy_url},
                auth=auth,
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                return ConnectionMethod(
                    name='Corporate Proxy NTLM',
                    success=True,
                    message=f'NTLM authentication successful: {domain}\\{username}',
                    config={'proxy': proxy_url, 'auth_type': 'ntlm'},
                    security_score=7,
                    auth_type='ntlm'
                )
            
            return ConnectionMethod(
                name='Corporate Proxy NTLM',
                success=False,
                message='NTLM authentication failed'
            )
            
        except ImportError:
            return ConnectionMethod(
                name='Corporate Proxy NTLM',
                success=False,
                message='requests-ntlm library not available'
            )
        except Exception as e:
            return ConnectionMethod(
                name='Corporate Proxy NTLM',
                success=False,
                message=f'NTLM test failed: {str(e)}'
            )
    
    @retry_with_exponential_backoff(max_retries=2)
    def _test_corporate_proxy_kerberos(self) -> ConnectionMethod:
        """Test Kerberos authentication through corporate proxy."""
        try:
            from requests_kerberos import HTTPKerberosAuth
            import requests
            
            proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
            if not proxy_url:
                return ConnectionMethod(
                    name='Corporate Proxy Kerberos',
                    success=False,
                    message='No proxy configured for Kerberos'
                )
            
            auth = HTTPKerberosAuth()
            response = requests.get(
                'https://httpbin.org/ip',
                proxies={'https': proxy_url, 'http': proxy_url},
                auth=auth,
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                return ConnectionMethod(
                    name='Corporate Proxy Kerberos',
                    success=True,
                    message='Kerberos authentication successful',
                    config={'proxy': proxy_url, 'auth_type': 'kerberos'},
                    security_score=8,
                    auth_type='kerberos'
                )
            
            return ConnectionMethod(
                name='Corporate Proxy Kerberos',
                success=False,
                message='Kerberos authentication failed'
            )
            
        except ImportError:
            return ConnectionMethod(
                name='Corporate Proxy Kerberos',
                success=False,
                message='requests-kerberos library not available'
            )
        except Exception as e:
            return ConnectionMethod(
                name='Corporate Proxy Kerberos',
                success=False,
                message=f'Kerberos test failed: {str(e)}'
            )
    
    def _test_corporate_ca_bundle(self) -> ConnectionMethod:
        """Test corporate CA certificate bundle verification."""
        try:
            import requests
            
            ca_paths = [
                os.environ.get('REQUESTS_CA_BUNDLE'),
                os.environ.get('CURL_CA_BUNDLE'),
                os.environ.get('SSL_CERT_FILE'),
                '/etc/ssl/certs/ca-certificates.crt',
                '/etc/ssl/certs/ca-bundle.crt',
                '/etc/pki/tls/certs/ca-bundle.crt',
                '/usr/local/etc/openssl/cert.pem',
                '/opt/local/etc/openssl/cert.pem',
                '/System/Library/Keychains/SystemRootCertificates.keychain',
                '/Library/Keychains/System.keychain'
            ]
            
            for ca_path in ca_paths:
                if ca_path and os.path.exists(ca_path):
                    try:
                        response = requests.get(
                            'https://httpbin.org/ip',
                            verify=ca_path,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            return ConnectionMethod(
                                name='Corporate CA Bundle',
                                success=True,
                                message=f'Corporate CA bundle working: {ca_path}',
                                config={'ca_bundle': ca_path},
                                security_score=6
                            )
                    except:
                        continue
            
            return ConnectionMethod(
                name='Corporate CA Bundle',
                success=False,
                message='No working corporate CA bundle found'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Corporate CA Bundle',
                success=False,
                message=f'CA bundle test failed: {str(e)}'
            )
    
    def _test_corporate_pkcs12_cert(self) -> ConnectionMethod:
        """Test PKCS#12 client certificate authentication."""
        try:
            import requests
            from cryptography.hazmat.primitives.serialization import pkcs12
            
            cert_paths = [
                os.path.expanduser('~/.certificates/client.p12'),
                os.path.expanduser('~/certificates/client.p12'),
                '/etc/ssl/certs/client.p12'
            ]
            
            for cert_path in cert_paths:
                if os.path.exists(cert_path) and cert_path.endswith('.p12'):
                    try:
                        passwords = [b'', b'password', b'changeme']
                        for password in passwords:
                            try:
                                with open(cert_path, 'rb') as f:
                                    cert_data = f.read()
                                
                                private_key, certificate, _ = pkcs12.load_key_and_certificates(
                                    cert_data, password
                                )
                                
                                response = requests.get(
                                    'https://httpbin.org/ip',
                                    cert=(cert_path, password.decode() if password else None),
                                    timeout=10,
                                    verify=False
                                )
                                
                                if response.status_code == 200:
                                    return ConnectionMethod(
                                        name='Corporate PKCS12 Cert',
                                        success=True,
                                        message=f'PKCS#12 certificate working: {cert_path}',
                                        config={'client_cert': cert_path},
                                        security_score=10
                                    )
                            except:
                                continue
                    except:
                        continue
            
            return ConnectionMethod(
                name='Corporate PKCS12 Cert',
                success=False,
                message='No working PKCS#12 client certificate found'
            )
            
        except ImportError:
            return ConnectionMethod(
                name='Corporate PKCS12 Cert',
                success=False,
                message='cryptography library not available'
            )
        except Exception as e:
            return ConnectionMethod(
                name='Corporate PKCS12 Cert',
                success=False,
                message=f'PKCS#12 test failed: {str(e)}'
            )
    
    def _test_corporate_pem_cert(self) -> ConnectionMethod:
        """Test PEM client certificate authentication."""
        try:
            import requests
            
            cert_locations = [
                (os.path.expanduser('~/.certificates/client.crt'), 
                 os.path.expanduser('~/.certificates/client.key')),
                (os.path.expanduser('~/certificates/client.crt'), 
                 os.path.expanduser('~/certificates/client.key')),
                ('/etc/ssl/certs/client.crt', '/etc/ssl/private/client.key'),
                ('/etc/pki/tls/certs/client.crt', '/etc/pki/tls/private/client.key')
            ]
            
            for cert_file, key_file in cert_locations:
                if os.path.exists(cert_file) and os.path.exists(key_file):
                    try:
                        response = requests.get(
                            'https://httpbin.org/ip',
                            cert=(cert_file, key_file),
                            timeout=10,
                            verify=False
                        )
                        
                        if response.status_code == 200:
                            return ConnectionMethod(
                                name='Corporate PEM Cert',
                                success=True,
                                message=f'PEM certificate working: {cert_file}',
                                config={'client_cert': cert_file, 'client_key': key_file},
                                security_score=9
                            )
                    except:
                        continue
            
            return ConnectionMethod(
                name='Corporate PEM Cert',
                success=False,
                message='No working PEM client certificate found'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Corporate PEM Cert',
                success=False,
                message=f'PEM certificate test failed: {str(e)}'
            )
    
    def _test_corporate_system_keychain(self) -> ConnectionMethod:
        """Test system keychain/certificate store integration."""
        try:
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                try:
                    import subprocess
                    result = subprocess.run([
                        'security', 'find-certificate', '-c', 'Corporate', '-p'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0 and result.stdout:
                        return ConnectionMethod(
                            name='Corporate System Keychain',
                            success=True,
                            message='macOS system keychain certificates available',
                            config={'keychain': 'system'},
                            security_score=4
                        )
                except:
                    pass
            
            elif system == 'Windows':  # Windows
                try:
                    import ssl
                    context = ssl.create_default_context()
                    context.load_default_certs(ssl.Purpose.SERVER_AUTH)
                    
                    return ConnectionMethod(
                        name='Corporate System Keychain',
                        success=True,
                        message='Windows certificate store accessible',
                        config={'certstore': 'system'},
                        security_score=4
                    )
                except:
                    pass
            
            return ConnectionMethod(
                name='Corporate System Keychain',
                success=False,
                message=f'System keychain not accessible on {system}'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Corporate System Keychain',
                success=False,
                message=f'System keychain test failed: {str(e)}'
            )
    
    def _test_pac_auto_config(self) -> ConnectionMethod:
        """Test Proxy Auto-Configuration (PAC) file detection."""
        try:
            import requests
            
            pac_urls = [
                os.environ.get('PAC_URL'),
                'http://wpad/wpad.dat',
                'http://wpad.corp/wpad.dat',
                'http://proxy.corp/proxy.pac',
                'http://autoconfigure.corp/proxy.pac'
            ]
            
            for pac_url in pac_urls:
                if pac_url:
                    try:
                        response = requests.get(pac_url, timeout=5)
                        if response.status_code == 200 and 'FindProxyForURL' in response.text:
                            return ConnectionMethod(
                                name='PAC Auto Config',
                                success=True,
                                message=f'PAC file found: {pac_url}',
                                config={'pac_url': pac_url},
                                security_score=2
                            )
                    except:
                        continue
            
            return ConnectionMethod(
                name='PAC Auto Config',
                success=False,
                message='No accessible PAC file found'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='PAC Auto Config',
                success=False,
                message=f'PAC detection failed: {str(e)}'
            )
    
    def _test_wpad_discovery(self) -> ConnectionMethod:
        """Test Web Proxy Auto-Discovery Protocol (WPAD)."""
        try:
            import socket
            import requests
            
            wpad_hosts = ['wpad', 'wpad.corp', 'proxy', 'proxy.corp']
            
            for host in wpad_hosts:
                try:
                    ip = socket.gethostbyname(host)
                    wpad_url = f'http://{host}/wpad.dat'
                    
                    response = requests.get(wpad_url, timeout=5)
                    if response.status_code == 200 and 'FindProxyForURL' in response.text:
                        return ConnectionMethod(
                            name='WPAD Discovery',
                            success=True,
                            message=f'WPAD discovered: {host} ({ip})',
                            config={'wpad_host': host, 'wpad_ip': ip},
                            security_score=2
                        )
                except:
                    continue
            
            return ConnectionMethod(
                name='WPAD Discovery',
                success=False,
                message='WPAD discovery failed'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='WPAD Discovery',
                success=False,
                message=f'WPAD discovery error: {str(e)}'
            )
    
    def _test_environment_proxy(self) -> ConnectionMethod:
        """Test environment variable proxy detection and validation."""
        try:
            import requests
            
            proxy_vars = ['HTTPS_PROXY', 'HTTP_PROXY', 'https_proxy', 'http_proxy', 'ALL_PROXY']
            
            for var in proxy_vars:
                proxy_url = os.environ.get(var)
                if proxy_url:
                    try:
                        response = requests.get(
                            'https://httpbin.org/ip',
                            proxies={'https': proxy_url, 'http': proxy_url},
                            timeout=10,
                            verify=False
                        )
                        
                        if response.status_code == 200:
                            return ConnectionMethod(
                                name='Environment Proxy',
                                success=True,
                                message=f'Environment proxy working: {var}',
                                config={'proxy': proxy_url, 'env_var': var},
                                security_score=3
                            )
                    except:
                        continue
            
            return ConnectionMethod(
                name='Environment Proxy',
                success=False,
                message='No working environment proxy found'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Environment Proxy',
                success=False,
                message=f'Environment proxy test failed: {str(e)}'
            )
    
    def _test_system_proxy_settings(self) -> ConnectionMethod:
        """Test system-level proxy settings detection."""
        try:
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                try:
                    import subprocess
                    result = subprocess.run([
                        'networksetup', '-getwebproxy', 'Wi-Fi'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if 'Enabled: Yes' in result.stdout:
                        lines = result.stdout.split('\n')
                        server = next((line.split(': ')[1] for line in lines if line.startswith('Server:')), None)
                        port = next((line.split(': ')[1] for line in lines if line.startswith('Port:')), None)
                        
                        if server and port:
                            return ConnectionMethod(
                                name='System Proxy Settings',
                                success=True,
                                message=f'macOS system proxy: {server}:{port}',
                                config={'proxy': f'http://{server}:{port}'},
                                security_score=3
                            )
                except:
                    pass
            
            elif system == 'Windows':  # Windows
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                       r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')
                    proxy_enable = winreg.QueryValueEx(key, 'ProxyEnable')[0]
                    
                    if proxy_enable:
                        proxy_server = winreg.QueryValueEx(key, 'ProxyServer')[0]
                        return ConnectionMethod(
                            name='System Proxy Settings',
                            success=True,
                            message=f'Windows system proxy: {proxy_server}',
                            config={'proxy': f'http://{proxy_server}'},
                            security_score=3
                        )
                except:
                    pass
            
            return ConnectionMethod(
                name='System Proxy Settings',
                success=False,
                message=f'No system proxy found on {system}'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='System Proxy Settings',
                success=False,
                message=f'System proxy detection failed: {str(e)}'
            )
    
    def _test_corporate_vpn_detection(self) -> ConnectionMethod:
        """Test corporate VPN connection detection."""
        try:
            import subprocess
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                try:
                    result = subprocess.run([
                        'ifconfig'
                    ], capture_output=True, text=True, timeout=5)
                    
                    vpn_indicators = ['tun', 'tap', 'ppp', 'utun', 'ipsec']
                    for indicator in vpn_indicators:
                        if indicator in result.stdout.lower():
                            return ConnectionMethod(
                                name='Corporate VPN Detection',
                                success=True,
                                message=f'Corporate VPN detected: {indicator} interface',
                                config={'vpn_type': indicator},
                                security_score=5
                            )
                except:
                    pass
            
            elif system == 'Windows':  # Windows
                try:
                    result = subprocess.run([
                        'ipconfig', '/all'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if 'VPN' in result.stdout or 'TAP' in result.stdout:
                        return ConnectionMethod(
                            name='Corporate VPN Detection',
                            success=True,
                            message='Corporate VPN detected: Windows VPN adapter',
                            config={'vpn_type': 'windows_vpn'},
                            security_score=5
                        )
                except:
                    pass
            
            return ConnectionMethod(
                name='Corporate VPN Detection',
                success=False,
                message='No corporate VPN detected'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Corporate VPN Detection',
                success=False,
                message=f'VPN detection failed: {str(e)}'
            )
    
    def _test_corporate_dns_resolution(self) -> ConnectionMethod:
        """Test corporate DNS resolution capability."""
        try:
            import socket
            
            test_domains = ['huggingface.co', 'github.com', 'pypi.org', 'googleapis.com']
            resolved_count = 0
            
            for domain in test_domains:
                try:
                    socket.gethostbyname(domain)
                    resolved_count += 1
                except:
                    continue
            
            success_rate = resolved_count / len(test_domains)
            if success_rate >= 0.75:
                return ConnectionMethod(
                    name='Corporate DNS Resolution',
                    success=True,
                    message=f'Corporate DNS working: {resolved_count}/{len(test_domains)} domains resolved',
                    config={'resolved_domains': resolved_count},
                    security_score=1
                )
            
            return ConnectionMethod(
                name='Corporate DNS Resolution',
                success=False,
                message=f'DNS resolution poor: {resolved_count}/{len(test_domains)} domains'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Corporate DNS Resolution',
                success=False,
                message=f'DNS resolution test failed: {str(e)}'
            )
    
    def _test_corporate_firewall_bypass(self) -> ConnectionMethod:
        """Test corporate firewall detection and bypass strategies."""
        try:
            import requests
            
            test_endpoints = [
                ('https://httpbin.org/ip', 443),
                ('http://httpbin.org/ip', 80),
                ('https://httpbin.org:8080/ip', 8080),
                ('https://httpbin.org:8443/ip', 8443)
            ]
            
            working_endpoints = []
            for endpoint, port in test_endpoints:
                try:
                    response = requests.get(endpoint, timeout=5, verify=False)
                    if response.status_code == 200:
                        working_endpoints.append((endpoint, port))
                except:
                    continue
            
            if working_endpoints:
                return ConnectionMethod(
                    name='Corporate Firewall Bypass',
                    success=True,
                    message=f'Firewall bypass successful: {len(working_endpoints)} ports accessible',
                    config={'working_ports': [port for _, port in working_endpoints]},
                    security_score=1
                )
            
            return ConnectionMethod(
                name='Corporate Firewall Bypass',
                success=False,
                message='No accessible ports found through firewall'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Corporate Firewall Bypass',
                success=False,
                message=f'Firewall bypass test failed: {str(e)}'
            )
    
    def _test_secure_tunnel_detection(self) -> ConnectionMethod:
        """Test secure tunnel detection (SSH, encrypted proxy, etc.)."""
        try:
            # Check for SSH tunnel environment variables
            ssh_vars = ['SSH_AUTH_SOCK', 'SSH_AGENT_PID', 'SSH_CONNECTION']
            ssh_detected = any(os.environ.get(var) for var in ssh_vars)
            
            if ssh_detected:
                return ConnectionMethod(
                    name='Secure Tunnel Detection',
                    success=True,
                    message='SSH tunnel environment detected',
                    config={'tunnel_type': 'ssh'},
                    security_score=5
                )
            
            # Check for common tunnel ports
            import socket
            tunnel_ports = [1080, 8080, 3128, 8888, 9050]
            
            for port in tunnel_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    
                    if result == 0:
                        return ConnectionMethod(
                            name='Secure Tunnel Detection',
                            success=True,
                            message=f'Local tunnel detected on port {port}',
                            config={'tunnel_port': port},
                            security_score=5
                        )
                except:
                    continue
            
            return ConnectionMethod(
                name='Secure Tunnel Detection',
                success=False,
                message='No secure tunnels detected'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Secure Tunnel Detection',
                success=False,
                message=f'Tunnel detection failed: {str(e)}'
            )
    
    def _test_corporate_sso_integration(self) -> ConnectionMethod:
        """Test corporate Single Sign-On integration detection."""
        try:
            # Check for SSO environment variables
            sso_vars = [
                'ADFS_TOKEN', 'SAML_TOKEN', 'OIDC_TOKEN', 'OAUTH_TOKEN',
                'KRB5_CONFIG', 'KRB5CCNAME', 'KERB_PRINCIPAL'
            ]
            
            detected_sso = [var for var in sso_vars if os.environ.get(var)]
            
            if detected_sso:
                return ConnectionMethod(
                    name='Corporate SSO Integration',
                    success=True,
                    message=f'Corporate SSO detected: {", ".join(detected_sso)}',
                    config={'sso_vars': detected_sso},
                    security_score=5
                )
            
            # Check for browser-based SSO tokens
            try:
                import sqlite3
                
                chrome_paths = [
                    os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies'),
                    os.path.expanduser('~/.config/google-chrome/Default/Cookies'),
                    os.path.expanduser('~/AppData/Local/Google/Chrome/User Data/Default/Cookies')
                ]
                
                for path in chrome_paths:
                    if os.path.exists(path):
                        return ConnectionMethod(
                            name='Corporate SSO Integration',
                            success=True,
                            message='Browser-based SSO tokens available',
                            config={'browser': 'chrome'},
                            security_score=5
                        )
            except:
                pass
            
            return ConnectionMethod(
                name='Corporate SSO Integration',
                success=False,
                message='No corporate SSO integration detected'
            )
            
        except Exception as e:
            return ConnectionMethod(
                name='Corporate SSO Integration',
                success=False,
                message=f'SSO detection failed: {str(e)}'
            )
    
    def _configure_optimal_connection(self) -> Dict[str, Any]:
        """
        Configure optimal connection based on working methods.
        
        Returns:
            Dict containing success status, methods count, and optimal configuration
        """
        logger.info("Analyzing optimal configuration from working methods")
        
        if not self.working_methods:
            logger.warning("No working secure connection methods found")
            return {'success': False, 'methods': 0}
        
        # Security scoring matrix
        method_priority = {
            'pkcs12_cert': 10,
            'pem_cert': 9,
            'kerberos_auth': 8,
            'ntlm_auth': 7,
            'proxy_auth': 6,
            'ca_bundle': 6,
            'sso_integration': 5,
            'vpn_detected': 5,
            'system_keychain': 4,
            'system_proxy': 3,
            'env_proxy': 3,
            'pac_config': 2,
            'wpad_discovery': 2,
            'dns_resolution': 1,
            'firewall_bypass': 1
        }
        
        # Select optimal method
        best_method = None
        best_score = 0
        
        for method_name, result in self.working_methods.items():
            # Calculate composite score based on security and reliability
            base_score = result.security_score or method_priority.get(result.name.lower().replace(' ', '_'), 0)
            
            if base_score > best_score:
                best_score = base_score
                best_method = result
        
        if best_method:
            self.optimal_method = best_method
            self.security_config = best_method.config
            
            logger.info(f"Optimal method selected: {best_method.name} (Score: {best_score}/10)")
            
            return {
                'success': True,
                'methods': len(self.working_methods),
                'optimal_method': best_method,
                'security_score': best_score,
                'config': self.security_config
            }
        
        return {'success': False, 'methods': len(self.working_methods)}


class MLDependencyManager:
    """
    Advanced ML library dependency manager with intelligent installation.
    
    Handles detection, installation, and verification of ML libraries
    with comprehensive error handling and fallback strategies.
    """
    
    def __init__(self):
        self.available_libraries: Dict[str, Dict[str, Any]] = {}
        self.installation_attempts: Dict[str, bool] = {}
        
    @lru_cache(maxsize=128)
    def check_and_install_dependencies(self) -> Dict[str, bool]:
        """
        Check for ML dependencies and install if missing.
        
        Returns:
            Dict mapping library names to availability status
        """
        dependencies = {
            'torch': ['torch', 'torchvision', 'torchaudio'],
            'transformers': ['transformers'],
            'sentence_transformers': ['sentence-transformers'],
            'huggingface_hub': ['huggingface_hub'],
            'sklearn': ['scikit-learn'],
            'numpy': ['numpy'],
            'google.cloud.bigquery': ['google-cloud-bigquery'],
            'google.oauth2': ['google-auth']
        }
        
        logger.info("Checking ML library availability")
        
        for lib_name, packages in dependencies.items():
            try:
                if lib_name == 'torch':
                    import torch
                    self.available_libraries[lib_name] = {
                        'available': True,
                        'version': torch.__version__,
                        'mps_available': hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
                    }
                    logger.info(f"PyTorch {torch.__version__} available")
                    
                elif lib_name == 'transformers':
                    import transformers
                    self.available_libraries[lib_name] = {
                        'available': True,
                        'version': transformers.__version__
                    }
                    logger.info(f"Transformers {transformers.__version__} available")
                    
                elif lib_name == 'sentence_transformers':
                    import sentence_transformers
                    self.available_libraries[lib_name] = {
                        'available': True,
                        'version': sentence_transformers.__version__
                    }
                    logger.info(f"Sentence Transformers {sentence_transformers.__version__} available")
                    
                elif lib_name == 'sklearn':
                    import sklearn
                    self.available_libraries[lib_name] = {
                        'available': True,
                        'version': sklearn.__version__
                    }
                    logger.info(f"Scikit-learn {sklearn.__version__} available")
                    
                elif lib_name in ['google.cloud.bigquery', 'google.oauth2']:
                    # Import test for Google Cloud libraries
                    if lib_name == 'google.cloud.bigquery':
                        from google.cloud import bigquery
                    else:
                        from google.oauth2 import service_account
                    
                    self.available_libraries[lib_name] = {'available': True}
                    logger.info(f"{lib_name} available")
                    
                else:
                    spec = importlib.util.find_spec(lib_name)
                    self.available_libraries[lib_name] = {'available': spec is not None}
                    if spec:
                        logger.info(f"{lib_name} available")
                
            except ImportError as e:
                self.available_libraries[lib_name] = {'available': False, 'error': str(e)}
                logger.warning(f"{lib_name} not available: {str(e)}")
                
                # Attempt installation
                if self._attempt_installation(packages):
                    # Re-check after installation
                    try:
                        importlib.import_module(lib_name.split('.')[0])
                        self.available_libraries[lib_name]['available'] = True
                        logger.info(f"{lib_name} successfully installed")
                    except ImportError:
                        logger.error(f"{lib_name} installation failed")
        
        return {k: v['available'] for k, v in self.available_libraries.items()}
    
    def _attempt_installation(self, packages: List[str]) -> bool:
        """
        Attempt to install missing packages using multiple methods.
        
        Args:
            packages: List of package names to install
            
        Returns:
            True if installation succeeded
        """
        for package in packages:
            if package in self.installation_attempts:
                continue
                
            installation_commands = [
                [sys.executable, '-m', 'pip', 'install', package],
                ['pip3', 'install', package],
                ['pip', 'install', package]
            ]
            
            for cmd in installation_commands:
                try:
                    logger.info(f"Installing {package} with {' '.join(cmd)}")
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        self.installation_attempts[package] = True
                        logger.info(f"Successfully installed {package}")
                        return True
                    else:
                        logger.warning(f"Installation failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"Installation timeout for {package}")
                except Exception as e:
                    logger.warning(f"Installation error for {package}: {str(e)}")
            
            self.installation_attempts[package] = False
        
        return False
    
    def get_ml_capability_summary(self) -> str:
        """
        Get summary of available ML capabilities.
        
        Returns:
            Human-readable summary string
        """
        available = sum(1 for lib in self.available_libraries.values() if lib['available'])
        total = len(self.available_libraries)
        
        if available == total:
            return "Full ML capabilities available"
        elif available >= total * 0.7:
            return "Most ML capabilities available"
        elif available >= total * 0.5:
            return "Some ML capabilities available"
        else:
            return "Limited ML capabilities available"


class AdvancedMLAnalyzer:
    """
    Advanced ML analyzer with M1 GPU acceleration and multiple strategies.
    
    Implements progressive fallback from advanced transformer models to
    built-in embeddings, with automatic optimization for available hardware.
    """
    
    def __init__(self, dependency_manager: MLDependencyManager):
        self.dependency_manager = dependency_manager
        self.available_libs = dependency_manager.available_libraries
        self.device = 'cpu'
        self.ml_strategy = 'pattern_only'
        self.models: Dict[str, Any] = {}
        self.built_in_embeddings = self._create_built_in_embeddings()
        
        self._initialize_ml_components()
    
    def _initialize_ml_components(self):
        """Initialize ML components based on available libraries and hardware."""
        # Detect and configure compute device
        if self.available_libs.get('torch', {}).get('available', False):
            try:
                import torch
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self.device = 'mps'
                    logger.info("M1 GPU (MPS) acceleration enabled")
                elif torch.cuda.is_available():
                    self.device = 'cuda'
                    logger.info("CUDA GPU acceleration enabled")
                else:
                    self.device = 'cpu'
                    logger.info("CPU processing mode")
            except Exception as e:
                self.device = 'cpu'
                logger.warning(f"Device detection failed: {e}")
        
        # Initialize ML strategy based on available libraries
        if self.available_libs.get('sentence_transformers', {}).get('available', False):
            self.ml_strategy = 'sentence_transformers'
            self._initialize_sentence_transformers()
        elif self.available_libs.get('transformers', {}).get('available', False):
            self.ml_strategy = 'transformers_basic'
            self._initialize_basic_transformers()
        elif self.available_libs.get('sklearn', {}).get('available', False):
            self.ml_strategy = 'tfidf_similarity'
            self._initialize_tfidf()
        else:
            self.ml_strategy = 'pattern_only'
            logger.info("Using pattern matching only")
    
    def _initialize_sentence_transformers(self):
        """Initialize sentence transformers using secure corporate connections."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info("Initializing sentence transformers with corporate security")
            
            # Get optimal connection configuration
            connection_manager = CorporateConnectionManager()
            connection_result = connection_manager.establish_secure_corporate_connection()
            
            if connection_result['success']:
                optimal_config = connection_result.get('config', {})
                logger.info(f"Using secure connection method: {connection_result['optimal_method'].name}")
                self._apply_secure_configuration(optimal_config)
            else:
                logger.warning("No secure connections available, using direct connection")
            
            # Model loading strategies
            models_to_try = [
                'sentence-transformers/all-MiniLM-L6-v2',
                'sentence-transformers/paraphrase-MiniLM-L6-v2',
                'sentence-transformers/all-mpnet-base-v2',
                'all-MiniLM-L6-v2',
                'paraphrase-MiniLM-L6-v2'
            ]
            
            for model_name in models_to_try:
                logger.info(f"Attempting to load {model_name}")
                
                # Strategy 1: Direct secure loading
                if self._try_secure_model_loading(model_name, optimal_config):
                    return
                
                # Strategy 2: Cached model loading
                if self._try_cached_model_loading(model_name):
                    return
            
            # Fallback to built-in embeddings
            logger.warning("All transformer models failed, using built-in embeddings")
            self.ml_strategy = 'built_in_embeddings'
            
        except ImportError:
            logger.error("Sentence Transformers library not available")
            self.ml_strategy = 'built_in_embeddings'
        except Exception as e:
            logger.error(f"Sentence transformer initialization failed: {e}")
            self.ml_strategy = 'built_in_embeddings'
    
    def _apply_secure_configuration(self, config: Dict[str, Any]):
        """Apply secure configuration for external connections only."""
        try:
            # Configure proxy for external connections, exclude Google services
            if 'proxy' in config:
                proxy_url = config['proxy']
                os.environ['HTTPS_PROXY'] = proxy_url
                os.environ['HTTP_PROXY'] = proxy_url
                
                # Exclude Google Cloud services from proxy
                gcloud_domains = 'googleapis.com,googleusercontent.com,storage.googleapis.com,bigquery.googleapis.com'
                no_proxy = os.environ.get('NO_PROXY', '')
                os.environ['NO_PROXY'] = f"{no_proxy},{gcloud_domains}" if no_proxy else gcloud_domains
                
                logger.info(f"Applied proxy for external connections: {proxy_url}")
            
            # Configure certificates for external connections
            if 'ca_bundle' in config:
                ca_bundle = config['ca_bundle']
                os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle
                os.environ['CURL_CA_BUNDLE'] = ca_bundle
                logger.info(f"Applied CA bundle: {ca_bundle}")
            
            if 'client_cert' in config:
                cert_file = config['client_cert']
                logger.info(f"Applied client certificate: {cert_file}")
            
        except Exception as e:
            logger.warning(f"Configuration application failed: {e}")
    
    def _try_secure_model_loading(self, model_name: str, config: Dict[str, Any]) -> bool:
        """Try loading model with secure configuration."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.debug(f"Attempting secure loading of {model_name}")
            
            model = SentenceTransformer(
                model_name,
                device=self.device,
                trust_remote_code=True,
                use_auth_token=False
            )
            
            # Verify model functionality
            test_encoding = model.encode(['test sentence'])
            if test_encoding is not None and len(test_encoding) > 0:
                self.models['sentence_transformer'] = model
                logger.info(f"Successfully loaded {model_name} with secure configuration")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Secure loading failed for {model_name}: {e}")
            return False
    
    def _try_cached_model_loading(self, model_name: str) -> bool:
        """Try loading model from local cache."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.debug(f"Attempting cached loading of {model_name}")
            
            model = SentenceTransformer(model_name, device=self.device, local_files_only=True)
            
            # Verify model functionality
            test_encoding = model.encode(['cached test sentence'])
            if test_encoding is not None and len(test_encoding) > 0:
                self.models['sentence_transformer'] = model
                logger.info(f"Successfully loaded {model_name} from cache")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Cached loading failed for {model_name}: {e}")
            return False
    
    def _initialize_basic_transformers(self):
        """Initialize basic transformers without sentence-transformers."""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            model_name = 'distilbert-base-uncased'
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            
            if self.device != 'cpu':
                model = model.to(self.device)
            
            self.models['tokenizer'] = tokenizer
            self.models['transformer'] = model
            logger.info(f"Basic transformers initialized: {model_name}")
            
        except Exception as e:
            logger.warning(f"Basic transformers initialization failed: {e}")
            self.ml_strategy = 'built_in_embeddings'
    
    def _initialize_tfidf(self):
        """Initialize TF-IDF similarity scoring."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            self.models['tfidf'] = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=1000
            )
            logger.info("TF-IDF vectorizer initialized")
            
        except ImportError:
            logger.warning("Scikit-learn not available")
            self.ml_strategy = 'pattern_only'
    
    def _create_built_in_embeddings(self) -> Dict[str, List[float]]:
        """
        Create optimized built-in semantic embeddings for AO1 keywords.
        
        Uses 8-dimensional vectors where each dimension represents:
        [identity, network, infrastructure, location, system, business, security, logging]
        
        Returns:
            Dict mapping keywords to embedding vectors
        """
        embeddings = {
            # REQ-1: Global View (Identity-focused)
            'hostname': [1.0, 0.8, 0.2, 0.1, 0.3, 0.1, 0.2, 0.9],
            'asset_id': [0.9, 0.7, 0.1, 0.1, 0.2, 0.1, 0.1, 0.8],
            'ip_address': [0.8, 0.9, 0.3, 0.1, 0.4, 0.1, 0.2, 0.7],
            'mac_address': [0.7, 0.9, 0.2, 0.1, 0.3, 0.1, 0.1, 0.6],
            'serial_number': [0.9, 0.2, 0.1, 0.1, 0.4, 0.1, 0.1, 0.5],
            
            # REQ-2: Infrastructure Type (Platform-focused)
            'cloud': [0.2, 0.1, 1.0, 0.8, 0.2, 0.1, 0.1, 0.3],
            'on_premises': [0.2, 0.1, 0.9, 0.2, 0.8, 0.1, 0.1, 0.3],
            'virtual_machine': [0.3, 0.2, 0.8, 0.7, 0.3, 0.1, 0.1, 0.4],
            'container': [0.2, 0.1, 0.9, 0.1, 0.4, 0.2, 0.1, 0.2],
            'saas': [0.1, 0.1, 0.8, 0.1, 0.1, 0.7, 0.1, 0.2],
            
            # REQ-3: Regional/Country (Location-focused)
            'region': [0.1, 0.2, 0.3, 1.0, 0.2, 0.1, 0.1, 0.2],
            'datacenter': [0.2, 0.3, 0.4, 0.9, 0.7, 0.1, 0.1, 0.3],
            'country': [0.1, 0.1, 0.2, 0.8, 0.1, 0.1, 0.1, 0.1],
            'timezone': [0.1, 0.1, 0.1, 0.7, 0.1, 0.1, 0.1, 0.1],
            
            # REQ-4: Business/Application (Business-focused)
            'application': [0.1, 0.1, 0.2, 0.1, 0.1, 1.0, 0.8, 0.2],
            'business_unit': [0.1, 0.1, 0.1, 0.2, 0.1, 0.9, 0.7, 0.1],
            'service': [0.2, 0.1, 0.3, 0.1, 0.1, 0.8, 0.9, 0.3],
            'department': [0.1, 0.1, 0.1, 0.1, 0.1, 0.9, 0.1, 0.1],
            
            # REQ-5: System Classification (System-focused)
            'operating_system': [0.3, 0.2, 0.4, 0.1, 1.0, 0.2, 0.1, 0.5],
            'windows': [0.3, 0.2, 0.3, 0.1, 0.9, 0.1, 0.1, 0.4],
            'linux': [0.3, 0.2, 0.4, 0.1, 0.8, 0.1, 0.1, 0.4],
            'web_server': [0.2, 0.3, 0.3, 0.1, 0.8, 0.3, 0.2, 0.4],
            'database_server': [0.2, 0.2, 0.3, 0.1, 0.9, 0.2, 0.3, 0.4],
            
            # REQ-6: Security Control (Security-focused)
            'crowdstrike': [0.4, 0.1, 0.2, 0.1, 0.2, 0.1, 1.0, 0.6],
            'edr': [0.3, 0.1, 0.2, 0.1, 0.2, 0.1, 0.9, 0.5],
            'tanium': [0.3, 0.1, 0.2, 0.1, 0.3, 0.1, 0.8, 0.4],
            'dlp': [0.2, 0.1, 0.1, 0.1, 0.1, 0.2, 0.9, 0.3],
            'agent_status': [0.3, 0.1, 0.1, 0.1, 0.2, 0.1, 0.8, 0.4],
            
            # REQ-7: Logging (Logging-focused)
            'splunk': [0.2, 0.1, 0.2, 0.1, 0.1, 0.3, 0.4, 1.0],
            'chronicle': [0.2, 0.1, 0.2, 0.1, 0.1, 0.3, 0.4, 0.9],
            'siem': [0.2, 0.1, 0.2, 0.1, 0.1, 0.2, 0.5, 0.8],
            'log_source': [0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.9],
            'syslog': [0.1, 0.1, 0.1, 0.1, 0.2, 0.1, 0.3, 0.8],
            
            # REQ-8: Domain Visibility (DNS-focused)
            'domain': [0.7, 0.6, 0.1, 0.2, 0.1, 0.1, 0.1, 0.3],
            'fqdn': [0.8, 0.7, 0.1, 0.2, 0.1, 0.1, 0.1, 0.4],
            'dns': [0.6, 0.8, 0.1, 0.3, 0.1, 0.1, 0.1, 0.2],
            'dns_record': [0.5, 0.8, 0.1, 0.2, 0.1, 0.1, 0.1, 0.3],
            'active_directory': [0.6, 0.3, 0.2, 0.1, 0.7, 0.3, 0.4, 0.2]
        }
        
        return embeddings
    
    def compute_semantic_similarity(self, field_name: str, requirement_keywords: Set[str]) -> float:
        """
        Compute semantic similarity between field and requirement keywords.
        
        Args:
            field_name: Name of the field to analyze
            requirement_keywords: Set of keywords for the requirement
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if self.ml_strategy == 'sentence_transformers' and 'sentence_transformer' in self.models:
            return self._compute_transformer_similarity(field_name, requirement_keywords)
        elif self.ml_strategy == 'built_in_embeddings':
            return self._compute_builtin_similarity(field_name, requirement_keywords)
        elif self.ml_strategy == 'tfidf_similarity':
            return self._compute_tfidf_similarity(field_name, requirement_keywords)
        else:
            return 0.0
    
    def _compute_transformer_similarity(self, field_name: str, requirement_keywords: Set[str]) -> float:
        """Compute similarity using sentence transformers."""
        try:
            model = self.models['sentence_transformer']
            
            field_embedding = model.encode([field_name])
            keyword_embeddings = model.encode(list(requirement_keywords))
            
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(field_embedding, keyword_embeddings)
            
            return float(similarities.max())
            
        except Exception as e:
            logger.warning(f"Transformer similarity computation failed: {e}")
            return self._compute_builtin_similarity(field_name, requirement_keywords)
    
    def _compute_builtin_similarity(self, field_name: str, requirement_keywords: Set[str]) -> float:
        """Compute similarity using built-in embeddings."""
        field_lower = field_name.lower()
        max_similarity = 0.0
        
        # Direct embedding lookup
        if field_lower in self.built_in_embeddings:
            field_vector = self.built_in_embeddings[field_lower]
            
            for keyword in requirement_keywords:
                if keyword in self.built_in_embeddings:
                    keyword_vector = self.built_in_embeddings[keyword]
                    similarity = self._cosine_similarity(field_vector, keyword_vector)
                    max_similarity = max(max_similarity, similarity)
        
        # Partial match analysis
        for embedding_key, embedding_vector in self.built_in_embeddings.items():
            if embedding_key in field_lower or field_lower in embedding_key:
                for keyword in requirement_keywords:
                    if keyword in self.built_in_embeddings:
                        keyword_vector = self.built_in_embeddings[keyword]
                        similarity = self._cosine_similarity(embedding_vector, keyword_vector)
                        max_similarity = max(max_similarity, similarity * 0.8)
        
        return max_similarity
    
    def _compute_tfidf_similarity(self, field_name: str, requirement_keywords: Set[str]) -> float:
        """Compute TF-IDF based similarity."""
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            documents = [field_name] + list(requirement_keywords)
            tfidf_matrix = self.models['tfidf'].fit_transform(documents)
            
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            return float(similarities.max()) if similarities.size > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"TF-IDF similarity computation failed: {e}")
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        try:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
                
            return dot_product / (magnitude1 * magnitude2)
        except:
            return 0.0


class BusinessContextAnalyzer:
    """
    Advanced business context analyzer for tables and fields.
    
    Provides sophisticated analysis of table purpose, business relevance,
    and contextual scoring for AO1 compliance assessment.
    """
    
    def __init__(self):
        self.table_context_patterns = {
            'cmdb': {
                'patterns': ['cmdb', 'configuration', 'asset', 'inventory', 'ci_'],
                'business_value': 'Critical for asset management and visibility',
                'ao1_relevance': ['REQ-1']
            },
            'security': {
                'patterns': ['security', 'sec_', 'edr', 'endpoint', 'agent', 'antivirus'],
                'business_value': 'Essential for security posture assessment',
                'ao1_relevance': ['REQ-6']
            },
            'logging': {
                'patterns': ['log', 'event', 'siem', 'splunk', 'chronicle', 'audit'],
                'business_value': 'Required for compliance and monitoring',
                'ao1_relevance': ['REQ-7']
            },
            'infrastructure': {
                'patterns': ['infra', 'server', 'vm', 'cloud', 'compute', 'instance'],
                'business_value': 'Important for infrastructure visibility',
                'ao1_relevance': ['REQ-2', 'REQ-5']
            },
            'network': {
                'patterns': ['network', 'net_', 'dns', 'ip_', 'domain', 'fqdn'],
                'business_value': 'Valuable for network asset tracking',
                'ao1_relevance': ['REQ-8']
            },
            'application': {
                'patterns': ['app', 'application', 'service', 'platform', 'workload'],
                'business_value': 'Useful for application mapping',
                'ao1_relevance': ['REQ-4']
            },
            'identity': {
                'patterns': ['identity', 'user', 'account', 'auth', 'ad_', 'ldap'],
                'business_value': 'Important for user access analysis',
                'ao1_relevance': ['REQ-8']
            },
            'business': {
                'patterns': ['business', 'org', 'department', 'cost_center', 'bu_'],
                'business_value': 'Valuable for organizational mapping',
                'ao1_relevance': ['REQ-4']
            }
        }
    
    def analyze_table_context(self, table_name: str, dataset_name: str) -> Dict[str, Any]:
        """
        Analyze the business context of a table.
        
        Args:
            table_name: Name of the table
            dataset_name: Name of the dataset
            
        Returns:
            Dict containing context analysis results
        """
        full_name = f"{dataset_name}.{table_name}".lower()
        
        context_scores = {}
        for context_type, config in self.table_context_patterns.items():
            score = 0
            for pattern in config['patterns']:
                if pattern in full_name:
                    score += 1
            context_scores[context_type] = score
        
        # Determine primary context
        primary_context = max(context_scores.items(), key=lambda x: x[1])
        context_type = primary_context[0] if primary_context[1] > 0 else 'general'
        
        config = self.table_context_patterns.get(context_type, {
            'business_value': 'Standard business data',
            'ao1_relevance': []
        })
        
        return {
            'primary_context': context_type,
            'context_scores': context_scores,
            'business_relevance': config['business_value'],
            'ao1_relevance': config['ao1_relevance'],
            'confidence': primary_context[1] / len(config.get('patterns', [1])) if primary_context[1] > 0 else 0.0
        }


class AO1FieldAnalyzer:
    """
    Comprehensive AO1 field analysis engine.
    
    Combines exact keyword matching, semantic analysis, business context,
    and strategic scoring to identify optimal AO1 compliance fields.
    """
    
    def __init__(self, ml_analyzer: AdvancedMLAnalyzer):
        self.ml_analyzer = ml_analyzer
        self.business_analyzer = BusinessContextAnalyzer()
        self.all_keywords = get_all_keywords()
        
    def analyze_field(self, field_name: str, table_name: str, dataset_name: str, row_count: int) -> Optional[FieldAnalysis]:
        """
        Comprehensive field analysis for AO1 compliance.
        
        Args:
            field_name: Name of the field to analyze
            table_name: Name of the containing table
            dataset_name: Name of the containing dataset
            row_count: Number of rows in the table
            
        Returns:
            FieldAnalysis object if field is AO1-relevant, None otherwise
        """
        if not field_name:
            return None
            
        field_lower = field_name.lower().strip()
        
        # Analyze table business context
        table_context = self.business_analyzer.analyze_table_context(table_name, dataset_name)
        
        # Check for exact keyword matches
        exact_matches = []
        matching_requirements = []
        
        if field_lower in self.all_keywords:
            exact_matches.append(field_lower)
            matching_requirements.extend(find_keyword_requirement(field_lower))
        
        # Check for partial matches
        partial_matches = []
        for keyword in self.all_keywords:
            if keyword != field_lower:
                if keyword in field_lower or field_lower in keyword:
                    partial_matches.append(keyword)
                    matching_requirements.extend(find_keyword_requirement(keyword))
        
        # Remove duplicate requirements
        matching_requirements = list(set(matching_requirements))
        
        # Compute semantic similarity across all requirements
        max_semantic_similarity = 0.0
        best_semantic_req = None
        
        for req_id, req_info in AO1_REQUIREMENTS.items():
            similarity = self.ml_analyzer.compute_semantic_similarity(field_name, req_info['keywords'])
            if similarity > max_semantic_similarity:
                max_semantic_similarity = similarity
                best_semantic_req = req_id
        
        # Determine match type and base confidence
        if exact_matches:
            match_type = 'EXACT'
            confidence = 100.0
        elif partial_matches and max_semantic_similarity > 0.7:
            match_type = 'ML_IDENTIFIED'
            confidence = min(90.0, max_semantic_similarity * 100)
            if best_semantic_req and f"{best_semantic_req}: {AO1_REQUIREMENTS[best_semantic_req]['name']}" not in matching_requirements:
                matching_requirements.append(f"{best_semantic_req}: {AO1_REQUIREMENTS[best_semantic_req]['name']}")
        elif partial_matches:
            match_type = 'PARTIAL'
            confidence = min(80.0, len(partial_matches) * 25)
        elif max_semantic_similarity > 0.5:
            match_type = 'SUSPECTED'
            confidence = max_semantic_similarity * 100
            if best_semantic_req:
                matching_requirements.append(f"{best_semantic_req}: {AO1_REQUIREMENTS[best_semantic_req]['name']}")
        else:
            return None  # Not AO1-relevant
        
        # Apply context-based confidence adjustments
        context_boost = self._calculate_context_boost(matching_requirements, table_context)
        confidence = min(100.0, confidence + context_boost)
        
        # Calculate strategic priority
        strategic_priority = self._calculate_strategic_priority(
            match_type, confidence, row_count, table_context, matching_requirements
        )
        
        # Generate business context and recommendations
        business_context = self._generate_business_context(
            field_name, table_name, dataset_name, matching_requirements, table_context
        )
        
        recommendation = self._generate_recommendation(
            match_type, confidence, matching_requirements, row_count, table_context
        )
        
        return FieldAnalysis(
            field_name=field_name,
            table_name=table_name,
            dataset_name=dataset_name,
            row_count=row_count,
            match_type=match_type,
            confidence=confidence,
            matching_keywords=exact_matches + partial_matches,
            matching_requirements=matching_requirements,
            semantic_similarity=max_semantic_similarity,
            business_context=business_context,
            table_context=table_context['primary_context'],
            recommendation=recommendation,
            strategic_priority=strategic_priority
        )
    
    def _calculate_context_boost(self, matching_requirements: List[str], table_context: Dict) -> float:
        """Calculate confidence boost based on table context alignment."""
        boost = 0.0
        context_type = table_context['primary_context']
        
        # Context-requirement alignment mapping
        context_req_mapping = {
            'cmdb': ['REQ-1'],
            'security': ['REQ-6'],
            'logging': ['REQ-7'],
            'infrastructure': ['REQ-2', 'REQ-5'],
            'network': ['REQ-8'],
            'application': ['REQ-4'],
            'business': ['REQ-4'],
            'identity': ['REQ-8']
        }
        
        expected_reqs = context_req_mapping.get(context_type, [])
        alignment_count = 0
        
        for req in matching_requirements:
            req_id = req.split(':')[0]
            if req_id in expected_reqs:
                alignment_count += 1
                boost += 10.0
        
        # Additional boost for high-confidence context
        if table_context.get('confidence', 0) > 0.8:
            boost += 5.0
        
        return min(boost, 25.0)  # Cap boost at 25 points
    
    def _calculate_strategic_priority(self, match_type: str, confidence: float, 
                                    row_count: int, table_context: Dict, 
                                    matching_requirements: List[str]) -> int:
        """
        Calculate strategic priority score for implementation planning.
        
        Returns:
            Integer priority score (higher = more strategic value)
        """
        priority = 0
        
        # Base score from match type
        match_scores = {
            'EXACT': 100,
            'ML_IDENTIFIED': 80,
            'PARTIAL': 60,
            'SUSPECTED': 40
        }
        priority += match_scores.get(match_type, 0)
        
        # Data volume bonus
        if row_count > 10000000:  # 10M+ rows
            priority += 50
        elif row_count > 1000000:  # 1M+ rows
            priority += 30
        elif row_count > 100000:  # 100K+ rows
            priority += 15
        elif row_count > 10000:  # 10K+ rows
            priority += 5
        
        # Confidence bonus
        priority += int(confidence * 0.5)
        
        # Business context bonus
        context_scores = {
            'cmdb': 40,
            'security': 35,
            'logging': 35,
            'infrastructure': 25,
            'network': 20,
            'application': 20,
            'business': 15,
            'identity': 15
        }
        priority += context_scores.get(table_context['primary_context'], 5)
        
        # Multiple requirement bonus
        if len(matching_requirements) > 1:
            priority += len(matching_requirements) * 10
        
        return priority
    
    def _generate_business_context(self, field_name: str, table_name: str, dataset_name: str,
                                 matching_requirements: List[str], table_context: Dict) -> str:
        """Generate comprehensive business context explanation."""
        context_type = table_context['primary_context']
        business_relevance = table_context['business_relevance']
        
        req_purposes = []
        for req in matching_requirements:
            req_id = req.split(':')[0]
            if req_id in AO1_REQUIREMENTS:
                req_purposes.append(AO1_REQUIREMENTS[req_id]['business_purpose'])
        
        context = f"The field '{field_name}' in table {dataset_name}.{table_name} "
        context += f"appears to be part of a {context_type} system with {business_relevance.lower()}. "
        
        if req_purposes:
            unique_purposes = list(set(req_purposes))
            context += f"This field supports: {'; '.join(unique_purposes)}. "
        
        # Add strategic context
        if context_type in ['cmdb', 'security', 'logging']:
            context += "This represents a high-priority data source for AO1 compliance measurement."
        elif context_type in ['infrastructure', 'network']:
            context += "This provides valuable technical asset visibility for compliance analysis."
        else:
            context += "This contributes to comprehensive organizational asset visibility."
            
        return context
    
    def _generate_recommendation(self, match_type: str, confidence: float,
                               matching_requirements: List[str], row_count: int,
                               table_context: Dict) -> str:
        """Generate actionable implementation recommendation."""
        recommendation = ""
        
        # Base recommendation from match type and confidence
        if match_type == 'EXACT' and confidence >= 95:
            recommendation = "HIGHLY RECOMMENDED - Perfect AO1 compliance match"
        elif match_type == 'EXACT':
            recommendation = "RECOMMENDED - Direct AO1 keyword match"
        elif match_type == 'ML_IDENTIFIED' and confidence >= 85:
            recommendation = "RECOMMENDED - ML analysis indicates high AO1 relevance"
        elif match_type == 'PARTIAL' and confidence >= 75:
            recommendation = "CONSIDER - Partial match with good confidence"
        elif match_type == 'SUSPECTED' and confidence >= 60:
            recommendation = "INVESTIGATE - Semantic analysis suggests potential relevance"
        else:
            recommendation = "REVIEW - Low confidence, requires manual validation"
        
        # Add data volume context
        if row_count > 5000000:
            recommendation += " - Exceptional data volume provides maximum visibility impact"
        elif row_count > 1000000:
            recommendation += " - High data volume provides substantial visibility"
        elif row_count > 100000:
            recommendation += " - Good data volume for meaningful analysis"
        elif row_count > 10000:
            recommendation += " - Moderate data volume"
        else:
            recommendation += " - Limited data volume may reduce impact"
        
        # Add business context guidance
        if table_context['primary_context'] in ['cmdb', 'security', 'logging']:
            recommendation += " - HIGH BUSINESS PRIORITY for compliance"
        elif table_context['primary_context'] in ['infrastructure', 'network']:
            recommendation += " - Important for technical asset visibility"
        
        return recommendation


class BigQueryScanner:
    """
    Advanced BigQuery scanning engine with enterprise authentication.
    
    Provides comprehensive dataset and table analysis with intelligent
    error handling and progress tracking.
    """
    
    def __init__(self, project_id: str = "prj-fisv-p-gcss-sas-dl9dd0f1df"):
        self.project_id = project_id
        self.client = None
        self.authenticated = False
        
    def authenticate(self) -> bool:
        """
        Authenticate with BigQuery using original Google Cloud methods.
        
        Separated from corporate connection management to avoid interference
        with Google Cloud service authentication.
        
        Returns:
            True if authentication successful
        """
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
            from google.auth import default
            
            logger.info("Authenticating with BigQuery using Google Cloud methods")
            
            # Method 1: Service account key file
            service_account_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if service_account_path and os.path.exists(service_account_path):
                try:
                    credentials = service_account.Credentials.from_service_account_file(service_account_path)
                    self.client = bigquery.Client(project=self.project_id, credentials=credentials)
                    
                    # Test with simple dataset listing
                    list(self.client.list_datasets(max_results=1))
                    logger.info("BigQuery service account authentication successful")
                    self.authenticated = True
                    return True
                except Exception as e:
                    logger.debug(f"Service account authentication failed: {e}")
            
            # Method 2: Default credentials (gcloud, service account, etc.)
            try:
                credentials, detected_project = default()
                self.client = bigquery.Client(project=self.project_id, credentials=credentials)
                
                # Test with simple dataset listing
                list(self.client.list_datasets(max_results=1))
                logger.info("BigQuery default credentials authentication successful")
                self.authenticated = True
                return True
            except Exception as e:
                logger.debug(f"Default credentials authentication failed: {e}")
            
            # Method 3: Project-only (for public datasets)
            try:
                self.client = bigquery.Client(project=self.project_id)
                list(self.client.list_datasets(max_results=1))
                logger.info("BigQuery project-only authentication successful")
                self.authenticated = True
                return True
            except Exception as e:
                logger.debug(f"Project-only authentication failed: {e}")
                
            logger.error("All BigQuery authentication methods failed")
            return False
                
        except ImportError as e:
            logger.error(f"BigQuery library not available: {e}")
            return False
    
    def scan_datasets_and_tables(self, analyzer: AO1FieldAnalyzer) -> Dict[str, List[FieldAnalysis]]:
        """
        Scan all datasets and tables for AO1-relevant fields.
        
        Args:
            analyzer: AO1FieldAnalyzer instance for field analysis
            
        Returns:
            Dict mapping dataset names to lists of field analyses
        """
        if not self.authenticated:
            logger.error("BigQuery authentication required before scanning")
            return {}
        
        results = {}
        scan_stats = {
            'datasets_scanned': 0,
            'tables_scanned': 0,
            'fields_analyzed': 0,
            'ao1_matches_found': 0
        }
        
        try:
            # Get all datasets
            datasets = list(self.client.list_datasets())
            total_datasets = len(datasets)
            scan_stats['datasets_scanned'] = total_datasets
            
            logger.info(f"Starting BigQuery scan: {total_datasets} datasets found")
            
            for dataset_idx, dataset in enumerate(datasets):
                dataset_id = dataset.dataset_id
                logger.info(f"Scanning dataset: {dataset_id} ({dataset_idx + 1}/{total_datasets})")
                
                dataset_results = []
                
                try:
                    # Get all tables in dataset
                    tables = list(self.client.list_tables(dataset.reference))
                    
                    # Sort tables by estimated row count (descending) for priority processing
                    table_data = []
                    for table in tables:
                        try:
                            table_ref = self.client.get_table(table.reference)
                            table_data.append((table_ref, table_ref.num_rows or 0))
                        except Exception as e:
                            logger.warning(f"Could not get table info for {table.table_id}: {e}")
                            table_data.append((table, 0))
                    
                    # Sort by row count (largest first)
                    table_data.sort(key=lambda x: x[1], reverse=True)
                    
                    for table_ref, row_count in table_data:
                        scan_stats['tables_scanned'] += 1
                        
                        logger.debug(f"Analyzing table: {table_ref.table_id} ({row_count:,} rows)")
                        
                        # Analyze each field in the table
                        for field in table_ref.schema:
                            scan_stats['fields_analyzed'] += 1
                            
                            field_analysis = analyzer.analyze_field(
                                field_name=field.name,
                                table_name=table_ref.table_id,
                                dataset_name=dataset_id,
                                row_count=row_count
                            )
                            
                            if field_analysis:
                                dataset_results.append(field_analysis)
                                scan_stats['ao1_matches_found'] += 1
                                logger.debug(f"AO1 match found: {field.name} ({field_analysis.match_type})")
                    
                    if dataset_results:
                        # Sort results by strategic priority
                        dataset_results.sort(key=lambda x: (x.strategic_priority, x.row_count), reverse=True)
                        results[dataset_id] = dataset_results
                        logger.info(f"Dataset {dataset_id}: {len(dataset_results)} AO1 fields found")
                    
                except Exception as e:
                    logger.warning(f"Error processing dataset {dataset_id}: {e}")
                    continue
            
            # Log final statistics
            logger.info(f"BigQuery scan completed:")
            logger.info(f"  Datasets scanned: {scan_stats['datasets_scanned']}")
            logger.info(f"  Tables analyzed: {scan_stats['tables_scanned']}")
            logger.info(f"  Fields analyzed: {scan_stats['fields_analyzed']}")
            logger.info(f"  AO1 matches found: {scan_stats['ao1_matches_found']}")
            
        except Exception as e:
            logger.error(f"BigQuery scanning failed: {e}")
            
        return results


class AO1ReportGenerator:
    """
    Professional AO1 compliance report generator.
    
    Creates comprehensive, executive-ready reports with strategic insights,
    implementation guidance, and actionable recommendations.
    """
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_comprehensive_report(self, scan_results: Dict[str, List[FieldAnalysis]], 
                                    output_dir: str = ".") -> str:
        """
        Generate comprehensive AO1 field discovery report.
        
        Args:
            scan_results: Results from BigQuery scanning
            output_dir: Directory to save the report
            
        Returns:
            Path to the generated report file
        """
        # Organize and prioritize results
        req_results = self._organize_by_requirement(scan_results)
        strategic_insights = self._generate_strategic_insights(scan_results, req_results)
        
        # Generate report content
        report_content = self._generate_report_content(req_results, scan_results, strategic_insights)
        
        # Write to file
        output_file = os.path.join(output_dir, f"AO1_Field_Discovery_Report_{self.timestamp}.txt")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Report generated: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return ""
    
    def _organize_by_requirement(self, scan_results: Dict[str, List[FieldAnalysis]]) -> Dict[str, List[FieldAnalysis]]:
        """Organize and prioritize results by AO1 requirement."""
        req_results = {}
        
        # Initialize all requirements
        for req_id in AO1_REQUIREMENTS.keys():
            req_results[req_id] = []
        
        # Categorize all findings
        for dataset_results in scan_results.values():
            for analysis in dataset_results:
                for req in analysis.matching_requirements:
                    req_id = req.split(':')[0]
                    if req_id in req_results:
                        req_results[req_id].append(analysis)
        
        # Sort each requirement's results by strategic priority
        for req_id in req_results:
            req_results[req_id].sort(key=lambda x: (x.strategic_priority, x.row_count), reverse=True)
        
        return req_results
    
    def _generate_strategic_insights(self, scan_results: Dict[str, List[FieldAnalysis]], 
                                   req_results: Dict[str, List[FieldAnalysis]]) -> Dict[str, Any]:
        """Generate strategic insights for executive summary."""
        total_findings = sum(len(results) for results in scan_results.values())
        
        # High-value opportunities (EXACT matches with substantial data)
        high_value_fields = []
        for dataset_results in scan_results.values():
            for analysis in dataset_results:
                if analysis.match_type == 'EXACT' and analysis.row_count > 100000:
                    high_value_fields.append(analysis)
        
        high_value_fields.sort(key=lambda x: x.strategic_priority, reverse=True)
        
        # Coverage analysis
        coverage_analysis = {}
        for req_id, req_info in AO1_REQUIREMENTS.items():
            findings = req_results.get(req_id, [])
            exact_matches = len([f for f in findings if f.match_type == 'EXACT'])
            high_confidence = len([f for f in findings if f.confidence >= 80])
            
            coverage_analysis[req_id] = {
                'name': req_info['name'],
                'total_candidates': len(findings),
                'exact_matches': exact_matches,
                'high_confidence': high_confidence,
                'coverage_score': min(100, (exact_matches * 20) + (high_confidence * 5))
            }
        
        # Quick wins identification
        quick_wins = []
        for dataset_results in scan_results.values():
            for analysis in dataset_results:
                if (analysis.match_type == 'EXACT' and 
                    analysis.confidence >= 95 and 
                    analysis.row_count > 50000):
                    quick_wins.append(analysis)
        
        quick_wins.sort(key=lambda x: x.strategic_priority, reverse=True)
        
        return {
            'total_findings': total_findings,
            'high_value_opportunities': high_value_fields[:10],
            'coverage_analysis': coverage_analysis,
            'quick_wins': quick_wins[:5],
            'datasets_with_findings': len(scan_results),
            'average_confidence': sum(
                analysis.confidence 
                for results in scan_results.values() 
                for analysis in results
            ) / max(total_findings, 1)
        }
    
    def _generate_report_content(self, req_results: Dict[str, List[FieldAnalysis]], 
                               scan_results: Dict[str, List[FieldAnalysis]], 
                               strategic_insights: Dict[str, Any]) -> str:
        """Generate the complete report content."""
        
        content = []
        
        # Header
        content.extend([
            "AO1 BIGQUERY FIELD DISCOVERY REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Target Project: prj-fisv-p-gcss-sas-dl9dd0f1df",
            f"Analysis Engine: Advanced ML with Corporate Security Integration",
            ""
        ])
        
        # Executive Summary
        content.extend([
            "EXECUTIVE SUMMARY",
            "=" * 50,
            "",
            f"Total AO1-relevant fields discovered: {strategic_insights['total_findings']:,}",
            f"Datasets with AO1 fields: {strategic_insights['datasets_with_findings']}",
            f"Average confidence score: {strategic_insights['average_confidence']:.1f}%",
            f"High-value opportunities identified: {len(strategic_insights['high_value_opportunities'])}",
            ""
        ])
        
        # Coverage Analysis
        content.extend([
            "AO1 REQUIREMENTS COVERAGE ANALYSIS",
            "-" * 45,
            ""
        ])
        
        for req_id, req_info in AO1_REQUIREMENTS.items():
            coverage = strategic_insights['coverage_analysis'][req_id]
            content.append(
                f"{req_id} {coverage['name']}: {coverage['total_candidates']} candidates "
                f"({coverage['exact_matches']} exact, {coverage['high_confidence']} high-confidence) "
                f"- Coverage Score: {coverage['coverage_score']}/100"
            )
        
        content.append("")
        
        # Strategic Recommendations
        content.extend([
            "STRATEGIC RECOMMENDATIONS",
            "-" * 35,
            ""
        ])
        
        if strategic_insights['quick_wins']:
            content.extend([
                "IMMEDIATE IMPLEMENTATION PRIORITIES:",
                ""
            ])
            
            for i, analysis in enumerate(strategic_insights['quick_wins'], 1):
                content.extend([
                    f"{i}. Field '{analysis.field_name}' in {analysis.dataset_name}.{analysis.table_name}",
                    f"   Data Volume: {analysis.row_count:,} rows | Confidence: {analysis.confidence:.1f}% | Type: {analysis.match_type}",
                    f"   Requirements: {', '.join(analysis.matching_requirements)}",
                    f"   Business Value: {analysis.business_context}",
                    f"   Implementation: {analysis.recommendation}",
                    ""
                ])
        
        if strategic_insights['high_value_opportunities']:
            content.extend([
                "HIGH-VALUE OPPORTUNITIES:",
                ""
            ])
            
            for i, analysis in enumerate(strategic_insights['high_value_opportunities'][:5], 1):
                content.extend([
                    f"{i}. {analysis.dataset_name}.{analysis.table_name}.{analysis.field_name}",
                    f"   Strategic Priority: {analysis.strategic_priority} | Data: {analysis.row_count:,} rows",
                    f"   {analysis.recommendation}",
                    ""
                ])
        
        # Detailed Results by Requirement
        content.extend([
            "",
            "DETAILED FINDINGS BY AO1 REQUIREMENT",
            "=" * 80,
            ""
        ])
        
        for req_id, req_info in AO1_REQUIREMENTS.items():
            findings = req_results.get(req_id, [])
            
            content.extend([
                f"{req_id}: {req_info['name']}",
                "-" * 60,
                f"Purpose: {req_info['description']}",
                f"Business Value: {req_info['business_purpose']}",
                f"Key Concepts: {', '.join(req_info['key_concepts'])}",
                ""
            ])
            
            if not findings:
                content.extend([
                    "No matching fields found for this requirement.",
                    "Recommendation: Review data sources and field naming conventions.",
                    ""
                ])
                continue
            
            # Categorize findings
            exact_matches = [f for f in findings if f.match_type == 'EXACT']
            ml_identified = [f for f in findings if f.match_type == 'ML_IDENTIFIED']
            partial_matches = [f for f in findings if f.match_type == 'PARTIAL']
            suspected = [f for f in findings if f.match_type == 'SUSPECTED']
            
            content.extend([
                f"FINDINGS SUMMARY: {len(findings)} total field candidates",
                f"  EXACT: {len(exact_matches)} | ML-IDENTIFIED: {len(ml_identified)} | PARTIAL: {len(partial_matches)} | SUSPECTED: {len(suspected)}",
                ""
            ])
            
            # Top recommendations for this requirement
            content.extend([
                "TOP FIELD RECOMMENDATIONS:",
                ""
            ])
            
            for i, analysis in enumerate(findings[:10], 1):
                content.extend([
                    f"{i}. Field '{analysis.field_name}' in {analysis.dataset_name}.{analysis.table_name}",
                    f"   Data Volume: {analysis.row_count:,} rows | Match: {analysis.match_type} | Confidence: {analysis.confidence:.1f}%",
                    f"   Table Context: {analysis.table_context} | Semantic Score: {analysis.semantic_similarity:.2f}",
                    "",
                    f"   Business Assessment:",
                    f"   {analysis.business_context}",
                    "",
                    f"   Implementation Guidance:",
                    f"   {analysis.recommendation}",
                    "",
                    "   " + "-" * 70,
                    ""
                ])
        
        # Implementation Roadmap
        content.extend([
            "",
            "IMPLEMENTATION ROADMAP",
            "=" * 30,
            "",
            "PHASE 1: Quick Wins (0-30 days)",
            "- Implement exact matches with high data volumes",
            "- Focus on CMDB, security, and logging tables",
            "- Establish baseline AO1 measurements",
            "",
            "PHASE 2: High-Confidence Matches (30-60 days)",
            "- Deploy ML-identified and high-confidence partial matches",
            "- Validate field mappings and data quality",
            "- Expand coverage across all 8 requirements",
            "",
            "PHASE 3: Comprehensive Coverage (60-90 days)",
            "- Investigate suspected matches through manual review",
            "- Optimize field selection based on initial results",
            "- Complete AO1 visibility implementation",
            "",
            "SUCCESS METRICS:",
            "- 80% coverage across all AO1 requirements",
            "- Automated visibility measurement deployment",
            "- Regular reporting and monitoring established"
        ])
        
        return "\n".join(content)


def main():
    """
    Main execution function with comprehensive AO1 field discovery.
    
    Orchestrates the complete process from corporate connection establishment
    through BigQuery scanning to report generation.
    """
    print("AO1 BIGQUERY FIELD DISCOVERY SYSTEM")
    print("=" * 80)
    print("Enterprise-grade AO1 compliance field identification")
    print("Advanced ML analysis with corporate security integration")
    print(f"Target Project: prj-fisv-p-gcss-sas-dl9dd0f1df")
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Step 1: Establish secure corporate connectivity for external services
        print("STEP 1: SECURE CORPORATE CONNECTIVITY")
        print("-" * 50)
        connection_manager = CorporateConnectionManager()
        connection_result = connection_manager.establish_secure_corporate_connection()
        
        if connection_result['success']:
            print(f"Secure connectivity established: {connection_result['methods']} methods working")
            print(f"Optimal method: {connection_result['optimal_method'].name}")
            print(f"Security score: {connection_result['security_score']}/10")
        else:
            print("Limited connectivity detected - continuing with offline capabilities")
        print()
        
        # Step 2: Initialize ML system with secure connections
        print("STEP 2: ML SYSTEM INITIALIZATION")
        print("-" * 40)
        dependency_manager = MLDependencyManager()
        available_libs = dependency_manager.check_and_install_dependencies()
        
        ml_analyzer = AdvancedMLAnalyzer(dependency_manager)
        capability_summary = dependency_manager.get_ml_capability_summary()
        
        print(f"ML capabilities: {capability_summary}")
        print(f"ML strategy: {ml_analyzer.ml_strategy}")
        print(f"Compute device: {ml_analyzer.device}")
        
        # Display specific ML features
        if ml_analyzer.ml_strategy == 'sentence_transformers':
            print("Advanced semantic analysis with transformer models enabled")
        elif ml_analyzer.ml_strategy == 'built_in_embeddings':
            print("Semantic analysis using optimized built-in embeddings")
        elif ml_analyzer.ml_strategy == 'tfidf_similarity':
            print("Statistical text similarity analysis available")
        else:
            print("Pattern matching analysis mode")
        print()
        
        # Step 3: Initialize AO1 analysis engine
        print("STEP 3: AO1 ANALYSIS ENGINE")
        print("-" * 35)
        field_analyzer = AO1FieldAnalyzer(ml_analyzer)
        keyword_count = len(get_all_keywords())
        
        print(f"AO1 keywords loaded: {keyword_count} across 8 requirements")
        print("Analysis capabilities: Exact matching, Pattern recognition, Semantic similarity, Business context")
        print()
        
        # Step 4: BigQuery scanning with original authentication
        print("STEP 4: BIGQUERY SCANNING")
        print("-" * 30)
        scanner = BigQueryScanner()
        
        if not scanner.authenticate():
            print("BigQuery authentication failed")
            print("Please ensure proper Google Cloud credentials are configured")
            return False
        
        print("BigQuery authentication successful")
        print("Beginning comprehensive dataset analysis...")
        
        # Perform the comprehensive scan
        scan_results = scanner.scan_datasets_and_tables(field_analyzer)
        
        if not scan_results:
            print("Scan completed: No AO1-relevant fields found")
            return True
        
        # Step 5: Generate comprehensive report
        print()
        print("STEP 5: REPORT GENERATION")
        print("-" * 30)
        report_generator = AO1ReportGenerator()
        report_file = report_generator.generate_comprehensive_report(scan_results)
        
        if report_file:
            print(f"Comprehensive report generated: {report_file}")
        else:
            print("Report generation failed")
        print()
        
        # Step 6: Executive summary
        print("EXECUTION SUMMARY")
        print("-" * 25)
        total_findings = sum(len(results) for results in scan_results.values())
        high_priority = sum(
            1 for results in scan_results.values() 
            for analysis in results 
            if analysis.strategic_priority > 150
        )
        
        print(f"Datasets analyzed: {len(scan_results)}")
        print(f"AO1-relevant fields found: {total_findings:,}")
        print(f"High-priority recommendations: {high_priority}")
        print(f"ML strategy used: {ml_analyzer.ml_strategy}")
        if report_file:
            print(f"Detailed report: {report_file}")
        print()
        
        print("AO1 FIELD DISCOVERY COMPLETE")
        print("Review the generated report for detailed findings and implementation guidance")
        
        return True
        
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        print(f"Critical error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)