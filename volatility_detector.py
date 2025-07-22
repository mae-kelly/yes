import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class VolatilityDetector:
    def __init__(self, config: Dict):
        self.config = config
        self.volatility_regimes = {'low': 0.15, 'normal': 0.25, 'high': 0.40, 'extreme': 0.60}
        self.volatility_models = {}
        self.realized_volatility = {}
        self.implied_volatility = {}
        self.volatility_forecasts = {}
        self.volatility_clusters = {}
        self.volatility_breakouts = {}
        self.volatility_mean_reversion = {}
        self.volatility_term_structure = {}
        self.volatility_smile = {}
        self.volatility_surface = {}
        self.volatility_skew = {}
        self.volatility_risk_premium = {}
        self.volatility_persistence = {}
        self.volatility_asymmetry = {}
        self.volatility_spillovers = {}
        self.volatility_transmission = {}
        self.volatility_contagion = {}
        self.volatility_synchronization = {}
        self.volatility_lead_lag = {}
        self.volatility_causality = {}
        self.volatility_feedback = {}
        self.volatility_amplification = {}
        self.volatility_attenuation = {}
        self.volatility_momentum = {}
        self.volatility_reversal = {}
        self.volatility_cycles = {}
        self.volatility_seasonality = {}
        self.volatility_trends = {}
        self.volatility_structural_breaks = {}
        self.volatility_regime_changes = {}
        self.volatility_thresholds = {'low_vol': 0.12, 'medium_vol': 0.25, 'high_vol': 0.45, 'extreme_vol': 0.70}
        self.volatility_estimators = {'parkinson': True, 'garman_klass': True, 'rogers_satchell': True, 'yang_zhang': True}
        self.volatility_filters = {'ema': 0.94, 'kalman': True, 'hodrick_prescott': 1600, 'butterworth': 0.1}
        self.volatility_transformations = {'log': True, 'sqrt': True, 'box_cox': True, 'yeo_johnson': True}
        self.volatility_normalizations = {'z_score': True, 'min_max': True, 'robust': True, 'quantile': True}
        
    def detect_volatility_regime(self, data: pd.DataFrame, symbol: str) -> str:
        try:
            if len(data) < 50:
                return 'normal'
            returns = data['close'].pct_change().dropna()
            current_vol = returns.rolling(window=24).std().iloc[-1] * np.sqrt(365)
            vol_percentile = returns.rolling(window=252).std().rank(pct=True).iloc[-1] if len(returns) > 252 else 0.5
            if current_vol < self.volatility_thresholds['low_vol']:
                return 'low'
            elif current_vol < self.volatility_thresholds['medium_vol']:
                return 'normal'
            elif current_vol < self.volatility_thresholds['high_vol']:
                return 'high'
            else:
                return 'extreme'
        except Exception as e:
            print(f"Error detecting volatility regime for {symbol}: {e}")
            return 'normal'
            
    def calculate_realized_volatility(self, data: pd.DataFrame, symbol: str, estimator: str = 'close_to_close') -> pd.Series:
        try:
            if estimator == 'close_to_close':
                returns = data['close'].pct_change()
                realized_vol = returns.rolling(window=24).std() * np.sqrt(365)
            elif estimator == 'parkinson':
                hl_ratio = np.log(data['high'] / data['low'])
                realized_vol = np.sqrt(hl_ratio.rolling(window=24).mean() / (4 * np.log(2))) * np.sqrt(365)
            elif estimator == 'garman_klass':
                ln_hl = np.log(data['high'] / data['low'])
                ln_co = np.log(data['close'] / data['open'])
                gk_vol = 0.5 * ln_hl**2 - (2*np.log(2)-1) * ln_co**2
                realized_vol = np.sqrt(gk_vol.rolling(window=24).mean()) * np.sqrt(365)
            elif estimator == 'rogers_satchell':
                ln_ho = np.log(data['high'] / data['open'])
                ln_hc = np.log(data['high'] / data['close'])
                ln_lo = np.log(data['low'] / data['open'])
                ln_lc = np.log(data['low'] / data['close'])
                rs_vol = ln_ho * ln_hc + ln_lo * ln_lc
                realized_vol = np.sqrt(rs_vol.rolling(window=24).mean()) * np.sqrt(365)
            elif estimator == 'yang_zhang':
                ln_co = np.log(data['close'] / data['open'])
                ln_oc = np.log(data['open'] / data['close'].shift(1))
                ln_ho = np.log(data['high'] / data['open'])
                ln_hc = np.log(data['high'] / data['close'])
                ln_lo = np.log(data['low'] / data['open'])
                ln_lc = np.log(data['low'] / data['close'])
                overnight = ln_oc**2
                rs = ln_ho * ln_hc + ln_lo * ln_lc
                k = 0.34 / (1.34 + (24+1)/(24-1))
                yz_vol = overnight + k*ln_co**2 + (1-k)*rs
                realized_vol = np.sqrt(yz_vol.rolling(window=24).mean()) * np.sqrt(365)
            else:
                returns = data['close'].pct_change()
                realized_vol = returns.rolling(window=24).std() * np.sqrt(365)
            return realized_vol.fillna(method='ffill')
        except Exception as e:
            print(f"Error calculating realized volatility for {symbol}: {e}")
            returns = data['close'].pct_change()
            return returns.rolling(window=24).std() * np.sqrt(365)
            
    def detect_volatility_clusters(self, data: pd.DataFrame, symbol: str) -> pd.Series:
        try:
            returns = data['close'].pct_change().dropna()
            abs_returns = np.abs(returns)
            volatility = abs_returns.rolling(window=24).mean()
            vol_threshold = volatility.quantile(0.75)
            clusters = (volatility > vol_threshold).astype(int)
            cluster_persistence = clusters.rolling(window=5).sum()
            return cluster_persistence >= 3
        except Exception as e:
            print(f"Error detecting volatility clusters for {symbol}: {e}")
            return pd.Series(False, index=data.index)
            
    def detect_volatility_breakouts(self, data: pd.DataFrame, symbol: str) -> Dict:
        try:
            volatility = self.calculate_realized_volatility(data, symbol)
            rolling_mean = volatility.rolling(window=50).mean()
            rolling_std = volatility.rolling(window=50).std()
            upper_band = rolling_mean + 2 * rolling_std
            lower_band = rolling_mean - 2 * rolling_std
            breakout_up = volatility > upper_band
            breakout_down = volatility < lower_band
            return {'breakout_up': breakout_up.iloc[-1] if not breakout_up.empty else False, 'breakout_down': breakout_down.iloc[-1] if not breakout_down.empty else False, 'current_vol': volatility.iloc[-1] if not volatility.empty else 0.2, 'upper_band': upper_band.iloc[-1] if not upper_band.empty else 0.3, 'lower_band': lower_band.iloc[-1] if not lower_band.empty else 0.1}
        except Exception as e:
            print(f"Error detecting volatility breakouts for {symbol}: {e}")
            return {'breakout_up': False, 'breakout_down': False, 'current_vol': 0.2, 'upper_band': 0.3, 'lower_band': 0.1}
            
    def calculate_volatility_momentum(self, data: pd.DataFrame, symbol: str, lookback: int = 10) -> float:
        try:
            volatility = self.calculate_realized_volatility(data, symbol)
            if len(volatility) < lookback + 1:
                return 0.0
            vol_momentum = (volatility.iloc[-1] - volatility.iloc[-lookback-1]) / volatility.iloc[-lookback-1]
            return vol_momentum
        except Exception as e:
            print(f"Error calculating volatility momentum for {symbol}: {e}")
            return 0.0
            
    def calculate_volatility_percentile(self, data: pd.DataFrame, symbol: str, window: int = 252) -> float:
        try:
            volatility = self.calculate_realized_volatility(data, symbol)
            if len(volatility) < window:
                return 0.5
            current_vol = volatility.iloc[-1]
            historical_vols = volatility.iloc[-window:]
            percentile = (historical_vols <= current_vol).mean()
            return percentile
        except Exception as e:
            print(f"Error calculating volatility percentile for {symbol}: {e}")
            return 0.5
            
    def forecast_volatility_garch(self, data: pd.DataFrame, symbol: str, horizon: int = 5) -> float:
        try:
            returns = data['close'].pct_change().dropna()
            if len(returns) < 100:
                return self.calculate_realized_volatility(data, symbol).iloc[-1]
            returns_scaled = returns * 100
            omega = 0.01
            alpha = 0.1
            beta = 0.85
            long_run_var = omega / (1 - alpha - beta)
            current_return = returns_scaled.iloc[-1]
            current_var = returns_scaled.rolling(window=10).var().iloc[-1]
            forecasted_var = long_run_var
            for h in range(horizon):
                forecasted_var = omega + alpha * (current_return**2 if h == 0 else forecasted_var) + beta * (current_var if h == 0 else forecasted_var)
            forecasted_vol = np.sqrt(forecasted_var) / 100 * np.sqrt(365)
            return forecasted_vol
        except Exception as e:
            print(f"Error forecasting GARCH volatility for {symbol}: {e}")
            return self.calculate_realized_volatility(data, symbol).iloc[-1]
            
    def calculate_volatility_skew(self, data: pd.DataFrame, symbol: str) -> float:
        try:
            returns = data['close'].pct_change().dropna()
            if len(returns) < 30:
                return 0.0
            skewness = returns.rolling(window=30).skew().iloc[-1]
            return skewness if not np.isnan(skewness) else 0.0
        except Exception as e:
            print(f"Error calculating volatility skew for {symbol}: {e}")
            return 0.0
            
    def calculate_volatility_kurtosis(self, data: pd.DataFrame, symbol: str) -> float:
        try:
            returns = data['close'].pct_change().dropna()
            if len(returns) < 30:
                return 3.0
            kurt = returns.rolling(window=30).kurt().iloc[-1]
            return kurt if not np.isnan(kurt) else 3.0
        except Exception as e:
            print(f"Error calculating volatility kurtosis for {symbol}: {e}")
            return 3.0
            
    def detect_volatility_regime_change(self, data: pd.DataFrame, symbol: str) -> Dict:
        try:
            volatility = self.calculate_realized_volatility(data, symbol)
            if len(volatility) < 100:
                return {'regime_change': False, 'new_regime': 'normal', 'confidence': 0.5}
            recent_vol = volatility.iloc[-20:].mean()
            historical_vol = volatility.iloc[-100:-20].mean()
            vol_change = (recent_vol - historical_vol) / historical_vol
            regime_change = abs(vol_change) > 0.3
            if recent_vol < self.volatility_thresholds['low_vol']:
                new_regime = 'low'
            elif recent_vol < self.volatility_thresholds['medium_vol']:
                new_regime = 'normal'
            elif recent_vol < self.volatility_thresholds['high_vol']:
                new_regime = 'high'
            else:
                new_regime = 'extreme'
            confidence = min(abs(vol_change), 1.0)
            return {'regime_change': regime_change, 'new_regime': new_regime, 'confidence': confidence, 'vol_change': vol_change}
        except Exception as e:
            print(f"Error detecting volatility regime change for {symbol}: {e}")
            return {'regime_change': False, 'new_regime': 'normal', 'confidence': 0.5, 'vol_change': 0.0}
            
    def calculate_volatility_ratio(self, data: pd.DataFrame, symbol: str, short_window: int = 10, long_window: int = 50) -> float:
        try:
            volatility = self.calculate_realized_volatility(data, symbol)
            if len(volatility) < long_window:
                return 1.0
            short_vol = volatility.iloc[-short_window:].mean()
            long_vol = volatility.iloc[-long_window:].mean()
            vol_ratio = short_vol / long_vol if long_vol > 0 else 1.0
            return vol_ratio
        except Exception as e:
            print(f"Error calculating volatility ratio for {symbol}: {e}")
            return 1.0
            
    def calculate_volatility_spread(self, data: pd.DataFrame, symbol: str) -> float:
        try:
            high_vol = self.calculate_realized_volatility(data, symbol, estimator='parkinson')
            low_vol = self.calculate_realized_volatility(data, symbol, estimator='close_to_close')
            if len(high_vol) == 0 or len(low_vol) == 0:
                return 0.0
            vol_spread = high_vol.iloc[-1] - low_vol.iloc[-1]
            return vol_spread
        except Exception as e:
            print(f"Error calculating volatility spread for {symbol}: {e}")
            return 0.0
            
    def get_volatility_signals(self, data: pd.DataFrame, symbol: str) -> Dict:
        try:
            current_regime = self.detect_volatility_regime(data, symbol)
            vol_clusters = self.detect_volatility_clusters(data, symbol)
            vol_breakouts = self.detect_volatility_breakouts(data, symbol)
            vol_momentum = self.calculate_volatility_momentum(data, symbol)
            vol_percentile = self.calculate_volatility_percentile(data, symbol)
            vol_forecast = self.forecast_volatility_garch(data, symbol)
            vol_skew = self.calculate_volatility_skew(data, symbol)
            vol_kurtosis = self.calculate_volatility_kurtosis(data, symbol)
            regime_change = self.detect_volatility_regime_change(data, symbol)
            vol_ratio = self.calculate_volatility_ratio(data, symbol)
            vol_spread = self.calculate_volatility_spread(data, symbol)
            return {'current_regime': current_regime, 'clusters_detected': vol_clusters.iloc[-1] if not vol_clusters.empty else False, 'breakout_signals': vol_breakouts, 'momentum': vol_momentum, 'percentile': vol_percentile, 'forecast': vol_forecast, 'skew': vol_skew, 'kurtosis': vol_kurtosis, 'regime_change': regime_change, 'volatility_ratio': vol_ratio, 'volatility_spread': vol_spread, 'timestamp': datetime.now()}
        except Exception as e:
            print(f"Error getting volatility signals for {symbol}: {e}")
            return {'current_regime': 'normal', 'clusters_detected': False, 'breakout_signals': {'breakout_up': False, 'breakout_down': False}, 'momentum': 0.0, 'percentile': 0.5, 'forecast': 0.2, 'skew': 0.0, 'kurtosis': 3.0, 'regime_change': {'regime_change': False}, 'volatility_ratio': 1.0, 'volatility_spread': 0.0, 'timestamp': datetime.now()}