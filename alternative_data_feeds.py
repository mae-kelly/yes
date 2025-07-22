import asyncio
import aiohttp
import requests
import numpy as np
import pandas as pd
from datetime import datetime
import time
from typing import Dict, List, Optional

class AlternativeDataFeeds:
    def __init__(self, config: Dict):
        self.config = config
        self.session = None
        self.data_cache = {}
        self.last_update = {}
        
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        
    async def get_fear_greed_index(self) -> float:
        """Get current Fear & Greed Index"""
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
                
        except Exception:
            pass
            
        return self.data_cache.get('fear_greed', 50.0)
        
    async def get_whale_activity(self, symbol: str) -> Dict:
        """Get whale transaction data"""
        try:
            cache_key = f'whale_{symbol}'
            if self._is_cached(cache_key, 900):
                return self.data_cache[cache_key]
                
            whale_api_key = self.config.get('whale_alert_api_key')
            if not whale_api_key:
                return self._generate_synthetic_whale_data()
                
            url = "https://api.whale-alert.io/v1/transactions"
            params = {
                'api_key': whale_api_key,
                'min_value': 100000,
                'limit': 20
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    whale_data = self._process_whale_data(data, symbol)
                else:
                    whale_data = self._generate_synthetic_whale_data()
                    
            self.data_cache[cache_key] = whale_data
            self.last_update[cache_key] = time.time()
            return whale_data
            
        except Exception:
            return self._generate_synthetic_whale_data()
            
    def _process_whale_data(self, data: Dict, symbol: str) -> Dict:
        """Process whale alert API response"""
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
        
    def _generate_synthetic_whale_data(self) -> Dict:
        """Generate synthetic whale data for testing"""
        num_txs = np.random.poisson(3)
        transactions = []
        total_volume = 0
        inflows = 0
        outflows = 0
        
        for _ in range(num_txs):
            amount = np.random.lognormal(12, 1)
            total_volume += amount
            
            if np.random.random() < 0.3:
                inflows += amount
            elif np.random.random() < 0.3:
                outflows += amount
                
        return {
            'whale_transactions': [],
            'total_volume': total_volume,
            'exchange_inflows': inflows,
            'exchange_outflows': outflows,
            'net_flow': outflows - inflows
        }
        
    def _is_cached(self, key: str, ttl: int) -> bool:
        if key not in self.data_cache or key not in self.last_update:
            return False
        return (time.time() - self.last_update[key]) < ttl
        
    async def close(self):
        if self.session:
            await self.session.close()
