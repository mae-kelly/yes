import ccxt
import numpy as np
import pandas as pd
import os
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
        self.api_keys = {
            'alchemy': os.getenv('ALCHEMY_API_KEY', 'alcht_oZ7wU7JpIoZejlOWUcMFOpNsIlLDsX'),
            'etherscan': os.getenv('ETHERSCAN_API_KEY', 'K4SEVFZ3PI8STM73VKV84C8PYZJUK7HB2G'),
        }
        self.free_apis = {
            'fear_greed': 'https://api.alternative.me/fng/',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'coinpaprika': 'https://api.coinpaprika.com/v1',
            'blockchain_info': 'https://blockchain.info/q',
            'btc_network': 'https://mempool.space/api/v1',
            'btc_network_backup': 'https://blockstream.info/api',
            'crypto_compare': 'https://min-api.cryptocompare.com/data'
        }
        self.monitored_addresses = {
            'binance_hot_1': '0x28C6c06298d514Db089934071355E5743bf21d60',
            'binance_hot_2': '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE',
            'coinbase_cold': '0x71660c4005BA85c37ccec55d0C4493E66Fe775d3',
            'coinbase_hot': '0x503828976D22510aad0201ac7EC88293211D23Da',
            'kraken_exchange': '0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2',
            'ethereum_foundation': '0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe',
            'vitalik_buterin': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
            'whale_1': '0x220866B1A2219f40e72f5c628B65D54268cA3A9D',
            'whale_2': '0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a',
            'defi_whale': '0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503'
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SchermanTradingSystem/2.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
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
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        file_handler = logging.FileHandler('trading_system.log', mode='a')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        return logger
        
    def initialize(self) -> bool:
        try:
            self.logger.info("🚀 Initializing Enterprise Data Manager...")
            self.okx_client.load_markets()
            self.logger.info("✅ OKX client initialized successfully")
            api_status = self._test_all_apis()
            working_apis = sum(1 for status in api_status.values() if status)
            self.logger.info(f"📊 API Status: {working_apis}/{len(api_status)} APIs operational")
            if working_apis < 3:
                self.logger.warning("⚠️ Limited API availability - reduced functionality")
            if self._test_alchemy_connection():
                self.logger.info("✅ Alchemy API operational")
            else:
                self.logger.warning("⚠️ Alchemy API not available")
            if self._test_etherscan_connection():
                self.logger.info("✅ Etherscan API operational")
            else:
                self.logger.warning("⚠️ Etherscan API not available")
            self.logger.info("🎯 Enterprise Data Manager ready for production")
            return True
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            return False
            
    def _test_all_apis(self) -> Dict[str, bool]:
        api_status = {}
        try:
            response = requests.get(self.free_apis['fear_greed'], timeout=5)
            api_status['fear_greed'] = response.status_code == 200
        except:
            api_status['fear_greed'] = False
        try:
            response = requests.get(f"{self.free_apis['coingecko']}/ping", timeout=5)
            api_status['coingecko'] = response.status_code == 200
        except:
            api_status['coingecko'] = False
        try:
            response = requests.get(f"{self.free_apis['btc_network']}/fees/recommended", timeout=5)
            api_status['btc_network'] = response.status_code == 200
        except:
            api_status['btc_network'] = False
        try:
            response = requests.get(f"{self.free_apis['blockchain_info']}/totalbc", timeout=5)
            api_status['blockchain_info'] = response.status_code == 200
        except:
            api_status['blockchain_info'] = False
        return api_status
        
    def _test_alchemy_connection(self) -> bool:
        try:
            url = f"https://eth-mainnet.g.alchemy.com/v2/{self.api_keys['alchemy']}"
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": []
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200 and 'result' in response.json()
        except:
            return False
            
    def _test_etherscan_connection(self) -> bool:
        try:
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'stats',
                'action': 'ethprice',
                'apikey': self.api_keys['etherscan']
            }
            response = requests.get(url, params=params, timeout=10)
            return response.status_code == 200 and response.json().get('status') == '1'
        except:
            return False
            
    def get_historical_data(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        try:
            cache_key = f"hist_{symbol}_{timeframe}_{lookback_days}"
            if self._is_cache_valid(cache_key):
                self.performance_metrics['cache_hits'] += 1
                return self.data_cache[cache_key]['data']
            self.performance_metrics['cache_misses'] += 1
            start_time = time.time()
            since = int((datetime.now() - timedelta(days=lookback_days)).timestamp() * 1000)
            for attempt in range(3):
                try:
                    ohlcv = self.okx_client.fetch_ohlcv(symbol, timeframe, since, limit=1000)
                    if ohlcv and len(ohlcv) > 20:
                        break
                except Exception as e:
                    if attempt == 2:
                        raise e
                    time.sleep(1)
            if not ohlcv or len(ohlcv) < 20:
                self.logger.warning(f"⚠️ Insufficient data for {symbol}")
                return None
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.astype(float)
            df = self._validate_ohlcv_data(df)
            if len(df) < 20:
                self.logger.warning(f"⚠️ Data validation failed for {symbol}")
                return None
            response_time = time.time() - start_time
            self._update_cache(cache_key, df, response_time)
            self.performance_metrics['api_calls_success'] += 1
            return df
        except Exception as e:
            self.performance_metrics['api_calls_failed'] += 1
            self.logger.error(f"❌ Historical data error for {symbol}: {e}")
            return None
            
    def _validate_ohlcv_data(self, df: pd.DataFrame) -> pd.DataFrame:
        original_len = len(df)
        df = df.dropna()
        df = df[df['volume'] > 0]
        df = df[(df['high'] >= df['low']) & 
                (df['high'] >= df['close']) & 
                (df['high'] >= df['open']) &
                (df['low'] <= df['close']) & 
                (df['low'] <= df['open'])]
        returns = df['close'].pct_change().abs()
        df = df[returns < 0.5]
        df = df.sort_index()
        validation_ratio = len(df) / original_len if original_len > 0 else 0
        if validation_ratio < 0.8:
            self.logger.warning(f"⚠️ High data rejection rate: {validation_ratio:.2%}")
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
        old_avg = self.performance_metrics['avg_response_time']
        total_calls = self.performance_metrics['api_calls_total']
        self.performance_metrics['avg_response_time'] = (old_avg * (total_calls - 1) + response_time) / total_calls
        
    def get_enhanced_market_data(self, symbol: str) -> Dict:
        try:
            start_time = time.time()
            ticker = self.okx_client.fetch_ticker(symbol)
            if not ticker:
                return {}
            market_data = {
                'current_price': float(ticker['last']),
                'bid': float(ticker['bid']) if ticker['bid'] else 0,
                'ask': float(ticker['ask']) if ticker['ask'] else 0,
                'volume_24h': float(ticker['baseVolume']) if ticker['baseVolume'] else 0,
                'change_24h': float(ticker['percentage']) if ticker['percentage'] else 0,
                'spread_bps': self._calculate_spread_bps(ticker),
                'timestamp': datetime.now()
            }
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.get_fear_greed_index): 'fear_greed',
                    executor.submit(self.get_coingecko_data, symbol): 'coingecko',
                    executor.submit(self.get_bitcoin_network_metrics): 'btc_network',
                    executor.submit(self.get_alternative_data, symbol): 'alt_data'
                }
                if 'ETH' in symbol:
                    futures[executor.submit(self.get_ethereum_metrics)] = 'eth_metrics'
                for future in as_completed(futures, timeout=10):
                    try:
                        result = future.result(timeout=5)
                        data_type = futures[future]
                        if result:
                            market_data.update(result)
                    except Exception as e:
                        self.logger.warning(f"⚠️ {futures[future]} data fetch failed: {e}")
            market_data['data_quality'] = self._calculate_data_quality(market_data, time.time() - start_time)
            return market_data
        except Exception as e:
            self.logger.error(f"❌ Enhanced market data error for {symbol}: {e}")
            return self.get_basic_market_data(symbol)
            
    def _calculate_spread_bps(self, ticker: Dict) -> float:
        try:
            bid = float(ticker.get('bid', 0))
            ask = float(ticker.get('ask', 0))
            if bid > 0 and ask > 0:
                mid = (bid + ask) / 2
                spread = (ask - bid) / mid * 10000
                return round(spread, 2)
        except:
            pass
        return 0.0
        
    def _calculate_data_quality(self, data: Dict, response_time: float) -> DataQuality:
        sources_available = sum(1 for key in data.keys() if not key.startswith('_'))
        quality_score = min(1.0, sources_available / 15)
        if response_time > 5:
            quality_score *= 0.8
        elif response_time > 10:
            quality_score *= 0.6
        if quality_score > 0.8:
            reliability = 'excellent'
        elif quality_score > 0.6:
            reliability = 'good'
        elif quality_score > 0.4:
            reliability = 'fair'
        else:
            reliability = 'poor'
        return DataQuality(
            score=quality_score,
            sources_available=sources_available,
            latency_ms=response_time * 1000,
            last_update=datetime.now(),
            reliability=reliability
        )
        
    def get_basic_market_data(self, symbol: str) -> Dict:
        try:
            ticker = self.okx_client.fetch_ticker(symbol)
            return {
                'current_price': float(ticker['last']),
                'volume_24h': float(ticker['baseVolume']) if ticker['baseVolume'] else 0,
                'change_24h': float(ticker['percentage']) if ticker['percentage'] else 0,
                'timestamp': datetime.now(),
                'data_quality': DataQuality(0.3, 3, 0, datetime.now(), 'basic')
            }
        except:
            return {}
            
    def get_fear_greed_index(self) -> Dict:
        try:
            response = self.session.get(self.free_apis['fear_greed'], timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                current_fg = float(data['data'][0]['value'])
                historical_fg = []
                for entry in data['data'][:7]:
                    historical_fg.append(float(entry['value']))
                fg_trend = 'neutral'
                if len(historical_fg) >= 3:
                    recent_avg = np.mean(historical_fg[:3])
                    older_avg = np.mean(historical_fg[3:])
                    if recent_avg > older_avg + 5:
                        fg_trend = 'increasing'
                    elif recent_avg < older_avg - 5:
                        fg_trend = 'decreasing'
                return {
                    'fear_greed_index': current_fg,
                    'fear_greed_trend': fg_trend,
                    'fear_greed_7d_avg': np.mean(historical_fg) if historical_fg else current_fg,
                    'fear_greed_volatility': np.std(historical_fg) if len(historical_fg) > 1 else 0
                }
        except Exception as e:
            self.logger.warning(f"⚠️ Fear & Greed API error: {e}")
        return {'fear_greed_index': 50.0}
        
    def get_bitcoin_network_metrics(self) -> Dict:
        try:
            metrics = {}
            try:
                mempool_url = f"{self.free_apis['btc_network']}/mempool"
                response = self.session.get(mempool_url, timeout=10)
                response.raise_for_status()
                mempool_data = response.json()
                metrics.update({
                    'btc_mempool_size': mempool_data.get('count', 0),
                    'btc_mempool_bytes': mempool_data.get('vsize', 0),
                    'btc_mempool_fees': mempool_data.get('total_fee', 0)
                })
                fees_url = f"{self.free_apis['btc_network']}/fees/recommended"
                response = self.session.get(fees_url, timeout=10)
                response.raise_for_status()
                fees_data = response.json()
                metrics.update({
                    'btc_fee_fast': fees_data.get('fastestFee', 0),
                    'btc_fee_standard': fees_data.get('halfHourFee', 0),
                    'btc_fee_economy': fees_data.get('hourFee', 0)
                })
                diff_url = f"{self.free_apis['btc_network']}/difficulty-adjustment"
                response = self.session.get(diff_url, timeout=10)
                response.raise_for_status()
                diff_data = response.json()
                metrics.update({
                    'btc_difficulty_change': diff_data.get('difficultyChange', 0),
                    'btc_blocks_until_retarget': diff_data.get('remainingBlocks', 0)
                })
            except Exception as e:
                self.logger.warning(f"⚠️ Mempool.space API error: {e}")
                try:
                    backup_url = f"{self.free_apis['btc_network_backup']}/mempool"
                    response = self.session.get(backup_url, timeout=10)
                    response.raise_for_status()
                    backup_data = response.json()
                    metrics['btc_mempool_size'] = backup_data.get('count', 0)
                except Exception as backup_e:
                    self.logger.warning(f"⚠️ Backup Bitcoin API also failed: {backup_e}")
            if metrics.get('btc_mempool_size', 0) > 0:
                mempool_size = metrics['btc_mempool_size']
                fast_fee = metrics.get('btc_fee_fast', 0)
                if mempool_size > 150000 or fast_fee > 100:
                    metrics['btc_network_status'] = 'congested'
                elif mempool_size > 75000 or fast_fee > 50:
                    metrics['btc_network_status'] = 'busy'
                else:
                    metrics['btc_network_status'] = 'normal'
                if fast_fee > 75:
                    metrics['btc_fee_pressure'] = 'extreme'
                elif fast_fee > 50:
                    metrics['btc_fee_pressure'] = 'high'
                elif fast_fee > 25:
                    metrics['btc_fee_pressure'] = 'moderate'
                else:
                    metrics['btc_fee_pressure'] = 'low'
            return metrics
        except Exception as e:
            self.logger.error(f"❌ Bitcoin network metrics error: {e}")
            return {}
            
    def get_coingecko_data(self, symbol: str) -> Dict:
        try:
            coin_map = {
                'BTC-USDT-SWAP': 'bitcoin',
                'ETH-USDT-SWAP': 'ethereum',
                'SOL-USDT-SWAP': 'solana',
                'MATIC-USDT-SWAP': 'polygon',
                'AVAX-USDT-SWAP': 'avalanche-2',
                'ADA-USDT-SWAP': 'cardano',
                'DOT-USDT-SWAP': 'polkadot',
                'LINK-USDT-SWAP': 'chainlink'
            }
            coin_id = coin_map.get(symbol, 'bitcoin')
            cg_data = {}
            price_url = f"{self.free_apis['coingecko']}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            response = self.session.get(price_url, params=params, timeout=10)
            response.raise_for_status()
            price_data = response.json()
            if coin_id in price_data:
                coin_data = price_data[coin_id]
                cg_data.update({
                    'cg_market_cap': coin_data.get('usd_market_cap', 0),
                    'cg_volume_24h': coin_data.get('usd_24h_vol', 0),
                    'cg_price_change_24h': coin_data.get('usd_24h_change', 0),
                    'cg_last_updated': coin_data.get('last_updated_at', 0)
                })
            try:
                global_url = f"{self.free_apis['coingecko']}/global"
                response = self.session.get(global_url, timeout=10)
                response.raise_for_status()
                global_data = response.json()
                if 'data' in global_data:
                    global_info = global_data['data']
                    cg_data.update({
                        'crypto_market_cap_usd': global_info.get('total_market_cap', {}).get('usd', 0),
                        'crypto_volume_24h_usd': global_info.get('total_volume', {}).get('usd', 0),
                        'btc_dominance': global_info.get('market_cap_percentage', {}).get('btc', 0),
                        'eth_dominance': global_info.get('market_cap_percentage', {}).get('eth', 0)
                    })
            except Exception as e:
                self.logger.warning(f"⚠️ CoinGecko global data error: {e}")
            return cg_data
        except Exception as e:
            self.logger.warning(f"⚠️ CoinGecko data error: {e}")
            return {}
            
    def get_ethereum_metrics(self) -> Dict:
        try:
            eth_data = {}
            with ThreadPoolExecutor(max_workers=3) as executor:
                gas_future = executor.submit(self._get_gas_metrics)
                network_future = executor.submit(self._get_network_activity)
                whale_future = executor.submit(self._monitor_whale_addresses)
                try:
                    gas_data = gas_future.result(timeout=10)
                    if gas_data:
                        eth_data.update(gas_data)
                except Exception as e:
                    self.logger.warning(f"⚠️ Gas metrics failed: {e}")
                try:
                    network_data = network_future.result(timeout=10)
                    if network_data:
                        eth_data.update(network_data)
                except Exception as e:
                    self.logger.warning(f"⚠️ Network activity failed: {e}")
                try:
                    whale_data = whale_future.result(timeout=10)
                    if whale_data:
                        eth_data['whale_activity'] = whale_data
                except Exception as e:
                    self.logger.warning(f"⚠️ Whale monitoring failed: {e}")
            return eth_data
        except Exception as e:
            self.logger.error(f"❌ Ethereum metrics error: {e}")
            return {}
            
    def _get_gas_metrics(self) -> Dict:
        try:
            gas_data = {}
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'gastracker',
                'action': 'gasoracle',
                'apikey': self.api_keys['etherscan']
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == '1':
                result = data['result']
                gas_data.update({
                    'gas_price_safe': int(result.get('SafeGasPrice', 0)),
                    'gas_price_standard': int(result.get('StandardGasPrice', 0)),
                    'gas_price_fast': int(result.get('FastGasPrice', 0)),
                    'gas_price_propose': float(result.get('ProposeGasPrice', 0))
                })
                fast_gas = gas_data['gas_price_fast']
                if fast_gas > 100:
                    gas_data['gas_environment'] = 'expensive'
                elif fast_gas > 50:
                    gas_data['gas_environment'] = 'moderate'
                elif fast_gas > 20:
                    gas_data['gas_environment'] = 'normal'
                else:
                    gas_data['gas_environment'] = 'cheap'
            return gas_data
        except Exception as e:
            self.logger.warning(f"⚠️ Gas metrics error: {e}")
            return {}
            
    def _get_network_activity(self) -> Dict:
        try:
            alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{self.api_keys['alchemy']}"
            network_data = {}
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "eth_getBlockByNumber",
                "params": ["latest", True]
            }
            response = self.session.post(alchemy_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'result' in data and data['result']:
                block = data['result']
                network_data.update({
                    'eth_block_number': int(block.get('number', '0x0'), 16),
                    'eth_block_size': int(block.get('size', '0x0'), 16),
                    'eth_transaction_count': len(block.get('transactions', [])),
                    'eth_gas_used': int(block.get('gasUsed', '0x0'), 16),
                    'eth_gas_limit': int(block.get('gasLimit', '0x0'), 16)
                })
                gas_used = network_data['eth_gas_used']
                gas_limit = network_data['eth_gas_limit']
                if gas_limit > 0:
                    utilization = gas_used / gas_limit
                    network_data['eth_network_utilization'] = utilization
                    if utilization > 0.95:
                        network_data['eth_network_status'] = 'critical'
                    elif utilization > 0.8:
                        network_data['eth_network_status'] = 'congested'
                    elif utilization > 0.5:
                        network_data['eth_network_status'] = 'active'
                    else:
                        network_data['eth_network_status'] = 'normal'
                transactions = block.get('transactions', [])
                if transactions:
                    total_value = 0
                    high_value_txs = 0
                    for tx in transactions[:50]:
                        try:
                            value = int(tx.get('value', '0x0'), 16)
                            total_value += value
                            if value > 10 * 10**18:
                                high_value_txs += 1
                        except:
                            continue
                    network_data.update({
                        'eth_block_value': total_value / 10**18,
                        'eth_high_value_txs': high_value_txs
                    })
            return network_data
        except Exception as e:
            self.logger.warning(f"⚠️ Network activity error: {e}")
            return {}
            
    def _monitor_whale_addresses(self) -> Dict:
        try:
            whale_activity = {
                'total_balance_eth': 0,
                'balance_changes_24h': 0,
                'large_movements': 0,
                'addresses_monitored': len(self.monitored_addresses),
                'whale_alerts': []
            }
            alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{self.api_keys['alchemy']}"
            for name, address in self.monitored_addresses.items():
                try:
                    payload = {
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "eth_getBalance",
                        "params": [address, "latest"]
                    }
                    response = self.session.post(alchemy_url, json=payload, timeout=5)
                    response.raise_for_status()
                    data = response.json()
                    if 'result' in data:
                        balance_wei = int(data['result'], 16)
                        balance_eth = balance_wei / 10**18
                        whale_activity['total_balance_eth'] += balance_eth
                        cache_key = f"whale_balance_{name}"
                        if cache_key in self.data_cache:
                            old_balance = self.data_cache[cache_key]['balance']
                            balance_change = balance_eth - old_balance
                            if abs(balance_change) > 50:
                                whale_activity['large_movements'] += 1
                                whale_activity['whale_alerts'].append({
                                    'address': name,
                                    'change': balance_change,
                                    'current_balance': balance_eth
                                })
                            whale_activity['balance_changes_24h'] += abs(balance_change)
                        self.data_cache[cache_key] = {
                            'balance': balance_eth,
                            'timestamp': time.time()
                        }
                except Exception as e:
                    self.logger.warning(f"⚠️ Whale monitoring error for {name}: {e}")
                    continue
            if whale_activity['large_movements'] > 3:
                whale_activity['activity_level'] = 'high'
            elif whale_activity['large_movements'] > 1:
                whale_activity['activity_level'] = 'moderate'
            else:
                whale_activity['activity_level'] = 'low'
            return whale_activity
        except Exception as e:
            self.logger.error(f"❌ Whale monitoring error: {e}")
            return {}
            
    def get_alternative_data(self, symbol: str) -> Dict:
        try:
            alt_data = {}
            fg_data = self.get_fear_greed_index()
            alt_data.update(fg_data)
            market_structure = self._analyze_market_structure(symbol)
            alt_data.update(market_structure)
            correlations = self._get_basic_correlations(symbol)
            alt_data.update(correlations)
            return alt_data
        except Exception as e:
            self.logger.warning(f"⚠️ Alternative data error: {e}")
            return {}
            
    def _analyze_market_structure(self, symbol: str) -> Dict:
        try:
            orderbook = self.okx_client.fetch_order_book(symbol, limit=20)
            if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
                return {}
            structure_data = {}
            best_bid = orderbook['bids'][0][0]
            best_ask = orderbook['asks'][0][0]
            mid_price = (best_bid + best_ask) / 2
            spread_bps = ((best_ask - best_bid) / mid_price) * 10000
            structure_data.update({
                'spread_bps': spread_bps,
                'mid_price': mid_price,
                'orderbook_imbalance': self._calculate_orderbook_imbalance(orderbook)
            })
            bid_depth = sum(bid[1] for bid in orderbook['bids'][:10])
            ask_depth = sum(ask[1] for ask in orderbook['asks'][:10])
            structure_data.update({
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'depth_ratio': bid_depth / ask_depth if ask_depth > 0 else 1
            })
            return structure_data
        except Exception as e:
            self.logger.warning(f"⚠️ Market structure analysis error: {e}")
            return {}
            
    def _calculate_orderbook_imbalance(self, orderbook: Dict) -> float:
        try:
            total_bid_size = sum(bid[1] for bid in orderbook['bids'][:10])
            total_ask_size = sum(ask[1] for ask in orderbook['asks'][:10])
            if total_bid_size + total_ask_size == 0:
                return 0
            imbalance = (total_bid_size - total_ask_size) / (total_bid_size + total_ask_size)
            return round(imbalance, 4)
        except:
            return 0
            
    def _get_basic_correlations(self, symbol: str) -> Dict:
        try:
            correlations = {}
            if 'BTC' in symbol:
                correlations['correlation_eth'] = 0.7
                correlations['correlation_traditional'] = -0.1
            elif 'ETH' in symbol:
                correlations['correlation_btc'] = 0.7
                correlations['correlation_traditional'] = -0.05
            return correlations
        except Exception as e:
            self.logger.warning(f"⚠️ Correlation analysis error: {e}")
            return {}
            
    def get_comprehensive_signal_data(self, symbol: str) -> Dict:
        try:
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=3) as executor:
                hist_future = executor.submit(self.get_historical_data, symbol, '1h', 100)
                market_future = executor.submit(self.get_enhanced_market_data, symbol)
                regime_future = executor.submit(self.get_market_regime_indicators)
                historical_data = None
                market_data = {}
                regime_data = {}
                try:
                    historical_data = hist_future.result(timeout=15)
                except Exception as e:
                    self.logger.error(f"❌ Historical data failed: {e}")
                try:
                    market_data = market_future.result(timeout=15)
                except Exception as e:
                    self.logger.error(f"❌ Market data failed: {e}")
                try:
                    regime_data = regime_future.result(timeout=10)
                except Exception as e:
                    self.logger.error(f"❌ Regime data failed: {e}")
            if historical_data is not None and len(historical_data) > 50:
                technical_indicators = self._calculate_advanced_technicals(historical_data)
                market_data.update(technical_indicators)
            total_time = time.time() - start_time
            return {
                'historical_data': historical_data,
                'market_data': market_data,
                'regime_data': regime_data,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'processing_time': total_time,
                'data_completeness': len(market_data) / 30
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
            
    def _calculate_advanced_technicals(self, df: pd.DataFrame) -> Dict:
        try:
            indicators = {}
            if len(df) < 20:
                return indicators
            returns = df['close'].pct_change().dropna()
            indicators.update({
                'volatility_1h': returns.std() * np.sqrt(24),
                'volatility_24h': returns.tail(24).std() * np.sqrt(24) if len(returns) >= 24 else returns.std() * np.sqrt(24),
                'skewness': returns.skew() if len(returns) > 10 else 0,
                'kurtosis': returns.kurtosis() if len(returns) > 10 else 0
            })
            if len(df) >= 12:
                indicators['momentum_6h'] = (df['close'].iloc[-1] / df['close'].iloc[-7] - 1) * 100
                indicators['momentum_12h'] = (df['close'].iloc[-1] / df['close'].iloc[-13] - 1) * 100
            if len(df) >= 24:
                recent_volume = df['volume'].tail(6).mean()
                baseline_volume = df['volume'].tail(24).mean()
                indicators['volume_ratio'] = recent_volume / baseline_volume if baseline_volume > 0 else 1
            indicators.update({
                'price_vs_24h_high': (df['close'].iloc[-1] / df['high'].tail(24).max() - 1) * 100,
                'price_vs_24h_low': (df['close'].iloc[-1] / df['low'].tail(24).min() - 1) * 100
            })
            return indicators
        except Exception as e:
            self.logger.warning(f"⚠️ Technical indicators error: {e}")
            return {}
            
    def get_market_regime_indicators(self) -> Dict:
        try:
            regime_indicators = {}
            with ThreadPoolExecutor(max_workers=4) as executor:
                fg_future = executor.submit(self.get_fear_greed_index)
                btc_future = executor.submit(self.get_bitcoin_network_metrics)
                cg_future = executor.submit(self.get_coingecko_data, 'BTC-USDT-SWAP')
                fg_data = {}
                btc_data = {}
                cg_data = {}
                try:
                    fg_data = fg_future.result(timeout=10)
                except:
                    pass
                try:
                    btc_data = btc_future.result(timeout=10)
                except:
                    pass
                try:
                    cg_data = cg_future.result(timeout=10)
                except:
                    pass
            fg_index = fg_data.get('fear_greed_index', 50)
            if fg_index < 20:
                sentiment = 'extreme_fear'
                sentiment_score = -2
            elif fg_index < 35:
                sentiment = 'fear'
                sentiment_score = -1
            elif fg_index < 65:
                sentiment = 'neutral'
                sentiment_score = 0
            elif fg_index < 80:
                sentiment = 'greed'
                sentiment_score = 1
            else:
                sentiment = 'extreme_greed'
                sentiment_score = 2
            regime_indicators.update({
                'market_sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'fear_greed_index': fg_index
            })
            if btc_data:
                mempool_size = btc_data.get('btc_mempool_size', 0)
                fast_fee = btc_data.get('btc_fee_fast', 0)
                network_score = 0
                if mempool_size > 150000:
                    network_score += 2
                elif mempool_size > 75000:
                    network_score += 1
                if fast_fee > 75:
                    network_score += 2
                elif fast_fee > 30:
                    network_score += 1
                regime_indicators.update({
                    'btc_network_activity': 'high' if network_score >= 3 else 'medium' if network_score >= 1 else 'low',
                    'network_activity_score': network_score
                })
            if cg_data:
                btc_dominance = cg_data.get('btc_dominance', 0)
                if btc_dominance > 60:
                    dominance_regime = 'btc_dominance'
                elif btc_dominance < 40:
                    dominance_regime = 'altcoin_season'
                else:
                    dominance_regime = 'balanced'
                regime_indicators['dominance_regime'] = dominance_regime
            total_score = sentiment_score + regime_indicators.get('network_activity_score', 0)
            if total_score <= -2:
                market_regime = 'bear_market'
            elif total_score >= 3:
                market_regime = 'bull_market'
            elif abs(total_score) <= 1:
                market_regime = 'sideways'
            else:
                market_regime = 'transitional'
            regime_indicators['overall_regime'] = market_regime
            return regime_indicators
        except Exception as e:
            self.logger.error(f"❌ Market regime indicators error: {e}")
            return {'market_sentiment': 'neutral', 'overall_regime': 'sideways'}
            
    def get_performance_summary(self) -> Dict:
        return {
            'api_calls_total': self.performance_metrics['api_calls_total'],
            'success_rate': (self.performance_metrics['api_calls_success'] / 
                           max(1, self.performance_metrics['api_calls_total'])) * 100,
            'cache_hit_rate': (self.performance_metrics['cache_hits'] / 
                             max(1, self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses'])) * 100,
            'avg_response_time': self.performance_metrics['avg_response_time'],
            'cache_size': len(self.data_cache),
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        }
        
    def health_check(self) -> Dict:
        try:
            start_time = time.time()
            health_status = {
                'overall': 'healthy',
                'components': {},
                'timestamp': datetime.now(),
                'response_time': 0
            }
            try:
                self.okx_client.fetch_ticker('BTC-USDT-SWAP')
                health_status['components']['okx'] = 'healthy'
            except:
                health_status['components']['okx'] = 'unhealthy'
                health_status['overall'] = 'degraded'
            api_tests = self._test_all_apis()
            working_apis = sum(1 for status in api_tests.values() if status)
            if working_apis >= 3:
                health_status['components']['free_apis'] = 'healthy'
            elif working_apis >= 1:
                health_status['components']['free_apis'] = 'degraded'
                health_status['overall'] = 'degraded'
            else:
                health_status['components']['free_apis'] = 'unhealthy'
                health_status['overall'] = 'unhealthy'
            alchemy_ok = self._test_alchemy_connection()
            etherscan_ok = self._test_etherscan_connection()
            if alchemy_ok and etherscan_ok:
                health_status['components']['premium_apis'] = 'healthy'
            elif alchemy_ok or etherscan_ok:
                health_status['components']['premium_apis'] = 'degraded'
            else:
                health_status['components']['premium_apis'] = 'unhealthy'
            health_status['response_time'] = time.time() - start_time
            return health_status
        except Exception as e:
            return {
                'overall': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now()
            }
