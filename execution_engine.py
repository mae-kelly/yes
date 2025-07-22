import ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import threading
import queue
import asyncio
import warnings
warnings.filterwarnings('ignore')

class ExecutionEngine:
    def __init__(self, config: Dict, okx_client):
        self.config = config
        self.okx_client = okx_client
        self.execution_queue = queue.Queue()
        self.order_tracker = {}
        self.execution_metrics = {
            'orders_filled': 0,
            'orders_canceled': 0,
            'orders_rejected': 0,
            'total_volume_executed': 0.0,
            'average_execution_time': 0.0,
            'total_slippage': 0.0,
            'total_market_impact': 0.0,
            'total_fees_paid': 0.0
        }
        self.running = False
        
    def place_order(self, symbol: str, side: str, size: float, order_type: str = 'market',
                   price: float = None, algorithm: str = 'aggressive', 
                   reduce_only: bool = False, **kwargs) -> Dict:
        
        if algorithm == 'twap':
            return self._twap_algorithm({
                'symbol': symbol, 'side': side, 'size': size,
                'duration': kwargs.get('duration', 30),
                'slices': kwargs.get('slices', 10)
            })
        elif algorithm == 'vwap':
            return self._vwap_algorithm({
                'symbol': symbol, 'side': side, 'size': size,
                'duration': kwargs.get('duration', 30)
            })
        elif algorithm == 'iceberg':
            return self._iceberg_algorithm({
                'symbol': symbol, 'side': side, 'size': size,
                'iceberg_size': kwargs.get('iceberg_size', size * 0.1)
            })
        elif algorithm == 'adaptive':
            return self._adaptive_algorithm({
                'symbol': symbol, 'side': side, 'size': size
            })
        else:
            return self._aggressive_algorithm({
                'symbol': symbol, 'side': side, 'size': size,
                'order_type': order_type, 'price': price, 'reduce_only': reduce_only
            })
            
    def _aggressive_algorithm(self, request: Dict) -> Dict:
        try:
            symbol = request['symbol']
            side = request['side']
            size = request['size']
            order_type = request.get('order_type', 'market')
            price = request.get('price')
            reduce_only = request.get('reduce_only', False)
            
            start_time = time.time()
            
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': size,
                'params': {'reduceOnly': reduce_only}
            }
            
            if order_type == 'limit' and price is not None:
                order_params['price'] = price
                
            if order_type == 'market':
                order_result = self.okx_client.create_market_order(symbol, side, size, None, None, {'reduceOnly': reduce_only})
            else:
                order_result = self.okx_client.create_limit_order(symbol, side, size, price, {'reduceOnly': reduce_only})
                
            execution_time = time.time() - start_time
            
            if order_result and order_result.get('id'):
                filled_order = self._wait_for_fill(order_result['id'], symbol)
                
                if filled_order and filled_order.get('status') in ['closed', 'filled']:
                    slippage = self._calculate_slippage(request, filled_order)
                    market_impact = self._calculate_market_impact(request, filled_order)
                    
                    self.execution_metrics['orders_filled'] += 1
                    self.execution_metrics['total_volume_executed'] += float(filled_order.get('filled', 0))
                    
                    avg_time = self.execution_metrics['average_execution_time']
                    total_orders = self.execution_metrics['orders_filled']
                    self.execution_metrics['average_execution_time'] = ((avg_time * (total_orders - 1) + execution_time) / total_orders)
                    
                    return {
                        'success': True,
                        'order_id': order_result['id'],
                        'symbol': symbol,
                        'side': side,
                        'size': size,
                        'filled_size': float(filled_order.get('filled', 0)),
                        'average_price': float(filled_order.get('average', 0)),
                        'fees': float(filled_order.get('fee', {}).get('cost', 0)),
                        'execution_time': execution_time,
                        'slippage': slippage,
                        'market_impact': market_impact,
                        'algorithm': 'aggressive',
                        'timestamp': datetime.now()
                    }
                else:
                    self.execution_metrics['orders_canceled'] += 1
                    return {'success': False, 'error': 'Order not filled'}
            else:
                self.execution_metrics['orders_rejected'] += 1
                return {'success': False, 'error': 'Order placement failed'}
                
        except Exception as e:
            self.execution_metrics['orders_rejected'] += 1
            return {'success': False, 'error': str(e)}
            
    def _twap_algorithm(self, request: Dict) -> Dict:
        try:
            symbol = request['symbol']
            side = request['side']
            total_size = request['size']
            duration_minutes = request.get('duration', 30)
            slice_count = request.get('slices', 10)
            
            slice_size = total_size / slice_count
            slice_interval = (duration_minutes * 60) / slice_count
            
            fills = []
            total_filled = 0
            
            for i in range(slice_count):
                try:
                    orderbook = self.okx_client.fetch_order_book(symbol, limit=10)
                    
                    if side == 'buy':
                        limit_price = orderbook['asks'][0][0] * 0.9999
                    else:
                        limit_price = orderbook['bids'][0][0] * 1.0001
                        
                    slice_order = self.okx_client.create_limit_order(symbol, side, slice_size, limit_price)
                    
                    if slice_order and slice_order.get('id'):
                        filled_order = self._wait_for_fill(slice_order['id'], symbol, timeout=min(slice_interval, 60))
                        
                        if filled_order and filled_order.get('status') in ['closed', 'filled']:
                            fills.append({
                                'filled_size': float(filled_order.get('filled', 0)),
                                'average_price': float(filled_order.get('average', 0)),
                                'fees': float(filled_order.get('fee', {}).get('cost', 0))
                            })
                            total_filled += float(filled_order.get('filled', 0))
                        else:
                            try:
                                self.okx_client.cancel_order(slice_order['id'], symbol)
                            except:
                                pass
                            
                            market_order = self.okx_client.create_market_order(symbol, side, slice_size)
                            if market_order:
                                market_filled = self._wait_for_fill(market_order['id'], symbol)
                                if market_filled:
                                    fills.append({
                                        'filled_size': float(market_filled.get('filled', 0)),
                                        'average_price': float(market_filled.get('average', 0)),
                                        'fees': float(market_filled.get('fee', {}).get('cost', 0))
                                    })
                                    total_filled += float(market_filled.get('filled', 0))
                    
                    if i < slice_count - 1:
                        time.sleep(slice_interval)
                        
                except Exception as e:
                    print(f"TWAP slice {i+1} error: {e}")
                    continue
                    
            if fills:
                total_value = sum([fill['filled_size'] * fill['average_price'] for fill in fills])
                average_price = total_value / total_filled if total_filled > 0 else 0
                total_fees = sum([fill['fees'] for fill in fills])
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'side': side,
                    'size': total_size,
                    'filled_size': total_filled,
                    'average_price': average_price,
                    'fees': total_fees,
                    'algorithm': 'twap',
                    'slice_count': len(fills),
                    'fills': fills,
                    'timestamp': datetime.now()
                }
            else:
                return {'success': False, 'error': 'No fills achieved'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _vwap_algorithm(self, request: Dict) -> Dict:
        try:
            symbol = request['symbol']
            side = request['side']
            total_size = request['size']
            duration_minutes = request.get('duration', 30)
            
            historical_volumes = self._get_volume_profile(symbol, duration_minutes)
            
            fills = []
            total_filled = 0
            
            for period_volume_ratio in historical_volumes:
                slice_size = total_size * period_volume_ratio
                
                if slice_size < 0.001:
                    continue
                    
                slice_result = self._aggressive_algorithm({
                    'symbol': symbol,
                    'side': side,
                    'size': slice_size,
                    'order_type': 'market'
                })
                
                if slice_result.get('success'):
                    fills.append(slice_result)
                    total_filled += slice_result.get('filled_size', 0)
                    
                time.sleep(60)
                
            if fills:
                total_value = sum([fill['filled_size'] * fill['average_price'] for fill in fills])
                average_price = total_value / total_filled if total_filled > 0 else 0
                total_fees = sum([fill.get('fees', 0) for fill in fills])
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'side': side,
                    'size': total_size,
                    'filled_size': total_filled,
                    'average_price': average_price,
                    'fees': total_fees,
                    'algorithm': 'vwap',
                    'slice_count': len(fills),
                    'fills': fills,
                    'timestamp': datetime.now()
                }
            else:
                return {'success': False, 'error': 'No fills achieved'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _iceberg_algorithm(self, request: Dict) -> Dict:
        try:
            symbol = request['symbol']
            side = request['side']
            total_size = request['size']
            iceberg_size = request.get('iceberg_size', total_size * 0.1)
            
            fills = []
            total_filled = 0
            
            while total_filled < total_size:
                remaining_size = total_size - total_filled
                current_slice = min(iceberg_size, remaining_size)
                
                orderbook = self.okx_client.fetch_order_book(symbol, limit=5)
                
                if side == 'buy':
                    limit_price = orderbook['bids'][0][0]
                else:
                    limit_price = orderbook['asks'][0][0]
                    
                slice_order = self.okx_client.create_limit_order(symbol, side, current_slice, limit_price, {'timeInForce': 'GTC'})
                
                if slice_order and slice_order.get('id'):
                    filled_order = self._wait_for_fill(slice_order['id'], symbol, timeout=30)
                    
                    if filled_order and filled_order.get('status') in ['closed', 'filled']:
                        fills.append({
                            'filled_size': float(filled_order.get('filled', 0)),
                            'average_price': float(filled_order.get('average', 0)),
                            'fees': float(filled_order.get('fee', {}).get('cost', 0))
                        })
                        total_filled += float(filled_order.get('filled', 0))
                    else:
                        try:
                            self.okx_client.cancel_order(slice_order['id'], symbol)
                        except:
                            pass
                        break
                        
                time.sleep(2)
                
            if fills:
                total_value = sum([fill['filled_size'] * fill['average_price'] for fill in fills])
                average_price = total_value / total_filled if total_filled > 0 else 0
                total_fees = sum([fill['fees'] for fill in fills])
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'side': side,
                    'size': total_size,
                    'filled_size': total_filled,
                    'average_price': average_price,
                    'fees': total_fees,
                    'algorithm': 'iceberg',
                    'iceberg_size': iceberg_size,
                    'slice_count': len(fills),
                    'fills': fills,
                    'timestamp': datetime.now()
                }
            else:
                return {'success': False, 'error': 'No fills achieved'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _adaptive_algorithm(self, request: Dict) -> Dict:
        try:
            symbol = request['symbol']
            market_conditions = self._assess_market_conditions(symbol)
            
            if market_conditions['volatility'] > 0.05:
                if market_conditions['liquidity'] > 0.7:
                    return self._aggressive_algorithm(request)
                else:
                    request['duration'] = 45
                    request['slices'] = 15
                    return self._twap_algorithm(request)
            elif market_conditions['liquidity'] < 0.3:
                request['iceberg_size'] = request['size'] * 0.05
                return self._iceberg_algorithm(request)
            else:
                return self._aggressive_algorithm(request)
                
        except Exception as e:
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
                    
                time.sleep(0.5)
                
            return {}
            
        except Exception:
            return {}
            
    def _calculate_slippage(self, request: Dict, filled_order: Dict) -> float:
        try:
            ticker = self.okx_client.fetch_ticker(request['symbol'])
            arrival_price = float(ticker['last'])
            execution_price = float(filled_order.get('average', 0))
            
            if arrival_price == 0 or execution_price == 0:
                return 0
                
            side = request['side']
            if side == 'buy':
                slippage = (execution_price - arrival_price) / arrival_price
            else:
                slippage = (arrival_price - execution_price) / arrival_price
                
            return slippage
            
        except Exception:
            return 0
            
    def _calculate_market_impact(self, request: Dict, filled_order: Dict) -> float:
        try:
            size = request['size']
            orderbook = self.okx_client.fetch_order_book(request['symbol'], limit=20)
            
            total_depth = (sum([bid[1] for bid in orderbook['bids'][:10]]) + 
                          sum([ask[1] for ask in orderbook['asks'][:10]]))
            
            if total_depth == 0:
                return 0.01
                
            volume_ratio = size / total_depth
            base_impact = volume_ratio * 0.001
            
            return min(base_impact, 0.05)
            
        except Exception:
            return 0.001
            
    def _get_volume_profile(self, symbol: str, duration_minutes: int) -> List[float]:
        try:
            historical_data = self.okx_client.fetch_ohlcv(symbol, '1m', limit=duration_minutes)
            
            if not historical_data:
                return [0.25, 0.25, 0.25, 0.25]
                
            volumes = [candle[5] for candle in historical_data]
            total_volume = sum(volumes)
            
            if total_volume == 0:
                return [0.25, 0.25, 0.25, 0.25]
                
            volume_ratios = [vol / total_volume for vol in volumes]
            
            return volume_ratios
            
        except Exception:
            return [0.25, 0.25, 0.25, 0.25]
            
    def _assess_market_conditions(self, symbol: str) -> Dict:
        try:
            ticker = self.okx_client.fetch_ticker(symbol)
            orderbook = self.okx_client.fetch_order_book(symbol, limit=20)
            
            spread = ((ticker['ask'] - ticker['bid']) / ticker['last'] 
                     if ticker['ask'] and ticker['bid'] and ticker['last'] else 0.01)
            
            bid_depth = sum([bid[1] for bid in orderbook['bids'][:10]]) if orderbook['bids'] else 0
            ask_depth = sum([ask[1] for ask in orderbook['asks'][:10]]) if orderbook['asks'] else 0
            total_depth = bid_depth + ask_depth
            
            price_change_24h = abs(ticker['percentage']) / 100 if ticker['percentage'] else 0.02
            
            return {
                'volatility': price_change_24h,
                'liquidity': min(total_depth / 100000, 1.0),
                'spread': spread,
                'depth': total_depth
            }
            
        except Exception:
            return {
                'volatility': 0.02,
                'liquidity': 0.5,
                'spread': 0.001,
                'depth': 50000
            }
            
    def get_execution_metrics(self) -> Dict:
        try:
            total_orders = (self.execution_metrics['orders_filled'] + 
                          self.execution_metrics['orders_canceled'] + 
                          self.execution_metrics['orders_rejected'])
            
            fill_rate = (self.execution_metrics['orders_filled'] / total_orders * 100) if total_orders > 0 else 0
            
            return {
                'total_orders': total_orders,
                'orders_filled': self.execution_metrics['orders_filled'],
                'orders_canceled': self.execution_metrics['orders_canceled'],
                'orders_rejected': self.execution_metrics['orders_rejected'],
                'fill_rate': fill_rate,
                'total_volume_executed': self.execution_metrics['total_volume_executed'],
                'average_execution_time': self.execution_metrics['average_execution_time'],
                'total_fees_paid': self.execution_metrics['total_fees_paid'],
                'timestamp': datetime.now()
            }
            
        except Exception:
            return {}
