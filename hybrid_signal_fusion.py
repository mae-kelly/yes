import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class HybridSignalFusion:
    def __init__(self, config: Dict):
        self.config = config
        self.scherman_weight = 0.70
        self.renaissance_weight = 0.30
        self.min_confidence_threshold = 0.62
        self.signal_history = []
        self.performance_tracking = {}
        self.adaptive_weights = True
        
    def fuse_signals(self, scherman_signal: Dict, renaissance_prediction: Dict, market_data: Dict) -> Dict:
        """Real-time signal fusion with adaptive weighting"""
        if not scherman_signal and not renaissance_prediction:
            print("❌ No signals to fuse")
            return {}
            
        print(f"🔄 Fusing signals:")
        print(f"   Scherman: {bool(scherman_signal)}")
        print(f"   Renaissance: {bool(renaissance_prediction)}")
        
        if self.adaptive_weights:
            self._update_adaptive_weights()
            
        scherman_score = self._normalize_scherman_signal(scherman_signal)
        renaissance_score = self._normalize_renaissance_prediction(renaissance_prediction)
        
        print(f"   Scherman Score: {scherman_score:.3f} (weight: {self.scherman_weight:.2f})")
        print(f"   Renaissance Score: {renaissance_score:.3f} (weight: {self.renaissance_weight:.2f})")
        
        combined_score = (scherman_score * self.scherman_weight + 
                         renaissance_score * self.renaissance_weight)
        
        direction, strength = self._determine_direction_and_strength(
            scherman_signal, renaissance_prediction, combined_score
        )
        
        confidence = self._calculate_fusion_confidence(
            scherman_signal, renaissance_prediction, market_data
        )
        
        market_regime_adjustment = self._apply_market_regime_adjustment(
            combined_score, confidence, market_data
        )
        
        final_score = combined_score * market_regime_adjustment
        final_confidence = confidence * market_regime_adjustment
        
        print(f"   Combined Score: {combined_score:.3f}")
        print(f"   Final Score: {final_score:.3f}")
        print(f"   Confidence: {final_confidence:.3f}")
        
        if final_confidence < self.min_confidence_threshold:
            print(f"❌ Signal rejected: Low confidence ({final_confidence:.3f} < {self.min_confidence_threshold})")
            return {}
            
        fused_signal = {
            'signal': 'hybrid_fusion',
            'direction': direction,
            'strength': strength,
            'confidence': final_confidence,
            'combined_score': final_score,
            'scherman_component': scherman_score,
            'renaissance_component': renaissance_score,
            'market_regime_adjustment': market_regime_adjustment,
            'entry_price': market_data.get('current_price', 0),
            'stop_loss': self._calculate_stop_loss(direction, market_data, final_confidence),
            'take_profit': self._calculate_take_profit(direction, market_data, final_confidence),
            'position_size_multiplier': self._calculate_size_multiplier(final_confidence, market_data),
            'risk_reward_ratio': self._calculate_risk_reward_ratio(direction, market_data),
            'expected_holding_period': self._estimate_holding_period(strength, market_data),
            'signal_quality': self._assess_signal_quality(scherman_signal, renaissance_prediction),
            'timestamp': datetime.now(),
            'weights_used': {
                'scherman': self.scherman_weight,
                'renaissance': self.renaissance_weight
            }
        }
        
        self.signal_history.append(fused_signal)
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]
            
        print(f"✅ Fused signal generated:")
        print(f"   Direction: {direction}")
        print(f"   Strength: {strength:.3f}")
        print(f"   Entry: ${fused_signal['entry_price']:.2f}")
        print(f"   Stop: ${fused_signal['stop_loss']:.2f}")
        print(f"   Target: ${fused_signal['take_profit']:.2f}")
        print(f"   R/R: {fused_signal['risk_reward_ratio']:.2f}")
        
        return fused_signal
        
    def _normalize_scherman_signal(self, signal: Dict) -> float:
        """Normalize Scherman VIX divergence signal to [-1, 1] range"""
        if not signal:
            return 0.0
            
        base_confidence = signal.get('confidence', 0.0)
        confirmations = signal.get('confirmations', 0)
        total_conditions = signal.get('total_conditions', 6)
        
        confirmation_ratio = confirmations / total_conditions if total_conditions > 0 else 0
        
        signal_strength = base_confidence * confirmation_ratio
        
        if signal.get('signal') == 'vix_divergence':
            signal_strength *= 1.4
            
        rsi = signal.get('rsi', 50)
        if rsi < 25:
            signal_strength *= 1.3
        elif rsi < 35:
            signal_strength *= 1.1
            
        volume_ratio = signal.get('volume_ratio', 1.0)
        if volume_ratio > 2.0:
            signal_strength *= 1.2
        elif volume_ratio > 1.5:
            signal_strength *= 1.1
            
        direction_multiplier = 1.0 if signal.get('direction') == 'long' else -1.0
        
        normalized_score = np.clip(signal_strength * direction_multiplier, -1.0, 1.0)
        
        return normalized_score
        
    def _normalize_renaissance_prediction(self, prediction: Dict) -> float:
        """Normalize Renaissance ML prediction to [-1, 1] range"""
        if not prediction:
            return 0.0
            
        try:
            if 'ensemble' in prediction:
                ensemble_data = prediction['ensemble']
                
                if isinstance(ensemble_data, dict) and 'predictions' in ensemble_data:
                    class_probs = ensemble_data['predictions']
                    
                    if isinstance(class_probs, dict) and len(class_probs) > 0:
                        values = list(class_probs.values())
                        if len(values) >= 5:
                            bearish_prob = values[0] + values[1]
                            neutral_prob = values[2]
                            bullish_prob = values[3] + values[4]
                        else:
                            bearish_prob = sum(values[:len(values)//3])
                            neutral_prob = sum(values[len(values)//3:2*len(values)//3])
                            bullish_prob = sum(values[2*len(values)//3:])
                    elif isinstance(class_probs, list) and len(class_probs) >= 5:
                        bearish_prob = class_probs[0] + class_probs[1]
                        neutral_prob = class_probs[2]
                        bullish_prob = class_probs[3] + class_probs[4]
                    else:
                        return 0.0
                        
                    net_sentiment = bullish_prob - bearish_prob
                    confidence = ensemble_data.get('confidence', 0.5)
                    
                    return np.clip(net_sentiment * confidence * 2, -1.0, 1.0)
                    
            prediction_value = prediction.get('prediction', 0.0)
            confidence = prediction.get('confidence', 0.5)
            
            return np.clip(prediction_value * confidence, -1.0, 1.0)
            
        except Exception as e:
            print(f"❌ Error normalizing Renaissance prediction: {e}")
            return 0.0
        
    def _determine_direction_and_strength(self, scherman_signal: Dict, renaissance_prediction: Dict, combined_score: float) -> tuple:
        """Determine trading direction and signal strength"""
        abs_score = abs(combined_score)
        
        if abs_score < 0.15:
            return 'hold', 0.0
        elif abs_score > 0.70:
            strength_level = 'strong'
        elif abs_score > 0.45:
            strength_level = 'medium'
        else:
            strength_level = 'weak'
            
        if combined_score > 0:
            direction = f"{strength_level}_long" if strength_level != 'weak' else 'long'
        else:
            direction = f"{strength_level}_short" if strength_level != 'weak' else 'short'
            
        return direction, abs_score
        
    def _calculate_fusion_confidence(self, scherman_signal: Dict, renaissance_prediction: Dict, market_data: Dict) -> float:
        """Calculate overall confidence in the fused signal"""
        scherman_conf = scherman_signal.get('confidence', 0.0) if scherman_signal else 0.0
        renaissance_conf = renaissance_prediction.get('confidence', 0.0) if renaissance_prediction else 0.0
        
        agreement_bonus = self._calculate_signal_agreement(scherman_signal, renaissance_prediction)
        market_condition_factor = self._assess_market_conditions(market_data)
        volume_factor = self._assess_volume_conditions(market_data)
        
        base_confidence = (scherman_conf * self.scherman_weight + 
                          renaissance_conf * self.renaissance_weight)
        
        confidence_multiplier = (1 + agreement_bonus) * market_condition_factor * volume_factor
        
        final_confidence = base_confidence * confidence_multiplier
        
        return np.clip(final_confidence, 0.0, 0.95)
        
    def _calculate_signal_agreement(self, scherman_signal: Dict, renaissance_prediction: Dict) -> float:
        """Calculate agreement between signals for confidence boost"""
        if not scherman_signal or not renaissance_prediction:
            return 0.0
            
        scherman_direction = scherman_signal.get('direction', 'hold')
        
        renaissance_score = self._normalize_renaissance_prediction(renaissance_prediction)
        if renaissance_score > 0.3:
            renaissance_direction = 'long'
        elif renaissance_score < -0.3:
            renaissance_direction = 'short'
        else:
            renaissance_direction = 'hold'
            
        if scherman_direction in ['long', 'strong_long'] and renaissance_direction == 'long':
            return 0.25
        elif scherman_direction in ['short', 'strong_short'] and renaissance_direction == 'short':
            return 0.25
        elif (scherman_direction in ['long', 'strong_long'] and renaissance_direction == 'short') or \
             (scherman_direction in ['short', 'strong_short'] and renaissance_direction == 'long'):
            return -0.30
        else:
            return 0.0
            
    def _assess_market_conditions(self, market_data: Dict) -> float:
        """Assess market conditions for confidence adjustment"""
        volatility = market_data.get('volatility', 0.25)
        liquidity = market_data.get('liquidity_score', 0.8)
        spread = market_data.get('spread_bps', 10)
        
        vol_factor = 1.3 if volatility < 0.12 else 1.1 if volatility < 0.20 else 0.9 if volatility < 0.40 else 0.7
        
        liq_factor = min(liquidity * 1.3, 1.2)
        
        spread_factor = 1.1 if spread < 5 else 1.0 if spread < 15 else 0.9 if spread < 30 else 0.8
        
        return vol_factor * liq_factor * spread_factor
        
    def _assess_volume_conditions(self, market_data: Dict) -> float:
        """Assess volume conditions for signal validation"""
        volume_24h = market_data.get('volume_24h', 0)
        
        if volume_24h == 0:
            return 1.0
            
        try:
            volume_ratio = market_data.get('volume_ratio', 1.0)
            
            if volume_ratio > 2.5:
                return 1.3
            elif volume_ratio > 1.8:
                return 1.2
            elif volume_ratio > 1.3:
                return 1.1
            elif volume_ratio < 0.7:
                return 0.8
            else:
                return 1.0
                
        except Exception:
            return 1.0
            
    def _apply_market_regime_adjustment(self, score: float, confidence: float, market_data: Dict) -> float:
        """Apply market regime-based adjustments"""
        fear_greed = market_data.get('fear_greed_index', 50)
        volatility = market_data.get('volatility', 0.25)
        
        if fear_greed < 20:
            regime_multiplier = 1.3
        elif fear_greed < 35:
            regime_multiplier = 1.15
        elif fear_greed > 80:
            regime_multiplier = 0.8
        elif fear_greed > 65:
            regime_multiplier = 0.9
        else:
            regime_multiplier = 1.0
            
        if volatility > 0.60:
            regime_multiplier *= 0.7
        elif volatility > 0.40:
            regime_multiplier *= 0.85
        elif volatility < 0.10:
            regime_multiplier *= 1.2
            
        return min(regime_multiplier, 1.5)
        
    def _calculate_stop_loss(self, direction: str, market_data: Dict, confidence: float) -> float:
        """Calculate dynamic stop loss based on market conditions"""
        current_price = market_data.get('current_price', 0)
        volatility = market_data.get('volatility', 0.25)
        
        base_stop_distance = volatility * current_price * 0.08
        
        confidence_adjustment = 1.5 - (confidence * 0.7)
        
        if 'strong' in direction:
            strength_multiplier = 1.8
        else:
            strength_multiplier = 2.2
            
        stop_distance = base_stop_distance * confidence_adjustment * strength_multiplier
        
        if 'long' in direction:
            return current_price - stop_distance
        else:
            return current_price + stop_distance
            
    def _calculate_take_profit(self, direction: str, market_data: Dict, confidence: float) -> float:
        """Calculate dynamic take profit target"""
        current_price = market_data.get('current_price', 0)
        volatility = market_data.get('volatility', 0.25)
        
        base_profit_distance = volatility * current_price * 0.12
        
        confidence_multiplier = 1.0 + (confidence * 1.5)
        
        if 'strong' in direction:
            strength_multiplier = 2.8
        else:
            strength_multiplier = 2.0
            
        profit_distance = base_profit_distance * confidence_multiplier * strength_multiplier
        
        if 'long' in direction:
            return current_price + profit_distance
        else:
            return current_price - profit_distance
            
    def _calculate_size_multiplier(self, confidence: float, market_data: Dict) -> float:
        """Calculate position size multiplier based on confidence and conditions"""
        base_multiplier = confidence * 1.6
        
        volatility = market_data.get('volatility', 0.25)
        vol_adjustment = 1.2 / (1.0 + volatility * 2)
        
        liquidity = market_data.get('liquidity_score', 0.8)
        liq_adjustment = min(liquidity * 1.3, 1.0)
        
        fear_greed = market_data.get('fear_greed_index', 50)
        fear_adjustment = 1.3 if fear_greed < 20 else 1.1 if fear_greed < 35 else 1.0
        
        final_multiplier = base_multiplier * vol_adjustment * liq_adjustment * fear_adjustment
        
        return np.clip(final_multiplier, 0.3, 2.5)
        
    def _calculate_risk_reward_ratio(self, direction: str, market_data: Dict) -> float:
        """Calculate risk-reward ratio for the trade"""
        current_price = market_data.get('current_price', 100)
        
        dummy_confidence = 0.75
        stop_loss = self._calculate_stop_loss(direction, market_data, dummy_confidence)
        take_profit = self._calculate_take_profit(direction, market_data, dummy_confidence)
        
        if 'long' in direction:
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
        else:
            risk = abs(stop_loss - current_price)
            reward = abs(current_price - take_profit)
            
        if risk == 0:
            return 3.0
            
        return reward / risk
        
    def _estimate_holding_period(self, strength: float, market_data: Dict) -> int:
        """Estimate expected holding period in hours"""
        base_period = 6
        
        volatility = market_data.get('volatility', 0.25)
        if volatility > 0.5:
            vol_multiplier = 0.6
        elif volatility > 0.3:
            vol_multiplier = 0.8
        else:
            vol_multiplier = 1.2
            
        strength_multiplier = 0.8 if strength > 0.7 else 1.0 if strength > 0.5 else 1.3
        
        estimated_hours = int(base_period * vol_multiplier * strength_multiplier)
        
        return max(2, min(estimated_hours, 24))
        
    def _assess_signal_quality(self, scherman_signal: Dict, renaissance_prediction: Dict) -> str:
        """Assess overall signal quality grade"""
        scherman_quality = 0
        if scherman_signal:
            conf = scherman_signal.get('confidence', 0)
            confirmations = scherman_signal.get('confirmations', 0)
            total = scherman_signal.get('total_conditions', 6)
            scherman_quality = (conf + confirmations/total) / 2
            
        renaissance_quality = renaissance_prediction.get('confidence', 0) if renaissance_prediction else 0
        
        overall_quality = (scherman_quality * self.scherman_weight + 
                          renaissance_quality * self.renaissance_weight)
        
        if overall_quality >= 0.85:
            return 'A+'
        elif overall_quality >= 0.75:
            return 'A'
        elif overall_quality >= 0.65:
            return 'B'
        elif overall_quality >= 0.55:
            return 'C'
        else:
            return 'D'
            
    def _update_adaptive_weights(self):
        """Update signal weights based on recent performance"""
        if len(self.signal_history) < 20:
            return
            
        recent_signals = self.signal_history[-20:]
        
        scherman_wins = 0
        renaissance_wins = 0
        total_trades = 0
        
        for signal in recent_signals:
            if 'performance' in signal:
                total_trades += 1
                if signal['performance'] > 0:
                    if signal['scherman_component'] > signal['renaissance_component']:
                        scherman_wins += 1
                    else:
                        renaissance_wins += 1
                        
        if total_trades >= 10:
            scherman_rate = scherman_wins / total_trades
            renaissance_rate = renaissance_wins / total_trades
            
            if scherman_rate > renaissance_rate + 0.2:
                self.scherman_weight = min(0.85, self.scherman_weight + 0.05)
                self.renaissance_weight = 1.0 - self.scherman_weight
            elif renaissance_rate > scherman_rate + 0.2:
                self.renaissance_weight = min(0.50, self.renaissance_weight + 0.05)
                self.scherman_weight = 1.0 - self.renaissance_weight
                
    def get_signal_statistics(self) -> Dict:
        """Get comprehensive signal statistics"""
        if not self.signal_history:
            return {}
            
        recent_signals = self.signal_history[-100:] if len(self.signal_history) > 100 else self.signal_history
        
        directions = [s.get('direction', 'hold') for s in recent_signals]
        confidences = [s.get('confidence', 0) for s in recent_signals]
        qualities = [s.get('signal_quality', 'C') for s in recent_signals]
        
        return {
            'total_signals': len(recent_signals),
            'long_signals': len([d for d in directions if 'long' in d]),
            'short_signals': len([d for d in directions if 'short' in d]),
            'hold_signals': directions.count('hold'),
            'avg_confidence': np.mean(confidences),
            'max_confidence': np.max(confidences) if confidences else 0,
            'min_confidence': np.min(confidences) if confidences else 0,
            'quality_distribution': {grade: qualities.count(grade) for grade in ['A+', 'A', 'B', 'C', 'D']},
            'current_weights': {
                'scherman': self.scherman_weight,
                'renaissance': self.renaissance_weight
            },
            'adaptive_weights_enabled': self.adaptive_weights
        }
