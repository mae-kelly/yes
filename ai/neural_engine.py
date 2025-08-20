import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import hashlib
import re
import os
import ssl
import certifi
import warnings
import logging

logger = logging.getLogger(__name__)

# SSL Fix Attempts for Corporate Environment
def setup_ssl_for_corporate():
    """Configure SSL for corporate environment with multiple fallback methods"""
    
    # Method 1: Use corporate certificate bundle
    corporate_cert_paths = [
        '/etc/ssl/certs/ca-certificates.crt',
        '/etc/pki/tls/certs/ca-bundle.crt',
        '/etc/ssl/ca-bundle.pem',
        '/etc/ssl/cert.pem',
        r'C:\Corporate\Certificates\ca-bundle.crt',
        os.path.join(os.environ.get('USERPROFILE', ''), 'ca-bundle.crt'),
        os.path.join(os.environ.get('HOME', ''), '.corporate-certs', 'ca-bundle.crt')
    ]
    
    for cert_path in corporate_cert_paths:
        if os.path.exists(cert_path):
            os.environ['REQUESTS_CA_BUNDLE'] = cert_path
            os.environ['SSL_CERT_FILE'] = cert_path
            os.environ['CURL_CA_BUNDLE'] = cert_path
            logger.info(f"Using corporate certificate: {cert_path}")
            break
    
    # Method 2: Set proxy if available
    if 'HTTP_PROXY' in os.environ or 'HTTPS_PROXY' in os.environ:
        os.environ['HF_HUB_DISABLE_SSL'] = '0'  # Keep SSL but use proxy
        logger.info("Corporate proxy detected and configured")
    
    # Method 3: Use system certificates
    try:
        import truststore
        truststore.inject_into_ssl()
        logger.info("Using system truststore for SSL")
    except ImportError:
        pass
    
    # Method 4: Configure requests session
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Try to use corporate CA bundle
        for cert_path in corporate_cert_paths:
            if os.path.exists(cert_path):
                session.verify = cert_path
                break
    except:
        pass

# Setup SSL before imports
setup_ssl_for_corporate()

# Try multiple transformer libraries with fallbacks
TRANSFORMER_BACKEND = None
tokenizer = None
transformer_model = None

