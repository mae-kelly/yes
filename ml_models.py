import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import warnings
warnings.filterwarnings('ignore')

class MLModelManager:
    def __init__(self, config: Dict):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.model_weights = {}
        self.model_performance = {}
        self.feature_importance = {}
        self.prediction_history = {}
        self.model_configs = {'random_forest': {'n_estimators': 100, 'max_depth': 10, 'min_samples_split': 20, 'min_samples_leaf': 10, 'random_state': 42}, 'xgboost': {'n_estimators': 100, 'max_depth': 6, 'learning_rate': 0.1, 'subsample': 0.8, 'colsample_bytree': 0.8, 'random_state': 42}, 'lightgbm': {'n_estimators': 100, 'max_depth': 6, 'learning_rate': 0.1, 'subsample': 0.8, 'colsample_bytree': 0.8, 'random_state': 42}, 'catboost': {'iterations': 100, 'depth': 6, 'learning_rate': 0.1, 'random_state': 42}, 'neural_network': {'hidden_layers': [64, 32], 'dropout': 0.2, 'activation': 'relu', 'optimizer': 'adam', 'epochs': 100, 'batch_size': 32}}
        self.ensemble_methods = ['voting', 'averaging', 'stacking', 'blending']
        self.hyperparameter_grids = {'random_forest': {'n_estimators': [50, 100, 200], 'max_depth': [5, 10, 15], 'min_samples_split': [10, 20, 50]}, 'xgboost': {'n_estimators': [50, 100, 200], 'max_depth': [3, 6, 9], 'learning_rate': [0.05, 0.1, 0.2]}, 'lightgbm': {'n_estimators': [50, 100, 200], 'max_depth': [3, 6, 9], 'learning_rate': [0.05, 0.1, 0.2]}}
        self.cross_validation = TimeSeriesSplit(n_splits=5)
        self.early_stopping = {'monitor': 'val_loss', 'patience': 10, 'restore_best_weights': True}
        self.feature_selection = {'method': 'importance', 'top_k': 50, 'threshold': 0.001}
        self.model_validation = {'test_size': 0.2, 'validation_size': 0.1, 'shuffle': False, 'stratify': False}
        self.prediction_intervals = {'method': 'quantile', 'alpha': 0.1, 'coverage': 0.9}
        self.model_interpretability = {'shap': True, 'lime': True, 'permutation': True, 'partial_dependence': True}
        self.model_monitoring = {'drift_detection': True, 'performance_decay': True, 'feature_drift': True, 'prediction_drift': True}
        self.auto_retraining = {'schedule': 'daily', 'trigger_threshold': 0.05, 'minimum_samples': 1000, 'performance_metric': 'accuracy'}
        
    def train_ensemble_models(self, features: pd.DataFrame, labels: pd.Series, symbol: str) -> Dict:
        try:
            if len(features) < 1000:
                print(f"Insufficient data for {symbol}: {len(features)} samples")
                return {}
            X_train, X_test, y_train, y_test = self._prepare_training_data(features, labels)
            if X_train is None:
                return {}
            models = {}
            scalers = {}
            performance = {}
            models['random_forest'], scalers['random_forest'] = self._train_random_forest(X_train, y_train, X_test, y_test)
            models['xgboost'], scalers['xgboost'] = self._train_xgboost(X_train, y_train, X_test, y_test)
            models['lightgbm'], scalers['lightgbm'] = self._train_lightgbm(X_train, y_train, X_test, y_test)
            models['catboost'], scalers['catboost'] = self._train_catboost(X_train, y_train, X_test, y_test)
            models['neural_network'], scalers['neural_network'] = self._train_neural_network(X_train, y_train, X_test, y_test)
            for model_name, model in models.items():
                if model is not None:
                    scaler = scalers[model_name]
                    if model_name == 'random_forest':
                        y_pred = model.predict(X_test)
                        y_pred_proba = model.predict_proba(X_test)
                    elif model_name == 'neural_network':
                        X_test_scaled = scaler.transform(X_test) if scaler else X_test
                        y_pred_proba = model.predict(X_test_scaled)
                        y_pred = np.argmax(y_pred_proba, axis=1)
                    else:
                        X_test_scaled = scaler.transform(X_test) if scaler else X_test
                        y_pred = model.predict(X_test_scaled)
                        y_pred_proba = model.predict_proba(X_test_scaled)
                    accuracy = accuracy_score(y_test, y_pred)
                    performance[model_name] = {'accuracy': accuracy, 'predictions': y_pred, 'probabilities': y_pred_proba}
            self.models[symbol] = models
            self.scalers[symbol] = scalers
            self.model_performance[symbol] = performance
            self.model_weights[symbol] = self._calculate_ensemble_weights(performance)
            self.feature_importance[symbol] = self._extract_feature_importance(models, features.columns)
            self._save_models(symbol, models, scalers, self.model_weights[symbol])
            return {'models': models, 'performance': performance, 'weights': self.model_weights[symbol], 'feature_importance': self.feature_importance[symbol]}
        except Exception as e:
            print(f"Error training ensemble models for {symbol}: {e}")
            return {}
            
    def _prepare_training_data(self, features: pd.DataFrame, labels: pd.Series) -> Tuple:
        try:
            valid_idx = ~(features.isna().any(axis=1) | labels.isna())
            X = features[valid_idx]
            y = labels[valid_idx]
            if len(X) < 500:
                return None, None, None, None
            test_size = self.model_validation['test_size']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False, random_state=42)
            return X_train, X_test, y_train, y_test
        except Exception as e:
            print(f"Error preparing training data: {e}")
            return None, None, None, None
            
    def _train_random_forest(self, X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple:
        try:
            config = self.model_configs['random_forest']
            model = RandomForestClassifier(**config)
            model.fit(X_train, y_train)
            return model, None
        except Exception as e:
            print(f"Error training Random Forest: {e}")
            return None, None
            
    def _train_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple:
        try:
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            config = self.model_configs['xgboost']
            model = xgb.XGBClassifier(**config)
            model.fit(X_train_scaled, y_train, eval_set=[(X_test_scaled, y_test)], verbose=False)
            return model, scaler
        except Exception as e:
            print(f"Error training XGBoost: {e}")
            return None, None
            
    def _train_lightgbm(self, X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple:
        try:
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            config = self.model_configs['lightgbm']
            model = lgb.LGBMClassifier(**config, verbose=-1)
            model.fit(X_train_scaled, y_train, eval_set=[(X_test_scaled, y_test)], callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)])
            return model, scaler
        except Exception as e:
            print(f"Error training LightGBM: {e}")
            return None, None
            
    def _train_catboost(self, X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple:
        try:
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            config = self.model_configs['catboost']
            model = CatBoostClassifier(**config, verbose=False)
            model.fit(X_train_scaled, y_train, eval_set=(X_test_scaled, y_test), early_stopping_rounds=10)
            return model, scaler
        except Exception as e:
            print(f"Error training CatBoost: {e}")
            return None, None
            
    def _train_neural_network(self, X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple:
        try:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            n_classes = len(np.unique(y_train))
            y