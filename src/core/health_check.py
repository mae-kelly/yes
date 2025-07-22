"""
Comprehensive health checking for Scherman Trading System
"""

import asyncio
import aiohttp
from typing import Dict, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    check_func: Callable
    timeout: int = 30
    critical: bool = True

class HealthMonitor:
    """Comprehensive health monitoring"""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.results: Dict[str, Dict] = {}
        self.last_check = None
    
    def add_check(self, name: str, check_func: Callable, timeout: int = 30, critical: bool = True):
        """Add a health check"""
        self.checks.append(HealthCheck(name, check_func, timeout, critical))
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        critical_failures = 0
        total_checks = len(self.checks)
        
        for check in self.checks:
            try:
                start_time = time.time()
                result = await asyncio.wait_for(check.check_func(), timeout=check.timeout)
                response_time = time.time() - start_time
                
                results[check.name] = {
                    'status': HealthStatus.HEALTHY.value,
                    'response_time': response_time,
                    'details': result,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            except asyncio.TimeoutError:
                results[check.name] = {
                    'status': HealthStatus.UNHEALTHY.value,
                    'error': 'Timeout',
                    'timestamp': datetime.utcnow().isoformat()
                }
                if check.critical:
                    critical_failures += 1
            
            except Exception as e:
                results[check.name] = {
                    'status': HealthStatus.UNHEALTHY.value,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                if check.critical:
                    critical_failures += 1
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = HealthStatus.UNHEALTHY.value
        elif any(r.get('status') == HealthStatus.UNHEALTHY.value for r in results.values()):
            overall_status = HealthStatus.DEGRADED.value
        else:
            overall_status = HealthStatus.HEALTHY.value
        
        self.results = results
        self.last_check = datetime.utcnow()
        
        return {
            'status': overall_status,
            'timestamp': self.last_check.isoformat(),
            'checks': results,
            'summary': {
                'total_checks': total_checks,
                'healthy': sum(1 for r in results.values() if r.get('status') == HealthStatus.HEALTHY.value),
                'degraded': sum(1 for r in results.values() if r.get('status') == HealthStatus.DEGRADED.value),
                'unhealthy': sum(1 for r in results.values() if r.get('status') == HealthStatus.UNHEALTHY.value)
            }
        }

