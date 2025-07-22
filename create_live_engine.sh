#!/bin/bash
set -e

cat > live_trading_engine.py << 'ENGINE'
import asyncio
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
from unified_core import UnifiedTradingCore
from real_data_feeds import RealDataFeeds
from production_risk_manager import ProductionRiskManager
from performance_optimizer import PerformanceOptimizer

class LiveTradingEngine:
    def __init__(self, config):
        self.config = config
        self.core = UnifiedTradingCore(config)
        self.data_feeds = RealDataFeeds(config)
        self.risk_manager = ProductionRiskManager(config)
        self.performance = PerformanceOptimizer(config)
        
        self.running = False
        self.positions = {}
        self.last_signals = {}
        
    async def initialize(self):
        try:
            if not self.core.initialize():
                return False
                
            await self.data_feeds.initialize()
            print("✅ Live trading engine initialized")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
            
    async def run_live_trading(self):
        print("🔴 STARTING LIVE TRADING")
        self.running = True
        
        try:
            while self.running:
                await self.trading_cycle()
                await asyncio.sleep(300)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.running = False
            
        finally:
            await self.data_feeds.close()
            
    async def trading_cycle(self):
        try:
            symbols = self.config['symbols']
            
            data_tasks = []
            for symbol in symbols:
                data_tasks.append(self.get_symbol_data(symbol))
                
            symbol_data = await asyncio.gather(*data_tasks)
            
            for i, symbol in enumerate(symbols):
                if symbol_data[i]:
                    await self.process_symbol(symbol, symbol_data[i])
                    
            self.manage_existing_positions()
            self.display_status()
            
        except Exception as e:
            print(f"❌ Trading cycle error: {e}")
            
    async def get_symbol_data(self, symbol):
        try:
            price_data = self.core.get_data(symbol, '1h', 100)
            if price_data.empty:
                return None
                
            comprehensive_data = await self.data_feeds.get_comprehensive_data([symbol])
            fear_greed = comprehensive_data.get('fear_greed', 50)
            
            return {
                'price_data': price_data,
                'fear_greed': fear_greed,
                'market_data': comprehensive_data.get(symbol, {}).get('market', {}),
                'whale_data': comprehensive_data.get(symbol, {}).get('whale', {}),
                'sentiment_data': comprehensive_data.get(symbol, {}).get('sentiment', {})
            }
            
        except Exception as e:
            print(f"❌ Data error for {symbol}: {e}")
            return None
            
    async def process_symbol(self, symbol, data):
        try:
            if symbol in self.positions:
                return
                
            signal = self.core.detect_vix_divergence(
                data['price_data'], 
                data['fear_greed']
            )
            
            if not signal:
                return
                
            signal = self.enhance_signal(signal, data)
            
            equity = self.get_current_equity()
            
            if self.risk_manager.validate_trade(symbol, signal, equity):
                position_size = self.risk_manager.calculate_position_size(signal, equity)
                
                success = await self.execute_trade(symbol, signal, position_size)
                
                if success:
                    self.last_signals[symbol] = signal
                    print(f"✅ {symbol} position opened - Confidence: {signal['confidence']:.2f}")
                    
        except Exception as e:
            print(f"❌ Processing error for {symbol}: {e}")
            
    def enhance_signal(self, signal, data):
        market_data = data.get('market_data', {})
        whale_data = data.get('whale_data', {})
        sentiment_data = data.get('sentiment_data', {})
        
        volume_factor = market_data.get('volume', 0) / 1000000
        whale_factor = min(whale_data.get('volume', 0) / 10000000, 1.0)
        sentiment_factor = abs(sentiment_data.get('sentiment', 0))
        
        confidence_boost = (volume_factor * 0.1 + whale_factor * 0.15 + sentiment_factor * 0.05)
        signal['confidence'] = min(signal['confidence'] + confidence_boost, 0.95)
        
        signal['enhanced'] = True
        signal['factors'] = {
            'volume': volume_factor,
            'whale': whale_factor,
            'sentiment': sentiment_factor
        }
        
        return signal
        
    async def execute_trade(self, symbol, signal, position_size):
        try:
            result = self.core.place_order(symbol, 'buy', position_size)
            
            if result['success']:
                position_data = {
                    'symbol': symbol,
                    'size': result['filled'],
                    'entry_price': result['price'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'timestamp': datetime.now(),
                    'signal': signal
                }
                
                self.positions[symbol] = position_data
                self.risk_manager.update_position(symbol, position_data)
                
                return True
                
        except Exception as e:
            print(f"❌ Execution error: {e}")
            
        return False
        
    def manage_existing_positions(self):
        for symbol, position in list(self.positions.items()):
            try:
                ticker = self.core.okx.fetch_ticker(symbol)
                current_price = ticker['last']
                
                should_close = False
                reason = ""
                
                if current_price <= position['stop_loss']:
                    should_close = True
                    reason = "Stop Loss"
                elif current_price >= position['take_profit']:
                    should_close = True
                    reason = "Take Profit"
                elif self.check_time_exit(position):
                    should_close = True
                    reason = "Time Exit"
                    
                if should_close:
                    self.close_position(symbol, current_price, reason)
                    
            except Exception as e:
                print(f"❌ Position management error: {e}")
                
    def check_time_exit(self, position):
        time_held = datetime.now() - position['timestamp']
        max_hold_time = timedelta(hours=self.config.get('max_hold_hours', 24))
        return time_held > max_hold_time
        
    def close_position(self, symbol, exit_price, reason):
        try:
            position = self.positions[symbol]
            
            result = self.core.place_order(symbol, 'sell', position['size'])
            
            if result['success']:
                pnl = (result['price'] - position['entry_price']) * position['size']
                
                trade_data = {
                    'symbol': symbol,
                    'entry_price': position['entry_price'],
                    'exit_price': result['price'],
                    'size': position['size'],
                    'pnl': pnl,
                    'reason': reason,
                    'duration': datetime.now() - position['timestamp'],
                    'confidence': position['signal']['confidence']
                }
                
                self.performance.track_trade(trade_data)
                self.risk_manager.update_daily_pnl(pnl)
                self.risk_manager.remove_position(symbol)
                
                del self.positions[symbol]
                
                print(f"🔄 {symbol} closed - {reason} - PnL: ${pnl:.2f}")
                
        except Exception as e:
            print(f"❌ Close position error: {e}")
            
    def get_current_equity(self):
        try:
            balance = self.core.okx.fetch_balance()
            return balance['USDT']['total']
        except:
            return 100000
            
    def display_status(self):
        equity = self.get_current_equity()
        self.performance.track_equity(equity)
        self.risk_manager.update_max_equity(equity)
        
        metrics = self.performance.get_performance_summary()
        risk_metrics = self.risk_manager.get_risk_metrics(equity)
        
        print(f"\n💰 Equity: ${equity:,.2f}")
        print(f"📊 Positions: {len(self.positions)}")
        print(f"📈 Total Return: ${metrics['performance']['total_return']:.2f}")
        print(f"🎯 Win Rate: {metrics['performance']['win_rate']:.1f}%")
        print(f"⚠️  Portfolio Heat: {risk_metrics['portfolio_heat']:.1%}")
        print(f"📉 Max Drawdown: {risk_metrics['drawdown']:.1%}")

async def main():
    import getpass
    
    print("🚀 SCHERMAN LIVE TRADING ENGINE")
    print("=" * 40)
    
    config = {
        'okx_api_key': getpass.getpass("OKX API Key: "),
        'okx_secret': getpass.getpass("OKX Secret: "),
        'okx_passphrase': getpass.getpass("OKX Passphrase: "),
        'sandbox': input("Sandbox mode? (y/n): ").lower() == 'y',
        'symbols': ['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP'],
        'whale_alert_key': input("Whale Alert API Key (optional): ").strip() or None,
        'news_api_key': input("News API Key (optional): ").strip() or None,
        'risk_per_trade': 0.02,
        'max_portfolio_risk': 0.15,
        'max_hold_hours': 24
    }
    
    engine = LiveTradingEngine(config)
    
    if await engine.initialize():
        await engine.run_live_trading()
    else:
        print("❌ Failed to initialize trading engine")

if __name__ == "__main__":
    asyncio.run(main())
ENGINE

echo "✅ Live trading engine created"
