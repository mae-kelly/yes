import ccxt
import numpy as np
import pandas as pd
from datetime import datetime
import time
import asyncio
from typing import Dict, List
import json

class ProductionExecutionEngine:
    def __init__(self, config: Dict, exchange_client):
        self.config = config
        self.exchange = exchange_client
        self.execution_metrics = {
            'orders_executed': 0,
            'total_volume': 0,
            'avg_slippage': 0,
            'avg_execution_time': 0,
            'success_rate': 0
        }
        self.order_history = []
        self.slippage_tracker = []
        
    def place_order(self, symbol: str, side: str, size: float, order_type: str = 'market', 
                   price: float = None, algorithm: str = 'smart') -> Dict:
        
        if algorithm == 'smart':
            return self._smart_execution(symbol, side, size, order_type, price)
        elif algorithm == 'twap':
            return self._twap_execution(symbol, side, size, 30, 10)
        elif algorithm == 'iceberg':
            return self._iceberg_execution(symbol, side, size, size * 0.1)
        else:
            return self._direct_execution(symbol, side, size, order_type, price)
    
    def _smart_execution(self, symbol: str, side: str, size: float, order_type: str, price: float) -> Dict:
        try:
            market_conditions = self._assess_market_conditions(symbol)
            
            if market_conditions['volatility'] > 0.05 and market_conditions['liquidity'] < 0.3:
                return self._iceberg_execution(symbol, side, size, size * 0.05)
            elif market_conditions['spread_bps'] > 20:
                return self._twap_execution(symbol, side, size, 20, 8)
            else:
                return self._direct_execution(symbol, side, size, order_type, price)
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _direct_execution(self, symbol: str, side: str, size: float, order_type: str, price: float) -> Dict:
        try:
            start_time = time.time()
            
            pre_trade_price = self._get_mid_price(symbol)
            
            if order_type == 'market':
                order = self.exchange.create_market_order(symbol, side, size)
            else:
                order = self.exchange.create_limit_order(symbol, side, size, price)
            
            if order and order.get('id'):
                filled_order = self._wait_for_fill(order['id'], symbol, 30)
                
                if filled_order and filled_order.get('status') == 'closed':
                    execution_time = time.time() - start_time
                    filled_price = float(filled_order.get('average', 0))
                    filled_size = float(filled_order.get('filled', 0))
                    fees = float(filled_order.get('fee', {}).get('cost', 0))
                    
                    slippage = self._calculate_slippage(pre_trade_price, filled_price, side)
                    
                    result = {
                        'success': True,
                        'order_id': order['id'],
                        'symbol': symbol,
                        'side': side,
                        'size': size,
                        'filled_size': filled_size,
                        'average_price': filled_price,
                        'fees': fees,
                        'execution_time': execution_time,
                        'slippage': slippage,
                        'algorithm': 'direct',
                        'timestamp': datetime.now()
                    }
                    
                    self._update_metrics(result)
                    return result
                    
            return {'success': False, 'error': 'Order not filled'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _twap_execution(self, symbol: str, side: str, total_size: float, duration_minutes: int, slices: int) -> Dict:
        try:
            slice_size = total_size / slices
            slice_interval = (duration_minutes * 60) / slices
            
            fills = []
            total_filled = 0
            
            for i in range(slices):
                try:
                    orderbook = self.exchange.fetch_order_book(symbol, 5)
                    
                    if side == 'buy':
                        limit_price = orderbook['bids'][0][0] * 1.0001
                    else:
                        limit_price = orderbook['asks'][0][0] * 0.9999
                    
                    slice_order = self.exchange.create_limit_order(symbol, side, slice_size, limit_price)
                    
                    if slice_order:
                        filled = self._wait_for_fill(slice_order['id'], symbol, min(slice_interval, 60))
                        
                        if filled and filled.get('status') == 'closed':
                            fills.append({
                                'size': float(filled.get('filled', 0)),
                                'price': float(filled.get('average', 0)),
                                'fees': float(filled.get('fee', {}).get('cost', 0))
                            })
                            total_filled += float(filled.get('filled', 0))
                        else:
                            self.exchange.cancel_order(slice_order['id'], symbol)
                            market_fill = self.exchange.create_market_order(symbol, side, slice_size)
                            if market_fill:
                                market_filled = self._wait_for_fill(market_fill['id'], symbol)
                                if market_filled:
                                    fills.append({
                                        'size': float(market_filled.get('filled', 0)),
                                        'price': float(market_filled.get('average', 0)),
                                        'fees': float(market_filled.get('fee', {}).get('cost', 0))
                                    })
                                    total_filled += float(market_filled.get('filled', 0))
                    
                    if i < slices - 1:
                        time.sleep(slice_interval)
                        
                except Exception as e:
                    continue
            
            if fills:
                total_value = sum([f['size'] * f['price'] for f in fills])
                avg_price = total_value / total_filled if total_filled > 0 else 0
                total_fees = sum([f['fees'] for f in fills])
                
                result = {
                    'success': True,
                    'symbol': symbol,
                    'side': side,
                    'size': total_size,
                    'filled_size': total_filled,
                    'average_price': avg_price,
                    'fees': total_fees,
                    'algorithm': 'twap',
                    'fills': fills,
                    'timestamp': datetime.now()
                }
                
                self._update_metrics(result)
                return result
                
            return {'success': False, 'error': 'No fills achieved'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _iceberg_execution(self, symbol: str, side: str, total_size: float, iceberg_size: float) -> Dict:
        try:
            fills = []
            remaining_size = total_size
            
            while remaining_size > 0:
                current_size = min(iceberg_size, remaining_size)
                
                orderbook = self.exchange.fetch_order_book(symbol, 5)
                
                if side == 'buy':
                    limit_price = orderbook['bids'][0][0]
                else:
                    limit_price = orderbook['asks'][0][0]
                
                order = self.exchange.create_limit_order(symbol, side, current_size, limit_price)
                
                if order:
                    filled = self._wait_for_fill(order['id'], symbol, 30)
                    
                    if filled and filled.get('status') == 'closed':
                        filled_size = float(filled.get('filled', 0))
                        fills.append({
                            'size': filled_size,
                            'price': float(filled.get('average', 0)),
                            'fees': float(filled.get('fee', {}).get('cost', 0))
                        })
                        remaining_size -= filled_size
                    else:
                        self.exchange.cancel_order(order['id'], symbol)
                        break
                        
                time.sleep(2)
            
            if fills:
                total_filled = sum([f['size'] for f in fills])
                total_value = sum([f['size'] * f['price'] for f in fills])
                avg_price = total_value / total_filled if total_filled > 0 else 0
                total_fees = sum([f['fees'] for f in fills])
                
                result = {
                    'success': True,
                    'symbol': symbol,
                    'side': side,
                    'size': total_size,
                    'filled_size': total_filled,
                    'average_price': avg_price,
                    'fees': total_fees,
                    'algorithm': 'iceberg',
                    'fills': fills,
                    'timestamp': datetime.now()
                }
                
                self._update_metrics(result)
                return result
                
            return {'success': False, 'error': 'Execution incomplete'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _wait_for_fill(self, order_id: str, symbol: str, timeout: int = 30) -> Dict:
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                order = self.exchange.fetch_order(order_id, symbol)
                
                if order['status'] in ['closed', 'filled']:
                    return order
                elif order['status'] in ['canceled', 'rejected']:
                    break
                    
                time.sleep(0.5)
                
            return {}
            
        except Exception as e:
            return {}
    
    def _get_mid_price(self, symbol: str) -> float:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            if ticker['bid'] and ticker['ask']:
                return (ticker['bid'] + ticker['ask']) / 2
            return ticker['last']
        except:
            return 0
    
    def _calculate_slippage(self, expected_price: float, executed_price: float, side: str) -> float:
        try:
            if side == 'buy':
                return (executed_price - expected_price) / expected_price
            else:
                return (expected_price - executed_price) / expected_price
        except:
            return 0
    
    def _assess_market_conditions(self, symbol: str) -> Dict:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            orderbook = self.exchange.fetch_order_book(symbol, 20)
            
            spread = (ticker['ask'] - ticker['bid']) / ticker['last'] if ticker['ask'] and ticker['bid'] else 0.001
            
            bid_depth = sum([bid[1] for bid in orderbook['bids'][:10]])
            ask_depth = sum([ask[1] for ask in orderbook['asks'][:10]])
            total_depth = bid_depth + ask_depth
            
            volatility = abs(ticker['percentage']) / 100 if ticker['percentage'] else 0.02
            
            return {
                'spread_bps': spread * 10000,
                'liquidity': min(total_depth / 100000, 1.0),
                'volatility': volatility,
                'imbalance': (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0
            }
            
        except:
            return {
                'spread_bps': 10,
                'liquidity': 0.5,
                'volatility': 0.02,
                'imbalance': 0
            }
    
    def _update_metrics(self, result: Dict):
        try:
            self.execution_metrics['orders_executed'] += 1
            self.execution_metrics['total_volume'] += result.get('filled_size', 0)
            
            if 'slippage' in result:
                self.slippage_tracker.append(result['slippage'])
                self.execution_metrics['avg_slippage'] = np.mean(self.slippage_tracker)
            
            if 'execution_time' in result:
                times = [r.get('execution_time', 0) for r in self.order_history[-50:]]
                times.append(result['execution_time'])
                self.execution_metrics['avg_execution_time'] = np.mean(times)
            
            successful_orders = len([r for r in self.order_history if r.get('success')])
            total_orders = len(self.order_history)
            self.execution_metrics['success_rate'] = successful_orders / total_orders if total_orders > 0 else 0
            
            self.order_history.append(result)
            if len(self.order_history) > 1000:
                self.order_history = self.order_history[-1000:]
                
        except Exception as e:
            pass
    
    def get_execution_metrics(self) -> Dict:
        return {
            **self.execution_metrics,
            'recent_orders': self.order_history[-10:],
            'timestamp': datetime.now()
        }
