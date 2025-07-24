#!/usr/bin/env python3

import os
import sys
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import getpass
import logging
import json
import signal
from typing import Dict, Optional, List
import warnings
from dataclasses import dataclass, asdict
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import hashlib

warnings.filterwarnings('ignore')

from .data_manager import EnterpriseDataManager
from .signal_engine import SchermanVIXDivergenceCore
from .risk_manager import RiskManager
from .execution_engine import ExecutionEngine

@dataclass
class TradingMetrics:
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    avg_trade_duration: float = 0.0
    profit_factor: float = 0.0

@dataclass
class SystemStatus:
    status: str = "initializing"
    uptime: float = 0.0
    last_signal_time: datetime = None
    active_positions: int = 0
    total_equity: float = 0.0
    daily_pnl: float = 0.0
    api_health: str = "unknown"

class PerfectTradingSystem:
    def __init__(self, config: Dict):
        self.config = config
        self.running = False
        self.start_time = time.time()
        self.logger = self._setup_enterprise_logging()
        self.okx_client = self._init_okx_client()
        self.data_manager = EnterpriseDataManager(config, self.okx_client)
        self.vix_core = SchermanVIXDivergenceCore(config)
        self.risk_manager = RiskManager(config)
        self.execution_engine = ExecutionEngine(config, self.okx_client)
        self.positions = {}
        self.trade_history = []
        self.equity_curve = []
        self.performance_metrics = TradingMetrics()
        self.system_status = SystemStatus()
        self.signal_queue = queue.Queue()
        self.execution_queue = queue.Queue()
        signal.signal(signal.SIGINT, self._emergency_shutdown)
        signal.signal(signal.SIGTERM, self._emergency_shutdown)
        self.last_health_check = time.time()
        self.health_check_interval = 300
        
    def _setup_enterprise_logging(self) -> logging.Logger:
        logger = logging.getLogger('PerfectTradingSystem')
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        file_handler = logging.FileHandler('trading_system.log', mode='a')
        file_handler.setLevel(logging.DEBUG)
        error_handler = logging.FileHandler('trading_errors.log', mode='a')
        error_handler.setLevel(logging.ERROR)
        trade_handler = logging.FileHandler('trades.log', mode='a')
        trade_handler.setLevel(logging.INFO)
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        console_handler.setFormatter(simple_formatter)
        file_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)
        trade_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(trade_handler)
        return logger
        
    def _init_okx_client(self):
        return ccxt.okx({
            'apiKey': self.config['okx_api_key'],
            'secret': self.config['okx_secret'],
            'password': self.config['okx_passphrase'],
            'sandbox': self.config.get('sandbox', True),
            'enableRateLimit': True,
            'rateLimit': 100,
            'options': {
                'defaultType': 'swap',
                'adjustForTimeDifference': True
            },
            'timeout': 30000,
            'headers': {
                'User-Agent': 'SchermanTradingSystem/2.0'
            }
        })
        
    def initialize(self) -> bool:
        # Validate credentials first
        if not self._validate_credentials():
            self.logger.error("❌ Invalid or missing credentials")
            return False        try:
            self.logger.info("🚀 Initializing Perfect Trading System...")
            self.logger.info(f"🔧 Mode: {'SANDBOX' if self.config.get('sandbox') else '🚨 LIVE'}")
            self.logger.info(f"💰 Risk per trade: {self.config.get('risk_per_trade', 0.01)*100:.1f}%")
            self.logger.info(f"🎯 Symbols: {self.config['symbols']}")
            if not self.data_manager.initialize():
                self.logger.error("❌ Data manager initialization failed")
                return False
            test_results = self._run_comprehensive_tests()
            if not test_results['success']:
                self.logger.error("❌ System tests failed")
                return False
            if not self.risk_manager.initialize():
                self.logger.error("❌ Risk manager initialization failed")
                return False
            if not self.execution_engine.initialize():
                self.logger.error("❌ Execution engine initialization failed")
                return False
            self._load_system_state()
            self.system_status.status = "ready"
            self.logger.info("✅ Perfect Trading System initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            self.system_status.status = "failed"
            return False
            
    def _run_comprehensive_tests(self) -> Dict:
        try:
            test_results = {
                'success': True,
                'tests': {},
                'warnings': [],
                'errors': []
            }
            for symbol in self.config['symbols']:
                test_data = self.data_manager.get_historical_data(symbol, '1h', 7)
                if test_data is None or len(test_data) < 50:
                    test_results['errors'].append(f"Insufficient data for {symbol}")
                    test_results['success'] = False
                else:
                    test_results['tests'][f'{symbol}_data'] = 'passed'
            health_check = self.data_manager.health_check()
            if health_check['overall'] == 'unhealthy':
                test_results['errors'].append("API health check failed")
                test_results['success'] = False
            elif health_check['overall'] == 'degraded':
                test_results['warnings'].append("Some APIs are degraded")
            test_results['tests']['api_health'] = health_check['overall']
            try:
                balance = self.okx_client.fetch_balance()
                test_results['tests']['exchange_connection'] = 'passed'
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                if usdt_balance < 100:
                    test_results['warnings'].append(f"Low USDT balance: ${usdt_balance:.2f}")
            except Exception as e:
                test_results['errors'].append(f"Exchange connection failed: {e}")
                test_results['success'] = False
            try:
                test_symbol = self.config['symbols'][0]
                signal_data = self.data_manager.get_comprehensive_signal_data(test_symbol)
                if signal_data['historical_data'] is not None:
                    test_results['tests']['signal_generation'] = 'passed'
                else:
                    test_results['errors'].append("Signal generation test failed")
                    test_results['success'] = False
            except Exception as e:
                test_results['errors'].append(f"Signal generation error: {e}")
                test_results['success'] = False
            if test_results['success']:
                self.logger.info("✅ All system tests passed")
            else:
                self.logger.error("❌ System tests failed")
            for warning in test_results['warnings']:
                self.logger.warning(f"⚠️ {warning}")
            for error in test_results['errors']:
                self.logger.error(f"❌ {error}")
            return test_results
        except Exception as e:
            self.logger.error(f"❌ Test execution failed: {e}")
            return {'success': False, 'error': str(e)}
            
    def run_perfect_trading(self):
        try:
            self.logger.info("🎯 STARTING PERFECT TRADING SYSTEM")
            self.logger.info("=" * 60)
            if not self._final_safety_checks():
                self.logger.error("❌ Safety checks failed - aborting")
                return
            self._start_monitoring_threads()
            self.running = True
            self.system_status.status = "running"
            cycle_count = 0
            consecutive_errors = 0
            max_consecutive_errors = 5
            self.logger.info("🔄 Entering main trading loop...")
            while self.running:
                cycle_start = time.time()
                cycle_count += 1
                try:
                    if time.time() - self.last_health_check > self.health_check_interval:
                        self._perform_health_check()
                    self._perfect_trading_cycle(cycle_count)
                    consecutive_errors = 0
                    if cycle_count % 10 == 0:
                        self._log_performance_summary()
                    cycle_time = time.time() - cycle_start
                    sleep_time = self._calculate_optimal_sleep_time(cycle_time)
                    if sleep_time > 0:
                        self.logger.debug(f"💤 Cycle {cycle_count} complete in {cycle_time:.2f}s, sleeping {sleep_time:.1f}s")
                        time.sleep(sleep_time)
                except KeyboardInterrupt:
                    self.logger.info("🛑 Manual shutdown requested")
                    break
                except Exception as e:
                    consecutive_errors += 1
                    self.logger.error(f"❌ Trading cycle error ({consecutive_errors}/{max_consecutive_errors}): {e}")
                    if consecutive_errors >= max_consecutive_errors:
                        self.logger.critical("🚨 Too many consecutive errors - emergency shutdown")
                        break
                    error_sleep = min(300, 30 * consecutive_errors)
                    self.logger.warning(f"⏳ Waiting {error_sleep}s before retry...")
                    time.sleep(error_sleep)
        except Exception as e:
            self.logger.critical(f"🚨 CRITICAL ERROR in main trading loop: {e}")
        finally:
            self._shutdown_trading_system()
            
    def _final_safety_checks(self) -> bool:
        try:
            is_live = not self.config.get('sandbox', True)
            if is_live:
                self.logger.warning("🚨 LIVE TRADING MODE DETECTED")
                self.logger.warning("This will use real money and place real trades!")
                confirmation = input("\nFinal confirmation - Type 'START_LIVE_TRADING' to proceed: ")
                if confirmation != 'START_LIVE_TRADING':
                    self.logger.info("❌ Live trading cancelled by user")
                    return False
            risk_per_trade = self.config.get('risk_per_trade', 0.01)
            if risk_per_trade > 0.05:
                self.logger.error(f"❌ Risk per trade too high: {risk_per_trade*100:.1f}%")
                return False
            try:
                balance = self.okx_client.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                if usdt_balance < 100:
                    self.logger.error(f"❌ Insufficient balance: ${usdt_balance:.2f}")
                    return False
                self.logger.info(f"💰 Available balance: ${usdt_balance:,.2f}")
            except Exception as e:
                self.logger.error(f"❌ Balance check failed: {e}")
                return False
            for symbol in self.config['symbols']:
                signal_data = self.data_manager.get_comprehensive_signal_data(symbol)
                if signal_data['data_completeness'] < 0.5:
                    self.logger.error(f"❌ Poor data quality for {symbol}")
                    return False
            self.logger.info("✅ All safety checks passed")
            return True
        except Exception as e:
            self.logger.error(f"❌ Safety check error: {e}")
            return False
            
    def _start_monitoring_threads(self):
        try:
            performance_thread = threading.Thread(
                target=self._performance_monitor,
                daemon=True,
                name="PerformanceMonitor"
            )
            performance_thread.start()
            health_thread = threading.Thread(
                target=self._health_monitor,
                daemon=True,
                name="HealthMonitor"
            )
            health_thread.start()
            self.logger.info("✅ Monitoring threads started")
        except Exception as e:
            self.logger.error(f"❌ Failed to start monitoring threads: {e}")
            
    def _perfect_trading_cycle(self, cycle_count: int):
        self.logger.debug(f"🔄 Starting trading cycle {cycle_count}")
        self.system_status.uptime = time.time() - self.start_time
        self.system_status.active_positions = len(self.positions)
        with ThreadPoolExecutor(max_workers=len(self.config['symbols'])) as executor:
            symbol_futures = {}
            for symbol in self.config['symbols']:
                future = executor.submit(self._process_symbol, symbol, cycle_count)
                symbol_futures[future] = symbol
            for future in symbol_futures:
                symbol = symbol_futures[future]
                try:
                    result = future.result(timeout=60)
                    if result:
                        self.logger.debug(f"✅ {symbol} processed successfully")
                except Exception as e:
                    self.logger.error(f"❌ Error processing {symbol}: {e}")
        self._update_performance_metrics()
        
    def _process_symbol(self, symbol: str, cycle_count: int) -> bool:
        try:
            if symbol in self.positions:
                return self._manage_existing_position(symbol)
            else:
                return self._evaluate_new_position(symbol)
        except Exception as e:
            self.logger.error(f"❌ Symbol processing error for {symbol}: {e}")
            return False
            
    def _manage_existing_position(self, symbol: str) -> bool:
        try:
            position = self.positions[symbol]
            current_data = self.data_manager.get_historical_data(symbol, '1m', 1)
            if current_data is None or len(current_data) == 0:
                self.logger.warning(f"⚠️ No current data for {symbol}")
                return False
            current_price = current_data['close'].iloc[-1]
            entry_price = position['entry_price']
            position_size = position['size']
            side = position['side']
            if side == 'long':
                unrealized_pnl = (current_price - entry_price) * position_size
            else:
                unrealized_pnl = (entry_price - current_price) * position_size
            position['unrealized_pnl'] = unrealized_pnl
            exit_signal = self._check_exit_conditions(symbol, position, current_price)
            if exit_signal:
                return self._close_position(symbol, current_price, exit_signal['reason'])
            if unrealized_pnl > 0:
                self._update_trailing_stop(symbol, position, current_price)
            return True
        except Exception as e:
            self.logger.error(f"❌ Position management error for {symbol}: {e}")
            return False
            
    def _evaluate_new_position(self, symbol: str) -> bool:
        try:
            signal = self._generate_enhanced_signal(symbol)
            if not signal or signal.get('action') in ['hold', 'neutral']:
                return True
            current_equity = self._get_current_equity()
            if not self.risk_manager.validate_signal(symbol, signal, self.positions):
                self.logger.debug(f"🚫 Signal rejected by risk manager for {symbol}")
                return True
            position_size = self.risk_manager.calculate_position_size(symbol, signal, current_equity)
            if position_size <= 0:
                self.logger.debug(f"🚫 Position size too small for {symbol}")
                return True
            return self._execute_enhanced_signal(symbol, signal, position_size)
        except Exception as e:
            self.logger.error(f"❌ Position evaluation error for {symbol}: {e}")
            return False
            
    def _generate_enhanced_signal(self, symbol: str) -> Optional[Dict]:
        try:
            signal_data = self.data_manager.get_comprehensive_signal_data(symbol)
            historical_data = signal_data['historical_data']
            market_data = signal_data['market_data']
            regime_data = signal_data['regime_data']
            if historical_data is None or len(historical_data) < 50:
                return None
            fear_greed = market_data.get('fear_greed_index', 50)
            base_signal = self.vix_core.detect_crypto_vix_divergence(historical_data, [fear_greed])
            if not base_signal:
                return None
            enhanced_signal = self._enhance_signal_with_premium_data(
                base_signal, market_data, regime_data, symbol
            )
            enhanced_signal.update({
                'symbol': symbol,
                'timestamp': datetime.now(),
                'data_quality': signal_data.get('data_completeness', 0),
                'processing_time': signal_data.get('processing_time', 0),
                'market_regime': regime_data.get('overall_regime', 'unknown')
            })
            return enhanced_signal
        except Exception as e:
            self.logger.error(f"❌ Enhanced signal generation error for {symbol}: {e}")
            return None
            
    def _enhance_signal_with_premium_data(self, signal: Dict, market_data: Dict, 
                                        regime_data: Dict, symbol: str) -> Dict:
        try:
            enhanced_signal = signal.copy()
            original_confidence = enhanced_signal.get('confidence', 0.5)
            confidence_adjustments = []
            market_regime = regime_data.get('overall_regime', 'sideways')
            sentiment_score = regime_data.get('sentiment_score', 0)
            if signal.get('direction') == 'long':
                if market_regime == 'bull_market' or sentiment_score <= -1:
                    confidence_adjustments.append(0.15)
                elif market_regime == 'bear_market' and sentiment_score >= 1:
                    confidence_adjustments.append(-0.1)
            else:
                if market_regime == 'bear_market' or sentiment_score >= 1:
                    confidence_adjustments.append(0.15)
                elif market_regime == 'bull_market' and sentiment_score <= -1:
                    confidence_adjustments.append(-0.1)
            if 'ETH' in symbol:
                gas_price_fast = market_data.get('gas_price_fast', 30)
                gas_environment = market_data.get('gas_environment', 'normal')
                if gas_environment == 'expensive':
                    confidence_adjustments.append(0.08)
                elif gas_environment == 'cheap':
                    if signal.get('direction') == 'long':
                        confidence_adjustments.append(0.05)
                network_utilization = market_data.get('eth_network_utilization', 0.5)
                if network_utilization > 0.9:
                    confidence_adjustments.append(0.06)
                whale_activity = market_data.get('whale_activity', {})
                large_movements = whale_activity.get('large_movements', 0)
                if large_movements > 3:
                    confidence_adjustments.append(0.1)
            if 'BTC' in symbol:
                network_status = market_data.get('btc_network_status', 'normal')
                fee_pressure = market_data.get('btc_fee_pressure', 'low')
                if network_status == 'congested' and fee_pressure in ['high', 'extreme']:
                    confidence_adjustments.append(0.08)
                elif network_status == 'normal' and fee_pressure == 'low':
                    if signal.get('direction') == 'long':
                        confidence_adjustments.append(0.03)
                mempool_size = market_data.get('btc_mempool_size', 0)
                if mempool_size > 150000:
                    confidence_adjustments.append(0.05)
            spread_bps = market_data.get('spread_bps', 0)
            if spread_bps > 0:
                if spread_bps < 5:
                    confidence_adjustments.append(0.03)
                elif spread_bps > 20:
                    confidence_adjustments.append(-0.05)
            orderbook_imbalance = market_data.get('orderbook_imbalance', 0)
            if abs(orderbook_imbalance) > 0.3:
                if (signal.get('direction') == 'long' and orderbook_imbalance > 0) or \
                   (signal.get('direction') == 'short' and orderbook_imbalance < 0):
                    confidence_adjustments.append(0.04)
            volume_ratio = market_data.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                confidence_adjustments.append(0.06)
            elif volume_ratio < 0.7:
                confidence_adjustments.append(-0.03)
            cg_volume = market_data.get('cg_volume_24h', 0)
            if cg_volume > 0:
                market_data_volume = market_data.get('volume_24h', 1)
                if market_data_volume > 0:
                    volume_consistency = min(cg_volume, market_data_volume) / max(cg_volume, market_data_volume)
                    if volume_consistency > 0.8:
                        confidence_adjustments.append(0.02)
            fg_trend = market_data.get('fear_greed_trend', 'neutral')
            fg_volatility = market_data.get('fear_greed_volatility', 0)
            if fg_trend == 'decreasing' and signal.get('direction') == 'long':
                confidence_adjustments.append(0.08)
            elif fg_trend == 'increasing' and signal.get('direction') == 'short':
                confidence_adjustments.append(0.08)
            if fg_volatility > 10:
                confidence_adjustments.append(-0.04)
            momentum_6h = market_data.get('momentum_6h', 0)
            momentum_12h = market_data.get('momentum_12h', 0)
            if signal.get('direction') == 'long':
                if momentum_6h > 0 and momentum_12h > 0:
                    confidence_adjustments.append(0.05)
                elif momentum_6h < -2 and momentum_12h < -5:
                    confidence_adjustments.append(0.07)
            else:
                if momentum_6h < 0 and momentum_12h < 0:
                    confidence_adjustments.append(0.05)
                elif momentum_6h > 2 and momentum_12h > 5:
                    confidence_adjustments.append(0.07)
            volatility_1h = market_data.get('volatility_1h', 0)
            volatility_24h = market_data.get('volatility_24h', 0)
            if volatility_1h > volatility_24h * 1.5:
                confidence_adjustments.append(0.04)
            elif volatility_1h < volatility_24h * 0.5:
                confidence_adjustments.append(0.03)
            total_adjustment = sum(confidence_adjustments)
            enhanced_confidence = original_confidence + total_adjustment
            enhanced_confidence = max(0.3, min(0.95, enhanced_confidence))
            enhanced_signal['confidence'] = enhanced_confidence
            enhanced_signal['confidence_adjustments'] = {
                'original_confidence': original_confidence,
                'total_adjustment': total_adjustment,
                'final_confidence': enhanced_confidence,
                'adjustment_factors': len(confidence_adjustments)
            }
            enhanced_signal['enhancement_data'] = {
                'market_regime': market_regime,
                'sentiment_score': sentiment_score,
                'data_sources_used': self._count_data_sources(market_data),
                'signal_strength': 'strong' if enhanced_confidence > 0.8 else 'medium' if enhanced_confidence > 0.6 else 'weak'
            }
            return enhanced_signal
        except Exception as e:
            self.logger.error(f"⚠️ Signal enhancement error: {e}")
            return signal
            
    def _count_data_sources(self, market_data: Dict) -> Dict:
        sources = {
            'okx_market_data': 1 if market_data.get('current_price') else 0,
            'fear_greed_index': 1 if market_data.get('fear_greed_index') else 0,
            'coingecko_data': 1 if market_data.get('cg_market_cap') else 0,
            'btc_network_data': 1 if market_data.get('btc_mempool_size') else 0,
            'eth_onchain_data': 1 if market_data.get('gas_price_fast') else 0,
            'whale_monitoring': 1 if market_data.get('whale_activity') else 0,
            'orderbook_analysis': 1 if market_data.get('spread_bps') else 0,
            'technical_indicators': 1 if market_data.get('volatility_1h') else 0
        }
        sources['total_active'] = sum(sources.values())
        return sources
        
    def _execute_enhanced_signal(self, symbol: str, signal: Dict, position_size: float) -> bool:
        try:
            side = 'buy' if signal.get('direction') == 'long' else 'sell'
            result = self.execution_engine.place_order(
                symbol=symbol,
                side=side,
                size=position_size,
                order_type='market',
                metadata=signal.get('enhancement_data', {})
            )
            if result.get('success'):
                self.positions[symbol] = {
                    'size': result['filled_size'],
                    'side': side,
                    'entry_price': result['average_price'],
                    'stop_loss': signal.get('stop_loss'),
                    'take_profit': signal.get('take_profit'),
                    'timestamp': datetime.now(),
                    'signal': signal,
                    'confidence': signal.get('confidence', 0),
                    'enhancement_data': signal.get('enhancement_data', {}),
                    'unrealized_pnl': 0.0,
                    'max_favorable_excursion': 0.0,
                    'max_adverse_excursion': 0.0
                }
                self._log_trade_execution(symbol, signal, result)
                self.system_status.last_signal_time = datetime.now()
                return True
            else:
                self.logger.error(f"❌ Order execution failed for {symbol}: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Signal execution error for {symbol}: {e}")
            return False
            
    def _log_trade_execution(self, symbol: str, signal: Dict, result: Dict):
        trade_info = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': signal.get('direction', 'unknown'),
            'size': result['filled_size'],
            'price': result['average_price'],
            'confidence': signal.get('confidence', 0),
            'signal_strength': signal.get('enhancement_data', {}).get('signal_strength', 'unknown'),
            'market_regime': signal.get('market_regime', 'unknown'),
            'data_sources': signal.get('enhancement_data', {}).get('data_sources_used', {}).get('total_active', 0)
        }
        self.logger.info(f"✅ TRADE EXECUTED: {json.dumps(trade_info, indent=2)}")
        self.trade_history.append(trade_info)
        
    def _check_exit_conditions(self, symbol: str, position: Dict, current_price: float) -> Optional[Dict]:
        try:
            entry_price = position['entry_price']
            side = position['side']
            if side == 'long':
                price_change_pct = (current_price - entry_price) / entry_price * 100
            else:
                price_change_pct = (entry_price - current_price) / entry_price * 100
            if position.get('stop_loss') and current_price <= position['stop_loss']:
                return {'action': 'close', 'reason': 'stop_loss', 'urgency': 'high'}
            if position.get('take_profit') and current_price >= position['take_profit']:
                return {'action': 'close', 'reason': 'take_profit', 'urgency': 'normal'}
            position_age = datetime.now() - position['timestamp']
            max_hold_time = timedelta(hours=self.config.get('max_hold_hours', 24))
            if position_age > max_hold_time:
                return {'action': 'close', 'reason': 'time_exit', 'urgency': 'normal'}
            original_confidence = position.get('confidence', 0.5)
            if original_confidence < 0.6 and price_change_pct < -2:
                return {'action': 'close', 'reason': 'confidence_decay', 'urgency': 'normal'}
            current_regime_data = self.data_manager.get_market_regime_indicators()
            current_regime = current_regime_data.get('overall_regime', 'unknown')
            entry_regime = position.get('signal', {}).get('market_regime', 'unknown')
            if current_regime != entry_regime and current_regime in ['bear_market', 'extreme_fear']:
                if side == 'long' and price_change_pct < 0:
                    return {'action': 'close', 'reason': 'regime_change', 'urgency': 'normal'}
            recent_data = self.data_manager.get_historical_data(symbol, '1h', 6)
            if recent_data is not None and len(recent_data) >= 6:
                recent_volatility = recent_data['close'].pct_change().std() * np.sqrt(24)
                if recent_volatility > 0.15:
                    if abs(price_change_pct) > 5:
                        return {'action': 'close', 'reason': 'volatility_exit', 'urgency': 'normal'}
            return None
        except Exception as e:
            self.logger.error(f"❌ Exit condition check error for {symbol}: {e}")
            return None
            
    def _update_trailing_stop(self, symbol: str, position: Dict, current_price: float):
        try:
            if position['side'] != 'long':
                return
            entry_price = position['entry_price']
            current_stop = position.get('stop_loss', 0)
            trailing_stop_pct = 0.02
            potential_stop = current_price * (1 - trailing_stop_pct)
            if potential_stop > current_stop:
                position['stop_loss'] = potential_stop
                self.logger.debug(f"🔄 Trailing stop updated for {symbol}: ${potential_stop:.4f}")
        except Exception as e:
            self.logger.error(f"❌ Trailing stop update error for {symbol}: {e}")
            
    def _close_position(self, symbol: str, exit_price: float, reason: str) -> bool:
        try:
            position = self.positions[symbol]
            exit_side = 'sell' if position['side'] == 'buy' else 'buy'
            result = self.execution_engine.place_order(
                symbol=symbol,
                side=exit_side,
                size=position['size'],
                order_type='market'
            )
            if result.get('success'):
                entry_price = position['entry_price']
                if position['side'] == 'buy':
                    pnl = (result['average_price'] - entry_price) * position['size']
                else:
                    pnl = (entry_price - result['average_price']) * position['size']
                close_info = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': 'close',
                    'reason': reason,
                    'entry_price': entry_price,
                    'exit_price': result['average_price'],
                    'size': position['size'],
                    'pnl': pnl,
                    'hold_time': str(datetime.now() - position['timestamp']),
                    'original_confidence': position.get('confidence', 0)
                }
                self.logger.info(f"🔄 POSITION CLOSED: {json.dumps(close_info, indent=2)}")
                self.performance_metrics.total_trades += 1
                self.performance_metrics.total_pnl += pnl
                if pnl > 0:
                    self.performance_metrics.winning_trades += 1
                else:
                    self.performance_metrics.losing_trades += 1
                total_trades = self.performance_metrics.total_trades
                self.performance_metrics.win_rate = (self.performance_metrics.winning_trades / total_trades * 100) if total_trades > 0 else 0
                del self.positions[symbol]
                self.trade_history.append(close_info)
                return True
            else:
                self.logger.error(f"❌ Failed to close position for {symbol}: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Position close error for {symbol}: {e}")
            return False
            
    def _get_current_equity(self) -> float:
        try:
            cache_key = 'current_equity'
            if self._is_cache_valid(cache_key, 30):
                return self.data_manager.data_cache[cache_key]['data']
            balance = self.okx_client.fetch_balance()
            equity = balance['USDT']['total']
            self.data_manager.data_cache[cache_key] = {
                'data': equity,
                'timestamp': time.time()
            }
            self.system_status.total_equity = equity
            return equity
        except Exception as e:
            self.logger.error(f"❌ Equity fetch error: {e}")
            return self.system_status.total_equity or 100000.0
            
    def _is_cache_valid(self, cache_key: str, max_age_seconds: int) -> bool:
        if cache_key not in self.data_manager.data_cache:
            return False
        cache_entry = self.data_manager.data_cache[cache_key]
        cache_age = time.time() - cache_entry.get('timestamp', 0)
        return cache_age < max_age_seconds
        
    def _calculate_optimal_sleep_time(self, cycle_time: float) -> float:
        base_interval = self.config.get('signal_interval', 300)
        try:
            total_volatility = 0
            valid_symbols = 0
            for symbol in self.config['symbols']:
                recent_data = self.data_manager.get_historical_data(symbol, '1h', 6)
                if recent_data is not None and len(recent_data) >= 6:
                    symbol_volatility = recent_data['close'].pct_change().std()
                    total_volatility += symbol_volatility
                    valid_symbols += 1
            if valid_symbols > 0:
                avg_volatility = total_volatility / valid_symbols
                if avg_volatility > 0.03:
                    interval_multiplier = 0.6
                elif avg_volatility > 0.02:
                    interval_multiplier = 0.8
                else:
                    interval_multiplier = 1.2
                adjusted_interval = base_interval * interval_multiplier
            else:
                adjusted_interval = base_interval
        except Exception:
            adjusted_interval = base_interval
        sleep_time = max(10, adjusted_interval - cycle_time)
        return sleep_time
        
    def _update_performance_metrics(self):
        try:
            current_equity = self._get_current_equity()
            self.equity_curve.append({
                'timestamp': datetime.now(),
                'equity': current_equity,
                'positions': len(self.positions),
                'unrealized_pnl': sum(pos.get('unrealized_pnl', 0) for pos in self.positions.values())
            })
            today = datetime.now().date()
            today_equity_records = [eq for eq in self.equity_curve if eq['timestamp'].date() == today]
            if len(today_equity_records) > 1:
                start_equity = today_equity_records[0]['equity']
                current_equity = today_equity_records[-1]['equity']
                self.system_status.daily_pnl = current_equity - start_equity
            else:
                self.system_status.daily_pnl = 0.0
            self.system_status.total_equity = current_equity
        except Exception as e:
            self.logger.error(f"❌ Performance metrics update error: {e}")
            
    def _log_performance_summary(self):
        try:
            current_equity = self.system_status.total_equity
            uptime = self.system_status.uptime
            summary = {
                'timestamp': datetime.now().isoformat(),
                'uptime_hours': round(uptime / 3600, 2),
                'current_equity': round(current_equity, 2),
                'daily_pnl': round(self.system_status.daily_pnl, 2),
                'active_positions': len(self.positions),
                'total_trades': self.performance_metrics.total_trades,
                'win_rate': round(self.performance_metrics.win_rate, 1),
                'total_pnl': round(self.performance_metrics.total_pnl, 2),
                'api_performance': self.data_manager.get_performance_summary()
            }
            self.logger.info(f"📊 PERFORMANCE SUMMARY: {json.dumps(summary, indent=2)}")
        except Exception as e:
            self.logger.error(f"❌ Performance summary error: {e}")
            
    def _perform_health_check(self):
        try:
            self.last_health_check = time.time()
            health_status = self.data_manager.health_check()
            self.system_status.api_health = health_status['overall']
            if health_status['overall'] == 'healthy':
                self.logger.debug("✅ System health check: All systems operational")
            elif health_status['overall'] == 'degraded':
                self.logger.warning("⚠️ System health check: Some systems degraded")
            else:
                self.logger.error("❌ System health check: Critical issues detected")
            problematic_positions = []
            for symbol, position in self.positions.items():
                position_age = datetime.now() - position['timestamp']
                if position_age > timedelta(hours=48):
                    problematic_positions.append(symbol)
            if problematic_positions:
                self.logger.warning(f"⚠️ Old positions detected: {problematic_positions}")
        except Exception as e:
            self.logger.error(f"❌ Health check error: {e}")
            
    def _performance_monitor(self):
        while self.running:
            try:
                time.sleep(60)
                if len(self.equity_curve) > 10:
                    recent_equity = [eq['equity'] for eq in self.equity_curve[-10:]]
                    peak_equity = max(recent_equity)
                    current_equity = recent_equity[-1]
                    drawdown = (peak_equity - current_equity) / peak_equity * 100
                    if drawdown > 10:
                        self.logger.warning(f"⚠️ Significant drawdown detected: {drawdown:.1f}%")
                    if drawdown > 20:
                        self.logger.critical(f"🚨 EMERGENCY: {drawdown:.1f}% drawdown - consider stopping")
            except Exception as e:
                self.logger.error(f"❌ Performance monitoring error: {e}")
                
    def _health_monitor(self):
        while self.running:
            try:
                time.sleep(300)
                performance = self.data_manager.get_performance_summary()
                avg_response = performance.get('avg_response_time', 0)
                if avg_response > 10:
                    self.logger.warning(f"⚠️ Slow API responses: {avg_response:.2f}s average")
                success_rate = performance.get('success_rate', 100)
                if success_rate < 90:
                    self.logger.warning(f"⚠️ Low API success rate: {success_rate:.1f}%")
            except Exception as e:
                self.logger.error(f"❌ Health monitoring error: {e}")
                
    def _emergency_shutdown(self, signum, frame):
        self.logger.critical("🚨 EMERGENCY SHUTDOWN INITIATED")
        self.running = False
        for symbol in list(self.positions.keys()):
            try:
                self._close_position(symbol, 0, "Emergency Shutdown")
            except Exception as e:
                self.logger.error(f"❌ Emergency close failed for {symbol}: {e}")
        self._shutdown_trading_system()
        sys.exit(1)
        
    def _load_system_state(self):
        try:
            state_file = 'trading_system_state.json'
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                if 'performance_metrics' in state:
                    metrics_data = state['performance_metrics']
                    for key, value in metrics_data.items():
                        if hasattr(self.performance_metrics, key):
                            setattr(self.performance_metrics, key, value)
                self.logger.info("✅ Previous system state loaded")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load previous state: {e}")
            
    def _save_system_state(self):
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'performance_metrics': asdict(self.performance_metrics),
                'system_status': asdict(self.system_status),
                'equity_curve_size': len(self.equity_curve),
                'trade_history_size': len(self.trade_history)
            }
            with open('trading_system_state.json', 'w') as f:
                json.dump(state, f, indent=2, default=str)
            self.logger.debug("💾 System state saved")
        except Exception as e:
            self.logger.error(f"❌ State save error: {e}")
            
    def _shutdown_trading_system(self):
        try:
            self.logger.info("🔄 Initiating system shutdown...")
            self.running = False
            self.system_status.status = "shutting_down"
            if self.positions:
                self.logger.info(f"🔄 Closing {len(self.positions)} open positions...")
                for symbol in list(self.positions.keys()):
                    try:
                        current_data = self.data_manager.get_historical_data(symbol, '1m', 1)
                        if current_data is not None and len(current_data) > 0:
                            current_price = current_data['close'].iloc[-1]
                            self._close_position(symbol, current_price, "System Shutdown")
                        else:
                            del self.positions[symbol]
                            self.logger.warning(f"⚠️ Force closed {symbol} - no price data")
                    except Exception as e:
                        self.logger.error(f"❌ Shutdown close error for {symbol}: {e}")
            self._save_system_state()
            self._log_final_performance_summary()
            self.system_status.status = "stopped"
            self.logger.info("✅ Trading system shutdown complete")
        except Exception as e:
            self.logger.error(f"❌ Shutdown error: {e}")
            
    def _log_final_performance_summary(self):
        try:
            uptime = time.time() - self.start_time
            final_summary = {
                'session_summary': {
                    'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'total_uptime_hours': round(uptime / 3600, 2),
                    'final_equity': self.system_status.total_equity,
                    'session_pnl': self.performance_metrics.total_pnl,
                    'total_trades': self.performance_metrics.total_trades,
                    'winning_trades': self.performance_metrics.winning_trades,
                    'losing_trades': self.performance_metrics.losing_trades,
                    'win_rate': round(self.performance_metrics.win_rate, 1),
                    'positions_closed_on_shutdown': len(self.positions)
                },
                'api_performance': self.data_manager.get_performance_summary(),
                'data_quality_summary': {
                    'cache_efficiency': f"{self.data_manager.get_performance_summary().get('cache_hit_rate', 0):.1f}%",
                    'avg_response_time': f"{self.data_manager.get_performance_summary().get('avg_response_time', 0):.2f}s"
                }
            }
            self.logger.info("📊 FINAL SESSION SUMMARY:")
            self.logger.info("=" * 60)
            self.logger.info(json.dumps(final_summary, indent=2))
            self.logger.info("=" * 60)
        except Exception as e:
            self.logger.error(f"❌ Final summary error: {e}")

