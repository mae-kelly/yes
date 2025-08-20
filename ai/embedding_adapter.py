"""
Embedding Dimension Adapter
Handles dimension mismatches between different embedding models and neural networks
"""

import torch
import torch.nn as nn
import numpy as np
import logging

logger = logging.getLogger(__name__)

class EmbeddingAdapter:
    """Adapts embeddings to match expected dimensions"""
    
    @staticmethod
    def adapt_dimensions(embeddings: torch.Tensor, target_dim: int) -> torch.Tensor:
        """
        Adapt embedding dimensions to match target dimension
        
        Args:
            embeddings: Input embeddings tensor (batch_size, current_dim)
            target_dim: Target dimension
            
        Returns:
            Adapted embeddings with shape (batch_size, target_dim)
        """
        if len(embeddings.shape) == 1:
            embeddings = embeddings.unsqueeze(0)
        
        current_dim = embeddings.shape[-1]
        
        if current_dim == target_dim:
            return embeddings
        
        batch_size = embeddings.shape[0]
        device = embeddings.device
        
        if current_dim < target_dim:
            # Pad with learned projection or zeros
            return EmbeddingAdapter._pad_embeddings(embeddings, target_dim)
        else:
            # Reduce dimensionality
            return EmbeddingAdapter._reduce_embeddings(embeddings, target_dim)
    
    @staticmethod
    def _pad_embeddings(embeddings: torch.Tensor, target_dim: int) -> torch.Tensor:
        """Pad embeddings to target dimension"""
        current_dim = embeddings.shape[-1]
        batch_size = embeddings.shape[0]
        device = embeddings.device
        
        # Method 1: Intelligent padding - repeat and scale
        if target_dim % current_dim == 0:
            # Perfect multiple - repeat the embeddings
            repeat_factor = target_dim // current_dim
            padded = embeddings.repeat(1, repeat_factor)
            # Scale to maintain magnitude
            padded = padded / np.sqrt(repeat_factor)
        else:
            # Method 2: Pad with projected values
            padding_needed = target_dim - current_dim
            
            # Create padding based on existing values
            if padding_needed <= current_dim:
                # Use circular padding
                padding = embeddings[:, :padding_needed]
            else:
                # Repeat embeddings to fill
                repeats = (padding_needed // current_dim) + 1
                padding = embeddings.repeat(1, repeats)[:, :padding_needed]
                padding = padding * 0.1  # Scale down padding
            
            padded = torch.cat([embeddings, padding], dim=-1)
        
        return padded
    
    @staticmethod
    def _reduce_embeddings(embeddings: torch.Tensor, target_dim: int) -> torch.Tensor:
        """Reduce embedding dimensionality"""
        current_dim = embeddings.shape[-1]
        device = embeddings.device
        
        # Method 1: Simple truncation (fastest)
        if target_dim >= current_dim * 0.5:
            return embeddings[:, :target_dim]
        
        # Method 2: Pooling-based reduction
        # Reshape and average pool
        batch_size = embeddings.shape[0]
        
        # Calculate pooling size
        pool_size = current_dim // target_dim
        remainder = current_dim % target_dim
        
        if remainder == 0:
            # Perfect division - use average pooling
            reshaped = embeddings[:, :pool_size * target_dim].reshape(batch_size, target_dim, pool_size)
            reduced = reshaped.mean(dim=-1)
        else:
            # Imperfect division - truncate then pool
            usable_dim = pool_size * target_dim
            reshaped = embeddings[:, :usable_dim].reshape(batch_size, target_dim, pool_size)
            reduced = reshaped.mean(dim=-1)
            
            # Add information from truncated dimensions
            if remainder > 0:
                extra = embeddings[:, usable_dim:usable_dim + target_dim]
                if extra.shape[-1] < target_dim:
                    padding = torch.zeros(batch_size, target_dim - extra.shape[-1]).to(device)
                    extra = torch.cat([extra, padding], dim=-1)
                reduced = reduced + extra * 0.1
        
        return reduced


class DimensionProjector(nn.Module):
    """Learnable dimension projector for embedding adaptation"""
    
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        if input_dim < output_dim:
            # Projection up
            self.projector = nn.Sequential(
                nn.Linear(input_dim, output_dim),
                nn.LayerNorm(output_dim),
                nn.GELU()
            )
        else:
            # Projection down
            self.projector = nn.Sequential(
                nn.Linear(input_dim, output_dim),
                nn.LayerNorm(output_dim)
            )
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize projection weights"""
        for module in self.projector:
            if isinstance(module, nn.Linear):
                # Xavier initialization
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Project embeddings to target dimension"""
        return self.projector(x)


class AdaptiveEmbeddingModel:
    """Wrapper for embedding models with automatic dimension adaptation"""
    
    def __init__(self, base_model, target_dim: int = 768):
        self.base_model = base_model
        self.target_dim = target_dim
        self.adapter = EmbeddingAdapter()
        
        # Test actual output dimension
        try:
            test_output = self.base_model.encode("test", convert_to_tensor=True)
            if len(test_output.shape) == 1:
                test_output = test_output.unsqueeze(0)
            self.actual_dim = test_output.shape[-1]
            logger.info(f"Base model output dimension: {self.actual_dim}, target: {self.target_dim}")
        except:
            self.actual_dim = None
            logger.warning("Could not determine base model output dimension")
    
    def encode(self, texts, convert_to_tensor: bool = False):
        """Encode texts with automatic dimension adaptation"""
        # Get base embeddings
        embeddings = self.base_model.encode(texts, convert_to_tensor=True)
        
        if len(embeddings.shape) == 1:
            embeddings = embeddings.unsqueeze(0)
        
        # Adapt dimensions if needed
        if embeddings.shape[-1] != self.target_dim:
            embeddings = self.adapter.adapt_dimensions(embeddings, self.target_dim)
        
        if not convert_to_tensor:
            embeddings = embeddings.cpu().numpy()
        
        return embeddings


def create_unified_embedder(target_dim: int = 768):
    """
    Create a unified embedder that works with any backend
    
    Args:
        target_dim: Target embedding dimension (default 768 for transformer compatibility)
    
    Returns:
        Embedder that always outputs the target dimension
    """
    import sys
    import os
    
    # Try to import the neural engine module
    try:
        # Add parent directory to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ai.neural_engine import transformer_model, TRANSFORMER_BACKEND
        
        if transformer_model is not None:
            # Wrap with adaptive model
            unified_model = AdaptiveEmbeddingModel(transformer_model, target_dim)
            logger.info(f"Created unified embedder with {TRANSFORMER_BACKEND} backend, output dim: {target_dim}")
            return unified_model
    except ImportError:
        logger.warning("Could not import transformer model")
    
    # Fallback: Create a simple hash-based embedder
    class SimpleEmbedder:
        def __init__(self, dim: int):
            self.dim = dim
        
        def encode(self, texts, convert_to_tensor: bool = False):
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = []
            for text in texts:
                np.random.seed(hash(text) % (2**32))
                embedding = np.random.randn(self.dim) * 0.1
                embeddings.append(embedding)
            
            embeddings = np.array(embeddings)
            
            if convert_to_tensor:
                import torch
                return torch.FloatTensor(embeddings)
            
            return embeddings
    
    logger.info(f"Created simple hash-based embedder with output dim: {target_dim}")
    return SimpleEmbedder(target_dim)


# Auto-fix for dimension mismatches
def fix_dimension_mismatch(model, embeddings, expected_dim):
    """
    Quick fix for dimension mismatches
    
    Args:
        model: The neural network model
        embeddings: Current embeddings
        expected_dim: Expected dimension
    
    Returns:
        Fixed embeddings
    """
    adapter = EmbeddingAdapter()
    return adapter.adapt_dimensions(embeddings, expected_dim)