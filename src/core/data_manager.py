import os
from dotenv import load_dotenv
load_dotenv()

import ccxt
import numpy as np
import pandas as pd
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
import time
from typing import Dict, Optional, List, Tuple
import warnings
import logging
from dataclasses import dataclass
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

warnings.filterwarnings('ignore')

@dataclass
class DataQuality:
    score: float
    sources_available: int
    latency_ms: float
    last_update: datetime
    reliability: str

class EnterpriseDataManager:
    def __init__(self, config: Dict, okx_client):
        self.config = config
        self.okx_client = okx_client
        self.data_cache = {}
        self.cache_metadata = {}
        self.max_cache_age = 300
        self.logger = self._setup_logging()
        
        # API keys from environment
        self.api_keys = {
            'alchemy': os.getenv('ALCHEMY_API_KEY', ''),
            'etherscan': os.getenv('ETHERSCAN_API_KEY', ''),
        }
        
        # Free API endpoints
        self.free_apis = {
            'fear_greed': 'https://api.alternative.me/fng/',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'coinpaprika': 'https://api.coinpaprika.com/v1',
            'blockchain_info': 'https://blockchain.info/q',
            'btc_network': 'https://mempool.space/api/v1',
            'crypto_compare': 'https://min-api.cryptocompare.com/data'
        }
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SchermanTradingSystem/2.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        # Performance metrics
        self.performance_metrics = {
            'api_calls_total': 0,
            'api_calls_success': 0,
            'api_calls_failed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_response_time': 0.0
        }
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('SchermanDataManager')
        logger.setLevel(logging.INFO)
        
        # Only add handler if not already present
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
        
    def initialize(self) -> bool:
        try:
            self.logger.info("🚀 Initializing Enterprise Data Manager...")
            
            # Test OKX client
            if hasattr(self.okx_client, 'load_markets'):
                self.okx_client.load_markets()
                self.logger.info("✅ OKX client initialized successfully")
            
            # Test API connectivity
            api_status = self._test_free_apis()
            working_apis = sum(1 for status in api_status.values() if status)
            self.logger.info(f"📊 API Status: {working_apis}/{len(api_status)} APIs operational")
            
            self.logger.info("🎯 Enterprise Data Manager ready")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            return False
            
    def _test_free_apis(self) -> Dict[str, bool]:
        api_status = {}
        
        # Test Fear & Greed API
        try:
            response = requests.get(self.free_apis['fear_greed'], timeout=5)
            api_status['fear_greed'] = response.status_code == 200
        except:
            api_status['fear_greed'] = False
            
        # Test CoinGecko API
        try:
            response = requests.get(f"{self.free_apis['coingecko']}/ping", timeout=5)
            api_status['coingecko'] = response.status_code == 200
        except:
            api_status['coingecko'] = False
            
        return api_status
        
    def get_historical_data(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        try:
            # Cache check
            cache_key = f"hist_{symbol}_{timeframe}_{lookback_days}"
            if self._is_cache_valid(cache_key):
                self.performance_metrics['cache_hits'] += 1
                return self.data_cache[cache_key]['data']
            
            self.performance_metrics['cache_misses'] += 1
            
            # Get data from exchange
            since = int((datetime.now() - timedelta(days=lookback_days)).timestamp() * 1000)
            
            ohlcv = self.okx_client.fetch_ohlcv(symbol, timeframe, since, limit=1000)
            
            if not ohlcv or len(ohlcv) < 20:
                self.logger.warning(f"⚠️ Insufficient data for {symbol}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.astype(float)
            
            # Validate data
            df = self._validate_ohlcv_data(df)
            
            if len(df) < 20:
                self.logger.warning(f"⚠️ Data validation failed for {symbol}")
                return None
                
            # Cache the result
            self._update_cache(cache_key, df, 0.1)
            self.performance_metrics['api_calls_success'] += 1
            
            return df
            
        except Exception as e:
            self.performance_metrics['api_calls_failed'] += 1
            self.logger.error(f"❌ Historical data error for {symbol}: {e}")
            return None
            
    def _validate_ohlcv_data(self, df: pd.DataFrame) -> pd.DataFrame:
        original_len = len(df)
        
        # Remove invalid data
        df = df.dropna()
        df = df[df['volume'] > 0]
        df = df[(df['high'] >= df['low']) & 
                (df['high'] >= df['close']) & 
                (df['high'] >= df['open']) &
                (df['low'] <= df['close']) & 
                (df['low'] <= df['open'])]
        
        # Remove extreme outliers
        returns = df['close'].pct_change().abs()
        df = df[returns < 0.5]
        
        df = df.sort_index()
        
        return df
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        if cache_key not in self.data_cache:
            return False
        metadata = self.cache_metadata.get(cache_key, {})
        cache_age = time.time() - metadata.get('timestamp', 0)
        return cache_age < self.max_cache_age
        
    def _update_cache(self, cache_key: str, data, response_time: float):
        self.data_cache[cache_key] = {'data': data}
        self.cache_metadata[cache_key] = {
            'timestamp': time.time(),
            'response_time': response_time,
            'size': len(data) if hasattr(data, '__len__') else 1
        }
        self.performance_metrics['api_calls_total'] += 1
        
    def get_enhanced_market_data(self, symbol: str) -> Dict:
        try:
            # Get basic ticker data
            ticker = self.okx_client.fetch_ticker(symbol)
            
            if not ticker:
                return {}
                
            market_data = {
                'current_price': float(ticker['last']),
                'bid': float(ticker['bid']) if ticker['bid'] else 0,
                'ask': float(ticker['ask']) if ticker['ask'] else 0,
                'volume_24h': float(ticker['baseVolume']) if ticker['baseVolume'] else 0,
                'change_24h': float(ticker['percentage']) if ticker['percentage'] else 0,
                'timestamp': datetime.now()
            }
            
            # Add fear/greed index
            try:
                fg_data = self._get_fear_greed_safe()
                market_data['fear_greed_index'] = fg_data
            except:
                market_data['fear_greed_index'] = 50  # Neutral fallback
                
            return market_data
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced market data error for {symbol}: {e}")
            return {}
            
    def _get_fear_greed_safe(self) -> float:
        try:
            response = self.session.get(self.free_apis['fear_greed'], timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return float(data['data'][0]['value'])
        except:
            pass
        return 50.0  # Neutral fallback
        
    def get_comprehensive_signal_data(self, symbol: str) -> Dict:
        try:
            historical_data = self.get_historical_data(symbol, '1h', 7)
            market_data = self.get_enhanced_market_data(symbol)
            
            return {
                'historical_data': historical_data,
                'market_data': market_data,
                'regime_data': {'overall_regime': 'sideways', 'sentiment_score': 0},
                'symbol': symbol,
                'timestamp': datetime.now(),
                'processing_time': 0.1,
                'data_completeness': 0.8 if historical_data is not None else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive signal data error for {symbol}: {e}")
            return {
                'historical_data': None,
                'market_data': {},
                'regime_data': {},
                'symbol': symbol,
                'timestamp': datetime.now(),
                'processing_time': 0,
                'data_completeness': 0
            }
            
    def health_check(self) -> Dict:
        try:
            health_status = {
                'overall': 'healthy',
                'components': {},
                'timestamp': datetime.now(),
                'response_time': 0
            }
            
            # Test OKX
            try:
                self.okx_client.fetch_ticker('BTC-USDT-SWAP')
                health_status['components']['okx'] = 'healthy'
            except:
                health_status['components']['okx'] = 'degraded'
                health_status['overall'] = 'degraded'
                
            # Test free APIs
            api_tests = self._test_free_apis()
            working_apis = sum(1 for status in api_tests.values() if status)
            
            if working_apis >= 2:
                health_status['components']['free_apis'] = 'healthy'
            elif working_apis >= 1:
                health_status['components']['free_apis'] = 'degraded'
                health_status['overall'] = 'degraded'
            else:
                health_status['components']['free_apis'] = 'unhealthy'
                health_status['overall'] = 'degraded'
                
            return health_status
            
        except Exception as e:
            return {
                'overall': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now()
            }
            
    def get_performance_summary(self) -> Dict:
        return {
            'api_calls_total': self.performance_metrics['api_calls_total'],
            'success_rate': (self.performance_metrics['api_calls_success'] / 
                           max(1, self.performance_metrics['api_calls_total'])) * 100,
            'cache_hit_rate': (self.performance_metrics['cache_hits'] / 
                             max(1, self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses'])) * 100,
            'avg_response_time': self.performance_metrics['avg_response_time']
        }
