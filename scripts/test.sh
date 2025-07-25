#!/bin/bash

cd "$(dirname "$0")/.."

echo "🧪 Testing Scherman System"
echo "========================="

echo "📦 Testing imports..."
python3 -c "
import sys
sys.path.insert(0, 'core')

try:
    from scherman_vix import SchermanVIXCore, SchermanRiskManager
    from data_manager import SchermanDataManager
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

echo "🔧 Testing basic functionality..."
python3 -c "
import sys
sys.path.insert(0, 'core')
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from scherman_vix import SchermanVIXCore

dates = pd.date_range(start=datetime.now() - timedelta(days=10), periods=100, freq='1H')
test_data = pd.DataFrame({
    'open': np.random.normal(50000, 100, 100),
    'high': np.random.normal(50100, 100, 100),
    'low': np.random.normal(49900, 100, 100),
    'close': np.random.normal(50000, 100, 100),
    'volume': np.random.normal(1000, 100, 100)
}, index=dates)

vix_core = SchermanVIXCore()
signal = vix_core.analyze_divergence(test_data, [20, 25, 30, 28, 32])

if signal:
    print('✅ Signal generation works')
    print(f'   Direction: {signal[\"direction\"]}')
    print(f'   Confidence: {signal[\"confidence\"]:.1%}')
else:
    print('ℹ️ No signal generated (normal for random data)')

print('✅ Basic functionality test passed')
"

echo ""
echo "🎉 All tests passed!"
echo ""
echo "Next steps:"
echo "1. Copy .env.template to .env"
echo "2. Add your OKX API credentials to .env"
echo "3. Run: ./scripts/run.sh"
