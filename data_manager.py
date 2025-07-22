import ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import asyncio
import aiohttp
import requests
import json
from typing import Dict, List, Optional, Tuple
import warnings
import getpass
warnings.filterwarnings('ignore')

class CryptoDataManager:
    def __init__(self, config: Dict, okx_client):
        self.config = config
        self.okx_client = okx_client
        self.data_cache = {}
        self.api_keys = self._get_api_keys()
        
    def _get_api_keys(self):
        print("\n🔑 Setting up alternative data API keys...")
        
        whale_key = input("Whale Alert API Key (press Enter to skip): ").strip()
        news_key = input("NewsAPI Key (press Enter to skip): ").strip()
        lunarcrush_key = input("LunarCrush API Key (press Enter to skip): ").strip()
        
        return {
            'whale_alert': whale_key if whale_key else None,
            'newsapi': news_key if news_key else None,
            'lunarcrush': lunarcrush_key if lunarcrush_key else None
        }
        
    def initialize(self):
        try:
            self.okx_client.load_markets()
            print("✅ OKX client initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            return False
            
    def get_historical_data(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        try:
            cache_key = f"{symbol}_{timeframe}_{lookback_days}"
            
            if cache_key in self.data_cache:
                cached_data = self.data_cache[cache_key]
                if time.time() - cached_data['timestamp'] < 300:
                    return cached_data['data']
                    
            since = int((datetime.now() - timedelta(days=lookback_days)).timestamp() * 1000)
            
            all_data = []
            current_since = since
            
            while len(all_data) < lookback_days * 24:
                try:
                    ohlcv = self.okx_client.fetch_ohlcv(symbol, timeframe, current_since, 1000)
                    
                    if not ohlcv:
                        break
                        
                    all_data.extend(ohlcv)
                    
                    if len(ohlcv) < 1000:
                        break
                        
                    current_since = ohlcv[-1][0] + 1
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"❌ Error fetching batch: {e}")
                    break
                    
            if not all_data:
                return None
                
            df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.astype(float)
            
            # Data validation
            df = df.drop_duplicates()
            df = df.sort_index()
            df = df[(df['high'] >= df['low']) & (df['high'] >= df['open']) & (df['high'] >= df['close'])]
            df = df[(df['low'] <= df['open']) & (df['low'] <= df['close'])]
            df = df[df['volume'] >= 0]
            
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].replace(0, np.nan)
                
            df = df.dropna()
            
            self.data_cache[cache_key] = {
                'data': df,
                'timestamp': time.time()
            }
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
            return None
            
    def get_fear_greed_index(self) -> float:
        try:
            response = requests.get("https://api.alternative.me/fng/", timeout=10)
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                return float(data['data'][0]['value'])
                
        except Exception as e:
            print(f"❌ Fear & Greed API error: {e}")
            
        return 50.0
            
    def get_whale_alerts(self, symbol: str) -> Dict:
        if not self.api_keys['whale_alert']:
            return {'whale_transactions': [], 'total_volume': 0, 'net_flow': 0}
            
        try:
            url = "https://api.whale-alert.io/v1/transactions"
            params = {
                'api_key': self.api_keys['whale_alert'],
                'min_value': 100000,
                'limit': 20
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Whale Alert API error: {response.status_code}")
                return {'whale_transactions': [], 'total_volume': 0, 'net_flow': 0}
                
            data = response.json()
            
            if data.get('transactions'):
                transactions = []
                total_volume = 0
                inflows = 0
                outflows = 0
                
                crypto_symbol = symbol.split('-')[0].lower()
                
                for tx in data['transactions']:
                    if crypto_symbol in tx.get('symbol', '').lower():
                        amount_usd = float(tx.get('amount_usd', 0))
                        total_volume += amount_usd
                        
                        from_owner = tx.get('from', {}).get('owner', '').lower()
                        to_owner = tx.get('to', {}).get('owner', '').lower()
                        
                        if 'exchange' in to_owner:
                            inflows += amount_usd
                        elif 'exchange' in from_owner:
                            outflows += amount_usd
                            
                        transactions.append({
                            'amount_usd': amount_usd,
                            'from_owner': from_owner,
                            'to_owner': to_owner,
                            'timestamp': tx.get('timestamp', 0)
                        })
                        
                return {
                    'whale_transactions': transactions,
                    'total_volume': total_volume,
                    'exchange_inflows': inflows,
                    'exchange_outflows': outflows,
                    'net_flow': outflows - inflows
                }
                
        except Exception as e:
            print(f"❌ Whale Alert API error: {e}")
            
        return {'whale_transactions': [], 'total_volume': 0, 'net_flow': 0}
            
    def get_news_sentiment(self, symbol: str) -> Dict:
        if not self.api_keys['newsapi']:
            return {'sentiment_score': 0, 'news_count': 0}
            
        try:
            coin_name = symbol.split('-')[0].lower()
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': f'{coin_name} cryptocurrency',
                'sortBy': 'publishedAt',
                'pageSize': 20,
                'apiKey': self.api_keys['newsapi']
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ NewsAPI error: {response.status_code}")
                return {'sentiment_score': 0, 'news_count': 0}
                
            data = response.json()
            
            if data.get('articles'):
                sentiment_scores = []
                
                for article in data['articles'][:10]:
                    title = article.get('title', '').lower()
                    description = article.get('description', '').lower()
                    text = f"{title} {description}"
                    
                    sentiment = self._analyze_text_sentiment(text)
                    if sentiment != 0:
                        sentiment_scores.append(sentiment)
                        
                if sentiment_scores:
                    avg_sentiment = np.mean(sentiment_scores)
                    return {
                        'sentiment_score': avg_sentiment,
                        'news_count': len(sentiment_scores)
                    }
                    
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
            
        return {'sentiment_score': 0, 'news_count': 0}
        
    def _analyze_text_sentiment(self, text: str) -> float:
        positive_words = ['bull', 'moon', 'pump', 'surge', 'rally', 'breakout', 'up', 'gain', 'rise', 'profit', 'bullish', 'positive', 'growth', 'increase']
        negative_words = ['bear', 'dump', 'crash', 'drop', 'fall', 'down', 'loss', 'decline', 'sell', 'fear', 'bearish', 'negative', 'decrease', 'plunge']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = positive_count + negative_count
        if total_words == 0:
            return 0.0
            
        return (positive_count - negative_count) / total_words
        
    def get_social_sentiment(self, symbol: str) -> Dict:
        if not self.api_keys['lunarcrush']:
            return {'social_score': 50, 'social_volume': 0}
            
        try:
            coin_map = {
                'BTC-USDT-SWAP': 'bitcoin',
                'ETH-USDT-SWAP': 'ethereum',
                'SOL-USDT-SWAP': 'solana'
            }
            
            coin_id = coin_map.get(symbol, 'bitcoin')
            
            headers = {'Authorization': f'Bearer {self.api_keys["lunarcrush"]}'}
            url = f"https://api.lunarcrush.com/v2/assets/{coin_id}/time-series"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ LunarCrush API error: {response.status_code}")
                return {'social_score': 50, 'social_volume': 0}
                
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                latest = data['data'][0]
                return {
                    'social_score': float(latest.get('social_score', 50)),
                    'social_volume': float(latest.get('social_volume', 0)),
                    'sentiment_score': float(latest.get('sentiment', 3.0)),
                    'twitter_mentions': int(latest.get('tweets', 0))
                }
                
        except Exception as e:
            print(f"❌ LunarCrush API error: {e}")
            
        return {'social_score': 50, 'social_volume': 0}
        
    def get_market_data(self, symbol: str) -> Dict:
        try:
            ticker = self.okx_client.fetch_ticker(symbol)
            orderbook = self.okx_client.fetch_order_book(symbol, limit=20)
            
            if not ticker:
                print(f"❌ Failed to fetch ticker for {symbol}")
                return {}
                
            spread = ticker['ask'] - ticker['bid'] if ticker['ask'] and ticker['bid'] else 0
            mid_price = (ticker['ask'] + ticker['bid']) / 2 if ticker['ask'] and ticker['bid'] else ticker['last']
            spread_bps = (spread / mid_price * 10000) if mid_price > 0 else 0
            
            bid_depth = sum([bid[1] for bid in orderbook['bids'][:5]]) if orderbook['bids'] else 0
            ask_depth = sum([ask[1] for ask in orderbook['asks'][:5]]) if orderbook['asks'] else 0
            total_depth = bid_depth + ask_depth
            imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0
            
            fear_greed = self.get_fear_greed_index()
            whale_data = self.get_whale_alerts(symbol)
            news_data = self.get_news_sentiment(symbol)
            social_data = self.get_social_sentiment(symbol)
            
            return {
                'current_price': float(ticker['last']),
                'bid': float(ticker['bid']) if ticker['bid'] else 0,
                'ask': float(ticker['ask']) if ticker['ask'] else 0,
                'spread_bps': spread_bps,
                'volume_24h': float(ticker['baseVolume']) if ticker['baseVolume'] else 0,
                'change_24h': float(ticker['percentage']) if ticker['percentage'] else 0,
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'orderbook_imbalance': imbalance,
                'liquidity_score': min(total_depth / 100000, 1.0),
                'fear_greed_index': fear_greed,
                'whale_net_flow': whale_data.get('net_flow', 0),
                'news_sentiment': news_data.get('sentiment_score', 0),
                'social_sentiment': social_data.get('social_score', 50),
                'volatility': self._calculate_volatility(symbol),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error getting market data for {symbol}: {e}")
            return {}
            
    def _calculate_volatility(self, symbol: str) -> float:
        try:
            data = self.get_historical_data(symbol, '1h', 7)
            if data is None or len(data) < 24:
                return 0.25
                
            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(24 * 365)
            
            return volatility
            
        except Exception:
            return 0.25
            
    def get_alternative_data(self, symbol: str) -> Dict:
        fear_greed = self.get_fear_greed_index()
        whale_data = self.get_whale_alerts(symbol)
        news_data = self.get_news_sentiment(symbol)
        social_data = self.get_social_sentiment(symbol)
        
        return {
            'fear_greed_index': fear_greed,
            'whale_alerts': whale_data,
            'news_sentiment': news_data,
            'social_sentiment': social_data,
            'timestamp': datetime.now()
        }
        
    def test_api_connections(self):
        print("\n🧪 Testing API connections...")
        
        try:
            self.okx_client.fetch_ticker('BTC-USDT-SWAP')
            print("✅ OKX API: Connected")
        except Exception as e:
            print(f"❌ OKX API: {e}")
            
        try:
            fg = self.get_fear_greed_index()
            print(f"✅ Fear & Greed API: {fg}")
        except Exception as e:
            print(f"❌ Fear & Greed API: {e}")
            
        if self.api_keys['whale_alert']:
            try:
                whale = self.get_whale_alerts('BTC-USDT-SWAP')
                print(f"✅ Whale Alert API: {len(whale.get('whale_transactions', []))} transactions")
            except Exception as e:
                print(f"❌ Whale Alert API: {e}")
        else:
            print("⚠️  Whale Alert API: Not configured")
            
        if self.api_keys['newsapi']:
            try:
                news = self.get_news_sentiment('BTC-USDT-SWAP')
                print(f"✅ NewsAPI: {news.get('news_count', 0)} articles")
            except Exception as e:
                print(f"❌ NewsAPI: {e}")
        else:
            print("⚠️  NewsAPI: Not configured")
            
        if self.api_keys['lunarcrush']:
            try:
                social = self.get_social_sentiment('BTC-USDT-SWAP')
                print(f"✅ LunarCrush API: Score {social.get('social_score', 0)}")
            except Exception as e:
                print(f"❌ LunarCrush API: {e}")
        else:
            print("⚠️  LunarCrush API: Not configured")