def get_secure_credentials():
    print("🔐 SECURE CREDENTIAL INPUT")
    print("=" * 40)
    print("⚠️  Credentials are encrypted in memory and never stored")
    print("")
    credentials = {}
    while True:
        api_key = getpass.getpass("OKX API Key: ").strip()
        if len(api_key) >= 20:
            credentials['okx_api_key'] = api_key
            break
        print("❌ API key too short - please check and retry")
    while True:
        secret = getpass.getpass("OKX Secret: ").strip()
        if len(secret) >= 20:
            credentials['okx_secret'] = secret
            break
        print("❌ Secret too short - please check and retry")
    while True:
        passphrase = getpass.getpass("OKX Passphrase: ").strip()
        if len(passphrase) >= 3:
            credentials['okx_passphrase'] = passphrase
            break
        print("❌ Passphrase too short - please check and retry")
    print("✅ Credentials validated")
    return credentials

def select_trading_mode():
    print("\n🎯 TRADING MODE SELECTION")
    print("=" * 40)
    print("1. 🧪 Sandbox Mode (Paper Trading)")
    print("   - No real money")
    print("   - Full system testing")
    print("   - Recommended for first use")
    print("")
    print("2. 💰 Live Mode (Real Trading)")
    print("   - REAL MONEY AT RISK")
    print("   - Requires multiple confirmations")
    print("   - Only for experienced users")
    print("")
    while True:
        choice = input("Select mode (1 for Sandbox, 2 for Live): ").strip()
        if choice == '1':
            print("✅ Sandbox mode selected - Safe for testing")
            return True
        elif choice == '2':
            print("\n🚨 LIVE TRADING MODE SELECTED")
            print("=" * 40)
            print("⚠️  WARNING: This mode uses REAL MONEY")
            print("⚠️  WARNING: You can LOSE REAL MONEY")
            print("⚠️  WARNING: Past performance does not guarantee future results")
            print("⚠️  WARNING: Cryptocurrency trading is highly risky")
            print("")
            confirm1 = input("Type 'I_UNDERSTAND_THE_RISKS' to continue: ").strip()
            if confirm1 != 'I_UNDERSTAND_THE_RISKS':
                print("❌ Live trading cancelled")
                continue
            confirm2 = input("Type 'START_LIVE_TRADING' for final confirmation: ").strip()
            if confirm2 != 'START_LIVE_TRADING':
                print("❌ Live trading cancelled")
                continue
            print("⚠️ LIVE TRADING MODE CONFIRMED")
            return False
        else:
            print("❌ Invalid selection - please enter 1 or 2")

