#!/usr/bin/env python3
"""
ML System Manager
================
Advanced ML with M1 GPU support and fallback strategies.
"""

import os
import importlib.util
from typing import Dict, List, Optional, Set
from ao1_config_and_logging import logger
from corporate_connectivity import get_corporate_connection

class MLManager:
    """Smart ML system with progressive fallback."""
    
    def __init__(self):
        self.device = 'cpu'
        self.strategy = 'pattern_only'
        self.models = {}
        self.embeddings = self._create_embeddings()
        
    def initialize(self) -> Dict[str, bool]:
        """Initialize ML system with best available strategy."""
        # Check available libraries
        libs = self._check_libraries()
        
        # Configure device
        if libs.get('torch', False):
            self.device = self._detect_device()
        
        # Set strategy
        if libs.get('sentence_transformers', False):
            self.strategy = 'transformers'
            self._init_transformers()
        elif libs.get('sklearn', False):
            self.strategy = 'tfidf'
            self._init_tfidf()
        
        logger.info(f"ML initialized: {self.strategy} on {self.device}")
        return libs
    
    def _check_libraries(self) -> Dict[str, bool]:
        """Check ML library availability."""
        libs = {}
        
        try:
            import torch
            libs['torch'] = True
            logger.info(f"PyTorch {torch.__version__} available")
        except ImportError:
            libs['torch'] = False
        
        try:
            import sentence_transformers
            libs['sentence_transformers'] = True
            logger.info(f"SentenceTransformers {sentence_transformers.__version__} available")
        except ImportError:
            libs['sentence_transformers'] = False
        
        try:
            import sklearn
            libs['sklearn'] = True
            logger.info(f"Sklearn {sklearn.__version__} available")
        except ImportError:
            libs['sklearn'] = False
        
        return libs
    
    def _detect_device(self) -> str:
        """Detect optimal compute device."""
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                logger.info("M1 GPU (MPS) detected")
                return 'mps'
            elif torch.cuda.is_available():
                logger.info("CUDA GPU detected")
                return 'cuda'
        except:
            pass
        
        return 'cpu'
    
    def _init_transformers(self):
        """Initialize transformer models with corporate security."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Apply corporate connection settings
            connection = get_corporate_connection()
            if connection['success']:
                self._apply_security_config(connection['config'])
            
            # Try models in priority order
            models = ['all-MiniLM-L6-v2', 'paraphrase-MiniLM-L6-v2']
            
            for model_name in models:
                if self._load_model(model_name):
                    break
            else:
                logger.warning("No transformer models loaded, using embeddings")
                self.strategy = 'embeddings'
                
        except Exception as e:
            logger.warning(f"Transformer init failed: {e}")
            self.strategy = 'embeddings'
    
    def _load_model(self, model_name: str) -> bool:
        """Load transformer model with fallback strategies."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Try direct loading
            model = SentenceTransformer(model_name, device=self.device)
            test = model.encode(['test'])
            if test is not None:
                self.models['transformer'] = model
                logger.info(f"Loaded model: {model_name}")
                return True
                
        except Exception as e:
            logger.debug(f"Model loading failed for {model_name}: {e}")
            
            # Try cached loading
            try:
                model = SentenceTransformer(model_name, device=self.device, local_files_only=True)
                test = model.encode(['test'])
                if test is not None:
                    self.models['transformer'] = model
                    logger.info(f"Loaded cached model: {model_name}")
                    return True
            except:
                pass
        
        return False
    
    def _init_tfidf(self):
        """Initialize TF-IDF system."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.models['tfidf'] = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            logger.info("TF-IDF initialized")
        except Exception as e:
            logger.warning(f"TF-IDF init failed: {e}")
            self.strategy = 'embeddings'
    
    def _apply_security_config(self, config: Dict):
        """Apply corporate security configuration."""
        if 'proxy' in config:
            proxy = config['proxy']
            os.environ['HTTPS_PROXY'] = proxy
            os.environ['HTTP_PROXY'] = proxy
            # Exclude Google services
            os.environ['NO_PROXY'] = 'googleapis.com,googleusercontent.com'
            logger.info("Applied corporate proxy for ML downloads")
    
    def _create_embeddings(self) -> Dict[str, List[float]]:
        """Create optimized AO1 embeddings."""
        return {
            'hostname': [1.0, 0.8, 0.2, 0.1, 0.3, 0.1, 0.2, 0.9],
            'ip_address': [0.8, 0.9, 0.3, 0.1, 0.4, 0.1, 0.2, 0.7],
            'cloud': [0.2, 0.1, 1.0, 0.8, 0.2, 0.1, 0.1, 0.3],
            'region': [0.1, 0.2, 0.3, 1.0, 0.2, 0.1, 0.1, 0.2],
            'application': [0.1, 0.1, 0.2, 0.1, 0.1, 1.0, 0.8, 0.2],
            'windows': [0.3, 0.2, 0.3, 0.1, 0.9, 0.1, 0.1, 0.4],
            'crowdstrike': [0.4, 0.1, 0.2, 0.1, 0.2, 0.1, 1.0, 0.6],
            'splunk': [0.2, 0.1, 0.2, 0.1, 0.1, 0.3, 0.4, 1.0],
            'domain': [0.7, 0.6, 0.1, 0.2, 0.1, 0.1, 0.1, 0.3]
        }
    
    def compute_similarity(self, field: str, keywords: Set[str]) -> float:
        """Compute semantic similarity."""
        if self.strategy == 'transformers' and 'transformer' in self.models:
            return self._transformer_similarity(field, keywords)
        elif self.strategy == 'tfidf' and 'tfidf' in self.models:
            return self._tfidf_similarity(field, keywords)
        else:
            return self._embedding_similarity(field, keywords)
    
    def _transformer_similarity(self, field: str, keywords: Set[str]) -> float:
        """Compute transformer similarity."""
        try:
            model = self.models['transformer']
            field_emb = model.encode([field])
            keyword_embs = model.encode(list(keywords))
            
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(field_emb, keyword_embs)
            return float(similarities.max())
        except Exception as e:
            logger.debug(f"Transformer similarity failed: {e}")
            return self._embedding_similarity(field, keywords)
    
    def _tfidf_similarity(self, field: str, keywords: Set[str]) -> float:
        """Compute TF-IDF similarity."""
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            docs = [field] + list(keywords)
            tfidf_matrix = self.models['tfidf'].fit_transform(docs)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            return float(similarities.max()) if similarities.size > 0 else 0.0
        except Exception as e:
            logger.debug(f"TF-IDF similarity failed: {e}")
            return 0.0
    
    def _embedding_similarity(self, field: str, keywords: Set[str]) -> float:
        """Compute built-in embedding similarity."""
        field_lower = field.lower()
        max_sim = 0.0
        
        if field_lower in self.embeddings:
            field_vec = self.embeddings[field_lower]
            for keyword in keywords:
                if keyword in self.embeddings:
                    keyword_vec = self.embeddings[keyword]
                    sim = self._cosine_sim(field_vec, keyword_vec)
                    max_sim = max(max_sim, sim)
        
        return max_sim
    
    def _cosine_sim(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity."""
        try:
            dot = sum(a * b for a, b in zip(v1, v2))
            mag1 = sum(a * a for a in v1) ** 0.5
            mag2 = sum(b * b for b in v2) ** 0.5
            return dot / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0.0
        except:
            return 0.0

def get_ml_system():
    """Get initialized ML system."""
    ml = MLManager()
    ml.initialize()
    return ml