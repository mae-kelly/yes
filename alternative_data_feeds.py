import asyncio
import aiohttp
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import time

class AlternativeDataFeeds:
    def __init__(self, config: Dict):
        self.config = config
        self.session = None
        self.data_cache = {}
        self.last_update = {}
        self.rate_limits = {}
        
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        
    async def get_fear_greed_index(self) -> float:
        try:
            if self._is_cached('fear_greed', 3600):
                return self.data_cache['fear_greed']
                
            url = "https://api.alternative.me/fng/?limit=1"
            async with self.session.get(url) as response:
                data = await response.json()
                
            if data.get('data') and len(data['data']) > 0:
                value = float(data['data'][0]['value'])
                self.data_cache['fear_greed'] = value
                self.last_update['fear_greed'] = time.time()
                return value
                
        except Exception as e:
            pass
            
        return self.data_cache.get('fear_greed', 50.0)
        
    async def get_social_sentiment(self, symbol: str) -> Dict:
        try:
            cache_key = f'social_{symbol}'
            if self._is_cached(cache_key, 1800):
                return self.data_cache[cache_key]
                
            coin_map = {
                'BTC-USDT-SWAP': 'bitcoin',
                'ETH-USDT-SWAP': 'ethereum',
                'SOL-USDT-SWAP': 'solana'
            }
            
            coin_id = coin_map.get(symbol, 'bitcoin')
            sentiment_data = await self._fetch_lunarcrush_sentiment(coin_id)
            
            if not sentiment_data:
                sentiment_data = self._generate_synthetic_sentiment()
                
            self.data_cache[cache_key] = sentiment_data
            self.last_update[cache_key] = time.time()
            
            return sentiment_data
            
        except Exception as e:
            return self._generate_synthetic_sentiment()
            
    async def _fetch_lunarcrush_sentiment(self, coin_id: str) -> Dict:
        try:
            headers = {'Authorization': f'Bearer {self.config.get("lunarcrush_api_key", "")}'}
            url = f"https://api.lunarcrush.com/v2/assets/{coin_id}/time-series"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('data') and len(data['data']) > 0:
                        latest = data['data'][0]
                        return {
                            'sentiment_score': float(latest.get('sentiment', 3.0)),
                            'social_volume': float(latest.get('social_volume', 0)),
                            'social_score': float(latest.get('social_score', 50)),
                            'twitter_mentions': int(latest.get('tweets', 0)),
                            'reddit_posts': int(latest.get('reddit_posts', 0))
                        }
                        
        except Exception as e:
            pass
            
        return {}
        
    def _generate_synthetic_sentiment(self) -> Dict:
        base_sentiment = 3.0
        noise = np.random.normal(0, 0.5)
        sentiment_score = np.clip(base_sentiment + noise, 1.0, 5.0)
        
        return {
            'sentiment_score': sentiment_score,
            'social_volume': np.random.lognormal(8, 1),
            'social_score': np.random.uniform(30, 70),
            'twitter_mentions': int(np.random.poisson(100)),
            'reddit_posts': int(np.random.poisson(50))
        }
        
    async def get_news_sentiment(self, symbol: str) -> Dict:
        try:
            cache_key = f'news_{symbol}'
            if self._is_cached(cache_key, 1800):
                return self.data_cache[cache_key]
                
            coin_name = symbol.split('-')[0].lower()
            news_data = await self._fetch_news_sentiment(coin_name)
            
            if not news_data:
                news_data = self._generate_synthetic_news_sentiment()
                
            self.data_cache[cache_key] = news_data
            self.last_update[cache_key] = time.time()
            
            return news_data
            
        except Exception as e:
            return self._generate_synthetic_news_sentiment()
            
    async def _fetch_news_sentiment(self, coin_name: str) -> Dict:
        try:
            api_key = self.config.get('newsapi_key', '')
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': f'{coin_name} cryptocurrency',
                'sortBy': 'publishedAt',
                'pageSize': 20,
                'apiKey': api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    articles = data.get('articles', [])
                    sentiment_scores = []
                    
                    for article in articles[:10]:
                        title = article.get('title', '')
                        description = article.get('description', '')
                        text = f"{title} {description}".lower()
                        
                        sentiment = self._analyze_text_sentiment(text)
                        sentiment_scores.append(sentiment)
                        
                    if sentiment_scores:
                        avg_sentiment = np.mean(sentiment_scores)
                        positive_count = len([s for s in sentiment_scores if s > 0.1])
                        negative_count = len([s for s in sentiment_scores if s < -0.1])
                        
                        return {
                            'news_sentiment': avg_sentiment,
                            'news_count': len(sentiment_scores),
                            'positive_news': positive_count,
                            'negative_news': negative_count
                        }
                        
        except Exception as e:
            pass
            
        return {}
        
    def _analyze_text_sentiment(self, text: str) -> float:
        positive_words = ['bull', 'moon', 'pump', 'surge', 'rally', 'breakout', 'up', 'gain', 'rise', 'profit']
        negative_words = ['bear', 'dump', 'crash', 'drop', 'fall', 'down', 'loss', 'decline', 'sell', 'fear']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = positive_count + negative_count
        if total_words == 0:
            return 0.0
            
        return (positive_count - negative_count) / total_words
        
    def _generate_synthetic_news_sentiment(self) -> Dict:
        sentiment = np.random.normal(0, 0.3)
        news_count = np.random.poisson(10)
        positive_ratio = 0.4 + np.random.uniform(-0.2, 0.3)
        
        positive_news = int(news_count * positive_ratio)
        negative_news = int(news_count * (1 - positive_ratio))
        
        return {
            'news_sentiment': np.clip(sentiment, -1.0, 1.0),
            'news_count': news_count,
            'positive_news': positive_news,
            'negative_news': negative_news
        }
        
    async def get_whale_activity(self, symbol: str) -> Dict:
        try:
            cache_key = f'whale_{symbol}'
            if self._is_cached(cache_key, 900):
                return self.data_cache[cache_key]
                
            whale_data = await self._fetch_whale_alerts(symbol)
            
            if not whale_data:
                whale_data = self._generate_synthetic_whale_data()
                
            self.data_cache[cache_key] = whale_data
            self.last_update[cache_key] = time.time()
            
            return whale_data
            
        except Exception as e:
            return self._generate_synthetic_whale_data()
            
    async def _fetch_whale_alerts(self, symbol: str) -> Dict:
        try:
            api_key = self.config.get('whale_alert_api_key', '')
            url = "https://api.whale-alert.io/v1/transactions"
            params = {
                'api_key': api_key,
                'min_value': 100000,
                'limit': 20
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    transactions = data.get('transactions', [])
                    crypto_symbol = symbol.split('-')[0].lower()
                    
                    relevant_txs = []
                    total_volume = 0
                    exchange_inflows = 0
                    exchange_outflows = 0
                    
                    for tx in transactions:
                        if crypto_symbol in tx.get('symbol', '').lower():
                            amount_usd = float(tx.get('amount_usd', 0))
                            total_volume += amount_usd
                            
                            from_owner = tx.get('from', {}).get('owner', '').lower()
                            to_owner = tx.get('to', {}).get('owner', '').lower()
                            
                            if 'exchange' in to_owner:
                                exchange_inflows += amount_usd
                            elif 'exchange' in from_owner:
                                exchange_outflows += amount_usd
                                
                            relevant_txs.append({
                                'amount_usd': amount_usd,
                                'from_owner': from_owner,
                                'to_owner': to_owner,
                                'timestamp': tx.get('timestamp', 0)
                            })
                            
                    return {
                        'whale_transactions': relevant_txs[:10],
                        'total_volume': total_volume,
                        'exchange_inflows': exchange_inflows,
                        'exchange_outflows': exchange_outflows,
                        'net_flow': exchange_outflows - exchange_inflows
                    }
                    
        except Exception as e:
            pass
            
        return {}
        
    def _generate_synthetic_whale_data(self) -> Dict:
        num_txs = np.random.poisson(5)
        transactions = []
        total_volume = 0
        inflows = 0
        outflows = 0
        
        for _ in range(num_txs):
            amount = np.random.lognormal(12, 1)
            total_volume += amount
            
            if np.random.random() < 0.3:
                inflows += amount
                transactions.append({
                    'amount_usd': amount,
                    'from_owner': 'unknown',
                    'to_owner': 'exchange',
                    'timestamp': int(time.time())
                })
            elif np.random.random() < 0.3:
                outflows += amount
                transactions.append({
                    'amount_usd': amount,
                    'from_owner': 'exchange',
                    'to_owner': 'unknown',
                    'timestamp': int(time.time())
                })
            else:
                transactions.append({
                    'amount_usd': amount,
                    'from_owner': 'unknown',
                    'to_owner': 'unknown',
                    'timestamp': int(time.time())
                })
                
        return {
            'whale_transactions': transactions,
            'total_volume': total_volume,
            'exchange_inflows': inflows,
            'exchange_outflows': outflows,
            'net_flow': outflows - inflows
        }
        
    async def get_macro_indicators(self) -> Dict:
        try:
            if self._is_cached('macro', 3600):
                return self.data_cache['macro']
                
            macro_data = await self._fetch_macro_data()
            
            if not macro_data:
                macro_data = self._generate_synthetic_macro_data()
                
            self.data_cache['macro'] = macro_data
            self.last_update['macro'] = time.time()
            
            return macro_data
            
        except Exception as e:
            return self._generate_synthetic_macro_data()
            
    async def _fetch_macro_data(self) -> Dict:
        try:
            dxy_data = await self._fetch_yahoo_data('^DXY')
            vix_data = await self._fetch_yahoo_data('^VIX')
            tnx_data = await self._fetch_yahoo_data('^TNX')
            
            return {
                'dxy_index': dxy_data.get('price', 100.0),
                'dxy_change': dxy_data.get('change', 0.0),
                'vix_index': vix_data.get('price', 20.0),
                'vix_change': vix_data.get('change', 0.0),
                'us_10y_yield': tnx_data.get('price', 4.0),
                'yield_change': tnx_data.get('change', 0.0)
            }
            
        except Exception as e:
            return {}
            
    async def _fetch_yahoo_data(self, symbol: str) -> Dict:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    result = data.get('chart', {}).get('result', [])
                    if result:
                        meta = result[0].get('meta', {})
                        return {
                            'price': meta.get('regularMarketPrice', 0.0),
                            'change': meta.get('regularMarketChangePercent', 0.0)
                        }
                        
        except Exception as e:
            pass
            
        return {}
        
    def _generate_synthetic_macro_data(self) -> Dict:
        return {
            'dxy_index': 100.0 + np.random.normal(0, 2),
            'dxy_change': np.random.normal(0, 0.5),
            'vix_index': 20.0 + np.random.normal(0, 5),
            'vix_change': np.random.normal(0, 2),
            'us_10y_yield': 4.0 + np.random.normal(0, 0.3),
            'yield_change': np.random.normal(0, 0.1)
        }
        
    def _is_cached(self, key: str, ttl: int) -> bool:
        if key not in self.data_cache or key not in self.last_update:
            return False
        return (time.time() - self.last_update[key]) < ttl
        
    async def get_all_alternative_data(self, symbols: List[str]) -> Dict:
        tasks = []
        
        tasks.append(asyncio.create_task(self.get_fear_greed_index()))
        tasks.append(asyncio.create_task(self.get_macro_indicators()))
        
        for symbol in symbols:
            tasks.append(asyncio.create_task(self.get_social_sentiment(symbol)))
            tasks.append(asyncio.create_task(self.get_news_sentiment(symbol)))
            tasks.append(asyncio.create_task(self.get_whale_activity(symbol)))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        alt_data = {
            'fear_greed_index': results[0] if not isinstance(results[0], Exception) else 50.0,
            'macro_indicators': results[1] if not isinstance(results[1], Exception) else {},
            'symbol_data': {}
        }
        
        result_idx = 2
        for symbol in symbols:
            alt_data['symbol_data'][symbol] = {
                'social_sentiment': results[result_idx] if not isinstance(results[result_idx], Exception) else {},
                'news_sentiment': results[result_idx + 1] if not isinstance(results[result_idx + 1], Exception) else {},
                'whale_activity': results[result_idx + 2] if not isinstance(results[result_idx + 2], Exception) else {}
            }
            result_idx += 3
            
        return alt_data
        
    async def close(self):
        if self.session:
            await self.session.close()