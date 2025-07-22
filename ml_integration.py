import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class RenaissanceMLIntegration:
    def __init__(self, config: Dict):
        self.config = config
        self.meta_learner = SimpleMetaLearner(config)
        self.ensemble_manager = SimpleEnsembleManager(config)
        self.feature_selector = SimpleFeatureSelector(config)
        self.model_weights = {}
        self.prediction_cache = {}
        
    async def predict_renaissance_signals(self, features: pd.DataFrame, symbols: List[str]) -> Dict:
        predictions = {}
        
        for symbol in symbols:
            if len(features) > 50:
                symbol_features = self._prepare_symbol_features(features, symbol)
                
                meta_pred = await self.meta_learner.predict(symbol_features, symbol)
                ensemble_pred = await self.ensemble_manager.predict(symbol_features, symbol)
                
                combined_pred = self._combine_predictions(meta_pred, ensemble_pred, symbol)
                predictions[symbol] = combined_pred
                
        return {'ensemble': predictions, 'confidence': self._calculate_ensemble_confidence(predictions)}
        
    def _prepare_symbol_features(self, features: pd.DataFrame, symbol: str) -> np.ndarray:
        if features.empty:
            return np.zeros((1, 50))
            
        selected_features = self.feature_selector.select_top_features(features, 50)
        feature_vector = selected_features.iloc[-1:].fillna(0).values
        
        if feature_vector.shape[1] < 50:
            padding = np.zeros((feature_vector.shape[0], 50 - feature_vector.shape[1]))
            feature_vector = np.hstack([feature_vector, padding])
        elif feature_vector.shape[1] > 50:
            feature_vector = feature_vector[:, :50]
            
        return feature_vector
        
    def _combine_predictions(self, meta_pred: Dict, ensemble_pred: Dict, symbol: str) -> Dict:
        meta_score = meta_pred.get('prediction', 0.0)
        ensemble_score = ensemble_pred.get('prediction', 0.0)
        
        meta_weight = self.model_weights.get(f'{symbol}_meta', 0.3)
        ensemble_weight = self.model_weights.get(f'{symbol}_ensemble', 0.7)
        
        combined_score = meta_score * meta_weight + ensemble_score * ensemble_weight
        combined_confidence = (meta_pred.get('confidence', 0.5) + ensemble_pred.get('confidence', 0.5)) / 2
        
        class_probs = self._score_to_class_probabilities(combined_score)
        
        return {
            'prediction': combined_score,
            'confidence': combined_confidence,
            'predictions': class_probs,
            'meta_component': meta_score,
            'ensemble_component': ensemble_score
        }
        
    def _score_to_class_probabilities(self, score: float) -> List[float]:
        score = np.clip(score, -1.0, 1.0)
        
        if score > 0.5:
            return [0.05, 0.1, 0.15, 0.3, 0.4]
        elif score > 0.2:
            return [0.1, 0.15, 0.2, 0.35, 0.2]
        elif score > -0.2:
            return [0.2, 0.2, 0.2, 0.2, 0.2]
        elif score > -0.5:
            return [0.2, 0.35, 0.2, 0.15, 0.1]
        else:
            return [0.4, 0.3, 0.15, 0.1, 0.05]
            
    def _calculate_ensemble_confidence(self, predictions: Dict) -> float:
        if not predictions:
            return 0.0
            
        confidences = [pred.get('confidence', 0.0) for pred in predictions.values()]
        return np.mean(confidences)

class SimpleMetaLearner:
    def __init__(self, config: Dict):
        self.config = config
        self.base_models = {}
        
    async def predict(self, features: np.ndarray, symbol: str) -> Dict:
        if symbol not in self.base_models:
            self._initialize_symbol_models(symbol)
            
        base_predictions = []
        
        for model_name, model in self.base_models[symbol].items():
            try:
                pred = model.predict(features.reshape(1, -1))[0]
                base_predictions.append(pred)
            except:
                base_predictions.append(0.0)
                
        if len(base_predictions) < 3:
            base_predictions.extend([0.0] * (3 - len(base_predictions)))
            
        meta_pred = np.mean(base_predictions)
        confidence = min(np.std(base_predictions) * 2, 0.9) if len(base_predictions) > 1 else 0.5
            
        return {
            'prediction': np.clip(meta_pred, -1.0, 1.0),
            'confidence': confidence,
            'base_predictions': base_predictions
        }
        
    def _initialize_symbol_models(self, symbol: str):
        self.base_models[symbol] = {
            'simple': SimpleLinearModel(),
            'trend': TrendModel(),
            'momentum': MomentumModel()
        }
        
        dummy_X = np.random.randn(100, 50)
        dummy_y = np.random.randn(100)
        
        for model in self.base_models[symbol].values():
            try:
                model.fit(dummy_X, dummy_y)
            except:
                pass

