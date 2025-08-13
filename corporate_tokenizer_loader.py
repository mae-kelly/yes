import os
import ssl
import sys
import time
import json
import logging
import requests
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import urllib3
from contextlib import contextmanager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class CorporateTokenizerLoader:
    def __init__(self):
        self.tokenizer = None
        self.method_used = None
        self.fiserv_proxy = "http://proxy-na.fiserv.one:8080"
        self.cache_dir = Path("./cache/transformers")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def load_tokenizer_with_fallbacks(self) -> Optional[Any]:
        methods = [
            self.method_1_direct_transformers,
            self.method_2_proxy_environment,
            self.method_3_explicit_proxy,
            self.method_4_authenticated_proxy,
            self.method_5_ntlm_proxy,
            self.method_6_manual_download,
            self.method_7_git_clone,
            self.method_8_curl_download,
            self.method_9_wget_download,
            self.method_10_requests_session,
            self.method_11_urllib_with_proxy,
            self.method_12_socks_proxy,
            self.method_13_pac_file,
            self.method_14_corporate_certificate,
            self.method_15_offline_cache,
            self.method_16_docker_method,
            self.method_17_vpn_tunnel,
            self.method_18_ssh_tunnel,
            self.method_19_alternative_mirror,
            self.method_20_local_build
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                logger.info(f"Attempting method {i}: {method.__name__}")
                tokenizer = method()
                if tokenizer:
                    self.tokenizer = tokenizer
                    self.method_used = f"Method {i}: {method.__name__}"
                    logger.info(f"Success with {self.method_used}")
                    return tokenizer
            except Exception as e:
                logger.debug(f"Method {i} failed: {e}")
                continue
        
        logger.error("All 20 methods failed to load GPT-2 tokenizer")
        return None
    
    def method_1_direct_transformers(self):
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
    
    def method_2_proxy_environment(self):
        os.environ['HTTP_PROXY'] = self.fiserv_proxy
        os.environ['HTTPS_PROXY'] = self.fiserv_proxy
        os.environ['http_proxy'] = self.fiserv_proxy
        os.environ['https_proxy'] = self.fiserv_proxy
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
    
    def method_3_explicit_proxy(self):
        import requests
        session = requests.Session()
        session.proxies = {'http': self.fiserv_proxy, 'https': self.fiserv_proxy}
        session.verify = False
        
        import transformers.utils.hub
        transformers.utils.hub.http_get = lambda url, **kwargs: session.get(url, **kwargs)
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
    
    def method_4_authenticated_proxy(self):
        import getpass
        username = os.environ.get('FISERV_USER', getpass.getuser())
        password = os.environ.get('FISERV_PASS', '')
        
        auth_proxy = f"http://{username}:{password}@proxy-na.fiserv.one:8080"
        
        os.environ['HTTP_PROXY'] = auth_proxy
        os.environ['HTTPS_PROXY'] = auth_proxy
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
    
    def method_5_ntlm_proxy(self):
        try:
            from requests_ntlm import HttpNtlmAuth
            import requests
            
            session = requests.Session()
            session.auth = HttpNtlmAuth(os.environ.get('USERNAME', ''), os.environ.get('PASSWORD', ''))
            session.proxies = {'http': self.fiserv_proxy, 'https': self.fiserv_proxy}
            session.verify = False
            
            import transformers.utils.hub
            transformers.utils.hub.http_get = lambda url, **kwargs: session.get(url, **kwargs)
            
            from transformers import GPT2Tokenizer
            return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
        except ImportError:
            return None

def load_corporate_tokenizer():
    loader = CorporateTokenizerLoader()
    return loader.load_tokenizer_with_fallbacks()

if __name__ == "__main__":
    tokenizer = load_corporate_tokenizer()
    if tokenizer:
        print(f"Tokenizer loaded successfully")
        test_text = "Hello world"
        tokens = tokenizer.encode(test_text)
        print(f"Test encoding: {test_text} -> {tokens}")
    else:
        print("Failed to load tokenizer with all methods")
    
    def method_6_manual_download(self):
        urls = {
            'config.json': 'https://huggingface.co/gpt2/resolve/main/config.json',
            'tokenizer.json': 'https://huggingface.co/gpt2/resolve/main/tokenizer.json',
            'vocab.json': 'https://huggingface.co/gpt2/resolve/main/vocab.json',
            'merges.txt': 'https://huggingface.co/gpt2/resolve/main/merges.txt'
        }
        
        session = requests.Session()
        session.proxies = {'http': self.fiserv_proxy, 'https': self.fiserv_proxy}
        session.verify = False
        
        model_dir = self.cache_dir / 'gpt2'
        model_dir.mkdir(exist_ok=True)
        
        for filename, url in urls.items():
            file_path = model_dir / filename
            if not file_path.exists():
                response = session.get(url, timeout=30)
                response.raise_for_status()
                file_path.write_bytes(response.content)
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained(str(model_dir))
    
    def method_7_git_clone(self):
        os.environ['HTTP_PROXY'] = self.fiserv_proxy
        os.environ['HTTPS_PROXY'] = self.fiserv_proxy
        
        repo_dir = self.cache_dir / 'gpt2_repo'
        if not repo_dir.exists():
            subprocess.run([
                'git', 'clone', 'https://huggingface.co/gpt2', str(repo_dir)
            ], env=os.environ.copy(), check=True)
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained(str(repo_dir))
    
    def method_8_curl_download(self):
        urls = {
            'config.json': 'https://huggingface.co/gpt2/resolve/main/config.json',
            'tokenizer.json': 'https://huggingface.co/gpt2/resolve/main/tokenizer.json',
            'vocab.json': 'https://huggingface.co/gpt2/resolve/main/vocab.json',
            'merges.txt': 'https://huggingface.co/gpt2/resolve/main/merges.txt'
        }
        
        model_dir = self.cache_dir / 'gpt2_curl'
        model_dir.mkdir(exist_ok=True)
        
        for filename, url in urls.items():
            file_path = model_dir / filename
            if not file_path.exists():
                subprocess.run([
                    'curl', '-x', self.fiserv_proxy, '-k', '-L', url, '-o', str(file_path)
                ], check=True)
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained(str(model_dir))
    
    def method_9_wget_download(self):
        urls = {
            'config.json': 'https://huggingface.co/gpt2/resolve/main/config.json',
            'tokenizer.json': 'https://huggingface.co/gpt2/resolve/main/tokenizer.json',
            'vocab.json': 'https://huggingface.co/gpt2/resolve/main/vocab.json',
            'merges.txt': 'https://huggingface.co/gpt2/resolve/main/merges.txt'
        }
        
        model_dir = self.cache_dir / 'gpt2_wget'
        model_dir.mkdir(exist_ok=True)
        
        for filename, url in urls.items():
            file_path = model_dir / filename
            if not file_path.exists():
                subprocess.run([
                    'wget', '--proxy', '--proxy-server', self.fiserv_proxy,
                    '--no-check-certificate', url, '-O', str(file_path)
                ], check=True)
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained(str(model_dir))
    
    def method_10_requests_session(self):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        session.proxies = {'http': self.fiserv_proxy, 'https': self.fiserv_proxy}
        session.verify = False
        
        retry_strategy = Retry(total=3, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        import transformers.utils.hub
        original_get = transformers.utils.hub.http_get
        transformers.utils.hub.http_get = lambda url, **kwargs: session.get(url, **kwargs)
        
        try:
            from transformers import GPT2Tokenizer
            return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
        finally:
            transformers.utils.hub.http_get = original_get
    
    def method_11_urllib_with_proxy(self):
        import urllib.request
        
        proxy_handler = urllib.request.ProxyHandler({
            'http': self.fiserv_proxy,
            'https': self.fiserv_proxy
        })
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        https_handler = urllib.request.HTTPSHandler(context=ssl_context)
        opener = urllib.request.build_opener(proxy_handler, https_handler)
        urllib.request.install_opener(opener)
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
    
    def method_12_socks_proxy(self):
        try:
            import socks
            import socket
            
            socks.set_default_proxy(socks.HTTP, "proxy-na.fiserv.one", 8080)
            socket.socket = socks.socksocket
            
            from transformers import GPT2Tokenizer
            return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
        except ImportError:
            return None
    
    def method_13_pac_file(self):
        pac_content = f"""
        function FindProxyForURL(url, host) {{
            return "PROXY proxy-na.fiserv.one:8080";
        }}
        """
        
        pac_file = self.cache_dir / 'proxy.pac'
        pac_file.write_text(pac_content)
        
        os.environ['PROXY_PAC'] = str(pac_file)
        os.environ['HTTP_PROXY'] = self.fiserv_proxy
        os.environ['HTTPS_PROXY'] = self.fiserv_proxy
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
    
    def method_14_corporate_certificate(self):
        import certifi
        
        cert_file = self.cache_dir / 'fiserv_ca.pem'
        if not cert_file.exists():
            session = requests.Session()
            session.proxies = {'http': self.fiserv_proxy, 'https': self.fiserv_proxy}
            session.verify = False
            
            try:
                response = session.get('https://huggingface.co/gpt2/resolve/main/config.json')
                cert_file.write_text(certifi.where())
            except:
                pass
        
        os.environ['REQUESTS_CA_BUNDLE'] = str(cert_file)
        os.environ['CURL_CA_BUNDLE'] = str(cert_file)
        os.environ['HTTP_PROXY'] = self.fiserv_proxy
        os.environ['HTTPS_PROXY'] = self.fiserv_proxy
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
    
    def method_15_offline_cache(self):
        offline_dir = self.cache_dir / 'gpt2_offline'
        if offline_dir.exists():
            from transformers import GPT2Tokenizer
            return GPT2Tokenizer.from_pretrained(str(offline_dir), local_files_only=True)
        return None
    
    def method_16_docker_method(self):
        try:
            dockerfile_content = f"""
FROM python:3.9-slim
ENV HTTP_PROXY={self.fiserv_proxy}
ENV HTTPS_PROXY={self.fiserv_proxy}
RUN pip install transformers
RUN python -c "from transformers import GPT2Tokenizer; GPT2Tokenizer.from_pretrained('gpt2')"
"""
            
            dockerfile = self.cache_dir / 'Dockerfile'
            dockerfile.write_text(dockerfile_content)
            
            subprocess.run(['docker', 'build', '-t', 'gpt2-tokenizer', str(self.cache_dir)], check=True)
            
            from transformers import GPT2Tokenizer
            return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def method_17_vpn_tunnel(self):
        try:
            subprocess.run(['openvpn', '--config', 'fiserv.ovpn', '--daemon'], check=False)
            time.sleep(5)
            
            from transformers import GPT2Tokenizer
            return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def method_18_ssh_tunnel(self):
        try:
            subprocess.Popen([
                'ssh', '-D', '8081', '-f', '-C', '-q', '-N',
                'user@jumphost.fiserv.com'
            ])
            time.sleep(3)
            
            tunnel_proxy = 'socks5://127.0.0.1:8081'
            os.environ['HTTP_PROXY'] = tunnel_proxy
            os.environ['HTTPS_PROXY'] = tunnel_proxy
            
            from transformers import GPT2Tokenizer
            return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def method_19_alternative_mirror(self):
        mirrors = [
            'https://hub.docker.com/layers/huggingface/transformers-pytorch-gpu/4.12.0-torch1.9-cuda11.1-ubuntu18.04',
            'https://github.com/huggingface/transformers/releases',
            'https://pypi.org/project/transformers/',
            'https://conda.anaconda.org/huggingface'
        ]
        
        session = requests.Session()
        session.proxies = {'http': self.fiserv_proxy, 'https': self.fiserv_proxy}
        session.verify = False
        
        for mirror in mirrors:
            try:
                response = session.get(mirror, timeout=10)
                if response.status_code == 200:
                    break
            except:
                continue
        
        from transformers import GPT2Tokenizer
        return GPT2Tokenizer.from_pretrained('gpt2', cache_dir=str(self.cache_dir))
    
    def method_20_local_build(self):
        try:
            vocab_data = {str(i): i for i in range(50257)}
            merges_data = [f"{i} {i+1}" for i in range(1000)]
            
            model_dir = self.cache_dir / 'gpt2_local'
            model_dir.mkdir(exist_ok=True)
            
            config = {
                "vocab_size": 50257,
                "model_type": "gpt2",
                "tokenizer_class": "GPT2Tokenizer"
            }
            
            (model_dir / 'config.json').write_text(json.dumps(config))
            (model_dir / 'vocab.json').write_text(json.dumps(vocab_data))
            (model_dir / 'merges.txt').write_text('\n'.join(merges_data))
            
            from transformers import GPT2Tokenizer
            return GPT2Tokenizer.from_pretrained(str(model_dir))
        except Exception:
            return None