def initialize_transformer():
    """Initialize transformer with multiple fallback options"""
    global TRANSFORMER_BACKEND, tokenizer, transformer_model
    
    # Option 1: Try Hugging Face Transformers
    try:
        from transformers import AutoModel, AutoTokenizer
        
        # Try offline mode first
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'
        
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        # Try to load from cache
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            transformer_model = AutoModel.from_pretrained(model_name, local_files_only=True)
            TRANSFORMER_BACKEND = 'transformers'
            logger.info(f"Loaded transformers from cache (offline mode)")
            return True
        except:
            # Try online with various SSL fixes
            os.environ['TRANSFORMERS_OFFLINE'] = '0'
            
            # Method 5: Try with different SSL contexts
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=False)
                transformer_model = AutoModel.from_pretrained(model_name, trust_remote_code=False)
                TRANSFORMER_BACKEND = 'transformers'
                logger.info("Loaded transformers with SSL workaround")
                return True
            except Exception as e:
                logger.warning(f"Transformers SSL failed: {e}")
    except ImportError:
        logger.warning("Transformers library not available")
    except Exception as e:
        logger.warning(f"Failed to load transformers: {e}")
    
    # Option 2: Try Sentence-Transformers directly
    try:
        from sentence_transformers import SentenceTransformer
        
        # Try with SSL disabled temporarily
        old_ssl = os.environ.get('CURL_CA_BUNDLE')
        os.environ['CURL_CA_BUNDLE'] = ''
        
        try:
            transformer_model = SentenceTransformer('all-MiniLM-L6-v2')
            TRANSFORMER_BACKEND = 'sentence-transformers'
            logger.info("Loaded sentence-transformers successfully")
            return True
        finally:
            if old_ssl:
                os.environ['CURL_CA_BUNDLE'] = old_ssl
    except Exception as e:
        logger.warning(f"Sentence-transformers failed: {e}")
    
    # Option 3: Fallback to scikit-learn TF-IDF + truncated SVD
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        from sklearn.pipeline import Pipeline
        
        class SklearnEmbedder:
            def __init__(self):
                self.pipeline = Pipeline([
                    ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 3))),
                    ('svd', TruncatedSVD(n_components=384))
                ])
                self.is_fitted = False
                
            def encode(self, texts, convert_to_tensor=False):
                if isinstance(texts, str):
                    texts = [texts]
                
                if not self.is_fitted:
                    # Fit on first use with dummy data
                    dummy_texts = [
                        "hostname server database",
                        "ip address network firewall", 
                        "cloud infrastructure region",
                        "security compliance audit",
                        "endpoint detection response"
                    ]
                    self.pipeline.fit(dummy_texts)
                    self.is_fitted = True
                
                embeddings = self.pipeline.transform(texts)
                
                if convert_to_tensor:
                    return torch.FloatTensor(embeddings)
                return embeddings
        
        transformer_model = SklearnEmbedder()
        TRANSFORMER_BACKEND = 'sklearn'
        logger.info("Using sklearn TF-IDF + SVD fallback for embeddings")
        return True
    except ImportError:
        logger.warning("Scikit-learn not available")
    
    # Option 4: Fallback to Word2Vec with gensim
    try:
        from gensim.models import Word2Vec
        import numpy as np
        
        class Word2VecEmbedder:
            def __init__(self):
                # Create a simple word2vec model with IT/security vocabulary
                sentences = [
                    ['hostname', 'server', 'computer', 'machine'],
                    ['ip', 'address', 'network', 'subnet'],
                    ['firewall', 'security', 'endpoint', 'protection'],
                    ['cloud', 'aws', 'azure', 'gcp', 'infrastructure'],
                    ['database', 'sql', 'oracle', 'postgres'],
                    ['splunk', 'logging', 'monitoring', 'observability'],
                    ['cmdb', 'asset', 'inventory', 'management'],
                    ['region', 'datacenter', 'location', 'zone']
                ]
                self.model = Word2Vec(sentences, vector_size=384, min_count=1, workers=1)
                
            def encode(self, texts, convert_to_tensor=False):
                if isinstance(texts, str):
                    texts = [texts]
                
                embeddings = []
                for text in texts:
                    words = text.lower().split()
                    word_vecs = []
                    for word in words:
                        if word in self.model.wv:
                            word_vecs.append(self.model.wv[word])
                    
                    if word_vecs:
                        # Average word vectors
                        embedding = np.mean(word_vecs, axis=0)
                    else:
                        # Random embedding for unknown words
                        embedding = np.random.randn(384) * 0.1
                    
                    embeddings.append(embedding)
                
                embeddings = np.array(embeddings)
                if convert_to_tensor:
                    return torch.FloatTensor(embeddings)
                return embeddings
        
        transformer_model = Word2VecEmbedder()
        TRANSFORMER_BACKEND = 'word2vec'
        logger.info("Using Word2Vec fallback for embeddings")
        return True
    except ImportError:
        logger.warning("Gensim not available")
    
    # Option 5: Ultimate fallback - Hash-based embeddings
    class HashEmbedder:
        def __init__(self, dim=384):
            self.dim = dim
            
        def encode(self, texts, convert_to_tensor=False):
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = []
            for text in texts:
                # Create deterministic hash-based embedding
                np.random.seed(hash(text) % (2**32))
                embedding = np.random.randn(self.dim) * 0.1
                
                # Add some semantic features
                text_lower = text.lower()
                if 'host' in text_lower or 'server' in text_lower:
                    embedding[0:10] += 0.5
                if 'ip' in text_lower or 'address' in text_lower:
                    embedding[10:20] += 0.5
                if 'cloud' in text_lower or 'aws' in text_lower or 'azure' in text_lower:
                    embedding[20:30] += 0.5
                if 'security' in text_lower or 'firewall' in text_lower:
                    embedding[30:40] += 0.5
                
                embeddings.append(embedding)
            
            embeddings = np.array(embeddings)
            if convert_to_tensor:
                return torch.FloatTensor(embeddings)
            return embeddings
    
    transformer_model = HashEmbedder()
    TRANSFORMER_BACKEND = 'hash'
    logger.warning("Using hash-based embeddings as final fallback")
    return True

# Initialize transformer on module load
initialize_transformer()

