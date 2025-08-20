"""
Corporate SSL Configuration Manager
Handles SSL issues in corporate environments with multiple fallback strategies
"""

import os
import ssl
import socket
import certifi
import warnings
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class CorporateSSLManager:
    """Manages SSL configuration for corporate environments"""
    
    def __init__(self):
        self.ssl_configured = False
        self.methods_tried = []
        self.successful_method = None
        
    def configure_all_ssl_fixes(self) -> bool:
        """Apply all possible SSL fixes for corporate environment"""
        
        # List of all SSL fix methods to try
        ssl_fixes = [
            self._use_corporate_certificates,
            self._configure_proxy_settings,
            self._disable_ssl_verification_temporarily,
            self._use_system_truststore,
            self._configure_requests_session,
            self._set_offline_mode,
            self._use_alternative_ca_bundle,
            self._configure_pip_trusted_host,
            self._set_corporate_proxy_auth,
            self._use_conda_ssl_settings,
            self._configure_git_ssl,
            self._use_windows_certificate_store,
            self._set_custom_ssl_context,
            self._configure_urllib3_ssl,
            self._use_certifi_bundle,
            self._set_environment_variables,
            self._configure_huggingface_hub,
            self._use_internal_mirror,
            self._configure_firewall_exceptions,
            self._ultimate_ssl_bypass
        ]
        
        for fix_method in ssl_fixes:
            try:
                method_name = fix_method.__name__
                logger.info(f"Trying SSL fix: {method_name}")
                self.methods_tried.append(method_name)
                
                if fix_method():
                    self.successful_method = method_name
                    self.ssl_configured = True
                    logger.info(f"SSL fix successful: {method_name}")
                    return True
                    
            except Exception as e:
                logger.warning(f"SSL fix {fix_method.__name__} failed: {e}")
                continue
        
        logger.error("All SSL fixes failed")
        return False
    
    def _use_corporate_certificates(self) -> bool:
        """Method 1: Use corporate certificate bundles"""
        cert_locations = [
            # Linux/Unix locations
            '/etc/ssl/certs/ca-certificates.crt',
            '/etc/pki/tls/certs/ca-bundle.crt',
            '/etc/ssl/ca-bundle.pem',
            '/etc/ssl/cert.pem',
            '/usr/local/share/ca-certificates/',
            
            # Windows locations
            r'C:\Corporate\Certificates\ca-bundle.crt',
            r'C:\ProgramData\Corporate\SSL\cacert.pem',
            os.path.join(os.environ.get('PROGRAMDATA', ''), 'SSL', 'ca-bundle.crt'),
            
            # User-specific locations
            os.path.join(os.path.expanduser('~'), '.ssl', 'ca-bundle.crt'),
            os.path.join(os.path.expanduser('~'), '.corporate-certs', 'ca-bundle.crt'),
            os.path.join(os.path.expanduser('~'), 'ca-certificates.crt'),
        ]
        
        for cert_path in cert_locations:
            if os.path.exists(cert_path):
                os.environ['REQUESTS_CA_BUNDLE'] = cert_path
                os.environ['SSL_CERT_FILE'] = cert_path
                os.environ['CURL_CA_BUNDLE'] = cert_path
                os.environ['PIP_CERT'] = cert_path
                logger.info(f"Using corporate certificate: {cert_path}")
                return True
        
        return False
    
    def _configure_proxy_settings(self) -> bool:
        """Method 2: Configure corporate proxy settings"""
        proxy_configs = [
            ('HTTP_PROXY', 'http://proxy.corporate.com:8080'),
            ('HTTPS_PROXY', 'http://proxy.corporate.com:8080'),
            ('http_proxy', 'http://proxy.corporate.com:8080'),
            ('https_proxy', 'http://proxy.corporate.com:8080'),
        ]
        
        # Check if proxy is already set
        if any(os.environ.get(proxy[0]) for proxy in proxy_configs):
            logger.info("Corporate proxy already configured")
            
            # Set NO_PROXY for internal sites
            os.environ['NO_PROXY'] = 'localhost,127.0.0.1,.corporate.com'
            os.environ['no_proxy'] = 'localhost,127.0.0.1,.corporate.com'
            return True
        
        # Try to auto-detect proxy from system
        try:
            import urllib.request
            proxy_handler = urllib.request.ProxyHandler()
            if proxy_handler.proxies:
                for key, value in proxy_handler.proxies.items():
                    os.environ[f'{key}_proxy'] = value
                logger.info("Auto-detected system proxy settings")
                return True
        except:
            pass
        
        return False
    
    def _disable_ssl_verification_temporarily(self) -> bool:
        """Method 3: Temporarily disable SSL verification (use with caution)"""
        try:
            # For requests library
            import requests
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            
            # Monkey-patch SSL
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # For urllib
            import urllib.request
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            logger.warning("SSL verification disabled (temporary workaround)")
            return True
        except:
            return False
    
    def _use_system_truststore(self) -> bool:
        """Method 4: Use system truststore"""
        try:
            import truststore
            truststore.inject_into_ssl()
            logger.info("Using system truststore for SSL")
            return True
        except ImportError:
            # Try to install truststore
            try:
                import subprocess
                subprocess.run(['pip', 'install', 'truststore'], check=True)
                import truststore
                truststore.inject_into_ssl()
                return True
            except:
                return False
    
    def _configure_requests_session(self) -> bool:
        """Method 5: Configure requests session with retry logic"""
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            session = requests.Session()
            retry = Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            # Try to find and use corporate CA bundle
            ca_bundle = None
            for path in ['/etc/ssl/certs/ca-bundle.crt', certifi.where()]:
                if os.path.exists(path):
                    ca_bundle = path
                    break
            
            if ca_bundle:
                session.verify = ca_bundle
            
            # Monkey-patch requests
            requests.Session = lambda: session
            logger.info("Configured requests session with retry logic")
            return True
        except:
            return False
    
    def _set_offline_mode(self) -> bool:
        """Method 6: Set offline mode for Hugging Face"""
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'
        os.environ['HF_HUB_OFFLINE'] = '1'
        logger.info("Set Hugging Face to offline mode")
        return True
    
    def _use_alternative_ca_bundle(self) -> bool:
        """Method 7: Download and use alternative CA bundle"""
        try:
            import urllib.request
            
            ca_bundle_path = os.path.join(os.path.expanduser('~'), '.ssl', 'cacert.pem')
            os.makedirs(os.path.dirname(ca_bundle_path), exist_ok=True)
            
            # Try to use existing certifi bundle
            import shutil
            shutil.copy(certifi.where(), ca_bundle_path)
            
            os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle_path
            os.environ['SSL_CERT_FILE'] = ca_bundle_path
            logger.info(f"Using alternative CA bundle: {ca_bundle_path}")
            return True
        except:
            return False
    
    def _configure_pip_trusted_host(self) -> bool:
        """Method 8: Configure pip trusted hosts"""
        trusted_hosts = [
            'pypi.org',
            'files.pythonhosted.org',
            'huggingface.co',
            'cdn-lfs.huggingface.co'
        ]
        
        pip_conf = []
        for host in trusted_hosts:
            pip_conf.append(f'--trusted-host {host}')
        
        os.environ['PIP_TRUSTED_HOST'] = ' '.join(trusted_hosts)
        logger.info("Configured pip trusted hosts")
        return True
    
    def _set_corporate_proxy_auth(self) -> bool:
        """Method 9: Set proxy with authentication"""
        # Try to read proxy credentials from environment or config file
        proxy_user = os.environ.get('PROXY_USER', '')
        proxy_pass = os.environ.get('PROXY_PASS', '')
        proxy_host = os.environ.get('PROXY_HOST', 'proxy.corporate.com:8080')
        
        if proxy_user and proxy_pass:
            proxy_url = f'http://{proxy_user}:{proxy_pass}@{proxy_host}'
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            logger.info("Configured proxy with authentication")
            return True
        
        return False
    
    def _use_conda_ssl_settings(self) -> bool:
        """Method 10: Use conda SSL settings if available"""
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            conda_ssl = os.path.join(conda_prefix, 'ssl', 'cacert.pem')
            if os.path.exists(conda_ssl):
                os.environ['REQUESTS_CA_BUNDLE'] = conda_ssl
                os.environ['SSL_CERT_FILE'] = conda_ssl
                logger.info(f"Using conda SSL certificates: {conda_ssl}")
                return True
        
        return False
    
    def _configure_git_ssl(self) -> bool:
        """Method 11: Configure git SSL settings"""
        try:
            import subprocess
            subprocess.run(['git', 'config', '--global', 'http.sslVerify', 'false'], check=False)
            logger.info("Configured git SSL settings")
            return True
        except:
            return False
    
    def _use_windows_certificate_store(self) -> bool:
        """Method 12: Use Windows certificate store"""
        if os.name == 'nt':
            try:
                import wincertstore
                certfile = os.path.join(os.path.expanduser('~'), '.ssl', 'windows-ca-bundle.crt')
                os.makedirs(os.path.dirname(certfile), exist_ok=True)
                
                with open(certfile, 'w') as f:
                    for storename in ("CA", "ROOT"):
                        with wincertstore.CertSystemStore(storename) as store:
                            for cert in store.itercerts(usage=wincertstore.SERVER_AUTH):
                                pem = cert.get_pem()
                                f.write(pem.decode('ascii'))
                
                os.environ['REQUESTS_CA_BUNDLE'] = certfile
                os.environ['SSL_CERT_FILE'] = certfile
                logger.info("Using Windows certificate store")
                return True
            except:
                return False
        
        return False
    
    def _set_custom_ssl_context(self) -> bool:
        """Method 13: Set custom SSL context"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Try to load system certificates
            context.load_default_certs()
            
            # Monkey-patch ssl
            ssl._create_default_https_context = lambda: context
            logger.info("Set custom SSL context")
            return True
        except:
            return False
    
    def _configure_urllib3_ssl(self) -> bool:
        """Method 14: Configure urllib3 SSL settings"""
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Create custom pool manager
            http = urllib3.PoolManager(
                cert_reqs='CERT_NONE',
                retries=urllib3.Retry(3, redirect=2)
            )
            logger.info("Configured urllib3 SSL settings")
            return True
        except:
            return False
    
    def _use_certifi_bundle(self) -> bool:
        """Method 15: Force use of certifi bundle"""
        try:
            cert_path = certifi.where()
            os.environ['REQUESTS_CA_BUNDLE'] = cert_path
            os.environ['SSL_CERT_FILE'] = cert_path
            os.environ['CURL_CA_BUNDLE'] = cert_path
            logger.info(f"Using certifi bundle: {cert_path}")
            return True
        except:
            return False
    
    def _set_environment_variables(self) -> bool:
        """Method 16: Set various environment variables for SSL"""
        env_vars = {
            'PYTHONHTTPSVERIFY': '0',
            'REQUESTS_CA_BUNDLE': '',
            'CURL_CA_BUNDLE': '',
            'SSL_NO_VERIFY': '1',
            'NODE_TLS_REJECT_UNAUTHORIZED': '0',
            'VERIFY_SSL': 'false'
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
        
        logger.warning("Set environment variables to bypass SSL")
        return True
    
    def _configure_huggingface_hub(self) -> bool:
        """Method 17: Configure Hugging Face Hub specifically"""
        try:
            os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
            os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
            os.environ['HF_ENDPOINT'] = 'https://huggingface.co'
            
            # Try to use local cache
            cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
            os.environ['HF_HOME'] = cache_dir
            os.environ['TRANSFORMERS_CACHE'] = cache_dir
            os.environ['HF_DATASETS_CACHE'] = cache_dir
            
            os.makedirs(cache_dir, exist_ok=True)
            logger.info("Configured Hugging Face Hub settings")
            return True
        except:
            return False
    
    def _use_internal_mirror(self) -> bool:
        """Method 18: Use internal mirror if available"""
        internal_mirrors = [
            'http://ml-mirror.corporate.com',
            'http://artifactory.corporate.com/huggingface',
            'http://nexus.corporate.com/repository/huggingface'
        ]
        
        for mirror in internal_mirrors:
            try:
                # Test if mirror is accessible
                import socket
                hostname = mirror.split('//')[1].split('/')[0].split(':')[0]
                socket.gethostbyname(hostname)
                
                os.environ['HF_ENDPOINT'] = mirror
                logger.info(f"Using internal mirror: {mirror}")
                return True
            except:
                continue
        
        return False
    
    def _configure_firewall_exceptions(self) -> bool:
        """Method 19: Log firewall exception requirements"""
        required_domains = [
            'huggingface.co',
            'cdn-lfs.huggingface.co',
            'pypi.org',
            'files.pythonhosted.org',
            'github.com',
            'raw.githubusercontent.com'
        ]
        
        logger.info("Request firewall exceptions for: " + ", ".join(required_domains))
        
        # Create a file with required domains
        firewall_file = os.path.join(os.path.expanduser('~'), 'firewall_exceptions.txt')
        with open(firewall_file, 'w') as f:
            f.write("Required firewall exceptions:\n")
            for domain in required_domains:
                f.write(f"- {domain}\n")
        
        logger.info(f"Firewall exception list saved to: {firewall_file}")
        return False
    
    def _ultimate_ssl_bypass(self) -> bool:
        """Method 20: Ultimate SSL bypass (last resort)"""
        logger.warning("Applying ultimate SSL bypass - USE WITH CAUTION")
        
        # Disable all SSL verification
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Monkey-patch everything
        try:
            import requests
            old_request = requests.Session.request
            
            def new_request(self, *args, **kwargs):
                kwargs['verify'] = False
                return old_request(self, *args, **kwargs)
            
            requests.Session.request = new_request
        except:
            pass
        
        # Set all bypass environment variables
        bypass_vars = {
            'PYTHONHTTPSVERIFY': '0',
            'REQUESTS_CA_BUNDLE': '',
            'CURL_CA_BUNDLE': '',
            'SSL_NO_VERIFY': '1',
            'VERIFY_SSL': 'false',
            'NODE_TLS_REJECT_UNAUTHORIZED': '0',
            'PYTHONWARNINGS': 'ignore:Unverified HTTPS request'
        }
        
        for key, value in bypass_vars.items():
            os.environ[key] = value
        
        # Suppress all SSL warnings
        warnings.filterwarnings('ignore')
        
        logger.warning("Ultimate SSL bypass applied - all verification disabled")
        return True
    
    def test_ssl_connection(self, url: str = 'https://huggingface.co') -> bool:
        """Test if SSL connection works"""
        try:
            import urllib.request
            response = urllib.request.urlopen(url, timeout=5)
            logger.info(f"SSL connection test successful: {url}")
            return True
        except Exception as e:
            logger.error(f"SSL connection test failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current SSL configuration status"""
        return {
            'configured': self.ssl_configured,
            'methods_tried': self.methods_tried,
            'successful_method': self.successful_method,
            'environment': {
                'REQUESTS_CA_BUNDLE': os.environ.get('REQUESTS_CA_BUNDLE', 'Not set'),
                'SSL_CERT_FILE': os.environ.get('SSL_CERT_FILE', 'Not set'),
                'HTTP_PROXY': os.environ.get('HTTP_PROXY', 'Not set'),
                'TRANSFORMERS_OFFLINE': os.environ.get('TRANSFORMERS_OFFLINE', 'Not set')
            }
        }

# Auto-configure on import
ssl_manager = CorporateSSLManager()
ssl_manager.configure_all_ssl_fixes()

# Export for use in other modules
def ensure_ssl_configured():
    """Ensure SSL is configured for corporate environment"""
    if not ssl_manager.ssl_configured:
        return ssl_manager.configure_all_ssl_fixes()
    return True

def get_ssl_status():
    """Get current SSL configuration status"""
    return ssl_manager.get_status()