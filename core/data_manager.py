import ccxt
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

class SchermanDataManager:
    def __init__(self, config: Dict):
        self.config = config
        self.exchange = self._init_exchange()
        self.cache = {}
        self.cache_duration = 60
        
    def _init_exchange(self):
        return ccxt.okx({
            'apiKey': self.config.get('api_key', ''),
            'secret': self.config.get('secret', ''),
            'password': self.config.get('passphrase', ''),
            'sandbox': self.config.get('sandbox', True),
            'enableRateLimit': True
        })
    
    def get_price_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[pd.DataFrame]:
        cache_key = f"price_{symbol}_{timeframe}_{limit}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv:
                return None
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            self._update_cache(cache_key, df)
            
            return df
            
        except Exception as e:
            print(f"Error fetching price data: {e}")
            return None
    
    def get_fear_greed_index(self) -> List[float]:
        cache_key = "fear_greed"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            response = requests.get('https://api.alternative.me/fng/?limit=10', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                values = [float(item['value']) for item in data['data']]
                
                self._update_cache(cache_key, values)
                return values
            else:
                return [50.0] * 10
                
        except Exception as e:
            print(f"Error fetching fear/greed data: {e}")
            return [50.0] * 10
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        
        age = time.time() - self.cache[key]['timestamp']
        return age < self.cache_duration
    
    def _update_cache(self, key: str, data):
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
