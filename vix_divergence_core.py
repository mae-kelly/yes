import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SchermanVIXDivergenceCore:
    def __init__(self, config: Dict):
        self.config = config
        self.divergence_threshold = 0.15
        self.std_dev_threshold = 2.0
        self.lookback_period = 30
        self.confirmation_period = 3
        
    def detect_crypto_vix_divergence(self, btc_data: pd.DataFrame, fear_greed_data: List[float]) -> Dict:
        if len(btc_data) < 50 or len(fear_greed_data) < 10:
            return {}
            
        btc_lows = btc_data['low'].rolling(20).min()
        btc_current_low = btc_lows.iloc[-1]
        btc_prev_low = btc_lows.iloc[-20:-1].min()
        
        fear_highs = pd.Series(fear_greed_data).rolling(10).max()
        fear_current_high = fear_highs.iloc[-1] if len(fear_highs) > 0 else 50
        fear_prev_high = fear_highs.iloc[-10:-1].max() if len(fear_highs) > 10 else 50
        
        btc_lower_low = btc_current_low < btc_prev_low
        fear_no_higher_high = fear_current_high <= fear_prev_high
        
        btc_sma = btc_data['close'].rolling(self.lookback_period).mean().iloc[-1]
        btc_std = btc_data['close'].rolling(self.lookback_period).std().iloc[-1]
        btc_current = btc_data['close'].iloc[-1]
        
        within_std_dev = abs(btc_current - btc_sma) <= (self.std_dev_threshold * btc_std)
        
        divergence_detected = btc_lower_low and fear_no_higher_high and within_std_dev
        
        if divergence_detected:
            confidence = self._calculate_divergence_confidence(btc_data, fear_greed_data)
            direction = 'long' if btc_current < btc_sma else 'short'
            
            return {
                'signal': 'vix_divergence',
                'direction': direction,
                'confidence': confidence,
                'entry_price': btc_current,
                'stop_loss': btc_current * (0.97 if direction == 'long' else 1.03),
                'take_profit': btc_current * (1.06 if direction == 'long' else 0.94),
                'timestamp': datetime.now()
            }
            
        return {}
        
    def _calculate_divergence_confidence(self, btc_data: pd.DataFrame, fear_greed_data: List[float]) -> float:
        rsi = self._calculate_rsi(btc_data['close'], 14)
        volume_surge = btc_data['volume'].iloc[-1] / btc_data['volume'].rolling(20).mean().iloc[-1]
        fear_extreme = 1.0 - abs(fear_greed_data[-1] - 50) / 50
        
        confidence = (rsi / 100) * 0.4 + min(volume_surge / 2, 1) * 0.3 + fear_extreme * 0.3
        return min(max(confidence, 0.5), 0.95)
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50.0

    def validate_divergence_signal(self, signal: Dict, market_data: Dict) -> bool:
        if not signal or signal.get('confidence', 0) < 0.6:
            return False
            
        volatility = market_data.get('volatility', 0.2)
        if volatility > 0.8:
            return False
            
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if volume_ratio < 0.8:
            return False
            
        return True
        
    def adjust_position_size(self, base_size: float, signal: Dict, market_conditions: Dict) -> float:
        confidence_multiplier = signal.get('confidence', 0.6)
        volatility_factor = 1.0 / (1.0 + market_conditions.get('volatility', 0.2))
        liquidity_factor = min(market_conditions.get('liquidity_score', 0.8), 1.0)
        
        adjusted_size = base_size * confidence_multiplier * volatility_factor * liquidity_factor
        return min(max(adjusted_size, base_size * 0.3), base_size * 1.5)