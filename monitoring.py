import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import json
import warnings
warnings.filterwarnings('ignore')

class PerformanceMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.performance_data = {}
        self.risk_metrics = {}
        self.execution_metrics = {}
        self.alerts = []
        self.thresholds = {'max_drawdown': config.get('max_drawdown', 0.15), 'min_sharpe': config.get('min_sharpe', 1.0), 'max_var': config.get('max_var', 0.05), 'min_win_rate': config.get('min_win_rate', 0.45), 'max_correlation': config.get('max_correlation', 0.8)}
        self.monitoring_intervals = {'performance': 300, 'risk': 60, 'execution': 30, 'alerts': 10}
        self.data_retention = {'days': 365, 'max_records': 100000}
        self.notification_settings = {'email': config.get('email_alerts', False), 'webhook': config.get('webhook_url', None), 'slack': config.get('slack_webhook', None)}
        self.performance_history = []
        self.risk_history = []
        self.execution_history = []
        self.position_history = []
        self.pnl_history = []
        self.drawdown_history = []
        self.volatility_history = []
        self.correlation_history = []
        self.volume_history = []
        self.latency_history = []
        self.error_history = []
        self.system_health = {'cpu_usage': 0, 'memory_usage': 0, 'disk_usage': 0, 'network_latency': 0, 'api_status': True}
        self.strategy_metrics = {'total_return': 0, 'annual_return': 0, 'sharpe_ratio': 0, 'sortino_ratio': 0, 'calmar_ratio': 0, 'max_drawdown': 0, 'win_rate': 0, 'profit_factor': 0, 'total_trades': 0, 'avg_trade_duration': 0}
        self.benchmark_metrics = {'benchmark_return': 0, 'alpha': 0, 'beta': 0, 'information_ratio': 0, 'tracking_error': 0, 'upside_capture': 0, 'downside_capture': 0}
        self.real_time_metrics = {}
        self.dashboard_data = {}
        
    def setup_performance_tracking(self):
        try:
            self.performance_data = {'equity_curve': [], 'daily_returns': [], 'monthly_returns': [], 'annual_returns': [], 'rolling_sharpe': [], 'rolling_volatility': [], 'rolling_drawdown': []}
            print("✅ Performance tracking initialized")
        except Exception as e:
            print(f"❌ Error setting up performance tracking: {e}")
            
    def setup_risk_monitoring(self):
        try:
            self.risk_metrics = {'portfolio_var': 0, 'portfolio_cvar': 0, 'maximum_drawdown': 0, 'current_drawdown': 0, 'portfolio_volatility': 0, 'portfolio_beta': 0, 'concentration_risk': 0, 'leverage_ratio': 0}
            print("✅ Risk monitoring initialized")
        except Exception as e:
            print(f"❌ Error setting up risk monitoring: {e}")
            
    def setup_execution_monitoring(self):
        try:
            self.execution_metrics = {'total_orders': 0, 'successful_orders': 0, 'failed_orders': 0, 'average_latency': 0, 'average_slippage': 0, 'fill_rate': 0, 'execution_cost': 0, 'market_impact': 0}
            print("✅ Execution monitoring initialized")
        except Exception as e:
            print(f"❌ Error setting up execution monitoring: {e}")
            
    def update_performance_metrics(self, equity: float, returns: float, positions: Dict, trades: List):
        try:
            current_time = datetime.now()
            self.performance_data['equity_curve'].append({'timestamp': current_time, 'equity': equity})
            self.performance_data['daily_returns'].append({'timestamp': current_time, 'return': returns})
            if len(self.performance_data['equity_curve']) > 1:
                equity_series = pd.Series([eq['equity'] for eq in self.performance_data['equity_curve']])
                returns_series = equity_series.pct_change().dropna()
                if len(returns_series) > 30:
                    rolling_sharpe = self._calculate_rolling_sharpe(returns_series, window=30)
                    rolling_vol = returns_series.rolling(30).std() * np.sqrt(365)
                    rolling_dd = self._calculate_rolling_drawdown(equity_series, window=30)
                    self.performance_data['rolling_sharpe'].append({'timestamp': current_time, 'sharpe': rolling_sharpe})
                    self.performance_data['rolling_volatility'].append({'timestamp': current_time, 'volatility': rolling_vol.iloc[-1]})
                    self.performance_data['rolling_drawdown'].append({'timestamp': current_time, 'drawdown': rolling_dd})
            self._update_strategy_metrics(equity, returns, trades)
            self._check_performance_alerts(equity, returns)
        except Exception as e:
            print(f"❌ Error updating performance metrics: {e}")
            
    def _calculate_rolling_sharpe(self, returns: pd.Series, window: int = 30) -> float:
        try:
            if len(returns) < window:
                return 0.0
            rolling_mean = returns.rolling(window).mean().iloc[-1]
            rolling_std = returns.rolling(window).std().iloc[-1]
            if rolling_std == 0:
                return 0.0
            return (rolling_mean / rolling_std) * np.sqrt(365)
        except Exception as e:
            return 0.0
            
    def _calculate_rolling_drawdown(self, equity: pd.Series, window: int = 30) -> float:
        try:
            if len(equity) < window:
                return 0.0
            rolling_equity = equity.rolling(window)
            peak = rolling_equity.max().iloc[-1]
            current = equity.iloc[-1]
            if peak == 0:
                return 0.0
            return (peak - current) / peak
        except Exception as e:
            return 0.0
            
    def _update_strategy_metrics(self, equity: float, returns: float, trades: List):
        try:
            if len(self.performance_data['equity_curve']) > 1:
                initial_equity = self.performance_data['equity_curve'][0]['equity']
                self.strategy_metrics['total_return'] = (equity / initial_equity - 1) * 100
                
            returns_list = [ret['return'] for ret in self.performance_data['daily_returns'] if ret['return'] != 0]
            if len(returns_list) > 1:
                returns_array = np.array(returns_list)
                annual_return = (np.mean(returns_array) * 365) * 100
                volatility = np.std(returns_array) * np.sqrt(365)
                self.strategy_metrics['annual_return'] = annual_return
                self.strategy_metrics['sharpe_ratio'] = (annual_return / 100) / volatility if volatility > 0 else 0
                downside_returns = returns_array[returns_array < 0]
                if len(downside_returns) > 0:
                    downside_vol = np.std(downside_returns) * np.sqrt(365)
                    self.strategy_metrics['sortino_ratio'] = (annual_return / 100) / downside_vol if downside_vol > 0 else 0
                
            if len(self.performance_data['equity_curve']) > 1:
                equity_series = pd.Series([eq['equity'] for eq in self.performance_data['equity_curve']])
                peak = equity_series.expanding().max()
                drawdown = (equity_series - peak) / peak
                self.strategy_metrics['max_drawdown'] = abs(drawdown.min()) * 100
                
            if trades:
                winning_trades = len([t for t in trades if self._calculate_trade_pnl(t) > 0])
                self.strategy_metrics['win_rate'] = (winning_trades / len(trades)) * 100
                self.strategy_metrics['total_trades'] = len(trades)
                profits = sum([self._calculate_trade_pnl(t) for t in trades if self._calculate_trade_pnl(t) > 0])
                losses = abs(sum([self._calculate_trade_pnl(t) for t in trades if self._calculate_trade_pnl(t) < 0]))
                self.strategy_metrics['profit_factor'] = profits / losses if losses > 0 else 0
                
        except Exception as e:
            print(f"❌ Error updating strategy metrics: {e}")
            
    def _calculate_trade_pnl(self, trade: Dict) -> float:
        try:
            if 'pnl' in trade:
                return trade['pnl']
            elif 'entry_price' in trade and 'exit_price' in trade and 'size' in trade:
                if trade.get('side') == 'long':
                    return (trade['exit_price'] - trade['entry_price']) * trade['size']
                else:
                    return (trade['entry_price'] - trade['exit_price']) * trade['size']
            return 0.0
        except Exception as e:
            return 0.0
            
    def update_risk_metrics(self, positions: Dict, portfolio_value: float, market_data: Dict):
        try:
            self.risk_metrics['portfolio_var'] = self._calculate_portfolio_var(positions, portfolio_value)
            self.risk_metrics['portfolio_cvar'] = self._calculate_portfolio_cvar(positions, portfolio_value)
            self.risk_metrics['concentration_risk'] = self._calculate_concentration_risk(positions, portfolio_value)
            self.risk_metrics['leverage_ratio'] = self._calculate_leverage_ratio(positions, portfolio_value)
            
            if len(self.performance_data['equity_curve']) > 1:
                equity_series = pd.Series([eq['equity'] for eq in self.performance_data['equity_curve']])
                peak = equity_series.expanding().max()
                current_drawdown = (peak.iloc[-1] - equity_series.iloc[-1]) / peak.iloc[-1]
                max_drawdown = ((equity_series - peak) / peak).min()
                
                self.risk_metrics['current_drawdown'] = current_drawdown
                self.risk_metrics['maximum_drawdown'] = abs(max_drawdown)
                
            returns_list = [ret['return'] for ret in self.performance_data['daily_returns'][-252:] if ret['return'] != 0]
            if len(returns_list) > 1:
                self.risk_metrics['portfolio_volatility'] = np.std(returns_list) * np.sqrt(365)
                
            self._check_risk_alerts()
        except Exception as e:
            print(f"❌ Error updating risk metrics: {e}")
            
    def _calculate_portfolio_var(self, positions: Dict, portfolio_value: float, confidence: float = 0.95) -> float:
        try:
            if not positions or portfolio_value == 0:
                return 0.0
            returns_list = [ret['return'] for ret in self.performance_data['daily_returns'][-252:] if ret['return'] != 0]
            if len(returns_list) < 30:
                return portfolio_value * 0.02
            returns_array = np.array(returns_list)
            var_percentile = np.percentile(returns_array, (1 - confidence) * 100)
            return abs(var_percentile * portfolio_value)
        except Exception as e:
            return portfolio_value * 0.02
            
    def _calculate_portfolio_cvar(self, positions: Dict, portfolio_value: float, confidence: float = 0.95) -> float:
        try:
            if not positions or portfolio_value == 0:
                return 0.0
            returns_list = [ret['return'] for ret in self.performance_data['daily_returns'][-252:] if ret['return'] != 0]
            if len(returns_list) < 30:
                return portfolio_value * 0.03
            returns_array = np.array(returns_list)
            var_percentile = np.percentile(returns_array, (1 - confidence) * 100)
            tail_returns = returns_array[returns_array <= var_percentile]
            if len(tail_returns) > 0:
                cvar = abs(np.mean(tail_returns) * portfolio_value)
            else:
                cvar = abs(var_percentile * portfolio_value)
            return cvar
        except Exception as e:
            return portfolio_value * 0.03
            
    def _calculate_concentration_risk(self, positions: Dict, portfolio_value: float) -> float:
        try:
            if not positions or portfolio_value == 0:
                return 0.0
            position_weights = []
            for symbol, position in positions.items():
                if position.get('size', 0) != 0:
                    weight = abs(position.get('notional', 0)) / portfolio_value
                    position_weights.append(weight)
            if not position_weights:
                return 0.0
            herfindahl_index = sum([w**2 for w in position_weights])
            return herfindahl_index
        except Exception as e:
            return 0.0
            
    def _calculate_leverage_ratio(self, positions: Dict, portfolio_value: float) -> float:
        try:
            if not positions or portfolio_value == 0:
                return 0.0
            total_notional = sum([abs(position.get('notional', 0)) for position in positions.values()])
            return total_notional / portfolio_value
        except Exception as e:
            return 0.0
            
    def update_execution_metrics(self, order_results: List[Dict]):
        try:
            if not order_results:
                return
            total_orders = len(order_results)
            successful_orders = len([order for order in order_results if order.get('success', False)])
            failed_orders = total_orders - successful_orders
            
            self.execution_metrics['total_orders'] += total_orders
            self.execution_metrics['successful_orders'] += successful_orders
            self.execution_metrics['failed_orders'] += failed_orders
            
            if self.execution_metrics['total_orders'] > 0:
                self.execution_metrics['fill_rate'] = (self.execution_metrics['successful_orders'] / self.execution_metrics['total_orders']) * 100
                
            execution_times = [order.get('execution_time', 0) for order in order_results if order.get('success', False)]
            if execution_times:
                current_avg_latency = self.execution_metrics['average_latency']
                new_latency = np.mean(execution_times)
                orders_count = self.execution_metrics['successful_orders']
                self.execution_metrics['average_latency'] = ((current_avg_latency * (orders_count - len(execution_times)) + new_latency * len(execution_times)) / orders_count)
                
            slippages = [order.get('slippage', 0) for order in order_results if order.get('success', False) and 'slippage' in order]
            if slippages:
                current_avg_slippage = self.execution_metrics['average_slippage']
                new_slippage = np.mean(slippages)
                orders_with_slippage = len([o for o in order_results if 'slippage' in o])
                if orders_with_slippage > 0:
                    self.execution_metrics['average_slippage'] = new_slippage
                    
            total_fees = sum([order.get('fees', 0) for order in order_results if order.get('success', False)])
            self.execution_metrics['execution_cost'] += total_fees
            
            market_impacts = [order.get('market_impact', 0) for order in order_results if order.get('success', False) and 'market_impact' in order]
            if market_impacts:
                self.execution_metrics['market_impact'] = np.mean(market_impacts)
                
            self._check_execution_alerts()
        except Exception as e:
            print(f"❌ Error updating execution metrics: {e}")
            
    def _check_performance_alerts(self, equity: float, returns: float):
        try:
            if self.risk_metrics.get('maximum_drawdown', 0) > self.thresholds['max_drawdown']:
                self._create_alert('HIGH_DRAWDOWN', f"Maximum drawdown exceeded: {self.risk_metrics['maximum_drawdown']:.2%}", 'HIGH')
                
            if self.strategy_metrics.get('sharpe_ratio', 0) < self.thresholds['min_sharpe']:
                self._create_alert('LOW_SHARPE', f"Sharpe ratio below threshold: {self.strategy_metrics['sharpe_ratio']:.2f}", 'MEDIUM')
                
            if self.strategy_metrics.get('win_rate', 100) < self.thresholds['min_win_rate'] * 100:
                self._create_alert('LOW_WIN_RATE', f"Win rate below threshold: {self.strategy_metrics['win_rate']:.1f}%", 'MEDIUM')
                
        except Exception as e:
            print(f"❌ Error checking performance alerts: {e}")
            
    def _check_risk_alerts(self):
        try:
            if self.risk_metrics.get('portfolio_var', 0) > self.thresholds['max_var']:
                self._create_alert('HIGH_VAR', f"Portfolio VaR exceeded: {self.risk_metrics['portfolio_var']:.2f}", 'HIGH')
                
            if self.risk_metrics.get('current_drawdown', 0) > self.thresholds['max_drawdown'] * 0.8:
                self._create_alert('DRAWDOWN_WARNING', f"Current drawdown approaching limit: {self.risk_metrics['current_drawdown']:.2%}", 'MEDIUM')
                
            if self.risk_metrics.get('concentration_risk', 0) > 0.5:
                self._create_alert('HIGH_CONCENTRATION', f"Portfolio concentration risk high: {self.risk_metrics['concentration_risk']:.2f}", 'MEDIUM')
                
            if self.risk_metrics.get('leverage_ratio', 0) > 5.0:
                self._create_alert('HIGH_LEVERAGE', f"Leverage ratio high: {self.risk_metrics['leverage_ratio']:.2f}", 'HIGH')
                
        except Exception as e:
            print(f"❌ Error checking risk alerts: {e}")
            
    def _check_execution_alerts(self):
        try:
            if self.execution_metrics.get('fill_rate', 100) < 90:
                self._create_alert('LOW_FILL_RATE', f"Fill rate low: {self.execution_metrics['fill_rate']:.1f}%", 'MEDIUM')
                
            if self.execution_metrics.get('average_latency', 0) > 5:
                self._create_alert('HIGH_LATENCY', f"Average latency high: {self.execution_metrics['average_latency']:.2f}s", 'MEDIUM')
                
            if abs(self.execution_metrics.get('average_slippage', 0)) > 0.005:
                self._create_alert('HIGH_SLIPPAGE', f"Average slippage high: {self.execution_metrics['average_slippage']:.4f}", 'MEDIUM')
                
        except Exception as e:
            print(f"❌ Error checking execution alerts: {e}")
            
    def _create_alert(self, alert_type: str, message: str, severity: str):
        try:
            alert = {'timestamp': datetime.now(), 'type': alert_type, 'message': message, 'severity': severity, 'acknowledged': False}
            self.alerts.append(alert)
            
            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]
                
            print(f"🚨 ALERT [{severity}] {alert_type}: {message}")
            
            if severity == 'HIGH':
                self._send_notification(alert)
                
        except Exception as e:
            print(f"❌ Error creating alert: {e}")
            
    def _send_notification(self, alert: Dict):
        try:
            if self.notification_settings.get('webhook'):
                self._send_webhook_notification(alert)
            if self.notification_settings.get('slack'):
                self._send_slack_notification(alert)
        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            
    def _send_webhook_notification(self, alert: Dict):
        try:
            import requests
            webhook_url = self.notification_settings['webhook']
            payload = {'alert_type': alert['type'], 'message': alert['message'], 'severity': alert['severity'], 'timestamp': alert['timestamp'].isoformat()}
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"❌ Error sending webhook notification: {e}")
            
    def _send_slack_notification(self, alert: Dict):
        try:
            import requests
            slack_url = self.notification_settings['slack']
            slack_message = {'text': f"🚨 {alert['type']}: {alert['message']}", 'username': 'Scherman Strategy Bot', 'icon_emoji': ':warning:'}
            requests.post(slack_url, json=slack_message, timeout=5)
        except Exception as e:
            print(f"❌ Error sending Slack notification: {e}")
            
    def get_performance_summary(self) -> Dict:
        try:
            return {'strategy_metrics': self.strategy_metrics, 'risk_metrics': self.risk_metrics, 'execution_metrics': self.execution_metrics, 'benchmark_metrics': self.benchmark_metrics, 'last_updated': datetime.now()}
        except Exception as e:
            print(f"❌ Error getting performance summary: {e}")
            return {}
            
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_alerts = [alert for alert in self.alerts if alert['timestamp'] > cutoff_time]
            return sorted(recent_alerts, key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            print(f"❌ Error getting recent alerts: {e}")
            return []
            
    def acknowledge_alert(self, alert_index: int) -> bool:
        try:
            if 0 <= alert_index < len(self.alerts):
                self.alerts[alert_index]['acknowledged'] = True
                return True
            return False
        except Exception as e:
            print(f"❌ Error acknowledging alert: {e}")
            return False
            
    def generate_daily_report(self) -> Dict:
        try:
            report = {'date': datetime.now().date(), 'performance_summary': self.get_performance_summary(), 'recent_alerts': self.get_recent_alerts(24), 'system_health': self.system_health}
            
            if len(self.performance_data['daily_returns']) > 0:
                today_return = self.performance_data['daily_returns'][-1]['return']
                report['today_return'] = today_return
                
            if len(self.performance_data['equity_curve']) > 1:
                current_equity = self.performance_data['equity_curve'][-1]['equity']
                previous_equity = self.performance_data['equity_curve'][-2]['equity']
                daily_change = (current_equity - previous_equity) / previous_equity
                report['daily_equity_change'] = daily_change
                
            return report
        except Exception as e:
            print(f"❌ Error generating daily report: {e}")
            return {}
            
    def update_system_health(self, cpu_usage: float, memory_usage: float, disk_usage: float, network_latency: float, api_status: bool):
        try:
            self.system_health = {'cpu_usage': cpu_usage, 'memory_usage': memory_usage, 'disk_usage': disk_usage, 'network_latency': network_latency, 'api_status': api_status, 'last_updated': datetime.now()}
            
            if cpu_usage > 90:
                self._create_alert('HIGH_CPU', f"CPU usage high: {cpu_usage:.1f}%", 'HIGH')
            if memory_usage > 90:
                self._create_alert('HIGH_MEMORY', f"Memory usage high: {memory_usage:.1f}%", 'HIGH')
            if disk_usage > 90:
                self._create_alert('HIGH_DISK', f"Disk usage high: {disk_usage:.1f}%", 'MEDIUM')
            if network_latency > 1000:
                self._create_alert('HIGH_LATENCY', f"Network latency high: {network_latency:.0f}ms", 'MEDIUM')
            if not api_status:
                self._create_alert('API_DOWN', "API connection lost", 'HIGH')
                
        except Exception as e:
            print(f"❌ Error updating system health: {e}")
            
    def cleanup_old_data(self, days: int = None):
        try:
            if days is None:
                days = self.data_retention['days']
                
            cutoff_date = datetime.now() - timedelta(days=days)
            
            self.performance_data['equity_curve'] = [eq for eq in self.performance_data['equity_curve'] if eq['timestamp'] > cutoff_date]
            self.performance_data['daily_returns'] = [ret for ret in self.performance_data['daily_returns'] if ret['timestamp'] > cutoff_date]
            self.alerts = [alert for alert in self.alerts if alert['timestamp'] > cutoff_date]
            
            print(f"✅ Cleaned up data older than {days} days")
        except Exception as e:
            print(f"❌ Error cleaning up old data: {e}")
            
    def export_performance_data(self, format: str = 'json') -> str:
        try:
            export_data = {'performance_data': self.performance_data, 'strategy_metrics': self.strategy_metrics, 'risk_metrics': self.risk_metrics, 'execution_metrics': self.execution_metrics, 'export_timestamp': datetime.now().isoformat()}
            
            if format == 'json':
                return json.dumps(export_data, default=str, indent=2)
            elif format == 'csv':
                df = pd.DataFrame(self.performance_data['equity_curve'])
                return df.to_csv(index=False)
            else:
                return json.dumps(export_data, default=str)
                
        except Exception as e:
            print(f"❌ Error exporting performance data: {e}")
            return ""
            
    def get_real_time_dashboard_data(self) -> Dict:
        try:
            dashboard_data = {'timestamp': datetime.now(), 'strategy_metrics': self.strategy_metrics, 'risk_metrics': self.risk_metrics, 'execution_metrics': self.execution_metrics, 'system_health': self.system_health, 'recent_alerts': self.get_recent_alerts(1), 'performance_chart_data': self.performance_data['equity_curve'][-100:] if len(self.performance_data['equity_curve']) > 100 else self.performance_data['equity_curve']}
            
            return dashboard_data
        except Exception as e:
            print(f"❌ Error getting dashboard data: {e}")
            return {}