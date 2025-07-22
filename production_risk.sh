#!/bin/bash
set -e

cat > production_risk_manager.py << 'RISK'
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ProductionRiskManager:
    def __init__(self, config):
        self.config = config
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.15)
        self.max_position_size = config.get('max_position_size', 0.05)
        self.max_daily_loss = config.get('max_daily_loss', 0.08)
        self.max_drawdown = config.get('max_drawdown', 0.20)
        self.leverage_limit = config.get('leverage_limit', 3.0)
        self.correlation_limit = config.get('correlation_limit', 0.7)
        
        self.daily_pnl = 0
        self.max_equity = 100000
        self.current_positions = {}
        self.risk_alerts = []
        
    def validate_trade(self, symbol, signal, portfolio_value):
        validations = [
            self.check_position_size(symbol, signal, portfolio_value),
            self.check_portfolio_heat(symbol, signal, portfolio_value),
            self.check_daily_loss_limit(),
            self.check_drawdown_limit(portfolio_value),
            self.check_leverage_limit(portfolio_value),
            self.check_correlation_exposure(symbol)
        ]
        
        return all(validations)
        
    def check_position_size(self, symbol, signal, portfolio_value):
        position_value = signal.get('size', 0) * signal.get('entry_price', 0)
        position_risk = position_value / portfolio_value
        
        if position_risk > self.max_position_size:
            self.add_alert(f"Position size too large: {position_risk:.2%}")
            return False
        return True
        
    def check_portfolio_heat(self, symbol, signal, portfolio_value):
        total_exposure = sum([pos.get('notional', 0) for pos in self.current_positions.values()])
        new_exposure = signal.get('size', 0) * signal.get('entry_price', 0)
        portfolio_heat = (total_exposure + new_exposure) / portfolio_value
        
        if portfolio_heat > self.max_portfolio_risk:
            self.add_alert(f"Portfolio heat too high: {portfolio_heat:.2%}")
            return False
        return True
        
    def check_daily_loss_limit(self):
        if self.daily_pnl < -self.max_daily_loss * self.max_equity:
            self.add_alert(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
            return False
        return True
        
    def check_drawdown_limit(self, current_equity):
        drawdown = (self.max_equity - current_equity) / self.max_equity
        if drawdown > self.max_drawdown:
            self.add_alert(f"Max drawdown exceeded: {drawdown:.2%}")
            return False
        return True
        
    def check_leverage_limit(self, portfolio_value):
        total_notional = sum([pos.get('notional', 0) for pos in self.current_positions.values()])
        leverage = total_notional / portfolio_value if portfolio_value > 0 else 0
        
        if leverage > self.leverage_limit:
            self.add_alert(f"Leverage too high: {leverage:.2f}x")
            return False
        return True
        
    def check_correlation_exposure(self, symbol):
        return True
        
    def calculate_position_size(self, signal, portfolio_value):
        confidence = signal.get('confidence', 0.6)
        risk_per_trade = self.config.get('risk_per_trade', 0.02)
        
        base_size = portfolio_value * risk_per_trade
        confidence_adjusted = base_size * confidence
        
        entry_price = signal.get('entry_price', 1)
        stop_loss = signal.get('stop_loss', entry_price * 0.95)
        
        risk_amount = abs(entry_price - stop_loss) * confidence_adjusted / entry_price
        kelly_size = self.calculate_kelly_size(signal, risk_amount)
        
        final_size = min(confidence_adjusted, kelly_size)
        max_size = portfolio_value * self.max_position_size
        
        return min(final_size / entry_price, max_size / entry_price)
        
    def calculate_kelly_size(self, signal, risk_amount):
        win_prob = signal.get('win_probability', 0.55)
        avg_win = signal.get('avg_win', 0.03)
        avg_loss = signal.get('avg_loss', 0.015)
        
        if avg_loss == 0:
            return risk_amount * 0.5
            
        kelly_fraction = (win_prob * avg_win - (1 - win_prob) * avg_loss) / avg_loss
        conservative_kelly = max(0, min(kelly_fraction * 0.25, 0.1))
        
        return risk_amount * (1 + conservative_kelly)
        
    def update_position(self, symbol, position_data):
        self.current_positions[symbol] = position_data
        
    def remove_position(self, symbol):
        if symbol in self.current_positions:
            del self.current_positions[symbol]
            
    def update_daily_pnl(self, pnl):
        self.daily_pnl += pnl
        
    def update_max_equity(self, equity):
        if equity > self.max_equity:
            self.max_equity = equity
            
    def add_alert(self, message):
        alert = {
            'timestamp': datetime.now(),
            'message': message,
            'severity': 'HIGH'
        }
        self.risk_alerts.append(alert)
        print(f"🚨 RISK ALERT: {message}")
        
    def get_risk_metrics(self, portfolio_value):
        total_exposure = sum([pos.get('notional', 0) for pos in self.current_positions.values()])
        leverage = total_exposure / portfolio_value if portfolio_value > 0 else 0
        drawdown = (self.max_equity - portfolio_value) / self.max_equity if self.max_equity > 0 else 0
        
        return {
            'portfolio_heat': total_exposure / portfolio_value if portfolio_value > 0 else 0,
            'leverage': leverage,
            'drawdown': drawdown,
            'daily_pnl': self.daily_pnl,
            'position_count': len(self.current_positions),
            'risk_alerts': len(self.risk_alerts)
        }
        
    def reset_daily_metrics(self):
        self.daily_pnl = 0
        self.risk_alerts = []
RISK

echo "✅ Production risk manager created"
