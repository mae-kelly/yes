#!/usr/bin/env python3
"""
Scherman Crypto Strategy - Production Version
A live crypto trading system implementing VIX divergence methodology
"""

import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import ccxt
from datetime import datetime, timedelta
import asyncio
import time
import getpass
from typing import Dict, List

# Import core modules
from data_manager import CryptoDataManager
from risk_manager import RiskManager
from portfolio_manager import PortfolioManager
from execution_engine import ExecutionEngine
from monitoring import PerformanceMonitor
from vix_divergence_core import SchermanVIXDivergenceCore
from hybrid_signal_fusion import HybridSignalFusion
from ml_integration import RenaissanceMLIntegration

class SchermanCryptoStrategy:
    def __init__(self, config: Dict):
        self.config = config
        self.okx_client = self._init_okx_client()
        
        # Initialize core components
        self.data_manager = CryptoDataManager(config, self.okx_client)
        self.risk_manager = RiskManager(config)
        self.portfolio_manager = PortfolioManager(config, self.okx_client)
        self.execution_engine = ExecutionEngine(config, self.okx_client)
        self.monitor = PerformanceMonitor(config)
        self.vix_core = SchermanVIXDivergenceCore(config)
        self.signal_fusion = HybridSignalFusion(config)
        self.ml_integration = RenaissanceMLIntegration(config)
        
        # Trading state
        self.positions = {}
        self.trade_log = []
        self.running = False
        
    def _init_okx_client(self):
        return ccxt.okx({
            'apiKey': self.config['okx_api_key'],
            'secret': self.config['okx_secret'],
            'password': self.config['okx_passphrase'],
            'sandbox': self.config.get('sandbox', False),
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        
    def initialize(self):
        print("🚀 Initializing Scherman Crypto Strategy...")
        try:
            if not self.data_manager.initialize():
                return False
            self.monitor.setup_performance_tracking()
            self.monitor.setup_risk_monitoring()
            self.monitor.setup_execution_monitoring()
            print("✅ Strategy initialized successfully!")
            return True
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
            
    def run_live_trading(self):
        print("🔴 STARTING LIVE TRADING MODE")
        print("⚠️  WARNING: This will place real trades with real money!")
        
        confirmation = input("Type 'CONFIRM_LIVE_TRADING' to proceed: ")
        if confirmation != 'CONFIRM_LIVE_TRADING':
            print("❌ Live trading cancelled")
            return
            
        print("🟢 Live trading confirmed - Starting execution...")
        self.running = True
        
        try:
            while self.running:
                current_time = datetime.now()
                print(f"\n📊 {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Processing signals...")
                
                for symbol in self.config['symbols']:
                    try:
                        signal = self._generate_real_signal(symbol)
                        if signal and signal.get('direction') != 'hold':
                            execution_result = self._execute_real_signal(symbol, signal)
                            if execution_result.get('success'):
                                print(f"✅ Executed {symbol}: {signal['direction']} - Size: {execution_result['filled_size']}")
                            else:
                                print(f"❌ Failed {symbol}: {execution_result.get('error')}")
                    except Exception as e:
                        print(f"❌ Error processing {symbol}: {e}")
                
                self._update_performance_metrics()
                time.sleep(self.config.get('signal_interval', 300))
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down trading system...")
            self.running = False
            
    def _generate_real_signal(self, symbol: str) -> Dict:
        try:
            # Get market data
            data = self.data_manager.get_historical_data(symbol, self.config['timeframe'], 100)
            if data is None or len(data) < 50:
                return None
                
            market_data = self.data_manager.get_market_data(symbol)
            alt_data = self.data_manager.get_alternative_data(symbol)
            
            # Generate VIX divergence signal
            vix_signal = self.vix_core.detect_crypto_vix_divergence(
                data, 
                [alt_data.get('fear_greed_index', 50)]
            )
            
            # Generate ML prediction
            features_df = self._generate_features(data)
            ml_prediction = {}
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                ml_prediction = loop.run_until_complete(
                    self.ml_integration.predict_renaissance_signals(features_df, [symbol])
                )
                loop.close()
            except Exception as e:
                print(f"⚠️  ML prediction failed: {e}")
                ml_prediction = {}
            
            # Fuse signals
            fused_signal = self.signal_fusion.fuse_signals(
                vix_signal, 
                ml_prediction, 
                market_data
            )
            
            # Validate with risk manager
            if fused_signal and self.risk_manager.validate_signal(symbol, fused_signal, self.positions):
                return fused_signal
                
            return None
            
        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
            return None
            
    def _generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate basic technical features"""
        features = pd.DataFrame(index=data.index)
        
        # Price features
        features['returns'] = data['close'].pct_change()
        features['volatility'] = features['returns'].rolling(24).std()
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            features[f'sma_{period}'] = data['close'].rolling(period).mean()
            features[f'ema_{period}'] = data['close'].ewm(span=period).mean()
            
        # Volume features
        features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
        
        # Technical indicators
        features['rsi_14'] = self._calculate_rsi(data['close'], 14)
        features['bb_position'] = self._calculate_bb_position(data['close'])
        
        return features.fillna(0)
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
        
    def _calculate_bb_position(self, prices: pd.Series, period: int = 20) -> pd.Series:
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = sma + (2 * std)
        lower = sma - (2 * std)
        return (prices - lower) / (upper - lower)
        
    def _execute_real_signal(self, symbol: str, signal: Dict) -> Dict:
        try:
            equity = self.portfolio_manager.get_total_equity()
            position_size = self.risk_manager.calculate_position_size(symbol, signal, equity)
            
            if position_size <= 0:
                return {'success': False, 'error': 'Invalid position size'}
                
            side = 'buy' if signal['direction'] in ['long', 'strong_long'] else 'sell'
            
            result = self.execution_engine.place_order(
                symbol=symbol,
                side=side,
                size=position_size,
                order_type='market'
            )
            
            if result['success']:
                self._update_position(symbol, result, signal)
                self._log_trade(symbol, result, signal)
                
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _update_position(self, symbol: str, order_result: Dict, signal: Dict):
        if symbol not in self.positions:
            self.positions[symbol] = {
                'size': 0, 'side': None, 'entry_price': 0, 
                'stop_loss': None, 'take_profit': None
            }
            
        position = self.positions[symbol]
        position['size'] = order_result['filled_size']
        position['side'] = signal['direction']
        position['entry_price'] = order_result['average_price']
        position['stop_loss'] = signal.get('stop_loss')
        position['take_profit'] = signal.get('take_profit')
        
    def _log_trade(self, symbol: str, order_result: Dict, signal: Dict):
        self.trade_log.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': signal['direction'],
            'size': order_result['filled_size'],
            'price': order_result['average_price'],
            'confidence': signal['confidence'],
            'fees': order_result.get('fees', 0)
        })
        
    def _update_performance_metrics(self):
        try:
            total_equity = self.portfolio_manager.get_total_equity()
            print(f"💰 Portfolio Equity: ${total_equity:,.2f}")
        except Exception as e:
            print(f"Error updating performance: {e}")

def get_credentials():
    """Securely get user credentials"""
    print("🔐 Enter your OKX API credentials:")
    api_key = getpass.getpass("API Key: ").strip()
    secret = getpass.getpass("Secret: ").strip()
    passphrase = getpass.getpass("Passphrase: ").strip()
    
    sandbox = input("Use sandbox mode? (y/n): ").lower().strip() == 'y'
    
    return {
        'okx_api_key': api_key,
        'okx_secret': secret,
        'okx_passphrase': passphrase,
        'sandbox': sandbox
    }

def main():
    print("=" * 60)
    print("🏆 SCHERMAN CRYPTO STRATEGY - LIVE TRADING SYSTEM")
    print("=" * 60)
    print("📋 Features:")
    print("   ✅ VIX Divergence Methodology")
    print("   ✅ Machine Learning Integration")
    print("   ✅ Advanced Risk Management")
    print("   ✅ Real-time Data Feeds")
    print("   ✅ Professional Execution")
    print("=" * 60)
    
    credentials = get_credentials()
    
    config = {
        **credentials,
        'symbols': ['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP'],
        'timeframe': '1h',
        'signal_interval': 300,  # 5 minutes
        'risk_per_trade': 0.02,
        'max_portfolio_heat': 0.15,
        'min_signal_confidence': 0.65
    }
    
    strategy = SchermanCryptoStrategy(config)
    
    if strategy.initialize():
        print("\n🎯 Choose your mode:")
        print("1. Live Trading (Real Money)")
        print("2. Paper Trading (Simulation)")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            strategy.run_live_trading()
        elif choice == "2":
            print("📊 Paper trading mode not implemented yet")
            print("💡 Use sandbox mode for safe testing")
        else:
            print("👋 Goodbye!")
    else:
        print("❌ Failed to initialize strategy")

if __name__ == "__main__":
    main()