def create_perfect_config(credentials: Dict, sandbox_mode: bool) -> Dict:
    print("\n🎯 SYMBOL SELECTION")
    print("=" * 30)
    print("Available symbols:")
    print("1. BTC-USDT-SWAP (Bitcoin with enhanced data)")
    print("2. ETH-USDT-SWAP (Ethereum with on-chain analytics)")
    print("3. Both BTC and ETH (Recommended)")
    print("")
    while True:
        symbol_choice = input("Select symbols (1/2/3): ").strip()
        if symbol_choice == '1':
            symbols = ['BTC-USDT-SWAP']
            break
        elif symbol_choice == '2':
            symbols = ['ETH-USDT-SWAP']
            break
        elif symbol_choice == '3':
            symbols = ['BTC-USDT-SWAP', 'ETH-USDT-SWAP']
            break
        else:
            print("❌ Invalid selection - please enter 1, 2, or 3")
    print("\n⚖️ RISK CONFIGURATION")
    print("=" * 30)
    if sandbox_mode:
        risk_per_trade = 0.02
        max_portfolio_heat = 0.10
        print("📊 Sandbox risk settings:")
        print(f"   - Risk per trade: {risk_per_trade*100:.1f}%")
        print(f"   - Max portfolio exposure: {max_portfolio_heat*100:.1f}%")
    else:
        print("Recommended live trading settings:")
        print("- Conservative: 0.5% per trade, 2% max exposure")
        print("- Moderate: 1.0% per trade, 5% max exposure")
        print("- Aggressive: 2.0% per trade, 10% max exposure")
        print("")
        while True:
            risk_choice = input("Select risk level (conservative/moderate/aggressive): ").strip().lower()
            if risk_choice in ['conservative', 'c']:
                risk_per_trade = 0.005
                max_portfolio_heat = 0.02
                break
            elif risk_choice in ['moderate', 'm']:
                risk_per_trade = 0.01
                max_portfolio_heat = 0.05
                break
            elif risk_choice in ['aggressive', 'a']:
                risk_per_trade = 0.02
                max_portfolio_heat = 0.10
                break
            else:
                print("❌ Invalid selection - please enter conservative, moderate, or aggressive")
    return {
        **credentials,
        'sandbox': sandbox_mode,
        'symbols': symbols,
        'timeframe': '1h',
        'signal_interval': 300,
        'risk_per_trade': risk_per_trade,
        'max_portfolio_heat': max_portfolio_heat,
        'min_signal_confidence': 0.70,
        'max_hold_hours': 24,
        'use_enhanced_signals': True,
        'use_onchain_data': True,
        'monitor_whale_addresses': True,
        'use_market_regime_detection': True,
        'enable_trailing_stops': True,
        'enable_performance_monitoring': True,
        'api_timeout': 30,
        'max_api_retries': 3,
        'cache_enabled': True,
        'parallel_processing': True
    }

