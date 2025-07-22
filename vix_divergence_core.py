import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import talib

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
            
        current_price = btc_data['close'].iloc[-1]
        sma_20 = btc_data['close'].rolling(20).mean().iloc[-1]
        std_20 = btc_data['close'].rolling(20).std().iloc[-1]
        
        price_lows = btc_data['low'].rolling(20).min()
        current_low = price_lows.iloc[-1]
        prev_low = price_lows.iloc[-21] if len(price_lows) > 20 else current_low
        
        fear_highs = pd.Series(fear_greed_data).rolling(10).max()
        current_fear_high = fear_highs.iloc[-1] if len(fear_highs) > 0 else 50
        prev_fear_high = fear_highs.iloc[-11] if len(fear_highs) > 10 else current_fear_high
        
        lower_low = current_low < prev_low * 0.995
        fear_no_higher = current_fear_high <= prev_fear_high * 1.02
        within_2std = abs(current_price - sma_20) <= (2.0 * std_20)
        
        rsi = talib.RSI(btc_data['close'].values, timeperiod=14)[-1]
        volume_ratio = btc_data['volume'].iloc[-1] / btc_data['volume'].rolling(20).mean().iloc[-1]
        
        if lower_low and fear_no_higher and within_2std and rsi < 40 and volume_ratio > 1.2:
            confidence = self._calculate_divergence_confidence(btc_data, fear_greed_data)
            atr = talib.ATR(btc_data['high'].values, btc_data['low'].values, btc_data['close'].values, timeperiod=14)[-1]
            
            return {
                'signal': 'vix_divergence',
                'direction': 'long',
                'confidence': confidence,
                'entry_price': current_price,
                'stop_loss': current_price - (2.5 * atr),
                'take_profit': current_price + (4.0 * atr),
                'timestamp': datetime.now(),
                'rsi': rsi,
                'volume_ratio': volume_ratio,
                'price_vs_sma': (current_price - sma_20) / sma_20
            }
            
        return {}
        
    def _calculate_divergence_confidence(self, btc_data: pd.DataFrame, fear_greed_data: List[float]) -> float:
        try:
            rsi = talib.RSI(btc_data['close'].values, timeperiod=14)[-1]
            rsi_score = (50 - rsi) / 50 if rsi < 50 else 0
            
            volume_sma = btc_data['volume'].rolling(20).mean().iloc[-1]
            volume_ratio = btc_data['volume'].iloc[-1] / volume_sma
            volume_score = min(volume_ratio / 3, 1.0)
            
            fear_current = fear_greed_data[-1]
            fear_score = (50 - fear_current) / 50 if fear_current < 50 else 0
            
            macd, macd_signal, macd_hist = talib.MACD(btc_data['close'].values)
            macd_score = 0.5 if macd_hist[-1] > macd_hist[-2] else 0
            
            bb_upper, bb_middle, bb_lower = talib.BBANDS(btc_data['close'].values, timeperiod=20)
            bb_position = (btc_data['close'].iloc[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
            bb_score = 1 - bb_position if bb_position < 0.5 else 0
            
            confidence = (rsi_score * 0.25 + volume_score * 0.20 + fear_score * 0.25 + 
                         macd_score * 0.15 + bb_score * 0.15)
            
            return min(max(confidence * 1.4, 0.6), 0.95)
            
        except Exception:
            return 0.65
            
    def validate_divergence_signal(self, signal: Dict, market_data: Dict) -> bool:
        if not signal or signal.get('confidence', 0) < 0.65:
            return False
            
        volatility = market_data.get('volatility', 0.2)
        if volatility > 0.8:
            return False
            
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if volume_ratio < 1.1:
            return False
            
        spread_bps = market_data.get('spread_bps', 10)
        if spread_bps > 25:
            return False
            
        return True
        
    def adjust_position_size(self, base_size: float, signal: Dict, market_conditions: Dict) -> float:
        confidence = signal.get('confidence', 0.6)
        volatility = market_conditions.get('volatility', 0.2)
        
        vol_scalar = min(0.20 / volatility, 2.5) if volatility > 0 else 1.0
        
        liquidity_scalar = min(market_conditions.get('liquidity_score', 0.8) * 1.3, 1.0)
        
        fear_greed = market_conditions.get('fear_greed_index', 50)
        fear_scalar = 1.4 if fear_greed < 20 else 1.2 if fear_greed < 35 else 1.0
        
        kelly_fraction = 0.15
        
        adjusted_size = base_size * confidence * vol_scalar * liquidity_scalar * fear_scalar * kelly_fraction
        
        return min(max(adjusted_size, base_size * 0.3), base_size * 2.5)
