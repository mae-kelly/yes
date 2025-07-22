import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import talib
import warnings
warnings.filterwarnings('ignore')

class SchermanSignalGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.vix_divergence_threshold = config.get('vix_divergence_threshold', 0.15)
        self.momentum_lookback = config.get('momentum_lookback', 20)
        self.mean_reversion_lookback = config.get('mean_reversion_lookback', 50)
        self.volume_surge_threshold = config.get('volume_surge_threshold', 2.0)
        self.volatility_regime_threshold = config.get('volatility_regime_threshold', 0.25)
        self.correlation_threshold = config.get('correlation_threshold', 0.7)
        self.signal_decay_factor = config.get('signal_decay_factor', 0.95)
        self.min_signal_strength = config.get('min_signal_strength', 0.6)
        self.max_signal_strength = config.get('max_signal_strength', 1.0)
        self.signal_combination_weights = {'momentum': 0.3, 'mean_reversion': 0.2, 'volume': 0.15, 'volatility': 0.15, 'divergence': 0.2}
        self.scherman_params = {'vix_sensitivity': 1.5, 'momentum_strength': 2.0, 'reversal_sensitivity': 1.2, 'volume_importance': 1.8, 'volatility_scaling': 2.5}
        self.signal_filters = {'min_confidence': 0.65, 'max_correlation': 0.8, 'min_volume_ratio': 1.5, 'volatility_adjustment': True, 'regime_filtering': True}
        self.adaptive_parameters = {'momentum_adaptive': True, 'volatility_adaptive': True, 'volume_adaptive': True, 'correlation_adaptive': True}
        self.regime_adjustments = {'bull_market': 1.2, 'bear_market': 0.8, 'sideways_market': 1.0, 'high_volatility': 0.7, 'low_volatility': 1.3}
        
    def generate_scherman_signals(self, data: pd.DataFrame, symbol: str, market_data: Dict = None) -> Dict:
        try:
            if len(data) < 100:
                return self._empty_signal()
            features = self._calculate_scherman_features(data, symbol)
            momentum_signals = self._generate_momentum_signals(features, data)
            mean_reversion_signals = self._generate_mean_reversion_signals(features, data)
            volume_signals = self._generate_volume_signals(features, data)
            volatility_signals = self._generate_volatility_signals(features, data)
            divergence_signals = self._generate_divergence_signals(features, data, market_data)
            combined_signal = self._combine_signals(momentum_signals, mean_reversion_signals, volume_signals, volatility_signals, divergence_signals)
            filtered_signal = self._apply_signal_filters(combined_signal, features, data)
            final_signal = self._apply_regime_adjustments(filtered_signal, features, data)
            return self._format_final_signal(final_signal, symbol, features)
        except Exception as e:
            print(f"Error generating Scherman signals for {symbol}: {e}")
            return self._empty_signal()
            
    def _calculate_scherman_features(self, data: pd.DataFrame, symbol: str) -> Dict:
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            volume = data['volume'].values
            features = {}
            features['returns'] = np.diff(np.log(close))
            features['volatility'] = pd.Series(close).pct_change().rolling(20).std().iloc[-1] * np.sqrt(365)
            features['rsi'] = talib.RSI(close, timeperiod=14)[-1] if len(close) > 14 else 50
            features['macd'], features['macd_signal'], features['macd_hist'] = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            features['macd'] = features['macd'][-1] if features['macd'] is not None and len(features['macd']) > 0 else 0
            features['macd_signal'] = features['macd_signal'][-1] if features['macd_signal'] is not None and len(features['macd_signal']) > 0 else 0
            features['macd_hist'] = features['macd_hist'][-1] if features['macd_hist'] is not None and len(features['macd_hist']) > 0 else 0
            features['bb_upper'], features['bb_middle'], features['bb_lower'] = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            features['bb_upper'] = features['bb_upper'][-1] if features['bb_upper'] is not None else close[-1] * 1.02
            features['bb_middle'] = features['bb_middle'][-1] if features['bb_middle'] is not None else close[-1]
            features['bb_lower'] = features['bb_lower'][-1] if features['bb_lower'] is not None else close[-1] * 0.98
            features['bb_position'] = (close[-1] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower']) if (features['bb_upper'] - features['bb_lower']) > 0 else 0.5
            features['atr'] = talib.ATR(high, low, close, timeperiod=14)[-1] if len(close) > 14 else (np.max(high[-14:]) - np.min(low[-14:])) / 14
            features['adx'] = talib.ADX(high, low, close, timeperiod=14)[-1] if len(close) > 14 else 25
            features['stoch_k'], features['stoch_d'] = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
            features['stoch_k'] = features['stoch_k'][-1] if features['stoch_k'] is not None and len(features['stoch_k']) > 0 else 50
            features['stoch_d'] = features['stoch_d'][-1] if features['stoch_d'] is not None and len(features['stoch_d']) > 0 else 50
            features['cci'] = talib.CCI(high, low, close, timeperiod=14)[-1] if len(close) > 14 else 0
            features['williams_r'] = talib.WILLR(high, low, close, timeperiod=14)[-1] if len(close) > 14 else -50
            features['roc'] = talib.ROC(close, timeperiod=10)[-1] if len(close) > 10 else 0
            features['mfi'] = talib.MFI(high, low, close, volume, timeperiod=14)[-1] if len(close) > 14 else 50
            features['obv'] = talib.OBV(close, volume)[-1] if len(close) > 1 else volume[-1]
            features['volume_sma'] = np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)
            features['volume_ratio'] = volume[-1] / features['volume_sma'] if features['volume_sma'] > 0 else 1.0
            features['price_momentum_5'] = (close[-1] / close[-6] - 1) * 100 if len(close) > 5 else 0
            features['price_momentum_10'] = (close[-1] / close[-11] - 1) * 100 if len(close) > 10 else 0
            features['price_momentum_20'] = (close[-1] / close[-21] - 1) * 100 if len(close) > 20 else 0
            features['sma_5'] = np.mean(close[-5:]) if len(close) >= 5 else close[-1]
            features['sma_10'] = np.mean(close[-10:]) if len(close) >= 10 else close[-1]
            features['sma_20'] = np.mean(close[-20:]) if len(close) >= 20 else close[-1]
            features['sma_50'] = np.mean(close[-50:]) if len(close) >= 50 else close[-1]
            features['price_vs_sma20'] = (close[-1] / features['sma_20'] - 1) * 100
            features['sma_slope'] = (features['sma_20'] - np.mean(close[-25:-5])) / np.mean(close[-25:-5]) * 100 if len(close) >= 25 else 0
            features['trend_strength'] = features['adx'] / 100
            features['momentum_divergence'] = self._calculate_momentum_divergence(close, features['rsi'])
            features['volume_price_trend'] = self._calculate_volume_price_trend(close, volume)
            features['volatility_breakout'] = self._calculate_volatility_breakout(close, features['atr'])
            return features
        except Exception as e:
            print(f"Error calculating Scherman features: {e}")
            return {}
            
    def _calculate_momentum_divergence(self, prices: np.ndarray, rsi: float) -> float:
        try:
            if len(prices) < 20:
                return 0.0
            price_momentum = (prices[-1] / prices[-20] - 1) * 100
            rsi_momentum = (rsi - 50) * 2
            divergence = abs(price_momentum) - abs(rsi_momentum)
            return np.clip(divergence / 100, -1.0, 1.0)
        except Exception as e:
            return 0.0
            
    def _calculate_volume_price_trend(self, prices: np.ndarray, volumes: np.ndarray) -> float:
        try:
            if len(prices) < 10 or len(volumes) < 10:
                return 0.0
            price_change = np.diff(prices[-10:])
            volume_weighted_price = np.average(price_change, weights=volumes[-9:])
            return np.clip(volume_weighted_price * 1000, -1.0, 1.0)
        except Exception as e:
            return 0.0
            
    def _calculate_volatility_breakout(self, prices: np.ndarray, atr: float) -> float:
        try:
            if len(prices) < 20:
                return 0.0
            recent_range = np.max(prices[-5:]) - np.min(prices[-5:])
            normalized_range = recent_range / atr if atr > 0 else 0
            return np.clip((normalized_range - 1.0), -1.0, 1.0)
        except Exception as e:
            return 0.0
            
    def _generate_momentum_signals(self, features: Dict, data: pd.DataFrame) -> Dict:
        try:
            momentum_score = 0.0
            momentum_confidence = 0.0
            rsi = features.get('rsi', 50)
            macd_hist = features.get('macd_hist', 0)
            price_momentum_20 = features.get('price_momentum_20', 0)
            adx = features.get('adx', 25)
            stoch_k = features.get('stoch_k', 50)
            rsi_signal = 0
            if rsi > 70:
                rsi_signal = -1
            elif rsi < 30:
                rsi_signal = 1
            else:
                rsi_signal = (50 - rsi) / 20
            macd_signal = np.clip(macd_hist * 100, -1, 1)
            price_momentum_signal = np.clip(price_momentum_20 / 10, -1, 1)
            trend_strength = adx / 100
            stoch_signal = 0
            if stoch_k > 80:
                stoch_signal = -1
            elif stoch_k < 20:
                stoch_signal = 1
            else:
                stoch_signal = (50 - stoch_k) / 30
            momentum_score = (rsi_signal * 0.3 + macd_signal * 0.3 + price_momentum_signal * 0.25 + stoch_signal * 0.15) * self.scherman_params['momentum_strength']
            momentum_confidence = min(trend_strength * 1.5, 1.0)
            momentum_direction = 'bullish' if momentum_score > 0 else 'bearish'
            return {'score': momentum_score, 'confidence': momentum_confidence, 'direction': momentum_direction, 'components': {'rsi': rsi_signal, 'macd': macd_signal, 'price_momentum': price_momentum_signal, 'stoch': stoch_signal}}
        except Exception as e:
            print(f"Error generating momentum signals: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'direction': 'neutral', 'components': {}}
            
    def _generate_mean_reversion_signals(self, features: Dict, data: pd.DataFrame) -> Dict:
        try:
            reversion_score = 0.0
            reversion_confidence = 0.0
            bb_position = features.get('bb_position', 0.5)
            rsi = features.get('rsi', 50)
            price_vs_sma20 = features.get('price_vs_sma20', 0)
            williams_r = features.get('williams_r', -50)
            cci = features.get('cci', 0)
            bb_signal = 0
            if bb_position > 0.9:
                bb_signal = -1
            elif bb_position < 0.1:
                bb_signal = 1
            else:
                bb_signal = (0.5 - bb_position) * 2
            rsi_reversion = 0
            if rsi > 80:
                rsi_reversion = -1
            elif rsi < 20:
                rsi_reversion = 1
            else:
                rsi_reversion = 0
            sma_reversion = np.clip(-price_vs_sma20 / 5, -1, 1)
            williams_reversion = 0
            if williams_r > -20:
                williams_reversion = -1
            elif williams_r < -80:
                williams_reversion = 1
            cci_reversion = 0
            if cci > 100:
                cci_reversion = -1
            elif cci < -100:
                cci_reversion = 1
            reversion_score = (bb_signal * 0.4 + rsi_reversion * 0.25 + sma_reversion * 0.2 + williams_reversion * 0.1 + cci_reversion * 0.05) * self.scherman_params['reversal_sensitivity']
            volatility = features.get('volatility', 0.2)
            reversion_confidence = min(volatility * 3, 1.0)
            reversion_direction = 'bullish' if reversion_score > 0 else 'bearish'
            return {'score': reversion_score, 'confidence': reversion_confidence, 'direction': reversion_direction, 'components': {'bb': bb_signal, 'rsi': rsi_reversion, 'sma': sma_reversion, 'williams': williams_reversion, 'cci': cci_reversion}}
        except Exception as e:
            print(f"Error generating mean reversion signals: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'direction': 'neutral', 'components': {}}
            
    def _generate_volume_signals(self, features: Dict, data: pd.DataFrame) -> Dict:
        try:
            volume_score = 0.0
            volume_confidence = 0.0
            volume_ratio = features.get('volume_ratio', 1.0)
            mfi = features.get('mfi', 50)
            obv = features.get('obv', 0)
            volume_price_trend = features.get('volume_price_trend', 0)
            volume_surge = min((volume_ratio - 1) * 2, 2.0)
            mfi_signal = 0
            if mfi > 80:
                mfi_signal = -0.5
            elif mfi < 20:
                mfi_signal = 0.5
            else:
                mfi_signal = (50 - mfi) / 60
            obv_momentum = volume_price_trend
            volume_score = (volume_surge * 0.5 + mfi_signal * 0.3 + obv_momentum * 0.2) * self.scherman_params['volume_importance']
            volume_confidence = min(volume_ratio / 2, 1.0)
            volume_direction = 'bullish' if volume_score > 0 else 'bearish'
            return {'score': volume_score, 'confidence': volume_confidence, 'direction': volume_direction, 'components': {'volume_surge': volume_surge, 'mfi': mfi_signal, 'obv_momentum': obv_momentum}}
        except Exception as e:
            print(f"Error generating volume signals: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'direction': 'neutral', 'components': {}}
            
    def _generate_volatility_signals(self, features: Dict, data: pd.DataFrame) -> Dict:
        try:
            volatility_score = 0.0
            volatility_confidence = 0.0
            volatility = features.get('volatility', 0.2)
            atr = features.get('atr', 0)
            volatility_breakout = features.get('volatility_breakout', 0)
            vol_regime = self._classify_volatility_regime(volatility)
            vol_percentile = self._calculate_volatility_percentile(data['close'].pct_change(), volatility)
            breakout_signal = volatility_breakout
            regime_signal = 0
            if vol_regime == 'low':
                regime_signal = 0.3
            elif vol_regime == 'high':
                regime_signal = -0.3
            percentile_signal = (vol_percentile - 0.5) * 2
            volatility_score = (breakout_signal * 0.5 + regime_signal * 0.3 + percentile_signal * 0.2) * self.scherman_params['volatility_scaling']
            volatility_confidence = min(abs(vol_percentile - 0.5) * 4, 1.0)
            volatility_direction = 'bullish' if volatility_score > 0 else 'bearish'
            return {'score': volatility_score, 'confidence': volatility_confidence, 'direction': volatility_direction, 'regime': vol_regime, 'components': {'breakout': breakout_signal, 'regime': regime_signal, 'percentile': percentile_signal}}
        except Exception as e:
            print(f"Error generating volatility signals: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'direction': 'neutral', 'regime': 'normal', 'components': {}}
            
    def _classify_volatility_regime(self, volatility: float) -> str:
        if volatility < 0.15:
            return 'low'
        elif volatility < 0.3:
            return 'normal'
        elif volatility < 0.5:
            return 'high'
        else:
            return 'extreme'
            
    def _calculate_volatility_percentile(self, returns: pd.Series, current_vol: float) -> float:
        try:
            if len(returns) < 100:
                return 0.5
            historical_vols = returns.rolling(20).std()
            historical_vols = historical_vols.dropna()
            if len(historical_vols) == 0:
                return 0.5
            percentile = (historical_vols <= current_vol).mean()
            return percentile
        except Exception as e:
            return 0.5
            
    def _generate_divergence_signals(self, features: Dict, data: pd.DataFrame, market_data: Dict = None) -> Dict:
        try:
            divergence_score = 0.0
            divergence_confidence = 0.0
            momentum_divergence = features.get('momentum_divergence', 0)
            price_momentum = features.get('price_momentum_20', 0)
            rsi = features.get('rsi', 50)
            macd_hist = features.get('macd_hist', 0)
            price_direction = 1 if price_momentum > 0 else -1
            rsi_direction = 1 if rsi > 50 else -1
            macd_direction = 1 if macd_hist > 0 else -1
            price_rsi_divergence = 0
            if price_direction != rsi_direction and abs(price_momentum) > 2:
                price_rsi_divergence = -price_direction * 0.5
            price_macd_divergence = 0
            if price_direction != macd_direction and abs(price_momentum) > 2:
                price_macd_divergence = -price_direction * 0.4
            momentum_div_signal = momentum_divergence * 0.6
            vix_divergence = 0
            if market_data and 'vix' in market_data:
                vix_divergence = self._calculate_vix_divergence(price_momentum, market_data['vix'])
            divergence_score = (price_rsi_divergence + price_macd_divergence + momentum_div_signal + vix_divergence) * self.scherman_params['vix_sensitivity']
            divergence_confidence = min(abs(momentum_divergence) * 2 + abs(price_rsi_divergence) + abs(price_macd_divergence), 1.0)
            divergence_direction = 'bullish' if divergence_score > 0 else 'bearish'
            return {'score': divergence_score, 'confidence': divergence_confidence, 'direction': divergence_direction, 'components': {'price_rsi': price_rsi_divergence, 'price_macd': price_macd_divergence, 'momentum': momentum_div_signal, 'vix': vix_divergence}}
        except Exception as e:
            print(f"Error generating divergence signals: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'direction': 'neutral', 'components': {}}
            
    def _calculate_vix_divergence(self, price_momentum: float, vix_data: float) -> float:
        try:
            expected_vix_direction = -1 if price_momentum > 0 else 1
            actual_vix_direction = 1 if vix_data > 20 else -1
            if expected_vix_direction != actual_vix_direction:
                return expected_vix_direction * 0.3
            return 0.0
        except Exception as e:
            return 0.0
            
    def _combine_signals(self, momentum: Dict, mean_reversion: Dict, volume: Dict, volatility: Dict, divergence: Dict) -> Dict:
        try:
            weights = self.signal_combination_weights
            combined_score = (momentum['score'] * weights['momentum'] + mean_reversion['score'] * weights['mean_reversion'] + volume['score'] * weights['volume'] + volatility['score'] * weights['volatility'] + divergence['score'] * weights['divergence'])
            combined_confidence = (momentum['confidence'] * weights['momentum'] + mean_reversion['confidence'] * weights['mean_reversion'] + volume['confidence'] * weights['volume'] + volatility['confidence'] * weights['volatility'] + divergence['confidence'] * weights['divergence'])
            normalized_score = np.clip(combined_score, -1.0, 1.0)
            normalized_confidence = np.clip(combined_confidence, 0.0, 1.0)
            if abs(normalized_score) < 0.1:
                signal_direction = 'neutral'
            elif normalized_score > 0:
                signal_direction = 'bullish'
            else:
                signal_direction = 'bearish'
            signal_strength = abs(normalized_score) * normalized_confidence
            return {'score': normalized_score, 'confidence': normalized_confidence, 'direction': signal_direction, 'strength': signal_strength, 'components': {'momentum': momentum, 'mean_reversion': mean_reversion, 'volume': volume, 'volatility': volatility, 'divergence': divergence}}
        except Exception as e:
            print(f"Error combining signals: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'direction': 'neutral', 'strength': 0.0, 'components': {}}
            
    def _apply_signal_filters(self, signal: Dict, features: Dict, data: pd.DataFrame) -> Dict:
        try:
            filtered_signal = signal.copy()
            min_confidence = self.signal_filters['min_confidence']
            if signal['confidence'] < min_confidence:
                filtered_signal['score'] *= 0.5
                filtered_signal['strength'] *= 0.5
            volume_ratio = features.get('volume_ratio', 1.0)
            min_volume_ratio = self.signal_filters['min_volume_ratio']
            if volume_ratio < min_volume_ratio:
                filtered_signal['score'] *= 0.7
                filtered_signal['strength'] *= 0.7
            volatility = features.get('volatility', 0.2)
            if self.signal_filters['volatility_adjustment']:
                if volatility > 0.5:
                    filtered_signal['score'] *= 0.8
                    filtered_signal['strength'] *= 0.8
                elif volatility < 0.1:
                    filtered_signal['score'] *= 1.2
                    filtered_signal['strength'] *= 1.2
            if self.signal_filters['regime_filtering']:
                regime = self._detect_market_regime(data)
                if regime == 'choppy':
                    filtered_signal['score'] *= 0.6
                    filtered_signal['strength'] *= 0.6
            return filtered_signal
        except Exception as e:
            print(f"Error applying signal filters: {e}")
            return signal
            
    def _detect_market_regime(self, data: pd.DataFrame) -> str:
        try:
            if len(data) < 50:
                return 'normal'
            returns = data['close'].pct_change().dropna()
            recent_returns = returns.tail(20)
            volatility = recent_returns.std()
            trend = recent_returns.mean()
            if volatility > 0.04:
                return 'choppy'
            elif abs(trend) > 0.002:
                return 'trending'
            else:
                return 'normal'
        except Exception as e:
            return 'normal'
            
    def _apply_regime_adjustments(self, signal: Dict, features: Dict, data: pd.DataFrame) -> Dict:
        try:
            adjusted_signal = signal.copy()
            if not self.adaptive_parameters.get('volatility_adaptive', True):
                return adjusted_signal
            volatility = features.get('volatility', 0.2)
            vol_regime = self._classify_volatility_regime(volatility)
            regime_multiplier = self.regime_adjustments.get(vol_regime, 1.0)
            adjusted_signal['score'] *= regime_multiplier
            adjusted_signal['strength'] *= regime_multiplier
            market_regime = self._detect_market_regime(data)
            market_multiplier = 1.0
            if market_regime == 'trending':
                market_multiplier = 1.1
            elif market_regime == 'choppy':
                market_multiplier = 0.9
            adjusted_signal['score'] *= market_multiplier
            adjusted_signal['strength'] *= market_multiplier
            return adjusted_signal
        except Exception as e:
            print(f"Error applying regime adjustments: {e}")
            return signal
            
    def _format_final_signal(self, signal: Dict, symbol: str, features: Dict) -> Dict:
        try:
            score = signal.get('score', 0.0)
            confidence = signal.get('confidence', 0.0)
            strength = signal.get('strength', 0.0)
            if strength < self.min_signal_strength:
                action = 'hold'
                position_size = 0.0
            elif score > 0.3:
                action = 'strong_buy'
                position_size = min(strength * 1.5, 1.0)
            elif score > 0.1:
                action = 'buy'
                position_size = min(strength, 0.8)
            elif score < -0.3:
                action = 'strong_sell'
                position_size = min(strength * 1.5, 1.0)
            elif score < -0.1:
                action = 'sell'
                position_size = min(strength, 0.8)
            else:
                action = 'hold'
                position_size = 0.0
            return {'symbol': symbol, 'action': action, 'score': score, 'confidence': confidence, 'strength': strength, 'position_size': position_size, 'direction': signal.get('direction', 'neutral'), 'timestamp': datetime.now(), 'features': features, 'components': signal.get('components', {}), 'risk_level': self._calculate_risk_level(strength, confidence), 'expected_return': self._estimate_expected_return(score, strength), 'holding_period': self._estimate_holding_period(signal, features)}
        except Exception as e:
            print(f"Error formatting final signal: {e}")
            return self._empty_signal()
            
    def _calculate_risk_level(self, strength: float, confidence: float) -> str:
        risk_score = strength * (1 - confidence)
        if risk_score < 0.2:
            return 'low'
        elif risk_score < 0.5:
            return 'medium'
        else:
            return 'high'
            
    def _estimate_expected_return(self, score: float, strength: float) -> float:
        base_return = abs(score) * 0.05
        strength_multiplier = 1 + strength
        return base_return * strength_multiplier * (1 if score > 0 else -1)
        
    def _estimate_holding_period(self, signal: Dict, features: Dict) -> int:
        base_period = 4
        volatility = features.get('volatility', 0.2)
        if volatility > 0.4:
            return max(base_period // 2, 1)
        elif volatility < 0.15:
            return base_period * 2
        return base_period
        
    def _empty_signal(self) -> Dict:
        return {'symbol': '', 'action': 'hold', 'score': 0.0, 'confidence': 0.0, 'strength': 0.0, 'position_size': 0.0, 'direction': 'neutral', 'timestamp': datetime.now(), 'features': {}, 'components': {}, 'risk_level': 'low', 'expected_return': 0.0, 'holding_period': 4}