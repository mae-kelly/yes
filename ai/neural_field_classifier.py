import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path
import sqlite3
from collections import defaultdict
import re
from .corporate_tokenizer_loader import load_corporate_tokenizer

logger = logging.getLogger(__name__)

class AdvancedFieldClassificationDataset(Dataset):
    def __init__(self, training_data: List[Dict[str, Any]], tokenizer, max_length: int = 256):
        self.data = training_data
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        self.field_types = [
            'hostname', 'ip_address', 'fqdn', 'mac_address', 'email_address',
            'identifier', 'classification', 'text_content', 'numeric', 'temporal',
            'location', 'unknown'
        ]
        
        self.field_type_to_id = {ft: i for i, ft in enumerate(self.field_types)}
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        column_name = item['column_name']
        data_samples = item.get('data_samples', [])[:10]
        context_columns = item.get('context_columns', [])[:10]
        field_type = item['field_type']
        
        combined_text = f"COLUMN:{column_name} SAMPLES:{' '.join(map(str, data_samples))} CONTEXT:{' '.join(context_columns)}"
        
        try:
            if self.tokenizer:
                encoding = self.tokenizer(
                    combined_text,
                    truncation=True,
                    padding='max_length',
                    max_length=self.max_length,
                    return_tensors='pt'
                )
                input_ids = encoding['input_ids'].squeeze()
                attention_mask = encoding['attention_mask'].squeeze()
            else:
                input_ids = torch.zeros(self.max_length, dtype=torch.long)
                attention_mask = torch.ones(self.max_length, dtype=torch.long)
        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            input_ids = torch.zeros(self.max_length, dtype=torch.long)
            attention_mask = torch.ones(self.max_length, dtype=torch.long)
        
        field_type_id = self.field_type_to_id.get(field_type, self.field_type_to_id['unknown'])
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'field_type_id': torch.tensor(field_type_id, dtype=torch.long),
            'confidence': torch.tensor(item.get('confidence', 0.5), dtype=torch.float),
            'column_name': column_name,
            'samples': data_samples
        }

