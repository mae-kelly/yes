import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
warnings.filterwarnings('ignore')

class RenaissanceMLIntegration:
    def __init__(self, config: Dict):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.feature_cols = None
        
    async def predict_renaissance_signals(self, features: pd.DataFrame, symbols: List[str]) -> Dict:
        predictions = {}
        
        for symbol in symbols:
            if symbol not in self.models:
                self._train_model(symbol, features)
            
            if symbol in self.models and len(features) > 0:
                pred = self._generate_prediction(symbol, features)
                predictions[symbol] = pred
        
        ensemble_confidence = np.mean([p.get('confidence', 0.5) for p in predictions.values()]) if predictions else 0.5
        
        return {
            'ensemble': {
                'predictions': self._aggregate_predictions(predictions),
                'confidence': ensemble_confidence
            },
            'confidence': ensemble_confidence
        }
    
    def _train_model(self, symbol: str, features: pd.DataFrame):
        try:
            if len(features) < 100:
                return
            
            X = features.select_dtypes(include=[np.number]).fillna(0)
            if len(X.columns) == 0:
                return
                
            self.feature_cols = X.columns.tolist()
            
            returns = features.get('returns', pd.Series(np.random.randn(len(X)) * 0.01))
            y = pd.cut(returns.fillna(0), bins=5, labels=[0, 1, 2, 3, 4]).astype(int)
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            model = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
            model.fit(X_scaled, y)
            
            self.models[symbol] = model
            self.scalers[symbol] = scaler
            
        except Exception as e:
            pass
    
    def _generate_prediction(self, symbol: str, features: pd.DataFrame) -> Dict:
        try:
            model = self.models[symbol]
            scaler = self.scalers[symbol]
            
            X = features.select_dtypes(include=[np.number]).fillna(0)
            if self.feature_cols:
                missing_cols = set(self.feature_cols) - set(X.columns)
                for col in missing_cols:
                    X[col] = 0
                X = X[self.feature_cols]
            
            X_scaled = scaler.transform(X.tail(1))
            
            probabilities = model.predict_proba(X_scaled)[0]
            prediction = model.predict(X_scaled)[0]
            confidence = np.max(probabilities)
            
            score = (prediction - 2) / 2
            
            return {
                'prediction': score,
                'confidence': confidence,
                'probabilities': probabilities.tolist()
            }
            
        except Exception as e:
            return {
                'prediction': 0.0,
                'confidence': 0.5,
                'probabilities': [0.2, 0.2, 0.2, 0.2, 0.2]
            }
    
    def _aggregate_predictions(self, predictions: Dict) -> List[float]:
        if not predictions:
            return [0.2, 0.2, 0.2, 0.2, 0.2]
        
        all_probs = [p.get('probabilities', [0.2, 0.2, 0.2, 0.2, 0.2]) for p in predictions.values()]
        return np.mean(all_probs, axis=0).tolist()
