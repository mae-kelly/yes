import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')

class SchermanVIXCore:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.min_confidence = self.config.get('min_confidence', 0.65)
        self.lookback_period = self.config.get('lookback_period', 50)
        
    def analyze_divergence(self, price_data: pd.DataFrame, fear_greed_values: List[float]) -> Optional[Dict]:
        if len(price_data) < self.lookback_period or len(fear_greed_values) < 5:
            return None
            
        try:
            indicators = self._calculate_indicators(price_data)
            current_price = float(price_data['close'].iloc[-1])
            current_fear_greed = float(fear_greed_values[-1])
            divergence = self._detect_divergence(indicators, fear_greed_values, current_price)
            
            if divergence:
                signal = self._build_signal(divergence, indicators, current_price, current_fear_greed)
                if signal and signal['confidence'] >= self.min_confidence:
                    return signal
                    
            return None
            
        except Exception as e:
            print(f"Error in Scherman analysis: {e}")
            return None
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict:
        prices = data['close'].values
        volumes = data['volume'].values
        
        sma_20 = pd.Series(prices).rolling(20).mean()
        sma_50 = pd.Series(prices).rolling(50).mean()
        rsi = self._calculate_rsi(prices)
        volume_ma = pd.Series(volumes).rolling(20).mean()
        volume_ratio = volumes[-1] / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1
        momentum_5 = (prices[-1] / prices[-6] - 1) * 100 if len(prices) > 5 else 0
        momentum_10 = (prices[-1] / prices[-11] - 1) * 100 if len(prices) > 10 else 0
        returns = pd.Series(prices).pct_change()
        volatility = returns.rolling(20).std().iloc[-1] * np.sqrt(365)
        
        return {
            'current_price': prices[-1],
            'sma_20': sma_20.iloc[-1],
            'sma_50': sma_50.iloc[-1],
            'rsi': rsi,
            'volume_ratio': volume_ratio,
            'momentum_5': momentum_5,
            'momentum_10': momentum_10,
            'volatility': volatility,
            'price_vs_sma20': (prices[-1] / sma_20.iloc[-1] - 1) * 100,
            'price_vs_sma50': (prices[-1] / sma_50.iloc[-1] - 1) * 100
        }
    
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
    
    def _detect_divergence(self, indicators: Dict, fear_greed_values: List[float], current_price: float) -> Optional[Dict]:
        current_fear_greed = fear_greed_values[-1]
        rsi = indicators['rsi']
        price_vs_sma20 = indicators['price_vs_sma20']
        volume_ratio = indicators['volume_ratio']
        momentum_5 = indicators['momentum_5']
        
        bullish_conditions = [
            current_fear_greed < 25,
            rsi < 35,
            price_vs_sma20 < -3,
            volume_ratio > 1.2,
            momentum_5 < -2
        ]
        
        bearish_conditions = [
            current_fear_greed > 75,
            rsi > 65,
            price_vs_sma20 > 3,
            volume_ratio > 1.2,
            momentum_5 > 2
        ]
        
        bullish_score = sum(bullish_conditions)
        bearish_score = sum(bearish_conditions)
        
        if bullish_score >= 3:
            return {
                'direction': 'bullish',
                'type': 'vix_divergence',
                'score': bullish_score,
                'max_score': len(bullish_conditions),
                'fear_greed': current_fear_greed,
                'rsi': rsi,
                'conditions_met': bullish_conditions
            }
        elif bearish_score >= 3:
            return {
                'direction': 'bearish', 
                'type': 'vix_divergence',
                'score': bearish_score,
                'max_score': len(bearish_conditions),
                'fear_greed': current_fear_greed,
                'rsi': rsi,
                'conditions_met': bearish_conditions
            }
            
        return None
    
    def _build_signal(self, divergence: Dict, indicators: Dict, current_price: float, fear_greed: float) -> Dict:
        direction = divergence['direction']
        base_confidence = divergence['score'] / divergence['max_score']
        
        confidence_boosts = []
        
        if (direction == 'bullish' and fear_greed < 20) or (direction == 'bearish' and fear_greed > 80):
            confidence_boosts.append(0.1)
            
        if indicators['volume_ratio'] > 1.5:
            confidence_boosts.append(0.05)
            
        if abs(indicators['momentum_5']) > 3:
            confidence_boosts.append(0.05)
            
        final_confidence = min(0.95, base_confidence + sum(confidence_boosts))
        
        volatility = indicators['volatility']
        atr_estimate = current_price * volatility * 0.05
        
        if direction == 'bullish':
            stop_loss = current_price - (atr_estimate * 2.0)
            take_profit = current_price + (atr_estimate * 3.0)
        else:
            stop_loss = current_price + (atr_estimate * 2.0) 
            take_profit = current_price - (atr_estimate * 3.0)
        
        return {
            'signal': 'scherman_vix_divergence',
            'direction': 'long' if direction == 'bullish' else 'short',
            'confidence': final_confidence,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': 3.0 / 2.0,
            'fear_greed_level': fear_greed,
            'rsi': indicators['rsi'],
            'volume_confirmation': indicators['volume_ratio'] > 1.2,
            'timestamp': datetime.now(),
            'conditions_met': divergence['score'],
            'total_conditions': divergence['max_score'],
            'volatility': volatility,
            'methodology': 'Scherman VIX Divergence'
        }

class SchermanRiskManager:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.02)
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.10)
        
    def calculate_position_size(self, signal: Dict, portfolio_value: float, current_positions: int = 0) -> float:
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        confidence = signal['confidence']
        
        price_risk = abs(entry_price - stop_loss) / entry_price
        
        if price_risk == 0:
            return 0
            
        risk_amount = portfolio_value * self.max_risk_per_trade
        confidence_multiplier = confidence
        adjusted_risk = risk_amount * confidence_multiplier
        position_size = adjusted_risk / price_risk
        max_position = portfolio_value * 0.25
        position_size = min(position_size, max_position)
        
        if current_positions >= 3:
            position_size *= 0.5
            
        return max(0, position_size)
    
    def validate_signal(self, signal: Dict, portfolio_value: float, current_positions: List[Dict]) -> bool:
        if signal['confidence'] < 0.65:
            return False
            
        if signal.get('risk_reward_ratio', 0) < 1.5:
            return False
            
        total_risk = sum([pos.get('risk_amount', 0) for pos in current_positions])
        max_total_risk = portfolio_value * self.max_portfolio_risk
        
        if total_risk >= max_total_risk:
            return False
            
        return True