class M1OptimizedFieldClassifier(nn.Module):
    def __init__(self, vocab_size=50257, embed_dim=768, num_heads=12, num_layers=6, num_field_types=12):
        super().__init__()
        
        self.device = self._setup_m1_gpu()
        self.embed_dim = embed_dim
        self.num_field_types = num_field_types
        
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.positional_encoding = nn.Parameter(torch.randn(512, embed_dim))
        
        self.column_name_processor = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.data_sample_processor = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.context_processor = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        
        self.transformer_layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=embed_dim,
                nhead=num_heads,
                dim_feedforward=embed_dim * 2,
                dropout=0.1,
                activation='gelu',
                batch_first=True
            ) for _ in range(num_layers)
        ])
        
        self.pattern_memory = nn.Parameter(torch.randn(1000, embed_dim))
        
        self.field_classifier = nn.Sequential(
            nn.Linear(embed_dim, embed_dim // 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(embed_dim // 2, embed_dim // 4),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(embed_dim // 4, num_field_types)
        )
        
        self.confidence_estimator = nn.Sequential(
            nn.Linear(embed_dim, embed_dim // 4),
            nn.GELU(),
            nn.Linear(embed_dim // 4, 1),
            nn.Sigmoid()
        )
        
        self.pattern_similarity_threshold = 0.8
        
        self.to(self.device)
        
    def _setup_m1_gpu(self):
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            try:
                torch.mps.set_per_process_memory_fraction(0.95)
                logger.info("M1 GPU optimization activated - 95% memory allocation")
                return torch.device('mps')
            except Exception as e:
                logger.warning(f"M1 GPU setup failed: {e}")
        elif torch.cuda.is_available():
            logger.info("CUDA GPU detected")
            return torch.device('cuda')
        
        logger.info("Using CPU for neural processing")
        return torch.device('cpu')
    
    def forward(self, input_ids, attention_mask=None):
        batch_size, seq_len = input_ids.shape
        
        x = self.token_embedding(input_ids)
        
        if seq_len <= 512:
            x = x + self.positional_encoding[:seq_len].unsqueeze(0)
        
        column_features, _ = self.column_name_processor(x, x, x, key_padding_mask=~attention_mask if attention_mask is not None else None)
        sample_features, _ = self.data_sample_processor(x, x, x, key_padding_mask=~attention_mask if attention_mask is not None else None)
        context_features, _ = self.context_processor(x, x, x, key_padding_mask=~attention_mask if attention_mask is not None else None)
        
        combined_features = column_features + sample_features + context_features
        
        for transformer_layer in self.transformer_layers:
            combined_features = transformer_layer(combined_features, src_key_padding_mask=~attention_mask if attention_mask is not None else None)
        
        pooled_features = combined_features.mean(dim=1)
        
        pattern_similarities = torch.matmul(pooled_features.unsqueeze(1), self.pattern_memory.T)
        pattern_weights = F.softmax(pattern_similarities, dim=-1)
        pattern_enhanced = torch.matmul(pattern_weights, self.pattern_memory).squeeze(1)
        
        final_features = pooled_features + 0.3 * pattern_enhanced
        
        field_logits = self.field_classifier(final_features)
        confidence_scores = self.confidence_estimator(final_features)
        
        return {
            'field_logits': field_logits,
            'confidence_scores': confidence_scores,
            'embeddings': final_features,
            'pattern_similarities': pattern_similarities,
            'pattern_weights': pattern_weights
        }
    
    def update_pattern_memory(self, new_patterns: torch.Tensor):
        with torch.no_grad():
            similarity_matrix = torch.matmul(new_patterns, self.pattern_memory.T)
            max_similarities, _ = similarity_matrix.max(dim=1)
            
            novel_patterns = new_patterns[max_similarities < self.pattern_similarity_threshold]
            
            if len(novel_patterns) > 0:
                update_indices = torch.randint(0, self.pattern_memory.size(0), (len(novel_patterns),))
                self.pattern_memory[update_indices] = novel_patterns
                
                logger.info(f"Updated {len(novel_patterns)} pattern memory entries")

class ContinualFieldLearner:
    def __init__(self, model: M1OptimizedFieldClassifier, cache_dir: str = ".field_learning_cache"):
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.tokenizer = self._load_corporate_tokenizer()
        
        self.optimizer = optim.AdamW(self.model.parameters(), lr=2e-5, weight_decay=0.01)
        self.scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(self.optimizer, T_0=100, T_mult=2)
        
        self.loss_fn = nn.CrossEntropyLoss()
        self.confidence_loss_fn = nn.MSELoss()
        
        self.training_stats = {
            'total_samples_seen': 0,
            'accuracy_history': [],
            'loss_history': [],
            'pattern_updates': 0,
            'tokenizer_method': getattr(self.tokenizer, 'method_used', 'fallback') if self.tokenizer else 'none'
        }
        
        self.field_type_accuracies = defaultdict(list)
        
    def _load_corporate_tokenizer(self):
        logger.info("Loading tokenizer with aggressive corporate methods")
        try:
            loaded_tokenizer = load_corporate_tokenizer()
            if loaded_tokenizer and self._validate_tokenizer_functionality(loaded_tokenizer):
                method_used = getattr(loaded_tokenizer, 'method_used', 'unknown')
                logger.info(f"Tokenizer loaded successfully: {method_used}")
                return loaded_tokenizer
            else:
                logger.warning("Tokenizer validation failed, using emergency tokenizer")
                return self._create_emergency_tokenizer()
        except Exception as e:
            logger.error(f"Tokenizer loading failed: {e}")
            return self._create_emergency_tokenizer()
    
    def _validate_tokenizer_functionality(self, test_tokenizer):
        try:
            test_result = test_tokenizer("test", return_tensors="pt", padding="max_length", max_length=10)
            return ('input_ids' in test_result and 'attention_mask' in test_result and 
                    test_result['input_ids'].shape[1] == 10)
        except Exception as e:
            logger.error(f"Tokenizer validation failed: {e}")
            return False
    
    def _create_emergency_tokenizer(self):
        logger.warning("Creating emergency character-based tokenizer")
        
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
    
    def train_on_dataset(self, training_data: List[Dict[str, Any]], epochs: int = 5, batch_size: int = 16):
        if not self.tokenizer:
            logger.error("Cannot train without functional tokenizer")
            return
        
        logger.info(f"Training on {len(training_data)} samples for {epochs} epochs")
        logger.info(f"Using tokenizer: {getattr(self.tokenizer, 'method_used', 'unknown')}")
        
        dataset = AdvancedFieldClassificationDataset(training_data, self.tokenizer)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        
        self.model.train()
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            correct_predictions = 0
            total_predictions = 0
            
            for batch_idx, batch in enumerate(dataloader):
                input_ids = batch['input_ids'].to(self.model.device)
                attention_mask = batch['attention_mask'].to(self.model.device)
                field_type_ids = batch['field_type_id'].to(self.model.device)
                confidence_targets = batch['confidence'].to(self.model.device)
                
                self.optimizer.zero_grad()
                
                outputs = self.model(input_ids, attention_mask)
                
                classification_loss = self.loss_fn(outputs['field_logits'], field_type_ids)
                confidence_loss = self.confidence_loss_fn(outputs['confidence_scores'].squeeze(), confidence_targets)
                
                total_loss = classification_loss + 0.1 * confidence_loss
                
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.optimizer.step()
                self.scheduler.step()
                
                epoch_loss += total_loss.item()
                
                predicted = torch.argmax(outputs['field_logits'], dim=1)
                correct_predictions += (predicted == field_type_ids).sum().item()
                total_predictions += field_type_ids.size(0)
                
                if batch_idx % 10 == 0:
                    self.model.update_pattern_memory(outputs['embeddings'])
                    self.training_stats['pattern_updates'] += 1
                
                self.training_stats['total_samples_seen'] += input_ids.size(0)
            
            epoch_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            avg_epoch_loss = epoch_loss / len(dataloader) if len(dataloader) > 0 else 0
            
            self.training_stats['accuracy_history'].append(epoch_accuracy)
            self.training_stats['loss_history'].append(avg_epoch_loss)
            
            logger.info(f"Epoch {epoch+1}/{epochs}: Loss={avg_epoch_loss:.4f}, Accuracy={epoch_accuracy:.4f}")
    
    def predict_field_type(self, column_name: str, data_samples: List[str], 
                          context_columns: List[str] = None) -> Tuple[str, float]:
        
        if not self.tokenizer:
            return 'unknown', 0.0
        
        if context_columns is None:
            context_columns = []
        
        combined_text = f"COLUMN:{column_name} SAMPLES:{' '.join(map(str, data_samples[:10]))} CONTEXT:{' '.join(context_columns[:10])}"
        
        try:
            encoding = self.tokenizer(
                combined_text,
                truncation=True,
                padding='max_length',
                max_length=256,
                return_tensors='pt'
            ).to(self.model.device)
            input_ids = encoding['input_ids'].to(self.model.device)
            attention_mask = encoding['attention_mask'].to(self.model.device)
        except Exception as e:
            logger.error(f"Prediction tokenization failed: {e}")
            return 'unknown', 0.0
        
        self.model.eval()
        with torch.no_grad():
            try:
                outputs = self.model(input_ids, attention_mask)
                
                field_probabilities = F.softmax(outputs['field_logits'], dim=-1)
                predicted_field_id = torch.argmax(field_probabilities, dim=-1).item()
                confidence = outputs['confidence_scores'].item()
                
                field_types = ['hostname', 'ip_address', 'fqdn', 'mac_address', 'email_address',
                              'identifier', 'classification', 'text_content', 'numeric', 'temporal',
                              'location', 'unknown']
                
                predicted_field_type = field_types[predicted_field_id] if predicted_field_id < len(field_types) else 'unknown'
                
                max_probability = field_probabilities[0, predicted_field_id].item()
                final_confidence = (confidence + max_probability) / 2.0
                
                return predicted_field_type, final_confidence
                
            except Exception as e:
                logger.error(f"Model prediction failed: {e}")
                return 'unknown', 0.0
    
    def evaluate_on_test_data(self, test_data: List[Dict[str, Any]]) -> Dict[str, float]:
        correct_predictions = 0
        total_predictions = len(test_data)
        
        field_type_correct = defaultdict(int)
        field_type_total = defaultdict(int)
        
        for item in test_data:
            predicted_type, confidence = self.predict_field_type(
                item['column_name'],
                item.get('data_samples', []),
                item.get('context_columns', [])
            )
            
            true_type = item['field_type']
            
            field_type_total[true_type] += 1
            
            if predicted_type == true_type:
                correct_predictions += 1
                field_type_correct[true_type] += 1
        
        overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        field_type_accuracies = {}
        for field_type in field_type_total:
            field_type_accuracies[field_type] = field_type_correct[field_type] / field_type_total[field_type]
        
        return {
            'overall_accuracy': overall_accuracy,
            'field_type_accuracies': field_type_accuracies,
            'total_samples': total_predictions
        }
    
    def save_model(self, filepath: str):
        try:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'scheduler_state_dict': self.scheduler.state_dict(),
                'training_stats': self.training_stats
            }, filepath)
            
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Model save failed: {e}")
    
    def load_model(self, filepath: str):
        try:
            checkpoint = torch.load(filepath, map_location=self.model.device)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            self.training_stats = checkpoint.get('training_stats', self.training_stats)
            
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Model load failed: {e}")
    
    def continual_learning_update(self, new_data: List[Dict[str, Any]]):
        logger.info(f"Performing continual learning update with {len(new_data)} new samples")
        
        self.train_on_dataset(new_data, epochs=1, batch_size=8)
        
        if len(self.training_stats['accuracy_history']) > 0:
            recent_accuracy = self.training_stats['accuracy_history'][-1]
            logger.info(f"Post-update accuracy: {recent_accuracy:.4f}")

class SmartFieldTypeInference:
    def __init__(self, model_path: Optional[str] = None):
        self.model = M1OptimizedFieldClassifier()
        self.learner = ContinualFieldLearner(self.model)
        
        if model_path and Path(model_path).exists():
            self.learner.load_model(model_path)
        
        self.pattern_cache = {}
        
    def analyze_column(self, column_name: str, data_samples: List[str], 
                      context_columns: List[str] = None) -> Tuple[str, float]:
        
        cache_key = f"{column_name}:{hash(tuple(data_samples[:5]))}"
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        try:
            predicted_type, confidence = self.learner.predict_field_type(
                column_name, data_samples, context_columns or []
            )
            
            result = (predicted_type, confidence)
            self.pattern_cache[cache_key] = result
            
            return result
        except Exception as e:
            logger.error(f"Field analysis failed: {e}")
            return 'unknown', 0.0
    
    def learn_from_feedback(self, column_name: str, data_samples: List[str], 
                           correct_field_type: str, context_columns: List[str] = None):
        
        feedback_data = [{
            'column_name': column_name,
            'data_samples': data_samples,
            'field_type': correct_field_type,
            'context_columns': context_columns or [],
            'confidence': 1.0
        }]
        
        try:
            self.learner.continual_learning_update(feedback_data)
        except Exception as e:
            logger.error(f"Learning feedback failed: {e}")