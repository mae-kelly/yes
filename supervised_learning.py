import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import json
import pickle
from pathlib import Path
from datetime import datetime
import logging
from collections import defaultdict
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroundTruthManager:
    def __init__(self):
        self.ground_truth_path = Path('ground_truth.json')
        self.feedback_path = Path('user_feedback.json')
        self.verified_hosts_path = Path('verified_hosts.json')
        self.ground_truth = self._load_ground_truth()
        self.feedback_history = self._load_feedback()
        self.verified_hosts = self._load_verified_hosts()
        
    def _load_ground_truth(self) -> Dict[str, Any]:
        if self.ground_truth_path.exists():
            with open(self.ground_truth_path, 'r') as f:
                return json.load(f)
        
        return {
            'verified_classifications': {},
            'verified_hosts': {},
            'correct_inferences': defaultdict(list),
            'incorrect_inferences': defaultdict(list),
            'field_mappings': {
                'hostname_patterns': {},
                'critical_hosts': [],
                'production_patterns': []
            }
        }
    
    def _load_feedback(self) -> List[Dict[str, Any]]:
        if self.feedback_path.exists():
            with open(self.feedback_path, 'r') as f:
                return json.load(f)
        return []
    
    def _load_verified_hosts(self) -> Dict[str, Any]:
        if self.verified_hosts_path.exists():
            with open(self.verified_hosts_path, 'r') as f:
                return json.load(f)
        
        return {
            'production_hosts': [],
            'development_hosts': [],
            'critical_systems': [],
            'non_critical_systems': [],
            'hosts_with_issues': {},
            'compliant_hosts': []
        }
    
    def add_ground_truth(self, entity_data: Dict[str, Any], correct_labels: Dict[str, Any]):
        entity_id = self._generate_id(entity_data)
        
        self.ground_truth['verified_classifications'][entity_id] = {
            'data': entity_data,
            'labels': correct_labels,
            'timestamp': datetime.now().isoformat()
        }
        
        if correct_labels.get('is_production'):
            self.verified_hosts['production_hosts'].append(entity_data.get('hostname'))
        
        if correct_labels.get('is_critical'):
            self.verified_hosts['critical_systems'].append(entity_data.get('hostname'))
        
        if correct_labels.get('has_security_gap'):
            self.verified_hosts['hosts_with_issues'][entity_data.get('hostname')] = correct_labels.get('issues', [])
        
        self._save_ground_truth()
    
    def record_feedback(self, prediction: Dict[str, Any], actual: Dict[str, Any], is_correct: bool):
        feedback = {
            'prediction': prediction,
            'actual': actual,
            'is_correct': is_correct,
            'timestamp': datetime.now().isoformat()
        }
        
        self.feedback_history.append(feedback)
        
        if is_correct:
            for inference in prediction.get('inferences', []):
                self.ground_truth['correct_inferences'][inference].append(prediction)
        else:
            for inference in prediction.get('inferences', []):
                self.ground_truth['incorrect_inferences'][inference].append(prediction)
        
        self._save_feedback()
    
    def get_training_data(self) -> Tuple[List[Dict], List[Dict]]:
        X = []
        y = []
        
        for entity_id, data in self.ground_truth['verified_classifications'].items():
            X.append(data['data'])
            y.append(data['labels'])
        
        return X, y
    
    def _generate_id(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def _save_ground_truth(self):
        with open(self.ground_truth_path, 'w') as f:
            json.dump(self.ground_truth, f, indent=2)
    
    def _save_feedback(self):
        with open(self.feedback_path, 'w') as f:
            json.dump(self.feedback_history, f, indent=2)
    
    def _save_verified_hosts(self):
        with open(self.verified_hosts_path, 'w') as f:
            json.dump(self.verified_hosts, f, indent=2)

class SupervisedNeuralNetwork(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: List[int], num_classes: int):
        super().__init__()
        
        layers = []
        current_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(current_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            current_dim = hidden_dim
        
        self.feature_extractor = nn.Sequential(*layers)
        
        self.classifiers = nn.ModuleDict({
            'is_production': nn.Linear(current_dim, 2),
            'is_critical': nn.Linear(current_dim, 2),
            'has_security_gap': nn.Linear(current_dim, 2),
            'needs_patching': nn.Linear(current_dim, 2),
            'environment_type': nn.Linear(current_dim, 4),
            'risk_level': nn.Linear(current_dim, 3)
        })
        
        self.confidence_estimator = nn.Sequential(
            nn.Linear(current_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        features = self.feature_extractor(x)
        
        outputs = {}
        for task, classifier in self.classifiers.items():
            outputs[task] = classifier(features)
        
        confidence = self.confidence_estimator(features)
        outputs['confidence'] = confidence
        
        return outputs

class HostDataset(Dataset):
    def __init__(self, X: List[Dict], y: List[Dict], feature_extractor):
        self.X = X
        self.y = y
        self.feature_extractor = feature_extractor
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        features = self.feature_extractor.extract_features(self.X[idx])
        
        labels = {
            'is_production': 1 if self.y[idx].get('is_production') else 0,
            'is_critical': 1 if self.y[idx].get('is_critical') else 0,
            'has_security_gap': 1 if self.y[idx].get('has_security_gap') else 0,
            'needs_patching': 1 if self.y[idx].get('needs_patching') else 0,
            'environment_type': self._encode_environment(self.y[idx].get('environment', 'unknown')),
            'risk_level': self._encode_risk(self.y[idx].get('risk_level', 'medium'))
        }
        
        return torch.FloatTensor(features), labels
    
    def _encode_environment(self, env: str) -> int:
        mapping = {'production': 0, 'development': 1, 'test': 2, 'unknown': 3}
        return mapping.get(env.lower(), 3)
    
    def _encode_risk(self, risk: str) -> int:
        mapping = {'low': 0, 'medium': 1, 'high': 2}
        return mapping.get(risk.lower(), 1)

class FeatureExtractor:
    def __init__(self, embedding_engine=None):
        self.embedding_engine = embedding_engine
        self.feature_dim = 256
        
    def extract_features(self, entity_data: Dict[str, Any]) -> np.ndarray:
        features = []
        
        hostname_features = self._extract_hostname_features(entity_data.get('hostname', ''))
        features.extend(hostname_features)
        
        network_features = self._extract_network_features(entity_data.get('ip_address', ''))
        features.extend(network_features)
        
        security_features = self._extract_security_features(entity_data)
        features.extend(security_features)
        
        metadata_features = self._extract_metadata_features(entity_data)
        features.extend(metadata_features)
        
        if self.embedding_engine:
            text_repr = ' '.join(str(v) for v in entity_data.values() if v)
            embedding = self.embedding_engine.encode(text_repr)[0][:128]
            features.extend(embedding)
        
        features = np.array(features)
        
        if len(features) < self.feature_dim:
            features = np.pad(features, (0, self.feature_dim - len(features)))
        elif len(features) > self.feature_dim:
            features = features[:self.feature_dim]
        
        return features
    
    def _extract_hostname_features(self, hostname: str) -> List[float]:
        features = []
        hostname_lower = hostname.lower()
        
        features.append(1.0 if 'prod' in hostname_lower else 0.0)
        features.append(1.0 if 'dev' in hostname_lower else 0.0)
        features.append(1.0 if 'test' in hostname_lower else 0.0)
        features.append(1.0 if 'qa' in hostname_lower else 0.0)
        
        features.append(1.0 if '-' in hostname else 0.0)
        features.append(hostname.count('-') / 10)
        features.append(len(hostname) / 50)
        
        features.append(1.0 if any(c.isdigit() for c in hostname) else 0.0)
        
        return features
    
    def _extract_network_features(self, ip_address: str) -> List[float]:
        features = []
        
        if not ip_address:
            return [0.0] * 8
        
        features.append(1.0 if ip_address.startswith('10.') else 0.0)
        features.append(1.0 if ip_address.startswith('192.168.') else 0.0)
        features.append(1.0 if ip_address.startswith('172.') else 0.0)
        
        parts = ip_address.split('.')
        if len(parts) == 4:
            for part in parts:
                try:
                    features.append(int(part) / 255)
                except:
                    features.append(0.0)
        else:
            features.extend([0.0] * 4)
        
        features.append(1.0 if ip_address else 0.0)
        
        return features[:8]
    
    def _extract_security_features(self, entity_data: Dict[str, Any]) -> List[float]:
        features = []
        
        features.append(1.0 if entity_data.get('edr_coverage') else 0.0)
        features.append(1.0 if entity_data.get('tanium_coverage') else 0.0)
        features.append(1.0 if entity_data.get('dlp_coverage') else 0.0)
        features.append(1.0 if entity_data.get('splunk_logging') else 0.0)
        features.append(1.0 if entity_data.get('gso_logging') else 0.0)
        features.append(1.0 if entity_data.get('cmdb_visibility') else 0.0)
        
        patch_date = entity_data.get('last_patch_date')
        if patch_date:
            try:
                days_since_patch = (datetime.now() - datetime.fromisoformat(str(patch_date))).days
                features.append(min(1.0, days_since_patch / 365))
            except:
                features.append(0.5)
        else:
            features.append(1.0)
        
        features.append(1.0 if entity_data.get('criticality') == 'high' else 0.5 if entity_data.get('criticality') == 'medium' else 0.0)
        
        return features
    
    def _extract_metadata_features(self, entity_data: Dict[str, Any]) -> List[float]:
        features = []
        
        features.append(len(entity_data) / 50)
        
        non_null_count = sum(1 for v in entity_data.values() if v not in [None, '', 'unknown'])
        features.append(non_null_count / len(entity_data) if entity_data else 0.0)
        
        features.append(1.0 if entity_data.get('environment') == 'production' else 0.0)
        features.append(1.0 if entity_data.get('environment') == 'development' else 0.0)
        
        features.append(1.0 if entity_data.get('domain') else 0.0)
        features.append(1.0 if entity_data.get('owner') else 0.0)
        features.append(1.0 if entity_data.get('business_unit') else 0.0)
        
        return features

class SupervisedLearningSystem:
    def __init__(self, embedding_engine=None):
        self.ground_truth_manager = GroundTruthManager()
        self.feature_extractor = FeatureExtractor(embedding_engine)
        self.model = SupervisedNeuralNetwork(
            input_dim=self.feature_extractor.feature_dim,
            hidden_dims=[512, 256, 128],
            num_classes=6
        )
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model_path = Path('supervised_model.pth')
        self.training_history = []
        
    def train(self, epochs: int = 50, batch_size: int = 32):
        X, y = self.ground_truth_manager.get_training_data()
        
        if len(X) < 10:
            logger.warning(f"Not enough training data: {len(X)} samples. Need at least 10.")
            return
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        train_dataset = HostDataset(X_train, y_train, self.feature_extractor)
        val_dataset = HostDataset(X_val, y_val, self.feature_extractor)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        criterion = nn.CrossEntropyLoss()
        
        for epoch in range(epochs):
            self.model.train()
            train_loss = 0
            
            for features, labels in train_loader:
                features = features.to(self.device)
                
                self.optimizer.zero_grad()
                outputs = self.model(features)
                
                loss = 0
                for task, output in outputs.items():
                    if task != 'confidence' and task in labels:
                        target = torch.LongTensor([labels[task]]).to(self.device)
                        loss += criterion(output, target)
                
                loss.backward()
                self.optimizer.step()
                train_loss += loss.item()
            
            val_loss, val_metrics = self._validate(val_loader, criterion)
            
            self.training_history.append({
                'epoch': epoch,
                'train_loss': train_loss / len(train_loader),
                'val_loss': val_loss,
                'val_metrics': val_metrics
            })
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Train Loss: {train_loss/len(train_loader):.4f}, Val Loss: {val_loss:.4f}")
                logger.info(f"Val Metrics: {val_metrics}")
        
        self._save_model()
    
    def _validate(self, val_loader, criterion):
        self.model.eval()
        val_loss = 0
        all_predictions = defaultdict(list)
        all_targets = defaultdict(list)
        
        with torch.no_grad():
            for features, labels in val_loader:
                features = features.to(self.device)
                outputs = self.model(features)
                
                loss = 0
                for task, output in outputs.items():
                    if task != 'confidence' and task in labels:
                        target = torch.LongTensor([labels[task]]).to(self.device)
                        loss += criterion(output, target)
                        
                        pred = torch.argmax(output, dim=1)
                        all_predictions[task].append(pred.cpu().numpy())
                        all_targets[task].append(labels[task])
                
                val_loss += loss.item()
        
        metrics = {}
        for task in all_predictions:
            if all_predictions[task] and all_targets[task]:
                predictions = np.concatenate(all_predictions[task])
                targets = np.array(all_targets[task])
                accuracy = accuracy_score(targets, predictions)
                metrics[task] = accuracy
        
        return val_loss / len(val_loader), metrics
    
    def predict(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        self.model.eval()
        
        features = self.feature_extractor.extract_features(entity_data)
        features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(features_tensor)
        
        predictions = {}
        for task, output in outputs.items():
            if task == 'confidence':
                predictions[task] = output.item()
            else:
                probs = torch.softmax(output, dim=1)
                pred_class = torch.argmax(output, dim=1).item()
                predictions[task] = {
                    'class': pred_class,
                    'probability': probs[0, pred_class].item()
                }
        
        inferences = self._generate_inferences(predictions, entity_data)
        
        return {
            'predictions': predictions,
            'confidence': predictions['confidence'],
            'inferences': inferences
        }
    
    def _generate_inferences(self, predictions: Dict[str, Any], entity_data: Dict[str, Any]) -> List[str]:
        inferences = []
        
        if predictions.get('is_production', {}).get('class') == 1:
            inferences.append('production_system')
        
        if predictions.get('is_critical', {}).get('class') == 1:
            inferences.append('critical_asset')
        
        if predictions.get('has_security_gap', {}).get('class') == 1:
            inferences.append('security_gap_detected')
            
            if not entity_data.get('edr_coverage'):
                inferences.append('no_endpoint_protection')
            
            if not entity_data.get('splunk_logging'):
                inferences.append('no_logging')
        
        if predictions.get('needs_patching', {}).get('class') == 1:
            inferences.append('outdated_patches')
        
        risk_level = predictions.get('risk_level', {}).get('class', 1)
        if risk_level == 2:
            inferences.append('high_risk')
        elif risk_level == 0:
            inferences.append('low_risk')
        
        return inferences
    
    def learn_from_feedback(self, entity_data: Dict[str, Any], prediction: Dict[str, Any], 
                           actual_labels: Dict[str, Any], is_correct: bool):
        self.ground_truth_manager.record_feedback(prediction, actual_labels, is_correct)
        
        if not is_correct:
            self.ground_truth_manager.add_ground_truth(entity_data, actual_labels)
            
            if len(self.ground_truth_manager.ground_truth['verified_classifications']) % 10 == 0:
                logger.info("Retraining model with new feedback...")
                self.train(epochs=10)
    
    def _save_model(self):
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_history': self.training_history
        }, self.model_path)
        logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self):
        if self.model_path.exists():
            checkpoint = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.training_history = checkpoint.get('training_history', [])
            logger.info("Model loaded successfully")
            return True
        return False

class ActiveLearningOrchestrator:
    def __init__(self, supervised_system: SupervisedLearningSystem):
        self.supervised_system = supervised_system
        self.uncertainty_threshold = 0.6
        self.feedback_queue = []
        
    def process_with_active_learning(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        prediction = self.supervised_system.predict(entity_data)
        
        if prediction['confidence'] < self.uncertainty_threshold:
            self.feedback_queue.append({
                'entity_data': entity_data,
                'prediction': prediction,
                'needs_verification': True
            })
        
        return prediction
    
    def request_human_verification(self) -> List[Dict[str, Any]]:
        uncertain_cases = [item for item in self.feedback_queue if item['needs_verification']]
        
        high_value_cases = sorted(uncertain_cases, 
                                 key=lambda x: self._calculate_learning_value(x), 
                                 reverse=True)[:10]
        
        return high_value_cases
    
    def _calculate_learning_value(self, case: Dict[str, Any]) -> float:
        confidence = case['prediction']['confidence']
        
        uncertainty = 1 - confidence
        
        is_production = 'prod' in str(case['entity_data'].get('hostname', '')).lower()
        importance = 1.5 if is_production else 1.0
        
        return uncertainty * importance
    
    def incorporate_human_feedback(self, case: Dict[str, Any], correct_labels: Dict[str, Any]):
        entity_data = case['entity_data']
        prediction = case['prediction']
        
        is_correct = self._check_if_correct(prediction, correct_labels)
        
        self.supervised_system.learn_from_feedback(
            entity_data, prediction, correct_labels, is_correct
        )
        
        case['needs_verification'] = False
        case['verified_labels'] = correct_labels
    
    def _check_if_correct(self, prediction: Dict[str, Any], correct_labels: Dict[str, Any]) -> bool:
        for key in ['is_production', 'is_critical', 'has_security_gap']:
            if key in correct_labels:
                pred_class = prediction['predictions'].get(key, {}).get('class')
                actual = 1 if correct_labels[key] else 0
                if pred_class != actual:
                    return False
        return True