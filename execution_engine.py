import ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import threading
import queue
import json
import warnings
warnings.filterwarnings('ignore')


class ExecutionEngine:
    def __init__(self, config: Dict, okx_client):
        self.config = config
        self.okx_client = okx_client
        self.execution_queue = queue.Queue()
        self.order_tracker = {}
        
        # Core execution algorithms
        self.execution_algorithms = {
            'aggressive': self._aggressive_algorithm,
            'passive': self._passive_algorithm,
            'twap': self._twap_algorithm,
            'vwap': self._vwap_algorithm,
            'adaptive': self._adaptive_algorithm,
            'iceberg': self._iceberg_algorithm
        }
        
        # Execution metrics
        self.execution_state = {
            'orders_filled': 0,
            'orders_canceled': 0,
            'orders_rejected': 0,
            'total_volume_executed': 0.0,
            'average_execution_time': 0.0,
            'total_slippage': 0.0,
            'total_market_impact': 0.0,
            'total_fees_paid': 0.0
        }
        
        # Market impact models
        self.slippage_model = {
            'linear_impact': 0.001,
            'sqrt_impact': 0.0005,
            'permanent_impact': 0.0002,
            'temporary_impact': 0.0008
        }
        
        self.running = False
        self.execution_thread = None
        
    def initialize(self):
        """Initialize execution engine"""
        try:
            self._start_execution_engine()
            return True
        except Exception as e:
            print(f"Failed to initialize execution engine: {e}")
            return False
            
    def _start_execution_engine(self):
        """Start background execution thread"""
        self.running = True
        self.execution_thread = threading.Thread(target=self._execution_loop)
        self.execution_thread.daemon = True
        self.execution_thread.start()
        
    def _execution_loop(self):
        """Main execution processing loop"""
        while self.running:
            try:
                if not self.execution_queue.empty():
                    execution_request = self.execution_queue.get()
                    self._process_execution_request(execution_request)
                time.sleep(0.001)
            except Exception as e:
                print(f"Execution loop error: {e}")
                time.sleep(1)
                
    def place_order(self, symbol: str, side: str, size: float, order_type: str = 'market',
                   price: float = None, algorithm: str = 'aggressive', 
                   reduce_only: bool = False, **kwargs) -> Dict:
        """Place order with specified execution algorithm"""
        try:
            execution_request = {
                'symbol': symbol,
                'side': side,
                'size': size,
                'order_type': order_type,
                'price': price,
                'algorithm': algorithm,
                'reduce_only': reduce_only,
                'timestamp': datetime.now(),
                'request_id': self._generate_request_id(),
                'kwargs': kwargs
            }
            
            if algorithm in self.execution_algorithms:
                return self.execution_algorithms[algorithm](execution_request)
            else:
                return self._aggressive_algorithm(execution_request)
                
        except Exception as e:
            print(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}
            
    def _process_execution_request(self, request: Dict):
        """Process execution request from queue"""
        try:
            algorithm = request.get('algorithm', 'aggressive')
            if algorithm in self.execution_algorithms:
                result = self.execution_algorithms[algorithm](request)
                self._update_execution_metrics(request, result)
        except Exception as e:
            print(f"Error processing execution request: {e}")
            
    def _aggressive_algorithm(self, request: Dict) -> Dict:
        """Aggressive market order execution"""
        try:
            symbol = request['symbol']
            side = request['side']
            size = request['size']
            order_type = request.get('order_type', 'market')
            price = request.get('price')
            reduce_only = request.get('reduce_only', False)
            
            start_time = time.time()
            
            # Create order parameters
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': size,
                'reduceOnly': reduce_only
            }
            
            if order_type == 'limit' and price is not None:
                order_params['price'] = price
                
            # Execute order
            if order_type == 'market':
                order_result = self.okx_client.create_market_order(**order_params)
            else:
                order_result = self.okx_client.create_limit_order(**order_params)
                
            execution_time = time.time() - start_time
            
            if order_result and order_result.get('id'):
                filled_order = self._wait_for_fill(order_result['id'], symbol)
                
                if filled_order:
                    slippage = self._calculate_slippage(request, filled_order)
                    market_impact = self._calculate_market_impact(request, filled_order)
                    
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
                    return {'success': False, 'error': 'Order not filled'}
            else:
                return {'success': False, 'error': 'Order placement failed'}
                
        except Exception as e:
            print(f"Aggressive algorithm error: {e}")
            return {'success': False, 'error': str(e)}
            
    def _passive_algorithm(self, request: Dict) -> Dict:
        """Passive limit order execution at best bid/ask"""
        try:
            symbol = request['symbol']
            side = request['side']
            size = request['size']
            reduce_only = request.get('reduce_only', False)
            
            # Get current orderbook
            orderbook = self.okx_client.fetch_order_book(symbol, limit=5)
            
            # Set limit price at best bid/ask
            if side == 'buy':
                limit_price = float(orderbook['bids'][0][0]) if orderbook['bids'] else None
            else:
                limit_price = float(orderbook['asks'][0][0]) if orderbook['asks'] else None
                
            if limit_price is None:
                return {'success': False, 'error': 'Unable to determine limit price'}
                
            start_time = time.time()
            
            order_result = self.okx_client.create_limit_order(
                symbol=symbol,
                side=side,
                amount=size,
                price=limit_price,
                params={'reduceOnly': reduce_only, 'timeInForce': 'GTC'}
            )
            
            execution_time = time.time() - start_time
            
            if order_result and order_result.get('id'):
                filled_order = self._wait_for_fill(order_result['id'], symbol, timeout=60)
                
                if filled_order and filled_order.get('status') == 'closed':
                    slippage = self._calculate_slippage(request, filled_order)
                    market_impact = self._calculate_market_impact(request, filled_order)
                    
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
                        'algorithm': 'passive',
                        'timestamp': datetime.now()
                    }
                else:
                    self.okx_client.cancel_order(order_result['id'], symbol)
                    return {'success': False, 'error': 'Order not filled, canceled'}
            else:
                return {'success': False, 'error': 'Order placement failed'}
                
        except Exception as e:
            print(f"Passive algorithm error: {e}")
            return {'success': False, 'error': str(e)}
            
    def _twap_algorithm(self, request: Dict) -> Dict:
        """Time-Weighted Average Price algorithm"""
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
                    slice_request = request.copy()
                    slice_request['size'] = slice_size
                    slice_request['algorithm'] = 'aggressive'
                    
                    slice_result = self._aggressive_algorithm(slice_request)
                    
                    if slice_result.get('success'):
                        fills.append(slice_result)
                        total_filled += slice_result.get('filled_size', 0)
                    else:
                        print(f"TWAP slice {i+1} failed: {slice_result.get('error')}")
                        
                    if i < slice_count - 1:
                        time.sleep(slice_interval)
                        
                except Exception as e:
                    print(f"TWAP slice {i+1} error: {e}")
                    continue
                    
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
                    'algorithm': 'twap',
                    'slice_count': len(fills),
                    'fills': fills,
                    'timestamp': datetime.now()
                }
            else:
                return {'success': False, 'error': 'No fills achieved'}
                
        except Exception as e:
            print(f"TWAP algorithm error: {e}")
            return {'success': False, 'error': str(e)}
            
    def _vwap_algorithm(self, request: Dict) -> Dict:
        """Volume-Weighted Average Price algorithm"""
        try:
            symbol = request['symbol']
            side = request['side']
            total_size = request['size']
            duration_minutes = request.get('duration', 30)
            
            # Simplified VWAP - use historical volume profile
            historical_volume = self._get_historical_volume_profile(symbol, duration_minutes)
            
            if not historical_volume:
                return self._twap_algorithm(request)
                
            fills = []
            total_filled = 0
            
            for period, volume_ratio in historical_volume.items():
                try:
                    slice_size = total_size * volume_ratio
                    
                    if slice_size < 0.001:
                        continue
                        
                    slice_request = request.copy()
                    slice_request['size'] = slice_size
                    slice_request['algorithm'] = 'aggressive'
                    
                    slice_result = self._aggressive_algorithm(slice_request)
                    
                    if slice_result.get('success'):
                        fills.append(slice_result)
                        total_filled += slice_result.get('filled_size', 0)
                        
                    time.sleep(60)
                    
                except Exception as e:
                    print(f"VWAP slice error: {e}")
                    continue
                    
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
            print(f"VWAP algorithm error: {e}")
            return {'success': False, 'error': str(e)}
            
    def _iceberg_algorithm(self, request: Dict) -> Dict:
        """Iceberg order algorithm - hide order size"""
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
                
                try:
                    slice_request = request.copy()
                    slice_request['size'] = current_slice
                    slice_request['algorithm'] = 'passive'
                    
                    slice_result = self._passive_algorithm(slice_request)
                    
                    if slice_result.get('success'):
                        fills.append(slice_result)
                        total_filled += slice_result.get('filled_size', 0)
                    else:
                        break
                        
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Iceberg slice error: {e}")
                    break
                    
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
                    'algorithm': 'iceberg',
                    'iceberg_size': iceberg_size,
                    'slice_count': len(fills),
                    'fills': fills,
                    'timestamp': datetime.now()
                }
            else:
                return {'success': False, 'error': 'No fills achieved'}
                
        except Exception as e:
            print(f"Iceberg algorithm error: {e}")
            return {'success': False, 'error': str(e)}
            
    def _adaptive_algorithm(self, request: Dict) -> Dict:
        """Adaptive algorithm based on market conditions"""
        try:
            symbol = request['symbol']
            market_conditions = self._assess_market_conditions(symbol)
            
            # Choose algorithm based on market conditions
            if market_conditions['volatility'] > 0.05:
                if market_conditions['liquidity'] > 0.7:
                    return self._passive_algorithm(request)
                else:
                    request['duration'] = 45
                    request['slices'] = 15
                    return self._twap_algorithm(request)
            elif market_conditions['trend_strength'] > 0.7:
                return self._aggressive_algorithm(request)
            elif market_conditions['liquidity'] < 0.3:
                request['iceberg_size'] = request['size'] * 0.05
                return self._iceberg_algorithm(request)
            else:
                return self._passive_algorithm(request)
                
        except Exception as e:
            print(f"Adaptive algorithm error: {e}")
            return {'success': False, 'error': str(e)}
            
    def _wait_for_fill(self, order_id: str, symbol: str, timeout: int = 30) -> Dict:
        """Wait for order to be filled"""
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
            print(f"Error waiting for fill: {e}")
            return {}
            
    def _calculate_slippage(self, request: Dict, filled_order: Dict) -> float:
        """Calculate execution slippage"""
        try:
            symbol = request['symbol']
            side = request['side']
            
            arrival_price = self._get_arrival_price(symbol)
            execution_price = float(filled_order.get('average', 0))
            
            if arrival_price == 0 or execution_price == 0:
                return 0
                
            if side == 'buy':
                slippage = (execution_price - arrival_price) / arrival_price
            else:
                slippage = (arrival_price - execution_price) / arrival_price
                
            return slippage
            
        except Exception as e:
            return 0
            
    def _calculate_market_impact(self, request: Dict, filled_order: Dict) -> float:
        """Calculate market impact"""
        try:
            symbol = request['symbol']
            size = request['size']
            
            orderbook = self.okx_client.fetch_order_book(symbol, limit=20)
            
            total_depth = (sum([bid[1] for bid in orderbook['bids'][:10]]) + 
                          sum([ask[1] for ask in orderbook['asks'][:10]]))
            
            if total_depth == 0:
                return 0.01
                
            volume_ratio = size / total_depth
            base_impact = volume_ratio * 0.001
            
            return min(base_impact, 0.05)
            
        except Exception as e:
            return 0.001
            
    def _get_arrival_price(self, symbol: str) -> float:
        """Get arrival price (current market price)"""
        try:
            ticker = self.okx_client.fetch_ticker(symbol)
            return float(ticker['last']) if ticker and ticker['last'] else 0
        except Exception as e:
            return 0
            
    def _get_historical_volume_profile(self, symbol: str, duration_minutes: int) -> Dict:
        """Get historical volume profile - simplified version"""
        try:
            # Simplified volume profile
            return {
                'period_1': 0.15,
                'period_2': 0.25,
                'period_3': 0.35,
                'period_4': 0.25
            }
        except Exception as e:
            return {}
            
    def _assess_market_conditions(self, symbol: str) -> Dict:
        """Assess current market conditions"""
        try:
            ticker = self.okx_client.fetch_ticker(symbol)
            orderbook = self.okx_client.fetch_order_book(symbol, limit=20)
            
            # Calculate basic market metrics
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
                'trend_strength': 0.5,  # Simplified
                'volume_trend': 0.5     # Simplified
            }
            
        except Exception as e:
            return {
                'volatility': 0.02,
                'liquidity': 0.5,
                'spread': 0.001,
                'trend_strength': 0.5,
                'volume_trend': 0.5
            }
            
    def _update_execution_metrics(self, request: Dict, result: Dict):
        """Update execution performance metrics"""
        try:
            if result.get('success'):
                self.execution_state['orders_filled'] += 1
                self.execution_state['total_volume_executed'] += result.get('filled_size', 0)
                
                execution_time = result.get('execution_time', 0)
                current_avg = self.execution_state['average_execution_time']
                total_orders = self.execution_state['orders_filled']
                
                self.execution_state['average_execution_time'] = (
                    (current_avg * (total_orders - 1) + execution_time) / total_orders
                )
                
                if 'slippage' in result:
                    slippage = result['slippage']
                    current_slippage = self.execution_state['total_slippage']
                    self.execution_state['total_slippage'] = (
                        (current_slippage * (total_orders - 1) + slippage) / total_orders
                    )
                    
                if 'market_impact' in result:
                    impact = result['market_impact']
                    current_impact = self.execution_state['total_market_impact']
                    self.execution_state['total_market_impact'] = (
                        (current_impact * (total_orders - 1) + impact) / total_orders
                    )
                    
                self.execution_state['total_fees_paid'] += result.get('fees', 0)
                
            else:
                if 'canceled' in result.get('error', '').lower():
                    self.execution_state['orders_canceled'] += 1
                else:
                    self.execution_state['orders_rejected'] += 1
                    
        except Exception as e:
            print(f"Error updating execution metrics: {e}")
            
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{int(time.time() * 1000000)}"
        
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel existing order"""
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
                return {'success': False, 'error': 'Cancel failed'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def get_execution_metrics(self) -> Dict:
        """Get current execution performance metrics"""
        try:
            total_orders = (self.execution_state['orders_filled'] + 
                          self.execution_state['orders_canceled'] + 
                          self.execution_state['orders_rejected'])
            
            fill_rate = (self.execution_state['orders_filled'] / total_orders * 100) if total_orders > 0 else 0
            
            return {
                'total_orders': total_orders,
                'orders_filled': self.execution_state['orders_filled'],
                'orders_canceled': self.execution_state['orders_canceled'],
                'orders_rejected': self.execution_state['orders_rejected'],
                'fill_rate': fill_rate,
                'total_volume_executed': self.execution_state['total_volume_executed'],
                'average_execution_time': self.execution_state['average_execution_time'],
                'average_slippage': self.execution_state['total_slippage'],
                'average_market_impact': self.execution_state['total_market_impact'],
                'total_fees_paid': self.execution_state['total_fees_paid'],
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error getting execution metrics: {e}")
            return {}
            
    def batch_order_execution(self, orders: List[Dict]) -> Dict:
        """Execute multiple orders in batch"""
        try:
            results = []
            successful_orders = 0
            failed_orders = 0
            
            for order in orders:
                try:
                    result = self.place_order(
                        symbol=order['symbol'],
                        side=order['side'],
                        size=order['size'],
                        order_type=order.get('order_type', 'market'),
                        price=order.get('price'),
                        algorithm=order.get('algorithm', 'aggressive'),
                        reduce_only=order.get('reduce_only', False)
                    )
                    
                    results.append({'order': order, 'result': result})
                    
                    if result.get('success'):
                        successful_orders += 1
                    else:
                        failed_orders += 1
                        
                    time.sleep(0.1)
                    
                except Exception as e:
                    results.append({
                        'order': order,
                        'result': {'success': False, 'error': str(e)}
                    })
                    failed_orders += 1
                    
            return {
                'success': True,
                'total_orders': len(orders),
                'successful_orders': successful_orders,
                'failed_orders': failed_orders,
                'success_rate': (successful_orders / len(orders) * 100) if orders else 0,
                'results': results,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error in batch order execution: {e}")
            return {'success': False, 'error': str(e)}
            
    def optimize_execution_strategy(self, symbol: str, size: float, urgency: str = 'medium') -> str:
        """Recommend optimal execution algorithm based on conditions"""
        try:
            market_conditions = self._assess_market_conditions(symbol)
            
            if urgency == 'high':
                if market_conditions['liquidity'] > 0.8:
                    return 'aggressive'
                else:
                    return 'twap'
            elif urgency == 'low':
                if market_conditions['volatility'] < 0.02:
                    return 'passive'
                else:
                    return 'iceberg'
            else:  # medium urgency
                if market_conditions['liquidity'] > 0.7 and market_conditions['volatility'] < 0.03:
                    return 'passive'
                elif market_conditions['volatility'] > 0.05:
                    return 'twap'
                else:
                    return 'adaptive'
                    
        except Exception as e:
            print(f"Error optimizing execution strategy: {e}")
            return 'aggressive'
            
    def emergency_stop_all_orders(self) -> Dict:
        """Emergency stop - cancel all open orders"""
        try:
            canceled_orders = []
            
            for symbol in self.config.get('symbols', []):
                try:
                    open_orders = self.okx_client.fetch_open_orders(symbol)
                    
                    for order in open_orders:
                        try:
                            cancel_result = self.okx_client.cancel_order(order['id'], symbol)
                            if cancel_result:
                                canceled_orders.append({
                                    'order_id': order['id'],
                                    'symbol': symbol,
                                    'side': order['side'],
                                    'amount': order['amount']
                                })
                        except Exception as e:
                            print(f"Failed to cancel order {order['id']}: {e}")
                            
                except Exception as e:
                    print(f"Error fetching orders for {symbol}: {e}")
                    
            self.order_tracker.clear()
            
            return {
                'success': True,
                'canceled_orders_count': len(canceled_orders),
                'canceled_orders': canceled_orders,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Emergency stop error: {e}")
            return {'success': False, 'error': str(e)}
            
    def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get status of specific order"""
        try:
            order_status = self.okx_client.fetch_order(order_id, symbol)
            
            return {
                'order_id': order_id,
                'symbol': symbol,
                'status': order_status.get('status', 'unknown'),
                'filled': float(order_status.get('filled', 0)),
                'remaining': float(order_status.get('remaining', 0)),
                'average_price': float(order_status.get('average', 0)),
                'timestamp': order_status.get('timestamp'),
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            print(f"Error getting order status: {e}")
            return {'error': str(e)}
            
    def analyze_execution_quality(self, trades: List[Dict]) -> Dict:
        """Analyze execution quality metrics"""
        try:
            if not trades:
                return {}
                
            total_trades = len(trades)
            successful_trades = len([t for t in trades if t.get('success')])
            
            slippages = [t.get('slippage', 0) for t in trades if t.get('success')]
            market_impacts = [t.get('market_impact', 0) for t in trades if t.get('success')]
            execution_times = [t.get('execution_time', 0) for t in trades if t.get('success')]
            fees = [t.get('fees', 0) for t in trades if t.get('success')]
            
            avg_slippage = np.mean(slippages) if slippages else 0
            avg_market_impact = np.mean(market_impacts) if market_impacts else 0
            avg_execution_time = np.mean(execution_times) if execution_times else 0
            total_fees = sum(fees)
            
            return {
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'success_rate': (successful_trades / total_trades * 100) if total_trades > 0 else 0,
                'average_slippage': avg_slippage,
                'average_market_impact': avg_market_impact,
                'average_execution_time': avg_execution_time,
                'total_fees': total_fees,
                'cost_per_trade': total_fees / successful_trades if successful_trades > 0 else 0,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error analyzing execution quality: {e}")
            return {}
            
    def generate_execution_report(self) -> Dict:
        """Generate comprehensive execution report"""
        try:
            metrics = self.get_execution_metrics()
            
            return {
                'report_date': datetime.now(),
                'execution_metrics': metrics,
                'engine_status': 'running' if self.running else 'stopped',
                'supported_algorithms': list(self.execution_algorithms.keys()),
                'queue_size': self.execution_queue.qsize(),
                'recommendations': self._generate_recommendations(metrics)
            }
            
        except Exception as e:
            print(f"Error generating execution report: {e}")
            return {}
            
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate execution improvement recommendations"""
        recommendations = []
        
        if metrics.get('fill_rate', 0) < 95:
            recommendations.append("Consider using more passive algorithms to improve fill rates")
            
        if metrics.get('average_slippage', 0) > 0.005:
            recommendations.append("High slippage detected - consider breaking large orders into smaller sizes")
            
        if metrics.get('average_execution_time', 0) > 5:
            recommendations.append("Execution times are high - review order routing and market timing")
            
        if metrics.get('total_fees_paid', 0) > 1000:
            recommendations.append("Consider optimizing for lower fee structures")
            
        return recommendations
        
    def shutdown(self):
        """Shutdown execution engine"""
        try:
            print("🛑 Initiating execution engine shutdown...")
            
            self.running = False
            
            if self.execution_thread and self.execution_thread.is_alive():
                print("⏳ Waiting for execution thread to finish...")
                self.execution_thread.join(timeout=10)
                
            emergency_result = self.emergency_stop_all_orders()
            print(f"🚫 Emergency stop result: {emergency_result.get('canceled_orders_count', 0)} orders canceled")
            
            while not self.execution_queue.empty():
                try:
                    self.execution_queue.get_nowait()
                except:
                    break
                    
            self.order_tracker.clear()
            
            final_metrics = self.get_execution_metrics()
            print(f"📊 Final metrics - Orders filled: {final_metrics.get('orders_filled', 0)}")
            
            print("✅ Execution engine shutdown completed successfully")
            
            return {
                'success': True,
                'shutdown_time': datetime.now(),
                'final_metrics': final_metrics,
                'orders_canceled': emergency_result.get('canceled_orders_count', 0)
            }
            
        except Exception as e:
            print(f"❌ Error during execution engine shutdown: {e}")
            return {'success': False, 'error': str(e)}