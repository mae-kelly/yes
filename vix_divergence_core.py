import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SchermanVIXDivergenceCore:
    def __init__(self, config: Dict):
        self.config = config
        self.divergence_threshold = 0.12
        self.std_dev_threshold = 2.0
        self.lookback_period = 21
        self.confirmation_period = 3
        self.rsi_oversold = 35
        self.rsi_overbought = 65
        self.volume_threshold = 1.3
        self.fear_level_threshold = 30
        self.price_deviation_max = 1.8
        
    def detect_crypto_vix_divergence(self, btc_data: pd.DataFrame, fear_greed_data: List[float]) -> Dict:
        """
        Real Scherman VIX Divergence detection for crypto markets
        Uses Fear & Greed Index as VIX proxy
        """
        if len(btc_data) < 50 or len(fear_greed_data) < 10:
            return {}
            
        try:
            # Convert to simple lists to avoid numpy array issues
            close_prices = btc_data['close'].tolist()
            high_prices = btc_data['high'].tolist()
            low_prices = btc_data['low'].tolist()
            volumes = btc_data['volume'].tolist()
            
            current_price = close_prices[-1]
            
            # Calculate SMA and std using pure Python
            sma_20 = self._simple_moving_average(close_prices, 20)
            std_20 = self._standard_deviation(close_prices[-20:]) if len(close_prices) >= 20 else current_price * 0.02
            
            # Price lows analysis
            price_lows = self._rolling_min(low_prices, self.lookback_period)
            current_low = price_lows[-1] if price_lows else current_price
            prev_low = price_lows[-self.lookback_period-1] if len(price_lows) > self.lookback_period else current_low
            
            # Fear & Greed analysis
            fear_highs = self._rolling_max(fear_greed_data, 10)
            current_fear = fear_greed_data[-1]
            current_fear_high = fear_highs[-1] if fear_highs else current_fear
            prev_fear_high = fear_highs[-11] if len(fear_highs) > 10 else current_fear_high
            
            # Signal conditions
            lower_low = current_low < prev_low * (1 - self.divergence_threshold)
            fear_no_higher = current_fear_high <= prev_fear_high * 1.05
            within_std_bands = abs(current_price - sma_20) <= (self.std_dev_threshold * std_20)
            
            # RSI calculation
            rsi = self._calculate_rsi_simple(close_prices, 14)
            rsi_oversold_condition = rsi < self.rsi_oversold
            
            # Volume analysis
            volume_avg = self._simple_moving_average(volumes, 20)
            volume_ratio = volumes[-1] / volume_avg if volume_avg > 0 else 1.0
            volume_surge = volume_ratio > self.volume_threshold
            
            extreme_fear = current_fear < self.fear_level_threshold
            
            print(f"🔍 VIX Divergence Analysis:")
            print(f"   Lower Low: {lower_low} (Current: {current_low:.2f}, Prev: {prev_low:.2f})")
            print(f"   Fear No Higher: {fear_no_higher} (Current: {current_fear_high:.1f}, Prev: {prev_fear_high:.1f})")
            print(f"   Within Std Bands: {within_std_bands}")
            print(f"   RSI Oversold: {rsi_oversold_condition} (RSI: {rsi:.1f})")
            print(f"   Volume Surge: {volume_surge} (Ratio: {volume_ratio:.2f})")
            print(f"   Extreme Fear: {extreme_fear} (Fear: {current_fear:.1f})")
            
            signal_conditions = [
                lower_low,
                fear_no_higher, 
                within_std_bands,
                rsi_oversold_condition,
                volume_surge,
                extreme_fear
            ]
            
            confirmations = sum(signal_conditions)
            min_confirmations = 4
            
            if confirmations >= min_confirmations:
                confidence = self._calculate_divergence_confidence_simple(
                    close_prices, volumes, fear_greed_data, confirmations, len(signal_conditions)
                )
                
                # Calculate ATR using simple method
                atr = self._calculate_atr_simple(high_prices, low_prices, close_prices, 14)
                
                stop_distance = max(atr * 2.5, std_20 * 1.5)
                profit_distance = max(atr * 4.0, std_20 * 3.0)
                
                signal = {
                    'signal': 'vix_divergence',
                    'direction': 'long',
                    'confidence': confidence,
                    'entry_price': current_price,
                    'stop_loss': current_price - stop_distance,
                    'take_profit': current_price + profit_distance,
                    'timestamp': datetime.now(),
                    'confirmations': confirmations,
                    'total_conditions': len(signal_conditions),
                    'rsi': rsi,
                    'volume_ratio': volume_ratio,
                    'fear_level': current_fear,
                    'price_vs_sma': (current_price - sma_20) / sma_20,
                    'conditions_met': {
                        'lower_low': lower_low,
                        'fear_no_higher': fear_no_higher,
                        'within_std_bands': within_std_bands,
                        'rsi_oversold': rsi_oversold_condition,
                        'volume_surge': volume_surge,
                        'extreme_fear': extreme_fear
                    }
                }
                
                print(f"✅ VIX Divergence Signal Generated!")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Entry: ${current_price:.2f}")
                print(f"   Stop: ${signal['stop_loss']:.2f}")
                print(f"   Target: ${signal['take_profit']:.2f}")
                
                return signal
            else:
                print(f"❌ Insufficient confirmations: {confirmations}/{min_confirmations}")
                
        except Exception as e:
            print(f"❌ VIX Divergence detection error: {e}")
            
        return {}
        
    def _simple_moving_average(self, data: List[float], period: int) -> float:
        """Calculate simple moving average"""
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        return sum(data[-period:]) / period
        
    def _standard_deviation(self, data: List[float]) -> float:
        """Calculate standard deviation"""
        if len(data) < 2:
            return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance ** 0.5
        
    def _rolling_min(self, data: List[float], period: int) -> List[float]:
        """Calculate rolling minimum"""
        result = []
        for i in range(len(data)):
            start_idx = max(0, i - period + 1)
            window = data[start_idx:i+1]
            result.append(min(window) if window else 0)
        return result
        
    def _rolling_max(self, data: List[float], period: int) -> List[float]:
        """Calculate rolling maximum"""
        result = []
        for i in range(len(data)):
            start_idx = max(0, i - period + 1)
            window = data[start_idx:i+1]
            result.append(max(window) if window else 0)
        return result
        
    def _calculate_rsi_simple(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI using simple Python"""
        if len(prices) < period + 1:
            return 50.0
            
        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [change if change > 0 else 0 for change in changes]
        losses = [-change if change < 0 else 0 for change in changes]
        
        # Calculate average gains and losses
        if len(gains) < period or len(losses) < period:
            return 50.0
            
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def _calculate_atr_simple(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Calculate ATR using simple Python"""
        if len(highs) < period or len(lows) < period or len(closes) < period:
            return (max(highs[-10:]) - min(lows[-10:])) / 10 if len(highs) >= 10 else highs[-1] * 0.02
            
        true_ranges = []
        for i in range(1, len(highs)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            true_range = max(high_low, high_close, low_close)
            true_ranges.append(true_range)
            
        if len(true_ranges) < period:
            return sum(true_ranges) / len(true_ranges) if true_ranges else highs[-1] * 0.02
            
        return sum(true_ranges[-period:]) / period
        
    def _calculate_divergence_confidence_simple(self, prices: List[float], volumes: List[float], 
                                              fear_data: List[float], confirmations: int, total_conditions: int) -> float:
        """Calculate confidence using simple methods"""
        try:
            base_confidence = confirmations / total_conditions
            
            # RSI component
            rsi = self._calculate_rsi_simple(prices, 14)
            rsi_score = max(0, (self.rsi_oversold - rsi) / self.rsi_oversold) if rsi < self.rsi_oversold else 0
            
            # Volume component
            volume_avg = self._simple_moving_average(volumes, 20)
            volume_ratio = volumes[-1] / volume_avg if volume_avg > 0 else 1.0
            volume_score = min((volume_ratio - 1) / 2, 1.0) if volume_ratio > 1 else 0
            
            # Fear component
            fear_current = fear_data[-1]
            fear_score = max(0, (self.fear_level_threshold - fear_current) / self.fear_level_threshold) if fear_current < self.fear_level_threshold else 0
            
            weighted_confidence = (
                base_confidence * 0.40 +
                rsi_score * 0.25 + 
                volume_score * 0.20 + 
                fear_score * 0.15
            )
            
            confidence_multiplier = 1.4
            final_confidence = min(weighted_confidence * confidence_multiplier, 0.95)
            
            return max(final_confidence, 0.60)
            
        except Exception as e:
            print(f"❌ Confidence calculation error: {e}")
            return 0.65
            
    def validate_divergence_signal(self, signal: Dict, market_data: Dict) -> bool:
        """Enhanced signal validation with real market conditions"""
        if not signal or signal.get('confidence', 0) < 0.60:
            print("❌ Signal validation failed: Low confidence")
            return False
            
        volatility = market_data.get('volatility', 0.2)
        if volatility > 1.0:
            print(f"❌ Signal validation failed: Extreme volatility ({volatility:.2f})")
            return False
            
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if volume_ratio < 1.1:
            print(f"❌ Signal validation failed: Low volume ({volume_ratio:.2f})")
            return False
            
        spread_bps = market_data.get('spread_bps', 10)
        if spread_bps > 50:
            print(f"❌ Signal validation failed: Wide spread ({spread_bps:.1f} bps)")
            return False
            
        liquidity_score = market_data.get('liquidity_score', 0.8)
        if liquidity_score < 0.3:
            print(f"❌ Signal validation failed: Poor liquidity ({liquidity_score:.2f})")
            return False
            
        print("✅ Signal validation passed")
        return True
        
    def adjust_position_size(self, base_size: float, signal: Dict, market_conditions: Dict) -> float:
        """Dynamic position sizing based on signal quality and market conditions"""
        try:
            confidence = signal.get('confidence', 0.6)
            confirmations = signal.get('confirmations', 0)
            total_conditions = signal.get('total_conditions', 6)
            
            confidence_scalar = confidence
            confirmation_ratio = confirmations / total_conditions
            confirmation_scalar = 0.7 + (confirmation_ratio * 0.6)
            
            volatility = market_conditions.get('volatility', 0.2)
            vol_scalar = min(0.15 / volatility, 2.0) if volatility > 0 else 1.0
            
            liquidity_scalar = min(market_conditions.get('liquidity_score', 0.8) * 1.3, 1.0)
            
            fear_greed = market_conditions.get('fear_greed_index', 50)
            if fear_greed < 15:
                fear_scalar = 1.6
            elif fear_greed < 25:
                fear_scalar = 1.4
            elif fear_greed < 35:
                fear_scalar = 1.2
            else:
                fear_scalar = 1.0
                
            volume_ratio = market_conditions.get('volume_ratio', 1.0)
            volume_scalar = min(volume_ratio / 1.5, 1.3) if volume_ratio > 1.2 else 0.8
            
            rsi = signal.get('rsi', 50)
            rsi_scalar = 1.3 if rsi < 25 else 1.1 if rsi < 35 else 1.0
            
            kelly_fraction = self._calculate_kelly_fraction_simple(signal, market_conditions)
            
            final_scalar = (
                confidence_scalar * 
                confirmation_scalar * 
                vol_scalar * 
                liquidity_scalar * 
                fear_scalar * 
                volume_scalar * 
                rsi_scalar * 
                kelly_fraction
            )
            
            adjusted_size = base_size * final_scalar
            
            min_size = base_size * 0.2
            max_size = base_size * 3.0
            
            final_size = max(min_size, min(adjusted_size, max_size))
            
            print(f"📊 Position Size Adjustment:")
            print(f"   Base Size: {base_size:.2f}")
            print(f"   Final Size: {final_size:.2f}")
            
            return final_size
            
        except Exception as e:
            print(f"❌ Position sizing error: {e}")
            return base_size * 0.5
            
    def _calculate_kelly_fraction_simple(self, signal: Dict, market_conditions: Dict) -> float:
        """Calculate Kelly fraction for optimal position sizing"""
        try:
            confidence = signal.get('confidence', 0.6)
            win_probability = 0.45 + (confidence * 0.3)
            
            atr_multiple = 2.5
            profit_multiple = 4.0
            
            avg_win = profit_multiple * atr_multiple * 0.01
            avg_loss = atr_multiple * 0.01
            
            if avg_loss == 0:
                return 0.1
                
            kelly = (win_probability * avg_win - (1 - win_probability) * avg_loss) / avg_loss
            conservative_kelly = kelly * 0.25
            
            return max(0.05, min(conservative_kelly, 0.20))
            
        except Exception as e:
            print(f"❌ Kelly calculation error: {e}")
            return 0.10
