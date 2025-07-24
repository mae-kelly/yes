#!/bin/bash

# MacOS-compatible System Health Check Script

set -e

echo "🏥 SYSTEM HEALTH CHECK (MacOS)"
echo "============================="

# Activate virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
fi

# Check each component
components_ok=0
total_components=5

echo "🔍 Checking core components..."

# 1. Check imports
echo -n "📦 Module imports: "
if python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from core.data_manager import EnterpriseDataManager
    from core.signal_engine import SchermanVIXDivergenceCore  
    from core.risk_manager import RiskManager
    print('✅ OK')
except ImportError as e:
    print(f'❌ FAILED - {e}')
    exit(1)
" 2>/dev/null; then
    ((components_ok++))
else
    echo "❌ FAILED"
fi

# 2. Check API connectivity
echo -n "🌐 API connectivity: "
if curl -s --max-time 10 "https://api.coingecko.com/api/v3/ping" | grep -q "gecko_says" 2>/dev/null; then
    echo "✅ OK"
    ((components_ok++))
else
    echo "❌ FAILED"
fi

# 3. Check credentials (MacOS compatible)
echo -n "🔐 Credentials: "
if [ -f ".env" ]; then
    if grep -q "your_okx_api_key_here" .env 2>/dev/null; then
        echo "❌ FAILED - Not configured"
    else
        # Check if values are present and non-empty
        source .env 2>/dev/null || true
        if [ -n "$OKX_API_KEY" ] && [ -n "$OKX_SECRET" ] && [ -n "$OKX_PASSPHRASE" ]; then
            echo "✅ OK"
            ((components_ok++))
        else
            echo "❌ FAILED - Empty values"
        fi
    fi
else
    echo "❌ FAILED - No .env file"
fi

# 4. Check file permissions
echo -n "📁 File permissions: "
if [ -r ".env" ] && [ -w "logs" ] && [ -w "data" ]; then
    echo "✅ OK"
    ((components_ok++))
else
    echo "❌ FAILED"
fi

# 5. Check system resources (MacOS compatible)
echo -n "💻 System resources: "
# Use vm_stat for MacOS memory check
if command -v vm_stat >/dev/null 2>&1; then
    free_pages=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    if [ -n "$free_pages" ] && [ "$free_pages" -gt 50000 ]; then
        echo "✅ OK"
        ((components_ok++))
    else
        echo "⚠️ LOW MEMORY"
        ((components_ok++))  # Still count as OK with warning
    fi
else
    echo "✅ OK (Check skipped on this system)"
    ((components_ok++))
fi

echo ""
echo "📊 Health Check Results: $components_ok/$total_components components OK"

if [ $components_ok -eq $total_components ]; then
    echo "✅ SYSTEM HEALTHY - Ready for operation"
    exit 0
elif [ $components_ok -ge 3 ]; then
    echo "⚠️ SYSTEM DEGRADED - Some issues detected"
    exit 1
else
    echo "❌ SYSTEM UNHEALTHY - Major issues detected"
    exit 2
fi
