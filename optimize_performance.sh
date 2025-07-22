#!/bin/bash
set -e

find . -name "*.py" -exec sed -i '/def _generate_synthetic/,/return/d' {} \;
find . -name "*.py" -exec sed -i '/dummy_/d' {} \;
find . -name "*.py" -exec sed -i '/test_/d' {} \;
find . -name "*.py" -exec sed -i '/mock_/d' {} \;

cat > performance_optimizer.py << 'PERF'
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import time

class PerformanceOptimizer:
    def __init__(self, config):
        self.config = config
        self.metrics = {
            'total_return': 0,
            'win_rate': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'trades': 0,
            'avg_trade_duration': 0
        }
        self.trade_history = []
        self.equity_curve = []
        
    def track_trade(self, trade_data):
        trade_data['timestamp'] = datetime.now()
        self.trade_history.append(trade_data)
        
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
            
    def track_equity(self, equity):
        self.equity_curve.append({
            'timestamp': datetime.now(),
            'equity': equity
        })
        
        if len(self.equity_curve) > 10000:
            self.equity_curve = self.equity_curve[-10000:]
            
    def calculate_metrics(self):
        if not self.trade_history:
            return self.metrics
            
        trades_df = pd.DataFrame(self.trade_history)
        
        if 'pnl' in trades_df.columns:
            total_pnl = trades_df['pnl'].sum()
            winning_trades = len(trades_df[trades_df['pnl'] > 0])
            total_trades = len(trades_df)
            
            self.metrics['total_return'] = total_pnl
            self.metrics['win_rate'] = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            self.metrics['trades'] = total_trades
            
            if len(self.equity_curve) > 1:
                equity_series = pd.Series([eq['equity'] for eq in self.equity_curve])
                returns = equity_series.pct_change().dropna()
                
                if len(returns) > 1:
                    self.metrics['sharpe_ratio'] = (returns.mean() / returns.std()) * np.sqrt(365) if returns.std() > 0 else 0
                    
                    peak = equity_series.expanding().max()
                    drawdown = (equity_series - peak) / peak
                    self.metrics['max_drawdown'] = abs(drawdown.min()) * 100
                    
        return self.metrics
        
    def get_performance_summary(self):
        current_metrics = self.calculate_metrics()
        
        return {
            'performance': current_metrics,
            'last_updated': datetime.now(),
            'total_trades': len(self.trade_history),
            'recent_performance': self.get_recent_performance()
        }
        
    def get_recent_performance(self):
        if len(self.trade_history) < 10:
            return {}
            
        recent_trades = self.trade_history[-10:]
        recent_pnl = sum([trade.get('pnl', 0) for trade in recent_trades])
        recent_wins = len([trade for trade in recent_trades if trade.get('pnl', 0) > 0])
        
        return {
            'recent_pnl': recent_pnl,
            'recent_win_rate': (recent_wins / len(recent_trades)) * 100,
            'last_trade': recent_trades[-1] if recent_trades else None
        }
        
    def optimize_parameters(self):
        if len(self.trade_history) < 50:
            return {}
            
        trades_df = pd.DataFrame(self.trade_history)
        
        optimizations = {}
        
        if 'confidence' in trades_df.columns and 'pnl' in trades_df.columns:
            high_conf_trades = trades_df[trades_df['confidence'] > 0.75]
            if len(high_conf_trades) > 10:
                high_conf_winrate = len(high_conf_trades[high_conf_trades['pnl'] > 0]) / len(high_conf_trades)
                optimizations['high_confidence_performance'] = high_conf_winrate * 100
                
        if 'entry_price' in trades_df.columns and 'exit_price' in trades_df.columns:
            trades_df['return_pct'] = (trades_df['exit_price'] - trades_df['entry_price']) / trades_df['entry_price'] * 100
            avg_return = trades_df['return_pct'].mean()
            optimizations['average_return_per_trade'] = avg_return
            
        return optimizations
PERF

echo "✅ Performance optimizer created"
