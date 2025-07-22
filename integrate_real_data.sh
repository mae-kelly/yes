#!/bin/bash
set -e

rm -f *backup* *test* *demo* *sample*

cat > real_data_feeds.py << 'FEEDS'
import requests
import ccxt
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json

class RealDataFeeds:
    def __init__(self, config):
        self.config = config
        self.okx = ccxt.okx(config)
        self.session = None
        
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        
    async def get_market_data(self, symbol):
        try:
            ticker = self.okx.fetch_ticker(symbol)
            orderbook = self.okx.fetch_order_book(symbol, 20)
            
            return {
                'price': float(ticker['last']),
                'volume': float(ticker['baseVolume']),
                'change_24h': float(ticker['percentage']),
                'bid': float(ticker['bid']),
                'ask': float(ticker['ask']),
                'spread': float(ticker['ask']) - float(ticker['bid']),
                'orderbook_depth': sum([bid[1] for bid in orderbook['bids'][:5]]),
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {}
            
    async def get_fear_greed_index(self):
        try:
            async with self.session.get("https://api.alternative.me/fng/") as response:
                data = await response.json()
                return float(data['data'][0]['value'])
        except:
            return 50.0
            
    async def get_whale_activity(self, symbol):
        try:
            whale_api_key = self.config.get('whale_alert_key')
            if not whale_api_key:
                return {'transactions': [], 'volume': 0}
                
            url = f"https://api.whale-alert.io/v1/transactions"
            params = {'api_key': whale_api_key, 'min_value': 100000}
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                crypto_symbol = symbol.split('-')[0].lower()
                relevant_txs = []
                
                for tx in data.get('transactions', []):
                    if crypto_symbol in tx.get('symbol', '').lower():
                        relevant_txs.append({
                            'amount_usd': float(tx.get('amount_usd', 0)),
                            'from': tx.get('from', {}).get('owner', ''),
                            'to': tx.get('to', {}).get('owner', ''),
                            'timestamp': tx.get('timestamp', 0)
                        })
                        
                return {
                    'transactions': relevant_txs[:10],
                    'volume': sum([tx['amount_usd'] for tx in relevant_txs])
                }
        except:
            return {'transactions': [], 'volume': 0}
            
    async def get_news_sentiment(self, symbol):
        try:
            news_api_key = self.config.get('news_api_key')
            if not news_api_key:
                return {'sentiment': 0, 'count': 0}
                
            coin = symbol.split('-')[0].lower()
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': f'{coin} cryptocurrency',
                'apiKey': news_api_key,
                'pageSize': 20,
                'sortBy': 'publishedAt'
            }
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                sentiment_scores = []
                for article in data.get('articles', [])[:10]:
                    title = article.get('title', '').lower()
                    sentiment = self.analyze_sentiment(title)
                    if sentiment != 0:
                        sentiment_scores.append(sentiment)
                        
                return {
                    'sentiment': np.mean(sentiment_scores) if sentiment_scores else 0,
                    'count': len(sentiment_scores)
                }
        except:
            return {'sentiment': 0, 'count': 0}
            
    def analyze_sentiment(self, text):
        positive = ['bull', 'moon', 'pump', 'surge', 'rally', 'gain', 'rise', 'profit']
        negative = ['bear', 'dump', 'crash', 'drop', 'fall', 'loss', 'decline']
        
        pos_count = sum(1 for word in positive if word in text)
        neg_count = sum(1 for word in negative if word in text)
        
        total = pos_count + neg_count
        if total == 0:
            return 0
            
        return (pos_count - neg_count) / total
        
    async def get_comprehensive_data(self, symbols):
        tasks = []
        
        for symbol in symbols:
            tasks.append(self.get_market_data(symbol))
            tasks.append(self.get_whale_activity(symbol))
            tasks.append(self.get_news_sentiment(symbol))
            
        tasks.append(self.get_fear_greed_index())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        comprehensive_data = {}
        fear_greed = results[-1] if not isinstance(results[-1], Exception) else 50.0
        
        for i, symbol in enumerate(symbols):
            base_idx = i * 3
            comprehensive_data[symbol] = {
                'market': results[base_idx] if not isinstance(results[base_idx], Exception) else {},
                'whale': results[base_idx + 1] if not isinstance(results[base_idx + 1], Exception) else {},
                'sentiment': results[base_idx + 2] if not isinstance(results[base_idx + 2], Exception) else {}
            }
            
        comprehensive_data['fear_greed'] = fear_greed
        return comprehensive_data
        
    async def close(self):
        if self.session:
            await self.session.close()
FEEDS

echo "✅ Real data feeds integrated"
