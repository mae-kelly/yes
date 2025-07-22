import asyncio
import aiohttp
import ccxt.pro as ccxtpro
import pandas as pd
import numpy as np
from datetime import datetime
import json
import time
from typing import Dict, List

class RealTimeDataEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.exchanges = {}
        self.data_feeds = {}
        self.market_data = {}
        self.alternative_data = {}
        self.session = None
        
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        
        for exchange_name in ['okx', 'binance', 'bybit']:
            try:
                exchange_class = getattr(ccxtpro, exchange_name)
                self.exchanges[exchange_name] = exchange_class({
                    'sandbox': False,
                    'enableRateLimit': True,
                    'options': {'defaultType': 'swap'}
                })
            except:
                pass
    
    async def start_real_time_streams(self, symbols: List[str]):
        tasks = []
        
        for symbol in symbols:
            for exchange_name, exchange in self.exchanges.items():
                tasks.append(asyncio.create_task(self._stream_ticker(exchange, symbol)))
                tasks.append(asyncio.create_task(self._stream_orderbook(exchange, symbol)))
                tasks.append(asyncio.create_task(self._stream_trades(exchange, symbol)))
        
        tasks.append(asyncio.create_task(self._stream_fear_greed()))
        tasks.append(asyncio.create_task(self._stream_macro_data()))
        tasks.append(asyncio.create_task(self._stream_whale_alerts()))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _stream_ticker(self, exchange, symbol: str):
        while True:
            try:
                ticker = await exchange.watch_ticker(symbol)
                self.market_data[f"{symbol}_ticker"] = {
                    'price': ticker['last'],
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'volume': ticker['baseVolume'],
                    'change': ticker['percentage'],
                    'timestamp': datetime.now()
                }
            except Exception as e:
                await asyncio.sleep(1)
    
    async def _stream_orderbook(self, exchange, symbol: str):
        while True:
            try:
                orderbook = await exchange.watch_order_book(symbol, 20)
                
                bid_depth = sum([bid[1] for bid in orderbook['bids'][:10]])
                ask_depth = sum([ask[1] for ask in orderbook['asks'][:10]])
                spread = orderbook['asks'][0][0] - orderbook['bids'][0][0]
                mid_price = (orderbook['asks'][0][0] + orderbook['bids'][0][0]) / 2
                
                self.market_data[f"{symbol}_orderbook"] = {
                    'bid_depth': bid_depth,
                    'ask_depth': ask_depth,
                    'spread': spread,
                    'spread_bps': (spread / mid_price) * 10000,
                    'imbalance': (bid_depth - ask_depth) / (bid_depth + ask_depth),
                    'timestamp': datetime.now()
                }
            except Exception as e:
                await asyncio.sleep(1)
    
    async def _stream_trades(self, exchange, symbol: str):
        while True:
            try:
                trades = await exchange.watch_trades(symbol)
                
                recent_trades = trades[-100:] if len(trades) > 100 else trades
                volumes = [trade['amount'] for trade in recent_trades]
                prices = [trade['price'] for trade in recent_trades]
                
                if volumes and prices:
                    vwap = sum([p * v for p, v in zip(prices, volumes)]) / sum(volumes)
                    trade_intensity = len(recent_trades) / 60
                    
                    self.market_data[f"{symbol}_trades"] = {
                        'vwap': vwap,
                        'trade_intensity': trade_intensity,
                        'avg_trade_size': np.mean(volumes),
                        'price_impact': np.std(prices) / np.mean(prices),
                        'timestamp': datetime.now()
                    }
            except Exception as e:
                await asyncio.sleep(1)
    
    async def _stream_fear_greed(self):
        while True:
            try:
                async with self.session.get('https://api.alternative.me/fng/') as response:
                    data = await response.json()
                    
                if data.get('data'):
                    fear_value = float(data['data'][0]['value'])
                    self.alternative_data['fear_greed'] = {
                        'value': fear_value,
                        'classification': data['data'][0]['value_classification'],
                        'timestamp': datetime.now()
                    }
                
                await asyncio.sleep(300)
                
            except Exception as e:
                await asyncio.sleep(300)
    
    async def _stream_macro_data(self):
        while True:
            try:
                urls = [
                    'https://query1.finance.yahoo.com/v8/finance/chart/^VIX',
                    'https://query1.finance.yahoo.com/v8/finance/chart/^DXY',
                    'https://query1.finance.yahoo.com/v8/finance/chart/^TNX'
                ]
                
                for url in urls:
                    try:
                        async with self.session.get(url) as response:
                            data = await response.json()
                            
                        if data.get('chart', {}).get('result'):
                            result = data['chart']['result'][0]
                            meta = result.get('meta', {})
                            symbol = meta.get('symbol', 'unknown')
                            
                            self.alternative_data[f'macro_{symbol}'] = {
                                'price': meta.get('regularMarketPrice', 0),
                                'change': meta.get('regularMarketChangePercent', 0),
                                'timestamp': datetime.now()
                            }
                    except:
                        continue
                
                await asyncio.sleep(600)
                
            except Exception as e:
                await asyncio.sleep(600)
    
    async def _stream_whale_alerts(self):
        while True:
            try:
                whale_api_key = self.config.get('whale_alert_api_key')
                if whale_api_key:
                    url = f"https://api.whale-alert.io/v1/transactions?api_key={whale_api_key}&min_value=100000&limit=10"
                    
                    async with self.session.get(url) as response:
                        data = await response.json()
                        
                    if data.get('transactions'):
                        total_volume = sum([tx.get('amount_usd', 0) for tx in data['transactions']])
                        exchange_inflows = sum([tx.get('amount_usd', 0) for tx in data['transactions'] 
                                              if 'exchange' in tx.get('to', {}).get('owner', '').lower()])
                        
                        self.alternative_data['whale_activity'] = {
                            'total_volume': total_volume,
                            'exchange_inflows': exchange_inflows,
                            'transaction_count': len(data['transactions']),
                            'timestamp': datetime.now()
                        }
                
                await asyncio.sleep(180)
                
            except Exception as e:
                await asyncio.sleep(180)
    
    def get_unified_market_data(self, symbol: str) -> Dict:
        unified = {
            'timestamp': datetime.now(),
            'symbol': symbol
        }
        
        ticker_data = self.market_data.get(f"{symbol}_ticker", {})
        orderbook_data = self.market_data.get(f"{symbol}_orderbook", {})
        trades_data = self.market_data.get(f"{symbol}_trades", {})
        
        unified.update(ticker_data)
        unified.update(orderbook_data)
        unified.update(trades_data)
        
        fear_greed = self.alternative_data.get('fear_greed', {})
        if fear_greed:
            unified['fear_greed_index'] = fear_greed.get('value', 50)
        
        whale_data = self.alternative_data.get('whale_activity', {})
        if whale_data:
            unified.update(whale_data)
        
        for key, macro_data in self.alternative_data.items():
            if key.startswith('macro_'):
                unified[key] = macro_data
        
        return unified
    
    async def close(self):
        if self.session:
            await self.session.close()
        
        for exchange in self.exchanges.values():
            await exchange.close()
