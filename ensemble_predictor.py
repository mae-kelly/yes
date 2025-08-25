import numpy as np
import torch
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

class EnsemblePredictor:
    def __init__(self):
        self.models = {}
        self.weights = {}
        self.scaler = StandardScaler()
        
        logger.info("Ensemble Predictor initialized for multi-model consensus")
    
    def configure_ensemble(self):
        logger.info("Configuring ensemble with multiple ML techniques")
        
        self.weights = {
            'lstm': 0.20,
            'transformer': 0.20,
            'isolation_forest': 0.10,
            'lof': 0.10,
            'ocsvm': 0.10,
            'autoencoder': 0.10,
            'vae': 0.10,
            'lstm_autoencoder': 0.10
        }
        
        logger.info(f"  Configured {len(self.weights)} models with weighted voting")
        logger.info(f"  Weight distribution: {self.weights}")
        
        return {'models': list(self.weights.keys()), 'weights': self.weights}
    
    def predict_batch(self, candidates, models):
        logger.info(f"  Ensemble prediction on batch of {len(candidates)} candidates")
        
        predictions = []
        
        for i, candidate in enumerate(candidates):
            if i % 100 == 0 and i > 0:
                logger.info(f"    Processed {i}/{len(candidates)} candidates")
            
            features = self._extract_features(candidate)
            features_scaled = self.scaler.fit_transform([features])
            features_tensor = torch.FloatTensor(features_scaled).to(device)
            
            scores = {}
            
            if 'lstm' in models and models['lstm']:
                models['lstm'].eval()
                with torch.no_grad():
                    scores['lstm'] = models['lstm'](features_tensor).cpu().item()
            
            if 'transformer' in models and models['transformer']:
                models['transformer'].eval()
                with torch.no_grad():
                    scores['transformer'] = models['transformer'](features_tensor).cpu().item()
            
            if 'isolation_forest' in models and models['isolation_forest']:
                score = models['isolation_forest'].decision_function(features_scaled)[0]
                scores['isolation_forest'] = 1 / (1 + np.exp(-score))
            
            if 'lof' in models and models['lof']:
                score = models['lof'].decision_function(features_scaled)[0]
                scores['lof'] = 1 / (1 + np.exp(-score))
            
            if 'ocsvm' in models and models['ocsvm']:
                score = models['ocsvm'].decision_function(features_scaled)[0]
                scores['ocsvm'] = 1 / (1 + np.exp(-score))
            
            if 'autoencoder' in models and models['autoencoder']:
                models['autoencoder'].eval()
                with torch.no_grad():
                    error = models['autoencoder'].get_reconstruction_error(features_tensor).cpu().item()
                    scores['autoencoder'] = 1 / (1 + error)
            
            if 'vae' in models and models['vae']:
                models['vae'].eval()
                with torch.no_grad():
                    recon, _, _ = models['vae'](features_tensor)
                    error = torch.mean((features_tensor - recon) ** 2).cpu().item()
                    scores['vae'] = 1 / (1 + error)
            
            if 'lstm_autoencoder' in models and models['lstm_autoencoder']:
                models['lstm_autoencoder'].eval()
                with torch.no_grad():
                    recon = models['lstm_autoencoder'](features_tensor)
                    if len(recon.shape) == 3:
                        recon = recon.squeeze(1)
                    error = torch.mean((features_tensor - recon) ** 2).cpu().item()
                    scores['lstm_autoencoder'] = 1 / (1 + error)
            
            ensemble_score = 0
            for model_name, score in scores.items():
                weight = self.weights.get(model_name, 0.125)
                ensemble_score += score * weight
            
            predictions.append({
                'hostname': candidate.get('hostname', 'unknown'),
                'confidence': ensemble_score,
                'individual_scores': scores,
                'source': candidate.get('source', 'unknown')
            })
        
        return predictions
    
    def _extract_features(self, candidate):
        hostname = candidate.get('hostname', '')
        
        features = [
            len(hostname),
            hostname.count('.'),
            hostname.count('-'),
            len([c for c in hostname if c.isdigit()]),
            len([c for c in hostname if c.isalpha()])
        ]
        
        keywords = ['srv', 'web', 'db', 'app', 'prod', 'dev', 'test']
        for kw in keywords:
            features.append(1 if kw in hostname.lower() else 0)
        
        while len(features) < 20:
            features.append(0)
        
        return np.array(features[:20])