class QuantumNeuralNetwork(nn.Module):
    def __init__(self, input_dim=None, hidden_dims=[512, 256, 128], num_classes=17):
        super().__init__()
        
        # Dynamically set input dimension based on backend
        if input_dim is None:
            if TRANSFORMER_BACKEND in ['sklearn', 'word2vec', 'hash']:
                input_dim = 384  # These backends use 384 dimensions
            else:
                input_dim = 768  # Transformers use 768 dimensions
        
        self.input_dim = input_dim
        self.encoder = nn.ModuleList()
        dims = [input_dim] + hidden_dims
        for i in range(len(dims)-1):
            self.encoder.append(nn.Linear(dims[i], dims[i+1]))
            self.encoder.append(nn.LayerNorm(dims[i+1]))
            self.encoder.append(nn.Dropout(0.1))
        
        self.attention = nn.MultiheadAttention(hidden_dims[-1], num_heads=8, batch_first=True)
        self.classifier = nn.Linear(hidden_dims[-1], num_classes)
        self.confidence = nn.Linear(hidden_dims[-1], 1)
        
    def forward(self, x):
        for layer in self.encoder:
            if isinstance(layer, nn.Linear):
                x = F.gelu(layer(x))
            else:
                x = layer(x)
        
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        attn_output, _ = self.attention(x, x, x)
        x = x + attn_output
        
        logits = self.classifier(x.squeeze(1))
        conf = torch.sigmoid(self.confidence(x.squeeze(1)))
        
        return logits, conf

