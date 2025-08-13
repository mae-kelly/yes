import os
import ssl
import urllib3
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ProxyTunnelManager:
    def __init__(self, proxy_host='proxy-na.fiserv.one', proxy_port=8080):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_url = f"http://{proxy_host}:{proxy_port}"
        self.is_configured = False
    
    def configure_proxy_tunnel(self):
        try:
            logger.info(f"Configuring Fiserv proxy tunnel: {self.proxy_url}")
            
            ssl._create_default_https_context = ssl._create_unverified_context
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            os.environ['SSL_CERT_FILE'] = ''
            os.environ['SSL_CERT_DIR'] = ''
            
            proxy_vars = {
                'HTTP_PROXY': self.proxy_url,
                'HTTPS_PROXY': self.proxy_url,
                'http_proxy': self.proxy_url,
                'https_proxy': self.proxy_url,
                'ALL_PROXY': self.proxy_url,
                'all_proxy': self.proxy_url
            }
            
            for var, value in proxy_vars.items():
                os.environ[var] = value
                logger.debug(f"Set {var}={value}")
            
            no_proxy = 'localhost,127.0.0.1,::1,.local'
            os.environ['NO_PROXY'] = no_proxy
            os.environ['no_proxy'] = no_proxy
            
            if self._test_proxy_connection():
                self.is_configured = True
                logger.info("Fiserv proxy tunnel configured successfully")
                return True
            else:
                logger.warning("Fiserv proxy tunnel configured but connectivity test failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to configure Fiserv proxy tunnel: {e}")
            return False
    
    def _test_proxy_connection(self):
        try:
            session = requests.Session()
            session.proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }
            session.verify = False
            
            response = session.get(
                'https://httpbin.org/ip',
                timeout=10,
                headers={'User-Agent': 'HyperIntelligent-Discovery/1.0'}
            )
            
            if response.status_code == 200:
                logger.info(f"Fiserv proxy connectivity test passed: {response.json()}")
                return True
            else:
                logger.warning(f"Fiserv proxy test returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.debug(f"Fiserv proxy connectivity test failed: {e}")
            return False
    
    def get_proxy_config(self) -> Dict[str, str]:
        return {
            'http': self.proxy_url,
            'https': self.proxy_url
        }
    
    def create_proxy_session(self) -> requests.Session:
        session = requests.Session()
        session.proxies.update(self.get_proxy_config())
        session.verify = False
        
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

def setup_model_download_proxy():
    proxy_manager = ProxyTunnelManager()
    
    if proxy_manager.configure_proxy_tunnel():
        logger.info("Fiserv model download proxy tunnel is ready")
        return proxy_manager
    else:
        logger.warning("Fiserv proxy setup failed, downloads may not work in restricted environments")
        return None

def download_with_proxy(url: str, proxy_manager: ProxyTunnelManager = None, **kwargs):
    if proxy_manager and proxy_manager.is_configured:
        session = proxy_manager.create_proxy_session()
        return session.get(url, **kwargs)
    else:
        return requests.get(url, **kwargs)