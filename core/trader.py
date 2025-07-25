import os
import sys
from datetime import datetime
import time
from typing import Dict, List
import json

from scherman_vix import SchermanVIXCore, SchermanRiskManager
from data_manager import SchermanDataManager

class SchermanTrader:
    def __init__(self, config: Dict):
        self.config = config
        self.data_manager = SchermanDataManager(config)
        self.vix_core = SchermanVIXCore(config)
        self.risk_manager = SchermanRiskManager(config)
        
        self.positions = []
        self.trade_log = []
        self.portfolio_value = config.get('initial_capital', 10000)
        self.running = False
        
    def run(self):
        print("🎯 Starting Scherman VIX Divergence Trading System")
        print(f"💰 Initial Capital: ${self.portfolio_value:,.2f}")
        print(f"⚖️ Max Risk Per Trade: {self.config.get('max_risk_per_trade', 0.02)*100:.1f}%")
        print(f"🎯 Symbols: {self.config['symbols']}")
        print()
        
        self.running = True
        
        try:
            while self.running:
                cycle_start = time.time()
                
                print(f"🔄 {datetime.now().strftime('%H:%M:%S')} - Analyzing markets...")
                
                for symbol in self.config['symbols']:
                    self._process_symbol(symbol)
                
                self._update_portfolio()
                
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, self.config.get('check_interval', 300) - cycle_time)
                
                if sleep_time > 0:
                    print(f"⏳ Waiting {sleep_time:.1f}s for next check...")
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping trading system...")
            self.running = False
        
        print("📊 Final portfolio value: ${:.2f}".format(self.portfolio_value))
    
    def _process_symbol(self, symbol: str):
        try:
            price_data = self.data_manager.get_price_data(symbol)
            fear_greed = self.data_manager.get_fear_greed_index()
            
            if price_data is None or len(price_data) < 50:
                print(f"⚠️ Insufficient data for {symbol}")
                return
            
            signal = self.vix_core.analyze_divergence(price_data, fear_greed)
            
            if signal:
                print(f"📈 {symbol}: {signal['direction'].upper()} signal (confidence: {signal['confidence']:.1%})")
                
                if self.risk_manager.validate_signal(signal, self.portfolio_value, self.positions):
                    
                    position_size = self.risk_manager.calculate_position_size(
                        signal, self.portfolio_value, len(self.positions)
                    )
                    
                    if position_size > 0:
                        self._execute_signal(symbol, signal, position_size)
                    else:
                        print(f"   ❌ Position size too small")
                else:
                    print(f"   ❌ Signal rejected by risk manager")
            else:
                print(f"   ℹ️ {symbol}: No signal")
                
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
    
    def _execute_signal(self, symbol: str, signal: Dict, position_size: float):
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        
        risk_amount = abs(entry_price - stop_loss) * position_size / entry_price
        
        position = {
            'symbol': symbol,
            'direction': signal['direction'],
            'entry_price': entry_price,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': risk_amount,
            'confidence': signal['confidence'],
            'entry_time': datetime.now(),
            'signal': signal
        }
        
        self.positions.append(position)
        
        print(f"✅ TRADE EXECUTED:")
        print(f"   Symbol: {symbol}")
        print(f"   Direction: {signal['direction'].upper()}")
        print(f"   Size: ${position_size:,.2f}")
        print(f"   Entry: ${entry_price:.2f}")
        print(f"   Stop: ${stop_loss:.2f}")
        print(f"   Target: ${take_profit:.2f}")
        print(f"   Risk: ${risk_amount:.2f} ({risk_amount/self.portfolio_value*100:.1f}%)")
        print()
    
    def _update_portfolio(self):
        total_risk = sum([pos['risk_amount'] for pos in self.positions])
        risk_pct = total_risk / self.portfolio_value * 100
        
        if len(self.positions) > 0:
            print(f"📊 Portfolio: ${self.portfolio_value:,.2f} | Positions: {len(self.positions)} | Risk: {risk_pct:.1f}%")

def load_config():
    config = {
        'api_key': os.getenv('OKX_API_KEY', ''),
        'secret': os.getenv('OKX_SECRET', ''),
        'passphrase': os.getenv('OKX_PASSPHRASE', ''),
        'sandbox': os.getenv('SANDBOX', 'true').lower() == 'true',
        'symbols': ['BTC-USDT-SWAP', 'ETH-USDT-SWAP'],
        'initial_capital': 10000,
        'max_risk_per_trade': 0.02,
        'max_portfolio_risk': 0.10,
        'check_interval': 300,
        'min_confidence': 0.65
    }
    
    return config

def main():
    print("🏆 SCHERMAN VIX DIVERGENCE TRADING SYSTEM")
    print("=" * 50)
    
    config = load_config()
    trader = SchermanTrader(config)
    
    mode = "SANDBOX" if config['sandbox'] else "LIVE"
    print(f"🔧 Mode: {mode}")
    print(f"💰 Capital: ${config['initial_capital']:,.2f}")
    print(f"⚖️ Risk per trade: {config['max_risk_per_trade']*100:.1f}%")
    
    if not config['sandbox']:
        confirm = input("\n⚠️ LIVE TRADING MODE! Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("❌ Cancelled")
            return
    
    trader.run()

if __name__ == "__main__":
    main()