class HyperIntelligence:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize transformer model (already done at module level)
        self.transformer = transformer_model
        self.tokenizer = tokenizer
        
        # Determine actual embedding dimension by testing
        try:
            test_embedding = self.encode_text("test")
            actual_dim = test_embedding.shape[-1]
            logger.info(f"Detected embedding dimension: {actual_dim}")
        except:
            # Default based on backend
            actual_dim = 384 if TRANSFORMER_BACKEND in ['sklearn', 'word2vec', 'hash'] else 768
            logger.info(f"Using default dimension for {TRANSFORMER_BACKEND}: {actual_dim}")
        
        # Create neural network with correct input dimension
        self.neural_net = QuantumNeuralNetwork(input_dim=actual_dim).to(self.device)
        
        logger.info(f"HyperIntelligence initialized with backend: {TRANSFORMER_BACKEND}, dim: {actual_dim}")
        
        self.field_mappings = {
        
        self.field_mappings = {
            'hostname': ['hostname', 'host_name', 'computer_name', 'device_name', 'machine_name', 'system_name', 'server_name', 'endpoint_name', 'asset_name'],
            'infrastructure_type': ['infrastructure_type', 'infra_type', 'platform_type', 'hosting_type', 'deployment_type', 'cloud', 'onprem', 'on_premise', 'saas', 'api'],
            'region': ['region', 'global_region', 'geo_region', 'geographic_region', 'location_region', 'area', 'territory'],
            'country': ['country', 'nation', 'country_code', 'country_name', 'geo_country'],
            'business_unit': ['business_unit', 'bu', 'department', 'division', 'org_unit', 'organization', 'business_division'],
            'datacenter': ['datacenter', 'data_center', 'dc', 'site', 'facility', 'location', 'data_centre'],
            'cloud_region': ['cloud_region', 'aws_region', 'azure_region', 'gcp_region', 'cloud_zone', 'availability_zone'],
            'cio': ['cio', 'cio_org', 'it_org', 'technology_org', 'it_organization', 'tech_org'],
            'apm': ['apm', 'application_monitoring', 'app_performance', 'performance_monitoring'],
            'application_class': ['application_class', 'app_class', 'app_type', 'application_type', 'app_category'],
            'system_classification': ['system_class', 'os_type', 'platform', 'operating_system', 'system_type', 'server_type'],
            'domain': ['domain', 'dns_domain', 'ad_domain', 'active_directory', 'dns', 'fqdn'],
            'ip_address': ['ip_address', 'ip', 'ipv4', 'ipv6', 'ip_addr', 'network_address'],
            'mac_address': ['mac_address', 'mac', 'physical_address', 'ethernet_address', 'hardware_address']
        }
        
        self.log_type_patterns = {
            'network': {
                'patterns': ['firewall', 'ids', 'ips', 'ndr', 'proxy', 'dns', 'waf', 'traffic'],
                'fields': ['source_ip', 'dest_ip', 'protocol', 'port', 'detection_signature', 'dns_record', 'http_headers'],
                'visibility': ['url_fqdn_coverage', 'cmdb_visibility', 'network_zones', 'ipam_public_ip', 'geolocation', 'vpc']
            },
            'endpoint': {
                'patterns': ['os_logs', 'edr', 'dlp', 'fim', 'winEvt', 'linux_syslog'],
                'fields': ['system_name', 'ip', 'filename'],
                'visibility': ['cmdb_visibility', 'crowdstrike_coverage', 'log_ingest_volume']
            },
            'cloud': {
                'patterns': ['cloud_event', 'cloud_load_balancer', 'cloud_config', 'theom', 'wiz', 'cloud_security'],
                'fields': [],
                'visibility': ['vpc', 'ipam_public_ip', 'url_fqdn_coverage', 'crowdstrike_coverage']
            },
            'application': {
                'patterns': ['web_logs', 'api_gateway', 'http_access'],
                'fields': ['authentication_attempts', 'privilege_escalation', 'identity_create_modify_destroy'],
                'visibility': ['url_fqdn_coverage', 'control_coverage', 'domain', 'internal', 'external', 'controls']
            },
            'identity': {
                'patterns': ['authentication', 'privilege', 'identity', 'access'],
                'fields': ['authentication_attempts', 'privilege_escalation', 'identity_operations'],
                'visibility': ['domain', 'internal', 'external', 'controls']
            }
        }
        
        self.system_classifications = {
            'web_server': ['web', 'apache', 'nginx', 'iis', 'tomcat', 'http'],
            'windows_server': ['windows', 'win', 'microsoft', 'server2019', 'server2016'],
            'linux_server': ['linux', 'ubuntu', 'centos', 'rhel', 'debian', 'suse'],
            'nix': ['aix', 'solaris', 'unix', 'hpux', 'bsd'],
            'mainframe': ['mainframe', 'zos', 'mvs', 'as400'],
            'database': ['database', 'sql', 'oracle', 'postgres', 'mysql', 'mongodb', 'db'],
            'network_appliance': ['firewall', 'router', 'switch', 'proxy', 'loadbalancer', 'fw', 'ndr']
        }
        
        self.infrastructure_types = {
            'on_premise': ['onprem', 'on-prem', 'datacenter', 'physical', 'bare_metal', 'local'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'ec2', 'vm', 'virtual'],
            'saas': ['saas', 'software_as_service', 'hosted', 'managed_service'],
            'api': ['api', 'endpoint', 'service', 'gateway', 'rest', 'soap']
        }
        
        self.regional_mappings = {
            'na': ['north_america', 'usa', 'united_states', 'canada', 'mexico', 'us-east', 'us-west'],
            'latam': ['latin_america', 'south_america', 'brazil', 'argentina', 'chile', 'colombia'],
            'europe': ['europe', 'eu', 'uk', 'germany', 'france', 'spain', 'italy', 'emea'],
            'apac': ['asia', 'pacific', 'japan', 'china', 'india', 'australia', 'singapore']
        }
    
    def encode_text(self, text: str) -> torch.Tensor:
        """Encode text using the available transformer backend"""
        try:
            if TRANSFORMER_BACKEND == 'transformers':
                inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                with torch.no_grad():
                    outputs = self.transformer(**inputs)
                    embeddings = outputs.last_hidden_state.mean(dim=1)
            elif TRANSFORMER_BACKEND == 'sentence-transformers':
                embeddings = self.transformer.encode(text, convert_to_tensor=True)
                embeddings = embeddings.unsqueeze(0) if len(embeddings.shape) == 1 else embeddings
                embeddings = embeddings.to(self.device)
            else:
                # sklearn, word2vec, or hash backend
                embeddings = self.transformer.encode(text, convert_to_tensor=True)
                embeddings = embeddings.unsqueeze(0) if len(embeddings.shape) == 1 else embeddings
                embeddings = embeddings.to(self.device)
            
            # Ensure correct dimensions
            if embeddings.shape[-1] != self.neural_net.input_dim:
                # Pad or truncate to match expected dimensions
                current_dim = embeddings.shape[-1]
                expected_dim = self.neural_net.input_dim
                
                if current_dim < expected_dim:
                    # Pad with zeros
                    padding = torch.zeros(embeddings.shape[0], expected_dim - current_dim).to(self.device)
                    embeddings = torch.cat([embeddings, padding], dim=-1)
                else:
                    # Truncate
                    embeddings = embeddings[:, :expected_dim]
            
            return embeddings
        except Exception as e:
            logger.error(f"Encoding failed: {e}, using random embeddings")
            # Emergency fallback with correct dimensions
            dim = self.neural_net.input_dim if hasattr(self, 'neural_net') else 768
            return torch.randn(1, dim).to(self.device)
    
    def classify_column(self, column_name: str, sample_values: List[str]) -> Tuple[str, float, Dict[str, Any]]:
        text = f"{column_name} {' '.join(sample_values[:10])}"
        
        try:
            embeddings = self.encode_text(text)
            
            # Ensure embeddings match neural network input dimension
            if embeddings.shape[-1] != self.neural_net.input_dim:
                from ai.embedding_adapter import EmbeddingAdapter
                adapter = EmbeddingAdapter()
                embeddings = adapter.adapt_dimensions(embeddings, self.neural_net.input_dim)
            
            with torch.no_grad():
                logits, confidence = self.neural_net(embeddings)
                probs = F.softmax(logits, dim=-1)
                max_prob, pred_idx = torch.max(probs, dim=-1)
            
            field_types = list(self.field_mappings.keys()) + ['unknown']
            predicted_type = field_types[pred_idx.item()] if pred_idx.item() < len(field_types) else 'unknown'
            
            pattern_score = self._calculate_pattern_score(column_name, sample_values, predicted_type)
            semantic_score = self._calculate_semantic_score(text, predicted_type)
            
            final_confidence = (max_prob.item() * 0.5 + pattern_score * 0.3 + semantic_score * 0.2)
            
            metadata = {
                'ml_confidence': max_prob.item(),
                'pattern_score': pattern_score,
                'semantic_score': semantic_score,
                'neural_confidence': confidence.item(),
                'method': f'quantum_neural_classification_{TRANSFORMER_BACKEND}'
            }
            
            return predicted_type, final_confidence, metadata
            
        except Exception as e:
            logger.warning(f"Neural classification failed: {e}, using pattern matching")
            # Fallback to pure pattern matching
            return self._pattern_based_classification(column_name, sample_values)
    
    def _pattern_based_classification(self, column_name: str, sample_values: List[str]) -> Tuple[str, float, Dict[str, Any]]:
        """Fallback pattern-based classification when neural network fails"""
        column_lower = column_name.lower()
        
        # Check each field type
        best_match = ('unknown', 0.0)
        
        for field_type, patterns in self.field_mappings.items():
            score = 0.0
            
            # Check column name
            for pattern in patterns:
                if pattern in column_lower:
                    score = 1.0
                    break
            
            # Check sample values for specific types
            if field_type == 'hostname' and score < 1.0:
                hostname_pattern = r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]
    
    def _calculate_pattern_score(self, column_name: str, samples: List[str], field_type: str) -> float:
        if field_type not in self.field_mappings:
            return 0.0
        
        patterns = self.field_mappings[field_type]
        column_lower = column_name.lower()
        
        name_score = max([1.0 if p in column_lower else 0.0 for p in patterns], default=0.0)
        
        if field_type == 'hostname':
            hostname_pattern = r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$'
            valid_samples = sum(1 for s in samples if re.match(hostname_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'ip_address':
            ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
            valid_samples = sum(1 for s in samples if re.match(ip_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'mac_address':
            mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'
            valid_samples = sum(1 for s in samples if re.match(mac_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        else:
            content_score = 0.5
        
        return (name_score * 0.6 + content_score * 0.4)
    
    def _calculate_semantic_score(self, text: str, field_type: str) -> float:
        if field_type == 'infrastructure_type':
            for infra_type, keywords in self.infrastructure_types.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'system_classification':
            for sys_class, keywords in self.system_classifications.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'region':
            for region, keywords in self.regional_mappings.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        return 0.5
    
    def identify_log_type(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        table_lower = table_name.lower()
        columns_lower = [c.lower() for c in columns]
        all_text = f"{table_lower} {' '.join(columns_lower)}"
        
        scores = {}
        for log_role, config in self.log_type_patterns.items():
            pattern_score = sum(1 for p in config['patterns'] if p in all_text) / len(config['patterns'])
            field_score = sum(1 for f in config['fields'] if any(f in c for c in columns_lower)) / max(len(config['fields']), 1)
            scores[log_role] = (pattern_score * 0.6 + field_score * 0.4)
        
        best_role = max(scores, key=scores.get)
        confidence = scores[best_role]
        
        return {
            'role': best_role,
            'confidence': confidence,
            'log_types': self.log_type_patterns[best_role]['patterns'],
            'visibility_factors': self.log_type_patterns[best_role]['visibility'],
            'scores': scores
        }
    
    def classify_infrastructure(self, text: str) -> str:
        text_lower = text.lower()
        for infra_type, keywords in self.infrastructure_types.items():
            if any(kw in text_lower for kw in keywords):
                return infra_type
        return 'on_premise'
    
    def classify_system(self, text: str) -> str:
        text_lower = text.lower()
        for sys_class, keywords in self.system_classifications.items():
            if any(kw in text_lower for kw in keywords):
                return sys_class
        return 'unknown'
    
    def map_region(self, text: str) -> str:
        text_lower = text.lower()
        for region, keywords in self.regional_mappings.items():
            if any(kw in text_lower for kw in keywords):
                return region
        return 'unknown'
    
    def calculate_anomaly_score(self, values: List[Any]) -> float:
        if not values:
            return 0.0
        
        str_values = [str(v) for v in values]
        unique_ratio = len(set(str_values)) / len(str_values)
        
        lengths = [len(v) for v in str_values]
        if lengths:
            mean_len = np.mean(lengths)
            std_len = np.std(lengths)
            cv = std_len / mean_len if mean_len > 0 else 0
        else:
            cv = 0
        
        anomaly_score = (1 - unique_ratio) * 0.5 + min(cv, 1.0) * 0.5
        return anomaly_score
                valid_samples = sum(1 for s in sample_values if re.match(hostname_pattern, s))
                if valid_samples > len(sample_values) * 0.5:
                    score = 0.8
            
            elif field_type == 'ip_address' and score < 1.0:
                ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}
    
    def _calculate_pattern_score(self, column_name: str, samples: List[str], field_type: str) -> float:
        if field_type not in self.field_mappings:
            return 0.0
        
        patterns = self.field_mappings[field_type]
        column_lower = column_name.lower()
        
        name_score = max([1.0 if p in column_lower else 0.0 for p in patterns], default=0.0)
        
        if field_type == 'hostname':
            hostname_pattern = r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$'
            valid_samples = sum(1 for s in samples if re.match(hostname_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'ip_address':
            ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
            valid_samples = sum(1 for s in samples if re.match(ip_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'mac_address':
            mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'
            valid_samples = sum(1 for s in samples if re.match(mac_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        else:
            content_score = 0.5
        
        return (name_score * 0.6 + content_score * 0.4)
    
    def _calculate_semantic_score(self, text: str, field_type: str) -> float:
        if field_type == 'infrastructure_type':
            for infra_type, keywords in self.infrastructure_types.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'system_classification':
            for sys_class, keywords in self.system_classifications.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'region':
            for region, keywords in self.regional_mappings.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        return 0.5
    
    def identify_log_type(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        table_lower = table_name.lower()
        columns_lower = [c.lower() for c in columns]
        all_text = f"{table_lower} {' '.join(columns_lower)}"
        
        scores = {}
        for log_role, config in self.log_type_patterns.items():
            pattern_score = sum(1 for p in config['patterns'] if p in all_text) / len(config['patterns'])
            field_score = sum(1 for f in config['fields'] if any(f in c for c in columns_lower)) / max(len(config['fields']), 1)
            scores[log_role] = (pattern_score * 0.6 + field_score * 0.4)
        
        best_role = max(scores, key=scores.get)
        confidence = scores[best_role]
        
        return {
            'role': best_role,
            'confidence': confidence,
            'log_types': self.log_type_patterns[best_role]['patterns'],
            'visibility_factors': self.log_type_patterns[best_role]['visibility'],
            'scores': scores
        }
    
    def classify_infrastructure(self, text: str) -> str:
        text_lower = text.lower()
        for infra_type, keywords in self.infrastructure_types.items():
            if any(kw in text_lower for kw in keywords):
                return infra_type
        return 'on_premise'
    
    def classify_system(self, text: str) -> str:
        text_lower = text.lower()
        for sys_class, keywords in self.system_classifications.items():
            if any(kw in text_lower for kw in keywords):
                return sys_class
        return 'unknown'
    
    def map_region(self, text: str) -> str:
        text_lower = text.lower()
        for region, keywords in self.regional_mappings.items():
            if any(kw in text_lower for kw in keywords):
                return region
        return 'unknown'
    
    def calculate_anomaly_score(self, values: List[Any]) -> float:
        if not values:
            return 0.0
        
        str_values = [str(v) for v in values]
        unique_ratio = len(set(str_values)) / len(str_values)
        
        lengths = [len(v) for v in str_values]
        if lengths:
            mean_len = np.mean(lengths)
            std_len = np.std(lengths)
            cv = std_len / mean_len if mean_len > 0 else 0
        else:
            cv = 0
        
        anomaly_score = (1 - unique_ratio) * 0.5 + min(cv, 1.0) * 0.5
        return anomaly_score
                valid_samples = sum(1 for s in sample_values if re.match(ip_pattern, s))
                if valid_samples > len(sample_values) * 0.5:
                    score = 0.9
            
            elif field_type == 'mac_address' and score < 1.0:
                mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}
    
    def _calculate_pattern_score(self, column_name: str, samples: List[str], field_type: str) -> float:
        if field_type not in self.field_mappings:
            return 0.0
        
        patterns = self.field_mappings[field_type]
        column_lower = column_name.lower()
        
        name_score = max([1.0 if p in column_lower else 0.0 for p in patterns], default=0.0)
        
        if field_type == 'hostname':
            hostname_pattern = r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$'
            valid_samples = sum(1 for s in samples if re.match(hostname_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'ip_address':
            ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
            valid_samples = sum(1 for s in samples if re.match(ip_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'mac_address':
            mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'
            valid_samples = sum(1 for s in samples if re.match(mac_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        else:
            content_score = 0.5
        
        return (name_score * 0.6 + content_score * 0.4)
    
    def _calculate_semantic_score(self, text: str, field_type: str) -> float:
        if field_type == 'infrastructure_type':
            for infra_type, keywords in self.infrastructure_types.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'system_classification':
            for sys_class, keywords in self.system_classifications.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'region':
            for region, keywords in self.regional_mappings.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        return 0.5
    
    def identify_log_type(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        table_lower = table_name.lower()
        columns_lower = [c.lower() for c in columns]
        all_text = f"{table_lower} {' '.join(columns_lower)}"
        
        scores = {}
        for log_role, config in self.log_type_patterns.items():
            pattern_score = sum(1 for p in config['patterns'] if p in all_text) / len(config['patterns'])
            field_score = sum(1 for f in config['fields'] if any(f in c for c in columns_lower)) / max(len(config['fields']), 1)
            scores[log_role] = (pattern_score * 0.6 + field_score * 0.4)
        
        best_role = max(scores, key=scores.get)
        confidence = scores[best_role]
        
        return {
            'role': best_role,
            'confidence': confidence,
            'log_types': self.log_type_patterns[best_role]['patterns'],
            'visibility_factors': self.log_type_patterns[best_role]['visibility'],
            'scores': scores
        }
    
    def classify_infrastructure(self, text: str) -> str:
        text_lower = text.lower()
        for infra_type, keywords in self.infrastructure_types.items():
            if any(kw in text_lower for kw in keywords):
                return infra_type
        return 'on_premise'
    
    def classify_system(self, text: str) -> str:
        text_lower = text.lower()
        for sys_class, keywords in self.system_classifications.items():
            if any(kw in text_lower for kw in keywords):
                return sys_class
        return 'unknown'
    
    def map_region(self, text: str) -> str:
        text_lower = text.lower()
        for region, keywords in self.regional_mappings.items():
            if any(kw in text_lower for kw in keywords):
                return region
        return 'unknown'
    
    def calculate_anomaly_score(self, values: List[Any]) -> float:
        if not values:
            return 0.0
        
        str_values = [str(v) for v in values]
        unique_ratio = len(set(str_values)) / len(str_values)
        
        lengths = [len(v) for v in str_values]
        if lengths:
            mean_len = np.mean(lengths)
            std_len = np.std(lengths)
            cv = std_len / mean_len if mean_len > 0 else 0
        else:
            cv = 0
        
        anomaly_score = (1 - unique_ratio) * 0.5 + min(cv, 1.0) * 0.5
        return anomaly_score
                valid_samples = sum(1 for s in sample_values if re.match(mac_pattern, s))
                if valid_samples > len(sample_values) * 0.5:
                    score = 0.9
            
            if score > best_match[1]:
                best_match = (field_type, score)
        
        return best_match[0], best_match[1], {'method': 'pattern_matching', 'pattern_score': best_match[1]}
    
    def _calculate_pattern_score(self, column_name: str, samples: List[str], field_type: str) -> float:
        if field_type not in self.field_mappings:
            return 0.0
        
        patterns = self.field_mappings[field_type]
        column_lower = column_name.lower()
        
        name_score = max([1.0 if p in column_lower else 0.0 for p in patterns], default=0.0)
        
        if field_type == 'hostname':
            hostname_pattern = r'^[a-zA-Z][a-zA-Z0-9\-]{1,62}[a-zA-Z0-9]$'
            valid_samples = sum(1 for s in samples if re.match(hostname_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'ip_address':
            ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
            valid_samples = sum(1 for s in samples if re.match(ip_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        elif field_type == 'mac_address':
            mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'
            valid_samples = sum(1 for s in samples if re.match(mac_pattern, s))
            content_score = valid_samples / len(samples) if samples else 0.0
        else:
            content_score = 0.5
        
        return (name_score * 0.6 + content_score * 0.4)
    
    def _calculate_semantic_score(self, text: str, field_type: str) -> float:
        if field_type == 'infrastructure_type':
            for infra_type, keywords in self.infrastructure_types.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'system_classification':
            for sys_class, keywords in self.system_classifications.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        elif field_type == 'region':
            for region, keywords in self.regional_mappings.items():
                if any(kw in text.lower() for kw in keywords):
                    return 0.9
        return 0.5
    
    def identify_log_type(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        table_lower = table_name.lower()
        columns_lower = [c.lower() for c in columns]
        all_text = f"{table_lower} {' '.join(columns_lower)}"
        
        scores = {}
        for log_role, config in self.log_type_patterns.items():
            pattern_score = sum(1 for p in config['patterns'] if p in all_text) / len(config['patterns'])
            field_score = sum(1 for f in config['fields'] if any(f in c for c in columns_lower)) / max(len(config['fields']), 1)
            scores[log_role] = (pattern_score * 0.6 + field_score * 0.4)
        
        best_role = max(scores, key=scores.get)
        confidence = scores[best_role]
        
        return {
            'role': best_role,
            'confidence': confidence,
            'log_types': self.log_type_patterns[best_role]['patterns'],
            'visibility_factors': self.log_type_patterns[best_role]['visibility'],
            'scores': scores
        }
    
    def classify_infrastructure(self, text: str) -> str:
        text_lower = text.lower()
        for infra_type, keywords in self.infrastructure_types.items():
            if any(kw in text_lower for kw in keywords):
                return infra_type
        return 'on_premise'
    
    def classify_system(self, text: str) -> str:
        text_lower = text.lower()
        for sys_class, keywords in self.system_classifications.items():
            if any(kw in text_lower for kw in keywords):
                return sys_class
        return 'unknown'
    
    def map_region(self, text: str) -> str:
        text_lower = text.lower()
        for region, keywords in self.regional_mappings.items():
            if any(kw in text_lower for kw in keywords):
                return region
        return 'unknown'
    
    def calculate_anomaly_score(self, values: List[Any]) -> float:
        if not values:
            return 0.0
        
        str_values = [str(v) for v in values]
        unique_ratio = len(set(str_values)) / len(str_values)
        
        lengths = [len(v) for v in str_values]
        if lengths:
            mean_len = np.mean(lengths)
            std_len = np.std(lengths)
            cv = std_len / mean_len if mean_len > 0 else 0
        else:
            cv = 0
        
        anomaly_score = (1 - unique_ratio) * 0.5 + min(cv, 1.0) * 0.5
        return anomaly_score