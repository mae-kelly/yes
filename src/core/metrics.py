"""
Prometheus metrics for Scherman Trading System
"""

import time
import threading
from typing import Dict, Any
from collections import defaultdict, Counter

class MetricsCollector:
    """Collect and expose system metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: defaultdict(float))
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.lock = threading.Lock()
    
    def inc_counter(self, name: str, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            key = self._build_key(name, labels or {})
            self.counters[key] += 1
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            key = self._build_key(name, labels or {})
            self.metrics['gauges'][key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe a value for histogram"""
        with self.lock:
            key = self._build_key(name, labels or {})
            self.histograms[key].append(value)
            
            # Keep only last 1000 values
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
    
    def _build_key(self, name: str, labels: Dict[str, str]) -> str:
        """Build metric key with labels"""
        if not labels:
            return name
        
        label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        with self.lock:
            output = []
            
            # Export counters
            for key, value in self.counters.items():
                output.append(f'# TYPE {key.split("{")[0]} counter')
                output.append(f'{key} {value}')
            
            # Export gauges
            for key, value in self.metrics['gauges'].items():
                output.append(f'# TYPE {key.split("{")[0]} gauge')
                output.append(f'{key} {value}')
            
            # Export histograms
            for key, values in self.histograms.items():
                if values:
                    output.append(f'# TYPE {key.split("{")[0]} histogram')
                    output.append(f'{key}_sum {sum(values)}')
                    output.append(f'{key}_count {len(values)}')
            
            return '\n'.join(output)

# Global metrics instance
metrics = MetricsCollector()

