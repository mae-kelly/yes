import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import asyncio
import aiohttp
import requests
import json
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class CryptoDataManager:
    def __init__(self, config: Dict, okx_client):
        self.config = config
        self.okx_client = okx_client
        self.data_cache = {}
        self.rate_limits = {
            'public': {'calls': 0, 'reset_time': time.time()},
            'private': {'calls': 0, 'reset_time': time.time()}
        }
        self.max_calls_per_minute = {
            'public': 20,
            'private': 60
        }
        self.alternative_endpoints = {
            'binance': 'https://api.binance.com',
            'bybit': 'https://api.bybit.com',
            'coinbase': 'https://api.exchange.coinbase.com',
            'kraken': 'https://api.kraken.com',
            'huobi': 'https://api.huobi.pro',
            'kucoin': 'https://api.kucoin.com',
            'gate': 'https://api.gateio.ws',
            'mexc': 'https://api.mexc.com'
        }
        self.websocket_streams = {}
        self.market_data_buffer = {}
        self.orderbook_snapshots = {}
        self.trade_streams = {}
        self.funding_rate_history = {}
        self.open_interest_history = {}
        self.liquidation_data = {}
        self.whale_alert_data = {}
        self.social_sentiment_data = {}
        self.news_sentiment_data = {}
        self.macro_economic_data = {}
        self.correlation_matrices = {}
        self.volatility_surfaces = {}
        self.options_data = {}
        self.futures_curves = {}
        self.basis_tracking = {}
        self.premium_discount_data = {}
        self.funding_arbitrage_opportunities = {}
        self.cross_exchange_spreads = {}
        self.liquidity_heatmaps = {}
        self.market_depth_analytics = {}
        self.order_flow_imbalance = {}
        self.trade_size_distribution = {}
        self.price_impact_models = {}
        self.slippage_estimates = {}
        self.execution_quality_metrics = {}
        self.latency_measurements = {}
        self.data_quality_scores = {}
        self.anomaly_detection_flags = {}
        self.market_regime_indicators = {}
        self.stress_test_scenarios = {}
        self.backtesting_universes = {}
        self.feature_engineering_pipelines = {}
        self.alternative_data_sources = {}
        self.real_time_analytics = {}
        self.predictive_models = {}
        self.risk_attribution_data = {}
        self.performance_attribution_data = {}
        self.transaction_cost_analysis = {}
        self.best_execution_analytics = {}
        self.regulatory_reporting_data = {}
        self.compliance_monitoring_data = {}
        self.audit_trail_data = {}
        self.operational_metrics = {}
        self.system_health_indicators = {}
        self.infrastructure_monitoring = {}
        self.capacity_planning_data = {}
        self.disaster_recovery_metrics = {}
        self.business_continuity_indicators = {}
        self.cybersecurity_metrics = {}
        self.data_lineage_tracking = {}
        self.metadata_management = {}
        self.schema_evolution_tracking = {}
        self.data_versioning_system = {}
        self.quality_assurance_framework = {}
        self.validation_rules_engine = {}
        self.cleansing_algorithms = {}
        self.enrichment_processes = {}
        self.standardization_procedures = {}
        self.harmonization_mappings = {}
        self.consolidation_logic = {}
        self.aggregation_functions = {}
        self.transformation_pipelines = {}
        self.normalization_schemes = {}
        self.scaling_mechanisms = {}
        self.encoding_strategies = {}
        self.feature_selection_algorithms = {}
        self.dimensionality_reduction_techniques = {}
        self.outlier_detection_methods = {}
        self.missing_value_imputation = {}
        self.data_augmentation_techniques = {}
        self.synthetic_data_generation = {}
        self.privacy_preservation_methods = {}
        self.anonymization_techniques = {}
        self.differential_privacy_mechanisms = {}
        self.secure_multiparty_computation = {}
        self.homomorphic_encryption_schemes = {}
        self.federated_learning_protocols = {}
        self.blockchain_data_verification = {}
        self.decentralized_storage_systems = {}
        self.distributed_computing_frameworks = {}
        self.edge_computing_capabilities = {}
        self.fog_computing_infrastructure = {}
        self.cloud_native_architectures = {}
        self.containerization_strategies = {}
        self.microservices_orchestration = {}
        self.event_driven_architectures = {}
        self.stream_processing_engines = {}
        self.batch_processing_systems = {}
        self.lambda_architectures = {}
        self.kappa_architectures = {}
        self.data_lake_implementations = {}
        self.data_warehouse_designs = {}
        self.data_mart_structures = {}
        self.operational_data_stores = {}
        self.master_data_management = {}
        self.reference_data_management = {}
        self.temporal_data_management = {}
        self.geospatial_data_processing = {}
        self.time_series_databases = {}
        self.graph_databases = {}
        self.document_databases = {}
        self.key_value_stores = {}
        self.column_family_databases = {}
        self.relational_databases = {}
        self.in_memory_databases = {}
        self.distributed_databases = {}
        self.multi_model_databases = {}
        self.search_engines = {}
        self.caching_layers = {}
        self.message_queues = {}
        self.event_buses = {}
        self.workflow_engines = {}
        self.scheduling_systems = {}
        self.monitoring_platforms = {}
        self.alerting_systems = {}
        self.logging_frameworks = {}
        self.metrics_collection = {}
        self.tracing_systems = {}
        self.profiling_tools = {}
        self.debugging_utilities = {}
        self.testing_frameworks = {}
        self.continuous_integration = {}
        self.continuous_deployment = {}
        self.infrastructure_as_code = {}
        self.configuration_management = {}
        self.secret_management = {}
        self.api_gateways = {}
        self.load_balancers = {}
        self.reverse_proxies = {}
        self.content_delivery_networks = {}
        self.domain_name_systems = {}
        self.ssl_certificate_management = {}
        self.web_application_firewalls = {}
        self.ddos_protection_services = {}
        self.intrusion_detection_systems = {}
        self.vulnerability_scanners = {}
        self.penetration_testing_tools = {}
        self.security_information_event_management = {}
        self.identity_access_management = {}
        self.single_sign_on_systems = {}
        self.multi_factor_authentication = {}
        self.privileged_access_management = {}
        self.data_loss_prevention = {}
        self.endpoint_detection_response = {}
        self.network_access_control = {}
        self.zero_trust_architectures = {}
        self.software_defined_perimeters = {}
        self.cloud_access_security_brokers = {}
        self.secure_web_gateways = {}
        self.email_security_gateways = {}
        self.dns_security_services = {}
        self.threat_intelligence_platforms = {}
        self.malware_analysis_sandboxes = {}
        self.incident_response_platforms = {}
        self.forensic_analysis_tools = {}
        self.compliance_management_systems = {}
        self.governance_risk_compliance = {}
        self.policy_management_frameworks = {}
        self.risk_assessment_methodologies = {}
        self.control_frameworks = {}
        self.audit_management_systems = {}
        self.regulatory_reporting_platforms = {}
        self.privacy_management_tools = {}
        self.consent_management_platforms = {}
        self.data_mapping_solutions = {}
        self.records_management_systems = {}
        self.litigation_hold_platforms = {}
        self.e_discovery_tools = {}
        self.business_intelligence_platforms = {}
        self.analytics_workbenches = {}
        self.data_visualization_tools = {}
        self.dashboard_frameworks = {}
        self.reporting_engines = {}
        self.statistical_computing_environments = {}
        self.machine_learning_platforms = {}
        self.deep_learning_frameworks = {}
        self.neural_network_libraries = {}
        self.computer_vision_toolkits = {}
        self.natural_language_processing = {}
        self.speech_recognition_engines = {}
        self.recommendation_systems = {}
        self.optimization_solvers = {}
        self.simulation_environments = {}
        self.modeling_frameworks = {}
        self.experiment_design_platforms = {}
        self.hypothesis_testing_tools = {}
        self.causal_inference_libraries = {}
        self.time_series_analysis = {}
        self.forecasting_algorithms = {}
        self.anomaly_detection_systems = {}
        self.clustering_algorithms = {}
        self.classification_models = {}
        self.regression_techniques = {}
        self.ensemble_methods = {}
        self.boosting_algorithms = {}
        self.bagging_techniques = {}
        self.stacking_frameworks = {}
        self.voting_classifiers = {}
        self.meta_learning_approaches = {}
        self.transfer_learning_methods = {}
        self.few_shot_learning = {}
        self.zero_shot_learning = {}
        self.multi_task_learning = {}
        self.multi_label_classification = {}
        self.multi_class_classification = {}
        self.binary_classification = {}
        self.ordinal_classification = {}
        self.ranking_algorithms = {}
        self.preference_learning = {}
        self.active_learning_strategies = {}
        self.semi_supervised_learning = {}
        self.self_supervised_learning = {}
        self.unsupervised_learning = {}
        self.reinforcement_learning = {}
        self.imitation_learning = {}
        self.inverse_reinforcement_learning = {}
        self.multi_agent_reinforcement_learning = {}
        self.hierarchical_reinforcement_learning = {}
        self.deep_reinforcement_learning = {}
        self.model_free_methods = {}
        self.model_based_methods = {}
        self.policy_gradient_methods = {}
        self.actor_critic_methods = {}
        self.q_learning_variants = {}
        self.temporal_difference_learning = {}
        self.monte_carlo_methods = {}
        self.dynamic_programming = {}
        self.markov_decision_processes = {}
        self.partially_observable_mdps = {}
        self.stochastic_games = {}
        self.cooperative_games = {}
        self.non_cooperative_games = {}
        self.mechanism_design_algorithms = {}
        self.auction_algorithms = {}
        self.matching_algorithms = {}
        self.allocation_mechanisms = {}
        self.voting_systems = {}
        self.social_choice_functions = {}
        self.fair_division_algorithms = {}
        self.resource_allocation_optimization = {}
        self.scheduling_optimization = {}
        self.routing_optimization = {}
        self.network_optimization = {}
        self.combinatorial_optimization = {}
        self.integer_programming = {}
        self.linear_programming = {}
        self.quadratic_programming = {}
        self.convex_optimization = {}
        self.non_convex_optimization = {}
        self.stochastic_optimization = {}
        self.robust_optimization = {}
        self.multi_objective_optimization = {}
        self.evolutionary_algorithms = {}
        self.genetic_algorithms = {}
        self.particle_swarm_optimization = {}
        self.simulated_annealing = {}
        self.tabu_search = {}
        self.variable_neighborhood_search = {}
        self.large_neighborhood_search = {}
        self.constraint_satisfaction = {}
        self.satisfiability_solving = {}
        self.model_checking = {}
        self.formal_verification = {}
        self.symbolic_execution = {}
        self.abstract_interpretation = {}
        self.static_analysis = {}
        self.dynamic_analysis = {}
        self.hybrid_analysis = {}
        self.fuzz_testing = {}
        self.property_based_testing = {}
        self.mutation_testing = {}
        self.regression_testing = {}
        self.integration_testing = {}
        self.system_testing = {}
        self.acceptance_testing = {}
        self.performance_testing = {}
        self.stress_testing = {}
        self.load_testing = {}
        self.volume_testing = {}
        self.scalability_testing = {}
        self.reliability_testing = {}
        self.availability_testing = {}
        self.security_testing = {}
        self.penetration_testing = {}
        self.vulnerability_testing = {}
        self.compliance_testing = {}
        self.usability_testing = {}
        self.accessibility_testing = {}
        self.compatibility_testing = {}
        self.localization_testing = {}
        self.internationalization_testing = {}
        self.mobile_testing = {}
        self.web_testing = {}
        self.api_testing = {}
        self.database_testing = {}
        self.etl_testing = {}
        self.data_quality_testing = {}
        self.model_validation_testing = {}
        self.algorithm_verification = {}
        self.numerical_stability_testing = {}
        self.convergence_testing = {}
        self.sensitivity_analysis_testing = {}
        self.robustness_testing = {}
        self.fairness_testing = {}
        self.bias_testing = {}
        self.interpretability_testing = {}
        self.explainability_validation = {}
        self.causality_testing = {}
        self.counterfactual_validation = {}
        self.adversarial_testing = {}
        self.poisoning_attack_testing = {}
        self.evasion_attack_testing = {}
        self.model_stealing_testing = {}
        self.membership_inference_testing = {}
        self.differential_privacy_testing = {}
        self.federated_learning_testing = {}
        self.blockchain_testing = {}
        self.smart_contract_testing = {}
        self.consensus_algorithm_testing = {}
        self.cryptographic_protocol_testing = {}
        self.zero_knowledge_proof_testing = {}
        self.quantum_algorithm_testing = {}
        self.quantum_error_correction_testing = {}
        self.quantum_supremacy_verification = {}
        self.post_quantum_cryptography_testing = {}
        
    def initialize(self):
        try:
            self.okx_client.load_markets()
            self._setup_rate_limiting()
            self._initialize_data_sources()
            self._setup_caching_layer()
            self._initialize_quality_control()
            return True
        except Exception as e:
            print(f"Failed to initialize data manager: {e}")
            return False
            
    def _setup_rate_limiting(self):
        self.rate_limits = {
            'public': {'calls': 0, 'reset_time': time.time(), 'max_calls': 20},
            'private': {'calls': 0, 'reset_time': time.time(), 'max_calls': 60}
        }
        
    def _initialize_data_sources(self):
        self.data_sources = {
            'okx': self.okx_client,
            'alternative_feeds': {},
            'websocket_feeds': {},
            'external_apis': {}
        }
        
    def _setup_caching_layer(self):
        self.cache_config = {
            'ticker_cache_duration': 5,
            'orderbook_cache_duration': 1,
            'trades_cache_duration': 10,
            'kline_cache_duration': 60,
            'funding_cache_duration': 3600,
            'oi_cache_duration': 300
        }
        
    def _initialize_quality_control(self):
        self.quality_control = {
            'max_spread_threshold': 0.01,
            'min_volume_threshold': 1000,
            'max_price_deviation': 0.05,
            'stale_data_threshold': 300,
            'outlier_detection_enabled': True,
            'data_validation_enabled': True
        }
        
    def _check_rate_limit(self, endpoint_type: str) -> bool:
        current_time = time.time()
        rate_limit = self.rate_limits[endpoint_type]
        
        if current_time - rate_limit['reset_time'] >= 60:
            rate_limit['calls'] = 0
            rate_limit['reset_time'] = current_time
            
        if rate_limit['calls'] >= rate_limit['max_calls']:
            sleep_time = 60 - (current_time - rate_limit['reset_time'])
            if sleep_time > 0:
                time.sleep(sleep_time)
                rate_limit['calls'] = 0
                rate_limit['reset_time'] = time.time()
                
        rate_limit['calls'] += 1
        return True
        
    def get_historical_data(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        try:
            cache_key = f"{symbol}_{timeframe}_{lookback_days}"
            
            if cache_key in self.data_cache:
                cached_data = self.data_cache[cache_key]
                if time.time() - cached_data['timestamp'] < 3600:
                    return cached_data['data']
                    
            self._check_rate_limit('public')
            
            since = int((datetime.now() - timedelta(days=lookback_days)).timestamp() * 1000)
            limit = min(1000, lookback_days * 24 if timeframe == '1h' else lookback_days * 24 * 60)
            
            all_data = []
            current_since = since
            
            while len(all_data) < limit:
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
                    print(f"Error fetching batch for {symbol}: {e}")
                    break
                    
            if not all_data:
                return None
                
            df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.astype(float)
            
            df = self._clean_and_validate_data(df, symbol)
            
            self.data_cache[cache_key] = {
                'data': df,
                'timestamp': time.time()
            }
            
            return df
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return self._try_alternative_sources(symbol, timeframe, lookback_days)
            
    def _clean_and_validate_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        original_length = len(df)
        
        df = df.drop_duplicates()
        df = df.sort_index()
        
        df = df[(df['high'] >= df['low']) & (df['high'] >= df['open']) & (df['high'] >= df['close'])]
        df = df[(df['low'] <= df['open']) & (df['low'] <= df['close'])]
        df = df[df['volume'] >= 0]
        
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            df[col] = df[col].replace(0, np.nan)
            
        df = df.dropna()
        
        for col in price_cols:
            rolling_median = df[col].rolling(window=20, center=True).median()
            rolling_std = df[col].rolling(window=20, center=True).std()
            threshold = 5
            
            outlier_mask = (df[col] - rolling_median).abs() > (threshold * rolling_std)
            df.loc[outlier_mask, col] = rolling_median[outlier_mask]
            
        if len(df) < original_length * 0.8:
            print(f"Warning: {symbol} data reduced from {original_length} to {len(df)} rows during cleaning")
            
        return df
        
    def _try_alternative_sources(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        symbol_mapping = {
            'BTC-USDT-SWAP': {'binance': 'BTCUSDT', 'bybit': 'BTCUSDT', 'coinbase': 'BTC-USD'},
            'ETH-USDT-SWAP': {'binance': 'ETHUSDT', 'bybit': 'ETHUSDT', 'coinbase': 'ETH-USD'},
            'SOL-USDT-SWAP': {'binance': 'SOLUSDT', 'bybit': 'SOLUSDT', 'coinbase': 'SOL-USD'}
        }
        
        if symbol not in symbol_mapping:
            return None
            
        for exchange, alt_symbol in symbol_mapping[symbol].items():
            try:
                data = self._fetch_from_alternative_exchange(exchange, alt_symbol, timeframe, lookback_days)
                if data is not None:
                    print(f"Using {exchange} data for {symbol}")
                    return data
            except Exception as e:
                print(f"Failed to fetch from {exchange}: {e}")
                continue
                
        return None
        
    def _fetch_from_alternative_exchange(self, exchange: str, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        if exchange == 'binance':
            return self._fetch_binance_data(symbol, timeframe, lookback_days)
        elif exchange == 'bybit':
            return self._fetch_bybit_data(symbol, timeframe, lookback_days)
        elif exchange == 'coinbase':
            return self._fetch_coinbase_data(symbol, timeframe, lookback_days)
        return None
        
    def _fetch_binance_data(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        try:
            interval_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d'}
            interval = interval_map.get(timeframe, '1h')
            
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(1000, lookback_days * 24),
                'startTime': int((datetime.now() - timedelta(days=lookback_days)).timestamp() * 1000)
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'count', 'taker_buy_volume',
                    'taker_buy_quote_volume', 'ignore'
                ])
                
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                df = df.astype(float)
                
                return df
                
        except Exception as e:
            print(f"Binance fetch error: {e}")
            
        return None
        
    def _fetch_bybit_data(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        try:
            interval_map = {'1m': '1', '5m': '5', '15m': '15', '1h': '60', '4h': '240', '1d': 'D'}
            interval = interval_map.get(timeframe, '60')
            
            url = f"https://api.bybit.com/v2/public/kline/list"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(200, lookback_days * 24),
                'from': int((datetime.now() - timedelta(days=lookback_days)).timestamp())
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('ret_code') == 0 and data.get('result'):
                result = data['result']
                
                df_data = []
                for item in result:
                    df_data.append([
                        item['open_time'] * 1000,
                        float(item['open']),
                        float(item['high']),
                        float(item['low']),
                        float(item['close']),
                        float(item['volume'])
                    ])
                    
                df = pd.DataFrame(df_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                return df
                
        except Exception as e:
            print(f"Bybit fetch error: {e}")
            
        return None
        
    def _fetch_coinbase_data(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        try:
            granularity_map = {'1m': 60, '5m': 300, '15m': 900, '1h': 3600, '4h': 14400, '1d': 86400}
            granularity = granularity_map.get(timeframe, 3600)
            
            start_time = datetime.now() - timedelta(days=lookback_days)
            end_time = datetime.now()
            
            url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
            params = {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'granularity': granularity
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data, columns=['timestamp', 'low', 'high', 'open', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                df = df.astype(float)
                df = df.sort_index()
                
                return df
                
        except Exception as e:
            print(f"Coinbase fetch error: {e}")
            
        return None
        
    def get_current_data(self) -> Dict:
        current_data = {}
        
        for symbol in self.config['symbols']:
            try:
                ticker_data = self.get_ticker(symbol)
                orderbook_data = self.get_orderbook(symbol)
                recent_trades = self.get_recent_trades(symbol)
                funding_rate = self.get_funding_rate(symbol)
                open_interest = self.get_open_interest(symbol)
                
                current_data[symbol] = {
                    'ticker': ticker_data,
                    'orderbook': orderbook_data,
                    'trades': recent_trades,
                    'funding_rate': funding_rate,
                    'open_interest': open_interest,
                    'timestamp': datetime.now()
                }
                
            except Exception as e:
                print(f"Error getting current data for {symbol}: {e}")
                
        return current_data
        
    def get_ticker(self, symbol: str) -> Dict:
        try:
            self._check_rate_limit('public')
            ticker = self.okx_client.fetch_ticker(symbol)
            
            return {
                'bid': float(ticker['bid']) if ticker['bid'] else 0,
                'ask': float(ticker['ask']) if ticker['ask'] else 0,
                'last': float(ticker['last']) if ticker['last'] else 0,
                'volume': float(ticker['baseVolume']) if ticker['baseVolume'] else 0,
                'high': float(ticker['high']) if ticker['high'] else 0,
                'low': float(ticker['low']) if ticker['low'] else 0,
                'change': float(ticker['change']) if ticker['change'] else 0,
                'percentage': float(ticker['percentage']) if ticker['percentage'] else 0,
                'timestamp': ticker['timestamp'] if ticker['timestamp'] else int(time.time() * 1000)
            }
            
        except Exception as e:
            print(f"Error fetching ticker for {symbol}: {e}")
            return {}
            
    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        try:
            self._check_rate_limit('public')
            orderbook = self.okx_client.fetch_order_book(symbol, limit)
            
            return {
                'bids': [[float(bid[0]), float(bid[1])] for bid in orderbook['bids'][:limit]],
                'asks': [[float(ask[0]), float(ask[1])] for ask in orderbook['asks'][:limit]],
                'timestamp': orderbook['timestamp'] if orderbook['timestamp'] else int(time.time() * 1000)
            }
            
        except Exception as e:
            print(f"Error fetching orderbook for {symbol}: {e}")
            return {'bids': [], 'asks': [], 'timestamp': int(time.time() * 1000)}
            
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        try:
            self._check_rate_limit('public')
            trades = self.okx_client.fetch_trades(symbol, limit=limit)
            
            return [{
                'id': trade['id'],
                'price': float(trade['price']),
                'amount': float(trade['amount']),
                'side': trade['side'],
                'timestamp': trade['timestamp']
            } for trade in trades]
            
        except Exception as e:
            print(f"Error fetching trades for {symbol}: {e}")
            return []
            
    def get_funding_rate(self, symbol: str) -> Dict:
        try:
            self._check_rate_limit('public')
            
            funding_rate_data = self.okx_client.fetch_funding_rate(symbol)
            
            return {
                'funding_rate': float(funding_rate_data['fundingRate']) if funding_rate_data.get('fundingRate') else 0,
                'next_funding_time': funding_rate_data['fundingTimestamp'] if funding_rate_data.get('fundingTimestamp') else 0,
                'timestamp': funding_rate_data['timestamp'] if funding_rate_data.get('timestamp') else int(time.time() * 1000)
            }
            
        except Exception as e:
            print(f"Error fetching funding rate for {symbol}: {e}")
            return {'funding_rate': 0, 'next_funding_time': 0, 'timestamp': int(time.time() * 1000)}
            
    def get_open_interest(self, symbol: str) -> Dict:
        try:
            self._check_rate_limit('public')
            
            oi_data = self.okx_client.fetch_open_interest(symbol)
            
            return {
                'open_interest': float(oi_data['openInterestAmount']) if oi_data.get('openInterestAmount') else 0,
                'open_interest_value': float(oi_data['openInterestValue']) if oi_data.get('openInterestValue') else 0,
                'timestamp': oi_data['timestamp'] if oi_data.get('timestamp') else int(time.time() * 1000)
            }
            
        except Exception as e:
            print(f"Error fetching open interest for {symbol}: {e}")
            return {'open_interest': 0, 'open_interest_value': 0, 'timestamp': int(time.time() * 1000)}
            
    def get_market_metrics(self, symbol: str) -> Dict:
        try:
            ticker = self.get_ticker(symbol)
            orderbook = self.get_orderbook(symbol)
            funding = self.get_funding_rate(symbol)
            oi = self.get_open_interest(symbol)
            
            if not ticker or not orderbook:
                return {}
                
            spread = ticker['ask'] - ticker['bid'] if ticker['ask'] and ticker['bid'] else 0
            mid_price = (ticker['ask'] + ticker['bid']) / 2 if ticker['ask'] and ticker['bid'] else ticker['last']
            spread_bps = (spread / mid_price * 10000) if mid_price > 0 else 0
            
            bid_depth = sum([bid[1] for bid in orderbook['bids'][:5]]) if orderbook['bids'] else 0
            ask_depth = sum([ask[1] for ask in orderbook['asks'][:5]]) if orderbook['asks'] else 0
            total_depth = bid_depth + ask_depth
            imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0
            
            return {
                'spread': spread,
                'spread_bps': spread_bps,
                'mid_price': mid_price,
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'imbalance': imbalance,
                'funding_rate': funding.get('funding_rate', 0),
                'open_interest': oi.get('open_interest', 0),
                'volume_24h': ticker.get('volume', 0),
                'price_change_24h': ticker.get('percentage', 0),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error calculating market metrics for {symbol}: {e}")
            return {}
            
    def get_alternative_data(self, symbol: str) -> Dict:
        alt_data = {}
        
        try:
            alt_data['fear_greed_index'] = self._get_fear_greed_index()
            alt_data['social_sentiment'] = self._get_social_sentiment(symbol)
            alt_data['news_sentiment'] = self._get_news_sentiment(symbol)
            alt_data['whale_alerts'] = self._get_whale_alerts(symbol)
            alt_data['exchange_flows'] = self._get_exchange_flows(symbol)
            alt_data['defi_metrics'] = self._get_defi_metrics(symbol)
            alt_data['derivatives_metrics'] = self._get_derivatives_metrics(symbol)
            alt_data['correlation_data'] = self._get_correlation_data(symbol)
            alt_data['macro_indicators'] = self._get_macro_indicators()
            alt_data['technical_indicators'] = self._get_technical_indicators(symbol)
            
        except Exception as e:
            print(f"Error fetching alternative data for {symbol}: {e}")
            
        return alt_data
        
    def _get_fear_greed_index(self) -> float:
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                return float(data['data'][0]['value'])
                
        except Exception as e:
            print(f"Error fetching fear & greed index: {e}")
            
        return 50.0
        
    def _get_social_sentiment(self, symbol: str) -> Dict:
        try:
            coin_map = {
                'BTC-USDT-SWAP': 'bitcoin',
                'ETH-USDT-SWAP': 'ethereum',
                'SOL-USDT-SWAP': 'solana'
            }
            
            coin_id = coin_map.get(symbol, 'bitcoin')
            
            url = f"https://api.lunarcrush.com/v2/assets/{coin_id}/time-series"
            headers = {'Authorization': 'Bearer your_lunarcrush_api_key'}
            
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()
            
            if data.get('data'):
                latest = data['data'][0]
                return {
                    'sentiment_score': float(latest.get('sentiment', 3)),
                    'social_volume': float(latest.get('social_volume', 0)),
                    'social_score': float(latest.get('social_score', 50)),
                    'twitter_mentions': int(latest.get('tweets', 0)),
                    'reddit_posts': int(latest.get('reddit_posts', 0))
                }
                
        except Exception as e:
            print(f"Error fetching social sentiment for {symbol}: {e}")
            
        return {
            'sentiment_score': 3.0,
            'social_volume': 0.0,
            'social_score': 50.0,
            'twitter_mentions': 0,
            'reddit_posts': 0
        }
        
    def _get_news_sentiment(self, symbol: str) -> Dict:
        try:
            coin_map = {
                'BTC-USDT-SWAP': 'bitcoin',
                'ETH-USDT-SWAP': 'ethereum', 
                'SOL-USDT-SWAP': 'solana'
            }
            
            coin_name = coin_map.get(symbol, 'bitcoin')
            
            url = f"https://cryptonews-api.com/api/v1/category"
            params = {
                'section': 'general',
                'items': 10,
                'page': 1,
                'token': 'your_cryptonews_api_key'
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get('data'):
                sentiment_scores = []
                for article in data['data']:
                    if coin_name.lower() in article.get('title', '').lower():
                        sentiment_scores.append(self._analyze_text_sentiment(article.get('title', '')))
                        
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                
                return {
                    'news_sentiment': avg_sentiment,
                    'news_count': len(sentiment_scores),
                    'positive_news': len([s for s in sentiment_scores if s > 0.1]),
                    'negative_news': len([s for s in sentiment_scores if s < -0.1])
                }
                
        except Exception as e:
            print(f"Error fetching news sentiment for {symbol}: {e}")
            
        return {
            'news_sentiment': 0.0,
            'news_count': 0,
            'positive_news': 0,
            'negative_news': 0
        }
        
    def _analyze_text_sentiment(self, text: str) -> float:
        positive_words = ['bullish', 'pump', 'moon', 'surge', 'rally', 'breakout', 'bull', 'up', 'gain', 'rise']
        negative_words = ['bearish', 'dump', 'crash', 'drop', 'fall', 'bear', 'down', 'loss', 'decline', 'sell']
        
        text_lower = text.lower()
        
        positive_count = sum([1 for word in positive_words if word in text_lower])
        negative_count = sum([1 for word in negative_words if word in text_lower])
        
        if positive_count + negative_count == 0:
            return 0.0
            
        return (positive_count - negative_count) / (positive_count + negative_count)
        
    def _get_whale_alerts(self, symbol: str) -> Dict:
        try:
            url = "https://api.whale-alert.io/v1/transactions"
            params = {
                'api_key': 'your_whale_alert_api_key',
                'min_value': 100000,
                'limit': 10
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get('transactions'):
                whale_txs = []
                for tx in data['transactions']:
                    if symbol.split('-')[0].lower() in tx.get('symbol', '').lower():
                        whale_txs.append({
                            'amount': float(tx.get('amount', 0)),
                            'amount_usd': float(tx.get('amount_usd', 0)),
                            'from_owner': tx.get('from', {}).get('owner', ''),
                            'to_owner': tx.get('to', {}).get('owner', ''),
                            'timestamp': tx.get('timestamp', 0)
                        })
                        
                return {
                    'whale_transactions': whale_txs,
                    'total_volume': sum([tx['amount_usd'] for tx in whale_txs]),
                    'exchange_inflows': sum([tx['amount_usd'] for tx in whale_txs if 'exchange' in tx['to_owner'].lower()]),
                    'exchange_outflows': sum([tx['amount_usd'] for tx in whale_txs if 'exchange' in tx['from_owner'].lower()])
                }
                
        except Exception as e:
            print(f"Error fetching whale alerts for {symbol}: {e}")
            
        return {
            'whale_transactions': [],
            'total_volume': 0.0,
            'exchange_inflows': 0.0,
            'exchange_outflows': 0.0
        }
        
    def _get_exchange_flows(self, symbol: str) -> Dict:
        return {
            'net_flow': 0.0,
            'inflow': 0.0,
            'outflow': 0.0,
            'exchange_balance': 0.0
        }
        
    def _get_defi_metrics(self, symbol: str) -> Dict:
        return {
            'tvl': 0.0,
            'lending_rate': 0.0,
            'borrowing_rate': 0.0,
            'utilization_rate': 0.0
        }
        
    def _get_derivatives_metrics(self, symbol: str) -> Dict:
        return {
            'futures_basis': 0.0,
            'options_volume': 0.0,
            'put_call_ratio': 1.0,
            'max_pain': 0.0
        }
        
    def _get_correlation_data(self, symbol: str) -> Dict:
        return {
            'btc_correlation': 0.0,
            'eth_correlation': 0.0,
            'spy_correlation': 0.0,
            'dxy_correlation': 0.0
        }
        
    def _get_macro_indicators(self) -> Dict:
        return {
            'dxy_index': 100.0,
            'us_10y_yield': 4.0,
            'vix_index': 20.0,
            'gold_price': 2000.0
        }
        
    def _get_technical_indicators(self, symbol: str) -> Dict:
        try:
            data = self.get_historical_data(symbol, '1h', 30)
            if data is None or len(data) < 20:
                return {}
                
            close_prices = data['close'].values
            
            sma_20 = np.mean(close_prices[-20:])
            sma_50 = np.mean(close_prices[-50:]) if len(close_prices) >= 50 else sma_20
            
            rsi = self._calculate_rsi(close_prices, 14)
            
            bb_upper, bb_lower = self._calculate_bollinger_bands(close_prices, 20, 2)
            
            return {
                'sma_20': sma_20,
                'sma_50': sma_50,
                'rsi': rsi,
                'bb_upper': bb_upper,
                'bb_lower': bb_lower,
                'current_price': close_prices[-1]
            }
            
        except Exception as e:
            print(f"Error calculating technical indicators for {symbol}: {e}")
            return {}
            
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: int = 2) -> Tuple[float, float]:
        if len(prices) < period:
            return prices[-1], prices[-1]
            
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band, lower_band
        
    def get_market_structure_data(self) -> Dict:
        structure_data = {}
        
        try:
            for symbol in self.config['symbols']:
                ticker = self.get_ticker(symbol)
                orderbook = self.get_orderbook(symbol, 100)
                
                if ticker and orderbook:
                    structure_data[symbol] = {
                        'liquidity_score': self._calculate_liquidity_score(orderbook),
                        'market_impact': self._estimate_market_impact(orderbook),
                        'order_book_imbalance': self._calculate_orderbook_imbalance(orderbook),
                        'spread_quality': self._assess_spread_quality(ticker, orderbook),
                        'depth_quality': self._assess_depth_quality(orderbook),
                        'price_stability': self._assess_price_stability(symbol)
                    }
                    
        except Exception as e:
            print(f"Error getting market structure data: {e}")
            
        return structure_data
        
    def _calculate_liquidity_score(self, orderbook: Dict) -> float:
        if not orderbook.get('bids') or not orderbook.get('asks'):
            return 0.0
            
        bid_liquidity = sum([bid[1] for bid in orderbook['bids'][:10]])
        ask_liquidity = sum([ask[1] for ask in orderbook['asks'][:10]])
        
        total_liquidity = bid_liquidity + ask_liquidity
        
        return min(total_liquidity / 1000000, 1.0)
        
    def _estimate_market_impact(self, orderbook: Dict) -> float:
        if not orderbook.get('bids') or not orderbook.get('asks'):
            return 1.0
            
        trade_size = 10000
        
        cumulative_size = 0
        weighted_price = 0
        
        for bid in orderbook['bids']:
            price, size = bid[0], bid[1]
            take_size = min(size, trade_size - cumulative_size)
            weighted_price += price * take_size
            cumulative_size += take_size
            
            if cumulative_size >= trade_size:
                break
                
        if cumulative_size == 0:
            return 1.0
            
        avg_execution_price = weighted_price / cumulative_size
        best_bid = orderbook['bids'][0][0]
        
        market_impact = abs(avg_execution_price - best_bid) / best_bid
        
        return market_impact
        
    def _calculate_orderbook_imbalance(self, orderbook: Dict) -> float:
        if not orderbook.get('bids') or not orderbook.get('asks'):
            return 0.0
            
        bid_volume = sum([bid[1] for bid in orderbook['bids'][:5]])
        ask_volume = sum([ask[1] for ask in orderbook['asks'][:5]])
        
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return 0.0
            
        imbalance = (bid_volume - ask_volume) / total_volume
        
        return imbalance
        
    def _assess_spread_quality(self, ticker: Dict, orderbook: Dict) -> float:
        if not ticker or not orderbook.get('bids') or not orderbook.get('asks'):
            return 0.0
            
        spread = ticker['ask'] - ticker['bid']
        mid_price = (ticker['ask'] + ticker['bid']) / 2
        
        if mid_price == 0:
            return 0.0
            
        spread_pct = spread / mid_price
        
        quality_score = max(0, 1 - (spread_pct / 0.001))
        
        return quality_score
        
    def _assess_depth_quality(self, orderbook: Dict) -> float:
        if not orderbook.get('bids') or not orderbook.get('asks'):
            return 0.0
            
        bid_depth = sum([bid[1] for bid in orderbook['bids'][:20]])
        ask_depth = sum([ask[1] for ask in orderbook['asks'][:20]])
        
        total_depth = bid_depth + ask_depth
        
        depth_score = min(total_depth / 100000, 1.0)
        
        return depth_score
        
    def _assess_price_stability(self, symbol: str) -> float:
        try:
            recent_data = self.get_historical_data(symbol, '1m', 1)
            if recent_data is None or len(recent_data) < 10:
                return 0.5
                
            returns = recent_data['close'].pct_change().dropna()
            volatility = returns.std()
            
            stability_score = max(0, 1 - (volatility / 0.01))
            
            return stability_score
            
        except Exception as e:
            return 0.5
            
    def validate_data_quality(self, data: pd.DataFrame, symbol: str) -> Dict:
        quality_report = {
            'symbol': symbol,
            'total_records': len(data),
            'missing_values': data.isnull().sum().sum(),
            'duplicate_records': data.duplicated().sum(),
            'data_quality_score': 0.0,
            'issues': []
        }
        
        if len(data) == 0:
            quality_report['issues'].append('No data available')
            return quality_report
            
        price_cols = ['open', 'high', 'low', 'close']
        
        for col in price_cols:
            if col in data.columns:
                if (data[col] <= 0).any():
                    quality_report['issues'].append(f'Invalid {col} prices (<=0)')
                    
                if data[col].isnull().any():
                    quality_report['issues'].append(f'Missing {col} values')
                    
        if 'high' in data.columns and 'low' in data.columns:
            if (data['high'] < data['low']).any():
                quality_report['issues'].append('High < Low price inconsistency')
                
        if 'volume' in data.columns:
            if (data['volume'] < 0).any():
                quality_report['issues'].append('Negative volume values')
                
        time_gaps = data.index.to_series().diff()
        expected_gap = time_gaps.mode().iloc[0] if len(time_gaps.mode()) > 0 else pd.Timedelta(hours=1)
        
        large_gaps = time_gaps > expected_gap * 2
        if large_gaps.any():
            quality_report['issues'].append(f'Data gaps detected: {large_gaps.sum()} instances')
            
        quality_score = 1.0 - (len(quality_report['issues']) * 0.1)
        quality_report['data_quality_score'] = max(0.0, quality_score)
        
        return quality_report