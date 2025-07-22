import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class AdvancedRiskSystem:
    def __init__(self, config: Dict):
        self.config = config
        self.position_limits = {
            'max_position_risk': 0.02,
            'max_portfolio_heat': 0.15,
            'max_correlation_exposure': 0.6,
            'max_leverage': 3.0,
            'max_drawdown_stop': 0.10
        }
        self.risk_metrics = {}
        self.portfolio_state = {}
        self.var_models = {}
        self.stress_scenarios = {}
        
    def validate_trade(self, symbol: str, signal: Dict, current_positions: Dict, portfolio_value: float) -> bool:
        validations = [
            self._check_position_sizing(symbol, signal, portfolio_value),
            self._check_portfolio_heat(signal, current_positions, portfolio_value),
            self._check_concentration_risk(symbol, signal, current_positions, portfolio_value),
            self._check_correlation_limits(symbol, signal, current_positions),
            self._check_drawdown_limits(portfolio_value),
            self._check_volatility_exposure(symbol, signal),
            self._check_leverage_limits(signal, current_positions, portfolio_value)
        ]
        
        return all(validations)
    
    def calculate_optimal_position_size(self, symbol: str, signal: Dict, portfolio_value: float, 
                                      current_positions: Dict) -> float:
        
        kelly_size = self._calculate_kelly_position_size(signal, portfolio_value)
        risk_parity_size = self._calculate_risk_parity_size(symbol, signal, portfolio_value)
        volatility_adjusted_size = self._calculate_volatility_adjusted_size(symbol, signal, portfolio_value)
        
        base_size = np.mean([kelly_size, risk_parity_size, volatility_adjusted_size])
        
        confidence_adjustment = signal.get('confidence', 0.5)
        regime_adjustment = self._get_regime_adjustment()
        correlation_adjustment = self._get_correlation_adjustment(symbol, current_positions)
        
        final_size = base_size * confidence_adjustment * regime_adjustment * correlation_adjustment
        
        max_size = portfolio_value * self.position_limits['max_position_risk']
        
        return min(final_size, max_size)
    
    def calculate_portfolio_var(self, positions: Dict, confidence_level: float = 0.99, 
                              time_horizon: int = 1) -> float:
        
        if not positions:
            return 0.0
        
        portfolio_returns = self._simulate_portfolio_returns(positions, 10000)
        
        var_percentile = (1 - confidence_level) * 100
        var_value = np.percentile(portfolio_returns, var_percentile)
        
        return abs(var_value)
    
    def calculate_expected_shortfall(self, positions: Dict, confidence_level: float = 0.99) -> float:
        portfolio_returns = self._simulate_portfolio_returns(positions, 10000)
        
        var_threshold = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        tail_losses = portfolio_returns[portfolio_returns <= var_threshold]
        
        if len(tail_losses) > 0:
            return abs(np.mean(tail_losses))
        
        return abs(var_threshold) * 1.3
    
    def run_stress_tests(self, positions: Dict, portfolio_value: float) -> Dict:
        stress_results = {}
        
        scenarios = {
            'market_crash_20': {'equity_shock': -0.20, 'vol_spike': 2.0},
            'crypto_crash_50': {'crypto_shock': -0.50, 'vol_spike': 3.0},
            'liquidity_crisis': {'spread_widen': 5.0, 'vol_spike': 2.5},
            'flash_crash': {'instant_drop': -0.15, 'recovery': 0.8},
            'correlation_breakdown': {'correlation_spike': 0.95, 'vol_spike': 1.5}
        }
        
        for scenario_name, params in scenarios.items():
            scenario_pnl = 0
            
            for symbol, position in positions.items():
                position_value = position.get('notional', 0)
                
                if 'equity_shock' in params:
                    shock = params['equity_shock']
                elif 'crypto_shock' in params and 'BTC' in symbol:
                    shock = params['crypto_shock']
                elif 'instant_drop' in params:
                    shock = params['instant_drop'] * params.get('recovery', 1.0)
                else:
                    shock = -0.05
                
                scenario_pnl += position_value * shock
            
            stress_results[scenario_name] = {
                'scenario_pnl': scenario_pnl,
                'portfolio_impact': scenario_pnl / portfolio_value,
                'survival_probability': 1.0 if scenario_pnl > -portfolio_value * 0.5 else 0.0
            }
        
        return stress_results
    
    def calculate_dynamic_correlation_matrix(self, symbols: List[str], lookback_days: int = 60) -> np.ndarray:
        correlation_matrix = np.eye(len(symbols))
        
        base_correlations = {
            ('BTC', 'ETH'): 0.85,
            ('BTC', 'SOL'): 0.75,
            ('ETH', 'SOL'): 0.80
        }
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i != j:
                    key1 = (symbol1.split('-')[0], symbol2.split('-')[0])
                    key2 = (symbol2.split('-')[0], symbol1.split('-')[0])
                    
                    base_corr = base_correlations.get(key1, base_correlations.get(key2, 0.6))
                    
                    volatility_adjustment = np.random.normal(0, 0.1)
                    correlation_matrix[i, j] = np.clip(base_corr + volatility_adjustment, -1, 1)
        
        return correlation_matrix
    
    def monitor_portfolio_risk(self, positions: Dict, portfolio_value: float) -> Dict:
        total_exposure = sum([abs(pos.get('notional', 0)) for pos in positions.values()])
        leverage = total_exposure / portfolio_value if portfolio_value > 0 else 0
        
        portfolio_var = self.calculate_portfolio_var(positions)
        expected_shortfall = self.calculate_expected_shortfall(positions)
        stress_results = self.run_stress_tests(positions, portfolio_value)
        
        concentration_risk = self._calculate_concentration_risk(positions, portfolio_value)
        correlation_risk = self._calculate_correlation_risk(positions)
        
        risk_score = self._calculate_overall_risk_score(
            leverage, portfolio_var, concentration_risk, correlation_risk
        )
        
        return {
            'leverage': leverage,
            'portfolio_var_99': portfolio_var,
            'expected_shortfall_99': expected_shortfall,
            'concentration_risk': concentration_risk,
            'correlation_risk': correlation_risk,
            'stress_test_results': stress_results,
            'overall_risk_score': risk_score,
            'risk_budget_utilization': total_exposure / (portfolio_value * 5),
            'timestamp': datetime.now()
        }
    
    def _check_position_sizing(self, symbol: str, signal: Dict, portfolio_value: float) -> bool:
        signal_size = signal.get('notional', 0)
        max_position_value = portfolio_value * self.position_limits['max_position_risk']
        return signal_size <= max_position_value
    
    def _check_portfolio_heat(self, signal: Dict, current_positions: Dict, portfolio_value: float) -> bool:
        current_heat = sum([abs(pos.get('notional', 0)) for pos in current_positions.values()])
        new_heat = (current_heat + signal.get('notional', 0)) / portfolio_value
        return new_heat <= self.position_limits['max_portfolio_heat']
    
    def _check_concentration_risk(self, symbol: str, signal: Dict, current_positions: Dict, portfolio_value: float) -> bool:
        current_position = current_positions.get(symbol, {}).get('notional', 0)
        new_position = current_position + signal.get('notional', 0)
        concentration = abs(new_position) / portfolio_value
        return concentration <= 0.05
    
    def _check_correlation_limits(self, symbol: str, signal: Dict, current_positions: Dict) -> bool:
        base_asset = symbol.split('-')[0]
        
        related_exposure = 0
        for pos_symbol, position in current_positions.items():
            if pos_symbol.split('-')[0] == base_asset:
                related_exposure += abs(position.get('notional', 0))
        
        return related_exposure <= 100000
    
    def _check_drawdown_limits(self, portfolio_value: float) -> bool:
        initial_value = self.portfolio_state.get('initial_value', portfolio_value)
        max_value = self.portfolio_state.get('max_value', portfolio_value)
        
        current_drawdown = (max_value - portfolio_value) / max_value if max_value > 0 else 0
        
        self.portfolio_state['max_value'] = max(max_value, portfolio_value)
        
        return current_drawdown <= self.position_limits['max_drawdown_stop']
    
    def _check_volatility_exposure(self, symbol: str, signal: Dict) -> bool:
        return True
    
    def _check_leverage_limits(self, signal: Dict, current_positions: Dict, portfolio_value: float) -> bool:
        total_exposure = sum([abs(pos.get('notional', 0)) for pos in current_positions.values()])
        new_leverage = (total_exposure + signal.get('notional', 0)) / portfolio_value
        return new_leverage <= self.position_limits['max_leverage']
    
    def _calculate_kelly_position_size(self, signal: Dict, portfolio_value: float) -> float:
        win_prob = signal.get('confidence', 0.55)
        avg_win = 0.04
        avg_loss = 0.02
        
        kelly_fraction = (win_prob * avg_win - (1 - win_prob) * avg_loss) / avg_loss
        kelly_fraction = max(0, min(kelly_fraction, 0.25))
        
        return portfolio_value * kelly_fraction * 0.5
    
    def _calculate_risk_parity_size(self, symbol: str, signal: Dict, portfolio_value: float) -> float:
        target_risk = 0.02
        asset_volatility = 0.25
        
        position_size = (portfolio_value * target_risk) / asset_volatility
        return position_size
    
    def _calculate_volatility_adjusted_size(self, symbol: str, signal: Dict, portfolio_value: float) -> float:
        base_size = portfolio_value * 0.02
        volatility = 0.25
        target_volatility = 0.15
        
        adjustment = target_volatility / volatility
        return base_size * adjustment
    
    def _get_regime_adjustment(self) -> float:
        return 1.0
    
    def _get_correlation_adjustment(self, symbol: str, current_positions: Dict) -> float:
        return 1.0
    
    def _simulate_portfolio_returns(self, positions: Dict, num_simulations: int) -> np.ndarray:
        returns = []
        
        for _ in range(num_simulations):
            portfolio_return = 0
            for symbol, position in positions.items():
                weight = position.get('notional', 0) / 100000
                asset_return = np.random.normal(0, 0.03)
                portfolio_return += weight * asset_return
            
            returns.append(portfolio_return)
        
        return np.array(returns)
    
    def _calculate_concentration_risk(self, positions: Dict, portfolio_value: float) -> float:
        weights = []
        for position in positions.values():
            weight = abs(position.get('notional', 0)) / portfolio_value
            weights.append(weight)
        
        if not weights:
            return 0.0
        
        return sum([w**2 for w in weights])
    
    def _calculate_correlation_risk(self, positions: Dict) -> float:
        return 0.6
    
    def _calculate_overall_risk_score(self, leverage: float, var: float, concentration: float, correlation: float) -> float:
        leverage_score = min(leverage / 2.0, 1.0)
        var_score = min(var * 100, 1.0)
        concentration_score = min(concentration * 10, 1.0)
        correlation_score = correlation
        
        overall_score = (leverage_score * 0.3 + var_score * 0.3 + 
                        concentration_score * 0.25 + correlation_score * 0.15)
        
        return min(overall_score, 1.0)
