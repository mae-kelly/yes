import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List

class SchermanVIXDivergenceCore:
    def __init__(self, config: Dict):
        self.config = config
        
    def detect_crypto_vix_divergence(self, data: pd.DataFrame, fear_data: List[float]) -> Dict:
        if len(data) < 50 or len(fear_data) < 10:
            return {}
            
        try:
            prices = data['close'].values.astype(float)
            volumes = data['volume'].values.astype(float)
            
            current_price = float(prices[-1])
            current_fear = float(fear_data[-1])
            
            price_ma = np.mean(prices[-20:])
            volume_ma = np.mean(volumes[-20:])
            volume_ratio = volumes[-1] / volume_ma
            
            price_momentum = (current_price / prices[-10] - 1) * 100
            fear_momentum = (current_fear - np.mean(fear_data[-10:])) 
            
            rsi = self._calculate_rsi(prices)
            volatility = np.std(np.diff(np.log(prices[-30:]))) * np.sqrt(365)
            
            conditions = [
                current_price < price_ma * 0.98,
                current_fear < 30,
                rsi < 35,
                volume_ratio > 1.5,
                price_momentum < -2,
                volatility > 0.15
            ]
            
            confirmations = sum(conditions)
            
            if confirmations >= 4:
                confidence = 0.65 + (confirmations * 0.05)
                atr = np.mean([prices[i] - prices[i-1] for i in range(1, min(15, len(prices)))])
                
                return {
                    'signal': 'vix_divergence',
                    'direction': 'long',
                    'confidence': min(confidence, 0.95),
                    'entry_price': current_price,
                    'stop_loss': current_price - (atr * 2.5),
                    'take_profit': current_price + (atr * 4.0),
                    'timestamp': datetime.now(),
                    'confirmations': confirmations,
                    'total_conditions': len(conditions),
                    'rsi': rsi,
                    'volume_ratio': volume_ratio,
                    'fear_level': current_fear,
                    'volatility': volatility
                }
            
            return {}
            
        except Exception as e:
            return {}
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def validate_divergence_signal(self, signal: Dict, market_data: Dict) -> bool:
        if not signal or signal.get('confidence', 0) < 0.65:
            return False
        return True
    
    def adjust_position_size(self, base_size: float, signal: Dict, market_conditions: Dict) -> float:
        confidence = signal.get('confidence', 0.65)
        volatility = market_conditions.get('volatility', 0.25)
        return base_size * confidence * min(0.2 / volatility, 2.0)
    
    def _validate_inputs(self, data, fear_data):
        """Validate inputs before processing"""
        if data is None or len(data) < 20:
            return False
        
        if fear_data is None or len(fear_data) == 0:
            return False
        
        required_columns = ['close', 'volume', 'high', 'low']
        for col in required_columns:
            if col not in data.columns:
                return False
        
        return True
    
    def detect_crypto_vix_divergence_safe(self, data, fear_data):
        """Safe version with validation"""
        if not self._validate_inputs(data, fear_data):
            return {}
        
        return self.detect_crypto_vix_divergence(data, fear_data)
