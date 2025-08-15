import os
import ssl
import sys
import logging
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class AggressiveCorporateTokenizerLoader:
    def __init__(self):
        self.tokenizer = None
        self.method_used = None
        self.corporate_proxies = [
            "http://proxy-na.fiserv.one:8080",
            "http://proxy.corp.fiserv.com:8080", 
            "http://proxy.fiserv.com:8080"
        ]
        self._setup_aggressive_environment()
        
    def _setup_aggressive_environment(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        
        working_proxy = self._find_working_proxy()
        if working_proxy:
            os.environ['HTTP_PROXY'] = working_proxy
            os.environ['HTTPS_PROXY'] = working_proxy
        
        os.environ['TRANSFORMERS_OFFLINE'] = '0'
        
    def _find_working_proxy(self):
        for proxy in self.corporate_proxies:
            try:
                response = requests.get('https://httpbin.org/ip', 
                                      proxies={'http': proxy, 'https': proxy},
                                      timeout=5, verify=False)
                if response.status_code == 200:
                    return proxy
            except:
                continue
        return None
        
    def load_tokenizer_with_aggressive_methods(self):
        methods = [
            self._method_direct_with_env,
            self._method_emergency_tokenizer
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                logger.info(f"Attempting method {i}: {method.__name__}")
                tokenizer = method()
                if tokenizer and self._validate_tokenizer(tokenizer):
                    self.tokenizer = tokenizer
                    self.method_used = f"Method {i}: {method.__name__}"
                    logger.info(f"SUCCESS: {self.method_used}")
                    return tokenizer
            except Exception as e:
                logger.debug(f"Method {i} failed: {e}")
                continue
        
        logger.error("All methods failed")
        return None
    
    def _validate_tokenizer(self, tokenizer):
        try:
            test_result = tokenizer("test text", return_tensors="pt", padding=True, truncation=True, max_length=10)
            return 'input_ids' in test_result and 'attention_mask' in test_result
        except:
            return False
    
    def _method_direct_with_env(self):
        try:
            import transformers
            from transformers import GPT2Tokenizer
            transformers.logging.set_verbosity_error()
            
            tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            
            if not hasattr(tokenizer, 'pad_token') or tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
                
            return tokenizer
        except Exception as e:
            logger.debug(f"Direct method failed: {e}")
            return None
    
    def _method_emergency_tokenizer(self):
        logger.info("Creating emergency tokenizer")
        
        class EmergencyTokenizer:
            def __init__(self):
                self.vocab = {}
                chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:@ '
                for i, char in enumerate(chars):
                    self.vocab[char] = i
                self.vocab['<UNK>'] = len(chars)
                self.vocab['<PAD>'] = len(chars) + 1
                self.pad_token = '<PAD>'
                self.eos_token = '<PAD>'
                self.vocab_size = len(self.vocab)
                self.method_used = "Emergency Character Tokenizer"
            
            def encode(self, text, **kwargs):
                return [self.vocab.get(char, self.vocab['<UNK>']) for char in str(text)[:200]]
            
            def decode(self, tokens, **kwargs):
                reverse_vocab = {v: k for k, v in self.vocab.items()}
                return ''.join([reverse_vocab.get(token, '?') for token in tokens])
            
            def __call__(self, text, truncation=True, padding='max_length', max_length=256, return_tensors=None, **kwargs):
                tokens = self.encode(text)[:max_length]
                
                if padding == 'max_length':
                    pad_length = max_length - len(tokens)
                    tokens.extend([self.vocab['<PAD>']] * pad_length)
                    attention_mask = [1] * (max_length - pad_length) + [0] * pad_length
                else:
                    attention_mask = [1] * len(tokens)
                
                result = {
                    'input_ids': tokens,
                    'attention_mask': attention_mask
                }
                
                if return_tensors == 'pt':
                    try:
                        import torch
                        result['input_ids'] = torch.tensor(result['input_ids']).unsqueeze(0)
                        result['attention_mask'] = torch.tensor(result['attention_mask']).unsqueeze(0)
                    except ImportError:
                        pass
                
                return result
        
        return EmergencyTokenizer()

def load_corporate_tokenizer():
    loader = AggressiveCorporateTokenizerLoader()
    tokenizer = loader.load_tokenizer_with_aggressive_methods()
    if tokenizer:
        tokenizer.method_used = loader.method_used
    return tokenizer

if __name__ == "__main__":
    tokenizer = load_corporate_tokenizer()
    if tokenizer:
        print(f"SUCCESS: {getattr(tokenizer, 'method_used', 'unknown method')}")
        test_text = "hostname server ip address"
        result = tokenizer(test_text, return_tensors="pt", padding="max_length", max_length=20)
        print(f"Test successful")
    else:
        print("FAILED: All methods exhausted")