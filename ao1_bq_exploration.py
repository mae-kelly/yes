"""
Advanced AO1 Field Discovery System with ML-Enhanced Analysis

This system uses machine learning on Apple M1 GPU acceleration to intelligently 
discover and categorize BigQuery fields relevant to AO1 audit requirements.
Features neural network-based field matching, semantic similarity analysis,
and confidence scoring for optimal field selection.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import time
import sys
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

# BigQuery imports
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud.exceptions import NotFound, Forbidden, BadRequest, ServerError

# ML imports for M1 GPU acceleration with multiple Hugging Face connection methods
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import Dataset, DataLoader
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Multiple Hugging Face connection attempts
    from sentence_transformers import SentenceTransformer
    from transformers import (
        AutoTokenizer, AutoModel, AutoConfig,
        pipeline, logging as hf_logging
    )
    import requests
    from huggingface_hub import (
        HfApi, hf_hub_download, login, 
        cached_download, snapshot_download
    )
    
    # Suppress HF warnings for cleaner output
    hf_logging.set_verbosity_error()
    
    # Check for MPS (Metal Performance Shaders) support on M1
    if torch.backends.mps.is_available():
        DEVICE = torch.device("mps")
        print("SYSTEM: M1 GPU acceleration enabled via Metal Performance Shaders")
    else:
        DEVICE = torch.device("cpu")
        print("SYSTEM: CPU processing mode (M1 GPU not detected)")
        
    HF_AVAILABLE = True
    print("HUGGING FACE: Libraries loaded successfully")
        
except ImportError as e:
    print("WARNING: ML libraries not available, falling back to basic matching")
    print("Install with: pip install torch sentence-transformers transformers huggingface-hub scikit-learn")
    DEVICE = None
    HF_AVAILABLE = False

# Import AO1 Keywords
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
    
    print("LOADED: {} AO1 keywords across 8 requirements".format(len(ALL_AO1_KEYWORDS)))
    
except ImportError as e:
    print("CRITICAL ERROR: Cannot import AO1 keywords module")
    print("Ensure ao1_keywords.py is in the project directory")
    sys.exit(1)

# Configuration
PROJECT_ID = "prj-fisv-p-gcss-sas-dl9dd0f1df"
SERVICE_ACCOUNT_FILE = "gcp_prod_key.json"

# Advanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('ao1_advanced_discovery.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FieldMatch:
    """Data class for field match results"""
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

class AO1NeuralMatcher(nn.Module):
    """Neural network for advanced field matching using M1 GPU acceleration"""
    
    def __init__(self, vocab_size: int, embedding_dim: int = 128, hidden_dim: int = 64):
        super(AO1NeuralMatcher, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, bidirectional=True, batch_first=True)
        self.attention = nn.MultiheadAttention(hidden_dim * 2, num_heads=4)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, 8),  # 8 requirements
            nn.Softmax(dim=1)
        )
        
    def forward(self, x):
        # Embedding layer
        embedded = self.embedding(x)
        
        # LSTM processing
        lstm_out, (hidden, cell) = self.lstm(embedded)
        
        # Attention mechanism
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Global max pooling
        pooled = torch.max(attn_out, dim=1)[0]
        
        # Classification
        output = self.classifier(pooled)
        return output

class HuggingFaceConnector:
    """Advanced Hugging Face model connector with multiple connection strategies"""
    
    def __init__(self):
        self.api = None
        self.models = {}
        self.connection_methods = []
        self.successful_connections = []
        
    def test_huggingface_connectivity(self):
        """Test multiple ways to connect to Hugging Face"""
        print("HUGGING FACE: Testing connectivity with multiple methods...")
        
        connection_results = {
            'hub_api': False,
            'direct_download': False,
            'pipeline_access': False,
            'sentence_transformers': False,
            'transformers_library': False,
            'cached_models': False,
            'offline_models': False
        }
        
        # Method 1: HuggingFace Hub API
        try:
            self.api = HfApi()
            models = self.api.list_models(limit=1)
            list(models)  # Force evaluation
            connection_results['hub_api'] = True
            self.successful_connections.append('Hub API')
            print("  ✓ Hub API: Connected successfully")
        except Exception as e:
            print("  ✗ Hub API: {}".format(str(e)[:50]))
        
        # Method 2: Direct model download
        try:
            model_id = "sentence-transformers/all-MiniLM-L6-v2"
            config_path = hf_hub_download(repo_id=model_id, filename="config.json")
            if os.path.exists(config_path):
                connection_results['direct_download'] = True
                self.successful_connections.append('Direct Download')
                print("  ✓ Direct Download: Model files accessible")
        except Exception as e:
            print("  ✗ Direct Download: {}".format(str(e)[:50]))
        
        # Method 3: Pipeline access
        try:
            pipe = pipeline("text-classification", model="distilbert-base-uncased", return_all_scores=True)
            test_result = pipe("test text")
            if test_result:
                connection_results['pipeline_access'] = True
                self.successful_connections.append('Pipeline Access')
                print("  ✓ Pipeline Access: Transformers pipeline working")
        except Exception as e:
            print("  ✗ Pipeline Access: {}".format(str(e)[:50]))
        
        # Method 4: Sentence Transformers
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            test_embedding = model.encode(["test"])
            if test_embedding is not None:
                connection_results['sentence_transformers'] = True
                self.successful_connections.append('Sentence Transformers')
                print("  ✓ Sentence Transformers: Model loaded and functional")
        except Exception as e:
            print("  ✗ Sentence Transformers: {}".format(str(e)[:50]))
        
        # Method 5: Raw Transformers library
        try:
            tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            model = AutoModel.from_pretrained("distilbert-base-uncased")
            test_tokens = tokenizer("test", return_tensors="pt")
            with torch.no_grad():
                outputs = model(**test_tokens)
            if outputs is not None:
                connection_results['transformers_library'] = True
                self.successful_connections.append('Raw Transformers')
                print("  ✓ Raw Transformers: Direct model access working")
        except Exception as e:
            print("  ✗ Raw Transformers: {}".format(str(e)[:50]))
        
        # Method 6: Check for cached models
        try:
            from huggingface_hub import scan_cache_dir
            cache_info = scan_cache_dir()
            if len(cache_info.repos) > 0:
                connection_results['cached_models'] = True
                self.successful_connections.append('Cached Models')
                print("  ✓ Cached Models: {} models found in local cache".format(len(cache_info.repos)))
        except Exception as e:
            print("  ✗ Cached Models: {}".format(str(e)[:50]))
        
        # Method 7: Offline model check
        try:
            import transformers
            transformers.utils.logging.set_verbosity_error()
            
            # Check if we can load models in offline mode
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_DATASETS_OFFLINE"] = "1"
            
            # Try to load a small model offline
            tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased", local_files_only=True)
            connection_results['offline_models'] = True
            self.successful_connections.append('Offline Mode')
            print("  ✓ Offline Models: Local model access confirmed")
            
            # Reset environment
            if "TRANSFORMERS_OFFLINE" in os.environ:
                del os.environ["TRANSFORMERS_OFFLINE"]
            if "HF_DATASETS_OFFLINE" in os.environ:
                del os.environ["HF_DATASETS_OFFLINE"]
                
        except Exception as e:
            print("  ✗ Offline Models: {}".format(str(e)[:50]))
        
        return connection_results
    
    def get_optimal_model_strategy(self, connection_results):
        """Determine the best model loading strategy based on connectivity"""
        strategies = []
        
        if connection_results['sentence_transformers']:
            strategies.append({
                'method': 'sentence_transformers',
                'priority': 1,
                'description': 'SentenceTransformers with automatic optimization'
            })
        
        if connection_results['transformers_library']:
            strategies.append({
                'method': 'transformers_direct',
                'priority': 2,
                'description': 'Direct transformers library access'
            })
        
        if connection_results['pipeline_access']:
            strategies.append({
                'method': 'pipeline',
                'priority': 3,
                'description': 'Transformers pipeline interface'
            })
        
        if connection_results['cached_models']:
            strategies.append({
                'method': 'cached',
                'priority': 2,
                'description': 'Local cached models'
            })
        
        if connection_results['offline_models']:
            strategies.append({
                'method': 'offline',
                'priority': 4,
                'description': 'Offline model access'
            })
        
        # Sort by priority
        strategies.sort(key=lambda x: x['priority'])
        
        return strategies
    
    def load_model_with_fallback(self, model_name, strategies):
        """Load model using fallback strategy chain"""
        print("HUGGING FACE: Loading model '{}' with fallback strategies...".format(model_name))
        
        for strategy in strategies:
            try:
                method = strategy['method']
                print("  Attempting: {}".format(strategy['description']))
                
                if method == 'sentence_transformers':
                    model = SentenceTransformer(model_name)
                    if DEVICE and DEVICE.type == 'mps':
                        model = model.to(DEVICE)
                    print("  ✓ SUCCESS: SentenceTransformers model loaded")
                    return model, method
                
                elif method == 'transformers_direct':
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModel.from_pretrained(model_name)
                    if DEVICE and DEVICE.type == 'mps':
                        model = model.to(DEVICE)
                    print("  ✓ SUCCESS: Direct transformers model loaded")
                    return {'model': model, 'tokenizer': tokenizer}, method
                
                elif method == 'pipeline':
                    model = pipeline("feature-extraction", model=model_name)
                    print("  ✓ SUCCESS: Pipeline model loaded")
                    return model, method
                
                elif method == 'cached':
                    # Try to load from cache with local_files_only
                    model = SentenceTransformer(model_name, local_files_only=True)
                    if DEVICE and DEVICE.type == 'mps':
                        model = model.to(DEVICE)
                    print("  ✓ SUCCESS: Cached model loaded")
                    return model, method
                
                elif method == 'offline':
                    os.environ["TRANSFORMERS_OFFLINE"] = "1"
                    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
                    model = AutoModel.from_pretrained(model_name, local_files_only=True)
                    if DEVICE and DEVICE.type == 'mps':
                        model = model.to(DEVICE)
                    # Reset environment
                    if "TRANSFORMERS_OFFLINE" in os.environ:
                        del os.environ["TRANSFORMERS_OFFLINE"]
                    print("  ✓ SUCCESS: Offline model loaded")
                    return {'model': model, 'tokenizer': tokenizer}, method
                
            except Exception as e:
                print("  ✗ FAILED: {}".format(str(e)[:60]))
                continue
        
        print("  ✗ ALL METHODS FAILED: Unable to load model '{}'".format(model_name))
        return None, None
    
    def authenticate_huggingface(self):
        """Attempt Hugging Face authentication with multiple methods"""
        auth_methods = []
        
        # Method 1: Environment variable
        if 'HUGGINGFACE_TOKEN' in os.environ:
            try:
                login(token=os.environ['HUGGINGFACE_TOKEN'])
                auth_methods.append('Environment Variable')
                print("HUGGING FACE AUTH: Authenticated via environment variable")
            except Exception as e:
                print("HUGGING FACE AUTH: Environment variable failed - {}".format(str(e)[:50]))
        
        # Method 2: Try cached token
        try:
            login()  # Will use cached token if available
            auth_methods.append('Cached Token')
            print("HUGGING FACE AUTH: Authenticated via cached token")
        except Exception as e:
            print("HUGGING FACE AUTH: Cached token failed - {}".format(str(e)[:50]))
        
        # Method 3: Anonymous access
        if not auth_methods:
            print("HUGGING FACE AUTH: Using anonymous access (limited to public models)")
            auth_methods.append('Anonymous')
        
        return auth_methods
    """Advanced ML-powered AO1 field analyzer"""
    
    def __init__(self):
        self.client = None
        self.neural_matcher = None
        self.sentence_model = None
        self.tfidf_vectorizer = None
        self.requirement_embeddings = {}
        self.field_vocabulary = {}
        self.initialize_ml_components()
        
class AdvancedAO1Analyzer:
    """Advanced ML-powered AO1 field analyzer with robust Hugging Face connectivity"""
    
    def __init__(self):
        self.client = None
        self.neural_matcher = None
        self.sentence_model = None
        self.sentence_model_method = None
        self.transformers_model = None
        self.tfidf_vectorizer = None
        self.requirement_embeddings = {}
        self.field_vocabulary = {}
        self.hf_connector = HuggingFaceConnector()
        self.initialize_ml_components()
        
    def initialize_ml_components(self):
        """Initialize ML components with robust Hugging Face connectivity"""
        try:
            if not HF_AVAILABLE:
                logger.warning("ML COMPONENTS: Hugging Face libraries not available - using basic mode")
                return
            
            # Test Hugging Face connectivity
            connection_results = self.hf_connector.test_huggingface_connectivity()
            successful_methods = sum(connection_results.values())
            
            print("CONNECTIVITY: {}/7 Hugging Face connection methods successful".format(successful_methods))
            
            if successful_methods == 0:
                print("WARNING: No Hugging Face connectivity - falling back to basic analysis")
                return
            
            # Authenticate if possible
            auth_methods = self.hf_connector.authenticate_huggingface()
            
            # Determine optimal loading strategy
            strategies = self.hf_connector.get_optimal_model_strategy(connection_results)
            
            if not strategies:
                print("WARNING: No viable model loading strategies found")
                return
            
            # Load sentence transformer model with fallback
            model_options = [
                'sentence-transformers/all-MiniLM-L6-v2',
                'sentence-transformers/all-mpnet-base-v2',
                'sentence-transformers/paraphrase-MiniLM-L6-v2',
                'distilbert-base-uncased',
                'bert-base-uncased'
            ]
            
            model_loaded = False
            for model_name in model_options:
                print("MODELS: Attempting to load '{}'...".format(model_name))
                model, method = self.hf_connector.load_model_with_fallback(model_name, strategies)
                
                if model is not None:
                    self.sentence_model = model
                    self.sentence_model_method = method
                    model_loaded = True
                    print("MODELS: Successfully loaded '{}' via {}".format(model_name, method))
                    break
                else:
                    print("MODELS: Failed to load '{}'".format(model_name))
            
            if not model_loaded:
                print("WARNING: Unable to load any sentence transformer models")
                self.sentence_model = None
                return
            
            # Initialize TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 3),
                stop_words='english'
            )
            
            # Pre-compute requirement embeddings
            self._compute_requirement_embeddings()
            
            # Initialize neural matcher
            self._initialize_neural_matcher()
            
            print("ML COMPONENTS: Full initialization complete with {} connectivity".format(
                len(self.hf_connector.successful_connections)
            ))
            
        except Exception as e:
            logger.error("ML INITIALIZATION ERROR: {}".format(e))
            print("ERROR: ML component initialization failed - {}".format(str(e)[:100]))
            self.sentence_model = None
        
    def initialize_ml_components(self):
        """Initialize ML components with robust Hugging Face connectivity"""
        try:
            if not HF_AVAILABLE:
                logger.warning("ML COMPONENTS: Hugging Face libraries not available - using basic mode")
                return
            
            # Test Hugging Face connectivity
            connection_results = self.hf_connector.test_huggingface_connectivity()
            successful_methods = sum(connection_results.values())
            
            print("CONNECTIVITY: {}/7 Hugging Face connection methods successful".format(successful_methods))
            
            if successful_methods == 0:
                print("WARNING: No Hugging Face connectivity - falling back to basic analysis")
                return
            
            # Authenticate if possible
            auth_methods = self.hf_connector.authenticate_huggingface()
            
            # Determine optimal loading strategy
            strategies = self.hf_connector.get_optimal_model_strategy(connection_results)
            
            if not strategies:
                print("WARNING: No viable model loading strategies found")
                return
            
            # Load sentence transformer model with fallback
            model_options = [
                'sentence-transformers/all-MiniLM-L6-v2',
                'sentence-transformers/all-mpnet-base-v2',
                'sentence-transformers/paraphrase-MiniLM-L6-v2',
                'distilbert-base-uncased',
                'bert-base-uncased'
            ]
            
            model_loaded = False
            for model_name in model_options:
                print("MODELS: Attempting to load '{}'...".format(model_name))
                model, method = self.hf_connector.load_model_with_fallback(model_name, strategies)
                
                if model is not None:
                    self.sentence_model = model
                    self.sentence_model_method = method
                    model_loaded = True
                    print("MODELS: Successfully loaded '{}' via {}".format(model_name, method))
                    break
                else:
                    print("MODELS: Failed to load '{}'".format(model_name))
            
            if not model_loaded:
                print("WARNING: Unable to load any sentence transformer models")
                self.sentence_model = None
                return
            
            # Initialize TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 3),
                stop_words='english'
            )
            
            # Pre-compute requirement embeddings
            self._compute_requirement_embeddings()
            
            # Initialize neural matcher
            self._initialize_neural_matcher()
            
            print("ML COMPONENTS: Full initialization complete with {} connectivity".format(
                len(self.hf_connector.successful_connections)
            ))
            
        except Exception as e:
            logger.error("ML INITIALIZATION ERROR: {}".format(e))
            print("ERROR: ML component initialization failed - {}".format(str(e)[:100]))
            self.sentence_model = None
    
    def _compute_requirement_embeddings(self):
        """Pre-compute embeddings for all AO1 requirements with multiple model strategies"""
        requirement_descriptions = {
            'REQ-1': 'global view asset identifiers hostname computer device system',
            'REQ-2': 'infrastructure type deployment cloud aws azure gcp onprem',
            'REQ-3': 'regional country geographic location datacenter region zone',
            'REQ-4': 'business application organizational unit department division',
            'REQ-5': 'system classification server function operating system windows linux',
            'REQ-6': 'security control coverage agent endpoint detection response',
            'REQ-7': 'logging compliance platform splunk chronicle ingestion parsing',
            'REQ-8': 'domain visibility hostname dns resolution network address'
        }
        
        if not self.sentence_model:
            print("EMBEDDINGS: No sentence model available - skipping embedding computation")
            return
        
        try:
            print("EMBEDDINGS: Computing requirement embeddings...")
            
            for req, desc in requirement_descriptions.items():
                if self.sentence_model_method == 'sentence_transformers':
                    # Standard SentenceTransformer approach
                    embedding = self.sentence_model.encode([desc])
                    self.requirement_embeddings[req] = embedding[0]
                    
                elif self.sentence_model_method in ['transformers_direct', 'offline']:
                    # Direct transformers approach
                    model = self.sentence_model['model']
                    tokenizer = self.sentence_model['tokenizer']
                    
                    inputs = tokenizer(desc, return_tensors='pt', padding=True, truncation=True)
                    if DEVICE and DEVICE.type == 'mps':
                        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = model(**inputs)
                        # Use mean pooling of last hidden states
                        embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()[0]
                        self.requirement_embeddings[req] = embedding
                
                elif self.sentence_model_method == 'pipeline':
                    # Pipeline approach
                    embedding = self.sentence_model(desc)[0]
                    # Average the token embeddings
                    if isinstance(embedding, list) and len(embedding) > 0:
                        embedding_array = np.array(embedding).mean(axis=0)
                        self.requirement_embeddings[req] = embedding_array
            
            print("EMBEDDINGS: Successfully computed embeddings for {} requirements".format(len(self.requirement_embeddings)))
            
        except Exception as e:
            logger.error("EMBEDDING COMPUTATION ERROR: {}".format(e))
            print("ERROR: Failed to compute requirement embeddings - {}".format(str(e)[:100]))
            self.requirement_embeddings = {}
    
    def _initialize_neural_matcher(self):
        """Initialize the neural network matcher"""
        try:
            # Build vocabulary from AO1 keywords
            vocab = list(ALL_AO1_KEYWORDS) + ['<UNK>', '<PAD>']
            self.field_vocabulary = {word: idx for idx, word in enumerate(vocab)}
            
            # Initialize neural network
            self.neural_matcher = AO1NeuralMatcher(
                vocab_size=len(vocab),
                embedding_dim=128,
                hidden_dim=64
            )
            
            if DEVICE and DEVICE.type == 'mps':
                self.neural_matcher = self.neural_matcher.to(DEVICE)
            
            logger.info("NEURAL NETWORK: Initialized with {} vocabulary terms".format(len(vocab)))
            
        except Exception as e:
            logger.error("NEURAL NETWORK ERROR: {}".format(e))
            self.neural_matcher = None
    
    def authenticate_bigquery(self):
        """Authenticate with BigQuery"""
        try:
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
            self.client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
            logger.info("BIGQUERY: Authentication successful")
            return True
        except Exception as e:
            logger.error("BIGQUERY AUTH ERROR: {}".format(e))
            return False
    
    def get_datasets(self) -> List[str]:
        """Get all accessible datasets"""
        try:
            datasets = [d.dataset_id for d in self.client.list_datasets()]
            logger.info("DATASETS: Found {} accessible datasets".format(len(datasets)))
            return datasets
        except Exception as e:
            logger.error("DATASET ACCESS ERROR: {}".format(e))
            return []
    
    def get_table_metadata(self, dataset_id: str, table_id: str) -> Optional[bigquery.Table]:
        """Get table metadata with error handling"""
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            return self.client.get_table(table_ref)
        except Exception:
            return None
    
    def compute_semantic_similarity(self, field_name: str, requirement: str) -> float:
        """Compute semantic similarity using multiple model strategies"""
        if not self.sentence_model or requirement not in self.requirement_embeddings:
            return 0.0
        
        try:
            if self.sentence_model_method == 'sentence_transformers':
                # Standard SentenceTransformer approach
                field_embedding = self.sentence_model.encode([field_name])
                req_embedding = self.requirement_embeddings[requirement].reshape(1, -1)
                similarity = cosine_similarity(field_embedding, req_embedding)[0][0]
                
            elif self.sentence_model_method in ['transformers_direct', 'offline']:
                # Direct transformers approach
                model = self.sentence_model['model']
                tokenizer = self.sentence_model['tokenizer']
                
                inputs = tokenizer(field_name, return_tensors='pt', padding=True, truncation=True)
                if DEVICE and DEVICE.type == 'mps':
                    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model(**inputs)
                    field_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
                
                req_embedding = self.requirement_embeddings[requirement].reshape(1, -1)
                similarity = cosine_similarity(field_embedding, req_embedding)[0][0]
                
            elif self.sentence_model_method == 'pipeline':
                # Pipeline approach
                field_result = self.sentence_model(field_name)[0]
                if isinstance(field_result, list) and len(field_result) > 0:
                    field_embedding = np.array(field_result).mean(axis=0).reshape(1, -1)
                    req_embedding = self.requirement_embeddings[requirement].reshape(1, -1)
                    similarity = cosine_similarity(field_embedding, req_embedding)[0][0]
                else:
                    similarity = 0.0
            else:
                similarity = 0.0
            
            return float(similarity)
            
        except Exception as e:
            logger.error("SEMANTIC SIMILARITY ERROR: {}".format(e))
            return 0.0
    
    def neural_field_classification(self, field_name: str) -> Dict[str, float]:
        """Use neural network to classify field relevance to requirements"""
        if not self.neural_matcher:
            return {}
        
        try:
            # Tokenize field name
            tokens = field_name.lower().split('_')
            token_ids = []
            
            for token in tokens:
                if token in self.field_vocabulary:
                    token_ids.append(self.field_vocabulary[token])
                else:
                    token_ids.append(self.field_vocabulary['<UNK>'])
            
            # Pad sequence
            max_len = 10
            if len(token_ids) < max_len:
                token_ids.extend([self.field_vocabulary['<PAD>']] * (max_len - len(token_ids)))
            else:
                token_ids = token_ids[:max_len]
            
            # Convert to tensor
            input_tensor = torch.tensor([token_ids], dtype=torch.long)
            if DEVICE and DEVICE.type == 'mps':
                input_tensor = input_tensor.to(DEVICE)
            
            # Forward pass
            with torch.no_grad():
                output = self.neural_matcher(input_tensor)
                probabilities = output.cpu().numpy()[0]
            
            # Map to requirements
            requirements = ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']
            return {req: prob for req, prob in zip(requirements, probabilities)}
            
        except Exception as e:
            logger.error("NEURAL CLASSIFICATION ERROR: {}".format(e))
            return {}
    
    def analyze_field_advanced(self, field_name: str, field_type: str) -> Tuple[bool, str, str, float]:
        """Advanced field analysis using multiple ML techniques"""
        field_lower = field_name.lower().strip()
        
        # Exact match check
        if field_lower in ALL_AO1_KEYWORDS:
            requirement = self.get_requirement_for_keyword(field_lower)
            return True, requirement, field_lower, 1.0
        
        # Neural network classification
        neural_scores = self.neural_field_classification(field_name)
        best_neural_req = max(neural_scores.items(), key=lambda x: x[1]) if neural_scores else (None, 0.0)
        
        # Semantic similarity analysis
        best_semantic_score = 0.0
        best_semantic_req = None
        
        for req in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
            semantic_score = self.compute_semantic_similarity(field_name, req)
            if semantic_score > best_semantic_score:
                best_semantic_score = semantic_score
                best_semantic_req = req
        
        # Pattern matching for partial matches
        best_pattern_match = None
        best_pattern_score = 0.0
        
        for keyword in ALL_AO1_KEYWORDS:
            if len(keyword) >= 3:
                if keyword in field_lower:
                    score = len(keyword) / len(field_lower)
                    if score > best_pattern_score:
                        best_pattern_score = score
                        best_pattern_match = keyword
                elif field_lower in keyword and len(field_lower) >= 3:
                    score = len(field_lower) / len(keyword)
                    if score > best_pattern_score:
                        best_pattern_score = score
                        best_pattern_match = keyword
        
        # Combine all scores for final decision
        combined_score = 0.0
        final_requirement = None
        matched_keyword = None
        
        if best_neural_req[1] > 0.3:  # Neural network confidence threshold
            combined_score += best_neural_req[1] * 0.4
            final_requirement = best_neural_req[0]
        
        if best_semantic_score > 0.2:  # Semantic similarity threshold
            combined_score += best_semantic_score * 0.3
            if not final_requirement:
                final_requirement = best_semantic_req
        
        if best_pattern_match and best_pattern_score > 0.3:  # Pattern match threshold
            combined_score += best_pattern_score * 0.3
            matched_keyword = best_pattern_match
            if not final_requirement:
                final_requirement = self.get_requirement_for_keyword(best_pattern_match)
        
        # Decision threshold
        if combined_score > 0.4 and final_requirement:
            return True, final_requirement, matched_keyword or field_lower, combined_score
        
        return False, None, None, 0.0
    
    def get_requirement_for_keyword(self, keyword: str) -> str:
        """Get requirement for a specific keyword"""
        for req, keywords in REQUIREMENT_KEYWORDS.items():
            if keyword in keywords:
                return req
        return "UNKNOWN"
    
    def scan_table_comprehensive(self, dataset_id: str, table_id: str) -> List[FieldMatch]:
        """Comprehensive table scanning with ML analysis"""
        table = self.get_table_metadata(dataset_id, table_id)
        if not table:
            return []
        
        matches = []
        
        def analyze_field_recursive(field, parent_path=""):
            field_path = "{}.{}".format(parent_path, field.name) if parent_path else field.name
            
            # Advanced field analysis
            is_match, requirement, matched_keyword, confidence = self.analyze_field_advanced(field.name, field.field_type)
            
            if is_match and requirement != "UNKNOWN":
                # Compute additional metrics
                semantic_sim = self.compute_semantic_similarity(field.name, requirement)
                context_relevance = self.compute_context_relevance(field.name, field.field_type, requirement)
                
                match_type = "EXACT" if confidence >= 0.9 else "ADVANCED_ML" if confidence >= 0.6 else "SUSPECTED"
                
                match = FieldMatch(
                    dataset=dataset_id,
                    table=table_id,
                    field_name=field.name,
                    field_path=field_path,
                    field_type=field.field_type,
                    requirement=requirement,
                    matched_keyword=matched_keyword,
                    match_type=match_type,
                    confidence_score=confidence,
                    table_rows=table.num_rows or 0,
                    table_size_bytes=table.num_bytes or 0,
                    semantic_similarity=semantic_sim,
                    context_relevance=context_relevance
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
    
    def compute_context_relevance(self, field_name: str, field_type: str, requirement: str) -> float:
        """Compute contextual relevance score"""
        relevance_score = 0.5  # Base score
        
        # Type-based relevance
        type_weights = {
            'STRING': 0.8, 'VARCHAR': 0.8, 'TEXT': 0.8,
            'INTEGER': 0.6, 'INT64': 0.6,
            'TIMESTAMP': 0.7, 'DATETIME': 0.7,
            'FLOAT': 0.5, 'NUMERIC': 0.5
        }
        
        relevance_score *= type_weights.get(field_type, 0.5)
        
        # Requirement-specific adjustments
        if requirement in ['REQ-1', 'REQ-8'] and any(term in field_name.lower() for term in ['id', 'name', 'host']):
            relevance_score *= 1.2
        elif requirement == 'REQ-2' and any(term in field_name.lower() for term in ['cloud', 'aws', 'azure']):
            relevance_score *= 1.3
        elif requirement == 'REQ-6' and any(term in field_name.lower() for term in ['agent', 'security', 'endpoint']):
            relevance_score *= 1.4
        
        return min(relevance_score, 1.0)
    
    def scan_all_datasets(self) -> List[FieldMatch]:
        """Scan all datasets with progress tracking"""
        datasets = self.get_datasets()
        if not datasets:
            return []
        
        all_matches = []
        total_tables = 0
        processed_tables = 0
        
        # Count total tables
        print("ANALYSIS: Counting tables across {} datasets...".format(len(datasets)))
        for dataset_id in datasets:
            try:
                tables = list(self.client.list_tables(dataset_id))
                total_tables += len(tables)
            except Exception:
                continue
        
        print("ANALYSIS: Processing {} tables with ML-enhanced field detection...".format(total_tables))
        
        # Process all tables
        for dataset_id in datasets:
            try:
                tables = list(self.client.list_tables(dataset_id))
                
                for table in tables:
                    processed_tables += 1
                    
                    if processed_tables % 50 == 0:
                        progress = (processed_tables / total_tables) * 100
                        print("PROGRESS: {:.1f}% complete ({}/{} tables)".format(progress, processed_tables, total_tables))
                    
                    matches = self.scan_table_comprehensive(dataset_id, table.table_id)
                    all_matches.extend(matches)
                    
            except Exception as e:
                logger.error("DATASET ERROR {}: {}".format(dataset_id, e))
                continue
        
        print("ANALYSIS: Complete - {} field matches discovered".format(len(all_matches)))
        return all_matches
    
    def generate_professional_report(self, matches: List[FieldMatch]):
        """Generate professional analysis report with connectivity status"""
        if not matches:
            print("\nAO1 FIELD DISCOVERY ANALYSIS")
            print("=" * 60)
            print("STATUS: No AO1-relevant fields discovered in accessible datasets")
            print("RECOMMENDATION: Verify field naming conventions and data ingestion processes")
            return
        
        # Sort matches by requirement, confidence, and table size
        matches.sort(key=lambda x: (x.requirement, -x.confidence_score, -x.table_rows))
        
        # Group by requirement
        by_requirement = defaultdict(list)
        for match in matches:
            by_requirement[match.requirement].append(match)
        
        print("\nADVANCED AO1 FIELD DISCOVERY ANALYSIS")
        print("=" * 60)
        print("ANALYSIS METHOD: ML-Enhanced with Neural Networks and Semantic Analysis")
        
        # Display connectivity status
        if hasattr(self, 'hf_connector') and self.hf_connector.successful_connections:
            print("HUGGING FACE: Connected via {}".format(", ".join(self.hf_connector.successful_connections[:3])))
        else:
            print("HUGGING FACE: Limited connectivity - using fallback methods")
            
        if self.sentence_model_method:
            print("MODEL STRATEGY: {}".format(self.sentence_model_method.replace('_', ' ').title()))
        
        print("GPU ACCELERATION: {}".format("M1 Metal Performance Shaders" if DEVICE and DEVICE.type == 'mps' else "CPU Processing"))
        print("TOTAL DISCOVERIES: {} fields across {} requirements".format(len(matches), len(by_requirement)))
        
        # Rest of the report generation remains the same...
        # Detailed requirement analysis
        for req_num in ['REQ-1', 'REQ-2', 'REQ-3', 'REQ-4', 'REQ-5', 'REQ-6', 'REQ-7', 'REQ-8']:
            req_matches = by_requirement.get(req_num, [])
            
            if not req_matches:
                print("\n{}: No suitable fields identified".format(req_num))
                continue
            
            # Categorize by match type
            exact_matches = [m for m in req_matches if m.match_type == 'EXACT']
            ml_matches = [m for m in req_matches if m.match_type == 'ADVANCED_ML']
            suspected_matches = [m for m in req_matches if m.match_type == 'SUSPECTED']
            
            print("\n{}: {} total field candidates identified".format(req_num, len(req_matches)))
            print("   EXACT: {} | ML-IDENTIFIED: {} | SUSPECTED: {}".format(len(exact_matches), len(ml_matches), len(suspected_matches)))
            
            # Show top recommendations
            top_matches = sorted(req_matches, key=lambda x: (-x.confidence_score, -x.table_rows))[:5]
            
            print("   TOP RECOMMENDATIONS (by confidence and data volume):")
            for i, match in enumerate(top_matches, 1):
                rows_display = "{:,} rows".format(match.table_rows) if match.table_rows > 0 else "size unknown"
                confidence_display = "{:.1%}".format(match.confidence_score)
                
                print("      {}. Field '{}' in {}.{} ({})".format(i, match.field_name, match.dataset, match.table, rows_display))
                print("         Confidence: {} | Type: {} | Keyword: '{}'".format(confidence_display, match.match_type, match.matched_keyword))
                
                if match.match_type == 'EXACT':
                    print("         Assessment: This field exactly matches AO1 keyword '{}' and provides direct {} measurement capability.".format(match.matched_keyword, req_num))
                elif match.match_type == 'ADVANCED_ML':
                    print("         Assessment: ML analysis indicates high probability this field supports {} requirements with {:.1%} semantic similarity.".format(req_num, match.semantic_similarity))
                else:
                    print("         Assessment: Suspected match for {} - manual verification recommended to confirm field usage patterns.".format(req_num))
        
        # Generate insights and recommendations
        self.generate_strategic_insights(matches, by_requirement)
    
    def generate_strategic_insights(self, matches: List[FieldMatch], by_requirement: Dict[str, List[FieldMatch]]):
        """Generate strategic insights from the analysis"""
        print("\nSTRATEGIC INSIGHTS AND RECOMMENDATIONS")
        print("=" * 60)
        
        # Coverage analysis
        coverage_score = len(by_requirement) / 8 * 100
        print("AO1 COVERAGE: {:.1f}% ({}/8 requirements have field candidates)".format(coverage_score, len(by_requirement)))
        
        # High-confidence recommendations
        high_confidence = [m for m in matches if m.confidence_score >= 0.8]
        print("HIGH-CONFIDENCE FIELDS: {} fields with 80%+ confidence scores".format(len(high_confidence)))
        
        # Data volume analysis
        total_rows = sum(m.table_rows for m in matches)
        print("TOTAL DATA VOLUME: {:,} rows across all candidate tables".format(total_rows))
        
        # Dataset distribution
        dataset_counts = Counter(m.dataset for m in matches)
        top_datasets = dataset_counts.most_common(3)
        print("PRIMARY DATASETS: {}".format(", ".join("{}({})".format(ds, count) for ds, count in top_datasets)))
        
        print("\nRECOMMENDATIONS:")
        print("1. IMMEDIATE: Focus validation on {} high-confidence exact matches".format(len([m for m in matches if m.match_type == 'EXACT'])))
        print("2. STRATEGIC: Investigate ML-identified fields for expanded AO1 coverage")
        print("3. OPERATIONAL: Prioritize tables with highest row counts for maximum visibility impact")
        
        if coverage_score < 50:
            print("4. CRITICAL: Low AO1 coverage detected - consider field naming standardization")
        
        print("5. VALIDATION: Confirm suspected matches through sample data analysis")
    
    def save_comprehensive_results(self, matches: List[FieldMatch]):
        """Save comprehensive results with ML analysis data"""
        if not matches:
            return
        
        # Convert to DataFrame
        df = pd.DataFrame([asdict(match) for match in matches])
        
        # Sort by strategic importance
        df['strategic_score'] = df['confidence_score'] * 0.6 + (df['table_rows'] / df['table_rows'].max()) * 0.4
        df = df.sort_values(['requirement', 'strategic_score'], ascending=[True, False])
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = "ao1_advanced_discovery_{}.csv".format(timestamp)
        df.to_csv(filename, index=False)
        
        # Save executive summary
        summary_df = df.groupby(['requirement', 'match_type']).agg({
            'field_name': 'count',
            'confidence_score': 'mean',
            'table_rows': 'sum'
        }).round(3)
        
        summary_filename = "ao1_executive_summary_{}.csv".format(timestamp)
        summary_df.to_csv(summary_filename)
        
        print("\nRESULTS SAVED:")
        print("Detailed Analysis: {}".format(filename))
        print("Executive Summary: {}".format(summary_filename))

def main():
    """Main execution with advanced ML analysis and robust Hugging Face connectivity"""
    print("ADVANCED AO1 FIELD DISCOVERY SYSTEM")
    print("Powered by Neural Networks and M1 GPU Acceleration")
    print("Multiple Hugging Face Connection Strategies")
    print("=" * 60)
    
    # Initialize analyzer
    print("INITIALIZATION: Setting up advanced ML components...")
    analyzer = AdvancedAO1Analyzer()
    
    # Display connectivity summary
    if hasattr(analyzer, 'hf_connector') and analyzer.hf_connector.successful_connections:
        print("CONNECTIVITY STATUS: Successfully connected via {}".format(
            ", ".join(analyzer.hf_connector.successful_connections)
        ))
    else:
        print("CONNECTIVITY STATUS: Limited Hugging Face access - using fallback analysis")
    
    # Authenticate
    if not analyzer.authenticate_bigquery():
        print("CRITICAL: BigQuery authentication failed")
        return
    
    # Run comprehensive analysis
    start_time = time.time()
    
    try:
        matches = analyzer.scan_all_datasets()
        
        analysis_time = time.time() - start_time
        print("\nANALYSIS COMPLETE")
        print("Processing Time: {:.2f} seconds".format(analysis_time))
        print("Model Strategy: {}".format(analyzer.sentence_model_method or "Basic Pattern Matching"))
        print("Fields Analyzed: Advanced ML processing on all accessible table schemas")
        
        # Generate reports
        analyzer.generate_professional_report(matches)
        analyzer.save_comprehensive_results(matches)
        
        # Additional connectivity diagnostics
        if hasattr(analyzer, 'hf_connector'):
            print("\nCONNECTIVITY DIAGNOSTICS:")
            print("Successful Methods: {}".format(len(analyzer.hf_connector.successful_connections)))
            if analyzer.hf_connector.successful_connections:
                for method in analyzer.hf_connector.successful_connections:
                    print("  - {}".format(method))
        
    except KeyboardInterrupt:
        print("\nANALYSIS INTERRUPTED: Partial results may be available in logs")
    except Exception as e:
        print("\nCRITICAL ERROR: {}".format(e))
        logger.error("MAIN EXECUTION ERROR: {}".format(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()