class SimpleEnsembleManager:
    def __init__(self, config: Dict):
        self.config = config
        self.models = {}
        self.model_performance = {}
        
    async def predict(self, features: np.ndarray, symbol: str) -> Dict:
        if symbol not in self.models:
            self._initialize_ensemble_models(symbol)
            
        predictions = []
        weights = []
        
        for model_name, model in self.models[symbol].items():
            try:
                pred = model.predict(features.reshape(1, -1))[0]
                weight = self.model_performance.get(f'{symbol}_{model_name}', 1.0)
                predictions.append(pred)
                weights.append(weight)
            except:
                predictions.append(0.0)
                weights.append(0.1)
                
        if not predictions:
            return {'prediction': 0.0, 'confidence': 0.0}
            
        weights = np.array(weights)
        weights = weights / np.sum(weights)
        
        ensemble_pred = np.average(predictions, weights=weights)
        confidence = 1.0 - (np.std(predictions) / (np.mean(np.abs(predictions)) + 1e-8))
        confidence = np.clip(confidence, 0.1, 0.9)
        
        return {
            'prediction': np.clip(ensemble_pred, -1.0, 1.0),
            'confidence': confidence,
            'individual_predictions': predictions,
            'weights': weights.tolist()
        }
        
    def _initialize_ensemble_models(self, symbol: str):
        self.models[symbol] = {
            'model1': SimpleLinearModel(),
            'model2': TrendModel(),
            'model3': MomentumModel()
        }
        
        dummy_X = np.random.randn(80, 50)
        dummy_y = np.random.randn(80)
        
        for model_name, model in self.models[symbol].items():
            try:
                model.fit(dummy_X, dummy_y)
                self.model_performance[f'{symbol}_{model_name}'] = 1.0
            except:
                self.model_performance[f'{symbol}_{model_name}'] = 0.1

class SimpleFeatureSelector:
    def __init__(self, config: Dict):
        self.config = config
        self.selected_features = {}
        
    def select_top_features(self, features: pd.DataFrame, top_k: int = 50) -> pd.DataFrame:
        if features.empty:
            return pd.DataFrame()
            
        feature_hash = str(hash(str(features.columns.tolist())))
        
        if feature_hash in self.selected_features:
            selected_cols = self.selected_features[feature_hash]
            available_cols = [col for col in selected_cols if col in features.columns]
            return features[available_cols]
            
        numeric_features = features.select_dtypes(include=[np.number])
        
        if len(numeric_features.columns) <= top_k:
            self.selected_features[feature_hash] = numeric_features.columns.tolist()
            return numeric_features
            
        variance_scores = numeric_features.var()
        top_features = variance_scores.nlargest(top_k).index.tolist()
        
        self.selected_features[feature_hash] = top_features
        return numeric_features[top_features]

class SimpleLinearModel:
    def __init__(self):
        self.weights = None
        self.bias = 0.0
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        try:
            X_with_bias = np.column_stack([X, np.ones(X.shape[0])])
            coeffs = np.linalg.lstsq(X_with_bias, y, rcond=None)[0]
            self.weights = coeffs[:-1]
            self.bias = coeffs[-1]
        except:
            self.weights = np.random.randn(X.shape[1]) * 0.01
            self.bias = 0.0
            
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.weights is None:
            return np.zeros(X.shape[0])
        return X @ self.weights + self.bias

class TrendModel:
    def __init__(self):
        self.trend_coeff = 0.01
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        if len(y) > 1:
            self.trend_coeff = np.mean(np.diff(y))
            
    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(X.shape[0], self.trend_coeff)

class MomentumModel:
    def __init__(self):
        self.momentum_factor = 0.005
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        if len(y) > 10:
            recent_momentum = np.mean(y[-10:]) - np.mean(y[-20:-10]) if len(y) > 20 else 0
            self.momentum_factor = recent_momentum
            
    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(X.shape[0], self.momentum_factor)
