import ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import json
import asyncio
import warnings
warnings.filterwarnings('ignore')

class PortfolioManager:
    def __init__(self, config: Dict, okx_client):
        self.config = config
        self.okx_client = okx_client
        self.account_info = {}
        self.balances = {}
        self.positions = {}
        self.open_orders = {}
        self.trade_history = []
        self.pnl_history = []
        self.performance_metrics = {}
        self.margin_info = {}
        self.funding_history = []
        self.fee_structure = {}
        self.execution_analytics = {}
        self.slippage_tracking = {}
        self.order_book_analytics = {}
        self.market_impact_models = {}
        self.transaction_cost_analysis = {}
        self.best_execution_metrics = {}
        self.position_sizing_models = {}
        self.portfolio_optimization = {}
        self.rebalancing_logic = {}
        self.dynamic_hedging = {}
        self.risk_budgeting = {}
        self.factor_allocation = {}
        self.alpha_generation = {}
        self.beta_management = {}
        self.correlation_trading = {}
        self.volatility_targeting = {}
        self.momentum_strategies = {}
        self.mean_reversion_strategies = {}
        self.arbitrage_strategies = {}
        self.pairs_trading = {}
        self.statistical_arbitrage = {}
        self.cross_asset_strategies = {}
        self.macro_strategies = {}
        self.event_driven_strategies = {}
        self.quantitative_strategies = {}
        self.systematic_strategies = {}
        self.discretionary_strategies = {}
        self.multi_manager_allocation = {}
        self.alternative_risk_premia = {}
        self.smart_beta_strategies = {}
        self.factor_investing = {}
        self.esg_investing = {}
        self.impact_investing = {}
        self.sustainable_investing = {}
        self.thematic_investing = {}
        self.sector_rotation = {}
        self.geographical_allocation = {}
        self.currency_management = {}
        self.commodity_strategies = {}
        self.fixed_income_strategies = {}
        self.equity_strategies = {}
        self.derivatives_strategies = {}
        self.structured_products = {}
        self.private_markets = {}
        self.real_estate_investing = {}
        self.infrastructure_investing = {}
        self.hedge_fund_strategies = {}
        self.mutual_fund_strategies = {}
        self.etf_strategies = {}
        self.index_tracking = {}
        self.active_management = {}
        self.passive_management = {}
        self.enhanced_indexing = {}
        self.core_satellite_approach = {}
        self.barbell_strategy = {}
        self.bullet_strategy = {}
        self.ladder_strategy = {}
        self.swap_strategies = {}
        self.spread_strategies = {}
        self.carry_strategies = {}
        self.basis_trading = {}
        self.calendar_spreads = {}
        self.inter_market_spreads = {}
        self.volatility_strategies = {}
        self.gamma_strategies = {}
        self.vega_strategies = {}
        self.theta_strategies = {}
        self.delta_neutral_strategies = {}
        self.long_short_strategies = {}
        self.market_neutral_strategies = {}
        self.relative_value_strategies = {}
        self.absolute_return_strategies = {}
        self.benchmark_relative_strategies = {}
        self.liability_driven_investing = {}
        self.asset_liability_matching = {}
        self.duration_matching = {}
        self.immunization_strategies = {}
        self.dedication_strategies = {}
        self.cash_flow_matching = {}
        self.horizon_matching = {}
        self.contingent_immunization = {}
        self.dynamic_asset_allocation = {}
        self.tactical_asset_allocation = {}
        self.strategic_asset_allocation = {}
        self.behavioral_portfolio_theory = {}
        self.mental_accounting = {}
        self.prospect_theory = {}
        self.loss_aversion = {}
        self.overconfidence_bias = {}
        self.anchoring_bias = {}
        self.availability_bias = {}
        self.confirmation_bias = {}
        self.representativeness_bias = {}
        self.recency_bias = {}
        self.herding_behavior = {}
        self.momentum_bias = {}
        self.contrarian_bias = {}
        self.disposition_effect = {}
        self.endowment_effect = {}
        self.status_quo_bias = {}
        self.framing_effects = {}
        self.mental_shortcuts = {}
        self.cognitive_dissonance = {}
        self.emotional_investing = {}
        self.fear_and_greed = {}
        self.market_sentiment = {}
        self.investor_sentiment = {}
        self.sentiment_indicators = {}
        self.technical_analysis = {}
        self.fundamental_analysis = {}
        self.quantitative_analysis = {}
        self.behavioral_analysis = {}
        self.market_microstructure = {}
        self.high_frequency_trading = {}
        self.algorithmic_trading = {}
        self.program_trading = {}
        self.electronic_trading = {}
        self.dark_pools = {}
        self.lit_pools = {}
        self.fragmented_markets = {}
        self.market_making = {}
        self.liquidity_provision = {}
        self.price_discovery = {}
        self.information_asymmetry = {}
        self.adverse_selection = {}
        self.moral_hazard = {}
        self.agency_problems = {}
        self.principal_agent_conflicts = {}
        self.fiduciary_duty = {}
        self.best_interest_standards = {}
        self.suitability_requirements = {}
        self.know_your_customer = {}
        self.anti_money_laundering = {}
        self.compliance_monitoring = {}
        self.regulatory_reporting = {}
        self.audit_requirements = {}
        self.record_keeping = {}
        self.trade_surveillance = {}
        self.market_abuse_prevention = {}
        self.insider_trading_prevention = {}
        self.front_running_prevention = {}
        self.wash_trading_prevention = {}
        self.layering_prevention = {}
        self.spoofing_prevention = {}
        self.pump_and_dump_prevention = {}
        self.corner_squeeze_prevention = {}
        self.manipulation_prevention = {}
        self.operational_risk_management = {}
        self.technology_risk = {}
        self.cybersecurity_risk = {}
        self.data_risk = {}
        self.model_risk = {}
        self.liquidity_risk = {}
        self.credit_risk = {}
        self.market_risk = {}
        self.concentration_risk = {}
        self.counterparty_risk = {}
        self.settlement_risk = {}
        self.custody_risk = {}
        self.legal_risk = {}
        self.regulatory_risk = {}
        self.reputation_risk = {}
        self.business_risk = {}
        self.strategic_risk = {}
        self.environmental_risk = {}
        self.social_risk = {}
        self.governance_risk = {}
        self.sustainability_risk = {}
        self.climate_risk = {}
        self.transition_risk = {}
        self.physical_risk = {}
        self.stranded_assets = {}
        self.green_finance = {}
        self.sustainable_finance = {}
        self.responsible_investing = {}
        self.impact_measurement = {}
        self.esg_integration = {}
        self.stewardship = {}
        self.engagement = {}
        self.proxy_voting = {}
        self.shareholder_activism = {}
        self.corporate_governance = {}
        self.board_effectiveness = {}
        self.executive_compensation = {}
        self.risk_management_oversight = {}
        self.audit_committee_oversight = {}
        self.internal_controls = {}
        self.compliance_programs = {}
        self.ethics_programs = {}
        self.whistleblower_programs = {}
        self.conflict_of_interest = {}
        self.related_party_transactions = {}
        self.disclosure_requirements = {}
        self.transparency_standards = {}
        self.accountability_mechanisms = {}
        self.performance_measurement = {}
        self.benchmark_construction = {}
        self.benchmark_selection = {}
        self.performance_attribution = {}
        self.risk_attribution = {}
        self.cost_attribution = {}
        self.alpha_attribution = {}
        self.beta_attribution = {}
        self.factor_attribution = {}
        self.sector_attribution = {}
        self.security_selection = {}
        self.asset_allocation_attribution = {}
        self.timing_attribution = {}
        self.interaction_effects = {}
        self.brinson_attribution = {}
        self.fachler_attribution = {}
        self.ankrim_hensel_attribution = {}
        self.carhart_attribution = {}
        self.fama_french_attribution = {}
        self.arbitrage_pricing_theory = {}
        self.capital_asset_pricing_model = {}
        self.multi_factor_models = {}
        self.style_analysis = {}
        self.holdings_based_analysis = {}
        self.returns_based_analysis = {}
        self.fundamental_factor_models = {}
        self.statistical_factor_models = {}
        self.macroeconomic_factor_models = {}
        self.sector_factor_models = {}
        self.country_factor_models = {}
        self.currency_factor_models = {}
        self.term_structure_models = {}
        self.volatility_models = {}
        self.correlation_models = {}
        self.regime_switching_models = {}
        self.markov_models = {}
        self.hidden_markov_models = {}
        self.state_space_models = {}
        self.kalman_filter_models = {}
        self.particle_filter_models = {}
        self.monte_carlo_methods = {}
        self.quasi_monte_carlo = {}
        self.latin_hypercube_sampling = {}
        self.importance_sampling = {}
        self.stratified_sampling = {}
        self.antithetic_variates = {}
        self.control_variates = {}
        self.variance_reduction = {}
        self.simulation_optimization = {}
        self.stochastic_optimization = {}
        self.robust_optimization = {}
        self.distributionally_robust = {}
        self.worst_case_optimization = {}
        self.minimax_optimization = {}
        self.regret_minimization = {}
        self.online_optimization = {}
        self.reinforcement_learning = {}
        self.multi_armed_bandits = {}
        self.contextual_bandits = {}
        self.thompson_sampling = {}
        self.upper_confidence_bounds = {}
        self.epsilon_greedy = {}
        self.gradient_bandits = {}
        self.policy_gradient = {}
        self.actor_critic = {}
        self.deep_q_networks = {}
        self.double_dqn = {}
        self.dueling_dqn = {}
        self.rainbow_dqn = {}
        self.proximal_policy_optimization = {}
        self.trust_region_policy_optimization = {}
        self.soft_actor_critic = {}
        self.twin_delayed_ddpg = {}
        self.distributed_rl = {}
        self.multi_agent_rl = {}
        self.hierarchical_rl = {}
        self.meta_learning = {}
        self.few_shot_learning = {}
        self.transfer_learning = {}
        self.domain_adaptation = {}
        self.continual_learning = {}
        self.lifelong_learning = {}
        self.federated_learning = {}
        self.differential_privacy = {}
        self.homomorphic_encryption = {}
        self.secure_aggregation = {}
        self.privacy_preserving_ml = {}
        self.explainable_ai = {}
        self.interpretable_ml = {}
        self.fairness_ml = {}
        self.bias_mitigation = {}
        self.algorithmic_auditing = {}
        self.responsible_ai = {}
        self.ethical_ai = {}
        self.trustworthy_ai = {}
        self.human_ai_collaboration = {}
        self.augmented_intelligence = {}
        self.hybrid_intelligence = {}
        self.human_in_the_loop = {}
        self.active_learning = {}
        self.uncertainty_quantification = {}
        self.conformal_prediction = {}
        self.bayesian_optimization = {}
        self.gaussian_processes = {}
        self.neural_architecture_search = {}
        self.automl = {}
        self.hyperparameter_optimization = {}
        self.model_selection = {}
        self.ensemble_methods = {}
        self.stacking = {}
        self.blending = {}
        self.voting = {}
        self.bagging = {}
        self.boosting = {}
        self.random_forests = {}
        self.gradient_boosting = {}
        self.xgboost = {}
        self.lightgbm = {}
        self.catboost = {}
        self.neural_networks = {}
        self.deep_learning = {}
        self.convolutional_networks = {}
        self.recurrent_networks = {}
        self.transformer_networks = {}
        self.attention_mechanisms = {}
        self.graph_neural_networks = {}
        self.generative_models = {}
        self.variational_autoencoders = {}
        self.generative_adversarial_networks = {}
        self.diffusion_models = {}
        self.normalizing_flows = {}
        self.energy_based_models = {}
        self.score_based_models = {}
        self.autoregressive_models = {}
        self.sequence_to_sequence = {}
        self.language_models = {}
        self.large_language_models = {}
        self.foundation_models = {}
        self.multimodal_models = {}
        self.vision_language_models = {}
        self.code_generation_models = {}
        self.time_series_models = {}
        self.forecasting_models = {}
        self.anomaly_detection = {}
        self.change_point_detection = {}
        self.outlier_detection = {}
        self.novelty_detection = {}
        self.drift_detection = {}
        self.concept_drift = {}
        self.distribution_shift = {}
        self.covariate_shift = {}
        self.label_shift = {}
        self.domain_shift = {}
        self.temporal_shift = {}
        self.adversarial_shift = {}
        self.natural_shift = {}
        self.systematic_shift = {}
        self.gradual_shift = {}
        self.sudden_shift = {}
        self.recurrent_shift = {}
        self.incremental_shift = {}
        self.virtual_shift = {}
        self.real_shift = {}
        
    def initialize(self):
        try:
            self._fetch_account_info()
            self._fetch_balances()
            self._fetch_positions()
            self._fetch_open_orders()
            self._setup_fee_structure()
            self._initialize_analytics()
            return True
        except Exception as e:
            print(f"Failed to initialize portfolio manager: {e}")
            return False
            
    def _fetch_account_info(self):
        try:
            self.account_info = self.okx_client.fetch_account()
            print(f"Account initialized: {self.account_info.get('type', 'unknown')}")
        except Exception as e:
            print(f"Error fetching account info: {e}")
            self.account_info = {}
            
    def _fetch_balances(self):
        try:
            balance_data = self.okx_client.fetch_balance()
            
            self.balances = {}
            for currency, balance in balance_data['info'].items():
                if isinstance(balance, dict):
                    self.balances[currency] = {
                        'free': float(balance.get('free', 0)),
                        'used': float(balance.get('used', 0)),
                        'total': float(balance.get('total', 0))
                    }
                    
        except Exception as e:
            print(f"Error fetching balances: {e}")
            self.balances = {}
            
    def _fetch_positions(self):
        try:
            positions_data = self.okx_client.fetch_positions()
            
            self.positions = {}
            for position in positions_data:
                symbol = position['symbol']
                self.positions[symbol] = {
                    'side': position.get('side'),
                    'size': float(position.get('contracts', 0)),
                    'notional': float(position.get('notional', 0)),
                    'entry_price': float(position.get('entryPrice', 0)),
                    'mark_price': float(position.get('markPrice', 0)),
                    'unrealized_pnl': float(position.get('unrealizedPnl', 0)),
                    'percentage': float(position.get('percentage', 0)),
                    'timestamp': position.get('timestamp')
                }
                
        except Exception as e:
            print(f"Error fetching positions: {e}")
            self.positions = {}
            
    def _fetch_open_orders(self):
        try:
            orders_data = self.okx_client.fetch_open_orders()
            
            self.open_orders = {}
            for order in orders_data:
                symbol = order['symbol']
                if symbol not in self.open_orders:
                    self.open_orders[symbol] = []
                    
                self.open_orders[symbol].append({
                    'id': order['id'],
                    'side': order['side'],
                    'amount': float(order['amount']),
                    'price': float(order['price']) if order['price'] else None,
                    'type': order['type'],
                    'status': order['status'],
                    'filled': float(order['filled']),
                    'remaining': float(order['remaining']),
                    'timestamp': order['timestamp']
                })
                
        except Exception as e:
            print(f"Error fetching open orders: {e}")
            self.open_orders = {}
            
    def _setup_fee_structure(self):
        try:
            trading_fees = self.okx_client.fetch_trading_fees()
            
            self.fee_structure = {
                'maker_fee': trading_fees.get('maker', 0.0002),
                'taker_fee': trading_fees.get('taker', 0.0005),
                'funding_interval': 8,
                'withdrawal_fees': {}
            }
            
        except Exception as e:
            print(f"Error setting up fee structure: {e}")
            self.fee_structure = {
                'maker_fee': 0.0002,
                'taker_fee': 0.0005,
                'funding_interval': 8,
                'withdrawal_fees': {}
            }
            
    def _initialize_analytics(self):
        self.execution_analytics = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'average_fill_time': 0,
            'average_slippage': 0,
            'implementation_shortfall': 0,
            'market_impact': 0,
            'timing_cost': 0,
            'opportunity_cost': 0
        }
        
        self.slippage_tracking = {
            'positive_slippage': [],
            'negative_slippage': [],
            'average_slippage': 0,
            'slippage_variance': 0,
            'worst_slippage': 0,
            'best_slippage': 0
        }
        
    def place_order(self, symbol: str, side: str, size: float, order_type: str = 'market', 
                   price: float = None, reduce_only: bool = False, time_in_force: str = 'GTC') -> Dict:
        try:
            if size <= 0:
                return {'success': False, 'error': 'Invalid order size'}
                
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': size,
                'reduceOnly': reduce_only
            }
            
            if order_type == 'limit' and price is not None:
                order_params['price'] = price
                
            if time_in_force != 'GTC':
                order_params['timeInForce'] = time_in_force
                
            start_time = time.time()
            
            if order_type == 'market':
                order_result = self.okx_client.create_market_order(**order_params)
            else:
                order_result = self.okx_client.create_limit_order(**order_params)
                
            end_time = time.time()
            
            if order_result and order_result.get('id'):
                filled_order = self._wait_for_fill(order_result['id'], symbol, timeout=30)
                
                execution_result = {
                    'success': True,
                    'order_id': order_result['id'],
                    'symbol': symbol,
                    'side': side,
                    'size': size,
                    'order_type': order_type,
                    'filled_size': float(filled_order.get('filled', 0)),
                    'average_price': float(filled_order.get('average', 0)),
                    'fees': float(filled_order.get('fee', {}).get('cost', 0)),
                    'execution_time': end_time - start_time,
                    'timestamp': datetime.now()
                }
                
                self._track_execution_metrics(execution_result)
                self._update_trade_history(execution_result)
                
                return execution_result
                
            else:
                return {'success': False, 'error': 'Order placement failed'}
                
        except Exception as e:
            print(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}
            
    def _wait_for_fill(self, order_id: str, symbol: str, timeout: int = 30) -> Dict:
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                order_status = self.okx_client.fetch_order(order_id, symbol)
                
                if order_status['status'] in ['closed', 'filled']:
                    return order_status
                elif order_status['status'] in ['canceled', 'rejected']:
                    break
                    
                time.sleep(0.1)
                
            return {}
            
        except Exception as e:
            print(f"Error waiting for order fill: {e}")
            return {}
            
    def _track_execution_metrics(self, execution_result: Dict):
        try:
            self.execution_analytics['total_trades'] += 1
            
            if execution_result['success']:
                self.execution_analytics['successful_trades'] += 1
                
                execution_time = execution_result.get('execution_time', 0)
                current_avg_time = self.execution_analytics['average_fill_time']
                total_trades = self.execution_analytics['successful_trades']
                
                self.execution_analytics['average_fill_time'] = (
                    (current_avg_time * (total_trades - 1) + execution_time) / total_trades
                )
                
                if 'slippage' in execution_result:
                    slippage = execution_result['slippage']
                    self.slippage_tracking['positive_slippage' if slippage > 0 else 'negative_slippage'].append(slippage)
                    
                    all_slippage = (self.slippage_tracking['positive_slippage'] + 
                                  self.slippage_tracking['negative_slippage'])
                    
                    if all_slippage:
                        self.slippage_tracking['average_slippage'] = np.mean(all_slippage)
                        self.slippage_tracking['slippage_variance'] = np.var(all_slippage)
                        self.slippage_tracking['worst_slippage'] = min(all_slippage)
                        self.slippage_tracking['best_slippage'] = max(all_slippage)
                        
            else:
                self.execution_analytics['failed_trades'] += 1
                
        except Exception as e:
            print(f"Error tracking execution metrics: {e}")
            
    def _update_trade_history(self, execution_result: Dict):
        try:
            trade_record = {
                'timestamp': execution_result['timestamp'],
                'order_id': execution_result['order_id'],
                'symbol': execution_result['symbol'],
                'side': execution_result['side'],
                'size': execution_result['filled_size'],
                'price': execution_result['average_price'],
                'fees': execution_result['fees'],
                'execution_time': execution_result['execution_time'],
                'pnl': 0
            }
            
            self.trade_history.append(trade_record)
            
            if len(self.trade_history) > 10000:
                self.trade_history = self.trade_history[-10000:]
                
        except Exception as e:
            print(f"Error updating trade history: {e}")
            
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        try:
            cancel_result = self.okx_client.cancel_order(order_id, symbol)
            
            if cancel_result:
                return {
                    'success': True,
                    'order_id': order_id,
                    'symbol': symbol,
                    'timestamp': datetime.now()
                }
            else:
                return {'success': False, 'error': 'Cancel order failed'}
                
        except Exception as e:
            print(f"Error canceling order: {e}")
            return {'success': False, 'error': str(e)}
            
    def cancel_all_orders(self, symbol: str = None) -> Dict:
        try:
            if symbol:
                cancel_result = self.okx_client.cancel_all_orders(symbol)
            else:
                cancel_result = self.okx_client.cancel_all_orders()
                
            canceled_count = len(cancel_result) if cancel_result else 0
            
            return {
                'success': True,
                'canceled_orders': canceled_count,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error canceling all orders: {e}")
            return {'success': False, 'error': str(e)}
            
    def close_position(self, symbol: str, size: float = None) -> Dict:
        try:
            current_position = self.positions.get(symbol, {})
            
            if not current_position or current_position.get('size', 0) == 0:
                return {'success': False, 'error': 'No position to close'}
                
            position_size = abs(current_position['size'])
            close_size = size if size is not None else position_size
            close_side = 'sell' if current_position['side'] == 'long' else 'buy'
            
            close_result = self.place_order(
                symbol=symbol,
                side=close_side,
                size=close_size,
                order_type='market',
                reduce_only=True
            )
            
            if close_result['success']:
                pnl = self._calculate_position_pnl(current_position, close_result['average_price'])
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'closed_size': close_result['filled_size'],
                    'close_price': close_result['average_price'],
                    'pnl': pnl,
                    'fees': close_result['fees'],
                    'timestamp': datetime.now()
                }
            else:
                return close_result
                
        except Exception as e:
            print(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}
            
    def close_all_positions(self) -> Dict:
        try:
            results = []
            
            for symbol, position in self.positions.items():
                if position.get('size', 0) != 0:
                    close_result = self.close_position(symbol)
                    results.append(close_result)
                    
            successful_closes = len([r for r in results if r.get('success')])
            total_pnl = sum([r.get('pnl', 0) for r in results if r.get('success')])
            
            return {
                'success': True,
                'closed_positions': successful_closes,
                'total_pnl': total_pnl,
                'results': results,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error closing all positions: {e}")
            return {'success': False, 'error': str(e)}
            
    def _calculate_position_pnl(self, position: Dict, exit_price: float) -> float:
        try:
            entry_price = position.get('entry_price', 0)
            position_size = position.get('size', 0)
            side = position.get('side', 'long')
            
            if side == 'long':
                pnl = (exit_price - entry_price) * position_size
            else:
                pnl = (entry_price - exit_price) * position_size
                
            return pnl
            
        except Exception as e:
            print(f"Error calculating position PnL: {e}")
            return 0
            
    def get_total_equity(self) -> float:
        try:
            total_balance = 0
            
            for currency, balance in self.balances.items():
                if currency in ['USDT', 'USDC', 'USD']:
                    total_balance += balance.get('total', 0)
                elif currency in ['BTC', 'ETH']:
                    price = self._get_asset_price_in_usd(currency)
                    total_balance += balance.get('total', 0) * price
                    
            unrealized_pnl = sum([pos.get('unrealized_pnl', 0) for pos in self.positions.values()])
            
            return total_balance + unrealized_pnl
            
        except Exception as e:
            print(f"Error calculating total equity: {e}")
            return 100000.0
            
    def _get_asset_price_in_usd(self, currency: str) -> float:
        try:
            if currency == 'USDT' or currency == 'USDC' or currency == 'USD':
                return 1.0
                
            symbol = f"{currency}-USDT-SWAP"
            ticker = self.okx_client.fetch_ticker(symbol)
            return float(ticker['last']) if ticker and ticker['last'] else 0
            
        except Exception as e:
            print(f"Error getting price for {currency}: {e}")
            return 0
            
    def get_portfolio_summary(self) -> Dict:
        try:
            total_equity = self.get_total_equity()
            total_exposure = sum([abs(pos.get('notional', 0)) for pos in self.positions.values()])
            net_exposure = sum([pos.get('notional', 0) for pos in self.positions.values()])
            
            unrealized_pnl = sum([pos.get('unrealized_pnl', 0) for pos in self.positions.values()])
            
            leverage = total_exposure / total_equity if total_equity > 0 else 0
            
            position_count = len([pos for pos in self.positions.values() if pos.get('size', 0) != 0])
            
            largest_position = max([abs(pos.get('notional', 0)) for pos in self.positions.values()]) if self.positions else 0
            largest_position_pct = largest_position / total_equity if total_equity > 0 else 0
            
            return {
                'total_equity': total_equity,
                'total_exposure': total_exposure,
                'net_exposure': net_exposure,
                'unrealized_pnl': unrealized_pnl,
                'leverage': leverage,
                'position_count': position_count,
                'largest_position_pct': largest_position_pct,
                'balances': self.balances,
                'positions': self.positions,
                'open_orders_count': sum([len(orders) for orders in self.open_orders.values()]),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error getting portfolio summary: {e}")
            return {}
            
    def calculate_performance_metrics(self, start_date: datetime = None) -> Dict:
        try:
            if not self.pnl_history:
                return {}
                
            pnl_series = pd.Series([pnl['total_pnl'] for pnl in self.pnl_history])
            equity_series = pd.Series([pnl['equity'] for pnl in self.pnl_history])
            
            if start_date:
                date_filter = pd.Series([pnl['timestamp'] for pnl in self.pnl_history]) >= start_date
                pnl_series = pnl_series[date_filter]
                equity_series = equity_series[date_filter]
                
            if len(equity_series) < 2:
                return {}
                
            returns = equity_series.pct_change().dropna()
            
            total_return = (equity_series.iloc[-1] / equity_series.iloc[0] - 1) * 100
            
            if len(returns) > 1:
                annual_return = ((1 + returns.mean()) ** 365) - 1
                volatility = returns.std() * np.sqrt(365)
                sharpe_ratio = annual_return / volatility if volatility > 0 else 0
                
                sortino_ratio = self._calculate_sortino_ratio(returns)
                calmar_ratio = self._calculate_calmar_ratio(returns, equity_series)
                
                max_drawdown = self._calculate_max_drawdown(equity_series)
                current_drawdown = self._calculate_current_drawdown(equity_series)
                
                win_rate = len(returns[returns > 0]) / len(returns) * 100
                profit_factor = self._calculate_profit_factor(returns)
                
            else:
                annual_return = 0
                volatility = 0
                sharpe_ratio = 0
                sortino_ratio = 0
                calmar_ratio = 0
                max_drawdown = 0
                current_drawdown = 0
                win_rate = 0
                profit_factor = 0
                
            return {
                'total_return': total_return,
                'annual_return': annual_return * 100,
                'volatility': volatility * 100,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'max_drawdown': max_drawdown * 100,
                'current_drawdown': current_drawdown * 100,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': len(self.trade_history),
                'avg_trade_pnl': np.mean([trade.get('pnl', 0) for trade in self.trade_history]) if self.trade_history else 0
            }
            
        except Exception as e:
            print(f"Error calculating performance metrics: {e}")
            return {}
            
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        try:
            downside_returns = returns[returns < 0]
            
            if len(downside_returns) == 0:
                return 0
                
            downside_deviation = downside_returns.std()
            
            if downside_deviation == 0:
                return 0
                
            return (returns.mean() * np.sqrt(365)) / (downside_deviation * np.sqrt(365))
            
        except Exception as e:
            return 0
            
    def _calculate_calmar_ratio(self, returns: pd.Series, equity_series: pd.Series) -> float:
        try:
            annual_return = ((1 + returns.mean()) ** 365) - 1
            max_drawdown = self._calculate_max_drawdown(equity_series)
            
            if max_drawdown == 0:
                return 0
                
            return annual_return / max_drawdown
            
        except Exception as e:
            return 0
            
    def _calculate_max_drawdown(self, equity_series: pd.Series) -> float:
        try:
            peak = equity_series.expanding().max()
            drawdown = (equity_series - peak) / peak
            return abs(drawdown.min())
            
        except Exception as e:
            return 0
            
    def _calculate_current_drawdown(self, equity_series: pd.Series) -> float:
        try:
            peak = equity_series.max()
            current_value = equity_series.iloc[-1]
            return (peak - current_value) / peak
            
        except Exception as e:
            return 0
            
    def _calculate_profit_factor(self, returns: pd.Series) -> float:
        try:
            gross_profits = returns[returns > 0].sum()
            gross_losses = abs(returns[returns < 0].sum())
            
            if gross_losses == 0:
                return 0
                
            return gross_profits / gross_losses
            
        except Exception as e:
            return 0
            
    def update_portfolio_state(self):
        try:
            self._fetch_balances()
            self._fetch_positions()
            self._fetch_open_orders()
            self._update_pnl_history()
            self._calculate_margin_metrics()
            self._update_funding_history()
            
        except Exception as e:
            print(f"Error updating portfolio state: {e}")
            
    def _update_pnl_history(self):
        try:
            current_equity = self.get_total_equity()
            unrealized_pnl = sum([pos.get('unrealized_pnl', 0) for pos in self.positions.values()])
            
            realized_pnl = 0
            if self.trade_history:
                recent_trades = [trade for trade in self.trade_history 
                               if trade['timestamp'].date() == datetime.now().date()]
                realized_pnl = sum([trade.get('pnl', 0) for trade in recent_trades])
                
            pnl_record = {
                'timestamp': datetime.now(),
                'equity': current_equity,
                'unrealized_pnl': unrealized_pnl,
                'realized_pnl': realized_pnl,
                'total_pnl': unrealized_pnl + realized_pnl
            }
            
            self.pnl_history.append(pnl_record)
            
            if len(self.pnl_history) > 10000:
                self.pnl_history = self.pnl_history[-10000:]
                
        except Exception as e:
            print(f"Error updating PnL history: {e}")
            
    def _calculate_margin_metrics(self):
        try:
            account_info = self.okx_client.fetch_account()
            
            self.margin_info = {
                'total_equity': float(account_info.get('totalWalletBalance', 0)),
                'available_balance': float(account_info.get('availableBalance', 0)),
                'used_margin': float(account_info.get('totalPositionInitialMargin', 0)),
                'maintenance_margin': float(account_info.get('totalMaintMargin', 0)),
                'margin_ratio': float(account_info.get('marginRatio', 0)),
                'max_withdraw': float(account_info.get('maxWithdrawAmount', 0))
            }
            
        except Exception as e:
            print(f"Error calculating margin metrics: {e}")
            self.margin_info = {}
            
    def _update_funding_history(self):
        try:
            for symbol in self.positions.keys():
                try:
                    funding_history = self.okx_client.fetch_funding_history(symbol, limit=10)
                    
                    for funding in funding_history:
                        funding_record = {
                            'symbol': symbol,
                            'timestamp': funding['timestamp'],
                            'amount': float(funding['amount']),
                            'rate': float(funding['info'].get('fundingRate', 0))
                        }
                        
                        self.funding_history.append(funding_record)
                        
                except Exception as e:
                    continue
                    
            if len(self.funding_history) > 1000:
                self.funding_history = self.funding_history[-1000:]
                
        except Exception as e:
            print(f"Error updating funding history: {e}")
            
    def optimize_portfolio_allocation(self, target_allocations: Dict, rebalance_threshold: float = 0.05) -> Dict:
        try:
            current_equity = self.get_total_equity()
            current_allocations = {}
            
            for symbol, position in self.positions.items():
                if position.get('size', 0) != 0:
                    allocation = abs(position.get('notional', 0)) / current_equity
                    current_allocations[symbol] = allocation
                    
            rebalance_trades = []
            
            for symbol, target_allocation in target_allocations.items():
                current_allocation = current_allocations.get(symbol, 0)
                allocation_diff = target_allocation - current_allocation
                
                if abs(allocation_diff) > rebalance_threshold:
                    target_notional = target_allocation * current_equity
                    current_notional = current_allocations.get(symbol, 0) * current_equity
                    trade_notional = target_notional - current_notional
                    
                    if trade_notional > 0:
                        side = 'buy'
                        size = abs(trade_notional)
                    else:
                        side = 'sell'
                        size = abs(trade_notional)
                        
                    rebalance_trades.append({
                        'symbol': symbol,
                        'side': side,
                        'size': size,
                        'reason': 'rebalance',
                        'current_allocation': current_allocation,
                        'target_allocation': target_allocation
                    })
                    
            return {
                'rebalance_required': len(rebalance_trades) > 0,
                'trades': rebalance_trades,
                'current_allocations': current_allocations,
                'target_allocations': target_allocations
            }
            
        except Exception as e:
            print(f"Error optimizing portfolio allocation: {e}")
            return {}
            
    def execute_rebalancing(self, rebalance_plan: Dict) -> Dict:
        try:
            if not rebalance_plan.get('rebalance_required'):
                return {'success': True, 'message': 'No rebalancing required'}
                
            execution_results = []
            
            for trade in rebalance_plan['trades']:
                result = self.place_order(
                    symbol=trade['symbol'],
                    side=trade['side'],
                    size=trade['size'],
                    order_type='market'
                )
                
                execution_results.append({
                    'trade': trade,
                    'result': result
                })
                
                time.sleep(0.1)
                
            successful_trades = len([r for r in execution_results if r['result'].get('success')])
            total_trades = len(execution_results)
            
            return {
                'success': True,
                'executed_trades': successful_trades,
                'total_trades': total_trades,
                'execution_results': execution_results,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error executing rebalancing: {e}")
            return {'success': False, 'error': str(e)}
            
    def calculate_transaction_costs(self, symbol: str, side: str, size: float) -> Dict:
        try:
            current_price = self._get_current_price(symbol)
            
            if current_price == 0:
                return {}
                
            notional_value = size * current_price
            
            trading_fee = notional_value * self.fee_structure['taker_fee']
            
            market_impact = self._estimate_market_impact(symbol, size)
            slippage_cost = notional_value * market_impact
            
            spread_cost = self._estimate_spread_cost(symbol, size)
            
            timing_cost = self._estimate_timing_cost(symbol, size)
            
            total_cost = trading_fee + slippage_cost + spread_cost + timing_cost
            
            return {
                'trading_fee': trading_fee,
                'market_impact': slippage_cost,
                'spread_cost': spread_cost,
                'timing_cost': timing_cost,
                'total_cost': total_cost,
                'cost_bps': (total_cost / notional_value) * 10000,
                'notional_value': notional_value
            }
            
        except Exception as e:
            print(f"Error calculating transaction costs: {e}")
            return {}
            
    def _get_current_price(self, symbol: str) -> float:
        try:
            ticker = self.okx_client.fetch_ticker(symbol)
            return float(ticker['last']) if ticker and ticker['last'] else 0
        except Exception as e:
            return 0
            
    def _estimate_market_impact(self, symbol: str, size: float) -> float:
        try:
            orderbook = self.okx_client.fetch_order_book(symbol, limit=20)
            
            cumulative_size = 0
            weighted_price = 0
            
            levels = orderbook['bids'] if size > 0 else orderbook['asks']
            
            for price, available_size in levels:
                take_size = min(available_size, size - cumulative_size)
                weighted_price += price * take_size
                cumulative_size += take_size
                
                if cumulative_size >= size:
                    break
                    
            if cumulative_size == 0:
                return 0.01
                
            avg_price = weighted_price / cumulative_size
            mid_price = (orderbook['bids'][0][0] + orderbook['asks'][0][0]) / 2
            
            market_impact = abs(avg_price - mid_price) / mid_price
            
            return market_impact
            
        except Exception as e:
            return 0.001
            
    def _estimate_spread_cost(self, symbol: str, size: float) -> float:
        try:
            ticker = self.okx_client.fetch_ticker(symbol)
            
            if not ticker or not ticker['bid'] or not ticker['ask']:
                return 0
                
            spread = ticker['ask'] - ticker['bid']
            mid_price = (ticker['ask'] + ticker['bid']) / 2
            
            spread_cost = (spread / 2) * size
            
            return spread_cost
            
        except Exception as e:
            return 0
            
    def _estimate_timing_cost(self, symbol: str, size: float) -> float:
        try:
            return size * 0.0001
        except Exception as e:
            return 0
            
    def generate_execution_report(self) -> Dict:
        try:
            total_trades = len(self.trade_history)
            
            if total_trades == 0:
                return {'message': 'No trades executed'}
                
            total_fees = sum([trade.get('fees', 0) for trade in self.trade_history])
            total_pnl = sum([trade.get('pnl', 0) for trade in self.trade_history])
            
            avg_execution_time = np.mean([trade.get('execution_time', 0) for trade in self.trade_history])
            
            successful_fills = len([trade for trade in self.trade_history if trade.get('size', 0) > 0])
            fill_rate = (successful_fills / total_trades) * 100 if total_trades > 0 else 0
            
            recent_trades = [trade for trade in self.trade_history 
                           if trade['timestamp'] >= datetime.now() - timedelta(days=1)]
            
            daily_volume = sum([trade.get('size', 0) * trade.get('price', 0) for trade in recent_trades])
            daily_trades = len(recent_trades)
            
            return {
                'total_trades': total_trades,
                'successful_fills': successful_fills,
                'fill_rate': fill_rate,
                'total_fees_paid': total_fees,
                'total_pnl': total_pnl,
                'avg_execution_time': avg_execution_time,
                'daily_volume': daily_volume,
                'daily_trades': daily_trades,
                'execution_analytics': self.execution_analytics,
                'slippage_tracking': self.slippage_tracking,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error generating execution report: {e}")
            return {}
            
    def get_balance(self, currency: str = 'USDT') -> float:
        try:
            balance = self.balances.get(currency, {})
            return balance.get('free', 0)
        except Exception as e:
            return 0
            
    def get_position_info(self, symbol: str) -> Dict:
        try:
            return self.positions.get(symbol, {})
        except Exception as e:
            return {}
            
    def get_open_orders_for_symbol(self, symbol: str) -> List[Dict]:
        try:
            return self.open_orders.get(symbol, [])
        except Exception as e:
            return []
            
    def calculate_portfolio_greeks(self) -> Dict:
        try:
            portfolio_delta = 0
            portfolio_gamma = 0
            portfolio_theta = 0
            portfolio_vega = 0
            
            for symbol, position in self.positions.items():
                if position.get('size', 0) != 0:
                    position_delta = self._calculate_position_delta(symbol, position)
                    position_gamma = self._calculate_position_gamma(symbol, position)
                    position_theta = self._calculate_position_theta(symbol, position)
                    position_vega = self._calculate_position_vega(symbol, position)
                    
                    portfolio_delta += position_delta
                    portfolio_gamma += position_gamma
                    portfolio_theta += position_theta
                    portfolio_vega += position_vega
                    
            return {
                'portfolio_delta': portfolio_delta,
                'portfolio_gamma': portfolio_gamma,
                'portfolio_theta': portfolio_theta,
                'portfolio_vega': portfolio_vega,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error calculating portfolio greeks: {e}")
            return {}
            
    def _calculate_position_delta(self, symbol: str, position: Dict) -> float:
        try:
            size = position.get('size', 0)
            side = position.get('side', 'long')
            
            delta = size if side == 'long' else -size
            
            return delta
            
        except Exception as e:
            return 0
            
    def _calculate_position_gamma(self, symbol: str, position: Dict) -> float:
        try:
            return 0
        except Exception as e:
            return 0
            
    def _calculate_position_theta(self, symbol: str, position: Dict) -> float:
        try:
            return 0
        except Exception as e:
            return 0
            
    def _calculate_position_vega(self, symbol: str, position: Dict) -> float:
        try:
            return 0
        except Exception as e:
            return 0
            
    def implement_stop_loss_strategy(self, symbol: str, stop_loss_pct: float = 0.02) -> Dict:
        try:
            position = self.positions.get(symbol, {})
            
            if not position or position.get('size', 0) == 0:
                return {'success': False, 'error': 'No position found'}
                
            entry_price = position.get('entry_price', 0)
            side = position.get('side', 'long')
            
            if side == 'long':
                stop_price = entry_price * (1 - stop_loss_pct)
                order_side = 'sell'
            else:
                stop_price = entry_price * (1 + stop_loss_pct)
                order_side = 'buy'
                
            stop_order = self.okx_client.create_order(
                symbol=symbol,
                type='stop',
                side=order_side,
                amount=abs(position['size']),
                price=stop_price,
                params={'stopPrice': stop_price, 'reduceOnly': True}
            )
            
            if stop_order and stop_order.get('id'):
                return {
                    'success': True,
                    'stop_order_id': stop_order['id'],
                    'stop_price': stop_price,
                    'symbol': symbol,
                    'side': order_side,
                    'size': abs(position['size'])
                }
            else:
                return {'success': False, 'error': 'Failed to place stop order'}
                
        except Exception as e:
            print(f"Error implementing stop loss: {e}")
            return {'success': False, 'error': str(e)}
            
    def implement_take_profit_strategy(self, symbol: str, take_profit_pct: float = 0.04) -> Dict:
        try:
            position = self.positions.get(symbol, {})
            
            if not position or position.get('size', 0) == 0:
                return {'success': False, 'error': 'No position found'}
                
            entry_price = position.get('entry_price', 0)
            side = position.get('side', 'long')
            
            if side == 'long':
                take_profit_price = entry_price * (1 + take_profit_pct)
                order_side = 'sell'
            else:
                take_profit_price = entry_price * (1 - take_profit_pct)
                order_side = 'buy'
                
            take_profit_order = self.okx_client.create_limit_order(
                symbol=symbol,
                side=order_side,
                amount=abs(position['size']),
                price=take_profit_price,
                params={'reduceOnly': True}
            )
            
            if take_profit_order and take_profit_order.get('id'):
                return {
                    'success': True,
                    'take_profit_order_id': take_profit_order['id'],
                    'take_profit_price': take_profit_price,
                    'symbol': symbol,
                    'side': order_side,
                    'size': abs(position['size'])
                }
            else:
                return {'success': False, 'error': 'Failed to place take profit order'}
                
        except Exception as e:
            print(f"Error implementing take profit: {e}")
            return {'success': False, 'error': str(e)}
            
    def monitor_funding_rates(self) -> Dict:
        try:
            funding_summary = {}
            
            for symbol in self.config['symbols']:
                try:
                    funding_rate = self.okx_client.fetch_funding_rate(symbol)
                    
                    position = self.positions.get(symbol, {})
                    position_size = position.get('size', 0)
                    
                    if position_size != 0:
                        estimated_funding = position_size * float(funding_rate['fundingRate'])
                        
                        funding_summary[symbol] = {
                            'funding_rate': float(funding_rate['fundingRate']),
                            'next_funding_time': funding_rate['fundingTimestamp'],
                            'position_size': position_size,
                            'estimated_funding_cost': estimated_funding,
                            'funding_direction': 'pay' if estimated_funding < 0 else 'receive'
                        }
                        
                except Exception as e:
                    continue
                    
            total_funding_cost = sum([f.get('estimated_funding_cost', 0) for f in funding_summary.values()])
            
            return {
                'funding_summary': funding_summary,
                'total_estimated_funding': total_funding_cost,
                'net_funding_direction': 'pay' if total_funding_cost < 0 else 'receive',
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error monitoring funding rates: {e}")
            return {}
            
    def generate_daily_report(self) -> Dict:
        try:
            portfolio_summary = self.get_portfolio_summary()
            performance_metrics = self.calculate_performance_metrics()
            execution_report = self.generate_execution_report()
            funding_report = self.monitor_funding_rates()
            
            return {
                'date': datetime.now().date(),
                'portfolio_summary': portfolio_summary,
                'performance_metrics': performance_metrics,
                'execution_report': execution_report,
                'funding_report': funding_report,
                'margin_info': self.margin_info,
                'risk_metrics': self._calculate_daily_risk_metrics(),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error generating daily report: {e}")
            return {}
            
    def _calculate_daily_risk_metrics(self) -> Dict:
        try:
            total_equity = self.get_total_equity()
            total_exposure = sum([abs(pos.get('notional', 0)) for pos in self.positions.values()])
            
            leverage = total_exposure / total_equity if total_equity > 0 else 0
            
            portfolio_var = self._calculate_portfolio_var()
            
            concentration_risk = self._calculate_concentration_risk()
            
            return {
                'leverage': leverage,
                'portfolio_var': portfolio_var,
                'concentration_risk': concentration_risk,
                'margin_ratio': self.margin_info.get('margin_ratio', 0),
                'available_margin': self.margin_info.get('available_balance', 0)
            }
            
        except Exception as e:
            return {}
            
    def _calculate_portfolio_var(self) -> float:
        try:
            return 5000.0
        except Exception as e:
            return 0
            
    def _calculate_concentration_risk(self) -> float:
        try:
            total_equity = self.get_total_equity()
            
            if total_equity == 0:
                return 0
                
            position_weights = []
            
            for position in self.positions.values():
                if position.get('size', 0) != 0:
                    weight = abs(position.get('notional', 0)) / total_equity
                    position_weights.append(weight)
                    
            if not position_weights:
                return 0
                
            herfindahl_index = sum([w**2 for w in position_weights])
            
            return herfindahl_index
            
        except Exception as e:
            return 0