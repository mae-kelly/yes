import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from vix_divergence_core import SchermanVIXDivergenceCore

class HybridSignalFusion:
    def __init__(self, config: Dict):
        self.config = config
        self.vix_core = SchermanVIXDivergenceCore(config)
        self.scherman_weight = 0.75
        self.renaissance_weight = 0.25
        self.min_confidence_threshold = 0.65
        self.signal_history = []
        
    def fuse_signals(self, scherman_signal: Dict, renaissance_prediction: Dict, market_data: Dict) -> Dict:
        if not scherman_signal and not renaissance_prediction:
            return {}
            
        scherman_score = self._normalize_scherman_signal(scherman_signal)
        renaissance_score = self._normalize_renaissance_prediction(renaissance_prediction)
        
        combined_score = (scherman_score * self.scherman_weight + 
                         renaissance_score * self.renaissance_weight)
        
        direction = self._determine_direction(scherman_signal, renaissance_prediction, combined_score)
        confidence = self._calculate_fusion_confidence(scherman_signal, renaissance_prediction, market_data)
        
        if confidence < self.min_confidence_threshold:
            return {}
            
        fused_signal = {
            'signal': 'hybrid_fusion',
            'direction': direction,
            'confidence': confidence,
            'combined_score': combined_score,
            'scherman_component': scherman_score,
            'renaissance_component': renaissance_score,
            'entry_price': market_data.get('current_price', 0),
            'stop_loss': self._calculate_stop_loss(direction, market_data),
            'take_profit': self._calculate_take_profit(direction, market_data, confidence),
            'position_size_multiplier': self._calculate_size_multiplier(confidence, market_data),
            'timestamp': datetime.now()
        }
        
        self.signal_history.append(fused_signal)
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]
            
        return fused_signal
        
    def _normalize_scherman_signal(self, signal: Dict) -> float:
        if not signal:
            return 0.0
            
        base_score = signal.get('confidence', 0.0)
        
        if signal.get('signal') == 'vix_divergence':
            base_score *= 1.3
            
        direction_multiplier = 1.0 if signal.get('direction') == 'long' else -1.0
        
        return np.clip(base_score * direction_multiplier, -1.0, 1.0)
        
    def _normalize_renaissance_prediction(self, prediction: Dict) -> float:
        if not prediction:
            return 0.0
            
        if 'ensemble' in prediction:
            ensemble_pred = prediction['ensemble']
            class_probs = ensemble_pred.get('predictions', [0.2, 0.2, 0.2, 0.2, 0.2])
            
            if len(class_probs) == 5:
                bearish_prob = class_probs[0] + class_probs[1]
                bullish_prob = class_probs[3] + class_probs[4]
                net_score = bullish_prob - bearish_prob
                
                confidence = ensemble_pred.get('confidence', 0.5)
                return np.clip(net_score * confidence, -1.0, 1.0)
                
        return 0.0
        
    def _determine_direction(self, scherman_signal: Dict, renaissance_prediction: Dict, combined_score: float) -> str:
        if abs(combined_score) < 0.1:
            return 'hold'
            
        if combined_score > 0.3:
            return 'strong_long' if combined_score > 0.6 else 'long'
        elif combined_score < -0.3:
            return 'strong_short' if combined_score < -0.6 else 'short'
        else:
            return 'hold'
            
    def _calculate_fusion_confidence(self, scherman_signal: Dict, renaissance_prediction: Dict, market_data: Dict) -> float:
        scherman_conf = scherman_signal.get('confidence', 0.0) if scherman_signal else 0.0
        renaissance_conf = renaissance_prediction.get('confidence', 0.0) if renaissance_prediction else 0.0
        
        agreement_bonus = self._calculate_signal_agreement(scherman_signal, renaissance_prediction)
        market_condition_factor = self._assess_market_conditions(market_data)
        
        base_confidence = (scherman_conf * self.scherman_weight + 
                          renaissance_conf * self.renaissance_weight)
        
        final_confidence = base_confidence * (1 + agreement_bonus) * market_condition_factor
        
        return np.clip(final_confidence, 0.0, 0.95)
        
    def _calculate_signal_agreement(self, scherman_signal: Dict, renaissance_prediction: Dict) -> float:
        if not scherman_signal or not renaissance_prediction:
            return 0.0
            
        scherman_dir = scherman_signal.get('direction', 'hold')
        
        renaissance_score = self._normalize_renaissance_prediction(renaissance_prediction)
        renaissance_dir = 'long' if renaissance_score > 0.2 else 'short' if renaissance_score < -0.2 else 'hold'
        
        if scherman_dir == renaissance_dir and scherman_dir != 'hold':
            return 0.2
        elif scherman_dir != 'hold' and renaissance_dir != 'hold' and scherman_dir != renaissance_dir:
            return -0.3
        else:
            return 0.0
            
    def _assess_market_conditions(self, market_data: Dict) -> float:
        volatility = market_data.get('volatility', 0.25)
        liquidity = market_data.get('liquidity_score', 0.8)
        volume_ratio = market_data.get('volume_ratio', 1.0)
        
        vol_factor = 1.2 if volatility < 0.15 else 0.8 if volatility > 0.5 else 1.0
        liq_factor = min(liquidity * 1.2, 1.0)
        vol_factor_adj = min(volume_ratio / 2, 1.0) if volume_ratio > 1.5 else 1.0
        
        return vol_factor * liq_factor * vol_factor_adj
        
    def _calculate_stop_loss(self, direction: str, market_data: Dict) -> float:
        current_price = market_data.get('current_price', 0)
        atr = market_data.get('atr', current_price * 0.02)
        
        if 'long' in direction:
            stop_multiplier = 2.5 if 'strong' in direction else 2.0
            return current_price - (stop_multiplier * atr)
        elif 'short' in direction:
            stop_multiplier = 2.5 if 'strong' in direction else 2.0
            return current_price + (stop_multiplier * atr)
        else:
            return current_price
            
    def _calculate_take_profit(self, direction: str, market_data: Dict, confidence: float) -> float:
        current_price = market_data.get('current_price', 0)
        atr = market_data.get('atr', current_price * 0.02)
        
        confidence_multiplier = 1.5 + confidence
        
        if 'long' in direction:
            tp_multiplier = 4.0 * confidence_multiplier if 'strong' in direction else 3.0 * confidence_multiplier
            return current_price + (tp_multiplier * atr)
        elif 'short' in direction:
            tp_multiplier = 4.0 * confidence_multiplier if 'strong' in direction else 3.0 * confidence_multiplier
            return current_price - (tp_multiplier * atr)
        else:
            return current_price
            
    def _calculate_size_multiplier(self, confidence: float, market_data: Dict) -> float:
        base_multiplier = confidence * 1.5
        
        volatility = market_data.get('volatility', 0.25)
        vol_adjustment = 1.0 / (1.0 + volatility)
        
        liquidity = market_data.get('liquidity_score', 0.8)
        liq_adjustment = min(liquidity * 1.2, 1.0)
        
        final_multiplier = base_multiplier * vol_adjustment * liq_adjustment
        
        return np.clip(final_multiplier, 0.3, 2.0)
        
    def get_signal_statistics(self) -> Dict:
        if not self.signal_history:
            return {}
            
        recent_signals = self.signal_history[-100:] if len(self.signal_history) > 100 else self.signal_history
        
        directions = [s.get('direction', 'hold') for s in recent_signals]
        confidences = [s.get('confidence', 0) for s in recent_signals]
        
        return {
            'total_signals': len(recent_signals),
            'long_signals': directions.count('long') + directions.count('strong_long'),
            'short_signals': directions.count('short') + directions.count('strong_short'),
            'hold_signals': directions.count('hold'),
            'avg_confidence': np.mean(confidences),
            'max_confidence': np.max(confidences),
            'min_confidence': np.min(confidences)
        }