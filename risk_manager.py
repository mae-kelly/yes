import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class RiskManager:
    def __init__(self, config: Dict):
        self.config = config
        self.position_limits = {'max_position_size_pct': config.get('max_position_size_pct', 0.1), 'max_portfolio_heat': config.get('max_portfolio_heat', 0.8), 'max_correlation_exposure': config.get('max_correlation_exposure', 0.5), 'max_single_asset_exposure': config.get('max_single_asset_exposure', 0.3), 'max_sector_exposure': config.get('max_sector_exposure', 0.6), 'max_leverage': config.get('max_leverage', 5.0), 'max_notional_per_trade': config.get('max_notional_per_trade', 50000), 'min_notional_per_trade': config.get('min_notional_per_trade', 100)}
        self.drawdown_limits = {'max_daily_loss': config.get('max_daily_loss', 0.05), 'max_weekly_loss': config.get('max_weekly_loss', 0.15), 'max_monthly_loss': config.get('max_monthly_loss', 0.25), 'max_trailing_drawdown': config.get('max_trailing_drawdown', 0.20), 'stop_trading_drawdown': config.get('stop_trading_drawdown', 0.30)}
        self.volatility_limits = {'max_portfolio_volatility': config.get('max_portfolio_volatility', 0.25), 'max_asset_volatility': config.get('max_asset_volatility', 0.50), 'volatility_scaling_factor': config.get('volatility_scaling_factor', 0.15), 'vol_lookback_days': config.get('vol_lookback_days', 30), 'min_volatility_threshold': config.get('min_volatility_threshold', 0.01), 'max_volatility_threshold': config.get('max_volatility_threshold', 1.00)}
        self.correlation_limits = {'max_pairwise_correlation': config.get('max_pairwise_correlation', 0.8), 'correlation_lookback_days': config.get('correlation_lookback_days', 60), 'min_correlation_observations': config.get('min_correlation_observations', 100), 'correlation_decay_factor': config.get('correlation_decay_factor', 0.95), 'regime_correlation_adjustment': config.get('regime_correlation_adjustment', 1.5)}
        self.liquidity_requirements = {'min_daily_volume': config.get('min_daily_volume', 1000000), 'max_volume_participation': config.get('max_volume_participation', 0.05), 'min_market_cap': config.get('min_market_cap', 100000000), 'min_order_book_depth': config.get('min_order_book_depth', 50000), 'max_spread_threshold': config.get('max_spread_threshold', 0.01)}
        self.stress_test_scenarios = {'market_crash': {'equity_shock': -0.30, 'volatility_spike': 3.0, 'correlation_surge': 0.9}, 'liquidity_crisis': {'spread_widening': 5.0, 'volume_drop': 0.3, 'slippage_increase': 3.0}, 'flash_crash': {'price_drop': -0.20, 'time_horizon': 0.25, 'recovery_time': 2.0}, 'regulatory_shock': {'trading_halt': 0.5, 'margin_increase': 2.0, 'position_limit': 0.5}, 'operational_failure': {'system_downtime': 4.0, 'data_loss': 0.1, 'execution_delay': 10.0}}
        self.var_models = {'historical_var': {'confidence_level': 0.99, 'lookback_days': 252}, 'parametric_var': {'confidence_level': 0.99, 'distribution': 'normal'}, 'monte_carlo_var': {'confidence_level': 0.99, 'simulations': 10000}, 'extreme_value_var': {'confidence_level': 0.99, 'threshold': 0.95}, 'copula_var': {'confidence_level': 0.99, 'copula_type': 't'}}
        self.risk_attribution_models = {'factor_risk': ['market_beta', 'size_factor', 'value_factor', 'momentum_factor', 'volatility_factor'], 'sector_risk': ['technology', 'finance', 'energy', 'healthcare', 'consumer'], 'geographic_risk': ['north_america', 'europe', 'asia_pacific', 'emerging_markets'], 'currency_risk': ['usd', 'eur', 'jpy', 'gbp', 'emerging_currencies'], 'style_risk': ['growth', 'value', 'quality', 'low_volatility', 'momentum']}
        self.dynamic_hedging_strategies = {'portfolio_insurance': {'floor_level': 0.9, 'participation_rate': 0.8, 'rebalance_frequency': 'daily'}, 'option_hedging': {'hedge_ratio': 0.5, 'strike_selection': 'otm_10', 'expiry': '30d'}, 'futures_hedging': {'hedge_ratio': 0.3, 'roll_strategy': 'calendar', 'basis_threshold': 0.02}, 'volatility_hedging': {'vol_target': 0.15, 'vol_lookback': 20, 'rebalance_threshold': 0.02}, 'correlation_hedging': {'target_correlation': 0.3, 'hedge_instruments': 'etfs', 'rebalance_weekly': True}}
        self.risk_monitoring_alerts = {'position_size_breach': {'threshold': 0.95, 'severity': 'high', 'action': 'reduce_position'}, 'correlation_spike': {'threshold': 0.85, 'severity': 'medium', 'action': 'hedge_exposure'}, 'volatility_surge': {'threshold': 2.0, 'severity': 'high', 'action': 'reduce_leverage'}, 'liquidity_drain': {'threshold': 0.5, 'severity': 'critical', 'action': 'emergency_exit'}, 'drawdown_warning': {'threshold': 0.15, 'severity': 'medium', 'action': 'review_positions'}}
        self.model_risk_controls = {'backtest_requirements': {'min_periods': 1000, 'out_of_sample': 0.3, 'walk_forward': True}, 'model_validation': {'cross_validation': 'time_series', 'significance_test': 'student_t', 'alpha': 0.05}, 'model_monitoring': {'performance_decay': 0.1, 'prediction_drift': 0.05, 'recalibration_trigger': 0.2}, 'ensemble_requirements': {'min_models': 3, 'max_correlation': 0.7, 'diversity_metric': 'prediction_variance'}, 'overfitting_controls': {'regularization': 'l1_l2', 'feature_selection': 'recursive', 'complexity_penalty': 0.01}}
        self.operational_risk_controls = {'system_redundancy': {'backup_systems': 2, 'failover_time': 30, 'data_replication': 'real_time'}, 'execution_controls': {'pre_trade_checks': True, 'post_trade_validation': True, 'trade_limits': 'real_time'}, 'data_quality': {'validation_rules': 100, 'anomaly_detection': True, 'data_lineage': 'full'}, 'cybersecurity': {'encryption': 'aes_256', 'authentication': 'multi_factor', 'network_segmentation': True}, 'business_continuity': {'disaster_recovery': '4_hour_rpo', 'backup_sites': 2, 'emergency_procedures': 'tested'}}
        self.regulatory_compliance = {'position_reporting': {'frequency': 'daily', 'threshold': 10000, 'format': 'xml'}, 'transaction_reporting': {'t1_reporting': True, 'trade_repository': 'dtcc', 'lei_required': True}, 'risk_reporting': {'var_reporting': 'daily', 'stress_testing': 'quarterly', 'liquidity_metrics': 'monthly'}, 'market_abuse': {'surveillance': 'real_time', 'pattern_detection': True, 'alert_generation': 'automated'}, 'best_execution': {'venue_analysis': 'quarterly', 'cost_analysis': 'daily', 'quality_metrics': 'real_time'}}
        self.portfolio_optimization = {'objective_function': 'utility_maximization', 'constraints': ['position_limits', 'turnover_limits', 'sector_limits', 'risk_limits'], 'optimization_method': 'quadratic_programming', 'rebalancing_frequency': 'weekly', 'transaction_cost_model': 'linear_impact'}
        self.risk_budgeting = {'risk_allocation_method': 'equal_risk_contribution', 'risk_measure': 'component_var', 'allocation_constraints': {'min_weight': 0.01, 'max_weight': 0.30}, 'rebalancing_threshold': 0.05, 'risk_target': 0.15}
        self.performance_attribution = {'attribution_method': 'brinson_fachler', 'benchmark': 'crypto_index', 'frequency': 'daily', 'factors': ['market', 'size', 'momentum', 'volatility'], 'interaction_effects': True}
        self.scenario_analysis = {'historical_scenarios': ['2008_crisis', '2020_covid', '2018_crypto_crash', '2022_terra_collapse'], 'hypothetical_scenarios': ['rate_shock', 'crypto_ban', 'exchange_hack', 'stablecoin_depeg'], 'monte_carlo_scenarios': {'simulations': 10000, 'time_horizon': 252, 'confidence_intervals': [0.95, 0.99]}, 'stress_frequency': 'weekly', 'scenario_weights': 'equal'}
        self.liquidity_risk_management = {'liquidity_scoring': {'volume_score': 0.3, 'spread_score': 0.2, 'depth_score': 0.3, 'stability_score': 0.2}, 'liquidity_buffers': {'cash_buffer': 0.1, 'liquid_assets': 0.2, 'credit_lines': 0.05}, 'funding_risk': {'funding_concentration': 0.3, 'maturity_mismatch': 0.5, 'rollover_risk': 0.2}, 'market_impact': {'temporary_impact': 'sqrt_volume', 'permanent_impact': 'linear_volume'}, 'liquidity_stress_tests': ['funding_crisis', 'market_closure', 'fire_sale']}
        self.counterparty_risk_management = {'credit_limits': {'per_counterparty': 0.1, 'per_sector': 0.3, 'per_geography': 0.5}, 'collateral_management': {'initial_margin': 0.1, 'variation_margin': 'daily', 'minimum_transfer': 1000}, 'netting_agreements': {'close_out_netting': True, 'payment_netting': True, 'cross_product_netting': False}, 'credit_monitoring': {'rating_triggers': True, 'cds_monitoring': True, 'news_monitoring': True}, 'wrong_way_risk': {'correlation_threshold': 0.3, 'stress_scenarios': True, 'additional_capital': 0.2}}
        self.margin_risk_management = {'initial_margin_models': ['var_based', 'historical_simulation', 'filtered_bootstrap'], 'margin_period_of_risk': 10, 'liquidation_horizon': 5, 'margin_buffers': {'operational_buffer': 0.1, 'model_buffer': 0.05, 'anti_procyclical': 0.25}, 'backtesting_requirements': {'daily_backtesting': True, 'exception_threshold': 4, 'model_validation': 'quarterly'}}
        self.concentration_risk_limits = {'single_name_limit': 0.05, 'sector_limit': 0.20, 'geography_limit': 0.30, 'strategy_limit': 0.25, 'tenor_limit': 0.40, 'currency_limit': 0.35}
        self.tail_risk_measures = {'expected_shortfall': {'confidence_levels': [0.95, 0.99], 'coherent_measure': True}, 'conditional_drawdown': {'threshold': 0.95, 'average_above_threshold': True}, 'maximum_loss': {'time_horizon': 252, 'confidence_level': 0.99}, 'tail_expectation': {'distribution': 'generalized_pareto', 'threshold': 0.95}, 'spectral_risk_measure': {'risk_aversion_function': 'exponential', 'lambda': 2.0}}
        self.regime_dependent_risk = {'regime_identification': {'method': 'markov_switching', 'states': 3, 'variables': ['returns', 'volatility']}, 'regime_risk_scaling': {'low_vol': 0.8, 'normal_vol': 1.0, 'high_vol': 1.5}, 'transition_probabilities': {'estimated': True, 'smoothing': 0.1, 'updating_frequency': 'monthly'}, 'regime_hedging': {'dynamic_hedging': True, 'hedge_ratio_scaling': 'regime_dependent', 'overlay_strategies': True}}
        self.current_portfolio_state = {'total_exposure': 0.0, 'net_exposure': 0.0, 'gross_exposure': 0.0, 'leverage': 0.0, 'portfolio_beta': 0.0, 'tracking_error': 0.0, 'information_ratio': 0.0, 'sharpe_ratio': 0.0, 'sortino_ratio': 0.0, 'calmar_ratio': 0.0, 'maximum_drawdown': 0.0, 'current_drawdown': 0.0, 'var_1d_99': 0.0, 'var_10d_99': 0.0, 'expected_shortfall': 0.0, 'portfolio_volatility': 0.0, 'correlation_risk': 0.0, 'concentration_risk': 0.0, 'liquidity_risk': 0.0}
        self.risk_alerts = []
        self.breached_limits = []
        self.stress_test_results = {}
        self.var_estimates = {}
        self.correlation_matrix = pd.DataFrame()
        self.factor_exposures = {}
        self.attribution_results = {}
        self.scenario_results = {}
        self.liquidity_scores = {}
        self.model_performance = {}
        self.operational_metrics = {}
        
    def validate_signal(self, symbol: str, signal: Dict, current_positions: Dict) -> bool:
        try:
            validation_checks = [self._check_position_limits(symbol, signal, current_positions), self._check_portfolio_heat(symbol, signal, current_positions), self._check_correlation_exposure(symbol, signal, current_positions), self._check_volatility_limits(symbol, signal), self._check_liquidity_requirements(symbol, signal), self._check_risk_capacity(symbol, signal, current_positions), self._check_drawdown_limits(current_positions), self._check_concentration_limits(symbol, signal, current_positions), self._check_leverage_limits(symbol, signal, current_positions), self._check_market_conditions(symbol, signal), self._check_operational_constraints(symbol, signal), self._check_regulatory_constraints(symbol, signal)]
            if not all(validation_checks):
                self._log_validation_failure(symbol, signal, validation_checks)
                return False
            return True
        except Exception as e:
            print(f"Error validating signal for {symbol}: {e}")
            return False
            
    def _check_position_limits(self, symbol: str, signal: Dict, current_positions: Dict) -> bool:
        try:
            current_position = current_positions.get(symbol, {})
            current_size = abs(current_position.get('size', 0))
            signal_size = abs(signal.get('size', 0))
            total_size = current_size + signal_size
            max_size = self.position_limits['max_notional_per_trade']
            if total_size > max_size:
                self.risk_alerts.append({'type': 'position_limit_breach', 'symbol': symbol, 'current_size': total_size, 'limit': max_size, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking position limits for {symbol}: {e}")
            return False
            
    def _check_portfolio_heat(self, symbol: str, signal: Dict, current_positions: Dict) -> bool:
        try:
            total_exposure = sum([abs(pos.get('notional', 0)) for pos in current_positions.values()])
            signal_notional = abs(signal.get('notional', 0))
            portfolio_value = self._get_portfolio_value()
            current_heat = total_exposure / portfolio_value if portfolio_value > 0 else 0
            new_heat = (total_exposure + signal_notional) / portfolio_value if portfolio_value > 0 else 0
            max_heat = self.position_limits['max_portfolio_heat']
            if new_heat > max_heat:
                self.risk_alerts.append({'type': 'portfolio_heat_breach', 'symbol': symbol, 'current_heat': new_heat, 'limit': max_heat, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking portfolio heat: {e}")
            return False
            
    def _check_correlation_exposure(self, symbol: str, signal: Dict, current_positions: Dict) -> bool:
        try:
            if len(current_positions) == 0:
                return True
            correlation_exposure = 0
            for other_symbol, position in current_positions.items():
                if other_symbol != symbol and position.get('size', 0) != 0:
                    correlation = self._get_correlation(symbol, other_symbol)
                    position_weight = abs(position.get('notional', 0)) / self._get_portfolio_value()
                    correlation_exposure += abs(correlation) * position_weight
            max_correlation_exposure = self.position_limits['max_correlation_exposure']
            if correlation_exposure > max_correlation_exposure:
                self.risk_alerts.append({'type': 'correlation_exposure_breach', 'symbol': symbol, 'correlation_exposure': correlation_exposure, 'limit': max_correlation_exposure, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking correlation exposure: {e}")
            return True
            
    def _check_volatility_limits(self, symbol: str, signal: Dict) -> bool:
        try:
            asset_volatility = self._get_asset_volatility(symbol)
            max_volatility = self.volatility_limits['max_asset_volatility']
            if asset_volatility > max_volatility:
                self.risk_alerts.append({'type': 'volatility_limit_breach', 'symbol': symbol, 'volatility': asset_volatility, 'limit': max_volatility, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking volatility limits for {symbol}: {e}")
            return True
            
    def _check_liquidity_requirements(self, symbol: str, signal: Dict) -> bool:
        try:
            liquidity_score = self._calculate_liquidity_score(symbol)
            min_liquidity = 0.5
            if liquidity_score < min_liquidity:
                self.risk_alerts.append({'type': 'liquidity_requirement_breach', 'symbol': symbol, 'liquidity_score': liquidity_score, 'minimum_required': min_liquidity, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking liquidity requirements for {symbol}: {e}")
            return True
            
    def _check_risk_capacity(self, symbol: str, signal: Dict, current_positions: Dict) -> bool:
        try:
            current_var = self._calculate_portfolio_var(current_positions)
            signal_var = self._estimate_signal_var(symbol, signal)
            projected_var = current_var + signal_var
            max_var = self._get_portfolio_value() * 0.05
            if projected_var > max_var:
                self.risk_alerts.append({'type': 'risk_capacity_breach', 'symbol': symbol, 'projected_var': projected_var, 'limit': max_var, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking risk capacity: {e}")
            return True
            
    def _check_drawdown_limits(self, current_positions: Dict) -> bool:
        try:
            current_drawdown = self._calculate_current_drawdown()
            max_drawdown = self.drawdown_limits['max_trailing_drawdown']
            if current_drawdown > max_drawdown:
                self.risk_alerts.append({'type': 'drawdown_limit_breach', 'current_drawdown': current_drawdown, 'limit': max_drawdown, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking drawdown limits: {e}")
            return True
            
    def _check_concentration_limits(self, symbol: str, signal: Dict, current_positions: Dict) -> bool:
        try:
            portfolio_value = self._get_portfolio_value()
            current_position = current_positions.get(symbol, {})
            current_exposure = abs(current_position.get('notional', 0))
            signal_exposure = abs(signal.get('notional', 0))
            total_exposure = current_exposure + signal_exposure
            concentration = total_exposure / portfolio_value if portfolio_value > 0 else 0
            max_concentration = self.position_limits['max_single_asset_exposure']
            if concentration > max_concentration:
                self.risk_alerts.append({'type': 'concentration_limit_breach', 'symbol': symbol, 'concentration': concentration, 'limit': max_concentration, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking concentration limits: {e}")
            return True
            
    def _check_leverage_limits(self, symbol: str, signal: Dict, current_positions: Dict) -> bool:
        try:
            total_notional = sum([abs(pos.get('notional', 0)) for pos in current_positions.values()])
            signal_notional = abs(signal.get('notional', 0))
            portfolio_value = self._get_portfolio_value()
            new_leverage = (total_notional + signal_notional) / portfolio_value if portfolio_value > 0 else 0
            max_leverage = self.position_limits['max_leverage']
            if new_leverage > max_leverage:
                self.risk_alerts.append({'type': 'leverage_limit_breach', 'symbol': symbol, 'leverage': new_leverage, 'limit': max_leverage, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking leverage limits: {e}")
            return True
            
    def _check_market_conditions(self, symbol: str, signal: Dict) -> bool:
        try:
            market_volatility = self._get_market_volatility()
            volatility_threshold = 0.5
            if market_volatility > volatility_threshold:
                signal_confidence = signal.get('confidence', 0)
                min_confidence_high_vol = 0.8
                if signal_confidence < min_confidence_high_vol:
                    self.risk_alerts.append({'type': 'market_condition_breach', 'symbol': symbol, 'market_volatility': market_volatility, 'signal_confidence': signal_confidence, 'required_confidence': min_confidence_high_vol, 'timestamp': datetime.now()})
                    return False
            return True
        except Exception as e:
            print(f"Error checking market conditions: {e}")
            return True
            
    def _check_operational_constraints(self, symbol: str, signal: Dict) -> bool:
        try:
            trading_hours = self._check_trading_hours(symbol)
            system_health = self._check_system_health()
            data_quality = self._check_data_quality(symbol)
            if not trading_hours:
                self.risk_alerts.append({'type': 'operational_constraint', 'symbol': symbol, 'reason': 'outside_trading_hours', 'timestamp': datetime.now()})
                return False
            if not system_health:
                self.risk_alerts.append({'type': 'operational_constraint', 'symbol': symbol, 'reason': 'system_health_poor', 'timestamp': datetime.now()})
                return False
            if not data_quality:
                self.risk_alerts.append({'type': 'operational_constraint', 'symbol': symbol, 'reason': 'data_quality_poor', 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking operational constraints: {e}")
            return True
            
    def _check_regulatory_constraints(self, symbol: str, signal: Dict) -> bool:
        try:
            position_reporting_threshold = 10000
            signal_notional = abs(signal.get('notional', 0))
            if signal_notional > position_reporting_threshold:
                self._trigger_position_reporting(symbol, signal)
            leverage_ratio = self._calculate_leverage_ratio()
            max_regulatory_leverage = 10.0
            if leverage_ratio > max_regulatory_leverage:
                self.risk_alerts.append({'type': 'regulatory_constraint', 'symbol': symbol, 'leverage_ratio': leverage_ratio, 'limit': max_regulatory_leverage, 'timestamp': datetime.now()})
                return False
            return True
        except Exception as e:
            print(f"Error checking regulatory constraints: {e}")
            return True
            
    def calculate_position_size(self, symbol: str, signal: Dict, portfolio_value: float) -> float:
        try:
            base_size = self._calculate_base_position_size(symbol, signal, portfolio_value)
            volatility_adjustment = self._apply_volatility_scaling(symbol, base_size)
            correlation_adjustment = self._apply_correlation_scaling(symbol, volatility_adjustment)
            confidence_adjustment = self._apply_confidence_scaling(signal, correlation_adjustment)
            liquidity_adjustment = self._apply_liquidity_scaling(symbol, confidence_adjustment)
            regime_adjustment = self._apply_regime_scaling(symbol, liquidity_adjustment)
            final_size = self._apply_position_limits(symbol, regime_adjustment, portfolio_value)
            return max(0, final_size)
        except Exception as e:
            print(f"Error calculating position size for {symbol}: {e}")
            return 0
            
    def _calculate_base_position_size(self, symbol: str, signal: Dict, portfolio_value: float) -> float:
        try:
            kelly_fraction = self._calculate_kelly_fraction(symbol, signal)
            risk_target = self.volatility_limits['volatility_scaling_factor']
            asset_volatility = self._get_asset_volatility(symbol)
            volatility_scaled_fraction = risk_target / asset_volatility if asset_volatility > 0 else 0
            position_fraction = min(kelly_fraction, volatility_scaled_fraction)
            position_fraction = min(position_fraction, self.position_limits['max_position_size_pct'])
            base_size = portfolio_value * position_fraction
            return base_size
        except Exception as e:
            print(f"Error calculating base position size: {e}")
            return 0
            
    def _calculate_kelly_fraction(self, symbol: str, signal: Dict) -> float:
        try:
            win_rate = signal.get('win_probability', 0.55)
            avg_win = signal.get('avg_win', 0.02)
            avg_loss = signal.get('avg_loss', 0.01)
            if avg_loss == 0:
                return 0
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_loss
            kelly_fraction = max(0, min(kelly_fraction, 0.25))
            return kelly_fraction
        except Exception as e:
            print(f"Error calculating Kelly fraction: {e}")
            return 0.05
            
    def _apply_volatility_scaling(self, symbol: str, base_size: float) -> float:
        try:
            current_volatility = self._get_asset_volatility(symbol)
            target_volatility = self.volatility_limits['volatility_scaling_factor']
            if current_volatility == 0:
                return 0
            volatility_scalar = target_volatility / current_volatility
            volatility_scalar = min(volatility_scalar, 2.0)
            volatility_scalar = max(volatility_scalar, 0.1)
            return base_size * volatility_scalar
        except Exception as e:
            print(f"Error applying volatility scaling: {e}")
            return base_size
            
    def _apply_correlation_scaling(self, symbol: str, size: float) -> float:
        try:
            avg_correlation = self._get_average_portfolio_correlation(symbol)
            correlation_scalar = 1.0 - (avg_correlation * 0.5)
            correlation_scalar = max(correlation_scalar, 0.2)
            return size * correlation_scalar
        except Exception as e:
            print(f"Error applying correlation scaling: {e}")
            return size
            
    def _apply_confidence_scaling(self, signal: Dict, size: float) -> float:
        try:
            confidence = signal.get('confidence', 0.5)
            min_confidence = 0.5
            max_confidence = 1.0
            normalized_confidence = (confidence - min_confidence) / (max_confidence - min_confidence)
            normalized_confidence = max(0, min(normalized_confidence, 1))
            confidence_scalar = 0.3 + (0.7 * normalized_confidence)
            return size * confidence_scalar
        except Exception as e:
            print(f"Error applying confidence scaling: {e}")
            return size
            
    def _apply_liquidity_scaling(self, symbol: str, size: float) -> float:
        try:
            liquidity_score = self._calculate_liquidity_score(symbol)
            liquidity_scalar = liquidity_score
            liquidity_scalar = max(liquidity_scalar, 0.1)
            return size * liquidity_scalar
        except Exception as e:
            print(f"Error applying liquidity scaling: {e}")
            return size
            
    def _apply_regime_scaling(self, symbol: str, size: float) -> float:
        try:
            market_regime = self._detect_market_regime()
            regime_scalars = {'bull_market': 1.2, 'bear_market': 0.6, 'sideways_market': 0.8, 'high_volatility': 0.5, 'low_volatility': 1.1}
            regime_scalar = regime_scalars.get(market_regime, 1.0)
            return size * regime_scalar
        except Exception as e:
            print(f"Error applying regime scaling: {e}")
            return size
            
    def _apply_position_limits(self, symbol: str, size: float, portfolio_value: float) -> float:
        try:
            max_notional = self.position_limits['max_notional_per_trade']
            min_notional = self.position_limits['min_notional_per_trade']
            size = min(size, max_notional)
            size = max(size, min_notional) if size > 0 else 0
            max_percentage = self.position_limits['max_position_size_pct'] * portfolio_value
            size = min(size, max_percentage)
            return size
        except Exception as e:
            print(f"Error applying position limits: {e}")
            return 0
            
    def _get_portfolio_value(self) -> float:
        return 100000.0
        
    def _get_correlation(self, symbol1: str, symbol2: str) -> float:
        return 0.3
        
    def _get_asset_volatility(self, symbol: str) -> float:
        return 0.25
        
    def _get_market_volatility(self) -> float:
        return 0.20
        
    def _calculate_liquidity_score(self, symbol: str) -> float:
        return 0.8
        
    def _calculate_portfolio_var(self, positions: Dict) -> float:
        return 5000.0
        
    def _estimate_signal_var(self, symbol: str, signal: Dict) -> float:
        return 1000.0
        
    def _calculate_current_drawdown(self) -> float:
        return 0.05
        
    def _check_trading_hours(self, symbol: str) -> bool:
        return True
        
    def _check_system_health(self) -> bool:
        return True
        
    def _check_data_quality(self, symbol: str) -> bool:
        return True
        
    def _calculate_leverage_ratio(self) -> float:
        return 2.0
        
    def _trigger_position_reporting(self, symbol: str, signal: Dict):
        pass
        
    def _get_average_portfolio_correlation(self, symbol: str) -> float:
        return 0.4
        
    def _detect_market_regime(self) -> str:
        return 'sideways_market'
        
    def _log_validation_failure(self, symbol: str, signal: Dict, checks: List[bool]):
        failed_checks = []
        check_names = ['position_limits', 'portfolio_heat', 'correlation_exposure', 'volatility_limits', 'liquidity_requirements', 'risk_capacity', 'drawdown_limits', 'concentration_limits', 'leverage_limits', 'market_conditions', 'operational_constraints', 'regulatory_constraints']
        for i, check_result in enumerate(checks):
            if not check_result:
                failed_checks.append(check_names[i])
        print(f"Signal validation failed for {symbol}. Failed checks: {failed_checks}")
        
    def calculate_portfolio_risk_metrics(self, positions: Dict) -> Dict:
        try:
            metrics = {}
            metrics['var_1d_95'] = self._calculate_var(positions, 1, 0.95)
            metrics['var_1d_99'] = self._calculate_var(positions, 1, 0.99)
            metrics['var_10d_99'] = self._calculate_var(positions, 10, 0.99)
            metrics['expected_shortfall_95'] = self._calculate_expected_shortfall(positions, 0.95)
            metrics['expected_shortfall_99'] = self._calculate_expected_shortfall(positions, 0.99)
            metrics['portfolio_volatility'] = self._calculate_portfolio_volatility(positions)
            metrics['portfolio_beta'] = self._calculate_portfolio_beta(positions)
            metrics['maximum_drawdown'] = self._calculate_maximum_drawdown()
            metrics['current_drawdown'] = self._calculate_current_drawdown()
            metrics['sharpe_ratio'] = self._calculate_sharpe_ratio()
            metrics['sortino_ratio'] = self._calculate_sortino_ratio()
            metrics['calmar_ratio'] = self._calculate_calmar_ratio()
            metrics['concentration_risk'] = self._calculate_concentration_risk(positions)
            metrics['correlation_risk'] = self._calculate_correlation_risk(positions)
            metrics['liquidity_risk'] = self._calculate_liquidity_risk(positions)
            return metrics
        except Exception as e:
            print(f"Error calculating portfolio risk metrics: {e}")
            return {}
            
    def _calculate_var(self, positions: Dict, time_horizon: int, confidence_level: float) -> float:
        try:
            portfolio_value = self._get_portfolio_value()
            portfolio_volatility = self._calculate_portfolio_volatility(positions)
            from scipy import stats
            z_score = stats.norm.ppf(confidence_level)
            var = portfolio_value * portfolio_volatility * np.sqrt(time_horizon) * z_score
            return var
        except Exception as e:
            print(f"Error calculating VaR: {e}")
            return 0
            
    def _calculate_expected_shortfall(self, positions: Dict, confidence_level: float) -> float:
        try:
            var = self._calculate_var(positions, 1, confidence_level)
            from scipy import stats
            z_score = stats.norm.ppf(confidence_level)
            expected_shortfall = var * (stats.norm.pdf(z_score) / (1 - confidence_level))
            return expected_shortfall
        except Exception as e:
            print(f"Error calculating Expected Shortfall: {e}")
            return 0
            
    def _calculate_portfolio_volatility(self, positions: Dict) -> float:
        try:
            if not positions:
                return 0
            portfolio_value = self._get_portfolio_value()
            weighted_volatility = 0
            for symbol, position in positions.items():
                weight = abs(position.get('notional', 0)) / portfolio_value
                asset_vol = self._get_asset_volatility(symbol)
                weighted_volatility += (weight ** 2) * (asset_vol ** 2)
            for symbol1, position1 in positions.items():
                for symbol2, position2 in positions.items():
                    if symbol1 != symbol2:
                        weight1 = abs(position1.get('notional', 0)) / portfolio_value
                        weight2 = abs(position2.get('notional', 0)) / portfolio_value
                        vol1 = self._get_asset_volatility(symbol1)
                        vol2 = self._get_asset_volatility(symbol2)
                        correlation = self._get_correlation(symbol1, symbol2)
                        weighted_volatility += weight1 * weight2 * vol1 * vol2 * correlation
            return np.sqrt(weighted_volatility)
        except Exception as e:
            print(f"Error calculating portfolio volatility: {e}")
            return 0
            
    def _calculate_portfolio_beta(self, positions: Dict) -> float:
        try:
            portfolio_value = self._get_portfolio_value()
            weighted_beta = 0
            for symbol, position in positions.items():
                weight = abs(position.get('notional', 0)) / portfolio_value
                asset_beta = self._get_asset_beta(symbol)
                weighted_beta += weight * asset_beta
            return weighted_beta
        except Exception as e:
            print(f"Error calculating portfolio beta: {e}")
            return 1.0
            
    def _get_asset_beta(self, symbol: str) -> float:
        return 1.0
        
    def _calculate_maximum_drawdown(self) -> float:
        return 0.10
        
    def _calculate_sharpe_ratio(self) -> float:
        return 1.5
        
    def _calculate_sortino_ratio(self) -> float:
        return 2.0
        
    def _calculate_calmar_ratio(self) -> float:
        return 1.2
        
    def _calculate_concentration_risk(self, positions: Dict) -> float:
        try:
            if not positions:
                return 0
            portfolio_value = self._get_portfolio_value()
            weights = []
            for position in positions.values():
                weight = abs(position.get('notional', 0)) / portfolio_value
                weights.append(weight)
            weights = np.array(weights)
            herfindahl_index = np.sum(weights ** 2)
            return herfindahl_index
        except Exception as e:
            print(f"Error calculating concentration risk: {e}")
            return 0
            
    def _calculate_correlation_risk(self, positions: Dict) -> float:
        try:
            if len(positions) < 2:
                return 0
            symbols = list(positions.keys())
            total_correlation = 0
            pairs = 0
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols[i+1:], i+1):
                    correlation = abs(self._get_correlation(symbol1, symbol2))
                    total_correlation += correlation
                    pairs += 1
            avg_correlation = total_correlation / pairs if pairs > 0 else 0
            return avg_correlation
        except Exception as e:
            print(f"Error calculating correlation risk: {e}")
            return 0
            
    def _calculate_liquidity_risk(self, positions: Dict) -> float:
        try:
            portfolio_value = self._get_portfolio_value()
            weighted_liquidity_risk = 0
            for symbol, position in positions.items():
                weight = abs(position.get('notional', 0)) / portfolio_value
                liquidity_score = self._calculate_liquidity_score(symbol)
                illiquidity_risk = 1 - liquidity_score
                weighted_liquidity_risk += weight * illiquidity_risk
            return weighted_liquidity_risk
        except Exception as e:
            print(f"Error calculating liquidity risk: {e}")
            return 0
            
    def run_stress_tests(self, positions: Dict) -> Dict:
        try:
            stress_results = {}
            for scenario_name, scenario_params in self.stress_test_scenarios.items():
                scenario_result = self._run_single_stress_test(positions, scenario_params)
                stress_results[scenario_name] = scenario_result
            return stress_results
        except Exception as e:
            print(f"Error running stress tests: {e}")
            return {}
            
    def _run_single_stress_test(self, positions: Dict, scenario_params: Dict) -> Dict:
        try:
            portfolio_value = self._get_portfolio_value()
            stressed_pnl = 0
            for symbol, position in positions.items():
                position_value = position.get('notional', 0)
                if 'equity_shock' in scenario_params:
                    shock = scenario_params['equity_shock']
                    stressed_pnl += position_value * shock
                if 'volatility_spike' in scenario_params:
                    vol_multiplier = scenario_params['volatility_spike']
                    current_vol = self._get_asset_volatility(symbol)
                    stressed_vol = current_vol * vol_multiplier
                    vol_impact = position_value * (stressed_vol - current_vol) * -0.1
                    stressed_pnl += vol_impact
            stressed_return = stressed_pnl / portfolio_value
            return {'stressed_pnl': stressed_pnl, 'stressed_return': stressed_return, 'portfolio_value_after': portfolio_value + stressed_pnl, 'max_drawdown_scenario': abs(min(0, stressed_return))}
        except Exception as e:
            print(f"Error running single stress test: {e}")
            return {}
            
    def generate_risk_report(self, positions: Dict) -> Dict:
        try:
            risk_report = {'timestamp': datetime.now(), 'portfolio_metrics': self.calculate_portfolio_risk_metrics(positions), 'stress_test_results': self.run_stress_tests(positions), 'risk_alerts': self.risk_alerts[-10:], 'breached_limits': self.breached_limits, 'position_summary': self._generate_position_summary(positions), 'risk_attribution': self._calculate_risk_attribution(positions), 'recommendations': self._generate_risk_recommendations(positions)}
            return risk_report
        except Exception as e:
            print(f"Error generating risk report: {e}")
            return {}
            
    def _generate_position_summary(self, positions: Dict) -> Dict:
        try:
            portfolio_value = self._get_portfolio_value()
            summary = {'total_positions': len(positions), 'total_exposure': sum([abs(pos.get('notional', 0)) for pos in positions.values()]), 'net_exposure': sum([pos.get('notional', 0) for pos in positions.values()]), 'leverage': 0, 'largest_position': 0, 'position_concentration': {}}
            if portfolio_value > 0:
                summary['leverage'] = summary['total_exposure'] / portfolio_value
            if positions:
                largest_pos_value = max([abs(pos.get('notional', 0)) for pos in positions.values()])
                summary['largest_position'] = largest_pos_value / portfolio_value
                for symbol, position in positions.items():
                    weight = abs(position.get('notional', 0)) / portfolio_value
                    summary['position_concentration'][symbol] = weight
            return summary
        except Exception as e:
            print(f"Error generating position summary: {e}")
            return {}
            
    def _calculate_risk_attribution(self, positions: Dict) -> Dict:
        try:
            attribution = {'factor_risk': {}, 'idiosyncratic_risk': {}, 'concentration_risk': self._calculate_concentration_risk(positions), 'correlation_risk': self._calculate_correlation_risk(positions), 'liquidity_risk': self._calculate_liquidity_risk(positions)}
            portfolio_value = self._get_portfolio_value()
            for symbol, position in positions.items():
                weight = abs(position.get('notional', 0)) / portfolio_value
                asset_vol = self._get_asset_volatility(symbol)
                attribution['factor_risk'][symbol] = weight * asset_vol * 0.7
                attribution['idiosyncratic_risk'][symbol] = weight * asset_vol * 0.3
            return attribution
        except Exception as e:
            print(f"Error calculating risk attribution: {e}")
            return {}
            
    def _generate_risk_recommendations(self, positions: Dict) -> List[str]:
        try:
            recommendations = []
            portfolio_metrics = self.calculate_portfolio_risk_metrics(positions)
            if portfolio_metrics.get('portfolio_volatility', 0) > self.volatility_limits['max_portfolio_volatility']:
                recommendations.append("Portfolio volatility exceeds target - consider reducing position sizes")
            if portfolio_metrics.get('concentration_risk', 0) > 0.5:
                recommendations.append("High concentration risk detected - diversify holdings")
            if portfolio_metrics.get('correlation_risk', 0) > 0.7:
                recommendations.append("High correlation between positions - seek uncorrelated assets")
            if portfolio_metrics.get('liquidity_risk', 0) > 0.3:
                recommendations.append("Liquidity risk elevated - increase allocation to liquid assets")
            if len(self.risk_alerts) > 5:
                recommendations.append("Multiple risk alerts triggered - review risk management framework")
            return recommendations
        except Exception as e:
            print(f"Error generating risk recommendations: {e}")
            return []
            
    def monitor_risk_limits(self, positions: Dict) -> Dict:
        try:
            limit_status = {'position_limits': 'OK', 'leverage_limits': 'OK', 'concentration_limits': 'OK', 'volatility_limits': 'OK', 'drawdown_limits': 'OK', 'correlation_limits': 'OK', 'liquidity_limits': 'OK', 'var_limits': 'OK'}
            portfolio_value = self._get_portfolio_value()
            total_exposure = sum([abs(pos.get('notional', 0)) for pos in positions.values()])
            leverage = total_exposure / portfolio_value if portfolio_value > 0 else 0
            if leverage > self.position_limits['max_leverage']:
                limit_status['leverage_limits'] = 'BREACH'
            concentration_risk = self._calculate_concentration_risk(positions)
            if concentration_risk > 0.5:
                limit_status['concentration_limits'] = 'WARNING'
            portfolio_vol = self._calculate_portfolio_volatility(positions)
            if portfolio_vol > self.volatility_limits['max_portfolio_volatility']:
                limit_status['volatility_limits'] = 'BREACH'
            current_drawdown = self._calculate_current_drawdown()
            if current_drawdown > self.drawdown_limits['max_trailing_drawdown']:
                limit_status['drawdown_limits'] = 'BREACH'
            correlation_risk = self._calculate_correlation_risk(positions)
            if correlation_risk > 0.7:
                limit_status['correlation_limits'] = 'WARNING'
            liquidity_risk = self._calculate_liquidity_risk(positions)
            if liquidity_risk > 0.3:
                limit_status['liquidity_limits'] = 'WARNING'
            var_99 = self._calculate_var(positions, 1, 0.99)
            if var_99 > portfolio_value * 0.05:
                limit_status['var_limits'] = 'WARNING'
            overall_status = 'OK' if all(status in ['OK', 'WARNING'] for status in limit_status.values()) else 'CRITICAL'
            return {'overall_status': overall_status, 'limit_status': limit_status, 'metrics': {'leverage': leverage, 'concentration_risk': concentration_risk, 'portfolio_volatility': portfolio_vol, 'current_drawdown': current_drawdown, 'correlation_risk': correlation_risk, 'liquidity_risk': liquidity_risk, 'var_99': var_99}, 'timestamp': datetime.now()}
        except Exception as e:
            print(f"Error monitoring risk limits: {e}")
            return {'overall_status': 'ERROR', 'error': str(e)}
            
    def calculate_risk_adjusted_returns(self, positions: Dict, returns_data: pd.DataFrame) -> Dict:
        try:
            if returns_data.empty:
                return {}
            total_return = returns_data.sum()
            volatility = returns_data.std()
            downside_returns = returns_data[returns_data < 0]
            downside_volatility = downside_returns.std() if len(downside_returns) > 0 else 0
            max_drawdown = self._calculate_running_max_drawdown(returns_data)
            sharpe_ratio = (total_return / volatility) if volatility > 0 else 0
            sortino_ratio = (total_return / downside_volatility) if downside_volatility > 0 else 0
            calmar_ratio = (total_return / abs(max_drawdown)) if max_drawdown != 0 else 0
            var_95 = np.percentile(returns_data, 5)
            var_99 = np.percentile(returns_data, 1)
            cvar_95 = returns_data[returns_data <= var_95].mean()
            cvar_99 = returns_data[returns_data <= var_99].mean()
            return {'total_return': total_return, 'volatility': volatility, 'downside_volatility': downside_volatility, 'max_drawdown': max_drawdown, 'sharpe_ratio': sharpe_ratio, 'sortino_ratio': sortino_ratio, 'calmar_ratio': calmar_ratio, 'var_95': var_95, 'var_99': var_99, 'cvar_95': cvar_95, 'cvar_99': cvar_99, 'skewness': returns_data.skew(), 'kurtosis': returns_data.kurtosis(), 'best_day': returns_data.max(), 'worst_day': returns_data.min()}
        except Exception as e:
            print(f"Error calculating risk-adjusted returns: {e}")
            return {}
            
    def _calculate_running_max_drawdown(self, returns: pd.Series) -> float:
        try:
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return drawdown.min()
        except Exception as e:
            return 0.0
            
    def optimize_portfolio_allocation(self, expected_returns: Dict, covariance_matrix: pd.DataFrame, risk_aversion: float = 1.0) -> Dict:
        try:
            from scipy.optimize import minimize
            n_assets = len(expected_returns)
            if n_assets == 0:
                return {}
            returns_array = np.array(list(expected_returns.values()))
            cov_matrix = covariance_matrix.values if isinstance(covariance_matrix, pd.DataFrame) else covariance_matrix
            def objective(weights):
                portfolio_return = np.dot(weights, returns_array)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                return -(portfolio_return - 0.5 * risk_aversion * portfolio_variance)
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, self.position_limits['max_single_asset_exposure']) for _ in range(n_assets))
            initial_guess = np.array([1/n_assets] * n_assets)
            result = minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
            if result.success:
                optimal_weights = dict(zip(expected_returns.keys(), result.x))
                portfolio_return = np.dot(result.x, returns_array)
                portfolio_variance = np.dot(result.x.T, np.dot(cov_matrix, result.x))
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
                return {'optimal_weights': optimal_weights, 'expected_return': portfolio_return, 'expected_volatility': portfolio_volatility, 'expected_sharpe': sharpe_ratio, 'optimization_success': True}
            else:
                return {'optimization_success': False, 'error': result.message}
        except Exception as e:
            print(f"Error optimizing portfolio allocation: {e}")
            return {'optimization_success': False, 'error': str(e)}
            
    def calculate_marginal_var(self, positions: Dict, symbol: str) -> float:
        try:
            current_var = self._calculate_var(positions, 1, 0.99)
            epsilon = 0.01
            test_positions = positions.copy()
            if symbol in test_positions:
                original_notional = test_positions[symbol].get('notional', 0)
                test_positions[symbol]['notional'] = original_notional * (1 + epsilon)
            else:
                test_positions[symbol] = {'notional': self._get_portfolio_value() * epsilon}
            perturbed_var = self._calculate_var(test_positions, 1, 0.99)
            marginal_var = (perturbed_var - current_var) / (self._get_portfolio_value() * epsilon)
            return marginal_var
        except Exception as e:
            print(f"Error calculating marginal VaR for {symbol}: {e}")
            return 0.0
            
    def calculate_component_var(self, positions: Dict) -> Dict:
        try:
            component_vars = {}
            portfolio_var = self._calculate_var(positions, 1, 0.99)
            portfolio_value = self._get_portfolio_value()
            for symbol, position in positions.items():
                weight = abs(position.get('notional', 0)) / portfolio_value
                marginal_var = self.calculate_marginal_var(positions, symbol)
                component_var = weight * marginal_var
                component_vars[symbol] = component_var
            return component_vars
        except Exception as e:
            print(f"Error calculating component VaR: {e}")
            return {}
            
    def emergency_risk_shutdown(self, positions: Dict) -> Dict:
        try:
            shutdown_actions = []
            current_drawdown = self._calculate_current_drawdown()
            if current_drawdown > self.drawdown_limits['stop_trading_drawdown']:
                shutdown_actions.append('EMERGENCY_STOP_TRADING')
            portfolio_var = self._calculate_var(positions, 1, 0.99)
            portfolio_value = self._get_portfolio_value()
            if portfolio_var > portfolio_value * 0.10:
                shutdown_actions.append('REDUCE_ALL_POSITIONS')
            leverage = sum([abs(pos.get('notional', 0)) for pos in positions.values()]) / portfolio_value
            if leverage > self.position_limits['max_leverage'] * 1.5:
                shutdown_actions.append('FORCE_DELEVER')
            correlation_risk = self._calculate_correlation_risk(positions)
            if correlation_risk > 0.9:
                shutdown_actions.append('DIVERSIFY_HOLDINGS')
            return {'emergency_triggered': len(shutdown_actions) > 0, 'shutdown_actions': shutdown_actions, 'trigger_metrics': {'current_drawdown': current_drawdown, 'portfolio_var': portfolio_var, 'leverage': leverage, 'correlation_risk': correlation_risk}, 'timestamp': datetime.now()}
        except Exception as e:
            print(f"Error in emergency risk shutdown: {e}")
            return {'emergency_triggered': False, 'error': str(e)}