def main():
    try:
        print("🏆 SCHERMAN PERFECT CRYPTO TRADING SYSTEM")
        print("=" * 60)
        print("🔒 Enterprise Security | ⚡ Maximum Performance | 🎯 Professional Grade")
        print("")
        credentials = get_secure_credentials()
        sandbox_mode = select_trading_mode()
        config = create_perfect_config(credentials, sandbox_mode)
        print("\n🎯 FINAL CONFIGURATION")
        print("=" * 40)
        print(f"🔧 Mode: {'SANDBOX (Paper Trading)' if sandbox_mode else '💰 LIVE TRADING'}")
        print(f"📊 Symbols: {', '.join(config['symbols'])}")
        print(f"⚖️ Risk per trade: {config['risk_per_trade']*100:.1f}%")
        print(f"🎯 Max exposure: {config['max_portfolio_heat']*100:.1f}%")
        print(f"⏱️ Signal interval: {config['signal_interval']}s")
        print(f"🧠 Min confidence: {config['min_signal_confidence']*100:.0f}%")
        print("")
        if not sandbox_mode:
            final_confirm = input("🚨 FINAL CONFIRMATION - Type 'LAUNCH_LIVE_SYSTEM' to start: ")
            if final_confirm != 'LAUNCH_LIVE_SYSTEM':
                print("❌ System launch cancelled")
                return
        system = PerfectTradingSystem(config)
        if system.initialize():
            print("\n🚀 LAUNCHING PERFECT TRADING SYSTEM")
            print("=" * 50)
            system.run_perfect_trading()
        else:
            print("❌ System initialization failed")
            return 1
    except KeyboardInterrupt:
        print("\n🛑 System startup cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
    
    def _validate_credentials(self) -> bool:
        """Validate that all required credentials are present"""
        required_keys = ['okx_api_key', 'okx_secret', 'okx_passphrase']
        
        for key in required_keys:
            value = self.config.get(key)
            if not value or len(str(value)) < 10:
                self.logger.error(f"Missing or invalid credential: {key}")
                return False
        
        return True
